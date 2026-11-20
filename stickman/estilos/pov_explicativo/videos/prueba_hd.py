"""Prueba de 5 s (vertical 1080x1920) con personajes HD recortados de las hojas de referencia.

Ejecutar desde stickman/estilos/pov_explicativo/:   python3 videos/prueba_hd.py   -> salida/prueba_hd.mp4
"""
import os, sys, math, subprocess, wave
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, "..")
sys.path.insert(0, RAIZ)
from escenarios import *
from PIL import Image

HD = os.path.join(RAIZ, "referencias_personajes", "hd", "hoja_A")
SAL = os.path.join(RAIZ, "salida")


def superficie_png(ruta):
    im = Image.open(ruta).convert("RGBA")
    a = np.asarray(im, np.float32) / 255
    al = a[..., 3:4]
    pre = np.concatenate([a[..., 2:3] * al, a[..., 1:2] * al, a[..., 0:1] * al, al], axis=2)
    buf = (pre * 255).astype(np.uint8)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, im.width, im.height)
    np.ndarray((im.height, s.get_stride()), np.uint8, s.get_data())[:, :im.width * 4] = buf.reshape(im.height, -1)
    s.mark_dirty()
    return s


class Recorte:
    """Personaje recortado (PNG con transparencia) animado: entrada, balanceo, respiración, rebote al hablar.

    x = centro, y = borde inferior, alto = altura en pantalla. entrada: 'pop' o 'izq'/'der' (desliza)."""

    def __init__(self, ruta, x, y, alto, t0=0.0, entrada="pop", espejo=False, habla=()):
        self.s = superficie_png(ruta); self.x, self.y, self.alto = x, y, alto
        self.t0, self.entrada, self.espejo, self.habla = t0, entrada, espejo, list(habla)

    def dibujar(self, c, t):
        tt = t - self.t0
        if tt < 0: return
        esc = self.alto / self.s.get_height()
        x, y = self.x, self.y
        k = 1.0
        if self.entrada == "pop":
            k = max(0.01, rebote(tt / 0.4))
        elif self.entrada in ("izq", "der"):
            u = suave2(tt / 0.55); x = lerp(-500 if self.entrada == "izq" else W + 500, self.x, u)
            y += -abs(math.sin(tt * 14)) * 22 * (1 - u)   # saltitos al entrar
        resp = 1 + math.sin(t * 2.4) * 0.012
        rot = math.sin(t * 1.3) * 0.018
        for (h0, h1) in self.habla:   # al hablar: pequeño rebote
            if h0 <= t <= h1: resp += abs(math.sin(t * 11)) * 0.018; rot += math.sin(t * 7) * 0.012
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(esc * k * (-1 if self.espejo else 1), esc * k * resp)
        c.set_source_surface(self.s, -self.s.get_width() / 2, -self.s.get_height())
        c.get_source().set_filter(cairo.FILTER_GOOD); c.paint(); c.restore()


def sombra_piso(x, y, w):
    def f(c, t):
        c.save(); c.translate(x, y); c.scale(1, 0.12)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, w); g.add_color_stop_rgba(0, 0, 0, 0, 0.35); g.add_color_stop_rgba(1, 0, 0, 0, 0)
        c.set_source(g); c.arc(0, 0, w, 0, 7); c.fill(); c.restore()
    return f


def titulo(txt, t0, y, tam, color=(1, 1, 1), halo=TINTA):
    def f(c, t):
        if t < t0: return
        k = rebote((t - t0) / 0.3)
        c.save(); c.translate(W / 2, y); c.scale(k, k); texto(c, txt, 0, 0, tam, color, MARKER, halo=halo); c.restore()
    return f


def escenas():
    poli = Recorte(os.path.join(HD, "04_policia_recorte.png"), 560, H + 10, 1500, 0.05, "pop", habla=[(0.5, 1.6)])
    e1 = Escena(0, 2.5, lambda c: calle(c, "tarde"), [poli,
                Etiqueta("¡ALTO!", 0.6, 250, 640, (190, 900), tam=110, color=ROJO_, curva=0.3),
                Etiqueta("POLICÍA", 1.2, 880, 1060, (720, 1260), tam=70, curva=-0.35)],
                pantalla=[titulo("POV:", 0.0, 170, 120), titulo("TE DETIENEN", 0.25, 300, 96)],
                cam=(1.0, 1.08, (540, 1000), (520, 1060)), sacudidas=[(0.15, 16)])
    det = Recorte(os.path.join(HD, "17_detective_recorte.png"), 560, H + 10, 1500, 0.05, "der", habla=[(1.0, 2.2)])
    e2 = Escena(2.5, 5.0, lambda c: oficina(c, "noche"), [det,
                Etiqueta("LUPA", 0.8, 900, 700, (880, 960), tam=72, curva=-0.35),
                Etiqueta("TE ESTÁ\nINVESTIGANDO", 1.4, 430, 470, None, tam=78, color=(1, 0.85, 0.2), halo=TINTA, rot=-5)],
                cam=(1.03, 1.12, (540, 1000), (540, 930)))
    return [e1, e2]


# ---------------------------------------------------------------- sonido
SR = 44100
def _t(d): return np.arange(int(SR * d)) / SR
def whoosh(d=0.5):
    n = np.random.default_rng(1).standard_normal(int(SR * d)); n = np.convolve(n, np.ones(40) / 40, "same")
    return n * np.sin(np.pi * np.arange(len(n)) / len(n)) ** 2 * 1.4
def pop(d=0.1):
    t = _t(d); f = 700 * np.exp(-t * 30) + 220
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 40) * 0.5
def golpe():
    t = _t(0.9); return np.sin(2 * np.pi * (45 + 60 * np.exp(-t * 12)) * t) * np.exp(-t * 4) * 0.9
def sirena(d):
    t = _t(d); f = 750 + 250 * np.sign(np.sin(2 * np.pi * 1.6 * t))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.12 * np.minimum(1, (d - t) / 0.3)
def musica(d):
    t = _t(d); s = np.sin(2 * np.pi * 55 * t) * 0.3 + np.sin(2 * np.pi * 82.4 * t) * 0.15
    for k in range(int(d / 0.4)):
        o = int(k * 0.4 * SR); g = np.sin(2 * np.pi * 60 * _t(0.2)) * np.exp(-_t(0.2) * 20) * 0.5
        s[o:o + len(g)] += g[:len(s) - o]
    return s * np.minimum(1, np.minimum(t / 0.3, (d - t) / 0.4))


def audio(ruta, es, dur=5.0):
    b = np.zeros(int(SR * dur) + SR)
    def poner(t, x, v=1): o = int(t * SR); b[o:o + len(x)] += x[:len(b) - o] * v
    poner(0, musica(dur), 0.35); poner(0.0, sirena(2.4), 1.0); poner(0.15, golpe(), 0.8); poner(2.3, whoosh(), 0.6)
    for e in es:
        for cap in e.capas:
            if isinstance(cap, Etiqueta): poner(e.t0 + cap.t0, pop(), 0.8)
    b = b / np.abs(b).max() * 0.85
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((b * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    os.makedirs(SAL, exist_ok=True)
    es = escenas()
    if "--fotos" in sys.argv:
        for t in (1.3, 4.2): Image.fromarray(cuadro_video(es, t)).save(os.path.join(SAL, f"prueba_hd_{t}.png"))
        sys.exit()
    v = os.path.join(SAL, "_prueba_v.mp4"); a = os.path.join(SAL, "_prueba_a.wav")
    render_tramo(es, 0, 5.0, v); audio(a, es)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", os.path.join(SAL, "prueba_hd.mp4")], check=True)
    os.remove(v); os.remove(a); print("listo: salida/prueba_hd.mp4")
