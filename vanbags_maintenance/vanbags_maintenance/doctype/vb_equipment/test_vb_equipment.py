from vanbags_maintenance.test_support import org_context, grant_scope
# Copyright (c) 2026, Daniel Trujillo and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class IntegrationTestVBEquipment(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.savepoint("test_vb_equipment")

	def tearDown(self):
		frappe.db.rollback(save_point="test_vb_equipment")
		frappe.set_user("Administrator")

	def test_manager_creates_valid_equipment(self):
		manager = self._create_user("test_equip_manager@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "Production",
		})
		category.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "  eq-001  ",
			"equipment_name": "  Pump A  ",
			"category": category.name,
			"status": "Planned",
		})
		equipment.insert()
		self.assertEqual(equipment.name, "EQ-001")
		self.assertEqual(equipment.equipment_code, "EQ-001")
		self.assertEqual(equipment.equipment_name, "Pump A")
		self.assertEqual(equipment.status, "Planned")

	def test_equipment_code_normalization_and_naming(self):
		manager = self._create_user("test_code_norm@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "Warehouse",
		})
		category.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "wh-01 ",
			"equipment_name": "Conveyor",
			"category": category.name,
		})
		equipment.insert()
		self.assertEqual(equipment.name, "WH-01")

	def test_required_fields_rejected(self):
		manager = self._create_user("test_required@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_name": "Orphan",
			}).insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": "ORPHAN-1",
				"equipment_name": "Orphan",
			}).insert()

	def test_blank_equipment_name_rejected(self):
		manager = self._create_user("test_blank_name@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "TestCat",
		})
		category.insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": "BLANK-1",
				"equipment_name": "   ",
				"category": category.name,
			}).insert()

	def test_code_charset_and_length(self):
		manager = self._create_user("test_code_charset@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "CharsetCat",
		})
		category.insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": "INVALID@CODE",
				"equipment_name": "Bad Code",
				"category": category.name,
			}).insert()

		long_code = "A" * 51
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": long_code,
				"equipment_name": "Long Code",
				"category": category.name,
			}).insert()

		valid_code = "A" * 50
		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": valid_code,
			"equipment_name": "Max Length",
			"category": category.name,
		})
		equipment.insert()
		self.assertEqual(equipment.name, valid_code)

	def test_duplicate_codes_rejected(self):
		manager = self._create_user("test_dup@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "DupCat",
		})
		category.insert()

		base = f"DUP-{id(self)}"
		frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": base,
			"equipment_name": "First",
			"category": category.name,
		}).insert()

		with self.assertRaises(frappe.DuplicateEntryError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": base.lower(),
				"equipment_name": "Duplicate",
				"category": category.name,
			}).insert()

		with self.assertRaises(frappe.DuplicateEntryError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": f" {base} ",
				"equipment_name": "Duplicate",
				"category": category.name,
			}).insert()

		self.assertEqual(frappe.db.count("VB Equipment", {"equipment_code": base}), 1)

	def test_equipment_code_immutable(self):
		manager = self._create_user("test_immutable@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "ImmutableCat",
		})
		category.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "IMM-1",
			"equipment_name": "Immutable",
			"category": category.name,
		})
		equipment.insert()
		equipment.reload()

		equipment.equipment_code = "IMM-2"
		with self.assertRaises(frappe.ValidationError):
			equipment.save()

	def test_enabled_category_location_assignable(self):
		manager = self._create_user("test_enabled_links@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "EnabledCat",
		})
		category.insert()

		location = frappe.get_doc({
			"doctype": "VB Equipment Location", **org_context(),
			"location_name": "EnabledLoc",
		})
		location.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "LINK-1",
			"equipment_name": "Linked",
			"category": category.name,
			"location": location.name,
		})
		equipment.insert()
		self.assertEqual(equipment.category, category.name)
		self.assertEqual(equipment.location, location.name)

	def test_disabled_category_location_rejected(self):
		manager = self._create_user("test_disabled_links@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "DisabledCat",
			"disabled": 1,
		})
		category.insert()

		location = frappe.get_doc({
			"doctype": "VB Equipment Location", **org_context(),
			"location_name": "DisabledLoc",
			"disabled": 1,
		})
		location.insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": "DIS-1",
				"equipment_name": "Disabled Link",
				"category": category.name,
			}).insert()

		enabled_cat = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "EnabledCat",
		})
		enabled_cat.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "DIS-2",
			"equipment_name": "Change Disabled",
			"category": enabled_cat.name,
		})
		equipment.insert()

		equipment.category = category.name
		with self.assertRaises(frappe.ValidationError):
			equipment.save()

	def test_unchanged_disabled_link_allows_unrelated_edits(self):
		manager = self._create_user("test_hist_disabled@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "HistCat",
		})
		category.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "HIST-1",
			"equipment_name": "History",
			"category": category.name,
		})
		equipment.insert()

		category.disabled = 1
		category.save()

		equipment.reload()
		equipment.equipment_name = "History Updated"
		equipment.save()
		self.assertEqual(equipment.equipment_name, "History Updated")

	def test_serial_number_non_unique(self):
		manager = self._create_user("test_serial@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "SerialCat",
		})
		category.insert()

		frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "SER-1",
			"equipment_name": "First",
			"category": category.name,
			"serial_number": "ABC123",
		}).insert()

		frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "SER-2",
			"equipment_name": "Second",
			"category": category.name,
			"serial_number": "ABC123",
		}).insert()

		records = frappe.get_all("VB Equipment", filters={"serial_number": "ABC123"})
		self.assertEqual(len(records), 2)

	def test_default_status_planned(self):
		manager = self._create_user("test_default_status@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "StatusCat",
		})
		category.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "STAT-1",
			"equipment_name": "Status Test",
			"category": category.name,
		})
		equipment.insert()
		self.assertEqual(equipment.status, "Planned")

	def test_all_statuses_save(self):
		manager = self._create_user("test_statuses@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "StatusesCat",
		})
		category.insert()

		statuses = ["Planned", "Active", "Under Maintenance", "Out of Service", "Retired"]
		for status in statuses:
			equipment = frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": f"STAT-{status[:4].upper()}",
				"equipment_name": f"Status {status}",
				"category": category.name,
				"status": status,
			})
			equipment.insert()
			self.assertEqual(equipment.status, status)

	def test_user_cannot_modify_equipment(self):
		manager = self._create_user("test_user_readonly@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "ReadonlyCat",
		})
		category.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "READ-1",
			"equipment_name": "Readonly",
			"category": category.name,
			"status": "Planned",
		})
		equipment.insert()

		user = self._create_user("test_user_ro@example.com", "VB Maintenance User")
		frappe.set_user(user)
		equipment.reload()
		equipment.status = "Active"
		with self.assertRaises(frappe.PermissionError):
			equipment.save()

	def test_date_ordering(self):
		manager = self._create_user("test_dates@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "DateCat",
		})
		category.insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": "DATE-1",
				"equipment_name": "Dates",
				"category": category.name,
				"acquisition_date": "2026-08-10",
				"commissioning_date": "2026-08-09",
			}).insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "DATE-2",
			"equipment_name": "Dates",
			"category": category.name,
			"acquisition_date": "2026-08-10",
			"commissioning_date": "2026-08-10",
		})
		equipment.insert()
		self.assertEqual(equipment.acquisition_date, "2026-08-10")
		self.assertEqual(equipment.commissioning_date, "2026-08-10")

	def test_equal_blank_future_dates_allowed(self):
		manager = self._create_user("test_future_dates@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "FutureCat",
		})
		category.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "FUT-1",
			"equipment_name": "Future",
			"category": category.name,
			"acquisition_date": "2030-01-01",
		})
		equipment.insert()
		self.assertEqual(equipment.acquisition_date, "2030-01-01")
		self.assertIsNone(equipment.commissioning_date)

	def test_user_permission_matrix(self):
		manager = self._create_user("test_user_perms@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "UserPermCat",
		})
		category.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "UPERM-1",
			"equipment_name": "User Perm",
			"category": category.name,
		})
		equipment.insert()

		user = self._create_user("test_user_perm@example.com", "VB Maintenance User")
		frappe.set_user(user)

		doc = frappe.get_doc("VB Equipment", "UPERM-1")
		self.assertIsNotNone(doc)

		doc.equipment_name = "Changed"
		with self.assertRaises(frappe.PermissionError):
			doc.save()

		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": "UPERM-2",
				"equipment_name": "New",
				"category": category.name,
			}).insert()

		with self.assertRaises(frappe.PermissionError):
			doc.delete()

	def test_manager_permission_matrix(self):
		manager = self._create_user("test_manager_perms@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "ManagerPermCat",
		})
		category.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "MPERM-1",
			"equipment_name": "Manager Perm",
			"category": category.name,
		})
		equipment.insert()

		equipment.equipment_name = "Manager Changed"
		equipment.save()
		self.assertEqual(equipment.equipment_name, "Manager Changed")

		with self.assertRaises(frappe.PermissionError):
			equipment.delete()

		self.assertEqual(equipment.equipment_name, "Manager Changed")

	def test_version_tracking(self):
		manager = self._create_user("test_version@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "VersionCat",
		})
		category.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "VER-1",
			"equipment_name": "Version",
			"category": category.name,
		})
		equipment.insert()

		version_count_before = frappe.db.count("Version", {
			"ref_doctype": "VB Equipment",
			"docname": "VER-1",
		})

		equipment.equipment_name = "Version Updated"
		equipment.save(ignore_version=False)

		version_count_after = frappe.db.count("Version", {
			"ref_doctype": "VB Equipment",
			"docname": "VER-1",
		})
		self.assertEqual(version_count_after, version_count_before + 1)

	def test_failed_write_no_persist(self):
		manager = self._create_user("test_failed_write@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "FailedCat",
		})
		category.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "FAIL-1",
			"equipment_name": "Original",
			"category": category.name,
		})
		equipment.insert()

		version_count_before = frappe.db.count("Version", {
			"ref_doctype": "VB Equipment",
			"docname": "FAIL-1",
		})

		equipment.equipment_name = "  "
		with self.assertRaises(frappe.ValidationError):
			equipment.save()

		equipment.reload()
		self.assertEqual(equipment.equipment_name, "Original")

		version_count_after = frappe.db.count("Version", {
			"ref_doctype": "VB Equipment",
			"docname": "FAIL-1",
		})
		self.assertEqual(version_count_after, version_count_before)

	def test_manager_cannot_rename_equipment(self):
		manager = self._create_user("test_no_rename@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "NoRenameCat",
		})
		category.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "RENAME-1",
			"equipment_name": "No Rename",
			"category": category.name,
		})
		equipment.insert()
		self.assertEqual(equipment.name, "RENAME-1")

		with self.assertRaises(frappe.ValidationError):
			equipment.rename("RENAME-2")

		equipment.reload()
		equipment.equipment_code = "RENAME-2"
		with self.assertRaises(frappe.ValidationError):
			equipment.save()

		equipment.reload()
		self.assertEqual(equipment.equipment_code, "RENAME-1")
		self.assertEqual(equipment.name, "RENAME-1")

	def test_user_create_and_write_denied(self):
		manager = self._create_user("test_user_deny@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "UserDenyCat",
		})
		category.insert()

		user = self._create_user("test_user_deny_u@example.com", "VB Maintenance User")
		frappe.set_user(user)

		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": "UDENY-1",
				"equipment_name": "User Deny",
				"category": category.name,
			}).insert()

		frappe.set_user(manager)

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "UDENY-2",
			"equipment_name": "User Deny 2",
			"category": category.name,
		})
		equipment.insert()

		frappe.set_user(user)
		equipment.reload()
		with self.assertRaises(frappe.PermissionError):
			equipment.save()

	def test_manager_can_update_category_location(self):
		manager = self._create_user("test_mgr_update_masters@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "MgrUpdateCat",
		})
		category.insert()

		location = frappe.get_doc({
			"doctype": "VB Equipment Location", **org_context(),
			"location_name": "MgrUpdateLoc",
		})
		location.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "CATALOG-LINK",
			"equipment_name": "Catalog link regression",
			"category": category.name,
			"location": location.name,
		}).insert()

		category.category_name = "MgrUpdateCat Renamed"
		category.save()
		category.reload()
		self.assertEqual(category.category_name, "MgrUpdateCat Renamed")
		self.assertEqual(category.name, "MgrUpdateCat")

		location.location_name = "MgrUpdateLoc Renamed"
		location.save()
		location.reload()
		self.assertEqual(location.location_name, "MgrUpdateLoc Renamed")
		self.assertEqual(location.name, "MgrUpdateLoc")
		equipment.reload()
		self.assertEqual(equipment.category, category.name)
		self.assertEqual(equipment.location, location.name)
		equipment.notes = "Links remain valid after label edits"
		equipment.save()

	def test_catalog_label_uniqueness_after_edit(self):
		for doctype, field in [("VB Equipment Category", "category_name"), ("VB Equipment Location", "location_name")]:
			with self.subTest(doctype=doctype):
				first = frappe.get_doc({"doctype": doctype, **(org_context() if doctype == "VB Equipment Location" else {}), field: "Stable First"}).insert()
				second = frappe.get_doc({"doctype": doctype, **(org_context() if doctype == "VB Equipment Location" else {}), field: "Stable Second"}).insert()
				first.set(field, "Edited Unique Label")
				first.save()
				second.set(field, "Edited Unique Label")
				with self.assertRaises(frappe.UniqueValidationError):
					second.save()
				second.reload()
				self.assertEqual(second.get(field), "Stable Second")
				self.assertEqual(first.name, "Stable First")
				self.assertEqual(second.name, "Stable Second")

	def test_disabled_location_rejected_new_and_changed(self):
		manager = self._create_user("test_disabled_loc@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "DisabledLocCat",
		})
		category.insert()

		disabled_loc = frappe.get_doc({
			"doctype": "VB Equipment Location", **org_context(),
			"location_name": "DisabledLoc",
			"disabled": 1,
		})
		disabled_loc.insert()

		enabled_loc = frappe.get_doc({
			"doctype": "VB Equipment Location", **org_context(),
			"location_name": "EnabledLoc",
		})
		enabled_loc.insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": "DL-1",
				"equipment_name": "Disabled Loc",
				"category": category.name,
				"location": disabled_loc.name,
			}).insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "DL-2",
			"equipment_name": "Change Disabled Loc",
			"category": category.name,
			"location": enabled_loc.name,
		})
		equipment.insert()

		equipment.location = disabled_loc.name
		with self.assertRaises(frappe.ValidationError):
			equipment.save()

	def test_unchanged_disabled_location_allows_unrelated_edits(self):
		manager = self._create_user("test_hist_disabled_loc@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "HistLocCat",
		})
		category.insert()

		location = frappe.get_doc({
			"doctype": "VB Equipment Location", **org_context(),
			"location_name": "HistLoc",
		})
		location.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "HLOC-1",
			"equipment_name": "History Loc",
			"category": category.name,
			"location": location.name,
		})
		equipment.insert()

		location.disabled = 1
		location.save()

		equipment.reload()
		equipment.equipment_name = "History Loc Updated"
		equipment.save()
		self.assertEqual(equipment.equipment_name, "History Loc Updated")

	def test_invalid_status_rejected_and_retired_transition(self):
		manager = self._create_user("test_status_transition@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "StatusTransCat",
		})
		category.insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": "STAT-INV",
				"equipment_name": "Invalid Status",
				"category": category.name,
				"status": "Invalid",
			}).insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "STAT-RET",
			"equipment_name": "Retired",
			"category": category.name,
			"status": "Retired",
		})
		equipment.insert()
		self.assertEqual(equipment.status, "Retired")

		equipment.status = "Active"
		equipment.save()
		equipment.reload()
		self.assertEqual(equipment.status, "Active")

	def test_missing_category_or_location(self):
		manager = self._create_user("test_missing_link@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "MissingLinkCat",
		})
		category.insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": "MISS-1",
				"equipment_name": "Missing Category",
				"category": "__no-category__",
			}).insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({
				"doctype": "VB Equipment", **org_context(),
				"equipment_code": "MISS-2",
				"equipment_name": "Missing Location",
				"category": category.name,
				"location": "__no-location__",
			}).insert()

	def test_serial_number_behavior(self):
		manager = self._create_user("test_serial_behavior@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "SerialBehaveCat",
		})
		category.insert()

		frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "SER-A",
			"equipment_name": "Serial A",
			"category": category.name,
			"serial_number": "  ",
		}).insert()

		frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "SER-B",
			"equipment_name": "Serial B",
			"category": category.name,
			"serial_number": "abc-123",
		}).insert()

		frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "SER-C",
			"equipment_name": "Serial C",
			"category": category.name,
			"serial_number": "  ABC-123  ",
		}).insert()

		frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "SER-D",
			"equipment_name": "Serial D",
			"category": category.name,
			"serial_number": "001-ABC/def",
		}).insert()

		frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "SER-E",
			"equipment_name": "Serial E",
			"category": category.name,
			"serial_number": " 001-ABC/def ",
		}).insert()

		self.assertEqual(frappe.get_value("VB Equipment", "SER-A", "serial_number"), "")
		self.assertEqual(frappe.get_value("VB Equipment", "SER-B", "serial_number"), "abc-123")
		self.assertEqual(frappe.get_value("VB Equipment", "SER-C", "serial_number"), "ABC-123")
		self.assertEqual(frappe.get_value("VB Equipment", "SER-D", "serial_number"), "001-ABC/def")
		self.assertEqual(frappe.get_value("VB Equipment", "SER-E", "serial_number"), "001-ABC/def")

		records = frappe.get_all("VB Equipment", filters={"serial_number": ["in", ["", "abc-123", "ABC-123", "001-ABC/def"]]})
		self.assertGreaterEqual(len(records), 3)

	def test_version_tracking_actor_and_values(self):
		manager = self._create_user("test_version_actor@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "VersionActorCat",
		})
		category.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "VER-ACTOR",
			"equipment_name": "Version Actor",
			"category": category.name,
		})
		equipment.insert()

		equipment.equipment_name = "Version Actor Updated"
		equipment.save(ignore_version=False)

		version = frappe.get_all("Version", {
			"ref_doctype": "VB Equipment",
			"docname": "VER-ACTOR",
		}, order_by="creation desc", limit=1)
		self.assertTrue(len(version) >= 1)
		ver_doc = frappe.get_doc("Version", version[0].name)
		self.assertEqual(ver_doc.owner, manager)
		import json

		version_data = json.loads(ver_doc.data)
		self.assertEqual(version_data.get("added"), [])
		self.assertEqual(version_data.get("removed"), [])
		changed = version_data.get("changed", [])
		self.assertEqual(len(changed), 1)
		self.assertEqual(changed[0][0], "equipment_name")
		self.assertEqual(changed[0][1], "Version Actor")
		self.assertEqual(changed[0][2], "Version Actor Updated")

	def test_atomic_failed_write_preserves_state(self):
		manager = self._create_user("test_atomic_fail@example.com", "VB Maintenance Manager")
		frappe.set_user(manager)

		category = frappe.get_doc({
			"doctype": "VB Equipment Category",
			"category_name": "AtomicFailCat",
		})
		category.insert()

		equipment = frappe.get_doc({
			"doctype": "VB Equipment", **org_context(),
			"equipment_code": "ATOMIC-1",
			"equipment_name": "Atomic",
			"category": category.name,
			"status": "Planned",
			"serial_number": "SR-1",
		})
		equipment.insert()

		version_count_before = frappe.db.count("Version", {
			"ref_doctype": "VB Equipment",
			"docname": "ATOMIC-1",
		})

		equipment.status = "InvalidStatus"
		with self.assertRaises(frappe.ValidationError):
			equipment.save()

		equipment.reload()
		self.assertEqual(equipment.status, "Planned")
		self.assertEqual(equipment.serial_number, "SR-1")

		version_count_after = frappe.db.count("Version", {
			"ref_doctype": "VB Equipment",
			"docname": "ATOMIC-1",
		})
		self.assertEqual(version_count_after, version_count_before)

	def _create_user(self, email, role):
		prev_user = frappe.session.user
		frappe.set_user("Administrator")
		try:
			if frappe.db.exists("User", email):
				user = frappe.get_doc("User", email)
				if not any(r.role == role for r in user.roles):
					user.append("roles", {"role": role})
					user.save(ignore_permissions=True)
			else:
				user = frappe.get_doc({
					"doctype": "User",
					"email": email,
					"first_name": "Test",
					"last_name": "User",
					"roles": [{"role": role}],
				})
				user.insert(ignore_permissions=True)
			grant_scope(user.name)
			return user.name
		finally:
			frappe.set_user(prev_user)

# Organization fixtures are explicit; avoid ERPNext demo-company fixtures.
IGNORE_TEST_RECORD_DEPENDENCIES = ["Company", "TruCMMS Site"]
