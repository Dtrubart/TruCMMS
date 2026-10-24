frappe.ui.form.on("TruCMMS Maintenance Work Order", {
 refresh(frm) {
  for (const field of ["subject", "scope", "priority"]) frm.set_df_property(field,"read_only",frm.doc.status !== "Draft");
 }
});
