"""Append-only technician execution and immutable private evidence."""
import frappe
from vanbags_maintenance import work_orders as wo
from vanbags_maintenance import organization as org
DT='TruCMMS Work Execution'


def order_for_recording(name, user=None, lock=False):
    user=user or frappe.session.user
    if lock:
        rows=frappe.db.sql('select * from `tabTruCMMS Maintenance Work Order` where name=%s for update',(name,),as_dict=True)
        if not rows:frappe.throw('Work order not found.',frappe.DoesNotExistError)
        order=frappe.get_doc({'doctype':wo.DT,**rows[0]})
    else:
        order=frappe.get_doc(wo.DT,name)
    if not order.has_permission('read',user=user):frappe.throw('Work order access required.',frappe.PermissionError)
    from vanbags_maintenance.allocations import current
    allocated=current(order,user)
    if (not org.in_scope(order,user) or order.status!='Assigned' or (order.assigned_to!=user and not allocated)
            or wo.TECHNICIAN not in frappe.get_roles(user) or not frappe.db.get_value('User',user,'enabled')):
        frappe.throw('Only the currently assigned, authorized technician may record execution.',frappe.PermissionError)
    from vanbags_maintenance.teams import execution_check
    execution_check(order,user)
    return order


def has_permission(doc,user=None,ptype=None):
    user=user or frappe.session.user
    if ptype=='create' or doc.is_new():
        if doc.work_order:order_for_recording(doc.work_order,user)
        elif wo.TECHNICIAN not in frappe.get_roles(user):frappe.throw('Technician role required.',frappe.PermissionError)
        return True
    order=frappe.get_doc(wo.DT,doc.work_order)
    if not wo.can_read(order,user):frappe.throw('Execution access requires work order access.',frappe.PermissionError)
    if ptype=='write':
        from vanbags_maintenance.adjustments import is_void
        if is_void(doc.name):frappe.throw('Voided execution evidence is frozen.',frappe.PermissionError)
        # Native upload_file requires parent write permission. The controller still
        # rejects every update to a saved entry; only evidence may be appended.
        if doc.technician!=user:frappe.throw('Only the recording technician may append evidence.',frappe.PermissionError)
        order_for_recording(doc.work_order,user)
    if ptype in ('delete','submit','cancel'):frappe.throw('Saved execution history is immutable.',frappe.PermissionError)
    return True


def query(user=None):
    condition=wo.query(user)
    if not condition:return ''
    return f"EXISTS (SELECT 1 FROM `tab{wo.DT}` WHERE `tab{wo.DT}`.name=`tab{DT}`.work_order AND ({condition}))"


def evidence_access(parent,user=None,write=False,existing=False):
    has_permission(parent,user,'read')
    if write:
        from vanbags_maintenance.adjustments import is_void
        if is_void(parent.name):frappe.throw('Voided execution evidence is frozen.',frappe.PermissionError)
        if existing:frappe.throw('Recorded execution evidence cannot be changed or deleted.',frappe.PermissionError)
        if parent.technician!=(user or frappe.session.user):frappe.throw('Only the recording technician may append evidence.',frappe.PermissionError)
        order=order_for_recording(parent.work_order,user)
        if (parent.execution_cycle or 1)!=(order.execution_cycle or 1):frappe.throw('Evidence from an earlier execution cycle is frozen.',frappe.PermissionError)


def validate_share(doc,method=None):
    if doc.share_doctype==DT:
        parent=frappe.get_doc(DT,doc.share_name)
        if doc.everyone:frappe.throw('Execution cannot be shared publicly.',frappe.PermissionError)
        has_permission(parent,doc.user,'read')
