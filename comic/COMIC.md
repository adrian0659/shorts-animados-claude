# Shorts explicativos de cómics (narrador + viñetas)

Videos verticales de 45–75 s que cuentan un dato o una historia de los cómics con **voz narradora**, **viñetas reales
del cómic** que se acercan y se mueven al ritmo de la voz, y **subtítulos karaoke**. Todo el montaje lo hace
`comic/montar_comic.py`.

## Fórmula del guion (150–190 palabras para ~60 s)
1. **Gancho (0–3 s):** el dato raro en una frase, sin saludo. «En su primer cómic, Hulk no era verde. Era gris.»
2. **Contexto (3–12 s):** año, autores, número del cómic. Da credibilidad: «Mayo de 1962. Stan Lee y Jack Kirby…»
3. **La historia (12–40 s):** qué pasó, en 3 o 4 pasos, cada uno con su viñeta.
4. **El giro (40–55 s):** lo que casi nadie sabe, o la consecuencia hasta hoy.
5. **Remate (últimos 5 s):** una frase corta que resume y deja pensando. El video termina en la última palabra.

Reglas:
- Cada dato con su fuente (número del cómic, año, autor) arriba del `GUION.md`. Si no estás seguro de un dato, no va.
- Una idea por viñeta; cambia de imagen cada 2–4 s.
- No describas con la voz lo que ya se ve («aquí vemos a Hulk…»): cuenta lo que la imagen no dice.
- Ritmo de narración: 3–3.4 palabras por segundo.

## Derechos: cómo usar viñetas sin meterte en problemas
Los personajes y las páginas son de Marvel/Disney. Los canales de este tipo trabajan bajo **uso legítimo / fair use**
(comentario y análisis). Lo que reduce el riesgo:
- **Comenta y explica sobre la imagen**; nunca subas páginas seguidas para que se lea el cómic.
- **Fragmentos cortos:** 2–4 s por viñeta, con zoom o recorte (no la página completa mucho tiempo).
- **Nada de escenas de películas o series**: Content ID las detecta.
- **No uses los logos de Marvel** como marca de tu canal ni en la miniatura como si fuera oficial.
- **Cita el cómic** en la descripción (título, número, año, autores).
- Consigue las páginas de forma legal: tus propios cómics (foto o escaneo), compras digitales o Marvel Unlimited.
  No descargues escaneos piratas.

Esto no es asesoría legal; es lo que suelen hacer los canales de análisis de cómics.

## Paso a paso
1. **Tema y datos.** Escribe `GUION.md` con las fuentes arriba y el texto de la narración.
2. **Voz.** Graba tu voz o genérala (ElevenLabs u otra) y guárdala como `voz.mp3` en la carpeta del proyecto.
3. **Páginas.** Pon las páginas o viñetas en `paginas/` (jpg o png, la mejor resolución que tengas).
4. **Cuadrícula.** `python3 comic/montar_comic.py PROYECTO --cuadricula` saca cada página con líneas al 10 %
   en `_cuadricula/` para medir los rectángulos fácilmente.
5. **Escenas.** En `escenas.json`, una escena por viñeta:
   - `imagen`: qué página.
   - `empieza`: las primeras 2–4 palabras de la frase donde entra (la primera escena no lo necesita).
   - `de` y `a`: rectángulo inicial y final `[x, y, ancho, alto]` de 0 a 1. Con los dos iguales, la cámara se
     queda quieta; si cambian, hace zoom o paneo suave. Sin `a`, hace un acercamiento lento.
   - Patrones que funcionan: **página completa → viñeta** (para presentar), **viñeta → cara** (para el momento
     fuerte), **viñeta izquierda → derecha** (para un antes y después).
6. **Monta:** `python3 comic/montar_comic.py PROYECTO` → `final.mp4`.
   Si Whisper escribe mal una palabra (nombres como «Kirby» o «Fixit»), corrígela en `palabras.json` y vuelve a
   correr. Opcional: `--musica musica.mp3`.

Instalación: Python 3, ffmpeg y `pip install faster-whisper numpy pillow`.

## Ideas de temas
- ¿Por qué Hulk era gris en su primer cómic? (ejemplo en `ejemplos/hulk_gris/`)
- El trato de Spider-Man con Mefisto que borró su matrimonio (*One More Day*, 2007)
- Los personajes que han levantado el martillo de Thor
- Cuando Wolverine tenía garras de hueso y nadie lo sabía
- El primer cómic de Deadpool: era un villano (*The New Mutants* #98, 1991)
- La muerte del Capitán Marvel (1982): el cómic sobre el cáncer
