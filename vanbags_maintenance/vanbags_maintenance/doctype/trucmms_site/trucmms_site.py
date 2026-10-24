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
        if not self.site_code or len(self.site_code)>50 or not re.fullmatch(r"[A-Z0-9._-]+", self.site_code):
            frappe.throw("Site Code must contain 1 to 50 letters, numbers, dots, underscores or hyphens.")
        old=self.get_doc_before_save()
        if old and old.site_code!=self.site_code:
            frappe.throw("Site Code cannot be changed after creation.")
