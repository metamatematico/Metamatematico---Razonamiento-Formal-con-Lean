# -*- coding: utf-8 -*-
"""El flujo de la consulta a la respuesta, dibujado desde lo que hoy hace el codigo.

POR QUE SE REHACE, OTRA VEZ. La version anterior tenia el paso 5 —la cascada de
tacticas— con una flecha que entraba y ninguna que saliera. Un callejon sin
salida, y no es lo que pasa: la cascada devuelve su resultado al veredicto y de
ahi sigue al paso 6 como cualquier otra rama. Ademas presentaba «error de
modulo» y «error semantico» como VEREDICTOS FINALES cuando son estados
intermedios: cada uno dispara un reintento y vuelve al flujo.

Lo que el codigo hace de verdad, leido en `_math_via_lean` (nucleo/core.py):

    paso 2b  repair_imports  -> reintenta la verificacion, UNA vez
    paso 2c  _revisar_con_lean -> vuelve al LLM con el error, MAXIMO 2 rondas
             y las dos solo se aceptan si el resultado MEJORA
    paso 3   la cascada corre solo en la rama SORRY y su salida es el
             veredicto «parcial», que sigue al paso 6

Y el veredicto final tiene SIETE estados, no seis y no dos:

    verificado · parcial · refutado · sin_teorema
    no_verificado · timeout · sin_entorno

Un dibujo que corta el flujo donde el codigo sigue engaña, y engañaba.

AHORA SE COMPRUEBA SOLO. Al final se verifica que cada caja no terminal tenga
al menos una flecha que entra y una que sale. La caja huerfana del paso 5 la
encontro el usuario leyendo el dibujo; deberia haberla encontrado el script.
La comprobacion no lee el SVG —eso ya rompio dos guardianes antes— sino el
registro de cajas y arcos que se va llenando al dibujar.

EL SVG LLEVA SU PROPIO ESTILO porque en el README va como <img>, donde las
variables CSS de la pagina no llegan. Y va PREFIJADO con el id del dibujo:
un <style> dentro de un <svg> inline en HTML no esta encapsulado, y sin
prefijo estas reglas repintaban las cifras de portada del artefacto.

    python scripts/dibujar_flujo.py
"""
import argparse
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

SALIDA = "E:/Metamatematico/docs/img/00-flujo-real.svg"
W, H = 1120, 810

#: EL DIBUJO NO PUEDE DEPENDER DE SU <style>. En GitHub el SVG se sirve como
#: <img> desde /raw/, con su propia CSP y su propia cache; alli todo el color
#: colgaba de que el bloque de estilo y el `id` del <svg> llegaran intactos. Si
#: se pierde cualquiera de los dos no casa ningun selector y el navegador pinta
#: los valores por defecto de SVG: relleno negro, sin trazo, sin fuente.
#:
#: Asi que el tema claro va en ATRIBUTOS DE PRESENTACION, elemento a elemento,
#: y el <style> queda SOLO para el oscuro. Cualquier regla de CSS gana por
#: especificidad a un atributo de presentacion, asi que donde el CSS llega el
#: modo oscuro sigue mandando, y donde no llega se ve el dibujo en claro.
SANS = "ui-sans-serif,system-ui,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,monospace"

CLARO = {
    "bg": {"fill": "#ffffff", "stroke": "#ddd6c2", "stroke-width": "1.3"},
    "gr": {"fill": "#e7e4f5", "stroke": "#564c9e", "stroke-width": "1.3"},
    "ve": {"fill": "#dbf0ea", "stroke": "#167a68", "stroke-width": "1.3"},
    "ll": {"fill": "#f5e7cf", "stroke": "#b4761f", "stroke-width": "1.3"},
    "al": {"fill": "#f6dfdc", "stroke": "#ae3b35", "stroke-width": "1.3"},
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

#: ancho aproximado por caracter, medido sobre las fuentes del dibujo. No
#: hace falta ser exacto: sirve para avisar de un texto que se sale de su
#: caja, que es el fallo que un lienzo sin renderizador no deja ver.
ANCHO = {"b": 7.3, "t": 7.3, "s": 5.4, "m": 6.6}


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


def pinta(cls):
    """Los atributos de presentacion de una clase, para no depender del CSS."""
    return "".join(' %s="%s"' % kv for kv in sorted(CLARO[cls].items()))


def estilo(ident, oscuro):
    """El <style> lleva SOLO el tema oscuro; el claro va en los atributos."""
    reglas = "".join(
        "#%s .%s{%s}" % (ident, cls, ";".join("%s:%s" % kv
                                              for kv in sorted(d.items())))
        for cls, d in oscuro.items())
    return ("<style>@media(prefers-color-scheme:dark){%s}</style>" % reglas)


ARIA = (
    "El flujo de la consulta a la respuesta. La consulta entra por la interfaz "
    "y un clasificador decide si es matematica; si no lo es va al modelo "
    "conversacional, que responde sin verificacion formal. Si lo es, el grafo "
    "actua en tres puntos numerados: prepara el prompt con nombres de Mathlib "
    "comprobados, elige que modulos importa Lean, y ordena las tacticas si "
    "queda un sorry. Cada punto lleva su veredicto medido: el primero y el "
    "tercero aportan, el segundo es inerte. Lean verifica en medio y abre "
    "cuatro caminos: si falta un modulo se repara el encabezado y se reintenta "
    "una vez, si el error es semantico el error vuelve al modelo hasta dos "
    "rondas, si queda un sorry entra la cascada de tacticas, y si Lean acepta "
    "se pasa directo al veredicto. Los tres caminos confluyen en un veredicto "
    "final de siete estados, que el modelo traduce a lenguaje natural antes de "
    "la respuesta."
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
             '<path class="pf"%s d="M0 0 L10 5 L0 10 z"/>' % pinta("pf") + '</marker></defs>')
    p.append(estilo("fig-flujo", OSCURO))

    p.append(txt(24, 26, "DE LA ENTRADA A LA SALIDA", "b"))
    p.append(txt(232, 26, "— el grafo actúa en TRES puntos, y sólo dos aportan",
                 "s"))

    # ── entrada y triaje ───────────────────────────────────────────────────
    p.append(caja("consulta", 170, 46, 150, 44, "bg", 9, "entrada"))
    p.append(txt(245, 68, "consulta", "b", "middle"))
    p.append(txt(245, 84, "UI · CLI", "s", "middle"))

    p.append(caja("triaje", 344, 46, 176, 44, "bg"))
    p.append(txt(432, 66, "¿es matemática?", "t", "middle"))
    p.append(txt(432, 82, "forma + vocabulario", "s", "middle"))
    p.append(ruta((320, 68), (342, 68)))

    p.append(caja("conversacional", 544, 46, 200, 44, "ll"))
    p.append(txt(644, 68, "LLM conversacional", "t", "middle"))
    p.append(txt(644, 84, "no formaliza nada", "s", "middle"))
    p.append(ruta((520, 68), (542, 68)))
    p.append(txt(531, 60, "no", "s", "middle"))
    p.append(txt(440, 112, "sí", "s"))
    p.append(ruta((432, 90), (432, 120)))

    # ── 1 · el grafo prepara ───────────────────────────────────────────────
    p.append(caja("paso1", 170, 124, 574, 72, "gr"))
    p.append(txt(186, 146, "1 · EL GRAFO PREPARA EL PROMPT", "b"))
    p.append(txt(186, 166, "conceptos activados · nombres de Mathlib "
                           "comprobados con #check · ejemplos few-shot", "s"))
    p.append(txt(186, 184, "APORTA · 12× sobre el azar, medido contra ProofNet",
                 "s"))

    # ── 2 · el LLM formaliza ───────────────────────────────────────────────
    p.append(ruta((432, 196), (432, 212)))
    p.append(caja("paso2", 170, 216, 574, 64, "ll"))
    p.append(txt(186, 238, "2 · EL LLM FORMALIZA", "b"))
    p.append(txt(186, 256, "escribe Lean 4 — no decide si es cierto", "s"))
    p.append(txt(186, 272, "si sale una tautología, se rehace una vez antes de "
                           "verificar", "s"))

    # ── 3 · imports ────────────────────────────────────────────────────────
    p.append(ruta((432, 280), (432, 296)))
    p.append(caja("paso3", 170, 300, 574, 72, "gr"))
    p.append(txt(186, 322, "3 · EL GRAFO ELIGE QUÉ MÓDULOS VE LEAN", "b"))
    p.append(txt(186, 342, "descarta `import Mathlib` — 742 s, más que el "
                           "timeout", "s"))
    p.append(txt(186, 360, "INERTE · empata con un conjunto fijo de 3 módulos, "
                           "y el margen total son 2,5 puntos", "s"))

    # ── 4 · Lean ───────────────────────────────────────────────────────────
    p.append(ruta((432, 372), (432, 388)))
    p.append(caja("paso4", 170, 392, 574, 50, "ve"))
    p.append(txt(186, 414, "4 · LEAN VERIFICA", "b"))
    p.append(txt(186, 432, "la fuente de verdad · su veredicto es inapelable",
                 "s"))

    # ── las cuatro salidas de Lean ─────────────────────────────────────────
    for x, arriba, abajo in RAMAS:
        cls = "ve" if arriba == "Lean acepta" else "al"
        p.append(caja("rama-%d" % x, x, 458, 136, 52, cls))
        p.append(txt(x + 68, 480, arriba, "m", "middle"))
        p.append(txt(x + 68, 498, abajo, "s", "middle"))
        p.append(ruta((432, 442), (432, 450), (x + 68, 450), (x + 68, 458)))

    # los dos reintentos, que vuelven al flujo
    p.append(ruta((238, 510), (238, 526), (138, 526), (138, 417), (166, 417)))
    p.append(ruta((384, 510), (384, 542), (98, 542), (98, 248), (166, 248)))

    # ── 5 · la cascada de tácticas ─────────────────────────────────────────
    p.append(ruta((530, 510), (530, 530)))
    p.append(caja("paso5", 170, 532, 460, 72, "gr"))
    p.append(txt(186, 554, "5 · EL GRAFO ORDENA LAS TÁCTICAS", "b"))
    p.append(txt(186, 574, "12 tácticas · premisas sólo si el objetivo "
                           "engancha", "s"))
    p.append(txt(186, 592, "APORTA · 2,4× menos intentos sobre 1600 pruebas de "
                           "Mathlib", "s"))

    # ── el veredicto final ─────────────────────────────────────────────────
    p.append(ruta((400, 604), (400, 616)))
    p.append(ruta((676, 510), (676, 616)))
    p.append(caja("veredicto", 170, 618, 574, 98, "bg"))
    p.append(txt(186, 640, "EL VEREDICTO FINAL — siete estados, no dos", "b"))
    for fila, y in zip(VEREDICTOS, (652, 682)):
        x = 186
        for s, cls in fila:
            marca, w = chip(x, y, s, cls)
            p.append(marca)
            x += w + 10

    # ── 6 · el LLM traduce, y la salida ────────────────────────────────────
    p.append(ruta((744, 667), (768, 667)))
    p.append(caja("paso6", 770, 618, 280, 98, "ll"))
    p.append(txt(786, 642, "6 · EL LLM TRADUCE", "b"))
    p.append(txt(786, 664, "explica el código que Lean", "s"))
    p.append(txt(786, 680, "aceptó — no lo que el", "s"))
    p.append(txt(786, 696, "modelo creía que era cierto", "s"))

    p.append(ruta((910, 716), (910, 740)))
    p.append(caja("respuesta", 770, 742, 280, 52, "bg", 9, "salida"))
    p.append(txt(910, 766, "respuesta", "b", "middle"))
    p.append(txt(910, 784, "el veredicto va delante, siempre", "s", "middle"))

    # la rama conversacional baja por fuera y llega a la misma salida
    p.append(ruta((744, 68), (1074, 68), (1074, 775), (1052, 775)))
    p.append(txt(752, 106, "sin verificación formal", "s"))

    # ── lo que no está en la cadena ────────────────────────────────────────
    p.append(caja("nota", 770, 124, 270, 380, "bg", 9, "deco"))
    p.append(txt(786, 148, "Lo que el dibujo NO cuenta", "b"))
    y = 172
    for bloque in NOTA:
        for linea in bloque:
            p.append(txt(786, y, linea, "s"))
            y += 17
        y += 16

    p.append("</svg>")
    io.open(SALIDA, "w", encoding="utf-8").write("\n".join(p))

    # ── y NADA puede depender del <style> ──────────────────────────────────
    # Si el bloque de estilo no llega —otra CSP, otro sanitizador, otro visor—
    # un elemento sin `fill` propio se pinta NEGRO por defecto y el dibujo se
    # convierte en una mancha. El tema claro tiene que ir en los atributos de
    # presentacion; el <style> solo puede llevar el oscuro.
    _els = re.findall(r"<(?:rect|text|circle|path)\b[^>]*>",
                      io.open(SALIDA, encoding="utf-8").read())
    _pelados = [e[:70] for e in _els if "fill=" not in e]


    # ── el dibujo tiene que cerrar, y se comprueba ─────────────────────────
    # Esto es lo que fallo: el paso 5 tenia entrada y no tenia salida, y nadie
    # lo vio hasta que el usuario leyo el dibujo. Se mira el registro, no el
    # SVG: parsear el propio SVG ya rompio dos guardianes antes.
    def toca(c, px, py, m=16):
        _, x, y, w, h = c[:5]
        return (x - m <= px <= x + w + m) and (y - m <= py <= y + h + m)

    sin_entrada, sin_salida = [], []
    for c in CAJAS:
        rol = c[5]
        entra = any(toca(c, a[2], a[3]) for a in ARCOS)
        sale = any(toca(c, a[0], a[1]) for a in ARCOS)
        if not entra and rol != "entrada":
            sin_entrada.append(c[0])
        if not sale and rol != "salida":
            sin_salida.append(c[0])

    sin_oscuro = sorted(set(CLARO) - set(OSCURO))
    print("  clases sin tema oscuro: %s" % (sin_oscuro or "ninguna"))
    fuera = [c[0] for c in CAJAS if c[1] + c[3] > W or c[2] + c[4] > H]

    # y ningun texto puede salirse de su caja: sin renderizador a mano es lo
    # unico que avisa de una linea que se derrama sobre la de al lado
    desborda = []
    for x, y, cad, cls, anc in TEXTOS:
        w = len(cad) * ANCHO.get(cls, 6.0)
        x0 = x if anc == "start" else (x - w / 2 if anc == "middle" else x - w)
        dentro = [c for c in TODAS
                  if c[0] <= x <= c[0] + c[2] and c[1] <= y - 6 <= c[1] + c[3]]
        if not dentro:
            continue
        c = min(dentro, key=lambda q: q[2] * q[3])
        if x0 < c[0] + 5 or x0 + w > c[0] + c[2] - 5:
            desborda.append(cad[:38])
    print("  texto que se sale     : %s" % (desborda or "ninguno"))
    print("  sin color propio      : %s" % (_pelados or "ninguno"))
    print("  cajas: %d · flechas: %d" % (len(CAJAS), len(ARCOS)))
    print("  sin flecha que entre : %s" % (sin_entrada or "ninguna"))
    print("  sin flecha que salga : %s" % (sin_salida or "ninguna"))
    print("  fuera del lienzo     : %s" % (fuera or "ninguna"))
    if sin_entrada or sin_salida or fuera or desborda or sin_oscuro or _pelados:
        print("     ATENCIÓN: el diagrama corta el flujo donde el código sigue")
        return 1
    print("\n  -> %s (%.1f KB)" % (SALIDA, os.path.getsize(SALIDA) / 1024))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    sys.exit(main(a))
