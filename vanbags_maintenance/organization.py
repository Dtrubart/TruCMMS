"""Company/site boundaries for TruCMMS, using native Frappe User Permissions."""
import frappe
from frappe.core.doctype.user_permission.user_permission import get_user_permissions
from frappe.permissions import get_allowed_docs_for_doctype


def privileged(user=None):
    user = user or frappe.session.user
    return user == "Administrator" or "System Manager" in frappe.get_roles(user)


def allowed(doctype, user=None):
    perms = get_user_permissions(user or frappe.session.user)
    return (get_allowed_docs_for_doctype(perms.get("Company", []), doctype),
            get_allowed_docs_for_doctype(perms.get("TruCMMS Site", []), doctype))


def in_scope(doc, user=None):
    if privileged(user):
        return True
    companies, sites = allowed(doc.doctype, user)
    site = doc.name if doc.doctype == "TruCMMS Site" else doc.get("site")
    return doc.get("company") in companies and site in sites


def has_permission(doc, user=None, ptype=None):
    # A hard boundary must not be overridden by Frappe's later DocShare fallback.
    if not in_scope(doc, user):
        frappe.throw("Company and site authorization is required.", frappe.PermissionError)
    return True  # Native role and User Permission checks still apply.


def validate_share(doc, method=None):
    if doc.share_doctype not in ("VB Equipment", "VB Equipment Location", "TruCMMS Site"):
        return
    target=frappe.get_doc(doc.share_doctype, doc.share_name)
    if doc.everyone or not in_scope(target, doc.user):
        frappe.throw("Sharing cannot cross Company or Site authorization boundaries.", frappe.PermissionError)


def query(doctype, user=None):
    if privileged(user):
        return ""
    companies, sites = allowed(doctype, user)
    if not companies or not sites:
        return "1=0"
    company_list = ",".join(frappe.db.escape(x) for x in companies)
    site_list = ",".join(frappe.db.escape(x) for x in sites)
    field = "name" if doctype == "TruCMMS Site" else "site"
    return f"`tab{doctype}`.company in ({company_list}) and `tab{doctype}`.`{field}` in ({site_list})"


def equipment_query(user=None):
    return query("VB Equipment", user)


def location_query(user=None):
    return query("VB Equipment Location", user)


def site_query(user=None):
    return query("TruCMMS Site", user)


def validate_context(doc):
    old = doc.get_doc_before_save()
    if old and old.get("company") and old.company != doc.company:
        frappe.throw("Company cannot be changed after creation.")
    if not in_scope(doc):
        frappe.throw("Company and site authorization is required.", frappe.PermissionError)
    if doc.doctype == "TruCMMS Site":
        return
    if doc.get("site"):
        site = frappe.db.get_value("TruCMMS Site", doc.site, ["company", "disabled"], as_dict=True)
        if site and site.company != doc.company:
            frappe.throw("Site must belong to the selected Company.")
        if site and site.disabled and (not old or old.get("site") != doc.site):
            frappe.throw("Cannot assign a disabled Site.")
    if doc.doctype == "VB Equipment" and doc.get("location"):
        location = frappe.db.get_value("VB Equipment Location", doc.location, ["company", "site"], as_dict=True)
        if location and (location.company != doc.company or location.site != doc.site):
            frappe.throw("Functional Location must belong to the selected Company and Site.")
    if doc.doctype == "VB Equipment Location":
        if old and old.get("site") and old.site != doc.site:
            frappe.throw("The Site of a Functional Location cannot be changed.")
        parent = doc.get("parent_location")
        seen = {doc.name}
        while parent:
            if parent in seen:
                frappe.throw("Functional Location hierarchy cannot contain a cycle.")
            seen.add(parent)
            row = frappe.db.get_value("VB Equipment Location", parent, ["company", "site", "parent_location", "disabled"], as_dict=True)
            if not row:
                break  # Native Link validation handles missing documents.
            if row.company != doc.company or row.site != doc.site:
                frappe.throw("Parent Functional Location must belong to the same Company and Site.")
            if parent == doc.get("parent_location") and row.disabled and (not old or old.get("parent_location") != parent):
                frappe.throw("Cannot assign a disabled Parent Functional Location.")
            parent = row.parent_location


def setup_company_selection():
    from frappe.permissions import add_permission
    for role in ("VB Maintenance User", "VB Maintenance Manager"):
        if not frappe.db.exists("Custom DocPerm", {"parent": "Company", "role": role, "permlevel": 0}):
            add_permission("Company", role, ptype="select")
    frappe.clear_cache(doctype="Company")
