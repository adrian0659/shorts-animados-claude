"""Renderiza un short de cómic vertical a partir de plan.json.

Uso:
  python3 render.py plan.json --fotos     # una foto por toma + hoja de revisión (rápido, para ajustar encuadres)
  python3 render.py plan.json             # video final con voz, música y efectos

plan.json:
{
  "paginas": "ruta/a/paginas",          # carpeta con pagina_000.jpg ... (de extraer_paginas.py)
  "voz": "voz.mp3",
  "salida": "video.mp4",
  "tomas": [
    {"t": 0.0, "pag": 3, "cx": 2886, "cy": 900, "ancho": 1250, "fx": ["golpe"], "nota": "ojos de Doom"},
    ...
  ]
}
Rutas relativas = relativas a la carpeta del plan.
  t      segundo en que empieza la toma (sacado de palabras.json)
  pag    número de página
  cx,cy  centro de la cámara en píxeles de la página (usa revision/cuadricula_XXX.jpg)
  ancho  ancho de la ventana en px de página. La altura es ancho*16/9. Más ancho = se ve más página.
         Para que una viñeta se vea completa: ancho >= ancho de la viñeta (y >= alto*9/16).
  clip   (en vez de pag/cx/cy/ancho) video para insertar, p. ej. un clip de la película; "desde": segundo inicial.
         Se ve a pantalla completa sin su audio (la voz va encima).
  sonido lista de efectos de ambiente para esa escena (pocos, suaves): "viento", "bofetada", "crujido",
         "clavos", "trueno", "lluvia" (sigue sonando hasta la última toma que también diga "lluvia"), "rugido".
  fx     efectos: "golpe" (zoom de entrada), "sacudir", "flash", "impacto" (flash + golpe fuerte + crujido,
         con silencio tenso justo antes; úsalo en EL momento del video).
Movimiento (estilo del video de referencia): dentro de la misma página la cámara se desliza de una toma a la
siguiente; al cambiar de página hay un barrido con desenfoque y separación de color; cada toma se acerca despacio.
"""
import sys, os, json, subprocess
import numpy as np
from PIL import Image

W, H, FPS, SR = 1080, 1920, 30, 44100
ASP = H / W
PAD = 700
PAN = 0.45     # segundos del deslizamiento entre viñetas de la misma página
WHIP = 4       # cuadros de barrido a cada lado de un cambio de página

plan_path = sys.argv[1]
FOTOS = "--fotos" in sys.argv
base = os.path.dirname(os.path.abspath(plan_path))
plan = json.load(open(plan_path))
rel = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
PAGES, VOZ, OUT = rel(plan["paginas"]), rel(plan["voz"]), rel(plan.get("salida", "video.mp4"))
TOMAS = sorted(plan["tomas"], key=lambda s: s["t"])
KEYS = [(s["t"], s.get("pag", "clip"), s.get("cx", 0), s.get("cy", 0), s.get("ancho", 1), s.get("fx", []))
        for s in TOMAS]

_clips = {}
def clip_frame(k, dt):
    s = TOMAS[k]; ruta = rel(s["clip"])
    if ruta not in _clips:
        cw, ch = 576, 1024
        raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", ruta, "-vf",
              f"fps={FPS},scale={cw}:{ch}:force_original_aspect_ratio=increase,crop={cw}:{ch}",
              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
        _clips[ruta] = np.frombuffer(raw, np.uint8).reshape(-1, ch, cw, 3)
    fr = _clips[ruta]
    i = min(len(fr) - 1, int((dt + s.get("desde", 0)) * FPS))
    return np.asarray(Image.fromarray(fr[i]).resize((W, H), Image.BICUBIC)).astype(np.float32)

_cache = {}
def page(n):
    if n not in _cache:
        if len(_cache) > 4: _cache.pop(next(iter(_cache)))
        im = Image.open(os.path.join(PAGES, f"pagina_{n:03d}.jpg")).convert("RGB")
        canvas = Image.new("RGB", (im.width + 2 * PAD, im.height + 2 * PAD), (14, 14, 18))
        canvas.paste(im, (PAD, PAD))
        _cache[n] = (canvas, im.width, im.height)
    return _cache[n]

def ease(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)

def cam(t):
    i = max(k for k, s in enumerate(KEYS) if s[0] <= t)
    t0, n, cx, cy, w, _ = KEYS[i]
    t1 = KEYS[i + 1][0] if i + 1 < len(KEYS) else t0 + 3
    w = w * (1 - 0.07 * ease((t - t0) / max(0.5, t1 - t0)))      # acercamiento lento
    if i > 0 and KEYS[i - 1][1] == n and n != "clip":                               # deslizamiento en la misma página
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
    i0 = max(k for k, s in enumerate(KEYS) if s[0] <= t)
    if KEYS[i0][1] == "clip":
        return clip_frame(i0, t - KEYS[i0][0])
    i, n, cx, cy, w = cam(t)
    efx = KEYS[i][5]; dt = t - KEYS[i][0]
    if "golpe" in efx or "impacto" in efx:
        w /= 1 + 0.12 * np.exp(-dt * 8)
    canvas, pw, ph = page(n)
    h = w * ASP
    cx = min(max(cx, w / 2), pw - w / 2) if w < pw else pw / 2
    cy = min(max(cy, h / 2), ph - h / 2) if h < ph else ph / 2
    if ("sacudir" in efx or "impacto" in efx) and dt < 0.55:
        a = w * 0.018 * np.exp(-dt * 7)
        cx += rng.uniform(-a, a); cy += rng.uniform(-a, a)
    x0, y0 = cx - w / 2 + PAD, cy - h / 2 + PAD
    arr = np.asarray(canvas.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h))).astype(np.float32)
    if ("flash" in efx or "impacto" in efx) and dt < 0.25:
        arr += (255 - arr) * (1 - dt / 0.25) * 0.85
    return arr

def whip(arr, k, sign):
    if k <= 0: return arr
    L = int(90 * k); acc = np.zeros_like(arr)
    for s in range(7):
        acc += np.roll(arr, int(sign * L * (s / 6 - 0.5)), axis=1)
    out = acc / 7; sh = int(24 * k)
    out[..., 0] = np.roll(out[..., 0], sh, axis=1)
    out[..., 2] = np.roll(out[..., 2], -sh, axis=1)
    return out

def duracion():
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", VOZ]).decode()) + 0.6

def fotos():
    dur = duracion(); rng = np.random.default_rng(1)
    rev = os.path.join(base, "revision_tomas"); os.makedirs(rev, exist_ok=True)
    minis = []
    for k, s in enumerate(KEYS):
        t1 = KEYS[k + 1][0] if k + 1 < len(KEYS) else dur
        t = s[0] + min(0.8, (t1 - s[0]) * 0.6)
        im = Image.fromarray(np.clip(render(t, rng), 0, 255).astype(np.uint8))
        im.save(os.path.join(rev, f"toma_{k:02d}.jpg"), quality=85)
        im.thumbnail((216, 384)); minis.append(im)
    cols = 10; rows = (len(minis) + cols - 1) // cols
    hoja = Image.new("RGB", (cols * 216, rows * 384))
    for k, m in enumerate(minis): hoja.paste(m, ((k % cols) * 216, (k // cols) * 384))
    hoja.save(os.path.join(rev, "hoja_tomas.jpg"), quality=85)
    print("fotos en", rev)

# ---------------- audio: voz + música de suspenso + efectos (todo sintetizado, sin derechos) -------------
def audio(dur, cortes, wav):
    voz = np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", VOZ, "-ac", "1", "-ar", str(SR),
                                                 "-f", "f32le", "-"]), np.float32).copy()
    n = int(dur * SR); t = np.arange(n) / SR; rng = np.random.default_rng(3)
    imp = [s[0] for s in KEYS if "impacto" in s[5]]
    t_imp = imp[0] if imp else dur * 0.78
    def env(t0, a, d):
        x = t - t0; return np.where(x < 0, 0, np.minimum(1, x / a) * np.exp(-np.maximum(x, 0) / d))
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t)
    dron = (np.sin(2*np.pi*36.7*t) + 0.6*np.sin(2*np.pi*73.4*t) + 0.35*np.sin(2*np.pi*87.3*t + 1)
            + 0.25*np.sin(2*np.pi*110*t + 2) + 0.12*np.sin(2*np.pi*146.8*t*1.003)) * lfo
    crece = np.clip((t - dur * 0.38) / (dur * 0.35), 0, 1)
    mus = 0.22 * dron + 0.15 * np.sin(2*np.pi*220*t) * np.sin(2*np.pi*0.25*t)**2 * (0.3 + 0.7 * crece)
    fase = np.cumsum((70 + 40 * crece) / 60 / SR)
    lat = np.exp(-(fase % 1) * 9) * np.sin(2*np.pi*55*t) + 0.6 * np.exp(-((fase + 0.22) % 1) * 12) * np.sin(2*np.pi*50*t)
    mus += 0.35 * lat * np.clip((t - 2.5) / 3, 0, 1) * (t < t_imp)
    mus *= np.clip(t / 0.5, 0, 1) * np.where((t > t_imp - 0.8) & (t < t_imp), 0.25, 1)
    sfx = np.zeros(n)
    def boom(t0, g):
        f = 60 * np.exp(-np.maximum(t - t0, 0) * 3) + 30
        sfx[:] += g * (t >= t0) * (np.sin(np.cumsum(2*np.pi*f/SR)) * env(t0, 0.005, 0.6)
                                   + 0.5 * rng.standard_normal(n) * env(t0, 0.002, 0.08))
    def whoosh(t0, g):
        x = t - t0; sh = np.clip(1 + x / 0.5, 0, 1) ** 2 * np.exp(-np.maximum(x, 0) * 20)
        sfx[:] += g * 0.4 * rng.standard_normal(n) * sh * ((x >= -0.5) & (x < 0.15))
    for s in KEYS:
        if "impacto" in s[5]:
            boom(s[0], 1.4); x = t - s[0]
            sfx[:] += ((x > 0) & (x < 0.5)) * rng.standard_normal(n) * (rng.random(n) < 0.02) * 1.2 * np.exp(-np.maximum(x, 0) * 5)
        elif {"golpe", "sacudir", "flash"} & set(s[5]):
            boom(s[0], 0.8)
    for c in cortes: whoosh(c, 0.5)
    # --- sonidos de ambiente por escena (pocos y suaves) ---
    amb = np.zeros(n)
    def suave(x, k):  # pasa bajos con promedio móvil
        return np.convolve(x, np.ones(k) / k, mode="same")
    def ventana(t0, t1, a=0.4):
        return np.clip((t - t0) / a, 0, 1) * np.clip((t1 - t) / a, 0, 1)
    fin = lambda k: TOMAS[k + 1]["t"] if k + 1 < len(TOMAS) else dur
    ruido = rng.standard_normal(n)
    lluvia = [s["t"] for s in TOMAS if "lluvia" in s.get("sonido", [])]
    if lluvia:
        k_ult = max(k for k, s in enumerate(TOMAS) if "lluvia" in s.get("sonido", []))
        amb += 0.35 * (ruido - suave(ruido, 6)) * ventana(lluvia[0], fin(k_ult), 1.0)
    for k, s in enumerate(TOMAS):
        t0 = s["t"]; t1 = fin(k); x = t - t0; pos = x >= 0
        for so in s.get("sonido", []):
            if so == "viento":
                v = suave(ruido, 60) * 6 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.4 * t))
                amb += 0.5 * v * ventana(t0, t1 + 0.5, 0.6)
            elif so == "bofetada":
                amb += 1.6 * pos * (ruido - suave(ruido, 3)) * np.exp(-np.maximum(x, 0) * 45)
            elif so == "crujido":
                amb += 1.4 * ((x > 0) & (x < 0.6)) * ruido * (rng.random(n) < 0.015) * np.exp(-np.maximum(x, 0) * 4)
            elif so == "clavos":
                for d in (0.15, 0.55, 0.95):
                    y = x - d; m = y >= 0; e = np.exp(-np.maximum(y, 0) * 18)
                    amb += 0.7 * m * e * (np.sin(2 * np.pi * 1850 * t) + 0.6 * np.sin(2 * np.pi * 2730 * t)
                                          + 0.8 * (ruido - suave(ruido, 4)) * np.exp(-np.maximum(y, 0) * 60))
            elif so == "trueno":
                ret = suave(ruido, 200) * 14
                amb += 1.2 * pos * (ret * np.exp(-np.maximum(x, 0) * 0.9) * np.clip(x / 0.08, 0, 1)
                                    + 0.6 * (ruido - suave(ruido, 3)) * np.exp(-np.maximum(x, 0) * 25))
            elif so == "rugido":
                f = 85 + 10 * np.sin(2 * np.pi * 7 * t)
                saw = 2 * ((np.cumsum(f / SR)) % 1) - 1
                amb += 0.6 * ((x > 0) & (x < 1.2)) * saw * (0.5 + 0.5 * suave(np.abs(ruido), 300) * 2) \
                       * np.clip(x / 0.1, 0, 1) * np.clip((1.2 - x) / 0.3, 0, 1)
    sfx = sfx + amb * (np.max(np.abs(sfx)) / (np.max(np.abs(amb)) + 1e-9)) * 0.55 if np.any(amb) else sfx
    v = np.zeros(n); v[:min(n, len(voz))] = voz[:n]
    rms = lambda x: np.sqrt(np.mean(x[np.abs(x) > 1e-4] ** 2) + 1e-12)
    mus *= rms(v) / rms(mus) * 10 ** (-13 / 20)
    sfx *= rms(v) / (np.max(np.abs(sfx)) + 1e-9) * 1.2
    envv = np.convolve(np.abs(v), np.ones(4410) / 4410, mode="same")
    duck = 1 - 0.35 * np.clip(envv / (envv.max() * 0.3), 0, 1)
    mix = (v + mus * duck + sfx * 0.5) * np.clip((dur - t) / 0.8, 0, 1)
    st = np.stack([mix, mix], 1).astype(np.float32)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", wav], input=st.tobytes(), check=True)

def video():
    dur = duracion(); nfr = int(dur * FPS)
    cortes_f = [round(s[0] * FPS) for k, s in enumerate(KEYS) if k > 0 and (s[1] != KEYS[k - 1][1] or s[1] == "clip")]
    vid, wav = OUT + ".tmp.mp4", OUT + ".tmp.wav"
    audio(dur, [c / FPS for c in cortes_f], wav)
    vig = vignette(); rng = np.random.default_rng(7)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                           "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
    for f in range(nfr):
        t = f / FPS; arr = render(t, rng)
        for c in cortes_f:
            d = f - c
            if -WHIP <= d < WHIP:
                arr = whip(arr, 1 - (abs(d + 0.5) - 0.5) / WHIP, 1 if d < 0 else -1)
        if t > dur - 1.0: arr *= max(0, (dur - t) / 1.0)
        arr *= vig
        ff.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
        if f % 300 == 0: print(f"  {t:5.1f}/{dur:.1f} s", flush=True)
    ff.stdin.close(); ff.wait()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", OUT], check=True)
    os.remove(vid); os.remove(wav)
    hoja = os.path.join(base, "revision_tomas", "hoja_video.jpg"); os.makedirs(os.path.dirname(hoja), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", OUT, "-vf", "select='not(mod(n\\,45))',scale=180:320,tile=10x4",
                    "-frames:v", "1", "-fps_mode", "vfr", hoja])
    print("listo:", OUT)

if __name__ == "__main__":
    fotos() if FOTOS else video()
