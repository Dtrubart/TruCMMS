frappe.query_reports["TruCMMS Installation Register"]={filters:[
 {fieldname:"company",label:__("Company"),fieldtype:"Link",options:"Company"},
 {fieldname:"site",label:__("Site"),fieldtype:"Link",options:"TruCMMS Site"},
 {fieldname:"equipment",label:__("Equipment"),fieldtype:"Link",options:"VB Equipment"},
 {fieldname:"location",label:__("Functional Location"),fieldtype:"Link",options:"VB Equipment Location"},
 {fieldname:"active_only",label:__("Active Only"),fieldtype:"Check",default:1},
 {fieldname:"as_of",label:__("As Of"),fieldtype:"Datetime",description:__("Effective occupancy at the selected time; overrides Active Only.")}
]};
