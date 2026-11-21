"""Personaje estilo «boceto» (cuerpo con ropa, trazo a mano, papel con grano).

A diferencia del monigote de palitos de motor.py, este personaje tiene volumen y puede
verse desde CUALQUIER ángulo: cada parte vive en un pequeño espacio 3D (cilindros y un
elipsoide para la cabeza) y se proyecta a la pantalla según `giro`:

    giro =   0  vista frontal         giro =  90  perfil mirando a la derecha
    giro =  45  tres cuartos          giro = 135  tres cuartos trasera
    giro = 180  espalda               giro = -90  perfil mirando a la izquierda

Los detalles de la ropa (bolsillos, solapas, costuras) y de la cara se definen sobre la
superficie con (ángulo alrededor del cuerpo, altura), así que giran solos y se ocultan
cuando quedan del lado de atrás. El trazo «hierve» (cambia un poco) 8 veces por segundo
para parecer dibujado a mano.

Unidades del modelo: el personaje mide ~470 unidades de los pies a la coronilla; `escala`
las convierte a píxeles. Y negativa = hacia arriba desde el suelo.
"""
import math
import numpy as np
import cairo
from PIL import Image

TINTA = (0.10, 0.09, 0.08)

# ---------------------------------------------------------------- paletas
DOCTOR = dict(
    piel=(0.93, 0.91, 0.86), bata=(0.91, 0.90, 0.86), pijama=(0.47, 0.63, 0.65),
    gorro=(0.50, 0.66, 0.68), mascarilla=(0.62, 0.76, 0.78), pantalon=(0.17, 0.17, 0.17),
    zapato=(0.07, 0.07, 0.07), sombra=(0.30, 0.25, 0.20),
    con_gorro=True, con_mascarilla=True, con_bata=True,
)


# ---------------------------------------------------------------- trazo a mano
_TAB = {}
def _tabla(cubo):
    t = _TAB.get(cubo)
    if t is None:
        if len(_TAB) > 48: _TAB.clear()
        t = _TAB[cubo] = np.random.default_rng(cubo * 7919 + 13).uniform(-1, 1, (8192, 2))
    return t

def remuestrear(pts, paso, cerrado=False):
    """Puntos espaciados de forma pareja (para que el temblor se vea como trazo, no como ruido)."""
    if cerrado: pts = list(pts) + [pts[0]]
    out = [pts[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d = math.hypot(x1 - x0, y1 - y0); n = max(1, int(d / paso))
        for k in range(1, n + 1): out.append((x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n))
    return out[:-1] if cerrado else out

def camino(ctx, pts, cerrado=True):
    ctx.new_path(); ctx.move_to(*pts[0])
    for p in pts[1:]: ctx.line_to(*p)
    if cerrado: ctx.close_path()

def tinta(ctx, pts, t, semilla, s, ancho=3.2, cerrado=False, alfa=1.0, color=TINTA):
    """Línea dibujada a mano: una pasada firme y otra fina, cada una con su temblor."""
    if len(pts) < 2: return
    pts = remuestrear(pts, 6 * s, cerrado)
    tab = _tabla(int(t * 8))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for pasada, (w, amp, a) in enumerate(((ancho, 0.7, 1.0), (ancho * 0.4, 1.6, 0.55))):
        ctx.new_path()
        for i, (x, y) in enumerate(pts):
            dx, dy = tab[(semilla * 977 + i * 31 + pasada * 4099) % 8192]
            (ctx.move_to if i == 0 else ctx.line_to)(x + dx * amp * s, y + dy * amp * s)
        if cerrado: ctx.close_path()
        ctx.set_source_rgba(*color, a * alfa); ctx.set_line_width(w * s); ctx.stroke()

def sombrear(ctx, pts, s, fuerza=0.42, color=(0.30, 0.25, 0.20), rayado=True):
    """Sombra del lado derecho (la luz viene de arriba a la izquierda) + rayado a mano."""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    xl, xr, yt, yb = min(xs), max(xs), min(ys), max(ys)
    if xr - xl < 2: return
    ctx.save(); camino(ctx, pts); ctx.clip()
    g = cairo.LinearGradient(xl, 0, xr, 0)
    g.add_color_stop_rgba(0, *color, 0.0); g.add_color_stop_rgba(0.5, *color, 0.0)
    g.add_color_stop_rgba(1, *color, fuerza)
    ctx.set_source(g); ctx.paint()
    if rayado:
        ctx.push_group()
        ctx.set_source_rgba(*TINTA, 0.55); ctx.set_line_width(1.1 * s)
        paso = 6.5 * s; h = yb - yt
        x = xl - h
        while x < xr + h:
            ctx.move_to(x, yb); ctx.line_to(x + h * 0.6, yt); x += paso
        ctx.stroke()
        ctx.pop_group_to_source()
        m = cairo.LinearGradient(xl, 0, xr, 0)
        m.add_color_stop_rgba(0, 0, 0, 0, 0); m.add_color_stop_rgba(0.62, 0, 0, 0, 0)
        m.add_color_stop_rgba(1, 0, 0, 0, 0.8)
        ctx.mask(m)
    ctx.restore()

def forma(ctx, pts, relleno, t, semilla, s, sombra=True, ancho=3.2, fuerza=0.42, rayado=True):
    camino(ctx, pts); ctx.set_source_rgb(*relleno); ctx.fill()
    if sombra: sombrear(ctx, pts, s, fuerza, rayado=rayado)
    tinta(ctx, pts, t, semilla, s, ancho, cerrado=True)

def elipse_pts(cx, cy, rx, ry, n=48, a0=0.0, a1=2 * math.pi):
    return [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in np.linspace(a0, a1, n)]


# ---------------------------------------------------------------- geometría del cuerpo
# Bata: secciones (altura, radio ancho, radio profundidad)
TORSO = [(-336, 48, 29), (-318, 55, 32), (-280, 55, 33), (-200, 52, 34), (-110, 58, 38)]
CAB = dict(y=-410, rx=53, ry=60)        # cabeza (elipsoide)
HOMBRO = dict(x=52, y=-322)              # articulación del hombro
BRAZO, ANTEBRAZO, ANCHO_BRAZO = 92, 80, 25
CADERA = dict(x=17, y=-190)
MUSLO, CANILLA, ANCHO_PIERNA = 92, 80, 25

def _interp(tabla, y):
    if y <= tabla[0][0]: return tabla[0][1:]
    for (y0, *a), (y1, *b) in zip(tabla, tabla[1:]):
        if y <= y1:
            k = (y - y0) / (y1 - y0); return tuple(p + (q - p) * k for p, q in zip(a, b))
    return tabla[-1][1:]

def _norm(a):
    return (a + 180) % 360 - 180


class Personaje:
    """Un personaje con volumen.

    Parámetros de `dibujar` (todos se pueden animar cuadro a cuadro):
        x, suelo   posición en pantalla de los pies
        escala     píxeles por unidad del modelo (1.0 ≈ 470 px de alto)
        giro       grados (0 frente, 90 perfil derecho, 180 espalda)
        cara       'preocupado' | 'enojado' | 'neutral' | 'sorpresa' | 'feliz'
        mira       -1..1 mueve los ojos a izquierda/derecha
        paso       None = quieto; número = fase de caminata (radianes, crece al caminar)
        brazos     dict opcional: {'i': (adelante, afuera, codo), 'd': (...)} en grados
    """
    def __init__(self, estilo=DOCTOR, semilla=1):
        self.e, self.semilla = estilo, semilla

    # ---------- proyección
    def _p(self, X, Y, Z):
        c, sn = self._c, self._s
        return (self._x + (X * c + Z * sn) * self._k, self._suelo + (Y + self._bob) * self._k), -X * sn + Z * c

    def _sup(self, tipo, phi, Y, abultado=1.0, clamp=True, centro=None):
        """Punto sobre la superficie: tipo 'torso' o 'cabeza'. Devuelve (pantalla, visible).
        `centro`: ángulo de referencia de la pieza, para que la parte oculta se pliegue al borde correcto."""
        a = _norm(phi + self._giro) if centro is None else _norm(centro + self._giro) + (phi - centro)
        vis = math.cos(math.radians(a))
        if clamp and abs(a) > 90:          # oculto: se pliega sobre el borde de la silueta
            phi += (90 if a > 0 else -90) - a
        f = math.radians(phi)
        if tipo == "torso":
            rx, rz = _interp(TORSO, Y)
        else:
            dy = max(-0.985, min(0.985, (Y - CAB["y"]) / CAB["ry"]))
            rx = rz = CAB["rx"] * math.sqrt(1 - dy * dy)
        rx *= abultado; rz *= abultado
        return self._p(rx * math.sin(f), Y, rz * math.cos(f))[0], vis

    def _curva(self, tipo, ctrl, n=24, abultado=1.0):
        """Muestrea una curva definida por puntos (phi, Y) sobre la superficie."""
        out = []; cen = sum(p for p, _ in ctrl) / len(ctrl)
        for (p0, y0), (p1, y1) in zip(ctrl, ctrl[1:]):
            for k in range(n):
                u = k / n; out.append(self._sup(tipo, p0 + (p1 - p0) * u, y0 + (y1 - y0) * u, abultado, centro=cen))
        out.append(self._sup(tipo, *ctrl[-1], abultado, centro=cen))
        return out

    def _linea_sup(self, ctx, tipo, ctrl, semilla, ancho=2.6, alfa=1.0, abultado=1.0, color=TINTA):
        """Dibuja solo los tramos visibles de una línea sobre la superficie."""
        tramo = []
        for p, vis in self._curva(tipo, ctrl, abultado=abultado) + [((0, 0), -1)]:
            if vis > 0.03: tramo.append(p)
            else:
                if len(tramo) > 1: tinta(ctx, tramo, self._t, semilla, self._k, ancho, alfa=alfa, color=color)
                tramo = []; semilla += 1

    def _parche(self, ctx, tipo, ctrl, relleno, semilla, abultado=1.0, sombra=True, fuerza=0.35):
        """Zona rellena sobre la superficie (bolsillo, mascarilla...). La parte oculta se pliega al borde."""
        pts = self._curva(tipo, ctrl + [ctrl[0]], n=14, abultado=abultado)
        if max(v for _, v in pts) <= 0.03: return
        poly = [p for p, _ in pts]
        camino(ctx, poly); ctx.set_source_rgb(*relleno); ctx.fill()
        if sombra: sombrear(ctx, poly, self._k, fuerza, rayado=False)
        tramo = []
        for p, vis in pts + [((0, 0), -1)]:
            if vis > 0.03: tramo.append(p)
            else:
                if len(tramo) > 1: tinta(ctx, tramo, self._t, semilla, self._k, 2.8)
                tramo = []; semilla += 1

    # ---------- extremidades
    def _cadena(self, base, lado, l1, l2, adelante, afuera, codo):
        """Brazo o pierna en 3D: ángulos en grados. Devuelve 3 puntos 3D."""
        def dir_(p, o):
            p, o = math.radians(p), math.radians(o)
            return (lado * math.sin(o) * math.cos(p), math.cos(o) * math.cos(p), math.sin(p))
        d1 = dir_(adelante, afuera); d2 = dir_(adelante + codo, afuera * 0.6)
        m = tuple(b + l1 * d for b, d in zip(base, d1))
        f = tuple(b + l2 * d for b, d in zip(m, d2))
        return base, m, f

    def _capsula(self, ctx, pts3, ancho, color, semilla):
        pts = [self._p(*q)[0] for q in pts3]; k = self._k
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        camino(ctx, pts, False); ctx.set_source_rgb(*TINTA); ctx.set_line_width((ancho + 6.4) * k); ctx.stroke()
        camino(ctx, pts, False); ctx.set_source_rgb(*color); ctx.set_line_width(ancho * k); ctx.stroke()
        # sombra a la derecha de la manga
        sh = [(x + ancho * 0.27 * k, y) for x, y in pts]
        camino(ctx, sh, False); ctx.set_source_rgba(*self.e["sombra"], 0.28)
        ctx.set_line_width(ancho * 0.36 * k); ctx.stroke()
        # temblor del contorno: repasamos los bordes con tinta fina
        for lado in (-1, 1):
            borde = []
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                d = math.hypot(x1 - x0, y1 - y0) or 1
                nx, ny = -(y1 - y0) / d, (x1 - x0) / d
                o = (ancho / 2 + 3.2) * k * lado
                borde += [(x0 + nx * o, y0 + ny * o), (x1 + nx * o, y1 + ny * o)]
            tinta(ctx, borde, self._t, semilla + lado, k, 1.2, alfa=0.7)
        return pts

    def _mano(self, ctx, muñeca3, codo3, lado, semilla):
        k = self._k
        (mx, my), _ = self._p(*muñeca3); (cx_, cy_), _ = self._p(*codo3)
        ang = math.atan2(my - cy_, mx - cx_)
        hx, hy = mx + math.cos(ang) * 12 * k, my + math.sin(ang) * 12 * k
        # pulgar: hacia delante y hacia el cuerpo
        (tx, ty), _ = self._p(muñeca3[0] - lado * 6, muñeca3[1] + 8, muñeca3[2] + 9)
        pul = elipse_pts(tx, ty, 6 * k, 9 * k, 20)
        forma(ctx, pul, self.e["piel"], self._t, semilla + 3, k, sombra=False, ancho=2.6)
        ctx.save(); ctx.translate(hx, hy); ctx.rotate(ang - math.pi / 2)
        pts = [(x, y) for x, y in elipse_pts(0, 0, 11 * k, 16 * k, 28)]
        m = ctx.get_matrix(); ctx.restore()
        pts = [m.transform_point(x, y) for x, y in pts]
        forma(ctx, pts, self.e["piel"], self._t, semilla, k, fuerza=0.3, rayado=False, ancho=2.8)
        # dedos insinuados
        for d in (-4, 4):
            a = m.transform_point(d * k, 6 * k); b = m.transform_point(d * k, 14 * k)
            tinta(ctx, [a, b], self._t, semilla + 7 + d, k, 1.4, alfa=0.7)

    def _zapato(self, ctx, tobillo3, semilla):
        k = self._k
        pts = []
        for a in np.linspace(0, 2 * math.pi, 24):   # huella del zapato vista desde arriba
            X = tobillo3[0] + 14 * math.cos(a); Z = tobillo3[2] + 8 + 21 * math.sin(a)
            pts.append(self._p(X, 0, Z)[0][0])
        xl, xr = min(pts), max(pts); y0 = self._p(*tobillo3)[0][1] + 18 * k   # suela
        # punta del zapato hacia donde mira
        frente = 1 if self._s > 0.2 else (-1 if self._s < -0.2 else 0)
        alto = 20 * k
        sil = []
        for u in np.linspace(0, 1, 18):
            x = xl + (xr - xl) * u
            bump = math.sin(math.pi * u) ** 0.7
            if frente == 1: bump *= 1 - 0.45 * max(0, u - 0.5) * 2
            if frente == -1: bump *= 1 - 0.45 * max(0, 0.5 - u) * 2
            sil.append((x, y0 - alto * bump))
        sil += [(xr, y0), (xl, y0)]
        forma(ctx, sil, self.e["zapato"], self._t, semilla, k, sombra=False, ancho=2.8)
        tinta(ctx, [(xl + 3 * k, y0 - 3 * k), (xr - 3 * k, y0 - 3 * k)], self._t, semilla + 2, k, 1.2,
              alfa=0.5, color=(0.5, 0.5, 0.5))

    # ---------- partes grandes
    def _torso(self, ctx):
        k, c, sn = self._k, self._c, self._s
        der, izq = [], []
        for Y in np.linspace(TORSO[0][0], TORSO[-1][0], 14):
            rx, rz = _interp(TORSO, Y); hw = math.hypot(rx * c, rz * sn)
            der.append(self._p(0, Y, 0)[0][0] + hw * k)
            izq.append(self._p(0, Y, 0)[0][0] - hw * k)
        ys = [self._p(0, Y, 0)[0][1] for Y in np.linspace(TORSO[0][0], TORSO[-1][0], 14)]
        cx = self._p(0, 0, 0)[0][0]; hw0 = der[0] - cx
        top = [(cx - hw0 * 0.45, ys[0] - 10 * k), (cx + hw0 * 0.45, ys[0] - 10 * k)]
        hem = [self._sup("torso", a - self._giro, -110)[0] for a in np.linspace(90, -90, 12)]
        hem = [(x, y + 4 * k * math.cos(math.radians(a))) for (x, y), a in zip(hem, np.linspace(90, -90, 12))]
        pts = top + list(zip(der, ys)) + hem + list(zip(izq, ys))[::-1]
        forma(ctx, pts, self.e["bata"], self._t, self.semilla * 10 + 1, k)
        e = self.e; sd = self.semilla * 100
        # pijama en el escote y cuello en V
        self._parche(ctx, "torso", [(-23, -340), (23, -340), (12, -252), (-12, -252)], e["pijama"], sd + 1, fuerza=0.25)
        self._linea_sup(ctx, "torso", [(-13, -340), (0, -312), (13, -340)], sd + 5, 2.2)
        # solapas
        for lado in (-1, 1):
            self._linea_sup(ctx, "torso", [(lado * 23, -341), (lado * 40, -316), (lado * 30, -303), (lado * 12, -252)], sd + 10 + lado)
        # cierre de la bata y bolsillos
        self._linea_sup(ctx, "torso", [(2, -252), (2, -112)], sd + 20)
        for lado in (-1, 1):
            self._parche(ctx, "torso", [(lado * 24, -205), (lado * 52, -205), (lado * 52, -160), (lado * 24, -160)],
                         e["bata"], sd + 30 + lado * 3, sombra=False)
        self._parche(ctx, "torso", [(22, -298), (44, -298), (44, -272), (22, -272)], e["bata"], sd + 40, sombra=False)
        self._linea_sup(ctx, "torso", [(30, -308), (30, -292)], sd + 45, 4.0, abultado=1.02)   # bolígrafo
        # espalda: costura central, cuello y medio cinturón
        self._linea_sup(ctx, "torso", [(180, -330), (180, -112)], sd + 50, 2.0, alfa=0.8)
        self._linea_sup(ctx, "torso", [(112, -332), (180, -322), (248, -332)], sd + 55, 2.4)
        self._parche(ctx, "torso", [(156, -232), (204, -232), (204, -218), (156, -218)], e["bata"], sd + 60, sombra=False)
        # pliegues de la tela
        for ph, y0, y1 in ((62, -290, -200), (-66, -280, -190), (120, -270, -180), (-128, -300, -200), (14, -200, -130)):
            self._linea_sup(ctx, "torso", [(ph, y0), (ph + 4, y1)], sd + 70 + ph, 1.6, alfa=0.5)

    def _cabeza(self, ctx, cara, mira, parpadeo):
        k, e, t = self._k, self.e, self._t
        sd = self.semilla * 1000
        (cx, cy), _ = self._p(0, CAB["y"], 0)
        # cuello
        (nx, ny), _ = self._p(0, -345, 0)
        forma(ctx, elipse_pts(nx, ny, 15 * k, 12 * k, 20), e["piel"], t, sd + 1, k, sombra=False)
        lazo_atras = e["con_gorro"] and math.cos(math.radians(_norm(180 + self._giro))) <= 0.02
        if lazo_atras: self._lazo(ctx, sd)
        forma(ctx, elipse_pts(cx, cy, CAB["rx"] * k, CAB["ry"] * k, 56), e["piel"], t, sd + 2, k, fuerza=0.35)
        # ojos y cejas
        cejas = dict(preocupado=(-446, -435), enojado=(-432, -446), neutral=(-440, -440),
                     sorpresa=(-452, -450), feliz=(-444, -441))[cara]
        for lado in (-1, 1):
            ph = lado * 21 + mira * 9
            (ex, ey), vis = self._sup("cabeza", ph, -418, clamp=False)
            if vis > 0.15:
                ancho = (5.5 + (1.5 if cara == "sorpresa" else 0)) * k * (0.45 + 0.55 * vis)
                if parpadeo:
                    tinta(ctx, [(ex - ancho, ey), (ex + ancho, ey)], t, sd + 20 + lado, k, 2.4)
                else:
                    camino(ctx, elipse_pts(ex, ey, ancho, 9.5 * k * (1.15 if cara == "sorpresa" else 1), 20))
                    ctx.set_source_rgb(*TINTA); ctx.fill()
                    ctx.set_source_rgba(1, 1, 1, 0.9); ctx.arc(ex + 1.6 * k, ey - 3 * k, 1.8 * k, 0, 2 * math.pi); ctx.fill()
            self._linea_sup(ctx, "cabeza", [(lado * 9, cejas[0]), (lado * 33, cejas[1])], sd + 25 + lado, 2.6, abultado=1.0)
        if not e["con_mascarilla"]:
            boca = dict(preocupado=[(-12, -374), (0, -377), (12, -373)], enojado=[(-12, -372), (0, -376), (12, -372)],
                        neutral=[(-11, -375), (11, -375)], sorpresa=[(-5, -378), (5, -378)],
                        feliz=[(-14, -380), (0, -370), (14, -380)])[cara]
            self._linea_sup(ctx, "cabeza", boca, sd + 30, 2.8)
        else:
            self._mascarilla(ctx, sd)
        if e["con_gorro"]: self._gorro(ctx, sd)
        if e["con_gorro"] and not lazo_atras: self._lazo(ctx, sd)

    def _mascarilla(self, ctx, sd):
        e = self.e
        # tiras: cruzan por detrás de la cabeza
        for lado in (-1, 1):
            for (p0, y0, p1, y1) in ((78, -400, 205, -386), (70, -381, 200, -414)):
                ctrl = [(lado * p0, y0), (lado * (p0 + p1) / 2, (y0 + y1) / 2 - 4), (lado * p1, y1)]
                self._linea_sup(ctx, "cabeza", ctrl, sd + 40 + p0 + lado, 5.6, abultado=1.02)
                self._linea_sup(ctx, "cabeza", ctrl, sd + 44 + p0 + lado, 3.0, abultado=1.025, color=(0.95, 0.94, 0.9))
        ctrl = [(-78, -403), (-30, -404), (0, -407), (30, -404), (78, -403), (74, -380), (50, -362), (20, -354),
                (0, -353), (-20, -354), (-50, -362), (-74, -380)]
        self._parche(ctx, "cabeza", ctrl, e["mascarilla"], sd + 50, abultado=1.07, fuerza=0.3)
        for y in (-393, -381, -369):   # pliegues
            self._linea_sup(ctx, "cabeza", [(-62, y), (0, y - 1), (62, y)], sd + 60 + y, 1.5, alfa=0.55, abultado=1.075)

    def _gorro(self, ctx, sd):
        k, t, e = self._k, self._t, self.e
        (cx, cy), _ = self._p(0, CAB["y"] - 5, 0)
        rx, ry = CAB["rx"] * 1.08 * k, CAB["ry"] * 1.07 * k
        borde_y = lambda ph: -428 + 16 * (1 - math.cos(math.radians(ph))) / 2
        brim = []
        for a in np.linspace(-90, 90, 28):
            ph = a - self._giro
            brim.append(self._sup("cabeza", ph, borde_y(ph), abultado=1.08)[0])
        region = brim + [(cx + rx * 1.4, cy - ry * 2), (cx - rx * 1.4, cy - ry * 2)]
        elip = elipse_pts(cx, cy, rx, ry, 64)
        ctx.save(); camino(ctx, region); ctx.clip()
        camino(ctx, elip); ctx.set_source_rgb(*e["gorro"]); ctx.fill()
        sombrear(ctx, elip, k, 0.45)
        tinta(ctx, elip, t, sd + 70, k, 3.2, cerrado=True)
        ctx.restore()
        tinta(ctx, brim, t, sd + 72, k, 3.0)
        # arrugas del gorro
        for ctrl in ([(-40, -452), (-5, -462)], [(10, -446), (40, -455)], [(-20, -436), (25, -438)],
                     [(140, -450), (175, -440)], [(200, -455), (230, -445)]):
            self._linea_sup(ctx, "cabeza", ctrl, sd + 80 + ctrl[0][0], 1.5, alfa=0.55, abultado=1.09)

    def _lazo(self, ctx, sd):
        """Nudo del gorro en la nuca: sobresale de la silueta en perfil."""
        k, t, e = self._k, self._t, self.e
        ph = math.radians(180); r = CAB["rx"] * 1.1
        (x, y), _ = self._p(r * math.sin(ph), -420, r * math.cos(ph))
        afuera = -self._s  # hacia atrás en pantalla
        for dx, dy in ((-1, -0.5), (1, -0.5)):
            lx = x + (dx * 9 * abs(self._c) + afuera * 12) * k
            forma(ctx, elipse_pts(lx, y + dy * 10 * k, 9 * k, 6 * k, 18), e["gorro"], t, sd + 90 + dx, k, sombra=False, ancho=2.4)
        for dx in (-1, 1):
            tail = [(x, y), (x + (dx * 6 * abs(self._c) + afuera * 16) * k, y + 18 * k),
                    (x + (dx * 4 * abs(self._c) + afuera * 22) * k, y + 26 * k),
                    (x + (dx * 12 * abs(self._c) + afuera * 10) * k, y + 22 * k)]
            forma(ctx, tail, e["gorro"], t, sd + 95 + dx, k, sombra=False, ancho=2.2)
        forma(ctx, elipse_pts(x, y, 6 * k, 6 * k, 14), e["gorro"], t, sd + 99, k, sombra=False, ancho=2.4)

    # ---------- dibujar todo
    def dibujar(self, ctx, t, x, suelo, escala=1.0, giro=0.0, cara="preocupado", mira=0.0,
                paso=None, brazos=None, parpadeo=None):
        self._t, self._x, self._suelo, self._k, self._giro = t, x, suelo, escala, giro
        self._c, self._s = math.cos(math.radians(giro)), math.sin(math.radians(giro))
        self._bob = math.sin(t * 2.1 + self.semilla) * 1.2   # respiración
        if parpadeo is None: parpadeo = ((t + self.semilla * 0.83) % 3.3) < 0.11

        # piernas y brazos (lado +1 = izquierdo del personaje = derecha en vista frontal)
        piernas, ang_brazos = {}, {}
        for lado in (-1, 1):
            if paso is None: adel, codo = 0, 0
            else:
                adel = 24 * math.sin(paso) * lado
                codo = -38 * max(0, math.sin(paso * 1 + (0 if lado > 0 else math.pi) - 1.1))
            piernas[lado] = (adel, codo)
            b = (brazos or {}).get("i" if lado < 0 else "d")
            if b is None:
                b = (-20 * math.sin(paso) * lado if paso is not None else 2, 9, 8)
            ang_brazos[lado] = b
        # bajar el cuerpo para que el pie más bajo toque el suelo
        cad = {l: self._cadena((l * CADERA["x"], CADERA["y"], 0), l, MUSLO, CANILLA, -a, 0, c)
               for l, (a, c) in piernas.items()}
        self._bob += -18 - max(q[2][1] for q in cad.values())

        # sombra en el piso
        ctx.save(); ctx.translate(x, suelo); ctx.scale(95 * escala, 11 * escala)
        ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); ctx.set_source_rgba(0, 0, 0, 0.32); ctx.fill()

        def prof(X3):
            return self._p(*X3)[1]
        brazo3 = {l: self._cadena((l * HOMBRO["x"], HOMBRO["y"], 0), l, BRAZO, ANTEBRAZO, *ang_brazos[l])
                  for l in (-1, 1)}
        orden_brazos = sorted((-1, 1), key=lambda l: prof(brazo3[l][0]))
        atras = [l for l in orden_brazos if prof(brazo3[l][0]) < -3]
        delante = [l for l in orden_brazos if l not in atras]

        for l in atras: self._brazo(ctx, brazo3[l], l)
        for l in sorted((-1, 1), key=lambda l: prof(cad[l][0])):
            self._capsula(ctx, cad[l], ANCHO_PIERNA, self.e["pantalon"], self.semilla * 50 + l)
            self._zapato(ctx, cad[l][2], self.semilla * 60 + l)
        self._torso(ctx)
        for l in delante: self._brazo(ctx, brazo3[l], l)
        self._cabeza(ctx, cara, mira, parpadeo)

    def _brazo(self, ctx, b3, lado):
        self._capsula(ctx, b3, ANCHO_BRAZO, self.e["bata"], self.semilla * 70 + lado)
        # puño de la manga
        p, _ = self._p(*b3[2]); q, _ = self._p(*b3[1])
        d = math.hypot(p[0] - q[0], p[1] - q[1]) or 1
        nx, ny = -(p[1] - q[1]) / d, (p[0] - q[0]) / d
        cx, cy = p[0] - (p[0] - q[0]) / d * 10 * self._k, p[1] - (p[1] - q[1]) / d * 10 * self._k
        o = ANCHO_BRAZO / 2 * self._k
        tinta(ctx, [(cx - nx * o, cy - ny * o), (cx + nx * o, cy + ny * o)], self._t, self.semilla * 80 + lado, self._k, 1.8)
        self._mano(ctx, b3[2], b3[1], lado, self.semilla * 90 + lado)


# ---------------------------------------------------------------- fondo y acabado
def _ruido(w, h, celdas, rng):
    small = rng.random((max(2, h // celdas), max(2, w // celdas))).astype(np.float32)
    return np.asarray(Image.fromarray(small).resize((w, h), Image.BICUBIC), np.float32)

def fondo_grunge(w, h, semilla=3, base=(0.35, 0.30, 0.25), borde_oscuro=0.27):
    """Papel sucio sepia con una mancha oscura arriba y viñeta. Devuelve (h, w, 3) float32 0..1."""
    rng = np.random.default_rng(semilla)
    n = sum(_ruido(w, h, c, rng) * a for c, a in ((480, 0.5), (160, 0.3), (40, 0.15), (8, 0.05)))
    img = np.array(base, np.float32)[None, None, :] * (0.78 + 0.45 * n[..., None])
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    orilla = h * borde_oscuro + (_ruido(w, 1, 120, rng)[0] - 0.5) * h * 0.03 + (_ruido(w, h, 6, rng) - 0.5) * 8
    tope = np.clip((yy - orilla) / (h * 0.025), 0, 1)[..., None]
    negro = np.array((0.05, 0.045, 0.04), np.float32) * (0.7 + 0.6 * _ruido(w, h, 90, rng)[..., None])
    img = img * tope + negro * (1 - tope)
    r = np.hypot((xx - w / 2) / (w / 2), (yy - h * 0.55) / (h * 0.6))
    img *= (1 - 0.5 * np.clip(r - 0.35, 0, 1) ** 1.6)[..., None]
    for _ in range(40):   # rayones y motas
        x0, y0 = rng.integers(0, w), rng.integers(int(h * 0.3), h)
        img[max(0, y0 - 1):y0 + 1, x0:x0 + rng.integers(10, 60)] *= 1.12
    return np.clip(img, 0, 1)

class Grano:
    """Grano de papel/película que se multiplica sobre el cuadro final (3 variantes que alternan)."""
    def __init__(self, w, h, fuerza=0.09, semilla=5):
        rng = np.random.default_rng(semilla)
        papel = _ruido(w, h, 3, rng) * 0.5 + _ruido(w, h, 25, rng) * 0.5
        self.var = [(1 - fuerza + 2 * fuerza * (0.6 * papel + 0.4 * rng.random((h, w), np.float32)))[..., None]
                    for _ in range(3)]

    def aplicar(self, rgb, t):
        g = self.var[int(t * 8) % 3]
        return np.clip(rgb.astype(np.float32) * g, 0, 255).astype(np.uint8)


class Lienzo:
    """Superficie de cairo con fondo precalculado; devuelve cuadros RGB uint8."""
    def __init__(self, w, h, fondo=None, grano=True):
        self.w, self.h = w, h
        self.buf = np.zeros((h, w, 4), np.uint8)
        self.sup = cairo.ImageSurface.create_for_data(self.buf, cairo.FORMAT_RGB24, w, h)
        self.fondo = None
        if fondo is not None:
            f = (fondo * 255).astype(np.uint8)
            self.fondo = np.dstack([f[..., 2], f[..., 1], f[..., 0], np.full(f.shape[:2], 255, np.uint8)])
        self.grano = Grano(w, h) if grano else None

    def nuevo(self):
        if self.fondo is not None: np.copyto(self.buf, self.fondo)
        else: self.buf[:] = 255
        self.sup.mark_dirty()
        ctx = cairo.Context(self.sup); ctx.set_antialias(cairo.ANTIALIAS_BEST)
        return ctx

    def rgb(self, t):
        self.sup.flush()
        out = self.buf[:, :, [2, 1, 0]]
        return self.grano.aplicar(out, t) if self.grano else out.copy()
