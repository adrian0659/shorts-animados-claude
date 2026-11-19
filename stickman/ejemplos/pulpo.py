"""Short de ejemplo: «Los pulpos tienen TRES corazones» (≈26 s, 1080x1920).

Ejecutar desde la carpeta stickman/:
    python3 ejemplos/pulpo.py            # video completo -> salida/pulpo.mp4
    python3 ejemplos/pulpo.py --fotos    # solo fotos de revisión -> salida/foto_*.png
"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from motor import *
import sonido as snd

DUR = 26.0
SUELO = 1500
os.makedirs("salida", exist_ok=True)

# ---------------- guion (texto en pantalla). *palabra* = resaltada
guion = [
    (0.3, 3.6,  "¿Sabías que los pulpos tienen *TRES* corazones?"),
    (3.6, 7.8,  "*Dos* bombean sangre a las branquias…"),
    (7.8, 11.6, "…y el *tercero* al resto del cuerpo."),
    (11.6, 16.4, "Y su sangre es *AZUL*, porque usa *cobre* en vez de hierro."),
    (16.4, 21.4, "Lo más loco: cuando nada, su corazón principal *se detiene*."),
    (21.4, 24.2, "Por eso prefiere *arrastrarse*."),
    (24.2, 26.0, "¡Sígueme para más *datos curiosos*!"),
]

fondo = Fondo([(0, (1.0, 0.86, 0.55)), (3.6, (0.55, 0.82, 0.95)), (11.6, (0.72, 0.8, 1.0)),
               (16.4, (0.35, 0.6, 0.85)), (21.4, (0.98, 0.78, 0.6))], suelo=SUELO)

# ---------------- monigote protagonista
yo = Monigote([
    dict(t=0.0,  pose="parado", x=-150, y=SUELO, caminar=True, cara="feliz"),
    dict(t=1.4,  pose="sorpresa", x=540, y=SUELO, cara="sorpresa"),
    dict(t=3.6,  pose="señalar_d", x=300, y=SUELO, caminar=True, cara="feliz", mira=1),
    dict(t=4.4,  pose="señalar_d", x=260, y=SUELO, cara="feliz", mira=1),
    dict(t=11.6, pose="pensar", x=260, y=SUELO, cara="pensar", mira=1),
    dict(t=16.4, pose="sorpresa", x=260, y=SUELO, cara="sorpresa"),
    dict(t=21.4, pose="encoger", x=260, y=SUELO, cara="feliz", mira=1),
    dict(t=23.7, pose="parado", x=260, y=SUELO, caminar=True, cara="feliz"),
    dict(t=24.4, pose="saludo", x=540, y=SUELO, cara="feliz"),
], escala=1.55)

# ---------------- pulpo en distintas escenas
def pos_nado(t):  # sube nadando y sale de cuadro
    k = suave((t - 16.6) / 4.6)
    return 780 + math.sin(t * 3) * 25, lerp(1050, 760, k)

def pos_arrastre(t):
    return lerp(1300, 760, suave((t - 21.4) / 2.2)), 1270 + math.sin(t * 6) * 6

el = [
    # gancho: tres corazones que saltan
    Elemento(corazon(), 1.5, 3.6, 300, 780, 0.9),
    Elemento(corazon(), 1.8, 3.6, 540, 700, 1.1),
    Elemento(corazon(), 2.1, 3.6, 780, 780, 0.9),
    Elemento(texto("x3", 150, (1, 0.85, 0.1), TINTA), 2.4, 3.6, 800, 1050),
    # explicación
    Elemento(pulpo(corazones=2), 3.6, 7.8, 760, 1080, 1.25),
    Elemento(texto("branquias", 56, TINTA), 4.6, 7.8, 760, 760),
    Elemento(pulpo(corazones=3), 7.8, 11.6, 760, 1080, 1.25, entrada=0.01),
    Elemento(texto("cuerpo", 56, TINTA), 8.3, 11.6, 760, 760),
    # sangre azul
    Elemento(pulpo(corazones=3, sangre_azul=True), 11.6, 16.4, 760, 1080, 1.25, entrada=0.01),
    Elemento(burbuja_pensamiento(lambda c, t, k: (c.save(), c.scale(0.7, 0.7), gota()(c, t, k), c.restore())),
             12.0, 16.4, 430, 700, 1.0),
    Elemento(texto("Cu", 80, (1, 1, 1), (0.75, 0.45, 0.2)), 13.6, 16.4, 980, 780),
    # nada -> corazón se detiene
    Elemento(burbujas_agua(), 16.4, 21.4, 0, 0, 1.0, entrada=0.01),
    Elemento(pulpo(nadar=True, corazones=3, sangre_azul=True), 16.4, 21.4, 0, 0, 1.0, mover=pos_nado, entrada=0.01),
    Elemento(texto("0 latidos", 70, (1, 0.3, 0.3), TINTA), 18.6, 21.4, 780, 1250),
    # arrastrarse
    Elemento(pulpo(), 21.4, 24.2, 0, 0, 0.9, mover=pos_arrastre, entrada=0.01),
    # cierre
    Elemento(texto("¡SÍGUEME!", 120, (1, 0.85, 0.1), TINTA), 24.4, 26.0, 540, 1700),
]

short = Short(DUR).agregar(fondo, *el, yo, Subtitulos(guion, y=300))
short.sacudir(1.4, 22); short.sacudir(16.6, 16)
short.zoom(7.9, 11.4, 1.12, 760, 1000)
short.zoom(18.4, 21.2, 1.1, 780, 900)

# ---------------- sonido
mez = snd.Mezcla(DUR)
mez.poner(0, snd.musica(DUR), 0.55)
mez.poner(1.4, snd.boing(), 1.0)
for tt in (1.5, 1.8, 2.1): mez.poner(tt, snd.pop(), 0.9)
mez.poner(2.4, snd.ding(), 0.8)
for tt in (3.6, 11.6, 16.4, 21.4, 24.2): mez.poner(tt - 0.15, snd.whoosh(), 0.5)
for tt in (4.6, 8.3, 12.0, 13.6): mez.poner(tt, snd.pop(), 0.7)
for tt in (8.0, 9.0, 10.0, 11.0): mez.poner(tt, snd.latido(), 0.9)
mez.poner(16.8, snd.latido(), 0.9); mez.poner(17.8, snd.latido(), 0.5)
mez.poner(18.6, snd.ding(440, 1.2), 0.6)
mez.poner(24.4, snd.tada(), 0.8)
# un "tic" suave por palabra de subtítulo
for tt in Subtitulos(guion).palabras_tiempos(): mez.poner(tt, snd.pop(0.05), 0.12)

if __name__ == "__main__":
    if "--fotos" in sys.argv:
        for tt in (0.8, 2.8, 5.5, 9.5, 14.5, 19.5, 22.8, 25.2):
            short.foto(tt, f"salida/foto_{tt:04.1f}.png"); print("foto", tt)
    else:
        mez.guardar("salida/pulpo.wav")
        short.render("salida/pulpo.mp4", audio="salida/pulpo.wav")
