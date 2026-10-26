import frappe
from frappe.tests import IntegrationTestCase


class TestTruCMMSNavigation(IntegrationTestCase):
	def test_installed_native_navigation_targets(self):
		workspace = frappe.get_doc("Workspace", "TruCMMS")
		self.assertEqual(workspace.module, "Vanbags Maintenance")
		self.assertEqual(workspace.app, "vanbags_maintenance")
		self.assertTrue(workspace.public)
		targets = {row.link_to for row in workspace.links if row.type == "Link" and row.link_type == "DocType"}
		self.assertEqual(targets, {"VB Equipment", "VB Equipment Category", "VB Equipment Location", "TruCMMS Site", "TruCMMS Maintenance Request", "TruCMMS Maintenance Work Order", "TruCMMS Work Execution", "TruCMMS Maintenance Team", "TruCMMS Discipline", "TruCMMS Team Membership", "TruCMMS Team Site Authorization", "TruCMMS Equipment Profile", "TruCMMS Criticality"})
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

	def test_d_navigation_upgrade_adds_links_without_resetting_custom_entries(self):
		from vanbags_maintenance.assets import setup_navigation
		frappe.db.savepoint('navigation_d_case');original=frappe.session.user;frappe.set_user('Administrator')
		try:
			for dt,table in [('Workspace','links'),('Workspace Sidebar','items')]:
				doc=frappe.get_doc(dt,'TruCMMS')
				doc.set(table,[r for r in doc.get(table) if r.link_to not in ('TruCMMS Equipment Profile','TruCMMS Criticality','TruCMMS Installation Register')])
				doc.append(table,{'type':'Link','label':'Preserved custom company link','link_type':'DocType','link_to':'Company'});doc.save(ignore_permissions=True)
			setup_navigation();setup_navigation()
			for dt,table in [('Workspace','links'),('Workspace Sidebar','items')]:
				links=frappe.get_doc(dt,'TruCMMS').get(table);names=[r.link_to for r in links]
				for name in ('Company','TruCMMS Equipment Profile','TruCMMS Criticality','TruCMMS Installation Register'):self.assertEqual(names.count(name),1)
		finally:
			frappe.db.rollback(save_point='navigation_d_case');frappe.set_user(original)
