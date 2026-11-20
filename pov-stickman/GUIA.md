# Videos «POV: Eres el creador de…» con monito stickman

Kit para hacer videos explicativos narrados en segunda persona, con un monito de cabeza
redonda dibujado a tinta sobre papel beige, como el video de referencia
(«POV: Eres el Creador de los Narcotanques de los Cárteles»).

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
| **Animación** | Ilustraciones fijas con poco movimiento: la cámara se acerca o se desliza, los objetos aparecen de golpe y algunos planos están animados con IA de video (brazos robóticos, cinta transportadora). |
| **Cómo se hizo (probable)** | Imágenes con IA (Nano Banana / Flow u otro) usando una **hoja de personaje fija** como referencia, voz con IA, movimiento con imagen→video y edición en CapCut o DaVinci. |

## 2. La fórmula del guion

Duración típica: 6–12 min. Ritmo: 150–160 palabras por minuto y **una imagen nueva cada 3–6 s**.

1. **Gancho (0–15 s):** «Eres [rol]. Tienes [problema absurdo]. Y tu solución va a ser [cosa extrema]».
2. **Contexto:** dónde y cuándo, por qué existe el problema y un dato duro con cifra.
3. **Primer intento, que sale mal.** Algo simple que fracasa por una razón concreta. Usa humor.
4. **Escalada, con 3 o 4 versiones:** cada versión resuelve el fallo anterior y crea uno nuevo (más blindaje → más peso → motor más grande…). Esta es la columna del video.
5. **El clímax:** la versión más exagerada, con el monito orgulloso y aura de villano.
6. **El giro / consecuencia real:** qué pasó de verdad (decomisos, arrestos, cómo acabó).
7. **Remate:** una frase seca e irónica sobre el protagonista.

Reglas:
- Hechos reales verificables, con fuente anotada arriba del guion. Si hay cifras dudosas, usa la estimación prudente.
- **Narra, no glorifiques.** Con temas criminales, explica el fenómeno y su final real, sin dar instrucciones de cómo fabricar o hacer nada peligroso.
- Frases cortas. Una idea por imagen. No describas con la voz lo que ya se ve.
- Usa `prompts/guion.txt` para pedirle el guion a Claude.

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
5. **Lista de escenas:** divide el guion en planos de 3–6 s. Para cada uno escribe: texto narrado, qué se ve, expresión del monito y objeto principal (ver `ejemplo/plan.json`).
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
- [ ] Cada imagen dura entre 3 y 6 s y ninguna se queda quieta.
- [ ] La voz va al frente y la música 15–20 dB más baja.
- [ ] Los datos tienen su fuente y no hay instrucciones peligrosas.
- [ ] El estilo es este, pero el personaje es tuyo: cambia la seña (otro color o forma de pelo, gorra, lentes). No copies el personaje, los guiones ni las miniaturas del canal de referencia.
