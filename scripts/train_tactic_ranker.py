"""
Entrena el rankeador de tacticas con datos supervisados reales.

POR QUE
-------
El GNN se entreno con etiqueta CONSTANTE (`todo problema -> ASSIST`), asi que
aprendio la funcion constante: devuelve ASSIST para cualquier entrada, incluido
"Hola, como estas". CR_tac lo detecta degenerado y lo ignora. Y el
GNNTacticRanker, que ordena la cascada por similitud coseno entre el embedding
del goal y los de las tacticas, da cosenos de 0,01-0,09 —practicamente
ortogonales— porque esos embeddings nunca vieron una senal discriminativa.

LeanWorkbook trae la senal que faltaba:

    state_before  ->  tactic       (que tactica cierra ESTE estado de prueba)

Es un objetivo con significado, no una constante.

METODO
------
TF-IDF sobre n-gramas de caracteres del estado de prueba + regresion logistica
multinomial. Elegido a proposito frente a una red: con ~7k ejemplos es mas
fuerte, entrena en segundos, da probabilidades calibradas —que es justo lo que
hace falta para RANKEAR la cascada— y permite auditar que mira.

HONESTIDAD DE LA METRICA
------------------------
La distribucion esta muy sesgada: nlinarith es el 45,7% de los ejemplos. Un
modelo que responda siempre "nlinarith" acierta el 45,7%. Por eso el script
reporta SIEMPRE la linea base de clase mayoritaria junto a la accuracy: una
cifra sin esa referencia no dice nada. Es el error que hizo vacuo el
"100% / 100% / 100%" del entrenamiento anterior.

USO
---
    python scripts/train_tactic_ranker.py [--min-por-clase 40] [--dry-run]
"""
from __future__ import annotations

import argparse
import collections
import json
import pickle
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = Path(r"E:\MetamatematicoDataSet\LeanWorkbook")
SALIDA = RAIZ / "data" / "tactic_ranker.pkl"
INFORME = RAIZ / "data" / "tactic_ranker_report.json"

#: Vocabulario objetivo. Amplia SOLVER_CASCADE con las tacticas que LeanWorkbook
#: demuestra frecuentes y que la cascada no tenia: norm_num (1.142 usos),
#: field_simp (1.306) y ring_nf (447). Ignorarlas dejaba fuera un 15% de la
#: senal disponible y, sobre todo, dejaba fuera solvers utiles.
VOCABULARIO = [
    "rfl", "simp", "norm_num", "ring", "ring_nf", "field_simp",
    "linarith", "nlinarith", "omega", "aesop",
]

_RE_CABEZA = re.compile(r"[a-zA-Z_][a-zA-Z0-9_?']*")


def _tactica_principal(tactic: str) -> str | None:
    """Cabeza de la tactica: `nlinarith [sq_nonneg x]` -> `nlinarith`."""
    m = _RE_CABEZA.match((tactic or "").strip())
    if not m:
        return None
    cab = m.group(0)
    return cab if cab in VOCABULARIO else None


def cargar(min_por_clase: int) -> tuple[list[str], list[str], dict]:
    from datasets import load_from_disk

    ds = load_from_disk(str(ORIGEN))
    X, y = [], []
    for fila in ds:
        if fila.get("status") != "proved":
            continue
        estado = (fila.get("state_before") or "").strip()
        tac = _tactica_principal(fila.get("tactic") or "")
        if not estado or not tac:
            continue
        # `no goals` no es un estado sobre el que decidir nada.
        if estado.lower().startswith("no goals"):
            continue
        X.append(estado)
        y.append(tac)

    # Clases con muy pocos ejemplos no se pueden ni entrenar ni evaluar.
    cuenta = collections.Counter(y)
    validas = {k for k, v in cuenta.items() if v >= min_por_clase}
    pares = [(a, b) for a, b in zip(X, y) if b in validas]
    X, y = [a for a, _ in pares], [b for _, b in pares]

    return X, y, dict(collections.Counter(y).most_common())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-por-clase", type=int, default=40)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not ORIGEN.exists():
        print(f"No encuentro el dataset en {ORIGEN}")
        return 1

    print("Cargando LeanWorkbook...")
    X, y, dist = cargar(args.min_por_clase)
    print(f"\nEjemplos utilizables: {len(X):,}  ·  clases: {len(dist)}")
    for k, v in dist.items():
        print(f"   {k:12s} {v:5,}  ({100*v/len(y):.1f}%)")

    mayoritaria = max(dist.values()) / len(y)
    print(f"\nLINEA BASE (clase mayoritaria): {mayoritaria:.1%}")
    print("   Cualquier accuracy por debajo de esto es peor que responder")
    print("   siempre lo mismo. La cifra sola no significa nada.")

    if args.dry_run:
        print("\n--dry-run: no se entrena")
        return 0

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import classification_report, top_k_accuracy_score
    import numpy as np

    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.2, random_state=0, stratify=y
    )
    print(f"\ntrain={len(Xtr):,}  test={len(Xte):,}")

    modelo = Pipeline([
        # N-gramas de caracteres: los estados de prueba son mitad simbolos
        # (⊢ ℝ ≤ ∑) y mitad identificadores. Partir por palabras pierde
        # justamente los simbolos, que son la senal mas discriminativa.
        ("tfidf", TfidfVectorizer(
            analyzer="char_wb", ngram_range=(2, 5),
            min_df=3, max_features=60000, sublinear_tf=True,
        )),
        ("clf", LogisticRegression(
            max_iter=2000, C=4.0, class_weight="balanced", n_jobs=-1,
        )),
    ])
    print("Entrenando...")
    modelo.fit(Xtr, ytr)

    acc = modelo.score(Xte, yte)
    proba = modelo.predict_proba(Xte)
    clases = list(modelo.classes_)
    top3 = top_k_accuracy_score(yte, proba, k=3, labels=clases)

    print(f"\n{'='*54}")
    print(f"  accuracy            : {acc:.1%}")
    print(f"  linea base mayoritaria: {mayoritaria:.1%}")
    print(f"  mejora sobre la base : {acc - mayoritaria:+.1%}")
    print(f"  top-3 accuracy       : {top3:.1%}   <- lo que importa para RANKEAR")
    print(f"{'='*54}")
    print("\n" + classification_report(yte, modelo.predict(Xte), zero_division=0))

    if acc <= mayoritaria:
        print("AVISO: el modelo no supera a la clase mayoritaria. NO se guarda.")
        return 2

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "wb") as f:
        pickle.dump({"modelo": modelo, "clases": clases}, f)
    informe = {
        "n_train": len(Xtr), "n_test": len(Xte),
        "accuracy": round(acc, 4),
        "baseline_mayoritaria": round(mayoritaria, 4),
        "mejora": round(acc - mayoritaria, 4),
        "top3_accuracy": round(float(top3), 4),
        "distribucion": dist,
        "vocabulario": clases,
    }
    INFORME.write_text(json.dumps(informe, ensure_ascii=False, indent=2),
                       encoding="utf-8")
    print(f"\nModelo -> {SALIDA}  ({SALIDA.stat().st_size // 1024} KB)")
    print(f"Informe -> {INFORME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
