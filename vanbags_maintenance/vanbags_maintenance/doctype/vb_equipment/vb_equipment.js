frappe.ui.form.on("VB Equipment", {
    setup(frm) {
        frm.set_query("site", () => ({filters: {company: frm.doc.company, disabled: 0}}));
        frm.set_query("location", () => ({filters: {
            company: frm.doc.company, site: frm.doc.site, disabled: 0,
            ...(false ? {name: ["!=", frm.doc.name]} : {})
        }}));
    }
});

frappe.ui.form.on("VB Equipment",{refresh(frm){if(!frm.is_new())frm.add_custom_button(__("Maintenance History"),()=>frappe.set_route("query-report","TruCMMS Equipment History",{equipment:frm.doc.name}));}});
