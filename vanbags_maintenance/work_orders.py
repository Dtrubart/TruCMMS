"""Native corrective work orders, authorization and scoped assignment."""
import frappe
from vanbags_maintenance import organization as org
DT='TruCMMS Maintenance Work Order'
SUPERVISOR='TruCMMS Supervisor'
TECHNICIAN='TruCMMS Technician'
DISPATCHER='TruCMMS Dispatcher'
CONTEXT=('company','site','equipment','functional_location')
AUDIT=('authorized_by','authorized_on','assigned_by','assigned_on')


def supervisor(user=None):
    return org.privileged(user) or SUPERVISOR in frappe.get_roles(user or frappe.session.user)


def can_read(doc,user=None):
    user=user or frappe.session.user
    if not org.in_scope(doc,user):return False
    roles=frappe.get_roles(user)
    from vanbags_maintenance.allocations import current
    allocated=bool(current(doc,user)) if TECHNICIAN in roles else False
    return org.privileged(user) or SUPERVISOR in roles or DISPATCHER in roles or (TECHNICIAN in roles and doc.status not in ('Draft','Authorized') and (doc.assigned_to==user or allocated)) or ('TruCMMS Requester' in roles and user in (doc.get('requester'),doc.get('acceptance_user')) and bool(doc.get('completed_on') or doc.get('rework_on') or doc.get('cancelled_on') or doc.get('has_review_history')))


def has_permission(doc,user=None,ptype=None):
    user=user or frappe.session.user
    if not can_read(doc,user):frappe.throw('Work order role and Company/Site authorization required.',frappe.PermissionError)
    if ptype in ('write','create','delete') and not supervisor(user):
        stored=frappe.db.get_value(DT,doc.name,'status') if not doc.is_new() else 'Draft'
        if DISPATCHER not in frappe.get_roles(user) or stored!='Draft':frappe.throw('Only supervisors may manage authorized work.',frappe.PermissionError)
    return True


def query(user=None):
    user=user or frappe.session.user
    scope=org.query(DT,user)
    if supervisor(user) or DISPATCHER in frappe.get_roles(user):return scope
    roles=frappe.get_roles(user);clauses=[]
    if TECHNICIAN in roles:
        from vanbags_maintenance.allocations import participant_sql
        clauses.append(f"(`tab{DT}`.status NOT IN ('Draft','Authorized') AND (`tab{DT}`.assigned_to={frappe.db.escape(user)} OR ({participant_sql(user)})))")
    if 'TruCMMS Requester' in roles:clauses.append(f"((`tab{DT}`.requester={frappe.db.escape(user)} OR `tab{DT}`.acceptance_user={frappe.db.escape(user)}) AND (`tab{DT}`.completed_on IS NOT NULL OR `tab{DT}`.rework_on IS NOT NULL OR `tab{DT}`.cancelled_on IS NOT NULL OR `tab{DT}`.has_review_history=1))")
    return f"({scope}) AND ("+' OR '.join(clauses)+')' if clauses else '1=0'


def validate_technician(doc):
    user=doc.assigned_to
    if not user or not frappe.db.get_value('User',user,'enabled') or TECHNICIAN not in frappe.get_roles(user):
        frappe.throw('Choose an enabled TruCMMS Technician.')
    if not org.in_scope(doc,user):frappe.throw('Technician must be authorized for the Company and Site.',frappe.PermissionError)


@frappe.whitelist(methods=["POST"])
def from_request(request):
    source=frappe.get_doc('TruCMMS Maintenance Request',request)
    source.check_permission('read')
    if source.status!='Approved':frappe.throw('Only approved requests can generate work orders.')
    # Serialize duplicate conversion requests, backed by a unique Link column.
    frappe.db.sql('select name from `tabTruCMMS Maintenance Request` where name=%s for update',(request,))
    existing=frappe.db.get_value(DT,{'maintenance_request':request},'name')
    if existing:
        doc=frappe.get_doc(DT,existing);doc.check_permission('read');return doc.as_dict()
    doc=frappe.get_doc({'doctype':DT,'maintenance_request':request,'origin_type':'Maintenance Request',
        **{f:source.get(f) for f in CONTEXT},'subject':source.subject,'scope':source.description,'priority':source.priority})
    doc.insert();return doc.as_dict()


def validate_share(doc,method=None):
    if doc.share_doctype==DT:
        parent=frappe.get_doc(DT,doc.share_name)
        if doc.everyone or not can_read(parent,doc.user):frappe.throw('Sharing cannot expand work order access.',frappe.PermissionError)


def setup():
    from vanbags_maintenance.requests import setup as request_setup
    request_setup()
    name='TruCMMS Work Order Workflow'
    if frappe.db.exists('Workflow',name):return
    for state in ('Draft','Authorized','Assigned'):
        if not frappe.db.exists('Workflow State',state):frappe.get_doc({'doctype':'Workflow State','workflow_state_name':state}).insert(ignore_permissions=True)
    for action in ('Authorize','Assign'):
        if not frappe.db.exists('Workflow Action Master',action):frappe.get_doc({'doctype':'Workflow Action Master','workflow_action_name':action}).insert(ignore_permissions=True)
    frappe.get_doc({'doctype':'Workflow','workflow_name':name,'document_type':DT,'is_active':1,'workflow_state_field':'status',
        'states':[{'state':s,'doc_status':'0','allow_edit':DISPATCHER if s=='Draft' else SUPERVISOR} for s in ('Draft','Authorized','Assigned')],
        'transitions':[{'state':a,'action':action,'next_state':b,'allowed':SUPERVISOR,'allow_self_approval':1} for a,action,b in [('Draft','Authorize','Authorized'),('Authorized','Assign','Assigned')]]}).insert(ignore_permissions=True)
