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
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: Mismo motivo que en dibujar_flujo: el tema claro va en atributos de
#: presentacion para que el dibujo no dependa de que su <style> llegue vivo
#: cuando GitHub lo sirve como <img>. El <style> queda solo para el oscuro.
SANS = "ui-sans-serif,system-ui,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,monospace"

CLARO = {
    "e":  {"fill": "none", "stroke": "#1b1e17", "opacity": ".11"},
    "n":  {"stroke": "none"},
    "g":  {"fill": "#564c9e"},
    "c":  {"fill": "#167a68"},
    "l":  {"fill": "#b4761f"},
    "t":  {"fill": "#ae3b35"},
    "si": {"opacity": ".38"},
    "sm": {"fill": "#1b1e17", "font-family": SANS, "font-size": "10",
           "opacity": ".62"},
    "tt": {"fill": "#1b1e17", "font-family": MONO, "font-size": "12",
           "font-weight": "600"},
    "lb": {"fill": "#1b1e17", "font-family": SANS, "font-size": "10.5",
           "font-weight": "600", "opacity": ".8"},
}

OSCURO = {
    "e":  {"stroke": "#e8e6de", "opacity": ".16"},
    "g":  {"fill": "#948bdd"},
    "c":  {"fill": "#4dc0aa"},
    "l":  {"fill": "#e2a94f"},
    "t":  {"fill": "#e2827a"},
    "sm": {"fill": "#e8e6de"},
    "tt": {"fill": "#e8e6de"},
    "lb": {"fill": "#e8e6de"},
}


def pinta(*clases):
    """Los atributos de presentacion de varias clases, en orden."""
    junto = {}
    for c in clases:
        junto.update(CLARO[c])
    return "".join(' %s="%s"' % kv for kv in sorted(junto.items()))


def estilo(ident, oscuro):
    """El <style> lleva SOLO el tema oscuro; el claro va en los atributos."""
    reglas = "".join(
        "#%s .%s{%s}" % (ident, cls, ";".join("%s:%s" % kv
                                                  for kv in sorted(d.items())))
        for cls, d in oscuro.items())
    return "<style>@media(prefers-color-scheme:dark){%s}</style>" % reglas

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
    p.append(estilo("fig-grafo", OSCURO))

    for a_, b_ in dep:
        x1, y1 = pos[a_]
        x2, y2 = pos[b_]
        p.append('<path class="e"%s d="M%.0f %.0f Q%.0f %.0f %.0f %.0f"/>'
                 % (pinta("e"), x1, y1, (x1 + CX) / 2, (y1 + CY) / 2, x2, y2))

    for sid in dib:
        x, y = pos[sid]
        col = COL.get(pilar_de[sid], "g")
        clases = ["n", col] + (["si"] if sid in sin_interpretar else [])
        r = 6.5 if prof[sid] == 0 else (4.6 if sid in areas else 3.2)
        p.append('<circle class="%s"%s cx="%.1f" cy="%.1f" r="%.1f"/>'
                 % (" ".join(clases), pinta(*clases), x, y, r))

    # nombres: solo pilares y areas, que son lo que estructura
    for sid in raices + areas:
        if sid not in pos:
            continue
        x, y = pos[sid]
        anc = "middle" if abs(x - CX) < 45 else ("end" if x < CX else "start")
        dx = 0 if anc == "middle" else (-7 if anc == "end" else 7)
        txt = sid.replace("area-", "") if sid in areas else sid
        cl = "tt" if sid in raices else "lb"
        p.append('<text class="%s"%s x="%.0f" y="%.0f" text-anchor="%s">%s'
                 '</text>' % (cl, pinta(cl), x + dx, y - 8, anc, txt))

    # las tacticas, aparte
    entran = sum(1 for m in g.morphisms
                 if m.target_id in tac and m.source_id not in tac)
    p.append('<text class="tt"%s x="%d" y="%d">las %d tácticas, aparte'
             '</text>' % (pinta("tt"), 966, 620, len(tac)))
    p.append('<text class="sm"%s x="%d" y="%d">%d aristas entran · 0 '
             'salen</text>' % (pinta("sm"), 966, 638, entran))
    for k, t in enumerate(sorted(tac)):
        p.append('<circle class="n t"%s cx="%d" cy="%d" r="3.2"/>'
                 % (pinta("n", "t"), 972, 660 + k * 13))
        p.append('<text class="sm"%s x="%d" y="%d">%s</text>'
                 % (pinta("sm"), 982, 664 + k * 13, t.replace("tactic-", "")))

    # leyenda
    cnt = collections.Counter(pilar_de[s] for s in dib)
    for k, (c, txt) in enumerate([("g", "SET  %d" % cnt["SET"]),
                                  ("c", "CAT  %d" % cnt["CAT"]),
                                  ("l", "LOG  %d" % cnt["LOG"]),
                                  ("t", "TYPE %d" % cnt["TYPE"])]):
        p.append('<circle class="n %s"%s cx="%d" cy="%d" r="4"/>'
                 % (c, pinta("n", c), 972, 58 + k * 19))
        p.append('<text class="sm"%s x="%d" y="%d">%s</text>'
                 % (pinta("sm"), 982, 62 + k * 19, txt))
    y0 = 58 + 4 * 19 + 8
    p.append('<circle class="n g si"%s cx="972" cy="%d" r="4"/>'
             % (pinta("n", "g", "si"), y0))
    p.append('<text class="sm"%s x="982" y="%d">%d sin interpretar'
             '</text>' % (pinta("sm"), y0 + 4, len(sin_interpretar)))
    p.append('<circle class="n g"%s cx="972" cy="%d" r="4.6"/>'
             % (pinta("n", "g"), y0 + 19))
    p.append('<text class="sm"%s x="982" y="%d">%d de área, que cosen'
             '</text>' % (pinta("sm"), y0 + 23, len(areas)))
    p.append('<text class="tt"%s x="966" y="%d">%d nodos · %d morfismos'
             '</text>' % (pinta("tt"), y0 + 54, len(S), len(g.morphisms)))
    p.append('<text class="sm"%s x="966" y="%d">se dibujan %d '
             'dependencias</text>' % (pinta("sm"), y0 + 72, len(dep)))
    p.append("</svg>")

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    io.open(SALIDA, "w", encoding="utf-8").write("\n".join(p))

    # ── y NADA puede depender del <style> ──────────────────────────────────
    # Si el bloque de estilo no llega —otra CSP, otro sanitizador, otro visor—
    # un elemento sin `fill` propio se pinta NEGRO por defecto y el dibujo se
    # convierte en una mancha. El tema claro tiene que ir en los atributos de
    # presentacion; el <style> solo puede llevar el oscuro.
    _els = re.findall(r"<(?:rect|text|circle|path)\b[^>]*>",
                      io.open(SALIDA, encoding="utf-8").read())
    _pelados = [e[:70] for e in _els if "fill=" not in e]


    # ── el dibujo tiene que ser legible, y se comprueba ────────────────────
    ps = list(pos.values())
    cerca = sum(1 for i in range(len(ps)) for j in range(i + 1, len(ps))
                if math.dist(ps[i], ps[j]) < 5)
    encimados = sum(1 for i in range(len(ps)) for j in range(i + 1, len(ps))
                    if math.dist(ps[i], ps[j]) < 1.5)
    fuera = [q for q in ps if not (0 <= q[0] <= W and 0 <= q[1] <= H)]
    print("  sin color propio      : %s" % (_pelados or "ninguno"))
    print("  nodos dibujados : %d de %d (%d tácticas aparte)"
          % (len(dib), len(S), len(tac)))
    print("  sin colocar     : %d" % (len(cuerpo) - len(dib)))
    print("  aristas         : %d" % len(dep))
    print("  pares a <5 px   : %d · encimados: %d · fuera del lienzo: %d"
          % (cerca, encimados, len(fuera)))
    if encimados or fuera or _pelados:
        print("     ATENCION: el dibujo pierde nodos o pierde su color")
    print("\n  -> %s (%.1f KB)" % (SALIDA, os.path.getsize(SALIDA) / 1024))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    sys.exit(main(a))
