"""Component identity and append-only, exclusive installation positions."""
import hashlib
import frappe
from frappe.utils import now_datetime,get_datetime
from vanbags_maintenance import r2_records as r,organization as org,teams
from vanbags_maintenance.work_contract import atomic

DT='TruCMMS Component'
INSTALL='TruCMMS Component Installation'

def validate_component(doc):
    r.editor(asset=True)
    old=doc.get_doc_before_save()
    if not doc.code or len(doc.code)>64 or not (doc.component_name or '').strip():frappe.throw('A component code of at most 64 characters and a name are required.')
    if old and not frappe.flags.get('trucmms_r2_write'):
        if any(doc.get(f)!=old.get(f) for f in ('code','company','site','equipment','position')):frappe.throw('Use controlled installation/removal; identity and Company are permanent.')
        if doc.disabled and doc.equipment:frappe.throw('Remove the component before retiring it.')
    if doc.equipment:
        equipment=frappe.get_doc('VB Equipment',doc.equipment);equipment.check_permission('read')
        if doc.is_new():doc.company,doc.site=equipment.company,equipment.site
        if (equipment.company,equipment.site)!=(doc.company,doc.site):frappe.throw('Component installation must match equipment Company/Site.')
        if not (doc.position or '').strip():frappe.throw('An installed component requires a position.')
    org.validate_context(doc)
    if doc.is_new() and doc.equipment:
        teams.locked_sql('SELECT name FROM `tabVB Equipment` WHERE name=%s FOR UPDATE',(doc.equipment,))
        if frappe.db.exists(INSTALL,{'active_key':slot(doc.equipment,doc.position)}):frappe.throw('This equipment position is already occupied.')

def slot(equipment,position):
    return hashlib.sha256((equipment+'|'+position.strip().upper()).encode()).hexdigest()

def install_record(doc,when,reason):
    teams.locked_sql('SELECT name FROM `tabVB Equipment` WHERE name=%s FOR UPDATE',(doc.equipment,))
    active=slot(doc.equipment,doc.position)
    if frappe.db.exists(INSTALL,{'active_key':active}):frappe.throw('This equipment position is already occupied.')
    return r.create(INSTALL,component=doc.name,company=doc.company,site=doc.site,equipment=doc.equipment,position=doc.position.strip().upper(),effective_from=when,active_key=active,reason=reason,recorded_by=frappe.session.user,recorded_on=now_datetime())

def initial_install(doc):
    install_record(doc,now_datetime(),'Initial declared component installation')

@frappe.whitelist(methods=['POST'])
@atomic
def place(component,equipment=None,position=None,reason=None,effective_on=None):
    r.editor(asset=True);reason=r.reason(reason)
    doc=teams.locked_document(DT,component);doc.check_permission('write')
    if doc.disabled:frappe.throw('A retired component cannot be installed.')
    when=get_datetime(effective_on) if effective_on else now_datetime()
    if when.tzinfo is not None or when>now_datetime():frappe.throw('Use a non-future system-time installation datetime.')
    # Existing plans retain their historical equipment; no automatic retargeting.
    if frappe.db.exists('TruCMMS PM Plan',{'component':doc.name,'status':'Active'}):frappe.throw('Pause or retire active component plans before moving the component.')
    if frappe.db.sql("SELECT w.name FROM `tabTruCMMS Maintenance Work Order` w INNER JOIN `tabTruCMMS PM Plan` p ON p.name=w.pm_plan WHERE p.component=%s AND w.status NOT IN ('Closed','Cancelled') LIMIT 1",(doc.name,)):frappe.throw('Resolve open component work before moving its installed target.')
    target=None
    if equipment:
        target=frappe.get_doc('VB Equipment',equipment);target.check_permission('read')
        if target.company!=doc.company:frappe.throw('Cross-company component transfer requires a separately governed process.')
        if not (position or '').strip():frappe.throw('An installation position is required.')
    if (doc.equipment or None,(doc.position or '').upper())==(equipment or None,(position or '').strip().upper() if equipment else ''):return doc.as_dict()
    for name in sorted({x for x in (doc.equipment,equipment) if x}):teams.locked_sql('SELECT name FROM `tabVB Equipment` WHERE name=%s FOR UPDATE',(name,))
    rows=teams.locked_sql(f'SELECT name,effective_from FROM `tab{INSTALL}` WHERE component=%s AND effective_until IS NULL FOR UPDATE',(doc.name,),as_dict=True)
    if len(rows)>1:frappe.throw('Reconcile overlapping component installations before moving.')
    if rows:
        if when<get_datetime(rows[0].effective_from):frappe.throw('Movement cannot precede the current installation.')
        current=frappe.get_doc(INSTALL,rows[0].name);current.effective_until=when;current.active_key=None;r.save(current)
    before={'equipment':doc.equipment,'position':doc.position,'site':doc.site}
    doc.equipment=equipment or None;doc.position=(position or '').strip().upper() if equipment else None
    if target:doc.site=target.site
    r.save(doc)
    if target:install_record(doc,when,reason)
    for name in frappe.get_all('TruCMMS Meter',filters={'component':doc.name},pluck='name'):
        meter=teams.locked_document('TruCMMS Meter',name)
        meter.equipment=equipment or None;meter.site=doc.site
        if not equipment:meter.disabled=1
        r.save(meter)
    r.event(doc,'Install Component' if equipment else 'Remove Component',reason,before=before,equipment=equipment,position=position)
    return doc.as_dict()

@frappe.whitelist(methods=['GET','POST'])
def history(component):
    doc=frappe.get_doc(DT,component);doc.check_permission('read')
    return frappe.get_list(INSTALL,filters={'component':component},fields=['name','equipment','position','effective_from','effective_until','company','site','reason'],order_by='effective_from,name',limit_page_length=500)

def before_equipment_transfer(doc,site,when):
    if site==doc.site:return
    if frappe.db.exists('TruCMMS PM Plan',{'equipment':doc.name,'status':'Active'}):frappe.throw('Pause or retire active preventive plans before transferring the equipment; plan scope is never silently retargeted.')
    rows=teams.locked_sql(f'SELECT i.name,i.effective_from FROM `tab{INSTALL}` i WHERE i.equipment=%s AND i.effective_until IS NULL FOR UPDATE',(doc.name,),as_dict=True)
    if any(get_datetime(x.effective_from)>when for x in rows):frappe.throw('Transfer cannot predate an installed component.')

def follow_equipment_transfer(doc,when,reason):
    for name in frappe.get_all(DT,filters={'equipment':doc.name},pluck='name'):
        component=teams.locked_document(DT,name);component.check_permission('read')
        for row in frappe.get_all(INSTALL,filters={'component':name,'effective_until':['is','not set']},pluck='name'):
            current=frappe.get_doc(INSTALL,row);current.effective_until=when;current.active_key=None;r.save(current)
        component.site=doc.site;r.save(component);install_record(component,when,reason)
        r.event(component,'Transfer Component With Equipment',reason,equipment=doc.name)
    for name in frappe.get_all('TruCMMS Meter',filters={'equipment':doc.name},pluck='name'):
        meter=teams.locked_document('TruCMMS Meter',name);meter.site=doc.site;r.save(meter)
        r.event(meter,'Transfer Meter With Equipment',reason,equipment=doc.name)
