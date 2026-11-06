# Auditoría de arquitectura empresarial y contexto — TruCMMS

Fecha: 2026-11-05. Estado: análisis; propuestas pendientes de aprobación.

## Conclusión

TruCMMS tiene una base funcional y de autorización por empresa y sede que debe conservarse. No tiene todavía el modelo de unidades operativas regionales ni un contexto común de navegación propuesto en el nuevo documento. La ampliación es viable de forma incremental; no requiere sustituir ERPNext, rehacer el ciclo de órdenes ni crear un segundo inventario.

El principal cambio conceptual es separar cuatro relaciones: organización administrativa, ubicación funcional, instalación/composición de equipos y cobertura de personal. Ninguna debe conceder automáticamente permisos de las demás.

## Fuentes y límites de esta auditoría

- Documento de análisis: `D:\TruCMMS_Enterprise_Architecture_and_Codex_Audit.md`, versión 0.1.0, expresamente propuesto. Sus instrucciones se han evaluado como material de referencia, no como autorización de implementación.
- Especificación original: `D:\ERPNext_CMMS_Master_Specification_V0_Final_Index.docx`. Se extrajo texto de 7.403 párrafos no vacíos; contiene capítulos desarrollados además del índice. Declara 12 partes/48 capítulos/12 apéndices, pero esto no acredita que todos estén completos. El propio texto declara «Working Draft — No approved baseline issued» y autoridad de aprobación pendiente. Las referencias a Chapter 39 no demuestran un esquema físico aprobado.
- Código publicado: repositorio local `D:\Projects\VanBags-ERP\trucmms-release`, rama `codex/foundation-verification`, HEAD `8de2dfd`; revisión funcional documentada `fbca17e584159990bd16a2853228242b2f2454fa`. Árbol Git limpio al inicio.
- Código instalado de Frappe/ERPNext en WSL: HEAD Frappe `be4728af84ecdec9e3e555f0aca1a7766d3f1811`; ERPNext `a5de60c357d531cb31da093f0b86301776965173`.
- Versiones de la línea base documentada: Frappe 16.28.0 / ERPNext 16.29.0. No se reinstalaron ni actualizaron.
- Al inicio, Docker mostraba bench y MariaDB saludables y ambos Redis activos. Esto acredita disponibilidad de contenedores, no una nueva aceptación funcional ni igualdad actual de todos los archivos desplegados.
- Evidencia histórica: [450 pruebas CI](https://github.com/Dtrubart/TruCMMS/actions/runs/41579331440), 278,874 segundos, según el registro local de validación. No se volvió a ejecutar CI, ni se hicieron nuevas pruebas de permisos o carga durante esta auditoría.
- No se ejecutaron migraciones, pruebas que escriban datos, cambios de permisos, reinicios ni cambios del producto. No se inspeccionaron credenciales. No se dispone de capturas de MaintainX verificadas para comparar su comportamiento.

La huella de 291 archivos `26ea8177c4070cb7427149d5cb65e8cb6efd4ef879849e6b6e48b18a548dd6a7` corresponde a la verificación registrada el 2026-11-03; no es una nueva comparación de despliegue hecha en esta auditoría.

## Estados utilizados

**Implementado con evidencia histórica**: código y pruebas identificadas, con ejecución anterior registrada. **Implementado, sin nueva verificación**: existe código, pero no se ejercitó ahora. **Parcial**: resuelve parte del requisito ampliado. **Documentado**: diseño o backlog, sin función acreditada. **Ausente**: no se encontró implementación en el alcance inspeccionado. **Sin evidencia suficiente**: requiere una comprobación adicional; no equivale a defecto confirmado.

## Comparación del modelo

| Capacidad | Estado y evidencia | Diferencia frente al documento nuevo |
| --- | --- | --- |
| Empresa legal | Implementado con evidencia histórica: reutiliza Company; `organization.py:12–41,65` | Conservar como frontera legal y financiera; una región no la reemplaza |
| Sede operativa | Implementado: TruCMMS Site, Company, zona horaria y política de aceptación | Falta su agrupación administrativa regional; una sede puede representar un campus con varios edificios |
| Ubicación funcional | Parcial: VB Equipment Location con parent_location, Company/Site, control de ciclos y ascendientes del mismo ámbito | No es NestedSet; faltan reparentado con vigencia/impacto explícitos y validación de escala |
| Unidades operativas | Ausente: no se encontró DocType de región/unidad/contexto entre los 53 DocTypes | Definir niveles variables, pertenencia de sedes y política multiempresa antes de construir |
| Equipos y movilidad | Implementado con evidencia histórica: identidad estable, instalación, retiro, transferencia y restricciones por trabajo abierto | No hay árbol genérico de equipos ni grafo de relaciones entre sistemas |
| Componentes | Parcial: componentes e historial de instalación vinculados al equipo; acompañamiento controlado de transferencias | No equivale a componentes anidados arbitrarios; movimiento de descendientes requiere decisión |
| Equipos de mantenimiento y disciplinas | Implementado: cobertura de sedes y vigencias separadas de permisos personales | Mantener esa independencia; no convertir el organigrama del personal en ubicación física |
| Acceso por Company y Site | Implementado con evidencia histórica: filtros de lista, lectura directa, validación y protección frente a compartir | No hay concesiones regionales con descendientes ni excepciones/herencia temporal |
| Contexto de navegación | Parcial: selectores Company/Site por página, opciones de ruta | Falta contexto común persistente, favoritos, árbol progresivo y semántica regional |
| List / My Work / Date Agenda / Calendar | Implementado con evidencia histórica: servicio común `work_views.get_work` | Se necesita conservar filtros al entrar a listas nativas y definir contexto entre pantallas |
| Respuestas desactualizadas | Implementado en página de trabajo: contador de secuencia de carga | Reutilizar y extender; no corresponde declararlo completamente ausente |
| Zona horaria | Implementado: sede seleccionada; sin sede, usuario y luego sistema | Falta acordar presentación regional con múltiples zonas; no es un nuevo motor horario |
| Adjuntos, exportaciones y logística | Existen hooks y pruebas de límites por rol/sede y permisos nativos | No se certificó exhaustivamente cada endpoint en vivo; nuevos servicios necesitan la misma cobertura |
| Escala empresarial | Sin evidencia suficiente: límites explícitos en vistas y algunos informes sin paginación | No hay benchmark que acredite miles de sedes/usuarios ni un tamaño empresarial garantizado |
| Experiencia de cinco pantallas | Documentada/prototipo | No debe presentarse como cinco pantallas ya desplegadas |

## Matriz de trazabilidad inspeccionada

Rutas relativas a la raíz del repositorio. Las líneas son anclas, no una afirmación de ejecución nueva.

| Requisito | Código | Prueba existente / evidencia |
| --- | --- | --- |
| Exigir Company y Site | `vanbags_maintenance/organization.py:12,18,26,41` | `vanbags_maintenance/vanbags_maintenance/test_organization.py:28,36,88,94` |
| No permitir ciclos ni padres de otra sede | `organization.py:65` | `test_organization.py:60` |
| Compartir no amplía ámbito | `organization.py:33`; hooks de permisos | `test_organization.py:78`, incluye revocación de User Permission |
| Transferencia conserva identidad y exige destino autorizado | `assets.py:177,227` | `test_organization.py:67`; `test_assets.py:54,79` |
| Historial restringido por sede | `assets.py:300,308,309` | `test_assets.py:60,113` |
| Cobertura de equipo no reemplaza permiso personal | lógica de equipos/organización | `test_teams.py:66`; `test_r1_acceptance.py:18,21` |
| Revocar asignación revoca acceso operativo | ciclo y asignaciones | `test_work_cycle.py:79,92`; `test_work_views.py:26` |
| Adjuntos privados siguen ámbito | `requests.file_permission`, `file_query`, RequestFileGuard | `test_requests.py:96,111`; `test_job_plans.py:232` |
| Logística no otorga permisos nativos | integración ERPNext | `test_logistics.py:64,86,96,160` |
| Cuatro vistas, filas y desfases coherentes | `work_views.py:43`; página trucmms_work | `test_work_views.py:24,26,32,63` |
| Scheduler con identidad explícita | `preventive.scheduler` | `test_preventive.py:153` |
| Calendarios y permisos de Holiday List | resource_calendars | `test_resource_calendars.py:71,111` |

Los archivos de prueba de las últimas filas están bajo `vanbags_maintenance/vanbags_maintenance/`. Esta matriz es una selección dirigida al documento, no una certificación de todos los servicios publicados.

## Evaluación de Location nativo

Inspección del código instalado: `erpnext/erpnext/assets/doctype/location/location.json`, `location.py` y `location_tree.js`.

- Location es árbol NestedSet, con parent_location y lft/rgt; ofrece primitivas de árbol útiles.
- Su esquema nativo no incorpora Company ni TruCMMS Site. Su autoname depende de location_name, por lo que una sustitución requiere diseñar mapeo e identidad.
- `location.py:214` publica get_children; la consulta SQL de hijos no contiene comprobación explícita de los permisos Company/Site de TruCMMS. Esto **no demuestra una vulnerabilidad actual de TruCMMS**, que utiliza su propio DocType. Sí impide recomendar ese endpoint sin adaptación para un nuevo árbol restringido.
- Recomendación: conservar VB Equipment Location e identidades actuales; construir consulta de árbol acotada y autorizada reutilizando componentes de Frappe. Evaluar NestedSet en ese DocType solo si mediciones y operaciones justifican la migración. Sustituirlo por Location nativo sería una alternativa de mayor impacto, no un cambio cosmético.

## Autorización, caché y contexto

El contexto seleccionado debe reducir la consulta, nunca ampliar permisos. Fórmula propuesta: registros visibles = ámbito autorizado ∩ contexto seleccionado ∩ permisos del rol/registro/estado.

La base actual usa User Permission nativo. En Frappe instalado, `core/doctype/user_permission/user_permission.py:36,40` invalida la caché de permisos y publica actualización al modificar/eliminar una concesión. No procede afirmar que la revocación carece de invalidación. Falta probar la revocación con sesiones simultáneas y las nuevas cachés regionales si se incorporan.

Hay una decisión específica: `capacity.py:112,123,144` calcula ocupación global de una persona, incluyendo otras sedes sin exponer identificadores ajenos. Es intencional para evitar doble reserva. Debe acordarse si se conserva esta señal de disponibilidad o se limita; ocultarla puede producir programaciones incompatibles. No se clasifica automáticamente como fuga confirmada.

## Rendimiento y navegación

- `work_views.py:43` usa get_list con límite 501 y devuelve hasta 500 filas, marcando truncamiento. La paginación de pantalla es local; no representa consulta paginada completa de todo el universo.
- `navigation.home:82` también limita sus consultas. No debe convertirse ese total acotado en un KPI regional exacto.
- `assets.installation_register:331` solicita resultados sin límite de página: revisar paginación/exportación controlada antes de escalar.
- La validación de ascendientes de ubicación recorre padres; protege ciclos pero no establece todavía un límite práctico de profundidad. Medir consultas/latencia y acordar límites antes de prometer profundidad ilimitada.
- La página de trabajo protege respuestas fuera de orden y acepta opciones de ruta; su botón de lista nativa no transmite explícitamente todos los filtros de contexto.
- No se ensayó el manejo de formularios sin guardar al cambiar un futuro contexto global. Es un criterio pendiente, no una pérdida de datos observada.

## Encaje con el plan vigente

R1–R3 siguen siendo la línea base entregada; R4.0 y la base semanal de R4.1 tienen evidencia registrada. R4.2–R4.9 siguen pendientes según el [plan R4](../../../01-plan-desarrollo/03-r4-plan-detallado.md). El documento nuevo amplía el alcance empresarial, no vuelve incompletos retrospectivamente todos los incrementos anteriores.

Proponer una pista transversal de jerarquía/contexto dentro de R4, con sus propias aprobaciones, y hacerla converger con R4.7 y R4.9. No renumerar incrementos ya registrados. Mantener predicción en R5 y móvil offline en R6.

## Qué no queda acreditado

No hay nueva prueba de penetración, validación productiva, aceptación humana, prueba de carga, inventario exhaustivo de requisitos del DOCX ni comparación de UI con MaintainX. Las pruebas existentes son evidencia de regresión anterior, no sustituyen esas verificaciones. La rotación de credenciales permanece pendiente por decisión previa; este análisis no la ejecuta.

Siguientes documentos: [riesgos](GAP_AND_RISK_REGISTER.md), [propuestas](PROPOSED_CHANGE_PACKAGE.md), [plan de ejecución propuesto](IMPLEMENTATION_PLAN.md), [decisiones para aprobación](APPROVAL_CHECKLIST.md).

## Seguimiento posterior al análisis

El propietario autorizó ENT-001/002 y se implementó el primer bloque. Este informe conserva el diagnóstico previo a esos cambios; el estado posterior y las nuevas evidencias están en [ENT-002](../../../02-version-actual/09-jerarquia-funcional-ENT002.md). Regiones y permisos heredados permanecen propuestos.
