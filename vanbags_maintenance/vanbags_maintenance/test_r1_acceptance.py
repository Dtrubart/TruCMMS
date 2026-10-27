import uuid
import frappe
from frappe.model.workflow import apply_workflow
from frappe.utils import now_datetime,add_to_date
from vanbags_maintenance import teams,work_orders as wo,work_contract,work_cycle,execution
from vanbags_maintenance.test_support import COMPANY_A,SITE_A,SITE_A2,grant_scope
from vanbags_maintenance.vanbags_maintenance.test_work_orders import WorkOrderCase

class TestR1AcceptanceEdges(WorkOrderCase):
    use_c_policy=True
    def second_site_order(self,authorize_team):
        frappe.set_user('Administrator')
        for role in ('dispatcher','supervisor','tech'):grant_scope(self.users[role],site=SITE_A2)
        location=frappe.get_doc({'doctype':'VB Equipment Location','company':COMPANY_A,'site':SITE_A2,'location_name':self.token+'-SECOND'}).insert()
        if authorize_team:frappe.get_doc({'doctype':teams.GRANT,'team':self.team,'site':SITE_A2,'valid_from':add_to_date(now_datetime(),minutes=-1)}).insert()
        frappe.set_user(self.users['dispatcher']);doc=frappe.get_doc(work_contract.create_direct(COMPANY_A,SITE_A2,'Shared team second-site work','R1 assignment verification','Medium',uuid.uuid4().hex,'Authorized direct assignment test',functional_location=location.name));doc.responsible_team=self.team;doc.required_discipline=self.discipline;doc.save()
        frappe.set_user(self.users['supervisor']);return apply_workflow(doc.as_dict(),'Authorize')
    def test_shared_team_assigns_at_second_authorized_site(self):
        doc=self.second_site_order(True);doc.assigned_to=self.users['tech'];doc.save();doc=apply_workflow(doc.as_dict(),'Assign');row=frappe.get_doc(teams.ASSIGN,doc.team_assignment)
        self.assertEqual(row.team,self.team);self.assertEqual(row.site,SITE_A2);frappe.set_user(self.users['tech']);self.assertEqual(execution.order_for_recording(doc.name).name,doc.name)
    def test_person_scope_does_not_replace_missing_team_site_authorization(self):
        doc=self.second_site_order(False);doc.assigned_to=self.users['tech']
        with self.assertRaises(frappe.PermissionError):doc.save()
        self.assertFalse(frappe.db.exists(teams.ASSIGN,{'work_order':doc.name}))
    def test_technician_changes_team_without_rewriting_prior_assignment(self):
        doc=self.assign();old=doc.team_assignment;frappe.set_user('Administrator')
        team=frappe.get_doc({'doctype':teams.TEAM,'team_code':self.token+'-NEW','team_name':'New responsible team','company':COMPANY_A,'management_site':SITE_A,'team_type':'Internal','disciplines':[{'discipline':self.discipline}]}).insert()
        for dt,values in [(teams.GRANT,{'site':SITE_A}),(teams.MEMBER,{'user':self.users['tech'],'discipline':self.discipline,'function':'Technician'})]:frappe.get_doc({'doctype':dt,'team':team.name,'valid_from':add_to_date(now_datetime(),minutes=-1),**values}).insert()
        membership=frappe.get_doc(teams.MEMBER,self.memberships['tech']);membership.revoked=1;membership.save()
        frappe.set_user(self.users['supervisor']);result=work_cycle.reassign(doc.name,self.users['tech'],'Technician moved to another authorized team',team=team.name,discipline=self.discipline)
        self.assertEqual(frappe.db.get_value(teams.ASSIGN,old,'team'),self.team);self.assertNotEqual(result['team_assignment'],old);self.assertEqual(frappe.db.get_value(teams.ASSIGN,result['team_assignment'],'team'),team.name)
        frappe.set_user(self.users['tech']);self.assertEqual(execution.order_for_recording(doc.name).responsible_team,team.name)
