# TruCMMS — documentación consolidada

Actualización: **2026-11-07**. TruCMMS es la app Frappe/ERPNext; VanBags es el negocio de ejemplo.

| Rama | Contenido | Entrada |
| --- | --- | --- |
| **1. Plan de implementación y desarrollo** | Qué se construirá, secuencia, decisiones y trabajo en curso | [Plan](01-plan-desarrollo/README.md) |
| **2. Versión actual implementada** | Qué está publicado y verificado, cómo funciona y sus límites | [Versión actual](02-version-actual/README.md) |

La línea base de aplicación de la rama 2 es `60cd0649700edf6c9b924fd7b9c4a76585b34d6f`, con **[486 pruebas CI aprobadas](https://github.com/Dtrubart/TruCMMS/actions/runs/42341253571)**. Incluye R0–R3, el modelo R4.0 de alcance/puntos/mediciones los calendarios semanales de R4.1 y el árbol funcional con historial ENT-002 y la organización opcional ENT-003. No equivale a aceptación humana ni a producción.

La implementación, evidencia local, CI y puertas pendientes de R4.0 se registran en el [detalle R4.0](02-version-actual/06-r4-alcance-local.md). El nuevo layout completo sigue en propuesta visual. R4 global no está cerrado.

Los archivos antiguos de documentación conservan su alcance histórico. Estos índices determinan vigencia y separan propuesta, desarrollo, verificación y aceptación operativa.

## Mantenimiento documental

Las propuestas permanecen en la rama 1. Tras implementar y verificar un incremento, se actualizan la rama 2, revisión y evidencias. Las actas históricas se conservan; no se reescriben para atribuirles funciones posteriores.

La exportación consolidada contiene este índice, ambas ramas, contratos técnicos y la especificación original como referencia. Bases, logs crudos, datos operativos, credenciales y configuración secreta permanecen fuera del paquete.

## Incremento local posterior

[ENT-002: arbol funcional e historial](02-version-actual/09-jerarquia-funcional-ENT002.md), sobre la base anterior, autorizado mediante [ENT-001](01-plan-desarrollo/08-jerarquia-y-contexto-ENT001.md). ENT-002 y su corrección visual están publicados en la rama de desarrollo; instalación limpia y 466 pruebas backend aprobadas en CI. La aceptación humana permanece separada. Consultar su acta para estado de despliegue, recuperacion y pruebas locales.

[ENT-003: organización operativa opcional](02-version-actual/10-organizacion-operativa-ENT003.md): DEV/TEST, instalación limpia, 486 pruebas CI, recuperación poblada y pruebas visuales locales verificadas. Las sedes siguen sin agrupación automática; aprobación humana y ENT-004/005 separadas.
