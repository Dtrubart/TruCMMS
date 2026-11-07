# Decisiones para aprobar — arquitectura empresarial

Actualización 2026-11-05: el propietario autorizó comenzar ENT-PROP-001 y ENT-PROP-002 tras revisar el plan detallado. El alcance ejecutable y sus límites se registran en [ENT-001](../../../01-plan-desarrollo/08-jerarquia-y-contexto-ENT001.md). Los demás paquetes siguen pendientes; las casillas siguientes no implican aprobación regional global.

## Ocho decisiones del modelo

- [ ] **1. Niveles administrativos.** Aprobar unidades opcionales, profundidad variable y etiquetas configurables; sin esquema obligatorio país/provincia/ciudad. Una sede con pertenencia primaria en la primera versión. Precisar límites máximos con medición.
- [ ] **2. Sede y Company.** Conservar una Company legal por sede; primera versión regional dentro de una Company. Diferir agregación multiempresa; nunca habilitar transacciones cruzadas mediante contexto.
- [ ] **3. Ubicaciones.** Conservar VB Equipment Location e IDs; árbol autorizado y reparentado controlado. Elegir adyacencia inicial recomendada, evaluación NestedSet propia o migración nativa independiente.
- [ ] **4. Equipos/componentes.** Mantener instalación separada de composición y conexiones de sistemas; no trasladar descendientes automáticamente. Aprobar primero diseño de casos antes de añadir árbol genérico.
- [ ] **5. Acceso.** Mantener Company + Site + rol/registro/estado como base. El contexto solo reduce alcance. Decidir si se autoriza desarrollar grants regionales; definir descendientes futuros, revocación y cobertura de equipos humanos. Decidir conservación de ocupación global anonimizada para evitar doble reserva.
- [ ] **6. UX y tiempo.** Una sede entra directamente; multisede conserva preferencia válida; técnico prioriza My Work. Definir opción «todas mis sedes», zona visible en región y protección de formularios sin guardar. Creación regional requiere sede explícita.
- [ ] **7. Releases.** Integrar jerarquía/contexto como pista transversal de R4, vinculada a R4.7/R4.9; no reabrir ni renumerar R1–R3. Predicción R5, offline R6. Confirmar si se prioriza esta pista antes de R4.2.
- [ ] **8. Migración/aceptación.** Preservar IDs e historia; ensayo y restauración aislados antes de migrar. Acordar volumen/umbrales de prueba, responsables del piloto y criterios de rollback.

## Aprobación por paquete

| Propuesta | Decisión pendiente | Recomendación |
| --- | --- | --- |
| ENT-PROP-001 | Aprobado para el primer bloque | Aprobar primero: contrato y decisiones |
| ENT-PROP-002 | Aprobado con adyacencia e IDs actuales | Primer desarrollo: ubicaciones y navegación de árbol seguras |
| ENT-PROP-003 | Aprobado para organización opcional el 2026-11-06 | Después: organización opcional por Company |
| ENT-PROP-004 | Aprobar / ajustar / diferir | Resolver ámbitos; grants regionales requieren política específica |
| ENT-PROP-005 | Aprobar / ajustar / diferir | Contexto común; posible entrega inicial solo Company/Site |
| ENT-PROP-006 | Aprobar / ajustar / diferir | Puerta de pruebas y escala de los paquetes autorizados |
| ENT-PROP-007 | Aprobar / ajustar / diferir | Diferir implementación; aprobar análisis de casos si es prioritario |

## Forma de autorizar un siguiente incremento

Registrar paquete(s), decisiones modificadas, entorno permitido, alcance de migración, pruebas y criterio de aceptación. Ejemplo para revisión: «Aprobar ENT-PROP-001 y diseñar ENT-PROP-002 conservando VB Equipment Location; sin desarrollar unidades regionales ni alterar permisos todavía». Esta frase es un ejemplo, no una aprobación registrada.

Una autorización de análisis/diseño no autoriza automáticamente migraciones, reinicios, datos demo, cambios de credenciales, publicación o todos los demás paquetes. La rotación de credenciales continúa pendiente por decisión previa.

## Documentos de apoyo

- [Estado actual y evidencias](CURRENT_STATE_AUDIT.md)
- [Brechas y riesgos](GAP_AND_RISK_REGISTER.md)
- [Alcance de cada propuesta](PROPOSED_CHANGE_PACKAGE.md)
- [Secuencia, pruebas y migración](IMPLEMENTATION_PLAN.md)

El propietario autorizó ENT-003 al pedir el siguiente paso. Se registra en [su contrato](../../../01-plan-desarrollo/09-organizacion-operativa-ENT003.md); ENT-004 a 007 siguen pendientes.
