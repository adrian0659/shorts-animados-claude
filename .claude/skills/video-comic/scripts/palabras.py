"""Tiempos por palabra de la narración (Whisper local).
Uso: python3 palabras.py VOZ.mp3 palabras.json   (pip install faster-whisper)
Imprime cada frase con su tiempo y todas las palabras como  tiempo:palabra  para planear las tomas."""
import sys, json, subprocess, numpy as np
from faster_whisper import WhisperModel
voz, out = sys.argv[1], sys.argv[2]
a = np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", voz, "-ac", "1", "-ar", "16000",
                                           "-f", "f32le", "-"]), np.float32)
m = WhisperModel("small", compute_type="int8")
segs, _ = m.transcribe(a, language="es", word_timestamps=True)
pal = []
for s in segs:
    print(f"{s.start:6.2f}-{s.end:6.2f} {s.text}")
    pal += [[round(w.start, 2), round(w.end, 2), w.word.strip()] for w in s.words]
json.dump(pal, open(out, "w"), ensure_ascii=False, indent=0)
print("\n" + " ".join(f"{a:.1f}:{w}" for a, b, w in pal))
