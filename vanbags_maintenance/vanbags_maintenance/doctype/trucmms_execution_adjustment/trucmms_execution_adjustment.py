import frappe
from frappe.model.document import Document

class TruCMMSExecutionAdjustment(Document):
    def validate(self):
        if not self.is_new() or frappe.flags.get('trucmms_void')!=self.execution:
            frappe.throw('Execution adjustments are immutable server records.',frappe.PermissionError)
    def on_trash(self):
        frappe.throw('Execution adjustments cannot be deleted.',frappe.PermissionError)
