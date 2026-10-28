frappe.pages['trucmms-preventive'].on_page_load=function(wrapper){
 const page=frappe.ui.make_app_page({parent:wrapper,title:__('Programación preventiva'),single_column:true});
 const root=$('<div class="pm-schedule"></div>').appendTo(page.body);
 $('<style>').text('.pm-schedule .pm-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:5px;margin:15px 0}.pm-schedule .pm-day{min-height:110px;border:1px solid var(--border-color);border-radius:6px;padding:6px;overflow-wrap:anywhere}.pm-schedule .pm-card{display:block;border:0;border-left:4px solid #3b82f6;background:var(--control-bg);padding:6px;margin:5px 0;width:100%;text-align:left;white-space:normal;overflow-wrap:anywhere}.pm-schedule .pm-list{overflow-x:auto}.pm-schedule td,.pm-schedule th{padding:8px;border-bottom:1px solid var(--border-color)}@media(max-width:600px){.pm-schedule .pm-grid{grid-template-columns:1fr}.pm-schedule .pm-day{min-height:0}.pm-schedule .pm-empty,.pm-schedule .pm-weekday{display:none}}').appendTo(root);
 const notice=$('<div role="status" aria-live="polite"></div>').appendTo(root),counts=$('<p></p>').appendTo(root),body=$('<div></div>').appendTo(root);
 const weekdays=['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'];
 let ready=false,seq=0,mode='Calendar';const today=frappe.datetime.get_today();
 const fields={};
 for(const def of [{fieldname:'company',label:'Empresa',fieldtype:'Link',options:'Company'},{fieldname:'site',label:'Sede',fieldtype:'Link',options:'TruCMMS Site'},{fieldname:'equipment',label:'Equipo',fieldtype:'Link',options:'VB Equipment'},{fieldname:'plan',label:'Plan',fieldtype:'Link',options:'TruCMMS PM Plan'},{fieldname:'from_date',label:'Desde',fieldtype:'Date',default:today.slice(0,7)+'-01'},{fieldname:'to_date',label:'Hasta',fieldtype:'Date',default:new Date(Date.UTC(Number(today.slice(0,4)),Number(today.slice(5,7)),0)).toISOString().slice(0,10)}])fields[def.fieldname]=page.add_field({...def,change:()=>ready&&load()});
 function args(){return Object.fromEntries(Object.entries(fields).map(([k,v])=>[k,v.get_value()]).filter(([,v])=>v));}
 function button(row,parent){
  let label=row.order_status==='In Progress'?'En proceso':({Planned:'Programada',Released:'Orden abierta',Completed:'Validada',Skipped:'Omitida',Cancelled:'Cancelada'}[row.status]||row.status);
  if(row.overdue)label+=' · Vencida';if(row.plan_status==='Paused')label+=' · Plan pausado';if(row.plan_status==='Retired')label+=' · Plan retirado';if(row.on_time===false)label+=' · Fuera de plazo';
  const color=row.overdue?'#dc2626':{Planned:'#3b82f6',Released:'#f59e0b',Completed:'#16a34a',Skipped:'#94a3b8',Cancelled:'#ef4444'}[row.status];
  const b=$('<button type="button" class="pm-card"></button>').css('border-left-color',color).attr('data-occurrence',row.name).appendTo(parent);
  $('<strong></strong>').text(row.subject).appendTo(b);$('<div></div>').text(row.equipment+' · '+label).appendTo(b);
  if(String(row.original_due)!==String(row.planned_for))$('<small></small>').text('Vencimiento original: '+row.original_due).appendTo(b);
  b.on('click',()=>frappe.set_route('Form','TruCMMS PM Occurrence',row.name));
 }
 async function load(){
  const request=++seq;notice.text(__('Cargando programación…'));body.empty();
  try{const query=args();const responses=await Promise.all([frappe.call({method:'vanbags_maintenance.preventive.schedule',type:'GET',args:query}),frappe.call({method:'vanbags_maintenance.preventive.compliance',type:'GET',args:query})]);const message=responses[0].message,summary=responses[1].message;if(request!==seq)return;for(const row of message.rows)Object.assign(row,summary.by_occurrence[row.name]||{});
   const rows=message.rows,totals={};for(const row of rows)totals[row.status]=(totals[row.status]||0)+1;
   counts.text('Programadas: '+(totals.Planned||0)+' · Liberadas: '+(totals.Released||0)+' · Validadas: '+(totals.Completed||0)+' · Omitidas: '+(totals.Skipped||0)+' · Pendientes vencidas: '+summary.counts.overdue+' · Cumplimiento del período vencido: '+(summary.counts.completion_percent===null?'—':summary.counts.completion_percent+'%')+' · A tiempo: '+(summary.counts.on_time_percent===null?'—':summary.counts.on_time_percent+'%'));
   notice.text(message.truncated?'Se muestran 500 ocurrencias; reduce el período.':'Fechas locales de cada sede. Las programadas no son órdenes abiertas. Se muestran ocurrencias materializadas; el plan ofrece vista previa y horizonte configurables.');
   if(mode==='List'){
    const table=$('<table class="table"><thead><tr><th>Fecha prevista</th><th>Vencimiento original</th><th>Trabajo y estado</th></tr></thead><tbody></tbody></table>').appendTo($('<div class="pm-list"></div>').appendTo(body));
    for(const row of rows){const tr=$('<tr></tr>').appendTo(table.find('tbody'));$('<td></td>').text(row.planned_for).appendTo(tr);$('<td></td>').text(row.original_due).appendTo(tr);button(row,$('<td></td>').appendTo(tr));}
   }else{
    const grid=$('<div class="pm-grid"></div>').appendTo(body);for(const name of weekdays)$('<strong class="pm-weekday"></strong>').text(name).appendTo(grid);let day=message.from_date;const offset=(new Date(day+'T12:00:00Z').getUTCDay()+6)%7;for(let i=0;i<offset;i++)$('<div class="pm-day pm-empty"></div>').appendTo(grid);
    while(day<=message.to_date){const entries=rows.filter(r=>r.planned_for===day);const box=$('<section class="pm-day"></section>').toggleClass('pm-empty',!entries.length).appendTo(grid);$('<strong></strong>').text(weekdays[(new Date(day+'T12:00:00Z').getUTCDay()+6)%7]+' '+frappe.datetime.str_to_user(day)).appendTo(box);for(const row of entries)button(row,box);day=frappe.datetime.add_days(day,1);}
   }
  }catch(e){if(request===seq)notice.text(__('No se pudo cargar la programación. Comprueba el período y los permisos.'));}
 }
 async function month(offset){const value=new Date((fields.from_date.get_value()||today)+'T12:00:00Z');value.setUTCDate(1);value.setUTCMonth(value.getUTCMonth()+offset);const end=new Date(Date.UTC(value.getUTCFullYear(),value.getUTCMonth()+1,0));ready=false;await fields.from_date.set_value(value.toISOString().slice(0,10));await fields.to_date.set_value(end.toISOString().slice(0,10));ready=true;load();}
 page.add_inner_button(__('Mes anterior'),()=>month(-1));page.add_inner_button(__('Mes siguiente'),()=>month(1));
 page.add_inner_button(__('Calendario'),()=>{mode='Calendar';load();});page.add_inner_button(__('Lista'),()=>{mode='List';load();});page.add_inner_button(__('Actualizar'),load);
 wrapper.pm_schedule={load};ready=true;load();
};
