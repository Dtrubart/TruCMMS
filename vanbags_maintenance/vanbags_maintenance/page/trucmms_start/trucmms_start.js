frappe.pages["trucmms-start"].on_page_load=function(wrapper){
 const page=frappe.ui.make_app_page({parent:wrapper,title:"TruCMMS",single_column:true});
 const root=$('<div class="trucmms-home"></div>').appendTo(page.body);
 $('<style>').text('.trucmms-home .home-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px;margin:16px 0}.trucmms-home .home-card{border:1px solid var(--border-color);border-radius:10px;padding:18px;min-width:0;overflow-wrap:anywhere}.trucmms-home .home-actions{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}.trucmms-home .home-link{display:block;padding:9px 0}.trucmms-home .btn{min-height:44px}.trucmms-home .home-count{font-size:24px;font-weight:600}@media(max-width:480px){.trucmms-home .home-grid{grid-template-columns:1fr}}').appendTo(root);
 const notice=$('<div role="status" aria-live="polite"></div>').appendTo(root),actions=$('<div class="home-actions"></div>').appendTo(root),cards=$('<div class="home-grid"></div>').appendTo(root),groups=$('<div class="home-grid"></div>').appendTo(root);
 let ready=false,sequence=0;
 const company=page.add_field({fieldname:'company',label:__('Empresa'),fieldtype:'Link',options:'Company',change:()=>ready&&load()});
 const site=page.add_field({fieldname:'site',label:__('Sede'),fieldtype:'Link',options:'TruCMMS Site',change:()=>ready&&load()});
 function context(){return Object.fromEntries([['company',company.get_value()],['site',site.get_value()]].filter(([,v])=>v));}
 function open(kind,target,filters={}){frappe.route_options=filters;if(kind==='DocType')frappe.set_route('List',target);else if(kind==='Report')frappe.set_route('query-report',target);else frappe.set_route(target);}
 async function load(){
  const request=++sequence;notice.text(__('Cargando tus accesos…'));actions.empty();cards.empty();groups.empty();
  try{const {message}=await frappe.call({method:'vanbags_maintenance.navigation.home',type:'GET',args:context()});if(request!==sequence)return;notice.text(__('Accesos y pendientes según tu rol y autorización por empresa y sede.'));
   for(const item of message.actions)$('<button class="btn btn-primary" type="button"></button>').text(__(item.label)).attr('data-action',item.label).appendTo(actions).on('click',()=>{if(item.action==='new')frappe.new_doc(item.target,context());else open('Page',item.target,{...context(),...(item.options||{})});});
   for(const item of message.cards){const card=$('<button class="home-card btn btn-default text-left" type="button"></button>').attr('data-card',item.label).appendTo(cards);$('<div class="home-count"></div>').text(item.count+(item.truncated?'+':'')).appendTo(card);$('<div></div>').text(__(item.label)).appendTo(card);card.on('click',()=>open('DocType',item.doctype,item.filters));}
   for(const group of message.groups){const card=$('<section class="home-card"></section>').attr('data-category',group.label).appendTo(groups);$('<h4></h4>').text(__(group.label)).appendTo(card);for(const item of group.links)$('<a href="#" class="home-link"></a>').text(__(item.label)).appendTo(card).on('click',event=>{event.preventDefault();open(item.kind,item.target,context());});}
  }catch(error){if(request===sequence)notice.text(__('No se pudieron cargar los accesos. Revisa la conexión y actualiza.'));}
 }
 page.add_inner_button(__('Actualizar'),load);wrapper.trucmms_home={load};ready=true;load();
};
