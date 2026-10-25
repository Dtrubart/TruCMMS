import frappe
from frappe.model.document import Document
class TruCMMSDeployment(Document):
    def before_insert(self):
        if not frappe.flags.get('trucmms_deployment_insert'):frappe.throw('Deployment evidence is server authored.',frappe.PermissionError)
    def validate(self):
        if not self.is_new():frappe.throw('Deployment evidence is immutable.',frappe.PermissionError)
    def on_trash(self):frappe.throw('Deployment evidence is immutable.',frappe.PermissionError)
