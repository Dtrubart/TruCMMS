frappe.pages["trucmms-work"].on_page_load=function(wrapper){
 const page=frappe.ui.make_app_page({parent:wrapper,title:__("TruCMMS Work Views"),single_column:true});
 const root=$('<div class="trucmms-work-views"></div>').appendTo(page.body);
 $('<style>').text(`
 .trucmms-work-views .work-toolbar{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
 .trucmms-work-views .work-row{border:1px solid var(--border-color);border-radius:8px;padding:12px;margin-bottom:8px;display:flex;gap:12px;align-items:center;justify-content:space-between}
 .trucmms-work-views .work-detail{min-width:0;flex:1;overflow-wrap:anywhere}
 .trucmms-work-views .work-muted{font-size:var(--text-sm);color:var(--text-muted)}
 .trucmms-work-views .work-days{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:3px}
 .trucmms-work-views .work-day{min-height:110px;min-width:0;border:1px solid var(--border-color);border-radius:4px;padding:4px;overflow:hidden}
 .trucmms-work-views .work-day a{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:var(--text-xs);padding:3px 0}
 .trucmms-work-views .work-empty{padding:20px;color:var(--text-muted)}
 @media(max-width:600px){.trucmms-work-views .work-row{display:block}.trucmms-work-views .work-row .btn{margin-top:8px;min-height:44px}.trucmms-work-views .work-day{min-height:90px}.trucmms-work-views .work-day .day-number{padding:4px;min-height:38px;min-width:34px}.trucmms-work-views .work-toolbar .btn{min-height:44px}}
 `).appendTo(root);
 const toolbar=$('<div class="work-toolbar" role="navigation" aria-label="Work views"></div>').appendTo(root);
 const note=$('<div class="work-note" role="status" aria-live="polite"></div>').appendTo(root);
 const content=$('<div class="work-content"></div>').appendTo(root);
 let ready=false,sequence=0,data=null,offset=0;
 const controls={};const modes=["List","My Work","Date Agenda","Calendar"];
 const today=frappe.datetime.get_today(),parts=today.split('-').map(Number),monthEnd=new Date(Date.UTC(parts[0],parts[1],0)).toISOString().slice(0,10);
 const refresh=()=>{if(ready)load();};
 for(const df of [
  {fieldname:"basis",label:__("Date Basis"),fieldtype:"Select",options:"All\nScheduled\nClosure Target\nWithout Schedule",default:"All"},
  {fieldname:"status",label:__("Status"),fieldtype:"Select",options:"Open\nAll\nDraft\nAuthorized\nAssigned\nOn Hold\nTechnical Completed\nVerified\nAccepted\nClosed\nCancelled",default:"Open"},
  {fieldname:"company",label:__("Company"),fieldtype:"Link",options:"Company"},
  {fieldname:"site",label:__("Site / Display Timezone"),fieldtype:"Link",options:"TruCMMS Site"},
  {fieldname:"equipment",label:__("Equipment"),fieldtype:"Link",options:"VB Equipment"},
  {fieldname:"from_date",label:__("From Date"),fieldtype:"Date",default:today.slice(0,7)+'-01'},
  {fieldname:"to_date",label:__("To Date"),fieldtype:"Date",default:monthEnd}
 ])controls[df.fieldname]=page.add_field({...df,change:refresh});
 let mode="List";
 const buttons={};for(const name of modes)buttons[name]=$('<button class="btn btn-default" type="button"></button>').text(__(name)).attr('data-view',name).appendTo(toolbar).on('click',async()=>{
  mode=name;offset=0;
  if(["Date Agenda","Calendar"].includes(mode)&&!["Scheduled","Closure Target"].includes(controls.basis.get_value())){ready=false;await controls.basis.set_value("Scheduled");ready=true;}
  load();
 });
 page.add_inner_button(__("Native List"),()=>frappe.set_route("List","TruCMMS Maintenance Work Order"));page.add_inner_button(__("Refresh"),refresh);
 function local(value){return value ? value.slice(0,16).replace('T',' ')+' '+value.slice(-6) : '—';}
 function rowCard(row,parent){
  const card=$('<article class="work-row"></article>').attr('data-work-order',row.name).appendTo(parent);const detail=$('<div class="work-detail"></div>').appendTo(card);
  $('<a></a>').attr('href','/desk/trucmms-maintenance-work-order/'+encodeURIComponent(row.name)).text(row.name+' — '+row.subject).appendTo(detail);
  $('<div class="work-muted"></div>').text([row.status,row.priority,row.equipment||row.functional_location||'',row.site].filter(Boolean).join(' · ')).appendTo(detail);
  $('<div class="work-muted"></div>').text(__("Scheduled")+': '+local(row.scheduled_start_local)+' → '+local(row.scheduled_end_local)).appendTo(detail);
  $('<div class="work-muted"></div>').text(__("Closure Target")+': '+local(row.target_closure_local)+(row.overdue ? ' · '+__("Overdue") : '')).appendTo(detail);
  if(row.execution_candidate)$('<button class="btn btn-primary btn-sm" type="button"></button>').text(__("Record Execution")).attr('data-execute',row.name).appendTo(card).on('click',()=>frappe.new_doc("TruCMMS Work Execution",{work_order:row.name,company:row.company,site:row.site}));
 }
 async function dayView(day,target="Date Agenda"){
  ready=false;await controls.from_date.set_value(day);await controls.to_date.set_value(day);ready=true;mode=target;offset=0;load();
 }
 function render(){
  content.empty();for(const name of modes)buttons[name].toggleClass('btn-primary',mode===name).attr('aria-pressed',String(mode===name));
  note.empty().append($('<p></p>').text(__("Display timezone")+': '+data.timezone+' · '+__("Date basis")+': '+__(data.basis)+' · '+data.rows.length+' '+__("visible orders")));
  if(data.truncated)note.append($('<div class="alert alert-warning"></div>').text(__("Only the first 500 authorized orders are shown. Narrow the filters; calendar and counts are incomplete.")));
  if(!data.rows.length && mode!=='Calendar'){content.append($('<p class="work-empty"></p>').text(mode==='My Work' ? __("No current assigned work matches these filters. My Work includes primary and additional technician allocations.") : __("No authorized work matches these filters.")));return;}
  if(["List","My Work"].includes(mode)){
   for(const row of data.rows.slice(offset,offset+50))rowCard(row,content);
   const nav=$('<div class="work-toolbar"></div>').appendTo(content);
   if(offset>0)$('<button class="btn btn-default"></button>').text(__("Previous")).appendTo(nav).on('click',()=>{offset-=50;render();});
   if(offset+50<data.rows.length)$('<button class="btn btn-default"></button>').text(__("Next")).appendTo(nav).on('click',()=>{offset+=50;render();});
  }else{
   const groups={};for(const row of data.rows)for(const day of row.local_days)(groups[day]||=[]).push(row);
   if(mode==='Date Agenda')for(const day of Object.keys(groups).sort()){
    $('<h4></h4>').text(day).appendTo(content);for(const row of groups[day].slice(0,50))rowCard(row,content);
    if(groups[day].length>50)$('<button class="btn btn-default"></button>').text(__("Show this day in List")).appendTo(content).on('click',()=>dayView(day,'List'));
   }else{
    const grid=$('<div class="work-days" aria-label="Calendar"></div>').appendTo(content);
    for(const day of ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'])$('<strong></strong>').text(__(day)).appendTo(grid);
    let current=new Date(data.from_date+'T12:00:00Z'),end=new Date(data.to_date+'T12:00:00Z');for(let i=0;i<current.getUTCDay();i++)$('<div></div>').appendTo(grid);
    while(current<=end){
     const day=current.toISOString().slice(0,10),cell=$('<div class="work-day"></div>').attr('data-day',day).appendTo(grid);
     $('<button class="btn btn-default btn-xs day-number"></button>').text(current.getUTCDate()).attr('aria-label',day+' '+__('agenda')).appendTo(cell).on('click',()=>dayView(day));
     for(const row of (groups[day]||[]).slice(0,3))$('<a></a>').text((data.basis==='Closure Target'?'◆ ':'')+row.name).attr({href:'/desk/trucmms-maintenance-work-order/'+encodeURIComponent(row.name),title:row.subject+' · '+row.status}).appendTo(cell);
     if((groups[day]||[]).length>3)$('<button class="btn btn-link btn-xs"></button>').text('+'+(groups[day].length-3)).appendTo(cell).on('click',()=>dayView(day));
     current.setUTCDate(current.getUTCDate()+1);
    }
   }
  }
 }
 async function load(){
  for(const key of ["from_date","to_date"])controls[key].$wrapper.toggle(["Scheduled","Closure Target"].includes(controls.basis.get_value()));
  const request=++sequence;offset=0;content.empty();note.text(__("Loading authorized work…"));
  const filters={mode};for(const [key,control] of Object.entries(controls))if(control.get_value())filters[key]=control.get_value();
  try{const result=await frappe.call({method:"vanbags_maintenance.work_views.get_work",type:"GET",args:{filters:JSON.stringify(filters)}});if(request!==sequence)return;data=result.message;render();}
  catch(error){if(request===sequence){note.text(__("Work could not be loaded. Check the connection and filters, then Refresh."));content.empty();}}
 }
 wrapper.trucmms_work={controls,load,get mode(){return mode;},async apply_options(options){ready=false;for(const key of ['company','site','equipment','status','basis','from_date','to_date'])if(options[key]!==undefined)await controls[key].set_value(options[key]);if(modes.includes(options.mode))mode=options.mode;if(['Date Agenda','Calendar'].includes(mode)&&!['Scheduled','Closure Target'].includes(controls.basis.get_value()))await controls.basis.set_value('Scheduled');ready=true;load();}};ready=true;load();
};

frappe.pages["trucmms-work"].on_page_show=function(wrapper){const options=frappe.route_options;if(options&&wrapper.trucmms_work){frappe.route_options=null;wrapper.trucmms_work.apply_options(options);}};
