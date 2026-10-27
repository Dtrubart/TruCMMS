# R2 — preventive maintenance, approved design and incremental delivery

R2 extends TruCMMS as an installable native Frappe/ERPNext app. The human-approved design includes diverse measurements, a clear separation between planned occurrences and open orders, controlled release policies, optional planned materials, and component-level follow-up. It does not replace the R1 work-order lifecycle.

## R2.1 — procedure library

Native documents: **TruCMMS Job Plan** (stable procedure identity and Company/Site scope), **TruCMMS Job Plan Revision**, and child tables for tasks, measurement definitions and planned materials.

- Dispatchers and supervisors edit drafts within authorized Company and Site. Supervisors approve and retire revisions with a mandatory reason. Technicians read approved/retired revisions in scope; requesters have no library access. Sharing, import, export and deletion are disabled.
- Revision numbers are allocated under the parent row lock. Approval freezes a canonical JSON snapshot and SHA-256 hash, instructions, task flags, measurements, material labels and Item-specific UOM conversion. A new revision copies the procedure and links its ancestor; no edit rewrites an approved revision. Retirement preserves the approved snapshot for history.
- Procedures may contain tasks only. Optional numeric definitions distinguish cumulative measurements (hours, distance, energy, total volume), condition (including decreasing tread depth) and rates (such as flow). Units use native ERPNext UOM, with explicit optional lower/upper limits so zero remains meaningful. These are definitions, not meter readings, threshold triggers or execution enforcement yet.
- Optional Item-linked material estimates require positive quantities and an Item-specific valid UOM. Template/disabled Items are rejected. Approval rechecks catalog state. Converted stock quantity is a planning value only; no stock reservation, purchase request, stock entry or costing transaction is created. Dispatchers/supervisors receive catalog select permission only, not stock/finance write permission.
- Procedure scope is one Company/Site. Reuse across equipment within that scope does not require duplicate procedures. Cross-site/global template publication is not implied by membership or sharing and needs an explicit future policy.
- Native navigation: Planes y rutinas → Procedimientos → Revisiones. Revisions remain contextual, not a second top-level module. Existing work orders and execution rules are unchanged.

## Approved remaining increments

| Increment | Scope | Acceptance target |
| --- | --- | --- |
| R2.2 | Calendar plans, fixed calendar vs interval from validated maintenance, preview and stable future occurrences | Weekly work can be mapped months ahead without creating months of open orders. |
| R2.3 | Controlled manual/automatic release, predecessor event and active-order limits per plan/equipment/component or explicit control group | Retry-safe generation; manual overrides, omissions, postponements and cancellations retain distinct reasons/history. |
| R2.4 | Preventive execution through R1 orders, closure, next due and compliance | Original due dates remain auditable; skipped work never counts as performed maintenance. |
| R2.5 | Meter readings, cumulative/condition/rate rules, corrections and replacement history | Hours/km/kWh/flow/wear remain semantically distinct; stale data is visible. |
| R2.6 | Maintainable components, inspections, findings and reviewed intervention recommendations | Component identity, installation position and measurement history remain separate; findings lead to traceable corrective work. |

Future occurrences and released work orders are separate objects. Release does not bypass authorization, eligibility, assignment or execution. Initial recommended control is one active order per plan/equipment, with broader locking optional; final policy settings are implemented and tested in R2.3. A major PM replacing a minor PM requires an explicit approved rule; no silent suppression is assumed.

Predictive remaining-life models, advanced combined calendar/meter scheduling and transactional ERPNext stock/procurement/costing remain separately scoped deliveries. Condition recommendations are not a claim of validated prediction. Site scheduler activation and production deployment require their own operational decisions.

## Verification and rollout

R2.1 integration tests cover task-only content, approval authority, immutable revisions, retirement, ancestry/numbering, Company/Site boundaries, forged fields, catalog conversions, diverse metric definitions, disabled catalog rechecks, no order/stock side effects and native permission restrictions. Existing R1 tests remain regression coverage. DEV receives schema/configuration only; synthetic examples belong to TEST. Human acceptance remains separate from automatic tests.
