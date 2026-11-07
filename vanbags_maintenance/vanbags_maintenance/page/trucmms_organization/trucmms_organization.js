frappe.pages['trucmms-organization'].on_page_load=function(wrapper){
 const page=frappe.ui.make_app_page({parent:wrapper,title:__('Estructura operativa'),single_column:true});
 const root=$('<div class="trucmms-organization"></div>').appendTo(page.body);
 $('<style>').text('.trucmms-organization .org-grid{display:grid;grid-template-columns:minmax(230px,1fr) minmax(280px,2fr);gap:24px;margin-top:20px}.trucmms-organization section{min-width:0;overflow-wrap:anywhere}.trucmms-organization .btn{min-height:44px;margin:4px}@media(max-width:700px){.trucmms-organization .org-grid{grid-template-columns:1fr}}').appendTo(root);
 const notice=$('<p role="status" aria-live="polite"></p>').appendTo(root),grid=$('<div class="org-grid"></div>').appendTo(root);
 const treePanel=$('<section></section>').appendTo(grid),detail=$('<section></section>').appendTo(grid);
 let ready=false,sequence=0,detailSequence=0;
 const company=page.add_field({fieldname:'company',label:__('Empresa'),fieldtype:'Link',options:'Company',change:()=>ready&&load()});
 const search=page.add_field({fieldname:'search',label:__('Buscar unidad'),fieldtype:'Data',change:()=>ready&&load()});
 function button(parent,label,action){return $('<button class="btn btn-default" type="button"></button>').text(__(label)).appendTo(parent).on('click',action);}
 async function show(name){
  const request=++detailSequence,context=sequence;detail.empty();
  const {message:doc}=await frappe.call({method:'vanbags_maintenance.operating_units.details',type:'GET',args:{name}});
  if(request!==detailSequence||context!==sequence)return;
  if(doc.company!==company.get_value()){notice.text(__('La unidad no pertenece a la empresa seleccionada.'));return;}
  const path=$('<nav aria-label="Organización"></nav>').appendTo(detail);
  doc.path.forEach((node,index)=>{if(index)$('<span></span>').text(' / ').appendTo(path);button(path,node.unit_name,()=>show(node.name));});
  $('<h3></h3>').text(doc.label).appendTo(detail);
  $('<p></p>').text([doc.company,doc.code,doc.unit_type,doc.disabled?__('Desactivada'):''].filter(Boolean).join(' · ')).appendTo(detail);
  button(detail,'Abrir ficha',()=>frappe.set_route('Form','TruCMMS Operating Unit',doc.name));
  if(doc.can_manage){
   button(detail,'Cambiar estructura operativa',()=>frappe.trucmms_organization_change(doc,'unit',async()=>{await load();show(doc.name);}));
   if(!doc.disabled)button(detail,'Crear unidad hija',()=>frappe.new_doc('TruCMMS Operating Unit',{company:doc.company,parent_unit:doc.name}));
   button(detail,'Historial administrativo de la empresa',()=>{frappe.route_options={company:doc.company};frappe.set_route('List','TruCMMS Organization Event');});
  }
  $('<h4></h4>').text(__('Sedes vinculadas directamente')).appendTo(detail);
  $('<p class="text-muted"></p>').text(__('Se muestran tus sedes autorizadas. La agrupación no concede acceso a otras sedes.')).appendTo(detail);
  for(const site of doc.sites)button(detail,site.site_name,()=>frappe.set_route('Form','TruCMMS Site',site.name));
  if(!doc.sites.length)$('<p></p>').text(__('No hay sedes vinculadas directamente que puedas consultar.')).appendTo(detail);
  if(doc.more_sites)button(detail,'Ver más sedes autorizadas',()=>{frappe.route_options={company:doc.company,operating_unit:doc.name};frappe.set_route('List','TruCMMS Site');});
 }
 async function load(){
  const request=++sequence;++detailSequence;treePanel.empty();detail.empty();
  if(!company.get_value()){notice.text(__('Selecciona una empresa. La agrupación de sedes es opcional.'));return;}
  const selected=company.get_value(),query=search.get_value().trim();notice.text(__('Cargando estructura…'));
  try{
   if(query){
    async function results(start=0){
     const {message:data}=await frappe.call({method:'vanbags_maintenance.operating_units.children',type:'GET',args:{company:selected,search:query,start}});
     if(request!==sequence)return;treePanel.empty();
     for(const row of data.rows)button(treePanel,row.unit_name,()=>show(row.name));
     if(start)button(treePanel,'Anterior',()=>results(Math.max(0,start-data.limit)));
     if(data.more)button(treePanel,'Siguiente',()=>results(start+data.limit));
     notice.text(data.rows.length?__('Resultados autorizados'):__('Sin resultados'));
    }
    await results();return;
   }
   const pages={},offsets={},pending={};let tree;
   class OrganizationTree extends frappe.ui.Tree{
    async get_nodes(value,is_root){const parent=is_root?'':value;if(pending[parent])return pending[parent];pending[parent]=this.fetch(parent);try{return await pending[parent];}finally{delete pending[parent];}}
    async fetch(parent){
     const {message:data}=await frappe.call({method:'vanbags_maintenance.operating_units.children',type:'GET',args:{company:selected,parent,start:offsets[parent]||0}});
     if(request!==sequence)return[];
     pages[parent]=[...(pages[parent]||[]),...data.rows.map(row=>({value:row.name,title:row.unit_name+(row.disabled?' · '+__('Desactivada'):''),expandable:1}))];
     return[...pages[parent],...(data.more?[{value:'__org_more__'+parent,title:__('Cargar más'),expandable:0,page_parent:parent,next:(offsets[parent]||0)+data.limit}]:[])];
    }
   }
   tree=new OrganizationTree({parent:treePanel,label:selected,root_value:'__org_root__',args:{doctype:'TruCMMS Operating Unit'},get_label:node=>frappe.utils.escape_html(node.title||node.label),expandable:true,with_skeleton:false,on_click(node){
    if(request!==sequence||node.is_root)return;
    if(Object.hasOwn(node.data,'page_parent')){offsets[node.data.page_parent]=node.data.next;tree.load_children(node.parent_node);return;}
    show(node.data.value);
   }});
   notice.text(__('Agrupación administrativa opcional. Conserva los permisos por empresa y sede.'));
  }catch(error){if(request===sequence)notice.text(__('No se pudo cargar la estructura. Revisa la empresa y tus permisos.'));}
 }
 page.add_inner_button(__('Actualizar'),load);
 if(frappe.model.can_create('TruCMMS Operating Unit'))page.add_inner_button(__('Nueva unidad raíz'),()=>{
  if(!company.get_value()){frappe.msgprint(__('Selecciona una empresa.'));return;}
  frappe.new_doc('TruCMMS Operating Unit',{company:company.get_value()});
 });
 wrapper.trucmms_organization={async applyOptions(){const values=frappe.route_options||{};frappe.route_options=null;ready=false;if(values.company)await company.set_value(values.company);ready=true;await load();if(values.unit)await show(values.unit);}};
 ready=true;
};
frappe.pages['trucmms-organization'].on_page_show=async function(wrapper){
 if(!frappe.route_options&&wrapper.trucmms_org_initialized)return;
 wrapper.trucmms_org_initialized=true;
 await wrapper.trucmms_organization.applyOptions();
};
