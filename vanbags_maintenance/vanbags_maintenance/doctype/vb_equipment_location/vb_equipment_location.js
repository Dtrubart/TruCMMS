frappe.ui.form.on("VB Equipment Location", {
    setup(frm) {
        frm.set_query("site", () => ({filters: {company: frm.doc.company, disabled: 0}}));
        frm.set_query("parent_location", () => ({filters: {
            company: frm.doc.company, site: frm.doc.site, disabled: 0,
            ...(true ? {name: ["!=", frm.doc.name]} : {})
        }}));
    }
});

frappe.ui.form.on("VB Equipment Location",{refresh(frm){
 if(frm.is_new() || !frappe.user.has_role(["VB Maintenance Manager","System Manager"]))return;
 frm.set_df_property("single_equipment","read_only",1);
 frm.add_custom_button(__("Configure Position"),()=>{
  const d=new frappe.ui.Dialog({title:__("Configure Position"),fields:[{fieldname:"single_equipment",label:__("Single Equipment Position"),fieldtype:"Check",default:frm.doc.single_equipment},{fieldname:"reason",label:__("Reason"),fieldtype:"Small Text",reqd:1}],primary_action_label:__("Save Policy"),primary_action:async values=>{await frappe.call({method:"vanbags_maintenance.assets.configure_position",args:{location:frm.doc.name,...values},freeze:true});d.hide();await frm.reload_doc();}});d.show();
 });
}});
