frappe.ui.form.on('TruCMMS Job Plan Revision', {
    setup(frm) {
        frm.set_query('job_plan', () => ({filters: {disabled: 0}}));
        frm.set_query('item', 'materials', () => ({filters: {disabled: 0, has_variants: 0}}));
    },
    refresh(frm) {
        const frozen = ['Approved', 'Retired'].includes(frm.doc.status);
        if (frozen) {
            frm.disable_save();
            for (const field of frm.meta.fields) frm.set_df_property(field.fieldname, 'read_only', 1);
        }
        if (frm.is_new()) return;
        const editor = frappe.user.has_role(['TruCMMS Dispatcher', 'TruCMMS Supervisor', 'System Manager']);
        const supervisor = frappe.user.has_role(['TruCMMS Supervisor', 'System Manager']);
        const run = (method, title, arg) => {
            if (frm.is_dirty()) {
                frappe.msgprint(__('Guarda los cambios antes de continuar.'));
                return;
            }
            frappe.prompt([{fieldname: 'reason', label: __('Motivo'), fieldtype: 'Small Text', reqd: 1}], values => {
                frappe.call({method: 'vanbags_maintenance.job_plans.' + method,
                    args: {name: frm.doc.name, [arg]: values.reason}, freeze: true,
                    callback(r) {
                        if (method === 'revise') frappe.set_route('Form', 'TruCMMS Job Plan Revision', r.message.name);
                        else frm.reload_doc();
                    }});
            }, __(title));
        };
        if (supervisor && frm.doc.status === 'Draft')
            frm.add_custom_button(__('Aprobar revisión'), () => run('approve', 'Aprobar revisión', 'approval_reason'));
        if (supervisor && frm.doc.status === 'Approved')
            frm.add_custom_button(__('Retirar revisión'), () => run('retire', 'Retirar revisión', 'retirement_reason'));
        if (editor && frozen)
            frm.add_custom_button(__('Nueva revisión'), () => run('revise', 'Nueva revisión', 'change_reason'));
    }
});
