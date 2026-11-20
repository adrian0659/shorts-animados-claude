"""Foto de prueba del estilo ilustrado: mecánico y cliente en el taller."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from motor import *
from ilustrado import *

SUELO = 1640
mecanico = Persona([dict(t=0, pose="entregar", x=330, y=SUELO, mira=1, cara="serio", mano_d="tablet")],
                   pelo="puntas", color_pelo=(0.08, 0.08, 0.1), semilla=2,
                   ropa=dict(tipo="camisa", color=(0.16, 0.2, 0.33), cuello=(0.78, 0.13, 0.13),
                             manga="corta", gafete="MECÁNICO", bolsillo=True))
cliente = Persona([dict(t=0, pose="telefono", x=760, y=SUELO + 30, mira=-1, cara="enojado", mano_d="telefono")],
                  pelo="raya", color_pelo=(0.45, 0.27, 0.15), semilla=5,
                  ropa=dict(tipo="camisa", color=(0.84, 0.85, 0.87), manga="larga", corbata=(0.5, 0.1, 0.17)))
short = Short(4).agregar(Taller(), Auto(980, 1560, 0.85, capo_abierto=True), mecanico, cliente)
os.makedirs("salida", exist_ok=True)
short.foto(1.0, "salida/taller_prueba.png")
