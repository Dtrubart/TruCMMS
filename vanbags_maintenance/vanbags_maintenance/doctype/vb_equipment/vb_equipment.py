import frappe
import re
from frappe.model.document import Document
from vanbags_maintenance.organization import validate_context


class VBEquipment(Document):
	def before_insert(self):
		self.equipment_code = (self.equipment_code or "").strip().upper()
		if not self.equipment_code:
			frappe.throw(
				"Equipment Code is required.",
				title="Missing Equipment Code",
			)

	def before_validate(self):
		self.equipment_code = (self.equipment_code or "").strip().upper()
		self.equipment_name = (self.equipment_name or "").strip()
		self.manufacturer = (self.manufacturer or "").strip()
		self.model = (self.model or "").strip()
		self.serial_number = (self.serial_number or "").strip()

	def validate(self):
		from vanbags_maintenance.assets import validate_equipment
		validate_equipment(self)
		validate_context(self)
		if not self.equipment_code:
			frappe.throw(
				"Equipment Code is required.",
				title="Missing Equipment Code",
			)

		if len(self.equipment_code) > 50:
			frappe.throw(
				"Equipment Code cannot be longer than 50 characters.",
				title="Invalid Equipment Code",
			)

		if not re.match(r"^[A-Z0-9._-]+$", self.equipment_code):
			frappe.throw(
				"Equipment Code may contain only letters, numbers, dots, underscores, and hyphens.",
				title="Invalid Equipment Code",
			)

		if not self.equipment_name:
			frappe.throw(
				"Equipment Name is required.",
				title="Missing Equipment Name",
			)

		if not self.category:
			frappe.throw(
				"Category is required.",
				title="Missing Category",
			)

		if self.status not in {
			"Planned",
			"Active",
			"Under Maintenance",
			"Out of Service",
			"Retired",
		}:
			frappe.throw(
				f"Invalid status: {self.status}",
				title="Invalid Status",
			)

		if self.acquisition_date and self.commissioning_date:
			if self.commissioning_date < self.acquisition_date:
				frappe.throw(
					"Commissioning Date cannot be before Acquisition Date.",
					title="Invalid Date Range",
				)

		old = self.get_doc_before_save()
		if old and old.equipment_code != self.equipment_code:
			frappe.throw(
				"Equipment Code cannot be changed after creation.",
				title="Immutable Field",
			)

		if self.category:
			category_changed = not old or old.category != self.category
			if category_changed:
				if frappe.db.get_value("VB Equipment Category", self.category, "disabled"):
					frappe.throw(
						f"Cannot assign a disabled Category: {self.category}",
						title="Invalid Category",
					)

		if self.location:
			location_changed = not old or old.location != self.location
			if location_changed:
				if frappe.db.get_value("VB Equipment Location", self.location, "disabled"):
					frappe.throw(
						f"Cannot assign a disabled Location: {self.location}",
						title="Invalid Location",
					)

	def after_insert(self):
		from vanbags_maintenance.assets import initialize_placement
		initialize_placement(self)
	def on_trash(self):
		if frappe.db.exists('TruCMMS Equipment Installation',{'equipment':self.name}):frappe.throw('Equipment with placement history must be retained.',frappe.PermissionError)
