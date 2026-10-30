import frappe
from frappe.model.document import Document

class TruCMMSSiteWarehouse(Document):
    def before_insert(self):
        from vanbags_maintenance.logistics import validate_binding
        validate_binding(self)

    def validate(self):
        from vanbags_maintenance.logistics import validate_binding
        validate_binding(self)

    def on_trash(self):
        frappe.throw('Disable warehouse authorization instead of deleting its history.', frappe.PermissionError)
