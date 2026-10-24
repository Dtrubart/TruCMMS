app_name = "vanbags_maintenance"
app_title = "TruCMMS"
app_publisher = "Daniel Trujillo"
app_description = "Maintenance management for equipment, plans, work orders, activity assignments, and spare part requirements."
app_email = "daniel.trujillo1105@gmail.com"
app_license = "mit"

fixtures = [
	{
		"doctype": "Role",
		"filters": {"role_name": ["in", ["VB Maintenance User", "VB Maintenance Manager", "TruCMMS Requester", "TruCMMS Dispatcher"]]}
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
