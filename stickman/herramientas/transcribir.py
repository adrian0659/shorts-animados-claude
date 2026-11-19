"""Transcribe una voz en español con tiempos por palabra (faster-whisper, modelo «small»).

    pip install faster-whisper
    python3 herramientas/transcribir.py voz.mp3 carpeta_salida/
Escribe palabras.json ([{w, a, b}]) y transcripcion.txt en la carpeta de salida.
El audio se decodifica con ffmpeg (la versión de PyAV instalada puede fallar al abrir mp3 directamente).
"""
import json, os, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel

ruta, salida = sys.argv[1], sys.argv[2]
os.makedirs(salida, exist_ok=True)
crudo = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", ruta, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                       capture_output=True, check=True).stdout
audio = np.frombuffer(crudo, np.int16).astype(np.float32) / 32768
segs, _ = WhisperModel("small", device="cpu", compute_type="int8").transcribe(audio, language="es", word_timestamps=True)
pal, txt = [], []
for s in segs:
    txt.append(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}")
    pal += [dict(w=w.word.strip(), a=round(w.start, 2), b=round(w.end, 2)) for w in s.words]
json.dump(pal, open(os.path.join(salida, "palabras.json"), "w"), ensure_ascii=False, indent=0)
open(os.path.join(salida, "transcripcion.txt"), "w").write("\n".join(txt))
print("\n".join(txt))
