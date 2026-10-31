"""R3 standard handoff: frozen PM demand -> native draft Material Requests.

Forecast demand is gross, not a stock reservation or net purchasing recommendation.
Native procurement/warehouse workflows remain responsible for approval and posting.
"""
from contextlib import contextmanager
from decimal import Decimal
import hashlib
import json
import uuid

import frappe
from frappe.utils import getdate, nowdate
from vanbags_maintenance import logistics, organization as org, teams, work_orders as wo, job_plans
from vanbags_maintenance.work_contract import atomic

ORIGIN = 'TruCMMS'
HEADER = ('trucmms_origin','trucmms_site','trucmms_work_order','trucmms_request_key','trucmms_payload_hash','trucmms_reason')
LINE = ('trucmms_source_key','trucmms_occurrence')


@contextmanager
def internal():
    old = frappe.flags.get('trucmms_material_request')
    frappe.flags.trucmms_material_request = True
    try: yield
    finally: frappe.flags.trucmms_material_request = old


def scope(company, site):
    doc = frappe.get_doc('TruCMMS Site', site)
    if doc.company != company or doc.disabled:
        frappe.throw('Choose an enabled Site belonging to the Company.')
    if not org.in_scope(doc):
        frappe.throw('Company and Site authorization required.', frappe.PermissionError)
    return doc


def warehouse_for(company, site, warehouse):
    scope(company, site)
    doc = frappe.get_doc('Warehouse', warehouse)
    doc.check_permission('read')
    if doc.company != company or doc.disabled or doc.is_group:
        frappe.throw('Choose an enabled non-group Warehouse in the Company.')
    if not frappe.db.exists(logistics.DT, {'company':company,'site':site,'warehouse':warehouse,'disabled':0}):
        frappe.throw('Warehouse must be authorized for this maintenance Site.')
    return doc


def stock_materials(snapshot):
    data = json.loads(snapshot or '{}')
    result = {}
    for row in data.get('materials', []):
        key = (row['item'], row['stock_uom'])
        result[key] = result.get(key, Decimal(0)) + job_plans.finite(row['stock_quantity'], 'Stock quantity', positive=True)
    return result


def source_key(occurrence, item, unit):
    return hashlib.sha256(json.dumps([occurrence,item,unit],separators=(',',':')).encode()).hexdigest()


def purchase_lines(keys):
    if not keys: return {}
    # Current locking read also protects repeat requests under REPEATABLE READ.
    rows = frappe.db.sql('''SELECT s.source_key, s.parent FROM `tabTruCMMS Material Source` s
        INNER JOIN `tabMaterial Request` p ON p.name=s.parent
        WHERE s.active_key IN %(keys)s AND p.docstatus<2 FOR UPDATE''', {'keys':tuple(keys)}, as_dict=True)
    return {row.source_key:row for row in rows}


@frappe.whitelist(methods=['GET'])
def forecast(company, site, from_date, to_date):
    logistics.reader()
    scope(company,site)
    start,end = getdate(from_date),getdate(to_date)
    if end < start or (end-start).days > 365:
        frappe.throw('Choose a forecast period of at most 366 days.')
    rows = frappe.get_list('TruCMMS PM Occurrence', filters={'company':company,'site':site,
        'planned_for':['between',[start,end]],'status':['in',['Planned','Released']]},
        fields=['name','plan','status','planned_for','work_order','equipment','procedure_snapshot'],
        order_by='planned_for,name', limit_page_length=301)
    if len(rows)>300: frappe.throw('Forecast exceeds 300 occurrences; use a shorter period.')
    details=[]
    for row in rows:
        snapshot=row.procedure_snapshot
        if row.work_order:
            order=frappe.get_doc(wo.DT,row.work_order)
            order.check_permission('read')
            if order.status in ('Closed','Cancelled'):continue
            snapshot=order.pm_procedure_snapshot
        elif frappe.db.get_value('TruCMMS PM Plan',row.plan,'status')!='Active':continue
        for (item,unit),quantity in stock_materials(snapshot).items():
            details.append(dict(key=source_key(row.name,item,unit),occurrence=row.name,plan=row.plan,
                work_order=row.work_order,equipment=row.equipment,needed_on=str(row.planned_for),
                item=item,stock_uom=unit,quantity=float(quantity)))
    from vanbags_maintenance.resource_planning import forecast_rows
    details.extend(forecast_rows(company,site,start,end))
    if len(details)>1000:frappe.throw('Forecast exceeds 1000 material lines; use a shorter period.')
    # Read endpoints must not take write locks. This view is advisory; creation
    # repeats the source/duplicate checks under the Site lock.
    keys=[r['key'] for r in details]
    requested={}
    if keys:
        requested={r.source_key:r for r in frappe.db.sql('''SELECT s.source_key,s.parent,
            (SELECT COALESCE(SUM(i.stock_qty),0) FROM `tabMaterial Request Item` i
             WHERE i.parent=s.parent AND i.item_code=s.item AND i.stock_uom=s.stock_uom)
            * s.quantity / NULLIF((SELECT SUM(t.quantity) FROM `tabTruCMMS Material Source` t
             WHERE t.parent=s.parent AND t.item=s.item AND t.stock_uom=s.stock_uom),0) AS stock_qty
            FROM `tabTruCMMS Material Source` s INNER JOIN `tabMaterial Request` p ON p.name=s.parent
            WHERE s.active_key IN %(keys)s AND p.docstatus<2''',{'keys':tuple(keys)},as_dict=True)}
    totals={}
    for row in details:
        existing=requested.get(row['key'])
        row['already_requested']=float(existing.stock_qty) if existing else 0
        row['covered']=bool(existing)
        # Do not expose a native document identifier without its read permission.
        row['material_request']=existing.parent if existing and frappe.has_permission('Material Request','read',doc=existing.parent) else None
        row['unrequested_quantity']=0 if existing else row['quantity']
        total=totals.setdefault((row['item'],row['stock_uom']),dict(item=row['item'],stock_uom=row['stock_uom'],quantity=0,already_requested=0,unrequested_quantity=0))
        for key in ('quantity','already_requested','unrequested_quantity'):total[key]+=row[key]
    return {'company':company,'site':site,'from_date':str(start),'to_date':str(end),'rows':details,
        'totals':list(totals.values()),'basis':'Gross frozen procedure demand; not net stock availability or a reservation.',
        'can_create_request':bool(frappe.has_permission('Material Request','create') and frappe.has_permission('Material Request','read'))}


def native_creator():
    for ptype in ('create','read'):
        if not frappe.has_permission('Material Request',ptype):
            frappe.throw('Native Material Request create/read permission required.',frappe.PermissionError)


def request_identity(key, payload):
    if not isinstance(key,str) or not 8<=len(key)<=100:
        frappe.throw('Use a stable request key between 8 and 100 characters.')
    identity=hashlib.sha256((frappe.session.user+'\0'+key).encode()).hexdigest()
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest()
    rows=frappe.db.sql('SELECT name,trucmms_payload_hash FROM `tabMaterial Request` WHERE trucmms_request_key=%s FOR UPDATE',(identity,),as_dict=True)
    if rows:
        doc=frappe.get_doc('Material Request',rows[0].name)
        doc.check_permission('read')
        if rows[0].trucmms_payload_hash!=digest:frappe.throw('Request key was already used for different material requirements.')
        return identity,digest,doc
    return identity,digest,None


def native_item(item,unit,quantity,warehouse,needed_on,**refs):
    doc=frappe.get_doc('Item',item)
    doc.check_permission('read')
    if doc.disabled or doc.has_variants or doc.stock_uom!=unit:
        frappe.throw('Material must be an enabled concrete Item with unchanged stock UOM.')
    quantity=job_plans.finite(quantity,'Requested quantity',positive=True)
    if frappe.db.get_value('UOM',unit,'must_be_whole_number') and quantity!=quantity.to_integral_value():
        frappe.throw('Requested quantity must be whole for this stock UOM.')
    return dict(item_code=item,qty=float(quantity),uom=unit,stock_uom=unit,conversion_factor=1,
        warehouse=warehouse,schedule_date=str(max(getdate(needed_on),getdate())),**refs)


def insert_request(company,site,purpose,items,identity,digest,reason,order=None,sources=None):
    with internal():
        doc=frappe.get_doc(dict(doctype='Material Request',company=company,material_request_type=purpose,
            transaction_date=nowdate(),schedule_date=min(r['schedule_date'] for r in items),items=items,
            trucmms_origin=ORIGIN,trucmms_site=site,trucmms_work_order=order,
            trucmms_request_key=identity,trucmms_payload_hash=digest,trucmms_reason=reason,
            trucmms_sources=sources or [])).insert()
    return {'doctype':doc.doctype,'name':doc.name,'docstatus':doc.docstatus,'created':True}


@frappe.whitelist(methods=['POST'])
@atomic
def purchase_request(company,site,from_date,to_date,warehouse,keys,key,reason):
    logistics.reader();native_creator();scope(company,site)
    teams.locked_document('TruCMMS Site',site)
    warehouse_for(company,site,warehouse)
    reason=job_plans.reason(reason)
    keys=json.loads(keys) if isinstance(keys,str) else keys
    if not isinstance(keys,list) or not keys or len(keys)>1000 or any(not isinstance(k,str) for k in keys):
        frappe.throw('Choose forecast material lines.')
    keys=sorted(set(keys))
    identity,digest,existing=request_identity(key,dict(company=company,site=site,from_date=from_date,to_date=to_date,warehouse=warehouse,keys=keys,reason=reason,purpose='Purchase'))
    if existing:return {'doctype':existing.doctype,'name':existing.name,'docstatus':existing.docstatus,'created':False}
    report=forecast(company,site,from_date,to_date)
    candidates={r['key']:r for r in report['rows']}
    if any(k not in candidates for k in keys):frappe.throw('Forecast changed; reload and select current requirements.')
    previous=purchase_lines(keys)
    if previous:frappe.throw('Some requirements already have a live purchase request. Reload the forecast.')
    grouped={};sources=[]
    for key in keys:
        row=candidates[key];group=(row['item'],row['stock_uom'])
        entry=grouped.setdefault(group,{'quantity':Decimal(0),'needed_on':row['needed_on']})
        entry['quantity']+=Decimal(str(row['quantity']))
        entry['needed_on']=min(entry['needed_on'],row['needed_on'])
        sources.append(dict(source_key=key,active_key=key,occurrence=row['occurrence'],estimate=row.get('estimate'),item=row['item'],
            stock_uom=row['stock_uom'],quantity=row['quantity'],needed_on=row['needed_on']))
    items=[native_item(item,unit,row['quantity'],warehouse,row['needed_on']) for (item,unit),row in sorted(grouped.items())]
    return insert_request(company,site,'Purchase',items,identity,digest,reason,sources=sources)


@frappe.whitelist(methods=['POST'])
@atomic
def issue_request(order,warehouse,items,key,reason):
    doc=teams.locked_document(wo.DT,order)
    doc.check_permission('read')
    if not org.privileged() and not set(frappe.get_roles()) & (logistics.READERS|{'TruCMMS Technician'}):
        frappe.throw('Maintenance participant required.',frappe.PermissionError)
    native_creator();scope(doc.company,doc.site)
    teams.locked_document('TruCMMS Site',doc.site)
    warehouse_for(doc.company,doc.site,warehouse)
    reason=job_plans.reason(reason)
    items=json.loads(items) if isinstance(items,str) else items
    if not isinstance(items,list) or not items or len(items)>50:frappe.throw('Provide between 1 and 50 materials.')
    normalized=[];seen=set()
    for row in items:
        if not isinstance(row,dict) or set(row)!={'item','quantity','stock_uom'}:frappe.throw('Use item, quantity and stock_uom for each material.')
        if row['item'] in seen:frappe.throw('Combine repeated Items in a single quantity.')
        seen.add(row['item'])
        if not frappe.db.get_value('Item',row['item'],'is_stock_item'):frappe.throw('Warehouse issues require stock Items.')
        normalized.append(native_item(row['item'],row['stock_uom'],row['quantity'],warehouse,nowdate()))
    identity,digest,existing=request_identity(key,dict(order=order,warehouse=warehouse,
        items=[{k:r[k] for k in ('item_code','qty','uom')} for r in normalized],reason=reason,purpose='Material Issue'))
    if existing:return {'doctype':existing.doctype,'name':existing.name,'docstatus':existing.docstatus,'created':False}
    if doc.status not in ('Authorized','Assigned'):frappe.throw('Material issues require an authorized, active work order.')
    return insert_request(doc.company,doc.site,'Material Issue',normalized,identity,digest,reason,order=order)


def guard_native(doc,method=None):
    old=doc.get_doc_before_save()
    if doc.is_new() and doc.get('amended_from') and frappe.db.get_value('Material Request',doc.amended_from,'trucmms_origin')==ORIGIN:
        frappe.throw('After cancelling a maintenance request, create a new handoff from its forecast or work order to preserve provenance.')
    linked=bool(doc.get('trucmms_origin'))
    if old and old.get('trucmms_origin'):
        if any(doc.get(k)!=old.get(k) for k in HEADER) or doc.company!=old.company or doc.material_request_type!=old.material_request_type:
            frappe.throw('Maintenance request origin and Company are permanent.')
        old_rows={r.name:r for r in old.items}
        fields=('name','source_key','active_key','occurrence','estimate','item','stock_uom')
        def origin(rows):
            return [tuple(r.get(k) for k in fields)+(Decimal(str(r.quantity)),str(getdate(r.needed_on))) for r in rows]
        if origin(doc.get('trucmms_sources',[])) != origin(old.get('trucmms_sources',[])):
            frappe.throw('Frozen maintenance demand sources cannot be changed.')
        for row in doc.items:
            previous=old_rows.get(row.name)
            if previous and previous.trucmms_source_key:
                if any(row.get(k)!=previous.get(k) for k in (*LINE,'trucmms_active_key','item_code','uom','conversion_factor')):
                    frappe.throw('Frozen maintenance material provenance cannot be changed.')
            elif any(row.get(k) for k in (*LINE,'trucmms_active_key')):
                frappe.throw('Use the maintenance service for forecast material provenance.')
    elif any(doc.get(k) for k in HEADER) or doc.get('trucmms_sources') or any(row.get(k) for row in doc.items for k in (*LINE,'trucmms_active_key')):
        if not frappe.flags.get('trucmms_material_request'):
            frappe.throw('Use the controlled maintenance material service.',frappe.PermissionError)
    if not linked:return
    if doc.trucmms_origin!=ORIGIN:frappe.throw('Invalid maintenance request origin.')
    if method=='before_cancel':
        native_permission(doc)
        return
    scope(doc.company,doc.trucmms_site)
    for row in doc.items:warehouse_for(doc.company,doc.trucmms_site,row.warehouse)
    current_items={(r.item_code,r.stock_uom) for r in doc.items}
    if any((r.item,r.stock_uom) not in current_items for r in doc.get('trucmms_sources',[])):
        frappe.throw('Keep the source Items in this request; cancel and regenerate to remove planned requirements.')


def cancelled(doc,method=None):
    if doc.get('trucmms_origin')==ORIGIN:
        frappe.db.sql('UPDATE `tabTruCMMS Material Source` SET active_key=NULL WHERE parent=%s',(doc.name,))


def native_permission(doc,user=None,ptype=None):
    if doc.get('trucmms_origin')==ORIGIN:
        context=frappe._dict(doctype='Material Request',company=doc.company,site=doc.trucmms_site)
        if not org.in_scope(context,user):
            frappe.throw('Maintenance material requests require Company and Site authorization.',frappe.PermissionError)
    return True


def native_query(user=None):
    # Normal ERP requests keep their own native permissions. The Site field is
    # intentionally not a global native filter for unrelated purchase requests.
    clause=org.query('Material Request',user)
    if not clause:return ''
    clause=clause.replace('`.`site`','`.`trucmms_site`')
    return f"(COALESCE(`tabMaterial Request`.trucmms_origin,'')!='TruCMMS' OR ({clause}))"


def source_query(user=None):
    user=user or frappe.session.user
    if not frappe.has_permission('Material Request','read',user=user):return '1=0'
    original=frappe.session.user
    try:
        if original!=user:frappe.set_user(user)
        parents=frappe.get_list('Material Request',pluck='name',limit_page_length=0)
    finally:
        if original!=user:frappe.set_user(original)
    if not parents:return '1=0'
    return '`tabTruCMMS Material Source`.parent IN ('+','.join(frappe.db.escape(name) for name in parents)+')'


def guard_stock_entry(doc,method=None):
    for row in doc.items:
        if not row.get('material_request'):continue
        request=frappe.get_doc('Material Request',row.material_request)
        if request.get('trucmms_origin')!=ORIGIN:continue
        request.check_permission('read')
        if doc.company!=request.company:frappe.throw('Stock movement must retain the maintenance request Company.')
        if method!='before_cancel':
            for warehouse in (row.get('s_warehouse'),row.get('t_warehouse')):
                if warehouse:warehouse_for(doc.company,request.trucmms_site,warehouse)


def validate_share(doc,method=None):
    if doc.share_doctype=='Material Request' and frappe.db.get_value('Material Request',doc.share_name,'trucmms_origin')==ORIGIN:
        frappe.throw('Maintenance procurement visibility is controlled by Company/Site and native roles, not sharing.',frappe.PermissionError)


def setup():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    def field(name,label,kind='Data',options=None,**kw):
        return dict(fieldname=name,label=label,fieldtype=kind,options=options,read_only=1,no_copy=1,**kw)
    create_custom_fields({'Material Request':[
        field('trucmms_origin','Origen TruCMMS'),field('trucmms_site','Sede TruCMMS','Link','TruCMMS Site',ignore_user_permissions=1),
        field('trucmms_work_order','Orden TruCMMS','Link',wo.DT),
        field('trucmms_request_key','Identidad de solicitud TruCMMS',unique=1,hidden=1),
        field('trucmms_payload_hash','Huella TruCMMS',hidden=1),field('trucmms_reason','Motivo TruCMMS','Small Text'),
        field('trucmms_sources','Detalle de demanda TruCMMS','Table','TruCMMS Material Source')],
        'Material Request Item':[
        field('trucmms_source_key','Demanda original TruCMMS',hidden=1),
        field('trucmms_active_key','Demanda vigente TruCMMS',unique=1,hidden=1),
        field('trucmms_occurrence','Ocurrencia TruCMMS','Link','TruCMMS PM Occurrence')]})
