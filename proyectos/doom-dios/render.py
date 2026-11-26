"""Render del short de cómic: viñetas del PDF con zoom lento, cortes en las palabras de la voz.

Uso:  python3 render.py <comic.pdf> [--preview] [--voz v.mp3 --palabras p.json --salida s.mp4]
Sale: doom_dios.mp4 (1080x1920, 30 fps) o preview.jpg con el primer cuadro de cada toma.
"""
import json, subprocess, sys, os, tempfile
from PIL import Image, ImageFilter, ImageEnhance

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))

# (palabra donde empieza, página, modo, caja x0,y0,x1,y1 en fracción de página, foco x)
TOMAS = [
    (0,   151, "cover", (0, 0, 1, .57), .45),        # Doom entre el fuego: "se convirtió en Dios"
    (9,   133, "cover", (0, 0, 1, 1), .5),           # portada #4: Doom con Sue y Valeria
    (18,  50,  "cover", (0, 0, 1, .7), .5),          # el multiverso muriendo
    (24,  11,  "cover", (0, .22, 1, .8), .5),        # mundos chocando
    (33,  22,  "cover", (0, 0, 1, 1), .5),           # el vacío / Beyonders
    (39,  23,  "cover", (0, .245, 1, .82), .62),     # "Soñadores. Destructores."
    (45,  48,  "fit",   (.06, .49, .94, .985), .5, 1.0),   # los héroes, derrotados
    (49,  23,  "fit",   (.04, .80, .96, .985), .5, 2.2),   # los ojos de Doom
    (53,  140, "fit",   (.04, .355, .96, .675), .62, 1.0), # "Los matamos y tomamos su poder"
    (64,  69,  "cover", (0, .5, 1, 1), .5),          # creación
    (73,  106, "fit",   (.28, .22, 1, .78), .5, 1.3),      # mapa de Battleworld
    (76,  64,  "cover", (0, 0, 1, 1), .5),           # trono del Dios Emperador
    (84,  55,  "fit",   (.05, .38, .95, .62), .5, 2.0),    # ojos en blanco: borró recuerdos
    (89,  109, "fit",   (.2, .4, .9, .58), .5, 1.5),       # Strange
    (96,  147, "cover", (0, .6, 1, 1), .45),         # Sue y Doom
    (102, 120, "fit",   (.5, .73, .96, .985), .5, 1.0),    # Franklin y Valeria
    (114, 75,  "cover", (0, 0, 1, 1), .5),           # la balsa en el desierto
    (118, 149, "cover", (0, 0, 1, .58), .5),         # frente a frente
    (131, 149, "fit",   (.5, .78, .93, .985), .5, 1.0),    # Reed
    (141, 122, "cover", (0, .6, 1, 1), .5),          # el rostro de Doom
    (153, 156, "cover", (0, 0, 1, .66), .5),         # pierde el poder
]

def page(pdf, n, cache):
    p = os.path.join(cache, f"p{n:03d}.png")
    if not os.path.exists(p):
        subprocess.run(["pdftoppm", "-r", "200", "-png", "-singlefile", "-f", str(n), "-l", str(n),
                        pdf, p[:-4]], check=True)
    return Image.open(p).convert("RGB")

def cover(img, cx, w, h):
    iw, ih = img.size
    if iw / ih > w / h:
        cw = ih * w / h
        x0 = min(max(cx * iw - cw / 2, 0), iw - cw)
        img = img.crop((int(x0), 0, int(x0 + cw), ih))
    else:
        ch = iw * h / w
        y0 = (ih - ch) / 2
        img = img.crop((0, int(y0), iw, int(y0 + ch)))
    return img.resize((w, h), Image.LANCZOS)

def lamina(pdf, toma, cache, w, h):
    _, n, modo, (x0, y0, x1, y1), cx, *resto = toma
    pg = page(pdf, n, cache)
    pw, ph = pg.size
    reg = pg.crop((int(x0 * pw), int(y0 * ph), int(x1 * pw), int(y1 * ph)))
    if modo == "cover":
        return cover(reg, cx, w, h)
    if resto:  # recorta la viñeta a esa proporción (ancho/alto) para que llene más pantalla
        a = resto[0]
        if reg.width / reg.height > a:
            cw = reg.height * a
            xc = min(max(cx * reg.width - cw / 2, 0), reg.width - cw)
            reg = reg.crop((int(xc), 0, int(xc + cw), reg.height))
    fondo = cover(reg, .5, w // 4, h // 4).filter(ImageFilter.GaussianBlur(10)).resize((w, h))
    fondo = ImageEnhance.Brightness(fondo).enhance(.45)
    fw = w
    fh = int(reg.height * fw / reg.width)
    if fh > h * .9:
        fh = int(h * .9); fw = int(reg.width * fh / reg.height)
    fondo.paste(reg.resize((fw, fh), Image.LANCZOS), ((w - fw) // 2, (h - fh) // 2))
    return fondo

def main():
    pdf = sys.argv[1]
    preview = "--preview" in sys.argv
    arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
    palabras = json.load(open(os.path.join(HERE, arg("--palabras", "palabras.json"))))
    voz = os.path.join(HERE, arg("--voz", "voz.mp3"))
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", voz]))
    total = dur + 0.4
    inicios = [0.0] + [max(palabras[t[0]]["s"] - 0.06, 0) for t in TOMAS[1:]]
    finales = inicios[1:] + [total]
    cache = os.path.join(tempfile.gettempdir(), "doom_paginas"); os.makedirs(cache, exist_ok=True)
    Z = 1.14  # margen para el zoom
    BW, BH = int(W * Z), int(H * Z)
    if preview:
        tiles = [lamina(pdf, t, cache, W, H).resize((270, 480)) for t in TOMAS]
        sh = Image.new("RGB", (270 * 7, 480 * 3))
        for i, t in enumerate(tiles):
            sh.paste(t, ((i % 7) * 270, (i // 7) * 480))
        sh.save(os.path.join(HERE, "preview.jpg"), quality=85)
        return
    sin_audio = os.path.join(cache, "video.mp4")
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                           "-crf", "18", "-pix_fmt", "yuv420p", sin_audio], stdin=subprocess.PIPE)
    for i, toma in enumerate(TOMAS):
        base = lamina(pdf, toma, cache, BW, BH)
        nfr = round(finales[i] * FPS) - round(inicios[i] * FPS)
        acerca = i % 2 == 0
        dx = (1 if i % 4 < 2 else -1) * 0.03
        for f in range(nfr):
            t = f / max(nfr - 1, 1)
            e = t * t * (3 - 2 * t) * 0.6 + t * 0.4
            z = 1 + (Z - 1) * (e if acerca else 1 - e)
            cw, ch = BW / z, BH / z
            cx = BW / 2 + dx * BW * (e - .5) * (z - 1) / (Z - 1)
            x0 = min(max(cx - cw / 2, 0), BW - cw); y0 = (BH - ch) / 2
            fr = base.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BILINEAR)
            ff.stdin.write(fr.tobytes())
        print(f"toma {i + 1}/{len(TOMAS)}", flush=True)
    ff.stdin.close(); ff.wait()
    out = os.path.join(HERE, arg("--salida", "doom_dios.mp4"))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", sin_audio, "-i", voz,
                    "-af", "apad,loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-shortest", out], check=True)
    print(out)

if __name__ == "__main__":
    main()
