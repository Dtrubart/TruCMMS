"""Immutable provenance, persisted only through its validated parent request."""
import frappe
from frappe.model.document import Document


class TruCMMSMaterialSource(Document):
    def reject_direct_mutation(self):
        # Parent inserts/updates/deletes persist children directly after validating
        # the entire request. Child REST saves must never bypass that validation.
        frappe.throw("Maintenance demand sources can only be maintained through their Material Request.", frappe.PermissionError)

    before_insert = reject_direct_mutation
    before_validate = reject_direct_mutation
    before_update_after_submit = reject_direct_mutation
    before_cancel = reject_direct_mutation
    on_trash = reject_direct_mutation
