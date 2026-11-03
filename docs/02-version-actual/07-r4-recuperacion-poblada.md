# R4.0 — recuperación del nuevo historial verificada

Fecha: 2026-11-02. Aplicación: `edd2353b2fd6e53528393762ababee8a4bfb9ae3`, sin cambios funcionales durante esta comprobación. Huella: `6b0aad4adce55e8f604dd51ec9f6ca577b2502e77c4fc4607aebbac523ce317e`.

## Caso y aislamiento

En el clon `restore-r4-scope.vanbags.localhost` se creó un caso sintético de VanBags / North Vancouver S1: dos AHU, un punto estable de caudal de agua y una referencia de área. La orden asignada conserva cuatro puntos, dos revisiones de alcance, lecturas de referencia de autorización, dos lecturas vinculadas, una corrección posterior y evidencia privada. Se utilizaron usuarios sintéticos nuevos con permisos por Company/sede.

Se conservaron base, archivos públicos/privados y configuración en un respaldo completo. Se restauró y migró en un destino nuevo: `restore-r4-populated.vanbags.localhost`. Ambos sitios de recuperación mantienen el scheduler pausado. No se cambió el sitio predeterminado.

## Resultado

- Coincidencia exacta de **542 documentos CMMS**, incluidos sus hijos, y documentos nativos de archivos, compras, inventario, contabilidad y tiempos incluidos en la referencia.
- **9 adjuntos** coincidentes por SHA-256; roles, User Permissions y configuración efectiva de cifrado conservados.
- Los cuatro puntos, dos revisiones y dos vínculos de lectura conservan sus identidades y referencias. La corrección posterior no reescribe la lectura de referencia de autorización.
- Repetir las dos capturas con sus claves originales después de restaurar devuelve las lecturas existentes, sin duplicación ni cambios en el historial.
- Técnico asignado y supervisor acceden al contexto. El solicitante consulta su solicitud, pero no la orden mientras permanece Assigned. El técnico no asignado no obtiene contexto, vínculos de lectura ni evidencia privada.
- Inicio de sesión HTTP con las cuentas sintéticas restauradas y acceso al servicio: técnico asignado HTTP 200; técnico no asignado HTTP 403.
- Tras las comprobaciones, el estado protegido continúa coincidiendo con la referencia del respaldo.

La primera ejecución del verificador esperaba incorrectamente acceso del solicitante a una orden Assigned. Se corrigió la expectativa del verificador según el contrato vigente; no se amplió ningún permiso del producto. Se repitió únicamente el verificador sobre el sitio ya restaurado, sin repetir la carga ni la suite completa.

## Preservación y límites

DEV permanece sin documentos operativos; TEST conserva sus 514 documentos anteriores, ocho adjuntos y conteos nativos. Los casos nuevos solo están en los clones aislados. No se rotaron credenciales compartidas ni se reiniciaron servicios.

Esta evidencia completa la puerta técnica pendiente de recuperación de registros nuevos R4.0. La aceptación humana, la revisión del prototipo de cinco pantallas y la producción son actividades separadas. R4 global sigue abierto; el siguiente incremento funcional es completar calendarios, turnos y excepciones de R4.1.

No se repitieron las 434 pruebas CI: la aplicación no cambió. Se mantiene su [ejecución aprobada](https://github.com/Dtrubart/TruCMMS/actions/runs/41559626517).

Procedimiento local: `docker/development/r4-populated-recovery.py`. Referencias y respaldos privados: `/workspace/r4-populated-candidate-evidence.json`, `/workspace/snapshots/r4-populated-candidate` y `/workspace/r4-populated-recovery-result.json`. El manifiesto contiene credenciales sintéticas y queda fuera del repositorio y de las exportaciones documentales.
