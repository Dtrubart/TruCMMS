# Evidencia y limitaciones

| Entrega | Revisión | Evidencia |
| --- | --- | --- |
| R2 | `fb0c068dc10e19450471e73acbdc75ce777c5a6d` | [338 pruebas CI](https://github.com/Dtrubart/TruCMMS/actions/runs/40640071255) |
| R3 | `7666406fcb90c60a6bec5ae2aaba5956bc5ecd93` | [407 pruebas, 246.974 s](https://github.com/Dtrubart/TruCMMS/actions/runs/41155848864), concurrencia y recuperación poblada |
| R4.1 inicial | `2c5f9ee59b25bbe5a820869c530e3165cd0c49ba` | [418 pruebas, 183.267 s](https://github.com/Dtrubart/TruCMMS/actions/runs/41181723132), instalación limpia y regresión |
| R4.0 alcance | `edd2353b2fd6e53528393762ababee8a4bfb9ae3` | [434 pruebas, 133.320 s](https://github.com/Dtrubart/TruCMMS/actions/runs/41559626517), instalación limpia, permisos e integración |

Las 11 pruebas específicas de capacidad (8.455 s) se solapan con la suite ampliada; no se suman como pruebas únicas.

## Estado comprobado el 2026-10-31

DEV/TEST: política `R4.1-capacity`; huella `452f0399ee84f6a4c8933ea9c9ea3b82ede62ec5e78e857224b9b9f5274f0428`; 261 archivos coincidentes entre publicación y fuente activa. Preservados 514 documentos CMMS, ocho hashes de archivos, conteos de inventario/contabilidad/compras y roles de siete perfiles demo. DEV tenía cero datos operativos; no se cargaron ventanas demo.

Esa evidencia describe la entrega inicial de capacidad, no las funciones R4.0 posteriores.

## Estado comprobado el 2026-11-02

DEV/TEST: política `R4.0-work-scope`; huella `6b0aad4adce55e8f604dd51ec9f6ca577b2502e77c4fc4607aebbac523ce317e`; 276 archivos de paquete coincidentes. Los 514 documentos de TEST, ocho adjuntos y conteos nativos siguen intactos. No se cargaron puntos, revisiones ni lecturas R4 operativas en DEV/TEST.

CI limpio: 434/434 aprobadas. Última regresión local: 433/434, 483.188 s; el único fallo fue `test_equipment_transfer_carries_components_and_meter_scope`, por un instante de movimiento no posterior a la instalación. Su repetición aislada pasó en 4.004 s. Se conserva esta diferencia; no se declara que la corrida local completa haya terminado sin errores. Recuperación de respaldo anterior y migración aislada: ver el [registro R4.0](06-r4-alcance-local.md).

La [recuperación poblada del nuevo historial R4.0](07-r4-recuperacion-poblada.md) está verificada: 542 documentos CMMS, nueve adjuntos, puntos/revisiones/lecturas y corrección conservados; reintentos sin duplicación y permisos backend/HTTP comprobados. Se completó sin cambios del producto ni repetición de CI.

## Interfaz y concurrencia

R3: proyección, compra/salida, conciliación, costos, CSV, técnico asignado/no asignado, impresión y móvil. R4.1: página/lista, siete días, Sin configurar, permisos, escritorio/móvil y ausencia de errores JavaScript. TEST no recibió transacciones operativas de estas comprobaciones.

Con conexiones independientes se verificó una identidad por reintento y una única salida/devolución enviada frente a competidores. Un deadlock transitorio requirió reintentar; no se promete éxito simultáneo sin reintento.

## Recuperación R3

Piloto sintético y restauración en destino nuevo: documentos CMMS/nativos, cantidades/costos/libros, roles/permisos/configuración de cifrado y **632 archivos archivados** coincidentes. Navegador y credenciales sintéticas comprobados. La verificación admite ausencia de clave específica del sitio y compara configuración efectiva, sin inventar claves.

## Límites

- Aceptación humana y producción pendientes.
- Cinco pantallas completas, recorridos/formatos y captura por actividad todavía en desarrollo/diseño R4; multipunto y medidores de instalaciones incluidos en R4.0.
- Capacidad informativa, ventanas explícitas y duración completa por participante; sin optimizador ni libro histórico congelado.
- Stock es fotografía orientativa; no reserva ni asigna suministro futuro.
- Salida neta no mide independientemente consumo físico.
- Costos excluyen impuestos/pagos/previsiones; permiso faltante implica total incompleto.
- Recogida autenticada/imprimible, sin proveedor externo de firma.
- Automatización preventiva opt-in, con identidad/datos válidos; no autoriza órdenes automáticamente.
- Sin offline, predicción ni certificación/calibración especializada.

Los logs crudos, capturas, manifiestos y respaldos se custodian fuera del paquete de análisis. La exportación aporta contratos, resultados y enlaces CI; excluye bases, contraseñas, `.env`, configuraciones secretas y datos operativos de clientes.
