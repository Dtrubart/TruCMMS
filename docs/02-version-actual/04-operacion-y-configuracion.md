# Operación y configuración

App `vanbags_maintenance`, dependiente de ERPNext, en sitio compatible. Base comprobada: Frappe 16.28.0/ERPNext 16.29.0, Python 3.14.7, Node 24.21.0 y dependencia horaria fijada por el paquete. Reglas de plataforma/app/navegador deben ser coherentes.

El Docker trabajado es de desarrollo; DEV/TEST son sitios distintos. Los comandos Bench deben identificar explícitamente el sitio, sin cambiar el predeterminado con `bench use` como atajo.

## Configuración funcional

1. Company, sede y zona horaria.
2. Ubicaciones/equipos, usuarios/roles y User Permissions de empresa/sede.
3. Disciplinas/equipos, membresías/autorizaciones con vigencia.
4. Política de aceptación y procedimientos.
5. Preventivo: revisión aprobada, plan, medidor/reglas y automatización explícita si aplica.
6. Logística: Item/UOM/Warehouse, vínculo de sede, roles nativos y configuración Company/fiscal/contable para transacciones reales.
7. Capacidad: ventanas explícitas; no se siembra jornada predeterminada.

Procurement complejo usa workflows nativos; operación sencilla puede configurar un circuito corto y recepción manual externa. No se omiten validaciones de integridad del ERP.

## Actualizar y recuperar

Identificar revisión/dependencias/sitio; conservar paquete previo y respaldo completo; ensayar actualización poblada cuando corresponda. Construir/enlazar assets, migrar, verificar salud, hostname, permisos, navegación y huella; registrar resultados.

El respaldo incluye base, archivos públicos/privados y configuración necesaria para recuperar secretos/cifrado. Custodiar fuera de Git/retención automática. Restaurar en sitio nuevo y comparar documentos, vínculos, roles/permisos, archivos por hash y reportes. No sobrescribir recuperaciones ni bajar código contra una base modificada sin ensayo.

La recuperación poblada más reciente corresponde a R3. R4.1 inicial tiene respaldo/preservación comprobados, no una recuperación completa nueva atribuida a R4.

## Producción pendiente

Acordar infraestructura, TLS/exposición, cuentas, custodia/retención, RPO/RTO, capacidad/monitoreo/responsables y aceptación humana. CI y demo sintética no son aprobación productiva. Credenciales permanecen fuera de la documentación exportable.

Referencia: [operaciones](referencia-tecnica/OPERATIONS-R1.md). Su contexto histórico de R1 no sustituye la [evidencia actual](05-validacion-y-limitaciones.md).
