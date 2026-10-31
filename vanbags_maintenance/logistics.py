"""R3.1: maintenance context over native ERPNext catalogs; no stock posting.

A site/warehouse binding restricts maintenance choices. It never grants native
Warehouse or Item access, and never represents stock ownership or availability.
"""
import hashlib

import frappe
from vanbags_maintenance import organization as org, work_orders as wo

DT = "TruCMMS Site Warehouse"
READERS = {"TruCMMS Supervisor", "TruCMMS Dispatcher"}


def reader(user=None):
    user = user or frappe.session.user
    if not org.privileged(user) and not READERS.intersection(frappe.get_roles(user)):
        frappe.throw("Maintenance planning role required for logistics.", frappe.PermissionError)


def editor():
    if not wo.supervisor():
        frappe.throw("A maintenance supervisor must configure site warehouses.", frappe.PermissionError)


def permission(doc, user=None, ptype=None):
    reader(user)
    if not org.in_scope(doc, user):
        frappe.throw("Logistics requires Company and Site authorization.", frappe.PermissionError)
    if doc.warehouse:
        if not frappe.has_permission("Warehouse", "read", doc=frappe.get_doc("Warehouse", doc.warehouse), user=user):
            frappe.throw("Native Warehouse read permission required.", frappe.PermissionError)
    return True


def query(user=None):
    user = user or frappe.session.user
    if not org.privileged(user) and not READERS.intersection(frappe.get_roles(user)):
        return "1=0"
    if not frappe.has_permission("Warehouse", "read", user=user):
        return "1=0"
    # Run native permission filtering as the requested user, including Warehouse
    # tree User Permissions. No custom SQL reconstruction of native boundaries.
    original = frappe.session.user
    try:
        if original != user:
            frappe.set_user(user)
        names = frappe.get_list("Warehouse", pluck="name", limit_page_length=0)
    finally:
        if original != user:
            frappe.set_user(original)
    if not names:
        return "1=0"
    native = ",".join(frappe.db.escape(name) for name in names)
    return f"({org.query(DT, user) or '1=1'}) AND `tab{DT}`.warehouse IN ({native})"


def validate_binding(doc):
    editor()
    org.validate_context(doc)
    warehouse = frappe.get_doc("Warehouse", doc.warehouse)
    warehouse.check_permission("read")
    if warehouse.company != doc.company:
        frappe.throw("Warehouse must belong to the Site Company.")
    if not doc.disabled and (warehouse.disabled or warehouse.is_group):
        frappe.throw("Choose an enabled, non-group native Warehouse.")
    key = hashlib.sha256(f"{doc.company}\0{doc.site}\0{doc.warehouse}".encode()).hexdigest()
    old = doc.get_doc_before_save()
    if old and any(old.get(k) != doc.get(k) for k in ("company", "site", "warehouse", "binding_key")):
        frappe.throw("Warehouse binding identity is permanent; disable it and create another binding.")
    if doc.binding_key and doc.binding_key != key:
        frappe.throw("Warehouse binding identity is server controlled.")
    if not (doc.change_reason or "").strip():
        frappe.throw("Explain the warehouse authorization or change.")
    doc.change_reason = doc.change_reason.strip()
    doc.binding_key = key


def validate_share(doc, method=None):
    if doc.share_doctype == DT:
        frappe.throw("Logistics access cannot be expanded through sharing.", frappe.PermissionError)


def order_context(order):
    reader()
    doc = frappe.get_doc(wo.DT, order)
    doc.check_permission("read")
    return doc


def warehouses(doc):
    # Native get_list enforces both the mapping's maintenance scope and native
    # warehouse permissions. Recheck current native status, not cached snapshots.
    rows = frappe.get_list(DT, filters={"company": doc.company, "site": doc.site, "disabled": 0},
                           fields=["name", "warehouse"], order_by="warehouse", limit_page_length=0)
    return [row for row in rows if not any(frappe.db.get_value("Warehouse", row.warehouse,
                                                             ["disabled", "is_group"]))
            and frappe.db.get_value("Warehouse", row.warehouse, "company") == doc.company]


@frappe.whitelist(methods=["GET"])
def context(order):
    doc = order_context(order)
    can_read_warehouse = bool(frappe.has_permission("Warehouse", "read"))
    return {"work_order": doc.name, "company": doc.company, "site": doc.site,
            "warehouses": warehouses(doc) if can_read_warehouse else [],
            "can_read_warehouse": can_read_warehouse,
            "can_read_item": bool(frappe.has_permission("Item", "read")),
            "posts_stock": False, "reserves_stock": False}


@frappe.whitelist(methods=["GET"])
def item_choices(order, search="", kind="All", limit=20):
    order_context(order)
    if kind not in ("All", "Stock", "Non-stock"):
        frappe.throw("Choose All, Stock or Non-stock.")
    if isinstance(limit, bool) or str(limit) not in {str(i) for i in range(1, 51)}:
        frappe.throw("Catalog limit must be an integer between 1 and 50.")
    search = str(search or "").strip()
    if len(search) > 100:
        frappe.throw("Catalog search is limited to 100 characters.")
    filters = {"disabled": 0, "has_variants": 0}
    if kind != "All":
        filters["is_stock_item"] = int(kind == "Stock")
    # Native Item read permission is required. Maintenance does not silently add
    # stock roles, expose valuation rates, or bypass Item User Permissions.
    return frappe.get_list("Item", filters=filters,
        or_filters=[["item_code", "like", f"%{search}%"], ["item_name", "like", f"%{search}%"]] if search else None,
        fields=["name", "item_name", "stock_uom", "is_stock_item", "has_batch_no", "has_serial_no"],
        order_by="name", limit_page_length=int(limit))


def setup():
    from vanbags_maintenance import r2_records, configuration, materials, fulfillment, resource_costs
    materials.setup()
    fulfillment.setup()
    resource_costs.setup()
    r2_records.setup()
    frappe.db.add_index(DT, ["company", "site", "disabled"], "site_warehouse_scope")
    configuration.record_deployment()
