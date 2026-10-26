frappe.ui.form.on("VB Equipment", {
    setup(frm) {
        frm.set_query("site", () => ({filters: {company: frm.doc.company, disabled: 0}}));
        frm.set_query("location", () => ({filters: {
            company: frm.doc.company, site: frm.doc.site, disabled: 0,
            ...(false ? {name: ["!=", frm.doc.name]} : {})
        }}));
    }
});

frappe.ui.form.on("VB Equipment",{refresh(frm){if(!frm.is_new())frm.add_custom_button(__("Maintenance History"),()=>frappe.set_route("query-report","TruCMMS Equipment History",{equipment:frm.doc.name}));}});

frappe.ui.form.on("VB Equipment", {
 refresh(frm) {
  if (frm.is_new()) return;
  frm.add_custom_button(__("Installation History"),()=>frappe.set_route("query-report","TruCMMS Installation Register",{equipment:frm.doc.name,active_only:0}),__("Asset"));
  if (!frappe.user.has_role(["VB Maintenance Manager","System Manager"])) return;
  const action=(method,args)=>frappe.call({method:"vanbags_maintenance.assets."+method,args:{equipment:frm.doc.name,...args},freeze:true}).then(()=>frm.reload_doc());
  const reasonAction=(label,method,extra=[])=>{
   const d=new frappe.ui.Dialog({title:__(label),fields:[...extra,{fieldname:"reason",label:__("Reason"),fieldtype:"Small Text",reqd:1}],primary_action_label:__(label),primary_action:async values=>{await action(method,values);d.hide();}});d.show();
  };
  if(frm.doc.placement_policy==="Legacy") {
   frm.add_custom_button(__("Declare Placement Baseline"),()=>reasonAction("Declare Placement Baseline","adopt"),__("Asset"));
  } else {
   frm.add_custom_button(__("Place / Transfer"),()=>reasonAction("Place / Transfer","place",[
    {fieldname:"site",label:__("Target Site"),fieldtype:"Link",options:"TruCMMS Site",reqd:1,default:frm.doc.site,get_query:()=>({filters:{company:frm.doc.company,disabled:0}})},
    {fieldname:"location",label:__("Target Functional Location"),fieldtype:"Link",options:"VB Equipment Location",get_query:()=>({filters:{company:frm.doc.company,site:cur_dialog.get_value("site"),disabled:0}}),description:__("Leave blank for mobile equipment or site custody.")}
   ]),__("Asset"));
   frm.add_custom_button(__("Remove Equipment"),()=>reasonAction("Remove Equipment","remove"),__("Asset"));
   if(frm.doc.location)frm.add_custom_button(__("Replace Equipment"),()=>reasonAction("Replace Equipment","replace",[{fieldname:"replacement",label:__("Replacement Equipment"),fieldtype:"Link",options:"VB Equipment",reqd:1,get_query:()=>({filters:{company:frm.doc.company,site:frm.doc.site,location:["is","not set"],name:["!=",frm.doc.name]}})}]),__("Asset"));
  }
  frm.add_custom_button(__("Configure Asset"),()=>{
   const select=new frappe.ui.Dialog({title:__("Configure Asset"),fields:[
    {fieldname:"asset_tag",label:__("Asset Tag"),fieldtype:"Data",default:frm.doc.asset_tag},
    {fieldname:"technical_profile",label:__("Technical Profile"),fieldtype:"Link",options:"TruCMMS Equipment Profile",default:frm.doc.technical_profile,get_query:()=>({filters:{disabled:0}})},
    {fieldname:"criticality",label:__("Criticality"),fieldtype:"Link",options:"TruCMMS Criticality",default:frm.doc.criticality,get_query:()=>({filters:{disabled:0}})},
    {fieldname:"reason",label:__("Reason"),fieldtype:"Small Text",reqd:1}
   ],primary_action_label:__("Continue"),primary_action:async config=>{
    const profile=config.technical_profile ? await frappe.db.get_doc("TruCMMS Equipment Profile",config.technical_profile) : {definitions:[]};
    const old=config.technical_profile===frm.doc.technical_profile ? Object.fromEntries((frm.doc.attributes||[]).map(r=>[r.key,r.value])) : {};
    const types={Text:"Data",Integer:"Int",Decimal:"Float",Date:"Date",Boolean:"Check",Choice:"Select"};
    const fields=profile.definitions.map(r=>({fieldname:"attr_"+r.key,label:r.label+(r.unit ? " ("+r.unit+")" : ""),fieldtype:types[r.value_type],options:r.value_type==="Choice" ? "\n"+r.choices : undefined,reqd:r.value_type!=="Boolean" && r.required,default:old[r.key],description:[r.minimum ? "Min: "+r.minimum : "",r.maximum ? "Max: "+r.maximum : ""].filter(Boolean).join("; ")}));
    const save=async values=>{const attributes={};for(const r of profile.definitions){const v=values["attr_"+r.key];if(v!==null && v!==undefined && v!=="")attributes[r.key]=String(v);}await action("configure",{...config,values:JSON.stringify(attributes)});};
    if(!fields.length){await save({});select.hide();return;}
    const edit=new frappe.ui.Dialog({title:__("Profile Attributes"),fields,primary_action_label:__("Save Configuration"),primary_action:async values=>{await save(values);edit.hide();select.hide();}});edit.show();
   }});select.show();
  },__("Asset"));
 }
});
