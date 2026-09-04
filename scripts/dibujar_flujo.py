# -*- coding: utf-8 -*-
"""El flujo de la consulta a la respuesta, dibujado desde lo que hoy hace el codigo.

QUE CAMBIO EN ESTA VERSION. El sistema tiene ahora una FRONTERA DE IDIOMA, y
sin ella el dibujo contaba una arquitectura que ya no es. Los alumnos preguntan
en español y todo el aparato es ingles —las 3 839 palabras clave del grafo, los
183 433 hechos de Mathlib, los ejemplos de miniF2F y el propio Lean—, asi que la
consulta se traduce UNA VEZ al entrar y la respuesta vuelve en el idioma en que
se pregunto.

Las fronteras no llevan numero, y es a proposito: los seis pasos numerados son
lo que el sistema HACE con la consulta; las fronteras son sus bordes.

LO QUE EL DIBUJO YA CONTABA BIEN, y sigue igual:

    paso 2b  repair_imports  -> reintenta la verificacion, UNA vez
    paso 2c  _revisar_con_lean -> vuelve al LLM con el error, MAXIMO 2 rondas
             y las dos solo se aceptan si el resultado MEJORA
    paso 3   la cascada corre solo en la rama SORRY y su salida es el
             veredicto «parcial», que sigue al paso 6

Y el veredicto final tiene SIETE estados, no seis y no dos:

    verificado · parcial · refutado · sin_teorema
    no_verificado · timeout · sin_entorno

SE COMPRUEBA SOLO. Cada caja no terminal tiene que tener una flecha que entra y
otra que sale —la caja huerfana del paso 5 la encontro el usuario leyendo el
dibujo, no el script—, ningun texto puede salirse de su caja, y ningun elemento
puede depender del <style> para tener color. Las tres comprobaciones miran el
registro que se llena al dibujar, no el SVG: parsear el propio SVG ya rompio dos
guardianes antes.

EL SVG LLEVA SU PROPIO ESTILO porque en el README va como <img>, donde las
variables CSS de la pagina no llegan. Y el tema CLARO va en atributos de
presentacion, no en el <style>: en GitHub el archivo se sirve como <img> con su
propia CSP, y si el bloque de estilo no llega el navegador pinta los valores por
defecto de SVG —relleno negro, sin trazo— y el diagrama sale como una mancha.

    python scripts/dibujar_flujo.py
"""
import argparse
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

SALIDA = "E:/Metamatematico/docs/img/00-flujo-real.svg"
W, H = 1180, 1100

SANS = "ui-sans-serif,system-ui,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,monospace"

CLARO = {
    "bg": {"fill": "#ffffff", "stroke": "#ddd6c2", "stroke-width": "1.3"},
    "gr": {"fill": "#e7e4f5", "stroke": "#564c9e", "stroke-width": "1.3"},
    "ve": {"fill": "#dbf0ea", "stroke": "#167a68", "stroke-width": "1.3"},
    "ll": {"fill": "#f5e7cf", "stroke": "#b4761f", "stroke-width": "1.3"},
    "al": {"fill": "#f6dfdc", "stroke": "#ae3b35", "stroke-width": "1.3"},
    "id": {"fill": "#e4eef6", "stroke": "#2b6a94", "stroke-width": "1.3"},
    "ln": {"fill": "none", "stroke": "#1b1e17", "stroke-width": "1.6",
           "opacity": ".5"},
    "pf": {"fill": "#1b1e17", "opacity": ".5"},
    "t":  {"fill": "#1b1e17", "font-family": SANS, "font-size": "13"},
    "b":  {"fill": "#1b1e17", "font-family": SANS, "font-size": "13",
           "font-weight": "600"},
    "s":  {"fill": "#1b1e17", "font-family": SANS, "font-size": "11",
           "opacity": ".66"},
    "m":  {"fill": "#1b1e17", "font-family": MONO, "font-size": "11",
           "opacity": ".78"},
}

#: el oscuro repite TODO lo que lleva color: si una clase se queda fuera,
#: hereda el claro y se pinta texto claro sobre fondo claro
OSCURO = {
    "bg": {"fill": "#171b23", "stroke": "#2b3140"},
    "gr": {"fill": "#242038", "stroke": "#948bdd"},
    "ve": {"fill": "#152722", "stroke": "#4dc0aa"},
    "ll": {"fill": "#332714", "stroke": "#e2a94f"},
    "al": {"fill": "#331d1b", "stroke": "#e2827a"},
    "id": {"fill": "#151f28", "stroke": "#6fb3d9"},
    "ln": {"stroke": "#e8e6de"},
    "pf": {"fill": "#e8e6de"},
    "t":  {"fill": "#e8e6de"},
    "b":  {"fill": "#e8e6de"},
    "s":  {"fill": "#e8e6de"},
    "m":  {"fill": "#e8e6de"},
}

CAJAS = []   # (nombre, x, y, w, h, rol) — las que participan en el flujo
TODAS = []   # (x, y, w, h) — tambien las decorativas, para medir el texto
ARCOS = []   # (x1, y1, x2, y2) — extremos reales de cada flecha
TEXTOS = []  # (x, y, cadena, clase, ancla)

#: ancho aproximado por caracter, medido sobre las fuentes del dibujo
ANCHO = {"b": 7.3, "t": 7.3, "s": 5.4, "m": 6.6}


def pinta(cls):
    """Los atributos de presentacion de una clase, para no depender del CSS."""
    return "".join(' %s="%s"' % kv for kv in sorted(CLARO[cls].items()))


def estilo(ident, oscuro):
    """El <style> lleva SOLO el tema oscuro; el claro va en los atributos."""
    reglas = "".join(
        "#%s .%s{%s}" % (ident, cls, ";".join("%s:%s" % kv
                                              for kv in sorted(d.items())))
        for cls, d in oscuro.items())
    return "<style>@media(prefers-color-scheme:dark){%s}</style>" % reglas


def caja(nombre, x, y, w, h, cls="", r=9, rol="normal"):
    if rol not in ("deco", "chip"):
        CAJAS.append((nombre, x, y, w, h, rol))
    if rol != "chip":
        TODAS.append((x, y, w, h))
    return ('<rect class="%s"%s x="%d" y="%d" width="%d" height="%d" rx="%d"/>'
            % (cls, pinta(cls), x, y, w, h, r))


def txt(x, y, s, cls="t", anc="start"):
    TEXTOS.append((x, y, s, cls, anc))
    return ('<text class="%s"%s x="%d" y="%d" text-anchor="%s">%s</text>'
            % (cls, pinta(cls), x, y, anc, s))


def ruta(*puntos):
    """Flecha por waypoints. Registra el primer y el ultimo punto."""
    ARCOS.append((puntos[0][0], puntos[0][1], puntos[-1][0], puntos[-1][1]))
    d = "M%d %d " % puntos[0] + " ".join("L%d %d" % q for q in puntos[1:])
    return ('<path class="ln"%s d="%s" marker-end="url(#p)"/>'
            % (pinta("ln"), d))


def chip(x, y, s, cls="bg"):
    w = int(len(s) * 6.4) + 22
    return (caja("", x, y, w, 24, cls, 12, "chip")
            + txt(x + w // 2, y + 16, s, "m", "middle")), w


ARIA = (
    "El flujo de la consulta a la respuesta. La consulta entra por la interfaz "
    "en español o en inglés y cruza la frontera del idioma: si viene en español "
    "se traduce al inglés con un modelo local, protegiendo la notación, porque "
    "todo el aparato del sistema es inglés; el inglés pasa directo. Un "
    "clasificador decide entonces si es matemática; si no lo es va al modelo "
    "conversacional, que responde sin verificación formal. Si lo es, el grafo "
    "actúa en tres puntos numerados: prepara el prompt con nombres de Mathlib "
    "comprobados, elige qué módulos importa Lean, y ordena las tácticas si "
    "queda un sorry. Solo el primero aporta: el segundo es inerte y el "
    "tercero no bate a su modelo nulo. "
    "Lean verifica y abre cuatro caminos: si falta un módulo se repara el "
    "encabezado y se reintenta una vez, si el error es semántico vuelve al "
    "modelo hasta dos rondas, si queda un sorry entra la cascada de tácticas, "
    "y si Lean acepta se pasa directo al veredicto. Los caminos confluyen en "
    "un veredicto final de siete estados, que el modelo traduce a lenguaje "
    "natural. Al final se cruza la frontera de vuelta: la respuesta sale en el "
    "idioma en que se preguntó y la pregunta que se le enseña al alumno es la "
    "suya, no la traducción."
)

NOTA = [
    ["Los co-reguladores deciden antes y la",
     "memoria MES registra después: ninguno",
     "formaliza ni verifica."],
    ["Los dos reintentos sólo se aceptan si",
     "MEJORAN. Nunca se sustituye un",
     "resultado por otro peor."],
    ["«Lean acepta» no es «hay prueba»:",
     "sin_teorema sale de un archivo que sólo",
     "hace #check, y refutado de haber",
     "probado lo contrario de lo pedido."],
    ["La lista de 183 433 hechos de Mathlib",
     "no toca el prompt: alimenta el índice",
     "de premisas del paso 5."],
    ["El reconocedor de área lee la FORMA del",
     "enunciado —75,4 % frente a un nulo del",
     "23,8 %— y está FUERA de la cadena:",
     "enchufarlo costaba 0,7 puntos de",
     "precisión sin ganar cobertura."],
    ["Los nombres de los 125 nodos generados",
     "no se inyectan: están deducidos, y 95",
     "de 447 no existen en Mathlib."],
]

RAMAS = [
    (170, "falta un módulo",   "repara y reintenta"),
    (316, "error semántico",   "vuelve al LLM, ×2"),
    (462, "queda un `sorry`",  "va a la cascada"),
    (608, "Lean acepta",       "no hay más que hacer"),
]

VEREDICTOS = [
    [("verificado", "ve"), ("parcial", "al"), ("refutado", "bg"),
     ("sin_teorema", "bg")],
    [("no_verificado", "bg"), ("timeout", "bg"), ("sin_entorno", "bg")],
]


def main(_):
    p = ['<svg xmlns="http://www.w3.org/2000/svg" role="img" '
         'id="fig-flujo" aria-label="%s" viewBox="0 0 %d %d">'
         % (ARIA, W, H)]
    p.append('<defs><marker id="p" viewBox="0 0 10 10" refX="9" refY="5" '
             'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
             '<path class="pf"%s d="M0 0 L10 5 L0 10 z"/></marker></defs>'
             % pinta("pf"))
    p.append(estilo("fig-flujo", OSCURO))

    p.append(txt(24, 26, "DE LA ENTRADA A LA SALIDA", "b"))
    p.append(txt(232, 26, "— el grafo actúa en TRES puntos, y sólo UNO aporta",
                 "s"))

    # ── entrada ────────────────────────────────────────────────────────────
    p.append(caja("consulta", 170, 46, 200, 44, "bg", 9, "entrada"))
    p.append(txt(270, 68, "consulta del alumno", "b", "middle"))
    p.append(txt(270, 84, "español · inglés · UI o CLI", "s", "middle"))
    p.append(ruta((270, 90), (270, 102)))

    # ── la frontera del idioma ─────────────────────────────────────────────
    p.append(caja("frontera", 170, 104, 574, 88, "id"))
    p.append(txt(186, 127, "LA FRONTERA DEL IDIOMA", "b"))
    p.append(txt(186, 148, "el alumno pregunta en español y TODO el aparato es "
                           "inglés: las 3 839 palabras", "s"))
    p.append(txt(186, 166, "clave, los 183 433 hechos, los ejemplos de miniF2F "
                           "y el propio Lean", "s"))
    p.append(txt(186, 184, "traductor local de 74 M · la notación va protegida "
                           "· el inglés pasa directo", "s"))
    p.append(ruta((290, 192), (290, 204)))

    # ── triaje ─────────────────────────────────────────────────────────────
    p.append(caja("triaje", 170, 206, 240, 50, "bg"))
    p.append(txt(290, 228, "¿es matemática?", "t", "middle"))
    p.append(txt(290, 244, "forma + vocabulario", "s", "middle"))

    p.append(caja("conversacional", 450, 206, 294, 50, "ll"))
    p.append(txt(597, 228, "LLM conversacional", "t", "middle"))
    p.append(txt(597, 244, "no formaliza nada · sin veredicto", "s", "middle"))
    p.append(ruta((410, 231), (448, 231)))
    p.append(txt(429, 223, "no", "s", "middle"))
    p.append(txt(298, 270, "sí", "s"))
    p.append(ruta((290, 256), (290, 274)))

    # ── 1 · el grafo prepara ───────────────────────────────────────────────
    p.append(caja("paso1", 170, 276, 574, 72, "gr"))
    p.append(txt(186, 298, "1 · EL GRAFO PREPARA EL PROMPT", "b"))
    p.append(txt(186, 318, "conceptos activados · nombres de Mathlib "
                           "comprobados con #check · ejemplos few-shot", "s"))
    p.append(txt(186, 336, "APORTA · 12× sobre el azar, medido contra ProofNet",
                 "s"))

    # ── 2 · el LLM formaliza ───────────────────────────────────────────────
    p.append(ruta((432, 348), (432, 360)))
    p.append(caja("paso2", 170, 362, 574, 64, "ll"))
    p.append(txt(186, 384, "2 · EL LLM FORMALIZA", "b"))
    p.append(txt(186, 402, "escribe Lean 4 — no decide si es cierto", "s"))
    p.append(txt(186, 418, "si sale una tautología, se rehace una vez antes de "
                           "verificar", "s"))

    # ── 3 · imports ────────────────────────────────────────────────────────
    p.append(ruta((432, 426), (432, 438)))
    p.append(caja("paso3", 170, 440, 574, 72, "gr"))
    p.append(txt(186, 462, "3 · EL GRAFO ELIGE QUÉ MÓDULOS VE LEAN", "b"))
    p.append(txt(186, 482, "descarta `import Mathlib` — 742 s, más que el "
                           "timeout", "s"))
    p.append(txt(186, 500, "INERTE · empata con un conjunto fijo de 3 módulos, "
                           "y el margen total son 2,5 puntos", "s"))

    # ── 4 · Lean ───────────────────────────────────────────────────────────
    p.append(ruta((432, 512), (432, 524)))
    p.append(caja("paso4", 170, 526, 574, 50, "ve"))
    p.append(txt(186, 548, "4 · LEAN VERIFICA", "b"))
    p.append(txt(186, 566, "la fuente de verdad · su veredicto es inapelable",
                 "s"))

    # ── las cuatro salidas de Lean ─────────────────────────────────────────
    for x, arriba, abajo in RAMAS:
        cls = "ve" if arriba == "Lean acepta" else "al"
        p.append(caja("rama-%d" % x, x, 592, 136, 52, cls))
        p.append(txt(x + 68, 614, arriba, "m", "middle"))
        p.append(txt(x + 68, 632, abajo, "s", "middle"))
        p.append(ruta((432, 576), (432, 584), (x + 68, 584), (x + 68, 592)))

    # los dos reintentos, que vuelven al flujo
    p.append(ruta((238, 644), (238, 654), (140, 654), (140, 551), (168, 551)))
    p.append(ruta((384, 644), (384, 664), (100, 664), (100, 394), (168, 394)))

    # ── 5 · la cascada de tácticas ─────────────────────────────────────────
    p.append(ruta((530, 644), (530, 666)))
    p.append(caja("paso5", 170, 668, 460, 72, "gr"))
    p.append(txt(186, 690, "5 · EL GRAFO ORDENA LAS TÁCTICAS", "b"))
    p.append(txt(186, 710, "12 tácticas · premisas sólo si el objetivo "
                           "engancha", "s"))
    p.append(txt(186, 728, "NO BATE AL NULO · 1,26 frente al 1,09 de «probar simp primero»", "s"))

    # ── el veredicto final ─────────────────────────────────────────────────
    p.append(ruta((400, 740), (400, 756)))
    p.append(ruta((676, 644), (676, 756)))
    p.append(caja("veredicto", 170, 758, 574, 98, "bg"))
    p.append(txt(186, 780, "EL VEREDICTO FINAL — siete estados, no dos", "b"))
    for fila, y in zip(VEREDICTOS, (792, 822)):
        x = 186
        for s, cls in fila:
            marca, w = chip(x, y, s, cls)
            p.append(marca)
            x += w + 10

    # ── 6 · el LLM traduce ─────────────────────────────────────────────────
    p.append(ruta((432, 856), (432, 870)))
    p.append(caja("paso6", 170, 872, 574, 64, "ll"))
    p.append(txt(186, 894, "6 · EL LLM TRADUCE EL VEREDICTO", "b"))
    p.append(txt(186, 912, "explica el código que Lean aceptó — no lo que el "
                           "modelo creía que era cierto", "s"))
    p.append(txt(186, 928, "el estado de Lean va dentro del prompt: no puede "
                           "decir que no pudo comprobarlo", "s"))

    # ── la frontera, de vuelta ─────────────────────────────────────────────
    p.append(ruta((432, 936), (432, 950)))
    p.append(caja("vuelta", 170, 952, 574, 88, "id"))
    p.append(txt(186, 975, "LA FRONTERA, DE VUELTA", "b"))
    p.append(txt(186, 996, "si preguntó en español, la respuesta sale en "
                           "español — se fija en el prompt,", "s"))
    p.append(txt(186, 1014, "porque el enunciado que el modelo tiene delante "
                            "ya está en inglés", "s"))
    p.append(txt(186, 1032, "«pregunta original» es la del alumno · el "
                            "historial guarda lo que él escribió", "s"))

    p.append(ruta((432, 1040), (432, 1052)))
    p.append(caja("respuesta", 170, 1054, 574, 44, "bg", 9, "salida"))
    p.append(txt(457, 1076, "respuesta", "b", "middle"))
    p.append(txt(457, 1092, "el veredicto va DELANTE del texto, siempre", "s",
                 "middle"))

    # la rama conversacional baja por fuera y llega a la misma salida
    p.append(ruta((744, 231), (1150, 231), (1150, 1076), (746, 1076)))

    # ── lo que no está en la cadena ────────────────────────────────────────
    p.append(caja("nota", 780, 276, 300, 664, "bg", 9, "deco"))
    p.append(txt(796, 300, "Lo que el dibujo NO cuenta", "b"))
    y = 324
    for bloque in NOTA:
        for linea in bloque:
            p.append(txt(796, y, linea, "s"))
            y += 17
        y += 16

    p.append("</svg>")
    io.open(SALIDA, "w", encoding="utf-8").write("\n".join(p))

    # ── y NADA puede depender del <style> ──────────────────────────────────
    _els = re.findall(r"<(?:rect|text|circle|path)\b[^>]*>",
                      io.open(SALIDA, encoding="utf-8").read())
    _pelados = [e[:70] for e in _els if "fill=" not in e]

    # ── el dibujo tiene que cerrar, y se comprueba ─────────────────────────
    def toca(c, px, py, m=16):
        _, x, y_, w, h = c[:5]
        return (x - m <= px <= x + w + m) and (y_ - m <= py <= y_ + h + m)

    sin_entrada, sin_salida = [], []
    for c in CAJAS:
        rol = c[5]
        if not any(toca(c, a[2], a[3]) for a in ARCOS) and rol != "entrada":
            sin_entrada.append(c[0])
        if not any(toca(c, a[0], a[1]) for a in ARCOS) and rol != "salida":
            sin_salida.append(c[0])

    desborda = []
    for x, y_, cad, cls, anc in TEXTOS:
        w = len(cad) * ANCHO.get(cls, 6.0)
        x0 = x if anc == "start" else (x - w / 2 if anc == "middle" else x - w)
        dentro = [c for c in TODAS
                  if c[0] <= x <= c[0] + c[2] and c[1] <= y_ - 6 <= c[1] + c[3]]
        if not dentro:
            continue
        c = min(dentro, key=lambda q: q[2] * q[3])
        if x0 < c[0] + 5 or x0 + w > c[0] + c[2] - 5:
            desborda.append(cad[:38])

    sin_oscuro = sorted(set(CLARO) - set(OSCURO))
    fuera = [c[0] for c in CAJAS if c[1] + c[3] > W or c[2] + c[4] > H]
    print("  cajas %d · flechas %d · textos %d"
          % (len(CAJAS), len(ARCOS), len(TEXTOS)))
    print("  clases sin tema oscuro: %s" % (sin_oscuro or "ninguna"))
    print("  sin color propio      : %s" % (_pelados or "ninguno"))
    print("  sin flecha que entre  : %s" % (sin_entrada or "ninguna"))
    print("  sin flecha que salga  : %s" % (sin_salida or "ninguna"))
    print("  texto que se sale     : %s" % (desborda or "ninguno"))
    print("  fuera del lienzo      : %s" % (fuera or "ninguna"))
    if (sin_entrada or sin_salida or fuera or desborda or sin_oscuro
            or _pelados):
        print("     ATENCIÓN: el diagrama corta el flujo o pierde su color")
        return 1
    print("\n  -> %s (%.1f KB)" % (SALIDA, os.path.getsize(SALIDA) / 1024))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    sys.exit(main(a))
