import frappe
from frappe.utils import now_datetime, add_to_date
from frappe.utils.file_manager import save_file
from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase
from vanbags_maintenance import execution as ex
from vanbags_maintenance import work_orders as wo


class TestExecution(WorkOrderCase):
    def setUp(self):
        super().setUp()
        self.order=self.assign()
        frappe.set_user('Administrator')
        frappe.db.set_value(wo.DT,self.order.name,{'assigned_on':add_to_date(now_datetime(),hours=-2),'authorized_on':add_to_date(now_datetime(),hours=-3)})
        self.order.reload();self.start=add_to_date(now_datetime(),minutes=-60);self.end=add_to_date(self.start,minutes=30)

    def entry(self,**values):
        frappe.set_user(self.users['tech'])
        return frappe.get_doc({'doctype':ex.DT,'work_order':self.order.name,'actual_start':self.start,'actual_end':self.end,
            'findings':'Bearing inspected; follow-up required','tasks':[{'task':'Inspect bearing','result':'Partial','findings':'Wear detected'}],**values}).insert()

    def test_recording_stamps_identity_context_and_duration(self):
        with self.assertRaises(frappe.PermissionError):self.entry(company='Forged')
        doc=self.entry(technician=self.users['other'],actual_minutes=900)
        self.assertEqual(doc.technician,self.users['tech']);self.assertEqual(doc.owner,self.users['tech']);self.assertEqual(doc.company,self.order.company)
        self.assertEqual(doc.site,self.order.site);self.assertAlmostEqual(doc.actual_minutes,30);self.assertTrue(doc.recorded_on)

    def test_unassigned_users_and_supervisor_cannot_record(self):
        for key in ('other','dispatcher','supervisor'):
            frappe.set_user(self.users[key])
            with self.assertRaises(frappe.PermissionError):
                frappe.get_doc({'doctype':ex.DT,'work_order':self.order.name,'actual_start':self.start,'actual_end':self.end,'findings':'Forged execution','tasks':[{'task':'Task','result':'Completed','findings':'Done'}]}).insert(ignore_permissions=True)

    def test_unassigned_state_blocks_recording(self):
        frappe.set_user('Administrator');frappe.db.set_value(wo.DT,self.order.name,'status','Authorized')
        with self.assertRaises(frappe.PermissionError):self.entry()

    def test_invalid_future_and_preassignment_times_rejected(self):
        for values in ({'actual_end':self.start},{'actual_end':add_to_date(self.start,minutes=-1)}, {'actual_end':add_to_date(now_datetime(),minutes=10)}, {'actual_start':add_to_date(now_datetime(),hours=-4)}):
            with self.assertRaises(frappe.ValidationError):self.entry(**values)

    def test_tasks_and_findings_are_required(self):
        for values in ({'tasks':[]},{'findings':'  '},{'tasks':[{'task':'Task','result':'Blocked','findings':' '}]}):
            with self.assertRaises(frappe.ValidationError):self.entry(**values)
        doc=self.entry(tasks=[{'task':'Inspect','result':'Blocked','findings':'Access unavailable'}]);self.assertEqual(doc.tasks[0].result,'Blocked')

    def test_overlapping_time_rejected_adjacent_time_allowed(self):
        self.entry()
        with self.assertRaises(frappe.ValidationError):self.entry(actual_start=add_to_date(self.start,minutes=10))
        second=self.entry(actual_start=self.end,actual_end=add_to_date(self.end,minutes=10));self.assertAlmostEqual(second.actual_minutes,10)

    def test_saved_entries_cannot_be_rewritten_or_deleted(self):
        doc=self.entry();doc.findings='Rewrite'
        with self.assertRaises(frappe.PermissionError):doc.save()
        frappe.set_user('Administrator')
        with self.assertRaises(frappe.PermissionError):frappe.delete_doc(ex.DT,doc.name)
        row=frappe.get_doc('TruCMMS Execution Task',doc.tasks[0].name);row.findings='Direct child rewrite'
        with self.assertRaises(frappe.PermissionError):row.save(ignore_permissions=True)
        doc.reload();doc.tasks[0].findings='Rewrite history'
        with self.assertRaises(frappe.PermissionError):doc.save(ignore_permissions=True)

    def test_execution_does_not_modify_authorized_scope(self):
        self.entry();self.order.reload();self.assertEqual(self.order.status,'Assigned');self.assertEqual(self.order.scope,'Inspect pump')
        self.order.scope='Tech replacement scope'
        with self.assertRaises(frappe.PermissionError):self.order.save()

    def test_private_evidence_is_append_only(self):
        doc=self.entry();file=save_file(self.token+'.txt',b'Execution evidence',ex.DT,doc.name,is_private=1);file=frappe.get_doc('File',file.name)
        self.assertTrue(file.is_downloadable())
        file.is_private=0
        with self.assertRaises(frappe.PermissionError):file.save()
        frappe.set_user('Administrator')
        with self.assertRaises(frappe.PermissionError):frappe.delete_doc('File',file.name)

    def test_evidence_visibility_and_revocation(self):
        doc=self.entry();file=save_file(self.token+'.txt',b'Execution evidence',ex.DT,doc.name,is_private=1);file=frappe.get_doc('File',file.name)
        frappe.set_user(self.users['other'])
        with self.assertRaises(frappe.PermissionError):file.is_downloadable()
        self.assertEqual(frappe.get_list(ex.DT,pluck='name'),[])
        self.assertEqual(frappe.get_list('File',filters={'name':file.name},pluck='name'),[])
        frappe.set_user('Administrator')
        for name in frappe.get_all('User Permission',filters={'user':self.users['tech']},pluck='name'):frappe.delete_doc('User Permission',name)
        frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.PermissionError):doc.check_permission('read')
        with self.assertRaises(frappe.PermissionError):file.is_downloadable()

    def test_reassignment_preserves_history_and_changes_access(self):
        doc=self.entry();frappe.set_user(self.users['supervisor']);self.order.assigned_to=self.users['other'];self.order.save(ignore_version=False)
        doc.check_permission('read')
        frappe.set_user(self.users['other']);doc.check_permission('read')
        with self.assertRaises(frappe.PermissionError):save_file(self.token+'.txt',b'Impersonation',ex.DT,doc.name,is_private=1)
        frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.PermissionError):doc.check_permission('read')
        self.assertEqual(frappe.get_list(ex.DT,pluck='name'),[])

    def test_sharing_and_public_evidence_denied(self):
        doc=self.entry()
        with self.assertRaises(frappe.ValidationError):save_file(self.token+'.txt',b'Public',ex.DT,doc.name,is_private=0)
        frappe.set_user('Administrator')
        with self.assertRaises(frappe.PermissionError):frappe.share.add(ex.DT,doc.name,user=self.users['other'],notify=0)
