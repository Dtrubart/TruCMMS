import uuid
import frappe
from frappe.tests import IntegrationTestCase
from frappe.model.workflow import apply_workflow
from frappe.utils.file_manager import save_file
from vanbags_maintenance import work_orders as wo
from vanbags_maintenance.test_support import org_context, grant_scope, COMPANY_A, SITE_A2


class WorkOrderCase(IntegrationTestCase):
    def setUp(self):
        super().setUp();frappe.set_user('Administrator');frappe.db.savepoint('wo_case')
        self.token='WO-'+uuid.uuid4().hex[:10]
        self.users={}
        for key,role in [('requester','TruCMMS Requester'),('dispatcher',wo.DISPATCHER),('supervisor',wo.SUPERVISOR),('tech',wo.TECHNICIAN),('other',wo.TECHNICIAN)]:
            user=frappe.get_doc({'doctype':'User','email':self.token+key+'@example.com','first_name':'Work order test','send_welcome_email':0,'roles':[{'role':role}]}).insert()
            self.users[key]=user.name;grant_scope(user.name)
        from frappe.utils import now_datetime,add_to_date
        from vanbags_maintenance import teams
        self.discipline='TEST-MECHANICAL'
        if not frappe.db.exists(teams.DISC,self.discipline):frappe.get_doc({'doctype':teams.DISC,'discipline_code':self.discipline,'discipline_name':'Test mechanical'}).insert()
        self.team=frappe.get_doc({'doctype':teams.TEAM,'team_code':self.token,'team_name':self.token,'company':COMPANY_A,'management_site':org_context()['site'],'team_type':'Internal','disciplines':[{'discipline':self.discipline}]}).insert().name
        start=add_to_date(now_datetime(),days=-20)
        self.site_grant=frappe.get_doc({'doctype':teams.GRANT,'team':self.team,'site':org_context()['site'],'valid_from':start}).insert().name
        self.memberships={}
        for key in ('tech','other'):
            self.memberships[key]=frappe.get_doc({'doctype':teams.MEMBER,'team':self.team,'user':self.users[key],'discipline':self.discipline,'function':'Technician','valid_from':start}).insert().name
        self.location=frappe.get_doc({'doctype':'VB Equipment Location',**org_context(),'location_name':self.token}).insert()
        frappe.set_user(self.users['requester'])
        self.request=frappe.get_doc({'doctype':'TruCMMS Maintenance Request',**org_context(),'subject':'Fault','description':'Inspect pump','functional_location':self.location.name,'priority':'High'}).insert()
        self.request=apply_workflow(self.request.as_dict(),'Send Request')
        frappe.set_user(self.users['dispatcher']);self.request=apply_workflow(self.request.as_dict(),'Triage');self.request=apply_workflow(self.request.as_dict(),'Approve')

    def tearDown(self):
        frappe.set_user('Administrator');frappe.db.rollback(save_point='wo_case');super().tearDown()

    def make(self):
        frappe.set_user(self.users['dispatcher']);doc=frappe.get_doc(wo.from_request(self.request.name))
        if not getattr(self,'use_c_policy',False):
            frappe.set_user('Administrator');frappe.db.set_value(wo.DT,doc.name,'lifecycle_policy','Legacy');doc.reload();frappe.set_user(self.users['dispatcher'])
        doc.responsible_team=self.team;doc.required_discipline=self.discipline;doc.save();return doc

    def authorize(self):
        doc=self.make();frappe.set_user(self.users['supervisor']);return apply_workflow(doc.as_dict(),'Authorize')

    def assign(self):
        doc=self.authorize();doc.assigned_to=self.users['tech'];doc.save(ignore_version=False)
        return apply_workflow(doc.as_dict(),'Assign')


class TestWorkOrders(WorkOrderCase):
    def test_conversion_is_idempotent_and_preserves_context(self):
        doc=self.make();again=wo.from_request(self.request.name)
        self.assertEqual(doc.name,again.name);self.assertEqual(doc.site,self.request.site);self.assertEqual(doc.functional_location,self.location.name);self.assertEqual(doc.maintenance_request,self.request.name)

    def test_unapproved_request_and_requester_conversion_denied(self):
        frappe.set_user('Administrator');frappe.db.set_value('TruCMMS Maintenance Request',self.request.name,'status','Rejected')
        frappe.set_user(self.users['dispatcher'])
        with self.assertRaises(frappe.ValidationError):wo.from_request(self.request.name)
        frappe.set_user('Administrator');frappe.db.set_value('TruCMMS Maintenance Request',self.request.name,'status','Approved')
        frappe.set_user(self.users['requester'])
        with self.assertRaises(frappe.PermissionError):wo.from_request(self.request.name)

    def test_dispatcher_cannot_authorize_or_skip_transition(self):
        doc=self.make()
        with self.assertRaises(frappe.ValidationError):apply_workflow(doc.as_dict(),'Authorize')
        doc.status='Assigned';doc.assigned_to=self.users['tech']
        with self.assertRaises(frappe.PermissionError):doc.save()

    def test_authorization_stamps_server_identity_and_freezes_scope(self):
        doc=self.authorize();self.assertEqual(doc.authorized_by,self.users['supervisor']);self.assertTrue(doc.authorized_on)
        doc.scope='Replacement scope'
        with self.assertRaises(frappe.ValidationError):doc.save()

    def test_assign_and_reassign_preserve_identity_and_version(self):
        doc=self.assign();name=doc.name
        self.assertEqual(doc.assigned_by,self.users['supervisor']);self.assertTrue(doc.assigned_on)
        doc.assigned_to=self.users['other'];doc.save(ignore_version=False)
        self.assertEqual(doc.name,name);self.assertTrue(frappe.db.exists('Version',{'ref_doctype':wo.DT,'docname':name}))
        frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.PermissionError):doc.check_permission('read')

    def test_technician_reads_only_assigned_order_and_cannot_edit(self):
        doc=self.assign();frappe.set_user(self.users['tech']);doc.check_permission('read')
        with self.assertRaises(frappe.PermissionError):doc.check_permission('write')
        frappe.set_user(self.users['other']);self.assertEqual(frappe.get_list(wo.DT,pluck='name'),[])
        with self.assertRaises(frappe.PermissionError):doc.check_permission('read')

    def test_assignment_requires_enabled_scoped_technician(self):
        doc=self.authorize();doc.assigned_to=self.users['requester']
        with self.assertRaises(frappe.ValidationError):doc.save()
        frappe.set_user('Administrator')
        for name in frappe.get_all('User Permission',filters={'user':self.users['tech']},pluck='name'):frappe.delete_doc('User Permission',name)
        frappe.set_user(self.users['supervisor']);doc.reload();doc.assigned_to=self.users['tech']
        with self.assertRaises(frappe.PermissionError):doc.save()

    def test_references_and_audit_fields_are_immutable(self):
        doc=self.make();doc.site=SITE_A2
        with self.assertRaises(frappe.PermissionError):doc.save()
        doc.reload();doc.authorized_by=self.users['dispatcher']
        with self.assertRaises(frappe.ValidationError):doc.save()

    def test_scope_revocation_sharing_and_private_evidence(self):
        doc=self.make();file=save_file(self.token+'.txt',b'work scope evidence',wo.DT,doc.name,is_private=1);file=frappe.get_doc('File',file.name)
        frappe.set_user(self.users['other'])
        with self.assertRaises(frappe.PermissionError):file.is_downloadable()
        frappe.set_user('Administrator')
        with self.assertRaises(frappe.PermissionError):frappe.share.add(wo.DT,doc.name,user=self.users['other'],notify=0)
        for name in frappe.get_all('User Permission',filters={'user':self.users['dispatcher']},pluck='name'):frappe.delete_doc('User Permission',name)
        frappe.set_user(self.users['dispatcher'])
        with self.assertRaises(frappe.PermissionError):doc.check_permission('read')
        with self.assertRaises(frappe.PermissionError):file.is_downloadable()

    def test_authorized_order_cannot_be_deleted(self):
        doc=self.authorize();frappe.set_user('Administrator')
        with self.assertRaises(frappe.PermissionError):frappe.delete_doc(wo.DT,doc.name)

    def test_supervisor_can_read_original_approved_fault_without_rewriting_it(self):
        frappe.set_user(self.users['supervisor']);self.request.check_permission('read')
        with self.assertRaises(frappe.PermissionError):self.request.check_permission('write')

    def test_operational_roles_cannot_bulk_export_or_share(self):
        doc=self.make()
        for key in ('dispatcher','supervisor','tech'):
            frappe.set_user(self.users[key])
            self.assertFalse(frappe.has_permission(wo.DT,'export'))
            self.assertFalse(frappe.has_permission(wo.DT,'share'))
        self.assertFalse(frappe.get_meta(wo.DT).allow_import)
