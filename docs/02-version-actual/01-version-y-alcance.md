# Versión y alcance implementado

| Elemento | Valor |
| --- | --- |
| Producto/app | TruCMMS / `vanbags_maintenance` |
| Revisión verificada | `60cd0649700edf6c9b924fd7b9c4a76585b34d6f` |
| Política de despliegue | `R4.1-operating-units` |
| Rama de publicación | `codex/foundation-verification` |
| Base técnica comprobada | Frappe 16.28.0, ERPNext 16.29.0, Python 3.14.7, Node 24.21.0 |
| Entornos | DEV/TEST; no producción |
| CI | [486 pruebas aprobadas; 262,084 s](https://github.com/Dtrubart/TruCMMS/actions/runs/42341253571) |

## Inventario funcional

| Área | Implementado |
| --- | --- |
| Fundamentos | Instalación/migraciones, permisos, CI y recuperación por candidato |
| Organización | Company nativo, sedes y ubicaciones; equipos, disciplinas, membresías y autorizaciones con vigencias |
| Activos | Identidad/tag, perfiles técnicos/criticidad, instalación/reemplazo efectivo e historial; independencia de Asset contable |
| Solicitudes | Reporte, envío, clasificación, aprobación/rechazo y evidencia privada |
| Órdenes | Origen solicitud/directo/preventivo/inspección, alcance por ubicación y múltiples puntos, autorización, asignaciones, programación y cambios auditados |
| Ejecución/cierre | Tareas, hallazgos, tiempos/evidencias; terminación técnica, verificación independiente, aceptación por sede, retrabajo, pausa, cancelación y reapertura |
| Vistas/reportes | Lista, Mi trabajo, agenda/calendario, historial y reportes conciliados; navegación por tareas |
| Preventivo | Procedimientos versionados, calendario, ocurrencias futuras, liberación controlada/excepciones y cumplimiento |
| Medidores | Equipo/componente instalado o punto estable de instalaciones; acumulativos/condición/tasa, unidades, cronología, correcciones, reinicios/épocas y disparadores; captura vinculada a orden/punto |
| Componentes/inspecciones | Identidades/instalaciones históricas, hallazgos numéricos, revisión y trabajo de seguimiento |
| Logística | Catálogo/almacenes por sede, proyección, estimaciones, requerimientos nativos, CSV y stock orientativo |
| Entrega/costos | Salida/recogida/constancia, devoluciones parciales/lote/serie y conciliación de inventario, servicios y Timesheet |
| Capacidad y calendarios | Patrones semanales reutilizables, vigencias por técnico, generación controlada, feriados nativos y excepciones; carga diaria/conflictos, nocturnos y cambios horarios |

## Límites de la versión

Las órdenes nuevas requieren ubicación de alcance y puntos antes de autorizar. Las anteriores conservan su contrato histórico. El [detalle R4.0](06-r4-alcance-local.md) distingue funciones verificadas, preservación de datos y puertas pendientes de recuperación/aceptación. Un medidor de instalaciones no requiere activo ficticio. La captura por actividad configurable y los disparadores preventivos de instalaciones sin equipo no se certifican en este incremento.

No están entregados el nuevo layout, constructor general de formatos, calificaciones/certificados, optimización asistida, coordinación avanzada ni gobierno documental R4. Los calendarios tienen patrones semanales y generación manual de hasta 31 días; ciclos rotativos multisemana y reemplazo masivo de turnos quedan fuera de esta entrega. Predicción R5 y offline R6 son futuros.

R1–R3 tienen cierres técnicos para sus alcances. R4 no está cerrado; aceptación humana y producción siguen pendientes.

## Incremento local ENT-002 — 2026-11-05

Arbol funcional autorizado por sede, cambios de padre/estado con vista previa y eventos inmutables. Conserva IDs y Company/Site. Politica local `R4.1-location-hierarchy`; 54 DocTypes y 70 servicios publicados en el paquete. Incremento publicado en la rama de desarrollo sobre la base indicada arriba, con CI aprobada; ver [verificaciones y limites](09-jerarquia-funcional-ENT002.md).

## ENT-003 — organización opcional

Unidades operativas por Company y pertenencia primaria opcional de sedes, con administración controlada e historial. Lectores solo ven ramas de sedes autorizadas; no se conceden permisos regionales. 56 DocTypes propios, 77 servicios y 306 archivos de paquete. [Entrega y límites](10-organizacion-operativa-ENT003.md).
