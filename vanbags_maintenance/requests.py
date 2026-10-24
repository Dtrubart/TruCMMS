"""Request access, workflow installation and private evidence boundaries."""
import frappe
from vanbags_maintenance import organization as org
REQUEST = "TruCMMS Maintenance Request"
REQUESTER = "TruCMMS Requester"
DISPATCHER = "TruCMMS Dispatcher"
FINAL = ("Approved", "Rejected")


def dispatcher(user=None):
    user=user or frappe.session.user
    return user=="Administrator" or DISPATCHER in frappe.get_roles(user)


def can_read(doc, user=None):
    user=user or frappe.session.user
    if not org.in_scope(doc,user):return False
    if org.privileged(user):return True
    roles=frappe.get_roles(user)
    return (REQUESTER in roles and doc.owner==user) or ((DISPATCHER in roles or "TruCMMS Supervisor" in roles) and doc.status!="Draft")


def has_permission(doc, user=None, ptype=None):
    user=user or frappe.session.user
    if not can_read(doc,user):
        frappe.throw("Request access requires an authorized scope and request role.",frappe.PermissionError)
    if ptype in ("write","create") and not org.privileged(user):
        stored=frappe.db.get_value(REQUEST,doc.name,"status") if not doc.is_new() else "Draft"
        if not ((doc.owner==user and REQUESTER in frappe.get_roles(user) and stored=="Draft") or
                (dispatcher(user) and stored in ("Submitted","Under Review"))):
            frappe.throw("The request cannot be edited in its current state.",frappe.PermissionError)
    return True


def query(user=None):
    user=user or frappe.session.user
    scope=org.query(REQUEST,user)
    if org.privileged(user):return scope
    clauses=[]
    roles=frappe.get_roles(user)
    if REQUESTER in roles:clauses.append(f"`tab{REQUEST}`.owner={frappe.db.escape(user)}")
    if DISPATCHER in roles or "TruCMMS Supervisor" in roles:clauses.append(f"`tab{REQUEST}`.status!='Draft'")
    visibility="("+" OR ".join(clauses)+")" if clauses else "1=0"
    return f"({scope}) AND {visibility}"


def file_request(doc):
    if doc.attached_to_doctype in (REQUEST, "TruCMMS Maintenance Work Order", "TruCMMS Work Execution") and doc.attached_to_name:
        return frappe.get_doc(doc.attached_to_doctype,doc.attached_to_name)


def check_evidence_parent(parent,user=None,write=False,existing=False):
    if parent.doctype=="TruCMMS Work Execution":
        from vanbags_maintenance.execution import evidence_access
        return evidence_access(parent,user,write,existing)
    if not parent.has_permission("read",user=user):
        frappe.throw("Evidence access requires parent document access.",frappe.PermissionError)
    if write:
        if not parent.has_permission("write",user=user):
            frappe.throw("Evidence changes require parent write access.",frappe.PermissionError)
        if parent.status in FINAL:frappe.throw("Final request evidence is read-only.",frappe.PermissionError)


def file_permission(doc,user=None,ptype=None):
    parent=file_request(doc)
    if parent:
        check_evidence_parent(parent,user,write=ptype in ("write","create","delete"),existing=not doc.is_new())
    return True


def file_query(user=None):
    if org.privileged(user):return ""
    from vanbags_maintenance.work_orders import DT, query as work_order_query
    from vanbags_maintenance.execution import DT as EXECUTION, query as execution_query
    clauses=[]
    for dt,condition in ((REQUEST,query(user)),(DT,work_order_query(user)),(EXECUTION,execution_query(user))):
        if not frappe.db.exists("DocType",dt):continue
        clauses.append(f"(`tabFile`.attached_to_doctype!={frappe.db.escape(dt)} OR EXISTS (SELECT 1 FROM `tab{dt}` WHERE `tab{dt}`.name=`tabFile`.attached_to_name AND ({condition})))")
    return "(`tabFile`.attached_to_doctype IS NULL OR ("+" AND ".join(clauses)+"))"


def validate_file(doc,method=None):
    old=doc.get_doc_before_save()
    if old and old.attached_to_doctype in (REQUEST, "TruCMMS Maintenance Work Order", "TruCMMS Work Execution") and (old.attached_to_doctype,old.attached_to_name)!=(doc.attached_to_doctype,doc.attached_to_name):
        frappe.throw("Request evidence cannot be detached or reassigned.",frappe.PermissionError)
    parent=file_request(doc)
    if not parent:return
    if not doc.is_private or not (doc.file_url or "").startswith("/private/files/"):
        frappe.throw("Request attachments must be private uploaded files.")
    check_evidence_parent(parent,write=True,existing=not doc.is_new())


def before_delete_file(doc,method=None):
    parent=file_request(doc)
    if parent:
        check_evidence_parent(parent,write=True,existing=True)


def validate_share(doc,method=None):
    if doc.share_doctype==REQUEST:
        parent=frappe.get_doc(REQUEST,doc.share_name)
    elif doc.share_doctype=="File":
        parent=file_request(frappe.get_doc("File",doc.share_name))
    else:return
    if parent:
        from vanbags_maintenance.work_orders import can_read as work_order_read
        if parent.doctype=="TruCMMS Work Execution":
            from vanbags_maintenance.execution import has_permission as execution_permission
            readable=execution_permission(parent,doc.user,"read")
        else:
            readable = can_read(parent,doc.user) if parent.doctype==REQUEST else work_order_read(parent,doc.user)
        if not doc.everyone and readable:return
        
        frappe.throw("Sharing cannot expand request visibility.",frappe.PermissionError)


def setup():
    org.setup_company_selection()
    name="TruCMMS Request Workflow"
    if frappe.db.exists("Workflow",name):return
    for state in ("Draft","Submitted","Under Review","Approved","Rejected"):
        if not frappe.db.exists("Workflow State",state):frappe.get_doc({"doctype":"Workflow State","workflow_state_name":state}).insert(ignore_permissions=True)
    for action in ("Send Request","Triage","Approve","Reject"):
        if not frappe.db.exists("Workflow Action Master",action):frappe.get_doc({"doctype":"Workflow Action Master","workflow_action_name":action}).insert(ignore_permissions=True)
    states=[{"state":s,"doc_status":"0","allow_edit":REQUESTER if s=="Draft" else DISPATCHER if s not in FINAL else "System Manager"} for s in ("Draft","Submitted","Under Review","Approved","Rejected")]
    transitions=[{"state":a,"action":action,"next_state":b,"allowed":role,"allow_self_approval":int(b not in FINAL)} for a,action,b,role in [("Draft","Send Request","Submitted",REQUESTER),("Submitted","Triage","Under Review",DISPATCHER),("Under Review","Approve","Approved",DISPATCHER),("Under Review","Reject","Rejected",DISPATCHER)]]
    frappe.get_doc({"doctype":"Workflow","workflow_name":name,"document_type":REQUEST,"is_active":1,"workflow_state_field":"status","send_email_alert":0,"states":states,"transitions":transitions}).insert(ignore_permissions=True)


class RequestFileGuard:
    """Validate before native File methods perform irreversible disk changes."""
    def before_insert(self):
        parent=file_request(self)
        if parent:
            check_evidence_parent(parent,write=True,existing=False)
            if not self.is_private:frappe.throw("Request attachments must be private uploaded files.")
            if self.file_url and not self.file_url.startswith("/private/files/"):
                frappe.throw("Request attachments must be private uploaded files.")
        return super().before_insert()

    def validate(self):
        validate_file(self)
        return super().validate()

    def is_downloadable(self):
        file_permission(self, user=frappe.session.user, ptype="read")
        return super().is_downloadable()

    def on_trash(self):
        before_delete_file(self)
        return super().on_trash()
