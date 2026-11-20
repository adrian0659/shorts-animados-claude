"""Estilo «stickman ilustrado»: cabeza grande blanca con contorno grueso, pelo con forma,
ojos de punto, ropa de color sobre el torso (camisa, uniforme, corbata), piernas y brazos
de palito, guantes blancos y zapatos negros. Escenarios con sombreado suave (taller, auto).

Se usa igual que `Monigote` (mismos fotogramas clave y poses) más la ropa:

    from ilustrado import Persona, Taller, Auto
    mecanico = Persona([dict(t=0, pose="parado", x=330, y=1650, mira=1, cara="serio")],
                       pelo="puntas", ropa=dict(tipo="camisa", color=(0.17, 0.22, 0.35),
                       cuello=(0.8, 0.15, 0.15), manga="corta", gafete="MECÁNICO"))
"""
import math, random
import cairo
from motor import (Monigote, POSES, ARTIC, W, H, TINTA, lerp, clamp, suave, vec)

# ---------------------------------------------------------------- poses nuevas
POSES.update({
    "telefono":   dict(torso=180, cabeza=4, bi=-12, ai=-4, bd=35, ad=168, mi=-7, pi=-3, md=7, pd=3),
    "entregar":   dict(torso=182, cabeza=6, bi=-12, ai=-4, bd=55, ad=88, mi=-7, pi=-3, md=8, pd=4),
    "recibir_i":  dict(torso=178, cabeza=-6, bi=-55, ai=-88, bd=12, ad=4, mi=-8, pi=-4, md=7, pd=3),
    "manos_frente": dict(torso=180, cabeza=4, bi=-35, ai=-75, bd=35, ad=75, mi=-8, pi=-4, md=8, pd=4),
    "brazos_cruzados": dict(torso=180, cabeza=0, bi=-20, ai=60, bd=20, ad=-60, mi=-8, pi=-4, md=8, pd=4),
    "explicar":   dict(torso=181, cabeza=6, bi=-14, ai=-6, bd=50, ad=120, mi=-8, pi=-4, md=8, pd=4),
    "cabeza_mano": dict(torso=178, cabeza=-8, bi=-14, ai=-6, bd=30, ad=-170, mi=-8, pi=-4, md=8, pd=4),
})

PIEL = (1.0, 1.0, 1.0)
SOMBRA_PIEL = (0.84, 0.86, 0.9)
NEGRO = (0.07, 0.07, 0.08)


def oscurecer(c, k=0.75): return tuple(v * k for v in c)


def _contorno(ctx, relleno, grosor, borde=NEGRO):
    ctx.set_source_rgb(*relleno); ctx.fill_preserve()
    ctx.set_source_rgb(*borde); ctx.set_line_width(grosor)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()


def _trazo_doble(ctx, pts, ancho, color, borde=3.0):
    """Polilínea gruesa de color con contorno negro (mangas, pantalones)."""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for w, c in ((ancho + borde * 2, NEGRO), (ancho, color)):
        ctx.move_to(*pts[0])
        for p in pts[1:]: ctx.line_to(*p)
        ctx.set_source_rgb(*c); ctx.set_line_width(w); ctx.stroke()


def _manga(ctx, a, b, w0, w1, color, s):
    """Manga como cuadrilátero de a (hombro) a b (puño), con ancho w0 -> w1."""
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    ctx.move_to(a[0] + nx * w0, a[1] + ny * w0); ctx.line_to(b[0] + nx * w1, b[1] + ny * w1)
    ctx.line_to(b[0] - nx * w1, b[1] - ny * w1); ctx.line_to(a[0] - nx * w0, a[1] - ny * w0)
    ctx.close_path(); _contorno(ctx, color, 2.6 * s)


def _sobre(a, b, k):  # punto a k del camino a->b
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))


# ---------------------------------------------------------------- objetos que se sostienen
def obj_telefono(ctx, s, ang, mira):
    ctx.save(); ctx.rotate(math.radians(-20 * (mira or 1)))
    ctx.rectangle(-11 * s, -26 * s, 22 * s, 52 * s)
    _contorno(ctx, (0.3, 0.32, 0.36), 3 * s)
    ctx.rectangle(-7 * s, -21 * s, 14 * s, 38 * s); ctx.set_source_rgb(0.55, 0.6, 0.66); ctx.fill()
    ctx.restore()


def obj_tablet(texto1="PRESUPUESTO", texto2="USD 1.200"):
    def f(ctx, s, ang, mira):
        ctx.save(); ctx.rotate(math.radians(-18 * (mira or 1)))
        ctx.translate(34 * s * (mira or 1), -6 * s)
        ctx.rectangle(-48 * s, -34 * s, 96 * s, 68 * s); _contorno(ctx, (0.15, 0.16, 0.18), 3 * s)
        ctx.rectangle(-41 * s, -27 * s, 82 * s, 54 * s); ctx.set_source_rgb(0.93, 0.95, 0.97); ctx.fill()
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        for i, (tx, tam) in enumerate(((texto1, 9.5), (texto2, 15))):
            ctx.set_font_size(tam * s); e = ctx.text_extents(tx)
            ctx.move_to(-e.width / 2 - e.x_bearing, (-8 + i * 22) * s)
            ctx.set_source_rgb(0.15, 0.18, 0.25); ctx.show_text(tx)
        ctx.restore()
    return f


def obj_llave(ctx, s, ang, mira):
    ctx.save(); ctx.rotate(math.radians(ang + 180))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for w, c in ((11 * s, NEGRO), (6 * s, (0.72, 0.74, 0.78))):
        ctx.move_to(0, 0); ctx.line_to(0, 70 * s); ctx.set_source_rgb(*c); ctx.set_line_width(w); ctx.stroke()
    ctx.arc(0, 74 * s, 11 * s, 0, 2 * math.pi); _contorno(ctx, (0.72, 0.74, 0.78), 3 * s)
    ctx.restore()


def obj_billete(ctx, s, ang, mira):
    ctx.save(); ctx.rotate(math.radians(-10))
    ctx.rectangle(-30 * s, -16 * s, 60 * s, 32 * s); _contorno(ctx, (0.55, 0.78, 0.5), 3 * s)
    ctx.arc(0, 0, 9 * s, 0, 2 * math.pi); ctx.set_source_rgb(0.35, 0.6, 0.35); ctx.fill()
    ctx.restore()


OBJETOS = {"telefono": obj_telefono, "tablet": obj_tablet(), "llave": obj_llave, "billete": obj_billete}


# ---------------------------------------------------------------- personaje
class Persona(Monigote):
    """Monigote ilustrado. Claves extra por fotograma: mano_d / mano_i (nombre de objeto o None).

    pelo: 'puntas', 'raya', 'corto', 'largo', 'coleta', 'calvo'
    ropa: dict(tipo='camisa'|'playera'|'vestido', color, cuello, manga='corta'|'larga',
               corbata=(r,g,b)|None, gafete='TEXTO'|None, pantalon=(r,g,b)|None, bolsillo=True)
    """
    def __init__(self, claves, escala=1.6, pelo="raya", color_pelo=(0.45, 0.27, 0.16),
                 ropa=None, semilla=1):
        super().__init__(claves, escala=escala, semilla=semilla)
        prev = dict(mano_d=None, mano_i=None)
        for c in self.claves:
            for k, v in prev.items(): c.setdefault(k, v)
            prev = dict(mano_d=c["mano_d"], mano_i=c["mano_i"])
        self.pelo, self.color_pelo = pelo, color_pelo
        self.ropa = dict(tipo="camisa", color=(0.85, 0.86, 0.88), cuello=None, manga="larga",
                         corbata=None, gafete=None, pantalon=None, bolsillo=False)
        self.ropa.update(ropa or {})

    # ------------------------------------------------------------ esqueleto
    def dibujar(self, ctx, t):
        pose, x, y, clave, moviendo = self.estado(t)
        s = self.s; pose = dict(pose)
        resp = math.sin(t * 2.2 + self.semilla) * 1.2
        pose["torso"] += math.sin(t * 1.3 + self.semilla) * 0.8
        if clave["pose"] == "saludo": pose["ad"] += math.sin(t * 12) * 22
        if clave["pose"] in ("explicar",): pose["ad"] += math.sin(t * 5) * 10
        dy = 0
        if moviendo:
            f = t * 8
            pose["mi"] = math.sin(f) * 24; pose["pi"] = pose["mi"] + max(0, math.sin(f - 1.2)) * -28
            pose["md"] = -math.sin(f) * 24; pose["pd"] = pose["md"] + max(0, -math.sin(f - 1.2)) * -28
            if clave["pose"] == "parado":
                pose["bi"] = -8 - math.sin(f) * 18; pose["ai"] = pose["bi"] - 10
                pose["bd"] = 8 + math.sin(f) * 18; pose["ad"] = pose["bd"] + 10
            dy = -abs(math.sin(f)) * 8 * s
        if clave["saltar"]: dy = -abs(math.sin(t * 7)) * 70 * s

        L = dict(torso=150 * s, brazo=78 * s, ante=72 * s, muslo=108 * s, pierna=104 * s, cabeza=70 * s)
        def cad2(o, a1, l1, a2, l2):
            p1 = (o[0] + vec(a1, l1)[0], o[1] + vec(a1, l1)[1])
            return p1, (p1[0] + vec(a2, l2)[0], p1[1] + vec(a2, l2)[1])
        rodi, pie_i = cad2((0, 0), pose["mi"], L["muslo"], pose["pi"], L["pierna"])
        rodd, pie_d = cad2((0, 0), pose["md"], L["muslo"], pose["pd"], L["pierna"])
        baja = max(pie_i[1], pie_d[1]) + 10 * s
        cad = (x, y + dy + resp - baja)
        mv = lambda p: (cad[0] + p[0], cad[1] + p[1])
        rodi, pie_i, rodd, pie_d = mv(rodi), mv(pie_i), mv(rodd), mv(pie_d)
        hombro = (cad[0] + vec(pose["torso"], L["torso"])[0], cad[1] + vec(pose["torso"], L["torso"])[1])
        ang_cab = pose["torso"] + pose["cabeza"]
        ang_pos = pose["torso"] + pose["cabeza"] * 0.3   # la cabeza gira más de lo que se desplaza
        cab = (hombro[0] + vec(ang_pos, L["cabeza"] * 0.95)[0], hombro[1] + vec(ang_pos, L["cabeza"] * 0.95)[1])
        hombro_i = (hombro[0] - 34 * s, hombro[1] + 12 * s)
        hombro_d = (hombro[0] + 34 * s, hombro[1] + 12 * s)
        codi, mani = cad2(hombro_i, pose["bi"], L["brazo"], pose["ai"], L["ante"])
        codd, mand = cad2(hombro_d, pose["bd"], L["brazo"], pose["ad"], L["ante"])
        mira = clave["mira"]

        # sombra en el piso
        ctx.save(); ctx.set_source_rgba(0, 0, 0, 0.16)
        ctx.translate(x, y); ctx.scale(1, 0.16); ctx.arc(0, 0, 95 * s * (1 - min(-dy, 80) / 200), 0, 2 * math.pi)
        ctx.fill(); ctx.restore()

        R = self.ropa; lw = 7 * s
        # piernas
        for (r, p) in ((rodi, pie_i), (rodd, pie_d)):
            if R["pantalon"]:
                _trazo_doble(ctx, [cad, r, p], 26 * s, R["pantalon"], 2.5 * s)
            else:
                ctx.set_source_rgb(*NEGRO); ctx.set_line_width(lw); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                ctx.move_to(cad[0] + (r[0] - cad[0]) * 0.02, cad[1]); ctx.line_to(*r); ctx.line_to(*p); ctx.stroke()
        # zapatos (domo con suela plana, punta hacia donde mira)
        for p, lado in ((pie_i, -1), (pie_d, 1)):
            d = mira if mira else lado * 0.5
            ctx.save(); ctx.translate(p[0] + d * 14 * s, p[1])
            ctx.move_to(-26 * s, 0); ctx.line_to(26 * s, 0)
            ctx.save(); ctx.translate(-d * 6 * s, 0); ctx.scale(1, 0.62)
            ctx.arc_negative(0, 0, 26 * s, 0, math.pi); ctx.restore()
            ctx.close_path(); ctx.set_source_rgb(0.13, 0.13, 0.14); ctx.fill_preserve()
            ctx.set_source_rgb(*NEGRO); ctx.set_line_width(2.5 * s); ctx.stroke()
            ctx.save(); ctx.translate(-d * 8 * s, -10 * s); ctx.scale(1, 0.4)
            ctx.arc(0, 0, 8 * s, 0, 2 * math.pi); ctx.restore(); ctx.set_source_rgba(1, 1, 1, 0.22); ctx.fill()
            ctx.restore()

        # cabello largo / coleta (detrás de la cabeza)
        self._pelo(ctx, cab, L["cabeza"], ang_cab, mira, atras=True)
        # torso de ropa
        self._ropa(ctx, cad, hombro, pose["torso"], s, mira, t)
        # brazos
        objetos = []
        for (h, c, m, ang, nombre) in ((hombro_i, codi, mani, pose["ai"], clave["mano_i"]),
                                       (hombro_d, codd, mand, pose["ad"], clave["mano_d"])):
            ctx.set_source_rgb(*NEGRO); ctx.set_line_width(lw); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(*h); ctx.line_to(*c); ctx.line_to(*m); ctx.stroke()
            if R["manga"] == "larga":
                _trazo_doble(ctx, [h, c, _sobre(c, m, 0.82)], 24 * s, R["color"], 2.6 * s)
                ctx.set_source_rgb(*NEGRO); ctx.set_line_width(lw)
            elif R["manga"] == "corta":
                ini = _sobre(h, c, -0.12)
                _manga(ctx, ini, _sobre(h, c, 0.62), 15 * s, 17 * s, R["color"], s)
                if R["cuello"]:
                    _manga(ctx, _sobre(h, c, 0.52), _sobre(h, c, 0.62), 16.5 * s, 17 * s, R["cuello"], s)
            objetos.append((m, ang, nombre))
        for (m, ang, nombre) in objetos:
            if nombre and nombre != "telefono":
                ctx.save(); ctx.translate(*m); OBJETOS[nombre](ctx, s, ang, mira); ctx.restore()
            self._mano(ctx, m, ang, s, mira)
            if nombre == "telefono":
                ctx.save(); ctx.translate(m[0] - 6 * s, m[1] - 12 * s); OBJETOS[nombre](ctx, s, ang, mira); ctx.restore()
        # cabeza
        self._cabeza(ctx, cab, L["cabeza"], ang_cab, mira, clave["cara"], t, s)

    # ------------------------------------------------------------ partes
    def _mano(self, ctx, m, ang, s, mira):
        ctx.save(); ctx.translate(*m); ctx.rotate(-math.radians(ang))
        ctx.save(); ctx.translate(0, 9 * s); ctx.scale(1, 1.15); ctx.arc(0, 0, 13 * s, 0, 2 * math.pi); ctx.restore()
        _contorno(ctx, PIEL, 2.8 * s)
        lado = 1 if (mira or 1) > 0 else -1
        ctx.save(); ctx.translate(lado * 12 * s, 3 * s); ctx.rotate(lado * 0.6); ctx.scale(0.55, 1)
        ctx.arc(0, 0, 9 * s, 0, 2 * math.pi); ctx.restore()
        _contorno(ctx, PIEL, 2.8 * s)
        ctx.restore()

    def _ropa(self, ctx, cad, hombro, ang, s, mira, t):
        R = self.ropa
        ux, uy = vec(ang, 1)          # de cadera a hombro
        nx, ny = -uy, ux              # perpendicular
        def P(a, b):                  # a = a lo ancho, b = a lo largo desde el hombro (positivo hacia abajo)
            return (hombro[0] + nx * a * s - ux * b * s, hombro[1] + ny * a * s - uy * b * s)
        largo = 150 + (80 if R["tipo"] == "vestido" else 26)
        bajo = 62 if R["tipo"] == "vestido" else 50
        pts = [P(-20, -6), P(-50, 4), P(-56, 22), P(-bajo, largo), P(bajo, largo), P(56, 22), P(50, 4), P(20, -6)]
        ctx.move_to(*pts[0])
        for p in pts[1:]: ctx.line_to(*p)
        ctx.close_path()
        ctx.save(); ctx.set_source_rgb(*R["color"]); ctx.fill_preserve(); ctx.clip_preserve()
        # sombra lateral (luz desde la izquierda)
        g = cairo.LinearGradient(*P(-60, 0), *P(60, 0))
        g.add_color_stop_rgba(0, 1, 1, 1, 0.10); g.add_color_stop_rgba(0.55, 0, 0, 0, 0.0); g.add_color_stop_rgba(1, 0, 0, 0, 0.22)
        ctx.set_source(g); ctx.fill_preserve(); ctx.restore()
        ctx.set_source_rgb(*NEGRO); ctx.set_line_width(3 * s); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
        # pliegues
        ctx.set_source_rgba(0, 0, 0, 0.25); ctx.set_line_width(2 * s)
        for (a0, b0, a1, b1) in ((-30, 100, -24, largo - 6), (26, 70, 32, 120)):
            ctx.move_to(*P(a0, b0)); ctx.line_to(*P(a1, b1)); ctx.stroke()
        # botones / línea central en camisa
        if R["tipo"] == "camisa":
            ctx.set_source_rgba(0, 0, 0, 0.35); ctx.set_line_width(2 * s)
            ctx.move_to(*P(0, 4)); ctx.line_to(*P(0, largo)); ctx.stroke()
        # cuello
        col = R["cuello"] or (oscurecer(R["color"], 0.92) if R["tipo"] == "camisa" else None)
        if R["tipo"] == "camisa":
            for lado in (-1, 1):
                ctx.move_to(*P(lado * 4, 2)); ctx.line_to(*P(lado * 24, -8)); ctx.line_to(*P(lado * 30, 6))
                ctx.line_to(*P(lado * 12, 26)); ctx.close_path(); _contorno(ctx, col, 2.6 * s)
        elif R["tipo"] in ("playera", "vestido"):
            ctx.move_to(*P(-20, -6)); ctx.curve_to(*P(-12, 12), *P(12, 12), *P(20, -6))
            ctx.set_source_rgb(*NEGRO); ctx.set_line_width(3 * s); ctx.stroke()
        # corbata
        if R["corbata"]:
            ctx.move_to(*P(-7, 0)); ctx.line_to(*P(7, 0)); ctx.line_to(*P(5, 14)); ctx.line_to(*P(-5, 14))
            ctx.close_path(); _contorno(ctx, R["corbata"], 2.4 * s)
            ctx.move_to(*P(-5, 14)); ctx.line_to(*P(5, 14)); ctx.line_to(*P(11, 120)); ctx.line_to(*P(0, 136))
            ctx.line_to(*P(-11, 120)); ctx.close_path(); _contorno(ctx, R["corbata"], 2.4 * s)
        # bolsillo y gafete
        lado = 1 if (mira or 1) > 0 else -1
        if R["bolsillo"]:
            q = [P(lado * 18, 46), P(lado * 40, 46), P(lado * 40, 72), P(lado * 18, 72)]
            ctx.move_to(*q[0]); [ctx.line_to(*p) for p in q[1:]]; ctx.close_path()
            ctx.set_source_rgba(0, 0, 0, 0.5); ctx.set_line_width(2 * s); ctx.stroke()
        if R["gafete"]:
            gx, gy = P(-lado * 22, 50)
            ctx.save(); ctx.translate(gx, gy); ctx.rotate(math.radians(180 - ang))
            ctx.rectangle(-21 * s, -7 * s, 42 * s, 14 * s); _contorno(ctx, (0.95, 0.95, 0.95), 2 * s)
            ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(7 * s); e = ctx.text_extents(R["gafete"])
            ctx.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing)
            ctx.set_source_rgb(0.1, 0.1, 0.15); ctx.show_text(R["gafete"]); ctx.restore()

    def _cabeza(self, ctx, c, r, ang, mira, cara, t, s):
        ctx.save(); ctx.translate(*c); ctx.rotate(math.radians(180 - ang))
        ctx.save(); ctx.scale(0.96, 1.0); ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.restore()
        g = cairo.LinearGradient(-r, -r, r, r)
        g.add_color_stop_rgb(0, *PIEL); g.add_color_stop_rgb(0.55, *PIEL); g.add_color_stop_rgb(1, *SOMBRA_PIEL)
        ctx.set_source(g); ctx.fill_preserve()
        ctx.set_source_rgb(*NEGRO); ctx.set_line_width(4.2 * s); ctx.stroke()
        ctx.restore()
        self._pelo(ctx, c, r, ang, mira, atras=False)
        # cara
        ctx.save(); ctx.translate(*c); ctx.rotate(math.radians(180 - ang))
        ox = (mira or 0) * r * 0.2
        parp = (t + self.semilla * 0.9) % 3.7 < 0.11
        ctx.set_source_rgb(*NEGRO); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        cejas = {"serio": (0.0, -6), "feliz": (-0.12, 0), "sorpresa": (-0.24, 0), "triste": (0.0, 14),
                 "pensar": (-0.1, -10), "enojado": (0.06, -22), "preocupado": (-0.06, 12)}
        cy_off, incl = cejas.get(cara, (0.0, 0))
        for lado in (-1, 1):
            ex, ey = ox + lado * r * 0.32, r * 0.04
            if parp:
                ctx.set_line_width(r * 0.06); ctx.move_to(ex - r * 0.08, ey); ctx.line_to(ex + r * 0.08, ey); ctx.stroke()
            else:
                ctx.save(); ctx.translate(ex, ey)
                k = 1.25 if cara == "sorpresa" else 1.0
                ctx.scale(0.085 * r * k, 0.13 * r * k); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); ctx.fill()
                ctx.set_source_rgb(1, 1, 1); ctx.arc(ex + r * 0.025, ey - r * 0.05, r * 0.025, 0, 2 * math.pi)
                ctx.fill(); ctx.set_source_rgb(*NEGRO)
            # ceja: incl>0 = extremo interior arriba (tristeza); <0 = abajo (enojo)
            by = -r * (0.27 - cy_off)
            a = math.radians(incl) * lado
            ctx.set_line_width(r * 0.075)
            ctx.move_to(ex - r * 0.13 * math.cos(a), by - r * 0.13 * math.sin(a))
            ctx.line_to(ex + r * 0.13 * math.cos(a), by + r * 0.13 * math.sin(a)); ctx.stroke()
        mx, my = ox * 1.1, r * 0.45
        ctx.set_line_width(r * 0.055)
        if cara == "feliz":
            ctx.arc(mx, my - r * 0.14, r * 0.17, math.radians(30), math.radians(150)); ctx.stroke()
        elif cara == "sorpresa":
            ctx.save(); ctx.translate(mx, my); ctx.scale(0.07 * r, 0.1 * r); ctx.arc(0, 0, 1, 0, 2 * math.pi)
            ctx.restore(); ctx.fill()
        elif cara in ("triste", "preocupado"):
            ctx.arc(mx, my + r * 0.12, r * 0.13, math.radians(215), math.radians(325)); ctx.stroke()
        elif cara == "enojado":
            ctx.move_to(mx - r * 0.12, my + r * 0.02); ctx.line_to(mx + r * 0.12, my - r * 0.02); ctx.stroke()
        elif cara == "pensar":
            ctx.move_to(mx - r * 0.1, my); ctx.line_to(mx + r * 0.1, my + r * 0.04); ctx.stroke()
        else:
            ctx.move_to(mx - r * 0.1, my); ctx.line_to(mx + r * 0.1, my); ctx.stroke()
        ctx.restore()

    def _pelo(self, ctx, c, r, ang, mira, atras):
        p = self.pelo
        if p == "calvo": return
        d = 1 if (mira or 0) >= 0 else -1
        col = self.color_pelo
        s = r / 64
        ctx.save(); ctx.translate(*c); ctx.rotate(math.radians(180 - ang)); ctx.scale(d, 1)
        if atras:
            if p == "largo":
                ctx.move_to(-r * 1.02, -r * 0.2); ctx.curve_to(-r * 1.25, r * 0.8, -r * 1.1, r * 1.35, -r * 0.6, r * 1.4)
                ctx.line_to(r * 0.6, r * 1.4); ctx.curve_to(r * 1.1, r * 1.35, r * 1.25, r * 0.8, r * 1.02, -r * 0.2)
                ctx.close_path(); _contorno(ctx, col, 3.2 * s)
            elif p == "coleta":
                ctx.save(); ctx.translate(-r * 0.95, -r * 0.35); ctx.rotate(0.5); ctx.scale(0.55, 1)
                ctx.arc(0, r * 0.5, r * 0.6, 0, 2 * math.pi); ctx.restore(); _contorno(ctx, col, 3.2 * s)
            ctx.restore(); return
        if p == "puntas":
            rnd = random.Random(self.semilla * 7 + 3)
            ctx.move_to(-r * 1.0, r * 0.05)
            n = 13
            for i in range(n + 1):
                a = math.radians(200 + (340 - 200) * i / n)
                rr = r * (1.03 if i % 2 else rnd.uniform(1.28, 1.48))
                aa = a + (math.radians(rnd.uniform(-4, 4)) if i % 2 == 0 else 0)
                ctx.line_to(math.cos(aa) * rr, math.sin(aa) * rr)
            ctx.line_to(r * 1.12, r * 0.0)
            ctx.line_to(r * 0.86, -r * 0.18)
            # flequillo en picos sobre la frente
            fr = [(0.78, -0.36), (0.62, -0.08), (0.45, -0.42), (0.25, -0.1), (0.1, -0.46), (-0.12, -0.14),
                  (-0.28, -0.5), (-0.5, -0.2), (-0.62, -0.5), (-0.86, -0.1)]
            for (fx, fy) in fr: ctx.line_to(fx * r, fy * r)
            ctx.close_path(); _contorno(ctx, col, 3.4 * s)
            ctx.set_source_rgba(1, 1, 1, 0.18); ctx.set_line_width(3 * s)
            ctx.move_to(-r * 0.4, -r * 0.95); ctx.line_to(-r * 0.15, -r * 0.75); ctx.stroke()
        elif p in ("raya", "corto", "coleta", "largo"):
            alto = 1.12 if p != "corto" else 1.06
            ctx.move_to(-r * 1.03, r * 0.05)
            ctx.curve_to(-r * 1.15, -r * 0.9, -r * 0.4, -r * alto * 1.18, r * 0.25, -r * alto)
            ctx.curve_to(r * 0.85, -r * 0.95, r * 1.12, -r * 0.5, r * 1.04, -r * 0.05)
            ctx.line_to(r * 0.92, -r * 0.08)
            ctx.curve_to(r * 0.85, -r * 0.42, r * 0.55, -r * 0.55, r * 0.2, -r * 0.5)
            ctx.curve_to(-r * 0.2, -r * 0.62, -r * 0.55, -r * 0.4, -r * 0.62, -r * 0.62)  # raya hacia el lado
            ctx.curve_to(-r * 0.78, -r * 0.4, -r * 0.86, -r * 0.2, -r * 0.88, r * 0.12)
            ctx.close_path(); _contorno(ctx, col, 3.4 * s)
            ctx.set_source_rgba(1, 1, 1, 0.2); ctx.set_line_width(3 * s)
            ctx.move_to(-r * 0.2, -r * 0.92); ctx.curve_to(r * 0.1, -r * 0.98, r * 0.4, -r * 0.92, r * 0.6, -r * 0.8); ctx.stroke()
        ctx.restore()


# ---------------------------------------------------------------- escenarios
def _texto(ctx, txt, x, y, tam, color, ancho=None, peso=cairo.FONT_WEIGHT_BOLD):
    ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, peso)
    ctx.set_font_size(tam)
    if ancho:
        mayor = max(ctx.text_extents(l).width for l in txt.split("\n"))
        if mayor > ancho: tam *= ancho / mayor; ctx.set_font_size(tam)
    for i, linea in enumerate(txt.split("\n")):
        e = ctx.text_extents(linea)
        ctx.move_to(x - e.width / 2 - e.x_bearing, y + i * tam * 1.12)
        ctx.set_source_rgb(*color); ctx.show_text(linea)


class Taller:
    """Taller mecánico limpio: pared gris, carteles, escritorio con monitor, ventanal y piso brillante.
    piso: altura (y) donde la pared toca el piso."""
    def __init__(self, carteles=("SERVICIO\nPREMIUM", "DIAGNÓSTICO", "REPUESTOS\nORIGINALES"), piso=1180):
        self.carteles, self.piso = carteles, piso

    def dibujar(self, ctx, t):
        P = self.piso
        g = cairo.LinearGradient(0, 0, 0, P)
        g.add_color_stop_rgb(0, 0.80, 0.81, 0.84); g.add_color_stop_rgb(1, 0.88, 0.89, 0.91)
        ctx.set_source(g); ctx.rectangle(0, 0, W, P); ctx.fill()
        # techo con lámparas
        ctx.set_source_rgb(0.72, 0.73, 0.76); ctx.rectangle(0, 0, W, 120); ctx.fill()
        for lx in (120, 620):
            ctx.rectangle(lx, 70, 340, 26); ctx.set_source_rgb(0.97, 0.98, 1.0); ctx.fill()
            gl = cairo.RadialGradient(lx + 170, 100, 10, lx + 170, 120, 420)
            gl.add_color_stop_rgba(0, 1, 1, 1, 0.35); gl.add_color_stop_rgba(1, 1, 1, 1, 0)
            ctx.set_source(gl); ctx.rectangle(0, 96, W, 500); ctx.fill()
        # ventanal (derecha)
        vx, vy, vw, vh = 640, 300, 520, 760
        ctx.rectangle(vx, vy, vw, vh); ctx.set_source_rgb(0.22, 0.24, 0.27); ctx.fill()
        for i in range(3):
            for j in range(3):
                px, py = vx + 18 + i * 170, vy + 18 + j * 248
                gv = cairo.LinearGradient(px, py, px + 150, py + 230)
                gv.add_color_stop_rgb(0, 0.93, 0.95, 0.98); gv.add_color_stop_rgb(1, 0.78, 0.82, 0.88)
                ctx.set_source(gv); ctx.rectangle(px, py, 152, 230); ctx.fill()
                ctx.set_source_rgba(1, 1, 1, 0.5); ctx.set_line_width(10)
                ctx.move_to(px + 30, py + 230); ctx.line_to(px + 110, py); ctx.stroke()
        # carteles
        xs = [60, 330]
        for i, txt in enumerate(self.carteles[:2]):
            cx, cy, cw, ch = xs[i], 360, 230, 290
            ctx.set_source_rgba(0, 0, 0, 0.18); ctx.rectangle(cx + 8, cy + 10, cw, ch); ctx.fill()
            ctx.rectangle(cx, cy, cw, ch); ctx.set_source_rgb(0.26, 0.28, 0.32); ctx.fill()
            ctx.rectangle(cx + 10, cy + 10, cw - 20, ch - 20); ctx.set_source_rgb(0.36, 0.38, 0.43); ctx.fill()
            _texto(ctx, txt, cx + cw / 2, cy + 58, 30, (0.95, 0.96, 0.98), ancho=cw - 36)
            # dibujito: engrane
            ex, ey = cx + cw / 2, cy + 200
            for k in range(8):
                a = k * math.pi / 4
                ctx.save(); ctx.translate(ex, ey); ctx.rotate(a); ctx.rectangle(-9, -48, 18, 16); ctx.restore()
            ctx.arc(ex, ey, 38, 0, 2 * math.pi); ctx.set_source_rgb(0.62, 0.65, 0.7); ctx.fill()
            ctx.arc(ex, ey, 14, 0, 2 * math.pi); ctx.set_source_rgb(0.36, 0.38, 0.43); ctx.fill()
        if len(self.carteles) > 2:
            cx, cy, cw, ch = 690, 160, 240, 120
            ctx.rectangle(cx, cy, cw, ch); ctx.set_source_rgb(0.93, 0.94, 0.96); ctx.fill()
            ctx.set_source_rgb(0.26, 0.28, 0.32); ctx.set_line_width(6); ctx.rectangle(cx, cy, cw, ch); ctx.stroke()
            _texto(ctx, self.carteles[2], cx + cw / 2, cy + 52, 26, (0.22, 0.3, 0.5))
        # zócalo
        ctx.rectangle(0, P - 150, W, 150); ctx.set_source_rgb(0.62, 0.64, 0.68); ctx.fill()
        ctx.rectangle(0, P - 156, W, 8); ctx.set_source_rgb(0.5, 0.52, 0.56); ctx.fill()
        # escritorio con monitor (izquierda)
        ctx.rectangle(30, 880, 560, 22); _contorno(ctx, (0.72, 0.6, 0.45), 3)
        for lx in (60, 545):
            ctx.rectangle(lx, 902, 16, P - 902); ctx.set_source_rgb(0.42, 0.44, 0.48); ctx.fill()
        ctx.rectangle(140, 720, 190, 130); _contorno(ctx, (0.2, 0.21, 0.24), 3)
        gm = cairo.LinearGradient(150, 730, 320, 840)
        gm.add_color_stop_rgb(0, 0.55, 0.6, 0.68); gm.add_color_stop_rgb(1, 0.3, 0.33, 0.38)
        ctx.set_source(gm); ctx.rectangle(150, 730, 170, 110); ctx.fill()
        ctx.rectangle(222, 850, 26, 30); ctx.set_source_rgb(0.2, 0.21, 0.24); ctx.fill()
        ctx.rectangle(150, 868, 170, 12); ctx.fill()
        # piso brillante
        g = cairo.LinearGradient(0, P, 0, H)
        g.add_color_stop_rgb(0, 0.74, 0.75, 0.78); g.add_color_stop_rgb(1, 0.9, 0.91, 0.93)
        ctx.set_source(g); ctx.rectangle(0, P, W, H - P); ctx.fill()
        for (rx, rw, a) in ((180, 120, 0.25), (520, 70, 0.18), (800, 160, 0.2)):   # reflejos de luz
            gr = cairo.LinearGradient(0, P, 0, H)
            gr.add_color_stop_rgba(0, 1, 1, 1, a); gr.add_color_stop_rgba(1, 1, 1, 1, 0)
            ctx.set_source(gr)
            ctx.move_to(rx, P); ctx.line_to(rx + rw, P); ctx.line_to(rx + rw * 2.2 - 100, H); ctx.line_to(rx - 100, H)
            ctx.close_path(); ctx.fill()
        ctx.set_source_rgba(0, 0, 0, 0.08); ctx.set_line_width(3)
        for i in range(-6, 12):
            ctx.move_to(W / 2 + i * 90, P); ctx.line_to(W / 2 + i * 260, H); ctx.stroke()


class Auto:
    """Sedán genérico de lado (sin marca), mirando a la izquierda. x,y = punto del piso bajo el centro."""
    def __init__(self, x=900, y=1700, escala=1.0, color=(0.74, 0.76, 0.8), capo_abierto=False, t0=0):
        self.x, self.y, self.s, self.color, self.capo, self.t0 = x, y, escala, color, capo_abierto, t0

    def dibujar(self, ctx, t):
        s = self.s; c = self.color
        ctx.save(); ctx.translate(self.x, self.y); ctx.scale(s, s)
        ctx.set_source_rgba(0, 0, 0, 0.22); ctx.save(); ctx.scale(1, 0.1); ctx.arc(0, 0, 470, 0, 2 * math.pi); ctx.restore(); ctx.fill()
        if self.capo:   # capó levantado (detrás de la carrocería)
            ctx.move_to(-410, -250); ctx.line_to(-120, -330); ctx.line_to(-160, -620); ctx.line_to(-400, -420)
            ctx.close_path(); _contorno(ctx, oscurecer(c, 0.55), 5)
            ctx.set_source_rgba(1, 1, 1, 0.12); ctx.move_to(-380, -420); ctx.line_to(-180, -580); ctx.line_to(-170, -540)
            ctx.close_path(); ctx.fill()
            ctx.set_source_rgb(0.15, 0.15, 0.16); ctx.set_line_width(6); ctx.move_to(-300, -260); ctx.line_to(-260, -470); ctx.stroke()
        # carrocería
        ctx.move_to(-470, -70)
        ctx.curve_to(-480, -150, -470, -220, -430, -250)
        ctx.line_to(-170, -290)
        ctx.curve_to(-100, -390, -10, -430, 120, -430)
        ctx.curve_to(250, -430, 330, -380, 400, -290)
        ctx.curve_to(460, -280, 480, -220, 480, -140)
        ctx.line_to(480, -70); ctx.close_path()
        g = cairo.LinearGradient(0, -430, 0, -60)
        g.add_color_stop_rgb(0, *[min(1, v * 1.15) for v in c]); g.add_color_stop_rgb(0.45, *c)
        g.add_color_stop_rgb(0.5, *oscurecer(c, 0.82)); g.add_color_stop_rgb(1, *oscurecer(c, 0.6))
        ctx.set_source(g); ctx.fill_preserve(); ctx.set_source_rgb(*NEGRO); ctx.set_line_width(5); ctx.stroke()
        # motor visible si el capó está abierto
        if self.capo:
            ctx.move_to(-420, -245); ctx.line_to(-175, -285); ctx.line_to(-185, -255); ctx.line_to(-420, -225)
            ctx.close_path(); ctx.set_source_rgb(0.18, 0.19, 0.21); ctx.fill()
        # ventanas
        ctx.move_to(-130, -290); ctx.curve_to(-80, -370, -10, -400, 100, -402); ctx.line_to(100, -290); ctx.close_path()
        ctx.move_to(130, -290); ctx.line_to(130, -402); ctx.curve_to(230, -400, 300, -360, 350, -290); ctx.close_path()
        gv = cairo.LinearGradient(-100, -400, 300, -290)
        gv.add_color_stop_rgb(0, 0.3, 0.34, 0.4); gv.add_color_stop_rgb(1, 0.12, 0.13, 0.16)
        ctx.set_source(gv); ctx.fill_preserve(); ctx.set_source_rgb(*NEGRO); ctx.set_line_width(4); ctx.stroke()
        # línea de puertas, manija, faro, parrilla
        ctx.set_source_rgba(0, 0, 0, 0.5); ctx.set_line_width(3)
        ctx.move_to(115, -290); ctx.line_to(115, -90); ctx.stroke()
        ctx.move_to(-150, -285); ctx.line_to(-150, -100); ctx.stroke()
        ctx.set_source_rgba(1, 1, 1, 0.6); ctx.set_line_width(4)
        ctx.move_to(-440, -215); ctx.line_to(440, -230); ctx.stroke()
        for hx in (-60, 200):
            ctx.rectangle(hx, -250, 46, 12); _contorno(ctx, oscurecer(c, 0.7), 2.5)
        ctx.move_to(-470, -200); ctx.line_to(-400, -212); ctx.line_to(-405, -175); ctx.line_to(-472, -170); ctx.close_path()
        _contorno(ctx, (0.95, 0.95, 0.88), 3)
        ctx.rectangle(-478, -150, 30, 50); _contorno(ctx, (0.15, 0.15, 0.17), 3)
        ctx.rectangle(455, -220, 25, 40); _contorno(ctx, (0.75, 0.15, 0.15), 3)
        # llantas
        for wx in (-280, 300):
            ctx.arc(wx, -85, 110, math.pi, 2 * math.pi); ctx.set_source_rgb(0.1, 0.1, 0.11); ctx.fill()
            ctx.arc(wx, -70, 92, 0, 2 * math.pi); _contorno(ctx, (0.12, 0.12, 0.13), 4)
            ctx.arc(wx, -70, 60, 0, 2 * math.pi); _contorno(ctx, (0.78, 0.8, 0.84), 3)
            ctx.set_source_rgb(0.45, 0.47, 0.5); ctx.set_line_width(12)
            for k in range(5):
                a = k * 2 * math.pi / 5 + 0.3
                ctx.move_to(wx, -70); ctx.line_to(wx + math.cos(a) * 55, -70 + math.sin(a) * 55); ctx.stroke()
            ctx.arc(wx, -70, 14, 0, 2 * math.pi); _contorno(ctx, (0.7, 0.72, 0.76), 2)
        ctx.restore()


class Cartel:
    """Tarjeta de dato en pantalla (estilo limpio, esquinas redondeadas)."""
    def __init__(self, txt, t0, t1, x=W / 2, y=380, tam=64, fondo=(1, 1, 1), color=(0.12, 0.13, 0.17),
                 acento=(0.85, 0.15, 0.15)):
        self.txt, self.t0, self.t1, self.x, self.y, self.tam = txt, t0, t1, x, y, tam
        self.fondo, self.color, self.acento = fondo, color, acento

    def dibujar(self, ctx, t):
        if not (self.t0 <= t <= self.t1): return
        from motor import rebote
        k = min(rebote((t - self.t0) / 0.35), 1.1) * suave((self.t1 - t) / 0.2)
        ctx.save(); ctx.translate(self.x, self.y); ctx.scale(k, k)
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(self.tam)
        lineas = self.txt.split("\n")
        ancho = max(ctx.text_extents(l).x_advance for l in lineas) + self.tam
        alto = len(lineas) * self.tam * 1.2 + self.tam * 0.6
        r = 22
        ctx.new_sub_path()
        for (cx, cy, a) in ((ancho / 2 - r, -alto / 2 + r, -90), (ancho / 2 - r, alto / 2 - r, 0),
                            (-ancho / 2 + r, alto / 2 - r, 90), (-ancho / 2 + r, -alto / 2 + r, 180)):
            ctx.arc(cx, cy, r, math.radians(a), math.radians(a + 90))
        ctx.close_path()
        ctx.save(); ctx.translate(6, 10); ctx.set_source_rgba(0, 0, 0, 0.25); ctx.fill_preserve(); ctx.restore()
        _contorno(ctx, self.fondo, 5)
        ctx.rectangle(-ancho / 2 + 14, -alto / 2 + 14, 10, alto - 28); ctx.set_source_rgb(*self.acento); ctx.fill()
        for i, l in enumerate(lineas):
            e = ctx.text_extents(l)
            ctx.move_to(-e.x_advance / 2 + 8, -alto / 2 + self.tam * 0.3 + self.tam * (i + 0.95) * 1.2 - self.tam * 0.2)
            ctx.set_source_rgb(*self.color); ctx.show_text(l)
        ctx.restore()
