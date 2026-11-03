# Versión y alcance implementado

| Elemento | Valor |
| --- | --- |
| Producto/app | TruCMMS / `vanbags_maintenance` |
| Revisión verificada | `edd2353b2fd6e53528393762ababee8a4bfb9ae3` |
| Política de despliegue | `R4.0-work-scope` |
| Rama de publicación | `codex/foundation-verification` |
| Base técnica comprobada | Frappe 16.28.0, ERPNext 16.29.0, Python 3.14.7, Node 24.21.0 |
| Entornos | DEV/TEST; no producción |
| CI | 434 pruebas aprobadas; 133,320 s |

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
| Capacidad inicial | Ventanas explícitas por persona/sede, ausencias, carga diaria y conflictos; turnos nocturnos/zona horaria |

## Límites de la versión

Las órdenes nuevas requieren ubicación de alcance y puntos antes de autorizar. Las anteriores conservan su contrato histórico. El [detalle R4.0](06-r4-alcance-local.md) distingue funciones verificadas, preservación de datos y puertas pendientes de recuperación/aceptación. Un medidor de instalaciones no requiere activo ficticio. La captura por actividad configurable y los disparadores preventivos de instalaciones sin equipo no se certifican en este incremento.

No están entregados el nuevo layout, constructor general de formatos, calificaciones/certificados, optimización asistida, coordinación avanzada ni gobierno documental R4. La capacidad no tiene patrones recurrentes/generación masiva. Predicción R5 y offline R6 son futuros.

R1–R3 tienen cierres técnicos para sus alcances. R4 no está cerrado; aceptación humana y producción siguen pendientes.
