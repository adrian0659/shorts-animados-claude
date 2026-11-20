"""Música de suspenso sintetizada (sin derechos): acordes graves en menor + pulso lento.
Uso: python3 musica_suspenso.py salida.wav 120"""
import sys, wave
import numpy as np
SR = 44100
dur = float(sys.argv[2]) if len(sys.argv) > 2 else 120
t = np.arange(int(SR * dur)) / SR
acordes = [(110.0, 130.81, 164.81), (87.31, 110.0, 130.81), (98.0, 116.54, 146.83), (82.41, 103.83, 123.47)]
s = np.zeros_like(t)
compas = 8.0
for i, ac in enumerate(acordes * int(dur // (compas * 4) + 1)):
    a, b = i * compas, (i + 1) * compas + 2
    m = (t >= a) & (t < b); tt = t[m] - a
    env = np.minimum(1, tt / 2.0) * np.minimum(1, np.maximum(0, (b - a - tt)) / 2.0)
    for f in ac:
        s[m] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.003 * tt)) * env * 0.12
# pulso grave tipo latido cada 1.2 s
for p in np.arange(0, dur, 1.2):
    i0 = int(p * SR); n = int(0.35 * SR); tt = np.arange(n) / SR
    golpe = np.sin(2 * np.pi * (55 + 30 * np.exp(-tt * 25)) * tt) * np.exp(-tt * 9) * 0.35
    s[i0:i0 + n] += golpe[:len(s) - i0]
fade = np.minimum(1, np.minimum(t / 3, (dur - t) / 4))
s = s * fade; s = s / np.abs(s).max() * 0.8
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((s * 32767).astype(np.int16).tobytes())
