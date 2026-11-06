# Datos y permisos actuales

| Dominio | Entidades/fuentes de verdad |
| --- | --- |
| Organización | Company/User nativos, TruCMMS Site, VB Equipment Location |
| Activos | VB Equipment, categorías, perfiles/criticidad, eventos/instalaciones |
| Personas | Team, Discipline, Membership, Site Authorization y Assignment/Allocation por orden/ciclo |
| Trabajo | Request → Work Order; Work Target/Scope Revision; Execution, Event, Cycle y ajustes |
| Preventivo | Job Plan/Revision → PM Plan → Occurrence → orden; eventos/hallazgos |
| Medición | Meter → Reading/Epoch, con equipo/componente instalado o Measurement Point; Work Reading vincula lectura a orden/punto |
| Logística | Site Warehouse, Material Estimate, Material Request con fuentes de demanda |
| Movimiento | Stock Entry nativo y Material Acknowledgment inmutable |
| Costos | Libro de stock; líneas Purchase Invoice/Timesheet vinculadas a orden |
| Capacidad | Resource Calendar/Calendar Slot → Calendar Assignment → Calendar Generation → Resource Window; consulta sobre asignaciones de trabajo |

El [diccionario](referencia-tecnica/DICCIONARIO-DOCTYPES.md) y [registro de servicios](referencia-tecnica/SERVICIOS-PUBLICADOS.md) se generan desde la revisión publicada `fbca17e584159990bd16a2853228242b2f2454fa`: 53 DocTypes y 66 servicios, sin ejecutar su código ni incluir datos operativos.

## Roles e integridad

Solicitante reporta/consulta su proceso y acepta cuando corresponde. Despachador clasifica/prepara. Supervisor autoriza/asigna/verifica/configura. Técnico ejecuta su trabajo asignado. Roles VB de activos mantienen catálogos según permisos. System Manager tiene administración explícita. Roles logísticos/contables se conceden aparte: ser supervisor CMMS no concede Stock User ni acceso financiero.

- Company/sede requieren autorización explícita para usuarios no privilegiados.
- Compartir no amplía límites duros de alcance, asignación o historia.
- Membresía no concede toda la visibilidad del equipo.
- Origen, ciclos y snapshots no se alteran editando campos/children directamente.
- Evidencias mantienen privacidad y restricciones de carga/descarga.
- ERPNext conserva inventario/valoración/contabilidad; no existe libro paralelo.
- Documentos nativos vinculados combinan sus permisos con el contexto CMMS pertinente.
- Reintentos usan claves/validación; conflictos transitorios pueden exigir repetir sin duplicar efecto.

## Campos nativos de integración

Material Request conserva origen/sede/orden, identidad/huella/motivo y fuentes. Stock Entry conserva orden/sede, salida original e identidad; devoluciones apuntan a la línea emitida. Líneas de Purchase Invoice no inventariables y Timesheet tienen vínculo de orden. Ver [contrato R3](referencia-tecnica/R3-STANDARD-HANDOFF.md).

El [contrato R4.0](06-r4-alcance-local.md) describe puntos, revisiones, lecturas y bloqueo de movimientos de activos secundarios. El nuevo layout completo y la ejecución por actividad configurable permanecen en el plan.

## Jerarquía funcional ENT-002

VB Equipment Location conserva identidad y Company/Site. Padre/estado se cambian mediante servicio con escritura nativa, vista previa vigente y motivo; historial TruCMMS Location Event inmutable y no compartible. No se agregan permisos regionales. [Contrato y evidencias](09-jerarquia-funcional-ENT002.md).
