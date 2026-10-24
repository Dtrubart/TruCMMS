import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime
from vanbags_maintenance import organization as org
from vanbags_maintenance import work_orders as policy


class TruCMMSMaintenanceWorkOrder(Document):
    def before_insert(self):
        if self.status not in (None, '', 'Draft'):
            frappe.throw('New work orders must start in Draft.')
        self.status='Draft'
        self.execution_cycle=1
        self.requester=frappe.db.get_value('TruCMMS Maintenance Request',self.maintenance_request,'owner')
        from vanbags_maintenance.lifecycle import AUDIT
        for field in AUDIT:self.set(field,None)
        for f in policy.AUDIT:self.set(f,None)

    def validate(self):
        org.validate_context(self)
        old=self.get_doc_before_save()
        from vanbags_maintenance import lifecycle
        if old:
            lifecycle.validate_change(self,old)
            if self.status!=old.status and (old.status,self.status) not in (('Draft','Authorized'),('Authorized','Assigned')):
                return
        for f in ('subject','scope'):self.set(f,(self.get(f) or '').strip())
        if not self.subject or not self.scope:frappe.throw('Subject and scope are required.')
        if self.origin_type!='Maintenance Request':frappe.throw('Unsupported work order origin.')
        if self.priority not in ('Low','Medium','High','Critical'):frappe.throw('Invalid work order priority.')
        if not old:
            request=frappe.get_doc('TruCMMS Maintenance Request',self.maintenance_request)
            request.check_permission('read')
            if request.status!='Approved':frappe.throw('Only approved requests can generate work orders.')
            if any(self.get(f)!=request.get(f) for f in policy.CONTEXT):frappe.throw('Work order context must match its approved request.')
            if self.assigned_to:frappe.throw('Authorize the work before assigning a technician.')
            return
        if self.maintenance_request!=old.maintenance_request or any(self.get(f)!=old.get(f) for f in policy.CONTEXT):
            frappe.throw('Request and organizational/equipment references cannot be changed.')
        for f in policy.AUDIT:
            a,b=old.get(f),self.get(f)
            if f.endswith('_on') and a and b:a,b=get_datetime(a),get_datetime(b)
            if a!=b:frappe.throw('Work order audit fields cannot be changed.')
        if old.status!='Draft' and any(self.get(f)!=old.get(f) for f in ('subject','scope','priority','origin_type')):
            frappe.throw('Authorized scope is immutable; a revision process is required.')
        if self.status!=old.status:
            if (old.status,self.status)==('Draft','Authorized'):
                if not policy.supervisor():frappe.throw('Supervisor authorization required.',frappe.PermissionError)
                if self.assigned_to:frappe.throw('Authorize before assigning a technician.')
                self.authorized_by=frappe.session.user;self.authorized_on=now_datetime()
            elif (old.status,self.status)==('Authorized','Assigned'):
                if not policy.supervisor():frappe.throw('Supervisor assignment required.',frappe.PermissionError)
                policy.validate_technician(self)
                self.assigned_by=frappe.session.user;self.assigned_on=now_datetime()
            else:frappe.throw('Invalid work order transition.')
        if self.assigned_to!=old.assigned_to:
            if not policy.supervisor() or self.status not in ('Authorized','Assigned'):frappe.throw('Assignment requires an authorized order and supervisor.',frappe.PermissionError)
            policy.validate_technician(self)
            if self.status=='Assigned':
                self.assigned_by=frappe.session.user;self.assigned_on=now_datetime()
        if self.status=='Assigned' and not self.assigned_to:frappe.throw('Assigned orders require a technician.')

    def on_trash(self):
        if self.status!='Draft':frappe.throw('Authorized work orders cannot be deleted.',frappe.PermissionError)
