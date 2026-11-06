import frappe
from frappe.model.document import Document
from vanbags_maintenance.organization import validate_context


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

	def validate(self):
		from vanbags_maintenance import location_hierarchy
		validate_context(self)
		location_hierarchy.validate(self)

	def after_insert(self):
		from vanbags_maintenance import location_hierarchy
		location_hierarchy.after_insert(self)

	def on_update(self):
		from vanbags_maintenance import location_hierarchy
		location_hierarchy.on_update(self)

	def on_trash(self):
		from vanbags_maintenance import location_hierarchy
		location_hierarchy.prevent_delete(self)
