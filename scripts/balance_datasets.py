"""
balance_datasets.py
===================
Paso 0 del sistema multi-agente: extrae, etiqueta y balancea problemas
de todos los datasets disponibles en E:/MetamatematicoDataSet/ y los
organiza en splits por categoría para entrenar los 14 agentes especializados.

Las 14 categorías del NLE v7.0:
    algebra, analysis, category-theory, combinatorics, computation,
    geometry, lean-tactics, logic, number-theory, optimization,
    probability, proof-strategies, set-theory, topology

Salida:
    E:/datadeentrenamientovalidacion_test/by_category/<categoria>/
        train.jsonl   (80%)
        val.jsonl     (10%)
        test.jsonl    (10%)
    E:/datadeentrenamientovalidacion_test/balanced_train.jsonl   (todos unidos, balanceados)

Uso:
    python scripts/balance_datasets.py
    python scripts/balance_datasets.py --target 5000   # ejemplos por categoría
    python scripts/balance_datasets.py --dry-run       # solo muestra estadísticas
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

DATASETS_DIR = Path("E:/MetamatematicoDataSet")
OUTPUT_DIR   = Path("E:/datadeentrenamientovalidacion_test/by_category")

# ──────────────────────────────────────────────────────────────────────────────
# Keywords por categoría para clasificar problemas sin etiqueta explícita
# ──────────────────────────────────────────────────────────────────────────────
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "topology": [
        "topolog", "compact", "hausdorff", "open set", "closed set",
        "homeomorphi", "continuous map", "metric space", "neighborhood",
        "connecte", "homotop", "manifold", "covering space", "quotient space",
        "basis for topology", "interior", "closure", "boundary",
    ],
    "category-theory": [
        "functor", "natural transformation", "adjoint", "adjunction",
        "category theory", "morphism", "commutative diagram", "limit",
        "colimit", "universal property", "yoneda", "topos", "monad",
        "abelian category", "exact sequence", "sheaf",
    ],
    "logic": [
        "propositional logic", "first-order logic", "fol", "predicate",
        "tautology", "satisfiable", "valid formula", "proof theory",
        "model theory", "completeness theorem", "gödel", "peano",
        "logical consequence", "entailment", "deduction", "axiom schema",
        "boolean algebra", "truth table",
    ],
    "optimization": [
        "minimize", "maximize", "objective function", "constraint",
        "linear programming", "convex", "gradient descent", "lagrange",
        "lagrangian", "simplex", "duality", "kuhn-tucker", "kkt",
        "optimization problem", "feasible region",
    ],
    "computation": [
        "algorithm", "complexity", "big-o", "turing machine", "automaton",
        "regular language", "context-free", "np-complete", "np-hard",
        "graph algorithm", "dynamic programming", "recursion", "sorting",
        "halting problem", "computability",
    ],
    "lean-tactics": [
        "lean 4", "lean4", "mathlib", "theorem prover", "tactic",
        "norm_num", "ring_nf", "omega", "simp", "exact", "apply",
        "rfl", "linarith", "nlinarith", "decide", "native_decide",
        "by induction", "have :", "show :", "suffices",
    ],
    "proof-strategies": [
        "proof by induction", "proof by contradiction", "proof by contrapositive",
        "direct proof", "constructive proof", "proof by cases",
        "mathematical induction", "strong induction", "well-ordering",
        "pigeonhole", "double counting", "bijection", "diagonalization",
        "existence proof", "uniqueness proof",
    ],
    "geometry": [
        "triangle", "circle", "angle", "polygon", "perpendicular",
        "parallel", "congruent", "similar", "area", "perimeter",
        "pythagorean", "euclidean", "coordinate geometry", "conic",
        "ellipse", "parabola", "hyperbola", "vector geometry",
        "affine", "projective geometry",
    ],
    "number-theory": [
        "prime", "divisib", "modular arithmetic", "congruence",
        "gcd", "lcm", "diophantine", "fermat", "euler", "chinese remainder",
        "quadratic residue", "number theory", "integer factorization",
        "perfect number", "arithmetic function", "multiplicative",
    ],
    "analysis": [
        "limit", "continuity", "differentiab", "integrab", "series",
        "convergence", "cauchy", "real analysis", "complex analysis",
        "uniform convergence", "epsilon-delta", "taylor", "fourier",
        "measure theory", "lebesgue", "metric space", "banach", "hilbert",
    ],
    "combinatorics": [
        "permutation", "combination", "binomial coefficient",
        "counting", "pigeonhole", "graph theory", "coloring",
        "partition", "generating function", "recurrence",
        "catalan", "stirling", "inclusion-exclusion", "bijection",
        "combinatorial identity",
    ],
    "probability": [
        "probability", "random variable", "expected value", "variance",
        "distribution", "bayes", "markov", "central limit theorem",
        "law of large numbers", "conditional probability", "stochastic",
        "normal distribution", "binomial distribution", "poisson",
    ],
    "set-theory": [
        "set theory", "zfc", "axiom of choice", "cardinal", "ordinal",
        "cantor", "power set", "uncountable", "countable", "bijection",
        "injection", "surjection", "russell", "zermelo", "well-founded",
    ],
    "algebra": [
        "algebra", "equation", "polynomial", "matrix", "determinant",
        "eigenvalue", "group", "ring", "field", "vector space",
        "linear algebra", "quadratic", "system of equations",
        "abstract algebra", "galois",
    ],
}


def classify_problem(text: str) -> str:
    """Clasifica un problema en una categoría por keywords. Retorna la mejor."""
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[cat] = score
    if not scores:
        return "algebra"  # fallback
    return max(scores, key=lambda c: scores[c])


def record(problem: str, solution: str, category: str,
           source: str, action_label: int = 2) -> dict:
    return {
        "problem":      problem,
        "solution":     solution,
        "category":     category,
        "action_label": action_label,
        "source":       source,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Extractores por dataset
# ──────────────────────────────────────────────────────────────────────────────

def extract_numina(max_per_source: int = 30_000) -> list[dict]:
    """Extrae de NuminaMath completo, categorizando por keywords."""
    try:
        from datasets import load_from_disk
    except ImportError:
        print("  [SKIP] datasets no disponible")
        return []

    path = DATASETS_DIR / "NuminaMath"
    if not path.exists():
        print("  [SKIP] NuminaMath no encontrado")
        return []

    print("  Cargando NuminaMath (859K)...")
    ds = load_from_disk(str(path))
    train = ds["train"]

    # Mapa de source → categoría directa
    SOURCE_TO_CAT = {
        "cn_k12":          None,           # clasificar por keywords
        "synthetic_math":  None,
        "orca_math":       None,
        "olympiads":       None,           # clasificar por keywords
        "synthetic_amc":   None,
        "aops_forum":      "proof-strategies",
        "math":            None,
        "gsm8k":           "algebra",
        "amc_aime":        None,
    }

    results = []
    per_source: Counter = Counter()

    for r in train:
        src = r.get("source", "unknown")
        if per_source[src] >= max_per_source:
            continue
        problem  = r.get("problem", "") or r.get("question", "") or ""
        solution = r.get("solution", "") or r.get("answer", "") or ""
        if not problem or not solution:
            continue

        base_cat = SOURCE_TO_CAT.get(src)
        cat = base_cat if base_cat else classify_problem(problem + " " + solution)

        results.append(record(problem, solution, cat, f"numina_{src}"))
        per_source[src] += 1

    print(f"  NuminaMath: {len(results):,} extraídos")
    return results


def extract_math_dataset() -> list[dict]:
    """Extrae MATH dataset por subdirectorio → categoría."""
    try:
        from datasets import load_from_disk
    except ImportError:
        return []

    path = DATASETS_DIR / "MATH"
    if not path.exists():
        return []

    SUBDIR_TO_CAT = {
        "algebra":               "algebra",
        "intermediate_algebra":  "algebra",
        "prealgebra":            "algebra",
        "geometry":              "geometry",
        "number_theory":         "number-theory",
        "counting_and_probability": "combinatorics",
        "precalculus":           "analysis",
    }

    results = []
    for subdir, cat in SUBDIR_TO_CAT.items():
        subpath = path / subdir
        if not subpath.exists():
            continue
        try:
            ds = load_from_disk(str(subpath))
            split = ds["train"] if "train" in ds else ds
            for r in split:
                p = r.get("problem", "")
                s = r.get("solution", "")
                if p and s:
                    results.append(record(p, s, cat, f"math_{subdir}"))
        except Exception as e:
            print(f"  [WARN] MATH/{subdir}: {e}")

    print(f"  MATH: {len(results):,} extraídos")
    return results


def extract_gsm8k() -> list[dict]:
    try:
        from datasets import load_from_disk
    except ImportError:
        return []
    path = DATASETS_DIR / "GSM8K"
    if not path.exists():
        return []
    results = []
    try:
        ds = load_from_disk(str(path))
        split = ds["train"] if "train" in ds else ds
        for r in split:
            p = r.get("question", "")
            s = r.get("answer", "")
            if p and s:
                results.append(record(p, s, "algebra", "gsm8k"))
    except Exception as e:
        print(f"  [WARN] GSM8K: {e}")
    print(f"  GSM8K: {len(results):,} extraídos")
    return results


def extract_proofnet() -> list[dict]:
    """ProofNet — JSONL en ProofNet-main/benchmark/{valid,test}.jsonl"""
    import json as _json
    benchmark_dir = DATASETS_DIR / "ProofNet" / "ProofNet-main" / "benchmark"
    if not benchmark_dir.exists():
        # Intentar también como dataset HF
        try:
            from datasets import load_from_disk
            path = DATASETS_DIR / "ProofNet"
            ds = load_from_disk(str(path))
            results = []
            for split_name in ds:
                for r in ds[split_name]:
                    p = r.get("nl_statement", "") or r.get("statement", "")
                    s = r.get("formal_statement", "") or r.get("nl_proof", "") or ""
                    if p:
                        results.append(record(p, s, "proof-strategies", "proofnet"))
            print(f"  ProofNet: {len(results):,} extraídos")
            return results
        except Exception:
            print("  [SKIP] ProofNet no encontrado")
            return []
    results = []
    for jsonl_file in benchmark_dir.rglob("*.jsonl"):
        try:
            with open(jsonl_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    r = _json.loads(line)
                    p = r.get("nl_statement", "") or r.get("formal_statement", "")
                    s = r.get("nl_proof", "") or r.get("formal_statement", "")
                    if p:
                        results.append(record(p, s, "proof-strategies", "proofnet"))
        except Exception as e:
            print(f"  [WARN] ProofNet/{jsonl_file.name}: {e}")
    print(f"  ProofNet: {len(results):,} extraídos")
    return results


def extract_logicot() -> list[dict]:
    try:
        from datasets import load_from_disk
    except ImportError:
        return []
    path = DATASETS_DIR / "LogiCoT"
    if not path.exists():
        print("  [SKIP] LogiCoT aún no descargado")
        return []
    results = []
    try:
        ds = load_from_disk(str(path))
        split = ds["train"] if "train" in ds else ds
        for r in split:
            p = r.get("question", "") or r.get("instruction", "") or r.get("input", "")
            s = r.get("answer", "") or r.get("output", "") or r.get("response", "")
            if p and s:
                results.append(record(p, s, "logic", "logicot"))
    except Exception as e:
        print(f"  [WARN] LogiCoT: {e}")
    print(f"  LogiCoT: {len(results):,} extraídos")
    return results


def extract_lean_workbook() -> list[dict]:
    try:
        from datasets import load_from_disk
    except ImportError:
        return []
    path = DATASETS_DIR / "LeanWorkbookProofs"
    if not path.exists():
        print("  [SKIP] LeanWorkbookProofs aún no descargado")
        return []
    results = []
    try:
        ds = load_from_disk(str(path))
        split = ds["train"] if "train" in ds else ds
        for r in split:
            # LeanWorkbookProofs tiene: problem_id + full_proof (Lean 4 completo)
            proof = r.get("full_proof", "") or r.get("proof", "") or r.get("formal_proof", "")
            pid = r.get("problem_id", "")
            # Extraer la línea theorem/lemma como "problema"
            import re as _re
            theorem_line = ""
            for line in proof.split("\n"):
                if _re.match(r"\s*(theorem|lemma|example)\s", line):
                    theorem_line = line.strip()
                    break
            p = theorem_line or pid  # fallback al ID si no hay theorem
            s = proof
            if p and s:
                results.append(record(p, s, "lean-tactics", "lean_workbook_proofs"))
    except Exception as e:
        print(f"  [WARN] LeanWorkbookProofs: {e}")
    print(f"  LeanWorkbookProofs: {len(results):,} extraídos")
    return results


def extract_ntp_mathlib() -> list[dict]:
    try:
        from datasets import load_from_disk
    except ImportError:
        return []
    path = DATASETS_DIR / "NTPMathlib"
    if not path.exists():
        print("  [SKIP] NTPMathlib aún no descargado")
        return []
    results = []
    try:
        ds = load_from_disk(str(path))
        split = ds["train"] if "train" in ds else ds
        for r in split:
            # ntp-mathlib tiene: state, next_tactic, decl_nm
            state = r.get("state", "") or r.get("goal", "")
            tactic = r.get("next_tactic", "") or r.get("tactic", "")
            decl = r.get("decl_nm", "") or r.get("theorem_name", "")
            if state and tactic:
                p = f"Given Lean 4 proof state:\n{state}\nWhat is the next tactic?"
                s = tactic
                results.append(record(p, s, "lean-tactics", "ntp_mathlib"))
    except Exception as e:
        print(f"  [WARN] NTPMathlib: {e}")
    print(f"  NTPMathlib: {len(results):,} extraídos")
    return results


def extract_openr1() -> list[dict]:
    """OpenR1-Math-220k — geometry, NT, combinatorics, analysis, algebra."""
    try:
        from datasets import load_from_disk
    except ImportError:
        return []
    path = DATASETS_DIR / "OpenR1Math"
    if not path.exists():
        print("  [SKIP] OpenR1Math aún no descargado")
        return []
    results = []
    try:
        ds = load_from_disk(str(path))
        split = ds["train"] if "train" in ds else ds
        for r in split:
            p = r.get("problem", "")
            s = r.get("solution", "") or r.get("answer", "")
            ptype = r.get("problem_type", "") or ""
            cat = classify_problem(p + " " + ptype) if ptype else classify_problem(p)
            if p and s:
                results.append(record(p, s, cat, "openr1_math"))
    except Exception as e:
        print(f"  [WARN] OpenR1Math: {e}")
    print(f"  OpenR1Math: {len(results):,} extraídos")
    return results


def extract_olympiads() -> list[dict]:
    """AI-MO/olympiads — geometry, NT, combinatorics, topology, algebra."""
    try:
        from datasets import load_from_disk
    except ImportError:
        return []
    path = DATASETS_DIR / "Olympiads"
    if not path.exists():
        print("  [SKIP] Olympiads aún no descargado")
        return []
    results = []
    try:
        ds = load_from_disk(str(path))
        split = ds["train"] if "train" in ds else ds
        for r in split:
            p = r.get("problem", "") or r.get("statement", "")
            s = r.get("solution", "") or r.get("answer", "")
            ptype = r.get("problem_type", "") or ""
            cat = classify_problem(p + " " + ptype)
            if p:
                results.append(record(p, s or "See solution.", cat, "olympiads"))
    except Exception as e:
        print(f"  [WARN] Olympiads: {e}")
    print(f"  Olympiads: {len(results):,} extraídos")
    return results


def extract_lean_workbook_states() -> list[dict]:
    """internlm/Lean-Workbook — lean-tactics (proof states)."""
    try:
        from datasets import load_from_disk
    except ImportError:
        return []
    path = DATASETS_DIR / "LeanWorkbook"
    if not path.exists():
        print("  [SKIP] LeanWorkbook aún no descargado")
        return []
    results = []
    try:
        ds = load_from_disk(str(path))
        split = ds["train"] if "train" in ds else ds
        for r in split:
            state_before = r.get("state_before", "") or ""
            tactic       = r.get("tactic", "") or ""
            state_after  = r.get("state_after", "") or ""
            if state_before and tactic:
                p = f"Lean 4 proof state:\n{state_before}\nApply next tactic:"
                s = tactic
                results.append(record(p, s, "lean-tactics", "lean_workbook"))
    except Exception as e:
        print(f"  [WARN] LeanWorkbook: {e}")
    print(f"  LeanWorkbook: {len(results):,} extraídos")
    return results


def extract_openmath_reasoning() -> list[dict]:
    """nvidia/OpenMathReasoning — proof-strategies, competition."""
    try:
        from datasets import load_from_disk
    except ImportError:
        return []
    path = DATASETS_DIR / "OpenMathReasoning"
    if not path.exists():
        print("  [SKIP] OpenMathReasoning aún no descargado")
        return []
    results = []
    try:
        ds = load_from_disk(str(path))
        split = ds["train"] if "train" in ds else ds
        for r in split:
            p = r.get("problem", "") or r.get("question", "")
            s = r.get("solution", "") or r.get("generated_solution", "") or r.get("answer", "")
            if p and s:
                cat = classify_problem(p)
                results.append(record(p, s, cat, "openmath_reasoning"))
    except Exception as e:
        print(f"  [WARN] OpenMathReasoning: {e}")
    print(f"  OpenMathReasoning: {len(results):,} extraídos")
    return results


def extract_autoformalization() -> list[dict]:
    """
    casey-martin/multilingual-mathematical-autoformalization
    327K ejemplos NL -> Lean/Isabelle.
    Cubre: category-theory, topology, logic, lean-tactics, proof-strategies, formal_proof.
    """
    try:
        from datasets import load_from_disk
    except ImportError:
        return []
    path = DATASETS_DIR / "Autoformalization"
    if not path.exists():
        print("  [SKIP] Autoformalization aún no descargado")
        return []
    results = []
    try:
        ds = load_from_disk(str(path))
        split = ds["train"] if "train" in ds else ds
        for r in split:
            p = r.get("input", "")
            s = r.get("output", "")
            if not p or not s:
                continue
            # Clasificar por keywords en ambos campos
            cat = classify_problem(p + " " + s)
            # Si el output es Lean/Isabelle puro, etiquetar como lean-tactics
            if any(kw in s for kw in ["theorem ", "lemma ", "by ", ":= by", "proof", "qed"]):
                if cat not in ("topology", "category-theory", "logic", "set-theory"):
                    cat = "lean-tactics"
            results.append(record(p, s, cat, "autoformalization"))
    except Exception as e:
        print(f"  [WARN] Autoformalization: {e}")
    print(f"  Autoformalization: {len(results):,} extraídos")
    return results


def extract_hendrycks_math() -> list[dict]:
    """EleutherAI/hendrycks_math — algebra, geometry, NT, combinatorics, analysis."""
    try:
        from datasets import load_from_disk
    except ImportError:
        return []
    path = DATASETS_DIR / "HendrycksMath"
    if not path.exists():
        print("  [SKIP] HendrycksMath aún no descargado")
        return []
    SUBTYPE_TO_CAT = {
        "Algebra":                    "algebra",
        "Geometry":                   "geometry",
        "Number Theory":              "number-theory",
        "Counting & Probability":     "combinatorics",
        "Precalculus":                "analysis",
        "Intermediate Algebra":       "algebra",
        "Prealgebra":                 "algebra",
    }
    results = []
    try:
        ds = load_from_disk(str(path))
        split = ds["train"] if "train" in ds else ds
        for r in split:
            p = r.get("problem", "")
            s = r.get("solution", "")
            t = r.get("type", "")
            cat = SUBTYPE_TO_CAT.get(t, classify_problem(p))
            if p and s:
                results.append(record(p, s, cat, "hendrycks_math"))
    except Exception as e:
        print(f"  [WARN] HendrycksMath: {e}")
    print(f"  HendrycksMath: {len(results):,} extraídos")
    return results


def extract_orca_math() -> list[dict]:
    """microsoft/orca-math-word-problems-200k — computation, optimization, algebra."""
    try:
        from datasets import load_from_disk
    except ImportError:
        return []
    path = DATASETS_DIR / "OrcaMath"
    if not path.exists():
        print("  [SKIP] OrcaMath aún no descargado")
        return []
    results = []
    try:
        ds = load_from_disk(str(path))
        split = ds["train"] if "train" in ds else ds
        for r in split:
            p = r.get("question", "")
            s = r.get("answer", "")
            if p and s:
                cat = classify_problem(p)
                results.append(record(p, s, cat, "orca_math"))
    except Exception as e:
        print(f"  [WARN] OrcaMath: {e}")
    print(f"  OrcaMath: {len(results):,} extraídos")
    return results


def extract_raw_parquet(dir_name: str, source_name: str,
                        prob_field: str = "problem",
                        sol_field: str = "solution",
                        cat_field: str = None) -> list[dict]:
    """
    Extrae desde un directorio con archivos .parquet o .jsonl descargados
    como snapshot (sin scripts HuggingFace).
    """
    import glob as _glob
    path = DATASETS_DIR / dir_name
    if not path.exists():
        print(f"  [SKIP] {dir_name} aún no descargado")
        return []

    files = list(path.rglob("*.parquet")) + list(path.rglob("*.jsonl"))
    if not files:
        print(f"  [SKIP] {dir_name}: sin archivos parquet/jsonl")
        return []

    results = []
    try:
        import pandas as pd
        for f in files:
            try:
                if str(f).endswith(".parquet"):
                    df = pd.read_parquet(f)
                else:
                    df = pd.read_json(f, lines=True)
                for _, row in df.iterrows():
                    p = str(row.get(prob_field, "") or "")
                    s = str(row.get(sol_field, "") or "")
                    if not p:
                        continue
                    cat_raw = str(row.get(cat_field, "")) if cat_field else ""
                    cat = classify_problem(p + " " + cat_raw) if not cat_raw else classify_problem(cat_raw + " " + p)
                    results.append(record(p, s or ".", cat, source_name))
            except Exception as e:
                pass
    except ImportError:
        print(f"  [WARN] pandas no disponible para {dir_name}")

    print(f"  {dir_name}: {len(results):,} extraídos")
    return results


def extract_deepmind() -> list[dict]:
    try:
        from datasets import load_from_disk
    except ImportError:
        return []
    base = DATASETS_DIR / "DeepMindMath"
    if not base.exists():
        print("  [SKIP] DeepMindMath aún no descargado")
        return []

    SUBSET_TO_CAT = {
        "calculus__differentiate":       "analysis",
        "algebra__linear_1d":            "algebra",
        "arithmetic__add_or_sub":        "computation",
        "probability__swr_p_level_set":  "probability",
    }

    results = []
    for subset, cat in SUBSET_TO_CAT.items():
        subpath = base / subset
        if not subpath.exists():
            continue
        try:
            ds = load_from_disk(str(subpath))
            split = ds["train"] if "train" in ds else ds
            for r in split:
                p = r.get("question", "")
                s = r.get("answer", "")
                if p and s:
                    results.append(record(p, s, cat, f"deepmind_{subset}"))
        except Exception as e:
            print(f"  [WARN] DeepMindMath/{subset}: {e}")

    print(f"  DeepMindMath: {len(results):,} extraídos")
    return results


def extract_omni_math() -> list[dict]:
    """KbsdJames/Omni-MATH — competition math: NT, geometry, combinatorics, algebra."""
    try:
        from datasets import load_from_disk
    except ImportError:
        return []
    path = DATASETS_DIR / "OmniMath"
    if not path.exists():
        print("  [SKIP] OmniMath aún no descargado")
        return []
    # Domain → category mapping
    DOMAIN_TO_CAT = {
        "Number Theory": "number-theory",
        "Combinatorics": "combinatorics",
        "Geometry": "geometry",
        "Algebra": "algebra",
        "Analysis": "analysis",
        "Probability": "probability",
        "Logic": "logic",
    }
    results = []
    try:
        ds = load_from_disk(str(path))
        split = ds["test"] if "test" in ds else ds
        for r in split:
            p = r.get("problem", "")
            s = r.get("solution", "")
            domain = r.get("domain", "")
            if p and s:
                cat = DOMAIN_TO_CAT.get(domain, classify_problem(p))
                results.append(record(p, s, cat, "omni_math"))
    except Exception as e:
        print(f"  [WARN] OmniMath: {e}")
    print(f"  OmniMath: {len(results):,} extraídos")
    return results


def extract_bigbench_logic() -> list[dict]:
    """tasksource/bigbench formal_fallacies — lógica formal y razonamiento."""
    try:
        from datasets import load_from_disk
    except ImportError:
        return []
    path = DATASETS_DIR / "BigbenchFormalFallacies"
    if not path.exists():
        print("  [SKIP] BigbenchFormalFallacies aún no descargado")
        return []
    results = []
    try:
        ds = load_from_disk(str(path))
        for split_name in ds:
            split = ds[split_name]
            for r in split:
                p = r.get("inputs", "")
                targets = r.get("targets", [])
                s = targets[0] if targets else ""
                if p and s:
                    results.append(record(p, s, "logic", "bigbench_logic"))
    except Exception as e:
        print(f"  [WARN] BigbenchFormalFallacies: {e}")
    print(f"  BigbenchFormalFallacies: {len(results):,} extraídos")
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Balance y splits
# ──────────────────────────────────────────────────────────────────────────────

CATEGORIES_14 = [
    "algebra", "analysis", "category-theory", "combinatorics", "computation",
    "geometry", "lean-tactics", "logic", "number-theory", "optimization",
    "probability", "proof-strategies", "set-theory", "topology",
]

# Mapeo de categorías del dataset → categorías NLE
CAT_REMAP = {
    "formal_proof":        "proof-strategies",
    "competition_math":    "algebra",
    "number_theory":       "number-theory",
    "counting":            "combinatorics",
    "counting_and_probability": "combinatorics",
    "precalculus":         "analysis",
    "intermediate_algebra": "algebra",
    "prealgebra":          "algebra",
}


def remap_category(cat: str) -> str:
    return CAT_REMAP.get(cat, cat)


def balance_and_split(
    all_records: list[dict],
    target: int = 5000,
    seed: int = 42,
) -> dict[str, list[dict]]:
    """
    Agrupa por categoría, balancea al target, hace split 80/10/10.
    Retorna dict {categoria: {"train": [...], "val": [...], "test": [...]}}
    """
    rng = random.Random(seed)
    by_cat: dict[str, list[dict]] = defaultdict(list)

    for r in all_records:
        cat = remap_category(r.get("category", "algebra"))
        r["category"] = cat
        by_cat[cat].append(r)

    splits: dict[str, dict] = {}
    stats: dict[str, int] = {}

    for cat in CATEGORIES_14:
        items = by_cat.get(cat, [])
        rng.shuffle(items)

        # Submuestrear si hay demasiados
        if len(items) > target:
            items = items[:target]
        # Upsample con repetición si hay muy pocos (mínimo 500 para entrenar)
        elif len(items) < target and len(items) >= 10:
            needed = target - len(items)
            extras = rng.choices(items, k=needed)
            items = items + extras

        n = len(items)
        n_train = int(n * 0.8)
        n_val   = int(n * 0.1)

        splits[cat] = {
            "train": items[:n_train],
            "val":   items[n_train:n_train + n_val],
            "test":  items[n_train + n_val:],
        }
        stats[cat] = n

    return splits, stats


def save_splits(splits: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Por categoría
    for cat, data in splits.items():
        cat_dir = output_dir / cat
        cat_dir.mkdir(exist_ok=True)
        for split_name, records in data.items():
            path = cat_dir / f"{split_name}.jsonl"
            with open(path, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Archivo unificado balanceado (para entrenar el orquestador)
    all_train = []
    for cat, data in splits.items():
        all_train.extend(data["train"])
    random.shuffle(all_train)

    unified_path = output_dir.parent / "balanced_train.jsonl"
    with open(unified_path, "w", encoding="utf-8") as f:
        for r in all_train:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n  balanced_train.jsonl: {len(all_train):,} ejemplos → {unified_path}")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Balancea datasets para 14 agentes")
    parser.add_argument("--target",  type=int, default=5000,
                        help="Ejemplos objetivo por categoría (default: 5000)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo muestra estadísticas, no guarda")
    parser.add_argument("--seed",    type=int, default=42)
    args = parser.parse_args()

    print("=" * 60)
    print("  Balance de Datasets — NLE v7.0 Multi-Agente")
    print(f"  Objetivo: {args.target} ejemplos por categoría")
    print("=" * 60)

    # Extraer todos los datasets disponibles
    print("\n[1/3] Extrayendo datasets...")
    all_records: list[dict] = []

    all_records += extract_numina(max_per_source=30_000)
    all_records += extract_math_dataset()
    all_records += extract_gsm8k()
    all_records += extract_proofnet()
    all_records += extract_logicot()           # logic (si disponible)
    all_records += extract_lean_workbook()     # lean-tactics (LeanWorkbookProofs)
    all_records += extract_lean_workbook_states()  # lean-tactics (LeanWorkbook states)
    all_records += extract_ntp_mathlib()       # lean-tactics (ntp-mathlib)
    all_records += extract_openr1()            # geometry, NT, combinatorics, analysis (HF format)
    all_records += extract_olympiads()         # geometry, NT, combinatorics, topology
    all_records += extract_openmath_reasoning()  # proof-strategies, competition
    all_records += extract_autoformalization()  # category-theory, topology, logic, lean-tactics
    # OpenR1Math_raw es el mismo dataset que OpenR1Math en formato parquet — skip para evitar duplicados
    # all_records += extract_raw_parquet("OpenR1Math_raw", ...)
    all_records += extract_raw_parquet("Olympiads_raw", "olympiads",
                                       prob_field="problem", sol_field="solution",
                                       cat_field="problem_type")
    all_records += extract_hendrycks_math()    # algebra, geometry, NT, analysis
    all_records += extract_orca_math()         # computation, optimization, algebra
    all_records += extract_deepmind()          # computation, probability (si disponible)
    all_records += extract_omni_math()         # competition: NT, geometry, combinatorics, algebra
    all_records += extract_bigbench_logic()    # lógica formal y razonamiento

    print(f"\n  Total extraído: {len(all_records):,} problemas")

    # Estadísticas antes de balancear
    print("\n[2/3] Distribución por categoría (antes de balancear):")
    before: Counter = Counter()
    for r in all_records:
        before[remap_category(r.get("category", "?"))] += 1
    for cat in CATEGORIES_14:
        n = before.get(cat, 0)
        bar = "█" * min(40, n // 200)
        status = "✅" if n >= args.target else ("⚠️" if n >= 500 else "❌")
        print(f"  {status} {cat:<20} {n:>7}  {bar}")

    if args.dry_run:
        print("\n[dry-run] No se guardaron archivos.")
        return

    # Balancear y guardar
    print(f"\n[3/3] Balanceando y guardando splits...")
    splits, stats = balance_and_split(all_records, target=args.target, seed=args.seed)

    print("\n  Distribución final por categoría:")
    total = 0
    for cat in CATEGORIES_14:
        n = stats.get(cat, 0)
        tr = len(splits[cat]["train"])
        vl = len(splits[cat]["val"])
        te = len(splits[cat]["test"])
        status = "✅" if n >= args.target else ("⚠️" if n >= 500 else "❌")
        print(f"  {status} {cat:<20} total={n:>6}  train={tr:>5}  val={vl:>4}  test={te:>4}")
        total += n

    save_splits(splits, OUTPUT_DIR)

    print(f"\n  Total balanceado: {total:,} ejemplos")
    print(f"  Guardado en: {OUTPUT_DIR}")
    print("\n  Siguiente paso:")
    print("    python scripts/train_multiagent.py --category algebra")
    print("    python scripts/train_multiagent.py --all")
    print("\n✅ Balance completado.")


if __name__ == "__main__":
    main()
