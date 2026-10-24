frappe.ui.form.on("TruCMMS Maintenance Request", {
    setup(frm) {
        frm.set_query("site", () => ({filters:{company:frm.doc.company,disabled:0}}));
        for (const field of ["equipment","functional_location"]) {
            frm.set_query(field, () => ({filters:{company:frm.doc.company,site:frm.doc.site}}));
        }
    },
    refresh(frm) {
        if (!frm.is_new() && frm.doc.status === "Approved" && (frappe.user.has_role("TruCMMS Dispatcher") || frappe.user.has_role("System Manager") || frappe.user.has_role("TruCMMS Supervisor"))) {
            frm.add_custom_button(__("Create / Open Work Order"), async () => {
                const result = await frappe.call({method:"vanbags_maintenance.work_orders.from_request",args:{request:frm.doc.name}});
                frappe.set_route("Form","TruCMMS Maintenance Work Order",result.message.name);
            });
        }
        if (frm.doc.status !== "Draft") {
            for (const field of ["company","site","equipment","functional_location","subject","description"]) frm.set_df_property(field,"read_only",1);
        }
    }
});
