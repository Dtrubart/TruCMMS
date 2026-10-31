import uuid
import frappe
from frappe.utils import getdate
from vanbags_maintenance import resource_planning as plan, resource_costs as costs, materials as mat
from vanbags_maintenance.vanbags_maintenance.test_materials import MaterialCase

class TestResourcePlanning(MaterialCase):
    def estimate(self,quantity=4):
        order=self.authorize()
        return frappe.get_doc(dict(doctype=plan.DT,work_order=order.name,item=self.item,quantity=quantity,needed_on=getdate(),reason='Additional corrective spare requirement')).insert()

    def test_direct_estimate_forecast_purchase_and_frozen_origin(self):
        estimate=self.estimate();report=self.report()
        self.assertEqual(report['totals'][0]['quantity'],4)
        request=frappe.get_doc('Material Request',self.buy()['name'])
        self.assertEqual(request.trucmms_sources[0].estimate,estimate.name)
        estimate.quantity=8
        with self.assertRaises(frappe.ValidationError):estimate.save()
        self.assertEqual(self.report()['totals'][0]['unrequested_quantity'],0)

    def test_estimates_are_explicitly_additive_to_pm_requirements(self):
        self.material_plan();self.estimate()
        self.assertEqual(self.report()['totals'][0]['quantity'],14)

    def test_unhanded_estimate_can_be_revised_and_disabled(self):
        estimate=self.estimate();estimate.quantity=3;estimate.save()
        self.assertEqual(self.report()['totals'][0]['quantity'],3)
        estimate.disabled=1;estimate.save();self.assertEqual(self.report()['rows'],[])

    def test_advisory_availability_uses_native_stock_and_no_reservation(self):
        self.estimate();frappe.set_user('Administrator')
        receipt=frappe.get_doc(dict(doctype='Stock Entry',purpose='Material Receipt',stock_entry_type='Material Receipt',company=self.period['company'],items=[dict(item_code=self.item,qty=3,t_warehouse=self.warehouse,basic_rate=5)])).insert();receipt.submit()
        report=plan.availability(**self.period,warehouse=self.warehouse)
        row=report['totals'][0];self.assertEqual(row['available_now'],3);self.assertEqual(row['suggested_purchase'],1)
        self.assertEqual(frappe.db.get_value('Bin',{'item_code':self.item,'warehouse':self.warehouse},'actual_qty'),3)

    def test_shopping_template_has_explicit_units_and_scope(self):
        self.estimate();plan.shopping_csv(**self.period)
        text=frappe.local.response.filecontent.decode('utf-8-sig')
        self.assertIn('Stock UOM',text);self.assertIn(self.item,text);self.assertIn(self.period['site'],text)

    def test_estimate_cross_site_and_requester_access_denied(self):
        estimate=self.estimate();frappe.set_user(self.users['requester'])
        with self.assertRaises(frappe.PermissionError):estimate.check_permission('read')

    def test_stock_invoice_cost_link_is_rejected_to_prevent_double_counting(self):
        order=self.authorize();frappe.set_user('Administrator')
        doc=frappe.get_doc(dict(doctype='Purchase Invoice',company=order.company,items=[dict(item_code=self.item,trucmms_work_order=order.name)]))
        with self.assertRaises(frappe.ValidationError):costs.validate_links(doc)

    def test_native_service_invoice_and_credit_reconcile_in_company_currency(self):
        order=self.authorize();frappe.set_user('Administrator')
        group=frappe.db.get_value('Supplier Group',{'is_group':1},'name')
        if not group:group=frappe.get_doc(dict(doctype='Supplier Group',supplier_group_name=self.token,is_group=1)).insert().name
        supplier=frappe.get_doc(dict(doctype='Supplier',supplier_name=self.token,supplier_group=group,supplier_type='Company')).insert()
        item=frappe.get_doc('Item',self.item);item.is_stock_item=0;item.save()
        invoice=frappe.get_doc(dict(doctype='Purchase Invoice',supplier=supplier.name,company=order.company,currency='CAD',conversion_rate=1,
            items=[dict(item_code=self.item,qty=1,rate=75,trucmms_work_order=order.name)])).insert();invoice.submit()
        self.assertEqual(costs.summary(order.name)['components']['services']['amount'],75)
        from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import make_debit_note
        credit=make_debit_note(invoice.name);self.assertEqual(credit.items[0].trucmms_work_order,order.name);credit.insert();credit.submit()
        self.assertEqual(costs.summary(order.name)['components']['services']['amount'],0)

    def test_native_employee_timesheet_cost_and_cancellation(self):
        from frappe.utils import now_datetime,add_to_date
        order=self.authorize();frappe.set_user('Administrator')
        if not frappe.db.exists('Gender','Male'):frappe.get_doc(dict(doctype='Gender',gender='Male')).insert()
        employee=frappe.get_doc(dict(doctype='Employee',first_name=self.token,gender='Male',date_of_birth='1990-01-01',date_of_joining='2020-01-01',company=order.company,status='Active')).insert()
        activity=frappe.get_doc(dict(doctype='Activity Type',activity_type=self.token,costing_rate=25)).insert()
        start=add_to_date(now_datetime(),hours=-2)
        timesheet=frappe.get_doc(dict(doctype='Timesheet',employee=employee.name,company=order.company,currency='CAD',exchange_rate=1,time_logs=[dict(activity_type=activity.name,from_time=start,to_time=add_to_date(start,hours=1),costing_rate=25,trucmms_work_order=order.name)])).insert();timesheet.submit()
        self.assertEqual(costs.summary(order.name)['components']['labor']['amount'],25)
        timesheet.cancel();self.assertEqual(costs.summary(order.name)['components']['labor']['amount'],0)

    def test_cost_links_enforce_site_and_cannot_be_shared(self):
        from vanbags_maintenance.test_support import SITE_A2
        order=self.authorize();frappe.set_user('Administrator')
        doc=frappe.get_doc(dict(doctype='Purchase Invoice',company=order.company,items=[dict(item_code=self.item,trucmms_work_order=order.name)]))
        frappe.db.set_value(order.doctype,order.name,'site',SITE_A2)
        frappe.set_user(self.users['supervisor'])
        with self.assertRaises(frappe.PermissionError):costs.native_permission(doc)
        with self.assertRaises(frappe.PermissionError):costs.validate_links(doc)

    def test_cost_child_reference_cannot_be_forged_directly(self):
        row=frappe.get_doc(dict(doctype='Timesheet Detail',trucmms_work_order='forged'))
        with self.assertRaises(frappe.PermissionError):costs.guard_cost_child(row)
