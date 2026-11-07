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
