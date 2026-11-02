# R1 candidate and task-oriented navigation

TruCMMS remains a Frappe app installed alongside ERPNext. Existing document identities, data and access rules are retained.

## Navigation

The approved full-scope structure is Inicio, Operación, Activos, Planes y rutinas, Recursos y servicios, Repuestos y costos, Análisis and Configuración. Only implemented, useful and permitted entries appear for a role. Plans and materials/cost transactions remain future deliveries; empty placeholder modules are hidden.

The existing `/desk/trucmms` URL opens the role-aware Home at `/desk/trucmms-start`. The native Workspace Sidebar uses collapsible categories. Home exposes scoped quick actions and counts. My Work opens its actual view, including when the Work Views page is already loaded. Team membership and site coverage are accessed inside a maintenance team; work execution, allocations, events, cycles and corrections remain contextual to their work order. Custom navigation shortcuts are preserved under additional accesses. Native Frappe routing and forms remain in use; no Frappe core files are changed.

Navigation visibility is not authorization. Server-side Company/Site, team eligibility, assignment/cycle and evidence checks still apply to direct URL/API access. Menus and Home are rebuilt for the authenticated actor without accepting another user identity or sharing another actor's navigation payload. Labels are in Spanish as approved; existing form language is retained.

## Technical release gates

`vanbags_maintenance/release/r1_acceptance.json` maps all 24 proposed CH02-R1-T01–24 scenarios to test methods. The suite verifies this traceability and functional behavior. Additional evidence covers clean installation, populated upgrade, roles/API/private files, concurrent operations, the four work views, 390px execution/evidence/retry behavior, grouped navigation, read-only load and full candidate restoration.

Use `bench --site SITE execute vanbags_maintenance.operations.health` for the administrative read-only service/queue/deployment/timezone/disk probe. This probe does not grant human or production approval. The Docker bench is still a development environment.

## Outstanding approval and production scope

Human pilot sign-off must identify the reviewed revision, roles/scenarios, findings and dispositions. Automated tests are not a substitute for that sign-off. Production requires its own target architecture, TLS/network boundaries, secret custody, backup retention/offsite recovery objectives, monitoring/alerts and representative capacity evidence. No production deployment, external notifications or recurring automation is enabled by this candidate.

Automatic PM/meters, transactional stock/purchasing/cost integration, specialized calibration and advanced reliability remain separate approved-roadmap deliveries. Direct authorized work without a requester does not imply that a PM generation engine exists.
