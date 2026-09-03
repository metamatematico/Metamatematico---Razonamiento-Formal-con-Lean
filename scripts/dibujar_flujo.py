# -*- coding: utf-8 -*-
"""El flujo de la consulta a la respuesta, dibujado desde lo que hoy hace el código.

POR QUE SE REHACE. El diagrama anterior se escribio a mano y decia «el grafo
actua en DOS puntos». Son TRES —el vocabulario del prompt, los modulos que
importa Lean, y el orden de las tacticas— y ademas cada uno tiene ya un
veredicto medido que el dibujo no contaba:

    1 · vocabulario   APORTA   12x sobre el azar (ProofNet)
    3 · imports       INERTE   empata con un conjunto fijo de 3 modulos
    6 · tacticas      APORTA   2,4x menos intentos

Un diagrama que presenta los tres como si fueran igual de utiles engaña, y era
justo lo que hacia: pintaba el paso 3 en violeta como contribucion del grafo
sin decir que se midio y no aporta.

Se genera con script y no a mano para que pueda actualizarse cuando el flujo
cambie — el anterior se quedo viejo y nadie lo noto hasta que se leyo entero.

EL SVG LLEVA SU PROPIO ESTILO porque en el README va como <img>, donde las
variables CSS de la pagina no llegan. Dentro del artefacto se le quita y hereda
los tokens del tema.

    python scripts/dibujar_flujo.py
"""
import argparse
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

SALIDA = "E:/Metamatematico/docs/img/00-flujo-real.svg"
W, H = 1120, 700


def caja(x, y, w, h, cls="", r=9):
    return ('<rect class="%s" x="%d" y="%d" width="%d" height="%d" rx="%d"/>'
            % (cls, x, y, w, h, r))


def txt(x, y, s, cls="t", anc="start"):
    return ('<text class="%s" x="%d" y="%d" text-anchor="%s">%s</text>'
            % (cls, x, y, anc, s))


def flecha(x1, y1, x2, y2, cls="ln"):
    return ('<path class="%s" d="M%d %d L%d %d" marker-end="url(#p)"/>'
            % (cls, x1, y1, x2, y2))


def main(_):
    p = ['<svg xmlns="http://www.w3.org/2000/svg" role="img" '
         'aria-label="El flujo de la consulta a la respuesta. La consulta entra '
         'por la interfaz y un clasificador decide si es matematica; si no lo '
         'es va al modelo conversacional sin verificacion formal. Si lo es, el '
         'grafo actua en tres puntos numerados: prepara el prompt con nombres '
         'de Mathlib comprobados, elige que modulos importa Lean, y ordena las '
         'tacticas si queda un sorry. Cada punto lleva su veredicto medido: el '
         'primero y el tercero aportan, el segundo es inerte. Lean verifica en '
         'medio y su veredicto tiene seis salidas distintas." '
         'viewBox="0 0 %d %d">' % (W, H)]
    p.append('<defs><marker id="p" viewBox="0 0 10 10" refX="9" refY="5" '
             'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
             '<path d="M0 0 L10 5 L0 10 z" class="pf"/></marker></defs>')
    p.append('<style>'
             'svg{color:#1b1e17}'
             '.bg{fill:#ffffff;stroke:#ddd6c2}'
             '.gr{fill:#e7e4f5;stroke:#564c9e}'
             '.ve{fill:#dbf0ea;stroke:#167a68}'
             '.ll{fill:#f5e7cf;stroke:#b4761f}'
             '.al{fill:#f6dfdc;stroke:#ae3b35}'
             '.ln{stroke:currentColor;opacity:.5;fill:none;stroke-width:1.6}'
             '.pf{fill:currentColor;opacity:.5}'
             '.t{font:13px ui-sans-serif,system-ui;fill:currentColor}'
             '.b{font:600 13px ui-sans-serif,system-ui;fill:currentColor}'
             '.s{font:11px ui-sans-serif,system-ui;fill:currentColor;opacity:.66}'
             '.m{font:11px ui-monospace,monospace;fill:currentColor;opacity:.72}'
             '.gt{fill:#564c9e}.vt{fill:#167a68}.lt{fill:#b4761f}.at{fill:#ae3b35}'
             '@media(prefers-color-scheme:dark){'
             'svg{color:#e8e6de}'
             '.bg{fill:#171b23;stroke:#2b3140}'
             '.gr{fill:#242038;stroke:#948bdd}'
             '.ve{fill:#152722;stroke:#4dc0aa}'
             '.ll{fill:#332714;stroke:#e2a94f}'
             '.al{fill:#331d1b;stroke:#e2827a}'
             '.gt{fill:#948bdd}.vt{fill:#4dc0aa}.lt{fill:#e2a94f}.at{fill:#e2827a}}'
             'rect{stroke-width:1.3}'
             '</style>')

    p.append(txt(24, 26, "DE LA ENTRADA A LA SALIDA", "b"))
    p.append(txt(232, 26, "— el grafo actúa en TRES puntos, y sólo dos aportan",
                 "s"))

    # entrada
    p.append(caja(24, 46, 150, 46, "bg"))
    p.append(txt(99, 68, "consulta", "b", "middle"))
    p.append(txt(99, 84, "UI · CLI", "s", "middle"))

    p.append(caja(196, 46, 176, 46, "bg"))
    p.append(txt(284, 66, "¿es matemática?", "t", "middle"))
    p.append(txt(284, 82, "forma + vocabulario", "s", "middle"))
    p.append(flecha(174, 69, 194, 69))

    p.append(caja(396, 46, 210, 46, "ll"))
    p.append(txt(501, 66, "LLM conversacional", "t", "middle"))
    p.append(txt(501, 82, "sin verificación formal", "s", "middle"))
    p.append(flecha(372, 69, 394, 69))
    p.append(txt(383, 62, "no", "s", "middle"))
    p.append(txt(290, 108, "sí", "s", "middle"))
    p.append(flecha(284, 92, 284, 122))

    # 1 · el grafo prepara
    p.append(caja(24, 126, 582, 74, "gr"))
    p.append(txt(40, 148, "1 · EL GRAFO PREPARA EL PROMPT", "b"))
    p.append(txt(40, 168, "conceptos activados · nombres de Mathlib "
                          "comprobados con #check · ejemplos few-shot", "s"))
    p.append(txt(40, 186, "APORTA · 12× sobre el azar, medido contra ProofNet",
                 "s"))
    p.append('<circle cx="590" cy="140" r="5" class="gt"/>')

    # 2 · LLM formaliza
    p.append(caja(24, 214, 582, 56, "ll"))
    p.append(txt(40, 236, "2 · EL LLM FORMALIZA", "b"))
    p.append(txt(40, 256, "escribe Lean 4 — no decide si es cierto", "s"))
    p.append(flecha(315, 200, 315, 212))

    # 3 · imports
    p.append(caja(24, 284, 582, 74, "gr"))
    p.append(txt(40, 306, "3 · EL GRAFO ELIGE QUÉ MÓDULOS VE LEAN", "b"))
    p.append(txt(40, 326, "descarta `import Mathlib` — 742 s, más que el "
                          "timeout", "s"))
    p.append(txt(40, 344, "INERTE · empata con un conjunto fijo de 3 módulos, "
                          "y el margen total son 2,5 puntos", "s"))
    p.append(flecha(315, 270, 315, 282))

    # 4 · Lean
    p.append(caja(24, 372, 582, 52, "ve"))
    p.append(txt(40, 394, "4 · LEAN VERIFICA", "b"))
    p.append(txt(40, 412, "la fuente de verdad · su veredicto es inapelable",
                 "s"))
    p.append(flecha(315, 358, 315, 370))

    # los seis veredictos
    ver = [("verificado", "ve"), ("no hay prueba", "bg"),
           ("lo pedido es falso", "bg"), ("error de módulo", "bg"),
           ("error semántico", "bg"), ("queda un `sorry`", "al")]
    for i, (t, c) in enumerate(ver):
        x = 24 + (i % 3) * 196
        y = 442 + (i // 3) * 40
        p.append(caja(x, y, 182, 30, c, 15))
        p.append(txt(x + 91, y + 20, t, "m", "middle"))
    p.append(flecha(315, 424, 315, 440))

    # 5 · tacticas
    p.append(caja(24, 534, 582, 74, "gr"))
    p.append(txt(40, 556, "5 · EL GRAFO ORDENA LAS TÁCTICAS", "b"))
    p.append(txt(40, 576, "12 tácticas · premisas sólo si el objetivo engancha "
                          "con algo específico", "s"))
    p.append(txt(40, 594, "APORTA · 2,4× menos intentos, medido sobre 1600 "
                          "pruebas de Mathlib", "s"))
    p.append(flecha(115, 512, 115, 532))

    # 6 · traduce y salida
    p.append(caja(646, 372, 450, 74, "ll"))
    p.append(txt(662, 394, "6 · EL LLM TRADUCE EL VEREDICTO", "b"))
    p.append(txt(662, 414, "explica el código que Lean aceptó —", "s"))
    p.append(txt(662, 432, "no lo que el modelo creía", "s"))
    p.append(flecha(606, 398, 644, 398))

    p.append(caja(646, 470, 450, 66, "bg"))
    p.append(txt(871, 496, "respuesta", "b", "middle"))
    p.append(txt(871, 516, "el veredicto va DELANTE del texto, siempre", "s",
                 "middle"))
    p.append(flecha(871, 446, 871, 468))

    # nota
    p.append(caja(646, 126, 450, 210, "bg"))
    p.append(txt(662, 150, "Lo que NO está en esta cadena", "b"))
    p.append(txt(662, 174, "Los co-reguladores deciden antes y la", "s"))
    p.append(txt(662, 190, "memoria MES registra después: ninguno", "s"))
    p.append(txt(662, 206, "formaliza ni verifica.", "s"))
    p.append(txt(662, 236, "La LISTA de 183 433 hechos de Mathlib", "s"))
    p.append(txt(662, 252, "no toca el prompt: alimenta el índice", "s"))
    p.append(txt(662, 268, "de premisas del paso 5.", "s"))
    p.append(txt(662, 298, "Los nombres de los 125 nodos generados", "s"))
    p.append(txt(662, 314, "no se inyectan: están deducidos, y 95", "s"))
    p.append(txt(662, 330, "de 447 no existen en Mathlib.", "s"))

    p.append("</svg>")

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    io.open(SALIDA, "w", encoding="utf-8").write("\n".join(p))

    # comprobacion: nada fuera del lienzo
    import re
    s = "\n".join(p)
    fuera = []
    for m in re.finditer(r'<rect[^>]*x="(\d+)" y="(\d+)" width="(\d+)" '
                         r'height="(\d+)"', s):
        x, y, w, h = map(int, m.groups())
        if x + w > W or y + h > H:
            fuera.append((x, y, w, h))
    for m in re.finditer(r'<text[^>]*x="(\d+)" y="(\d+)"', s):
        x, y = map(int, m.groups())
        if x > W or y > H:
            fuera.append((x, y))
    print("  cajas y textos fuera del lienzo: %d" % len(fuera))
    if fuera:
        print("     ATENCION:", fuera[:4])
    print("  -> %s (%.1f KB)" % (SALIDA, os.path.getsize(SALIDA) / 1024))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    sys.exit(main(a))
