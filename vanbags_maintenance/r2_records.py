"""Native R2 permission boundaries and controlled append-only records."""
from contextlib import contextmanager
import json
import frappe
from frappe.utils import now_datetime
from vanbags_maintenance import organization as org

READ_ROLES={'TruCMMS Dispatcher','TruCMMS Supervisor','TruCMMS Technician'}
ASSET_ROLES=READ_ROLES|{'VB Maintenance User','VB Maintenance Manager'}
MUTABLE={'TruCMMS PM Plan','TruCMMS Meter','TruCMMS Component'}
TYPES=('TruCMMS PM Plan','TruCMMS PM Occurrence','TruCMMS PM Event','TruCMMS Meter','TruCMMS Meter Reading','TruCMMS Meter Epoch','TruCMMS Component','TruCMMS Component Installation','TruCMMS Inspection Finding')

@contextmanager
def internal():
    old=frappe.flags.get('trucmms_r2_write');frappe.flags.trucmms_r2_write=True
    try:yield
    finally:frappe.flags.trucmms_r2_write=old

def create(dt,**values):
    with internal():return frappe.get_doc(dict(doctype=dt,**values)).insert(ignore_permissions=True)

def save(doc):
    with internal():doc.save(ignore_permissions=True)
    return doc

def asset_type(dt):return any(x in dt for x in ('Meter','Component'))

def role_allowed(dt,user=None):
    user=user or frappe.session.user;roles=set(frappe.get_roles(user))
    if org.privileged(user):return True
    if dt=='TruCMMS PM Event':return bool(roles&{'TruCMMS Dispatcher','TruCMMS Supervisor','VB Maintenance Manager'})
    return bool(roles&(ASSET_ROLES if asset_type(dt) else READ_ROLES))

def permission(doc,user=None,ptype=None):
    scoped=doc
    if doc.is_new() and doc.doctype in ('TruCMMS Meter','TruCMMS Component') and doc.equipment:
        target=frappe.db.get_value('VB Equipment',doc.equipment,['company','site'],as_dict=True)
        if target:scoped=frappe._dict(doctype=doc.doctype,**target)
    if not org.in_scope(scoped,user) or not role_allowed(doc.doctype,user):frappe.throw('R2 access requires an authorized Company/Site and role.',frappe.PermissionError)
    if doc.doctype=='TruCMMS PM Event':
        for field,dt in [('plan','TruCMMS PM Plan'),('finding','TruCMMS Inspection Finding')]:
            if doc.get(field) and not frappe.has_permission(dt,'read',doc=frappe.get_doc(dt,doc.get(field)),user=user):frappe.throw('Event access requires access to its planning/inspection parent.',frappe.PermissionError)
    if doc.doctype=='TruCMMS PM Plan' and doc.status=='Draft' and not org.privileged(user) and not set(frappe.get_roles(user))&{'TruCMMS Supervisor','TruCMMS Dispatcher'}:frappe.throw('Draft planning requires an editor.',frappe.PermissionError)
    return True

def query_for(dt,user=None):
    if not role_allowed(dt,user):return '1=0'
    result=org.query(dt,user) or '1=1'
    if dt=='TruCMMS PM Event' and not org.privileged(user) and not set(frappe.get_roles(user))&{'TruCMMS Supervisor','TruCMMS Dispatcher'}:result+=" AND COALESCE(`tabTruCMMS PM Event`.plan,'')='' AND COALESCE(`tabTruCMMS PM Event`.finding,'')=''"
    if dt=='TruCMMS PM Plan' and not org.privileged(user) and not set(frappe.get_roles(user))&{'TruCMMS Supervisor','TruCMMS Dispatcher'}:result+=f" AND `tab{dt}`.status!='Draft'"
    return result

def before_insert(doc):
    if doc.doctype not in MUTABLE and not frappe.flags.get('trucmms_r2_write'):frappe.throw('Use the controlled R2 service.',frappe.PermissionError)

def validate_doc(doc):
    if doc.doctype in MUTABLE:
        if doc.doctype=='TruCMMS PM Plan':
            from vanbags_maintenance.preventive import validate_plan
            validate_plan(doc)
        elif doc.doctype=='TruCMMS Meter':
            from vanbags_maintenance.meters import validate_meter
            validate_meter(doc)
        else:
            from vanbags_maintenance.components import validate_component
            validate_component(doc)
    elif not frappe.flags.get('trucmms_r2_write'):frappe.throw('Saved R2 records are controlled and cannot be edited directly.',frappe.PermissionError)

def after_insert(doc):
    if doc.doctype=='TruCMMS Component' and doc.equipment:
        from vanbags_maintenance.components import initial_install
        initial_install(doc)

def event(doc,action,reason,**details):
    reason=(reason or '').strip()
    if not reason:frappe.throw('A reason is required.')
    refs={k:doc.get(k) for k in ('plan','occurrence','meter','component','finding') if doc.get(k)}
    mapped={'TruCMMS PM Plan':'plan','TruCMMS PM Occurrence':'occurrence','TruCMMS Meter':'meter','TruCMMS Component':'component','TruCMMS Inspection Finding':'finding'}
    if doc.doctype in mapped:refs[mapped[doc.doctype]]=doc.name
    return create('TruCMMS PM Event',company=doc.company,site=doc.site,action=action,reason=reason,actor=frappe.session.user,recorded_on=now_datetime(),details=json.dumps(details,default=str,sort_keys=True),**refs)

def validate_share(doc,method=None):
    if doc.share_doctype in TYPES:frappe.throw('R2 visibility cannot be expanded through sharing.',frappe.PermissionError)

def editor(asset=False):
    roles={'TruCMMS Supervisor','VB Maintenance Manager'} if asset else {'TruCMMS Supervisor','TruCMMS Dispatcher'}
    if not org.privileged() and not set(frappe.get_roles())&roles:frappe.throw('Authorized maintenance editor required.',frappe.PermissionError)

def supervisor():
    if not org.privileged() and 'TruCMMS Supervisor' not in frappe.get_roles():frappe.throw('Supervisor required.',frappe.PermissionError)

def reason(value):
    value=(value or '').strip()
    if not value:frappe.throw('A reason is required.')
    return value

def setup():
    from vanbags_maintenance import job_plans
    from frappe.permissions import add_permission
    if not frappe.db.exists('Custom DocPerm',{'parent':'UOM','role':'VB Maintenance Manager','permlevel':0}):add_permission('UOM','VB Maintenance Manager',ptype='select')
    frappe.clear_cache(doctype='UOM')
    for dt,fields,name in [('TruCMMS PM Plan',['status','automation_enabled'],'pm_automation'),('TruCMMS PM Occurrence',['plan','status','sequence'],'pm_plan_sequence'),('TruCMMS PM Occurrence',['company','site','planned_for'],'pm_calendar_scope'),('TruCMMS Meter Reading',['meter','epoch','actual_on'],'meter_chronology'),('TruCMMS Meter Reading',['correction_of'],'meter_corrections'),('TruCMMS Component Installation',['component','effective_until'],'component_history'),('TruCMMS Inspection Finding',['work_order','status'],'inspection_review'),('TruCMMS Maintenance Work Order',['pm_plan','status'],'pm_work_slot')]:
        frappe.db.add_index(dt,fields,name)
    job_plans.setup()

# Explicit hook names avoid framework-version-dependent partial-function dispatch.
def plan_query(user=None):return query_for('TruCMMS PM Plan',user)
def occurrence_query(user=None):return query_for('TruCMMS PM Occurrence',user)
def event_query(user=None):return query_for('TruCMMS PM Event',user)
def meter_query(user=None):return query_for('TruCMMS Meter',user)
def reading_query(user=None):return query_for('TruCMMS Meter Reading',user)
def epoch_query(user=None):return query_for('TruCMMS Meter Epoch',user)
def component_query(user=None):return query_for('TruCMMS Component',user)
def installation_query(user=None):return query_for('TruCMMS Component Installation',user)
def finding_query(user=None):return query_for('TruCMMS Inspection Finding',user)
