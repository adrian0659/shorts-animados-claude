# Dramas cortos con animales realistas (estilo «karma»)

Shorts verticales de 60–80 s donde **animales fotorrealistas con cuerpo humano** (perros, gatos, osos…) actúan un
drama de oficina, restaurante o barrio con **diálogo** y **subtítulos karaoke**. Las imágenes y voces se generan con
IA; este paquete pone la fórmula de la historia, los prompts y el montaje final (`montar.py`).

## Lo que se midió del video de referencia (75 s)
| Qué | Valor |
|---|---|
| Formato | 1080x1920, vertical |
| Tomas | ~30, una frase por toma, **corte cada 2.3–2.6 s** (algunas de 5 s con dos frases) |
| Movimiento | clips de video de IA: los personajes mueven cabeza, manos y boca; cámara casi fija |
| Voz | diálogo actuado, una voz distinta por personaje, español latino coloquial («wey», «parce», «patrón») |
| Narrador | ninguno: la historia avanza solo con diálogos |
| Subtítulos | 1–3 palabras, MAYÚSCULAS, letra condensada gruesa, blanco con contorno negro, **palabra activa en cian**, a ~78 % de altura |
| Look | fotorrealista, luz cálida de tungsteno, fondo desenfocado, lugares de lujo contra lugares humildes |
| Música | ninguna o casi inaudible |

## La fórmula de la historia (karma en 4 actos)
1. **La petición (0–10 s).** Los buenos piden algo justo (aumento, crédito, respeto). El poderoso se burla:
   «Hay muchos que pueden hacer lo mismo». Sin introducción: el video empieza en la discusión.
2. **La prueba (10–30 s).** Vemos que los buenos son la razón del éxito: clientes felices, lugar lleno, elogios
   directos («¿Ustedes cocinaron esto?»). El poderoso lo ve y aun así no cede.
3. **La traición (30–47 s).** El poderoso los reemplaza por gente más barata y los despide en su cara.
   Línea clave del villano, corta y fría («Si cobran menos, me sirven más»).
4. **La caída y el triunfo (47–75 s).** Todo se cae: quejas, platos devueltos, clientes que se van preguntando por
   los de antes. Corte a los buenos empezando algo humilde pero propio. **El video termina en su frase final**
   («Y todo lo que ganemos será de nosotros»), sin cierre ni moraleja dicha.

Reglas:
- Una frase por toma, de 5 a 10 palabras (cabe en 2.5 s). Nunca dos personajes hablando en el mismo clip.
- Cada personaje tiene una muletilla fija que lo identifica.
- Nombres humanos para los personajes («Señor Richard», «Diego»): hace que se sienta telenovela.
- Los villanos no son caricaturas: hablan tranquilos, con desprecio.
- Un objeto que lo dice todo en cada acto (máquina de contar billetes, currículums con precio, el plato devuelto,
  la libreta con el plan del puesto).

## Producción paso a paso
1. **Historia.** Elige una idea (abajo hay 10) y escribe `GUION.md` con la tabla de tomas: número, personaje,
   frase, lugar, acción y encuadre. Usa `ejemplos/la_receta/GUION.md` como plantilla.
2. **Biblia de personajes.** Un bloque fijo por personaje (raza, pelaje, ropa, accesorios) que se pega **igual,
   palabra por palabra**, en cada prompt. Es lo que hace que el personaje no cambie entre tomas.
3. **Imágenes de referencia.** Genera primero un retrato de cuerpo medio de cada personaje y una imagen de cada
   lugar. Elige la mejor y úsala como referencia («ingredientes» o «imagen a video») en todas sus tomas.
4. **Clips.** Genera cada toma como video de 8 s **con audio** en un modelo que haga voz con labios sincronizados
   (Veo 3 en Google Flow / Gemini, Kling con lip-sync, etc.). Prompt por toma = plantilla de abajo.
   - Sin modelo con voz: genera imágenes, crea la voz de cada frase aparte (ElevenLabs u otra) y pon
     `05.png + 05.mp3`; `montar.py` las anima con un zoom lento.
5. **Recorta cada clip** a solo la frase (≈2.5 s): quita el silencio del inicio y del final. Guárdalos en
   `tomas/01.mp4, 02.mp4…` en orden.
6. **Monta:** `python3 drama/montar.py ruta/del/proyecto` → `final.mp4` con subtítulos.
   Si Whisper escribe mal una palabra («Parse» en vez de «parce»), corrígela en `palabras.json` y vuelve a correr.
   Opcional: `--musica musica.mp3` (queda 18 dB por debajo de las voces).
7. **Revisa** que cada subtítulo caiga con su voz y que ningún personaje cambie de cara o de ropa entre tomas.

Instalación del montaje: Python 3, ffmpeg y `pip install faster-whisper numpy`. La letra (Barlow Condensed,
licencia OFL) viene en `drama/fuentes/`.

## Plantilla de prompt por toma (video con voz)
```
Photorealistic cinematic vertical 9:16 video. [BLOQUE DEL PERSONAJE QUE HABLA, IDÉNTICO CADA VEZ].
[Otros personajes visibles, con su bloque corto]. Location: [LUGAR, idéntico en todas sus tomas].
Action: [qué hace mientras habla, un solo gesto]. Camera: [medium shot / close-up / over-the-shoulder], static
with a very slow push-in, eye level, 35mm, shallow depth of field.
He speaks in Mexican Spanish, [tono: calm and arrogant / frustrated / grateful], lips synced:
"[FRASE EXACTA]"
Warm tungsten practical lights, realistic fur detail, natural skin-tone human hands.
Only this character speaks. No music, no subtitles, no on-screen text, no watermark.
```
Para imágenes fijas, la misma plantilla sin la parte de voz, y agrega `hyperrealistic photograph, 8k`.

Consejos que evitan repetir generaciones:
- Escribe la frase **entre comillas y exacta**; si es larga, el modelo la corta o la acelera.
- «Only this character speaks»: si no, los demás también mueven la boca.
- Pide manos humanas («natural human hands»): las patas en lugar de manos se ven raras con ropa.
- Mismo lugar = misma descripción y misma hora del día en todas sus tomas.
- Letreros con texto (RESTAURANTE, nombres) salen mejor en la imagen de referencia que en el video.

## 10 ideas listas para escribir
1. **La receta** — la panadera crea el pan que hizo famosa la panadería; el dueño la corre y se queda con «la receta»,
   pero el pan nunca vuelve a salir igual. (Ejemplo completo en `ejemplos/la_receta/`).
2. **El mecánico** — el taller despide al mecánico viejo por «lento»; los clientes de siempre lo siguen a su cochera.
3. **La señora de la limpieza** — el gerente la humilla frente a todos; ella es la dueña que vino de incógnito.
4. **El hijo consentido** — el papá deja la empresa al hijo flojo y no al trabajador; en un año la quiebra.
5. **El mesero honrado** — devuelve una cartera llena; el dueño lo regaña por «perder tiempo»; el dueño de la
   cartera era el inversionista que estaba por comprar el lugar.
6. **La renta** — el casero sube la renta al puesto de tacos que llenó la calle; se mudan enfrente y la calle los sigue.
7. **El chofer** — el jefe se burla del chofer que estudia de noche; años después el chofer lo entrevista.
8. **La costurera** — la tienda de lujo vende sus vestidos como propios; ella abre su marca en redes.
9. **El portero** — no deja entrar a un cliente mal vestido; era quien iba a pagar la fiesta de 500 personas.
10. **El pastel de la abuela** — el chef famoso se burla de la abuela en un concurso; ella gana con su receta de casa.

## Qué no hacer
- No copies historias, nombres ni personajes de videos de otros canales: usa la fórmula, no el contenido.
- No uses marcas, logos ni personas reales.
- Los videos de referencia son solo para estudiar el estilo; no los subas ni los reutilices.
