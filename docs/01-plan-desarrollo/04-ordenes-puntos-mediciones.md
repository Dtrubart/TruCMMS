# Órdenes, puntos de trabajo y mediciones

**Diseño acordado en dirección general; implementación en curso. No describe la versión publicada.**

## Estructura

Orden → puntos de trabajo → actividades, resultados, lecturas, evidencias y hallazgos. La orden mantiene una empresa, una sede, ubicación de alcance y responsabilidades/estados comunes. Un activo es opcional.

| Punto | Identidad y ejemplo |
| --- | --- |
| Activo | Equipo estable: AHU1, camión, trituradora |
| Componente | Identidad e instalación: motor o rodamiento |
| Área | Ubicación funcional: cuarto mecánico, pasillo, cubierta |
| Punto de medición | Identidad estable en ubicación/sistema: entrada/salida de well water o suministro eléctrico; sin activo ficticio |
| Referencia | Ubicación y descripción para trabajo ocasional: sellado junto a puerta norte |

Para acumular lecturas o historial repetido se requiere identidad estable. Una descripción ocasional no sustituye ese registro.

## Ubicación y división del trabajo

La ubicación de alcance agrupa el trabajo; cada punto conserva su ubicación específica dentro de la misma sede. Una ronda de edificio puede recorrer varios cuartos mecánicos. En flotas/campo debe precisarse el contexto de intervención/base sin afirmar una instalación física permanente inexistente.

Una orden multipunto comparte programación, autorización y cierre. Una reparación con otra programación, responsabilidad o aceptación genera trabajo vinculado al hallazgo. La ronda no se convierte automáticamente en la reparación de su máquina fallida.

## Mediciones

Punto → variable/medidor → valor/unidad → fecha → persona → actividad/orden de origen. Distinguir contadores acumulativos (km, horas, kWh, volumen), condición (temperatura/espesor) y tasas/valores instantáneos (caudal, potencia u otras variables configuradas).

Captura única: una lectura de actividad alimenta el historial del punto y se resume en General. La orden conserva la referencia histórica usada; lecturas posteriores no la sustituyen. Correcciones/reinicios deben reutilizar la auditoría de R2. El resumen indica valor, unidad, fecha/origen y antigüedad pertinente; un dato ausente o antiguo no se presenta como actual válido.

## Inspección

Pass / Alarm / Failure, además de Pendiente / No inspeccionado / No aplica. La plantilla define motivos/evidencias. Omitir no equivale a Pass. Resultado de inspección, estado del activo y estado de orden son distintos; sus efectos automáticos requieren reglas explícitas.

Ejemplo: ronda diaria del edificio → Mechanical Room 1 (AHU1/AHU2), Mechanical Room 2 (área/equipos), well water (entrada/salida). Lista e instrucciones quedan versionadas por ejecución.

## Compatibilidad

Conservar solicitudes, preventivos, equipos, costos y lecturas existentes. Distinguir contratos anteriores; una ubicación histórica desconocida requiere revisión, no una ubicación inventada ni la ubicación actual del activo tomada como pasada.

R3 conserva totales por orden. Atribuir materiales/costos a punto/actividad necesita reglas conciliadas, sin duplicar libros nativos. Revisión de alcance autorizado, tiempos por participante y distribución de costos requieren contrato específico.
