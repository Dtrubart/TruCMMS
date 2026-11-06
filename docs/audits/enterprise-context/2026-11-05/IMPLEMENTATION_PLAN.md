# Plan propuesto de ejecución y validación

Estado: pendiente de aprobación; este documento no inicia las fases. Las estimaciones son días de ingeniería efectivos orientativos, con acceso a entorno de pruebas y revisión del propietario; no plazos comprometidos. No incluyen esperas ni cambios de alcance.

| Fase | Paquete / resultado revisable | Esfuerzo orientativo | Puerta para continuar |
| --- | --- | --- | --- |
| 0 | ENT-PROP-001: decisiones, ejemplos y matriz de trazabilidad | 1–3 días | Propietario aprueba modelo y alcance concreto |
| 1 | ENT-PROP-002: diseño/servicio de árbol y reparentado de ubicación existente | 4–8 días | Pruebas de seguridad, historial y concurrencia; revisión de navegación |
| 2 | ENT-PROP-003: unidades operativas opcionales y pertenencia de sedes | 4–7 días | Cliente de una sede sin complejidad extra; Company inmutable |
| 3 | ENT-PROP-004: resolver de ámbito e invalidación | 4–8 días sin concesiones regionales nuevas | Pruebas negativas y decisión explícita si se añade herencia de grants |
| 4 | ENT-PROP-005: contexto común y cuatro vistas | 4–8 días | Revisión humana de recorridos y móvil online |
| 5 | ENT-PROP-006: agregados/paginación, perfil de carga y piloto | 3–6 días | Métricas, restauración y aceptación registradas |
| Separada | ENT-PROP-007: diseño de relaciones de equipos | 2–4 días de análisis | Nueva aprobación antes de implementar |

Concesiones regionales con excepciones/vigencias, migración a Location nativo o cambio a NestedSet requieren estimación posterior propia. No sumar estos rangos como una promesa de fecha; varias decisiones cambian el esfuerzo.

## Orden mínimo recomendado

1. Aprobar definiciones, límites de Company y política de ocupación de personas.
2. Mejorar ubicaciones conservando sus IDs y comprobar árbol autorizado/historia.
3. Incorporar agrupación administrativa opcional y resolver de sedes.
4. Extender contexto común; empezar por Company/Site si se quiere una entrega UX menor antes de regiones.
5. Cerrar con consultas completas, carga representativa y piloto humano.

No avanzar automáticamente a todos los paquetes por aprobar el primero. No interrumpir R4.2–R4.9 sin registrar la priorización elegida; integrar esta pista con R4.7/R4.9 sin renumerarlas.

## Matriz de aceptación propuesta

Estas son pruebas futuras; no se ejecutaron en esta auditoría.

| Caso | Comprobación requerida |
| --- | --- |
| 1. Una sede | Acceso directo y creación con sede inequívoca; sin árbol regional obligatorio |
| 2. Multisede | Cambiar sede filtra las cuatro vistas y búsquedas; no concede autorización |
| 3. Región parcial | Usuario autorizado en parte de una región ve exclusivamente esa intersección; conteos y exportaciones coinciden |
| 4. Company | Una agrupación no habilita cruces legales; almacenes/compras/costos siguen permisos nativos |
| 5. Equipo compartido | Cobertura de varias sedes no sustituye permisos personales, disciplina ni elegibilidad |
| 6. Revocación | Revocar en otra sesión bloquea consulta/acción posterior, preferencia guardada y archivo; invalida caché y tarea en cola |
| 7. Reparentado | Detecta ciclos y carreras concurrentes; conserva identidad, vigencia, motivo e historia; no altera ámbito silenciosamente |
| 8. Transferencia | Equipo móvil válido; origen/destino autorizados; órdenes abiertas y componentes respetan reglas existentes |
| 9. Formulario | Cambiar contexto con edición pendiente permite guardar/descartar/cancelar; respuestas viejas no sobrescriben contexto |
| 10. Cuatro vistas / hora | Mismo conjunto autorizado según filtros; criterio de fecha explícito; zonas y DST coherentes, creación regional sin sede implícita |
| 11. Canales alternos | API directa, Link search, informes, adjuntos privados, exportación, share y scheduler mantienen límites |
| 12. Escala | Perfil sintético acordado, consultas acotadas, paginación real, totales completos y latencia medida |

Añadir escenarios de desactivación, restauración y rollback a las pruebas de migración. No usar datos de clientes para pruebas de carga sin alcance y autorización específicos.

## Despliegue, migración y reversión

- Antes de una fase con datos: inventario de nodos/Links/historia, copia restaurable y ensayo en sitio aislado. No ejecutar migración solo por aprobar el diseño.
- Preferir cambios aditivos y funciones opcionales. Preservar nombres actuales, Company/Site y snapshots históricos; evitar migraciones de etiquetas a identificadores nuevos innecesarios.
- El árbol administrativo nuevo no cambia Company de sedes ni autoriza usuarios automáticamente. Las pertenencias iniciales requieren revisión; no inferir regiones por nombres.
- Versionar contrato de consultas/contexto y exponer mensajes de truncamiento. Mantener lectura del estado anterior durante transición cuando sea viable.
- Ensayar restauración con base y adjuntos, además de rollback de código; revertir código solo no revierte datos migrados. Documentar punto de no retorno y alcance del respaldo.
- Ejecutar primero pruebas dirigidas al paquete. Una suite completa al integrar cambios de seguridad/esquema, sin repetirla si no hay cambios o fallos nuevos. CI remota solo al llegar a una entrega autorizada.
- En entrega: actualizar documentación de versión actual con lo realmente verificado; mantener el resto en plan de desarrollo. Registrar evidencia y aprobación humana. Publicación/GitHub según autorización vigente, sin confundir este informe con permiso de despliegue.

## Trabajo de esta auditoría

Se generaron únicamente cinco documentos nuevos en esta carpeta. No se cambiaron archivos funcionales, permisos, datos del sitio ni servicios. No se efectuó commit/push. La rotación de credenciales sigue separada y pendiente.
