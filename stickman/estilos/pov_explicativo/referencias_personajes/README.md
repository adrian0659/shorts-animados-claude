# Referencias de personajes (monigotes con ropa de oficio)

Imágenes de referencia del usuario (noviembre 2026), guardadas para copiar este estilo de personaje.

| Archivo | Qué es |
|---|---|
| `hoja_A_oficios_fondo_blanco.jpg` | 30 oficios sobre fondo blanco (con nombre abajo) |
| `hoja_B_oficios_con_fondo.jpg` | 30 oficios con escenario de color (número arriba) |
| `hoja_C_30_carreras.jpg` | «30 different careers», cada uno en su escenario |
| `mecanico_y_cliente.jpg`, `taller_escena.jpg` | Escena del taller (el look de video que se busca) |
| `hd/hoja_A/`, `hd/hoja_B/`, `hd/hoja_C/` | **Cada personaje ampliado y aclarado (~1030x1430 px)**: `NN_oficio.jpg` |
| `hd/hoja_A/*_recorte.png` | Personajes de la hoja A en HD **con fondo transparente**, listos para cualquier escenario |
| `ampliar.py` | Amplía x8 y limpia (Real-ESRGAN anime 6B + Lanczos + niveles/enfoque) y hace los recortes |
| `recortar.py` | Coordenadas de cada viñeta y función de quitar fondo (la usa `ampliar.py`) |
| `muestra_antes_despues.png`, `muestra_vertical_hd.jpg` | Comparación y prueba sobre un cuadro vertical 1080x1920 |

Oficios disponibles (A): chef, bombero, doctor, policía, científica, construcción, artista, astronauta, maestra, granjero,
músico, piloto, empresario, atleta, juez, panadera, detective, cartero, carpintero, marinero, enfermera, electricista,
fotógrafo, buzo, barbero, soldado, jardinero, salvavidas, mago, programador.
Extra en B y C: futbolista, capitán, plomero, oficinista, mesero, azafata, **mecánico**, veterinario, boxeador,
repartidor, arqueólogo.

## Rasgos del estilo (para imitarlo con código o pedirlo a una IA)
- Cabeza blanca grande y redonda (≈ 1/4 de la altura), contorno negro grueso; ojos de punto ovalados, cejas cortas
  y gruesas, boca de una línea o sonrisa pequeña; a veces lengua de fuera, bigote o lentes.
- Sin nariz ni orejas. Pelo o sombrero/casco/gorra del oficio encima de la cabeza (muy característico de cada oficio).
- Cuerpo: la **ropa del oficio forma el torso** (bata, uniforme, chaleco, overol, traje) con cuello, botones,
  bolsillos, insignias y cinturón; brazos y piernas de **palito negro** (o con manga/pantalón cuando la ropa los cubre).
- Manos blancas redondas de caricatura; zapatos/botas negros grandes.
- Siempre sostienen el objeto de su oficio (batidor, manguera, portapapeles, matraz, martillo, paleta...).
- Línea de tinta uniforme, colores planos con sombra suave, sin texturas fuertes.

## Cómo se usan en un video
1. Elegir el recorte (`hoja_A/NN_oficio_recorte.png`) o pedir uno nuevo con la misma pose sobre fondo blanco.
2. Ponerlo sobre un escenario de `escenarios.py` como capa de imagen, con zoom lento, un poco de balanceo y
   etiquetas/insertos del motor.
3. Resolución: cada personaje HD mide ≈ 1030x1430 px, suficiente para ocupar todo el ancho de un video vertical
   1080x1920. Al ampliar con IA se pierde algo de textura fina, pero la línea queda limpia y los blancos puros.
   Para regenerarlos: bajar `RealESRGAN_x4plus_anime_6B.pth` (Hugging Face, ximso/RealESRGAN_x4plus_anime_6B) y
   correr `python3 ampliar.py --modelo ruta.pth` (≈ 3 min en CPU para los 90).
