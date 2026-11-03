import frappe
from frappe.model.document import Document
class TruCMMSWorkTarget(Document):
    def reject(self):frappe.throw('Configure work points through the parent scope service.',frappe.PermissionError)
    before_insert=reject
    before_validate=reject
    before_update_after_submit=reject
    on_trash=reject
