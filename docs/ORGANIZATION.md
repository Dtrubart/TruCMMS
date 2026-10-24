# TruCMMS company and site context

Equipment and functional locations require an ERPNext Company and a TruCMMS Site. Each Site belongs to one Company. A location may have a parent in the same Company and Site; cycles are rejected. Existing VB identifiers and equipment names remain stable.

ERPNext Company is reused. ERPNext Location was evaluated: its tree has no Company/Site ownership, includes accounting/stock role grants and uses a parent link that ignores user permissions. This increment therefore extends the existing maintenance-location master rather than maintaining a second maintenance-location source of truth. No core files are changed.

System Manager creates Sites from **TruCMMS → Sites**. Maintenance managers maintain equipment and functional locations within their assigned scope. Categories remain a shared role-controlled taxonomy. Actual site names and company assignments are business configuration; installation does not seed a VanBags site.

For each maintenance user, an administrator creates native **User Permission** records for both **Company** and **TruCMMS Site**, normally with **Apply To All Document Types** enabled. Grant every authorized company and site explicitly. Having a maintenance role, only a company permission, or only a site permission grants no access to scoped records. Company links have select-only permission for the maintenance roles; this does not grant administration of Companies.

Server permission hooks and query conditions enforce the intersection of both scopes for direct reads, lists, API writes and Link searches. Sharing cannot grant organizational scope, and revoking scope also denies previously shared records. Document validation checks that Company, Site and Functional Location agree. Site creation and organizational assignment remain administrative operations.

Company cannot be changed on a previously assigned master. Equipment may move between authorized Sites within the same Company, keeping its identity and recording the change in Version history. Clear or replace its Functional Location to match the destination. A functional location retains its Site; use a new functional position for a different site. Cross-company transfer needs a separate controlled process.

Disabling a Site blocks new assignments but preserves existing history and unrelated edits. The inherited globally unique location labels and equipment codes remain unchanged. The parent relationship supports functional hierarchy through native Link fields; a graphical tree editor is not part of this increment.

On upgrade, new fields do not rename or delete existing records. Legacy records without Company/Site remain available only to administrators until explicitly assigned; there is no guessed company or site backfill. DEV and TEST had no existing equipment or location records at the pre-change audit. Test fixtures create clearly named test Companies/Sites only when the test runner executes.

Test suite: 61 integration tests, including cross-company, same-company cross-site, unassigned users, context consistency, stable company identity, moves, hierarchy cycles, site disablement and share/revocation boundaries. Browser/HTTP verification additionally exercises native form creation and Link search.
