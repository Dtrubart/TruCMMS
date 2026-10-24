"""Exercise native import, export and share enforcement for CMMS masters."""
import uuid
import frappe
from frappe.tests import IntegrationTestCase
from frappe.core.doctype.data_import.exporter import Exporter
from frappe.core.doctype.data_export.exporter import DataExporter
from frappe.core.doctype.data_import.data_import import DataImport


class TestFoundationPermissions(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        self.token = "FOUNDATION-" + uuid.uuid4().hex[:10].upper()
        self.users = {}
        for role in ("VB Maintenance User", "VB Maintenance Manager", "System Manager"):
            user = frappe.get_doc({"doctype": "User", "email": self.token.lower()+role.replace(" ", "").lower()+"@example.com", "first_name": "Foundation test", "send_welcome_email": 0, "roles": [{"role": role}]}).insert()
            self.users[role] = user.name
        category = frappe.get_doc({"doctype": "VB Equipment Category", "category_name": self.token}).insert()
        location = frappe.get_doc({"doctype": "VB Equipment Location", "location_name": self.token}).insert()
        equipment = frappe.get_doc({"doctype": "VB Equipment", "equipment_code": self.token, "equipment_name": "Foundation test", "category": category.name, "location": location.name}).insert()
        self.docs = [category, location, equipment]

    def tearDown(self):
        frappe.set_user("Administrator")
        super().tearDown()

    def test_maintenance_roles_cannot_export_through_native_exporters(self):
        for role in ("VB Maintenance User", "VB Maintenance Manager"):
            frappe.set_user(self.users[role])
            for doc in self.docs:
                with self.subTest(role=role, doctype=doc.doctype):
                    self.assertFalse(frappe.has_permission(doc.doctype, "export"))
                    with self.assertRaises(frappe.PermissionError):
                        Exporter(doc.doctype, export_fields={doc.doctype: ["name"]}, export_data=True)
                    with self.assertRaises(frappe.PermissionError):
                        DataExporter(doctype=doc.doctype, with_data=True).build_response()

    def test_system_manager_can_export(self):
        frappe.set_user(self.users["System Manager"])
        for doc in self.docs:
            exporter = Exporter(doc.doctype, export_fields={doc.doctype: ["name"]}, export_data=True, export_filters={"name": doc.name})
            self.assertTrue(exporter.data)
            DataExporter(doctype=doc.doctype, with_data=True, filters={"name": doc.name}).build_response()

    def test_maintenance_roles_cannot_share_or_grant_write(self):
        recipient = self.users["System Manager"]
        for role in ("VB Maintenance User", "VB Maintenance Manager"):
            frappe.set_user(self.users[role])
            for doc in self.docs:
                with self.subTest(role=role, doctype=doc.doctype):
                    with self.assertRaises(frappe.PermissionError):
                        frappe.share.add(doc.doctype, doc.name, user=recipient, write=1, notify=0)
                    self.assertFalse(frappe.db.exists("DocShare", {"share_doctype": doc.doctype, "share_name": doc.name}))

    def test_system_manager_can_share(self):
        frappe.set_user(self.users["System Manager"])
        for doc in self.docs:
            shared = frappe.share.add(doc.doctype, doc.name, user=self.users["VB Maintenance User"], notify=0)
            self.assertEqual(shared.share_name, doc.name)

    def test_bulk_import_is_disabled_for_all_foundation_masters(self):
        for role, user in self.users.items():
            frappe.set_user(user)
            for doc in self.docs:
                with self.subTest(role=role, doctype=doc.doctype):
                    self.assertFalse(frappe.get_meta(doc.doctype).allow_import)
                    if role != "System Manager":
                        self.assertFalse(frappe.has_permission(doc.doctype, "import"))
                    data_import = frappe.get_doc({"doctype": "Data Import", "reference_doctype": doc.doctype, "import_type": "Insert New Records"})
                    with self.assertRaises(frappe.ValidationError):
                        data_import.validate_doctype()
