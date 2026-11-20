import sys; import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from escenarios import *
from PIL import Image
POSES["entregar"] = dict(torso=182, cab=4, bi=-14, ai=10, bd=55, ad=78, mi=-8, pi=-3, md=10, pd=4)
mec = Actor("mecanico", [dict(t=0, pose="entregar", x=330, y=1720, cara="serio", mira=0.5, objeto="tablet")], escala=1.5, semilla=2)
cli = Actor("cliente", [dict(t=0, pose="audifono", x=790, y=1690, cara="enojado", mira=-0.5, fac=-1, objeto="telefono")], escala=1.45, semilla=6)
def fondo(c):
    taller(c); camioneta(c, 1010, 1640, 1.3, -1, color=(0.45, 0.47, 0.52))
e = Escena(0, 3, fondo, [cli, mec])
s = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); c = cairo.Context(s); e.cuadro(1.2, c); viñeta(c); s.write_to_png("salida/personajes_test.png")
Image.open("salida/personajes_test.png").crop((0, 700, 1080, 1920)).resize((720, 813)).save("salida/personajes_test_s.png")
