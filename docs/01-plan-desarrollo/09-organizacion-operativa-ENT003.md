# ENT-003 — organización administrativa opcional

Autorización: el 2026-11-06 el propietario indicó «ahora vayamos con el siguiente paso», después de identificar ENT-003 como siguiente bloque. Esta autorización cubre organización opcional; no incorpora concesiones regionales de ENT-004 ni contexto global de ENT-005.

## Contrato

- Cada unidad operativa pertenece a una Company nativa. Su padre opcional pertenece a la misma Company. No se permiten agrupaciones multiempresa en esta versión.
- El árbol tiene profundidad variable; «país», «región» o «división» son etiquetas opcionales, no niveles obligatorios ni estructuras financieras.
- Nueva entidad `TruCMMS Operating Unit`: identidad hash estable; código único dentro de la Company, nombre, tipo opcional, padre y estado. Company y código son permanentes; cambiar nombre/tipo conserva identidad.
- `TruCMMS Site.operating_unit` es un Link opcional y único: pertenencia administrativa primaria actual. Las sedes existentes no se agrupan automáticamente. Un cliente con una sede puede omitir toda esta configuración.
- Agrupar o mover una sede no cambia su Company ni mueve equipos, almacenes, equipos humanos, solicitudes, órdenes o documentos financieros.
- Cambiar pertenencia o padre exige vista previa vigente, motivo y confirmación del administrador. El efecto es inmediato con fecha del servidor; sin fechas retroactivas/futuras.
- `TruCMMS Organization Event` conserva creación, cambios de etiqueta/tipo, reparentado, activación/desactivación y pertenencia de sede. Snapshots anteriores/posteriores permiten interpretar el cambio sin reescribir historia. No se reconstruye historia anterior a la entrega.
- Las vistas y listas de esta versión muestran organización **actual**. Los eventos permiten revisión histórica administrativa; no hay reporte general reconstruido «a fecha».

## Permisos y experiencia

System Manager / Administrator configura unidades y pertenencias, sujeto a permisos nativos de lectura de Company y escritura del documento. No se crea un rol regional nuevo.

Los roles CMMS existentes pueden leer las unidades que sean ascendientes de sus sedes autorizadas. La consulta usa los permisos nativos vigentes de Site; no otorga acceso a sedes hermanas ni a unidades vacías/no vinculadas. Los detalles muestran solo sedes directamente vinculadas que el usuario pueda consultar. El historial administrativo global queda restringido al administrador porque puede contener otras ramas y sedes.

Esta proyección de lectura no es una concesión regional. No se materializan User Permissions, ni se heredan permisos de negocio desde el padre, ni se cambia el cálculo existente de ocupación de personas. No hay caché global de visibilidad; cada consulta revalida permisos.

Navegación: TruCMMS → Configuración → Estructura operativa, y enlaces desde las fichas de unidad/sede. Creación mediante formularios nativos; árbol con expansión progresiva, búsqueda y páginas de 50. En sede: «Asignar unidad operativa» y «Historial de agrupación». Las funciones de cinco pantallas de órdenes siguen en R4.7.

## Integridad y límites iniciales

Código normalizado, unicidad por Company, ciclos y cruces de empresa rechazados. Operaciones serializadas por Company con lecturas bloqueantes actuales; una vista previa obsoleta o un conflicto exige reintento. La vista previa incluye unidades y sedes afectadas.

Máximo inicial: 64 niveles, 5.000 unidades por Company y 10.000 sedes afectadas por una operación estructural. Son límites conservadores, no capacidad empresarial certificada. No se truncan movimientos mayores silenciosamente.

Desactivar requiere resolver hijos activos y desvincular sedes; no hay cascada automática. Reactivar exige ascendientes activos. No se eliminan unidades desde el flujo normal. El historial permanece inmutable y no compartible. Una sede desactivada puede desvincularse, pero debe activarse antes de recibir nueva pertenencia.

## Verificación requerida

Preservación antes/después de migración, permisos/revocación, empresa y código inmutables, unicidad, ciclos/profundidad, sedes sin agrupación, historial, vistas previas obsoletas y concurrencia. Prueba visual con administrador y lector de una sola sede; fixtures sintéticos aislados de los datos del ejemplo VanBags. Regresión y CI de instalación limpia, recuperación poblada y documentación de resultados reales antes del cierre técnico.

La aceptación humana, ENT-004/005, agregados regionales, jerarquía genérica de equipos, predicción R5 y offline R6 siguen separados.
