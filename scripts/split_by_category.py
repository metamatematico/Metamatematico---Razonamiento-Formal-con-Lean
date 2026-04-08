"""
split_by_category.py
====================
Lee los JSONL existentes en E:/datadeentrenamientovalidacion_test/
y los clasifica en 14 categorias sin recargar ningun dataset de HuggingFace.

Tarda segundos, no horas.

Uso:
    python scripts/split_by_category.py
    python scripts/split_by_category.py --dry-run
"""
from __future__ import annotations
import json, re, sys
from collections import defaultdict, Counter
from pathlib import Path

OUTPUT_DIR = Path("E:/Metamatematico/training/by_category")

# Fuentes JSONL existentes (de mayor a menor prioridad)
SOURCES = [
    Path("E:/datadeentrenamientovalidacion_test/all_train.jsonl"),
    Path("E:/datadeentrenamientovalidacion_test/all_val.jsonl"),
    Path("E:/datadeentrenamientovalidacion_test/all_test.jsonl"),
    Path("E:/datadeentrenamientovalidacion_test/numina/train.jsonl"),
    Path("E:/datadeentrenamientovalidacion_test/math/train.jsonl"),
    Path("E:/datadeentrenamientovalidacion_test/gsm8k/train.jsonl"),
    Path("E:/datadeentrenamientovalidacion_test/proofnet/train.jsonl"),
]

CATEGORIES = [
    "algebra", "analysis", "category-theory", "combinatorics", "computation",
    "geometry", "lean-tactics", "logic", "number-theory", "optimization",
    "probability", "proof-strategies", "set-theory", "topology",
]

# Keywords por categoria (orden importa: mas especifico primero)
KEYWORDS: dict[str, list[str]] = {
    "lean-tactics":     ["lean4", "lean 4", "mathlib", "norm_num", "ring_nf",
                         "by simp", "by ring", "by omega", "by exact", "tactic",
                         "theorem prover", "linarith", "nlinarith", "by decide"],
    "proof-strategies": ["proof by induction", "by contradiction", "contrapositive",
                         "base case", "inductive step", "constructive proof",
                         "proof by cases", "without loss of generality", "wlog",
                         "diagonal argument", "pigeonhole"],
    "category-theory":  ["functor", "natural transformation", "adjoint", "adjunction",
                         "category theory", "commutative diagram", "yoneda",
                         "topos", "monad", "abelian category", "exact sequence"],
    "topology":         ["topolog", "compact", "hausdorff", "open set", "closed set",
                         "homeomorphi", "continuous map", "metric space",
                         "connecte", "homotop", "manifold", "covering space"],
    "set-theory":       ["set theory", "power set", "cardinality", "countable",
                         "uncountable", "zfc", "axiom of choice", "ordinal",
                         "cardinal", "cantor", "well-order", "∈", "⊆"],
    "logic":            ["propositional logic", "first-order logic", "fol",
                         "tautology", "satisfiable", "godel", "completeness",
                         "logical consequence", "truth table", "boolean algebra",
                         "predicate logic", "deduction theorem"],
    "computation":      ["algorithm", "complexity", "big-o", "turing machine",
                         "np-complete", "np-hard", "decidable", "halting problem",
                         "automaton", "regular language", "context-free",
                         "dynamic programming", "computability"],
    "optimization":     ["minimize", "maximize", "objective function", "constraint",
                         "linear programming", "convex", "gradient descent",
                         "lagrange", "simplex", "duality", "kkt", "feasible"],
    "probability":      ["probability", "random variable", "expected value",
                         "variance", "distribution", "bayes", "conditional",
                         "stochastic", "markov", "p(a|b)", "p(a∩b)", "p(a∪b)"],
    "analysis":         ["limit", "continuity", "differentiable", "uniform",
                         "cauchy", "series converge", "integral", "derivative",
                         "real analysis", "epsilon-delta", "supremum", "infimum"],
    "geometry":         ["triangle", "circle", "angle", "polygon", "area",
                         "perimeter", "volume", "pythagorean", "euclidean",
                         "coordinate", "distance formula", "midpoint", "parallel"],
    "number-theory":    ["prime", "divisib", "modulo", "congruent", "gcd", "lcm",
                         "fermat", "euler", "diophantine", "quadratic residue",
                         "arithmetic progression", "bezout", "coprime"],
    "combinatorics":    ["permutation", "combination", "binomial", "counting",
                         "graph coloring", "partition", "pigeonhole", "inclusion",
                         "generating function", "recurrence", "fibonacci"],
    "algebra":          ["polynomial", "equation", "group", "ring", "field",
                         "vector space", "matrix", "eigenvalue", "determinant",
                         "linear", "quadratic", "factor", "root", "solve"],
}

def classify(text: str) -> str:
    t = text.lower()
    for cat, kws in KEYWORDS.items():
        if any(kw in t for kw in kws):
            return cat
    return "algebra"  # default más común


def load_all() -> list[dict]:
    records = []
    seen: set[str] = set()
    for src in SOURCES:
        if not src.exists():
            continue
        n = 0
        with open(src, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                problem = rec.get("problem", rec.get("query",
                          rec.get("question", rec.get("input", ""))))
                if not problem:
                    continue
                key = problem[:120]
                if key in seen:
                    continue
                seen.add(key)
                rec["problem"] = problem
                rec.setdefault("solution", rec.get("answer", rec.get("output", "")))
                records.append(rec)
                n += 1
        print(f"  {src.name:<30} {n:>6} ejemplos")
    return records


def split_80_10_10(items: list) -> tuple[list, list, list]:
    import random
    rng = random.Random(42)
    data = items.copy()
    rng.shuffle(data)
    n = len(data)
    t = int(n * 0.8)
    v = int(n * 0.9)
    return data[:t], data[t:v], data[v:]


def write_splits(by_cat: dict[str, list], dry_run: bool):
    total = sum(len(v) for v in by_cat.values())
    print(f"\n  {'Categoria':<22} {'Total':>6}  {'Train':>5}  {'Val':>4}  {'Test':>4}")
    print("  " + "-" * 50)
    for cat in CATEGORIES:
        items = by_cat.get(cat, [])
        n = len(items)
        train, val, test = split_80_10_10(items)
        status = "[OK]  " if n >= 500 else "[LOW] "
        print(f"  {status}{cat:<20} {n:>6}  {len(train):>5}  {len(val):>4}  {len(test):>4}")
        if not dry_run:
            cat_dir = OUTPUT_DIR / cat
            cat_dir.mkdir(parents=True, exist_ok=True)
            for split_name, split_data in [("train", train), ("val", val), ("test", test)]:
                with open(cat_dir / f"{split_name}.jsonl", "w", encoding="utf-8") as f:
                    for rec in split_data:
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\n  Total: {total:,} ejemplos en 14 categorias")
    if not dry_run:
        print(f"  Guardado en: {OUTPUT_DIR}")


def main():
    dry_run = "--dry-run" in sys.argv
    print("=" * 55)
    print("  Split por categoria — NLE v7.0")
    print("=" * 55)
    print("\nCargando JSONL existentes...")
    records = load_all()
    print(f"\nTotal cargado: {len(records):,} ejemplos unicos")

    print("\nClasificando por categoria...")
    by_cat: dict[str, list] = defaultdict(list)
    for rec in records:
        text = rec.get("problem", "") + " " + rec.get("solution", "")
        cat = rec.get("category") or classify(text)
        if cat not in CATEGORIES:
            cat = classify(text)
        by_cat[cat].append(rec)

    dist = Counter({cat: len(v) for cat, v in by_cat.items()})
    print(f"Categorias detectadas: {dict(dist.most_common())}")

    if dry_run:
        print("\n[dry-run] No se guardaron archivos.")
    write_splits(by_cat, dry_run)

    if not dry_run:
        print("\n[DONE] Listo para entrenar:")
        print("  python scripts/train_multiagent.py --device cuda")

if __name__ == "__main__":
    main()
