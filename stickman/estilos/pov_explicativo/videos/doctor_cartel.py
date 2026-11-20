"""POV: te acabas de graduar de doctor y el cártel te recluta (114.5 s, vertical 1080x1920).

Personajes HD recortados de las hojas de referencia (doctor, empresario = jefe, soldado = hombres armados) con
expresiones nuevas (recortes.py). Historia ficticia.

Ejecutar desde stickman/estilos/pov_explicativo/:
    python3 videos/doctor_cartel.py --fotos     # una foto por escena
    python3 videos/doctor_cartel.py             # video final -> salida/video2/doctor_cartel.mp4 (voz en salida/video2/voz.mp3)
"""
import os, sys, math, random, subprocess, wave
from concurrent.futures import ProcessPoolExecutor
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, ".."))
sys.path.insert(0, AQUI)
from escenarios import *
from recortes import Recorte
import escolta as ESC

SAL = os.path.join(AQUI, "..", "salida", "video2")
DUR = 114.52
ROJO = (0.85, 0.12, 0.12)
VERDE = (0.15, 0.55, 0.25)
C = [0, 4.6, 10.0, 16.15, 18.25, 24.6, 28.05, 33.0, 36.3, 42.3, 44.7, 51.55, 57.6, 63.45, 68.1, 72.65, 81.2, 84.45,
     91.95, 96.85, 101.5, 104.4, 108.7, DUR]


# ------------------------------------------------------------------ utilería
def confeti(sem=1, n=70):
    r = random.Random(sem)
    d = [(r.uniform(0, W), r.uniform(-1900, 0), r.uniform(250, 450), r.uniform(0, 6), r.choice([(0.95, 0.3, 0.4), (0.3, 0.7, 0.95), (0.98, 0.8, 0.2), (0.4, 0.8, 0.4)])) for _ in range(n)]
    def f(c, t):
        for (x, y, v, ph, col) in d:
            yy = y + t * v
            if yy < -50 or yy > H + 50: continue
            c.save(); c.translate(x + math.sin(t * 3 + ph) * 30, yy); c.rotate(t * 4 + ph); c.scale(1, abs(math.sin(t * 5 + ph)) + 0.2)
            c.rectangle(-12, -7, 24, 14); c.set_source_rgb(*col); c.fill(); c.restore()
    return f


def diploma(c, w, h, t):
    c.set_source(degradado(0, h, (0.98, 0.96, 0.88), (0.93, 0.89, 0.76))); c.paint()
    rrect(c, 20, 20, w - 40, h - 40, 6); c.set_source_rgb(0.75, 0.6, 0.25); c.set_line_width(6); c.stroke()
    texto(c, "TÍTULO DE", w / 2, h * 0.22, 40, TINTA)
    texto(c, "MÉDICO CIRUJANO", w / 2, h * 0.4, 52, (0.15, 0.3, 0.55))
    linea(c, [(w * 0.25, h * 0.62), (w * 0.75, h * 0.62)], 3, TINTA, 0.5)
    texto(c, "TU NOMBRE", w / 2, h * 0.7, 28, (0.4, 0.4, 0.4), MANO, peso=cairo.FONT_WEIGHT_BOLD)
    c.arc(w * 0.82, h * 0.8, 40, 0, 7); relleno(c, (0.85, 0.15, 0.15), 3)
    linea(c, [(w * 0.8, h * 0.85), (w * 0.76, h * 0.98)], 14, (0.85, 0.15, 0.15)); linea(c, [(w * 0.84, h * 0.85), (w * 0.88, h * 0.98)], 14, (0.85, 0.15, 0.15))


def chat(mensajes, titulo="MENSAJES"):
    def f(c, w, h, t):
        c.set_source(degradado(0, h, (0.2, 0.22, 0.28), (0.1, 0.1, 0.14))); c.paint()
        rrect(c, w * 0.06, h * 0.06, w * 0.88, h * 0.88, 26); relleno(c, (0.94, 0.95, 0.97), 4)
        texto(c, titulo, w / 2, h * 0.14, h * 0.055, TINTA)
        linea(c, [(w * 0.1, h * 0.2), (w * 0.9, h * 0.2)], 2, TINTA, 0.3)
        for i, (t0, txt, col) in enumerate(mensajes):
            if t < t0: continue
            k = rebote((t - t0) / 0.3); yy = h * (0.3 + i * 0.2)
            c.save(); c.translate(w * 0.46, yy); c.scale(k, k)
            rrect(c, -w * 0.36, -h * 0.075, w * 0.72, h * 0.15, 18); relleno(c, col, 3)
            texto(c, txt, 0, 0, h * 0.04, TINTA, MANO, peso=cairo.FONT_WEIGHT_BOLD)
            c.restore()
    return f


def reloj_24(c, w, h, t):
    c.set_source_rgb(0.96, 0.96, 0.94); c.paint()
    cx, cy, r = w / 2, h * 0.45, min(w, h) * 0.32
    c.arc(cx, cy, r, 0, 7); relleno(c, (1, 1, 1), 8)
    for k in range(12):
        a = k * math.pi / 6; linea(c, [(cx + math.cos(a) * r * 0.8, cy + math.sin(a) * r * 0.8), (cx + math.cos(a) * r * 0.92, cy + math.sin(a) * r * 0.92)], 5)
    a = t * 6; linea(c, [(cx, cy), (cx + math.sin(a) * r * 0.75, cy - math.cos(a) * r * 0.75)], 7, ROJO)
    linea(c, [(cx, cy), (cx + math.sin(a / 12) * r * 0.5, cy - math.cos(a / 12) * r * 0.5)], 10)
    texto(c, "24 HORAS", w / 2, h * 0.88, h * 0.1, ROJO)


def candado(c, w, h, t):
    c.set_source(degradado(0, h, (0.15, 0.15, 0.18), (0.05, 0.05, 0.07))); c.paint()
    cx, cy = w / 2, h * 0.5
    c.arc(cx, cy - 40, 80, math.pi, 0); c.set_source_rgb(0.75, 0.77, 0.8); c.set_line_width(34); c.stroke()
    rrect(c, cx - 130, cy - 40, 260, 200, 24); relleno(c, degradado(cy - 40, cy + 160, (0.95, 0.8, 0.3), (0.75, 0.55, 0.15)), 6)
    c.arc(cx, cy + 40, 24, 0, 7); relleno(c, TINTA, 0); c.rectangle(cx - 9, cy + 40, 18, 60); c.set_source_rgb(*TINTA); c.fill()


def botiquin(c, w, h, t):
    c.set_source_rgb(0.95, 0.95, 0.93); c.paint()
    rrect(c, w * 0.15, h * 0.25, w * 0.7, h * 0.55, 20); relleno(c, (0.92, 0.2, 0.2), 6)
    rrect(c, w * 0.38, h * 0.15, w * 0.24, h * 0.12, 10); c.set_source_rgb(*TINTA); c.set_line_width(10); c.stroke()
    c.rectangle(w * 0.45, h * 0.35, w * 0.1, h * 0.35); c.rectangle(w * 0.33, h * 0.475, w * 0.34, h * 0.1); c.set_source_rgb(1, 1, 1); c.fill()


def camilla(x, y, s=1.0, critico=False):
    def f(c, t):
        c.save(); c.translate(x, y); c.scale(s, s)
        for lx in (-300, 280): linea(c, [(lx, 0), (lx, -230)], 12, (0.6, 0.62, 0.66))
        for lx in (-300, 280): c.arc(lx, 10, 18, 0, 7); relleno(c, (0.2, 0.2, 0.22), 3)
        rrect(c, -340, -270, 680, 50, 12); relleno(c, (0.75, 0.77, 0.8), 4)
        # paciente con sábana
        c.arc(-250, -330, 62, 0, 7); relleno(c, (0.98, 0.98, 0.98), 6)
        resp = math.sin(t * (6 if critico else 2)) * 6
        for lado in (-1, 1): c.arc(-250 + lado * 20, -335, 7, 0, 7); c.set_source_rgb(*TINTA); c.fill()
        linea(c, [(-262, -305), (-238, -305)], 5)
        c.move_to(-200, -270); c.curve_to(-180, -350 - resp, 200, -340 - resp, 330, -280); c.line_to(330, -260); c.line_to(-200, -260); c.close_path()
        relleno(c, (0.62, 0.78, 0.9), 5)
        if critico:
            c.arc(-60, -320 - resp, 28, 0, 7); c.set_source_rgba(0.8, 0.05, 0.05, 0.85); c.fill()
        c.restore()
    return f


def monitor_ecg(x, y, critico=False):
    def f(c, t):
        rrect(c, x - 150, y - 110, 300, 220, 16); relleno(c, (0.25, 0.26, 0.3), 5)
        rrect(c, x - 130, y - 90, 260, 160, 8); relleno(c, (0.05, 0.1, 0.08), 3)
        pts = []
        vel = 3.5 if critico else 1.3
        for i in range(60):
            u = i / 59; ph = (u * 2 - t * vel) % 1
            yy = 0
            if 0.4 < ph < 0.45: yy = -60 * math.sin((ph - 0.4) / 0.05 * math.pi)
            elif 0.45 < ph < 0.5: yy = 30 * math.sin((ph - 0.45) / 0.05 * math.pi)
            pts.append((x - 125 + u * 250, y - 10 + yy))
        linea(c, pts, 4, (0.3, 1, 0.4) if not critico else (1, 0.3, 0.3))
        texto(c, "180" if critico else "72", x + 90, y + 90, 34, (1, 0.3, 0.3) if critico else (0.3, 1, 0.4), "Inter", peso=cairo.FONT_WEIGHT_BOLD)
    return f


def escritorio_frente(y0=1500, color=(0.42, 0.28, 0.17)):
    def f(c, t):
        sombra_suave(c, lambda cc: cc.rectangle(0, y0 - 30, W, 60), 30, 0.4)
        c.rectangle(-20, y0, W + 40, 50); relleno(c, degradado(y0, y0 + 50, osc(color, 1.3), color), 5)
        textura(c, lambda cc: cc.rectangle(-20, y0, W + 40, 50), "madera", 0.5, sem=3)
        c.rectangle(-20, y0 + 50, W + 40, H); relleno(c, degradado(y0, H, osc(color, 0.9), osc(color, 0.6)), 5)
        for xx in (60, 560): rrect(c, xx, y0 + 90, 440, 160, 10); c.set_source_rgb(*TINTA); c.set_line_width(3); c.stroke()
    return f


def muro_bajo(y0=1450):
    def f(c, t):
        c.rectangle(-20, y0, W + 40, H - y0); relleno(c, degradado(y0, H, (0.78, 0.7, 0.58), (0.6, 0.52, 0.42)), 5)
        r = random.Random(4)
        for j in range(5):
            x = -30 - j * 40
            while x < W:
                w = r.uniform(80, 150); rrect(c, x, y0 + 10 + j * 70, w - 6, 62, 10)
                c.set_source_rgb(*osc((0.7, 0.62, 0.52), r.uniform(0.85, 1.12))); c.fill_preserve(); c.set_source_rgba(*TINTA, 0.5); c.set_line_width(2.5); c.stroke()
                x += w
        linea(c, [(-20, y0), (W + 20, y0)], 5)
    return f


def tarjeta_opcion(titulo_, sub, col, t0):
    def f(c, t):
        if t < t0: return
        k = rebote((t - t0) / 0.35)
        return k
    return f


def opciones(c, t):
    for i, (txt, col, t0, x) in enumerate([("ACEPTAR\nEL DINERO", VERDE, 1.25, 290), ("ABANDONAR\nTODO", ROJO, 2.2, 790)]):
        if t < t0: continue
        k = max(0.01, rebote((t - t0) / 0.35))
        c.save(); c.translate(x, 760); c.scale(k, k); c.rotate(math.radians(-4 if i == 0 else 4))
        sombra_suave(c, lambda cc: rrect(cc, -210, -150, 420, 300, 30), 20, 0.35, 8, 12)
        rrect(c, -210, -150, 420, 300, 30); relleno(c, (1, 1, 1), 6)
        texto(c, txt, 0, -10, 62, col)
        texto(c, "A" if i == 0 else "B", 0, 110, 50, (0.5, 0.5, 0.5))
        c.restore()
    if t > 2.3:
        texto(c, "VS", 540, 760, 70, TINTA, halo=(1, 1, 1))


def x_roja(c, x, y, s, k): ESC.x_roja(c, x, y, s, k)


# ------------------------------------------------------------------ escenas
def escenas():
    E = []
    def esc(i, *a, **k): E.append(Escena(C[i], C[i + 1], *a, **k))
    r = lambda i, t: t - C[i]
    DOC = dict(x=540, y=1960, alto=1450)

    # 0 · POV graduado y reclutado
    i = 0
    d = Recorte("doctor", [dict(t=0, **DOC, cara="feliz", birrete=True), dict(t=r(i, 2.9), cara="sorpresa", birrete=True)])
    esc(i, lambda c: calle(c, "tarde"), [d, confeti(1),
        Etiqueta("TÚ, DOCTOR", r(i, 1.6), 220, 1120, (330, 1010), tam=66, curva=-0.3),
        Etiqueta("EL CÁRTEL\nTE RECLUTA", r(i, 3.1), 800, 560, None, tam=72, color=ROJO, rot=5)],
        pantalla=[ESC.titulo_pantalla("POV:", 0.0, 200, 140), ESC.titulo_pantalla("TE GRADUASTE", 0.6, 340, 86)],
        cam=(1.0, 1.08, (540, 1000), (540, 1060)), sacudidas=[(r(i, 3.1), 18)])

    # 1 · 6 años y el título
    i = 1
    d = Recorte("doctor", [dict(t=0, **DOC, cara="feliz", birrete=True)])
    esc(i, lambda c: oficina(c, "dia"), [d, confeti(2, 40),
        Etiqueta("6 AÑOS\nDE ESTUDIO", r(i, 5.4), 220, 600, None, tam=74, rot=-4)],
        pantalla=[Inserto(r(i, 8.6), 470, 160, 560, 400, diploma)],
        cam=(1.0, 1.07, (540, 1050), (540, 1000)))

    # 2 · el sueño: consultorio
    i = 2
    d = Recorte("doctor", [dict(t=0, **DOC, cara="feliz", mira=0.3)])
    def letrero(c, w, h, t):
        c.set_source(degradado(0, h, (0.9, 0.95, 1), (0.75, 0.85, 0.95))); c.paint()
        rrect(c, 30, 40, w - 60, h - 80, 16); relleno(c, (1, 1, 1), 5)
        c.rectangle(w / 2 - 22, 70, 44, 120); c.rectangle(w / 2 - 60, 108, 120, 44); c.set_source_rgb(*ROJO); c.fill()
        texto(c, "CONSULTORIO", w / 2, h * 0.62, 54, (0.15, 0.3, 0.55)); texto(c, "DR. TÚ", w / 2, h * 0.8, 46, TINTA)
    esc(i, lambda c: sala(c, "dia"), [d,
        Etiqueta("AYUDAR A\nLAS PERSONAS", r(i, 13.3), 260, 600, None, tam=64, color=(0.15, 0.3, 0.55), rot=-4),
        Etiqueta("UNA BUENA VIDA", r(i, 15.0), 280, 400, None, tam=56, color=VERDE, rot=4)],
        pantalla=[Inserto(r(i, 11.6), 500, 150, 520, 400, letrero)],
        tinte=(1.0, 0.95, 0.85, 0.2), cam=(1.0, 1.06, (540, 1000), (540, 1040)))

    # 3 · pero hay un problema
    i = 3
    d = Recorte("doctor", [dict(t=0, x=540, y=2500, alto=2300, cara="neutral"), dict(t=r(i, 17.1), cara="preocupado")])
    esc(i, lambda c: None, [ESC.fondo_rayos((0.5, 0.08, 0.08), (0.15, 0.02, 0.02)), d,
        Etiqueta("UN PROBLEMA", r(i, 17.5), 540, 330, None, tam=110, color=(1, 1, 1), halo=TINTA, rot=-4)],
        cam=(1.0, 1.1, (540, 1000), (540, 960)), sacudidas=[(r(i, 17.5), 20)])

    # 4 · sin experiencia
    i = 4
    d = Recorte("doctor", [dict(t=0, **DOC, cara="preocupado", mira=-0.3), dict(t=r(i, 21.5), cara="triste")])
    esc(i, lambda c: calle(c, "dia"), [d,
        Etiqueta("SIN\nEXPERIENCIA", r(i, 20.2), 260, 480, None, tam=74, color=ROJO, rot=-3)],
        pantalla=[Inserto(r(i, 21.4), 520, 150, 500, 520, chat([(0.1, "Buscamos 5 años de exp.", (1, 1, 1)),
                                                                   (0.9, "Vacante ocupada", (1, 1, 1)),
                                                                   (1.7, "Lo sentimos...", (1, 0.85, 0.85))], "CORREO"))],
        cam=(1.0, 1.07, (540, 1050), (520, 1080)))

    # 5 · oferta extraña
    i = 5
    d = Recorte("doctor", [dict(t=0, **DOC, cara="neutral", mira=0.4), dict(t=r(i, 27.3), cara="sorpresa")])
    esc(i, lambda c: sala(c, "noche"), [d,
        Etiqueta("BASTANTE\nEXTRAÑA...", r(i, 27.4), 250, 560, None, tam=66, color=(1, 0.85, 0.2), halo=TINTA, rot=-5)],
        pantalla=[Inserto(r(i, 25.4), 500, 150, 520, 520, chat([(0.1, "Oferta de trabajo", (0.85, 0.95, 0.85)),
                                                                   (1.0, "Paga: $$$$$", (0.85, 0.95, 0.85)),
                                                                   (1.8, "¿Te interesa?", (0.85, 0.95, 0.85))], "NÚMERO DESCONOCIDO"))],
        cam=(1.0, 1.06, (540, 1050), (540, 1030)))

    # 6 · muchísimo dinero, propiedad privada
    i = 6
    d = Recorte("doctor", [dict(t=0, **DOC, cara="sorpresa")])
    esc(i, lambda c: sala(c, "noche"), [ESC.dinero_cae(5, 26), d,
        Etiqueta("MUCHÍSIMO\nDINERO", r(i, 29.3), 280, 660, None, tam=80, color=VERDE, rot=-5),
        Etiqueta("PROPIEDAD\nPRIVADA", r(i, 31.9), 790, 760, None, tam=64, rot=4)],
        cam=(1.0, 1.08, (540, 1050), (540, 1000)))

    # 7 · ¿empresarios adinerados?
    i = 7
    d = Recorte("doctor", [dict(t=0, x=330, y=1960, alto=1300, cara="pensando", mira=0.5)])
    j = Recorte("jefe", [dict(t=r(i, 34.6), x=820, y=1960, alto=1150, cara="feliz", mira=-0.4)])
    esc(i, lambda c: oficina(c, "dia"), [j, d,
        Etiqueta("¿EMPRESARIOS\nADINERADOS?", r(i, 35.2), 700, 540, (800, 820), tam=62, curva=-0.3)],
        cam=(1.0, 1.06, (540, 1050), (560, 1060)))

    # 8 · propiedad con hombres armados
    i = 8
    d = Recorte("doctor", [dict(t=0, x=-200, y=1980, alto=1250, cara="neutral", caminar=True),
                           dict(t=r(i, 38.4), x=540, y=1980, alto=1250, cara="neutral", mover=True),
                           dict(t=r(i, 40.4), cara="miedo", mira=-0.6)], entrada=None)
    guardias = [Recorte("soldado", [dict(t=r(i, 39.6) + k * 0.15, x=x, y=1520, alto=760, cara="serio", espejo=e)], sem=k + 3)
                for k, (x, e) in enumerate([(150, False), (930, True), (720, True)])]
    esc(i, lambda c: rancho(c, "dia"), guardias + [muro_bajo(1450), d,
        Etiqueta("HOMBRES\nARMADOS", r(i, 40.5), 540, 540, (220, 900), tam=70, color=ROJO, curva=0.3),
        Etiqueta("ENORME PROPIEDAD", r(i, 38.6), 540, 300, None, tam=60, rot=-3)],
        cam=(1.0, 1.06, (540, 1100), (540, 1100)))

    # 9 · aparece el jefe
    i = 9
    j = Recorte("jefe", [dict(t=0.1, x=540, y=1940, alto=1500, cara="malicia")])
    esc(i, lambda c: oficina(c, "noche"), [j,
        Etiqueta("EL JEFE", r(i, 43.9), 540, 520, None, tam=130, color=ROJO, halo=(1, 1, 1), rot=-4)],
        tinte=(0.75, 0.7, 0.8, 0.3), cam=(1.0, 1.1, (540, 1050), (540, 980)), sacudidas=[(r(i, 44.0), 22)])

    # 10 · médico 24 h, sin preguntas
    i = 10
    j = Recorte("jefe", [dict(t=0, x=760, y=1700, alto=1250, cara="serio", mira=-0.5)], entrada=None, habla=[(0, 6.5)])
    d = Recorte("doctor", [dict(t=0, x=260, y=1990, alto=1200, cara="neutral", mira=0.6), dict(t=r(i, 49.4), cara="preocupado", mira=0.6)], entrada=None)
    esc(i, lambda c: oficina(c, "noche"), [j, escritorio_frente(1520), d,
        Etiqueta("SIN\nPREGUNTAS", r(i, 49.5), 820, 600, None, tam=76, color=ROJO, rot=4)],
        pantalla=[Inserto(r(i, 47.1), 60, 150, 420, 420, reloj_24)],
        cam=(1.0, 1.06, (540, 1050), (560, 1050)))

    # 11 · no son empresarios: es un cártel
    i = 11
    d = Recorte("doctor", [dict(t=0, x=540, y=2300, alto=1900, cara="preocupado"), dict(t=r(i, 55.8), cara="miedo")], entrada=None)
    esc(i, lambda c: oficina(c, "noche"), [d,
        Etiqueta("EMPRESARIOS", r(i, 54.4), 540, 380, None, tam=80, tachar=True),
        Etiqueta("UN CÁRTEL", r(i, 57.2), 540, 560, None, tam=110, color=ROJO, halo=(1, 1, 1), rot=-4)],
        tinte=lambda t: (1, 0.55, 0.5, clamp((t - (57.2 - C[11])) / 0.3) * 0.4), cam=(1.0, 1.1, (540, 1000), (540, 940)),
        sacudidas=[(r(i, 57.2), 22)])

    # 12 · dinero nunca imaginado
    i = 12
    d = Recorte("doctor", [dict(t=0, x=540, y=1990, alto=1350, cara="sorpresa")], entrada=None)
    def mesa_dinero(c, t):
        escritorio_frente(1560)(c, t)
        r_ = random.Random(2)
        for k in range(14):
            if t < 0.3 + k * 0.12: continue
            billete(c, 120 + (k % 7) * 140 + r_.uniform(-20, 20), 1530 - (k // 7) * 40, 1.3, r_.uniform(-0.3, 0.3))
    esc(i, lambda c: oficina(c, "noche"), [d, mesa_dinero,
        Etiqueta("JAMÁS LO\nHABÍAS IMAGINADO", r(i, 60.2), 540, 560, None, tam=66, color=VERDE, halo=(1, 1, 1), rot=-3)],
        cam=(1.0, 1.07, (540, 1100), (540, 1060)))

    # 13 · condición: discreción
    i = 13
    j = Recorte("jefe", [dict(t=0, x=540, y=2100, alto=1800, cara="serio"), dict(t=r(i, 66.2), cara="enojado")], entrada=None, habla=[(0, 4.5)])
    esc(i, lambda c: oficina(c, "noche"), [j,
        Etiqueta("UNA CONDICIÓN", r(i, 65.0), 540, 380, None, tam=86, color=(1, 1, 1), halo=TINTA, rot=-3)],
        pantalla=[Inserto(r(i, 66.3), 290, 1380, 500, 380, candado), ESC.titulo_pantalla("ABSOLUTA DISCRECIÓN", r(i, 66.6), 1820, 74, (1, 0.85, 0.2), TINTA)],
        tinte=(0.8, 0.75, 0.85, 0.3), cam=(1.0, 1.1, (540, 1050), (540, 980)))

    # 14 · heridas y emergencias
    i = 14
    d = Recorte("doctor", [dict(t=0, x=330, y=1990, alto=1300, cara="serio", mira=0.6)], entrada=None)
    esc(i, lambda c: bodega(c), [camilla(720, 1650, 0.9), d,
        Etiqueta("HERIDAS", r(i, 70.7), 760, 760, (760, 1290), tam=70, color=ROJO),
        Etiqueta("EMERGENCIAS", r(i, 71.4), 760, 560, None, tam=66, rot=4)],
        pantalla=[Inserto(r(i, 69.0), 40, 150, 360, 300, botiquin)],
        cam=(1.0, 1.06, (540, 1100), (560, 1100)))

    # 15 · atrapado: amenazas, miedo, sin hospital
    i = 15
    d = Recorte("doctor", [dict(t=0, x=540, y=1990, alto=1400, cara="preocupado"), dict(t=r(i, 76.4), cara="miedo")], entrada=None)
    def hospital(c, w, h, t):
        c.set_source_rgb(0.92, 0.95, 0.98); c.paint()
        c.rectangle(w * 0.2, h * 0.3, w * 0.6, h * 0.55); relleno(c, (1, 1, 1), 5)
        c.rectangle(w * 0.46, h * 0.38, w * 0.08, h * 0.2); c.rectangle(w * 0.39, h * 0.445, w * 0.22, h * 0.07); c.set_source_rgb(*ROJO); c.fill()
        texto(c, "HOSPITAL", w / 2, h * 0.2, 40, (0.15, 0.3, 0.55))
        ESC.x_roja(c, w / 2, h * 0.55, 0.9, (t - 0.4) / 0.5)
    esc(i, lambda c: bodega(c), [d,
        Etiqueta("ATRAPADO", r(i, 74.9), 540, 300, None, tam=100, color=(1, 1, 1), halo=TINTA, rot=-4),
        Etiqueta("AMENAZAS", r(i, 76.5), 300, 600, None, tam=70, color=ROJO, halo=(1, 1, 1), rot=-6),
        Etiqueta("MIEDO", r(i, 77.5), 850, 700, None, tam=78, color=(1, 0.85, 0.2), halo=TINTA, rot=5)],
        pantalla=[Inserto(r(i, 79.4), 600, 1280, 420, 360, hospital)],
        tinte=(0.6, 0.62, 0.8, 0.4), cam=(1.0, 1.1, (540, 1050), (540, 1000)), sacudidas=[(r(i, 76.5), 14)])

    # 16 · ¿vale la pena?
    i = 16
    d = Recorte("doctor", [dict(t=0, x=880, y=1990, alto=900, cara="pensando", mira=-0.6)], entrada=None)
    esc(i, ESC.fondo_papel((0.93, 0.9, 0.84)), [ESC.balanza(0), d,
        Etiqueta("DINERO", r(i, 82.9), 220, 1350, None, tam=60, color=VERDE),
        Etiqueta("TU PAZ", r(i, 83.6), 800, 1080, None, tam=60, color=ROJO)],
        pantalla=[ESC.titulo_pantalla("¿VALE LA PENA?", r(i, 83.6), 300, 104, ROJO, (1, 1, 1))],
        cam=(1.0, 1.05, (540, 1000), (540, 1040)))

    # 17 · paciente en estado crítico
    i = 17
    d = Recorte("doctor", [dict(t=0, x=300, y=1990, alto=1300, cara="sorpresa", mira=0.7), dict(t=r(i, 88.5), cara="miedo", mira=0.7)], entrada=None)
    def alarma(t):
        return (1.0, 0.35, 0.35, 0.18 + 0.22 * (0.5 + 0.5 * math.sin(t * 7)))
    esc(i, lambda c: bodega(c), [camilla(720, 1700, 0.95, critico=True), monitor_ecg(860, 1080, critico=True), d,
        Etiqueta("ESTADO\nCRÍTICO", r(i, 87.1), 760, 560, (720, 1380), tam=78, color=ROJO, halo=(1, 1, 1), curva=0.25),
        Etiqueta("ESTO NO\nES NORMAL", r(i, 90.9), 300, 520, None, tam=64, color=(1, 1, 1), halo=TINTA, rot=-5)],
        tinte=alarma, cam=(1.0, 1.08, (540, 1100), (600, 1100)), sacudidas=[(r(i, 85.9), 16)])

    # 18 · renunciar / sabes demasiado
    i = 18
    j = Recorte("jefe", [dict(t=0, x=760, y=1700, alto=1300, cara="serio", mira=-0.5), dict(t=r(i, 93.6), cara="enojado", mira=-0.5)], entrada=None, habla=[(1.5, 4.5)])
    d = Recorte("doctor", [dict(t=0, x=260, y=1990, alto=1200, cara="preocupado", mira=0.6), dict(t=r(i, 94.5), cara="miedo", mira=0.6)], entrada=None)
    def carta(c, w, h, t):
        c.set_source_rgb(0.95, 0.95, 0.93); c.paint()
        c.rectangle(w * 0.2, h * 0.12, w * 0.6, h * 0.76); relleno(c, (1, 1, 1), 4)
        texto(c, "RENUNCIA", w / 2, h * 0.25, 42, TINTA)
        for k in range(5): linea(c, [(w * 0.28, h * (0.4 + k * 0.08)), (w * 0.72, h * (0.4 + k * 0.08))], 3, TINTA, 0.35)
        ESC.x_roja(c, w / 2, h / 2, 0.85, (t - 1.2) / 0.5)
    esc(i, lambda c: oficina(c, "noche"), [j, escritorio_frente(1520), d,
        Etiqueta("SABES\nDEMASIADO", r(i, 95.3), 780, 470, None, tam=82, color=ROJO, halo=(1, 1, 1), rot=4)],
        pantalla=[Inserto(r(i, 92.2), 40, 180, 400, 420, carta)],
        tinte=(0.85, 0.7, 0.75, 0.3), cam=(1.0, 1.07, (540, 1050), (580, 1050)), sacudidas=[(r(i, 95.3), 16)])

    # 19 · el mayor error
    i = 19
    d = Recorte("doctor", [dict(t=0, x=540, y=2300, alto=1900, cara="triste")], entrada=None)
    esc(i, lambda c: None, [ESC.fondo_rayos((0.22, 0.22, 0.28), (0.06, 0.06, 0.08), 24), d,
        Etiqueta("EL MAYOR\nERROR", r(i, 99.9), 540, 400, None, tam=120, color=ROJO, halo=(1, 1, 1), rot=-4)],
        cam=(1.0, 1.1, (540, 1000), (540, 960)))

    # 20 · estudiaste para salvar vidas
    i = 20
    d = Recorte("doctor", [dict(t=0, **DOC, cara="feliz", birrete=True)], entrada=None)
    def corazon(c, t):
        if t < r(20, 103.4): return
        k = rebote((t - r(20, 103.4)) / 0.35) * (1 + 0.08 * max(0, math.sin(t * 8)) ** 4)
        c.save(); c.translate(860, 640); c.scale(k * 1.3, k * 1.3)
        c.move_to(0, 60); c.curve_to(-110, -10, -60, -95, 0, -40); c.curve_to(60, -95, 110, -10, 0, 60); c.close_path()
        relleno(c, ROJO, 7); c.restore()
    esc(i, lambda c: calle(c, "tarde"), [d, corazon,
        Etiqueta("SALVAR VIDAS", r(i, 103.4), 360, 560, None, tam=72, color=(1, 1, 1), halo=TINTA, rot=-4)],
        tinte=(1.0, 0.88, 0.7, 0.35), cam=(1.0, 1.06, (540, 1000), (540, 1030)))

    # 21 · una organización que las pone en peligro
    i = 21
    j = Recorte("jefe", [dict(t=0.2, x=540, y=1600, alto=1050, cara="malicia")])
    guardias = [Recorte("soldado", [dict(t=0.5 + k * 0.15, x=x, y=1640, alto=900, cara="serio", espejo=e)], sem=k + 5)
                for k, (x, e) in enumerate([(170, False), (910, True)])]
    esc(i, lambda c: rancho(c, "noche"), guardias + [j, muro_bajo(1500),
        Etiqueta("PELIGRO", r(i, 107.8), 540, 330, None, tam=130, color=ROJO, halo=(1, 1, 1), rot=-4)],
        tinte=(1.0, 0.5, 0.45, 0.35), cam=(1.0, 1.07, (540, 1100), (540, 1080)))

    # 22 · ¿tú qué harías?
    i = 22
    d = Recorte("doctor", [dict(t=0, x=540, y=2000, alto=1050, cara="pensando", mira=-0.4), dict(t=r(i, 111.2), cara="preocupado", mira=0.4)], entrada=None)
    esc(i, ESC.fondo_papel((0.93, 0.92, 0.88)), [opciones, d],
        pantalla=[ESC.titulo_pantalla("¿TÚ QUÉ HARÍAS?", 0.15, 300, 100, TINTA, (1, 1, 1))],
        cam=(1.0, 1.05, (540, 1000), (540, 1000)))
    return E


# ------------------------------------------------------------------ sonido
SR = ESC.SR


def mezcla_audio(voz_wav, ruta, es):
    with wave.open(voz_wav) as w:
        voz = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    n = int(SR * DUR) + SR; fx = np.zeros(n)
    def poner(t, x, v=1.0):
        o = int(t * SR); e = min(n, o + len(x)); fx[o:e] += x[:e - o] * v
    for k, tc in enumerate(C[1:-1]): poner(tc - 0.25, ESC.whoosh(0.5, k), 0.35)
    for e in es:
        for cap in e.capas:
            if isinstance(cap, Etiqueta): poner(e.t0 + cap.t0, ESC.pop(), 0.5)
        for ts, _ in e.sac: poner(e.t0 + ts, ESC.golpe(), 0.7)
    for tt in np.arange(C[17], C[18], 0.45): poner(tt, ESC.latido(), 0.6)
    for tt in np.arange(C[15], C[16], 1.0): poner(tt, ESC.latido(), 0.35)
    mus = ESC.musica(DUR); m = np.zeros(n); m[:len(mus)] = mus
    v = np.zeros(n); v[:len(voz)] = voz[:n]
    total = v + m * 0.11 + fx * 0.22
    total = total / max(1e-6, np.abs(total).max()) * 0.9
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((total * 32767).astype(np.int16).tobytes())


def _tramo(args):
    a, b, ruta = args
    render_tramo(escenas(), a, b, ruta); return ruta


if __name__ == "__main__":
    os.makedirs(os.path.join(SAL, "fotos"), exist_ok=True)
    if "--fotos" in sys.argv:
        from PIL import Image
        es = escenas()
        for k, e in enumerate(es):
            t = e.t0 + (e.t1 - e.t0) * 0.85
            Image.fromarray(cuadro_video(es, t)).save(os.path.join(SAL, "fotos", f"esc_{k:02d}.png")); print("foto", k, flush=True)
        sys.exit()
    voz = os.path.join(SAL, "voz.mp3"); vw = os.path.join(SAL, "voz.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", voz, "-ac", "1", "-ar", str(SR), vw], check=True)
    mezcla_audio(vw, os.path.join(SAL, "mezcla.wav"), escenas())
    n = os.cpu_count() or 4
    cortes = np.linspace(0, DUR, n * 2 + 1)
    tareas = [(round(cortes[k] * FPS) / FPS, round(cortes[k + 1] * FPS) / FPS, os.path.join(SAL, f"parte_{k:02d}.mp4")) for k in range(len(cortes) - 1)]
    with ProcessPoolExecutor(n) as ex:
        for p in ex.map(_tramo, tareas): print("listo", os.path.basename(p), flush=True)
    lista = os.path.join(SAL, "lista.txt")
    open(lista, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for _, _, p in tareas))
    final = os.path.join(SAL, "doctor_cartel.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lista, "-i", os.path.join(SAL, "mezcla.wav"),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", final], check=True)
    for _, _, p in tareas: os.remove(p)
    print("VIDEO:", final)
