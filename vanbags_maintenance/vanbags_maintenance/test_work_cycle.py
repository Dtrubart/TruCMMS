import json,uuid
import frappe
from frappe.model.workflow import apply_workflow
from frappe.utils import now_datetime,add_to_date
from vanbags_maintenance import work_orders as wo,work_cycle as cycle,work_contract as contract,allocations,teams,reporting
from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase

class TestWorkCycle(WorkOrderCase):
    use_c_policy=True
    def setUp(self):
        super().setUp();self.order=self.assign();self.backdate(self.order)
    def backdate(self,order):
        frappe.set_user('Administrator');past=add_to_date(now_datetime(),hours=-3)
        frappe.db.set_value(wo.DT,order.name,'assigned_on',past)
        for row in allocations.active(order):frappe.db.set_value(allocations.DT,row.name,'assigned_on',past)
        order.reload()
    def action(self,role,action,reason='C test decision'):
        frappe.set_user(self.users[role]);self.order=frappe.get_doc(cycle.perform(self.order.name,action,reason));return self.order
    def entry(self,role='tech',minutes=-30):
        frappe.set_user(self.users[role]);start=add_to_date(now_datetime(),minutes=minutes)
        return frappe.get_doc({'doctype':'TruCMMS Work Execution','work_order':self.order.name,'actual_start':start,'actual_end':add_to_date(start,minutes=10),'findings':'C functional verification','tasks':[{'task':'Repair and inspect','result':'Completed','findings':'Passed'}]}).insert()
    def complete(self):self.entry();return self.action('tech','Complete Work')
    def verify(self):self.complete();return self.action('supervisor','Verify Work')
    def close(self):self.verify();self.action('requester','Accept Work');return self.action('supervisor','Close Order')
    def site_policy(self,value):
        frappe.set_user('Administrator');site=frappe.get_doc('TruCMMS Site',self.order.site);site.acceptance_policy=value;site.save()
    def direct(self,key=None,**values):
        frappe.set_user(self.users['dispatcher'])
        return frappe.get_doc(contract.create_direct(self.order.company,self.order.site,'Direct repair','Authorized direct scope','High',key or uuid.uuid4().hex,'No requester needed for this authorized work',functional_location=self.location.name,**values))

    def test_request_requires_verification_before_acceptance(self):
        self.complete()
        with self.assertRaises(frappe.ValidationError):self.action('requester','Accept Work')
        self.action('supervisor','Verify Work');self.action('requester','Accept Work');doc=self.action('supervisor','Close Order')
        self.assertEqual(doc.status,'Closed');self.assertTrue(doc.verified_on);self.assertEqual(doc.verified_by,self.users['supervisor'])
    def test_technician_cannot_verify_own_execution(self):
        self.complete()
        with self.assertRaises(frappe.PermissionError):self.action('tech','Verify Work')
    def test_site_policy_is_snapshotted_and_not_retroactive(self):
        self.site_policy('Not Required');self.order.reload();self.assertTrue(self.order.acceptance_required);self.assertEqual(self.order.acceptance_policy_snapshot,'By Origin')
    def test_no_acceptance_policy_closes_after_verification(self):
        self.site_policy('Not Required');doc=self.direct();self.assertFalse(doc.acceptance_required)
        doc.responsible_team=self.team;doc.required_discipline=self.discipline;doc.save();frappe.set_user(self.users['supervisor']);doc=apply_workflow(doc.as_dict(),'Authorize');doc.assigned_to=self.users['tech'];doc.save();doc=apply_workflow(doc.as_dict(),'Assign');self.order=doc;self.backdate(doc)
        self.verify();closed=self.action('supervisor','Close Order');self.assertEqual(closed.acceptance_method,'Not Applicable')
    def test_required_policy_direct_work_needs_designated_acceptor(self):
        self.site_policy('Required');doc=self.direct();self.assertTrue(doc.acceptance_required)
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.ValidationError):apply_workflow(doc.as_dict(),'Authorize')
        doc.reload();doc.acceptance_user=self.users['requester'];doc.save();doc=apply_workflow(doc.as_dict(),'Authorize');self.assertEqual(doc.status,'Authorized')
    def test_direct_creation_is_idempotent_and_rejects_key_reuse(self):
        before=frappe.db.count('TruCMMS Maintenance Request');key=uuid.uuid4().hex;doc=self.direct(key);again=self.direct(key)
        self.assertEqual(doc.name,again.name);self.assertFalse(doc.maintenance_request);self.assertEqual(before,frappe.db.count('TruCMMS Maintenance Request'))
        with self.assertRaises(frappe.ValidationError):contract.create_direct(doc.company,doc.site,'Different','Other scope','High',key,'No requester needed for this authorized work',functional_location=self.location.name)
    def test_direct_factory_rejects_requester_and_missing_context(self):
        frappe.set_user(self.users['requester'])
        with self.assertRaises(frappe.PermissionError):contract.create_direct(self.order.company,self.order.site,'Bad','Bad','High',uuid.uuid4().hex,'Reason',functional_location=self.location.name)
        frappe.set_user(self.users['dispatcher'])
        with self.assertRaises(frappe.ValidationError):contract.create_direct(self.order.company,self.order.site,'Bad','Bad','High',uuid.uuid4().hex,'Reason')
    def test_native_direct_insert_cannot_forge_factory_keys(self):
        frappe.set_user('Administrator')
        with self.assertRaises(frappe.PermissionError):frappe.get_doc({'doctype':wo.DT,'origin_type':'Direct','company':self.order.company,'site':self.order.site,'functional_location':self.location.name,'subject':'Forged','scope':'Forged','priority':'High','direct_key':'Forged'}).insert()
    def test_schedule_is_separate_and_reasoned_after_authorization(self):
        start=add_to_date(now_datetime(),days=1);end=add_to_date(start,hours=2);deadline=add_to_date(now_datetime(),days=-1)
        frappe.set_user(self.users['supervisor']);doc=frappe.get_doc(cycle.replan(self.order.name,start,end,deadline,'Schedule overdue recovery'))
        self.assertTrue(doc.scheduled_start);self.assertEqual(str(doc.target_closure),str(deadline))
        doc.scheduled_end=add_to_date(end,hours=1)
        with self.assertRaises(frappe.ValidationError):doc.save()
    def test_invalid_and_partial_schedule_rejected(self):
        frappe.set_user(self.users['supervisor']);start=now_datetime()
        for a,z in [(start,None),(start,start),(start,add_to_date(start,hours=-1))]:
            with self.assertRaises(frappe.ValidationError):cycle.replan(self.order.name,a,z,None,'Invalid schedule')
    def test_hold_blocks_execution_and_resume_preserves_assignments(self):
        self.action('supervisor','Hold Work');self.assertEqual(self.order.status,'On Hold')
        with self.assertRaises(frappe.PermissionError):self.entry()
        self.action('supervisor','Resume Work');self.assertEqual(self.order.status,'Assigned');self.entry()
    def test_resume_rechecks_eligibility(self):
        self.action('supervisor','Hold Work');frappe.set_user('Administrator');member=frappe.get_doc(teams.MEMBER,self.memberships['tech']);member.revoked=1;member.save()
        with self.assertRaises(frappe.PermissionError):self.action('supervisor','Resume Work')
    def test_reasoned_reassignment_preserves_history_and_revokes_old_access(self):
        self.entry();frappe.set_user(self.users['supervisor']);old=self.order.team_assignment;doc=frappe.get_doc(cycle.reassign(self.order.name,self.users['other'],'Specialist coverage'));self.assertNotEqual(doc.team_assignment,old)
        self.assertTrue(frappe.db.exists(teams.ASSIGN,old));frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.PermissionError):doc.check_permission('read')
    def test_direct_primary_edit_is_denied(self):
        frappe.set_user(self.users['supervisor']);self.order.assigned_to=self.users['other']
        with self.assertRaises(frappe.ValidationError):self.order.save()
    def test_additional_discipline_participant_can_record_only_allocated_work(self):
        frappe.set_user(self.users['supervisor']);row=allocations.add(self.order.name,self.users['other'],self.discipline,'Second technician');self.backdate(self.order)
        self.entry('other');self.entry();self.action('tech','Complete Work');self.assertEqual(self.order.status,'Technical Completed')
    def test_completion_waits_for_all_active_participants(self):
        frappe.set_user(self.users['supervisor']);allocations.add(self.order.name,self.users['other'],self.discipline,'Additional work');self.backdate(self.order);self.entry()
        with self.assertRaises(frappe.ValidationError):self.action('tech','Complete Work')
    def test_removal_preserves_allocation_history_and_revokes_access(self):
        frappe.set_user(self.users['supervisor']);row=allocations.add(self.order.name,self.users['other'],self.discipline,'Additional work');allocations.remove(row['name'],'No longer required')
        self.assertTrue(frappe.db.get_value(allocations.DT,row['name'],'ended_on'));frappe.set_user(self.users['other'])
        with self.assertRaises(frappe.PermissionError):self.order.check_permission('read')
    def test_primary_allocation_cannot_be_removed_as_secondary(self):
        frappe.set_user(self.users['supervisor']);row=allocations.current(self.order,self.users['tech'])
        with self.assertRaises(frappe.ValidationError):allocations.remove(row.name,'Attempt removal')
    def test_rework_archives_cycle_and_requires_new_execution(self):
        self.verify();self.action('requester','Request Rework');self.assertEqual(self.order.execution_cycle,2)
        snapshot=frappe.get_doc(cycle.CYCLE,frappe.db.get_value(cycle.CYCLE,{'work_order':self.order.name},'name'));self.assertEqual(json.loads(snapshot.snapshot)['status'],'Verified')
        with self.assertRaises(frappe.ValidationError):self.action('tech','Complete Work')
    def test_reopening_archives_closure_and_returns_authorized(self):
        self.close();old=self.order.closed_on;doc=self.action('supervisor','Reopen Order','Repeat failure')
        self.assertEqual(doc.status,'Authorized');self.assertEqual(doc.execution_cycle,2);self.assertFalse(doc.assigned_to);self.assertFalse(doc.closed_on)
        snap=json.loads(frappe.db.get_value(cycle.CYCLE,{'work_order':doc.name},'snapshot'));self.assertEqual(snap['status'],'Closed');self.assertEqual(snap['closed_on'],str(old))
    def test_closed_order_requires_reopen_service(self):
        self.close();frappe.set_user(self.users['supervisor']);self.order.status='Authorized'
        with self.assertRaises(frappe.PermissionError):self.order.save()
    def test_cycle_and_allocation_history_cannot_be_forged(self):
        self.close();self.action('supervisor','Reopen Order');frappe.set_user('Administrator');row=frappe.get_doc(cycle.CYCLE,frappe.db.get_value(cycle.CYCLE,{'work_order':self.order.name},'name'));row.ended_action='Rewrite'
        with self.assertRaises(frappe.PermissionError):row.save(ignore_permissions=True)
        allocation=frappe.get_doc(allocations.DT,frappe.db.get_value(allocations.DT,{'work_order':self.order.name},'name'));allocation.technician=self.users['other']
        with self.assertRaises(frappe.PermissionError):allocation.save(ignore_permissions=True)
    def test_workflow_bypass_does_not_create_verification(self):
        self.complete();frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.PermissionError):apply_workflow(self.order.as_dict(),'Verify Work')
    def test_reviewer_cannot_waive_acceptance_by_field_edit(self):
        self.verify();frappe.set_user(self.users['supervisor']);self.order.acceptance_required=0
        with self.assertRaises(frappe.PermissionError):self.order.save()

    def electrical(self):
        frappe.set_user('Administrator');code=(self.token+'-ELEC').upper()
        frappe.get_doc({'doctype':teams.DISC,'discipline_code':code,'discipline_name':'Electrical'}).insert()
        team=frappe.get_doc(teams.TEAM,self.team);team.append('disciplines',{'discipline':code});team.save()
        frappe.get_doc({'doctype':teams.MEMBER,'team':self.team,'user':self.users['other'],'discipline':code,'function':'Technician','valid_from':add_to_date(now_datetime(),days=-1)}).insert()
        return code
    def test_distinct_disciplines_are_preserved_on_execution(self):
        code=self.electrical();frappe.set_user(self.users['supervisor']);allocations.add(self.order.name,self.users['other'],code,'Electrical inspection');self.backdate(self.order)
        entry=self.entry('other');self.assertEqual(entry.discipline,code);self.assertTrue(entry.allocation)
        self.entry();self.action('tech','Complete Work')
    def test_paused_reassignment_can_restore_eligibility(self):
        self.action('supervisor','Hold Work');frappe.set_user('Administrator');m=frappe.get_doc(teams.MEMBER,self.memberships['tech']);m.revoked=1;m.save()
        frappe.set_user(self.users['supervisor']);self.order=frappe.get_doc(cycle.reassign(self.order.name,self.users['other'],'Replace unavailable technician'))
        self.assertEqual(self.order.status,'On Hold');self.action('supervisor','Resume Work');self.assertEqual(self.order.status,'Assigned')
    def test_paused_secondary_can_be_removed_before_resume(self):
        frappe.set_user(self.users['supervisor']);row=allocations.add(self.order.name,self.users['other'],self.discipline,'Additional work');self.action('supervisor','Hold Work')
        frappe.set_user('Administrator');m=frappe.get_doc(teams.MEMBER,self.memberships['other']);m.revoked=1;m.save()
        frappe.set_user(self.users['supervisor']);allocations.remove(row['name'],'Unavailable while paused');self.action('supervisor','Resume Work')
    def test_backdated_execution_cannot_cross_pause(self):
        self.action('supervisor','Hold Work');self.action('supervisor','Resume Work');frappe.set_user('Administrator')
        for action,minutes in [('Hold Work',-25),('Resume Work',-20)]:
            name=frappe.db.get_value(cycle.EVENT,{'work_order':self.order.name,'action':action},'name');frappe.db.set_value(cycle.EVENT,name,'occurred_on',add_to_date(now_datetime(),minutes=minutes))
        with self.assertRaises(frappe.ValidationError):self.entry(minutes=-30)
    def test_invalid_site_policy_is_rejected(self):
        frappe.set_user('Administrator');site=frappe.get_doc('TruCMMS Site',self.order.site);site.acceptance_policy='Bypass verification'
        with self.assertRaises(frappe.ValidationError):site.save()
    def test_secondary_executor_cannot_verify_even_with_supervisor_role(self):
        frappe.set_user('Administrator');user=frappe.get_doc('User',self.users['other']);user.append('roles',{'role':wo.SUPERVISOR});user.save()
        frappe.set_user(self.users['supervisor']);allocations.add(self.order.name,self.users['other'],self.discipline,'Additional inspection');self.backdate(self.order)
        self.entry('other');self.entry();self.action('tech','Complete Work')
        with self.assertRaises(frappe.PermissionError):self.action('other','Verify Work')

    def test_failed_reassignment_is_atomic(self):
        frappe.set_user(self.users['supervisor']);before=allocations.current(self.order,self.users['tech']).name
        with self.assertRaises(frappe.ValidationError):cycle.reassign(self.order.name,self.users['requester'],'Invalid replacement')
        self.assertEqual(allocations.current(self.order,self.users['tech']).name,before);self.order.reload();self.assertEqual(self.order.assigned_to,self.users['tech'])

    def test_archived_execution_cannot_be_voided_after_rework(self):
        from vanbags_maintenance.adjustments import void_entry
        entry=self.entry();self.action('tech','Complete Work');self.action('supervisor','Verify Work');self.action('requester','Request Rework')
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.ValidationError):void_entry(entry.name,'Do not rewrite accepted cycle totals')
    def test_verified_order_evidence_is_frozen(self):
        from frappe.utils.file_manager import save_file
        self.verify();frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.PermissionError):save_file(self.token+'late.txt',b'Late evidence',wo.DT,self.order.name,is_private=1)

    def test_reopened_direct_order_can_resolve_new_required_acceptance_policy(self):
        doc=self.direct();doc.responsible_team=self.team;doc.required_discipline=self.discipline;doc.save();frappe.set_user(self.users['supervisor']);doc=apply_workflow(doc.as_dict(),'Authorize');doc.assigned_to=self.users['tech'];doc.save();doc=apply_workflow(doc.as_dict(),'Assign');self.order=doc;self.backdate(doc)
        self.verify();self.action('supervisor','Close Order');self.site_policy('Required');self.action('supervisor','Reopen Order');self.assertTrue(self.order.acceptance_required);self.assertEqual(self.order.status,'Authorized')
        frappe.set_user(self.users['supervisor']);self.order=frappe.get_doc(cycle.designate_acceptor(self.order.name,self.users['requester'],'Requester identified for reopened cycle'));self.order.assigned_to=self.users['tech'];self.order.save();self.order=apply_workflow(self.order.as_dict(),'Assign');self.assertEqual(self.order.status,'Assigned')
