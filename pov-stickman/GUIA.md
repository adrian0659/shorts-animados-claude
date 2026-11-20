# Videos «POV: Eres el creador de…» con monito stickman

Kit para hacer videos explicativos narrados en segunda persona, con un monito de cabeza
redonda dibujado a tinta sobre papel beige, como el video de referencia
(«POV: Eres el Creador de los Narcotanques de los Cárteles»).
**El análisis medido del video completo está en `ANALISIS.md`.**

## 1. Análisis del video de referencia

| Aspecto | Qué se ve |
|---|---|
| **Formato** | Horizontal 16:9 (video largo de YouTube, no short). Funciona igual en 9:16. |
| **Título** | `POV: Eres el creador de [cosa famosa, peligrosa o absurda]`. Pone al espectador en la piel de quien lo inventó. |
| **Narrador** | Segunda persona: «Eres…», «Tú decides…», «Pero tienes un problema…». Tono serio con humor seco. |
| **Protagonista** | El mismo monito en todo el video: cabeza circular blanca, grande, con contorno negro, **pelo rubio despeinado** (su seña), cuerpo de palitos y sombra ovalada en el suelo. Expresiones exageradas: sonrisa maliciosa, cejas en V y brazos en jarras. |
| **Secundarios** | Monitos idénticos sin pelo (calvos), cada uno con un solo accesorio que dice quién es: chaleco táctico, rifle, casco o bata. |
| **Fondo** | Papel beige texturizado, casi vacío. Solo hay una línea de suelo con trazos sueltos. Los personajes no tapan nada. |
| **Objetos** | Mucho más detallados que los personajes: estilo cómic entintado y sombreado, con óxido, remaches y metal soldado. El contraste entre el monito simple y el objeto detallado es la clave visual. |
| **Texto en imagen** | Rótulos cortos en los objetos (cajas con una palabra) y flechas rojas a mano en la miniatura. Casi sin texto sobreimpreso. |
| **Efectos** | Chispas de soldadura, aura morada humeante («modo villano») y líneas de movimiento. |
| **Miniatura** | El objeto en grande, una mano en primer plano trabajando (soldando), chispas brillantes y una flecha roja. |
| **Animación** | Imágenes fijas con zoom lento, fundidos cortos entre planos y unos pocos planos con movimiento de IA. Los primeros planos de caras crecen lentamente durante 4–8 s. |
| **Cómo se hizo (probable)** | Imágenes con IA (Nano Banana / Flow u otro) usando una **hoja de personaje fija** como referencia, voz con IA, movimiento con imagen→video y edición en CapCut o DaVinci. |

## 2. La fórmula del guion (medida en el video completo: ver `ANALISIS.md`)

Duración: 7–10 min. Voz a **150 palabras/min**, casi sin pausas. **Una imagen nueva cada 2–4 s**
(media de 3,2 s), con fundidos cortos dentro de una escena y cortes secos en los golpes.

Es una **historia de ficción en segunda persona sobre un fenómeno real**: una persona normal que va cayendo,
paso a paso, en algo oscuro.

1. **Adelanto en frío (0–15 s, sin voz):** imágenes épicas del final con música.
2. **«Este eres tú» (15–50 s):** una escena imposible del presente → «cualquiera asumiría que eres X…
   pero la verdad es más patética» → «¿Cómo es que…?» → «Descubramos esta absurda historia».
3. **El pozo:** origen humilde, deudas y un negocio que fracasa.
4. **La primera tentación:** una propuesta sospechosa con dinero → acepta por necesidad → le pagan de más.
5. **Escalada:** vuelven con algo peor y aparece una evidencia que asusta → acepta por miedo. Sigue el autoengaño.
6. **La oferta definitiva:** dice que NO → castigo silencioso → acepta («vendiste tu alma»).
7. **Transformación:** recursos ilimitados, el negocio cambia por completo y algo oscuro despierta.
8. **Cierre:** el éxito llega al máximo, se vuelve a la escena del gancho y termina con una frase irónica.

Reglas:
- Narración en segunda persona con la jerga de tu público y frases sensoriales en los momentos clave.
- Datos reales del fenómeno para dar credibilidad, con su fuente.
- **Narra, no glorifiques.** Muestra el costo moral, sin instrucciones para fabricar o hacer nada peligroso.
- Usa `prompts/guion.txt`: ya devuelve el guion dividido en planos.

## 3. Herramientas

| Paso | Opción recomendada | Alternativas |
|---|---|---|
| Guion | Claude con `prompts/guion.txt` | — |
| Voz | ElevenLabs (voz masculina narrativa, estable) | Higgsfield `generate_audio`, tu propia voz |
| Tiempos por palabra | Whisper (`pip install openai-whisper`) | El skill `videos-animados-2d` lo hace solo |
| Hoja de personaje | **Google Flow / Nano Banana** (MCP `srz-google-flow-mcp`) con `prompts/personaje.txt` | Higgsfield `generate_image` |
| Imágenes de escena | Flow con `@{protagonista}` como referencia + `prompts/escena.txt` | Higgsfield con imagen de referencia |
| Movimiento | `ensamblar.py` (zoom y paneo sobre cada imagen, gratis) | Veo en Flow o Kling/Higgsfield imagen→video para planos clave |
| Música y efectos | Biblioteca de audio de YouTube (sin derechos) | Pixabay, Epidemic Sound |
| Edición final | `ensamblar.py` para el corte base y CapCut/DaVinci para pulir | — |

Atajo: el skill **`videos-animados-2d`** ya hace todo el proceso de monitos stickman (voz → tiempos →
escenas → render → música → MP4 y metadatos). Úsalo cuando tengas la voz; este kit le da el
look y la fórmula de este formato.

## 4. Proceso paso a paso

1. **Tema:** elige algo real con «inventor» claro y una escalada (narcosubmarinos, la Muralla, el primer paracaídas…).
2. **Guion:** usa `prompts/guion.txt` y revisa los datos.
3. **Voz:** genera `voz.mp3` y saca los tiempos con Whisper.
4. **Hoja de personaje:** genera 4 opciones con `prompts/personaje.txt`, elige una y súbela a Flow como `protagonista`. **Esta imagen se usa en TODAS las escenas.**
5. **Lista de escenas:** divide el guion en planos de 2–4 s. Para cada uno escribe: texto narrado, qué se ve, expresión del monito y objeto principal (ver `ejemplo/plan.json`).
6. **Imágenes:** genera cada plano con `prompts/escena.txt` en 16:9 (o 9:16 para shorts) y repite los que salgan con otro estilo.
7. **Ensamblar:** completa `plan.json` con las rutas y los tiempos y luego ejecuta:
   ```
   python3 ensamblar.py ejemplo/plan.json salida.mp4
   ```
   Cada imagen recibe un zoom o paneo suave, un corte rápido y la voz y la música mezcladas.
8. **Pulir:** anima con imagen→video 3 a 5 planos importantes (gancho, clímax, giro), añade efectos (chispas, golpes, whoosh) en CapCut y crea la miniatura con `prompts/miniatura.txt`.

## 5. Control de calidad

- [ ] El protagonista se ve igual en todas las imágenes (pelo, tamaño de cabeza y grosor de línea).
- [ ] El fondo es siempre papel beige con poco detalle.
- [ ] Los objetos son detallados y los personajes simples.
- [ ] Las imágenes duran 2–4 s (los primeros planos de cara, hasta 8 s) y ninguna se queda quieta.
- [ ] El video arranca con un adelanto sin voz y el gancho «Este eres tú».
- [ ] Ninguna imagen tiene texto mal escrito ni en otro idioma.
- [ ] La voz va al frente, la música de suspenso suena 15–20 dB más baja y el final queda a −14 LUFS.
- [ ] Los datos tienen su fuente y no hay instrucciones peligrosas.
- [ ] El estilo es este, pero el personaje es tuyo: cambia la seña (otro color o forma de pelo, gorra, lentes). No copies el personaje, los guiones ni las miniaturas del canal de referencia.
