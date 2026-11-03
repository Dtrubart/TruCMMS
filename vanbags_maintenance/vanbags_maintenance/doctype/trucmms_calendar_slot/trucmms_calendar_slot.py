import frappe
from frappe.model.document import Document
from vanbags_maintenance import resource_calendars as calendars
class TruCMMSCalendarSlot(Document):
    def before_validate(self):frappe.throw('Edit weekly slots through the parent calendar.',frappe.PermissionError)
    before_insert=before_validate
    on_trash=before_validate
