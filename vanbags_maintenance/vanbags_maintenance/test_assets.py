import json,uuid
import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime,add_to_date
from vanbags_maintenance import assets as a
from vanbags_maintenance.test_support import COMPANY_A,COMPANY_B,SITE_A,SITE_A2,SITE_B,grant_scope

class TestAssets(IntegrationTestCase):
    def setUp(self):
        super().setUp();frappe.db.savepoint('asset_case');frappe.set_user('Administrator');self.token='D-'+uuid.uuid4().hex[:10].upper()
        self.category=frappe.get_doc({'doctype':'VB Equipment Category','category_name':self.token}).insert().name
        self.locations=[]
        for i,site in enumerate([SITE_A,SITE_A,SITE_A2]):
            self.locations.append(frappe.get_doc({'doctype':'VB Equipment Location','location_name':self.token+str(i),'company':COMPANY_A,'site':site,'single_equipment':int(i==0)}).insert().name)
        self.eq=self.equipment('ONE',self.locations[0]);self.spare=self.equipment('TWO')
        self.user=frappe.get_doc({'doctype':'User','email':self.token.lower()+'@example.com','first_name':'Asset manager','send_welcome_email':0,'roles':[{'role':'VB Maintenance Manager'}]}).insert().name
        grant_scope(self.user)
    def tearDown(self):
        frappe.set_user('Administrator');frappe.db.rollback(save_point='asset_case');super().tearDown()
    def equipment(self,suffix,location=None,company=COMPANY_A,site=SITE_A,**values):
        return frappe.get_doc({'doctype':a.EQ,'equipment_code':self.token+suffix,'equipment_name':'Asset verification','category':self.category,'company':company,'site':site,'location':location,**values}).insert()
    def profile(self,definitions=None):
        return frappe.get_doc({'doctype':a.PROFILE,'code':self.token,'profile_name':'HVAC typed profile','version':1,'definitions':definitions or [{'key':'power_kw','label':'Rated power','value_type':'Decimal','unit':'kW','required':1,'minimum':'0','maximum':'500'},{'key':'stages','label':'Stages','value_type':'Integer','minimum':'1'},{'key':'commissioned','label':'Commissioned','value_type':'Date'},{'key':'guarded','label':'Guarded','value_type':'Boolean'},{'key':'service','label':'Service','value_type':'Choice','choices':'Internal\nContractor'}]}).insert()
    def config(self,**kw):return a.configure(self.eq.name,'Declared configuration',**kw)
    def test_new_equipment_records_real_initial_baseline(self):
        row=a.current(self.eq);self.assertEqual(self.eq.placement_policy,'D1');self.assertEqual(row.location,self.locations[0]);self.assertEqual(row.recorded_by,'Administrator');self.assertEqual(row.entry_type,'Initial')
    def test_legacy_adoption_does_not_invent_installation_date(self):
        # An actual legacy shape, not a client-created downgrade.
        for row in frappe.get_all(a.INSTALL,filters={'equipment':self.spare.name},pluck='name'):frappe.db.delete(a.INSTALL,{'name':row})
        frappe.db.set_value(a.EQ,self.spare.name,'placement_policy','Legacy');before=now_datetime();a.adopt(self.spare.name,'Declare observed custody');self.spare.reload();row=a.current(self.spare)
        self.assertGreaterEqual(row.effective_from,before);self.assertEqual(self.spare.placement_policy,'D1');self.assertEqual(row.entry_type,'Declared Baseline');self.assertEqual(row.reason,'Declare observed custody')
        with self.assertRaises(frappe.ValidationError):a.adopt(self.spare.name,'Again')
    def test_direct_relocation_is_blocked(self):
        self.eq.location=self.locations[1]
        with self.assertRaises(frappe.ValidationError):self.eq.save()
    def test_placement_keeps_identity_and_nonoverlapping_history(self):
        result=a.place(self.eq.name,SITE_A,self.locations[1],'Relocate machine');self.assertEqual(result['name'],self.eq.name)
        rows=frappe.get_all(a.INSTALL,filters={'equipment':self.eq.name},fields=['effective_from','effective_until'],order_by='effective_from')
        self.assertEqual(len(rows),2);self.assertEqual(rows[0].effective_until,rows[1].effective_from);self.assertFalse(rows[1].effective_until)
    def test_single_position_blocks_new_and_moved_equipment(self):
        with self.assertRaises(frappe.ValidationError):self.equipment('THREE',self.locations[0])
        with self.assertRaises(frappe.ValidationError):a.place(self.spare.name,SITE_A,self.locations[0],'Try occupied position')
    def test_multi_equipment_position_accepts_multiple_assets(self):
        a.place(self.eq.name,SITE_A,self.locations[1],'Shared area');a.place(self.spare.name,SITE_A,self.locations[1],'Shared area')
        with self.assertRaises(frappe.ValidationError):a.configure_position(self.locations[1],1,'Make exclusive')
    def test_remove_retains_site_and_history(self):
        result=a.remove(self.eq.name,'Removed to stores');self.assertFalse(result['location']);self.assertEqual(result['site'],SITE_A);self.assertFalse(a.current(self.eq));self.assertEqual(frappe.db.count(a.INSTALL,{'equipment':self.eq.name}),1)
    def test_replacement_is_atomic_and_keeps_two_identities(self):
        result=a.replace(self.eq.name,self.spare.name,'Replace AHU');self.assertEqual(result,{'removed':self.eq.name,'installed':self.spare.name});self.eq.reload();self.spare.reload();self.assertFalse(self.eq.location);self.assertEqual(self.spare.location,self.locations[0]);self.assertFalse(a.current(self.eq));self.assertEqual(a.current(self.spare).entry_type,'Replacement')
    def test_failed_replacement_preserves_original(self):
        a.place(self.spare.name,SITE_A,self.locations[1],'Install spare')
        with self.assertRaises(frappe.ValidationError):a.replace(self.eq.name,self.spare.name,'Invalid replacement')
        self.eq.reload();self.assertEqual(self.eq.location,self.locations[0]);self.assertTrue(a.current(self.eq))
    def test_cross_site_transfer_requires_both_scopes(self):
        frappe.set_user(self.user)
        with self.assertRaises(frappe.PermissionError):a.place(self.eq.name,SITE_A2,self.locations[2],'Target denied')
        grant_scope(self.user,site=SITE_A2);result=a.place(self.eq.name,SITE_A2,self.locations[2],'Authorized transfer');self.assertEqual(result['site'],SITE_A2)
    def test_history_permissions_cannot_be_shared_across_sites(self):
        row=a.current(self.eq);user=self.user;frappe.set_user(user);row.check_permission('read');frappe.set_user('Administrator');grant_scope(user,site=SITE_A2)
        event_name=a.place(self.eq.name,SITE_A2,self.locations[2],'Transfer')['name'];events=frappe.get_all(a.EVENT,filters={'equipment':event_name},pluck='name');event=frappe.get_doc(a.EVENT,events[0]);frappe.set_user(user);event.check_permission('read');frappe.set_user('Administrator')
        for name in frappe.get_all('User Permission',filters={'user':user,'allow':'TruCMMS Site','for_value':SITE_A},pluck='name'):frappe.delete_doc('User Permission',name)
        frappe.set_user(user)
        with self.assertRaises(frappe.PermissionError):event.check_permission('read')
        self.assertEqual(frappe.get_list(a.EVENT,filters={'equipment':self.eq.name}),[])
    def test_cross_company_replacement_is_denied(self):
        foreign=self.equipment('FOREIGN',company=COMPANY_B,site=SITE_B)
        with self.assertRaises(frappe.ValidationError):a.replace(self.eq.name,foreign.name,'Cross company')
    def test_future_and_out_of_order_movements_rejected(self):
        for value in [add_to_date(now_datetime(),days=1),add_to_date(now_datetime(),days=-1)]:
            with self.assertRaises(frappe.ValidationError):a.place(self.eq.name,SITE_A,self.locations[1],'Invalid time',value)
        self.eq.reload();self.assertEqual(self.eq.location,self.locations[0])
    def test_history_cannot_be_inserted_edited_or_deleted_directly(self):
        row=a.current(self.eq);row.reason='Forged'
        with self.assertRaises(frappe.PermissionError):row.save()
        with self.assertRaises(frappe.PermissionError):row.delete()
        with self.assertRaises(frappe.PermissionError):frappe.get_doc({'doctype':a.EVENT,'equipment':self.eq.name,'company':COMPANY_A,'site':SITE_A,'action':'Fake','reason':'Fake','effective_on':now_datetime(),'recorded_on':now_datetime(),'recorded_by':'Administrator'}).insert()
    def test_tag_is_company_unique_normalized_and_identity_stays_stable(self):
        doc=self.config(asset_tag=' ahu  001 ');self.assertEqual(doc['asset_tag'],'AHU 001');self.assertEqual(doc['name'],self.eq.name)
        with self.assertRaises((frappe.UniqueValidationError,frappe.DuplicateEntryError)):a.configure(self.spare.name,'Duplicate tag',asset_tag='AHU 001')
        other=self.equipment('FOREIGN',company=COMPANY_B,site=SITE_B);a.configure(other.name,'Independent company',asset_tag='AHU 001')
    def test_direct_tag_and_snapshot_forgery_is_rejected(self):
        self.eq.asset_tag='FORGED'
        with self.assertRaises(frappe.ValidationError):self.eq.save()
        self.eq.reload();self.eq.profile_snapshot='{}'
        with self.assertRaises(frappe.ValidationError):self.eq.save()
    def test_profile_validates_types_bounds_and_snapshot(self):
        profile=self.profile();doc=self.config(technical_profile=profile.name,values={'power_kw':'12.50','stages':'2','commissioned':'2025-10-25','guarded':'1','service':'Internal'})
        self.assertEqual(json.loads(doc['profile_snapshot'])['version'],1);self.assertEqual(doc['attributes'][0]['unit'],'kW');self.assertEqual(doc['attributes'][0]['value_type'],'Decimal')
        for values in [{},{'power_kw':'NaN'},{'power_kw':'501'},{'power_kw':'1','stages':'1.5'},{'power_kw':'1','guarded':'yes'},{'power_kw':'1','commissioned':'2025-02-30'},{'power_kw':'1','service':'Other'},{'power_kw':'1','unknown':'x'}]:
            with self.assertRaises(frappe.ValidationError):self.config(technical_profile=profile.name,values=values)
    def test_profile_definition_is_versioned_not_mutated(self):
        profile=self.profile();profile.definitions[0].unit='HP'
        with self.assertRaises(frappe.ValidationError):profile.save()
    def test_invalid_profile_schema_is_rejected(self):
        for definitions in [[{'key':'bad key','label':'Bad','value_type':'Text'}],[{'key':'a','label':'Bad','value_type':'Integer','minimum':'2','maximum':'1'}],[{'key':'a','label':'Bad','value_type':'Choice','choices':'A\nA'}]]:
            with self.assertRaises(frappe.ValidationError):self.profile(definitions)
    def test_criticality_is_explicit_and_snapshotted(self):
        value=frappe.get_doc({'doctype':a.CRIT,'code':self.token,'criticality_name':'Safety critical','rank':1,'description':'Declared pilot classification'}).insert();doc=self.config(criticality=value.name);self.assertEqual(json.loads(doc['criticality_snapshot'])['rank'],1)
        value.disabled=1;value.save();self.eq.reload();self.eq.equipment_name='Unrelated change';self.eq.save()
        with self.assertRaises(frappe.ValidationError):a.configure(self.spare.name,'Disabled policy',criticality=value.name)
    def test_config_actions_require_manager_and_reason(self):
        frappe.set_user(self.user)
        with self.assertRaises(frappe.ValidationError):a.configure(self.eq.name,'')
        frappe.set_user('Guest')
        with self.assertRaises(frappe.PermissionError):a.remove(self.eq.name,'Unauthorized')
    def test_position_policy_cannot_be_changed_without_reasoned_service(self):
        doc=frappe.get_doc('VB Equipment Location',self.locations[1]);doc.single_equipment=1
        with self.assertRaises(frappe.ValidationError):doc.save()
        a.configure_position(doc.name,1,'Reserve machine position');self.assertTrue(frappe.db.get_value(doc.doctype,doc.name,'single_equipment'));self.assertTrue(frappe.db.exists(a.EVENT,{'location':doc.name,'action':'Configure Position','reason':'Reserve machine position'}))

    def test_installation_report_is_effective_dated_and_scoped(self):
        old=a.current(self.eq);a.place(self.eq.name,SITE_A,self.locations[1],'Move for report')
        rows=a.installation_register({'equipment':self.eq.name,'as_of':old.effective_from})[1];self.assertEqual(len(rows),1);self.assertEqual(rows[0].location,self.locations[0])
        rows=a.installation_register({'equipment':self.eq.name,'active_only':1})[1];self.assertEqual(len(rows),1);self.assertEqual(rows[0].location,self.locations[1])
        frappe.set_user(self.user);self.assertEqual(len(a.installation_register({'equipment':self.eq.name})[1]),2)
    def test_disabled_profile_is_not_newly_assignable(self):
        profile=self.profile();profile.disabled=1;profile.save()
        with self.assertRaises(frappe.ValidationError):self.config(technical_profile=profile.name,values={'power_kw':'10'})
    def test_asset_history_attachments_are_rejected(self):
        from frappe.utils.file_manager import save_file
        row=a.current(self.eq)
        with self.assertRaises(frappe.PermissionError):save_file(self.token+'.txt',b'not an editable audit record',a.INSTALL,row.name,is_private=1)

from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase
class TestAssetWorkContext(WorkOrderCase):
    use_c_policy=True
    def asset_order(self):
        from vanbags_maintenance.work_contract import create_direct
        frappe.set_user('Administrator');category=frappe.get_doc({'doctype':'VB Equipment Category','category_name':self.token}).insert()
        self.asset=frappe.get_doc({'doctype':a.EQ,'equipment_code':self.token.upper(),'equipment_name':'Work context asset','company':COMPANY_A,'site':SITE_A,'location':self.location.name,'category':category.name,'model':'Original model'}).insert()
        frappe.set_user(self.users['dispatcher']);return frappe.get_doc(create_direct(COMPANY_A,SITE_A,'Direct repair','Repair scope','High',uuid.uuid4().hex,'Authorized direct work',equipment=self.asset.name))
    def test_open_order_blocks_equipment_removal(self):
        doc=self.asset_order();frappe.set_user('Administrator')
        with self.assertRaises(frappe.ValidationError):a.remove(self.asset.name,'Try during open work')
        self.asset.reload();self.assertEqual(self.asset.location,self.location.name)
    def test_order_keeps_equipment_context_after_model_changes(self):
        doc=self.asset_order();frappe.set_user('Administrator');self.asset.model='New model';self.asset.save();doc.reload();self.assertEqual(json.loads(doc.equipment_snapshot)['model'],'Original model')
        doc.equipment_snapshot='{}'
        with self.assertRaises(frappe.ValidationError):doc.save()
    def test_new_order_rejects_equipment_from_previous_site(self):
        doc=self.asset_order();frappe.set_user('Administrator');frappe.db.set_value(doc.doctype,doc.name,'status','Cancelled');a.place(self.asset.name,SITE_A2,None,'Transfer after cancellation')
        from vanbags_maintenance.work_contract import create_direct
        with self.assertRaises(frappe.ValidationError):create_direct(COMPANY_A,SITE_A,'Old context','Repair scope','High',uuid.uuid4().hex,'Invalid old site',equipment=self.asset.name)
    def test_reopening_requires_equipment_still_at_order_site(self):
        doc=self.asset_order();frappe.set_user('Administrator');frappe.db.set_value(doc.doctype,doc.name,'status','Closed');a.place(self.asset.name,SITE_A2,None,'Transfer closed equipment')
        from vanbags_maintenance.work_cycle import perform
        with self.assertRaises(frappe.ValidationError):perform(doc.name,'Reopen Order','Cannot reopen old site after relocation')
