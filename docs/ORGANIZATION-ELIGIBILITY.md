# Maintenance organization and eligibility — A/B-1

TruCMMS reuses ERPNext Company/User. Its teams are independent from native Asset Maintenance Team because service-site authorization, technical disciplines and effective membership require a different permission contract.

Teams have a stable company, management site and Internal/External type. System Manager maintains the global discipline catalog. Supervisors administer teams only when authorized for the management site and every non-revoked service-site grant. Dispatcher/technician access remains read-only and scoped; membership never grants work-order visibility.

Membership applies to a user and discipline. Site authorization applies to a team and site of the same company. Intervals include their start and exclude their end. Revocations are audited and cannot be reversed; create another interval. Equivalent intervals cannot overlap. Concurrent edits may return an explicit conflict requiring a fresh retry.

New orders use Managed eligibility. Before assignment and technician actions, the server checks enabled users/roles, native Company/Site permissions, team/discipline, membership and site eligibility. Every managed assignment creates immutable history. Existing orders migrate to Legacy without inventing missing team data. Supervisors can explicitly adopt open Legacy orders with a reason; prior history is retained.

TruCMMS Site stores an IANA operating timezone. Existing ERPNext timestamps and interval forms remain in the system timezone; operating views must explicitly convert them. Changing a system clock containing maintenance records requires a separate timestamp migration. No automatic timestamp shifts are performed. Future scheduling fields and four-view UI are outside this increment.

Organization and audit records do not accept attachments; maintenance evidence belongs to work records. Import/export/share remain restricted for operational roles. Procurement, contract costs, multiple assignments, PM generation and new completion states are outside A/B.

Deployment records preserve the normalized package SHA-256, site, framework version, policy and schema migration result. A migration record is not user acceptance or production readiness.
