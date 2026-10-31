frappe.ui.form.on('TruCMMS Resource Window',{
 setup(frm){frm.set_query('site',()=>({filters:{company:frm.doc.company,disabled:0}}));frm.set_query('technician',()=>({filters:{enabled:1}}));},
 refresh(frm){frm.set_intro(__('Las fechas usan el control horario nativo de ERPNext. Define una ventana por turno; para turnos nocturnos, selecciona el día siguiente como fin. Una ausencia resta capacidad y no cambia permisos de asignación.'));if(!frm.is_new())for(const field of ['company','site','technician','kind'])frm.set_df_property(field,'read_only',1);}
});
