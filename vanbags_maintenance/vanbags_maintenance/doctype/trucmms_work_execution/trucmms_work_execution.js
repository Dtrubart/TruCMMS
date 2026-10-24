frappe.ui.form.on("TruCMMS Work Execution", {
 setup(frm) {frm.set_query("work_order",()=>({filters:{status:"Assigned",assigned_to:frappe.session.user}}));},
 async work_order(frm) {
  if (!frm.is_new() || !frm.doc.work_order) return;
  const order=await frappe.db.get_doc("TruCMMS Maintenance Work Order",frm.doc.work_order);
  await frm.set_value({company:order.company,site:order.site});
 },
 refresh(frm) {
  for (const field of ["work_order","actual_start","actual_end","findings","tasks"]) frm.set_df_property(field,"read_only",!frm.is_new());
  if (frm.is_new()) frm.enable_save(); else frm.disable_save();
 }
});
