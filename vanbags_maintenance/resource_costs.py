"""Read-through costs in Company currency; native documents own valuation."""
import frappe
from vanbags_maintenance import organization as org, work_orders as wo, logistics

DETAILS={'Purchase Invoice':'items','Timesheet':'time_logs'}


def validate_links(doc,method=None):
    old=doc.get_doc_before_save()
    for row in doc.get(DETAILS[doc.doctype]):
        if not row.get('trucmms_work_order'):continue
        order=frappe.get_doc(wo.DT,row.trucmms_work_order)
        if doc.company!=order.company or not org.in_scope(order):frappe.throw('Cost reference requires matching Company/Site authorization.',frappe.PermissionError)
        order.check_permission('read')
        if doc.doctype=='Purchase Invoice' and frappe.db.get_value('Item',row.item_code,'is_stock_item'):
            frappe.throw('Link service/non-stock invoice lines here; stock costs come from native inventory movements.')
        if doc.doctype=='Timesheet' and not doc.employee:frappe.throw('Internal labor costing requires the native Employee Timesheet.')
    if old and old.docstatus==1:
        before={r.name:r.get('trucmms_work_order') for r in old.get(DETAILS[doc.doctype])}
        if before!={r.name:r.get('trucmms_work_order') for r in doc.get(DETAILS[doc.doctype])}:
            frappe.throw('Submitted cost references cannot change.')


@frappe.whitelist(methods=['GET'])
def summary(order):
    logistics.reader()
    work=frappe.get_doc(wo.DT,order);work.check_permission('read')
    if not org.in_scope(work):frappe.throw('Company/Site authorization required.',frappe.PermissionError)
    result={'order':order,'currency':frappe.db.get_value('Company',work.company,'default_currency'),'components':{},'complete':True}
    entries=frappe.get_all('Stock Entry',filters={'trucmms_work_order':order,'docstatus':1},pluck='name')
    if not frappe.has_permission('Stock Ledger Entry','read') or any(not frappe.has_permission('Stock Entry','read',doc=n) for n in entries):
        result['components']['materials']={'available':False};result['complete']=False
    else:
        rows=[]
        for name in entries:
            ledger=frappe.get_list('Stock Ledger Entry',filters={'voucher_type':'Stock Entry','voucher_no':name,'is_cancelled':0},fields=['stock_value_difference'],limit_page_length=0)
            if len(ledger)!=frappe.db.count('Stock Ledger Entry',{'voucher_type':'Stock Entry','voucher_no':name,'is_cancelled':0}):
                result['components']['materials']={'available':False};result['complete']=False;break
            rows.append({'document':name,'cost':-sum(float(r.stock_value_difference) for r in ledger)})
        if 'materials' not in result['components']:result['components']['materials']={'available':True,'amount':sum(r['cost'] for r in rows),'documents':rows}
    for label,parent,child,amount in [('services','Purchase Invoice','Purchase Invoice Item','base_net_amount'),('labor','Timesheet','Timesheet Detail','base_costing_amount')]:
        if not frappe.has_permission(parent,'read'):
            result['components'][label]={'available':False};result['complete']=False;continue
        # Deliberately do not substitute zero for inaccessible source costs.
        rows=frappe.db.sql(f"""SELECT c.parent document,SUM(c.`{amount}`) cost FROM `tab{child}` c JOIN `tab{parent}` p ON p.name=c.parent
            WHERE c.trucmms_work_order=%s AND p.docstatus=1 AND p.company=%s GROUP BY c.parent""",(order,work.company),as_dict=True)
        if any(not frappe.has_permission(parent,'read',doc=r.document) for r in rows):
            result['components'][label]={'available':False};result['complete']=False;continue
        result['components'][label]={'available':True,'amount':sum(float(r.cost) for r in rows),'documents':rows}
    result['total']=sum(r['amount'] for r in result['components'].values()) if result['complete'] else None
    result['basis']='Net native stock valuation + non-stock invoice net amount (credit notes signed) + Employee Timesheet costing. Taxes, payment status and forecasts excluded. Reposting may revise stock valuation.'
    return result


def setup():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields({dt:[dict(fieldname='trucmms_work_order',label='Orden TruCMMS',fieldtype='Link',options=wo.DT,no_copy=0)] for dt in ('Purchase Invoice Item','Timesheet Detail')})


def guard_cost_child(doc,method=None):
    old=doc.get_doc_before_save()
    if doc.get('trucmms_work_order') or old and old.get('trucmms_work_order'):
        frappe.throw('Edit cost references through their native parent document.',frappe.PermissionError)


def native_permission(doc,user=None,ptype=None):
    for row in doc.get(DETAILS[doc.doctype]):
        if row.get('trucmms_work_order'):
            order=frappe.get_doc(wo.DT,row.trucmms_work_order)
            if doc.company!=order.company or not org.in_scope(order,user):
                frappe.throw('Maintenance costs require Company/Site authorization.',frappe.PermissionError)
    return True


def native_query(parent,child,user=None):
    clause=org.query(wo.DT,user)
    if not clause:return ''
    return f"NOT EXISTS (SELECT 1 FROM `tab{child}` c WHERE c.parent=`tab{parent}`.name AND COALESCE(c.trucmms_work_order,'')!='' AND NOT EXISTS (SELECT 1 FROM `tab{wo.DT}` WHERE `tab{wo.DT}`.name=c.trucmms_work_order AND ({clause})))"


def invoice_query(user=None):return native_query('Purchase Invoice','Purchase Invoice Item',user)
def timesheet_query(user=None):return native_query('Timesheet','Timesheet Detail',user)


def validate_share(doc,method=None):
    children={'Purchase Invoice':'Purchase Invoice Item','Timesheet':'Timesheet Detail'}
    if doc.share_doctype in children and frappe.db.exists(children[doc.share_doctype],{'parent':doc.share_name,'trucmms_work_order':['is','set']}):
        frappe.throw('Maintenance cost document access cannot be expanded through sharing.',frappe.PermissionError)

def before_cancel(doc,method=None):
    stored=frappe.get_doc(doc.doctype,doc.name)
    native_permission(stored)
    if stored.company!=doc.company or {r.name:r.get('trucmms_work_order') for r in stored.get(DETAILS[doc.doctype])}!={r.name:r.get('trucmms_work_order') for r in doc.get(DETAILS[doc.doctype])}:
        frappe.throw('Do not change cost references during cancellation.')
