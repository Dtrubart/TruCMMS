import frappe
from frappe.model.document import Document
from vanbags_maintenance import teams

class TruCMMSMaintenanceTeam(Document):
    def before_insert(self): self.team_code=(self.team_code or '').strip().upper()
    def validate(self): teams.validate_team(self)
    def on_trash(self): frappe.throw('Disable team instead of deleting history.')
