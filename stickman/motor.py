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
    "barbilla":  dict(torso=178, cabeza=-10, bi=-14, ai=-6, bd=-8, ad=-158, mi=-8, pi=-4, md=8, pd=4),
    "jarras":    dict(torso=180, cabeza=4, bi=-62, ai=48, bd=62, ad=-48, mi=-10, pi=-6, md=10, pd=6),
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


# ---------------------------------------------------------------- personaje con sudadera
SOMBRA_FRIA = (0.80, 0.85, 0.92)   # sombreado gris azulado de la cabeza y la ropa
PELO_CAFE = (0.47, 0.29, 0.16)
SUDADERA_BLANCA = (0.93, 0.94, 0.95)


def _rel(origen, ang, x, y):
    """Punto (x, y) en el marco local de una pieza girada 'ang' (0 = abajo, 180 = arriba).
    En el marco local, -y apunta hacia 'ang + 180°'... es decir, 'arriba' de la pieza."""
    a = math.pi - math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    return origen[0] + x * c - y * s, origen[1] + x * s + y * c


class Personaje(Monigote):
    """Monigote estilo «cabezón con sudadera»: cabeza blanca grande con sombreado frío, pelo café en
    picos, cejas gruesas expresivas, sudadera con capucha, cordones y bolsillo, extremidades de palito,
    manos y pies negros. Usa las mismas claves y poses que Monigote.

    Caras: feliz, picaro (sonrisa de lado, una ceja alzada), sorpresa, triste, serio, pensar, enojado.
    """
    def __init__(self, claves, escala=1.0, pelo=PELO_CAFE, sudadera=SUDADERA_BLANCA, grosor=11, semilla=1):
        # con sudadera, «pensar» lleva la mano a la barbilla por delante del cuerpo
        claves = [dict(c, pose="barbilla") if c.get("pose") == "pensar" else c for c in claves]
        super().__init__(claves, escala=escala, grosor=grosor, semilla=semilla)
        self.pelo, self.sudadera = pelo, sudadera

    def dibujar(self, ctx, t):
        pose, x, y, clave, moviendo = self.estado(t)
        s = self.s
        pose = dict(pose)
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

        T, R = 165 * s, 92 * s                       # largo del torso y radio de la cabeza
        L = dict(brazo=78 * s, ante=72 * s, muslo=92 * s, pierna=88 * s)

        def cadena(o, a1, l1, a2, l2):
            p1 = (o[0] + vec(a1, l1)[0], o[1] + vec(a1, l1)[1])
            return p1, (p1[0] + vec(a2, l2)[0], p1[1] + vec(a2, l2)[1])
        rodi, pie_i = cadena((0, 0), pose["mi"], L["muslo"], pose["pi"], L["pierna"])
        rodd, pie_d = cadena((0, 0), pose["md"], L["muslo"], pose["pd"], L["pierna"])
        baja = max(pie_i[1], pie_d[1]) + 12 * s
        cad = (x, y + dy + resp - baja)
        tor = pose["torso"]
        cad_i, cad_d = _rel(cad, tor, -22 * s, 0), _rel(cad, tor, 22 * s, 0)
        rodi = (cad_i[0] + rodi[0], cad_i[1] + rodi[1]); pie_i = (cad_i[0] + pie_i[0], cad_i[1] + pie_i[1])
        rodd = (cad_d[0] + rodd[0], cad_d[1] + rodd[1]); pie_d = (cad_d[0] + pie_d[0], cad_d[1] + pie_d[1])
        hom_i, hom_d = _rel(cad, tor, -60 * s, -T + 45 * s), _rel(cad, tor, 60 * s, -T + 45 * s)
        codi, mani = cadena(hom_i, pose["bi"], L["brazo"], pose["ai"], L["ante"])
        codd, mand = cadena(hom_d, pose["bd"], L["brazo"], pose["ad"], L["ante"])
        ang_cab = tor + pose["cabeza"]
        cab = _rel(_rel(cad, tor, 0, -T + 8 * s), ang_cab, 0, -R * 0.82)

        # sombra en el suelo
        ctx.save(); ctx.set_source_rgba(0, 0, 0, 0.13)
        ctx.translate(x, y); ctx.scale(1, 0.16); ctx.arc(0, 0, 95 * s * (1 - min(-dy, 80) / 200), 0, 2 * math.pi)
        ctx.fill(); ctx.restore()

        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        j = lambda p, n: (p[0] + temblor((self.semilla, n), t, 0.8)[0], p[1] + temblor((self.semilla, n), t, 0.8)[1])
        palo = lambda pts, n: (ctx.move_to(*j(pts[0], n)), ctx.line_to(*j(pts[1], n + 1)),
                               ctx.line_to(*j(pts[2], n + 2)), ctx.stroke())
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(self.g * s)
        # piernas y pies (los pies apuntan hacia afuera, o hacia donde mira)
        for n, (c0, ro, pie, lado) in enumerate([(cad_i, rodi, pie_i, -1), (cad_d, rodd, pie_d, 1)]):
            palo((c0, ro, pie), 10 + n * 3)
            hacia = clave["mira"] or lado
            ctx.save(); ctx.translate(pie[0] + hacia * 14 * s, pie[1] + 2 * s); ctx.scale(1, 0.5)
            ctx.arc(0, 0, 25 * s, 0, 2 * math.pi); ctx.restore(); ctx.fill()
        # brazos y manos; si la mano cruza el cuerpo (p. ej. «pensar»), el brazo va encima de la sudadera
        brazos = [(hom_i, codi, mani), (hom_d, codd, mand)]
        a_t = math.pi - math.radians(tor)
        def cruza(ma):
            dx, dy2 = ma[0] - cad[0], ma[1] - cad[1]
            lx = dx * math.cos(a_t) + dy2 * math.sin(a_t)
            ly = -dx * math.sin(a_t) + dy2 * math.cos(a_t)
            return abs(lx) < 58 * s and -T - 20 * s < ly < 20 * s
        def mano(co, ma):
            ang = math.degrees(math.atan2(ma[0] - co[0], ma[1] - co[1]))
            ctx.save(); ctx.translate(*_rel(ma, ang, 0, 6 * s)); ctx.rotate(math.pi - math.radians(ang))
            ctx.scale(0.8, 1); ctx.arc(0, 0, 15 * s, 0, 2 * math.pi); ctx.restore(); ctx.fill()
        for n, (h, co, ma) in enumerate(brazos):
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(self.g * s); palo((h, co, ma), 20 + n * 3); mano(co, ma)

        self._sudadera(ctx, cad, tor, T, s)
        for n, (h, co, ma) in enumerate(brazos):
            if cruza(ma):
                ctx.set_source_rgb(*TINTA); ctx.set_line_width(self.g * s)
                palo((h, co, ma), 20 + n * 3); mano(co, ma)
        self._cabeza(ctx, cab, ang_cab, R, clave, t)

    # -- ropa ----------------------------------------------------------------
    def _sudadera(self, ctx, cad, tor, T, s):
        ctx.save(); ctx.translate(*cad); ctx.rotate(math.pi - math.radians(tor))
        col, sombra = self.sudadera, tuple(v * 0.86 for v in self.sudadera)
        lw = 7 * s
        def tinta(w=lw): ctx.set_source_rgb(*TINTA); ctx.set_line_width(w); ctx.stroke()
        # cuerpo de la sudadera
        def cuerpo():
            ctx.move_to(-64 * s, -T + 24 * s)
            ctx.curve_to(-84 * s, -T + 70 * s, -74 * s, -40 * s, -68 * s, 14 * s)
            ctx.line_to(68 * s, 14 * s)
            ctx.curve_to(74 * s, -40 * s, 84 * s, -T + 70 * s, 64 * s, -T + 24 * s); ctx.close_path()
        cuerpo(); ctx.set_source_rgb(*col); ctx.fill_preserve(); ctx.save(); ctx.clip()
        ctx.set_source_rgb(*sombra)                      # sombreado lateral, como en el dibujo
        ctx.rectangle(-90 * s, -T, 30 * s, T + 30 * s); ctx.fill()
        ctx.move_to(-60 * s, -T + 60 * s); ctx.curve_to(-20 * s, -T + 48 * s, 20 * s, -T + 48 * s, 60 * s, -T + 60 * s)
        ctx.line_to(60 * s, -T + 30 * s); ctx.line_to(-60 * s, -T + 30 * s); ctx.close_path(); ctx.fill()
        ctx.restore(); cuerpo(); tinta()
        # resorte de abajo
        ctx.rectangle(-69 * s, 2 * s, 138 * s, 18 * s); ctx.set_source_rgb(*col); ctx.fill_preserve(); tinta(6 * s)
        # bolsillo canguro
        ctx.move_to(-38 * s, -6 * s); ctx.line_to(-30 * s, -50 * s); ctx.line_to(30 * s, -50 * s)
        ctx.line_to(38 * s, -6 * s); tinta(5.5 * s)
        ctx.set_source_rgba(*SOMBRA_FRIA, 0.9); ctx.rectangle(-30 * s, -48 * s, 60 * s, 8 * s); ctx.fill()
        # capucha (rodea el cuello)
        ctx.save(); ctx.translate(0, -T + 22 * s); ctx.scale(1, 0.48)
        ctx.arc(0, 0, 76 * s, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgb(*col); ctx.fill_preserve(); tinta()
        ctx.save(); ctx.translate(0, -T + 16 * s); ctx.scale(1, 0.42); ctx.arc(0, 0, 42 * s, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgb(*SOMBRA_FRIA); ctx.fill_preserve(); tinta(5 * s)
        # cordones con puntas
        for lado in (-1, 1):
            ctx.move_to(lado * 16 * s, -T + 32 * s)
            ctx.curve_to(lado * 19 * s, -T + 55 * s, lado * 14 * s, -T + 75 * s, lado * 17 * s, -T + 92 * s)
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(9 * s); ctx.stroke_preserve()
            ctx.set_source_rgb(*col); ctx.set_line_width(4.5 * s); ctx.stroke()
            ctx.save(); ctx.translate(lado * 17 * s, -T + 98 * s); ctx.scale(0.75, 1)
            ctx.arc(0, 0, 7 * s, 0, 2 * math.pi); ctx.restore()
            ctx.set_source_rgb(*col); ctx.fill_preserve(); tinta(3.5 * s)
        ctx.restore()

    # -- cabeza ----------------------------------------------------------------
    def _cabeza(self, ctx, c, ang, r, clave, t):
        ctx.save(); ctx.translate(*c); ctx.rotate(math.pi - math.radians(ang))
        ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.save(); ctx.clip()
        ctx.set_source_rgb(*SOMBRA_FRIA); ctx.paint()                  # sombra fría abajo a la izquierda
        ctx.set_source_rgb(1, 1, 1); ctx.arc(r * 0.13, -r * 0.12, r * 0.96, 0, 2 * math.pi); ctx.fill()
        ctx.restore()
        ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.set_source_rgb(*TINTA); ctx.set_line_width(8 * self.s); ctx.stroke()
        self._pelo(ctx, r)
        self._cara2(ctx, r, clave["cara"], clave["mira"] * r * 0.16, t)
        ctx.restore()

    def _pelo(self, ctx, r):
        # contorno en sentido horario: mechones colgando a la izquierda, copete que barre a la derecha
        # y fleco con dos puntas sobre la frente. Las puntas quedan filosas y los tramos se curvan hacia afuera.
        pts = [(-0.97, -0.02), (-0.86, -0.30), (-1.10, -0.44), (-0.90, -0.58), (-0.98, -0.90),
               (-0.62, -0.92), (-0.30, -1.14), (0.20, -1.12), (0.60, -1.06), (1.20, -0.96),
               (0.90, -0.76), (1.10, -0.56), (0.84, -0.52), (0.58, -0.72), (0.30, -0.54),
               (0.08, -0.74), (-0.26, -0.52), (-0.44, -0.70), (-0.72, -0.34)]
        cx0, cy0 = 0.0, -0.35
        ctx.move_to(pts[0][0] * r, pts[0][1] * r)
        for i in range(len(pts)):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
            mx, my = (x0 + x1) / 2 - cx0, (y0 + y1) / 2 - cy0
            d = math.hypot(mx, my) or 1; seg = math.hypot(x1 - x0, y1 - y0)
            fuera = 1 if i < 12 else -0.6                      # el fleco se curva hacia adentro
            ox, oy = mx / d * seg * 0.12 * fuera, my / d * seg * 0.12 * fuera
            ctx.curve_to((x0 + (x1 - x0) / 3 + ox) * r, (y0 + (y1 - y0) / 3 + oy) * r,
                         (x0 + 2 * (x1 - x0) / 3 + ox) * r, (y0 + 2 * (y1 - y0) / 3 + oy) * r, x1 * r, y1 * r)
        ctx.close_path()
        ctx.set_source_rgb(*self.pelo); ctx.fill_preserve(); ctx.save(); ctx.clip()
        ctx.set_source_rgba(*[v * 0.55 for v in self.pelo], 0.85); ctx.set_line_width(3.2 * self.s)
        for (a, b, c2) in [((-0.7, -0.75), (-0.4, -0.95), (0.0, -0.98)), ((-0.2, -0.8), (0.2, -0.95), (0.7, -0.92)),
                           ((-0.85, -0.45), (-0.8, -0.6), (-0.65, -0.75)), ((0.3, -0.72), (0.6, -0.8), (0.95, -0.8))]:
            ctx.move_to(a[0] * r, a[1] * r); ctx.curve_to(b[0] * r, b[1] * r, b[0] * r, b[1] * r, c2[0] * r, c2[1] * r)
            ctx.stroke()
        ctx.restore()
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(6.5 * self.s)
        # repetir el trazo para el contorno
        ctx.move_to(pts[0][0] * r, pts[0][1] * r)
        for i in range(len(pts)):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
            mx, my = (x0 + x1) / 2 - cx0, (y0 + y1) / 2 - cy0
            d = math.hypot(mx, my) or 1; seg = math.hypot(x1 - x0, y1 - y0)
            fuera = 1 if i < 12 else -0.6
            ox, oy = mx / d * seg * 0.12 * fuera, my / d * seg * 0.12 * fuera
            ctx.curve_to((x0 + (x1 - x0) / 3 + ox) * r, (y0 + (y1 - y0) / 3 + oy) * r,
                         (x0 + 2 * (x1 - x0) / 3 + ox) * r, (y0 + 2 * (y1 - y0) / 3 + oy) * r, x1 * r, y1 * r)
        ctx.close_path(); ctx.stroke()

    def _cara2(self, ctx, r, cara, ox, t):
        ctx.set_source_rgb(*TINTA)
        parpadeo = (t + self.semilla * 0.7) % 3.4 < 0.12
        # cejas: (alto de la punta interior, alto de la punta exterior) por lado; negativo = más arriba
        cejas = dict(feliz=((-0.32, -0.36), (-0.32, -0.36)), picaro=((-0.27, -0.31), (-0.36, -0.47)),
                     sorpresa=((-0.50, -0.50), (-0.50, -0.50)), triste=((-0.44, -0.30), (-0.44, -0.30)),
                     serio=((-0.33, -0.36), (-0.33, -0.36)), pensar=((-0.32, -0.34), (-0.46, -0.50)),
                     enojado=((-0.24, -0.40), (-0.24, -0.40))).get(cara, ((-0.36, -0.40), (-0.36, -0.40)))
        for n, lado in enumerate((-1, 1)):
            ex, ey = ox + lado * r * 0.30, -r * 0.04
            yi, ye = cejas[n]
            # ceja gruesa con arco
            xi, xe = ex - lado * r * 0.13, ex + lado * r * 0.20
            ctx.set_line_width(r * 0.095); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(xi, yi * r)
            ctx.curve_to(ex - lado * r * 0.02, (yi + ye) / 2 * r - r * 0.09, ex + lado * r * 0.1, ye * r - r * 0.04, xe, ye * r + r * 0.03)
            ctx.stroke()
            ex2 = ex + ox * 0.15
            if parpadeo and cara != "sorpresa":
                ctx.set_line_width(r * 0.05); ctx.move_to(ex2 - r * 0.08, ey); ctx.line_to(ex2 + r * 0.08, ey); ctx.stroke()
                continue
            alto = 0.16 if cara == "sorpresa" else 0.125
            ctx.save()
            if cara in ("picaro", "serio", "enojado"):            # párpado a media asta: corta la parte de arriba
                ctx.rectangle(ex2 - r * 0.2, ey - r * 0.045, r * 0.4, r * 0.4); ctx.clip()
            ctx.translate(ex2, ey); ctx.scale(0.66, 1); ctx.arc(0, 0, r * alto, 0, 2 * math.pi); ctx.restore(); ctx.fill()
            if cara in ("picaro", "serio", "enojado"):
                ctx.set_line_width(r * 0.045); ctx.set_line_cap(cairo.LINE_CAP_BUTT)
                ctx.move_to(ex2 - r * 0.095, ey - r * 0.045); ctx.line_to(ex2 + r * 0.095, ey - r * 0.045); ctx.stroke()
                ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            else:
                ctx.set_source_rgb(1, 1, 1); ctx.arc(ex2 + r * 0.025, ey - r * 0.055, r * 0.025, 0, 2 * math.pi)
                ctx.fill(); ctx.set_source_rgb(*TINTA)
        mx, my = ox, r * 0.36
        ctx.set_line_width(r * 0.055)
        if cara == "feliz":
            ctx.move_to(mx - r * 0.32, my - r * 0.06)
            ctx.curve_to(mx - r * 0.15, my + r * 0.16, mx + r * 0.15, my + r * 0.16, mx + r * 0.32, my - r * 0.06)
            ctx.stroke()
        elif cara == "picaro":                                    # sonrisa de lado
            ctx.move_to(mx - r * 0.34, my - r * 0.04)
            ctx.curve_to(mx - r * 0.18, my + r * 0.12, mx + r * 0.2, my + r * 0.08, mx + r * 0.40, my - r * 0.14)
            ctx.stroke()
            ctx.move_to(mx - r * 0.38, my - r * 0.09); ctx.line_to(mx - r * 0.33, my - r * 0.02); ctx.stroke()
        elif cara == "sorpresa":
            ctx.save(); ctx.translate(mx, my + r * 0.04); ctx.scale(0.8, 1); ctx.arc(0, 0, r * 0.12, 0, 2 * math.pi)
            ctx.restore(); ctx.fill()
        elif cara == "triste":
            ctx.move_to(mx - r * 0.25, my + r * 0.08)
            ctx.curve_to(mx - r * 0.1, my - r * 0.06, mx + r * 0.1, my - r * 0.06, mx + r * 0.25, my + r * 0.08)
            ctx.stroke()
        elif cara == "pensar":
            ctx.move_to(mx - r * 0.2, my); ctx.curve_to(mx - r * 0.05, my - r * 0.08, mx + r * 0.05, my + r * 0.08,
                                                        mx + r * 0.22, my - r * 0.02); ctx.stroke()
        elif cara == "enojado":
            ctx.move_to(mx - r * 0.22, my + r * 0.05); ctx.curve_to(mx - r * 0.1, my - r * 0.03, mx + r * 0.1, my - r * 0.03,
                                                                    mx + r * 0.22, my + r * 0.05); ctx.stroke()
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
