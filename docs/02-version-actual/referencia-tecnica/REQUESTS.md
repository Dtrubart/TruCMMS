# Maintenance requests

TruCMMS Maintenance Request is a native Desk DocType with Company/Site scope and Equipment or Functional Location. Roles: TruCMMS Requester and TruCMMS Dispatcher; both require Company and Site User Permissions.

Draft -> Send Request -> Submitted -> Triage -> Under Review -> Approve/Reject -> Approved/Rejected. These are business states on docstatus 0. Requesters own their drafts and track their submitted requests; dispatchers see submitted requests within scope. A different dispatcher must make the decision. Rejection requires a reason. Original fault details and audit fields are protected after submission; final decisions are immutable. Submitted requests cannot be deleted.

Attachments are private uploaded files. File permissions, list queries and download checks follow request access, including revocation of the uploader's organizational scope. Evidence cannot be detached, reassigned or made public; final evidence cannot be changed/deleted. Native File is extended through Frappe extend_doctype_class; ERPNext/Frappe source is unchanged.

Installation/migration installs roles and creates the default workflow if absent. Existing workflows are preserved. The current controller supports the documented transitions; arbitrary workflow customization is not yet supported.

Verification on 2026-10-24: 73 server tests passed, including request workflow, private evidence and prior equipment/organization regressions. HTTP sessions verified ownership and site boundaries, private uploads/downloads, revocation, approval, reason-required rejection and requester tracking. A real Desk session opened Maintenance Requests from TruCMMS and displayed the final request form. No work-order creation is included.
