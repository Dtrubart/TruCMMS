"""Scoped weekly calendars materialized as immutable-provenance resource windows."""
import hashlib
import json
from contextlib import contextmanager
from datetime import datetime,time,timedelta,timezone
import frappe
from frappe.utils import getdate,get_time,get_datetime,now_datetime
from vanbags_maintenance import capacity as c,organization as org,teams,configuration
from vanbags_maintenance.work_contract import atomic

CALENDAR='TruCMMS Resource Calendar'
ASSIGNMENT='TruCMMS Calendar Assignment'
GENERATION='TruCMMS Calendar Generation'
WEEKDAYS=('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')
ORIGIN=('calendar_assignment','calendar_generation','calendar_key')

@contextmanager
def internal():
    old=frappe.flags.get('trucmms_calendar_write');frappe.flags.trucmms_calendar_write=True
    try:yield
    finally:frappe.flags.trucmms_calendar_write=old

def manager():
    if not teams.manager():frappe.throw('Supervisor required to configure or generate calendars.',frappe.PermissionError)

def permission(doc,user=None,ptype=None):
    if doc.doctype==CALENDAR:
        if not org.in_scope(doc,user) or not (c.planner(user) or 'TruCMMS Technician' in frappe.get_roles(user)):
            frappe.throw('Calendar requires an authorized Company/Site and maintenance role.',frappe.PermissionError)
    else:c.allowed(doc,user)
    if ptype in ('create','write','delete') and not teams.manager(user):
        frappe.throw('Supervisor required to configure calendars.',frappe.PermissionError)
    return True

def query_for(dt,user=None):
    if dt==CALENDAR:
        if not (c.planner(user) or 'TruCMMS Technician' in frappe.get_roles(user)):return '1=0'
        return org.query(dt,user)
    clause=org.query(dt,user) or '1=1'
    if not c.planner(user):
        if 'TruCMMS Technician' not in frappe.get_roles(user):return '1=0'
        clause+=' AND `tab'+dt+'`.technician='+frappe.db.escape(user or frappe.session.user)
    return clause

def calendar_query(user=None):return query_for(CALENDAR,user)
def assignment_query(user=None):return query_for(ASSIGNMENT,user)
def generation_query(user=None):return query_for(GENERATION,user)
def slot_query(user=None):
    clause=calendar_query(user) or '1=1'
    return f'EXISTS (SELECT 1 FROM `tab{CALENDAR}` WHERE `tab{CALENDAR}`.name=`tabTruCMMS Calendar Slot`.parent AND ({clause}))'

def pattern(doc):
    rows=[]
    for row in doc.slots:
        if row.weekday not in WEEKDAYS:frappe.throw('Choose a valid weekday.')
        if row.starts_at in (None,'') or row.ends_at in (None,''):frappe.throw('Every weekly slot needs start and end times.')
        begin,end=get_time(row.starts_at),get_time(row.ends_at)
        if not begin or not end:frappe.throw('Every weekly slot needs start and end times.')
        offset=int(bool(row.next_day))
        start=begin.hour*3600+begin.minute*60+begin.second
        finish=end.hour*3600+end.minute*60+end.second+86400*offset
        if not 0<finish-start<=86400:frappe.throw('A weekly slot must last more than zero and at most 24 hours; specify next day for overnight work.')
        rows.append(dict(weekday=WEEKDAYS.index(row.weekday),starts_at=begin.isoformat(),ends_at=end.isoformat(),next_day=offset))
    if not 1<=len(rows)<=56:frappe.throw('Choose between 1 and 56 weekly slots.')
    intervals=[]
    for row in rows:
        a=get_time(row['starts_at']);b=get_time(row['ends_at'])
        start=row['weekday']*86400+a.hour*3600+a.minute*60+a.second
        end=row['weekday']*86400+b.hour*3600+b.minute*60+b.second+row['next_day']*86400
        intervals.extend([(start,end),(start+604800,end+604800)])
    previous=None
    for start,end in sorted(intervals):
        if previous is not None and start<previous:frappe.throw('Weekly slots overlap, including across midnight or the week boundary.')
        previous=end
    return rows

def validate_calendar(doc):
    manager();org.validate_context(doc);permission(doc)
    if frappe.db.get_value('TruCMMS Site',doc.site,'disabled'):frappe.throw('Choose an enabled Site.')
    if not (doc.code or '').strip() or not (doc.calendar_name or '').strip():frappe.throw('Calendar code and name required.')
    if doc.dst_occurrence not in ('First','Second'):frappe.throw('Choose a DST occurrence policy.')
    slots=pattern(doc)
    if doc.holiday_list:frappe.get_doc('Holiday List',doc.holiday_list).check_permission('read')
    old=doc.get_doc_before_save()
    if old:
        if any(doc.get(k)!=old.get(k) for k in ('code','company','site')):frappe.throw('Calendar identity and Company/Site are permanent.')
        if frappe.db.exists(ASSIGNMENT,{'calendar':doc.name}) and (slots!=pattern(old) or doc.holiday_list!=old.holiday_list or doc.dst_occurrence!=old.dst_occurrence):
            frappe.throw('This calendar has assignments; create a new calendar for a different pattern. Existing assignments retain their snapshot.')

def validate_assignment(doc):
    manager();org.validate_context(doc);c.allowed(doc)
    calendar=frappe.get_doc(CALENDAR,doc.calendar);calendar.check_permission('read')
    if (calendar.company,calendar.site)!=(doc.company,doc.site):frappe.throw('Calendar and assignment must share Company/Site.')
    if not doc.from_date or not doc.to_date:frappe.throw('Both assignment dates are required.')
    first,last=getdate(doc.from_date),getdate(doc.to_date)
    doc.from_date,doc.to_date=first,last
    if last<first or (last-first).days>365:frappe.throw('Assignment validity is limited to 366 calendar days.')
    if not (doc.reason or '').strip():frappe.throw('Explain the calendar assignment or change.')
    if not frappe.db.get_value('User',doc.technician,'enabled') or 'TruCMMS Technician' not in frappe.get_roles(doc.technician) or not org.in_scope(doc,doc.technician):
        frappe.throw('Choose an enabled technician authorized for this Company/Site.',frappe.PermissionError)
    old=doc.get_doc_before_save()
    if old:
        if any(doc.get(k)!=old.get(k) for k in ('company','site','technician','calendar','from_date','to_date','calendar_snapshot')):
            frappe.throw('Assignment identity, validity and snapshot are permanent; disable it and configure a replacement.')
        if bool(doc.disabled)!=bool(old.disabled) and doc.reason.strip()==(old.reason or '').strip():
            frappe.throw('Provide a new reason for changing future calendar generation.')
    else:
        if calendar.disabled:frappe.throw('Choose an enabled calendar.')
        if doc.calendar_snapshot:frappe.throw('Calendar snapshot is server controlled.',frappe.PermissionError)
        doc.calendar_snapshot=json.dumps(dict(slots=pattern(calendar),holiday_list=calendar.holiday_list,dst_occurrence=calendar.dst_occurrence,
            time_zone=frappe.db.get_value('TruCMMS Site',doc.site,'time_zone')),sort_keys=True)
    teams.locked_document('User',doc.technician)
    if not doc.disabled and frappe.db.sql(f'SELECT name FROM `tab{ASSIGNMENT}` WHERE technician=%s AND company=%s AND site=%s AND disabled=0 AND from_date<=%s AND to_date>=%s AND name!=%s LIMIT 1 FOR UPDATE',
        (doc.technician,doc.company,doc.site,last,first,doc.name or '')):
        frappe.throw('An active calendar assignment already covers this person and Site during this validity.')

def validate_generation(doc):
    if not doc.is_new() or not frappe.flags.get('trucmms_calendar_write'):
        frappe.throw('Calendar generation history is immutable; use the generation service.',frappe.PermissionError)

def guard_window(doc,old):
    if not old:
        if any(doc.get(k) for k in ORIGIN) and not frappe.flags.get('trucmms_calendar_write'):
            frappe.throw('Window generation provenance is server controlled.',frappe.PermissionError)
    elif any(doc.get(k)!=old.get(k) for k in ORIGIN) or old.get('calendar_generation') and any(get_datetime(doc.get(k))!=get_datetime(old.get(k)) for k in ('starts_on','ends_on')):
        frappe.throw('Generated window provenance and times are immutable; disable with a reason and add an explicit replacement.',frappe.PermissionError)
    elif old.get('calendar_generation') and bool(doc.disabled)!=bool(old.disabled) and (doc.reason or '').strip()==(old.reason or '').strip():
        frappe.throw('Provide a new reason for this generated-window exception.')

def holidays(name,first,last):
    if not name:return []
    doc=frappe.get_doc('Holiday List',name);doc.check_permission('read')
    if getdate(doc.from_date)>first or getdate(doc.to_date)<last:frappe.throw('Native Holiday List must cover every date touched by these shifts.')
    return sorted({getdate(row.holiday_date) for row in doc.holidays if first<=getdate(row.holiday_date)<=last})

@frappe.whitelist(methods=['POST'])
@atomic
def generate(assignment,from_date,to_date,reason):
    manager()
    doc=teams.locked_document(ASSIGNMENT,assignment);doc.check_permission('read')
    if doc.disabled:frappe.throw('This calendar assignment is disabled.')
    if frappe.db.get_value('TruCMMS Site',doc.site,'disabled') or not frappe.db.get_value('User',doc.technician,'enabled') or 'TruCMMS Technician' not in frappe.get_roles(doc.technician) or not org.in_scope(doc,doc.technician):
        frappe.throw('Reconcile the Site and technician authorization before generating availability.',frappe.PermissionError)
    if not from_date or not to_date:frappe.throw('Provide both generation dates.')
    first,last=getdate(from_date),getdate(to_date)
    if last<first or (last-first).days>30 or first<getdate(doc.from_date) or last>getdate(doc.to_date):
        frappe.throw('Generate at most 31 days within the assignment validity.')
    reason=(reason or '').strip()
    if not reason:frappe.throw('Explain this calendar generation.')
    teams.locked_document('User',doc.technician)
    key=hashlib.sha256(json.dumps([assignment,str(first),str(last)]).encode()).hexdigest()
    previous=teams.locked_sql(f'SELECT name,window_count FROM `tab{GENERATION}` WHERE generation_key=%s FOR UPDATE',(key,),as_dict=True)
    if previous:return dict(name=previous[0].name,created=False,window_count=previous[0].window_count)
    if teams.locked_sql(f'SELECT name FROM `tab{GENERATION}` WHERE assignment=%s AND from_date<=%s AND to_date>=%s LIMIT 1 FOR UPDATE',(assignment,last,first)):
        frappe.throw('This period overlaps a prior generation; use a disjoint period or review its existing windows.')
    frozen=json.loads(doc.calendar_snapshot)
    if frozen['time_zone']!=frappe.db.get_value('TruCMMS Site',doc.site,'time_zone'):
        frappe.throw('Site timezone changed; reconcile the assignment before generating further windows.')
    fold=0 if frozen['dst_occurrence']=='First' else 1
    def instant(day,at):
        return datetime.fromisoformat(configuration.local_instant(datetime.combine(day,get_time(at)),doc.site,fold=fold)).astimezone(timezone.utc)
    raw=[];touched=last
    for offset in range((last-first).days+1):
        day=first+timedelta(days=offset)
        for row in frozen['slots']:
            if day.weekday()!=row['weekday']:continue
            end_day=day+timedelta(days=row['next_day'])
            touched=max(touched,end_day if get_time(row['ends_at'])!=time.min else end_day-timedelta(days=1))
            start,end=instant(day,row['starts_at']),instant(end_day,row['ends_at'])
            if end<=start:frappe.throw('The DST policy produces an invalid shift; configure a different pattern.')
            raw.append((start,end))
    excluded=holidays(frozen.get('holiday_list'),first,touched)
    blocks=[(instant(day,'00:00:00'),instant(day+timedelta(days=1),'00:00:00')) for day in excluded]
    planned=sorted(segment for interval in raw for segment in c.subtract([interval],blocks))
    payload=dict(calendar_snapshot=frozen,holidays=[str(x) for x in excluded],windows=[[str(c.server(a)),str(c.server(b))] for a,b in planned])
    with internal():
        event=frappe.get_doc(dict(doctype=GENERATION,assignment=assignment,company=doc.company,site=doc.site,technician=doc.technician,
            from_date=first,to_date=last,generation_key=key,reason=reason,recorded_by=frappe.session.user,recorded_on=now_datetime(),
            window_count=len(planned),snapshot=json.dumps(payload,sort_keys=True))).insert(ignore_permissions=True)
        for index,(start,end) in enumerate(planned):
            window_key=hashlib.sha256((key+':'+str(index)).encode()).hexdigest()
            frappe.get_doc(dict(doctype=c.DT,company=doc.company,site=doc.site,technician=doc.technician,kind='Working',starts_on=c.server(start),ends_on=c.server(end),
                reason=reason,calendar_assignment=assignment,calendar_generation=event.name,calendar_key=window_key)).insert()
    return dict(name=event.name,created=True,window_count=len(planned))

def coverage(company,site,technician,first,last):
    if not frappe.db.table_exists(GENERATION):return set()
    rows=frappe.get_list(GENERATION,filters={'company':company,'site':site,'technician':technician,'from_date':['<=',last],'to_date':['>=',first]},fields=['from_date','to_date'],limit_page_length=1001)
    if len(rows)>1000:frappe.throw('Too many calendar generations; shorten the period.')
    return {first+timedelta(days=offset) for offset in range((last-first).days+1) if any(getdate(row.from_date)<=first+timedelta(days=offset)<=getdate(row.to_date) for row in rows)}

def validate_share(doc,method=None):
    if doc.share_doctype in (CALENDAR,ASSIGNMENT,GENERATION):frappe.throw('Calendar access cannot be expanded through sharing.',frappe.PermissionError)

def setup():
    from vanbags_maintenance import work_scope
    work_scope.setup()
    frappe.db.add_index(ASSIGNMENT,['technician','site','from_date','to_date'],'resource_calendar_validity')
    frappe.db.add_index(GENERATION,['assignment','from_date','to_date'],'resource_calendar_period')
