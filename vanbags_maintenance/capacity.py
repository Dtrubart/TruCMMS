"""R4.1 explicit availability; advisory capacity never grants assignment eligibility."""
from datetime import datetime, time, timedelta, timezone
import frappe
from frappe.utils import getdate, get_datetime
from vanbags_maintenance import organization as org, work_orders as wo, teams, configuration
from vanbags_maintenance.timezones import zone as ZoneInfo
DT='TruCMMS Resource Window'
PLANNERS={'TruCMMS Supervisor','TruCMMS Dispatcher'}


def planner(user=None):
    return org.privileged(user) or bool(PLANNERS.intersection(frappe.get_roles(user)))


def allowed(doc,user=None):
    user=user or frappe.session.user
    if not org.in_scope(doc,user) or not (planner(user) or doc.technician==user and 'TruCMMS Technician' in frappe.get_roles(user)):
        frappe.throw('Resource availability requires authorized Company/Site and participant access.',frappe.PermissionError)
    return True


def permission(doc,user=None,ptype=None):
    allowed(doc,user)
    if ptype in ('create','write','delete') and not teams.manager(user):frappe.throw('Supervisor required to configure availability.',frappe.PermissionError)
    return True


def query(user=None):
    user=user or frappe.session.user
    clause=org.query(DT,user) or '1=1'
    if not planner(user):
        if 'TruCMMS Technician' not in frappe.get_roles(user):return '1=0'
        clause+=' AND `tab'+DT+'`.technician='+frappe.db.escape(user)
    return clause


def validate(doc):
    if not teams.manager():frappe.throw('Supervisor required to configure availability.',frappe.PermissionError)
    org.validate_context(doc);allowed(doc)
    site=frappe.get_doc('TruCMMS Site',doc.site)
    if site.disabled:frappe.throw('Configure availability on an enabled Site.')
    if not frappe.db.get_value('User',doc.technician,'enabled') or 'TruCMMS Technician' not in frappe.get_roles(doc.technician):
        frappe.throw('Choose an enabled TruCMMS Technician.')
    if not org.in_scope(frappe._dict(doctype=DT,company=doc.company,site=doc.site),doc.technician):
        frappe.throw('Technician must be authorized for this Company and Site.')
    if doc.kind not in ('Working','Unavailable'):frappe.throw('Choose Working or Unavailable.')
    if not doc.starts_on or not doc.ends_on:frappe.throw('Provide both interval endpoints.')
    start,end=get_datetime(doc.starts_on),get_datetime(doc.ends_on)
    if start.tzinfo or end.tzinfo:frappe.throw('Use native system-time datetimes without offset suffixes.')
    if end<=start or end-start>timedelta(days=31):frappe.throw('Use a positive interval of at most 31 days.')
    if not (doc.reason or '').strip():frappe.throw('Explain this availability window or change.')
    doc.starts_on,doc.ends_on,doc.reason=start,end,doc.reason.strip()
    old=doc.get_doc_before_save()
    if old and any(doc.get(k)!=old.get(k) for k in ('company','site','technician','kind')):
        frappe.throw('Resource window identity is permanent; disable it and create another.')
    # One person cannot promise the same working interval to several sites.
    # Serialize changes globally for that user; never expose the conflicting record.
    teams.locked_document('User',doc.technician)
    if not doc.disabled and frappe.db.sql(f"""SELECT name FROM `tab{DT}` WHERE technician=%s AND kind=%s
        AND disabled=0 AND starts_on<%s AND ends_on>%s AND name!=%s LIMIT 1 FOR UPDATE""",
        (doc.technician,doc.kind,end,start,doc.name or '')):
        frappe.throw('This person already has an overlapping window of the same kind. Review their calendar.')


def merged(intervals):
    result=[]
    for start,end in sorted(intervals):
        if end<=start:continue
        if result and start<=result[-1][1]:result[-1]=(result[-1][0],max(result[-1][1],end))
        else:result.append((start,end))
    return result


def subtract(working,unavailable):
    result=merged(working)
    for left,right in merged(unavailable):
        next_result=[]
        for start,end in result:
            if end<=left or start>=right:next_result.append((start,end));continue
            if start<left:next_result.append((start,left))
            if end>right:next_result.append((right,end))
        result=next_result
    return result


def seconds(intervals):return sum((end-start).total_seconds() for start,end in intervals)
def clipped(intervals,start,end):return [(max(a,start),min(b,end)) for a,b in intervals if a<end and b>start]
def intersect(intervals,available):return [(max(a,c),min(b,d)) for a,b in intervals for c,d in available if a<d and b>c]
def system_zone():return ZoneInfo(frappe.db.get_single_value('System Settings','time_zone') or 'UTC')
def utc(value):return get_datetime(value).replace(tzinfo=system_zone()).astimezone(timezone.utc)
def server(value):return value.astimezone(system_zone()).replace(tzinfo=None)


@frappe.whitelist(methods=['GET'])
def overview(company,site,technician,from_date,to_date):
    context=frappe._dict(doctype=DT,company=company,site=site,technician=technician)
    allowed(context)
    if frappe.db.get_value('TruCMMS Site',site,'company')!=company:frappe.throw('Company and Site must match.')
    first,last=getdate(from_date),getdate(to_date)
    if last<first or (last-first).days>30:frappe.throw('Choose at most 31 calendar days.')
    if 'TruCMMS Technician' not in frappe.get_roles(technician) or not org.in_scope(context,technician):frappe.throw('Choose a technician authorized for this Company and Site.',frappe.PermissionError)
    def boundary(day):
        return datetime.fromisoformat(configuration.local_instant(datetime.combine(day,time.min),site,fold=0)).astimezone(timezone.utc)
    begin,finish=boundary(first),boundary(last+timedelta(days=1))
    windows=frappe.get_list(DT,filters={'company':company,'site':site,'technician':technician,'disabled':0,
        'starts_on':['<',server(finish)],'ends_on':['>',server(begin)]},fields=['starts_on','ends_on','kind'],limit_page_length=1001)
    if len(windows)>1000:frappe.throw('Too many resource windows; shorten the period.')
    working=[(utc(r.starts_on),utc(r.ends_on)) for r in windows if r.kind=='Working']
    # Absences at other authorized contexts still make the same person unavailable.
    # Only intersecting capacity is returned, without foreign document identifiers.
    absences=frappe.db.sql(f"""SELECT starts_on,ends_on FROM `tab{DT}` WHERE technician=%s AND kind='Unavailable'
        AND disabled=0 AND starts_on<%s AND ends_on>%s LIMIT 1001""",(technician,server(finish),server(begin)),as_dict=True)
    if len(absences)>1000:frappe.throw('Too many absence windows; shorten the period.')
    unavailable=[(utc(r.starts_on),utc(r.ends_on)) for r in absences]
    orders=frappe.db.sql(f"""SELECT w.name,w.scheduled_start,w.scheduled_end FROM `tab{wo.DT}` w
        WHERE w.status IN ('Authorized','Assigned','On Hold') AND (w.assigned_to=%s OR EXISTS
        (SELECT 1 FROM `tabTruCMMS Work Allocation` a WHERE a.work_order=w.name AND a.execution_cycle=w.execution_cycle
        AND a.technician=%s AND a.ended_on IS NULL)) AND (w.scheduled_start IS NULL OR
        (w.scheduled_start<%s AND w.scheduled_end>%s)) LIMIT 1001""",(technician,technician,server(finish),server(begin)),as_dict=True)
    if len(orders)>1000:frappe.throw('Too many work assignments; shorten the period.')
    # Occupancy is global for this person. Foreign work never leaks its name/scope.
    visible=set(frappe.get_list(wo.DT,filters={'name':['in',[r.name for r in orders]]},pluck='name',limit_page_length=0)) if orders else set()
    load=[(utc(r.scheduled_start),utc(r.scheduled_end)) for r in orders if r.scheduled_start and r.scheduled_end]
    unscheduled=[r.name for r in orders if not r.scheduled_start and r.name in visible]
    days=[]
    for offset in range((last-first).days+1):
        day=first+timedelta(days=offset);start,end=boundary(day),boundary(day+timedelta(days=1))
        shifts=clipped(working,start,end);available=subtract(shifts,clipped(unavailable,start,end))
        scheduled=clipped(load,start,end);inside=intersect(scheduled,available)
        hours=lambda value:round(value/3600,4)
        capacity=hours(seconds(available)) if shifts else None
        days.append(dict(date=str(day),configured=bool(shifts),available_hours=capacity,scheduled_hours=hours(seconds(scheduled)),
            free_hours=max(0,round(capacity-hours(seconds(inside)),4)) if capacity is not None else None,
            overload_hours=hours(max(0,seconds(inside)-seconds(available))) if shifts else None,
            overlap_hours=hours(seconds(scheduled)-seconds(merged(scheduled))),
            outside_hours=hours(seconds(scheduled)-seconds(inside)) if shifts else None))
    return dict(company=company,site=site,technician=technician,time_zone=frappe.db.get_value('TruCMMS Site',site,'time_zone'),days=days,
        visible_orders=sorted(visible),unscheduled_orders=unscheduled,
        basis='Explicit working windows minus absences. Scheduled load includes all active allocations, including other sites without exposing their identifiers. No automatic assignment or eligibility override.')


def validate_share(doc,method=None):
    if doc.share_doctype==DT:frappe.throw('Resource calendars cannot be shared outside their controlled access.',frappe.PermissionError)


def setup():
    from vanbags_maintenance import logistics
    logistics.setup()
    frappe.db.add_index(DT,['technician','starts_on','ends_on'],'resource_interval')
