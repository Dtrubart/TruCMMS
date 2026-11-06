"""Scoped adjacency tree and controlled, immediate location changes (ENT-002)."""
import hashlib
import json
from contextlib import contextmanager
from functools import wraps

import frappe
from frappe.utils import cint, now_datetime
from vanbags_maintenance import organization as org
from vanbags_maintenance.work_contract import atomic

LOCATION = 'VB Equipment Location'
EVENT = 'TruCMMS Location Event'
MAX_DEPTH = 64
MAX_NODES = 5000
PAGE_SIZE = 50


def conflict_message(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except frappe.QueryDeadlockError:
            frappe.throw('The hierarchy changed concurrently. Preview again and retry.', frappe.TimestampMismatchError)
    return wrapped


def text(value, label, optional=False):
    if optional and value in (None, ''):
        return ''
    if not isinstance(value, str) or not value.strip() or len(value) > 140:
        frappe.throw(f'Choose a valid {label}.')
    return value.strip()


def context(site, company=None):
    site = text(site, 'Site')
    doc = frappe.get_doc('TruCMMS Site', site)
    doc.check_permission('read')
    if company and text(company, 'Company') != doc.company:
        frappe.throw('Company and Site must match.')
    if not frappe.has_permission(LOCATION, 'read'):
        frappe.throw('Location read permission required.', frappe.PermissionError)
    return dict(company=doc.company, site=doc.name)


def read(name, write=False):
    doc = frappe.get_doc(LOCATION, text(name, 'Location'))
    doc.check_permission('write' if write else 'read')
    return doc


def lock(company):
    # Shared with asset placement: serialize hierarchy and placement mutations.
    frappe.db.sql('SELECT name FROM `tabCompany` WHERE name=%s FOR UPDATE', company)


def graph(company, site):
    # Current locking read, not a Repeatable Read snapshot from before the lock.
    rows = frappe.db.sql(f'''SELECT name, location_name, parent_location, disabled
        FROM `tab{LOCATION}` WHERE company=%s AND site=%s ORDER BY name
        LIMIT {MAX_NODES + 1} FOR UPDATE''', (company, site), as_dict=True)
    if len(rows) > MAX_NODES:
        frappe.throw('This hierarchy exceeds the controlled-change limit of 5000 locations. Contact an administrator.')
    return {r.name: dict(r) for r in rows}


def path(nodes, name):
    result, seen = [], set()
    while name:
        if name in seen:
            frappe.throw('Functional Location hierarchy cannot contain a cycle.')
        if name not in nodes:
            frappe.throw('Parent Functional Location must belong to the same Company and Site.')
        seen.add(name)
        if len(seen) > MAX_DEPTH:
            frappe.throw('Functional Location hierarchy is limited to 64 levels.')
        result.append(name)
        name = nodes[name].get('parent_location')
    return list(reversed(result))


def subtree(nodes, name):
    children = {}
    for row in nodes.values():
        children.setdefault(row.get('parent_location') or '', []).append(row['name'])
    result, pending = [], [name]
    while pending:
        current = pending.pop()
        if current in result:
            frappe.throw('Functional Location hierarchy cannot contain a cycle.')
        result.append(current)
        pending.extend(children.get(current, []))
    return sorted(result)


def readable(nodes, names, company, site):
    visible = set(frappe.get_list(LOCATION, filters={'company': company, 'site': site,
        'name': ['in', names]}, pluck='name', limit_page_length=MAX_NODES + 1))
    if visible != set(names):
        frappe.throw('All affected locations must be readable.', frappe.PermissionError)


@contextmanager
def internal(name):
    old = frappe.flags.get('trucmms_location_change')
    frappe.flags.trucmms_location_change = name
    try:
        yield
    finally:
        frappe.flags.trucmms_location_change = old


def validate(doc):
    old = doc.get_doc_before_save()
    structural = old and any((doc.get(k) or '') != (old.get(k) or '') for k in ('parent_location', 'disabled'))
    if structural and frappe.flags.get('trucmms_location_change') != doc.name:
        frappe.throw('Use Preview / Change hierarchy with a reason to change parent or status.')
    if doc.is_new():
        # Authorize before obtaining locks or looking at the site graph.
        org.validate_context(doc)
        lock(doc.company)
        nodes = graph(doc.company, doc.site)
        key = doc.name or '__new_location__'
        nodes[key] = dict(name=key, parent_location=doc.parent_location, disabled=doc.disabled)
        path(nodes, key)
        if doc.parent_location and any(nodes[n]['disabled'] for n in path(nodes, doc.parent_location)):
            frappe.throw('Choose an active parent path.')


def record(doc, action, reason, before, after):
    with internal(doc.name):
        return frappe.get_doc(dict(doctype=EVENT, location=doc.name, company=doc.company,
            site=doc.site, action=action, reason=reason, effective_on=now_datetime(),
            recorded_by=frappe.session.user, before_snapshot=json.dumps(before, sort_keys=True, default=str),
            after_snapshot=json.dumps(after, sort_keys=True, default=str))).insert(ignore_permissions=True)


def after_insert(doc):
    record(doc, 'Created', 'Location created', {}, dict(name=doc.name,
        label=doc.location_name, parent=doc.parent_location, disabled=doc.disabled))


def on_update(doc):
    old = doc.get_doc_before_save()
    if old and old.location_name != doc.location_name:
        record(doc, 'Label changed', 'Location label updated; identity retained',
            dict(label=old.location_name), dict(label=doc.location_name))


def prevent_delete(doc):
    frappe.throw('Locations retain their identity and history. Deactivate instead of deleting.')


def event_permission(doc, user=None, ptype=None):
    org.has_permission(doc, user, ptype)
    if ptype in ('write', 'delete', 'create'):
        return False
    if not frappe.get_doc(LOCATION, doc.location).has_permission('read', user=user):
        frappe.throw('Location read permission required.', frappe.PermissionError)
    return True


def event_query(user=None):
    return org.query(EVENT, user)


def event_share(doc, method=None):
    if doc.share_doctype == EVENT:
        frappe.throw('Location history cannot be shared.', frappe.PermissionError)


@frappe.whitelist(methods=['GET'])
def children(site, parent=None, start=0, search=None, company=None):
    filters = context(site, company)
    parent = text(parent, 'parent', optional=True)
    search = text(search, 'search', optional=True)
    start = cint(start)
    if start < 0 or start > MAX_NODES:
        frappe.throw('Invalid page offset.')
    if parent:
        doc = read(parent)
        if doc.company != filters['company'] or doc.site != filters['site']:
            frappe.throw('Parent must belong to the selected Site.')
    if search:
        filters['location_name'] = ['like', '%' + search.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%']
    else:
        filters['parent_location'] = parent or ['is', 'not set']
    rows = frappe.get_list(LOCATION, filters=filters,
        fields=['name', 'location_name', 'parent_location', 'disabled'], order_by='name asc',
        limit_start=start, limit_page_length=PAGE_SIZE + 1)
    visible = rows[:PAGE_SIZE]
    parents = set(frappe.get_list(LOCATION, filters={'company': filters['company'], 'site': filters['site'],
        'parent_location': ['in', [r.name for r in visible]]}, fields=['parent_location'],
        group_by='parent_location', pluck='parent_location', limit_page_length=PAGE_SIZE)) if visible else set()
    for row in visible:
        row.expandable = int(row.name in parents)
    return dict(rows=visible, more=len(rows) > PAGE_SIZE, start=start, limit=PAGE_SIZE)


@frappe.whitelist(methods=['GET'])
def details(name):
    doc = read(name)
    trail, seen, current = [], set(), doc
    while current:
        if current.name in seen or len(seen) >= MAX_DEPTH:
            frappe.throw('Invalid or excessively deep hierarchy; contact an administrator.')
        seen.add(current.name)
        trail.append(dict(name=current.name, label=current.location_name))
        current = read(current.parent_location) if current.parent_location else None
    events = frappe.get_list(EVENT, filters={'location': doc.name},
        fields=['name', 'action', 'reason', 'effective_on', 'recorded_by'],
        order_by='creation desc, name desc', limit_page_length=21)
    return dict(name=doc.name, company=doc.company, site=doc.site, label=doc.location_name,
        disabled=doc.disabled, parent=doc.parent_location, path=list(reversed(trail)),
        can_write=bool(frappe.has_permission(LOCATION, 'write', doc=doc)),
        events=events[:20], more_events=len(events) > 20)


def prepare(name, action, parent=None):
    doc = read(name, write=True)
    if action not in ('Reparent', 'Deactivate', 'Reactivate'):
        frappe.throw('Choose Reparent, Deactivate or Reactivate.')
    lock(doc.company)
    doc = frappe.get_doc(LOCATION, doc.name, for_update=True)
    doc.check_permission('write')
    context(doc.site, doc.company)
    if frappe.db.get_value('TruCMMS Site', doc.site, 'disabled'):
        frappe.throw('Hierarchy changes require an enabled Site.')
    nodes = graph(doc.company, doc.site)
    affected = subtree(nodes, doc.name)
    readable(nodes, affected, doc.company, doc.site)
    before = dict(path=path(nodes, doc.name), subtree=[dict(nodes[n]) for n in affected])
    readable(nodes, before['path'], doc.company, doc.site)
    parent = text(parent, 'parent', optional=True)
    if action == 'Reparent':
        if doc.disabled:
            frappe.throw('Reactivate the location before reparenting.')
        if parent == (doc.parent_location or ''):
            frappe.throw('Choose a different parent.')
        if parent:
            target = read(parent)
            if target.company != doc.company or target.site != doc.site:
                frappe.throw('Parent must belong to the same Company and Site.')
            for ancestor in path(nodes, parent):
                read(ancestor)
                if nodes[ancestor]['disabled']:
                    frappe.throw('Choose an active parent path.')
        nodes[doc.name]['parent_location'] = parent
        for n in affected:
            path(nodes, n)
    else:
        if parent:
            frappe.throw('Parent is only valid for Reparent.')
        disabled = int(action == 'Deactivate')
        if cint(doc.disabled) == disabled:
            frappe.throw('Location already has this status.')
        if disabled:
            if any(not nodes[n]['disabled'] for n in affected if n != doc.name):
                frappe.throw('Deactivate active descendants first.')
            if frappe.db.exists('VB Equipment', {'location': doc.name}) or frappe.db.exists(
                    'TruCMMS Measurement Point', {'functional_location': doc.name, 'disabled': 0}):
                frappe.throw('Relocate equipment and deactivate measurement points before deactivating this location.')
            if frappe.db.exists('TruCMMS Maintenance Work Order', {'status': ['not in', ['Closed', 'Cancelled']],
                    'functional_location': doc.name}) or frappe.db.exists('TruCMMS Maintenance Work Order', {
                    'status': ['not in', ['Closed', 'Cancelled']], 'scope_location': doc.name}):
                frappe.throw('Resolve open work before deactivating this location.')
            targets = frappe.db.sql('''SELECT t.name FROM `tabTruCMMS Work Target` t
                JOIN `tabTruCMMS Maintenance Work Order` w ON w.name=t.parent
                WHERE t.functional_location=%s AND w.status NOT IN ('Closed','Cancelled') LIMIT 1''', doc.name)
            if targets:
                frappe.throw('Resolve open work before deactivating this location.')
        elif doc.parent_location:
            for n in path(nodes, doc.parent_location):
                read(n)
                if nodes[n]['disabled']:
                    frappe.throw('Reactivate ancestors first.')
        nodes[doc.name]['disabled'] = disabled
    after = dict(path=path(nodes, doc.name), subtree=[dict(nodes[n]) for n in affected])
    payload = dict(name=doc.name, company=doc.company, site=doc.site, action=action, parent=parent,
        modified=str(doc.modified), before=before, after=after)
    token = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    return doc, payload, token


@frappe.whitelist(methods=['POST'])
@atomic
@conflict_message
def preview(name, action, parent=None):
    doc, payload, token = prepare(name, action, parent)
    return dict(token=token, affected=len(payload['before']['subtree']), before=payload['before']['path'],
        after=payload['after']['path'], action=action, name=doc.name)


@frappe.whitelist(methods=['POST'])
@atomic
@conflict_message
def change(name, action, token, reason, parent=None):
    if not isinstance(reason, str) or not 3 <= len(reason.strip()) <= 1000:
        frappe.throw('Provide a reason between 3 and 1000 characters.')
    doc, payload, expected = prepare(name, action, parent)
    if token != expected:
        frappe.throw('The hierarchy changed. Preview again before confirming.')
    with internal(doc.name):
        if action == 'Reparent':
            doc.parent_location = payload['parent'] or None
        else:
            doc.disabled = int(action == 'Deactivate')
        doc.save()
        event = record(doc, action, reason.strip(), payload['before'], payload['after'])
    return dict(name=doc.name, event=event.name, action=action)


def setup():
    from vanbags_maintenance import resource_calendars
    resource_calendars.setup()
    frappe.db.add_index(LOCATION, ['company', 'site', 'parent_location', 'name'], 'location_scope_parent')
    frappe.db.add_index(EVENT, ['location', 'creation'], 'location_event_history')
