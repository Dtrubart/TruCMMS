# R4 — Advanced operations and customer configurability

Approved direction: resource availability, qualifications, template-based forms and document requirements, assisted scheduling optimization, grouped work, online field UX, contractor governance and an integrated pilot. R5 owns reliability/failure prediction; R6 owns offline mobile.

## Sequence

1. R4.1 Availability/capacity: explicit person working windows and absences; site-local daily load, free capacity and conflicts.
2. R4.2 Qualifications: skills, certificates, validity and intervention requirements, extending existing discipline/team eligibility.
3. R4.3 Configurable formats: supplied templates, guided editor, versions, preview/publication and conditional evidence requirements.
4. R4.4 Preparation/documents: applicability, reviews, validity and controlled execution holds.
5. R4.5 Assisted scheduling: proposals considering capacity, skills, operating windows, dependencies and R3 resources; planner confirms changes.
6. R4.6 Coordinated work: parent/child work, campaigns, shutdowns and emergencies.
7. R4.7 Online field workspace and equipment QR/barcode access.
8. R4.8 Contractor qualification, documentation and work evaluation over native ERPNext providers/services.
9. R4.9 Reconciled operational reporting and representative user pilot.

## First increment: capacity windows

The first delivery provides a native Resource Window DocType and Resources and services → Capacity and availability page. Supervisors configure person/site working intervals and absences; dispatchers consult them. Technicians may read their own scoped windows and query their own capacity directly. Team membership never grants broader work visibility.

Intervals are explicit; define one window per shift (including an overnight shift). Repeating weekly patterns and bulk calendar generation remain a follow-up within R4.1. No 8-hour default is assumed: a day without a working window displays Unconfigured. This is advisory planning, not automatic assignment or a replacement for current eligibility checks.

Capacity subtracts absences from working windows. Load includes primary and secondary current allocations on Authorized, Assigned and On Hold orders. Every participant uses the full scheduled order interval in this increment; effort per participant and partial participation need the later scheduling contract. Technical-completed/closed/cancelled work does not occupy future capacity. Work without dates is listed separately when visible.

One person cannot have overlapping same-kind windows, even at different sites. Other-site work and absences can consume availability without exposing their private document identifiers. Configuration changes retain native Version history and a required reason; records are disabled instead of deleted. The view reflects current configuration, not a frozen historical capacity ledger.

Dates entered through native forms follow ERPNext timezone controls. Capacity groups intervals by the operating site's timezone and measures elapsed time across midnight and DST transitions. Maximum query horizon is 31 days; the service bounds result sizes.

Technical verification and deployment evidence must be recorded against the final revision. R4 as a whole remains in development.
