frappe.ui.form.on("VB Equipment", {
    setup(frm) {
        frm.set_query("site", () => ({filters: {company: frm.doc.company, disabled: 0}}));
        frm.set_query("location", () => ({filters: {
            company: frm.doc.company, site: frm.doc.site, disabled: 0,
            ...(false ? {name: ["!=", frm.doc.name]} : {})
        }}));
    }
});
