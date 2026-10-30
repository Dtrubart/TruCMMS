import json,uuid
from datetime import timedelta
import frappe
from frappe.utils import getdate
from frappe.model.workflow import apply_workflow
from vanbags_maintenance import materials as mat, logistics, job_plans as jp, preventive as pm
from vanbags_maintenance.test_support import COMPANY_A,SITE_A,SITE_A2,SITE_B,COMPANY_B,stock_catalog
from vanbags_maintenance.vanbags_maintenance.test_preventive import PreventiveCase


class TestMaterialHandoff(PreventiveCase):
    def setUp(self):
        super().setUp()
        group=stock_catalog()
        self.item=frappe.get_doc({'doctype':'Item','item_code':self.token+'PART','item_name':'Synthetic spare',
            'item_group':group,'stock_uom':'Nos','is_stock_item':1}).insert().name
        self.warehouse=frappe.get_doc({'doctype':'Warehouse','warehouse_name':self.token,'company':COMPANY_A}).insert().name
        frappe.get_doc({'doctype':logistics.DT,'company':COMPANY_A,'site':SITE_A,'warehouse':self.warehouse,'change_reason':'Synthetic material handoff'}).insert()
        user=frappe.get_doc('User',self.users['supervisor']);user.append('roles',{'role':'Stock User'});user.save();frappe.clear_cache(user=user.name)
        self.period=dict(company=COMPANY_A,site=SITE_A,from_date=str(getdate()),to_date=str(getdate()+timedelta(days=28)))

    def material_plan(self,quantity=2):
        frappe.set_user(self.users['dispatcher']);self.number+=1
        parent=frappe.get_doc({'doctype':jp.PLAN,'code':self.token+'M'+str(self.number),'plan_name':'Material routine','company':COMPANY_A,'site':SITE_A}).insert()
        revision=frappe.get_doc({'doctype':jp.REVISION,'job_plan':parent.name,'revision_title':'Replace spare',
            'change_reason':'Synthetic materials','tasks':[{'task_code':'inspect','instructions':'Inspect','mandatory':1}],
            'materials':[{'item':self.item,'quantity':quantity,'uom':'Nos'}]}).insert()
        frappe.set_user(self.users['supervisor']);jp.approve(revision.name,'Approved material estimate')
        return self.plan(revision=revision)

    def report(self):
        frappe.set_user(self.users['supervisor']);return mat.forecast(**self.period)

    def buy(self,keys=None,key=None,**kw):
        keys=keys if keys is not None else [r['key'] for r in self.report()['rows'] if not r['covered']]
        return mat.purchase_request(**self.period,warehouse=self.warehouse,keys=keys,key=key or uuid.uuid4().hex,reason='Reviewed gross material demand',**kw)

    def issue(self,order,key=None,items=None):
        return mat.issue_request(order.name,self.warehouse,items or [{'item':self.item,'quantity':2,'stock_uom':'Nos'}],key or uuid.uuid4().hex,'Materials required for authorized maintenance')

    def test_forecast_uses_frozen_materials_and_aggregates_stock_units(self):
        plan=self.material_plan();report=self.report()
        self.assertEqual(len(report['rows']),5)
        self.assertEqual(report['totals'][0]['quantity'],10)
        self.assertEqual(report['totals'][0]['unrequested_quantity'],10)
        self.assertIn('Gross',report['basis'])

    def test_released_occurrence_and_work_order_are_one_demand(self):
        plan=self.material_plan();before=self.report()
        self.release(plan)
        after=self.report()
        self.assertEqual([r['key'] for r in before['rows']],[r['key'] for r in after['rows']])
        self.assertEqual(after['totals'][0]['quantity'],10)

    def test_skipped_cancelled_and_paused_planned_sources_are_not_forecast(self):
        plan=self.material_plan();rows=self.occurrences(plan)
        pm.change_occurrence(rows[0].name,'Skip','Capacity unavailable')
        pm.change_occurrence(rows[1].name,'Cancel','No longer needed')
        self.assertEqual(len(self.report()['rows']),3)
        pm.disposition(plan.name,'Pause','Planning suspended')
        self.assertEqual(self.report()['rows'],[])

    def test_purchase_handoff_is_native_draft_with_source_links(self):
        self.material_plan();result=self.buy();doc=frappe.get_doc('Material Request',result['name'])
        self.assertEqual(doc.material_request_type,'Purchase');self.assertEqual(doc.docstatus,0)
        self.assertEqual(doc.company,COMPANY_A);self.assertEqual(doc.trucmms_site,SITE_A)
        self.assertEqual(len(doc.items),5)
        self.assertTrue(all(r.trucmms_occurrence and r.trucmms_source_key==r.trucmms_active_key for r in doc.items))
        self.assertEqual(self.report()['totals'][0]['unrequested_quantity'],0)

    def test_exact_purchase_retry_returns_same_native_document(self):
        self.material_plan();keys=[r['key'] for r in self.report()['rows']];key=uuid.uuid4().hex
        first=self.buy(keys,key);again=self.buy(keys,key)
        self.assertEqual(first['name'],again['name']);self.assertFalse(again['created'])

    def test_changed_retry_payload_rejected(self):
        self.material_plan();keys=[r['key'] for r in self.report()['rows']];key=uuid.uuid4().hex
        self.buy(keys,key)
        with self.assertRaises(frappe.ValidationError):self.buy(keys[:1],key)

    def test_different_request_key_does_not_duplicate_existing_forecast(self):
        self.material_plan();keys=[r['key'] for r in self.report()['rows']];self.buy(keys)
        with self.assertRaises(frappe.ValidationError):self.buy(keys)

    def test_selected_forecast_subset_leaves_other_requirements_unrequested(self):
        self.material_plan();keys=[r['key'] for r in self.report()['rows']]
        self.buy(keys[:1]);self.assertEqual(self.report()['totals'][0]['unrequested_quantity'],8)

    def test_native_cancellation_preserves_source_and_allows_new_handoff(self):
        self.material_plan();keys=[r['key'] for r in self.report()['rows']]
        result=self.buy(keys);doc=frappe.get_doc('Material Request',result['name'])
        frappe.set_user('Administrator');doc.submit();doc.cancel()
        self.assertTrue(all(r.trucmms_occurrence for r in doc.items))
        self.assertEqual(self.report()['totals'][0]['unrequested_quantity'],10)
        second=self.buy(keys);self.assertNotEqual(second['name'],doc.name)

    def test_missing_native_create_permission_blocks_handoff(self):
        self.material_plan();keys=[r['key'] for r in self.report()['rows']]
        frappe.set_user(self.users['dispatcher'])
        with self.assertRaises(frappe.PermissionError):self.buy(keys)

    def test_forecast_scopes_dates_and_unrecognized_keys_are_enforced(self):
        self.material_plan()
        with self.assertRaises(frappe.PermissionError):mat.forecast(COMPANY_B,SITE_B,self.period['from_date'],self.period['to_date'])
        with self.assertRaises(frappe.ValidationError):mat.forecast(COMPANY_A,SITE_A,'2026-01-01','2028-01-01')
        with self.assertRaises(frappe.ValidationError):self.buy(['forged-key'])

    def test_requester_cannot_read_forecast(self):
        frappe.set_user(self.users['requester'])
        with self.assertRaises(frappe.PermissionError):mat.forecast(**self.period)

    def test_unmapped_warehouse_is_rejected(self):
        self.material_plan();keys=[r['key'] for r in self.report()['rows']]
        frappe.set_user('Administrator');other=frappe.get_doc({'doctype':'Warehouse','warehouse_name':self.token+'OTHER','company':COMPANY_A}).insert()
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.ValidationError):mat.purchase_request(**self.period,warehouse=other.name,keys=keys,key=uuid.uuid4().hex,reason='Test invalid warehouse')

    def test_native_draft_cannot_forge_maintenance_origin(self):
        frappe.set_user('Administrator')
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc({'doctype':'Material Request','company':COMPANY_A,'material_request_type':'Purchase',
                'transaction_date':getdate(),'schedule_date':getdate(),'trucmms_origin':'TruCMMS','trucmms_site':SITE_A,
                'items':[{'item_code':self.item,'qty':1,'warehouse':self.warehouse,'schedule_date':getdate()}]}).insert()

    def test_native_draft_provenance_is_frozen_but_quantity_can_be_reviewed(self):
        self.material_plan();doc=frappe.get_doc('Material Request',self.buy()['name'])
        doc.items[0].qty=3;doc.save()
        self.assertEqual(doc.items[0].qty,3)
        doc.items[0].trucmms_source_key='forged'
        with self.assertRaises(frappe.ValidationError):doc.save()

    def test_issue_request_links_authorized_order_and_native_stock_workflow(self):
        order=self.authorize();result=self.issue(order);doc=frappe.get_doc('Material Request',result['name'])
        self.assertEqual(doc.material_request_type,'Material Issue');self.assertEqual(doc.docstatus,0)
        self.assertEqual(doc.trucmms_work_order,order.name);self.assertEqual(doc.items[0].qty,2)

    def test_issue_draft_is_not_stock_consumption(self):
        order=self.authorize();before={dt:frappe.db.count(dt) for dt in ('Stock Entry','Stock Ledger Entry','GL Entry')}
        self.issue(order)
        self.assertEqual(before,{dt:frappe.db.count(dt) for dt in before})

    def test_issue_retry_is_idempotent(self):
        order=self.authorize();key=uuid.uuid4().hex
        self.assertEqual(self.issue(order,key)['name'],self.issue(order,key)['name'])

    def test_unauthorized_order_and_nonstock_issue_rejected(self):
        order=self.make();frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.ValidationError):self.issue(order)
        frappe.set_user('Administrator');frappe.db.set_value('Item',self.item,'is_stock_item',0)
        order=self.authorize()
        with self.assertRaises(frappe.ValidationError):self.issue(order)

    def test_technician_needs_assignment_and_native_material_permission(self):
        order=self.assign();frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.PermissionError):self.issue(order)
        frappe.set_user('Administrator');user=frappe.get_doc('User',self.users['other']);user.append('roles',{'role':'Stock User'});user.save();frappe.clear_cache(user=user.name)
        frappe.set_user(user.name)
        with self.assertRaises(frappe.PermissionError):self.issue(order)

    def test_native_request_list_filters_other_site_and_share_cannot_bypass(self):
        self.material_plan();doc=frappe.get_doc('Material Request',self.buy()['name'])
        frappe.set_user('Administrator');frappe.db.set_value('Material Request',doc.name,'trucmms_site',SITE_A2)
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc({'doctype':'DocShare','share_doctype':'Material Request','share_name':doc.name,'user':self.users['supervisor'],'read':1}).insert()
        frappe.set_user(self.users['supervisor'])
        self.assertNotIn(doc.name,frappe.get_list('Material Request',pluck='name'))
        with self.assertRaises(frappe.PermissionError):frappe.get_doc('Material Request',doc.name).check_permission('read')

    def test_normal_native_request_keeps_native_access_without_cmms_site(self):
        frappe.set_user(self.users['supervisor'])
        doc=frappe.get_doc({'doctype':'Material Request','company':COMPANY_A,'material_request_type':'Purchase',
            'transaction_date':getdate(),'schedule_date':getdate(),'items':[{'item_code':self.item,'qty':1,'warehouse':self.warehouse,'schedule_date':getdate()}]}).insert()
        self.assertIn(doc.name,frappe.get_list('Material Request',pluck='name'))
        doc.check_permission('read')

    def test_stock_movement_reference_cannot_bypass_request_site(self):
        self.material_plan();request=self.buy()['name']
        frappe.set_user('Administrator');frappe.db.set_value('Material Request',request,'trucmms_site',SITE_A2)
        frappe.set_user(self.users['supervisor'])
        stock=frappe.get_doc({'doctype':'Stock Entry','company':COMPANY_A,'items':[{'item_code':self.item,'material_request':request,'s_warehouse':self.warehouse,'qty':1}]})
        with self.assertRaises(frappe.PermissionError):mat.guard_stock_entry(stock,'validate')

    def test_native_amendment_cannot_silently_drop_maintenance_provenance(self):
        self.material_plan();doc=frappe.get_doc('Material Request',self.buy()['name'])
        frappe.set_user('Administrator');doc.submit();doc.cancel()
        amendment=frappe.copy_doc(doc);amendment.docstatus=0;amendment.amended_from=doc.name
        with self.assertRaises(frappe.ValidationError):amendment.insert()
