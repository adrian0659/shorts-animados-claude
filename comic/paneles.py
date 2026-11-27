#!/usr/bin/env python3
"""Detecta las viñetas de una o varias páginas de cómic.

Uso:
    python3 paneles.py paginas/*.jpg            # crea paneles.json y fotos numeradas en salida/paneles/

Busca los "canales" (espacios blancos o negros entre viñetas) y devuelve la caja de cada viñeta
[x0, y0, x1, y1] en píxeles de la página. Revisa las fotos numeradas: si alguna caja quedó mal,
corrígela a mano en tu plan (la caja es solo una lista de 4 números).
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def mascara_canal(img, tol=28):
    """True donde el píxel parece canal (casi blanco o casi negro y sin color)."""
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    gris = a.mean(axis=2)
    sat = a.max(axis=2) - a.min(axis=2)
    return ((gris > 255 - tol) | (gris < tol)) & (sat < 30)


def cortar(mask, x0, y0, x1, y1, min_lado, prof=0):
    """Divide recursivamente la región por filas/columnas que son canal completo."""
    sub = mask[y0:y1, x0:x1]
    if sub.size == 0:
        return []
    # recortar márgenes de canal
    filas = sub.mean(axis=1) > 0.985
    cols = sub.mean(axis=0) > 0.985
    ys = np.where(~filas)[0]
    xs = np.where(~cols)[0]
    if len(ys) == 0 or len(xs) == 0:
        return []
    y0, y1 = y0 + ys[0], y0 + ys[-1] + 1
    x0, x1 = x0 + xs[0], x0 + xs[-1] + 1
    if prof > 12:
        return [[int(x0), int(y0), int(x1), int(y1)]]
    sub = mask[y0:y1, x0:x1]
    for eje in (0, 1):  # 0: cortes horizontales (filas), 1: verticales (columnas)
        linea = sub.mean(axis=1 - eje) > 0.985
        # buscar tramos de canal de al menos 4 px que no toquen los bordes
        idx = np.where(linea)[0]
        if len(idx) == 0:
            continue
        tramos, ini = [], idx[0]
        for p, q in zip(idx[:-1], idx[1:]):
            if q != p + 1:
                tramos.append((ini, p))
                ini = q
        tramos.append((ini, idx[-1]))
        tramos = [(a, b) for a, b in tramos if b - a >= 3 and a > min_lado // 2 and b < len(linea) - min_lado // 2]
        if not tramos:
            continue
        a, b = max(tramos, key=lambda t: t[1] - t[0])
        if eje == 0:
            return (cortar(mask, x0, y0, x1, y0 + a, min_lado, prof + 1)
                    + cortar(mask, x0, y0 + b + 1, x1, y1, min_lado, prof + 1))
        return (cortar(mask, x0, y0, x0 + a, y1, min_lado, prof + 1)
                + cortar(mask, x0 + b + 1, y0, x1, y1, min_lado, prof + 1))
    return [[int(x0), int(y0), int(x1), int(y1)]]


def detectar(ruta):
    img = Image.open(ruta)
    w, h = img.size
    min_lado = int(min(w, h) * 0.08)
    cajas = cortar(mascara_canal(img), 0, 0, w, h, min_lado)
    cajas = [c for c in cajas if (c[2] - c[0]) >= min_lado and (c[3] - c[1]) >= min_lado]
    if not cajas:
        cajas = [[0, 0, w, h]]
    return img, cajas


def foto_numerada(img, cajas, salida):
    im = img.convert("RGB").copy()
    d = ImageDraw.Draw(im)
    s = max(24, im.width // 18)
    try:
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", s)
    except OSError:
        f = ImageFont.load_default()
    for i, (x0, y0, x1, y1) in enumerate(cajas):
        d.rectangle([x0, y0, x1, y1], outline=(255, 0, 80), width=max(3, s // 8))
        d.rectangle([x0, y0, x0 + s * 1.6, y0 + s * 1.3], fill=(255, 0, 80))
        d.text((x0 + s * 0.25, y0 + s * 0.1), str(i), fill="white", font=f)
    im.thumbnail((900, 900))
    im.save(salida, quality=85)


def main(rutas):
    os.makedirs("salida/paneles", exist_ok=True)
    res = {}
    for r in rutas:
        img, cajas = detectar(r)
        res[r] = cajas
        nombre = os.path.splitext(os.path.basename(r))[0]
        foto_numerada(img, cajas, f"salida/paneles/{nombre}.jpg")
        print(f"{r}: {len(cajas)} viñetas -> salida/paneles/{nombre}.jpg")
    with open("salida/paneles.json", "w") as fh:
        json.dump(res, fh, indent=1)
    print("Cajas guardadas en salida/paneles.json")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
