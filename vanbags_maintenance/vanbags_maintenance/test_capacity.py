from datetime import datetime,timedelta,timezone
import frappe
from vanbags_maintenance import capacity as c,organization as org
from vanbags_maintenance.test_support import COMPANY_A,SITE_A,SITE_A2
from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase

class TestCapacity(WorkOrderCase):
    use_c_policy=True
    def setUp(self):
        super().setUp();frappe.set_user('Administrator')
        frappe.db.set_value('TruCMMS Site',SITE_A,'time_zone','UTC')
        self.start=c.server(datetime(2027,2,1,8,tzinfo=timezone.utc));self.end=self.start+timedelta(hours=8)
    def window(self,kind='Working',start=None,end=None,technician=None,site=SITE_A):
        frappe.set_user(self.users['supervisor'])
        return frappe.get_doc(dict(doctype=c.DT,company=COMPANY_A,site=site,technician=technician or self.users['tech'],kind=kind,
            starts_on=start or self.start,ends_on=end or self.end,reason='Synthetic availability configuration')).insert()
    def report(self,**kw):
        return c.overview(COMPANY_A,SITE_A,self.users['tech'],'2027-02-01','2027-02-01',**kw)
    def scheduled(self,start=None,end=None,technician=None):
        order=self.assign();frappe.set_user('Administrator')
        frappe.db.set_value(order.doctype,order.name,{'scheduled_start':start or self.start,'scheduled_end':end or self.end})
        return order
    def test_explicit_working_hours_and_unconfigured_days(self):
        frappe.set_user(self.users['supervisor']);self.assertIsNone(self.report()['days'][0]['available_hours'])
        self.window();self.assertEqual(self.report()['days'][0]['available_hours'],8)
    def test_overlapping_absence_subtracts_only_covered_shift(self):
        self.window();self.window('Unavailable',self.start-timedelta(hours=2),self.start+timedelta(hours=2))
        self.assertEqual(self.report()['days'][0]['available_hours'],6)
    def test_overnight_shift_splits_on_site_calendar_days(self):
        self.window(start=self.start+timedelta(hours=14),end=self.start+timedelta(hours=22))
        rows=c.overview(COMPANY_A,SITE_A,self.users['tech'],'2027-02-01','2027-02-02')['days']
        self.assertEqual([r['available_hours'] for r in rows],[2,6])
    def test_load_free_time_overlap_and_outside_hours(self):
        self.window();self.scheduled(self.start-timedelta(hours=1),self.start+timedelta(hours=2))
        frappe.set_user(self.users['supervisor']);row=self.report()['days'][0]
        self.assertEqual((row['scheduled_hours'],row['outside_hours'],row['free_hours']),(3,1,6))
    def test_second_participant_load_and_conflicts_are_not_duplicated(self):
        from vanbags_maintenance import allocations
        self.window();order=self.scheduled();frappe.set_user(self.users['supervisor'])
        allocations.add(order.name,self.users['other'],self.discipline,'Second specialist')
        self.assertEqual(self.report()['days'][0]['scheduled_hours'],8)
        other=c.overview(COMPANY_A,SITE_A,self.users['other'],'2027-02-01','2027-02-01')
        self.assertEqual(other['days'][0]['scheduled_hours'],8)
    def test_duplicate_windows_rejected_and_disabled_windows_excluded(self):
        row=self.window()
        with self.assertRaises(frappe.ValidationError):self.window()
        row.disabled=1;row.reason='Shift cancelled';row.save();self.assertIsNone(self.report()['days'][0]['available_hours'])
    def test_technician_only_reads_own_windows_and_cannot_edit(self):
        row=self.window();self.window(technician=self.users['other']);frappe.set_user(self.users['tech'])
        self.assertEqual(frappe.get_list(c.DT,pluck='name'),[row.name])
        with self.assertRaises(frappe.PermissionError):row.save()
    def test_requester_and_foreign_scope_denied(self):
        self.window();frappe.set_user(self.users['requester'])
        with self.assertRaises(frappe.PermissionError):self.report()
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.PermissionError):c.overview(COMPANY_A,SITE_A2,self.users['tech'],'2027-02-01','2027-02-01')
    def test_dst_site_day_has_real_elapsed_duration(self):
        frappe.set_user('Administrator');frappe.db.set_value('TruCMMS Site',SITE_A,'time_zone','America/New_York')
        begin=datetime.fromisoformat(c.configuration.local_instant('2027-03-14 00:00:00',SITE_A,fold=0))
        end=datetime.fromisoformat(c.configuration.local_instant('2027-03-15 00:00:00',SITE_A,fold=0))
        self.window(start=c.server(begin),end=c.server(end))
        self.assertEqual(c.overview(COMPANY_A,SITE_A,self.users['tech'],'2027-03-14','2027-03-14')['days'][0]['available_hours'],23)
    def test_window_history_share_and_invalid_dates(self):
        row=self.window()
        with self.assertRaises(frappe.PermissionError):frappe.delete_doc(c.DT,row.name)
        with self.assertRaises(frappe.PermissionError):frappe.share.add(c.DT,row.name,user=self.users['other'])
        with self.assertRaises(frappe.ValidationError):self.window(start=self.end,end=self.start)

    def test_two_real_orders_report_overload_and_overlap(self):
        from frappe.model.workflow import apply_workflow
        self.window();self.scheduled()
        frappe.set_user(self.users['requester'])
        request=frappe.get_doc(dict(doctype='TruCMMS Maintenance Request',company=COMPANY_A,site=SITE_A,
            subject='Independent second fault',description='Another maintenance demand',functional_location=self.location.name,priority='High')).insert()
        request=apply_workflow(request.as_dict(),'Send Request')
        frappe.set_user(self.users['dispatcher']);request=apply_workflow(request.as_dict(),'Triage');self.request=apply_workflow(request.as_dict(),'Approve')
        self.scheduled();frappe.set_user(self.users['supervisor']);day=self.report()['days'][0]
        self.assertEqual((day['scheduled_hours'],day['overload_hours'],day['overlap_hours'],day['free_hours']),(16,8,8,0))
