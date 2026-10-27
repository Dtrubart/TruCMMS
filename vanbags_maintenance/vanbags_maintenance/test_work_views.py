import json,uuid
from datetime import datetime,timezone
from vanbags_maintenance.timezones import zone as ZoneInfo
from unittest.mock import patch
import frappe
from frappe.utils import now_datetime,add_to_date
from vanbags_maintenance import work_views as views,work_orders as wo,allocations,submission,work_contract
from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase

class ViewCase(WorkOrderCase):
    use_c_policy=True
    def setUp(self):
        super().setUp();self.order=self.assign();frappe.set_user('Administrator');self.system=ZoneInfo(frappe.db.get_single_value('System Settings','time_zone') or 'UTC')
        self.site=self.order.site;site=frappe.get_doc('TruCMMS Site',self.site);site.time_zone='America/Vancouver';site.save()
        past=add_to_date(now_datetime(),hours=-3);frappe.db.set_value(wo.DT,self.order.name,'assigned_on',past)
        for row in allocations.active(self.order):frappe.db.set_value(allocations.DT,row.name,'assigned_on',past)
    def schedule(self,start='2025-11-02T08:30:00+00:00',end='2025-11-02T10:30:00+00:00',target='2025-11-04T08:00:00+00:00'):
        def stored(x):return datetime.fromisoformat(x).astimezone(self.system).replace(tzinfo=None) if x else None
        frappe.set_user('Administrator');frappe.db.set_value(wo.DT,self.order.name,{'scheduled_start':stored(start),'scheduled_end':stored(end),'target_closure':stored(target)})
    def feed(self,role='tech',**filters):
        frappe.set_user(self.users[role]);return views.get_work({'site':self.site,'status':'All',**filters})

class TestWorkViews(ViewCase):
    def test_list_uses_native_permission_scope(self):
        self.assertEqual([r.name for r in self.feed()['rows']],[self.order.name]);self.assertEqual(self.feed('other')['rows'],[])
    def test_my_work_includes_secondary_and_revokes_removed_allocation(self):
        self.assertEqual(len(self.feed(mode='My Work')['rows']),1);self.assertEqual(self.feed('other',mode='My Work')['rows'],[])
        frappe.set_user(self.users['supervisor']);row=allocations.add(self.order.name,self.users['other'],self.discipline,'E secondary work')
        self.assertTrue(self.feed('other',mode='My Work')['rows'][0].execution_candidate)
        frappe.set_user(self.users['supervisor']);allocations.remove(row['name'],'E removal');self.assertEqual(self.feed('other',mode='My Work')['rows'],[])
    def test_requester_my_work_does_not_mean_own_requests(self):self.assertEqual(self.feed('requester',mode='My Work')['rows'],[])
    def test_calendar_and_agenda_share_rows_and_explicit_offsets(self):
        self.schedule();filters=dict(basis='Scheduled',from_date='2025-11-02',to_date='2025-11-02')
        a=self.feed(mode='Date Agenda',**filters);b=self.feed(mode='Calendar',**filters);self.assertEqual(a['rows'],b['rows']);row=a['rows'][0];self.assertEqual(row.local_days,['2025-11-02']);self.assertTrue(row.scheduled_start.endswith('+00:00'));self.assertTrue(row.scheduled_start_local.endswith('-07:00'));self.assertTrue(row.scheduled_end_local.endswith('-08:00'))
    def test_dst_days_are_23_and_25_hours(self):
        zone=ZoneInfo('America/Vancouver')
        for day,hours in [('2025-03-09',23),('2025-11-02',25)]:
            result=views.dates({'from_date':day,'to_date':day},zone);self.assertEqual((result[3]-result[2]).total_seconds()/3600,hours)
    def test_overnight_schedule_groups_each_occupied_local_day(self):
        self.schedule('2025-11-02T06:00:00+00:00','2025-11-02T10:00:00+00:00')
        row=self.feed(mode='Calendar',basis='Scheduled',from_date='2025-11-01',to_date='2025-11-02')['rows'][0];self.assertEqual(row.local_days,['2025-11-01','2025-11-02'])
    def test_end_at_midnight_does_not_occupy_next_day(self):
        self.schedule('2025-11-02T06:00:00+00:00','2025-11-02T07:00:00+00:00')
        self.assertEqual(self.feed(mode='Calendar',basis='Scheduled',from_date='2025-11-02',to_date='2025-11-02')['rows'],[])
    def test_closure_is_a_separate_milestone_not_execution_duration(self):
        self.schedule();result=self.feed(mode='Calendar',basis='Closure Target',from_date='2025-11-04',to_date='2025-11-04');self.assertEqual(len(result['rows']),1);self.assertTrue(result['events'][0]['milestone']);self.assertIsNone(result['events'][0]['end'])
    def test_without_schedule_uses_schedule_fields_not_closure_target(self):
        self.schedule(None,None);self.assertEqual(len(self.feed(basis='Without Schedule')['rows']),1)
        self.schedule();self.assertEqual(self.feed(basis='Without Schedule')['rows'],[])
    def test_invalid_filter_mode_range_and_actor_override_rejected(self):
        for filters in [{'user':self.users['other']},{'mode':'Admin'},{'mode':'Calendar','basis':'All'},{'basis':'Scheduled','from_date':'2026-01-01','to_date':'2026-12-31'},{'site':['in',[self.site]]}]:
            with self.assertRaises(frappe.ValidationError):self.feed(**filters)
    def test_closed_work_not_in_actionable_my_work(self):
        frappe.db.set_value(wo.DT,self.order.name,'status','Closed');self.assertEqual(self.feed(mode='My Work')['rows'],[])
    def test_secondary_is_available_in_native_execution_link_query(self):
        frappe.set_user(self.users['supervisor']);allocations.add(self.order.name,self.users['other'],self.discipline,'E link query')
        frappe.set_user(self.users['other']);rows=views.execution_order_query(wo.DT,'','name',0,20);self.assertEqual(rows[0][0],self.order.name)
    def test_bounded_feed_explicitly_reports_truncation(self):
        frappe.set_user(self.users['dispatcher'])
        for i in range(3):work_contract.create_direct(self.order.company,self.site,'E bounded '+str(i),'E scope','Medium',uuid.uuid4().hex,'Bounded feed verification',functional_location=self.location.name)
        with patch.object(views,'CAP',2):
            result=self.feed('dispatcher');self.assertEqual(len(result['rows']),2);self.assertTrue(result['truncated']);self.assertEqual(result['limit'],2)
    def test_read_views_do_not_change_order_or_audit(self):
        before=frappe.db.get_value(wo.DT,self.order.name,'modified');count=frappe.db.count('TruCMMS Work Event',{'work_order':self.order.name});self.feed();self.feed(mode='My Work');self.assertEqual(frappe.db.get_value(wo.DT,self.order.name,'modified'),before);self.assertEqual(frappe.db.count('TruCMMS Work Event',{'work_order':self.order.name}),count)
    def test_ambiguous_storage_timestamp_fails_explicitly(self):
        with self.assertRaises(frappe.ValidationError):views.instant('2025-11-02 01:30:00',ZoneInfo('America/Vancouver'))

class TestExecutionSubmission(ViewCase):
    def payload(self):
        return dict(work_order=self.order.name,actual_start=str(add_to_date(now_datetime(),minutes=-40)),actual_end=str(add_to_date(now_datetime(),minutes=-30)),findings='E retry-safe execution',tasks=[dict(task='Inspect',result='Completed',findings='Passed')])
    def test_same_submission_returns_original_and_preserves_one_execution(self):
        values=self.payload();key=str(uuid.uuid4());frappe.set_user(self.users['tech']);first=submission.submit(values,key);second=submission.submit(values,key);self.assertEqual(first['name'],second['name']);self.assertEqual(frappe.db.count(submission.EX,{'work_order':self.order.name}),1)
    def test_changed_retry_is_rejected_without_another_record(self):
        values=self.payload();key=str(uuid.uuid4());frappe.set_user(self.users['tech']);submission.submit(values,key);values['findings']='Changed after confirmation lost'
        with self.assertRaises(frappe.ValidationError):submission.submit(values,key)
        self.assertEqual(frappe.db.count(submission.EX,{'work_order':self.order.name}),1)
    def test_validation_failure_can_be_corrected_with_same_key(self):
        values=self.payload();key=str(uuid.uuid4());original=values['actual_end'];values['actual_end']=values['actual_start'];frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.ValidationError):submission.submit(values,key)
        self.assertFalse(frappe.db.exists(submission.EX,{'work_order':self.order.name}));values['actual_end']=original;self.assertTrue(submission.submit(values,key)['name'])
    def test_unassigned_technician_and_forged_hidden_fields_are_rejected(self):
        values=self.payload();frappe.set_user(self.users['other'])
        with self.assertRaises(frappe.PermissionError):submission.submit(values,str(uuid.uuid4()))
        frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.PermissionError):frappe.get_doc({'doctype':submission.EX,**values,'submission_key':'forged','submission_digest':'forged'}).insert()
    def test_readable_saved_retry_survives_order_completion(self):
        values=self.payload();key=str(uuid.uuid4());frappe.set_user(self.users['tech']);first=submission.submit(values,key);frappe.set_user('Administrator');frappe.db.set_value(wo.DT,self.order.name,'status','Technical Completed');frappe.set_user(self.users['tech']);self.assertEqual(submission.submit(values,key)['name'],first['name'])
    def test_submission_rejects_injected_context_and_invalid_key(self):
        values=self.payload();frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.ValidationError):submission.submit(values,'bad')
        values['technician']=self.users['other']
        with self.assertRaises(frappe.ValidationError):submission.submit(values,str(uuid.uuid4()))


class TestCurrentTimezoneRules(WorkOrderCase):
    def test_browser_and_backend_ship_the_same_official_timezone_data(self):
        from vanbags_maintenance.timezones import RULES_VERSION,zone
        from pathlib import Path
        import tzdata,vanbags_maintenance
        text=(Path(vanbags_maintenance.__file__).parent/'public/js/timezone_rules.js').read_text()
        data=json.loads(text.split('const data=',1)[1].split(';if(window.moment',1)[0])
        self.assertEqual(data['version'],RULES_VERSION);self.assertEqual(tzdata.IANA_VERSION,RULES_VERSION)
        self.assertEqual(zone('America/Vancouver').key,'America/Vancouver')

    def test_vancouver_no_longer_falls_back_in_november_2026(self):
        zone=ZoneInfo('America/Vancouver');result=views.dates({'from_date':'2026-11-01','to_date':'2026-11-01'},zone)
        self.assertEqual((result[3]-result[2]).total_seconds()/3600,24)
        self.assertEqual(views.instant('2026-11-01 01:30:00',zone),datetime(2026,11,1,8,30,tzinfo=timezone.utc))

    def test_mismatched_platform_storage_clock_is_explicitly_blocked(self):
        from vanbags_maintenance import timezones
        from datetime import timedelta
        system=frappe.db.get_single_value('System Settings','time_zone') or 'UTC';timezones.zone(system)
        with patch.object(timezones,'ZoneInfo',return_value=timezone(timedelta(hours=13))):
            with self.assertRaises(frappe.ValidationError):timezones.assert_storage_clock()
