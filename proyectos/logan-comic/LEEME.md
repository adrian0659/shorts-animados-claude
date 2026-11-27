# Logan — short vertical estilo cómic (16 s, 1080x1920, 30 fps)

Vaquero original (no es el personaje de Marvel) amarrado a una cruz en el desierto de Sonora, 1887.
Cinco viñetas: plano general → cara → el cuervo («¿Craaa?» / «Todavía no, amigo.») → ojos + ¡CRAC! → Logan libre y el título.

- Imagen: `src/Comic.tsx` (Remotion + SVG: trama de puntos, tinta gruesa, globos, onomatopeyas).
- Sonido: `audio/sonido.py` (todo sintetizado: viento, guitarra western, cuervo, golpe y remate).
- Fuente: Bangers (OFL) en `public/Bangers.ttf`.

Render:
```
npm install
npx remotion render src/index.ts LoganComic out/video_mudo.mp4 --codec h264 --crf 18
python3 audio/sonido.py out/audio.wav
ffmpeg -i out/video_mudo.mp4 -i out/audio.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest logan_comic.mp4
```
