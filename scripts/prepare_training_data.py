"""
prepare_training_data.py
========================
Divide los datasets matematicos en splits train/val/test y los guarda
listos para entrenar el GNN+PPO del NLE.

Destino: E:\\datadeentrenamientovalidacion_test\\

Splits por dataset:
  MATH       : train(8500) -> 80/10/10  |  test_orig(5000) -> test extra
  GSM8K      : train(7473) -> 80/10/10  |  test_orig(1319) -> test extra
  NuminaMath : N muestreados (def 50000) -> 80/10/10 estratificado por source
  ProofNet   : 369 teoremas -> 70/15/15

Formato de salida (JSONL, un JSON por linea):
  problem       - enunciado del problema en lenguaje natural
  solution      - solucion / prueba referencia
  category      - categoria NLE (algebra, geometry, number_theory, ...)
  action_label  - 2 = ASSIST (pasar a Lean) para todos los problemas matematicos
  source        - dataset de origen
  split         - train | val | test

Uso:
  python scripts/prepare_training_data.py
  python scripts/prepare_training_data.py --numina-n 20000 --seed 42
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATASET_DIR   = Path("E:/MetamatematicoDataSet")
OUT_DIR       = Path("E:/datadeentrenamientovalidacion_test")

# Accion ASSIST = indice 2 en ACTION_TYPES = [RESPONSE, REORGANIZE, ASSIST]
ACTION_ASSIST = 2

# Mapeo de categorias MATH -> categorias NLE
MATH_CAT_MAP = {
    "algebra":                   "algebra",
    "intermediate_algebra":      "algebra",
    "prealgebra":                "algebra",
    "counting_and_probability":  "combinatorics",
    "geometry":                  "geometry",
    "number_theory":             "number_theory",
    "precalculus":               "analysis",
}

# Mapeo de fuentes NuminaMath -> categorias NLE
NUMINA_SOURCE_MAP = {
    "amc_aime":          "competition_math",
    "math":              "algebra",
    "olympiad":          "competition_math",
    "cn_k12":            "algebra",
    "synthetic_math":    "algebra",
    "orca_math":         "algebra",
}


# =============================================================================
# Funciones de carga
# =============================================================================

def load_math_dataset() -> list[dict]:
    """Carga todas las categorias de MATH (train + test)."""
    try:
        from datasets import load_from_disk
    except ImportError:
        print("  [ERROR] pip install datasets")
        return []

    records = []
    math_root = DATASET_DIR / "MATH"
    for cat_dir in sorted(math_root.iterdir()):
        if not cat_dir.is_dir():
            continue
        cat_name = cat_dir.name
        nle_cat  = MATH_CAT_MAP.get(cat_name, "algebra")
        for split_dir in sorted(cat_dir.iterdir()):
            if not split_dir.is_dir():
                continue
            orig_split = split_dir.name  # "train" o "test"
            try:
                ds = load_from_disk(str(split_dir))
            except Exception as e:
                print(f"  [SKIP] {split_dir}: {e}")
                continue
            for row in ds:
                records.append({
                    "problem":      row.get("problem", ""),
                    "solution":     row.get("solution", ""),
                    "category":     nle_cat,
                    "action_label": ACTION_ASSIST,
                    "source":       f"math_{cat_name}",
                    "_orig_split":  orig_split,
                })
    print(f"  MATH: {len(records)} registros totales")
    return records


def load_gsm8k_dataset() -> list[dict]:
    """Carga GSM8K (train + test)."""
    try:
        from datasets import load_from_disk
    except ImportError:
        print("  [ERROR] pip install datasets")
        return []

    records = []
    try:
        ds = load_from_disk(str(DATASET_DIR / "GSM8K"))
        for split_name in ds.keys():
            for row in ds[split_name]:
                records.append({
                    "problem":      row.get("question", ""),
                    "solution":     row.get("answer", ""),
                    "category":     "algebra",
                    "action_label": ACTION_ASSIST,
                    "source":       "gsm8k",
                    "_orig_split":  split_name,
                })
    except Exception as e:
        print(f"  [ERROR] GSM8K: {e}")
    print(f"  GSM8K: {len(records)} registros totales")
    return records


def load_numina_dataset(n: int = 50000, seed: int = 42) -> list[dict]:
    """Carga N ejemplos de NuminaMath estratificado por source."""
    try:
        from datasets import load_from_disk
    except ImportError:
        print("  [ERROR] pip install datasets")
        return []

    try:
        ds = load_from_disk(str(DATASET_DIR / "NuminaMath"))["train"]
    except Exception as e:
        print(f"  [ERROR] NuminaMath: {e}")
        return []

    total = len(ds)
    if n >= total:
        indices = list(range(total))
    else:
        rng = random.Random(seed)
        # Estratificar por source
        by_source: dict[str, list[int]] = {}
        for i in range(total):
            src = ds[i].get("source", "unknown")
            by_source.setdefault(src, []).append(i)

        # Muestrear proporcional
        indices = []
        for src, idx_list in by_source.items():
            k = max(1, round(n * len(idx_list) / total))
            sampled = rng.sample(idx_list, min(k, len(idx_list)))
            indices.extend(sampled)

        # Ajustar al total pedido
        rng.shuffle(indices)
        indices = indices[:n]

    records = []
    for i in indices:
        row = ds[i]
        src     = row.get("source", "numina")
        problem = row.get("problem", "")
        sol     = row.get("solution", "")
        if not problem:
            continue
        nle_cat = NUMINA_SOURCE_MAP.get(src, "competition_math")
        records.append({
            "problem":      problem[:500],
            "solution":     sol[:500],
            "category":     nle_cat,
            "action_label": ACTION_ASSIST,
            "source":       f"numina_{src}",
            "_orig_split":  "train",
        })

    print(f"  NuminaMath: {len(records)} registros muestreados (de {total})")
    return records


def load_proofnet_dataset() -> list[dict]:
    """Carga ProofNet (test + valid)."""
    import re

    records = []
    proofnet_dir = DATASET_DIR / "ProofNet/ProofNet-main/benchmark"
    for fname in ("test.jsonl", "valid.jsonl"):
        path = proofnet_dir / fname
        if not path.exists():
            print(f"  [SKIP] {path}")
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                nl  = row.get("nl_statement", "")
                fs  = row.get("formal_statement", "")
                if not nl:
                    continue
                records.append({
                    "problem":      nl,
                    "solution":     fs,
                    "category":     "formal_proof",
                    "action_label": ACTION_ASSIST,
                    "source":       "proofnet",
                    "_orig_split":  "train",
                })
    print(f"  ProofNet: {len(records)} registros")
    return records


# =============================================================================
# Splitting
# =============================================================================

def split_records(
    records: list[dict],
    train_ratio: float = 0.80,
    val_ratio: float = 0.10,
    seed: int = 42,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Divide los registros en train/val/test.

    Si el registro tiene _orig_split == 'test', siempre va a test.
    El resto se divide segun los ratios.
    """
    rng = random.Random(seed)

    fixed_test = [r for r in records if r.get("_orig_split") == "test"]
    pool       = [r for r in records if r.get("_orig_split") != "test"]

    rng.shuffle(pool)
    n = len(pool)
    n_train = int(n * train_ratio)
    n_val   = int(n * val_ratio)

    train = pool[:n_train]
    val   = pool[n_train:n_train + n_val]
    test  = pool[n_train + n_val:] + fixed_test

    return train, val, test


# =============================================================================
# Escritura
# =============================================================================

def save_jsonl(records: list[dict], path: Path, split: str) -> None:
    """Guarda registros como JSONL, anadiendo el campo split."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            out = {k: v for k, v in rec.items() if not k.startswith("_")}
            out["split"] = split
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
    print(f"    -> {len(records):>6} registros  {path}")


def save_split(name: str, train: list, val: list, test: list) -> None:
    """Guarda los tres splits de un dataset."""
    base = OUT_DIR / name
    save_jsonl(train, base / "train.jsonl", "train")
    save_jsonl(val,   base / "val.jsonl",   "val")
    save_jsonl(test,  base / "test.jsonl",  "test")
    total = len(train) + len(val) + len(test)
    print(f"    Total {name}: {total}  (train={len(train)}, val={len(val)}, test={len(test)})")


# =============================================================================
# Resumen y manifest
# =============================================================================

def save_manifest(stats: dict) -> None:
    """Guarda un manifest.json con estadisticas del split."""
    path = OUT_DIR / "manifest.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"\n  Manifest guardado: {path}")


# =============================================================================
# CLI
# =============================================================================

def parse_args():
    p = argparse.ArgumentParser(description="Prepara splits train/val/test para el NLE")
    p.add_argument("--numina-n", type=int, default=50000,
                   help="Cuantos ejemplos de NuminaMath usar (default: 50000)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--train-ratio", type=float, default=0.80)
    p.add_argument("--val-ratio",   type=float, default=0.10)
    p.add_argument("--skip-numina",   action="store_true")
    p.add_argument("--skip-proofnet", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    print(f"\n{'='*60}")
    print(f"  Preparando splits de entrenamiento GNN+PPO")
    print(f"  Destino: {OUT_DIR}")
    print(f"{'='*60}\n")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    stats = {}

    # MATH
    print("[1/4] MATH dataset")
    math_records = load_math_dataset()
    if math_records:
        tr, va, te = split_records(math_records, args.train_ratio, args.val_ratio, args.seed)
        save_split("math", tr, va, te)
        stats["math"] = {"train": len(tr), "val": len(va), "test": len(te)}

    # GSM8K
    print("\n[2/4] GSM8K dataset")
    gsm_records = load_gsm8k_dataset()
    if gsm_records:
        tr, va, te = split_records(gsm_records, args.train_ratio, args.val_ratio, args.seed)
        save_split("gsm8k", tr, va, te)
        stats["gsm8k"] = {"train": len(tr), "val": len(va), "test": len(te)}

    # NuminaMath
    if not args.skip_numina:
        print(f"\n[3/4] NuminaMath dataset  (n={args.numina_n})")
        num_records = load_numina_dataset(args.numina_n, args.seed)
        if num_records:
            tr, va, te = split_records(num_records, args.train_ratio, args.val_ratio, args.seed)
            save_split("numina", tr, va, te)
            stats["numina"] = {"train": len(tr), "val": len(va), "test": len(te)}
    else:
        print("\n[3/4] NuminaMath -> SKIP")

    # ProofNet
    if not args.skip_proofnet:
        print("\n[4/4] ProofNet dataset")
        pn_records = load_proofnet_dataset()
        if pn_records:
            tr, va, te = split_records(pn_records, 0.70, 0.15, args.seed)
            save_split("proofnet", tr, va, te)
            stats["proofnet"] = {"train": len(tr), "val": len(va), "test": len(te)}
    else:
        print("\n[4/4] ProofNet -> SKIP")

    # Crear split combinado (union de todos los trains)
    print("\n[Combinado] Uniendo todos los splits...")
    _merge_splits(stats)

    save_manifest(stats)

    ds_stats    = {k: v for k, v in stats.items() if "train" in v}
    total_train = sum(s["train"] for s in ds_stats.values())
    total_val   = sum(s["val"]   for s in ds_stats.values())
    total_test  = sum(s["test"]  for s in ds_stats.values())

    print(f"\n{'='*60}")
    print(f"  LISTO")
    print(f"  train : {total_train:>7} ejemplos")
    print(f"  val   : {total_val:>7} ejemplos")
    print(f"  test  : {total_test:>7} ejemplos")
    print(f"  Total : {total_train+total_val+total_test:>7} ejemplos")
    print(f"{'='*60}\n")


def _merge_splits(stats: dict) -> None:
    """Combina todos los splits individuales en archivos all_train/all_val/all_test."""
    for split in ("train", "val", "test"):
        out_path = OUT_DIR / f"all_{split}.jsonl"
        count = 0
        with open(out_path, "w", encoding="utf-8") as fout:
            for dataset in stats.keys():
                src_path = OUT_DIR / dataset / f"{split}.jsonl"
                if src_path.exists():
                    with open(src_path, encoding="utf-8") as fin:
                        for line in fin:
                            fout.write(line)
                            count += 1
        print(f"    all_{split}.jsonl: {count} registros -> {out_path}")
    stats["_combined"] = {}


if __name__ == "__main__":
    main()
