#!/usr/bin/env python3
"""
Genera PROMPTS.md (guion + prompts listos para copiar) a partir de historia.json.

Uso:
    python3 prompts.py ejemplos/la_receta/historia.json

historia.json:
{
  "titulo": "...",
  "acento": "Mexican Spanish",
  "personajes": {"LUCIA": {"nombre": "Lucía", "bloque": "...descripción fija en inglés...", "voz": "..."}},
  "lugares":    {"COCINA": "...descripción fija en inglés..."},
  "tomas": [
    {"habla": "LUCIA", "frase": "...", "tono": "...", "lugar": "COCINA",
     "otros": ["TONO"], "accion": "...", "camara": "medium shot"}
  ]
}
"""
import json
import sys
from pathlib import Path

PLANTILLA = """Photorealistic cinematic vertical 9:16 video. {bloque}{otros} Location: {lugar}
Action: {accion} Camera: {camara}, static with a very slow push-in, eye level, 35mm lens, shallow depth of field.
{pronombre} speaks in {acento} with a {voz} voice, {tono}, perfectly lip-synced:
"{frase}"
Warm tungsten practical lights, realistic fur detail, natural human hands.
Only this character speaks. No music, no subtitles, no on-screen text, no watermark."""

IMAGEN = """Hyperrealistic cinematic photograph, vertical 9:16. {bloque} Standing in: {lugar}
Medium shot, eye level, 35mm lens, shallow depth of field, warm tungsten practical lights, realistic fur detail,
natural human hands. No text, no watermark."""


def main():
    ruta = Path(sys.argv[1])
    h = json.loads(ruta.read_text(encoding="utf-8"))
    P, L = h["personajes"], h["lugares"]
    out = [f"# {h['titulo']} — guion y prompts", "",
           "Generado con `drama/prompts.py` desde `historia.json`. Edita el JSON y vuelve a correrlo.", "",
           "## Guion", "", "| # | Quién | Frase |", "|---|---|---|"]
    for i, t in enumerate(h["tomas"], 1):
        out.append(f"| {i:02d} | {P[t['habla']]['nombre']} | {t['frase']} |")
    palabras = sum(len(t["frase"].split()) for t in h["tomas"])
    out += ["", f"{len(h['tomas'])} tomas · {palabras} palabras · ~{palabras / 3.2:.0f} s a ritmo de diálogo", ""]

    out += ["## 1. Imágenes de referencia (una por personaje)", "",
            "Genera cada una, elige la mejor y úsala como referencia en todas las tomas de ese personaje.", ""]
    for k, p in P.items():
        lugar = L[p.get("lugar_ref", next(iter(L)))]
        out += [f"### {p['nombre']}", "```", IMAGEN.format(bloque=p["bloque"], lugar=lugar), "```", ""]
    out += ["## 2. Lugares (sin personajes)", ""]
    for k, l in L.items():
        out += [f"### {k}", "```",
                f"Hyperrealistic cinematic photograph, vertical 9:16, empty establishing shot, no characters. {l} "
                "Warm tungsten practical lights, 35mm lens. No text except the signage described, no watermark.",
                "```", ""]

    out += ["## 3. Tomas (video de 8 s con voz; recorta a la frase)", ""]
    for i, t in enumerate(h["tomas"], 1):
        p = P[t["habla"]]
        otros = "".join(f" Also in frame: {P[o]['corto']}." for o in t.get("otros", []))
        prompt = PLANTILLA.format(
            bloque=p["bloque"], otros=otros, lugar=L[t["lugar"]], accion=t["accion"],
            camara=t.get("camara", "medium shot"), pronombre=p.get("pronombre", "He"),
            acento=h.get("acento", "Mexican Spanish"), voz=p["voz"], tono=t["tono"], frase=t["frase"])
        out += [f"### Toma {i:02d} — {p['nombre']}: «{t['frase']}»",
                f"Referencias: {', '.join([p['nombre']] + [P[o]['nombre'] for o in t.get('otros', [])])} · "
                f"lugar {t['lugar']}", "```", prompt, "```", ""]

    destino = ruta.with_name("PROMPTS.md")
    destino.write_text("\n".join(out), encoding="utf-8")
    print(f"Escrito {destino} ({len(h['tomas'])} tomas, ~{palabras / 3.2:.0f} s)")


if __name__ == "__main__":
    main()
