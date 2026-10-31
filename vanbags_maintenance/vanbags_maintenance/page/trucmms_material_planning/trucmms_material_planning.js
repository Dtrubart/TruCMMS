frappe.pages['trucmms-material-planning'].on_page_load = function(wrapper) {
 const page=frappe.ui.make_app_page({parent:wrapper,title:__('Proyección de materiales'),single_column:true});
 const root=$('<div class="material-planning"></div>').appendTo(page.body);
 $('<style>').text('.material-planning{padding:16px}.material-planning .material-results{overflow-x:auto}.material-planning td,.material-planning th{padding:8px;white-space:nowrap}.material-planning button{min-height:44px;margin:4px}').appendTo(root);
 const notice=$('<p role="status"></p>').appendTo(root);
 $('<p>').text(__('Demanda bruta de procedimientos aprobados. No descuenta existencias ni reserva stock. Revisa cantidades y disponibilidad antes de comprar.')).appendTo(root);
 const results=$('<div class="material-results"></div>').appendTo(root),actions=$('<div></div>').appendTo(root);
 const company=page.add_field({fieldname:'company',label:__('Empresa'),fieldtype:'Link',options:'Company',reqd:1});
 const site=page.add_field({fieldname:'site',label:__('Sede'),fieldtype:'Link',options:'TruCMMS Site',reqd:1,get_query:()=>({filters:{company:company.get_value(),disabled:0}})});
 const from=page.add_field({fieldname:'from_date',label:__('Desde'),fieldtype:'Date',default:frappe.datetime.get_today(),reqd:1});
 const until=page.add_field({fieldname:'to_date',label:__('Hasta'),fieldtype:'Date',default:frappe.datetime.add_days(frappe.datetime.get_today(),30),reqd:1});
 let report=null,identity=null;
 function filters(){return {company:company.get_value(),site:site.get_value(),from_date:from.get_value(),to_date:until.get_value()};}
 function valid(){return Object.values(filters()).every(Boolean);}
 function cell(row,value){$('<td>').text(value??'').appendTo(row);}
 async function load(){
  if(!valid()){frappe.msgprint(__('Selecciona empresa, sede y período.'));return;}
  report=null;identity=null;actions.empty();results.empty();notice.text(__('Cargando…'));
  const current=filters();
  try{
   const {message:data}=await frappe.call({method:'vanbags_maintenance.materials.forecast',type:'GET',args:current});
   if(JSON.stringify(filters())!==JSON.stringify(current)){notice.text(__('Los filtros cambiaron; actualiza la proyección.'));return;}
   report=data;identity=crypto.randomUUID();notice.text(__(`${data.rows.length} necesidades de materiales. Las cantidades ya requeridas no se vuelven a enviar.`));
   const table=$('<table class="table table-bordered">').appendTo(results),head=$('<tr>').appendTo($('<thead>').appendTo(table));
   for(const text of ['Artículo','Unidad','Previsto','En requerimientos','Sin requerimiento'])$('<th>').text(__(text)).appendTo(head);
   const body=$('<tbody>').appendTo(table);
   for(const item of data.totals){const row=$('<tr>').appendTo(body);for(const key of ['item','stock_uom','quantity','already_requested','unrequested_quantity'])cell(row,item[key]);}
   if(!data.rows.length)notice.text(__('Sin materiales previstos en el período.'));
   if(data.can_create_request&&data.rows.some(r=>!r.covered))$('<button class="btn btn-primary">').text(__('Crear requerimiento de compra')).appendTo(actions).on('click',()=>{
    if(JSON.stringify(filters())!==JSON.stringify(current)){frappe.msgprint(__('Actualiza la proyección después de cambiar filtros.'));return;}
    frappe.prompt([{fieldname:'warehouse',label:__('Almacén destino autorizado'),fieldtype:'Link',options:'Warehouse',reqd:1,get_query:()=>({filters:{company:current.company,disabled:0,is_group:0}})},
     {fieldname:'reason',label:__('Motivo y revisión de cantidades'),fieldtype:'Small Text',reqd:1}],async values=>{
      const response=await frappe.call({method:'vanbags_maintenance.materials.purchase_request',type:'POST',freeze:true,args:{...current,...values,keys:JSON.stringify(data.rows.filter(r=>!r.covered).map(r=>r.key)),key:identity}});
      frappe.set_route('Form','Material Request',response.message.name);
     },__('Enviar demanda bruta a logística (borrador)'));
   });
  }catch(error){notice.text(__('No se pudo cargar la proyección. Revisa los permisos y el período.'));}
 }
 page.set_primary_action(__('Consultar'),load);
 page.add_inner_button(__('Ver detalle por trabajo'),()=>{
  if(!report){frappe.msgprint(__('Consulta una proyección primero.'));return;}
  const escape=frappe.utils.escape_html;
  frappe.msgprint({title:__('Origen de la demanda'),message:report.rows.map(r=>`<p>${escape(r.needed_on)} · ${escape(r.equipment)} · ${escape(r.item)}: ${escape(String(r.quantity))} ${escape(r.stock_uom)} · ${escape(r.occurrence)}</p>`).join('')||__('Sin materiales.')});
 });
 page.add_inner_button(__('Descargar lista de compras'),()=>{
  if(!valid()){frappe.msgprint(__('Selecciona empresa, sede y período.'));return;}
  window.open('/api/method/vanbags_maintenance.resource_planning.shopping_csv?'+new URLSearchParams(filters()).toString(),'_blank','noopener');
 });
 page.add_inner_button(__('Consultar existencias'),()=>{
  if(!valid()){frappe.msgprint(__('Selecciona empresa, sede y período.'));return;}
  frappe.prompt([{fieldname:'warehouse',label:__('Almacén autorizado'),fieldtype:'Link',options:'Warehouse',reqd:1,get_query:()=>({filters:{company:company.get_value(),disabled:0,is_group:0}})}],async values=>{
   const {message:data}=await frappe.call({method:'vanbags_maintenance.resource_planning.availability',type:'GET',args:{...filters(),...values}});
   const esc=v=>frappe.utils.escape_html(String(v??''));
   frappe.msgprint({title:__('Disponibilidad orientativa'),message:'<p>'+__('Consulta actual, sin reserva ni garantía de disponibilidad futura. La propuesta descuenta stock disponible de las necesidades aún no requeridas.')+'</p>'+data.totals.map(r=>'<p>'+esc(r.item)+' · '+__('Disponible: ')+esc(r.available_now)+' · '+__('Compra sugerida: ')+esc(r.suggested_purchase)+' '+esc(r.stock_uom)+'</p>').join('')});
  },__('Consultar stock nativo'));
 });
 const options=frappe.route_options||{};frappe.route_options=null;
 for(const [field,key] of [[company,'company'],[site,'site'],[from,'from_date'],[until,'to_date']])if(options[key])field.set_value(options[key]);
};
