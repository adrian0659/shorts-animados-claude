"""Arma el video a partir de imágenes fijas + voz + música, con zoom/paneo suave en cada plano.

Uso:
    python3 ensamblar.py plan.json salida.mp4            # video final
    python3 ensamblar.py plan.json salida.mp4 --borrador  # mitad de resolución, rápido para revisar

Si una imagen del plan todavía no existe, se dibuja una tarjeta con el texto del plano
(sirve como «animatic» para revisar ritmos antes de generar imágenes).

Requiere: pip install pillow numpy  ·  ffmpeg en el PATH.

plan.json:
{
  "ancho": 1920, "alto": 1080, "fps": 30,
  "voz": "voz.mp3",                 (opcional)
  "musica": "musica.mp3",           (opcional, se repite en bucle)
  "volumen_musica": 0.12,
  "planos": [
    {"imagen": "img/01.png", "inicio": 0.0, "fin": 4.2, "movimiento": "zoom_in",
     "texto": "Eres un mecánico en 2010…"},
    ...
  ]
}
movimiento: zoom_in | zoom_out | paneo_der | paneo_izq | subir | bajar | sacudida | fijo
Los tiempos van en segundos; si «inicio» falta, el plano empieza donde terminó el anterior.
Las rutas son relativas a la carpeta del plan.
"""
import json, math, os, subprocess, sys, textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BEIGE = (236, 226, 204)


def suave(k):
    k = max(0.0, min(1.0, k)); return k * k * (3 - 2 * k)


def fuente(tam):
    for f in ("/usr/share/fonts/opentype/inter/Inter-Bold.otf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "C:/Windows/Fonts/arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try: return ImageFont.truetype(f, tam)
        except OSError: pass
    return ImageFont.load_default()


def tarjeta(texto, W, H, n):
    im = Image.new("RGB", (W, H), BEIGE); d = ImageDraw.Draw(im)
    f, f2 = fuente(H // 16), fuente(H // 26)
    d.text((W * 0.16, H * 0.18), f"PLANO {n}  (falta imagen)", fill=(170, 60, 50), font=f2)
    y = H * 0.32
    for linea in textwrap.wrap(texto or "", 30):
        d.text((W * 0.16, y), linea, fill=(30, 30, 30), font=f); y += H / 12
    d.line((W * 0.14, H * 0.8, W * 0.86, H * 0.8), fill=(40, 40, 40), width=max(2, H // 300))
    return im


def cubrir(im, W, H, margen=1.18):
    """Escala la imagen para cubrir W×H con margen extra para mover la cámara."""
    im = im.convert("RGB")
    k = max(W / im.width, H / im.height) * margen
    return im.resize((math.ceil(im.width * k), math.ceil(im.height * k)), Image.LANCZOS)


def camara(mov, k, t_local, dur):
    """Devuelve (zoom, dx, dy) en fracciones; zoom 1 = encuadre base."""
    z, dx, dy = 1.0, 0.0, 0.0
    if mov == "zoom_in": z = 1 + 0.12 * k
    elif mov == "zoom_out": z = 1.12 - 0.12 * k
    elif mov == "paneo_der": z, dx = 1.06, -0.05 + 0.1 * k
    elif mov == "paneo_izq": z, dx = 1.06, 0.05 - 0.1 * k
    elif mov == "subir": z, dy = 1.06, 0.05 - 0.1 * k
    elif mov == "bajar": z, dy = 1.06, -0.05 + 0.1 * k
    elif mov == "sacudida":
        z = 1.05 + 0.03 * k; a = max(0, 1 - t_local / 0.5) * 0.012
        dx, dy = math.sin(t_local * 60) * a, math.cos(t_local * 47) * a
    # «golpe» al entrar en cada plano: arranca un 4 % más cerca y se asienta
    z *= 1 + 0.04 * (1 - suave(t_local / 0.25))
    return z, dx, dy


def cuadro(base, W, H, z, dx, dy):
    bw, bh = base.size
    # tamaño de la ventana de recorte en la imagen base (margen 1.18 → zoom 1 = ventana W*1.18/... )
    vw, vh = bw / 1.18 / z, bh / 1.18 / z
    cx = bw / 2 + dx * bw; cy = bh / 2 + dy * bh
    cx = min(max(cx, vw / 2), bw - vw / 2); cy = min(max(cy, vh / 2), bh - vh / 2)
    caja = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)
    return base.resize((W, H), Image.BICUBIC, box=caja)


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    ruta_plan, salida = sys.argv[1], sys.argv[2]
    borrador = "--borrador" in sys.argv
    carpeta = os.path.dirname(os.path.abspath(ruta_plan))
    plan = json.load(open(ruta_plan, encoding="utf8"))
    W, H, FPS = plan.get("ancho", 1920), plan.get("alto", 1080), plan.get("fps", 30)
    if borrador: W, H = W // 2 // 2 * 2, H // 2 // 2 * 2
    rel = lambda p: p if os.path.isabs(p) else os.path.join(carpeta, p)

    planos, t = [], 0.0
    for i, p in enumerate(plan["planos"]):
        ini = p.get("inicio", t); fin = p["fin"]
        planos.append((i + 1, ini, fin, p)); t = fin
    total = planos[-1][2]

    tmp_video = salida + ".video.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast" if borrador else "medium",
           "-crf", "20", "-pix_fmt", "yuv420p", tmp_video]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n_total = int(round(total * FPS))
    actual, base = None, None
    for f in range(n_total):
        tt = f / FPS
        n, ini, fin, p = next((x for x in planos if x[1] <= tt < x[2]), planos[-1])
        if actual != n:
            img = rel(p["imagen"]) if p.get("imagen") else None
            im = Image.open(img) if img and os.path.exists(img) else tarjeta(p.get("texto", ""), W, H, n)
            base, actual = cubrir(im, W, H), n
        dur = fin - ini; tl = tt - ini
        z, dx, dy = camara(p.get("movimiento", "zoom_in"), suave(tl / max(dur, 1e-3)), tl, dur)
        ff.stdin.write(np.asarray(cuadro(base, W, H, z, dx, dy), dtype=np.uint8).tobytes())
        if f % FPS == 0: print(f"\r  imagen {tt:6.1f}s / {total:.1f}s", end="", flush=True)
    ff.stdin.close(); ff.wait(); print()

    # audio: voz al frente, música en bucle por debajo
    entradas, filtros, mezcla = ["-i", tmp_video], [], []
    if plan.get("voz") and os.path.exists(rel(plan["voz"])):
        entradas += ["-i", rel(plan["voz"])]; filtros.append(f"[{len(mezcla) + 1}:a]volume=1.0[a{len(mezcla)}]"); mezcla.append(1)
    if plan.get("musica") and os.path.exists(rel(plan["musica"])):
        entradas += ["-stream_loop", "-1", "-i", rel(plan["musica"])]
        vol = plan.get("volumen_musica", 0.12)
        filtros.append(f"[{len(mezcla) + 1}:a]volume={vol},afade=t=out:st={max(0, total - 2)}:d=2[a{len(mezcla)}]")
        mezcla.append(1)
    if mezcla:
        etiquetas = "".join(f"[a{i}]" for i in range(len(mezcla)))
        filtro = ";".join(filtros) + f";{etiquetas}amix=inputs={len(mezcla)}:normalize=0,loudnorm=I=-14:TP=-1.5[aout]"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *entradas, "-filter_complex", filtro,
                        "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-t", f"{total:.3f}", "-movflags", "+faststart", salida], check=True)
        os.remove(tmp_video)
    else:
        os.replace(tmp_video, salida)
    print(f"  listo: {salida}  ({total:.1f} s, {W}x{H})")


if __name__ == "__main__":
    main()
