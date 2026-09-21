# -*- coding: utf-8 -*-
"""Baja los encoders de Lean candidatos a D1 denso a `E:/Metamatematico/modelos/`.

Los tres de la propuesta (§6), sin elegir antes de medir:

    premise-selection  Zhu et al., ICLR 2026. DistilRoBERTa; los pesos que
                       enlaza su README. ~0,3 GB. Corre en esta máquina.
    LeanSearch-PS      un adaptador LoRA de 42 MB sobre e5-mistral-7b-instruct,
                       que también se baja (~14 GB).
    Lean Finder        ~7 000 millones de parámetros e índices de Mathlib
                       ya hechos, 27 GB.

LOS DOS GRANDES NO CORREN AQUÍ A VELOCIDAD ÚTIL, y se dice: con una RTX 3050
de 4,3 GB, codificar los 183 433 enunciados de Mathlib con un modelo de 7 B
llevaría días. Se bajan para tenerlos; se miden cuando haya una máquina que
pueda.

La carpeta está en .gitignore. Se reanuda si se corta: `snapshot_download` no
vuelve a bajar lo que ya está.

    python -m scripts.bajar_encoders                 # los cuatro repos
    python -m scripts.bajar_encoders --solo pequenos
"""
import argparse
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, "modelos")

#: (carpeta, repo, pequeño, rama, tipo). EL REPO Y LA RAMA IMPORTAN: el modelo
#: se reentrena por versión de Lean, y los embeddings precalculados de
#: `l3lab/lean-premises` (rama v4.29.0) los hizo `l3lab/…`, rama v4.29.0. El
#: homónimo de `hanwenzhu/` sólo llega a v4.20.0, y con él cada premisa se
#: parece a su propia fila (coseno mediano 0,33) casi lo mismo que a la vecina
#: (0,26): medido con `scripts/alinear_premisas.py`, que por eso no escribió
#: el índice.
REPOS = [
    ("premise-selection", "l3lab/all-distilroberta-v1-lr2e-4-bs256-nneg3-ml-ne2",
     True, "v4.29.0", "model"),
    ("lean-premises-v4.29.0", "l3lab/lean-premises", True, "v4.29.0", "dataset"),
    ("leansearch-ps", "FrenzyMath/LeanSearch-PS", True, None, "model"),
    ("e5-mistral-7b-instruct", "intfloat/e5-mistral-7b-instruct", False, None, "model"),
    ("lean-finder", "delta-lab-ai/lean-finder", False, None, "model"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", choices=["pequenos", "todos"], default="todos")
    args = ap.parse_args()
    from huggingface_hub import snapshot_download
    os.makedirs(DESTINO, exist_ok=True)
    for nombre, repo, pequeno, rama, tipo in REPOS:
        if args.solo == "pequenos" and not pequeno:
            continue
        t0 = time.time()
        print("== %s  (%s)" % (nombre, repo), flush=True)
        try:
            ruta = snapshot_download(repo_id=repo, revision=rama, repo_type=tipo,
                                     local_dir=os.path.join(DESTINO, nombre))
            tam = sum(os.path.getsize(os.path.join(d, f))
                      for d, _, fs in os.walk(ruta) for f in fs)
            print("   ok · %.2f GB · %.0f s" % (tam / 1e9, time.time() - t0), flush=True)
        except Exception as e:                                 # noqa: BLE001
            print("   FALLO: %s" % str(e)[:300], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
