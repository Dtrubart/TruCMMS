import frappe
from frappe.model.document import Document
from vanbags_maintenance import capacity
class TruCMMSResourceWindow(Document):
    def validate(self):capacity.validate(self)
    def on_trash(self):frappe.throw('Disable resource windows instead of deleting their history.',frappe.PermissionError)
