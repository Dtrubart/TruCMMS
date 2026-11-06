# ENT-001 / ENT-002 — contrato y alcance aprobado

Fecha: 2026-11-05. Autorización: el propietario respondió «excelente empecemos» al plan que recomendaba comenzar con ENT-PROP-001 y ENT-PROP-002. Se autoriza ese primer bloque, no el desarrollo regional completo.

## Contrato del primer bloque

- TruCMMS permanece como aplicación nativa de Frappe/ERPNext. Company conserva significado legal/financiero; cada TruCMMS Site pertenece a una Company.
- VB Equipment Location representa una ubicación funcional dentro de esa sede. Sus padres son ubicaciones de la misma Company/Site; no se usan regiones, equipos humanos ni equipos físicos como padres de ubicación.
- Se conserva adyacencia, identificadores y enlaces existentes. El nombre visible puede cambiar sin renombrar el documento. No se migra a Location nativo ni a NestedSet en este bloque.
- Árbol progresivo y búsqueda por sede autorizada; páginas de 50 resultados, con continuación explícita. Historial y ubicaciones desactivadas permanecen consultables.
- Cambiar padre o estado exige permisos nativos de escritura, vista previa vigente, motivo y evento inmutable. Efecto inmediato con hora del servidor; no hay fechas retroactivas ni programación futura.
- Reparentar no cambia Company/Site, instalación de equipos, alcance congelado de órdenes ni autorizaciones de usuarios. Los descendientes conservan su padre inmediato y cambian su ruta actual por la reorganización del ancestro.
- Para desactivar, resolver descendientes activos, equipos ubicados allí, puntos de medición activos y órdenes abiertas que la referencien. Reactivar requiere ascendientes activos. No se borran ubicaciones mediante el flujo normal: se desactivan para preservar identidad.
- Los registros antiguos mantienen Version y snapshots existentes. No se inventa una cronología anterior: los eventos nuevos registran creación o cambios posteriores a esta entrega. El primer movimiento conserva la estructura anterior afectada.
- Límites iniciales de seguridad: 64 niveles y 5.000 nodos por sede para operaciones estructurales. Son límites operativos conservadores, no capacidad empresarial certificada. Si una jerarquía antigua los excede, detener esa operación y evaluar su tratamiento; no truncarla ni repararla automáticamente.
- Serializar operaciones estructurales con el mismo bloqueo de Company utilizado por instalación/traslado de equipos; detectar vistas previas obsoletas. No garantizar ausencia total de deadlocks externos; si ocurre un conflicto transaccional, reintentar desde una nueva vista previa.

## Experiencia inicial

Acceso «Árbol de ubicaciones» en Activos y desde la ficha de ubicación. Sede única autorizada se preselecciona; en otros casos se exige seleccionar sede. Permite búsqueda, breadcrumb, apertura de ficha, creación de raíz/hija según permisos, consulta de historial y acceso a listas relacionadas por ubicación exacta.

Los enlaces a listas no representan todavía un informe consolidado de descendientes ni de todos los puntos secundarios de órdenes. Las cinco pantallas completas siguen en R4.7. Los formularios con cambios pendientes deben guardarse o descartarse antes de lanzar la operación controlada.

## Decisiones que permanecen propuestas

ENT-PROP-003 a 007 no se implementan por esta aprobación: unidades operativas, pertenencias regionales, concesiones con descendientes, contexto global persistente, agregados regionales, relaciones genéricas de equipos y benchmarks empresariales.

La separación conceptual se acepta para evitar acoplamiento, pero cardinalidades y políticas de esas funciones requieren su propia revisión. Se conserva el cálculo vigente de ocupación global sin identificadores ajenos. No se altera esa política ni se rotan credenciales.

R4.2–R4.9 conservan sus nombres. Este bloque es una mejora transversal hacia R4.7/R4.9; R5 predicción y R6 offline permanecen separados.

## Puerta de entrega

Pruebas dirigidas de ámbito, búsqueda/paginación, jerarquía, concurrencia, revocación, inmutabilidad, desactivación y UX; regresión de organización/equipos y suite de integración al consolidar. Respaldo previo y migración aditiva en TEST antes de DEV. Documentar resultados reales, limitaciones y aceptación humana pendiente.

Referencia: [auditoría](../audits/enterprise-context/2026-11-05/CURRENT_STATE_AUDIT.md) y [plan propuesto](../audits/enterprise-context/2026-11-05/IMPLEMENTATION_PLAN.md).
