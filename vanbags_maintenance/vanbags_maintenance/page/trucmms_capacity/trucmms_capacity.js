frappe.pages['trucmms-capacity'].on_page_load=function(wrapper){
 const page=frappe.ui.make_app_page({parent:wrapper,title:__('Capacidad y disponibilidad'),single_column:true});
 const root=$('<div class="capacity-view" style="padding:16px"></div>').appendTo(page.body);
 $('<p>').text(__('La capacidad usa ventanas de trabajo explícitas y descuenta ausencias. Sin calendario se muestra «Sin configurar». La carga considera asignaciones activas; esta consulta no asigna ni autoriza trabajos.')).appendTo(root);
 const status=$('<p role="status"></p>').appendTo(root),results=$('<div style="overflow-x:auto"></div>').appendTo(root);
 const company=page.add_field({fieldname:'company',label:__('Empresa'),fieldtype:'Link',options:'Company',reqd:1});
 const site=page.add_field({fieldname:'site',label:__('Sede'),fieldtype:'Link',options:'TruCMMS Site',reqd:1,get_query:()=>({filters:{company:company.get_value()}})});
 const technician=page.add_field({fieldname:'technician',label:__('Técnico'),fieldtype:'Link',options:'User',reqd:1});
 const first=page.add_field({fieldname:'from_date',label:__('Desde'),fieldtype:'Date',default:frappe.datetime.get_today(),reqd:1});
 const last=page.add_field({fieldname:'to_date',label:__('Hasta'),fieldtype:'Date',default:frappe.datetime.add_days(frappe.datetime.get_today(),6),reqd:1});
 function filters(){return {company:company.get_value(),site:site.get_value(),technician:technician.get_value(),from_date:first.get_value(),to_date:last.get_value()};}
 page.set_primary_action(__('Consultar'),async()=>{
  const args=filters();if(!Object.values(args).every(Boolean)){frappe.msgprint(__('Completa los filtros.'));return;}
  status.text(__('Consultando…'));results.empty();
  try{
   const {message:data}=await frappe.call({method:'vanbags_maintenance.capacity.overview',type:'GET',args});
   if(JSON.stringify(args)!==JSON.stringify(filters())){status.text(__('Los filtros cambiaron; consulta nuevamente.'));return;}
   status.text(__('Zona de la sede: ')+data.time_zone);
   const table=$('<table class="table table-bordered"><thead><tr></tr></thead><tbody></tbody></table>').appendTo(results);
   for(const label of ['Fecha','Disponible (h)','Programado (h)','Libre (h)','Sobrecarga (h)','Solapamiento (h)','Fuera de disponibilidad (h)'])$('<th style="white-space:nowrap">').text(__(label)).appendTo(table.find('thead tr'));
   for(const day of data.days){const row=$('<tr>').appendTo(table.find('tbody'));for(const key of ['date','available_hours','scheduled_hours','free_hours','overload_hours','overlap_hours','outside_hours'])$('<td>').text(day[key]===null?__('Sin configurar'):day[key]).appendTo(row);}
   if(data.unscheduled_orders.length)$('<p>').text(__('Órdenes visibles sin programación: ')+data.unscheduled_orders.join(', ')).appendTo(results);
  }catch(error){status.text(__('No se pudo consultar la capacidad. Revisa el período y los permisos.'));}
 });
 if(frappe.model.can_read('TruCMMS Resource Window'))page.add_inner_button(__('Ventanas y ausencias'),()=>frappe.set_route('List','TruCMMS Resource Window'));
};
