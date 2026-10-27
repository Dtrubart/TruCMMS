"""Task-oriented native navigation; visibility never replaces document permissions."""
import frappe
from vanbags_maintenance import organization as org,work_orders as wo
CMMS_ROLES={'VB Maintenance User','VB Maintenance Manager','TruCMMS Requester','TruCMMS Dispatcher','TruCMMS Supervisor','TruCMMS Technician','System Manager'}
GROUPS=[
 ('Operación',{'TruCMMS Requester','TruCMMS Dispatcher','TruCMMS Supervisor','TruCMMS Technician','System Manager'},[
  ('Solicitudes','DocType','TruCMMS Maintenance Request'),('Órdenes de trabajo','DocType',wo.DT),('Vistas de trabajo','Page','trucmms-work')]),
 ('Activos',{'VB Maintenance User','VB Maintenance Manager','TruCMMS Dispatcher','TruCMMS Supervisor','TruCMMS Technician','System Manager'},[
  ('Equipos físicos','DocType','VB Equipment'),('Ubicaciones funcionales','DocType','VB Equipment Location'),('Instalaciones y reemplazos','Report','TruCMMS Installation Register')]),
 ('Planes y rutinas',set(),[]),
 ('Recursos y servicios',{'TruCMMS Dispatcher','TruCMMS Supervisor','System Manager'},[
  ('Equipos de mantenimiento','DocType','TruCMMS Maintenance Team')]),
 ('Repuestos y costos',set(),[]),
 ('Análisis',{'VB Maintenance Manager','TruCMMS Dispatcher','TruCMMS Supervisor','System Manager'},[
  ('Registro de trabajo','Report','TruCMMS Work Register'),('Historial de equipos','Report','TruCMMS Equipment History')]),
 ('Configuración',{'VB Maintenance Manager','System Manager'},[
  ('Empresas','DocType','Company'),('Sedes','DocType','TruCMMS Site'),('Categorías de equipos','DocType','VB Equipment Category'),('Perfiles técnicos','DocType','TruCMMS Equipment Profile'),('Criticidad','DocType','TruCMMS Criticality'),('Disciplinas','DocType','TruCMMS Discipline')])]
CONTEXTUAL={'TruCMMS Team Membership','TruCMMS Team Site Authorization','TruCMMS Work Execution','TruCMMS Work Event','TruCMMS Work Cycle','TruCMMS Work Allocation','TruCMMS Team Assignment','TruCMMS Execution Adjustment'}
MANAGED={target for _,_,entries in GROUPS for _,_,target in entries}|CONTEXTUAL|{'TruCMMS','trucmms-start'}

LEGACY_LABELS={'TruCMMS': ['Home'], 'VB Equipment': ['Equipment'], 'VB Equipment Category': ['Equipment Categories'], 'VB Equipment Location': ['Functional Locations'], 'TruCMMS Site': ['Sites'], 'TruCMMS Maintenance Request': ['Maintenance Requests'], 'TruCMMS Maintenance Work Order': ['Maintenance Work Orders'], 'TruCMMS Work Execution': ['Work Execution'], 'TruCMMS Work Register': ['TruCMMS Work Register'], 'TruCMMS Equipment History': ['TruCMMS Equipment History'], 'TruCMMS Maintenance Team': ['Maintenance Team'], 'TruCMMS Discipline': ['Discipline'], 'TruCMMS Team Membership': ['Team Membership'], 'TruCMMS Team Site Authorization': ['Team Site Authorization'], 'TruCMMS Equipment Profile': ['TruCMMS Equipment Profile'], 'TruCMMS Criticality': ['TruCMMS Criticality'], 'TruCMMS Installation Register': ['TruCMMS Installation Register'], 'trucmms-work': ['Work Views']}

def is_managed(row):
    target=row.get('link_to');label=row.get('label')
    names=set(LEGACY_LABELS.get(target,[]))
    names.update(n for _,_,entries in GROUPS for n,_,t in entries if t==target)
    if target=='trucmms-start':names.add('Inicio')
    return target in MANAGED and label in names

def authorized(doctype,ptype='read'):
    return bool(frappe.has_permission(doctype,ptype))

def allowed_link(kind,target):
    if kind=='DocType':return authorized(target)
    if kind=='Report':
        doc=frappe.get_doc('Report',target)
        return not doc.disabled and authorized(doc.ref_doctype,'report')
    if kind=='Page':return authorized(wo.DT)
    return False

def groups():
    roles=set(frappe.get_roles());privileged=org.privileged()
    result=[]
    for label,allowed,entries in GROUPS:
        if not entries or not (privileged or roles&allowed):continue
        links=[{'label':label,'kind':kind,'target':target} for label,kind,target in entries if allowed_link(kind,target)]
        if links:result.append({'label':label,'links':links})
    return result

def sidebar_rows(visible_groups,extras=None):
    rows=[{'type':'Link','label':'Inicio','link_type':'Page','link_to':'trucmms-start','icon':'home','child':0}]
    for group in visible_groups:
        rows.append({'type':'Section Break','label':group['label'],'collapsible':1,'keep_closed':1,'child':0})
        rows.extend({'type':'Link','label':link['label'],'link_type':link['kind'],'link_to':link['target'],'child':1,'collapsible':0} for link in group['links'])
    if extras:
        rows.append({'type':'Section Break','label':'Accesos adicionales','collapsible':1,'keep_closed':1,'child':0})
        for item in extras:rows.append({**item,'child':1})
    return rows

def extend_bootinfo(bootinfo):
    sidebars=bootinfo.get('workspace_sidebar_item') or {};sidebar=sidebars.get('trucmms')
    if not sidebar:return
    roles=set(frappe.get_roles())
    if not org.privileged() and not roles&CMMS_ROLES:return
    extras=[dict(row) for row in sidebar.get('items',[]) if (row.get('link_to') or row.get('url')) and not is_managed(row)]
    sidebar['items']=sidebar_rows(groups(),extras)

def scope(company=None,site=None):
    if not org.privileged() and not set(frappe.get_roles())&CMMS_ROLES:frappe.throw('Maintenance access required.',frappe.PermissionError)
    if site:
        doc=frappe.get_doc('TruCMMS Site',site);doc.check_permission('read')
        if company and company!=doc.company:frappe.throw('Choose a Site belonging to the selected Company.')
        company=doc.company
    return {k:v for k,v in [('company',company),('site',site)] if v}

@frappe.whitelist(methods=['GET','POST'])
def home(company=None,site=None):
    filters=scope(company,site);roles=set(frappe.get_roles());actions=[];cards=[]
    def card(label,dt,extra=None):
        if not authorized(dt):return
        query={**filters,**(extra or {})};names=frappe.get_list(dt,filters=query,pluck='name',limit_page_length=501)
        cards.append({'label':label,'count':min(len(names),500),'truncated':len(names)>500,'doctype':dt,'filters':query})
    if authorized('TruCMMS Maintenance Request','create'):
        actions.append({'label':'Reportar una falla','action':'new','target':'TruCMMS Maintenance Request'})
    if 'TruCMMS Technician' in roles:
        actions.append({'label':'Mi trabajo','action':'view','target':'trucmms-work','options':{'mode':'My Work'}})
    if authorized(wo.DT):
        actions.append({'label':'Agenda de mantenimiento','action':'view','target':'trucmms-work','options':{'mode':'Date Agenda','basis':'Scheduled'}})
    if 'TruCMMS Requester' in roles:card('Mis solicitudes','TruCMMS Maintenance Request',{'owner':frappe.session.user})
    if 'TruCMMS Supervisor' in roles or org.privileged():
        card('Por autorizar',wo.DT,{'status':'Draft'});card('Por revisar',wo.DT,{'status':'Technical Completed'})
    card('Órdenes abiertas',wo.DT,{'status':['not in',['Closed','Cancelled']]})
    card('Equipos físicos','VB Equipment')
    return {'groups':groups(),'actions':actions,'cards':cards,'context':filters}

def save_navigation(doc):
    previous=(frappe.flags.get('in_import'),frappe.flags.get('in_patch'));frappe.flags.in_import=True;frappe.flags.in_patch=True
    try:doc.save(ignore_permissions=True)
    finally:frappe.flags.in_import,frappe.flags.in_patch=previous

def setup():
    from vanbags_maintenance import work_views,configuration
    work_views.setup(record=False)
    canonical=[{'label':label,'links':[{'label':n,'kind':kind,'target':target} for n,kind,target in entries]} for label,_,entries in GROUPS if entries]
    sidebar=frappe.get_doc('Workspace Sidebar','TruCMMS')
    extras=[{k:row.get(k) for k in ('type','label','link_type','link_to','url','filters','route_options')} for row in sidebar.items if (row.link_to or row.get('url')) and not is_managed(row)]
    sidebar.set('items',sidebar_rows(canonical,extras));save_navigation(sidebar)
    workspace=frappe.get_doc('Workspace','TruCMMS');workspace.type='Link';workspace.link_type='Page';workspace.link_to='trucmms-start'
    custom=[{k:row.get(k) for k in ('type','label','link_type','link_to')} for row in workspace.links if (row.link_to or row.get('url')) and not is_managed(row)]
    workspace.set('links',[{'type':'Link','label':'Inicio','link_type':'Page','link_to':'trucmms-start'}]+[{'type':'Link','label':n,'link_type':kind,'link_to':target} for _,_,entries in GROUPS for n,kind,target in entries]+custom)
    save_navigation(workspace);frappe.clear_cache();configuration.record_deployment()
