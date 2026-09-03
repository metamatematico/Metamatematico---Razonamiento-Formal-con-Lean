# -*- coding: utf-8 -*-
"""¿La FORMA del enunciado dice qué hechos hacen falta para probarlo?

POR QUE ESTE EXPERIMENTO. Lo que el sistema llamaba «sintaxis» no lo era: eran
n-gramas de 1 a 4 caracteres sobre el texto sin palabras
(`scripts/entrenar_reconocedor.py`). Una bolsa de fragmentos de símbolos no sabe
cuál es la relación principal del enunciado, ni si hay cuantificadores, ni qué
es hipótesis y qué es conclusión. Es estadística léxica sobre símbolos, no
estructura.

La relación sintaxis-semántica es la que sostiene toda la lógica matemática: una
fórmula es un objeto puramente simbólico, y su verdad se decide en una
interpretación. Aquí se puede medir sin metáforas, porque hay las dos mitades:

    enunciado en Lean   ->  la forma, un objeto sintáctico
    lemas que se usaron ->  lo que hizo falta en el universo matemático

23 243 pares en `data/banco_lemas.jsonl`, 809 lemas distintos.

QUE SE COMPARA, y todo contra el mismo modelo nulo:

    nulo         ofrecer siempre los k lemas más citados
    n-gramas     char_wb 1-4 sobre el enunciado entero (lo que hay hoy)
    ESTRUCTURA   la relación principal, los tipos, los operadores, la forma
                 de las hipótesis y la profundidad del árbol
    las dos      unidas

La pregunta que decide: ¿la estructura aporta algo que los n-gramas no tienen?
Si no, la sintaxis está ya cubierta por la bolsa de símbolos y no hay nada que
construir. Si sí, es una vía nueva y hay que decir cuánta.

    python scripts/sintaxis_contra_premisas.py
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

DATOS = "E:/Metamatematico/data/banco_lemas.jsonl"
SALIDA = "E:/Metamatematico/data/sintaxis_contra_premisas.json"

#: cuántos lemas se ofrecen por enunciado. Seis es lo que caben en el prompt
#: sin desplazar al resto del contexto, y es el mismo tope que usa
#: `_nombres_mathlib` para el vocabulario del grafo.
K = 6

#: se aprenden sólo los lemas con suficientes ejemplos: por debajo, el modelo
#: memoriza en vez de generalizar y la medición se vuelve optimista
MINIMO_EJEMPLOS = 30


# ── la sintaxis, de verdad ────────────────────────────────────────────────
#
# Un enunciado de Lean tiene forma: `(binders) (hipótesis) : conclusión`. Lo que
# sigue extrae ESA estructura, no los caracteres que la componen.

RELACIONES = ["≥", "≤", ">", "<", "≠", "=", "∣", "∈", "⊆", "↔", "→"]
TIPOS = ["ℝ", "ℕ", "ℤ", "ℚ", "ℂ", "Finset", "Set", "Matrix", "Polynomial"]
OPERADORES = ["^", "√", "∑", "∏", "∫", "!", "%", "⌊", "|", "/", "*", "+", "-"]
CONECTIVAS = ["∧", "∨", "¬", "∀", "∃"]


def parte_en_dos(enunciado: str):
    """Separa hipótesis de conclusión por el ÚLTIMO `:` a profundidad cero.

    No vale partir por el primero: `(a b : ℝ)` ya trae uno dentro. La
    conclusión es lo que queda tras cerrar todos los binders, y esa es
    exactamente la distinción hipótesis/tesis que la lógica hace.
    """
    prof = corte = 0
    for i, c in enumerate(enunciado):
        if c in "([{":
            prof += 1
        elif c in ")]}":
            prof -= 1
        elif c == ":" and prof == 0:
            corte = i
    if not corte:
        return "", enunciado
    return enunciado[:corte], enunciado[corte + 1:]


def rasgos(enunciado: str) -> dict:
    """La estructura del enunciado, como diccionario de rasgos."""
    hip, con = parte_en_dos(enunciado)
    f = {}

    # LA RELACIÓN PRINCIPAL de la conclusión. Es el rasgo más informativo que
    # hay: una desigualdad y una igualdad no se prueban con lo mismo.
    f["rel=ninguna"] = 1
    for r in RELACIONES:
        if r in con:
            f["rel=%s" % r] = 1
            f["rel=ninguna"] = 0
            break

    for r in RELACIONES:
        f["con_tiene_%s" % r] = int(r in con)
        f["hip_tiene_%s" % r] = int(r in hip)
    for t in TIPOS:
        f["tipo_%s" % t] = int(t in enunciado)
    for o in OPERADORES:
        f["op_%s" % o] = int(o in con)
    for c in CONECTIVAS:
        f["conec_%s" % c] = int(c in enunciado)

    # LA FORMA, no su contenido
    f["n_binders"] = enunciado.count("(") + enunciado.count("{")
    f["n_hipotesis"] = len(re.findall(r"h[₀-₉0-9']*\s*:", hip))
    f["n_variables"] = len(set(re.findall(r"\b[a-z]\b", enunciado)))
    f["prof_max"] = _profundidad(con)
    f["largo_con"] = min(len(con) // 10, 20)
    f["hay_hipotesis"] = int(bool(hip.strip()))
    # simetría: `a + b + c` frente a `a + 2*b`. Una desigualdad simétrica se
    # ataca distinto que una que no lo es.
    f["simetrica"] = int(_simetrica(con))
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


def _simetrica(con: str) -> bool:
    """¿Las variables aparecen el mismo número de veces?"""
    v = collections.Counter(re.findall(r"\b[a-z]\b", con))
    return len(v) > 1 and len(set(v.values())) == 1


def main(a):
    import numpy as np
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.multiclass import OneVsRestClassifier
    from sklearn.preprocessing import MultiLabelBinarizer
    from scipy.sparse import hstack

    filas = [json.loads(l) for l in io.open(DATOS, encoding="utf-8")]
    cuenta = collections.Counter(x for d in filas for x in d["lemas"])
    aprendibles = {l for l, n in cuenta.items() if n >= MINIMO_EJEMPLOS}
    filas = [d for d in filas if set(d["lemas"]) & aprendibles]
    print("%d enunciados · %d lemas con >= %d ejemplos (de %d)"
          % (len(filas), len(aprendibles), MINIMO_EJEMPLOS, len(cuenta)))

    corte = int(len(filas) * 0.8)
    tr, te = filas[:corte], filas[corte:]
    Ytr = [sorted(set(d["lemas"]) & aprendibles) for d in tr]
    oro = [set(d["lemas"]) & aprendibles for d in te]
    print("train %d · test %d\n" % (len(tr), len(te)))

    mlb = MultiLabelBinarizer().fit(Ytr)
    Y = mlb.transform(Ytr)
    clases = np.array(mlb.classes_)

    def cobertura(pred):
        """De lo que hacía falta, cuánto se ofreció."""
        num = sum(len(p & g) for p, g in zip(pred, oro))
        den = sum(len(g) for g in oro)
        alg = sum(1 for p, g in zip(pred, oro) if p & g)
        return 100 * num / den, 100 * alg / len(oro)

    filas_txt = lambda F: [d["enunciado"] for d in F]           # noqa: E731

    # ── modelo nulo ────────────────────────────────────────────────────────
    top = {l for l, _ in collections.Counter(
        x for d in tr for x in d["lemas"] if x in aprendibles).most_common(K)}
    res = {}
    res["nulo"] = cobertura([top] * len(te))

    def entrena(Xtr, Xte, etiqueta):
        m = OneVsRestClassifier(
            LogisticRegression(max_iter=1000, C=1.0), n_jobs=-1).fit(Xtr, Y)
        d = m.decision_function(Xte)
        pred = [set(clases[fila.argsort()[::-1][:K]]) for fila in d]
        res[etiqueta] = cobertura(pred)
        return d

    vN = TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 4), min_df=3,
                         max_features=40000)
    Ntr = vN.fit_transform(filas_txt(tr))
    Nte = vN.transform(filas_txt(te))
    entrena(Ntr, Nte, "n-gramas")

    vE = DictVectorizer(sparse=True)
    Etr = vE.fit_transform([rasgos(d["enunciado"]) for d in tr])
    Ete = vE.transform([rasgos(d["enunciado"]) for d in te])
    entrena(Etr, Ete, "ESTRUCTURA")
    print("  rasgos de estructura: %d" % Etr.shape[1])

    entrena(hstack([Ntr, Etr]).tocsr(), hstack([Nte, Ete]).tocsr(), "las dos")

    print("\n  %-14s %12s %14s" % ("", "cobertura", "acierta alguno"))
    for k in ("nulo", "n-gramas", "ESTRUCTURA", "las dos"):
        print("  %-14s %10.1f %% %12.1f %%" % (k, res[k][0], res[k][1]))

    io.open(SALIDA, "w", encoding="utf-8").write(json.dumps({
        "enunciados": len(filas), "lemas_aprendibles": len(aprendibles),
        "k": K, "minimo_ejemplos": MINIMO_EJEMPLOS,
        "rasgos_estructura": int(Etr.shape[1]),
        "resultados": {k: [round(v[0], 2), round(v[1], 2)]
                       for k, v in res.items()},
    }, ensure_ascii=False, indent=1))
    print("\n  -> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sys.exit(main(ap.parse_args()))
