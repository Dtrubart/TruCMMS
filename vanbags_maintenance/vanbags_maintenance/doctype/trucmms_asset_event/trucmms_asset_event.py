import frappe
from frappe.model.document import Document
class TruCMMSAssetEvent(Document):
    def validate(self):
        if not self.is_new() or not frappe.flags.get('trucmms_asset_write'):frappe.throw('Asset events are server-authored and immutable.',frappe.PermissionError)
    def on_trash(self):frappe.throw('Asset history cannot be deleted.',frappe.PermissionError)
