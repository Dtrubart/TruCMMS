// Keep the established Home URL and native procedure forms inside TruCMMS.
(function () {
    function navigate() {
        const route = frappe.get_route() || [];
        if (route[0] === 'Workspaces' && route[1] === 'TruCMMS') {
            frappe.set_route('trucmms-start');
            return;
        }
        // The technical module name remains stable. Contextual revisions have no
        // top-level sidebar link, so native module fallback would select the old
        // module sidebar. Run after native refresh using its standard setup API.
        if (['Form', 'List'].includes(route[0]) &&
            ['TruCMMS Site Warehouse','TruCMMS Job Plan', 'TruCMMS Job Plan Revision','TruCMMS PM Plan','TruCMMS PM Occurrence','TruCMMS Meter','TruCMMS Meter Reading','TruCMMS Meter Epoch','TruCMMS Component','TruCMMS Component Installation','TruCMMS Inspection Finding','TruCMMS PM Event'].includes(route[1])) {
            queueMicrotask(() => {
                const current = frappe.get_route() || [];
                if (current[0] !== route[0] || current[1] !== route[1]) return;
                const sidebar = frappe.app?.sidebar;
                if (sidebar && frappe.boot?.workspace_sidebar_item?.trucmms &&
                    sidebar.sidebar_title !== 'TruCMMS') sidebar.setup('TruCMMS');
            });
        }
    }
    $(document).on('page-change.trucmms form-refresh.trucmms', navigate);
    $(navigate);
})();
