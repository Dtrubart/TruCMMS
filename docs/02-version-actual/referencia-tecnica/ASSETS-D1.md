# TruCMMS D1 — asset identity and placement

TruCMMS remains a native Frappe app installed alongside ERPNext. Company remains ERPNext's organizational master. This increment does not replace the financial Asset, inventory, purchasing or accounting ledgers.

## Identity and configuration

Existing VB Equipment document names and Equipment Codes remain permanent, globally unique identifiers. They are never renamed or repurposed when equipment moves or is replaced. The optional Asset Tag is a mutable operational label, normalized to uppercase with collapsed spaces and unique within Company. Serial numbers remain descriptive, without introducing a new uniqueness assumption for existing records.

System Managers maintain global reusable Equipment Profiles and Criticality definitions. Profile codes and positive versions identify immutable schemas; a new definition requires a new code/version. Supported attribute types are Text, Integer, Decimal, Date, Boolean (0/1) and Choice. Definitions specify units, required values and numeric bounds. Equipment retains a schema snapshot and canonical typed values. Criticality is explicit and snapshotted; rank does not automatically change priority, response targets or safety rules. Disabled configuration remains interpretable but cannot be newly assigned.

Equipment managers use Configure Asset with a reason and the complete intended tag/profile/values/criticality configuration. Omitted configuration is cleared deliberately by this API. Native dialogs preserve existing choices and collect profile values before saving. Unrelated equipment fields retain existing native change tracking. New requests/orders snapshot their equipment context; migration does not invent historical snapshots for existing work.

## Effective placement

New equipment receives an Initial declared placement at actual creation time, including mobile equipment with Site custody and no fixed location. Existing equipment is marked Legacy without altering Company, Site or location; Declare Placement Baseline records the currently observed placement at the time of adoption with the operator's reason. Neither initial nor declared baselines assert an earlier physical installation date.

Place / Transfer and Remove Equipment append effective relationships with start-inclusive/end-exclusive intervals. Native forms record current movements; API effective_on uses system-time Datetime and cannot be future dated or precede the latest placement/removal. Backdating across existing request/work-order activity is rejected. Removal retains the equipment's administrative Site and closes the active placement; a blank location alone does not establish whether there is an active mobile custody interval. Use the Installation Register.

A functional location may contain multiple equipment records or be configured as a single-equipment position through a reasoned action. Existing occupancy, including Legacy equipment, must be reconciled before exclusivity is enabled. Capacity is serialized per Company. Replacement atomically removes one equipment and installs a different managed, uninstalled equipment at the same Company/Site position, preserving separate identities and histories. Failed operations roll back all intervals, events and current-location changes.

Open work orders block removal/relocation/replacement. New work validates the equipment's current Company/Site while holding its record lock. A closed order cannot reopen under its previous Site after the equipment transfers elsewhere. Moving equipment does not rewrite old requests, orders, executions or attachments. Retired equipment cannot receive a new placement or act as a replacement.

## Permissions and audit

Asset management requires VB Maintenance Manager or privileged administration plus native Company and Site scope. Transfers require both source and target authorization. Installation history is filtered by its historical Company/Site. Movement events containing two sites require authorization to both; sharing cannot expand this scope. History is server-authored, immutable through generic CRUD, and does not accept attachments. Configuration catalogs are globally readable by maintenance roles and writable only by System Manager. Asset events snapshot supported domain fields, excluding arbitrary custom fields.

TruCMMS Equipment History includes placement and asset events. TruCMMS Installation Register supports Company/Site/equipment/location, active intervals and effective occupancy as-of a Datetime. Effective dates follow the established system storage/user display timezone contract. Unknown pre-adoption history remains unknown.

## Boundaries

D1 does not implement automatic preventive plans, meters, component bills, asset ownership across companies, financial Asset synchronization, stock/costing transactions, automatic SLA generation, advanced scheduling, offline/mobile certification or production readiness. Labels remain configurable without changing the server's security/workflow invariants. Company serialization favors correctness; high-volume movement throughput remains part of performance validation.
