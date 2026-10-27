"""Retry-safe submission for native execution forms; authorization stays on the controller."""
import hashlib,json,uuid
import frappe
from frappe.utils import get_datetime
from vanbags_maintenance import teams,work_orders as wo
from vanbags_maintenance.work_contract import atomic
EX='TruCMMS Work Execution'

def normalize(payload):
    payload=frappe.parse_json(payload) if isinstance(payload,str) else payload
    if not isinstance(payload,dict) or set(payload)-{'work_order','actual_start','actual_end','findings','tasks'}:frappe.throw('Unsupported execution payload.')
    if not all(isinstance(payload.get(k),str) and payload[k].strip() for k in ('work_order','actual_start','actual_end','findings')):frappe.throw('Work order, actual start/end and findings are required.')
    tasks=payload.get('tasks')
    if not isinstance(tasks,list) or not 1<=len(tasks)<=100:frappe.throw('Supply between 1 and 100 performed tasks.')
    values=[]
    for row in tasks:
        if not isinstance(row,dict) or set(row)-{'task','result','findings'} or not all(isinstance(row.get(k),str) for k in ('task','result','findings')):frappe.throw('Each task requires task, result and findings.')
        values.append({k:row[k].strip() for k in ('task','result','findings')})
    return {'work_order':payload['work_order'],'actual_start':str(get_datetime(payload['actual_start'])),'actual_end':str(get_datetime(payload['actual_end'])),'findings':payload['findings'].strip(),'tasks':values}

@frappe.whitelist(methods=['POST'])
@atomic
def submit(payload,key):
    try:key=str(uuid.UUID(key))
    except (ValueError,TypeError,AttributeError):frappe.throw('Invalid submission identifier. Keep the original form open to retry.')
    values=normalize(payload);user=frappe.session.user
    order=teams.locked_document(wo.DT,values['work_order']);order.check_permission('read')
    if order.status=='Assigned':
        from vanbags_maintenance.execution import order_for_recording
        order_for_recording(order.name)
    teams.locked_sql('SELECT name FROM `tabUser` WHERE name=%s FOR UPDATE',(user,))
    identity=hashlib.sha256((user+'|'+key).encode()).hexdigest();digest=hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()
    existing=teams.locked_sql(f'SELECT name,submission_digest,technician FROM `tab{EX}` WHERE submission_key=%s FOR UPDATE',(identity,),as_dict=True)
    if existing:
        doc=teams.locked_document(EX,existing[0].name);doc.check_permission('read')
        if existing[0].technician!=user or existing[0].submission_digest!=digest:frappe.throw('This submission was already saved with different contents. Review '+frappe.utils.get_link_to_form(EX,doc.name)+' before creating another execution.')
        return doc.as_dict()
    prior=frappe.flags.get('trucmms_submission');frappe.flags.trucmms_submission=(identity,digest)
    try:return frappe.get_doc({'doctype':EX,**values,'submission_key':identity,'submission_digest':digest}).insert().as_dict()
    finally:frappe.flags.trucmms_submission=prior

def validate_new(doc):
    if doc.submission_key or doc.submission_digest:
        if frappe.flags.get('trucmms_submission')!=(doc.submission_key,doc.submission_digest):frappe.throw('Submission identifiers are server controlled.',frappe.PermissionError)
