# Diccionario de DocTypes de la versión verificada

Fuente: `60cd0649700edf6c9b924fd7b9c4a76585b34d6f`. Metadatos propios; no contiene datos operativos. Los campos custom en documentos nativos se explican en el contrato R3.

## TruCMMS Asset Event

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| equipment | Link | VB Equipment | 0 |  |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| other_site | Link | TruCMMS Site |  |  |
| action | Data |  | 1 |  |
| reason | Small Text |  | 1 |  |
| effective_on | Datetime |  | 1 |  |
| recorded_on | Datetime |  | 1 |  |
| recorded_by | Link | User | 1 |  |
| before_snapshot | JSON |  |  |  |
| after_snapshot | JSON |  |  |  |
| location | Link | VB Equipment Location |  |  |

Roles definidos: VB Maintenance User: read, select, report; VB Maintenance Manager: read, select, report; TruCMMS Requester: read, select, report; TruCMMS Dispatcher: read, select, report; TruCMMS Supervisor: read, select, report; TruCMMS Technician: read, select, report; System Manager: read, select, report. Los hooks pueden restringir más estos permisos.

## TruCMMS Attribute Definition

Tipo: tabla hija. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| key | Data |  | 1 |  |
| label | Data |  | 1 |  |
| value_type | Select | Text<br>Integer<br>Decimal<br>Date<br>Boolean<br>Choice | 1 |  |
| unit | Data |  |  |  |
| required | Check |  |  |  |
| minimum | Data |  |  |  |
| maximum | Data |  |  |  |
| choices | Small Text |  |  |  |

Roles definidos: . Los hooks pueden restringir más estos permisos.

## TruCMMS Attribute Value

Tipo: tabla hija. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| key | Data |  | 1 |  |
| value | Small Text |  | 1 |  |
| value_type | Data |  |  | 1 |
| unit | Data |  |  | 1 |

Roles definidos: . Los hooks pueden restringir más estos permisos.

## TruCMMS Calendar Assignment

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| technician | Link | User | 1 |  |
| calendar | Link | TruCMMS Resource Calendar | 1 |  |
| from_date | Date |  | 1 |  |
| to_date | Date |  | 1 |  |
| disabled | Check |  |  |  |
| reason | Small Text |  | 1 |  |
| calendar_snapshot | Long Text |  |  | 1 |

Roles definidos: System Manager: read, select, create, write; TruCMMS Supervisor: read, select, create, write; TruCMMS Dispatcher: read, select; TruCMMS Technician: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Calendar Generation

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| technician | Link | User | 1 | 1 |
| assignment | Link | TruCMMS Calendar Assignment | 1 | 1 |
| from_date | Date |  | 1 | 1 |
| to_date | Date |  | 1 | 1 |
| window_count | Int |  |  | 1 |
| reason | Small Text |  | 1 | 1 |
| recorded_by | Link | User | 1 | 1 |
| recorded_on | Datetime |  | 1 | 1 |
| generation_key | Data |  |  | 1 |
| snapshot | Long Text |  |  | 1 |

Roles definidos: System Manager: read, select; TruCMMS Supervisor: read, select; TruCMMS Dispatcher: read, select; TruCMMS Technician: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Calendar Slot

Tipo: tabla hija. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| weekday | Select | Monday<br>Tuesday<br>Wednesday<br>Thursday<br>Friday<br>Saturday<br>Sunday | 1 |  |
| starts_at | Time |  | 1 |  |
| ends_at | Time |  | 1 |  |
| next_day | Check |  |  |  |

Roles definidos: . Los hooks pueden restringir más estos permisos.

## TruCMMS Component

Tipo: documento. Identidad: `field:code`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| code | Data |  | 1 |  |
| component_name | Data |  | 1 |  |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| equipment | Link | VB Equipment |  |  |
| position | Data |  |  |  |
| serial_number | Data |  |  |  |
| criticality | Link | TruCMMS Criticality |  |  |
| disabled | Check |  |  |  |
| description | Small Text |  |  |  |

Roles definidos: TruCMMS Dispatcher: read, select, report; TruCMMS Supervisor: read, select, create, write, report; TruCMMS Technician: read, select, report; System Manager: read, select, create, write, report; VB Maintenance Manager: read, select, create, write, report; VB Maintenance User: read, select, report. Los hooks pueden restringir más estos permisos.

## TruCMMS Component Installation

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| component | Link | TruCMMS Component |  | 1 |
| company | Link | Company | 1 | 1 |
| site | Link | TruCMMS Site | 1 | 1 |
| equipment | Link | VB Equipment |  | 1 |
| position | Data |  |  | 1 |
| effective_from | Datetime |  |  | 1 |
| effective_until | Datetime |  |  | 1 |
| active_key | Data |  |  | 1 |
| reason | Small Text |  |  | 1 |
| recorded_by | Link | User |  | 1 |
| recorded_on | Datetime |  |  | 1 |

Roles definidos: TruCMMS Dispatcher: read, select, report; TruCMMS Supervisor: read, select, report; TruCMMS Technician: read, select, report; System Manager: read, select, report; VB Maintenance Manager: read, select, report; VB Maintenance User: read, select, report. Los hooks pueden restringir más estos permisos.

## TruCMMS Criticality

Tipo: documento. Identidad: `field:code`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| code | Data |  | 1 |  |
| criticality_name | Data |  | 1 |  |
| rank | Int |  | 1 |  |
| description | Small Text |  |  |  |
| disabled | Check |  |  |  |

Roles definidos: VB Maintenance User: read, select, report; VB Maintenance Manager: read, select, report; TruCMMS Requester: read, select, report; TruCMMS Dispatcher: read, select, report; TruCMMS Supervisor: read, select, report; TruCMMS Technician: read, select, report; System Manager: read, select, create, write, report. Los hooks pueden restringir más estos permisos.

## TruCMMS Deployment

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| package_fingerprint | Data |  | 1 | 1 |
| site_name | Data |  | 1 | 1 |
| framework_version | Data |  | 1 | 1 |
| policy_version | Data |  | 1 | 1 |
| migration_result | Data |  | 1 | 1 |
| storage_timezone | Data |  | 1 | 1 |
| deployed_on | Datetime |  | 1 | 1 |

Roles definidos: System Manager: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Discipline

Tipo: documento. Identidad: `field:discipline_code`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| discipline_code | Data |  | 1 |  |
| discipline_name | Data |  | 1 |  |
| description | Small Text |  | 0 |  |
| disabled | Check |  | 0 |  |

Roles definidos: System Manager: read, select, create, write; TruCMMS Supervisor: read, select; TruCMMS Dispatcher: read, select; TruCMMS Technician: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Equipment Installation

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| equipment | Link | VB Equipment | 1 |  |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| location | Link | VB Equipment Location |  |  |
| effective_from | Datetime |  | 1 |  |
| effective_until | Datetime |  |  |  |
| recorded_on | Datetime |  | 1 |  |
| recorded_by | Link | User | 1 |  |
| ended_on | Datetime |  |  |  |
| ended_by | Link | User |  |  |
| reason | Small Text |  | 1 |  |
| end_reason | Small Text |  |  |  |
| entry_type | Select | Initial<br>Declared Baseline<br>Install<br>Transfer<br>Replacement | 1 |  |

Roles definidos: VB Maintenance User: read, select, report; VB Maintenance Manager: read, select, report; TruCMMS Requester: read, select, report; TruCMMS Dispatcher: read, select, report; TruCMMS Supervisor: read, select, report; TruCMMS Technician: read, select, report; System Manager: read, select, report. Los hooks pueden restringir más estos permisos.

## TruCMMS Equipment Profile

Tipo: documento. Identidad: `field:code`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| code | Data |  | 1 |  |
| profile_name | Data |  | 1 |  |
| version | Int |  | 1 |  |
| disabled | Check |  |  |  |
| definitions | Table | TruCMMS Attribute Definition | 1 |  |

Roles definidos: VB Maintenance User: read, select, report; VB Maintenance Manager: read, select, report; TruCMMS Requester: read, select, report; TruCMMS Dispatcher: read, select, report; TruCMMS Supervisor: read, select, report; TruCMMS Technician: read, select, report; System Manager: read, select, create, write, report. Los hooks pueden restringir más estos permisos.

## TruCMMS Execution Adjustment

Tipo: documento. Identidad: `format:ADJ-{YYYY}-{#####}`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| execution | Link | TruCMMS Work Execution | 1 |  |
| work_order | Link | TruCMMS Maintenance Work Order |  | 1 |
| company | Link | Company |  | 1 |
| site | Link | TruCMMS Site |  | 1 |
| reason | Long Text |  | 1 | 1 |
| actor | Link | User |  | 1 |
| occurred_on | Datetime |  |  | 1 |

Roles definidos: TruCMMS Supervisor: read; TruCMMS Dispatcher: read; TruCMMS Technician: read; TruCMMS Requester: read; System Manager: read. Los hooks pueden restringir más estos permisos.

## TruCMMS Execution Task

Tipo: tabla hija. Identidad: `nativa`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| task | Data |  | 1 |  |
| result | Select | Completed<br>Partial<br>Blocked | 1 |  |
| findings | Small Text |  | 1 |  |
| procedure_task_code | Data |  |  |  |

Roles definidos: . Los hooks pueden restringir más estos permisos.

## TruCMMS Inspection Finding

Tipo: documento. Identidad: `field:finding_key`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| finding_key | Data |  |  | 1 |
| company | Link | Company | 1 | 1 |
| site | Link | TruCMMS Site | 1 | 1 |
| equipment | Link | VB Equipment |  | 1 |
| component | Link | TruCMMS Component |  | 1 |
| work_order | Link | TruCMMS Maintenance Work Order |  | 1 |
| execution | Link | TruCMMS Work Execution |  | 1 |
| metric_key | Data |  |  | 1 |
| description | Small Text |  |  | 1 |
| observed_value | Float |  |  | 1 |
| expected_range | Data |  |  | 1 |
| status | Select | Open<br>Action Required<br>Accepted Deviation<br>Resolved |  | 1 |
| followup_order | Link | TruCMMS Maintenance Work Order |  | 1 |
| review_reason | Small Text |  |  | 1 |
| reviewed_by | Link | User |  | 1 |
| reviewed_on | Datetime |  |  | 1 |
| recorded_by | Link | User |  | 1 |
| recorded_on | Datetime |  |  | 1 |

Roles definidos: TruCMMS Dispatcher: read, select, report; TruCMMS Supervisor: read, select, report; TruCMMS Technician: read, select, report; System Manager: read, select, report. Los hooks pueden restringir más estos permisos.

## TruCMMS Job Plan

Tipo: documento. Identidad: `field:code`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| code | Data |  | 1 |  |
| plan_name | Data |  | 1 |  |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| disabled | Check |  |  |  |
| description | Small Text |  |  |  |

Roles definidos: TruCMMS Dispatcher: read, select, create, write, report; TruCMMS Supervisor: read, select, create, write, report; TruCMMS Technician: read, select, report; System Manager: read, select, create, write, report. Los hooks pueden restringir más estos permisos.

## TruCMMS Job Plan Material

Tipo: tabla hija. Identidad: `nativa`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| task_code | Data |  |  |  |
| item | Link | Item | 1 |  |
| quantity | Float |  | 1 |  |
| uom | Link | UOM | 1 |  |
| item_name | Data |  |  | 1 |
| stock_uom | Link | UOM |  | 1 |
| conversion_factor | Float |  |  | 1 |
| stock_quantity | Float |  |  | 1 |
| notes | Small Text |  |  |  |

Roles definidos: . Los hooks pueden restringir más estos permisos.

## TruCMMS Job Plan Measurement

Tipo: tabla hija. Identidad: `nativa`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| task_code | Data |  | 1 |  |
| metric_key | Data |  | 1 |  |
| metric_name | Data |  | 1 |  |
| metric_kind | Select | Cumulative<br>Condition<br>Rate | 1 |  |
| unit | Link | UOM | 1 |  |
| direction | Select | Increasing<br>Decreasing<br>Variable | 1 |  |
| required | Check |  |  |  |
| has_lower_limit | Check |  |  |  |
| lower_limit | Float |  |  |  |
| has_upper_limit | Check |  |  |  |
| upper_limit | Float |  |  |  |

Roles definidos: . Los hooks pueden restringir más estos permisos.

## TruCMMS Job Plan Revision

Tipo: documento. Identidad: `field:revision_key`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| job_plan | Link | TruCMMS Job Plan | 1 |  |
| revision_title | Data |  | 1 |  |
| revision_number | Int |  |  | 1 |
| revision_key | Data |  |  | 1 |
| status | Select | Draft<br>Approved<br>Retired |  | 1 |
| company | Link | Company |  | 1 |
| site | Link | TruCMMS Site |  | 1 |
| previous_revision | Link | TruCMMS Job Plan Revision |  | 1 |
| change_reason | Small Text |  | 1 |  |
| safety_notes | Small Text |  |  |  |
| task_section | Section Break |  |  |  |
| tasks | Table | TruCMMS Job Plan Task | 1 |  |
| measurement_section | Section Break |  |  |  |
| measurements | Table | TruCMMS Job Plan Measurement |  |  |
| material_section | Section Break |  |  |  |
| materials | Table | TruCMMS Job Plan Material |  |  |
| audit_section | Section Break |  |  |  |
| approved_by | Link | User |  | 1 |
| approved_on | Datetime |  |  | 1 |
| approval_reason | Small Text |  |  | 1 |
| retired_by | Link | User |  | 1 |
| retired_on | Datetime |  |  | 1 |
| retirement_reason | Small Text |  |  | 1 |
| content_hash | Data |  |  | 1 |
| content_json | Code | JSON |  | 1 |

Roles definidos: TruCMMS Dispatcher: read, select, create, write, report; TruCMMS Supervisor: read, select, create, write, report; TruCMMS Technician: read, select, report; System Manager: read, select, create, write, report. Los hooks pueden restringir más estos permisos.

## TruCMMS Job Plan Task

Tipo: tabla hija. Identidad: `nativa`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| task_code | Data |  | 1 |  |
| instructions | Small Text |  | 1 |  |
| discipline | Link | TruCMMS Discipline |  |  |
| estimated_minutes | Float |  |  |  |
| mandatory | Check |  |  |  |
| evidence_required | Check |  |  |  |

Roles definidos: . Los hooks pueden restringir más estos permisos.

## TruCMMS Maintenance Request

Tipo: documento. Identidad: `MR-.YYYY.-.#####`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| equipment | Link | VB Equipment |  |  |
| functional_location | Link | VB Equipment Location |  |  |
| subject | Data |  | 1 |  |
| description | Long Text |  | 1 |  |
| priority | Select | Low<br>Medium<br>High<br>Critical | 1 |  |
| status | Select | Draft<br>Submitted<br>Under Review<br>Approved<br>Rejected |  | 1 |
| dispatcher_notes | Small Text |  |  |  |
| rejection_reason | Small Text |  |  |  |
| requested_by | Link | User |  | 1 |
| submitted_on | Datetime |  |  | 1 |
| reviewed_by | Link | User |  | 1 |
| reviewed_on | Datetime |  |  | 1 |
| equipment_snapshot | JSON |  |  | 1 |

Roles definidos: TruCMMS Requester: read, create, write; TruCMMS Dispatcher: read, write; System Manager: read, write, delete, report, export, share; TruCMMS Supervisor: read. Los hooks pueden restringir más estos permisos.

## TruCMMS Maintenance Team

Tipo: documento. Identidad: `field:team_code`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| team_code | Data |  | 1 |  |
| team_name | Data |  | 1 |  |
| company | Link | Company | 1 |  |
| management_site | Link | TruCMMS Site | 1 |  |
| team_type | Select | Internal<br>External | 1 |  |
| disabled | Check |  | 0 |  |
| disciplines | Table | TruCMMS Team Discipline | 1 |  |

Roles definidos: System Manager: read, select, create, write; TruCMMS Supervisor: read, select, create, write; TruCMMS Dispatcher: read, select; TruCMMS Technician: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Maintenance Work Order

Tipo: documento. Identidad: `format:MWO-{YYYY}-{#####}`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| status | Select | Draft<br>Authorized<br>Assigned<br>On Hold<br>Technical Completed<br>Verified<br>Accepted<br>Closed<br>Cancelled | 1 | 1 |
| origin_type | Select | Maintenance Request<br>Direct<br>Preventive<br>Inspection | 1 | 1 |
| maintenance_request | Link | TruCMMS Maintenance Request | 0 | 1 |
| company | Link | Company | 1 | 1 |
| site | Link | TruCMMS Site | 1 | 1 |
| equipment | Link | VB Equipment | 0 | 1 |
| functional_location | Link | VB Equipment Location | 0 | 1 |
| subject | Data |  | 1 |  |
| scope | Long Text |  | 1 |  |
| priority | Select | Low<br>Medium<br>High<br>Critical | 1 |  |
| assigned_to | Link | User |  |  |
| authorized_by | Link | User |  | 1 |
| authorized_on | Datetime |  |  | 1 |
| assigned_by | Link | User |  | 1 |
| assigned_on | Datetime |  |  | 1 |
| requester | Link | User |  | 1 |
| execution_cycle | Int |  |  | 1 |
| completed_by | Link | User |  | 1 |
| completed_on | Datetime |  |  | 1 |
| completed_reason | Long Text |  |  | 1 |
| accepted_by | Link | User |  | 1 |
| accepted_on | Datetime |  |  | 1 |
| accepted_reason | Long Text |  |  | 1 |
| closed_by | Link | User |  | 1 |
| closed_on | Datetime |  |  | 1 |
| closed_reason | Long Text |  |  | 1 |
| cancelled_by | Link | User |  | 1 |
| cancelled_on | Datetime |  |  | 1 |
| cancelled_reason | Long Text |  |  | 1 |
| rework_by | Link | User |  | 1 |
| rework_on | Datetime |  |  | 1 |
| rework_reason | Long Text |  |  | 1 |
| acceptance_method | Data |  |  | 1 |
| target_closure | Datetime |  |  |  |
| team_policy | Select | Managed<br>Legacy | 0 | 1 |
| responsible_team | Link | TruCMMS Maintenance Team | 0 |  |
| required_discipline | Link | TruCMMS Discipline | 0 |  |
| team_assignment | Link | TruCMMS Team Assignment | 0 | 1 |
| lifecycle_policy | Select | <br>C1<br>Legacy |  | 1 |
| acceptance_policy_snapshot | Data |  |  | 1 |
| acceptance_required | Check |  |  | 1 |
| acceptance_user | Link | User |  |  |
| scheduled_start | Datetime |  |  |  |
| scheduled_end | Datetime |  |  |  |
| direct_key | Data |  |  | 1 |
| direct_payload_hash | Data |  |  | 1 |
| direct_reason | Small Text |  |  | 1 |
| has_review_history | Check |  |  | 1 |
| hold_from_state | Data |  |  | 1 |
| verified_by | Link | User |  | 1 |
| verified_on | Datetime |  |  | 1 |
| verified_reason | Small Text |  |  | 1 |
| held_by | Link | User |  | 1 |
| held_on | Datetime |  |  | 1 |
| held_reason | Small Text |  |  | 1 |
| resumed_by | Link | User |  | 1 |
| resumed_on | Datetime |  |  | 1 |
| resumed_reason | Small Text |  |  | 1 |
| reopened_by | Link | User |  | 1 |
| reopened_on | Datetime |  |  | 1 |
| reopened_reason | Small Text |  |  | 1 |
| equipment_snapshot | JSON |  |  | 1 |
| pm_section | Section Break |  |  |  |
| pm_plan | Link | TruCMMS PM Plan |  | 1 |
| pm_occurrence | Link | TruCMMS PM Occurrence |  | 1 |
| pm_finding | Link | TruCMMS Inspection Finding |  | 1 |
| pm_procedure_snapshot | Code | JSON |  | 1 |
| pm_started_on | Datetime |  |  | 1 |
| pm_started_by | Link | User |  | 1 |
| scope_section | Section Break |  |  |  |
| scope_policy | Data |  |  | 1 |
| scope_location | Link | VB Equipment Location |  | 1 |
| scope_revision | Link | TruCMMS Scope Revision |  | 1 |
| work_targets | Table | TruCMMS Work Target |  | 1 |
| scope_snapshot | Long Text |  |  | 1 |

Roles definidos: TruCMMS Dispatcher: read, create, write, report; TruCMMS Supervisor: read, create, write, report; TruCMMS Technician: read, report; System Manager: read, create, write, delete, report, export, share; TruCMMS Requester: read, report. Los hooks pueden restringir más estos permisos.

## TruCMMS Material Acknowledgment

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| stock_entry | Link | Stock Entry | 1 | 1 |
| work_order | Link | TruCMMS Maintenance Work Order | 1 | 1 |
| company | Link | Company | 1 | 1 |
| site | Link | TruCMMS Site | 1 | 1 |
| received_by | Link | User | 1 | 1 |
| received_on | Datetime |  | 1 | 1 |
| reason | Small Text |  | 1 | 1 |
| items_snapshot | Long Text |  | 1 | 1 |

Roles definidos: System Manager: read, select, print; TruCMMS Supervisor: read, select, print; TruCMMS Dispatcher: read, select, print; TruCMMS Technician: read, select, print. Los hooks pueden restringir más estos permisos.

## TruCMMS Material Estimate

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| work_order | Link | TruCMMS Maintenance Work Order | 1 | 0 |
| company | Link | Company | 0 | 1 |
| site | Link | TruCMMS Site | 0 | 1 |
| item | Link | Item | 1 | 0 |
| stock_uom | Link | UOM | 0 | 1 |
| quantity | Float |  | 1 | 0 |
| needed_on | Date |  | 1 | 0 |
| disabled | Check |  | 0 | 0 |
| reason | Small Text |  | 1 | 0 |

Roles definidos: System Manager: read, select, create, write; TruCMMS Supervisor: read, select, create, write; TruCMMS Dispatcher: read, select, create, write. Los hooks pueden restringir más estos permisos.

## TruCMMS Material Source

Tipo: tabla hija. Identidad: `nativa`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| source_key | Data |  |  |  |
| active_key | Data |  |  |  |
| occurrence | Link | TruCMMS PM Occurrence |  |  |
| item | Link | Item |  |  |
| stock_uom | Link | UOM |  |  |
| quantity | Float |  |  |  |
| needed_on | Date |  |  |  |
| estimate | Link | TruCMMS Material Estimate |  |  |

Roles definidos: . Los hooks pueden restringir más estos permisos.

## TruCMMS Measurement Point

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| code | Data |  | 1 |  |
| point_name | Data |  | 1 |  |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| functional_location | Link | VB Equipment Location | 1 |  |
| disabled | Check |  |  |  |

Roles definidos: System Manager: read, select, create, write; TruCMMS Supervisor: read, select, create, write; TruCMMS Dispatcher: read, select; TruCMMS Technician: read, select; VB Maintenance Manager: read, select, create, write; VB Maintenance User: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Meter

Tipo: documento. Identidad: `field:code`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| code | Data |  | 1 |  |
| meter_name | Data |  | 1 |  |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| equipment | Link | VB Equipment | 0 |  |
| component | Link | TruCMMS Component |  |  |
| unit | Link | UOM | 1 |  |
| metric_kind | Select | Cumulative<br>Condition<br>Rate | 1 |  |
| direction | Select | Increasing<br>Decreasing<br>Variable | 1 |  |
| max_age_hours | Float |  |  |  |
| disabled | Check |  |  |  |
| epoch | Int |  |  | 1 |
| epoch_offset | Float |  |  | 1 |
| last_reading | Link | TruCMMS Meter Reading |  | 1 |
| measurement_point | Link | TruCMMS Measurement Point |  | 0 |

Roles definidos: TruCMMS Dispatcher: read, select, report; TruCMMS Supervisor: read, select, create, write, report; TruCMMS Technician: read, select, report; System Manager: read, select, create, write, report; VB Maintenance Manager: read, select, create, write, report; VB Maintenance User: read, select, report. Los hooks pueden restringir más estos permisos.

## TruCMMS Meter Epoch

Tipo: documento. Identidad: `field:epoch_key`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| epoch_key | Data |  |  | 1 |
| meter | Link | TruCMMS Meter |  | 1 |
| company | Link | Company | 1 | 1 |
| site | Link | TruCMMS Site | 1 | 1 |
| old_epoch | Int |  |  | 1 |
| new_epoch | Int |  |  | 1 |
| initial_value | Float |  |  | 1 |
| continuity_offset | Float |  |  | 1 |
| effective_on | Datetime |  |  | 1 |
| reason | Small Text |  |  | 1 |
| recorded_by | Link | User |  | 1 |
| measurement_point | Link | TruCMMS Measurement Point |  | 1 |

Roles definidos: TruCMMS Dispatcher: read, select, report; TruCMMS Supervisor: read, select, report; TruCMMS Technician: read, select, report; System Manager: read, select, report; VB Maintenance Manager: read, select, report; VB Maintenance User: read, select, report. Los hooks pueden restringir más estos permisos.

## TruCMMS Meter Reading

Tipo: documento. Identidad: `field:reading_key`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| reading_key | Data |  |  | 1 |
| meter | Link | TruCMMS Meter |  | 1 |
| company | Link | Company | 1 | 1 |
| site | Link | TruCMMS Site | 1 | 1 |
| equipment | Link | VB Equipment | 0 | 1 |
| component | Link | TruCMMS Component |  | 1 |
| value | Float |  |  | 1 |
| total_value | Float |  |  | 1 |
| actual_on | Datetime |  |  | 1 |
| epoch | Int |  |  | 1 |
| correction_of | Link | TruCMMS Meter Reading |  | 1 |
| reason | Small Text |  |  | 1 |
| payload_hash | Data |  |  | 1 |
| recorded_by | Link | User |  | 1 |
| recorded_on | Datetime |  |  | 1 |
| measurement_point | Link | TruCMMS Measurement Point |  | 1 |

Roles definidos: TruCMMS Dispatcher: read, select, report; TruCMMS Supervisor: read, select, report; TruCMMS Technician: read, select, report; System Manager: read, select, report; VB Maintenance Manager: read, select, report; VB Maintenance User: read, select, report. Los hooks pueden restringir más estos permisos.

## TruCMMS PM Event

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| company | Link | Company | 1 | 1 |
| site | Link | TruCMMS Site | 1 | 1 |
| plan | Link | TruCMMS PM Plan |  | 1 |
| occurrence | Link | TruCMMS PM Occurrence |  | 1 |
| meter | Link | TruCMMS Meter |  | 1 |
| component | Link | TruCMMS Component |  | 1 |
| finding | Link | TruCMMS Inspection Finding |  | 1 |
| action | Data |  |  | 1 |
| reason | Small Text |  |  | 1 |
| actor | Link | User |  | 1 |
| recorded_on | Datetime |  |  | 1 |
| details | Code | JSON |  | 1 |

Roles definidos: TruCMMS Dispatcher: read, select, report; TruCMMS Supervisor: read, select, report; System Manager: read, select, report; VB Maintenance Manager: read, select, report. Los hooks pueden restringir más estos permisos.

## TruCMMS PM Measurement Result

Tipo: tabla hija. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| metric_key | Data |  | 1 |  |
| value | Data |  | 1 |  |
| metric_label | Data |  |  | 1 |
| unit | Data |  |  | 1 |
| meter_reading | Link | TruCMMS Meter Reading |  |  |
| out_of_range | Check |  |  | 1 |

Roles definidos: . Los hooks pueden restringir más estos permisos.

## TruCMMS PM Occurrence

Tipo: documento. Identidad: `field:occurrence_key`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| occurrence_key | Data |  |  | 1 |
| plan | Link | TruCMMS PM Plan |  | 1 |
| company | Link | Company | 1 | 1 |
| site | Link | TruCMMS Site | 1 | 1 |
| equipment | Link | VB Equipment |  | 1 |
| component | Link | TruCMMS Component |  | 1 |
| subject | Data |  |  | 1 |
| original_due | Date |  |  | 1 |
| planned_for | Date |  |  | 1 |
| status | Select | Planned<br>Released<br>Completed<br>Skipped<br>Cancelled |  | 1 |
| work_order | Link | TruCMMS Maintenance Work Order |  | 1 |
| trigger_reading | Link | TruCMMS Meter Reading |  | 1 |
| trigger_total | Float |  |  | 1 |
| source_key | Data |  |  | 1 |
| sequence | Int |  |  | 1 |
| procedure_snapshot | Code | JSON |  | 1 |
| last_reason | Small Text |  |  | 1 |
| baseline_before | Code | JSON |  | 1 |
| completed_actual_on | Datetime |  |  | 1 |
| completion_reading | Link | TruCMMS Meter Reading |  | 1 |
| recorded_on | Datetime |  |  | 1 |

Roles definidos: TruCMMS Dispatcher: read, select, report; TruCMMS Supervisor: read, select, report; TruCMMS Technician: read, select, report; System Manager: read, select, report. Los hooks pueden restringir más estos permisos.

## TruCMMS PM Plan

Tipo: documento. Identidad: `field:code`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| code | Data |  | 1 |  |
| plan_name | Data |  | 1 |  |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| equipment | Link | VB Equipment | 1 |  |
| component | Link | TruCMMS Component |  |  |
| procedure_revision | Link | TruCMMS Job Plan Revision | 1 |  |
| status | Select | Draft<br>Active<br>Paused<br>Retired |  | 1 |
| schedule_type | Select | Calendar<br>Meter | 1 |  |
| calendar_policy | Select | Fixed<br>After Completion |  |  |
| anchor_date | Date |  |  |  |
| end_date | Date |  |  |  |
| frequency | Select | Days<br>Weeks<br>Months |  |  |
| interval | Int |  |  |  |
| time_of_day | Time |  |  |  |
| duration_minutes | Int |  |  |  |
| horizon_days | Int |  |  |  |
| meter | Link | TruCMMS Meter |  |  |
| meter_metric_key | Data |  |  |  |
| trigger_kind | Select | Usage<br>Below<br>Above<br>Outside |  |  |
| usage_interval | Float |  |  |  |
| lower_threshold | Float |  |  |  |
| upper_threshold | Float |  |  |  |
| release_section | Section Break |  |  |  |
| release_mode | Select | Manual<br>Automatic |  |  |
| release_event | Select | Started<br>Verified<br>Closed |  |  |
| release_scope | Select | Plan<br>Equipment<br>Component<br>Group |  |  |
| include_corrective_work | Check |  |  |  |
| control_group | Data |  |  |  |
| max_active | Int |  |  |  |
| lead_days | Int |  |  |  |
| priority | Select | Low<br>Medium<br>High<br>Critical |  |  |
| responsible_team | Link | TruCMMS Maintenance Team |  |  |
| required_discipline | Link | TruCMMS Discipline |  |  |
| acceptance_user | Link | User |  |  |
| automation_enabled | Check |  |  |  |
| automation_user | Link | User |  |  |
| audit_section | Section Break |  |  |  |
| operating_timezone | Data |  |  | 1 |
| configuration_snapshot | Code | JSON |  | 1 |
| procedure_snapshot | Code | JSON |  | 1 |
| approved_by | Link | User |  | 1 |
| approved_on | Datetime |  |  | 1 |
| last_reason | Small Text |  |  | 1 |
| last_evaluated_on | Datetime |  |  | 1 |
| last_error | Small Text |  |  | 1 |
| baseline_reading | Link | TruCMMS Meter Reading |  | 1 |
| baseline_total | Float |  |  | 1 |
| next_trigger_total | Float |  |  | 1 |
| condition_latched | Check |  |  | 1 |
| trigger_sequence | Int |  |  | 1 |
| next_due_date | Date |  |  | 1 |
| next_due_key | Data |  |  | 1 |
| baseline_occurrence | Link | TruCMMS PM Occurrence |  | 1 |

Roles definidos: TruCMMS Dispatcher: read, select, create, write, report; TruCMMS Supervisor: read, select, create, write, report; TruCMMS Technician: read, select, report; System Manager: read, select, create, write, report. Los hooks pueden restringir más estos permisos.

## TruCMMS Resource Calendar

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| code | Data |  | 1 |  |
| calendar_name | Data |  | 1 |  |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| holiday_list | Link | Holiday List |  |  |
| dst_occurrence | Select | First<br>Second | 1 |  |
| slots | Table | TruCMMS Calendar Slot | 1 |  |
| disabled | Check |  |  |  |

Roles definidos: System Manager: read, select, create, write; TruCMMS Supervisor: read, select, create, write; TruCMMS Dispatcher: read, select; TruCMMS Technician: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Resource Window

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| technician | Link | User | 1 |  |
| kind | Select | Working<br>Unavailable | 1 |  |
| starts_on | Datetime |  | 1 |  |
| ends_on | Datetime |  | 1 |  |
| disabled | Check |  | 0 |  |
| reason | Small Text |  | 1 |  |
| calendar_assignment | Link | TruCMMS Calendar Assignment |  | 1 |
| calendar_generation | Link | TruCMMS Calendar Generation |  | 1 |
| calendar_key | Data |  |  | 1 |

Roles definidos: System Manager: read, select, create, write; TruCMMS Supervisor: read, select, create, write; TruCMMS Dispatcher: read, select; TruCMMS Technician: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Scope Revision

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| work_order | Link | TruCMMS Maintenance Work Order | 1 | 1 |
| company | Link | Company | 1 | 1 |
| site | Link | TruCMMS Site | 1 | 1 |
| request_key | Data |  |  |  |
| payload_hash | Data |  |  |  |
| snapshot | Long Text |  |  | 1 |
| reason | Small Text |  |  | 1 |
| recorded_by | Link | User |  | 1 |
| recorded_on | Datetime |  |  | 1 |

Roles definidos: System Manager: read, select; TruCMMS Supervisor: read, select; TruCMMS Dispatcher: read, select; TruCMMS Technician: read, select; TruCMMS Requester: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Site

Tipo: documento. Identidad: `field:site_code`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| site_code | Data |  | 1 |  |
| site_name | Data |  | 1 |  |
| company | Link | Company | 1 |  |
| disabled | Check |  |  |  |
| time_zone | Data |  | 0 |  |
| acceptance_policy | Select | By Origin<br>Required<br>Not Required |  |  |

Roles definidos: VB Maintenance User: read, select; VB Maintenance Manager: read, select; System Manager: read, select, create, write, delete, report, export, share, print; TruCMMS Requester: read, select; TruCMMS Dispatcher: read, select; TruCMMS Supervisor: read, select; TruCMMS Technician: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Site Warehouse

Tipo: documento. Identidad: `field:binding_key`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| binding_key | Data |  |  | 1 |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| warehouse | Link | Warehouse | 1 |  |
| disabled | Check |  |  |  |
| change_reason | Small Text |  | 1 |  |

Roles definidos: System Manager: read, select, create, write; TruCMMS Supervisor: read, select, create, write; TruCMMS Dispatcher: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Team Assignment

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| work_order | Link | TruCMMS Maintenance Work Order | 1 |  |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| team | Link | TruCMMS Maintenance Team | 1 |  |
| discipline | Link | TruCMMS Discipline | 1 |  |
| technician | Link | User | 1 |  |
| membership | Link | TruCMMS Team Membership | 1 |  |
| site_authorization | Link | TruCMMS Team Site Authorization | 1 |  |
| assigned_on | Datetime |  | 1 |  |
| assigned_by | Link | User | 1 |  |
| reason | Small Text |  | 1 |  |

Roles definidos: TruCMMS Dispatcher: read, report; TruCMMS Supervisor: read, report; TruCMMS Technician: read, report; System Manager: read, report; TruCMMS Requester: read, report. Los hooks pueden restringir más estos permisos.

## TruCMMS Team Discipline

Tipo: tabla hija. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| discipline | Link | TruCMMS Discipline | 1 |  |

Roles definidos: . Los hooks pueden restringir más estos permisos.

## TruCMMS Team Membership

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| team | Link | TruCMMS Maintenance Team | 1 |  |
| company | Link | Company | 0 | 1 |
| user | Link | User | 1 |  |
| discipline | Link | TruCMMS Discipline | 1 |  |
| function | Select | Technician<br>Lead | 1 |  |
| valid_from | Datetime |  | 1 |  |
| valid_until | Datetime |  | 0 |  |
| revoked | Check |  | 0 |  |
| revoked_on | Datetime |  | 0 | 1 |
| revoked_by | Link | User | 0 | 1 |

Roles definidos: System Manager: read, select, create, write; TruCMMS Supervisor: read, select, create, write; TruCMMS Dispatcher: read, select; TruCMMS Technician: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Team Site Authorization

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| team | Link | TruCMMS Maintenance Team | 1 |  |
| company | Link | Company | 0 | 1 |
| site | Link | TruCMMS Site | 1 |  |
| valid_from | Datetime |  | 1 |  |
| valid_until | Datetime |  | 0 |  |
| revoked | Check |  | 0 |  |
| revoked_on | Datetime |  | 0 | 1 |
| revoked_by | Link | User | 0 | 1 |

Roles definidos: System Manager: read, select, create, write; TruCMMS Supervisor: read, select, create, write; TruCMMS Dispatcher: read, select; TruCMMS Technician: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Work Allocation

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| work_order | Link | TruCMMS Maintenance Work Order | 1 |  |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| execution_cycle | Int |  | 1 |  |
| technician | Link | User | 1 |  |
| discipline | Link | TruCMMS Discipline | 1 |  |
| team | Link | TruCMMS Maintenance Team | 1 |  |
| assignment | Link | TruCMMS Team Assignment | 1 |  |
| assigned_on | Datetime |  | 1 |  |
| assigned_by | Link | User | 1 |  |
| ended_on | Datetime |  |  | 1 |
| ended_by | Link | User |  | 1 |
| reason | Small Text |  | 1 |  |

Roles definidos: TruCMMS Dispatcher: read, select; TruCMMS Supervisor: read, select; TruCMMS Technician: read, select; System Manager: read, select; TruCMMS Requester: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Work Cycle

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| work_order | Link | TruCMMS Maintenance Work Order | 1 |  |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| execution_cycle | Int |  | 1 |  |
| snapshot | Code | JSON | 1 |  |
| ended_action | Data |  | 1 |  |
| recorded_on | Datetime |  | 1 |  |
| recorded_by | Link | User | 1 |  |

Roles definidos: TruCMMS Dispatcher: read, select; TruCMMS Supervisor: read, select; TruCMMS Technician: read, select; System Manager: read, select; TruCMMS Requester: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Work Event

Tipo: documento. Identidad: `format:EVT-{YYYY}-{#####}`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| work_order | Link | TruCMMS Maintenance Work Order | 1 |  |
| company | Link | Company |  | 1 |
| site | Link | TruCMMS Site |  | 1 |
| action | Data |  |  | 1 |
| from_state | Data |  |  | 1 |
| to_state | Data |  |  | 1 |
| actor | Link | User |  | 1 |
| occurred_on | Datetime |  |  | 1 |
| reason | Long Text |  |  | 1 |
| execution_cycle | Int |  |  | 1 |
| before_snapshot | Code | JSON |  | 1 |

Roles definidos: TruCMMS Requester: read; TruCMMS Dispatcher: read; TruCMMS Supervisor: read; TruCMMS Technician: read; System Manager: read. Los hooks pueden restringir más estos permisos.

## TruCMMS Work Execution

Tipo: documento. Identidad: `format:EXE-{YYYY}-{#####}`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| work_order | Link | TruCMMS Maintenance Work Order | 1 |  |
| company | Link | Company | 1 | 1 |
| site | Link | TruCMMS Site | 1 | 1 |
| technician | Link | User |  | 1 |
| recorded_on | Datetime |  |  | 1 |
| actual_start | Datetime |  | 1 |  |
| actual_end | Datetime |  | 1 |  |
| actual_minutes | Float |  |  | 1 |
| findings | Long Text |  | 1 |  |
| tasks | Table | TruCMMS Execution Task | 1 |  |
| execution_cycle | Int |  |  | 1 |
| allocation | Link | TruCMMS Work Allocation |  | 1 |
| discipline | Link | TruCMMS Discipline |  | 1 |
| team | Link | TruCMMS Maintenance Team |  | 1 |
| submission_key | Data |  |  | 1 |
| submission_digest | Data |  |  | 1 |
| pm_measurements | Table | TruCMMS PM Measurement Result |  |  |

Roles definidos: TruCMMS Technician: read, create, write; TruCMMS Supervisor: read; TruCMMS Dispatcher: read; System Manager: read, report, export; TruCMMS Requester: read. Los hooks pueden restringir más estos permisos.

## TruCMMS Work Reading

Tipo: documento. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| work_order | Link | TruCMMS Maintenance Work Order | 1 | 1 |
| company | Link | Company | 1 | 1 |
| site | Link | TruCMMS Site | 1 | 1 |
| target_id | Data |  |  | 1 |
| meter | Link | TruCMMS Meter |  | 1 |
| meter_reading | Link | TruCMMS Meter Reading |  | 1 |
| recorded_by | Link | User |  | 1 |
| recorded_on | Datetime |  |  | 1 |

Roles definidos: System Manager: read, select; TruCMMS Supervisor: read, select; TruCMMS Dispatcher: read, select; TruCMMS Technician: read, select; TruCMMS Requester: read, select. Los hooks pueden restringir más estos permisos.

## TruCMMS Work Target

Tipo: tabla hija. Identidad: `hash`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| target_id | Data |  |  | 1 |
| kind | Select | Equipment<br>Component<br>Location<br>Measurement Point<br>Reference |  |  |
| label | Data |  |  |  |
| functional_location | Link | VB Equipment Location |  |  |
| equipment | Link | VB Equipment |  |  |
| component | Link | TruCMMS Component |  |  |
| measurement_point | Link | TruCMMS Measurement Point |  |  |
| context_snapshot | Long Text |  |  |  |

Roles definidos: . Los hooks pueden restringir más estos permisos.

## VB Equipment

Tipo: documento. Identidad: `field:equipment_code`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| equipment_code | Data |  | 1 |  |
| equipment_name | Data |  | 1 |  |
| status | Select | Planned<br>Active<br>Under Maintenance<br>Out of Service<br>Retired | 1 |  |
| category | Link | VB Equipment Category | 1 |  |
| location | Link | VB Equipment Location |  |  |
| manufacturer | Data |  |  |  |
| model | Data |  |  |  |
| serial_number | Data |  |  |  |
| acquisition_date | Date |  |  |  |
| commissioning_date | Date |  |  |  |
| notes | Small Text |  |  |  |
| asset_tag | Data |  |  |  |
| tag_key | Data |  |  | 1 |
| placement_policy | Select | <br>D1<br>Legacy |  | 1 |
| technical_profile | Link | TruCMMS Equipment Profile |  |  |
| profile_snapshot | JSON |  |  | 1 |
| attributes | Table | TruCMMS Attribute Value |  |  |
| criticality | Link | TruCMMS Criticality |  |  |
| criticality_snapshot | JSON |  |  | 1 |

Roles definidos: VB Maintenance User: read, report; VB Maintenance Manager: read, create, write, report; System Manager: read, create, write, delete, report, export, share, print; TruCMMS Requester: read, select, report; TruCMMS Dispatcher: read, select, report; TruCMMS Supervisor: read, select, report; TruCMMS Technician: read, select, report. Los hooks pueden restringir más estos permisos.

## VB Equipment Category

Tipo: documento. Identidad: `format:{category_name}`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| category_name | Data |  | 1 |  |
| disabled | Check |  | 1 |  |

Roles definidos: VB Maintenance User: read, report; VB Maintenance Manager: read, create, write, report; System Manager: read, create, write, delete, report, export, share, print. Los hooks pueden restringir más estos permisos.

## VB Equipment Location

Tipo: documento. Identidad: `format:{location_name}`.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| company | Link | Company | 1 |  |
| site | Link | TruCMMS Site | 1 |  |
| location_name | Data |  | 1 |  |
| disabled | Check |  | 1 |  |
| parent_location | Link | VB Equipment Location |  |  |
| single_equipment | Check |  |  |  |

Roles definidos: VB Maintenance User: read, report; VB Maintenance Manager: read, create, write, report; System Manager: read, create, write, delete, report, export, share, print; TruCMMS Requester: read, select; TruCMMS Dispatcher: read, select; TruCMMS Supervisor: read, select; TruCMMS Technician: read, select. Los hooks pueden restringir más estos permisos.

## Ampliación ENT-002 — TruCMMS Location Event

Se agrega un documento: inventario de ENT-002, 54 DocTypes antes de ENT-003. Identidad `hash`, sin renombrado; historial creado exclusivamente por servicio/controlador. Lectura por rol y Company/Site, sin escritura, eliminacion, importacion, exportacion o share ordinarios.

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| location | Link | VB Equipment Location | 1 | 1 |
| company | Link | Company | 1 | 1 |
| site | Link | TruCMMS Site | 1 | 1 |
| action | Data |  | 1 | 1 |
| reason | Small Text |  | 1 | 1 |
| effective_on | Datetime |  | 1 | 1 |
| recorded_by | Link | User | 1 | 1 |
| before_snapshot | JSON |  | 1 | 1 |
| after_snapshot | JSON |  | 1 | 1 |

## ENT-003 — TruCMMS Operating Unit

Identidad hash, sin renombrado. Datos y acceso según [contrato ENT-003](../10-organizacion-operativa-ENT003.md).

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| company | Link | Company | 1 | 0 |
| unit_code | Data |  | 1 | 0 |
| unit_name | Data |  | 1 | 0 |
| unit_type | Data |  | 0 | 0 |
| parent_unit | Link | TruCMMS Operating Unit | 0 | 0 |
| disabled | Check |  | 0 | 0 |

## ENT-003 — TruCMMS Organization Event

Identidad hash, sin renombrado. Datos y acceso según [contrato ENT-003](../10-organizacion-operativa-ENT003.md).

| Campo | Tipo | Opciones | Obligatorio | Solo lectura |
| --- | --- | --- | --- | --- |
| company | Link | Company | 1 | 1 |
| operating_unit | Link | TruCMMS Operating Unit | 0 | 1 |
| site | Link | TruCMMS Site | 0 | 1 |
| action | Data |  | 1 | 1 |
| reason | Small Text |  | 1 | 1 |
| effective_on | Datetime |  | 1 | 1 |
| recorded_by | Link | User | 1 | 1 |
| before_snapshot | JSON |  | 1 | 1 |
| after_snapshot | JSON |  | 1 | 1 |

Campo adicional ENT-003 en TruCMMS Site: `operating_unit`, Link opcional a TruCMMS Operating Unit. La Company y el código del sitio no cambian; la asignación existente pasa por el servicio controlado. Inventario total: 56 DocTypes propios.
