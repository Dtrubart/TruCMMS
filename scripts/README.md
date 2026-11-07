# Verificación visual ENT-002

`verify-ent002-ui.mjs` comprueba la integración real de la página de ubicaciones con Frappe Tree. Requiere Node, Playwright disponible y un navegador compatible instalado. No instala dependencias ni inicia servicios.

Configurar en el entorno del proceso:

| Variable | Uso |
| --- | --- |
| `TRUCMMS_UI_PASSWORD` | Contraseña de la cuenta de verificación; obligatoria, no guardarla en el repositorio |
| `TRUCMMS_UI_USER` | Usuario con acceso administrativo a la pantalla; por defecto Administrator |
| `TRUCMMS_BASE_URL` | Por defecto `http://test.vanbags.localhost:8100` |
| `TRUCMMS_PLAYWRIGHT_MODULE` | Opcional: ruta a un módulo Playwright existente; por defecto resuelve `playwright` |
| `TRUCMMS_BROWSER_CHANNEL` | Opcional: canal del navegador; Windows usa msedge por defecto |
| `TRUCMMS_UI_ARTIFACT_DIR` | Opcional: carpeta de evidencias; por defecto `test-results/ent002` |

Con las variables configuradas de forma privada:

```text
node scripts/verify-ent002-ui.mjs
```

El sitio debe contener al menos una ubicación raíz activa para consultar. El script inicia sesión, espera un nodo real con la identidad esperada, lo abre desde el árbol, comprueba breadcrumb, diálogo de cambio, ficha nativa, búsqueda y diseño de 390 px. No confirma cambios de jerarquía ni crea datos operativos. El inicio de sesión y las preferencias nativas de Desk pueden registrar actividad de usuario.

Genera dos capturas y un resumen JSON. `test-results/` está excluido de Git porque las capturas pueden mostrar información del sitio. No publicar capturas o logs sin revisar su contenido.

Esta prueba local complementa la suite backend de GitHub CI; el workflow actual no ejecuta Playwright. La presencia del contenedor `.tree` por sí sola no acredita que se hayan renderizado sus nodos.

## Organización operativa ENT-003

`ent003-ui-fixture.py` crea una región, dos distritos, dos sedes y un lector restringido, exclusivamente en `test.vanbags.localhost` o `test_site` con `allow_tests` activo. Requiere la Company de pruebas preparada por las pruebas de integración. No usar datos de sedes operativas existentes.

Ejecutar con el Python del Bench desde su carpeta `sites`, o configurar `TRUCMMS_SITES_DIR`. `TRUCMMS_TEST_SITE` selecciona uno de los sitios de prueba admitidos. `TRUCMMS_ORG_FIXTURE_FILE` debe apuntar a un archivo privado fuera del repositorio: guarda las identidades y contraseña sintéticas, con permisos 0600.

```text
python /ruta/al/repositorio/scripts/ent003-ui-fixture.py seed
node scripts/verify-ent003-ui.mjs
python /ruta/al/repositorio/scripts/ent003-ui-fixture.py clean
```

Para Node, el archivo de fixture debe ser accesible por su sistema de archivos. Se usan las mismas variables privadas de autenticación/navegador del ensayo ENT-002. La carpeta de resultados predeterminada es `test-results/ent003`.

La comprobación exige nodos reales, confirma una pertenencia en una sede sintética y la restaura, verifica que el lector no vea la rama/sede ajena y comprueba rechazos de detalle y título por API. `clean` retira únicamente las identidades de ese fixture; la actividad de autenticación nativa puede conservar su auditoría. No ejecutar el ensayo si una ejecución anterior dejó una fixture sin revisar.
