(function () {
 const eligible = () => frappe.user.has_role(['TruCMMS Supervisor', 'TruCMMS Dispatcher', 'System Manager']);
 const escape = value => frappe.utils.escape_html(String(value ?? ''));
 frappe.ui.form.on('TruCMMS Site Warehouse', {
  setup(frm) {
   frm.set_query('site', () => ({filters: {company: frm.doc.company, disabled: 0}}));
   frm.set_query('warehouse', () => ({filters: {company: frm.doc.company, is_group: 0, disabled: 0}}));
  },
  refresh(frm) {
   if (!frm.is_new()) for (const field of ['company', 'site', 'warehouse']) frm.set_df_property(field, 'read_only', 1);
   if (!frappe.model.can_read('Warehouse')) frm.set_intro(__('Configurar este vínculo requiere permiso nativo de lectura de Warehouse y autorización de supervisor para la empresa y sede.'), 'orange');
  }
 });
 frappe.ui.form.on('TruCMMS Maintenance Work Order', {
  refresh(frm) {
   if (frm.is_new()) return;
   if (frappe.model.can_create('Material Request') && frappe.user.has_role(['TruCMMS Supervisor','TruCMMS Dispatcher','TruCMMS Technician','System Manager']) && ['Authorized','Assigned'].includes(frm.doc.status)) {
    frm.add_custom_button(__('Solicitar salida'), () => {
     const key=crypto.randomUUID();
     let materials=[];
     try {materials=JSON.parse(frm.doc.pm_procedure_snapshot||'{}').materials||[];} catch(error) {materials=[];}
     frappe.prompt([
      {fieldname:'warehouse',label:__('Almacén autorizado'),fieldtype:'Link',options:'Warehouse',reqd:1,get_query:()=>({filters:{company:frm.doc.company,disabled:0,is_group:0}})},
      {fieldname:'reason',label:__('Motivo de solicitud'),fieldtype:'Small Text',reqd:1},
      {fieldname:'items',label:__('Materiales inventariables'),fieldtype:'Table',reqd:1,in_place_edit:true,
       fields:[{fieldname:'item',label:__('Artículo'),fieldtype:'Link',options:'Item',reqd:1,in_list_view:1,get_query:()=>({filters:{disabled:0,has_variants:0,is_stock_item:1}})},
        {fieldname:'quantity',label:__('Cantidad'),fieldtype:'Float',reqd:1,in_list_view:1},
        {fieldname:'stock_uom',label:__('Unidad de inventario'),fieldtype:'Link',options:'UOM',reqd:1,in_list_view:1}],
       data:materials.map(r=>({item:r.item,quantity:r.stock_quantity,stock_uom:r.stock_uom}))}
     ],async values=>{
      const items=values.items.map(r=>({item:r.item,quantity:r.quantity,stock_uom:r.stock_uom}));
      const {message}=await frappe.call({method:'vanbags_maintenance.materials.issue_request',type:'POST',freeze:true,args:{order:frm.doc.name,warehouse:values.warehouse,reason:values.reason,items:JSON.stringify(items),key}});
      frappe.set_route('Form','Material Request',message.name);
     },__('Solicitar materiales a almacén (borrador)'));
    }, __('Materiales'));
   }
   if (frappe.model.can_read('Material Request')) frm.add_custom_button(__('Requerimientos de la orden'),()=>frappe.set_route('List','Material Request',{trucmms_work_order:frm.doc.name}),__('Materiales'));
   if (!eligible()) return;
   frm.add_custom_button(__('Contexto logístico'), async () => {
    const {message: data} = await frappe.call({method: 'vanbags_maintenance.logistics.context', type: 'GET', args: {order: frm.doc.name}});
    const rows = data.warehouses.map(row => `<li>${escape(row.warehouse)}</li>`).join('');
    frappe.msgprint({title: __('Almacenes autorizados de la sede'), message:
     `<p>${escape(data.company)} · ${escape(data.site)}</p>` +
     (data.can_read_warehouse ? (rows ? `<ul>${rows}</ul>` : '<p>Sin almacenes habilitados para esta sede y usuario.</p>') : '<p>Se requiere permiso nativo de lectura de Warehouse para consultar almacenes.</p>') +
     '<p>Esta consulta no reserva ni consume existencias.</p>'});
   }, __('Materiales'));
   if (frappe.model.can_read('Item')) frm.add_custom_button(__('Buscar artículo'), () => {
    frappe.prompt([{fieldname: 'search', label: __('Código o nombre'), fieldtype: 'Data', reqd: 1}], async values => {
     const {message: rows} = await frappe.call({method: 'vanbags_maintenance.logistics.item_choices', type: 'GET', args: {order: frm.doc.name, search: values.search}});
     frappe.msgprint({title: __('Catálogo de artículos'), message: rows.length ? rows.map(row => `<p>${escape(row.name)} · ${escape(row.item_name)} · ${escape(row.stock_uom)} · ${row.is_stock_item ? __('Inventariable') : __('No inventariable')}</p>`).join('') : __('Sin resultados autorizados. La búsqueda muestra hasta 20 artículos.')});
    }, __('Buscar artículo'));
   }, __('Materiales'));
  }
 });
})();
