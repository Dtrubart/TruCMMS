import frappe
from frappe.model.workflow import apply_workflow
from frappe.utils import now_datetime,add_to_date
from vanbags_maintenance import teams,configuration,work_orders as wo,execution
from vanbags_maintenance.test_support import grant_scope,COMPANY_A,COMPANY_B,SITE_A,SITE_A2,SITE_B
from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase

class TestTeams(WorkOrderCase):
    def admin(self):frappe.set_user('Administrator')
    def member(self):return frappe.get_doc(teams.MEMBER,self.memberships['tech'])
    def grant(self):return frappe.get_doc(teams.GRANT,self.site_grant)

    def test_new_orders_cannot_choose_legacy_policy(self):
        doc=self.make();self.assertEqual(doc.team_policy,'Managed')
        doc.team_policy='Legacy'
        with self.assertRaises(frappe.PermissionError):doc.save()

    def test_assignment_requires_team_and_discipline(self):
        doc=self.authorize();doc.responsible_team=None;doc.required_discipline=None;doc.assigned_to=self.users['tech']
        with self.assertRaises(frappe.ValidationError):doc.save()

    def test_assignment_records_immutable_eligibility_snapshot(self):
        doc=self.assign();self.assertTrue(doc.team_assignment)
        self.admin();row=frappe.get_doc(teams.ASSIGN,doc.team_assignment)
        self.assertEqual(row.membership,self.memberships['tech']);self.assertEqual(row.site_authorization,self.site_grant)
        row.reason='Rewrite'
        with self.assertRaises(frappe.PermissionError):row.save(ignore_permissions=True)
        with self.assertRaises(frappe.PermissionError):frappe.delete_doc(teams.ASSIGN,row.name)

    def test_direct_assignment_history_insertion_is_denied(self):
        doc=self.assign();self.admin();data=frappe.get_doc(teams.ASSIGN,doc.team_assignment).as_dict();data.pop('name')
        with self.assertRaises(frappe.PermissionError):frappe.get_doc(data).insert(ignore_permissions=True)

    def test_expired_membership_blocks_assignment(self):
        self.admin();m=self.member();frappe.db.set_value(teams.MEMBER,m.name,'valid_until',add_to_date(now_datetime(),minutes=-1))
        with self.assertRaises(frappe.PermissionError):self.assign()

    def test_future_membership_blocks_assignment(self):
        self.admin();frappe.db.set_value(teams.MEMBER,self.memberships['tech'],'valid_from',add_to_date(now_datetime(),days=1))
        with self.assertRaises(frappe.PermissionError):self.assign()

    def test_revocation_blocks_execution_but_preserves_history(self):
        doc=self.assign();self.admin();m=self.member();m.revoked=1;m.save()
        frappe.set_user(self.users['tech']);doc.reload();doc.check_permission('read')
        with self.assertRaises(frappe.PermissionError):execution.order_for_recording(doc.name)
        self.assertTrue(frappe.db.exists(teams.ASSIGN,doc.team_assignment))

    def test_expired_site_grant_blocks_assignment(self):
        self.admin();frappe.db.set_value(teams.GRANT,self.site_grant,'valid_until',add_to_date(now_datetime(),minutes=-1))
        with self.assertRaises(frappe.PermissionError):self.assign()

    def test_disabled_team_and_discipline_block_assignment(self):
        self.admin();frappe.db.set_value(teams.TEAM,self.team,'disabled',1)
        with self.assertRaises(frappe.PermissionError):self.assign()
        self.admin();frappe.db.set_value(teams.TEAM,self.team,'disabled',0);frappe.db.set_value(teams.DISC,self.discipline,'disabled',1)
        with self.assertRaises(frappe.PermissionError):self.assign()

    def test_cross_company_site_authorization_is_rejected(self):
        self.admin()
        with self.assertRaises(frappe.ValidationError):frappe.get_doc({'doctype':teams.GRANT,'team':self.team,'site':SITE_B,'valid_from':now_datetime()}).insert()

    def test_supervisor_cannot_authorize_outside_own_scope(self):
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.PermissionError):frappe.get_doc({'doctype':teams.GRANT,'team':self.team,'site':SITE_A2,'valid_from':now_datetime()}).insert()

    def test_shared_team_authorization_and_scope_remain_separate(self):
        self.admin();grant_scope(self.users['supervisor'],site=SITE_A2)
        frappe.set_user(self.users['supervisor'])
        second=frappe.get_doc({'doctype':teams.GRANT,'team':self.team,'site':SITE_A2,'valid_from':now_datetime()}).insert()
        self.assertEqual(second.company,COMPANY_A)
        self.admin()
        for name in frappe.get_all('User Permission',filters={'user':self.users['supervisor'],'allow':'TruCMMS Site','for_value':SITE_A2},pluck='name'):frappe.delete_doc('User Permission',name)
        frappe.set_user(self.users['supervisor']);team=frappe.get_doc(teams.TEAM,self.team);team.team_name='Unsafe administration'
        with self.assertRaises(frappe.PermissionError):team.save()

    def test_overlapping_intervals_rejected_and_adjacent_allowed(self):
        self.admin();m=self.member()
        with self.assertRaises(frappe.ValidationError):frappe.get_doc({'doctype':teams.MEMBER,'team':self.team,'user':self.users['tech'],'discipline':self.discipline,'function':'Technician','valid_from':now_datetime()}).insert()
        end=add_to_date(now_datetime(),days=1);m.valid_until=end;m.save()
        new=frappe.get_doc({'doctype':teams.MEMBER,'team':self.team,'user':self.users['tech'],'discipline':self.discipline,'function':'Lead','valid_from':end}).insert()
        self.assertFalse(teams.active(m,end));self.assertTrue(teams.active(new,end))

    def test_interval_identity_and_revocation_audit_cannot_be_forged(self):
        self.admin();m=self.member();m.user=self.users['other']
        with self.assertRaises(frappe.ValidationError):m.save()
        m.reload();m.revoked_on=now_datetime()
        with self.assertRaises(frappe.ValidationError):m.save()
        m.reload();m.revoked=1;m.save();m.revoked=0
        with self.assertRaises(frappe.ValidationError):m.save()

    def test_membership_never_grants_another_technicians_work(self):
        doc=self.assign();frappe.set_user(self.users['other'])
        self.assertNotIn(doc.name,frappe.get_list(wo.DT,pluck='name'))
        with self.assertRaises(frappe.PermissionError):doc.check_permission('read')
        self.assertNotIn(doc.team_assignment,frappe.get_list(teams.ASSIGN,pluck='name'))

    def test_team_metadata_and_sharing_follow_scope(self):
        self.admin();outsider=frappe.get_doc({'doctype':'User','email':self.token+'outside@example.com','first_name':'Outside','send_welcome_email':0,'roles':[{'role':'TruCMMS Technician'}]}).insert();grant_scope(outsider.name,COMPANY_B,SITE_B)
        frappe.set_user(outsider.name);self.assertNotIn(self.team,frappe.get_list(teams.TEAM,pluck='name'))
        with self.assertRaises(frappe.PermissionError):frappe.get_doc(teams.TEAM,self.team).check_permission('read')
        self.admin()
        with self.assertRaises(frappe.PermissionError):frappe.share.add(teams.TEAM,self.team,user=outsider.name,notify=0)

    def test_legacy_adoption_is_reasoned_and_preserves_assignment_clock(self):
        doc=self.assign();self.admin();clock=doc.assigned_on
        frappe.db.set_value(wo.DT,doc.name,{'team_policy':'Legacy','responsible_team':None,'required_discipline':None,'team_assignment':None})
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.ValidationError):teams.adopt_legacy(doc.name,self.team,self.discipline,'')
        result=teams.adopt_legacy(doc.name,self.team,self.discipline,'Adopt existing responsibility')
        self.assertEqual(result['team_policy'],'Managed');self.assertEqual(str(result['assigned_on']),str(clock));self.assertTrue(result['team_assignment'])

    def test_site_timezone_rejects_invalid_names_and_handles_dst(self):
        self.admin();site=frappe.get_doc('TruCMMS Site',SITE_A);site.time_zone='America/Vancouver';site.save()
        self.assertEqual(configuration.local_instant('2026-10-24 10:00:00',SITE_A),'2026-10-24T17:00:00+00:00')
        site.time_zone='America/New_York';site.save()
        with self.assertRaises(frappe.ValidationError):configuration.local_instant('2026-03-08 02:30:00',SITE_A)
        with self.assertRaises(frappe.ValidationError):configuration.local_instant('2026-11-01 01:30:00',SITE_A)
        self.assertNotEqual(configuration.local_instant('2026-11-01 01:30:00',SITE_A,0),configuration.local_instant('2026-11-01 01:30:00',SITE_A,1))
        site.time_zone='Invalid/Timezone'
        with self.assertRaises(frappe.ValidationError):site.save()

    def test_system_timezone_change_requires_timestamp_migration(self):
        self.make();self.admin();settings=frappe.get_doc('System Settings');settings.time_zone='UTC' if settings.time_zone!='UTC' else 'America/Vancouver'
        with self.assertRaises(frappe.ValidationError):settings.save()
