# -*- coding: utf-8 -*-
"""¿El ESTADO DE PRUEBA dice qué táctica lo cierra?

ESTO ES LO QUE LA CASCADA DECIDE. El paso 5 del sistema prueba hasta 12 tácticas
en un orden fijo por área, y está medido en 2,59 -> 1,29 intentos
(`efecto_orden_cascada.py`): es el punto del grafo que mejor funciona. Pero el
orden es por ÁREA, no por objetivo — dos metas distintas del mismo problema
reciben la misma lista.

`LeanWorkbook` trae 25 214 transiciones etiquetadas y no se estaba usando
ninguna:

    state_before   el estado de prueba: hipótesis arriba, `⊢ objetivo` abajo
    tactic         la táctica que se aplicó
    state_after    lo que quedó; «no goals» si la cerró

De esas, 13 517 (53,6 %) CIERRAN el objetivo. Ese subconjunto es exactamente la
pregunta de la cascada: dado este objetivo, ¿qué táctica lo cierra?

LA DIFERENCIA CON `sintaxis_contra_tacticas.py`. Aquel predice la primera
táctica desde el ENUNCIADO inicial; éste predice desde el ESTADO, que es lo que
hay delante en cada paso, ya con las hipótesis introducidas y el objetivo
transformado. Y el problema es más duro: 76 tácticas con un nulo del 13,0 %,
frente a 25 con un nulo del 23,6 %.

TRES VIAS, contra el mismo nulo:

    nulo         la táctica mayoritaria
    n-gramas     char_wb 1-4 sobre el estado entero
    ESTRUCTURA   la relación del objetivo, los tipos, los operadores, cuántas
                 hipótesis hay y qué relación traen

NO ES COMPARABLE CON EL 1,29 DE LA CASCADA, y hay que decirlo. Ese numero sale
de `efecto_orden_cascada.py`: otro corpus (1 600 pruebas de Mathlib), otro
conjunto de tacticas (12, no 22) y otra tarea. Lo comparable es lo de dentro de
esta medicion: ordenar por el modelo frente a ordenar por frecuencia, que es lo
que la cascada hace hoy dentro de un area.

Para saber si esto MEJORA la cascada hay que medirlo en el banco de la cascada.
Todavia no esta hecho.

    python scripts/estado_contra_tactica.py
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

FUENTE = "E:/MetamatematicoDataSet/LeanWorkbook"
SALIDA = "E:/Metamatematico/data/estado_contra_tactica.json"
MINIMO = 50

IDENT = re.compile(r"[a-zA-Z_][\w'!?]*")

RELACIONES = ["≥", "≤", ">", "<", "≠", "=", "∣", "∈", "⊆", "↔", "→"]
TIPOS = ["ℝ", "ℕ", "ℤ", "ℚ", "ℂ", "Finset", "Set", "Matrix", "Polynomial"]
OPERADORES = ["^", "√", "∑", "∏", "∫", "!", "%", "⌊", "|", "/", "*", "+", "-"]
CONECTIVAS = ["∧", "∨", "¬", "∀", "∃"]


def parte_estado(estado: str):
    """(hipótesis, objetivo) de un estado de prueba de Lean.

    El corte es el `⊢`, que es la barra de deducción: encima está lo que se
    supone y debajo lo que hay que demostrar. Es la misma distinción que en un
    enunciado, pero ya con las hipótesis introducidas.
    """
    i = estado.find("⊢")
    if i < 0:
        return estado, ""
    return estado[:i], estado[i + 1:]


def rasgos_estado(estado: str) -> dict:
    """La estructura del estado de prueba, no sus caracteres."""
    hip, obj = parte_estado(estado)
    f = {}

    # LA RELACIÓN DEL OBJETIVO. Es el rasgo que más manda: una igualdad se
    # cierra con `ring`, una desigualdad con `nlinarith`, y eso no es una
    # opinión sino lo que hacen las 13 517 pruebas de este corpus.
    f["obj_rel=ninguna"] = 1
    for r in RELACIONES:
        if r in obj:
            f["obj_rel=%s" % r] = 1
            f["obj_rel=ninguna"] = 0
            break

    for r in RELACIONES:
        f["obj_%s" % r] = int(r in obj)
        f["hip_%s" % r] = int(r in hip)
    for t in TIPOS:
        f["tipo_%s" % t] = int(t in estado)
    for o in OPERADORES:
        f["op_%s" % o] = int(o in obj)
    for c in CONECTIVAS:
        f["obj_conec_%s" % c] = int(c in obj)
        f["hip_conec_%s" % c] = int(c in hip)

    lineas = [l for l in hip.split("\n") if l.strip()]
    f["n_hipotesis"] = min(len(lineas), 12)
    f["hay_hipotesis"] = int(bool(lineas))
    f["n_variables"] = min(len(set(re.findall(r"\b[a-z]\b", obj))), 8)
    f["prof_max"] = _profundidad(obj)
    f["largo_obj"] = min(len(obj) // 20, 15)
    f["obj_negado"] = int(obj.strip().startswith("¬"))
    f["obj_es_falso"] = int("False" in obj)
    f["simetrico"] = int(_simetrico(obj))
    return f


def _profundidad(s: str) -> int:
    prof = mx = 0
    for c in s:
        if c in "([{":
            prof += 1
            mx = max(mx, prof)
        elif c in ")]}":
            prof -= 1
    return min(mx, 8)


def _simetrico(obj: str) -> bool:
    v = collections.Counter(re.findall(r"\b[a-z]\b", obj))
    return len(v) > 1 and len(set(v.values())) == 1


def main(a):
    import numpy as np
    from datasets import load_from_disk
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import LinearSVC
    from sklearn.metrics import accuracy_score, balanced_accuracy_score
    from scipy.sparse import hstack

    d = load_from_disk(FUENTE)
    ds = d[list(d.keys())[0]] if hasattr(d, "keys") else d
    filas = []
    for r in ds:
        m = IDENT.match((r["tactic"] or "").strip())
        if not m or "⊢" not in (r["state_before"] or ""):
            continue
        filas.append((r["state_before"], m.group(0),
                      (r["state_after"] or "").strip() == "no goals"))
    print("%d transiciones · %d cierran el objetivo (%.1f %%)\n"
          % (len(filas), sum(1 for f in filas if f[2]),
             100 * sum(1 for f in filas if f[2]) / len(filas)))

    resultados = {}
    for etiqueta, sub in (("todas las transiciones", filas),
                          ("SOLO LAS QUE CIERRAN", [f for f in filas if f[2]])):
        X = [f[0] for f in sub]
        y = np.array([f[1] for f in sub])
        frec = collections.Counter(y)
        keep = np.array([frec[v] >= MINIMO for v in y])
        X = [x for x, k in zip(X, keep) if k]
        y = y[keep]
        n = int(len(X) * 0.8)
        Xtr, Xte, ytr, yte = X[:n], X[n:], y[:n], y[n:]
        clases = sorted(set(y))
        may = collections.Counter(ytr).most_common(1)[0][0]

        res = {"nulo": (100 * (yte == may).mean(), 100.0 / len(clases))}
        vN = TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 4), min_df=3,
                             max_features=40000)
        Ntr, Nte = vN.fit_transform(Xtr), vN.transform(Xte)
        vE = DictVectorizer(sparse=True)
        Etr = vE.fit_transform([rasgos_estado(x) for x in Xtr])
        Ete = vE.transform([rasgos_estado(x) for x in Xte])
        for et, A, B in (("n-gramas", Ntr, Nte), ("ESTRUCTURA", Etr, Ete),
                         ("las dos", hstack([Ntr, Etr]).tocsr(),
                          hstack([Nte, Ete]).tocsr())):
            p = LinearSVC(max_iter=3000).fit(A, ytr).predict(B)
            res[et] = (100 * accuracy_score(yte, p),
                       100 * balanced_accuracy_score(yte, p))

        print("=== %s ===" % etiqueta)
        print("  %d casos · %d tácticas con >= %d ejemplos · nulo «%s»"
              % (len(X), len(clases), MINIMO, may))
        print("  %-14s %11s %14s" % ("", "exactitud", "equilibrada"))
        for k in ("nulo", "n-gramas", "ESTRUCTURA", "las dos"):
            print("  %-14s %9.1f %% %12.1f %%" % (k, res[k][0], res[k][1]))
        print("  rasgos: n-gramas %d · estructura %d"
              % (Ntr.shape[1], Etr.shape[1]))

        # ── INTENTOS ESPERADOS, que es lo que la cascada paga ──────────────
        # Acertar a la primera es sólo una parte: lo que cuesta son las
        # llamadas a Lean que hacen falta hasta que una táctica cierra. Se
        # compara con el ORDEN FIJO POR FRECUENCIA, que es lo que la cascada
        # hace hoy dentro de un área: la misma lista para todos los objetivos.
        mo = LinearSVC(max_iter=3000).fit(hstack([Ntr, Etr]).tocsr(), ytr)
        D = mo.decision_function(hstack([Nte, Ete]).tocsr())
        fijo = [t for t, _ in collections.Counter(ytr).most_common()]
        pos_fijo = {t: i + 1 for i, t in enumerate(fijo)}
        rk_fijo = np.array([pos_fijo.get(t, len(fijo)) for t in yte])
        pos = {t: i for i, t in enumerate(mo.classes_)}
        orden = np.argsort(-D, axis=1)
        rk_mod = np.array([int(np.where(orden[i] == pos[t])[0][0]) + 1
                           for i, t in enumerate(yte)])
        print("  %-26s %7s %11s %10s"
              % ("", "media", "1er intento", "en los 3"))
        for et, rk in (("orden fijo por frecuencia", rk_fijo),
                       ("ORDENADO POR EL MODELO", rk_mod)):
            print("  %-26s %7.2f %9.1f %% %9.1f %%"
                  % (et, rk.mean(), 100 * (rk == 1).mean(),
                     100 * (rk <= 3).mean()))
        res["intentos_fijo"] = (float(rk_fijo.mean()), 0.0)
        res["intentos_modelo"] = (float(rk_mod.mean()), 0.0)
        print()

        resultados[etiqueta] = {
            "casos": len(X), "tacticas": len(clases), "mayoritaria": may,
            "rasgos_estructura": int(Etr.shape[1]),
            "resultados": {k: [round(v[0], 2), round(v[1], 2)]
                           for k, v in res.items()}}

    io.open(SALIDA, "w", encoding="utf-8").write(
        json.dumps(resultados, ensure_ascii=False, indent=1))
    print("  -> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sys.exit(main(ap.parse_args()))
