# -*- coding: utf-8 -*-
"""¿La FORMA del enunciado dice con qué táctica se ataca?

QUE ES LEAN WORKBOOK. Un conjunto de problemas de competición formalizados en
Lean 4. En disco hay dos piezas, y de la segunda sólo se estaba usando una
esquina:

    LeanWorkbookProofs   29 750 PRUEBAS COMPLETAS que compilan
    LeanWorkbook         25 214 filas con `state_before` -> `tactic` ->
                         `state_after`, es decir transiciones de estado de
                         prueba etiquetadas

De las 29 750 pruebas, `construir_banco_lemas.py` extraía sólo los NOMBRES DE
LEMA citados y tiraba el resto. Lo que se tiraba es el guion de la prueba: la
secuencia de tácticas que de verdad la cerró. Y el paso 5 del sistema —el orden
de la cascada— es el punto del grafo que mejor está medido (2,59 -> 1,29
intentos), así que es donde más vale mejorar.

LO QUE MIDE ESTE SCRIPT. Predecir la PRIMERA TÁCTICA de la prueba a partir del
enunciado, que es exactamente lo que la cascada tiene que decidir. Tres vías
contra el mismo nulo:

    nulo         la táctica mayoritaria (`nlinarith`)
    n-gramas     char_wb 1-4 sobre el enunciado (lo que había)
    ESTRUCTURA   la relación principal, los tipos, los operadores, la forma
                 de las hipótesis (los 68 rasgos de sintaxis_contra_premisas)

CUIDADO CON EL EXTRACTOR, que ya se rompió tres veces aquí y siempre por lo
mismo: los COMENTARIOS. Estas pruebas llevan un bloque `/- ... -/` con la
explicación y además comentarios `--` intercalados en cada paso. Sin quitar los
dos, el 82 % de las pruebas «no tenían táctica» y la distribución que salía era
de una muestra sesgada del 18 %. Es el mismo fallo que una vez hizo que `the`
apareciera como el lema más citado de Mathlib. Por eso este script AVISA si no
consigue extraer de todas.

    python scripts/sintaxis_contra_tacticas.py
"""
import argparse
import collections
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FUENTE = "E:/MetamatematicoDataSet/LeanWorkbookProofs"
SALIDA = "E:/Metamatematico/data/sintaxis_contra_tacticas.json"

#: sólo las tácticas con ejemplos suficientes; por debajo el modelo memoriza
MINIMO = 50

BLOQUE = re.compile(r"/-.*?-/", re.S)
LINEA = re.compile(r"--[^\n]*")
IDENT = re.compile(r"[a-zA-Z_][\w'!?]*")


def parte(prueba: str):
    """(enunciado, primera táctica) de una prueba completa, o None."""
    i = prueba.find(":= by")
    j = prueba.find("theorem ")
    if i < 0 or j < 0:
        return None
    enun = prueba[j + 8:i]
    enun = enun[enun.find(" "):] if " " in enun else enun    # fuera el nombre
    cuerpo = LINEA.sub(" ", BLOQUE.sub(" ", prueba[i + 5:]))
    for linea in cuerpo.split("\n"):
        m = IDENT.match(linea.strip().lstrip("·<;>[]() "))
        if m:
            return enun.strip(), m.group(0)
    return None


def main(a):
    import numpy as np
    from datasets import load_from_disk
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import LinearSVC
    from sklearn.metrics import accuracy_score, balanced_accuracy_score
    from scipy.sparse import hstack
    from sintaxis_contra_premisas import rasgos

    d = load_from_disk(FUENTE)
    ds = d[list(d.keys())[0]] if hasattr(d, "keys") else d
    pares = [parte(r["full_proof"]) for r in ds]
    fallos = sum(1 for p in pares if p is None)
    print("LeanWorkbookProofs: %d pruebas · sin extraer: %d" % (len(ds), fallos))
    if fallos > len(ds) * 0.02:
        print("     ATENCIÓN: el extractor falla en el %.1f %%. La distribución "
              "que salga es de una muestra sesgada — revisar los comentarios."
              % (100 * fallos / len(ds)))
        return 1

    X = [p[0] for p in pares if p]
    y = np.array([p[1] for p in pares if p])
    frec = collections.Counter(y)
    keep = np.array([frec[v] >= MINIMO for v in y])
    X = [x for x, k in zip(X, keep) if k]
    y = y[keep]
    n = int(len(X) * 0.8)
    Xtr, Xte, ytr, yte = X[:n], X[n:], y[:n], y[n:]
    clases = sorted(set(y))
    print("%d enunciados · %d tácticas con >= %d ejemplos · train %d test %d\n"
          % (len(X), len(clases), MINIMO, n, len(Xte)))

    may = collections.Counter(ytr).most_common(1)[0][0]
    res = {"nulo": (100 * (yte == may).mean(), 100.0 / len(clases))}

    vN = TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 4), min_df=3,
                         max_features=40000)
    Ntr, Nte = vN.fit_transform(Xtr), vN.transform(Xte)
    vE = DictVectorizer(sparse=True)
    Etr = vE.fit_transform([rasgos(x) for x in Xtr])
    Ete = vE.transform([rasgos(x) for x in Xte])

    for etq, A, B in (("n-gramas", Ntr, Nte),
                      ("ESTRUCTURA", Etr, Ete),
                      ("las dos", hstack([Ntr, Etr]).tocsr(),
                       hstack([Nte, Ete]).tocsr())):
        p = LinearSVC(max_iter=3000).fit(A, ytr).predict(B)
        res[etq] = (100 * accuracy_score(yte, p),
                    100 * balanced_accuracy_score(yte, p))

    print("  %-14s %11s %14s" % ("", "exactitud", "equilibrada"))
    for k in ("nulo", "n-gramas", "ESTRUCTURA", "las dos"):
        print("  %-14s %9.1f %% %12.1f %%" % (k, res[k][0], res[k][1]))
    print("\n  rasgos: n-gramas %d · estructura %d" % (Ntr.shape[1], Etr.shape[1]))

    io.open(SALIDA, "w", encoding="utf-8").write(json.dumps({
        "pruebas": len(ds), "usadas": len(X), "tacticas": len(clases),
        "minimo_ejemplos": MINIMO, "mayoritaria": may,
        "resultados": {k: [round(v[0], 2), round(v[1], 2)]
                       for k, v in res.items()},
        "distribucion": dict(collections.Counter(y).most_common(12)),
    }, ensure_ascii=False, indent=1))
    print("  -> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sys.exit(main(ap.parse_args()))
