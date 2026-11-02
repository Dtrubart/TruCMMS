# Technician execution — step 5

TruCMMS Work Execution is a native Desk record linked to the authorized work order. Its performed-task rows capture task, Completed/Partial/Blocked result and findings. The entry captures overall findings and actual start/end; the server calculates duration in minutes and stamps technician, owner, recorded time, Company and Site.

Only the enabled, scoped, currently assigned TruCMMS Technician can create an entry on an Assigned order. Work cannot be recorded before the current assignment or in the future. Positive durations and complete task rows are mandatory. A User-row lock serializes entries for the same technician; overlap checks use current locking reads across all orders. Adjacent intervals are allowed. This is elapsed technician time, not payroll, costing, machine downtime or a task-by-task time allocation.

Saved entries and task rows cannot be changed or deleted, including through direct child-document operations. The work order remains read-only to technicians; scope and authorization stay intact. Record Execution and Execution History buttons expose the native forms/lists. Completion/acceptance/closure remain step 6; Completed on a task is not completion of the order.

Private evidence can be appended by the recording technician while still assigned and authorized. Native upload_file requires parent write permission: the technician receives that narrow permission, while the entry controller rejects every saved-entry update. File guards separately prohibit editing, detaching, publishing or deleting recorded evidence, including through administrator APIs. Other technicians cannot attach evidence to someone else's entry. Supervisor/dispatcher visibility follows work-order access; scope revocation/reassignment removes previous technician access. The next assignee can read the existing history without impersonating its original author.

Corrections/voiding of recorded entries and time adjustments need a controlled subsequent design; this increment does not silently rewrite or subtract historical time. Mandatory evidence counts and sector-specific checklists/job-plan tasks are not implemented. Datetimes use the existing Frappe site/user conventions; no independent timezone system is introduced.

Verification: 97 local server tests passed (85 regressions and 12 execution cases). Native Desk/HTTP verification created an entry, recorded task findings and elapsed time, uploaded/downloaded private evidence, denied cross-scope access and unauthorized edits/deletion, and retained the original authorized order scope.
