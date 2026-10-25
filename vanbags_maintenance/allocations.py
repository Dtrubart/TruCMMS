"""Explicit per-person, per-discipline allocation without team-wide visibility."""
import frappe
from frappe.utils import now_datetime,cint,get_datetime
from vanbags_maintenance import teams,work_orders as wo
from vanbags_maintenance.work_contract import atomic
DT='TruCMMS Work Allocation'

def current(order,user=None):
    if order.get('lifecycle_policy')!='C1':return None
    rows=frappe.get_all(DT,filters={'work_order':order.name,'execution_cycle':cint(order.execution_cycle),'technician':user or frappe.session.user,'ended_on':['is','not set']},fields=['name','technician','discipline','team','assigned_on','assigned_by','assignment'])
    if len(rows)>1:frappe.throw('Duplicate active allocation; administrative review required.')
    return rows[0] if rows else None

def active(order):
    return frappe.get_all(DT,filters={'work_order':order.name,'execution_cycle':cint(order.execution_cycle),'ended_on':['is','not set']},fields=['name','technician','discipline','team','assigned_on','assigned_by','assignment'])

def write(values):
    previous=frappe.flags.get('trucmms_allocation_write');frappe.flags.trucmms_allocation_write=True
    try:return frappe.get_doc({'doctype':DT,**values}).insert(ignore_permissions=True)
    finally:frappe.flags.trucmms_allocation_write=previous

def end(row,reason):
    rows=teams.locked_sql(f'SELECT * FROM `tab{DT}` WHERE name=%s FOR UPDATE',(row.name,),as_dict=True)
    doc=frappe.get_doc({'doctype':DT,**rows[0]})
    if doc.ended_on:frappe.throw('Allocation is already ended.')
    previous=frappe.flags.get('trucmms_allocation_write');frappe.flags.trucmms_allocation_write=True
    try:
        doc.ended_on=now_datetime();doc.ended_by=frappe.session.user;doc.reason=doc.reason+' | End: '+reason;doc.save(ignore_permissions=True)
    finally:frappe.flags.trucmms_allocation_write=previous

def ensure_primary(doc,method=None):
    if doc.get('lifecycle_policy')!='C1' or not (doc.status=='Assigned' or doc.status=='On Hold' and doc.hold_from_state=='Assigned') or not doc.assigned_to or current(doc,doc.assigned_to):return
    if not doc.team_assignment:frappe.throw('Managed team responsibility is required before C execution.')
    write({'work_order':doc.name,'company':doc.company,'site':doc.site,'execution_cycle':doc.execution_cycle,'technician':doc.assigned_to,'discipline':doc.required_discipline,'team':doc.responsible_team,'assignment':doc.team_assignment,'assigned_on':doc.assigned_on,'assigned_by':doc.assigned_by,'reason':'Primary authorized assignment'})

def execution_context(order,user):
    row=current(order,user)
    if not row:frappe.throw('An active current-cycle allocation is required.',frappe.PermissionError)
    context=frappe._dict(order.as_dict());context.required_discipline=row.discipline;context.responsible_team=row.team;context.assigned_to=user
    teams.eligibility(context,user,lock=True)
    return row

def assignment_start(order,user):
    row=current(order,user)
    return row.assigned_on if row else order.assigned_on

def participant_sql(user):
    return f"EXISTS (SELECT 1 FROM `tab{DT}` alloc WHERE alloc.work_order=`tab{wo.DT}`.name AND alloc.execution_cycle=`tab{wo.DT}`.execution_cycle AND alloc.technician={frappe.db.escape(user)} AND alloc.ended_on IS NULL)"

def archive_and_carry(order,rows,reason,carry=False):
    for row in rows:end(row,reason)
    if carry:
        for row in rows:
            write({'work_order':order.name,'company':order.company,'site':order.site,'execution_cycle':order.execution_cycle,'technician':row.technician,'discipline':row.discipline,'team':row.team,'assignment':row.assignment,'assigned_on':now_datetime(),'assigned_by':row.assigned_by,'reason':'Carry forward authorized assignment: '+reason})

def check_completion(order):
    rows=active(order)
    if not rows or not any(r.technician==order.assigned_to for r in rows):frappe.throw('Primary allocation is missing.')
    for row in rows:
        execution_context(order,row.technician)
        entries=teams.locked_sql("SELECT e.name,e.actual_end FROM `tabTruCMMS Work Execution` e WHERE e.work_order=%s AND e.execution_cycle=%s AND e.technician=%s AND NOT EXISTS (SELECT 1 FROM `tabTruCMMS Execution Adjustment` a WHERE a.execution=e.name) ORDER BY e.actual_end DESC,e.creation DESC LIMIT 1 FOR UPDATE",(order.name,order.execution_cycle,row.technician),as_dict=True)
        if not entries or get_datetime(entries[0].actual_end)<get_datetime(row.assigned_on):frappe.throw('Every active allocation requires current execution before completion.')
        entry=frappe.get_doc('TruCMMS Work Execution',entries[0].name)
        if any(t.result!='Completed' for t in entry.tasks):frappe.throw('Every active allocation must report completed tasks.')

@frappe.whitelist(methods=['POST'])
@atomic
def add(work_order,technician,discipline,reason):
    from vanbags_maintenance import work_cycle
    order=work_cycle.locked_order(work_order)
    if not wo.supervisor():frappe.throw('Supervisor required.',frappe.PermissionError)
    if order.lifecycle_policy!='C1' or order.status!='Assigned':frappe.throw('Add participants only to assigned C orders.')
    if not (reason or '').strip():frappe.throw('Allocation reason required.')
    if current(order,technician):frappe.throw('This technician already has an active allocation.')
    context=frappe._dict(order.as_dict());context.required_discipline=discipline;context.assigned_to=technician
    member,grant=teams.eligibility(context,technician,lock=True)
    previous=frappe.flags.get('trucmms_assignment_insert');frappe.flags.trucmms_assignment_insert=True
    try:
        assignment=frappe.get_doc({'doctype':teams.ASSIGN,'work_order':order.name,'company':order.company,'site':order.site,'team':order.responsible_team,'discipline':discipline,'technician':technician,'membership':member,'site_authorization':grant,'assigned_on':now_datetime(),'assigned_by':frappe.session.user,'reason':reason}).insert(ignore_permissions=True)
    finally:frappe.flags.trucmms_assignment_insert=previous
    row=write({'work_order':order.name,'company':order.company,'site':order.site,'execution_cycle':order.execution_cycle,'technician':technician,'discipline':discipline,'team':order.responsible_team,'assignment':assignment.name,'assigned_on':assignment.assigned_on,'assigned_by':frappe.session.user,'reason':reason})
    work_cycle.event(order,'Add Allocation',order.status,reason)
    return row.as_dict()

@frappe.whitelist(methods=['POST'])
@atomic
def remove(allocation,reason):
    from vanbags_maintenance import work_cycle
    origin=frappe.db.get_value(DT,allocation,'work_order')
    if not origin:frappe.throw('Allocation not found.',frappe.DoesNotExistError)
    order=work_cycle.locked_order(origin)
    rows=teams.locked_sql(f'SELECT * FROM `tab{DT}` WHERE name=%s FOR UPDATE',(allocation,),as_dict=True)
    row=frappe.get_doc({'doctype':DT,**rows[0]})
    if not wo.supervisor():frappe.throw('Supervisor required.',frappe.PermissionError)
    if order.lifecycle_policy!='C1' or not (order.status=='Assigned' or order.status=='On Hold' and order.hold_from_state=='Assigned') or row.execution_cycle!=order.execution_cycle or row.ended_on:frappe.throw('Only active current allocations can be removed.')
    if row.technician==order.assigned_to:frappe.throw('Use primary reassignment instead.')
    if not (reason or '').strip():frappe.throw('Removal reason required.')
    end(row,reason);work_cycle.event(order,'End Allocation',order.status,reason)
    return {'name':row.name}


@frappe.whitelist()
def mine(work_order):
    order=frappe.get_doc(wo.DT,work_order);order.check_permission('read')
    return current(order,frappe.session.user)


def validate_execution(order,entry,start,end):
    row=current(order,entry.technician)
    if not row or (entry.allocation,entry.discipline,entry.team)!=(row.name,row.discipline,row.team):frappe.throw('Execution allocation context is server controlled.')
    events=frappe.get_all('TruCMMS Work Event',filters={'work_order':order.name,'execution_cycle':order.execution_cycle,'action':['in',['Hold Work','Resume Work']]},fields=['action','occurred_on'],order_by='occurred_on asc')
    held=None
    for event in events:
        if event.action=='Hold Work':held=get_datetime(event.occurred_on)
        elif held:
            if start<get_datetime(event.occurred_on) and end>held:frappe.throw('Execution time cannot overlap a paused interval.')
            held=None
    if held and end>held:frappe.throw('Execution time cannot overlap an unreleased pause.')
