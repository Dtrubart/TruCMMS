"""Effective-dated maintenance eligibility; membership never grants work visibility."""
import re
import frappe
from frappe.utils import now_datetime,get_datetime
from vanbags_maintenance import organization as org
TEAM='TruCMMS Maintenance Team'
MEMBER='TruCMMS Team Membership'
GRANT='TruCMMS Team Site Authorization'
ASSIGN='TruCMMS Team Assignment'
DISC='TruCMMS Discipline'
FIELDS=('responsible_team','required_discipline','team_policy','team_assignment')

def locked_sql(query,values=None,**kwargs):
    try:return frappe.db.sql(query,values,**kwargs)
    except frappe.QueryDeadlockError as error:
        cause=error.args[0] if error.args else None
        code=cause.args[0] if isinstance(cause,Exception) and cause.args else cause
        if code in (1020,1205,1213):
            frappe.throw('Team eligibility changed concurrently. Reload and retry; no eligibility changes were committed.',frappe.TimestampMismatchError)
        raise


def locked_document(doctype,name):
    try:return frappe.get_doc(doctype,name,for_update=True)
    except frappe.QueryDeadlockError as error:
        cause=error.args[0] if error.args else None
        code=cause.args[0] if isinstance(cause,Exception) and cause.args else cause
        if code in (1020,1205,1213):frappe.throw('Maintenance data changed concurrently. Reload and retry.',frappe.TimestampMismatchError)
        raise


def manager(user=None):
    return org.privileged(user) or 'TruCMMS Supervisor' in frappe.get_roles(user or frappe.session.user)

def team_sites(team):
    rows=locked_sql(f'SELECT company,management_site FROM `tab{TEAM}` WHERE name=%s FOR UPDATE',(team,),as_dict=True)
    if not rows:frappe.throw('Maintenance team not found.')
    row=rows[0]
    sites=locked_sql(f'SELECT site FROM `tab{GRANT}` WHERE team=%s AND revoked=0 FOR UPDATE',(team,),pluck=True)
    return row,set([row.management_site]+sites)

def manage_team(team):
    if not manager():frappe.throw('Supervisor role required.',frappe.PermissionError)
    row,sites=team_sites(team)
    if not org.privileged():
        companies,allowed=org.allowed(TEAM)
        if row.company not in companies or not sites.issubset(set(allowed)):
            frappe.throw('Administration requires access to every authorized site of this team.',frappe.PermissionError)
    return row

def scope_sql(dt,user=None):
    user=user or frappe.session.user
    if org.privileged(user):return ''
    companies,sites=org.allowed(dt,user)
    if not companies or not sites:return '1=0'
    cs=','.join(frappe.db.escape(x) for x in companies);ss=','.join(frappe.db.escape(x) for x in sites)
    t=f'`tab{dt}`'
    team_expr=t+'.name' if dt==TEAM else t+'.team'
    allowed_team=f"EXISTS (SELECT 1 FROM `tab{TEAM}` t WHERE t.name={team_expr} AND (t.management_site IN ({ss}) OR EXISTS (SELECT 1 FROM `tab{GRANT}` g WHERE g.team=t.name AND g.site IN ({ss}))))"
    role=manager(user) or 'TruCMMS Dispatcher' in frappe.get_roles(user)
    if not role:
        if 'TruCMMS Technician' not in frappe.get_roles(user):return '1=0'
        allowed_team+=f" AND EXISTS (SELECT 1 FROM `tab{MEMBER}` m WHERE m.team={team_expr} AND m.user={frappe.db.escape(user)})"
    if dt==GRANT:allowed_team+=f' AND {t}.site IN ({ss})'
    if dt==MEMBER and not role:allowed_team+=f' AND {t}.user={frappe.db.escape(user)}'
    return f'{t}.company IN ({cs}) AND ({allowed_team})'

def team_query(user=None):return scope_sql(TEAM,user)
def member_query(user=None):return scope_sql(MEMBER,user)
def grant_query(user=None):return scope_sql(GRANT,user)

def permission(doc,user=None,ptype=None):
    user=user or frappe.session.user
    if not org.privileged(user):
        condition=scope_sql(doc.doctype,user)
        if doc.is_new():
            if not manager(user):frappe.throw('Supervisor role required.',frappe.PermissionError)
        elif not locked_sql(f'SELECT name FROM `tab{doc.doctype}` WHERE name=%s AND ({condition})',(doc.name,)):
            frappe.throw('Team administration or membership scope required.',frappe.PermissionError)
    if ptype in ('write','create','delete'):
        if user!=frappe.session.user or not manager(user):frappe.throw('Supervisor role required.',frappe.PermissionError)
        if not doc.is_new():manage_team(doc.name if doc.doctype==TEAM else doc.team)
    return True

def validate_discipline(doc):
    if not org.privileged():frappe.throw('System Manager maintains the discipline catalog.',frappe.PermissionError)
    doc.discipline_code=(doc.discipline_code or '').strip().upper()
    if not re.fullmatch(r'[A-Z0-9._-]{1,50}',doc.discipline_code or ''):frappe.throw('Invalid discipline code.')
    old=doc.get_doc_before_save()
    if old and old.discipline_code!=doc.discipline_code:frappe.throw('Discipline identity is immutable.')

def validate_team(doc):
    if not manager():frappe.throw('Supervisor role required.',frappe.PermissionError)
    org.validate_context(frappe._dict(doctype=TEAM,company=doc.company,site=doc.management_site,get_doc_before_save=lambda:None))
    doc.team_code=(doc.team_code or '').strip().upper()
    if not re.fullmatch(r'[A-Z0-9._-]{1,50}',doc.team_code or ''):frappe.throw('Invalid team code.')
    old=doc.get_doc_before_save()
    if old:
        manage_team(doc.name)
        if any(doc.get(f)!=old.get(f) for f in ('company','management_site','team_code','team_type')):frappe.throw('Team identity, company, management site and type are immutable.')
    if doc.team_type not in ('Internal','External'):frappe.throw('Choose Internal or External.')
    values=[r.discipline for r in doc.disciplines]
    if not values or len(set(values))!=len(values):frappe.throw('Choose distinct team disciplines.')
    for value in values:
        if frappe.db.get_value(DISC,value,'disabled') and (not old or value not in [r.discipline for r in old.disciplines]):frappe.throw('Cannot add a disabled discipline.')
    if old:
        removed=set(r.discipline for r in old.disciplines)-set(values)
        if removed and frappe.db.exists(MEMBER,{'team':doc.name,'discipline':['in',list(removed)]}):frappe.throw('Referenced disciplines must remain in the team history.')

def end_of(row):
    values=[get_datetime(row.get(f)) for f in ('valid_until','revoked_on') if row.get(f)]
    return min(values) if values else None

def active(row,at=None):
    at=get_datetime(at or now_datetime());end=end_of(row)
    return get_datetime(row.valid_from)<=at and (not end or at<end)

def validate_interval(doc):
    row=manage_team(doc.team);doc.company=row.company
    old=doc.get_doc_before_save();now=now_datetime()
    doc.valid_from=get_datetime(doc.valid_from);doc.valid_until=get_datetime(doc.valid_until) if doc.valid_until else None
    if doc.valid_until and doc.valid_until<=doc.valid_from:frappe.throw('End must be later than start; end is exclusive.')
    identity=('team','company','valid_from')+(('user','discipline','function') if doc.doctype==MEMBER else ('site',))
    if old:
        for f in identity:
            a,b=doc.get(f),old.get(f)
            if f=='valid_from':a,b=get_datetime(a),get_datetime(b)
            if a!=b:frappe.throw('Eligibility identity and start are immutable; create a new interval.')
        if old.revoked and (doc.revoked!=old.revoked or doc.valid_until!= (get_datetime(old.valid_until) if old.valid_until else None)):frappe.throw('Revoked eligibility is immutable.')
        if doc.valid_until!=(get_datetime(old.valid_until) if old.valid_until else None) and doc.valid_until and doc.valid_until<now:frappe.throw('Do not rewrite an elapsed eligibility interval.')
    for f in ('revoked_on','revoked_by'):
        a,b=doc.get(f),(old.get(f) if old else None)
        if f.endswith('_on') and a and b:a,b=get_datetime(a),get_datetime(b)
        if a!=b:frappe.throw('Revocation audit fields are server controlled.')
    if doc.revoked and (not old or not old.revoked):
        if not old:frappe.throw('Create an eligible interval before revoking it.')
        doc.revoked_on=now;doc.revoked_by=frappe.session.user
    if doc.doctype==GRANT:
        site=frappe.get_doc('TruCMMS Site',doc.site)
        if site.company!=doc.company:frappe.throw('Team and site must have the same company.')
        if not org.in_scope(site):frappe.throw('Site administration authorization required.',frappe.PermissionError)
        if site.disabled and not old:frappe.throw('Cannot authorize a disabled site.')
        match={'team':doc.team,'site':doc.site}
    else:
        if doc.discipline not in frappe.get_all('TruCMMS Team Discipline',filters={'parent':doc.team,'parenttype':TEAM},pluck='discipline'):frappe.throw('Discipline is not supported by this team.')
        if not frappe.db.get_value('User',doc.user,'enabled') or 'TruCMMS Technician' not in frappe.get_roles(doc.user):frappe.throw('Choose an enabled maintenance technician.')
        if doc.function not in ('Technician','Lead'):frappe.throw('Invalid membership function.')
        match={'team':doc.team,'user':doc.user,'discipline':doc.discipline}
    # Team row serializes eligibility edits and assignment checks in a single lock order.
    locked_sql(f'SELECT name FROM `tab{TEAM}` WHERE name=%s FOR UPDATE',(doc.team,))
    where=' AND '.join('`'+key+'`=%s' for key in match)
    others=locked_sql(f'SELECT name,valid_from,valid_until,revoked_on FROM `tab{doc.doctype}` WHERE {where} FOR UPDATE',tuple(match.values()),as_dict=True)
    for other in others:
        if other.name==doc.name:continue
        start=max(doc.valid_from,get_datetime(other.valid_from));ends=[x for x in (end_of(doc),end_of(other)) if x]
        if not ends or start<min(ends):frappe.throw('Equivalent eligibility intervals cannot overlap.')

def eligibility(order,user=None,at=None,lock=False):
    user=user or order.assigned_to
    if not order.responsible_team or not order.required_discipline:frappe.throw('Choose the responsible team and required discipline before assigning.')
    if lock:locked_sql(f'SELECT name FROM `tab{TEAM}` WHERE name=%s FOR UPDATE',(order.responsible_team,))
    team=locked_sql(f'SELECT name,company,disabled FROM `tab{TEAM}` WHERE name=%s FOR UPDATE',(order.responsible_team,),as_dict=True)
    if not team:frappe.throw('Maintenance team not found.')
    team=team[0]
    if team.company!=order.company or team.disabled:frappe.throw('An enabled team of the same company is required.',frappe.PermissionError)
    disciplines=locked_sql('SELECT discipline FROM `tabTruCMMS Team Discipline` WHERE parent=%s AND parenttype=%s FOR UPDATE',(team.name,TEAM),pluck=True)
    if order.required_discipline not in disciplines or frappe.db.get_value(DISC,order.required_discipline,'disabled'):frappe.throw('An enabled team discipline is required.',frappe.PermissionError)
    site=frappe.get_doc('TruCMMS Site',order.site)
    if site.disabled:frappe.throw('The operating site is disabled.',frappe.PermissionError)
    if not frappe.db.get_value('User',user,'enabled') or 'TruCMMS Technician' not in frappe.get_roles(user):frappe.throw('Choose an enabled maintenance technician.')
    if not org.in_scope(order,user):frappe.throw('Scoped technician required.',frappe.PermissionError)
    members=[r for r in locked_sql(f'SELECT name,valid_from,valid_until,revoked_on FROM `tab{MEMBER}` WHERE team=%s AND user=%s AND discipline=%s FOR UPDATE',(team.name,user,order.required_discipline),as_dict=True) if active(r,at)]
    grants=[r for r in locked_sql(f'SELECT name,valid_from,valid_until,revoked_on FROM `tab{GRANT}` WHERE team=%s AND site=%s FOR UPDATE',(team.name,order.site),as_dict=True) if active(r,at)]
    if len(members)!=1 or len(grants)!=1:frappe.throw('Current membership and site authorization are required.',frappe.PermissionError)
    return members[0].name,grants[0].name

def validate_order(doc,old):
    if not old:
        if doc.team_policy not in (None,'','Managed') or doc.team_assignment:frappe.throw('New orders must use managed team eligibility.')
        doc.team_policy='Managed';return
    locked_sql('SELECT name FROM `tabTruCMMS Maintenance Work Order` WHERE name=%s FOR UPDATE',(doc.name,))
    cctx=frappe.flags.get('trucmms_c_action')
    if cctx and cctx['name']==doc.name and cctx['action']=='Reopen Order':return
    adoption=frappe.flags.get('trucmms_team_adoption')
    adopting=bool(adoption and adoption['name']==doc.name and old.team_policy=='Legacy')
    if doc.team_policy!=old.team_policy and not adopting:frappe.throw('Use controlled legacy adoption.',frappe.PermissionError)
    if doc.team_assignment!=old.team_assignment:frappe.throw('Assignment reference is server controlled.',frappe.PermissionError)
    changed=any(doc.get(f)!=old.get(f) for f in ('responsible_team','required_discipline','assigned_to'))
    if changed and not manager() and not (old.status=='Draft' and doc.status=='Draft' and not doc.assigned_to and 'TruCMMS Dispatcher' in frappe.get_roles()):frappe.throw('Supervisor assignment required.',frappe.PermissionError)
    if old.status in ('Closed','Cancelled','Technical Completed','Accepted') and (changed or adopting):frappe.throw('Team responsibility cannot change at this stage.')
    if doc.team_policy=='Legacy':
        if changed:frappe.throw('Adopt the open legacy order before changing its assignment.')
        return
    if doc.responsible_team and (changed or adopting or old.status=='Authorized' and doc.status=='Assigned'):
        team=frappe.get_doc(TEAM,doc.responsible_team);team.check_permission('read')
        if team.company!=doc.company:frappe.throw('Team and order company must match.')
    if doc.assigned_to and (changed or old.status=='Authorized' and doc.status=='Assigned' or adopting):
        membership,grant=eligibility(doc,lock=True)
        if doc.status=='Assigned' or cctx and cctx['action']=='Reassign Work' and doc.status=='On Hold':
            previous=frappe.flags.get('trucmms_assignment_insert');frappe.flags.trucmms_assignment_insert=True
            try:
                row=frappe.get_doc({'doctype':ASSIGN,'work_order':doc.name,'company':doc.company,'site':doc.site,'team':doc.responsible_team,'discipline':doc.required_discipline,'technician':doc.assigned_to,'membership':membership,'site_authorization':grant,'assigned_on':now_datetime(),'assigned_by':frappe.session.user,'reason':adoption['reason'] if adopting else 'Authorized technician assignment'}).insert(ignore_permissions=True)
                doc.team_assignment=row.name
            finally:frappe.flags.trucmms_assignment_insert=previous

def execution_check(order,user=None):
    if order.get('lifecycle_policy')=='C1':
        from vanbags_maintenance.allocations import execution_context
        execution_context(order,user or order.assigned_to)
    elif order.team_policy=='Managed':eligibility(order,user,lock=True)

@frappe.whitelist(methods=['POST'])
def adopt_legacy(work_order,team,discipline,reason):
    from vanbags_maintenance import work_orders as wo
    if not manager():frappe.throw('Supervisor role required.',frappe.PermissionError)
    if not (reason or '').strip():frappe.throw('Explain the legacy adoption.')
    locked_sql(f'SELECT name FROM `tab{wo.DT}` WHERE name=%s FOR UPDATE',(work_order,))
    doc=frappe.get_doc(wo.DT,work_order);doc.check_permission('write')
    if doc.team_policy!='Legacy' or doc.status not in ('Draft','Authorized','Assigned'):frappe.throw('Only open legacy orders may be adopted.')
    snapshot=doc.as_dict()
    previous=frappe.flags.get('trucmms_team_adoption');frappe.flags.trucmms_team_adoption={'name':doc.name,'reason':reason.strip()}
    try:
        doc.responsible_team=team;doc.required_discipline=discipline;doc.team_policy='Managed';doc.save()
        from vanbags_maintenance.work_cycle import event
        event(doc,'Adopt Team Eligibility',doc.status,reason.strip(),snapshot)
        return doc.as_dict()
    finally:frappe.flags.trucmms_team_adoption=previous

def validate_share(doc,method=None):
    if doc.share_doctype in (TEAM,MEMBER,GRANT):
        if doc.everyone:frappe.throw('Team records cannot be shared publicly.',frappe.PermissionError)
        permission(frappe.get_doc(doc.share_doctype,doc.share_name),doc.user,'read')
    elif doc.share_doctype==ASSIGN:
        from vanbags_maintenance.lifecycle import event_permission
        if doc.everyone:frappe.throw('Assignment history cannot be public.',frappe.PermissionError)
        event_permission(frappe.get_doc(ASSIGN,doc.share_name),doc.user,'read')


def assignment_query(user=None):
    from vanbags_maintenance import work_orders as wo
    condition=wo.query(user)
    return f"EXISTS (SELECT 1 FROM `tab{wo.DT}` WHERE `tab{wo.DT}`.name=`tab{ASSIGN}`.work_order AND ({condition}))" if condition else ''
