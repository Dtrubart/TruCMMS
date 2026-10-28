frappe.ui.form.on("TruCMMS Work Execution", {
 setup(frm) {frm.set_query("work_order",()=>({query:"vanbags_maintenance.work_views.execution_order_query"}));},
 async work_order(frm) {
  if (!frm.is_new() || !frm.doc.work_order) return;
  const order=await frappe.db.get_doc("TruCMMS Maintenance Work Order",frm.doc.work_order);
  await frm.set_value({company:order.company,site:order.site});
 },
 async refresh(frm) {
  let voided=false;
  if (!frm.is_new()) {
   const adjustments=await frappe.db.get_list("TruCMMS Execution Adjustment",{filters:{execution:frm.doc.name},fields:["name"]});
   voided=adjustments.length>0;
   if (adjustments.length) frm.dashboard.add_indicator(__("Voided — original retained"),"orange");
   else if(frappe.user.has_role("TruCMMS Supervisor") || frappe.user.has_role("System Manager")) {
    const order=await frappe.db.get_doc("TruCMMS Maintenance Work Order",frm.doc.work_order);
    if(order.status==="Assigned")frm.add_custom_button(__("Void Entry"),()=>frappe.prompt({fieldname:"reason",fieldtype:"Small Text",label:__("Void Reason"),reqd:1},async values=>{await frappe.call({method:"vanbags_maintenance.adjustments.void_entry",args:{execution:frm.doc.name,reason:values.reason}});await frm.reload_doc();},__("Void Entry"),__("Confirm")));
   }
  }
  frm.disable_save(frm.is_new());
  if(!frm.is_new() && frm.doc.technician===frappe.session.user && frappe.user.has_role("TruCMMS Technician")) {
   const order=await frappe.db.get_doc("TruCMMS Maintenance Work Order",frm.doc.work_order);
   let current=order.assigned_to===frappe.session.user;
   if(order.lifecycle_policy==="C1") {const result=await frappe.call({method:"vanbags_maintenance.allocations.mine",args:{work_order:order.name}});current=!!result.message && result.message.name===frm.doc.allocation;}
   if(!voided && order.status==="Assigned" && current && order.execution_cycle===frm.doc.execution_cycle)frm.page.set_primary_action(__("Add Private Evidence"),()=>frm.attachments.new_attachment());
  }
  for (const field of ["work_order","actual_start","actual_end","findings","tasks"]) frm.set_df_property(field,"read_only",!frm.is_new());
  if (frm.is_new()) {
   frm.trucmms_submission_key ||= crypto.randomUUID();
   frm.set_intro(__("Wait for confirmation before leaving this form. If the connection is interrupted, keep it open and retry."),"blue");
   frm.page.set_primary_action(__("Submit Execution"),async()=>{
    if(frm.trucmms_submitting)return;
    frm.trucmms_submitting=true;
    try {
     const payload={work_order:frm.doc.work_order,actual_start:frm.doc.actual_start,actual_end:frm.doc.actual_end,findings:frm.doc.findings,tasks:(frm.doc.tasks||[]).filter(r=>r.task || r.findings || (r.result && r.result!=="Completed")).map(r=>({task:r.task,result:r.result,findings:r.findings,...(r.procedure_task_code?{procedure_task_code:r.procedure_task_code}:{})}))};
     if((frm.doc.pm_measurements||[]).length)payload.pm_measurements=frm.doc.pm_measurements.map(r=>({metric_key:r.metric_key,value:r.value,...(r.meter_reading?{meter_reading:r.meter_reading}:{})}));
     const result=await frappe.call({method:"vanbags_maintenance.submission.submit",type:"POST",args:{payload:JSON.stringify(payload),key:frm.trucmms_submission_key},freeze:true});
     frappe.model.sync(result.message);frm.doc.__unsaved=0;frappe.set_route("Form","TruCMMS Work Execution",result.message.name);
    } finally {frm.trucmms_submitting=false;}
   });
  }
 }
});
