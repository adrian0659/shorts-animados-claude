"""Saca las páginas de un cómic (.cbr, .cbz, .pdf, carpeta de imágenes o enlace de Google Drive)
y prepara hojas de revisión con cuadrícula de coordenadas.

Uso:  python3 extraer_paginas.py ENTRADA CARPETA_SALIDA
Crea:
  CARPETA_SALIDA/paginas/pagina_000.jpg ...  (en orden; el número es el que va en plan.json)
  CARPETA_SALIDA/revision/hoja_general.jpg   (todas las páginas en miniatura con su número)
  CARPETA_SALIDA/revision/cuadricula_000.jpg (cada página con líneas cada 200 px y sus coordenadas)
Necesita: unar (para .cbr: apt-get install unar / brew install unar), pdftoppm (para .pdf), Pillow.
"""
import sys, os, re, glob, shutil, subprocess, zipfile, tempfile, urllib.request
from PIL import Image, ImageDraw, ImageFont

ent, sal = sys.argv[1], sys.argv[2]
pag_dir = os.path.join(sal, "paginas"); rev_dir = os.path.join(sal, "revision")
os.makedirs(pag_dir, exist_ok=True); os.makedirs(rev_dir, exist_ok=True)
tmp = tempfile.mkdtemp()

m = re.search(r"drive\.google\.com/(?:file/d/|open\?id=)([\w-]+)", ent)
if m:
    dest = os.path.join(tmp, "descarga")
    url = f"https://drive.usercontent.google.com/download?id={m.group(1)}&export=download&confirm=t"
    subprocess.run(["curl", "-sSL", "-o", dest, url], check=True)
    ent = dest

def tipo(p):
    if os.path.isdir(p): return "dir"
    head = open(p, "rb").read(8)
    if head.startswith(b"Rar!"): return "rar"
    if head.startswith(b"PK"): return "zip"
    if head.startswith(b"%PDF"): return "pdf"
    if head.startswith(b"7z"): return "rar"
    raise SystemExit(f"No reconozco el formato de {p}")

t = tipo(ent); src = os.path.join(tmp, "x"); os.makedirs(src)
if t == "rar":
    subprocess.run(["unar", "-q", "-f", "-o", src, ent], check=True)
elif t == "zip":
    zipfile.ZipFile(ent).extractall(src)
elif t == "pdf":
    subprocess.run(["pdftoppm", "-r", "200", "-jpeg", ent, os.path.join(src, "p")], check=True)
else:
    src = ent

imgs = sorted(f for f in glob.glob(os.path.join(src, "**", "*"), recursive=True)
              if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
# descartar marcas de agua / créditos sueltos de los scans (archivos que empiezan con z)
imgs = [f for f in imgs if not os.path.basename(f).lower().startswith("z")] or imgs
for old in glob.glob(os.path.join(pag_dir, "pagina_*.jpg")): os.remove(old)
try: font = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
except OSError: font = ImageFont.load_default()
minis = []
for i, f in enumerate(imgs):
    im = Image.open(f).convert("RGB")
    # capturas de pantalla del celular: quitar las franjas negras de arriba/abajo/lados
    import numpy as np
    g8 = np.asarray(im.convert("L"))
    filas = np.where(g8.mean(1) > 25)[0]; cols = np.where(g8.mean(0) > 25)[0]
    if len(filas) and len(cols):
        im = im.crop((int(cols[0]), int(filas[0]), int(cols[-1]) + 1, int(filas[-1]) + 1))
    im.save(os.path.join(pag_dir, f"pagina_{i:03d}.jpg"), quality=95)
    # cuadrícula: líneas cada 200 px con la coordenada escrita
    g = im.copy(); d = ImageDraw.Draw(g)
    for x in range(0, im.width, 200):
        d.line([(x, 0), (x, im.height)], fill=(255, 0, 255) if x % 1000 == 0 else (0, 255, 255), width=3)
        d.text((x + 6, 6), str(x), fill=(255, 0, 255), font=font, stroke_width=3, stroke_fill=(0, 0, 0))
    for y in range(0, im.height, 200):
        d.line([(0, y), (im.width, y)], fill=(255, 0, 255) if y % 1000 == 0 else (0, 255, 255), width=3)
        d.text((6, y + 6), str(y), fill=(255, 0, 255), font=font, stroke_width=3, stroke_fill=(0, 0, 0))
    g.thumbnail((1300 if im.width > im.height else 900, 1300))
    g.save(os.path.join(rev_dir, f"cuadricula_{i:03d}.jpg"), quality=85)
    mi = im.copy(); mi.thumbnail((300 * (2 if im.width > im.height else 1), 460))
    dm = ImageDraw.Draw(mi); dm.text((8, 8), str(i), fill=(255, 255, 0), font=font, stroke_width=4, stroke_fill=(0, 0, 0))
    minis.append(mi)
# hoja general
cols = 8; cw, ch = 300, 460
rows = []; fila = []; ancho = 0
for mi in minis:
    if ancho + mi.width > cols * cw and fila: rows.append(fila); fila = []; ancho = 0
    fila.append(mi); ancho += mi.width
if fila: rows.append(fila)
hoja = Image.new("RGB", (cols * cw, len(rows) * ch), (20, 20, 20))
for r, fila in enumerate(rows):
    x = 0
    for mi in fila: hoja.paste(mi, (x, r * ch)); x += mi.width
hoja.save(os.path.join(rev_dir, "hoja_general.jpg"), quality=85)
print(f"{len(imgs)} páginas en {pag_dir}")
for i, f in enumerate(imgs):
    w, h = Image.open(os.path.join(pag_dir, f"pagina_{i:03d}.jpg")).size
    print(f"  {i:3d}  {w}x{h}  {os.path.basename(f)}")
shutil.rmtree(tmp, ignore_errors=True)
