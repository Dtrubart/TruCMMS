# R1 — operación y preparación del candidato

Estos procedimientos corresponden al paquete TruCMMS en Frappe/ERPNext. El Docker actual es de desarrollo. La aprobación del piloto y la decisión de producción son puertas independientes de las pruebas automáticas.

## Verificación de salud

En el bench y sitio que se desea verificar:

```text
bench --site NOMBRE_DEL_SITIO execute vanbags_maintenance.operations.health
```

El diagnóstico es de solo lectura y requiere administración. Comprueba conexión de base de datos, Redis, trabajadores de las colas short/default/long, scheduler, espacio libre, reloj de almacenamiento y huella del paquete desplegado. No muestra contraseñas ni claves. Un resultado saludable no constituye aprobación productiva. Scheduler deshabilitado, developer_mode o maintenance_mode deben interpretarse con el contexto del entorno; no se habilitan automáticamente.

## Antes de actualizar

1. Identificar revisión publicada, versiones de Frappe/ERPNext, dependencias Python y reglas horarias. Comparar la fuente desplegada con el paquete publicado y conservar la huella por sitio.
2. Confirmar ventana de mantenimiento y destino. Nunca ejecutar `bench use` para cambiar implícitamente el sitio de trabajo.
3. Generar respaldo completo con base de datos, archivos públicos/privados y configuración necesaria para descifrar. Proteger la configuración de respaldo como un secreto; guardarla fuera del repositorio y de la retención automática.
4. Restaurar ese respaldo en un sitio nuevo y probar la actualización allí antes de aplicarla al destino. Evitar reusar o sobrescribir sitios de recuperación anteriores.
5. Validar permisos por empresa/sede, archivos privados y cambios de esquema sobre datos poblados. Registrar revisión, evidencia y resultado.

## Despliegue del candidato

1. Instalar la dependencia fijada en `pyproject.toml`, incluido `tzdata==2026.5`, junto con las versiones compatibles de Frappe/ERPNext.
2. Construir/enlazar los assets de la app mediante `bench build --app vanbags_maintenance`.
3. Ejecutar `bench --site NOMBRE_DEL_SITIO migrate`. La huella se registra después de completar las migraciones y la navegación.
4. Verificar salud, identidad de sitio/hostname, navegación por rol, My Work/Agenda/Calendar y acceso privado. Recargar el navegador para obtener los assets y el boot de la nueva versión.
5. Registrar resultados y aprobación humana del piloto. La demo sintética no representa mantenimiento físico ni aprobación de producción.

## Recuperación y rollback

Conservar tanto el paquete anterior compatible como su respaldo completo. Crear un destino de recuperación nuevo; restaurar base de datos, archivos y configuración de cifrado; instalar el paquete compatible y migrar solo bajo una ruta probada. Comparar documentos, vínculos, versiones, roles, User Permissions, archivos por hash y reportes. Confirmar qué trabajos se registraron después del respaldo antes de decidir el corte. No hacer downgrade del código contra una base modificada sin un ensayo de compatibilidad. Un rollback que use un respaldo requiere una decisión explícita sobre los datos posteriores al punto recuperado.

## Alertas y revisión operativa

- Investigar ausencia de trabajadores o heartbeats antiguos, crecimiento de colas, scheduler detenido, errores repetidos y caída de ping/socket.
- Vigilar espacio libre, crecimiento de archivos, fallos de respaldos y discrepancias de huella/código o reglas horarias.
- Verificar restauración periódicamente en un destino aislado. Un archivo de backup existente por sí solo no demuestra recuperación.
- Definir responsables y canales de aviso antes de producción. No se configura una automatización ni se envían avisos externos en esta entrega.

## Puertas del destino productivo — pendientes de decisión y comprobación

| Puerta | Evidencia requerida |
|---|---|
| Aceptación humana | Revisión y disposición de CH02-R1-T01–24, participantes y revisión exacta |
| Entorno | Arquitectura productiva, developer_mode deshabilitado y proceso de despliegue validado |
| TLS y exposición | Dominio, certificados y límites de red comprobados |
| Secretos | Contraseñas únicas, acceso mínimo y mecanismo de custodia; credenciales demo fuera de producción |
| Recuperación | Destino externo de backups, cifrado/custodia, retención, RPO y RTO acordados y ensayados |
| Operación | Scheduler/colas, monitoreo, alertas y responsables activos |
| Capacidad | Carga y datos representativos del volumen acordado; la medición local es una línea base, no un SLA |
| Relojes | Reglas horarias coherentes de plataforma, app y controles de navegador |

## Aceptación del piloto

Registrar responsable, fecha, revisión, sedes, roles probados, escenarios aceptados, incidencias y disposiciones. La aprobación del menú visual no sustituye los escenarios funcionales. La aprobación del piloto demo no habilita automáticamente un despliegue productivo. Ver `R1-ACCEPTANCE-MATRIX-2026-10-26.md` y el recorrido de revisión de esta entrega.
