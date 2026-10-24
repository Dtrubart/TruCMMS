from vanbags_maintenance.test_support import org_context, grant_scope
# Copyright (c) 2026, Daniel Trujillo and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestVBEquipmentCategory(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_test_users()

	@classmethod
	def _ensure_test_users(cls):
		users = [
			("test_category_manager@example.com", "VB Maintenance Manager"),
			("test_category_user@example.com", "VB Maintenance User"),
			("test_category_manager_del@example.com", "VB Maintenance Manager"),
		]
		for email, role in users:
			if not frappe.db.exists("User", email):
				user = frappe.get_doc({
					"doctype": "User",
					"email": email,
					"first_name": "Test",
					"last_name": "User",
					"roles": [{"role": role}],
				})
				user.insert(ignore_permissions=True)
		frappe.db.commit()

	def setUp(self):
		super().setUp()
		frappe.db.savepoint("test_vb_category")

	def tearDown(self):
		frappe.db.rollback(save_point="test_vb_category")
		frappe.set_user("Administrator")

	def test_category_name_trimmed_and_unique(self):
		name = self._unique("Trimmed")
		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": f"  {name}  ",
		})
		category.insert()
		self.assertEqual(category.name, name)
		self.assertEqual(frappe.get_value("VB Equipment Category", name, "category_name"), name)

		with self.assertRaises(frappe.DuplicateEntryError):
			frappe.get_doc({
				"doctype": "VB Equipment Category",
				"category_name": name,
			}).insert()

	def test_category_default_disabled(self):
		name = self._unique("Default")
		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": name,
		})
		category.insert()
		self.assertEqual(category.disabled, 0)

	def test_manager_can_create_category(self):
		manager = self._get_test_user("test_category_manager@example.com")
		frappe.set_user(manager)
		name = self._unique("MgrCreate")
		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": name,
		})
		category.insert()
		self.assertIsNotNone(category.name)

	def test_user_can_read_disabled_category(self):
		name = self._unique("Disabled")
		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": name,
			"disabled": 1,
		})
		category.insert()

		user = self._get_test_user("test_category_user@example.com")
		frappe.set_user(user)
		self.assertIsNotNone(frappe.get_doc("VB Equipment Category", name))

	def test_manager_cannot_delete_category(self):
		name = self._unique("NoDel")
		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": name,
		})
		category.insert()

		manager = self._get_test_user("test_category_manager_del@example.com")
		frappe.set_user(manager)
		with self.assertRaises(frappe.PermissionError):
			category.delete()

	def test_blank_category_name_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "VB Equipment Category",
				"category_name": "   ",
			}).insert()

	def _get_test_user(self, email):
		return email

	def _unique(self, suffix):
		return f"TestCat_{suffix}_{id(self)}"
