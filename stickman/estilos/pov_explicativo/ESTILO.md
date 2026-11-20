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
