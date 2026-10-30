"""Operating timezone contract and reproducible per-site deployment evidence."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfoNotFoundError
from vanbags_maintenance.timezones import zone as ZoneInfo
import frappe
from frappe.utils import get_datetime
POLICY_VERSION = 'R3-standard-handoff'

def validate_zone(value):
    try:ZoneInfo(value)
    except (ZoneInfoNotFoundError,ValueError,TypeError):frappe.throw('Choose a valid IANA timezone, such as America/Vancouver.')
    return value

def site_time(value,site):
    source=frappe.db.get_single_value('System Settings','time_zone') or 'UTC'
    target=frappe.db.get_value('TruCMMS Site',site,'time_zone')
    if not target:frappe.throw('Configure the operating site timezone.')
    stamp=get_datetime(value)
    if stamp.tzinfo is None:stamp=stamp.replace(tzinfo=ZoneInfo(source))
    return stamp.astimezone(ZoneInfo(target)).isoformat()

def local_instant(value,site,fold=None):
    # Explicitly reject DST gaps and ambiguous wall times unless a fold is chosen.
    zone=ZoneInfo(frappe.db.get_value('TruCMMS Site',site,'time_zone'))
    wall=get_datetime(value).replace(tzinfo=None);candidates=[]
    for choice in (0,1):
        aware=wall.replace(tzinfo=zone,fold=choice)
        if aware.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)==wall:candidates.append(aware)
    if not candidates:frappe.throw('This local time does not exist because of daylight saving time.')
    if len({x.utcoffset() for x in candidates})>1 and fold is None:frappe.throw('Choose the first or second occurrence of this ambiguous local time.')
    if fold not in (None,0,1):frappe.throw('Invalid daylight saving occurrence.')
    selected=next((x for x in candidates if x.fold==(fold or 0)),candidates[0])
    return selected.astimezone(timezone.utc).isoformat()

def guard_system_timezone(doc,method=None):
    old=doc.get_doc_before_save()
    if old and old.time_zone!=doc.time_zone:
        if frappe.db.count('TruCMMS Equipment Installation') or frappe.db.count('TruCMMS Maintenance Work Order') or frappe.db.count('TruCMMS Team Membership') or frappe.db.count('TruCMMS Team Site Authorization'):
            frappe.throw('A versioned timestamp migration is required before changing the system timezone. Configure the operating timezone on TruCMMS Site instead.')

def setup(record=True):
    from vanbags_maintenance.lifecycle import setup as previous
    previous()
    # Existing records are legacy only once. Clients cannot request this policy.
    frappe.db.sql("UPDATE `tabTruCMMS Maintenance Work Order` SET team_policy='Legacy' WHERE COALESCE(team_policy,'')=''")
    for dt,fields,index in [('TruCMMS Team Membership',['team','user','discipline','valid_from'],'team_member_interval'),('TruCMMS Team Site Authorization',['team','site','valid_from'],'team_site_interval'),('TruCMMS Team Assignment',['work_order','assigned_on'],'work_team_history')]:
        frappe.db.add_index(dt,fields,index)
    default=frappe.db.get_single_value('System Settings','time_zone') or 'UTC'
    frappe.db.sql("UPDATE `tabTruCMMS Site` SET time_zone=%s WHERE COALESCE(time_zone,'')=''",(default,))
    if record:record_deployment()


def record_deployment():
    default=frappe.db.get_single_value('System Settings','time_zone') or 'UTC'
    fingerprint=package_fingerprint()
    if not frappe.db.exists('TruCMMS Deployment',{'package_fingerprint':fingerprint,'site_name':frappe.local.site}):
        previous_flag=frappe.flags.get('trucmms_deployment_insert');frappe.flags.trucmms_deployment_insert=True
        try:
            frappe.get_doc({'doctype':'TruCMMS Deployment','package_fingerprint':fingerprint,'site_name':frappe.local.site,'framework_version':frappe.__version__,'policy_version':POLICY_VERSION,'migration_result':'Completed','storage_timezone':default,'deployed_on':frappe.utils.now_datetime()}).insert(ignore_permissions=True)
        finally:frappe.flags.trucmms_deployment_insert=previous_flag


@frappe.whitelist()
def operating_clock(site,value=None):
    doc=frappe.get_doc('TruCMMS Site',site);doc.check_permission('read')
    return {'system_timezone':frappe.db.get_single_value('System Settings','time_zone') or 'UTC','operating_timezone':doc.time_zone,'operating_time':site_time(value or frappe.utils.now_datetime(),site)}


def package_fingerprint():
    folder=Path(__file__).parent;digest=hashlib.sha256()
    for p in sorted(folder.rglob('*')):
        if p.is_file() and p.suffix in ('.py','.js','.json') and '__pycache__' not in p.parts:
            digest.update(str(p.relative_to(folder)).encode());digest.update(p.read_text().replace('\r\n','\n').encode())
    return digest.hexdigest()
