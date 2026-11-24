"""Short: «¿Cómo saber si tienes PREDIABETES?» (≈72 s, 1080x1920).

Datos (fuentes):
- CDC, "Prediabetes – Your Chance to Prevent Type 2 Diabetes": en EE. UU. 98 millones de adultos
  (más de 1 de cada 3) tienen prediabetes y más del 80 % no lo sabe.
- ADA, Standards of Care in Diabetes (criterios diagnósticos):
  glucosa en ayunas 100–125 mg/dL · HbA1c 5.7–6.4 % · curva de tolerancia a 2 h 140–199 mg/dL.
  Diabetes: ayunas >= 126 mg/dL · HbA1c >= 6.5 %. Revisión a partir de los 35 años (o antes con factores de riesgo).
- Diabetes Prevention Program (NEJM 2002): bajar 5–7 % del peso + 150 min/semana de actividad
  redujo 58 % el riesgo de pasar a diabetes tipo 2.
- Señales posibles: acantosis nigricans (piel oscura en cuello/axilas), sed, cansancio (Mayo Clinic).

Ejecutar desde la carpeta stickman/:
    python3 ejemplos/prediabetes.py            # video -> salida/prediabetes.mp4
    python3 ejemplos/prediabetes.py --fotos    # fotos de revisión -> salida/pd_*.png
"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from motor import *
import sonido as snd

DUR = 72.0
SUELO = 1560
os.makedirs("salida", exist_ok=True)

AMARILLO = (1, 0.85, 0.1)
ROJO = (0.9, 0.22, 0.25)
VERDE = (0.25, 0.75, 0.4)
NARANJA = (1.0, 0.65, 0.15)
BLANCO = (1, 1, 1)

# ---------------- guion (texto en pantalla). *palabra* = resaltada
guion = [
    (0.3, 4.6,   "En EE. UU., más de *1 de cada 3* adultos tiene *prediabetes*…"),
    (4.6, 8.4,   "…y *8 de cada 10* ni siquiera lo saben."),
    (8.4, 13.2,  "¿Qué es? Tu *azúcar en la sangre* está más alta de lo normal…"),
    (13.2, 17.4, "…pero todavía *no* llega a ser diabetes."),
    (17.4, 21.6, "El problema: casi *nunca da síntomas*."),
    (21.6, 27.6, "Algunas pistas: *piel oscura* en cuello o axilas, mucha *sed* y *cansancio*."),
    (27.6, 34.6, "¿Tienes *más riesgo*? Revisa esta lista:"),
    (34.6, 38.6, "La única forma de saberlo: un *análisis de sangre*."),
    (38.6, 45.6, "Glucosa en ayunas: de *100 a 125* mg/dL es *prediabetes*."),
    (45.6, 52.6, "Hemoglobina A1c: de *5.7 a 6.4 %* es *prediabetes*."),
    (52.6, 56.6, "La buena noticia: se puede *revertir*."),
    (56.6, 63.6, "Bajar del *5 al 7 %* de tu peso y caminar *30 minutos* al día baja tu riesgo un *58 %*."),
    (63.6, 68.2, "Pídele a tu médico el *análisis*. Es rápido y sencillo."),
    (68.2, 72.0, "¡*Compártelo* con alguien que lo necesite!"),
]

fondo = Fondo([(0, (1.0, 0.86, 0.55)), (8.4, (0.98, 0.72, 0.72)), (17.4, (0.75, 0.82, 0.95)),
               (27.6, (0.98, 0.8, 0.6)), (34.6, (0.7, 0.88, 0.95)), (52.6, (0.7, 0.93, 0.72)),
               (63.6, (1.0, 0.86, 0.55))], suelo=SUELO)


class Ventana:
    """Dibuja una capa solo entre t0 y t1."""
    def __init__(self, capa, t0, t1): self.capa, self.t0, self.t1 = capa, t0, t1
    def dibujar(self, ctx, t):
        if self.t0 <= t < self.t1: self.capa.dibujar(ctx, t)


# ---------------- dibujos nuevos
def interrogacion(color=AMARILLO):
    def f(ctx, t, k):
        ctx.save(); ctx.rotate(math.sin(t * 5) * 0.15); texto("?", 120, color, TINTA)(ctx, t, k); ctx.restore()
    return f


def cubo_azucar():
    def f(ctx, t, k):
        ctx.save(); ctx.rotate(math.sin(t * 2) * 0.2)
        ctx.rectangle(-45, -45, 90, 90); contorno(ctx, (1, 1, 1), 8)
        ctx.set_source_rgba(0.7, 0.7, 0.75, 0.7)
        for (a, b) in [(-20, -15), (15, 10), (-5, 25), (20, -25)]:
            ctx.arc(a, b, 5, 0, 2 * math.pi); ctx.fill()
        ctx.restore()
    return f


def vaso_sangre():
    """Un vaso sanguíneo con glóbulos rojos y cubos de azúcar que fluyen."""
    def f(ctx, t, k):
        ctx.rectangle(-560, -150, 1120, 300)
        ctx.set_source_rgb(0.95, 0.55, 0.55); ctx.fill()
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(12)
        for y in (-150, 150):
            ctx.move_to(-560, y)
            for x in range(-560, 561, 40): ctx.line_to(x, y + math.sin(x * 0.02 + t * 2) * 6)
            ctx.stroke()
        for i in range(7):
            x = ((i * 170 + t * 160) % 1200) - 600
            y = math.sin(i * 1.7) * 80
            ctx.save(); ctx.translate(x, y); ctx.scale(1, 0.6)
            ctx.arc(0, 0, 42, 0, 2 * math.pi); contorno(ctx, ROJO, 7)
            ctx.restore()
        n_az = int(2 + 6 * clamp((t - 9.5) / 3))
        for i in range(n_az):
            x = ((i * 150 + 60 + t * 200) % 1200) - 600
            y = math.cos(i * 2.3) * 85
            ctx.save(); ctx.translate(x, y); ctx.scale(0.45, 0.45); cubo_azucar()(ctx, t + i, k); ctx.restore()
    return f


def barra_rango(titulo, cortes, etiquetas, valor, t_mov, unidad=""):
    """Barra con tres zonas (normal, prediabetes, diabetes) y un marcador que se mueve hasta 'valor'.
    cortes: (min, c1, c2, max) en las unidades de la prueba."""
    mn, c1, c2, mx = cortes
    ANCHO = 900
    def px(v): return -ANCHO / 2 + (v - mn) / (mx - mn) * ANCHO
    def f(ctx, t, k):
        ctx.save(); ctx.translate(0, -215); texto(titulo, 62, BLANCO, TINTA)(ctx, t, k); ctx.restore()
        zonas = [(mn, c1, VERDE, "Normal"), (c1, c2, NARANJA, "Prediabetes"), (c2, mx, ROJO, "Diabetes")]
        for (a, b, col, nom) in zonas:
            ctx.rectangle(px(a), -50, px(b) - px(a), 100); contorno(ctx, col, 9)
            ctx.save(); ctx.translate((px(a) + px(b)) / 2, 110)
            texto(nom, 38 if nom == "Prediabetes" else 42, TINTA)(ctx, t, k); ctx.restore()
        for v, et in zip((c1, c2), etiquetas):
            ctx.save(); ctx.translate(px(v), -90); texto(et, 46, TINTA)(ctx, t, k); ctx.restore()
        # marcador
        kv = suave((t - t_mov) / 1.6)
        v = lerp(mn, valor, kv)
        x = px(v) + (math.sin(t * 9) * 4 if kv >= 1 else 0)
        ctx.move_to(x, -60); ctx.line_to(x - 34, -125); ctx.line_to(x + 34, -125); ctx.close_path()
        contorno(ctx, BLANCO, 8)
        if kv >= 1:
            ctx.save(); ctx.translate(x, 215)
            esc = max(0.01, rebote(clamp((t - t_mov - 1.6) / 0.3))); ctx.scale(esc, esc)
            texto("¡ALERTA!", 70, AMARILLO, TINTA)(ctx, t, k); ctx.restore()
    return f


def cuello_mancha():
    """Cabeza de perfil con mancha oscura en el cuello (acantosis nigricans)."""
    def f(ctx, t, k):
        ctx.set_line_width(14); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.rectangle(-45, 40, 90, 120); ctx.set_source_rgb(0.98, 0.85, 0.72); ctx.fill()
        ctx.set_source_rgba(0.35, 0.25, 0.18, 0.75)
        ctx.rectangle(-45, 70, 90, 60); ctx.fill()
        ctx.set_source_rgb(*TINTA); ctx.move_to(-45, 40); ctx.line_to(-45, 160)
        ctx.move_to(45, 40); ctx.line_to(45, 160); ctx.stroke()
        ctx.arc(0, -40, 95, 0, 2 * math.pi); contorno(ctx, (0.98, 0.85, 0.72), 12)
        for lado in (-1, 1):
            ctx.set_source_rgb(*TINTA); ctx.arc(lado * 32, -55, 10, 0, 2 * math.pi); ctx.fill()
        ctx.set_line_width(9); ctx.move_to(-25, 5); ctx.line_to(25, 5); ctx.stroke()
        # lupa
        ctx.save(); ctx.translate(120 + math.sin(t * 3) * 8, 120)
        ctx.set_line_width(22); ctx.move_to(40, 40); ctx.line_to(95, 95); ctx.stroke()
        ctx.arc(0, 0, 60, 0, 2 * math.pi); ctx.set_source_rgba(0.8, 0.95, 1, 0.45); ctx.fill_preserve()
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(12); ctx.stroke(); ctx.restore()
    return f


def vaso_agua():
    def f(ctx, t, k):
        ctx.move_to(-70, -100); ctx.line_to(70, -100); ctx.line_to(50, 100); ctx.line_to(-50, 100); ctx.close_path()
        contorno(ctx, (0.9, 0.97, 1), 10)
        nivel = -30 + math.sin(t * 3) * 6
        ctx.move_to(-64 + (nivel + 100) * 0.1, nivel); ctx.line_to(64 - (nivel + 100) * 0.1, nivel)
        ctx.line_to(50, 95); ctx.line_to(-50, 95); ctx.close_path()
        ctx.set_source_rgba(0.3, 0.6, 1, 0.8); ctx.fill()
    return f


def bateria_baja():
    def f(ctx, t, k):
        ctx.rectangle(-110, -55, 200, 110); contorno(ctx, (1, 1, 1), 10)
        ctx.rectangle(90, -22, 26, 44); contorno(ctx, TINTA, 6)
        if int(t * 3) % 2 == 0:
            ctx.rectangle(-95, -40, 45, 80); ctx.set_source_rgb(*ROJO); ctx.fill()
    return f


def palomita(color=VERDE):
    def f(ctx, t, k):
        ctx.arc(0, 0, 40, 0, 2 * math.pi); contorno(ctx, color, 7)
        ctx.set_source_rgb(1, 1, 1); ctx.set_line_width(12); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(-18, 0); ctx.line_to(-4, 16); ctx.line_to(20, -16); ctx.stroke()
    return f


def renglon(txt):
    def f(ctx, t, k):
        palomita(ROJO)(ctx, t, k)
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(64); ctx.move_to(70, 22); ctx.text_path(txt)
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(12); ctx.stroke_preserve()
        ctx.set_source_rgb(1, 1, 1); ctx.fill()
    return f


def tubo_ensayo():
    def f(ctx, t, k):
        ctx.save(); ctx.rotate(0.25 + math.sin(t * 2) * 0.05)
        ctx.move_to(-55, -200); ctx.line_to(-55, 150); ctx.arc_negative(0, 150, 55, math.pi, 0)
        ctx.line_to(55, -200); ctx.close_path(); contorno(ctx, (0.93, 0.97, 1), 10)
        ctx.move_to(-46, -20); ctx.line_to(-46, 150); ctx.arc_negative(0, 150, 46, math.pi, 0)
        ctx.line_to(46, -20); ctx.close_path(); ctx.set_source_rgb(*ROJO); ctx.fill()
        ctx.rectangle(-75, -240, 150, 50); contorno(ctx, (0.35, 0.55, 0.95), 9)
        ctx.restore()
    return f


def bascula():
    def f(ctx, t, k):
        ctx.rectangle(-130, -40, 260, 80); contorno(ctx, (0.92, 0.92, 0.95), 9)
        ctx.rectangle(-55, -25, 110, 45); contorno(ctx, (0.75, 0.95, 0.8), 6)
        ctx.save(); ctx.translate(0, -2); texto("-7%", 34, TINTA)(ctx, t, k); ctx.restore()
        # flecha hacia abajo
        dy = math.sin(t * 5) * 10
        ctx.move_to(0, -210 + dy); ctx.line_to(0, -110 + dy)
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(22); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.stroke()
        ctx.move_to(-45, -140 + dy); ctx.line_to(0, -85 + dy); ctx.line_to(45, -140 + dy); ctx.stroke()
        ctx.set_source_rgb(*VERDE); ctx.set_line_width(12)
        ctx.move_to(0, -210 + dy); ctx.line_to(0, -110 + dy); ctx.stroke()
        ctx.move_to(-45, -140 + dy); ctx.line_to(0, -85 + dy); ctx.line_to(45, -140 + dy); ctx.stroke()
    return f


def reloj():
    def f(ctx, t, k):
        ctx.arc(0, 0, 95, 0, 2 * math.pi); contorno(ctx, (1, 1, 1), 10)
        ctx.set_source_rgb(*TINTA); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_width(12); ctx.move_to(0, 0); ctx.line_to(0, -55); ctx.stroke()
        a = t * 3; ctx.set_line_width(8); ctx.move_to(0, 0); ctx.line_to(math.sin(a) * 75, -math.cos(a) * 75); ctx.stroke()
        ctx.move_to(0, 0); ctx.arc(0, 0, 80, -math.pi / 2, -math.pi / 2 + math.pi)
        ctx.close_path(); ctx.set_source_rgba(0.25, 0.75, 0.4, 0.35); ctx.fill()
        ctx.save(); ctx.translate(0, 140); texto("30 min", 54, BLANCO, TINTA)(ctx, t, k); ctx.restore()
    return f


def aviso():
    def f(ctx, t, k):
        texto("Información educativa. No sustituye la consulta médica.", 32, TINTA)(ctx, t, k)
    return f


# ---------------- personajes
# gancho: tres adultos, uno de ellos (rojo) con prediabetes
gente = [
    Ventana(Monigote([dict(t=0, pose="parado", x=230, y=SUELO, cara="feliz"),
                      dict(t=4.6, pose="encoger", x=230, y=SUELO, cara="pensar")], escala=1.2, semilla=3), 0, 8.4),
    Ventana(Monigote([dict(t=0, pose="parado", x=540, y=SUELO, cara="feliz"),
                      dict(t=1.8, pose="sorpresa", x=540, y=SUELO, cara="sorpresa"),
                      dict(t=4.6, pose="encoger", x=540, y=SUELO, cara="pensar")], escala=1.2, color=ROJO, semilla=5), 0, 8.4),
    Ventana(Monigote([dict(t=0, pose="parado", x=850, y=SUELO, cara="feliz"),
                      dict(t=4.6, pose="encoger", x=850, y=SUELO, cara="pensar")], escala=1.2, semilla=7), 0, 8.4),
]

yo = Ventana(Monigote([
    dict(t=8.4,  pose="parado", x=-150, y=SUELO, caminar=True, cara="feliz"),
    dict(t=9.6,  pose="señalar_d", x=170, y=SUELO, cara="pensar", mira=1),
    dict(t=13.2, pose="encoger", x=170, y=SUELO, cara="feliz"),
    dict(t=17.0, pose="encoger", x=170, y=SUELO, cara="feliz"),
    dict(t=17.4, pose="festejar", x=170, y=SUELO, caminar=True, cara="feliz"),
    dict(t=18.4, pose="festejar", x=540, y=SUELO, cara="feliz"),
    dict(t=19.8, pose="pensar", x=540, y=SUELO, cara="pensar"),
    dict(t=21.2, pose="pensar", x=540, y=SUELO, cara="pensar"),
    dict(t=21.6, pose="parado", x=540, y=SUELO, caminar=True, cara="serio"),
    dict(t=22.6, pose="señalar_d", x=180, y=SUELO, cara="serio", mira=1),
    dict(t=27.6, pose="pensar", x=150, y=SUELO, cara="pensar", mira=1),
    dict(t=34.6, pose="señalar_d", x=170, y=SUELO, cara="feliz", mira=1),
    dict(t=38.6, pose="sorpresa", x=105, y=SUELO, cara="sorpresa"),
    dict(t=40.0, pose="señalar_d", x=105, y=SUELO, cara="serio", mira=1),
    dict(t=42.4, pose="pensar", x=105, y=SUELO, cara="pensar", mira=1),
    dict(t=45.6, pose="señalar_d", x=105, y=SUELO, cara="serio", mira=1),
    dict(t=49.0, pose="pensar", x=105, y=SUELO, cara="pensar", mira=1),
    dict(t=52.2, pose="pensar", x=105, y=SUELO, cara="pensar", mira=1),
    dict(t=52.6, pose="festejar", x=105, y=SUELO, caminar=True, saltar=True, cara="feliz"),
    dict(t=53.6, pose="festejar", x=540, y=SUELO, saltar=True, cara="feliz"),
    dict(t=56.2, pose="festejar", x=540, y=SUELO, cara="feliz"),
    dict(t=56.6, pose="parado", x=540, y=SUELO, caminar=True, cara="feliz"),
    dict(t=57.6, pose="señalar_d", x=180, y=SUELO, cara="feliz", mira=1),
    dict(t=63.2, pose="señalar_d", x=180, y=SUELO, cara="feliz", mira=1),
    dict(t=63.6, pose="parado", x=180, y=SUELO, caminar=True, cara="feliz"),
    dict(t=64.4, pose="señalar_d", x=480, y=SUELO, cara="feliz", mira=1),
    dict(t=68.2, pose="saludo", x=480, y=SUELO, cara="feliz"),
], escala=1.45), 8.4, DUR)

# ---------------- elementos
LINEA_Y = 1000
el = [
    # gancho
    Elemento(texto("1 de cada 3", 120, AMARILLO, TINTA), 1.6, 4.6, 540, 830),
    Elemento(interrogacion(), 5.0, 8.4, 230, 1000),
    Elemento(interrogacion(), 5.2, 8.4, 540, 1000),
    Elemento(interrogacion(), 5.4, 8.4, 850, 1000),
    Elemento(texto("8 de 10 no lo saben", 80, BLANCO, TINTA), 5.8, 8.4, 540, 820),
    # qué es: azúcar en la sangre
    Elemento(vaso_sangre(), 8.6, 13.2, 540, 900, 0.85),
    Elemento(texto("+ AZÚCAR", 90, AMARILLO, TINTA), 10.4, 13.2, 700, 1180),
    Elemento(barra_rango("Tu azúcar", (70, 100, 126, 160), ("", ""), 113, 13.6), 13.2, 17.4, 560, 760, 0.95),
    # sin síntomas
    Elemento(texto("SIN SÍNTOMAS", 110, BLANCO, TINTA), 17.8, 21.6, 540, 650),
    Elemento(texto("…en silencio", 64, TINTA), 19.0, 21.6, 540, 780),
    # pistas
    Elemento(cuello_mancha(), 22.4, 27.6, 720, 760, 1.0),
    Elemento(texto("piel oscura", 52, BLANCO, TINTA), 22.9, 27.6, 720, 1010),
    Elemento(vaso_agua(), 24.6, 27.6, 560, 1200, 0.8),
    Elemento(texto("sed", 52, BLANCO, TINTA), 24.8, 27.6, 560, 1330),
    Elemento(bateria_baja(), 25.8, 27.6, 870, 1200, 0.8),
    Elemento(texto("cansancio", 52, BLANCO, TINTA), 26.0, 27.6, 870, 1330),
    # factores de riesgo
    Elemento(renglon("Sobrepeso"), 28.4, 34.6, 360, 700, 1.0),
    Elemento(renglon("Más de 35 años"), 29.8, 34.6, 360, 850, 1.0),
    Elemento(renglon("Familia con diabetes"), 31.2, 34.6, 330, 1000, 0.92),
    Elemento(renglon("Poco ejercicio"), 32.6, 34.6, 360, 1150, 1.0),
    # análisis
    Elemento(tubo_ensayo(), 35.2, 38.6, 760, 1050, 1.3),
    Elemento(gota(ROJO), 35.6, 38.6, 960, 760, 0.6),
    # rangos
    Elemento(barra_rango("Glucosa en ayunas", (70, 100, 126, 160), ("100", "126"), 112, 40.2, "mg/dL"),
             38.6, 45.6, 560, 860, 1.0),
    Elemento(barra_rango("Hemoglobina A1c", (4.8, 5.7, 6.5, 7.6), ("5.7%", "6.5%"), 6.0, 47.2), 45.6, 52.6, 560, 860, 1.0),
    Elemento(texto("(promedio de 3 meses)", 44, TINTA), 46.4, 52.6, 640, 1190),
    # buena noticia
    Elemento(texto("¡REVERSIBLE!", 120, VERDE, TINTA), 53.0, 56.6, 540, 700),
    Elemento(bascula(), 57.4, 63.6, 600, 1040, 1.1),
    Elemento(reloj(), 59.4, 63.6, 860, 800, 0.9),
    Elemento(texto("-58% riesgo", 90, AMARILLO, TINTA), 61.4, 63.6, 660, 1330),
    # cierre
    Elemento(tubo_ensayo(), 64.2, 68.2, 820, 1050, 1.0),
    Elemento(texto("¡COMPÁRTELO!", 110, AMARILLO, TINTA), 68.6, 72.0, 540, 660),
    Elemento(aviso(), 63.8, 72.0, 540, 1760, 1.0, entrada=0.2),
]

short = Short(DUR).agregar(fondo, *gente, *el, yo, Subtitulos(guion, y=300, tam=80))
short.sacudir(1.8, 20); short.sacudir(5.8, 12); short.sacudir(17.8, 16)
short.sacudir(41.8, 14); short.sacudir(48.8, 14); short.sacudir(53.0, 16)
short.zoom(10.0, 13.0, 1.08, 540, 900)
short.zoom(22.6, 24.4, 1.1, 720, 800)
short.zoom(40.4, 45.2, 1.08, 560, 880)
short.zoom(47.4, 52.2, 1.08, 560, 880)
short.zoom(61.0, 63.4, 1.08, 540, 1100)

# ---------------- voz (una toma por línea del guion en voz/01.mp3 … voz/14.mp3)
# Si están todas, el video se re-cronometra para seguir a la voz: cada tramo del guion dura lo que
# dura su frase (+ una pausa corta) y el tiempo "viejo" de cada cuadro se obtiene interpolando.
import subprocess, numpy as np
VOZ_DIR = os.path.join(os.path.dirname(__file__), "..", "voz")
PAUSA = 0.35

def cargar_voz(ruta):
    """Decodifica a 44.1 kHz mono y quita el silencio del principio y del final."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-ac", "1", "-ar", str(snd.SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).astype(np.float64)
    voz = np.nonzero(np.abs(a) > 0.02)[0]
    return a[max(0, voz[0] - 400): voz[-1] + 2000] if len(voz) else a

clips = [os.path.join(VOZ_DIR, f"{i:02d}.mp3") for i in range(1, len(guion) + 1)]
CON_VOZ = all(os.path.exists(c) for c in clips) and "--sin-voz" not in sys.argv
viejos = [g[0] for g in guion] + [DUR]          # límites de tramo en el tiempo original
if CON_VOZ:
    voces = [cargar_voz(c) for c in clips]
    nuevos = [viejos[0]]
    for v in voces: nuevos.append(nuevos[-1] + len(v) / snd.SR + PAUSA)
    nuevos[-1] += 0.6                             # colchón al final
else:
    nuevos = list(viejos)
viejos = [0.0] + viejos; nuevos = [0.0] + nuevos
DUR_FINAL = nuevos[-1]

def a_viejo(T): return float(np.interp(T, nuevos, viejos))
def a_nuevo(t): return float(np.interp(t, viejos, nuevos))

_cuadro = short.cuadro
short.cuadro = lambda T: _cuadro(a_viejo(T))
short.dur = DUR_FINAL

# ---------------- sonido (los tiempos se escriben en el reloj original y se convierten)
class MezclaRetimed(snd.Mezcla):
    def poner(self, t, sonido, vol=1.0, nuevo=False):
        super().poner(t if nuevo else a_nuevo(t), sonido, vol)

FX = 0.3 if CON_VOZ else 1.0                      # con voz, música y efectos ~10 dB abajo
mez = MezclaRetimed(DUR_FINAL)
mez.poner(0, snd.musica(DUR_FINAL), 0.5 * FX * 0.8, nuevo=True)
for tt in (8.4, 17.4, 21.6, 27.6, 34.6, 38.6, 45.6, 52.6, 56.6, 63.6, 68.2):
    mez.poner(tt - 0.15, snd.whoosh(), 0.5 * FX)
mez.poner(1.6, snd.boing(), 0.9 * FX); mez.poner(1.8, snd.ding(), 0.6 * FX)
for tt in (5.0, 5.2, 5.4): mez.poner(tt, snd.pop(), 0.8 * FX)
mez.poner(10.4, snd.pop(), 0.8 * FX)
for tt in (22.4, 24.6, 25.8, 28.4, 29.8, 31.2, 32.6, 35.2, 59.4): mez.poner(tt, snd.pop(), 0.7 * FX)
for tt in (41.8, 48.8): mez.poner(tt, snd.ding(440, 1.2), 0.7 * FX)
for tt in (35.6, 36.4): mez.poner(tt, snd.latido(), 0.8 * FX)
mez.poner(53.0, snd.tada(), 0.8 * FX); mez.poner(61.4, snd.ding(), 0.7 * FX)
mez.poner(68.6, snd.tada(), 0.8 * FX)
if CON_VOZ:
    for t0, v in zip(nuevos[1:-1], voces):
        mez.poner(t0 + 0.05, v / max(1e-6, np.abs(v).max()) * 0.9, 1.0, nuevo=True)
else:
    for tt in Subtitulos(guion).palabras_tiempos(): mez.poner(tt, snd.pop(0.05), 0.1)

if __name__ == "__main__":
    print("con voz" if CON_VOZ else "sin voz", f"- duración {DUR_FINAL:.1f} s")
    if "--fotos" in sys.argv:
        for tt in (3.5, 7.5, 12.0, 16.5, 20.5, 27.0, 34.0, 37.5, 44.0, 51.0, 55.5, 62.8, 67.0, 71.0):
            short.foto(a_nuevo(tt), f"salida/pd_{tt:04.1f}.png"); print("foto", tt)
    else:
        mez.guardar("salida/prediabetes_mezcla.wav")
        # volumen final de redes: -14 LUFS
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", "salida/prediabetes_mezcla.wav",
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "salida/prediabetes.wav"], check=True)
        short.render("salida/prediabetes.mp4", audio="salida/prediabetes.wav")
