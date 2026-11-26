#!/usr/bin/env python3
"""
Monta un short explicativo de cómics (1080x1920): narración + viñetas con acercamientos y paneos
sincronizados con la voz + subtítulos karaoke.

Uso:
    python3 comic/montar_comic.py CARPETA_DEL_PROYECTO [--sin-subtitulos] [--musica musica.mp3]

La carpeta debe tener:
    voz.mp3 (o .wav/.m4a)    la narración completa
    paginas/                 las páginas o viñetas escaneadas (jpg/png)
    escenas.json             qué imagen se ve en cada momento y cómo se mueve la cámara

escenas.json:
{
  "titulo": "HULK NO ERA VERDE",            (opcional: texto grande arriba los primeros 3 s)
  "escenas": [
    {"imagen": "paginas/portada.jpg",
     "empieza": "En su primer cómic",          primeras palabras de la frase donde entra esta imagen
     "de": [0, 0, 1, 1],                       rectángulo inicial [x, y, ancho, alto] de 0 a 1
     "a":  [0.25, 0.1, 0.5, 0.45]}             rectángulo final (opcional: sin él, acercamiento lento)
  ]
}
Cada escena dura hasta que empieza la siguiente; la última, hasta que termina la voz.
Para encontrar los rectángulos: abre la página, mide en píxeles y divide entre el ancho/alto
(o usa  --cuadricula  para sacar cada página con una cuadrícula al 10 %).
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "drama"))
from montar import (FUENTES, W, H, FPS, ENC, run, duracion, transcribir,  # noqa: E402
                    agrupar, escribir_ass)

MARGEN = 40           # margen a los lados de la viñeta
CAJA_ALTO = 1180      # alto máximo de la viñeta (deja libres título y subtítulos)
CENTRO_Y = 820        # centro vertical de la viñeta
BORDE = 6             # borde blanco tipo recorte
ENTRADA = 0.08        # la imagen cambia un poco antes de su palabra
AUD_EXT = [".mp3", ".wav", ".m4a", ".aac", ".ogg"]


def normal(t):
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9ñ ]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


def ubicar(escenas, palabras, total):
    """Pone tiempo de inicio a cada escena buscando su frase 'empieza' en la narración."""
    claves = [normal(w["palabra"]) for w in palabras]
    pos, inicios = 0, []
    for i, e in enumerate(escenas):
        if i == 0:
            inicios.append(0.0)
            continue
        buscar = normal(e["empieza"]).split()
        hallado = None
        for j in range(pos, len(claves) - len(buscar) + 1):
            if claves[j:j + len(buscar)] == buscar:
                hallado = j
                break
        if hallado is None:
            sys.exit(f"No encontré «{e['empieza']}» (escena {i + 1}) en la narración después de la escena "
                     f"anterior. Revisa palabras.json o cambia la frase.")
        pos = hallado + len(buscar)
        inicios.append(max(inicios[-1] + 0.3, palabras[hallado]["inicio"] - ENTRADA))
    return [(a, b) for a, b in zip(inicios, inicios[1:] + [total])]


def suave(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def rect_px(r, img):
    x, y, w, h = (max(0.0, min(1.0, v)) for v in r)
    return x * img.width, y * img.height, max(w, 0.02) * img.width, max(h, 0.02) * img.height


def fondo(img):
    """Toda la página, cubriendo 9:16, desenfocada y oscurecida."""
    esc = max(W / img.width, H / img.height)
    f = img.resize((int(img.width * esc) + 1, int(img.height * esc) + 1), Image.BILINEAR)
    f = f.crop(((f.width - W) // 2, (f.height - H) // 2, (f.width - W) // 2 + W, (f.height - H) // 2 + H))
    f = f.resize((W // 4, H // 4)).filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BILINEAR)
    return Image.blend(f, Image.new("RGB", (W, H), (0, 0, 0)), 0.55)


def cuadro(img, bg, r):
    x, y, w, h = r
    esc = min((W - 2 * MARGEN) / w, CAJA_ALTO / h)
    fw, fh = int(w * esc), int(h * esc)
    vineta = img.resize((fw, fh), Image.BICUBIC, box=(x, y, x + w, y + h))
    out = bg.copy()
    px, py = (W - fw) // 2, CENTRO_Y - fh // 2
    d = ImageDraw.Draw(out)
    d.rectangle([px - BORDE + 14, py - BORDE + 18, px + fw + BORDE + 14, py + fh + BORDE + 18], fill=(0, 0, 0))
    d.rectangle([px - BORDE, py - BORDE, px + fw + BORDE, py + fh + BORDE], fill=(255, 255, 255))
    out.paste(vineta, (px, py))
    return out


def cuadricula(proy):
    """Saca cada página con una cuadrícula al 10 % para elegir rectángulos."""
    dest = proy / "_cuadricula"
    dest.mkdir(exist_ok=True)
    for p in sorted((proy / "paginas").iterdir()):
        if p.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        img = Image.open(p).convert("RGB")
        d = ImageDraw.Draw(img)
        f = ImageFont.load_default(size=max(14, img.width // 40))
        for k in range(1, 10):
            x, y = img.width * k / 10, img.height * k / 10
            d.line([(x, 0), (x, img.height)], fill=(255, 0, 80), width=max(1, img.width // 400))
            d.line([(0, y), (img.width, y)], fill=(255, 0, 80), width=max(1, img.width // 400))
            d.text((x + 4, 4), f"{k / 10:.1f}", fill=(255, 0, 80), font=f)
            d.text((4, y + 4), f"{k / 10:.1f}", fill=(255, 0, 80), font=f)
        img.save(dest / f"{p.stem}.jpg", quality=85)
    print(f"Cuadrículas en {dest}")


def main():
    ap = argparse.ArgumentParser(description="Short explicativo de cómics con viñetas animadas.")
    ap.add_argument("proyecto", type=Path)
    ap.add_argument("--sin-subtitulos", action="store_true")
    ap.add_argument("--musica", type=Path, help="música de fondo (18 dB debajo de la voz)")
    ap.add_argument("--cuadricula", action="store_true", help="solo dibuja cuadrículas sobre las páginas")
    ap.add_argument("--idioma", default="es")
    a = ap.parse_args()
    proy = a.proyecto.resolve()
    if a.cuadricula:
        return cuadricula(proy)

    voz = next((proy / f"voz{e}" for e in AUD_EXT if (proy / f"voz{e}").exists()), None)
    if not voz:
        sys.exit(f"Falta la narración: {proy}/voz.mp3")
    guion = json.loads((proy / "escenas.json").read_text(encoding="utf-8"))
    escenas = guion["escenas"]
    total = duracion(voz) + 0.3
    trabajo = proy / "_trabajo"
    shutil.rmtree(trabajo, ignore_errors=True)
    trabajo.mkdir()

    pj = proy / "palabras.json"
    if pj.exists():
        print("1/4 Usando palabras.json existente (bórralo para volver a transcribir)")
        palabras = json.loads(pj.read_text(encoding="utf-8"))
    else:
        print("1/4 Transcribiendo la voz con Whisper…")
        palabras = transcribir(voz, a.idioma)
        pj.write_text(json.dumps(palabras, ensure_ascii=False, indent=1), encoding="utf-8")

    tiempos = ubicar(escenas, palabras, total)
    print(f"2/4 Animando {len(escenas)} escenas…")
    video = trabajo / "imagen.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                           "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(video)],
                          stdin=subprocess.PIPE)
    hechos = 0
    for i, (e, (t0, t1)) in enumerate(zip(escenas, tiempos)):
        ruta = proy / e["imagen"]
        if not ruta.exists():
            ff.kill()
            sys.exit(f"Falta la imagen de la escena {i + 1}: {ruta}")
        img = Image.open(ruta).convert("RGB")
        bg = fondo(img)
        r0 = rect_px(e.get("de", [0, 0, 1, 1]), img)
        if "a" in e:
            r1 = rect_px(e["a"], img)
        else:  # acercamiento lento del 8 % hacia el centro
            x, y, w, h = r0
            r1 = (x + w * 0.04, y + h * 0.04, w * 0.92, h * 0.92)
        fin = round(t1 * FPS)
        n = max(1, fin - hechos)
        for k in range(n):
            s = suave(k / max(1, n - 1))
            r = tuple(p + (q - p) * s for p, q in zip(r0, r1))
            ff.stdin.write(cuadro(img, bg, r).tobytes())
        hechos += n
        print(f"   {i + 1:02d} {Path(e['imagen']).name:28s} {t0:6.2f} → {t1:6.2f} s")
    ff.stdin.close()
    if ff.wait() != 0:
        sys.exit("ffmpeg falló al crear la imagen")

    print("3/4 Subtítulos…")
    filtros_v = "null"
    if not a.sin_subtitulos:
        ass = trabajo / "subs.ass"
        escribir_ass(agrupar(palabras, [t for t, _ in tiempos[1:]]), ass)
        if guion.get("titulo"):
            texto = ass.read_text(encoding="utf-8")
            texto = texto.replace("[Events]", "Style: Titulo,Barlow Condensed ExtraBold,104,&H0000E5FF,"
                                  "&H0000E5FF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,8,3,8,60,60,70,1"
                                  "\n\n[Events]")
            texto += (f"Dialogue: 1,0:00:00.00,0:00:03.00,Titulo,,0,0,0,,{{\\fad(0,250)}}"
                      f"{guion['titulo'].upper()}\n")
            ass.write_text(texto, encoding="utf-8")
        esc = lambda p: p.as_posix().replace(":", r"\:")
        filtros_v = f"subtitles=filename='{esc(ass)}':fontsdir='{esc(FUENTES)}'"

    print("4/4 Mezclando y exportando…")
    final = proy / "final.mp4"
    entradas = ["-i", str(video), "-i", str(voz)]
    largo = f"{hechos / FPS:.3f}"
    if a.musica:
        entradas += ["-i", str(a.musica)]
        audio = (f"[1:a]apad=whole_dur={largo}[v0];[2:a]volume=-18dB,aloop=-1:size=2e9[m];"
                 "[v0][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    else:
        audio = f"[1:a]apad=whole_dur={largo},loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    run(["ffmpeg", "-y", "-v", "error", *entradas, "-filter_complex", f"[0:v]{filtros_v}[v];{audio}",
         "-map", "[v]", "-map", "[a]", "-t", largo, *ENC, "-movflags", "+faststart", str(final)])
    print(f"Listo: {final}  ({duracion(final):.1f} s)")


if __name__ == "__main__":
    main()
