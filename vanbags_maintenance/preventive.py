"""Calendar/usage/condition obligations, explicit release gates and R1 order provider."""
import hashlib,json
from datetime import datetime,timedelta,timezone
from dateutil.relativedelta import relativedelta
import frappe
from frappe.utils import getdate,get_datetime,now_datetime,cint
from vanbags_maintenance import r2_records as r,organization as org,teams,job_plans as jp,configuration,meters
from vanbags_maintenance.timezones import zone
from vanbags_maintenance.work_contract import atomic

PLAN='TruCMMS PM Plan';OCC='TruCMMS PM Occurrence'
CONFIG=('code','plan_name','company','site','equipment','component','procedure_revision','schedule_type','calendar_policy','anchor_date','end_date','frequency','interval','time_of_day','duration_minutes','horizon_days','meter','meter_metric_key','trigger_kind','usage_interval','lower_threshold','upper_threshold','release_mode','release_event','release_scope','include_corrective_work','control_group','max_active','lead_days','priority','responsible_team','required_discipline','acceptance_user','automation_enabled','automation_user')
STATE=('status','operating_timezone','configuration_snapshot','procedure_snapshot','approved_by','approved_on','last_reason','last_evaluated_on','last_error','baseline_reading','baseline_total','next_trigger_total','condition_latched','trigger_sequence','next_due_date','next_due_key','baseline_occurrence')
PM_FIELDS=('pm_plan','pm_occurrence','pm_finding','pm_procedure_snapshot','pm_started_on','pm_started_by')

def config(doc):return json.loads(json.dumps({k:doc.get(k) for k in CONFIG},default=str))

def validate_plan(doc):
    internal=frappe.flags.get('trucmms_r2_write');old=doc.get_doc_before_save()
    if not internal:r.editor()
    org.validate_context(doc)
    if not doc.code or len(doc.code)>64 or not (doc.plan_name or '').strip():frappe.throw('Plan code (maximum 64 characters) and name are required.')
    if old and (old.code!=doc.code or (old.company,old.site)!=(doc.company,doc.site)):frappe.throw('Plan identity and organizational scope are permanent.')
    if not internal:
        if not old and any(doc.get(k) for k in ('trigger_sequence','condition_latched','baseline_total','next_trigger_total')):frappe.throw('New plan runtime counters are server controlled.')
        if old and any(doc.get(k)!=old.get(k) for k in STATE):frappe.throw('Use controlled plan activation, pause and retirement actions.')
        if not old and (doc.status not in (None,'','Draft') or any(doc.get(k) for k in STATE if k not in ('status','trigger_sequence','condition_latched','baseline_total','next_trigger_total'))):frappe.throw('New plans must be unapproved drafts.')
        if not old:doc.status='Draft'
        if old and old.status!='Draft' and config(doc)!=config(old):frappe.throw('Approved plan configuration is frozen; retire it and create a replacement plan.')
    if old and old.status!='Draft':return
    validate_target(doc)
    revision=frappe.get_doc(jp.REVISION,doc.procedure_revision);revision.check_permission('read')
    if revision.status!='Approved' or (revision.company,revision.site)!=(doc.company,doc.site):frappe.throw('Choose an approved procedure revision in the same Company/Site.')
    if doc.schedule_type not in ('Calendar','Meter'):frappe.throw('Choose Calendar or Meter scheduling.')
    if doc.release_mode not in ('Manual','Automatic') or doc.release_event not in ('Started','Verified','Closed') or doc.release_scope not in ('Plan','Equipment','Component','Group'):frappe.throw('Invalid release policy.')
    if not 1<=cint(doc.max_active)<=100 or not 0<=cint(doc.lead_days)<=366 or not 1<=cint(doc.horizon_days)<=366 or not 1<=cint(doc.duration_minutes)<=525600:frappe.throw('Choose bounded release and planning horizons.')
    if doc.release_scope=='Component' and not doc.component or doc.release_scope=='Group' and not (doc.control_group or '').strip():frappe.throw('Component/group release control requires its explicit identity.')
    if doc.calendar_policy not in ('Fixed','After Completion') or doc.frequency not in ('Days','Weeks','Months') or not 1<=cint(doc.interval)<=10000:frappe.throw('Invalid calendar interval.')
    if doc.schedule_type=='Calendar':
        if not doc.anchor_date:frappe.throw('A calendar anchor date is required.')
        if doc.end_date and getdate(doc.end_date)<getdate(doc.anchor_date):frappe.throw('Plan end precedes its anchor.')
        if getdate(doc.anchor_date)<getdate()-timedelta(days=366):frappe.throw('Declare a recent baseline date rather than generating years of invented maintenance obligations.')
    else:
        meter=meters.meter(doc.meter,lock=False)
        if (meter.company,meter.site,meter.equipment,meter.component or None)!=(doc.company,doc.site,doc.equipment,doc.component or None):frappe.throw('Trigger meter must belong to the same maintained target.')
        definition=next((x for x in revision.measurements if x.metric_key==doc.meter_metric_key),None)
        if not definition or (definition.unit,definition.metric_kind)!=(meter.unit,meter.metric_kind):frappe.throw('Map the trigger meter to a procedure measurement with matching units and semantics.')
        if doc.trigger_kind not in ('Usage','Below','Above','Outside'):frappe.throw('Invalid meter trigger.')
        if doc.trigger_kind=='Usage':
            if meter.metric_kind!='Cumulative':frappe.throw('Usage intervals require a cumulative meter.')
            jp.finite(doc.usage_interval,'Usage interval',positive=True)
        else:
            if meter.metric_kind=='Cumulative':frappe.throw('Condition thresholds require a condition/rate meter.')
            jp.finite(doc.lower_threshold or 0,'Lower threshold');jp.finite(doc.upper_threshold or 0,'Upper threshold')
            if doc.trigger_kind=='Outside' and (doc.lower_threshold or 0)>(doc.upper_threshold or 0):frappe.throw('Lower threshold exceeds upper threshold.')
    if doc.responsible_team:
        team=frappe.get_doc('TruCMMS Maintenance Team',doc.responsible_team);team.check_permission('read')
        if team.company!=doc.company:frappe.throw('Responsible team belongs to another Company.')
    if doc.automation_enabled:automation_identity(doc)

def validate_target(doc):
    equipment=frappe.get_doc('VB Equipment',doc.equipment);equipment.check_permission('read')
    if (equipment.company,equipment.site)!=(doc.company,doc.site):frappe.throw('The equipment must currently belong to the plan Company/Site.')
    if doc.component:
        component=frappe.get_doc('TruCMMS Component',doc.component);component.check_permission('read')
        if component.disabled or component.equipment!=doc.equipment:frappe.throw('The component is no longer installed on the plan equipment; explicitly replace/retire this plan.')

def automation_identity(doc):
    user=doc.automation_user
    if not user or user=='Administrator' or not frappe.db.get_value('User',user,'enabled') or 'TruCMMS Supervisor' not in frappe.get_roles(user) or not org.in_scope(doc,user):frappe.throw('Automation requires an explicit enabled supervisor identity scoped to this Company/Site; implicit Administrator is not permitted.')

def locked(name):
    scope=frappe.db.get_value(PLAN,name,['company','site'],as_dict=True)
    if not scope:frappe.throw('Preventive plan not found.',frappe.DoesNotExistError)
    # Shared release serialization precedes order locking, including C1 actions.
    teams.locked_sql('SELECT name FROM `tabTruCMMS Site` WHERE name=%s FOR UPDATE',(scope.site,))
    doc=teams.locked_document(PLAN,name);doc.check_permission('read');return doc

def lock_order_scope(name):
    plan=frappe.db.get_value('TruCMMS Maintenance Work Order',name,'pm_plan')
    if plan:locked(plan)

def local_day(doc,stamp):
    source=zone(frappe.db.get_single_value('System Settings','time_zone') or 'UTC')
    target=zone(doc.operating_timezone or frappe.db.get_value('TruCMMS Site',doc.site,'time_zone'))
    return get_datetime(stamp).replace(tzinfo=source).astimezone(target).date()

def local_today(doc):return local_day(doc,now_datetime())

def advance(doc,day,n=1):
    kw={dict(Days='days',Weeks='weeks',Months='months')[doc.frequency]:cint(doc.interval)*n}
    return getdate(day)+relativedelta(**kw)

def calendar_dates(doc,start,end):
    start,end=getdate(start),getdate(end)
    if end<start or (end-start).days>366:frappe.throw('Choose an inclusive date window of at most 367 days.')
    anchor=getdate(doc.anchor_date)
    if doc.calendar_policy=='After Completion':
        due=getdate(doc.next_due_date or anchor)
        return [due] if start<=due<=end and (not doc.end_date or due<=getdate(doc.end_date)) else []
    if doc.frequency=='Months':n=max(0,((start.year-anchor.year)*12+start.month-anchor.month)//cint(doc.interval)-1)
    else:n=max(0,(start-anchor).days//(cint(doc.interval)*(7 if doc.frequency=='Weeks' else 1))-1)
    result=[]
    while True:
        day=advance(doc,anchor,n);n+=1
        if day>end or doc.end_date and day>getdate(doc.end_date):break
        if day>=start:result.append(day)
        if len(result)>500:frappe.throw('Preview exceeds 500 occurrences; narrow the window.')
    return result

@frappe.whitelist(methods=['GET','POST'])
def preview(plan,from_date=None,to_date=None):
    doc=frappe.get_doc(PLAN,plan);doc.check_permission('read')
    start=getdate(from_date) if from_date else local_today(doc);end=getdate(to_date) if to_date else start+timedelta(days=cint(doc.horizon_days))
    if doc.schedule_type!='Calendar':return {'rows':[],'message':'Meter plans have no invented future calendar dates.'}
    return {'rows':[{'plan':doc.name,'equipment':doc.equipment,'due':str(day),'kind':'Forecast','work_order':None} for day in calendar_dates(doc,start,end)],'timezone':doc.operating_timezone or frappe.db.get_value('TruCMMS Site',doc.site,'time_zone')}

def occurrence(doc,source,due,reading=None,total=None):
    identity='PMO-'+hashlib.sha256((doc.name+'|'+source).encode()).hexdigest()
    if teams.locked_sql(f'SELECT name FROM `tab{OCC}` WHERE name=%s FOR UPDATE',(identity,)):return teams.locked_document(OCC,identity)
    doc.trigger_sequence=cint(doc.trigger_sequence)+1;r.save(doc)
    row=r.create(OCC,occurrence_key=identity,plan=doc.name,company=doc.company,site=doc.site,equipment=doc.equipment,component=doc.component,subject=doc.plan_name,original_due=due,planned_for=due,status='Planned',trigger_reading=reading,trigger_total=total,source_key=source,sequence=doc.trigger_sequence,procedure_snapshot=doc.procedure_snapshot,recorded_on=now_datetime())
    r.event(row,'Plan Occurrence','Materialized approved preventive obligation',source=source,due=due)
    return row

def _materialize(doc,until=None):
    if doc.status!='Active':frappe.throw('Only active plans materialize obligations.')
    validate_target(doc)
    if doc.schedule_type=='Meter':return evaluate_meter(doc)
    today=local_today(doc);end=getdate(until) if until else today+timedelta(days=cint(doc.horizon_days))
    if end>today+timedelta(days=366):frappe.throw('Materialization is bounded to one year ahead.')
    if doc.calendar_policy=='After Completion':
        if frappe.db.exists(OCC,{'plan':doc.name,'status':['in',['Planned','Released']]}):return []
        due=getdate(doc.next_due_date or doc.anchor_date)
        if due>end or doc.end_date and due>getdate(doc.end_date):return []
        return [occurrence(doc,doc.next_due_key or 'initial:'+str(due),due).name]
    start=max(getdate(doc.anchor_date),today-timedelta(days=366))
    # Two bounded windows allow the initial historical baseline plus future year.
    dates=calendar_dates(doc,start,min(end,start+timedelta(days=366)))
    if end>start+timedelta(days=366):dates+=calendar_dates(doc,start+timedelta(days=367),end)
    return [occurrence(doc,'calendar:'+str(day),day).name for day in dates]

@frappe.whitelist(methods=['POST'])
@atomic
def materialize(plan,until=None):
    r.editor();doc=locked(plan)
    return {'occurrences':_materialize(doc,until),'orders_created':0}

@frappe.whitelist(methods=['POST'])
@atomic
def activate(plan,reason,baseline_reading=None):
    r.supervisor();doc=locked(plan);reason=r.reason(reason)
    if doc.status!='Draft':frappe.throw('Activate a draft plan.')
    validate_plan(doc)
    doc.procedure_snapshot=json.dumps(jp.approved_snapshot(doc.procedure_revision),sort_keys=True,ensure_ascii=False)
    doc.operating_timezone=frappe.db.get_value('TruCMMS Site',doc.site,'time_zone')
    configuration.validate_zone(doc.operating_timezone)
    if doc.schedule_type=='Calendar':due_instant(doc,doc.anchor_date)
    doc.configuration_snapshot=json.dumps(config(doc),sort_keys=True)
    doc.status='Active';doc.approved_by=frappe.session.user;doc.approved_on=now_datetime();doc.last_reason=reason
    if doc.schedule_type=='Meter':
        meter=meters.meter(doc.meter);reading=meters.latest(meter,fresh=True)
        if baseline_reading:
            base=frappe.get_doc(meters.READING,baseline_reading);base.check_permission('read')
            if base.meter!=meter.name or meters.corrected(base.name) or base.actual_on>reading.actual_on:frappe.throw('Choose a valid historical reading of this meter as the declared initial baseline.')
        else:base=reading
        doc.baseline_reading=base.name;doc.baseline_total=base.total_value
        doc.next_trigger_total=float(base.total_value or 0)+float(doc.usage_interval or 0)
    r.save(doc);r.event(doc,'Activate Plan',reason,initial_baseline=doc.baseline_reading)
    return {'name':doc.name,'occurrences':_materialize(doc),'orders_created':0}

@frappe.whitelist(methods=['POST'])
@atomic
def disposition(plan,action,reason):
    r.supervisor();doc=locked(plan);reason=r.reason(reason)
    allowed={('Active','Pause'):'Paused',('Paused','Resume'):'Active',('Active','Retire'):'Retired',('Paused','Retire'):'Retired',('Draft','Retire'):'Retired'}
    target=allowed.get((doc.status,action))
    if not target:frappe.throw('Invalid plan disposition.')
    if target=='Active':validate_target(doc)
    doc.status=target;doc.last_reason=reason;r.save(doc);r.event(doc,action+' Plan',reason)
    return {'name':doc.name,'status':doc.status}

def violated(doc,value):
    if doc.trigger_kind=='Below':return value<=float(doc.lower_threshold or 0)
    if doc.trigger_kind=='Above':return value>=float(doc.upper_threshold or 0)
    return value<float(doc.lower_threshold or 0) or value>float(doc.upper_threshold or 0)

def evaluate_meter(doc):
    meter=meters.meter(doc.meter);reading=meters.latest(meter,fresh=True)
    if doc.baseline_reading and meters.corrected(doc.baseline_reading):frappe.throw('The validated baseline reading was corrected; a reasoned rebase is required.')
    pending=frappe.db.get_value(OCC,{'plan':doc.name,'status':['in',['Planned','Released']]},'name')
    if pending:return [pending]
    if doc.trigger_kind=='Usage':
        if float(reading.total_value)<float(doc.next_trigger_total):return []
        source='usage:'+str(doc.next_trigger_total)+':'+str(doc.baseline_reading)
        return [occurrence(doc,source,local_today(doc),reading.name,doc.next_trigger_total).name]
    alarm=violated(doc,float(reading.value))
    if not alarm:
        if doc.condition_latched:doc.condition_latched=0;r.save(doc)
        return []
    if doc.condition_latched:return []
    doc.condition_latched=1;r.save(doc)
    return [occurrence(doc,'condition:'+str(cint(doc.trigger_sequence)+1)+':'+reading.name,local_today(doc),reading.name).name]

@frappe.whitelist(methods=['POST'])
@atomic
def rebase(plan,reading,reason):
    r.supervisor();doc=locked(plan);reason=r.reason(reason)
    if doc.schedule_type!='Meter' or doc.trigger_kind!='Usage':frappe.throw('Only usage plans have an explicit maintenance baseline.')
    source=frappe.get_doc(meters.READING,reading);source.check_permission('read');meter=meters.meter(doc.meter);current=meters.latest(meter,fresh=True)
    if source.meter!=meter.name or meters.corrected(source.name) or source.actual_on>current.actual_on:frappe.throw('Choose a valid reading of this meter.')
    if frappe.db.exists(OCC,{'plan':doc.name,'status':['in',['Planned','Released']]}):frappe.throw('Resolve pending obligations before rebasing; they must not disappear silently.')
    before=doc.baseline_reading;doc.baseline_reading=source.name;doc.baseline_total=source.total_value;doc.next_trigger_total=float(source.total_value)+float(doc.usage_interval);r.save(doc);r.event(doc,'Declare Usage Baseline',reason,previous=before,reading=source.name)
    return doc.as_dict()

@frappe.whitelist(methods=['POST'])
@atomic
def renew_condition(plan,reason):
    r.supervisor();doc=locked(plan);reason=r.reason(reason)
    if doc.status!='Active' or doc.schedule_type!='Meter' or doc.trigger_kind=='Usage':frappe.throw('Only active condition plans support explicit renewed intervention.')
    pending=frappe.db.get_value(OCC,{'plan':plan,'status':['in',['Planned','Released']]},'name')
    if pending:return {'occurrences':[pending]}
    doc.condition_latched=0;r.save(doc);r.event(doc,'Renew Condition Intervention',reason)
    return {'occurrences':evaluate_meter(doc)}

def get_occurrence(name):
    plan=frappe.db.get_value(OCC,name,'plan')
    if not plan:frappe.throw('Occurrence not found.',frappe.DoesNotExistError)
    doc=locked(plan);row=teams.locked_document(OCC,name);row.check_permission('read');return doc,row

def slot_orders(doc,exclude=None):
    from vanbags_maintenance.work_orders import DT
    filters=['w.company=%s','w.site=%s'];values=[doc.company,doc.site]
    if not (doc.release_scope=='Equipment' and doc.include_corrective_work):filters.append('w.pm_plan IS NOT NULL')
    if doc.release_scope=='Plan':filters.append('w.pm_plan=%s');values.append(doc.name)
    elif doc.release_scope=='Equipment':filters.append('w.equipment=%s');values.append(doc.equipment)
    elif doc.release_scope=='Component':filters.append('p.component=%s');values.append(doc.component)
    else:filters.append('p.control_group=%s AND p.release_scope=%s');values.extend([doc.control_group,'Group'])
    if exclude:filters.append('w.name!=%s');values.append(exclude)
    rows=teams.locked_sql(f"SELECT w.name,w.status,w.pm_started_on FROM `tab{DT}` w LEFT JOIN `tab{PLAN}` p ON p.name=w.pm_plan WHERE "+' AND '.join(filters)+' FOR UPDATE',tuple(values),as_dict=True)
    blocked=[]
    for row in rows:
        if row.status in ('Closed','Cancelled'):continue
        if doc.release_event=='Verified' and row.status in ('Verified','Accepted'):continue
        effective=frappe.db.sql('SELECT e.name FROM `tabTruCMMS Work Execution` e WHERE e.work_order=%s AND NOT EXISTS (SELECT 1 FROM `tabTruCMMS Execution Adjustment` a WHERE a.execution=e.name) LIMIT 1',(row.name,))
        if doc.release_event=='Started' and (row.pm_started_on or effective or row.status in ('Technical Completed','Verified','Accepted')):continue
        blocked.append(row.name)
    return blocked

def due_instant(doc,day):
    wall=datetime.combine(getdate(day),datetime.min.time())
    time=str(doc.time_of_day or '09:00:00');hours,minutes,*seconds=time.split(':')
    wall+=timedelta(hours=int(hours),minutes=int(minutes),seconds=float(seconds[0]) if seconds else 0)
    tz=zone(doc.operating_timezone);candidates=[]
    for fold in (0,1):
        local=wall.replace(tzinfo=tz,fold=fold)
        if local.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None)==wall:candidates.append(local)
    if not candidates or len({x.utcoffset() for x in candidates})>1:frappe.throw('The planned local time is missing or ambiguous; explicitly postpone this occurrence to a valid date/time policy.')
    system=zone(frappe.db.get_single_value('System Settings','time_zone') or 'UTC')
    return candidates[0].astimezone(system).replace(tzinfo=None)

@frappe.whitelist(methods=['POST'])
@atomic
def release(occurrence_name,reason,override=0):
    r.editor();doc,row=get_occurrence(occurrence_name);reason=r.reason(reason);override=cint(override)
    if row.work_order:
        order=teams.locked_document('TruCMMS Maintenance Work Order',row.work_order);order.check_permission('read');return order.as_dict()
    if doc.status!='Active' or row.status!='Planned':frappe.throw('Only planned occurrences of active plans can be released.')
    validate_target(doc)
    revision=frappe.get_doc(jp.REVISION,doc.procedure_revision);revision.check_permission('read')
    if revision.status!='Approved' or frappe.db.get_value(jp.PLAN,revision.job_plan,'disabled'):frappe.throw('The procedure was retired/disabled; approve a replacement plan before releasing new work.')
    if json.loads(doc.procedure_snapshot)!=jp.approved_snapshot(doc.procedure_revision):frappe.throw('Procedure snapshot integrity mismatch.')
    blockers=[]
    if getdate(row.planned_for)>local_today(doc)+timedelta(days=cint(doc.lead_days)):blockers.append('outside anticipation window')
    if len(slot_orders(doc))>=cint(doc.max_active):blockers.append('active-work limit')
    earlier=frappe.db.exists(OCC,{'plan':doc.name,'sequence':['<',row.sequence],'status':'Planned'})
    if earlier:blockers.append('an earlier occurrence is still planned; explicitly skip or resolve it')
    if doc.schedule_type=='Meter':
        reading=meters.latest(meters.meter(doc.meter),fresh=True)
        if doc.trigger_kind=='Usage' and float(reading.total_value)<float(row.trigger_total):blockers.append('usage threshold no longer reached')
        elif doc.trigger_kind!='Usage' and not violated(doc,float(reading.value)):blockers.append('condition is no longer present')
    if blockers:
        if not override:frappe.throw('Release blocked: '+', '.join(blockers)+'. Supervisor exception requires an explicit reason.')
        r.supervisor()
    elif override:r.supervisor()
    from vanbags_maintenance.work_contract import create_origin
    start=due_instant(doc,row.planned_for)
    provider={'origin':'Preventive','pm_plan':doc.name,'pm_occurrence':row.name,'pm_procedure_snapshot':row.procedure_snapshot,'responsible_team':doc.responsible_team,'required_discipline':doc.required_discipline,'scheduled_start':start,'scheduled_end':start+timedelta(minutes=cint(doc.duration_minutes)),'target_closure':start+timedelta(minutes=cint(doc.duration_minutes))}
    order=create_origin(doc.company,doc.site,row.subject,'\n'.join(t['task_code']+': '+t['instructions'] for t in json.loads(row.procedure_snapshot)['tasks']),doc.priority,row.name,reason,equipment=doc.equipment,acceptance_user=doc.acceptance_user,provider=provider)
    row.work_order=order['name'];row.status='Released';row.last_reason=reason;r.save(row);r.event(row,'Release Preventive Order',reason,work_order=row.work_order,override=bool(override),blockers=blockers)
    return order

@frappe.whitelist(methods=['POST'])
@atomic
def change_occurrence(occurrence_name,action,reason,planned_for=None):
    r.supervisor();doc,row=get_occurrence(occurrence_name);reason=r.reason(reason)
    if row.status!='Planned':frappe.throw('Use the order lifecycle for already released work; completed obligations cannot be rewritten.')
    if action=='Postpone':
        if not planned_for:frappe.throw('Choose a new planned date.')
        row.planned_for=getdate(planned_for)
    elif action in ('Skip','Cancel'):row.status='Skipped' if action=='Skip' else 'Cancelled'
    else:frappe.throw('Unknown occurrence disposition.')
    row.last_reason=reason;r.save(row);r.event(row,action+' Occurrence',reason,original_due=row.original_due,planned_for=row.planned_for)
    if action in ('Skip','Cancel'):next_after_disposition(doc,row,'skipped')
    return row.as_dict()

def next_after_disposition(doc,row,key):
    if doc.schedule_type=='Calendar' and doc.calendar_policy=='After Completion':
        doc.next_due_date=advance(doc,row.original_due);doc.next_due_key=key+':'+row.name+':'+str(doc.next_due_date);r.save(doc)
        if doc.status=='Active':_materialize(doc)
    elif doc.schedule_type=='Meter' and doc.trigger_kind=='Usage':
        doc.next_trigger_total=float(row.trigger_total or doc.next_trigger_total)+float(doc.usage_interval);r.save(doc)

def validate_order(doc,old):
    if not old:
        provider=frappe.flags.get('trucmms_origin_provider')
        if doc.origin_type in ('Preventive','Inspection'):
            if not provider or provider.get('origin')!=doc.origin_type:frappe.throw('Use the controlled preventive/inspection provider.',frappe.PermissionError)
            for field in PM_FIELDS:
                if doc.get(field)!=provider.get(field):frappe.throw('Provider provenance must match the controlled source.')
        elif any(doc.get(k) for k in PM_FIELDS):frappe.throw('Direct/request orders cannot forge preventive provenance.')
    else:
        action=frappe.flags.get('trucmms_c_action') or {}
        for field in PM_FIELDS:
            if str(doc.get(field) or '')!=str(old.get(field) or '') and not (action.get('name')==doc.name and field in action.get('allowed',())):frappe.throw('Preventive origin and start audit are immutable.',frappe.PermissionError)

@frappe.whitelist(methods=['POST'])
@atomic
def start_work(work_order,reason):
    lock_order_scope(work_order)
    from vanbags_maintenance import execution,work_cycle
    order=execution.order_for_recording(work_order)
    if not order.pm_occurrence:frappe.throw('This explicit preventive start action requires a preventive order.')
    if order.pm_started_on:return order.as_dict()
    reason=r.reason(reason);order.pm_started_on=now_datetime();order.pm_started_by=frappe.session.user
    work_cycle.save(order,'Start Preventive Work',reason,('pm_started_on','pm_started_by'));work_cycle.event(order,'Start Preventive Work',order.status,reason)
    kick(order.pm_plan)
    return order.as_dict()

def pre_transition(order,action):
    if not order.pm_occurrence:return
    if action in ('Request Rework','Reopen Order'):
        plan,row=get_occurrence(order.pm_occurrence)
        if row.status=='Completed':
            if plan.baseline_occurrence and plan.baseline_occurrence!=row.name:frappe.throw('Later maintenance already advanced the baseline; reconcile it explicitly before reopening this older work.')
            successors=frappe.get_all(OCC,filters={'plan':plan.name,'source_key':['like','after:'+row.name+':%']},fields=['name','status'])
            if any(x.status in ('Released','Completed') for x in successors):frappe.throw('Resolve the released successor before reopening this maintenance cycle.')
    if action=='Complete Work':
        from vanbags_maintenance.inspections import check_completion
        check_completion(order)
    if action=='Verify Work':
        from vanbags_maintenance.inspections import open_findings
        if open_findings(order):frappe.throw('Review open inspection findings before validating this maintenance.')

def order_updated(order,method=None):
    if not order.pm_occurrence:return
    old=order.get_doc_before_save()
    if not old or old.status==order.status:return
    plan,row=get_occurrence(order.pm_occurrence)
    if order.status=='Verified' and row.status!='Completed':
        from vanbags_maintenance.inspections import maintenance_actual
        actual,reading=maintenance_actual(order,plan)
        row.baseline_before=json.dumps({k:str(plan.get(k)) if plan.get(k) is not None else None for k in ('baseline_reading','baseline_total','next_trigger_total','baseline_occurrence','next_due_date','next_due_key')})
        row.status='Completed';row.completed_actual_on=actual;row.completion_reading=reading.name if reading else None;r.save(row)
        plan.baseline_occurrence=row.name
        if reading:plan.baseline_reading=reading.name;plan.baseline_total=reading.total_value;plan.next_trigger_total=float(reading.total_value)+float(plan.usage_interval or 0)
        if plan.schedule_type=='Calendar' and plan.calendar_policy=='After Completion':
            actual_day=local_day(plan,actual);plan.next_due_date=advance(plan,actual_day);plan.next_due_key='after:'+row.name+':C'+str(order.execution_cycle)+':'+str(plan.next_due_date)
        r.save(plan);r.event(row,'Validate Preventive Maintenance',order.verified_reason or 'Independent technical verification',actual_end=actual,reading=row.completion_reading)
        if plan.status=='Active' and plan.schedule_type=='Calendar' and plan.calendar_policy=='After Completion':_materialize(plan)
    elif order.status=='Cancelled' and row.status!='Cancelled':
        row.status='Cancelled';row.last_reason=order.cancelled_reason;r.save(row);r.event(row,'Cancel Released Occurrence',order.cancelled_reason);next_after_disposition(plan,row,'cancelled')
    elif order.status in ('Assigned','Authorized') and row.status=='Completed':
        for name in frappe.get_all(OCC,filters={'plan':plan.name,'source_key':['like','after:'+row.name+':%'],'status':'Planned'},pluck='name'):
            successor=frappe.get_doc(OCC,name);successor.status='Cancelled';successor.last_reason='Predecessor reopened/reworked';r.save(successor);r.event(successor,'Cancel Future Occurrence','Predecessor reopened/reworked')
        before=json.loads(row.baseline_before or '{}')
        for field,value in before.items():plan.set(field,value)
        r.save(plan);row.status='Released';row.completed_actual_on=None;row.completion_reading=None;r.save(row);r.event(row,'Reopen Preventive Cycle',order.reopened_reason or order.rework_reason or 'Controlled rework')
    kick(plan.name)

def kick(plan):
    if not plan:return
    enabled=frappe.db.get_value(PLAN,plan,['status','automation_enabled','release_mode'],as_dict=True)
    if enabled and enabled.status=='Active' and enabled.automation_enabled and enabled.release_mode=='Automatic':
        frappe.enqueue('vanbags_maintenance.preventive.process_plan_job',queue='short',enqueue_after_commit=True,plan=plan)

def process_plan_job(plan):
    original=frappe.session.user
    try:
        doc=frappe.get_doc(PLAN,plan)
        if doc.status!='Active' or not doc.automation_enabled:return
        automation_identity(doc);frappe.set_user(doc.automation_user)
        run_plan(plan,'Committed work event triggered preventive evaluation')
    finally:frappe.set_user(original)

@frappe.whitelist(methods=['POST'])
@atomic
def run_plan(plan,reason):
    r.supervisor();doc=locked(plan);r.reason(reason)
    if doc.status!='Active':frappe.throw('Only active plans can be evaluated.')
    names=_materialize(doc);released=[];blocked=[]
    if doc.release_mode=='Automatic':
        rows=frappe.get_all(OCC,filters={'plan':doc.name,'status':'Planned','planned_for':['<=',local_today(doc)+timedelta(days=cint(doc.lead_days))]},pluck='name',order_by='sequence',limit=100)
        for name in rows:
            try:released.append(release(name,'Automatic release from approved plan: '+reason)['name'])
            except frappe.ValidationError:blocked.append(name);break
    doc.reload();doc.last_evaluated_on=now_datetime();doc.last_error='';r.save(doc)
    return {'occurrences':names,'released':released,'blocked':blocked}

def scheduler():
    # CLI/worker entry only. No implicit Administrator service authority.
    actor=frappe.session.user
    filters={'status':'Active','automation_enabled':1};cursor=frappe.cache.get_value('trucmms_pm_scheduler_cursor')
    if cursor:filters['name']=['>',cursor]
    rows=frappe.get_all(PLAN,filters=filters,fields=['name','automation_user'],order_by='name',limit=50)
    if not rows and cursor:rows=frappe.get_all(PLAN,filters={'status':'Active','automation_enabled':1},fields=['name','automation_user'],order_by='name',limit=50)
    for row in rows:
        try:
            frappe.set_user(row.automation_user or 'Guest');doc=frappe.get_doc(PLAN,row.name);automation_identity(doc)
            run_plan(row.name,'Scheduled preventive evaluation');frappe.db.commit()
        except Exception as exc:
            frappe.db.rollback()
            # Do not publish traceback/credentials. Log only safe error category.
            try:
                doc=frappe.get_doc(PLAN,row.name);doc.check_permission('read');doc.last_error=('Evaluation blocked: '+(str(exc) if isinstance(exc,(frappe.ValidationError,frappe.PermissionError)) else type(exc).__name__))[:300];doc.last_evaluated_on=now_datetime();r.save(doc);frappe.db.commit()
            except Exception:frappe.db.rollback()
        finally:frappe.set_user(actor)
    if rows:frappe.cache.set_value('trucmms_pm_scheduler_cursor',rows[-1].name)

@frappe.whitelist(methods=['GET','POST'])
def schedule(from_date,to_date,company=None,site=None,equipment=None,plan=None):
    start,end=getdate(from_date),getdate(to_date)
    if end<start or (end-start).days>93:frappe.throw('Calendar queries are limited to 94 inclusive days.')
    filters={'planned_for':['between',[start,end]]}
    for key,value in [('company',company),('site',site),('equipment',equipment),('plan',plan)]:
        if value:filters[key]=value
    rows=frappe.get_list(OCC,filters=filters,fields=['name','plan','subject','equipment','component','original_due','planned_for','status','work_order','trigger_total','last_reason'],order_by='planned_for,plan,sequence,name',limit_page_length=501)
    truncated=len(rows)>500;rows=rows[:500]
    for row in rows:
        row['kind']='Programmed' if row.status=='Planned' else row.status
        if row.work_order:
            order=frappe.get_doc('TruCMMS Maintenance Work Order',row.work_order)
            try:
                order.check_permission('read')
                active_execution=frappe.db.sql('SELECT e.name FROM `tabTruCMMS Work Execution` e WHERE e.work_order=%s AND NOT EXISTS (SELECT 1 FROM `tabTruCMMS Execution Adjustment` a WHERE a.execution=e.name) LIMIT 1',(order.name,))
                row['order_status']='In Progress' if (order.pm_started_on or active_execution) and order.status=='Assigned' else order.status
            except frappe.PermissionError:row.work_order=None
    return {'rows':rows,'truncated':truncated,'from_date':str(start),'to_date':str(end)}
