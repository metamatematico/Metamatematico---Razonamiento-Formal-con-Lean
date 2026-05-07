"""Tipos de datos del módulo Consultores Avanzados."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class RequestType(Enum):
    THEOREM      = "theorem"
    METATHEOREM  = "metatheorem"
    OPTIMIZATION = "optimization"
    TOOL         = "tool"
    HYBRID       = "hybrid"
    UNKNOWN      = "unknown"


@dataclass
class FormalSpec:
    enunciado_formal: str = ""
    entradas: list[str] = field(default_factory=list)
    supuestos: list[str] = field(default_factory=list)
    criterios_exito: list[str] = field(default_factory=list)
    formato_salida: list[str] = field(default_factory=list)
    mathlib_anchors: list[str] = field(default_factory=list)


@dataclass
class Candidate:
    """Un artefacto candidato completo."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    lean_file: str = ""            # contenido .lean autocontenido
    proof_skeleton: str = ""       # estrategia de prueba en lenguaje natural
    solver_script: str = ""        # Python/OR-Tools/PuLP (vacío si no aplica)
    verification_bridge: str = ""  # convierte solution.json → instancia Lean
    verification_plan: list[str] = field(default_factory=list)
    lean_commands: list[str] = field(default_factory=list)  # comandos exactos
    # Llenado por la capa de verificación del NLE
    lean_verified: Optional[bool] = None
    lean_errors: list[str] = field(default_factory=list)
    sorry_count: int = 0

    @property
    def has_solver(self) -> bool:
        return bool(self.solver_script.strip())

    @property
    def verification_badge(self) -> str:
        if self.lean_verified is None:
            return "⏳ pendiente"
        if self.lean_verified and self.sorry_count == 0:
            return "✅ verificado"
        if self.lean_verified:
            return f"⚠️ verificado ({self.sorry_count} sorry)"
        return "❌ error Lean"


@dataclass
class CandidateMetrics:
    syntax_score: float = 0.0
    mathlib_coverage: float = 0.0
    proof_complexity: int = 3      # 1=trivial … 5=muy compleja
    completeness: float = 0.0
    lean_score: float = 0.0        # 1.0=sin sorry, 0.5=con sorry, 0=error
    total_score: float = 0.0
    human_review: bool = False
    notas: str = ""

    @classmethod
    def compute(
        cls,
        candidate: Candidate,
        syntax_ok: bool = True,
        n_mathlib_imports: int = 0,
        n_total_imports: int = 1,
        notas: str = "",
    ) -> CandidateMetrics:
        m = cls()
        m.notas = notas
        m.syntax_score = 1.0 if syntax_ok else 0.0
        m.mathlib_coverage = n_mathlib_imports / max(n_total_imports, 1)

        lines = candidate.lean_file.count("\n") + 1
        m.proof_complexity = (
            1 if lines < 20 else
            2 if lines < 50 else
            3 if lines < 100 else
            4 if lines < 200 else 5
        )

        if not candidate.lean_file:
            m.completeness = 0.0
        elif candidate.sorry_count == 0:
            m.completeness = 1.0
        else:
            total = max(
                candidate.lean_file.count("theorem")
                + candidate.lean_file.count("lemma"), 1,
            )
            m.completeness = max(0.0, 1.0 - candidate.sorry_count / total)

        if candidate.lean_verified is True and candidate.sorry_count == 0:
            m.lean_score = 1.0
        elif candidate.lean_verified is True:
            m.lean_score = 0.5
        elif candidate.lean_verified is False:
            m.lean_score = 0.0
        else:
            m.lean_score = 0.25  # no ejecutado

        m.total_score = (
            0.25 * m.syntax_score
            + 0.15 * m.mathlib_coverage
            + 0.10 * (1.0 / m.proof_complexity)
            + 0.25 * m.completeness
            + 0.25 * m.lean_score
        )
        m.human_review = m.total_score < 0.60
        return m


@dataclass
class RankedCandidate:
    candidate: Candidate
    metrics: CandidateMetrics
    rank: int = 0


@dataclass
class AuditTrace:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    query: str = ""
    request_type: str = ""
    n_candidates_generated: int = 0
    n_lean_passed: int = 0
    model_used: str = ""
    processing_time_s: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "query_preview": self.query[:200],
            "request_type": self.request_type,
            "n_candidates": self.n_candidates_generated,
            "n_lean_passed": self.n_lean_passed,
            "model": self.model_used,
            "time_s": round(self.processing_time_s, 2),
            **self.metadata,
        }


@dataclass
class ConsultingResult:
    query: str = ""
    request_type: RequestType = RequestType.UNKNOWN
    spec: Optional[FormalSpec] = None
    ranked_candidates: list[RankedCandidate] = field(default_factory=list)
    audit: Optional[AuditTrace] = None
    executive_summary: str = ""
    raw_llm_response: str = ""
    error: Optional[str] = None

    @property
    def best(self) -> Optional[RankedCandidate]:
        return self.ranked_candidates[0] if self.ranked_candidates else None

    @property
    def has_verified(self) -> bool:
        return any(rc.candidate.lean_verified is True for rc in self.ranked_candidates)

    @property
    def has_solvers(self) -> bool:
        return any(rc.candidate.has_solver for rc in self.ranked_candidates)
