(function(){
 const role=roles=>frappe.user.has_role(roles);
 const editor=()=>role(['TruCMMS Supervisor','TruCMMS Dispatcher','System Manager']);
 const supervisor=()=>role(['TruCMMS Supervisor','System Manager']);
 const assetEditor=()=>role(['TruCMMS Supervisor','VB Maintenance Manager','System Manager']);
 const why={fieldname:'reason',label:__('Motivo'),fieldtype:'Small Text',reqd:1};
 function action(frm,label,method,base,fields=[]){frm.add_custom_button(__(label),()=>{
  if(frm.is_dirty()){frappe.msgprint(__('Guarda los cambios antes de continuar.'));return;}
  const key=crypto.randomUUID();
  const run=values=>frappe.call({method:'vanbags_maintenance.'+method,type:'POST',args:{...base,...values,...(base.key==='AUTO'?{key}:{} )},freeze:true,callback:()=>frm.reload_doc()});
  if(fields.length)frappe.prompt(fields,run,__(label));else run({});
 });}
 function scope(frm){if(!frm.doc.equipment)return;frappe.db.get_doc('VB Equipment',frm.doc.equipment).then(e=>frm.set_value({company:e.company,site:e.site}));}
 frappe.ui.form.on('TruCMMS PM Plan',{
  setup(frm){frm.set_query('equipment',()=>({filters:{company:frm.doc.company,site:frm.doc.site}}));frm.set_query('procedure_revision',()=>({filters:{company:frm.doc.company,site:frm.doc.site,status:'Approved'}}));frm.set_query('component',()=>({filters:{equipment:frm.doc.equipment,disabled:0}}));},
  equipment:scope,
  refresh(frm){
   if(frm.is_new())return;
   if(frm.doc.status!=='Draft'){frm.disable_save();for(const field of frm.meta.fields)frm.set_df_property(field.fieldname,'read_only',1);}
   frm.add_custom_button(__('Ocurrencias'),()=>frappe.set_route('List','TruCMMS PM Occurrence',{plan:frm.doc.name}));
   frm.add_custom_button(__('Vista previa'),async()=>{const {message}=await frappe.call({method:'vanbags_maintenance.preventive.preview',args:{plan:frm.doc.name}});frappe.msgprint({title:__('Vista previa sin crear órdenes'),message:message.rows.map(r=>frappe.utils.escape_html(r.due+' · '+r.equipment)).join('<br>')||frappe.utils.escape_html(message.message||'Sin fechas previstas')});});
   if(supervisor()){
    if(frm.doc.status==='Draft')action(frm,'Activar plan','preventive.activate',{plan:frm.doc.name},[why,{fieldname:'baseline_reading',label:__('Lectura base inicial (opcional)'),fieldtype:'Link',options:'TruCMMS Meter Reading'}]);
    if(frm.doc.status==='Active')action(frm,'Pausar plan','preventive.disposition',{plan:frm.doc.name,action:'Pause'},[why]);
    if(frm.doc.status==='Paused')action(frm,'Reanudar plan','preventive.disposition',{plan:frm.doc.name,action:'Resume'},[why]);
    if(frm.doc.status!=='Retired')action(frm,'Retirar plan','preventive.disposition',{plan:frm.doc.name,action:'Retire'},[why]);
    if(frm.doc.status==='Active')action(frm,'Evaluar y liberar según política','preventive.run_plan',{plan:frm.doc.name},[why]);
    if(frm.doc.status==='Active'&&frm.doc.schedule_type==='Meter'&&frm.doc.trigger_kind!=='Usage')action(frm,'Renovar intervención por condición','preventive.renew_condition',{plan:frm.doc.name},[why]);
    if(frm.doc.schedule_type==='Meter'&&frm.doc.trigger_kind==='Usage')action(frm,'Declarar nueva base de uso','preventive.rebase',{plan:frm.doc.name},[{fieldname:'reading',label:__('Lectura base'),fieldtype:'Link',options:'TruCMMS Meter Reading',reqd:1},why]);
   }
   if(editor()&&frm.doc.status==='Active')action(frm,frm.doc.schedule_type==='Calendar'?'Materializar programación':'Evaluar disparador','preventive.materialize',{plan:frm.doc.name},frm.doc.schedule_type==='Calendar'?[{fieldname:'until',label:__('Hasta'),fieldtype:'Date',reqd:1}]:[]);
  }
 });
 frappe.ui.form.on('TruCMMS PM Occurrence',{refresh(frm){frm.disable_save();if(frm.is_new())return;
  if(frm.doc.work_order)frm.add_custom_button(__('Abrir orden'),()=>frappe.set_route('Form','TruCMMS Maintenance Work Order',frm.doc.work_order));
  if(editor()&&frm.doc.status==='Planned')action(frm,'Liberar orden','preventive.release',{occurrence_name:frm.doc.name},[why,...(supervisor()?[{fieldname:'override',label:__('Excepción autorizada a cupo/anticipación/precedencia'),fieldtype:'Check'}]:[])]);
  if(supervisor()&&frm.doc.status==='Planned'){
   for(const [label,value]of[['Omitir ocurrencia','Skip'],['Cancelar ocurrencia','Cancel']])action(frm,label,'preventive.change_occurrence',{occurrence_name:frm.doc.name,action:value},[why]);
   action(frm,'Aplazar ocurrencia','preventive.change_occurrence',{occurrence_name:frm.doc.name,action:'Postpone'},[{fieldname:'planned_for',label:__('Nueva fecha prevista'),fieldtype:'Date',reqd:1},why]);
  }
 }});
 frappe.ui.form.on('TruCMMS Meter',{equipment:scope,component(frm){if(frm.doc.component&&frm.is_new())frappe.db.get_doc('TruCMMS Component',frm.doc.component).then(c=>frm.set_value({equipment:c.equipment,company:c.company,site:c.site}));},refresh(frm){if(frm.is_new()){if(frm.doc.component&&!frm.doc.equipment)frappe.db.get_doc('TruCMMS Component',frm.doc.component).then(c=>frm.set_value({equipment:c.equipment,company:c.company,site:c.site}));else if(frm.doc.equipment&&!frm.doc.company)scope(frm);return;}
  for(const field of ['code','company','site','equipment','component','unit','metric_kind','direction'])frm.set_df_property(field,'read_only',1);
  frm.add_custom_button(__('Lecturas'),()=>frappe.set_route('List','TruCMMS Meter Reading',{meter:frm.doc.name}));
  if(!frm.doc.disabled&&role(['TruCMMS Technician','TruCMMS Supervisor','VB Maintenance Manager','System Manager']))action(frm,'Registrar lectura','meters.record',{meter_name:frm.doc.name,key:'AUTO'},[{fieldname:'value',label:__('Valor ('+frm.doc.unit+')'),fieldtype:'Data',reqd:1},{fieldname:'actual_on',label:__('Fecha de medición'),fieldtype:'Datetime',reqd:1},why]);
  if(assetEditor())action(frm,'Reinicio / reemplazo de medidor','meters.reset',{meter_name:frm.doc.name,key:'AUTO'},[{fieldname:'initial_value',label:__('Lectura inicial'),fieldtype:'Data',reqd:1},why]);
 }});
 frappe.ui.form.on('TruCMMS Meter Reading',{refresh(frm){frm.disable_save();if(!frm.is_new()&&assetEditor())action(frm,'Corregir última lectura','meters.correct',{reading:frm.doc.name,key:'AUTO'},[{fieldname:'value',label:__('Valor corregido'),fieldtype:'Data',reqd:1},why]);}});
 frappe.ui.form.on('TruCMMS Component',{equipment:scope,refresh(frm){if(frm.is_new())return;
  for(const field of ['code','company','site','equipment','position'])frm.set_df_property(field,'read_only',1);
  frm.add_custom_button(__('Historial de instalaciones'),()=>frappe.set_route('List','TruCMMS Component Installation',{component:frm.doc.name}));
  frm.add_custom_button(__('Medidores del componente'),()=>frappe.set_route('List','TruCMMS Meter',{component:frm.doc.name}));
  if(assetEditor())action(frm,'Instalar / mover / retirar','components.place',{component:frm.doc.name},[{fieldname:'equipment',label:__('Equipo destino (vacío para retirar)'),fieldtype:'Link',options:'VB Equipment'},{fieldname:'position',label:__('Posición destino'),fieldtype:'Data'},why]);
 }});
 frappe.ui.form.on('TruCMMS Inspection Finding',{refresh(frm){frm.disable_save();if(frm.is_new())return;
  if(frm.doc.followup_order)frm.add_custom_button(__('Orden de seguimiento'),()=>frappe.set_route('Form','TruCMMS Maintenance Work Order',frm.doc.followup_order));
  if(supervisor())action(frm,'Revisar hallazgo','inspections.review',{finding:frm.doc.name},[{fieldname:'disposition',label:__('Disposición'),fieldtype:'Select',options:'Action Required\nAccepted Deviation\nResolved',reqd:1},why]);
  if(editor()&&frm.doc.status==='Action Required'&&!frm.doc.followup_order)action(frm,'Generar seguimiento correctivo','inspections.followup',{finding:frm.doc.name},[why]);
 }});
 frappe.ui.form.on('TruCMMS Maintenance Work Order',{refresh(frm){
  if(frm.doc.pm_occurrence&&frm.doc.status==='Assigned'&&!frm.doc.pm_started_on&&role('TruCMMS Technician'))action(frm,'Iniciar trabajo preventivo','preventive.start_work',{work_order:frm.doc.name},[why]);
  if(frm.doc.pm_procedure_snapshot)frm.add_custom_button(__('Procedimiento y materiales'),()=>{const p=JSON.parse(frm.doc.pm_procedure_snapshot),esc=frappe.utils.escape_html;frappe.msgprint({title:__('Procedimiento conservado'),message:'<h4>'+esc(p.title||'')+'</h4><ul>'+p.tasks.map(t=>'<li>'+esc(t.task_code+': '+t.instructions)+'</li>').join('')+'</ul><h4>'+__('Materiales previstos')+'</h4><ul>'+(p.materials||[]).map(m=>'<li>'+esc(m.item+' · '+m.quantity+' '+m.uom)+'</li>').join('')+'</ul>'});});
  if(frm.doc.pm_occurrence)frm.add_custom_button(__('Ocurrencia de origen'),()=>frappe.set_route('Form','TruCMMS PM Occurrence',frm.doc.pm_occurrence));
 }});
 frappe.ui.form.on('TruCMMS Work Execution',{refresh(frm){
  if(!frm.is_new()){frm.set_df_property('pm_measurements','read_only',1);return;}
  if(!frm.doc.work_order||frm.pm_template_for===frm.doc.work_order)return;
  frm.pm_template_for=frm.doc.work_order;
  frappe.db.get_doc('TruCMMS Maintenance Work Order',frm.doc.work_order).then(order=>{
   if(!order.pm_procedure_snapshot)return;const spec=JSON.parse(order.pm_procedure_snapshot);
   if(!(frm.doc.tasks||[]).some(x=>x.task||x.findings)){frm.clear_table('tasks');for(const task of spec.tasks)frm.add_child('tasks',{procedure_task_code:task.task_code,task:task.instructions.slice(0,130),result:'Partial'});frm.refresh_field('tasks');}
   if(!(frm.doc.pm_measurements||[]).length){for(const metric of spec.measurements||[])frm.add_child('pm_measurements',{metric_key:metric.metric_key,metric_label:metric.metric_name,unit:metric.unit});frm.refresh_field('pm_measurements');}
  });
 }});
})();
