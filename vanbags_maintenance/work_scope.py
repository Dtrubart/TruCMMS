"""R4.0 work scope, stable targets and readings over the existing R2 meter service."""
import hashlib,json,uuid
from contextlib import contextmanager
import frappe
from frappe.utils import now_datetime
from vanbags_maintenance import organization as org,work_orders as wo,teams,meters,r2_records as r2
from vanbags_maintenance.work_contract import atomic
POINT='TruCMMS Measurement Point'
TARGET='TruCMMS Work Target'
REVISION='TruCMMS Scope Revision'
READING='TruCMMS Work Reading'
KINDS={'Equipment','Component','Location','Measurement Point','Reference'}
SCOPE_FIELDS=('scope_policy','scope_location','scope_revision','scope_snapshot')

@contextmanager
def internal():
    old=frappe.flags.get('trucmms_scope_write');frappe.flags.trucmms_scope_write=True
    try:yield
    finally:frappe.flags.trucmms_scope_write=old


def point_permission(doc,user=None,ptype=None):
    if not org.in_scope(doc,user):frappe.throw('Measurement point requires Company/Site authorization.',frappe.PermissionError)
    return True


def point_query(user=None):return org.query(POINT,user)


def validate_point(doc):
    r2.editor(asset=True);org.validate_context(doc)
    location=frappe.get_doc('VB Equipment Location',doc.functional_location);location.check_permission('read')
    if (location.company,location.site)!=(doc.company,doc.site):frappe.throw('Measurement point and Location must share Company/Site.')
    doc.code=(doc.code or '').strip()
    if not doc.code or len(doc.code)>64 or not (doc.point_name or '').strip():frappe.throw('Point code and name required (code up to 64 characters).')
    old=doc.get_doc_before_save()
    if old and any(doc.get(k)!=old.get(k) for k in ('code','company','site','functional_location')):
        frappe.throw('Measurement point identity/location is permanent; disable it and create a replacement.')


def location(name,order):
    doc=frappe.get_doc('VB Equipment Location',name);doc.check_permission('read')
    if (doc.company,doc.site)!=(order.company,order.site):frappe.throw('Every work point must belong to this Company/Site.')
    return doc


def target(order,values):
    if not isinstance(values,dict) or set(values)-{'target_id','kind','equipment','component','functional_location','measurement_point','label'}:
        frappe.throw('Use supported work point fields.')
    kind=values.get('kind');snapshot={};equipment=component=point=None
    if kind not in KINDS:frappe.throw('Choose a supported work point type.')
    field={'Equipment':'equipment','Component':'component','Location':'functional_location','Measurement Point':'measurement_point'}.get(kind)
    if field and not values.get(field):frappe.throw('Choose the work point reference.')
    if kind=='Equipment':
        doc=frappe.get_doc('VB Equipment',values['equipment']);doc.check_permission('read');equipment=doc.name
        snapshot={k:doc.get(k) for k in ('name','equipment_code','asset_tag','equipment_name','company','site','location','manufacturer','model','serial_number')}
        label=doc.equipment_name
    elif kind=='Component':
        doc=frappe.get_doc('TruCMMS Component',values['component']);doc.check_permission('read')
        if not doc.equipment:frappe.throw('Choose an installed component.')
        equipment,component=doc.equipment,doc.name
        snapshot={k:doc.get(k) for k in ('name','code','component_name','equipment','position','serial_number','company','site')};label=doc.get('component_name') or doc.name
    elif kind=='Measurement Point':
        doc=frappe.get_doc(POINT,values['measurement_point']);doc.check_permission('read')
        if doc.disabled:frappe.throw('Choose an enabled measurement point.')
        point=doc.name;snapshot={k:doc.get(k) for k in ('name','code','point_name','company','site','functional_location')};label=doc.point_name
    elif kind=='Location':
        doc=location(values['functional_location'],order);label=doc.location_name;snapshot={'name':doc.name,'location_name':label}
    else:
        doc=None;label=(values.get('label') or '').strip()
        if not label:frappe.throw('Describe the reference point.')
    if doc and (doc.company,doc.site)!=(order.company,order.site):frappe.throw('Every work point must belong to this Company/Site.')
    here=values.get('functional_location') or (doc.get('functional_location') if point else None) or (snapshot.get('location') if kind=='Equipment' else None) or order.get('scope_location')
    if here:location(here,order)
    if kind=='Measurement Point' and here!=doc.functional_location:frappe.throw('Use the measurement point own Location.')
    return dict(target_id=values.get('target_id') or uuid.uuid4().hex,kind=kind,equipment=equipment,component=component,
        functional_location=here,measurement_point=point,label=(values.get('label') or label).strip(),context_snapshot=json.dumps(snapshot,sort_keys=True,default=str))


def fingerprint(rows):
    fields=('target_id','kind','equipment','component','functional_location','measurement_point','label','context_snapshot')
    return [[row.get(k) or None for k in fields] for row in rows]


def validate_order(doc,old):
    controlled=frappe.flags.get('trucmms_scope_write')
    if old:
        if any(doc.get(k)!=old.get(k) for k in SCOPE_FIELDS) or fingerprint(doc.get('work_targets',[]))!=fingerprint(old.get('work_targets',[])):
            if not controlled:frappe.throw('Use controlled work scope configuration; historical context cannot be edited directly.',frappe.PermissionError)
    else:
        if doc.get('scope_policy') not in (None,'','R4'):frappe.throw('New work uses the current scope contract.')
        if doc.get('work_targets') or doc.get('scope_revision') or doc.get('scope_snapshot') or doc.get('scope_location'):
            frappe.throw('Configure work scope through the controlled service.',frappe.PermissionError)
        doc.scope_policy='R4'
        here=doc.functional_location
        if not here and doc.equipment:here=frappe.db.get_value('VB Equipment',doc.equipment,'location')
        doc.scope_location=here
        if doc.equipment:doc.append('work_targets',target(doc,{'kind':'Equipment','equipment':doc.equipment}))
        elif here:doc.append('work_targets',target(doc,{'kind':'Location','functional_location':here}))
    if doc.scope_policy!='R4':return # Existing approved work retains its original contract.
    if controlled and old and old.status!='Draft':frappe.throw('Authorized scope is frozen; use a separate linked work order for additional work.')
    if doc.scope_location:location(doc.scope_location,doc)
    if doc.status!='Draft':
        if not doc.scope_location or not doc.work_targets:frappe.throw('Define the scope Location and work points before authorization.')
        if any(not row.functional_location for row in doc.work_targets):frappe.throw('Each work point needs a work Location before authorization.')
    if old and old.status=='Draft' and doc.status=='Authorized':
        # Freeze the exact reference readings without creating duplicate measurements.
        snapshots=[]
        for row in doc.work_targets:
            # A secondary point may have moved or been disabled since configuration.
            current=target(doc,{k:row.get(k) for k in ('target_id','kind','equipment','component','functional_location','measurement_point','label')})
            if current['equipment']!=row.equipment:
                frappe.throw('A component changed equipment; review the Draft work scope before authorization.')
            context=json.loads(current['context_snapshot'])
            filters={'disabled':0}
            if row.measurement_point:filters['measurement_point']=row.measurement_point
            elif row.component:filters['component']=row.component
            elif row.equipment:filters['equipment']=row.equipment
            else:
                snapshots.append({'target_id':row.target_id,'context':context,'reference_readings':[]});continue
            refs=frappe.get_list(meters.DT,filters=filters,fields=['name','unit','last_reading'],limit_page_length=101)
            if len(refs)>100:frappe.throw('Too many meters for this work point; use more specific targets.')
            readings=[]
            for ref in refs:
                if ref.last_reading:
                    value=frappe.get_doc(meters.READING,ref.last_reading);value.check_permission('read')
                    readings.append(dict(meter=ref.name,unit=ref.unit,reading=value.name,value=value.value,actual_on=str(value.actual_on)))
            snapshots.append({'target_id':row.target_id,'context':context,'reference_readings':readings})
        doc.scope_snapshot=json.dumps(snapshots,sort_keys=True,default=str)


@frappe.whitelist(methods=['POST'])
@atomic
def configure(order,scope_location,targets,reason,key):
    doc=teams.locked_document(wo.DT,order);doc.check_permission('write')
    if doc.status!='Draft':frappe.throw('Configure the work scope before authorization.')
    reason=r2.reason(reason)
    if not isinstance(key,str) or not 8<=len(key)<=100:frappe.throw('Provide a stable request key (8-100 characters).')
    targets=json.loads(targets) if isinstance(targets,str) else targets
    if not isinstance(targets,list) or not 1<=len(targets)<=100:frappe.throw('Choose between 1 and 100 work points.')
    digest=hashlib.sha256(json.dumps([scope_location,targets,reason],sort_keys=True).encode()).hexdigest()
    identity=hashlib.sha256(json.dumps([order,frappe.session.user,key]).encode()).hexdigest()
    previous=frappe.db.sql(f'SELECT name,payload_hash FROM `tab{REVISION}` WHERE request_key=%s FOR UPDATE',identity,as_dict=True)
    if previous:
        if previous[0].payload_hash!=digest or doc.scope_revision!=previous[0].name:frappe.throw('Scope request key is stale or belongs to different contents.')
        return {'name':doc.name,'revision':previous[0].name,'created':False}
    location(scope_location,doc);doc.scope_location=scope_location
    rows=[target(doc,row) for row in targets]
    ids=[row['target_id'] for row in rows]
    if len(set(ids))!=len(ids):frappe.throw('Work point identifiers must be distinct.')
    if any(not row['functional_location'] for row in rows):frappe.throw('Every work point needs a Location.')
    with internal():
        event=frappe.get_doc(dict(doctype=REVISION,work_order=order,company=doc.company,site=doc.site,request_key=identity,payload_hash=digest,
            reason=reason,recorded_by=frappe.session.user,recorded_on=now_datetime(),snapshot=json.dumps({'scope_location':scope_location,'targets':rows},sort_keys=True))).insert(ignore_permissions=True)
        doc.scope_policy='R4';doc.scope_revision=event.name;doc.set('work_targets',rows);doc.save()
    return {'name':order,'revision':event.name,'created':True}


def related_query(dt,user=None):
    condition=wo.query(user) or '1=1'
    field='parent' if dt==TARGET else 'work_order'
    return f'EXISTS (SELECT 1 FROM `tab{wo.DT}` WHERE `tab{wo.DT}`.name=`tab{dt}`.`{field}` AND ({condition}))'

def target_query(user=None):return related_query(TARGET,user)
def revision_query(user=None):return related_query(REVISION,user)
def reading_query(user=None):return related_query(READING,user)

def related_permission(doc,user=None,ptype=None):
    if not wo.can_read(frappe.get_doc(wo.DT,doc.work_order),user):frappe.throw('Work order access required.',frappe.PermissionError)
    if ptype in ('create','write','delete'):frappe.throw('Work history is immutable.',frappe.PermissionError)
    return True


@frappe.whitelist(methods=['POST'])
@atomic
def record_reading(order,target_id,meter,value,actual_on,key,reason):
    from vanbags_maintenance import allocations
    doc=teams.locked_document(wo.DT,order);doc.check_permission('read')
    if doc.status!='Assigned':frappe.throw('Record work readings during assigned execution.')
    if not wo.supervisor():allocations.execution_context(doc,frappe.session.user)
    point=next((row for row in doc.work_targets if row.target_id==target_id),None)
    if not point:frappe.throw('Choose a work point in this order.')
    measured=meters.meter(meter)
    if (measured.company,measured.site)!=(doc.company,doc.site):frappe.throw('Meter must belong to the work Company/Site.')
    matches=(measured.measurement_point==point.measurement_point if point.measurement_point else measured.component==point.component if point.component else measured.equipment==point.equipment if point.equipment else False)
    if not matches:frappe.throw('Meter must belong to the selected work point.')
    result=meters.record(meter,value,actual_on,key,r2.reason(reason))
    existing=frappe.db.sql(f'SELECT name,work_order,target_id FROM `tab{READING}` WHERE meter_reading=%s FOR UPDATE',result['name'],as_dict=True)
    if existing:
        if (existing[0].work_order,existing[0].target_id)!=(order,target_id):frappe.throw('This reading is already attributed to another work point.')
        return {'name':existing[0].name,'reading':result['name'],'created':False}
    with internal():
        link=frappe.get_doc(dict(doctype=READING,work_order=order,company=doc.company,site=doc.site,target_id=target_id,
            meter=meter,meter_reading=result['name'],recorded_by=frappe.session.user,recorded_on=now_datetime())).insert(ignore_permissions=True)
    return {'name':link.name,'reading':result['name'],'created':True}


@frappe.whitelist(methods=['GET'])
def overview(order):
    doc=frappe.get_doc(wo.DT,order);doc.check_permission('read')
    linked=frappe.get_list(READING,filters={'work_order':order},fields=['name','target_id','meter','meter_reading','recorded_by','recorded_on'],limit_page_length=501)
    if len(linked)>500:frappe.throw('More than 500 readings; consult the meter history or a narrower work order.')
    for row in linked:
        value=frappe.db.get_value(meters.READING,row.meter_reading,['meter','value','actual_on'],as_dict=True)
        if not value or value.meter!=row.meter:frappe.throw('Work reading provenance needs administrative reconciliation.')
        row.update(value);row.unit=frappe.db.get_value(meters.DT,row.meter,'unit');row.corrected=meters.corrected(row.meter_reading)
    return dict(order=order,policy=doc.scope_policy or 'Legacy',scope_location=doc.scope_location,
        targets=[row.as_dict() for row in doc.work_targets],authorization_snapshot=json.loads(doc.scope_snapshot or '[]'),readings=linked)


def validate_share(doc,method=None):
    if doc.share_doctype in (POINT,REVISION,READING):frappe.throw('Work point access cannot be expanded through sharing.',frappe.PermissionError)


def setup():
    from vanbags_maintenance import capacity
    capacity.setup()
    frappe.db.add_index(READING,['work_order','target_id'],'work_point_readings')
