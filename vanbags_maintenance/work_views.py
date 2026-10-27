"""Permission-aware operational views with explicit date basis and timezone."""
from datetime import datetime,date,time,timedelta,timezone
from vanbags_maintenance.timezones import zone as ZoneInfo,assert_storage_clock,RULES_VERSION
import frappe
from frappe.utils import get_datetime,cint
from vanbags_maintenance import work_orders as wo,organization as org
STATES=('Draft','Authorized','Assigned','On Hold','Technical Completed','Verified','Accepted','Closed','Cancelled')
FIELDS=['name','company','site','equipment','functional_location','subject','status','priority','assigned_to','responsible_team','required_discipline','scheduled_start','scheduled_end','target_closure','execution_cycle','lifecycle_policy']
CAP=500

def personal_names(user=None):
    user=user or frappe.session.user
    if wo.TECHNICIAN not in frappe.get_roles(user):return []
    return frappe.db.sql(f"SELECT w.name FROM `tab{wo.DT}` w WHERE w.status IN ('Assigned','On Hold') AND ((w.lifecycle_policy='C1' AND EXISTS (SELECT 1 FROM `tabTruCMMS Work Allocation` a WHERE a.work_order=w.name AND a.execution_cycle=w.execution_cycle AND a.technician=%s AND a.ended_on IS NULL)) OR (COALESCE(w.lifecycle_policy,'')!='C1' AND w.assigned_to=%s))",(user,user),pluck=True)

def instant(value,zone):
    wall=get_datetime(value)
    if wall.tzinfo:return wall.astimezone(timezone.utc)
    candidates=[]
    for fold in (0,1):
        aware=wall.replace(tzinfo=zone,fold=fold);utc=aware.astimezone(timezone.utc)
        if utc.astimezone(zone).replace(tzinfo=None)==wall:candidates.append(utc)
    if not candidates or len(set(candidates))!=1:frappe.throw('Ambiguous or nonexistent system timestamp requires explicit temporal correction.')
    return candidates[0]

def civil_boundary(day,zone):
    wall=datetime.combine(day,time());candidates=[]
    for fold in (0,1):
        aware=wall.replace(tzinfo=zone,fold=fold);utc=aware.astimezone(timezone.utc)
        if utc.astimezone(zone).replace(tzinfo=None)==wall:candidates.append(utc)
    if not candidates:frappe.throw('This date starts at a nonexistent local midnight. Choose a supported date boundary.')
    return min(candidates)

def dates(filters,display_zone):
    try:
        start=date.fromisoformat(filters.get('from_date') or '')
        end=date.fromisoformat(filters.get('to_date') or '')
    except ValueError:frappe.throw('Choose From Date and To Date in YYYY-MM-DD format.')
    if end<start or (end-start).days>92:frappe.throw('Choose an ordered date range of at most 93 days.')
    return start,end,civil_boundary(start,display_zone),civil_boundary(end+timedelta(days=1),display_zone)

@frappe.whitelist(methods=['GET','POST'])
def get_work(filters=None):
    assert_storage_clock()
    if not frappe.has_permission(wo.DT,'read'):frappe.throw('Work-order read permission required.',frappe.PermissionError)
    filters=frappe._dict(frappe.parse_json(filters) if isinstance(filters,str) else filters or {})
    if set(filters)-{'mode','basis','status','company','site','equipment','from_date','to_date'}:frappe.throw('Unsupported view filter.')
    if any(value is not None and (not isinstance(value,str) or len(value)>140) for value in filters.values()):frappe.throw('View filters must be text values.')
    mode=filters.get('mode') or 'List';basis=filters.get('basis') or ('Scheduled' if mode in ('Date Agenda','Calendar') else 'All')
    if mode not in ('List','My Work','Date Agenda','Calendar') or basis not in ('All','Scheduled','Closure Target','Without Schedule'):frappe.throw('Unsupported work view or date basis.')
    if mode in ('Date Agenda','Calendar') and basis not in ('Scheduled','Closure Target'):frappe.throw('Agenda and Calendar require Scheduled or Closure Target date basis.')
    status=filters.get('status') or 'Open'
    if status not in ('All','Open')+STATES:frappe.throw('Unsupported work status.')
    system=ZoneInfo(frappe.db.get_single_value('System Settings','time_zone') or 'UTC')
    zone_name=frappe.db.get_value('User',frappe.session.user,'time_zone') or str(system)
    if filters.site:
        site=frappe.get_doc('TruCMMS Site',filters.site);site.check_permission('read');zone_name=site.time_zone
    display=ZoneInfo(zone_name);conditions={k:filters[k] for k in ('company','site','equipment') if filters.get(k)}
    if status=='Open':conditions['status']=['not in',['Closed','Cancelled']]
    elif status!='All':conditions['status']=status
    personal=set(personal_names());window=None
    if mode=='My Work':conditions['name']=['in',sorted(personal) or ['']]
    if basis in ('Scheduled','Closure Target'):
        start,end,a,z=dates(filters,display);window=(start,end,a,z)
        # Query in the existing system storage timezone; serialization below is explicit UTC/offset.
        lower=a.astimezone(system).replace(tzinfo=None);upper=z.astimezone(system).replace(tzinfo=None)
        if basis=='Scheduled':conditions.update(scheduled_start=['<',upper],scheduled_end=['>',lower])
        else:conditions['target_closure']=['between',[lower,upper-timedelta(microseconds=1)]]
    elif basis=='Without Schedule':conditions['scheduled_start']=['is','not set']
    rows=frappe.get_list(wo.DT,filters=conditions,fields=FIELDS,order_by='name asc',limit_page_length=CAP+1)
    truncated=len(rows)>CAP;rows=rows[:CAP];now=datetime.now(timezone.utc);events=[]
    for row in rows:
        stamps={k:instant(row[k],system) if row.get(k) else None for k in ('scheduled_start','scheduled_end','target_closure')}
        row.overdue=bool(stamps['target_closure'] and stamps['target_closure']<now and row.status not in ('Closed','Cancelled'))
        row.execution_candidate=row.name in personal and row.status=='Assigned'
        row.without_schedule=not(row.scheduled_start and row.scheduled_end)
        row.local_days=[]
        if window:
            start,end,a,z=window
            if basis=='Scheduled':
                x,y=stamps['scheduled_start'],stamps['scheduled_end']
                if not x or not y or y<=x:frappe.throw('Invalid historical schedule requires explicit correction.')
                cursor=max(x,a).astimezone(display).date();last=(min(y,z)-timedelta(microseconds=1)).astimezone(display).date()
            else:cursor=last=stamps['target_closure'].astimezone(display).date()
            while cursor<=last:
                row.local_days.append(cursor.isoformat());cursor+=timedelta(days=1)
        for k,value in stamps.items():
            row[k]=value.isoformat() if value else None;row[k+'_local']=value.astimezone(display).isoformat() if value else None
        if window:events.append({'name':row.name,'days':row.local_days,'start':row.scheduled_start if basis=='Scheduled' else row.target_closure,'end':row.scheduled_end if basis=='Scheduled' else None,'milestone':basis=='Closure Target'})
    return {'rows':rows,'events':events,'mode':mode,'basis':basis,'timezone':zone_name,'storage_timezone':str(system),'timezone_rules':RULES_VERSION,'generated_at':now.isoformat(),'truncated':truncated,'limit':CAP,'from_date':window[0].isoformat() if window else None,'to_date':window[1].isoformat() if window else None}

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def execution_order_query(doctype,txt,searchfield,start,page_len,filters=None):
    if not frappe.has_permission(wo.DT,'read'):return []
    names=personal_names()
    if not names:return []
    rows=frappe.get_list(wo.DT,filters={'name':['in',names],'status':'Assigned'},or_filters={'name':['like','%'+txt+'%'],'subject':['like','%'+txt+'%']},fields=['name','subject'],order_by='name asc',limit_start=max(0,cint(start)),limit_page_length=min(50,max(1,cint(page_len))))
    return [[r.name,r.subject] for r in rows]

def setup():
    from vanbags_maintenance import assets,configuration
    assets.setup(record=False)
    for dt,table in [('Workspace','links'),('Workspace Sidebar','items')]:
        doc=frappe.get_doc(dt,'TruCMMS')
        if not any(row.link_to=='trucmms-work' and row.link_type=='Page' for row in doc.get(table)):
            doc.append(table,{'type':'Link','label':'Work Views','link_type':'Page','link_to':'trucmms-work','collapsible':0,'child':0})
            prior=(frappe.flags.get('in_import'),frappe.flags.get('in_patch'));frappe.flags.in_import=True;frappe.flags.in_patch=True
            try:doc.save(ignore_permissions=True)
            finally:frappe.flags.in_import,frappe.flags.in_patch=prior
    configuration.record_deployment()
