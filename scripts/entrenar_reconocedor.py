# -*- coding: utf-8 -*-
"""Reconocer el área de un enunciado por su FORMA, no sólo por sus palabras.

POR QUE. El emparejador del grafo compara la consulta con 3 839 palabras clave
escritas a mano. `(a+b)^2 = a^2+2ab+b^2` no contiene NI UNA de ellas, y 15 de 24
consultas reales no activan nada. Toda la señal de ese enunciado está en su
forma —un cuadrado de un binomio— y se estaba tirando entera.

Medido aquí, sobre los 7 temas reales de MATH:

    modelo nulo (la clase mayoritaria)     23,8 %
    sólo símbolos, sin una sola palabra    60,4 %
    sólo palabras                          73,9 %
    al menos uno de los dos acierta        84,1 %   <- techo de combinarlos

La síntaxis rescata el 39 % de los casos donde las palabras fallan. Es una ruta
COMPLEMENTARIA, no redundante. Y tiene algo que las palabras no pueden tener:
los símbolos no llevan idioma. El corpus es inglés y las consultas del sistema
son español; `(a+b)^2` se clasifica igual en los dos.

POR QUE NO ES UN TRANSFORMER. Se probó, y está medido en
`data/emparejador_semantico.json`: un bi-encoder multilingüe de estantería
acertaba el área en el 11,9 % de los casos y arrastraba cualquier problema hacia
`cic` y `ordinals`. Lo que faltaba no era capacidad sino supervisión, y la
supervisión que hay —6 000 problemas etiquetados— sostiene un modelo lineal, no
uno de 118 M de parámetros. Cuando el retriever de lemas dé pares de
entrenamiento de verdad, este archivo es el sitio donde cambiarlo.

EL PESO SE ELIGE EN VALIDACIÓN, no en test. La primera versión de esta medición
probó w=0,3 y w=0,5 directamente sobre el test y se quedó con el mejor: eso es
elegir mirando la respuesta.

    python scripts/entrenar_reconocedor.py
"""
import argparse
import collections
import io
import json
import os
import pickle
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATOS = "E:/datadeentrenamientovalidacion_test/"
SALIDA = "E:/Metamatematico/data/reconocedor_area.pkl"
INFORME = "E:/Metamatematico/data/reconocedor_area.json"

#: sólo las filas de MATH: son las únicas con TEMA real. Las de numina y gsm8k
#: van todas etiquetadas «algebra», y con ellas dentro el modelo nulo sube al
#: 79,4 % — un artefacto que hizo parecer imposible un problema que no lo es.
PREFIJO = "math_"

PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")


def solo_simbolos(t):
    """Se van las palabras. Queda la notación, que no tiene idioma."""
    return PALABRA.sub(" ", t)


def solo_palabras(t):
    return " ".join(PALABRA.findall(t))


def carga(nombre):
    X, y = [], []
    for linea in io.open(DATOS + nombre, encoding="utf-8"):
        d = json.loads(linea)
        if d.get("source", "").startswith(PREFIJO):
            X.append(d["problem"])
            y.append(d["source"])
    return X, y


def normaliza(d):
    """Puntuaciones comparables entre los dos modelos."""
    return (d - d.mean(1, keepdims=True)) / (d.std(1, keepdims=True) + 1e-9)


def main(a):
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import LinearSVC
    from sklearn.metrics import accuracy_score, balanced_accuracy_score

    Xtr, ytr = carga("all_train.jsonl")
    Xva, yva = carga("all_val.jsonl")
    Xte, yte = carga("all_test.jsonl")
    print("train %d · val %d · test %d · %d temas"
          % (len(Xtr), len(Xva), len(Xte), len(set(ytr))))

    mayor = collections.Counter(ytr).most_common(1)[0][0]
    nulo = sum(1 for t in yte if t == mayor) / len(yte)
    print("  modelo nulo (siempre «%s»)      %5.1f %%\n" % (mayor, 100 * nulo))

    def entrena(f, **kw):
        v = TfidfVectorizer(**kw)
        A = v.fit_transform([f(x) for x in Xtr])
        m = LinearSVC(C=1.0, max_iter=5000).fit(A, ytr)
        d = lambda X: m.decision_function(v.transform([f(x) for x in X]))
        return v, m, d

    vS, mS, dS = entrena(solo_simbolos, analyzer="char_wb", ngram_range=(1, 4),
                         min_df=3, max_features=60000)
    vP, mP, dP = entrena(solo_palabras, ngram_range=(1, 2), min_df=3)
    cls = mP.classes_
    assert list(cls) == list(mS.classes_), "las clases no coinciden"

    dSva, dPva = normaliza(dS(Xva)), normaliza(dP(Xva))
    dSte, dPte = normaliza(dS(Xte)), normaliza(dP(Xte))

    print("  %-30s %-12s %s" % ("", "exactitud", "equilibrada"))
    for nom, p in (("sólo síntaxis", cls[dSte.argmax(1)]),
                   ("sólo palabras", cls[dPte.argmax(1)])):
        print("  %-30s %8.1f %% %10.1f %%"
              % (nom, 100*accuracy_score(yte, p), 100*balanced_accuracy_score(yte, p)))

    # EL PESO, EN VALIDACION
    pesos = [0.0, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5]
    marcas = [(w, accuracy_score(yva, cls[(dPva + w*dSva).argmax(1)])) for w in pesos]
    w = max(marcas, key=lambda t: t[1])[0]
    print("\n  peso elegido en validación: w=%.1f  %s"
          % (w, " ".join("%.1f:%.3f" % t for t in marcas)))

    p = cls[(dPte + w*dSte).argmax(1)]
    exa, equ = accuracy_score(yte, p), balanced_accuracy_score(yte, p)
    techo = ((cls[dSte.argmax(1)] == np.array(yte))
             | (cls[dPte.argmax(1)] == np.array(yte))).mean()
    print("  %-30s %8.1f %% %10.1f %%" % ("LAS DOS, w de validación", 100*exa, 100*equ))
    print("  %-30s %8.1f %%" % ("techo (acierta alguno)", 100*techo))
    print("  %-30s %8.1f %%" % ("modelo nulo", 100*nulo))

    okS = cls[dSte.argmax(1)] == np.array(yte)
    okP = cls[dPte.argmax(1)] == np.array(yte)
    rescate = (okS & ~okP).sum() / max((~okP).sum(), 1)
    print("\n  la síntaxis rescata el %.1f %% de lo que las palabras fallan"
          % (100 * rescate))

    if a.guardar:
        with io.open(SALIDA, "wb") as fh:
            pickle.dump({"vS": vS, "mS": mS, "vP": vP, "mP": mP,
                         "w": w, "clases": list(cls)}, fh)
        print("\n  -> %s (%.1f MB)" % (SALIDA, os.path.getsize(SALIDA)/1e6))
    io.open(INFORME, "w", encoding="utf-8").write(json.dumps({
        "temas": sorted(set(ytr)), "train": len(Xtr), "test": len(Xte),
        "nulo": round(nulo, 4), "peso_validacion": w,
        "solo_sintaxis": round(accuracy_score(yte, cls[dSte.argmax(1)]), 4),
        "solo_palabras": round(accuracy_score(yte, cls[dPte.argmax(1)]), 4),
        "combinado": round(exa, 4), "combinado_equilibrado": round(equ, 4),
        "techo": round(float(techo), 4), "rescate_sintaxis": round(float(rescate), 4),
    }, ensure_ascii=False, indent=1))
    print("  -> %s" % INFORME)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", action="store_true", default=True)
    sys.exit(main(ap.parse_args()))
