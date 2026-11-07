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

Configurar medidor del equipo/componente o de un punto estable de instalaciones, unidad y semántica. Lecturas finitas/cronológicas; acumulativos no disminuyen sin reinicio/reemplazo explícito. Corregir la última lectura conserva original y momento. Historial desde el medidor.

En una orden guardada, menú Alcance: configurar ubicación y puntos antes de autorizar; consultar referencias históricas; registrar una lectura vinculada durante la ejecución asignada. Un punto de instalaciones no necesita un activo ficticio. El layout completo de cinco pantallas permanece como propuesta.

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

## Capacidad y calendarios

Supervisor define Ventanas y ausencias por persona/sede, con motivo; turno nocturno termina al día siguiente. Capacidad y disponibilidad consulta hasta 31 días. Disponible descuenta ausencias; Programado incluye participantes activos; Libre es saldo neto, no bloques continuos garantizados. Informa solapamientos, sobrecarga y trabajo fuera de disponibilidad. Sin calendario: Sin configurar. No autoriza ni asigna trabajo.

Para un patrón recurrente, Recursos y servicios → Calendarios semanales: elegir empresa/sede, turnos por día y, opcionalmente, lista nativa de feriados con permiso de lectura. Indicar expresamente si un turno termina al día siguiente. Calendarios por técnico: elegir calendario, persona y vigencia; guardar y usar Calendario → Generar disponibilidad para un periodo de hasta 31 días. El historial conserva cada generación.

Un día generado sin turnos muestra 0 horas. Para una excepción sobre una ventana generada, deshabilitarla con nuevo motivo y crear una ventana explícita de reemplazo, o registrar una ausencia. Detener futuras generaciones en la asignación conserva las ventanas ya existentes. Repetir el mismo periodo devuelve lo generado; un periodo parcialmente solapado se rechaza.

## Árbol de ubicaciones

TruCMMS → Activos → Árbol de ubicaciones. Elegir sede, expandir/buscar y abrir ficha o listas relacionadas. Usuarios con escritura pueden usar vista previa y motivo para cambiar padre o estado. [Guía y límites ENT-002](09-jerarquia-funcional-ENT002.md).

## Organización operativa opcional

1. Como administrador, abrir Configuración → Estructura operativa y seleccionar Company.
2. Crear unidad raíz o hija con código y nombre; tipo opcional, sin niveles geográficos obligatorios.
3. En la ficha de una sede, usar Asignar unidad operativa, motivo, vista previa y confirmación. Vacío desvincula la sede.
4. Consultar el árbol y el historial de agrupación. Los lectores ven solo las ramas/sedes que ya puedan consultar.

Las sedes existentes no requieren este paso. No cambia equipos, almacenes, permisos ni trabajo autorizado. [Reglas y evidencias ENT-003](10-organizacion-operativa-ENT003.md).
