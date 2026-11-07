# Brechas y riesgos — contexto empresarial

Fecha: 2026-11-05. Identificadores ENT-FIND locales a esta auditoría; no sustituyen IDs de requisitos/decisiones de la especificación. Prioridad indica orden recomendado, no defecto confirmado ni autorización.

| ID | Prioridad / tipo | Hallazgo y consecuencia | Evidencia / tratamiento propuesto |
| --- | --- | --- | --- |
| ENT-FIND-001 | Alta / gobierno | El brief propone niveles y asignaciones de releases nuevos; el DOCX es borrador y el roadmap vigente tiene entregas verificadas. Mezclarlos falsearía el estado | CURRENT_STATE_AUDIT, fuentes y encaje. Conciliar requisitos/decisiones sin renumerar R1–R3; ENT-PROP-001 |
| ENT-FIND-002 | Alta / diseño de seguridad | Reutilizar el get_children de Location como árbol TruCMMS no aplica explícitamente Company/Site | Location instalado:214. No es exploit actual demostrado. Endpoint propio autorizado; ENT-PROP-002 |
| ENT-FIND-003 | Alta / historial | Cambiar parent_location tiene validación y track_changes, pero no un evento empresarial con vigencia e impacto en trabajo/reportes/concesiones | organization.validate_context y JSON de ubicación. Conservar Version; añadir política/operación controlada antes de herencia regional; ENT-PROP-002 |
| ENT-FIND-004 | Alta / alcance ausente | No hay unidades operativas ni pertenencia administrativa de sedes | Inventario de 53 DocTypes. Definir cardinalidad y empresa; ENT-PROP-003 |
| ENT-FIND-005 | Alta / alcance ausente | No hay concesiones por nodo con descendientes. Añadir filtros UI no resolvería autorización | organization.allowed/in_scope. Resolver sedes e intersectar permisos existentes; decidir herencia antes de persistir grants; ENT-PROP-004 |
| ENT-FIND-006 | Media / UX parcial | Contexto Company/Site local a páginas; pérdida de continuidad al abrir algunas listas nativas; sin preferencias regionales/favoritos | navigation, work_views y trucmms_work.js. Contexto explícito compartido; ENT-PROP-005 |
| ENT-FIND-007 | Alta / escala no acreditada | Vistas truncadas a 500, paginación local e informe de instalaciones sin límite; grandes ámbitos podrían ser lentos o inducir totales incompletos | work_views.get_work, navigation.home, assets.installation_register. Paginación/consultas agregadas y benchmark; ENT-PROP-006 |
| ENT-FIND-008 | Media / decisión de privacidad | Capacidad calcula ocupación global sin nombres de trabajo ajeno. Suprimirlo evita cierta inferencia pero permite doble reserva | capacity.py:112,123,144. Aprobar política de señal de disponibilidad, mantener base actual entretanto; ENT-PROP-001/004 |
| ENT-FIND-009 | Media / diseño no aprobado | Confundir instalación, contención y conexión de sistemas produciría transferencias/herencia incorrectas | assets, components, brief. Mantener relaciones separadas; ENT-PROP-007 |
| ENT-FIND-010 | Alta / validación pendiente | No hay nuevas pruebas de revocación multisession, cachés regionales, servicios de árbol ni exportación regional | Existen invalidación nativa y pruebas históricas, no servicios regionales desplegados. Matriz negativa obligatoria antes de entrega; ENT-PROP-004/006 |
| ENT-FIND-011 | Media / migración | Reemplazar VB Equipment Location por Location afectaría Links, IDs, permisos e historia | JSON y controlador nativos/custom. Retener IDs; si se elige reemplazo exigir mapeo, ensayo y rollback; ENT-PROP-002 |
| ENT-FIND-012 | Media / UX no validada | Contexto global podría ocultar cambios sin guardar o presentar horas ambiguas entre zonas | No es fallo observado. Definir transición y zona explícitas; ENT-PROP-005 |
| ENT-FIND-013 | Media / cobertura funcional | Árbol genérico de equipos/componentes y relación de sistemas no existen; no debe venderse como soportado | VB Equipment y TruCMMS Component sin parent_equipment; instalación sí existe. Diseñar solo con casos aprobados; ENT-PROP-007 |
| ENT-FIND-014 | Alta / operación pendiente previa | Rotación de credenciales de desarrollo permanece pendiente por decisión del propietario | Antecedente de la sesión; no se recuperaron ni probaron secretos. Mantener acción separada, con aprobación específica, sin bloquear el análisis |

## Criterios de cierre

Cada hallazgo se cierra con decisión registrada y evidencia de aceptación, no solo con un commit. Una capacidad diferida queda aceptada como limitación explícita, no marcada implementada. No se identificó en esta auditoría un bypass nuevo reproducido que permita acceso no autorizado; las observaciones de seguridad son controles que deben preservarse o incorporarse al ampliar el modelo.

Las afirmaciones sobre ausencia se limitan al código y documentación inspeccionados. Una verificación posterior puede reclasificar un hallazgo aportando evidencia concreta.

## Seguimiento ENT-001/002 autorizado

ENT-FIND-001: contrato inicial registrado, decisiones regionales futuras separadas. ENT-FIND-002/003: se entrega árbol propio autorizado y cambios con eventos/efecto inmediato, conservando IDs. ENT-FIND-006: mejora parcial por sede, sin contexto global. ENT-FIND-007/010: controles acotados y pruebas locales añadidos; escala empresarial y concesiones regionales siguen pendientes. [Evidencia posterior](../../../02-version-actual/09-jerarquia-funcional-ENT002.md). La rotación de credenciales continúa pendiente.

## Seguimiento ENT-003 autorizado

ENT-FIND-004: organización opcional y pertenencia primaria implementadas con Company inmutable e historial. Se añadieron controles para títulos de Unit/Site y pruebas de lector parcial, sin grants regionales. ENT-FIND-005/006/007/010 conservan el trabajo pendiente de resolver común, contexto global, escala y concesiones regionales. [Evidencias posteriores](../../../02-version-actual/10-organizacion-operativa-ENT003.md).
