# Generar las 38 imágenes con Google Flow (para Claude Code en tu ordenador)

Estas instrucciones son para Claude Code en el ordenador del usuario, con el MCP `srz-google-flow-mcp` instalado.
Carpeta de trabajo: la carpeta de este archivo (`pov-stickman/proyectos/doctor-cartel/`).

## Antes de empezar
1. Comprueba que existen las herramientas `flow_upload_file`, `flow_generate_image` y `flow_new_project`.
   Si no están, ayuda al usuario a instalar el MCP (descomprime `srzGoogleFlowMCP.zip`, abre Claude allí
   y escribe «instálalo») y pídele que reinicie Claude.
2. Llama a `flow_new_project` para trabajar en un proyecto limpio.

## Paso 1: subir la referencia de estilo
`flow_upload_file({ filePath: "<ruta absoluta>/pov-stickman/referencias/estilo_taller.jpg", name: "estilo" })`

## Paso 2: hoja del personaje (el doctor)
Genera 4 opciones en 16:9 con el modelo `pro`:

```
Image 1 -> Style: @{estilo}

Character reference sheet in the exact style of @Image 1: one young doctor, spiky messy black hair,
perfectly round white head with thin black outline, simple face (black dot eyes, short straight eyebrows,
small line mouth), white lab coat over a light blue shirt, stethoscope around the neck, thin black stick
arms and stick legs, white cartoon glove hands, big black shoes.
Show him 4 times: front neutral, proud smile holding a diploma, shocked with arms up, worried and sweating.
Plain light gray background, no text.
```

Enséñale las 4 al usuario y **espera a que elija una**. Súbela con
`flow_upload_file({ filePath: "<la elegida>", name: "doctor" })`.

## Paso 3: los 38 planos
Lee `plan.json`. Para cada plano `NN` (01…38) genera **1 imagen en 16:9** con el modelo `2`
(usa `pro` si el resultado no se parece al estilo) y este prompt, cambiando ESCENA por el campo `escena`:

```
Image 1 -> Style: @{estilo}
Image 2 -> Character: @{doctor}

Clean digital cartoon illustration in the exact style of @Image 1. Characters have perfectly round white
heads with thin black outlines, simple faces, thin black stick arms and legs, white cartoon glove hands,
big black shoes and real clothes drawn over the stick body. The doctor is exactly the character from
@Image 2 (spiky black hair, white lab coat, stethoscope).
Scene: ESCENA.
Realistic clean setting with detailed objects, soft cool gray and blue tones, bright daylight.
Any visible text must be in correct Spanish. No captions, no watermark.
```

Si el plano tiene `"atmosfera": "oscura"`, cambia la penúltima línea de ambiente por:
`Dark moody setting at night, a single overhead light casting hard shadows, deep shadows.`

Personajes que se repiten (descríbelos igual en cada plano donde salgan):
- **El jefe:** «the cartel boss: round white head, thick black mustache, cowboy hat, gold chain, flashy patterned shirt».
- **Los sicarios:** «stickmen gunmen with tactical vests, tattoos and rifles».

Guarda cada resultado como `img/NN.png` (por ejemplo `img/07.png`), copiándolo desde la carpeta de salida de Flow.
Ve de 5 en 5 y enséñale al usuario cómo van. Repite una imagen si:
- el doctor no se parece a la hoja;
- el estilo cambia (por ejemplo, papel beige o 3D);
- tiene texto mal escrito o en inglés.

## Paso 4: armar el video
Cuando estén las 38 imágenes:
```
python3 ../../ensamblar.py plan.json final.mp4
```
(Necesita `pip install pillow numpy` y `ffmpeg`.) Si el usuario tiene música sin derechos, guárdala como
`musica.mp3` en esta carpeta antes de ejecutar. Si no, el video sale solo con la voz.
