frappe.ui.form.on("TruCMMS Maintenance Work Order", {
 async refresh(frm) {
  const managed=frm.doc.lifecycle_policy==="C1";
  const supervisor=frappe.user.has_role("TruCMMS Supervisor")||frappe.user.has_role("System Manager");
  const technician=frappe.user.has_role("TruCMMS Technician");
  const primary=frm.doc.assigned_to===frappe.session.user;
  const acceptor=(frm.doc.acceptance_user||frm.doc.requester)===frappe.session.user && frappe.user.has_role("TruCMMS Requester");
  frm.trucmms_action=action=>frappe.prompt({fieldname:"reason",label:__("Reason / Summary"),fieldtype:"Small Text",reqd:1},async values=>{
   await frappe.call({method:"vanbags_maintenance.lifecycle.perform",type:"POST",args:{work_order:frm.doc.name,action,reason:values.reason}});await frm.reload_doc();
  },__(action));
  const action=name=>frm.add_custom_button(__(name),()=>frm.trucmms_action(name));
  if(frm.states&&!frm.states.trucmms_lifecycle_bound){
   const original=frm.states.handle_workflow_action.bind(frm.states);
   const controlled=["Complete Work","Verify Work","Accept Work","Accept on Behalf","Request Rework","Close Order","Cancel Order","Hold Work","Resume Work","Reopen Order"];
   frm.states.handle_workflow_action=transition=>controlled.includes(transition.action)?frm.trucmms_action(transition.action):original(transition);frm.states.trucmms_lifecycle_bound=true;
  }
  for(const field of ["subject","scope","priority","target_closure","scheduled_start","scheduled_end","acceptance_user"])frm.set_df_property(field,"read_only",frm.doc.status!=="Draft"||(field==="acceptance_user"&&frm.doc.origin_type==="Maintenance Request"));
  const assignment_locked=["On Hold","Technical Completed","Verified","Accepted","Closed","Cancelled"].includes(frm.doc.status)||(managed&&frm.doc.status==="Assigned");
  for(const field of ["responsible_team","required_discipline"])frm.set_df_property(field,"read_only",assignment_locked||frm.doc.team_policy==="Legacy");
  if(managed)frm.set_df_property("assigned_to","read_only",assignment_locked||frm.doc.status==="Assigned");
  frm.set_query("responsible_team",()=>({filters:{company:frm.doc.company,disabled:0}}));frm.set_query("required_discipline",()=>({filters:{disabled:0}}));
  if(frm.is_new())return;
  frm.add_custom_button(__("Work Register"),()=>frappe.set_route("query-report","TruCMMS Work Register",{work_order:frm.doc.name}));
  for(const [label,type] of [["Lifecycle History","TruCMMS Work Event"],["Execution History","TruCMMS Work Execution"],["Cycle History","TruCMMS Work Cycle"],["Allocations","TruCMMS Work Allocation"]])frm.add_custom_button(__(label),()=>frappe.set_route("List",type,{work_order:frm.doc.name}));
  if(frm.doc.status==="Assigned"&&primary&&technician)action("Complete Work");
  let allocated=primary;
  if(managed&&technician&&!primary){const result=await frappe.call({method:"vanbags_maintenance.allocations.mine",args:{work_order:frm.doc.name}});allocated=!!result.message;}
  if(frm.doc.status==="Assigned"&&allocated&&technician)frm.page.set_primary_action(__("Record Execution"),()=>frappe.new_doc("TruCMMS Work Execution",{work_order:frm.doc.name,company:frm.doc.company,site:frm.doc.site}));
  if(frm.doc.status==="Technical Completed"){
   if(managed&&supervisor)action("Verify Work");
   if(!managed&&acceptor)action("Accept Work");
   if(!managed&&supervisor)action("Accept on Behalf");
   if(supervisor||acceptor)action("Request Rework");
  }
  if(managed&&frm.doc.status==="Verified"){
   if(frm.doc.acceptance_required&&acceptor)action("Accept Work");
   if(frm.doc.acceptance_required&&supervisor)action("Accept on Behalf");
   if(!frm.doc.acceptance_required&&supervisor)action("Close Order");
   if(supervisor||acceptor)action("Request Rework");
  }
  if(supervisor){
   if(frm.doc.status==="Accepted")action("Close Order");
   if(["Draft","Authorized","Assigned","On Hold","Technical Completed","Verified"].includes(frm.doc.status))action("Cancel Order");
   if(managed&&["Authorized","Assigned"].includes(frm.doc.status))action("Hold Work");
   if(managed&&frm.doc.status==="On Hold")action("Resume Work");
   if(frm.doc.status==="Closed")action("Reopen Order");
   if(managed&&["Draft","Authorized","Assigned","On Hold"].includes(frm.doc.status))frm.add_custom_button(__("Reschedule Work"),()=>frappe.prompt([
    {fieldname:"scheduled_start",label:__("Scheduled Start"),fieldtype:"Datetime",default:frm.doc.scheduled_start},
    {fieldname:"scheduled_end",label:__("Scheduled End"),fieldtype:"Datetime",default:frm.doc.scheduled_end},
    {fieldname:"target_closure",label:__("Target Closure"),fieldtype:"Datetime",default:frm.doc.target_closure},
    {fieldname:"reason",label:__("Reason"),fieldtype:"Small Text",reqd:1}
   ],async values=>{await frappe.call({method:"vanbags_maintenance.work_cycle.replan",type:"POST",args:{work_order:frm.doc.name,...values}});await frm.reload_doc();},__("Reschedule Work")));
   if(managed&&(frm.doc.status==="Assigned"||frm.doc.status==="On Hold"&&frm.doc.hold_from_state==="Assigned"))frm.add_custom_button(__("Reassign Work"),()=>frappe.prompt([
    {fieldname:"technician",label:__("Technician"),fieldtype:"Link",options:"User",reqd:1},
    {fieldname:"team",label:__("Responsible Team"),fieldtype:"Link",options:"TruCMMS Maintenance Team",default:frm.doc.responsible_team},
    {fieldname:"discipline",label:__("Required Discipline"),fieldtype:"Link",options:"TruCMMS Discipline",default:frm.doc.required_discipline},
    {fieldname:"reason",label:__("Reason"),fieldtype:"Small Text",reqd:1}
   ],async values=>{await frappe.call({method:"vanbags_maintenance.work_cycle.reassign",type:"POST",args:{work_order:frm.doc.name,...values}});await frm.reload_doc();},__("Reassign Work")));
   if(managed&&frm.doc.origin_type==="Direct"&&frm.doc.status==="Authorized")frm.add_custom_button(__("Designate Acceptor"),()=>frappe.prompt([
    {fieldname:"user",label:__("Acceptance User"),fieldtype:"Link",options:"User",reqd:1},
    {fieldname:"reason",label:__("Reason"),fieldtype:"Small Text",reqd:1}
   ],async values=>{await frappe.call({method:"vanbags_maintenance.work_cycle.designate_acceptor",type:"POST",args:{work_order:frm.doc.name,...values}});await frm.reload_doc();}));
   if(managed&&frm.doc.status==="Assigned")frm.add_custom_button(__("Add Participant"),()=>frappe.prompt([
    {fieldname:"technician",label:__("Technician"),fieldtype:"Link",options:"User",reqd:1},
    {fieldname:"discipline",label:__("Discipline"),fieldtype:"Link",options:"TruCMMS Discipline",reqd:1},
    {fieldname:"reason",label:__("Reason"),fieldtype:"Small Text",reqd:1}
   ],async values=>{await frappe.call({method:"vanbags_maintenance.allocations.add",type:"POST",args:{work_order:frm.doc.name,...values}});await frm.reload_doc();},__("Add Participant")));
   if(!managed&&["Draft","Authorized","Assigned","Technical Completed"].includes(frm.doc.status))frm.add_custom_button(__("Adopt C Lifecycle"),()=>frappe.prompt({fieldname:"reason",label:__("Reason"),fieldtype:"Small Text",reqd:1},async values=>{await frappe.call({method:"vanbags_maintenance.work_cycle.adopt",type:"POST",args:{work_order:frm.doc.name,...values}});await frm.reload_doc();}));
   if(frm.doc.team_policy==="Legacy"&&["Draft","Authorized","Assigned"].includes(frm.doc.status))frm.add_custom_button(__("Adopt Team Eligibility"),()=>frappe.prompt([
    {fieldname:"team",label:__("Responsible Team"),fieldtype:"Link",options:"TruCMMS Maintenance Team",reqd:1},
    {fieldname:"discipline",label:__("Required Discipline"),fieldtype:"Link",options:"TruCMMS Discipline",reqd:1},
    {fieldname:"reason",label:__("Reason"),fieldtype:"Small Text",reqd:1}
   ],async values=>{await frappe.call({method:"vanbags_maintenance.teams.adopt_legacy",type:"POST",args:{work_order:frm.doc.name,...values}});await frm.reload_doc();}));
  }
 }
});
