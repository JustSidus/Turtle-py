# Turtle + Web: cómo ejecutar

Este repo dibuja una rosa (u otras figuras) desde un archivo JSON de regiones, tanto en web como en Python.

## Ejecutar la versión web (recomendada)

1) Desde la carpeta `web/`, levanta un servidor local:

```powershell
cd .\web
python -m http.server 5500
```

2) Abre en el navegador:
- http://localhost:5500/

3) Haz clic en el botón y ajusta la velocidad. La app carga `./resources/rosas.json` automáticamente.

Publicación: el repo incluye un workflow de GitHub Actions que publica `web/` en GitHub Pages. Ver `README_PAGES.md`.

## Ejecutar scripts de Python

Crear entorno e instalar dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

1) Convertir imagen → JSON de regiones:

```powershell
python .\tools\image_to_regions_json.py --input .\resources\mi_imagen.jpg --output .\resources\mi_imagen.json --colors 16 --epsilon 0.01 --min-area 50 --resize-longest 800
```

2) Dibujar JSON (turtle/Tkinter):

```powershell
python .\draw_from_json.py .\resources\rosas.json
```

Notas rápidas:
- Los JSON pueden ser una lista `[ { contour, color }, ... ]` o `{ regions: [...] }`.
- Si la ventana se cierra rápido, ejecuta desde PowerShell o usa una versión que espere click para cerrar.

## Estructura mínima
- `web/` (index.html, styles.css, main.js, resources/)
- `tools/image_to_regions_json.py`
- `draw_from_json.py`
- `resources/` (ejemplos e imágenes)