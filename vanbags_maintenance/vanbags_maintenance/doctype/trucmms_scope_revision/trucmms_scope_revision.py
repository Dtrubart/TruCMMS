import frappe
from frappe.model.document import Document
class TruCMMSScopeRevision(Document):
    def validate(self):
        if not self.is_new() or not frappe.flags.get('trucmms_scope_write'):frappe.throw('Work scope history is immutable.',frappe.PermissionError)
    def on_trash(self):frappe.throw('Work scope history cannot be deleted.',frappe.PermissionError)
