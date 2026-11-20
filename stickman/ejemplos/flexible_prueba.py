"""Prueba de flexibilidad: camina, frena, se sorprende, se desanima, habla y festeja (8 s)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from motor import *
from ilustrado import *

S = 1640
uniforme = dict(tipo="camisa", color=(0.16, 0.2, 0.33), cuello=(0.78, 0.13, 0.13), manga="corta",
                gafete="MECÁNICO", bolsillo=True)
mec = Persona([
    dict(t=0.0, pose="parado", x=-80, y=S, caminar=True, mira=1, cara="feliz"),
    dict(t=1.6, pose="parado", x=330, y=S, mira=1, cara="serio"),
    dict(t=2.0, pose="sorpresa", x=330, y=S, mira=1, cara="sorpresa"),
    dict(t=3.2, pose="triste", x=330, y=S, mira=1, cara="triste"),
    dict(t=4.6, pose="explicar", x=330, y=S, mira=1, cara="serio", habla=True),
    dict(t=6.4, pose="festejar", x=330, y=S, mira=0, cara="feliz", saltar=True),
], pelo="puntas", color_pelo=(0.08, 0.08, 0.1), semilla=2, ropa=uniforme)
cli = Persona([
    dict(t=0.0, pose="telefono", x=770, y=S + 30, mira=-1, cara="enojado", mano_d="telefono", habla=True),
    dict(t=2.0, pose="brazos_cruzados", x=770, y=S + 30, mira=-1, cara="enojado", mano_d=None),
    dict(t=4.6, pose="pensar", x=770, y=S + 30, mira=-1, cara="pensar"),
    dict(t=6.4, pose="saludo", x=770, y=S + 30, mira=-1, cara="feliz"),
], pelo="raya", semilla=5, ropa=dict(tipo="camisa", color=(0.84, 0.85, 0.87), manga="larga", corbata=(0.5, 0.1, 0.17)))

short = Short(8).agregar(Taller(), Auto(980, 1560, 0.85, capo_abierto=True), mec, cli)
if __name__ == "__main__":
    os.makedirs("salida", exist_ok=True)
    short.render("salida/flexible_prueba.mp4")
