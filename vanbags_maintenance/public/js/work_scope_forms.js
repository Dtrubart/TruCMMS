(function(){
 const esc=v=>frappe.utils.escape_html(String(v??''));
 const api=(method,args)=>frappe.call({method:'vanbags_maintenance.work_scope.'+method,type:method==='overview'?'GET':'POST',args,freeze:true});
 const fields=['target_id','kind','equipment','component','functional_location','measurement_point','label'];
 frappe.ui.form.on('TruCMMS Measurement Point',{
  setup(frm){frm.set_query('functional_location',()=>({filters:{company:frm.doc.company,site:frm.doc.site}}));frm.set_query('site',()=>({filters:{company:frm.doc.company}}));},
  refresh(frm){if(!frm.is_new())for(const field of ['code','company','site','functional_location'])frm.set_df_property(field,'read_only',1);}
 });
 frappe.ui.form.on('TruCMMS Meter',{
  setup(frm){frm.set_query('measurement_point',()=>({filters:{company:frm.doc.company,site:frm.doc.site,disabled:0}}));},
  measurement_point(frm){if(frm.is_new()&&frm.doc.measurement_point)frappe.db.get_doc('TruCMMS Measurement Point',frm.doc.measurement_point).then(p=>frm.set_value({company:p.company,site:p.site,equipment:null,component:null}));},
  refresh(frm){if(!frm.is_new())frm.set_df_property('measurement_point','read_only',1);}
 });
 frappe.ui.form.on('TruCMMS Maintenance Work Order',{
  refresh(frm){
   if(frm.is_new())return;
   if(frm.doc.status==='Draft'&&frappe.user.has_role(['System Manager','TruCMMS Supervisor','TruCMMS Dispatcher'])){
    frm.add_custom_button(__('Configurar alcance'),()=>{
     const key=crypto.randomUUID();
     frappe.prompt([
      {fieldname:'scope_location',label:__('Ubicación de alcance'),fieldtype:'Link',options:'VB Equipment Location',reqd:1,default:frm.doc.scope_location||frm.doc.functional_location,get_query:()=>({filters:{company:frm.doc.company,site:frm.doc.site}})},
      {fieldname:'reason',label:__('Motivo de esta revisión'),fieldtype:'Small Text',reqd:1},
      {fieldname:'targets',label:__('Puntos de trabajo'),fieldtype:'Table',reqd:1,in_place_edit:true,
       fields:[
        {fieldname:'target_id',fieldtype:'Data',hidden:1},
        {fieldname:'kind',label:__('Tipo'),fieldtype:'Select',options:'Equipment\nComponent\nLocation\nMeasurement Point\nReference',default:'Equipment',reqd:1,in_list_view:1},
        {fieldname:'label',label:__('Nombre en el recorrido'),fieldtype:'Data',in_list_view:1},
        {fieldname:'equipment',label:__('Equipo'),fieldtype:'Link',options:'VB Equipment',in_list_view:1,get_query:()=>({filters:{company:frm.doc.company,site:frm.doc.site}})},
        {fieldname:'component',label:__('Componente'),fieldtype:'Link',options:'TruCMMS Component',get_query:()=>({filters:{company:frm.doc.company,site:frm.doc.site}})},
        {fieldname:'functional_location',label:__('Ubicación del punto'),fieldtype:'Link',options:'VB Equipment Location',get_query:()=>({filters:{company:frm.doc.company,site:frm.doc.site}})},
        {fieldname:'measurement_point',label:__('Punto de medición'),fieldtype:'Link',options:'TruCMMS Measurement Point',get_query:()=>({filters:{company:frm.doc.company,site:frm.doc.site,disabled:0}})}
       ],data:(frm.doc.work_targets||[]).map(row=>Object.fromEntries(fields.map(k=>[k,row[k]])))}
     ],async values=>{
      const targets=values.targets.map(row=>Object.fromEntries(fields.filter(k=>row[k]).map(k=>[k,row[k]])));
      await api('configure',{order:frm.doc.name,scope_location:values.scope_location,targets:JSON.stringify(targets),reason:values.reason,key});await frm.reload_doc();
     },__('Configurar puntos antes de autorizar'));
    },__('Alcance'));
   }
   frm.add_custom_button(__('Contexto y lecturas de referencia'),async()=>{
    const {message:data}=await api('overview',{order:frm.doc.name});
    let html='<p>'+esc(data.policy)+' · '+esc(data.scope_location||__('Ubicación pendiente de revisión'))+'</p>';
    for(const point of data.targets){
     html+='<h5>'+esc(point.label)+' · '+esc(point.kind)+'</h5><p>'+esc(point.functional_location||'')+'</p>';
     const snapshot=data.authorization_snapshot.find(x=>x.target_id===point.target_id);
     if(snapshot)for(const reading of snapshot.reference_readings)html+='<p>'+esc(reading.meter)+': '+esc(reading.value)+' '+esc(reading.unit)+' · '+esc(reading.actual_on)+'</p>';
    }
    if(data.readings.length){html+='<h4>'+__('Lecturas registradas en este trabajo')+'</h4>';for(const row of data.readings)html+='<p>'+esc(row.meter)+': '+esc(row.value)+' '+esc(row.unit)+' · '+esc(row.actual_on)+(row.corrected?' · '+__('Corregida posteriormente; revisar historial'):'')+'</p>';}
    if(!data.targets.length)html+='<p>'+__('Esta orden conserva el contrato anterior; sus datos históricos no se han reinterpretado.')+'</p>';
    frappe.msgprint({title:__('Alcance conservado de la orden'),message:html});
   },__('Alcance'));
   if(frm.doc.status==='Assigned'&&(frm.doc.work_targets||[]).length&&frappe.user.has_role(['System Manager','TruCMMS Supervisor','TruCMMS Technician'])){
    frm.add_custom_button(__('Registrar lectura de la orden'),()=>{
     const points=frm.doc.work_targets.filter(row=>row.equipment||row.component||row.measurement_point);
     if(!points.length){frappe.msgprint(__('Esta orden no contiene puntos con medidores vinculables.'));return;}
     const names=points.map((p,i)=>(i+1)+'. '+p.label),key=crypto.randomUUID();
     const dialog=new frappe.ui.Dialog({title:__('Lectura del punto de trabajo'),fields:[
      {fieldname:'point',label:__('Punto'),fieldtype:'Select',options:names.join('\n'),reqd:1,default:names[0],onchange:()=>dialog.set_value('meter',null)},
      {fieldname:'meter',label:__('Medidor'),fieldtype:'Link',options:'TruCMMS Meter',reqd:1,onchange:async()=>{
       const name=dialog.get_value('meter');
       if(!name){dialog.set_value('meter_context','');return;}
       const measured=await frappe.db.get_doc('TruCMMS Meter',name);
       if(dialog.get_value('meter')===name)dialog.set_value('meter_context',[measured.unit,measured.metric_kind,measured.direction].join(' · '));
      },get_query:()=>{
       const point=points[names.indexOf(dialog.get_value('point'))];const filters={company:frm.doc.company,site:frm.doc.site,disabled:0};
       if(point?.measurement_point)filters.measurement_point=point.measurement_point;else if(point?.component)filters.component=point.component;else if(point?.equipment)filters.equipment=point.equipment;
       return {filters};
      }},
      {fieldname:'meter_context',label:__('Unidad y tipo de medición'),fieldtype:'Data',read_only:1},
      {fieldname:'value',label:__('Valor en la unidad del medidor'),fieldtype:'Data',reqd:1},
      {fieldname:'actual_on',label:__('Fecha de medición'),fieldtype:'Datetime',reqd:1},
      {fieldname:'reason',label:__('Observación / motivo'),fieldtype:'Small Text',reqd:1}
     ],primary_action_label:__('Registrar'),async primary_action(values){
      const point=points[names.indexOf(values.point)];
      await api('record_reading',{order:frm.doc.name,target_id:point.target_id,meter:values.meter,value:values.value,actual_on:values.actual_on,reason:values.reason,key});
      dialog.hide();frappe.show_alert({message:__('Lectura registrada una vez en el medidor y vinculada a la orden.'),indicator:'green'});
     }});dialog.show();
    },__('Alcance'));
   }
  }
 });
})();
