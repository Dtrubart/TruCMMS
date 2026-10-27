"""Read-only operator checks. Production approval is deliberately outside this probe."""
from datetime import datetime,timezone
import shutil
import frappe
from vanbags_maintenance import organization as org,configuration
from vanbags_maintenance.timezones import assert_storage_clock,RULES_VERSION

def health():
    if not org.privileged():frappe.throw('System Manager required for operational diagnostics.',frappe.PermissionError)
    from frappe.utils.background_jobs import get_workers,get_queue
    from frappe.utils.scheduler import is_scheduler_inactive
    fingerprint=configuration.package_fingerprint();checks={}
    checks['database']=frappe.db.sql('SELECT 1')[0][0]==1
    checks['cache']=bool(frappe.cache.ping())
    queue_checks={}
    for name in ('short','default','long'):
        queue=get_queue(name);workers=get_workers(queue);fresh=[]
        for worker in workers:
            heartbeat=worker.last_heartbeat
            if heartbeat:
                if heartbeat.tzinfo is None:heartbeat=heartbeat.replace(tzinfo=timezone.utc)
                if (datetime.now(timezone.utc)-heartbeat).total_seconds()<180:fresh.append(worker)
        queue_checks[name]={'fresh_workers':len(fresh),'pending_jobs':queue.count}
    checks['workers']=all(x['fresh_workers'] for x in queue_checks.values())
    checks['scheduler_enabled']=not is_scheduler_inactive(verbose=False)
    checks['deployed_package']=bool(frappe.db.exists('TruCMMS Deployment',{'site_name':frappe.local.site,'package_fingerprint':fingerprint,'policy_version':configuration.POLICY_VERSION,'migration_result':'Completed'}))
    try:assert_storage_clock();checks['storage_clock']=True
    except frappe.ValidationError:checks['storage_clock']=False
    disk=shutil.disk_usage(frappe.get_site_path());checks['disk_free']=disk.free>2*1024**3
    return {'site':frappe.local.site,'package_fingerprint':fingerprint,'policy':configuration.POLICY_VERSION,'timezone_rules':RULES_VERSION,'checks':checks,'queues':queue_checks,'disk_free_gib':round(disk.free/1024**3,2),'developer_mode':bool(frappe.conf.developer_mode),'maintenance_mode':bool(frappe.conf.maintenance_mode),'technical_health':all(checks.values()),'production_approval':'Not evaluated by this probe','human_pilot_acceptance':'External sign-off required'}
