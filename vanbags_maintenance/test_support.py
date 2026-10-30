"""Explicit organization fixtures; only called by the test runner."""
import frappe
COMPANY_A = "TruCMMS Test A"
COMPANY_B = "TruCMMS Test B"
SITE_A = "CMMS-TEST-A1"
SITE_A2 = "CMMS-TEST-A2"
SITE_B = "CMMS-TEST-B1"


def stock_catalog():
    """Test-only prerequisites for headless installs without setup-wizard data."""
    if not frappe.in_test:
        raise RuntimeError('Stock test catalogs must not be seeded outside tests.')
    group = frappe.db.get_value('Item Group', {'parent_item_group':['is','not set']}, 'name')
    if not group:
        group = frappe.get_doc({'doctype':'Item Group','item_group_name':'TruCMMS Stock Test Root','is_group':1}).insert().name
    if not frappe.db.exists('UOM','Nos'):
        frappe.get_doc({'doctype':'UOM','uom_name':'Nos','must_be_whole_number':1}).insert()
    return group


def prepare_organization():
    original=frappe.session.user
    frappe.set_user("Administrator")
    try:
        # Native Company creation expects the setup-wizard Transit warehouse type.
        if not frappe.db.exists("Warehouse Type", "Transit"):
            frappe.get_doc({"doctype":"Warehouse Type","name":"Transit"}).insert()
        for company, abbr in [(COMPANY_A,"TCMA"),(COMPANY_B,"TCMB")]:
            if not frappe.db.exists("Company", company):
                frappe.get_doc({"doctype":"Company","company_name":company,"abbr":abbr,"country":"Canada","default_currency":"CAD"}).insert()
        for code,company in [(SITE_A,COMPANY_A),(SITE_A2,COMPANY_A),(SITE_B,COMPANY_B)]:
            if not frappe.db.exists("TruCMMS Site",code):
                frappe.get_doc({"doctype":"TruCMMS Site","site_code":code,"site_name":code,"company":company}).insert()
        frappe.db.commit()
    finally:
        frappe.set_user(original)


def org_context():
    return {"company":COMPANY_A,"site":SITE_A}


def grant_scope(user, company=COMPANY_A, site=SITE_A):
    original=frappe.session.user
    frappe.set_user("Administrator")
    try:
        for allow,value in [("Company",company),("TruCMMS Site",site)]:
            if not frappe.db.exists("User Permission",{"user":user,"allow":allow,"for_value":value,"apply_to_all_doctypes":1}):
                frappe.get_doc({"doctype":"User Permission","user":user,"allow":allow,"for_value":value,"apply_to_all_doctypes":1}).insert()
    finally:
        frappe.set_user(original)
