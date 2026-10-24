import uuid
import frappe
from frappe.tests import IntegrationTestCase
from vanbags_maintenance.test_support import COMPANY_A, COMPANY_B, SITE_A, SITE_A2, SITE_B, org_context, grant_scope


class TestOrganization(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        frappe.db.savepoint("organization_case")
        frappe.set_user("Administrator")
        self.token="ORG-"+uuid.uuid4().hex[:10].upper()
        self.category=frappe.get_doc({"doctype":"VB Equipment Category","category_name":self.token}).insert()
        self.locations=[]
        self.equipment=[]
        for index,(company,site) in enumerate([(COMPANY_A,SITE_A),(COMPANY_A,SITE_A2),(COMPANY_B,SITE_B)]):
            location=frappe.get_doc({"doctype":"VB Equipment Location","location_name":self.token+str(index),"company":company,"site":site}).insert()
            self.locations.append(location)
            self.equipment.append(frappe.get_doc({"doctype":"VB Equipment","equipment_code":self.token+str(index),"equipment_name":"Scope verification","category":self.category.name,"location":location.name,"company":company,"site":site}).insert())
        self.user=frappe.get_doc({"doctype":"User","email":self.token.lower()+"@example.com","first_name":"Organization test","send_welcome_email":0,"roles":[{"role":"VB Maintenance Manager"}]}).insert().name

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback(save_point="organization_case")
        frappe.clear_document_cache("TruCMMS Site", SITE_A)
        super().tearDown()

    def test_no_scope_denies_list_read_and_create(self):
        frappe.set_user(self.user)
        self.assertEqual(frappe.get_list("VB Equipment",pluck="name"),[])
        with self.assertRaises(frappe.PermissionError):
            self.equipment[0].check_permission("read")
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc({"doctype":"VB Equipment",**org_context(),"equipment_code":self.token+"NEW","equipment_name":"Denied","category":self.category.name}).insert()

    def test_company_and_site_scope_filters_lists_and_direct_reads(self):
        grant_scope(self.user)
        frappe.set_user(self.user)
        names=frappe.get_list("VB Equipment",filters={"name":["like",self.token+"%"]},pluck="name")
        self.assertEqual(names,[self.equipment[0].name])
        self.equipment[0].check_permission("read")
        self.equipment[0].equipment_name="Authorized change"
        self.equipment[0].save()
        for doc in self.equipment[1:]+self.locations[1:]:
            with self.assertRaises(frappe.PermissionError):doc.check_permission("read")
            with self.assertRaises(frappe.PermissionError):doc.check_permission("write")
        sites=frappe.get_list("TruCMMS Site",pluck="name")
        self.assertEqual(sites,[SITE_A])

    def test_company_site_and_location_must_match(self):
        self.equipment[0].site=SITE_B
        with self.assertRaises(frappe.ValidationError):self.equipment[0].save()
        self.equipment[0].reload();self.equipment[0].location=self.locations[1].name
        with self.assertRaises(frappe.ValidationError):self.equipment[0].save()

    def test_company_identity_is_stable(self):
        self.equipment[0].company=COMPANY_B;self.equipment[0].site=SITE_B;self.equipment[0].location=self.locations[2].name
        with self.assertRaises(frappe.ValidationError):self.equipment[0].save()

    def test_functional_parent_scope_and_cycles(self):
        child=frappe.get_doc({"doctype":"VB Equipment Location",**org_context(),"location_name":self.token+"CHILD","parent_location":self.locations[0].name}).insert()
        self.locations[0].parent_location=child.name
        with self.assertRaises(frappe.ValidationError):self.locations[0].save()
        child.parent_location=self.locations[1].name
        with self.assertRaises(frappe.ValidationError):child.save()

    def test_equipment_move_keeps_identity_and_requires_target_scope(self):
        grant_scope(self.user);frappe.set_user(self.user)
        equipment=self.equipment[0];original=equipment.name
        equipment.site=SITE_A2;equipment.location=self.locations[1].name
        with self.assertRaises(frappe.PermissionError):equipment.save()
        grant_scope(self.user,site=SITE_A2)
        equipment.save();self.assertEqual(equipment.name,original)

    def test_sharing_cannot_expand_scope(self):
        grant_scope(self.user)
        with self.assertRaises(frappe.PermissionError):
            frappe.share.add("VB Equipment",self.equipment[2].name,user=self.user,notify=0)
        frappe.share.add("VB Equipment",self.equipment[0].name,user=self.user,notify=0)
        permissions=frappe.get_all("User Permission",filters={"user":self.user},pluck="name")
        for name in permissions:frappe.delete_doc("User Permission",name)
        frappe.set_user(self.user)
        with self.assertRaises(frappe.PermissionError):self.equipment[0].check_permission("read")

    def test_site_requires_both_authorizations(self):
        grant_scope(self.user,company=COMPANY_A,site=SITE_B)
        frappe.set_user(self.user)
        self.assertEqual(frappe.get_list("VB Equipment",pluck="name"),[])
        with self.assertRaises(frappe.PermissionError):self.equipment[2].check_permission("read")

    def test_company_only_permission_is_not_sufficient(self):
        frappe.get_doc({"doctype":"User Permission","user":self.user,"allow":"Company","for_value":COMPANY_A,"apply_to_all_doctypes":1}).insert()
        frappe.set_user(self.user)
        self.assertEqual(frappe.get_list("VB Equipment",pluck="name"),[])
        with self.assertRaises(frappe.PermissionError):self.equipment[0].check_permission("read")

    def test_disabled_site_rejects_new_assignment_but_preserves_history(self):
        site=frappe.get_doc("TruCMMS Site",SITE_A)
        site.disabled=1;site.save()
        self.equipment[0].equipment_name="Historical record update";self.equipment[0].save()
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({"doctype":"VB Equipment",**org_context(),"equipment_code":self.token+"NEW","equipment_name":"New assignment","category":self.category.name}).insert()

    def test_site_code_stays_stable_when_description_changes(self):
        site=frappe.get_doc("TruCMMS Site",SITE_A)
        site.site_name="Editable description";site.save();self.assertEqual(site.name,SITE_A)
        site.site_code=SITE_A+"-CHANGED"
        with self.assertRaises(frappe.ValidationError):site.save()
