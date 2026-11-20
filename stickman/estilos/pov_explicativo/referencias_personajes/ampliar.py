"""Amplía y limpia los 90 personajes de las hojas de referencia para usarlos en video vertical.

- Corta cada viñeta de la hoja original (sin el texto del nombre).
- Amplía x4 con Real-ESRGAN x4plus anime 6B (limpia la compresión JPEG y deja la línea nítida) y luego x2 con
  Lanczos: cada personaje queda de ~1000x1400 px.
- «Aclara»: blancos puros, negros más profundos, enfoque suave.
- Hoja A (fondo blanco): además genera el recorte con fondo transparente.

Uso:  python3 ampliar.py --modelo RUTA/RealESRGAN_x4plus_anime_6B.pth
El modelo se baja de Hugging Face (repo ximso/RealESRGAN_x4plus_anime_6B). Requiere torch, spandrel, scipy.
Salida: hd/hoja_A/NN_oficio.jpg, hd/hoja_A/NN_oficio_recorte.png, hd/hoja_B/..., hd/hoja_C/...
"""
import os, sys, time
import numpy as np
import torch
from PIL import Image, ImageFilter
from spandrel import ModelLoader
from recortar import HOJAS, sin_fondo

AQUI = os.path.dirname(os.path.abspath(__file__))


def aclarar(im):
    a = np.asarray(im, np.float32)
    lum = a.mean(axis=2, keepdims=True); sat = a.max(axis=2, keepdims=True) - a.min(axis=2, keepdims=True)
    # niveles: 22 -> 0, 238 -> 255 (blancos casi puros se vuelven blancos)
    b = np.clip((a - 22) * 255 / (238 - 22), 0, 255)
    # grises neutros muy claros (fondo, cabezas) -> blanco puro
    blanco = (lum > 228) & (sat < 22)
    b = np.where(blanco, 255, b)
    im = Image.fromarray(b.astype(np.uint8))
    return im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))


def main():
    ruta = sys.argv[sys.argv.index("--modelo") + 1]
    torch.set_num_threads(os.cpu_count() or 4)
    m = ModelLoader().load_from_file(ruta).eval()
    for clave, h in HOJAS.items():
        hoja = Image.open(os.path.join(AQUI, h["archivo"])).convert("RGB")
        nombres = h["nombres"].split()
        out = os.path.join(AQUI, "hd", f"hoja_{clave}"); os.makedirs(out, exist_ok=True)
        i = 0; t0 = time.time()
        for (y0, y1) in h["filas"]:
            for (x0, x1) in h["cols"]:
                p = hoja.crop((x0 + 3, y0 + 3 + h["arriba"], x1 - 3, y1 - 3))
                x = torch.from_numpy(np.asarray(p, np.float32) / 255).permute(2, 0, 1)[None]
                with torch.no_grad():
                    y = m.model(x)
                g = Image.fromarray((y[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255).astype(np.uint8))
                g = g.resize((g.width * 2, g.height * 2), Image.LANCZOS)
                g = aclarar(g)
                nom = f"{i + 1:02d}_{nombres[i]}"
                g.save(os.path.join(out, nom + ".jpg"), quality=92)
                if clave == "A":
                    sin_fondo(g).save(os.path.join(out, nom + "_recorte.png"), optimize=True)
                i += 1
        print(clave, i, "personajes", round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    main()
