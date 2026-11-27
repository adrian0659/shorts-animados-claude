"""Sonido sintetizado del cómic de Logan (sin samples externos).
Uso: python3 audio/sonido.py out/audio.wav"""
import sys, wave
import numpy as np

SR = 44100
DUR = 16.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
fr = lambda f: int(f / 30 * SR)  # cuadro -> muestra

def lowpass(x, a):
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += a * (x[i] - acc); y[i] = acc
    return y

def onepole(x, cutoff):
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    return lowpass(x, a)

def add(buf, sig, start, gain=1.0):
    end = min(len(buf), start + len(sig))
    buf[start:end] += sig[: end - start] * gain

def pluck(freq, dur=2.2, bright=0.5):
    n = int(SR * dur); p = int(SR / freq)
    ring = rng.uniform(-1, 1, p)
    out = np.empty(n)
    for i in range(n):
        j = i % p
        out[i] = ring[j]
        ring[j] = 0.996 * (bright * ring[j] + (1 - bright) * ring[(j + 1) % p])
    return out * np.exp(-np.linspace(0, 3, n))

mix = np.zeros(N)

# viento: ruido filtrado que sube y baja
w = onepole(rng.normal(0, 1, N), 500)
swell = 0.6 + 0.4 * np.sin(np.linspace(0, 5 * np.pi, N))
mix += w * swell * 0.15

# dron grave en Re menor
t = np.arange(N) / SR
drone = sum(np.sin(2 * np.pi * f * t) * g for f, g in [(73.4, 0.5), (110, 0.25), (146.8, 0.15)])
env = np.clip(t / 2, 0, 1) * np.clip((fr(330) / SR + 0.1 - t) * 4, 0, 1)
mix += drone * env * 0.12

# guitarra western (Re menor) en las primeras viñetas
notes = [(0, 293.7), (14, 349.2), (28, 440), (46, 392), (60, 349.2), (78, 293.7),
         (100, 220), (118, 293.7), (136, 349.2), (160, 329.6), (190, 293.7), (215, 261.6), (240, 293.7)]
for f0, hz in notes:
    add(mix, pluck(hz), fr(f0), 0.35)

# whoosh en cada viñeta que entra
for f0 in [92, 182, 282, 362]:
    n = int(SR * 0.45)
    x = onepole(rng.normal(0, 1, n), 2500) * np.sin(np.linspace(0, np.pi, n)) ** 2
    add(mix, x, fr(f0) - int(SR * 0.1), 0.9)

# graznido del cuervo
def caw(start):
    n = int(SR * 0.35); tt = np.arange(n) / SR
    f = 700 - 250 * tt / tt[-1]
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sign(np.sin(ph)) * 0.5 + np.sin(ph * 2) * 0.3 + rng.normal(0, 0.3, n)
    s = onepole(s, 3000) * np.sin(np.linspace(0, np.pi, n)) ** 0.5
    add(mix, s, start, 0.45)
caw(fr(226)); caw(fr(226) + int(SR * 0.42))

# subida de tensión antes del golpe (ojos abriéndose)
n = fr(330) - fr(296); tt = np.arange(n) / SR
rise = np.sin(2 * np.pi * np.cumsum(80 + 400 * (tt / tt[-1]) ** 2) / SR) * (tt / tt[-1]) ** 2
add(mix, rise, fr(296), 0.3)

# ¡CRAC!: chasquido + golpe grave
n = int(SR * 1.2); tt = np.arange(n) / SR
crack = rng.normal(0, 1, n) * np.exp(-tt * 30)
boom = np.sin(2 * np.pi * (45 + 60 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 3.5)
add(mix, crack * 0.9 + boom * 1.2, fr(330))

# remate con el título: acorde + guitarra
n = int(SR * 3); tt = np.arange(n) / SR
chord = sum(np.sin(2 * np.pi * f * tt) for f in [146.8, 220, 293.7, 349.2]) * np.exp(-tt * 0.9) * 0.25
add(mix, chord, fr(416))
add(mix, onepole(rng.normal(0, 1, int(SR * 0.6)), 1500) * np.exp(-np.linspace(0, 6, int(SR * 0.6))), fr(416), 0.8)
for k, hz in enumerate([146.8, 220, 293.7, 440]):
    add(mix, pluck(hz, 3.0, 0.6), fr(416) + k * 2200, 0.4)

# final: fundido y normalizado
mix *= np.clip((DUR - t) / 0.6, 0, 1)
mix = np.tanh(mix * 1.2)
mix /= np.max(np.abs(mix)) * 1.12
data = (mix * 32767).astype(np.int16)
st = np.stack([data, data], 1)
with wave.open(sys.argv[1], 'wb') as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(st.tobytes())
print('ok', sys.argv[1])
