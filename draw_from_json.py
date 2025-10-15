import argparse
import json
import math
import random
import statistics
import turtle


# ------------------------
# Colores
# ------------------------
def _clamp(v, a, b):
    return max(a, min(b, v))

def _hsv_rad_to_rgb01(h_rad: float, s: float, v: float):
    h = (h_rad % (2.0 * math.pi)) / (2.0 * math.pi)
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    i %= 6
    if i == 0:   r, g, b = v, t, p
    elif i == 1: r, g, b = q, v, p
    elif i == 2: r, g, b = p, v, t
    elif i == 3: r, g, b = p, q, v
    elif i == 4: r, g, b = t, p, v
    else:        r, g, b = v, p, q
    return (_clamp(r, 0, 1), _clamp(g, 0, 1), _clamp(b, 0, 1))

def _rgb01_to_hex(rgb01):
    r = int(round(_clamp(rgb01[0], 0, 1) * 255))
    g = int(round(_clamp(rgb01[1], 0, 1) * 255))
    b = int(round(_clamp(rgb01[2], 0, 1) * 255))
    return f"#{r:02x}{g:02x}{b:02x}"

def _rgb255_to_hex(rgb255):
    r = int(round(_clamp(rgb255[0], 0, 255)))
    g = int(round(_clamp(rgb255[1], 0, 255)))
    b = int(round(_clamp(rgb255[2], 0, 255)))
    return f"#{r:02x}{g:02x}{b:02x}"

def _color_to_hex(color):
    if not isinstance(color, (list, tuple)) or len(color) != 3:
        return "#ffffff"
    c0, c1, c2 = float(color[0]), float(color[1]), float(color[2])
    if 0 <= c1 <= 1 and 0 <= c2 <= 1 and 0 <= c0 <= (2 * math.pi + 1e-6):
        return _rgb01_to_hex(_hsv_rad_to_rgb01(c0, c1, c2))
    if 0 <= c0 <= 1 and 0 <= c1 <= 1 and 0 <= c2 <= 1:
        return _rgb01_to_hex((c0, c1, c2))
    return _rgb255_to_hex((c0, c1, c2))


# ------------------------
# Geometría y utilidades
# ------------------------
def _perp_dist(p, a, b):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)
    t = ((x - x1) * dx + (y - y1) * dy) / float(dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    projx, projy = x1 + t * dx, y1 + t * dy
    return math.hypot(x - projx, y - projy)

def _rdp_screen(points, epsilon):
    if epsilon <= 0 or len(points) <= 3:
        return points
    stack = [(0, len(points) - 1)]
    keep = {0, len(points) - 1}
    while stack:
        start, end = stack.pop()
        a, b = points[start], points[end]
        idx, dmax = None, 0.0
        for i in range(start + 1, end):
            d = _perp_dist(points[i], a, b)
            if d > dmax:
                idx, dmax = i, d
        if idx is not None and dmax > epsilon:
            keep.add(idx)
            stack.append((start, idx))
            stack.append((idx, end))
    out = [points[i] for i in sorted(keep)]
    return out if len(out) >= 3 else points

def _poly_area(pts):
    n = len(pts)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) * 0.5

def _dedupe_and_minseg_screen(pts, min_seg_px):
    if not pts:
        return pts
    out = []
    last = None
    for p in pts:
        if last is None or p != last:
            if last is None or min_seg_px <= 0 or math.hypot(p[0]-last[0], p[1]-last[1]) >= min_seg_px:
                out.append(p); last = p
    return out

def _print_stats(regions):
    counts = [len(r["contour"]) for r in regions]
    total = sum(counts)
    mx = max(counts) if counts else 0
    p50 = int(statistics.median(counts)) if counts else 0
    p90 = int(statistics.quantiles(counts, n=10)[-1]) if len(counts) >= 10 else mx
    p99 = int(statistics.quantiles(counts, n=100)[-1]) if len(counts) >= 100 else mx
    print(f"Regiones: {len(regions)}  Puntos totales: {total}  max: {mx}  p50: {p50}  p90: {p90}  p99: {p99}")


# ------------------------
# Render con animación (ON por defecto)
# ------------------------
def draw_from_json(
    json_file: str,
    update_every: int = 300,
    wait: bool = True,
    bg: str = "black",
    margin: float = 0.10,
    simplify_eps: float = 0.0,
    simplify_min_points: int = 200,
    min_seg_px: float = 0.8,
    animate: bool = True,      # ahora por defecto True
    delay_ms: int = 80,        # retardo visible por defecto
    order: str = "area",       # area | input | random | smallfirst
    stats_only: bool = False,
):
    # Cargar y limpiar
    with open(json_file, encoding="utf-8") as f:
        raw = json.load(f)
    regions = [
        {
            "color": r.get("color", [255, 255, 255]),
            "contour": [(float(p[0]), float(p[1])) for p in r.get("contour", []) if isinstance(p, (list, tuple)) and len(p) >= 2]
        }
        for r in raw
    ]
    regions = [r for r in regions if len(r["contour"]) >= 3]
    if not regions:
        print("Sin polígonos válidos.")
        return

    if stats_only:
        _print_stats(regions)
        return

    # BBox datos
    all_x = [x for r in regions for (x, _) in r["contour"]]
    all_y = [y for r in regions for (_, y) in r["contour"]]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    data_w = max(1e-9, max_x - min_x)
    data_h = max(1e-9, max_y - min_y)
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0

    # Orden de dibujo
    if order == "area":
        regions.sort(key=lambda r: _poly_area(r["contour"]), reverse=True)
    elif order == "smallfirst":
        regions.sort(key=lambda r: _poly_area(r["contour"]))
    elif order == "random":
        random.shuffle(regions)

    # Ventana/Canvas
    screen = turtle.Screen()
    screen.bgcolor(bg)
    screen.setup(width=1000, height=800)
    screen.tracer(0, 0)
    turtle.delay(0)
    screen.update()
    canvas = screen.getcanvas()

    # Transform centrado (coords Canvas centradas)
    def compute_transform():
        try:
            screen._root.update_idletasks()  # type: ignore[attr-defined]
        except Exception:
            pass
        cw = canvas.winfo_width() or screen.window_width()
        ch = canvas.winfo_height() or screen.window_height()
        safe_w = cw * (1.0 - 2.0 * margin)
        safe_h = ch * (1.0 - 2.0 * margin)
        scale_fit = min(safe_w / data_w, safe_h / data_h)
        scale = max(1e-9, scale_fit * 0.995)  # colchón anti-corte

        def to_canvas_xy(x, y):
            return (int(round((x - cx) * scale)), int(round((y - cy) * scale)))
        return cw, ch, scale, to_canvas_xy

    cw, ch, scale, to_canvas_xy = compute_transform()

    # Prepara regiones en pantalla (limpieza/simplificación)
    screen_regions = []
    for r in regions:
        pts_scr = [to_canvas_xy(x, y) for (x, y) in r["contour"]]
        pts_scr = _dedupe_and_minseg_screen(pts_scr, min_seg_px)
        if simplify_eps > 0 and len(pts_scr) > simplify_min_points:
            pts_scr = _rdp_screen(pts_scr, simplify_eps)
        if len(pts_scr) >= 3:
            screen_regions.append((r["color"], pts_scr))

    # Dibujo
    def draw_polygon(color, pts):
        color_hex = _color_to_hex(color)
        flat = [v for xy in pts for v in xy]
        canvas.create_polygon(*flat, fill=color_hex, outline=color_hex, joinstyle="round")

    if animate:
        state = {"i": 0, "paused": False, "delay": max(1, int(delay_ms)), "done": False}

        def step():
            if state["done"] or state["paused"]:
                return
            if state["i"] >= len(screen_regions):
                state["done"] = True
                screen._root.wm_title("Listo")  # type: ignore[attr-defined]
                screen.update()
                return
            color, pts = screen_regions[state["i"]]
            draw_polygon(color, pts)
            state["i"] += 1
            # HUD en el título de la ventana
            try:
                screen._root.wm_title(f"{state['i']}/{len(screen_regions)}")  # type: ignore[attr-defined]
            except Exception:
                pass
            # actualizar SIEMPRE cada paso para que se note
            screen.update()
            canvas.after(state["delay"], step)

        # Controles
        def toggle_pause(_=None):
            state["paused"] = not state["paused"]
            if not state["paused"]:
                step()
        def speed_up(_=None):
            state["delay"] = max(1, int(state["delay"] * 0.8))
        def speed_down(_=None):
            state["delay"] = int(state["delay"] / 0.8) + 1
        def speed_reset(_=None):
            state["delay"] = max(1, int(delay_ms))
        def finish_now(_=None):
            state["paused"] = True
            for j in range(state["i"], len(screen_regions)):
                color, pts = screen_regions[j]
                draw_polygon(color, pts)
            state["i"] = len(screen_regions)
            state["done"] = True
            try:
                screen._root.wm_title("Listo")  # type: ignore[attr-defined]
            except Exception:
                pass
            screen.update()
        def shuffle_and_restart(_=None):
            if state["done"]:
                return
            random.shuffle(screen_regions)
            canvas.delete("all")
            state["i"] = 0
            step()

        try:
            root = screen._root  # type: ignore[attr-defined]
            root.bind("<space>", toggle_pause)
            root.bind("<Key-plus>", speed_up)
            root.bind("<Key-equal>", speed_up)     # '=' suele ser '+'
            root.bind("<Key-KP_Add>", speed_up)    # numpad +
            root.bind("<Key-minus>", speed_down)
            root.bind("<Key-KP_Subtract>", speed_down)
            root.bind("0", speed_reset)
            root.bind("f", finish_now)
            root.bind("r", shuffle_and_restart)
        except Exception:
            pass

        step()
    else:
        i = 0
        while i < len(screen_regions):
            end = min(i + update_every, len(screen_regions))
            for j in range(i, end):
                color, pts = screen_regions[j]
                draw_polygon(color, pts)
            i = end
            screen.update()

    if wait:
        screen.exitonclick()
    else:
        turtle.done()


# ------------------------
# CLI
# ------------------------
def main():
    parser = argparse.ArgumentParser(description="Dibujar JSON de regiones con animación paso a paso.")
    parser.add_argument("json", nargs="?", default="resources/rosas.json", help="Ruta del JSON")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas y salir")
    parser.add_argument("--bg", type=str, default="black", help="Color de fondo")
    parser.add_argument("--margin", type=float, default=0.10, help="Margen relativo (0–0.3)")
    parser.add_argument("--simplify-eps", type=float, default=0.0, help="RDP en px de pantalla (1–2 p/archivos grandes)")
    parser.add_argument("--simplify-min-points", type=int, default=200, help="Umbral de puntos para simplificar")
    parser.add_argument("--min-seg-px", type=float, default=0.8, help="Eliminar segmentos menores a N px (0=off)")
    parser.add_argument("--no-animate", dest="animate", action="store_false", help="Desactivar animación")
    parser.add_argument("--delay-ms", type=int, default=80, help="Retardo entre regiones en ms (animación)")
    parser.add_argument("--order", type=str, choices=["area", "input", "random", "smallfirst"], default="area", help="Orden de dibujo")
    parser.add_argument("--update-every", type=int, default=300, help="Regiones por actualización (no animado)")
    parser.add_argument("--no-wait", dest="wait", action="store_false", help="No esperar click al final")
    args = parser.parse_args()

    if args.stats:
        with open(args.json, encoding="utf-8") as f:
            _print_stats([{"contour": r.get("contour", [])} for r in json.load(f)])
        return

    draw_from_json(
        args.json,
        update_every=args.update_every,
        wait=args.wait,
        bg=args.bg,
        margin=args.margin,
        simplify_eps=args.simplify_eps,
        simplify_min_points=args.simplify_min_points,
        min_seg_px=args.min_seg_px,
        animate=args.animate,
        delay_ms=args.delay_ms,
        order=args.order,
    )

if __name__ == "__main__":
    main()