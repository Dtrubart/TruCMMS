import uuid
import frappe
from vanbags_maintenance import fulfillment as f
from vanbags_maintenance.vanbags_maintenance.test_materials import MaterialCase

class TestFulfillment(MaterialCase):
    def stock_issue(self, qty=2):
        order=self.assign()
        request=self.issue(order)['name']
        frappe.set_user('Administrator')
        frappe.get_doc('Material Request',request).submit()
        receipt=frappe.get_doc(dict(doctype='Stock Entry',stock_entry_type='Material Receipt',purpose='Material Receipt',
            company=order.company,items=[dict(item_code=self.item,qty=20,t_warehouse=self.warehouse,basic_rate=10)])).insert()
        receipt.submit()
        result=f.delivery(request,uuid.uuid4().hex)
        stock=frappe.get_doc('Stock Entry',result['name']);stock.items[0].qty=qty;stock.save();stock.submit()
        return order,stock

    def test_native_issue_acknowledgment_partial_return_and_reconciliation(self):
        order,stock=self.stock_issue()
        self.assertEqual(stock.trucmms_work_order,order.name)
        frappe.set_user(self.users['tech'])
        ack=f.acknowledge(stock.name,'Materials collected from warehouse')
        self.assertFalse(f.acknowledge(stock.name,'Retry collection')['created'])
        self.assertEqual(frappe.get_doc(f.ACK,ack['name']).received_by,self.users['tech'])
        rendered=frappe.render_template(f.COLLECTION_PRINT,{'doc':frappe.get_doc(f.ACK,ack['name'])})
        self.assertIn(self.item,rendered);self.assertIn(self.users['tech'],rendered)
        frappe.set_user('Administrator')
        ret=frappe.get_doc('Stock Entry',f.return_draft(stock.name,uuid.uuid4().hex)['name'])
        ret.items[0].qty=1;ret.save();ret.submit()
        report=f.reconciliation(order.name)
        self.assertEqual((report['rows'][0]['issued'],report['rows'][0]['returned'],report['rows'][0]['net_issued']),(2,1,1))
        with self.assertRaises(frappe.ValidationError):stock.cancel()
        ret.reload().cancel();stock.reload().cancel()
        self.assertEqual(f.reconciliation(order.name)['rows'][0]['net_issued'],0)
        self.assertTrue(frappe.db.exists(f.ACK,ack['name']))

    def test_overdelivery_and_overreturn_are_rejected(self):
        order,stock=self.stock_issue()
        ret=frappe.get_doc('Stock Entry',f.return_draft(stock.name,uuid.uuid4().hex)['name'])
        ret.items[0].qty=3
        with self.assertRaises(frappe.ValidationError):ret.save()

    def test_collection_requires_assigned_or_supervisor_access(self):
        order,stock=self.stock_issue()
        frappe.set_user(self.users['other'])
        with self.assertRaises(frappe.PermissionError):f.acknowledge(stock.name,'Not assigned to this work')
        frappe.set_user(self.users['requester'])
        with self.assertRaises(frappe.PermissionError):f.acknowledge(stock.name,'Requester cannot collect')

    def test_native_issue_draft_retry_and_scope_guard(self):
        order=self.assign();request=self.issue(order)['name'];frappe.set_user('Administrator')
        frappe.get_doc('Material Request',request).submit()
        frappe.db.set_value('Item',self.item,'valuation_rate',10)
        key=uuid.uuid4().hex;result=f.delivery(request,key)
        self.assertEqual(result['name'],f.delivery(request,key)['name'])
        stock=frappe.get_doc('Stock Entry',result['name']);stock.trucmms_site='CMMS-TEST-A2'
        with self.assertRaises(frappe.ValidationError):stock.save()

    def test_costs_reconcile_to_native_ledger_and_hide_incomplete_totals(self):
        from vanbags_maintenance import resource_costs
        order,stock=self.stock_issue()
        report=resource_costs.summary(order.name)
        self.assertTrue(report['complete']);self.assertEqual(report['components']['materials']['amount'],20)
        ret=frappe.get_doc('Stock Entry',f.return_draft(stock.name,uuid.uuid4().hex)['name'])
        ret.items[0].qty=1;ret.save();ret.submit()
        self.assertEqual(resource_costs.summary(order.name)['components']['materials']['amount'],10)
        frappe.set_user(self.users['dispatcher'])
        report=resource_costs.summary(order.name)
        self.assertFalse(report['complete']);self.assertIsNone(report['total'])

    def test_cancelled_issue_keeps_printable_acknowledgment_history(self):
        order,stock=self.stock_issue()
        frappe.set_user(self.users['tech']);ack=f.acknowledge(stock.name,'Collected and counted')
        doc=frappe.get_doc(f.ACK,ack['name']);doc.check_permission('read')
        with self.assertRaises(frappe.PermissionError):doc.delete()
        frappe.set_user('Administrator');stock.reload().cancel()
        frappe.set_user(self.users['tech']);doc.check_permission('read')
        self.assertIn(doc.name,frappe.get_list(f.ACK,pluck='name'))

    def test_two_draft_returns_cannot_exceed_original_quantity(self):
        order,stock=self.stock_issue()
        first=frappe.get_doc('Stock Entry',f.return_draft(stock.name,uuid.uuid4().hex)['name'])
        second=frappe.get_doc('Stock Entry',f.return_draft(stock.name,uuid.uuid4().hex)['name'])
        first.submit()
        with self.assertRaises(frappe.ValidationError):second.reload().submit()

    def test_two_draft_issues_cannot_exceed_original_request(self):
        order,stock=self.stock_issue(qty=1)
        request=stock.items[0].material_request
        first=frappe.get_doc('Stock Entry',f.delivery(request,uuid.uuid4().hex)['name'])
        second=frappe.get_doc('Stock Entry',f.delivery(request,uuid.uuid4().hex)['name'])
        first.submit()
        with self.assertRaises(frappe.ValidationError):second.reload().submit()

    def test_cannot_forge_direct_child_return_reference(self):
        order,stock=self.stock_issue()
        row=frappe.get_doc('Stock Entry Detail',stock.items[0].name);row.trucmms_issue_detail='forged'
        with self.assertRaises(frappe.PermissionError):row.save()

    def tracked_return(self,serial=False):
        frappe.set_user('Administrator')
        frappe.db.set_single_value('Stock Settings','enable_serial_and_batch_no_for_item',1)
        frappe.db.set_single_value('Stock Settings','use_serial_batch_fields',1)
        frappe.clear_document_cache('Stock Settings','Stock Settings')
        item=frappe.get_doc('Item',self.item)
        item.has_serial_no=int(serial);item.has_batch_no=int(not serial);item.save()
        values={'use_serial_batch_fields':1}
        if serial:values['serial_no']=self.token+'-01\n'+self.token+'-02'
        else:
            batch=frappe.get_doc(dict(doctype='Batch',batch_id=self.token+'-B',item=self.item)).insert()
            values['batch_no']=batch.name
        order=self.assign();request=self.issue(order)['name'];frappe.set_user('Administrator')
        frappe.get_doc('Material Request',request).submit()
        receipt=frappe.get_doc(dict(doctype='Stock Entry',stock_entry_type='Material Receipt',purpose='Material Receipt',company=order.company,
            items=[dict(item_code=self.item,qty=2,t_warehouse=self.warehouse,basic_rate=10,**values)])).insert();receipt.submit()
        issue=frappe.get_doc('Stock Entry',f.delivery(request,uuid.uuid4().hex)['name'])
        issue.items[0].update(values);issue.save();issue.submit()
        ret=frappe.get_doc('Stock Entry',f.return_draft(issue.name,uuid.uuid4().hex)['name'])
        if serial:ret.remove(ret.items[-1])
        else:ret.items[0].qty=1
        ret.save();ret.submit()
        self.assertEqual(f.reconciliation(order.name)['rows'][0]['returned'],1)
        remainder=frappe.get_doc('Stock Entry',f.return_draft(issue.name,uuid.uuid4().hex)['name']);remainder.submit()
        self.assertEqual(f.reconciliation(order.name)['rows'][0]['net_issued'],0)

    def test_native_batch_partial_returns_preserve_original_batch(self):self.tracked_return()

    def test_native_serial_partial_returns_preserve_original_serials(self):self.tracked_return(serial=True)

    def test_cancellation_cannot_strip_scope_or_change_movement_lines(self):
        order,stock=self.stock_issue()
        stock.trucmms_work_order=None;stock.trucmms_site=None
        with self.assertRaises(frappe.ValidationError):f.before_cancel(stock)
        stock.reload();stock.items[0].qty=99
        with self.assertRaises(frappe.ValidationError):f.before_cancel(stock)
