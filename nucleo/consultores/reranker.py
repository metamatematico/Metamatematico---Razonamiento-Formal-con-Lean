"""Reranking de candidatos del módulo Consultores Avanzados."""
from __future__ import annotations

import re
from typing import Optional

from nucleo.consultores.artifacts import (
    Candidate,
    CandidateMetrics,
    RankedCandidate,
)


def _count_mathlib_imports(lean_file: str) -> tuple[int, int]:
    """Devuelve (n_mathlib, n_total) de líneas import en el .lean."""
    total = 0
    mathlib = 0
    for line in lean_file.splitlines():
        stripped = line.strip()
        if stripped.startswith("import "):
            total += 1
            if "Mathlib" in stripped:
                mathlib += 1
    return mathlib, max(total, 1)


def _syntax_ok(lean_file: str) -> bool:
    """Heurística rápida: si hay #check sin cierre o error obvio."""
    if not lean_file.strip():
        return False
    # Rechazar si tiene bloques sin cerrar (llaves desbalanceadas > 5)
    depth = lean_file.count("{") - lean_file.count("}")
    if abs(depth) > 5:
        return False
    return True


def score_and_rank(candidates: list[Candidate]) -> list[RankedCandidate]:
    """
    Puntuar y ordenar candidatos.

    El orden prioriza:
      1. Candidatos Lean verificados sin sorry
      2. Candidatos Lean verificados con sorry
      3. Candidatos no verificados (por puntuación estimada)
      4. Candidatos con error Lean
    """
    ranked: list[RankedCandidate] = []

    for cand in candidates:
        n_mathlib, n_total = _count_mathlib_imports(cand.lean_file)
        syntax = _syntax_ok(cand.lean_file)
        metrics = CandidateMetrics.compute(
            cand,
            syntax_ok=syntax,
            n_mathlib_imports=n_mathlib,
            n_total_imports=n_total,
        )
        ranked.append(RankedCandidate(candidate=cand, metrics=metrics))

    # Ordenar: mayor total_score primero; en empate, sin sorry primero
    ranked.sort(
        key=lambda rc: (
            rc.metrics.total_score,
            -rc.candidate.sorry_count,
        ),
        reverse=True,
    )

    for i, rc in enumerate(ranked):
        rc.rank = i + 1

    return ranked
