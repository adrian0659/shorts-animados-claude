"""Efectos de sonido y música de fondo sintetizados (sin archivos externos ni licencias)."""
import wave
import numpy as np

SR = 44100

def _t(d): return np.arange(int(SR * d)) / SR

def pop(d=0.12):
    t = _t(d); f = 900 * np.exp(-t * 30) + 250
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35) * 0.6

def whoosh(d=0.45):
    t = _t(d); n = np.random.default_rng(1).standard_normal(len(t))
    # ruido filtrado con ventana suave (paso bajo simple variable)
    out = np.zeros_like(n); a = 0
    for i, v in enumerate(n):
        k = 0.02 + 0.25 * np.sin(np.pi * i / len(n)); a += k * (v - a); out[i] = a
    return out * np.sin(np.pi * t / d) ** 2 * 1.2

def ding(f=1320, d=0.9):
    t = _t(d)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-t * 5) * 0.35

def latido():
    t = _t(0.18)
    golpe = lambda: np.sin(2 * np.pi * (60 + 40 * np.exp(-t * 30)) * t) * np.exp(-t * 22)
    s = np.zeros(int(SR * 0.45)); g = golpe()
    s[:len(g)] += g; s[int(SR * 0.2):int(SR * 0.2) + len(g)] += g * 0.7
    return s * 0.9

def boing(d=0.5):
    t = _t(d); f = 220 + 120 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5) * 0.5

def tada():
    s = np.zeros(int(SR * 1.2))
    for i, f in enumerate([523, 659, 784, 1046]):
        n = ding(f, 1.0) * 0.8; o = int(SR * 0.07 * i); s[o:o + len(n)] += n[:len(s) - o]
    return s

def musica(dur, bpm=104):
    """Bucle alegre de pulsos (bajo + punteo) muy bajito, para no tapar."""
    s = np.zeros(int(SR * dur)); beat = 60 / bpm
    prog = [[262, 330, 392], [220, 262, 330], [175, 220, 262], [196, 247, 294]]
    i = 0; tt = 0.0
    while tt < dur:
        acorde = prog[(i // 8) % 4]
        f = acorde[i % 3] * (2 if i % 4 == 3 else 1)
        t = _t(beat * 0.9)
        nota = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 7) * 0.18
        if i % 2 == 0:
            nota += np.sin(2 * np.pi * acorde[0] / 2 * t) * np.exp(-t * 4) * 0.22
        o = int(tt * SR); e = min(len(s), o + len(nota)); s[o:e] += nota[:e - o]
        i += 1; tt += beat / 2
    fade = np.minimum(1, np.minimum(np.arange(len(s)) / SR / 0.5, (len(s) - np.arange(len(s))) / SR / 1.0))
    return s * fade


def tension(dur, bpm=84):
    """Música de suspenso: bajo grave sostenido, pulso como latido y notas menores sueltas, muy bajita."""
    t = _t(dur); s = np.zeros(len(t))
    for f, v in [(55, 0.22), (82.4, 0.12), (58.3, 0.08)]:                 # dron grave con leve disonancia
        s += np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.2 * t)) * v
    s *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.25 * t)
    beat = 60 / bpm; tt = 0.0; i = 0
    notas = [220, 261.6, 207.7, 196, 233.1]
    while tt < dur:
        g = latido() * 0.5; o = int(tt * SR); e = min(len(s), o + len(g)); s[o:e] += g[:e - o]
        if i % 4 == 2:
            n = ding(notas[(i // 4) % len(notas)], 2.0) * 0.35; e = min(len(s), o + len(n)); s[o:e] += n[:e - o]
        tt += beat; i += 1
    fade = np.minimum(1, np.minimum(np.arange(len(s)) / SR / 1.0, (len(s) - np.arange(len(s))) / SR / 1.5))
    return s * fade * 0.6

def timbre(veces=2):
    """Teléfono sonando (dos tonos alternos), 'veces' repiques."""
    out = np.zeros(int(SR * 1.2 * veces))
    for v in range(veces):
        t = _t(0.8)
        r = (np.sin(2 * np.pi * 1400 * t) + np.sin(2 * np.pi * 1750 * t)) * (np.sin(2 * np.pi * 20 * t) > 0) * 0.25
        o = int(SR * 1.2 * v); out[o:o + len(r)] += r * np.minimum(1, (0.8 - t) * 20)
    return out

def alarma(d=1.6):
    t = _t(d); f = 700 + 300 * (np.sin(2 * np.pi * 2.5 * t) > 0)
    return np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.12 * np.minimum(1, (d - t) * 6)

def impacto(d=1.4):
    """Golpe grave de suspenso (para revelaciones)."""
    t = _t(d); n = np.random.default_rng(3).standard_normal(len(t))
    grave = np.sin(2 * np.pi * (45 + 60 * np.exp(-t * 8)) * t) * np.exp(-t * 2.5)
    return (grave * 0.9 + n * np.exp(-t * 25) * 0.25)

def cargar(ruta):
    """Lee cualquier audio (mp3, wav…) como mono a 44.1 kHz."""
    import subprocess
    crudo = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", ruta, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                           capture_output=True, check=True).stdout
    return np.frombuffer(crudo, np.int16).astype(np.float32) / 32768


class Mezcla:
    def __init__(self, dur):
        self.buf = np.zeros(int(SR * dur) + SR)

    def poner(self, t, sonido, vol=1.0):
        o = int(t * SR); e = min(len(self.buf), o + len(sonido))
        self.buf[o:e] += sonido[:e - o] * vol

    def guardar(self, ruta):
        b = self.buf / max(1e-6, np.abs(self.buf).max()) * 0.85
        with wave.open(ruta, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((b * 32767).astype(np.int16).tobytes())
