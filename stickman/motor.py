"""Motor de shorts estilo stickman (monigote) — Python + pycairo + ffmpeg.

Dibuja todo con código: monigotes con poses, utilería simple, subtítulos grandes
palabra por palabra y efectos de sonido sintetizados. Salida: MP4 vertical 1080x1920.

Uso típico (ver ejemplos/pulpo.py):
    from motor import Short, Monigote, Subtitulos
    short = Short(duracion=26)
    ...
    short.render("salida.mp4")
"""
import math, subprocess, random
import numpy as np
import cairo

W, H, FPS = 1080, 1920, 30
TINTA = (0.08, 0.08, 0.1)
PAPEL = (0.98, 0.97, 0.94)

# ---------------------------------------------------------------- utilidades
def lerp(a, b, k): return a + (b - a) * k
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def suave(k):  # ease in-out
    k = clamp(k); return k * k * (3 - 2 * k)
def rebote(k):  # ease-out-back: aparece con un pequeño "pop"
    k = clamp(k); c = 1.9
    return 1 + (c + 1) * (k - 1) ** 3 + c * (k - 1) ** 2

def temblor(seed, t, amp=2.0):
    """Efecto 'dibujado a mano': cambia ~8 veces por segundo."""
    r = random.Random(hash((seed, int(t * 8))))
    return r.uniform(-amp, amp), r.uniform(-amp, amp)

# ---------------------------------------------------------------- poses
# Ángulos absolutos en grados: 0 = hacia abajo, 90 = hacia la derecha, 180 = arriba, -90 = izquierda.
# 'i' = extremidad que se ve a la izquierda de la pantalla, 'd' = a la derecha.
POSES = {
    "parado":    dict(torso=180, cabeza=0, bi=-14, ai=-6, bd=14, ad=6, mi=-8, pi=-4, md=8, pd=4),
    "saludo":    dict(torso=180, cabeza=6, bi=-14, ai=-6, bd=125, ad=165, mi=-8, pi=-4, md=8, pd=4),
    "señalar_d": dict(torso=184, cabeza=8, bi=-14, ai=-6, bd=95, ad=95, mi=-8, pi=-4, md=10, pd=6),
    "señalar_i": dict(torso=176, cabeza=-8, bi=-95, ai=-95, bd=14, ad=6, mi=-10, pi=-6, md=8, pd=4),
    "sorpresa":  dict(torso=180, cabeza=0, bi=-135, ai=-165, bd=135, ad=165, mi=-14, pi=-10, md=14, pd=10),
    "pensar":    dict(torso=178, cabeza=-10, bi=-14, ai=-6, bd=30, ad=-150, mi=-8, pi=-4, md=8, pd=4),
    "encoger":   dict(torso=180, cabeza=10, bi=-60, ai=-140, bd=60, ad=140, mi=-8, pi=-4, md=8, pd=4),
    "festejar":  dict(torso=180, cabeza=0, bi=-150, ai=-175, bd=150, ad=175, mi=-25, pi=-5, md=25, pd=5),
    "triste":    dict(torso=172, cabeza=-25, bi=-6, ai=-2, bd=6, ad=2, mi=-6, pi=-3, md=6, pd=3),
}
ARTIC = list(POSES["parado"].keys())

def mezclar(p1, p2, k):
    return {j: lerp(p1[j], p2[j], k) for j in ARTIC}

def vec(ang, largo):
    a = math.radians(ang); return math.sin(a) * largo, math.cos(a) * largo


class Monigote:
    """Un monigote con fotogramas clave.

    claves: lista de dicts con 't' (segundos) y cualquiera de:
        pose, x, y, cara ('feliz','sorpresa','triste','serio','pensar'),
        caminar (True/False), saltar (True/False), mira (-1 izq / 1 der)
    """
    def __init__(self, claves, escala=1.0, grosor=14, color=TINTA, semilla=1):
        self.claves = sorted(claves, key=lambda c: c["t"])
        self.s, self.g, self.color, self.semilla = escala, grosor, color, semilla
        # rellena los valores que falten con los del fotograma anterior
        prev = dict(pose="parado", x=W / 2, y=1350, cara="feliz", caminar=False, saltar=False, mira=0)
        for c in self.claves:
            for k, v in prev.items(): c.setdefault(k, v)
            prev = dict(c); prev.pop("t"); prev["caminar"] = False; prev["saltar"] = False  # no se heredan

    def estado(self, t, dur_trans=0.35):
        cs = self.claves
        if t <= cs[0]["t"]: a = b = cs[0]; k = 0
        else:
            a = cs[0]; b = cs[0]
            for c in cs:
                if c["t"] <= t: a = c
            idx = cs.index(a)
            b = cs[idx + 1] if idx + 1 < len(cs) else a
            # la posición se interpola durante todo el tramo; la pose cambia rápido al inicio
            span = max(b["t"] - a["t"], 1e-6)
            k = suave((t - a["t"]) / span) if b is not a else 0
        # pose: transición corta desde la clave anterior
        idx = cs.index(a)
        anterior = cs[idx - 1] if idx > 0 else a
        kp = suave((t - a["t"]) / dur_trans)
        pose = mezclar(POSES[anterior["pose"]], POSES[a["pose"]], kp)
        x, y = lerp(a["x"], b["x"], k), lerp(a["y"], b["y"], k)
        moviendo = a["caminar"] and abs(b["x"] - a["x"]) > 1 and t < b["t"]
        return pose, x, y, a, moviendo

    def dibujar(self, ctx, t):
        pose, x, y, clave, moviendo = self.estado(t)
        s = self.s
        pose = dict(pose)
        # respiración / vida
        resp = math.sin(t * 2.2 + self.semilla) * 1.5
        pose["torso"] += math.sin(t * 1.3 + self.semilla) * 1.2
        if clave["pose"] == "saludo":
            pose["ad"] += math.sin(t * 12) * 22
        dy = 0
        if moviendo:
            f = t * 9
            pose["mi"] = math.sin(f) * 28; pose["pi"] = pose["mi"] + max(0, math.sin(f - 1.2)) * -30
            pose["md"] = -math.sin(f) * 28; pose["pd"] = pose["md"] + max(0, -math.sin(f - 1.2)) * -30
            pose["bi"] = -10 - math.sin(f) * 22; pose["ai"] = pose["bi"] - 12
            pose["bd"] = 10 + math.sin(f) * 22; pose["ad"] = pose["bd"] + 12
            dy = -abs(math.sin(f)) * 10 * s
        if clave["saltar"]:
            dy = -abs(math.sin(t * 7)) * 70 * s

        L = dict(torso=150 * s, cuello=10 * s, brazo=82 * s, ante=78 * s, muslo=92 * s, pierna=88 * s, cabeza=46 * s)
        cad = (x, y + dy + resp)
        # el pie más bajo toca el suelo: calculamos piernas primero
        def cadena(origen, a1, l1, a2, l2):
            p1 = (origen[0] + vec(a1, l1)[0], origen[1] + vec(a1, l1)[1])
            p2 = (p1[0] + vec(a2, l2)[0], p1[1] + vec(a2, l2)[1])
            return p1, p2
        rodi, pie_i = cadena((0, 0), pose["mi"], L["muslo"], pose["pi"], L["pierna"])
        rodd, pie_d = cadena((0, 0), pose["md"], L["muslo"], pose["pd"], L["pierna"])
        baja = max(pie_i[1], pie_d[1])
        cad = (cad[0], cad[1] - baja)  # y = línea del suelo
        hombro = (cad[0] + vec(pose["torso"], L["torso"])[0], cad[1] + vec(pose["torso"], L["torso"])[1])
        cuello = (hombro[0] + vec(pose["torso"], L["cuello"])[0], hombro[1] + vec(pose["torso"], L["cuello"])[1])
        cab = (cuello[0] + vec(pose["torso"] + pose["cabeza"], L["cabeza"])[0],
               cuello[1] + vec(pose["torso"] + pose["cabeza"], L["cabeza"])[1])
        codi, mani = cadena(hombro, pose["bi"], L["brazo"], pose["ai"], L["ante"])
        codd, mand = cadena(hombro, pose["bd"], L["brazo"], pose["ad"], L["ante"])
        rodi = (cad[0] + rodi[0], cad[1] + rodi[1]); pie_i = (cad[0] + pie_i[0], cad[1] + pie_i[1])
        rodd = (cad[0] + rodd[0], cad[1] + rodd[1]); pie_d = (cad[0] + pie_d[0], cad[1] + pie_d[1])

        # sombra
        ctx.save(); ctx.set_source_rgba(0, 0, 0, 0.12)
        ctx.translate(x, y); ctx.scale(1, 0.18); ctx.arc(0, 0, 80 * s * (1 - min(-dy, 80) / 200), 0, 2 * math.pi)
        ctx.fill(); ctx.restore()

        ctx.set_source_rgb(*self.color); ctx.set_line_width(self.g * s)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        j = lambda p, n: (p[0] + temblor((self.semilla, n), t, 1.2)[0], p[1] + temblor((self.semilla, n), t, 1.2)[1])
        for i, pts in enumerate([(cad, hombro, cuello), (cad, rodi, pie_i), (cad, rodd, pie_d),
                                 (hombro, codi, mani), (hombro, codd, mand)]):
            ctx.move_to(*j(pts[0], i * 3))
            ctx.line_to(*j(pts[1], i * 3 + 1)); ctx.line_to(*j(pts[2], i * 3 + 2)); ctx.stroke()
        # cabeza
        ctx.set_source_rgb(*PAPEL); ctx.arc(cab[0], cab[1], L["cabeza"], 0, 2 * math.pi); ctx.fill_preserve()
        ctx.set_source_rgb(*self.color); ctx.stroke()
        self._cara(ctx, cab, L["cabeza"], clave["cara"], pose["cabeza"] / 40 + clave["mira"] * 0.35, t)

    def _cara(self, ctx, c, r, cara, giro, t):
        ox = giro * r * 0.6
        parpadeo = (t + self.semilla * 0.7) % 3.4 < 0.12
        ctx.set_source_rgb(*self.color)
        for lado in (-1, 1):
            ex, ey = c[0] + ox + lado * r * 0.36, c[1] - r * 0.12
            if cara == "sorpresa":
                ctx.set_line_width(r * 0.1); ctx.arc(ex, ey, r * 0.16, 0, 2 * math.pi); ctx.stroke()
                ctx.arc(ex, ey, r * 0.06, 0, 2 * math.pi); ctx.fill()
                ctx.move_to(ex - r * 0.18, ey - r * 0.38); ctx.line_to(ex + r * 0.14, ey - r * 0.44 + lado * 0.0); ctx.stroke()
            elif parpadeo:
                ctx.set_line_width(r * 0.1); ctx.move_to(ex - r * 0.12, ey); ctx.line_to(ex + r * 0.12, ey); ctx.stroke()
            else:
                ctx.arc(ex, ey, r * 0.11, 0, 2 * math.pi); ctx.fill()
            if cara == "triste":
                ctx.set_line_width(r * 0.09)
                ctx.move_to(ex - lado * r * 0.2, ey - r * 0.25); ctx.line_to(ex + lado * r * 0.15, ey - r * 0.38); ctx.stroke()
        mx, my = c[0] + ox, c[1] + r * 0.38
        ctx.set_line_width(r * 0.11)
        if cara == "feliz":
            ctx.arc(mx, my - r * 0.18, r * 0.3, math.radians(25), math.radians(155)); ctx.stroke()
        elif cara == "sorpresa":
            ctx.save(); ctx.translate(mx, my); ctx.scale(1, 1.3); ctx.arc(0, 0, r * 0.15, 0, 2 * math.pi); ctx.restore(); ctx.fill()
        elif cara == "triste":
            ctx.arc(mx, my + r * 0.15, r * 0.25, math.radians(205), math.radians(335)); ctx.stroke()
        elif cara == "pensar":
            ctx.move_to(mx - r * 0.2, my); ctx.curve_to(mx - r * 0.05, my - r * 0.1, mx + r * 0.05, my + r * 0.1, mx + r * 0.22, my - r * 0.02); ctx.stroke()
        else:
            ctx.move_to(mx - r * 0.2, my); ctx.line_to(mx + r * 0.2, my); ctx.stroke()


# ---------------------------------------------------------------- utilería
class Elemento:
    """Cualquier dibujo que aparece (pop) y desaparece en un tiempo dado.
    dibujo(ctx, t, k): función que dibuja centrada en (0,0); k = progreso de aparición 0..1."""
    def __init__(self, dibujo, t0, t1, x, y, escala=1.0, mover=None, entrada=0.35, salida=0.25):
        self.f, self.t0, self.t1, self.x, self.y, self.s = dibujo, t0, t1, x, y, escala
        self.mover, self.entrada, self.salida = mover, entrada, salida

    def dibujar(self, ctx, t):
        if not (self.t0 <= t <= self.t1): return
        k_in = rebote((t - self.t0) / self.entrada)
        k_out = max(0.01, suave((self.t1 - t) / self.salida))
        k = min(k_in, 1) * k_out if k_in < 1 else k_out
        esc = self.s * max(0.01, min(k_in, 1.15)) * (0.6 + 0.4 * k_out)
        x, y = (self.mover(t) if self.mover else (self.x, self.y))
        ctx.save(); ctx.translate(x, y); ctx.scale(esc, esc)
        self.f(ctx, t, clamp(k)); ctx.restore()


def contorno(ctx, relleno, grosor=10):
    ctx.set_source_rgb(*relleno); ctx.fill_preserve()
    ctx.set_source_rgb(*TINTA); ctx.set_line_width(grosor); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()


def corazon(color=(0.92, 0.2, 0.25), latido=True):
    def f(ctx, t, k):
        p = 1 + (0.12 * max(0, math.sin(t * 8)) ** 4 if latido else 0)
        ctx.scale(p, p)
        ctx.move_to(0, 60)
        ctx.curve_to(-110, -10, -60, -95, 0, -40)
        ctx.curve_to(60, -95, 110, -10, 0, 60); ctx.close_path()
        contorno(ctx, color)
        ctx.set_source_rgba(1, 1, 1, 0.55); ctx.arc(-38, -30, 12, 0, 2 * math.pi); ctx.fill()
    return f


def texto(txt, tam=90, color=TINTA, borde=None, fuente="Inter"):
    def f(ctx, t, k):
        ctx.select_font_face(fuente, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(tam)
        e = ctx.text_extents(txt)
        ctx.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing)
        ctx.text_path(txt)
        if borde:
            ctx.set_source_rgb(*borde); ctx.set_line_width(tam * 0.18); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
        ctx.set_source_rgb(*color); ctx.fill()
    return f


def burbuja_pensamiento(interior=None):
    def f(ctx, t, k):
        for (bx, by, br) in [(-150, 170, 14), (-115, 130, 22)]:
            ctx.arc(bx, by, br, 0, 2 * math.pi); contorno(ctx, (1, 1, 1), 7)
        ctx.save(); ctx.scale(1.35, 1); ctx.arc(0, 0, 120, 0, 2 * math.pi); ctx.restore()
        contorno(ctx, (1, 1, 1), 9)
        if interior: interior(ctx, t, k)
    return f


def gota(color=(0.2, 0.45, 0.95)):
    def f(ctx, t, k):
        ctx.move_to(0, -110); ctx.curve_to(40, -40, 80, 0, 80, 40)
        ctx.curve_to(80, 95, -80, 95, -80, 40); ctx.curve_to(-80, 0, -40, -40, 0, -110); ctx.close_path()
        contorno(ctx, color)
        ctx.set_source_rgba(1, 1, 1, 0.6); ctx.arc(-35, 35, 14, 0, 2 * math.pi); ctx.fill()
    return f


def pulpo(color=(0.95, 0.45, 0.55), nadar=False, corazones=0, sangre_azul=False):
    """corazones: 0 = ninguno visible, 2 = los de las branquias, 3 = todos."""
    def f(ctx, t, k):
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ondula = 4 if nadar else 1.6
        # tentáculos
        for i in range(8):
            base = -105 + i * 30
            ctx.move_to(base * 0.8, 40)
            pts = []
            for s in range(1, 9):
                yy = 40 + s * 24 * (1.25 if nadar else 1)
                xx = base * (0.8 + s * (0.04 if nadar else 0.12)) + math.sin(t * ondula + i + s * 0.7) * (6 + s * 3)
                pts.append((xx, yy))
            for p in pts: ctx.line_to(*p)
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(30); ctx.stroke_preserve()
            ctx.set_source_rgb(*color); ctx.set_line_width(19); ctx.stroke()
        # cabeza
        ctx.save(); ctx.scale(1, 1.15); ctx.arc(0, -60, 130, 0, 2 * math.pi); ctx.restore()
        contorno(ctx, color, 10)
        # manchas
        ctx.set_source_rgba(0.8, 0.25, 0.4, 0.5)
        for (mx, my, mr) in [(-55, -150, 16), (45, -170, 11), (70, -100, 13), (-80, -80, 9)]:
            ctx.arc(mx, my, mr, 0, 2 * math.pi); ctx.fill()
        # ojos
        for lado in (-1, 1):
            ctx.arc(lado * 50, 0, 30, 0, 2 * math.pi); contorno(ctx, (1, 1, 1), 7)
            ctx.set_source_rgb(*TINTA); ctx.arc(lado * 50 + 6, 4, 13, 0, 2 * math.pi); ctx.fill()
        ctx.set_line_width(8); ctx.arc(0, 45, 22, math.radians(20), math.radians(160)); ctx.stroke()
        # corazones internos
        if corazones:
            col = (0.2, 0.45, 0.95) if sangre_azul else (0.92, 0.2, 0.25)
            pos = [(-95, -95, 0.32), (95, -95, 0.32)] + ([(0, -125, 0.5)] if corazones >= 3 else [])
            for (hx, hy, hs) in pos:
                ctx.save(); ctx.translate(hx, hy); ctx.scale(hs, hs); corazon(col)(ctx, t, k); ctx.restore()
    return f


def burbujas_agua(semilla=3, n=14):
    rnd = random.Random(semilla)
    datos = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(8, 26), rnd.uniform(60, 160)) for _ in range(n)]
    def f(ctx, t, k):
        ctx.set_line_width(4)
        for (bx, by, br, vel) in datos:
            y = (by - t * vel) % (H + 100) - 50
            ctx.arc(bx + math.sin(t * 2 + by) * 12, y, br, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 0.35); ctx.fill_preserve(); ctx.set_source_rgba(1, 1, 1, 0.8); ctx.stroke()
    return f


# ---------------------------------------------------------------- fondo y subtítulos
class Fondo:
    """Cambia de color por tramos: [(t, (r,g,b)), ...]; 'suelo' dibuja la línea del piso."""
    def __init__(self, colores, suelo=1350):
        self.colores, self.suelo = colores, suelo

    def dibujar(self, ctx, t):
        c = self.colores[0][1]
        for i, (ti, col) in enumerate(self.colores):
            if t >= ti:
                prev = self.colores[i - 1][1] if i else col
                c = tuple(lerp(p, q, suave((t - ti) / 0.5)) for p, q in zip(prev, col))
        g = cairo.LinearGradient(0, 0, 0, H)
        g.add_color_stop_rgb(0, *[min(1, v + 0.06) for v in c]); g.add_color_stop_rgb(1, *[v * 0.9 for v in c])
        ctx.set_source(g); ctx.paint()
        if self.suelo:
            ctx.set_source_rgba(*TINTA, 0.85); ctx.set_line_width(8); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(60, self.suelo)
            for xx in range(60, W - 59, 60):
                ctx.line_to(xx, self.suelo + temblor(("suelo", xx), t, 2.5)[1])
            ctx.stroke()


class Subtitulos:
    """Subtítulos grandes estilo shorts. Las palabras entre *asteriscos* se resaltan en amarillo.
    lineas: [(t0, t1, "texto"), ...] — las palabras se revelan de una en una dentro del tramo."""
    def __init__(self, lineas, y=430, tam=84, ancho=920):
        self.lineas, self.y, self.tam, self.ancho = lineas, y, tam, ancho

    def palabras_tiempos(self):
        out = []
        for (t0, t1, txt) in self.lineas:
            pal = txt.split(); n = len(pal)
            for i, p in enumerate(pal): out.append(t0 + (t1 - t0) * 0.85 * i / max(n, 1))
        return out

    def dibujar(self, ctx, t):
        for (t0, t1, txt) in self.lineas:
            if not (t0 <= t < t1): continue
            pal = txt.split()
            ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(self.tam)
            # partir en renglones
            renglones, actual = [], []
            for i, p in enumerate(pal):
                prueba = " ".join(w.replace("*", "") for _, w in actual + [(i, p)])
                if ctx.text_extents(prueba).x_advance > self.ancho and actual:
                    renglones.append(actual); actual = []
                actual.append((i, p))
            renglones.append(actual)
            n = len(pal); sp = ctx.text_extents(" ").x_advance
            for r, ren in enumerate(renglones):
                ancho = sum(ctx.text_extents(w.replace("*", "")).x_advance for _, w in ren) + sp * (len(ren) - 1)
                x = (W - ancho) / 2; y = self.y + r * self.tam * 1.2
                for i, w in ren:
                    ti = t0 + (t1 - t0) * 0.85 * i / max(n, 1)
                    limpio = w.replace("*", "")
                    adv = ctx.text_extents(limpio).x_advance
                    if t >= ti:
                        k = max(0.01, rebote((t - ti) / 0.18))
                        ctx.save(); ctx.translate(x + adv / 2, y); ctx.scale(k, k)
                        ctx.move_to(-adv / 2, 0); ctx.text_path(limpio)
                        ctx.set_source_rgb(*TINTA); ctx.set_line_width(self.tam * 0.2)
                        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
                        ctx.set_source_rgb(*((1, 0.85, 0.1) if "*" in w else (1, 1, 1))); ctx.fill()
                        ctx.restore()
                    x += adv + sp


# ---------------------------------------------------------------- render
class Short:
    def __init__(self, duracion, capas=None):
        self.dur, self.capas = duracion, capas or []
        self.sacudidas = []  # [(t, fuerza)]
        self.zooms = []      # [(t0, t1, escala, cx, cy)]

    def agregar(self, *capas): self.capas.extend(capas); return self

    def sacudir(self, t, fuerza=18): self.sacudidas.append((t, fuerza))

    def zoom(self, t0, t1, escala, cx=W / 2, cy=H / 2): self.zooms.append((t0, t1, escala, cx, cy))

    def cuadro(self, t):
        sup = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
        ctx = cairo.Context(sup)
        ctx.set_antialias(cairo.ANTIALIAS_BEST)
        dx = dy = 0
        for (ts, f) in self.sacudidas:
            if 0 <= t - ts < 0.35:
                d = (1 - (t - ts) / 0.35) * f
                dx += math.sin(t * 90) * d; dy += math.cos(t * 77) * d
        esc, cx, cy = 1.0, W / 2, H / 2
        for (t0, t1, e, zx, zy) in self.zooms:
            if t0 <= t <= t1:
                k = suave(min((t - t0) / 0.4, (t1 - t) / 0.4, 1)); esc = lerp(1, e, k); cx, cy = zx, zy
        ctx.translate(dx, dy)
        ctx.translate(cx, cy); ctx.scale(esc, esc); ctx.translate(-cx, -cy)
        subs = [c for c in self.capas if isinstance(c, Subtitulos)]
        for c in self.capas:
            if not isinstance(c, Subtitulos): c.dibujar(ctx, t)
        ctx.identity_matrix()  # los subtítulos no se mueven con la cámara
        for c in subs: c.dibujar(ctx, t)
        buf = np.ndarray((H, W, 4), np.uint8, sup.get_data())
        return buf[:, :, [2, 1, 0]].copy()  # BGRA -> RGB

    def foto(self, t, ruta):
        from PIL import Image
        Image.fromarray(self.cuadro(t)).save(ruta)

    def render(self, ruta, audio=None, desde=0.0, hasta=None):
        hasta = hasta or self.dur
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
        if audio: cmd += ["-i", audio, "-c:a", "aac", "-b:a", "160k", "-shortest"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", ruta]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        n = int((hasta - desde) * FPS)
        for i in range(n):
            p.stdin.write(self.cuadro(desde + i / FPS).tobytes())
            if i % FPS == 0: print(f"\r  render {i / FPS:5.1f}s / {hasta - desde:.1f}s", end="", flush=True)
        p.stdin.close(); p.wait(); print(f"\r  listo: {ruta}            ")
