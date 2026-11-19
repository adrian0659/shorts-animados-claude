"""Muestra del personaje «cabezón con sudadera» (clase Personaje de motor.py).

Ejecutar desde la carpeta stickman/:
    python3 ejemplos/sudadera.py            # hoja de poses y caras -> salida/sudadera_hoja.png
    python3 ejemplos/sudadera.py --video    # clip de 6 s -> salida/sudadera.mp4
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from motor import *
from PIL import Image

os.makedirs("salida", exist_ok=True)
SUELO = 1700

if "--video" in sys.argv:
    fondo = Fondo([(0, (0.98, 0.97, 0.94)), (3.0, (0.86, 0.93, 1.0))], suelo=SUELO)
    yo = Personaje([
        dict(t=0.0, pose="parado", x=-200, y=SUELO, caminar=True, cara="feliz"),
        dict(t=1.6, pose="saludo", x=540, y=SUELO, cara="feliz"),
        dict(t=3.0, pose="sorpresa", x=540, y=SUELO, cara="sorpresa"),
        dict(t=4.2, pose="jarras", x=540, y=SUELO, cara="picaro"),
    ], escala=2.2)
    short = Short(6).agregar(fondo, yo)
    short.sacudir(3.0, 12)
    short.render("salida/sudadera.mp4")
else:
    poses = [("jarras", "picaro"), ("saludo", "feliz"), ("sorpresa", "sorpresa"),
             ("pensar", "pensar"), ("triste", "triste"), ("señalar_d", "enojado")]
    fotos = []
    for pose, cara in poses:
        p = Personaje([dict(t=0, pose=pose, x=540, y=SUELO, cara=cara)], escala=2.2)
        s = Short(1).agregar(Fondo([(0, (1, 1, 1))], suelo=None), p,
                             Elemento(texto(f"{pose} · {cara}", 70), 0, 9, 540, 200, entrada=0.01))
        fotos.append(Image.fromarray(s.cuadro(1.0)).resize((540, 960)))
    hoja = Image.new("RGB", (540 * 3, 960 * 2), "white")
    for i, f in enumerate(fotos): hoja.paste(f, ((i % 3) * 540, (i // 3) * 960))
    hoja.save("salida/sudadera_hoja.png"); print("listo: salida/sudadera_hoja.png")
