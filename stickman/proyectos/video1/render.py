"""Video «POV: eres el abogado del cártel» — imágenes animadas + voz + subtítulos + música.

Ejecutar desde esta carpeta:
    python3 render.py --fotos      # fotos de revisión en salida/
    python3 render.py              # video final -> salida/abogado_cartel.mp4
    python3 render.py --desde 60 --hasta 75   # solo un tramo (para revisar rápido)
"""
import os, sys, json, math, subprocess, random
import numpy as np
import cv2
import cairo

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import sonido as snd

W, H, FPS = 1080, 1920, 30
DUR = 144.6
AQUI = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(AQUI, "salida"), exist_ok=True)

def suave(k):
    k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)

# ------------------------------------------------------------------ escenas
# (inicio, imagen, cámara, efectos)
# cámara: lista de (tiempo, zoom, cx, cy). tiempo <= 1 => fracción de la escena; > 1 => segundo absoluto.
# cx, cy: centro del encuadre en coordenadas de la imagen (0..1).
E = [
    (0.00,   "10", [(0, 1.0, .5, .45), (1, 1.35, .5, .33)], {}),
    (3.30,   "01", [(0, 1.05, .62, .45), (1, 1.25, .66, .38)], {}),
    (6.80,   "02", [(0, 1.25, .62, .55), (.4, 1.25, .62, .55), (1, 1.45, .4, .2)], {}),
    (13.45,  "03", [(0, 1.0, .5, .5), (1, 1.3, .62, .42)], {"parpadeo_luz": 1}),
    (16.20,  "04", [(0, 1.1, .5, .5), (1, 1.3, .55, .36)], {"brillo": (.33, .37)}),
    (19.30,  "05", [(0, 1.0, .5, .5), (1, 1.4, .45, .47)], {}),
    (23.30,  "06", [(0, 1.0, .5, .5), (1, 1.3, .5, .45)], {"parpadeo_luz": 1}),
    (27.20,  "07", [(0, 1.0, .5, .55), (1, 1.2, .5, .45)], {}),
    (28.90,  "08", [(0, 1.05, .45, .55), (1, 1.25, .45, .5)], {}),
    (31.10,  "09", [(0, 1.0, .5, .45), (1, 1.35, .5, .42)], {}),
    (33.10,  "10", [(0, 1.0, .5, .5), (1, 1.25, .5, .35)], {}),
    (37.10,  "11", [(0, 1.0, .5, .5), (43.45, 1.08, .52, .48), (43.75, 1.55, .6, .43), (1, 1.65, .6, .43)], {}),
    (46.10,  "12", [(0, 1.1, .55, .5), (1, 1.4, .6, .6)], {}),
    (49.40,  "13", [(0, 1.35, .5, .35), (1, 1.05, .5, .45)], {}),
    (53.50,  "14", [(0, 1.05, .5, .4), (1, 1.3, .5, .45)], {"brillo": (.36, .35)}),
    (57.05,  "15", [(0, 1.0, .5, .55), (1, 1.25, .45, .5)], {}),
    (59.55,  "16", [(0, 1.05, .5, .5), (1, 1.2, .6, .55)], {}),
    (60.70,  "17", [(0, 1.0, .5, .55), (1, 1.22, .58, .48)], {}),
    (64.20,  "18", [(0, 1.0, .5, .5), (1, 1.4, .52, .43)], {}),
    (69.40,  "19", [(0, 1.05, .5, .5), (1, 1.35, .55, .42)], {}),
    (71.90,  "20", [(0, 1.0, .5, .5), (1, 1.25, .5, .42)], {"flashes": 1}),
    (74.35,  "21", [(0, 1.25, .4, .6), (1, 1.25, .6, .45)], {"flashes": 1}),
    (78.25,  "22", [(0, 1.35, .5, .45), (1, 1.05, .5, .5)], {}),
    (83.45,  "23", [(0, 1.0, .5, .5), (87.3, 1.15, .6, .55), (1, 1.5, .62, .44)], {}),
    (89.40,  "24", [(0, 1.05, .5, .5), (1, 1.4, .62, .44)], {"brillo": (.66, .45)}),
    (92.80,  "25", [(0, 1.0, .5, .5), (1, 1.25, .5, .45)], {"flashes": 1}),
    (95.95,  "26", [(0, 1.3, .7, .3), (1, 1.3, .4, .62)], {}),
    (98.70,  "27", [(0, 1.0, .5, .5), (1, 1.3, .42, .45)], {}),
    (106.60, "19", [(0, 1.5, .55, .38), (1, 1.15, .5, .45)], {}),
    (112.65, "15", [(0, 1.1, .5, .55), (1, 1.55, .3, .72)], {}),
    (115.75, "28", [(0, 1.0, .5, .5), (117.0, 1.1, .5, .45), (117.25, 1.35, .5, .36), (1, 1.42, .5, .36)], {}),
    (120.95, "29", [(0, 1.05, .45, .55), (1, 1.2, .6, .55)], {}),
    (125.45, "30", [(0, 1.3, .6, .55), (1, 1.05, .5, .5)], {}),
    (133.15, "01", [(0, 1.3, .6, .4), (1, 1.0, .5, .5)], {}),
    (137.20, "02", [(0, 1.1, .5, .5), (1, 1.4, .25, .65)], {}),
    (139.95, "12", [(0, 1.1, .55, .55), (1, 1.5, .6, .62)], {}),
]
SACUDIDAS = [(0.05, 26), (43.5, 22), (73.64, 26), (88.54, 18), (117.12, 18), (141.2, 12)]
DESTELLOS = [(43.5, 0.5), (71.9, 0.8)]          # destello blanco (t, fuerza)
CRUCE = 0.14                                    # segundos de fundido entre escenas

# ------------------------------------------------------------------ imágenes
_cache = {}
def imagen(nombre):
    """Imagen ampliada (cubre 1080x1920 a zoom 1, con margen x1.5 para acercamientos nítidos)."""
    if nombre not in _cache:
        im = cv2.imread(os.path.join(AQUI, "imagenes", f"{nombre}.jpg"))[:, :, ::-1]
        h, w = im.shape[:2]
        k = max(W / w, H / h) * 1.5
        big = cv2.resize(im, (round(w * k), round(h * k)), interpolation=cv2.INTER_LANCZOS4)
        blur = cv2.GaussianBlur(big, (0, 0), 2.2)
        big = cv2.addWeighted(big, 1.45, blur, -0.45, 0)       # enfoque suave tras ampliar
        _cache[nombre] = big
    return _cache[nombre]

def camara(esc, fin, t):
    t0, _, kf, _ = esc
    dur = fin - t0
    pts = [(t0 + k[0] * dur if k[0] <= 1 else k[0], *k[1:]) for k in kf]
    if t <= pts[0][0]: return pts[0][1:]
    for a, b in zip(pts, pts[1:]):
        if t <= b[0]:
            u = suave((t - a[0]) / max(b[0] - a[0], 1e-6))
            return tuple(p + (q - p) * u for p, q in zip(a[1:], b[1:]))
    return pts[-1][1:]

def sacudida(t):
    dx = dy = 0.0
    for ts, f in SACUDIDAS:
        if 0 <= t - ts < 0.45:
            d = (1 - (t - ts) / 0.45) ** 2 * f
            dx += math.sin(t * 93) * d; dy += math.cos(t * 71) * d
    return dx, dy

def cuadro_escena(i, t):
    esc = E[i]; fin = E[i + 1][0] if i + 1 < len(E) else DUR
    src = imagen(esc[1]); sh, sw = src.shape[:2]
    z, cx, cy = camara(esc, fin, t)
    # cámara en mano: deriva muy leve para que nunca esté quieta
    z *= 1 + 0.008 * math.sin(t * 0.9 + i)
    cx += 0.004 * math.sin(t * 0.7 + i * 1.7); cy += 0.004 * math.cos(t * 0.6 + i)
    vw = 1 / z; vh = (H / W) * (sw / sh) / z
    cx = min(max(cx, vw / 2), 1 - vw / 2); cy = min(max(cy, vh / 2), 1 - vh / 2)
    s = vw * sw / W
    dx, dy = sacudida(t)
    M = np.float32([[s, 0, (cx - vw / 2) * sw - dx * s], [0, s, (cy - vh / 2) * sh - dy * s]])
    out = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                         borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    fx = esc[3]
    if "parpadeo_luz" in fx:
        r = random.Random(int(t * 12) + i * 1000)
        out *= 0.93 + 0.07 * r.random() if r.random() < 0.25 else 1.0
    if "brillo" in fx:
        bx, by = fx["brillo"]
        px, py = (bx - (cx - vw / 2)) / vw * W, (by - (cy - vh / 2)) / vh * H
        out += _halo(px, py, 380) * (40 + 22 * math.sin(t * 5))
    if "flashes" in fx:
        for tf, px, py in _flashes(i, esc[0], fin):
            if 0 <= t - tf < 0.16:
                k = (1 - (t - tf) / 0.16) ** 2
                out += _halo(px, py, 520) * 255 * 0.9 * k
                out += 60 * k
    return out

_halos = {}
def _halo(px, py, r):
    key = (int(px) // 8, int(py) // 8, r)
    if key not in _halos:
        if len(_halos) > 200: _halos.clear()
        yy, xx = np.ogrid[0:H, 0:W]
        d2 = ((xx - px) ** 2 + (yy - py) ** 2) / (r * r)
        _halos[key] = np.exp(-d2 * 2.5).astype(np.float32)[..., None]
    return _halos[key]

_fl = {}
def _flashes(i, t0, t1):
    if i not in _fl:
        r = random.Random(i * 77); t = t0 + 0.2; lst = []
        while t < t1 - 0.2:
            lst.append((t, r.uniform(120, W - 120), r.uniform(500, H - 300))); t += r.uniform(0.25, 0.7)
        _fl[i] = lst
    return _fl[i]

# ------------------------------------------------------------------ acabado (viñeta, grano, color)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.42 * np.clip(np.hypot((xx - W / 2) / (W * 0.62), (yy - H / 2) / (H * 0.62)) - 0.35, 0, 1) ** 1.5)[..., None]
_rng = np.random.default_rng(4)
GRANO = [(VIG * (1 + 0.05 * (_rng.random((H, W), np.float32) - 0.5)[..., None])).astype(np.float32) for _ in range(4)]
del yy, xx

# ------------------------------------------------------------------ subtítulos
CLAVE = {"cártel", "$50,000", "$100,000", "armados", "poderosos", "dinero", "millonario", "nadie", "urgente",
         "detenido", "peligroso", "amenazas", "periodistas", "autoridades", "familia", "precio", "doble",
         "rechazar", "decisión", "vida", "pov:", "aceptas", "clientes?", "nuevo"}

def palabras():
    d = json.load(open(os.path.join(AQUI, "transcripcion.json")))
    ws = [dict(w) for s in d for w in s["palabras"]]
    out = []
    for w in ws:   # unir "$50" + ",000"
        if out and w["p"].startswith(",") and out[-1]["p"].startswith("$"):
            out[-1]["p"] += w["p"]; out[-1]["f"] = w["f"]
        else: out.append(w)
    return out

def bloques(ws):
    res, cur = [], []
    for w in ws:
        if cur and (len(cur) >= 3 or cur[-1]["p"][-1] in ".,?!" or w["i"] - cur[-1]["f"] > 0.35):
            res.append(cur); cur = []
        cur.append(w)
    res.append(cur)
    out = []
    for k, b in enumerate(res):
        fin = res[k + 1][0]["i"] if k + 1 < len(res) else b[-1]["f"] + 0.6
        out.append((b[0]["i"], min(fin, b[-1]["f"] + 0.9), b))
    return out

BLOQUES = bloques(palabras())
SUB_Y, SUB_ALTO = 1330, 360
_sub = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, SUB_ALTO)

def subtitulos(frame, t):
    blq = next((b for b in BLOQUES if b[0] <= t < b[1]), None)
    if blq is None: return frame
    ctx = cairo.Context(_sub)
    ctx.set_operator(cairo.OPERATOR_CLEAR); ctx.paint(); ctx.set_operator(cairo.OPERATOR_OVER)
    ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    tam = 84; ctx.set_font_size(tam)
    ws = [w for w in blq[2] if w["i"] <= t + 0.02]
    textos = [w["p"].upper() for w in blq[2]]
    sp = ctx.text_extents(" ").x_advance
    # partir en renglones según el bloque completo (para que no salte al aparecer palabras)
    renglones, act, ancho = [], [], 0
    for j, tx in enumerate(textos):
        a = ctx.text_extents(tx).x_advance
        if act and ancho + sp + a > 960: renglones.append(act); act, ancho = [], 0
        act.append(j); ancho += (sp if len(act) > 1 else 0) + a
    renglones.append(act)
    y0 = SUB_ALTO / 2 - (len(renglones) - 1) * tam * 0.6 + tam * 0.35
    for r, ren in enumerate(renglones):
        anch = sum(ctx.text_extents(textos[j]).x_advance for j in ren) + sp * (len(ren) - 1)
        x = (W - anch) / 2; y = y0 + r * tam * 1.2
        for j in ren:
            w = blq[2][j]; tx = textos[j]; adv = ctx.text_extents(tx).x_advance
            if j < len(ws):
                k = min(1.0, (t - w["i"]) / 0.12)
                esc = 0.7 + 0.3 * k + 0.08 * math.sin(k * math.pi)
                clave = w["p"].lower().strip(".,¿?¡!") in CLAVE or w["p"].lower() in CLAVE
                ctx.save(); ctx.translate(x + adv / 2, y); ctx.scale(esc, esc)
                ctx.move_to(-adv / 2, 0); ctx.text_path(tx)
                ctx.set_source_rgba(0, 0, 0, 0.95); ctx.set_line_width(15); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
                ctx.stroke_preserve()
                ctx.set_source_rgb(*((1.0, 0.84, 0.15) if clave else (1, 1, 1))); ctx.fill()
                ctx.restore()
            x += adv + sp
    _sub.flush()
    a = np.ndarray((SUB_ALTO, W, 4), np.uint8, _sub.get_data()).astype(np.float32) / 255
    alpha = a[..., 3:4]
    rgb = a[..., [2, 1, 0]] * 255           # premultiplicado
    zona = frame[SUB_Y:SUB_Y + SUB_ALTO]
    frame[SUB_Y:SUB_Y + SUB_ALTO] = zona * (1 - alpha) + rgb
    return frame

# ------------------------------------------------------------------ cuadro final
def escena_en(t):
    i = 0
    for k, e in enumerate(E):
        if e[0] <= t: i = k
    return i

def cuadro(t):
    i = escena_en(t)
    f = cuadro_escena(i, t)
    if i > 0 and t - E[i][0] < CRUCE:
        k = suave((t - E[i][0]) / CRUCE)
        f = cuadro_escena(i - 1, t) * (1 - k) + f * k
    for td, fuerza in DESTELLOS:
        if 0 <= t - td < 0.3: f += 255 * fuerza * (1 - (t - td) / 0.3) ** 2
    f *= GRANO[int(t * 12) % 4]
    f = (f - 128) * 1.06 + 128                                  # un poco más de contraste
    if t > DUR - 0.9: f *= max(0.0, (DUR - t) / 0.9)            # fundido a negro final
    if t < 0.25: f *= t / 0.25
    f = np.clip(f, 0, 255)
    f = subtitulos(f, t)
    return np.clip(f, 0, 255).astype(np.uint8)

# ------------------------------------------------------------------ audio
SR = snd.SR
def tono_pad(f, d, brillo=4.0):
    t = np.arange(int(SR * d)) / SR
    s = sum(np.sin(2 * np.pi * f * n * t * (1 + 0.0015 * (n % 3 - 1))) / n * math.exp(-n / brillo) for n in range(1, 9))
    s += 0.5 * np.sin(2 * np.pi * f * 1.003 * t)
    return s

def musica():
    """Fondo oscuro de suspenso que se aclara en el final."""
    total = np.zeros(int(SR * (DUR + 1)))
    oscuro = [(110.0, 130.81, 164.81), (87.31, 110.0, 130.81), (73.42, 87.31, 110.0), (82.41, 103.83, 123.47)]
    claro = [(130.81, 164.81, 196.0), (98.0, 123.47, 146.83), (110.0, 130.81, 164.81), (87.31, 110.0, 130.81)]
    d = 4.0; t = 0.0; n = 0
    while t < DUR:
        acordes = claro if t >= 125.0 else oscuro
        ch = acordes[n % 4]
        seg = sum(tono_pad(f, d + 1.5) for f in ch)
        seg += 1.4 * np.sin(2 * np.pi * ch[0] / 2 * np.arange(len(seg)) / SR)   # bajo
        env = np.minimum(1, np.arange(len(seg)) / (SR * 1.2)) * np.minimum(1, (len(seg) - np.arange(len(seg))) / (SR * 1.5))
        a = int(t * SR); total[a:a + len(seg)] += (seg * env)[:len(total) - a]
        t += d; n += 1
    # pulso grave (como latido lejano) en la parte tensa
    for tt in np.arange(69.4, 121.0, 1.0):
        lat = snd.latido() * 0.5; a = int(tt * SR); total[a:a + len(lat)] += lat * 3
    return total / np.max(np.abs(total))

def golpe():
    t = np.arange(int(SR * 1.2)) / SR
    s = np.sin(2 * np.pi * (48 + 70 * np.exp(-t * 8)) * t) * np.exp(-t * 3.2)
    n = np.random.default_rng(2).standard_normal(len(t)) * np.exp(-t * 18) * 0.3
    return (s + n) * 0.9

def telefono():
    t = np.arange(int(SR * 0.9)) / SR
    tono = (np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 480 * t)) * 0.25
    vib = (np.sin(2 * np.pi * 22 * t) > 0) * 1.0
    env = ((t % 0.45) < 0.32) * 1.0
    return tono * env * (0.6 + 0.4 * vib)

def obturador():
    t = np.arange(int(SR * 0.09)) / SR
    n = np.random.default_rng(int(t.size)).standard_normal(len(t))
    return n * (np.exp(-t * 90) + 0.6 * np.exp(-np.maximum(0, t - 0.04) * 120) * (t > 0.04)) * 0.4

def dinero():
    return snd.ding(1568, 0.7) * 0.8 + np.pad(snd.ding(2093, 0.6) * 0.6, (int(SR * 0.08), 0))[:int(SR * 0.7)]

def construir_audio(ruta):
    voz = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(AQUI, "voz.mp3"), "-f", "f32le",
                                        "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout, np.float32).astype(np.float64)
    n = int(SR * DUR)
    mez = np.zeros(n)
    mez[:min(n, len(voz))] += voz[:n]
    rms_voz = np.sqrt(np.mean(voz[voz != 0] ** 2))
    mus = musica()[:n]
    mus = mus / np.sqrt(np.mean(mus ** 2)) * rms_voz * 0.22
    mez[:len(mus)] += mus
    def poner(t, s, vol):
        a = int(t * SR); b = min(n, a + len(s)); mez[a:b] += s[:b - a] * vol * rms_voz * 3
    for t, _ in SACUDIDAS: poner(t, golpe(), 0.9)
    for t in (16.3, 69.5, 106.75): poner(t, telefono(), 0.35)
    for t in (19.4, 40.2, 57.5): poner(t, dinero(), 0.35)
    for i, e in enumerate(E):
        if "flashes" in e[3]:
            fin = E[i + 1][0]
            for tf, _, _ in _flashes(i, e[0], fin): poner(tf, obturador(), 0.5)
        if i in (2, 7, 10, 19, 22, 28, 33): poner(e[0] - 0.2, snd.whoosh(), 0.12)
    mez /= np.max(np.abs(mez)) / 0.9
    tmp = ruta + ".raw.wav"
    import wave
    with wave.open(tmp, "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((mez * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", ruta], check=True)
    os.remove(tmp)

# ------------------------------------------------------------------ main
if __name__ == "__main__":
    from PIL import Image
    sal = os.path.join(AQUI, "salida")
    if "--fotos" in sys.argv:
        for tt in [e[0] + 1.0 for e in E]:
            Image.fromarray(cuadro(tt)).save(f"{sal}/foto_{tt:06.2f}.jpg", quality=85)
        print("fotos listas")
        sys.exit()
    desde = float(sys.argv[sys.argv.index("--desde") + 1]) if "--desde" in sys.argv else 0.0
    hasta = float(sys.argv[sys.argv.index("--hasta") + 1]) if "--hasta" in sys.argv else DUR
    audio = f"{sal}/audio.wav"
    if not os.path.exists(audio) or "--audio" in sys.argv:
        construir_audio(audio); print("audio listo")
    nombre = "abogado_cartel.mp4" if (desde, hasta) == (0.0, DUR) else f"tramo_{desde:g}_{hasta:g}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-ss", str(desde), "-i", audio, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", f"{sal}/{nombre}"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = int((hasta - desde) * FPS)
    for k in range(total):
        p.stdin.write(cuadro(desde + k / FPS).tobytes())
        if k % (FPS * 5) == 0: print(f"  {desde + k / FPS:6.1f}s / {hasta:.1f}s", flush=True)
    p.stdin.close(); p.wait(); print("listo:", nombre)
