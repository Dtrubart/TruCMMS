"""Direct-order estimates and permission-aware advisory stock planning."""
import csv
import io
import frappe
from frappe.utils import getdate, now_datetime
from vanbags_maintenance import materials as mat, logistics, organization as org, work_orders as wo, job_plans

DT='TruCMMS Material Estimate'


def permission(doc,user=None,ptype=None):
    logistics.reader(user)
    if not org.in_scope(doc,user):frappe.throw('Company/Site authorization required.',frappe.PermissionError)
    return True


def query(user=None):
    if not org.privileged(user) and not logistics.READERS.intersection(frappe.get_roles(user)):return '1=0'
    return org.query(DT,user)


def validate(doc):
    logistics.reader()
    order=frappe.get_doc(wo.DT,doc.work_order);order.check_permission('read')
    if not org.in_scope(order):frappe.throw('Company/Site authorization required.',frappe.PermissionError)
    old=doc.get_doc_before_save()
    if old and any(doc.get(k)!=old.get(k) for k in ('work_order','company','site')):frappe.throw('Estimate scope cannot change.')
    doc.company,doc.site=order.company,order.site
    if order.status in ('Closed','Cancelled'):frappe.throw('Estimate only open work.')
    item=frappe.get_doc('Item',doc.item);item.check_permission('read')
    if item.disabled or item.has_variants:frappe.throw('Choose an enabled concrete Item.')
    doc.stock_uom=item.stock_uom
    doc.quantity=float(job_plans.finite(doc.quantity,'Estimated quantity',positive=True))
    if frappe.db.get_value('UOM',doc.stock_uom,'must_be_whole_number') and not doc.quantity.is_integer():frappe.throw('This stock UOM requires whole quantities.')
    doc.needed_on=getdate(doc.needed_on);job_plans.reason(doc.reason)
    if old and frappe.db.exists('TruCMMS Material Source',{'estimate':doc.name}):
        if any(str(doc.get(k))!=str(old.get(k)) for k in ('item','stock_uom','quantity','needed_on')):
            frappe.throw('Handed-off estimates are frozen. Add an explicit supplementary estimate if needed.')
        if doc.disabled and not old.disabled and frappe.db.exists('TruCMMS Material Source',{'estimate':doc.name,'active_key':['is','set']}):
            frappe.throw('Cancel the live purchase request before disabling its estimate.')


def forecast_rows(company,site,start,end):
    rows=frappe.get_list(DT,filters={'company':company,'site':site,'disabled':0,'needed_on':['between',[start,end]]},
        fields=['name','work_order','item','stock_uom','quantity','needed_on'],limit_page_length=301)
    if len(rows)>300:frappe.throw('Too many direct material estimates; shorten the period.')
    result=[]
    for row in rows:
        order=frappe.get_doc(wo.DT,row.work_order);order.check_permission('read')
        if order.status in ('Closed','Cancelled'):continue
        result.append(dict(key=mat.source_key('estimate:'+row.name,row.item,row.stock_uom),estimate=row.name,occurrence=None,
            plan=None,work_order=order.name,equipment=order.equipment,needed_on=str(row.needed_on),item=row.item,
            stock_uom=row.stock_uom,quantity=float(row.quantity)))
    return result


@frappe.whitelist(methods=['GET'])
def availability(company,site,from_date,to_date,warehouse):
    report=mat.forecast(company,site,from_date,to_date)
    mat.warehouse_for(company,site,warehouse)
    if not frappe.has_permission('Bin','read'):frappe.throw('Native stock balance permission required.',frappe.PermissionError)
    for row in report['totals']:
        frappe.get_doc('Item',row['item']).check_permission('read')
        bins=frappe.get_list('Bin',filters={'warehouse':warehouse,'item_code':row['item']},fields=['actual_qty','reserved_stock'],limit_page_length=1)
        balance=bins[0] if bins else frappe._dict(actual_qty=0,reserved_stock=0)
        row['actual_qty']=float(balance.actual_qty or 0);row['reserved_stock']=float(balance.reserved_stock or 0)
        row['available_now']=max(0,row['actual_qty']-row['reserved_stock'])
        row['suggested_purchase']=max(0,row['unrequested_quantity']-row['available_now'])
    report['warehouse']=warehouse;report['as_of']=str(now_datetime())
    report['basis']='Advisory snapshot: unrequested demand less current stock minus native reserved_stock. No reservation, future allocation or automatic purchase.'
    return report


@frappe.whitelist(methods=['GET'])
def shopping_csv(company,site,from_date,to_date):
    report=mat.forecast(company,site,from_date,to_date)
    output=io.StringIO(newline='');writer=csv.writer(output)
    def safe(value):
        value=str(value or '')
        return "'"+value if value.lstrip().startswith(('=','+','-','@')) else value
    writer.writerow(['Company','Site','Item','Stock UOM','Gross planned','Already requested','Not requested'])
    for row in report['totals']:
        writer.writerow([safe(company),safe(site),safe(row['item']),safe(row['stock_uom']),row['quantity'],row['already_requested'],row['unrequested_quantity']])
    frappe.local.response.filename='trucmms-shopping-list.csv'
    frappe.local.response.filecontent=output.getvalue().encode('utf-8-sig')
    frappe.local.response.type='download'


def validate_share(doc,method=None):
    if doc.share_doctype==DT:frappe.throw('Material estimates cannot be shared outside their scope.',frappe.PermissionError)
