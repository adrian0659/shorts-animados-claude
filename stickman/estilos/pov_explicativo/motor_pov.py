"""Motor del estilo «POV explicativo»: monigote con ropa, escenarios ilustrados dibujados con código,
etiquetas escritas a mano con flecha, recuadros de detalle y zoom lento por escena.

Todo con pycairo + numpy + ffmpeg. Ver ESTILO.md y videos/escolta.py.
"""
import math, os, random, subprocess
import numpy as np
import cairo

W, H, FPS = 1080, 1920, 30
TINTA = (0.09, 0.09, 0.11)
PIEL = (0.985, 0.98, 0.97)
MARKER = "Permanent Marker"
MANO = "Kalam"


# ------------------------------------------------------------------ utilidades
def lerp(a, b, k): return a + (b - a) * k
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def suave(k): k = clamp(k); return k * k * (3 - 2 * k)
def suave2(k): k = clamp(k); return k * k * k * (k * (k * 6 - 15) + 10)
def rebote(k):
    k = clamp(k); c = 1.7
    return 1 + (c + 1) * (k - 1) ** 3 + c * (k - 1) ** 2
def hexc(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def osc(c, f): return tuple(clamp(v * f) for v in c)
def mezcla(c1, c2, k): return tuple(lerp(a, b, k) for a, b in zip(c1, c2))


def rrect(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def quad(ctx, cx, cy, x, y):
    x0, y0 = ctx.get_current_point()
    ctx.curve_to(x0 + 2 / 3 * (cx - x0), y0 + 2 / 3 * (cy - y0), x + 2 / 3 * (cx - x), y + 2 / 3 * (cy - y), x, y)


def relleno(ctx, color, grosor=5, tinta=TINTA, alfa=1.0):
    """Rellena el camino actual y lo contornea con tinta."""
    if isinstance(color, cairo.Pattern): ctx.set_source(color)
    else: ctx.set_source_rgba(*color, alfa)
    ctx.fill_preserve()
    if grosor:
        ctx.set_source_rgb(*tinta); ctx.set_line_width(grosor)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
    else:
        ctx.new_path()


def degradado(y0, y1, c0, c1, x0=0, x1=0):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    g.add_color_stop_rgb(0, *c0); g.add_color_stop_rgb(1, *c1); return g


def linea(ctx, pts, ancho=5, color=TINTA, alfa=1):
    ctx.set_source_rgba(*color, alfa); ctx.set_line_width(ancho)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*pts[0])
    for p in pts[1:]: ctx.line_to(*p)
    ctx.stroke()


def texto(ctx, txt, x, y, tam, color=TINTA, fuente=MARKER, halo=None, alinear="c", peso=cairo.FONT_WEIGHT_NORMAL,
          interlinea=1.05):
    ctx.select_font_face(fuente, cairo.FONT_SLANT_NORMAL, peso); ctx.set_font_size(tam)
    lineas = txt.split("\n")
    alto = tam * interlinea
    y0 = y - alto * (len(lineas) - 1) / 2
    for i, l in enumerate(lineas):
        e = ctx.text_extents(l)
        dx = {"c": -e.width / 2 - e.x_bearing, "i": -e.x_bearing, "d": -e.width - e.x_bearing}[alinear]
        ctx.move_to(x + dx, y0 + i * alto + tam * 0.36)
        ctx.text_path(l)
    if halo:
        ctx.set_source_rgb(*halo); ctx.set_line_width(tam * 0.22); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
    ctx.set_source_rgb(*color); ctx.fill()


def medir(ctx, txt, tam, fuente=MARKER):
    ctx.select_font_face(fuente, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL); ctx.set_font_size(tam)
    ls = txt.split("\n")
    return max(ctx.text_extents(l).x_advance for l in ls), tam * 1.05 * len(ls)


# ------------------------------------------------------------------ personajes
# Ángulos en grados en espacio de pantalla mirando a la derecha: 0 = abajo, 90 = adelante, 180 = arriba.
# b* = brazo superior, a* = antebrazo, m* = muslo, p* = pierna; i = brazo/pierna de atrás, d = de adelante.
POSES = {
    "parado":    dict(torso=180, cab=0, bi=-10, ai=-4, bd=10, ad=4, mi=-6, pi=-2, md=6, pd=2),
    "guardia":   dict(torso=180, cab=0, bi=-22, ai=42, bd=22, ad=-42, mi=-9, pi=-4, md=9, pd=4),
    "cruzado":   dict(torso=180, cab=0, bi=-26, ai=76, bd=26, ad=-76, mi=-9, pi=-4, md=9, pd=4),
    "cadera":    dict(torso=180, cab=0, bi=-42, ai=16, bd=42, ad=-16, mi=-9, pi=-4, md=9, pd=4),
    "audifono":  dict(torso=180, cab=-6, bi=-10, ai=-4, bd=100, ad=218, mi=-6, pi=-2, md=6, pd=2),
    "senalar":   dict(torso=182, cab=4, bi=-10, ai=-4, bd=88, ad=92, mi=-6, pi=-2, md=8, pd=3),
    "pensar":    dict(torso=178, cab=-8, bi=-24, ai=70, bd=24, ad=195, mi=-6, pi=-2, md=6, pd=2),
    "sorpresa":  dict(torso=180, cab=0, bi=-135, ai=-160, bd=135, ad=160, mi=-12, pi=-6, md=12, pd=6),
    "encoger":   dict(torso=180, cab=8, bi=-55, ai=-135, bd=55, ad=135, mi=-6, pi=-2, md=6, pd=2),
    "agachado":  dict(torso=158, cab=10, bi=30, ai=90, bd=50, ad=110, mi=75, pi=-12, md=40, pd=-35),
    "sentado":   dict(torso=184, cab=0, bi=25, ai=80, bd=35, ad=85, mi=88, pi=2, md=82, pd=-2),
    "dinero":    dict(torso=182, cab=8, bi=-10, ai=-4, bd=118, ad=158, mi=-8, pi=-3, md=8, pd=3),
    "abrir":     dict(torso=184, cab=0, bi=-10, ai=-4, bd=72, ad=88, mi=-10, pi=-4, md=12, pd=5),
    "triste":    dict(torso=174, cab=22, bi=-4, ai=-2, bd=4, ad=2, mi=-5, pi=-2, md=5, pd=2),
    "manos_cara": dict(torso=176, cab=14, bi=-30, ai=150, bd=30, ad=-150, mi=-8, pi=-3, md=8, pd=3),
    "telefono":  dict(torso=180, cab=12, bi=-10, ai=-4, bd=30, ad=150, mi=-6, pi=-2, md=6, pd=2),
    "mesa":      dict(torso=184, cab=0, bi=40, ai=86, bd=50, ad=88, mi=88, pi=2, md=82, pd=-2),
}
ARTIC = list(POSES["parado"].keys())


def vec(ang, largo, f=1):
    a = math.radians(ang); return math.sin(a) * largo * f, math.cos(a) * largo


# trajes: camisa, mangas largas, extra
TRAJES = {
    "escolta": dict(camisa=(0.13, 0.14, 0.17), largo=True, saco=True, corbata=(0.12, 0.12, 0.14), pelo="picos",
                    audifono=True),
    "jefe":    dict(camisa=(0.62, 0.18, 0.16), largo=True, cuadros=(0.35, 0.08, 0.08), pelo="sombrero", bigote=True),
    "soldado": dict(camisa=(0.33, 0.38, 0.24), largo=True, pelo="casco", chaleco=(0.24, 0.27, 0.18)),
    "empresario": dict(camisa=(0.3, 0.38, 0.55), largo=True, saco=True, corbata=(0.75, 0.15, 0.2), pelo="raya",
                       color_pelo=(0.35, 0.22, 0.12)),
    "politico": dict(camisa=(0.2, 0.22, 0.3), largo=True, saco=True, corbata=(0.15, 0.4, 0.75), pelo="raya",
                     color_pelo=(0.55, 0.55, 0.58)),
    "socio":   dict(camisa=(0.85, 0.82, 0.74), largo=True, pelo="raya", color_pelo=(0.12, 0.1, 0.1), bigote=True),
    "socio2":  dict(camisa=(0.2, 0.32, 0.3), largo=False, pelo="corto", color_pelo=(0.1, 0.08, 0.06)),
    "amigo":   dict(camisa=(0.95, 0.65, 0.2), largo=False, pelo="corto", color_pelo=(0.1, 0.08, 0.06)),
    "amiga":   dict(camisa=(0.35, 0.6, 0.85), largo=False, pelo="largo", color_pelo=(0.3, 0.18, 0.1)),
}


class Actor:
    """Monigote con fotogramas clave (tiempos relativos a la escena).
    Cada clave: t, pose, x, y (suelo), cara, mira (-1..1), fac (1 derecha, -1 izquierda), caminar, sudor."""

    def __init__(self, traje, claves, escala=1.0, semilla=1, oscuro=0.0):
        self.tr = TRAJES[traje]; self.s = escala; self.sem = semilla; self.oscuro = oscuro
        prev = dict(pose="parado", x=W / 2, y=1600, cara="neutral", mira=0.0, fac=1, caminar=False, sudor=False)
        self.claves = []
        for c in sorted(claves, key=lambda c: c["t"]):
            c = dict(c)
            for k, v in prev.items(): c.setdefault(k, v)
            self.claves.append(c)
            prev = dict(c); prev.pop("t"); prev["caminar"] = False

    def estado(self, t):
        cs = self.claves; a = cs[0]
        for c in cs:
            if c["t"] <= t: a = c
        i = cs.index(a); b = cs[i + 1] if i + 1 < len(cs) else a
        k = suave((t - a["t"]) / max(1e-6, b["t"] - a["t"])) if b is not a else 0
        if a["caminar"]: k = clamp((t - a["t"]) / max(1e-6, b["t"] - a["t"]))
        ant = cs[i - 1] if i else a
        kp = suave2((t - a["t"]) / 0.4)
        pose = {j: lerp(POSES[ant["pose"]][j], POSES[a["pose"]][j], kp) for j in ARTIC}
        mira = lerp(ant["mira"], a["mira"], kp)
        return pose, lerp(a["x"], b["x"], k), lerp(a["y"], b["y"], k), a, mira, a["caminar"] and b is not a and t < b["t"]

    def dibujar(self, ctx, t):
        pose, x, y, cl, mira, camina = self.estado(t)
        s, f, tr = self.s, cl["fac"], self.tr
        pose = dict(pose)
        pose["torso"] += math.sin(t * 1.4 + self.sem) * 1.0
        pose["cab"] += math.sin(t * 0.9 + self.sem * 2) * 2.5
        resp = math.sin(t * 2.0 + self.sem) * 1.8 * s
        dy = 0
        if camina:
            ph = t * 8.5
            pose.update(mi=math.sin(ph) * 26, md=-math.sin(ph) * 26,
                        bi=-math.sin(ph) * 20 - 6, bd=math.sin(ph) * 20 + 6)
            pose["pi"] = pose["mi"] - max(0, math.sin(ph - 1.3)) * 35
            pose["pd"] = pose["md"] - max(0, -math.sin(ph - 1.3)) * 35
            pose["ai"] = pose["bi"] + 14; pose["ad"] = pose["bd"] + 14
            dy = -abs(math.sin(ph)) * 8 * s
        L = dict(torso=175 * s, cuello=14 * s, br=100 * s, an=94 * s, mu=118 * s, pi=116 * s, r=62 * s)

        def cad(o, a1, l1, a2, l2):
            p1 = (o[0] + vec(a1, l1, f)[0], o[1] + vec(a1, l1, f)[1])
            return p1, (p1[0] + vec(a2, l2, f)[0], p1[1] + vec(a2, l2, f)[1])
        ri, fi = cad((0, 0), pose["mi"], L["mu"], pose["pi"], L["pi"])
        rd, fd = cad((0, 0), pose["md"], L["mu"], pose["pd"], L["pi"])
        baja = max(fi[1], fd[1]) + 14 * s
        cad0 = (x, y + dy - baja)
        T = lambda p: (cad0[0] + p[0], cad0[1] + p[1])
        ri, fi, rd, fd = T(ri), T(fi), T(rd), T(fd)
        hom = (cad0[0] + vec(pose["torso"], L["torso"], f)[0], cad0[1] + vec(pose["torso"], L["torso"], f)[1] + resp)
        cue = (hom[0] + vec(pose["torso"], L["cuello"], f)[0], hom[1] + vec(pose["torso"], L["cuello"], f)[1])
        ca = (cue[0] + vec(pose["torso"] + pose["cab"], L["r"] * 0.92, f)[0],
              cue[1] + vec(pose["torso"] + pose["cab"], L["r"] * 0.92, f)[1])
        hb = (hom[0] - 30 * s * f, hom[1] + 4 * s); hf = (hom[0] + 24 * s * f, hom[1] + 4 * s)
        ci, mi_ = cad(hb, pose["bi"], L["br"], pose["ai"], L["an"])
        cd, md_ = cad(hf, pose["bd"], L["br"], pose["ad"], L["an"])

        # sombra de contacto
        ctx.save(); ctx.translate(x, y); ctx.scale(1, 0.16)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 120 * s)
        g.add_color_stop_rgba(0, 0, 0, 0, 0.32); g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(g); ctx.arc(0, 0, 120 * s, 0, 2 * math.pi); ctx.fill(); ctx.restore()

        g_ = 10 * s
        self._pierna(ctx, cad0, ri, fi, g_, f, s)
        self._brazo(ctx, hb, ci, mi_, g_, s, atras=True)
        self._torso(ctx, cad0, hom, f, s, pose)
        self._pierna(ctx, cad0, rd, fd, g_, f, s)
        self._brazo(ctx, hf, cd, md_, g_, s)
        self._cabeza(ctx, ca, L["r"], f, cl, mira + (f * 0.15), t, pose)

    # -- partes
    def _pierna(self, ctx, c, r, p, g, f, s):
        linea(ctx, [c, r, p], g)
        ctx.save(); ctx.translate(p[0] + 14 * s * f, p[1] + 2 * s); ctx.scale(1, 0.55)
        ctx.arc(0, 0, 30 * s, 0, 2 * math.pi); ctx.restore()
        relleno(ctx, (0.1, 0.1, 0.11), 3 * s)
        ctx.set_source_rgba(1, 1, 1, 0.25); ctx.set_line_width(3 * s)
        ctx.arc(p[0] + 8 * s * f, p[1] - 4 * s, 14 * s, math.pi * 1.15, math.pi * 1.6); ctx.stroke()

    def _brazo(self, ctx, h, c, m, g, s, atras=False):
        tr = self.tr; col = osc(tr["camisa"], 0.82 if atras else 1.0)
        fin = m if tr["largo"] else (lerp(h[0], c[0], 0.75), lerp(h[1], c[1], 0.75))
        if tr["largo"]:
            linea(ctx, [h, c, (lerp(c[0], m[0], 0.86), lerp(c[1], m[1], 0.86))], 36 * s)
            linea(ctx, [h, c, (lerp(c[0], m[0], 0.86), lerp(c[1], m[1], 0.86))], 27 * s, col)
            if tr.get("saco"):
                p = (lerp(c[0], m[0], 0.86), lerp(c[1], m[1], 0.86)); q = (lerp(c[0], m[0], 0.8), lerp(c[1], m[1], 0.8))
                linea(ctx, [q, p], 27 * s, (0.95, 0.95, 0.95)); linea(ctx, [q, p], 3 * s, TINTA, 0.5)
        else:
            linea(ctx, [c, m], g)
            linea(ctx, [h, fin], 36 * s); linea(ctx, [h, fin], 27 * s, col)
        ctx.arc(m[0], m[1], 15 * s, 0, 2 * math.pi); relleno(ctx, PIEL, 4 * s)

    def _torso(self, ctx, c, h, f, s, pose):
        tr = self.tr
        ang = math.radians(pose["torso"]); ux, uy = math.sin(ang) * f, math.cos(ang)   # eje cadera->hombro
        px, py = -uy, ux
        wh, wc = 52 * s, 44 * s
        A = (h[0] + px * wh, h[1] + py * wh); B = (h[0] - px * wh, h[1] - py * wh)
        C = (c[0] - px * wc - ux * 22 * s, c[1] - py * wc - uy * 22 * s)
        D = (c[0] + px * wc - ux * 22 * s, c[1] + py * wc - uy * 22 * s)
        ctx.move_to(*A); ctx.curve_to(A[0] + ux * 10, A[1] - 6 * s, B[0], B[1] - 10 * s, *B)
        ctx.line_to(*C); ctx.line_to(*D); ctx.close_path()
        base = tr["camisa"]
        gr = cairo.LinearGradient(c[0] - 60 * s * f, 0, c[0] + 60 * s * f, 0)
        gr.add_color_stop_rgb(0, *osc(base, 0.78)); gr.add_color_stop_rgb(1, *osc(base, 1.12))
        ctx.save(); relleno(ctx, gr, 5 * s); ctx.restore()
        mid = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2); bot = ((C[0] + D[0]) / 2, (C[1] + D[1]) / 2)
        if tr.get("cuadros"):
            ctx.save(); ctx.move_to(*A); ctx.line_to(*B); ctx.line_to(*C); ctx.line_to(*D); ctx.close_path(); ctx.clip()
            ctx.set_source_rgba(*tr["cuadros"], 0.55); ctx.set_line_width(7 * s)
            for k in range(-6, 7):
                ctx.move_to(mid[0] + k * 22 * s, mid[1] - 40 * s); ctx.line_to(mid[0] + k * 22 * s, bot[1] + 40 * s)
                ctx.move_to(mid[0] - 120 * s, mid[1] + k * 22 * s + 40 * s); ctx.line_to(mid[0] + 120 * s, mid[1] + k * 22 * s + 40 * s)
            ctx.stroke(); ctx.restore()
            linea(ctx, [mid, (lerp(mid[0], bot[0], 0.92), lerp(mid[1], bot[1], 0.92))], 2.5 * s, TINTA, 0.6)
        if tr.get("saco"):
            v = (lerp(mid[0], bot[0], 0.42), lerp(mid[1], bot[1], 0.42))
            ctx.move_to(mid[0] - px * 22 * s, mid[1] - py * 22 * s); ctx.line_to(*v)
            ctx.line_to(mid[0] + px * 22 * s, mid[1] + py * 22 * s); ctx.close_path()
            relleno(ctx, (0.96, 0.96, 0.95), 3 * s)
            if tr.get("corbata"):
                t0 = (mid[0], mid[1] + 6 * s)
                ctx.move_to(t0[0] - 6 * s, t0[1]); ctx.line_to(t0[0] + 6 * s, t0[1])
                ctx.line_to(v[0] + 7 * s, v[1] - 4 * s); ctx.line_to(v[0], v[1] + 8 * s); ctx.line_to(v[0] - 7 * s, v[1] - 4 * s)
                ctx.close_path(); relleno(ctx, tr["corbata"], 2.5 * s)
            linea(ctx, [v, (lerp(mid[0], bot[0], 0.95), lerp(mid[1], bot[1], 0.95))], 2.5 * s, (0.4, 0.4, 0.45))
            for k in (0.62, 0.8):
                ctx.arc(lerp(mid[0], bot[0], k) + px * 6 * s, lerp(mid[1], bot[1], k) + py * 6 * s, 3.5 * s, 0, 7)
                ctx.set_source_rgb(0.45, 0.45, 0.5); ctx.fill()
        elif tr.get("chaleco"):
            ctx.save(); ctx.move_to(*A); ctx.line_to(*B); ctx.line_to(*C); ctx.line_to(*D); ctx.close_path(); ctx.clip()
            rrect(ctx, mid[0] - 50 * s, mid[1] + 18 * s, 100 * s, 130 * s, 12 * s); relleno(ctx, tr["chaleco"], 3 * s)
            for k in range(3):
                rrect(ctx, mid[0] - 40 * s + k * 28 * s, mid[1] + 60 * s, 22 * s, 30 * s, 4 * s)
                relleno(ctx, osc(tr["chaleco"], 0.8), 2 * s)
            ctx.restore()
        else:
            ctx.move_to(mid[0] - px * 20 * s, mid[1] - py * 20 * s)
            ctx.line_to(lerp(mid[0], bot[0], 0.18), lerp(mid[1], bot[1], 0.18))
            ctx.line_to(mid[0] + px * 20 * s, mid[1] + py * 20 * s)
            linea_ = ctx.copy_path(); ctx.new_path()
            ctx.append_path(linea_); ctx.set_source_rgb(*TINTA); ctx.set_line_width(3.5 * s); ctx.stroke()

    def _cabeza(self, ctx, c, r, f, cl, mira, t, pose):
        tr = self.tr; cara = cl["cara"]
        ctx.save(); ctx.translate(*c); ctx.rotate(-math.radians(pose["cab"]) * f * 0.6)
        pelo = tr.get("pelo"); cp = tr.get("color_pelo", (0.07, 0.07, 0.08))
        if pelo == "largo":
            ctx.move_to(-r * 1.05, -r * 0.2); ctx.curve_to(-r * 1.2, r * 0.9, -r * 0.8, r * 1.4, -r * 0.4, r * 1.3)
            ctx.line_to(r * 0.4, r * 1.3); ctx.curve_to(r * 0.8, r * 1.4, r * 1.2, r * 0.9, r * 1.05, -r * 0.2)
            ctx.close_path(); relleno(ctx, cp, 4)
        # cabeza
        ctx.save(); ctx.scale(1, 0.97); ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.restore()
        g = cairo.RadialGradient(-r * 0.3, -r * 0.35, r * 0.2, 0, 0, r * 1.1)
        g.add_color_stop_rgb(0, *PIEL); g.add_color_stop_rgb(1, 0.86, 0.86, 0.88)
        relleno(ctx, g, max(4, 6.5 * self.s))
        ox = mira * r * 0.32
        # pelo
        if pelo == "picos":
            rnd = random.Random(self.sem)
            ctx.move_to(-r * 1.02, -r * 0.05)
            n = 11
            for i in range(n + 1):
                a = math.pi + i * math.pi / n
                rr = r * (1.05 + rnd.uniform(0.12, 0.42))
                aa = a + rnd.uniform(-0.12, 0.12)
                ctx.line_to(math.cos(aa) * rr, math.sin(aa) * rr - r * 0.05)
                if i < n:
                    a2 = a + math.pi / n / 2
                    ctx.line_to(math.cos(a2) * r * 0.96, math.sin(a2) * r * 0.9 - r * 0.05)
            ctx.line_to(r * 1.02, -r * 0.05)
            ctx.curve_to(r * 0.6, -r * 0.42, r * 0.2, -r * 0.18, -r * 0.05 + ox * 0.3, -r * 0.5)
            ctx.curve_to(-r * 0.3, -r * 0.2, -r * 0.6, -r * 0.4, -r * 1.02, -r * 0.05)
            ctx.close_path(); relleno(ctx, cp, 3)
        elif pelo in ("raya", "corto", "largo"):
            ctx.move_to(-r * 1.0, -r * 0.05)
            ctx.curve_to(-r * 1.1, -r * 1.2, r * 1.1, -r * 1.25, r * 1.0, -r * 0.05)
            ctx.curve_to(r * 0.7, -r * 0.55, r * 0.1, -r * 0.45, -r * 0.2 + ox * 0.3, -r * 0.62)
            ctx.curve_to(-r * 0.5, -r * 0.35, -r * 0.8, -r * 0.4, -r * 1.0, -r * 0.05)
            ctx.close_path(); relleno(ctx, cp, 3)
        elif pelo == "sombrero":
            ctx.save(); ctx.translate(0, -r * 0.55)
            ctx.move_to(-r * 1.75, r * 0.05); ctx.curve_to(-r * 1.2, r * 0.4, r * 1.2, r * 0.4, r * 1.75, r * 0.05)
            ctx.curve_to(r * 1.3, r * 0.15, r * 0.9, -r * 0.05, r * 0.7, -r * 0.1)
            ctx.curve_to(r * 0.75, -r * 0.9, r * 0.2, -r * 1.0, 0, -r * 0.75)
            ctx.curve_to(-r * 0.2, -r * 1.0, -r * 0.75, -r * 0.9, -r * 0.7, -r * 0.1)
            ctx.curve_to(-r * 0.9, -r * 0.05, -r * 1.3, r * 0.15, -r * 1.75, r * 0.05)
            ctx.close_path()
            relleno(ctx, degradado(-r, r * 0.3, (0.93, 0.88, 0.74), (0.72, 0.64, 0.48)), 5)
            ctx.move_to(-r * 0.72, -r * 0.18); ctx.curve_to(-r * 0.2, r * 0.0, r * 0.2, r * 0.0, r * 0.72, -r * 0.18)
            ctx.set_source_rgb(0.3, 0.2, 0.12); ctx.set_line_width(r * 0.13); ctx.stroke()
            ctx.restore()
        elif pelo == "casco":
            ctx.move_to(-r * 1.12, -r * 0.08)
            ctx.curve_to(-r * 1.15, -r * 1.35, r * 1.15, -r * 1.35, r * 1.12, -r * 0.08); ctx.close_path()
            relleno(ctx, degradado(-r, 0, (0.42, 0.47, 0.3), (0.26, 0.3, 0.18)), 5)
            ctx.set_source_rgba(0.15, 0.17, 0.1, 0.5)
            for (a, b, rr) in [(-0.5, -0.6, 0.18), (0.3, -0.8, 0.14), (0.6, -0.35, 0.12)]:
                ctx.arc(a * r, b * r, rr * r, 0, 7); ctx.fill()
        if tr.get("audifono"):
            ex = -r * 0.98 * f if True else 0
            ctx.arc(-r * 0.9 * f, r * 0.05, r * 0.11, 0, 7); relleno(ctx, (0.15, 0.15, 0.17), 2)
            ctx.move_to(-r * 0.9 * f, r * 0.15)
            for k in range(1, 7):
                ctx.line_to(-r * 0.9 * f + math.sin(k * 2.2) * r * 0.06 * f, r * 0.15 + k * r * 0.14)
            ctx.set_source_rgba(0.85, 0.85, 0.9, 0.9); ctx.set_line_width(2.4); ctx.stroke()
        # cara
        parp = ((t * 1.0 + self.sem * 0.37) % 3.1) < 0.11
        ey = -r * 0.05; sep = r * 0.33
        ctx.set_source_rgb(*TINTA)
        for lado in (-1, 1):
            ex = ox + lado * sep
            if cara in ("sorpresa", "miedo"):
                ctx.arc(ex, ey, r * 0.15, 0, 7); relleno(ctx, (1, 1, 1), r * 0.06)
                ctx.arc(ex + mira * r * 0.04, ey, r * 0.075, 0, 7); ctx.set_source_rgb(*TINTA); ctx.fill()
            elif parp:
                linea(ctx, [(ex - r * 0.1, ey), (ex + r * 0.1, ey)], r * 0.07)
            elif cara == "lado":
                ctx.arc(ex + r * 0.05 * (1 if mira >= 0 else -1), ey, r * 0.085, 0, 7); ctx.fill()
            else:
                ctx.arc(ex, ey, r * 0.09, 0, 7); ctx.fill()
            # cejas
            cejas = {"serio": (0.0, 0.0), "enojado": (0.12, -0.04), "preocupado": (-0.12, 0.0), "miedo": (-0.16, -0.08),
                     "sorpresa": (0.0, -0.12), "triste": (-0.14, 0.02), "pensar": (0.05 * lado, -0.03), "lado": (0.06, 0.0)}
            if cara in cejas:
                inc, sube = cejas[cara]
                y0 = ey - r * 0.27 + sube * r
                linea(ctx, [(ex - r * 0.13, y0 - inc * r * lado * -1 * 1.0), (ex + r * 0.13, y0 + inc * r * lado * -1 * -1.0)],
                      r * 0.07)
        mx, my = ox * 1.05, r * 0.42
        lw = r * 0.075
        if tr.get("bigote"):
            ctx.move_to(mx - r * 0.34, my - r * 0.02)
            ctx.curve_to(mx - r * 0.25, my - r * 0.22, mx - r * 0.05, my - r * 0.2, mx, my - r * 0.12)
            ctx.curve_to(mx + r * 0.05, my - r * 0.2, mx + r * 0.25, my - r * 0.22, mx + r * 0.34, my - r * 0.02)
            ctx.curve_to(mx + r * 0.15, my - r * 0.08, mx - r * 0.15, my - r * 0.08, mx - r * 0.34, my - r * 0.02)
            relleno(ctx, (0.12, 0.08, 0.06), 2); my += r * 0.08
        if cara in ("sorpresa", "miedo"):
            ctx.save(); ctx.translate(mx, my); ctx.scale(1, 1.25); ctx.arc(0, 0, r * 0.1, 0, 7); ctx.restore()
            relleno(ctx, (0.25, 0.08, 0.08), lw * 0.7)
        elif cara in ("preocupado", "triste"):
            ctx.move_to(mx - r * 0.18, my + r * 0.04)
            ctx.curve_to(mx - r * 0.06, my - r * 0.06, mx + r * 0.06, my - r * 0.06, mx + r * 0.18, my + r * 0.04)
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(lw); ctx.stroke()
        elif cara == "feliz":
            ctx.arc(mx, my - r * 0.12, r * 0.2, math.radians(30), math.radians(150))
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(lw); ctx.stroke()
        elif cara == "pensar":
            linea(ctx, [(mx - r * 0.14, my), (mx + r * 0.05, my - r * 0.02), (mx + r * 0.15, my - r * 0.06)], lw)
        else:  # neutral, serio, enojado, lado
            linea(ctx, [(mx - r * 0.14, my), (mx + r * 0.14, my)], lw)
        if cl.get("sudor"):
            k = (t * 0.7) % 1.0
            sx, sy = r * 0.85 * (-1 if f > 0 else 1), -r * 0.35 + k * r * 0.5
            ctx.move_to(sx, sy - r * 0.2); ctx.curve_to(sx + r * 0.12, sy, sx + r * 0.1, sy + r * 0.13, sx, sy + r * 0.13)
            ctx.curve_to(sx - r * 0.1, sy + r * 0.13, sx - r * 0.12, sy, sx, sy - r * 0.2)
            relleno(ctx, (0.55, 0.8, 1.0), 2.5, alfa=1 - k * 0.6)
        ctx.restore()


# ------------------------------------------------------------------ escenarios (fondos)
def cielo(ctx, c0, c1, y1=H):
    ctx.rectangle(0, 0, W, y1); ctx.set_source(degradado(0, y1, c0, c1)); ctx.fill()


def nubes(ctx, sem, y0, y1, n=5, color=(1, 1, 1), alfa=0.85):
    rnd = random.Random(sem)
    for _ in range(n):
        x, y, s = rnd.uniform(-100, W + 100), rnd.uniform(y0, y1), rnd.uniform(0.6, 1.4)
        ctx.new_path()
        for (dx, dy, r) in [(-70, 10, 45), (-20, -15, 60), (40, 0, 50), (90, 15, 35)]:
            ctx.new_sub_path(); ctx.arc(x + dx * s, y + dy * s, r * s, 0, 7)
        ctx.set_source_rgba(*color, alfa); ctx.fill()


def montanas(ctx, ybase, alto, color, sem, rugo=1.0, nieve=False, borde=0):
    rnd = random.Random(sem)
    pts = [(-50, ybase)]
    x = -50
    while x < W + 100:
        x += rnd.uniform(60, 160)
        pts.append((x, ybase - alto * rnd.uniform(0.35, 1.0) * rugo))
    pts.append((W + 100, ybase)); pts.append((W + 100, H)); pts.append((-50, H))
    ctx.move_to(*pts[0])
    for i in range(1, len(pts) - 3):
        a, b = pts[i - 1], pts[i]
        ctx.curve_to(lerp(a[0], b[0], 0.5), a[1], lerp(a[0], b[0], 0.5), b[1], *b)
    for p in pts[-3:]: ctx.line_to(*p)
    ctx.close_path()
    relleno(ctx, color, borde)


def suelo(ctx, y, c0, c1):
    ctx.rectangle(0, y, W, H - y); ctx.set_source(degradado(y, H, c0, c1)); ctx.fill()
    linea(ctx, [(0, y), (W, y)], 4, TINTA, 0.6)


def agave(ctx, x, y, s=1.0, color=(0.35, 0.55, 0.5)):
    for i in range(9):
        a = math.radians(-80 + i * 20)
        L = (130 if abs(i - 4) < 2 else 100) * s
        tip = (x + math.sin(a) * L, y - math.cos(a) * L * 1.1)
        ctx.move_to(x - 10 * s, y); quad(ctx, lerp(x, tip[0], 0.6) - 12 * s, lerp(y, tip[1], 0.5), *tip)
        quad(ctx, lerp(x, tip[0], 0.6) + 12 * s, lerp(y, tip[1], 0.5), x + 10 * s, y); ctx.close_path()
        relleno(ctx, osc(color, 0.85 + 0.05 * (i % 3)), 3)


def arbol(ctx, x, y, s=1.0, color=(0.3, 0.45, 0.25)):
    ctx.move_to(x - 12 * s, y); ctx.line_to(x - 8 * s, y - 160 * s); ctx.line_to(x + 8 * s, y - 160 * s)
    ctx.line_to(x + 12 * s, y); ctx.close_path(); relleno(ctx, (0.38, 0.26, 0.17), 4)
    ctx.new_path()
    for (dx, dy, r) in [(-60, -190, 70), (40, -200, 80), (-10, -270, 85), (70, -260, 55), (-80, -250, 50)]:
        ctx.new_sub_path(); ctx.arc(x + dx * s, y + dy * s, r * s, 0, 7)
    relleno(ctx, color, 4)
    ctx.new_path()
    for (dx, dy, r) in [(-40, -260, 35), (20, -290, 30)]:
        ctx.new_sub_path(); ctx.arc(x + dx * s, y + dy * s, r * s, 0, 7)
    ctx.set_source_rgba(1, 1, 1, 0.12); ctx.fill()


def rancho(ctx, x0, y, w, h, noche=False):
    """Casa de rancho: muro de adobe crema, techo de teja, arcos."""
    muro = (0.93, 0.85, 0.7) if not noche else (0.5, 0.48, 0.55)
    ctx.rectangle(x0, y - h, w, h); relleno(ctx, degradado(y - h, y, muro, osc(muro, 0.85)), 5)
    # techo de teja
    ctx.move_to(x0 - 30, y - h); ctx.line_to(x0 + 30, y - h - 70); ctx.line_to(x0 + w - 30, y - h - 70)
    ctx.line_to(x0 + w + 30, y - h); ctx.close_path()
    teja = (0.72, 0.3, 0.18) if not noche else (0.35, 0.18, 0.2)
    relleno(ctx, degradado(y - h - 70, y - h, osc(teja, 1.1), osc(teja, 0.8)), 5)
    for k in range(int(w / 40) + 2):
        xx = x0 - 20 + k * 40
        linea(ctx, [(xx, y - h - 2), (xx + 22, y - h - 66)], 3, TINTA, 0.35)
    # arcos del portal
    n = max(2, int(w / 190)); aw = w / n
    for i in range(n):
        ax = x0 + i * aw + aw * 0.15; ww = aw * 0.7; top = y - h * 0.72
        ctx.move_to(ax, y); ctx.line_to(ax, top + ww / 2); ctx.arc(ax + ww / 2, top + ww / 2, ww / 2, math.pi, 0)
        ctx.line_to(ax + ww, y); ctx.close_path()
        relleno(ctx, degradado(top, y, (0.35, 0.25, 0.2) if not noche else (0.12, 0.1, 0.15),
                               (0.2, 0.14, 0.12) if not noche else (0.06, 0.05, 0.08)), 4)
        if noche:
            g = cairo.RadialGradient(ax + ww / 2, top + ww * 0.6, 5, ax + ww / 2, top + ww * 0.6, ww * 0.7)
            g.add_color_stop_rgba(0, 1, 0.75, 0.4, 0.55); g.add_color_stop_rgba(1, 1, 0.7, 0.4, 0)
            ctx.set_source(g); ctx.arc(ax + ww / 2, top + ww * 0.6, ww * 0.7, 0, 7); ctx.fill()
    linea(ctx, [(x0, y - h * 0.08), (x0 + w, y - h * 0.08)], 3, TINTA, 0.3)


def reja(ctx, x0, y, w, h):
    ctx.set_source_rgb(*TINTA)
    for k in range(int(w / 26) + 1):
        xx = x0 + k * 26
        linea(ctx, [(xx, y), (xx, y - h)], 6, (0.12, 0.12, 0.13))
        ctx.move_to(xx - 7, y - h); ctx.line_to(xx, y - h - 18); ctx.line_to(xx + 7, y - h); ctx.close_path()
        relleno(ctx, (0.12, 0.12, 0.13), 0)
    for yy in (y - h * 0.15, y - h * 0.85):
        linea(ctx, [(x0, yy), (x0 + w, yy)], 7, (0.12, 0.12, 0.13))


def camioneta(ctx, x, y, s=1.0, f=1, color=(0.08, 0.08, 0.1), noche=False, faros=False):
    """SUV negra de lado. (x,y) = centro inferior entre ruedas sobre el suelo."""
    ctx.save(); ctx.translate(x, y); ctx.scale(s * f, s)
    ctx.save(); ctx.scale(1, 0.12)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 340); g.add_color_stop_rgba(0, 0, 0, 0, 0.35); g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.set_source(g); ctx.arc(0, 0, 340, 0, 7); ctx.fill(); ctx.restore()
    ctx.move_to(-300, -50); ctx.line_to(-300, -150); ctx.line_to(-270, -175); ctx.line_to(-200, -185)
    ctx.line_to(-170, -290); ctx.line_to(130, -295); ctx.line_to(215, -195); ctx.line_to(290, -180)
    ctx.line_to(305, -140); ctx.line_to(305, -55); ctx.close_path()
    relleno(ctx, degradado(-295, -50, osc(color, 2.4), color), 5)
    # ventanas
    ctx.move_to(-155, -275); ctx.line_to(-30, -278); ctx.line_to(-30, -195); ctx.line_to(-185, -192); ctx.close_path()
    relleno(ctx, degradado(-278, -192, (0.35, 0.4, 0.48), (0.12, 0.13, 0.16)), 4)
    ctx.move_to(-15, -278); ctx.line_to(120, -280); ctx.line_to(195, -196); ctx.line_to(-15, -195); ctx.close_path()
    relleno(ctx, degradado(-278, -192, (0.35, 0.4, 0.48), (0.12, 0.13, 0.16)), 4)
    ctx.set_source_rgba(1, 1, 1, 0.22); ctx.move_to(-120, -272); ctx.line_to(-90, -272); ctx.line_to(-140, -197)
    ctx.line_to(-170, -197); ctx.close_path(); ctx.fill()
    linea(ctx, [(-30, -190), (-30, -60)], 3, (0.3, 0.3, 0.35))
    linea(ctx, [(200, -190), (200, -70)], 3, (0.3, 0.3, 0.35))
    linea(ctx, [(-300, -120), (305, -120)], 3, (0.35, 0.35, 0.4), 0.7)
    for hx in (-60, 165): linea(ctx, [(hx, -165), (hx + 26, -165)], 5, (0.6, 0.6, 0.65))
    rrect(ctx, 275, -170, 30, 22, 5); relleno(ctx, (1, 0.95, 0.75) if faros else (0.85, 0.85, 0.8), 3)
    rrect(ctx, -302, -170, 16, 30, 4); relleno(ctx, (0.8, 0.1, 0.1), 3)
    if faros:
        g = cairo.RadialGradient(300, -160, 5, 300, -160, 260)
        g.add_color_stop_rgba(0, 1, 0.95, 0.7, 0.75); g.add_color_stop_rgba(1, 1, 0.95, 0.7, 0)
        ctx.set_source(g); ctx.move_to(300, -160); ctx.line_to(620, -260); ctx.line_to(620, -20); ctx.close_path(); ctx.fill()
    for wx in (-185, 185):
        ctx.arc(wx, -50, 62, 0, 7); relleno(ctx, (0.06, 0.06, 0.07), 4)
        ctx.arc(wx, -50, 36, 0, 7); relleno(ctx, degradado(-86, -14, (0.8, 0.8, 0.85), (0.45, 0.45, 0.5)), 3)
        for k in range(5):
            a = k * 2 * math.pi / 5
            linea(ctx, [(wx, -50), (wx + math.cos(a) * 32, -50 + math.sin(a) * 32)], 4, (0.3, 0.3, 0.35))
        ctx.arc(wx, -50, 9, 0, 7); relleno(ctx, (0.3, 0.3, 0.35), 2)
    ctx.restore()


def helicoptero(ctx, x, y, s, t, f=1, color=(0.3, 0.35, 0.25), luz=False):
    ctx.save(); ctx.translate(x, y); ctx.scale(s * f, s); ctx.rotate(math.radians(-6))
    if luz:
        g = cairo.LinearGradient(0, 40, 0, 1400)
        g.add_color_stop_rgba(0, 1, 1, 0.85, 0.45); g.add_color_stop_rgba(1, 1, 1, 0.85, 0)
        ctx.set_source(g); ctx.move_to(-10, 40); ctx.line_to(-260, 1400); ctx.line_to(240, 1400); ctx.line_to(10, 40)
        ctx.close_path(); ctx.fill()
    ctx.move_to(-60, -20); ctx.line_to(-330, -45); ctx.line_to(-340, -10); ctx.line_to(-60, 20); ctx.close_path()
    relleno(ctx, color, 4)
    ctx.move_to(-330, -45); ctx.line_to(-350, -95); ctx.line_to(-320, -95); ctx.line_to(-300, -40); ctx.close_path()
    relleno(ctx, color, 4)
    ctx.save(); ctx.scale(1.35, 1); ctx.arc(0, 0, 85, 0, 7); ctx.restore(); relleno(ctx, degradado(-85, 85, osc(color, 1.3), osc(color, 0.7)), 5)
    ctx.move_to(30, -60); ctx.curve_to(110, -55, 120, 10, 105, 25); ctx.line_to(35, 20); ctx.close_path()
    relleno(ctx, (0.55, 0.7, 0.8), 4)
    linea(ctx, [(-70, 85), (-80, 105), (80, 105), (95, 90)], 6)
    linea(ctx, [(-40, 85), (-50, 105)], 5); linea(ctx, [(50, 85), (50, 105)], 5)
    linea(ctx, [(0, -85), (0, -105)], 8)
    sp = math.sin(t * 40)
    ctx.save(); ctx.translate(0, -108); ctx.scale(1, 0.12)
    ctx.set_source_rgba(0.1, 0.1, 0.1, 0.55); ctx.move_to(-260 * sp, -20); ctx.line_to(260 * sp, 20); ctx.line_to(260 * sp, -20)
    ctx.line_to(-260 * sp, 20); ctx.close_path(); ctx.fill()
    ctx.set_source_rgba(0.1, 0.1, 0.1, 0.18); ctx.arc(0, 0, 270, 0, 7); ctx.fill(); ctx.restore()
    ctx.save(); ctx.translate(-340, -70); ctx.rotate(t * 30)
    linea(ctx, [(-40, 0), (40, 0)], 5, TINTA, 0.6); ctx.restore()
    ctx.restore()


def interior(ctx, pared, piso, y_piso=1380, techo=True, zocalo=(0.6, 0.15, 0.15)):
    ctx.rectangle(0, 0, W, y_piso); ctx.set_source(degradado(0, y_piso, osc(pared, 1.06), osc(pared, 0.9))); ctx.fill()
    if techo:
        ctx.rectangle(0, 0, W, 90); ctx.set_source(degradado(0, 90, osc(pared, 0.8), osc(pared, 0.95))); ctx.fill()
        linea(ctx, [(0, 90), (W, 90)], 4, TINTA, 0.5)
    ctx.rectangle(0, y_piso, W, H - y_piso); ctx.set_source(degradado(y_piso, H, osc(piso, 0.9), osc(piso, 1.12))); ctx.fill()
    for k in range(-6, 7):
        linea(ctx, [(W / 2 + k * 90, y_piso), (W / 2 + k * 330, H)], 2.5, TINTA, 0.12)
    for yy in (y_piso + 70, y_piso + 190, y_piso + 380):
        linea(ctx, [(0, yy), (W, yy)], 2.5, TINTA, 0.1)
    ctx.rectangle(0, y_piso - 26, W, 26); relleno(ctx, zocalo, 0)
    linea(ctx, [(0, y_piso), (W, y_piso)], 5, TINTA, 0.8)
    linea(ctx, [(0, y_piso - 26), (W, y_piso - 26)], 3, TINTA, 0.5)


def ventana(ctx, x, y, w, h, c0=(0.55, 0.75, 0.95), c1=(0.85, 0.92, 0.98), marco=(0.95, 0.95, 0.95), paisaje=True):
    rrect(ctx, x - 14, y - 14, w + 28, h + 28, 6); relleno(ctx, marco, 4)
    ctx.save(); ctx.rectangle(x, y, w, h); ctx.clip()
    ctx.rectangle(x, y, w, h); ctx.set_source(degradado(y, y + h, c0, c1)); ctx.fill()
    if paisaje:
        ctx.translate(x, y + h * 0.15); ctx.scale(w / W, h / H * 1.4)
        montanas(ctx, H * 0.75, 300, mezcla(c1, (0.4, 0.5, 0.45), 0.5), 7)
        montanas(ctx, H * 0.85, 200, mezcla(c1, (0.3, 0.4, 0.3), 0.7), 8)
    ctx.restore()
    linea(ctx, [(x + w / 2, y), (x + w / 2, y + h)], 7, marco); linea(ctx, [(x, y + h / 2), (x + w, y + h / 2)], 7, marco)
    ctx.rectangle(x, y, w, h); ctx.set_source_rgb(*TINTA); ctx.set_line_width(4); ctx.stroke()
    ctx.set_source_rgba(1, 1, 1, 0.25); ctx.move_to(x + w * 0.1, y + h * 0.9); ctx.line_to(x + w * 0.3, y + h * 0.1)
    ctx.line_to(x + w * 0.42, y + h * 0.1); ctx.line_to(x + w * 0.22, y + h * 0.9); ctx.close_path(); ctx.fill()


def lampara(ctx, x, y, w=260, prendida=True):
    rrect(ctx, x - w / 2, y, w, 22, 8); relleno(ctx, (0.97, 0.97, 0.95) if prendida else (0.6, 0.6, 0.6), 3)
    if prendida:
        g = cairo.LinearGradient(0, y, 0, y + 400); g.add_color_stop_rgba(0, 1, 1, 0.9, 0.28); g.add_color_stop_rgba(1, 1, 1, 0.9, 0)
        ctx.set_source(g); ctx.move_to(x - w / 2, y + 22); ctx.line_to(x + w / 2, y + 22); ctx.line_to(x + w, y + 400)
        ctx.line_to(x - w, y + 400); ctx.close_path(); ctx.fill()


def cuadro_pared(ctx, x, y, w, h, dibujo=None, titulo=None, fondo=(0.95, 0.94, 0.9)):
    ctx.save(); ctx.translate(6, 8); rrect(ctx, x, y, w, h, 4); ctx.set_source_rgba(0, 0, 0, 0.18); ctx.fill(); ctx.restore()
    rrect(ctx, x, y, w, h, 4); relleno(ctx, fondo, 4)
    if titulo: texto(ctx, titulo, x + w / 2, y + 34, 30, TINTA, MARKER)
    if dibujo:
        ctx.save(); ctx.rectangle(x + 8, y + 8, w - 16, h - 16); ctx.clip(); dibujo(ctx, x, y, w, h); ctx.restore()


def mesa(ctx, x, y, w=520, alto=300, color=(0.45, 0.3, 0.2)):
    ctx.rectangle(x - w / 2, y - alto, w, 34); relleno(ctx, degradado(y - alto, y - alto + 34, osc(color, 1.2), color), 5)
    for lx in (x - w / 2 + 30, x + w / 2 - 50):
        ctx.rectangle(lx, y - alto + 34, 20, alto - 34); relleno(ctx, osc(color, 0.8), 4)


def silla(ctx, x, y, f=1, alto_asiento=250, color=(0.4, 0.25, 0.15)):
    ctx.save(); ctx.translate(x, y); ctx.scale(f, 1)
    ctx.rectangle(-70, -alto_asiento - 20, 150, 26); relleno(ctx, color, 4)
    ctx.rectangle(-75, -alto_asiento - 230, 24, 230); relleno(ctx, osc(color, 0.9), 4)
    ctx.rectangle(-70, -alto_asiento - 200, 20, 120); relleno(ctx, osc(color, 1.15), 3)
    for lx in (-70, 55): ctx.rectangle(lx, -alto_asiento + 6, 16, alto_asiento - 6); relleno(ctx, osc(color, 0.8), 4)
    ctx.restore()


def botella(ctx, x, y, s=1, color=(0.55, 0.4, 0.15)):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.move_to(-22, 0); ctx.line_to(-22, -70); ctx.curve_to(-22, -95, -8, -100, -8, -120); ctx.line_to(-8, -145)
    ctx.line_to(8, -145); ctx.line_to(8, -120); ctx.curve_to(8, -100, 22, -95, 22, -70); ctx.line_to(22, 0); ctx.close_path()
    relleno(ctx, color, 3, alfa=0.9); rrect(ctx, -18, -60, 36, 34, 3); relleno(ctx, (0.95, 0.92, 0.8), 2)
    ctx.restore()


def billete(ctx, x, y, s=1, rot=0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s)
    rrect(ctx, -70, -32, 140, 64, 6); relleno(ctx, degradado(-32, 32, (0.6, 0.82, 0.55), (0.42, 0.65, 0.4)), 3)
    ctx.arc(0, 0, 18, 0, 7); relleno(ctx, (0.75, 0.9, 0.7), 2)
    texto(ctx, "$", 0, 0, 26, (0.2, 0.4, 0.2), "Inter", peso=cairo.FONT_WEIGHT_BOLD)
    ctx.restore()


def calendario(ctx, x, y, s, dia, mes, anio=None, color=(0.85, 0.15, 0.15)):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    rrect(ctx, -110, -120, 220, 240, 18); relleno(ctx, (0.98, 0.98, 0.96), 5)
    ctx.save(); rrect(ctx, -110, -120, 220, 240, 18); ctx.clip(); ctx.rectangle(-110, -120, 220, 70); ctx.set_source_rgb(*color); ctx.fill(); ctx.restore()
    rrect(ctx, -110, -120, 220, 240, 18); ctx.set_source_rgb(*TINTA); ctx.set_line_width(5); ctx.stroke()
    texto(ctx, mes, 0, -86, 40, (1, 1, 1), MARKER)
    texto(ctx, dia, 0, 20, 100, TINTA, "Inter", peso=cairo.FONT_WEIGHT_BOLD)
    if anio: texto(ctx, anio, 0, 92, 34, (0.4, 0.4, 0.4), MARKER)
    for rx in (-55, 55):
        rrect(ctx, rx - 8, -138, 16, 38, 6); relleno(ctx, (0.5, 0.5, 0.55), 3)
    ctx.restore()


MEXICO = [(-117.1, 32.5), (-114.7, 32.7), (-111.0, 31.3), (-108.2, 31.3), (-108.2, 31.8), (-106.5, 31.8), (-104.5, 29.6),
          (-103.0, 29.0), (-102.3, 29.9), (-101.4, 29.8), (-100.0, 28.2), (-99.5, 27.5), (-97.4, 25.9), (-97.6, 24.0),
          (-97.8, 22.3), (-97.2, 20.6), (-96.3, 19.3), (-95.0, 18.6), (-94.5, 18.2), (-92.5, 18.6), (-91.3, 18.9),
          (-90.4, 20.9), (-90.3, 21.1), (-88.0, 21.6), (-86.8, 21.3), (-87.4, 19.5), (-88.3, 18.5), (-89.1, 17.8),
          (-90.98, 17.8), (-91.0, 17.25), (-91.4, 16.1), (-90.4, 16.1), (-92.2, 15.0), (-92.2, 14.5), (-93.5, 15.9),
          (-94.8, 16.2), (-96.5, 15.7), (-98.5, 16.3), (-100.5, 17.2), (-101.9, 17.9), (-103.5, 18.3), (-104.5, 19.1),
          (-105.5, 20.4), (-105.3, 21.5), (-105.7, 22.6), (-106.9, 23.8), (-108.3, 25.2), (-109.4, 26.0), (-110.5, 27.9),
          (-111.6, 28.9), (-112.4, 29.8), (-113.1, 31.2), (-114.8, 31.8), (-114.3, 30.0), (-113.0, 28.5), (-112.2, 27.2),
          (-111.3, 25.8), (-110.6, 24.2), (-109.9, 22.9), (-110.4, 23.5), (-111.9, 24.6), (-112.2, 25.9), (-113.2, 26.7),
          (-114.5, 27.8), (-114.1, 28.5), (-115.7, 29.8), (-116.7, 31.6)]


def mapa_xy(lon, lat, x, y, ancho):
    return x + (lon + 117.5) / 31.5 * ancho, y + (33.0 - lat) / 31.5 * ancho * 1.07


def mapa_mexico(ctx, x, y, ancho, color=(0.93, 0.88, 0.72)):
    pts = [mapa_xy(lo, la, x, y, ancho) for lo, la in MEXICO]
    ctx.save(); ctx.translate(8, 10); ctx.move_to(*pts[0])
    for p in pts[1:]: ctx.line_to(*p)
    ctx.close_path(); ctx.set_source_rgba(0, 0, 0, 0.2); ctx.fill(); ctx.restore()
    ctx.move_to(*pts[0])
    for p in pts[1:]: ctx.line_to(*p)
    ctx.close_path(); relleno(ctx, color, 5)


# ------------------------------------------------------------------ etiquetas e insertos
class Etiqueta:
    """Texto escrito a mano con flecha curva hacia un objetivo. Coordenadas del mundo de la escena."""

    def __init__(self, txt, t0, x, y, objetivo=None, tam=58, color=TINTA, curva=0.35, halo=(1, 1, 1),
                 t1=None, palomita=False, tachar=False, rot=-3):
        self.txt, self.t0, self.x, self.y, self.obj = txt, t0, x, y, objetivo
        self.tam, self.color, self.curva, self.halo, self.t1 = tam, color, curva, halo, t1
        self.pal, self.tachar, self.rot = palomita, tachar, rot

    def dibujar(self, ctx, t):
        if t < self.t0 or (self.t1 is not None and t > self.t1): return
        k = rebote((t - self.t0) / 0.32)
        ctx.save(); ctx.translate(self.x, self.y); ctx.rotate(math.radians(self.rot)); ctx.scale(k, k)
        texto(ctx, self.txt, 0, 0, self.tam, self.color, MARKER, halo=self.halo)
        w, h = medir(ctx, self.txt, self.tam)
        if self.pal:
            kk = clamp((t - self.t0 - 0.3) / 0.25)
            px = w / 2 + self.tam * 0.45
            pts = [(px - 20, 0), (px - 4, 18), (px + 30, -26)]
            ctx.save(); ctx.set_source_rgb(1, 1, 1); ctx.set_line_width(22); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(*pts[0]); ctx.line_to(*pts[1]); ctx.line_to(*pts[2]); ctx.stroke(); ctx.restore()
            if kk > 0: linea(ctx, pts[:2] + [(lerp(pts[1][0], pts[2][0], kk), lerp(pts[1][1], pts[2][1], kk))], 11, (0.15, 0.7, 0.25))
        if self.tachar:
            kk = clamp((t - self.t0 - 0.35) / 0.3)
            if kk > 0:
                linea(ctx, [(-w / 2 - 10, 8), (lerp(-w / 2 - 10, w / 2 + 10, kk), lerp(8, -4, kk))], self.tam * 0.16, (0.85, 0.1, 0.1))
        ctx.restore()
        if self.obj:
            ka = clamp((t - self.t0 - 0.12) / 0.4)
            if ka <= 0: return
            w, h = medir(ctx, self.txt, self.tam)
            ox, oy = self.obj
            dx, dy = ox - self.x, oy - self.y
            # sale del borde del texto más cercano al objetivo
            if abs(dx) / (w / 2 + 1) > abs(dy) / (h / 2 + 1):
                sx, sy = self.x + math.copysign(w / 2 + 14, dx), self.y
            else:
                sx, sy = self.x, self.y + math.copysign(h / 2 + 10, dy)
            L = math.hypot(ox - sx, oy - sy) + 1e-6
            nx, ny = -(oy - sy) / L, (ox - sx) / L
            cx, cy = (sx + ox) / 2 + nx * L * self.curva, (sy + oy) / 2 + ny * L * self.curva
            pts = []
            for i in range(31):
                u = i / 30 * ka
                pts.append(((1 - u) ** 2 * sx + 2 * (1 - u) * u * cx + u * u * ox,
                            (1 - u) ** 2 * sy + 2 * (1 - u) * u * cy + u * u * oy))
            linea(ctx, pts, 13, self.halo or (1, 1, 1)); linea(ctx, pts, 6, self.color)
            if ka > 0.97:
                (ax, ay), (bx, by) = pts[-3], pts[-1]
                a = math.atan2(by - ay, bx - ax)
                tip = [(bx + math.cos(a + math.pi - 0.5) * 30, by + math.sin(a + math.pi - 0.5) * 30), (bx, by),
                       (bx + math.cos(a + math.pi + 0.5) * 30, by + math.sin(a + math.pi + 0.5) * 30)]
                linea(ctx, tip, 13, self.halo or (1, 1, 1)); linea(ctx, tip, 6, self.color)


class Inserto:
    """Recuadro de detalle con borde blanco (en coordenadas de pantalla)."""

    def __init__(self, t0, x, y, w, h, dibujo, t1=None):
        self.t0, self.x, self.y, self.w, self.h, self.dib, self.t1 = t0, x, y, w, h, dibujo, t1

    def dibujar(self, ctx, t):
        if t < self.t0 or (self.t1 is not None and t > self.t1): return
        k = rebote((t - self.t0) / 0.35)
        ctx.save(); ctx.translate(self.x + self.w / 2, self.y + self.h / 2); ctx.scale(k, k)
        ctx.translate(-self.w / 2, -self.h / 2)
        ctx.save(); ctx.translate(10, 14); rrect(ctx, 0, 0, self.w, self.h, 22); ctx.set_source_rgba(0, 0, 0, 0.3); ctx.fill(); ctx.restore()
        rrect(ctx, 0, 0, self.w, self.h, 22); ctx.set_source_rgb(1, 1, 1); ctx.fill()
        rrect(ctx, 12, 12, self.w - 24, self.h - 24, 14); ctx.save(); ctx.clip()
        self.dib(ctx, self.w, self.h, t - self.t0); ctx.restore()
        rrect(ctx, 12, 12, self.w - 24, self.h - 24, 14); ctx.set_source_rgb(*TINTA); ctx.set_line_width(4); ctx.stroke()
        rrect(ctx, 0, 0, self.w, self.h, 22); ctx.set_line_width(5); ctx.stroke()
        ctx.restore()


# ------------------------------------------------------------------ escena y render
class Escena:
    """Una toma: fondo fijo (cacheado) + capas animadas + etiquetas + cámara lenta.

    fondo(ctx): dibuja el escenario estático.
    capas: objetos con .dibujar(ctx, t) o funciones f(ctx, t) en coordenadas del mundo.
    pantalla: capas en coordenadas de pantalla (insertos, títulos).
    cam: (zoom0, zoom1, (cx0, cy0), (cx1, cy1)).
    tinte: (r,g,b,a) encima de todo (noche, alarma).
    """

    def __init__(self, t0, t1, fondo, capas=(), pantalla=(), cam=(1.0, 1.07, (W / 2, H / 2), (W / 2, H / 2)),
                 tinte=None, sacudidas=(), frente=()):
        self.t0, self.t1, self.fondo = t0, t1, fondo
        self.capas, self.pantalla, self.cam = list(capas), list(pantalla), cam
        self.tinte, self.frente = tinte, list(frente)
        self.sac = [x if isinstance(x, tuple) else (x, 22) for x in sacudidas]
        self._bg = None

    def bg(self):
        if self._bg is None:
            s = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); c = cairo.Context(s)
            c.set_source_rgb(1, 1, 1); c.paint(); self.fondo(c); self._bg = s
        return self._bg

    def camara(self, t):
        z0, z1, a, b = self.cam
        k = suave((t) / max(0.1, self.t1 - self.t0)) * 0.6 + clamp(t / max(0.1, self.t1 - self.t0)) * 0.4
        z = lerp(z0, z1, k); cx, cy = lerp(a[0], b[0], k), lerp(a[1], b[1], k)
        hw, hh = W / 2 / z, H / 2 / z
        cx = clamp(cx, hw, W - hw); cy = clamp(cy, hh, H - hh)
        dx = dy = 0
        for (ts, fza) in self.sac:
            if 0 <= t - ts < 0.45:
                d = (1 - (t - ts) / 0.45) ** 2 * fza
                dx += math.sin(t * 95) * d; dy += math.cos(t * 81) * d
        return z, cx, cy, dx, dy

    def cuadro(self, t, ctx):
        z, cx, cy, dx, dy = self.camara(t)
        ctx.save()
        ctx.translate(W / 2 + dx, H / 2 + dy); ctx.scale(z, z); ctx.translate(-cx, -cy)
        ctx.set_source_surface(self.bg(), 0, 0); ctx.get_source().set_filter(cairo.FILTER_GOOD); ctx.paint()
        for c in self.capas:
            (c.dibujar if hasattr(c, "dibujar") else (lambda cc, tt, c=c: c(cc, tt)))(ctx, t)
        ctx.restore()
        if self.tinte:
            r, g, b, a = self.tinte if not callable(self.tinte) else self.tinte(t)
            if a > 0:
                ctx.save(); ctx.set_operator(cairo.OPERATOR_MULTIPLY); ctx.set_source_rgba(r, g, b, a); ctx.paint(); ctx.restore()
        ctx.save(); ctx.translate(W / 2 + dx, H / 2 + dy); ctx.scale(z, z); ctx.translate(-cx, -cy)
        for c in self.frente:
            (c.dibujar if hasattr(c, "dibujar") else (lambda cc, tt, c=c: c(cc, tt)))(ctx, t)
        ctx.restore()
        for c in self.pantalla:
            (c.dibujar if hasattr(c, "dibujar") else (lambda cc, tt, c=c: c(cc, tt)))(ctx, t)


_VIÑETA = None


def viñeta(ctx):
    global _VIÑETA
    if _VIÑETA is None:
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(s)
        g = cairo.RadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 0.75)
        g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.38)
        c.set_source(g); c.paint(); _VIÑETA = s
    ctx.set_source_surface(_VIÑETA, 0, 0); ctx.paint()


def cuadro_video(escenas, t):
    sup = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); ctx = cairo.Context(sup)
    ctx.set_source_rgb(0, 0, 0); ctx.paint()
    for e in escenas:
        if e.t0 <= t < e.t1:
            e.cuadro(t - e.t0, ctx); break
    viñeta(ctx)
    buf = np.ndarray((H, W, 4), np.uint8, sup.get_data())
    return buf[:, :, [2, 1, 0]].copy()


def render_tramo(escenas, desde, hasta, ruta):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", ruta]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(round(desde * FPS), round(hasta * FPS)):
        p.stdin.write(cuadro_video(escenas, i / FPS).tobytes())
    p.stdin.close(); p.wait()
