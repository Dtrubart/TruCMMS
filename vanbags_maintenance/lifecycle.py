"""Controlled technical completion, independent acceptance, rework and closure."""
import frappe
from frappe.utils import now_datetime, cint, get_datetime
from vanbags_maintenance import work_orders as wo
from vanbags_maintenance import organization as org
DT=wo.DT
EVENT='TruCMMS Work Event'
AUDIT=tuple(f'{p}_{s}' for p in ('completed','accepted','closed','cancelled','rework') for s in ('by','on','reason'))+('acceptance_method',)
TERMINAL=('Closed','Cancelled')
EDGES={'Complete Work':('Assigned','Technical Completed'),'Accept Work':('Technical Completed','Accepted'),
       'Accept on Behalf':('Technical Completed','Accepted'),'Request Rework':('Technical Completed','Assigned'),
       'Close Order':('Accepted','Closed')}


def validate_action(doc,action,reason):
    if doc.get('lifecycle_policy')=='C1':
        from vanbags_maintenance.work_cycle import validate_action as current
        return current(doc,action,reason)
    user=frappe.session.user
    if not org.in_scope(doc,user) or not wo.can_read(doc,user):frappe.throw('Company/Site and work order access required.',frappe.PermissionError)
    if not (reason or '').strip():frappe.throw('A reason or summary is required.')
    if action=='Cancel Order':
        if doc.status not in ('Draft','Authorized','Assigned','Technical Completed'):frappe.throw('This order cannot be cancelled.')
        if not wo.supervisor():frappe.throw('Supervisor role required.',frappe.PermissionError)
        return 'Cancelled'
    if action not in EDGES or doc.status!=EDGES[action][0]:frappe.throw('Invalid lifecycle action for the current state.')
    requester='TruCMMS Requester' in frappe.get_roles() and doc.requester==user
    if action=='Complete Work':
        if wo.TECHNICIAN not in frappe.get_roles() or doc.assigned_to!=user:frappe.throw('Assigned technician required.',frappe.PermissionError)
        from vanbags_maintenance.teams import execution_check
        execution_check(doc,user)
        from vanbags_maintenance.adjustments import effective_latest
        latest=effective_latest(doc.name,cint(doc.execution_cycle) or 1)
        if not latest:frappe.throw('Record execution for the current cycle before completing work.')
        entry=frappe.get_doc('TruCMMS Work Execution',latest[0].name)
        if entry.technician!=user or get_datetime(entry.actual_end)<get_datetime(doc.assigned_on):frappe.throw('Record execution for the current assigned technician before completing work.')
        if any(row.result!='Completed' for row in entry.tasks):frappe.throw('The latest execution must report completed tasks before technical completion.')
    elif action in ('Accept Work','Accept on Behalf'):
        if user==doc.completed_by:frappe.throw('The technician who completed work cannot accept their own completion.',frappe.PermissionError)
        if action=='Accept Work' and not requester:frappe.throw('Original requester acceptance required.',frappe.PermissionError)
        if action=='Accept on Behalf' and not wo.supervisor():frappe.throw('Supervisor acceptance with justification required.',frappe.PermissionError)
    elif action=='Request Rework':
        if not requester and not wo.supervisor():frappe.throw('Requester or supervisor review required.',frappe.PermissionError)
    elif action=='Close Order' and not wo.supervisor():frappe.throw('Supervisor closure required.',frappe.PermissionError)
    return EDGES[action][1]


def validate_change(doc,old):
    if old.get('lifecycle_policy')=='C1' or doc.get('lifecycle_policy')=='C1' or frappe.flags.get('trucmms_c_action'):
        from vanbags_maintenance.work_cycle import validate_change as current
        return current(doc,old)
    if old.status in TERMINAL:frappe.throw('Closed and cancelled orders are immutable.',frappe.PermissionError)
    ctx=frappe.flags.get('trucmms_lifecycle')
    if ctx and ctx['name']==doc.name:
        if any(doc.get(f)!=old.get(f) for f in wo.CONTEXT+('maintenance_request','requester','subject','scope','priority','assigned_to','origin_type','target_closure','responsible_team','required_discipline','team_policy','team_assignment')+wo.AUDIT):
            frappe.throw('Lifecycle actions cannot change authorized scope or assignment.')
        if doc.status!=validate_action(old,ctx['action'],ctx['reason']):frappe.throw('Invalid lifecycle destination.')
        return
    for field in AUDIT+('requester','execution_cycle'):
        a,z=doc.get(field),old.get(field)
        if field.endswith('_on') and a and z:a,z=get_datetime(a),get_datetime(z)
        if a!=z:frappe.throw('Lifecycle audit fields cannot be changed.')
    if doc.status!=old.status and (old.status,doc.status) not in (('Draft','Authorized'),('Authorized','Assigned')):
        frappe.throw('Use a controlled lifecycle action to change this state.',frappe.PermissionError)


@frappe.whitelist(methods=["POST"])
def perform(work_order,action,reason):
    reason=(reason or '').strip()
    frappe.db.sql('select name from `tabTruCMMS Maintenance Work Order` where name=%s for update',(work_order,))
    doc=frappe.get_doc(DT,work_order)
    if doc.get('lifecycle_policy')=='C1' or action=='Reopen Order':
        from vanbags_maintenance.work_cycle import perform as current
        return current(work_order,action,reason)
    doc.check_permission('read')
    target=validate_action(doc,action,reason)
    before=doc.status;stamp=now_datetime();user=frappe.session.user
    prefix={'Complete Work':'completed','Accept Work':'accepted','Accept on Behalf':'accepted','Request Rework':'rework','Close Order':'closed','Cancel Order':'cancelled'}[action]
    doc.set(prefix+'_by',user);doc.set(prefix+'_on',stamp);doc.set(prefix+'_reason',reason)
    if action in ('Accept Work','Accept on Behalf'):doc.acceptance_method='Requester' if action=='Accept Work' else 'Supervisor on behalf'
    if action=='Request Rework':doc.execution_cycle=(cint(doc.execution_cycle) or 1)+1
    doc.status=target
    previous=frappe.flags.get('trucmms_lifecycle');frappe.flags.trucmms_lifecycle={'name':doc.name,'action':action,'reason':reason}
    try:
        doc.save(ignore_permissions=True,ignore_version=False)
        frappe.get_doc({'doctype':EVENT,'work_order':doc.name,'company':doc.company,'site':doc.site,'action':action,
            'from_state':before,'to_state':target,'actor':user,'occurred_on':stamp,'reason':reason,'execution_cycle':doc.execution_cycle}).insert(ignore_permissions=True)
    finally:frappe.flags.trucmms_lifecycle=previous
    return doc.as_dict()


def event_permission(doc,user=None,ptype=None):
    if not wo.can_read(frappe.get_doc(DT,doc.work_order),user):frappe.throw('Work event access requires work order access.',frappe.PermissionError)
    if ptype in ('write','create','delete'):frappe.throw('Work events are immutable.',frappe.PermissionError)
    return True


def event_query(user=None):
    condition=wo.query(user)
    return f"EXISTS (SELECT 1 FROM `tab{DT}` WHERE `tab{DT}`.name=`tab{EVENT}`.work_order AND ({condition}))" if condition else ''


def validate_share(doc,method=None):
    if doc.share_doctype==EVENT:
        if doc.everyone:frappe.throw('Lifecycle events cannot be shared publicly.',frappe.PermissionError)
        event_permission(frappe.get_doc(EVENT,doc.share_name),doc.user,'read')


def setup():
    wo.setup()
    # Versioned upgrade of the managed three-state workflow. Preserve customization
    # by refusing to overwrite a different state/transition contract.
    workflow=frappe.get_doc('Workflow','TruCMMS Work Order Workflow')
    states={row.state for row in workflow.states}
    target={'Draft','Authorized','Assigned','Technical Completed','Accepted','Closed','Cancelled'}
    if states=={'Draft','Authorized','Assigned'}:
        original={(r.state,r.action,r.next_state,r.allowed) for r in workflow.transitions}
        expected={('Draft','Authorize','Authorized',wo.SUPERVISOR),('Authorized','Assign','Assigned',wo.SUPERVISOR)}
        if original!=expected or any(r.condition for r in workflow.transitions):frappe.throw('Custom work order workflow requires explicit upgrade review.')
        for state in target:
            if not frappe.db.exists('Workflow State',state):frappe.get_doc({'doctype':'Workflow State','workflow_state_name':state}).insert(ignore_permissions=True)
        transitions=[('Assigned','Complete Work','Technical Completed',wo.TECHNICIAN),('Technical Completed','Accept Work','Accepted','TruCMMS Requester'),
          ('Technical Completed','Accept on Behalf','Accepted',wo.SUPERVISOR),('Technical Completed','Request Rework','Assigned','TruCMMS Requester'),
          ('Technical Completed','Request Rework','Assigned',wo.SUPERVISOR),('Accepted','Close Order','Closed',wo.SUPERVISOR)]
        transitions += [(state,'Cancel Order','Cancelled',wo.SUPERVISOR) for state in ('Draft','Authorized','Assigned','Technical Completed')]
        for a,action,z,role in transitions:
            if not frappe.db.exists('Workflow Action Master',action):frappe.get_doc({'doctype':'Workflow Action Master','workflow_action_name':action}).insert(ignore_permissions=True)
            workflow.append('transitions',{'state':a,'action':action,'next_state':z,'allowed':role,'allow_self_approval':1})
        for state in sorted(target-states):workflow.append('states',{'state':state,'doc_status':'0','allow_edit':wo.SUPERVISOR})
        workflow.save(ignore_permissions=True)
    elif states!=target:frappe.throw('Custom work order workflow requires explicit upgrade review.')
    # System Manager has the same explicit administrative authority as the
    # supervisor policy; represent it in native Workflow too, without bypassing it.
    existing={(r.state,r.action,r.next_state,r.allowed) for r in workflow.transitions}
    changed=False
    for row in list(workflow.transitions):
        key=(row.state,row.action,row.next_state,'System Manager')
        if row.allowed==wo.SUPERVISOR and key not in existing:
            workflow.append('transitions',{'state':row.state,'action':row.action,'next_state':row.next_state,'allowed':'System Manager','allow_self_approval':1})
            existing.add(key);changed=True
    if changed:workflow.save(ignore_permissions=True)
    frappe.db.sql("update `tabTruCMMS Maintenance Work Order` w join `tabTruCMMS Maintenance Request` r on r.name=w.maintenance_request set w.requester=r.owner where coalesce(w.requester,'')=''")
    frappe.db.sql('update `tabTruCMMS Maintenance Work Order` set execution_cycle=1 where coalesce(execution_cycle,0)=0')
    frappe.db.sql('update `tabTruCMMS Work Execution` set execution_cycle=1 where coalesce(execution_cycle,0)=0')
