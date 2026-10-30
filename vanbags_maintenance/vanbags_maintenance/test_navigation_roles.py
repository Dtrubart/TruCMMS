import frappe
from unittest.mock import patch
from vanbags_maintenance import navigation as nav
from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase
from vanbags_maintenance.test_support import SITE_B

class TestTaskNavigation(WorkOrderCase):
    def labels(self,role):
        frappe.set_user(self.users[role]);return [g['label'] for g in nav.groups()]
    def test_requester_has_only_operational_primary_navigation(self):self.assertEqual(self.labels('requester'),['Operación'])
    def test_technician_has_work_and_assets_without_administration(self):self.assertEqual(self.labels('tech'),['Operación','Activos','Planes y rutinas'])
    def test_supervisor_sees_resources_and_analysis(self):
        labels=self.labels('supervisor');self.assertIn('Recursos y servicios',labels);self.assertIn('Análisis',labels);self.assertNotIn('Configuración',labels)
    def test_implemented_logistics_group_and_contextual_entities(self):
        frappe.set_user('Administrator');groups=nav.groups();self.assertIn('Planes y rutinas',[g['label'] for g in groups]);self.assertIn('Repuestos y costos',[g['label'] for g in groups]);targets={e['target'] for g in groups for e in g['links']};self.assertIn('TruCMMS Site Warehouse',targets);self.assertIn('TruCMMS Job Plan',targets);self.assertFalse(targets&nav.CONTEXTUAL)
    def test_home_counts_are_permission_scoped(self):
        order=self.assign();frappe.set_user(self.users['other']);data=nav.home();counts={c['label']:c['count'] for c in data['cards']};self.assertEqual(counts.get('Órdenes abiertas'),0)
        frappe.set_user(self.users['tech']);data=nav.home();self.assertTrue(any(a['label']=='Mi trabajo' for a in data['actions']));self.assertFalse(any(a['label']=='Reportar una falla' for a in data['actions']))
    def test_home_rejects_unauthorized_site(self):
        frappe.set_user(self.users['tech'])
        with self.assertRaises(frappe.PermissionError):nav.home(site=SITE_B)
    def test_guest_cannot_use_home_api(self):
        frappe.set_user('Guest')
        with self.assertRaises(frappe.PermissionError):nav.home()
    def test_boot_modifies_only_the_trucmms_sidebar(self):
        frappe.set_user(self.users['tech']);boot={'workspace_sidebar_item':{'trucmms':{'items':[{'type':'Link','label':'Preserved custom link','link_type':'DocType','link_to':'Company'}]},'accounting':{'items':[{'label':'Leave unchanged'}]}}};nav.extend_bootinfo(boot);self.assertEqual(boot['workspace_sidebar_item']['accounting']['items'],[{'label':'Leave unchanged'}]);items=boot['workspace_sidebar_item']['trucmms']['items'];self.assertEqual(items[0]['link_to'],'trucmms-start');self.assertTrue(any(i.get('link_to')=='Company' for i in items));self.assertFalse(any(i.get('label')=='Configuración' for i in items))
    @patch('frappe.desk.doctype.workspace_sidebar.workspace_sidebar.WorkspaceSidebar.export_sidebar')
    def test_setup_is_idempotent_and_preserves_custom_navigation(self,_export):
        frappe.set_user('Administrator');doc=frappe.get_doc('Workspace Sidebar','TruCMMS');doc.append('items',{'type':'Link','label':'Custom company','link_type':'DocType','link_to':'Company'});nav.save_navigation(doc);nav.setup();nav.setup();doc.reload();self.assertEqual(sum(r.link_to=='trucmms-start' for r in doc.items),1);self.assertEqual(sum(r.link_to=='Company' for r in doc.items),2) # Config entry and preserved custom entry.
        workspace=frappe.get_doc('Workspace','TruCMMS');self.assertEqual((workspace.type,workspace.link_type,workspace.link_to),('Link','Page','trucmms-start'))
