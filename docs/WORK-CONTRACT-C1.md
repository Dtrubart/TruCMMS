# Work-order contract C1

New orders use C1; earlier orders remain Legacy until explicit adoption. The supported V1 workflow is preserved inactive and a versioned C1 workflow handles both policies. Incompatible workflow customization requires upgrade review.

## Origins and planning

Requests generate orders through the existing authorized conversion service. Direct work uses POST `vanbags_maintenance.work_contract.create_direct` with Company, Site, equipment/location, scope, priority, reason and a stable client key. Repeating an identical key/input returns the same order; different input is rejected. PM and inspection origin providers are not enabled yet.

Scheduled start/end are a separate pair from Target Closure. Scheduling recovery after an expired deadline is permitted; it does not hide overdue work. After authorization, supervisors reschedule through a reasoned action preserving the previous values.

## Verification and site policy

Technical completion requires completed effective execution for every active allocation in the current cycle. The primary technician submits completion. A supervisor who did not execute work verifies it.

Site acceptance policy is snapshotted: By Origin requires acceptance for request work; Required requires a designated acceptor; Not Required permits closure after verification with explicit Not Applicable acceptance. Site edits do not rewrite current orders. Execution participants cannot verify or accept their own work. Supervisor acceptance on behalf requires a reason. Direct work can designate an eligible acceptor before execution when a reopened cycle requires one.

## Exceptions and assignments

Supervisors hold authorized/assigned work and resume to its previous state after eligibility checks. Execution and evidence recording are blocked while paused; backdated intervals cannot cross pauses. Reasoned reassignment or ending a secondary allocation while paused can resolve expired eligibility without enabling execution.

A responsible team may allocate multiple technicians/disciplines. Each participant needs personal Company/Site scope and current membership/eligibility. Team membership alone grants no work-order visibility. Execution records retain immutable allocation, discipline and team references. Changing the responsible team requires ending secondary allocations first.

Rework archives the old operational cycle and carries authorized allocations forward to a new cycle requiring new execution. Reopening a closed order archives the closure, snapshots the current site policy, and returns a new cycle to Authorized without an active assignment. Cancelled orders remain terminal. Earlier-cycle execution cannot be voided or edited.

## Evidence and migration

Lifecycle events and cycle archives are server authored; archived operational snapshots omit fields with higher permission levels. Technical completion/verification freeze evidence. Actions use transaction savepoints to avoid partial allocations, events or cycles on failure.

The migration distinguishes new-order initialization from legacy schema backfill. It preserves existing operational values and does not fabricate historical verification. Installation, populated upgrade, role/API/Desk scenarios, reconciliation and candidate recovery are release checks. This increment does not provide PM generation, inventory/cost integration, advanced calendars or specialized sector modules.
