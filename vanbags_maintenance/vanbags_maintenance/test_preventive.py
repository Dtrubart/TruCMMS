import json,uuid
from unittest.mock import patch
from datetime import timedelta
import frappe
from frappe.utils import now_datetime,add_to_date,getdate
from frappe.model.workflow import apply_workflow
from vanbags_maintenance import preventive as pm,job_plans as jp,meters,components,inspections,work_orders as wo,work_cycle as cycle,allocations
from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase
from vanbags_maintenance.test_support import COMPANY_A,SITE_A,SITE_B,COMPANY_B,grant_scope

class PreventiveCase(WorkOrderCase):
    use_c_policy=True
    def setUp(self):
        super().setUp();frappe.set_user('Administrator')
        self.category=frappe.get_doc({'doctype':'VB Equipment Category','category_name':self.token}).insert().name
        self.eq=frappe.get_doc({'doctype':'VB Equipment','equipment_code':self.token,'equipment_name':'Preventive target','category':self.category,'company':COMPANY_A,'site':SITE_A}).insert()
        if not frappe.db.exists('UOM','Hour'):frappe.get_doc({'doctype':'UOM','uom_name':'Hour'}).insert()
        self.unit='Hour';self.number=0
    def procedure(self,measurements=None,evidence=0):
        frappe.set_user(self.users['dispatcher']);self.number+=1
        parent=frappe.get_doc({'doctype':jp.PLAN,'code':self.token+'-J'+str(self.number),'plan_name':'Routine','company':COMPANY_A,'site':SITE_A}).insert()
        revision=frappe.get_doc({'doctype':jp.REVISION,'job_plan':parent.name,'revision_title':'Inspect','change_reason':'Test procedure','tasks':[{'task_code':'inspect','instructions':'Inspect target','mandatory':1,'evidence_required':evidence}], 'measurements':measurements or []}).insert()
        frappe.set_user(self.users['supervisor']);jp.approve(revision.name,'Approved synthetic test procedure');return revision.reload()
    def plan(self,revision=None,activate=True,**values):
        revision=revision or self.procedure();frappe.set_user(self.users['dispatcher']);self.number+=1
        doc=frappe.get_doc({'doctype':pm.PLAN,'code':self.token+'-P'+str(self.number),'plan_name':'Weekly inspection','company':COMPANY_A,'site':SITE_A,'equipment':self.eq.name,'procedure_revision':revision.name,'anchor_date':getdate(),'horizon_days':28,'lead_days':28,'responsible_team':self.team,'required_discipline':self.discipline,**values}).insert()
        if activate:
            frappe.set_user(self.users['supervisor']);pm.activate(doc.name,'Approved test plan')
        return doc.reload()
    def occurrences(self,plan):return frappe.get_all(pm.OCC,filters={'plan':plan.name},fields=['name','status','original_due','planned_for','sequence','work_order'],order_by='sequence')
    def release(self,plan,index=0,**kw):
        frappe.set_user(self.users['supervisor']);return frappe.get_doc(pm.release(self.occurrences(plan)[index].name,'Release test work',**kw))
    def assigned(self,plan):
        order=self.release(plan);order=apply_workflow(order.as_dict(),'Authorize');order.assigned_to=self.users['tech'];order.save();order=apply_workflow(order.as_dict(),'Assign')
        frappe.set_user('Administrator');past=add_to_date(now_datetime(),hours=-3);frappe.db.set_value(wo.DT,order.name,'assigned_on',past)
        for row in allocations.active(order):frappe.db.set_value(allocations.DT,row.name,'assigned_on',past)
        return order.reload()
    def entry(self,order,**kw):
        frappe.set_user(self.users['tech']);start=add_to_date(now_datetime(),minutes=-30)
        return frappe.get_doc({'doctype':'TruCMMS Work Execution','work_order':order.name,'actual_start':start,'actual_end':add_to_date(start,minutes=10),'findings':'Synthetic inspection results','tasks':[{'task':'Inspect','procedure_task_code':'inspect','result':'Completed','findings':'Inspected'}],**kw}).insert()
    def verify(self,order,entry=True):
        if entry:self.entry(order)
        frappe.set_user(self.users['tech']);cycle.perform(order.name,'Complete Work','Tasks performed')
        frappe.set_user(self.users['supervisor']);cycle.perform(order.name,'Verify Work','Independent verification')
        return order.reload()
    def meter(self,kind='Cumulative',component=None,**values):
        frappe.set_user('Administrator');self.number+=1
        return frappe.get_doc({'doctype':meters.DT,'code':self.token+'-M'+str(self.number),'meter_name':'Operating measurement','company':COMPANY_A,'site':SITE_A,'equipment':self.eq.name,'component':component,'unit':self.unit,'metric_kind':kind,'direction':'Increasing' if kind=='Cumulative' else 'Decreasing','max_age_hours':168,**values}).insert()
    def reading(self,meter,value,minutes=-60,key=None):
        frappe.set_user(self.users['tech']);return frappe.get_doc(meters.record(meter.name,value,add_to_date(now_datetime(),minutes=minutes),key or uuid.uuid4().hex,'Observed test reading'))

class TestPreventive(PreventiveCase):
    def test_automatic_work_events_enqueue_only_after_commit(self):
        plan=self.plan(release_mode='Automatic',automation_enabled=1,automation_user=self.users['supervisor'])
        with patch('frappe.enqueue') as enqueue:
            order=self.assigned(plan);frappe.set_user(self.users['tech']);enqueue.reset_mock()
            pm.start_work(order.name,'Begin automatic plan work')
            enqueue.assert_called_once()
            self.assertTrue(enqueue.call_args.kwargs['enqueue_after_commit'])
            self.assertEqual(enqueue.call_args.kwargs['plan'],plan.name)
    def test_automatic_evaluation_opens_only_draft_and_retries_once(self):
        plan=self.plan(release_mode='Automatic',automation_enabled=1,automation_user=self.users['supervisor'])
        result=pm.run_plan(plan.name,'Approved automatic evaluation');again=pm.run_plan(plan.name,'Retry evaluation')
        self.assertEqual(len(result['released']),1);self.assertEqual(again['released'],[])
        order=frappe.get_doc(wo.DT,result['released'][0]);self.assertEqual(order.status,'Draft');self.assertFalse(order.authorized_by)
    def test_new_plan_cannot_forge_runtime_counters(self):
        for value in ('trigger_sequence','baseline_total','next_trigger_total','condition_latched'):
            with self.assertRaises(frappe.ValidationError):self.plan(activate=False,**{value:999})
    def test_dispatcher_cannot_override_release_capacity(self):
        plan=self.plan();self.release(plan);frappe.set_user(self.users['dispatcher'])
        with self.assertRaises(frappe.PermissionError):pm.release(self.occurrences(plan)[1].name,'Attempt supervisor exception',override=1)
    def test_calendar_frozen_zone_is_used_after_site_timezone_changes(self):
        plan=self.plan();before=pm.due_instant(plan,getdate());frappe.set_user('Administrator');site=frappe.get_doc('TruCMMS Site',SITE_A);site.time_zone='Pacific/Auckland';site.save();self.assertEqual(pm.due_instant(plan,getdate()),before)
    def test_activation_materializes_many_obligations_and_zero_orders(self):
        before=frappe.db.count(wo.DT);plan=self.plan();self.assertEqual(len(self.occurrences(plan)),5);self.assertEqual(frappe.db.count(wo.DT),before)
    def test_repeated_materialization_and_release_are_idempotent(self):
        plan=self.plan();pm.materialize(plan.name);self.assertEqual(len(self.occurrences(plan)),5)
        order=self.release(plan);again=self.release(plan);self.assertEqual(order.name,again.name);self.assertEqual(order.origin_type,'Preventive');self.assertTrue(order.pm_occurrence)
    def test_original_due_survives_postponement(self):
        plan=self.plan();row=self.occurrences(plan)[0];pm.change_occurrence(row.name,'Postpone','Capacity constraint',getdate()+timedelta(days=3));after=frappe.get_doc(pm.OCC,row.name);self.assertEqual(after.original_due,row.original_due);self.assertNotEqual(after.planned_for,after.original_due)
    def test_skip_does_not_create_execution_or_mark_maintenance_done(self):
        plan=self.plan(calendar_policy='After Completion');row=self.occurrences(plan)[0];pm.change_occurrence(row.name,'Skip','Maintenance capacity unavailable');plan.reload();self.assertFalse(plan.baseline_occurrence);self.assertEqual(len(self.occurrences(plan)),2)
    def test_active_order_gate_and_supervisor_exception(self):
        plan=self.plan();self.release(plan)
        with self.assertRaises(frappe.ValidationError):self.release(plan,1)
        second=self.release(plan,1,override=1);self.assertEqual(second.status,'Draft')
    def test_manual_opening_next_requires_explicit_skip_of_earlier(self):
        plan=self.plan()
        with self.assertRaises(frappe.ValidationError):self.release(plan,1)
        pm.change_occurrence(self.occurrences(plan)[0].name,'Skip','Explicitly omitted due to capacity');self.assertEqual(self.release(plan,1).status,'Draft')
    def test_equipment_scope_serializes_different_plans(self):
        first=self.plan(release_scope='Equipment');second=self.plan(release_scope='Equipment');self.release(first)
        with self.assertRaises(frappe.ValidationError):self.release(second)
    def test_equipment_gate_can_explicitly_include_corrective_orders(self):
        from vanbags_maintenance.work_contract import create_direct
        plan=self.plan(release_scope='Equipment',include_corrective_work=1)
        create_direct(COMPANY_A,SITE_A,'Corrective repair','Repair asset','High',uuid.uuid4().hex,'Observed fault',equipment=self.eq.name)
        with self.assertRaises(frappe.ValidationError):self.release(plan)
    def test_started_policy_frees_next_slot_without_closing_current(self):
        plan=self.plan(release_event='Started');order=self.assigned(plan);frappe.set_user(self.users['tech']);pm.start_work(order.name,'Begin preventive work');next_order=self.release(plan,1);self.assertNotEqual(order.name,next_order.name);self.assertEqual(order.reload().status,'Assigned')
    def test_verified_policy_releases_next_before_final_closure(self):
        plan=self.plan(release_event='Verified');order=self.assigned(plan);self.verify(order);self.assertEqual(self.release(plan,1).status,'Draft')
    def test_after_completion_uses_actual_work_not_verification_date(self):
        plan=self.plan(calendar_policy='After Completion');order=self.assigned(plan);entry=self.entry(order);self.verify(order,entry=False);plan.reload();self.assertEqual(getdate(plan.next_due_date),pm.advance(plan,getdate(entry.actual_end)))
    def test_mandatory_procedure_task_is_enforced(self):
        plan=self.plan();order=self.assigned(plan);self.entry(order,tasks=[{'task':'Other task','result':'Completed','findings':'Done'}]);frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.ValidationError):cycle.perform(order.name,'Complete Work','Attempt incomplete procedure')
    def test_evidence_requirement_is_enforced(self):
        plan=self.plan(revision=self.procedure(evidence=1));order=self.assigned(plan);self.entry(order);frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.ValidationError):cycle.perform(order.name,'Complete Work','No evidence supplied')
    def test_plan_and_occurrence_provenance_cannot_be_forged(self):
        plan=self.plan();order=self.release(plan);order.pm_occurrence=self.occurrences(plan)[1].name
        with self.assertRaises(frappe.PermissionError):order.save()
        row=frappe.get_doc(pm.OCC,self.occurrences(plan)[1].name);row.original_due=getdate()+timedelta(days=50)
        with self.assertRaises(frappe.PermissionError):row.save(ignore_permissions=True)
    def test_active_plan_configuration_is_frozen(self):
        plan=self.plan();plan.interval=2
        with self.assertRaises(frappe.ValidationError):plan.save()
    def test_paused_plan_cannot_release_but_retains_history(self):
        plan=self.plan();pm.disposition(plan.name,'Pause','No maintenance window')
        with self.assertRaises(frappe.ValidationError):self.release(plan)
        pm.disposition(plan.name,'Resume','Window restored');self.assertEqual(self.release(plan).status,'Draft')
    def test_monthly_anchor_does_not_drift_at_february(self):
        plan=self.plan(activate=False,frequency='Months',anchor_date='2026-01-31')
        self.assertEqual([str(x) for x in pm.calendar_dates(plan,'2026-01-01','2026-04-30')],['2026-01-31','2026-02-28','2026-03-31','2026-04-30'])
    def test_permissions_and_preview_limits_are_enforced(self):
        plan=self.plan();frappe.set_user(self.users['requester'])
        with self.assertRaises(frappe.PermissionError):pm.preview(plan.name)
        frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.PermissionError):pm.release(self.occurrences(plan)[0].name,'Unauthorized')
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.ValidationError):pm.preview(plan.name,'2026-01-01','2028-01-01')
    def test_rework_reconciles_unreleased_successor_and_retains_cycle(self):
        plan=self.plan(calendar_policy='After Completion');order=self.assigned(plan);self.verify(order);frappe.set_user(self.users['supervisor']);cycle.perform(order.name,'Request Rework','Repeat inspection');rows=self.occurrences(plan);self.assertEqual(rows[0].status,'Released');self.assertEqual(rows[1].status,'Cancelled');self.assertEqual(frappe.db.count('TruCMMS Work Cycle',{'work_order':order.name}),1)
    def test_cancelled_order_is_not_successful_preventive_maintenance(self):
        plan=self.plan(calendar_policy='After Completion');order=self.release(plan);cycle.perform(order.name,'Cancel Order','Cancelled before work');plan.reload();self.assertFalse(plan.baseline_occurrence);self.assertEqual(self.occurrences(plan)[0].status,'Cancelled')
    def test_scheduler_requires_explicit_scoped_identity(self):
        with self.assertRaises(frappe.ValidationError):self.plan(automation_enabled=1,automation_user='Administrator')

class TestMeters(PreventiveCase):
    def test_reset_key_is_required_and_conflicting_retries_are_rejected(self):
        meter=self.meter();self.reading(meter,100);frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.ValidationError):meters.reset(meter.name,0,'Replacement','')
        stamp=add_to_date(now_datetime(),minutes=-30);a=meters.reset(meter.name,0,'Replacement','same-reset',stamp);b=meters.reset(meter.name,0,'Replacement','same-reset',stamp);self.assertEqual(a['name'],b['name'])
        with self.assertRaises(frappe.ValidationError):meters.reset(meter.name,9,'Replacement','same-reset',stamp)
    def test_usage_completion_advances_from_recorded_maintenance_reading(self):
        meter=self.meter();self.reading(meter,100,minutes=-120);revision=self.procedure(measurements=[{'task_code':'inspect','metric_key':'hours','metric_name':'Hours','metric_kind':'Cumulative','unit':self.unit,'direction':'Increasing','required':1}]);plan=self.plan(revision=revision,schedule_type='Meter',meter=meter.name,meter_metric_key='hours',usage_interval=10);self.reading(meter,110,minutes=-90);frappe.set_user(self.users['supervisor']);pm.run_plan(plan.name,'Evaluate usage');order=self.assigned(plan)
        reading=self.reading(meter,112,minutes=-25);self.entry(order,pm_measurements=[{'metric_key':'hours','value':'112','meter_reading':reading.name}]);self.verify(order,entry=False);plan.reload();self.assertEqual(plan.baseline_reading,reading.name);self.assertEqual(plan.next_trigger_total,122)
    def test_skipped_usage_advances_obligation_without_false_service_baseline(self):
        meter=self.meter();base=self.reading(meter,100);revision=self.procedure(measurements=[{'task_code':'inspect','metric_key':'hours','metric_name':'Hours','metric_kind':'Cumulative','unit':self.unit,'direction':'Increasing','required':1}]);plan=self.plan(revision=revision,schedule_type='Meter',meter=meter.name,meter_metric_key='hours',usage_interval=10);self.reading(meter,125,minutes=-30);frappe.set_user(self.users['supervisor']);pm.run_plan(plan.name,'Evaluate usage');pm.change_occurrence(self.occurrences(plan)[0].name,'Skip','Capacity unavailable');pm.run_plan(plan.name,'Next threshold');plan.reload();self.assertEqual(plan.baseline_reading,base.name);self.assertEqual(plan.next_trigger_total,120);self.assertEqual(len(self.occurrences(plan)),2)
    def test_persistent_condition_requires_explicit_renewal_after_skip(self):
        meter=self.meter('Condition');self.reading(meter,2);revision=self.procedure(measurements=[{'task_code':'inspect','metric_key':'wear','metric_name':'Wear','metric_kind':'Condition','unit':self.unit,'direction':'Decreasing','required':1}]);plan=self.plan(revision=revision,schedule_type='Meter',meter=meter.name,meter_metric_key='wear',trigger_kind='Below',lower_threshold=3);pm.change_occurrence(self.occurrences(plan)[0].name,'Skip','Capacity unavailable');pm.run_plan(plan.name,'No flood');self.assertEqual(len(self.occurrences(plan)),1);pm.renew_condition(plan.name,'Supervisor requires a new intervention');self.assertEqual(len(self.occurrences(plan)),2)
    def test_reading_retry_returns_one_immutable_record(self):
        meter=self.meter();stamp=add_to_date(now_datetime(),minutes=-5);frappe.set_user(self.users['tech']);a=meters.record(meter.name,100,stamp,'same','Observed');b=meters.record(meter.name,100,stamp,'same','Observed');self.assertEqual(a['name'],b['name']);self.assertEqual(frappe.db.count(meters.READING,{'meter':meter.name}),1)
    def test_counter_drop_requires_epoch_reset_and_preserves_total(self):
        meter=self.meter();self.reading(meter,100)
        with self.assertRaises(frappe.ValidationError):self.reading(meter,1,minutes=-50)
        frappe.set_user(self.users['supervisor']);meters.reset(meter.name,0,'Physical counter replaced','reset1',add_to_date(now_datetime(),minutes=-40));row=self.reading(meter,5,minutes=-30);self.assertEqual(row.total_value,105)
    def test_latest_correction_is_append_only(self):
        meter=self.meter();a=self.reading(meter,100);frappe.set_user(self.users['supervisor']);b=meters.correct(a.name,101,'Transcription correction','fix1');self.assertNotEqual(a.name,b['name']);self.assertEqual(a.reload().value,100);self.assertTrue(meters.corrected(a.name))
    def test_out_of_order_and_future_readings_are_rejected(self):
        meter=self.meter();self.reading(meter,100,minutes=-30)
        with self.assertRaises(frappe.ValidationError):self.reading(meter,110,minutes=-40)
        with self.assertRaises(frappe.ValidationError):self.reading(meter,110,minutes=30)
    def test_condition_can_decrease_and_zero_is_valid(self):
        meter=self.meter('Condition');self.reading(meter,5);row=self.reading(meter,0,minutes=-30);self.assertEqual(row.value,0)
    def test_stale_readings_cannot_drive_automatic_decisions(self):
        meter=self.meter(max_age_hours=1);self.reading(meter,100,minutes=-120);frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.ValidationError):meters.latest(meter.reload(),fresh=True)
    def test_usage_threshold_generates_obligation_not_order(self):
        meter=self.meter();self.reading(meter,100);revision=self.procedure(measurements=[{'task_code':'inspect','metric_key':'hours','metric_name':'Hours','metric_kind':'Cumulative','unit':self.unit,'direction':'Increasing','required':1}]);plan=self.plan(revision=revision,schedule_type='Meter',meter=meter.name,meter_metric_key='hours',usage_interval=10);self.assertEqual(self.occurrences(plan),[]);self.reading(meter,110,minutes=-30);frappe.set_user(self.users['supervisor']);pm.run_plan(plan.name,'Evaluate threshold');self.assertEqual(len(self.occurrences(plan)),1);self.assertFalse(self.occurrences(plan)[0].work_order)
    def test_condition_latching_avoids_duplicate_obligations(self):
        meter=self.meter('Condition');self.reading(meter,8);revision=self.procedure(measurements=[{'task_code':'inspect','metric_key':'wear','metric_name':'Wear','metric_kind':'Condition','unit':self.unit,'direction':'Decreasing','required':1}]);plan=self.plan(revision=revision,schedule_type='Meter',meter=meter.name,meter_metric_key='wear',trigger_kind='Below',lower_threshold=3);self.reading(meter,2,minutes=-30);frappe.set_user(self.users['supervisor']);pm.run_plan(plan.name,'Evaluate wear');pm.run_plan(plan.name,'Evaluate again');self.assertEqual(len(self.occurrences(plan)),1)
    def test_meter_scope_and_history_cannot_be_edited(self):
        meter=self.meter();self.reading(meter,10);frappe.set_user(self.users['supervisor']);meter.reload();meter.epoch_offset=999
        with self.assertRaises(frappe.ValidationError):meter.save()
        row=frappe.get_doc(meters.READING,meter.last_reading);row.value=999
        with self.assertRaises(frappe.PermissionError):row.save(ignore_permissions=True)

class TestComponents(PreventiveCase):
    def test_asset_only_role_cannot_read_planning_audit_events(self):
        plan=self.plan();frappe.set_user('Administrator');user=frappe.get_doc({'doctype':'User','email':self.token+'asset@example.com','first_name':'Asset-only role','send_welcome_email':0,'roles':[{'role':'VB Maintenance Manager'}]}).insert();grant_scope(user.name)
        event=frappe.db.get_value('TruCMMS PM Event',{'plan':plan.name,'action':'Activate Plan'},'name');frappe.set_user(user.name)
        with self.assertRaises(frappe.PermissionError):frappe.get_doc('TruCMMS PM Event',event).check_permission('read')
        self.assertNotIn(event,frappe.get_list('TruCMMS PM Event',pluck='name'))
    def test_repeated_identical_component_placement_is_a_noop(self):
        component=self.component();components.place(component.name,self.eq.name,'LEFT','Retry current location');self.assertEqual(len(components.history(component.name)),1)
    def test_equipment_transfer_carries_components_and_meter_scope(self):
        from vanbags_maintenance import assets
        from vanbags_maintenance.test_support import SITE_A2
        component=self.component();meter=self.meter(component=component.name);old=self.reading(meter,100);frappe.set_user('Administrator');assets.place(self.eq.name,SITE_A2,reason='Transfer assembled equipment');self.assertEqual(component.reload().site,SITE_A2);self.assertEqual(meter.reload().site,SITE_A2);self.assertEqual(old.reload().site,SITE_A);self.assertEqual(len(components.history(component.name)),2)
    def test_active_plan_blocks_silent_equipment_retarget(self):
        from vanbags_maintenance import assets
        from vanbags_maintenance.test_support import SITE_A2
        self.plan();frappe.set_user('Administrator')
        with self.assertRaises(frappe.ValidationError):assets.place(self.eq.name,SITE_A2,reason='Unreconciled transfer')
    def component(self,position='LEFT'):
        frappe.set_user('Administrator');self.number+=1
        doc=frappe.get_doc({'doctype':components.DT,'code':self.token+'-C'+str(self.number),'component_name':'Tracked tire','company':COMPANY_A,'site':SITE_A,'equipment':self.eq.name,'position':position}).insert()
        # Explicit synthetic fixture timeline for readings backdated by this test.
        for name in frappe.get_all(components.INSTALL,filters={'component':doc.name},pluck='name'):frappe.db.set_value(components.INSTALL,name,'effective_from',add_to_date(now_datetime(),days=-1))
        return doc
    def test_component_reading_cannot_be_attributed_before_installation(self):
        component=self.component();meter=self.meter(component=component.name)
        with self.assertRaises(frappe.ValidationError):self.reading(meter,100,minutes=-3000)
    def test_position_is_exclusive_and_movement_preserves_history(self):
        component=self.component()
        with self.assertRaises(frappe.ValidationError):self.component()
        components.place(component.name,reason='Removed to store');component.reload();self.assertFalse(component.equipment);rows=components.history(component.name);self.assertEqual(len(rows),1);self.assertTrue(rows[0].effective_until)
    def test_meter_follows_component_identity(self):
        component=self.component();meter=self.meter(component=component.name);self.reading(meter,100);frappe.set_user('Administrator');components.place(component.name,self.eq.name,'RIGHT','Rotation');self.assertEqual(meter.reload().component,component.name);self.assertEqual(frappe.db.count(meters.READING,{'meter':meter.name}),1)
    def test_active_component_plan_must_be_paused_before_move(self):
        component=self.component();self.plan(component=component.name);frappe.set_user('Administrator')
        with self.assertRaises(frappe.ValidationError):components.place(component.name,self.eq.name,'RIGHT','Unsafe silent retarget')

class TestInspections(PreventiveCase):
    def test_out_of_range_measurement_creates_reviewable_finding(self):
        revision=self.procedure(measurements=[{'task_code':'inspect','metric_key':'condition','metric_name':'Condition','metric_kind':'Condition','unit':self.unit,'direction':'Variable','required':1,'has_upper_limit':1,'upper_limit':5}]);plan=self.plan(revision=revision);order=self.assigned(plan);entry=self.entry(order,pm_measurements=[{'metric_key':'condition','value':'8'}]);self.assertEqual(frappe.db.count(inspections.FINDING,{'execution':entry.name,'status':'Open'}),1)
        frappe.set_user(self.users['tech']);cycle.perform(order.name,'Complete Work','Inspection completed');frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.ValidationError):cycle.perform(order.name,'Verify Work','Review still missing')
        finding=frappe.db.get_value(inspections.FINDING,{'execution':entry.name},'name');inspections.review(finding,'Action Required','Repair required');follow=inspections.followup(finding,'Create traceable corrective work');self.assertEqual(follow['origin_type'],'Inspection');self.assertEqual(follow['status'],'Draft');self.assertEqual(inspections.followup(finding,'Retry')['name'],follow['name']);cycle.perform(order.name,'Verify Work','Finding reviewed and follow-up created')
