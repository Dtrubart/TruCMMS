import frappe
from frappe.model.document import Document

class TruCMMSJobPlanRevision(Document):
    def before_insert(self):
        from vanbags_maintenance.job_plans import before_revision_insert
        before_revision_insert(self)
    def validate(self):
        from vanbags_maintenance.job_plans import validate_revision
        validate_revision(self)
    def on_trash(self):
        frappe.throw('Procedure revisions cannot be deleted.', frappe.PermissionError)
