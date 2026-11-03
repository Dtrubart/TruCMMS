# R4.1 — calendarios semanales y disponibilidad generada

Calendarios de Company/sede con uno o varios turnos por día; asignaciones por técnico y vigencia de hasta 366 días; generación manual de periodos de hasta 31 días. Se reutiliza `TruCMMS Resource Window` para disponibilidad y ausencias, sin duplicar el cálculo de capacidad ni otorgar elegibilidad de asignación.

## Contrato

- Calendario → asignación con patrón y zona horaria conservados → generación inmutable → ventanas Working con origen controlado.
- El patrón usado no se edita retroactivamente: se crea otro calendario para cambiarlo. La asignación conserva identidad y vigencia; detenerla requiere motivo y solo evita generaciones posteriores.
- El mismo periodo devuelve la generación existente. Periodos parcialmente solapados se rechazan. La operación bloquea asignación/técnico y aplica unicidad e inserción transaccional.
- Los turnos usan hora de sede; el fin al día siguiente es explícito. Se rechazan solapes semanales, incluidos domingo/lunes, y horarios inexistentes por DST. La hora repetida tiene política First/Second; las horas reportadas son duración real.
- La lista nativa `Holiday List` es opcional. Crear un calendario con ella y generar exige permiso nativo de lectura; no se conceden roles HR ni permisos globales nuevos. Se descuentan exclusivamente los segmentos de feriado, incluidos turnos nocturnos. La lista debe cubrir las fechas afectadas.
- Se conservan los feriados aplicados en cada generación. Cambios nativos posteriores afectan solo periodos nuevos; un reintento no reescribe el pasado.
- Las ventanas generadas no permiten cambiar origen ni fechas. Para una excepción, el supervisor deshabilita con un nuevo motivo y crea un reemplazo explícito. Una ausencia descuenta horas mediante el mecanismo existente. Detener la asignación no elimina ventanas previas.
- El tablero distingue 0 horas en días generados sin turnos de días todavía sin configurar. Una asignación sin generación no inventa disponibilidad. La carga y conflictos entre sedes siguen considerando a la persona globalmente, sin revelar identificadores ajenos.

## Permisos y navegación

Supervisor/System Manager configura y genera dentro de sus límites efectivos. Dispatcher consulta; el técnico consulta sus asignaciones, generaciones y ventanas. Compartir no amplía acceso. El código no cambia membresías, habilitaciones ni autorizaciones de órdenes.

TruCMMS → Recursos y servicios → **Calendarios semanales** y **Calendarios por técnico**. Desde una asignación guardada se generan ventanas y se consulta su historial. Se mantienen las vistas existentes de capacidad y ausencias.

## Límites de esta entrega

Patrones semanales; sin ciclos rotativos multisemana, nómina, aprobación de vacaciones, optimizador ni asignación automática. No hay regeneración destructiva de rangos materializados ni reemplazo masivo de futuros turnos. La modificación de zona horaria de sede exige reconciliar la asignación antes de seguir generando. La prueba de carrera con conexiones independientes y la recuperación poblada de calendarios nuevos se registran como verificaciones separadas, sin atribuirles resultados de versiones anteriores.

Estado inicial: pruebas específicas y revisión de interfaz aprobadas; consultar la documentación de versión actual para revisión, CI y pendientes vigentes.
