import frappe
from frappe.model.document import Document


class TruCMMSWorkEvent(Document):
    def validate(self):
        ctx=frappe.flags.get('trucmms_lifecycle')
        if not self.is_new() or not ctx or ctx['name']!=self.work_order or ctx['action']!=self.action:
            frappe.throw('Lifecycle events are immutable server-generated records.',frappe.PermissionError)

    def on_trash(self):
        frappe.throw('Lifecycle events cannot be deleted.',frappe.PermissionError)
