# R4.0 — candidato local de alcance y mediciones

Fecha: 2026-11-02. Entornos: DEV y TEST. Este documento complementa la línea base publicada `2c5f9ee`; no atribuye a esa revisión el código posterior. La publicación, CI independiente, recuperación del candidato y aceptación humana se registran por separado.

## Comportamiento implementado

- Las órdenes nuevas usan el contrato `R4`: requieren ubicación de alcance y al menos un punto antes de autorizar. Se admite guardar un borrador incompleto para resolver su alcance explícitamente.
- Una orden mantiene una sola Company y sede. Sus puntos pueden ser equipos, componentes instalados, ubicaciones, puntos estables de medición de instalaciones o referencias ocasionales con descripción.
- Cada fila tiene identidad estable. La configuración del borrador conserva revisión, actor, fecha y motivo. Después de autorizar, el alcance queda congelado.
- Al autorizar se revalidan todos los puntos contra su contexto actual y se conservan los identificadores, valores, unidades y fechas de las lecturas de referencia. Una lectura posterior no reescribe esta referencia histórica.
- Los medidores de R2 admiten un punto de instalaciones sin equipo ficticio. Conservan unidades y semántica acumulativa/condición/tasa, correcciones, reinicios y épocas. Equipo/componente y punto de instalaciones son asociaciones excluyentes.
- Durante la ejecución asignada se registra una lectura mediante el servicio de R2 y se vincula a la orden y al punto. Una repetición con la misma clave no duplica el registro ni permite atribuirlo a otro punto.
- Los registros anteriores conservan su contrato anterior y sus campos originales; la migración no inventa ubicaciones, puntos ni mediciones históricas. Un borrador anterior puede adoptar el nuevo contrato mediante configuración explícita.

## Acceso en Desk

En una orden guardada: menú **Alcance** → **Configurar alcance** durante el borrador; **Contexto y lecturas de referencia** para consultar; **Registrar lectura de la orden** durante la ejecución asignada, según rol y autorización efectiva.

En **Planes y rutinas → Puntos de medición** se configuran los puntos estables. Un medidor puede asociarse a ese punto en lugar de a un equipo. Company/sede y la ubicación del punto se comprueban en servidor.

Las revisiones y vínculos de lectura son inmutables. Los permisos se subordinan al acceso a la orden; no se amplían mediante compartir. Los puntos están limitados por Company/sede y rol. La operación de configuración y la captura usan transacciones y bloqueos del documento padre.

## Límites explícitos

La interfaz entregada utiliza formularios y diálogos nativos de Frappe. El [prototipo de cinco pantallas](../01-plan-desarrollo/prototipos/r4-orden-cinco-pantallas.html) contiene datos sintéticos y está separado del producto para revisión visual.

La lectura se vincula a orden/punto; aún no a una actividad de recorrido configurable. Los checklists Pass/Alarm/Failure, formularios, asignaciones/tiempos y costos por actividad/punto, bloqueos documentales y nuevo layout completo pertenecen a los siguientes incrementos. Los resultados del prototipo no crean fallas ni órdenes.

No se certifica en esta entrega la programación preventiva de instalaciones independiente de equipos ni una migración masiva de órdenes históricas al contrato nuevo. R5 sigue siendo predicción/confiabilidad; R6, móvil offline.

## Evidencia local

- Respaldos completos previos de ambos sitios y copia de la fuente anterior conservados bajo `/workspace/snapshots/r4-scope-before-*` y `/workspace/snapshots/r4-scope-source-before` en Ubuntu, alojado en D.
- Referencia de TEST: 514 documentos de TruCMMS, 8 adjuntos y conteos de documentos/movimientos nativos. DEV: cero documentos operativos. Comparación aditiva: valores originales intactos y campos históricos nuevos vacíos.
- Primera batería específica: 12 pruebas aprobadas en 13,400 s.
- Primera regresión: 429/430 aprobadas; el escenario sintético de cuatro sectores omitía ubicación para órdenes nuevas. Se adaptó la solicitud de prueba para indicarla, sin relajar la regla de autorización.
- Se añadieron dos pruebas para cambios de sede/deshabilitación entre configuración y autorización. Regresión final: en ejecución al preparar este registro; consultar el acta final antes de declararla aprobada.
- Verificación de Desk: sitio correcto, diálogo de alcance, contexto anterior y formulario de punto de medición; sin guardar documentos operativos. Capturas de escritorio/móvil y prueba interactiva del prototipo completadas.
- CI remoto y recuperación poblada de este candidato: pendientes. La evidencia de recuperación de versiones anteriores no sustituye estas comprobaciones.

Herramientas locales: `docker/development/r4-scope-preserve.py`, `r4-scope-check.py` y `verify-r4-scope-ui.mjs` en el workspace de desarrollo. Los respaldos, configuraciones y registros crudos quedan fuera de la publicación documental.
