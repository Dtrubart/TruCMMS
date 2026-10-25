frappe.ui.form.on('TruCMMS Work Allocation',{
 refresh(frm){
  if(!frm.is_new()&&!frm.doc.ended_on&&(frappe.user.has_role('TruCMMS Supervisor')||frappe.user.has_role('System Manager')))frm.add_custom_button(__('End Allocation'),()=>frappe.prompt({fieldname:'reason',label:__('Reason'),fieldtype:'Small Text',reqd:1},async values=>{await frappe.call({method:'vanbags_maintenance.allocations.remove',type:'POST',args:{allocation:frm.doc.name,...values}});await frm.reload_doc();}));
 }
});
