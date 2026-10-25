import frappe
from frappe.utils import now_datetime,add_to_date
from frappe.model.workflow import apply_workflow
from vanbags_maintenance import teams,execution,work_orders as wo
from vanbags_maintenance.test_support import grant_scope,SITE_A,SITE_A2,COMPANY_A
from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase

class TestTeamCompatibility(WorkOrderCase):
    def test_external_team_can_assign_scoped_member(self):
        frappe.set_user('Administrator')
        external=frappe.get_doc({'doctype':teams.TEAM,'team_code':self.token+'-EXT','team_name':'External service','company':COMPANY_A,'management_site':SITE_A,'team_type':'External','disciplines':[{'discipline':self.discipline}]}).insert()
        for dt,extra in [(teams.GRANT,{'site':SITE_A}),(teams.MEMBER,{'user':self.users['tech'],'discipline':self.discipline,'function':'Technician'})]:
            frappe.get_doc({'doctype':dt,'team':external.name,'valid_from':add_to_date(now_datetime(),days=-1),**extra}).insert()
        doc=self.authorize();doc.responsible_team=external.name;doc.assigned_to=self.users['tech'];doc.save();doc=apply_workflow(doc.as_dict(),'Assign')
        self.assertEqual(frappe.db.get_value(teams.ASSIGN,doc.team_assignment,'team'),external.name)

    def test_member_can_read_team_serving_second_site_without_management_site_permission(self):
        frappe.set_user('Administrator')
        grant_scope(self.users['tech'],site=SITE_A2)
        frappe.get_doc({'doctype':teams.GRANT,'team':self.team,'site':SITE_A2,'valid_from':now_datetime()}).insert()
        for name in frappe.get_all('User Permission',filters={'user':self.users['tech'],'allow':'TruCMMS Site','for_value':SITE_A},pluck='name'):frappe.delete_doc('User Permission',name)
        frappe.set_user(self.users['tech']);frappe.get_doc(teams.TEAM,self.team).check_permission('read')
        self.assertIn(self.team,frappe.get_list(teams.TEAM,pluck='name'))

    def test_other_discipline_and_nonmember_assignment_are_rejected(self):
        doc=self.authorize();frappe.set_user('Administrator')
        frappe.get_doc({'doctype':teams.DISC,'discipline_code':self.token+'-ELEC','discipline_name':'Electrical'}).insert()
        frappe.set_user(self.users['supervisor']);doc.required_discipline=self.token+'-ELEC';doc.assigned_to=self.users['tech']
        with self.assertRaises(frappe.PermissionError):doc.save()
        doc.reload();doc.assigned_to=self.users['other'];frappe.set_user('Administrator')
        membership=frappe.get_doc(teams.MEMBER,self.memberships['other']);membership.revoked=1;membership.save()
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.PermissionError):doc.save()

    def test_operational_roles_cannot_import_export_or_share_team_records(self):
        for role in ('supervisor','dispatcher','tech'):
            frappe.set_user(self.users[role])
            for dt in (teams.TEAM,teams.MEMBER,teams.GRANT,teams.ASSIGN):
                self.assertFalse(frappe.has_permission(dt,'export'));self.assertFalse(frappe.has_permission(dt,'share'));self.assertFalse(frappe.get_meta(dt).allow_import)

    def test_legacy_execution_remains_compatible_until_explicit_adoption(self):
        doc=self.assign();frappe.set_user('Administrator')
        frappe.db.set_value(wo.DT,doc.name,{'team_policy':'Legacy','team_assignment':None,'responsible_team':None,'required_discipline':None})
        membership=frappe.get_doc(teams.MEMBER,self.memberships['tech']);membership.revoked=1;membership.save()
        frappe.set_user(self.users['tech']);self.assertEqual(execution.order_for_recording(doc.name).name,doc.name)

    def test_organizational_attachments_cannot_become_public(self):
        from frappe.utils.file_manager import save_file
        frappe.set_user('Administrator')
        with self.assertRaises(frappe.PermissionError):save_file('team-private.txt',b'Roster information',teams.TEAM,self.team,is_private=0)
