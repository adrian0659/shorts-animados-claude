"""Escena de demostración «estilo referencia»: taller mecánico, mecánico y cliente con traje.

Monigotes con cabeza blanca grande, pelo, ropa, guantes y zapatos, sobre un escenario
detallado dibujado con código (pared, carteles, ventana, escritorio, auto con capó abierto).

Ejecutar desde la carpeta stickman/:
    python3 ejemplos/taller.py --foto   # una foto -> salida/taller.png
    python3 ejemplos/taller.py          # clip de 6 s -> salida/taller.mp4
"""
import os, sys, math, subprocess
import numpy as np
import cairo

W, H, FPS, DUR = 1080, 1920, 30, 6.0
TINTA = (0.07, 0.07, 0.09)
BLANCO = (1, 1, 1)
LINEA = 7
os.makedirs("salida", exist_ok=True)


# ------------------------------------------------------------------ utilidades
def suave(k):
    k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)

def borde(ctx, relleno, g=LINEA):
    ctx.set_source_rgb(*relleno); ctx.fill_preserve()
    ctx.set_source_rgb(*TINTA); ctx.set_line_width(g)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()

def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()

def poly(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]: ctx.line_to(*p)
    ctx.close_path()

def texto(ctx, txt, x, y, tam, color, peso=cairo.FONT_WEIGHT_BOLD, centro=True, contorno=None):
    ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, peso); ctx.set_font_size(tam)
    e = ctx.text_extents(txt)
    ctx.move_to(x - (e.width / 2 + e.x_bearing if centro else 0), y)
    ctx.text_path(txt)
    if contorno:
        ctx.set_source_rgb(*contorno); ctx.set_line_width(tam * 0.16)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
    ctx.set_source_rgb(*color); ctx.fill()

def trazo(ctx, pts, ancho, color=TINTA):
    ctx.set_source_rgb(*color); ctx.set_line_width(ancho)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*pts[0])
    for p in pts[1:]: ctx.line_to(*p)
    ctx.stroke()

def manga(ctx, pts, ancho, color):
    """Manga larga: trazo grueso con contorno."""
    trazo(ctx, pts, ancho + LINEA * 2, TINTA); trazo(ctx, pts, ancho, color)

def guante(ctx, x, y, ang=0, s=1.0):
    ctx.save(); ctx.translate(x, y); ctx.rotate(math.radians(ang)); ctx.scale(s, s)
    ctx.move_to(-22, -18); ctx.curve_to(-30, 10, -20, 30, 2, 30)
    ctx.curve_to(26, 30, 32, 6, 26, -16); ctx.curve_to(18, -30, -14, -30, -22, -18); ctx.close_path()
    borde(ctx, BLANCO, 6)
    # pulgar
    ctx.move_to(22, -6); ctx.curve_to(40, -14, 44, 2, 28, 10); borde(ctx, BLANCO, 6)
    ctx.restore()

def zapato(ctx, x, y, dir=1):
    ctx.save(); ctx.translate(x, y); ctx.scale(dir, 1)
    ctx.move_to(-28, -30); ctx.curve_to(-30, -6, -32, 4, -20, 6); ctx.line_to(48, 6)
    ctx.curve_to(66, 6, 62, -22, 36, -26); ctx.curve_to(18, -30, 6, -44, -28, -30); ctx.close_path()
    borde(ctx, (0.12, 0.12, 0.14), 5)
    ctx.set_source_rgba(1, 1, 1, 0.25); ctx.set_line_width(5)
    ctx.move_to(14, -28); ctx.curve_to(30, -22, 44, -18, 50, -10); ctx.stroke()
    ctx.restore()

def sombra(ctx, x, y, rx, ry, a=0.16):
    ctx.save(); ctx.translate(x, y); ctx.scale(rx, ry); ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore(); ctx.set_source_rgba(0, 0, 0, a); ctx.fill()


# ------------------------------------------------------------------ caras
def cabeza(ctx, cx, cy, r):
    ctx.arc(cx, cy, r, 0, 2 * math.pi); borde(ctx, BLANCO, LINEA)
    # luz suave en la parte de abajo para dar volumen
    ctx.save(); ctx.arc(cx, cy, r - LINEA / 2, 0, 2 * math.pi); ctx.clip()
    g = cairo.RadialGradient(cx - r * 0.3, cy - r * 0.4, r * 0.2, cx, cy, r * 1.1)
    g.add_color_stop_rgba(0, 1, 1, 1, 0); g.add_color_stop_rgba(1, 0.75, 0.78, 0.85, 0.45)
    ctx.set_source(g); ctx.paint(); ctx.restore()

def ojos(ctx, cx, cy, r, mira=0.0, parpadeo=False, ceño=0.0):
    for lado in (-1, 1):
        ex, ey = cx + lado * r * 0.33 + mira * r * 0.12, cy - r * 0.02
        ctx.set_source_rgb(*TINTA)
        if parpadeo:
            ctx.set_line_width(r * 0.07); ctx.move_to(ex - r * 0.09, ey); ctx.line_to(ex + r * 0.09, ey); ctx.stroke()
        else:
            ctx.save(); ctx.translate(ex, ey); ctx.scale(r * 0.085, r * 0.15)
            ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); ctx.fill()
            ctx.set_source_rgb(1, 1, 1); ctx.arc(ex + r * 0.025, ey - r * 0.06, r * 0.028, 0, 2 * math.pi); ctx.fill()
        # ceja: ceño > 0 = enojado (baja hacia el centro)
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(r * 0.075); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        bx = ex
        ctx.move_to(bx - lado * r * 0.16, ey - r * 0.27 - ceño * r * 0.02)
        ctx.line_to(bx + lado * r * 0.14, ey - r * 0.27 + ceño * r * 0.12); ctx.stroke()

def boca(ctx, cx, cy, r, abierta=0.0, mira=0.0):
    mx, my = cx + mira * r * 0.12, cy + r * 0.42
    ctx.set_source_rgb(*TINTA)
    if abierta > 0.15:
        ctx.save(); ctx.translate(mx, my); ctx.scale(r * 0.13, r * 0.08 * abierta + r * 0.02)
        ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore(); ctx.fill()
    else:
        ctx.set_line_width(r * 0.06); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(mx - r * 0.14, my); ctx.line_to(mx + r * 0.12, my - r * 0.01); ctx.stroke()

def pelo_puntas(ctx, cx, cy, r):
    """Pelo negro despeinado (mecánico)."""
    pts = []
    picos = [(190, 1.08), (200, 1.32), (212, 1.12), (222, 1.45), (236, 1.18), (250, 1.55), (262, 1.22),
             (276, 1.5), (290, 1.2), (304, 1.48), (318, 1.16), (332, 1.38), (344, 1.1), (356, 1.3), (6, 1.02)]
    for a, k in picos:
        ar = math.radians(a); pts.append((cx + math.cos(ar) * r * k, cy + math.sin(ar) * r * k))
    # flequillo con puntas hacia abajo sobre la frente
    fl = [(0.98, -0.12), (0.78, -0.42), (0.62, -0.08), (0.42, -0.4), (0.22, -0.02), (0.02, -0.38),
          (-0.2, -0.04), (-0.38, -0.4), (-0.58, -0.1), (-0.76, -0.42), (-0.98, -0.05)]
    for fx, fy in fl: pts.append((cx + fx * r, cy + fy * r))
    poly(ctx, pts); borde(ctx, (0.08, 0.08, 0.1), 5)

def pelo_peinado(ctx, cx, cy, r):
    """Pelo castaño con raya al costado (cliente)."""
    c = (0.48, 0.3, 0.2)
    ctx.move_to(cx - r * 1.0, cy - r * 0.05)
    ctx.curve_to(cx - r * 1.12, cy - r * 0.9, cx - r * 0.4, cy - r * 1.28, cx + r * 0.25, cy - r * 1.15)
    ctx.curve_to(cx + r * 0.85, cy - r * 1.05, cx + r * 1.1, cy - r * 0.6, cx + r * 1.0, cy - r * 0.08)
    ctx.curve_to(cx + r * 0.9, cy - r * 0.35, cx + r * 0.75, cy - r * 0.5, cx + r * 0.55, cy - r * 0.5)
    ctx.curve_to(cx + r * 0.1, cy - r * 0.48, cx - r * 0.35, cy - r * 0.62, cx - r * 0.55, cy - r * 0.42)
    ctx.curve_to(cx - r * 0.75, cy - r * 0.3, cx - r * 0.85, cy - r * 0.2, cx - r * 1.0, cy - r * 0.05)
    borde(ctx, c, 5)
    ctx.set_source_rgba(1, 1, 1, 0.22); ctx.set_line_width(6)
    ctx.move_to(cx - r * 0.4, cy - r * 0.95); ctx.curve_to(cx, cy - r * 1.1, cx + r * 0.4, cy - r * 1.0, cx + r * 0.6, cy - r * 0.8); ctx.stroke()


# ------------------------------------------------------------------ fondo
def cartel(ctx, x, y, w, h, lineas, oscuro=True, icono=None):
    ctx.save(); ctx.translate(x, y)
    rrect(ctx, 6, 8, w, h, 4); ctx.set_source_rgba(0, 0, 0, 0.12); ctx.fill()
    rrect(ctx, 0, 0, w, h, 4); borde(ctx, (0.27, 0.31, 0.38) if oscuro else (0.93, 0.94, 0.96), 5)
    col = (0.95, 0.96, 0.98) if oscuro else (0.2, 0.3, 0.45)
    for i, l in enumerate(lineas):
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(36)
        tam = min(36, 36 * (w - 30) / ctx.text_extents(max(lineas, key=len)).width)
        texto(ctx, l, w / 2, 56 + i * tam * 1.15, tam, col)
    if icono == "engranaje":
        gx, gy, gr = w / 2, h * 0.68, w * 0.24
        ctx.set_source_rgb(0.45, 0.5, 0.58)
        for i in range(12):
            a = i * math.pi / 6; ctx.save(); ctx.translate(gx, gy); ctx.rotate(a)
            ctx.rectangle(-9, -gr - 14, 18, 20); ctx.restore(); ctx.fill()
        ctx.arc(gx, gy, gr, 0, 2 * math.pi); ctx.fill()
        ctx.set_source_rgb(0.85, 0.87, 0.9); ctx.arc(gx, gy, gr * 0.45, 0, 2 * math.pi); ctx.fill()
    elif icono == "motor":
        ctx.set_source_rgba(1, 1, 1, 0.18)
        for k in range(5): ctx.arc(w / 2, h * 0.68, 20 + k * 16, 0, 2 * math.pi); ctx.set_line_width(5); ctx.stroke()
        ctx.set_source_rgb(0.85, 0.3, 0.25); ctx.arc(w * 0.78, h * 0.72, 12, 0, 2 * math.pi); ctx.fill()
    elif icono == "pantalla":
        rrect(ctx, w * 0.18, h * 0.5, w * 0.64, h * 0.34, 6); borde(ctx, (0.4, 0.46, 0.55), 4)
        trazo(ctx, [(w * 0.25, h * 0.75), (w * 0.38, h * 0.62), (w * 0.5, h * 0.7), (w * 0.72, h * 0.58)], 5, (0.6, 0.85, 0.95))
    ctx.restore()

def fondo(ctx, t):
    # pared
    g = cairo.LinearGradient(0, 0, 0, 1150)
    g.add_color_stop_rgb(0, 0.9, 0.91, 0.93); g.add_color_stop_rgb(1, 0.82, 0.83, 0.86)
    ctx.set_source(g); ctx.rectangle(0, 0, W, 1150); ctx.fill()
    ctx.set_source_rgb(0.74, 0.75, 0.78); ctx.rectangle(0, 0, W, 40); ctx.fill()
    for x in (60, 520, 980):  # lámparas
        rrect(ctx, x - 70, 34, 140, 14, 7); ctx.set_source_rgb(0.97, 0.97, 0.95); ctx.fill()
    # ventana grande a la derecha
    vx, vy, vw, vh = 700, 120, 420, 900
    ctx.rectangle(vx, vy, vw, vh); borde(ctx, (0.35, 0.38, 0.43), 8)
    g = cairo.LinearGradient(vx, vy, vx + vw, vy + vh)
    g.add_color_stop_rgb(0, 0.86, 0.9, 0.93); g.add_color_stop_rgb(1, 0.72, 0.78, 0.83)
    ctx.set_source(g); ctx.rectangle(vx + 18, vy + 18, vw - 36, vh - 36); ctx.fill()
    ctx.set_source_rgb(0.35, 0.38, 0.43)
    for xx in (vx + vw / 2,): ctx.rectangle(xx - 7, vy, 14, vh); ctx.fill()
    for yy in (vy + 300, vy + 600): ctx.rectangle(vx, yy - 7, vw, 14); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.35); poly(ctx, [(vx + 40, vy + vh - 40), (vx + 160, vy + 40), (vx + 230, vy + 40), (vx + 110, vy + vh - 40)]); ctx.fill()
    # carteles
    cartel(ctx, 30, 190, 200, 300, ["SERVICIO", "PREMIUM"], icono="motor")
    cartel(ctx, 255, 190, 210, 300, ["DIAGNÓSTICO"], icono="pantalla")
    cartel(ctx, 490, 190, 190, 300, ["REPUESTOS", "ORIGINALES"], oscuro=False, icono="engranaje")
    # zócalo
    ctx.set_source_rgb(0.7, 0.72, 0.76); ctx.rectangle(0, 860, 700, 290); ctx.fill()
    trazo(ctx, [(0, 860), (700, 860)], 6, (0.55, 0.57, 0.62))
    # escritorio con monitor
    ctx.set_source_rgb(0.3, 0.3, 0.33)
    for lx in (40, 620): ctx.rectangle(lx, 980, 18, 200); ctx.fill()
    rrect(ctx, 0, 958, 680, 30, 4); borde(ctx, (0.78, 0.62, 0.42), 5)
    rrect(ctx, 120, 790, 210, 140, 8); borde(ctx, (0.25, 0.26, 0.3), 6)
    ctx.set_source_rgb(0.55, 0.6, 0.66); ctx.rectangle(136, 806, 178, 108); ctx.fill()
    ctx.set_source_rgb(0.25, 0.26, 0.3); ctx.rectangle(215, 930, 20, 28); ctx.fill()
    rrect(ctx, 175, 948, 100, 12, 4); ctx.fill()
    # piso brillante
    g = cairo.LinearGradient(0, 1150, 0, H)
    g.add_color_stop_rgb(0, 0.8, 0.81, 0.84); g.add_color_stop_rgb(1, 0.9, 0.91, 0.93)
    ctx.set_source(g); ctx.rectangle(0, 1150, W, H - 1150); ctx.fill()
    trazo(ctx, [(0, 1150), (W, 1150)], 5, (0.6, 0.62, 0.66))
    ctx.set_source_rgba(1, 1, 1, 0.45)
    for x0 in (-80, 260):
        poly(ctx, [(x0, H), (x0 + 220, 1150), (x0 + 320, 1150), (x0 + 120, H)]); ctx.fill()


# ------------------------------------------------------------------ auto (genérico, sin marca)
def auto(ctx):
    plata, plata_osc = (0.78, 0.8, 0.83), (0.58, 0.6, 0.64)
    # capó abierto
    poly(ctx, [(700, 950), (760, 420), (1000, 300), (1100, 330), (1100, 900)]); borde(ctx, (0.36, 0.38, 0.42), 7)
    ctx.set_source_rgba(1, 1, 1, 0.12); poly(ctx, [(780, 820), (820, 460), (900, 400), (860, 820)]); ctx.fill()
    # motor visible
    poly(ctx, [(690, 1010), (740, 930), (1100, 900), (1100, 1040)]); borde(ctx, (0.22, 0.23, 0.26), 6)
    for k in range(4):
        rrect(ctx, 770 + k * 75, 940 - k * 6, 60, 40, 6); borde(ctx, (0.35, 0.36, 0.4), 4)
    trazo(ctx, [(760, 1000), (1060, 970)], 8, (0.75, 0.55, 0.15))
    # carrocería
    ctx.move_to(640, 1040); ctx.curve_to(660, 1010, 700, 1000, 760, 1010)
    ctx.line_to(1100, 1000); ctx.line_to(1100, 1480); ctx.line_to(700, 1480)
    ctx.curve_to(650, 1470, 630, 1420, 630, 1360); ctx.close_path(); borde(ctx, plata, 7)
    g = cairo.LinearGradient(0, 1010, 0, 1480)
    g.add_color_stop_rgba(0, 1, 1, 1, 0.35); g.add_color_stop_rgba(0.5, 1, 1, 1, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.18)
    ctx.set_source(g); ctx.rectangle(630, 1000, 470, 480); ctx.fill()
    # faro
    poly(ctx, [(660, 1080), (800, 1070), (830, 1130), (680, 1150)]); borde(ctx, (0.9, 0.93, 0.96), 6)
    for k in range(2): ctx.arc(715 + k * 55, 1110, 18, 0, 2 * math.pi); borde(ctx, (0.97, 0.98, 1), 4)
    # parrilla genérica
    rrect(ctx, 650, 1180, 150, 70, 14); borde(ctx, (0.15, 0.15, 0.17), 6)
    ctx.set_source_rgba(1, 1, 1, 0.3); ctx.set_line_width(3)
    for k in range(6): ctx.move_to(670 + k * 22, 1190); ctx.line_to(670 + k * 22, 1240); ctx.stroke()
    # paragolpes
    rrect(ctx, 640, 1300, 220, 60, 20); borde(ctx, plata_osc, 6)
    # rueda
    cx, cy = 1040, 1430
    ctx.arc(cx, cy, 170, 0, 2 * math.pi); borde(ctx, (0.12, 0.12, 0.14), 7)
    ctx.arc(cx, cy, 115, 0, 2 * math.pi); borde(ctx, (0.82, 0.84, 0.87), 6)
    ctx.set_source_rgb(0.55, 0.57, 0.6); ctx.set_line_width(14); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(10):
        a = i * math.pi / 5; ctx.move_to(cx + math.cos(a) * 25, cy + math.sin(a) * 25)
        ctx.line_to(cx + math.cos(a) * 105, cy + math.sin(a) * 105); ctx.stroke()
    ctx.arc(cx, cy, 26, 0, 2 * math.pi); borde(ctx, (0.3, 0.32, 0.36), 5)
    # reflejo en el piso
    sombra(ctx, 880, 1610, 320, 36, 0.18)


# ------------------------------------------------------------------ personajes
def mecanico(ctx, t):
    x = 290
    resp = math.sin(t * 2.0) * 4
    hy = 720 + resp
    sombra(ctx, x, 1650, 170, 26)
    # piernas
    trazo(ctx, [(x - 30, 1180), (x - 55, 1420), (x - 75, 1620)], 15)
    trazo(ctx, [(x + 35, 1180), (x + 45, 1410), (x + 70, 1610)], 15)
    zapato(ctx, x - 90, 1640, -1); zapato(ctx, x + 75, 1630, 1)
    # camisa de trabajo
    azul, rojo = (0.16, 0.2, 0.33), (0.82, 0.16, 0.16)
    sy = 820 + resp
    poly(ctx, [(x - 95, sy), (x + 95, sy), (x + 100, 1200), (x - 100, 1200)]); borde(ctx, azul)
    # mangas cortas con puño rojo
    poly(ctx, [(x - 95, sy), (x - 150, sy + 120), (x - 100, sy + 150), (x - 80, sy + 70)]); borde(ctx, azul)
    poly(ctx, [(x + 95, sy), (x + 150, sy + 120), (x + 100, sy + 150), (x + 80, sy + 70)]); borde(ctx, azul)
    trazo(ctx, [(x - 150, sy + 120), (x - 100, sy + 150)], 14, rojo)
    trazo(ctx, [(x + 150, sy + 120), (x + 100, sy + 150)], 14, rojo)
    # cuello rojo
    poly(ctx, [(x - 50, sy - 6), (x, sy + 60), (x - 15, sy + 70), (x - 70, sy + 20)]); borde(ctx, rojo, 5)
    poly(ctx, [(x + 50, sy - 6), (x, sy + 60), (x + 15, sy + 70), (x + 70, sy + 20)]); borde(ctx, rojo, 5)
    trazo(ctx, [(x, sy + 60), (x, 1200)], 4, (0.1, 0.12, 0.2))
    # bolsillo y parche con nombre
    rrect(ctx, x + 22, sy + 100, 60, 64, 4); borde(ctx, azul, 4)
    rrect(ctx, x - 85, sy + 105, 78, 26, 3); borde(ctx, BLANCO, 3)
    texto(ctx, "MECÁNICO", x - 46, sy + 124, 13, TINTA)
    # brazo izquierdo (cuelga junto al cuerpo)
    trazo(ctx, [(x - 128, sy + 140), (x - 140, sy + 250), (x - 128, sy + 340)], 13)
    guante(ctx, x - 125, sy + 352, 0)
    # brazo derecho: entrega la tableta
    trazo(ctx, [(x + 125, sy + 140), (x + 160, sy + 260), (486, 1150)], 13)
    # cabeza
    cabeza(ctx, x, hy, 100)
    parp = (t % 3.1) < 0.12
    mira = 1.0 if t > 2.2 else 0.4
    ojos(ctx, x, hy, 100, mira=mira, parpadeo=parp, ceño=0.3)
    boca(ctx, x, hy, 100, mira=mira)
    pelo_puntas(ctx, x, hy, 100)
    return (486, 1158)

def tableta(ctx, cx, cy, t):
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(math.radians(-22))
    rrect(ctx, -105, -72, 210, 144, 14); borde(ctx, (0.16, 0.17, 0.2), 6)
    rrect(ctx, -90, -58, 180, 116, 6); ctx.set_source_rgb(0.94, 0.96, 0.98); ctx.fill()
    texto(ctx, "PRESUPUESTO", 0, -24, 22, (0.15, 0.2, 0.3))
    texto(ctx, "APROBADO", 0, 2, 20, (0.15, 0.45, 0.25))
    texto(ctx, "USD 1.200", 0, 42, 32, TINTA)
    ctx.restore()

def cliente(ctx, t):
    x = 760
    resp = math.sin(t * 1.8 + 1) * 4
    hy = 640 + resp
    sombra(ctx, x, 1660, 150, 24)
    # piernas (pantalón negro)
    trazo(ctx, [(x - 25, 1140), (x - 35, 1400), (x - 45, 1630)], 17)
    trazo(ctx, [(x + 30, 1140), (x + 40, 1400), (x + 50, 1630)], 17)
    zapato(ctx, x - 75, 1655, -1); zapato(ctx, x + 60, 1655, 1)
    gris = (0.86, 0.87, 0.89)
    sy = 740 + resp
    # brazo derecho levantado con el teléfono (detrás de la cabeza)
    manga(ctx, [(x + 85, sy + 40), (x + 145, sy + 170), (x + 110, sy - 20)], 44, gris)
    # camisa
    poly(ctx, [(x - 88, sy), (x + 88, sy), (x + 92, 1160), (x - 92, 1160)]); borde(ctx, gris)
    ctx.set_source_rgba(0, 0, 0, 0.07); poly(ctx, [(x + 30, sy + 10), (x + 88, sy), (x + 92, 1160), (x + 40, 1160)]); ctx.fill()
    # cuello y corbata
    poly(ctx, [(x - 45, sy - 8), (x, sy + 40), (x - 10, sy + 58), (x - 62, sy + 18)]); borde(ctx, BLANCO, 5)
    poly(ctx, [(x + 45, sy - 8), (x, sy + 40), (x + 10, sy + 58), (x + 62, sy + 18)]); borde(ctx, BLANCO, 5)
    vino = (0.5, 0.12, 0.2)
    poly(ctx, [(x - 15, sy + 38), (x + 15, sy + 38), (x + 9, sy + 66), (x - 9, sy + 66)]); borde(ctx, vino, 5)
    poly(ctx, [(x - 9, sy + 66), (x + 9, sy + 66), (x + 26, sy + 300), (x, sy + 335), (x - 26, sy + 300)]); borde(ctx, vino, 5)
    # brazo izquierdo: recibe la tableta
    manga(ctx, [(x - 80, sy + 40), (x - 125, sy + 170), (642, 1005)], 44, gris)
    # cabeza
    cabeza(ctx, x, hy, 100)
    habla = max(0, math.sin(t * 13)) * (1 if (t % 2.0) < 1.3 else 0)
    ojos(ctx, x, hy, 100, mira=-0.5, parpadeo=((t + 1.3) % 3.7) < 0.12, ceño=1.0)
    boca(ctx, x, hy, 100, abierta=habla, mira=-0.5)
    pelo_peinado(ctx, x, hy, 100)
    # teléfono y mano en la oreja (por delante de la cabeza)
    ctx.save(); ctx.translate(x + 95, hy - 5); ctx.rotate(math.radians(18))
    rrect(ctx, -22, -55, 44, 110, 9); borde(ctx, (0.55, 0.57, 0.6), 5)
    ctx.restore()
    guante(ctx, x + 112, hy + 45, -70, 1.05)
    return (x - 230, sy + 300)


def subtitulo(ctx, t):
    lineas = [(0.3, 3.0, "«Aprobado. Haz lo que haga falta.»"), (3.0, 6.0, "Pero la falla era un fusible de $2…")]
    for t0, t1, txt in lineas:
        if t0 <= t < t1:
            k = suave((t - t0) / 0.25)
            ctx.save(); ctx.translate(W / 2, 1800); ctx.scale(0.85 + 0.15 * k, 0.85 + 0.15 * k)
            texto(ctx, txt, 0, 0, 52, (1, 1, 1), contorno=TINTA); ctx.restore()


def cuadro(t):
    sup = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(sup); ctx.set_antialias(cairo.ANTIALIAS_BEST)
    z = 1.0 + 0.06 * suave(t / DUR)  # cámara que se acerca despacio
    ctx.translate(W / 2, 1100); ctx.scale(z, z); ctx.translate(-W / 2, -1100)
    fondo(ctx, t); auto(ctx)
    cliente(ctx, t)
    mx, my = mecanico(ctx, t)
    tableta(ctx, 555, 1075, t)
    guante(ctx, mx, my, 10)          # mano del mecánico sobre la tableta
    guante(ctx, 636, 1000, 160, 0.95)  # mano del cliente
    ctx.identity_matrix(); subtitulo(ctx, t)
    buf = np.ndarray((H, W, 4), np.uint8, sup.get_data())
    return buf[:, :, [2, 1, 0]].copy()


if __name__ == "__main__":
    from PIL import Image
    if "--foto" in sys.argv:
        Image.fromarray(cuadro(1.0)).save("salida/taller.png"); print("salida/taller.png")
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", "salida/taller.mp4"]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(int(DUR * FPS)): p.stdin.write(cuadro(i / FPS).tobytes())
        p.stdin.close(); p.wait(); print("salida/taller.mp4")
