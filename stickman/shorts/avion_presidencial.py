"""Short «POV: eres el piloto del avión presidencial» (69 s, 1080x1920) con la voz del usuario.

Ejecutar desde la carpeta stickman/:
    python3 shorts/avion_presidencial.py --fotos   # una foto por escena -> salida/avion/
    python3 shorts/avion_presidencial.py           # video final -> salida/avion_presidencial.mp4
"""
import os, sys, json, math, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from motor import *
import sonido as snd

CARPETA = os.path.join(os.path.dirname(__file__), "avion_presidencial")
VOZ = os.path.join(CARPETA, "voz.mp3")
DUR = 69.4
os.makedirs("salida/avion", exist_ok=True)

# ---------------------------------------------------------------- subtítulos (tiempos de la transcripción)
pal = json.load(open(os.path.join(CARPETA, "palabras.json")))
pal = [dict(w="POV,", a=0.0, b=0.7)] + pal[3:]                       # «P.O.B.» -> «POV»
resaltar = {"presidencial", "2", "madrugada", "presidente", "privada", "ruta", "nadie", "cerrar", "armados",
            "sobre", "vivos", "temblar", "miles", "peligro", "confíe", "obedecerías"}
lineas = subtitulos_desde_palabras(pal, resaltar, cambios={"Abordo": "A bordo"})
GLOBOS = [(19.5, 23.2), (42.9, 46.3), (60.85, 64.6)]       # ahí el texto ya va en el globo de diálogo
lineas = [l for l in lineas if not any(a <= l[0] < b for a, b in GLOBOS)]
subs = Subtitulos(lineas, y=250, tam=78)

# ---------------------------------------------------------------- reparto y vestuario
SUELO_CAB = 1900          # en la cabina el tablero tapa las piernas: parecen sentados
def piloto(claves, escala=1.5, **kw):
    return Personaje(claves, escala=escala, vestuario="piloto", pelo=PELO_CAFE, semilla=3, **kw)
def copiloto(claves, escala=1.4):
    return Personaje(claves, escala=escala, vestuario="piloto", peinado="chongo", pelo=RUBIO,
                     accesorios=("charreteras",), semilla=5)
def presidente(claves, escala=1.3):
    return Personaje(claves, escala=escala, vestuario="presidente", semilla=7)
def agente(claves, escala=1.4, semilla=9, **kw):
    return Personaje(claves, escala=escala, vestuario="agente", semilla=semilla, **kw)

env = habla_desde_audio(VOZ)
env_agente = env.copy(); env_agente[:int(42.9 * FPS)] = 0; env_agente[int(46.2 * FPS):] = 0

# ---------------------------------------------------------------- fondos
def cabina(alerta_desde=None):
    def f(ctx, t):
        g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.22, 0.24, 0.3); g.add_color_stop_rgb(1, 0.12, 0.13, 0.17)
        ctx.set_source(g); ctx.paint()
        for lado in (-1, 1):
            q = [(540 + lado * 470, 230), (540 + lado * 22, 170), (540 + lado * 22, 1010), (540 + lado * 450, 1090)]
            ctx.move_to(*q[0]); [ctx.line_to(*p) for p in q[1:]]; ctx.close_path()
            ctx.save(); ctx.clip(); cielo_noche(ctx, t, alto=1100, velocidad=260); ctx.restore()
            ctx.move_to(*q[0]); [ctx.line_to(*p) for p in q[1:]]; ctx.close_path()
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(16); ctx.stroke()
            ctx.move_to(540 + lado * 400, 260); ctx.line_to(540 + lado * 300, 420)
            ctx.set_source_rgba(1, 1, 1, 0.18); ctx.set_line_width(14); ctx.stroke()
        if alerta_desde is not None and t >= alerta_desde and (t * 2.5) % 1 < 0.5:
            ctx.set_source_rgba(0.9, 0.05, 0.05, 0.28); ctx.paint()
    return Dibujo(f)

def tablero(ctx, t):
    ctx.move_to(0, 1560); ctx.curve_to(300, 1500, 780, 1500, W, 1560); ctx.line_to(W, H); ctx.line_to(0, H); ctx.close_path()
    contorno(ctx, (0.17, 0.18, 0.21), 12)
    for i, gx in enumerate((150, 330, 750, 930)):
        ctx.arc(gx, 1680, 62, 0, 2 * math.pi); contorno(ctx, (0.06, 0.07, 0.08), 8)
        a = math.sin(t * (0.7 + i * 0.3) + i) * 1.2 - 0.6
        ctx.move_to(gx, 1680); ctx.line_to(gx + math.cos(a) * 46, 1680 + math.sin(a) * 46)
        ctx.set_source_rgb(1, 0.6, 0.2); ctx.set_line_width(7); ctx.stroke()
    for i in range(10):
        on = int(t * 3 + i * 1.7) % 3 != 0
        ctx.rectangle(400 + (i % 5) * 60, 1640 + (i // 5) * 70, 40, 34)
        ctx.set_source_rgb(*((0.2, 0.9, 0.4) if i % 3 else (1, 0.75, 0.2)) if on else (0.25, 0.27, 0.3)); ctx.fill()

def salon(ctx, t):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, 0.95, 0.92, 0.84); g.add_color_stop_rgb(1, 0.86, 0.81, 0.7)
    ctx.set_source(g); ctx.paint()
    for i in range(4):
        cx = 150 + i * 260
        ctx.save(); ctx.translate(cx, 820); ctx.scale(0.7, 1); ctx.arc(0, 0, 90, 0, 2 * math.pi); ctx.restore()
        ctx.save(); ctx.clip(); cielo_noche(ctx, t + i, alto=H, nubes=False); ctx.restore()
        ctx.save(); ctx.translate(cx, 820); ctx.scale(0.7, 1); ctx.arc(0, 0, 90, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(10); ctx.stroke()
    ctx.rectangle(0, 1180, W, 60); contorno(ctx, (0.55, 0.36, 0.2), 8)
    ctx.rectangle(-10, 1690, W + 20, 300); contorno(ctx, (0.18, 0.26, 0.5), 10)
    ctx.arc(540, 520, 85, 0, 2 * math.pi); contorno(ctx, (0.9, 0.72, 0.25), 8)
    Personaje._estrella(None, ctx, 540, 520, 50, (0.98, 0.9, 0.6))

def pasillo(ctx, t):
    ctx.set_source_rgb(0.25, 0.27, 0.32); ctx.paint()
    ctx.rectangle(110, 560, 420, 1400); ctx.set_source_rgb(0.86, 0.82, 0.72); ctx.fill()
    for i in range(4):
        ctx.arc(320, 640 + i * 10, 140 - i * 30, 0, math.pi); ctx.set_source_rgba(1, 0.95, 0.75, 0.25); ctx.fill()
    ctx.rectangle(110, 560, 420, 1400); ctx.set_source_rgb(*TINTA); ctx.set_line_width(14); ctx.stroke()
    ctx.move_to(530, 560); ctx.line_to(640, 520); ctx.line_to(640, 1990); ctx.line_to(530, 1960); ctx.close_path()
    contorno(ctx, (0.4, 0.42, 0.48), 12)
    ctx.rectangle(-10, 1820, W + 20, 200); contorno(ctx, (0.15, 0.16, 0.2), 10)

def exterior(ctx, t):
    cielo_noche(ctx, t, velocidad=120)
    for capa_n, (yb, vel, col) in enumerate([(1500, 90, (0.32, 0.36, 0.55)), (1650, 160, (0.42, 0.46, 0.66))]):
        for i in range(9):
            cx = (i * 190 - t * vel) % (W + 400) - 200
            ctx.arc(cx, yb + (i % 3) * 30, 140, 0, 2 * math.pi); ctx.set_source_rgb(*col); ctx.fill()
        ctx.rectangle(0, yb + 60, W, H); ctx.set_source_rgb(*col); ctx.fill()

def pista(ctx, t):
    cielo_noche(ctx, t, nubes=False)
    ctx.rectangle(0, 1300, W, 700); ctx.set_source_rgb(0.2, 0.21, 0.24); ctx.fill()
    ctx.set_source_rgb(0.95, 0.8, 0.2)
    for i in range(6): ctx.rectangle(i * 220 - 40, 1560, 120, 16); ctx.fill()
    for i in range(12):
        on = int(t * 2 + i) % 2
        ctx.arc(i * 100 + 30, 1330, 9, 0, 2 * math.pi); ctx.set_source_rgb(*((0.3, 0.6, 1) if on else (0.15, 0.25, 0.45))); ctx.fill()

def rojo(ctx, t):
    pulso = 0.5 + 0.5 * math.sin(t * 6)
    g = cairo.RadialGradient(540, 960, 100, 540, 960, 1200)
    g.add_color_stop_rgb(0, 0.55 + 0.15 * pulso, 0.06, 0.08); g.add_color_stop_rgb(1, 0.12, 0.01, 0.02)
    ctx.set_source(g); ctx.paint()

def signo(txt="?", tam=260, color=(1, 0.85, 0.1)): return texto(txt, tam, color, TINTA)

# ---------------------------------------------------------------- escenas
P = dict(y=SUELO_CAB)
escenas = [
    # 1. POV: eres el piloto
    Tramo(0.0, 4.0, Dibujo(pista), Elemento(avion(), 0.0, 4.0, 540, 1080, 1.05, entrada=0.01),
          piloto([dict(t=0, pose="parado", x=540, y=1880, cara="feliz"),
                  dict(t=1.4, pose="jarras", x=540, y=1880, cara="picaro")], escala=1.45)),
    # 2. Son las 2 de la madrugada
    Tramo(4.0, 9.8, cabina(), Elemento(reloj_digital("2:00", "AM"), 4.5, 7.6, 540, 700, 1.0),
          Elemento(texto("EL AVIÓN MÁS IMPORTANTE", 58, (1, 0.85, 0.1), TINTA), 7.8, 9.8, 540, 760),
          piloto([dict(t=4.0, pose="parado", x=330, cara="serio", **P), dict(t=7.3, pose="jarras", x=330, cara="picaro", **P)]),
          copiloto([dict(t=4.0, pose="parado", x=780, cara="feliz", mira=-1, **P)]), Dibujo(tablero)),
    # 3. A bordo viaja el presidente con sus asesores
    Tramo(9.8, 13.7, Dibujo(salon),
          Personaje([dict(t=9.8, pose="parado", x=190, y=1760, cara="serio", mira=1)], escala=1.15, vestuario="ejecutivo",
                    color=(0.45, 0.47, 0.5), color2=(0.3, 0.3, 0.35), pelo=NEGRO, semilla=11),
          Personaje([dict(t=9.8, pose="parado", x=890, y=1760, cara="serio", mira=-1)], escala=1.15, vestuario="ejecutivo",
                    color=(0.42, 0.33, 0.25), color2=(0.6, 0.15, 0.15), peinado="chongo", semilla=12),
          presidente([dict(t=9.8, pose="parado", x=540, y=1800, cara="feliz"),
                      dict(t=10.6, pose="saludo", x=540, y=1800, cara="feliz")])),
    # 4. Todo normal… hasta la llamada
    Tramo(13.7, 18.2, cabina(),
          piloto([dict(t=13.7, pose="jarras", x=330, cara="feliz", **P),
                  dict(t=15.4, pose="sorpresa", x=330, cara="sorpresa", mira=1, **P)]),
          copiloto([dict(t=13.7, pose="parado", x=780, cara="feliz", **P)]), Dibujo(tablero),
          Elemento(telefono("LÍNEA\nPRIVADA"), 15.3, 18.2, 560, 760, 0.95)),
    # 5. «¡Cambie la ruta! No informe a nadie»
    Tramo(18.2, 23.2, cabina(alerta_desde=19.6),
          piloto([dict(t=18.2, pose="parado", x=330, y=2420, cara="sorpresa", mira=1),
                  dict(t=21.6, pose="parado", x=330, y=2420, cara="serio", mira=1)], escala=2.2),
          Elemento(telefono("LÍNEA\nPRIVADA", sonando=False), 18.2, 23.2, 860, 1350, 0.7, entrada=0.01),
          Elemento(burbuja_dialogo("¡Cambie la ruta inmediatamente!", 62, 560, cola=(1, 1)), 19.5, 21.55, 560, 640),
          Elemento(burbuja_dialogo("No informe a nadie.", 62, 560, cola=(1, 1)), 21.6, 23.2, 560, 640)),
    # 6. ¿Quién habla? La llamada termina
    Tramo(23.2, 27.8, cabina(),
          piloto([dict(t=23.2, pose="encoger", x=330, cara="pensar", mira=1, **P),
                  dict(t=25.6, pose="triste", x=330, cara="serio", **P)]),
          copiloto([dict(t=23.2, pose="parado", x=780, cara="serio", mira=-1, **P)]), Dibujo(tablero),
          Elemento(signo("?", 200), 23.7, 25.5, 330, 760),
          Elemento(telefono("LLAMADA\nTERMINADA", sonando=False, color_pantalla=(0.75, 0.12, 0.14)), 25.55, 27.8, 560, 760, 0.95)),
    # 7. Notificación: aeropuerto cerrado
    Tramo(27.8, 35.8, cabina(alerta_desde=33.36),
          piloto([dict(t=27.8, pose="parado", x=330, cara="serio", mira=1, **P),
                  dict(t=33.4, pose="sorpresa", x=330, cara="sorpresa", mira=1, **P)]),
          copiloto([dict(t=27.8, pose="parado", x=780, cara="serio", **P),
                    dict(t=30.4, pose="señalar_i", x=780, cara="sorpresa", mira=-1, **P),
                    dict(t=33.4, pose="sorpresa", x=780, cara="sorpresa", **P)]), Dibujo(tablero),
          Elemento(alerta("NOTIFICACIÓN", "Mensaje de la torre"), 30.4, 31.6, 560, 760, 1.0),
          Elemento(alerta("ALERTA", "Aeropuerto CERRADO"), 31.6, 35.8, 560, 760, 1.05, entrada=0.2)),
    # 8. Dos agentes armados entran
    Tramo(35.8, 40.4, Dibujo(pasillo),
          agente([dict(t=35.8, pose="parado", x=-200, y=1900, cara="serio", caminar=True, lleva=pistola(), mira=1),
                  dict(t=38.6, pose="parado", x=230, y=1900, cara="serio", mira=1)], escala=1.35),
          agente([dict(t=36.6, pose="parado", x=-250, y=1900, cara="enojado", caminar=True, lleva=pistola(), mira=1),
                  dict(t=39.4, pose="parado", x=470, y=1900, cara="enojado", mira=1)], escala=1.35, semilla=10),
          piloto([dict(t=35.8, pose="parado", x=850, y=1900, cara="serio", mira=-1),
                  dict(t=36.3, pose="sorpresa", x=850, y=1900, cara="sorpresa", mira=-1)])),
    # 9. Te entrega un sobre: «Si quiere que todos lleguen vivos…»
    Tramo(40.4, 47.2, Dibujo(pasillo),
          agente([dict(t=40.4, pose="parado", x=300, y=1900, cara="serio", mira=1, lleva=sobre()),
                  dict(t=41.1, pose="señalar_d", x=300, y=1900, cara="serio", mira=1)], escala=1.45, habla=env_agente),
          piloto([dict(t=40.4, pose="sorpresa", x=850, y=1900, cara="sorpresa", mira=-1),
                  dict(t=44.2, pose="triste", x=850, y=1900, cara="triste", mira=-1)]),
          Elemento(burbuja_dialogo("Si quiere que todos lleguen vivos, siga estas instrucciones.", 54, 600, cola=(-1, 1)),
                   42.9, 47.2, 560, 720)),
    # 10. Tus manos tiemblan
    Tramo(47.2, 49.8, cabina(),
          piloto([dict(t=47.2, pose="señalar_d", x=420, y=2420, cara="triste", lleva=sobre(), temblar=True)], escala=2.2),
          Elemento(texto("TIC TAC", 70, (1, 0.85, 0.1), TINTA), 47.9, 49.8, 820, 820)),
    # 11. Miles de metros de altura
    Tramo(49.8, 52.1, Dibujo(exterior),
          Elemento(avion(), 49.8, 52.1, 0, 0, 0.95, mover=lambda t: (540 + math.sin(t) * 20, 980 + math.sin(t * 1.6) * 14),
                   entrada=0.01),
          Elemento(texto("10 000 m", 110, (1, 0.85, 0.1), TINTA), 50.1, 52.1, 540, 1380),
          Elemento(texto("↓", 140, (1, 1, 1), TINTA), 50.4, 52.1, 540, 1530)),
    # 12. Un presidente detrás de ti
    Tramo(52.1, 54.3, Dibujo(pasillo),
          presidente([dict(t=52.1, pose="parado", x=330, y=1880, cara="serio", mira=1)], escala=1.25),
          piloto([dict(t=52.1, pose="parado", x=840, y=1900, cara="triste", mira=-1)])),
    # 13. Una orden que pone en peligro al país
    Tramo(54.3, 57.5, Dibujo(rojo), Elemento(documento("ORDEN", "CONFIDENCIAL"), 54.4, 57.5, 540, 1050, 1.25),
          Elemento(texto("PELIGRO", 120, (1, 0.25, 0.2), (1, 1, 1)), 55.6, 57.5, 540, 1560)),
    # 14. Una última frase por los auriculares
    Tramo(57.5, 60.9, cabina(),
          piloto([dict(t=57.5, pose="parado", x=330, cara="serio", mira=1, **P),
                  dict(t=59.7, pose="pensar", x=330, cara="pensar", mira=1, **P)], accesorios=("charreteras", "alas", "auriculares")),
          copiloto([dict(t=57.5, pose="parado", x=780, cara="serio", mira=-1, **P)]), Dibujo(tablero)),
    # 15. «Piloto, no confíe en nadie…»
    Tramo(60.9, 65.5, Dibujo(rojo),
          piloto([dict(t=60.9, pose="parado", x=540, y=2420, cara="sorpresa"),
                  dict(t=62.0, pose="parado", x=540, y=2420, cara="sorpresa", mira=-1),
                  dict(t=62.8, pose="parado", x=540, y=2420, cara="sorpresa", mira=1),
                  dict(t=63.6, pose="parado", x=540, y=2420, cara="serio", mira=-1)], escala=2.2,
                 accesorios=("charreteras", "alas", "auriculares")),
          Elemento(burbuja_dialogo("Piloto, no confíe en nadie que esté dentro de ese avión.", 54, 620, cola=(0, 1),
                                   color=(0.08, 0.08, 0.1), color_txt=(1, 1, 1)), 60.9, 65.5, 540, 640)),
    # 16. ¿A quién obedecerías?
    Tramo(65.5, DUR + 1, Dibujo(pasillo),
          presidente([dict(t=65.5, pose="parado", x=190, y=1880, cara="serio", mira=1)], escala=1.1),
          agente([dict(t=65.5, pose="parado", x=900, y=1880, cara="serio", mira=-1, lleva=pistola())], escala=1.1),
          piloto([dict(t=65.5, pose="pensar", x=540, y=1900, cara="pensar")], escala=1.3),
          Elemento(telefono("LÍNEA\nPRIVADA", sonando=True), 67.9, DUR + 1, 540, 640, 0.6),
          Elemento(signo("?", 120), 66.7, DUR + 1, 190, 980), Elemento(signo("?", 120), 66.9, DUR + 1, 900, 980),
          Elemento(signo("?", 120), 67.1, DUR + 1, 760, 560)),
]

short = Short(DUR).agregar(*escenas, subs)
for (t0, t1, e, cx, cy) in [(0.3, 3.9, 1.08, 540, 1300), (4.3, 9.7, 1.05, 540, 1000), (10.0, 13.6, 1.06, 540, 1300),
                            (13.9, 18.1, 1.06, 400, 1200), (23.4, 27.7, 1.05, 400, 1200), (28.0, 35.7, 1.05, 560, 1100),
                            (40.6, 47.1, 1.06, 560, 1300), (52.2, 54.2, 1.08, 600, 1300), (57.6, 60.8, 1.1, 330, 1250),
                            (65.6, DUR, 1.06, 540, 1200)]:
    short.zoom(t0, t1, e, cx, cy)
for (t, f) in [(15.4, 10), (19.62, 18), (33.36, 14), (37.76, 16), (44.16, 10), (55.68, 20), (61.94, 18)]:
    short.sacudir(t, f)

# ---------------------------------------------------------------- sonido: voz al frente, música y efectos debajo
mez = snd.Mezcla(DUR)
mez.poner(0, snd.tension(DUR), 0.16)
mez.poner(0, snd.cargar(VOZ), 1.0)
for t in (4.0, 9.8, 13.7, 18.2, 27.8, 35.8, 40.4, 47.2, 49.8, 52.1, 54.3, 57.5, 60.9, 65.5):
    mez.poner(t - 0.2, snd.whoosh(), 0.18)
mez.poner(15.3, snd.timbre(2), 0.22)
mez.poner(33.36, snd.alarma(2.2), 0.18)
for t in (19.62, 37.76, 55.68, 61.94): mez.poner(t, snd.impacto(), 0.35)
for t in (47.4, 48.1, 48.8, 49.5): mez.poner(t, snd.latido(), 0.4)
for t in (4.5, 15.3, 30.4, 31.6, 41.1, 54.4, 66.7, 66.9, 67.1): mez.poner(t, snd.pop(), 0.2)
mez.poner(68.22, snd.ding(660, 1.2), 0.2)

if __name__ == "__main__":
    if "--fotos" in sys.argv:
        for i, t in enumerate([2.5, 6.0, 11.5, 16.5, 20.5, 26.5, 34.0, 38.5, 44.5, 48.5, 51.0, 53.0, 56.0, 59.5, 62.5, 68.5]):
            short.foto(t, f"salida/avion/{i + 1:02d}_{t:04.1f}.png")
        print("fotos listas en salida/avion/")
    else:
        mez.guardar("salida/avion_presidencial_crudo.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "salida/avion_presidencial_crudo.wav",
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "salida/avion_presidencial.wav"], check=True)
        short.render("salida/avion_presidencial.mp4", audio="salida/avion_presidencial.wav")
