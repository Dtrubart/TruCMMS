frappe.ui.form.on("TruCMMS Maintenance Request", {
    setup(frm) {
        frm.set_query("site", () => ({filters:{company:frm.doc.company,disabled:0}}));
        for (const field of ["equipment","functional_location"]) {
            frm.set_query(field, () => ({filters:{company:frm.doc.company,site:frm.doc.site}}));
        }
    },
    refresh(frm) {
        if (frm.doc.status !== "Draft") {
            for (const field of ["company","site","equipment","functional_location","subject","description"]) frm.set_df_property(field,"read_only",1);
        }
    }
});
