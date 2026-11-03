import uuid
from datetime import datetime,timedelta
import frappe
from vanbags_maintenance import resource_calendars as r,capacity as c
from vanbags_maintenance.test_support import COMPANY_A,SITE_A,SITE_A2,grant_scope
from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase

class TestResourceCalendars(WorkOrderCase):
    def setUp(self):
        super().setUp();frappe.set_user('Administrator');frappe.db.set_value('TruCMMS Site',SITE_A,'time_zone','UTC')
    def calendar(self,slots=None,holiday=None,admin=False,**extra):
        frappe.set_user('Administrator' if admin else self.users['supervisor'])
        values=dict(doctype=r.CALENDAR,code=self.token+'-'+uuid.uuid4().hex[:6],calendar_name='Synthetic weekly roster',company=COMPANY_A,site=SITE_A,
            dst_occurrence='First',holiday_list=holiday,slots=slots or [dict(weekday='Monday',starts_at='08:00:00',ends_at='12:00:00'),dict(weekday='Monday',starts_at='13:00:00',ends_at='17:00:00')])
        values.update(extra)
        return frappe.get_doc(values).insert()
    def assignment(self,calendar=None,first='2027-02-01',last='2027-02-28'):
        calendar=calendar or self.calendar();frappe.set_user(self.users['supervisor'])
        return frappe.get_doc(dict(doctype=r.ASSIGNMENT,company=COMPANY_A,site=SITE_A,calendar=calendar.name,technician=self.users['tech'],from_date=first,to_date=last,reason='Synthetic roster assignment')).insert()
    def generate(self,doc,first='2027-02-01',last='2027-02-07',admin=False):
        frappe.set_user('Administrator' if admin else self.users['supervisor'])
        return r.generate(doc.name,first,last,'Synthetic weekly generation')
    def holiday(self,dates):
        frappe.set_user('Administrator')
        return frappe.get_doc(dict(doctype='Holiday List',holiday_list_name=self.token,from_date='2027-01-01',to_date='2027-12-31',
            holidays=[dict(holiday_date=date,description='Synthetic holiday') for date in dates])).insert()
    def report(self,first='2027-02-01',last='2027-02-07'):
        return c.overview(COMPANY_A,SITE_A,self.users['tech'],first,last)['days']
    def test_weekly_split_shifts_and_zero_days_are_known(self):
        doc=self.assignment();self.assertIsNone(self.report()[0]['available_hours'])
        event=self.generate(doc);self.assertEqual(event['window_count'],2)
        days=self.report();self.assertEqual(days[0]['available_hours'],8)
        self.assertEqual([d['available_hours'] for d in days[1:]],[0]*6)
        self.assertTrue(all(d['configured'] for d in days))
    def test_night_shift_spans_site_days(self):
        calendar=self.calendar([dict(weekday='Monday',starts_at='22:00:00',ends_at='06:00:00',next_day=1)])
        self.generate(self.assignment(calendar));days=self.report()
        self.assertEqual([days[i]['available_hours'] for i in (0,1)],[2,6])
    def test_holiday_clips_only_the_affected_day_of_overnight_work(self):
        holiday=self.holiday(['2027-02-02'])
        calendar=self.calendar([dict(weekday='Monday',starts_at='22:00:00',ends_at='06:00:00',next_day=1)],holiday.name,admin=True)
        event=self.generate(self.assignment(calendar),admin=True);self.assertEqual(event['window_count'],1)
        days=self.report();self.assertEqual([days[i]['available_hours'] for i in (0,1)],[2,0])
    def test_retry_preserves_generation_and_rejects_partial_overlap(self):
        doc=self.assignment();first=self.generate(doc);again=self.generate(doc)
        self.assertEqual(first['name'],again['name']);self.assertFalse(again['created'])
        self.assertEqual(frappe.db.count(c.DT,{'calendar_assignment':doc.name}),2)
        with self.assertRaises(frappe.ValidationError):self.generate(doc,'2027-02-07','2027-02-14')
    def test_absence_subtracts_from_generated_capacity(self):
        doc=self.assignment();self.generate(doc)
        start=c.server(datetime.fromisoformat('2027-02-01T09:00:00+00:00'))
        frappe.get_doc(dict(doctype=c.DT,company=COMPANY_A,site=SITE_A,technician=self.users['tech'],kind='Unavailable',starts_on=start,ends_on=start+timedelta(hours=2),reason='Synthetic absence')).insert()
        self.assertEqual(self.report()[0]['available_hours'],6)
    def test_generated_provenance_and_times_cannot_be_forged(self):
        doc=self.assignment();event=self.generate(doc)
        window=frappe.get_doc(c.DT,frappe.db.get_value(c.DT,{'calendar_generation':event['name']},'name'))
        window.starts_on+=timedelta(minutes=1)
        with self.assertRaises(frappe.PermissionError):window.save()
        window.reload();window.disabled=1
        with self.assertRaises(frappe.ValidationError):window.save()
        window.reload();window.disabled=1;window.reason='Explicit exception cancels this shift';window.save()
        self.assertEqual(self.report()[0]['available_hours'],4)
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc(dict(doctype=c.DT,company=COMPANY_A,site=SITE_A,technician=self.users['tech'],kind='Working',starts_on='2027-02-03 08:00:00',ends_on='2027-02-03 09:00:00',reason='Forged origin',calendar_key='forged')).insert()
    def test_used_pattern_and_generation_history_are_immutable(self):
        calendar=self.calendar();doc=self.assignment(calendar);event=self.generate(doc)
        calendar.reload().slots[0].starts_at='07:00:00'
        with self.assertRaises(frappe.ValidationError):calendar.save()
        history=frappe.get_doc(r.GENERATION,event['name']);history.reason='Rewrite history'
        with self.assertRaises(frappe.PermissionError):history.save()
    def test_read_and_generation_permissions(self):
        doc=self.assignment();self.generate(doc)
        frappe.set_user(self.users['tech']);self.assertEqual(frappe.get_list(r.ASSIGNMENT,pluck='name'),[doc.name])
        with self.assertRaises(frappe.PermissionError):r.generate(doc.name,'2027-02-08','2027-02-14','Unauthorized')
        frappe.set_user(self.users['other']);self.assertEqual(frappe.get_list(r.GENERATION,pluck='name'),[])
        frappe.set_user(self.users['dispatcher'])
        with self.assertRaises(frappe.PermissionError):r.generate(doc.name,'2027-02-08','2027-02-14','Dispatcher cannot configure')
    def test_disabled_assignment_does_not_erase_existing_windows(self):
        doc=self.assignment();self.generate(doc);doc.reload();doc.disabled=1
        with self.assertRaises(frappe.ValidationError):doc.save()
        doc.reload();doc.disabled=1;doc.reason='Stop future generation';doc.save()
        with self.assertRaises(frappe.ValidationError):self.generate(doc,'2027-02-08','2027-02-14')
        self.assertEqual(self.report()[0]['available_hours'],8)
    def test_overlapping_assignments_and_pattern_slots_rejected(self):
        self.assignment()
        with self.assertRaises(frappe.ValidationError):self.assignment()
        with self.assertRaises(frappe.ValidationError):self.calendar([dict(weekday='Sunday',starts_at='22:00:00',ends_at='06:00:00',next_day=1),dict(weekday='Monday',starts_at='05:00:00',ends_at='08:00:00')])
    def test_dst_gap_is_atomic_and_real_night_duration_is_preserved(self):
        frappe.set_user('Administrator');frappe.db.set_value('TruCMMS Site',SITE_A,'time_zone','America/New_York')
        calendar=self.calendar([dict(weekday='Sunday',starts_at='02:30:00',ends_at='04:00:00')])
        doc=self.assignment(calendar,'2027-03-01','2027-03-31')
        with self.assertRaises(frappe.ValidationError):self.generate(doc,'2027-03-14','2027-03-14')
        self.assertEqual(frappe.db.count(r.GENERATION,{'assignment':doc.name}),0)
        doc.disabled=1;doc.reason='Replace impossible wall-time pattern';doc.save()
        calendar=self.calendar([dict(weekday='Saturday',starts_at='22:00:00',ends_at='06:00:00',next_day=1)])
        doc=self.assignment(calendar,'2027-03-01','2027-03-31');self.generate(doc,'2027-03-13','2027-03-14')
        self.assertEqual(sum(d['available_hours'] for d in self.report('2027-03-13','2027-03-14')),7)
    def test_foreign_working_window_conflict_rolls_back_generation(self):
        frappe.set_user('Administrator');grant_scope(self.users['tech'],site=SITE_A2)
        start=c.server(datetime.fromisoformat('2027-02-01T08:00:00+00:00'))
        frappe.get_doc(dict(doctype=c.DT,company=COMPANY_A,site=SITE_A2,technician=self.users['tech'],kind='Working',starts_on=start,ends_on=start+timedelta(hours=8),reason='Other Site existing commitment')).insert()
        doc=self.assignment()
        with self.assertRaises(frappe.ValidationError):self.generate(doc)
        self.assertEqual(frappe.db.count(r.GENERATION,{'assignment':doc.name}),0)
        self.assertEqual(frappe.db.count(c.DT,{'calendar_assignment':doc.name}),0)
    def test_same_pattern_can_be_reused_for_two_people(self):
        calendar=self.calendar();first=self.assignment(calendar);self.generate(first)
        second=frappe.get_doc(dict(doctype=r.ASSIGNMENT,company=COMPANY_A,site=SITE_A,technician=self.users['other'],calendar=calendar.name,from_date='2027-02-01',to_date='2027-02-28',reason='Reuse approved pattern')).insert()
        self.generate(second)
        self.assertEqual(frappe.db.count(c.DT,{'calendar_assignment':['in',[first.name,second.name]]}),4)
    def test_native_holiday_permission_is_not_bypassed(self):
        holiday=self.holiday(['2027-02-02']);calendar=self.calendar(holiday=holiday.name,admin=True);doc=self.assignment(calendar)
        frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.PermissionError):frappe.get_doc('Holiday List',holiday.name).check_permission('read')
        # A supervisor without native Holiday List access cannot materialize its dates.
        with self.assertRaises(frappe.PermissionError):self.generate(doc)
        self.assertEqual(frappe.db.count(r.GENERATION,{'assignment':doc.name}),0)
        frappe.set_user('Administrator');frappe.get_doc('Holiday List',holiday.name).check_permission('read')
        self.assertEqual(self.generate(doc,admin=True)['window_count'],2)
    def test_holiday_edits_affect_only_new_generation_periods(self):
        holiday=self.holiday(['2027-02-02']);doc=self.assignment(self.calendar(holiday=holiday.name,admin=True))
        first=self.generate(doc,admin=True)
        frappe.set_user('Administrator');holiday.append('holidays',dict(holiday_date='2027-02-01',description='Changed after generation'));holiday.append('holidays',dict(holiday_date='2027-02-08',description='Future holiday'));holiday.save()
        again=self.generate(doc,admin=True);self.assertFalse(again['created']);self.assertEqual(again['name'],first['name'])
        self.assertEqual(self.report()[0]['available_hours'],8)
        future=self.generate(doc,'2027-02-08','2027-02-14',admin=True);self.assertEqual(future['window_count'],0)
        self.assertEqual(self.report('2027-02-08','2027-02-14')[0]['available_hours'],0)
    def test_ambiguous_dst_occurrence_policy_is_explicit(self):
        frappe.set_user('Administrator');frappe.db.set_value('TruCMMS Site',SITE_A,'time_zone','America/New_York')
        slots=[dict(weekday='Sunday',starts_at='01:30:00',ends_at='02:30:00')]
        first=self.assignment(self.calendar(slots),'2027-11-07','2027-11-07');self.generate(first,'2027-11-07','2027-11-07')
        calendar=self.calendar(slots,dst_occurrence='Second')
        second=frappe.get_doc(dict(doctype=r.ASSIGNMENT,company=COMPANY_A,site=SITE_A,technician=self.users['other'],calendar=calendar.name,from_date='2027-11-07',to_date='2027-11-07',reason='Second occurrence roster')).insert()
        self.generate(second,'2027-11-07','2027-11-07')
        self.assertEqual(self.report('2027-11-07','2027-11-07')[0]['available_hours'],2)
        self.assertEqual(c.overview(COMPANY_A,SITE_A,self.users['other'],'2027-11-07','2027-11-07')['days'][0]['available_hours'],1)
