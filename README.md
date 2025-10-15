# Image -> Regions JSON -> Turtle Drawer

Este proyecto contiene dos piezas:

1. `tools/image_to_regions_json.py`: Convierte una imagen (PNG/JPG) en un archivo `.json` con una lista de regiones `{ contour, color }`.
2. `draw_from_json.py`: Dibuja ese JSON usando `turtle`.

## Instalación

En Windows PowerShell, desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Generar un JSON desde una imagen

```powershell
# Ejemplo: reducir colores a 16, simplificar contornos, y opcionalmente redimensionar
python .\tools\image_to_regions_json.py --input .\resources\mi_imagen.jpg --output .\resources\mi_imagen.json --colors 16 --epsilon 0.01 --min-area 50 --resize-longest 800
```

Parámetros útiles:
- `--colors/-k`: número de colores para k-means (2-64). Más colores = más fidelidad y JSON más grande.
- `--epsilon`: fracción del perímetro para simplificación (0.005-0.03 típico). Menor = más detalle.
- `--min-area`: descarta regiones pequeñas (ruido) por debajo de ese tamaño en píxeles.
- `--resize-longest`: redimensiona la imagen para que su lado más largo sea este valor (0 = no redimensionar).

El JSON generado tendrá la forma:
```json
[
  { "contour": [[x,y],...], "color": [r,g,b] },
  ...
]
```

## Dibujar el JSON con turtle

Puedes usar tu `draw_from_json.py`. Asegúrate de que apunte a tu JSON o pásale la ruta que quieras (si lo adaptas para CLI). Por ejemplo, editando la ruta al final del archivo para usar `resources/mi_imagen.json`.

Para que la ventana se mantenga abierta, usa la versión que espera a click (si la tienes) o ejecuta desde una terminal interactiva.

## Consejos de calidad
- Ajusta `--colors` hasta obtener una paleta que represente bien la imagen sin crear demasiadas regiones.
- Usa `--epsilon` bajo para conservar detalles o más alto para suavizar polígonos y reducir tamaño.
- Sube `--min-area` si aparecen muchas motas pequeñas.
- Redimensionar (`--resize-longest`) ayuda a controlar el tamaño del JSON y la suavidad del resultado.

## Problemas comunes
- `ImportError: cv2`: instala dependencias con `pip install -r requirements.txt` dentro del entorno virtual activo.
- Ventana turtle se cierra rápido: ejecuta desde PowerShell y/o usa `screen.exitonclick()`.