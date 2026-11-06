# TruCMMS — documentación consolidada

Actualización: **2026-11-06**. TruCMMS es la app Frappe/ERPNext; VanBags es el negocio de ejemplo.

| Rama | Contenido | Entrada |
| --- | --- | --- |
| **1. Plan de implementación y desarrollo** | Qué se construirá, secuencia, decisiones y trabajo en curso | [Plan](01-plan-desarrollo/README.md) |
| **2. Versión actual implementada** | Qué está publicado y verificado, cómo funciona y sus límites | [Versión actual](02-version-actual/README.md) |

La línea base de aplicación de la rama 2 es `fbca17e584159990bd16a2853228242b2f2454fa`, con **450 pruebas CI aprobadas**. Incluye R0–R3, el modelo R4.0 de alcance/puntos/mediciones y los calendarios semanales de R4.1. No equivale a aceptación humana ni a producción.

La implementación, evidencia local, CI y puertas pendientes de R4.0 se registran en el [detalle R4.0](02-version-actual/06-r4-alcance-local.md). El nuevo layout completo sigue en propuesta visual. R4 global no está cerrado.

Los archivos antiguos de documentación conservan su alcance histórico. Estos índices determinan vigencia y separan propuesta, desarrollo, verificación y aceptación operativa.

## Mantenimiento documental

Las propuestas permanecen en la rama 1. Tras implementar y verificar un incremento, se actualizan la rama 2, revisión y evidencias. Las actas históricas se conservan; no se reescriben para atribuirles funciones posteriores.

La exportación consolidada contiene este índice, ambas ramas, contratos técnicos y la especificación original como referencia. Bases, logs crudos, datos operativos, credenciales y configuración secreta permanecen fuera del paquete.

## Incremento local posterior

[ENT-002: arbol funcional e historial](02-version-actual/09-jerarquia-funcional-ENT002.md), sobre la base anterior, autorizado mediante [ENT-001](01-plan-desarrollo/08-jerarquia-y-contexto-ENT001.md). Primer commit ENT-002 publicado en la rama de desarrollo; corrección visual y CI en verificación. La CI anterior no acredita automáticamente este incremento. Consultar su acta para estado de despliegue, recuperacion y pruebas locales.
