"""R3.1 integration: both maintenance and native ERPNext permissions apply."""
import frappe
from vanbags_maintenance import logistics as log
from vanbags_maintenance.test_support import COMPANY_A, COMPANY_B, SITE_A, SITE_A2, SITE_B, grant_scope, stock_catalog
from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase


class TestLogistics(WorkOrderCase):
    def setUp(self):
        super().setUp()
        self.order = self.make()
        frappe.set_user('Administrator')
        self.group = stock_catalog()
        self.warehouse = self.new_warehouse('MAIN')
        self.second = self.new_warehouse('SECOND')
        self.foreign = self.new_warehouse('OTHER', company=COMPANY_B)
        self.binding = self.bind(self.warehouse)
        self.item = self.new_item('STOCK')
        self.service = self.new_item('NONSTOCK', is_stock_item=0)

    def new_warehouse(self, suffix, company=COMPANY_A, **values):
        return frappe.get_doc({'doctype':'Warehouse','warehouse_name':self.token+suffix,'company':company, **values}).insert().name

    def bind(self, warehouse, site=SITE_A, company=COMPANY_A, **values):
        return frappe.get_doc({'doctype':log.DT,'company':company,'site':site,'warehouse':warehouse,'change_reason':'Synthetic site logistics authorization',**values}).insert()

    def new_item(self, suffix, **values):
        return frappe.get_doc({'doctype':'Item','item_code':self.token+suffix,'item_name':self.token+suffix,
            'item_group':self.group,'stock_uom':'Nos','is_stock_item':1,**values}).insert().name

    def stock_role(self, actor='supervisor'):
        frappe.set_user('Administrator')
        user = frappe.get_doc('User',self.users[actor])
        user.append('roles',{'role':'Stock User'})
        user.save()
        frappe.clear_cache(user=user.name)
        frappe.set_user(user.name)

    def test_binding_requires_same_native_company(self):
        with self.assertRaises(frappe.ValidationError): self.bind(self.foreign)

    def test_binding_rejects_group_and_disabled_native_warehouse(self):
        group = self.new_warehouse('GROUP', is_group=1)
        disabled = self.new_warehouse('DISABLED', disabled=1)
        for name in (group, disabled):
            with self.assertRaises(frappe.ValidationError): self.bind(name)

    def test_binding_is_unique_per_site_but_warehouse_can_serve_two_sites(self):
        with self.assertRaises(frappe.DuplicateEntryError): self.bind(self.warehouse)
        other = self.bind(self.warehouse, site=SITE_A2)
        self.assertNotEqual(self.binding.name, other.name)

    def test_binding_cannot_be_retargeted_or_identity_forged(self):
        for field,value in [('warehouse',self.second),('site',SITE_A2),('binding_key','forged')]:
            doc = frappe.get_doc(log.DT,self.binding.name)
            doc.set(field,value)
            with self.assertRaises(frappe.ValidationError): doc.save()

    def test_binding_requires_reason_and_cannot_be_deleted(self):
        self.binding.change_reason = ''
        with self.assertRaises(frappe.ValidationError): self.binding.save()
        with self.assertRaises(frappe.PermissionError): frappe.delete_doc(log.DT,self.binding.name)

    def test_mapping_does_not_grant_native_stock_permissions(self):
        frappe.set_user(self.users['supervisor'])
        before = {dt:bool(frappe.has_permission(dt,'read')) for dt in ('Warehouse','Item','Stock Entry')}
        self.assertFalse(frappe.has_permission('Warehouse','read'))
        result = log.context(self.order.name)
        self.assertFalse(result['can_read_warehouse'])
        self.assertEqual(result['warehouses'],[])
        self.assertEqual(result['can_read_item'],before['Item'])
        self.assertEqual(before,{dt:bool(frappe.has_permission(dt,'read')) for dt in before})
        with self.assertRaises(frappe.PermissionError): self.binding.check_permission('read')
        self.assertEqual(frappe.get_list(log.DT,pluck='name'),[])

    def test_supervisor_with_native_read_can_configure_warehouse(self):
        self.stock_role()
        doc = self.bind(self.second)
        self.assertEqual(doc.site,SITE_A)

    def test_dispatcher_can_read_but_cannot_configure_even_with_stock_role(self):
        self.stock_role('dispatcher')
        self.assertEqual(len(log.context(self.order.name)['warehouses']),1)
        with self.assertRaises(frappe.PermissionError): self.bind(self.second)

    def test_native_warehouse_user_permission_filters_mapping_and_direct_read(self):
        self.bind(self.second)
        self.stock_role()
        frappe.set_user('Administrator')
        frappe.get_doc({'doctype':'User Permission','user':self.users['supervisor'], 'allow':'Warehouse',
            'for_value':self.second,'apply_to_all_doctypes':1}).insert()
        frappe.set_user(self.users['supervisor'])
        self.assertEqual([r.warehouse for r in log.context(self.order.name)['warehouses']],[self.second])
        with self.assertRaises(frappe.PermissionError): self.binding.check_permission('read')

    def test_other_site_not_visible_or_usable_despite_native_stock_role(self):
        other = self.bind(self.second,site=SITE_A2)
        self.stock_role()
        self.assertNotIn(other.name,frappe.get_list(log.DT,pluck='name'))
        with self.assertRaises(frappe.PermissionError): other.check_permission('read')
        with self.assertRaises(frappe.PermissionError): self.bind(self.second,site=SITE_A2)

    def test_disabled_mapping_and_later_disabled_warehouse_excluded(self):
        doc = self.bind(self.second)
        doc.disabled = 1
        doc.change_reason = 'Temporarily unavailable'
        doc.save()
        self.assertEqual(len(log.context(self.order.name)['warehouses']),1)
        frappe.db.set_value('Warehouse',self.warehouse,'disabled',1)
        self.assertEqual(log.context(self.order.name)['warehouses'],[])

    def test_requester_cannot_access_logistics_with_native_stock_role(self):
        self.stock_role('requester')
        with self.assertRaises(frappe.PermissionError): log.context(self.order.name)
        with self.assertRaises(frappe.PermissionError): log.item_choices(self.order.name)

    def test_order_scope_cannot_be_bypassed_by_catalog(self):
        frappe.db.set_value('TruCMMS Maintenance Work Order',self.order.name,{'company':COMPANY_B,'site':SITE_B})
        self.stock_role()
        with self.assertRaises(frappe.PermissionError): log.context(self.order.name)
        with self.assertRaises(frappe.PermissionError): log.item_choices(self.order.name)

    def test_catalog_respects_disabled_templates_native_uom_and_kind(self):
        disabled = self.new_item('DISABLED', disabled=1)
        attribute = frappe.get_doc({'doctype':'Item Attribute','attribute_name':self.token+'ATTRIBUTE',
            'item_attribute_values':[{'attribute_value':'Synthetic','abbr':'SYN'}]}).insert()
        template = self.new_item('TEMPLATE', has_variants=1, attributes=[{'attribute':attribute.name}])
        self.stock_role()
        rows = log.item_choices(self.order.name,search=self.token)
        self.assertEqual({r.name for r in rows},{self.item,self.service})
        self.assertTrue(all(r.stock_uom == 'Nos' for r in rows))
        self.assertEqual([r.name for r in log.item_choices(self.order.name,search=self.token,kind='Stock')],[self.item])
        self.assertEqual([r.name for r in log.item_choices(self.order.name,search=self.token,kind='Non-stock')],[self.service])
        self.assertTrue(all('valuation_rate' not in r and 'standard_rate' not in r for r in rows))

    def test_catalog_honors_native_item_user_permission(self):
        self.stock_role()
        frappe.set_user('Administrator')
        frappe.get_doc({'doctype':'User Permission','user':self.users['supervisor'],'allow':'Item',
            'for_value':self.item,'apply_to_all_doctypes':1}).insert()
        frappe.set_user(self.users['supervisor'])
        self.assertEqual([r.name for r in log.item_choices(self.order.name,search=self.token)],[self.item])

    def test_catalog_limits_and_filter_injection_are_rejected(self):
        for value in (0,51,True,'1 OR 1=1','1.5'):
            with self.assertRaises(frappe.ValidationError): log.item_choices(self.order.name,limit=value)
        with self.assertRaises(frappe.ValidationError): log.item_choices(self.order.name,kind='Anything')
        with self.assertRaises(frappe.ValidationError): log.item_choices(self.order.name,search='x'*101)
        self.assertEqual(log.item_choices(self.order.name,search="' OR 1=1 --"),[])

    def test_reads_never_post_reserve_or_change_native_documents(self):
        types = ('Stock Entry','Stock Ledger Entry','GL Entry','Material Request','Purchase Order')
        before = {dt:frappe.db.count(dt) for dt in types}
        result = log.context(self.order.name)
        log.item_choices(self.order.name,search=self.token)
        self.assertFalse(result['posts_stock'])
        self.assertFalse(result['reserves_stock'])
        self.assertEqual(before,{dt:frappe.db.count(dt) for dt in types})

    def test_binding_sharing_cannot_expand_scope(self):
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc({'doctype':'DocShare','share_doctype':log.DT,'share_name':self.binding.name,
                'user':self.users['other'],'read':1}).insert()

    def test_stock_role_alone_does_not_grant_maintenance_planning(self):
        self.stock_role('other')
        with self.assertRaises(frappe.PermissionError): log.context(self.order.name)
        with self.assertRaises(frappe.PermissionError): log.item_choices(self.order.name)

    def test_logistics_configuration_has_no_export_import_or_share_grants(self):
        self.stock_role()
        for perm in frappe.get_meta(log.DT).permissions:
            self.assertFalse(perm.get('export'))
            self.assertFalse(perm.get('share'))
        self.assertFalse(frappe.get_meta(log.DT).allow_import)
