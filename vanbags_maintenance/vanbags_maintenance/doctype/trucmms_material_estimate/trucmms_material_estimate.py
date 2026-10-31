import frappe
from frappe.model.document import Document
from vanbags_maintenance.resource_planning import validate
class TruCMMSMaterialEstimate(Document):
    def validate(self):validate(self)
    def on_trash(self):frappe.throw('Disable material estimates instead of deleting their history.',frappe.PermissionError)
