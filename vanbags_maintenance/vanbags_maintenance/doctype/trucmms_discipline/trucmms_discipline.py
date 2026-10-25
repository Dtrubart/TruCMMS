import frappe
from frappe.model.document import Document
from vanbags_maintenance import teams

class TruCMMSDiscipline(Document):
    def before_insert(self): self.discipline_code=(self.discipline_code or '').strip().upper()
    def validate(self): teams.validate_discipline(self)
    def on_trash(self): frappe.throw('Disable discipline instead of deleting history.')
