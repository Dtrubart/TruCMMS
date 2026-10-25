import frappe
from frappe.model.document import Document
from vanbags_maintenance import teams

class TruCMMSTeamDiscipline(Document):
    def validate(self):
        if not frappe.flags.get('trucmms_team_save'): frappe.throw('Edit disciplines through the maintenance team.',frappe.PermissionError)
    def on_trash(self): frappe.throw('Edit disciplines through the maintenance team.',frappe.PermissionError)
