import frappe
from frappe.utils import now_datetime, add_to_date
from frappe.utils.file_manager import save_file
from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase
from vanbags_maintenance import lifecycle as life, work_orders as wo


class TestLifecycle(WorkOrderCase):
    def setUp(self):
        super().setUp();self.order=self.assign()
        frappe.set_user('Administrator');frappe.db.set_value(wo.DT,self.order.name,'assigned_on',add_to_date(now_datetime(),hours=-3));self.order.reload()

    def execution(self,result='Completed',minutes=-60):
        frappe.set_user(self.users['tech'])
        return frappe.get_doc({'doctype':'TruCMMS Work Execution','work_order':self.order.name,'actual_start':add_to_date(now_datetime(),minutes=minutes),'actual_end':add_to_date(now_datetime(),minutes=minutes+10),'findings':'Service restored','tasks':[{'task':'Repair','result':result,'findings':'Checked'}]}).insert()

    def action(self,key,action,reason='Verified service restored'):
        frappe.set_user(self.users[key]);return frappe.get_doc(life.perform(self.order.name,action,reason))

    def complete(self):
        self.execution();return self.action('tech','Complete Work')

    def test_complete_accept_close_has_distinct_audited_stages(self):
        doc=self.complete();self.assertEqual(doc.status,'Technical Completed');self.assertEqual(doc.completed_by,self.users['tech'])
        doc=self.action('requester','Accept Work');self.assertEqual(doc.status,'Accepted');self.assertEqual(doc.accepted_by,self.users['requester'])
        doc=self.action('supervisor','Close Order');self.assertEqual(doc.status,'Closed');self.assertEqual(doc.closed_by,self.users['supervisor'])
        self.assertEqual(frappe.db.count(life.EVENT,{'work_order':doc.name}),3)
        self.assertTrue(frappe.db.exists('Version',{'ref_doctype':wo.DT,'docname':doc.name}))
        self.assertEqual(frappe.db.get_value('TruCMMS Maintenance Request',self.request.name,'status'),'Approved')

    def test_completion_requires_current_execution_and_completed_tasks(self):
        with self.assertRaises(frappe.ValidationError):self.action('tech','Complete Work')
        self.execution('Blocked')
        with self.assertRaises(frappe.ValidationError):self.action('tech','Complete Work')
        self.execution('Completed',minutes=-30);self.action('tech','Complete Work')

    def test_wrong_role_wrong_requester_and_skip_close_denied(self):
        with self.assertRaises(frappe.PermissionError):self.action('dispatcher','Complete Work')
        with self.assertRaises(frappe.ValidationError):self.action('supervisor','Close Order')
        self.complete()
        with self.assertRaises(frappe.PermissionError):self.action('other','Accept Work')
        with self.assertRaises(frappe.PermissionError):self.action('dispatcher','Accept on Behalf')

    def test_rework_requires_reason_and_new_execution_cycle(self):
        self.complete()
        with self.assertRaises(frappe.ValidationError):self.action('requester','Request Rework',' ')
        doc=self.action('requester','Request Rework','Noise persists');self.assertEqual(doc.status,'Assigned');self.assertEqual(doc.execution_cycle,2)
        with self.assertRaises(frappe.ValidationError):self.action('tech','Complete Work')
        frappe.set_user('Administrator');frappe.db.set_value(wo.DT,self.order.name,'rework_on',add_to_date(now_datetime(),hours=-2))
        entry=self.execution(minutes=-30);self.assertEqual(entry.execution_cycle,2)
        self.action('tech','Complete Work');self.action('requester','Accept Work');self.action('supervisor','Close Order')
        self.assertEqual(frappe.db.count(life.EVENT,{'work_order':doc.name}),5)

    def test_supervisor_acceptance_records_justification(self):
        self.complete()
        with self.assertRaises(frappe.ValidationError):self.action('supervisor','Accept on Behalf','')
        doc=self.action('supervisor','Accept on Behalf','Requester unavailable; verified service with site lead')
        self.assertEqual(doc.acceptance_method,'Supervisor on behalf');self.assertEqual(doc.accepted_by,self.users['supervisor'])

    def test_self_acceptance_is_denied_even_with_supervisor_role(self):
        self.complete();frappe.set_user('Administrator');user=frappe.get_doc('User',self.users['tech']);user.append('roles',{'role':wo.SUPERVISOR});user.save()
        with self.assertRaises(frappe.PermissionError):self.action('tech','Accept on Behalf')

    def test_cancel_preserves_history_and_is_visible_to_requester(self):
        entry=self.execution()
        with self.assertRaises(frappe.ValidationError):self.action('supervisor','Cancel Order','')
        doc=self.action('supervisor','Cancel Order','Work stopped; replacement equipment selected');self.assertEqual(doc.status,'Cancelled')
        self.assertTrue(frappe.db.exists('TruCMMS Work Execution',entry.name))
        frappe.set_user(self.users['requester']);doc.check_permission('read')
        self.assertEqual(frappe.get_list(wo.DT,filters={'name':doc.name},pluck='name'),[doc.name])
        with self.assertRaises(frappe.ValidationError):self.action('supervisor','Close Order')

    def test_closed_and_cancelled_orders_cannot_be_rewritten(self):
        self.complete();self.action('requester','Accept Work');doc=self.action('supervisor','Close Order')
        frappe.set_user('Administrator');doc.scope='Rewrite'
        with self.assertRaises(frappe.PermissionError):doc.save()
        with self.assertRaises(frappe.PermissionError):frappe.delete_doc(wo.DT,doc.name)
        with self.assertRaises(frappe.ValidationError):self.action('supervisor','Cancel Order')

    def test_completion_freezes_execution_and_evidence_until_rework(self):
        entry=self.execution();self.action('tech','Complete Work');frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.PermissionError):save_file(self.token+'.txt',b'Late evidence','TruCMMS Work Execution',entry.name,is_private=1)
        self.action('requester','Request Rework','More work required')
        frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.PermissionError):save_file(self.token+'.txt',b'Rework evidence','TruCMMS Work Execution',entry.name,is_private=1)
        frappe.set_user('Administrator');frappe.db.set_value(wo.DT,self.order.name,'rework_on',add_to_date(now_datetime(),hours=-2))
        new_entry=self.execution(minutes=-30);save_file(self.token+'new.txt',b'New cycle evidence','TruCMMS Work Execution',new_entry.name,is_private=1)

    def test_native_workflow_and_audit_field_bypasses_denied(self):
        from frappe.model.workflow import apply_workflow
        self.execution();frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.PermissionError):apply_workflow(self.order.as_dict(),'Complete Work')
        frappe.set_user(self.users['supervisor']);self.order.completed_by=self.users['tech']
        with self.assertRaises(frappe.ValidationError):self.order.save()

    def test_events_are_immutable_and_scoped(self):
        self.complete();event=frappe.get_doc(life.EVENT,frappe.db.get_value(life.EVENT,{'work_order':self.order.name},'name'))
        frappe.set_user(self.users['other'])
        with self.assertRaises(frappe.PermissionError):event.check_permission('read')
        self.assertEqual(frappe.get_list(life.EVENT,filters={'work_order':self.order.name},pluck='name'),[])
        frappe.set_user('Administrator');event.reason='Rewrite'
        with self.assertRaises(frappe.PermissionError):event.save(ignore_permissions=True)
        with self.assertRaises(frappe.PermissionError):frappe.delete_doc(life.EVENT,event.name)

    def test_acceptance_scope_revocation_prevents_review(self):
        self.complete();frappe.set_user('Administrator')
        for name in frappe.get_all('User Permission',filters={'user':self.users['requester']},pluck='name'):frappe.delete_doc('User Permission',name)
        with self.assertRaises(frappe.PermissionError):self.action('requester','Accept Work')

    def test_rework_cannot_be_backdated_before_review(self):
        self.complete();self.action('requester','Request Rework','Retest under load')
        with self.assertRaises(frappe.ValidationError):self.execution(minutes=-30)

    def test_accepted_work_cannot_be_cancelled(self):
        self.complete();self.action('requester','Accept Work')
        with self.assertRaises(frappe.ValidationError):self.action('supervisor','Cancel Order')

    def test_workflow_upgrade_backfills_populated_orders_and_is_idempotent(self):
        frappe.set_user('Administrator');frappe.db.set_value(wo.DT,self.order.name,{'requester':None,'execution_cycle':0})
        life.setup();life.setup();self.order.reload()
        self.assertEqual(self.order.requester,self.users['requester']);self.assertEqual(self.order.execution_cycle,1)
        self.assertEqual(self.order.assigned_to,self.users['tech'])
        workflow=frappe.get_doc('Workflow','TruCMMS Work Order Workflow')
        self.assertEqual(len(workflow.states),7);self.assertEqual(len(workflow.transitions),12)

    def test_reassignment_from_full_desk_document_preserves_datetime_audit(self):
        self.complete();doc=self.action('requester','Request Rework','Specialist required')
        frappe.set_user(self.users['supervisor']);payload=frappe.parse_json(frappe.as_json(doc.as_dict()))
        updated=frappe.get_doc(payload);updated.assigned_to=self.users['other'];updated.save(ignore_version=False)
        self.assertEqual(updated.assigned_to,self.users['other']);self.assertEqual(updated.execution_cycle,2)
