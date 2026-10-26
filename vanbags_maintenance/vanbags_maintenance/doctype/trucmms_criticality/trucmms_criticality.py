import frappe
from frappe.model.document import Document
class TruCMMSCriticality(Document):
    def validate(self):
        from vanbags_maintenance.assets import validate_criticality
        validate_criticality(self)
    def on_trash(self):frappe.throw('Versioned configuration cannot be deleted; disable it instead.',frappe.PermissionError)
