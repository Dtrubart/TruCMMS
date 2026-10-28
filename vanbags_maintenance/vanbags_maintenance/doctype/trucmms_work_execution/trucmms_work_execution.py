import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime
from vanbags_maintenance import execution as policy


class TruCMMSWorkExecution(Document):
    def before_insert(self):
        from vanbags_maintenance.submission import validate_new
        validate_new(self)
        order=policy.order_for_recording(self.work_order, lock=True)
        self.company=order.company;self.site=order.site;self.execution_cycle=order.execution_cycle or 1
        self.technician=self.owner=frappe.session.user
        self.recorded_on=now_datetime()
        from vanbags_maintenance.allocations import current
        allocation=current(order,frappe.session.user,lock=True)
        self.allocation=allocation.name if allocation else None
        self.discipline=allocation.discipline if allocation else None
        self.team=allocation.team if allocation else None

    def validate(self):
        if not self.is_new():frappe.throw('Saved execution entries are immutable.',frappe.PermissionError)
        order=policy.order_for_recording(self.work_order,lock=True)
        if (self.company,self.site,self.technician)!=(order.company,order.site,frappe.session.user):
            frappe.throw('Execution context and technician are set by the server.')
        start,end=get_datetime(self.actual_start),get_datetime(self.actual_end)
        if not self.actual_start or not self.actual_end or end<=start:frappe.throw('Actual end must be after actual start.')
        if end>now_datetime():frappe.throw('Actual execution cannot be recorded in the future.')
        from vanbags_maintenance.allocations import assignment_start
        assigned=assignment_start(order,self.technician)
        if not assigned or start<get_datetime(assigned):frappe.throw('Execution must occur after the current assignment.')
        if order.get('rework_on') and start<get_datetime(order.rework_on):frappe.throw('Rework execution must occur after the rework decision.')
        if order.get('lifecycle_policy')=='C1':
            from vanbags_maintenance.allocations import validate_execution
            validate_execution(order,self,start,end)
        self.findings=(self.findings or '').strip()
        if not self.findings or not self.tasks:frappe.throw('Findings and at least one performed task are required.')
        for row in self.tasks:
            row.task=(row.task or '').strip();row.findings=(row.findings or '').strip()
            if not row.task or not row.findings or row.result not in ('Completed','Partial','Blocked'):
                frappe.throw('Each performed task requires a task, valid result and findings.')
        # Serialize all entries for this technician, including work on different orders.
        frappe.db.sql('select name from `tabUser` where name=%s for update',(self.technician,))
        if frappe.db.sql('select name from `tabTruCMMS Work Execution` where technician=%s and actual_start<%s and actual_end>%s and not exists (select 1 from `tabTruCMMS Execution Adjustment` a where a.execution=`tabTruCMMS Work Execution`.name) for update',(self.technician,end,start)):
            frappe.throw('Actual time overlaps another execution entry for this technician.')
        self.actual_minutes=(end-start).total_seconds()/60
        from vanbags_maintenance.inspections import validate_execution
        validate_execution(self,order)

    def on_trash(self):
        frappe.throw('Execution history cannot be deleted.',frappe.PermissionError)
