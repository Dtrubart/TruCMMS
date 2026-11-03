# R4.0 — alcance y mediciones implementados

Fecha: 2026-11-02. Entornos: DEV y TEST. Revisión publicada y aprobada en CI: `edd2353b2fd6e53528393762ababee8a4bfb9ae3`. Este documento complementa los contratos históricos de R1–R3. Publicación, CI, recuperación y aceptación humana se registran por separado.

## Comportamiento implementado

- Las órdenes nuevas usan el contrato `R4`: requieren ubicación de alcance y al menos un punto antes de autorizar. Se admite guardar un borrador incompleto para resolver su alcance explícitamente.
- Una orden mantiene una sola Company y sede. Sus puntos pueden ser equipos, componentes instalados, ubicaciones, puntos estables de medición de instalaciones o referencias ocasionales con descripción.
- Cada fila tiene identidad estable. La configuración del borrador conserva revisión, actor, fecha y motivo. Después de autorizar, el alcance queda congelado.
- Al autorizar se revalidan todos los puntos contra su contexto actual y se conservan los identificadores, valores, unidades y fechas de las lecturas de referencia. Una lectura posterior no reescribe esta referencia histórica.
- Los medidores de R2 admiten un punto de instalaciones sin equipo ficticio. Conservan unidades y semántica acumulativa/condición/tasa, correcciones, reinicios y épocas. Equipo/componente y punto de instalaciones son asociaciones excluyentes.
- Durante la ejecución asignada se registra una lectura mediante el servicio de R2 y se vincula a la orden y al punto. Una repetición con la misma clave no duplica el registro ni permite atribuirlo a otro punto.
- Los registros anteriores conservan su contrato anterior y sus campos originales; la migración no inventa ubicaciones, puntos ni mediciones históricas. Un borrador anterior puede adoptar el nuevo contrato mediante configuración explícita.
- Un activo secundario de una orden abierta también bloquea su traslado/remoción/reemplazo. La comprobación de movimientos retroactivos incluye el historial de participación secundaria en órdenes cerradas.

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
- Se añadieron pruebas para cambios de sede/deshabilitación entre configuración y autorización, bloqueo de traslado de activos secundarios e historial de movimientos. [CI independiente: 434/434 pruebas, 133.320 s](https://github.com/Dtrubart/TruCMMS/actions/runs/41559626517), incluida instalación limpia.
- La corrida intermedia de 432 pruebas tuvo un fallo temporal en una prueba anterior de traslado: el instante del movimiento no era posterior a la instalación inicial. La prueba de permisos declara ahora una instalación sintética una hora antes; no se cambió la validación temporal productiva.
- Verificación de Desk: sitio correcto, diálogo de alcance, contexto anterior y formulario de punto de medición; sin guardar documentos operativos. Capturas de escritorio/móvil y prueba interactiva del prototipo completadas.
- Última regresión local: 433/434 aprobadas en 483.188 s. El escenario de traslado con componentes falló por un movimiento no posterior al inicio de instalación; su repetición aislada pasó en 4.004 s. No se presenta esa corrida local como totalmente aprobada. Las 16 pruebas de alcance pasaron dentro de ella.
- Recuperación/upgrade verificados: respaldo anterior restaurado en `restore-r4-scope.vanbags.localhost`, migrado a R4.0 y comparado contra los 514 documentos, ocho adjuntos y conteos nativos originales. DEV y TEST no fueron reemplazados. La [recuperación del nuevo historial R4](07-r4-recuperacion-poblada.md) también está aprobada: 542 documentos CMMS, nueve adjuntos, cuatro puntos, dos revisiones y dos lecturas vinculadas, con corrección y permisos conservados.
- Política DEV/TEST: `R4.0-work-scope`. Huella común: `6b0aad4adce55e8f604dd51ec9f6ca577b2502e77c4fc4607aebbac523ce317e`. Los 276 archivos del paquete coinciden entre publicación y fuente activa. No se generaron registros R4 operativos en DEV/TEST.

## Pendientes antes del cierre ampliado

La puerta técnica de recuperación poblada R4.0 está completada. Permanecen la revisión humana del prototipo, posteriores incrementos del layout y aceptación operativa. R4 global sigue abierto. Se conserva evidencia de la intermitencia temporal local sin atribuirle una causa de infraestructura no demostrada.

Herramientas locales: `docker/development/r4-scope-preserve.py`, `r4-scope-check.py` y `verify-r4-scope-ui.mjs` en el workspace de desarrollo. Los respaldos, configuraciones y registros crudos quedan fuera de la publicación documental.
