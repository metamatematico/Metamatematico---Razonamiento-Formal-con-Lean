"""
Construye el banco de ejemplos few-shot en Lean 4 desde LeanWorkbook.

POR QUE
-------
`data/lean_examples.json` venia de miniF2F y estaba en **Lean 3**: 44 senales
de sintaxis Lean 3 (`begin`/`end`, `nat.`, `real.`) frente a 3 de Lean 4. El
prompt de formalizacion incluso se disculpaba por ello —"Ejemplos de
referencia (Lean 3 — adapta la sintaxis a Lean 4)"— es decir, se le pedia al
modelo que tradujera de un dialecto a otro mientras formalizaba. Dos tareas en
vez de una, y la mitad de los ejemplos empujando hacia la sintaxis equivocada.

LeanWorkbook trae 25.214 problemas con:
    natural_language_statement  ->  formal_statement   (el paso de formalizar)
    tactic, state_before, state_after                  (el paso de probar)
todo en Lean 4 y con `status == "proved"`.

USO
---
    python scripts/seed_lean4_examples.py [--max-por-categoria 40] [--dry-run]

Escribe data/lean_examples.json y guarda el anterior como
data/lean_examples_lean3.json.bak
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = Path(r"E:\MetamatematicoDataSet\LeanWorkbook")
DESTINO = RAIZ / "data" / "lean_examples.json"
RESPALDO = RAIZ / "data" / "lean_examples_lean3.json.bak"

# Las mismas categorias que infiere Nucleo._build_few_shot_context, para que el
# banco y el consumidor hablen el mismo idioma.
CATEGORIAS: dict[str, tuple[str, ...]] = {
    "algebra": ("equation", "polynomial", "inequality", "solve", "factor",
                "quadratic", "algebra", "expression", "simplify"),
    "number_theory": ("prime", "divisible", "divides", "modulo", "integer",
                      "gcd", "lcm", "remainder", "digit", "number theory"),
    "geometry": ("triangle", "angle", "circle", "geometry", "area",
                 "perimeter", "radius", "polygon"),
    "analysis": ("limit", "continuous", "derivative", "integral", "converge",
                 "sequence", "series", "function"),
    "combinatorics": ("permutation", "combination", "counting", "choose",
                      "arrangement", "probability", "combinatoric"),
}

# Sintaxis que delata Lean 3: si aparece, el ejemplo no sirve como modelo.
LEAN3 = re.compile(r"\bbegin\b|\bend\b|\bnat\.|\breal\.|\bint\.|\bfinset\.")


def _categoriza(texto: str) -> str:
    t = (texto or "").lower()
    mejor, puntos = "competition_math", 0
    for cat, claves in CATEGORIAS.items():
        p = sum(1 for k in claves if k in t)
        if p > puntos:
            mejor, puntos = cat, p
    return mejor


def _tacticas(tactic: str) -> list[str]:
    """Parte una tactica compuesta en pasos legibles."""
    if not tactic:
        return []
    # `<;>` y `;` encadenan; el salto de linea separa pasos.
    pasos = re.split(r"\n|(?<!<);(?!>)", tactic)
    return [p.strip() for p in pasos if p.strip()][:4]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-por-categoria", type=int, default=40)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not ORIGEN.exists():
        print(f"No encuentro el dataset en {ORIGEN}")
        return 1

    from datasets import load_from_disk
    ds = load_from_disk(str(ORIGEN))
    print(f"LeanWorkbook: {len(ds):,} ejemplos")

    por_cat: dict[str, list[dict]] = defaultdict(list)
    descartados_lean3 = 0
    vistos: set[str] = set()

    for fila in ds:
        if fila.get("status") != "proved":
            continue
        formal = (fila.get("formal_statement") or "").strip()
        nl = (fila.get("natural_language_statement") or "").strip()
        tac = (fila.get("tactic") or "").strip()
        if not (formal and nl and tac):
            continue
        if LEAN3.search(formal) or LEAN3.search(tac):
            descartados_lean3 += 1
            continue
        # Evitar enunciados repetidos: el banco debe cubrir, no repetir.
        clave = formal[:120]
        if clave in vistos:
            continue

        cat = _categoriza(nl)
        if len(por_cat[cat]) >= args.max_por_categoria:
            continue
        vistos.add(clave)

        por_cat[cat].append({
            "name": fila.get("id") or f"lw_{len(vistos)}",
            "statement": formal,
            "tactics": _tacticas(tac),
            # El enunciado en lenguaje natural permite ordenar por relevancia
            # a la consulta, en vez de servir siempre los dos primeros.
            "nl": nl[:300],
        })

    banco = {k: v for k, v in sorted(por_cat.items()) if v}
    total = sum(len(v) for v in banco.values())

    print(f"\nBanco construido: {total} ejemplos en {len(banco)} categorias")
    for cat, ejs in banco.items():
        print(f"   {cat:20s} {len(ejs):3d}")
    print(f"   (descartados por sintaxis Lean 3: {descartados_lean3:,})")

    if args.dry_run:
        print("\n--dry-run: no se escribe nada")
        return 0

    if DESTINO.exists() and not RESPALDO.exists():
        shutil.copy2(DESTINO, RESPALDO)
        print(f"\nRespaldo del banco anterior -> {RESPALDO.name}")

    DESTINO.write_text(
        json.dumps(banco, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"Escrito {DESTINO} ({DESTINO.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
