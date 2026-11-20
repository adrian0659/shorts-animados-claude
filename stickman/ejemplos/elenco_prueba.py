"""Hoja de prueba: peinados, ropa, caras y poses del estilo ilustrado."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from motor import *
from ilustrado import *

S = 1700
gente = [
    Persona([dict(t=0, pose="saludo", x=200, y=S - 700, cara="feliz", mira=1)], escala=1.05, pelo="largo",
            color_pelo=(0.2, 0.12, 0.08), ropa=dict(tipo="vestido", color=(0.85, 0.35, 0.4), manga="corta")),
    Persona([dict(t=0, pose="sorpresa", x=540, y=S - 700, cara="sorpresa")], escala=1.05, pelo="coleta",
            color_pelo=(0.85, 0.65, 0.3), ropa=dict(tipo="playera", color=(0.25, 0.55, 0.45), manga="corta", pantalon=(0.2, 0.25, 0.4))),
    Persona([dict(t=0, pose="triste", x=880, y=S - 700, cara="triste", mira=-1)], escala=1.05, pelo="calvo",
            ropa=dict(tipo="camisa", color=(0.9, 0.8, 0.45), manga="larga")),
    Persona([dict(t=0, pose="pensar", x=200, y=S, cara="pensar", mira=1)], escala=1.05, pelo="corto",
            color_pelo=(0.1, 0.1, 0.1), ropa=dict(tipo="camisa", color=(0.3, 0.3, 0.35), corbata=(0.2, 0.4, 0.8))),
    Persona([dict(t=0, pose="festejar", x=540, y=S, cara="feliz", saltar=True)], escala=1.05, pelo="puntas",
            color_pelo=(0.55, 0.3, 0.1), semilla=9, ropa=dict(tipo="playera", color=(0.95, 0.6, 0.15), manga="corta")),
    Persona([dict(t=0, pose="brazos_cruzados", x=880, y=S, cara="enojado", mira=-1, mano_d="llave")], escala=1.05,
            pelo="raya", color_pelo=(0.3, 0.3, 0.32), ropa=dict(tipo="camisa", color=(0.16, 0.2, 0.33), cuello=(0.78, 0.13, 0.13), manga="corta")),
]
short = Short(4).agregar(Taller(), *gente)
short.foto(0.6, "salida/elenco_prueba.png")
# caminata corta para probar movimiento
cam = Persona([dict(t=0, pose="parado", x=100, y=1640, caminar=True, mira=1, cara="feliz"),
               dict(t=2.5, pose="saludo", x=700, y=1640, mira=0, cara="feliz")], pelo="puntas", color_pelo=(0.08,0.08,0.1),
              ropa=dict(tipo="camisa", color=(0.16, 0.2, 0.33), cuello=(0.78, 0.13, 0.13), manga="corta", gafete="MECÁNICO"))
Short(3.5).agregar(Taller(), cam).render("salida/caminata_prueba.mp4")
