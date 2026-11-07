import json
import uuid
import frappe
from frappe.tests import IntegrationTestCase
from vanbags_maintenance import operating_units as u
from vanbags_maintenance.test_support import COMPANY_A, COMPANY_B, SITE_A, SITE_A2, SITE_B, grant_scope


class TestOperatingUnits(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        frappe.set_user('Administrator');frappe.db.savepoint('operating_unit_case')
        self.code = 'OU-'+uuid.uuid4().hex[:9].upper()
        self.root = self.unit('ROOT')
        self.child = self.unit('CHILD', self.root.name)
        self.other = self.unit('OTHER')
        self.foreign = self.unit('ROOT', company=COMPANY_B)
        self.reader = frappe.get_doc(dict(doctype='User', email=self.code.lower()+'@example.com',
            first_name='Organization test', send_welcome_email=0,
            roles=[dict(role='VB Maintenance Manager')])).insert().name
        grant_scope(self.reader)

    def tearDown(self):
        frappe.set_user('Administrator');frappe.db.rollback(save_point='operating_unit_case')
        super().tearDown()

    def unit(self, suffix, parent=None, company=COMPANY_A):
        return frappe.get_doc(dict(doctype=u.UNIT, company=company, unit_code=self.code+'-'+suffix,
            unit_name=self.code+' '+suffix, unit_type='Region' if not parent else 'District', parent_unit=parent)).insert()

    def assign(self, site, unit=None):
        preview = u.preview_site(site, unit)
        return u.assign_site(site, preview['token'], 'Reviewed administrative membership', unit)

    def change(self, unit, action, parent=None):
        preview = u.preview_unit(unit, action, parent)
        return u.change_unit(unit, action, preview['token'], 'Reviewed organization change', parent)

    def test_single_site_remains_valid_without_unit(self):
        site = frappe.get_doc(dict(doctype=u.SITE,company=COMPANY_A,site_code=self.code,
            site_name='Independent single site',acceptance_policy='By Origin')).insert()
        self.assertFalse(site.operating_unit)
        self.assertFalse(frappe.db.exists(u.EVENT,{'site':site.name}))

    def test_assignment_does_not_change_company_identity_grants_or_equipment(self):
        permissions = frappe.get_all('User Permission',fields=['*'],order_by='name',limit_page_length=0)
        equipment = frappe.get_all('VB Equipment',fields=['name','company','site','location','modified'],order_by='name',limit_page_length=0)
        original = frappe.get_doc(u.SITE,SITE_A)
        self.assign(SITE_A,self.child.name)
        current = frappe.get_doc(u.SITE,SITE_A)
        self.assertEqual((current.name,current.company),(original.name,original.company))
        self.assertEqual(permissions,frappe.get_all('User Permission',fields=['*'],order_by='name',limit_page_length=0))
        self.assertEqual(equipment,frappe.get_all('VB Equipment',fields=['name','company','site','location','modified'],order_by='name',limit_page_length=0))

    def test_reader_sees_only_authorized_ancestry_and_sites(self):
        self.assign(SITE_A,self.child.name);self.assign(SITE_A2,self.child.name)
        self.assign(SITE_B,self.foreign.name)
        frappe.set_user(self.reader)
        self.assertEqual(set(frappe.get_list(u.UNIT,pluck='name')),{self.root.name,self.child.name})
        self.assertEqual([row.name for row in u.details(self.child.name)['sites']],[SITE_A])
        self.assertEqual([r.name for r in u.children(COMPANY_A)['rows']],[self.root.name])
        with self.assertRaises(frappe.PermissionError): u.details(self.other.name)
        with self.assertRaises(frappe.PermissionError): u.details(self.foreign.name)
        with self.assertRaises(frappe.PermissionError): u.children(COMPANY_B)
        with self.assertRaises(frappe.PermissionError):frappe.get_list(u.EVENT,pluck='name')

    def test_native_site_permission_revocation_removes_unit_visibility(self):
        self.assign(SITE_A,self.child.name)
        frappe.set_user(self.reader);self.assertTrue(u.details(self.child.name))
        frappe.set_user('Administrator')
        for name in frappe.get_all('User Permission',filters={'user':self.reader,'allow':u.SITE},pluck='name'):
            frappe.delete_doc('User Permission',name)
        frappe.set_user(self.reader)
        self.assertEqual(frappe.get_list(u.UNIT,pluck='name'),[])
        with self.assertRaises(frappe.PermissionError): u.details(self.child.name)

    def test_link_title_cannot_disclose_hidden_operating_unit_names(self):
        self.assign(SITE_A,self.child.name)
        frappe.set_user(self.reader)
        self.assertEqual(u.link_title(u.UNIT,self.child.name),self.child.unit_name)
        with self.assertRaises(frappe.PermissionError):u.link_title(u.UNIT,self.other.name)
        with self.assertRaises(frappe.PermissionError):u.link_title(u.SITE,SITE_A2)
        self.assertEqual(u.link_title(u.SITE,SITE_A),frappe.db.get_value(u.SITE,SITE_A,'site_name'))
        self.assertEqual(u.link_title('Company',COMPANY_A),COMPANY_A)

    def test_membership_changes_have_old_and_new_paths(self):
        self.assign(SITE_A,self.child.name)
        changed = self.assign(SITE_A,self.other.name)
        event = frappe.get_doc(u.EVENT,changed['event'])
        self.assertEqual([x['name'] for x in json.loads(event.before_snapshot)['path']],[self.root.name,self.child.name])
        self.assertEqual([x['name'] for x in json.loads(event.after_snapshot)['path']],[self.other.name])
        self.assign(SITE_A)
        self.assertFalse(frappe.get_doc(u.SITE,SITE_A).operating_unit)

    def test_cross_company_membership_parent_and_identity_are_rejected(self):
        with self.assertRaises(frappe.ValidationError): u.preview_site(SITE_A,self.foreign.name)
        with self.assertRaises(frappe.ValidationError): u.preview_unit(self.child.name,'Reparent',self.foreign.name)
        self.child.company=COMPANY_B
        with self.assertRaises(frappe.ValidationError): self.child.save()
        self.child.reload();self.child.unit_code+='-CHANGED'
        with self.assertRaises(frappe.ValidationError): self.child.save()

    def test_same_code_allowed_in_different_companies_not_same_company(self):
        self.assertEqual(self.root.unit_code,self.foreign.unit_code)
        with self.assertRaises(frappe.ValidationError): self.unit('ROOT')

    def test_cycle_rejected_and_reparent_keeps_identity_and_site_link(self):
        self.assign(SITE_A,self.child.name)
        with self.assertRaises(frappe.ValidationError): u.preview_unit(self.root.name,'Reparent',self.child.name)
        self.change(self.child.name,'Reparent',self.other.name)
        self.assertEqual(frappe.get_doc(u.SITE,SITE_A).operating_unit,self.child.name)
        self.assertEqual([x['name'] for x in u.details(self.child.name)['path']],[self.other.name,self.child.name])

    def test_direct_mutations_cannot_bypass_controlled_actions(self):
        site=frappe.get_doc(u.SITE,SITE_A);site.operating_unit=self.child.name
        with self.assertRaises(frappe.ValidationError):site.save()
        self.child.parent_unit=self.other.name
        with self.assertRaises(frappe.ValidationError):self.child.save()
        self.child.reload();self.child.disabled=1
        with self.assertRaises(frappe.ValidationError):self.child.save()

    def test_stale_site_preview_is_rejected_after_unit_label_change(self):
        preview=u.preview_site(SITE_A,self.child.name)
        self.child.unit_name='Changed label';self.child.save()
        with self.assertRaises(frappe.ValidationError):u.assign_site(SITE_A,preview['token'],'Outdated preview',self.child.name)
        self.assertFalse(frappe.get_doc(u.SITE,SITE_A).operating_unit)

    def test_new_site_membership_invalidates_unit_impact_preview(self):
        preview=u.preview_unit(self.child.name,'Reparent',self.other.name)
        self.assertEqual(preview['affected_sites'],0)
        self.assign(SITE_A,self.child.name)
        with self.assertRaises(frappe.ValidationError):
            u.change_unit(self.child.name,'Reparent',preview['token'],'Outdated affected sites',self.other.name)
        self.assertEqual(self.child.reload().parent_unit,self.root.name)

    def test_pagination_returns_all_authorized_root_units_without_duplicates(self):
        for n in range(51):self.unit('PAGE-'+str(n))
        first=u.children(COMPANY_A,search=self.code+' PAGE-');second=u.children(COMPANY_A,search=self.code+' PAGE-',start=50)
        self.assertTrue(first['more']);self.assertFalse(second['more'])
        names=[row.name for row in first['rows']+second['rows']]
        self.assertEqual(len(names),51)
        self.assertEqual(len(set(names)),51)

    def test_disabled_units_and_disabled_ancestors_reject_new_use(self):
        self.change(self.child.name,'Deactivate')
        self.change(self.root.name,'Deactivate')
        with self.assertRaises(frappe.ValidationError):u.preview_site(SITE_A,self.child.name)
        with self.assertRaises(frappe.ValidationError):self.change(self.child.name,'Reactivate')
        with self.assertRaises(frappe.ValidationError):self.unit('BELOW',self.child.name)
        self.change(self.root.name,'Reactivate');self.change(self.child.name,'Reactivate')

    def test_deactivation_requires_detaching_sites_and_resolving_children(self):
        with self.assertRaises(frappe.ValidationError):u.preview_unit(self.root.name,'Deactivate')
        self.assign(SITE_A,self.child.name)
        with self.assertRaises(frappe.ValidationError):u.preview_unit(self.child.name,'Deactivate')
        self.assign(SITE_A)
        self.change(self.child.name,'Deactivate')

    def test_ordinary_manager_cannot_configure_even_with_site_write(self):
        frappe.set_user(self.reader)
        with self.assertRaises(frappe.PermissionError):self.unit('DENIED')
        with self.assertRaises(frappe.PermissionError):u.preview_site(SITE_A,self.child.name)
        with self.assertRaises(frappe.PermissionError):u.preview_unit(self.child.name,'Reparent',self.other.name)

    def test_events_and_unit_identity_cannot_be_deleted_or_shared(self):
        result=self.assign(SITE_A,self.child.name);event=frappe.get_doc(u.EVENT,result['event'])
        event.reason='Forged reason'
        with self.assertRaises(frappe.PermissionError):event.save(ignore_permissions=True)
        with self.assertRaises(frappe.PermissionError):event.delete(ignore_permissions=True)
        with self.assertRaises(frappe.ValidationError):self.other.delete(ignore_permissions=True)
        with self.assertRaises(frappe.ValidationError):frappe.rename_doc(u.UNIT,self.other.name,self.code+'-RENAMED',force=True)
        with self.assertRaises(frappe.ValidationError):frappe.rename_doc(u.EVENT,event.name,self.code+'-EVENT',force=True)
        with self.assertRaises(frappe.PermissionError):frappe.share.add(u.UNIT,self.child.name,user=self.reader,notify=0)

    def test_site_creation_can_optionally_link_and_audit_membership(self):
        site=frappe.get_doc(dict(doctype=u.SITE,company=COMPANY_A,site_code=self.code,
            site_name='Grouped site',operating_unit=self.child.name,acceptance_policy='By Origin')).insert()
        self.assertTrue(frappe.db.exists(u.EVENT,{'site':site.name,'action':'Site linked'}))
        self.assertEqual(site.company,COMPANY_A)

    def test_literal_search_and_pagination_limit(self):
        self.assertEqual(u.children(COMPANY_A,search=self.code+' ROOT%')['rows'],[])
        self.assertEqual(u.children(COMPANY_A)['limit'],50)
        with self.assertRaises(frappe.ValidationError):u.children(COMPANY_A,start=-1)

    def test_depth_limit_rejects_new_descendant_and_too_deep_move(self):
        parent=self.root.name
        for n in range(63):
            name=self.code+'-DEPTH-'+str(n)
            frappe.db.sql(f'''INSERT INTO `tab{u.UNIT}` (name,company,unit_code,unit_name,parent_unit,disabled)
                VALUES (%s,%s,%s,%s,%s,0)''',(name,COMPANY_A,name,name,parent))
            parent=name
        with self.assertRaises(frappe.ValidationError):self.unit('TOO-DEEP',parent)
        with self.assertRaises(frappe.ValidationError):u.preview_unit(self.other.name,'Reparent',parent)
