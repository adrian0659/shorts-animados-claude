"""Short stickman: «Tiró a la basura 8.000 bitcoins» (James Howells), con la voz del usuario (55.6 s).

Datos (de la narración, verificados en prensa):
- 2013: James Howells (Newport, Gales) tiró por error un disco duro con la llave de ~8.000 BTC minados en 2009.
- El disco terminó en el vertedero de Docksway, Newport. La ciudad negó la excavación varias veces,
  aunque él ofreció compartir lo recuperado.
- Enero de 2025: el Tribunal Superior desestimó su demanda. La ciudad planea cerrar el vertedero
  y poner paneles solares. Él ha dicho que intentaría comprar el terreno.
  (BBC News, ene 2025; The Guardian, ene 2025)

Ejecutar desde la carpeta stickman/:
    python3 proyectos/bitcoin/bitcoin.py --fotos   # hoja de revisión
    python3 proyectos/bitcoin/bitcoin.py           # video final
"""
import os, sys, math, json, random, subprocess, wave
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", ".."))
import motor
from motor import *
import sonido as snd
import numpy as np

SAL = os.path.join(AQUI, "salida"); os.makedirs(SAL, exist_ok=True)
VOZ = os.path.join(AQUI, "voz.wav")
DUR = 55.6
SUELO = 1500
ORO = (1.0, 0.78, 0.15)
AMARILLO = (1, 0.85, 0.1)

# ---------------------------------------------------------------- tiempos por palabra
PAL = json.load(open(os.path.join(AQUI, "palabras.json")))
for p in PAL:  # correcciones a la transcripción
    if p["w"] == "gales,": p["w"] = "Gales,"

def _limpia(w): return w.lower().strip("¿?¡!.,;:")
def en(palabra, n=1):
    """Segundo en que empieza la n-ésima aparición de la palabra en la voz."""
    c = 0
    for p in PAL:
        if _limpia(p["w"]) == palabra:
            c += 1
            if c == n: return p["s"]
    raise KeyError(palabra)

# ---------------------------------------------------------------- poses nuevas
POSES.update({
    "cargar":   dict(torso=182, cabeza=6, bi=40, ai=100, bd=55, ad=105, mi=-8, pi=-4, md=8, pd=4),
    "lanzar":   dict(torso=188, cabeza=10, bi=-40, ai=-30, bd=150, ad=130, mi=-14, pi=-6, md=16, pd=8),
    "ofrecer":  dict(torso=184, cabeza=8, bi=70, ai=95, bd=80, ad=100, mi=-8, pi=-4, md=8, pd=4),
    "cruzado":  dict(torso=180, cabeza=-4, bi=-28, ai=95, bd=28, ad=-95, mi=-10, pi=-5, md=10, pd=5),
    "palear":   dict(torso=196, cabeza=14, bi=40, ai=70, bd=60, ad=45, mi=-16, pi=-8, md=20, pd=10),
    "mazo_arr": dict(torso=180, cabeza=4, bi=-14, ai=-6, bd=160, ad=175, mi=-8, pi=-4, md=8, pd=4),
    "mazo_abj": dict(torso=184, cabeza=10, bi=-14, ai=-6, bd=95, ad=70, mi=-8, pi=-4, md=8, pd=4),
})
motor.ARTIC = list(POSES["parado"].keys())

def mano(x, y, s, pose, lado="d"):
    """Dónde queda la mano de un monigote (para ponerle objetos)."""
    p = POSES[pose]
    def v(a, l): return vec(a, l * s)
    pi = (v(p["mi"], 92)[0] + v(p["pi"], 88)[0], v(p["mi"], 92)[1] + v(p["pi"], 88)[1])
    pd = (v(p["md"], 92)[0] + v(p["pd"], 88)[0], v(p["md"], 92)[1] + v(p["pd"], 88)[1])
    cad = (x, y - max(pi[1], pd[1]))
    h = (cad[0] + v(p["torso"], 150)[0], cad[1] + v(p["torso"], 150)[1])
    b, a = (p["bd"], p["ad"]) if lado == "d" else (p["bi"], p["ai"])
    return h[0] + v(b, 82)[0] + v(a, 78)[0], h[1] + v(b, 82)[1] + v(a, 78)[1]

def cabeza_y(y, s): return y - 396 * s

# ---------------------------------------------------------------- utilería
def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()

def disco(brillo=False):
    def f(ctx, t, k):
        if brillo:
            g = cairo.RadialGradient(0, 0, 40, 0, 0, 220)
            g.add_color_stop_rgba(0, 1, 0.9, 0.3, 0.7); g.add_color_stop_rgba(1, 1, 0.9, 0.3, 0)
            ctx.set_source(g); ctx.arc(0, 0, 220, 0, 2 * math.pi); ctx.fill()
        rrect(ctx, -110, -75, 220, 150, 18); contorno(ctx, (0.74, 0.76, 0.8), 9)
        ctx.arc(-25, 0, 52, 0, 2 * math.pi); contorno(ctx, (0.9, 0.91, 0.94), 6)
        ctx.arc(-25, 0, 10, 0, 2 * math.pi); contorno(ctx, (0.5, 0.52, 0.56), 4)
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(7); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(70, -45); ctx.line_to(5, 20); ctx.stroke()
        rrect(ctx, 45, 35, 50, 24, 5); contorno(ctx, (0.25, 0.3, 0.38), 4)
        for (sx, sy) in [(-95, -60), (95, -60), (-95, 60), (95, 60)]:
            ctx.arc(sx, sy, 5, 0, 2 * math.pi); ctx.set_source_rgb(*TINTA); ctx.fill()
    return f

def bolsa(abierta=False):
    def f(ctx, t, k):
        ctx.move_to(-40, -110)
        ctx.curve_to(-150, -60, -170, 90, -100, 130); ctx.curve_to(-40, 160, 60, 160, 110, 125)
        ctx.curve_to(175, 80, 150, -60, 40, -110); ctx.close_path()
        contorno(ctx, (0.13, 0.13, 0.16), 9)
        ctx.set_source_rgba(1, 1, 1, 0.18); ctx.set_line_width(14); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(-95, -20); ctx.curve_to(-110, 30, -100, 70, -80, 95); ctx.stroke()
        if abierta:
            ctx.save(); ctx.scale(1, 0.35); ctx.arc(0, -330, 70, 0, 2 * math.pi); ctx.restore()
            contorno(ctx, (0.05, 0.05, 0.06), 7)
        else:
            for lado in (-1, 1):
                ctx.move_to(0, -110); ctx.curve_to(lado * 30, -170, lado * 75, -175, lado * 55, -135)
                ctx.close_path(); contorno(ctx, (0.13, 0.13, 0.16), 7)
    return f

def bote():
    def f(ctx, t, k):
        ctx.move_to(-115, -300); ctx.line_to(115, -300); ctx.line_to(95, 0); ctx.line_to(-95, 0); ctx.close_path()
        contorno(ctx, (0.45, 0.6, 0.5), 9)
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(6)
        for xx in (-50, 0, 50):
            ctx.move_to(xx, -260); ctx.line_to(xx * 0.85, -40); ctx.stroke()
        rrect(ctx, -135, -335, 270, 40, 12); contorno(ctx, (0.38, 0.52, 0.43), 9)
    return f

def btc(tam, color):
    """Símbolo ₿ dibujado (la fuente no lo trae): una B con dos rayitas arriba y abajo."""
    def f(ctx, t, k):
        texto("B", tam, color)(ctx, t, k)
        ctx.set_source_rgb(*color); ctx.set_line_width(tam * 0.09); ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        for dx in (-0.12, 0.08):
            for (y0, y1) in ((-0.5, -0.36), (0.36, 0.5)):
                ctx.move_to(tam * dx, tam * y0); ctx.line_to(tam * dx, tam * y1); ctx.stroke()
    return f

def moneda(r=60):
    def f(ctx, t, k):
        ctx.arc(0, 0, r, 0, 2 * math.pi); contorno(ctx, ORO, max(4, r * 0.12))
        ctx.arc(0, 0, r * 0.78, 0, 2 * math.pi); ctx.set_source_rgb(0.9, 0.62, 0.08)
        ctx.set_line_width(r * 0.06); ctx.stroke()
        btc(r * 1.05, (0.62, 0.38, 0.02))(ctx, t, k)
        ctx.set_source_rgba(1, 1, 1, 0.55); ctx.arc(-r * 0.45, -r * 0.45, r * 0.13, 0, 2 * math.pi); ctx.fill()
    return f

def billete():
    def f(ctx, t, k):
        rrect(ctx, -85, -45, 170, 90, 8); contorno(ctx, (0.55, 0.82, 0.5), 6)
        ctx.arc(0, 0, 26, 0, 2 * math.pi); contorno(ctx, (0.75, 0.92, 0.7), 4)
        texto("$", 40, (0.15, 0.4, 0.15))(ctx, t, k)
    return f

def escritorio(abre=None):
    """abre(t) -> 0..1, cuánto sale el cajón."""
    def f(ctx, t, k):
        a = abre(t) if abre else 0
        ctx.rectangle(-260, -330, 520, 34); contorno(ctx, (0.72, 0.5, 0.3), 9)
        for xx in (-240, 200):
            ctx.rectangle(xx, -296, 40, 296); contorno(ctx, (0.62, 0.42, 0.25), 8)
        ctx.rectangle(-200, -296, 400, 150); contorno(ctx, (0.66, 0.46, 0.27), 8)
        if a > 0.01:
            ctx.rectangle(-170, -280, 340, 110); contorno(ctx, (0.12, 0.08, 0.06), 6)
        oy = 90 * a; sc = 1 + 0.12 * a
        ctx.save(); ctx.translate(0, -225 + oy); ctx.scale(sc, sc)
        if a > 0.01:
            ctx.move_to(-170, -55); ctx.line_to(170, -55); ctx.line_to(150, -55 - 60 * a); ctx.line_to(-150, -55 - 60 * a)
            ctx.close_path(); contorno(ctx, (0.5, 0.33, 0.18), 6)
        rrect(ctx, -175, -55, 350, 110, 8); contorno(ctx, (0.8, 0.58, 0.36), 8)
        rrect(ctx, -45, -12, 90, 24, 10); contorno(ctx, (0.35, 0.25, 0.15), 6)
        ctx.restore()
    return f

def perfil_monton(x):  # altura de la montaña de basura (x relativo al centro)
    return 380 * math.exp(-(x / 400) ** 2) + 40 * math.exp(-((x + 380) / 160) ** 2)

def monton(semilla=4):
    rnd = random.Random(semilla)
    cosas = []
    for _ in range(70):
        x = rnd.uniform(-620, 620); top = perfil_monton(x)
        y = -rnd.uniform(10, max(12, top - 15))
        cosas.append((x, y, rnd.choice("bcl"), rnd.uniform(14, 34), rnd.uniform(0, 6.3),
                      rnd.choice([(0.85, 0.3, 0.25), (0.3, 0.5, 0.8), (0.9, 0.8, 0.3), (0.2, 0.2, 0.22), (0.95, 0.95, 0.92)])))
    def f(ctx, t, k):
        ctx.move_to(-700, 30)
        for xx in range(-700, 701, 20):
            ctx.line_to(xx, -perfil_monton(xx) + math.sin(xx * 0.09) * 7)
        ctx.line_to(700, 30); ctx.close_path()
        ctx.save(); contorno(ctx, (0.56, 0.5, 0.42), 9); ctx.restore()
        ctx.save()
        ctx.move_to(-700, 30)
        for xx in range(-700, 701, 20): ctx.line_to(xx, -perfil_monton(xx) + math.sin(xx * 0.09) * 7)
        ctx.line_to(700, 30); ctx.close_path(); ctx.clip()
        for (x, y, tipo, r, ang, col) in cosas:
            ctx.save(); ctx.translate(x, y); ctx.rotate(ang)
            if tipo == "b": ctx.arc(0, 0, r, 0, 2 * math.pi)
            elif tipo == "c": ctx.rectangle(-r, -r * 0.45, r * 2, r * 0.9)
            else: ctx.move_to(-r, r * 0.5); ctx.line_to(0, -r); ctx.line_to(r, r * 0.5); ctx.close_path()
            contorno(ctx, col, 4); ctx.restore()
        ctx.restore()
    return f

def letrero(txt, tam=52, color=(0.95, 0.88, 0.7), alto=260):
    def f(ctx, t, k):
        ctx.rectangle(-10, -alto, 20, alto); contorno(ctx, (0.5, 0.34, 0.2), 6)
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(tam)
        w = ctx.text_extents(txt).x_advance + 50
        rrect(ctx, -w / 2, -alto - 70, w, tam + 40, 10); contorno(ctx, color, 7)
        ctx.save(); ctx.translate(0, -alto - 70 + (tam + 40) / 2); texto(txt, tam)(ctx, t, k); ctx.restore()
    return f

def ayuntamiento():
    def f(ctx, t, k):
        ctx.rectangle(-230, -520, 460, 520); contorno(ctx, (0.88, 0.85, 0.78), 9)
        ctx.move_to(-260, -520); ctx.line_to(0, -680); ctx.line_to(260, -520); ctx.close_path()
        contorno(ctx, (0.78, 0.74, 0.66), 9)
        for xx in (-170, -60, 50, 160):
            ctx.rectangle(xx - 18 + 5, -470, 26, 400); contorno(ctx, (0.96, 0.94, 0.9), 6)
        rrect(ctx, -60, -150, 120, 150, 50); contorno(ctx, (0.45, 0.3, 0.2), 7)
        ctx.save(); ctx.translate(0, -495); texto("AYUNTAMIENTO", 34)(ctx, t, k); ctx.restore()
    return f

def sello(txt, tam=150, ang=-12):
    def f(ctx, t, k):
        ctx.rotate(math.radians(ang))
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(tam)
        w = ctx.text_extents(txt).x_advance + tam * 0.6; h = tam * 1.25
        rrect(ctx, -w / 2, -h / 2, w, h, 20)
        ctx.set_source_rgba(1, 1, 1, 0.85); ctx.fill_preserve()
        ctx.set_source_rgb(0.85, 0.1, 0.12); ctx.set_line_width(tam * 0.1); ctx.stroke()
        texto(txt, tam, (0.85, 0.1, 0.12))(ctx, t, k)
    return f

def estrado():
    def f(ctx, t, k):
        ctx.rectangle(-320, -380, 640, 380); contorno(ctx, (0.55, 0.33, 0.18), 10)
        ctx.rectangle(-350, -410, 700, 40); contorno(ctx, (0.45, 0.27, 0.14), 9)
        for xx in (-200, 0, 200):
            rrect(ctx, xx - 70, -320, 140, 260, 10); contorno(ctx, (0.62, 0.39, 0.22), 6)
        ctx.save(); ctx.translate(0, -190); texto("⚖", 120, (0.95, 0.8, 0.3), fuente="DejaVu Sans")(ctx, t, k); ctx.restore()
    return f

def mazo(ang_fn):
    def f(ctx, t, k):
        ctx.rotate(math.radians(ang_fn(t)))
        ctx.rectangle(-8, -10, 16, 120); contorno(ctx, (0.55, 0.33, 0.18), 5)
        rrect(ctx, -55, -45, 110, 50, 10); contorno(ctx, (0.45, 0.27, 0.14), 7)
    return f

def pala():
    def f(ctx, t, k):
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(-30, -40); ctx.line_to(110, 250); ctx.set_source_rgb(*TINTA); ctx.set_line_width(22); ctx.stroke_preserve()
        ctx.set_source_rgb(0.7, 0.5, 0.3); ctx.set_line_width(12); ctx.stroke()
        ctx.save(); ctx.translate(120, 275); ctx.rotate(math.radians(-26))
        ctx.move_to(-38, -20); ctx.line_to(38, -20); ctx.line_to(30, 50); ctx.line_to(0, 70); ctx.line_to(-30, 50); ctx.close_path()
        contorno(ctx, (0.7, 0.72, 0.76), 7); ctx.restore()
    return f

def escoba(t0):
    def f(ctx, t, k):
        ctx.rotate(math.radians(math.sin((t - t0) * 9) * 14))
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(-20, -60); ctx.line_to(80, 260); ctx.set_source_rgb(*TINTA); ctx.set_line_width(20); ctx.stroke_preserve()
        ctx.set_source_rgb(0.75, 0.55, 0.3); ctx.set_line_width(10); ctx.stroke()
        ctx.save(); ctx.translate(90, 290); ctx.rotate(math.radians(-17))
        ctx.move_to(-30, -20); ctx.line_to(30, -20); ctx.line_to(60, 50); ctx.line_to(-60, 50); ctx.close_path()
        contorno(ctx, (0.92, 0.78, 0.35), 7); ctx.restore()
    return f

def polvo(semilla):
    rnd = random.Random(semilla); bol = [(rnd.uniform(-70, 70), rnd.uniform(-30, 30), rnd.uniform(25, 50)) for _ in range(6)]
    def f(ctx, t, k):
        for (bx, by, br) in bol:
            ctx.arc(bx, by, br, 0, 2 * math.pi); ctx.set_source_rgba(0.85, 0.83, 0.78, 0.9); ctx.fill_preserve()
            ctx.set_source_rgba(*TINTA, 0.6); ctx.set_line_width(4); ctx.stroke()
    return f

def llave():
    def f(ctx, t, k):
        g = cairo.RadialGradient(0, 0, 20, 0, 0, 190)
        g.add_color_stop_rgba(0, 1, 0.9, 0.4, 0.6); g.add_color_stop_rgba(1, 1, 0.9, 0.4, 0)
        ctx.set_source(g); ctx.arc(0, 0, 190, 0, 2 * math.pi); ctx.fill()
        ctx.rotate(math.radians(-30 + math.sin(t * 3) * 6))
        ctx.arc(-80, 0, 45, 0, 2 * math.pi); ctx.arc_negative(-80, 0, 20, 2 * math.pi, 0); contorno(ctx, ORO, 8)
        ctx.rectangle(-38, -12, 150, 24); contorno(ctx, ORO, 8)
        for xx in (70, 100):
            ctx.rectangle(xx, 10, 16, 32); contorno(ctx, ORO, 6)
    return f

def computadora():
    def f(ctx, t, k):
        rrect(ctx, -150, -260, 300, 230, 16); contorno(ctx, (0.85, 0.83, 0.76), 9)
        rrect(ctx, -115, -228, 230, 165, 10); contorno(ctx, (0.1, 0.25, 0.2), 6)
        ctx.save(); ctx.translate(0, -146); btc(95, (0.4, 1, 0.55))(ctx, t, k); ctx.restore()
        ctx.rectangle(-40, -30, 80, 30); contorno(ctx, (0.75, 0.73, 0.66), 7)
        rrect(ctx, -170, 0, 340, 30, 8); contorno(ctx, (0.8, 0.78, 0.7), 7)
    return f

def mesa():
    def f(ctx, t, k):
        ctx.rectangle(-200, -24, 400, 24); contorno(ctx, (0.72, 0.5, 0.3), 8)
        for xx in (-180, 160):
            ctx.rectangle(xx, 0, 20, 300); contorno(ctx, (0.62, 0.42, 0.25), 6)
    return f

def panel():
    def f(ctx, t, k):
        ctx.move_to(-70, -10); ctx.line_to(60, -10); ctx.line_to(80, -70); ctx.line_to(-50, -70); ctx.close_path()
        contorno(ctx, (0.2, 0.35, 0.75), 6)
        ctx.set_source_rgba(0.8, 0.9, 1, 0.7); ctx.set_line_width(3)
        for i in (1, 2, 3):
            ctx.move_to(-70 + 32.5 * i, -10); ctx.line_to(-50 + 32.5 * i, -70); ctx.stroke()
        ctx.move_to(-60, -40); ctx.line_to(70, -40); ctx.stroke()
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(6); ctx.move_to(0, -10); ctx.line_to(0, 10); ctx.stroke()
    return f

def sol():
    def f(ctx, t, k):
        ctx.save(); ctx.rotate(t * 0.4)
        for i in range(12):
            ctx.save(); ctx.rotate(i * math.pi / 6); ctx.rectangle(-8, 95, 16, 45); contorno(ctx, AMARILLO, 5); ctx.restore()
        ctx.restore()
        ctx.arc(0, 0, 80, 0, 2 * math.pi); contorno(ctx, AMARILLO, 8)
    return f

def marca_x():
    def f(ctx, t, k):
        p = 1 + 0.08 * math.sin(t * 6)
        g = cairo.RadialGradient(0, 0, 10, 0, 0, 170 * p)
        g.add_color_stop_rgba(0, 1, 0.85, 0.2, 0.85); g.add_color_stop_rgba(1, 1, 0.85, 0.2, 0)
        ctx.set_source(g); ctx.arc(0, 0, 170 * p, 0, 2 * math.pi); ctx.fill()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for a in (45, -45):
            ctx.save(); ctx.rotate(math.radians(a)); ctx.move_to(-60, 0); ctx.line_to(60, 0)
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(34); ctx.stroke_preserve()
            ctx.set_source_rgb(0.9, 0.15, 0.15); ctx.set_line_width(20); ctx.stroke(); ctx.restore()
    return f

def tierra_encima(t0, t1):
    """Capa de basura que crece y tapa la bolsa."""
    def f(ctx, t, k):
        a = suave((t - t0) / (t1 - t0))
        if a <= 0: return
        ctx.save(); ctx.scale(1, 0.55 + 0.45 * a); ctx.arc(0, 0, 60 + 170 * a, math.pi, 2 * math.pi); ctx.close_path(); ctx.restore()
        contorno(ctx, (0.52, 0.47, 0.4), 8)
        rnd = random.Random(9)
        for _ in range(int(14 * a)):
            ctx.save(); ctx.translate(rnd.uniform(-150, 150) * a, -rnd.uniform(5, 90) * a); ctx.rotate(rnd.uniform(0, 6))
            ctx.rectangle(-16, -8, 32, 16)
            contorno(ctx, rnd.choice([(0.85, 0.3, 0.25), (0.3, 0.5, 0.8), (0.9, 0.8, 0.3), (0.95, 0.95, 0.92)]), 4); ctx.restore()
    return f

def lluvia(t0, cosa, n=26, semilla=2, vel=900, hasta=SUELO, xs=(60, W - 60)):
    rnd = random.Random(semilla)
    datos = [(rnd.uniform(*xs), rnd.uniform(0, 1.6), rnd.uniform(0.6, 1.1), rnd.uniform(-3, 3)) for _ in range(n)]
    def f(ctx, t, k):
        for (x, d, e, giro) in datos:
            tt = t - t0 - d
            if tt < 0: continue
            y = min(-120 + tt * vel * e, hasta - 40 - 30 * e)
            ctx.save(); ctx.translate(x, y); ctx.rotate(giro * min(tt, (hasta + 120) / (vel * e)))
            ctx.scale(e, e); cosa(ctx, t, k); ctx.restore()
    return f

def billetes_volando(t0, n=14):
    rnd = random.Random(7)
    datos = [(rnd.uniform(-1, 1), rnd.uniform(0, 1.2), rnd.uniform(0.7, 1.1)) for _ in range(n)]
    b = billete()
    def f(ctx, t, k):
        for (dx, d, e) in datos:
            tt = t - t0 - d
            if tt < 0 or tt > 1.8: continue
            ctx.save(); ctx.translate(dx * 260 * tt + math.sin(tt * 5 + d * 9) * 30, -340 - 520 * tt + 120 * tt * tt)
            ctx.rotate(math.sin(tt * 4 + dx * 6) * 0.8); ctx.scale(e * 0.9, e * 0.9)
            b(ctx, t, k); ctx.restore()
    return f

def monedas_orbita(t0, n=10, radio=330):
    m = moneda(46)
    def f(ctx, t, k):
        for i in range(n):
            a = suave((t - t0 - i * 0.05) / 0.5)
            if a <= 0: continue
            ang = i * 2 * math.pi / n + (t - t0) * 0.9
            ctx.save(); ctx.translate(math.cos(ang) * radio * a, math.sin(ang) * radio * a * 0.75)
            ctx.scale(a, a); m(ctx, t, k); ctx.restore()
    return f

def mitades(t0):
    m = moneda(70)
    def f(ctx, t, k):
        sep = 50 * suave((t - t0) / 0.5)
        for lado in (-1, 1):
            ctx.save(); ctx.translate(lado * sep, 0)
            ctx.rectangle(0 if lado > 0 else -90, -90, 90, 180); ctx.clip()
            m(ctx, t, k); ctx.restore()
    return f

def burbuja(interior, cola=-1):
    def f(ctx, t, k):
        for (bx, by, br) in [(cola * 130, 150, 14), (cola * 100, 115, 22)]:
            ctx.arc(bx, by, br, 0, 2 * math.pi); contorno(ctx, (1, 1, 1), 7)
        ctx.save(); ctx.scale(1.3, 1); ctx.arc(0, 0, 110, 0, 2 * math.pi); ctx.restore()
        contorno(ctx, (1, 1, 1), 9)
        interior(ctx, t, k)
    return f

def escalado(dib, s):
    def f(ctx, t, k):
        ctx.save(); ctx.scale(s, s); dib(ctx, t, k); ctx.restore()
    return f

class Ventana:
    """Dibuja sus capas solo dentro de [t0, t1)."""
    def __init__(self, t0, t1, *capas): self.t0, self.t1, self.capas = t0, t1, capas
    def dibujar(self, ctx, t):
        if self.t0 <= t < self.t1:
            for c in self.capas: c.dibujar(ctx, t)

def fijo(dib, t0, t1, x, y, s=1.0): return Elemento(dib, t0, t1, x, y, s, entrada=0.01, salida=0.01)

# ---------------------------------------------------------------- subtítulos con tiempos reales
RESALTA = {"millones", "dólares", "2013", "james", "discos", "basura", "problema", "ocho", "mil", "bitcoins",
           "minado", "newport", "enterrada", "cientos", "no", "fortuna", "juicio", "2025", "rechazó",
           "paneles", "solares", "tierra", "disco", "seguirías", "buscando"}

class SubsVoz:
    def __init__(self, y=300, tam=82, ancho=930):
        self.y, self.tam, self.ancho = y, tam, ancho
        self.grupos, actual = [], []
        for i, p in enumerate(PAL):
            actual.append(p)
            fin = p["w"][-1] in ".,?" or len(actual) >= 4
            sig = PAL[i + 1] if i + 1 < len(PAL) else None
            if fin or sig is None or sig["s"] - p["e"] > 0.35:
                self.grupos.append(actual); actual = []
        self.tramos = []
        for i, g in enumerate(self.grupos):
            t1 = self.grupos[i + 1][0]["s"] if i + 1 < len(self.grupos) else DUR
            self.tramos.append((g[0]["s"] - 0.03, min(t1, g[-1]["e"] + 0.6), g))

    def dibujar(self, ctx, t):
        for (t0, t1, g) in self.tramos:
            if not (t0 <= t < t1): continue
            ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(self.tam)
            sp = ctx.text_extents(" ").x_advance
            renglones, act = [], []
            for p in g:
                prueba = " ".join(q["w"] for q in act + [p])
                if ctx.text_extents(prueba).x_advance > self.ancho and act: renglones.append(act); act = []
                act.append(p)
            renglones.append(act)
            for r, ren in enumerate(renglones):
                ancho = sum(ctx.text_extents(p["w"]).x_advance for p in ren) + sp * (len(ren) - 1)
                x = (W - ancho) / 2; y = self.y + r * self.tam * 1.2
                for p in ren:
                    adv = ctx.text_extents(p["w"]).x_advance
                    if t >= p["s"] - 0.04:
                        kk = max(0.01, rebote((t - p["s"] + 0.04) / 0.16))
                        ctx.save(); ctx.translate(x + adv / 2, y); ctx.scale(kk, kk)
                        ctx.move_to(-adv / 2, 0); ctx.text_path(p["w"])
                        ctx.set_source_rgb(*TINTA); ctx.set_line_width(self.tam * 0.2)
                        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
                        ctx.set_source_rgb(*(AMARILLO if _limpia(p["w"]) in RESALTA else (1, 1, 1))); ctx.fill()
                        ctx.restore()
                    x += adv + sp

# ---------------------------------------------------------------- cámara que nunca se queda quieta
class ShortCam(Short):
    def __init__(self, dur, tomas):
        super().__init__(dur); self.tomas = tomas  # [(t0, t1, esc0, esc1, cx, cy)]
        self.golpes = []  # [(t, extra)] zoom de golpe

    def cuadro(self, t):
        sup = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); ctx = cairo.Context(sup)
        ctx.set_antialias(cairo.ANTIALIAS_BEST)
        dx = dy = 0
        for (ts, f) in self.sacudidas:
            if 0 <= t - ts < 0.35:
                d = (1 - (t - ts) / 0.35) * f; dx += math.sin(t * 90) * d; dy += math.cos(t * 77) * d
        esc, cx, cy = 1.0, W / 2, H / 2
        for (a, b, e0, e1, zx, zy) in self.tomas:
            if a <= t < b: esc = lerp(e0, e1, suave((t - a) / (b - a))); cx, cy = zx, zy
        for (tg, extra) in self.golpes:
            if 0 <= t - tg < 0.5: esc *= 1 + extra * (1 - suave((t - tg) / 0.5))
        ctx.translate(dx, dy); ctx.translate(cx, cy); ctx.scale(esc, esc); ctx.translate(-cx, -cy)
        subs = [c for c in self.capas if isinstance(c, SubsVoz)]
        for c in self.capas:
            if not isinstance(c, SubsVoz): c.dibujar(ctx, t)
        ctx.identity_matrix()
        for c in subs: c.dibujar(ctx, t)
        buf = np.ndarray((H, W, 4), np.uint8, sup.get_data())
        return buf[:, :, [2, 1, 0]].copy()

# ---------------------------------------------------------------- escenas
S = [0.0, 3.3, 8.15, 11.25, 14.0, 15.05, 17.95, 19.62, 21.82, 26.18, 30.2, 37.72, 41.72, 45.5, 50.45, DUR]
c = {}
capas = []
sfx = []  # (t, nombre, vol)

fondo = Fondo([(S[0], (1.0, 0.88, 0.6)), (S[1], (0.78, 0.87, 0.96)), (S[2], (0.95, 0.86, 0.72)),
               (S[4], (0.96, 0.45, 0.4)), (S[5], (0.2, 0.24, 0.38)), (S[6], (0.75, 0.9, 0.82)),
               (S[7], (0.86, 0.8, 0.95)), (S[8], (0.74, 0.8, 0.72)), (S[10], (0.85, 0.89, 0.97)),
               (S[11], (0.93, 0.83, 0.68)), (S[12], (0.6, 0.82, 0.98)), (S[14], (0.22, 0.2, 0.26))], suelo=SUELO)
# el fondo cambia de golpe en cada corte (no fundido)
fondo_dib = fondo.dibujar
def fondo_corte(ctx, t):
    for i, (ti, col) in enumerate(fondo.colores):
        if t >= ti: cc = col
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *[min(1, v + 0.07) for v in cc]); g.add_color_stop_rgb(1, *[v * 0.88 for v in cc])
    ctx.set_source(g); ctx.paint()
    ctx.set_source_rgba(*TINTA, 0.85); ctx.set_line_width(8); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(-200, SUELO)
    for xx in range(-200, W + 201, 60): ctx.line_to(xx, SUELO + temblor(("suelo", xx), t, 2.5)[1])
    ctx.stroke()
fondo.dibujar = fondo_corte
capas.append(fondo)

# ---- 1. Gancho: tira la bolsa y salen billetes (0–3.3)
s1 = 1.4
j1 = Monigote([dict(t=0, pose="cargar", x=330, y=SUELO, mira=1),
               dict(t=0.42, pose="lanzar", x=330, y=SUELO, mira=1),
               dict(t=1.0, pose="parado", x=330, y=SUELO, mira=1),
               dict(t=1.86, pose="parado", x=330, y=SUELO, caminar=True, mira=-1),
               dict(t=3.3, pose="parado", x=-250, y=SUELO, mira=-1)], escala=s1, semilla=3)
mano_c = mano(330, SUELO, s1, "cargar")
def vuelo_bolsa(t):
    k = clamp((t - 0.42) / 0.5)
    x = lerp(mano_c[0] + 30, 820, k); y = lerp(mano_c[1] - 40, SUELO - 380, k) - math.sin(k * math.pi) * 320
    return x, y
capas += [
    fijo(bote(), 0, S[1], 820, SUELO, 1.15),
    Ventana(0, S[1], j1),
    Elemento(bolsa(), 0, 0.95, 0, 0, 0.75, mover=vuelo_bolsa, entrada=0.01, salida=0.08),
    Elemento(billetes_volando(en("millones") - 0.1, 16), 0.6, S[1], 820, SUELO - 300, 1.0, entrada=0.01),
    Elemento(texto("$$$", 150, (0.3, 0.75, 0.3), TINTA), en("dólares"), S[1], 820, 820, 1.0),
]
sfx += [(0.5, "whoosh", 0.6), (0.95, "golpe", 0.6), (en("millones"), "ding", 0.5), (en("dólares"), "pop", 0.5)]

# ---- 2. 2013, Gales, decide limpiar (3.3–8.15)
s2 = 1.35
j2 = Monigote([dict(t=S[1], pose="parado", x=-200, y=SUELO, caminar=True, mira=1),
               dict(t=en("ingeniero") - 0.1, pose="saludo", x=330, y=SUELO, cara="feliz"),
               dict(t=en("limpiar") - 0.05, pose="palear", x=330, y=SUELO, mira=1),
               dict(t=S[2], pose="palear", x=330, y=SUELO)], escala=s2, semilla=3)
capas += [
    fijo(escritorio(), S[1], S[2], 790, SUELO, 0.85),
    Elemento(texto("2013", 210, AMARILLO, TINTA), en("2013"), en("james") - 0.05, 540, 760),
    Elemento(texto("Gales, Reino Unido", 70, TINTA), en("gales"), S[2], 540, 640),
    Elemento(texto("ingeniero", 54, (1, 1, 1), TINTA), en("ingeniero"), en("gales"), 330, cabeza_y(SUELO, s2) - 110),
    Ventana(S[1], S[2], j2),
    Elemento(escoba(en("limpiar")), en("limpiar") - 0.05, S[2], *mano(330, SUELO, s2, "palear"), 1.0, entrada=0.01),
]
for i, tt in enumerate([en("limpiar") + 0.1, en("su") + 0.1, en("oficina") + 0.15, en("oficina") + 0.45]):
    capas.append(Elemento(polvo(i), tt, tt + 0.7, 470 + i * 45, SUELO - 30 - i * 10, 0.8))
    sfx.append((tt, "pop", 0.25))
sfx += [(S[1] - 0.15, "whoosh", 0.5), (en("2013"), "ding", 0.55)]

# ---- 3. El cajón con dos discos (8.15–11.25)
abre = lambda t: suave((t - en("cajón")) / 0.4)
capas += [
    fijo(escritorio(abre), S[2], S[3], 540, SUELO, 1.5),
    Elemento(disco(), en("dos"), S[3], 360, 900, 1.05),
    Elemento(disco(), en("discos"), S[3], 720, 900, 1.05),
    Elemento(texto("x2", 110, AMARILLO, TINTA), en("duros"), S[3], 540, 690),
    Elemento(polvo(11), en("viejos"), S[3], 360, 830, 0.5), Elemento(polvo(12), en("viejos") + 0.12, S[3], 720, 830, 0.5),
]
sfx += [(S[2] - 0.15, "whoosh", 0.5), (en("cajón"), "cajon", 0.6), (en("dos"), "pop", 0.6), (en("discos"), "pop", 0.6)]

# ---- 4. Uno termina en la bolsa (11.25–14.0)
def caida_disco(t):
    k = suave((t - en("terminó")) / 0.75)
    return lerp(330, 790, k), lerp(SUELO - 560, SUELO - 240, k) - math.sin(k * math.pi) * 260
t_cierra = en("basura", 2)
capas += [
    fijo(escritorio(lambda t: 1.0), S[3], S[4], 330, SUELO, 1.0),
    fijo(disco(), S[3], S[4], 400, SUELO - 400, 0.7),
    Elemento(bolsa(abierta=True), en("una") - 0.05, t_cierra, 790, SUELO - 180, 1.25, salida=0.01),
    Elemento(disco(brillo=True), S[3], en("bolsa") + 0.05, 0, 0, 0.7, mover=caida_disco, entrada=0.01, salida=0.05),
    Elemento(bolsa(), t_cierra, S[4], 790, SUELO - 180, 1.25, entrada=0.01),
]
sfx += [(S[3] - 0.15, "whoosh", 0.5), (en("terminó") + 0.1, "whoosh", 0.45), (en("bolsa") + 0.05, "golpe", 0.55),
        (t_cierra, "pop", 0.5)]

# ---- 5. ¿El problema? (14.0–15.05)
j5 = Monigote([dict(t=S[4], pose="sorpresa", x=540, y=2230, cara="sorpresa")], escala=3.3, semilla=5)
capas += [Ventana(S[4], S[5], j5), Elemento(texto("?", 260, AMARILLO, TINTA), en("problema"), S[5], 870, 620)]
sfx += [(S[4], "golpe", 0.7), (en("problema"), "boing", 0.45)]

# ---- 6a. La llave de 8.000 bitcoins (15.05–17.95)
capas += [
    fijo(disco(brillo=True), S[5], S[6], 540, 1150, 2.0),
    Elemento(llave(), en("llave"), S[6], 0, 0, 1.0,
             mover=lambda t: (540, lerp(1150, 880, suave((t - en("llave")) / 0.5)))),
    Elemento(monedas_orbita(en("bitcoins"), 12, 360), en("bitcoins"), S[6], 540, 1010, 1.0, entrada=0.01),
    Elemento(texto("8.000", 190, AMARILLO, TINTA), en("ocho"), S[6], 540, 620),
]
sfx += [(S[5] - 0.15, "whoosh", 0.5), (en("llave"), "ding", 0.55), (en("ocho"), "golpe", 0.6),
        (en("bitcoins"), "monedas", 0.5)]

# ---- 6b. Él mismo los minó en 2009 (17.95–19.62)
s6 = 1.35
j6 = Monigote([dict(t=S[6], pose="cargar", x=260, y=SUELO, cara="feliz", mira=1)], escala=s6, semilla=3)
capas += [
    fijo(mesa(), S[6], S[7], 690, SUELO - 300, 1.0),
    fijo(computadora(), S[6], S[7], 690, SUELO - 330, 1.15),
    Ventana(S[6], S[7], j6),
    Elemento(texto("2009", 150, AMARILLO, TINTA), en("él"), S[7], 540, 660),
]
for i, tt in enumerate([en("minado") - 0.1, en("minado") + 0.1, en("minado") + 0.3]):
    capas.append(Elemento(moneda(48), tt, S[7], 600 + i * 90, SUELO - 760 - (i % 2) * 70, 1.0))
    sfx.append((tt, "pop", 0.45))
sfx += [(S[6] - 0.15, "whoosh", 0.5), (en("él"), "ding", 0.45)]

# ---- 6c. Casi nadie sabía qué era (19.62–21.82)
for i, (x, col, pose) in enumerate([(220, (0.55, 0.2, 0.25), "encoger"), (540, (0.15, 0.3, 0.55), "pensar"),
                                    (860, (0.2, 0.45, 0.25), "encoger")]):
    capas.append(Ventana(S[7], S[8], Monigote([dict(t=S[7], pose=pose, x=x, y=SUELO, cara="pensar")],
                                              escala=1.1, color=col, semilla=10 + i)))
    capas.append(Elemento(texto("?", 120, (1, 1, 1), TINTA), en("nadie") + i * 0.15, S[8], x, cabeza_y(SUELO, 1.1) - 110))
    sfx.append((en("nadie") + i * 0.15, "pop", 0.4))
capas.append(Elemento(moneda(55), en("cuando"), S[8], 540, 820, 1.0))
sfx += [(S[7] - 0.15, "whoosh", 0.5)]

# ---- 7. Llega al basurero de Newport y queda enterrada (21.82–26.18)
X_BOLSA, Y_BOLSA = 560, SUELO - perfil_monton(20) + 40
def caida_bolsa(t):
    k = clamp((t - en("llegó")) / 0.45); k = k * k
    return X_BOLSA, lerp(-150, Y_BOLSA - 60, k)
capas += [
    fijo(monton(), S[8], S[10], 540, SUELO, 1.0),
    fijo(monton(), S[12], S[14], 540, SUELO, 1.0),
    Elemento(bolsa(), en("llegó"), S[9], 0, 0, 0.6, mover=caida_bolsa, entrada=0.01, salida=0.01),
    Elemento(letrero("NEWPORT"), en("newport"), S[9], 150, SUELO, 1.0),
    fijo(tierra_encima(en("enterrada"), en("desechos")), S[8], S[10], X_BOLSA, Y_BOLSA - 20, 1.0),
    fijo(tierra_encima(0, 0.01), S[12], S[14], X_BOLSA, Y_BOLSA - 20, 1.0),
    Elemento(lluvia(en("quedó"), escalado(bolsa(), 0.28), 14, 5, 1300, Y_BOLSA - 30, (X_BOLSA - 170, X_BOLSA + 170)), en("quedó"), S[9], 0, 0, 1.0, entrada=0.01),
]
sfx += [(S[8] - 0.15, "whoosh", 0.5), (en("llegó") + 0.4, "golpe", 0.6), (en("newport"), "pop", 0.5),
        (en("toneladas"), "golpe", 0.8), (en("enterrada"), "whoosh", 0.4)]

# ---- 8. Hoy valen cientos de millones (26.18–30.2)
j8 = Monigote([dict(t=S[9], pose="triste", x=120, y=SUELO - perfil_monton(120 - 540) + 15, cara="triste", mira=1)],
              escala=0.95, semilla=3)
def rayos_x(ctx, t, k):
    p = 1 + 0.1 * math.sin(t * 7)
    g = cairo.RadialGradient(0, 0, 10, 0, 0, 200 * p)
    g.add_color_stop_rgba(0, 1, 0.9, 0.3, 0.9); g.add_color_stop_rgba(1, 1, 0.9, 0.3, 0)
    ctx.set_source(g); ctx.arc(0, 0, 200 * p, 0, 2 * math.pi); ctx.fill()
    moneda(55)(ctx, t, k)
capas += [
    Elemento(texto("HOY", 150, (1, 1, 1), TINTA), en("hoy"), S[10], 540, 640),
    Elemento(rayos_x, en("esos"), S[10], X_BOLSA, Y_BOLSA - 40, 1.0),
    Elemento(lluvia(en("valen"), moneda(40), 30, 3, 1000, H + 300), en("valen"), S[10], 0, 0, 1.0, entrada=0.01),
    Elemento(texto("$ cientos de millones", 76, (0.4, 0.9, 0.4), TINTA), en("cientos"), S[10], 540, 820),
    Ventana(S[9], S[10], j8),
]
sfx += [(en("hoy"), "golpe", 0.5), (en("esos"), "ding", 0.5), (en("valen"), "monedas", 0.55), (en("cientos"), "ding", 0.5)]

# ---- 9. Pide excavar, ofrece compartir: NO y NO (30.2–37.72)
s9 = 1.2
j9 = Monigote([dict(t=S[10], pose="señalar_d", x=230, y=SUELO, cara="feliz", mira=1),
               dict(t=en("no", 1) + 0.1, pose="sorpresa", x=230, y=SUELO, cara="sorpresa", mira=1),
               dict(t=en("ofreció") - 0.05, pose="ofrecer", x=230, y=SUELO, cara="feliz", mira=1),
               dict(t=en("no", 2) + 0.1, pose="triste", x=230, y=SUELO, cara="triste", mira=1)], escala=s9, semilla=3)
of = Monigote([dict(t=S[10], pose="parado", x=640, y=SUELO, cara="serio", mira=-1),
               dict(t=en("no", 1) - 0.1, pose="cruzado", x=640, y=SUELO, cara="serio", mira=-1)],
              escala=s9, color=(0.12, 0.2, 0.45), semilla=21)
capas += [
    fijo(ayuntamiento(), S[10], S[11], 850, SUELO, 1.0),
    Ventana(S[10], S[11], of, j9),
    Elemento(burbuja(escalado(pala(), 0.45), cola=-1), en("excavar"), en("no", 1), 400, cabeza_y(SUELO, s9) - 170, 1.0),
    Elemento(sello("NO"), en("no", 1), en("ofreció"), 540, 900, 1.0, entrada=0.22),
    Elemento(mitades(en("compartir")), en("compartir"), en("no", 2), 400, cabeza_y(SUELO, s9) - 40, 1.0),
    Elemento(sello("¡NO!", 190, 10), en("no", 2), S[11], 540, 900, 1.0, entrada=0.22),
]
sfx += [(S[10] - 0.15, "whoosh", 0.5), (en("excavar"), "pop", 0.5), (en("no", 1), "sello", 0.8),
        (en("compartir"), "monedas", 0.45), (en("no", 2), "sello", 0.9)]

# ---- 10. Juicio en 2025: rechazado (37.72–41.72)
golpe = en("rechazó")
def pose_juez(t): return "mazo_abj" if t >= golpe else "mazo_arr"
juez = Monigote([dict(t=S[11], pose="parado", x=540, y=SUELO - 160, cara="serio"),
                 dict(t=en("juez") - 0.2, pose="mazo_arr", x=540, y=SUELO - 160, cara="serio"),
                 dict(t=golpe, pose="mazo_abj", x=540, y=SUELO - 160, cara="serio")], escala=1.25,
                color=(0.1, 0.1, 0.12), semilla=31)
def mazo_pos(t):
    p = "parado" if t < en("juez") - 0.2 else pose_juez(t)
    return mano(540, SUELO - 160, 1.25, p)
capas += [
    Ventana(S[11], S[12], juez),
    Elemento(mazo(lambda t: 60 if t >= golpe else -20), en("juez") - 0.2, S[12], 0, 0, 1.0, mover=mazo_pos, entrada=0.15),
    fijo(estrado(), S[11], S[12], 540, SUELO, 1.0),
    Elemento(texto("2025", 140, AMARILLO, TINTA), en("2025"), S[12], 200, 680),
    Elemento(sello("RECHAZADO", 110, -8), golpe, S[12], 540, 1240, 1.0, entrada=0.22),
]
sfx += [(S[11] - 0.15, "whoosh", 0.5), (en("2025"), "ding", 0.5), (golpe, "sello", 1.0)]

# ---- 11. Cerrar el basurero y cubrirlo con paneles solares (41.72–45.5)
capas += [
    Elemento(sol(), S[12], S[14], 900, 640, 0.8, entrada=0.01),
    Elemento(letrero("CERRADO", 50, (0.95, 0.5, 0.45), 230), en("cerrar"), S[14], 150, SUELO, 1.0),
]
paneles = []
for i, dxp in enumerate([-240, -160, -80, 0, 80, 160, 240, -120, -40, 40, 120]):
    tt = en("paneles") + i * 0.06 if i < 7 else en("solares") + (i - 7) * 0.06
    y = SUELO - perfil_monton(dxp) + 20 - (0 if i < 7 else 0)
    paneles.append(Elemento(panel(), tt, S[14], 540 + dxp, y, 1.0))
    sfx.append((tt, "pop", 0.25))
capas += paneles
sfx += [(S[12] - 0.15, "whoosh", 0.5), (en("cerrar"), "golpe", 0.45)]

# ---- 12. James sigue buscando comprar el terreno (45.5–50.45)
def y_monton(x): return SUELO - perfil_monton(x - 540) + 20
j12 = Monigote([dict(t=S[13], pose="palear", x=-120, y=y_monton(-120), caminar=True, mira=1),
                dict(t=en("comprar"), pose="palear", x=260, y=y_monton(260), cara="pensar", mira=1),
                dict(t=S[14], pose="palear", x=300, y=y_monton(300), mira=1)], escala=0.9, semilla=3)
def pos_pala(t):
    x = j12.estado(t)[1]; return mano(x, y_monton(x), 0.9, "palear")
capas += [
    Ventana(S[13], S[14], j12),
    Elemento(escalado(pala(), 0.75), S[13], S[14], 0, 0, 1.0, mover=pos_pala, entrada=0.01),
    Elemento(letrero("¿SE VENDE?", 46, (0.98, 0.9, 0.55), 200), en("comprar"), S[14], 870, SUELO, 1.0),
    Elemento(marca_x(), en("donde"), S[14], X_BOLSA + 60, Y_BOLSA - 100, 0.85),
    Elemento(disco(), en("disco", 2), S[14], X_BOLSA + 60, Y_BOLSA - 330, 0.6),
]
sfx += [(S[13] - 0.15, "whoosh", 0.5), (en("comprar"), "pop", 0.5), (en("donde"), "ding", 0.55), (en("disco", 2), "pop", 0.5)]

# ---- 13. Remate (50.45–55.6)
jf = Monigote([dict(t=S[14], pose="parado", x=540, y=SUELO, cara="serio"),
               dict(t=en("seguirías") - 0.2, pose="pensar", x=540, y=SUELO, cara="pensar", mira=1)], escala=1.15, semilla=3)
capas += [
    Elemento(bolsa(), en("bolsa", 3), DUR, 250, 780, 1.2),
    Elemento(texto("=", 160, (1, 1, 1), TINTA), en("ocho", 2) - 0.25, DUR, 540, 780),
    Elemento(moneda(130), en("ocho", 2), DUR, 830, 780, 1.0),
    Elemento(texto("8.000", 90, AMARILLO, TINTA), en("bitcoins", 3), DUR, 830, 970),
    Ventana(en("tú") - 0.25, DUR + 1, jf),
    Elemento(texto("?", 200, AMARILLO, TINTA), en("buscando", 2), DUR, 330, 1180),
]
sfx += [(S[14] - 0.15, "whoosh", 0.5), (en("bolsa", 3), "golpe", 0.6), (en("ocho", 2), "monedas", 0.5),
        (en("tú"), "whoosh", 0.35), (en("buscando", 2), "ding", 0.5)]

capas.append(SubsVoz())

# ---------------------------------------------------------------- cámara
tomas = [
    (S[0], S[1], 1.0, 1.06, 600, 1150), (S[1], S[2], 1.0, 1.06, 540, 1100), (S[2], S[3], 1.0, 1.1, 540, 1000),
    (S[3], S[4], 1.0, 1.07, 620, 1150), (S[4], S[5], 1.0, 1.12, 540, 900), (S[5], S[6], 1.0, 1.08, 540, 1000),
    (S[6], S[7], 1.0, 1.06, 500, 1150), (S[7], S[8], 1.04, 1.0, 540, 1200), (S[8], S[9], 1.0, 1.1, 560, 1150),
    (S[9], S[10], 1.1, 1.02, 560, 1150), (S[10], S[11], 1.0, 1.06, 500, 1150), (S[11], S[12], 1.0, 1.08, 540, 1050),
    (S[12], S[13], 1.02, 1.0, 540, 1150), (S[13], S[14], 1.0, 1.08, 560, 1150), (S[14], DUR, 1.0, 1.07, 540, 1000),
]
short = ShortCam(DUR, tomas).agregar(*capas)
for tt in (en("problema"), en("ocho"), en("toneladas"), en("no", 1), en("no", 2), golpe, en("bolsa", 3)):
    short.sacudir(tt, 16)
short.golpes += [(S[4], 0.12), (en("ocho"), 0.06), (en("no", 2), 0.06), (golpe, 0.08)]

# ---------------------------------------------------------------- sonido
SR = snd.SR
def golpe_snd(d=0.35):
    t = np.arange(int(SR * d)) / SR
    return np.sin(2 * np.pi * (55 + 90 * np.exp(-t * 25)) * t) * np.exp(-t * 14) * 0.9
def sello_snd():
    g = golpe_snd(0.3); n = np.random.default_rng(4).standard_normal(len(g)) * np.exp(-np.arange(len(g)) / SR * 40) * 0.35
    return g + n
def monedas_snd():
    s = np.zeros(int(SR * 0.9)); rng = np.random.default_rng(8)
    for i in range(7):
        d = snd.ding(rng.uniform(1800, 2600), 0.35) * 0.5; o = int(SR * (i * 0.08 + rng.uniform(0, 0.03)))
        s[o:o + len(d)] += d[:len(s) - o]
    return s
def cajon_snd():
    t = np.arange(int(SR * 0.4)) / SR; n = np.random.default_rng(2).standard_normal(len(t))
    return n * 0.25 * np.sin(np.pi * t / 0.4) * (0.5 + 0.5 * np.sin(2 * np.pi * 30 * t))
GEN = {"pop": lambda: snd.pop(), "whoosh": lambda: snd.whoosh(), "ding": lambda: snd.ding(), "boing": lambda: snd.boing(),
       "golpe": golpe_snd, "sello": sello_snd, "monedas": monedas_snd, "cajon": cajon_snd}

def leer_voz():
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", VOZ, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

def mezclar(ruta):
    n = int(SR * DUR)
    voz = leer_voz()[:n]; voz = np.pad(voz, (0, n - len(voz)))
    pico_voz = np.abs(voz).max()
    musica = snd.musica(DUR, bpm=92)[:n]; musica = np.pad(musica, (0, n - len(musica)))
    musica *= pico_voz * 0.16 / max(1e-6, np.abs(musica).max())  # ~ -16 dB bajo la voz
    efectos = np.zeros(n + SR)
    for (t, nombre, vol) in sfx:
        s = GEN[nombre](); o = int(t * SR); e = min(len(efectos), o + len(s)); efectos[o:e] += s[:e - o] * vol
    efectos = efectos[:n] * pico_voz * 0.32  # ~ -10 dB bajo la voz
    total = voz + musica + efectos
    total = total / max(1e-6, np.abs(total).max()) * 0.9
    tmp = ruta + ".tmp.wav"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((total * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                    "-ar", str(SR), ruta], check=True)
    os.remove(tmp)

if __name__ == "__main__":
    if "--fotos" in sys.argv:
        from PIL import Image
        ts = [0.6, 2.4, 5.6, 7.2, 9.9, 12.4, 14.5, 17.4, 18.9, 20.8, 25.0, 28.8, 34.6, 37.2, 40.8, 44.9, 49.3, 54.9]
        fotos = []
        for tt in ts:
            im = Image.fromarray(short.cuadro(tt)).resize((270, 480)); fotos.append(im); print("foto", tt)
        hoja = Image.new("RGB", (270 * 6, 480 * 3), "white")
        for i, im in enumerate(fotos): hoja.paste(im, ((i % 6) * 270, (i // 6) * 480))
        hoja.save(os.path.join(SAL, "hoja.png"))
    else:
        audio = os.path.join(SAL, "mezcla.wav")
        mezclar(audio)
        short.render(os.path.join(SAL, "bitcoin_basura.mp4"), audio=audio)
