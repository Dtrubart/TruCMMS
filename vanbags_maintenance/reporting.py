"""Permission-aware operational registers and equipment history; no shared cache."""
from collections import defaultdict
from datetime import timedelta
import frappe
from frappe.utils import now_datetime,get_datetime,getdate,add_days,flt
from vanbags_maintenance import work_orders as wo
from vanbags_maintenance import adjustments as adj
EX='TruCMMS Work Execution'
EVENT='TruCMMS Work Event'


def visible(dt,filters,fields,order_by='creation asc'):
    if not frappe.has_permission(dt,'read'):return []
    return frappe.get_list(dt,filters=filters,fields=fields,order_by=order_by,limit_page_length=0)


def register(filters=None):
    filters=frappe._dict(filters or {})
    if not frappe.has_permission(wo.DT,'report'):frappe.throw('Work report permission required.',frappe.PermissionError)
    allowed={'All','Open','Overdue','Technical Completed','Accepted','Verified','On Hold','Closed','Cancelled','Unscheduled'}
    view=filters.get('view') or 'Open'
    if view not in allowed:frappe.throw('Invalid report view.')
    conditions={k:filters[k] for k in ('company','site','equipment','name') if filters.get(k)}
    if filters.get('work_order'):conditions['name']=filters.work_order
    if filters.get('from_date') and filters.get('to_date') and getdate(filters.from_date)>getdate(filters.to_date):frappe.throw('From date must not exceed to date.')
    if filters.get('from_date') and filters.get('to_date'):conditions['creation']=['between',[str(getdate(filters.from_date)),str(get_datetime(str(add_days(getdate(filters.to_date),1)))-timedelta(microseconds=1))]]
    elif filters.get('from_date'):conditions['creation']=['>=',getdate(filters.from_date)]
    elif filters.get('to_date'):conditions['creation']=['<',add_days(getdate(filters.to_date),1)]
    rows=visible(wo.DT,conditions,['name','maintenance_request','company','site','equipment','functional_location','subject','status','assigned_to','target_closure','completed_on','accepted_on','closed_on','creation','scheduled_start','scheduled_end','execution_cycle','lifecycle_policy','verified_on'])
    now=now_datetime()
    for row in rows:
        row.overdue=int(row.status not in ('Closed','Cancelled') and bool(row.target_closure) and get_datetime(row.target_closure)<now)
    if view=='Open':rows=[r for r in rows if r.status not in ('Closed','Cancelled')]
    elif view=='Overdue':rows=[r for r in rows if r.overdue]
    elif view=='Unscheduled':rows=[r for r in rows if not r.target_closure and r.status not in ('Closed','Cancelled')]
    elif view!='All':rows=[r for r in rows if r.status==view]
    names=[r.name for r in rows];totals=defaultdict(lambda:dict(recorded_minutes=0,voided_minutes=0,effective_minutes=0,execution_count=0,void_count=0))
    if names:
        entries=visible(EX,{'work_order':['in',names]},['name','work_order','actual_minutes'])
        voids={r.execution for r in visible(adj.DT,{'work_order':['in',names]},['execution'])}
        for entry in entries:
            t=totals[entry.work_order];minutes=flt(entry.actual_minutes)
            t['recorded_minutes']+=minutes;t['execution_count']+=1
            if entry.name in voids:t['voided_minutes']+=minutes;t['void_count']+=1
            else:t['effective_minutes']+=minutes
    for row in rows:row.update(totals[row.name])
    return rows


def work_register(filters=None):
    rows=register(filters)
    columns=[dict(fieldname=n,label=l,fieldtype=t,options=o,width=w) for n,l,t,o,w in [
        ('name','Work Order','Link',wo.DT,180),('status','Status','Data',None,150),('company','Company','Link','Company',150),('site','Site','Link','TruCMMS Site',150),
        ('equipment','Equipment','Link','VB Equipment',160),('subject','Subject','Data',None,220),('maintenance_request','Request','Link','TruCMMS Maintenance Request',170),
        ('execution_cycle','Current Cycle','Int',None,100),('scheduled_start','Scheduled Start','Datetime',None,170),('scheduled_end','Scheduled End','Datetime',None,170),('assigned_to','Technician','Link','User',180),('target_closure','Target Closure','Datetime',None,170),('overdue','Overdue','Check',None,80),
        ('recorded_minutes','Recorded Minutes','Float',None,140),('voided_minutes','Voided Minutes','Float',None,140),('effective_minutes','Effective Minutes','Float',None,145),('execution_count','Execution Entries','Int',None,120),('void_count','Voids','Int',None,80)]]
    summary=[dict(label=label,value=value,datatype=kind,indicator='Blue') for label,value,kind in [
        ('Orders',len(rows),'Int'),('Overdue',sum(r.overdue for r in rows),'Int'),('Closed',sum(r.status=='Closed' for r in rows),'Int'),
        ('Effective Minutes',sum(r.effective_minutes for r in rows),'Float'),('Voided Minutes',sum(r.voided_minutes for r in rows),'Float')]]
    return columns,rows,'Targets refer to final closure. Open includes pending acceptance/closure; no target means unscheduled.',None,summary


def equipment_history(filters=None):
    f=frappe._dict(filters or {})
    if not f.equipment:frappe.throw('Choose an equipment record.')
    equipment=frappe.get_doc('VB Equipment',f.equipment);equipment.check_permission('read')
    if not frappe.has_permission('VB Equipment','report'):frappe.throw('Equipment history report permission required.',frappe.PermissionError)
    rows=[]
    def add(dt,doc,when,detail,order=None,request=None):
        rows.append(dict(record_type=dt,record=doc.name,occurred_on=when,description=detail,work_order=order,maintenance_request=request,company=doc.company,site=doc.site))
    requests=visible('TruCMMS Maintenance Request',{'equipment':f.equipment},['name','creation','company','site','status','description'])
    for r in requests:add('TruCMMS Maintenance Request',r,r.creation,r.status+': '+r.description,request=r.name)
    orders=register({'equipment':f.equipment,'view':'All'}) if frappe.has_permission(wo.DT,'report') else []
    for o in orders:add(wo.DT,o,o.creation,o.status+': '+o.subject,order=o.name,request=o.maintenance_request)
    names=[o.name for o in orders]
    if names:
        for e in visible(EX,{'work_order':['in',names]},['name','work_order','company','site','actual_end','findings','actual_minutes']):
            add(EX,e,e.actual_end,e.findings+' ('+str(e.actual_minutes)+' recorded minutes)',order=e.work_order)
        for e in visible(EVENT,{'work_order':['in',names]},['name','work_order','company','site','occurred_on','action','reason']):add(EVENT,e,e.occurred_on,e.action+': '+e.reason,order=e.work_order)
        for e in visible('TruCMMS Team Assignment',{'work_order':['in',names]},['name','work_order','company','site','assigned_on','team','discipline','technician']):add('TruCMMS Team Assignment',e,e.assigned_on,e.team+' / '+e.discipline+': '+e.technician,order=e.work_order)
        for e in visible('TruCMMS Work Cycle',{'work_order':['in',names]},['name','work_order','company','site','recorded_on','execution_cycle','ended_action']):add('TruCMMS Work Cycle',e,e.recorded_on,'Cycle '+str(e.execution_cycle)+': '+e.ended_action,order=e.work_order)
        for e in visible(adj.DT,{'work_order':['in',names]},['name','work_order','company','site','occurred_on','execution','reason']):add(adj.DT,e,e.occurred_on,'Void '+e.execution+': '+e.reason,order=e.work_order)
    for e in visible('TruCMMS Equipment Installation',{'equipment':f.equipment},['name','company','site','location','effective_from','effective_until','entry_type']):
        add('TruCMMS Equipment Installation',e,e.effective_from,e.entry_type+': '+(e.location or 'Mobile / site custody')+(' — removed '+str(e.effective_until) if e.effective_until else ' — active'))
    for e in visible('TruCMMS Asset Event',{'equipment':f.equipment},['name','company','site','effective_on','action','reason']):add('TruCMMS Asset Event',e,e.effective_on,e.action+': '+e.reason)
    rows.sort(key=lambda r:(get_datetime(r['occurred_on']),r['record']))
    columns=[dict(fieldname=n,label=l,fieldtype=t,options=o,width=w) for n,l,t,o,w in [
        ('occurred_on','Occurred','Datetime',None,170),('record_type','Record Type','Link','DocType',210),('record','Record','Dynamic Link','record_type',180),
        ('description','Description','Data',None,400),('work_order','Work Order','Link',wo.DT,170),('maintenance_request','Request','Link','TruCMMS Maintenance Request',170),('company','Historical Company','Link','Company',160),('site','Historical Site','Link','TruCMMS Site',140)]]
    return columns,rows,'History is limited to authorized records and retains their original organizational context.'
