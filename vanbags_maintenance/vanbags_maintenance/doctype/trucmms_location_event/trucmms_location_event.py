import frappe
from frappe.model.document import Document


class TruCMMSLocationEvent(Document):
    def validate(self):
        if not self.is_new() or frappe.flags.get('trucmms_location_change') != self.location:
            frappe.throw('Location history is server controlled and immutable.', frappe.PermissionError)

    def on_trash(self):
        frappe.throw('Location history cannot be deleted.', frappe.PermissionError)
