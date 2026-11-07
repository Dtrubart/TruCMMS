"""Temporary TEST-only UI fixture; never assign existing business sites."""
import json
import os
from pathlib import Path
import secrets
import sys
import uuid
import frappe

MANIFEST = Path(os.environ['TRUCMMS_ORG_FIXTURE_FILE'])


def main():
    os.chdir(os.environ.get('TRUCMMS_SITES_DIR','.'))
    test_site=os.environ.get('TRUCMMS_TEST_SITE','test.vanbags.localhost')
    assert test_site in ('test.vanbags.localhost','test_site'), 'Only explicitly named TEST sites are supported.'
    frappe.init(site=test_site,sites_path='.');frappe.connect();frappe.set_user('Administrator')
    from vanbags_maintenance import operating_units as u
    from vanbags_maintenance.test_support import COMPANY_A,grant_scope
    try:
        assert frappe.conf.allow_tests
        if sys.argv[1]=='seed':
            assert not MANIFEST.exists(), 'Preserve an existing fixture until it is cleaned.'
            code='ENT3-UI-'+uuid.uuid4().hex[:10].upper()
            units=[]
            for suffix,label,parent in [('ROOT','ENT003 UI Region',None),('A','ENT003 UI District A',0),('B','ENT003 UI Hidden District B',0)]:
                units.append(frappe.get_doc(dict(doctype=u.UNIT,company=COMPANY_A,unit_code=code+'-'+suffix,
                    unit_name=label,parent_unit=units[parent].name if parent is not None else None)).insert())
            sites=[]
            for suffix,unit in [('A',units[1]),('B',units[2])]:
                sites.append(frappe.get_doc(dict(doctype=u.SITE,company=COMPANY_A,site_code=code+'-'+suffix,
                    site_name='ENT003 UI Site '+suffix,operating_unit=unit.name,acceptance_policy='By Origin')).insert())
            password=secrets.token_urlsafe(30)
            user=frappe.get_doc(dict(doctype='User',email=code.lower()+'@example.com',first_name='Organization UI',
                send_welcome_email=0,new_password=password,roles=[dict(role='VB Maintenance Manager')])).insert()
            grant_scope(user.name,company=COMPANY_A,site=sites[0].name)
            data=dict(prefix=code,company=COMPANY_A,units=[x.name for x in units],sites=[x.name for x in sites],
                reader=user.name,password=password)
            frappe.db.commit();MANIFEST.write_text(json.dumps(data));MANIFEST.chmod(0o600)
            print('Synthetic UI fixture created on TEST; credentials retained privately.')
        elif sys.argv[1]=='clean':
            data=json.loads(MANIFEST.read_text());assert data['prefix'].startswith('ENT3-UI-')
            assert all(x.startswith(data['prefix']) for x in data['sites'])
            for name in data['sites']:
                frappe.db.delete(u.EVENT,{'site':name,'company':data['company']})
                frappe.db.delete('Version',{'ref_doctype':u.SITE,'docname':name})
                frappe.db.delete(u.SITE,{'name':name,'company':data['company']})
            for name in data['units']:
                frappe.db.delete(u.EVENT,{'operating_unit':name,'company':data['company']})
                frappe.db.delete('Version',{'ref_doctype':u.UNIT,'docname':name})
                frappe.db.delete(u.UNIT,{'name':name,'company':data['company'],'unit_code':['like',data['prefix']+'%']})
            frappe.delete_doc('User',data['reader'],ignore_permissions=True,force=True)
            frappe.db.commit();MANIFEST.unlink()
            print('Exact synthetic UI identities removed from TEST.')
        else:raise ValueError('Choose seed or clean.')
    finally:frappe.destroy()


if __name__=='__main__':main()
