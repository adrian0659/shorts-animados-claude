"""Corta las 3 hojas de referencia en una imagen por personaje (x2 de tamaño) y hace recortes con fondo
transparente de la hoja A (fondo blanco).  Ejecutar desde esta carpeta:  python3 recortar.py"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage

AQUI = os.path.dirname(os.path.abspath(__file__))
HOJAS = {
    "A": dict(archivo="hoja_A_oficios_fondo_blanco.jpg",
              cols=[(19, 155), (170, 306), (321, 456), (470, 605), (620, 755)],
              filas=[(20, 205), (250, 436), (481, 666), (711, 896), (936, 1121), (1159, 1343)], arriba=0,
              nombres="chef bombero doctor policia cientifica construccion artista astronauta maestra granjero musico piloto "
                      "empresario atleta juez panadera detective cartero carpintero marinero enfermera electricista fotografo "
                      "buzo barbero soldado jardinero salvavidas mago programador"),
    "B": dict(archivo="hoja_B_oficios_con_fondo.jpg",
              cols=[(2, 149), (157, 304), (312, 459), (467, 612), (621, 766)],
              filas=[(6, 217), (224, 450), (459, 684), (691, 916), (923, 1147), (1155, 1370)], arriba=0,
              nombres="bombero doctor chef astronauta policia maestra construccion artista cientifico piloto futbolista musico "
                      "panadero detective granjero juez cartero buzo electricista enfermera jardinero salvavidas capitan plomero "
                      "oficinista mesero fotografo azafata mecanico veterinario"),
    "C": dict(archivo="hoja_C_30_carreras.jpg",
              cols=[(9, 142), (156, 303), (311, 459), (466, 613), (621, 767)],
              filas=[(60, 268), (276, 484), (492, 700), (707, 928), (936, 1158), (1165, 1371)], arriba=26,
              nombres="astronauta chef doctor bombero policia construccion artista granjero cientifico atleta piloto musico "
                      "maestro detective buzo panadero oficinista mesero mecanico fotografo jardinero juez boxeador repartidor "
                      "mago barbero salvavidas veterinario azafata arqueologo"),
}


def sin_fondo(im):
    """Quita el blanco que toca el borde (fondo) y deja al personaje con transparencia."""
    a = np.asarray(im.convert("RGB"), np.int16)
    blanco = (a.min(axis=2) > 225) & (np.ptp(a, axis=2) < 25)
    lab, n = ndimage.label(blanco)
    borde = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    fondo = np.isin(lab, list(borde))
    fondo = ndimage.binary_opening(fondo, iterations=1)
    alfa = np.where(fondo, 0, 255).astype(np.uint8)
    alfa = np.asarray(Image.fromarray(alfa).filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(0.8)))
    rgba = np.dstack([a.astype(np.uint8), alfa])
    return Image.fromarray(rgba, "RGBA")


if __name__ == "__main__":
    for clave, h in HOJAS.items():
        im = Image.open(os.path.join(AQUI, h["archivo"])).convert("RGB")
        nombres = h["nombres"].split()
        out = os.path.join(AQUI, f"hoja_{clave}"); os.makedirs(out, exist_ok=True)
        i = 0
        for (y0, y1) in h["filas"]:
            for (x0, x1) in h["cols"]:
                p = im.crop((x0 + 4, y0 + 4 + h["arriba"], x1 - 4, y1 - 4))
                p = p.resize((p.width * 2, p.height * 2), Image.LANCZOS)
                nom = f"{i + 1:02d}_{nombres[i]}"
                p.save(os.path.join(out, nom + ".png"))
                if clave == "A":
                    sin_fondo(p).save(os.path.join(out, nom + "_recorte.png"))
                i += 1
        print(clave, i, "personajes")
