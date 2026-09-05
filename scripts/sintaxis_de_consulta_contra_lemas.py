# -*- coding: utf-8 -*-
"""¿La sintaxis de LA CONSULTA ayuda a recuperar los lemas? Contra la verdad.

QUE PREGUNTA ES ESTA Y EN QUE SE DIFERENCIA DE LA HERMANA
---------------------------------------------------------
`sintaxis_contra_premisas.py` ya midió que 68 rasgos de estructura igualan a
40 000 n-gramas prediciendo qué lemas usa una prueba. Pero aquellos rasgos se
calculan sobre el ENUNCIADO DE LEAN, que sólo existe DESPUES de que el modelo
formalice. Para elegir qué meter en el prompt de formalización no servían: en
ese momento no hay enunciado de Lean, hay una consulta escrita a mano.

Esto mide lo mismo sobre lo que SI hay antes de llamar a nadie: el árbol de la
consulta en lenguaje natural. Misma tabla, mismo corpus, mismo K, mismo modelo
nulo, para que las dos cifras se puedan poner una al lado de la otra.

    hermana   rasgos del enunciado de Lean   -> disponibles en el paso 2
    ESTA      rasgos de la consulta          -> disponibles en el paso 1

LAS CUATRO COLUMNAS, TODAS OFRECIENDO K NOMBRES
-----------------------------------------------
    nulo         los K lemas más frecuentes, sin mirar la consulta
    n-gramas     TF-IDF de caracteres sobre el texto de la consulta
    ESTRUCTURA   los rasgos del árbol: relación principal, tipos, operadores,
                 conectivas, profundidad, simetría
    las dos      unidas

TODAS OFRECEN EXACTAMENTE K. Comparar cobertura entre configuraciones que
ofrecen distinto número de nombres no mide nada: quien ofrece más, cubre más.

EL NULO AQUI ES DURISIMO. `sq_nonneg` aparece en 16 719 de las 23 243 pruebas
—el 72 %—, así que ofrecer los seis de siempre ya acierta muchísimo. Esa es
justamente la razón de ponerlo: sin él, cualquier número parece bueno.

LO QUE ESTA MEDIDA NO DICE. Los lemas vienen de pruebas de LeanWorkbook, que
son sobre todo desigualdades de concurso. Que la estructura ayude aquí no dice
que ayude en topología algebraica, donde ni hay `≥` ni hay `√`.
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

from nucleo.sintaxis.rasgos import rasgos_de_consulta

DATOS = RAIZ / "data" / "banco_lemas.jsonl"
SALIDA = RAIZ / "data" / "sintaxis_de_consulta_contra_lemas.json"

#: Cuántos nombres ofrece cada configuración. El mismo que la hermana, para
#: que las dos tablas se lean juntas.
K = 6

#: Un lema con menos de esto no se puede aprender ni evaluar: aparecería una
#: vez en test y ninguna en train, o al revés.
MINIMO_EJEMPLOS = 30


def main(a) -> int:
    import numpy as np
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.multiclass import OneVsRestClassifier
    from sklearn.preprocessing import MultiLabelBinarizer
    from scipy.sparse import hstack

    filas = [json.loads(l) for l in io.open(a.datos, encoding="utf-8")]
    filas = [d for d in filas if (d.get("nl") or "").strip()]
    cuenta = collections.Counter(x for d in filas for x in d["lemas"])
    aprendibles = {l for l, n in cuenta.items() if n >= a.minimo}
    filas = [d for d in filas if set(d["lemas"]) & aprendibles]
    print("%d consultas · %d lemas con >= %d ejemplos (de %d)"
          % (len(filas), len(aprendibles), a.minimo, len(cuenta)))

    corte = int(len(filas) * 0.8)
    tr, te = filas[:corte], filas[corte:]
    Ytr = [sorted(set(d["lemas"]) & aprendibles) for d in tr]
    oro = [set(d["lemas"]) & aprendibles for d in te]
    print("train %d · test %d" % (len(tr), len(te)))

    mlb = MultiLabelBinarizer().fit(Ytr)
    Y = mlb.transform(Ytr)
    clases = np.array(mlb.classes_)

    def cobertura(pred):
        """De lo que hacía falta, cuánto se ofreció; y en cuántas acertó algo."""
        num = sum(len(p & g) for p, g in zip(pred, oro))
        den = sum(len(g) for g in oro)
        alg = sum(1 for p, g in zip(pred, oro) if p & g)
        return 100 * num / den, 100 * alg / len(oro)

    texto = lambda F: [d["nl"] for d in F]                      # noqa: E731
    res: dict = {}

    # ── el nulo ────────────────────────────────────────────────────────────
    top = {l for l, _ in collections.Counter(
        x for d in tr for x in d["lemas"] if x in aprendibles).most_common(a.k)}
    res["nulo"] = cobertura([top] * len(te))
    guardadas: dict = {"nulo": [top] * len(te)}
    print("\nnulo = %s" % ", ".join(sorted(top)))

    def entrena(Xtr, Xte, etiqueta):
        m = OneVsRestClassifier(
            LogisticRegression(max_iter=1000, C=1.0), n_jobs=-1).fit(Xtr, Y)
        d = m.decision_function(Xte)
        pred = [set(clases[fila.argsort()[::-1][:a.k]]) for fila in d]
        guardadas[etiqueta] = pred
        res[etiqueta] = cobertura(pred)

    vN = TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 4), min_df=3,
                         max_features=40000)
    Ntr = vN.fit_transform(texto(tr))
    Nte = vN.transform(texto(te))
    entrena(Ntr, Nte, "n-gramas")

    print("calculando el árbol de %d consultas..." % len(filas))
    vE = DictVectorizer(sparse=True)
    Etr = vE.fit_transform([rasgos_de_consulta(d["nl"]) for d in tr])
    Ete = vE.transform([rasgos_de_consulta(d["nl"]) for d in te])
    entrena(Etr, Ete, "ESTRUCTURA")

    entrena(hstack([Ntr, Etr]).tocsr(), hstack([Nte, Ete]).tocsr(), "las dos")

    print("\n  rasgos de estructura: %d   ·   n-gramas: %d   ·   K = %d"
          % (Etr.shape[1], Ntr.shape[1], a.k))
    print("\n  %-14s %12s %16s" % ("", "cobertura", "acierta alguno"))
    for k in ("nulo", "n-gramas", "ESTRUCTURA", "las dos"):
        print("  %-14s %10.1f %% %14.1f %%" % (k, res[k][0], res[k][1]))
    # ── ¿la diferencia se distingue del ruido? ─────────────────────────────
    # Un «+0,8 puntos» puede ser una mejora o puede ser cómo cayó el reparto.
    # Se remuestrean las consultas de test —EMPAREJADAS, las mismas para las
    # dos configuraciones— y se mira si el intervalo del 95 % cruza el cero.
    # Sin esto, «suma» y «no suma» se escriben igual.
    rng = np.random.default_rng(20260904)
    n_te = len(oro)

    def diferencia(pa, pb, idx):
        na = sum(len(pa[i] & oro[i]) for i in idx)
        nb = sum(len(pb[i] & oro[i]) for i in idx)
        den = sum(len(oro[i]) for i in idx)
        return 100 * (na - nb) / max(1, den)

    intervalos = {}
    for etiqueta, contra in (("ESTRUCTURA", "nulo"),
                             ("ESTRUCTURA", "n-gramas"),
                             ("las dos", "n-gramas")):
        muestras = [diferencia(guardadas[etiqueta], guardadas[contra],
                               rng.integers(0, n_te, n_te))
                    for _ in range(a.remuestreos)]
        lo, hi = np.percentile(muestras, [2.5, 97.5])
        intervalos["%s - %s" % (etiqueta, contra)] = [round(float(lo), 2),
                                                      round(float(hi), 2)]

    print()
    for k, (lo, hi) in intervalos.items():
        izq, der = k.split(" - ")
        obs = res[izq][0] - res[der][0]
        veredicto = ("SI" if lo > 0 else
                     "NO, es peor" if hi < 0 else "no se distingue del ruido")
        print("  %-26s %+6.1f  IC95 [%+.1f, %+.1f]   %s"
              % (k, obs, lo, hi, veredicto))

    # ── ¿SON COMPLEMENTARIAS? El promedio no lo puede decir ────────────────
    #
    # «Las dos suman +0,8» es una media sobre 22 117 consultas, y una media
    # esconde el caso que importa: aquél en que la prosa da poco y lo que
    # cierra el recorrido es la NOTACION. Para verlo hay que partir el test
    # por lo bien que le va al lado léxico y mirar dentro de cada mitad.
    #
    # Dos cortes, y los dos hacen falta:
    #
    #   LA TABLA 2x2 mide COMPLEMENTARIEDAD sin condicionar nada: para cada
    #   consulta, ¿acertó algo el léxico? ¿y la estructura? La celda «sólo
    #   estructura» es exactamente lo que un promedio no puede enseñar.
    #
    #   EL ESTRATO DE RESCATE mira sólo las consultas donde el léxico NO
    #   acertó nada, y pregunta cuántas rescata la estructura y con qué
    #   precisión. Lo primero es cobertura —lo que el léxico no alcanza—; lo
    #   segundo es que lo que añade no sea ruido. Sin las dos mitades el
    #   número no dice nada: rescatar mucho ofreciendo basura no es rescatar.
    def acierta(pred):
        return [bool(p & g) for p, g in zip(pred, oro)]

    aN = acierta(guardadas["n-gramas"])
    aE = acierta(guardadas["ESTRUCTURA"])

    celdas = {
        "las dos aciertan": sum(1 for x, y in zip(aN, aE) if x and y),
        "solo n-gramas": sum(1 for x, y in zip(aN, aE) if x and not y),
        "SOLO ESTRUCTURA": sum(1 for x, y in zip(aN, aE) if y and not x),
        "ninguna": sum(1 for x, y in zip(aN, aE) if not x and not y),
    }
    print()
    print("  ¿SE SOLAPAN O SE COMPLEMENTAN? (acierta al menos un lema)")
    for k, v in celdas.items():
        print("      %-20s %5d   %5.1f %%" % (k, v, 100 * v / n_te))
    solo_e = celdas["SOLO ESTRUCTURA"]
    print("      -> la estructura llega a %d consultas que el lexico no toca"
          % solo_e)

    # el estrato donde el léxico se queda corto
    idx = [i for i in range(n_te) if not aN[i]]
    estrato = {}
    if idx:
        def cob(pred):
            num = sum(len(pred[i] & oro[i]) for i in idx)
            den = sum(len(oro[i]) for i in idx)
            alg = sum(1 for i in idx if pred[i] & oro[i])
            # precisión: de los K nombres ofrecidos, cuántos hacían falta
            prec = num / max(1, a.k * len(idx))
            return (100 * num / max(1, den), 100 * alg / len(idx), 100 * prec)

        print()
        print("  EL ESTRATO QUE IMPORTA: las %d consultas (%.1f %%) donde los"
              " n-gramas no aciertan NADA" % (len(idx), 100 * len(idx) / n_te))
        print("      %-14s %10s %14s %12s" % ("", "cobertura", "acierta alguno",
                                              "precision"))
        for k in ("nulo", "ESTRUCTURA", "las dos"):
            c, al, pr = cob(guardadas[k])
            estrato[k] = [round(c, 2), round(al, 2), round(pr, 2)]
            print("      %-14s %8.1f %% %12.1f %% %10.1f %%" % (k, c, al, pr))
        print("      (los n-gramas dan 0,0 % por construccion:"
              " asi se define el estrato)")

    pathlib.Path(a.salida).write_text(json.dumps({
        "consultas": len(filas), "lemas_aprendibles": len(aprendibles),
        "k": a.k, "minimo_ejemplos": a.minimo,
        "rasgos_estructura": int(Etr.shape[1]),
        "rasgos_ngramas": int(Ntr.shape[1]),
        "resultados": {k: [round(v[0], 2), round(v[1], 2)]
                       for k, v in res.items()},
        "ic95_diferencias": intervalos,
        "remuestreos": a.remuestreos,
        "complementariedad": celdas,
        "estrato_sin_lexico": {"n": len(idx), "resultados": estrato},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nescrito -> %s" % a.salida)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datos", default=str(DATOS))
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--k", type=int, default=K)
    ap.add_argument("--minimo", type=int, default=MINIMO_EJEMPLOS)
    ap.add_argument("--remuestreos", type=int, default=2000)
    raise SystemExit(main(ap.parse_args()))
