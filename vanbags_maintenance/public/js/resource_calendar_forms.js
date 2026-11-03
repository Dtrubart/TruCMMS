(function(){
 const calendar='TruCMMS Resource Calendar',assignment='TruCMMS Calendar Assignment',generation='TruCMMS Calendar Generation';
 for(const dt of [calendar,assignment])frappe.ui.form.on(dt,{
  setup(frm){frm.set_query('site',()=>({filters:{company:frm.doc.company,disabled:0}}));if(dt===assignment){frm.set_query('calendar',()=>({filters:{company:frm.doc.company,site:frm.doc.site,disabled:0}}));frm.set_query('technician',()=>({filters:{enabled:1}}));}},
  refresh(frm){
   if(dt===calendar){frm.set_intro(__('Los turnos usan la hora local de la sede. Indica si terminan al día siguiente. Una vez asignado, crea otro calendario para cambiar el patrón. Los feriados requieren permiso de lectura nativo de ERPNext.'));return;}
   frm.set_intro(__('Genera periodos de hasta 31 días. Detener futuras generaciones conserva las ventanas existentes. Para una excepción, deshabilita la ventana con motivo y crea un reemplazo explícito, o registra una ausencia.'));
   if(frm.is_new())return;
   for(const f of ['company','site','technician','calendar','from_date','to_date'])frm.set_df_property(f,'read_only',1);
   frm.add_custom_button(__('Ventanas de esta asignación'),()=>frappe.set_route('List','TruCMMS Resource Window',{calendar_assignment:frm.doc.name}),__('Calendario'));
   frm.add_custom_button(__('Historial de generación'),()=>frappe.set_route('List',generation,{assignment:frm.doc.name}),__('Calendario'));
   if(!frm.doc.disabled&&frappe.user.has_role(['System Manager','TruCMMS Supervisor']))frm.add_custom_button(__('Generar disponibilidad'),()=>{
    if(frm.is_dirty()){frappe.msgprint(__('Guarda los cambios antes de generar.'));return;}
    frappe.prompt([
     {fieldname:'from_date',label:__('Desde (inclusive)'),fieldtype:'Date',reqd:1,default:frm.doc.from_date},
     {fieldname:'to_date',label:__('Hasta (inclusive, máximo 31 días)'),fieldtype:'Date',reqd:1},
     {fieldname:'reason',label:__('Motivo'),fieldtype:'Small Text',reqd:1}
    ],async values=>{
     const r=await frappe.call({method:'vanbags_maintenance.resource_calendars.generate',type:'POST',args:{assignment:frm.doc.name,...values},freeze:true});
     frappe.msgprint({title:__('Disponibilidad generada'),message:__('Ventanas: {0}. {1}',[r.message.window_count,r.message.created?__('Se conservaron patrón, fechas y autor.'):__('Se devolvió la generación existente sin duplicar.')])});
    },__('Generar ventanas de trabajo'));
   },__('Calendario'));
  }
 });
 frappe.ui.form.on('TruCMMS Resource Window',{refresh(frm){if(frm.doc.calendar_generation){frm.set_df_property('starts_on','read_only',1);frm.set_df_property('ends_on','read_only',1);frm.set_intro(__('Ventana generada desde un calendario. Conserva sus fechas originales; para una excepción deshabilítala con motivo y crea el reemplazo. Las ausencias se registran por separado.'));}}});
})();
