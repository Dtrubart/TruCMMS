import frappe
from frappe.model.document import Document

class TruCMMSMaterialAcknowledgment(Document):
    def validate(self):
        if not self.is_new() or not frappe.flags.get('trucmms_material_request'):
            frappe.throw('Collection acknowledgments are immutable service records.',frappe.PermissionError)
    def on_trash(self):
        frappe.throw('Collection acknowledgments cannot be deleted.',frappe.PermissionError)
