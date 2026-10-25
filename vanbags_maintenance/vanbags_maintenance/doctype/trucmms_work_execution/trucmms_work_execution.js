frappe.ui.form.on("TruCMMS Work Execution", {
 setup(frm) {frm.set_query("work_order",()=>({filters:{status:"Assigned",assigned_to:frappe.session.user}}));},
 async work_order(frm) {
  if (!frm.is_new() || !frm.doc.work_order) return;
  const order=await frappe.db.get_doc("TruCMMS Maintenance Work Order",frm.doc.work_order);
  await frm.set_value({company:order.company,site:order.site});
 },
 async refresh(frm) {
  if (!frm.is_new()) {
   const adjustments=await frappe.db.get_list("TruCMMS Execution Adjustment",{filters:{execution:frm.doc.name},fields:["name"]});
   if (adjustments.length) frm.dashboard.add_indicator(__("Voided — original retained"),"orange");
   else if(frappe.user.has_role("TruCMMS Supervisor") || frappe.user.has_role("System Manager")) {
    const order=await frappe.db.get_doc("TruCMMS Maintenance Work Order",frm.doc.work_order);
    if(order.status==="Assigned")frm.add_custom_button(__("Void Entry"),()=>frappe.prompt({fieldname:"reason",fieldtype:"Small Text",label:__("Void Reason"),reqd:1},async values=>{await frappe.call({method:"vanbags_maintenance.adjustments.void_entry",args:{execution:frm.doc.name,reason:values.reason}});await frm.reload_doc();},__("Void Entry"),__("Confirm")));
   }
  }
  for (const field of ["work_order","actual_start","actual_end","findings","tasks"]) frm.set_df_property(field,"read_only",!frm.is_new());
  if (frm.is_new()) frm.enable_save(); else frm.disable_save();
 }
});
