import frappe
from frappe.model.document import Document

class TruCMMSJobPlan(Document):
    def validate(self):
        from vanbags_maintenance.job_plans import validate_plan
        validate_plan(self)
    def on_trash(self):
        frappe.throw('Procedures retain their revision history; disable instead.', frappe.PermissionError)
