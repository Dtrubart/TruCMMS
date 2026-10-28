"""Versioned work-order origin, scheduling and acceptance contract."""
import json,hashlib,uuid
from functools import wraps
import frappe
from frappe.utils import get_datetime
from vanbags_maintenance import work_orders as wo,organization as org,teams
C_FIELDS=('lifecycle_policy','acceptance_policy_snapshot','acceptance_required','direct_key','direct_payload_hash','direct_reason','has_review_history','hold_from_state')
SCHEDULE=('scheduled_start','scheduled_end','target_closure')

def atomic(fn):
    @wraps(fn)
    def wrapped(*args,**kwargs):
        point='c_'+uuid.uuid4().hex
        frappe.db.savepoint(point)
        try:
            result=fn(*args,**kwargs)
        except Exception:
            try:frappe.db.rollback(save_point=point)
            except Exception:frappe.db.rollback()
            raise
        frappe.db.sql('RELEASE SAVEPOINT '+point)
        return result
    return wrapped


def context(doc):
    value=frappe.flags.get('trucmms_c_action')
    return value if value and value['name']==doc.name else None

def acceptance(doc):
    policy=frappe.db.get_value('TruCMMS Site',doc.site,'acceptance_policy') or 'By Origin'
    if policy not in ('By Origin','Required','Not Required'):frappe.throw('Invalid site acceptance policy.')
    doc.acceptance_policy_snapshot=policy
    doc.acceptance_required=int(policy=='Required' or policy=='By Origin' and doc.origin_type=='Maintenance Request')
    if doc.origin_type=='Maintenance Request':doc.acceptance_user=doc.requester

def initialize(doc):
    if doc.get('lifecycle_policy') not in (None,'','C1'):frappe.throw('New orders must use the current lifecycle policy.')
    doc.lifecycle_policy='C1';doc.has_review_history=0
    for prefix in ('verified','held','resumed','reopened'):
        for suffix in ('by','on','reason'):doc.set(prefix+'_'+suffix,None)
    doc.hold_from_state=None
    if doc.origin_type in ('Direct','Preventive','Inspection'):
        creation=frappe.flags.get('trucmms_direct_creation')
        if not creation:frappe.throw('Create direct orders through the authorized service.',frappe.PermissionError)
        doc.direct_key=creation['key'];doc.direct_payload_hash=creation['hash'];doc.direct_reason=creation['reason']
    elif doc.origin_type=='Maintenance Request':
        if any(doc.get(f) for f in ('direct_key','direct_payload_hash','direct_reason')):frappe.throw('Request orders cannot have a direct origin key.')
    else:frappe.throw('This origin provider is not implemented.')
    acceptance(doc)

def valid_acceptor(doc):
    if not doc.acceptance_required:return
    user=doc.acceptance_user
    if doc.origin_type=='Maintenance Request' and user and user==doc.requester:return  # Supervisor-on-behalf remains available if the original requester leaves.
    if not user or not frappe.db.get_value('User',user,'enabled') or 'TruCMMS Requester' not in frappe.get_roles(user) or not org.in_scope(doc,user):
        frappe.throw('Choose an enabled, scoped TruCMMS Requester to accept this work.')

def equal(a,b,field):
    if field.endswith(('_on','_start','_end')) or field=='target_closure':
        return get_datetime(a)==get_datetime(b) if a and b else not a and not b
    return a==b

def validate(doc,old):
    for field in SCHEDULE:
        value=doc.get(field)
        if value:
            try:value=get_datetime(value)
            except (ValueError,TypeError):frappe.throw('Enter a valid scheduling datetime.')
            if value.tzinfo is not None:frappe.throw('API scheduling dates must use the ERPNext system timezone without an offset suffix.')
            doc.set(field,value)
    if bool(doc.scheduled_start)!=bool(doc.scheduled_end):frappe.throw('Specify both scheduled start and end, or neither.')
    if doc.scheduled_start and doc.scheduled_end<=doc.scheduled_start:frappe.throw('Scheduled end must be after scheduled start.')
    if not old:return
    ctx=context(doc);allowed=set(ctx.get('allowed',())) if ctx else set()
    for field in C_FIELDS:
        if not equal(doc.get(field),old.get(field),field) and field not in allowed:frappe.throw('Work contract fields are server controlled.',frappe.PermissionError)
    if doc.acceptance_user!=old.acceptance_user and (old.status!='Draft' or doc.origin_type=='Maintenance Request') and 'acceptance_user' not in allowed:
        frappe.throw('The authorized acceptance identity is immutable.')
    for field in SCHEDULE:
        if old.status!='Draft' and not equal(doc.get(field),old.get(field),field) and field not in allowed:frappe.throw('Use controlled rescheduling after authorization.')
    if doc.lifecycle_policy=='C1' and old.status in ('Assigned','On Hold','Technical Completed','Verified','Accepted','Closed','Cancelled') and any(doc.get(f)!=old.get(f) for f in ('assigned_to','responsible_team','required_discipline')) and not ctx:frappe.throw('Use reasoned reassignment instead of editing the technician.')
    if doc.lifecycle_policy=='C1' and (old.status=='Draft' and doc.status=='Authorized' or old.status=='Authorized' and doc.status=='Assigned'):valid_acceptor(doc)

def validate_direct_context(doc):
    if not doc.equipment and not doc.functional_location:frappe.throw('Choose equipment or a functional location.')
    if doc.equipment:
        item=frappe.get_doc('VB Equipment',doc.equipment);item.check_permission('read')
        if (item.company,item.site)!=(doc.company,doc.site):frappe.throw('Equipment must belong to the order Company/Site.')
    if doc.functional_location:
        location=frappe.get_doc('VB Equipment Location',doc.functional_location);location.check_permission('read')
        if (location.company,location.site)!=(doc.company,doc.site):frappe.throw('Location must belong to the order Company/Site.')

@frappe.whitelist(methods=['POST'])
@atomic
def create_direct(company,site,subject,scope,priority,key,reason,equipment=None,functional_location=None,acceptance_user=None):
    return create_origin(company,site,subject,scope,priority,key,reason,equipment,functional_location,acceptance_user)


def create_origin(company,site,subject,scope,priority,key,reason,equipment=None,functional_location=None,acceptance_user=None,provider=None):
    if not (wo.supervisor() or wo.DISPATCHER in frappe.get_roles()):frappe.throw('Dispatcher or supervisor required.',frappe.PermissionError)
    if not (key or '').strip() or len(key)>100 or not (reason or '').strip():frappe.throw('A stable request key and direct-work reason are required.')
    payload={'company':company,'site':site,'subject':(subject or '').strip(),'scope':(scope or '').strip(),'priority':priority,'equipment':equipment or None,'functional_location':functional_location or None,'acceptance_user':acceptance_user or None,'reason':reason.strip()}
    origin=provider.get('origin') if provider else 'Direct'
    if origin not in ('Direct','Preventive','Inspection'):frappe.throw('Unsupported origin provider.')
    values={k:v for k,v in (provider or {}).items() if k!='origin'}
    doc=frappe.get_doc({'doctype':wo.DT,'origin_type':origin,**{k:v for k,v in payload.items() if k!='reason'},**values})
    org.validate_context(doc);validate_direct_context(doc)
    identity=('DIRECT' if origin=='Direct' else origin.upper())+'-'+hashlib.sha256(json.dumps([company,site,key.strip()]).encode()).hexdigest()
    if provider:payload['provider']=provider
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()
    teams.locked_sql('SELECT name FROM `tabTruCMMS Site` WHERE name=%s FOR UPDATE',(site,))
    rows=teams.locked_sql(f'SELECT name,direct_payload_hash FROM `tab{wo.DT}` WHERE direct_key=%s FOR UPDATE',(identity,),as_dict=True)
    if rows:
        existing=teams.locked_document(wo.DT,rows[0].name);existing.check_permission('read')
        if rows[0].direct_payload_hash!=digest:frappe.throw('This origin key already belongs to different input.')
        return existing.as_dict()
    previous=frappe.flags.get('trucmms_direct_creation');old_provider=frappe.flags.get('trucmms_origin_provider');frappe.flags.trucmms_direct_creation={'key':identity,'hash':digest,'reason':reason.strip()};frappe.flags.trucmms_origin_provider=provider
    try:doc.insert();return doc.as_dict()
    finally:frappe.flags.trucmms_direct_creation=previous;frappe.flags.trucmms_origin_provider=old_provider
