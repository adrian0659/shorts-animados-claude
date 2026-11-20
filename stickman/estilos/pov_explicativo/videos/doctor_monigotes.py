"""POV: te graduaste de doctor y el cártel te recluta — versión con monigotes dibujados con código (estilo del
video del escolta), sobre escenarios detallados. Misma voz y cortes que videos/doctor_cartel.py.

Ejecutar desde stickman/estilos/pov_explicativo/:
    python3 videos/doctor_monigotes.py --fotos     # una foto por escena
    python3 videos/doctor_monigotes.py             # -> salida/video3/doctor_monigotes.mp4 (voz en salida/video2/voz.mp3)
"""
import os, sys, math, random, subprocess
from concurrent.futures import ProcessPoolExecutor
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..")); sys.path.insert(0, AQUI)
from escenarios import *
import escolta as ESC
import doctor_cartel as DC

SAL = os.path.join(AQUI, "..", "salida", "video3")
VOZ = os.path.join(AQUI, "..", "salida", "video2", "voz.mp3")
C, DUR, ROJO, VERDE = DC.C, DC.DUR, DC.ROJO, DC.VERDE
S = 1.5

POSES.setdefault("celebrar", dict(torso=180, cab=-6, bi=-30, ai=-40, bd=150, ad=170, mi=-8, pi=-3, md=8, pd=3))


def doc(claves, traje="doctor", escala=S, sem=2):
    return Actor(traje, claves, escala=escala, semilla=sem)


def escenas():
    E = []
    def esc(i, *a, **k): E.append(Escena(C[i], C[i + 1], *a, **k))
    r = lambda i, t: t - C[i]

    # 0 · POV graduado y reclutado
    i = 0
    d = doc([dict(t=0, pose="celebrar", x=540, y=1830, cara="feliz"), dict(t=r(i, 2.9), pose="sorpresa", cara="sorpresa")], "doctor_grad")
    esc(i, lambda c: calle(c, "tarde"), [d, DC.confeti(1),
        Etiqueta("TÚ, DOCTOR", r(i, 1.6), 300, 1020, (450, 1120), tam=66, curva=-0.3),
        Etiqueta("EL CÁRTEL\nTE RECLUTA", r(i, 3.1), 800, 600, None, tam=72, color=ROJO, rot=5)],
        pantalla=[ESC.titulo_pantalla("POV:", 0.0, 200, 140), ESC.titulo_pantalla("TE GRADUASTE", 0.6, 340, 86)],
        cam=(1.0, 1.08, (540, 1150), (540, 1200)), sacudidas=[(r(i, 3.1), 18)])

    # 1 · 6 años y el título
    i = 1
    d = doc([dict(t=0, pose="parado", x=-120, y=1830, cara="feliz", caminar=True), dict(t=1.8, pose="dinero", x=420, y=1830, cara="feliz", objeto=None)], "doctor_grad")
    esc(i, lambda c: oficina(c, "dia"), [d, DC.confeti(2, 40),
        Etiqueta("6 AÑOS\nDE ESTUDIO", r(i, 5.4), 280, 640, None, tam=70, rot=-4)],
        pantalla=[Inserto(r(i, 8.6), 470, 160, 560, 400, DC.diploma)],
        cam=(1.0, 1.07, (540, 1150), (540, 1100)))

    # 2 · el sueño
    i = 2
    d = doc([dict(t=0, pose="pensar", x=380, y=1830, cara="feliz", mira=0.4)])
    paciente = Actor("amiga", [dict(t=r(i, 13.2), pose="parado", x=800, y=1760, cara="feliz", fac=-1)], escala=1.25, semilla=8)
    def letrero(c, w, h, t):
        c.set_source(degradado(0, h, (0.9, 0.95, 1), (0.75, 0.85, 0.95))); c.paint()
        rrect(c, 30, 40, w - 60, h - 80, 16); relleno(c, (1, 1, 1), 5)
        c.rectangle(w / 2 - 22, 70, 44, 120); c.rectangle(w / 2 - 60, 108, 120, 44); c.set_source_rgb(*ROJO); c.fill()
        texto(c, "CONSULTORIO", w / 2, h * 0.62, 54, (0.15, 0.3, 0.55)); texto(c, "DR. TÚ", w / 2, h * 0.8, 46, TINTA)
    esc(i, lambda c: sala(c, "dia"), [paciente, d,
        Etiqueta("AYUDAR A\nLAS PERSONAS", r(i, 13.3), 820, 840, (800, 1000), tam=56, color=(0.15, 0.3, 0.55), curva=0.3),
        Etiqueta("UNA BUENA VIDA", r(i, 15.0), 300, 620, None, tam=56, color=VERDE, rot=-4)],
        pantalla=[Inserto(r(i, 11.6), 520, 150, 500, 380, letrero)],
        tinte=(1.0, 0.95, 0.85, 0.2), cam=(1.0, 1.06, (540, 1150), (540, 1150)))

    # 3 · pero hay un problema
    i = 3
    d = doc([dict(t=0, pose="parado", x=540, y=2420, cara="neutral"), dict(t=r(i, 17.1), cara="preocupado", sudor=True)], escala=3.0)
    esc(i, lambda c: None, [ESC.fondo_rayos((0.5, 0.08, 0.08), (0.15, 0.02, 0.02)), d,
        Etiqueta("UN PROBLEMA", r(i, 17.5), 540, 330, None, tam=110, color=(1, 1, 1), halo=TINTA, rot=-4)],
        cam=(1.0, 1.1, (540, 1000), (540, 960)), sacudidas=[(r(i, 17.5), 20)])

    # 4 · sin experiencia
    i = 4
    d = doc([dict(t=0, pose="telefono", x=360, y=1830, cara="preocupado", objeto="telefono"), dict(t=r(i, 21.5), cara="triste")])
    esc(i, lambda c: calle(c, "dia"), [d,
        Etiqueta("SIN\nEXPERIENCIA", r(i, 20.2), 300, 520, None, tam=64, color=ROJO, rot=-3)],
        pantalla=[Inserto(r(i, 21.4), 520, 150, 500, 520, DC.chat([(0.1, "Buscamos 5 años de exp.", (1, 1, 1)),
                                                                     (0.9, "Vacante ocupada", (1, 1, 1)),
                                                                     (1.7, "Lo sentimos...", (1, 0.85, 0.85))], "CORREO"))],
        cam=(1.0, 1.07, (540, 1150), (500, 1150)))

    # 5 · oferta extraña
    i = 5
    d = doc([dict(t=0, pose="telefono", x=360, y=1830, cara="neutral", objeto="telefono"), dict(t=r(i, 27.3), cara="sorpresa")])
    esc(i, lambda c: sala(c, "noche"), [d,
        Etiqueta("BASTANTE\nEXTRAÑA...", r(i, 27.4), 290, 560, None, tam=66, color=(1, 0.85, 0.2), halo=TINTA, rot=-5)],
        pantalla=[Inserto(r(i, 25.4), 500, 150, 520, 520, DC.chat([(0.1, "Oferta de trabajo", (0.85, 0.95, 0.85)),
                                                                     (1.0, "Paga: $$$$$", (0.85, 0.95, 0.85)),
                                                                     (1.8, "¿Te interesa?", (0.85, 0.95, 0.85))], "NÚMERO DESCONOCIDO"))],
        cam=(1.0, 1.06, (540, 1150), (520, 1150)))

    # 6 · muchísimo dinero
    i = 6
    d = doc([dict(t=0, pose="sorpresa", x=540, y=1830, cara="sorpresa")])
    esc(i, lambda c: sala(c, "noche"), [ESC.dinero_cae(5, 26), d,
        Etiqueta("MUCHÍSIMO\nDINERO", r(i, 29.3), 310, 600, None, tam=80, color=VERDE, rot=-5),
        Etiqueta("PROPIEDAD\nPRIVADA", r(i, 31.9), 800, 760, None, tam=64, rot=4)],
        cam=(1.0, 1.08, (540, 1150), (540, 1100)))

    # 7 · ¿empresarios adinerados?
    i = 7
    d = doc([dict(t=0, pose="pensar", x=330, y=1830, cara="pensar", mira=0.6)])
    j = Actor("jefe_traje", [dict(t=0, pose="cadera", x=1400, y=1780, cara="feliz", fac=-1, caminar=True),
                             dict(t=r(i, 35.0), pose="cadera", x=800, y=1780, cara="feliz", fac=-1)], escala=1.45, semilla=4)
    esc(i, lambda c: oficina(c, "dia"), [j, d,
        Etiqueta("¿EMPRESARIOS\nADINERADOS?", r(i, 35.2), 700, 560, (800, 900), tam=62, curva=-0.3)],
        cam=(1.0, 1.06, (540, 1150), (560, 1150)))

    # 8 · propiedad con hombres armados
    i = 8
    d = doc([dict(t=0, pose="parado", x=-150, y=1850, cara="neutral", caminar=True),
             dict(t=r(i, 38.6), pose="parado", x=520, y=1850, cara="neutral", mira=0.0),
             dict(t=r(i, 40.4), pose="encoger", cara="miedo", mira=-0.8, sudor=True)])
    guardias = [Actor("soldado", [dict(t=0, pose=p, x=x, y=1500, cara="serio", fac=f)], escala=1.0, semilla=10 + k)
                for k, (x, p, f) in enumerate([(150, "cruzado", 1), (930, "cruzado", -1), (720, "guardia", -1)])]
    esc(i, lambda c: rancho(c, "dia"), guardias + [DC.muro_bajo(1420), d,
        Etiqueta("HOMBRES\nARMADOS", r(i, 40.5), 540, 560, (190, 860), tam=70, color=ROJO, curva=0.3),
        Etiqueta("ENORME PROPIEDAD", r(i, 38.6), 540, 300, None, tam=60, rot=-3)],
        cam=(1.0, 1.06, (540, 1100), (540, 1100)))

    # 9 · aparece el jefe
    i = 9
    j = Actor("jefe_traje", [dict(t=0, pose="cruzado", x=540, y=2050, cara="serio"), dict(t=r(i, 43.9), cara="enojado")], escala=2.1, semilla=4)
    esc(i, lambda c: oficina(c, "noche"), [j,
        Etiqueta("EL JEFE", r(i, 43.9), 540, 420, None, tam=130, color=ROJO, halo=(1, 1, 1), rot=-4)],
        tinte=(0.75, 0.7, 0.8, 0.3), cam=(1.0, 1.1, (540, 1050), (540, 980)), sacudidas=[(r(i, 44.0), 22)])

    # 10 · médico 24 h, sin preguntas
    i = 10
    j = Actor("jefe_traje", [dict(t=0, pose="mesa", x=760, y=1640, cara="serio", fac=-1), dict(t=r(i, 49.2), pose="senalar", cara="enojado", fac=-1)], escala=1.4, semilla=4)
    d = doc([dict(t=0, pose="parado", x=250, y=1880, cara="neutral", mira=0.7), dict(t=r(i, 49.5), pose="encoger", cara="preocupado", mira=0.7)], escala=1.4)
    esc(i, lambda c: oficina(c, "noche"), [j, DC.escritorio_frente(1560), d,
        Etiqueta("SIN\nPREGUNTAS", r(i, 49.5), 820, 560, None, tam=76, color=ROJO, rot=4)],
        pantalla=[Inserto(r(i, 47.1), 60, 150, 420, 420, DC.reloj_24)],
        cam=(1.0, 1.06, (540, 1150), (560, 1150)))

    # 11 · es un cártel
    i = 11
    d = doc([dict(t=0, pose="parado", x=540, y=2380, cara="preocupado"), dict(t=r(i, 55.8), pose="manos_cara", cara="miedo", sudor=True)], escala=2.6)
    esc(i, lambda c: oficina(c, "noche"), [d,
        Etiqueta("EMPRESARIOS", r(i, 54.4), 540, 380, None, tam=80, tachar=True),
        Etiqueta("UN CÁRTEL", r(i, 57.2), 540, 560, None, tam=110, color=ROJO, halo=(1, 1, 1), rot=-4)],
        tinte=lambda t: (1, 0.55, 0.5, clamp((t - (57.2 - C[11])) / 0.3) * 0.4), cam=(1.0, 1.1, (540, 1000), (540, 940)),
        sacudidas=[(r(i, 57.2), 22)])

    # 12 · dinero nunca imaginado
    i = 12
    d = doc([dict(t=0, pose="sorpresa", x=540, y=1700, cara="sorpresa")])
    def mesa_dinero(c, t):
        DC.escritorio_frente(1600)(c, t)
        r_ = random.Random(2)
        for k in range(14):
            if t < 0.3 + k * 0.12: continue
            billete(c, 120 + (k % 7) * 140 + r_.uniform(-20, 20), 1570 - (k // 7) * 40, 1.3, r_.uniform(-0.3, 0.3))
    esc(i, lambda c: oficina(c, "noche"), [d, mesa_dinero,
        Etiqueta("JAMÁS LO\nHABÍAS IMAGINADO", r(i, 60.2), 540, 560, None, tam=66, color=VERDE, halo=(1, 1, 1), rot=-3)],
        cam=(1.0, 1.07, (540, 1150), (540, 1100)))

    # 13 · condición
    i = 13
    j = Actor("jefe_traje", [dict(t=0, pose="cruzado", x=540, y=2350, cara="serio"), dict(t=r(i, 66.2), pose="senalar", cara="enojado", fac=-1)], escala=2.4, semilla=4)
    esc(i, lambda c: oficina(c, "noche"), [j,
        Etiqueta("UNA CONDICIÓN", r(i, 65.0), 540, 360, None, tam=86, color=(1, 1, 1), halo=TINTA, rot=-3)],
        pantalla=[Inserto(r(i, 66.3), 290, 1380, 500, 380, DC.candado), ESC.titulo_pantalla("ABSOLUTA DISCRECIÓN", r(i, 66.6), 1820, 74, (1, 0.85, 0.2), TINTA)],
        tinte=(0.8, 0.75, 0.85, 0.3), cam=(1.0, 1.1, (540, 1050), (540, 980)))

    # 14 · heridas y emergencias
    i = 14
    d = doc([dict(t=0, pose="senalar", x=300, y=1860, cara="serio", mira=0.6, objeto="linterna")], escala=1.4)
    esc(i, lambda c: bodega(c), [DC.camilla(740, 1700, 0.85), d,
        Etiqueta("HERIDAS", r(i, 70.7), 760, 760, (700, 1340), tam=70, color=ROJO),
        Etiqueta("EMERGENCIAS", r(i, 71.4), 760, 560, None, tam=66, rot=4)],
        pantalla=[Inserto(r(i, 69.0), 40, 150, 360, 300, DC.botiquin)],
        cam=(1.0, 1.06, (540, 1150), (560, 1150)))

    # 15 · atrapado
    i = 15
    d = doc([dict(t=0, pose="cruzado", x=540, y=1850, cara="preocupado"), dict(t=r(i, 76.4), pose="encoger", cara="miedo", sudor=True)])
    def hospital(c, w, h, t):
        c.set_source_rgb(0.92, 0.95, 0.98); c.paint()
        c.rectangle(w * 0.2, h * 0.3, w * 0.6, h * 0.55); relleno(c, (1, 1, 1), 5)
        c.rectangle(w * 0.46, h * 0.38, w * 0.08, h * 0.2); c.rectangle(w * 0.39, h * 0.445, w * 0.22, h * 0.07); c.set_source_rgb(*ROJO); c.fill()
        texto(c, "HOSPITAL", w / 2, h * 0.2, 40, (0.15, 0.3, 0.55))
        ESC.x_roja(c, w / 2, h * 0.55, 0.9, (t - 0.4) / 0.5)
    esc(i, lambda c: bodega(c), [d,
        Etiqueta("ATRAPADO", r(i, 74.9), 540, 300, None, tam=100, color=(1, 1, 1), halo=TINTA, rot=-4),
        Etiqueta("AMENAZAS", r(i, 76.5), 340, 600, None, tam=70, color=ROJO, halo=(1, 1, 1), rot=-6),
        Etiqueta("MIEDO", r(i, 77.5), 850, 700, None, tam=78, color=(1, 0.85, 0.2), halo=TINTA, rot=5)],
        pantalla=[Inserto(r(i, 79.4), 620, 1300, 400, 340, hospital)],
        tinte=(0.6, 0.62, 0.8, 0.4), cam=(1.0, 1.1, (540, 1150), (540, 1100)), sacudidas=[(r(i, 76.5), 14)])

    # 16 · ¿vale la pena?
    i = 16
    d = doc([dict(t=0, pose="pensar", x=880, y=1880, cara="pensar", mira=-0.6, fac=-1)], escala=1.15)
    esc(i, ESC.fondo_papel((0.93, 0.9, 0.84)), [ESC.balanza(0), d,
        Etiqueta("DINERO", r(i, 82.9), 220, 1350, None, tam=60, color=VERDE),
        Etiqueta("TU PAZ", r(i, 83.6), 800, 1080, None, tam=60, color=ROJO)],
        pantalla=[ESC.titulo_pantalla("¿VALE LA PENA?", r(i, 83.6), 300, 104, ROJO, (1, 1, 1))],
        cam=(1.0, 1.05, (540, 1000), (540, 1040)))

    # 17 · paciente en estado crítico
    i = 17
    d = doc([dict(t=0, pose="sorpresa", x=270, y=1870, cara="sorpresa", mira=0.7),
             dict(t=r(i, 88.5), pose="manos_cara", cara="miedo", mira=0.7, sudor=True)], escala=1.4)
    esc(i, lambda c: bodega(c), [DC.camilla(730, 1720, 0.95, critico=True), DC.monitor_ecg(860, 1080, critico=True), d,
        Etiqueta("ESTADO\nCRÍTICO", r(i, 87.1), 760, 560, (720, 1400), tam=78, color=ROJO, halo=(1, 1, 1), curva=0.25),
        Etiqueta("ESTO NO\nES NORMAL", r(i, 90.9), 300, 520, None, tam=64, color=(1, 1, 1), halo=TINTA, rot=-5)],
        tinte=lambda t: (1.0, 0.35, 0.35, 0.18 + 0.22 * (0.5 + 0.5 * math.sin(t * 7))),
        cam=(1.0, 1.08, (540, 1150), (600, 1150)), sacudidas=[(r(i, 85.9), 16)])

    # 18 · renunciar / sabes demasiado
    i = 18
    j = Actor("jefe_traje", [dict(t=0, pose="mesa", x=760, y=1640, cara="serio", fac=-1), dict(t=r(i, 93.6), pose="senalar", cara="enojado", fac=-1)], escala=1.4, semilla=4)
    d = doc([dict(t=0, pose="parado", x=250, y=1880, cara="preocupado", mira=0.7), dict(t=r(i, 94.5), pose="encoger", cara="miedo", mira=0.7, sudor=True)], escala=1.4)
    def carta(c, w, h, t):
        c.set_source_rgb(0.95, 0.95, 0.93); c.paint()
        c.rectangle(w * 0.2, h * 0.12, w * 0.6, h * 0.76); relleno(c, (1, 1, 1), 4)
        texto(c, "RENUNCIA", w / 2, h * 0.25, 42, TINTA)
        for k in range(5): linea(c, [(w * 0.28, h * (0.4 + k * 0.08)), (w * 0.72, h * (0.4 + k * 0.08))], 3, TINTA, 0.35)
        ESC.x_roja(c, w / 2, h / 2, 0.85, (t - 1.2) / 0.5)
    esc(i, lambda c: oficina(c, "noche"), [j, DC.escritorio_frente(1560), d,
        Etiqueta("SABES\nDEMASIADO", r(i, 95.3), 780, 470, None, tam=82, color=ROJO, halo=(1, 1, 1), rot=4)],
        pantalla=[Inserto(r(i, 92.2), 40, 180, 400, 420, carta)],
        tinte=(0.85, 0.7, 0.75, 0.3), cam=(1.0, 1.07, (540, 1150), (580, 1150)), sacudidas=[(r(i, 95.3), 16)])

    # 19 · el mayor error
    i = 19
    d = doc([dict(t=0, pose="triste", x=540, y=2250, cara="triste")], escala=2.7)
    esc(i, lambda c: None, [ESC.fondo_rayos((0.22, 0.22, 0.28), (0.06, 0.06, 0.08), 24), d,
        Etiqueta("EL MAYOR\nERROR", r(i, 99.9), 540, 400, None, tam=120, color=ROJO, halo=(1, 1, 1), rot=-4)],
        cam=(1.0, 1.1, (540, 1000), (540, 960)))

    # 20 · salvar vidas
    i = 20
    d = doc([dict(t=0, pose="celebrar", x=420, y=1830, cara="feliz")], "doctor_grad")
    def corazon(c, t):
        if t < r(20, 103.4): return
        k = max(0.01, rebote((t - r(20, 103.4)) / 0.35)) * (1 + 0.08 * max(0, math.sin(t * 8)) ** 4)
        c.save(); c.translate(820, 760); c.scale(k * 1.3, k * 1.3)
        c.move_to(0, 60); c.curve_to(-110, -10, -60, -95, 0, -40); c.curve_to(60, -95, 110, -10, 0, 60); c.close_path()
        relleno(c, ROJO, 7); c.restore()
    esc(i, lambda c: calle(c, "tarde"), [d, corazon,
        Etiqueta("SALVAR VIDAS", r(i, 103.4), 540, 480, None, tam=80, color=(1, 1, 1), halo=TINTA, rot=-4)],
        tinte=(1.0, 0.88, 0.7, 0.35), cam=(1.0, 1.06, (540, 1150), (540, 1150)))

    # 21 · peligro
    i = 21
    j = Actor("jefe_traje", [dict(t=0, pose="cadera", x=540, y=1560, cara="enojado")], escala=1.25, semilla=4)
    guardias = [Actor("soldado", [dict(t=0, pose="cruzado", x=x, y=1600, cara="serio", fac=f)], escala=1.15, semilla=5 + k)
                for k, (x, f) in enumerate([(170, 1), (910, -1)])]
    esc(i, lambda c: rancho(c, "noche"), guardias + [j, DC.muro_bajo(1480),
        Etiqueta("PELIGRO", r(i, 107.8), 540, 330, None, tam=130, color=ROJO, halo=(1, 1, 1), rot=-4)],
        tinte=(1.0, 0.5, 0.45, 0.35), cam=(1.0, 1.07, (540, 1100), (540, 1080)))

    # 22 · ¿tú qué harías?
    i = 22
    d = doc([dict(t=0, pose="pensar", x=540, y=1880, cara="pensar", mira=-0.4), dict(t=r(i, 111.2), cara="preocupado", mira=0.4)], escala=1.2)
    esc(i, ESC.fondo_papel((0.93, 0.92, 0.88)), [DC.opciones, d],
        pantalla=[ESC.titulo_pantalla("¿TÚ QUÉ HARÍAS?", 0.15, 300, 100, TINTA, (1, 1, 1))],
        cam=(1.0, 1.05, (540, 1000), (540, 1000)))
    return E


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
    vw = os.path.join(SAL, "voz.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", VOZ, "-ac", "1", "-ar", str(DC.SR), vw], check=True)
    DC.mezcla_audio(vw, os.path.join(SAL, "mezcla.wav"), escenas())
    n = os.cpu_count() or 4
    cortes = np.linspace(0, DUR, n * 2 + 1)
    tareas = [(round(cortes[k] * FPS) / FPS, round(cortes[k + 1] * FPS) / FPS, os.path.join(SAL, f"parte_{k:02d}.mp4")) for k in range(len(cortes) - 1)]
    with ProcessPoolExecutor(n) as ex:
        for p in ex.map(_tramo, tareas): print("listo", os.path.basename(p), flush=True)
    lista = os.path.join(SAL, "lista.txt")
    open(lista, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for _, _, p in tareas))
    final = os.path.join(SAL, "doctor_monigotes.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lista, "-i", os.path.join(SAL, "mezcla.wav"),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,volume=1.8dB,alimiter=limit=0.89",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", final], check=True)
    for _, _, p in tareas: os.remove(p)
    print("VIDEO:", final)
