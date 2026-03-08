"""
seed_from_datasets.py
=====================
Conecta los datasets descargados al Nucleo Logico Evolutivo.

Fuentes:
  ProofNet  → MES Memory (316 teoremas formales verificados)
  miniF2F   → lean_examples.json (ejemplos few-shot para _math_via_lean)
  NuminaMath→ MES Memory (primeros N problemas con solucion)

Salida:
  data/memory.json         - MES Memory enriquecida (se fusiona con la existente)
  data/lean_examples.json  - Banco de ejemplos Lean para el LLM

Uso:
  python scripts/seed_from_datasets.py
  python scripts/seed_from_datasets.py --numina-n 500 --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATASET_DIR  = Path("E:/MetamatematicoDataSet")
PROOFNET_DIR = DATASET_DIR / "ProofNet/ProofNet-main/benchmark"
MINIF2F_DIR  = DATASET_DIR / "miniF2F/miniF2F-main/lean/src"
NUMINA_DIR   = DATASET_DIR / "NuminaMath"
DATA_DIR     = PROJECT_ROOT / "data"


# =============================================================================
# 1. ProofNet → MES Memory
# =============================================================================

def load_proofnet() -> list[dict]:
    """
    Carga ProofNet (test + valid).

    Cada entrada:
      id              - identificador del teorema (e.g. "Rudin|exercise_1_1b")
      nl_statement    - enunciado en lenguaje natural (LaTeX)
      formal_statement- formalizacion en Lean 3 (theorem ...)
      nl_proof        - demostracion en lenguaje natural
    """
    records = []
    for fname in ("test.jsonl", "valid.jsonl"):
        path = PROOFNET_DIR / fname
        if not path.exists():
            print(f"  [SKIP] {path} no encontrado")
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    print(f"  ProofNet: {len(records)} registros")
    return records


def proofnet_to_memory_entries(records: list[dict]) -> list[dict]:
    """
    Convierte registros ProofNet a entradas de MES Memory.

    Cada entrada se guarda como ProceduralMemory con:
      pattern_id    = "proofnet-<id>"
      query_text    = nl_statement (busqueda por keywords)
      lean_goal     = formal_statement (codigo Lean)
      tactic_used   = "lean4-formal"
      success_rate  = 1.0 (teoremas del libro de Rudin son correctos)
    """
    entries = []
    for r in records:
        pid = r.get("id", "")
        nl  = r.get("nl_statement", "")
        fs  = r.get("formal_statement", "")
        if not nl or not fs:
            continue

        # Extraer nombre del teorema de la formal_statement
        m = re.search(r"theorem\s+(\w+)", fs)
        theorem_name = m.group(1) if m else pid.replace("|", "_")

        entries.append({
            "pattern_id":  f"proofnet-{theorem_name}",
            "query_text":  nl,
            "lean_goal":   fs.strip(),
            "tactic_used": "lean4-formal",
            "action_sequence": ["formalize", "verify"],
            "success_rate": 1.0,
            "source": "proofnet",
        })
    return entries


# =============================================================================
# 2. miniF2F → lean_examples.json (few-shot bank)
# =============================================================================

def load_minif2f_examples() -> list[dict]:
    """
    Extrae teoremas de miniF2F (Lean 3) como ejemplos few-shot.

    Cada ejemplo:
      name        - nombre del teorema (e.g. mathd_algebra_478)
      category    - categoria inferida del nombre
      statement   - cabecera del teorema (sin la prueba)
      proof       - tacticas usadas (si no son sorry)
    """
    examples = []

    for fname in ("test.lean", "valid.lean"):
        path = MINIF2F_DIR / fname
        if not path.exists():
            print(f"  [SKIP] {path} no encontrado")
            continue

        text = path.read_text(encoding="utf-8")

        # Extraer bloques: theorem <name> ... := begin ... end
        # o theorem <name> ... := by ... (Lean 4 style)
        pattern = re.compile(
            r"(theorem\s+(\w+)\s*(.*?):=\s*)(begin(.*?)end|by\s+(\S.*?)(?=\n\n|\ntheorem|\Z))",
            re.DOTALL
        )

        for m in pattern.finditer(text):
            name      = m.group(2)
            header    = m.group(1).strip()
            proof_raw = m.group(4) or m.group(6) or ""

            # Extraer tacticas (lineas que no son espacios ni comentarios)
            tactics = [
                t.strip() for t in proof_raw.split("\n")
                if t.strip() and not t.strip().startswith("--")
                and t.strip() not in ("begin", "end")
            ][:5]  # Max 5 tacticas como ejemplo

            # Inferir categoria del nombre
            category = _infer_category(name)

            # Ignorar si solo tiene sorry
            has_real_proof = any(t not in ("sorry", "") for t in tactics)

            examples.append({
                "name":       name,
                "category":   category,
                "statement":  header,
                "tactics":    tactics,
                "has_proof":  has_real_proof,
                "source":     fname,
            })

    print(f"  miniF2F: {len(examples)} ejemplos")
    return examples


def _infer_category(name: str) -> str:
    """Infiere la categoria matematica del nombre del teorema."""
    name_lower = name.lower()
    if "algebra" in name_lower:
        return "algebra"
    if "numbertheory" in name_lower or "number_theory" in name_lower:
        return "number_theory"
    if "geometry" in name_lower or "geom" in name_lower:
        return "geometry"
    if "combinatorics" in name_lower or "combin" in name_lower:
        return "combinatorics"
    if "calculus" in name_lower or "analysis" in name_lower:
        return "analysis"
    if "aime" in name_lower:
        return "competition_aime"
    if "amc" in name_lower:
        return "competition_amc"
    if "imo" in name_lower:
        return "competition_imo"
    if "mathd" in name_lower:
        return "competition_math"
    return "general"


# =============================================================================
# 3. NuminaMath → MES Memory
# =============================================================================

def load_numina_patterns(n: int = 1000) -> list[dict]:
    """
    Carga los primeros N problemas de NuminaMath como patrones de MES Memory.

    Cada entrada:
      pattern_id    = "numina-<source>-<idx>"
      query_text    = problem (para matching por keywords)
      lean_goal     = "" (NuminaMath no tiene Lean, pero guarda la solucion)
      tactic_used   = "math-problem-solving"
      solution      = solucion completa (guardada para referencia)
    """
    try:
        from datasets import load_from_disk
    except ImportError:
        print("  [SKIP] datasets no instalado")
        return []

    path = NUMINA_DIR
    if not path.exists():
        print(f"  [SKIP] {path} no encontrado")
        return []

    ds = load_from_disk(str(path))
    subset = ds["train"]
    n = min(n, len(subset))

    entries = []
    for i in range(n):
        row    = subset[i]
        source = row.get("source", "numina")
        prob   = row.get("problem", "")
        sol    = row.get("solution", "")
        if not prob:
            continue

        entries.append({
            "pattern_id":  f"numina-{source}-{i}",
            "query_text":  prob[:200],  # Truncar para eficiencia
            "lean_goal":   "",
            "tactic_used": "math-problem-solving",
            "action_sequence": ["analyze", "solve"],
            "success_rate": 1.0,
            "solution":    sol[:500],
            "source":      "numina",
        })

    print(f"  NuminaMath: {len(entries)} patrones (de {len(subset)})")
    return entries


# =============================================================================
# 4. Escritura a MES Memory
# =============================================================================

def seed_mes_memory(entries: list[dict], dry_run: bool = False) -> int:
    """
    Inyecta entradas en la MES Memory del Nucleo.

    Carga la memoria existente, agrega los nuevos registros,
    y guarda de vuelta a data/memory.json.
    """
    from nucleo.mes.memory import MESMemory
    from nucleo.config import NucleoConfig

    config = NucleoConfig()
    memory = MESMemory(
        max_records=config.mes.max_records,
        consolidation_threshold=config.mes.consolidation_threshold,
        econcept_min_records=config.mes.econcept_min_records,
    )

    # Cargar memoria existente
    mem_path = DATA_DIR / "memory.json"
    if mem_path.exists():
        loaded = memory.load(mem_path)
        if loaded:
            print(f"  Memoria existente cargada: {memory.stats}")

    # Agregar nuevas entradas
    added = 0
    for e in entries:
        try:
            memory.learn_procedure(
                pattern_id=e["pattern_id"],
                action_sequence=e.get("action_sequence", ["respond"]),
                success=True,
                query_text=e.get("query_text", ""),
                tactic_used=e.get("tactic_used", ""),
                lean_goal=e.get("lean_goal", ""),
            )
            added += 1
        except Exception as ex:
            print(f"    [WARN] {e['pattern_id']}: {ex}")

    if not dry_run:
        DATA_DIR.mkdir(exist_ok=True)
        memory.save(mem_path)
        print(f"  MES Memory guardada: {added} entradas nuevas → {mem_path}")
    else:
        print(f"  [DRY-RUN] Se agregarían {added} entradas (no guardado)")

    return added


# =============================================================================
# 5. Escritura de lean_examples.json
# =============================================================================

def save_lean_examples(examples: list[dict], dry_run: bool = False) -> None:
    """
    Guarda el banco de ejemplos miniF2F como JSON.

    El Nucleo lo carga en initialize() y lo usa en _math_via_lean()
    como contexto few-shot para el LLM formalizador.
    """
    out_path = DATA_DIR / "lean_examples.json"

    # Separar por categoria para busqueda rapida
    by_category: dict[str, list] = {}
    for ex in examples:
        cat = ex["category"]
        if cat not in by_category:
            by_category[cat] = []
        # Guardar solo los que tienen prueba real (no sorry)
        if ex.get("has_proof", False):
            by_category[cat].append({
                "name":      ex["name"],
                "statement": ex["statement"],
                "tactics":   ex["tactics"],
            })

    total = sum(len(v) for v in by_category.values())
    print(f"  lean_examples.json: {total} ejemplos con prueba real ({len(by_category)} categorias)")

    if not dry_run:
        DATA_DIR.mkdir(exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(by_category, f, ensure_ascii=False, indent=2)
        print(f"  Guardado: {out_path}")
    else:
        print(f"  [DRY-RUN] No guardado")


# =============================================================================
# CLI
# =============================================================================

def parse_args():
    p = argparse.ArgumentParser(description="Conecta datasets al NLE")
    p.add_argument("--numina-n", type=int, default=2000,
                   help="Cuantos problemas de NuminaMath cargar (default: 2000)")
    p.add_argument("--skip-proofnet",  action="store_true")
    p.add_argument("--skip-minif2f",   action="store_true")
    p.add_argument("--skip-numina",    action="store_true")
    p.add_argument("--dry-run", action="store_true",
                   help="Simular sin escribir archivos")
    return p.parse_args()


def main():
    args = parse_args()
    print(f"\n{'='*60}")
    print(f"  Seeding NLE desde datasets matematicos")
    print(f"{'='*60}\n")

    memory_entries = []
    lean_examples  = []

    # --- ProofNet ---
    if not args.skip_proofnet:
        print("[1/3] ProofNet → MES Memory")
        records = load_proofnet()
        memory_entries.extend(proofnet_to_memory_entries(records))
    else:
        print("[1/3] ProofNet → SKIP")

    # --- miniF2F ---
    if not args.skip_minif2f:
        print("\n[2/3] miniF2F → lean_examples.json")
        lean_examples = load_minif2f_examples()
    else:
        print("\n[2/3] miniF2F → SKIP")

    # --- NuminaMath ---
    if not args.skip_numina:
        print(f"\n[3/3] NuminaMath → MES Memory  (n={args.numina_n})")
        memory_entries.extend(load_numina_patterns(args.numina_n))
    else:
        print("\n[3/3] NuminaMath → SKIP")

    # --- Escribir MES Memory ---
    print(f"\n{'─'*60}")
    print(f"Escribiendo MES Memory ({len(memory_entries)} entradas totales)...")
    added = seed_mes_memory(memory_entries, dry_run=args.dry_run)

    # --- Escribir lean_examples.json ---
    if lean_examples:
        print(f"\nEscribiendo lean_examples.json...")
        save_lean_examples(lean_examples, dry_run=args.dry_run)

    print(f"\n{'='*60}")
    print(f"  Listo. {added} patrones en MES Memory.")
    print(f"  Reinicia la app para que el Nucleo los cargue.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
