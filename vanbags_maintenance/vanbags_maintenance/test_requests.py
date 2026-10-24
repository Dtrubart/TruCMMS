import uuid
import frappe
from frappe.tests import IntegrationTestCase
from frappe.model.workflow import apply_workflow
from frappe.utils.file_manager import save_file
from vanbags_maintenance import requests as policy
from vanbags_maintenance.test_support import org_context, grant_scope, COMPANY_A, SITE_A, SITE_A2


class TestRequests(IntegrationTestCase):
    def setUp(self):
        super().setUp();frappe.set_user("Administrator")
        frappe.db.savepoint("request_case")
        self.token="REQ-"+uuid.uuid4().hex[:10].upper()
        self.users={}
        for key,role in [("requester",policy.REQUESTER),("other",policy.REQUESTER),("dispatcher",policy.DISPATCHER)]:
            user=frappe.get_doc({"doctype":"User","email":self.token.lower()+key+"@example.com","first_name":"Request test","send_welcome_email":0,"roles":[{"role":role}]}).insert()
            self.users[key]=user.name;grant_scope(user.name)
        self.location=frappe.get_doc({"doctype":"VB Equipment Location",**org_context(),"location_name":self.token}).insert()
        self.foreign=frappe.get_doc({"doctype":"VB Equipment Location","company":COMPANY_A,"site":SITE_A2,"location_name":self.token+"OTHER"}).insert()

    def tearDown(self):
        frappe.set_user("Administrator");frappe.db.rollback(save_point="request_case");super().tearDown()

    def make(self,**values):
        frappe.set_user(self.users["requester"])
        return frappe.get_doc({"doctype":policy.REQUEST,**org_context(),"subject":"Fault report","description":"Unusual noise","priority":"Medium","functional_location":self.location.name,**values}).insert()

    def review(self,doc):
        frappe.set_user(self.users["requester"]);apply_workflow(doc.as_dict(),"Send Request")
        frappe.set_user(self.users["dispatcher"]);return apply_workflow(doc.as_dict(),"Triage")

    def test_requester_sends_dispatcher_approves(self):
        doc=self.make();self.assertEqual(doc.requested_by,self.users["requester"])
        doc=self.review(doc);doc.priority="High";doc.dispatcher_notes="Inspection required";doc.save(ignore_version=False)
        doc=apply_workflow(doc.as_dict(),"Approve")
        self.assertEqual(doc.status,"Approved");self.assertEqual(doc.reviewed_by,self.users["dispatcher"]);self.assertTrue(doc.submitted_on and doc.reviewed_on)
        self.assertTrue(frappe.db.exists("Version",{"ref_doctype":policy.REQUEST,"docname":doc.name}))
        frappe.set_user(self.users["requester"]);doc.check_permission("read")

    def test_rejection_requires_reason_and_preserves_decision(self):
        doc=self.review(self.make())
        with self.assertRaises(frappe.ValidationError):apply_workflow(doc.as_dict(),"Reject")
        doc.reload();doc.rejection_reason="Duplicate report";doc.save()
        doc=apply_workflow(doc.as_dict(),"Reject");self.assertEqual(doc.status,"Rejected");self.assertEqual(doc.rejection_reason,"Duplicate report")

    def test_other_requester_cannot_read_draft_or_submitted_request(self):
        doc=self.make();frappe.set_user(self.users["other"])
        self.assertEqual(frappe.get_list(policy.REQUEST,pluck="name"),[])
        with self.assertRaises(frappe.PermissionError):doc.check_permission("read")
        frappe.set_user(self.users["requester"]);doc=apply_workflow(doc.as_dict(),"Send Request")
        frappe.set_user(self.users["other"])
        with self.assertRaises(frappe.PermissionError):doc.check_permission("read")

    def test_dispatcher_cannot_read_someone_elses_draft(self):
        doc=self.make();frappe.set_user(self.users["dispatcher"])
        with self.assertRaises(frappe.PermissionError):doc.check_permission("read")
        self.assertEqual(frappe.get_list(policy.REQUEST,filters={"name":doc.name},pluck="name"),[])

    def test_requester_cannot_bypass_flow_or_edit_after_sending(self):
        doc=self.make();doc.status="Approved"
        with self.assertRaises(frappe.ValidationError):doc.save()
        doc.reload();doc=apply_workflow(doc.as_dict(),"Send Request")
        doc.description="Rewritten report"
        with self.assertRaises(frappe.PermissionError):doc.save()
        with self.assertRaises(frappe.ValidationError):apply_workflow(doc.as_dict(),"Approve")

    def test_new_request_cannot_start_approved_or_spoof_requester(self):
        with self.assertRaises(frappe.ValidationError):self.make(status="Approved")
        doc=self.make(requested_by=self.users["other"]);self.assertEqual(doc.requested_by,self.users["requester"])

    def test_reference_and_scope_validation(self):
        with self.assertRaises(frappe.PermissionError):self.make(functional_location=self.foreign.name)
        with self.assertRaises(frappe.ValidationError):self.make(functional_location=None)
        doc=self.make();frappe.set_user("Administrator")
        for name in frappe.get_all("User Permission",filters={"user":self.users["requester"]},pluck="name"):frappe.delete_doc("User Permission",name)
        frappe.set_user(self.users["requester"])
        with self.assertRaises(frappe.PermissionError):doc.check_permission("read")

    def test_dispatcher_cannot_rewrite_fault_or_forge_audit_fields(self):
        doc=self.review(self.make());doc.description="Changed original fault"
        with self.assertRaises(frappe.ValidationError):doc.save()
        doc.reload();doc.reviewed_by=self.users["dispatcher"]
        with self.assertRaises(frappe.ValidationError):doc.save()

    def test_self_approval_and_final_mutation_are_denied(self):
        doc=self.make();frappe.set_user("Administrator")
        user=frappe.get_doc("User",self.users["requester"]);user.append("roles",{"role":policy.DISPATCHER});user.save()
        frappe.set_user(self.users["requester"]);doc=apply_workflow(doc.as_dict(),"Send Request");doc=apply_workflow(doc.as_dict(),"Triage")
        with self.assertRaises(frappe.ValidationError):apply_workflow(doc.as_dict(),"Approve")
        frappe.set_user(self.users["dispatcher"]);doc=apply_workflow(doc.as_dict(),"Approve");doc.priority="Critical"
        with self.assertRaises(frappe.PermissionError):doc.save()
        frappe.set_user("Administrator")
        with self.assertRaises(frappe.PermissionError):frappe.delete_doc(policy.REQUEST,doc.name)

    def test_private_evidence_is_scoped_and_cannot_be_detached(self):
        doc=self.make();file=save_file(self.token+".txt",b"private fault evidence",policy.REQUEST,doc.name,is_private=1)
        file=frappe.get_doc("File",file.name)
        frappe.set_user(self.users["other"])
        with self.assertRaises(frappe.PermissionError):file.check_permission("read")
        with self.assertRaises(frappe.PermissionError):file.is_downloadable()
        self.assertEqual(frappe.get_list("File",filters={"name":file.name},pluck="name"),[])
        frappe.set_user(self.users["requester"]);file.attached_to_doctype=None;file.attached_to_name=None
        with self.assertRaises(frappe.PermissionError):file.save()
        frappe.set_user("Administrator")
        for name in frappe.get_all("User Permission",filters={"user":self.users["requester"]},pluck="name"):frappe.delete_doc("User Permission",name)
        frappe.set_user(self.users["requester"]);file.reload()
        with self.assertRaises(frappe.PermissionError):file.check_permission("read")
        with self.assertRaises(frappe.PermissionError):file.is_downloadable()

    def test_public_evidence_and_shared_visibility_bypasses_are_denied(self):
        doc=self.make()
        with self.assertRaises(frappe.ValidationError):save_file(self.token+"public.txt",b"must not be public",policy.REQUEST,doc.name,is_private=0)
        frappe.set_user("Administrator")
        with self.assertRaises(frappe.PermissionError):frappe.share.add(policy.REQUEST,doc.name,user=self.users["other"],notify=0)

    def test_file_cannot_be_made_public_or_deleted_after_decision(self):
        from pathlib import Path
        doc=self.make();file=save_file(self.token+"protected.txt",b"preserved evidence",policy.REQUEST,doc.name,is_private=1)
        file=frappe.get_doc("File",file.name);path=Path(file.get_full_path())
        file.is_private=0
        with self.assertRaises(frappe.ValidationError):file.save()
        self.assertTrue(path.exists())
        doc=self.review(doc);doc=apply_workflow(doc.as_dict(),"Approve")
        frappe.set_user("Administrator")
        with self.assertRaises(frappe.PermissionError):frappe.delete_doc("File",file.name)
        self.assertTrue(path.exists())
