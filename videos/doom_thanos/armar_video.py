"""Arma el short «¿Sabías que el Doctor Doom eliminó a Thanos?» con viñetas del cómic.

Uso:  python3 armar_video.py CARPETA_PAGINAS VOZ.mp3 SALIDA.mp4
CARPETA_PAGINAS = carpeta con las páginas .jpg de Secret Wars (2015) #8 (sacadas del .cbr).
Vertical 1080x1920, 30 fps. Cada toma: viñeta recortada, fondo desenfocado, zoom/paneo lento,
"golpe" de zoom en cada corte, sacudidas y destellos en los impactos. Música y efectos sintetizados.
"""
import sys, os, subprocess, json
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

W, H, FPS = 1080, 1920, 30
PAGES, VOZ, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

def page(n):
    return os.path.join(PAGES, f"Secret Wars (2015-) 008-{n:03d}.jpg")

# (inicio, página, recorte x0,y0,x1,y1 en px de la página, modo, foco fx,fy, zoom inicial, zoom final, efectos)
# modo "fit": viñeta a lo ancho sobre fondo desenfocado; "cover": llena toda la pantalla.
SHOTS = [
    (0.00, 3,  (1750, 0, 3975, 830),    "fit",   (0.5, 0.5), 1.00, 1.15, ["golpe"]),
    (1.30, 21, (0, 611, 1988, 2370),    "cover", (0.25, 0.25), 1.10, 1.25, ["flash", "sacudir"]),
    (2.80, 3,  (1750, 0, 3975, 1350),   "fit",   (0.5, 0.5), 1.00, 1.12, []),
    (5.30, 6,  (0, 0, 1988, 1433),      "cover", (0.5, 0.5), 1.05, 1.25, ["sacudir"]),
    (7.90, 4,  (406, 358, 984, 636),    "fit",   (0.5, 0.4), 1.00, 1.15, []),
    (9.50, 4,  (1018, 358, 1614, 636),  "fit",   (0.5, 0.4), 1.00, 1.15, []),
    (11.40, 22, (82, 2071, 1931, 2987), "fit",   (0.5, 0.5), 1.00, 1.18, ["flash"]),
    (13.30, 5, (80, 60, 1990, 815),     "fit",   (0.6, 0.4), 1.00, 1.15, []),
    (16.20, 8, (67, 60, 1937, 557),     "fit",   (0.5, 0.5), 1.05, 1.20, []),
    (19.70, 23, (85, 0, 1916, 498),     "cover", (0.55, 0.5), 1.00, 1.15, ["golpe"]),
    (22.00, 6, (818, 1413, 1913, 2210), "fit",   (0.3, 0.5), 1.00, 1.12, []),
    (24.40, 5, (0, 1453, 1988, 2290),   "cover", (0.5, 0.5), 1.05, 1.20, ["sacudir"]),
    (26.20, 19, (0, 0, 1988, 1070),     "cover", (0.72, 0.30), 1.00, 1.45, []),
    (28.00, 19, (76, 1070, 765, 1950),  "cover", (0.5, 0.35), 1.00, 1.15, ["golpe", "sacudir"]),
    (29.20, 19, (787, 1070, 1910, 1950),"cover", (0.5, 0.5), 1.00, 1.12, ["sacudir"]),
    (30.40, 20, (710, 69, 1291, 970),   "cover", (0.5, 0.5), 1.00, 1.12, []),
    (32.30, 20, (458, 978, 1910, 1467), "fit",   (0.4, 0.5), 1.00, 1.15, []),
    (33.80, 20, (76, 1474, 1910, 1880), "fit",   (0.5, 0.5), 1.05, 1.25, []),
    (35.50, 20, (76, 69, 688, 970),     "cover", (0.5, 0.45), 1.00, 1.15, []),
    (37.50, 19, (76, 2000, 985, 2972),  "cover", (0.6, 0.4), 1.00, 1.12, ["golpe"]),
    (39.40, 20, (1306, 1933, 1910, 2972),"cover", (0.5, 0.6), 1.00, 1.15, []),
    (40.80, 20, (76, 1933, 1291, 2972), "cover", (0.45, 0.4), 1.00, 1.18, []),
    (43.20, 23, (1497, 1870, 1916, 3025),"cover",(0.5, 0.30), 1.00, 1.12, ["golpe"]),
    (44.10, 21, (76, 76, 1910, 611),    "fit",   (0.5, 0.5), 1.05, 1.20, ["golpe", "sacudir"]),
    (44.90, 21, (0, 611, 1988, 2370),   "cover", (0.3, 0.3), 1.00, 1.20, ["flash", "sacudir"]),
    (47.40, 21, (76, 2384, 1910, 2972), "fit",   (0.45, 0.5), 1.00, 1.20, []),
    (49.60, 19, (1008, 2000, 1910, 2972),"cover",(0.5, 0.5), 1.00, 1.15, []),
    (51.60, 23, (1497, 1870, 1916, 3025),"cover",(0.5, 0.30), 1.00, 1.15, []),
    (54.00, 21, (0, 611, 1988, 2370),   "cover", (0.55, 0.40), 1.25, 1.45, []),
    (56.80, 3,  (1750, 0, 3975, 830),   "fit",   (0.5, 0.5), 1.05, 1.30, ["golpe"]),
]

def load_shot(s):
    t0, n, box, modo, foco, z0, z1, fx = s
    img = Image.open(page(n)).convert("RGB").crop(box)
    if modo == "cover":
        # imagen base que cubre 1080x1920 (con margen para zoom)
        sc = max(W / img.width, H / img.height)
        base = img.resize((int(img.width * sc * 1.0 + 1), int(img.height * sc + 1)), Image.LANCZOS)
        bg = None
    else:
        k = min(2.2, max(1.0, 0.5 * H / (img.height * W / img.width)))
        sc = W * k / img.width
        base = img.resize((int(W * k), int(img.height * sc)), Image.LANCZOS)
        cov = max(W / img.width, H / img.height)
        bg = img.resize((int(img.width * cov) + 1, int(img.height * cov) + 1), Image.BILINEAR)
        bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
        bg = bg.filter(ImageFilter.GaussianBlur(28))
        bg = ImageEnhance.Brightness(bg).enhance(0.45)
    return base, bg

def ease(u):
    return u * u * (3 - 2 * u)

def vignette():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    return np.clip(1.0 - 0.45 * np.clip(d - 0.55, 0, 1) ** 1.5, 0, 1)[..., None].astype(np.float32)

def main():
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", VOZ]).decode()) + 0.6
    nfr = int(dur * FPS)
    cache = {}
    vig = vignette()
    rng = np.random.default_rng(7)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                           "-crf", "18", "-pix_fmt", "yuv420p", "/tmp/_doom_video.mp4"], stdin=subprocess.PIPE)
    for f in range(nfr):
        t = f / FPS
        i = max(k for k, s in enumerate(SHOTS) if s[0] <= t)
        s = SHOTS[i]
        t0, n, box, modo, (fx, fy), z0, z1, efx = s
        t1 = SHOTS[i + 1][0] if i + 1 < len(SHOTS) else dur
        u = ease(min(1, (t - t0) / max(0.01, t1 - t0)))
        z = z0 + (z1 - z0) * u
        dt = t - t0
        if True:
            # pequeño golpe de zoom en cada corte (como el video de referencia)
            amp = 0.10 if "golpe" in efx else 0.04
            z *= 1 + amp * np.exp(-dt * 9)
        if i not in cache:
            cache.clear(); cache[i] = load_shot(s)
        base, bg = cache[i]
        ox = oy = 0.0
        if "sacudir" in efx and dt < 0.5:
            a = 22 * np.exp(-dt * 7)
            ox, oy = rng.uniform(-a, a), rng.uniform(-a, a)
        if modo == "cover":
            # ventana de W/z x H/z dentro de base, centrada hacia el foco
            cw, ch = W / z, H / z
            sc = z
            cx = fx * base.width; cy = fy * base.height
            # mover el centro del encuadre del centro de la imagen al foco según el zoom
            mix = min(1, (z - 1) / 0.25 + 0.3)
            cx = base.width / 2 + (cx - base.width / 2) * mix
            cy = base.height / 2 + (cy - base.height / 2) * mix
            x0 = np.clip(cx - cw / 2, 0, base.width - cw) + ox / sc
            y0 = np.clip(cy - ch / 2, 0, base.height - ch) + oy / sc
            x0 = float(np.clip(x0, 0, base.width - cw)); y0 = float(np.clip(y0, 0, base.height - ch))
            frame = base.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
        else:
            frame = bg.copy()
            fw = int(base.width * z); fh = int(base.height * z)
            fg = base.resize((fw, fh), Image.BILINEAR)
            px = int((W - fw) * fx + ox); py = int((H - fh) / 2 + oy)
            frame.paste(fg, (px, py))
        arr = np.asarray(frame).astype(np.float32)
        if "flash" in efx and dt < 0.25:
            arr = arr + (255 - arr) * (1 - dt / 0.25) * 0.85
        # fundido de entrada en los primeros cuadros de la toma (corte suave de 2 cuadros)
        if dt < 2 / FPS and i > 0:
            arr *= 0.75
        # fundido a negro al final
        if t > dur - 1.0:
            arr *= max(0, (dur - t) / 1.0)
        arr = arr * vig
        ff.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
    print("video ok", dur)

if __name__ == "__main__":
    main()
