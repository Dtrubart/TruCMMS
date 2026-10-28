"""Chronological, retry-safe readings and auditable counter epochs/corrections."""
import hashlib,json
from decimal import Decimal
import frappe
from frappe.utils import now_datetime,get_datetime
from vanbags_maintenance import r2_records as r,organization as org,teams
from vanbags_maintenance.job_plans import finite
from vanbags_maintenance.work_contract import atomic
DT='TruCMMS Meter'
READING='TruCMMS Meter Reading'

def validate_meter(doc):
    if not frappe.flags.get('trucmms_r2_write'):r.editor(asset=True)
    old=doc.get_doc_before_save();internal=frappe.flags.get('trucmms_r2_write')
    if not doc.code or len(doc.code)>64 or not (doc.meter_name or '').strip():frappe.throw('Meter code (maximum 64 characters) and name are required.')
    if doc.component:
        component=frappe.get_doc('TruCMMS Component',doc.component);component.check_permission('read')
        if not component.equipment and not internal:frappe.throw('Install the component before configuring a meter.')
        if doc.is_new():doc.equipment=component.equipment
        if component.equipment!=doc.equipment:frappe.throw('Meter must follow its component equipment.')
    if doc.equipment:
        equipment=frappe.get_doc('VB Equipment',doc.equipment);equipment.check_permission('read')
        if doc.is_new():doc.company,doc.site=equipment.company,equipment.site
        if (doc.company,doc.site)!=(equipment.company,equipment.site):frappe.throw('Meter and equipment Company/Site must match.')
    elif not (internal and doc.disabled):frappe.throw('An operational meter needs installed equipment.')
    org.validate_context(doc)
    if doc.metric_kind not in ('Cumulative','Condition','Rate') or doc.direction not in ('Increasing','Decreasing','Variable'):frappe.throw('Invalid measurement semantics.')
    if doc.metric_kind=='Cumulative' and doc.direction!='Increasing':frappe.throw('Use Condition for decreasing wear measurements.')
    finite(doc.max_age_hours,'Maximum reading age',positive=True)
    if old and not internal:
        if any(doc.get(k)!=old.get(k) for k in ('code','company','site','equipment','component','unit','metric_kind','direction','epoch','epoch_offset','last_reading')):frappe.throw('Meter identity, units and history are permanent; use replacement/reset services.')
    if not old and not internal:
        if doc.last_reading or doc.epoch_offset or doc.epoch not in (None,0,1):frappe.throw('Meter history is server controlled.')
        doc.epoch=1;doc.epoch_offset=0

def meter(name,lock=True):
    doc=teams.locked_document(DT,name) if lock else frappe.get_doc(DT,name)
    doc.check_permission('read')
    if doc.disabled or not doc.equipment:frappe.throw('Choose an enabled, installed meter.')
    equipment=frappe.get_doc('VB Equipment',doc.equipment);equipment.check_permission('read')
    if (equipment.company,equipment.site)!=(doc.company,doc.site):frappe.throw('Reconcile meter scope after equipment movement.')
    if doc.component:
        component=frappe.get_doc('TruCMMS Component',doc.component);component.check_permission('read')
        if component.equipment!=doc.equipment:frappe.throw('Meter component is not installed on this equipment.')
    return doc

def timestamp(value):
    value=get_datetime(value) if value else now_datetime()
    if value.tzinfo is not None or value>now_datetime():frappe.throw('Reading time must be a non-future system-time datetime.')
    return value

def corrected(name):return bool(frappe.db.exists(READING,{'correction_of':name}))

def latest(doc,fresh=False):
    if not doc.last_reading:frappe.throw('Record a meter reading first.')
    reading=teams.locked_document(READING,doc.last_reading);reading.check_permission('read')
    if reading.epoch!=doc.epoch or corrected(reading.name):frappe.throw('Reconcile the current meter reading.')
    if fresh and (now_datetime()-get_datetime(reading.actual_on)).total_seconds()>float(doc.max_age_hours)*3600:frappe.throw('The latest reading is stale; record a fresh reading before unattended decisions.')
    return reading

def read_actor(doc):
    if not org.privileged() and not set(frappe.get_roles())&{'TruCMMS Technician','TruCMMS Supervisor','VB Maintenance Manager'}:frappe.throw('A scoped technician or maintenance manager must record readings.',frappe.PermissionError)

def _record(doc,value,actual_on,key,reason,correction_of=None,reset=False):
    value=finite(value,'Reading value');actual_on=timestamp(actual_on)
    if doc.metric_kind=='Cumulative' and value<0:frappe.throw('Cumulative raw readings cannot be negative.')
    key=(key or '').strip()
    if not key or len(key)>100:frappe.throw('A stable reading request key of at most 100 characters is required.')
    data={'meter':doc.name,'value':str(value),'actual_on':str(actual_on),'reason':reason or '', 'correction_of':correction_of}
    identity='MR-'+hashlib.sha256((frappe.session.user+'|'+doc.name+'|'+key).encode()).hexdigest()
    digest=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
    existing=teams.locked_sql(f'SELECT name,payload_hash FROM `tab{READING}` WHERE reading_key=%s FOR UPDATE',(identity,),as_dict=True)
    existing=existing[0] if existing else None
    if existing:
        if existing.payload_hash!=digest:frappe.throw('This reading key was already used with different contents.')
        result=teams.locked_document(READING,existing.name);result.check_permission('read');return result
    old=teams.locked_document(READING,doc.last_reading) if doc.last_reading else None
    if old and not reset:
        if correction_of:
            if old.name!=correction_of or corrected(old.name):frappe.throw('Only the latest uncorrected reading can be corrected.')
            if actual_on!=get_datetime(old.actual_on):frappe.throw('A correction retains the original measurement time.')
            previous=frappe.db.sql(f'SELECT name,value FROM `tab{READING}` a WHERE meter=%s AND epoch=%s AND name!=%s AND actual_on<%s AND NOT EXISTS (SELECT 1 FROM `tab{READING}` b WHERE b.correction_of=a.name) ORDER BY actual_on DESC,name DESC LIMIT 1',(doc.name,doc.epoch,old.name,actual_on),as_dict=True)
            if doc.metric_kind=='Cumulative' and previous and value<Decimal(str(previous[0].value)):frappe.throw('Correction would make the counter decrease within this epoch.')
        else:
            if actual_on<=get_datetime(old.actual_on):frappe.throw('Readings must be chronological; use the explicit correction action for the latest reading.')
            if doc.metric_kind=='Cumulative' and value<Decimal(str(old.value)):frappe.throw('Counter decreased; use an explicit reset/replacement with a reason.')
    context=old if correction_of else doc
    if context.component:
        placements=teams.locked_sql('SELECT name FROM `tabTruCMMS Component Installation` WHERE component=%s AND equipment=%s AND company=%s AND site=%s AND effective_from<=%s AND (effective_until IS NULL OR effective_until>%s) FOR UPDATE',(context.component,context.equipment,context.company,context.site,actual_on,actual_on))
        if not placements:frappe.throw('Reading time must belong to a recorded installation of this component on the measured equipment/site.')
    total=finite(value+Decimal(str(doc.epoch_offset or 0)) if doc.metric_kind=='Cumulative' else value,'Continuous reading')
    row=r.create(READING,reading_key=identity,meter=doc.name,company=context.company,site=context.site,equipment=context.equipment,component=context.component,value=float(value),total_value=float(total),actual_on=actual_on,epoch=doc.epoch,correction_of=correction_of,reason=reason,payload_hash=digest,recorded_by=frappe.session.user,recorded_on=now_datetime())
    doc.last_reading=row.name;r.save(doc)
    return row

@frappe.whitelist(methods=['POST'])
@atomic
def record(meter_name,value,actual_on,key,reason=None):
    doc=meter(meter_name);read_actor(doc)
    return _record(doc,value,actual_on,key,reason).as_dict()

@frappe.whitelist(methods=['POST'])
@atomic
def correct(reading,value,reason,key):
    r.editor(asset=True);reason=r.reason(reason)
    source=frappe.get_doc(READING,reading);source.check_permission('read');doc=meter(source.meter)
    result=_record(doc,value,source.actual_on,key,reason,correction_of=source.name)
    r.event(doc,'Correct Meter Reading',reason,original=source.name,replacement=result.name)
    return result.as_dict()

@frappe.whitelist(methods=['POST'])
@atomic
def reset(meter_name,initial_value,reason,key,actual_on=None):
    if not isinstance(key,str) or not key.strip() or len(key)>80:frappe.throw('A stable reset key of at most 80 characters is required.')
    r.editor(asset=True);reason=r.reason(reason);doc=meter(meter_name)
    epoch_key='ME-'+hashlib.sha256((doc.name+'|'+str(key)).encode()).hexdigest()
    existing=teams.locked_sql('SELECT name,initial_value,reason,effective_on FROM `tabTruCMMS Meter Epoch` WHERE epoch_key=%s FOR UPDATE',(epoch_key,),as_dict=True)
    existing=existing[0] if existing else None
    if existing:
        if Decimal(str(existing.initial_value))!=finite(initial_value,'Initial reading') or existing.reason!=reason:frappe.throw('Reset request key has conflicting contents.')
        if actual_on and get_datetime(existing.effective_on)!=timestamp(actual_on):frappe.throw('Reset request key belongs to a different effective time.')
        return {'name':existing.name,'meter':doc.name}
    old=latest(doc);when=timestamp(actual_on)
    if when<=get_datetime(old.actual_on):frappe.throw('Reset must follow the latest reading.')
    initial=finite(initial_value,'Initial reading')
    if doc.metric_kind=='Cumulative' and initial<0:frappe.throw('Initial cumulative reading cannot be negative.')
    old_epoch=doc.epoch;doc.epoch+=1
    doc.epoch_offset=float(Decimal(str(old.total_value))-initial) if doc.metric_kind=='Cumulative' else 0
    row=r.create('TruCMMS Meter Epoch',epoch_key=epoch_key,meter=doc.name,company=doc.company,site=doc.site,old_epoch=old_epoch,new_epoch=doc.epoch,initial_value=float(initial),continuity_offset=doc.epoch_offset,effective_on=when,reason=reason,recorded_by=frappe.session.user)
    _record(doc,initial,when,'reset-'+str(key),reason,reset=True)
    r.event(doc,'Reset/Replace Meter',reason,old_epoch=old_epoch,new_epoch=doc.epoch)
    return {'name':row.name,'meter':doc.name,'epoch':doc.epoch}

@frappe.whitelist(methods=['GET','POST'])
def readings(meter_name):
    doc=frappe.get_doc(DT,meter_name);doc.check_permission('read')
    rows=frappe.get_list(READING,filters={'meter':meter_name},fields=['name','value','total_value','actual_on','epoch','correction_of','reason','recorded_by'],order_by='actual_on desc,creation desc',limit_page_length=500)
    for row in rows:row['corrected']=corrected(row.name)
    return rows
