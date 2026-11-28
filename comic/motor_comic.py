#!/usr/bin/env python3
"""Motor de shorts narrados de cómic (estilo "¿Sabías que...?").

Toma páginas de cómic, una voz narrando y un plan (JSON) que dice qué viñeta se ve mientras se dice
cada frase. Hace el video vertical con paneos y acercamientos suaves sobre cada viñeta, cortes secos,
sacudida en los golpes, y mezcla la voz con música de fondo que baja sola cuando se habla.

Uso:
    python3 motor_comic.py plan.json --fotos   # hoja de revisión: una foto por toma
    python3 motor_comic.py plan.json           # video final

Plan (ver ejemplos/plan_ejemplo.json):
{
  "salida": "salida/mi_short.mp4",
  "voz": "voz.mp3",                       # narración; los tiempos salen solos con Whisper
  "musica": "musica.mp3",                 # opcional
  "vol_musica": 0.18,
  "tomas": [
    {"texto": "¿Sabías que ...?", "img": "paginas/p1.jpg", "panel": 0, "mov": "zoom_in", "impacto": true},
    {"texto": "frase larga ...", "vinetas": [            # varias viñetas repartidas en una frase
        {"img": "paginas/p1.jpg", "panel": 2},
        {"img": "paginas/p2.jpg", "caja": [10, 20, 600, 900], "mov": "pan_abajo"}]}
  ]
}
- "panel": número de viñeta según paneles.py (se detecta solo). "caja": [x0,y0,x1,y1] a mano. Sin
  ninguno de los dos se usa la página completa.
- "mov": auto, zoom_in, zoom_out, pan_der, pan_izq, pan_abajo, pan_arriba, quieto.
- "dur": segundos fijos (solo si no hay voz).
- "peso" en una viñeta: cuánto tiempo recibe dentro de su frase (por defecto 1).
"""
import difflib
import json
import os
import re
import subprocess
import sys
import unicodedata

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paneles  # noqa: E402

ANCHO, ALTO, FPS = 1080, 1920, 30
MIN_ANCHO = float(os.environ.get("MIN_ANCHO", 0.45))  # fracción del ancho de página


# ---------------------------------------------------------------- tiempos con Whisper
def leer_audio(ruta, sr=16000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def duracion(ruta):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", ruta],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def normal(p):
    p = unicodedata.normalize("NFD", p.lower())
    p = "".join(c for c in p if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9ñ]", "", p)


def palabras_whisper(ruta_voz, cache):
    if os.path.exists(cache):
        with open(cache) as fh:
            return json.load(fh)
    from faster_whisper import WhisperModel
    print("Transcribiendo la voz con Whisper (solo la primera vez)...")
    m = WhisperModel(os.environ.get("WHISPER_MODELO", "small"), compute_type="int8")
    segs, _ = m.transcribe(leer_audio(ruta_voz), language="es", word_timestamps=True)
    pal = [{"p": w.word.strip(), "t0": round(w.start, 3), "t1": round(w.end, 3)} for s in segs for w in s.words]
    with open(cache, "w") as fh:
        json.dump(pal, fh, ensure_ascii=False, indent=0)
    return pal


def tiempos_tomas(plan, base):
    """Devuelve [(t0, t1)] por toma: cada toma empieza cuando la voz dice su primera palabra."""
    tomas = plan["tomas"]
    if not plan.get("voz"):
        t, res = 0.0, []
        for tm in tomas:
            res.append((t, t + tm.get("dur", 2.5)))
            t += tm.get("dur", 2.5)
        return res, t
    voz = os.path.join(base, plan["voz"])
    total = duracion(voz)
    wh = palabras_whisper(voz, os.path.splitext(voz)[0] + ".palabras.json")
    guion, dueno = [], []
    for i, tm in enumerate(tomas):
        for p in tm.get("texto", "").split():
            if normal(p):
                guion.append(normal(p))
                dueno.append(i)
    sm = difflib.SequenceMatcher(None, guion, [normal(w["p"]) for w in wh], autojunk=False)
    mapa = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            mapa[a + k] = b + k
    inicios = []
    for i in range(len(tomas)):
        idx = [g for g, d in enumerate(dueno) if d == i]
        t = None
        for g in idx:  # primera palabra de la frase que Whisper reconoció
            if g in mapa:
                t = wh[mapa[g]]["t0"]
                # restar lo que dura la parte no reconocida antes de ella
                t -= 0.3 * (idx.index(g))
                break
        inicios.append(t)
    inicios[0] = 0.0
    # rellenar frases que no se encontraron, repartiendo entre vecinas
    for i, t in enumerate(inicios):
        if t is None:
            prev = inicios[i - 1]
            j = next((k for k in range(i + 1, len(inicios)) if inicios[k] is not None), None)
            fin = inicios[j] if j is not None else total
            inicios[i] = prev + (fin - prev) * 0.5
    for i in range(1, len(inicios)):  # corte un poco antes de la palabra, se siente más vivo
        inicios[i] = max(inicios[i - 1] + 0.4, inicios[i] - 0.08)
    fin_total = total + 0.4
    return [(inicios[i], inicios[i + 1] if i + 1 < len(inicios) else fin_total) for i in range(len(inicios))], fin_total


# ---------------------------------------------------------------- cámara sobre la viñeta
_imgs, _cajas = {}, {}


def pagina(ruta):
    if ruta not in _imgs:
        _imgs[ruta] = Image.open(ruta).convert("RGB")
    return _imgs[ruta]


def caja_de(v, base):
    ruta = os.path.join(base, v["img"])
    img = pagina(ruta)
    if "caja" in v:
        return ruta, v["caja"]
    if "caja_rel" in v:  # fracciones de la página: [x0, y0, x1, y1] entre 0 y 1
        a, b, c, d = v["caja_rel"]
        return ruta, [a * img.width, b * img.height, c * img.width, d * img.height]
    if "panel" in v:
        if ruta not in _cajas:
            _cajas[ruta] = paneles.detectar(ruta)[1]
        cajas = _cajas[ruta]
        if v["panel"] >= len(cajas):
            sys.exit(f"{v['img']} solo tiene {len(cajas)} viñetas detectadas (pediste la {v['panel']}).")
        return ruta, cajas[v["panel"]]
    return ruta, [0, 0, img.width, img.height]


def suave(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def vista(img, caja, mov, u):
    """Rectángulo (x0, y0, x1, y1) de la página que se ve en el instante u (0..1) de la toma."""
    aspecto = ANCHO / ALTO
    x0, y0, x1, y1 = caja
    bw, bh = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ancha = bw / bh > aspecto
    if ancha:
        vh, vw = bh, bh * aspecto
    else:
        vw, vh = bw, bw / aspecto
    # nunca acercarse tanto que se vea borroso: la vista mide al menos MIN_ANCHO de la página
    if vw < MIN_ANCHO * img.width:
        k = MIN_ANCHO * img.width / vw
        vw, vh = vw * k, vh * k
    if mov == "auto":
        r = (bw / bh) / aspecto
        if r > 1.35:
            mov = "pan_der"
        elif r < 1 / 1.35:
            mov = "pan_abajo"
        else:
            mov = "zoom_in"
    e = suave(u)
    zoom = 1.0
    if mov == "zoom_in":
        zoom = 1.0 - 0.14 * e
    elif mov == "zoom_out":
        zoom = 0.86 + 0.14 * e
    elif mov != "quieto":
        zoom = 0.97 - 0.04 * e  # un poco de empuje también al panear
    vw2, vh2 = vw * zoom, vh * zoom
    # recorrido disponible dentro de la viñeta
    hx, hy = max(0.0, (bw - vw2) / 2), max(0.0, (bh - vh2) / 2)
    if mov in ("pan_der", "pan_izq") and hx < bw * 0.04:
        hx = vw2 * 0.06
    if mov in ("pan_abajo", "pan_arriba") and hy < bh * 0.04:
        hy = vh2 * 0.06
    px = {"pan_der": -1 + 2 * e, "pan_izq": 1 - 2 * e}.get(mov, 0.0)
    py = {"pan_abajo": -1 + 2 * e, "pan_arriba": 1 - 2 * e}.get(mov, 0.0)
    cx2, cy2 = cx + px * hx, cy + py * hy
    # que nunca se salga de la página
    s = min(1.0, img.width / vw2, img.height / vh2)
    vw2, vh2 = vw2 * s, vh2 * s
    ax = min(max(cx2 - vw2 / 2, 0), img.width - vw2)
    ay = min(max(cy2 - vh2 / 2, 0), img.height - vh2)
    return ax, ay, ax + vw2, ay + vh2


def cuadro(v, base, u, t_local):
    ruta, caja = caja_de(v, base)
    img = pagina(ruta)
    x0, y0, x1, y1 = vista(img, caja, v.get("mov", "auto"), u)
    if v.get("impacto") and t_local < 0.35:  # golpe: entra más cerca y tiembla
        k = 1 - t_local / 0.35
        w, h = x1 - x0, y1 - y0
        z = 0.08 * k
        rng = np.random.default_rng(int(t_local * 1000))
        dx, dy = rng.uniform(-1, 1, 2) * 0.03 * k * np.array([w, h])
        x0, y0, x1, y1 = x0 + w * z / 2 + dx, y0 + h * z / 2 + dy, x1 - w * z / 2 + dx, y1 - h * z / 2 + dy
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(img.width, x1), min(img.height, y1)
    return img.resize((ANCHO, ALTO), Image.BICUBIC, box=(x0, y0, x1, y1))


def lista_vistas(plan, tiempos):
    """Aplana tomas -> [(viñeta, t0, t1)] repartiendo cada frase entre sus viñetas."""
    res = []
    for tm, (t0, t1) in zip(plan["tomas"], tiempos):
        vs = tm.get("vinetas") or [tm]
        pesos = [x.get("peso", 1.0) for x in vs]
        t = t0
        for x, p in zip(vs, pesos):
            d = (t1 - t0) * p / sum(pesos)
            v = dict(x)
            v.setdefault("impacto", tm.get("impacto", False) if x is vs[0] else False)
            res.append((v, t, t + d))
            t += d
    return res


# ---------------------------------------------------------------- salida
def hoja_fotos(vistas, base, salida):
    fotos = []
    for v, t0, t1 in vistas:
        tw, th = (216, 384) if ALTO > ANCHO else (384, 216)
        im = cuadro(v, base, 0.5, 1.0).resize((tw, th))
        ImageDraw.Draw(im).text((6, 6), f"{t0:.1f}s", fill="yellow")
        fotos.append(im)
    cols = 8
    filas = (len(fotos) + cols - 1) // cols
    hoja = Image.new("RGB", (cols * tw, filas * th), "black")
    for i, f in enumerate(fotos):
        hoja.paste(f, ((i % cols) * tw, (i // cols) * th))
    hoja.save(salida, quality=85)
    print(f"Hoja de revisión: {salida}")


def render(plan, base, vistas, total, salida):
    tmp = salida + ".sinaudio.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{ANCHO}x{ALTO}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                           "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    n = int(round(total * FPS))
    k = 0
    for f in range(n):
        t = f / FPS
        while k + 1 < len(vistas) and t >= vistas[k + 1][1]:
            k += 1
        v, t0, t1 = vistas[k]
        u = (t - t0) / max(0.01, t1 - t0)
        ff.stdin.write(cuadro(v, base, u, t - t0).tobytes())
        if f % (FPS * 5) == 0:
            print(f"  {t:5.1f}/{total:.1f} s")
    ff.stdin.close()
    ff.wait()

    entradas, filtro = ["-i", tmp], ""
    if plan.get("voz"):
        entradas += ["-i", os.path.join(base, plan["voz"])]
        if plan.get("musica"):
            entradas += ["-stream_loop", "-1", "-i", os.path.join(base, plan["musica"])]
            vol = plan.get("vol_musica", 0.18)
            filtro = (f"[1:a]aformat=channel_layouts=stereo,asplit=2[v1][v2];"
                      f"[2:a]aformat=channel_layouts=stereo,volume={vol}[m];"
                      f"[m][v2]sidechaincompress=threshold=0.03:ratio=4:attack=20:release=400[md];"
                      f"[v1][md]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5[a]")
        else:
            filtro = "[1:a]loudnorm=I=-14:TP=-1.5[a]"
    cmd = ["ffmpeg", "-y", "-v", "error"] + entradas
    if filtro:
        cmd += ["-filter_complex", filtro, "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "copy", "-t", f"{total:.2f}", "-movflags", "+faststart", salida]
    subprocess.run(cmd, check=True)
    os.remove(tmp)
    print(f"Listo: {salida}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ruta_plan = sys.argv[1]
    base = os.path.dirname(os.path.abspath(ruta_plan))
    with open(ruta_plan) as fh:
        plan = json.load(fh)
    global ANCHO, ALTO
    if plan.get("formato") == "horizontal":  # 16:9 para YouTube
        ANCHO, ALTO = 1920, 1080
    tiempos, total = tiempos_tomas(plan, base)
    for tm, (a, b) in zip(plan["tomas"], tiempos):
        print(f"{a:6.2f}-{b:6.2f}  {tm.get('texto', '')[:70]}")
    vistas = lista_vistas(plan, tiempos)
    salida = os.path.join(base, plan.get("salida", "salida/short.mp4"))
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    if "--fotos" in sys.argv:
        hoja_fotos(vistas, base, os.path.splitext(salida)[0] + "_hoja.jpg")
    else:
        render(plan, base, vistas, total, salida)


if __name__ == "__main__":
    main()
