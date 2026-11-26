"""Música de suspenso y efectos sintetizados + voz. Uso: python3 mezcla.py VOZ.mp3 SALIDA.wav"""
import sys, subprocess, numpy as np
SR = 44100
voz_path, out = sys.argv[1], sys.argv[2]
voz = np.frombuffer(subprocess.check_output(["ffmpeg", "-v", "error", "-i", voz_path, "-ac", "1", "-ar", str(SR),
                                             "-f", "f32le", "-"]), np.float32).copy()
dur = len(voz) / SR + 0.6
n = int(dur * SR); t = np.arange(n) / SR
rng = np.random.default_rng(3)

def env(t0, a=0.01, d=1.0):
    x = t - t0
    return np.where(x < 0, 0, np.minimum(1, x / a) * np.exp(-np.maximum(x, 0) / d))



# --- música: dron grave en Re menor + pulso tipo latido que crece ---
lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t)
dron = (np.sin(2*np.pi*36.7*t) + 0.6*np.sin(2*np.pi*73.4*t) + 0.35*np.sin(2*np.pi*87.3*t + 1)
        + 0.25*np.sin(2*np.pi*110*t + 2) + 0.12*np.sin(2*np.pi*146.8*t*1.003)) * lfo
crece = np.clip((t - 22) / 20, 0, 1)
pad = 0.15 * np.sin(2*np.pi*220*t) * np.sin(2*np.pi*0.25*t)**2 * (0.3 + 0.7 * crece)
mus = 0.22 * dron + pad
bpm = 70 + 40 * crece
fase = np.cumsum(bpm / 60 / SR)
golpe = np.exp(-(fase % 1) * 9) * np.sin(2*np.pi*55*t)
golpe2 = np.exp(-((fase + 0.22) % 1) * 12) * np.sin(2*np.pi*50*t) * 0.6
mus += 0.35 * (golpe + golpe2) * np.clip((t - 2.8) / 3, 0, 1) * (t < 44.9)
mus *= np.clip(t / 0.5, 0, 1)
# silencio tenso antes del golpe final y respiro al final
mus *= np.where((t > 44.1) & (t < 44.9), 0.25, 1)

# --- efectos ---
sfx = np.zeros(n)
def boom(t0, g=1.0):
    x = t - t0; m = x >= 0
    f = 60 * np.exp(-np.maximum(x, 0) * 3) + 30
    ph = np.cumsum(2*np.pi*f/SR)
    s = np.sin(ph) * env(t0, 0.005, 0.6) + 0.5 * rng.standard_normal(n) * env(t0, 0.002, 0.08)
    sfx[:] += g * s * m
def whoosh(t0, g=0.5, L=0.5):
    x = t - t0; m = (x >= -L) & (x < 0.15)
    sh = np.clip(1 + x / L, 0, 1) ** 2 * np.exp(-np.maximum(x, 0) * 20)
    sfx[:] += g * rng.standard_normal(n) * sh * m * 0.4
for tt in [0.0, 1.3, 5.3, 19.7, 24.4, 28.0, 37.5, 44.1]:
    boom(tt, 0.8)
for tt in [2.8, 7.9, 13.3, 16.2, 22.0, 26.2, 30.4, 33.8, 35.5, 40.8, 47.4, 51.6, 56.8]:
    whoosh(tt, 0.5)
boom(44.9, 1.4)   # la columna
# crujido de huesos
x = t - 44.9; m = (x > 0) & (x < 0.5)
sfx += m * rng.standard_normal(n) * (rng.random(n) < 0.02) * 1.2 * np.exp(-np.maximum(x, 0) * 5)

sfx_s = sfx  # (sin filtro: ya es grave)
def rms(x): return np.sqrt(np.mean(x[np.abs(x) > 1e-4] ** 2) + 1e-12)
v = np.zeros(n); v[:len(voz)] = voz
# voz al frente; música ~13 dB abajo; efectos ~8 dB abajo
mus *= rms(v) / rms(mus) * 10 ** (-13 / 20)
sfx_s *= rms(v) / (np.max(np.abs(sfx_s)) + 1e-9) * 1.2
# ducking: la música baja cuando habla la voz
envv = np.convolve(np.abs(v), np.ones(4410) / 4410, mode="same")
duck = 1 - 0.35 * np.clip(envv / (envv.max() * 0.3), 0, 1)
mix = v + mus * duck + sfx_s * 0.5
fade = np.clip((dur - t) / 0.8, 0, 1)
mix *= fade
st = np.stack([mix, mix], 1).astype(np.float32)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", out], input=st.tobytes(), check=True)
print("audio ok")
