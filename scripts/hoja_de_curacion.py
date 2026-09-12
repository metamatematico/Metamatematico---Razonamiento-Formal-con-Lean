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
       F  un funtor o una clase de flechas -> ARISTA *en este ambiente*
       O  un objeto individual  -> vertice degenerado
       T  ni objetos ni flechas -> FUERA

   `F` NO dice «esto no puede ser un vertice nunca»: eso es falso y esta
   demostrado que lo es en FlechasComoObjetos.lean —las flechas de C son
   exactamente los objetos de Arrow C, y los funtores son los objetos de
   C => D—. Dice que EN ESTE GRAFO, cuyos objetos son conceptos y cuyas
   flechas son dependencias, la etiqueta nombra una flecha.

   No es opinable ni automatizable. `homology` es F: no es una coleccion que
   se pueda colimitar aqui, es el funtor A LO LARGO DEL CUAL se colimita.
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
sin gastar API. Baseline hoy: 22,8 % / 18,0 % contra 1,45 % / 3,3 %.
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
SALIDA_TEX = os.path.join(RAIZ, "docs", "CURACION_PENDIENTE.tex")

#: Lo que LaTeX se come si no se escapa. Los identificadores de Mathlib traen
#: guiones bajos a mansalva —`card_aditivo`, `sumTransform`— y sin escapar
#: cada uno es un subindice o un error.
_ESCAPES = ((chr(92), r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
            ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"),
            ("}", r"\}"), ("~", r"\textasciitilde{}"),
            ("^", r"\textasciicircum{}"))


def tex(s: str) -> str:
    for a, b in _ESCAPES:
        s = s.replace(a, b)
    return s


#: Nombres que `#check` ACEPTA con Mathlib entero importado, aunque el indice
#: que construye `mapa_modulos_mathlib.construir()` no los encuentre. La
#: distincion es la que decide la curacion: si el nombre existe, lo que hay
#: que arreglar es el indice o asignar el modulo a mano; si no existe, hay que
#: reescribir el nombre. Verificados en un solo `#check` con Mathlib entero.
VERIFICADOS_CON_CHECK = frozenset({
    "MeasureTheory.condExp", "MeasureTheory.integral",
})


#: MODULOS QUE YA SE DECIDIERON Y NO PRODUCEN NODO. Siguen saliendo como
#: «sin nodo» en `lo_que_falta_emerge` —y es correcto: no hay nodo— pero no son
#: trabajo pendiente, son una decision tomada. Sin esta tabla la hoja los
#: volveria a pedir en cada tanda.
DECIDIDOS_SIN_NODO = {
    "Mathlib.Computability.AkraBazzi.SumTransform":
        "T · es el teorema de Akra-Bazzi y sus piezas de demostracion, no un "
        "objeto: el mismo caso que prime-factorization",
    "Mathlib.Control.Bitraversable.Basic":
        "T · interfaz de efectos de Lean: endofuntores sobre Type, y un lazo "
        "no es una dependencia",
    "Mathlib.Control.Fix":
        "T · Part.fix es el punto fijo con el que Lean define funciones "
        "parciales: maquinaria de definicion",
    "Mathlib.Control.Functor.Multivariate": "T · la misma rama de efectos",
    "Mathlib.Control.Monad.Cont": "T · la misma rama de efectos",
    "Mathlib.Data.TypeVec":
        "T · vectores de tipos para inductivos multivariados: infraestructura",
    "Mathlib.Order.PFilter":
        "T · un PFilter es un filtro sobre un preorden, pero `Order` no es "
        "area del grafo y un nodo solo no la justifica: sin padre la arista no "
        "existiria. Primer candidato si algun dia entra la teoria de ordenes",
    "Mathlib.SetTheory.Ordinal.Notation":
        "T · ONote y NONote son la forma normal de Cantor como dato "
        "computable: notacion, no objeto. El nodo `ordinals` ya existe",
    "Mathlib.AlgebraicTopology.SimplexCategory.GeneratorsRelations.Basic":
        "T · es SimplexCategory presentada por generadores: la misma categoria "
        "con otro nombre, y dos nombres para un objeto gastan dos plazas",
    "Mathlib.Topology.Category.TopCat.Basic":
        "CUBIERTO · `TopCat` ya es la identidad de `point-set-topology`. La "
        "convencion del proyecto pone el envoltorio categorico en el campo "
        "`lean` del concepto (group-theory lleva GrpCat), no en un nodo aparte",
}


def nombres_sin_modulo():
    """Las etiquetas que dan nombre al prompt y no dan modulo que importar.

    Sale de `data/mathlib_modulos.json`, que lo anota al construirse: no se
    recalcula aqui para que la hoja no pueda discrepar del mapa que usa el
    sistema.
    """
    p = os.path.join(RAIZ, "data", "mathlib_modulos.json")
    if not os.path.exists(p):
        return []
    d = json.load(io.open(p, encoding="utf-8"))
    fuera = []
    for x in d.get("sin_modulo") or []:
        causa = x.get("causa") or ""
        if x.get("nombre") in VERIFICADOS_CON_CHECK:
            causa = ("existe —`#check` lo acepta— pero el índice no lo "
                     "encuentra")
        fuera.append((x.get("skill"), x.get("marca"), x.get("nombre"), causa))
    return fuera


def tt(s: str) -> str:
    """Un identificador de Mathlib en `\\texttt`, que PUEDA partirse.

    `HomogeneousLocalization.NumDenSameDeg.embedding` son 47 caracteres y
    `\\texttt` no parte por ningun sitio: se salia 33 pt del papel. Los
    nombres de Mathlib parten por los PUNTOS, que es como se leen, asi que
    se le pone ahi un punto de corte opcional.

    Y por los GUIONES, que es como parten las etiquetas del grafo:
    `sheafed-space-complexes` y `conditional-expectation` se salian 13 pt de
    la columna de la tabla de nombres huerfanos.
    """
    return (r"\texttt{%s}" % tex(s)
            .replace(".", r".\allowbreak{}")
            .replace("-", r"-\allowbreak{}"))

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


#: Preambulo de la version imprimible. Compila con pdfLaTeX.
#: No usa tikz ni listings, asi que no le aplican las dos trampas conocidas
#: —babel-espanol volviendo activo el `"`, y listings leyendo bytes—.
PREAMBULO = r"""% Generado por scripts/hoja_de_curacion.py. NO EDITAR A MANO.
\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish,es-nodecimaldot,es-noquoting]{babel}
\usepackage[a4paper,margin=2.1cm]{geometry}
\usepackage{lmodern}
\usepackage{booktabs}
\usepackage{array}
\usepackage{amssymb}
\usepackage{xcolor}
\usepackage{mdframed}
\usepackage{microtype}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}

% LOS IDENTIFICADORES DE MATHLIB TRAEN UNICODE, y pdfLaTeX no lo sabe leer.
% El primer intento murio con «Unicode character U+2080 not set up» por un
% `min_bi` con subindice. Se declara el RANGO, no el caracter que fallo hoy:
% esta hoja se regenera, y manana los modulos pendientes seran otros.
\DeclareUnicodeCharacter{2080}{\ensuremath{_0}}
\DeclareUnicodeCharacter{2081}{\ensuremath{_1}}
\DeclareUnicodeCharacter{2082}{\ensuremath{_2}}
\DeclareUnicodeCharacter{2083}{\ensuremath{_3}}
\DeclareUnicodeCharacter{2084}{\ensuremath{_4}}
\DeclareUnicodeCharacter{2085}{\ensuremath{_5}}
\DeclareUnicodeCharacter{2086}{\ensuremath{_6}}
\DeclareUnicodeCharacter{2087}{\ensuremath{_7}}
\DeclareUnicodeCharacter{2088}{\ensuremath{_8}}
\DeclareUnicodeCharacter{2089}{\ensuremath{_9}}
\DeclareUnicodeCharacter{1D62}{\ensuremath{_i}}
\DeclareUnicodeCharacter{2C7C}{\ensuremath{_j}}
\DeclareUnicodeCharacter{207F}{\ensuremath{^n}}
\DeclareUnicodeCharacter{03B1}{\ensuremath{\alpha}}
\DeclareUnicodeCharacter{03B2}{\ensuremath{\beta}}
\DeclareUnicodeCharacter{03B3}{\ensuremath{\gamma}}
\DeclareUnicodeCharacter{03B4}{\ensuremath{\delta}}
\DeclareUnicodeCharacter{03BC}{\ensuremath{\mu}}
\DeclareUnicodeCharacter{03C3}{\ensuremath{\sigma}}
\DeclareUnicodeCharacter{03C6}{\ensuremath{\varphi}}
\DeclareUnicodeCharacter{2115}{\ensuremath{\mathbb{N}}}
\DeclareUnicodeCharacter{2124}{\ensuremath{\mathbb{Z}}}
\DeclareUnicodeCharacter{211A}{\ensuremath{\mathbb{Q}}}
\DeclareUnicodeCharacter{211D}{\ensuremath{\mathbb{R}}}
\DeclareUnicodeCharacter{2102}{\ensuremath{\mathbb{C}}}
\DeclareUnicodeCharacter{1D55C}{\ensuremath{\Bbbk}}
\DeclareUnicodeCharacter{2192}{\ensuremath{\rightarrow}}
\DeclareUnicodeCharacter{2200}{\ensuremath{\forall}}
\DeclareUnicodeCharacter{2203}{\ensuremath{\exists}}

\definecolor{acento}{RGB}{70,60,140}
\definecolor{suave}{RGB}{120,120,130}
\definecolor{fondo}{RGB}{244,243,248}
\definecolor{aviso}{RGB}{150,90,20}

\newcommand{\Mathlib}{\textsc{Mathlib}}

\titleformat{\section}{\large\bfseries\color{acento}}{}{0pt}{}
\titlespacing{\section}{0pt}{16pt}{6pt}
\titleformat{\subsection}{\normalsize\bfseries}{}{0pt}{}
\titlespacing{\subsection}{0pt}{10pt}{4pt}

\newmdenv[backgroundcolor=fondo,linewidth=0pt,skipabove=8pt,skipbelow=8pt,
          innerleftmargin=10pt,innerrightmargin=10pt,
          innertopmargin=8pt,innerbottommargin=8pt]{marca}
\newmdenv[linecolor=aviso,linewidth=1.2pt,topline=false,bottomline=false,
          rightline=false,skipabove=6pt,skipbelow=6pt,
          innerleftmargin=8pt,innertopmargin=4pt,
          innerbottommargin=4pt]{aviso}

\pagestyle{fancy}\fancyhf{}
\renewcommand{\headrulewidth}{0.3pt}
\fancyhead[L]{\small\color{suave}Metamatemático · curación pendiente}
\fancyhead[R]{\small\color{suave}\thepage}

\begin{document}
\begin{center}
{\LARGE\bfseries\color{acento} Curación pendiente}\par\smallskip
{\color{suave}\small Los 41 módulos que el grafo no cubre, con todo lo
verificable ya resuelto.}\par
{\color{suave}\footnotesize Generado por \texttt{scripts/hoja\_de\_curacion.py}
· se regenera, no se edita a mano}
\end{center}
\vspace{4pt}
"""


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
            if m in DECIDIDOS_SIN_NODO:
                continue          # decidido, no pendiente
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
    if not mods:
        # LA HOJA TIENE QUE SABER DECIR QUE NO QUEDA NADA. Con la lista vacía
        # el texto de arriba seguía citando los 43 originales y luego ponía
        # «0 módulos», que es un documento que se contradice a sí mismo.
        L.append("**No queda nada pendiente.** Los %d módulos que "
                 "`lo_que_falta_emerge` seguía marcando «sin nodo» están "
                 "todos decididos.\n" % len(DECIDIDOS_SIN_NODO))
        L.append("| módulo | decisión |")
        L.append("|---|---|")
        for m in sorted(DECIDIDOS_SIN_NODO):
            L.append("| `%s` | %s |"
                     % (m.replace("Mathlib.", ""), DECIDIDOS_SIN_NODO[m]))
        L.append("")
        L.append("Nueve son marca `T` —ni objetos ni flechas, así que no "
                 "entran— y uno ya está cubierto por un nodo existente. "
                 "Siguen apareciendo como «sin nodo» en la medición, y es "
                 "correcto: no hay nodo. Lo que no son es trabajo.\n")
        L.append("Si mañana la medición destapa módulos nuevos, esta hoja "
                 "vuelve a llenarse sola.\n")
        L.append("---\n")
    else:
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
    L.append("| `F` | un funtor o clase de flechas | **arista** *en este "
             "ambiente* |")
    L.append("| `O` | un objeto individual | vértice degenerado |")
    L.append("| `T` | ni objetos ni flechas | **fuera** |")
    L.append("")
    L.append("`F` **no** dice «esto no puede ser un vértice nunca». Eso es "
             "falso, y está demostrado que lo es en `FlechasComoObjetos.lean`: "
             "las flechas de `C` son exactamente los objetos de `Arrow C`, y "
             "los funtores son los objetos de `C ⥤ D`. Lo que dice es que "
             "**en este grafo** —cuyos objetos son conceptos y cuyas flechas "
             "son dependencias— la etiqueta nombra una flecha.")
    L.append("")
    L.append("`homology` es `F`: aquí no es una colección que se pueda "
             "colimitar, es el funtor *a lo largo del cual* se colimita. "
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

    # ── la otra tarea: nombres que llegan al prompt sin modulo ──────────
    huerfanos = nombres_sin_modulo()
    if huerfanos:
        L.append("---\n")
        L.append("## Lo otro que hay que curar: %d nombres que no llegan a "
                 "módulo\n" % len({h[0] for h in huerfanos}))
        L.append("Esto **no** son módulos que falten en el grafo: son "
                 "etiquetas **ya curadas** cuyo nombre de Mathlib sí se le "
                 "ofrece al modelo y para el que el sistema no tiene con qué "
                 "escribir el `import`. El modelo escribe el identificador y "
                 "Lean contesta `unknown identifier`.\n")
        L.append("Salió al quitar del mapa de módulos un filtro por la marca "
                 "del grafo, que era un error de tipo —la marca dice si algo "
                 "es objeto o flecha, no en qué fichero vive—. Con el filtro "
                 "eran 40; sin él, estos.\n")
        L.append("| etiqueta | marca | nombre que declara | por qué no resuelve |")
        L.append("|---|---|---|---|")
        for sk, mk, nom, causa in huerfanos:
            L.append("| `%s` | `%s` | `%s` | %s |" % (sk, mk, nom, causa))
        L.append("")
        L.append("**La decisión, en cada uno, es una de estas tres:**\n")
        L.append("- [ ] **el nombre está mal** → escribir el que exista "
                 "(`ModuleCat R` no es un identificador: o es `ModuleCat`, "
                 "o es otra cosa)")
        L.append("- [ ] **el nombre está bien y el índice no lo ve** → "
                 "asignarle el módulo a mano (los dos de `MeasureTheory` son "
                 "de estos: `#check` los acepta)")
        L.append("- [ ] **no hay nada que importar** → quitarle el nombre a "
                 "la etiqueta, para que no lo ofrezca (`QuotientGroup` es un "
                 "espacio de nombres, no una declaración: `#check` lo "
                 "rechaza)")
        L.append("")
        L.append("Lo que **no** vale es dejarlo como está: hoy la etiqueta "
                 "gasta una de las plazas del prompt para dar un nombre que "
                 "no se puede importar.\n")

    L.append("---\n")
    L.append("## Antes de dar por buena una tanda\n")
    L.append("```\npython -m scripts.recuperacion_contra_proofnet\n```\n")
    L.append("Precisión y cobertura contra 371 formalizaciones de oro, con su "
             "modelo nulo y sin gastar API.\n")
    L.append("**Baseline hoy: 22,8 % / 18,0 % contra 1,45 % / 3,3 % — "
             "15,7×.** Si la precisión baja, esa tanda no entra.")
    L.append("")
    L.append("Y la regla tiene una letra pequeña que costó descubrir. La primera tanda de 31 nodos **bajaba la precisión a 19,9 %** sin mover la cobertura, y la causa no era ningún veredicto equivocado —los 47 nombres los acepta `#check`— sino que el emparejador tokeniza el **id y el nombre** de cada nodo: `different-ideal` aportaba el token `different`, que sale en media biblioteca, y con eso gastaba una de las dos plazas del prompt. La puerta que lo arregla —*sólo se ocupa plaza con una keyword declarada*— subió la línea base de 21,3 % a 22,8 %. Si una tanda baja la precisión, mira primero si sus nodos entran en plaza por su nombre.")
    L.append("")
    L.append("Ya pasó: ofrecer los sustantivos de los nodos generados bajaba "
             "de 14,0 % a 11,5 %. Añadir vocabulario tiene coste.")
    L.append("")

    io.open(SALIDA, "w", encoding="utf-8").write("\n".join(L))

    # ── la misma hoja en LaTeX, para imprimirla y marcarla a mano ────────
    T = [PREAMBULO]
    # OJO: nada de `%` de Python sobre texto LaTeX. El `\%` de «69 \,\%» se
    # lee como especificador de formato y revienta con un error que no
    # menciona a LaTeX. Se concatena.
    if not mods:
        T.append(r"\section*{No queda nada pendiente}")
        T.append(r"""
Los \textbf{""" + str(len(DECIDIDOS_SIN_NODO)) + r"""} módulos que la medición
sigue marcando «sin nodo» están todos decididos. Nueve son marca \texttt{T}
—ni objetos ni flechas, así que no entran— y uno ya está cubierto por un nodo
que existía. Siguen apareciendo como «sin nodo», y es correcto: no hay nodo.
Lo que no son es trabajo.\par\medskip
""")
        T.append(r"\noindent\small\begin{tabular}"
                 r"{@{}>{\raggedright\arraybackslash}p{0.34\linewidth}"
                 r">{\raggedright\arraybackslash}p{0.62\linewidth}@{}}\toprule")
        T.append(r"módulo & decisión\\\midrule")
        for m in sorted(DECIDIDOS_SIN_NODO):
            T.append(r"%s & %s\\" % (tt(m.replace("Mathlib.", "")),
                                     tex(DECIDIDOS_SIN_NODO[m])))
        T.append(r"\bottomrule\end{tabular}\par\medskip")
        T.append(r"""
Si mañana la medición destapa módulos nuevos, esta hoja vuelve a llenarse
sola.\par\medskip
""")
    else:
        T.append(r"\section*{Qué hay que decidir}")
        T.append(r"""
De 203 enunciados reales de \Mathlib{} tomados al azar, \textbf{62 nombran
algo que la cabecera fija no alcanza}. De esos, en \textbf{43 el grafo no
tiene ningún nodo} que lo cubra —el 69\,\%—. Ningún recorrido recupera lo que
no está: son \textbf{""" + str(len(mods)) + r"""} módulos distintos, y son
curación.
""")
    T.append(r"\begin{marca}")
    T.append(r"\textbf{1 · La marca.} Es lo que sostiene el grafo, y no la "
             r"decide nada automático:\par\smallskip")
    T.append(r"\begin{tabular}{@{}llll@{}}\toprule")
    T.append(r"\texttt{C} & una categoría & $\to$ & \textbf{vértice}\\")
    T.append(r"\texttt{S} & una subcategoría plena & $\to$ & \textbf{vértice}, "
             r"y la inclusión es arista\\")
    T.append(r"\texttt{F} & un funtor o clase de flechas & $\to$ & "
             r"\textbf{arista} \emph{en este ambiente}\\")
    T.append(r"\texttt{O} & un objeto individual & $\to$ & vértice degenerado\\")
    T.append(r"\texttt{T} & ni objetos ni flechas & $\to$ & \textbf{fuera}\\")
    T.append(r"\bottomrule\end{tabular}\par\smallskip")
    # `sloppypar`: `\texttt{FlechasComoObjetos.lean}` es un bloque de 24
    # caracteres que no parte, y el párrafo se salía 16,7 pt.
    T.append(r"\begin{sloppypar}")
    T.append(r"\texttt{F} \textbf{no} dice «esto no puede ser un vértice "
             r"nunca». Eso es falso, y está demostrado que lo es en "
             r"\texttt{FlechasComoObjetos.lean}: las flechas de $C$ son "
             r"exactamente los objetos de la categoría de flechas "
             r"$\mathrm{Arrow}\,C$, y los funtores son los objetos de la "
             r"categoría de funtores $[C,D]$. Lo que dice es que "
             r"\textbf{en este grafo} —cuyos objetos son conceptos y cuyas "
             r"flechas son dependencias— la etiqueta nombra una "
             r"flecha.\end{sloppypar}\smallskip")
    T.append(r"\texttt{homology} es \texttt{F}: aquí no es una colección que "
             r"se pueda colimitar, es el funtor \emph{a lo largo del cual} se "
             r"colimita. \texttt{prime-factorization} es \texttt{T}: es un "
             r"teorema, no un objeto.\par\medskip")
    T.append(r"\textbf{2 · El padre.} De qué concepto es especialización. La "
             r"flecha va del general al específico.\par\medskip")
    T.append(r"\textbf{3 · Cuáles nombres se quedan.} Que exista no lo hace "
             r"correcto: \texttt{Nat.Prime} es la noción de primo, "
             r"\texttt{Nat.minFac} no lo es.")
    T.append(r"\end{marca}")
    T.append(r"""
\noindent Lo que \textbf{no} hay que decidir, porque ya está verificado: si el
nombre existe, en qué módulo vive, cuál es el canónico —las citas— y el DAG de
\texttt{import}s. Los identificadores de abajo están \textbf{leídos de su
declaración}, no deducidos de la ruta: de 447 deducidos así, 95 no existían.
\par\medskip
""")
    T.append(r"\begin{center}\small\begin{tabular}{@{}lr@{\quad}lr@{\quad}lr@{}}"
             r"\toprule")
    orden = sorted(grupos, key=lambda r: (-len(grupos[r]), r))
    filas = [(orden[i:i + 3]) for i in range(0, len(orden), 3)]
    for f in filas:
        T.append(" & ".join("%s & %d" % (tex(r), len(grupos[r])) for r in f)
                 + r"\\")
    T.append(r"\bottomrule\end{tabular}\end{center}")

    for rama in orden:
        area = RAMA_A_AREA.get(rama, "")
        T.append(r"\section{%s\hfill{\normalsize\normalfont %s}}"
                 % (tex(rama), (r"área \texttt{%s}" % tex(area)) if area
                    else r"\textbf{sin área en el grafo}"))
        if not area:
            T.append(r"\begin{aviso}\Mathlib{} no organiza esta rama como un "
                     r"área del grafo. Puede que estos conceptos sean "
                     r"\texttt{T} y no toquen.\end{aviso}")
        elif por_area.get(area):
            # `\texttt` con guiones no parte, y una lista larga se salia del
            # papel —48 pt en el peor caso—. `sloppypar` estira los espacios
            # en vez de desbordar, que en una hoja para imprimir es la
            # diferencia entre usable e inservible.
            T.append(r"\begin{sloppypar}\noindent\small\textit{Padres "
                     r"candidatos ya en el grafo:} %s\end{sloppypar}"
                     % ", ".join(r"\texttt{%s}" % tex(x)
                                 for x in sorted(por_area[area])[:10]))
        for m in sorted(grupos[rama]):
            ss = por.get(m, [])[:args.k]
            T.append(r"\subsection*{\texttt{%s}}"
                     % tex(m.replace("Mathlib.", "")))
            if not ss:
                T.append(r"\noindent\small Sin sustantivos propios: sólo "
                         r"aporta teoremas. El grafo aporta \emph{sustantivos} "
                         r"—de sus 176 identificadores ninguno es un teorema—, "
                         r"así que probablemente no le toca.\par\medskip")
                continue
            # La columna del identificador va con ancho fijo y alineada a la
            # izquierda: asi el corte por puntos que pone `tt` tiene donde
            # caer. Con `l` a secas, un nombre de 47 caracteres se salia.
            T.append(r"\noindent\begin{minipage}{0.56\linewidth}\small"
                     r"\begin{tabular}"
                     r"{@{}>{\raggedright\arraybackslash}p{0.58\linewidth}"
                     r"ll@{}}\toprule")
            T.append(r"identificador & tipo & citas\\\midrule")
            for s in ss:
                T.append(r"%s & %s & %d\\" % (
                    tt(s["nombre"]), tex(s.get("tipo") or ""),
                    int(s.get("citas") or 0)))
            T.append(r"\bottomrule\end{tabular}\end{minipage}\hfill"
                     r"\begin{minipage}{0.40\linewidth}\small"
                     r"$\square$~marca \texttt{C S F O T}\par\smallskip"
                     r"$\square$~padre: \dotfill\par\smallskip"
                     r"$\square$~se quedan: \dotfill\par\end{minipage}"
                     r"\par\medskip")

    # ── la otra tarea, en LaTeX ─────────────────────────────────────────
    if huerfanos:
        T.append(r"\section*{Lo otro que hay que curar: " +
                 str(len({h[0] for h in huerfanos})) +
                 r" nombres que no llegan a módulo}")
        T.append(r"""
Esto \textbf{no} son módulos que falten en el grafo: son etiquetas
\textbf{ya curadas} cuyo nombre de \Mathlib{} sí se le ofrece al modelo y para
el que el sistema no tiene con qué escribir el \texttt{import}. El modelo
escribe el identificador y Lean contesta \texttt{unknown identifier}.\par\medskip
Salió al quitar del mapa de módulos un filtro por la marca del grafo, que era
un error de tipo —la marca dice si algo es objeto o flecha, no en qué fichero
vive—. Con el filtro eran 40; sin él, estos.\par\medskip
""")
        T.append(r"\noindent\small\begin{tabular}"
                 r"{@{}>{\raggedright\arraybackslash}p{0.20\linewidth}c"
                 r">{\raggedright\arraybackslash}p{0.28\linewidth}"
                 r">{\raggedright\arraybackslash}p{0.34\linewidth}@{}}"
                 r"\toprule")
        T.append(r"etiqueta & marca & nombre que declara & por qué no "
                 r"resuelve\\\midrule")
        for sk, mk, nom, causa in huerfanos:
            T.append(r"%s & \texttt{%s} & %s & %s\\"
                     % (tt(sk), tex(mk or ""), tt(nom),
                        tex(causa).replace("`", "")))
        T.append(r"\bottomrule\end{tabular}\par\medskip")
        T.append(r"""
\begin{marca}
\textbf{La decisión, en cada uno, es una de estas tres:}\par\smallskip
$\square$~\textbf{el nombre está mal} $\to$ escribir el que exista.
\texttt{ModuleCat R} no es un identificador: o es \texttt{ModuleCat}, o es otra
cosa.\par\smallskip
$\square$~\textbf{el nombre está bien y el índice no lo ve} $\to$ asignarle el
módulo a mano. Los dos de \texttt{MeasureTheory} son de estos: \texttt{\#check}
los acepta con \Mathlib{} entero importado.\par\smallskip
$\square$~\textbf{no hay nada que importar} $\to$ quitarle el nombre a la
etiqueta, para que no lo ofrezca. \texttt{QuotientGroup} es un espacio de
nombres, no una declaración, y \texttt{\#check} lo rechaza.\par\medskip
Lo que \textbf{no} vale es dejarlo como está: hoy la etiqueta gasta una de las
plazas del prompt para dar un nombre que no se puede importar.
\end{marca}
""")

    T.append(r"\section*{Antes de dar por buena una tanda}")
    T.append(r"""
\begin{marca}
\noindent\texttt{python -m scripts.recuperacion\_contra\_proofnet}\par\smallskip
Precisión y cobertura contra 371 formalizaciones de oro, con su modelo nulo y
sin gastar API.\par\medskip
\textbf{Baseline hoy: 22,8\,\% / 18,0\,\% contra 1,45\,\% / 3,3\,\% —
15,7$\times$.} Si la precisión baja, esa tanda \textbf{no entra}.\par\medskip
Ya pasó: ofrecer los sustantivos de los nodos generados bajaba de 14,0\,\% a
11,5\,\%. Añadir vocabulario tiene coste.\par\medskip
\textbf{Y la regla tiene letra pequeña.} La primera tanda de 31 nodos bajaba
la precisión a 19,9\,\% sin mover la cobertura, y la causa no era ningún
veredicto equivocado —los 47 nombres los acepta \texttt{\#check}— sino que el
emparejador tokeniza el \textbf{id y el nombre} de cada nodo:
\texttt{different-\allowbreak{}ideal} aportaba el token \texttt{different},
que sale en media biblioteca, y con eso gastaba una de las dos plazas del
prompt. La puerta que lo arregla —\emph{sólo se ocupa plaza con una keyword
declarada}— subió la línea base de 21,3\,\% a 22,8\,\%. Si una tanda baja la
precisión, mira primero si sus nodos entran en plaza por su nombre.
\end{marca}
""")
    T.append(r"\end{document}")
    io.open(SALIDA_TEX, "w", encoding="utf-8").write("\n".join(T))

    print("modulos pendientes: %d, en %d ramas" % (len(mods), len(grupos)))
    print("-> %s" % SALIDA)
    print("-> %s" % SALIDA_TEX)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
