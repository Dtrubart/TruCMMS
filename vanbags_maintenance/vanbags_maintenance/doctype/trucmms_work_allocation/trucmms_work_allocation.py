import frappe
from frappe.model.document import Document
class TruCMMSWorkAllocation(Document):
    def validate(self):
        if not frappe.flags.get('trucmms_allocation_write'):frappe.throw('Use controlled allocation actions.',frappe.PermissionError)
    def on_trash(self):frappe.throw('Allocation history cannot be deleted.',frappe.PermissionError)
