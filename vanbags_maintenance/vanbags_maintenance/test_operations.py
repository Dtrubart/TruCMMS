import frappe
from vanbags_maintenance import operations,configuration
from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase

class TestOperationalProbe(WorkOrderCase):
    def test_operator_diagnostics_require_administration(self):
        frappe.set_user(self.users['dispatcher'])
        with self.assertRaises(frappe.PermissionError):operations.health()
    def test_probe_does_not_claim_production_approval_or_write_domain_data(self):
        frappe.set_user('Administrator');before=frappe.db.count('TruCMMS Deployment');result=operations.health()
        self.assertTrue(result['checks']['database']);self.assertTrue(result['checks']['cache']);self.assertEqual(result['production_approval'],'Not evaluated by this probe');self.assertEqual(result['package_fingerprint'],configuration.package_fingerprint());self.assertEqual(frappe.db.count('TruCMMS Deployment'),before)

    def test_r1_matrix_has_24_unique_traceable_cases(self):
        import ast,json
        from pathlib import Path
        import vanbags_maintenance
        root=Path(vanbags_maintenance.__file__).parent;cases=json.loads((root/'release/r1_acceptance.json').read_text())['cases']
        self.assertEqual([c['id'] for c in cases],[f'CH02-R1-T{i:02d}' for i in range(1,25)])
        for case in cases:
            methods={node.name for node in ast.walk(ast.parse((root/case['file']).read_text())) if isinstance(node,ast.FunctionDef)};self.assertIn(case['test'],methods,case['id'])
