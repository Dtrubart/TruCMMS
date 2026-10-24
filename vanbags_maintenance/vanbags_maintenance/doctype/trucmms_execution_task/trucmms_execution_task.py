import frappe
from frappe.model.document import Document


class TruCMMSExecutionTask(Document):
    def validate(self):
        frappe.throw('Execution tasks are recorded only through a new execution entry.',frappe.PermissionError)

    def on_trash(self):
        frappe.throw('Recorded execution tasks cannot be deleted.',frappe.PermissionError)
