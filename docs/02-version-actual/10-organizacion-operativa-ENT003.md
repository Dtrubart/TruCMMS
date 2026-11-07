# ENT-003 — organización operativa opcional

Fecha de entrega: 2026-11-06. [Contrato autorizado](../01-plan-desarrollo/09-organizacion-operativa-ENT003.md). Incremento sobre ENT-002; aceptación humana separada.

## Uso

Acceso: **TruCMMS → Configuración → Estructura operativa**, ruta `/desk/trucmms-organization`. Seleccionar Company para explorar o buscar unidades. El administrador crea unidades raíz/hijas con código, nombre y tipo opcional; no existen niveles geográficos obligatorios.

En **TruCMMS Site**, el administrador usa «Asignar unidad operativa», elige unidad o deja vacío para desvincular, escribe motivo, revisa la vista previa y confirma. «Historial de agrupación» abre los eventos de esa sede. Los formularios con cambios sin guardar deben guardarse o descartarse antes de iniciar la acción.

La pertenencia es opcional y primaria. Las sedes existentes siguen sin agrupación; no se crearon regiones ni se asignó automáticamente VanBags/North Vancouver S1. No se crean sedes, almacenes, equipos, personal o permisos por mover una unidad.

## Reglas

Company y código de unidad son permanentes; nombre/tipo pueden editarse conservando identidad. No se permite renombrar el identificador ni forzar su cambio por el flujo nativo. Un padre pertenece a la misma Company; ciclos y exceso de profundidad se rechazan.

Cambiar padre o estado exige vista previa con unidades/sedes afectadas y motivo. Si la estructura, etiquetas o pertenencias relevantes cambian entre vista previa y confirmación, se exige una nueva. Operaciones serializadas por Company; los conflictos transaccionales pueden requerir reintento.

Desactivar exige resolver hijos activos y desvincular sedes, incluidas las archivadas que sigan asociadas. Reactivar exige ascendientes activos. Una sede desactivada puede desvincularse, pero debe activarse para recibir una pertenencia nueva. No se borran unidades ni eventos por el flujo normal.

Los cambios tienen efecto inmediato con fecha del servidor, sin retroactividad ni programación futura. Las listas muestran organización actual. El historial conserva rutas y estados anteriores/posteriores; no se entrega todavía un reporte consolidado reconstruido «a fecha».

## Datos y acceso

Nuevos DocTypes: **TruCMMS Operating Unit** y **TruCMMS Organization Event**. Campo opcional nuevo: `TruCMMS Site.operating_unit`. Inventario: 56 DocTypes propios y 77 servicios publicados.

System Manager/Administrator configura, respetando permisos nativos de Company/documento. Los roles CMMS consultan únicamente unidades ascendientes de sus sedes autorizadas y sedes directamente vinculadas que ya puedan leer. No se generan User Permissions ni concesiones de acceso regional. Compartir no amplía visibilidad.

El historial administrativo global es solo para administrador porque sus snapshots pueden contener otras sedes. Eventos creados por servidor, inmutables y no compartibles. La búsqueda de títulos nativa se adapta para Operating Unit y Site: exige permiso de lectura del registro antes de devolver su etiqueta; los demás DocTypes conservan el comportamiento nativo.

## Verificación

| Comprobación | Evidencia |
| --- | --- |
| Preservación de migración DEV | 57 tablas comparadas, 46 filas de referencia, sin cambios en registros/grants/ledger existentes |
| Preservación de migración TEST | 57 tablas comparadas, 710 filas de referencia, sin cambios; ningún agrupamiento automático |
| Regresión local | 485 pruebas, 605,552 s, OK, antes del último control de títulos/renombrado |
| Bloque dirigido final | 20 pruebas, 7,264 s, OK; lectura por sede, revocación, títulos, cruces, identidad, historia, obsolescencia, profundidad y paginación |
| Concurrencia | Dos conexiones por caso: un reparentado y una pertenencia ganadores; competidores rechazados, sin ciclo y un solo evento de pertenencia |
| Interfaz | Árbol real con administrador/lector, vista previa y confirmación en sede, rama/sede ajena oculta, APIs de detalle/título ajenos rechazadas, móvil 390 px; sin errores JS observados |
| Respaldo previo | DEV/TEST con base, configuración y adjuntos públicos/privados |
| Recuperación poblada | restore-ent003: 59 tablas, 1.421 filas y 717 archivos coincidentes; pertenencia/rutas restauradas, historia inmutable y scheduler pausado |
| CI de instalación limpia | Pendiente de registrar para el candidato final |

La suite local de 485 y el bloque final de 20 no se suman como pruebas distintas. El candidato final contiene 486 casos backend. No se repite la suite completa local por cambios acotados verificados de nuevo en el bloque dirigido; la CI del candidato final verificará el conjunto completo.

Los ensayos visuales y de concurrencia usan identidades sintéticas en TEST, retiradas después de cada ensayo; no modifican sedes operativas existentes. Los eventos de autenticación nativos pueden registrar actividad del usuario sintético.

Helpers locales en `D:/Projects/VanBags-ERP/docker/development/`: `ent003-preserve.py`, `ent003-concurrency-check.py`, `ent003-ui-fixture.py`, `verify-ent003-ui.mjs`, `ent003-recovery-check.py`. Evidencia visual saneada: `D:/Projects/VanBags-ERP/logs/ent003-ui-results.json`. Los manifiestos/respaldo con configuración permanecen privados en el workspace Linux.

## Límites y pendientes

64 niveles, 5.000 unidades por Company, páginas de 50 y máximo 10.000 sedes afectadas por cambio estructural. La proyección de lectura admite hasta 10.000 sedes autorizadas vinculadas por usuario; no hay caché global de visibilidad. Los límites son conservadores, sin certificación de escala empresarial.

No incluye concesiones regionales, filtros globales persistentes, agregados regionales completos, relaciones genéricas de equipos ni reportes generales «a fecha». ENT-004/005 y la aceptación humana siguen pendientes. Predicción R5 y offline R6 permanecen separados.

## Identidad y evidencia de despliegue

DEV/TEST: política `R4.1-operating-units`, huella `947759a23eff5a8cd3c52e30f8f0698d2e29deb49880d7e9f1b03669b4caeeba`. Paquete: 306 archivos propios. Índice único Company/código comprobado, pertenencia opcional y fixtures sintéticos retirados de ambos entornos. Se mantiene selección de sitio por hostname (`default_site` vacío).

La recuperación se comparó con un manifiesto previo al respaldo; solo Deployment por sitio y los IDs/timestamps regenerables de filas Has Role se excluyen de la comparación física. Las concesiones efectivas de rol sí se compararon. La configuración y respaldos permanecen privados. Evidencias saneadas en `D:/Projects/VanBags-ERP/logs/`: `ent003-final-result.json`, `ent003-recovery-result.json`, `ent003-concurrency-result.json`, `ent003-ui-results.json`.

Pruebas visuales reproducibles: [fixture](../../scripts/ent003-ui-fixture.py), [ensayo](../../scripts/verify-ent003-ui.mjs) e [instrucciones](../../scripts/README.md). El workflow remoto no ejecuta Playwright; la comprobación visual se hizo localmente.
