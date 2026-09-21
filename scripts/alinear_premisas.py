# -*- coding: utf-8 -*-
"""¿La fila i de los embeddings precalculados ES la premisa i? (D1 denso)

Los embeddings de `l3lab/lean-premises` (rama v4.29.0) son una matriz sin
nombres: 382 212 × 768. El nombre de cada fila sale de reconstruir el corpus
con el MISMO código que los calculó (`nucleo/lazo/terceros/`), en el mismo
orden. Si ese orden se tuerce —un fichero descartado, un filtro distinto—, el
buscador devuelve premisas equivocadas con toda la seguridad del mundo, y
nada falla. Así que se comprueba, y no por longitud sólo:

    1. LONGITUD    len(Corpus.premises) == filas de la matriz.
    2. CONTENIDO   se vuelven a codificar 64 premisas al azar (semilla 0) con
                   el modelo, y el coseno con SU fila tiene que ser ≥ 0,99; con
                   una fila desplazada daría el de dos premisas cualesquiera.

Si pasan las dos, se escribe `modelos/lean-premises-v4.29.0/premisas.jsonl`:
una línea por fila, con nombre, clase, si es proposición y módulo, para que el
proponente no tenga que reconstruir el corpus (minutos y ~5 GB) cada vez.

    python -m scripts.alinear_premisas
"""
from __future__ import annotations

import io
import json
import os
import random
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

DATOS = os.path.join(RAIZ, "modelos", "lean-premises-v4.29.0")
MODELO = os.path.join(RAIZ, "modelos", "premise-selection")
EMB = os.path.join(DATOS, "embeddings",
                   "all-distilroberta-v1-lr2e-4-bs256-nneg3-ml-ne2-v4.29.0.npy")
INDICE = os.path.join(DATOS, "premisas.jsonl")
MUESTRA, UMBRAL = 64, 0.99


def main():
    import logging
    import numpy as np
    logging.basicConfig(level=logging.WARNING)
    from nucleo.lazo.terceros.lean_premises_models import Corpus

    t0 = time.time()
    c = Corpus.from_ntp_toolkit(os.path.join(DATOS, "Mathlib"))
    e = np.load(EMB, mmap_mode="r")
    print("corpus %d premisas · embeddings %s · %.0f s"
          % (len(c.premises), e.shape, time.time() - t0), flush=True)
    if len(c.premises) != e.shape[0]:
        print("NO CASA LA LONGITUD: no se escribe el índice")
        return 1

    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(MODELO, device="cpu")
    idx = random.Random(0).sample(range(len(c.premises)), MUESTRA)
    v = m.encode([c.premises[i].to_string() for i in idx], normalize_embeddings=True)
    cos = [float(np.dot(v[k], e[i]) / np.linalg.norm(e[i])) for k, i in enumerate(idx)]
    # el mismo vector contra la fila VECINA: lo que daría un desplazamiento de uno
    vec = [float(np.dot(v[k], e[(i + 1) % e.shape[0]]) / np.linalg.norm(e[(i + 1) % e.shape[0]]))
           for k, i in enumerate(idx)]
    print("coseno con su fila: mín %.4f, mediana %.4f · con la vecina: mediana %.4f"
          % (min(cos), sorted(cos)[len(cos) // 2], sorted(vec)[len(vec) // 2]))
    if min(cos) < UMBRAL:
        print("NO CASA EL CONTENIDO: no se escribe el índice")
        return 1

    with io.open(INDICE, "w", encoding="utf-8") as f:
        for p in c.premises:
            f.write(json.dumps({"nombre": p.name, "clase": p.kind,
                                "prop": bool(p.is_prop), "modulo": p.module},
                               ensure_ascii=False) + "\n")
    print("ALINEADO · -> %s" % INDICE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
