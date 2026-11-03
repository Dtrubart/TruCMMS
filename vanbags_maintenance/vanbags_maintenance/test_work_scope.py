import json,uuid
from datetime import timedelta
import frappe
from frappe.utils import now_datetime
from frappe.model.workflow import apply_workflow
from vanbags_maintenance import work_scope as s,meters,work_contract
from vanbags_maintenance.test_support import COMPANY_A,SITE_A,SITE_A2
from vanbags_maintenance.vanbags_maintenance.test_preventive import PreventiveCase

class TestWorkScope(PreventiveCase):
    def facility(self):
        frappe.set_user('Administrator')
        if not frappe.db.exists('UOM','kWh'):frappe.get_doc(dict(doctype='UOM',uom_name='kWh')).insert()
        point=frappe.get_doc(dict(doctype=s.POINT,code=self.token+'-IN',point_name='Building utility inlet',company=COMPANY_A,site=SITE_A,functional_location=self.location.name)).insert()
        meter=frappe.get_doc(dict(doctype=meters.DT,code=self.token+'-KWH',meter_name='Utility consumption',company=COMPANY_A,site=SITE_A,
            measurement_point=point.name,unit='kWh',metric_kind='Cumulative',direction='Increasing',max_age_hours=168)).insert()
        return point,meter
    def configure(self,order,targets,key=None):
        frappe.set_user(self.users['supervisor'])
        return s.configure(order.name,self.location.name,targets,'Reviewed scope for this work',key or uuid.uuid4().hex)
    def test_one_order_can_cover_asset_area_and_facility_point(self):
        point,meter=self.facility();order=self.make()
        self.configure(order,[dict(kind='Equipment',equipment=self.eq.name),dict(kind='Location',functional_location=self.location.name),dict(kind='Measurement Point',measurement_point=point.name),dict(kind='Reference',label='Inspect north door seal')])
        self.assertEqual(len(order.reload().work_targets),4)
        self.assertTrue(all(t.functional_location for t in order.work_targets))
        self.assertEqual(order.work_targets[2].measurement_point,point.name)
    def test_facility_meter_records_and_corrects_without_fake_equipment(self):
        point,meter=self.facility();frappe.set_user(self.users['tech']);when=now_datetime()-timedelta(minutes=5)
        row=meters.record(meter.name,10,when,uuid.uuid4().hex,'Observed utility counter')
        self.assertFalse(row['equipment']);self.assertEqual(row['measurement_point'],point.name)
        frappe.set_user(self.users['supervisor']);fixed=meters.correct(row['name'],11,'Corrected transcription',uuid.uuid4().hex)
        self.assertEqual(fixed['measurement_point'],point.name)
        meters.reset(meter.name,0,'Counter replaced',uuid.uuid4().hex,now_datetime()-timedelta(minutes=1))
        self.assertEqual(frappe.get_doc(meters.DT,meter.name).epoch,2)
    def test_auth_freezes_reference_reading_and_new_reading_does_not_rewrite_it(self):
        point,meter=self.facility();frappe.set_user(self.users['tech'])
        first=meters.record(meter.name,10,now_datetime()-timedelta(minutes=5),uuid.uuid4().hex,'Reference utility reading')
        order=self.make();self.configure(order,[dict(kind='Measurement Point',measurement_point=point.name)])
        order=apply_workflow(order.reload().as_dict(),'Authorize');before=order.scope_snapshot
        frappe.set_user(self.users['tech']);meters.record(meter.name,12,now_datetime()-timedelta(minutes=1),uuid.uuid4().hex,'Later utility reading')
        self.assertEqual(order.reload().scope_snapshot,before);self.assertIn(first['name'],before)
    def test_scope_is_frozen_after_authorization(self):
        order=self.authorize()
        with self.assertRaises(frappe.ValidationError):self.configure(order,[dict(kind='Location',functional_location=self.location.name)])
        order.reload().work_targets[0].label='Changed approved point'
        with self.assertRaises(frappe.PermissionError):order.save()
    def test_work_reading_uses_r2_once_and_links_its_target(self):
        point,meter=self.facility();order=self.make();self.configure(order,[dict(kind='Measurement Point',measurement_point=point.name)])
        order=self.assign();target=order.work_targets[0].target_id;frappe.set_user(self.users['tech'])
        args=dict(order=order.name,target_id=target,meter=meter.name,value=15,actual_on=now_datetime()-timedelta(minutes=1),key=uuid.uuid4().hex,reason='Read during work')
        first=s.record_reading(**args);again=s.record_reading(**args)
        self.assertEqual(first['reading'],again['reading']);self.assertFalse(again['created'])
        self.assertEqual(frappe.db.count(s.READING,{'work_order':order.name}),1)
    def test_meter_must_match_the_selected_point(self):
        point,meter=self.facility();order=self.assign();frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.ValidationError):s.record_reading(order.name,order.work_targets[0].target_id,meter.name,10,now_datetime(),uuid.uuid4().hex,'Wrong point')
    def test_idempotent_scope_retry_and_stale_key(self):
        order=self.make();targets=[dict(kind='Equipment',equipment=self.eq.name)];key=uuid.uuid4().hex
        first=self.configure(order,targets,key);self.assertFalse(self.configure(order,targets,key)['created'])
        self.configure(order,[dict(kind='Reference',label='Other work')])
        with self.assertRaises(frappe.ValidationError):self.configure(order,targets,key)
    def test_direct_child_mutation_and_unassigned_reading_denied(self):
        order=self.assign();frappe.set_user(self.users['other'])
        with self.assertRaises(frappe.PermissionError):s.overview(order.name)
        frappe.set_user('Administrator');row=frappe.get_doc(s.TARGET,order.work_targets[0].name);row.label='Tampered'
        with self.assertRaises(frappe.PermissionError):row.save()
    def test_new_unplaced_asset_work_needs_scope_before_authorization(self):
        frappe.set_user('Administrator')
        equipment=frappe.get_doc(dict(doctype='VB Equipment',equipment_code=self.token+'-UNPLACED',equipment_name='Unplaced asset',category=self.category,company=COMPANY_A,site=SITE_A)).insert()
        order=frappe.get_doc(work_contract.create_direct(COMPANY_A,SITE_A,'Inspect unplaced equipment','Review equipment','Medium',uuid.uuid4().hex,'Direct work',equipment=equipment.name))
        order.responsible_team=self.team;order.required_discipline=self.discipline;order.save()
        with self.assertRaises(frappe.ValidationError):apply_workflow(order.as_dict(),'Authorize')
        self.configure(order,[dict(kind='Equipment',equipment=equipment.name)])
        self.assertEqual(apply_workflow(order.reload().as_dict(),'Authorize').status,'Authorized')
    def test_foreign_scope_and_point_identity_cannot_be_rebound(self):
        point,meter=self.facility();point.functional_location=self.location.name;point.site=SITE_A2
        with self.assertRaises(frappe.ValidationError):point.save()
        meter.measurement_point=None;meter.equipment=self.eq.name
        with self.assertRaises(frappe.ValidationError):meter.save()
    def test_legacy_order_is_not_silently_reinterpreted(self):
        order=self.make();frappe.set_user('Administrator');frappe.db.set_value(order.doctype,order.name,{'scope_policy':None,'scope_location':None})
        order.reload();frappe.set_user(self.users['supervisor']);self.assertEqual(apply_workflow(order.as_dict(),'Authorize').status,'Authorized')
    def test_component_target_keeps_parent_asset_reference(self):
        from vanbags_maintenance import components
        frappe.set_user('Administrator');component=frappe.get_doc(dict(doctype=components.DT,code=self.token+'-CMP',component_name='Critical motor',position='MOTOR-1',company=COMPANY_A,site=SITE_A,equipment=self.eq.name)).insert()
        order=self.make();self.configure(order,[dict(kind='Component',component=component.name)])
        self.assertEqual(order.reload().work_targets[0].equipment,self.eq.name)
    def test_authorization_rechecks_secondary_point_current_scope(self):
        order=self.make();self.configure(order,[dict(kind='Location',functional_location=self.location.name),dict(kind='Equipment',equipment=self.eq.name)])
        frappe.set_user('Administrator');frappe.db.set_value('VB Equipment',self.eq.name,'site',SITE_A2)
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises((frappe.ValidationError,frappe.PermissionError)):
            apply_workflow(order.reload().as_dict(),'Authorize')
        self.assertEqual(order.reload().status,'Draft')
    def test_authorization_rechecks_disabled_facility_point(self):
        point,meter=self.facility();order=self.make();self.configure(order,[dict(kind='Measurement Point',measurement_point=point.name)])
        frappe.set_user('Administrator');point.disabled=1;point.save()
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.ValidationError):apply_workflow(order.reload().as_dict(),'Authorize')
