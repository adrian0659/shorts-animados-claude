"""Escenarios caricatura «realistas y detallados» para el estilo POV.

Look: ilustración semi-realista con contorno de tinta, perspectiva de un punto, texturas (estuco, concreto,
madera, ladrillo, pasto), sombras suaves, luz de ventana, reflejos en pisos brillantes, mucha utilería.

Cada escenario es una función  f(c, hora="dia")  que pinta un lienzo vertical 1080x1920 (W, H de motor_pov).
hora: "dia", "tarde" o "noche". Úsalos como fondo de Escena:  Escena(t0, t1, lambda c: taller(c), ...)

Escenarios: taller, oficina, sala, calle, rancho, sierra, cocina, bodega.
Ver hoja de muestra: python3 escenarios.py  -> salida/escenarios_muestra.png
"""
import math, random
import numpy as np
import cairo
from motor_pov import *

# ================================================================== utilidades de render
_CACHE = {}


def ruido(w, h, escala=40, sem=1, octavas=4):
    """Ruido de valor suave 0..1 (numpy)."""
    clave = ("r", w, h, escala, sem, octavas)
    if clave in _CACHE: return _CACHE[clave]
    rng = np.random.default_rng(sem); out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octavas):
        s = max(2, escala / (2 ** o))
        gw, gh = int(w / s) + 2, int(h / s) + 2
        g = rng.random((gh, gw)).astype(np.float32)
        ys = np.linspace(0, gh - 1.001, h); xs = np.linspace(0, gw - 1.001, w)
        y0 = ys.astype(int); x0 = xs.astype(int); fy = (ys - y0)[:, None]; fx = (xs - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; cc = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
        out += amp * ((a * (1 - fx) + b * fx) * (1 - fy) + (cc * (1 - fx) + d * fx) * fy); tot += amp; amp *= 0.5
    out /= tot; _CACHE[clave] = out; return out


def _superficie(rgba):
    """numpy HxWx4 float (rgb + alfa, sin premultiplicar) -> cairo ImageSurface ARGB32."""
    h, w, _ = rgba.shape
    a = np.clip(rgba[..., 3], 0, 1)
    buf = np.empty((h, w, 4), np.uint8)
    buf[..., 0] = np.clip(rgba[..., 2] * a * 255, 0, 255); buf[..., 1] = np.clip(rgba[..., 1] * a * 255, 0, 255)
    buf[..., 2] = np.clip(rgba[..., 0] * a * 255, 0, 255); buf[..., 3] = a * 255
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    st = s.get_stride()
    np.ndarray((h, st), np.uint8, s.get_data())[:, :w * 4] = buf.reshape(h, w * 4)
    s.mark_dirty()
    return s


def textura(c, camino, tipo="estuco", fuerza=0.18, escala=None, sem=1, color_oscuro=(0, 0, 0), color_claro=(1, 1, 1)):
    """Aplica una textura dentro del camino `camino(c)` (función que traza el contorno)."""
    clave = ("t", tipo, fuerza, escala, sem, color_oscuro, color_claro)
    if clave not in _CACHE:
        if tipo == "estuco":
            n = ruido(W, H, escala or 6, sem, 3) * 0.6 + ruido(W, H, 60, sem + 1, 3) * 0.4
        elif tipo == "concreto":
            n = ruido(W, H, escala or 3, sem, 2) * 0.5 + ruido(W, H, 120, sem + 1, 4) * 0.5
        elif tipo == "madera":
            yy = np.arange(H)[:, None] / (escala or 9.0)
            n = 0.5 + 0.5 * np.sin(yy + ruido(W, H, 80, sem, 3) * 9) * 0.6 + (ruido(W, H, 4, sem + 2, 1) - 0.5) * 0.4
        elif tipo == "pasto":
            n = ruido(W, H, escala or 2, sem, 2) * 0.7 + ruido(W, H, 50, sem + 1, 3) * 0.3
        else:  # suave
            n = ruido(W, H, escala or 90, sem, 4)
        n = (n - n.mean()) / (n.std() + 1e-6)
        rgba = np.zeros((H, W, 4), np.float32)
        osc_ = n < 0
        for i in range(3):
            rgba[..., i] = np.where(osc_, color_oscuro[i], color_claro[i])
        rgba[..., 3] = np.clip(np.abs(n) * fuerza * 0.11, 0, 0.25)
        _CACHE[clave] = _superficie(rgba)
    c.save(); camino(c); c.clip(); c.set_source_surface(_CACHE[clave], 0, 0); c.paint(); c.restore()


def sombra_suave(c, forma, desenfoque=18, alfa=0.35, dx=0, dy=0, color=(0, 0, 0)):
    """Sombra difusa de una forma: forma(c) traza el camino."""
    from PIL import Image, ImageFilter
    k = 4
    s = cairo.ImageSurface(cairo.FORMAT_A8, W // k, H // k); cc = cairo.Context(s)
    cc.scale(1 / k, 1 / k); cc.translate(dx, dy); forma(cc); cc.set_source_rgba(0, 0, 0, 1); cc.fill()
    s.flush()
    a = np.ndarray((H // k, s.get_stride()), np.uint8, s.get_data())[:, :W // k].copy()
    a = np.asarray(Image.fromarray(a).filter(ImageFilter.GaussianBlur(desenfoque / k)), np.float32) / 255
    rgba = np.zeros((H // k, W // k, 4), np.float32); rgba[..., :3] = color; rgba[..., 3] = a * alfa
    sup = _superficie(rgba)
    c.save(); c.scale(k, k); c.set_source_surface(sup, 0, 0); c.get_source().set_filter(cairo.FILTER_BILINEAR); c.paint(); c.restore()


def oclusion(c, pts, ancho=60, alfa=0.25):
    """Oscurece suavemente a lo largo de una esquina (línea pts)."""
    def forma(cc):
        cc.move_to(*pts[0])
        for p in pts[1:]: cc.line_to(*p)
        cc.set_line_width(ancho); cc.stroke_preserve() if False else None
        cc.new_path()
        for (a, b) in zip(pts, pts[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) + 1e-6
            nx, ny = -dy / L * ancho / 2, dx / L * ancho / 2
            cc.move_to(a[0] + nx, a[1] + ny); cc.line_to(b[0] + nx, b[1] + ny); cc.line_to(b[0] - nx, b[1] - ny)
            cc.line_to(a[0] - nx, a[1] - ny); cc.close_path()
    sombra_suave(c, forma, ancho * 0.8, alfa)


def haz_luz(c, pts, alfa=0.35, color=(1, 0.97, 0.85), largo=None):
    """Haz de luz (polígono) con degradado desde el primer borde."""
    c.save(); c.move_to(*pts[0])
    for p in pts[1:]: c.line_to(*p)
    c.close_path()
    x0 = (pts[0][0] + pts[1][0]) / 2; y0 = (pts[0][1] + pts[1][1]) / 2
    x1 = (pts[2][0] + pts[3][0]) / 2; y1 = (pts[2][1] + pts[3][1]) / 2
    g = cairo.LinearGradient(x0, y0, x1, y1)
    g.add_color_stop_rgba(0, *color, alfa); g.add_color_stop_rgba(1, *color, 0)
    c.set_source(g); c.set_operator(cairo.OPERATOR_SCREEN); c.fill(); c.restore()


def reflejo_piso(c, y_piso, alto=420, alfa=0.22, desenfoque=6):
    """Refleja lo que está arriba de y_piso sobre el piso (piso brillante)."""
    from PIL import Image, ImageFilter
    tgt = c.get_target(); tgt.flush()
    arr = np.ndarray((H, W, 4), np.uint8, tgt.get_data())
    y0 = max(0, int(y_piso) - alto)
    trozo = arr[y0:int(y_piso), :, :3][::-1].copy()
    im = Image.fromarray(trozo[:, :, ::-1]).filter(ImageFilter.GaussianBlur(desenfoque))
    t = np.asarray(im, np.float32) / 255
    h = t.shape[0]
    rgba = np.zeros((H, W, 4), np.float32)
    rgba[int(y_piso):int(y_piso) + h, :, :3] = t[:H - int(y_piso)]
    fade = np.linspace(alfa, 0, h)[:, None]
    rgba[int(y_piso):int(y_piso) + h, :, 3] = fade[:H - int(y_piso)]
    sup = _superficie(rgba); c.save(); c.set_source_surface(sup, 0, 0); c.paint(); c.restore()


def poli(c, pts):
    c.move_to(*pts[0])
    for p in pts[1:]: c.line_to(*p)
    c.close_path()


def poli_f(pts): return lambda cc: poli(cc, pts)


# ================================================================== cuarto en perspectiva (un punto)
class Cuarto:
    """Habitación en perspectiva de un punto para lienzo vertical.

    Pared del fondo: rectángulo (x0,y0)-(x1,y1); y1 = línea del piso al fondo. vp = punto de fuga.
    u = profundidad (0 = orilla del cuadro, 1 = pared del fondo), v = altura (0 = piso, 1 = techo).
    """

    def __init__(self, x0=210, y0=520, x1=870, y1=1260, vp=(540, 1000)):
        self.x0, self.y0, self.x1, self.y1, self.vp = x0, y0, x1, y1, vp
        self.izq = [self._borde(x0, y0, 0), (x0, y0), (x0, y1), self._borde(x0, y1, 0)]
        self.der = [self._borde(x1, y0, W), (x1, y0), (x1, y1), self._borde(x1, y1, W)]

    def _borde(self, x, y, xb):
        vx, vy = self.vp; k = (xb - vx) / (x - vx); return (xb, vy + (y - vy) * k)

    def pared(self, lado, u, v):
        q = self.izq if lado == "izq" else self.der
        top = (lerp(q[0][0], q[1][0], u), lerp(q[0][1], q[1][1], u))
        bot = (lerp(q[3][0], q[2][0], u), lerp(q[3][1], q[2][1], u))
        return (lerp(bot[0], top[0], v), lerp(bot[1], top[1], v))

    def quad(self, lado, u0, u1, v0, v1):
        return [self.pared(lado, u0, v1), self.pared(lado, u1, v1), self.pared(lado, u1, v0), self.pared(lado, u0, v0)]

    def piso_y(self, u):
        """altura en pantalla de la línea pared-piso a profundidad u (sobre la pared izquierda)."""
        return self.pared("izq", u, 0)[1]

    def fondo(self, v):
        return lerp(self.y1, self.y0, v)

    def pintar(self, c, pared=(0.9, 0.9, 0.9), lateral=None, piso=(0.75, 0.75, 0.78), techo=(0.95, 0.95, 0.95),
               tex_pared="estuco", tex_piso="concreto", franja=None, zocalo=None, brillo_piso=True):
        lateral = lateral or osc(pared, 0.93)
        vx, vy = self.vp
        # techo
        poli(c, [(0, 0), (W, 0), self.der[0], (self.x1, self.y0), (self.x0, self.y0), self.izq[0]])
        c.set_source(degradado(0, self.y0, osc(techo, 0.8), techo)); c.fill()
        # piso
        poli(c, [self.izq[3], (self.x0, self.y1), (self.x1, self.y1), self.der[3], (W, H), (0, H)])
        g = degradado(self.y1, H, osc(piso, 0.85), osc(piso, 1.1)); c.set_source(g); c.fill()
        piso_f = poli_f([self.izq[3], (self.x0, self.y1), (self.x1, self.y1), self.der[3], (W, H), (0, H)])
        if tex_piso == "madera":
            self.tablones(c, piso)
        else:
            textura(c, piso_f, tex_piso, 0.35, sem=4)
        # paredes laterales
        for q, lado in ((self.izq, -1), (self.der, 1)):
            poli(c, q); g = cairo.LinearGradient(q[0][0], 0, q[1][0], 0)
            g.add_color_stop_rgb(0, *osc(lateral, 0.9)); g.add_color_stop_rgb(1, *osc(lateral, 1.03)); c.set_source(g); c.fill()
            textura(c, poli_f(q), tex_pared, 0.3, sem=2)
        # pared del fondo
        c.rectangle(self.x0, self.y0, self.x1 - self.x0, self.y1 - self.y0)
        c.set_source(degradado(self.y0, self.y1, osc(pared, 1.04), osc(pared, 0.94))); c.fill()
        textura(c, lambda cc: cc.rectangle(self.x0, self.y0, self.x1 - self.x0, self.y1 - self.y0), tex_pared, 0.3, sem=3)
        if franja:
            col, v0, v1 = franja
            c.rectangle(self.x0, self.fondo(v1), self.x1 - self.x0, self.fondo(v0) - self.fondo(v1)); c.set_source_rgb(*col); c.fill()
            for lado in ("izq", "der"):
                poli(c, self.quad(lado, 0, 1, v0, v1)); c.set_source_rgb(*osc(col, 0.9)); c.fill()
        if zocalo:
            for lado in ("izq", "der"):
                poli(c, self.quad(lado, 0, 1, 0, 0.035)); c.set_source_rgb(*osc(zocalo, 0.9)); c.fill()
            c.rectangle(self.x0, self.y1 - (self.y1 - self.y0) * 0.035, self.x1 - self.x0, (self.y1 - self.y0) * 0.035)
            c.set_source_rgb(*zocalo); c.fill()
        # oclusión en esquinas
        for pts in ([(self.x0, self.y0), (self.x0, self.y1)], [(self.x1, self.y0), (self.x1, self.y1)],
                    [self.izq[3], (self.x0, self.y1), (self.x1, self.y1), self.der[3]],
                    [self.izq[0], (self.x0, self.y0), (self.x1, self.y0), self.der[0]]):
            oclusion(c, pts, 70, 0.22)
        # líneas de tinta
        for a, b in [((self.x0, self.y0), (self.x1, self.y0)), ((self.x1, self.y0), (self.x1, self.y1)),
                     ((self.x1, self.y1), (self.x0, self.y1)), ((self.x0, self.y1), (self.x0, self.y0)),
                     (self.izq[0], (self.x0, self.y0)), (self.izq[3], (self.x0, self.y1)),
                     (self.der[0], (self.x1, self.y0)), (self.der[3], (self.x1, self.y1))]:
            linea(c, [a, b], 4.5, TINTA, 0.85)

    def tablones(self, c, color):
        """Piso de duela: tablas que fugan al punto de fuga, con juntas escalonadas y veta suave."""
        vx, vy = self.vp
        c.save(); poli(c, [self.izq[3], (self.x0, self.y1), (self.x1, self.y1), self.der[3], (W, H), (0, H)]); c.clip()
        r = random.Random(9)
        n = 16
        xs = [lerp(self.x0, self.x1, k / n) for k in range(n + 1)]
        def en_y(x_fondo, y):  # x en la altura y de la línea que va del punto de fuga a (x_fondo, y1)
            return vx + (x_fondo - vx) * (y - vy) / (self.y1 - vy)
        extra = 14
        xs = [lerp(self.x0, self.x1, k / n) for k in range(-extra, n + extra + 1)]
        for k in range(len(xs) - 1):
            a, b = xs[k], xs[k + 1]
            tono = osc(color, r.uniform(0.9, 1.08))
            poli(c, [(a, self.y1), (b, self.y1), (en_y(b, H), H), (en_y(a, H), H)])
            c.set_source(degradado(self.y1, H, osc(tono, 0.88), osc(tono, 1.08))); c.fill()
            linea(c, [(a, self.y1), (en_y(a, H), H)], 2, TINTA, 0.35)
            # juntas
            y = self.y1 + r.uniform(10, 60)
            while y < H:
                linea(c, [(en_y(a, y), y), (en_y(b, y), y)], 1.6, TINTA, 0.35)
                y += (y - vy) * r.uniform(0.5, 0.9)
        c.restore()
        textura(c, poli_f([self.izq[3], (self.x0, self.y1), (self.x1, self.y1), self.der[3], (W, H), (0, H)]), "suave", 0.25, sem=4)

    def lampara_techo(self, c, u, x_rel=0.5, largo=0.32, prendida=True):
        """Lámpara fluorescente en el techo a profundidad u (0 cerca, 1 fondo)."""
        y = lerp(self.izq[0][1] * 0.25, self.y0 - 12, u)
        x0 = lerp(0, self.x0, u); x1 = lerp(W, self.x1, u)
        cx = lerp(x0, x1, x_rel); w = (x1 - x0) * largo; h = lerp(30, 12, u)
        if prendida:
            g = cairo.RadialGradient(cx, y, 5, cx, y, w * 0.9)
            g.add_color_stop_rgba(0, 1, 1, 0.95, 0.35); g.add_color_stop_rgba(1, 1, 1, 0.95, 0)
            c.set_source(g); c.arc(cx, y, w * 0.9, 0, 7); c.fill()
        rrect(c, cx - w / 2, y - h / 2, w, h, h / 2); relleno(c, (1, 1, 0.97) if prendida else (0.7, 0.7, 0.7), 3)


# ================================================================== utilería detallada
def cartel(c, x, y, w, h, titulo, dibujo=None, fondo_=(0.18, 0.2, 0.28), texto_col=(1, 1, 1)):
    sombra_suave(c, lambda cc: cc.rectangle(x, y, w, h), 10, 0.3, 6, 8)
    c.rectangle(x, y, w, h); relleno(c, degradado(y, y + h, osc(fondo_, 1.2), fondo_), 3.5)
    texto(c, titulo, x + w / 2, y + h * 0.15, w * 0.13, texto_col, "Inter", peso=cairo.FONT_WEIGHT_BOLD)
    if dibujo:
        c.save(); c.rectangle(x + 8, y + h * 0.3, w - 16, h * 0.62); c.clip(); dibujo(c, x + 8, y + h * 0.3, w - 16, h * 0.62); c.restore()


def herramientas_tablero(c, x, y, w, h):
    c.rectangle(x, y, w, h); relleno(c, (0.62, 0.64, 0.68), 4)
    for i in range(int(w / 22)):
        for j in range(int(h / 22)):
            c.arc(x + 11 + i * 22, y + 11 + j * 22, 2.2, 0, 7)
    c.set_source_rgba(0, 0, 0, 0.35); c.fill()
    r = random.Random(4)
    xx = x + 20
    while xx < x + w - 30:
        tipo = r.choice(["llave", "desarmador", "martillo", "pinza"])
        yy = y + 30 + r.uniform(0, 20)
        if tipo == "llave":
            L = r.uniform(70, 120)
            linea(c, [(xx, yy), (xx, yy + L)], 9, (0.75, 0.77, 0.8)); linea(c, [(xx, yy), (xx, yy + L)], 2, TINTA, 0.6)
            c.arc(xx, yy, 11, 0, 7); relleno(c, (0.75, 0.77, 0.8), 2.5)
        elif tipo == "desarmador":
            rrect(c, xx - 7, yy, 14, 45, 5); relleno(c, r.choice([ROJO_, (0.95, 0.75, 0.1), (0.2, 0.4, 0.8)]), 2.5)
            linea(c, [(xx, yy + 45), (xx, yy + 100)], 4, (0.6, 0.6, 0.65))
        elif tipo == "martillo":
            linea(c, [(xx, yy + 15), (xx, yy + 110)], 9, (0.55, 0.38, 0.22)); c.rectangle(xx - 22, yy, 44, 18); relleno(c, (0.35, 0.36, 0.4), 2.5)
        else:
            linea(c, [(xx - 6, yy), (xx - 10, yy + 90)], 7, ROJO_); linea(c, [(xx + 6, yy), (xx + 10, yy + 90)], 7, ROJO_)
        xx += r.uniform(34, 52)
    yy = y + h * 0.62
    for k in range(int(w / 70)):
        cx = x + 35 + k * 70
        c.arc(cx, yy, 18, 0, 7); relleno(c, (0.3, 0.3, 0.33), 2.5); c.arc(cx, yy, 8, 0, 7); relleno(c, (0.55, 0.55, 0.6), 2)


ROJO_ = (0.82, 0.12, 0.12)


def gabinete_rojo(c, x, y, w, h):
    """Gabinete de herramientas rojo con cajones (y = base)."""
    sombra_suave(c, lambda cc: cc.rectangle(x + 10, y - 20, w, 40), 20, 0.35)
    c.rectangle(x, y - h, w, h); relleno(c, degradado(0, 0, (0.95, 0.2, 0.2), (0.6, 0.06, 0.06), x, x + w), 4.5)
    n = 6
    for i in range(n):
        yy = y - h + 18 + i * (h - 50) / n
        rrect(c, x + 12, yy, w - 24, (h - 50) / n - 10, 4); relleno(c, degradado(yy, yy + 50, (0.92, 0.18, 0.18), (0.7, 0.08, 0.08)), 3)
        linea(c, [(x + w * 0.3, yy + 14), (x + w * 0.7, yy + 14)], 7, (0.85, 0.85, 0.88)); linea(c, [(x + w * 0.3, yy + 14), (x + w * 0.7, yy + 14)], 2, TINTA, 0.5)
    for wx in (x + 20, x + w - 20):
        c.arc(wx, y + 6, 14, 0, 7); relleno(c, (0.15, 0.15, 0.15), 3)
    c.set_source_rgba(1, 1, 1, 0.18); c.rectangle(x + 8, y - h + 6, 10, h - 20); c.fill()


def estante(c, x, y, w, h, niveles=4, sem=3, colores=None):
    r = random.Random(sem)
    colores = colores or [(0.75, 0.6, 0.4), (0.3, 0.45, 0.7), (0.85, 0.3, 0.2), (0.95, 0.8, 0.3), (0.4, 0.6, 0.4), (0.9, 0.9, 0.9)]
    for lx in (x, x + w - 12): c.rectangle(lx, y - h, 12, h); relleno(c, (0.45, 0.47, 0.52), 3)
    for i in range(niveles):
        yy = y - i * h / niveles - 8
        c.rectangle(x, yy - 10, w, 12); relleno(c, (0.55, 0.57, 0.62), 3)
        xx = x + 18
        while xx < x + w - 50:
            bw, bh = r.uniform(35, 80), r.uniform(30, h / niveles - 30)
            if r.random() < 0.65:
                c.rectangle(xx, yy - 10 - bh, bw, bh); relleno(c, r.choice(colores), 2.5)
                if r.random() < 0.5: linea(c, [(xx + 6, yy - 10 - bh * 0.6), (xx + bw - 6, yy - 10 - bh * 0.6)], 2, TINTA, 0.4)
            else:
                rrect(c, xx, yy - 10 - bh, bw * 0.45, bh, 6); relleno(c, r.choice(colores), 2.5)
            xx += bw + r.uniform(4, 14)


def banco_trabajo(c, x, y, w, alto=280):
    sombra_suave(c, lambda cc: cc.rectangle(x, y - 20, w, 40), 20, 0.3)
    c.rectangle(x, y - alto, w, 34); relleno(c, degradado(0, 0, (0.75, 0.55, 0.35), (0.55, 0.38, 0.22), 0, 0), 4)
    textura(c, lambda cc: cc.rectangle(x, y - alto, w, 34), "madera", 0.5, sem=7)
    c.rectangle(x + 20, y - alto + 34, w - 40, alto - 34); relleno(c, (0.4, 0.42, 0.46), 4)
    for i in range(3):
        yy = y - alto + 50 + i * (alto - 70) / 3
        c.rectangle(x + 34, yy, w - 68, (alto - 70) / 3 - 10); relleno(c, (0.5, 0.52, 0.57), 3)
        linea(c, [(x + w / 2 - 30, yy + 14), (x + w / 2 + 30, yy + 14)], 5, (0.8, 0.8, 0.82))


def computadora(c, x, y, s=1.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    rrect(c, -70, -110, 140, 90, 6); relleno(c, (0.2, 0.2, 0.22), 3)
    c.rectangle(-60, -100, 120, 70); c.set_source(degradado(-100, -30, (0.4, 0.7, 0.9), (0.2, 0.4, 0.7))); c.fill()
    c.rectangle(-8, -20, 16, 16); relleno(c, (0.3, 0.3, 0.32), 2); c.rectangle(-35, -6, 70, 8); relleno(c, (0.3, 0.3, 0.32), 2)
    c.restore()


def planta(c, x, y, s=1.0, sem=1):
    r = random.Random(sem)
    c.move_to(x - 40 * s, y - 90 * s); c.line_to(x + 40 * s, y - 90 * s); c.line_to(x + 30 * s, y); c.line_to(x - 30 * s, y); c.close_path()
    relleno(c, degradado(y - 90 * s, y, (0.85, 0.5, 0.3), (0.6, 0.32, 0.2)), 3.5)
    for i in range(11):
        a = math.radians(-70 + i * 14 + r.uniform(-6, 6)); L = r.uniform(90, 160) * s
        tip = (x + math.sin(a) * L, y - 90 * s - math.cos(a) * L)
        mid = (lerp(x, tip[0], 0.5) + math.cos(a) * 18 * s, lerp(y - 90 * s, tip[1], 0.5) + math.sin(a) * 18 * s)
        c.move_to(x, y - 90 * s); c.curve_to(mid[0], mid[1], mid[0], mid[1], *tip)
        mid2 = (lerp(x, tip[0], 0.5) - math.cos(a) * 18 * s, lerp(y - 90 * s, tip[1], 0.5) - math.sin(a) * 18 * s)
        c.curve_to(mid2[0], mid2[1], mid2[0], mid2[1], x, y - 90 * s)
        relleno(c, osc((0.3, 0.55, 0.3), r.uniform(0.85, 1.15)), 2.5)


def reloj(c, x, y, r=34):
    c.arc(x, y, r, 0, 7); relleno(c, (0.97, 0.97, 0.95), 4)
    for k in range(12):
        a = k * math.pi / 6; linea(c, [(x + math.cos(a) * r * 0.75, y + math.sin(a) * r * 0.75), (x + math.cos(a) * r * 0.88, y + math.sin(a) * r * 0.88)], 2)
    linea(c, [(x, y), (x + r * 0.45, y - r * 0.3)], 4); linea(c, [(x, y), (x - r * 0.1, y - r * 0.7)], 3)


def ventana_lateral(c, cuarto, lado, u0, u1, v0, v1, cielo_=((0.55, 0.75, 0.95), (0.9, 0.95, 1.0)), luz=True, divisiones=3):
    q = cuarto.quad(lado, u0, u1, v0, v1)
    poli(c, q); g = degradado(q[0][1], q[3][1], *cielo_); c.set_source(g); c.fill()
    # edificios/árboles lejanos
    c.save(); poli(c, q); c.clip()
    r = random.Random(5)
    for k in range(10):
        uu = lerp(u0, u1, k / 10)
        p = cuarto.pared(lado, uu, v0); top = cuarto.pared(lado, uu, lerp(v0, v1, r.uniform(0.25, 0.55)))
        p2 = cuarto.pared(lado, lerp(u0, u1, (k + 1) / 10), v0)
        poli(c, [top, (p2[0], top[1]), p2, p]); c.set_source_rgba(*mezcla(cielo_[1], (0.5, 0.6, 0.65), 0.45), 1); c.fill()
    c.restore()
    for k in range(1, divisiones):
        u = lerp(u0, u1, k / divisiones)
        linea(c, [cuarto.pared(lado, u, v0), cuarto.pared(lado, u, v1)], 8, (0.92, 0.92, 0.94))
    linea(c, [cuarto.pared(lado, u0, (v0 + v1) / 2), cuarto.pared(lado, u1, (v0 + v1) / 2)], 7, (0.92, 0.92, 0.94))
    poli(c, q); c.set_source_rgb(0.92, 0.92, 0.94); c.set_line_width(12); c.stroke()
    poli(c, q); c.set_source_rgb(*TINTA); c.set_line_width(3.5); c.stroke()
    # reflejo en vidrio
    a = cuarto.pared(lado, lerp(u0, u1, 0.15), v1); b = cuarto.pared(lado, lerp(u0, u1, 0.3), v1)
    d = cuarto.pared(lado, lerp(u0, u1, 0.05), v0); e = cuarto.pared(lado, lerp(u0, u1, 0.2), v0)
    poli(c, [a, b, e, d]); c.set_source_rgba(1, 1, 1, 0.22); c.fill()
    if luz:
        sgn = 1 if lado == "izq" else -1
        sp = [q[3], q[2]]
        dst = [(sp[0][0] + sgn * 520, sp[0][1] + 700), (sp[1][0] + sgn * 420, sp[1][1] + 520)]
        haz_luz(c, [q[0], q[1], dst[1], dst[0]], 0.28)


def puerta(c, x, y, w, h, color=(0.55, 0.35, 0.2), vidrio=False):
    c.rectangle(x - 10, y - h - 10, w + 20, h + 10); relleno(c, osc(color, 0.8), 4)
    c.rectangle(x, y - h, w, h); relleno(c, degradado(0, 0, osc(color, 1.15), osc(color, 0.85), x, x + w), 4)
    textura(c, lambda cc: cc.rectangle(x, y - h, w, h), "madera", 0.4, sem=11)
    for (yy, hh) in ((0.08, 0.38), (0.54, 0.38)):
        rrect(c, x + w * 0.14, y - h + h * yy, w * 0.72, h * hh, 6)
        if vidrio and yy < 0.2: relleno(c, degradado(0, 1, (0.6, 0.75, 0.85), (0.4, 0.5, 0.6)), 3)
        else: c.set_source_rgb(*TINTA); c.set_line_width(2.5); c.stroke()
    c.arc(x + w * 0.85, y - h * 0.47, 9, 0, 7); relleno(c, (0.85, 0.75, 0.35), 2.5)


# ================================================================== escenarios
def _cielo_hora(hora):
    return {"dia": ((0.42, 0.63, 0.92), (0.88, 0.93, 0.98)), "tarde": ((0.95, 0.55, 0.35), (1.0, 0.85, 0.6)),
            "noche": ((0.05, 0.07, 0.16), (0.2, 0.22, 0.38))}[hora]


def _noche(c, alfa=0.55):
    c.save(); c.set_operator(cairo.OPERATOR_MULTIPLY); c.set_source_rgba(0.35, 0.4, 0.65, alfa); c.paint(); c.restore()


def taller(c, hora="dia"):
    """Taller mecánico limpio: piso epóxico brillante, gabinete rojo, tablero de herramientas, carteles."""
    k = Cuarto(200, 470, 880, 1240, (540, 980))
    k.pintar(c, pared=(0.92, 0.93, 0.95), piso=(0.78, 0.8, 0.84), techo=(0.95, 0.95, 0.96), franja=((0.75, 0.12, 0.12), 0.3, 0.34),
             zocalo=(0.5, 0.52, 0.58))
    for u in (0.15, 0.55, 0.85): k.lampara_techo(c, u, 0.5, 0.35)
    ventana_lateral(c, k, "der", 0.25, 0.9, 0.42, 0.9, _cielo_hora(hora), luz=hora != "noche")
    cartel(c, 250, 560, 150, 190, "SERVICIO", lambda cc, x, y, w, h: llanta(cc, x + w / 2, y + h / 2, h * 0.42))
    cartel(c, 430, 560, 150, 190, "DIAGNÓSTICO", lambda cc, x, y, w, h: (computadora(cc, x + w / 2, y + h * 0.95, 0.85),))
    cartel(c, 610, 560, 150, 190, "REFACCIONES", lambda cc, x, y, w, h: engrane(cc, x + w / 2, y + h / 2, h * 0.36))
    reloj(c, 820, 600)
    herramientas_tablero(c, 240, 820, 300, 230)
    banco_trabajo(c, 560, 1240, 300, 230); computadora(c, 700, 1006, 0.9)
    estante(c, 222, 1240, 0, 0) if False else None
    # pared izquierda: estante en perspectiva simplificado (cajas)
    for (u, v, col) in [(0.55, 0.35, (0.75, 0.6, 0.4)), (0.7, 0.35, (0.3, 0.45, 0.7)), (0.55, 0.55, (0.85, 0.3, 0.2)), (0.72, 0.55, (0.95, 0.8, 0.3))]:
        poli(c, k.quad("izq", u, u + 0.12, v, v + 0.14)); relleno(c, col, 3)
    for v in (0.35, 0.55):
        poli(c, k.quad("izq", 0.5, 0.88, v - 0.015, v)); relleno(c, (0.5, 0.52, 0.57), 3)
    reflejo_piso(c, 1240, 420, 0.25)
    gabinete_rojo(c, 30, 1560, 250, 420)
    llanta(c, 950, 1600, 95, apilar=2)
    if hora == "noche": _noche(c)


def llanta(c, x, y, r, apilar=1):
    sombra_suave(c, lambda cc: (cc.save(), cc.translate(x, y), cc.scale(1, 0.25), cc.arc(0, 0, r * 1.2, 0, 7), cc.restore()), 16, 0.4)
    for i in range(apilar):
        yy = y - i * r * 0.62
        rrect(c, x - r, yy - r * 0.6, 2 * r, r * 0.6, r * 0.25); relleno(c, degradado(yy - r * 0.6, yy, (0.25, 0.25, 0.27), (0.08, 0.08, 0.09)), 4)
        for k in range(7):
            xx = x - r * 0.85 + k * r * 0.28
            linea(c, [(xx, yy - r * 0.52), (xx + r * 0.1, yy - r * 0.08)], 3, (0.35, 0.35, 0.38))
    c.save(); c.translate(x, y - apilar * r * 0.62 + r * 0.02); c.scale(1, 0.3)
    c.arc(0, 0, r, 0, 7); relleno(c, (0.12, 0.12, 0.13), 4); c.arc(0, 0, r * 0.5, 0, 7); relleno(c, (0.05, 0.05, 0.05), 3); c.restore()


def engrane(c, x, y, r):
    c.save(); c.translate(x, y); c.new_path()
    for k in range(16):
        a = k * math.pi / 8; rr = r if k % 2 == 0 else r * 0.8
        c.line_to(math.cos(a - 0.2) * rr, math.sin(a - 0.2) * rr); c.line_to(math.cos(a + 0.2) * rr, math.sin(a + 0.2) * rr)
    c.close_path(); relleno(c, (0.75, 0.77, 0.8), 3); c.arc(0, 0, r * 0.35, 0, 7); relleno(c, (0.3, 0.32, 0.38), 3); c.restore()


def oficina(c, hora="dia"):
    """Oficina moderna con ventanal a la ciudad, escritorio, plantas y librero."""
    k = Cuarto(190, 480, 890, 1240, (540, 960))
    k.pintar(c, pared=(0.93, 0.91, 0.87), piso=(0.62, 0.48, 0.36), tex_piso="madera", zocalo=(0.35, 0.3, 0.28))
    # ventanal en la pared del fondo
    cx0, cy0, cx1, cy1 = 300, 560, 780, 1000
    cie = _cielo_hora(hora)
    c.rectangle(cx0, cy0, cx1 - cx0, cy1 - cy0); c.set_source(degradado(cy0, cy1, *cie)); c.fill()
    r = random.Random(8)
    c.save(); c.rectangle(cx0, cy0, cx1 - cx0, cy1 - cy0); c.clip()
    x = cx0 - 10
    while x < cx1:
        bw, bh = r.uniform(40, 90), r.uniform(120, 360)
        col = mezcla(cie[1], (0.35, 0.42, 0.55), r.uniform(0.4, 0.7))
        c.rectangle(x, cy1 - bh, bw, bh); c.set_source_rgb(*col); c.fill()
        for wy in np.arange(cy1 - bh + 10, cy1, 22):
            for wx in np.arange(x + 6, x + bw - 8, 16):
                c.rectangle(wx, wy, 8, 10)
                c.set_source_rgba(1, 0.9, 0.5, 0.9) if hora == "noche" and r.random() < 0.5 else c.set_source_rgba(1, 1, 1, 0.25)
                c.fill()
        x += bw + r.uniform(2, 10)
    c.restore()
    for xx in np.linspace(cx0, cx1, 4): linea(c, [(xx, cy0), (xx, cy1)], 9, (0.3, 0.3, 0.32))
    c.rectangle(cx0, cy0, cx1 - cx0, cy1 - cy0); c.set_source_rgb(*TINTA); c.set_line_width(4); c.stroke()
    # librero izquierdo en perspectiva (frente simple)
    for v in (0.2, 0.42, 0.64):
        poli(c, k.quad("izq", 0.35, 0.85, v, v + 0.02)); relleno(c, (0.4, 0.28, 0.2), 3)
        rr = random.Random(int(v * 100))
        u = 0.37
        while u < 0.82:
            du = rr.uniform(0.025, 0.05)
            poli(c, k.quad("izq", u, u + du, v + 0.02, v + 0.02 + rr.uniform(0.1, 0.16)))
            relleno(c, rr.choice([(0.6, 0.15, 0.15), (0.2, 0.3, 0.55), (0.85, 0.75, 0.4), (0.3, 0.45, 0.35)]), 2)
            u += du + 0.005
    # cuadros
    cartel(c, 820 - 20, 600, 60, 90, "", None, (0.9, 0.85, 0.75))
    # escritorio
    sombra_suave(c, lambda cc: cc.rectangle(240, 1330, 620, 60), 25, 0.35)
    c.move_to(200, 1150); c.line_to(880, 1150); c.line_to(920, 1210); c.line_to(160, 1210); c.close_path()
    relleno(c, degradado(1150, 1210, (0.5, 0.33, 0.2), (0.38, 0.24, 0.14)), 4)
    textura(c, lambda cc: (cc.move_to(200, 1150), cc.line_to(880, 1150), cc.line_to(920, 1210), cc.line_to(160, 1210), cc.close_path()), "madera", 0.5, sem=12)
    c.rectangle(170, 1210, 740, 160); relleno(c, degradado(1210, 1370, (0.42, 0.28, 0.17), (0.3, 0.2, 0.12)), 4)
    computadora(c, 640, 1155, 1.3)
    for k_ in range(4): c.rectangle(300 + k_ * 6, 1120 - k_ * 8, 120, 8); relleno(c, (0.97, 0.97, 0.95), 2)
    c.arc(470, 1130, 22, 0, 7); relleno(c, (0.95, 0.95, 0.95), 3)
    reflejo_piso(c, 1240, 300, 0.12)
    planta(c, 980, 1660, 1.3, 2); planta(c, 90, 1500, 1.0, 3)
    if hora == "noche": _noche(c, 0.45)


def sala(c, hora="dia"):
    """Sala de casa: sillón, tapete, tele, lámpara de pie, cortinas."""
    k = Cuarto(200, 500, 880, 1250, (540, 980))
    k.pintar(c, pared=(0.86, 0.8, 0.68), piso=(0.66, 0.5, 0.36), tex_piso="madera", zocalo=(0.95, 0.95, 0.92))
    ventana_lateral(c, k, "izq", 0.3, 0.85, 0.35, 0.85, _cielo_hora(hora), luz=hora != "noche")
    # cortinas
    for u in (0.24, 0.86):
        poli(c, k.quad("izq", u - 0.06, u + 0.04, 0.2, 0.92)); relleno(c, (0.75, 0.35, 0.3), 3)
    # cuadros
    cartel(c, 420, 600, 240, 160, "", lambda cc, x, y, w, h: _paisajito(cc, x, y, w, h), (0.95, 0.92, 0.85))
    # tele y mueble
    c.rectangle(560, 960, 260, 150); relleno(c, (0.12, 0.12, 0.14), 4)
    c.rectangle(572, 972, 236, 126); c.set_source(degradado(972, 1098, (0.25, 0.3, 0.4), (0.08, 0.08, 0.1))); c.fill()
    c.rectangle(520, 1110, 340, 120); relleno(c, (0.45, 0.3, 0.2), 4)
    textura(c, lambda cc: cc.rectangle(520, 1110, 340, 120), "madera", 0.45, sem=13)
    # lámpara de pie
    linea(c, [(300, 1250), (300, 820)], 8, (0.25, 0.25, 0.27))
    c.move_to(250, 820); c.line_to(350, 820); c.line_to(330, 740); c.line_to(270, 740); c.close_path(); relleno(c, (0.98, 0.92, 0.75), 3)
    g = cairo.RadialGradient(300, 800, 10, 300, 800, 260); g.add_color_stop_rgba(0, 1, 0.9, 0.6, 0.35); g.add_color_stop_rgba(1, 1, 0.9, 0.6, 0)
    c.set_source(g); c.arc(300, 800, 260, 0, 7); c.fill()
    reflejo_piso(c, 1250, 300, 0.1)
    # tapete
    c.save(); c.translate(540, 1560); c.scale(1, 0.32); c.arc(0, 0, 460, 0, 7); c.restore(); relleno(c, (0.55, 0.25, 0.25), 4)
    c.save(); c.translate(540, 1560); c.scale(1, 0.32); c.arc(0, 0, 380, 0, 7); c.restore(); c.set_source_rgba(1, 0.85, 0.6, 0.35); c.set_line_width(10); c.stroke()
    # sillón en primer plano (de espaldas, abajo)
    sombra_suave(c, lambda cc: rrect(cc, 120, 1700, 840, 160, 40), 30, 0.35)
    rrect(c, 100, 1660, 880, 300, 50); relleno(c, degradado(1660, 1960, (0.3, 0.4, 0.55), (0.18, 0.25, 0.35)), 5)
    textura(c, lambda cc: rrect(cc, 100, 1660, 880, 300, 50), "suave", 0.3, sem=9)
    rrect(c, 60, 1620, 120, 340, 40); relleno(c, (0.25, 0.34, 0.48), 5); rrect(c, 900, 1620, 120, 340, 40); relleno(c, (0.25, 0.34, 0.48), 5)
    planta(c, 940, 1300, 1.1, 5)
    if hora == "noche": _noche(c, 0.5)


def _paisajito(c, x, y, w, h):
    c.rectangle(x, y, w, h); c.set_source(degradado(y, y + h, (0.95, 0.7, 0.45), (0.98, 0.9, 0.7))); c.fill()
    c.arc(x + w * 0.7, y + h * 0.45, h * 0.15, 0, 7); c.set_source_rgb(1, 0.95, 0.7); c.fill()
    c.move_to(x, y + h); c.line_to(x + w * 0.3, y + h * 0.5); c.line_to(x + w * 0.55, y + h * 0.8); c.line_to(x + w * 0.8, y + h * 0.55)
    c.line_to(x + w, y + h); c.close_path(); c.set_source_rgb(0.45, 0.4, 0.5); c.fill()


def cocina(c, hora="dia"):
    k = Cuarto(200, 500, 880, 1250, (540, 980))
    k.pintar(c, pared=(0.95, 0.94, 0.9), piso=(0.85, 0.83, 0.78), tex_pared="suave", zocalo=None)
    # azulejo
    c.save(); c.rectangle(200, 820, 680, 220); c.clip()
    c.rectangle(200, 820, 680, 220); c.set_source_rgb(0.75, 0.88, 0.9); c.fill()
    for xx in range(200, 880, 40): linea(c, [(xx, 820), (xx, 1040)], 2, (1, 1, 1))
    for yy in range(820, 1040, 40): linea(c, [(200, yy), (880, yy)], 2, (1, 1, 1))
    c.restore()
    # alacenas
    for x in range(220, 860, 160):
        c.rectangle(x, 560, 150, 230); relleno(c, degradado(560, 790, (0.75, 0.55, 0.35), (0.6, 0.42, 0.26)), 4)
        rrect(c, x + 14, 576, 122, 198, 6); c.set_source_rgb(*TINTA); c.set_line_width(2); c.stroke()
        linea(c, [(x + 120, 740), (x + 120, 770)], 6, (0.85, 0.85, 0.88))
    # barra
    c.rectangle(200, 1040, 680, 30); relleno(c, (0.25, 0.25, 0.28), 4)
    c.rectangle(200, 1070, 680, 180); relleno(c, degradado(1070, 1250, (0.7, 0.5, 0.32), (0.55, 0.38, 0.24)), 4)
    for x in range(220, 860, 170):
        rrect(c, x, 1085, 155, 150, 6); c.set_source_rgb(*TINTA); c.set_line_width(2); c.stroke()
    # estufa / refri
    c.rectangle(560, 1040, 180, 30); relleno(c, (0.15, 0.15, 0.16), 3)
    for kx in (600, 700): c.save(); c.translate(kx, 1052); c.scale(1, 0.3); c.arc(0, 0, 30, 0, 7); c.restore(); relleno(c, (0.3, 0.3, 0.32), 2)
    poli(c, k.quad("der", 0.55, 0.95, 0, 0.82)); relleno(c, (0.88, 0.9, 0.92), 4)
    linea(c, [k.pared("der", 0.6, 0.35), k.pared("der", 0.6, 0.6)], 7, (0.6, 0.6, 0.65))
    reflejo_piso(c, 1250, 250, 0.12)
    for u in (0.3, 0.75): k.lampara_techo(c, u, 0.5, 0.25)
    if hora == "noche": _noche(c, 0.45)


def bodega(c, hora="noche"):
    """Bodega oscura: concreto, cajas apiladas, foco colgante."""
    k = Cuarto(180, 420, 900, 1240, (540, 980))
    k.pintar(c, pared=(0.55, 0.55, 0.58), piso=(0.45, 0.45, 0.47), tex_pared="concreto")
    r = random.Random(6)
    for (x, y, n) in [(230, 1240, 3), (650, 1240, 4), (40, 1720, 3), (760, 1760, 2)]:
        s = 1.0 if y < 1300 else 1.6
        for i in range(n):
            bw, bh = 130 * s, 100 * s
            xx = x + (i % 2) * 20; yy = y - i * bh
            c.rectangle(xx, yy - bh, bw, bh); relleno(c, degradado(0, 0, (0.8, 0.62, 0.4), (0.6, 0.45, 0.28), xx, xx + bw), 4)
            linea(c, [(xx, yy - bh / 2), (xx + bw, yy - bh / 2)], 6 * s, (0.75, 0.68, 0.5))
            texto(c, "FRÁGIL" if r.random() < 0.4 else "", xx + bw / 2, yy - bh * 0.25, 18 * s, ROJO_)
    linea(c, [(540, 0), (540, 520)], 4)
    c.arc(540, 545, 26, 0, 7); relleno(c, (1, 0.95, 0.7), 3)
    g = cairo.RadialGradient(540, 560, 10, 540, 900, 900); g.add_color_stop_rgba(0, 1, 0.9, 0.6, 0.45); g.add_color_stop_rgba(1, 1, 0.9, 0.6, 0)
    c.set_source(g); c.move_to(510, 560); c.line_to(570, 560); c.line_to(1100, 1920); c.line_to(-20, 1920); c.close_path(); c.fill()
    vig = cairo.RadialGradient(540, 1100, 300, 540, 1100, 1300); vig.add_color_stop_rgba(0, 0, 0, 0, 0); vig.add_color_stop_rgba(1, 0, 0, 0, 0.6)
    c.set_source(vig); c.paint()


def calle(c, hora="dia"):
    """Calle mexicana en perspectiva: fachadas de colores, banquetas, postes, cables, coches estacionados."""
    vp = (540, 1050)
    cie = _cielo_hora(hora)
    cielo(c, cie[0], cie[1], 1100)
    nubes(c, 4, 120, 600, 5, (1, 1, 1) if hora != "noche" else (0.3, 0.32, 0.45), 0.8)
    # calle
    poli(c, [(vp[0] - 40, vp[1]), (vp[0] + 40, vp[1]), (W + 300, H), (-300, H)])
    c.set_source(degradado(vp[1], H, (0.45, 0.45, 0.48), (0.3, 0.3, 0.33))); c.fill()
    textura(c, poli_f([(vp[0] - 40, vp[1]), (vp[0] + 40, vp[1]), (W + 300, H), (-300, H)]), "concreto", 0.4, sem=21)
    for k in range(9):
        a = (k / 9) ** 2.2; b = ((k + 0.5) / 9) ** 2.2
        y0 = lerp(vp[1], H, a); y1 = lerp(vp[1], H, b)
        w0, w1 = lerp(2, 24, a), lerp(2, 24, b)
        poli(c, [(540 - w0, y0), (540 + w0, y0), (540 + w1, y1), (540 - w1, y1)]); c.set_source_rgb(0.95, 0.85, 0.3); c.fill()
    # banquetas
    for s in (-1, 1):
        bx = W / 2 + s * 40
        poli(c, [(bx, vp[1]), (bx + s * 30, vp[1]), (W / 2 + s * 900, H), (W / 2 + s * 700, H)])
        c.set_source_rgb(0.78, 0.76, 0.72); c.fill()
    # fachadas a cada lado
    cols = [(0.95, 0.72, 0.5), (0.5, 0.72, 0.85), (0.95, 0.55, 0.55), (0.65, 0.82, 0.55), (0.98, 0.85, 0.45), (0.85, 0.6, 0.85)]
    for s in (-1, 1):
        r = random.Random(30 + s)
        cuts = [0.0, 0.25, 0.45, 0.62, 0.76, 0.87, 0.95, 1.0]
        for i in range(len(cuts) - 1, 0, -1):
            u0, u1 = cuts[i - 1], cuts[i]
            def P(u, alto):
                x = lerp(W / 2 + s * (W / 2 + 120), vp[0] + s * 70, u)
                ybase = lerp(H - 230, vp[1], u)
                top = lerp(ybase - alto, vp[1] - alto * 0.12, u)
                return x, ybase, top
            alto = r.uniform(900, 1300)
            xa, ya, ta = P(u0, alto); xb, yb, tb = P(u1, alto)
            col = cols[(i + (s > 0) * 3) % len(cols)]
            poli(c, [(xa, ta), (xb, tb), (xb, yb), (xa, ya)])
            c.set_source(degradado(0, 0, osc(col, 0.85), col, xa, xb)); c.fill()
            textura(c, poli_f([(xa, ta), (xb, tb), (xb, yb), (xa, ya)]), "estuco", 0.35, sem=40 + i)
            poli(c, [(xa, ta), (xb, tb), (xb, yb), (xa, ya)]); c.set_source_rgb(*TINTA); c.set_line_width(3.5); c.stroke()
            # cornisa
            poli(c, [(xa, ta), (xb, tb), (xb, tb + (yb - tb) * 0.05), (xa, ta + (ya - ta) * 0.05)]); relleno(c, osc(col, 0.7), 2.5)
            # ventanas y puerta
            for f in (0.22, 0.5):
                for (uu0, uu1) in ((0.15, 0.4), (0.6, 0.85)):
                    q = []
                    for uu, ff in ((uu0, f), (uu1, f), (uu1, f + 0.17), (uu0, f + 0.17)):
                        x = lerp(xa, xb, uu); t = lerp(ta, tb, uu); y = lerp(ya, yb, uu)
                        q.append((x, lerp(t, y, ff)))
                    poli(c, q)
                    relleno(c, degradado(q[0][1], q[2][1], (0.3, 0.38, 0.5), (0.15, 0.18, 0.25)) if hora != "noche" else (1, 0.85, 0.5), 2.5)
                    # balcón de herrería
                    if f == 0.22:
                        linea(c, [(q[3][0] - 6 * s, q[3][1] + 6), (q[2][0] + 6 * s, q[2][1] + 6)], 4)
            q = []
            for uu, ff in ((0.35, 0.75), (0.65, 0.75), (0.65, 1.0), (0.35, 1.0)):
                x = lerp(xa, xb, uu); t = lerp(ta, tb, uu); y = lerp(ya, yb, uu); q.append((x, lerp(t, y, ff)))
            poli(c, q); relleno(c, (0.45, 0.28, 0.18), 3)
            if r.random() < 0.5:
                q2 = []
                for uu, ff in ((0.1, 0.68), (0.9, 0.68), (0.9, 0.74), (0.1, 0.74)):
                    x = lerp(xa, xb, uu); t = lerp(ta, tb, uu); y = lerp(ya, yb, uu); q2.append((x, lerp(t, y, ff)))
                poli(c, q2); relleno(c, r.choice([ROJO_, (0.2, 0.5, 0.3), (0.2, 0.3, 0.6)]), 2)
    # postes y cables
    for s in (-1, 1):
        for u in (0.05, 0.5, 0.8):
            x = lerp(W / 2 + s * 520, vp[0] + s * 60, u); yb = lerp(H - 120, vp[1], u); h = lerp(1300, 140, u)
            linea(c, [(x, yb), (x, yb - h)], lerp(14, 3, u), (0.3, 0.3, 0.32))
            linea(c, [(x, yb - h), (x - s * lerp(120, 15, u), yb - h + lerp(20, 3, u))], lerp(8, 2, u), (0.3, 0.3, 0.32))
    for k in range(3):
        y = 260 + k * 60
        c.move_to(-20, y); c.curve_to(300, y + 160, 700, y + 140, W + 20, y + 20); c.set_source_rgba(*TINTA, 0.8); c.set_line_width(3); c.stroke()
    camioneta(c, 230, 1700, 0.85, 1, color=(0.6, 0.12, 0.12))
    if hora == "noche":
        _noche(c, 0.5)
        for s in (-1, 1):
            x = lerp(W / 2 + s * 520, vp[0] + s * 60, 0.05) - s * 120
            g = cairo.RadialGradient(x, 640, 10, x, 640, 500); g.add_color_stop_rgba(0, 1, 0.85, 0.5, 0.5); g.add_color_stop_rgba(1, 1, 0.85, 0.5, 0)
            c.set_source(g); c.arc(x, 640, 500, 0, 7); c.fill()


def rancho(c, hora="dia"):
    """Hacienda/rancho: muro de piedra, portal de arcos, buganvilias, patio empedrado, montañas con bruma."""
    from motor_pov import rancho as rancho_simple
    cie = _cielo_hora(hora)
    cielo(c, cie[0], cie[1], 1150)
    if hora == "noche":
        for i in range(70):
            r = random.Random(i); c.arc(r.uniform(0, W), r.uniform(0, 800), r.uniform(1, 2.6), 0, 7); c.set_source_rgba(1, 1, 1, r.uniform(0.4, 0.9)); c.fill()
        c.arc(860, 260, 60, 0, 7); c.set_source_rgb(0.95, 0.94, 0.85); c.fill()
    else:
        nubes(c, 3, 150, 600, 6)
    for (yb, al, col, sm) in [(980, 380, 0.75, 41), (1060, 300, 0.6, 42), (1150, 200, 0.45, 43)]:
        tono = mezcla(cie[1], (0.3, 0.42, 0.35) if hora != "noche" else (0.08, 0.1, 0.16), col)
        montanas(c, yb, al, tono, sm, borde=0)
    # patio empedrado
    c.rectangle(0, 1150, W, H - 1150); c.set_source(degradado(1150, H, (0.72, 0.62, 0.5), (0.55, 0.45, 0.35))); c.fill()
    r = random.Random(17)
    for j in range(26):
        y = 1160 + (j ** 1.6) * 6.2
        if y > H: break
        hh = 8 + j * 2.6
        x = -r.uniform(0, hh * 2)
        while x < W:
            ww = hh * r.uniform(1.4, 2.2)
            rrect(c, x, y, ww - 3, hh - 3, hh * 0.35)
            c.set_source_rgb(*osc((0.66, 0.57, 0.46), r.uniform(0.82, 1.12))); c.fill_preserve()
            c.set_source_rgba(*TINTA, 0.35); c.set_line_width(1.5); c.stroke()
            x += ww
    rancho_simple(c, 40, 1150, 1000, 380, noche=hora == "noche")
    # piedra en la base del muro
    c.rectangle(40, 1060, 1000, 90); c.set_source_rgb(0.6, 0.55, 0.5); c.fill()
    for j in range(3):
        x = 40 - j * 25
        while x < 1040:
            w = r.uniform(40, 80); rrect(c, max(40, x), 1062 + j * 29, min(w, 1040 - max(40, x)) - 3, 26, 8)
            c.set_source_rgb(*osc((0.62, 0.57, 0.52), r.uniform(0.8, 1.15))); c.fill_preserve(); c.set_source_rgba(*TINTA, 0.5); c.set_line_width(2); c.stroke()
            x += w
    linea(c, [(40, 1060), (1040, 1060)], 3)
    # buganvilias
    for (bx, by) in [(60, 800), (1000, 820)]:
        for i in range(70):
            a, d = r.uniform(0, 6.28), r.uniform(0, 120)
            c.arc(bx + math.cos(a) * d, by + math.sin(a) * d * 1.4, r.uniform(9, 18), 0, 7)
            c.set_source_rgb(*r.choice([(0.85, 0.2, 0.5), (0.95, 0.35, 0.6), (0.7, 0.12, 0.4), (0.3, 0.5, 0.25)])); c.fill()
    # faroles
    for x in (300, 780):
        linea(c, [(x, 860), (x, 900)], 4); rrect(c, x - 18, 900, 36, 50, 6); relleno(c, (1, 0.85, 0.5) if hora == "noche" else (0.9, 0.9, 0.8), 3)
        if hora == "noche":
            g = cairo.RadialGradient(x, 925, 5, x, 925, 220); g.add_color_stop_rgba(0, 1, 0.8, 0.45, 0.6); g.add_color_stop_rgba(1, 1, 0.8, 0.45, 0)
            c.set_source(g); c.arc(x, 925, 220, 0, 7); c.fill()
    for (x, y, s) in [(110, 1260, 1.1), (990, 1290, 1.0)]: agave(c, x, y, s)
    for (x, y, s) in [(70, 1820, 2.0)]: agave(c, x, y, s, (0.3, 0.5, 0.45))
    if hora == "noche": _noche(c, 0.35)


def sierra(c, hora="tarde"):
    """Sierra con pinos, niebla en capas y luz de amanecer/atardecer."""
    cie = {"tarde": ((0.25, 0.22, 0.4), (0.98, 0.55, 0.3)), "dia": ((0.45, 0.65, 0.92), (0.9, 0.93, 0.96)),
           "noche": ((0.04, 0.05, 0.12), (0.15, 0.18, 0.3))}[hora]
    cielo(c, cie[0], cie[1], 1300)
    if hora != "noche":
        c.arc(560, 1000, 120, 0, 7); c.set_source_rgba(1, 0.9, 0.6, 0.9); c.fill()
    nubes(c, 11, 200, 700, 5, mezcla(cie[1], (1, 1, 1), 0.5), 0.55)
    capas = [(980, 360, 0.25), (1100, 300, 0.42), (1250, 260, 0.6), (1450, 220, 0.78), (1700, 200, 0.92)]
    for i, (yb, al, d) in enumerate(capas):
        tono = mezcla(cie[1], (0.08, 0.14, 0.1), d)
        montanas(c, yb, al * 0.6, tono, 60 + i)
        r = random.Random(70 + i)
        n = 10 + i * 4
        for k in range(n):
            x = r.uniform(-50, W + 50); y = yb - al * 0.25 + r.uniform(0, al * 0.4)
            pino(c, x, y, (0.35 + i * 0.28) * r.uniform(0.8, 1.2), tono)
        # niebla
        g = cairo.LinearGradient(0, yb - 80, 0, yb + 120)
        g.add_color_stop_rgba(0, *cie[1], 0); g.add_color_stop_rgba(0.5, *cie[1], 0.35 * (1 - d * 0.5)); g.add_color_stop_rgba(1, *cie[1], 0)
        c.set_source(g); c.rectangle(0, yb - 80, W, 200); c.fill()


def pino(c, x, y, s=1.0, color=(0.2, 0.35, 0.25)):
    c.rectangle(x - 7 * s, y - 40 * s, 14 * s, 40 * s); relleno(c, osc(color, 0.7), 2 * s)
    for i in range(4):
        w, yy = (100 - i * 20) * s, y - 30 * s - i * 62 * s
        c.move_to(x - w, yy); c.line_to(x, yy - 120 * s); c.line_to(x + w, yy); c.close_path()
        relleno(c, osc(color, 1 + i * 0.05), max(1, 2.5 * s))


ESCENARIOS = dict(taller=taller, oficina=oficina, sala=sala, cocina=cocina, bodega=bodega, calle=calle, rancho=rancho, sierra=sierra)


if __name__ == "__main__":
    import os, sys
    from PIL import Image
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "salida"); os.makedirs(out, exist_ok=True)
    nombres = sys.argv[1:] or list(ESCENARIOS)
    ims = []
    for n in nombres:
        hora = "dia"
        if ":" in n: n, hora = n.split(":")
        s = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); c = cairo.Context(s); c.set_source_rgb(1, 1, 1); c.paint()
        ESCENARIOS[n](c, hora) if n != "bodega" else ESCENARIOS[n](c)
        p = os.path.join(out, f"esc_{n}_{hora}.png"); s.write_to_png(p); ims.append(Image.open(p).convert("RGB").resize((360, 640)))
        print("ok", n, hora)
    hoja = Image.new("RGB", (360 * min(4, len(ims)), 640 * ((len(ims) + 3) // 4)), "white")
    for i, im in enumerate(ims): hoja.paste(im, (360 * (i % 4), 640 * (i // 4)))
    hoja.save(os.path.join(out, "escenarios_muestra.png")); print("hoja lista")
