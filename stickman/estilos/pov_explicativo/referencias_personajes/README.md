# Referencias de personajes (monigotes con ropa de oficio)

Imágenes de referencia del usuario (noviembre 2026), guardadas para copiar este estilo de personaje.

| Archivo | Qué es |
|---|---|
| `hoja_A_oficios_fondo_blanco.jpg` | 30 oficios sobre fondo blanco (con nombre abajo) |
| `hoja_B_oficios_con_fondo.jpg` | 30 oficios con escenario de color (número arriba) |
| `hoja_C_30_carreras.jpg` | «30 different careers», cada uno en su escenario |
| `mecanico_y_cliente.jpg`, `taller_escena.jpg` | Escena del taller (el look de video que se busca) |
| `hoja_A/`, `hoja_B/`, `hoja_C/` | Cada personaje por separado, al doble de tamaño (`NN_oficio.png`) |
| `hoja_A/*_recorte.png` | Personajes de la hoja A **con fondo transparente**, listos para poner sobre cualquier escenario |
| `recortar.py` | Vuelve a generar los cortes y recortes |

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
3. Resolución: cada recorte mide ≈ 270x370 px (las hojas originales son de 768x1376). Sirve para planos medios;
   para primeros planos o pantalla completa conviene la imagen original en alta resolución.
