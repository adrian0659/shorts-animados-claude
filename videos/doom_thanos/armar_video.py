"""Arma el short «¿Sabías que el Doctor Doom eliminó a Thanos?» con las páginas del cómic.

Uso:  python3 armar_video.py CARPETA_PAGINAS VOZ.mp3
CARPETA_PAGINAS = carpeta con las páginas .jpg de Secret Wars (2015) #8 (sacadas del .cbr).

Estilo del video de referencia: una "cámara" vertical 9:16 recorre la página completa. Las viñetas se ven
enteras (con sus bordes y las vecinas arriba/abajo); dentro de la misma página la cámara se DESLIZA de una
viñeta a otra; al cambiar de página hay un barrido con desenfoque de movimiento y separación de color.
Salida: /tmp/_doom_video.mp4 (1080x1920, 30 fps, sin audio).
"""
import sys, os, subprocess
import numpy as np
from PIL import Image

W, H, FPS = 1080, 1920, 30
ASP = H / W
PAD = 700
PAGES, VOZ = sys.argv[1], sys.argv[2]

# (tiempo, página, centro x, centro y, ancho de la ventana en px de página, efectos)
KEYS = [
    (0.00, 3, 2886, 900, 1250, ["golpe"]),          # ojos de Doom
    (1.30, 21, 760, 1330, 1350, ["flash", "sacudir"]),  # adelanto: la columna
    (2.80, 3, 2886, 1050, 1750, []),                # título Secret Wars
    (5.30, 6, 994, 1000, 1700, ["sacudir"]),        # el multiverso se destruye
    (7.90, 4, 695, 520, 760, []),                   # Doom (reparto)
    (9.50, 4, 1316, 520, 760, []),                  # Hombre Molécula (desliza)
    (11.40, 22, 1006, 2400, 1900, ["flash"]),       # poder infinito
    (13.30, 5, 1035, 800, 1900, []),                # castillo
    (16.20, 8, 1002, 1000, 1900, []),               # Mundo de Batalla
    (19.70, 23, 1000, 900, 1650, ["golpe"]),        # Dios Emperador
    (22.00, 6, 1365, 1811, 1300, []),               # los rebeldes llegan
    (24.40, 5, 994, 1871, 1900, ["sacudir"]),       # explosión
    (26.20, 19, 994, 700, 1950, []),                # Thanos aparece
    (28.00, 19, 450, 1550, 1000, ["golpe", "sacudir"]),  # ENOUGH!
    (29.20, 19, 1330, 1550, 1250, ["sacudir"]),     # aterriza (desliza)
    (30.40, 20, 1000, 750, 1350, []),               # "me ofreces un regalo"
    (32.30, 20, 1184, 1300, 1700, []),              # dios débil, farsante (desliza)
    (33.80, 20, 993, 1700, 1950, []),               # inclínate ante mí (desliza)
    (35.50, 20, 420, 700, 1000, []),                # Doom ofrece (desliza)
    (37.50, 19, 560, 2400, 1150, ["golpe"]),        # "DOOM."
    (39.40, 20, 1580, 2420, 1050, []),              # Thanos sonríe
    (40.80, 20, 700, 2420, 1350, []),               # ¿tienes un guantelete? (desliza)
    (43.20, 23, 1706, 2420, 900, ["golpe"]),        # mirada de Doom
    (44.10, 21, 993, 600, 1950, ["golpe", "sacudir"]),  # HURK
    (44.90, 21, 760, 1350, 1400, ["flash", "sacudir"]), # la columna (desliza)
    (47.40, 21, 993, 2500, 1950, []),               # Annihilus con el cráneo (desliza)
    (49.60, 19, 1459, 2480, 1100, []),              # frente a todos
    (51.60, 23, 1706, 2400, 900, []),               # mirada de Doom
    (54.00, 21, 950, 1150, 1250, []),               # Doom con la columna
    (56.80, 3, 2886, 900, 1300, ["golpe"]),         # ojos de Doom
]
PAN = 0.45      # duración del deslizamiento entre viñetas de la misma página
WHIP = 4        # cuadros de barrido a cada lado de un cambio de página

_cache = {}
def page(n):
    if n not in _cache:
        if len(_cache) > 4:
            _cache.pop(next(iter(_cache)))
        im = Image.open(os.path.join(PAGES, f"Secret Wars (2015-) 008-{n:03d}.jpg")).convert("RGB")
        canvas = Image.new("RGB", (im.width + 2 * PAD, im.height + 2 * PAD), (14, 14, 18))
        canvas.paste(im, (PAD, PAD))
        _cache[n] = (canvas, im.width, im.height)
    return _cache[n]

def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def cam(t):
    """Devuelve (índice, página, cx, cy, w) en el tiempo t."""
    i = max(k for k, s in enumerate(KEYS) if s[0] <= t)
    t0, n, cx, cy, w, _ = KEYS[i]
    t1 = KEYS[i + 1][0] if i + 1 < len(KEYS) else t0 + 3
    # deriva lenta mientras se sostiene la toma (acercamiento suave, como en la referencia)
    hold = ease((t - t0) / max(0.5, t1 - t0))
    w = w * (1 - 0.07 * hold)
    # deslizamiento desde la viñeta anterior si es la misma página
    if i > 0 and KEYS[i - 1][1] == n:
        _, _, px, py, pw, _ = KEYS[i - 1]
        u = ease((t - t0) / PAN)
        cx, cy = px + (cx - px) * u, py + (cy - py) * u
        w = pw * 0.93 + (w - pw * 0.93) * u
    return i, n, cx, cy, w

def vignette():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    return np.clip(1.0 - 0.35 * np.clip(d - 0.6, 0, 1) ** 1.5, 0, 1)[..., None].astype(np.float32)

def render(t, rng):
    i, n, cx, cy, w = cam(t)
    efx = KEYS[i][5]; dt = t - KEYS[i][0]
    if "golpe" in efx:
        w /= 1 + 0.12 * np.exp(-dt * 8)
    canvas, pw, ph = page(n)
    h = w * ASP
    # mantener la ventana dentro de la página cuando se pueda
    if w < pw: cx = min(max(cx, w / 2), pw - w / 2)
    else: cx = pw / 2
    if h < ph: cy = min(max(cy, h / 2), ph - h / 2)
    else: cy = ph / 2
    if "sacudir" in efx and dt < 0.55:
        a = w * 0.018 * np.exp(-dt * 7)
        cx += rng.uniform(-a, a); cy += rng.uniform(-a, a)
    x0, y0 = cx - w / 2 + PAD, cy - h / 2 + PAD
    fr = canvas.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h))
    arr = np.asarray(fr).astype(np.float32)
    if "flash" in efx and dt < 0.25:
        arr += (255 - arr) * (1 - dt / 0.25) * 0.85
    return arr, i

def whip(arr, k, sign):
    """Barrido: desenfoque de movimiento horizontal + separación de color. k en 0..1."""
    if k <= 0: return arr
    L = int(90 * k)
    acc = np.zeros_like(arr)
    steps = 7
    for s in range(steps):
        acc += np.roll(arr, int(sign * L * (s / (steps - 1) - 0.5)), axis=1)
    out = acc / steps
    sh = int(24 * k)
    out[..., 0] = np.roll(out[..., 0], sh, axis=1)
    out[..., 2] = np.roll(out[..., 2], -sh, axis=1)
    return out

def main():
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", VOZ]).decode()) + 0.6
    nfr = int(dur * FPS)
    cuts = [round(s[0] * FPS) for k, s in enumerate(KEYS) if k > 0 and s[1] != KEYS[k - 1][1]]
    vig = vignette()
    rng = np.random.default_rng(7)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                           "-crf", "18", "-pix_fmt", "yuv420p", "/tmp/_doom_video.mp4"], stdin=subprocess.PIPE)
    for f in range(nfr):
        t = f / FPS
        arr, i = render(t, rng)
        for c in cuts:
            d = f - c
            if -WHIP <= d < WHIP:
                k = 1 - (abs(d + 0.5) - 0.5) / WHIP
                arr = whip(arr, k, 1 if d < 0 else -1)
        if t > dur - 1.0:
            arr *= max(0, (dur - t) / 1.0)
        arr *= vig
        ff.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
    print("video ok", dur)

if __name__ == "__main__":
    main()
