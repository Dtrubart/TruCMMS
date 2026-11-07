"""Optional administrative organization; membership never grants site access."""
import hashlib
import json
import re
from contextlib import contextmanager

import frappe
from frappe.utils import cint, now_datetime
from vanbags_maintenance import organization as org, location_hierarchy as h
from vanbags_maintenance.work_contract import atomic

UNIT = 'TruCMMS Operating Unit'
EVENT = 'TruCMMS Organization Event'
SITE = 'TruCMMS Site'
MAX_UNITS = 5000
MAX_DEPTH = 64
PAGE_SIZE = 50


def manager(company=None):
    if not org.privileged():
        frappe.throw('System Manager required to configure operational organization.', frappe.PermissionError)
    if company:
        frappe.get_doc('Company', company).check_permission('read')


def nodes(company, locking=False):
    rows = frappe.db.sql(f'''SELECT name,company,unit_code,unit_name,unit_type,parent_unit,disabled
        FROM `tab{UNIT}` WHERE company=%s ORDER BY name LIMIT {MAX_UNITS + 1}
        {'FOR UPDATE' if locking else ''}''', company, as_dict=True)
    if len(rows) > MAX_UNITS:
        frappe.throw('Organization exceeds the limit of 5000 units per Company.')
    return {row.name: dict(row) for row in rows}


def path(graph, name):
    result, seen = [], set()
    while name:
        if name in seen:
            frappe.throw('Operating Unit hierarchy cannot contain a cycle.')
        if name not in graph:
            frappe.throw('Parent Operating Unit must belong to the same Company.')
        seen.add(name)
        if len(seen) > MAX_DEPTH:
            frappe.throw('Operating Unit hierarchy is limited to 64 levels.')
        result.append(dict(graph[name]))
        name = graph[name].get('parent_unit')
    return list(reversed(result))


def active_path(graph, name):
    rows = path(graph, name)
    if any(cint(row['disabled']) for row in rows):
        frappe.throw('Choose an active Operating Unit path.')
    return rows


def visible_units(user=None):
    """Read only the ancestry of explicitly authorized sites, without regional grants."""
    user = user or frappe.session.user
    if not frappe.has_permission(SITE, 'read', user=user):
        return set()
    # Existing Site hooks and native User Permissions remain authoritative.
    sites = frappe.get_list(SITE, fields=['company', 'operating_unit'],
        filters={'operating_unit': ['is', 'set']}, limit_page_length=10001, user=user)
    if len(sites) > 10000:
        frappe.throw('Too many authorized sites for this organization view; use a narrower account scope.')
    result, graphs = set(), {}
    for site in sites:
        if site.company not in graphs:
            graphs[site.company] = nodes(site.company)
        graph = graphs[site.company]
        if site.operating_unit in graph:
            result.update(row['name'] for row in path(graph, site.operating_unit))
    return result


def permission(doc, user=None, ptype=None):
    if org.privileged(user):
        return True
    if ptype not in (None, 'read', 'select') or doc.name not in visible_units(user):
        frappe.throw('Operating Unit is outside your authorized sites.', frappe.PermissionError)
    return True


def query(user=None):
    if org.privileged(user):
        return ''
    allowed = visible_units(user)
    return '`tab'+UNIT+'`.name IN ('+','.join(frappe.db.escape(x) for x in sorted(allowed))+')' if allowed else '1=0'


def event_permission(doc, user=None, ptype=None):
    if not org.privileged(user) or ptype in ('create', 'write', 'delete'):
        frappe.throw('Organization history is restricted to administrators and immutable.', frappe.PermissionError)
    return True


def event_query(user=None):
    return '' if org.privileged(user) else '1=0'


@frappe.whitelist(methods=['GET', 'POST'])
def link_title(doctype, docname):
    # Native get_link_title reads the title without checking the document scope.
    # Protect organization and Site labels; retain native behavior for other types.
    if doctype in (UNIT, SITE):
        doc = frappe.get_doc(doctype, h.text(docname, 'document'))
        doc.check_permission('read')
        return doc.unit_name if doctype == UNIT else doc.site_name
    from frappe.desk.search import get_link_title
    return get_link_title(doctype, docname)


def validate_share(doc, method=None):
    if doc.share_doctype in (UNIT, EVENT):
        frappe.throw('Organization access cannot be expanded through sharing.', frappe.PermissionError)


@contextmanager
def internal(name):
    old = frappe.flags.get('trucmms_organization_change')
    frappe.flags.trucmms_organization_change = name
    try:
        yield
    finally:
        frappe.flags.trucmms_organization_change = old


def record(company, action, reason, before, after, unit=None, site=None):
    old = frappe.flags.get('trucmms_organization_event')
    frappe.flags.trucmms_organization_event = True
    try:
        return frappe.get_doc(dict(doctype=EVENT, company=company, operating_unit=unit, site=site,
            action=action, reason=reason, effective_on=now_datetime(), recorded_by=frappe.session.user,
            before_snapshot=json.dumps(before, sort_keys=True, default=str),
            after_snapshot=json.dumps(after, sort_keys=True, default=str))).insert(ignore_permissions=True)
    finally:
        frappe.flags.trucmms_organization_event = old


def validate_unit(doc):
    manager(doc.company)
    doc.unit_code = (doc.unit_code or '').strip().upper()
    doc.unit_name = (doc.unit_name or '').strip()
    doc.unit_type = (doc.unit_type or '').strip()
    if not re.fullmatch(r'[A-Z0-9._-]{1,50}', doc.unit_code) or not doc.unit_name:
        frappe.throw('Provide a name and a unit code of 1 to 50 letters, numbers, dots, underscores or hyphens.')
    if len(doc.unit_name) > 140 or len(doc.unit_type) > 60:
        frappe.throw('Unit name is limited to 140 characters and optional type to 60.')
    old = doc.get_doc_before_save()
    if old:
        if (doc.company, doc.unit_code) != (old.company, old.unit_code):
            frappe.throw('Company and Unit Code are permanent.')
        if any((doc.get(k) or '') != (old.get(k) or '') for k in ('parent_unit', 'disabled')):
            if frappe.flags.get('trucmms_organization_change') != doc.name:
                frappe.throw('Use Preview / Change organization with a reason.')
    else:
        h.lock(doc.company)
        graph = nodes(doc.company, locking=True)
        if any(row['unit_code'] == doc.unit_code for row in graph.values()):
            frappe.throw('Unit Code must be unique within the Company.')
        if doc.parent_unit:
            active_path(graph, doc.parent_unit)
        graph[doc.name] = dict(name=doc.name, company=doc.company, unit_code=doc.unit_code,
            unit_name=doc.unit_name, unit_type=doc.unit_type, parent_unit=doc.parent_unit, disabled=doc.disabled)
        path(graph, doc.name)


def unit_created(doc):
    record(doc.company, 'Unit created', 'Operating Unit created', {},
        dict(name=doc.name, label=doc.unit_name, unit_type=doc.unit_type, parent_unit=doc.parent_unit), unit=doc.name)


def unit_updated(doc):
    old = doc.get_doc_before_save()
    if old and any(doc.get(k) != old.get(k) for k in ('unit_name', 'unit_type')):
        record(doc.company, 'Unit label changed', 'Operating Unit label/type updated; identity retained',
            dict(label=old.unit_name, unit_type=old.unit_type), dict(label=doc.unit_name, unit_type=doc.unit_type), unit=doc.name)


def validate_site(doc):
    old = doc.get_doc_before_save()
    unit = doc.get('operating_unit')
    if old and (old.get('operating_unit') or '') != (unit or ''):
        if frappe.flags.get('trucmms_organization_change') != doc.name:
            frappe.throw('Use Assign Operating Unit with preview and reason.')
    if unit and (not old or old.get('operating_unit') != unit):
        manager(doc.company)
        if doc.disabled:
            frappe.throw('Enable the Site before assigning an Operating Unit.')
        h.lock(doc.company)
        active_path(nodes(doc.company, locking=True), unit)


def site_created(doc):
    if doc.get('operating_unit'):
        record(doc.company, 'Site linked', 'Initial administrative membership', {},
            dict(operating_unit=doc.operating_unit, path=path(nodes(doc.company), doc.operating_unit)),
            unit=doc.operating_unit, site=doc.name)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def reason_text(reason):
    if not isinstance(reason, str) or not 3 <= len(reason.strip()) <= 1000:
        frappe.throw('Provide a reason between 3 and 1000 characters.')
    return reason.strip()


def prepare_unit(name, action, parent=None):
    manager()
    doc = frappe.get_doc(UNIT, h.text(name, 'Operating Unit'))
    doc.check_permission('write'); manager(doc.company)
    h.lock(doc.company)
    doc = frappe.get_doc(UNIT, doc.name, for_update=True)
    graph = nodes(doc.company, locking=True)
    before = path(graph, doc.name)
    original = {name: dict(row) for name, row in graph.items()}
    parent = h.text(parent, 'Parent Unit', optional=True)
    if action == 'Reparent':
        if doc.disabled or parent == (doc.parent_unit or ''):
            frappe.throw('Choose a different parent for an active unit.')
        if parent:
            active_path(graph, parent)
        graph[doc.name]['parent_unit'] = parent
        # Check moved descendants as well as the selected node; no partial truncation.
        for name in graph:
            path(graph, name)
    elif action in ('Deactivate', 'Reactivate'):
        disabled = int(action == 'Deactivate')
        if cint(doc.disabled) == disabled or parent:
            frappe.throw('Choose a different status without a parent value.')
        if disabled:
            if any(row['parent_unit'] == doc.name and not row['disabled'] for row in graph.values()) or frappe.db.exists(SITE, {'operating_unit': doc.name}):
                frappe.throw('Resolve active child units and detach associated sites first.')
        elif doc.parent_unit:
            active_path(graph, doc.parent_unit)
        graph[doc.name]['disabled'] = disabled
    else:
        frappe.throw('Choose Reparent, Deactivate or Reactivate.')
    affected = [name for name in graph if doc.name in [row['name'] for row in path(graph, name)]]
    sites = frappe.db.sql(f'''SELECT name,operating_unit FROM `tab{SITE}`
        WHERE company=%(company)s AND operating_unit IN %(units)s ORDER BY name LIMIT 10001 FOR UPDATE''',
        {'company': doc.company, 'units': tuple(affected)}, as_dict=True)
    if len(sites) > 10000:
        frappe.throw('Too many affected sites; contact an administrator before reorganizing.')
    if action == 'Deactivate' and sites:
        frappe.throw('Detach associated sites before deactivating this branch.')
    after = path(graph, doc.name)
    return doc, dict(action=action, parent=parent, modified=str(doc.modified), before=before,
        after=after, affected=[graph[n] for n in sorted(affected)],
        affected_before=[original[n] for n in sorted(affected)], sites=sites)


@frappe.whitelist(methods=['POST'])
@atomic
@h.conflict_message
def preview_unit(name, action, parent=None):
    doc, payload = prepare_unit(name, action, parent)
    return dict(token=digest(payload), affected=len(payload['affected']), affected_sites=len(payload['sites']),
        before=payload['before'], after=payload['after'])


@frappe.whitelist(methods=['POST'])
@atomic
@h.conflict_message
def change_unit(name, action, token, reason, parent=None):
    reason = reason_text(reason)
    doc, payload = prepare_unit(name, action, parent)
    if token != digest(payload):
        frappe.throw('Organization changed. Preview again before confirming.')
    with internal(doc.name):
        if action == 'Reparent': doc.parent_unit = parent or None
        else: doc.disabled = int(action == 'Deactivate')
        doc.save()
    event = record(doc.company, action, reason, dict(path=payload['before'], affected=payload['affected_before'], sites=payload['sites']),
        dict(path=payload['after'], affected=payload['affected'], sites=payload['sites']), unit=doc.name)
    return dict(name=doc.name, event=event.name)


def prepare_site(site, unit=None):
    manager()
    doc = frappe.get_doc(SITE, h.text(site, 'Site'))
    doc.check_permission('write'); manager(doc.company)
    h.lock(doc.company)
    doc = frappe.get_doc(SITE, doc.name, for_update=True)
    unit = h.text(unit, 'Operating Unit', optional=True)
    if unit == (doc.get('operating_unit') or ''):
        frappe.throw('Choose a different unit, or clear it to detach the site.')
    graph = nodes(doc.company, locking=True)
    before = path(graph, doc.operating_unit) if doc.operating_unit else []
    if unit and doc.disabled:
        frappe.throw('Enable the Site before assigning an Operating Unit.')
    after = active_path(graph, unit) if unit else []
    return doc, dict(site=doc.name, company=doc.company, unit=unit, modified=str(doc.modified),
        before=dict(operating_unit=doc.operating_unit, path=before), after=dict(operating_unit=unit or None, path=after))


@frappe.whitelist(methods=['POST'])
@atomic
@h.conflict_message
def preview_site(site, unit=None):
    doc, payload = prepare_site(site, unit)
    return dict(token=digest(payload), before=payload['before'], after=payload['after'])


@frappe.whitelist(methods=['POST'])
@atomic
@h.conflict_message
def assign_site(site, token, reason, unit=None):
    reason = reason_text(reason)
    doc, payload = prepare_site(site, unit)
    if token != digest(payload):
        frappe.throw('Site or organization changed. Preview again before confirming.')
    with internal(doc.name):
        doc.operating_unit = payload['unit'] or None
        doc.save()
    event = record(doc.company, 'Site linked' if unit else 'Site detached', reason,
        payload['before'], payload['after'], unit=unit or None, site=doc.name)
    return dict(site=doc.name, event=event.name)


@frappe.whitelist(methods=['GET'])
def children(company, parent=None, start=0, search=None):
    company = h.text(company, 'Company')
    if org.privileged(): manager(company)
    elif company not in org.allowed(SITE)[0]:
        frappe.throw('Company authorization required.', frappe.PermissionError)
    if not frappe.has_permission(UNIT, 'read'):
        frappe.throw('Operating Unit read permission required.', frappe.PermissionError)
    filters = dict(company=company)
    parent = h.text(parent, 'Parent Unit', optional=True)
    search = h.text(search, 'search', optional=True)
    if parent:
        doc = frappe.get_doc(UNIT, parent); doc.check_permission('read')
        if doc.company != company: frappe.throw('Parent must belong to the selected Company.')
    if search:
        filters['unit_name'] = ['like', '%'+search.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')+'%']
    else:
        filters['parent_unit'] = parent or ['is', 'not set']
    start = cint(start)
    if not 0 <= start <= MAX_UNITS: frappe.throw('Invalid page offset.')
    rows = frappe.get_list(UNIT, filters=filters, fields=['name','unit_name','unit_code','unit_type','disabled'],
        order_by='unit_code asc,name asc', limit_start=start, limit_page_length=PAGE_SIZE+1)
    return dict(rows=rows[:PAGE_SIZE], more=len(rows)>PAGE_SIZE, limit=PAGE_SIZE)


@frappe.whitelist(methods=['GET'])
def details(name):
    doc = frappe.get_doc(UNIT, h.text(name, 'Operating Unit')); doc.check_permission('read')
    trail = path(nodes(doc.company), doc.name)
    for row in trail: frappe.get_doc(UNIT, row['name']).check_permission('read')
    sites = frappe.get_list(SITE, filters={'company': doc.company, 'operating_unit': doc.name}, fields=['name','site_name'],
        order_by='name asc', limit_page_length=51)
    return dict(name=doc.name, company=doc.company, label=doc.unit_name, code=doc.unit_code,
        unit_type=doc.unit_type, disabled=doc.disabled, path=trail, sites=sites[:50], more_sites=len(sites)>50,
        can_manage=org.privileged())


def setup():
    h.setup()
    frappe.db.add_unique(UNIT, ['company', 'unit_code'], 'operating_unit_company_code')
    frappe.db.add_index(UNIT, ['company', 'parent_unit'], 'operating_unit_parent')
    frappe.db.add_index(SITE, ['company', 'operating_unit'], 'site_operating_unit')
    frappe.db.add_index(EVENT, ['company', 'effective_on'], 'organization_history')
