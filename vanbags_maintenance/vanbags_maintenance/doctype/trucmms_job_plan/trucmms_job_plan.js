frappe.ui.form.on('TruCMMS Job Plan', {
    setup(frm) {
        frm.set_query('site', () => ({filters: {company: frm.doc.company, disabled: 0}}));
    },
    company(frm) { if (!frm.is_new()) return; frm.set_value('site', null); },
    refresh(frm) {
        if (frm.is_new()) return;
        frm.add_custom_button(__('Revisiones'), () =>
            frappe.set_route('List', 'TruCMMS Job Plan Revision', {job_plan: frm.doc.name}));
        if (!frm.doc.disabled && frm.has_perm('write')) {
            frm.add_custom_button(__('Nuevo borrador'), () => {
                frappe.new_doc('TruCMMS Job Plan Revision', {
                    job_plan: frm.doc.name, revision_title: frm.doc.plan_name
                });
            });
        }
    }
});
