import frappe
from frappe.model.document import Document
from vanbags_maintenance import teams

class TruCMMSTeamSiteAuthorization(Document):
    def validate(self): teams.validate_interval(self)
    def on_trash(self): frappe.throw('Revoke authorization instead of deleting history.')
