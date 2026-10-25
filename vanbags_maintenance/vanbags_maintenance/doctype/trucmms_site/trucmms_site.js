frappe.ui.form.on('TruCMMS Site', {
    async refresh(frm) {
        if (frm.is_new()) return;
        const {message} = await frappe.call({method:'vanbags_maintenance.configuration.operating_clock',args:{site:frm.doc.name}});
        frm.dashboard.set_headline(__('Operating time: {0} ({1}). Form dates: {2}.',[message.operating_time,message.operating_timezone,message.system_timezone]));
    }
});
