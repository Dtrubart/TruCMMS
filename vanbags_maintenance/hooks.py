app_name = "vanbags_maintenance"
app_title = "TruCMMS"
app_publisher = "Daniel Trujillo"
app_description = "Maintenance management for equipment, plans, work orders, activity assignments, and spare part requirements."
app_email = "daniel.trujillo1105@gmail.com"
app_license = "mit"

fixtures = [
	{
		"doctype": "Role",
		"filters": {"role_name": ["in", ["VB Maintenance User", "VB Maintenance Manager", "TruCMMS Requester", "TruCMMS Dispatcher", "TruCMMS Supervisor", "TruCMMS Technician"]]}
	}
]

# Apps
# ------------------

required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "vanbags_maintenance",
# 		"logo": "/assets/vanbags_maintenance/logo.png",
# 		"title": "Vanbags Maintenance",
# 		"route": "/vanbags_maintenance",
# 		"has_permission": "vanbags_maintenance.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/vanbags_maintenance/css/vanbags_maintenance.css"
# app_include_js = "/assets/vanbags_maintenance/js/vanbags_maintenance.js"

# include js, css files in header of web template
# web_include_css = "/assets/vanbags_maintenance/css/vanbags_maintenance.css"
# web_include_js = "/assets/vanbags_maintenance/js/vanbags_maintenance.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "vanbags_maintenance/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "vanbags_maintenance/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "vanbags_maintenance.utils.jinja_methods",
# 	"filters": "vanbags_maintenance.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "vanbags_maintenance.install.before_install"
# after_install = "vanbags_maintenance.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "vanbags_maintenance.uninstall.before_uninstall"
# after_uninstall = "vanbags_maintenance.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "vanbags_maintenance.utils.before_app_install"
# after_app_install = "vanbags_maintenance.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "vanbags_maintenance.utils.before_app_uninstall"
# after_app_uninstall = "vanbags_maintenance.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "vanbags_maintenance.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "vanbags_maintenance.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"vanbags_maintenance.tasks.all"
# 	],
# 	"daily": [
# 		"vanbags_maintenance.tasks.daily"
# 	],
# 	"hourly": [
# 		"vanbags_maintenance.tasks.hourly"
# 	],
# 	"weekly": [
# 		"vanbags_maintenance.tasks.weekly"
# 	],
# 	"monthly": [
# 		"vanbags_maintenance.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "vanbags_maintenance.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "vanbags_maintenance.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "vanbags_maintenance.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "vanbags_maintenance.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["vanbags_maintenance.utils.before_request"]
# after_request = ["vanbags_maintenance.utils.after_request"]

# Job Events
# ----------
# before_job = ["vanbags_maintenance.utils.before_job"]
# after_job = ["vanbags_maintenance.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"vanbags_maintenance.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


# Native organizational context and least-privilege scope checks.
after_install = "vanbags_maintenance.organization.setup_company_selection"
after_migrate = "vanbags_maintenance.organization.setup_company_selection"
before_tests = "vanbags_maintenance.test_support.prepare_organization"
has_permission = {dt: "vanbags_maintenance.organization.has_permission" for dt in ("VB Equipment", "VB Equipment Location", "TruCMMS Site")}
permission_query_conditions = {
    "VB Equipment": "vanbags_maintenance.organization.equipment_query",
    "VB Equipment Location": "vanbags_maintenance.organization.location_query",
    "TruCMMS Site": "vanbags_maintenance.organization.site_query",
}

doc_events = {"DocShare": {"validate": "vanbags_maintenance.organization.validate_share"}}

# Native requests and evidence access; existing equipment scopes stay unchanged.
after_install = "vanbags_maintenance.requests.setup"
after_migrate = "vanbags_maintenance.requests.setup"
has_permission["TruCMMS Maintenance Request"] = "vanbags_maintenance.requests.has_permission"
has_permission["File"] = "vanbags_maintenance.requests.file_permission"
permission_query_conditions["TruCMMS Maintenance Request"] = "vanbags_maintenance.requests.query"
permission_query_conditions["File"] = "vanbags_maintenance.requests.file_query"
extend_doctype_class = {"File": ["vanbags_maintenance.requests.RequestFileGuard"]}
doc_events["DocShare"]["validate"] = ["vanbags_maintenance.organization.validate_share", "vanbags_maintenance.requests.validate_share"]

# Maintenance work orders: scope, authorization and assignment.
after_install = "vanbags_maintenance.work_orders.setup"
after_migrate = "vanbags_maintenance.work_orders.setup"
has_permission["TruCMMS Maintenance Work Order"] = "vanbags_maintenance.work_orders.has_permission"
permission_query_conditions["TruCMMS Maintenance Work Order"] = "vanbags_maintenance.work_orders.query"
doc_events["DocShare"]["validate"].append("vanbags_maintenance.work_orders.validate_share")

# Technician execution entries preserve the authorized order unchanged.
has_permission["TruCMMS Work Execution"] = "vanbags_maintenance.execution.has_permission"
permission_query_conditions["TruCMMS Work Execution"] = "vanbags_maintenance.execution.query"
doc_events["DocShare"]["validate"].append("vanbags_maintenance.execution.validate_share")

after_install = "vanbags_maintenance.lifecycle.setup"
after_migrate = "vanbags_maintenance.lifecycle.setup"
has_permission["TruCMMS Work Event"] = "vanbags_maintenance.lifecycle.event_permission"
permission_query_conditions["TruCMMS Work Event"] = "vanbags_maintenance.lifecycle.event_query"
doc_events["DocShare"]["validate"].append("vanbags_maintenance.lifecycle.validate_share")

has_permission["TruCMMS Execution Adjustment"]="vanbags_maintenance.adjustments.has_permission"
permission_query_conditions["TruCMMS Execution Adjustment"]="vanbags_maintenance.adjustments.query"
doc_events["DocShare"]["validate"].append("vanbags_maintenance.adjustments.validate_share")

# A/B: explicit team eligibility and safe temporal configuration.
after_install = "vanbags_maintenance.configuration.setup"
after_migrate = "vanbags_maintenance.configuration.setup"
for dt, query_name in [("TruCMMS Maintenance Team","team_query"),("TruCMMS Team Membership","member_query"),("TruCMMS Team Site Authorization","grant_query")]:
    has_permission[dt]="vanbags_maintenance.teams.permission"
    permission_query_conditions[dt]="vanbags_maintenance.teams."+query_name
has_permission["TruCMMS Team Assignment"]="vanbags_maintenance.lifecycle.event_permission"
permission_query_conditions["TruCMMS Team Assignment"]="vanbags_maintenance.teams.assignment_query"
doc_events["DocShare"]["validate"].append("vanbags_maintenance.teams.validate_share")
doc_events["System Settings"]={"validate":"vanbags_maintenance.configuration.guard_system_timezone"}

# C1 keeps the previous workflow as an inactive compatibility contract.
after_install="vanbags_maintenance.work_cycle.setup"
after_migrate="vanbags_maintenance.work_cycle.setup"
for dt,method in [("TruCMMS Work Cycle","cycle_query"),("TruCMMS Work Allocation","allocation_query")]:
    has_permission[dt]="vanbags_maintenance.lifecycle.event_permission"
    permission_query_conditions[dt]="vanbags_maintenance.work_cycle."+method
doc_events["DocShare"]["validate"].append("vanbags_maintenance.work_cycle.validate_share")

# D: stable equipment identities, controlled effective placement and typed profiles.
after_install="vanbags_maintenance.assets.setup"
after_migrate="vanbags_maintenance.assets.setup"
for dt,method in [("TruCMMS Equipment Installation","installation_query"),("TruCMMS Asset Event","event_query")]:
    has_permission[dt]="vanbags_maintenance.assets.history_permission"
    permission_query_conditions[dt]="vanbags_maintenance.assets."+method
doc_events["DocShare"]["validate"].append("vanbags_maintenance.assets.validate_share")
doc_events["VB Equipment Location"]={"validate":"vanbags_maintenance.assets.validate_location"}

# E: permission-coherent work views and retry-safe native execution submission.
after_install="vanbags_maintenance.work_views.setup"
after_migrate="vanbags_maintenance.work_views.setup"

# Current IANA rules for native Desk Datetime controls, using the supported Moment API.
app_include_js=["/assets/vanbags_maintenance/js/timezone_rules.js","/assets/vanbags_maintenance/js/navigation.js","/assets/vanbags_maintenance/js/r2_forms.js"]

# R1 candidate: approved task-oriented navigation, with native permissions preserved.
after_install="vanbags_maintenance.navigation.setup"
after_migrate="vanbags_maintenance.navigation.setup"
extend_bootinfo=["vanbags_maintenance.navigation.extend_bootinfo"]

# R2.1: versioned procedure library; no scheduler or order generation yet.
after_install="vanbags_maintenance.job_plans.setup"
after_migrate="vanbags_maintenance.job_plans.setup"
for dt,method in [("TruCMMS Job Plan","plan_query"),("TruCMMS Job Plan Revision","revision_query")]:
    has_permission[dt]="vanbags_maintenance.job_plans.permission"
    permission_query_conditions[dt]="vanbags_maintenance.job_plans."+method
doc_events["DocShare"]["validate"].append("vanbags_maintenance.job_plans.validate_share")

# Complete R2: explicit future obligations, controlled providers and scoped meters.
after_install="vanbags_maintenance.r2_records.setup"
after_migrate="vanbags_maintenance.r2_records.setup"
for dt,method in [("TruCMMS PM Plan","plan_query"),("TruCMMS PM Occurrence","occurrence_query"),("TruCMMS PM Event","event_query"),("TruCMMS Meter","meter_query"),("TruCMMS Meter Reading","reading_query"),("TruCMMS Meter Epoch","epoch_query"),("TruCMMS Component","component_query"),("TruCMMS Component Installation","installation_query"),("TruCMMS Inspection Finding","finding_query")]:
    has_permission[dt]="vanbags_maintenance.r2_records.permission"
    permission_query_conditions[dt]="vanbags_maintenance.r2_records."+method
doc_events["DocShare"]["validate"].append("vanbags_maintenance.r2_records.validate_share")
doc_events["TruCMMS Maintenance Work Order"]={"on_update":"vanbags_maintenance.preventive.order_updated"}
doc_events["TruCMMS Work Execution"]={"after_insert":"vanbags_maintenance.inspections.recorded"}
scheduler_events={"hourly":["vanbags_maintenance.preventive.scheduler"]}
