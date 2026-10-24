frappe.ui.form.on("TruCMMS Maintenance Work Order", {
 refresh(frm) {
  if (!frm.is_new()) {
   frm.add_custom_button(__("Execution History"),()=>frappe.set_route("List","TruCMMS Work Execution",{work_order:frm.doc.name}));
   if (frm.doc.status === "Assigned" && frm.doc.assigned_to === frappe.session.user && frappe.user.has_role("TruCMMS Technician")) {
    frm.add_custom_button(__("Record Execution"),()=>frappe.new_doc("TruCMMS Work Execution",{work_order:frm.doc.name,company:frm.doc.company,site:frm.doc.site}));
   }
  }
  for (const field of ["subject", "scope", "priority"]) frm.set_df_property(field,"read_only",frm.doc.status !== "Draft");
 }
});
