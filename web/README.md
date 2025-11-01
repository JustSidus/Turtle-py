
Pequeña app web que dibuja una rosa a partir de un JSON de regiones.

## Probar localmente

1. Abre una terminal en esta carpeta (`web/`).
2. Inicia un servidor HTTP (necesario para que `fetch` funcione):
   - Con Python 3:
     - Windows PowerShell:
       - `python -m http.server 5500`
   - Con Node.js:
     - `npx serve -l 5500`
3. Abre http://localhost:5500/ y pulsa el botón “Haz clic para que florezca”.

Si ves un aviso sobre `file://`, significa que abriste `index.html` directamente sin servidor; usa el paso 2.

## Estructura

- `index.html`: Página principal y UI.
- `styles.css`: Estilos.
- `main.js`: Render animado en `<canvas>` y carga del JSON.
- `resources/rosas.json`: Datos de la rosa.

## Publicar

- GitHub Pages (branch `gh-pages`):
  - Sube el contenido de `web/` como raíz del sitio (lo que esté dentro de `web/` debe quedar en la raíz del branch de Pages).
  - La app busca `./resources/rosas.json`, así que asegúrate de subir también `web/resources/`.
- Azure Static Web Apps:
  - App location: `web`
  - No build task requerido.

## Notas

- El script acepta tanto JSON plano `[ { contour, color } ]` como `{ regions: [ ... ] }`.
- Si el JSON es grande, la animación tarda un poco; ajusta la velocidad con el deslizador.
