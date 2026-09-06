# -*- coding: utf-8 -*-
"""¿Sirve de algo BUSCAR en los 217 419 nombres, en vez de sólo comprobarlos?

EL HUECO QUE MIDE
-----------------
El repositorio tiene 217 419 nombres de Mathlib indexados, con su módulo. Se
consultan para saber si un nombre existe y para cualificarlo antes de compilar.
NUNCA para buscar. Lo que decide qué nombres entran en el prompt es el
vocabulario curado a mano por skill, y ahí mandan las colisiones de palabra:
«Banach» lleva a los espacios de Banach, no al teorema del punto fijo.

Este script pregunta si el índice, usado como buscador, bate a ese vocabulario.

EL BANCO ES EL MISMO QUE `recuperacion_contra_proofnet.py`, y a propósito: 371
ejercicios de ProofNet con el enunciado en lenguaje natural Y su formalización
escrita por matemáticos. La formalización de oro dice QUÉ identificadores hacían
falta de verdad. Mismo K, mismo modelo nulo, misma normalización Lean 3 ↔
Mathlib 4, para que las columnas se puedan poner una al lado de la otra.

CÓMO BUSCA
----------
Índice invertido de token → nombres. Un nombre de Mathlib se parte por `.`, por
`_` y por mayúscula: `Nat.succ_le_iff` da {nat, succ, iff}. La consulta se parte
igual. La puntuación es la suma de las idf de los tokens que coinciden, así que
un token que sale en media biblioteca —`theorem`, `set`— pesa poco y uno raro
—`irrational`, `nilpotent`— pesa mucho. Es lo mismo que hace el emparejador a
mano, pero sobre los 217 419 en vez de sobre las 173 skills curadas.

TODAS LAS COLUMNAS OFRECEN EXACTAMENTE K NOMBRES. Comparar precisión entre
configuraciones que ofrecen distinto número no mide nada.

LO QUE ESTA MEDIDA NO DICE. Nada sobre si el nombre recuperado CIERRA la
prueba: dice si es uno de los que la formalización de oro usa. Es la misma
métrica que la hermana, con la misma limitación.

No gasta API ni Lean.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.recuperacion_contra_proofnet import cargar, nombres_de_oro, _norm

SALIDA = RAIZ / "data" / "recuperacion_por_indice.json"

#: Palabras que salen en media biblioteca y no distinguen. La idf ya las
#: castiga, pero quitarlas de la consulta ahorra recorrer listas enormes.
_VACIAS = frozenset("""
the a an of to in for that this with and or not is are be as by on it its
prove show let then thus such any all some every there exists we have has
where which when if only iff such theorem lemma statement problem exercise
suppose assume given consider define defined denote denotes call called
""".split())

_PARTE = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z]+|[0-9]+")


def trozos(nombre: str) -> set:
    """Los tokens de un nombre de Mathlib o de una frase.

    `Nat.succ_le_iff` -> {nat, succ, iff};  `IsCompact` -> {compact}.
    Se piden tres letras como minimo: `le`, `of`, `to` no distinguen nada.
    """
    return {t.lower() for t in _PARTE.findall(nombre or "") if len(t) >= 3}


def construir_indice(nombres):
    """token -> nombres que lo contienen, y la idf de cada token."""
    inv = collections.defaultdict(set)
    for n in nombres:
        for t in trozos(n):
            inv[t].add(n)
    total = max(1, len(nombres))
    idf = {t: math.log(total / len(ns)) for t, ns in inv.items()}
    return inv, idf


def buscar(consulta, inv, idf, k, tope_candidatos=4000):
    """Los k nombres mejor puntuados para esta consulta."""
    tokens = {t for t in trozos(consulta) if t not in _VACIAS}
    # los tokens rarísimos primero: acotan el conjunto de candidatos
    tokens = sorted(tokens, key=lambda t: -idf.get(t, 0.0))
    puntos = collections.Counter()
    vistos = 0
    for t in tokens:
        ns = inv.get(t)
        if not ns:
            continue
        peso = idf[t]
        # un token que sale en media biblioteca no acota nada y cuesta mucho
        if len(ns) > tope_candidatos:
            continue
        for n in ns:
            puntos[n] += peso
        vistos += 1
        if vistos >= 12:
            break
    return [n for n, _ in puntos.most_common(k)]


def main(a) -> int:
    from nucleo.lean import nombres as N
    N._cargar()
    todos = sorted(N._NOMBRES or ())
    if not todos:
        print("no hay indice de nombres")
        return 1

    filas = cargar()
    if not filas:
        print("no se pudo leer ProofNet")
        return 1
    print("%d ejercicios de ProofNet · %d nombres en el indice"
          % (len(filas), len(todos)))

    print("construyendo el indice invertido...")
    inv, idf = construir_indice(todos)
    print("  %d tokens distintos" % len(inv))

    # ── EL NULO SE TOMA DEL BANCO, NO SE RECALCULA AQUI ────────────────────
    #
    # La primera version lo calculaba como «los K nombres mas frecuentes en las
    # formalizaciones de oro» —de ESTE mismo banco— y salia 18,2 % de precision
    # contra el 1,6 % que da el banco. La diferencia era FUGA: el nulo estaba
    # mirando las respuestas. Un nulo inflado hace que todo lo demas parezca
    # peor de lo que es, que es la manera elegante de equivocarse.
    #
    # Se usa el del banco hermano, que se calcula sin mirar el oro.

    def evalua(elige, etiqueta):
        tp = fp = fn = 0
        con_algo = 0
        for _id, nl, fs in filas:
            oro = {_norm(x) for x in nombres_de_oro(fs)}
            ofrecidos = elige(nl)[:a.k]
            if ofrecidos:
                con_algo += 1
            propuestos = {_norm(x) for x in ofrecidos}
            aciertos = propuestos & oro
            tp += len(aciertos)
            fp += len(propuestos - oro)
            fn += len(oro - propuestos)
        prec = 100 * tp / max(1, tp + fp)
        cob = 100 * tp / max(1, tp + fn)
        print("  %-16s precision %5.1f %%   cobertura %5.1f %%   "
              "(tp %d, fp %d, con algo %d)"
              % (etiqueta, prec, cob, tp, fp, con_algo))
        return {"precision": round(prec, 2), "cobertura": round(cob, 2),
                "tp": tp, "fp": fp, "fn": fn, "con_algo": con_algo}

    print()
    print("K = %d — todas las columnas ofrecen el mismo numero de nombres" % a.k)
    res = {}
    res["INDICE_todo"] = evalua(
        lambda nl: buscar(nl, inv, idf, a.k), "INDICE (217k)")

    # SOLO SUSTANTIVOS. Las formalizaciones citan TIPOS —`Irrational`, `Set`,
    # `PartialOrder`— y el indice es 84 % lemas, asi que la busqueda devolvia
    # `Irrational.ne_rational` donde el oro pedia `Irrational`: relevante, y
    # cero segun la metrica. Restringir al indice de sustantivos es darle la
    # mejor oportunidad posible.
    try:
        import io as _io
        sus = []
        for linea in _io.open(RAIZ / "data" / "sustantivos_mathlib.jsonl",
                              encoding="utf-8"):
            d = json.loads(linea)
            n = d.get("nombre") or d.get("name")
            if n:
                sus.append(n)
        inv_s, idf_s = construir_indice(sus)
        res["INDICE_sustantivos"] = evalua(
            lambda nl: buscar(nl, inv_s, idf_s, a.k),
            "INDICE (34k sust.)")
    except Exception as e:                                     # noqa: BLE001
        print("  (sin indice de sustantivos: %s)" % e)

    # ── la referencia: el vocabulario curado del grafo ─────────────────────
    try:
        viejo = json.loads(
            (RAIZ / "data" / "recuperacion_proofnet.json").read_text("utf-8"))
        lex = viejo["resultados"]["lexico"]
        print("  %-16s precision %5.1f %%   cobertura %5.1f %%   (medido antes)"
              % ("lexico (grafo)", lex["precision"], lex["cobertura"]))
        res["lexico_grafo"] = lex
    except Exception:                                          # noqa: BLE001
        pass

    print()
    try:
        nulo = viejo["resultados"]["nulo"]
        res["nulo_del_banco"] = nulo
        print("  %-16s precision %5.1f %%   cobertura %5.1f %%   (del banco)"
              % ("nulo", nulo["precision"], nulo["cobertura"]))
    except Exception:                                          # noqa: BLE001
        nulo = None
    print()
    mejor = max((res[k]["precision"], k) for k in res
                if k.startswith("INDICE"))[1]
    if "lexico_grafo" in res:
        print("  el mejor INDICE (%s) contra el vocabulario curado: %+.1f "
              "precision" % (mejor,
                             res[mejor]["precision"]
                             - res["lexico_grafo"]["precision"]))
    if nulo:
        print("  el mejor INDICE contra el nulo:                    %+.1f "
              "precision" % (res[mejor]["precision"] - nulo["precision"]))

    SALIDA.write_text(json.dumps(
        {"n": len(filas), "k": a.k, "nombres_indice": len(todos),
         "tokens": len(inv), "resultados": res},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print("escrito -> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--k", type=int, default=2)
    raise SystemExit(main(ap.parse_args()))
