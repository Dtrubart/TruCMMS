# Versión y alcance implementado

| Elemento | Valor |
| --- | --- |
| Producto/app | TruCMMS / `vanbags_maintenance` |
| Revisión verificada | `2c5f9ee59b25bbe5a820869c530e3165cd0c49ba` |
| Política de despliegue | `R4.1-capacity` |
| Rama de publicación | `codex/foundation-verification` |
| Base técnica comprobada | Frappe 16.28.0, ERPNext 16.29.0, Python 3.14.7, Node 24.21.0 |
| Entornos | DEV/TEST; no producción |
| CI | 418 pruebas aprobadas |

## Inventario funcional

| Área | Implementado |
| --- | --- |
| Fundamentos | Instalación/migraciones, permisos, CI y recuperación por candidato |
| Organización | Company nativo, sedes y ubicaciones; equipos, disciplinas, membresías y autorizaciones con vigencias |
| Activos | Identidad/tag, perfiles técnicos/criticidad, instalación/reemplazo efectivo e historial; independencia de Asset contable |
| Solicitudes | Reporte, envío, clasificación, aprobación/rechazo y evidencia privada |
| Órdenes | Origen solicitud/directo/preventivo/inspección, autorización, asignaciones, programación y cambios auditados |
| Ejecución/cierre | Tareas, hallazgos, tiempos/evidencias; terminación técnica, verificación independiente, aceptación por sede, retrabajo, pausa, cancelación y reapertura |
| Vistas/reportes | Lista, Mi trabajo, agenda/calendario, historial y reportes conciliados; navegación por tareas |
| Preventivo | Procedimientos versionados, calendario, ocurrencias futuras, liberación controlada/excepciones y cumplimiento |
| Medidores | Equipo/componente instalado; acumulativos/condición/tasa, unidades, cronología, correcciones, reinicios/épocas y disparadores |
| Componentes/inspecciones | Identidades/instalaciones históricas, hallazgos numéricos, revisión y trabajo de seguimiento |
| Logística | Catálogo/almacenes por sede, proyección, estimaciones, requerimientos nativos, CSV y stock orientativo |
| Entrega/costos | Salida/recogida/constancia, devoluciones parciales/lote/serie y conciliación de inventario, servicios y Timesheet |
| Capacidad inicial | Ventanas explícitas por persona/sede, ausencias, carga diaria y conflictos; turnos nocturnos/zona horaria |

## Límites de la versión

La orden conserva el modelo anterior de equipo principal o ubicación. No ofrece la nueva lista de múltiples puntos ni exige la nueva ubicación de alcance para toda orden. Los medidores operativos requieren equipo/componente; los puntos independientes de instalaciones están en R4.0 en desarrollo.

No están entregados el nuevo layout, constructor general de formatos, calificaciones/certificados, optimización asistida, coordinación avanzada ni gobierno documental R4. La capacidad no tiene patrones recurrentes/generación masiva. Predicción R5 y offline R6 son futuros.

R1–R3 tienen cierres técnicos para sus alcances. R4 no está cerrado; aceptación humana y producción siguen pendientes.
