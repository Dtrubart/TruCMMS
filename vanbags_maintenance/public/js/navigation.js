// Keep the established Workspace URL as a compatible entry to the role-aware Home.
(function(){
 function open_home(){const route=frappe.get_route();if(route[0]==='Workspaces'&&route[1]==='TruCMMS')frappe.set_route('trucmms-start');}
 $(document).on('page-change.trucmms',open_home);
 $(open_home);
})();
