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

(function(){
 const esc=v=>frappe.utils.escape_html(String(v??''));
 const api=(method,args)=>frappe.call({method:'vanbags_maintenance.'+method,args,type:method.endsWith('reconciliation')||method.endsWith('summary')?'GET':'POST',freeze:true});
 frappe.ui.form.on('Material Request',{refresh(frm){
  if(frm.doc.trucmms_origin==='TruCMMS'&&frm.doc.material_request_type==='Material Issue'&&frm.doc.docstatus===1&&frappe.model.can_create('Stock Entry')){
   frm.add_custom_button(__('Preparar vale de salida'),async()=>{
    const {message}=await api('fulfillment.delivery',{request:frm.doc.name,key:crypto.randomUUID()});
    frappe.set_route('Form','Stock Entry',message.name);
   },__('TruCMMS'));
  }
 }});
 frappe.ui.form.on('Stock Entry',{refresh(frm){
  if(!frm.doc.trucmms_work_order)return;
  frm.set_intro(__('Movimiento vinculado a mantenimiento. La confirmación de recogida se registra desde la orden; este documento conserva la aprobación y contabilización nativas.'));
  if(frm.doc.docstatus===1&&frm.doc.purpose==='Material Issue'&&frappe.model.can_create('Stock Entry')){
   frm.add_custom_button(__('Preparar devolución'),async()=>{
    const {message}=await api('fulfillment.return_draft',{issue:frm.doc.name,key:crypto.randomUUID()});
    frappe.set_route('Form','Stock Entry',message.name);
    frappe.show_alert({message:__('Revisa la cantidad que realmente devuelves antes de enviar el documento.'),indicator:'orange'});
   },__('TruCMMS'));
  }
 }});
 frappe.ui.form.on('TruCMMS Maintenance Work Order',{refresh(frm){
  if(frm.is_new())return;
  frm.add_custom_button(__('Entregas y devoluciones'),async()=>{
   const {message:data}=await api('fulfillment.reconciliation',{order:frm.doc.name});
   const dialog=new frappe.ui.Dialog({title:__('Materiales de la orden'),size:'large',fields:[{fieldname:'content',fieldtype:'HTML'}]});
   const root=dialog.fields_dict.content.$wrapper;
   root.html('<p>'+__('Salida neta = entregado menos devuelto. Los borradores y anulados no suman.')+'</p>');
   const wrap=$('<div style="overflow-x:auto"></div>').appendTo(root);
   const table=$('<table class="table table-bordered"><thead><tr><th>Artículo</th><th>Unidad</th><th>Solicitado</th><th>Entregado</th><th>Devuelto</th><th>Salida neta</th></tr></thead><tbody></tbody></table>').appendTo(wrap);
   for(const row of data.rows)$('<tr>').html(['item','stock_uom','requested','issued','returned','net_issued'].map(k=>'<td>'+esc(row[k])+'</td>').join('')).appendTo(table.find('tbody'));
   for(const movement of data.movements){
    const line=$('<div class="mb-3"></div>').appendTo(root);
    $('<span>').text(movement.name+' · '+movement.purpose+' · '+['Borrador','Enviado','Anulado'][movement.docstatus]).appendTo(line);
    if(movement.can_open)$('<button class="btn btn-xs btn-default ml-2">').text(__('Abrir vale')).appendTo(line).on('click',()=>frappe.set_route('Form','Stock Entry',movement.name));
    if(movement.acknowledgment){
     $('<p>').text(__('Recogida confirmada por ')+movement.acknowledgment.received_by+' · '+movement.acknowledgment.received_on).appendTo(line);
     $('<button class="btn btn-xs btn-default">').text(__('Ver constancia')).appendTo(line).on('click',()=>frappe.set_route('Form','TruCMMS Material Acknowledgment',movement.acknowledgment.name));
    }else if(movement.docstatus===1&&movement.purpose==='Material Issue'&&frappe.user.has_role(['TruCMMS Technician','TruCMMS Supervisor','System Manager'])){
     $('<button class="btn btn-sm btn-primary ml-2">').text(__('Confirmar recogida')).appendTo(line).on('click',()=>{
      const details=movement.items.map(r=>`${r.item_code}: ${r.transfer_qty} ${r.stock_uom}`).join('; ');
      frappe.prompt([{fieldname:'reason',label:__('Confirmo haber recibido: ')+details,fieldtype:'Small Text',reqd:1}],async values=>{
       await api('fulfillment.acknowledge',{stock_entry:movement.name,reason:values.reason});dialog.hide();frappe.show_alert({message:__('Recogida registrada con tu usuario y fecha.'),indicator:'green'});
      },__('Validar recogida completa del vale'));
     });
    }
   }
   dialog.show();
  },__('Materiales'));
  if(frappe.model.can_create('TruCMMS Material Estimate'))frm.add_custom_button(__('Agregar estimación'),()=>frappe.new_doc('TruCMMS Material Estimate',{work_order:frm.doc.name,needed_on:frappe.datetime.get_today()}),__('Materiales'));
  if(frappe.user.has_role(['TruCMMS Supervisor','TruCMMS Dispatcher','System Manager']))frm.add_custom_button(__('Costos vinculados'),async()=>{
   const {message:data}=await api('resource_costs.summary',{order:frm.doc.name});
   const labels={materials:__('Materiales netos'),services:__('Servicios facturados'),labor:__('Mano de obra interna')};
   let html='<p>'+esc(data.currency)+'</p>';
   for(const [name,row] of Object.entries(data.components))html+='<p>'+esc(labels[name])+': '+(row.available?esc(row.amount):__('No disponible con tus permisos'))+'</p>';
   html+='<p>'+__('Total: ')+(data.complete?esc(data.total):__('Incompleto por permisos'))+'</p><p>'+__('Valores de documentos enviados; se excluyen impuestos, borradores y anulados. La salida neta se valora con el libro de inventario nativo.')+'</p>';
   frappe.msgprint({title:__('Costos de la orden'),message:html});
  },__('Materiales'));
 }});
})();

frappe.ui.form.on('TruCMMS Material Acknowledgment',{refresh(frm){
 frm.set_df_property('items_snapshot','hidden',1);
 const esc=v=>frappe.utils.escape_html(String(v??''));
 let rows=[];try{rows=JSON.parse(frm.doc.items_snapshot||'[]');}catch(error){return;}
 frm.dashboard.add_section('<div style="overflow-x:auto"><table class="table table-bordered"><thead><tr><th>Artículo</th><th>Cantidad</th><th>Unidad</th><th>Almacén</th></tr></thead><tbody>'+rows.map(r=>'<tr>'+['item','quantity','stock_uom','warehouse'].map(k=>'<td>'+esc(r[k])+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>',__('Materiales recibidos'));
 frm.add_custom_button(__('Imprimir constancia'),()=>frappe.set_route('print',frm.doc.doctype,frm.doc.name));
}});
