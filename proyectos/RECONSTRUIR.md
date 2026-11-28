# Reconstruir los videos sin gastar créditos

Todo lo necesario ya existe: la voz está guardada en ElevenLabs (no se vuelve a generar ni cobra), los cómics en Google Drive y los
planes de tomas en esta rama (`claude/happy-johnson-78xw49`). Nada se vuelve a generar.

Instalar: `pip install pillow numpy faster-whisper` (y tener ffmpeg y pdfimages).

## 1. ¿Quién es Doctor Doom? (horizontal 1920x1080)
- Cómic (PDF): Google Drive id `1M4Xvgy-6pszz04V_vIzVOGUIHee8ZBB0`
  `curl -sL -o doom.pdf "https://drive.usercontent.google.com/download?id=1M4Xvgy-6pszz04V_vIzVOGUIHee8ZBB0&export=download&confirm=t"`
  `mkdir -p proyectos/doom/paginas && pdfimages -j doom.pdf proyectos/doom/paginas/p`
- Voz (ElevenLabs, voz «Cómics», toma A): pedir el enlace con la herramienta
  `creative_get_flow_run_status` (flow_id `BBrYqparnGYlpoqBz631`, session_ids `["2SnP5i0Nx5jMnzP0pAt4"]`,
  generación `2sx7O2zkvxDK48gQgRud`) y descargar su `content_url` a `proyectos/doom/voz.mp3`.
- Render: `cd proyectos/doom && python3 ../../comic/motor_comic.py plan.json`
  → `proyectos/doom/salida/quien_es_doom.mp4`

## 2. Doctor Strange y Doctor Doom: Triunfo y Tormento (vertical 1080x1920)
- Cómic (ZIP de JPG): Google Drive id `1NZkVZkjH1sT_B-VNH8HYvvN_609nF0MP`
  `curl -sL -o sd.zip "https://drive.usercontent.google.com/download?id=1NZkVZkjH1sT_B-VNH8HYvvN_609nF0MP&export=download&confirm=t"`
  `mkdir -p proyectos/comic2/paginas && unzip -q -j sd.zip -d proyectos/comic2/paginas`
- Voz (toma A): `creative_get_flow_run_status` con flow_id `TmxItPuPVDLrYleHe0Ii`, session_ids
  `["62NMaRg8HnMegEpkNaiS"]`, generación `az1oxtUxY8E5eys7f12D` → descargar a `proyectos/comic2/voz.mp3`.
- Render: `cd proyectos/comic2 && MIN_ANCHO=0.28 python3 ../../comic/motor_comic.py plan.json`
  → `proyectos/comic2/salida/strange_doom.mp4`

## 3. Guardar
Subir los dos MP4 a `adrian0659/Carpeta-de-videos-` (privado). GitHub no acepta archivos de más de
100 MB en commits normales: el de Strange y Doom pesa ~138 MB, así que conviene subirlos como archivos de
una Release (hasta 2 GB) o con Git LFS.
