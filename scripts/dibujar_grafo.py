# -*- coding: utf-8 -*-
"""Dibuja el grafo tal como está, sin graphviz y sin maquillarlo.

`graphviz` no esta instalado y el `.dot` oficial de Mathlib son 2,5 MB, asi que
el SVG se genera aqui. Lo que se dibuja es el grafo del runtime —298 nodos,
1 722 morfismos— con una disposicion que hace visible su estructura real:

  · cuatro sectores, uno por pilar fundacional (SET, CAT, LOG, TYPE)
  · anillos por nivel: las bases al centro, las sub-ramas fuera
  · los generados desde Mathlib en tono distinto, porque NO estan
    interpretados categoricamente y esa diferencia no debe perderse en el dibujo
  · las nueve tacticas aparte, abajo, porque son SUMIDEROS: 453 aristas entran
    y ninguna sale. Dibujarlas dentro convertia el grafo en una maraña que
    ocultaba el resto — y esa maraña es justamente un hallazgo, no un problema
    de dibujo

No se dibujan las 1 722 aristas: se dibujan las de DEPENDENCY entre nodos
curados, que son las que tienen lectura categorica. Las demas se cuentan en la
leyenda. Un dibujo que enseña todo no enseña nada.

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

SALIDA = "E:/Metamatematico/docs/img/10-grafo-real.svg"
W, H = 1100, 780
CX, CY = 520, 372

PILAR_ANG = {"SET": (-60, 120), "CAT": (120, 200),
             "LOG": (200, 260), "TYPE": (260, 300)}
COLOR = {"SET": "g", "CAT": "c", "LOG": "l", "TYPE": "t"}


def main(_):
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.types import MorphismType as MT

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph
    S = g.skills

    tac = {s.id for s in S if (s.metadata or {}).get("category") == "lean-tactics"}
    cob = {s.id for s in S if (s.metadata or {}).get("origen") == "mathlib"}
    cuerpo = [s for s in S if s.id not in tac]

    # posicion: sector por pilar, radio por nivel
    porp = collections.defaultdict(list)
    for s in cuerpo:
        porp[s.pillar.name if s.pillar else "SET"].append(s)
    pos = {}
    for pil, lst in porp.items():
        a0, a1 = PILAR_ANG.get(pil, (0, 90))
        # dentro del sector, ordenados por nivel y luego por id
        lst = sorted(lst, key=lambda s: (s.level, s.id))
        for k, s in enumerate(lst):
            ang = math.radians(a0 + (a1 - a0) * (k + 0.5) / len(lst))
            r = 58 + s.level * 62 + (17 if s.id in cob else 0)
            pos[s.id] = (CX + r * math.cos(ang), CY + r * math.sin(ang))

    dep = [(m.source_id, m.target_id) for m in g.morphisms
           if m.morphism_type == MT.DEPENDENCY
           and m.source_id in pos and m.target_id in pos
           and m.source_id not in cob and m.target_id not in cob]

    # La descripcion accesible tambien lleva las cifras CALCULADAS: escritas a
    # mano mienten en cuanto el grafo cambia, y ademas en silencio — es lo que
    # paso con «298 nodos · 1722 morfismos», que el dibujo siguio diciendo
    # despues de que el grafo creciera a 315 y 1917.
    aria = ("El grafo del runtime: %d nodos repartidos en cuatro sectores, uno "
            "por pilar fundacional, con las bases al centro y las sub-ramas "
            "hacia fuera. Los %d nodos generados desde Mathlib van en tono mas "
            "claro porque no estan interpretados categoricamente. Las %d "
            "tacticas se dibujan aparte abajo porque son sumideros: reciben "
            "aristas y no emiten ninguna."
            % (len(S), len(cob), len(tac)))
    p = ['<svg xmlns="http://www.w3.org/2000/svg" role="img" '
         'aria-label="%s" viewBox="0 0 %d %d">' % (aria, W, H)]
    # EL SVG LLEVA SU PROPIO COLOR, y para los dos temas.
    #
    # Se usa dentro del artefacto (inline, donde heredaria los tokens) pero
    # tambien en el README como <img>, y ahi las variables CSS de la pagina no
    # llegan: un SVG sin colores propios sale negro sobre fondo oscuro. La
    # media query dentro del propio SVG si funciona en ambos contextos.
    p.append('<style>'
             'svg{color:#1b1e17}'
             '.e{stroke:currentColor;opacity:.13;fill:none}'
             '.n{stroke:none}'
             '.g{fill:#564c9e}.c{fill:#167a68}.l{fill:#b4761f}.t{fill:#ae3b35}'
             '.cob{opacity:.42}'
             '.sm{font:10px ui-sans-serif,system-ui;fill:currentColor;opacity:.62}'
             '.tt{font:600 12px ui-monospace,monospace;fill:currentColor}'
             '@media(prefers-color-scheme:dark){'
             'svg{color:#e8e6de}'
             '.g{fill:#948bdd}.c{fill:#4dc0aa}.l{fill:#e2a94f}.t{fill:#e2827a}'
             '.e{opacity:.18}}'
             '</style>')

    for a, b in dep:
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        p.append('<path class="e" d="M%.0f %.0f Q%.0f %.0f %.0f %.0f"/>'
                 % (x1, y1, (x1 + x2) / 2 + (y2 - y1) * .12,
                    (y1 + y2) / 2 - (x2 - x1) * .12, x2, y2))

    for s in cuerpo:
        x, y = pos[s.id]
        cls = COLOR.get(s.pillar.name if s.pillar else "SET", "g")
        if s.id in cob:
            cls += " cob"
        r = 5.5 if s.level == 0 else 3.4
        p.append('<circle class="n %s" cx="%.0f" cy="%.0f" r="%.1f"/>'
                 % (cls, x, y, r))

    # los diez fundacionales, con nombre
    for s in cuerpo:
        if s.level == 0:
            x, y = pos[s.id]
            p.append('<text class="sm" x="%.0f" y="%.0f" text-anchor="middle">'
                     '%s</text>' % (x, y - 9, s.id))

    # las tacticas, aparte
    p.append('<text class="tt" x="%d" y="%d">las 9 tacticas, aparte</text>'
             % (860, 620))
    p.append('<text class="sm" x="%d" y="%d">453 aristas entran · 0 salen</text>'
             % (860, 638))
    for k, t in enumerate(sorted(tac)):
        p.append('<circle class="n t" cx="%d" cy="%d" r="3.4"/>'
                 % (866, 660 + k * 13))
        p.append('<text class="sm" x="%d" y="%d">%s</text>'
                 % (876, 664 + k * 13, t.replace("tactic-", "")))

    # leyenda
    ley = [("g", "SET  %d" % len(porp.get("SET", ()))),
           ("c", "CAT  %d" % len(porp.get("CAT", ()))),
           ("l", "LOG  %d" % len(porp.get("LOG", ()))),
           ("t", "TYPE %d" % len(porp.get("TYPE", ())))]
    for k, (c, txt) in enumerate(ley):
        p.append('<circle class="n %s" cx="%d" cy="%d" r="4"/>'
                 % (c, 866, 60 + k * 19))
        p.append('<text class="sm" x="%d" y="%d">%s</text>'
                 % (876, 64 + k * 19, txt))
    p.append('<circle class="n g cob" cx="866" cy="%d" r="4"/>' % (60 + 4 * 19))
    p.append('<text class="sm" x="876" y="%d">%d generados, sin interpretar</text>'
             % (64 + 4 * 19, len(cob)))
    # CALCULADO, no escrito a mano. Estaba fijo en «298 nodos · 1722
    # morfismos» y el dibujo siguio diciendolo despues de que el grafo creciera
    # a 315 y 1917. Una figura con cifras a mano miente en cuanto cambia el
    # dato, y ademas en silencio.
    p.append('<text class="tt" x="860" y="%d">%d nodos · %d morfismos</text>'
             % (60 + 6 * 19, len(S), len(g.morphisms)))
    p.append('<text class="sm" x="860" y="%d">se dibujan las %d dependencias '
             'entre curados</text>' % (60 + 7 * 19 - 4, len(dep)))
    p.append("</svg>")

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    io.open(SALIDA, "w", encoding="utf-8").write("\n".join(p))
    print("  nodos dibujados : %d (%d curados, %d generados)"
          % (len(cuerpo), len(cuerpo) - len(cob), len(cob)))
    print("  aristas         : %d de dependencia entre curados" % len(dep))
    print("  tacticas aparte : %d" % len(tac))
    print("\n  -> %s (%.1f KB)" % (SALIDA, os.path.getsize(SALIDA) / 1024))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    a = ap.parse_args()
    sys.exit(main(a))
