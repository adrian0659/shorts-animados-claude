# Shorts estilo stickman (monigotes)

Tercer estilo del paquete: monigotes dibujados con código para **historias y datos curiosos**.
Todo es Python: sin Blender, sin Remotion, sin IA de video. Un short de 26 s se renderiza en ~15 s.

Ejemplo: [video del pulpo](../ejemplos/video-stickman-pulpo.mp4) · [hoja de fotos](../ejemplos/stickman-pulpo-hoja.png)

## Instalar
```
pip install pycairo numpy pillow
```
Además necesitas `ffmpeg` (en Mac: `brew install ffmpeg`; en Windows: `winget install ffmpeg`).

## Usar
```
cd stickman
python3 ejemplos/pulpo.py --fotos   # fotos de revisión en salida/
python3 ejemplos/pulpo.py           # video final: salida/pulpo.mp4
```

## Cómo se arma un short (copia `ejemplos/pulpo.py` y cambia)
- **Guion**: lista de `(inicio, fin, "texto")`. Las palabras entre `*asteriscos*` salen en amarillo.
- **Monigote**: fotogramas clave con `t`, `pose`, `x`, `cara`, `caminar`, `saltar`, `mira`.
  - Poses: `parado, saludo, señalar_d, señalar_i, sorpresa, pensar, encoger, festejar, triste`.
  - Caras: `feliz, sorpresa, triste, serio, pensar`.
  - Puedes agregar poses nuevas en `POSES` de `motor.py` (ángulos: 0 = abajo, 90 = derecha, 180 = arriba).
- **Elementos** (`Elemento(dibujo, t0, t1, x, y, escala)`): aparecen con un "pop". Incluidos: `corazon`,
  `texto`, `burbuja_pensamiento`, `gota`, `pulpo`, `burbujas_agua`. Para un dato nuevo, dibuja tu objeto
  con formas simples (círculos, curvas) y `contorno()`.
- **Cámara**: `short.sacudir(t)` y `short.zoom(t0, t1, escala, cx, cy)`.
- **Sonido** (`sonido.py`): `pop, whoosh, ding, latido, boing, tada, musica`, todo sintetizado y libre de derechos.

## Voz
El ejemplo usa texto en pantalla, sin narración. Para agregar voz, graba o genera un audio y mézclalo con
`Mezcla.poner(0, audio)`; ajusta los tiempos del guion a la voz.

## Estilo ilustrado (personajes con ropa)
`ilustrado.py` agrega un segundo look: cabeza grande blanca con contorno grueso, pelo con forma, ojos de punto,
cejas expresivas, ropa de color (camisa, playera, vestido, corbata, gafete), guantes blancos y zapatos negros,
con escenarios sombreados (`Taller`, `Auto`) y tarjetas de dato (`Cartel`).

```
python3 ejemplos/taller_prueba.py   # salida/taller_prueba.png
python3 ejemplos/elenco_prueba.py   # peinados, ropa, caras y poses
```
- `Persona(claves, pelo=..., color_pelo=..., ropa=dict(...))`: mismas claves que `Monigote` más `mano_d` / `mano_i`
  (`telefono`, `tablet`, `llave`, `billete`).
- Peinados: `puntas, raya, corto, largo, coleta, calvo`. Caras: `serio, feliz, sorpresa, triste, pensar, enojado, preocupado`.
- Poses nuevas: `telefono, entregar, recibir_i, manos_frente, brazos_cruzados, explicar, cabeza_mano`.
