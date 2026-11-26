#!/usr/bin/env python3
"""
Monta un short de drama vertical (1080x1920) a partir de las tomas generadas con IA.

Uso:
    python3 montar.py CARPETA_DEL_PROYECTO [--sin-subtitulos] [--musica musica.mp3]

La carpeta debe tener una subcarpeta `tomas/` con los archivos en orden por nombre:
    tomas/01.mp4, tomas/02.mp4, ...          clips de video con su voz (Veo, Flow, Kling...)
    tomas/05.png + tomas/05.mp3              una imagen fija y su audio: se anima con zoom lento
    tomas/07.png (sin audio)                 imagen fija de 2.5 s en silencio

Qué hace:
    1. Normaliza cada toma a 1080x1920, 30 fps, audio estéreo 48 kHz (recorta al centro, no deforma).
    2. Las une en orden.
    3. Saca los tiempos de cada palabra con Whisper y los guarda en `palabras.json`.
       Si Whisper se equivoca en una palabra, corrige el texto en `palabras.json` y vuelve a correr:
       el archivo existente se reutiliza (bórralo para volver a transcribir).
    4. Pone subtítulos estilo karaoke: 1 a 3 palabras en mayúsculas, palabra activa en cian.
    5. Música opcional por debajo de las voces (-18 dB) y volumen final a -14 LUFS.
Resultado: CARPETA/final.mp4
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FUENTES = AQUI / "fuentes"
W, H, FPS = 1080, 1920, 30
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
AUD_EXT = [".mp3", ".wav", ".m4a", ".aac", ".ogg"]

# Estilo de subtítulos (medido del video de referencia)
FUENTE = "Barlow Condensed ExtraBold"
TAM = 92               # tamaño de letra
ALTURA = 0.80          # borde inferior de la línea (fracción desde arriba); la referencia la centra en ~78%
CIAN = "&H00FFFF00&"   # ASS usa BGR: R=00 G=FF B=FF
BLANCO = "&H00FFFFFF&"
MAX_PALABRAS = 3
MAX_LETRAS = 18


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.exit(f"Falló: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r.stdout


def duracion(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "csv=p=0", str(p)]).strip())


def tiene_audio(p):
    return bool(run(["ffprobe", "-v", "error", "-select_streams", "a",
                     "-show_entries", "stream=index", "-of", "csv=p=0", str(p)]).strip())


ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
LLENAR = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"


def normalizar(toma, salida):
    ext = toma.suffix.lower()
    if ext in VIDEO_EXT:
        if tiene_audio(toma):
            run(["ffmpeg", "-y", "-v", "error", "-i", str(toma),
                 "-vf", f"{LLENAR},fps={FPS}", *ENC, str(salida)])
        else:
            run(["ffmpeg", "-y", "-v", "error", "-i", str(toma),
                 "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                 "-vf", f"{LLENAR},fps={FPS}", "-shortest", *ENC, str(salida)])
        return
    # Imagen fija: zoom lento hacia adentro (o hacia afuera en tomas pares) durante lo que dure su audio
    audio = next((toma.with_suffix(e) for e in AUD_EXT if toma.with_suffix(e).exists()), None)
    dur = duracion(audio) + 0.15 if audio else 2.5
    n = int(dur * FPS) + 1
    entra = int(re.sub(r"\D", "", toma.stem) or 0) % 2 == 1
    z = f"1+0.08*on/{n}" if entra else f"1.08-0.08*on/{n}"
    vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
          f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},setsar=1")
    entradas = ["-loop", "1", "-i", str(toma)]
    if audio:
        entradas += ["-i", str(audio)]
    else:
        entradas += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    run(["ffmpeg", "-y", "-v", "error", *entradas, "-vf", vf, "-t", f"{dur:.3f}",
         "-af", "apad", *ENC, str(salida)])


def transcribir(wav, idioma="es"):
    try:
        from faster_whisper import WhisperModel
        import numpy as np
    except ImportError:
        sys.exit("Falta Whisper. Instálalo con:  pip install faster-whisper")
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000",
                          "-f", "s16le", "-"], capture_output=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    modelo = WhisperModel("small", compute_type="int8")
    segs, _ = modelo.transcribe(audio, language=idioma, word_timestamps=True, vad_filter=True)
    return [{"palabra": w.word.strip(), "inicio": round(w.start, 3), "fin": round(w.end, 3)}
            for s in segs for w in s.words if w.word.strip()]


def limpiar(p):
    return re.sub(r"[^\wÁÉÍÓÚÜÑáéíóúüñ¿?¡!'-]", "", p).strip("¿¡").upper()


def agrupar(palabras, cortes):
    """Grupos de 1-3 palabras; corta en puntuación, pausas y cambios de toma."""
    grupos, actual = [], []
    for i, w in enumerate(palabras):
        actual.append(w)
        sig = palabras[i + 1] if i + 1 < len(palabras) else None
        letras = sum(len(limpiar(x["palabra"])) + 1 for x in actual)
        fin = (sig is None or len(actual) >= MAX_PALABRAS or letras >= MAX_LETRAS
               or re.search(r"[.,!?;:…]$", w["palabra"])
               or sig["inicio"] - w["fin"] > 0.35
               or any(w["fin"] <= c < sig["inicio"] + 0.05 for c in cortes)
               or letras + len(limpiar(sig["palabra"])) > MAX_LETRAS + 4)
        if fin:
            grupos.append(actual)
            actual = []
    return grupos


def t_ass(s):
    s = max(0, s)
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def escribir_ass(grupos, ruta):
    margen = int(H * (1 - ALTURA))
    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{FUENTE},{TAM},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,7,3,2,90,90,{margen},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lineas = []
    for gi, g in enumerate(grupos):
        fin_grupo = g[-1]["fin"]
        if gi + 1 < len(grupos):  # sostener hasta el siguiente grupo si la pausa es corta
            sig = grupos[gi + 1][0]["inicio"]
            fin_grupo = sig if sig - fin_grupo < 0.6 else fin_grupo + 0.25
        else:
            fin_grupo += 0.4
        for wi, w in enumerate(g):
            ini = g[0]["inicio"] if wi == 0 else w["inicio"]
            fin = g[wi + 1]["inicio"] if wi + 1 < len(g) else fin_grupo
            texto = " ".join(
                (f"{{\\c{CIAN}}}{limpiar(x['palabra'])}{{\\c{BLANCO}}}" if xi == wi else limpiar(x["palabra"]))
                for xi, x in enumerate(g))
            pop = "{\\fscx112\\fscy112\\t(0,90,\\fscx100\\fscy100)}" if wi == 0 else ""
            lineas.append(f"Dialogue: 0,{t_ass(ini)},{t_ass(fin)},Sub,,0,0,0,,{pop}{texto}")
    ruta.write_text(cab + "\n".join(lineas) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Monta un short de drama con subtítulos karaoke.")
    ap.add_argument("proyecto", type=Path)
    ap.add_argument("--sin-subtitulos", action="store_true")
    ap.add_argument("--musica", type=Path, help="música de fondo (va 18 dB debajo de las voces)")
    ap.add_argument("--idioma", default="es")
    a = ap.parse_args()

    proy = a.proyecto.resolve()
    tomas = sorted(p for p in (proy / "tomas").iterdir()
                   if p.suffix.lower() in VIDEO_EXT | IMG_EXT) if (proy / "tomas").is_dir() else []
    if not tomas:
        sys.exit(f"No encontré tomas en {proy / 'tomas'} (01.mp4, 02.mp4, ... o imágenes .png/.jpg)")
    trabajo = proy / "_trabajo"
    shutil.rmtree(trabajo, ignore_errors=True)
    trabajo.mkdir()

    print(f"1/4 Normalizando {len(tomas)} tomas…")
    norm, cortes, t = [], [], 0.0
    for i, toma in enumerate(tomas):
        out = trabajo / f"{i:03d}.mp4"
        normalizar(toma, out)
        norm.append(out)
        t += duracion(out)
        cortes.append(t)
        print(f"   {toma.name}  →  termina en {t:5.2f} s")

    print("2/4 Uniendo…")
    lista = trabajo / "lista.txt"
    lista.write_text("".join(f"file '{p.as_posix()}'\n" for p in norm))
    unido = trabajo / "unido.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(unido)])

    filtros_v = "null"
    if not a.sin_subtitulos:
        pj = proy / "palabras.json"
        if pj.exists():
            print("3/4 Usando palabras.json existente (bórralo para volver a transcribir)")
            palabras = json.loads(pj.read_text(encoding="utf-8"))
        else:
            print("3/4 Transcribiendo con Whisper (la primera vez descarga el modelo)…")
            palabras = transcribir(unido, a.idioma)
            pj.write_text(json.dumps(palabras, ensure_ascii=False, indent=1), encoding="utf-8")
        ass = trabajo / "subs.ass"
        escribir_ass(agrupar(palabras, cortes[:-1]), ass)
        esc = lambda p: p.as_posix().replace(":", r"\:")
        filtros_v = f"subtitles=filename='{esc(ass)}':fontsdir='{esc(FUENTES)}'"
    else:
        print("3/4 Sin subtítulos")

    print("4/4 Mezclando y exportando…")
    final = proy / "final.mp4"
    if a.musica:
        fc = (f"[0:v]{filtros_v}[v];[1:a]volume=-18dB,aloop=-1:size=2e9[m];"
              f"[0:a][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
        entradas = ["-i", str(unido), "-i", str(a.musica)]
    else:
        fc = f"[0:v]{filtros_v}[v];[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]"
        entradas = ["-i", str(unido)]
    run(["ffmpeg", "-y", "-v", "error", *entradas, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         *ENC, "-movflags", "+faststart", str(final)])
    print(f"Listo: {final}  ({duracion(final):.1f} s)")


if __name__ == "__main__":
    main()
