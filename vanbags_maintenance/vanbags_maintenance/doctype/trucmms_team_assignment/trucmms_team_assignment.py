import frappe
from frappe.model.document import Document
from vanbags_maintenance import teams

class TruCMMSTeamAssignment(Document):
    def before_insert(self):
        if not frappe.flags.get('trucmms_assignment_insert'): frappe.throw('Use controlled work order assignment.',frappe.PermissionError)
    def validate(self):
        if not self.is_new(): frappe.throw('Assignment history is immutable.',frappe.PermissionError)
    def on_trash(self): frappe.throw('Assignment history is immutable.',frappe.PermissionError)
