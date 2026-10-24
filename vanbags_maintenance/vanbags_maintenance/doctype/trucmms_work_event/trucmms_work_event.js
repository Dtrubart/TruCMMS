frappe.ui.form.on("TruCMMS Work Event", {
 refresh(frm) {frm.disable_save();if (frm.attachments) frm.attachments.add_attachment_wrapper.hide();}
});
