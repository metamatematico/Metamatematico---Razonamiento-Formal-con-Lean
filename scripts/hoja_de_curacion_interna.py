# -*- coding: utf-8 -*-
"""La curacion que nadie pidio: lo que le falta al grafo POR DENTRO.

DE DONDE SALE ESTA HOJA
-----------------------
Las otras dos miran hacia AFUERA — que trozo de Mathlib no cubre el grafo:

    hoja_de_curacion.py            enunciados que fallan   -> AGOTADA (0)
    hoja_de_curacion.py --ramas    cobertura de Mathlib    -> 24 modulos

Esta mira hacia ADENTRO, y pregunta otra cosa: de los nodos QUE YA ESTAN,
cuales no cumplen lo que su propia marca promete. Salio de una pregunta
lateral —«¿por que el explorador no ensena la marca?»— y destapo 48
decisiones que ninguna medicion habia pedido nunca, porque ninguna medicion
mira ahi: los bancos miden que se OFRECE, no que se PROMETE.

LOS TRES MONTONES, Y POR QUE SON TRES Y NO UNO
----------------------------------------------
A. VERTICES SIN VOZ.  Marca `C`, `S` u `O` —es decir, vertice legitimo— y
   cero identificadores de Mathlib. El nodo dice ser una categoria y no
   aporta ni un nombre al prompt.

   OJO CON ESTE, QUE YO LO LEI MAL LA PRIMERA VEZ. No son diez olvidos: los
   diez llevan `lean=None` en el veredicto, y eso no es la ausencia de una
   decision sino una decision escrita —«ese nombre no existe en Mathlib»—.
   Asi que la pregunta no es «¿cual falta?» sino **¿sigue siendo verdad?**.
   El veredicto cita el arbol 05322f9 (28 ago 2026) y el indice es
   posterior; una decision sobre lo que Mathlib NO tiene caduca sola cada
   vez que Mathlib crece. `homotopy-type-theory` no caduca nunca —Lean 4 no
   es HoTT— y `homotopy-theory` puede haber caducado ya.

B. VERTICES MARCADOS FUERA.  Marca `T` —«ni objetos ni flechas»— y sin
   embargo son nodos de pleno derecho, con palabras clave que capturan
   consultas y flechas que enrutan. La contradiccion es exacta: el veredicto
   los expulsa y el grafo los usa.

C. MARCADOS FUERA Y CON VOZ.  Marca `T` y ADEMAS ofrecen identificadores al
   prompt. Es el montones A y B a la vez y al reves: lo peor de los dos.

Son tres porque la DECISION es distinta en cada uno. En A se elige un nombre
o se cambia la marca; en B se elige entre retirar, remarcar o dejar como
enrutador declarado; en C una de las dos mitades sobra y hay que decir cual.

POR QUE `T` ES EL MONTON QUE MAS URGE
-------------------------------------
Del veredicto del autor sobre `DECIDIDOS_SIN_NODO`: «`T` es la marca que no
se revisa nunca, asi que archivar bajo `T` algo que si hay que revisar
equivale a perderlo». Aquello eran diez modulos fuera del grafo. Esto son 38
nodos DENTRO, y llevan mas tiempo.

LO QUE PASO DESPUES, Y POR QUE ESTA HOJA ES MAS CORTA QUE SU PRIMERA VERSION
---------------------------------------------------------------------------
El veredicto sobre las 48 no contesto ficha por ficha: contesto que faltaba
UNA COLUMNA. El grafo tiene dos clases de nodo —concepto y rama— y una sola
columna para las dos, asi que 33 de las 36 del monton B no eran 33 decisiones
sino un campo ausente. Con `rol` escrito en `interpretacion.py`, la hoja pasa
de 48 fichas a menos de diez sin que nadie haya decidido caso por caso.

Esta hoja se regenera, asi que las cifras de aqui arriba son las de su
primera pasada y no las de hoy; lo que se imprime siempre es el estado
actual. Que encoja es la senal de que el diagnostico era el correcto.

LO QUE ESTA HOJA NO DECIDE
--------------------------
Si el nombre existe, en que modulo vive y cuantas veces se cita: todo eso
sale del indice y viene resuelto. Lo que no puede salir de ningun indice es
si el concepto es una categoria.

    python -m scripts.hoja_de_curacion_interna
    cd docs && pdflatex CURACION_INTERNA.tex
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

SALIDA = os.path.join(RAIZ, "docs", "CURACION_INTERNA.md")
SALIDA_TEX = os.path.join(RAIZ, "docs", "CURACION_INTERNA.tex")

#: Cuantos candidatos de Mathlib se ofrecen por nodo. Mas de seis y la hoja
#: deja de ser una decision para ser una lista de la compra.
TOPE_CANDIDATOS = 6

#: Cuantos se dan cuando NINGUNO es del area del nodo. Ver el comentario del
#: final de `candidatos()`: ahi la busqueda ya no sabe, y lo unico honesto es
#: dar pocas y decirlo.
TOPE_SIN_AREA = 3

#: LA TERCERA TRAMPA DE BABEL-ESPANOL, y la que costo este documento.
#:
#: `hoja_de_curacion.py` documenta dos —el `"` activo y `listings` leyendo
#: bytes—. Hay una tercera: **`~` tambien queda activo**. Escribir
#: `$\square$~{\small ...}` para separar el cuadradito de su texto revienta
#: con `Missing \endcsname inserted` y un `\language@active@arg~` en el log,
#: que no menciona ni a babel ni al `~`. Aqui se usa `\,` en su lugar.
ESPACIO_TRAS_CASILLA = r"\,"

#: Los tipos de declaracion que pueden ser el OBJETO de un concepto. Un
#: teorema no lo es nunca — de los 217 identificadores que el grafo ofrece
#: hoy, ninguno es un teorema, y esa es la razon.
TIPOS_OBJETO = frozenset({
    "structure", "class", "inductive", "def", "abbrev",
})

#: CUANTAS DECLARACIONES PUEDE TOCAR UNA PALABRA PARA SEGUIR SIENDO SENAL.
#:
#: La primera version de este buscador devolvia `CategoryTheory.Iso.symm`,
#: `...ShortComplex.Homotopy.symm` y otros dieciseis `symm` como candidatos a
#: objeto de `cic`. Dos fallos distintos, y los dos daban lo mismo por fuera:
#:
#:   1. buscaba en el NOMBRE ENTERO, asi que la palabra «theory» de «type
#:      theory» casaba con el `CategoryTheory.` de media biblioteca y traia de
#:      vuelta el metodo del final, que no es un objeto de nada;
#:   2. no tenia forma de saber que «type» o «space» no distinguen nada.
#:
#: Lo primero se arregla buscando solo en el NOMBRE CORTO. Lo segundo con
#: este tope: una palabra que toca mas de 300 declaraciones no esta senalando
#: un objeto, esta senalando un barrio. Es `_GENERICAS` otra vez —«una palabra
#: corriente no es senal»— pero MEDIDA en vez de enumerada, que es lo que hay
#: que hacer cuando el vocabulario es el de Mathlib y no el del usuario.
TOPE_POSTINGS = 300

#: LOS QUE EL TOPE NO CAZA, cada uno con la ficha que lo prueba.
#:
#: El tope de 300 descarta `order` (515), `limit` (591) y `continuous` (340).
#: Estos seis se quedan por debajo y son igual de inutiles para buscar un
#: objeto: no es cuestion de frecuencia sino de que no distinguen NADA. El
#: veredicto sobre las 48 los saco leyendo las fichas, que es donde se ven.
#:
#: Cada entrada dice que ficha lo delato, porque una lista de palabras
#: prohibidas sin su motivo se convierte en superticion a la tercera vez que
#: alguien la amplia.
GENERICAS_A_MANO = {
    "theory":   "las mismas tres filas `FirstOrder.Language.*` salian en "
                "homotopy-type-theory, ramsey-theory, computability-theory y "
                "proof-theory",
    "form":     "canonical-forms recibia BilinForm, traceForm, killingForm, "
                "formPerm",
    "complete": "np-completeness recibia CompleteSpace, CompleteLattice, "
                "CauSeq.IsComplete",
    "discrete": "discrete-optimization recibia DiscreteTopology, "
                "CategoryTheory.Discrete",
    "analytic": "analytic-number-theory recibia AnalyticAt, AnalyticOnNhd, "
                "AnalyticOn",
    "simplex":  "linear-programming recibia Affine.Simplex y SimplexCategory: "
                "el metodo simplex no es el simplex",
}

#: QUE PARTE DEL NOMBRE CORTO TIENE QUE CUBRIR LA PALABRA BUSCADA.
#:
#: Quitar el ruido de `symm` dejo otro debajo: `fol-deduction` traia
#: `Nat.stirlingFirst` y cinco `firstMap` —la palabra «first» de «first order
#: logic»— y `lambda-calculus` traia `ContinuousFunctionalCalculus`. La senal
#: que los separa no es la frecuencia sino la PROPORCION: en
#: `ContinuousMap.Homotopy` la palabra buscada ES el nombre corto entero; en
#: `ContinuousFunctionalCalculus` es una octava parte, y el nombre habla de
#: otra cosa.
#:
#: El umbral es mas duro cuando el nodo NO tiene area, porque entonces no hay
#: segunda senal que corrija: los fundacionales no pueden apoyarse en que el
#: candidato viva en su rama, asi que tienen que apoyarse en el nombre.
COBERTURA_MINIMA = 0.34
COBERTURA_SIN_AREA = 0.60


def _segmentos(nombre: str) -> set:
    """`Path.Homotopy` -> {path, homotopy}. Los trozos por los que se busca.

    Se parte por puntos y por CamelCase porque asi es como se leen los
    identificadores de Mathlib: `HomogeneousLocalization` es «homogeneous» y
    «localization», y quien cura busca una de las dos, no la cadena entera.
    """
    out = set()
    for parte in nombre.split("."):
        for s in re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+", parte):
            if len(s) >= 3:
                out.add(s.lower())
    return out


def indice_mathlib():
    """segmento del NOMBRE CORTO -> declaraciones. Solo tipos de objeto.

    Se indexa una vez y se consulta 48 veces. Al reves —recorrer el fichero
    por nodo— son 48 pasadas sobre 9 MB.

    Se indexa por el nombre CORTO y no por el entero a proposito: ver el
    comentario de `TOPE_POSTINGS`. `CategoryTheory.Iso.symm` se indexa bajo
    «symm», que es lo que declara, y no bajo «category» ni «theory», que son
    donde vive.
    """
    ruta = os.path.join(RAIZ, "data", "sustantivos_mathlib.jsonl")
    idx = {}
    for linea in io.open(ruta, encoding="utf-8"):
        linea = linea.strip()
        if not linea:
            continue
        try:
            d = json.loads(linea)
        except ValueError:
            continue
        if (d.get("tipo") or "") not in TIPOS_OBJETO:
            continue
        corto = d.get("corto") or (d.get("nombre") or "").split(".")[-1]
        if not corto:
            continue
        for seg in _segmentos(corto):
            idx.setdefault(seg, []).append(d)
    return idx


def _terminos(sid: str, nombre: str, keywords) -> set:
    """Por que palabras se busca el objeto de este nodo.

    Se filtran con `_GENERICAS`, la misma lista que usa el nucleo para
    decidir si una palabra es evidencia. Mismo principio, otro nivel: una
    palabra corriente no sirve para encontrar un objeto, igual que no sirve
    para ganar una plaza del prompt.
    """
    from nucleo.core import _GENERICAS
    bruto = set()
    for fuente in (nombre, sid.replace("-", " ")):
        for w in re.findall(r"[a-zA-Z]+", fuente):
            bruto.add(w.lower())
    for k in keywords or ():
        for w in re.findall(r"[a-zA-Z]+", k):
            bruto.add(w.lower())
    return {w for w in bruto if len(w) >= 4 and w not in _GENERICAS}


def candidatos(sid, nombre, keywords, area, idx, rama_a_area):
    """Los identificadores de Mathlib que podrian ser el objeto de este nodo.

    Ordenados por (coincide el area, citas). El area pesa mas que las citas
    a proposito: `Homotopy` en `AlgebraicTopology` vale para
    `homotopy-theory` y `HomotopicalAlgebra` en `ModelCategory` no, aunque
    las dos tengan 2 247 citas.

    Devuelve tambien las palabras que se DESCARTARON por genericas. Un nodo
    sin candidatos porque no hay objeto y un nodo sin candidatos porque todas
    sus palabras tocan medio Mathlib son dos cosas distintas, y la segunda le
    dice al que cura que busque a mano en vez de concluir que no hay nada.
    """
    minimo = COBERTURA_MINIMA if area else COBERTURA_SIN_AREA
    vistos, salida, genericas = set(), [], []
    for t in sorted(_terminos(sid, nombre, keywords)):
        postings = idx.get(t, ())
        if len(postings) > TOPE_POSTINGS or t in GENERICAS_A_MANO:
            genericas.append((t, len(postings)))
            continue
        for d in postings:
            nom = d.get("nombre") or ""
            if nom in vistos:
                continue
            corto = d.get("corto") or nom.split(".")[-1]
            if not corto or len(t) / float(len(corto)) < minimo:
                continue
            vistos.add(nom)
            mod = d.get("modulo") or ""
            rama = mod.split(".")[1] if mod.count(".") > 1 else ""
            mismo = 1 if (area and rama_a_area.get(rama) == area) else 0
            salida.append((mismo, int(d.get("citas") or 0), nom,
                           d.get("tipo") or "", mod))
    # SI HAY CANDIDATOS DEL AREA DEL NODO, LOS DE FUERA SOBRAN. Seis pistas
    # de las cuales cuatro son de otra rama no son seis pistas: son dos, con
    # cuatro distracciones que hay que descartar una por una.
    #
    # Y SI NO HAY NINGUNO DEL AREA, LA BUSQUEDA NO SABE. Este indice es
    # lexico: casa palabras contra nombres. Para `homotopy-theory` acierta —
    # `ContinuousMap.Homotopy` es exactamente eso— y para `fol-deduction`
    # devuelve seis `firstMap` porque «first order logic» empieza por
    # «first». No es un fallo que se pueda afinar: es la frontera de la
    # formalizacion, la misma que mide todo el proyecto. Un buscador que
    # imprime seis adivinanzas con la misma cara que seis aciertos le cuesta
    # al que cura mas tiempo del que le ahorra, asi que cuando no hay senal
    # de area se dan TRES como mucho y etiquetadas como lo que son.
    del_area = [x for x in salida if x[0]]
    if del_area:
        salida, fiable = del_area, True
    else:
        salida, fiable = salida, False
    salida.sort(key=lambda x: (-x[0], -x[1], x[2]))
    genericas.sort(key=lambda x: -x[1])
    tope = TOPE_CANDIDATOS if fiable else TOPE_SIN_AREA
    return salida[:tope], genericas, fiable


def reunir():
    """Los tres montones, con todo lo que hace falta para decidirlos."""
    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.graph import interpretacion as I
    from scripts.hoja_de_curacion import RAMA_A_AREA

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph
    S = list(g.skills)
    meta = {s.id: (s.metadata or {}) for s in S}

    # flechas reales (sin identidades) en los dos sentidos
    sal, ent = {}, {}
    for m in g.morphisms:
        if m.morphism_type.name == "IDENTITY":
            continue
        sal.setdefault(m.source_id, []).append(m.target_id)
        ent.setdefault(m.target_id, []).append(m.source_id)

    idx = indice_mathlib()

    filas = {"A": [], "B": [], "C": []}
    resueltas_por_rol = []
    for s in S:
        if meta[s.id].get("sort") != "CONCEPTO":
            continue
        mk = I.marca(s.id)
        nombres = [p.strip() for p in
                   re.split(r"[,+]", I.nombres_de_trabajo(s.id) or "")
                   if p.strip()]
        # UNA RAMA DECLARADA YA NO ES UNA CONTRADICCION, y por eso sale de la
        # hoja. Marca `T` con hijos era el sintoma; el diagnostico —le falta
        # una columna al grafo, no una marca— se escribio en `rol`, y con el
        # escrito el nodo dice dos cosas coherentes a la vez: no es un objeto
        # (marca) y si es estructura de enrutamiento (rol).
        #
        # La guardia que lo sostiene vive en `test_interpretacion.py`: una
        # rama no toma nombre nunca. El dia que una lo tome, vuelve aqui.
        if I.es_rama(s.id):
            resueltas_por_rol.append(s.id)
            continue
        if mk == I.T and nombres:
            monton = "C"
        elif mk == I.T:
            monton = "B"
        elif not nombres:
            monton = "A"
        else:
            continue

        area = meta[s.id].get("category") or ""
        kws = [k for k in (meta[s.id].get("keywords") or []) if k.strip()]
        hijos = sorted(set(sal.get(s.id, ())))
        # QUE SE ROMPERIA AL QUITARLO: los hijos cuya UNICA flecha de
        # entrada viene de este nodo. Sin esto, «retirar el nodo» es una
        # casilla que nadie puede marcar con criterio.
        sueltos = [h for h in hijos if set(ent.get(h, ())) == {s.id}]
        e = I.VEREDICTO.get(s.id)
        cand, genericas, fiable = candidatos(s.id, s.name or s.id, kws, area,
                                             idx, RAMA_A_AREA)
        filas[monton].append({
            "id": s.id,
            "nombre": s.name or s.id,
            "marca": mk,
            "area": area,
            "nivel": meta[s.id].get("level", getattr(s, "level", None)),
            "kws": kws,
            "nombres": nombres,
            "padres": sorted(set(ent.get(s.id, ()))),
            "hijos": hijos,
            "sueltos": sueltos,
            "nota": ((getattr(e, "nota", "") or getattr(e, "objeto", "")
                      or getattr(e, "morfismos", "") or "") if e else ""),
            "cand": cand,
            "genericas": genericas,
            "fiable": fiable,
        })

    # EN EL MONTON A MANDA LA CADUCIDAD, no el alfabeto. Los diez llevan
    # `lean=None` —«no existe en Mathlib»— y lo que hay que mirar primero es
    # aquel para el que el indice SI encuentra hoy algo en su propia area:
    # ese es el que puede haber dejado de ser verdad.
    filas["rol"] = sorted(resueltas_por_rol)
    filas["A"].sort(key=lambda f: (not f["fiable"], f["area"], f["id"]))
    for k in ("B", "C"):
        filas[k].sort(key=lambda f: (f["area"], f["id"]))
    return filas, len(S), sum(1 for s in S
                              if meta[s.id].get("sort") == "CONCEPTO")


# ─────────────────────────── el documento ────────────────────────────────

def _md(filas, n_nodos, n_conc):
    A, B, C = filas["A"], filas["B"], filas["C"]
    total = len(A) + len(B) + len(C)
    L = []
    L.append("# Curación interna\n")
    L.append("> Generado por `scripts/hoja_de_curacion_interna.py`. **No "
             "editar a mano**: se regenera.\n")
    L.append("")
    L.append("Las otras dos hojas miran hacia **afuera** — qué trozo de "
             "Mathlib no cubre el grafo. Ésta mira hacia **adentro**: de los "
             "%d conceptos que ya están, cuáles no cumplen lo que su propia "
             "marca promete.\n" % n_conc)
    L.append("Son **%d decisiones**, y ninguna medición las había pedido "
             "nunca — porque ninguna medición mira ahí. Los bancos miden lo "
             "que el grafo **ofrece**; esto es lo que el grafo **promete**.\n"
             % total)
    L.append("## El inventario completo, para que se vea qué parte es ésta\n")
    L.append("| montón | qué es | cuántos | dónde |")
    L.append("|---|---|---:|---|")
    L.append("| enunciados que fallan | los 62 que la cabecera fija no "
             "alcanzaba | **0** | agotado |")
    L.append("| cobertura de Mathlib | ramas que el grafo abrió y dejó finas "
             "| **24** | `CURACION_RAMAS.pdf` |")
    L.append("| **A · `lean=None` que puede haber caducado** | marca de "
             "vértice, cero nombres, y un «no existe» fechado en agosto "
             "| **%d** | *aquí* |" % len(A))
    L.append("| **B · vértices marcados fuera** | marca `T` y sin embargo son "
             "nodos | **%d** | *aquí* |" % len(B))
    L.append("| **C · marcados fuera y con voz** | marca `T` y además dan "
             "nombres | **%d** | *aquí* |" % len(C))
    L.append("")
    L.append("Lo que **no** hay que curar, para acotar el trabajo: la "
             "cobertura de marca en la capa curada es del **100 %** (los 205 "
             "nodos del autor la tienen; los 147 sin marca son 125 módulos de "
             "Mathlib y 22 áreas, que no son suyos), las 15 tácticas y "
             "estrategias son `T` y está bien —una táctica no es un objeto—, "
             "`homology` y `cohomology` tienen veredicto `F` y no son nodo —"
             "correcto, son flechas— y **ningún concepto se ha quedado sin "
             "palabras clave**: ninguno es inalcanzable desde una consulta.\n")
    L.append("---\n")

    L.append("## Qué hay que decidir, y por qué no lo decide nadie más\n")
    L.append("Las marcas, otra vez, porque son lo que está en juego:\n")
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
    L.append("**En el montón A** no hay ninguna promesa rota: hay diez "
             "`lean=None`, que es una decisión escrita —*no existe en "
             "Mathlib*— fechada en agosto. La decisión es **si sigue siendo "
             "verdad**, y es la única de las tres que caduca sola: cada vez "
             "que Mathlib crece, un «no existe» se acerca un poco más a ser "
             "falso.\n")
    L.append("**En el montón B** la promesa rota es al revés: `T` dice "
             "*fuera* y el nodo está dentro, enrutando. Tres salidas, y "
             "conviene no confundirlas:\n")
    L.append("- **se retira** — si de verdad no pinta nada. La hoja dice "
             "cuántos hijos quedarían sueltos;")
    L.append("- **cambia de marca** — si el veredicto se equivocó. La hoja "
             "dice si hay un objeto esperando en Mathlib;")
    L.append("- **se queda, declarado enrutador** — un nodo sin voz que "
             "existe sólo para que las palabras clave lleguen a sus hijos. Es "
             "una decisión legítima, pero **hoy no está escrita en ningún "
             "sitio**, y ésa es justamente la diferencia.")
    L.append("")
    L.append("> La tercera opción es la que más importa de las tres. Si es la "
             "correcta para la mayoría de los %d, entonces lo que falta no son "
             "%d decisiones sino **una marca nueva** — algo como `R` de "
             "enrutador — y la hoja se cierra de golpe. Si no lo es, hay que "
             "ir uno por uno.\n" % (len(B), len(B)))
    L.append("**En el montón C** la contradicción es exacta y no admite "
             "«se queda como está»: el veredicto dice que no son objetos y "
             "están alimentando plazas del prompt. Una de las dos mitades "
             "sobra.\n")
    L.append("### Qué valen los candidatos que trae cada ficha\n")
    L.append("Salen de un índice **léxico**: casan las palabras del nodo "
             "contra los nombres cortos de Mathlib. Donde el nodo tiene área, "
             "aciertan — a `homotopy-theory` le traen `ContinuousMap.Homotopy` "
             "y `Path.Homotopy`, que es exactamente lo que es. Donde no la "
             "tiene, **no saben**: a `fol-deduction` le traían seis `firstMap` "
             "porque «first order logic» empieza por «first».\n")
    L.append("No es un fallo que se pueda afinar. Es la misma frontera que "
             "mide todo el proyecto: el índice busca por palabras y el objeto "
             "se identifica por estructura. Así que las fichas marcan cuál de "
             "los dos casos es, y cuando no hay señal dan tres pistas en vez "
             "de seis. **Una lista vacía no demuestra que no haya objeto** — "
             "demuestra que por ahí no se encuentra.\n")
    L.append("---\n")

    def _por_area(f):
        return "área `%s`" % (f["area"] or "(fundacional)")

    def _por_caducidad(f):
        return ("el índice **sí** encuentra algo en su área hoy — empezar "
                "por éstos" if f["fiable"] else
                "el índice no encuentra nada en su área")

    def _bloque(titulo, entradas, casillas, intro, agrupar=None):
        agrupar = agrupar or _por_area
        L.append("## %s\n" % titulo)
        L.append(intro + "\n")
        grupo = None
        for f in entradas:
            if agrupar(f) != grupo:
                grupo = agrupar(f)
                L.append("### %s\n" % grupo)
            L.append("#### `%s` — %s\n" % (f["id"], f["nombre"]))
            L.append("| marca | nivel | palabras clave | padres | hijos | "
                     "hijos que quedarían sueltos |")
            L.append("|---|---|---:|---|---:|---:|")
            L.append("| `%s` | %s | %d | %s | %d | %s |" % (
                f["marca"], f["nivel"] if f["nivel"] is not None else "—",
                len(f["kws"]),
                ", ".join("`%s`" % p for p in f["padres"][:3]) or "—",
                len(f["hijos"]),
                ("**%d**" % len(f["sueltos"])) if f["sueltos"] else "0"))
            L.append("")
            if f["nota"]:
                L.append("> El veredicto dijo: «%s»\n" % f["nota"])
            if f["nombres"]:
                L.append("**Nombres que ya ofrece al prompt:** %s\n"
                         % ", ".join("`%s`" % x for x in f["nombres"]))
            if f["sueltos"]:
                L.append("Si se retira, quedan sueltos: %s\n"
                         % ", ".join("`%s`" % x for x in f["sueltos"]))
            if f["cand"]:
                L.append("**%s**\n" % (
                    "Candidatos en su área (existen; el módulo está "
                    "verificado)" if f["fiable"] else
                    "Ninguno en su área. Pistas léxicas, probablemente "
                    "ninguna sirve"))
                L.append("| identificador | tipo | citas | módulo |")
                L.append("|---|---|---:|---|")
                for mismo, citas, nom, tipo, mod in f["cand"]:
                    L.append("| `%s` | %s | %d | `%s` |"
                             % (nom, tipo, citas,
                                mod.replace("Mathlib.", "")))
                L.append("")
                if not f["fiable"]:
                    L.append("<small>El índice casa palabras contra nombres. "
                             "Sin señal de área no sabe, y estas tres salen "
                             "de que alguna palabra del nodo aparece en el "
                             "nombre — nada más.</small>\n")
            else:
                L.append("**No hay ningún candidato en el índice.** Ni "
                         "buscando por su nombre ni por sus palabras clave "
                         "aparece un `structure`, `class`, `def` o "
                         "`inductive` que pueda ser su objeto.\n")
            if f["genericas"]:
                L.append("<small>Descartadas por genéricas (tocan más de %d "
                         "declaraciones cada una): %s. Si el objeto existe, "
                         "hay que buscarlo a mano: sus palabras no "
                         "distinguen.</small>\n"
                         % (TOPE_POSTINGS,
                            ", ".join("`%s` (%d)" % (t, n)
                                      for t, n in f["genericas"][:6])))
            for c in casillas:
                L.append("- [ ] %s" % c)
            L.append("")
        L.append("---\n")

    _bloque(
        "Montón A · %d decisiones que pueden haber caducado" % len(A), A,
        ("**sigue sin nombre** — la decisión aguanta",
         "**ya no es verdad**, y el nombre que entra es: ",
         "**la marca era lo que estaba mal** → pasa a: `___`"),
        "Marca de vértice —`C`, `S` u `O`— y **cero identificadores de "
        "Mathlib**.\n\n**No son diez olvidos.** Los diez llevan `lean=None` "
        "en el veredicto, y eso no es la ausencia de una decisión sino una "
        "decisión escrita: *ese nombre no existe en Mathlib*. Así que la "
        "pregunta no es cuál falta, sino **si sigue siendo verdad**.\n\n"
        "Y una decisión sobre lo que Mathlib **no** tiene caduca sola cada "
        "vez que Mathlib crece. El veredicto cita el árbol `05322f9` "
        "(28 ago 2026) y el índice es posterior. `homotopy-type-theory` no "
        "caduca nunca —Lean 4 no es HoTT, y el propio veredicto lo llama «la "
        "única etiqueta excluida por fundamento, no por biblioteca»—; "
        "`homotopy-theory` puede haber caducado ya.\n\n"
        "Por eso van ordenados por caducidad y no por área: primero aquellos "
        "para los que el índice **sí** encuentra hoy algo en su propia rama.",
        agrupar=_por_caducidad)

    _bloque(
        "Montón B · %d vértices marcados fuera" % len(B), B,
        ("se **retira** del grafo",
         "**cambia de marca** a `___` y toma el nombre: ",
         "se queda como **enrutador declarado**: sin voz, sólo para que sus "
         "palabras clave lleguen a los hijos"),
        "Marca `T` —«ni objetos ni flechas»— y sin embargo son nodos de pleno "
        "derecho.\n\nEl caso más fuerte está aquí: **`zfc-axioms` está "
        "marcado `T`** y de él salen **143 flechas**. Su hermano fundacional "
        "`fol-deduction` está marcado `C`. Los dos pilares del grafo "
        "recibieron marcas opuestas, y ninguna medición iba a notarlo.")

    _bloque(
        "Montón C · %d marcados fuera y con voz" % len(C), C,
        ("**la marca estaba mal** → pasa a `___`",
         "**la marca está bien** → se le quitan los nombres",
         "sus propias notas ya lo susurran; escribir cuál de las dos gana"),
        "Marca `T` **y además** ofrecen identificadores al prompt. Es la "
        "contradicción exacta, y la única del documento que no admite «se "
        "queda como está».")

    L.append("## Antes de dar por buena cualquier respuesta\n")
    L.append("```\npython -m scripts.recuperacion_contra_proofnet\n"
             "python -m scripts.banco_docstrings\n"
             "python -m scripts.banco_herald\n```\n")
    L.append("**Baseline hoy: 23,9 % / 16,5 % contra ProofNet**, 5,0 % sobre "
             "Mathlib entero, 10,6 % contra Herald. Una tanda entra si sube "
             "su barrio y no baja el global.\n")
    L.append("Y aquí hay una asimetría que conviene tener presente: **quitar "
             "un nombre o retirar un nodo casi nunca baja la precisión**, "
             "así que el montón C y las retiradas del B se pueden medir "
             "barato. **Añadir** nombres sí tiene coste — la primera tanda "
             "bajó de 21,3 % a 19,9 % antes de que la puerta "
             "`_evidencia_declarada` lo arreglara. El montón A es el caro.\n")
    return L


def _tex(filas, n_nodos, n_conc):
    from scripts.hoja_de_curacion import PREAMBULO, tex, tt
    A, B, C = filas["A"], filas["B"], filas["C"]
    total = len(A) + len(B) + len(C)
    cab = PREAMBULO.split(r"\begin{document}")[0].replace(
        "curación pendiente", "curación interna").replace(
        "scripts/hoja_de_curacion.py", "scripts/hoja_de_curacion_interna.py")
    T = [cab]
    T.append(r"\begin{document}")
    T.append(r"\begin{center}")
    T.append(r"{\LARGE\bfseries\color{acento} Curación interna}\par\smallskip")
    T.append(r"{\color{suave}\small Lo que le falta al grafo por dentro: "
             + str(total) + r" nodos que no cumplen lo que su marca "
             r"promete.}\par")
    T.append(r"{\color{suave}\footnotesize Generado por "
             r"\texttt{scripts/hoja\_de\_curacion\_interna.py} · se regenera, "
             r"no se edita a mano}")
    T.append(r"\end{center}")
    T.append(r"\vspace{4pt}")

    T.append(r"\section*{De dónde sale esta hoja}")
    T.append(r"""
Las otras dos miran hacia \textbf{afuera} —qué trozo de \Mathlib{} no cubre el
grafo—. Ésta mira hacia \textbf{adentro}: de los """ + str(n_conc) + r"""
conceptos que ya están, cuáles no cumplen lo que su propia marca promete.
Son \textbf{""" + str(total) + r"""} decisiones, y ninguna medición las había
pedido nunca, porque ninguna medición mira ahí: los bancos miden lo que el
grafo \emph{ofrece}, no lo que \emph{promete}.\par\medskip
""")
    T.append(r"\noindent\small\begin{tabular}"
             r"{@{}>{\raggedright\arraybackslash}p{0.26\linewidth}"
             r">{\raggedright\arraybackslash}p{0.40\linewidth}r"
             r">{\raggedright\arraybackslash}p{0.16\linewidth}@{}}\toprule")
    T.append(r"montón & qué es & n.\ & dónde\\\midrule")
    T.append(r"enunciados que fallan & los 62 que la cabecera fija no "
             r"alcanzaba & 0 & agotado\\")
    T.append(r"cobertura de \Mathlib{} & ramas que el grafo abrió y dejó "
             r"finas & 24 & \texttt{CURACION\_RAMAS}\\")
    T.append(r"\textbf{A · \texttt{lean=None} caducable} & marca de vértice, "
             r"cero nombres, y un «no existe» fechado en agosto & \textbf{"
             + str(len(A)) + r"} & \emph{aquí}\\")
    T.append(r"\textbf{B · marcados fuera} & marca \texttt{T} y sin embargo "
             r"son nodos & \textbf{" + str(len(B)) + r"} & \emph{aquí}\\")
    T.append(r"\textbf{C · fuera y con voz} & marca \texttt{T} y además dan "
             r"nombres & \textbf{" + str(len(C)) + r"} & \emph{aquí}\\")
    T.append(r"\bottomrule\end{tabular}\par\medskip")
    T.append(r"""
\noindent Lo que \textbf{no} hay que curar, para acotar el trabajo: la
cobertura de marca en la capa curada es del \textbf{100\,\%} —los 205 nodos
del autor la tienen; los 147 sin marca son 125 módulos de \Mathlib{} y 22
áreas, que no son suyos—, las 15 tácticas y estrategias son \texttt{T} y está
bien, \texttt{homology} y \texttt{cohomology} tienen veredicto \texttt{F} y no
son nodo, y \textbf{ningún concepto se ha quedado sin palabras clave}.
\par\medskip
""")

    T.append(r"\section*{Qué hay que decidir, y por qué no lo decide nadie más}")
    T.append(r"\noindent\small\begin{tabular}{@{}ll l@{}}\toprule")
    T.append(r"\texttt{C} & una categoría & \textbf{vértice}\\")
    T.append(r"\texttt{S} & una subcategoría plena & \textbf{vértice}, y la "
             r"inclusión es arista\\")
    T.append(r"\texttt{F} & un funtor o clase de flechas & \textbf{arista} "
             r"\emph{en este ambiente}\\")
    T.append(r"\texttt{O} & un objeto individual & vértice degenerado\\")
    T.append(r"\texttt{T} & ni objetos ni flechas & \textbf{fuera}\\")
    T.append(r"\bottomrule\end{tabular}\par\medskip")
    T.append(r"""
\noindent\textbf{En el montón A} no hay ninguna promesa rota: hay diez
\texttt{lean=None}, que es una decisión escrita —\emph{no existe en
\Mathlib{}}— fechada en agosto. La decisión es \textbf{si sigue siendo
verdad}, y es la única de las tres que caduca sola: cada vez que \Mathlib{}
crece, un «no existe» se acerca un poco más a ser falso.\par\medskip
\noindent\textbf{En el montón B} la promesa rota es al revés: \texttt{T} dice
\emph{fuera} y el nodo está dentro, enrutando. Tres salidas: \textbf{se
retira} —la hoja dice cuántos hijos quedarían sueltos—, \textbf{cambia de
marca} —la hoja dice si hay un objeto esperando— o \textbf{se queda como
enrutador declarado}, un nodo sin voz que existe sólo para que sus palabras
clave lleguen a los hijos.\par\medskip
""")
    T.append(r"\begin{aviso}\small ")
    T.append(r"La tercera opción es la que más importa de las tres. Si es la "
             r"correcta para la mayoría de los " + str(len(B)) + r", lo que "
             r"falta no son " + str(len(B)) + r" decisiones sino \textbf{una "
             r"marca nueva} —algo como \texttt{R} de enrutador— y la hoja se "
             r"cierra de golpe. Si no lo es, hay que ir uno por uno.")
    T.append(r"\end{aviso}")
    T.append(r"""
\noindent\textbf{En el montón C} la contradicción es exacta y no admite «se
queda como está»: el veredicto dice que no son objetos y están alimentando
plazas del prompt. Una de las dos mitades sobra.\par\medskip
\subsection*{Qué valen los candidatos que trae cada ficha}
\noindent Salen de un índice \textbf{léxico}: casan las palabras del nodo
contra los nombres cortos de \Mathlib{}. Donde el nodo tiene área, aciertan —a
\texttt{homotopy-theory} le traen \texttt{ContinuousMap.Homotopy} y
\texttt{Path.Homotopy}, que es exactamente lo que es—. Donde no la tiene,
\textbf{no saben}: a \texttt{fol-deduction} le traían seis \texttt{firstMap}
porque «first order logic» empieza por «first».\par\medskip
\noindent No es un fallo que se pueda afinar. Es la misma frontera que mide
todo el proyecto: el índice busca por palabras y el objeto se identifica por
estructura. Las fichas marcan cuál de los dos casos es, y cuando no hay señal
dan tres pistas en vez de seis. \textbf{Una lista vacía no demuestra que no
haya objeto}: demuestra que por ahí no se encuentra.\par\medskip
""")

    def _por_area(f):
        return r"área \texttt{%s}" % tex(f["area"] or "(fundacional)")

    def _por_caducidad(f):
        return (r"el índice \textbf{sí} encuentra algo en su área hoy — "
                r"empezar por éstos" if f["fiable"] else
                r"el índice no encuentra nada en su área")

    def _bloque(titulo, entradas, casillas, intro, agrupar=None):
        agrupar = agrupar or _por_area
        T.append(r"\newpage")
        T.append(r"\section*{" + titulo + r"}")
        T.append(intro)
        T.append(r"\par\medskip")
        grupo = None
        for f in entradas:
            if agrupar(f) != grupo:
                grupo = agrupar(f)
                T.append(r"\subsection*{" + grupo + r"}")
            T.append(r"\noindent" + tt(f["id"]) + r"\quad{\color{suave}\small "
                     + tex(f["nombre"]) + r"}\par")
            T.append(r"{\small\color{suave}marca \texttt{" + tex(f["marca"])
                     + r"} · " + str(len(f["kws"])) + r" palabras clave · "
                     + str(len(f["hijos"])) + r" hijos · "
                     + (r"\textbf{" + str(len(f["sueltos"]))
                        + r" quedarían sueltos}" if f["sueltos"]
                        else r"0 quedarían sueltos") + r"}\par\smallskip")
            if f["nota"]:
                T.append(r"{\small\emph{El veredicto dijo:} " + tex(f["nota"])
                         + r"}\par\smallskip")
            if f["nombres"]:
                T.append(r"{\small\textbf{Ya ofrece al prompt:} "
                         + ", ".join(tt(x) for x in f["nombres"])
                         + r"}\par\smallskip")
            if f["cand"]:
                T.append(r"{\small\textbf{" + (
                    r"Candidatos en su área" if f["fiable"] else
                    r"Ninguno en su área. Pistas léxicas, probablemente "
                    r"ninguna sirve") + r"}}\par\smallskip")
                T.append(r"\noindent\small\begin{tabular}"
                         r"{@{}>{\raggedright\arraybackslash}p{0.34\linewidth}"
                         r"l r>{\raggedright\arraybackslash}"
                         r"p{0.34\linewidth}@{}}\toprule")
                T.append(r"identificador & tipo & citas & módulo\\\midrule")
                for mismo, citas, nom, tipo, mod in f["cand"]:
                    T.append(tt(nom) + r" & " + tex(tipo) + r" & " + str(citas)
                             + r" & " + tt(mod.replace("Mathlib.", ""))
                             + r"\\")
                T.append(r"\bottomrule\end{tabular}\par\smallskip")
            else:
                T.append(r"{\small\textbf{No hay ningún candidato en el "
                         r"índice.}}\par\smallskip")
            if f["genericas"]:
                T.append(r"{\footnotesize\color{suave}Descartadas por "
                         r"genéricas: "
                         + ", ".join(tt(t) + r"\,(" + str(n) + r")"
                                     for t, n in f["genericas"][:6])
                         + r". Si el objeto existe hay que buscarlo a mano: "
                         r"sus palabras no distinguen.}\par\smallskip")
            for c in casillas:
                T.append(r"\noindent$\square$" + ESPACIO_TRAS_CASILLA
                         + r"{\small " + c + r"}\par")
            T.append(r"\medskip")

    _bloque(
        r"Montón A · " + str(len(A))
        + r" decisiones que pueden haber caducado", A,
        (r"\textbf{sigue sin nombre} — la decisión aguanta",
         r"\textbf{ya no es verdad}, y el nombre que entra es: \dotfill",
         r"\textbf{la marca era lo que estaba mal} $\rightarrow$ pasa a: "
         r"\rule{2em}{0.4pt}"),
        r"""
Marca de vértice —\texttt{C}, \texttt{S} u \texttt{O}— y \textbf{cero
identificadores de \Mathlib{}}.\par\medskip
\noindent\textbf{No son diez olvidos.} Los diez llevan \texttt{lean=None} en
el veredicto, y eso no es la ausencia de una decisión sino una decisión
escrita: \emph{ese nombre no existe en \Mathlib{}}. La pregunta no es cuál
falta, sino \textbf{si sigue siendo verdad}.\par\medskip
\noindent Y una decisión sobre lo que \Mathlib{} \textbf{no} tiene caduca sola
cada vez que \Mathlib{} crece. El veredicto cita el árbol \texttt{05322f9}
(28 ago 2026) y el índice es posterior. \texttt{homotopy-type-theory} no
caduca nunca —Lean 4 no es HoTT, y el propio veredicto lo llama «la única
etiqueta excluida por fundamento, no por biblioteca»—;
\texttt{homotopy-theory} puede haber caducado ya. Por eso van ordenados por
caducidad y no por área.""",
        agrupar=_por_caducidad)

    _bloque(
        r"Montón B · " + str(len(B)) + r" vértices marcados fuera", B,
        (r"se \textbf{retira} del grafo",
         r"\textbf{cambia de marca} a \rule{2em}{0.4pt} y toma el nombre: "
         r"\dotfill",
         r"se queda como \textbf{enrutador declarado}: sin voz, sólo para que "
         r"sus palabras clave lleguen a los hijos"),
        r"""
Marca \texttt{T} —«ni objetos ni flechas»— y sin embargo son nodos de pleno
derecho. El caso más fuerte está aquí: \textbf{\texttt{zfc-axioms} está
marcado \texttt{T}} y de él salen \textbf{143 flechas}. Su hermano fundacional
\texttt{fol-deduction} está marcado \texttt{C}. Los dos pilares del grafo
recibieron marcas opuestas, y ninguna medición iba a notarlo.""")

    _bloque(
        r"Montón C · " + str(len(C)) + r" marcados fuera y con voz", C,
        (r"\textbf{la marca estaba mal} $\rightarrow$ pasa a "
         r"\rule{2em}{0.4pt}",
         r"\textbf{la marca está bien} $\rightarrow$ se le quitan los nombres",
         r"cuál de las dos gana, y por qué: \dotfill"),
        r"""
Marca \texttt{T} \textbf{y además} ofrecen identificadores al prompt. Es la
contradicción exacta, y la única del documento que no admite «se queda como
está».""")

    T.append(r"\newpage")
    T.append(r"\section*{Antes de dar por buena cualquier respuesta}")
    T.append(r"\begin{marca}\small")
    T.append(r"""
\texttt{python -m scripts.recuperacion\_contra\_proofnet}\par
\texttt{python -m scripts.banco\_docstrings}\par
\texttt{python -m scripts.banco\_herald}\par\medskip
\textbf{Baseline hoy: 22,8\,\% / 18,0\,\% contra ProofNet}, 5,0\,\% sobre
\Mathlib{} entero, 10,6\,\% contra Herald. Una tanda entra si sube su barrio y
no baja el global.\par\medskip
Y hay una asimetría que conviene tener presente: \textbf{quitar un nombre o
retirar un nodo casi nunca baja la precisión}, así que el montón C y las
retiradas del B se pueden medir barato. \textbf{Añadir} nombres sí tiene
coste —la primera tanda bajó de 21,3\,\% a 19,9\,\% antes de que la puerta
\texttt{\_evidencia\_declarada} lo arreglara—. El montón A es el caro.
""")
    T.append(r"\end{marca}")
    T.append(r"\end{document}")
    return T


def main() -> int:
    filas, n_nodos, n_conc = reunir()
    io.open(SALIDA, "w", encoding="utf-8").write(
        "\n".join(_md(filas, n_nodos, n_conc)))
    io.open(SALIDA_TEX, "w", encoding="utf-8").write(
        "\n".join(_tex(filas, n_nodos, n_conc)))
    caducables = sum(1 for f in filas["A"] if f["fiable"])
    print("monton A (lean=None caducable)   : %d  (%d con candidato en su "
          "area HOY)" % (len(filas["A"]), caducables))
    print("monton B (marcados T, sin voz)   : %d" % len(filas["B"]))
    print("monton C (marcados T, CON voz)   : %d" % len(filas["C"]))
    print("   cerradas por el campo `rol`     : %d" % len(filas["rol"]))
    print("                   QUEDAN PENDIENTES : %d de %d conceptos"
          % (len(filas["A"]) + len(filas["B"]) + len(filas["C"]), n_conc))
    print("-> %s" % SALIDA)
    print("-> %s" % SALIDA_TEX)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
