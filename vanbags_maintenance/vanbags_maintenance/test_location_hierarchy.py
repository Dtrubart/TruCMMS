import json
import uuid

import frappe
from frappe.tests import IntegrationTestCase
from vanbags_maintenance import location_hierarchy as h
from vanbags_maintenance.test_support import COMPANY_A, SITE_A, SITE_A2, org_context, grant_scope


class TestLocationHierarchy(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        frappe.set_user('Administrator')
        frappe.db.savepoint('location_hierarchy_case')
        self.prefix = 'LH-' + uuid.uuid4().hex[:10]
        self.root = self.location('Root')
        self.child = self.location('Child', self.root.name)
        self.other = self.location('Other')
        self.foreign = self.location('Foreign', site=SITE_A2)
        self.user = frappe.get_doc(dict(doctype='User', email=self.prefix.lower()+'@example.com',
            first_name='Hierarchy test', send_welcome_email=0,
            roles=[dict(role='VB Maintenance Manager')])).insert().name
        grant_scope(self.user)

    def tearDown(self):
        frappe.set_user('Administrator')
        frappe.db.rollback(save_point='location_hierarchy_case')
        super().tearDown()

    def location(self, suffix, parent=None, site=SITE_A):
        return frappe.get_doc(dict(doctype=h.LOCATION, company=COMPANY_A, site=site,
            location_name=self.prefix+suffix, parent_location=parent)).insert()

    def change(self, name, action, parent=None):
        preview = h.preview(name, action, parent)
        return h.change(name, action, preview['token'], 'Approved hierarchy adjustment', parent)

    def test_tree_search_and_direct_read_are_scoped(self):
        frappe.set_user(self.user)
        rows = h.children(SITE_A, search=self.prefix)['rows']
        self.assertEqual({r.name for r in rows}, {self.root.name, self.child.name, self.other.name})
        self.assertEqual([r.name for r in h.children(SITE_A, self.root.name)['rows']], [self.child.name])
        with self.assertRaises(frappe.PermissionError): h.children(SITE_A2)
        with self.assertRaises(frappe.PermissionError): h.details(self.foreign.name)
        with self.assertRaises(frappe.PermissionError): h.children(SITE_A, parent=self.foreign.name)

    def test_reparent_keeps_identity_and_records_immutable_paths(self):
        frappe.set_user(self.user)
        result = self.change(self.child.name, 'Reparent', self.other.name)
        doc = h.details(self.child.name)
        self.assertEqual(doc['name'], self.child.name)
        self.assertEqual([x['name'] for x in doc['path']], [self.other.name, self.child.name])
        event = frappe.get_doc(h.EVENT, result['event'])
        self.assertEqual(json.loads(event.before_snapshot)['path'], [self.root.name, self.child.name])
        event.reason = 'Forged history'
        with self.assertRaises(frappe.PermissionError): event.save(ignore_permissions=True)
        with self.assertRaises(frappe.PermissionError): event.delete(ignore_permissions=True)

    def test_direct_edit_cannot_bypass_controlled_change(self):
        self.child.parent_location = self.other.name
        with self.assertRaises(frappe.ValidationError): self.child.save()
        self.child.reload(); self.child.disabled = 1
        with self.assertRaises(frappe.ValidationError): self.child.save()

    def test_cycles_and_cross_site_moves_rejected(self):
        with self.assertRaises(frappe.ValidationError): h.preview(self.root.name, 'Reparent', self.child.name)
        with self.assertRaises(frappe.ValidationError): h.preview(self.child.name, 'Reparent', self.foreign.name)

    def test_changed_subtree_invalidates_preview(self):
        before = h.preview(self.root.name, 'Reparent', self.other.name)
        self.location('NewChild', self.root.name)
        with self.assertRaises(frappe.ValidationError):
            h.change(self.root.name, 'Reparent', before['token'], 'Stale adjustment', self.other.name)
        self.assertIsNone(self.root.reload().parent_location)

    def test_revocation_blocks_preview_confirmation_and_history(self):
        frappe.set_user(self.user)
        before = h.preview(self.child.name, 'Reparent', self.other.name)
        frappe.set_user('Administrator')
        for name in frappe.get_all('User Permission', filters={'user': self.user}, pluck='name'):
            frappe.delete_doc('User Permission', name)
        frappe.set_user(self.user)
        with self.assertRaises(frappe.PermissionError):
            h.change(self.child.name, 'Reparent', before['token'], 'Revoked scope', self.other.name)
        self.assertEqual(frappe.get_list(h.EVENT, pluck='name'), [])

    def test_deactivation_is_bottom_up_and_reactivation_top_down(self):
        with self.assertRaises(frappe.ValidationError): h.preview(self.root.name, 'Deactivate')
        self.change(self.child.name, 'Deactivate')
        self.change(self.root.name, 'Deactivate')
        with self.assertRaises(frappe.ValidationError): h.preview(self.child.name, 'Reactivate')
        self.change(self.root.name, 'Reactivate')
        self.change(self.child.name, 'Reactivate')
        self.assertEqual(self.child.reload().disabled, 0)

    def test_new_location_rejects_disabled_legacy_ancestor(self):
        # Simulate a pre-policy hierarchy; preserve its readability, not new use.
        frappe.db.set_value(h.LOCATION, self.root.name, 'disabled', 1)
        with self.assertRaises(frappe.ValidationError): self.location('BelowInactivePath', self.child.name)
        self.assertTrue(h.details(self.child.name)['path'])

    def test_label_change_keeps_identity_and_events(self):
        name = self.child.name
        self.child.location_name += ' renamed'; self.child.save()
        self.assertEqual(self.child.name, name)
        self.assertTrue(frappe.db.exists(h.EVENT, {'location': name, 'action': 'Label changed'}))
        with self.assertRaises(frappe.ValidationError): self.child.delete(ignore_permissions=True)

    def test_event_direct_read_and_share_preserve_scope(self):
        event = frappe.get_doc(h.EVENT, {'location': self.child.name, 'action': 'Created'})
        frappe.set_user(self.user)
        event.check_permission('read')
        foreign = frappe.get_doc(h.EVENT, {'location': self.foreign.name, 'action': 'Created'})
        with self.assertRaises(frappe.PermissionError): foreign.check_permission('read')
        frappe.set_user('Administrator')
        with self.assertRaises(frappe.PermissionError): frappe.share.add(h.EVENT, event.name, user=self.user, notify=0)

    def test_search_is_literal_and_pages_are_bounded(self):
        self.assertEqual(h.children(SITE_A, search=self.prefix+'%')['rows'], [])
        self.assertEqual(h.children(SITE_A, search=self.prefix+"' OR 1=1 --")['rows'], [])
        with self.assertRaises(frappe.ValidationError): h.children(SITE_A, start=-1)
        self.assertEqual(h.children(SITE_A)['limit'], 50)

    def test_pagination_has_no_missing_or_duplicate_children(self):
        for n in range(55):
            self.location('Page'+str(n), self.root.name)
        first = h.children(SITE_A, parent=self.root.name)
        second = h.children(SITE_A, parent=self.root.name, start=50)
        self.assertTrue(first['more']); self.assertFalse(second['more'])
        names = [r.name for r in first['rows'] + second['rows']]
        self.assertEqual(len(names), 56)
        self.assertEqual(len(set(names)), 56)

    def test_deactivation_rejects_installed_equipment_and_active_points(self):
        category = frappe.get_doc(dict(doctype='VB Equipment Category', category_name=self.prefix)).insert()
        frappe.get_doc(dict(doctype='VB Equipment', **org_context(), category=category.name,
            equipment_code=self.prefix, equipment_name='Installed fixture', location=self.other.name)).insert()
        with self.assertRaises(frappe.ValidationError): h.preview(self.other.name, 'Deactivate')
        frappe.get_doc(dict(doctype='TruCMMS Measurement Point', **org_context(),
            code=self.prefix, point_name='Utility inlet', functional_location=self.child.name)).insert()
        with self.assertRaises(frappe.ValidationError): h.preview(self.child.name, 'Deactivate')

    def test_open_work_blocks_deactivation_and_reparent_preserves_order(self):
        from vanbags_maintenance import work_contract, work_scope
        order = frappe.get_doc(work_contract.create_direct(COMPANY_A, SITE_A, 'Hierarchy fixture',
            'Inspect room', 'Medium', uuid.uuid4().hex, 'Isolated history check', functional_location=self.child.name))
        work_scope.configure(order.name, self.child.name,
            [dict(kind='Location', functional_location=self.child.name)], 'Initial scope snapshot', uuid.uuid4().hex)
        from frappe.model.workflow import apply_workflow
        apply_workflow(order.reload(), 'Authorize')
        order.reload()
        self.assertTrue(order.scope_snapshot)
        before = {key: order.get(key) for key in ('name', 'modified', 'scope_snapshot', 'scope_revision', 'functional_location')}
        with self.assertRaises(frappe.ValidationError): h.preview(self.child.name, 'Deactivate')
        self.change(self.child.name, 'Reparent', self.other.name)
        order.reload()
        self.assertEqual(before, {key: order.get(key) for key in before})

    def test_depth_guard_includes_moved_descendants(self):
        # Synthetic legacy chain isolates the boundary without creating 64 event fixtures.
        parent = self.root.name
        for n in range(63):
            name = self.prefix + 'Depth' + str(n)
            frappe.db.sql(f'''INSERT INTO `tab{h.LOCATION}` (name,company,site,location_name,parent_location,disabled)
                VALUES (%s,%s,%s,%s,%s,0)''', (name, COMPANY_A, SITE_A, name, parent))
            parent = name
        with self.assertRaises(frappe.ValidationError): self.location('TooDeep', parent)
        with self.assertRaises(frappe.ValidationError): h.preview(self.other.name, 'Reparent', parent)

    def test_read_only_role_cannot_change_or_forge_events(self):
        user = frappe.get_doc('User', self.user)
        user.roles = []; user.append('roles', {'role': 'VB Maintenance User'}); user.save()
        frappe.set_user(self.user)
        self.assertTrue(h.details(self.child.name)['path'])
        with self.assertRaises(frappe.PermissionError): h.preview(self.child.name, 'Reparent', self.other.name)
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc(dict(doctype=h.EVENT, location=self.child.name, company=COMPANY_A,
                site=SITE_A, action='Reparent', reason='Forged event', effective_on=frappe.utils.now_datetime(),
                recorded_by=self.user, before_snapshot='{}', after_snapshot='{}')).insert(ignore_permissions=True)
