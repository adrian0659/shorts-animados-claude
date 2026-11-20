"""Estilo «cómic POV»: personas caricatura detalladas (cara expresiva, ropa con estampado, manos con dedos),
cámara en primera persona con las manos del espectador en primer plano y escenarios muy cargados.

Lienzo por defecto 16:9 (1920x1080). Ver ESTILO.md (sección «Cómic POV») y la demo:
    python3 comic.py            -> salida/comic_demo.png  y  salida/comic_demo.mp4 (5 s)
"""
import math, random
import numpy as np
import cairo
import motor_pov as M
from motor_pov import (lerp, clamp, suave, rebote, osc, mezcla, rrect, relleno, degradado, linea, texto, TINTA,
                       MARKER, Etiqueta, Inserto, Escena, viñeta, cuadro_video, render_tramo)
import escenarios as E

M.formato(1920, 1080)
W, H = 1920, 1080

PIELES = {"morena": (0.78, 0.56, 0.42), "clara": (0.95, 0.8, 0.68), "media": (0.86, 0.66, 0.5), "oscura": (0.5, 0.34, 0.25)}


# ================================================================== trazos de cómic
def tinta(c, ancho=3.2, alfa=1.0):
    c.set_source_rgba(*TINTA, alfa); c.set_line_width(ancho)
    c.set_line_join(cairo.LINE_JOIN_ROUND); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()


def sombreado(c, camino, color, alfa=0.35, lado=1, frac=0.45, ancho=None):
    """Sombra de cel dentro de `camino`: oscurece una banda del lado `lado` (1 der, -1 izq)."""
    c.save(); camino(c); c.clip()
    x0, y0, x1, y1 = c.clip_extents()
    w = (x1 - x0)
    if lado > 0: c.rectangle(x1 - w * frac, y0, w * frac + 5, y1 - y0)
    else: c.rectangle(x0 - 5, y0, w * frac + 5, y1 - y0)
    c.set_source_rgba(*osc(color, 0.62), alfa); c.fill()
    c.restore()


def achurado(c, camino, sep=9, alfa=0.25, ang=40, ancho=1.6):
    c.save(); camino(c); c.clip()
    x0, y0, x1, y1 = c.clip_extents()
    a = math.radians(ang); L = (x1 - x0) + (y1 - y0)
    k = -L
    while k < L:
        c.move_to(x0 + k, y0); c.line_to(x0 + k + math.cos(a) * L * 2, y0 + math.sin(a) * L * 2); k += sep
    c.set_source_rgba(*TINTA, alfa); c.set_line_width(ancho); c.stroke(); c.restore()


def miembro(c, pts, ancho, color, borde=3.4):
    """Brazo/antebrazo grueso con contorno de tinta."""
    for w_, col in ((ancho + borde * 2, TINTA), (ancho, color)):
        c.set_source_rgb(*col); c.set_line_width(w_)
        c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.move_to(*pts[0])
        for p in pts[1:]: c.line_to(*p)
        c.stroke()


def mano(c, x, y, ang, s, tipo="abierta", color=(0.86, 0.66, 0.5), guante=False):
    """Mano con dedos. (x,y) = muñeca; ang = hacia dónde apuntan los dedos (grados, 0 = derecha, 90 = abajo)."""
    col = (0.97, 0.97, 0.96) if guante else color
    c.save(); c.translate(x, y); c.rotate(math.radians(ang)); c.scale(s, s)
    # dedos (dibujados antes de la palma para que la palma tape la base)
    dedos = []
    if tipo == "abierta":
        dedos = [(52, -16, 44, -10), (56, -5, 50, -2), (55, 6, 48, 4), (50, 16, 38, 12)]
    elif tipo == "senalar":
        dedos = [(52, -14, 62, -4)]
    elif tipo == "agarrar":
        dedos = [(50, -16, 30, 50), (54, -5, 30, 60), (53, 6, 26, 62), (48, 15, 22, 56)]
    for (bx, by, L, ang2) in dedos:
        a = math.radians(ang2)
        ex, ey = bx + math.cos(a) * L * 0.55, by + math.sin(a) * L * 0.55
        if tipo == "agarrar":
            pts = [(bx - 8, by), (bx + 10, by + 4), (bx + 8, by + 18)]
        else:
            pts = [(bx - 8, by), (ex, ey)]
        miembro(c, pts, 13, col, 2.6)
        if guante: pass
    # palma
    c.move_to(-6, -22); c.curve_to(20, -28, 48, -24, 56, -12); c.curve_to(60, 0, 58, 14, 50, 22)
    c.curve_to(30, 28, 5, 26, -6, 20); c.close_path()
    c.set_source_rgb(*col); c.fill_preserve(); tinta(c, 3)
    if tipo in ("senalar", "puno", "agarrar"):
        # nudillos de los dedos doblados
        for k in range(3 if tipo == "senalar" else 4):
            yy = -2 + k * 9 if tipo == "senalar" else -16 + k * 10
            c.arc(52, yy, 7, -1.4, 1.4); tinta(c, 2.4)
    # pulgar
    c.move_to(14, -20); c.curve_to(26, -38, 40, -42, 46, -36); c.curve_to(44, -28, 32, -22, 26, -14)
    c.set_source_rgb(*col); c.fill_preserve(); tinta(c, 2.8)
    if guante:
        c.move_to(-6, -22); c.line_to(-6, 20); tinta(c, 2)
        c.set_source_rgba(0.6, 0.62, 0.68, 0.25); c.arc(30, 10, 22, 0, 7); c.fill()
    else:
        linea(c, [(20, 4), (38, 10)], 1.6, TINTA, 0.5)
    c.restore()


# ================================================================== personas
ROPA = {
    "hawaiana": dict(base=(0.86, 0.66, 0.16), dibujo="flores", manga="corta", cuello="abierto"),
    "sudadera": dict(base=(0.27, 0.29, 0.32), playera=(0.93, 0.92, 0.88), dibujo="sudadera", manga="larga"),
    "camisa":   dict(base=(0.9, 0.9, 0.92), dibujo="botones", manga="larga", cuello="cerrado"),
    "traje":    dict(base=(0.14, 0.15, 0.18), dibujo="traje", manga="larga", corbata=(0.6, 0.1, 0.12)),
    "cuadros":  dict(base=(0.65, 0.18, 0.16), dibujo="cuadros", manga="larga", cuello="abierto"),
    "playera":  dict(base=(0.25, 0.45, 0.7), dibujo=None, manga="corta"),
    "bata":     dict(base=(0.96, 0.96, 0.97), dibujo="bata", manga="larga", cuello="abierto"),
    "militar":  dict(base=(0.36, 0.4, 0.26), dibujo="militar", manga="larga"),
}

EXPRESIONES = {
    #            cejas(ángulo, altura)  ojos(apertura)  boca         arrugas
    "neutral":  (0, 0, 1.0, "linea", False),
    "enojado":  (24, 6, 0.75, "grito", True),
    "furioso":  (30, 8, 0.7, "grito", True),
    "miedo":    (-22, -12, 1.45, "oval", True),
    "sorpresa": (-6, -16, 1.45, "oval", False),
    "feliz":    (-4, -4, 0.8, "sonrisa", False),
    "serio":    (10, 2, 0.85, "linea", False),
    "triste":   (-20, -4, 0.85, "triste", False),
    "pensando": (12, -6, 0.9, "torcida", False),
    "malicia":  (18, 2, 0.7, "sonrisa_lado", False),
}

POSES_BRAZOS = {
    # por brazo: codo (x,y), muñeca (x,y) relativos al hombro en unidades de escala; mano: tipo, ángulo
    "relajado":    {"i": ((-25, 190), (-15, 360), "abierta", 95), "d": ((25, 190), (15, 360), "abierta", 85)},
    "senalar_d":   {"i": ((-25, 190), (-15, 360), "abierta", 95), "d": ((130, 80), (235, -70), "senalar", -22)},
    "senalar_i":   {"d": ((25, 190), (15, 360), "abierta", 85), "i": ((-130, 80), (-235, -70), "senalar", 202)},
    "manos_cabeza": {"i": ((-135, -20), (32, -205), "abierta", -78), "d": ((135, -20), (-32, -205), "abierta", -102)},
    "apoyado":     {"i": ((-70, 175), (-60, 330), "abierta", 75), "d": ((70, 175), (60, 330), "abierta", 105)},
    "cruzados":    {"i": ((-60, 175), (120, 200), "abierta", 10), "d": ((60, 175), (-120, 215), "abierta", 170)},
    "pensar":      {"i": ((-60, 175), (110, 210), "abierta", 10), "d": ((80, 180), (0, -10), "abierta", -110)},
    "telefono":    {"i": ((-25, 190), (-15, 360), "abierta", 95), "d": ((110, 90), (75, -60), "abierta", -120)},
    "dinero":      {"i": ((-25, 190), (-15, 360), "abierta", 95), "d": ((120, 40), (160, -150), "abierta", -80)},
}


class Persona:
    """Persona caricatura de la cintura para arriba (o con piernas si piernas=True).

    cfg: piel, pelo ('ondulado','gorro','gorra','corto','calvo','largo','canoso'), color_pelo, ropa (clave de ROPA),
         bigote, barba ('candado','tupida', None), barba_crecida, lentes ('sol','normal', None), cigarro, cicatriz.
    claves: [dict(t, pose, expr, mira, x, y)] en tiempo de escena.
    """

    def __init__(self, cfg, claves, s=1.0, sem=1):
        self.cfg = dict(piel="media", pelo="corto", color_pelo=(0.1, 0.08, 0.07), ropa="playera", bigote=False,
                        barba=None, barba_crecida=False, lentes=None, cigarro=False, cicatriz=False, gorro_color=None)
        self.cfg.update(cfg); self.s = s; self.sem = sem
        prev = dict(pose="relajado", expr="neutral", mira=0.0, x=W / 2, y=400, inclina=0.0)
        self.claves = []
        for c_ in sorted(claves, key=lambda k: k["t"]):
            c_ = dict(c_)
            for k, v in prev.items(): c_.setdefault(k, v)
            self.claves.append(c_); prev = dict(c_); prev.pop("t")

    def estado(self, t):
        cs = self.claves; a = cs[0]
        for k in cs:
            if k["t"] <= t: a = k
        i = cs.index(a); ant = cs[i - 1] if i else a
        kp = E.suave2((t - a["t"]) / 0.35) if hasattr(E, "suave2") else suave((t - a["t"]) / 0.35)
        return a, ant, kp

    def dibujar(self, c, t):
        a, ant, kp = self.estado(t)
        cfg, s = self.cfg, self.s
        piel = PIELES.get(cfg["piel"], cfg["piel"]) if isinstance(cfg["piel"], str) else cfg["piel"]
        x = lerp(ant["x"], a["x"], kp); y = lerp(ant["y"], a["y"], kp)
        mira = lerp(ant["mira"], a["mira"], kp)
        temblor = 0
        if a["expr"] in ("miedo",): temblor = math.sin(t * 38) * 2.2 * s
        if a["expr"] in ("furioso", "enojado"): temblor = math.sin(t * 24) * 1.5 * s
        inc = lerp(ant["inclina"], a["inclina"], kp) + math.sin(t * 1.3 + self.sem) * 1.2
        hx, hy = x + temblor, y + math.sin(t * 2 + self.sem) * 2 * s
        ropa = ROPA[cfg["ropa"]]
        # brazos (interpolados)
        P0, P1 = POSES_BRAZOS[ant["pose"]], POSES_BRAZOS[a["pose"]]
        brazos = {}
        for lado in ("i", "d"):
            e0, w0, _, g0 = P0[lado]; e1, w1, tipo, g1 = P1[lado]
            e = (lerp(e0[0], e1[0], kp), lerp(e0[1], e1[1], kp)); w_ = (lerp(w0[0], w1[0], kp), lerp(w0[1], w1[1], kp))
            g = lerp(g0, g1, kp)
            if tipo == "senalar": w_ = (w_[0] + math.sin(t * 9) * 8, w_[1] + math.cos(t * 9) * 5)  # dedo que sacude
            sx = hx + (-112 if lado == "i" else 112) * s; sy = hy + 178 * s
            brazos[lado] = ((sx, sy), (sx + e[0] * s, sy + e[1] * s), (sx + w_[0] * s, sy + w_[1] * s), tipo if kp > 0.5 else P0[lado][2], g)
        # brazos que van detrás del torso (los que bajan)
        delante = {l: (b[2][1] < hy + 330 * s) for l, b in brazos.items()}
        for l, b in brazos.items():
            if not delante[l]: self._brazo(c, b, piel, ropa, s, l)
        self._torso(c, hx, hy, s, piel, ropa)
        self._cabeza(c, hx, hy, s, piel, a["expr"], ant["expr"], kp, mira, t, inc)
        for l, b in brazos.items():
            if delante[l]: self._brazo(c, b, piel, ropa, s, l)

    # ---------------------------------------------------------------- torso
    def _torso_path(self, c, hx, hy, s):
        c.move_to(hx - 45 * s, hy + 128 * s)
        c.curve_to(hx - 80 * s, hy + 140 * s, hx - 118 * s, hy + 150 * s, hx - 128 * s, hy + 195 * s)
        c.curve_to(hx - 132 * s, hy + 300 * s, hx - 122 * s, hy + 420 * s, hx - 118 * s, hy + 560 * s)
        c.line_to(hx + 118 * s, hy + 560 * s)
        c.curve_to(hx + 122 * s, hy + 420 * s, hx + 132 * s, hy + 300 * s, hx + 128 * s, hy + 195 * s)
        c.curve_to(hx + 118 * s, hy + 150 * s, hx + 80 * s, hy + 140 * s, hx + 45 * s, hy + 128 * s)
        c.close_path()

    def _torso(self, c, hx, hy, s, piel, ropa):
        # cuello
        c.move_to(hx - 36 * s, hy + 70 * s); c.line_to(hx - 40 * s, hy + 140 * s); c.line_to(hx + 40 * s, hy + 140 * s)
        c.line_to(hx + 36 * s, hy + 70 * s); c.close_path(); c.set_source_rgb(*osc(piel, 0.88)); c.fill_preserve(); tinta(c, 3 * s)
        c.move_to(hx - 38 * s, hy + 85 * s); c.curve_to(hx - 10 * s, hy + 110 * s, hx + 10 * s, hy + 110 * s, hx + 38 * s, hy + 85 * s)
        c.line_to(hx + 38 * s, hy + 70 * s); c.line_to(hx - 38 * s, hy + 70 * s); c.close_path()
        c.set_source_rgba(*osc(piel, 0.6), 0.5); c.fill()
        base = ropa["base"]
        tp = lambda cc: self._torso_path(cc, hx, hy, s)
        tp(c); c.set_source_rgb(*base); c.fill()
        d = ropa.get("dibujo")
        if d == "flores": self._flores(c, tp, base, s)
        if d == "cuadros":
            c.save(); tp(c); c.clip()
            for k in range(-12, 13):
                c.rectangle(hx + k * 34 * s, hy, 14 * s, 700 * s); c.rectangle(hx - 200 * s, hy + 120 * s + k * 34 * s, 400 * s, 14 * s)
            c.set_source_rgba(*osc(base, 0.6), 0.5); c.fill(); c.restore()
        if d == "sudadera":
            # playera visible en el frente abierto
            c.move_to(hx - 62 * s, hy + 135 * s); c.line_to(hx + 62 * s, hy + 135 * s); c.line_to(hx + 70 * s, hy + 560 * s)
            c.line_to(hx - 70 * s, hy + 560 * s); c.close_path(); c.set_source_rgb(*ropa["playera"]); c.fill_preserve(); tinta(c, 3 * s)
            c.arc(hx, hy + 330 * s, 45 * s, 0, 7); c.set_source_rgba(0.85, 0.2, 0.2, 0.85); c.fill()
            texto(c, "?", hx, hy + 330 * s, 64 * s, (1, 1, 1), "Inter", peso=cairo.FONT_WEIGHT_BOLD)
            for sx in (-1, 1):  # capucha y cordones
                linea(c, [(hx + sx * 50 * s, hy + 150 * s), (hx + sx * 46 * s, hy + 300 * s)], 4 * s, (0.85, 0.85, 0.85))
                c.arc(hx + sx * 46 * s, hy + 305 * s, 6 * s, 0, 7); c.set_source_rgb(0.85, 0.85, 0.85); c.fill()
            c.move_to(hx - 110 * s, hy + 150 * s); c.curve_to(hx - 90 * s, hy + 110 * s, hx + 90 * s, hy + 110 * s, hx + 110 * s, hy + 150 * s)
            c.curve_to(hx + 70 * s, hy + 170 * s, hx - 70 * s, hy + 170 * s, hx - 110 * s, hy + 150 * s); c.close_path()
            c.set_source_rgb(*osc(base, 0.85)); c.fill_preserve(); tinta(c, 3 * s)
        if ropa.get("cuello") == "abierto":
            c.move_to(hx - 42 * s, hy + 130 * s); c.line_to(hx, hy + 230 * s); c.line_to(hx + 42 * s, hy + 130 * s); c.close_path()
            c.set_source_rgb(*piel); c.fill_preserve(); tinta(c, 3 * s)
            if self.cfg.get("cadena", True):
                c.move_to(hx - 30 * s, hy + 135 * s); c.curve_to(hx - 20 * s, hy + 200 * s, hx + 20 * s, hy + 200 * s, hx + 30 * s, hy + 135 * s)
                c.set_source_rgb(0.85, 0.7, 0.25); c.set_line_width(3.5 * s); c.stroke()
            for sx in (-1, 1):  # solapas
                c.move_to(hx + sx * 42 * s, hy + 128 * s); c.line_to(hx + sx * 95 * s, hy + 150 * s); c.line_to(hx + sx * 12 * s, hy + 245 * s)
                c.line_to(hx + sx * 8 * s, hy + 225 * s); c.close_path(); c.set_source_rgb(*osc(base, 0.9)); c.fill_preserve(); tinta(c, 3 * s)
        if d == "botones":
            for k in range(5): c.arc(hx, hy + (170 + k * 70) * s, 4.5 * s, 0, 7); c.set_source_rgb(0.4, 0.4, 0.45); c.fill()
            linea(c, [(hx, hy + 140 * s), (hx, hy + 560 * s)], 2 * s, TINTA, 0.6)
        if d == "traje":
            c.move_to(hx - 45 * s, hy + 130 * s); c.line_to(hx, hy + 300 * s); c.line_to(hx + 45 * s, hy + 130 * s); c.close_path()
            c.set_source_rgb(0.95, 0.95, 0.95); c.fill_preserve(); tinta(c, 3 * s)
            c.move_to(hx - 10 * s, hy + 140 * s); c.line_to(hx + 10 * s, hy + 140 * s); c.line_to(hx + 14 * s, hy + 280 * s)
            c.line_to(hx, hy + 305 * s); c.line_to(hx - 14 * s, hy + 280 * s); c.close_path(); c.set_source_rgb(*ropa["corbata"]); c.fill_preserve(); tinta(c, 2.5 * s)
        if d == "bata":
            linea(c, [(hx - 10 * s, hy + 230 * s), (hx - 25 * s, hy + 560 * s)], 3 * s, TINTA, 0.7)
            rrect(c, hx + 40 * s, hy + 260 * s, 60 * s, 50 * s, 6 * s); c.set_source_rgb(*TINTA); c.set_line_width(2.5 * s); c.stroke()
        if d == "militar":
            rrect(c, hx - 105 * s, hy + 190 * s, 210 * s, 300 * s, 16 * s); c.set_source_rgb(*osc(base, 0.75)); c.fill_preserve(); tinta(c, 3 * s)
            for k in range(3):
                rrect(c, hx - 90 * s + k * 62 * s, hy + 260 * s, 52 * s, 70 * s, 6 * s); c.set_source_rgb(*osc(base, 0.65)); c.fill_preserve(); tinta(c, 2.5 * s)
        sombreado(c, tp, base, 0.45, 1, 0.32)
        achurado(c, lambda cc: (cc.rectangle(hx + 70 * s, hy + 150 * s, 70 * s, 420 * s)), 9 * s, 0.18)
        tp(c); tinta(c, 3.6 * s)
        # arrugas de tela
        for (a_, b_) in [((-80, 300), (-50, 360)), ((60, 280), (90, 340)), ((-30, 450), (10, 480))]:
            linea(c, [(hx + a_[0] * s, hy + a_[1] * s), (hx + b_[0] * s, hy + b_[1] * s)], 2.2 * s, TINTA, 0.55)

    def _flores(self, c, tp, base, s):
        c.save(); tp(c); c.clip()
        x0, y0, x1, y1 = c.clip_extents()
        r = random.Random(self.sem)
        col = osc(base, 0.72)
        for _ in range(int((x1 - x0) * (y1 - y0) / (5200 * s * s)) + 4):
            fx, fy, fr = r.uniform(x0, x1), r.uniform(y0, y1), r.uniform(16, 30) * s
            for k in range(5):
                a = k * 2 * math.pi / 5 + r.uniform(0, 1)
                c.save(); c.translate(fx + math.cos(a) * fr * 0.55, fy + math.sin(a) * fr * 0.55); c.rotate(a)
                c.scale(1, 0.6); c.arc(0, 0, fr * 0.5, 0, 7); c.restore()
            c.set_source_rgba(*col, 0.85); c.fill_preserve(); c.set_source_rgba(*TINTA, 0.35); c.set_line_width(1.5 * s); c.stroke()
            c.arc(fx, fy, fr * 0.18, 0, 7); c.set_source_rgba(*osc(base, 1.12), 1); c.fill()
            # hojitas
            c.move_to(fx + fr * 0.6, fy + fr * 0.6); c.curve_to(fx + fr * 1.2, fy + fr * 0.5, fx + fr * 1.4, fy + fr * 1.1, fx + fr * 1.5, fy + fr * 1.3)
            c.set_source_rgba(*col, 0.7); c.set_line_width(4 * s); c.stroke()
        c.restore()

    # ---------------------------------------------------------------- brazos
    def _brazo(self, c, b, piel, ropa, s, lado):
        (sx, sy), (ex, ey), (wx, wy), tipo, ang = b
        base = ropa["base"]
        manga_col = base
        if ropa.get("manga") == "larga":
            miembro(c, [(sx, sy), (ex, ey), (wx, wy)], 62 * s, manga_col, 3.4 * s)
            # puño
            miembro(c, [(lerp(ex, wx, 0.88), lerp(ey, wy, 0.88)), (wx, wy)], 60 * s, osc(manga_col, 0.88), 3 * s)
        else:
            miembro(c, [(ex, ey), (wx, wy)], 46 * s, piel, 3.2 * s)
            mid = (lerp(sx, ex, 0.82), lerp(sy, ey, 0.82))
            miembro(c, [(sx, sy), mid], 70 * s, manga_col, 3.4 * s)
            if ropa.get("dibujo") == "flores":
                c.save(); c.set_line_width(64 * s); c.move_to(sx, sy); c.line_to(*mid); c.stroke_to_path() if hasattr(c, "stroke_to_path") else None
                c.restore()
            # vello del antebrazo
            for k in range(5):
                u = 0.25 + k * 0.12
                px, py = lerp(ex, wx, u), lerp(ey, wy, u)
                linea(c, [(px - 4 * s, py - 6 * s), (px + 3 * s, py - 10 * s)], 1.4 * s, TINTA, 0.35)
        if ropa.get("dibujo") == "flores" and ropa.get("manga") == "corta":
            mid = (lerp(sx, ex, 0.82), lerp(sy, ey, 0.82))
            r = random.Random(self.sem + (1 if lado == "d" else 2))
            for k in range(3):
                u = r.uniform(0.15, 0.85); fx, fy = lerp(sx, mid[0], u), lerp(sy, mid[1], u)
                c.arc(fx + r.uniform(-12, 12) * s, fy, 13 * s, 0, 7); c.set_source_rgba(*osc(base, 0.72), 0.8); c.fill()
        ang_real = math.degrees(math.atan2(wy - ey, wx - ex))
        a_mano = ang if tipo != "abierta" or ang is not None else ang_real
        mano(c, wx, wy, a_mano, 1.0 * s, tipo, piel)

    # ---------------------------------------------------------------- cabeza
    def _cara_path(self, c, hx, hy, s):
        c.move_to(hx - 78 * s, hy - 10 * s)
        c.curve_to(hx - 82 * s, hy - 110 * s, hx + 82 * s, hy - 110 * s, hx + 78 * s, hy - 10 * s)
        c.curve_to(hx + 78 * s, hy + 40 * s, hx + 62 * s, hy + 85 * s, hx + 30 * s, hy + 108 * s)
        c.curve_to(hx + 12 * s, hy + 118 * s, hx - 12 * s, hy + 118 * s, hx - 30 * s, hy + 108 * s)
        c.curve_to(hx - 62 * s, hy + 85 * s, hx - 78 * s, hy + 40 * s, hx - 78 * s, hy - 10 * s)
        c.close_path()

    def _cabeza(self, c, hx, hy, s, piel, expr, expr_ant, kp, mira, t, inc):
        cfg = self.cfg
        c.save(); c.translate(hx, hy + 40 * s); c.rotate(math.radians(inc)); c.translate(-hx, -hy - 40 * s)
        pelo, cp = cfg["pelo"], cfg["color_pelo"]
        if pelo == "largo":
            c.move_to(hx - 90 * s, hy - 40 * s); c.curve_to(hx - 110 * s, hy + 120 * s, hx - 80 * s, hy + 170 * s, hx - 40 * s, hy + 160 * s)
            c.line_to(hx + 40 * s, hy + 160 * s); c.curve_to(hx + 80 * s, hy + 170 * s, hx + 110 * s, hy + 120 * s, hx + 90 * s, hy - 40 * s)
            c.close_path(); c.set_source_rgb(*cp); c.fill_preserve(); tinta(c, 3 * s)
        # orejas
        for sx in (-1, 1):
            c.save(); c.translate(hx + sx * 78 * s, hy + 8 * s); c.scale(1, 1.5); c.arc(0, 0, 16 * s, 0, 7); c.restore()
            c.set_source_rgb(*osc(piel, 0.92)); c.fill_preserve(); tinta(c, 3 * s)
            c.arc(hx + sx * 80 * s, hy + 8 * s, 7 * s, -1, 1) if sx > 0 else c.arc(hx + sx * 80 * s, hy + 8 * s, 7 * s, 2.1, 4.2)
            tinta(c, 2 * s, 0.6)
        cara = lambda cc: self._cara_path(cc, hx, hy, s)
        cara(c); c.set_source(degradado(hy - 100 * s, hy + 110 * s, osc(piel, 1.05), osc(piel, 0.95))); c.fill()
        sombreado(c, cara, piel, 0.5, 1 if mira <= 0 else -1, 0.22)
        if cfg.get("barba_crecida"):
            c.save(); cara(c); c.clip()
            r = random.Random(self.sem * 7)
            for _ in range(170):
                a = r.uniform(0.2, math.pi - 0.2); d = r.uniform(0.55, 0.98)
                px = hx + math.cos(a) * 72 * s * d; py = hy + 45 * s + math.sin(a) * 70 * s * d
                if abs(px - hx) < 30 * s and py < hy + 95 * s: continue
                c.new_sub_path(); c.arc(px, py, 1.0 * s, 0, 7)
            c.set_source_rgba(0.2, 0.18, 0.2, 0.4); c.fill(); c.restore()
        if cfg.get("barba") == "candado":
            c.move_to(hx - 40 * s, hy + 70 * s); c.curve_to(hx - 35 * s, hy + 120 * s, hx + 35 * s, hy + 120 * s, hx + 40 * s, hy + 70 * s)
            c.curve_to(hx + 20 * s, hy + 95 * s, hx - 20 * s, hy + 95 * s, hx - 40 * s, hy + 70 * s); c.set_source_rgb(*cp); c.fill_preserve(); tinta(c, 2 * s)
        cara(c); tinta(c, 3.8 * s)
        # expresión interpolada
        e0, e1 = EXPRESIONES[expr_ant], EXPRESIONES[expr]
        ca = lerp(e0[0], e1[0], kp); ch = lerp(e0[1], e1[1], kp); ab = lerp(e0[2], e1[2], kp)
        boca, arr = e1[3] if kp > 0.4 else e0[3], e1[4]
        ox = mira * 14 * s
        parp = ((t + self.sem * 0.53) % 3.3) < 0.11
        # ojos
        for sx in (-1, 1):
            ex, ey = hx + sx * 33 * s + ox, hy - 2 * s
            ry = 11 * s * ab
            if parp:
                linea(c, [(ex - 18 * s, ey), (ex + 18 * s, ey)], 3 * s)
            else:
                c.save(); c.translate(ex, ey); c.scale(1, ry / (18 * s)); c.arc(0, 0, 18 * s, 0, 7); c.restore()
                c.set_source_rgb(0.99, 0.99, 0.98); c.fill_preserve(); tinta(c, 2.4 * s)
                ir = min(9 * s, ry * 0.95)
                c.arc(ex + mira * 6 * s, ey, ir, 0, 7); c.set_source_rgb(0.35, 0.22, 0.12); c.fill()
                c.arc(ex + mira * 6 * s, ey, ir * 0.5, 0, 7); c.set_source_rgb(*TINTA); c.fill()
                c.arc(ex + mira * 6 * s - 3 * s, ey - 3 * s, 2.4 * s, 0, 7); c.set_source_rgb(1, 1, 1); c.fill()
                # párpado superior grueso
                c.save(); c.translate(ex, ey); c.scale(1, ry / (18 * s)); c.arc(0, 0, 18 * s, math.pi * 1.05, math.pi * 1.95); c.restore()
                tinta(c, 4.2 * s)
                if ab > 1.2:  # ojos de susto: línea inferior
                    c.save(); c.translate(ex, ey + 4 * s); c.scale(1, ry / (18 * s)); c.arc(0, 0, 20 * s, 0.3, math.pi - 0.3); c.restore(); tinta(c, 1.4 * s, 0.5)
            # bolsas bajo los ojos
            c.arc(ex, ey + 14 * s, 14 * s, 0.5, math.pi - 0.5); tinta(c, 1.4 * s, 0.4)
            # cejas
            by = ey - 26 * s + ch * s
            ix, oxx = ex - sx * 4 * s, ex + sx * 24 * s
            iy = by + ca * 0.6 * s; oy = by - ca * 0.25 * s
            c.move_to(ix, iy); c.curve_to(lerp(ix, oxx, 0.4), iy - 8 * s, lerp(ix, oxx, 0.7), oy - 8 * s, oxx, oy + 4 * s)
            c.line_to(oxx, oy - 2 * s); c.curve_to(lerp(ix, oxx, 0.7), oy - 15 * s, lerp(ix, oxx, 0.4), iy - 16 * s, ix, iy - 9 * s)
            c.close_path(); c.set_source_rgb(*cp if pelo != "calvo" else (0.15, 0.12, 0.1)); c.fill_preserve(); tinta(c, 1.6 * s)
        if arr:
            for k in range(3):
                linea(c, [(hx - 26 * s + ox, hy - 52 * s - k * 9 * s), (hx + 26 * s + ox, hy - 52 * s - k * 9 * s - (3 if ca > 0 else -3) * s)], 1.8 * s, TINTA, 0.55)
            linea(c, [(hx - 3 * s + ox, hy - 30 * s), (hx - 5 * s + ox, hy - 16 * s)], 1.8 * s, TINTA, 0.5)
            linea(c, [(hx + 5 * s + ox, hy - 30 * s), (hx + 7 * s + ox, hy - 16 * s)], 1.8 * s, TINTA, 0.5)
        # nariz
        nx = hx + ox * 1.3
        c.move_to(nx - 2 * s, hy + 2 * s); c.curve_to(nx - 6 * s, hy + 20 * s, nx - 14 * s, hy + 36 * s, nx - 12 * s, hy + 44 * s)
        c.curve_to(nx - 6 * s, hy + 50 * s, nx + 6 * s, hy + 50 * s, nx + 14 * s, hy + 44 * s); tinta(c, 2.6 * s)
        c.arc(nx - 7 * s, hy + 44 * s, 3 * s, 0, 7); c.arc(nx + 8 * s, hy + 44 * s, 3 * s, 0, 7); c.set_source_rgba(*TINTA, 0.7); c.fill()
        # surcos nasolabiales
        for sx in (-1, 1):
            c.move_to(nx + sx * 20 * s, hy + 46 * s); c.curve_to(nx + sx * 32 * s, hy + 60 * s, nx + sx * 34 * s, hy + 72 * s, nx + sx * 32 * s, hy + 82 * s)
            tinta(c, 1.8 * s, 0.45)
        # boca
        mx, my = hx + ox * 1.2, hy + 72 * s
        if boca == "grito":
            ap = (0.65 + 0.35 * abs(math.sin(t * 8.5))) * s
            c.move_to(mx - 32 * s, my - 6 * s); c.curve_to(mx - 10 * s, my - 14 * s, mx + 10 * s, my - 14 * s, mx + 32 * s, my - 6 * s)
            c.curve_to(mx + 30 * s, my + 30 * ap, mx + 14 * s, my + 46 * ap, mx, my + 46 * ap)
            c.curve_to(mx - 14 * s, my + 46 * ap, mx - 30 * s, my + 30 * ap, mx - 32 * s, my - 6 * s); c.close_path()
            path = c.copy_path(); c.set_source_rgb(0.35, 0.06, 0.06); c.fill()
            c.save(); c.append_path(path); c.clip()
            c.rectangle(mx - 40 * s, my - 20 * s, 80 * s, 18 * s); c.set_source_rgb(1, 1, 0.97); c.fill()
            c.save(); c.translate(mx, my + 46 * ap); c.scale(1, 0.5); c.arc(0, 0, 22 * s, 0, 7); c.restore(); c.set_source_rgb(0.85, 0.35, 0.35); c.fill()
            c.restore(); c.append_path(path); tinta(c, 3 * s)
        elif boca == "oval":
            c.save(); c.translate(mx, my + 8 * s); c.scale(1, 1.3); c.arc(0, 0, 14 * s, 0, 7); c.restore()
            c.set_source_rgb(0.3, 0.05, 0.05); c.fill_preserve(); tinta(c, 3 * s)
        elif boca == "sonrisa":
            c.move_to(mx - 26 * s, my); c.curve_to(mx - 10 * s, my + 16 * s, mx + 10 * s, my + 16 * s, mx + 26 * s, my); tinta(c, 3.2 * s)
        elif boca == "sonrisa_lado":
            c.move_to(mx - 22 * s, my + 4 * s); c.curve_to(mx, my + 8 * s, mx + 14 * s, my + 4 * s, mx + 26 * s, my - 6 * s); tinta(c, 3.2 * s)
        elif boca == "triste":
            c.move_to(mx - 24 * s, my + 8 * s); c.curve_to(mx - 8 * s, my - 4 * s, mx + 8 * s, my - 4 * s, mx + 24 * s, my + 8 * s); tinta(c, 3.2 * s)
        elif boca == "torcida":
            c.move_to(mx - 22 * s, my + 2 * s); c.curve_to(mx - 5 * s, my + 6 * s, mx + 8 * s, my - 2 * s, mx + 22 * s, my - 4 * s); tinta(c, 3 * s)
        else:
            linea(c, [(mx - 24 * s, my + 2 * s), (mx + 24 * s, my + 2 * s)], 3.2 * s)
        if cfg.get("bigote"):
            c.move_to(mx - 44 * s, my + 4 * s)
            c.curve_to(mx - 40 * s, my - 22 * s, mx - 12 * s, my - 26 * s, mx, my - 18 * s)
            c.curve_to(mx + 12 * s, my - 26 * s, mx + 40 * s, my - 22 * s, mx + 44 * s, my + 4 * s)
            c.curve_to(mx + 30 * s, my - 6 * s, mx + 15 * s, my - 8 * s, mx, my - 6 * s)
            c.curve_to(mx - 15 * s, my - 8 * s, mx - 30 * s, my - 6 * s, mx - 44 * s, my + 4 * s); c.close_path()
            c.set_source_rgb(*cp); c.fill_preserve(); tinta(c, 2.2 * s)
        if cfg.get("cigarro"):
            c.save(); c.translate(mx + 18 * s, my + 10 * s); c.rotate(0.35)
            rrect(c, 0, -5 * s, 60 * s, 10 * s, 3 * s); c.set_source_rgb(0.98, 0.98, 0.95); c.fill_preserve(); tinta(c, 2 * s)
            c.rectangle(0, -5 * s, 16 * s, 10 * s); c.set_source_rgb(0.85, 0.6, 0.3); c.fill()
            c.arc(60 * s, 0, 5 * s, 0, 7); c.set_source_rgb(1, 0.4, 0.1); c.fill(); c.restore()
            humo(c, mx + 75 * s, my + 30 * s - 4 * s, t, s)
        if cfg.get("cicatriz"):
            linea(c, [(hx + 40 * s, hy - 30 * s), (hx + 55 * s, hy + 20 * s)], 3 * s, (0.6, 0.25, 0.25))
            for k in range(3): linea(c, [(hx + 38 * s + k * 6 * s, hy - 15 * s + k * 12 * s), (hx + 52 * s + k * 6 * s, hy - 18 * s + k * 12 * s)], 2 * s, (0.6, 0.25, 0.25))
        if cfg.get("lentes") == "sol":
            for sx in (-1, 1):
                rrect(c, hx + sx * 33 * s + ox - 26 * s, hy - 16 * s, 52 * s, 34 * s, 10 * s); c.set_source_rgb(0.08, 0.08, 0.1); c.fill_preserve(); tinta(c, 2.5 * s)
            linea(c, [(hx - 7 * s + ox, hy - 6 * s), (hx + 7 * s + ox, hy - 6 * s)], 4 * s)
        # pelo
        self._pelo(c, hx, hy, s, pelo, cp)
        if expr in ("miedo",):
            k = (t * 0.8) % 1
            c.move_to(hx - 70 * s, hy - 40 * s + k * 50 * s)
            c.curve_to(hx - 62 * s, hy - 25 * s + k * 50 * s, hx - 62 * s, hy - 15 * s + k * 50 * s, hx - 70 * s, hy - 12 * s + k * 50 * s)
            c.curve_to(hx - 78 * s, hy - 15 * s + k * 50 * s, hx - 78 * s, hy - 25 * s + k * 50 * s, hx - 70 * s, hy - 40 * s + k * 50 * s)
            c.set_source_rgba(0.6, 0.85, 1, 1 - k * 0.6); c.fill_preserve(); tinta(c, 1.6 * s, 1 - k * 0.6)
        c.restore()

    def _pelo(self, c, hx, hy, s, pelo, cp):
        r = random.Random(self.sem)
        if pelo in ("ondulado", "canoso"):
            c.move_to(hx - 84 * s, hy + 10 * s)
            pts = 13
            for k in range(pts + 1):
                a = math.pi + k * math.pi / pts
                rr = (98 + r.uniform(0, 26)) * s
                c.curve_to(hx + math.cos(a - 0.12) * rr * 1.15, hy - 22 * s + math.sin(a - 0.12) * rr * 1.1,
                           hx + math.cos(a) * rr * 1.18, hy - 22 * s + math.sin(a) * rr * 1.12,
                           hx + math.cos(a + 0.05) * rr, hy - 22 * s + math.sin(a + 0.05) * rr)
            c.line_to(hx + 84 * s, hy + 10 * s)
            c.curve_to(hx + 70 * s, hy - 45 * s, hx + 40 * s, hy - 55 * s, hx + 10 * s, hy - 62 * s)
            c.curve_to(hx - 20 * s, hy - 40 * s, hx - 55 * s, hy - 55 * s, hx - 72 * s, hy - 30 * s)
            c.close_path(); c.set_source_rgb(*cp); c.fill_preserve(); tinta(c, 3.2 * s)
            for k in range(9):  # mechones
                a = math.pi + 0.3 + k * 0.28
                c.move_to(hx + math.cos(a) * 60 * s, hy - 30 * s + math.sin(a) * 60 * s)
                c.curve_to(hx + math.cos(a) * 80 * s, hy - 40 * s + math.sin(a) * 85 * s, hx + math.cos(a + 0.2) * 95 * s,
                           hy - 30 * s + math.sin(a + 0.2) * 90 * s, hx + math.cos(a + 0.25) * 100 * s, hy - 25 * s + math.sin(a + 0.25) * 92 * s)
                c.set_source_rgba(*(osc(cp, 3.0) if pelo == "canoso" else (1, 1, 1)), 0.3); c.set_line_width(3 * s); c.stroke()
            if pelo == "canoso" or True:
                c.move_to(hx + 20 * s, hy - 100 * s); c.curve_to(hx + 40 * s, hy - 110 * s, hx + 60 * s, hy - 95 * s, hx + 70 * s, hy - 75 * s)
                c.set_source_rgba(0.75, 0.75, 0.78, 0.6); c.set_line_width(7 * s); c.stroke()
        elif pelo == "gorro":
            col = self.cfg.get("gorro_color") or ((0.85, 0.15, 0.15), (0.2, 0.2, 0.22))
            c.move_to(hx - 92 * s, hy - 18 * s); c.curve_to(hx - 100 * s, hy - 150 * s, hx + 100 * s, hy - 150 * s, hx + 92 * s, hy - 18 * s)
            c.close_path(); path = c.copy_path()
            c.set_source_rgb(*col[1]); c.fill()
            c.save(); c.append_path(path); c.clip()
            for k in range(4): c.rectangle(hx - 120 * s, hy - 120 * s + k * 26 * s, 240 * s, 12 * s)
            c.set_source_rgb(*col[0]); c.fill()
            for k in range(-10, 11): linea(c, [(hx + k * 9 * s, hy - 140 * s), (hx + k * 9 * s, hy)], 1 * s, TINTA, 0.25)
            c.restore(); c.append_path(path); tinta(c, 3.2 * s)
            rrect(c, hx - 95 * s, hy - 40 * s, 190 * s, 30 * s, 12 * s); c.set_source_rgb(*osc(col[1], 1.15)); c.fill_preserve(); tinta(c, 3 * s)
            for sx in (-1, 1):
                c.move_to(hx + sx * 82 * s, hy - 12 * s); c.line_to(hx + sx * 92 * s, hy + 25 * s); c.line_to(hx + sx * 74 * s, hy + 8 * s)
                c.set_source_rgb(*self.cfg["color_pelo"]); c.fill()
        elif pelo == "gorra":
            col = self.cfg.get("gorro_color") or ((0.15, 0.3, 0.6),)
            c.move_to(hx - 84 * s, hy - 30 * s); c.curve_to(hx - 90 * s, hy - 145 * s, hx + 90 * s, hy - 145 * s, hx + 84 * s, hy - 30 * s)
            c.close_path(); c.set_source_rgb(*col[0]); c.fill_preserve(); tinta(c, 3.2 * s)
            c.move_to(hx - 84 * s, hy - 30 * s); c.curve_to(hx - 40 * s, hy - 10 * s, hx + 120 * s, hy - 20 * s, hx + 150 * s, hy - 38 * s)
            c.curve_to(hx + 110 * s, hy - 58 * s, hx, hy - 52 * s, hx - 84 * s, hy - 30 * s); c.set_source_rgb(*osc(col[0], 0.8)); c.fill_preserve(); tinta(c, 3 * s)
            c.arc(hx, hy - 128 * s, 7 * s, 0, 7); c.set_source_rgb(*osc(col[0], 0.7)); c.fill()
        elif pelo == "corto":
            c.move_to(hx - 82 * s, hy - 5 * s); c.curve_to(hx - 92 * s, hy - 135 * s, hx + 92 * s, hy - 135 * s, hx + 82 * s, hy - 5 * s)
            c.curve_to(hx + 74 * s, hy - 50 * s, hx + 40 * s, hy - 62 * s, hx + 10 * s, hy - 66 * s)
            c.curve_to(hx - 30 * s, hy - 60 * s, hx - 70 * s, hy - 52 * s, hx - 82 * s, hy - 5 * s); c.close_path()
            c.set_source_rgb(*cp); c.fill_preserve(); tinta(c, 3 * s)
            for k in range(14):
                xx = hx - 70 * s + k * 11 * s
                linea(c, [(xx, hy - 60 * s), (xx + 6 * s, hy - 95 * s)], 1.3 * s, (1, 1, 1), 0.25)
        elif pelo == "calvo":
            for sx in (-1, 1):
                c.move_to(hx + sx * 80 * s, hy - 20 * s); c.curve_to(hx + sx * 88 * s, hy - 40 * s, hx + sx * 84 * s, hy - 60 * s, hx + sx * 70 * s, hy - 66 * s)
                c.line_to(hx + sx * 72 * s, hy - 20 * s); c.close_path(); c.set_source_rgb(*cp); c.fill_preserve(); tinta(c, 2 * s)
            c.arc(hx - 25 * s, hy - 80 * s, 14 * s, 0, 7); c.set_source_rgba(1, 1, 1, 0.35); c.fill()


def humo(c, x, y, t, s=1.0):
    for k in range(3):
        ph = t * 0.9 + k * 0.33
        u = ph % 1
        c.move_to(x, y)
        pts = []
        for j in range(12):
            v = j / 11
            pts.append((x + math.sin(v * 6 + t * 2 + k) * 14 * s * (0.3 + v), y - v * 180 * s))
        for p in pts: c.line_to(*p)
        c.set_source_rgba(0.85, 0.85, 0.88, 0.35 * (1 - k * 0.25)); c.set_line_width((8 - k * 2) * s); c.stroke()


# ================================================================== manos en primera persona
def manos_pov(objeto_izq="matraz", objeto_der="espatula", guantes=True, piel=(0.88, 0.68, 0.52)):
    """Antebrazos del espectador saliendo del borde inferior. Devuelve capa f(c, t)."""
    def f(c, t):
        bob = math.sin(t * 1.6) * 6
        g = (0.97, 0.97, 0.96) if guantes else piel
        # izquierda
        c.save(); c.translate(0, bob)
        miembro(c, [(250, 1160), (520, 860)], 150, piel, 4)
        c.save(); c.translate(560, 860); c.rotate(-0.8); rrect(c, -80, -75, 170, 150, 55); c.restore()
        c.set_source_rgb(*g); c.fill_preserve(); tinta(c, 3.6)
        c.save(); c.translate(500, 920); c.rotate(-0.8); rrect(c, -70, -85, 50, 170, 18); c.restore()
        c.set_source_rgb(*osc(g, 0.93)); c.fill_preserve(); tinta(c, 3)
        if objeto_izq == "matraz": matraz(c, 690, 900, 1.2)
        for k in range(4):  # dedos rodeando el objeto
            miembro(c, [(585, 800 + k * 32), (650, 790 + k * 32), (670, 812 + k * 32)], 30, g, 3)
        miembro(c, [(560, 800), (620, 760), (650, 768)], 30, g, 3)
        c.restore()
        # derecha
        c.save(); c.translate(0, -bob * 0.7)
        miembro(c, [(1700, 1160), (1360, 930)], 150, piel, 4)
        c.save(); c.translate(1330, 935); c.rotate(0.55); rrect(c, -85, -70, 165, 140, 55); c.restore()
        c.set_source_rgb(*g); c.fill_preserve(); tinta(c, 3.6)
        c.save(); c.translate(1405, 985); c.rotate(0.55); rrect(c, 0, -80, 50, 160, 18); c.restore()
        c.set_source_rgb(*osc(g, 0.93)); c.fill_preserve(); tinta(c, 3)
        if objeto_der == "espatula":
            linea(c, [(1290, 935), (1000, 900)], 12, (0.7, 0.72, 0.76)); linea(c, [(1290, 935), (1000, 900)], 2, TINTA, 0.6)
            c.save(); c.translate(960, 896); c.rotate(-0.12); c.scale(1, 0.4); c.arc(0, 0, 50, 0, 7); c.restore()
            c.set_source_rgb(0.75, 0.77, 0.8); c.fill_preserve(); tinta(c, 2.6)
        for k in range(4):
            miembro(c, [(1300 - k * 8, 890 + k * 26), (1250 - k * 8, 900 + k * 26), (1238 - k * 8, 925 + k * 26)], 30, g, 3)
        c.restore()
    return f


def matraz(c, x, y, s=1.0, liquido=(0.75, 0.85, 0.95)):
    c.save(); c.translate(x, y); c.scale(s, s)
    c.move_to(-18, -120); c.line_to(-18, -40); c.line_to(-80, 60); c.curve_to(-88, 78, -78, 90, -60, 90)
    c.line_to(60, 90); c.curve_to(78, 90, 88, 78, 80, 60); c.line_to(18, -40); c.line_to(18, -120); c.close_path()
    path = c.copy_path()
    c.set_source_rgba(0.85, 0.92, 0.96, 0.45); c.fill()
    c.save(); c.append_path(path); c.clip(); c.rectangle(-100, 40, 200, 60); c.set_source_rgba(*liquido, 0.7); c.fill(); c.restore()
    c.append_path(path); tinta(c, 3)
    rrect(c, -24, -130, 48, 14, 5); c.set_source_rgba(0.85, 0.92, 0.96, 0.6); c.fill_preserve(); tinta(c, 2.5)
    linea(c, [(-50, 50), (-30, 10)], 6, (1, 1, 1), 0.7)
    c.restore()


def frasco(c, x, y, w, h, contenido=None, tapa=None, vidrio=(0.85, 0.92, 0.96), etiqueta=None):
    c.save(); c.translate(x, y)
    rrect(c, -w / 2, -h, w, h, w * 0.12); path = c.copy_path()
    c.set_source_rgba(*vidrio, 0.4); c.fill()
    if contenido:
        c.save(); c.append_path(path); c.clip(); contenido(c, w, h); c.restore()
    c.append_path(path); tinta(c, 3)
    if tapa:
        rrect(c, -w * 0.45, -h - h * 0.1, w * 0.9, h * 0.12, 4); c.set_source_rgb(*tapa); c.fill_preserve(); tinta(c, 2.5)
    if etiqueta:
        c.rectangle(-w * 0.35, -h * 0.6, w * 0.7, h * 0.3); c.set_source_rgb(0.95, 0.92, 0.85); c.fill_preserve(); tinta(c, 2)
    linea(c, [(-w * 0.32, -h * 0.85), (-w * 0.32, -h * 0.2)], max(3, w * 0.05), (1, 1, 1), 0.6)
    c.restore()


def cristales(c, w, h):
    r = random.Random(3)
    for _ in range(26):
        x = r.uniform(-w * 0.42, w * 0.42); y = r.uniform(-h * 0.45, -h * 0.05)
        a = r.uniform(-0.8, 0.8); L = r.uniform(30, 70)
        c.save(); c.translate(x, y); c.rotate(a)
        c.move_to(0, -L / 2); c.line_to(14, -L / 4); c.line_to(12, L / 2); c.line_to(-12, L / 2); c.line_to(-14, -L / 4); c.close_path()
        c.set_source_rgba(0.85, 0.93, 1.0, 0.9); c.fill_preserve(); tinta(c, 1.8, 0.7)
        linea(c, [(0, -L / 2), (0, L / 2)], 1.2, (0.6, 0.75, 0.9), 0.8); c.restore()


def fajos(c, x, y, n=6, s=1.0, sem=2):
    r = random.Random(sem)
    for i in range(n):
        fx = x + (i % 3) * 120 * s + r.uniform(-8, 8); fy = y - (i // 3) * 46 * s
        c.save(); c.translate(fx, fy); c.scale(s, s); c.rotate(r.uniform(-0.05, 0.05))
        c.move_to(0, 0); c.line_to(110, -10); c.line_to(150, 10); c.line_to(40, 22); c.close_path()
        c.set_source_rgb(0.62, 0.75, 0.55); c.fill_preserve(); tinta(c, 2.5)
        c.move_to(40, 22); c.line_to(150, 10); c.line_to(150, 48); c.line_to(40, 60); c.close_path()
        c.set_source_rgb(0.5, 0.62, 0.45); c.fill_preserve(); tinta(c, 2.5)
        for k in range(6): linea(c, [(42, 28 + k * 5), (148, 16 + k * 5)], 1, TINTA, 0.35)
        c.move_to(0, 0); c.line_to(40, 22); c.line_to(40, 60); c.line_to(0, 38); c.close_path()
        c.set_source_rgb(0.56, 0.7, 0.5); c.fill_preserve(); tinta(c, 2.5)
        c.move_to(80, -5); c.line_to(95, 15); c.line_to(95, 54); c.line_to(80, 34); c.close_path(); c.set_source_rgb(0.95, 0.9, 0.7); c.fill()
        c.restore()


def lentes_sol(c, x, y, s=1.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    for sx in (-1, 1):
        c.save(); c.translate(sx * 38, 0); c.scale(1, 0.75); c.arc(0, 0, 32, 0, 7); c.restore()
        c.set_source_rgb(0.1, 0.1, 0.12); c.fill_preserve(); tinta(c, 2.5)
    linea(c, [(-8, -6), (8, -6)], 5); linea(c, [(-70, -10), (-110, -16)], 4); linea(c, [(70, -10), (110, -16)], 4)
    c.restore()


# ================================================================== escenario: laboratorio en casa rodante
def casa_rodante(c, hora="dia"):
    """Interior de casa rodante convertida en laboratorio (16:9)."""
    vp = (960, 380)
    c.set_source(degradado(0, H, (0.9, 0.9, 0.88), (0.8, 0.8, 0.78))); c.paint()
    # techo curvo
    c.move_to(0, 0); c.line_to(W, 0); c.line_to(W, 150); c.curve_to(1500, 60, 420, 60, 0, 150); c.close_path()
    c.set_source(degradado(0, 150, (0.82, 0.83, 0.82), (0.93, 0.93, 0.92))); c.fill()
    # pared del fondo (puerta trasera)
    bx0, by0, bx1, by1 = 640, 140, 1280, 640
    rrect(c, bx0, by0, bx1 - bx0, by1 - by0, 50); c.set_source(degradado(by0, by1, (0.92, 0.92, 0.9), (0.84, 0.84, 0.82))); c.fill_preserve(); tinta(c, 3.5)
    E.textura(c, lambda cc: rrect(cc, bx0, by0, bx1 - bx0, by1 - by0, 50), "estuco", 0.2, sem=31)
    for x in (bx0 + 70, bx1 - 300):  # alacenas del fondo
        rrect(c, x, 190, 230, 120, 10); c.set_source_rgb(0.86, 0.86, 0.83); c.fill_preserve(); tinta(c, 3)
        linea(c, [(x + 115, 195), (x + 115, 305)], 2.5)
    rrect(c, 830, 330, 260, 240, 30); c.set_source(degradado(330, 570, (0.7, 0.82, 0.9), (0.9, 0.95, 0.98))); c.fill_preserve(); tinta(c, 3.5)
    # paredes laterales con ventanas redondeadas
    for sx in (-1, 1):
        q = [(960 + sx * 960, 130), (960 + sx * 330, 160), (960 + sx * 330, 640), (960 + sx * 960, 900)]
        E.poli(c, q); c.set_source(degradado(0, 0, (0.86, 0.86, 0.84), (0.93, 0.93, 0.91), q[0][0], q[1][0])); c.fill()
        E.textura(c, E.poli_f(q), "estuco", 0.2, sem=32 + sx)
        xw0, xw1 = 960 + sx * 900, 960 + sx * 620
        c.move_to(xw0, 230); c.line_to(xw1, 250); c.line_to(xw1, 470); c.line_to(xw0, 560); c.close_path()
        c.set_source(degradado(230, 560, (0.75, 0.88, 0.95), (0.95, 0.97, 0.99))); c.fill_preserve()
        c.set_source_rgb(0.75, 0.75, 0.72); c.set_line_width(22); c.stroke_preserve(); tinta(c, 3.2)
        E.haz_luz(c, [(xw0, 230), (xw1, 250), (xw1 + sx * -120, 900), (xw0 + sx * -200, 1080)], 0.25)
    # tubo fluorescente y ventila
    rrect(c, 820, 0, 280, 50, 10); c.set_source_rgb(0.7, 0.7, 0.68); c.fill_preserve(); tinta(c, 3)
    for k in range(7): linea(c, [(840 + k * 38, 8), (840 + k * 38, 42)], 3, TINTA, 0.6)
    c.save(); c.translate(380, 110); c.rotate(0.38)
    rrect(c, -150, -18, 300, 36, 12); c.set_source_rgb(0.75, 0.75, 0.72); c.fill_preserve(); tinta(c, 3)
    rrect(c, -135, -10, 270, 20, 8); c.set_source_rgb(1, 1, 0.94); c.fill(); c.restore()
    g = cairo.RadialGradient(380, 120, 10, 380, 120, 450); g.add_color_stop_rgba(0, 1, 1, 0.9, 0.3); g.add_color_stop_rgba(1, 1, 1, 0.9, 0)
    c.set_source(g); c.arc(380, 120, 450, 0, 7); c.fill()
    # cables por el techo
    for k in range(3):
        c.move_to(0, 60 + k * 18); c.curve_to(300, 120 + k * 10, 500, 30 + k * 15, 800, 70 + k * 10)
        c.set_source_rgb(*TINTA); c.set_line_width(5 - k); c.stroke()
    c.move_to(1200, 60); c.curve_to(1500, 120, 1700, 80, 1920, 140); c.set_source_rgb(*TINTA); c.set_line_width(5); c.stroke()
    # estante metálico izquierdo con matraces
    for xx in (300, 560): linea(c, [(xx, 220), (xx, 700)], 10, (0.6, 0.62, 0.66)); linea(c, [(xx, 220), (xx, 700)], 2, TINTA, 0.6)
    for yy in (300, 420, 540, 660):
        c.move_to(290, yy); c.line_to(570, yy - 6); c.line_to(570, yy + 10); c.line_to(290, yy + 16); c.close_path()
        c.set_source_rgb(0.7, 0.72, 0.76); c.fill_preserve(); tinta(c, 2.5)
    r = random.Random(4)
    for yy in (300, 420, 540, 660):
        for k in range(3):
            matraz(c, 340 + k * 80 + r.uniform(-10, 10), yy - 48, 0.42, liquido=r.choice([(0.8, 0.9, 1), (0.9, 0.8, 0.5), (0.7, 0.9, 0.7)]))
    # alacenas superiores derecha
    c.move_to(1500, 0); c.line_to(1920, 0); c.line_to(1920, 330); c.line_to(1500, 230); c.close_path()
    c.set_source(degradado(0, 330, (0.8, 0.8, 0.77), (0.7, 0.7, 0.67))); c.fill_preserve(); tinta(c, 3.5)
    for x in (1560, 1760):
        E.poli(c, [(x, 20), (x + 150, 20), (x + 150, 255 + (x - 1500) * 0.24), (x, 240 + (x - 1500) * 0.2)])
        c.set_source_rgb(0.78, 0.78, 0.75); c.fill_preserve(); tinta(c, 2.5)
        linea(c, [(x + 130, 150), (x + 130, 200)], 6, (0.55, 0.55, 0.55))
    # tablero eléctrico
    rrect(c, 1640, 470, 260, 150, 8); c.set_source_rgb(0.75, 0.77, 0.78); c.fill_preserve(); tinta(c, 3)
    for k in range(4):
        rrect(c, 1660 + k * 40, 505, 26, 60, 4); c.set_source_rgb(0.25, 0.25, 0.28); c.fill_preserve(); tinta(c, 2)
        rrect(c, 1664 + k * 40, 512 + (k % 2) * 20, 18, 22, 3); c.set_source_rgb(*((0.85, 0.15, 0.15) if k == 1 else (0.95, 0.95, 0.95))); c.fill()
    c.arc(1850, 520, 30, 0, 7); c.set_source_rgb(0.97, 0.97, 0.95); c.fill_preserve(); tinta(c, 2.5)
    linea(c, [(1850, 520), (1866, 500)], 3, (0.8, 0.1, 0.1)); c.arc(1850, 585, 14, 0, 7); c.set_source_rgb(0.3, 0.3, 0.32); c.fill()
    # cajonera derecha
    E.poli(c, [(1540, 640), (1920, 600), (1920, 900), (1540, 860)]); c.set_source_rgb(0.78, 0.78, 0.75); c.fill_preserve(); tinta(c, 3)
    for k in range(3):
        E.poli(c, [(1560, 660 + k * 66), (1700, 648 + k * 66), (1700, 700 + k * 66), (1560, 712 + k * 66)])
        c.set_source_rgb(0.84, 0.84, 0.81); c.fill_preserve(); tinta(c, 2)
    if hora == "noche":
        c.save(); c.set_operator(cairo.OPERATOR_MULTIPLY); c.set_source_rgba(0.45, 0.5, 0.7, 0.5); c.paint(); c.restore()


def mostrador_lab(c, t=0):
    """Mesa metálica en primer plano con material de laboratorio y dinero (va delante de los personajes)."""
    c.move_to(0, 690); c.line_to(W, 690); c.line_to(W, 1080); c.line_to(0, 1080); c.close_path()
    c.set_source(degradado(690, 1080, (0.78, 0.8, 0.82), (0.6, 0.62, 0.66))); c.fill()
    E.textura(c, lambda cc: cc.rectangle(0, 690, W, 390), "concreto", 0.25, sem=50)
    linea(c, [(0, 690), (W, 690)], 4)
    c.rectangle(0, 990, W, 90); c.set_source(degradado(990, 1080, (0.55, 0.57, 0.6), (0.4, 0.42, 0.45))); c.fill(); linea(c, [(0, 990), (W, 990)], 4)
    # charola
    E.poli(c, [(30, 820), (330, 800), (360, 900), (60, 930)]); c.set_source_rgb(0.6, 0.62, 0.66); c.fill_preserve(); tinta(c, 3)
    E.poli(c, [(55, 830), (315, 812), (338, 890), (78, 915)]); c.set_source_rgb(0.5, 0.52, 0.56); c.fill()
    # botellitas y vasos
    for (x, w_, h_, col, tapa) in [(110, 70, 110, None, (0.9, 0.9, 0.88)), (200, 60, 150, None, None), (330, 45, 70, (0.55, 0.3, 0.1), (0.15, 0.15, 0.15)),
                                   (395, 50, 90, (0.35, 0.5, 0.75), (0.95, 0.95, 0.95)), (455, 40, 60, (0.55, 0.3, 0.1), (0.2, 0.2, 0.2))]:
        frasco(c, x, 760, w_, h_, (lambda cc, w, h, col=col: (cc.rectangle(-w, -h * 0.6, 2 * w, h), cc.set_source_rgba(*col, 0.8), cc.fill())) if col else None,
               tapa=tapa, vidrio=(0.85, 0.92, 0.96), etiqueta=col is not None and x > 300)
    # guante suelto
    c.move_to(240, 940); c.curve_to(300, 900, 380, 910, 420, 930); c.curve_to(400, 970, 300, 990, 230, 980); c.close_path()
    c.set_source_rgb(0.96, 0.96, 0.95); c.fill_preserve(); tinta(c, 3)
    # frasco grande con cristales al centro
    frasco(c, 960, 860, 250, 290, lambda cc, w, h: cristales(cc, w, h * 1.5) if False else cristales_bajo(cc, w, h))
    # dinero y lentes
    fajos(c, 1430, 760, 9, 1.0)
    for k in range(3):
        c.save(); c.translate(1350 + k * 140, 900 + (k % 2) * 30); c.rotate(-0.15 + k * 0.12)
        E.billete(c, 0, 0, 1.2) if hasattr(E, "billete") else M.billete(c, 0, 0, 1.2); c.restore()
    lentes_sol(c, 1760, 860, 1.0)


def cristales_bajo(c, w, h):
    r = random.Random(3)
    for _ in range(30):
        x = r.uniform(-w * 0.4, w * 0.4); y = r.uniform(-h * 0.42, -h * 0.06)
        a = r.uniform(-0.9, 0.9); L = r.uniform(30, 70)
        c.save(); c.translate(x, y); c.rotate(a)
        c.move_to(0, -L / 2); c.line_to(13, -L / 4); c.line_to(11, L / 2); c.line_to(-11, L / 2); c.line_to(-13, -L / 4); c.close_path()
        c.set_source_rgba(0.88, 0.95, 1.0, 0.95); c.fill_preserve(); tinta(c, 1.6, 0.7)
        linea(c, [(0, -L / 2), (0, L / 2)], 1.2, (0.6, 0.75, 0.9), 0.8); c.restore()


# ================================================================== demo
def demo_escena(t0=0, t1=5):
    jefe = Persona(dict(piel="morena", pelo="ondulado", color_pelo=(0.1, 0.08, 0.07), ropa="hawaiana", bigote=True, barba_crecida=True),
                   [dict(t=0, pose="senalar_d", expr="furioso", mira=0.6, x=560, y=280, inclina=-4)], s=1.15, sem=3)
    chavo = Persona(dict(piel="clara", pelo="gorra", color_pelo=(0.4, 0.28, 0.15), ropa="sudadera", barba_crecida=True, cigarro=True,
                         gorro_color=((0.2, 0.45, 0.35),)),
                    [dict(t=0, pose="manos_cabeza", expr="miedo", mira=-0.4, x=1340, y=300, inclina=3)], s=1.08, sem=5)
    return Escena(t0, t1, casa_rodante, [jefe, chavo, lambda c, t: mostrador_lab(c, t), manos_pov()],
                  cam=(1.0, 1.05, (960, 540), (960, 520)),
                  pantalla=[])


if __name__ == "__main__":
    import os, subprocess
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "salida"); os.makedirs(out, exist_ok=True)
    e = demo_escena()
    from PIL import Image
    Image.fromarray(cuadro_video([e], 2.0)).save(os.path.join(out, "comic_demo.png"))
    print("foto lista")
    import sys
    if "--video" in sys.argv:
        render_tramo([e], 0, 5, os.path.join(out, "comic_demo.mp4")); print("video listo")
