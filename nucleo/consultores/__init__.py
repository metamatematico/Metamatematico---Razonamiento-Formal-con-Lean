"""
Consultores Avanzados — módulo opcional del NLE
================================================

Genera artefactos reproducibles, verificables y auditables para
usuarios expertos en matemáticas.

El módulo reutiliza los MISMOS componentes que el NLE:
    LLMClient    — mismo proveedor/API key configurado
    LeanClient   — misma instalación de Lean 4
    PatternManager / MESMemory — mismo grafo y memoria

Activación (desde Nucleo):
    nucleo.set_consultores_mode(n_candidates=3)

Desactivación:
    nucleo.disable_consultores_mode()

Acceso directo desde páginas Streamlit:
    from nucleo.consultores import ConsultoresModule
    result = await nucleo._consultores.process(query)
"""

from nucleo.consultores.artifacts import (
    RequestType,
    FormalSpec,
    Candidate,
    CandidateMetrics,
    RankedCandidate,
    AuditTrace,
    ConsultingResult,
)
from nucleo.consultores.orchestrator import ConsultoresModule

__all__ = [
    "ConsultoresModule",
    "RequestType",
    "FormalSpec",
    "Candidate",
    "CandidateMetrics",
    "RankedCandidate",
    "AuditTrace",
    "ConsultingResult",
]
