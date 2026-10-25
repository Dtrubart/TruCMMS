frappe.ui.form.on("TruCMMS Maintenance Work Order", {
 refresh(frm) {
  if (!frm.is_new()) frm.add_custom_button(__("Work Register"),()=>frappe.set_route("query-report","TruCMMS Work Register",{work_order:frm.doc.name}));
  frm.trucmms_action=(action)=>frappe.prompt({fieldname:"reason",label:__("Reason / Summary"),fieldtype:"Small Text",reqd:1},async values=>{
   await frappe.call({method:"vanbags_maintenance.lifecycle.perform",args:{work_order:frm.doc.name,action,reason:values.reason}});
   await frm.reload_doc();
  },__(action),__("Confirm"));
  const add_action=(action)=>frm.add_custom_button(__(action),()=>frm.trucmms_action(action));
  if (frm.states && !frm.states.trucmms_lifecycle_bound) {
   const original=frm.states.handle_workflow_action.bind(frm.states);
   const actions=["Complete Work","Accept Work","Accept on Behalf","Request Rework","Close Order","Cancel Order"];
   frm.states.handle_workflow_action=(transition)=>actions.includes(transition.action) ? frm.trucmms_action(transition.action) : original(transition);
   frm.states.trucmms_lifecycle_bound=true;
  }
  if (!frm.is_new()) {
   frm.add_custom_button(__("Lifecycle History"),()=>frappe.set_route("List","TruCMMS Work Event",{work_order:frm.doc.name}));
   if (frm.doc.status==="Assigned" && frm.doc.assigned_to===frappe.session.user && frappe.user.has_role("TruCMMS Technician")) add_action("Complete Work");
   if (frm.doc.status==="Technical Completed") {
    if (frappe.user.has_role("TruCMMS Requester") && frm.doc.requester===frappe.session.user) {add_action("Accept Work");add_action("Request Rework");}
    if (frappe.user.has_role("TruCMMS Supervisor") || frappe.user.has_role("System Manager")) {add_action("Accept on Behalf");add_action("Request Rework");}
   }
   if (frappe.user.has_role("TruCMMS Supervisor") || frappe.user.has_role("System Manager")) {
    if (frm.doc.status==="Accepted") add_action("Close Order");
    if (["Draft","Authorized","Assigned","Technical Completed"].includes(frm.doc.status)) add_action("Cancel Order");
   }
  }
  if (!frm.is_new()) {
   frm.add_custom_button(__("Execution History"),()=>frappe.set_route("List","TruCMMS Work Execution",{work_order:frm.doc.name}));
   if (frm.doc.status === "Assigned" && frm.doc.assigned_to === frappe.session.user && frappe.user.has_role("TruCMMS Technician")) {
    frm.add_custom_button(__("Record Execution"),()=>frappe.new_doc("TruCMMS Work Execution",{work_order:frm.doc.name,company:frm.doc.company,site:frm.doc.site}));
   }
  }
  for (const field of ["subject", "scope", "priority", "target_closure"]) frm.set_df_property(field,"read_only",frm.doc.status !== "Draft");
 }
});
