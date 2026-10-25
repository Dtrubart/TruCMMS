import frappe
from frappe.utils import now_datetime,add_to_date,get_datetime
from frappe.utils.file_manager import save_file
from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase
from vanbags_maintenance import reporting as reports, adjustments as adj, lifecycle as life,work_orders as wo


class TestReporting(WorkOrderCase):
    def setUp(self):
        super().setUp()
        self.order=self.make();self.order.target_closure=add_to_date(now_datetime(),days=-1);self.order.save()
        frappe.set_user(self.users['supervisor'])
        from frappe.model.workflow import apply_workflow
        self.order=apply_workflow(self.order.as_dict(),'Authorize');self.order.assigned_to=self.users['tech'];self.order.save();self.order=apply_workflow(self.order.as_dict(),'Assign')
        frappe.set_user('Administrator');frappe.db.set_value(wo.DT,self.order.name,'assigned_on',add_to_date(now_datetime(),hours=-3));self.order.reload()

    def entry(self,minutes=-60,result='Completed'):
        frappe.set_user(self.users['tech'])
        return frappe.get_doc({'doctype':'TruCMMS Work Execution','work_order':self.order.name,'actual_start':add_to_date(now_datetime(),minutes=minutes),'actual_end':add_to_date(now_datetime(),minutes=minutes+10),'findings':'Functional check','tasks':[{'task':'Inspect','result':result,'findings':'Recorded'}]}).insert()

    def rows(self,view='All'):
        return reports.register({'view':view,'work_order':self.order.name})

    def test_open_overdue_unscheduled_and_closed_are_distinct(self):
        frappe.set_user(self.users['supervisor']);self.assertEqual(len(self.rows('Open')),1);self.assertEqual(len(self.rows('Overdue')),1);self.assertEqual(self.rows('Unscheduled'),[])
        self.entry();life.perform(self.order.name,'Complete Work','Complete')
        frappe.set_user(self.users['requester']);life.perform(self.order.name,'Accept Work','Accepted')
        frappe.set_user(self.users['supervisor']);life.perform(self.order.name,'Close Order','Closed')
        self.assertEqual(self.rows('Open'),[]);self.assertEqual(self.rows('Overdue'),[]);self.assertEqual(len(self.rows('Closed')),1)

    def test_no_target_is_not_overdue(self):
        frappe.set_user('Administrator');frappe.db.set_value(wo.DT,self.order.name,'target_closure',None)
        self.assertEqual(self.rows('Overdue'),[]);self.assertEqual(len(self.rows('Unscheduled')),1)

    def test_effective_minutes_reconcile_and_do_not_duplicate_task_rows(self):
        entry=self.entry();frappe.set_user(self.users['supervisor']);rows=self.rows();self.assertAlmostEqual(rows[0].effective_minutes,10)
        void=adj.void_entry(entry.name,'Incorrect time entry');again=adj.void_entry(entry.name,'Retry')
        self.assertEqual(void.name,again.name)
        rows=self.rows();self.assertAlmostEqual(rows[0].recorded_minutes,10);self.assertAlmostEqual(rows[0].voided_minutes,10);self.assertEqual(rows[0].effective_minutes,0)
        self.assertTrue(frappe.db.exists('TruCMMS Work Execution',entry.name))
        replacement=self.entry();self.assertNotEqual(replacement.name,entry.name)
        frappe.set_user(self.users['supervisor']);row=self.rows()[0];self.assertAlmostEqual(row.recorded_minutes,20);self.assertAlmostEqual(row.effective_minutes,10)

    def test_void_requires_supervisor_and_reason(self):
        entry=self.entry()
        with self.assertRaises(frappe.PermissionError):adj.void_entry(entry.name,'Wrong duration')
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.ValidationError):adj.void_entry(entry.name,' ')
        adj.void_entry(entry.name,'Wrong duration')
        frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.PermissionError):save_file(self.token+'.txt',b'Late evidence','TruCMMS Work Execution',entry.name,is_private=1)
        with self.assertRaises(frappe.ValidationError):life.perform(self.order.name,'Complete Work','No effective work')

    def test_void_and_adjustment_history_are_immutable(self):
        entry=self.entry();frappe.set_user(self.users['supervisor']);data=adj.void_entry(entry.name,'Wrong duration')
        doc=frappe.get_doc(adj.DT,data.name);frappe.set_user('Administrator');doc.reason='Rewrite'
        with self.assertRaises(frappe.PermissionError):doc.save(ignore_permissions=True)
        with self.assertRaises(frappe.PermissionError):frappe.delete_doc(adj.DT,doc.name)

    def test_report_and_adjustment_visibility_follow_scope_and_assignment(self):
        entry=self.entry();frappe.set_user(self.users['supervisor']);adj.void_entry(entry.name,'Wrong duration')
        frappe.set_user(self.users['other']);self.assertEqual(self.rows(),[]);self.assertEqual(frappe.get_list(adj.DT,filters={'work_order':self.order.name},pluck='name'),[])
        frappe.set_user('Administrator')
        for name in frappe.get_all('User Permission',filters={'user':self.users['supervisor']},pluck='name'):frappe.delete_doc('User Permission',name)
        frappe.set_user(self.users['supervisor']);self.assertEqual(self.rows(),[])
        with self.assertRaises(frappe.PermissionError):adj.void_entry(entry.name,'No scope')

    def test_completed_order_cannot_have_time_voided(self):
        entry=self.entry();life.perform(self.order.name,'Complete Work','Complete')
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.ValidationError):adj.void_entry(entry.name,'Late correction')

    def test_equipment_history_preserves_original_links(self):
        frappe.set_user('Administrator');category=frappe.get_doc({'doctype':'VB Equipment Category','category_name':self.token}).insert()
        equipment=frappe.get_doc({'doctype':'VB Equipment','company':self.order.company,'site':self.order.site,'equipment_code':self.token.upper(),'equipment_name':'Pilot equipment','category':category.name}).insert()
        # Historical links set only in this fixture; operating controllers prohibit rebinding.
        frappe.db.set_value(wo.DT,self.order.name,'equipment',equipment.name)
        frappe.db.set_value('TruCMMS Maintenance Request',self.request.name,'equipment',equipment.name)
        entry=self.entry();frappe.set_user(self.users['supervisor']);adj.void_entry(entry.name,'Incorrect record')
        columns,rows,message=reports.equipment_history({'equipment':equipment.name})
        kinds={r['record_type'] for r in rows};self.assertIn(wo.DT,kinds);self.assertIn('TruCMMS Maintenance Request',kinds);self.assertIn('TruCMMS Work Execution',kinds);self.assertIn(adj.DT,kinds)
        self.assertTrue(all(r['site']==self.order.site for r in rows))

    def test_report_filters_and_summary_match_rows(self):
        self.entry();frappe.set_user(self.users['supervisor']);columns,rows,message,chart,summary=reports.work_register({'work_order':self.order.name,'view':'All'})
        self.assertEqual(summary[0]['value'],len(rows));self.assertAlmostEqual(summary[3]['value'],sum(r.effective_minutes for r in rows))
        with self.assertRaises(frappe.ValidationError):reports.register({'view':'Forged'})
        with self.assertRaises(frappe.ValidationError):reports.register({'from_date':'2026-10-25','to_date':'2026-10-24'})

    def test_target_is_frozen_and_accepts_full_desk_datetime(self):
        frappe.set_user(self.users['supervisor']);payload=frappe.parse_json(frappe.as_json(self.order.as_dict()));doc=frappe.get_doc(payload);doc.save()
        doc.target_closure=add_to_date(now_datetime(),days=5)
        with self.assertRaises(frappe.ValidationError):doc.save()

    def test_more_than_twenty_entries_are_fully_reconciled(self):
        frappe.set_user(self.users['tech'])
        start=add_to_date(now_datetime(),hours=-2)
        for index in range(21):
            a=add_to_date(start,seconds=index*30)
            frappe.get_doc({'doctype':'TruCMMS Work Execution','work_order':self.order.name,'actual_start':a,'actual_end':add_to_date(a,seconds=10),'findings':'Batch check','tasks':[{'task':'Inspect','result':'Completed','findings':'Passed'}]}).insert()
        frappe.set_user(self.users['supervisor']);row=self.rows()[0]
        self.assertEqual(row.execution_count,21)
        self.assertAlmostEqual(row.effective_minutes,sum(frappe.get_all('TruCMMS Work Execution',filters={'work_order':self.order.name},pluck='actual_minutes')))

    def test_four_sector_common_corrective_scenarios(self):
        from frappe.model.workflow import apply_workflow
        for index,(sector,equipment_name) in enumerate([('Fleet','Delivery vehicle'),('Manufacturing','Production pump'),('Laboratory','Laboratory instrument'),('Facilities','Air handling unit')]):
            frappe.set_user('Administrator');category=frappe.get_doc({'doctype':'VB Equipment Category','category_name':self.token+sector}).insert()
            equipment=frappe.get_doc({'doctype':'VB Equipment','company':self.order.company,'site':self.order.site,'equipment_code':(self.token+'-'+sector).upper(),'equipment_name':equipment_name,'category':category.name}).insert()
            frappe.set_user(self.users['requester'])
            request=frappe.get_doc({'doctype':'TruCMMS Maintenance Request','company':self.order.company,'site':self.order.site,'equipment':equipment.name,'subject':sector+' fault','description':'Functional failure','priority':'High'}).insert()
            request=apply_workflow(request.as_dict(),'Send Request');frappe.set_user(self.users['dispatcher']);request=apply_workflow(request.as_dict(),'Triage');request=apply_workflow(request.as_dict(),'Approve')
            order=frappe.get_doc(wo.from_request(request.name));frappe.set_user(self.users['supervisor']);order=apply_workflow(order.as_dict(),'Authorize');order.assigned_to=self.users['tech'];order.save();order=apply_workflow(order.as_dict(),'Assign')
            frappe.set_user('Administrator');frappe.db.set_value(wo.DT,order.name,'assigned_on',add_to_date(now_datetime(),hours=-3))
            frappe.set_user(self.users['tech']);start=add_to_date(now_datetime(),minutes=-150+index*20)
            frappe.get_doc({'doctype':'TruCMMS Work Execution','work_order':order.name,'actual_start':start,'actual_end':add_to_date(start,minutes=10),'findings':'Function restored','tasks':[{'task':'Repair and test','result':'Completed','findings':'Passed'}]}).insert()
            life.perform(order.name,'Complete Work','Functional test passed');frappe.set_user(self.users['requester']);life.perform(order.name,'Accept Work','Service verified');frappe.set_user(self.users['supervisor']);life.perform(order.name,'Close Order','History checked')
            rows=reports.register({'view':'Closed','equipment':equipment.name});self.assertEqual(len(rows),1);self.assertAlmostEqual(rows[0].effective_minutes,10)
            columns,history,message=reports.equipment_history({'equipment':equipment.name});self.assertEqual(sum(r['record_type']==life.EVENT for r in history),3)
