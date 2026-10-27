frappe.listview_settings['TruCMMS Maintenance Work Order']={
 onload(listview){
  listview.page.add_inner_button(__("Work Views"),()=>frappe.set_route("trucmms-work"));
  if(!['TruCMMS Supervisor','TruCMMS Dispatcher','System Manager'].some(role=>frappe.user.has_role(role)))return;
  listview.page.add_inner_button(__('New Direct Order'),()=>{const request_key=crypto.randomUUID();return frappe.prompt([
   {fieldname:'company',label:__('Company'),fieldtype:'Link',options:'Company',reqd:1},
   {fieldname:'site',label:__('Operating Site'),fieldtype:'Link',options:'TruCMMS Site',reqd:1},
   {fieldname:'equipment',label:__('Equipment'),fieldtype:'Link',options:'VB Equipment'},
   {fieldname:'functional_location',label:__('Functional Location'),fieldtype:'Link',options:'VB Equipment Location'},
   {fieldname:'subject',label:__('Subject'),fieldtype:'Data',reqd:1},
   {fieldname:'scope',label:__('Work Scope'),fieldtype:'Small Text',reqd:1},
   {fieldname:'priority',label:__('Priority'),fieldtype:'Select',options:'Low\nMedium\nHigh\nCritical',default:'Medium',reqd:1},
   {fieldname:'acceptance_user',label:__('Acceptance User'),fieldtype:'Link',options:'User'},
   {fieldname:'reason',label:__('Direct Work Reason'),fieldtype:'Small Text',reqd:1}
  ],async values=>{const {message}=await frappe.call({method:'vanbags_maintenance.work_contract.create_direct',type:'POST',args:{...values,key:request_key}});frappe.set_route('Form','TruCMMS Maintenance Work Order',message.name);},__('New Direct Order'));});
 }
};
