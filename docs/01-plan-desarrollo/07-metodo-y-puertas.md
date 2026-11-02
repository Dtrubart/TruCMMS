# Implementación, validación y mantenimiento documental

## Estados separados

Diseño: propuesto/acordado/pendiente de precisión. Desarrollo: pendiente/en desarrollo/implementado. Verificación: sin probar/en prueba/aprobado/fallido. Aceptación operativa y producción se registran aparte. Publicar una revisión no la convierte en aprobación productiva.

## Por incremento

1. Definir comportamiento, dependencias, datos afectados y límites.
2. Acordar criterios de aceptación y compatibilidad.
3. Conservar respaldo y cambios locales; preparar migración explícita.
4. Implementar un tramo verificable y ejecutar pruebas específicas.
5. Congelar código y ejecutar integración/CI aplicables.
6. Verificar interfaz, roles, datos y huella; para candidatos, recuperación poblada.
7. Registrar revisión, evidencia y límites; actualizar la versión actual solo con lo verificado.

Las suites completas se repiten ante cambio, fallo o preocupación nueva. Evidencias pertenecen a una revisión exacta y los conteos solapados no se suman como pruebas únicas.

## Documentación

La rama 1 conserva pendientes/decisiones; la rama 2 recibe los contratos, guía, diccionario y evidencia del nuevo incremento verificado. Las actas antiguas mantienen fecha/alcance. La exportación identifica revisión y manifiesto. Una actualización documental puede versionarse sin incorporar código funcional no terminado del mismo checkout.

El cierre técnico DEV/TEST no sustituye aceptación de usuarios ni preparación de infraestructura, cuentas, custodia, recuperación y operación productivas.
