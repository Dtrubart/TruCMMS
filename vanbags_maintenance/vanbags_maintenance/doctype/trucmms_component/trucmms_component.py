import frappe
from frappe.model.document import Document

class TruCMMSComponent(Document):
    def before_insert(self):
        from vanbags_maintenance.r2_records import before_insert
        before_insert(self)
    def validate(self):
        from vanbags_maintenance.r2_records import validate_doc
        validate_doc(self)
    def after_insert(self):
        from vanbags_maintenance.r2_records import after_insert
        after_insert(self)
    def on_trash(self):
        frappe.throw('R2 history cannot be deleted; use controlled retirement/cancellation.', frappe.PermissionError)
