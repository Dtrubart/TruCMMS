# Maintenance work orders — step 4

Native DocType: TruCMMS Maintenance Work Order. A dispatcher or supervisor creates/opens an order from an approved request. The conversion method serializes on the request and the request Link has a unique database constraint: repeated conversion returns the same order. The initial release supports one corrective order per approved request; preventive/inspection origins and multiple-order splitting require a later controlled extension.

Context (Company, Site, Equipment, Functional Location and source request) is immutable. Scope/subject/priority are editable in Draft and frozen on authorization. Workflow: Draft -> Authorize -> Authorized -> Assign -> Assigned, with business states on docstatus 0. TruCMMS Supervisor authorizes and assigns; assigned technicians must be enabled TruCMMS Technician users with Company and Site authorization. Assignment can be prepared while Authorized, but technician visibility starts only at Assigned. Reassignment preserves order identity and Version history, and removes the previous technician's access. The assigned technician is read-only until execution is implemented in step 5.

Supervisors can read submitted source requests but cannot change their triage decisions without the dispatcher role. Work order authorization and assignment identities/timestamps are server generated. There is no mandatory second-person approval for orders in this increment; the Supervisor role is the authorization boundary. Authorized orders cannot be deleted; no cancellation, completion or closure transitions are introduced yet.

Company/Site scopes apply to document/list/file access and sharing. Private attachment policy is shared with requests through supported native File extension hooks. Operational roles cannot bulk import, export or share work orders. System Manager retains administrative privileges subject to controller invariants.

The order has a distinct identity from ERPNext manufacturing Work Order. No stock, purchasing or accounting ledger is duplicated. Future task rows, job plan revision links and ERP transaction references can extend the order without changing existing IDs; their execution is not implemented here.

Local verification: 12 new server cases plus prior regressions; HTTP/Desk conversion from an approved request, duplicate conversion, supervisor authorization and assignment, denied dispatcher authorization, scoped technician read and denied technician edit. The original approved request and equipment/location references remain intact.
