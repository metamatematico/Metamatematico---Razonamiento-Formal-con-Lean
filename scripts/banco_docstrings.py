# -*- coding: utf-8 -*-
"""Un banco de (enunciado informal, nombres de oro) sacado de Mathlib.

POR QUE HACE FALTA
------------------
La tanda de curacion metio 31 conceptos —formas modulares, algebras de Lie, el
ideal diferente, la categoria simplicial— y el banco con el que se mide el
vocabulario, ProofNet, son 371 ejercicios de Rudin, Artin, Munkres y
Dummit-Foote. NO CONTIENE NI UN EJERCICIO DE ESOS TEMAS.

Eso no es un detalle: significa que ProofNet solo puede medir el COSTE de esos
31 conceptos —ocupan plazas del prompt— y nunca su beneficio. Un instrumento
que solo puede restar no decide si algo aporta.

QUE ES UNA FILA
---------------
Mathlib documenta muchas declaraciones con un comentario `/-- ... -/` escrito
en ingles por quien la formalizo. Ese comentario es el lado CONSULTA; la
declaracion que hay debajo da el lado ORO, sus identificadores.

Es la misma forma que ProofNet —informal + formalizacion correcta— y sale
gratis, porque Mathlib ya esta en disco.

LA CONTAMINACION, Y COMO SE TRATA
---------------------------------
El docstring NOMBRA lo que documenta, casi siempre entre comillas invertidas:

    /-- If `τ` is a `CanonicallyOrderedAdd` monoid, then the notions
        `IsForwardInvariant` and `IsInvariant` are equivalent. -/
    theorem IsForwardInvariant.isInvariant ...

Dejarlo asi seria regalar la respuesta: el grafo "acertaria" copiando el
nombre que la pregunta ya trae. Es exactamente la familia de instrumento roto
que este repositorio caza. Asi que:

  1. se quita TODO lo que va entre comillas invertidas;
  2. se descarta la fila si el nombre de la declaracion sigue apareciendo;
  3. se descarta si tras limpiar quedan menos de 5 palabras.

Medido sobre los 20 modulos de la tanda: de 343 docstrings, 80 se nombran a si
mismos y 30 quedan en nada. Sobreviven 233. El filtro es caro y no es opcional.

EL NULO
-------
El mismo que usa `recuperacion_contra_proofnet`: ofrecer los nombres mas
frecuentes del grafo sin mirar la consulta. Sin el, un porcentaje no dice nada.

LA ALARMA DEL INSTRUMENTO
-------------------------
Si el nulo sale por encima del real, o si el real supera el 60 %, es que la
limpieza fallo y los nombres siguen en la consulta. Se avisa y se sale.

    python -m scripts.banco_docstrings              # todo Mathlib
    python -m scripts.banco_docstrings --tanda      # solo los 20 de la tanda
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

MATHLIB = os.path.join(RAIZ, ".lake", "packages", "mathlib", "Mathlib")
SALIDA = os.path.join(RAIZ, "data", "banco_docstrings.json")

#: Los 20 modulos que produjeron la tanda de curacion. Se miden aparte porque
#: son la unica razon por la que este banco existe.
MODULOS_TANDA = [
    "Computability/DFA.lean", "Computability/Language.lean",
    "Computability/Partrec.lean", "Computability/Primrec.lean", "Data/PFun.lean",
    "RingTheory/DedekindDomain/Different.lean",
    "RingTheory/Derivation/Basic.lean",
    "RingTheory/GradedAlgebra/Homogeneous/Ideal.lean",
    "RingTheory/GradedAlgebra/HomogeneousLocalization.lean",
    "SetTheory/ZFC/Class.lean", "SetTheory/ZFC/Basic.lean", "SetTheory/Lists.lean",
    "Topology/MetricSpace/Congruence.lean",
    "Topology/MetricSpace/Similarity.lean", "Topology/MetricSpace/Holder.lean",
    "Algebra/Lie/Basic.lean", "Algebra/Module/CharacterModule.lean",
    "NumberTheory/ModularForms/Basic.lean",
    "NumberTheory/ModularForms/SlashInvariantForms.lean",
    "NumberTheory/NumberField/InfinitePlace/Basic.lean",
    "AlgebraicTopology/SimplexCategory/Defs.lean",
    "Analysis/Complex/Circle.lean",
    "Analysis/Complex/UpperHalfPlane/Basic.lean",
    "Dynamics/Circle/RotationNumber/TranslationNumber.lean", "Dynamics/Flow.lean",
    "Geometry/Manifold/Algebra/LeftInvariantDerivation.lean",
    "Geometry/Manifold/Algebra/LieGroup.lean",
    "AlgebraicGeometry/ProjectiveSpectrum/Topology.lean",
    "LinearAlgebra/AffineSpace/FiniteDimensional.lean",
    "ModelTheory/Arithmetic/Presburger/Semilinear/Defs.lean",
]

#: docstring + la declaracion que documenta, con su firma (las lineas
#: sangradas que la continuan).
PAR = re.compile(
    r"/--(.*?)-/\s*\n"
    r"((?:@\[[^\]]*\]\s*\n)?[ ]*(?:private |protected |noncomputable )*"
    r"(?:theorem|lemma|def|structure|class|abbrev|instance)\s+"
    r"([A-Za-z_][\w.']*)[^\n]*(?:\n[ ]+[^\n]*)*)", re.S)

IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_.']*")

#: Palabras de Lean que no son nombres de Mathlib.
SINTAXIS = {
    "theorem", "lemma", "def", "structure", "class", "abbrev", "instance",
    "private", "protected", "noncomputable", "variable", "universe",
    "forall", "exists", "fun", "let", "have", "show", "from", "with",
    "where", "this", "type", "sort", "prop", "match", "deriving", "extends",
    "open", "namespace", "section", "end", "import", "attribute",
}

#: Minimo de palabras en el enunciado ya limpio.
MINIMO_PALABRAS = 5


def modulo_de(ruta: str) -> str:
    rel = os.path.relpath(ruta, os.path.dirname(MATHLIB))
    return rel[:-5].replace(os.sep, ".").replace("/", ".")


def _limpiar(doc: str) -> str:
    """El docstring SIN el codigo: es donde Mathlib escribe los nombres."""
    t = " ".join(doc.split())
    t = re.sub(r"`[^`]*`", " ", t)          # los nombres van aqui
    t = re.sub(r"\$[^$]*\$", " ", t)        # y a veces en LaTeX
    return " ".join(t.split())


def _oro(decl: str) -> set:
    """Los identificadores de la FIRMA. Lo de despues de `:=` es la prueba."""
    firma = decl.split(":=")[0]
    out = set()
    for n in IDENT.findall(firma):
        if n.lower() in SINTAXIS:
            continue
        if len(n) < 4 and "_" not in n and "." not in n:
            continue                         # variable ligada, no un nombre
        out.add(n)
    return out


def extraer(ficheros) -> tuple:
    """Devuelve (filas, descartes). Una fila es lo que se puede medir."""
    filas = []
    desc = {"se_nombra": 0, "corto": 0, "sin_oro": 0}
    for ruta in ficheros:
        try:
            src = io.open(ruta, encoding="utf-8", errors="replace").read()
        except Exception:                                    # noqa: BLE001
            continue
        mod = modulo_de(ruta)
        for doc, decl, nombre in PAR.findall(src):
            nl = _limpiar(doc)
            corto = nombre.split(".")[-1]
            # 1 · la fila que se nombra a si misma regala la respuesta
            if corto and corto in nl:
                desc["se_nombra"] += 1
                continue
            # 2 · sin frase no hay consulta
            if len(nl.split()) < MINIMO_PALABRAS:
                desc["corto"] += 1
                continue
            oro = _oro(decl)
            if not oro:
                desc["sin_oro"] += 1
                continue
            filas.append({"modulo": mod, "nombre": nombre,
                          "informal": nl, "oro": sorted(oro)})
    return filas, desc


def medir(filas, k: int) -> dict:
    """Precision y cobertura del grafo sobre estas filas, con su nulo."""
    import collections
    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.graph.interpretacion import nombres_de_trabajo, TANDA_CURACION
    from nucleo.texto import normalizar as _norm
    from scripts.recuperacion_contra_proofnet import ofrecidos_de

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph

    # EL NULO: los nombres mas comunes del grafo, sin mirar la consulta.
    todos = collections.Counter()
    for s in g.skill_ids:
        for p in re.split(r"[,+]", nombres_de_trabajo(s) or ""):
            p = p.strip()
            if p:
                todos[p] += 1
    nulo = set()
    for p, _ in todos.most_common(k * 3):
        nulo.add(_norm(p))
        nulo.add(_norm(p.split(".")[0]))

    res = {}
    for etq in ("grafo", "sin_tanda", "nulo"):
        tp = fp = fn = con_algo = 0
        for f in filas:
            oro = set()
            for x in f["oro"]:
                oro.add(_norm(x))
                oro.add(_norm(x.split(".")[0]))
            if etq == "nulo":
                ofr = set(nulo)
            else:
                ids = Nucleo._match_skills_to_query(n, f["informal"], g)
                if etq == "sin_tanda":
                    ids = [x for x in ids if x not in TANDA_CURACION]
                ofr = ofrecidos_de(n, ids, k, f["informal"])
            if ofr:
                con_algo += 1
            tp += len(ofr & oro)
            fp += len(ofr - oro)
            fn += len(oro - ofr)
        res[etq] = {
            "precision": 100.0 * tp / (tp + fp) if tp + fp else 0.0,
            "cobertura": 100.0 * tp / (tp + fn) if tp + fn else 0.0,
            "con_algo": con_algo, "tp": tp, "fp": fp, "fn": fn,
        }
    return res



def _huella_medida():
    """La huella del grafo que este banco acaba de usar.

    Se recalcula en vez de recibirse para que no dependa de que el llamante se
    acuerde de pasarla: un dato de procedencia que hay que recordar poner es
    un dato que algun dia falta.
    """
    from nucleo.graph.huella import huella_viva
    return huella_viva()

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tanda", action="store_true",
                    help="solo los modulos que produjeron la tanda de curacion")
    # EL `k` SE IMPORTA, NO SE ESCRIBE. Un medidor con el valor a mano mide
    # una configuracion que el sistema no sirve en cuanto la constante cambia,
    # y sus filas dejan de ser comparables con las de los otros bancos. Ya
    # paso dos veces en este repositorio; hay un guardian que lo caza.
    from nucleo.core import PLAZAS_CON_NOMBRES
    ap.add_argument("--k", type=int, default=PLAZAS_CON_NOMBRES,
                    help="plazas con nombres; por defecto, el de produccion")
    args = ap.parse_args()

    if not os.path.isdir(MATHLIB):
        print("no esta Mathlib en %s" % MATHLIB)
        return 1

    if args.tanda:
        ficheros = [os.path.join(MATHLIB, m) for m in MODULOS_TANDA]
        faltan = [m for m, p in zip(MODULOS_TANDA, ficheros)
                  if not os.path.exists(p)]
        ficheros = [p for p in ficheros if os.path.exists(p)]
        print("LOS MODULOS DE LA TANDA: %d de %d en disco"
              % (len(ficheros), len(MODULOS_TANDA)))
        if faltan:
            print("  no estan: %s" % ", ".join(faltan))
    else:
        ficheros = []
        for raiz, _d, fs in os.walk(MATHLIB):
            ficheros.extend(os.path.join(raiz, f) for f in fs
                            if f.endswith(".lean"))
        print("MATHLIB ENTERO: %d ficheros" % len(ficheros))

    filas, desc = extraer(ficheros)
    bruto = len(filas) + sum(desc.values())
    print()
    print("docstrings con declaracion : %d" % bruto)
    print("  se nombran a si mismos   : %d  (regalan la respuesta)"
          % desc["se_nombra"])
    print("  menos de %d palabras      : %d" % (MINIMO_PALABRAS, desc["corto"]))
    print("  sin identificadores      : %d" % desc["sin_oro"])
    print("  USABLES                  : %d" % len(filas))

    if not filas:
        print("\n  ATENCION: el filtro dejo cero filas — revisa la extraccion")
        return 1

    print("\nmidiendo con k=%d..." % args.k)
    res = medir(filas, args.k)

    print()
    for etq, txt in (("sin_tanda", "sin la tanda"), ("grafo", "con la tanda"),
                     ("nulo", "modelo nulo")):
        r = res[etq]
        print("  %-14s precision %5.1f %%   cobertura %5.1f %%   habla en %d de %d"
              % (txt, r["precision"], r["cobertura"], r["con_algo"], len(filas)))

    # ── LA ALARMA DEL INSTRUMENTO ────────────────────────────────────────
    p = res["grafo"]["precision"]
    if p > 60.0:
        print("\n  INSTRUMENTO ROTO: %.1f %% de precision es imposible sobre "
              "un banco limpio.\n  Lo mas probable es que la limpieza no "
              "quitara los nombres de la consulta." % p)
        return 1
    if res["nulo"]["precision"] >= p:
        print("\n  EL NULO GANA O EMPATA: el grafo no aporta sobre este banco.")

    factor = (p / res["nulo"]["precision"]) if res["nulo"]["precision"] else 0.0
    print("\n  factor sobre el nulo: %.1fx" % factor)

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    io.open(SALIDA, "w", encoding="utf-8").write(json.dumps(
        {"ambito": "tanda" if args.tanda else "mathlib",
         "k": args.k, "filas": len(filas), "descartes": desc,
         # la huella del grafo medido: ver nucleo/graph/huella.py
         "grafo": _huella_medida(),
         "resultados": res,
         "muestra": filas[:20]},
        ensure_ascii=False, indent=2))
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
