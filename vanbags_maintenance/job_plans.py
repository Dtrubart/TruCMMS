"""R2.1: scoped procedures and immutable, explicitly approved revisions.

This library neither schedules occurrences nor opens orders or posts stock.
"""
import hashlib
import json
import math
import re
from decimal import Decimal, InvalidOperation

import frappe
from frappe.utils import now_datetime
from vanbags_maintenance import organization as org, teams
from vanbags_maintenance.work_contract import atomic

PLAN = 'TruCMMS Job Plan'
REVISION = 'TruCMMS Job Plan Revision'
EDITORS = {'TruCMMS Dispatcher', 'TruCMMS Supervisor'}
READERS = EDITORS | {'TruCMMS Technician'}
AUDIT = ('approved_by', 'approved_on', 'approval_reason', 'content_json', 'content_hash',
         'retired_by', 'retired_on', 'retirement_reason')


def editor():
    if not org.privileged() and not EDITORS.intersection(frappe.get_roles()):
        frappe.throw('Procedure editor role required.', frappe.PermissionError)


def supervisor():
    if not teams.manager():
        frappe.throw('Supervisor approval required.', frappe.PermissionError)


def permission(doc, user=None, ptype=None):
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    scoped = doc
    if doc.doctype == REVISION and doc.is_new() and doc.job_plan:
        parent = frappe.db.get_value(PLAN, doc.job_plan, ['company', 'site'], as_dict=True)
        if parent:
            scoped = frappe._dict(doctype=REVISION, **parent)
    if not org.in_scope(scoped, user) or not (org.privileged(user) or roles & READERS):
        frappe.throw('Procedure access requires an authorized Company, Site and role.', frappe.PermissionError)
    if not org.privileged(user) and not roles & EDITORS:
        if ptype in ('create', 'write', 'delete') or doc.doctype == REVISION and doc.status == 'Draft':
            frappe.throw('Draft procedures require an editor role.', frappe.PermissionError)
    return True


def scoped_query(dt, user=None):
    user = user or frappe.session.user
    if not org.privileged(user) and not set(frappe.get_roles(user)) & READERS:
        return '1=0'
    clause = org.query(dt, user) or '1=1'
    if dt == REVISION and not org.privileged(user) and not set(frappe.get_roles(user)) & EDITORS:
        clause += f" AND `tab{dt}`.status IN ('Approved','Retired')"
    return clause


def plan_query(user=None):
    return scoped_query(PLAN, user)


def revision_query(user=None):
    return scoped_query(REVISION, user)


def validate_share(doc, method=None):
    if doc.share_doctype in (PLAN, REVISION):
        frappe.throw('Procedure access is controlled by role and Company/Site; sharing is disabled.', frappe.PermissionError)


def validate_plan(doc):
    editor()
    org.validate_context(doc)
    old = doc.get_doc_before_save()
    if old and any(old.get(k) != doc.get(k) for k in ('code', 'company', 'site')):
        frappe.throw('Procedure identity and scope are permanent; create a separate procedure instead.')
    doc.code = (doc.code or '').strip()
    doc.plan_name = (doc.plan_name or '').strip()
    if not doc.code or not doc.plan_name:
        frappe.throw('Procedure code and name are required.')


def parent_for_revision(doc):
    parent = teams.locked_document(PLAN, doc.job_plan)
    parent.check_permission('read')
    if parent.disabled:
        frappe.throw('Cannot create or approve a revision for a disabled procedure.')
    return parent


def before_revision_insert(doc):
    editor()
    if doc.status not in (None, '', 'Draft') or any(doc.get(k) for k in AUDIT):
        frappe.throw('New revisions must be unapproved drafts.')
    if doc.revision_number or doc.revision_key or doc.previous_revision:
        frappe.throw('Revision identity is server controlled.')
    parent = parent_for_revision(doc)
    # Every creator serializes on the same stable parent, including API inserts.
    number = frappe.db.sql(f'SELECT COALESCE(MAX(revision_number),0)+1 FROM `tab{REVISION}` WHERE job_plan=%s', (parent.name,))[0][0]
    doc.revision_number = number
    doc.revision_key = f'{parent.name}-R{number:04d}'
    doc.company, doc.site, doc.status = parent.company, parent.site, 'Draft'


def finite(value, label, positive=False):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        frappe.throw(f'{label} must be a finite number.')
    if not number.is_finite() or not math.isfinite(float(number)) or positive and number <= 0:
        frappe.throw(f'{label} must be {"positive and " if positive else ""}finite.')
    return number


def key(value, seen, label):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,39}', value or '') or value in seen:
        frappe.throw(f'{label} must be unique and use letters, digits, underscores or hyphens.')
    seen.add(value)


def validate_content(doc):
    if not (doc.revision_title or '').strip() or not doc.tasks:
        frappe.throw('A revision title and at least one task are required.')
    task_keys = set()
    for task in doc.tasks:
        key(task.task_code, task_keys, 'Task code')
        if not (task.instructions or '').strip():
            frappe.throw('Every task needs instructions.')
        if finite(task.estimated_minutes or 0, 'Estimated minutes') < 0:
            frappe.throw('Estimated minutes cannot be negative.')
        if task.discipline and frappe.db.get_value('TruCMMS Discipline', task.discipline, 'disabled'):
            frappe.throw('Choose an active discipline.')
    metrics = set()
    for row in doc.measurements:
        key(row.metric_key, metrics, 'Measurement key')
        if row.task_code not in task_keys:
            frappe.throw('Each measurement must reference a task in this revision.')
        if not (row.metric_name or '').strip() or not row.unit:
            frappe.throw('Measurement name and unit are required.')
        if row.metric_kind not in ('Cumulative', 'Condition', 'Rate') or row.direction not in ('Increasing', 'Decreasing', 'Variable'):
            frappe.throw('Choose a supported measurement kind and direction.')
        if row.metric_kind == 'Cumulative' and row.direction != 'Increasing':
            frappe.throw('Cumulative counters must increase; use Condition for decreasing wear measurements.')
        if row.has_lower_limit:
            finite(row.lower_limit, 'Lower limit')
        if row.has_upper_limit:
            finite(row.upper_limit, 'Upper limit')
        if row.has_lower_limit and row.has_upper_limit and Decimal(str(row.lower_limit)) > Decimal(str(row.upper_limit)):
            frappe.throw('Lower limit cannot exceed upper limit.')
    for row in doc.materials:
        if row.task_code and row.task_code not in task_keys:
            frappe.throw('Material task must belong to this revision.')
        finite(row.quantity, 'Planned quantity', positive=True)
        item = frappe.get_doc('Item', row.item)
        item.check_permission('select')
        if item.disabled or item.has_variants:
            frappe.throw('Choose an active concrete Item, not an Item template.')
        if row.uom == item.stock_uom:
            factor = Decimal(1)
        else:
            conversion = next((u for u in item.uoms if u.uom == row.uom), None)
            if not conversion:
                frappe.throw('Planned UOM must be the stock UOM or an Item-specific conversion.')
            factor = finite(conversion.conversion_factor, 'Item UOM conversion', positive=True)
        row.item_name, row.stock_uom = item.item_name, item.stock_uom
        row.conversion_factor = float(factor)
        row.stock_quantity = float(finite(Decimal(str(row.quantity)) * factor, 'Converted stock quantity', positive=True))


def validate_revision(doc):
    editor()
    old = doc.get_doc_before_save()
    action = frappe.flags.get('trucmms_procedure_action')
    controlled = action == (doc.name, 'approve') or action == (doc.name, 'retire')
    if old and old.status != 'Draft':
        if action != (doc.name, 'retire') or old.status != 'Approved':
            frappe.throw('Approved revisions are immutable; create a new draft revision.')
        # Retirement changes disposition only; approved content stays byte-identical.
        allowed = {'status', 'retired_by', 'retired_on', 'retirement_reason', 'modified', 'modified_by'}
        for field in doc.meta.fields:
            if field.fieldname not in allowed and doc.get(field.fieldname) != old.get(field.fieldname):
                if field.fieldtype != 'Table' or [{f.fieldname:r.get(f.fieldname) for f in r.meta.fields} for r in doc.get(field.fieldname)] != [{f.fieldname:r.get(f.fieldname) for f in r.meta.fields} for r in old.get(field.fieldname)]:
                    frappe.throw('Retirement cannot change approved procedure content.')
        return
    parent = parent_for_revision(doc)
    if (doc.company, doc.site) != (parent.company, parent.site):
        frappe.throw('Revision scope must match its procedure.')
    org.validate_context(doc)
    if old and any(doc.get(k) != old.get(k) for k in ('job_plan', 'company', 'site', 'revision_number', 'revision_key', 'previous_revision')):
        frappe.throw('Revision identity, scope and ancestry are immutable.')
    if not controlled and (doc.status != 'Draft' or any(doc.get(k) != (old.get(k) if old else None) for k in AUDIT)):
        frappe.throw('Use the controlled approval and retirement actions.')
    validate_content(doc)
    if action == (doc.name, 'approve'):
        payload = content(doc, parent)
        doc.content_json = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        doc.content_hash = hashlib.sha256(doc.content_json.encode()).hexdigest()


def content(doc, parent):
    def rows(table, fields):
        return [{k:row.get(k) for k in fields} for row in doc.get(table)]
    return dict(schema='R2.1', job_plan=parent.name, plan_name=parent.plan_name,
                company=doc.company, site=doc.site, revision=doc.name,
                revision_number=doc.revision_number, title=doc.revision_title,
                change_reason=doc.change_reason, safety_notes=doc.safety_notes,
                tasks=rows('tasks', ('task_code', 'instructions', 'discipline', 'estimated_minutes', 'mandatory', 'evidence_required')),
                measurements=rows('measurements', ('task_code', 'metric_key', 'metric_name', 'metric_kind', 'unit', 'direction', 'required', 'has_lower_limit', 'lower_limit', 'has_upper_limit', 'upper_limit')),
                materials=rows('materials', ('task_code', 'item', 'item_name', 'quantity', 'uom', 'stock_uom', 'conversion_factor', 'stock_quantity', 'notes')))


def locked_revision(name):
    parent = frappe.db.get_value(REVISION, name, 'job_plan')
    if not parent:
        frappe.throw('Procedure revision not found.', frappe.DoesNotExistError)
    teams.locked_document(PLAN, parent)
    doc = teams.locked_document(REVISION, name)
    doc.check_permission('write')
    return doc


def reason(value):
    value = (value or '').strip()
    if not value:
        frappe.throw('A reason is required.')
    return value


@frappe.whitelist(methods=['POST'])
@atomic
def approve(name, approval_reason):
    supervisor()
    doc = locked_revision(name)
    if doc.status != 'Draft':
        frappe.throw('Only draft revisions can be approved.')
    doc.status = 'Approved'
    doc.approved_by, doc.approved_on, doc.approval_reason = frappe.session.user, now_datetime(), reason(approval_reason)
    previous = frappe.flags.get('trucmms_procedure_action')
    frappe.flags.trucmms_procedure_action = (doc.name, 'approve')
    try:
        doc.save()
    finally:
        frappe.flags.trucmms_procedure_action = previous
    return {'name':doc.name, 'status':doc.status, 'content_hash':doc.content_hash}


@frappe.whitelist(methods=['POST'])
@atomic
def retire(name, retirement_reason):
    supervisor()
    doc = locked_revision(name)
    if doc.status != 'Approved':
        frappe.throw('Only approved revisions can be retired.')
    doc.status = 'Retired'
    doc.retired_by, doc.retired_on, doc.retirement_reason = frappe.session.user, now_datetime(), reason(retirement_reason)
    previous = frappe.flags.get('trucmms_procedure_action')
    frappe.flags.trucmms_procedure_action = (doc.name, 'retire')
    try:
        doc.save()
    finally:
        frappe.flags.trucmms_procedure_action = previous
    return {'name':doc.name, 'status':doc.status}


@frappe.whitelist(methods=['POST'])
@atomic
def revise(name, change_reason):
    editor()
    source = locked_revision(name)
    if source.status not in ('Approved', 'Retired'):
        frappe.throw('Create a revision from an approved or retired procedure.')
    draft = frappe.get_doc({'doctype':REVISION, 'job_plan':source.job_plan,
        'revision_title':source.revision_title, 'change_reason':reason(change_reason),
        'safety_notes':source.safety_notes})
    for table in ('tasks', 'measurements', 'materials'):
        for row in source.get(table):
            draft.append(table, {f.fieldname:row.get(f.fieldname) for f in row.meta.fields})
    draft.insert()
    # Set ancestry through a server action, never a client-writable field.
    draft.db_set('previous_revision', source.name, update_modified=False)
    return {'name':draft.name, 'status':'Draft', 'revision_number':draft.revision_number}


@frappe.whitelist(methods=['GET','POST'])
def approved_snapshot(name):
    doc = frappe.get_doc(REVISION, name)
    doc.check_permission('read')
    if doc.status not in ('Approved', 'Retired') or not doc.content_json:
        frappe.throw('An approved procedure snapshot is required.')
    if hashlib.sha256(doc.content_json.encode()).hexdigest() != doc.content_hash:
        frappe.throw('Procedure snapshot integrity check failed.')
    return json.loads(doc.content_json)


def setup():
    from vanbags_maintenance import navigation
    from frappe.permissions import add_permission
    # Catalog selection only: no stock, purchase, finance or export permission.
    for dt in ('Item', 'UOM'):
        for role in EDITORS:
            if not frappe.has_permission(dt, 'select', user='Administrator'):
                frappe.throw('ERPNext catalog metadata is unavailable.')
            if not frappe.db.exists('Custom DocPerm', {'parent':dt, 'role':role, 'permlevel':0}):
                add_permission(dt, role, ptype='select')
        frappe.clear_cache(doctype=dt)
    navigation.setup()
