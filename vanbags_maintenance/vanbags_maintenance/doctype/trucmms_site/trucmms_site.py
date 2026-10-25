import re
import frappe
from frappe.model.document import Document
from vanbags_maintenance.organization import validate_context

class TruCMMSSite(Document):
    def before_insert(self):
        self.before_validate()
    def before_validate(self):
        self.site_code = (self.site_code or "").strip().upper()
        self.site_name = (self.site_name or "").strip()
    def validate(self):
        validate_context(self)
        old=self.get_doc_before_save()
        if old and old.time_zone and not self.time_zone:frappe.throw("Operating timezone cannot be cleared.")
        from vanbags_maintenance.configuration import validate_zone
        self.time_zone=validate_zone(self.time_zone or frappe.db.get_single_value("System Settings","time_zone") or "UTC")
        if not self.site_code or len(self.site_code)>50 or not re.fullmatch(r"[A-Z0-9._-]+", self.site_code):
            frappe.throw("Site Code must contain 1 to 50 letters, numbers, dots, underscores or hyphens.")
        if self.get('acceptance_policy') not in ('By Origin','Required','Not Required'):frappe.throw('Choose a supported site acceptance policy.')
        old=self.get_doc_before_save()
        if old and old.site_code!=self.site_code:
            frappe.throw("Site Code cannot be changed after creation.")
