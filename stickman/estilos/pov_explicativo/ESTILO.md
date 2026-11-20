# Estilo «POV explicativo» (monigote ilustrado en escenario detallado)

Estilo guardado a partir de un video de referencia del usuario (13.8 s, noviembre 2026).
Úsalo cuando pida «el estilo que te guardé», «el del mecánico» o «estilo POV».
Cuadros de referencia: `cuadros/escena1-4.jpg` y `hoja_referencia.jpg` (solo para estudiar el look;
la historia, los personajes y la voz del video nuevo deben ser del usuario).

## Formato
- Horizontal **16:9** (la referencia se ve a 1280x720 aprox.; exportar 1920x1080, 30 fps).
- Una escena = **una frase de la narración**, de **3.5 a 4.5 s** cada una.
- Cortes duros entre escenas (en la referencia: ~0, 3.7, 7.95, 12.4 s). Sin transiciones vistosas.

## Guion y voz
- Narración en **segunda persona, presente** («Descubres…», «Reparas…», «Te guardas…»): el espectador ES
  el protagonista. Tono seco, sin emoción exagerada; el humor sale de los hechos.
- Estructura de mini historia con giro moral/pícaro:
  1. **Situación** con una cifra concreta («un presupuesto de 1.200 dólares por el repuesto alemán nuevo»).
  2. **Descubrimiento** que contradice la situación («solo tenía un cable suelto»).
  3. **Acción barata/rápida** con detalle concreto («en 10 minutos usando cinta eléctrica negra»).
  4. **Remate corto** de 3–5 palabras que revela la trampa («Te guardas la pieza nueva.»). El video termina ahí.
- Ritmo: ~2.9 palabras por segundo, pausas de 0.4–0.6 s entre frases. Una sola voz, sin música protagonista.

## Imagen
- **Protagonista:** monigote con cabeza blanca redonda grande, pelo negro alborotado de picos, ojos de punto,
  boca de una línea (expresión seria / dudosa / pícara con ceja fruncida), cuerpo y piernas de palito negro,
  zapatos negros grandes. **Lleva ropa** del oficio (aquí: camisa de trabajo azul marino con detalles rojos y
  parche de nombre). El mismo diseño en todas las escenas.
- Personajes secundarios con el mismo cuerpo de palito pero rasgos un poco más realistas (cliente con camisa,
  corbata y teléfono).
- **Escenario:** ilustración detallada, semi-realista, con contorno de tinta negra fino, sombreado suave y luz
  natural de ventana. Mucho detalle de ambiente (herramientas, carteles, muebles). Paleta fría y limpia
  (grises, blancos, azul) con **acentos rojos** (gabinete de herramientas, franja en la pared).
- Objetos clave dibujados con más realismo que el personaje (el auto, la pieza).
- Cámara a la altura del pecho, plano medio-abierto: personaje de cuerpo entero a la izquierda/centro, objeto
  clave a la derecha.

## Textos en pantalla (la firma del estilo)
- **Etiquetas escritas a mano** en MAYÚSCULAS negras, condensadas, con **flecha curva** apuntando al objeto:
  «ALTERNADOR ORIGINAL», «CABLE SUELTO», «CINTA ELÉCTRICA NEGRA», «CABLE REPARADO ✓», «10 MINUTOS» con un
  cronómetro dibujado. Repiten las palabras clave de la narración.
- Palomita verde ✓ para lo «aprobado/arreglado».
- **Recuadro de detalle** (inserto) en una esquina con borde blanco: un acercamiento al dato clave
  (pantalla de tablet con «PRESUPUESTO APROBADO · USD 1.200 ✓»).
- Las etiquetas aparecen junto con la frase que las menciona. Sin subtítulos de la narración.

## Movimiento
- Cada escena es casi un cuadro fijo con **vida sutil**: zoom lento (Ken Burns 3–5 %), pequeños gestos del
  personaje (cabeza que se inclina, parpadeo, mano que se mueve, luz de linterna).
- Las etiquetas entran con un pequeño «pop» o trazo.

## Cómo producirlo
- Escenarios y personaje: imágenes ilustradas (generadas o dibujadas) a 16:9, manteniendo el mismo personaje;
  después se animan con zoom lento + capas (personaje, etiquetas) en Python (`stickman/motor.py` sirve para
  etiquetas, pops, zoom y sonido) o en Remotion.
- El motor `stickman/motor.py` por sí solo da monigotes más simples (fondo plano); para este look hay que
  usar escenarios ilustrados de fondo.
- No copies el escenario del taller ni la historia del mecánico: es la referencia del look.
- Si usas generadores de imágenes con costo, avisa al usuario antes.

## Versión dibujada con código (sin IA, gratis)
`motor_pov.py` reproduce el estilo sin generar imágenes: monigote con ropa (`Actor`, trajes en `TRAJES`,
poses en `POSES`), escenarios (`rancho`, `interior`, `ventana`, `camioneta`, `helicoptero`, `mapa_mexico`...),
`Etiqueta` (texto a mano + flecha curva, opción `tachar` y `palomita`), `Inserto` (recuadro de detalle) y
`Escena` (fondo cacheado, zoom lento, sacudidas, tinte de noche). Fuentes en `fuentes/` (licencia OFL):
instálalas en `~/.fonts` o en el sistema antes de renderizar.

Ejemplo completo: `videos/escolta.py` (vertical 9:16, 2:08, 31 escenas, voz de ElevenLabs).
```
python3 videos/escolta.py --fotos        # una foto por escena
python3 videos/escolta.py --voz voz.mp3  # video final en salida/escolta/escolta.mp4
```
Flujo: transcribir la voz con tiempos por palabra (faster-whisper) → un corte por frase, 0.15 s antes →
una escena por frase con 1–3 etiquetas que caen sobre su palabra → fotos de revisión → render en paralelo.

## Escenarios realistas y detallados (caricatura) — `escenarios.py`
Fondos con más realismo, cerca de la referencia: perspectiva de un punto (`Cuarto`), texturas sutiles
(estuco, concreto, duela de madera, piedra, empedrado), sombras suaves difuminadas, oclusión en esquinas,
haces de luz de ventana, reflejo en pisos brillantes, lámparas, bruma por capas y mucha utilería.
Muestra: `escenarios_muestra.png` · con monigote y etiquetas: `escenarios_demo_taller.png`.

| Escenario | Qué trae | Horas |
|---|---|---|
| `taller` | taller mecánico: piso epóxico con reflejo, gabinete rojo, tablero de herramientas, carteles, banco, llantas | dia/tarde/noche |
| `oficina` | ventanal a la ciudad (luces de noche), escritorio, librero, plantas, duela | dia/noche |
| `sala` | sillón en primer plano, tapete, tele, lámpara de pie, cortinas, cuadro | dia/tarde/noche |
| `cocina` | alacenas, azulejo, estufa, refri, barra | dia/noche |
| `bodega` | concreto, cajas «FRÁGIL», foco colgante con cono de luz | noche |
| `calle` | calle mexicana en perspectiva: fachadas de colores, balcones, postes, cables, coche | dia/tarde/noche |
| `rancho` | hacienda con arcos, base de piedra, buganvilias, faroles, empedrado, montañas | dia/tarde/noche |
| `sierra` | pinos en capas con niebla, sol bajo | dia/tarde/noche |

Uso: `Escena(t0, t1, lambda c: taller(c, "noche"), capas=[actor, Etiqueta(...)])`.
Hoja de muestra: `python3 escenarios.py taller oficina calle:tarde rancho:noche`.
Para un escenario nuevo: crea un `Cuarto(...)`, llama `pintar(...)` y coloca utilería con `quad(lado, u0, u1, v0, v1)`
(paredes laterales) o en coordenadas directas (pared del fondo); termina con `reflejo_piso` si el piso brilla.
Trajes nuevos: `mecanico`, `oficinista`.

## Cómic POV (personas caricatura + manos en primera persona) — `comic.py`
Referencia: `cuadros/referencia_comic_pov.jpg` · resultado con código: `comic_pov_demo.png`.
- **Formato 16:9** (`M.formato(1920, 1080)`; también sirve 9:16 cambiando el formato y las posiciones).
- **Cámara en primera persona:** los antebrazos del espectador salen del borde inferior con guantes y sostienen
  objetos (`manos_pov(objeto_izq, objeto_der, guantes)`); se mecen un poco.
- **Personas caricatura** (`Persona(cfg, claves, s)`), de la cintura para arriba detrás de una mesa:
  cara con orejas, nariz, surcos, ojos con iris, párpado grueso, cejas gruesas, arrugas de enojo/miedo, sudor;
  bocas `grito` (con dientes y lengua, se mueve), `oval`, `sonrisa`, `sonrisa_lado`, `triste`, `torcida`, `linea`.
  - Expresiones: `neutral, enojado, furioso, miedo, sorpresa, feliz, serio, triste, pensando, malicia` (tiemblan si hay miedo/furia).
  - Poses de brazos: `relajado, senalar_d, senalar_i, manos_cabeza, apoyado, cruzados, pensar, telefono, dinero`.
  - Pelo: `ondulado, canoso, gorro, gorra, corto, calvo, largo`; extras: `bigote, barba ('candado'),
    barba_crecida, lentes='sol', cigarro (con humo), cicatriz, cadena`.
  - Ropa: `hawaiana` (flores), `sudadera` (playera con estampado), `camisa, traje, cuadros, playera, bata, militar`.
- **Tinta de cómic:** contorno grueso, sombra de cel en un lado, achurado diagonal, arrugas de tela.
- **Escenario** `casa_rodante` (laboratorio en casa rodante: techo curvo, ventilas, tubo fluorescente, cables,
  estante con matraces, alacenas, tablero eléctrico) + `mostrador_lab` en primer plano (frascos, charola,
  guante, frasco con cristales, fajos de billetes, lentes). Combínalo con los escenarios de `escenarios.py`.
- Personajes siempre **originales**: no copies caras, ropa ni nombres de series o películas.
- Demo: `python3 comic.py --video` → `salida/comic_demo.png` y `salida/comic_demo.mp4`.

## Personajes (monigote con ropa) — referencia `cuadros/referencia_personajes.jpg`, resultado `personajes_demo.png`
`Actor` de `motor_pov.py` ya dibuja así a todos los personajes:
- Cabeza blanca **un poco ovalada**, ojos ovalados negros con brillo, **cejas gruesas siempre** (cambian con la cara),
  boca pequeña. Pelo `picos` (negro alborotado con fleco en picos) o `raya` (café con volumen y patillas).
- **Camisa de verdad:** cuello con puntas (color propio con `cuello=`), tapeta con botones, bolsillo, **parche con
  nombre** (`parche="MECÁNICO"`), ribete de manga (`puno=`), corbata (`corbata=`), pliegues.
- Antebrazos y piernas de palito negro; **manos blancas de caricatura** (guante con pulgar); **zapatos grandes**
  con suela, agujetas y brillo.
- **Objeto en la mano** con la clave `objeto`: `telefono`, `tablet` (presupuesto), `llave`, `linterna`, `dinero`.
- Trajes listos: `mecanico` (azul marino, cuello y ribete rojos, parche) y `cliente` (camisa gris, corbata vino, pelo café).
- Ejemplo: `python3 videos/demo_personajes.py`.
