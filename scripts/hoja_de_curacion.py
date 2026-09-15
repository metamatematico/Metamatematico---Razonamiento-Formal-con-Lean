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
import re
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


#: POR QUE EL MOTIVO VA SEPARADO DE LA MARCA, y no es cosmetica.
#:
#: Esta tabla tenia un solo campo y los diez modulos decididos estaban
#: archivados bajo `T`. La decision —los diez fuera— era correcta; NUEVE DE
#: LAS DIEZ RAZONES NO. La marca `T` significa «ni objetos ni flechas», y
#: nueve de estos diez declaran objetos. `Data.TypeVec` es el caso que lo
#: refuta de frente: define objetos (`TypeVec`, linea 41), flechas con
#: notacion propia (`Arrow`, 52, con `⟹`), identidad (`id`, 71) y
#: composicion. Sea cual sea el motivo para dejarlo fuera, «ni objetos ni
#: flechas» no puede serlo.
#:
#: Y en una hoja que se regenera sola, LA RAZON ES LO UNICO QUE VIAJA AL
#: FUTURO: la decision ya la tomo la medicion, pero la razon es la que va a
#: decidir el proximo modulo parecido. Cada motivo tiene un DISPARADOR DE
#: REVISION distinto, y esa es toda la diferencia — `T` es la marca que no se
#: revisa nunca, asi que archivar bajo `T` algo que si hay que revisar
#: equivale a perderlo.
#:
#: Verificado contra Mathlib4 (este arbol: 401ee04, 7 mar 2026); el veredicto
#: del autor cita 17019dc, 14 sep 2026, de ahi que alguna linea baile una.
MOTIVOS_DE_EXCLUSION = {
    "alias": ("una presentacion del objeto de un nodo que YA existe; su "
              "nombre va en el campo `lean` de ese nodo, no en uno nuevo",
              "si cambia el nodo padre"),
    "huerfano": ("objeto legitimo cuya AREA no esta en el grafo: sin padre "
                 "la arista no existiria y el nombre quedaria suelto",
                 "si entra el area"),
    "politica": ("TIENE objetos, pero es metalenguaje y su vocabulario es "
                 "caro: sus tokens salen en media biblioteca",
                 "nunca, salvo decision explicita"),
    "cubierto": ("el nombre ya esta en el campo `lean` de un nodo: el alias "
                 "ya aplicado", "si cambia ese nodo"),
    "T": ("ni objetos ni flechas", "nunca"),
}

#: MODULOS QUE YA SE DECIDIERON Y NO PRODUCEN NODO. Siguen saliendo como
#: «sin nodo» en `lo_que_falta_emerge` —y es correcto: no hay nodo— pero no son
#: trabajo pendiente, son una decision tomada. Sin esta tabla la hoja los
#: volveria a pedir en cada tanda.
#:
#: Cada entrada es (motivo, razon). Tras el veredicto del autor no queda
#: NINGUNO en `T`.
DECIDIDOS_SIN_NODO = {
    # ── ALIAS: otra presentacion de algo que ya tiene nodo ───────────────
    "Mathlib.AlgebraicTopology.SimplexCategory.GeneratorsRelations.Basic": (
        "alias",
        "`SimplexCategoryGenRel` (linea 75) es SimplexCategory presentada por "
        "generadores y relaciones. AVISO: la equivalencia "
        "`SimplexCategoryGenRel ≌ SimplexCategory` NO esta probada en Mathlib "
        "—solo el funtor `toSimplexCategory` (251) y las piezas de EpiMono y "
        "NormalForms—, asi que «la misma categoria con otro nombre» es una "
        "conjetura, no un hecho verificado, y el alias apuntaria a traves de "
        "un funtor del que aun no se sabe que sea equivalencia"),
    "Mathlib.SetTheory.Ordinal.Notation": (
        "alias",
        "`ONote` (40) y `NONote` (1129) son la forma normal de Cantor como "
        "dato computable, y `repr` (69) es la flecha canonica de evaluacion "
        "hacia `Ordinal`. NO es la identidad: es una presentacion del objeto "
        "del nodo `ordinals`, que ya existe"),

    # ── HUERFANO: objeto legitimo, area ausente ─────────────────────────
    "Mathlib.Order.PFilter": (
        "huerfano",
        "`PFilter` (45) es una estructura con `instance : PartialOrder` (77): "
        "objeto de pleno derecho. Lo que falta es el PADRE — no hay ni un "
        "concepto curado de teoria de ordenes, solo nodos generados y el "
        "area. Y el area ya esta medio dentro sin nombre: `divisibility-gcd`, "
        "`subgroups-cosets` e `ideals-quotient-rings` son reticulos y "
        "preordenes colgando de otro sitio. AVISO PARA CUANDO ENTRE: su token "
        "es `filter`, de los mas frecuentes de Mathlib; sin keyword declarada "
        "bajaria la precision como hizo `different`"),
    "Mathlib.Computability.AkraBazzi.SumTransform": (
        "huerfano",
        "`structure AkraBazziRecurrence` (60) empaqueta la recurrencia con "
        "sus hipotesis: hay objeto. La analogia con `prime-factorization` NO "
        "se sostiene —aquel es un teorema sin estructura empaquetada—. Lo que "
        "falta es el padre: `algorithm-analysis` esta marcado T y sin nombre"),

    # ── POLITICA: hay objetos, pero el vocabulario es caro ───────────────
    "Mathlib.Control.Bitraversable.Basic": (
        "politica",
        "`class Bitraversable` (48) es un objeto. Fuera por metalenguaje: es "
        "la interfaz de efectos de Lean"),
    "Mathlib.Control.Fix": (
        "politica",
        "`class Fix` (35) es un objeto. Fuera porque su token seria `fix`, "
        "que sale en media biblioteca"),
    "Mathlib.Control.Functor.Multivariate": (
        "politica",
        "`class MvFunctor` (32) es un objeto. Su token seria `functor`"),
    "Mathlib.Control.Monad.Cont": (
        "politica",
        "`class MonadCont` (33) y `def ContT` (48) son objetos. Su token "
        "seria `cont`"),
    "Mathlib.Data.TypeVec": (
        "politica",
        "EL CASO QUE REFUTA LA MARCA DE FRENTE: define objetos (`TypeVec`, "
        "41), flechas con notacion propia (`Arrow`, 52, con `⟹`), identidad "
        "(`id`, 71) y composicion. Fuera por metalenguaje y porque su token "
        "seria `type`. La puerta de las plazas ya lo para sin prohibirlo: no "
        "se le declara ninguna keyword, y esa es la razon"),

    # ── CUBIERTO: el alias, ya aplicado ─────────────────────────────────
    "Mathlib.Topology.Category.TopCat.Basic": (
        "cubierto",
        "`structure TopCat` (32) ya es la identidad de `point-set-topology`. "
        "La convencion del proyecto pone el envoltorio categorico en el campo "
        "`lean` del concepto (group-theory lleva GrpCat), no en un nodo "
        "aparte"),
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

    Y en los tramos LARGOS SIN PUNTO, antes de cada mayuscula:
    `qExpansionFormalMultilinearSeries` son 33 caracteres de una pieza y no
    hay donde cortar. Solo en tramos de mas de 16, para no descuadrar los
    nombres normales.
    """
    def _camel(tramo: str) -> str:
        if len(tramo) <= 16:
            return tramo
        return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", r"\\allowbreak{}", tramo)

    partido = ".".join(_camel(t) for t in tex(s).split("."))
    return (r"\texttt{%s}" % partido
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
#:
#: Y hay una TERCERA, encontrada al generar `CURACION_INTERNA`: babel-espanol
#: deja activo tambien el `~`. Un `$\square$~{\small ...}` revienta con
#: `Missing \endcsname inserted` y un `\language@active@arg~` en el log, que
#: no menciona ni a babel ni al `~`. Estas dos hojas se salvan por no usarlo;
#: quien lo escriba, que ponga `\,`.
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
% Los simbolos de CATEGORIAS, que salen en cuanto la hoja habla de alias:
% `SimplexCategoryGenRel ≌ SimplexCategory` tumbo la compilacion. Se declara
% la familia entera y no el que fallo hoy, que es la leccion de U+2080.
\DeclareUnicodeCharacter{224C}{\ensuremath{\backsimeq}}
\DeclareUnicodeCharacter{2243}{\ensuremath{\simeq}}
\DeclareUnicodeCharacter{2245}{\ensuremath{\cong}}
\DeclareUnicodeCharacter{27F9}{\ensuremath{\Longrightarrow}}
\DeclareUnicodeCharacter{27F6}{\ensuremath{\longrightarrow}}
\DeclareUnicodeCharacter{2964}{\ensuremath{\rightarrowtail}}
\DeclareUnicodeCharacter{2045}{\ensuremath{[\![}}
\DeclareUnicodeCharacter{2046}{\ensuremath{]\!]}}
\DeclareUnicodeCharacter{1D7ED}{\ensuremath{\mathbf{1}}}

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


#: Cuantos teoremas debe tener un modulo para merecer una decision. Por
#: debajo de esto, curarlo cuesta mas de lo que puede aportar.
MINIMO_TEOREMAS = 30

_TEOREMA = re.compile(
    r"^\s*(?:@\[[^\]]*\]\s*)?(?:private |protected |noncomputable )*"
    r"(?:theorem|lemma)\s", re.M)


#: LAS RAMAS QUE ABRIO LA TANDA DE CURACION. Son el primer grupo de la hoja:
#: seguir lo empezado. Cada una tiene ya un nodo y el resto sin tocar.
RAMAS_DE_LA_TANDA = (
    "Mathlib.Algebra.Lie", "Mathlib.NumberTheory.ModularForms",
    "Mathlib.Dynamics", "Mathlib.Computability", "Mathlib.SetTheory.ZFC",
    "Mathlib.RingTheory.GradedAlgebra", "Mathlib.RingTheory.Derivation",
    "Mathlib.AlgebraicTopology.SimplexCategory",
)

#: Cuantos modulos entran por cada grupo. La primera tanda fueron 41 y costo
#: una sesion entera; doce por grupo es lo que cabe en una sentada.
TOPE_POR_GRUPO = 12


def _rama_de(mod: str) -> str:
    p = mod.split(".")
    return ".".join(p[:3]) if len(p) > 2 else ".".join(p[:2])


def ramas_abiertas_y_finas():
    """Dos grupos de modulos por curar, con criterios distintos a proposito.

    OTRO CRITERIO, Y POR ESO OTRA HOJA. El selector de siempre parte de
    `lo_que_falta_emerge`: enunciados reales que nombran algo que el grafo no
    alcanza. Ese banco esta AGOTADO — los 41 se curaron y los 10 que quedan
    estan decididos en DECIDIDOS_SIN_NODO.

    Este mira la cobertura de Mathlib directamente, y devuelve DOS grupos
    porque son dos apuestas distintas y conviene no mezclarlas:

    GRUPO 1 · SEGUIR LA TANDA.  La curacion anterior metio el primer nodo de
    varias ramas y se paro ahi. `Algebra.Lie` tiene 1 228 teoremas en 50
    ficheros y el grafo toca UNO: un algebra de Lie sin subalgebras, sin
    ideales y sin pesos. Son rincones —volumen pequeno— pero el barrio se
    mide limpio y son los conceptos que busca quien investiga.

    GRUPO 2 · EL NUCLEO.  Aplicando el mismo criterio a Mathlib entero salen
    161 ramas abiertas y finas, y las mayores NO son las de la tanda:

        Algebra.Order              5 140 teoremas ·   1 de 208 modulos
        Algebra.Group              4 102          ·   4 de 148
        Analysis.SpecialFunctions  3 906          ·   1 de  98
        Analysis.Calculus          3 607          ·   2 de 122

    Ahi es donde caen las consultas de un alumno, y explica el 5,0 % de
    precision sobre Mathlib entero: el grafo es fino en casi todas partes, no
    solo en los rincones.

    UNA CAUTELA QUE VA EN LA HOJA, no en un comentario: en el grupo 2 el grafo
    YA TIENE nodo de cabecera —`group-theory`, `ring-theory`,
    `real-analysis`— y lo que falta son los modulos finos de debajo. Puede que
    la respuesta correcta no sea un nodo nuevo sino MAS NOMBRES en el que ya
    hay, que es una decision distinta y mas barata. La hoja lo pregunta.

    Y AHORA SE PUEDE MEDIR EL RESULTADO, que es lo que faltaba la vez
    anterior: `banco_docstrings.py` y `banco_herald.py` ven estos temas. Sobre
    la primera tanda, sus modulos pasaron de 3,9 % a 16,9 % y de 4,0 % a
    20,6 % de precision sin mover el global. Una tanda entra si sube su barrio
    Y no baja el global.
    """
    mathlib = os.path.join(RAIZ, ".lake", "packages", "mathlib", "Mathlib")
    if not os.path.isdir(mathlib):
        return [], {}
    cubiertos = set()
    mapa = os.path.join(RAIZ, "data", "mathlib_modulos.json")
    if os.path.exists(mapa):
        d = json.load(io.open(mapa, encoding="utf-8"))
        for ms in (d.get("por_skill") or {}).values():
            cubiertos.update(ms)

    teoremas, ramas = {}, {}
    for raiz, _s, fs in os.walk(mathlib):
        for f in fs:
            if not f.endswith(".lean"):
                continue
            ruta = os.path.join(raiz, f)
            rel = os.path.relpath(ruta, os.path.dirname(mathlib))
            mod = rel[:-5].replace(os.sep, ".").replace("/", ".")
            try:
                src = io.open(ruta, encoding="utf-8", errors="replace").read()
            except Exception:                                # noqa: BLE001
                continue
            teoremas[mod] = len(_TEOREMA.findall(src))
            r = ramas.setdefault(_rama_de(mod), {"teo": 0, "mod": 0, "cub": 0})
            r["teo"] += teoremas[mod]
            r["mod"] += 1
            if mod in cubiertos:
                r["cub"] += 1

    def candidatos(filtro, por_rama=None):
        """Los mas grandes que cumplen `filtro`, sin los ya decididos.

        Con `por_rama` se limita cuantos entran de cada rama. Sin ese tope,
        las dos ramas mas grandes se comen la tanda entera: `Algebra.Lie` y
        `Computability` dejaban fuera a las formas modulares, que es una de
        las tres ramas que esta hoja existe para continuar.
        """
        c = [(n, m) for m, n in teoremas.items()
             if m not in cubiertos
             and m not in DECIDIDOS_SIN_NODO      # ya se decidio que no entra
             and n >= MINIMO_TEOREMAS and filtro(m)]
        c.sort(reverse=True)
        fuera, cuenta = [], {}
        if por_rama:
            for n, m in c:
                r = _rama_de(m)
                if cuenta.get(r, 0) >= por_rama:
                    continue
                cuenta[r] = cuenta.get(r, 0) + 1
                fuera.append(m)
                if len(fuera) >= TOPE_POR_GRUPO:
                    break
            # si el tope por rama deja hueco, se rellena con los siguientes
            for n, m in c:
                if len(fuera) >= TOPE_POR_GRUPO:
                    break
                if m not in fuera:
                    fuera.append(m)
            return fuera
        return [m for _n, m in c[:TOPE_POR_GRUPO]]

    # GRUPO 1 · las ramas que la tanda abrio
    de_la_tanda = candidatos(
        lambda m: any(m.startswith(r + ".") or m == r
                      for r in RAMAS_DE_LA_TANDA), por_rama=3)

    # GRUPO 2 · el nucleo: abiertas, finas (<=25 % cubierto) y grandes
    nucleo_ramas = {r for r, v in ramas.items()
                    if v["cub"] >= 1 and v["cub"] / v["mod"] <= 0.25
                    and v["teo"] >= 2000
                    and not any(r.startswith(t) for t in RAMAS_DE_LA_TANDA)}
    del_nucleo = candidatos(lambda m: _rama_de(m) in nucleo_ramas,
                            por_rama=3)

    meta = {"teoremas": teoremas, "ramas": ramas,
            "grupo": {}, "nucleo_ramas": sorted(nucleo_ramas)}
    for m in de_la_tanda:
        meta["grupo"][m] = "tanda"
    for m in del_nucleo:
        meta["grupo"][m] = "nucleo"
    # el grupo 1 primero: es el que continua algo ya decidido
    return de_la_tanda + [m for m in del_nucleo if m not in de_la_tanda], meta


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--ramas", action="store_true",
                    help="otro criterio: ramas que el grafo abrio y dejo finas")
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
    meta = {}
    if args.ramas:
        mods, meta = ramas_abiertas_y_finas()
        if not mods:
            print("sin candidatos — ¿esta Mathlib en .lake/packages?")
            return 1
    else:
        d = json.load(io.open(emer, encoding="utf-8"))
        mods = []
        for x in d.get("detalle", []):
            if x.get("veredicto") != "sin_nodo":
                continue
            for m in x.get("faltan", []):
                if m in DECIDIDOS_SIN_NODO:
                    continue      # decidido, no pendiente
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
    L.append("# %s\n" % ("Curación por cobertura" if args.ramas
                         else "Curación pendiente"))
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
        L.append("**Fuera no es lo mismo que `T`.** La decisión —los diez "
                 "fuera— la tomó la medición; el **motivo** es lo único que "
                 "viaja al futuro, porque es lo que va a decidir el próximo "
                 "módulo parecido. Cada uno tiene un **disparador de revisión "
                 "distinto**, y `T` es la marca que no se revisa nunca: "
                 "archivar bajo `T` algo que sí hay que revisar equivale a "
                 "perderlo.\n")
        L.append("| motivo | qué es | cuándo se revisa |")
        L.append("|---|---|---|")
        for mot in ("alias", "huerfano", "politica", "cubierto", "T"):
            que, cuando = MOTIVOS_DE_EXCLUSION[mot]
            L.append("| **%s** | %s | %s |" % (mot, que, cuando))
        L.append("")
        L.append("| módulo | motivo | por qué |")
        L.append("|---|---|---|")
        for m in sorted(DECIDIDOS_SIN_NODO,
                        key=lambda x: (DECIDIDOS_SIN_NODO[x][0], x)):
            mot, razon = DECIDIDOS_SIN_NODO[m]
            L.append("| `%s` | **%s** | %s |"
                     % (m.replace("Mathlib.", ""), mot, razon))
        L.append("")
        _por_mot = {}
        for mot, _r in DECIDIDOS_SIN_NODO.values():
            _por_mot[mot] = _por_mot.get(mot, 0) + 1
        L.append("Reparto: %s. **Ninguno queda en `T`** — nueve de los diez "
                 "declaran objetos, y `Data.TypeVec` declara además flechas, "
                 "identidad y composición en el propio fichero. Siguen "
                 "apareciendo como «sin nodo» en la medición, y es correcto: "
                 "no hay nodo. Lo que no son es trabajo.\n"
                 % ", ".join("%d %s" % (n, k)
                             for k, n in sorted(_por_mot.items())))
        L.append("Si mañana la medición destapa módulos nuevos, esta hoja "
                 "vuelve a llenarse sola.\n")
        L.append("---\n")
    elif args.ramas:
        # LA PROSA TIENE QUE DECIR EL CRITERIO QUE SE USO, no otro. Esta hoja
        # no sale de enunciados que fallan —ese banco esta agotado— sino de
        # mirar la cobertura de Mathlib.
        n_tanda = sum(1 for m in mods if meta["grupo"].get(m) == "tanda")
        L.append("El banco de enunciados que fallan **está agotado**: los 41 "
                 "módulos que destapó se curaron y los 10 que quedaban están "
                 "decididos. Esta hoja sale de otro sitio — de mirar "
                 "directamente qué partes de Mathlib no cubre el grafo.\n")
        L.append("Son **%d módulos en dos grupos**, y son dos apuestas "
                 "distintas que conviene no mezclar.\n" % len(mods))
        L.append("**Grupo 1 · seguir la tanda** — %d módulos. La curación "
                 "anterior metió el primer nodo de varias ramas y se paró "
                 "ahí. `Algebra.Lie` tiene **1 228 teoremas en 50 ficheros y "
                 "el grafo toca uno**: un álgebra de Lie sin subálgebras, sin "
                 "ideales y sin pesos. Son rincones —poco volumen— pero el "
                 "barrio se mide limpio y son los conceptos que busca quien "
                 "investiga.\n" % n_tanda)
        L.append("**Grupo 2 · el núcleo** — %d módulos. El mismo criterio "
                 "sobre Mathlib entero da **161 ramas abiertas y finas**, y "
                 "las mayores no son las de la tanda:\n" % (len(mods) - n_tanda))
        L.append("| rama | teoremas | módulos | cubiertos |")
        L.append("|---|---:|---:|---:|")
        for r in sorted(meta.get("nucleo_ramas") or [],
                        key=lambda x: -meta["ramas"][x]["teo"])[:5]:
            v = meta["ramas"][r]
            L.append("| `%s` | %d | %d | %d |"
                     % (r.replace("Mathlib.", ""), v["teo"], v["mod"], v["cub"]))
        L.append("")
        L.append("Ahí es donde caen las consultas de un alumno, y explica el "
                 "**5,0 % de precisión sobre Mathlib entero**: el grafo es "
                 "fino en casi todas partes, no sólo en los rincones.\n")
        L.append("> **Una pregunta extra para el grupo 2.** Ahí el grafo ya "
                 "tiene nodo de cabecera —`group-theory`, `ring-theory`, "
                 "`real-analysis`— y lo que falta son los módulos finos de "
                 "debajo. Puede que la respuesta correcta **no sea un nodo "
                 "nuevo sino más nombres en el que ya hay**, que es una "
                 "decisión distinta y más barata. Si es el caso, escríbelo en "
                 "vez de la marca.\n")
        L.append("Y ahora hay con qué decidir, que es lo que faltó la vez "
                 "anterior: `banco_docstrings.py` y `banco_herald.py` **sí "
                 "ven** estos temas. Sobre la primera tanda, sus módulos "
                 "pasaron de 3,9 % a 16,9 % y de 4,0 % a 20,6 % de precisión "
                 "sin mover el global. **Una tanda entra si sube su barrio y "
                 "no baja el global.**\n")
        L.append("Repartidos por rama:")
        L.append("")
        L.append("| rama | módulos |")
        L.append("|---|---|")
        for r, ms in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
            L.append("| %s | %d |" % (r, len(ms)))
        L.append("")
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
            # CADA MODULO DICE DE QUE GRUPO ES, porque la decision no es la
            # misma: en el grupo 2 la respuesta puede ser «mas nombres en el
            # nodo que ya hay» en vez de un nodo nuevo.
            _g = (meta.get("grupo") or {}).get(m)
            _etq = {"tanda": "  ·  *grupo 1 · seguir la tanda*",
                    "nucleo": "  ·  *grupo 2 · el núcleo*"}.get(_g, "")
            L.append("### `%s`%s\n" % (m.replace("Mathlib.", ""), _etq))
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

    # EN MODO --ramas VA A OTRO FICHERO. Son dos hojas con criterios
    # distintos; pisarse una a otra perderia el trabajo de la anterior.
    salida = SALIDA.replace("PENDIENTE", "RAMAS") if args.ramas else SALIDA
    io.open(salida, "w", encoding="utf-8").write("\n".join(L))

    # ── la misma hoja en LaTeX, para imprimirla y marcarla a mano ────────
    T = [PREAMBULO]
    # OJO: nada de `%` de Python sobre texto LaTeX. El `\%` de «69 \,\%» se
    # lee como especificador de formato y revienta con un error que no
    # menciona a LaTeX. Se concatena.
    if not mods:
        T.append(r"\section*{No queda nada pendiente}")
        T.append(r"""
Los \textbf{""" + str(len(DECIDIDOS_SIN_NODO)) + r"""} módulos que la medición
sigue marcando «sin nodo» están todos decididos, y \textbf{ninguno queda en
\texttt{T}}. La decisión la tomó la medición; el \emph{motivo} es lo único que
viaja al futuro, porque es lo que va a decidir el próximo módulo parecido.
Cada motivo tiene un disparador de revisión distinto, y \texttt{T} es la marca
que no se revisa nunca: archivar bajo \texttt{T} algo que sí hay que revisar
equivale a perderlo.\par\medskip
""")
        T.append(r"\noindent\small\begin{tabular}"
                 r"{@{}l>{\raggedright\arraybackslash}p{0.52\linewidth}"
                 r">{\raggedright\arraybackslash}p{0.27\linewidth}@{}}\toprule")
        T.append(r"motivo & qué es & cuándo se revisa\\\midrule")
        for _mot in ("alias", "huerfano", "politica", "cubierto", "T"):
            _que, _cuando = MOTIVOS_DE_EXCLUSION[_mot]
            T.append(r"\texttt{%s} & %s & %s\\"
                     % (tex(_mot), tex(_que), tex(_cuando)))
        T.append(r"\bottomrule\end{tabular}\par\medskip")
        T.append(r"\noindent\small\begin{tabular}"
                 r"{@{}>{\raggedright\arraybackslash}p{0.28\linewidth}l"
                 r">{\raggedright\arraybackslash}p{0.50\linewidth}@{}}\toprule")
        T.append(r"módulo & motivo & por qué\\\midrule")
        for m in sorted(DECIDIDOS_SIN_NODO,
                        key=lambda x: (DECIDIDOS_SIN_NODO[x][0], x)):
            _mot, _razon = DECIDIDOS_SIN_NODO[m]
            T.append(r"%s & \texttt{%s} & %s\\"
                     % (tt(m.replace("Mathlib.", "")), tex(_mot), tex(_razon)))
        T.append(r"\bottomrule\end{tabular}\par\medskip")
        T.append(r"""
Si mañana la medición destapa módulos nuevos, esta hoja vuelve a llenarse
sola.\par\medskip
""")
    elif args.ramas:
        n_tanda = sum(1 for m in mods
                      if (meta.get("grupo") or {}).get(m) == "tanda")
        T.append(r"\section*{Dos grupos, dos apuestas}")
        T.append(r"""
El banco de enunciados que fallan está \textbf{agotado}: los 41 módulos que
destapó se curaron y los 10 que quedaban están decididos. Esta hoja sale de
mirar directamente qué partes de \Mathlib{} no cubre el grafo, y trae
\textbf{""" + str(len(mods)) + r"""} módulos en dos grupos que conviene no
mezclar.\par\medskip
\textbf{Grupo 1 · seguir la tanda} —""" + str(n_tanda) + r""" módulos. La
curación anterior metió el primer nodo de varias ramas y se paró ahí.
\texttt{Algebra.Lie} tiene \textbf{1\,228 teoremas en 50 ficheros y el grafo
toca uno}: un álgebra de Lie sin subálgebras, sin ideales y sin pesos. Son
rincones —poco volumen— pero el barrio se mide limpio.\par\medskip
\textbf{Grupo 2 · el núcleo} —""" + str(len(mods) - n_tanda) + r""" módulos.
El mismo criterio sobre \Mathlib{} entero da \textbf{161 ramas abiertas y
finas}, y las mayores no son las de la tanda: \texttt{Algebra.Order} con
5\,140 teoremas y \textbf{1 módulo cubierto de 208}, \texttt{Algebra.Group}
con 4\,102 y 4 de 148, \texttt{Analysis.SpecialFunctions} con 3\,906 y 1 de
98. Ahí caen las consultas de un alumno, y explica el \textbf{5,0\,\%} de
precisión sobre \Mathlib{} entero.\par\medskip
\textbf{Una pregunta extra para el grupo 2.} Ahí el grafo YA tiene nodo de
cabecera —\texttt{group-theory}, \texttt{real-analysis}— y lo que falta son
los módulos finos de debajo. Puede que la respuesta correcta no sea un nodo
nuevo sino \emph{más nombres en el que ya hay}, que es más barato. Si es el
caso, escríbelo en vez de la marca.
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
    salida_tex = (SALIDA_TEX.replace("PENDIENTE", "RAMAS") if args.ramas
                  else SALIDA_TEX)
    io.open(salida_tex, "w", encoding="utf-8").write("\n".join(T))

    print("modulos pendientes: %d, en %d ramas" % (len(mods), len(grupos)))
    print("-> %s" % salida)
    print("-> %s" % salida_tex)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
