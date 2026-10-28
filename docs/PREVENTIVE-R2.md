# R2 — native preventive maintenance

R2 extends the same TruCMMS/Frappe/ERPNext app and the R1 authorization, assignment, execution and independent verification lifecycle. Company/Site boundaries remain mandatory. No separate execution engine, stock ledger or invented maintenance request is introduced.

## Functional scope

| Block | Implemented contract |
| --- | --- |
| Procedure library | Scoped, versioned tasks, numeric measurement definitions and optional Item/UOM material estimates. Approved JSON/SHA-256 snapshot remains immutable; retirement retains history. |
| Calendar plans | Anchored day/week/month intervals, month-end clamping without fixed-calendar drift, or next due from validated actual execution. Approved operating timezone is frozen. Bounded preview/materialization creates occurrences, not orders. |
| Occurrences | Stable source identity, original due date, independent planned date, planned/released/validated/skipped/cancelled dispositions. Reasoned postponement never erases original lateness. Omission does not count as performed maintenance. |
| Order release | Manual or automatic release into Draft, preserving normal authorization and eligibility. Slot gates on start/verification/closure; scope plan/equipment/component/explicit Company-Site group. Equipment scope can explicitly include corrective work. Supervisor reasoned exceptions are audited. |
| Preventive execution | Genuine Preventive origin, frozen procedure/material provenance, task codes, mandatory tasks/measurements and discipline/evidence gates. Explicit start audit or effective execution indicates progress while the compatible C1 status remains Assigned. |
| Completion | Independent verification advances the preventive baseline using actual effective execution and, for meter plans, the recorded maintenance reading. Rework/reopen preserve cycles; released successors/later validated baselines require explicit reconciliation. |
| Meters | Cumulative counters, condition and rates with native UOM; chronological finite readings, retry keys, append-only latest-reading corrections and explicit reset/replacement epochs. Cumulative continuity survives counter reset. Stale data blocks unattended decisions. |
| Condition/usage | One primary trigger per plan; many independent plans per asset. Usage increments, below/above/outside thresholds, condition latching, and supervisor renewal after a skipped persistent condition. Corrected baselines require explicit rebase. |
| Components | Stable identities, exclusive equipment positions, append-only installation/removal, scoped rotation/transfer. Meter history follows component identity. Active plans/open work must be reconciled rather than silently retargeted. Whole-equipment site transfers carry current component/meter scope and preserve old reading/install contexts. |
| Inspections | Numeric results outside approved limits create findings. Supervisor review is required before verification. Action Required findings generate retry-safe genuine Inspection follow-up orders, still requiring authorization. Resolution requires closed follow-up work. |
| Native navigation | Plans/routines: Procedures, Plans, Preventive Schedule, Meters and Findings. Components under Assets. Readings, occurrence details, histories and events remain contextual. Calendar distinguishes programmed obligations, open/in-progress orders and validated/omitted/cancelled work. |

## Governance and automation

Draft procedures/plans are edited by dispatchers/supervisors, with supervisor activation and reasoned dispositions. Technicians read approved planning data within scope, record eligible execution/readings, and cannot grant themselves authority. Asset managers maintain components/meters. Sharing, import/export and deletion do not bypass server boundaries. Unversioned attachments to planning/audit records are blocked before writing files; execution evidence stays private on work records.

Plan configuration is frozen after activation; retire the plan and create a replacement when its rule changes. Existing obligations and order snapshots retain their original source. Procedure retirement/disablement blocks new releases against that revision. A calendar plan's approval fixes its timezone; nonexistent/ambiguous wall times require explicit valid scheduling rather than silent timestamp shifts.

Automation is opt-in per plan, requires an enabled explicitly scoped supervisor identity and never uses implicit Administrator authority. Committed start/execution/lifecycle events enqueue evaluation after commit; an hourly bounded reconciliation handles missed events and future windows. Every evaluation rechecks identity, active state, meter freshness and release constraints. Scheduled processing rotates its cursor to avoid starvation. Repeated/concurrent generation and readings use current locking reads and stable unique identities. Automatic work is opened as Draft, never automatically authorized or assigned. TEST scheduler is not enabled by this implementation; explicitly enqueued worker jobs still operate for opted-in demo plans.

## Temporal and functional limits

- Preview at most 367 inclusive days, calendar queries at most 94 inclusive days/500 rows with visible truncation, materialization at most one year ahead. Forecast preview and persisted occurrences are distinct. After-completion plans project only the next established obligation, not fictitious future completion dates.
- Readings are chronological; corrections target the latest uncorrected reading, with a mandatory reason. Replacement/reset starts a new epoch. Arbitrary retroactive history editing is not supported.
- Combined calendar/meter AND/OR policies, advanced resource optimization and predictive remaining-life models remain separately scoped future work. Condition-triggered recommendations are not validated prediction.
- Planned Item quantities are estimates. No stock reservation, purchase, consumption, return or financial posting is performed; R3 will use native ERPNext transactions.
- No specialized regulatory calibration certification, offline/mobile certification or production approval is claimed. Human pilot acceptance remains separate from tests.

## Verification

The regression suite retains R1/R2.1 coverage and adds calendar anchors, future-obligation/order separation, idempotence, skip/postpone/cancel, slot scope/events/overrides, opt-in automation, effective execution, independent verification, findings/follow-up, meter freshness/corrections/epochs, component positions/transfers and immutable provenance. Site deployment fingerprints are recorded after migration. Candidate evidence and human acceptance are recorded separately from this functional contract.
