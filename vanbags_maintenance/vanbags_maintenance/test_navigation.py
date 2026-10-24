import frappe
from frappe.tests import IntegrationTestCase


class TestTruCMMSNavigation(IntegrationTestCase):
	def test_installed_native_navigation_targets(self):
		workspace = frappe.get_doc("Workspace", "TruCMMS")
		self.assertEqual(workspace.module, "Vanbags Maintenance")
		self.assertEqual(workspace.app, "vanbags_maintenance")
		self.assertTrue(workspace.public)
		targets = {row.link_to for row in workspace.links if row.type == "Link"}
		self.assertEqual(targets, {"VB Equipment", "VB Equipment Category", "VB Equipment Location", "TruCMMS Site", "TruCMMS Maintenance Request", "TruCMMS Maintenance Work Order", "TruCMMS Work Execution"})
		for target in targets:
			self.assertTrue(frappe.db.exists("DocType", target))

	def test_desktop_entry_uses_native_sidebar(self):
		icon = frappe.get_doc("Desktop Icon", "TruCMMS")
		self.assertTrue(icon.standard)
		self.assertFalse(icon.hidden)
		self.assertEqual(icon.icon_type, "Link")
		self.assertEqual(icon.link_type, "Workspace Sidebar")
		self.assertEqual(icon.link_to, "TruCMMS")
		self.assertEqual({row.role for row in icon.roles}, {"VB Maintenance User", "VB Maintenance Manager", "System Manager", "TruCMMS Requester", "TruCMMS Dispatcher", "TruCMMS Supervisor", "TruCMMS Technician"})
		sidebar = frappe.get_doc("Workspace Sidebar", icon.link_to)
		self.assertTrue(sidebar.standard)
		self.assertEqual(sidebar.items[0].link_to, "TruCMMS")
		self.assertEqual(sidebar.items[0].link_type, "Workspace")
