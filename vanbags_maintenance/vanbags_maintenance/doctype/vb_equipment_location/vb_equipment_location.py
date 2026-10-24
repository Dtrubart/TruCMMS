import frappe
from frappe.model.document import Document


class VBEquipmentLocation(Document):
	def before_insert(self):
		self.location_name = (self.location_name or "").strip()
		if not self.location_name:
			frappe.throw(
				"Location Name is required.",
				title="Missing Location Name",
			)

	def before_validate(self):
		self.location_name = (self.location_name or "").strip()
		if not self.location_name:
			frappe.throw(
				"Location Name is required.",
				title="Missing Location Name",
			)
