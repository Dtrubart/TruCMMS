# R4.1 — calendarios semanales, primera entrega

Actualización: 2026-11-03. Revisión de aplicación: `fbca17e584159990bd16a2853228242b2f2454fa`. Política DEV/TEST: `R4.1-resource-calendars`. Huella común: `26ea8177c4070cb7427149d5cb65e8cb6efd4ef879849e6b6e48b18a548dd6a7`.

## Implementado

Calendario semanal de Company/sede con turnos partidos o nocturnos; asignaciones por técnico y vigencia; generación controlada en ventanas existentes de disponibilidad. Cada asignación conserva el patrón y cada generación su periodo, feriados, autor y resultado. Un día generado sin turnos cuenta como cero horas; un día aún sin configuración mantiene «Sin configurar».

Feriados nativos opcionales sujetos a permisos ERPNext; cambios posteriores afectan periodos nuevos. Las ausencias existentes descuentan horas. Las ventanas generadas mantienen fechas/origen inmutables y admiten deshabilitación con nuevo motivo para gestionar excepciones. La asignación deshabilitada detiene generaciones futuras sin eliminar ventanas previas. Reintentos no duplican; periodos parcialmente solapados se rechazan. El cálculo sigue siendo orientativo y no concede elegibilidad de asignación.

Acceso: **TruCMMS → Recursos y servicios → Calendarios semanales / Calendarios por técnico**. Desde una asignación guardada: Generar disponibilidad, Ventanas de esta asignación e Historial de generación.

El [contrato técnico](../R4-RESOURCE-CALENDARS.md) precisa límites de 31 días por generación, vigencias, permisos y tratamiento horario.

## Verificación

- 16 pruebas nuevas aprobadas por grupos: patrón compartido, turnos partidos/nocturnos, feriados y cambios futuros, cero horas, ausencia, reintentos/solapes, permisos nativos, procedencia, excepciones y DST.
- 11 pruebas existentes de capacidad aprobadas en 11.925 s. Las repeticiones específicas tras ajustes no se suman como pruebas únicas.
- Formularios de escritorio/móvil, turno nocturno, navegación y ocultación de datos internos comprobados en Edge; no se guardaron calendarios operativos.
- Respaldos completos DEV/TEST y fuente anterior conservados antes de migrar. DEV mantiene cero datos operativos. En TEST, 509 de los 514 documentos iniciales permanecen idénticos; cuatro órdenes tuvieron transiciones concurrentes corroboradas por Version nativo y un plan solo adelantó su marca de evaluación. Se conservaron los contextos, ocho adjuntos y conteos nativos; hay tres documentos adicionales de actividad concurrente. No se atribuye al despliegue ni se revierte esa actividad.
- CI de la revisión exacta: [450 pruebas aprobadas en 278.874 s](https://github.com/Dtrubart/TruCMMS/actions/runs/41579331440), incluida instalación limpia. La corrida anterior tuvo una discrepancia en la lista esperada de menús; se actualizaron los dos accesos nuevos y pasaron las tres pruebas de navegación locales antes del CI final.

## Concurrencia y recuperación

En el clon aislado se probaron tres carreras con conexiones independientes: mismo periodo (una generación y reintento con la misma identidad), periodos parcialmente solapados (solo uno admitido) y dos sedes prometiendo al mismo técnico el mismo horario (solo una admitida, sin revelar identificadores ajenos). Hubo dos reintentos transitorios en total; no se promete éxito simultáneo sin reintento.

El candidato contiene dos calendarios, tres asignaciones, tres generaciones y seis ventanas generadas, además de un reemplazo explícito y una ausencia. La capacidad resultante es de seis horas el lunes y cero horas configuradas en los otros seis días consultados.

Su respaldo completo se restauró y migró en `restore-r4-calendars.vanbags.localhost`: coincidencia exacta de **559 documentos CMMS**, documentos nativos incluidos en la referencia, nueve adjuntos por hash, roles, User Permissions y configuración efectiva de cifrado. Se conservaron los patrones, generaciones, excepción/reemplazo/ausencia y el mismo reporte de capacidad. El reintento posterior devolvió la generación existente; el técnico conserva acceso solo a sus asignaciones/historial, otro técnico no obtiene registros y el historial rechaza modificaciones incluso de Administrator. La comparación final siguió coincidiendo tras esas comprobaciones.

La carga y restauración se hicieron exclusivamente en clones con scheduler pausado; DEV/TEST no fueron reemplazados ni recibieron calendarios de estas pruebas. No se cambiaron credenciales compartidas. La evidencia pertenece a los calendarios nuevos; no se reutiliza la recuperación R4.0 como sustituto.

Procedimiento local: `docker/development/r4-calendar-recovery.py`. Artefactos privados fuera de Git: `/workspace/r4-calendar-race-fixture.json`, `/workspace/r4-calendar-races`, `/workspace/r4-calendar-candidate-evidence.json`, `/workspace/snapshots/r4-calendar-candidate` y `/workspace/r4-calendar-recovery-result.json`. Las referencias técnicas de publicación incluyen 53 DocTypes y 66 servicios de la revisión aprobada en CI.

Aceptación operativa y producción continúan separadas.

Patrones rotativos multisemana, reemplazo masivo de ventanas futuras, nómina y optimización automática no forman parte de esta entrega. La revisión del prototipo de órdenes R4.7 sigue siendo independiente.
