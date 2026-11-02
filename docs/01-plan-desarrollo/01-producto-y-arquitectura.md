# Producto y arquitectura

**TruCMMS** es el producto y **VanBags** una empresa de ejemplo. La app técnica conserva `vanbags_maintenance` y ciertos DocTypes VB para preservar identidad y migraciones; la marca visible no implica renombrar tablas.

Se desarrolla en **Frappe**, requiere **ERPNext** y aparece dentro del escritorio como módulo propio, con formularios, roles y documentos nativos. No se plantea un inventario independiente ni una aplicación standalone que sustituya ERPNext.

## Núcleo reutilizable

Activos/componentes, ubicaciones, solicitudes, órdenes, ejecución, preventivos, medidores, materiales y costos forman un núcleo común. Flotas, manufactura, laboratorios y facilities se cubren con configuración y extensiones especializadas cuando sean necesarias.

Se reutilizan Company, User, Item, UOM, Warehouse, Material Request, Stock Entry, Purchase Invoice y Timesheet. ERPNext conserva inventario, valoración y contabilidad.

## Principios

- Empresa/sede delimitan acceso; pertenecer a un equipo no concede toda su visibilidad.
- Solicitud, obligación programada y orden abierta son entidades diferentes.
- Autorización, ejecución, verificación, aceptación y cierre mantienen responsabilidades y auditoría.
- Lecturas y eventos se corrigen mediante servicios controlados, conservando historia.
- Una nueva estructura requiere migración compatible; no se reinterpreta silenciosamente trabajo aprobado.
- La interfaz se organiza por tareas y rol; el servidor aplica la seguridad.

## Configurabilidad acordada

Plantillas guiadas para que el cliente adapte secciones, campos, unidades, tablas, obligatoriedad, condiciones sencillas, rangos, evidencias y revisores dentro de capacidades soportadas. Las actualizaciones no sobrescriben adaptaciones del cliente ni ejecuciones históricas.

Una plantilla no puede desactivar permisos, modificar contabilidad ni inventar transiciones centrales. Cálculos especializados, conexiones externas y nuevos procesos transaccionales requieren diseño propio. No buscamos un constructor universal de software.
