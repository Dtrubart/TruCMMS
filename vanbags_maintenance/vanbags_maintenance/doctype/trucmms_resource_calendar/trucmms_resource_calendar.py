import frappe
from frappe.model.document import Document
from vanbags_maintenance import resource_calendars as calendars
class TruCMMSResourceCalendar(Document):
    def validate(self):calendars.validate_calendar(self)
    def on_trash(self):frappe.throw('Calendar history cannot be deleted; disable configuration where applicable.',frappe.PermissionError)
