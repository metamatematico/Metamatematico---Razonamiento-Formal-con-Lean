# -*- coding: utf-8 -*-
"""La hoja de trabajo: que hay que curar a mano, con todo para decidirlo.

QUE ES ESTO
-----------
De 203 enunciados reales de Mathlib, 62 nombran algo que la cabecera fija no
alcanza. De esos 62, en 43 el grafo NO TIENE NINGUN NODO que lo cubra — el
69 %. Ningun recorrido recupera lo que no esta, asi que esos 43 son curacion.

Esta hoja los reune, uno por modulo, con lo unico que no se puede automatizar:
la decision. Y con todo lo que si se puede, ya resuelto.

QUE TRAE CADA ENTRADA
---------------------
  · los sustantivos mas citados del modulo, LEIDOS DE SU DECLARACION
    (no deducidos de la ruta: de los deducidos, 95 de 447 no existian)
  · los conceptos que el grafo ya tiene en esa area, como padres candidatos
  · si el area tiene rama en Mathlib

QUE HAY QUE DECIDIR, Y POR QUE NO LO DECIDE NADIE MAS
-----------------------------------------------------
1. LA MARCA. Es la decision que sostiene el grafo:

       C  una categoria        -> VERTICE
       S  una subcategoria plena-> VERTICE (y la inclusion es arista)
       F  un funtor o una clase de flechas -> ARISTA, no vertice
       O  un objeto individual  -> vertice degenerado
       T  ni objetos ni flechas -> FUERA

   No es opinable ni automatizable. `homology` es F: no es una coleccion que
   se pueda colimitar, es el funtor A LO LARGO DEL CUAL se colimita.
   `prime-factorization` es T: es un teorema, no un objeto. Un proceso
   automatico los habria hecho nodos y habria roto la categoria.

2. EL PADRE. De que concepto es especializacion. La flecha va del general al
   especifico.

3. CUAL DE LOS NOMBRES. Que exista no lo hace el correcto: `Nat.Prime` es la
   nocion de primo y `Nat.minFac` no lo es.

LO QUE NO HAY QUE DECIDIR, porque ya esta verificado: si el nombre existe, en
que modulo vive, cual es el canonico (las citas) y el DAG de imports.

Y NADA ENTRA SIN MEDIRSE:

    python -m scripts.recuperacion_contra_proofnet

Precision y cobertura contra 371 formalizaciones de oro, con su modelo nulo y
sin gastar API. Baseline hoy: 21,3 % / 18,4 % contra 1,45 % / 3,3 %.
Si la precision baja, esa tanda no entra. Ya paso: ofrecer los sustantivos de
los nodos generados bajaba de 14,0 % a 11,5 %.

    python -m scripts.hoja_de_curacion
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

SALIDA = os.path.join(RAIZ, "docs", "CURACION_PENDIENTE.md")

#: rama de Mathlib -> area del grafo. Las que no estan aqui NO tienen area:
#: Mathlib no organiza asi, y eso ya avisa de que el concepto puede ser T.
RAMA_A_AREA = {
    "Algebra": "algebra", "RingTheory": "algebra", "GroupTheory": "algebra",
    "LinearAlgebra": "algebra", "FieldTheory": "algebra",
    "RepresentationTheory": "algebra",
    "Analysis": "analysis", "MeasureTheory": "analysis",
    "Topology": "topology", "AlgebraicTopology": "topology",
    "NumberTheory": "number-theory", "Combinatorics": "combinatorics",
    "Logic": "logic", "ModelTheory": "logic",
    "Computability": "computation", "Probability": "probability",
    "Dynamics": "probability",
    "Geometry": "geometry", "AlgebraicGeometry": "geometry",
    "CategoryTheory": "category-theory", "SetTheory": "set-theory",
    "Order": "", "Data": "", "Control": "", "Init": "", "Util": "",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--k", type=int, default=4)
    args = ap.parse_args()

    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    emer = os.path.join(RAIZ, "data", "lo_que_falta_emerge.json")
    sus = os.path.join(RAIZ, "data", "sustantivos_mathlib.jsonl")
    web = os.path.join(RAIZ, "data", "grafo_web.json")
    for p in (emer, sus, web):
        if not os.path.exists(p):
            print("falta %s" % p)
            return 1

    # los modulos pendientes
    d = json.load(io.open(emer, encoding="utf-8"))
    mods = []
    for x in d.get("detalle", []):
        if x.get("veredicto") != "sin_nodo":
            continue
        for m in x.get("faltan", []):
            if m not in mods:
                mods.append(m)

    # los sustantivos, por modulo
    por = {}
    for l in io.open(sus, encoding="utf-8"):
        l = l.strip()
        if not l:
            continue
        try:
            s = json.loads(l)
        except ValueError:
            continue
        por.setdefault(s.get("modulo") or "", []).append(s)
    for m in por:
        por[m].sort(key=lambda x: -int(x.get("citas") or 0))

    # los conceptos que ya hay, por area
    nodos = json.load(io.open(web, encoding="utf-8"))["nodos"]
    por_area = {}
    for n in nodos:
        if n["s"] != "CONCEPTO":
            continue
        por_area.setdefault(n.get("a") or "", []).append(n["id"])

    # agrupar por rama
    grupos = {}
    for m in mods:
        rama = m.split(".")[1] if m.count(".") > 1 else "?"
        grupos.setdefault(rama, []).append(m)

    L = []
    L.append("# Curación pendiente\n")
    L.append("> Generado por `scripts/hoja_de_curacion.py`. **No editar a "
             "mano**: se regenera.\n")
    L.append("")
    L.append("De 203 enunciados reales de Mathlib tomados al azar, **62 "
             "nombran algo que la cabecera fija no alcanza**. De esos, en "
             "**43 el grafo no tiene ningún nodo** que lo cubra — el 69 %. "
             "Ningún recorrido recupera lo que no está.")
    L.append("")
    L.append("Son **%d módulos distintos**, repartidos así:" % len(mods))
    L.append("")
    L.append("| rama | módulos |")
    L.append("|---|---|")
    for r, ms in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        L.append("| %s | %d |" % (r, len(ms)))
    L.append("")
    L.append("---\n")
    L.append("## Qué hay que decidir en cada uno\n")
    L.append("**1 · La marca.** Es lo que sostiene el grafo y no lo decide "
             "nada automático:\n")
    L.append("| | | |")
    L.append("|---|---|---|")
    L.append("| `C` | una categoría | **vértice** |")
    L.append("| `S` | una subcategoría plena | **vértice**, y la inclusión "
             "es arista |")
    L.append("| `F` | un funtor o clase de flechas | **arista**, no vértice |")
    L.append("| `O` | un objeto individual | vértice degenerado |")
    L.append("| `T` | ni objetos ni flechas | **fuera** |")
    L.append("")
    L.append("`homology` es `F`: no es una colección que se pueda colimitar, "
             "es el funtor *a lo largo del cual* se colimita. "
             "`prime-factorization` es `T`: es un teorema, no un objeto.")
    L.append("")
    L.append("**2 · El padre.** De qué concepto es especialización. La flecha "
             "va del general al específico.")
    L.append("")
    L.append("**3 · Cuál de los nombres.** Que exista no lo hace correcto: "
             "`Nat.Prime` es la noción de primo, `Nat.minFac` no.")
    L.append("")
    L.append("Lo que **no** hay que decidir, porque ya está verificado: si el "
             "nombre existe, en qué módulo vive, cuál es el canónico (las "
             "citas) y el DAG de imports.")
    L.append("")
    L.append("---\n")

    for rama in sorted(grupos, key=lambda r: -len(grupos[r])):
        area = RAMA_A_AREA.get(rama, "")
        L.append("## %s%s\n" % (rama, "  ·  área `%s`" % area if area
                                else "  ·  **sin área en el grafo**"))
        if not area:
            L.append("> Mathlib no organiza esta rama como un área del grafo. "
                     "Puede que estos conceptos sean `T`.\n")
        elif por_area.get(area):
            L.append("Padres candidatos ya en el grafo: %s\n"
                     % ", ".join("`%s`" % x for x in sorted(
                         por_area[area])[:14]))
        for m in sorted(grupos[rama]):
            ss = por.get(m, [])[:args.k]
            L.append("### `%s`\n" % m.replace("Mathlib.", ""))
            if not ss:
                L.append("Sin sustantivos propios: sólo aporta teoremas. El "
                         "grafo aporta **sustantivos** —de sus 176 "
                         "identificadores ninguno es un teorema—, así que "
                         "probablemente no le toca.\n")
                continue
            L.append("| identificador | tipo | citas |")
            L.append("|---|---|---|")
            for s in ss:
                L.append("| `%s` | %s | %d |" % (
                    s["nombre"], s.get("tipo") or "",
                    int(s.get("citas") or 0)))
            L.append("")
            L.append("- [ ] marca: `C` / `S` / `F` / `O` / `T`")
            L.append("- [ ] padre:")
            L.append("- [ ] identificadores que se quedan:")
            L.append("")

    L.append("---\n")
    L.append("## Antes de dar por buena una tanda\n")
    L.append("```\npython -m scripts.recuperacion_contra_proofnet\n```\n")
    L.append("Precisión y cobertura contra 371 formalizaciones de oro, con su "
             "modelo nulo y sin gastar API.\n")
    L.append("**Baseline hoy: 21,3 % / 18,4 % contra 1,45 % / 3,3 % — "
             "14,7×.** Si la precisión baja, esa tanda no entra.")
    L.append("")
    L.append("Ya pasó: ofrecer los sustantivos de los nodos generados bajaba "
             "de 14,0 % a 11,5 %. Añadir vocabulario tiene coste.")
    L.append("")

    io.open(SALIDA, "w", encoding="utf-8").write("\n".join(L))
    print("modulos pendientes: %d, en %d ramas" % (len(mods), len(grupos)))
    print("-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
