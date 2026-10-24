# Copyright (c) 2026, Daniel Trujillo and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestVBEquipmentLocation(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_test_users()

	@classmethod
	def _ensure_test_users(cls):
		users = [
			("test_location_manager@example.com", "VB Maintenance Manager"),
			("test_location_user@example.com", "VB Maintenance User"),
			("test_location_manager_del@example.com", "VB Maintenance Manager"),
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
		frappe.db.savepoint("test_vb_location")

	def tearDown(self):
		frappe.db.rollback(save_point="test_vb_location")
		frappe.set_user("Administrator")

	def test_location_name_trimmed_and_unique(self):
		name = self._unique("Trimmed")
		location = frappe.get_doc({
			"doctype": "VB Equipment Location",
			"location_name": f"  {name}  ",
		})
		location.insert()
		self.assertEqual(location.name, name)
		self.assertEqual(frappe.get_value("VB Equipment Location", name, "location_name"), name)

		with self.assertRaises(frappe.DuplicateEntryError):
			frappe.get_doc({
				"doctype": "VB Equipment Location",
				"location_name": name,
			}).insert()

	def test_location_default_disabled(self):
		name = self._unique("Default")
		location = frappe.get_doc({
			"doctype": "VB Equipment Location",
			"location_name": name,
		})
		location.insert()
		self.assertEqual(location.disabled, 0)

	def test_manager_can_create_location(self):
		manager = self._get_test_user("test_location_manager@example.com")
		frappe.set_user(manager)
		name = self._unique("MgrCreate")
		location = frappe.get_doc({
			"doctype": "VB Equipment Location",
			"location_name": name,
		})
		location.insert()
		self.assertIsNotNone(location.name)

	def test_user_can_read_disabled_location(self):
		name = self._unique("Disabled")
		location = frappe.get_doc({
			"doctype": "VB Equipment Location",
			"location_name": name,
			"disabled": 1,
		})
		location.insert()

		user = self._get_test_user("test_location_user@example.com")
		frappe.set_user(user)
		self.assertIsNotNone(frappe.get_doc("VB Equipment Location", name))

	def test_manager_cannot_delete_location(self):
		name = self._unique("NoDel")
		location = frappe.get_doc({
			"doctype": "VB Equipment Location",
			"location_name": name,
		})
		location.insert()

		manager = self._get_test_user("test_location_manager_del@example.com")
		frappe.set_user(manager)
		with self.assertRaises(frappe.PermissionError):
			location.delete()

	def test_blank_location_name_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "VB Equipment Location",
				"location_name": "   ",
			}).insert()

	def _get_test_user(self, email):
		return email

	def _unique(self, suffix):
		return f"TestLoc_{suffix}_{id(self)}"
