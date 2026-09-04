# -*- coding: utf-8 -*-
"""El predictor de tácticas, medido EN EL BANCO DE LA CASCADA.

POR QUE ESTE SCRIPT. `estado_contra_tactica.py` mide 4,64 -> 1,90 intentos, y
`efecto_orden_cascada.py` mide 2,59 -> 1,29 en el suyo. Son bancos distintos:
otro corpus, 22 tácticas frente a 12, otra tarea. Comparar esas dos cifras entre
sí no dice nada. Aquí se lleva el predictor AL banco de la cascada, que es la
única comparación que decide si se cablea.

Y AL HACERLO APARECE ALGO QUE LA MEDICION ORIGINAL NO PREGUNTO. En los 1 600
casos de Mathlib, `simp` cierra el 95,8 %:

    simp      1532  (95,8 %)
    aesop       34  ( 2,1 %)
    rfl         23  ( 1,4 %)
    norm_num     5  ( 0,3 %)
    linarith     5  ( 0,3 %)
    ring         1  ( 0,1 %)

Con esa distribución hay un modelo nulo evidente —probar `simp` primero y el
resto por frecuencia— y `efecto_orden_cascada.py` NO LO TIENE. Su «2,4x de
mejora» compara dos reglas entre sí, ninguna de las dos contra el suelo.

Este script mide cuatro órdenes sobre el MISMO conjunto de prueba:

    viejo    el área primero, luego los patrones del objetivo
    regla    los patrones primero, luego el área  (lo que hay hoy)
    NULO     `simp` primero, el resto por frecuencia del entrenamiento
    modelo   ordenado por el clasificador de forma + n-gramas

La métrica es la de la cascada: POSICIÓN de la táctica que cierra, es decir
cuántas invocaciones de Lean hacen falta antes de acertar.

EL REPARTO ES HONESTO: el modelo se entrena en el 80 % y las CUATRO órdenes se
miden en el 20 % restante. La regla no se entrena, pero se construyó mirando
mediciones sobre este mismo corpus, así que su 1,29 publicado es en parte una
cifra dentro de muestra; medirla aquí en la partición de prueba es lo justo.

    python scripts/modelo_en_la_cascada.py
"""
import argparse
import collections
import io
import json
import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SALIDA = "E:/Metamatematico/data/modelo_en_la_cascada.json"
SEMILLA = 20260901


def main(a):
    import numpy as np
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import LinearSVC
    from scipy.sparse import hstack

    from nucleo.lean.solver_cascade import GoalAnalyzer
    from scripts.efecto_orden_cascada import (SOLVERS, casos, orden_nuevo,
                                              orden_viejo)
    from scripts.sintaxis_contra_premisas import rasgos

    todos = casos()
    if not todos:
        print("  ATENCIÓN: ningún caso — ¿está Mathlib en .lake/packages?")
        return 1
    random.seed(SEMILLA)
    random.shuffle(todos)
    corte = int(len(todos) * 0.8)
    tr, te = todos[:corte], todos[corte:]
    print("%d casos de Mathlib · %d tácticas en la cascada" % (len(todos), len(SOLVERS)))
    print("train %d · test %d (semilla %d)\n" % (len(tr), len(te), SEMILLA))

    dist = collections.Counter(t for _, _, t in todos)
    print("la táctica que cierra:")
    for k, v in dist.most_common():
        print("   %-12s %5d  (%4.1f %%)" % (k, v, 100 * v / len(todos)))

    # ── EL NULO, que la medición original no tenía ─────────────────────────
    # Ordenar por frecuencia del entrenamiento. Con `simp` cerrando el 95,8 %
    # esto es «prueba simp primero», que es lo mínimo que hay que batir.
    frec = collections.Counter(t for _, _, t in tr)
    nulo = [t for t, _ in frec.most_common()]
    nulo += [s for s in SOLVERS if s not in nulo]

    # ── EL MODELO ──────────────────────────────────────────────────────────
    Xtr = [e for e, _, _ in tr]
    ytr = np.array([t for _, _, t in tr])
    Xte = [e for e, _, _ in te]
    vN = TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 4), min_df=2,
                         max_features=40000)
    Ntr, Nte = vN.fit_transform(Xtr), vN.transform(Xte)
    vE = DictVectorizer(sparse=True)
    Etr = vE.fit_transform([rasgos(x) for x in Xtr])
    Ete = vE.transform([rasgos(x) for x in Xte])
    mo = LinearSVC(max_iter=5000).fit(hstack([Ntr, Etr]).tocsr(), ytr)
    D = mo.decision_function(hstack([Nte, Ete]).tocsr())
    if D.ndim == 1:                       # dos clases: sklearn da un vector
        D = np.column_stack([-D, D])
    clases = list(mo.classes_)

    def orden_modelo(i):
        """La cascada ordenada por el clasificador, sin perder ninguna."""
        pref = [clases[j] for j in np.argsort(-D[i])]
        return pref + [s for s in SOLVERS if s not in pref]

    an = GoalAnalyzer()
    pos = collections.defaultdict(list)
    for i, (enun, area, tac) in enumerate(te):
        pos["viejo"].append(orden_viejo(an, enun, area).index(tac) + 1)
        pos["regla"].append(orden_nuevo(an, enun, area).index(tac) + 1)
        pos["NULO"].append(nulo.index(tac) + 1)
        pos["modelo"].append(orden_modelo(i).index(tac) + 1)

    print("\n=== POSICIÓN DE LA TÁCTICA QUE CIERRA, en el 20 % de prueba ===")
    print("    (invocaciones de Lean antes de acertar)\n")
    print("  %-10s %8s %12s %11s" % ("", "media", "1er intento", "en los 3"))
    res = {}
    for k in ("viejo", "regla", "NULO", "modelo"):
        v = np.array(pos[k])
        res[k] = [round(float(v.mean()), 3),
                  round(100 * float((v == 1).mean()), 1),
                  round(100 * float((v <= 3).mean()), 1)]
        print("  %-10s %8.2f %10.1f %% %9.1f %%" % (k, *res[k]))

    print("\n  para referencia, lo publicado sobre TODO el corpus:")
    print("    orden viejo 2,59 · orden nuevo 1,29 · sin modelo nulo")

    mejor = min(res, key=lambda k: res[k][0])
    print("\n  el mejor aquí es: %s (%.2f)" % (mejor, res[mejor][0]))
    if res["modelo"][0] >= res["NULO"][0]:
        print("  EL MODELO NO BATE AL NULO. No hay nada que cablear.")
    if res["regla"][0] >= res["NULO"][0]:
        print("  LA REGLA DE HOY TAMPOCO BATE AL NULO.")

    io.open(SALIDA, "w", encoding="utf-8").write(json.dumps({
        "casos": len(todos), "train": len(tr), "test": len(te),
        "semilla": SEMILLA, "tacticas": len(SOLVERS),
        "distribucion": dict(dist.most_common()),
        "columnas": ["posicion_media", "1er_intento_pct", "en_los_3_pct"],
        "resultados": res,
    }, ensure_ascii=False, indent=1))
    print("\n  -> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sys.exit(main(ap.parse_args()))
