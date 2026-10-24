frappe.ui.form.on("VB Equipment Location", {
    setup(frm) {
        frm.set_query("site", () => ({filters: {company: frm.doc.company, disabled: 0}}));
        frm.set_query("parent_location", () => ({filters: {
            company: frm.doc.company, site: frm.doc.site, disabled: 0,
            ...(true ? {name: ["!=", frm.doc.name]} : {})
        }}));
    }
});
