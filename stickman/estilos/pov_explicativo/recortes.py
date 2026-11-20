"""Personajes recortados (PNG HD) con expresiones nuevas: se borra la cara original y se dibuja otra en el mismo estilo.

    from recortes import Recorte
    doc = Recorte("doctor", [dict(t=0, x=540, y=1930, alto=1400, cara="feliz"), dict(t=2, cara="miedo")])

Caras: neutral, feliz, serio, preocupado, miedo, sorpresa, enojado, triste, pensando, malicia (+ parpadeo automático).
Extras: birrete=True (gorro de graduación), espejo=True, entrada 'pop'/'izq'/'der'.
"""
import os, math, random
import numpy as np
import cairo
from PIL import Image
from scipy import ndimage
from motor_pov import lerp, clamp, suave, suave2, rebote, TINTA, rrect, relleno, linea, degradado

AQUI = os.path.dirname(os.path.abspath(__file__))
HD = os.path.join(AQUI, "referencias_personajes", "hd", "hoja_A")
PERSONAJES = {"doctor": "03_doctor", "jefe": "13_empresario", "soldado": "26_soldado", "enfermera": "21_enfermera",
              "policia": "04_policia", "detective": "17_detective"}
_CACHE = {}


def _a_superficie(im):
    a = np.asarray(im.convert("RGBA"), np.float32) / 255
    al = a[..., 3:4]
    pre = np.concatenate([a[..., 2:3] * al, a[..., 1:2] * al, a[..., 0:1] * al, al], axis=2)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, im.width, im.height)
    np.ndarray((im.height, s.get_stride()), np.uint8, s.get_data())[:, :im.width * 4] = (pre * 255).astype(np.uint8).reshape(im.height, -1)
    s.mark_dirty(); return s


def _base(nombre):
    """Recorte con la cara borrada + geometría de la cabeza."""
    if ("b", nombre) in _CACHE: return _CACHE[("b", nombre)]
    im = Image.open(os.path.join(HD, PERSONAJES[nombre] + "_recorte.png")).convert("RGBA")
    a = np.asarray(im).copy(); h, w = a.shape[:2]
    wh = (a[..., 3] > 200) & (a[..., :3].min(axis=2) > 235); wh[int(h * 0.55):] = False
    lab, k = ndimage.label(wh); i = int(np.argmax(ndimage.sum(wh, lab, range(1, k + 1)))) + 1
    reg = ndimage.binary_fill_holes(lab == i)
    ys, xs = np.nonzero(reg)
    cara = ndimage.binary_erosion(reg, iterations=9)
    a[cara, :3] = 255
    r = (xs.max() - xs.min()) / 2
    geo = dict(cx=(xs.max() + xs.min()) / 2, cy=ys.max() - r * 0.98, r=r, top=ys.min(), w=w, h=h)
    _CACHE[("b", nombre)] = (Image.fromarray(a), geo)
    return _CACHE[("b", nombre)]


CARAS = {  # cejas (inclinación, altura), ojos (alto), boca
    "neutral": (0.02, 0.0, 1.0, "linea"), "feliz": (-0.02, -0.02, 1.0, "sonrisa"), "serio": (0.08, 0.02, 0.9, "linea"),
    "preocupado": (-0.12, -0.02, 1.0, "ondulada"), "miedo": (-0.16, -0.08, 1.25, "o"), "sorpresa": (-0.04, -0.12, 1.3, "o"),
    "enojado": (0.16, 0.03, 0.85, "enojo"), "triste": (-0.14, 0.0, 0.85, "triste"), "pensando": (0.08, -0.04, 0.95, "lado"),
    "malicia": (0.14, 0.02, 0.8, "sonrisa_lado"),
}


def _dibujar_cara(c, g, cara, parp, mira=0.0):
    cx, cy, r = g["cx"], g["cy"], g["r"]
    inc, sube, ojo, boca = CARAS[cara]
    ox = mira * r * 0.12
    ey = cy + r * 0.05
    for lado in (-1, 1):
        ex = cx + ox + lado * r * 0.3
        if parp:
            linea(c, [(ex - r * 0.09, ey), (ex + r * 0.09, ey)], r * 0.05)
        else:
            c.save(); c.translate(ex, ey); c.scale(0.68, ojo); c.arc(0, 0, r * 0.1, 0, 7); c.restore()
            c.set_source_rgb(*TINTA); c.fill()
            c.arc(ex - r * 0.025, ey - r * 0.045 * ojo, r * 0.025, 0, 7); c.set_source_rgb(1, 1, 1); c.fill()
        by = ey - r * 0.25 + sube * r
        a = (ex - r * 0.13, by - inc * r * lado * -1); b = (ex + r * 0.13, by + inc * r * lado * -1)
        c.move_to(*a); c.curve_to(a[0] + r * 0.07, a[1] - r * 0.05, b[0] - r * 0.07, b[1] - r * 0.05, *b)
        c.set_source_rgb(*TINTA); c.set_line_width(r * 0.07); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
    mx, my = cx + ox, cy + r * 0.45
    lw = r * 0.055
    c.set_source_rgb(*TINTA); c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_ROUND)
    if boca == "sonrisa":
        c.arc(mx, my - r * 0.2, r * 0.22, math.radians(35), math.radians(145)); c.stroke()
    elif boca == "o":
        c.save(); c.translate(mx, my); c.scale(1, 1.3); c.arc(0, 0, r * 0.075, 0, 7); c.restore(); c.fill()
    elif boca == "triste":
        c.arc(mx, my + r * 0.16, r * 0.17, math.radians(215), math.radians(325)); c.stroke()
    elif boca == "ondulada":
        c.move_to(mx - r * 0.14, my); c.curve_to(mx - r * 0.07, my - r * 0.06, mx, my + r * 0.05, mx + r * 0.07, my - r * 0.02)
        c.line_to(mx + r * 0.14, my + r * 0.02); c.stroke()
    elif boca == "enojo":
        c.move_to(mx - r * 0.13, my + r * 0.03); c.curve_to(mx - r * 0.05, my - r * 0.03, mx + r * 0.05, my - r * 0.03, mx + r * 0.13, my + r * 0.03); c.stroke()
    elif boca == "lado":
        c.move_to(mx - r * 0.1, my + r * 0.02); c.line_to(mx + r * 0.14, my - r * 0.03); c.stroke()
    elif boca == "sonrisa_lado":
        c.move_to(mx - r * 0.12, my); c.curve_to(mx, my + r * 0.05, mx + r * 0.1, my + r * 0.02, mx + r * 0.16, my - r * 0.06); c.stroke()
    else:
        c.move_to(mx - r * 0.11, my); c.line_to(mx + r * 0.11, my); c.stroke()


def _birrete(c, g):
    cx, top, r = g["cx"], g["top"], g["r"]
    y = top + r * 0.05
    c.move_to(cx - r * 0.75, y + r * 0.05); c.curve_to(cx - r * 0.7, y - r * 0.25, cx + r * 0.7, y - r * 0.25, cx + r * 0.75, y + r * 0.05)
    c.close_path(); relleno(c, (0.12, 0.12, 0.14), r * 0.035)
    c.move_to(cx, y - r * 0.55); c.line_to(cx + r * 1.15, y - r * 0.28); c.line_to(cx, y - r * 0.02); c.line_to(cx - r * 1.15, y - r * 0.28)
    c.close_path(); relleno(c, degradado(y - r * 0.55, y, (0.25, 0.25, 0.28), (0.1, 0.1, 0.12)), r * 0.035)
    c.arc(cx, y - r * 0.28, r * 0.05, 0, 7); relleno(c, (0.9, 0.75, 0.2), 0)
    linea(c, [(cx, y - r * 0.28), (cx + r * 0.7, y - r * 0.1), (cx + r * 0.75, y + r * 0.35)], r * 0.03, (0.9, 0.75, 0.2))
    c.arc(cx + r * 0.75, y + r * 0.38, r * 0.06, 0, 7); relleno(c, (0.9, 0.75, 0.2), r * 0.02)


def variante(nombre, cara, parp=False, birrete=False, mira=0.0):
    clave = ("v", nombre, cara, parp, birrete, round(mira, 1))
    if clave in _CACHE: return _CACHE[clave]
    im, g = _base(nombre)
    s = _a_superficie(im); c = cairo.Context(s)
    _dibujar_cara(c, g, cara, parp, mira)
    if birrete: _birrete(c, g)
    _CACHE[clave] = (s, g); return s, g


class Recorte:
    """Personaje recortado animado. claves: dict(t, x, y (borde inferior), alto, cara, mira, birrete, espejo)."""

    def __init__(self, nombre, claves, entrada="pop", sem=1, habla=()):
        self.n, self.entrada, self.sem, self.habla = nombre, entrada, sem, list(habla)
        prev = dict(x=540, y=1930, alto=1400, cara="neutral", mira=0.0, birrete=False, espejo=False)
        self.claves = []
        for k in sorted(claves, key=lambda k: k["t"]):
            k = dict(k)
            for a, b in prev.items(): k.setdefault(a, b)
            self.claves.append(k); prev = dict(k); prev.pop("t")
        self.t0 = self.claves[0]["t"]

    def dibujar(self, c, t):
        tt = t - self.t0
        if tt < 0: return
        cs = self.claves; a = cs[0]
        for k in cs:
            if k["t"] <= t: a = k
        i = cs.index(a); b = cs[i + 1] if i + 1 < len(cs) else a
        u = suave2((t - a["t"]) / max(1e-6, b["t"] - a["t"])) if b is not a and b.get("mover") else 0
        x, y, alto = lerp(a["x"], b["x"], u), lerp(a["y"], b["y"], u), lerp(a["alto"], b["alto"], u)
        parp = ((t + self.sem * 0.7) % 3.2) < 0.12
        s, g = variante(self.n, a["cara"], parp, a["birrete"], a["mira"])
        esc = alto / g["h"]; k = 1.0
        if self.entrada == "pop": k = max(0.01, rebote(tt / 0.4))
        elif self.entrada in ("izq", "der"):
            v = suave2(tt / 0.55); x = lerp(-600 if self.entrada == "izq" else 1700, x, v)
            y += -abs(math.sin(tt * 14)) * 22 * (1 - v)
        if a.get("caminar") and b is not a and t < b["t"]:
            y += -abs(math.sin(t * 9)) * 16
        resp = 1 + math.sin(t * 2.4 + self.sem) * 0.012
        rot = math.sin(t * 1.3 + self.sem) * 0.016
        if a["cara"] in ("miedo",): rot += math.sin(t * 40) * 0.006
        for (h0, h1) in self.habla:
            if h0 <= t <= h1: resp += abs(math.sin(t * 11)) * 0.016
        c.save(); c.translate(x, y); c.rotate(rot); c.scale(esc * k * (-1 if a["espejo"] else 1), esc * k * resp)
        c.set_source_surface(s, -g["w"] / 2, -g["h"]); c.get_source().set_filter(cairo.FILTER_GOOD); c.paint(); c.restore()


if __name__ == "__main__":
    from PIL import Image as I
    caras = list(CARAS)
    for n in ("doctor", "jefe", "soldado"):
        fila = []
        for cara in caras:
            s, g = variante(n, cara, birrete=(n == "doctor" and cara == "feliz"))
            buf = np.ndarray((g["h"], s.get_stride()), np.uint8, s.get_data())[:, :g["w"] * 4].reshape(g["h"], g["w"], 4)
            im = I.fromarray(buf[..., [2, 1, 0, 3]].copy(), "RGBA").crop((0, 0, g["w"], int(g["h"] * 0.55)))
            fila.append(im.resize((im.width // 4, im.height // 4)))
        hoja = I.new("RGBA", (sum(f.width for f in fila), fila[0].height), (230, 230, 230, 255)); x = 0
        for f in fila: hoja.alpha_composite(f, (x, 0)); x += f.width
        hoja.convert("RGB").save(os.path.join(AQUI, "salida", f"caras_{n}.png"))
    print("ok")
