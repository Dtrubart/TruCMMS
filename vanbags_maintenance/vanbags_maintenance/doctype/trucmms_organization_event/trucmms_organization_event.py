import frappe
from frappe.model.document import Document


class TruCMMSOrganizationEvent(Document):
    def validate(self):
        if not self.is_new() or not frappe.flags.get('trucmms_organization_event'):
            frappe.throw('Organization history is server controlled and immutable.', frappe.PermissionError)

    def on_trash(self):
        frappe.throw('Organization history cannot be deleted.', frappe.PermissionError)

    def before_rename(self, *args, **kwargs):
        frappe.throw('Organization history identity is immutable.')
