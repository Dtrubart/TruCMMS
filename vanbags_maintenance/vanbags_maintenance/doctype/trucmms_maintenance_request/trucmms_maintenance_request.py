import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime
from vanbags_maintenance import organization as org
from vanbags_maintenance import requests as policy


class TruCMMSMaintenanceRequest(Document):
    def before_insert(self):
        self.owner=frappe.session.user
        self.requested_by=frappe.session.user
        if self.status not in (None,"","Draft"):
            frappe.throw("New requests must start in Draft.")
        self.status="Draft"
        self.submitted_on=self.reviewed_on=self.reviewed_by=None

    def before_validate(self):
        for field in ("subject","description","dispatcher_notes","rejection_reason"):
            self.set(field,(self.get(field) or "").strip())

    def validate(self):
        org.validate_context(self)
        old=self.get_doc_before_save()
        user=frappe.session.user
        if self.priority not in ("Low","Medium","High","Critical"):
            frappe.throw("Invalid request priority.")
        if not self.equipment and not self.functional_location:
            frappe.throw("Choose Equipment or Functional Location.")
        for field,doctype in [("equipment","VB Equipment"),("functional_location","VB Equipment Location")]:
            if self.get(field) and (not old or old.get(field)!=self.get(field) or old.site!=self.site):
                linked=frappe.get_doc(doctype,self.get(field))
                linked.check_permission("read")
                if linked.company!=self.company or linked.site!=self.site:
                    frappe.throw("Request references must belong to the selected Company and Site.")
                if linked.get("disabled"):frappe.throw("Cannot assign a disabled Functional Location.")
        if not old:
            if self.dispatcher_notes or self.rejection_reason:
                frappe.throw("Triage fields are reserved for dispatchers after submission.")
            return
        for field in ("owner","requested_by","submitted_on","reviewed_by","reviewed_on"):
            before,after=old.get(field),self.get(field)
            if field.endswith("_on") and before and after:before,after=get_datetime(before),get_datetime(after)
            if before!=after:frappe.throw("Request audit fields cannot be changed.")
        reporting=("company","site","equipment","functional_location","subject","description")
        if old.status!="Draft" and any(old.get(f)!=self.get(f) for f in reporting):
            frappe.throw("Submitted fault details are read-only.")
        if old.status in policy.FINAL and any(old.get(f)!=self.get(f) for f in reporting+("status","priority","dispatcher_notes","rejection_reason")):
            frappe.throw("Final requests are read-only.")
        triage_changed=any(old.get(f)!=self.get(f) for f in ("dispatcher_notes","rejection_reason"))
        if triage_changed and not (policy.dispatcher() and old.status in ("Submitted","Under Review")):
            frappe.throw("Only a dispatcher may edit triage fields after submission.",frappe.PermissionError)
        if self.status==old.status:return
        edge=(old.status,self.status)
        if edge==("Draft","Submitted"):
            if self.owner!=user or not (policy.REQUESTER in frappe.get_roles() or user=="Administrator"):
                frappe.throw("Only the requester may send this request.",frappe.PermissionError)
            self.submitted_on=now_datetime()
        elif edge==("Submitted","Under Review"):
            if not policy.dispatcher():frappe.throw("Dispatcher role required.",frappe.PermissionError)
        elif old.status=="Under Review" and self.status in policy.FINAL:
            if not policy.dispatcher() or user==self.owner:
                frappe.throw("A different dispatcher must decide the request.",frappe.PermissionError)
            if self.status=="Rejected" and not self.rejection_reason:
                frappe.throw("A rejection reason is required.")
            self.reviewed_by=user;self.reviewed_on=now_datetime()
        else:frappe.throw("Invalid request state transition.")

    def on_trash(self):
        if self.status!="Draft":frappe.throw("Submitted requests cannot be deleted.",frappe.PermissionError)
