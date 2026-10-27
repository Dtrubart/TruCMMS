import hashlib
import json
import uuid

import frappe
from frappe.tests import IntegrationTestCase
from vanbags_maintenance import job_plans as jp, navigation
from vanbags_maintenance.test_support import COMPANY_A, SITE_A, SITE_B, COMPANY_B, grant_scope


class TestJobPlans(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        frappe.set_user('Administrator')
        frappe.db.savepoint('job_plan_case')
        self.token = 'JP-' + uuid.uuid4().hex[:10]
        self.users = {}
        for key, role in [('dispatcher','TruCMMS Dispatcher'),('supervisor','TruCMMS Supervisor'),('tech','TruCMMS Technician'),('requester','TruCMMS Requester')]:
            doc = frappe.get_doc(dict(doctype='User', email=self.token+key+'@example.com', first_name='Procedure test', send_welcome_email=0, roles=[{'role':role}])).insert()
            self.users[key] = doc.name
            grant_scope(doc.name)
        self.units = {}
        for label in ('mm','kWh','L-min','hour','box','each'):
            self.units[label] = frappe.get_doc(dict(doctype='UOM', uom_name=self.token+'-'+label, must_be_whole_number=0)).insert().name
        # A fresh headless ERPNext install has no setup-wizard Item Group tree.
        # Build the test's own root only when needed; never seed production data.
        group = frappe.db.get_value('Item Group', {'parent_item_group':['is','not set']}, 'name')
        if not group:
            group = frappe.get_doc(dict(doctype='Item Group', item_group_name='TruCMMS Test Item Root', is_group=1)).insert().name
        self.item = frappe.get_doc(dict(doctype='Item', item_code=self.token, item_name='Filter pack', item_group=group, stock_uom=self.units['each'], is_stock_item=0, is_sales_item=0, is_purchase_item=0,
            uoms=[dict(uom=self.units['each'], conversion_factor=1),dict(uom=self.units['box'], conversion_factor=4)])).insert()
        self.plan = self.make_plan()
        frappe.set_user(self.users['dispatcher'])

    def tearDown(self):
        frappe.set_user('Administrator')
        frappe.db.rollback(save_point='job_plan_case')
        super().tearDown()

    def make_plan(self, company=COMPANY_A, site=SITE_A):
        return frappe.get_doc(dict(doctype=jp.PLAN, code=self.token+'-'+site, plan_name='AHU routine', company=company, site=site)).insert()

    def draft(self, **kw):
        values=dict(doctype=jp.REVISION, job_plan=self.plan.name, revision_title='Inspect AHU filters', change_reason='Initial controlled procedure',
            tasks=[dict(task_code='inspect', instructions='Inspect the equipment', estimated_minutes=10, mandatory=1)])
        values.update(kw)
        return frappe.get_doc(values).insert()

    def approved(self, **kw):
        doc=self.draft(**kw)
        frappe.set_user(self.users['supervisor'])
        jp.approve(doc.name, 'Reviewed procedure scope and instructions')
        return doc.reload()

    def metric(self, **kw):
        values=dict(task_code='inspect', metric_key='tread', metric_name='Tread depth', metric_kind='Condition', unit=self.units['mm'], direction='Decreasing', required=1, has_lower_limit=1, lower_limit=0)
        values.update(kw)
        return values

    def material(self, **kw):
        values=dict(task_code='inspect', item=self.item.name, quantity=2, uom=self.units['box'])
        values.update(kw)
        return values

    def test_task_only_revision_needs_no_material_or_measurement(self):
        doc=self.draft()
        self.assertEqual((doc.status,doc.revision_number,doc.company,doc.site),('Draft',1,COMPANY_A,SITE_A))
        self.assertFalse(doc.materials)
        self.assertFalse(doc.measurements)

    def test_approval_captures_hash_actor_tasks_and_units(self):
        doc=self.approved(measurements=[self.metric()],materials=[self.material()])
        payload=jp.approved_snapshot(doc.name)
        self.assertEqual(doc.approved_by,self.users['supervisor'])
        self.assertEqual(doc.content_hash,hashlib.sha256(doc.content_json.encode()).hexdigest())
        self.assertEqual(payload['materials'][0]['stock_quantity'],8)
        self.assertEqual(payload['measurements'][0]['lower_limit'],0)

    def test_dispatcher_cannot_self_approve(self):
        doc=self.draft()
        with self.assertRaises(frappe.PermissionError): jp.approve(doc.name,'Approve')
        self.assertEqual(doc.reload().status,'Draft')

    def test_status_and_snapshot_cannot_be_forged(self):
        for field,value in [('status','Approved'),('content_json','{}'),('approved_by',self.users['supervisor'])]:
            doc=self.draft()
            doc.set(field,value)
            with self.assertRaises(frappe.ValidationError): doc.save()

    def test_inserted_revision_cannot_forge_identity_or_approval(self):
        for values in [dict(revision_number=50),dict(status='Approved'),dict(content_hash='fake')]:
            with self.assertRaises(frappe.ValidationError): self.draft(**values)

    def test_approved_content_and_children_are_immutable(self):
        doc=self.approved()
        for field,value in [('revision_title','Altered'),('status','Draft')]:
            doc.reload();doc.set(field,value)
            with self.assertRaises(frappe.ValidationError): doc.save()
        doc.reload();doc.tasks[0].instructions='Altered'
        with self.assertRaises(frappe.ValidationError): doc.save()

    def test_new_revision_preserves_prior_content_and_links_ancestry(self):
        old=self.approved(measurements=[self.metric()],materials=[self.material()])
        before=old.content_json
        result=jp.revise(old.name,'New inspection method')
        draft=frappe.get_doc(jp.REVISION,result['name'])
        self.assertEqual((draft.revision_number,draft.status,draft.previous_revision),(2,'Draft',old.name))
        self.assertFalse(draft.content_json)
        draft.tasks[0].instructions='Updated procedure';draft.save()
        self.assertEqual(old.reload().content_json,before)

    def test_retirement_preserves_approved_snapshot_and_is_not_reapproval(self):
        doc=self.approved(materials=[self.material()]);before=doc.content_json
        jp.retire(doc.name,'Replaced by a newer method')
        doc.reload();self.assertEqual(doc.status,'Retired');self.assertEqual(doc.content_json,before)
        self.assertEqual(jp.approved_snapshot(doc.name)['revision'],doc.name)
        with self.assertRaises(frappe.ValidationError): jp.approve(doc.name,'Again')

    def test_reasons_are_required_and_failed_action_rolls_back(self):
        doc=self.draft();frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.ValidationError): jp.approve(doc.name,'  ')
        self.assertEqual(doc.reload().status,'Draft')
        self.assertFalse(doc.approved_by)

    def test_technician_reads_approved_but_not_draft_or_writes(self):
        draft=self.draft();approved=self.approved()
        frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.PermissionError): draft.check_permission('read')
        approved.check_permission('read')
        with self.assertRaises(frappe.PermissionError): jp.revise(approved.name,'Not an editor')
        names=frappe.get_list(jp.REVISION,pluck='name')
        self.assertIn(approved.name,names);self.assertNotIn(draft.name,names)

    def test_requester_and_guest_cannot_read_procedures(self):
        doc=self.approved()
        for user in [self.users['requester'],'Guest']:
            frappe.set_user(user)
            with self.assertRaises(frappe.PermissionError): jp.approved_snapshot(doc.name)

    def test_company_and_site_scope_cannot_be_shared_or_bypassed(self):
        frappe.set_user('Administrator');foreign=self.make_plan(COMPANY_B,SITE_B)
        other=self.draft(job_plan=foreign.name)
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.PermissionError): other.check_permission('read')
        with self.assertRaises(frappe.PermissionError): jp.approve(other.name,'Foreign approval')
        self.assertNotIn(other.name,frappe.get_list(jp.REVISION,pluck='name'))
        frappe.set_user('Administrator')
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc(dict(doctype='DocShare',share_doctype=jp.REVISION,share_name=other.name,user=self.users['supervisor'],read=1)).insert(ignore_permissions=True)

    def test_revision_identity_and_scope_cannot_change(self):
        doc=self.draft()
        for field,value in [('revision_number',100),('site',SITE_B),('previous_revision','forged')]:
            doc.reload();doc.set(field,value)
            error = frappe.PermissionError if field == 'site' else frappe.ValidationError
            with self.assertRaises(error): doc.save()

    def test_disabled_parent_prevents_new_revisions_and_approval(self):
        doc=self.draft();self.plan.disabled=1;self.plan.save()
        with self.assertRaises(frappe.ValidationError): self.draft()
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.ValidationError): jp.approve(doc.name,'Disabled')

    def test_task_and_measurement_references_must_be_valid_and_unique(self):
        for values in [dict(tasks=[]),dict(tasks=[dict(task_code='x',instructions='A'),dict(task_code='x',instructions='B')]),dict(measurements=[self.metric(task_code='missing')]),dict(measurements=[self.metric(),self.metric()])]:
            with self.assertRaises(frappe.ValidationError): self.draft(**values)

    def test_decreasing_condition_and_diverse_metrics_are_supported(self):
        doc=self.draft(measurements=[self.metric(),self.metric(metric_key='energy',metric_name='Energy',unit=self.units['kWh'],metric_kind='Cumulative',direction='Increasing'),self.metric(metric_key='flow',metric_name='Flow',unit=self.units['L-min'],metric_kind='Rate',direction='Variable'),self.metric(metric_key='hours',metric_name='Operating hours',unit=self.units['hour'],metric_kind='Cumulative',direction='Increasing')])
        self.assertEqual(len(doc.measurements),4)

    def test_invalid_bounds_and_counter_direction_are_rejected(self):
        for metric in [self.metric(lower_limit=5,has_upper_limit=1,upper_limit=2),self.metric(metric_kind='Cumulative',direction='Decreasing')]:
            with self.assertRaises(frappe.ValidationError): self.draft(measurements=[metric])
        for value in ['NaN','Infinity','-Infinity','1e1000']:
            with self.assertRaises(frappe.ValidationError): jp.finite(value,'Metric')

    def test_material_quantity_and_item_conversion_are_validated(self):
        for row in [self.material(quantity=0),self.material(quantity=-1),self.material(uom=self.units['mm']),self.material(task_code='missing')]:
            with self.assertRaises(frappe.ValidationError): self.draft(materials=[row])

    def test_disabled_item_is_rechecked_at_approval(self):
        doc=self.draft(materials=[self.material()])
        frappe.set_user('Administrator');self.item.disabled=1;self.item.save()
        with self.assertRaises(frappe.ValidationError): jp.approve(doc.name,'Review')
        self.assertEqual(doc.reload().status,'Draft')

    def test_later_item_and_parent_edits_do_not_rewrite_snapshot(self):
        doc=self.approved(materials=[self.material()]);before=jp.approved_snapshot(doc.name)
        frappe.set_user('Administrator');self.item.item_name='Renamed filter';self.item.save()
        self.plan.plan_name='Renamed library entry';self.plan.save()
        self.assertEqual(jp.approved_snapshot(doc.name),before)

    def test_library_does_not_generate_orders_or_inventory_transactions(self):
        types=['TruCMMS Maintenance Work Order','Stock Entry','Material Request','Stock Ledger Entry']
        before={dt:frappe.db.count(dt) for dt in types}
        self.approved(materials=[self.material()])
        self.assertEqual(before,{dt:frappe.db.count(dt) for dt in types})

    def test_revision_numbers_are_sequential_and_deletion_is_denied(self):
        first=self.draft();second=self.draft()
        self.assertEqual((first.revision_number,second.revision_number),(1,2))
        frappe.set_user('Administrator')
        with self.assertRaises(frappe.PermissionError): first.delete()
        with self.assertRaises(frappe.PermissionError): self.plan.delete()

    def test_native_permissions_do_not_allow_export_share_or_catalog_writes(self):
        frappe.set_user(self.users['dispatcher'])
        for dt in (jp.PLAN,jp.REVISION):
            for ptype in ('export','share','delete','import'):
                self.assertFalse(frappe.has_permission(dt,ptype), (dt,ptype))
        self.assertTrue(frappe.has_permission('Item','select'))
        self.assertFalse(frappe.has_permission('Item','write'))
        self.assertFalse(frappe.has_permission('Stock Entry','create'))

    def test_revision_navigation_remains_contextual(self):
        targets={link['target'] for group in navigation.groups() for link in group['links']}
        self.assertIn(jp.PLAN,targets)
        self.assertNotIn(jp.REVISION,targets)

    def test_snapshot_corruption_is_reported_instead_of_returned(self):
        doc=self.approved()
        frappe.db.set_value(jp.REVISION,doc.name,'content_hash','corrupted')
        with self.assertRaises(frappe.ValidationError): jp.approved_snapshot(doc.name)

    def test_procedure_scope_and_identity_remain_permanent(self):
        frappe.set_user('Administrator')
        for field,value in [('code','renamed'),('company',COMPANY_B),('site',SITE_B)]:
            self.plan.reload();self.plan.set(field,value)
            with self.assertRaises(frappe.ValidationError): self.plan.save()

    def test_unversioned_file_attachments_cannot_bypass_procedure_scope(self):
        from frappe.utils.file_manager import save_file
        doc=self.approved()
        for dt,name in [(jp.PLAN,self.plan.name),(jp.REVISION,doc.name)]:
            for private in (0,1):
                with self.assertRaises(frappe.PermissionError):
                    save_file(self.token+'.txt','Unversioned content',dt,name,is_private=private)
