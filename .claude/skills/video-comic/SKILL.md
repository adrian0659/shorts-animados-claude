---
name: video-comic
description: >-
  Hace un short vertical de «¿Sabías que…?» contando una escena de un cómic, con las viñetas del propio cómic
  (.cbr, .cbz, .pdf o enlace de Google Drive), narración con la voz «Cómics» de ElevenLabs, cámara que recorre
  la página, barridos entre páginas, música de suspenso y efectos. Úsala cuando pidan un video de cómic como
  el de Venom o el de Doom vs Thanos, o escriban /video-comic.
argument-hint: "[tema o escena] [enlace o archivo del cómic]"
---

# Video de cómic «¿Sabías que…?»

Formato probado en `videos/doom_thanos/` («¿Sabías que el Doctor Doom eliminó a Thanos?», Secret Wars #8):
vertical 1080×1920, 30 fps, ~60 s, una voz narrando de corrido, la cámara recorriendo las páginas del cómic.
Habla siempre en español sencillo con la persona. Una pregunta a la vez solo si falta algo imprescindible.

Herramientas (en `.claude/skills/video-comic/scripts/`, llámalas con su ruta completa):
- `extraer_paginas.py ENTRADA CARPETA` → páginas numeradas + hojas de revisión con cuadrícula de coordenadas.
- `palabras.py VOZ.mp3 palabras.json` → tiempos por palabra (Whisper local).
- `render.py plan.json --fotos` → una foto por toma para revisar encuadres (segundos).
- `render.py plan.json` → MP4 final con voz, música y efectos (~2 min por minuto de video).
Requisitos: `ffmpeg`, `unar` (para .cbr), `pdftoppm` (para .pdf), `pip install pillow numpy faster-whisper`.
Si falta algo, instálalo (apt-get install -y unar / pip install …) y avisa en una línea.

## Proceso (hazlo de corrido; solo detente donde dice «espera»)

1. **Carpeta del proyecto**: `videos/<tema_corto>/` (p. ej. `videos/hulk_vs_thor/`). Ahí va todo.

2. **Cómic.** Si la persona ya dio enlace o archivo en `$ARGUMENTS` o en el chat, úsalo; si no, pídeselo
   (acepta .cbr, .cbz, .pdf, carpeta de imágenes o enlace de Google Drive compartido «cualquiera con el enlace»).
   `python3 …/extraer_paginas.py ENTRADA videos/<tema>/comic`
   Mira `comic/revision/hoja_general.jpg` para ubicar la escena y luego las `cuadricula_XXX.jpg` de esas páginas.

3. **Guion fiel al cómic — LEE LAS PÁGINAS ANTES DE ESCRIBIR.** En el video de Doom el primer guion salió de memoria
   y tenía dos errores (lugar del encuentro y lo que se dijeron). Los fans lo notan en los comentarios.
   Escribe lo que realmente pasa y se dice en las viñetas, traducido. Si algo del contexto no está en este número
   (p. ej. cómo empezó todo), dilo de forma general o verifica la fuente.
   Fórmula (igual que el video de referencia de Venom):
   - **Gancho** en una frase: «¿Sabías que [personaje] [hizo algo impactante]?» = el título.
   - Contexto en 1–2 frases (número y año del cómic, situación).
   - La escena paso a paso, una frase por viñeta, cada vez más tensa. Usa las frases reales de los globos.
   - **El momento** (el golpe, la traición, la muerte).
   - **Remate** corto y frío al final. El video termina en la última palabra.
   - 150–180 palabras ≈ 55–60 s. Sin describir lo que ya se ve; cuenta lo que significa.
   Entrega título, guion, descripción y hashtags. **Espera** a que la persona apruebe o corrija el guion.

4. **Voz** (ElevenLabs, gasta créditos: ~1,100 por toma de 60 s; dilo antes en una línea).
   - Voz por defecto: **«Cómics»** de la persona, `voice_id` `R2HX9H9oWlDgArKTc7Sv` (clonada, español mexicano).
     Confírmala con `creative_list_voices` (search "comics") si falla.
   - Modelo `eleven_v4` con etiquetas de tono al inicio de cada frase, como en el de Doom:
     `[intrigued, fast]` gancho · `[mysterious]` contexto · `[urgent]`/`[epic]` escalada · `[tense]` ·
     `[cold, slow]` amenaza · `[short pause]` · `[intense, building]` antes del golpe · `[dramatic]` ·
     `[ominous, quieter]` · `[whispering, chilling]` remate.
   - Escribe los nombres como se pronuncian bien (Doom salió bien escrito «Doctor Doom»).
   - Genera con el número de tomas por defecto (2), espera con `creative_get_flow_run_status`, descarga ambas con
     curl a la carpeta (`voz_toma1.mp3`, `voz_toma2.mp3`), transcribe las dos con `palabras.py` y elige la que
     pronuncie mejor el gancho y los nombres. Manda las dos a la persona y di cuál usas.

5. **Tiempos**: `python3 …/palabras.py voz_tomaN.mp3 palabras.json`.

6. **Plan de tomas** `plan.json` (ejemplo completo: `videos/doom_thanos/plan.json`; formato al inicio de `render.py`).
   - Una toma cada 1.3–2.5 s, empezando cuando empieza la frase o la palabra clave.
   - Abre con el momento más fuerte (adelanto del clímax) durante el gancho, como la referencia.
   - Encadena viñetas **de la misma página** en tomas seguidas: la cámara se desliza entre ellas (se ve como
     la referencia). Cambiar de página = barrido.
   - `ancho` para que se vea la viñeta completa: ≥ ancho de la viñeta y ≥ alto×9/16. Rostros/miradas: 800–1000.
     Viñeta ancha: 1700–1950 (se ven también las de arriba y abajo, como en la referencia). No cortes globos.
   - Efectos: `golpe` en cortes fuertes, `sacudir` en golpes/explosiones, `flash` en revelaciones, `impacto`
     solo en EL momento (hace silencio tenso antes, golpe fuerte y crujido).
   - Termina en la viñeta más icónica con `golpe`.
   - Los anchos de arriba son para páginas de ~2000 px. Si las páginas miden otra cosa (p. ej. capturas de celular
     de 1284 px), multiplica por ancho_página/2000. Las capturas se recortan solas (franjas negras fuera).
   - **Clip de película** al inicio (si la persona manda uno): toma `{"t":0,"clip":"comic/clip.mov","desde":0}`.
     Se ve a pantalla completa sin su audio; la voz va encima. Ejemplo: `videos/wolverine_crucificado/plan.json`.
   - **Sonidos de escena** (pocos y suaves, la persona los pidió así): `"sonido": ["viento"|"bofetada"|"crujido"|
     "clavos"|"trueno"|"lluvia"|"rugido"]` solo donde la narración lo cuenta (golpe, tormenta, desierto…).

7. **Revisión rápida**: `python3 …/render.py plan.json --fotos` y mira `revision_tomas/hoja_tomas.jpg`
   (y fotos sueltas si dudas). Corrige encuadres que corten globos o caras, o que repitan viñeta.

8. **Render**: `python3 …/render.py plan.json`. Mira `revision_tomas/hoja_video.jpg`. Comprueba con ffprobe que
   tiene video y audio y la duración. Volumen final −14 LUFS (lo hace el script).

9. **Entrega**: manda el MP4 con SendUserFile (display render). Resume en pocas líneas: qué se ve, tiempos clave,
   costo de voz. Commit y push de `plan.json`, voces, `palabras.json` y MP4 (las páginas del cómic NO se suben:
   `comic/` va en `.gitignore`). Recuerda una vez el aviso de derechos: las viñetas son del editor; las
   plataformas pueden silenciar o quitar el video.

## Cambios que la persona pidió en el primer video (ya incluidos en render.py)
- «Movimientos como el video de referencia»: cámara que recorre la página y se desliza de viñeta a viñeta,
  barridos con desenfoque y separación de color entre páginas, acercamiento lento constante, sacudidas.
- «Que se vean más las viñetas sin cortarlas»: ventanas anchas sobre la página completa en vez de recortes.
