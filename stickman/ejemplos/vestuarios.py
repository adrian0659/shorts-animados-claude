"""Hoja con todos los vestuarios listos del personaje (VESTUARIOS en motor.py).

Ejecutar desde la carpeta stickman/:
    python3 ejemplos/vestuarios.py      # -> salida/vestuarios.png
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from motor import *
from PIL import Image

os.makedirs("salida", exist_ok=True)
caras = ["feliz", "picaro", "serio", "sorpresa", "pensar", "enojado"]
poses = ["parado", "jarras", "saludo", "señalar_d", "parado", "jarras"]
nombres = list(VESTUARIOS)
col, celda_w, celda_h = 6, 360, 640
filas = (len(nombres) + col - 1) // col
hoja = Image.new("RGB", (col * celda_w, filas * celda_h), "white")
for i, nombre in enumerate(nombres):
    p = Personaje([dict(t=0, pose=poses[i % 6], x=540, y=1640, cara=caras[i % 6])], escala=2.0, vestuario=nombre)
    s = Short(1).agregar(Fondo([(0, (1, 1, 1))], suelo=None), p,
                         Elemento(texto(nombre, 90), 0, 9, 540, 170, entrada=0.01))
    hoja.paste(Image.fromarray(s.cuadro(1.0)).resize((celda_w, celda_h)), ((i % col) * celda_w, (i // col) * celda_h))
hoja.save("salida/vestuarios.png"); print("listo: salida/vestuarios.png")
