import frappe
from frappe.model.document import Document
from vanbags_maintenance import work_scope
class TruCMMSMeasurementPoint(Document):
    def validate(self):work_scope.validate_point(self)
    def on_trash(self):frappe.throw('Disable measurement points instead of deleting their history.',frappe.PermissionError)
