/* The same preview/confirm action is used by the native form and location browser. */
frappe.trucmms_location_change = function (name, company, site, on_done) {
 const dialog = new frappe.ui.Dialog({title: __('Cambiar jerarquía o estado'), fields: [
  {fieldname: 'action', label: __('Acción'), fieldtype: 'Select', options: 'Reparent\nDeactivate\nReactivate', reqd: 1},
  {fieldname: 'parent', label: __('Nuevo padre (vacío = raíz)'), fieldtype: 'Link', options: 'VB Equipment Location',
   depends_on: "eval:doc.action=='Reparent'", get_query: () => ({filters: {company, site, disabled: 0, name: ['!=', name]}})},
  {fieldname: 'reason', label: __('Motivo'), fieldtype: 'Small Text', reqd: 1},
  {fieldname: 'notice', fieldtype: 'HTML', options: '<p>' + __('El cambio tiene efecto inmediato. No modifica las ubicaciones registradas en órdenes históricas.') + '</p>'}
 ], primary_action_label: __('Ver impacto'), primary_action: async values => {
  const args = {name, action: values.action, parent: values.action === 'Reparent' ? (values.parent || '') : ''};
  dialog.disable_primary_action();
  try {
   const {message: impact} = await frappe.call({method: 'vanbags_maintenance.location_hierarchy.preview', args});
   const escape = frappe.utils.escape_html;
   const description = '<p>' + __('Ubicaciones afectadas: {0}', [impact.affected]) + '</p><p>' +
    __('Ruta anterior') + ': ' + escape(impact.before.join(' / ')) + '</p><p>' +
    __('Ruta posterior') + ': ' + escape(impact.after.join(' / ')) + '</p><p>' +
    __('Acción') + ': ' + escape(impact.action) + '</p><p>' + __('Motivo') + ': ' + escape(values.reason) + '</p>';
   frappe.confirm(description, async () => {
    dialog.disable_primary_action();
    try {
     await frappe.call({method: 'vanbags_maintenance.location_hierarchy.change',
      args: {...args, token: impact.token, reason: values.reason}, freeze: true});
     dialog.hide(); frappe.show_alert({message: __('Cambio registrado'), indicator: 'green'});
     if (on_done) on_done();
    } finally { dialog.enable_primary_action(); }
   });
  } finally { dialog.enable_primary_action(); }
 }});
 dialog.show();
};

frappe.ui.form.on('VB Equipment Location', {
 refresh(frm) {
  if (frm.is_new()) return;
  frm.set_df_property('parent_location', 'read_only', 1);
  frm.set_df_property('disabled', 'read_only', 1);
  frm.add_custom_button(__('Árbol de ubicaciones'), () => {
   if (frm.is_dirty()) { frappe.msgprint(__('Guarda o descarta los cambios antes de navegar.')); return; }
   frappe.route_options = {company: frm.doc.company, site: frm.doc.site, location: frm.doc.name};
   frappe.set_route('trucmms-locations');
  });
  if (frappe.model.can_write(frm.doctype)) frm.add_custom_button(__('Cambiar jerarquía / estado'), () => {
   if (frm.is_dirty()) { frappe.msgprint(__('Guarda o descarta los cambios antes de continuar.')); return; }
   frappe.trucmms_location_change(frm.doc.name, frm.doc.company, frm.doc.site, () => frm.reload_doc());
  });
 }
});
