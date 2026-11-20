"""Las 38 escenas de «POV: te acabas de graduar de doctor y el cártel te recluta», dibujadas con código.

Uso (desde esta carpeta):
    python3 escenas_doctor.py ../proyectos/doctor-cartel/img          # todas
    python3 escenas_doctor.py ../proyectos/doctor-cartel/img 7 12     # solo algunas
"""
import os, sys, math, random
from monitos import *

SUELO = 900


def primer_plano(ctx, m, cx, cy, R):
    """Dibuja el personaje m tan grande que su cabeza (radio R) queda centrada en (cx, cy)."""
    s = R / 80
    m.dibujar(ctx, cx, cy + 476.4 * s, s)


def lluvia_billetes(ctx, n=14, semilla=2, zona=(250, 1670, 120, 900)):
    rnd = random.Random(semilla)
    for _ in range(n):
        billete(ctx, rnd.uniform(zona[0], zona[1]), rnd.uniform(zona[2], zona[3]), rnd.uniform(0.6, 1.0), rnd.uniform(-40, 40))


def confeti(ctx, n=60, semilla=4):
    rnd = random.Random(semilla)
    cols = [(0.95, 0.3, 0.3), (0.3, 0.6, 0.95), (0.98, 0.8, 0.2), (0.4, 0.8, 0.45), (0.8, 0.4, 0.9)]
    for _ in range(n):
        x, y = rnd.uniform(200, 1720), rnd.uniform(80, 700)
        ctx.save(); ctx.translate(x, y); ctx.rotate(rnd.uniform(0, 3))
        ctx.rectangle(-9, -5, 18, 10); ctx.set_source_rgb(*rnd.choice(cols)); ctx.fill(); ctx.restore()


def cartel(ctx, x, y, w, h, txt, tam=40, fondo=(0.3, 0.35, 0.45), color=BLANCO):
    ctx.rectangle(x - w / 2, y - h / 2, w, h); pintar(ctx, fondo, 6)
    lineas = txt.split("\n")
    for i, l in enumerate(lineas):
        texto(ctx, l, x, y + (i - (len(lineas) - 1) / 2) * tam * 1.15, tam, color)


# ================================================================ escenas
def e01(ctx):  # graduación feliz
    interior(ctx, pared=(0.78, 0.82, 0.9), ventana=None)
    cartel(ctx, 960, 150, 760, 100, "GRADUACIÓN 2026", 54, (0.2, 0.3, 0.55))
    for x in (380, 1540): linea(ctx, [(x, 120), (x, 280)], 6); circulo(ctx, x, 300, 28, ORO, 5)
    m = Monito("toga", cara="orgulloso", pose="mostrar_d", pelo="picos", sombrero="birrete").dibujar(ctx, 900, SUELO + 40, 1.15)
    mx, my = m.manos["d"]
    ctx.save(); ctx.translate(mx + 20, my - 10); ctx.rotate(-0.4)
    redondo(ctx, -25, -90, 50, 180, 20); pintar(ctx, (0.99, 0.97, 0.9), 5)
    linea(ctx, [(-25, 0), (25, 0)], 8, ROJO); ctx.restore()
    confeti(ctx)


def e02(ctx):  # siluetas armadas detrás
    interior(ctx, pared=(0.78, 0.82, 0.9))
    oscurecer(ctx, foco=(960, 420), radio=420, fuerza=0.55, bombilla=False)
    for x in (620, 1320):
        sicario_con_rifle(ctx, x, SUELO + 10, 1.3); sicario(cara="serio").dibujar(ctx, x, SUELO + 10, 1.3, silueta=True, color_silueta=(0.06, 0.07, 0.1))
    Monito("toga", cara="aterrado", pose="brazos_arriba", pelo="picos", sombrero="birrete", sudor=True).dibujar(ctx, 960, SUELO + 40, 1.2)


def e03(ctx):  # estudiando seis años
    interior(ctx, pared=(0.84, 0.86, 0.9), ventana=(1250, 140, 420, 300))
    oscurecer(ctx, foco=(760, 500), radio=600, fuerza=0.45, bombilla=False)
    doctor("dormido", "mirar_manos").dibujar(ctx, 900, 905, 1.05)
    escritorio(ctx, 900, 640, 1000)
    for (x, n, sem) in ((560, 10, 1), (700, 7, 2), (1150, 9, 3), (1290, 12, 4)): libros(ctx, x, 640, n, 0.9, sem)
    for x in (1010, 1080):
        redondo(ctx, x - 22, 585, 44, 55, 6); pintar(ctx, BLANCO, 4)
    # lámpara
    linea(ctx, [(470, 640), (470, 470), (560, 420)], 10); ctx.new_path(); ctx.move_to(520, 380); ctx.line_to(620, 420)
    ctx.line_to(590, 470); ctx.close_path(); pintar(ctx, (0.3, 0.55, 0.4), 5)
    texto(ctx, "6 AÑOS", 960, 200, 90, ROJO, borde=TINTA, peso="Black")


def e04(ctx):  # consigue el título
    interior(ctx, pared=(0.86, 0.88, 0.92), ventana=(180, 150, 380, 300))
    m = doctor("orgulloso", "mostrar_d").dibujar(ctx, 820, SUELO, 1.2)
    mx, my = m.manos["d"]
    diploma(ctx, mx + 150, my - 60, 1.0)
    circulo(ctx, mx, my, 20, BLANCO, 5)
    for (dx, dy) in ((-230, -150), (220, -240), (300, 120), (-200, 80)): estrella(ctx, mx + 150 + dx, my - 60 + dy, 30)


def e05(ctx):  # sueño del consultorio
    interior(ctx, pared=(0.86, 0.88, 0.92))
    m = doctor("feliz", "jarras", mira=0.4).dibujar(ctx, 560, SUELO, 1.15)
    cx, cy, R = m.cabeza

    def sueno(c):
        c.save(); c.translate(1180, 470)
        c.rectangle(-260, -120, 520, 230); pintar(c, (0.95, 0.96, 0.98), 6)
        c.rectangle(-60, -10, 120, 120); pintar(c, (0.6, 0.78, 0.9), 5)
        for dx in (-190, 120): c.rectangle(dx, -60, 80, 70); pintar(c, (0.6, 0.78, 0.9), 4)
        redondo(c, -230, -200, 460, 70, 10); pintar(c, (0.2, 0.45, 0.75), 5)
        texto(c, "CONSULTORIO", 0, -165, 46, BLANCO)
        cruz_medica(c, 0, -60, 26)
        c.restore()
    burbuja(ctx, 1180, 430, 760, 520, hacia=(cx + R, cy - R * 0.4), contenido=sueno)


def e06(ctx):  # ayudar a las personas
    interior(ctx, pared=(0.86, 0.9, 0.93), ventana=(1320, 140, 380, 280))
    ctx.rectangle(280, 260, 220, 300); pintar(ctx, BLANCO, 5)
    texto(ctx, "AAAA", 390, 320, 30, TINTA); texto(ctx, "AAA", 390, 380, 24, TINTA); texto(ctx, "AA", 390, 430, 18, TINTA)
    doctor("feliz", "señalar_d", mira=0.6).dibujar(ctx, 700, SUELO, 1.15)
    Monito("nina", cara="feliz", pelo="coleta", mira=-0.5).dibujar(ctx, 1020, SUELO, 1.1)
    Monito("mujer", cara="feliz", pelo="largo", pose="cruzados", mira=-0.5).dibujar(ctx, 1330, SUELO, 1.1)
    for (x, y) in ((1100, 380), (1180, 330)):
        ctx.new_path(); ctx.move_to(x, y + 20); ctx.curve_to(x - 30, y - 5, x - 15, y - 30, x, y - 12)
        ctx.curve_to(x + 15, y - 30, x + 30, y - 5, x, y + 20); pintar(ctx, (0.92, 0.3, 0.4), 3)


def e07(ctx):  # PERO…
    liso(ctx, (0.88, 0.89, 0.92))
    for i in range(24):
        a = 2 * math.pi * i / 24
        linea(ctx, [(960 + math.cos(a) * 380, 540 + math.sin(a) * 260), (960 + math.cos(a) * 700, 540 + math.sin(a) * 480)],
              6, (0.6, 0.62, 0.68))
    texto(ctx, "PERO…", 960, 540, 330, BLANCO, borde=TINTA, peso="Black")
    for (a, b) in (((760, 420), (840, 540)), ((840, 540), (800, 640)), ((1150, 400), (1100, 520)), ((1100, 520), (1180, 620))):
        linea(ctx, [a, b], 6, TINTA)


def e08(ctx):  # SE REQUIERE EXPERIENCIA
    interior(ctx, pared=(0.84, 0.86, 0.9), ventana=(1350, 130, 360, 280))
    escritorio(ctx, 1380, 640, 640)
    Monito("reclutador", cara="serio", pose="sostener", pelo="castano", lentes=True).dibujar(ctx, 1420, 905, 1.0)
    ctx.save(); ctx.translate(1230, 610); ctx.rotate(-0.05)
    ctx.rectangle(-140, -40, 280, 80); pintar(ctx, (0.99, 0.99, 0.97), 4); ctx.restore()
    texto(ctx, "SE REQUIERE", 960, 210, 64, ROJO, rot=-10, peso="Black")
    texto(ctx, "EXPERIENCIA", 960, 290, 64, ROJO, rot=-10, peso="Black")
    ctx.save(); ctx.translate(960, 250); ctx.rotate(math.radians(-10)); redondo(ctx, -300, -95, 600, 190, 16)
    ctx.set_source_rgb(*ROJO); ctx.set_line_width(14); ctx.stroke(); ctx.restore()
    doctor("triste", "parado", mira=0.5).dibujar(ctx, 560, SUELO, 1.15)


def e09(ctx):  # cartas de rechazo
    interior(ctx, pared=(0.8, 0.82, 0.86), ventana=(1300, 150, 330, 260), luz=False)
    ctx.rectangle(600, 640, 760, 140); pintar(ctx, (0.55, 0.6, 0.75), 6)
    ctx.rectangle(560, 560, 70, 220); pintar(ctx, (0.45, 0.32, 0.22), 5)
    doctor("preocupado", "mirar_manos", sudor=True).dibujar(ctx, 900, 820, 1.0)
    rnd = random.Random(5)
    for i in range(12):
        x = rnd.uniform(350, 1600); y = rnd.uniform(790, 980); r = rnd.uniform(-30, 30)
        ctx.save(); ctx.translate(x, y); ctx.rotate(math.radians(r))
        ctx.rectangle(-70, -45, 140, 90); pintar(ctx, (0.99, 0.98, 0.95), 3)
        texto(ctx, "RECHAZADO", 0, 0, 22, ROJO, rot=-12); ctx.restore()


def e10(ctx):  # oferta extraña en el teléfono
    interior(ctx, pared=(0.84, 0.86, 0.9))
    m = doctor("dudoso", "mirar_telefono", mira=0.5).dibujar(ctx, 600, SUELO, 1.15)

    def pant(c):
        redondo(c, -45, -80, 90, 40, 8); pintar(c, (0.85, 0.85, 0.88), 0)
        texto(c, "¿?", 0, 30, 60, TINTA)
    telefono(ctx, 1220, 500, 2.0, None)
    ctx.rectangle(1130, 330, 180, 50); pintar(ctx, (0.2, 0.45, 0.75), 0)
    texto(ctx, "NÚMERO", 1220, 345, 26, BLANCO); texto(ctx, "DESCONOCIDO", 1220, 372, 22, BLANCO)
    redondo(ctx, 1135, 410, 170, 110, 14); pintar(ctx, BLANCO, 3)
    texto(ctx, "¿Necesitas", 1220, 445, 26, TINTA); texto(ctx, "trabajo?", 1220, 485, 26, TINTA)
    texto(ctx, "?", 840, 230, 120, ROJO, borde=TINTA, peso="Black")


def e11(ctx):  # muchísimo dinero (primer plano)
    liso(ctx, (0.82, 0.9, 0.84))
    lluvia_billetes(ctx, 18, 3, (120, 1800, 60, 1020))
    primer_plano(ctx, doctor("sorpresa"), 960, 520, 330)
    texto(ctx, "$$$", 960, 140, 110, VERDE_DINERO, borde=TINTA, peso="Black")


def e12(ctx):  # propiedad privada (burbuja)
    interior(ctx, pared=(0.84, 0.86, 0.9))
    m = doctor("dudoso", "jarras", mira=0.4).dibujar(ctx, 520, SUELO, 1.1)
    cx, cy, R = m.cabeza

    def sueno(c):
        c.save(); c.rectangle(890, 230, 640, 420); c.clip()
        exterior(c, suelo_y=560)
        c.restore()
        mansion(c, 1210, 560, 0.55); palmera(c, 960, 570, 0.6); palmera(c, 1460, 570, 0.6); reja(c, 900, 1520, 620, 90)
    burbuja(ctx, 1210, 440, 800, 520, hacia=(cx + R, cy - R * 0.3), contenido=sueno)


def e13(ctx):  # empresarios adinerados (burbuja)
    interior(ctx, pared=(0.84, 0.86, 0.9))
    m = doctor("feliz", "parado", mira=0.4).dibujar(ctx, 470, SUELO, 1.1)
    cx, cy, R = m.cabeza

    def sueno(c):
        for (x, pelo) in ((1000, "castano"), (1200, None), (1400, "castano")):
            Monito("traje", cara="feliz", pose="entregar", pelo=pelo, lentes=(pelo is None)).dibujar(c, x, 640, 0.62)
        texto(c, "EMPRESARIOS", 1200, 230, 42, (0.2, 0.3, 0.55))
    burbuja(ctx, 1200, 440, 820, 540, hacia=(cx + R, cy - R * 0.3), contenido=sueno)


def e14(ctx):  # viaje en coche
    exterior(ctx, suelo_y=700, suelo=(0.85, 0.77, 0.6))
    ctx.new_path(); ctx.move_to(0, 780); ctx.line_to(W, 760); ctx.line_to(W, 900); ctx.line_to(0, 920); ctx.close_path()
    pintar(ctx, (0.55, 0.55, 0.58), 0)
    for x in range(60, W, 220): ctx.rectangle(x, 838, 110, 12); ctx.set_source_rgb(1, 1, 1); ctx.fill()
    reja(ctx, 1450, 1700, 760, 300)
    carrito(ctx, 760, 880, 1.2)
    ctx.save(); ctx.rectangle(560, 560, 300, 200); ctx.clip()
    doctor("serio", "sostener").dibujar(ctx, 700, 1100, 0.8); ctx.restore()
    for i in range(4):
        ctx.new_path(); ctx.arc(420 - i * 70, 840 - i * 8, 30 + i * 8, 0, 2 * math.pi)
        ctx.set_source_rgba(0.8, 0.72, 0.55, 0.6 - i * 0.12); ctx.fill()


def e15(ctx):  # mansión con hombres armados
    exterior(ctx, suelo_y=640)
    mansion(ctx, 960, 640, 0.95); palmera(ctx, 360, 660, 0.9); palmera(ctx, 1560, 660, 0.9)
    for (x, s) in ((520, 0.8), (760, 0.8), (1160, 0.8), (1400, 0.8)): sicario_con_rifle(ctx, x, 880, s, cara="enojado")
    doctor("aterrado", "parado", sudor=True, mira=-0.4).dibujar(ctx, 960, 1000, 0.85)


def e16(ctx):  # aparece el jefe (silueta)
    interior(ctx, pared=(0.5, 0.45, 0.42), piso=(0.4, 0.33, 0.28), luz=False, zocalo=False)
    ctx.rectangle(0, 0, W, H); ctx.set_source_rgba(0.03, 0.03, 0.06, 0.75); ctx.fill()
    ctx.rectangle(790, 200, 340, 700); ctx.set_source_rgb(1, 0.9, 0.6); ctx.fill()
    ctx.move_to(790, 900); ctx.line_to(1130, 900); ctx.line_to(1500, H); ctx.line_to(420, H); ctx.close_path()
    ctx.set_source_rgba(1, 0.9, 0.6, 0.35); ctx.fill()
    jefe("serio", "jarras").dibujar(ctx, 960, 895, 1.05, silueta=True, color_silueta=(0.03, 0.03, 0.05))
    doctor("aterrado", "parado", sudor=True, mira=0.6).dibujar(ctx, 420, 1040, 1.0)


def e17(ctx):  # médico 24 horas
    interior(ctx, pared=(0.55, 0.42, 0.32), piso=(0.42, 0.32, 0.24), zocalo=True, luz=False)
    reloj(ctx, 1520, 300, 100)
    jefe("serio", "sostener").dibujar(ctx, 960, 930, 1.05)
    escritorio(ctx, 960, 640, 900, (0.42, 0.26, 0.16))
    doctor("preocupado", "parado", mira=0.3).dibujar(ctx, 330, 1020, 1.0)
    oscurecer(ctx, foco=(960, 380), radio=620, fuerza=0.55)


def e18(ctx):  # no hacer preguntas (shh)
    interior(ctx, pared=(0.55, 0.42, 0.32), piso=(0.42, 0.32, 0.24), luz=False)
    m = jefe("enojado", "parado")
    primer_plano(ctx, m, 1180, 470, 250)
    cx, cy, R = m.cabeza
    redondo(ctx, cx - 22, cy + R * 0.05, 44, R * 0.75, 22); pintar(ctx, BLANCO, 6)
    circulo(ctx, cx, cy + R * 0.95, 62, BLANCO, 6)
    doctor("aterrado", "parado", sudor=True, mira=0.6).dibujar(ctx, 440, 1000, 0.95)
    texto(ctx, "SHHH…", 1580, 180, 70, BLANCO, borde=TINTA, peso="Black")
    oscurecer(ctx, foco=(960, 420), radio=640, fuerza=0.5, bombilla=False)


def e19(ctx):  # comprende la verdad (primer plano)
    liso(ctx, (0.35, 0.36, 0.42))
    for i in range(30):
        a = 2 * math.pi * i / 30
        linea(ctx, [(960 + math.cos(a) * 420, 540 + math.sin(a) * 420), (960 + math.cos(a) * 1200, 540 + math.sin(a) * 1200)],
              10, (0.28, 0.29, 0.34))
    primer_plano(ctx, doctor("aterrado", sudor=True), 960, 540, 340)


def e20(ctx):  # fila de sicarios
    interior(ctx, pared=(0.42, 0.4, 0.4), piso=(0.32, 0.3, 0.3), luz=False)
    for (x, c, p) in ((380, "enojado", "rapado"), (720, "serio", None), (1060, "enojado", "rapado"), (1400, "serio", None)):
        sicario_con_rifle(ctx, x + 80, 960, 1.2, cara=c, pelo=p)
    oscurecer(ctx, foco=(960, 300), radio=760, fuerza=0.45)


def e21(ctx):  # maletín de dinero
    interior(ctx, pared=(0.55, 0.42, 0.32), piso=(0.42, 0.32, 0.24), luz=False, zocalo=False)
    ctx.rectangle(0, 680, W, 400); pintar(ctx, (0.45, 0.28, 0.17), 0)
    linea(ctx, [(0, 680), (W, 680)], 8, (0.3, 0.18, 0.1))
    maletin_dinero(ctx, 960, 690, 1.55)
    oscurecer(ctx, foco=(960, 450), radio=720, fuerza=0.4, bombilla=False)


def e22(ctx):  # VS
    ctx.rectangle(0, 0, W / 2, H); ctx.set_source_rgb(0.86, 0.88, 0.92); ctx.fill()
    ctx.rectangle(W / 2, 0, W / 2, H); ctx.set_source_rgb(0.82, 0.9, 0.82); ctx.fill()
    linea(ctx, [(W / 2, 0), (W / 2, H)], 10)
    m = doctor("triste", "mostrar_d").dibujar(ctx, 520, 950, 1.05)
    mx, my = m.manos["d"]
    ctx.rectangle(mx + 10, my - 40, 110, 60); pintar(ctx, (0.99, 0.98, 0.93), 4); texto(ctx, "$ 300", mx + 65, my - 10, 26, TINTA)
    for i, (x, y) in enumerate([(1250, 820), (1450, 820), (1650, 820), (1350, 740), (1550, 740), (1450, 660), (1350, 900), (1550, 900)]):
        fajo(ctx, x, y, 1.0)
    texto(ctx, "$ 50,000", 1450, 300, 90, VERDE_DINERO, borde=TINTA, peso="Black")
    texto(ctx, "RECIÉN GRADUADO", 520, 230, 52, TINTA)
    vs(ctx, W / 2, 540, 230)


def e23(ctx):  # una condición
    interior(ctx, pared=(0.55, 0.42, 0.32), piso=(0.42, 0.32, 0.24), luz=False)
    jefe("serio", "dedo_arriba").dibujar(ctx, 1150, SUELO, 1.3)
    doctor("preocupado", "parado", mira=0.6).dibujar(ctx, 520, SUELO, 1.1)
    texto(ctx, "1", 1360, 200, 140, ROJO, borde=TINTA, peso="Black")
    oscurecer(ctx, foco=(960, 380), radio=650, fuerza=0.5)


def e24(ctx):  # absoluta discreción
    liso(ctx, (0.2, 0.21, 0.26))
    circulo(ctx, 960, 560, 300, CARA, 10)
    ctx.new_path(); ctx.move_to(780, 620); ctx.line_to(1140, 620); ctx.set_source_rgb(*TINTA); ctx.set_line_width(14); ctx.stroke()
    for x in range(800, 1130, 30): linea(ctx, [(x, 600), (x + 10, 640)], 6)
    for lado in (-1, 1): ctx.new_path(); ctx.arc(960 + lado * 110, 470, 26, 0, 2 * math.pi); ctx.set_source_rgb(*TINTA); ctx.fill()
    candado(ctx, 1190, 760, 0.9)
    texto(ctx, "DISCRECIÓN", 960, 160, 120, BLANCO, borde=TINTA, peso="Black")


def e25(ctx):  # atender heridas
    interior(ctx, pared=(0.85, 0.87, 0.88), ventana=(1350, 140, 330, 260))
    mesa(ctx, 1450, 690, 420); botiquin(ctx, 1400, 690); libros(ctx, 1560, 690, 2, 0.6)
    s = sicario("enojado", "vendar").dibujar(ctx, 1000, SUELO, 1.15)
    mx, my = s.manos["d"]
    doctor("serio", "vendar", mira=0.6).dibujar(ctx, 650, SUELO, 1.15)
    ctx.rectangle(mx - 70, my - 50, 50, 40); pintar(ctx, BLANCO, 3)
    for k in range(3): linea(ctx, [(mx - 70, my - 45 + k * 12), (mx - 20, my - 40 + k * 12)], 2, (0.85, 0.3, 0.3))


def e26(ctx):  # atrapado (barrotes)
    interior(ctx, pared=(0.7, 0.72, 0.74), luz=False)
    mesa(ctx, 1300, 700, 360); botiquin(ctx, 1300, 700)
    doctor("triste", "parado").dibujar(ctx, 900, SUELO, 1.15)
    for x in (1550, 1750): sicario_con_rifle(ctx, x, SUELO, 1.0, cara="serio")
    oscurecer(ctx, foco=(900, 420), radio=560, fuerza=0.5)
    for x in range(120, W, 150):
        linea(ctx, [(x, 0), (x, H)], 30); linea(ctx, [(x, 0), (x, H)], 18, (0.45, 0.47, 0.5))


def e27(ctx):  # no pueden ir al hospital
    exterior(ctx, suelo_y=760, noche=True)
    edificio_hospital(ctx, 560, 760, 0.95)
    x_roja(ctx, 560, 470, 560, 520)
    mansion(ctx, 1380, 760, 0.62, noche=True)
    camioneta(ctx, 1350, 960, 0.75, faros=True)


def e28(ctx):  # diablito y angelito
    interior(ctx, pared=(0.86, 0.88, 0.92))
    m = doctor("dudoso", "parado").dibujar(ctx, 960, SUELO + 40, 1.3)
    diablito(ctx, 640, 470, 1.5); angel(ctx, 1280, 470, 1.5)
    for (x, y, r) in ((560, 430, -20), (520, 560, 15)): billete(ctx, x, y, 0.8, r)


def e29(ctx):  # paciente crítico de noche
    interior(ctx, pared=(0.6, 0.62, 0.66), luz=False)
    camilla(ctx, 900, 740, 1.0)
    for x in (560, 1240): sicario("enojado", "sostener").dibujar(ctx, x, SUELO, 1.05)
    doctor("aterrado", "correr", sudor=True, mira=-0.6).dibujar(ctx, 1600, SUELO, 1.1)
    oscurecer(ctx, foco=(960, 420), radio=640, fuerza=0.6)
    cruz_medica(ctx, 300, 200, 40, (0.95, 0.25, 0.25))


def e30(ctx):  # mira sus manos
    liso(ctx, (0.3, 0.31, 0.36))
    m = doctor("triste", "mirar_manos").dibujar(ctx, 960, 1000, 1.45)
    for mano in m.manos.values():
        circulo(ctx, mano[0], mano[1], 26, (0.75, 0.85, 0.95), 5)
    oscurecer(ctx, foco=(960, 380), radio=520, fuerza=0.7)


def e31(ctx):  # quiere renunciar
    interior(ctx, pared=(0.55, 0.42, 0.32), piso=(0.42, 0.32, 0.24), luz=False)
    escritorio(ctx, 1300, 640, 700, (0.42, 0.26, 0.16))
    m = doctor("preocupado", "entregar", sudor=True).dibujar(ctx, 620, SUELO, 1.15)
    mx, my = m.manos["d"]
    sobre(ctx, mx + 120, my - 20, 0.8, rot=-8)


def e32(ctx):  # conoces demasiados secretos
    interior(ctx, pared=(0.5, 0.38, 0.3), piso=(0.4, 0.3, 0.22), luz=False)
    primer_plano(ctx, jefe("malvado"), 1150, 470, 290)
    carpeta(ctx, 560, 640, 1.1)
    oscurecer(ctx, foco=(1100, 420), radio=600, fuerza=0.6, bombilla=False)


def e33(ctx):  # el mayor error
    interior(ctx, pared=(0.56, 0.58, 0.62), luz=False)
    m = doctor("triste", "cabeza", sudor=True)
    ctx.save(); ctx.translate(0, 120); m.dibujar(ctx, 760, SUELO, 1.0); ctx.restore()
    cx, cy, R = m.cabeza

    def recuerdo(c):
        telefono(c, 1300, 430, 1.4)
        texto(c, "¿Necesitas", 1300, 410, 30, TINTA); texto(c, "trabajo?", 1300, 450, 30, TINTA)
    burbuja(ctx, 1300, 430, 520, 460, hacia=(cx + R, cy + 120 - R * 0.3), contenido=recuerdo)
    oscurecer(ctx, foco=(900, 400), radio=620, fuerza=0.55)


def e34(ctx):  # foto rota
    interior(ctx, pared=(0.8, 0.82, 0.86), zocalo=False)
    foto_rota(ctx, 960, 470, 1.35)
    linea(ctx, [(960, 220), (960, 150)], 6); circulo(ctx, 960, 145, 10, (0.5, 0.5, 0.5), 3)


def e35(ctx):  # sombra gigante
    liso(ctx, (0.75, 0.73, 0.72))
    for (x, s) in ((520, 1.75), (1400, 1.75)): sicario().dibujar(ctx, x, 1100, s, silueta=True, color_silueta=(0.12, 0.12, 0.15))
    jefe("malvado", "jarras").dibujar(ctx, 960, 1130, 1.85, silueta=True, color_silueta=(0.05, 0.05, 0.08))
    doctor("aterrado", "parado", sudor=True).dibujar(ctx, 960, 1010, 0.62)


def e36(ctx):  # ¿tú qué harías?
    liso(ctx, (0.88, 0.9, 0.93))
    primer_plano(ctx, doctor("serio"), 960, 540, 320)
    texto(ctx, "?", 1480, 330, 220, ROJO, borde=TINTA, peso="Black")


def e37(ctx):  # ¿aceptarías el dinero?
    liso(ctx, (0.84, 0.9, 0.84))
    maletin_dinero(ctx, 960, 700, 1.7)
    texto(ctx, "?", 1580, 280, 200, ROJO, borde=TINTA, peso="Black")


def e38(ctx):  # cruce de caminos
    exterior(ctx, suelo_y=520, suelo=(0.62, 0.72, 0.5))
    # mitad izquierda oscura
    ctx.rectangle(0, 0, W / 2, 520); ctx.set_source_rgba(0.05, 0.05, 0.12, 0.6); ctx.fill()
    g = cairo.RadialGradient(1500, 520, 20, 1500, 520, 380)
    g.add_color_stop_rgba(0, 1, 0.85, 0.4, 0.95); g.add_color_stop_rgba(1, 1, 0.85, 0.4, 0)
    ctx.set_source(g); ctx.paint()
    circulo(ctx, 1500, 520, 90, (1, 0.85, 0.35), 0)
    for (pts, col) in (([(860, H), (1060, H), (700, 560), (640, 560)], (0.5, 0.48, 0.45)),
                       ([(860, H), (1060, H), (1290, 560), (1230, 560)], (0.75, 0.68, 0.55))):
        ctx.new_path(); ctx.move_to(*pts[0])
        for p in pts[1:]: ctx.line_to(*p)
        ctx.close_path(); pintar(ctx, col, 5)
    mansion(ctx, 470, 560, 0.4, noche=True)
    ctx.rectangle(1360, 470, 160, 90); pintar(ctx, (0.95, 0.96, 0.98), 4); cruz_medica(ctx, 1440, 510, 20)
    billete(ctx, 330, 300, 0.9, -15); billete(ctx, 600, 260, 0.9, 20)
    doctor("dudoso", "parado", mira=0.0).dibujar(ctx, 960, 1060, 0.9)
    texto(ctx, "?", 960, 230, 160, ROJO, borde=TINTA, peso="Black")


ESCENAS = [globals()[f"e{i:02d}"] for i in range(1, 39)]


if __name__ == "__main__":
    salida = sys.argv[1] if len(sys.argv) > 1 else "salida"
    os.makedirs(salida, exist_ok=True)
    cuales = [int(a) for a in sys.argv[2:]] or list(range(1, 39))
    for n in cuales:
        sup, ctx = lienzo()
        ESCENAS[n - 1](ctx)
        sup.write_to_png(os.path.join(salida, f"{n:02d}.png"))
        print("escena", n)
