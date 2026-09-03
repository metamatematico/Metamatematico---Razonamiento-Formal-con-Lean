# -*- coding: utf-8 -*-
"""Dibuja el grafo tal como está, sin graphviz y sin maquillarlo.

`graphviz` no esta instalado y el `.dot` oficial de Mathlib son 2,5 MB, asi que
el SVG se genera aqui, desde el grafo del runtime.

POR QUE ES UN ARBOL RADIAL Y NO ANILLOS POR NIVEL. La primera version ponia el
radio segun el nivel y el angulo segun el orden alfabetico dentro del pilar. Con
230 nodos en el pilar SET, mas de cien caian en el mismo anillo del mismo
sector: medido, 317 pares a menos de 5 px y 27 practicamente encimados. Un
dibujo ilegible, y que ademas mentia por omision — parecian menos nodos de los
que hay.

Ahora el angulo se reparte por TAMAÑO DE SUBARBOL siguiendo la jerarquia real
—pilar, area, dominio— que es la que se acaba de construir. Dos nodos no pueden
caer en el mismo sitio porque cada uno recibe su propia porcion de angulo. Y al
final se COMPRUEBA y se avisa si quedan superpuestos.

QUE SE DISTINGUE, y por que importa:

  · los 173 CURADOS llevan veredicto categorico
  · los 125 GENERADOS desde Mathlib y los 17 de AREA no lo llevan: van en tono
    mas claro, porque confundirlos seria afirmar que alguien decidio que son.
    En la version anterior los de area se dibujaban como curados
  · las 9 TACTICAS van aparte: son sumideros —reciben cientos de aristas y no
    emiten ninguna— y dentro convertian el grafo en un embudo

Las cifras del dibujo se CALCULAN. Estaban escritas a mano, y el dibujo siguio
diciendo «298 nodos · 1722 morfismos» despues de que el grafo creciera a 315 y
1917.

    python scripts/dibujar_grafo.py
"""
import argparse
import collections
import io
import math
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CLARO = [
    ('svg', 'color:#1b1e17'),
    ('.e', 'stroke:currentColor;opacity:.11;fill:none'),
    ('.n', 'stroke:none'),
    ('.g', 'fill:#564c9e'),
    ('.c', 'fill:#167a68'),
    ('.l', 'fill:#b4761f'),
    ('.t', 'fill:#ae3b35'),
    ('.si', 'opacity:.38'),
    ('.sm', 'font:10px ui-sans-serif,system-ui;fill:currentColor;opacity:.62'),
    ('.tt', 'font:600 12px ui-monospace,monospace;fill:currentColor'),
    ('.lb', 'font:600 10.5px ui-sans-serif,system-ui;fill:currentColor;opacity:.8'),
]

OSCURO = [
    ('svg', 'color:#e8e6de'),
    ('.g', 'fill:#948bdd'),
    ('.c', 'fill:#4dc0aa'),
    ('.l', 'fill:#e2a94f'),
    ('.t', 'fill:#e2827a'),
    ('.e', 'opacity:.16'),
]

def estilo(ident, claro, oscuro):
    """Prefija cada selector con el id del dibujo.

    Un <style> dentro de un <svg> inline en HTML NO esta encapsulado: define
    reglas del documento entero. Sin prefijo, `.l` y `.n` de aqui repintaban
    las cifras de portada del artefacto, que usan esas mismas clases.
    """
    def pre(reglas):
        salida = []
        for sel, decl in reglas:
            sel = "#%s" % ident if sel == "svg" else "#%s %s" % (ident, sel)
            salida.append("%s{%s}" % (sel, decl))
        return "".join(salida)
    return ("<style>" + pre(claro)
            + "@media(prefers-color-scheme:dark){" + pre(oscuro) + "}"
            + "</style>")


SALIDA = "E:/Metamatematico/docs/img/10-grafo-real.svg"
W, H = 1180, 820
CX, CY = 560, 410
R_PILAR, R_AREA, R_HOJA = 92, 214, 348


def main(_):
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.types import MorphismType as MT

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph
    S = g.skills
    meta = {s.id: (s.metadata or {}) for s in S}

    tac = {s.id for s in S if meta[s.id].get("category") == "lean-tactics"}
    areas = [s.id for s in S if meta[s.id].get("category") == "area"]
    gen = {s.id for s in S if meta[s.id].get("origen") == "mathlib"}
    sin_interpretar = gen | set(areas)
    L0 = [s.id for s in S if s.level == 0]
    pilar_de = {s.id: (s.pillar.name if s.pillar else "SET") for s in S}

    # ── quien cuelga de quien, por las aristas de jerarquia ────────────────
    hijos = collections.defaultdict(list)
    padre = {}
    for m in g.morphisms:
        if m.morphism_type != MT.DEPENDENCY:
            continue
        rel = (m.metadata or {}).get("relation", "")
        if rel in ("general-se-inyecta-en-especial", "pilar-sostiene-area"):
            if m.target_id in tac or m.target_id in padre:
                continue
            hijos[m.source_id].append(m.target_id)
            padre[m.target_id] = m.source_id

    base_de_pilar = {"SET": "zfc-axioms", "CAT": "cat-basics",
                     "LOG": "fol-deduction", "TYPE": "cic"}
    cuerpo = [s.id for s in S if s.id not in tac]
    for sid in cuerpo:
        if sid in padre or sid in L0:
            continue
        b = base_de_pilar.get(pilar_de[sid], "zfc-axioms")
        if b != sid:
            hijos[b].append(sid)
            padre[sid] = b

    # ── el angulo, por tamaño de subarbol: asi no puede haber colisiones ───
    memo = {}

    def tam(sid):
        if sid in memo:
            return memo[sid]
        memo[sid] = 1                       # corta recursion si hubiera ciclo
        h = hijos.get(sid, ())
        memo[sid] = 1 + sum(tam(x) for x in h) if h else 1
        return memo[sid]

    raices = [s for s in L0 if s in cuerpo]
    total = sum(tam(r) for r in raices) or 1
    pos, prof = {}, {}

    def coloca(sid, a0, a1, nivel):
        if sid in pos:
            return
        prof[sid] = nivel
        ang = math.radians((a0 + a1) / 2 - 90)
        r = (R_PILAR, R_AREA, R_HOJA)[nivel] if nivel < 3 else R_HOJA + (nivel - 2) * 36
        pos[sid] = (CX + r * math.cos(ang), CY + r * math.sin(ang))
        h = [x for x in hijos.get(sid, ()) if x not in pos]
        if not h:
            return
        pesos = [tam(x) for x in h]
        tot = sum(pesos) or 1
        a = a0
        for x, w in zip(h, pesos):
            paso = (a1 - a0) * w / tot
            coloca(x, a, a + paso, nivel + 1)
            a += paso

    a = 0.0
    for r in raices:
        paso = 360.0 * tam(r) / total
        coloca(r, a, a + paso, 0)
        a += paso

    dib = [s for s in cuerpo if s in pos]
    dep = [(m.source_id, m.target_id) for m in g.morphisms
           if m.morphism_type == MT.DEPENDENCY
           and m.source_id in pos and m.target_id in pos]

    COL = {"SET": "g", "CAT": "c", "LOG": "l", "TYPE": "t"}
    aria = ("El grafo del runtime como arbol radial: %d nodos que salen de los "
            "%d pilares fundacionales del centro hacia las sub-ramas de fuera, "
            "con el angulo repartido por tamaño de subarbol. Los %d generados "
            "desde Mathlib y los %d de area van en tono mas claro porque no "
            "estan interpretados categoricamente. Las %d tacticas se dibujan "
            "aparte porque son sumideros: reciben aristas y no emiten ninguna."
            % (len(S), len(raices), len(gen), len(areas), len(tac)))
    p = ['<svg xmlns="http://www.w3.org/2000/svg" role="img" '
         'id="fig-grafo" aria-label="%s" viewBox="0 0 %d %d">'
         % (aria, W, H)]
    p.append(estilo("fig-grafo", CLARO, OSCURO))

    for a_, b_ in dep:
        x1, y1 = pos[a_]
        x2, y2 = pos[b_]
        p.append('<path class="e" d="M%.0f %.0f Q%.0f %.0f %.0f %.0f"/>'
                 % (x1, y1, (x1 + CX) / 2, (y1 + CY) / 2, x2, y2))

    for sid in dib:
        x, y = pos[sid]
        cls = COL.get(pilar_de[sid], "g")
        if sid in sin_interpretar:
            cls += " si"
        r = 6.5 if prof[sid] == 0 else (4.6 if sid in areas else 3.2)
        p.append('<circle class="n %s" cx="%.1f" cy="%.1f" r="%.1f"/>'
                 % (cls, x, y, r))

    # nombres: solo pilares y areas, que son lo que estructura
    for sid in raices + areas:
        if sid not in pos:
            continue
        x, y = pos[sid]
        anc = "middle" if abs(x - CX) < 45 else ("end" if x < CX else "start")
        dx = 0 if anc == "middle" else (-7 if anc == "end" else 7)
        txt = sid.replace("area-", "") if sid in areas else sid
        p.append('<text class="%s" x="%.0f" y="%.0f" text-anchor="%s">%s</text>'
                 % ("tt" if sid in raices else "lb", x + dx, y - 8, anc, txt))

    # las tacticas, aparte
    entran = sum(1 for m in g.morphisms
                 if m.target_id in tac and m.source_id not in tac)
    p.append('<text class="tt" x="%d" y="%d">las %d tácticas, aparte</text>'
             % (966, 620, len(tac)))
    p.append('<text class="sm" x="%d" y="%d">%d aristas entran · 0 salen</text>'
             % (966, 638, entran))
    for k, t in enumerate(sorted(tac)):
        p.append('<circle class="n t" cx="%d" cy="%d" r="3.2"/>'
                 % (972, 660 + k * 13))
        p.append('<text class="sm" x="%d" y="%d">%s</text>'
                 % (982, 664 + k * 13, t.replace("tactic-", "")))

    # leyenda
    cnt = collections.Counter(pilar_de[s] for s in dib)
    for k, (c, txt) in enumerate([("g", "SET  %d" % cnt["SET"]),
                                  ("c", "CAT  %d" % cnt["CAT"]),
                                  ("l", "LOG  %d" % cnt["LOG"]),
                                  ("t", "TYPE %d" % cnt["TYPE"])]):
        p.append('<circle class="n %s" cx="%d" cy="%d" r="4"/>'
                 % (c, 972, 58 + k * 19))
        p.append('<text class="sm" x="%d" y="%d">%s</text>'
                 % (982, 62 + k * 19, txt))
    y0 = 58 + 4 * 19 + 8
    p.append('<circle class="n g si" cx="972" cy="%d" r="4"/>' % y0)
    p.append('<text class="sm" x="982" y="%d">%d sin interpretar</text>'
             % (y0 + 4, len(sin_interpretar)))
    p.append('<circle class="n g" cx="972" cy="%d" r="4.6"/>' % (y0 + 19))
    p.append('<text class="sm" x="982" y="%d">%d de área, que cosen</text>'
             % (y0 + 23, len(areas)))
    p.append('<text class="tt" x="966" y="%d">%d nodos · %d morfismos</text>'
             % (y0 + 54, len(S), len(g.morphisms)))
    p.append('<text class="sm" x="966" y="%d">se dibujan %d dependencias</text>'
             % (y0 + 72, len(dep)))
    p.append("</svg>")

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    io.open(SALIDA, "w", encoding="utf-8").write("\n".join(p))

    # ── el dibujo tiene que ser legible, y se comprueba ────────────────────
    ps = list(pos.values())
    cerca = sum(1 for i in range(len(ps)) for j in range(i + 1, len(ps))
                if math.dist(ps[i], ps[j]) < 5)
    encimados = sum(1 for i in range(len(ps)) for j in range(i + 1, len(ps))
                    if math.dist(ps[i], ps[j]) < 1.5)
    fuera = [q for q in ps if not (0 <= q[0] <= W and 0 <= q[1] <= H)]
    print("  nodos dibujados : %d de %d (%d tácticas aparte)"
          % (len(dib), len(S), len(tac)))
    print("  sin colocar     : %d" % (len(cuerpo) - len(dib)))
    print("  aristas         : %d" % len(dep))
    print("  pares a <5 px   : %d · encimados: %d · fuera del lienzo: %d"
          % (cerca, encimados, len(fuera)))
    if encimados or fuera:
        print("     ATENCION: el dibujo pierde nodos y miente por omisión")
    print("\n  -> %s (%.1f KB)" % (SALIDA, os.path.getsize(SALIDA) / 1024))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    sys.exit(main(a))
