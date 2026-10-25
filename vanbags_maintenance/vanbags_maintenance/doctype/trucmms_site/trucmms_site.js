frappe.ui.form.on('TruCMMS Site', {
    async refresh(frm) {
        if (frm.is_new()) return;
        const {message} = await frappe.call({method:'vanbags_maintenance.configuration.operating_clock',args:{site:frm.doc.name}});
        const user_zone=frappe.boot.time_zone?.user || message.system_timezone;
        frm.dashboard.set_headline(__('Operating time: {0} ({1}). Form dates: {2}. Storage: {3}.',[message.operating_time,message.operating_timezone,user_zone,message.system_timezone]));
    }
});
