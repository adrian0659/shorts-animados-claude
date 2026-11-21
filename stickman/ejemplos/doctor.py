"""Demostración del personaje estilo «boceto»: el doctor.

Ejecutar desde la carpeta stickman/:
    python3 ejemplos/doctor.py --hoja    # hoja de giro con 5 vistas -> salida/doctor_hoja.png
    python3 ejemplos/doctor.py --foto 5  # una foto del video en el segundo 5
    python3 ejemplos/doctor.py           # video de 9 s -> salida/doctor.mp4
"""
import os, sys, math, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import cairo
from personaje import Personaje, Lienzo, fondo_grunge, tinta, DOCTOR

W, H, FPS, DUR = 1080, 1920, 30, 9.0
os.makedirs("salida", exist_ok=True)
doc = Personaje(DOCTOR, semilla=2)


def rotulo(ctx, txt, x, y, tam=34):
    ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL); ctx.set_font_size(tam)
    for i, linea in enumerate(txt.split("\n")):
        e = ctx.text_extents(linea)
        ctx.move_to(x - e.width / 2 - e.x_bearing, y + i * tam * 1.15)
        ctx.text_path(linea)
    ctx.set_source_rgb(0.08, 0.07, 0.06); ctx.fill()


def hoja():
    lz = Lienzo(W, H, fondo_grunge(W, H))
    ctx = lz.nuevo()
    suelo, esc = 1290, 1.3
    for y in (suelo - 470 * esc, suelo - 350 * esc, suelo - 110 * esc - 70, suelo):  # líneas guía
        tinta(ctx, [(20, y), (W - 20, y)], 0, int(y), 1, 1.4, alfa=0.45)
    vistas = [(0, "VISTA\nFRONTAL"), (-40, "TRES\nCUARTOS"), (-90, "PERFIL"),
              (-140, "TRES CUARTOS\nTRASERA"), (180, "VISTA\nTRASERA")]
    for i, (g, nombre) in enumerate(vistas):
        x = 120 + i * 210
        doc.dibujar(ctx, 0.0, x, suelo, esc, giro=g, cara="preocupado", parpadeo=False)
        rotulo(ctx, nombre, x, suelo + 60, 30)
    from PIL import Image
    Image.fromarray(lz.rgb(0)).save("salida/doctor_hoja.png"); print("salida/doctor_hoja.png")


def suave(k):
    k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)


lz_video = None
def cuadro(t):
    global lz_video
    if lz_video is None: lz_video = Lienzo(W, H, fondo_grunge(W, H, semilla=8, borde_oscuro=0.18))
    ctx = lz_video.nuevo()
    suelo, esc = 1660, 2.15
    x, giro, cara, mira, paso = W / 2, 0.0, "preocupado", 0.0, None
    brazos = None
    if t < 3.6:                         # da una vuelta completa
        giro = 360 * suave(t / 3.6)
    elif t < 5.6:                       # mira a los lados, preocupado
        mira = math.sin((t - 3.6) * 3.2)
        cara = "sorpresa" if 4.7 < t < 5.3 else "preocupado"
        if 4.7 < t < 5.6: brazos = {"i": (35, 10, 70), "d": (35, 10, 70)}
    else:                               # gira de perfil y sale caminando
        k = suave((t - 5.6) / 0.5)
        giro = 90 * k
        if t > 6.0:
            dist = (t - 6.0) * 260
            x = W / 2 + dist
            paso = dist / 40.0
    doc.dibujar(ctx, t, x, suelo, esc, giro=giro, cara=cara, mira=mira, paso=paso, brazos=brazos)
    return lz_video.rgb(t)


if __name__ == "__main__":
    from PIL import Image
    if "--hoja" in sys.argv:
        hoja()
    elif "--foto" in sys.argv:
        tt = float(sys.argv[sys.argv.index("--foto") + 1])
        Image.fromarray(cuadro(tt)).save(f"salida/doctor_{tt:04.1f}.png"); print("foto", tt)
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", "salida/doctor.mp4"]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(int(DUR * FPS)): p.stdin.write(cuadro(i / FPS).tobytes())
        p.stdin.close(); p.wait(); print("salida/doctor.mp4")
