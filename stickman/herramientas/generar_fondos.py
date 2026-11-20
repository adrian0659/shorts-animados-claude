"""Genera fondos semirrealistas con IA local y gratuita (LCM Dreamshaper v7, licencia MIT), sin personas.

    pip install torch diffusers transformers accelerate safetensors
    python3 herramientas/generar_fondos.py fondos.json carpeta_salida/ [variantes]
fondos.json: {"nombre": "descripción en inglés", ...}. Sale <nombre>_<n>.png en vertical (512x912).
Corre en CPU: ~30–60 s por imagen. El estilo y lo que se evita se añaden solos a cada descripción.
"""
import json, os, sys, time
import torch
from huggingface_hub import snapshot_download
from diffusers import DiffusionPipeline

ESTILO = ("semi-realistic digital painting, cinematic lighting, highly detailed environment concept art, "
          "vertical composition, empty scene, no people")
EVITAR = "people, person, man, woman, face, hands, text, letters, watermark, logo, deformed, blurry, lowres"

fondos, salida = json.load(open(sys.argv[1])), sys.argv[2]
variantes = int(sys.argv[3]) if len(sys.argv) > 3 else 2
os.makedirs(salida, exist_ok=True)
ruta = snapshot_download("SimianLuo/LCM_Dreamshaper_v7", ignore_patterns=["*.onnx", "*.onnx_data", "*4k.safetensors",
                                                                          "*.png", "safety_checker/*"])
pipe = DiffusionPipeline.from_pretrained(ruta, torch_dtype=torch.float32, safety_checker=None, requires_safety_checker=False)
pipe.set_progress_bar_config(disable=True)
torch.set_num_threads(os.cpu_count())
for nombre, desc in fondos.items():
    for v in range(variantes):
        destino = os.path.join(salida, f"{nombre}_{v}.png")
        if os.path.exists(destino): continue
        t0 = time.time()
        g = torch.Generator().manual_seed(1000 + v * 77 + len(nombre))
        img = pipe(prompt=f"{desc}, {ESTILO}", negative_prompt=EVITAR, num_inference_steps=6, guidance_scale=8.0,
                   width=512, height=912, generator=g).images[0]
        img.save(destino); print(f"{destino}  ({time.time() - t0:.0f} s)", flush=True)
print("FIN", flush=True)
