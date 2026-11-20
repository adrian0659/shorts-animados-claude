"""POV: eres el escolta del narcotraficante más buscado de México (127.6 s, 1080x1920).

Ejecutar desde stickman/estilos/pov_explicativo/:
    python3 videos/escolta.py --fotos            # una foto por escena -> salida/escolta/fotos/
    python3 videos/escolta.py                    # video final -> salida/escolta/escolta.mp4
Requiere la voz en salida/escolta/voz.mp3 (o pasa --voz ruta.mp3).

Datos (verificados en noviembre de 2026): Nemesio Oseguera Cervantes, «El Mencho», fundador y líder del CJNG,
murió el 22 de febrero de 2026 tras un operativo del Ejército en Tapalpa, Jalisco (Sedena; NPR; Expansión).
"""
import os, sys, math, random, subprocess, wave
from concurrent.futures import ProcessPoolExecutor
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
from motor_pov import *

SAL = os.path.join(AQUI, "..", "salida", "escolta")
DUR = 127.6
NOCHE = (0.32, 0.38, 0.62, 0.62)
ROJO = (0.85, 0.12, 0.12)
S = 1.45  # escala del monigote principal

# cortes (s), un poco antes de cada frase de la voz
C = [0, 5.2, 10.0, 13.3, 18.4, 21.5, 23.9, 26.2, 30.6, 34.6, 40.2, 44.55, 49.15, 53.3, 57.6, 62.1, 66.7,
     69.75, 73.1, 77.45, 79.4, 85.2, 88.6, 93.0, 96.1, 100.6, 104.0, 107.3, 112.7, 118.6, 124.5, DUR]


# ------------------------------------------------------------------ piezas propias de este video
def pino(ctx, x, y, s=1.0, color=(0.2, 0.35, 0.25)):
    ctx.rectangle(x - 8 * s, y - 40 * s, 16 * s, 40 * s); relleno(ctx, (0.35, 0.24, 0.15), 3)
    for i in range(4):
        w, yy = (110 - i * 22) * s, y - 30 * s - i * 70 * s
        ctx.move_to(x - w, yy); ctx.line_to(x, yy - 130 * s); ctx.line_to(x + w, yy); ctx.close_path()
        relleno(ctx, osc(color, 1 + i * 0.06), 3)


def fondo_rancho(noche=False, camioneta_x=None, arco=True):
    def f(c):
        if noche:
            cielo(c, (0.05, 0.07, 0.16), (0.2, 0.22, 0.38), 1150)
            for i in range(60):
                r = random.Random(i); c.arc(r.uniform(0, W), r.uniform(0, 800), r.uniform(1, 3), 0, 7)
                c.set_source_rgba(1, 1, 1, r.uniform(0.4, 0.9)); c.fill()
            c.arc(860, 260, 70, 0, 7); relleno(c, (0.95, 0.94, 0.85), 0)
            montanas(c, 1050, 300, (0.12, 0.14, 0.24), 4); montanas(c, 1150, 180, (0.1, 0.13, 0.18), 5)
            suelo(c, 1150, (0.28, 0.25, 0.28), (0.18, 0.16, 0.2))
        else:
            cielo(c, (0.42, 0.62, 0.9), (0.93, 0.88, 0.76), 1150)
            nubes(c, 3, 150, 600, 6)
            montanas(c, 1050, 320, (0.6, 0.66, 0.75), 4); montanas(c, 1150, 200, (0.45, 0.56, 0.45), 5, borde=3)
            suelo(c, 1150, (0.8, 0.68, 0.52), (0.62, 0.5, 0.36))
        rancho(c, 40, 1150, 1000, 360, noche=noche)
        for (x, y, s) in [(90, 1220, 0.9), (1000, 1240, 0.8)]:
            agave(c, x, y, s, (0.2, 0.32, 0.3) if noche else (0.35, 0.55, 0.5))
        if camioneta_x is not None:
            camioneta(c, camioneta_x, 1420, 1.15, -1, faros=False)
    return f


def fondo_oficina(c, noche=False):
    interior(c, (0.88, 0.8, 0.66), (0.6, 0.42, 0.3), 1420, zocalo=(0.55, 0.3, 0.2))
    ventana(c, 640, 330, 330, 430, c0=(0.42, 0.62, 0.9), c1=(0.9, 0.85, 0.7))
    lampara(c, 300, 92)
    cuadro_pared(c, 110, 380, 240, 300, lambda cc, x, y, w, h: (pino(cc, x + w / 2, y + h - 20, 0.9),), fondo=(0.75, 0.85, 0.9))
    cuadro_pared(c, 380, 470, 180, 150, None, "JALISCO", fondo=(0.95, 0.9, 0.75))
    # repisa con botellas
    c.rectangle(80, 840, 420, 22); relleno(c, (0.45, 0.3, 0.2), 4)
    for i, col in enumerate([(0.55, 0.4, 0.15), (0.3, 0.45, 0.25), (0.6, 0.25, 0.2), (0.5, 0.45, 0.3)]):
        botella(c, 130 + i * 95, 840, 0.75, col)


def cartel_se_busca(c, x, y, w, h, recompensa=True):
    c.save(); c.translate(x, y); c.rotate(math.radians(-2))
    rrect(c, 0, 0, w, h, 6); relleno(c, degradado(0, h, (0.96, 0.9, 0.74), (0.88, 0.8, 0.6)), 5)
    texto(c, "SE BUSCA", w / 2, h * 0.12, w * 0.17, ROJO)
    c.rectangle(w * 0.18, h * 0.22, w * 0.64, h * 0.5); relleno(c, (0.92, 0.92, 0.9), 4)
    c.save(); c.rectangle(w * 0.18, h * 0.22, w * 0.64, h * 0.5); c.clip()
    j = Actor("jefe", [dict(t=0, pose="parado", x=w / 2, y=h * 1.25, cara="serio")], escala=w / 520, semilla=4)
    j.dibujar(c, 0); c.restore()
    if recompensa:
        texto(c, "RECOMPENSA", w / 2, h * 0.8, w * 0.1, TINTA)
        texto(c, "$ MILLONES DE DÓLARES", w / 2, h * 0.89, w * 0.065, (0.15, 0.45, 0.2))
    for (px, py) in [(14, 14), (w - 14, 14)]:
        c.arc(px, py, 9, 0, 7); relleno(c, ROJO, 2)
    c.restore()


def tarjeta(c, x, y, w, h, titulo, quien=None, color=(0.98, 0.97, 0.93), incognita=False, t=0):
    c.save(); c.translate(x, y)
    c.save(); c.translate(6, 8); rrect(c, -w / 2, -h / 2, w, h, 12); c.set_source_rgba(0, 0, 0, 0.25); c.fill(); c.restore()
    rrect(c, -w / 2, -h / 2, w, h, 12); relleno(c, color, 4)
    if incognita:
        texto(c, "?", 0, -h * 0.1, h * 0.5, (0.4, 0.4, 0.45))
    elif quien:
        c.save(); rrect(c, -w / 2 + 8, -h / 2 + 8, w - 16, h * 0.62, 8); c.clip()
        a = Actor(quien, [dict(t=0, pose="parado", x=0, y=h * 0.9, cara="serio")], escala=h / 560, semilla=4)
        a.dibujar(c, t); c.restore()
    texto(c, titulo, 0, h * 0.32, min(h * 0.16, w * 0.13), TINTA)
    c.restore()


def organigrama(t, k_lineas=1.0, cabeza_vacia=False, tiembla=0.0):
    def f(c, tt):
        top = (540, 520)
        hijos = [(220, 1000), (540, 1000), (860, 1000)]
        for (hx, hy) in hijos:
            kk = clamp((tt - 0.6) / 0.8) * k_lineas
            pts = [(top[0], top[1] + 170), (top[0], 760), (hx, 760), (hx, hy - 150)]
            ln = [pts[0]]
            # dibuja hasta kk
            seg = [(pts[i], pts[i + 1]) for i in range(3)]
            tot = sum(math.dist(a, b) for a, b in seg); d = kk * tot
            for a, b in seg:
                L = max(1e-6, math.dist(a, b))
                if d <= 0: break
                u = min(1, d / L); ln.append((lerp(a[0], b[0], u), lerp(a[1], b[1], u))); d -= L
            if len(ln) > 1: linea(c, ln, 7, (0.25, 0.2, 0.18))
        for i, (hx, hy) in enumerate(hijos):
            if clamp((tt - 1.0 - i * 0.2) / 0.3) > 0:
                j = math.sin(tt * 30 + i) * tiembla
                tarjeta(c, hx + j, hy, 250, 300, "PLAZA " + "ABC"[i], incognita=True)
        j = math.sin(tt * 25) * tiembla * 1.5
        if cabeza_vacia:
            tarjeta(c, top[0] + j, top[1], 340, 360, "LÍDER", incognita=True, color=(0.95, 0.9, 0.85))
        else:
            tarjeta(c, top[0], top[1], 340, 360, "EL MENCHO", "jefe", color=(0.99, 0.95, 0.85), t=tt)
    return f


def fondo_corcho(c):
    c.set_source(degradado(0, H, (0.75, 0.58, 0.4), (0.6, 0.45, 0.3))); c.paint()
    r = random.Random(2)
    for _ in range(2500):
        c.arc(r.uniform(0, W), r.uniform(0, H), r.uniform(1, 3), 0, 7)
        c.set_source_rgba(0.35, 0.22, 0.12, r.uniform(0.1, 0.35)); c.fill()
    c.rectangle(0, 0, W, H); c.set_source_rgb(0.35, 0.22, 0.14); c.set_line_width(60); c.stroke()


def fondo_papel(color=(0.95, 0.92, 0.85)):
    def f(c):
        c.set_source(degradado(0, H, osc(color, 1.03), osc(color, 0.92))); c.paint()
        r = random.Random(5)
        for _ in range(1500):
            c.arc(r.uniform(0, W), r.uniform(0, H), r.uniform(0.5, 2), 0, 7)
            c.set_source_rgba(0.4, 0.35, 0.3, r.uniform(0.05, 0.15)); c.fill()
    return f


def fondo_rayos(c0, c1, n=18):
    def f(c, t):
        c.save(); c.set_source(degradado(0, H, c0, c1)); c.paint()
        c.translate(W / 2, H * 0.45); c.rotate(t * 0.25)
        for i in range(n):
            a = i * 2 * math.pi / n
            c.move_to(0, 0); c.arc(0, 0, 2000, a, a + math.pi / n); c.close_path()
            c.set_source_rgba(1, 1, 1, 0.07); c.fill()
        c.restore()
    return f


def telefono(c, w, h, t):
    c.set_source(degradado(0, h, (0.2, 0.22, 0.28), (0.1, 0.1, 0.14))); c.paint()
    rrect(c, w * 0.08, h * 0.08, w * 0.84, h * 0.84, 24); relleno(c, (0.93, 0.95, 0.97), 4)
    texto(c, "LOS COMPAS", w / 2, h * 0.17, h * 0.07, TINTA)
    linea(c, [(w * 0.12, h * 0.24), (w * 0.88, h * 0.24)], 2, TINTA, 0.3)
    msgs = [(0.2, "¿Vienes a la carne asada?", 0), (1.0, "¡Ya llegamos todos!", 0), (2.2, "No puedo...", 1)]
    for i, (t0, m, mio) in enumerate(msgs):
        if t < t0: continue
        k = rebote((t - t0) / 0.3)
        yy = h * (0.35 + i * 0.17)
        c.save(); c.translate(w * (0.62 if mio else 0.4), yy); c.scale(k, k)
        rrect(c, -w * 0.3, -h * 0.06, w * 0.6, h * 0.12, 18)
        relleno(c, (0.3, 0.75, 0.45) if mio else (1, 1, 1), 3)
        texto(c, m, 0, 0, h * 0.045, TINTA, MANO, peso=cairo.FONT_WEIGHT_BOLD)
        c.restore()


def puesto_tacos(c, x, y):
    c.rectangle(x - 180, y - 220, 360, 220); relleno(c, degradado(y - 220, y, (0.95, 0.85, 0.6), (0.85, 0.7, 0.45)), 5)
    for i in range(6):
        c.move_to(x - 210 + i * 70, y - 330); c.line_to(x - 140 + i * 70, y - 330); c.line_to(x - 140 + i * 70, y - 290)
        c.curve_to(x - 160 + i * 70, y - 270, x - 190 + i * 70, y - 270, x - 210 + i * 70, y - 290); c.close_path()
        relleno(c, ROJO if i % 2 == 0 else (1, 1, 1), 3)
    linea(c, [(x - 170, y - 330), (x - 170, y - 220)], 6); linea(c, [(x + 170, y - 330), (x + 170, y - 220)], 6)
    texto(c, "TACOS", x, y - 140, 64, ROJO, halo=(1, 1, 1))


def fondo_calle(c):
    cielo(c, (0.98, 0.7, 0.45), (0.98, 0.88, 0.7), 1100)
    nubes(c, 9, 150, 500, 4, (1, 0.9, 0.8))
    cols = [(0.95, 0.75, 0.55), (0.55, 0.75, 0.85), (0.95, 0.6, 0.6), (0.7, 0.85, 0.6), (0.98, 0.85, 0.5)]
    x = -40
    for i, col in enumerate(cols * 2):
        w = 230 + (i * 37) % 80; h = 420 + (i * 53) % 220
        c.rectangle(x, 1100 - h, w, h); relleno(c, col, 5)
        for wy in range(int(1100 - h + 50), 1020, 140):
            rrect(c, x + 40, wy, 60, 80, 6); relleno(c, (0.35, 0.4, 0.5), 3)
            if w > 250: rrect(c, x + 140, wy, 60, 80, 6); relleno(c, (0.35, 0.4, 0.5), 3)
        x += w
        if x > W + 50: break
    # banqueta y calle
    c.rectangle(0, 1100, W, 90); relleno(c, (0.78, 0.76, 0.72), 4)
    c.rectangle(0, 1190, W, H - 1190); c.set_source(degradado(1190, H, (0.35, 0.35, 0.38), (0.25, 0.25, 0.28))); c.fill()
    for xx in range(-40, W, 220): c.rectangle(xx, 1420, 120, 18); c.set_source_rgb(0.95, 0.85, 0.3); c.fill()
    puesto_tacos(c, 760, 1110)
    # papel picado
    for i in range(14):
        xx = i * 80 + 20; yy = 180 + math.sin(i) * 20
        c.move_to(xx, yy); c.line_to(xx + 60, yy + 6); c.line_to(xx + 58, yy + 70); c.line_to(xx + 2, yy + 64); c.close_path()
        relleno(c, [(0.95, 0.3, 0.5), (0.3, 0.7, 0.95), (0.98, 0.8, 0.2), (0.4, 0.8, 0.4)][i % 4], 2)
    linea(c, [(0, 178), (W, 190)], 3)


def fondo_cuarto(c):
    interior(c, (0.55, 0.58, 0.68), (0.42, 0.38, 0.4), 1450, zocalo=(0.3, 0.3, 0.35))
    ventana(c, 560, 300, 380, 520, c0=(0.05, 0.07, 0.16), c1=(0.2, 0.22, 0.38), paisaje=True)
    c.arc(820, 420, 40, 0, 7); relleno(c, (0.95, 0.94, 0.85), 0)
    # cama
    c.rectangle(-40, 1330, 520, 160); relleno(c, (0.4, 0.3, 0.25), 5)
    rrect(c, -40, 1270, 520, 90, 20); relleno(c, (0.75, 0.78, 0.85), 4)
    rrect(c, 20, 1230, 170, 70, 25); relleno(c, (0.95, 0.95, 0.95), 4)
    # luz de luna en el piso
    c.move_to(560, 820); c.line_to(940, 820); c.line_to(1100, 1900); c.line_to(400, 1900); c.close_path()
    c.set_source_rgba(0.8, 0.85, 1.0, 0.12); c.fill()


def calendario_pared(c, x, y, tachados=20, marca=None):
    c.save(); c.translate(x, y)
    rrect(c, -230, -260, 460, 520, 10); relleno(c, (0.97, 0.97, 0.95), 5)
    c.rectangle(-230, -260, 460, 90); c.set_source_rgb(*ROJO); c.fill()
    rrect(c, -230, -260, 460, 520, 10); c.set_source_rgb(*TINTA); c.set_line_width(5); c.stroke()
    texto(c, "MES", 0, -215, 52, (1, 1, 1))
    for i in range(35):
        cx, cy = -195 + (i % 7) * 65, -130 + (i // 7) * 75
        texto(c, str(i + 1) if i < 31 else "", cx, cy, 28, (0.3, 0.3, 0.3), MANO, peso=cairo.FONT_WEIGHT_BOLD)
        if i < tachados:
            linea(c, [(cx - 22, cy - 22), (cx + 22, cy + 22)], 6, ROJO, 0.85)
            linea(c, [(cx + 22, cy - 22), (cx - 22, cy + 22)], 6, ROJO, 0.85)
        if marca is not None and i == marca:
            c.arc(cx, cy, 32, 0, 7); c.set_source_rgb(*ROJO); c.set_line_width(5); c.stroke()
    c.restore()


def fondo_sierra(amanecer=True):
    def f(c):
        cielo(c, (0.25, 0.22, 0.4), (0.98, 0.55, 0.3), 1100)
        c.arc(540, 1080, 140, 0, 7); c.set_source_rgba(1, 0.85, 0.5, 0.9); c.fill()
        nubes(c, 11, 200, 700, 5, (0.95, 0.55, 0.45), 0.5)
        montanas(c, 1000, 380, (0.42, 0.3, 0.42), 21)
        montanas(c, 1100, 260, (0.3, 0.24, 0.32), 22, borde=3)
        suelo(c, 1100, (0.3, 0.3, 0.25), (0.2, 0.2, 0.17))
        r = random.Random(3)
        for i in range(26):
            x = r.uniform(-40, W + 40); y = r.uniform(1110, 1250)
            pino(c, x, y, r.uniform(0.5, 0.8), (0.15, 0.22, 0.18))
        rancho(c, 330, 1330, 420, 160)
        for i in range(12):
            x = i * 100 + r.uniform(-20, 20); y = 1500 + r.uniform(0, 300)
            pino(c, x, y + 200, r.uniform(1.0, 1.5), (0.12, 0.2, 0.15))
    return f


def silueta_punteada(c, x, y, s):
    c.save(); c.set_dash([18, 14]); c.set_source_rgba(1, 1, 1, 0.9); c.set_line_width(7)
    c.arc(x, y - 640 * s, 62 * s, 0, 7); c.stroke()
    c.move_to(x - 105 * s, y - 640 * s - 30 * s); c.curve_to(x - 60 * s, y - 760 * s, x + 60 * s, y - 760 * s, x + 105 * s, y - 670 * s); c.stroke()
    c.move_to(x - 55 * s, y - 560 * s); c.line_to(x + 55 * s, y - 560 * s); c.line_to(x + 45 * s, y - 360 * s)
    c.line_to(x - 45 * s, y - 360 * s); c.close_path(); c.stroke()
    for sx in (-1, 1):
        c.move_to(x + sx * 20 * s, y - 360 * s); c.line_to(x + sx * 30 * s, y); c.stroke()
        c.move_to(x + sx * 55 * s, y - 555 * s); c.line_to(x + sx * 90 * s, y - 380 * s); c.stroke()
    c.restore()


def balanza(t):
    def f(c, tt):
        ang = math.radians(-14 * suave((tt - 1.5) / 1.2) + 2 * math.sin(tt * 2))
        cx, cy = 540, 760
        c.rectangle(cx - 16, cy, 32, 640); relleno(c, (0.75, 0.6, 0.25), 4)
        c.move_to(cx - 150, cy + 660); c.line_to(cx + 150, cy + 660); c.line_to(cx + 90, cy + 610); c.line_to(cx - 90, cy + 610)
        c.close_path(); relleno(c, (0.7, 0.55, 0.2), 4)
        c.save(); c.translate(cx, cy); c.rotate(ang)
        c.rectangle(-420, -14, 840, 28); relleno(c, (0.85, 0.7, 0.3), 4)
        ends = [(-400, 0), (400, 0)]
        c.restore()
        c.arc(cx, cy, 30, 0, 7); relleno(c, (0.85, 0.7, 0.3), 4)
        for i, (ex, ey) in enumerate(ends):
            px = cx + ex * math.cos(ang) - ey * math.sin(ang); py = cy + ex * math.sin(ang) + ey * math.cos(ang)
            linea(c, [(px, py), (px - 130, py + 260)], 4); linea(c, [(px, py), (px + 130, py + 260)], 4)
            c.move_to(px - 170, py + 260); c.curve_to(px - 120, py + 340, px + 120, py + 340, px + 170, py + 260); c.close_path()
            relleno(c, (0.85, 0.7, 0.3), 4)
            if i == 0:
                for j in range(5):
                    billete(c, px - 60 + j * 30, py + 225 - j * 22, 1.0, math.radians(-10 + j * 8))
            else:
                c.save(); c.translate(px, py + 175); c.scale(0.9, 0.9)
                c.move_to(0, 60); c.curve_to(-110, -10, -60, -95, 0, -40); c.curve_to(60, -95, 110, -10, 0, 60)
                c.close_path(); relleno(c, ROJO, 6)
                c.restore()
    return f


def apreton(c, t):
    sep = suave((t - 4.2) / 1.0) * 160
    for lado in (-1, 1):
        c.save(); c.translate(540 + lado * sep, 900)
        col = (0.13, 0.14, 0.17) if lado < 0 else (0.62, 0.18, 0.16)
        c.move_to(lado * 700, 200); c.line_to(lado * 70, 20)
        c.set_source_rgb(*TINTA); c.set_line_width(150); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
        c.move_to(lado * 700, 200); c.line_to(lado * 70, 20); c.set_source_rgb(*col); c.set_line_width(134); c.stroke()
        c.save(); c.scale(1, 0.8); c.arc(lado * 10, 15, 95, 0, 7); c.restore(); relleno(c, PIEL, 8)
        for k in range(3):
            linea(c, [(lado * 60 - 30, -20 + k * 32), (lado * -60 + 30 * lado, -10 + k * 32)], 5, TINTA, 0.5)
        c.restore()
    if t > 4.0:
        k = clamp((t - 4.0) / 0.3)
        pts = [(540, 700), (520, 780), (560, 840), (515, 920), (555, 990), (530, 1100)]
        linea(c, pts[:max(2, int(len(pts) * k))], 9, (0.1, 0.1, 0.1))


def x_roja(c, x, y, s, k):
    if k <= 0: return
    a = [(x - 150 * s, y - 150 * s), (x + 150 * s, y + 150 * s)]; b = [(x + 150 * s, y - 150 * s), (x - 150 * s, y + 150 * s)]
    k1, k2 = clamp(k * 2), clamp(k * 2 - 1)
    for (p, q), kk in ((a, k1), (b, k2)):
        if kk > 0:
            e = (lerp(p[0], q[0], kk), lerp(p[1], q[1], kk))
            linea(c, [p, e], 46 * s, (1, 1, 1)); linea(c, [p, e], 30 * s, ROJO)


def podio(c, x, y):
    c.move_to(x - 120, y); c.line_to(x - 90, y - 300); c.line_to(x + 90, y - 300); c.line_to(x + 120, y); c.close_path()
    relleno(c, degradado(y - 300, y, (0.5, 0.35, 0.25), (0.35, 0.24, 0.17)), 5)
    c.arc(x, y - 200, 45, 0, 7); relleno(c, (0.85, 0.75, 0.3), 4)
    linea(c, [(x + 40, y - 300), (x + 20, y - 380)], 6); c.arc(x + 20, y - 390, 14, 0, 7); relleno(c, (0.2, 0.2, 0.2), 3)


def maletin(c, x, y):
    rrect(c, x - 60, y - 45, 120, 90, 10); relleno(c, (0.35, 0.22, 0.12), 4)
    c.arc(x, y - 45, 20, math.pi, 0); c.set_source_rgb(*TINTA); c.set_line_width(7); c.stroke()


def mapa_capa(c, t):
    mx, my, an = 70, 520, 940
    mapa_mexico(c, mx, my, an)
    jal = mapa_xy(-103.6, 20.3, mx, my, an)
    lugares = [(-103.6, 20.3), (-102.5, 19.2), (-104.0, 19.1), (-102.3, 21.9), (-101.0, 21.0), (-99.2, 19.4), (-100.3, 25.7),
               (-106.4, 23.2), (-110.9, 29.1), (-96.7, 17.1), (-92.6, 16.7), (-89.6, 21.0), (-86.9, 21.1), (-97.5, 22.3),
               (-116.9, 32.5), (-104.9, 21.5), (-103.4, 25.5), (-98.2, 19.0), (-93.1, 18.0), (-96.1, 19.2), (-101.7, 21.1),
               (-106.1, 28.6), (-99.9, 16.9), (-108.9, 25.8)]
    for i, (lo, la) in enumerate(lugares):
        t0 = 0.4 + i * 0.16
        if t < t0: continue
        k = rebote((t - t0) / 0.3)
        x, y = mapa_xy(lo, la, mx, my, an)
        g = cairo.RadialGradient(x, y, 0, x, y, 70 * k)
        g.add_color_stop_rgba(0, 0.9, 0.1, 0.1, 0.55); g.add_color_stop_rgba(1, 0.9, 0.1, 0.1, 0)
        c.set_source(g); c.arc(x, y, 70 * k, 0, 7); c.fill()
        c.arc(x, y, 13 * k, 0, 7); relleno(c, ROJO, 3)
    c.arc(*jal, 22, 0, 7); relleno(c, (0.6, 0.0, 0.0), 4)


def soldados_fila(xs, y, s, t0, desde=-300, dur=3.0, cara="serio"):
    return [Actor("soldado", [dict(t=0, pose="parado", x=x + desde, y=y, caminar=True, cara=cara),
                              dict(t=t0 + dur, pose="parado", x=x, y=y, cara=cara)], escala=s, semilla=10 + i)
            for i, x in enumerate(xs)]


def helis(lista):
    """lista de (x0, y0, x1, y1, s, luz)"""
    def f(c, t, dur=4.0):
        for (x0, y0, x1, y1, s, luz) in lista:
            k = clamp(t / dur)
            helicoptero(c, lerp(x0, x1, k), lerp(y0, y1, k) + math.sin(t * 2) * 8, s, t, f=-1 if x1 < x0 else 1, luz=luz)
    return f


def titulo_pantalla(txt, t0, y=260, tam=120, color=(1, 1, 1), halo=TINTA, t1=None):
    def f(c, t):
        if t < t0 or (t1 and t > t1): return
        k = rebote((t - t0) / 0.3)
        c.save(); c.translate(W / 2, y); c.scale(k, k); texto(c, txt, 0, 0, tam, color, MARKER, halo=halo); c.restore()
    return f


def dinero_cae(semilla=1, n=26, t0=0.0):
    rnd = random.Random(semilla)
    d = [(rnd.uniform(0, W), rnd.uniform(-600, 0), rnd.uniform(220, 380), rnd.uniform(0, 6), rnd.uniform(0.8, 1.3)) for _ in range(n)]
    def f(c, t):
        if t < t0: return
        tt = t - t0
        for (x, y, v, ph, s) in d:
            yy = y + tt * v
            if -100 < yy < H + 100: billete(c, x + math.sin(tt * 2 + ph) * 40, yy, s, math.sin(tt * 3 + ph) * 0.6)
    return f


def barrotes(t0):
    def f(c, t):
        if t < t0: return
        k = suave((t - t0) / 0.6)
        for i in range(8):
            x = 70 + i * 135
            y1 = lerp(-H, 0, k)
            c.rectangle(x - 16, y1, 32, H); relleno(c, degradado(0, 0, (0.2, 0.2, 0.22), (0.45, 0.45, 0.5), x - 16, x + 16), 4)
        for yy in (180, 1720):
            c.rectangle(0, lerp(-H, 0, k) + yy, W, 40); relleno(c, (0.25, 0.25, 0.28), 4)
    return f


def polvo(x, y, t0):
    def f(c, t):
        if t < t0: return
        r = random.Random(1)
        for i in range(14):
            k = ((t - t0) * 0.6 + i / 14) % 1
            c.arc(x - k * 300 + r.uniform(-40, 40), y - k * 120 + r.uniform(-40, 40), 30 + k * 60, 0, 7)
            c.set_source_rgba(0.8, 0.7, 0.55, 0.35 * (1 - k)); c.fill()
    return f


def convoy(c, t):
    for i, x0 in enumerate([1500, 2200]):
        x = x0 - t * 380
        camioneta(c, x, 1300 + i * 0, 0.85, -1)


# ------------------------------------------------------------------ escenas
def escenas():
    E = []
    def esc(i, *a, **k): E.append(Escena(C[i], C[i + 1], *a, **k))
    r = lambda i, t: t - C[i]   # tiempo de la voz -> tiempo dentro de la escena

    # 0 · POV hook
    i = 0
    yo = Actor("escolta", [dict(t=0, pose="guardia", x=330, y=1760, cara="serio", mira=0.2),
                           dict(t=2.2, pose="audifono", cara="serio", mira=-0.2), dict(t=3.6, pose="guardia", cara="serio")], escala=S)
    jefe = Actor("jefe", [dict(t=0, pose="cadera", x=780, y=1560, cara="serio", fac=-1)], escala=1.15, semilla=4)
    esc(i, fondo_rancho(camioneta_x=None), [jefe, yo,
        Etiqueta("TÚ", r(i, 1.2), 150, 860, (285, 990), tam=78),
        Etiqueta("EL MÁS\nBUSCADO", r(i, 3.2), 830, 760, (790, 900), tam=58, color=ROJO)],
        pantalla=[titulo_pantalla("POV:", 0.0, 230, 150), titulo_pantalla("ERES EL ESCOLTA", 1.1, 380, 82)],
        cam=(1.0, 1.08, (540, 1100), (540, 1150)))

    # 1 · proteger al más buscado
    i = 1
    yo = Actor("escolta", [dict(t=0, pose="parado", x=760, y=1780, cara="neutral", mira=-0.6, fac=-1),
                           dict(t=2.2, pose="pensar", cara="preocupado", mira=-0.6)], escala=S, semilla=2)
    def f1(c):
        fondo_oficina(c); cartel_se_busca(c, 100, 330, 470, 640)
    esc(i, f1, [yo, Etiqueta("TU JEFE", r(i, 7.2), 360, 1130, (330, 940), tam=70, color=ROJO, curva=-0.3)],
        cam=(1.02, 1.12, (500, 950), (420, 860)))

    # 2 · un solo error
    i = 2
    yo = Actor("escolta", [dict(t=0, pose="parado", x=540, y=2750, cara="preocupado", sudor=True, mira=0.0),
                           dict(t=1.2, pose="parado", cara="miedo", sudor=True)], escala=3.0, semilla=3)
    esc(i, lambda c: None, [fondo_rayos((0.55, 0.06, 0.06), (0.2, 0.02, 0.02)), yo,
        Etiqueta("UN SOLO\nERROR...", r(i, 10.5), 540, 330, None, tam=110, color=(1, 1, 1), halo=TINTA, rot=-4),
        Etiqueta("= TU VIDA", r(i, 12.2), 560, 1650, None, tam=96, color=(1, 0.85, 0.2), halo=TINTA, rot=3)],
        cam=(1.0, 1.12, (540, 1000), (540, 1050)), sacudidas=[r(i, 11.1)])

    # 3 · El Mencho
    i = 3
    jefe = Actor("jefe", [dict(t=0, pose="mesa", x=640, y=1560, cara="serio", fac=-1)], escala=1.3, semilla=4)
    yo = Actor("escolta", [dict(t=0, pose="guardia", x=250, y=1800, cara="serio", mira=0.6)], escala=S, semilla=2)
    def f3(c): fondo_oficina(c); silla(c, 700, 1560, -1, 280)
    def mesa3(c, t): mesa(c, 560, 1640, 560, 300); botella(c, 420, 1340, 0.8)
    esc(i, f3, [jefe, mesa3, yo,
        Etiqueta("NEMESIO OSEGUERA\nCERVANTES", r(i, 14.4), 600, 560, (660, 790), tam=56),
        Etiqueta("«EL MENCHO»", r(i, 17.5), 640, 380, None, tam=96, color=ROJO, rot=-5)],
        cam=(1.0, 1.1, (560, 1100), (600, 1000)))

    # 4 · líder del CJNG
    i = 4
    jefe = Actor("jefe", [dict(t=0, pose="mesa", x=640, y=1560, cara="serio", fac=-1, mira=-0.3)], escala=1.3, semilla=4)
    def tarjeta_cjng(c, w, h, t):
        c.set_source(degradado(0, h, (0.15, 0.15, 0.18), (0.05, 0.05, 0.07))); c.paint()
        texto(c, "LÍDER DEL", w / 2, h * 0.18, 52, (0.85, 0.85, 0.85))
        texto(c, "CJNG", w / 2, h * 0.45, 170, ROJO, halo=(1, 1, 1))
        texto(c, "CÁRTEL JALISCO\nNUEVA GENERACIÓN", w / 2, h * 0.78, 50, (1, 1, 1))
    esc(i, f3, [jefe, mesa3],
        pantalla=[Inserto(0.25, 90, 220, 900, 560, tarjeta_cjng)],
        cam=(1.25, 1.35, (640, 1050), (640, 1000)))

    # 5 · no es cualquier trabajo
    i = 5
    yo = Actor("escolta", [dict(t=0, pose="audifono", x=300, y=1800, cara="serio", mira=0.5)], escala=S, semilla=2)
    esc(i, fondo_rancho(camioneta_x=700), [yo,
        Etiqueta("AUDÍFONO", r(i, 22.0), 230, 780, (180, 990), tam=56),
        Etiqueta("CAMIONETA\nBLINDADA", r(i, 22.6), 800, 950, (760, 1180), tam=56)],
        cam=(1.0, 1.08, (540, 1150), (500, 1150)))

    # 6 · ni empresario ni político
    i = 6
    emp = Actor("empresario", [dict(t=0, pose="parado", x=280, y=1500, cara="feliz")], escala=1.05, semilla=5)
    pol = Actor("politico", [dict(t=0, pose="senalar", x=760, y=1500, cara="feliz", fac=-1)], escala=1.05, semilla=6)
    def capa6(c, t):
        maletin(c, 360, 1350); podio(c, 860, 1500)
        x_roja(c, 280, 1100, 1.0, (t - r(i, 24.6)) / 0.5)
        x_roja(c, 790, 1100, 1.0, (t - r(i, 25.6)) / 0.5)
    esc(i, fondo_papel(), [emp, pol, capa6,
        Etiqueta("EMPRESARIO", r(i, 24.7), 280, 560, None, tam=66, tachar=True),
        Etiqueta("POLÍTICO", r(i, 25.6), 790, 560, None, tam=66, tachar=True)],
        cam=(1.0, 1.05, (540, 1000), (540, 1000)))

    # 7 · de los más perseguidos (noche, helicóptero)
    i = 7
    jefe = Actor("jefe", [dict(t=0, pose="parado", x=720, y=1680, cara="preocupado", fac=-1, mira=-0.3)], escala=1.2, semilla=4)
    yo = Actor("escolta", [dict(t=0, pose="guardia", x=330, y=1800, cara="serio", mira=0.6),
                           dict(t=1.5, pose="senalar", cara="miedo", mira=0.6)], escala=S, semilla=2)
    esc(i, fondo_rancho(noche=True), [jefe, yo],
        frente=[helis([(1250, 320, 620, 300, 0.9, True)]),
                Etiqueta("PERSEGUIDO", r(i, 28.9), 800, 1000, (740, 1050), tam=62, color=ROJO, curva=0.5)],
        tinte=(0.7, 0.75, 0.95, 0.25), cam=(1.0, 1.08, (540, 1000), (560, 1050)))

    # 8 · tu vida cambia
    i = 8
    yo = Actor("escolta", [dict(t=0, pose="parado", x=-100, y=1760, caminar=True, cara="serio"),
                           dict(t=2.6, pose="parado", x=520, y=1760, cara="serio", mira=0.6),
                           dict(t=3.1, pose="parado", cara="preocupado", mira=-0.4)], escala=S, semilla=2)
    def f8(c):
        fondo_rancho()(c); reja(c, 0, 1300, 1080, 420)
    def cal8(c, w, h, t):
        c.set_source_rgb(0.96, 0.96, 0.94); c.paint(); calendario(c, w / 2, h / 2 + 10, 1.25, "1", "DÍA")
    esc(i, f8, [yo, Etiqueta("TU NUEVA VIDA", r(i, 32.9), 540, 640, (540, 870), tam=72)],
        pantalla=[Inserto(r(i, 31.2), 640, 1040, 380, 380, cal8)],
        cam=(1.0, 1.08, (540, 1150), (540, 1150)))

    # 9 · ya no puedes salir
    i = 9
    am1 = Actor("amigo", [dict(t=0, pose="saludo" if "saludo" in POSES else "senalar", x=620, y=1260, cara="feliz", fac=-1)], escala=0.75, semilla=7)
    am2 = Actor("amiga", [dict(t=0, pose="cadera", x=900, y=1270, cara="feliz", fac=-1)], escala=0.72, semilla=8)
    yo = Actor("escolta", [dict(t=0, pose="parado", x=280, y=1850, cara="triste", mira=0.6),
                           dict(t=3.0, pose="telefono", cara="triste", mira=0.3)], escala=S, semilla=2)
    def capa9(c, t): reja(c, 0, 1900, 1080, 760)
    esc(i, fondo_calle, [am1, am2, capa9, yo,
        Etiqueta("AMIGOS", r(i, 36.8), 760, 720, (720, 900), tam=64, tachar=True),
        Etiqueta("LA CALLE", r(i, 38.2), 700, 1560, (620, 1380), tam=64, tachar=True)],
        pantalla=[Inserto(r(i, 35.0), 600, 140, 440, 440, telefono, t1=r(i, 36.6))],
        cam=(1.0, 1.08, (540, 1100), (560, 1150)))

    # 10 · tensión, miedo, desconfianza
    i = 10
    yo = Actor("escolta", [dict(t=0, pose="cruzado", x=640, y=1820, cara="preocupado", mira=-0.4, sudor=True, fac=-1),
                           dict(t=2.8, pose="cruzado", cara="miedo", mira=0.5, sudor=True)], escala=S, semilla=2)
    esc(i, fondo_cuarto, [yo,
        Etiqueta("TENSIÓN", r(i, 42.0), 360, 560, None, tam=86, color=(1, 1, 1), halo=TINTA, rot=-6),
        Etiqueta("MIEDO", r(i, 43.0), 300, 820, None, tam=96, color=(1, 0.85, 0.2), halo=TINTA, rot=4),
        Etiqueta("DESCONFIANZA", r(i, 43.5), 540, 1080, None, tam=82, color=ROJO, halo=(1, 1, 1), rot=-3)],
        tinte=(0.55, 0.6, 0.85, 0.5), cam=(1.0, 1.08, (540, 1100), (540, 1120)), sacudidas=[r(i, 43.0)])

    # 11 · tu último día
    i = 11
    yo = Actor("escolta", [dict(t=0, pose="parado", x=760, y=1830, cara="serio", mira=-0.7, fac=-1),
                           dict(t=2.0, pose="pensar", cara="preocupado", mira=-0.7, sudor=True)], escala=S, semilla=2)
    def f11(c):
        interior(c, (0.6, 0.62, 0.7), (0.42, 0.38, 0.4), 1450, zocalo=(0.3, 0.3, 0.35)); lampara(c, 540, 92)
    def cal11(c, t):
        k = int(clamp(t / 3.4) * 22)
        calendario_pared(c, 330, 760, tachados=k, marca=k)
    esc(i, f11, [cal11, yo, Etiqueta("¿HOY?", r(i, 47.9), 380, 360, (340, 520), tam=100, color=ROJO)],
        tinte=(0.75, 0.75, 0.9, 0.35), cam=(1.0, 1.1, (480, 1000), (420, 900)))

    # 12 · buscado por las autoridades
    i = 12
    sold = [Actor("soldado", [dict(t=0, pose=p, x=x, y=1800, cara="serio", fac=fc, mira=m)], escala=1.25, semilla=12 + k)
            for k, (x, p, fc, m) in enumerate([(200, "senalar", 1, 0.5), (880, "cruzado", -1, -0.5)])]
    def f12(c):
        interior(c, (0.7, 0.72, 0.68), (0.45, 0.45, 0.42), 1450, zocalo=(0.3, 0.35, 0.25))
        rrect(c, 140, 220, 800, 920, 10); relleno(c, (0.72, 0.56, 0.38), 6)
        cartel_se_busca(c, 330, 280, 420, 580)
        for (x, y) in [(200, 330), (820, 300), (230, 980), (800, 950)]:
            c.rectangle(x - 60, y - 70, 120, 140); relleno(c, (0.97, 0.97, 0.95), 3)
            for k in range(4): linea(c, [(x - 40, y - 40 + k * 25), (x + 40, y - 40 + k * 25)], 3, TINTA, 0.4)
        for (x, y) in [(200, 330), (820, 300), (230, 980), (800, 950)]:
            linea(c, [(540, 560), (x, y)], 4, ROJO, 0.9)
        for (x, y) in [(200, 330), (820, 300), (230, 980), (800, 950), (540, 560)]:
            c.arc(x, y - 60, 10, 0, 7); relleno(c, ROJO, 2)
    esc(i, f12, sold + [Etiqueta("AUTORIDADES\nMEXICANAS", r(i, 51.9), 540, 1300, (230, 1060), tam=58, curva=-0.3)],
        cam=(1.0, 1.08, (540, 900), (540, 960)))

    # 13 · fundador y líder
    i = 13
    esc(i, fondo_corcho, [organigrama(0),
        Etiqueta("FUNDADOR", r(i, 54.1), 230, 260, (380, 420), tam=62, color=(1, 1, 1), halo=TINTA),
        Etiqueta("Y LÍDER", r(i, 54.9), 860, 260, (710, 420), tam=62, color=(1, 0.85, 0.2), halo=TINTA, curva=-0.35)],
        cam=(1.0, 1.06, (540, 900), (540, 860)))

    # 14 · territorios
    i = 14
    esc(i, fondo_papel((0.75, 0.85, 0.92)), [mapa_capa,
        Etiqueta("JALISCO", r(i, 58.4), 330, 1500, (395, 1250), tam=64, color=ROJO),
        Etiqueta("NUMEROSOS\nTERRITORIOS", r(i, 60.6), 700, 1650, None, tam=66)],
        pantalla=[titulo_pantalla("SU EXPANSIÓN", 0.1, 280, 96, TINTA, (1, 1, 1))],
        cam=(1.0, 1.06, (540, 1000), (520, 1060)))

    # 15 · justo al lado
    i = 15
    yo = Actor("escolta", [dict(t=0, pose="parado", x=-40, y=1800, caminar=True, cara="serio", mira=0.5),
                           dict(t=3.2, pose="guardia", x=380, y=1800, cara="serio", mira=0.6)], escala=S, semilla=2)
    jefe = Actor("jefe", [dict(t=0, pose="parado", x=230, y=1760, caminar=True, cara="serio"),
                          dict(t=3.2, pose="cadera", x=720, y=1760, cara="serio", fac=-1)], escala=1.3, semilla=4)
    def medida(c, t):
        if t < r(i, 63.4): return
        k = suave((t - r(i, 63.4)) / 0.4)
        a, b = 470, lerp(470, 630, k)
        linea(c, [(a, 1050), (b, 1050)], 6, ROJO); linea(c, [(a, 1025), (a, 1075)], 6, ROJO); linea(c, [(b, 1025), (b, 1075)], 6, ROJO)
    esc(i, fondo_rancho(), [jefe, yo, medida,
        Etiqueta("A CENTÍMETROS", r(i, 63.6), 550, 960, None, tam=52, color=ROJO, rot=0),
        Etiqueta("TÚ", r(i, 62.6), 200, 820, (320, 960), tam=72),
        Etiqueta("ÉL", r(i, 64.4), 900, 840, (780, 960), tam=72)],
        cam=(1.0, 1.08, (540, 1150), (560, 1150)))

    # 16 · cuando él se mueve
    i = 16
    jefe = Actor("jefe", [dict(t=0, pose="parado", x=1000, y=1780, caminar=True, cara="serio", fac=-1),
                          dict(t=2.0, pose="parado", x=720, y=1780, cara="serio", fac=-1)], escala=1.3, semilla=4)
    yo = Actor("escolta", [dict(t=0, pose="abrir", x=260, y=1820, cara="serio", mira=0.7),
                           dict(t=1.6, pose="abrir", cara="lado", mira=-1)], escala=S, semilla=2)
    def f16(c):
        cielo(c, (0.45, 0.65, 0.92), (0.95, 0.88, 0.75), 1150); nubes(c, 4, 150, 500)
        montanas(c, 1050, 300, (0.6, 0.66, 0.75), 14); montanas(c, 1150, 200, (0.5, 0.58, 0.45), 15, borde=3)
        suelo(c, 1150, (0.8, 0.68, 0.52), (0.62, 0.5, 0.36))
        c.move_to(0, 1250); c.line_to(W, 1220); c.line_to(W, 1480); c.line_to(0, 1520); c.close_path()
        relleno(c, (0.68, 0.57, 0.43), 0)
        for (x, y, s) in [(950, 1210, 0.8), (80, 1230, 0.9)]: agave(c, x, y, s)
        camioneta(c, 330, 1560, 1.25, 1)
    esc(i, f16, [convoy, jefe, yo, polvo(1100, 1290, 0.0),
        Etiqueta("¡ALERTA!", r(i, 68.9), 300, 640, None, tam=96, color=ROJO, rot=-6)],
        cam=(1.0, 1.08, (540, 1200), (500, 1200)))

    # 17 · reunión
    i = 17
    def f17(c):
        interior(c, (0.8, 0.72, 0.6), (0.5, 0.36, 0.26), 1380, zocalo=(0.45, 0.25, 0.18))
        lampara(c, 540, 92); ventana(c, 90, 330, 280, 400); ventana(c, 710, 330, 280, 400)
        silla(c, 210, 1640, 1, 280); silla(c, 880, 1640, -1, 280)
    jefe = Actor("jefe", [dict(t=0, pose="mesa", x=230, y=1640, cara="serio")], escala=1.2, semilla=4)
    socio = Actor("socio", [dict(t=0, pose="mesa", x=860, y=1640, cara="neutral", fac=-1)], escala=1.2, semilla=9)
    socio2 = Actor("socio2", [dict(t=0, pose="cruzado", x=940, y=1580, cara="serio", fac=-1)], escala=1.15, semilla=11)
    yo = Actor("escolta", [dict(t=0, pose="guardia", x=110, y=1620, cara="lado", mira=1.0)], escala=1.3, semilla=2)
    def mesa17(c, t):
        mesa(c, 545, 1700, 640, 310, (0.4, 0.27, 0.18)); botella(c, 470, 1390, 0.85); botella(c, 600, 1390, 0.7, (0.3, 0.45, 0.25))
    reunion = [socio2, yo, jefe, socio, mesa17]
    esc(i, f17, reunion + [Etiqueta("ATENTO A TODO", r(i, 71.5), 330, 620, (160, 790), tam=60)],
        cam=(1.0, 1.08, (540, 1150), (500, 1100)))

    # 18 · el ambiente cambia
    i = 18
    jefe = Actor("jefe", [dict(t=0, pose="mesa", x=230, y=1640, cara="serio"), dict(t=1.5, pose="mesa", cara="enojado")], escala=1.2, semilla=4)
    socio = Actor("socio", [dict(t=0, pose="mesa", x=860, y=1640, cara="serio", fac=-1),
                            dict(t=1.2, pose="senalar", cara="enojado", fac=-1)], escala=1.2, semilla=9)
    socio2 = Actor("socio2", [dict(t=0, pose="cruzado", x=940, y=1580, cara="enojado", fac=-1)], escala=1.15, semilla=11)
    yo = Actor("escolta", [dict(t=0, pose="guardia", x=110, y=1620, cara="miedo", mira=1.0, sudor=True)], escala=1.3, semilla=2)
    esc(i, f17, [socio2, yo, jefe, socio, mesa17,
        Etiqueta("ALGO NO\nESTÁ BIEN...", r(i, 75.0), 560, 560, None, tam=84, color=(1, 1, 1), halo=TINTA, rot=-4)],
        tinte=lambda t: (1.0, 0.45, 0.4, clamp(t / 1.5) * 0.45), cam=(1.05, 1.18, (500, 1100), (420, 1050)),
        sacudidas=[r(i, 76.4)])

    # 19 · dinero
    i = 19
    yo = Actor("escolta", [dict(t=0, pose="dinero", x=540, y=1820, cara="serio", mira=0.2)], escala=1.6, semilla=2)
    def mano_billetes(c, t):
        st = yo.estado(t)  # no se usa: los billetes salen cerca de la mano arriba
        for k in range(4): billete(c, 760 + k * 12, 690 - k * 18, 1.2, math.radians(-30 + k * 14))
    esc(i, fondo_papel((0.85, 0.92, 0.82)), [dinero_cae(3, 22), yo, mano_billetes,
        Etiqueta("NO IMPORTA\nCUÁNTO TE PAGUEN", r(i, 77.7), 540, 330, None, tam=70, rot=-3)],
        cam=(1.0, 1.06, (540, 1000), (540, 1000)))

    # 20 · lealtad
    i = 20
    def leal(c, t):
        a = 1 - clamp((t - 4.0) / 1.5)
        c.save(); c.push_group(); texto(c, "LEALTAD", 540, 520, 120, (1, 0.85, 0.2), halo=TINTA)
        c.pop_group_to_source(); c.paint_with_alpha(a); c.restore()
    esc(i, lambda c: (c.set_source(degradado(0, H, (0.18, 0.18, 0.22), (0.06, 0.06, 0.08))), c.paint()),
        [apreton, leal], pantalla=[titulo_pantalla("¿DE QUIÉN TE FÍAS?", 1.2, 1520, 76, (1, 1, 1), TINTA)],
        cam=(1.0, 1.1, (540, 900), (540, 920)), sacudidas=[4.1])

    # 21 · el día que todos temían
    i = 21
    esc(i, fondo_sierra(), [Etiqueta("TAPALPA, JALISCO", r(i, 86.2), 540, 1450, (540, 1250), tam=66, color=(1, 1, 1), halo=TINTA)],
        pantalla=[titulo_pantalla("EL DÍA QUE\nTODOS TEMÍAN", 0.6, 330, 92, (1, 1, 1), TINTA)],
        cam=(1.0, 1.1, (540, 1000), (540, 1150)))

    # 22 · 22 de febrero de 2026
    i = 22
    def cal22(c, w, h, t):
        c.set_source_rgb(0.96, 0.96, 0.94); c.paint(); calendario(c, w / 2, h / 2 + 12, 1.3, "22", "FEBRERO", "2026")
    esc(i, fondo_sierra(), [helis([(1300, 500, 300, 420, 0.75, False), (1700, 700, 700, 640, 0.6, False), (1900, 360, 950, 300, 0.5, False)]),
        Etiqueta("FUERZAS\nMILITARES", r(i, 91.6), 760, 900, (560, 690), tam=64, color=(1, 1, 1), halo=TINTA)],
        pantalla=[Inserto(r(i, 88.9), 60, 1180, 400, 420, cal22)],
        cam=(1.0, 1.06, (540, 900), (540, 950)))

    # 23 · operativo
    i = 23
    yo = Actor("escolta", [dict(t=0, pose="agachado", x=820, y=1850, cara="miedo", fac=-1, sudor=True, mira=-1)], escala=S, semilla=2)
    sold = soldados_fila([120, 300, 470], 1640, 1.0, 0, desde=-500, dur=2.6)
    esc(i, fondo_rancho(camioneta_x=None), sold + [lambda c, t: camioneta(c, 760, 1700, 1.2, -1), yo],
        frente=[helis([(1200, 260, 700, 330, 0.85, False), (-300, 520, 250, 470, 0.6, False)]),
                Etiqueta("OPERATIVO", r(i, 93.9), 540, 700, None, tam=100, color=ROJO, rot=-5)],
        cam=(1.0, 1.08, (540, 1150), (600, 1150)), sacudidas=[r(i, 94.3), r(i, 95.5)])

    # 24 · murió
    i = 24
    def f24(c):
        fondo_oficina(c)
        silla(c, 600, 1560, -1, 280)
        c.save(); c.translate(820, 1620); c.rotate(math.radians(12))
        h = Actor("jefe", [dict(t=0, pose="parado", x=0, y=0, cara="serio")], escala=1.0)
        r_ = 62
        c.move_to(-r_ * 1.75, 0); c.curve_to(-r_ * 1.2, r_ * 0.35, r_ * 1.2, r_ * 0.35, r_ * 1.75, 0)
        c.curve_to(r_ * 1.3, r_ * 0.1, r_ * 0.9, -r_ * 0.1, r_ * 0.7, -r_ * 0.15)
        c.curve_to(r_ * 0.75, -r_ * 0.95, r_ * 0.2, -r_ * 1.05, 0, -r_ * 0.8)
        c.curve_to(-r_ * 0.2, -r_ * 1.05, -r_ * 0.75, -r_ * 0.95, -r_ * 0.7, -r_ * 0.15)
        c.curve_to(-r_ * 0.9, -r_ * 0.1, -r_ * 1.3, r_ * 0.1, -r_ * 1.75, 0); c.close_path()
        relleno(c, degradado(-r_, r_ * 0.3, (0.93, 0.88, 0.74), (0.72, 0.64, 0.48)), 5)
        c.restore()
    esc(i, f24, [Etiqueta("EL LÍDER DEL CJNG", r(i, 97.9), 540, 1040, None, tam=70),
                 Etiqueta("MURIÓ", r(i, 99.6), 760, 1250, (810, 1540), tam=96, color=ROJO)],
        tinte=(0.7, 0.72, 0.85, 0.45), cam=(1.0, 1.15, (600, 1150), (760, 1350)))

    # 25 · tu mundo cambia
    i = 25
    yo = Actor("escolta", [dict(t=0, pose="sorpresa", x=540, y=1800, cara="sorpresa"),
                           dict(t=1.6, pose="manos_cara", cara="miedo", sudor=True)], escala=1.6, semilla=2)
    esc(i, lambda c: None, [fondo_rayos((0.25, 0.25, 0.3), (0.08, 0.08, 0.1), 24), yo],
        pantalla=[titulo_pantalla("TU MUNDO CAMBIA", 1.4, 330, 96, (1, 1, 1), TINTA)],
        cam=(1.0, 1.14, (540, 1100), (540, 1000)), sacudidas=[0.15, 1.8])

    # 26 · ya no está
    i = 26
    yo = Actor("escolta", [dict(t=0, pose="guardia", x=330, y=1800, cara="serio", mira=0.6),
                           dict(t=1.8, pose="triste", cara="triste", mira=0.8)], escala=S, semilla=2)
    esc(i, fondo_rancho(), [lambda c, t: silueta_punteada(c, 720, 1780, 1.3), yo,
        Etiqueta("YA NO ESTÁ", r(i, 106.6), 760, 600, (740, 760), tam=80, color=ROJO)],
        tinte=(0.8, 0.8, 0.88, 0.4), cam=(1.0, 1.08, (540, 1150), (560, 1150)))

    # 27 · nueva etapa
    i = 27
    yo = Actor("escolta", [dict(t=0, pose="pensar", x=540, y=2050, cara="pensar", mira=-0.4),
                           dict(t=3.5, pose="pensar", cara="preocupado", mira=0.4)], escala=1.25, semilla=2)
    esc(i, fondo_corcho, [organigrama(0, cabeza_vacia=True, tiembla=6), yo,
        Etiqueta("NUEVA ETAPA", r(i, 109.2), 540, 200, None, tam=80, color=(1, 1, 1), halo=TINTA)],
        cam=(1.0, 1.07, (540, 900), (540, 1000)))

    # 28 · ¿vale la pena?
    i = 28
    yo = Actor("escolta", [dict(t=0, pose="pensar", x=880, y=1880, cara="pensar", mira=-0.6, fac=-1)], escala=1.15, semilla=2)
    esc(i, fondo_papel((0.93, 0.9, 0.84)), [balanza(0), yo,
        Etiqueta("DINERO", r(i, 113.6), 220, 1350, None, tam=60, color=(0.15, 0.45, 0.2)),
        Etiqueta("TU VIDA", r(i, 114.5), 860, 1150, None, tam=60, color=ROJO)],
        pantalla=[titulo_pantalla("¿VALE LA PENA?", 0.2, 300, 110, ROJO, (1, 1, 1))],
        cam=(1.0, 1.06, (540, 1000), (540, 1050)))

    # 29 · dinero y poder
    i = 29
    yo = Actor("escolta", [dict(t=0, pose="cadera", x=380, y=1800, cara="serio", mira=0.3),
                           dict(t=3.2, pose="dinero", cara="feliz", mira=0.3)], escala=S, semilla=2)
    esc(i, fondo_rancho(camioneta_x=760), [yo, dinero_cae(7, 18, 3.6),
        Etiqueta("DINERO", r(i, 123.2), 260, 640, None, tam=84, color=(0.15, 0.55, 0.25), rot=-6),
        Etiqueta("PODER", r(i, 123.8), 800, 700, None, tam=84, color=(0.85, 0.6, 0.1), rot=5)],
        tinte=(1.0, 0.92, 0.75, 0.25), cam=(1.0, 1.08, (540, 1150), (500, 1150)))

    # 30 · condena
    i = 30
    yo = Actor("escolta", [dict(t=0, pose="triste", x=540, y=1800, cara="triste", mira=0)], escala=S, semilla=2)
    esc(i, fondo_rancho(), [yo],
        frente=[barrotes(r(i, 125.4)), Etiqueta("CONDENA", r(i, 126.7), 540, 520, None, tam=130, color=ROJO, rot=-4)],
        tinte=lambda t: (0.6, 0.62, 0.7, clamp(t / 1.5) * 0.6), cam=(1.0, 1.1, (540, 1100), (540, 1050)),
        sacudidas=[r(i, 125.9)])
    return E


# ------------------------------------------------------------------ sonido (sintetizado)
SR = 44100
def _t(d): return np.arange(int(SR * d)) / SR

def whoosh(d=0.5, sem=1):
    n = np.random.default_rng(sem).standard_normal(int(SR * d))
    k = np.sin(np.pi * np.arange(len(n)) / len(n)) ** 2
    out = np.convolve(n, np.ones(40) / 40, "same")
    return out * k * 1.4

def pop(d=0.1):
    t = _t(d); f = 700 * np.exp(-t * 30) + 220
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 40) * 0.45

def golpe():
    t = _t(1.2)
    s = np.sin(2 * np.pi * (45 + 60 * np.exp(-t * 12)) * t) * np.exp(-t * 3.5)
    n = np.random.default_rng(3).standard_normal(len(t)) * np.exp(-t * 18) * 0.4
    return (s + np.convolve(n, np.ones(20) / 20, "same")) * 0.9

def latido():
    t = _t(0.16); g = np.sin(2 * np.pi * (55 + 35 * np.exp(-t * 30)) * t) * np.exp(-t * 22)
    s = np.zeros(int(SR * 0.45)); s[:len(g)] += g; s[int(SR * 0.2):int(SR * 0.2) + len(g)] += g * 0.7
    return s

def rotor(d):
    t = _t(d); n = np.random.default_rng(5).standard_normal(len(t))
    n = np.convolve(n, np.ones(60) / 60, "same")
    am = (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 11 * t))) * 0.8 + 0.2
    fade = np.minimum(1, np.minimum(t / 0.8, (d - t) / 0.8))
    return n * am * fade * 2.2

def musica(dur):
    """Fondo tenso: dron grave en Re menor + pulso suave + campanita lejana."""
    t = _t(dur); s = np.zeros_like(t)
    for f, a in [(36.7, 0.35), (73.4, 0.22), (110.0, 0.12), (87.3, 0.08)]:
        s += np.sin(2 * np.pi * f * t + np.sin(2 * np.pi * 0.07 * t) * 2) * a
    s *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t) ** 2
    beat = 60 / 76
    for k in range(int(dur / beat)):
        o = int(k * beat * SR); g = np.sin(2 * np.pi * 50 * _t(0.25)) * np.exp(-_t(0.25) * 18) * (0.5 if k % 2 else 0.3)
        e = min(len(s), o + len(g)); s[o:e] += g[:e - o]
    for k in range(int(dur / (beat * 8))):
        o = int(k * beat * 8 * SR); tt = _t(2.5)
        g = np.sin(2 * np.pi * [587, 698, 523, 440][k % 4] * tt) * np.exp(-tt * 2.2) * 0.05
        e = min(len(s), o + len(g)); s[o:e] += g[:e - o]
    fade = np.minimum(1, np.minimum(t / 1.5, (dur - t) / 1.5))
    return s * fade


def mezcla_audio(voz_wav, ruta, escenas_):
    with wave.open(voz_wav) as w:
        voz = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    n = int(SR * DUR) + SR
    fx = np.zeros(n)
    def poner(t, x, v=1.0):
        o = int(t * SR); e = min(n, o + len(x)); fx[o:e] += x[:e - o] * v
    for k, tc in enumerate(C[1:-1]): poner(tc - 0.25, whoosh(0.5, k), 0.35)
    for e in escenas_:
        for cap in e.capas + e.frente:
            if isinstance(cap, Etiqueta): poner(e.t0 + cap.t0, pop(), 0.5)
        for ts, _ in e.sac: poner(e.t0 + ts, golpe(), 0.7)
    poner(C[7], rotor(C[8] - C[7]), 0.25)
    poner(C[22], rotor(C[24] - C[22]), 0.3)
    for tt in np.arange(C[10], C[12], 0.9): poner(tt, latido(), 0.5)
    poner(C[25], golpe(), 0.8)
    mus = musica(DUR); m = np.zeros(n); m[:len(mus)] = mus
    v = np.zeros(n); v[:len(voz)] = voz[:n]
    total = v * 1.0 + m * 0.11 + fx * 0.22
    total = total / max(1e-6, np.abs(total).max()) * 0.9
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((total * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------ main
def _tramo(args):
    a, b, ruta = args
    render_tramo(escenas(), a, b, ruta); return ruta


if __name__ == "__main__":
    os.makedirs(os.path.join(SAL, "fotos"), exist_ok=True)
    if "--fotos" in sys.argv:
        from PIL import Image
        es = escenas()
        sel = [int(x) for x in sys.argv[sys.argv.index("--fotos") + 1].split(",")] if len(sys.argv) > sys.argv.index("--fotos") + 1 else range(len(es))
        for k in sel:
            e = es[k]; t = e.t0 + (e.t1 - e.t0) * 0.8
            Image.fromarray(cuadro_video(es, t)).save(os.path.join(SAL, "fotos", f"esc_{k:02d}.png"))
            print("foto", k, round(t, 2))
        sys.exit()
    voz = sys.argv[sys.argv.index("--voz") + 1] if "--voz" in sys.argv else os.path.join(SAL, "voz.mp3")
    vw = os.path.join(SAL, "voz.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", voz, "-ac", "1", "-ar", str(SR), vw], check=True)
    mezcla_audio(vw, os.path.join(SAL, "mezcla.wav"), escenas())
    n = os.cpu_count() or 4
    cortes = np.linspace(0, DUR, n * 2 + 1)
    tareas = [(round(cortes[k] * FPS) / FPS, round(cortes[k + 1] * FPS) / FPS, os.path.join(SAL, f"parte_{k:02d}.mp4")) for k in range(len(cortes) - 1)]
    with ProcessPoolExecutor(n) as ex:
        for p in ex.map(_tramo, tareas): print("listo", os.path.basename(p), flush=True)
    lista = os.path.join(SAL, "lista.txt")
    open(lista, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for _, _, p in tareas))
    final = os.path.join(SAL, "escolta.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lista, "-i", os.path.join(SAL, "mezcla.wav"),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", final], check=True)
    for _, _, p in tareas: os.remove(p)
    print("VIDEO:", final)
