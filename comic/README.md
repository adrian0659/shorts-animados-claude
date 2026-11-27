# Shorts narrados de cómic («¿Sabías que...?»)

Cuarto estilo del paquete: tomas las páginas de un cómic, una voz cuenta la historia y la cámara recorre
cada viñeta con paneos y acercamientos, con cortes secos al ritmo de cada frase (formato de TikTok/Shorts
de curiosidades de cómics). Todo en Python + ffmpeg; un short de 60 s se renderiza en menos de 1 minuto.

## Instalar
```
pip install pillow numpy faster-whisper
```
Además `ffmpeg`.

## Pasos
1. **Páginas**: pon las páginas del cómic en `mi_short/paginas/` (jpg o png, lo más grandes posible).
2. **Viñetas**: `python3 comic/paneles.py mi_short/paginas/*.jpg` → fotos numeradas en `salida/paneles/`.
3. **Guion** (40-60 s, ~150 palabras): gancho con «¿Sabías que...?» en la primera frase, la historia en
   frases cortas y un cierre fuerte. Una frase = una toma (o varias viñetas con `"vinetas"`).
4. **Voz**: grábala o genérala (ElevenLabs) leyendo exactamente el guion → `mi_short/voz.mp3`.
5. **Plan**: `mi_short/plan.json` (formato en `motor_comic.py`; ejemplo en `ejemplos/plan_ejemplo.json`).
   Los tiempos salen solos: Whisper escucha la voz y corta cada toma cuando empieza su frase.
6. **Revisar**: `python3 comic/motor_comic.py mi_short/plan.json --fotos` → hoja con una foto por toma.
7. **Render**: `python3 comic/motor_comic.py mi_short/plan.json` → MP4 1080x1920, 30 fps, voz a -14 LUFS
   y música opcional que baja sola cuando se habla.

## Consejos del formato (medidos en un short de referencia de 60 s)
- Un corte cada 1.5-3 s; en frases largas reparte 2-3 viñetas.
- Primeros planos de caras para emociones; viñetas anchas para acción (el motor las recorre).
- `"impacto": true` en el gancho, en los golpes y en el giro final.
- Los cómics tienen derechos de autor: el uso en redes es responsabilidad de quien publica.
