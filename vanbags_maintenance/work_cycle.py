"""C1 lifecycle: independent verification, controlled exceptions and cycle archives."""
import json
import frappe
from frappe.utils import now_datetime,cint,get_datetime
from vanbags_maintenance import work_orders as wo,organization as org,teams,work_contract as contract,allocations
EVENT='TruCMMS Work Event'
CYCLE='TruCMMS Work Cycle'
AUDIT=tuple(p+'_'+s for p in ('verified','held','resumed','reopened') for s in ('by','on','reason'))

def audit_snapshot(doc):
    data=doc.as_dict()
    for field in doc.meta.fields:
        if field.permlevel:data.pop(field.fieldname,None)
    return data

def public_snapshot(data):
    result=dict(data)
    for field in frappe.get_meta(wo.DT).fields:
        if field.permlevel:result.pop(field.fieldname,None)
    return result


def locked_order(name):
    teams.locked_sql(f'SELECT name FROM `tab{wo.DT}` WHERE name=%s FOR UPDATE',(name,))
    doc=frappe.get_doc(wo.DT,name);doc.check_permission('read');return doc

def event(doc,action,before,reason,snapshot=None):
    previous=frappe.flags.get('trucmms_lifecycle');frappe.flags.trucmms_lifecycle={'name':doc.name,'action':action,'reason':reason}
    try:return frappe.get_doc({'doctype':EVENT,'work_order':doc.name,'company':doc.company,'site':doc.site,'action':action,'from_state':before,'to_state':doc.status,'actor':frappe.session.user,'occurred_on':now_datetime(),'reason':reason,'execution_cycle':doc.execution_cycle,'before_snapshot':frappe.as_json(public_snapshot(snapshot)) if snapshot else None}).insert(ignore_permissions=True)
    finally:frappe.flags.trucmms_lifecycle=previous

def save(doc,action,reason,allowed):
    previous=frappe.flags.get('trucmms_c_action');frappe.flags.trucmms_c_action={'name':doc.name,'action':action,'reason':reason,'allowed':tuple(allowed)}
    try:doc.save(ignore_permissions=True,ignore_version=False)
    finally:frappe.flags.trucmms_c_action=previous

def archive(doc,action):
    previous=frappe.flags.get('trucmms_cycle_insert');frappe.flags.trucmms_cycle_insert=True
    try:frappe.get_doc({'doctype':CYCLE,'work_order':doc.name,'company':doc.company,'site':doc.site,'execution_cycle':doc.execution_cycle,'snapshot':frappe.as_json(audit_snapshot(doc)),'ended_action':action,'recorded_on':now_datetime(),'recorded_by':frappe.session.user}).insert(ignore_permissions=True)
    finally:frappe.flags.trucmms_cycle_insert=previous

def validate_action(doc,action,reason):
    user=frappe.session.user
    if not org.in_scope(doc,user) or not wo.can_read(doc,user):frappe.throw('Company/Site and order access required.',frappe.PermissionError)
    if not (reason or '').strip():frappe.throw('A reason or summary is required.')
    supervisor=wo.supervisor();requester='TruCMMS Requester' in frappe.get_roles() and user==doc.acceptance_user
    if action=='Complete Work':
        if doc.status!='Assigned':frappe.throw('Complete only assigned work.')
        if user!=doc.assigned_to or wo.TECHNICIAN not in frappe.get_roles():frappe.throw('Primary assigned technician required.',frappe.PermissionError)
        allocations.check_completion(doc);return 'Technical Completed'
    if action=='Verify Work':
        if doc.status!='Technical Completed':frappe.throw('Verify technically completed work.')
        if not supervisor:frappe.throw('Supervisor verification required.',frappe.PermissionError)
        if user==doc.completed_by or frappe.db.exists('TruCMMS Work Execution',{'work_order':doc.name,'execution_cycle':doc.execution_cycle,'technician':user}):frappe.throw('Execution participants cannot verify their own work.',frappe.PermissionError)
        return 'Verified'
    if action in ('Accept Work','Accept on Behalf'):
        if doc.status!='Verified' or not doc.acceptance_required:frappe.throw('Only verified work requiring acceptance can be accepted.')
        if user==doc.completed_by or frappe.db.exists('TruCMMS Work Execution',{'work_order':doc.name,'execution_cycle':doc.execution_cycle,'technician':user}):frappe.throw('Execution participants cannot accept their own work.',frappe.PermissionError)
        if action=='Accept Work' and not requester:frappe.throw('Designated requester acceptance required.',frappe.PermissionError)
        if action=='Accept on Behalf' and not supervisor:frappe.throw('Supervisor acceptance with justification required.',frappe.PermissionError)
        return 'Accepted'
    if action=='Close Order':
        if not supervisor:frappe.throw('Supervisor closure required.',frappe.PermissionError)
        if doc.status!='Accepted' and not (doc.status=='Verified' and not doc.acceptance_required):frappe.throw('Verification and applicable acceptance are required before closure.')
        return 'Closed'
    if action=='Request Rework':
        if doc.status not in ('Technical Completed','Verified'):frappe.throw('Review completed or verified work before requesting rework.')
        if not supervisor and not requester:frappe.throw('Reviewer role required.',frappe.PermissionError)
        return 'Assigned'
    if action=='Hold Work':
        if not supervisor:frappe.throw('Supervisor hold required.',frappe.PermissionError)
        if doc.status not in ('Authorized','Assigned'):frappe.throw('Hold authorized or assigned work.')
        return 'On Hold'
    if action=='Resume Work':
        if not supervisor:frappe.throw('Supervisor resume required.',frappe.PermissionError)
        if doc.status!='On Hold' or doc.hold_from_state not in ('Authorized','Assigned'):frappe.throw('This order is not resumable.')
        if doc.hold_from_state=='Assigned':
            for row in allocations.active(doc):allocations.execution_context(doc,row.technician)
        return doc.hold_from_state
    if action=='Cancel Order':
        if not supervisor:frappe.throw('Supervisor cancellation required.',frappe.PermissionError)
        if doc.status not in ('Draft','Authorized','Assigned','On Hold','Technical Completed','Verified'):frappe.throw('This order cannot be cancelled.')
        return 'Cancelled'
    if action=='Reopen Order':
        if not supervisor:frappe.throw('Supervisor reopening required.',frappe.PermissionError)
        if doc.status!='Closed':frappe.throw('Only closed orders may be reopened.')
        return 'Authorized'
    frappe.throw('Unsupported lifecycle action.')

def validate_change(doc,old):
    from vanbags_maintenance import lifecycle as old_policy
    ctx=contract.context(doc)
    if not ctx:
        if old.status in ('Closed','Cancelled'):frappe.throw('Terminal history is immutable.',frappe.PermissionError)
        for field in old_policy.AUDIT+AUDIT+('execution_cycle',):
            if not contract.equal(doc.get(field),old.get(field),field):frappe.throw('Lifecycle audit is server controlled.')
        if doc.status!=old.status and (old.status,doc.status) not in (('Draft','Authorized'),('Authorized','Assigned')):frappe.throw('Use a controlled lifecycle action.',frappe.PermissionError)
        return
    allowed=set(ctx['allowed'])
    for field in wo.CONTEXT+('maintenance_request','requester','subject','scope','priority','origin_type','assigned_to','responsible_team','required_discipline','team_assignment')+wo.AUDIT+old_policy.AUDIT+AUDIT+('execution_cycle',):
        if not contract.equal(doc.get(field),old.get(field),field) and field not in allowed:frappe.throw('The action cannot alter unrelated authorized data.',frappe.PermissionError)
    if ctx['action'] in ('Replan Work','Reassign Work','Adopt C Policy','Designate Acceptor'):
        if doc.status!=old.status:frappe.throw('This action cannot change workflow state.')
    elif doc.status!=validate_action(old,ctx['action'],ctx['reason']):frappe.throw('Invalid lifecycle destination.')

@frappe.whitelist(methods=['POST'])
@contract.atomic
def perform(work_order,action,reason):
    from vanbags_maintenance import lifecycle as old_policy
    doc=locked_order(work_order)
    if doc.lifecycle_policy!='C1' and action!='Reopen Order':return old_policy.perform(work_order,action,reason)
    target=validate_action(doc,action,reason);before=doc.status;snapshot=doc.as_dict();stamp=now_datetime();user=frappe.session.user
    prefixes={'Complete Work':'completed','Verify Work':'verified','Accept Work':'accepted','Accept on Behalf':'accepted','Close Order':'closed','Request Rework':'rework','Hold Work':'held','Resume Work':'resumed','Cancel Order':'cancelled','Reopen Order':'reopened'}
    allowed=set(old_policy.AUDIT+AUDIT+('execution_cycle','has_review_history','hold_from_state'))
    rows=allocations.active(doc) if doc.lifecycle_policy=='C1' else []
    if action in ('Request Rework','Reopen Order'):
        archive(doc,action)
        doc.execution_cycle=(cint(doc.execution_cycle) or 1)+1
        for prefix in ('completed','verified','accepted','closed'):
            for suffix in ('by','on','reason'):doc.set(prefix+'_'+suffix,None)
        doc.acceptance_method=None
        if action=='Reopen Order':
            doc.lifecycle_policy='C1';contract.acceptance(doc);doc.assigned_to=None;doc.team_assignment=None
            doc.authorized_by=user;doc.authorized_on=stamp;doc.assigned_by=None;doc.assigned_on=None;doc.hold_from_state=None
            allowed.update(('lifecycle_policy','acceptance_policy_snapshot','acceptance_required','acceptance_user','assigned_to','team_assignment')+wo.AUDIT)
        allocations.archive_and_carry(doc,rows,reason,carry=action=='Request Rework')
    prefix=prefixes[action]
    for suffix,value in [('by',user),('on',stamp),('reason',reason.strip())]:doc.set(prefix+'_'+suffix,value)
    if action in ('Complete Work','Cancel Order','Reopen Order'):doc.has_review_history=1
    if action=='Verify Work' and not doc.acceptance_required:doc.acceptance_method='Not Applicable'
    if action in ('Accept Work','Accept on Behalf'):doc.acceptance_method='Requester' if action=='Accept Work' else 'Supervisor on behalf'
    if action=='Hold Work':doc.hold_from_state=before
    if action=='Resume Work':doc.hold_from_state=None
    doc.status=target;save(doc,action,reason,allowed);event(doc,action,before,reason,snapshot)
    return doc.as_dict()

@frappe.whitelist(methods=['POST'])
@contract.atomic
def replan(work_order,scheduled_start=None,scheduled_end=None,target_closure=None,reason=None):
    doc=locked_order(work_order)
    if not wo.supervisor():frappe.throw('Supervisor scheduling required.',frappe.PermissionError)
    if doc.lifecycle_policy!='C1' or doc.status not in ('Draft','Authorized','Assigned','On Hold'):frappe.throw('Reschedule open C work before completion.')
    if not (reason or '').strip():frappe.throw('Scheduling reason required.')
    snapshot=doc.as_dict()
    for f,value in zip(contract.SCHEDULE,(scheduled_start,scheduled_end,target_closure)):doc.set(f,value or None)
    save(doc,'Replan Work',reason,contract.SCHEDULE);event(doc,'Replan Work',doc.status,reason,snapshot);return doc.as_dict()

@frappe.whitelist(methods=['POST'])
@contract.atomic
def reassign(work_order,technician,reason,team=None,discipline=None):
    doc=locked_order(work_order)
    if not wo.supervisor():frappe.throw('Supervisor reassignment required.',frappe.PermissionError)
    if doc.lifecycle_policy!='C1' or not (doc.status=='Assigned' or doc.status=='On Hold' and doc.hold_from_state=='Assigned'):frappe.throw('Reassign assigned or paused-assigned C work only.')
    if not (reason or '').strip():frappe.throw('Reassignment reason required.')
    team=team or doc.responsible_team;discipline=discipline or doc.required_discipline
    if (technician,team,discipline)==(doc.assigned_to,doc.responsible_team,doc.required_discipline):frappe.throw('Choose a different assignment.')
    if team!=doc.responsible_team and any(r.technician!=doc.assigned_to for r in allocations.active(doc)):frappe.throw('End secondary allocations before changing the responsible team.')
    if technician!=doc.assigned_to and allocations.current(doc,technician):frappe.throw('End the existing secondary allocation before making it primary.')
    snapshot=doc.as_dict();old=allocations.current(doc,doc.assigned_to)
    if old:allocations.end(old,reason)
    doc.assigned_to=technician;doc.responsible_team=team;doc.required_discipline=discipline
    save(doc,'Reassign Work',reason,('assigned_to','responsible_team','required_discipline','team_assignment')+wo.AUDIT)
    event(doc,'Reassign Work',doc.status,reason,snapshot);return doc.as_dict()

@frappe.whitelist(methods=['POST'])
@contract.atomic
def adopt(work_order,reason,acceptance_user=None):
    doc=locked_order(work_order)
    if not wo.supervisor():frappe.throw('Supervisor adoption required.',frappe.PermissionError)
    if doc.lifecycle_policy=='C1' or doc.status not in ('Draft','Authorized','Assigned','Technical Completed'):frappe.throw('Adopt open legacy work before acceptance.')
    if not (reason or '').strip():frappe.throw('Adoption reason required.')
    if doc.status in ('Assigned','Technical Completed') and doc.team_policy!='Managed':frappe.throw('Adopt managed team eligibility first.')
    snapshot=doc.as_dict();doc.lifecycle_policy='C1';contract.acceptance(doc)
    if acceptance_user and doc.origin_type=='Direct':doc.acceptance_user=acceptance_user
    if doc.status!='Draft':contract.valid_acceptor(doc)
    save(doc,'Adopt C Policy',reason,('lifecycle_policy','acceptance_policy_snapshot','acceptance_required','acceptance_user'))
    event(doc,'Adopt C Policy',doc.status,reason,snapshot);return doc.as_dict()


def setup():
    from vanbags_maintenance import configuration
    configuration.setup()
    frappe.db.sql("UPDATE `tabTruCMMS Maintenance Work Order` SET lifecycle_policy='Legacy' WHERE COALESCE(lifecycle_policy,'')=''")
    frappe.db.sql("UPDATE `tabTruCMMS Site` SET acceptance_policy='By Origin' WHERE COALESCE(acceptance_policy,'')=''")
    frappe.db.add_unique(CYCLE,['work_order','execution_cycle'],'work_cycle_once')
    frappe.db.add_index(allocations.DT,['work_order','execution_cycle','technician','ended_on'],'work_active_allocation')
    name='TruCMMS Work Order Workflow C1'
    states=['Draft','Authorized','Assigned','On Hold','Technical Completed','Verified','Accepted','Closed','Cancelled']
    for state in states:
        if not frappe.db.exists('Workflow State',state):frappe.get_doc({'doctype':'Workflow State','workflow_state_name':state}).insert(ignore_permissions=True)
    edges=[('Draft','Authorize','Authorized',wo.SUPERVISOR,''),('Authorized','Assign','Assigned',wo.SUPERVISOR,''),('Assigned','Complete Work','Technical Completed',wo.TECHNICIAN,'')]
    legacy="doc.lifecycle_policy != 'C1'";current="doc.lifecycle_policy == 'C1'"
    for role,action in [('TruCMMS Requester','Accept Work'),(wo.SUPERVISOR,'Accept on Behalf')]:
        edges.extend([('Technical Completed',action,'Accepted',role,legacy),('Verified',action,'Accepted',role,current+' and doc.acceptance_required')])
    for role in ('TruCMMS Requester',wo.SUPERVISOR):
        edges.extend([('Technical Completed','Request Rework','Assigned',role,''),('Verified','Request Rework','Assigned',role,current)])
    edges.extend([('Technical Completed','Verify Work','Verified',wo.SUPERVISOR,current),('Accepted','Close Order','Closed',wo.SUPERVISOR,''),('Verified','Close Order','Closed',wo.SUPERVISOR,current+' and not doc.acceptance_required')])
    for state in ('Authorized','Assigned'):edges.append((state,'Hold Work','On Hold',wo.SUPERVISOR,current))
    for state in ('Authorized','Assigned'):edges.append(('On Hold','Resume Work',state,wo.SUPERVISOR,current+f" and doc.hold_from_state == '{state}'"))
    edges.append(('Closed','Reopen Order','Authorized',wo.SUPERVISOR,''))
    for state in ('Draft','Authorized','Assigned','On Hold','Technical Completed','Verified'):edges.append((state,'Cancel Order','Cancelled',wo.SUPERVISOR,'' if state not in ('On Hold','Verified') else current))
    edges += [(a,action,z,'System Manager',condition) for a,action,z,role,condition in list(edges) if role==wo.SUPERVISOR]
    for _,action,_,_,_ in edges:
        if not frappe.db.exists('Workflow Action Master',action):frappe.get_doc({'doctype':'Workflow Action Master','workflow_action_name':action}).insert(ignore_permissions=True)
    expected={(a,action,z,role,condition) for a,action,z,role,condition in edges}
    if frappe.db.exists('Workflow',name):
        flow=frappe.get_doc('Workflow',name)
        actual={(r.state,r.action,r.next_state,r.allowed,r.condition or '') for r in flow.transitions}
        if actual!=expected or {r.state for r in flow.states}!=set(states) or not flow.is_active or flow.document_type!=wo.DT or flow.workflow_state_field!='status' or any(str(r.doc_status)!='0' or r.allow_edit!=wo.SUPERVISOR for r in flow.states):frappe.throw('Custom C workflow requires explicit upgrade review.')
    else:
        original=frappe.get_doc('Workflow','TruCMMS Work Order Workflow')
        legacy_states={'Draft','Authorized','Assigned','Technical Completed','Accepted','Closed','Cancelled'}
        legacy_edges={(a,action,z,role) for a,action,z,role,condition in edges if a in legacy_states and z in legacy_states and action!='Reopen Order' and condition in ('',legacy)}
        actual_legacy={(r.state,r.action,r.next_state,r.allowed) for r in original.transitions}
        if actual_legacy!=legacy_edges or {r.state for r in original.states}!=legacy_states or original.document_type!=wo.DT or original.workflow_state_field!='status' or any(r.condition or not r.allow_self_approval for r in original.transitions) or any(str(r.doc_status)!='0' or r.allow_edit!=(wo.DISPATCHER if r.state=='Draft' else wo.SUPERVISOR) for r in original.states):frappe.throw('Custom legacy workflow requires explicit C upgrade review.')
        original.is_active=0;original.save(ignore_permissions=True)
        flow=frappe.get_doc({'doctype':'Workflow','workflow_name':name,'document_type':wo.DT,'is_active':1,'workflow_state_field':'status','send_email_alert':0,'states':[{'state':state,'doc_status':'0','allow_edit':wo.SUPERVISOR} for state in states],'transitions':[{'state':a,'action':action,'next_state':z,'allowed':role,'allow_self_approval':1,'condition':condition} for a,action,z,role,condition in edges]})
        flow.insert(ignore_permissions=True)
    frappe.clear_cache(doctype=wo.DT)


def history_query(dt,user=None):
    condition=wo.query(user)
    return f"EXISTS (SELECT 1 FROM `tab{wo.DT}` WHERE `tab{wo.DT}`.name=`tab{dt}`.work_order AND ({condition}))" if condition else ''
def cycle_query(user=None):return history_query(CYCLE,user)
def allocation_query(user=None):return history_query(allocations.DT,user)
def validate_share(doc,method=None):
    if doc.share_doctype in (CYCLE,allocations.DT):
        if doc.everyone:frappe.throw('Work history cannot be public.',frappe.PermissionError)
        from vanbags_maintenance.lifecycle import event_permission
        event_permission(frappe.get_doc(doc.share_doctype,doc.share_name),doc.user,'read')


@frappe.whitelist(methods=['POST'])
@contract.atomic
def designate_acceptor(work_order,user,reason):
    doc=locked_order(work_order)
    if not wo.supervisor():frappe.throw('Supervisor designation required.',frappe.PermissionError)
    if doc.lifecycle_policy!='C1' or doc.origin_type!='Direct' or doc.status!='Authorized':frappe.throw('Designate an acceptor for authorized direct work before execution.')
    if not (reason or '').strip():frappe.throw('Designation reason required.')
    snapshot=doc.as_dict();doc.acceptance_user=user;contract.valid_acceptor(doc)
    save(doc,'Designate Acceptor',reason,('acceptance_user',));event(doc,'Designate Acceptor',doc.status,reason,snapshot);return doc.as_dict()
