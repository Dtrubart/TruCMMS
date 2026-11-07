import frappe
from frappe.model.document import Document
from vanbags_maintenance import operating_units as units


class TruCMMSOperatingUnit(Document):
    def validate(self):
        units.validate_unit(self)

    def after_insert(self):
        units.unit_created(self)

    def on_update(self):
        units.unit_updated(self)

    def on_trash(self):
        frappe.throw('Operating Units retain their identity and history. Deactivate instead of deleting.')

    def before_rename(self, *args, **kwargs):
        frappe.throw('Operating Unit identity is permanent. Edit the display name instead.')
