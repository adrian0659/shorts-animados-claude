---
name: remotion
description: >-
  Crea un short vertical de caricatura (personajes planos en un mundo 3D) con Three.js y Remotion usando las
  plantillas de este repo. Úsala cuando escriban /remotion o pidan un short de caricatura, un video como el de
  Alejandro Magno o el del puente, o renderizar con Remotion.
---

# /remotion — shorts de caricatura con Three.js + Remotion

Atajo directo al estilo **caricatura** del paquete. No preguntes por el estilo: ya está elegido. No uses Blender
(eso es `realista/REALISTA.md`) ni el motor de Python de `stickman/`.

## Antes de empezar
1. Lee la parte de caricatura de `SKILL.md` en la raíz del repo: **Reglas del estilo**, **Proceso** (pasos 1–11),
   **Lo que aprendimos con Alejandro**, **Valores finales del look** y **Trampas conocidas**. Esa es la fuente de
   verdad; este archivo solo te lleva hasta ahí.
2. Si vas a escribir o cambiar código de Remotion, carga también la skill `remotion-best-practices`.
3. Habla en español sencillo y pregunta una cosa por vez si la persona es principiante.

## Qué pedirle a la persona (solo lo que falte)
- La **idea o el dato real** que quiere contar y la **duración** aproximada.
- Si ya tiene **guion** o **voz** (`voz.wav`), úsalos y no se los vuelvas a pedir.
- Dónde quiere guardar el proyecto. No pidas claves en el chat; si hace falta un servicio de voz con costo, explica
  las opciones antes.

## Elegir plantilla
- `plantillas/alejandro/` → batallas, multitudes, cámara lenta, fuego y brasas (composición `Alejandro`).
- `plantillas/puente/` → pueblo, personajes que caminan, luz de día o atardecer.

Copia la más parecida a `src/videos/<nombre>/` y regístrala en `src/Root.tsx`
(guía: `plantillas/alejandro/Root_ejemplo.tsx`; dependencias: `plantillas/alejandro/package_ejemplo.json`).

## Flujo corto
1. Datos con fuente → guion con la fórmula de `referencias/BIBLIA_DE_ESTILO.md` → espera aprobación.
2. Voz + `palabras.json` con tiempos por palabra.
3. Tomas en `story.ts` sincronizadas con las palabras; luego mundo, personajes y post.
4. Fotos de revisión: `node plantillas/scripts/fotos.mjs out/x_ 20,100,200 0.5`.
5. Medición: `python herramientas/medir_30fps.py out/video.mp4 out/medida`.
6. Render: `npx remotion render src/index.ts <Composición> out/video.mp4 --codec h264 --crf 16`,
   y une la voz con ffmpeg usando `-map 0:v:0 -map 1:a:0`.
7. QA: `python plantillas/scripts/short_qa.py final.mp4 out/qa shots.json`.

Prepara `RENDERIZAR.bat` (Windows) o `RENDERIZAR.command` (Mac) como indica `SKILL.md`. Antes de decir que
terminaste, comprueba que el MP4 tiene imagen, audio y la duración correcta; si algo falla, dilo.
