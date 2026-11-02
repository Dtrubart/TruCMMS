# R1 — matriz de trazabilidad y aceptación

Fecha: 2026-10-26. La especificación original se usa como línea base propuesta. Esta matriz no sustituye la aceptación humana ni declara listo el entorno de desarrollo para producción. Los 24 escenarios tienen implementación y pruebas asociadas; sus resultados finales se vinculan al registro de publicación de la revisión candidata.

| ID | Escenario original | Evidencia automatizada | Aceptación humana |
|---|---|---|---|
| CH02-R1-T01 | Create equipment without a financial Asset | `test_manager_creates_valid_equipment` — `vanbags_maintenance/doctype/vb_equipment/test_vb_equipment.py` | Pendiente |
| CH02-R1-T02 | Replace equipment at a functional location | `test_replacement_is_atomic_and_keeps_two_identities` — `vanbags_maintenance/test_assets.py` | Pendiente |
| CH02-R1-T03 | Create maintenance request | `test_requester_sends_dispatcher_approves` — `vanbags_maintenance/test_requests.py` | Pendiente |
| CH02-R1-T04 | Approve and convert request | `test_conversion_is_idempotent_and_preserves_context` — `vanbags_maintenance/test_work_orders.py` | Pendiente |
| CH02-R1-T05 | Reject request | `test_rejection_requires_reason_and_preserves_decision` — `vanbags_maintenance/test_requests.py` | Pendiente |
| CH02-R1-T06 | Assign site-specific team | `test_assignment_records_immutable_eligibility_snapshot` — `vanbags_maintenance/test_teams.py` | Pendiente |
| CH02-R1-T07 | Assign shared team at authorized site | `test_shared_team_assigns_at_second_authorized_site` — `vanbags_maintenance/test_r1_acceptance.py` | Pendiente |
| CH02-R1-T08 | Assign team at unauthorized site | `test_person_scope_does_not_replace_missing_team_site_authorization` — `vanbags_maintenance/test_r1_acceptance.py` | Pendiente |
| CH02-R1-T09 | Assign two technical disciplines | `test_distinct_disciplines_are_preserved_on_execution` — `vanbags_maintenance/test_work_cycle.py` | Pendiente |
| CH02-R1-T10 | Technician records tasks and labor | `test_recording_stamps_identity_context_and_duration` — `vanbags_maintenance/test_execution.py` | Pendiente |
| CH02-R1-T11 | Technician attaches evidence | `test_private_evidence_is_append_only` — `vanbags_maintenance/test_execution.py` | Pendiente |
| CH02-R1-T12 | Supervisor verifies completion | `test_request_requires_verification_before_acceptance` — `vanbags_maintenance/test_work_cycle.py` | Pendiente |
| CH02-R1-T13 | Requester rejects completed work | `test_rework_archives_cycle_and_requires_new_execution` — `vanbags_maintenance/test_work_cycle.py` | Pendiente |
| CH02-R1-T14 | Requester accepts completed work | `test_request_requires_verification_before_acceptance` — `vanbags_maintenance/test_work_cycle.py` | Pendiente |
| CH02-R1-T15 | PM-like work without requester | `test_direct_creation_is_idempotent_and_rejects_key_reuse` — `vanbags_maintenance/test_work_cycle.py` | Pendiente |
| CH02-R1-T16 | Technician uses mobile browser | `test_same_submission_returns_original_and_preserves_one_execution` — `vanbags_maintenance/test_work_views.py` | Pendiente |
| CH02-R1-T17 | Technician opens My Work | `test_my_work_includes_secondary_and_revokes_removed_allocation` — `vanbags_maintenance/test_work_views.py` | Pendiente |
| CH02-R1-T18 | Supervisor opens Date Agenda | `test_calendar_and_agenda_share_rows_and_explicit_offsets` — `vanbags_maintenance/test_work_views.py` | Pendiente |
| CH02-R1-T19 | User opens Calendar | `test_end_at_midnight_does_not_occupy_next_day` — `vanbags_maintenance/test_work_views.py` | Pendiente |
| CH02-R1-T20 | Unauthorized API call | `test_unassigned_technician_and_forged_hidden_fields_are_rejected` — `vanbags_maintenance/test_work_views.py` | Pendiente |
| CH02-R1-T21 | Technician changes teams | `test_technician_changes_team_without_rewriting_prior_assignment` — `vanbags_maintenance/test_r1_acceptance.py` | Pendiente |
| CH02-R1-T22 | Equipment maintenance history report | `test_equipment_history_preserves_original_links` — `vanbags_maintenance/test_reporting.py` | Pendiente |
| CH02-R1-T23 | Work Order cancelled | `test_c1_cancellation_retains_execution_and_reason` — `vanbags_maintenance/test_work_cycle.py` | Pendiente |
| CH02-R1-T24 | Work Order reopened or reworked | `test_reopening_archives_closure_and_returns_authorized` — `vanbags_maintenance/test_work_cycle.py` | Pendiente |

## Evidencia complementaria

- Navegador móvil a 390×844: Mi trabajo del participante secundario, retención ante error, pérdida deliberada de respuesta exitosa, reintento que recupera la misma ejecución y carga privada denegada a Guest. Evidencia: `docker/development/verify-e-mobile.mjs`, captura `logs/e-mobile-execution.png` y manifiesto de demo E.
- Agenda/Calendario: permisos de seis perfiles, límites de fecha, intervalos nocturnos y fin exclusivo, reglas IANA 2026e, días históricos de 23/25 horas y Vancouver sin retroceso de reloj en noviembre de 2026. Referencia oficial: https://news.gov.bc.ca/releases/2026AG0013-000209.
- Actualización poblada D→E: 219 documentos y 383 archivos preservados. Recuperación de E: 412 archivos y comparación exacta de datos, asignaciones, ciclos, permisos y las cuatro vistas por rol.
- La prueba móvil automatizada no equivale al recorrido humano del negocio. Los ensayos de lectura local no certifican capacidad de producción.

## Disposiciones del alcance ampliado

1. Equipos humanos y elegibilidad por sede, disciplinas, verificación, origen directo, excepciones y programación están implementados. Sus invariantes de seguridad no son estados editables libremente.
2. Perfiles técnicos y criticidad, aceptación por sede, zona operativa y ocupación de ubicaciones son configurables. Prioridades y transiciones permanecen controladas; reglas arbitrarias de prioridades/SLA y editor de workflows requieren una entrega aprobada distinta.
3. PM-like sin solicitante se valida mediante origen directo autorizado. El motor preventivo, medidores y generación automática siguen en R2; T15 no declara que exista ese motor.
4. La demo cubre HVAC/contratistas, diez camiones, XRF y una línea de proceso. Calibración automática/certificación normativa, BOM de componentes, inventario/compras/costos y confiabilidad avanzada permanecen diferidos.
5. El paquete conserva su identidad técnica compatible. Fuente única de publicación, huella por sitio y actualización/restauración son puertas verificables; la identidad técnica no se renombra silenciosamente.

## Puertas de aceptación

- Técnica: instalación limpia, suite completa, actualización poblada, permisos/API/adjuntos, concurrencia, navegación por rol/móvil, comparación fuente-publicación y recuperación de candidato.
- Operativa: salud de servicios y colas, carga acotada de lectura, runbook y procedimiento de respaldo/recuperación. Scheduler, TLS, secretos, respaldo externo y alertas deben validarse en el destino productivo.
- Humana: el responsable revisa los escenarios con roles representativos y registra nombre, fecha, revisión y decisiones. No se completa automáticamente por ejecutar pruebas.
