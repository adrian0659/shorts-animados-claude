---
name: stickman
description: >-
  Crea un short vertical con el personaje «cabezón» (estilo del usuario: cabeza blanca grande, cejas gruesas,
  extremidades de palito) vestido según la historia, a partir de una historia, guion o audio que dé el usuario.
  Úsala cuando escriban /stickman, pidan un short o video nuevo, o den un audio o una historia para animar.
---

# /stickman — shorts con el personaje cabezón y vestuario según la historia

**Este es el estilo por defecto de los shorts de este usuario.** No ofrezcas Blender, Remotion ni el monigote
clásico salvo que lo pidan. Todo es Python (`stickman/motor.py`): sin IA de video ni servicios de pago.

## 1. Entrada
- **Historia o guion en texto**: úsalo tal cual; si es largo, propón un recorte de 20–60 s y espera el visto bueno.
- **Audio** (`.wav`, `.mp3`, `.m4a`…): es la voz del short y manda en los tiempos.
  - Copia el audio a `stickman/shorts/<nombre>/voz.<ext>` y transcribe con tiempos por palabra:
    `pip install faster-whisper` y `python3 herramientas/transcribir.py shorts/<nombre>/voz.mp3 shorts/<nombre>/`
    (desde `stickman/`). Si el modelo no se puede descargar, pide el texto del audio. Revisa la transcripción:
    corrige palabras mal oídas con `cambios=` en `subtitulos_desde_palabras` (p. ej. «P.O.B.» → «POV»).
  - La duración del short = duración del audio.
- Pregunta solo lo que falte. No pidas claves en el chat.

## 2. Reparto y vestuario (lo más importante)
Haz una tabla corta antes de animar: **personaje → vestuario → por qué** (época, oficio, lugar de la historia), y
muéstrala a la persona junto con el plan de escenas.
- Parte de `VESTUARIOS` en `motor.py`: casual, estudiante, doctor, cientifico, ejecutivo, policia, soldado, rey,
  reina, romano, caballero, griego, vaquero, granjero, obrero, chef, mago, pirata, astronauta, deportista,
  abuelo, abuela, nina. Hoja de referencia: `python3 ejemplos/vestuarios.py` → `salida/vestuarios.png`.
- Ajusta con parámetros: `ropa` (sudadera, camiseta, camisa, uniforme, traje, bata, vestido, tunica, armadura,
  overol, espacial), `color`, `color2`, `pelo` (`CANOSO`, `NEGRO`, `RUBIO`, `PELIRROJO` o RGB), `peinado`
  (picos, corto, largo, chongo, calvo), `sombrero` (gorra, corona, casco_romano, vaquero, casco_obra, chef, mago,
  pirata, policia, burbuja, paja), `accesorios` (lentes, bigote, barba, parche, corbata, estetoscopio, medalla),
  `capa` (color).
- Sé fiel a la época y al lugar: colores y prendas que correspondan (un faraón no lleva traje; un médico de 1800
  no lleva bata moderna). Si nada encaja, combina piezas; si de verdad falta una prenda o un sombrero, agrégalo
  en `Personaje._prenda` o `Personaje._sombrero` con el mismo trazo (contorno `TINTA`, sombra a la izquierda) y
  revísalo en la hoja de vestuarios.
- Distingue a los personajes entre sí por color de ropa y peinado. El narrador o protagonista sin papel en la
  historia usa `casual`.
- Si un personaje cambia de ropa a mitad de la historia, crea otro `Personaje` y alterna su aparición por tramos.

## 3. Construir el short
Parte de `stickman/shorts/avion_presidencial.py` (ejemplo completo con voz: 16 escenas, globos de diálogo, boca
sincronizada, subtítulos con tiempos exactos y mezcla normalizada). Cópialo a `stickman/shorts/<nombre>.py`:
```python
narrador = Personaje(claves, escala=2.2, vestuario="cientifico", habla="voz.wav")
rey = Personaje(claves_rey, escala=2.0, vestuario="rey", pelo=CANOSO)
```
- `habla="voz.wav"` mueve la boca con la voz. Si hay varios personajes, pásale a cada uno la lista de tramos en
  que habla: `habla=[(0.0, 3.2), (7.5, 9.0)]`.
- Poses: parado, saludo, señalar_d, señalar_i, sorpresa, pensar, encoger, festejar, triste, jarras.
  Caras: feliz, picaro, sorpresa, triste, serio, pensar, enojado. Cada reacción cae 0–3 cuadros antes de su palabra.
- Escenas con `Tramo(t0, t1, capas...)`: una por idea del guion, cortando en el inicio de su frase. Fondos con
  `Dibujo(f)`; en la cabina o detrás de un mostrador, un primer plano tapa las piernas y parecen sentados.
- Objetos en la mano con la clave `lleva=` (`sobre()`, `pistola()`, `telefono()`…) y nervios con `temblar=True`.
- Utilería lista: `avion`, `telefono`, `sobre`, `documento`, `burbuja_dialogo`, `reloj_digital`, `alerta`, `pistola`,
  `cielo_noche`, `corazon`, `gota`, `texto`. Si falta algo, dibújalo con formas simples y `contorno()`.
- Subtítulos con `subtitulos_desde_palabras(palabras, resaltar={...})` (tiempos exactos de la transcripción).
  Cuando una cita va en globo de diálogo, quita los subtítulos de ese tramo para no repetir el texto.
- Fondo, utilería (`Elemento`), sacudidas y zoom como en el ejemplo; efectos de `sonido.py`. La voz va al frente y
  la música y los efectos de 5 a 10 dB por debajo.

## 4. Revisar y entregar
1. Fotos de revisión de cada escena (`short.foto(t, ruta)`) y míralas antes del render: ropa correcta, nada
   tapando caras, personajes dentro del cuadro.
2. Render: `short.render("salida/<nombre>.mp4", audio=...)` (1080x1920, 30 fps; ~1 min por minuto de video).
   Normaliza la mezcla a −14 LUFS con `loudnorm` antes del render (como en el ejemplo del avión).
3. Comprueba con `ffprobe` que el MP4 tiene imagen y audio y la duración correcta. Si algo falla, dilo; no lo
   anuncies como terminado.
4. Entrega el MP4 y la tabla de vestuario. Pregunta qué ajustar.
