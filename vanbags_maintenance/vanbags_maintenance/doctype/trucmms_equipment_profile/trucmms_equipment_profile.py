import frappe
from frappe.model.document import Document
class TruCMMSEquipmentProfile(Document):
    def validate(self):
        from vanbags_maintenance.assets import validate_profile
        validate_profile(self)
    def on_trash(self):frappe.throw('Versioned configuration cannot be deleted; disable it instead.',frappe.PermissionError)
