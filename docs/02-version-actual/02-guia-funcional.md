# Guía funcional de la base verificada

## Navegación

Abrir TruCMMS desde ERPNext. Grupos: Operación, Activos, Planes y rutinas, Recursos y servicios, Repuestos y costos, Análisis y Configuración. Se muestran según rol; la autorización permanece en servidor.

## Correctivo

1. Solicitante registra falla, equipo/ubicación, descripción, prioridad y evidencia permitida.
2. Envía; despachador clasifica y aprueba/rechaza.
3. La solicitud aprobada genera una orden sin duplicar origen. También existen creación directa controlada y proveedores preventivo/inspección.
4. Se prepara alcance, equipo/disciplina y programación; supervisor autoriza/asigna a personas elegibles.
5. Técnicos asignados registran tareas, resultados, tiempos y evidencia privada; secundarios conservan participación individual.
6. Terminación técnica precede a verificación independiente; aceptación según sede y cierre. Pausa, retrabajo, cancelación y reapertura conservan eventos/ciclos.

Reabrir devuelve a autorización para revisar programación y elegibilidad. No devuelve silenciosamente una orden cerrada a ejecución.

## Activos/componentes

Mantener identidad física/tag, perfiles y criticidad; registrar instalación/reemplazo con vigencia. Conservar qué equipo ocupaba una ubicación y qué componente estaba instalado. Planes activos/trabajo abierto requieren reconciliación antes de cambios incompatibles.

## Preventivo

1. Preparar/aprobar revisión de procedimiento con tareas, mediciones y materiales opcionales.
2. Crear/activar plan con contexto, calendario/medidor y reglas.
3. Materializar obligaciones futuras; no equivale a abrir una orden por cada fecha.
4. Liberar manualmente o habilitar automatización explícita con identidad autorizada. Se abre Draft y continúan controles normales.
5. Ejecutar sobre snapshot; la verificación válida actualiza vencimientos/baselines según regla.
6. Posponer, omitir, cancelar o renovar condiciones con motivo. Omitir no cuenta como mantenimiento cumplido.

Hay restricciones de liberación y excepciones auditadas. Automatización revalida identidad, alcance y antigüedad de lecturas.

## Lecturas actuales

Configurar medidor del equipo/componente, unidad y semántica. Lecturas finitas/cronológicas; acumulativos no disminuyen sin reinicio/reemplazo explícito. Corregir la última lectura conserva original y momento. Historial desde el medidor.

Todavía no existe el selector multipunto dentro de la orden ni el medidor de instalaciones sin equipo del diseño R4.0.

## Recursos/compras

Repuestos y costos → Proyección de materiales. Combina procedimientos congelados y estimaciones adicionales de órdenes abiertas. Consultar existencias o descargar CSV; son ayudas de revisión, no reservas/compras automáticas.

Material Request Purchase se crea en borrador; logística revisa y continúa con roles/workflows nativos. Para compra externa se usa la lista y Material Receipt al llegar bienes, registrando cantidades, valoración y trazabilidad.

## Entrega/devolución

- Orden autorizada/asignada → Materiales → Solicitar salida.
- Material Request Material Issue enviado → TruCMMS → Preparar vale de salida.
- Almacén revisa/envía Stock Entry mediante controles nativos.
- Orden → Entregas y devoluciones: consulta y confirmación por técnico asignado/supervisor.
- Constancia imprimible con usuario, fecha, motivo y materiales.
- Salida enviada → Preparar devolución: revisar cantidad real y enviar Material Receipt vinculado; controles de cantidad, lote/serie y valoración.

Solicitar no descuenta stock. Confirmar recogida completa se hace por vale; una entrega parcial usa el vale por su cantidad real. Anulaciones conservan la constancia y requieren tratar devoluciones activas.

## Costos

Vincular orden en líneas no inventariables de Purchase Invoice y líneas de Timesheet de empleado. Consultar Costos vinculados: valoración neta de inventario + servicios netos + costo de horas nativas, en moneda de empresa. No suma de nuevo tiempos de ejecución técnica. Falta de permisos produce un total explícitamente incompleto.

## Capacidad inicial

Supervisor define Ventanas y ausencias por persona/sede, con motivo; turno nocturno termina al día siguiente. Capacidad y disponibilidad consulta hasta 31 días. Disponible descuenta ausencias; Programado incluye participantes activos; Libre es saldo neto, no bloques continuos garantizados. Informa solapamientos, sobrecarga y trabajo fuera de disponibilidad. Sin calendario: Sin configurar. No autoriza ni asigna trabajo.
