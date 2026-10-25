"""Reasoned voids retain original execution and audit data."""
import frappe
from frappe.utils import now_datetime
from vanbags_maintenance import work_orders as wo
DT='TruCMMS Execution Adjustment'

def is_void(execution):
    return bool(frappe.db.exists(DT,{'execution':execution}))

def effective_latest(order,cycle):
    return frappe.db.sql("""select e.name from `tabTruCMMS Work Execution` e where e.work_order=%s and e.execution_cycle=%s
        and not exists(select 1 from `tabTruCMMS Execution Adjustment` a where a.execution=e.name)
        order by e.actual_end desc,e.creation desc limit 1""",(order,cycle),as_dict=True)

@frappe.whitelist(methods=['POST'])
def void_entry(execution,reason):
    reason=(reason or '').strip()
    if not reason:frappe.throw('A void reason is required.')
    entry=frappe.get_doc('TruCMMS Work Execution',execution)
    frappe.db.sql('select name from `tabTruCMMS Maintenance Work Order` where name=%s for update',(entry.work_order,))
    order=frappe.get_doc(wo.DT,entry.work_order);order.check_permission('read')
    if not wo.supervisor():frappe.throw('Supervisor authorization required.',frappe.PermissionError)
    if order.status!='Assigned':frappe.throw('Execution can be voided only while the order is Assigned.')
    if (entry.execution_cycle or 1)!=(order.execution_cycle or 1):frappe.throw('Execution from an archived cycle cannot be voided.')
    frappe.db.sql('select name from `tabUser` where name=%s for update',(entry.technician,))
    existing=frappe.db.get_value(DT,{'execution':execution},'name')
    if existing:return frappe.get_doc(DT,existing).as_dict()
    previous=frappe.flags.get('trucmms_void');frappe.flags.trucmms_void=execution
    try:
        doc=frappe.get_doc({'doctype':DT,'execution':execution,'work_order':order.name,'company':order.company,'site':order.site,
            'reason':reason,'actor':frappe.session.user,'occurred_on':now_datetime()}).insert(ignore_permissions=True)
        return doc.as_dict()
    finally:frappe.flags.trucmms_void=previous

def has_permission(doc,user=None,ptype=None):
    if not wo.can_read(frappe.get_doc(wo.DT,doc.work_order),user):frappe.throw('Work order access required.',frappe.PermissionError)
    if ptype in ('write','create','delete'):frappe.throw('Execution adjustments are immutable.',frappe.PermissionError)
    return True

def query(user=None):
    condition=wo.query(user)
    return f"EXISTS (SELECT 1 FROM `tab{wo.DT}` WHERE `tab{wo.DT}`.name=`tab{DT}`.work_order AND ({condition}))" if condition else ''

def validate_share(doc,method=None):
    if doc.share_doctype==DT:
        if doc.everyone:frappe.throw('Adjustments cannot be shared publicly.',frappe.PermissionError)
        has_permission(frappe.get_doc(DT,doc.share_name),doc.user,'read')
