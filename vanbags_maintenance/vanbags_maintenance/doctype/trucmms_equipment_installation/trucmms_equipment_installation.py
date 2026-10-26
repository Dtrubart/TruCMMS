import frappe
from frappe.model.document import Document
class TruCMMSEquipmentInstallation(Document):
    def validate(self):
        if not frappe.flags.get('trucmms_asset_write'):frappe.throw('Use controlled equipment placement actions.',frappe.PermissionError)
    def on_trash(self):frappe.throw('Installation history is immutable.',frappe.PermissionError)
