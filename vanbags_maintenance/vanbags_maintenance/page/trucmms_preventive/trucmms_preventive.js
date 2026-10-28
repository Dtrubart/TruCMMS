frappe.pages['trucmms-preventive'].on_page_load=function(wrapper){
 const page=frappe.ui.make_app_page({parent:wrapper,title:__('Programación preventiva'),single_column:true});
 const root=$('<div class="pm-schedule"></div>').appendTo(page.body);
 $('<style>').text('.pm-schedule .pm-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:5px;margin:15px 0}.pm-schedule .pm-day{min-height:110px;border:1px solid var(--border-color);border-radius:6px;padding:6px;overflow-wrap:anywhere}.pm-schedule .pm-card{display:block;border:0;border-left:4px solid #3b82f6;background:var(--control-bg);padding:6px;margin:5px 0;width:100%;text-align:left;white-space:normal;overflow-wrap:anywhere}.pm-schedule .pm-list{overflow-x:auto}.pm-schedule td,.pm-schedule th{padding:8px;border-bottom:1px solid var(--border-color)}@media(max-width:600px){.pm-schedule .pm-grid{grid-template-columns:1fr}.pm-schedule .pm-day{min-height:0}.pm-schedule .pm-empty{display:none}}').appendTo(root);
 const notice=$('<div role="status" aria-live="polite"></div>').appendTo(root),counts=$('<p></p>').appendTo(root),body=$('<div></div>').appendTo(root);
 let ready=false,seq=0,mode='Calendar';const today=frappe.datetime.get_today();
 const fields={};
 for(const def of [{fieldname:'company',label:'Empresa',fieldtype:'Link',options:'Company'},{fieldname:'site',label:'Sede',fieldtype:'Link',options:'TruCMMS Site'},{fieldname:'equipment',label:'Equipo',fieldtype:'Link',options:'VB Equipment'},{fieldname:'plan',label:'Plan',fieldtype:'Link',options:'TruCMMS PM Plan'},{fieldname:'from_date',label:'Desde',fieldtype:'Date',default:today.slice(0,7)+'-01'},{fieldname:'to_date',label:'Hasta',fieldtype:'Date',default:frappe.datetime.add_days(today,30)}])fields[def.fieldname]=page.add_field({...def,change:()=>ready&&load()});
 function args(){return Object.fromEntries(Object.entries(fields).map(([k,v])=>[k,v.get_value()]).filter(([,v])=>v));}
 function button(row,parent){
  const label=row.order_status==='In Progress'?'En proceso':({Planned:'Programada',Released:'Orden abierta',Completed:'Validada',Skipped:'Omitida',Cancelled:'Cancelada'}[row.status]||row.status);
  const color={Planned:'#3b82f6',Released:'#f59e0b',Completed:'#16a34a',Skipped:'#94a3b8',Cancelled:'#ef4444'}[row.status];
  const b=$('<button type="button" class="pm-card"></button>').css('border-left-color',color).attr('data-occurrence',row.name).appendTo(parent);
  $('<strong></strong>').text(row.subject).appendTo(b);$('<div></div>').text(row.equipment+' · '+label).appendTo(b);
  if(String(row.original_due)!==String(row.planned_for))$('<small></small>').text('Vencimiento original: '+row.original_due).appendTo(b);
  b.on('click',()=>frappe.set_route('Form','TruCMMS PM Occurrence',row.name));
 }
 async function load(){
  const request=++seq;notice.text(__('Cargando programación…'));body.empty();
  try{const {message}=await frappe.call({method:'vanbags_maintenance.preventive.schedule',type:'GET',args:args()});if(request!==seq)return;
   const rows=message.rows,totals={};for(const row of rows)totals[row.status]=(totals[row.status]||0)+1;
   counts.text('Programadas: '+(totals.Planned||0)+' · Liberadas: '+(totals.Released||0)+' · Validadas: '+(totals.Completed||0)+' · Omitidas: '+(totals.Skipped||0));
   notice.text(message.truncated?'Se muestran 500 ocurrencias; reduce el período.':'Las programadas no son órdenes abiertas. Se muestran ocurrencias materializadas; el plan ofrece vista previa y horizonte configurables.');
   if(mode==='List'){
    const table=$('<table class="table"><thead><tr><th>Fecha prevista</th><th>Vencimiento original</th><th>Trabajo y estado</th></tr></thead><tbody></tbody></table>').appendTo($('<div class="pm-list"></div>').appendTo(body));
    for(const row of rows){const tr=$('<tr></tr>').appendTo(table.find('tbody'));$('<td></td>').text(row.planned_for).appendTo(tr);$('<td></td>').text(row.original_due).appendTo(tr);button(row,$('<td></td>').appendTo(tr));}
   }else{
    const grid=$('<div class="pm-grid"></div>').appendTo(body);let day=message.from_date;
    while(day<=message.to_date){const entries=rows.filter(r=>r.planned_for===day);const box=$('<section class="pm-day"></section>').toggleClass('pm-empty',!entries.length).appendTo(grid);$('<strong></strong>').text(frappe.datetime.str_to_user(day)).appendTo(box);for(const row of entries)button(row,box);day=frappe.datetime.add_days(day,1);}
   }
  }catch(e){if(request===seq)notice.text(__('No se pudo cargar la programación. Comprueba el período y los permisos.'));}
 }
 page.add_inner_button(__('Calendario'),()=>{mode='Calendar';load();});page.add_inner_button(__('Lista'),()=>{mode='List';load();});page.add_inner_button(__('Actualizar'),load);
 wrapper.pm_schedule={load};ready=true;load();
};
