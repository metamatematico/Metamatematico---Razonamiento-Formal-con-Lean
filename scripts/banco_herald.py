# -*- coding: utf-8 -*-
"""El mismo banco, pero con los enunciados informales de Herald.

POR QUE HAY DOS BANCOS Y NO UNO
-------------------------------
`banco_docstrings.py` saca el lado informal de los comentarios `/-- ... -/` de
Mathlib. Eso es gratis y cubre TODOS los modulos, pero tiene un parentesco
incomodo: los nombres del grafo salieron de leer Mathlib, y el oro de este
banco tambien. Un resultado alto puede ser eco.

Herald (`FrenzyMath/Herald_proofs`, 44 553 filas, Apache 2.0) es el control.
Sus enunciados informales estan REESCRITOS por otro sistema a partir de la
formalizacion, asi que:

  · son frases completas, no comentarios con el nombre dentro;
  · no los produjo este repositorio, ni su extractor;
  · el lado formal sigue siendo Mathlib, que no se equivoca sobre si mismo.

LO QUE HERALD NO CUBRE, Y HAY QUE DECIRLO
-----------------------------------------
Esta construido sobre Mathlib v4.11. De los 31 nodos de la tanda de curacion
toca 25, con 695 filas; seis se quedan a cero —`different-ideal`,
`lie-groups`, `semilinear-sets`, `similarity-transformations`,
`congruence-transformations` y `holder-continuity`— porque sus modulos son
posteriores. Para esos seis, el banco de docstrings es lo unico que hay.

LA MISMA CONTAMINACION, COMPROBADA IGUAL
----------------------------------------
Un enunciado informal puede seguir nombrando su teorema. Se aplica el mismo
filtro que en el otro banco y se cuenta cuantas filas caen, porque la cifra
sin ese recuento no es interpretable.

    python -m scripts.banco_herald            # las 44 553
    python -m scripts.banco_herald --tanda    # solo las que tocan la tanda
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

HERALD = "E:/MetamatematicoDataSet/Herald_proofs"
SALIDA = os.path.join(RAIZ, "data", "banco_herald.json")

#: prefijo de Mathlib -> nodo de la tanda que lo cubre. Sirve para el
#: subconjunto `--tanda`, no para puntuar.
PREFIJOS = {
    "ModularForm": "modular-forms", "SlashInvariantForm": "slash-invariant-forms",
    "LieAlgebra": "lie-algebras", "LieRing": "lie-algebras",
    "LieHom": "lie-algebra-morphisms", "LieModuleHom": "lie-algebra-morphisms",
    "LieGroup": "lie-groups",
    "LeftInvariantDerivation": "left-invariant-derivations",
    "Derivation": "derivations", "differentIdeal": "different-ideal",
    "HomogeneousIdeal": "homogeneous-ideals",
    "HomogeneousLocalization": "homogeneous-localization",
    "ZFSet": "zfc-sets", "Class": "zfc-classes",
    "Lists": "hereditarily-finite-sets",
    "Similar": "similarity-transformations",
    "Congruent": "congruence-transformations", "Holder": "holder-continuity",
    "CharacterModule": "character-modules",
    "NumberField.InfinitePlace": "infinite-places",
    "SimplexCategory": "simplex-category", "Circle": "unit-circle",
    "UpperHalfPlane": "upper-half-plane", "PFun": "partial-functions",
    "CircleDeg1Lift": "rotation-number", "Flow": "flows",
    "ProjectiveSpectrum": "projective-spectrum",
    "Collinear": "collinearity-coplanarity",
    "Coplanar": "collinearity-coplanarity",
    "IsSemilinearSet": "semilinear-sets", "DFA": "finite-automata",
    "Language": "formal-languages", "Partrec": "partial-recursive-functions",
    "Primrec": "primitive-recursive-functions",
}

IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_.']*")
SINTAXIS = {
    "theorem", "lemma", "def", "structure", "class", "abbrev", "instance",
    "forall", "exists", "fun", "let", "have", "show", "from", "with",
    "where", "this", "type", "sort", "prop", "match", "deriving", "extends",
    "open", "namespace", "section", "end", "import", "variable", "universe",
}
MINIMO_PALABRAS = 5


def _limpiar(t: str) -> str:
    t = " ".join((t or "").split())
    t = re.sub(r"`[^`]*`", " ", t)
    t = re.sub(r"\$[^$]*\$", " ", t)
    return " ".join(t.split())


def _oro(formal: str) -> set:
    firma = (formal or "").split(":=")[0]
    out = set()
    for n in IDENT.findall(firma):
        if n.lower() in SINTAXIS:
            continue
        if len(n) < 4 and "_" not in n and "." not in n:
            continue
        out.add(n)
    return out


def toca_tanda(nombre: str) -> bool:
    nombre = nombre or ""
    for p in PREFIJOS:
        if nombre == p or nombre.startswith(p + ".") or ("." + p + ".") in nombre:
            return True
    return False


def cargar(solo_tanda: bool):
    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)
    from datasets import load_from_disk

    d = load_from_disk(HERALD)
    filas = []
    desc = {"se_nombra": 0, "corto": 0, "sin_oro": 0, "fuera_de_tanda": 0}
    for x in d:
        nombre = x.get("name") or ""
        if solo_tanda and not toca_tanda(nombre):
            desc["fuera_de_tanda"] += 1
            continue
        nl = _limpiar(x.get("informal_theorem"))
        corto = nombre.split(".")[-1]
        if corto and corto in nl:
            desc["se_nombra"] += 1
            continue
        if len(nl.split()) < MINIMO_PALABRAS:
            desc["corto"] += 1
            continue
        oro = _oro(x.get("formal_theorem"))
        if not oro:
            desc["sin_oro"] += 1
            continue
        filas.append({"nombre": nombre, "informal": nl, "oro": sorted(oro)})
    return filas, desc


def medir(filas, k: int) -> dict:
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
                    ids = [s for s in ids if s not in TANDA_CURACION]
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tanda", action="store_true",
                    help="solo las filas que tocan un nodo de la tanda")
    # EL `k` SE IMPORTA, NO SE ESCRIBE. Un medidor con el valor a mano mide
    # una configuracion que el sistema no sirve en cuanto la constante cambia,
    # y sus filas dejan de ser comparables con las de los otros bancos. Ya
    # paso dos veces en este repositorio; hay un guardian que lo caza.
    from nucleo.core import PLAZAS_CON_NOMBRES
    ap.add_argument("--k", type=int, default=PLAZAS_CON_NOMBRES,
                    help="plazas con nombres; por defecto, el de produccion")
    args = ap.parse_args()

    if not os.path.isdir(HERALD):
        print("no esta Herald en %s" % HERALD)
        print("  bajarlo con: load_dataset('FrenzyMath/Herald_proofs')")
        return 1

    filas, desc = cargar(args.tanda)
    print("HERALD %s" % ("· solo la tanda" if args.tanda else "· entero"))
    if args.tanda:
        print("  fuera de la tanda        : %d" % desc["fuera_de_tanda"])
    print("  se nombran a si mismos   : %d  (regalan la respuesta)"
          % desc["se_nombra"])
    print("  menos de %d palabras      : %d" % (MINIMO_PALABRAS, desc["corto"]))
    print("  sin identificadores      : %d" % desc["sin_oro"])
    print("  USABLES                  : %d" % len(filas))
    if not filas:
        print("\n  ATENCION: cero filas tras el filtro")
        return 1

    print("\nmidiendo con k=%d..." % args.k)
    res = medir(filas, args.k)
    for etq, txt in (("sin_tanda", "sin la tanda"), ("grafo", "con la tanda"),
                     ("nulo", "modelo nulo")):
        r = res[etq]
        print("  %-14s precision %5.1f %%   cobertura %5.1f %%   habla en %d de %d"
              % (txt, r["precision"], r["cobertura"], r["con_algo"], len(filas)))

    p, pn = res["grafo"]["precision"], res["nulo"]["precision"]
    if p > 60.0:
        print("\n  INSTRUMENTO ROTO: %.1f %% es imposible sobre un banco "
              "limpio; probablemente los nombres siguen en la consulta." % p)
        return 1
    print("\n  factor sobre el nulo: %.1fx" % ((p / pn) if pn else 0.0))

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    io.open(SALIDA, "w", encoding="utf-8").write(json.dumps(
        {"ambito": "tanda" if args.tanda else "herald-entero", "k": args.k,
         "filas": len(filas), "descartes": desc, "resultados": res,
         "muestra": filas[:20]}, ensure_ascii=False, indent=2))
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
