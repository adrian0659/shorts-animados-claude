"""Motor de shorts estilo stickman (monigote) — Python + pycairo + ffmpeg.

Dibuja todo con código: monigotes con poses, utilería simple, subtítulos grandes
palabra por palabra y efectos de sonido sintetizados. Salida: MP4 vertical 1080x1920.

Uso típico (ver ejemplos/pulpo.py):
    from motor import Short, Monigote, Subtitulos
    short = Short(duracion=26)
    ...
    short.render("salida.mp4")
"""
import math, subprocess, random
import numpy as np
import cairo

W, H, FPS = 1080, 1920, 30
TINTA = (0.08, 0.08, 0.1)
PAPEL = (0.98, 0.97, 0.94)

# ---------------------------------------------------------------- utilidades
def lerp(a, b, k): return a + (b - a) * k
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def suave(k):  # ease in-out
    k = clamp(k); return k * k * (3 - 2 * k)
def rebote(k):  # ease-out-back: aparece con un pequeño "pop"
    k = clamp(k); c = 1.9
    return 1 + (c + 1) * (k - 1) ** 3 + c * (k - 1) ** 2

def temblor(seed, t, amp=2.0):
    """Efecto 'dibujado a mano': cambia ~8 veces por segundo."""
    r = random.Random(hash((seed, int(t * 8))))
    return r.uniform(-amp, amp), r.uniform(-amp, amp)

# ---------------------------------------------------------------- poses
# Ángulos absolutos en grados: 0 = hacia abajo, 90 = hacia la derecha, 180 = arriba, -90 = izquierda.
# 'i' = extremidad que se ve a la izquierda de la pantalla, 'd' = a la derecha.
POSES = {
    "parado":    dict(torso=180, cabeza=0, bi=-14, ai=-6, bd=14, ad=6, mi=-8, pi=-4, md=8, pd=4),
    "saludo":    dict(torso=180, cabeza=6, bi=-14, ai=-6, bd=125, ad=165, mi=-8, pi=-4, md=8, pd=4),
    "señalar_d": dict(torso=184, cabeza=8, bi=-14, ai=-6, bd=95, ad=95, mi=-8, pi=-4, md=10, pd=6),
    "señalar_i": dict(torso=176, cabeza=-8, bi=-95, ai=-95, bd=14, ad=6, mi=-10, pi=-6, md=8, pd=4),
    "sorpresa":  dict(torso=180, cabeza=0, bi=-135, ai=-165, bd=135, ad=165, mi=-14, pi=-10, md=14, pd=10),
    "pensar":    dict(torso=178, cabeza=-10, bi=-14, ai=-6, bd=30, ad=-150, mi=-8, pi=-4, md=8, pd=4),
    "encoger":   dict(torso=180, cabeza=10, bi=-60, ai=-140, bd=60, ad=140, mi=-8, pi=-4, md=8, pd=4),
    "festejar":  dict(torso=180, cabeza=0, bi=-150, ai=-175, bd=150, ad=175, mi=-25, pi=-5, md=25, pd=5),
    "triste":    dict(torso=172, cabeza=-25, bi=-6, ai=-2, bd=6, ad=2, mi=-6, pi=-3, md=6, pd=3),
    "barbilla":  dict(torso=178, cabeza=-10, bi=-14, ai=-6, bd=-8, ad=-158, mi=-8, pi=-4, md=8, pd=4),
    "jarras":    dict(torso=180, cabeza=4, bi=-62, ai=48, bd=62, ad=-48, mi=-10, pi=-6, md=10, pd=6),
}
ARTIC = list(POSES["parado"].keys())

def mezclar(p1, p2, k):
    return {j: lerp(p1[j], p2[j], k) for j in ARTIC}

def vec(ang, largo):
    a = math.radians(ang); return math.sin(a) * largo, math.cos(a) * largo


class Monigote:
    """Un monigote con fotogramas clave.

    claves: lista de dicts con 't' (segundos) y cualquiera de:
        pose, x, y, cara ('feliz','sorpresa','triste','serio','pensar'),
        caminar (True/False), saltar (True/False), mira (-1 izq / 1 der)
    """
    def __init__(self, claves, escala=1.0, grosor=14, color=TINTA, semilla=1):
        self.claves = sorted(claves, key=lambda c: c["t"])
        self.s, self.g, self.color, self.semilla = escala, grosor, color, semilla
        # rellena los valores que falten con los del fotograma anterior
        prev = dict(pose="parado", x=W / 2, y=1350, cara="feliz", caminar=False, saltar=False, mira=0)
        for c in self.claves:
            for k, v in prev.items(): c.setdefault(k, v)
            prev = dict(c); prev.pop("t"); prev["caminar"] = False; prev["saltar"] = False  # no se heredan

    def estado(self, t, dur_trans=0.35):
        cs = self.claves
        if t <= cs[0]["t"]: a = b = cs[0]; k = 0
        else:
            a = cs[0]; b = cs[0]
            for c in cs:
                if c["t"] <= t: a = c
            idx = cs.index(a)
            b = cs[idx + 1] if idx + 1 < len(cs) else a
            # la posición se interpola durante todo el tramo; la pose cambia rápido al inicio
            span = max(b["t"] - a["t"], 1e-6)
            k = suave((t - a["t"]) / span) if b is not a else 0
        # pose: transición corta desde la clave anterior
        idx = cs.index(a)
        anterior = cs[idx - 1] if idx > 0 else a
        kp = suave((t - a["t"]) / dur_trans)
        pose = mezclar(POSES[anterior["pose"]], POSES[a["pose"]], kp)
        x, y = lerp(a["x"], b["x"], k), lerp(a["y"], b["y"], k)
        moviendo = a["caminar"] and abs(b["x"] - a["x"]) > 1 and t < b["t"]
        return pose, x, y, a, moviendo

    def dibujar(self, ctx, t):
        pose, x, y, clave, moviendo = self.estado(t)
        s = self.s
        pose = dict(pose)
        # respiración / vida
        resp = math.sin(t * 2.2 + self.semilla) * 1.5
        pose["torso"] += math.sin(t * 1.3 + self.semilla) * 1.2
        if clave["pose"] == "saludo":
            pose["ad"] += math.sin(t * 12) * 22
        dy = 0
        if moviendo:
            f = t * 9
            pose["mi"] = math.sin(f) * 28; pose["pi"] = pose["mi"] + max(0, math.sin(f - 1.2)) * -30
            pose["md"] = -math.sin(f) * 28; pose["pd"] = pose["md"] + max(0, -math.sin(f - 1.2)) * -30
            pose["bi"] = -10 - math.sin(f) * 22; pose["ai"] = pose["bi"] - 12
            pose["bd"] = 10 + math.sin(f) * 22; pose["ad"] = pose["bd"] + 12
            dy = -abs(math.sin(f)) * 10 * s
        if clave["saltar"]:
            dy = -abs(math.sin(t * 7)) * 70 * s

        L = dict(torso=150 * s, cuello=10 * s, brazo=82 * s, ante=78 * s, muslo=92 * s, pierna=88 * s, cabeza=46 * s)
        cad = (x, y + dy + resp)
        # el pie más bajo toca el suelo: calculamos piernas primero
        def cadena(origen, a1, l1, a2, l2):
            p1 = (origen[0] + vec(a1, l1)[0], origen[1] + vec(a1, l1)[1])
            p2 = (p1[0] + vec(a2, l2)[0], p1[1] + vec(a2, l2)[1])
            return p1, p2
        rodi, pie_i = cadena((0, 0), pose["mi"], L["muslo"], pose["pi"], L["pierna"])
        rodd, pie_d = cadena((0, 0), pose["md"], L["muslo"], pose["pd"], L["pierna"])
        baja = max(pie_i[1], pie_d[1])
        cad = (cad[0], cad[1] - baja)  # y = línea del suelo
        hombro = (cad[0] + vec(pose["torso"], L["torso"])[0], cad[1] + vec(pose["torso"], L["torso"])[1])
        cuello = (hombro[0] + vec(pose["torso"], L["cuello"])[0], hombro[1] + vec(pose["torso"], L["cuello"])[1])
        cab = (cuello[0] + vec(pose["torso"] + pose["cabeza"], L["cabeza"])[0],
               cuello[1] + vec(pose["torso"] + pose["cabeza"], L["cabeza"])[1])
        codi, mani = cadena(hombro, pose["bi"], L["brazo"], pose["ai"], L["ante"])
        codd, mand = cadena(hombro, pose["bd"], L["brazo"], pose["ad"], L["ante"])
        rodi = (cad[0] + rodi[0], cad[1] + rodi[1]); pie_i = (cad[0] + pie_i[0], cad[1] + pie_i[1])
        rodd = (cad[0] + rodd[0], cad[1] + rodd[1]); pie_d = (cad[0] + pie_d[0], cad[1] + pie_d[1])

        # sombra
        ctx.save(); ctx.set_source_rgba(0, 0, 0, 0.12)
        ctx.translate(x, y); ctx.scale(1, 0.18); ctx.arc(0, 0, 80 * s * (1 - min(-dy, 80) / 200), 0, 2 * math.pi)
        ctx.fill(); ctx.restore()

        ctx.set_source_rgb(*self.color); ctx.set_line_width(self.g * s)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        j = lambda p, n: (p[0] + temblor((self.semilla, n), t, 1.2)[0], p[1] + temblor((self.semilla, n), t, 1.2)[1])
        for i, pts in enumerate([(cad, hombro, cuello), (cad, rodi, pie_i), (cad, rodd, pie_d),
                                 (hombro, codi, mani), (hombro, codd, mand)]):
            ctx.move_to(*j(pts[0], i * 3))
            ctx.line_to(*j(pts[1], i * 3 + 1)); ctx.line_to(*j(pts[2], i * 3 + 2)); ctx.stroke()
        # cabeza
        ctx.set_source_rgb(*PAPEL); ctx.arc(cab[0], cab[1], L["cabeza"], 0, 2 * math.pi); ctx.fill_preserve()
        ctx.set_source_rgb(*self.color); ctx.stroke()
        self._cara(ctx, cab, L["cabeza"], clave["cara"], pose["cabeza"] / 40 + clave["mira"] * 0.35, t)

    def _cara(self, ctx, c, r, cara, giro, t):
        ox = giro * r * 0.6
        parpadeo = (t + self.semilla * 0.7) % 3.4 < 0.12
        ctx.set_source_rgb(*self.color)
        for lado in (-1, 1):
            ex, ey = c[0] + ox + lado * r * 0.36, c[1] - r * 0.12
            if cara == "sorpresa":
                ctx.set_line_width(r * 0.1); ctx.arc(ex, ey, r * 0.16, 0, 2 * math.pi); ctx.stroke()
                ctx.arc(ex, ey, r * 0.06, 0, 2 * math.pi); ctx.fill()
                ctx.move_to(ex - r * 0.18, ey - r * 0.38); ctx.line_to(ex + r * 0.14, ey - r * 0.44 + lado * 0.0); ctx.stroke()
            elif parpadeo:
                ctx.set_line_width(r * 0.1); ctx.move_to(ex - r * 0.12, ey); ctx.line_to(ex + r * 0.12, ey); ctx.stroke()
            else:
                ctx.arc(ex, ey, r * 0.11, 0, 2 * math.pi); ctx.fill()
            if cara == "triste":
                ctx.set_line_width(r * 0.09)
                ctx.move_to(ex - lado * r * 0.2, ey - r * 0.25); ctx.line_to(ex + lado * r * 0.15, ey - r * 0.38); ctx.stroke()
        mx, my = c[0] + ox, c[1] + r * 0.38
        ctx.set_line_width(r * 0.11)
        if cara == "feliz":
            ctx.arc(mx, my - r * 0.18, r * 0.3, math.radians(25), math.radians(155)); ctx.stroke()
        elif cara == "sorpresa":
            ctx.save(); ctx.translate(mx, my); ctx.scale(1, 1.3); ctx.arc(0, 0, r * 0.15, 0, 2 * math.pi); ctx.restore(); ctx.fill()
        elif cara == "triste":
            ctx.arc(mx, my + r * 0.15, r * 0.25, math.radians(205), math.radians(335)); ctx.stroke()
        elif cara == "pensar":
            ctx.move_to(mx - r * 0.2, my); ctx.curve_to(mx - r * 0.05, my - r * 0.1, mx + r * 0.05, my + r * 0.1, mx + r * 0.22, my - r * 0.02); ctx.stroke()
        else:
            ctx.move_to(mx - r * 0.2, my); ctx.line_to(mx + r * 0.2, my); ctx.stroke()


# ---------------------------------------------------------------- personaje con sudadera
SOMBRA_FRIA = (0.80, 0.85, 0.92)   # sombreado gris azulado de la cabeza y la ropa
PELO_CAFE = (0.47, 0.29, 0.16)
SUDADERA_BLANCA = (0.93, 0.94, 0.95)


def _rel(origen, ang, x, y):
    """Punto (x, y) en el marco local de una pieza girada 'ang' (0 = abajo, 180 = arriba).
    En el marco local, -y apunta hacia 'ang + 180°'... es decir, 'arriba' de la pieza."""
    a = math.pi - math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    return origen[0] + x * c - y * s, origen[1] + x * s + y * c


# Vestuarios listos: elige el más cercano a la historia y cambia lo que haga falta.
# Claves: ropa, color, color2, pelo, peinado, sombrero, color_sombrero, accesorios, capa.
ROPAS = ("sudadera", "camiseta", "camisa", "uniforme", "traje", "bata", "vestido", "tunica", "armadura",
         "overol", "espacial")
PEINADOS = ("picos", "corto", "largo", "chongo", "calvo")
SOMBREROS = ("gorra", "corona", "casco_romano", "vaquero", "casco_obra", "chef", "mago", "pirata", "policia",
             "burbuja", "paja", "piloto")
ACCESORIOS = ("lentes", "gafas_sol", "auriculares", "bigote", "barba", "parche", "corbata", "estetoscopio", "medalla",
              "charreteras", "alas")

CANOSO, NEGRO, RUBIO, PELIRROJO = (0.78, 0.78, 0.8), (0.16, 0.14, 0.14), (0.93, 0.76, 0.35), (0.85, 0.38, 0.16)

VESTUARIOS = {
    "casual":      dict(ropa="sudadera", color=SUDADERA_BLANCA),
    "estudiante":  dict(ropa="sudadera", color=(0.30, 0.50, 0.85)),
    "doctor":      dict(ropa="bata", color=(0.97, 0.97, 0.98), color2=(0.55, 0.78, 0.92), accesorios=("estetoscopio",)),
    "cientifico":  dict(ropa="bata", color=(0.97, 0.97, 0.98), color2=(0.45, 0.62, 0.45), accesorios=("lentes",),
                        peinado="picos", pelo=CANOSO),
    "ejecutivo":   dict(ropa="traje", color=(0.22, 0.25, 0.33), color2=(0.82, 0.16, 0.18), peinado="corto"),
    "policia":     dict(ropa="uniforme", color=(0.20, 0.32, 0.58), sombrero="policia", peinado="corto"),
    "soldado":     dict(ropa="uniforme", color=(0.38, 0.45, 0.28), sombrero="casco_obra", color_sombrero=(0.35, 0.42, 0.26),
                        peinado="corto"),
    "rey":         dict(ropa="tunica", color=(0.48, 0.20, 0.60), color2=(0.85, 0.65, 0.15), sombrero="corona",
                        capa=(0.80, 0.12, 0.15), accesorios=("barba",)),
    "reina":       dict(ropa="vestido", color=(0.48, 0.20, 0.60), color2=(0.85, 0.65, 0.15), sombrero="corona",
                        peinado="largo", capa=(0.80, 0.12, 0.15)),
    "romano":      dict(ropa="armadura", color=(0.80, 0.62, 0.30), color2=(0.78, 0.14, 0.14), sombrero="casco_romano",
                        capa=(0.78, 0.14, 0.14)),
    "caballero":   dict(ropa="armadura", color=(0.72, 0.74, 0.78), color2=(0.20, 0.35, 0.70), capa=(0.20, 0.35, 0.70)),
    "griego":      dict(ropa="tunica", color=(0.95, 0.93, 0.86), color2=(0.70, 0.55, 0.25), accesorios=("barba",)),
    "vaquero":     dict(ropa="camisa", color=(0.78, 0.35, 0.22), sombrero="vaquero", accesorios=("bigote",)),
    "granjero":    dict(ropa="overol", color=(0.28, 0.42, 0.68), color2=(0.85, 0.25, 0.22), sombrero="paja"),
    "obrero":      dict(ropa="overol", color=(0.95, 0.55, 0.15), color2=(0.30, 0.45, 0.70), sombrero="casco_obra"),
    "chef":        dict(ropa="bata", color=(0.98, 0.98, 0.98), color2=(0.98, 0.98, 0.98), sombrero="chef",
                        accesorios=("bigote",)),
    "mago":        dict(ropa="tunica", color=(0.22, 0.25, 0.60), color2=(0.85, 0.70, 0.20), sombrero="mago",
                        pelo=CANOSO, accesorios=("barba",)),
    "pirata":      dict(ropa="camisa", color=(0.95, 0.93, 0.86), color2=(0.55, 0.12, 0.12), sombrero="pirata",
                        accesorios=("parche", "barba"), pelo=NEGRO),
    "astronauta":  dict(ropa="espacial", color=(0.95, 0.95, 0.96), sombrero="burbuja", peinado="corto"),
    "piloto":      dict(ropa="traje", color=(0.13, 0.17, 0.30), color2=(0.10, 0.10, 0.12), sombrero="piloto",
                        accesorios=("charreteras", "alas"), peinado="corto"),
    "presidente":  dict(ropa="traje", color=(0.16, 0.20, 0.36), color2=(0.20, 0.40, 0.80), peinado="corto",
                        pelo=CANOSO, accesorios=("medalla",)),
    "agente":      dict(ropa="traje", color=(0.10, 0.10, 0.12), color2=(0.10, 0.10, 0.12), peinado="corto",
                        pelo=NEGRO, accesorios=("gafas_sol",)),
    "deportista":  dict(ropa="camiseta", color=(0.90, 0.20, 0.20), sombrero="gorra", color_sombrero=(0.90, 0.20, 0.20)),
    "abuelo":      dict(ropa="camisa", color=(0.62, 0.55, 0.42), peinado="calvo", pelo=CANOSO, accesorios=("lentes", "bigote")),
    "abuela":      dict(ropa="vestido", color=(0.55, 0.62, 0.78), peinado="chongo", pelo=CANOSO, accesorios=("lentes",)),
    "nina":        dict(ropa="vestido", color=(0.95, 0.45, 0.60), peinado="largo"),
}


def habla_desde_audio(ruta, fps=FPS):
    """Lee un audio (wav, mp3…) y devuelve la apertura de la boca por cuadro (0..1) para sincronizar labios."""
    crudo = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", ruta, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                           capture_output=True, check=True).stdout
    a = np.frombuffer(crudo, np.int16).astype(np.float32) / 32768
    paso = 16000 // fps
    n = len(a) // paso
    rms = np.sqrt((a[:n * paso].reshape(n, paso) ** 2).mean(axis=1) + 1e-9)
    ref = np.percentile(rms, 95) or 1
    env = np.clip((rms / ref - 0.12) / 0.7, 0, 1)
    return np.convolve(env, [0.25, 0.5, 0.25], mode="same")


class Personaje(Monigote):
    """Monigote estilo «cabezón»: cabeza blanca grande con sombreado frío, cejas gruesas expresivas, extremidades
    de palito, manos y pies negros, y vestuario según la historia. Usa las mismas claves y poses que Monigote.

    vestuario: nombre de VESTUARIOS ("doctor", "rey", "romano"…); los demás parámetros lo ajustan.
    ropa: una de ROPAS · peinado: uno de PEINADOS · sombrero: uno de SOMBREROS o None
    accesorios: tupla con ACCESORIOS · capa: color (r,g,b) o None · color/color2: colores de la ropa
    habla: ruta de audio (sincroniza la boca con la voz) o lista de tramos [(t0, t1), ...] en que habla.

    Caras: feliz, picaro (sonrisa de lado, una ceja alzada), sorpresa, triste, serio, pensar, enojado.
    """
    def __init__(self, claves, escala=1.0, vestuario="casual", ropa=None, color=None, color2=None, pelo=None,
                 peinado=None, sombrero=None, color_sombrero=None, accesorios=None, capa=None, habla=None,
                 sudadera=None, grosor=11, semilla=1):
        # con este personaje «pensar» lleva la mano a la barbilla por delante del cuerpo
        claves = [dict(c, pose="barbilla") if c.get("pose") == "pensar" else c for c in claves]
        super().__init__(claves, escala=escala, grosor=grosor, semilla=semilla)
        v = dict(VESTUARIOS[vestuario])
        for k, val in dict(ropa=ropa, color=color or sudadera, color2=color2, pelo=pelo, peinado=peinado,
                           sombrero=sombrero, color_sombrero=color_sombrero, accesorios=accesorios, capa=capa).items():
            if val is not None: v[k] = val
        self.ropa = v.get("ropa", "sudadera")
        self.color = v.get("color", SUDADERA_BLANCA)
        self.color2 = v.get("color2", (0.85, 0.2, 0.2))
        self.pelo = v.get("pelo", PELO_CAFE)
        self.peinado = v.get("peinado", "picos")
        self.sombrero = v.get("sombrero")
        self.color_sombrero = v.get("color_sombrero")
        self.accesorios = tuple(v.get("accesorios", ()))
        self.capa = v.get("capa")
        self.habla = habla_desde_audio(habla) if isinstance(habla, str) else habla
        self._boca = 0.0
        assert self.ropa in ROPAS and self.peinado in PEINADOS and (self.sombrero is None or self.sombrero in SOMBREROS)

    def apertura_boca(self, t):
        if self.habla is None: return 0.0
        if isinstance(self.habla, np.ndarray):
            i = int(t * FPS); return float(self.habla[i]) if 0 <= i < len(self.habla) else 0.0
        for (t0, t1) in self.habla:
            if t0 <= t < t1: return 0.35 + 0.65 * abs(math.sin(t * 13 + math.sin(t * 5)))
        return 0.0

    def dibujar(self, ctx, t):
        pose, x, y, clave, moviendo = self.estado(t)
        s = self.s
        pose = dict(pose)
        resp = math.sin(t * 2.2 + self.semilla) * 1.5
        pose["torso"] += math.sin(t * 1.3 + self.semilla) * 1.2
        if clave["pose"] == "saludo":
            pose["ad"] += math.sin(t * 12) * 22
        if clave.get("temblar"):                                   # nervios: tiembla todo el cuerpo
            x += math.sin(t * 71) * 4 * s
            for k2 in ("bi", "ai", "bd", "ad"): pose[k2] += math.sin(t * 63 + len(k2)) * 5
        dy = 0
        if moviendo:
            f = t * 9
            pose["mi"] = math.sin(f) * 28; pose["pi"] = pose["mi"] + max(0, math.sin(f - 1.2)) * -30
            pose["md"] = -math.sin(f) * 28; pose["pd"] = pose["md"] + max(0, -math.sin(f - 1.2)) * -30
            pose["bi"] = -10 - math.sin(f) * 22; pose["ai"] = pose["bi"] - 12
            pose["bd"] = 10 + math.sin(f) * 22; pose["ad"] = pose["bd"] + 12
            dy = -abs(math.sin(f)) * 10 * s
        if clave["saltar"]:
            dy = -abs(math.sin(t * 7)) * 70 * s

        T, R = 165 * s, 92 * s                       # largo del torso y radio de la cabeza
        L = dict(brazo=78 * s, ante=72 * s, muslo=92 * s, pierna=88 * s)

        def cadena(o, a1, l1, a2, l2):
            p1 = (o[0] + vec(a1, l1)[0], o[1] + vec(a1, l1)[1])
            return p1, (p1[0] + vec(a2, l2)[0], p1[1] + vec(a2, l2)[1])
        rodi, pie_i = cadena((0, 0), pose["mi"], L["muslo"], pose["pi"], L["pierna"])
        rodd, pie_d = cadena((0, 0), pose["md"], L["muslo"], pose["pd"], L["pierna"])
        baja = max(pie_i[1], pie_d[1]) + 12 * s
        cad = (x, y + dy + resp - baja)
        tor = pose["torso"]
        cad_i, cad_d = _rel(cad, tor, -22 * s, 0), _rel(cad, tor, 22 * s, 0)
        rodi = (cad_i[0] + rodi[0], cad_i[1] + rodi[1]); pie_i = (cad_i[0] + pie_i[0], cad_i[1] + pie_i[1])
        rodd = (cad_d[0] + rodd[0], cad_d[1] + rodd[1]); pie_d = (cad_d[0] + pie_d[0], cad_d[1] + pie_d[1])
        hom_i, hom_d = _rel(cad, tor, -60 * s, -T + 45 * s), _rel(cad, tor, 60 * s, -T + 45 * s)
        codi, mani = cadena(hom_i, pose["bi"], L["brazo"], pose["ai"], L["ante"])
        codd, mand = cadena(hom_d, pose["bd"], L["brazo"], pose["ad"], L["ante"])
        ang_cab = tor + pose["cabeza"]
        cab = _rel(_rel(cad, tor, 0, -T + 8 * s), ang_cab, 0, -R * 0.82)

        # sombra en el suelo
        ctx.save(); ctx.set_source_rgba(0, 0, 0, 0.13)
        ctx.translate(x, y); ctx.scale(1, 0.16); ctx.arc(0, 0, 95 * s * (1 - min(-dy, 80) / 200), 0, 2 * math.pi)
        ctx.fill(); ctx.restore()

        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        self._boca = self.apertura_boca(t)
        if self.capa: self._capa(ctx, cad, tor, T, s)
        j = lambda p, n: (p[0] + temblor((self.semilla, n), t, 0.8)[0], p[1] + temblor((self.semilla, n), t, 0.8)[1])
        palo = lambda pts, n: (ctx.move_to(*j(pts[0], n)), ctx.line_to(*j(pts[1], n + 1)),
                               ctx.line_to(*j(pts[2], n + 2)), ctx.stroke())
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(self.g * s)
        # piernas y pies (los pies apuntan hacia afuera, o hacia donde mira)
        for n, (c0, ro, pie, lado) in enumerate([(cad_i, rodi, pie_i, -1), (cad_d, rodd, pie_d, 1)]):
            palo((c0, ro, pie), 10 + n * 3)
            hacia = clave["mira"] or lado
            ctx.save(); ctx.translate(pie[0] + hacia * 14 * s, pie[1] + 2 * s); ctx.scale(1, 0.5)
            ctx.arc(0, 0, 25 * s, 0, 2 * math.pi); ctx.restore(); ctx.fill()
        # brazos y manos; si la mano cruza el cuerpo (p. ej. «pensar»), el brazo va encima de la sudadera
        brazos = [(hom_i, codi, mani), (hom_d, codd, mand)]
        a_t = math.pi - math.radians(tor)
        def cruza(ma):
            dx, dy2 = ma[0] - cad[0], ma[1] - cad[1]
            lx = dx * math.cos(a_t) + dy2 * math.sin(a_t)
            ly = -dx * math.sin(a_t) + dy2 * math.cos(a_t)
            return abs(lx) < 58 * s and -T - 20 * s < ly < 20 * s
        def mano(co, ma):
            ang = math.degrees(math.atan2(ma[0] - co[0], ma[1] - co[1]))
            ctx.save(); ctx.translate(*_rel(ma, ang, 0, 6 * s)); ctx.rotate(math.pi - math.radians(ang))
            ctx.scale(0.8, 1); ctx.arc(0, 0, 15 * s, 0, 2 * math.pi); ctx.restore(); ctx.fill()
        for n, (h, co, ma) in enumerate(brazos):
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(self.g * s); palo((h, co, ma), 20 + n * 3); mano(co, ma)

        self._ropa(ctx, cad, tor, T, s)
        for n, (h, co, ma) in enumerate(brazos):
            if cruza(ma):
                ctx.set_source_rgb(*TINTA); ctx.set_line_width(self.g * s)
                palo((h, co, ma), 20 + n * 3); mano(co, ma)
        if clave.get("lleva"):                                     # objeto en la mano derecha (de la pantalla)
            ctx.save(); ctx.translate(*mand); ctx.scale(s * 0.45, s * 0.45); clave["lleva"](ctx, t, 1.0); ctx.restore()
        self._cabeza(ctx, cab, ang_cab, R, clave, t)

    # -- ropa ----------------------------------------------------------------
    def _capa(self, ctx, cad, tor, T, s):
        ctx.save(); ctx.translate(*cad); ctx.rotate(math.pi - math.radians(tor))
        ctx.move_to(-58 * s, -T + 30 * s); ctx.curve_to(-90 * s, -T + 90 * s, -118 * s, 20 * s, -122 * s, 105 * s)
        ctx.curve_to(-40 * s, 118 * s, 40 * s, 118 * s, 122 * s, 105 * s)
        ctx.curve_to(118 * s, 20 * s, 90 * s, -T + 90 * s, 58 * s, -T + 30 * s); ctx.close_path()
        ctx.set_source_rgb(*[v * 0.78 for v in self.capa]); ctx.fill_preserve()
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(7 * s); ctx.stroke()
        ctx.restore()

    def _ropa(self, ctx, cad, tor, T, s):
        if self.ropa == "sudadera":
            self._sudadera(ctx, cad, tor, T, s)
        else:
            ctx.save(); ctx.translate(*cad); ctx.rotate(math.pi - math.radians(tor))
            self._prenda(ctx, T, s)
            ctx.restore()
        if self.accesorios:
            ctx.save(); ctx.translate(*cad); ctx.rotate(math.pi - math.radians(tor))
            self._accesorios_cuerpo(ctx, T, s)
            ctx.restore()

    def _prenda(self, ctx, T, s):
        T = T / s                      # aquí todas las medidas van sin escala y se multiplican por s al dibujar
        r, col, col2 = self.ropa, self.color, self.color2
        claro = tuple(min(1, v * 0.35 + 0.68) for v in col)
        def tinta(w=7): ctx.set_source_rgb(*TINTA); ctx.set_line_width(w * s); ctx.stroke()
        def poli(pts, relleno, w=5.5):
            ctx.move_to(pts[0][0] * s, pts[0][1] * s)
            for (a, b) in pts[1:]: ctx.line_to(a * s, b * s)
            ctx.close_path(); ctx.set_source_rgb(*relleno); ctx.fill_preserve(); tinta(w)
        def linea(pts, w=5, color=TINTA):
            ctx.move_to(pts[0][0] * s, pts[0][1] * s)
            for (a, b) in pts[1:]: ctx.line_to(a * s, b * s)
            ctx.set_source_rgb(*color); ctx.set_line_width(w * s); ctx.stroke()
        def punto(x, y, rad, relleno):
            ctx.arc(x * s, y * s, rad * s, 0, 2 * math.pi); ctx.set_source_rgb(*relleno); ctx.fill_preserve(); tinta(3)
        largo, abajo = dict(bata=82, vestido=108, tunica=100, overol=44, espacial=30, armadura=14).get(r, (14)), \
            dict(bata=86, vestido=118, tunica=100, overol=72, espacial=82).get(r, 68)
        top = -T + 24
        if r == "armadura":   # faldón de tiras debajo de la coraza
            for i in range(-3, 4):
                ctx.rectangle((i * 19 - 9) * s, -10 * s, 18 * s, 70 * s)
                ctx.set_source_rgb(*col2); ctx.fill_preserve(); tinta(4)
        def cuerpo(dx=0, dy=0):
            ancho_pecho = 84 if r != "espacial" else 92
            ctx.move_to((-64 + dx) * s, (top + dy) * s)
            ctx.curve_to((-ancho_pecho + dx) * s, (-T + 70 + dy) * s, (-max(74, abajo * 0.8) + dx) * s, (-30 + dy) * s,
                         (-abajo + dx) * s, (largo + dy) * s)
            if largo > 40:
                ctx.curve_to((-abajo * 0.4 + dx) * s, (largo + 8 + dy) * s, (abajo * 0.4 + dx) * s, (largo + 8 + dy) * s,
                             (abajo + dx) * s, (largo + dy) * s)
            else:
                ctx.line_to((abajo + dx) * s, (largo + dy) * s)
            ctx.curve_to((max(74, abajo * 0.8) + dx) * s, (-30 + dy) * s, (ancho_pecho + dx) * s, (-T + 70 + dy) * s,
                         (64 + dx) * s, (top + dy) * s)
            ctx.curve_to((30 + dx) * s, (top - 8 + dy) * s, (-30 + dx) * s, (top - 8 + dy) * s, (-64 + dx) * s, (top + dy) * s)
            ctx.close_path()
        # cuerpo con sombra a la izquierda y abajo (la tela iluminada se corre arriba a la derecha)
        cuerpo(); ctx.set_source_rgb(*[v * 0.84 for v in col]); ctx.fill_preserve(); ctx.save(); ctx.clip()
        cuerpo(12, -10); ctx.set_source_rgb(*col); ctx.fill()
        if r == "overol":     # camisa debajo del peto
            ctx.rectangle(-100 * s, -T * s, 200 * s, 92 * s); ctx.set_source_rgb(*col2); ctx.fill()
            ctx.rectangle(-100 * s, -T * s, 26 * s, 92 * s); ctx.set_source_rgb(*[v * 0.84 for v in col2]); ctx.fill()
        ctx.restore(); cuerpo(); tinta()

        if r == "camiseta":
            ctx.save(); ctx.translate(0, (top + 4) * s); ctx.scale(1, 0.4); ctx.arc(0, 0, 36 * s, 0, 2 * math.pi)
            ctx.restore(); ctx.set_source_rgb(*[v * 0.6 for v in col]); ctx.fill_preserve(); tinta(5)
            linea([(-50, -T + 90), (-40, -T + 96)], 4); linea([(-66, 2), (66, 2)], 4)
        if r in ("camisa", "uniforme"):
            linea([(0, top + 18), (0, 12)], 4)
            for yy in (-T + 70, -T + 100, -T + 130): punto(0, yy, 4.5, claro)
            for lado in (-1, 1): poli([(0, top + 22), (lado * 40, top - 4), (lado * 46, top + 22)], claro)
            if r == "uniforme":
                for lado in (-1, 1):
                    poli([(lado * 20, -T + 66), (lado * 52, -T + 66), (lado * 50, -T + 96), (lado * 22, -T + 96)], col, 4)
                    linea([(lado * 20, -T + 74), (lado * 52, -T + 74)], 3.5)
                self._estrella(ctx, -36 * s, (-T + 58) * s, 14 * s, (0.95, 0.78, 0.2))
                ctx.rectangle(-70 * s, -8 * s, 140 * s, 18 * s); ctx.set_source_rgb(0.15, 0.13, 0.12); ctx.fill()
                ctx.rectangle(-12 * s, -10 * s, 24 * s, 22 * s); ctx.set_source_rgb(0.92, 0.75, 0.25); ctx.fill_preserve(); tinta(3)
        if r == "traje":
            poli([(0, -T + 120), (-30, top - 2), (30, top - 2)], (0.97, 0.97, 0.97), 5)
            self._corbata(ctx, T, s, col2, largo_c=94)
            for lado in (-1, 1):
                poli([(lado * 30, top - 2), (lado * 46, top + 30), (lado * 22, top + 40), (0, -T + 120), (lado * 10, -T + 60)],
                     [v * 0.9 for v in col], 4.5)
            for yy in (-T + 132, -T + 152): punto(6, yy, 5, [v * 0.6 for v in col])
            linea([(-58, -T + 110), (-34, -T + 110)], 4); linea([(34, -T + 82), (54, -T + 82)], 4)
        if r == "bata":
            poli([(0, -T + 112), (-28, top - 2), (28, top - 2)], col2, 5)
            for lado in (-1, 1):
                poli([(lado * 28, top - 2), (lado * 50, top + 26), (lado * 26, top + 34), (lado * 2, -T + 112)], claro, 4.5)
            linea([(2, -T + 112), (2, largo - 2)], 5)
            for lado in (-1, 1):
                poli([(lado * 24, 0), (lado * 62, 0), (lado * 62, 30), (lado * 24, 30)], col, 4)
            poli([(-56, -T + 74), (-28, -T + 74), (-28, -T + 98), (-56, -T + 98)], col, 4)
            linea([(-48, -T + 80), (-48, -T + 64)], 5, (0.2, 0.35, 0.8))
        if r == "vestido":
            ctx.arc(0, (top - 4) * s, 34 * s, math.radians(20), math.radians(160)); tinta(5)
            ctx.rectangle(-76 * s, -62 * s, 152 * s, 16 * s); ctx.set_source_rgb(*col2); ctx.fill_preserve(); tinta(4.5)
            for xx in (-60, -22, 22, 60): linea([(xx * 0.5, -40), (xx, largo - 6)], 3.5, [v * 0.7 for v in col])
        if r == "tunica":
            linea([(-26, top + 2), (0, top + 46), (26, top + 2)], 5)
            ctx.rectangle(-78 * s, -36 * s, 156 * s, 18 * s); ctx.set_source_rgb(*col2); ctx.fill_preserve(); tinta(4.5)
            punto(0, -27, 9, [min(1, v * 1.2) for v in col2])
            for xx in (-60, -25, 25, 60): linea([(xx * 0.6, -10), (xx, largo - 6)], 3.5, [v * 0.72 for v in col])
        if r == "armadura":
            for yy in (-T + 80, -T + 110, -T + 138, -14):
                ctx.move_to(-74 * s, yy * s); ctx.curve_to(-30 * s, (yy + 10) * s, 30 * s, (yy + 10) * s, 74 * s, yy * s)
                tinta(4.5)
            ctx.rectangle(18 * s, (top + 10) * s, 12 * s, (14 - top - 20) * s)
            ctx.set_source_rgba(1, 1, 1, 0.45); ctx.fill()
            for lado in (-1, 1):
                ctx.arc(lado * 64 * s, (-T + 42) * s, 28 * s, math.pi, 2 * math.pi); ctx.close_path()
                ctx.set_source_rgb(*col); ctx.fill_preserve(); tinta(5)
        if r == "overol":
            poli([(-44, -T + 78), (44, -T + 78), (44, 0), (-44, 0)], col, 5)
            for lado in (-1, 1):
                linea([(lado * 38, -T + 80), (lado * 52, top + 2)], 15); linea([(lado * 38, -T + 80), (lado * 52, top + 2)], 7, col)
                punto(lado * 36, -T + 86, 6, (0.95, 0.78, 0.2))
            poli([(-22, -T + 100), (22, -T + 100), (20, -T + 130), (-20, -T + 130)], col, 4)
            linea([(0, 6), (0, largo - 2)], 4)
        if r == "espacial":
            poli([(-32, -T + 68), (32, -T + 68), (32, -T + 108), (-32, -T + 108)], (0.62, 0.66, 0.72), 4.5)
            for i, c in enumerate([(0.9, 0.2, 0.2), (0.2, 0.7, 0.3), (0.2, 0.45, 0.9)]): punto(-18 + i * 18, -T + 88, 6, c)
            ctx.rectangle(-82 * s, -14 * s, 164 * s, 16 * s); ctx.set_source_rgb(0.62, 0.66, 0.72); ctx.fill_preserve(); tinta(4.5)
            ctx.save(); ctx.translate(0, (top + 4) * s); ctx.scale(1, 0.38); ctx.arc(0, 0, 70 * s, 0, 2 * math.pi)
            ctx.restore(); ctx.set_source_rgb(0.62, 0.66, 0.72); ctx.fill_preserve(); tinta(5)
        if r in ("camisa", "camiseta", "uniforme", "traje") and "corbata" in self.accesorios and r != "traje":
            self._corbata(ctx, T, s, col2)

    def _corbata(self, ctx, T, s, color, largo_c=100):   # T sin escala
        top = -T + 24
        ctx.move_to(-9 * s, (top + 10) * s); ctx.line_to(9 * s, (top + 10) * s); ctx.line_to(6 * s, (top + 24) * s)
        ctx.line_to(14 * s, (top + largo_c) * s); ctx.line_to(0, (top + largo_c + 14) * s); ctx.line_to(-14 * s, (top + largo_c) * s)
        ctx.line_to(-6 * s, (top + 24) * s); ctx.close_path()
        ctx.set_source_rgb(*color); ctx.fill_preserve(); ctx.set_source_rgb(*TINTA); ctx.set_line_width(4.5 * s); ctx.stroke()

    def _estrella(self, ctx, x, y, rad, color):
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5; rr = rad if i % 2 == 0 else rad * 0.45
            (ctx.move_to if i == 0 else ctx.line_to)(x + math.cos(a) * rr, y + math.sin(a) * rr)
        ctx.close_path(); ctx.set_source_rgb(*color); ctx.fill_preserve()
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(rad * 0.22); ctx.stroke()

    def _accesorios_cuerpo(self, ctx, T, s):
        T = T / s
        top = -T + 24
        if "estetoscopio" in self.accesorios:
            ctx.move_to(-34 * s, (top + 2) * s)
            ctx.curve_to(-30 * s, (top + 90) * s, 30 * s, (top + 90) * s, 30 * s, (top + 2) * s)
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(10 * s); ctx.stroke_preserve()
            ctx.set_source_rgb(0.35, 0.37, 0.42); ctx.set_line_width(5 * s); ctx.stroke()
            ctx.move_to(14 * s, (top + 64) * s); ctx.line_to(30 * s, (top + 100) * s)
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(5 * s); ctx.stroke()
            ctx.arc(30 * s, (top + 108) * s, 11 * s, 0, 2 * math.pi); ctx.set_source_rgb(0.75, 0.77, 0.8)
            ctx.fill_preserve(); ctx.set_source_rgb(*TINTA); ctx.set_line_width(4 * s); ctx.stroke()
        if "charreteras" in self.accesorios:
            for lado in (-1, 1):
                ctx.save(); ctx.translate(lado * 58 * s, (top + 14) * s); ctx.rotate(lado * 0.35)
                ctx.rectangle(-22 * s, -8 * s, 44 * s, 16 * s); ctx.set_source_rgb(0.12, 0.12, 0.16); ctx.fill_preserve()
                ctx.set_source_rgb(*TINTA); ctx.set_line_width(3.5 * s); ctx.stroke()
                for k in (-8, 0, 8):
                    ctx.move_to(k * s, -6 * s); ctx.line_to(k * s, 6 * s)
                    ctx.set_source_rgb(0.95, 0.78, 0.2); ctx.set_line_width(3.5 * s); ctx.stroke()
                ctx.restore()
        if "alas" in self.accesorios:
            ctx.save(); ctx.translate(-40 * s, (top + 50) * s)
            for lado in (-1, 1):
                ctx.move_to(0, 0); ctx.curve_to(lado * 10 * s, -10 * s, lado * 22 * s, -8 * s, lado * 28 * s, -6 * s)
                ctx.curve_to(lado * 20 * s, 0, lado * 10 * s, 4 * s, 0, 4 * s); ctx.close_path()
                ctx.set_source_rgb(0.95, 0.78, 0.2); ctx.fill_preserve()
                ctx.set_source_rgb(*TINTA); ctx.set_line_width(2.5 * s); ctx.stroke()
            ctx.arc(0, 0, 6 * s, 0, 2 * math.pi); ctx.set_source_rgb(0.95, 0.78, 0.2); ctx.fill_preserve()
            ctx.set_source_rgb(*TINTA); ctx.stroke(); ctx.restore()
        if "medalla" in self.accesorios:
            ctx.move_to(-46 * s, (top + 30) * s); ctx.line_to(-36 * s, (top + 56) * s); ctx.line_to(-26 * s, (top + 30) * s)
            ctx.set_source_rgb(0.2, 0.4, 0.85); ctx.set_line_width(8 * s); ctx.stroke()
            ctx.arc(-36 * s, (top + 64) * s, 12 * s, 0, 2 * math.pi); ctx.set_source_rgb(0.95, 0.78, 0.2)
            ctx.fill_preserve(); ctx.set_source_rgb(*TINTA); ctx.set_line_width(4 * s); ctx.stroke()

    def _sudadera(self, ctx, cad, tor, T, s):
        ctx.save(); ctx.translate(*cad); ctx.rotate(math.pi - math.radians(tor))
        col, sombra = self.color, tuple(v * 0.86 for v in self.color)
        lw = 7 * s
        def tinta(w=lw): ctx.set_source_rgb(*TINTA); ctx.set_line_width(w); ctx.stroke()
        # cuerpo de la sudadera
        def cuerpo():
            ctx.move_to(-64 * s, -T + 24 * s)
            ctx.curve_to(-84 * s, -T + 70 * s, -74 * s, -40 * s, -68 * s, 14 * s)
            ctx.line_to(68 * s, 14 * s)
            ctx.curve_to(74 * s, -40 * s, 84 * s, -T + 70 * s, 64 * s, -T + 24 * s); ctx.close_path()
        cuerpo(); ctx.set_source_rgb(*col); ctx.fill_preserve(); ctx.save(); ctx.clip()
        ctx.set_source_rgb(*sombra)                      # sombreado lateral, como en el dibujo
        ctx.rectangle(-90 * s, -T, 30 * s, T + 30 * s); ctx.fill()
        ctx.move_to(-60 * s, -T + 60 * s); ctx.curve_to(-20 * s, -T + 48 * s, 20 * s, -T + 48 * s, 60 * s, -T + 60 * s)
        ctx.line_to(60 * s, -T + 30 * s); ctx.line_to(-60 * s, -T + 30 * s); ctx.close_path(); ctx.fill()
        ctx.restore(); cuerpo(); tinta()
        # resorte de abajo
        ctx.rectangle(-69 * s, 2 * s, 138 * s, 18 * s); ctx.set_source_rgb(*col); ctx.fill_preserve(); tinta(6 * s)
        # bolsillo canguro
        ctx.move_to(-38 * s, -6 * s); ctx.line_to(-30 * s, -50 * s); ctx.line_to(30 * s, -50 * s)
        ctx.line_to(38 * s, -6 * s); tinta(5.5 * s)
        ctx.set_source_rgba(*SOMBRA_FRIA, 0.9); ctx.rectangle(-30 * s, -48 * s, 60 * s, 8 * s); ctx.fill()
        # capucha (rodea el cuello)
        ctx.save(); ctx.translate(0, -T + 22 * s); ctx.scale(1, 0.48)
        ctx.arc(0, 0, 76 * s, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgb(*col); ctx.fill_preserve(); tinta()
        ctx.save(); ctx.translate(0, -T + 16 * s); ctx.scale(1, 0.42); ctx.arc(0, 0, 42 * s, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgb(*SOMBRA_FRIA); ctx.fill_preserve(); tinta(5 * s)
        # cordones con puntas
        for lado in (-1, 1):
            ctx.move_to(lado * 16 * s, -T + 32 * s)
            ctx.curve_to(lado * 19 * s, -T + 55 * s, lado * 14 * s, -T + 75 * s, lado * 17 * s, -T + 92 * s)
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(9 * s); ctx.stroke_preserve()
            ctx.set_source_rgb(*col); ctx.set_line_width(4.5 * s); ctx.stroke()
            ctx.save(); ctx.translate(lado * 17 * s, -T + 98 * s); ctx.scale(0.75, 1)
            ctx.arc(0, 0, 7 * s, 0, 2 * math.pi); ctx.restore()
            ctx.set_source_rgb(*col); ctx.fill_preserve(); tinta(3.5 * s)
        ctx.restore()

    # -- cabeza ----------------------------------------------------------------
    def _cabeza(self, ctx, c, ang, r, clave, t):
        ctx.save(); ctx.translate(*c); ctx.rotate(math.pi - math.radians(ang))
        if self.peinado == "largo":                                   # melena detrás de la cabeza
            ctx.move_to(-0.9 * r, -0.5 * r); ctx.curve_to(-1.15 * r, 0.2 * r, -1.1 * r, 0.8 * r, -1.0 * r, 1.05 * r)
            ctx.curve_to(-0.4 * r, 1.15 * r, 0.4 * r, 1.15 * r, 1.0 * r, 1.05 * r)
            ctx.curve_to(1.1 * r, 0.8 * r, 1.15 * r, 0.2 * r, 0.9 * r, -0.5 * r); ctx.close_path()
            ctx.set_source_rgb(*[v * 0.85 for v in self.pelo]); ctx.fill_preserve()
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(6.5 * self.s); ctx.stroke()
        if self.peinado == "chongo":
            ctx.arc(0.1 * r, -1.08 * r, 0.36 * r, 0, 2 * math.pi); ctx.set_source_rgb(*self.pelo); ctx.fill_preserve()
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(6.5 * self.s); ctx.stroke()
        ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.save(); ctx.clip()
        ctx.set_source_rgb(*SOMBRA_FRIA); ctx.paint()                  # sombra fría abajo a la izquierda
        ctx.set_source_rgb(1, 1, 1); ctx.arc(r * 0.13, -r * 0.12, r * 0.96, 0, 2 * math.pi); ctx.fill()
        ctx.restore()
        ctx.arc(0, 0, r, 0, 2 * math.pi); ctx.set_source_rgb(*TINTA); ctx.set_line_width(8 * self.s); ctx.stroke()
        {"picos": self._pelo, "largo": self._pelo, "corto": self._pelo_corto, "chongo": self._pelo_corto,
         "calvo": self._pelo_calvo}[self.peinado](ctx, r)
        ox = clave["mira"] * r * 0.16
        if "barba" in self.accesorios: self._barba(ctx, r, ox)
        self._cara2(ctx, r, clave["cara"], ox, t)
        self._accesorios_cara(ctx, r, ox)
        if self.sombrero: self._sombrero(ctx, r, clave["mira"])
        ctx.restore()

    def _trazo(self, ctx, relleno, w=6.5):
        ctx.set_source_rgb(*relleno); ctx.fill_preserve()
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(w * self.s); ctx.stroke()

    def _pelo_corto(self, ctx, r):
        ctx.move_to(-0.96 * r, -0.25 * r)
        ctx.curve_to(-1.02 * r, -0.95 * r, -0.4 * r, -1.12 * r, 0.1 * r, -1.08 * r)
        ctx.curve_to(0.7 * r, -1.05 * r, 1.05 * r, -0.7 * r, 0.97 * r, -0.22 * r)
        ctx.curve_to(0.85 * r, -0.5 * r, 0.7 * r, -0.6 * r, 0.45 * r, -0.62 * r)
        ctx.curve_to(0.2 * r, -0.5 * r, -0.05 * r, -0.7 * r, -0.3 * r, -0.6 * r)
        ctx.curve_to(-0.6 * r, -0.62 * r, -0.85 * r, -0.5 * r, -0.96 * r, -0.25 * r); ctx.close_path()
        self._trazo(ctx, self.pelo)

    def _pelo_calvo(self, ctx, r):
        for lado in (-1, 1):
            ctx.move_to(lado * 0.98 * r, -0.05 * r); ctx.curve_to(lado * 1.12 * r, -0.2 * r, lado * 1.08 * r, -0.45 * r,
                                                                   lado * 0.9 * r, -0.5 * r)
            ctx.curve_to(lado * 0.92 * r, -0.35 * r, lado * 0.9 * r, -0.2 * r, lado * 0.98 * r, -0.05 * r); ctx.close_path()
            self._trazo(ctx, self.pelo, 5)
        ctx.set_source_rgba(1, 1, 1, 0.9); ctx.arc(0.3 * r, -0.72 * r, 0.1 * r, 0, 2 * math.pi); ctx.fill()

    def _barba(self, ctx, r, ox):
        ctx.save(); ctx.arc(0, 0, r * 1.02, 0, 2 * math.pi); ctx.clip()
        ctx.move_to(-0.98 * r, 0.0); ctx.curve_to(-0.6 * r, 0.25 * r, -0.4 * r, 0.22 * r, ox, 0.22 * r)
        ctx.curve_to(0.4 * r, 0.22 * r, 0.6 * r, 0.25 * r, 0.98 * r, 0.0)
        ctx.line_to(r * 1.2, r * 1.3); ctx.line_to(-r * 1.2, r * 1.3); ctx.close_path()
        ctx.set_source_rgb(*self.pelo); ctx.fill()
        ctx.restore()
        ctx.move_to(-0.98 * r, 0.0); ctx.curve_to(-0.6 * r, 0.25 * r, -0.4 * r, 0.22 * r, ox, 0.22 * r)
        ctx.curve_to(0.4 * r, 0.22 * r, 0.6 * r, 0.25 * r, 0.98 * r, 0.0)
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(5 * self.s); ctx.stroke()
        # hueco claro para que la boca se lea
        ctx.save(); ctx.translate(ox, 0.37 * r); ctx.scale(1, 0.5); ctx.arc(0, 0, 0.3 * r, 0, 2 * math.pi); ctx.restore()
        ctx.set_source_rgb(1, 1, 1); ctx.fill()

    def _accesorios_cara(self, ctx, r, ox):
        ac = self.accesorios
        ctx.set_source_rgb(*TINTA)
        if "lentes" in ac:
            ctx.set_line_width(5 * self.s)
            for lado in (-1, 1):
                ctx.arc(ox * 1.15 + lado * 0.30 * r, -0.04 * r, 0.2 * r, 0, 2 * math.pi); ctx.stroke()
            ctx.move_to(ox * 1.15 - 0.1 * r, -0.08 * r); ctx.curve_to(ox * 1.15 - 0.03 * r, -0.14 * r, ox * 1.15 + 0.03 * r,
                                                                     -0.14 * r, ox * 1.15 + 0.1 * r, -0.08 * r); ctx.stroke()
        if "gafas_sol" in ac:
            for lado in (-1, 1):
                cx2 = ox * 1.15 + lado * 0.30 * r
                ctx.move_to(cx2 - 0.2 * r, -0.16 * r); ctx.line_to(cx2 + 0.2 * r, -0.16 * r)
                ctx.curve_to(cx2 + 0.2 * r, 0.08 * r, cx2 - 0.2 * r, 0.1 * r, cx2 - 0.2 * r, -0.16 * r); ctx.close_path()
                ctx.set_source_rgb(0.06, 0.06, 0.08); ctx.fill()
                ctx.set_source_rgba(1, 1, 1, 0.5); ctx.set_line_width(0.03 * r)
                ctx.move_to(cx2 - 0.1 * r, -0.1 * r); ctx.line_to(cx2 - 0.02 * r, -0.03 * r); ctx.stroke()
            ctx.set_source_rgb(0.06, 0.06, 0.08); ctx.set_line_width(0.05 * r)
            ctx.move_to(ox * 1.15 - 0.12 * r, -0.14 * r); ctx.line_to(ox * 1.15 + 0.12 * r, -0.14 * r); ctx.stroke()
            ctx.move_to(-0.98 * r, -0.12 * r); ctx.line_to(ox * 1.15 - 0.5 * r, -0.15 * r); ctx.stroke()
            ctx.move_to(0.98 * r, -0.12 * r); ctx.line_to(ox * 1.15 + 0.5 * r, -0.15 * r); ctx.stroke()
            ctx.set_source_rgb(*TINTA)
        if "auriculares" in ac:
            ctx.arc(0, -0.1 * r, 1.08 * r, math.radians(195), math.radians(345))
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(0.16 * r); ctx.stroke_preserve()
            ctx.set_source_rgb(0.3, 0.32, 0.36); ctx.set_line_width(0.08 * r); ctx.stroke()
            for lado in (-1, 1):
                ctx.save(); ctx.translate(lado * 1.0 * r, 0.02 * r); ctx.scale(0.6, 1)
                ctx.arc(0, 0, 0.26 * r, 0, 2 * math.pi); ctx.restore(); self._trazo(ctx, (0.25, 0.27, 0.3), 5)
            ctx.move_to(-1.0 * r, 0.15 * r); ctx.curve_to(-0.9 * r, 0.55 * r, -0.6 * r, 0.6 * r, ox - 0.32 * r, 0.42 * r)
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(0.05 * r); ctx.stroke()
            ctx.arc(ox - 0.3 * r, 0.42 * r, 0.07 * r, 0, 2 * math.pi); self._trazo(ctx, (0.25, 0.27, 0.3), 3)
        if "bigote" in ac:
            for lado in (-1, 1):
                ctx.move_to(ox, 0.2 * r)
                ctx.curve_to(ox + lado * 0.15 * r, 0.1 * r, ox + lado * 0.32 * r, 0.14 * r, ox + lado * 0.4 * r, 0.3 * r)
                ctx.curve_to(ox + lado * 0.28 * r, 0.24 * r, ox + lado * 0.14 * r, 0.3 * r, ox, 0.26 * r); ctx.close_path()
                self._trazo(ctx, self.pelo, 3.5)
        if "parche" in ac:
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(4 * self.s)
            ctx.move_to(-0.9 * r, -0.45 * r); ctx.line_to(0.95 * r, 0.15 * r); ctx.stroke()
            ctx.save(); ctx.translate(ox + 0.3 * r, -0.04 * r); ctx.scale(1, 0.85); ctx.arc(0, 0, 0.19 * r, 0, 2 * math.pi)
            ctx.restore(); ctx.fill()

    def _sombrero(self, ctx, r, mira):
        tipo = self.sombrero
        def col(defecto): return self.color_sombrero or defecto
        tr = self._trazo
        if tipo == "gorra":
            ctx.move_to(-0.98 * r, -0.4 * r); ctx.curve_to(-0.95 * r, -1.25 * r, 0.95 * r, -1.25 * r, 0.98 * r, -0.4 * r)
            ctx.curve_to(0.4 * r, -0.52 * r, -0.4 * r, -0.52 * r, -0.98 * r, -0.4 * r); ctx.close_path(); tr(ctx, col((0.85, 0.2, 0.2)))
            d = mira or 1
            ctx.save(); ctx.translate(d * 0.85 * r, -0.44 * r); ctx.scale(1, 0.28); ctx.arc(0, 0, 0.55 * r, 0, 2 * math.pi)
            ctx.restore(); tr(ctx, [v * 0.8 for v in col((0.85, 0.2, 0.2))])
            ctx.arc(0, -1.07 * r, 0.08 * r, 0, 2 * math.pi); tr(ctx, col((0.85, 0.2, 0.2)), 4)
        elif tipo == "corona":
            pts = [(-0.62, -0.72), (-0.66, -1.42), (-0.33, -1.1), (0, -1.5), (0.33, -1.1), (0.66, -1.42), (0.62, -0.72)]
            ctx.move_to(pts[0][0] * r, pts[0][1] * r)
            for (a, b) in pts[1:]: ctx.line_to(a * r, b * r)
            ctx.curve_to(0.3 * r, -0.62 * r, -0.3 * r, -0.62 * r, -0.62 * r, -0.72 * r); ctx.close_path()
            tr(ctx, col((0.95, 0.75, 0.2)))
            for (a, b, c2) in [(-0.33, -0.86, (0.85, 0.15, 0.2)), (0, -0.9, (0.2, 0.45, 0.9)), (0.33, -0.86, (0.2, 0.7, 0.3))]:
                ctx.arc(a * r, b * r, 0.08 * r, 0, 2 * math.pi); tr(ctx, c2, 3)
        elif tipo == "casco_romano":
            ctx.move_to(-0.55 * r, -0.95 * r)                          # penacho rojo
            ctx.curve_to(-0.6 * r, -1.75 * r, 0.6 * r, -1.75 * r, 0.75 * r, -0.95 * r)
            ctx.curve_to(0.3 * r, -1.35 * r, -0.2 * r, -1.35 * r, -0.55 * r, -0.95 * r); ctx.close_path()
            tr(ctx, self.color2 if self.ropa == "armadura" else (0.78, 0.14, 0.14))
            ctx.move_to(-1.0 * r, -0.2 * r); ctx.curve_to(-1.1 * r, -1.3 * r, 1.1 * r, -1.3 * r, 1.0 * r, -0.2 * r)
            ctx.line_to(0.8 * r, -0.2 * r); ctx.curve_to(0.75 * r, -0.55 * r, -0.75 * r, -0.55 * r, -0.8 * r, -0.2 * r)
            ctx.close_path(); tr(ctx, col((0.80, 0.62, 0.30)))
            for lado in (-1, 1):                                      # carrilleras
                ctx.move_to(lado * 0.98 * r, -0.25 * r); ctx.line_to(lado * 0.98 * r, 0.25 * r)
                ctx.line_to(lado * 0.72 * r, 0.15 * r); ctx.line_to(lado * 0.78 * r, -0.25 * r); ctx.close_path()
                tr(ctx, col((0.80, 0.62, 0.30)), 5)
        elif tipo == "vaquero":
            c0 = col((0.55, 0.36, 0.2))
            ctx.save(); ctx.translate(0, -0.72 * r); ctx.scale(1, 0.22); ctx.arc(0, 0, 1.5 * r, 0, 2 * math.pi); ctx.restore()
            tr(ctx, c0)
            ctx.move_to(-0.7 * r, -0.75 * r); ctx.curve_to(-0.8 * r, -1.6 * r, -0.3 * r, -1.5 * r, 0, -1.35 * r)
            ctx.curve_to(0.3 * r, -1.5 * r, 0.8 * r, -1.6 * r, 0.7 * r, -0.75 * r); ctx.close_path(); tr(ctx, c0)
            ctx.rectangle(-0.72 * r, -0.98 * r, 1.44 * r, 0.16 * r); tr(ctx, [v * 0.55 for v in c0], 4)
        elif tipo == "paja":
            c0 = col((0.93, 0.8, 0.45))
            ctx.save(); ctx.translate(0, -0.7 * r); ctx.scale(1, 0.24); ctx.arc(0, 0, 1.45 * r, 0, 2 * math.pi); ctx.restore()
            tr(ctx, c0)
            ctx.move_to(-0.68 * r, -0.74 * r); ctx.curve_to(-0.7 * r, -1.45 * r, 0.7 * r, -1.45 * r, 0.68 * r, -0.74 * r)
            ctx.close_path(); tr(ctx, c0)
            ctx.rectangle(-0.69 * r, -0.95 * r, 1.38 * r, 0.14 * r); tr(ctx, (0.85, 0.25, 0.22), 4)
        elif tipo == "casco_obra":
            c0 = col((0.98, 0.8, 0.15))
            ctx.move_to(-0.95 * r, -0.45 * r); ctx.curve_to(-0.95 * r, -1.35 * r, 0.95 * r, -1.35 * r, 0.95 * r, -0.45 * r)
            ctx.close_path(); tr(ctx, c0)
            ctx.save(); ctx.translate(0, -0.45 * r); ctx.scale(1, 0.16); ctx.arc(0, 0, 1.18 * r, 0, 2 * math.pi); ctx.restore()
            tr(ctx, c0)
            ctx.move_to(0, -1.12 * r); ctx.line_to(0, -0.5 * r); ctx.set_line_width(0.16 * r); ctx.stroke()
            ctx.move_to(0, -1.12 * r); ctx.line_to(0, -0.5 * r); ctx.set_source_rgb(*c0); ctx.set_line_width(0.1 * r)
            ctx.stroke()
        elif tipo == "chef":
            for (a, b, rr) in [(-0.45, -1.35, 0.38), (0.45, -1.35, 0.38), (0, -1.55, 0.45)]:
                ctx.arc(a * r, b * r, rr * r, 0, 2 * math.pi); tr(ctx, (0.98, 0.98, 0.98))
            ctx.rectangle(-0.7 * r, -1.25 * r, 1.4 * r, 0.55 * r); tr(ctx, (0.98, 0.98, 0.98))
        elif tipo == "mago":
            c0 = col((0.22, 0.25, 0.6))
            ctx.move_to(-0.75 * r, -0.75 * r); ctx.curve_to(-0.4 * r, -1.4 * r, 0.1 * r, -1.9 * r, 0.75 * r, -2.25 * r)
            ctx.curve_to(0.4 * r, -1.7 * r, 0.6 * r, -1.2 * r, 0.75 * r, -0.75 * r); ctx.close_path(); tr(ctx, c0)
            ctx.save(); ctx.translate(0, -0.72 * r); ctx.scale(1, 0.2); ctx.arc(0, 0, 1.3 * r, 0, 2 * math.pi); ctx.restore()
            tr(ctx, c0)
            self._estrella(ctx, 0.05 * r, -1.2 * r, 0.16 * r, (0.95, 0.8, 0.2))
            self._estrella(ctx, 0.35 * r, -1.65 * r, 0.1 * r, (0.95, 0.8, 0.2))
        elif tipo == "pirata":
            c0 = col((0.13, 0.12, 0.14))
            ctx.move_to(-1.35 * r, -0.65 * r); ctx.curve_to(-0.9 * r, -1.65 * r, 0.9 * r, -1.65 * r, 1.35 * r, -0.65 * r)
            ctx.curve_to(0.5 * r, -0.95 * r, -0.5 * r, -0.95 * r, -1.35 * r, -0.65 * r); ctx.close_path(); tr(ctx, c0)
            ctx.arc(0, -1.12 * r, 0.14 * r, 0, 2 * math.pi); ctx.set_source_rgb(1, 1, 1); ctx.fill()
            ctx.set_source_rgb(1, 1, 1); ctx.set_line_width(0.05 * r)
            ctx.move_to(-0.18 * r, -0.86 * r); ctx.line_to(0.18 * r, -0.98 * r); ctx.stroke()
            ctx.move_to(-0.18 * r, -0.98 * r); ctx.line_to(0.18 * r, -0.86 * r); ctx.stroke()
        elif tipo == "policia":
            c0 = col((0.18, 0.28, 0.52))
            ctx.move_to(-1.1 * r, -1.05 * r); ctx.curve_to(-0.6 * r, -1.4 * r, 0.6 * r, -1.4 * r, 1.1 * r, -1.05 * r)
            ctx.line_to(0.82 * r, -0.66 * r); ctx.line_to(-0.82 * r, -0.66 * r); ctx.close_path(); tr(ctx, c0)
            ctx.rectangle(-0.84 * r, -0.8 * r, 1.68 * r, 0.2 * r); tr(ctx, (0.12, 0.12, 0.14), 4)
            ctx.save(); ctx.translate(0.2 * (mira or 1) * r, -0.58 * r); ctx.scale(1, 0.25)
            ctx.arc(0, 0, 0.7 * r, 0, math.pi); ctx.restore(); tr(ctx, (0.1, 0.1, 0.12), 4)
            self._estrella(ctx, 0, -1.0 * r, 0.14 * r, (0.95, 0.78, 0.2))
        elif tipo == "piloto":
            c0 = col((0.13, 0.17, 0.30))
            ctx.move_to(-1.12 * r, -1.0 * r); ctx.curve_to(-0.6 * r, -1.38 * r, 0.6 * r, -1.38 * r, 1.12 * r, -1.0 * r)
            ctx.line_to(0.84 * r, -0.66 * r); ctx.line_to(-0.84 * r, -0.66 * r); ctx.close_path(); tr(ctx, c0)
            ctx.rectangle(-0.85 * r, -0.82 * r, 1.7 * r, 0.18 * r); tr(ctx, (0.95, 0.78, 0.2), 4)
            ctx.save(); ctx.translate(0.15 * (mira or 1) * r, -0.6 * r); ctx.scale(1, 0.25)
            ctx.arc(0, 0, 0.72 * r, 0, math.pi); ctx.restore(); tr(ctx, (0.08, 0.08, 0.1), 4)
            ctx.save(); ctx.translate(0, -1.02 * r)
            for lado in (-1, 1):
                ctx.move_to(0, 0); ctx.curve_to(lado * 0.12 * r, -0.12 * r, lado * 0.3 * r, -0.1 * r, lado * 0.4 * r, -0.06 * r)
                ctx.curve_to(lado * 0.28 * r, 0.02 * r, lado * 0.12 * r, 0.06 * r, 0, 0.05 * r); ctx.close_path()
                tr(ctx, (0.95, 0.78, 0.2), 3)
            ctx.restore()
        elif tipo == "burbuja":
            ctx.arc(0, -0.05 * r, 1.32 * r, 0, 2 * math.pi)
            ctx.set_source_rgba(0.75, 0.88, 1.0, 0.28); ctx.fill_preserve()
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(7 * self.s); ctx.stroke()
            ctx.set_source_rgba(1, 1, 1, 0.75); ctx.set_line_width(0.08 * r)
            ctx.arc(-0.1 * r, -0.1 * r, 1.08 * r, math.radians(200), math.radians(250)); ctx.stroke()

    def _pelo(self, ctx, r):
        # contorno en sentido horario: mechones colgando a la izquierda, copete que barre a la derecha
        # y fleco con dos puntas sobre la frente. Las puntas quedan filosas y los tramos se curvan hacia afuera.
        pts = [(-0.97, -0.02), (-0.86, -0.30), (-1.10, -0.44), (-0.90, -0.58), (-0.98, -0.90),
               (-0.62, -0.92), (-0.30, -1.14), (0.20, -1.12), (0.60, -1.06), (1.20, -0.96),
               (0.90, -0.76), (1.10, -0.56), (0.84, -0.52), (0.58, -0.72), (0.30, -0.54),
               (0.08, -0.74), (-0.26, -0.52), (-0.44, -0.70), (-0.72, -0.34)]
        cx0, cy0 = 0.0, -0.35
        ctx.move_to(pts[0][0] * r, pts[0][1] * r)
        for i in range(len(pts)):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
            mx, my = (x0 + x1) / 2 - cx0, (y0 + y1) / 2 - cy0
            d = math.hypot(mx, my) or 1; seg = math.hypot(x1 - x0, y1 - y0)
            fuera = 1 if i < 12 else -0.6                      # el fleco se curva hacia adentro
            ox, oy = mx / d * seg * 0.12 * fuera, my / d * seg * 0.12 * fuera
            ctx.curve_to((x0 + (x1 - x0) / 3 + ox) * r, (y0 + (y1 - y0) / 3 + oy) * r,
                         (x0 + 2 * (x1 - x0) / 3 + ox) * r, (y0 + 2 * (y1 - y0) / 3 + oy) * r, x1 * r, y1 * r)
        ctx.close_path()
        ctx.set_source_rgb(*self.pelo); ctx.fill_preserve(); ctx.save(); ctx.clip()
        ctx.set_source_rgba(*[v * 0.55 for v in self.pelo], 0.85); ctx.set_line_width(3.2 * self.s)
        for (a, b, c2) in [((-0.7, -0.75), (-0.4, -0.95), (0.0, -0.98)), ((-0.2, -0.8), (0.2, -0.95), (0.7, -0.92)),
                           ((-0.85, -0.45), (-0.8, -0.6), (-0.65, -0.75)), ((0.3, -0.72), (0.6, -0.8), (0.95, -0.8))]:
            ctx.move_to(a[0] * r, a[1] * r); ctx.curve_to(b[0] * r, b[1] * r, b[0] * r, b[1] * r, c2[0] * r, c2[1] * r)
            ctx.stroke()
        ctx.restore()
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(6.5 * self.s)
        # repetir el trazo para el contorno
        ctx.move_to(pts[0][0] * r, pts[0][1] * r)
        for i in range(len(pts)):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
            mx, my = (x0 + x1) / 2 - cx0, (y0 + y1) / 2 - cy0
            d = math.hypot(mx, my) or 1; seg = math.hypot(x1 - x0, y1 - y0)
            fuera = 1 if i < 12 else -0.6
            ox, oy = mx / d * seg * 0.12 * fuera, my / d * seg * 0.12 * fuera
            ctx.curve_to((x0 + (x1 - x0) / 3 + ox) * r, (y0 + (y1 - y0) / 3 + oy) * r,
                         (x0 + 2 * (x1 - x0) / 3 + ox) * r, (y0 + 2 * (y1 - y0) / 3 + oy) * r, x1 * r, y1 * r)
        ctx.close_path(); ctx.stroke()

    def _cara2(self, ctx, r, cara, ox, t):
        ctx.set_source_rgb(*TINTA)
        parpadeo = (t + self.semilla * 0.7) % 3.4 < 0.12
        # cejas: (alto de la punta interior, alto de la punta exterior) por lado; negativo = más arriba
        cejas = dict(feliz=((-0.32, -0.36), (-0.32, -0.36)), picaro=((-0.27, -0.31), (-0.36, -0.47)),
                     sorpresa=((-0.50, -0.50), (-0.50, -0.50)), triste=((-0.44, -0.30), (-0.44, -0.30)),
                     serio=((-0.33, -0.36), (-0.33, -0.36)), pensar=((-0.32, -0.34), (-0.46, -0.50)),
                     enojado=((-0.24, -0.40), (-0.24, -0.40))).get(cara, ((-0.36, -0.40), (-0.36, -0.40)))
        for n, lado in enumerate((-1, 1)):
            ex, ey = ox + lado * r * 0.30, -r * 0.04
            yi, ye = cejas[n]
            # ceja gruesa con arco
            xi, xe = ex - lado * r * 0.13, ex + lado * r * 0.20
            ctx.set_line_width(r * 0.095); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(xi, yi * r)
            ctx.curve_to(ex - lado * r * 0.02, (yi + ye) / 2 * r - r * 0.09, ex + lado * r * 0.1, ye * r - r * 0.04, xe, ye * r + r * 0.03)
            ctx.stroke()
            ex2 = ex + ox * 0.15
            if parpadeo and cara != "sorpresa":
                ctx.set_line_width(r * 0.05); ctx.move_to(ex2 - r * 0.08, ey); ctx.line_to(ex2 + r * 0.08, ey); ctx.stroke()
                continue
            alto = 0.16 if cara == "sorpresa" else 0.125
            ctx.save()
            if cara in ("picaro", "serio", "enojado"):            # párpado a media asta: corta la parte de arriba
                ctx.rectangle(ex2 - r * 0.2, ey - r * 0.045, r * 0.4, r * 0.4); ctx.clip()
            ctx.translate(ex2, ey); ctx.scale(0.66, 1); ctx.arc(0, 0, r * alto, 0, 2 * math.pi); ctx.restore(); ctx.fill()
            if cara in ("picaro", "serio", "enojado"):
                ctx.set_line_width(r * 0.045); ctx.set_line_cap(cairo.LINE_CAP_BUTT)
                ctx.move_to(ex2 - r * 0.095, ey - r * 0.045); ctx.line_to(ex2 + r * 0.095, ey - r * 0.045); ctx.stroke()
                ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            else:
                ctx.set_source_rgb(1, 1, 1); ctx.arc(ex2 + r * 0.025, ey - r * 0.055, r * 0.025, 0, 2 * math.pi)
                ctx.fill(); ctx.set_source_rgb(*TINTA)
        mx, my = ox, r * 0.36
        ctx.set_line_width(r * 0.055)
        if self._boca > 0.08 and cara != "sorpresa":                 # hablando: boca abierta según la voz
            k = self._boca
            ctx.save(); ctx.translate(mx, my - r * 0.02); ctx.scale(1, 0.25 + 0.75 * k)
            ctx.arc(0, 0, r * (0.17 + 0.05 * k), 0, math.pi); ctx.close_path(); ctx.restore()
            ctx.set_source_rgb(0.35, 0.08, 0.1); ctx.fill_preserve(); ctx.set_source_rgb(*TINTA); ctx.stroke()
            if k > 0.45:
                ctx.save(); ctx.translate(mx, my + r * 0.09 * k); ctx.scale(1, 0.45); ctx.arc(0, 0, r * 0.09, 0, 2 * math.pi)
                ctx.restore(); ctx.set_source_rgb(0.9, 0.4, 0.45); ctx.fill(); ctx.set_source_rgb(*TINTA)
        elif cara == "feliz":
            ctx.move_to(mx - r * 0.32, my - r * 0.06)
            ctx.curve_to(mx - r * 0.15, my + r * 0.16, mx + r * 0.15, my + r * 0.16, mx + r * 0.32, my - r * 0.06)
            ctx.stroke()
        elif cara == "picaro":                                    # sonrisa de lado
            ctx.move_to(mx - r * 0.34, my - r * 0.04)
            ctx.curve_to(mx - r * 0.18, my + r * 0.12, mx + r * 0.2, my + r * 0.08, mx + r * 0.40, my - r * 0.14)
            ctx.stroke()
            ctx.move_to(mx - r * 0.38, my - r * 0.09); ctx.line_to(mx - r * 0.33, my - r * 0.02); ctx.stroke()
        elif cara == "sorpresa":
            ctx.save(); ctx.translate(mx, my + r * 0.04); ctx.scale(0.8, 1); ctx.arc(0, 0, r * 0.12, 0, 2 * math.pi)
            ctx.restore(); ctx.fill()
        elif cara == "triste":
            ctx.move_to(mx - r * 0.25, my + r * 0.08)
            ctx.curve_to(mx - r * 0.1, my - r * 0.06, mx + r * 0.1, my - r * 0.06, mx + r * 0.25, my + r * 0.08)
            ctx.stroke()
        elif cara == "pensar":
            ctx.move_to(mx - r * 0.2, my); ctx.curve_to(mx - r * 0.05, my - r * 0.08, mx + r * 0.05, my + r * 0.08,
                                                        mx + r * 0.22, my - r * 0.02); ctx.stroke()
        elif cara == "enojado":
            ctx.move_to(mx - r * 0.22, my + r * 0.05); ctx.curve_to(mx - r * 0.1, my - r * 0.03, mx + r * 0.1, my - r * 0.03,
                                                                    mx + r * 0.22, my + r * 0.05); ctx.stroke()
        else:
            ctx.move_to(mx - r * 0.2, my); ctx.line_to(mx + r * 0.2, my); ctx.stroke()


# ---------------------------------------------------------------- utilería
class Elemento:
    """Cualquier dibujo que aparece (pop) y desaparece en un tiempo dado.
    dibujo(ctx, t, k): función que dibuja centrada en (0,0); k = progreso de aparición 0..1."""
    def __init__(self, dibujo, t0, t1, x, y, escala=1.0, mover=None, entrada=0.35, salida=0.25):
        self.f, self.t0, self.t1, self.x, self.y, self.s = dibujo, t0, t1, x, y, escala
        self.mover, self.entrada, self.salida = mover, entrada, salida

    def dibujar(self, ctx, t):
        if not (self.t0 <= t <= self.t1): return
        k_in = rebote((t - self.t0) / self.entrada)
        k_out = max(0.01, suave((self.t1 - t) / self.salida))
        k = min(k_in, 1) * k_out if k_in < 1 else k_out
        esc = self.s * max(0.01, min(k_in, 1.15)) * (0.6 + 0.4 * k_out)
        x, y = (self.mover(t) if self.mover else (self.x, self.y))
        ctx.save(); ctx.translate(x, y); ctx.scale(esc, esc)
        self.f(ctx, t, clamp(k)); ctx.restore()


def contorno(ctx, relleno, grosor=10):
    ctx.set_source_rgb(*relleno); ctx.fill_preserve()
    ctx.set_source_rgb(*TINTA); ctx.set_line_width(grosor); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()


def corazon(color=(0.92, 0.2, 0.25), latido=True):
    def f(ctx, t, k):
        p = 1 + (0.12 * max(0, math.sin(t * 8)) ** 4 if latido else 0)
        ctx.scale(p, p)
        ctx.move_to(0, 60)
        ctx.curve_to(-110, -10, -60, -95, 0, -40)
        ctx.curve_to(60, -95, 110, -10, 0, 60); ctx.close_path()
        contorno(ctx, color)
        ctx.set_source_rgba(1, 1, 1, 0.55); ctx.arc(-38, -30, 12, 0, 2 * math.pi); ctx.fill()
    return f


def texto(txt, tam=90, color=TINTA, borde=None, fuente="Inter"):
    def f(ctx, t, k):
        ctx.select_font_face(fuente, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(tam)
        e = ctx.text_extents(txt)
        ctx.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing)
        ctx.text_path(txt)
        if borde:
            ctx.set_source_rgb(*borde); ctx.set_line_width(tam * 0.18); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
        ctx.set_source_rgb(*color); ctx.fill()
    return f


def burbuja_pensamiento(interior=None):
    def f(ctx, t, k):
        for (bx, by, br) in [(-150, 170, 14), (-115, 130, 22)]:
            ctx.arc(bx, by, br, 0, 2 * math.pi); contorno(ctx, (1, 1, 1), 7)
        ctx.save(); ctx.scale(1.35, 1); ctx.arc(0, 0, 120, 0, 2 * math.pi); ctx.restore()
        contorno(ctx, (1, 1, 1), 9)
        if interior: interior(ctx, t, k)
    return f


def gota(color=(0.2, 0.45, 0.95)):
    def f(ctx, t, k):
        ctx.move_to(0, -110); ctx.curve_to(40, -40, 80, 0, 80, 40)
        ctx.curve_to(80, 95, -80, 95, -80, 40); ctx.curve_to(-80, 0, -40, -40, 0, -110); ctx.close_path()
        contorno(ctx, color)
        ctx.set_source_rgba(1, 1, 1, 0.6); ctx.arc(-35, 35, 14, 0, 2 * math.pi); ctx.fill()
    return f


def pulpo(color=(0.95, 0.45, 0.55), nadar=False, corazones=0, sangre_azul=False):
    """corazones: 0 = ninguno visible, 2 = los de las branquias, 3 = todos."""
    def f(ctx, t, k):
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ondula = 4 if nadar else 1.6
        # tentáculos
        for i in range(8):
            base = -105 + i * 30
            ctx.move_to(base * 0.8, 40)
            pts = []
            for s in range(1, 9):
                yy = 40 + s * 24 * (1.25 if nadar else 1)
                xx = base * (0.8 + s * (0.04 if nadar else 0.12)) + math.sin(t * ondula + i + s * 0.7) * (6 + s * 3)
                pts.append((xx, yy))
            for p in pts: ctx.line_to(*p)
            ctx.set_source_rgb(*TINTA); ctx.set_line_width(30); ctx.stroke_preserve()
            ctx.set_source_rgb(*color); ctx.set_line_width(19); ctx.stroke()
        # cabeza
        ctx.save(); ctx.scale(1, 1.15); ctx.arc(0, -60, 130, 0, 2 * math.pi); ctx.restore()
        contorno(ctx, color, 10)
        # manchas
        ctx.set_source_rgba(0.8, 0.25, 0.4, 0.5)
        for (mx, my, mr) in [(-55, -150, 16), (45, -170, 11), (70, -100, 13), (-80, -80, 9)]:
            ctx.arc(mx, my, mr, 0, 2 * math.pi); ctx.fill()
        # ojos
        for lado in (-1, 1):
            ctx.arc(lado * 50, 0, 30, 0, 2 * math.pi); contorno(ctx, (1, 1, 1), 7)
            ctx.set_source_rgb(*TINTA); ctx.arc(lado * 50 + 6, 4, 13, 0, 2 * math.pi); ctx.fill()
        ctx.set_line_width(8); ctx.arc(0, 45, 22, math.radians(20), math.radians(160)); ctx.stroke()
        # corazones internos
        if corazones:
            col = (0.2, 0.45, 0.95) if sangre_azul else (0.92, 0.2, 0.25)
            pos = [(-95, -95, 0.32), (95, -95, 0.32)] + ([(0, -125, 0.5)] if corazones >= 3 else [])
            for (hx, hy, hs) in pos:
                ctx.save(); ctx.translate(hx, hy); ctx.scale(hs, hs); corazon(col)(ctx, t, k); ctx.restore()
    return f


def burbujas_agua(semilla=3, n=14):
    rnd = random.Random(semilla)
    datos = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(8, 26), rnd.uniform(60, 160)) for _ in range(n)]
    def f(ctx, t, k):
        ctx.set_line_width(4)
        for (bx, by, br, vel) in datos:
            y = (by - t * vel) % (H + 100) - 50
            ctx.arc(bx + math.sin(t * 2 + by) * 12, y, br, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 0.35); ctx.fill_preserve(); ctx.set_source_rgba(1, 1, 1, 0.8); ctx.stroke()
    return f


# ---------------------------------------------------------------- fondo y subtítulos
class Fondo:
    """Cambia de color por tramos: [(t, (r,g,b)), ...]; 'suelo' dibuja la línea del piso."""
    def __init__(self, colores, suelo=1350):
        self.colores, self.suelo = colores, suelo

    def dibujar(self, ctx, t):
        c = self.colores[0][1]
        for i, (ti, col) in enumerate(self.colores):
            if t >= ti:
                prev = self.colores[i - 1][1] if i else col
                c = tuple(lerp(p, q, suave((t - ti) / 0.5)) for p, q in zip(prev, col))
        g = cairo.LinearGradient(0, 0, 0, H)
        g.add_color_stop_rgb(0, *[min(1, v + 0.06) for v in c]); g.add_color_stop_rgb(1, *[v * 0.9 for v in c])
        ctx.set_source(g); ctx.paint()
        if self.suelo:
            ctx.set_source_rgba(*TINTA, 0.85); ctx.set_line_width(8); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(60, self.suelo)
            for xx in range(60, W - 59, 60):
                ctx.line_to(xx, self.suelo + temblor(("suelo", xx), t, 2.5)[1])
            ctx.stroke()


class Subtitulos:
    """Subtítulos grandes estilo shorts. Las palabras entre *asteriscos* se resaltan en amarillo.
    lineas: [(t0, t1, "texto"), ...] — las palabras se revelan de una en una dentro del tramo."""
    def __init__(self, lineas, y=430, tam=84, ancho=920):
        self.lineas, self.y, self.tam, self.ancho = lineas, y, tam, ancho

    def _tiempo(self, linea, i):
        t0, t1, txt = linea[:3]
        if len(linea) > 3: return linea[3][i]                      # tiempos exactos (de la transcripción)
        return t0 + (t1 - t0) * 0.85 * i / max(len(txt.split()), 1)

    def palabras_tiempos(self):
        return [self._tiempo(l, i) for l in self.lineas for i in range(len(l[2].split()))]

    def dibujar(self, ctx, t):
        for linea in self.lineas:
            t0, t1, txt = linea[:3]
            if not (t0 <= t < t1): continue
            pal = txt.split()
            ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(self.tam)
            # partir en renglones
            renglones, actual = [], []
            for i, p in enumerate(pal):
                prueba = " ".join(w.replace("*", "") for _, w in actual + [(i, p)])
                if ctx.text_extents(prueba).x_advance > self.ancho and actual:
                    renglones.append(actual); actual = []
                actual.append((i, p))
            renglones.append(actual)
            n = len(pal); sp = ctx.text_extents(" ").x_advance
            for r, ren in enumerate(renglones):
                ancho = sum(ctx.text_extents(w.replace("*", "")).x_advance for _, w in ren) + sp * (len(ren) - 1)
                x = (W - ancho) / 2; y = self.y + r * self.tam * 1.2
                for i, w in ren:
                    ti = self._tiempo(linea, i)
                    limpio = w.replace("*", "")
                    adv = ctx.text_extents(limpio).x_advance
                    if t >= ti:
                        k = max(0.01, rebote((t - ti) / 0.18))
                        ctx.save(); ctx.translate(x + adv / 2, y); ctx.scale(k, k)
                        ctx.move_to(-adv / 2, 0); ctx.text_path(limpio)
                        ctx.set_source_rgb(*TINTA); ctx.set_line_width(self.tam * 0.2)
                        ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke_preserve()
                        ctx.set_source_rgb(*((1, 0.85, 0.1) if "*" in w else (1, 1, 1))); ctx.fill()
                        ctx.restore()
                    x += adv + sp


def subtitulos_desde_palabras(palabras, resaltar=(), max_palabras=4, cambios=()):
    """palabras: [{'w','a','b'}] (de la transcripción). Agrupa en renglones cortos con sus tiempos exactos.
    resaltar: palabras (en minúsculas, sin signos) que salen en amarillo. cambios: {original: corregida}."""
    cambios = dict(cambios); limpio = lambda w: w.strip(".,¡!¿?;:«»'\"").lower()
    grupos, act = [], []
    for i, p in enumerate(palabras):
        act.append(p)
        sig = palabras[i + 1] if i + 1 < len(palabras) else None
        corte = (len(act) >= max_palabras or p["w"][-1:] in ".,?!;:" or sig is None or sig["a"] - p["b"] > 0.35)
        if corte: grupos.append(act); act = []
    lineas = []
    for g, grupo in enumerate(grupos):
        fin = grupos[g + 1][0]["a"] if g + 1 < len(grupos) else grupo[-1]["b"] + 0.8
        fin = min(fin, grupo[-1]["b"] + 0.7)
        pal, tiempos = [], []
        for p in grupo:
            for w in cambios.get(p["w"], p["w"]).split():          # una corrección puede dar varias palabras
                pal.append(f"*{w}*" if limpio(w) in resaltar else w); tiempos.append(p["a"] - 0.05)
        lineas.append((grupo[0]["a"] - 0.05, fin, " ".join(pal), tiempos))
    return lineas


class Tramo:
    """Muestra unas capas solo entre t0 y t1 (una escena). Las capas reciben el tiempo global."""
    def __init__(self, t0, t1, *capas):
        self.t0, self.t1, self.capas = t0, t1, capas

    def dibujar(self, ctx, t):
        if self.t0 <= t < self.t1:
            for c in self.capas: c.dibujar(ctx, t)


class Dibujo:
    """Capa a partir de una función f(ctx, t) (fondos, primeros planos)."""
    def __init__(self, f): self.f = f
    def dibujar(self, ctx, t): ctx.save(); self.f(ctx, t); ctx.restore()


class Foto:
    """Fondo con una foto real, recortada a vertical y preparada una sola vez.

    foco: punto de la foto que queda al centro (0..1, 0..1). zoom: acercamiento extra sobre el recorte.
    mover: (zoom_final, dx, dy) para un paneo lento tipo «Ken Burns» entre t0 y t1 (dx, dy en px de pantalla).
    desenfoque: radio en px (separa la foto de los personajes). luz: multiplica el brillo.
    tinte: (r, g, b) que se mezcla con la foto (p. ej. azul noche) y fuerza: cuánto. vineta: 0..1.
    """
    def __init__(self, ruta, t0=0.0, t1=None, foco=(0.5, 0.5), zoom=1.0, mover=None, desenfoque=6, luz=1.0,
                 tinte=None, fuerza=0.0, vineta=0.45, espejo=False):
        from PIL import Image, ImageFilter, ImageEnhance, ImageOps
        im = Image.open(ruta).convert("RGB")
        if espejo: im = ImageOps.mirror(im)
        margen = 1.12                                            # sobra para el paneo
        esc = max(W * margen / im.width, H * margen / im.height) * zoom
        im = im.resize((max(1, int(im.width * esc)), max(1, int(im.height * esc))), Image.LANCZOS)
        cw, ch = int(W * margen), int(H * margen)
        x0 = int(clamp(foco[0] * im.width - cw / 2, 0, im.width - cw))
        y0 = int(clamp(foco[1] * im.height - ch / 2, 0, im.height - ch))
        im = im.crop((x0, y0, x0 + cw, y0 + ch))
        if desenfoque: im = im.filter(ImageFilter.GaussianBlur(desenfoque))
        if luz != 1.0: im = ImageEnhance.Brightness(im).enhance(luz)
        a = np.asarray(im).astype(np.float32) / 255
        if tinte: a = a * (1 - fuerza) + a.mean(axis=2, keepdims=True) * np.array(tinte) * fuerza * 1.6
        if vineta:
            yy, xx = np.mgrid[0:ch, 0:cw]
            d = np.sqrt(((xx - cw / 2) / (cw / 2)) ** 2 + ((yy - ch / 2) / (ch / 2)) ** 2)
            a *= (1 - vineta * np.clip(d - 0.55, 0, 1) ** 1.5)[..., None]
        a = (np.clip(a, 0, 1) * 255).astype(np.uint8)
        bgra = np.zeros((ch, cw, 4), np.uint8); bgra[..., 0], bgra[..., 1], bgra[..., 2] = a[..., 2], a[..., 1], a[..., 0]
        self.sup = cairo.ImageSurface.create_for_data(bytearray(bgra.tobytes()), cairo.FORMAT_RGB24, cw, ch, cw * 4)
        self.cw, self.ch, self.t0, self.t1, self.mover = cw, ch, t0, t1, mover

    def dibujar(self, ctx, t):
        k = suave((t - self.t0) / max(1e-6, (self.t1 or self.t0 + 1) - self.t0)) if self.mover else 0
        z, dx, dy = (lerp(1, self.mover[0], k), self.mover[1] * k, self.mover[2] * k) if self.mover else (1, 0, 0)
        ctx.save(); ctx.translate(W / 2 + dx, H / 2 + dy); ctx.scale(z, z)
        ctx.set_source_surface(self.sup, -self.cw / 2, -self.ch / 2); ctx.paint(); ctx.restore()


# ---------------------------------------------------------------- más utilería
def cielo_noche(ctx, t, alto=H, nubes=True, velocidad=60, semilla=7):
    g = cairo.LinearGradient(0, 0, 0, alto)
    g.add_color_stop_rgb(0, 0.03, 0.05, 0.14); g.add_color_stop_rgb(1, 0.13, 0.17, 0.36)
    ctx.set_source(g); ctx.rectangle(0, 0, W, alto); ctx.fill()
    rnd = random.Random(semilla)
    for _ in range(70):
        sx, sy, sr = rnd.uniform(0, W), rnd.uniform(0, alto), rnd.uniform(1.5, 4)
        brillo = 0.5 + 0.5 * math.sin(t * rnd.uniform(1, 4) + sx)
        ctx.set_source_rgba(1, 1, 0.9, 0.35 + 0.55 * brillo); ctx.arc(sx, sy, sr, 0, 2 * math.pi); ctx.fill()
    ctx.arc(W * 0.8, alto * 0.16, 70, 0, 2 * math.pi); ctx.set_source_rgb(0.97, 0.95, 0.82); ctx.fill()
    ctx.arc(W * 0.8 + 28, alto * 0.16 - 18, 64, 0, 2 * math.pi); ctx.set_source_rgb(0.05, 0.07, 0.17); ctx.fill()
    if nubes:
        for i in range(5):
            nx = (rnd.uniform(0, W + 600) - t * velocidad * (0.6 + i * 0.15)) % (W + 600) - 300
            ny = rnd.uniform(alto * 0.3, alto * 0.9)
            ctx.set_source_rgba(0.55, 0.6, 0.8, 0.22)
            for (dx, dy, rr) in [(0, 0, 60), (60, -20, 75), (130, 0, 60), (65, 15, 70)]:
                ctx.arc(nx + dx, ny + dy, rr, 0, 2 * math.pi); ctx.fill()


def avion(color=(0.97, 0.97, 0.98), franja=(0.16, 0.30, 0.62), luces=True):
    """Avión presidencial de perfil, mirando a la derecha (unos 900 px de largo a escala 1)."""
    def f(ctx, t, k):
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        # ala lejana
        ctx.move_to(-40, 10); ctx.line_to(-170, -70); ctx.line_to(-120, -70); ctx.line_to(60, 5); ctx.close_path()
        contorno(ctx, (0.75, 0.78, 0.84), 8)
        # cola
        ctx.move_to(-330, -20); ctx.line_to(-420, -200); ctx.line_to(-360, -200); ctx.line_to(-250, -30); ctx.close_path()
        contorno(ctx, franja, 9)
        # fuselaje
        ctx.move_to(-440, -40); ctx.curve_to(-300, -70, 250, -75, 360, -55)
        ctx.curve_to(450, -40, 470, 20, 420, 40); ctx.curve_to(250, 70, -300, 60, -420, 20)
        ctx.curve_to(-445, 5, -450, -25, -440, -40); ctx.close_path()
        contorno(ctx, color, 10)
        ctx.save(); ctx.move_to(-440, -40); ctx.curve_to(-300, -70, 250, -75, 360, -55)
        ctx.curve_to(450, -40, 470, 20, 420, 40); ctx.curve_to(250, 70, -300, 60, -420, 20); ctx.close_path(); ctx.clip()
        ctx.rectangle(-460, 8, 940, 70); ctx.set_source_rgb(*franja); ctx.fill()
        ctx.rectangle(-460, 0, 940, 9); ctx.set_source_rgb(0.85, 0.7, 0.25); ctx.fill()
        ctx.restore()
        ctx.move_to(-440, -40); ctx.curve_to(-300, -70, 250, -75, 360, -55)
        ctx.curve_to(450, -40, 470, 20, 420, 40); ctx.curve_to(250, 70, -300, 60, -420, 20); ctx.close_path()
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(10); ctx.stroke()
        # ventanillas y cabina
        for i in range(16):
            ctx.arc(-300 + i * 38, -28, 8, 0, 2 * math.pi); ctx.set_source_rgb(1, 0.88, 0.45); ctx.fill()
        ctx.move_to(372, -40); ctx.line_to(420, -36); ctx.line_to(430, -22); ctx.line_to(375, -24); ctx.close_path()
        contorno(ctx, (0.2, 0.25, 0.35), 5)
        # ala cercana y motores
        ctx.move_to(-20, 20); ctx.line_to(-200, 150); ctx.line_to(-140, 150); ctx.line_to(90, 25); ctx.close_path()
        contorno(ctx, (0.85, 0.87, 0.9), 9)
        for (mx, my) in [(-60, 80), (-140, 125)]:
            ctx.save(); ctx.translate(mx, my); ctx.scale(1, 0.45); ctx.arc(0, 0, 40, 0, 2 * math.pi); ctx.restore()
            contorno(ctx, (0.7, 0.73, 0.8), 7)
        if luces and int(t * 2) % 2 == 0:
            ctx.arc(-410, -195, 12, 0, 2 * math.pi); ctx.set_source_rgb(1, 0.2, 0.2); ctx.fill()
            ctx.arc(-200, 150, 10, 0, 2 * math.pi); ctx.set_source_rgb(0.3, 1, 0.4); ctx.fill()
    return f


def telefono(texto_pantalla="LÍNEA PRIVADA", sonando=True, color_pantalla=(0.12, 0.6, 0.35)):
    def f(ctx, t, k):
        vib = math.sin(t * 60) * 6 if sonando and (t * 2) % 1 < 0.6 else 0
        ctx.translate(vib, 0); ctx.rotate(vib * 0.004)
        if sonando:
            for i in range(3):
                ctx.set_source_rgba(*TINTA, 0.9); ctx.set_line_width(9)
                for lado in (-1, 1):
                    ctx.arc(0, -40, 150 + i * 35, math.radians(-90 + lado * 50) - 0.3, math.radians(-90 + lado * 50) + 0.3)
                    ctx.stroke()
        ctx.move_to(-85, -160); ctx.line_to(85, -160); ctx.curve_to(105, -160, 105, -160, 105, -140)
        ctx.line_to(105, 160); ctx.curve_to(105, 180, 105, 180, 85, 180); ctx.line_to(-85, 180)
        ctx.curve_to(-105, 180, -105, 180, -105, 160); ctx.line_to(-105, -140); ctx.curve_to(-105, -160, -105, -160, -85, -160)
        ctx.close_path(); contorno(ctx, (0.12, 0.12, 0.14), 9)
        ctx.rectangle(-88, -140, 176, 290); ctx.set_source_rgb(*color_pantalla); ctx.fill()
        ctx.arc(0, -40, 42, 0, 2 * math.pi); ctx.set_source_rgb(1, 1, 1); ctx.fill()
        ctx.set_source_rgb(*color_pantalla); ctx.set_line_width(12)               # auricular dibujado
        ctx.arc(0, -40, 22, math.radians(40), math.radians(220)); ctx.stroke()
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_source_rgb(1, 1, 1)
        for i, renglon in enumerate(texto_pantalla.split("\n")):
            ctx.set_font_size(26); e = ctx.text_extents(renglon)
            ctx.move_to(-e.width / 2 - e.x_bearing, 50 + i * 34); ctx.show_text(renglon)
    return f


def sobre(sello=(0.78, 0.12, 0.14)):
    def f(ctx, t, k):
        ctx.rectangle(-150, -95, 300, 190); contorno(ctx, (0.93, 0.86, 0.68), 9)
        ctx.move_to(-150, -95); ctx.line_to(0, 20); ctx.line_to(150, -95)
        ctx.set_source_rgb(*TINTA); ctx.set_line_width(7); ctx.stroke()
        ctx.arc(0, 20, 28, 0, 2 * math.pi); contorno(ctx, sello, 6)
    return f


def documento(titulo="ORDEN", sello_txt="CONFIDENCIAL"):
    def f(ctx, t, k):
        ctx.rectangle(-170, -230, 340, 460); contorno(ctx, (0.98, 0.97, 0.92), 9)
        ctx.save(); ctx.translate(0, -165); texto(titulo, 60)(ctx, t, k); ctx.restore()
        ctx.set_source_rgba(*TINTA, 0.55); ctx.set_line_width(10)
        for i in range(6):
            ctx.move_to(-130, -90 + i * 42); ctx.line_to(130 - (60 if i % 3 == 2 else 0), -90 + i * 42); ctx.stroke()
        ctx.save(); ctx.translate(20, 150); ctx.rotate(-0.2)
        ctx.rectangle(-150, -38, 300, 76); ctx.set_source_rgb(0.85, 0.1, 0.12); ctx.set_line_width(8); ctx.stroke()
        texto(sello_txt, 44, (0.85, 0.1, 0.12))(ctx, t, k); ctx.restore()
    return f


def burbuja_dialogo(txt, tam=56, ancho=620, cola=(-1, 1), color=(1, 1, 1), color_txt=TINTA):
    """Globo de diálogo con el texto partido en renglones; cola = dirección (x, y) hacia quien habla."""
    def f(ctx, t, k):
        ctx.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); ctx.set_font_size(tam)
        renglones, act = [], ""
        for w in txt.split():
            prueba = (act + " " + w).strip()
            if ctx.text_extents(prueba).x_advance > ancho and act: renglones.append(act); act = w
            else: act = prueba
        renglones.append(act)
        alto = len(renglones) * tam * 1.25 + 60; anch = ancho + 80
        ctx.move_to(cola[0] * 60, alto / 2 - 10); ctx.line_to(cola[0] * 160, cola[1] * (alto / 2 + 90))
        ctx.line_to(cola[0] * 140 + (-cola[0]) * 80, alto / 2 - 10); ctx.close_path(); contorno(ctx, color, 8)
        x0, y0, rr = -anch / 2, -alto / 2, 50
        ctx.new_sub_path(); ctx.arc(x0 + anch - rr, y0 + rr, rr, -math.pi / 2, 0)
        ctx.arc(x0 + anch - rr, y0 + alto - rr, rr, 0, math.pi / 2); ctx.arc(x0 + rr, y0 + alto - rr, rr, math.pi / 2, math.pi)
        ctx.arc(x0 + rr, y0 + rr, rr, math.pi, 3 * math.pi / 2); ctx.close_path(); contorno(ctx, color, 8)
        ctx.set_source_rgb(*color); ctx.rectangle(cola[0] * 60 - 50, alto / 2 - 30, 120, 26); ctx.fill()
        ctx.set_source_rgb(*color_txt)
        for i, ren in enumerate(renglones):
            e = ctx.text_extents(ren)
            ctx.move_to(-e.x_advance / 2, y0 + 30 + tam + i * tam * 1.25 - tam * 0.2); ctx.show_text(ren)
    return f


def reloj_digital(hora="2:00", sufijo="AM"):
    def f(ctx, t, k):
        ctx.rectangle(-220, -95, 440, 190); contorno(ctx, (0.1, 0.1, 0.12), 10)
        txt = hora if (t * 2) % 2 < 1.6 else hora.replace(":", " ")
        ctx.save(); ctx.translate(-30, 0); texto(txt, 120, (1, 0.25, 0.2))(ctx, t, k); ctx.restore()
        ctx.save(); ctx.translate(150, 30); texto(sufijo, 46, (1, 0.25, 0.2))(ctx, t, k); ctx.restore()
    return f


def pistola():
    def f(ctx, t, k):
        ctx.move_to(-20, -30); ctx.line_to(110, -30); ctx.line_to(110, 0); ctx.line_to(20, 0); ctx.line_to(14, 50)
        ctx.line_to(-24, 50); ctx.close_path(); contorno(ctx, (0.18, 0.18, 0.2), 6)
    return f


def alerta(titulo="ALERTA", cuerpo="Aeropuerto CERRADO"):
    def f(ctx, t, k):
        ctx.rectangle(-260, -150, 520, 300); contorno(ctx, (0.97, 0.97, 0.98), 9)
        ctx.rectangle(-255, -145, 510, 90); ctx.set_source_rgb(0.85, 0.12, 0.14); ctx.fill()
        ctx.save(); ctx.translate(0, -100); texto("⚠ " + titulo, 54, (1, 1, 1))(ctx, t, k); ctx.restore()
        ctx.save(); ctx.translate(0, 40); texto(cuerpo, 46)(ctx, t, k); ctx.restore()
    return f


# ---------------------------------------------------------------- render
class Short:
    def __init__(self, duracion, capas=None):
        self.dur, self.capas = duracion, capas or []
        self.sacudidas = []  # [(t, fuerza)]
        self.zooms = []      # [(t0, t1, escala, cx, cy)]

    def agregar(self, *capas): self.capas.extend(capas); return self

    def sacudir(self, t, fuerza=18): self.sacudidas.append((t, fuerza))

    def zoom(self, t0, t1, escala, cx=W / 2, cy=H / 2): self.zooms.append((t0, t1, escala, cx, cy))

    def cuadro(self, t):
        sup = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
        ctx = cairo.Context(sup)
        ctx.set_antialias(cairo.ANTIALIAS_BEST)
        dx = dy = 0
        for (ts, f) in self.sacudidas:
            if 0 <= t - ts < 0.35:
                d = (1 - (t - ts) / 0.35) * f
                dx += math.sin(t * 90) * d; dy += math.cos(t * 77) * d
        esc, cx, cy = 1.0, W / 2, H / 2
        for (t0, t1, e, zx, zy) in self.zooms:
            if t0 <= t <= t1:
                k = suave(min((t - t0) / 0.4, (t1 - t) / 0.4, 1)); esc = lerp(1, e, k); cx, cy = zx, zy
        ctx.translate(dx, dy)
        ctx.translate(cx, cy); ctx.scale(esc, esc); ctx.translate(-cx, -cy)
        subs = [c for c in self.capas if isinstance(c, Subtitulos)]
        for c in self.capas:
            if not isinstance(c, Subtitulos): c.dibujar(ctx, t)
        ctx.identity_matrix()  # los subtítulos no se mueven con la cámara
        for c in subs: c.dibujar(ctx, t)
        buf = np.ndarray((H, W, 4), np.uint8, sup.get_data())
        return buf[:, :, [2, 1, 0]].copy()  # BGRA -> RGB

    def foto(self, t, ruta):
        from PIL import Image
        Image.fromarray(self.cuadro(t)).save(ruta)

    def render(self, ruta, audio=None, desde=0.0, hasta=None):
        hasta = hasta or self.dur
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
        if audio: cmd += ["-i", audio, "-c:a", "aac", "-b:a", "160k", "-shortest"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", ruta]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        n = int((hasta - desde) * FPS)
        for i in range(n):
            p.stdin.write(self.cuadro(desde + i / FPS).tobytes())
            if i % FPS == 0: print(f"\r  render {i / FPS:5.1f}s / {hasta - desde:.1f}s", end="", flush=True)
        p.stdin.close(); p.wait(); print(f"\r  listo: {ruta}            ")
