import frappe
from frappe.model.document import Document


class VBEquipmentCategory(Document):
	def before_insert(self):
		self.category_name = (self.category_name or "").strip()
		if not self.category_name:
			frappe.throw(
				"Category Name is required.",
				title="Missing Category Name",
			)

	def before_validate(self):
		self.category_name = (self.category_name or "").strip()
		if not self.category_name:
			frappe.throw(
				"Category Name is required.",
				title="Missing Category Name",
			)
