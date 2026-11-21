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

## Personaje con volumen, estilo «boceto» (`personaje.py`)
Segundo modelo de personaje, basado en una hoja de giro de referencia: cabeza blanca grande, ropa con
volumen, contorno dibujado a mano que «hierve», sombra rayada, grano de papel y fondo sepia sucio.
Se puede ver **desde cualquier ángulo** (`giro`: 0 frente, 90 perfil, 180 espalda) y girar de forma continua.

```
python3 ejemplos/doctor.py --hoja   # hoja con 5 vistas -> salida/doctor_hoja.png
python3 ejemplos/doctor.py          # video de 9 s: gira 360°, mira preocupado, sale caminando
```

- `Personaje(estilo).dibujar(ctx, t, x, suelo, escala, giro, cara, mira, paso, brazos)`
  - `cara`: `preocupado, enojado, neutral, sorpresa, feliz` · `mira`: -1..1 · `paso`: fase de caminata o `None`
  - `brazos`: `{"i": (adelante, afuera, codo), "d": (...)}` en grados
- Estilo: copia `DOCTOR` y cambia colores o quita `con_gorro`, `con_mascarilla` (sin mascarilla se dibuja la boca).
- Fondo y acabado: `Lienzo(W, H, fondo_grunge(W, H))` → `ctx = lienzo.nuevo()` → dibujar → `lienzo.rgb(t)`.
- `ejemplos/taller.py` es el estilo anterior (plano y limpio, tipo caricatura) por si lo prefieres.
