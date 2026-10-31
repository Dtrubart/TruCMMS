"""Native stock fulfillment and immutable authenticated collection acknowledgments."""
import hashlib
import json
from decimal import Decimal
import frappe
from frappe.utils import now_datetime
from vanbags_maintenance import materials as mat, organization as org, work_orders as wo, teams, job_plans
from vanbags_maintenance.work_contract import atomic

ACK = 'TruCMMS Material Acknowledgment'
HEADER = ('trucmms_work_order', 'trucmms_site', 'trucmms_return_against', 'trucmms_delivery_key')


def context(doc, user=None):
    if doc.get('trucmms_work_order'):
        order = frappe.get_doc(wo.DT, doc.trucmms_work_order)
        if doc.company != order.company or doc.trucmms_site != order.site or not org.in_scope(order, user):
            frappe.throw('Material movement requires the work order Company and Site authorization.', frappe.PermissionError)
        return order


def stock_permission(doc, user=None, ptype=None):
    context(doc, user)
    return True


def stock_query(user=None):
    clause = org.query('Stock Entry', user).replace('`.`site`', '`.`trucmms_site`')
    return "(COALESCE(`tabStock Entry`.trucmms_work_order,'')='' OR (" + clause + '))' if clause else ''


def prepare_stock(doc, method=None):
    old = doc.get_doc_before_save()
    if doc.is_new() and doc.get('amended_from') and frappe.db.get_value('Stock Entry', doc.amended_from, 'trucmms_work_order'):
        frappe.throw('Regenerate a maintenance movement from its request or original issue after cancellation.')
    if old and any(old.get(k) != doc.get(k) for k in HEADER):
        frappe.throw('Maintenance movement identity cannot be changed.')
    orders = set()
    for row in doc.items:
        if not row.get('material_request'): continue
        request = frappe.get_doc('Material Request', row.material_request)
        if request.get('trucmms_origin') != mat.ORIGIN: continue
        request.check_permission('read')
        if request.material_request_type != 'Material Issue' or doc.purpose != 'Material Issue':
            frappe.throw('Use a maintenance issue request only for a native Material Issue.')
        if request.docstatus != 1 or request.status in ('Stopped', 'Cancelled'):
            frappe.throw('Submit and keep the material request active before delivery.')
        orders.add(request.trucmms_work_order)
    if len(orders) > 1: frappe.throw('Use one maintenance work order per stock movement.')
    if orders:
        order = frappe.get_doc(wo.DT, next(iter(orders)))
        if doc.get('trucmms_work_order') and doc.trucmms_work_order != order.name:
            frappe.throw('Stock movement and request must refer to the same work order.')
        doc.trucmms_work_order, doc.trucmms_site = order.name, order.site
    if doc.get('trucmms_return_against'):
        source = frappe.get_doc('Stock Entry', doc.trucmms_return_against)
        source.check_permission('read')
        if source.docstatus != 1 or source.purpose != 'Material Issue' or not source.get('trucmms_work_order'):
            frappe.throw('Return requires a submitted maintenance issue.')
        if doc.is_new() and not frappe.flags.get('trucmms_material_request'):
            frappe.throw('Create maintenance returns from the original issue.', frappe.PermissionError)
        doc.trucmms_work_order, doc.trucmms_site = source.trucmms_work_order, source.trucmms_site
        if doc.purpose != 'Material Receipt': frappe.throw('Maintenance returns use native Material Receipt.')
    order = context(doc)
    if not order:
        if doc.get('trucmms_site') or doc.get('trucmms_delivery_key') or any(r.get('trucmms_issue_detail') for r in doc.items):
            frappe.throw('Incomplete maintenance movement identity.')
        return
    if doc.purpose == 'Material Issue':
        if not orders or any(not r.get('material_request') or frappe.db.get_value('Material Request', r.material_request, 'trucmms_work_order') != order.name for r in doc.items):
            frappe.throw('Every maintenance issue line must originate in this work order material requests.')
        if order.status not in ('Authorized', 'Assigned'):
            frappe.throw('Issue materials only for authorized active work.')
    elif not doc.get('trucmms_return_against'):
        frappe.throw('Use a linked issue or return for maintenance stock movements.')
    for row in doc.items:
        for warehouse in (row.get('s_warehouse'), row.get('t_warehouse')):
            if warehouse: mat.warehouse_for(doc.company, order.site, warehouse)


def validate_stock(doc, method=None):
    if not doc.get('trucmms_work_order'): return
    context(doc)
    if doc.get('trucmms_return_against'):
        source = teams.locked_document('Stock Entry', doc.trucmms_return_against)
        if source.docstatus != 1: frappe.throw('Original issue must remain submitted.')
        originals = {r.name: r for r in source.items}
        totals = {}
        traces = {}
        if doc.additional_costs: frappe.throw('Do not add extra costs to a maintenance return.')
        for row in doc.items:
            original = originals.get(row.get('trucmms_issue_detail'))
            if not original: frappe.throw('Each return line must identify an original issue line.')
            if (row.item_code, row.stock_uom, row.t_warehouse) != (original.item_code, original.stock_uom, original.s_warehouse) or row.s_warehouse or row.material_request:
                frappe.throw('Return the original Item to its original warehouse without a new issue request.')
            qty = job_plans.finite(row.transfer_qty, 'Return quantity', positive=True)
            totals[original.name] = totals.get(original.name,Decimal(0)) + qty
            trace = trace_data(row)
            allowed = trace_data(original)
            rate = Decimal(str(original.valuation_rate))
            if allowed:
                if abs(sum(v[0] for v in trace.values())-qty)>Decimal('0.000001'):
                    frappe.throw('Choose the original serials/batches for every returned unit.')
                value=Decimal(0)
                for key,(amount,_) in trace.items():
                    if key not in allowed:frappe.throw('Serial or batch does not belong to the original issue line.')
                    aggregate=traces.setdefault(original.name,{})
                    aggregate[key]=aggregate.get(key,Decimal(0))+amount
                    value+=amount*allowed[key][1]
                rate=value/qty
            if abs(Decimal(str(row.basic_rate))-rate)>Decimal('0.000001'):
                frappe.throw('Return valuation must use the original issued units valuation rate.')
        for detail, quantity in totals.items():
            used,used_trace=returned(source.name,detail,doc.name)
            if quantity > Decimal(str(originals[detail].transfer_qty))-used:
                frappe.throw('Return quantity exceeds the unreturned original issue quantity.')
            original_trace=trace_data(originals[detail])
            for key,amount in traces.get(detail,{}).items():
                if amount>original_trace[key][0]-used_trace.get(key,Decimal(0)):
                    frappe.throw('These issued serials/batch quantities were already returned.')
    elif method == 'before_submit':
        # Serialize competing deliveries even when native over-delivery tolerance is enabled.
        for request in sorted({r.material_request for r in doc.items}):
            teams.locked_document('Material Request', request)
        totals = {}
        for row in doc.items:
            key = (row.material_request, row.material_request_item)
            totals[key] = totals.get(key, Decimal(0)) + Decimal(str(row.transfer_qty))
        for (request, detail), quantity in totals.items():
            expected = frappe.db.get_value('Material Request Item', {'name':detail, 'parent':request}, 'stock_qty')
            delivered = frappe.db.sql("""SELECT COALESCE(SUM(d.transfer_qty),0) FROM `tabStock Entry Detail` d
                JOIN `tabStock Entry` p ON p.name=d.parent WHERE p.docstatus=1 AND p.purpose='Material Issue'
                AND d.material_request=%s AND d.material_request_item=%s AND p.name!=%s""", (request, detail, doc.name))[0][0]
            if expected is None or quantity + Decimal(str(delivered)) > Decimal(str(expected)):
                frappe.throw('Delivery exceeds the submitted material request quantity.')


def before_cancel(doc, method=None):
    stored=teams.locked_document('Stock Entry', doc.name)
    if not stored.get('trucmms_work_order') and not doc.get('trucmms_work_order'):return
    if stored.company!=doc.company or any(stored.get(k)!=doc.get(k) for k in HEADER):
        frappe.throw('Movement identity cannot change during cancellation.')
    fields=('name','item_code','qty','transfer_qty','s_warehouse','t_warehouse','material_request','material_request_item','trucmms_issue_detail','serial_and_batch_bundle')
    if [[r.get(k) for k in fields] for r in stored.items]!=[[r.get(k) for k in fields] for r in doc.items]:
        frappe.throw('Do not change submitted movement lines while cancelling.')
    context(stored)
    if frappe.db.exists('Stock Entry', {'trucmms_return_against':doc.name, 'docstatus':1}):
        frappe.throw('Cancel the linked returns before cancelling this issue.')


def after_cancel(doc, method=None):
    if doc.get('trucmms_work_order'):
        doc.ignore_linked_doctypes = tuple(doc.get('ignore_linked_doctypes') or ()) + (ACK,)


def idempotent(key, source, kind):
    if not isinstance(key, str) or not 8 <= len(key) <= 100: frappe.throw('Provide a stable request key (8-100 characters).')
    identity = hashlib.sha256(json.dumps([frappe.session.user, kind, source, key]).encode()).hexdigest()
    name = frappe.db.get_value('Stock Entry', {'trucmms_delivery_key':identity}, 'name')
    if name: frappe.get_doc('Stock Entry', name).check_permission('read')
    return identity, name


@frappe.whitelist(methods=['POST'])
@atomic
def delivery(request, key):
    doc = teams.locked_document('Material Request', request)
    doc.check_permission('read')
    if doc.get('trucmms_origin') != mat.ORIGIN or doc.material_request_type != 'Material Issue':
        frappe.throw('Choose a TruCMMS material issue request.')
    if not frappe.has_permission('Stock Entry', 'create'): frappe.throw('Native Stock Entry create permission required.', frappe.PermissionError)
    identity, existing = idempotent(key, request, 'Issue')
    if existing: return {'name':existing, 'created':False}
    from erpnext.stock.doctype.material_request.material_request import make_stock_entry
    stock = make_stock_entry(request)
    stock.trucmms_delivery_key = identity
    stock.insert()
    return {'name':stock.name, 'created':True}


@frappe.whitelist(methods=['POST'])
@atomic
def return_draft(issue, key):
    source = teams.locked_document('Stock Entry', issue)
    source.check_permission('read'); context(source)
    if source.docstatus != 1 or source.purpose != 'Material Issue' or not source.get('trucmms_work_order'):
        frappe.throw('Choose a submitted maintenance issue.')
    if not frappe.has_permission('Stock Entry', 'create'): frappe.throw('Native Stock Entry create permission required.', frappe.PermissionError)
    identity, existing = idempotent(key, issue, 'Return')
    if existing: return {'name':existing, 'created':False}
    items = []
    for row in source.items:
        used,used_trace=returned(source.name,row.name)
        qty=Decimal(str(row.transfer_qty))-used
        if qty<=0:continue
        trace=trace_data(row)
        selections=[(None,None,qty,Decimal(str(row.valuation_rate)))]
        if trace:
            selections=[(serial,batch,amount-used_trace.get((serial,batch),Decimal(0)),rate)
                for (serial,batch),(amount,rate) in trace.items() if amount>used_trace.get((serial,batch),Decimal(0))]
        for serial,batch,quantity,rate in selections:
            items.append(dict(item_code=row.item_code,qty=float(quantity),uom=row.stock_uom,stock_uom=row.stock_uom,
                conversion_factor=1,t_warehouse=row.s_warehouse,basic_rate=float(rate),set_basic_rate_manually=1,
                allow_zero_valuation_rate=int(not rate),expense_account=row.expense_account,cost_center=row.cost_center,
                trucmms_issue_detail=row.name,use_serial_batch_fields=int(bool(trace)),serial_no=serial,batch_no=batch))
    if not items: frappe.throw('No issued quantity remains to return.')
    with mat.internal():
        doc = frappe.get_doc(dict(doctype='Stock Entry',stock_entry_type='Material Receipt',purpose='Material Receipt',
            company=source.company,trucmms_return_against=issue,trucmms_delivery_key=identity,items=items)).insert()
    return {'name':doc.name, 'created':True}


def ack_permission(doc, user=None, ptype=None):
    order = frappe.get_doc(wo.DT,doc.work_order)
    if not wo.can_read(order,user):frappe.throw('Work order read permission required.',frappe.PermissionError)
    if not org.in_scope(order,user): frappe.throw('Company/Site authorization required.',frappe.PermissionError)
    return True


def ack_query(user=None):
    from vanbags_maintenance import lifecycle
    return lifecycle.event_query(user).replace('tabTruCMMS Work Event', 'tab'+ACK)


@frappe.whitelist(methods=['POST'])
@atomic
def acknowledge(stock_entry, reason):
    stock = teams.locked_document('Stock Entry', stock_entry)
    order = context(stock)
    if not order or stock.docstatus != 1 or stock.purpose != 'Material Issue': frappe.throw('A submitted maintenance issue is required.')
    order.check_permission('read')
    roles = set(frappe.get_roles())
    if not org.privileged() and not roles.intersection({'TruCMMS Supervisor','TruCMMS Technician'}):
        frappe.throw('An authorized technician or supervisor must confirm collection.',frappe.PermissionError)
    # Work order permission limits technicians to their current allocations.
    reason = job_plans.reason(reason)
    existing = frappe.db.get_value(ACK, {'stock_entry':stock.name}, 'name')
    if existing: return {'name':existing,'created':False}
    snapshot = json.dumps([dict(item=r.item_code,quantity=r.transfer_qty,stock_uom=r.stock_uom,warehouse=r.s_warehouse) for r in stock.items],sort_keys=True)
    with mat.internal():
        doc = frappe.get_doc(dict(doctype=ACK,stock_entry=stock.name,work_order=order.name,company=order.company,site=order.site,
            received_by=frappe.session.user,received_on=now_datetime(),reason=reason,items_snapshot=snapshot)).insert(ignore_permissions=True)
    return {'name':doc.name,'created':True}


def validate_share(doc, method=None):
    if doc.share_doctype == ACK or doc.share_doctype == 'Stock Entry' and frappe.db.get_value('Stock Entry',doc.share_name,'trucmms_work_order'):
        frappe.throw('Maintenance material access cannot be expanded through sharing.',frappe.PermissionError)


@frappe.whitelist(methods=['GET'])
def reconciliation(order):
    doc = frappe.get_doc(wo.DT,order);doc.check_permission('read')
    if not org.in_scope(doc): frappe.throw('Company/Site authorization required.',frappe.PermissionError)
    entries = frappe.get_all('Stock Entry',filters={'trucmms_work_order':order},fields=['name','purpose','docstatus','trucmms_return_against','posting_date'],order_by='creation')
    requested = frappe.db.sql("""SELECT i.item_code,i.stock_uom,SUM(i.stock_qty) quantity FROM `tabMaterial Request Item` i
        JOIN `tabMaterial Request` p ON p.name=i.parent WHERE p.trucmms_work_order=%s AND p.docstatus=1
        AND p.material_request_type='Material Issue' GROUP BY i.item_code,i.stock_uom""",order,as_dict=True)
    totals = {(r.item_code,r.stock_uom):dict(item=r.item_code,stock_uom=r.stock_uom,requested=float(r.quantity),issued=0,returned=0,net_issued=0) for r in requested}
    for entry in entries:
        entry['acknowledgment'] = frappe.db.get_value(ACK,{'stock_entry':entry.name},['name','received_by','received_on'],as_dict=True)
        rows = frappe.get_all('Stock Entry Detail',filters={'parent':entry.name},fields=['item_code','stock_uom','transfer_qty'])
        entry['items'] = rows
        entry['can_open'] = bool(frappe.has_permission('Stock Entry','read',doc=entry.name))
        if entry.docstatus != 1: continue
        for row in rows:
            target=totals.setdefault((row.item_code,row.stock_uom),dict(item=row.item_code,stock_uom=row.stock_uom,requested=0,issued=0,returned=0,net_issued=0))
            target['returned' if entry.trucmms_return_against else 'issued'] += float(row.transfer_qty)
    for row in totals.values():row['net_issued']=row['issued']-row['returned'];row['pending_issue']=max(0,row['requested']-row['issued'])
    return {'order':order,'rows':list(totals.values()),'movements':entries,
        'basis':'Submitted native issues less linked returns; net issued is not independently measured physical consumption.'}


def setup():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    def field(name,label,kind='Data',options=None,**kw):
        return dict(fieldname=name,label=label,fieldtype=kind,options=options,read_only=1,no_copy=1,**kw)
    create_custom_fields({'Stock Entry':[
        field('trucmms_work_order','Orden TruCMMS','Link',wo.DT,ignore_user_permissions=1),
        field('trucmms_site','Sede TruCMMS','Link','TruCMMS Site',ignore_user_permissions=1),
        field('trucmms_return_against','Salida original TruCMMS','Link','Stock Entry'),
        field('trucmms_delivery_key','Identidad TruCMMS',unique=1,hidden=1)],
        'Stock Entry Detail':[field('trucmms_issue_detail','Línea original TruCMMS',hidden=1)]})
    if not frappe.db.exists('Print Format','TruCMMS Collection Receipt'):
        frappe.get_doc(dict(doctype='Print Format',name='TruCMMS Collection Receipt',doc_type=ACK,custom_format=1,print_format_type='Jinja',
            html=COLLECTION_PRINT)).insert(ignore_permissions=True)
    else:
        form=frappe.get_doc('Print Format','TruCMMS Collection Receipt')
        if 'frappe.parse_json(doc.items_snapshot)' in (form.html or ''):
            form.html=form.html.replace('frappe.parse_json(doc.items_snapshot)','json.loads(doc.items_snapshot)');form.save(ignore_permissions=True)


def guard_child(doc,method=None):
    old=doc.get_doc_before_save()
    for row in (doc,old):
        if not row:continue
        if row.get('trucmms_issue_detail') or row.parent and frappe.db.get_value('Stock Entry',row.parent,'trucmms_work_order') or row.get('material_request') and frappe.db.get_value('Material Request',row.material_request,'trucmms_origin')==mat.ORIGIN:
            frappe.throw('Edit maintenance stock details through their native parent document.',frappe.PermissionError)


def trace_data(row):
    result={}
    if row.get('serial_and_batch_bundle'):
        entries=frappe.get_all('Serial and Batch Entry',filters={'parent':row.serial_and_batch_bundle},
            fields=['serial_no','batch_no','qty','stock_value_difference'])
        for entry in entries:
            key=(entry.serial_no or None,entry.batch_no or None);qty=abs(Decimal(str(entry.qty)))
            if not qty:continue
            rate=abs(Decimal(str(entry.stock_value_difference or 0)))/qty
            prior=result.get(key,(Decimal(0),rate))
            result[key]=(prior[0]+qty,(prior[0]*prior[1]+qty*rate)/(prior[0]+qty))
    else:
        serials=[v.strip() for v in (row.get('serial_no') or '').splitlines() if v.strip()]
        if len(set(serials))!=len(serials):frappe.throw('A serial number cannot appear twice.')
        rate=Decimal(str(row.get('valuation_rate') or row.get('basic_rate') or 0))
        if serials:
            for serial in serials:result[(serial,row.get('batch_no') or None)]=(Decimal(1),rate)
        elif row.get('batch_no'):result[(None,row.batch_no)]=(Decimal(str(row.transfer_qty)),rate)
    return result


def returned(issue,detail,exclude=''):
    rows=frappe.db.sql("""SELECT d.* FROM `tabStock Entry Detail` d JOIN `tabStock Entry` p ON p.name=d.parent
        WHERE p.docstatus=1 AND p.trucmms_return_against=%s AND d.trucmms_issue_detail=%s AND p.name!=%s""",
        (issue,detail,exclude or ''),as_dict=True)
    total=Decimal(0);trace={}
    for row in rows:
        total+=Decimal(str(row.transfer_qty))
        for key,(qty,_) in trace_data(row).items():trace[key]=trace.get(key,Decimal(0))+qty
    return total,trace


COLLECTION_PRINT = """<h2>Constancia de recogida de materiales</h2>
<p>{{ doc.company | e }} · {{ doc.site | e }}</p>
<p>Orden: {{ doc.work_order | e }} · Vale: {{ doc.stock_entry | e }}</p>
{% if frappe.db.get_value('Stock Entry',doc.stock_entry,'docstatus') == 2 %}<p><strong>Vale anulado — constancia histórica</strong></p>{% endif %}
<table class="table table-bordered"><thead><tr><th>Artículo</th><th>Cantidad</th><th>Unidad</th><th>Almacén</th></tr></thead><tbody>
{% for row in json.loads(doc.items_snapshot) %}<tr><td>{{ row.item | e }}</td><td>{{ row.quantity | e }}</td><td>{{ row.stock_uom | e }}</td><td>{{ row.warehouse | e }}</td></tr>{% endfor %}
</tbody></table><p>Recibido por: {{ doc.received_by | e }} · {{ doc.received_on | e }}</p><p>{{ doc.reason | e }}</p>"""
