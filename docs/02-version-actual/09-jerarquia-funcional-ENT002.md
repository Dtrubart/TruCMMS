# ENT-002 — árbol funcional e historial

Fecha: 2026-11-05. Desarrollo local autorizado mediante [ENT-001](../01-plan-desarrollo/08-jerarquia-y-contexto-ENT001.md). No sustituye la revisión publicada `fbca17e584159990bd16a2853228242b2f2454fa`; amplía esa base en el árbol de trabajo, sin commit/push todavía.

## Acceso

En Desk: **TruCMMS → Activos → Árbol de ubicaciones**. Ruta TEST: `http://test.vanbags.localhost:8100/desk/trucmms-locations`.

Seleccionar empresa/sede autorizadas; si solo hay una sede visible se preselecciona. Expandir el árbol o buscar por nombre. Elegir una ubicación muestra breadcrumb, estado, ficha e historial. La ficha nativa también incorpora «Árbol de ubicaciones» y conserva Company/Site/ubicación al regresar.

Los enlaces relacionados consultan ubicación exacta: equipos, puntos de medición, solicitudes y órdenes cuyo alcance es esa ubicación. No son agregados de descendientes ni una búsqueda de todos los puntos secundarios de una orden.

## Cambios controlados

Los usuarios con escritura nativa de ubicación pueden elegir **Cambiar jerarquía / estado**. El resto puede consultar según su ámbito.

1. Elegir Reparent, Deactivate o Reactivate. Padre vacío significa raíz de la misma sede.
2. Indicar motivo y solicitar vista previa.
3. Revisar rutas y cantidad de ubicaciones afectadas.
4. Confirmar. El servidor revalida permisos y estado; si cambió la estructura, pedir nueva vista previa.

No se permite cambiar padre/estado mediante guardado directo de la ficha. Los formularios con cambios sin guardar deben guardarse o descartarse antes de abrir esta acción. El nombre visible puede editarse manteniendo el ID.

El cambio tiene efecto inmediato; no acepta fecha retroactiva o futura. Reparentar no traslada equipos ni cambia Company/Site ni alcance congelado de órdenes. Los nodos se desactivan en lugar de eliminarse.

Para desactivar se exige resolver descendientes activos, equipos ubicados allí, puntos de medición activos y referencias de órdenes abiertas. Reactivar requiere ascendientes activos. Las ubicaciones antiguas ya desactivadas conservan lectura e interpretación histórica.

## Datos y permisos

Se conserva VB Equipment Location por adyacencia. Nuevo **TruCMMS Location Event**, de identidad hash, registra ubicación, Company/Site, acción, motivo, actor, fecha efectiva y snapshots anterior/posterior. Creación y cambio de etiqueta también generan eventos. Los eventos no se editan, eliminan ni comparten mediante el flujo normal.

La lectura sigue permisos nativos y frontera Company + Site, incluida lectura directa de eventos. Ningún permiso regional ni derecho financiero se añade por este bloque. Los eventos anteriores al despliegue no se reconstruyen: los documentos antiguos mantienen Version y los snapshots existentes; su siguiente movimiento conserva la estructura anterior afectada.

Mutaciones estructurales usan bloqueo de Company compartido con operaciones de instalación de equipos. Las consultas bloqueantes leen el estado actual. Un conflicto transaccional pide nueva vista previa/reintento; no se promete éxito simultáneo de cambios incompatibles.

## Verificación local

| Comprobación | Resultado |
| --- | --- |
| Regresión completa de la aplicación | 463 pruebas, 373,711 s, OK; incluye los primeros 13 casos de jerarquía |
| Bloque dirigido final | 16 pruebas, 5,524 s, OK; añade lectura directa de eventos, conservación de snapshot de orden autorizada y rechazo de nuevos nodos bajo ancestros antiguos desactivados, con ajuste final de conflictos |
| Dos conexiones independientes | Un cambio confirmado, el incompatible rechazado; ningún ciclo. Reintento del movimiento perdedor rechazado por ciclo |
| Navegador TEST | Árbol/contexto/breadcrumb, diálogo, ficha, búsqueda y móvil de 390 px; cero errores JavaScript observados; sin cambios operativos de la prueba UI |
| Respaldo previo | DEV y TEST, base/configuración/archivos públicos y privados, completados antes de la migración |
| Migración TEST | Completada, aditiva; IDs y estructura existente conservados |
| Recuperación poblada | Verificada en restore-ent002: 57 tablas / 1.404 filas comparadas y 700 hashes de archivos; jerarquía e historial inmutable recuperados; scheduler pausado |
| Migración DEV | Completada; página, nuevo DocType e índice comprobados en DEV/TEST |

La suite completa de 463 no se presenta como una ejecución de los 466 casos ahora presentes: los tres casos adicionales se verificaron en el bloque dirigido de 16. CI remota de este incremento y aceptación humana permanecen pendientes. La evidencia CI anterior de 450 pruebas conserva su alcance histórico.

Helpers reproducibles, fuera del paquete de la app: `D:/Projects/VanBags-ERP/docker/development/verify-ent002-ui.mjs`, `ent002-concurrency-check.py`, `ent002-recovery-check.py`. Evidencia UI: `D:/Projects/VanBags-ERP/logs/ent002-ui-results.json`, capturas desktop/mobile. Logs de integración en el contenedor: `/tmp/trucmms-ent002-regression.log` y `/tmp/trucmms-ent002-final-targeted.log`.

## Límites

- Páginas de 50 nodos/resultados; expansión progresiva. El historial de detalle muestra los últimos 20 eventos con enlace al listado completo.
- Operaciones estructurales: máximo 64 niveles y 5.000 ubicaciones por sede. No se truncan silenciosamente movimientos mayores ni se corrigen árboles antiguos automáticamente.
- Sin unidades regionales, permisos heredados, contexto global persistente, reconstrucción histórica «a fecha», árbol genérico de equipos, migración a Location nativo o NestedSet.
- La ubicación elegida conserva sus propios permisos. El árbol no cambia asignaciones, verificaciones, aceptación ni cierre de órdenes.
- No se acreditó escala empresarial, producción ni aceptación del usuario. Predicción sigue en R5; offline en R6.

## Recuperación operativa

Para actualizar otra instalación, respaldar base/configuración/adjuntos, sincronizar el paquete y ejecutar la migración del sitio explícito en un entorno de prueba. No usar `bench use` ni borrar volúmenes. Revertir código no elimina el nuevo historial: un rollback de datos requiere restaurar el respaldo coordinadamente y decidir el tratamiento de cambios posteriores. Mantener los sitios de recuperación aislados con scheduler pausado.

### Incidencias del ensayo de recuperación

La comparación inicial detectó IDs/timestamps de filas Has Role regeneradas durante migración y archivos extraídos bajo un prefijo `sites/test.vanbags.localhost/`. Se contrastaron las concesiones efectivas (parent/parenttype/parentfield/role) y se normalizó la ubicación de archivos dentro del sitio aislado, conservando la copia extraída y rechazando sobrescrituras diferentes. La comparación final es equivalencia con SOURCE tras migración, excluyendo las identidades sintéticas del ensayo y Deployment por sitio; las rutas anterior/posterior del movimiento sintético y su inmutabilidad se verificaron por separado. No se afirma igualdad de IDs de metadatos regenerables. Evidencia saneada: `D:/Projects/VanBags-ERP/logs/ent002-recovery-result.json`.

### Identidad final de entrega local

DEV/TEST: política `R4.1-location-hierarchy`; huella `c47efbfcd206e06207042b19201a77fa03ac62297d774ecfc8486c39fb1d12d6`. Publicación y fuente activa: 294 archivos de paquete coincidentes, 54 DocTypes y 70 servicios. `default_site` permanece vacío; fixtures sintéticos del ensayo eliminados de DEV/TEST. El sitio restore-ent002 se conserva aislado con scheduler pausado.

Evidencias saneadas: `D:/Projects/VanBags-ERP/logs/ent002-tests-result.json`, `ent002-ui-results.json`, `ent002-final-result.json` y `ent002-recovery-result.json`. No contienen credenciales ni configuración del sitio.
