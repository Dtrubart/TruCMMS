import frappe
from frappe.model.document import Document
class TruCMMSWorkCycle(Document):
    def validate(self):
        if not self.is_new() or not frappe.flags.get('trucmms_cycle_insert'):frappe.throw('Cycle snapshots are immutable server-generated records.',frappe.PermissionError)
    def on_trash(self):frappe.throw('Cycle history cannot be deleted.',frappe.PermissionError)
