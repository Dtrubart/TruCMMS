frappe.trucmms_organization_change = function (doc, kind, done) {
 const site = kind === 'site';
 const dialog = new frappe.ui.Dialog({title: __(site ? 'Asignar unidad operativa' : 'Cambiar estructura operativa'), fields: [
  ...(!site ? [{fieldname:'action', label:__('Acción'), fieldtype:'Select', options:'Reparent\nDeactivate\nReactivate', reqd:1}] : []),
  {fieldname:'unit', label:__(site ? 'Unidad (vacío = sin agrupación)' : 'Nuevo padre (vacío = raíz)'), fieldtype:'Link', options:'TruCMMS Operating Unit',
   depends_on:site ? undefined : "eval:doc.action=='Reparent'", get_query:()=>({filters:{company:doc.company,disabled:0,...(!site ? {name:['!=',doc.name]} : {})}})},
  {fieldname:'reason',label:__('Motivo'),fieldtype:'Small Text',reqd:1},
  {fieldtype:'HTML',options:'<p>'+__('El cambio es inmediato. No modifica permisos, activos, órdenes ni documentos financieros.')+'</p>'}
 ], primary_action_label:__('Ver impacto'), primary_action:async values=>{
  const args = site ? {site:doc.name,unit:values.unit||''} : {name:doc.name,action:values.action,parent:values.action==='Reparent' ? values.unit||'' : ''};
  dialog.disable_primary_action();
  try {
   const {message:impact} = await frappe.call({method:'vanbags_maintenance.operating_units.'+(site?'preview_site':'preview_unit'),args});
   const before = site ? impact.before.path : impact.before, after = site ? impact.after.path : impact.after;
   const escape=frappe.utils.escape_html, format=rows=>rows.map(row=>row.unit_name).join(' / ')||__('Sin agrupación');
   frappe.confirm('<p>'+__('Antes')+': '+escape(format(before))+'</p><p>'+__('Después')+': '+escape(format(after))+'</p><p>'+__('Motivo')+': '+escape(values.reason)+'</p>'+(!site ? '<p>'+__('Unidades afectadas: {0}',[impact.affected])+'</p><p>'+__('Sedes afectadas: {0}',[impact.affected_sites])+'</p>' : ''),async()=>{
    dialog.disable_primary_action();
    try {
     await frappe.call({method:'vanbags_maintenance.operating_units.'+(site?'assign_site':'change_unit'),args:{...args,token:impact.token,reason:values.reason},freeze:true});
     dialog.hide();frappe.show_alert({message:__('Organización actualizada'),indicator:'green'});if(done)done();
    } finally {dialog.enable_primary_action();}
   });
  } finally {dialog.enable_primary_action();}
 }});
 dialog.show();
};

for (const doctype of ['TruCMMS Operating Unit','TruCMMS Site']) frappe.ui.form.on(doctype,{
 refresh(frm){
  const site=doctype==='TruCMMS Site', admin=frappe.session.user==='Administrator'||frappe.user.has_role('System Manager');
  if(site&&!admin)frm.set_df_property('operating_unit','read_only',1);
  if(frm.is_new())return;
  for(const field of site?['operating_unit']:['parent_unit','disabled','company','unit_code'])frm.set_df_property(field,'read_only',1);
  if(!site||frm.doc.operating_unit)frm.add_custom_button(__('Estructura operativa'),()=>{
   if(frm.is_dirty()){frappe.msgprint(__('Guarda o descarta los cambios antes de navegar.'));return;}
   frappe.route_options={company:frm.doc.company,unit:site?frm.doc.operating_unit:frm.doc.name};frappe.set_route('trucmms-organization');
  });
  if(admin)frm.add_custom_button(__(site?'Asignar unidad operativa':'Cambiar estructura operativa'),()=>{
   if(frm.is_dirty()){frappe.msgprint(__('Guarda o descarta los cambios antes de continuar.'));return;}
   frappe.trucmms_organization_change(frm.doc,site?'site':'unit',()=>frm.reload_doc());
  });
  if(admin&&site)frm.add_custom_button(__('Historial de agrupación'),()=>{
   frappe.route_options={site:frm.doc.name};frappe.set_route('List','TruCMMS Organization Event');
  });
 }
});
