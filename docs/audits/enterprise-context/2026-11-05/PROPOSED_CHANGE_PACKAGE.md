# Paquetes propuestos — jerarquía y contexto

Estado: propuestas independientes para aprobación; no implementadas por esta auditoría. IDs ENT-PROP son provisionales y locales. No crear todavía DocTypes con nombres sugeridos como si fueran contratos definitivos.

## ENT-PROP-001 — Decisiones y contrato de alcance

**Objetivo:** fijar significado y límites antes de tocar datos.

Entregables: glosario, relación entre requisitos originales/brief/roadmap, decisiones con propietario, política Company/Site, política de ocupación global, y matriz de pruebas. Distinguir historial de ubicación, instalación de equipo y cobertura de personal. Mantener nombre TruCMMS y paquete nativo actual.

Propuesta inicial: cada sede pertenece a una Company; la primera versión de unidad operativa pertenece a una Company y tiene un padre opcional de la misma Company. Niveles y etiquetas configurables, sin columnas obligatorias país/provincia/ciudad. Una sede tiene una pertenencia administrativa primaria; relaciones secundarias se posponen hasta justificar su necesidad. Una región multiempresa queda diferida y no otorga derechos financieros.

**Aceptación:** ocho decisiones del checklist resueltas; requisitos nuevos identificados como nuevos; ninguna entrega histórica renombrada. **Dependencias:** ninguna. **Riesgo:** bajo; trabajo documental.

## ENT-PROP-002 — Árbol funcional controlado

**Objetivo:** navegar edificios/áreas sin perder identidad ni historia.

Conservar VB Equipment Location, Company/Site e IDs. Reutilizar herramientas de árbol de Frappe con endpoint propio paginado/autorizado y expansión progresiva. Mantener ciclos, mismo ámbito y rechazo de padres inválidos. La profundidad máxima se acordará con ejemplos y medición; no prometer profundidad ilimitada.

El reparentado debe ser operación explícita con motivo, actor, fecha efectiva, origen/destino, impacto mostrado y serialización para impedir ciclos concurrentes. No cambiar sedes o empresas mediante reparentado. No borrar nodos usados en historia; desactivar conservando referencias. Definir fechas retroactivas y su impacto antes de habilitarlas. No cambiar historia congelada de órdenes existentes.

Alternativas: A, mantener adyacencia y añadir servicio/control/historial (recomendada inicialmente); B, migrar el DocType propio a NestedSet tras evaluación de volumen; C, migrar a Location ERPNext con mapeo completo (mayor impacto, no recomendada de inicio).

**Aceptación:** árbol y búsquedas solo muestran nodos autorizados; ciclos concurrentes rechazados; reparentado conserva IDs e historia; órdenes históricas siguen legibles; rollback ensayado si hay migración. **Dependencia:** 001. **Riesgo:** medio, afecta jerarquía vigente.

## ENT-PROP-003 — Organización administrativa opcional

**Objetivo:** coordinar varias sedes sin imponer complejidad a un cliente pequeño.

Añadir unidades operativas opcionales y pertenencia de sedes según 001. Separar estas unidades de ubicaciones, equipos y equipos humanos. Empresa con una sede funciona sin crear árbol regional. Cambios de pertenencia con fecha y evento conservan interpretación histórica; decidir si los reportes usan organización actual o «a fecha» y mostrarlo.

No inferir Company de una etiqueta regional ni permitir que mover una sede cambie su Company. No mover activos, almacenes o personas automáticamente al cambiar su agrupación administrativa.

**Aceptación:** cliente de una sede sin pasos extra; árbol variable con sedes hermanas; operaciones entre empresas rechazadas; historial interpretable. **Dependencias:** 001, diseño de controles reutilizable de 002. **Riesgo:** medio; esquema nuevo opcional.

## ENT-PROP-004 — Resolución de ámbito y concesiones

**Objetivo:** una sola interpretación de alcance para UI, consultas y servicios nuevos.

Implementar resolución servidor de contexto a sedes autorizadas. Inicialmente usar permisos Company/Site existentes como autoridad: pertenecer a una región no da permisos. Si se aprueban concesiones administrativas por nodo, diseñar explícitamente su materialización/intersección con User Permission y no introducir un segundo motor contradictorio. La revocación deberá afectar lecturas y acciones nuevas, preservando historial.

Definir si una concesión de descendientes sigue cambios futuros del árbol o congela una lista; se recomienda herencia dinámica con previsualización de impacto y autorización de cambios de pertenencia. Ausencia de concesión válida deniega acceso; no usar «sitio vacío = autorizado en todo». Equipos humanos con cobertura regional siguen exigiendo autorización personal y elegibilidad.

Validar identificadores de contexto, Company/Site y permisos de registro/estado. Incluir búsquedas, reportes, adjuntos, exportaciones y tareas de fondo. Cachés deben distinguir usuario, permisos vigentes y contexto; invalidar al revocar o cambiar árbol. Un trabajo en cola revalida identidad y ámbito al ejecutarse; no hereda privilegios de la UI.

Mantener por defecto la señal de ocupación global sin identificadores ajenos; presentar la decisión explícita del propietario antes de cambiar ese contrato.

**Aceptación:** matriz negativa sin acceso por API directa, búsquedas, descargas ni cachés; revocación en otra sesión efectiva; ningún permiso financiero implícito. **Dependencias:** 001; 003 para contexto regional. **Riesgo:** alto por sensibilidad de autorización; entrega separada y revisable.

## ENT-PROP-005 — Contexto y navegación coherentes

**Objetivo:** interfaz simple para una sede y útil para varias.

Selector común con Company/sede y, cuando exista, unidad operativa; breadcrumb, recientes/favoritos y opción explícita de todas las sedes autorizadas. Validar preferencias guardadas contra permisos actuales. Usuario de una sede entra directamente; usuario multisede conserva preferencia válida; técnico entra a My Work con alcance claramente indicado. El contexto es un filtro, no una concesión.

List/My Work/Agenda/Calendar comparten filtros, criterio de fecha y zona de presentación. Conservar contexto al entrar a listas nativas y al regresar de una orden; mostrar Company/Site de cada registro. En creación, sugerir sede solo si el contexto es inequívoco; exigir selección explícita en contexto regional. Nunca asignar arbitrariamente la primera sede.

Antes de cambiar contexto, proteger el formulario sin guardar mediante guardar/descartar/cancelar; reutilizar la protección de respuestas desactualizadas existente. En calendario regional, mostrar zona seleccionada y conversión explícita; no mezclar horas locales sin indicarlo. No incluye offline.

**Aceptación:** recorrido simple y regional, cuatro vistas consistentes, preferencias revocadas rechazadas, formulario preservado, escritorio y móvil online. **Dependencias:** 001 y resolver 004 para ámbito regional. La mejora Company/Site puede entregarse antes de 003 con alcance acotado. **Riesgo:** medio.

## ENT-PROP-006 — Consultas, reportes y validación empresarial

**Objetivo:** que amplitud de contexto no produzca información incompleta o consultas excesivas.

Paginación real y búsqueda acotada de árbol/listas; totales calculados con consultas agregadas autorizadas, no por longitud de una página. Exportación controlada con límites e identidad explícitos; conservar restricciones por rol. Revisar índices según planes de consulta medidos, no añadirlos indiscriminadamente. Registrar truncamiento y zona/ámbito en reportes.

Definir un perfil de volumen representativo con el propietario. Propuesta de ensayo, no capacidad garantizada: 3 Companies, 50 sedes, 5.000 ubicaciones, 10.000 equipos y 100.000 órdenes sintéticas; probar también un cliente de una sede. Ajustar a infraestructura y necesidad real. Medir latencia p50/p95, memoria, consultas y tamaño de respuesta. Fijar umbrales antes del ensayo; referencia candidata p95 <2 s para lista/expansión y <5 s para agregado en hardware acordado. Excluir generación/exportación pesada de ese umbral interactivo y definir su propio límite.

**Aceptación:** sin resultados de otras sedes ni totales truncados silenciosamente; mediciones reproducibles y límites publicados. **Dependencias:** 002/004/005 según función. **Riesgo:** medio; carga solo en entorno aislado aprobado.

## ENT-PROP-007 — Equipos, componentes y sistemas

**Objetivo:** cubrir composición real sin inventar activos para áreas ni duplicar instalación.

Recoger tres casos: equipo con componentes reemplazables; conjuntos físicos con subequipos; sistemas conectados que no se desplazan juntos. Elegir cardinalidades y tipo de relación. Conservar instalación y movimiento existentes; no activar traslado automático de descendientes. Definir permisos, vigencia, trabajo abierto, mediciones e historia por entidad antes del esquema.

**Aceptación del diseño:** casos AHU1/AHU2, flota, XRF y producción se pueden representar sin mezclar ubicación con activo. Implementación y migración requieren aprobación posterior del diseño. **Dependencias:** 001/002. **Riesgo:** alto si se generaliza sin casos; diferible, no bloquea contexto por sede/región.

## Recomendación de aprobación

Aprobar primero 001 y 002. Después resolver 003/004 y la UX 005. Usar 006 como puerta de entrega; no dejar toda la seguridad para el final. Mantener 007 como diseño separado hasta justificar el alcance. Estos paquetes amplían R4 transversalmente; R4.2 competencias sigue siendo un incremento pendiente, R5 predicción y R6 offline conservan su asignación.
