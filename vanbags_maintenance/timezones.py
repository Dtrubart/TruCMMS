"""Versioned official IANA rules shared by TruCMMS views and native Desk controls."""
from functools import lru_cache
from importlib.resources import files
from datetime import datetime,timezone
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
import tzdata
import frappe
RULES_VERSION='2026e'

@lru_cache(maxsize=128)
def zone(name):
    if tzdata.IANA_VERSION!=RULES_VERSION:frappe.throw('Install the supported timezone-data dependency before using maintenance date views.')
    if not isinstance(name,str) or not name or any(part in ('','..','.') for part in name.split('/')):raise ZoneInfoNotFoundError(name)
    try:
        with files('tzdata.zoneinfo').joinpath(*name.split('/')).open('rb') as data:return ZoneInfo.from_file(data,key=name)
    except (FileNotFoundError,IsADirectoryError):raise ZoneInfoNotFoundError(name)

def assert_storage_clock():
    name=frappe.db.get_single_value('System Settings','time_zone') or 'UTC';now=datetime.now(timezone.utc)
    if now.astimezone(ZoneInfo(name)).utcoffset()!=now.astimezone(zone(name)).utcoffset():
        frappe.throw('The platform system timezone database differs from current maintenance rules. Update the platform timezone data before recording work; do not shift existing timestamps.')
