"""Monitos con ropa, escenarios y utilería dibujados con código (pycairo), en el estilo «taller»:
cabeza redonda blanca, brazos y piernas de palito, manos de guante blancas, zapatos grandes,
ropa real encima y escenarios limpios en grises y azules.

Todo se dibuja en un lienzo de 1920x1080. Deja lo importante dentro de x 260–1660, y 140–940
(ensamblar.py recorta los bordes al hacer zoom).

Requiere: pip install pycairo
"""
import math, random
import cairo

W, H = 1920, 1080
TINTA = (0.10, 0.10, 0.12)
BLANCO = (1, 1, 1)
CARA = (0.985, 0.985, 0.985)
SOMBRA = (0.88, 0.89, 0.91)
ROJO = (0.85, 0.16, 0.16)
VERDE_DINERO = (0.42, 0.66, 0.38)
ORO = (0.96, 0.77, 0.22)
FUENTE = "Inter"


# ---------------------------------------------------------------- básicos
def lienzo():
    sup = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(sup)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    return sup, ctx


def redondo(ctx, x, y, w, h, r):
    r = max(0.1, min(r, w / 2, h / 2))
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def pintar(ctx, color, grosor=5, linea=TINTA):
    ctx.set_source_rgb(*color)
    if grosor:
        ctx.fill_preserve(); ctx.set_source_rgb(*linea); ctx.set_line_width(grosor); ctx.stroke()
    else:
        ctx.fill()


def linea(ctx, pts, ancho, color=TINTA):
    ctx.move_to(*pts[0])
    for p in pts[1:]: ctx.line_to(*p)
    ctx.set_source_rgb(*color); ctx.set_line_width(ancho); ctx.stroke()


def circulo(ctx, x, y, r, color, grosor=5):
    ctx.new_path(); ctx.arc(x, y, r, 0, 2 * math.pi); pintar(ctx, color, grosor)


def oscuro(c, f=0.75): return tuple(v * f for v in c)
def claro(c, f=0.3): return tuple(v + (1 - v) * f for v in c)


def texto(ctx, txt, x, y, tam, color=TINTA, borde=None, peso="Bold", rot=0, centro=True, fuente=None):
    ctx.save(); ctx.translate(x, y); ctx.rotate(math.radians(rot))
    fam = fuente or (FUENTE + (" Black" if peso == "Black" else ""))
    ctx.select_font_face(fam, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(tam)
    e = ctx.text_extents(txt)
    ctx.move_to(-e.width / 2 - e.x_bearing if centro else 0, -e.height / 2 - e.y_bearing)
    ctx.text_path(txt)
    if borde:
        ctx.set_source_rgb(*borde); ctx.set_line_width(tam * 0.16); ctx.stroke_preserve()
    ctx.set_source_rgb(*color); ctx.fill(); ctx.restore()


# ---------------------------------------------------------------- personaje
# Ángulos en grados: 0 = abajo, 90 = hacia la derecha de la pantalla, 180 = arriba, -90 = izquierda.
# Cada brazo: (hombro→codo, codo→mano). i = brazo de la izquierda de la pantalla, d = derecha.
POSES = {
    "parado":      dict(i=(-10, -4), d=(10, 4)),
    "jarras":      dict(i=(-50, 40), d=(50, -40)),
    "brazos_arriba": dict(i=(-150, -175), d=(150, 175)),
    "sostener":    dict(i=(-30, 40), d=(30, -40)),          # sostiene algo delante (con las dos manos)
    "sostener_d":  dict(i=(-10, -4), d=(40, 100)),           # sostiene algo con la mano derecha, a un lado
    "mostrar_d":   dict(i=(-10, -4), d=(110, 150)),          # levanta algo con la derecha
    "señalar_d":   dict(i=(-10, -4), d=(95, 95)),
    "dedo_arriba": dict(i=(-10, -4), d=(40, 170)),
    "shh":         dict(i=(-10, -4), d=(30, 200)),
    "cabeza":      dict(i=(-120, 150), d=(120, -150)),       # manos en la cabeza
    "telefono":    dict(i=(-10, -4), d=(35, 175)),           # teléfono en la oreja (lado derecho)
    "mirar_telefono": dict(i=(-35, 45), d=(35, -45)),
    "mirar_manos": dict(i=(-40, 60), d=(40, -60)),
    "entregar":    dict(i=(-10, -4), d=(70, 100)),
    "vendar":      dict(i=(-60, 80), d=(80, 100)),
    "cruzados":    dict(i=(-35, 75), d=(35, -75)),
    "rifle":       dict(i=(-20, 70), d=(25, -60)),
    "saludo":      dict(i=(-10, -4), d=(130, 165)),
    "correr":      dict(i=(-60, -120), d=(60, 120)),
}


class Monito:
    """Personaje. ropa: bata, toga, camisa, traje, sicario, jefe, reclutador, nina, mujer.
    cara: neutral, feliz, orgulloso, sorpresa, preocupado, triste, serio, enojado, malvado, aterrado, dudoso, dormido
    pelo: picos, castano, largo, coleta, rapado, None.   sombrero: vaquero, birrete, gorra, None."""
    def __init__(self, ropa="camisa", cara="neutral", pose="parado", pelo=None, sombrero=None, bigote=False,
                 sudor=False, mira=0.0, color=None, tatuajes=False, cadena=False, lentes=False, manchas=False):
        self.ropa, self.cara, self.pose, self.pelo, self.sombrero = ropa, cara, pose, pelo, sombrero
        self.bigote, self.sudor, self.mira, self.color = bigote, sudor, mira, color
        self.tatuajes, self.cadena, self.lentes, self.manchas = tatuajes, cadena, lentes, manchas
        self.manos = {}

    # ------------------------------------------------------------
    def dibujar(self, ctx, x, y, s=1.0, silueta=False, color_silueta=TINTA):
        if silueta:
            ctx.push_group(); self._dibujar(ctx, x, y, s); patron = ctx.pop_group()
            ctx.set_source_rgb(*color_silueta); ctx.mask(patron); return self
        self._dibujar(ctx, x, y, s); return self

    def _dibujar(self, ctx, x, y, s):
        r = self.ropa
        # sombra en el piso
        ctx.save(); ctx.translate(x, y + 4 * s); ctx.scale(1, 0.13); ctx.arc(0, 0, 95 * s, 0, 2 * math.pi)
        ctx.restore(); ctx.set_source_rgba(0, 0, 0, 0.16); ctx.fill()
        chico = r in ("nina",)
        k = 0.62 if chico else 1.0
        pierna = 205 * s * k
        cadera = (x, y - 26 * s - pierna)
        # piernas y zapatos
        for lado in (-1, 1):
            hx = x + lado * 15 * s; fx = x + lado * 32 * s
            pant = {"traje": (0.16, 0.18, 0.24), "sicario": (0.32, 0.34, 0.26), "jefe": (0.2, 0.25, 0.4),
                    "reclutador": (0.22, 0.24, 0.3)}.get(r)
            if pant:  # pantalón de verdad
                ctx.move_to(hx, cadera[1]); ctx.line_to(fx, y - 30 * s)
                ctx.set_source_rgb(*TINTA); ctx.set_line_width(30 * s); ctx.stroke()
                ctx.move_to(hx, cadera[1]); ctx.line_to(fx, y - 30 * s)
                ctx.set_source_rgb(*pant); ctx.set_line_width(22 * s); ctx.stroke()
            else:
                linea(ctx, [(hx, cadera[1]), (fx, y - 22 * s)], 8 * s)
            ctx.save(); ctx.translate(fx + lado * 14 * s, y - 14 * s); ctx.scale(1.6, 0.85)
            ctx.arc(0, 0, 21 * s * (0.8 if chico else 1), 0, 2 * math.pi); ctx.restore()
            pintar(ctx, (0.12, 0.12, 0.14), 4 * s)
            ctx.save(); ctx.translate(fx + lado * 20 * s, y - 22 * s); ctx.scale(1.6, 0.6)
            ctx.arc(0, 0, 7 * s, 0, 2 * math.pi); ctx.restore(); ctx.set_source_rgba(1, 1, 1, 0.25); ctx.fill()
        # torso (ropa)
        alto_t = 175 * s * k; ancho_t = 118 * s * k
        hombro_y = cadera[1] - alto_t
        self._ropa(ctx, x, cadera[1], hombro_y, ancho_t, alto_t, s * k)
        # brazos
        pose = POSES[self.pose]
        manga = self._color_manga()
        for lado, clave in ((-1, "i"), (1, "d")):
            a1, a2 = pose[clave]
            hx, hy = x + lado * (ancho_t / 2 - 8 * s), hombro_y + 18 * s
            l1, l2 = 88 * s * k, 82 * s * k
            cx_, cy_ = hx + math.sin(math.radians(a1)) * l1, hy + math.cos(math.radians(a1)) * l1
            mx, my = cx_ + math.sin(math.radians(a2)) * l2, cy_ + math.cos(math.radians(a2)) * l2
            linea(ctx, [(hx, hy), (cx_, cy_), (mx, my)], 8 * s)
            if manga:  # manga sobre el brazo superior
                largo = 0.95 if r in ("bata", "traje", "toga", "reclutador") else 0.5
                ex, ey = hx + (cx_ - hx) * largo, hy + (cy_ - hy) * largo
                ctx.move_to(hx, hy); ctx.line_to(ex, ey)
                ctx.set_source_rgb(*TINTA); ctx.set_line_width(34 * s * k); ctx.stroke()
                ctx.move_to(hx, hy); ctx.line_to(ex, ey)
                ctx.set_source_rgb(*manga); ctx.set_line_width(26 * s * k); ctx.stroke()
                if r == "bata" and largo > 0.9:  # la bata sigue en el antebrazo
                    fx2, fy2 = cx_ + (mx - cx_) * 0.55, cy_ + (my - cy_) * 0.55
                    ctx.move_to(cx_, cy_); ctx.line_to(fx2, fy2)
                    ctx.set_source_rgb(*TINTA); ctx.set_line_width(30 * s); ctx.stroke()
                    ctx.move_to(cx_, cy_); ctx.line_to(fx2, fy2)
                    ctx.set_source_rgb(*manga); ctx.set_line_width(22 * s); ctx.stroke()
            if self.tatuajes:
                for t in (0.62, 0.8):
                    tx, ty = hx + (cx_ - hx) * t, hy + (cy_ - hy) * t
                    linea(ctx, [(tx - 7 * s, ty - 3 * s), (tx + 7 * s, ty + 3 * s)], 3 * s, (0.25, 0.3, 0.45))
            circulo(ctx, mx, my, 17 * s * k, BLANCO, 4 * s)          # guante
            ctx.arc(mx - 5 * s, my - 4 * s, 5 * s, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, 0.0); ctx.fill()
            self.manos[clave] = (mx, my)
        # cabeza
        R = 80 * s * (0.8 if chico else 1)
        cx, cy = x, hombro_y - R * 0.88
        linea(ctx, [(x, hombro_y), (x, hombro_y - 14 * s)], 8 * s)
        if self.pelo in ("largo", "coleta"): self._pelo_atras(ctx, cx, cy, R)
        ctx.new_path(); ctx.arc(cx, cy, R, 0, 2 * math.pi); ctx.set_source_rgb(*CARA); ctx.fill()
        ctx.save(); ctx.arc(cx, cy, R, 0, 2 * math.pi); ctx.clip()
        ctx.new_path(); ctx.arc(cx + R * 0.95, cy + R * 0.25, R * 0.75, 0, 2 * math.pi)
        ctx.set_source_rgb(*SOMBRA); ctx.fill(); ctx.restore()
        if self.manchas:
            ctx.save(); ctx.arc(cx, cy, R, 0, 2 * math.pi); ctx.clip()
            for (dx, dy, rr) in ((-0.45, 0.35, 0.12), (0.4, -0.3, 0.09), (0.3, 0.45, 0.07)):
                ctx.new_path(); ctx.arc(cx + dx * R, cy + dy * R, rr * R, 0, 2 * math.pi)
                ctx.set_source_rgba(0.35, 0.3, 0.25, 0.45); ctx.fill()
            ctx.restore()
        ctx.new_path(); ctx.arc(cx, cy, R, 0, 2 * math.pi); ctx.set_source_rgb(*TINTA)
        ctx.set_line_width(5 * s); ctx.stroke()
        self._cara(ctx, cx, cy, R, s)
        self._pelo(ctx, cx, cy, R, s)
        self._sombrero(ctx, cx, cy, R, s)
        self.cabeza = (cx, cy, R)
        return self

    def _color_manga(self):
        return {"bata": (0.97, 0.97, 0.98), "toga": (0.12, 0.12, 0.16), "camisa": self.color or (0.36, 0.55, 0.78),
                "traje": (0.16, 0.18, 0.24), "sicario": (0.25, 0.27, 0.22), "jefe": (0.78, 0.18, 0.2),
                "reclutador": (0.22, 0.24, 0.3), "nina": self.color or (0.95, 0.55, 0.7), "mujer": self.color or (0.55, 0.42, 0.7)
                }.get(self.ropa)

    def _ropa(self, ctx, x, yc, yh, w, h, s):
        r = self.ropa
        if r == "bata":
            # camisa celeste y bata blanca larga
            redondo(ctx, x - w / 2, yh, w, h, 22 * s); pintar(ctx, (0.62, 0.78, 0.92), 5 * s)
            for lado in (-1, 1):
                ctx.move_to(x + lado * 6 * s, yh + 4 * s); ctx.line_to(x + lado * w / 2, yh + 4 * s)
                ctx.line_to(x + lado * (w / 2 + 10 * s), yc + 70 * s); ctx.line_to(x + lado * 14 * s, yc + 70 * s)
                ctx.line_to(x + lado * 16 * s, yh + 70 * s); ctx.close_path(); pintar(ctx, (0.98, 0.98, 0.99), 5 * s)
            ctx.rectangle(x - w / 2 + 14 * s, yh + 95 * s, 30 * s, 24 * s); pintar(ctx, (0.98, 0.98, 0.99), 3 * s)
            linea(ctx, [(x - w / 2 + 22 * s, yh + 98 * s), (x - w / 2 + 22 * s, yh + 88 * s)], 4 * s, (0.2, 0.35, 0.8))
            # estetoscopio
            ctx.new_path(); ctx.move_to(x - 22 * s, yh + 6 * s)
            ctx.curve_to(x - 34 * s, yh + 70 * s, x + 30 * s, yh + 80 * s, x + 18 * s, yh + 120 * s)
            ctx.set_source_rgb(0.25, 0.27, 0.3); ctx.set_line_width(6 * s); ctx.stroke()
            linea(ctx, [(x + 22 * s, yh + 6 * s), (x + 10 * s, yh + 40 * s)], 6 * s, (0.25, 0.27, 0.3))
            circulo(ctx, x + 18 * s, yh + 128 * s, 9 * s, (0.75, 0.77, 0.8), 3 * s)
        elif r == "toga":
            ctx.move_to(x - w / 2, yh + 10 * s); ctx.line_to(x + w / 2, yh + 10 * s)
            ctx.line_to(x + w / 2 + 22 * s, yc + 85 * s); ctx.line_to(x - w / 2 - 22 * s, yc + 85 * s); ctx.close_path()
            pintar(ctx, (0.12, 0.12, 0.16), 5 * s)
            ctx.move_to(x - 28 * s, yh + 6 * s); ctx.line_to(x, yh + 50 * s); ctx.line_to(x + 28 * s, yh + 6 * s)
            ctx.close_path(); pintar(ctx, (0.85, 0.7, 0.2), 4 * s)
        elif r in ("traje", "reclutador"):
            col = (0.16, 0.18, 0.24) if r == "traje" else (0.22, 0.24, 0.3)
            redondo(ctx, x - w / 2, yh, w, h + 10 * s, 20 * s); pintar(ctx, col, 5 * s)
            ctx.move_to(x - 24 * s, yh + 2 * s); ctx.line_to(x, yh + 75 * s); ctx.line_to(x + 24 * s, yh + 2 * s)
            ctx.close_path(); pintar(ctx, BLANCO, 3 * s)
            ctx.move_to(x, yh + 14 * s); ctx.line_to(x - 8 * s, yh + 60 * s); ctx.line_to(x, yh + 72 * s)
            ctx.line_to(x + 8 * s, yh + 60 * s); ctx.close_path(); pintar(ctx, (0.55, 0.12, 0.18), 2 * s)
        elif r == "sicario":
            redondo(ctx, x - w / 2, yh, w, h, 22 * s); pintar(ctx, (0.25, 0.27, 0.22), 5 * s)
            redondo(ctx, x - w / 2 + 6 * s, yh + 30 * s, w - 12 * s, h - 40 * s, 14 * s); pintar(ctx, (0.38, 0.4, 0.3), 5 * s)
            for i in range(3):
                redondo(ctx, x - w / 2 + 12 * s + i * (w - 24 * s) / 3, yh + 105 * s, (w - 36 * s) / 3, 34 * s, 5 * s)
                pintar(ctx, (0.3, 0.32, 0.24), 3 * s)
            linea(ctx, [(x - w / 2 + 10 * s, yh + 40 * s), (x + w / 2 - 10 * s, yh + 40 * s)], 4 * s, (0.2, 0.2, 0.16))
        elif r == "jefe":
            redondo(ctx, x - w / 2 - 6 * s, yh, w + 12 * s, h, 26 * s); pintar(ctx, (0.78, 0.18, 0.2), 5 * s)
            rnd = random.Random(7)
            ctx.save(); redondo(ctx, x - w / 2 - 6 * s, yh, w + 12 * s, h, 26 * s); ctx.clip()
            for _ in range(26):
                ctx.new_path(); ctx.arc(x + rnd.uniform(-w / 2, w / 2), yh + rnd.uniform(0, h), 6 * s, 0, 2 * math.pi)
                ctx.set_source_rgb(*ORO); ctx.fill()
            ctx.restore()
            ctx.move_to(x - 26 * s, yh + 2 * s); ctx.line_to(x, yh + 40 * s); ctx.line_to(x + 26 * s, yh + 2 * s)
            ctx.close_path(); pintar(ctx, CARA, 3 * s)
            ctx.new_path(); ctx.arc(x, yh + 10 * s, 30 * s, math.radians(20), math.radians(160))
            ctx.set_source_rgb(*ORO); ctx.set_line_width(7 * s); ctx.stroke()
            ctx.rectangle(x - w / 2 - 6 * s, yc - 26 * s, w + 12 * s, 22 * s); pintar(ctx, (0.35, 0.22, 0.12), 4 * s)
            redondo(ctx, x - 22 * s, yc - 30 * s, 44 * s, 30 * s, 6 * s); pintar(ctx, ORO, 3 * s)
        elif r == "nina":
            ctx.move_to(x - w / 2, yh + 8 * s); ctx.line_to(x + w / 2, yh + 8 * s)
            ctx.line_to(x + w / 2 + 25 * s, yc + 40 * s); ctx.line_to(x - w / 2 - 25 * s, yc + 40 * s); ctx.close_path()
            pintar(ctx, self.color or (0.95, 0.55, 0.7), 5 * s)
        elif r == "mujer":
            col = self.color or (0.55, 0.42, 0.7)
            ctx.move_to(x - w / 2, yh + 8 * s); ctx.line_to(x + w / 2, yh + 8 * s)
            ctx.line_to(x + w / 2 + 25 * s, yc + 80 * s); ctx.line_to(x - w / 2 - 25 * s, yc + 80 * s); ctx.close_path()
            pintar(ctx, col, 5 * s)
        else:  # camisa
            col = self.color or (0.36, 0.55, 0.78)
            redondo(ctx, x - w / 2, yh, w, h, 22 * s); pintar(ctx, col, 5 * s)
            ctx.move_to(x - 22 * s, yh + 2 * s); ctx.line_to(x, yh + 26 * s); ctx.line_to(x + 22 * s, yh + 2 * s)
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(4 * s); ctx.stroke()
            for i in range(3): circulo(ctx, x, yh + 50 * s + i * 34 * s, 4 * s, claro(col, 0.5), 2 * s)
        if self.cadena and r != "jefe":
            ctx.new_path(); ctx.arc(x, yh + 10 * s, 30 * s, math.radians(20), math.radians(160))
            ctx.set_source_rgb(*ORO); ctx.set_line_width(7 * s); ctx.stroke()

    def _cara(self, ctx, cx, cy, R, s):
        c = self.cara; ox = self.mira * R * 0.3
        ey = cy - R * 0.06
        ctx.set_source_rgb(*TINTA)
        for lado in (-1, 1):
            ex = cx + ox + lado * R * 0.3
            if c in ("orgulloso", "dormido"):
                ctx.new_path(); ctx.arc(ex, ey + R * 0.05, R * 0.1, math.radians(200 if c == "orgulloso" else 20),
                                         math.radians(340 if c == "orgulloso" else 160))
                ctx.set_line_width(R * 0.06); ctx.stroke()
            elif c in ("sorpresa", "aterrado"):
                circulo(ctx, ex, ey, R * 0.13, BLANCO, R * 0.04)
                ctx.new_path(); ctx.arc(ex, ey, R * (0.035 if c == "aterrado" else 0.06), 0, 2 * math.pi)
                ctx.set_source_rgb(*TINTA); ctx.fill()
            else:
                ctx.new_path(); ctx.save(); ctx.translate(ex, ey); ctx.scale(0.85, 1.15)
                ctx.arc(0, 0, R * 0.075, 0, 2 * math.pi); ctx.restore(); ctx.set_source_rgb(*TINTA); ctx.fill()
            # cejas
            by = ey - R * 0.24; ctx.set_line_width(R * 0.06); ctx.new_path()
            if c in ("enojado", "malvado"):
                ctx.move_to(ex - lado * R * 0.14, by - R * 0.06); ctx.line_to(ex + lado * R * 0.13, by + R * 0.06)
            elif c in ("preocupado", "triste", "aterrado"):
                ctx.move_to(ex - lado * R * 0.13, by + R * 0.04); ctx.line_to(ex + lado * R * 0.12, by - R * 0.06)
            elif c == "sorpresa":
                ctx.arc(ex, by + R * 0.02, R * 0.13, math.radians(215), math.radians(325))
            elif c == "dudoso":
                yy = by - (R * 0.06 if lado == 1 else 0)
                ctx.move_to(ex - R * 0.12, yy); ctx.line_to(ex + R * 0.12, yy)
            elif c != "dormido":
                ctx.move_to(ex - R * 0.12, by); ctx.line_to(ex + R * 0.12, by)
            ctx.set_source_rgb(*TINTA); ctx.stroke()
        if self.lentes:
            for lado in (-1, 1):
                ctx.new_path(); ctx.arc(cx + ox + lado * R * 0.3, ey, R * 0.17, 0, 2 * math.pi)
                ctx.set_source_rgba(0.7, 0.85, 0.95, 0.35); ctx.fill_preserve()
                ctx.set_source_rgb(*TINTA); ctx.set_line_width(R * 0.04); ctx.stroke()
        # boca
        mx, my = cx + ox, cy + R * 0.38
        ctx.new_path(); ctx.set_line_width(R * 0.05); ctx.set_source_rgb(*TINTA)
        if c in ("feliz", "orgulloso"):
            ancho = 0.24 if c == "feliz" else 0.3
            ctx.move_to(mx - R * ancho, my - R * 0.06)
            ctx.curve_to(mx - R * ancho * 0.6, my + R * 0.2, mx + R * ancho * 0.6, my + R * 0.2, mx + R * ancho, my - R * 0.06)
            if c == "orgulloso":
                ctx.close_path(); pintar(ctx, (0.5, 0.1, 0.15), R * 0.04)
            else: ctx.stroke()
        elif c in ("sorpresa", "aterrado"):
            ctx.save(); ctx.translate(mx, my); ctx.scale(1, 1.3); ctx.arc(0, 0, R * 0.1, 0, 2 * math.pi); ctx.restore()
            pintar(ctx, (0.45, 0.08, 0.12), R * 0.04)
        elif c in ("triste",):
            ctx.arc(mx, my + R * 0.13, R * 0.14, math.radians(210), math.radians(330)); ctx.stroke()
        elif c == "preocupado":
            ctx.move_to(mx - R * 0.15, my); ctx.curve_to(mx - R * 0.05, my - R * 0.06, mx + R * 0.05, my + R * 0.06, mx + R * 0.15, my)
            ctx.stroke()
        elif c == "malvado":
            ctx.move_to(mx - R * 0.18, my - R * 0.02); ctx.curve_to(mx - R * 0.05, my + R * 0.08, mx + R * 0.12, my + R * 0.04, mx + R * 0.22, my - R * 0.1)
            ctx.stroke()
        elif c == "enojado":
            ctx.arc(mx, my + R * 0.1, R * 0.12, math.radians(215), math.radians(325)); ctx.stroke()
        else:
            ctx.move_to(mx - R * 0.12, my); ctx.line_to(mx + R * 0.12, my); ctx.stroke()
        if self.bigote:
            ctx.new_path(); ctx.save(); ctx.translate(mx, my); ctx.scale(1.35, 1.5); ctx.translate(-mx, -my); ctx.move_to(mx - R * 0.3, my - R * 0.02)
            ctx.curve_to(mx - R * 0.2, my - R * 0.2, mx - R * 0.02, my - R * 0.16, mx, my - R * 0.1)
            ctx.curve_to(mx + R * 0.02, my - R * 0.16, mx + R * 0.2, my - R * 0.2, mx + R * 0.3, my - R * 0.02)
            ctx.curve_to(mx + R * 0.15, my - R * 0.06, mx + R * 0.05, my - R * 0.04, mx, my - R * 0.05)
            ctx.curve_to(mx - R * 0.05, my - R * 0.04, mx - R * 0.15, my - R * 0.06, mx - R * 0.3, my - R * 0.02)
            ctx.close_path(); ctx.restore(); ctx.set_source_rgb(*TINTA); ctx.fill()
        if self.sudor:
            for (dx, dy, k) in ((0.62, -0.35, 1), (0.75, -0.05, 0.75), (-0.7, -0.25, 0.8)):
                gx, gy, gr = cx + dx * R, cy + dy * R, R * 0.07 * k
                ctx.new_path(); ctx.move_to(gx, gy - gr * 2.2)
                ctx.curve_to(gx + gr, gy - gr * 0.5, gx + gr, gy + gr, gx, gy + gr)
                ctx.curve_to(gx - gr, gy + gr, gx - gr, gy - gr * 0.5, gx, gy - gr * 2.2)
                pintar(ctx, (0.6, 0.85, 1.0), R * 0.025)

    def _pelo_atras(self, ctx, cx, cy, R):
        col = (0.35, 0.2, 0.12) if self.pelo == "largo" else (0.55, 0.32, 0.15)
        ctx.new_path(); redondo(ctx, cx - R * 1.08, cy - R * 0.6, R * 2.16, R * 1.75, R * 0.5)
        pintar(ctx, col, R * 0.06)
        if self.pelo == "coleta":
            ctx.new_path(); ctx.arc(cx + R * 1.05, cy - R * 0.45, R * 0.32, 0, 2 * math.pi); pintar(ctx, col, R * 0.06)

    def _pelo(self, ctx, cx, cy, R, s):
        p = self.pelo
        if p == "picos":
            pts = [(-1.02, 0.0), (-1.2, -0.35), (-0.9, -0.42), (-1.1, -0.8), (-0.6, -0.72), (-0.65, -1.2),
                   (-0.25, -0.95), (-0.05, -1.35), (0.2, -0.98), (0.55, -1.25), (0.55, -0.85), (1.0, -1.0),
                   (0.85, -0.55), (1.22, -0.45), (1.0, -0.12), (0.7, -0.5), (0.3, -0.62), (0.0, -0.45),
                   (-0.35, -0.62), (-0.7, -0.4)]
            ctx.new_path(); ctx.move_to(cx + pts[0][0] * R, cy + pts[0][1] * R)
            for (a, b) in pts[1:]: ctx.line_to(cx + a * R, cy + b * R)
            ctx.close_path(); pintar(ctx, (0.1, 0.1, 0.13), R * 0.04)
            linea(ctx, [(cx - 0.3 * R, cy - 0.85 * R), (cx + 0.1 * R, cy - 0.7 * R)], R * 0.03, (0.35, 0.35, 0.42))
        elif p == "castano":
            ctx.new_path(); ctx.move_to(cx - R * 0.98, cy - R * 0.1)
            ctx.curve_to(cx - R * 1.05, cy - R * 1.15, cx + R * 0.9, cy - R * 1.25, cx + R * 1.0, cy - R * 0.2)
            ctx.curve_to(cx + R * 0.6, cy - R * 0.7, cx - R * 0.1, cy - R * 0.62, cx - R * 0.55, cy - R * 0.5)
            ctx.curve_to(cx - R * 0.8, cy - R * 0.4, cx - R * 0.9, cy - R * 0.2, cx - R * 0.98, cy - R * 0.1)
            ctx.close_path(); pintar(ctx, (0.45, 0.28, 0.17), R * 0.04)
        elif p in ("largo", "coleta"):
            col = (0.35, 0.2, 0.12) if p == "largo" else (0.55, 0.32, 0.15)
            ctx.new_path(); ctx.arc(cx, cy, R * 1.02, math.radians(185), math.radians(355))
            ctx.curve_to(cx + R * 0.5, cy - R * 0.55, cx - R * 0.3, cy - R * 0.75, cx - R * 1.0, cy - R * 0.1)
            ctx.close_path(); pintar(ctx, col, R * 0.04)
        elif p == "rapado":
            ctx.save(); ctx.arc(cx, cy, R, 0, 2 * math.pi); ctx.clip()
            ctx.new_path(); ctx.arc(cx, cy - R * 0.25, R * 1.0, math.radians(180), math.radians(360))
            ctx.set_source_rgba(0.2, 0.2, 0.22, 0.35); ctx.fill(); ctx.restore()

    def _sombrero(self, ctx, cx, cy, R, s):
        h = self.sombrero
        top = cy - R
        if h == "vaquero":
            col = (0.6, 0.42, 0.24)
            ctx.new_path(); ctx.move_to(cx - R * 1.6, top + R * 0.3)
            ctx.curve_to(cx - R * 1.2, top + R * 0.55, cx + R * 1.2, top + R * 0.55, cx + R * 1.6, top + R * 0.3)
            ctx.curve_to(cx + R * 1.1, top + R * 0.15, cx - R * 1.1, top + R * 0.15, cx - R * 1.6, top + R * 0.3)
            ctx.close_path(); pintar(ctx, col, R * 0.05)
            ctx.new_path(); ctx.move_to(cx - R * 0.75, top + R * 0.28)
            ctx.curve_to(cx - R * 0.8, top - R * 0.55, cx - R * 0.1, top - R * 0.45, cx, top - R * 0.3)
            ctx.curve_to(cx + R * 0.1, top - R * 0.45, cx + R * 0.8, top - R * 0.55, cx + R * 0.75, top + R * 0.28)
            ctx.close_path(); pintar(ctx, col, R * 0.05)
            ctx.rectangle(cx - R * 0.75, top + R * 0.08, R * 1.5, R * 0.16); pintar(ctx, (0.3, 0.2, 0.12), R * 0.03)
        elif h == "birrete":
            ctx.new_path(); ctx.move_to(cx - R * 1.3, top + R * 0.05); ctx.line_to(cx, top - R * 0.35)
            ctx.line_to(cx + R * 1.3, top + R * 0.05); ctx.line_to(cx, top + R * 0.42); ctx.close_path()
            pintar(ctx, (0.12, 0.12, 0.16), R * 0.05)
            ctx.rectangle(cx - R * 0.6, top + R * 0.25, R * 1.2, R * 0.3); pintar(ctx, (0.12, 0.12, 0.16), R * 0.05)
            linea(ctx, [(cx, top + R * 0.02), (cx + R * 1.0, top + R * 0.15), (cx + R * 1.05, top + R * 0.75)], R * 0.04, ORO)
            circulo(ctx, cx + R * 1.05, top + R * 0.8, R * 0.08, ORO, R * 0.02)
        elif h == "gorra":
            ctx.new_path(); ctx.arc(cx, top + R * 0.45, R * 0.95, math.pi, 2 * math.pi); ctx.close_path()
            pintar(ctx, (0.3, 0.33, 0.25), R * 0.05)
            ctx.new_path(); ctx.save(); ctx.translate(cx + R * 0.7, top + R * 0.45); ctx.scale(1, 0.3)
            ctx.arc(0, 0, R * 0.6, 0, 2 * math.pi); ctx.restore(); pintar(ctx, (0.25, 0.28, 0.2), R * 0.05)


# ---------------------------------------------------------------- escenarios
def interior(ctx, pared=(0.86, 0.88, 0.9), suelo_y=880, piso=(0.78, 0.8, 0.83), ventana=None, zocalo=True, luz=True):
    g = cairo.LinearGradient(0, 0, 0, suelo_y)
    g.add_color_stop_rgb(0, *claro(pared, 0.15)); g.add_color_stop_rgb(1, *oscuro(pared, 0.93))
    ctx.rectangle(0, 0, W, suelo_y); ctx.set_source(g); ctx.fill()
    if ventana:
        vx, vy, vw, vh = ventana
        ctx.rectangle(vx, vy, vw, vh); pintar(ctx, (0.8, 0.88, 0.94), 7)
        for i in range(1, 4):
            linea(ctx, [(vx + vw * i / 4, vy), (vx + vw * i / 4, vy + vh)], 6, (0.55, 0.6, 0.66))
        linea(ctx, [(vx, vy + vh * 0.5), (vx + vw, vy + vh * 0.5)], 6, (0.55, 0.6, 0.66))
    if zocalo:
        ctx.rectangle(0, suelo_y - 120, W, 120); ctx.set_source_rgb(*oscuro(pared, 0.82)); ctx.fill()
        linea(ctx, [(0, suelo_y - 120), (W, suelo_y - 120)], 5, oscuro(pared, 0.6))
    g = cairo.LinearGradient(0, suelo_y, 0, H)
    g.add_color_stop_rgb(0, *piso); g.add_color_stop_rgb(1, *claro(piso, 0.25))
    ctx.rectangle(0, suelo_y, W, H - suelo_y); ctx.set_source(g); ctx.fill()
    linea(ctx, [(0, suelo_y), (W, suelo_y)], 5, oscuro(pared, 0.55))
    for i in range(-6, 8):
        ctx.move_to(W / 2 + i * 150, suelo_y); ctx.line_to(W / 2 + i * 480, H)
        ctx.set_source_rgba(0, 0, 0, 0.05); ctx.set_line_width(3); ctx.stroke()
    if luz:
        for (x0, a) in ((300, 0.10), (1150, 0.07)):
            ctx.move_to(x0, 0); ctx.line_to(x0 + 260, 0); ctx.line_to(x0 + 520, H); ctx.line_to(x0 + 120, H)
            ctx.close_path(); ctx.set_source_rgba(1, 1, 1, a); ctx.fill()


def exterior(ctx, suelo_y=820, cielo=(0.62, 0.8, 0.95), suelo=(0.82, 0.74, 0.58), noche=False):
    if noche: cielo = (0.12, 0.15, 0.28)
    g = cairo.LinearGradient(0, 0, 0, suelo_y)
    g.add_color_stop_rgb(0, *cielo); g.add_color_stop_rgb(1, *claro(cielo, 0.45 if not noche else 0.15))
    ctx.rectangle(0, 0, W, suelo_y); ctx.set_source(g); ctx.fill()
    if noche:
        rnd = random.Random(3)
        for _ in range(70):
            ctx.new_path(); ctx.arc(rnd.uniform(0, W), rnd.uniform(0, suelo_y * 0.7), rnd.uniform(1, 2.5), 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 0.8); ctx.fill()
        circulo(ctx, 1580, 180, 60, (0.95, 0.95, 0.85), 0)
    else:
        for (cx, cy, k) in ((380, 200, 1), (1400, 150, 0.8), (1000, 300, 0.6)):
            ctx.new_path()
            for (dx, dy, r) in ((0, 0, 60), (65, -25, 75), (140, 0, 58)):
                ctx.arc(cx + dx * k, cy + dy * k, r * k, 0, 2 * math.pi); ctx.close_path()
            ctx.set_source_rgba(1, 1, 1, 0.9); ctx.fill()
    ctx.new_path(); ctx.move_to(0, suelo_y)
    for x in range(0, W + 61, 60): ctx.line_to(x, suelo_y - 70 - 40 * math.sin(x / 300))
    ctx.line_to(W, suelo_y); ctx.close_path()
    pintar(ctx, (0.5, 0.6, 0.48) if not noche else (0.12, 0.16, 0.2), 0)
    ctx.rectangle(0, suelo_y, W, H - suelo_y)
    pintar(ctx, suelo if not noche else oscuro(suelo, 0.35), 0)
    linea(ctx, [(0, suelo_y), (W, suelo_y)], 4, oscuro(suelo, 0.6))


def liso(ctx, color=(0.9, 0.91, 0.93)):
    g = cairo.RadialGradient(W / 2, H / 2, 100, W / 2, H / 2, W * 0.7)
    g.add_color_stop_rgb(0, *claro(color, 0.3)); g.add_color_stop_rgb(1, *oscuro(color, 0.88))
    ctx.set_source(g); ctx.paint()


def oscurecer(ctx, foco=(W / 2, 520), radio=520, fuerza=0.78, bombilla=True):
    """Convierte la escena en «variante oscura»: todo en penumbra salvo un cono de luz."""
    fx, fy = foco
    g = cairo.RadialGradient(fx, fy, radio * 0.25, fx, fy, radio * 1.6)
    g.add_color_stop_rgba(0, 0.02, 0.03, 0.08, 0.05); g.add_color_stop_rgba(0.6, 0.02, 0.03, 0.08, fuerza * 0.8)
    g.add_color_stop_rgba(1, 0.02, 0.03, 0.08, fuerza)
    ctx.set_source(g); ctx.paint()
    if bombilla:
        ctx.move_to(fx - 40, 60); ctx.line_to(fx + 40, 60); ctx.line_to(fx + radio * 0.75, fy + radio * 0.75)
        ctx.line_to(fx - radio * 0.75, fy + radio * 0.75); ctx.close_path()
        ctx.set_source_rgba(1, 0.92, 0.7, 0.08); ctx.fill()
        linea(ctx, [(fx, 0), (fx, 50)], 4, (0.15, 0.15, 0.15))
        circulo(ctx, fx, 66, 18, (1, 0.93, 0.6), 3)


# ---------------------------------------------------------------- utilería
def burbuja(ctx, x, y, w, h, hacia=(None, None), contenido=None):
    """Burbuja de pensamiento centrada en (x,y). hacia = punto (cabeza) al que bajan las bolitas."""
    hx, hy = hacia
    if hx is not None:
        for k, r in ((0.3, 22), (0.55, 15), (0.78, 10)):
            circulo(ctx, x + (hx - x) * k + 0, y + h / 2 * (1 - k) + (hy - y) * k, r, BLANCO, 5)
    ctx.new_path()
    n = 12
    for i in range(n):
        a = 2 * math.pi * i / n
        ctx.arc(x + math.cos(a) * w / 2 * 0.92, y + math.sin(a) * h / 2 * 0.88, min(w, h) * 0.17, 0, 2 * math.pi)
        ctx.close_path()
    ctx.set_source_rgb(*TINTA); ctx.set_line_width(10); ctx.stroke_preserve(); ctx.set_source_rgb(*BLANCO); ctx.fill()
    ctx.save(); ctx.translate(x, y); ctx.scale(w / 2 * 0.95, h / 2 * 0.92); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    ctx.set_source_rgb(*BLANCO); ctx.fill()
    if contenido:
        ctx.save(); contenido(ctx); ctx.restore()


def billete(ctx, x, y, s=1.0, rot=0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(math.radians(rot)); ctx.scale(s, s)
    redondo(ctx, -60, -30, 120, 60, 6); pintar(ctx, VERDE_DINERO, 4)
    ctx.new_path(); ctx.arc(0, 0, 18, 0, 2 * math.pi); pintar(ctx, claro(VERDE_DINERO, 0.4), 3)
    texto(ctx, "$", 0, 1, 26, oscuro(VERDE_DINERO, 0.6))
    ctx.restore()


def fajo(ctx, x, y, s=1.0):
    for i in range(5):
        ctx.save(); ctx.translate(x, y - i * 12 * s); ctx.scale(s, s)
        redondo(ctx, -75, -22, 150, 34, 5); pintar(ctx, VERDE_DINERO if i % 2 == 0 else oscuro(VERDE_DINERO, 0.9), 4)
        ctx.restore()
    ctx.rectangle(x - 18 * s, y - 70 * s, 36 * s, 66 * s); pintar(ctx, (0.92, 0.88, 0.7), 3)


def maletin_dinero(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    # tapa abierta
    ctx.move_to(-230, -40); ctx.line_to(230, -40); ctx.line_to(200, -230); ctx.line_to(-200, -230); ctx.close_path()
    pintar(ctx, (0.35, 0.22, 0.14), 6)
    ctx.move_to(-205, -60); ctx.line_to(205, -60); ctx.line_to(182, -210); ctx.line_to(-182, -210); ctx.close_path()
    pintar(ctx, (0.25, 0.15, 0.1), 4)
    redondo(ctx, -240, -40, 480, 160, 14); pintar(ctx, (0.42, 0.27, 0.16), 6)
    for fila in range(2):
        for i in range(5):
            fajo(ctx, -170 + i * 85, -20 + fila * 70, 0.55)
    redondo(ctx, -50, 95, 100, 22, 6); pintar(ctx, ORO, 4)
    ctx.restore()
    # brillo
    for (dx, dy) in ((-260, -240), (250, -200), (0, -300)):
        estrella(ctx, x + dx * s, y + dy * s, 22 * s)


def estrella(ctx, x, y, r, color=(1, 0.95, 0.6)):
    ctx.new_path()
    for i in range(8):
        a = math.pi / 4 * i; rr = r if i % 2 == 0 else r * 0.35
        ctx.line_to(x + math.cos(a) * rr, y + math.sin(a) * rr)
    ctx.close_path(); pintar(ctx, color, 2)


def telefono(ctx, x, y, s=1.0, pantalla=None, rot=0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(math.radians(rot)); ctx.scale(s, s)
    redondo(ctx, -60, -110, 120, 220, 18); pintar(ctx, (0.15, 0.16, 0.2), 5)
    redondo(ctx, -50, -95, 100, 185, 10); pintar(ctx, (0.85, 0.92, 0.98), 0)
    if pantalla: pantalla(ctx)
    ctx.restore()


def diploma(ctx, x, y, s=1.0, txt="MÉDICO CIRUJANO", marco=True):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    if marco:
        ctx.rectangle(-170, -120, 340, 240); pintar(ctx, (0.55, 0.38, 0.2), 6)
    ctx.rectangle(-150, -100, 300, 200); pintar(ctx, (0.99, 0.97, 0.9), 4)
    texto(ctx, "TÍTULO", 0, -60, 30, (0.3, 0.3, 0.35))
    texto(ctx, txt, 0, -15, 30, TINTA)
    for i in range(2): linea(ctx, [(-100, 25 + i * 22), (100, 25 + i * 22)], 3, (0.75, 0.75, 0.75))
    circulo(ctx, 95, 70, 22, ROJO, 3)
    ctx.restore()


def libros(ctx, x, y, n=8, s=1.0, semilla=1):
    rnd = random.Random(semilla); yy = y
    cols = [(0.7, 0.2, 0.2), (0.2, 0.4, 0.7), (0.25, 0.55, 0.35), (0.85, 0.65, 0.2), (0.45, 0.3, 0.6)]
    for i in range(n):
        h = rnd.uniform(28, 40) * s; w = rnd.uniform(150, 200) * s; dx = rnd.uniform(-15, 15) * s
        redondo(ctx, x - w / 2 + dx, yy - h, w, h, 4 * s); pintar(ctx, cols[i % 5], 4 * s)
        linea(ctx, [(x - w / 2 + dx + 12 * s, yy - h / 2), (x + w / 2 + dx - 30 * s, yy - h / 2)], 2 * s, (1, 1, 1))
        yy -= h
    return yy


def escritorio(ctx, x, y, w=700, color=(0.55, 0.38, 0.24)):
    """y = altura de la superficie."""
    ctx.rectangle(x - w / 2, y, w, 28); pintar(ctx, claro(color, 0.1), 5)
    ctx.rectangle(x - w / 2 + 20, y + 28, w - 40, 210); pintar(ctx, color, 5)
    for lado in (-1, 1):
        redondo(ctx, x + lado * (w / 4) - 100, y + 60, 200, 70, 6); pintar(ctx, oscuro(color, 0.9), 4)
        redondo(ctx, x + lado * (w / 4) - 30, y + 88, 60, 14, 7); pintar(ctx, ORO, 3)


def mesa(ctx, x, y, w=500, color=(0.7, 0.72, 0.76)):
    ctx.rectangle(x - w / 2, y, w, 22); pintar(ctx, color, 5)
    for lado in (-1, 1): linea(ctx, [(x + lado * (w / 2 - 30), y + 22), (x + lado * (w / 2 - 30), y + 210)], 10)


def rifle(ctx, x, y, s=1.0, rot=-25):
    ctx.save(); ctx.translate(x, y); ctx.rotate(math.radians(rot)); ctx.scale(s, s)
    redondo(ctx, -110, -14, 220, 26, 6); pintar(ctx, (0.22, 0.22, 0.24), 4)
    ctx.rectangle(-150, -10, 50, 30); pintar(ctx, (0.4, 0.28, 0.18), 4)
    ctx.rectangle(-10, 10, 18, 40); pintar(ctx, (0.22, 0.22, 0.24), 4)
    ctx.rectangle(110, -6, 70, 10); pintar(ctx, (0.18, 0.18, 0.2), 3)
    ctx.restore()


def sicario(cara="serio", pose="rifle", **kw):
    return Monito("sicario", cara=cara, pose=pose, pelo=kw.pop("pelo", "rapado"), tatuajes=True, **kw)


def sicario_con_rifle(ctx, x, y, s=1.0, cara="serio", **kw):
    m = sicario(cara=cara, **kw).dibujar(ctx, x, y, s)
    mi, md = m.manos["i"], m.manos["d"]
    rifle(ctx, (mi[0] + md[0]) / 2, (mi[1] + md[1]) / 2, s * 0.9, -20)
    for mano in (mi, md): circulo(ctx, mano[0], mano[1], 17 * s, BLANCO, 4 * s)
    return m


def jefe(cara="serio", pose="parado"):
    return Monito("jefe", cara=cara, pose=pose, sombrero="vaquero", bigote=True, cadena=True)


def doctor(cara="neutral", pose="parado", **kw):
    return Monito("bata", cara=cara, pose=pose, pelo="picos", **kw)


def camioneta(ctx, x, y, s=1.0, color=(0.1, 0.1, 0.12), faros=False):
    """SUV vista de lado; y = suelo."""
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    redondo(ctx, -330, -230, 660, 170, 30); pintar(ctx, color, 6)
    ctx.move_to(-250, -230); ctx.line_to(-200, -360); ctx.line_to(200, -360); ctx.line_to(280, -230); ctx.close_path()
    pintar(ctx, color, 6)
    for (a, b) in ((-190, -20), (10, 190)):
        ctx.move_to(a, -240); ctx.line_to(a + 20, -340); ctx.line_to(b - 10, -340); ctx.line_to(b + 20, -240)
        ctx.close_path(); pintar(ctx, (0.25, 0.3, 0.38), 4)
    for wx in (-200, 210):
        circulo(ctx, wx, -60, 70, (0.12, 0.12, 0.14), 6); circulo(ctx, wx, -60, 34, (0.6, 0.62, 0.66), 4)
    if faros:
        ctx.move_to(330, -170); ctx.line_to(900, -320); ctx.line_to(900, 0); ctx.close_path()
        ctx.set_source_rgba(1, 0.95, 0.7, 0.25); ctx.fill()
        circulo(ctx, 320, -170, 18, (1, 0.97, 0.75), 3)
    ctx.restore()


def carrito(ctx, x, y, s=1.0, color=(0.75, 0.55, 0.3)):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    redondo(ctx, -230, -150, 460, 100, 30); pintar(ctx, color, 6)
    ctx.move_to(-140, -150); ctx.line_to(-90, -240); ctx.line_to(110, -240); ctx.line_to(160, -150); ctx.close_path()
    pintar(ctx, color, 6)
    ctx.move_to(-110, -155); ctx.line_to(-75, -225); ctx.line_to(95, -225); ctx.line_to(130, -155); ctx.close_path()
    pintar(ctx, (0.75, 0.85, 0.92), 4)
    for wx in (-140, 150):
        circulo(ctx, wx, -45, 48, (0.12, 0.12, 0.14), 6); circulo(ctx, wx, -45, 22, (0.7, 0.7, 0.72), 3)
    ctx.restore()


def mansion(ctx, x, y, s=1.0, noche=False):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    pared = (0.95, 0.9, 0.8) if not noche else (0.3, 0.3, 0.36)
    ctx.rectangle(-420, -330, 840, 330); pintar(ctx, pared, 6)
    ctx.move_to(-460, -330); ctx.line_to(0, -470); ctx.line_to(460, -330); ctx.close_path()
    pintar(ctx, (0.72, 0.35, 0.25) if not noche else (0.22, 0.14, 0.14), 6)
    for i in range(6):
        ctx.rectangle(-360 + i * 130, -290, 70, 100)
        pintar(ctx, (0.6, 0.78, 0.9) if not noche else (1, 0.85, 0.45), 4)
    for i in range(5): ctx.rectangle(-330 + i * 160, -170, 26, 170); pintar(ctx, BLANCO if not noche else (0.5, 0.5, 0.55), 4)
    ctx.rectangle(-60, -150, 120, 150); pintar(ctx, (0.45, 0.3, 0.2), 5)
    ctx.restore()


def palmera(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.move_to(-12, 0); ctx.curve_to(-20, -150, 10, -280, 20, -380); ctx.line_to(36, -380)
    ctx.curve_to(26, -280, 6, -150, 12, 0); ctx.close_path(); pintar(ctx, (0.6, 0.45, 0.3), 5)
    for a in (-160, -120, -60, -20, 20, 200):
        ctx.save(); ctx.translate(28, -380); ctx.rotate(math.radians(a))
        ctx.move_to(0, 0); ctx.curve_to(60, -40, 130, -20, 170, 30); ctx.curve_to(120, 0, 60, 10, 0, 0)
        pintar(ctx, (0.3, 0.6, 0.3), 4); ctx.restore()
    ctx.restore()


def reja(ctx, x0, x1, y, alto=260):
    for xx in range(int(x0), int(x1), 40):
        linea(ctx, [(xx, y), (xx, y - alto)], 10, (0.15, 0.15, 0.17))
        ctx.new_path(); ctx.move_to(xx - 10, y - alto); ctx.line_to(xx, y - alto - 28); ctx.line_to(xx + 10, y - alto)
        ctx.close_path(); pintar(ctx, (0.15, 0.15, 0.17), 0)
    for yy in (y - 30, y - alto + 20): linea(ctx, [(x0 - 10, yy), (x1, yy)], 10, (0.15, 0.15, 0.17))


def reloj(ctx, x, y, r=90, texto_c="24 H"):
    circulo(ctx, x, y, r, BLANCO, 8)
    for i in range(12):
        a = math.pi / 6 * i
        linea(ctx, [(x + math.cos(a) * r * 0.8, y + math.sin(a) * r * 0.8), (x + math.cos(a) * r * 0.92, y + math.sin(a) * r * 0.92)], 5)
    linea(ctx, [(x, y), (x, y - r * 0.6)], 7); linea(ctx, [(x, y), (x + r * 0.45, y + r * 0.1)], 7)
    texto(ctx, texto_c, x, y + r * 0.45, r * 0.3, ROJO)


def x_roja(ctx, x, y, w, h, grosor=34):
    for (a, b) in (((x - w / 2, y - h / 2), (x + w / 2, y + h / 2)), ((x + w / 2, y - h / 2), (x - w / 2, y + h / 2))):
        linea(ctx, [a, b], grosor + 10, TINTA); linea(ctx, [a, b], grosor, ROJO)


def edificio_hospital(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.rectangle(-300, -420, 600, 420); pintar(ctx, (0.93, 0.95, 0.97), 6)
    for f in range(4):
        for c in range(5):
            ctx.rectangle(-250 + c * 105, -380 + f * 85, 70, 55); pintar(ctx, (0.6, 0.78, 0.9), 3)
    ctx.rectangle(-70, -110, 140, 110); pintar(ctx, (0.6, 0.78, 0.9), 4)
    redondo(ctx, -170, -500, 340, 70, 10); pintar(ctx, ROJO, 5)
    texto(ctx, "HOSPITAL", 0, -465, 44, BLANCO)
    ctx.restore()


def cruz_medica(ctx, x, y, r=40, color=ROJO):
    ctx.rectangle(x - r * 0.3, y - r, r * 0.6, r * 2); ctx.rectangle(x - r, y - r * 0.3, r * 2, r * 0.6)
    ctx.set_source_rgb(*color); ctx.fill()


def botiquin(ctx, x, y, s=1.0):
    redondo(ctx, x - 90 * s, y - 70 * s, 180 * s, 70 * s, 10 * s); pintar(ctx, BLANCO, 4)
    cruz_medica(ctx, x, y - 35 * s, 22 * s)


def sobre(ctx, x, y, s=1.0, txt="RENUNCIA", rot=0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(math.radians(rot)); ctx.scale(s, s)
    ctx.rectangle(-130, -80, 260, 160); pintar(ctx, (0.98, 0.96, 0.9), 5)
    ctx.move_to(-130, -80); ctx.line_to(0, 10); ctx.line_to(130, -80); ctx.set_source_rgb(*TINTA)
    ctx.set_line_width(4); ctx.stroke()
    texto(ctx, txt, 0, 50, 34, TINTA)
    ctx.restore()


def carpeta(ctx, x, y, s=1.0, txt="SECRETOS"):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    for i in range(3, 0, -1):
        ctx.rectangle(-170 + i * 6, -110 - i * 8, 340, 220); pintar(ctx, (0.98, 0.98, 0.96), 3)
    redondo(ctx, -170, -140, 120, 40, 6); pintar(ctx, (0.85, 0.7, 0.4), 4)
    ctx.rectangle(-170, -110, 340, 220); pintar(ctx, (0.88, 0.74, 0.44), 5)
    texto(ctx, txt, 0, -10, 46, ROJO, rot=-6)
    ctx.restore()


def angel(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    for lado in (-1, 1):
        ctx.new_path(); ctx.save(); ctx.translate(lado * 45, -20); ctx.scale(1.2, 0.8)
        ctx.arc(0, 0, 35, 0, 2 * math.pi); ctx.restore(); pintar(ctx, BLANCO, 4)
    Monito("nina", cara="feliz", color=BLANCO).dibujar(ctx, 0, 110, 0.55)
    ctx.new_path(); ctx.save(); ctx.translate(0, -105); ctx.scale(1.4, 0.4); ctx.arc(0, 0, 22, 0, 2 * math.pi); ctx.restore()
    ctx.set_source_rgb(*ORO); ctx.set_line_width(6); ctx.stroke()
    ctx.restore()


def diablito(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    m = Monito("nina", cara="malvado", color=(0.85, 0.15, 0.15))
    m.dibujar(ctx, 0, 110, 0.55)
    cx, cy, R = m.cabeza
    for lado in (-1, 1):
        ctx.new_path(); ctx.move_to(cx + lado * R * 0.5, cy - R * 0.75); ctx.line_to(cx + lado * R * 0.75, cy - R * 1.45)
        ctx.line_to(cx + lado * R * 0.15, cy - R * 0.92); ctx.close_path(); pintar(ctx, ROJO, 3)
    linea(ctx, [(60, 40), (60, -80)], 6, (0.3, 0.3, 0.3))
    for dx in (-14, 0, 14): linea(ctx, [(60 + dx, -80), (60 + dx, -105)], 5, (0.3, 0.3, 0.3))
    linea(ctx, [(46, -80), (74, -80)], 5, (0.3, 0.3, 0.3))
    ctx.restore()


def camilla(ctx, x, y, s=1.0):
    """Camilla con un paciente acostado (y = altura de la camilla)."""
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.rectangle(-260, -10, 520, 30); pintar(ctx, (0.85, 0.87, 0.9), 5)
    ctx.restore()
    ctx.save(); ctx.translate(x, y - 10 * s); ctx.rotate(math.radians(-90))
    Monito("camisa", cara="dormido", color=(0.5, 0.52, 0.5)).dibujar(ctx, 0, 230 * s, s * 0.8)
    ctx.restore()
    ctx.save(); ctx.translate(x - 40 * s, y - 40 * s); ctx.scale(s, s)
    ctx.rectangle(-150, 0, 300, 34); pintar(ctx, (0.96, 0.96, 0.98), 4)
    ctx.restore()


def foto_rota(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.rectangle(-230, -170, 460, 340); pintar(ctx, (0.25, 0.2, 0.15), 8)
    ctx.rectangle(-200, -140, 400, 280); pintar(ctx, (0.85, 0.9, 0.95), 4)
    ctx.save(); ctx.rectangle(-200, -140, 400, 280); ctx.clip()
    Monito("toga", cara="orgulloso", pose="mostrar_d", pelo="picos", sombrero="birrete").dibujar(ctx, 0, 250, 0.62)
    ctx.restore()
    for (a, b) in (((40, -40), (200, -140)), ((40, -40), (-120, 140)), ((40, -40), (200, 60)), ((40, -40), (-200, -60)),
                   ((40, -40), (90, 140)), ((-60, 60), (-200, 100))):
        linea(ctx, [a, b], 4, (1, 1, 1)); linea(ctx, [a, b], 1.5, (0.4, 0.45, 0.5))
    ctx.restore()


def candado(ctx, x, y, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s)
    ctx.new_path(); ctx.arc(0, -60, 60, math.pi, 2 * math.pi)
    ctx.set_source_rgb(*TINTA); ctx.set_line_width(36); ctx.stroke()
    ctx.new_path(); ctx.arc(0, -60, 60, math.pi, 2 * math.pi); ctx.set_source_rgb(0.7, 0.72, 0.76); ctx.set_line_width(24); ctx.stroke()
    redondo(ctx, -95, -70, 190, 150, 18); pintar(ctx, ORO, 7)
    circulo(ctx, 0, -10, 16, TINTA, 0); ctx.rectangle(-7, -10, 14, 45); ctx.set_source_rgb(*TINTA); ctx.fill()
    ctx.restore()


def vs(ctx, x=W / 2, y=H / 2, tam=200):
    texto(ctx, "VS", x, y, tam, ROJO, borde=TINTA, peso="Black")
