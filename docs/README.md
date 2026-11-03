# TruCMMS — documentación consolidada

Actualización: **2026-11-02**. TruCMMS es la app Frappe/ERPNext; VanBags es el negocio de ejemplo.

| Rama | Contenido | Entrada |
| --- | --- | --- |
| **1. Plan de implementación y desarrollo** | Qué se construirá, secuencia, decisiones y trabajo en curso | [Plan](01-plan-desarrollo/README.md) |
| **2. Versión actual implementada** | Qué está publicado y verificado, cómo funciona y sus límites | [Versión actual](02-version-actual/README.md) |

La línea base de aplicación de la rama 2 es `2c5f9ee59b25bbe5a820869c530e3165cd0c49ba`, con **418 pruebas CI aprobadas**. Incluye R0–R3 y la primera entrega de capacidad de R4.1. No equivale a aceptación humana ni a producción.

**R4.0 no está incluido en esa línea base publicada.** Su implementación posterior en DEV/TEST y sus puertas pendientes se registran en el [candidato local R4.0](02-version-actual/06-r4-alcance-local.md). El nuevo layout completo sigue en propuesta visual. Un despliegue local no equivale a CI remoto aprobado ni a aceptación productiva.

Los archivos antiguos de documentación conservan su alcance histórico. Estos índices determinan vigencia y separan propuesta, desarrollo, verificación y aceptación operativa.

## Mantenimiento documental

Las propuestas permanecen en la rama 1. Tras implementar y verificar un incremento, se actualizan la rama 2, revisión y evidencias. Las actas históricas se conservan; no se reescriben para atribuirles funciones posteriores.

La exportación consolidada contiene este índice, ambas ramas, contratos técnicos y la especificación original como referencia. Bases, logs crudos, datos operativos, credenciales y configuración secreta permanecen fuera del paquete.
