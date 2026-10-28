"""Procedure execution requirements, numeric results and reviewed corrective follow-up."""
import hashlib,json
from decimal import Decimal
import frappe
from frappe.utils import get_datetime,now_datetime
from vanbags_maintenance import r2_records as r,meters,job_plans as jp,teams
from vanbags_maintenance.work_contract import atomic
FINDING='TruCMMS Inspection Finding'
EX='TruCMMS Work Execution'

def definition(order):return json.loads(order.pm_procedure_snapshot) if order.get('pm_procedure_snapshot') else None

def validate_execution(doc,order):
    spec=definition(order)
    if not spec:
        if doc.get('pm_measurements') or any(x.get('procedure_task_code') for x in doc.tasks):frappe.throw('This order has no approved procedure definition.')
        return
    tasks={x['task_code']:x for x in spec['tasks']};seen=set()
    for task in doc.tasks:
        code=task.get('procedure_task_code')
        if not code:continue
        if code not in tasks or code in seen:frappe.throw('Procedure task codes must be valid and unique within an execution.')
        seen.add(code)
        if tasks[code].get('discipline') and tasks[code]['discipline']!=doc.discipline:frappe.throw('This procedure task requires a different assigned discipline.')
    definitions={x['metric_key']:x for x in spec.get('measurements',[])};seen=set()
    for row in doc.get('pm_measurements') or []:
        if row.metric_key not in definitions or row.metric_key in seen:frappe.throw('Measurement keys must be valid and unique within an execution.')
        seen.add(row.metric_key);metric=definitions[row.metric_key]
        if metric['task_code'] not in {x.get('procedure_task_code') for x in doc.tasks}:frappe.throw('Record the measurement with its corresponding procedure task.')
        value=jp.finite(row.value,'Measured value');row.value=str(value)
        row.metric_label=metric['metric_name'];row.unit=metric['unit']
        row.out_of_range=int(bool(metric.get('has_lower_limit') and value<Decimal(str(metric['lower_limit'])) or metric.get('has_upper_limit') and value>Decimal(str(metric['upper_limit']))))
        if row.meter_reading:
            reading=frappe.get_doc(meters.READING,row.meter_reading);reading.check_permission('read');meter=frappe.get_doc(meters.DT,reading.meter);meter.check_permission('read')
            if meters.corrected(reading.name) or reading.equipment!=order.equipment or (reading.company,reading.site)!=(order.company,order.site) or (meter.unit,meter.metric_kind)!=(metric['unit'],metric['metric_kind']):frappe.throw('Reading target, units and semantics must match the approved procedure.')
            target_component=frappe.db.get_value('TruCMMS PM Plan',order.pm_plan,'component') if order.pm_plan else None
            if target_component and reading.component!=target_component:frappe.throw('Use the reading of the component maintained by this plan.')
            if Decimal(str(reading.value))!=value or not get_datetime(doc.actual_start)<=get_datetime(reading.actual_on)<=get_datetime(doc.actual_end):frappe.throw('The linked meter reading must match this value and execution time interval.')

def recorded(doc,method=None):
    order=frappe.get_doc('TruCMMS Maintenance Work Order',doc.work_order);spec=definition(order)
    if not spec:return
    definitions={x['metric_key']:x for x in spec.get('measurements',[])}
    for row in doc.get('pm_measurements') or []:
        if row.out_of_range:
            metric=definitions[row.metric_key]
            expected=('>= '+str(metric['lower_limit']) if metric.get('has_lower_limit') else '')+(' <= '+str(metric['upper_limit']) if metric.get('has_upper_limit') else '')
            _finding(order,doc.name,row.metric_key,'Measured '+metric['metric_name']+' outside approved limits',row.value,expected)
    if order.pm_plan:
        from vanbags_maintenance.preventive import kick
        kick(order.pm_plan)

def _finding(order,execution,key,description,value=None,expected=None,component=None):
    identity='IF-'+hashlib.sha256((execution+'|'+key).encode()).hexdigest()
    if frappe.db.exists(FINDING,identity):return frappe.get_doc(FINDING,identity)
    component=component or (frappe.db.get_value('TruCMMS PM Plan',order.pm_plan,'component') if order.pm_plan else None)
    return r.create(FINDING,finding_key=identity,company=order.company,site=order.site,equipment=order.equipment,component=component,work_order=order.name,execution=execution,metric_key=key,description=description,observed_value=float(value) if value is not None else None,expected_range=expected,status='Open',recorded_by=frappe.session.user,recorded_on=now_datetime())

@frappe.whitelist(methods=['POST'])
@atomic
def report(execution,description,key,component=None):
    description=r.reason(description)
    if not key or len(key)>100:frappe.throw('A stable finding key is required.')
    entry=frappe.get_doc(EX,execution);entry.check_permission('read')
    order=frappe.get_doc('TruCMMS Maintenance Work Order',entry.work_order);order.check_permission('read')
    if entry.technician!=frappe.session.user:r.supervisor()
    if order.status not in ('Assigned','Technical Completed'):frappe.throw('Record inspection findings before verification.')
    if component:
        target=frappe.get_doc('TruCMMS Component',component);target.check_permission('read')
        if target.equipment!=order.equipment:frappe.throw('The component must be installed on this equipment.')
    result=_finding(order,execution,'manual:'+key,description,component=component)
    if result.description!=description:frappe.throw('Finding key already belongs to different content.')
    return result.as_dict()

@frappe.whitelist(methods=['POST'])
@atomic
def review(finding,disposition,reason):
    r.supervisor();reason=r.reason(reason);doc=teams.locked_document(FINDING,finding);doc.check_permission('read')
    if disposition not in ('Action Required','Accepted Deviation','Resolved'):frappe.throw('Choose an explicit reviewed disposition.')
    if disposition=='Resolved' and (not doc.followup_order or frappe.db.get_value('TruCMMS Maintenance Work Order',doc.followup_order,'status')!='Closed'):frappe.throw('Close the linked corrective work before resolving this finding.')
    doc.status=disposition;doc.review_reason=reason;doc.reviewed_by=frappe.session.user;doc.reviewed_on=now_datetime();r.save(doc);r.event(doc,'Review Inspection Finding',reason,disposition=disposition)
    return doc.as_dict()

@frappe.whitelist(methods=['POST'])
@atomic
def followup(finding,reason,priority='Medium'):
    r.editor();reason=r.reason(reason);doc=teams.locked_document(FINDING,finding);doc.check_permission('read')
    if doc.followup_order:
        order=teams.locked_document('TruCMMS Maintenance Work Order',doc.followup_order);order.check_permission('read');return order.as_dict()
    if doc.status!='Action Required':frappe.throw('Supervisor must review the finding as Action Required before generating corrective follow-up.')
    from vanbags_maintenance.work_contract import create_origin
    result=create_origin(doc.company,doc.site,'Inspection follow-up',doc.description,priority,doc.name,reason,equipment=doc.equipment,provider={'origin':'Inspection','pm_finding':doc.name})
    doc.followup_order=result['name'];r.save(doc);r.event(doc,'Generate Inspection Follow-up',reason,work_order=result['name'])
    return result

def entries(order):
    rows=frappe.db.sql(f'SELECT e.name FROM `tab{EX}` e WHERE e.work_order=%s AND e.execution_cycle=%s AND NOT EXISTS (SELECT 1 FROM `tabTruCMMS Execution Adjustment` a WHERE a.execution=e.name) ORDER BY e.actual_end,e.name',(order.name,order.execution_cycle),pluck=True)
    return [frappe.get_doc(EX,name) for name in rows]

def check_completion(order):
    spec=definition(order)
    if not spec:return
    performed=entries(order);done=set();measured=set()
    for entry in performed:
        completed={t.get('procedure_task_code') for t in entry.tasks if t.result=='Completed'}
        for task in spec['tasks']:
            if task['task_code'] not in completed:continue
            if task.get('evidence_required') and not frappe.db.exists('File',{'attached_to_doctype':EX,'attached_to_name':entry.name,'is_private':1}):frappe.throw('Attach the required private evidence for task '+task['task_code']+'.')
            done.add(task['task_code'])
        for metric in spec.get('measurements',[]):
            if metric['task_code'] in completed and any(x.metric_key==metric['metric_key'] for x in entry.get('pm_measurements') or []):measured.add(metric['metric_key'])
    missing=[x['task_code'] for x in spec['tasks'] if x.get('mandatory') and x['task_code'] not in done]
    missing += [x['metric_key'] for x in spec.get('measurements',[]) if x.get('required') and x['metric_key'] not in measured]
    if missing:frappe.throw('Complete required procedure tasks/measurements: '+', '.join(missing))
    if order.pm_plan:
        plan=frappe.get_doc('TruCMMS PM Plan',order.pm_plan)
        if plan.schedule_type=='Meter':maintenance_actual(order,plan)

def maintenance_actual(order,plan):
    performed=entries(order)
    if not performed:frappe.throw('Validated preventive maintenance requires effective execution records.')
    actual=max(get_datetime(e.actual_end) for e in performed);reading=None
    if plan.schedule_type=='Meter':
        choices=[]
        for entry in performed:
            for row in entry.get('pm_measurements') or []:
                if row.metric_key==plan.meter_metric_key and row.meter_reading:
                    source=frappe.get_doc(meters.READING,row.meter_reading)
                    if source.meter==plan.meter and not meters.corrected(source.name):choices.append(source)
        if not choices:frappe.throw('Record the trigger meter reading within the maintenance execution; no fabricated usage baseline is allowed.')
        reading=max(choices,key=lambda x:get_datetime(x.actual_on))
    return actual,reading

def open_findings(order):
    valid={e.name for e in entries(order)}
    return [x.name for x in frappe.get_all(FINDING,filters={'work_order':order.name,'status':'Open'},fields=['name','execution']) if x.execution in valid]
