import argparse
import json
import os
from typing import List, Tuple

import cv2
import numpy as np


def resize_longest_side(img: np.ndarray, longest: int) -> np.ndarray:
    if longest is None or longest <= 0:
        return img
    h, w = img.shape[:2]
    current_longest = max(h, w)
    if current_longest <= longest:
        return img
    scale = float(longest) / float(current_longest)
    new_w, new_h = int(round(w * scale)), int(round(h * scale))
    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    return cv2.resize(img, (new_w, new_h), interpolation=interp)


def quantize_kmeans_rgb(img_rgb: np.ndarray, k: int, attempts: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    h, w = img_rgb.shape[:2]
    samples = img_rgb.reshape((-1, 3)).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    compactness, labels, centers = cv2.kmeans(
        samples, k, None, criteria, attempts, cv2.KMEANS_PP_CENTERS
    )
    labels = labels.reshape((h, w))
    centers = centers.astype(np.uint8)  # RGB centers in [0..255]
    return labels, centers


def find_contours(mask: np.ndarray) -> List[np.ndarray]:
    # Limpieza ligera para evitar fragmentación
    kernel = np.ones((3, 3), np.uint8)
    proc = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    proc = cv2.morphologyEx(proc, cv2.MORPH_CLOSE, kernel, iterations=1)
    cnts_info = cv2.findContours(proc, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = cnts_info[0] if len(cnts_info) == 2 else cnts_info[1]
    return contours


def simplify_contour(cnt: np.ndarray, epsilon_frac: float) -> np.ndarray:
    peri = cv2.arcLength(cnt, True)
    eps = max(1.0, epsilon_frac * peri)
    approx = cv2.approxPolyDP(cnt, epsilon=eps, closed=True)
    return approx


def generate_regions_from_image(
    input_path: str,
    output_path: str,
    k_colors: int = 16,
    min_area: int = 50,
    epsilon_frac: float = 0.01,
    resize_longest: int = 0,
):
    # Leer imagen
    bgr = cv2.imread(input_path, cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(f"No se pudo abrir la imagen: {input_path}")

    # Redimensionar opcionalmente
    bgr = resize_longest_side(bgr, resize_longest)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]

    # KMeans en RGB
    labels, centers_rgb = quantize_kmeans_rgb(rgb, k=k_colors)

    regions = []

    for idx, center in enumerate(centers_rgb.tolist()):
        mask = np.uint8(labels == idx) * 255
        if cv2.countNonZero(mask) < min_area:
            continue
        contours = find_contours(mask)
        if not contours:
            continue

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            approx = simplify_contour(cnt, epsilon_frac=epsilon_frac)
            pts = approx.reshape(-1, 2)

            # Filtrar puntos fuera de límites y asegurar mínimo 3 puntos
            pts_list = []
            for x, y in pts:
                xi = int(x)
                yi = int(y)
                if 0 <= xi < w and 0 <= yi < h:
                    pts_list.append([xi, yi])
            if len(pts_list) < 3:
                continue

            r, g, b = [int(max(0, min(255, c))) for c in center]
            regions.append({
                "contour": pts_list,
                "color": [r, g, b]
            })

    # Ordenar por área descendente (opcional, ayuda a pintar grandes primero)
    def contour_area(region_obj):
        cnt = np.array(region_obj["contour"], dtype=np.int32).reshape(-1, 1, 2)
        return float(cv2.contourArea(cnt))

    regions.sort(key=contour_area, reverse=True)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(regions, f, ensure_ascii=False, indent=2)


def build_argparser():
    p = argparse.ArgumentParser(
        description="Convierte una imagen en un JSON de regiones (contour + color RGB) compatible con draw_from_json.py"
    )
    p.add_argument("--input", "-i", required=True, help="Ruta de la imagen de entrada (png, jpg, etc.)")
    p.add_argument("--output", "-o", required=True, help="Ruta del JSON de salida")
    p.add_argument("--colors", "-k", type=int, default=16, help="Número de colores para k-means (>=2)")
    p.add_argument("--min-area", type=int, default=50, help="Área mínima de contorno en píxeles")
    p.add_argument("--epsilon", type=float, default=0.01, help="Fracción del perímetro para simplificación de contornos (0.005-0.03)")
    p.add_argument("--resize-longest", type=int, default=0, help="Redimensiona para que el lado más largo sea este valor (0 = no redimensionar)")
    return p


def main():
    args = build_argparser().parse_args()
    if args.colors < 2:
        raise ValueError("--colors debe ser >= 2")
    if args.epsilon <= 0:
        raise ValueError("--epsilon debe ser > 0")
    generate_regions_from_image(
        input_path=args.input,
        output_path=args.output,
        k_colors=args.colors,
        min_area=args.min_area,
        epsilon_frac=args.epsilon,
        resize_longest=args.resize_longest,
    )


if __name__ == "__main__":
    main()
