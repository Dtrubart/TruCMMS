# TruCMMS E1 — shared work views and mobile execution

`/desk/trucmms-work` is a native Frappe Desk Page. List, My Work, Date Agenda and Calendar share one permission-aware service; the existing native work-order List remains accessible. Company, Site, equipment, status and date-basis filters do not grant additional access.

My Work means current actionable primary/additional technician allocations in Assigned or On Hold, with legacy primary assignments supported. It is not a requester inbox or a team-wide view. Actor selection is never accepted from the client. Execution still rechecks assignment, Company/Site scope, current team eligibility, cycle and evidence rules on the server.

## Dates

Scheduled uses the planned start/end interval; Closure Target is a distinct milestone, with no invented execution duration. Without Schedule means no planned interval. These definitions do not change the legacy Work Register's Unscheduled filter (no closure target). Agenda and Calendar require an explicit Scheduled or Closure Target basis and an ordered civil-date window of at most 93 days. The end of a scheduled interval is exclusive: an interval ending at midnight does not occupy the next day.

Selecting a Site uses its operating timezone; otherwise the view uses the User timezone, falling back to the system timezone. Responses include explicit UTC and offset timestamps. Date grouping and boundary conversion come from server rules, without relying on a device's timezone library. Calendar is read only; changes continue through authorized reasoned rescheduling on the order.

The feed returns at most 500 authorized orders and signals truncation prominently. List pagination and per-day Calendar/Agenda disclosure do not claim complete counts when the server limit is exceeded. Narrow the filters for a complete bounded result. This is not an advanced scheduler or a load/performance certification.

## Current timezone rules

Native Frappe Desk's bundled timezone data was older than the current Vancouver rules. The app includes official moment-timezone 0.6.5 packed IANA 2026e data under its MIT license and loads it through Moment's supported API only when the platform data is older. No Frappe/ERPNext source files are changed. Backend conversions use the matching pinned `tzdata==2026.5` dependency. Native Datetime controls and the custom views are tested against the same current rules, including Vancouver's November 2026 permanent UTC-07 behavior and historical 23/25-hour days.

The system storage clock is not shifted. If the platform's system timezone offset disagrees with the current maintenance rules, technical recording/views fail explicitly until platform timezone data is updated. Operator timezone-data upgrades and the platform's other timezone-dependent capabilities remain part of release readiness. Newer platform browser timezone data is never downgraded by the app.

## Mobile and retry safety

Native execution forms use an accessible primary Submit Execution action and an Add Private Evidence action for eligible saved entries. Empty unused grid placeholder rows are ignored; partially entered tasks remain subject to validation. Forms retain unsaved changes and submission identity on validation or connection errors. Keep the same form open and retry after an uncertain response; no offline persistence is claimed.

The POST submission service scopes a UUID to the authenticated actor, hashes canonical payload contents, serializes work/user checks and stores a unique identity on the immutable execution. Same-key, same-content retries return the original readable execution; changed contents conflict and link to the saved record for review. Generic CRUD cannot forge these fields. Existing executions keep null submission fields; no historical keys are fabricated. A controlled concurrent transaction conflict may require retrying the same request/key.

Validation includes a 390×844 touch browser, a deliberately lost successful server response, correction after validation failure, duplicate suppression, concurrent submissions, native private file upload, Guest download denial and absence of page-level horizontal overflow. This does not certify every phone, browser, camera or intermittent/offline environment.

## Boundaries

No PM engine, automatic dispatch, optimization, drag/drop schedule editing, offline queues or production readiness is added. Human pilot acceptance and the broader R1 readiness gates remain outstanding.
