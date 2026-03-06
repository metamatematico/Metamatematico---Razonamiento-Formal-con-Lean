"""
Integracion con Lean 4
======================

Modulo de comunicacion bidireccional con el asistente de pruebas Lean 4.

Componentes:
- LeanClient: Cliente para comunicacion con Lean 4
- LeanParser: Parser de respuestas de Lean
- TacticMapper: Mapeo de tacticas y estrategias
- TacticsDatabase: Base de datos de tacticas (de lean4-skills)
- SorryFiller: Estrategia para rellenar sorries automaticamente

Experimento Go/No-Go #1 (Mes 0-3):
- Pregunta: Puede el nucleo comunicarse bidireccionalmente con Lean?
- Criterio de exito: >= 80% de teoremas procesados correctamente
"""

from nucleo.lean.client import LeanClient, LeanResult
from nucleo.lean.parser import LeanParser, LeanMessage, MessageSeverity
from nucleo.lean.tactics import TacticMapper, Tactic, TacticCategory
from nucleo.lean.tactics_db import (
    TacticsDatabase,
    TacticCategory as DbTacticCategory,
    Tactic as DbTactic,
    GoalPattern,
    get_tactics_database,
)
from nucleo.lean.sorry_filler import (
    SorryFiller,
    SorryType,
    SorryContext,
    ProofCandidate,
    SorryFillingResult,
    classify_goal_type,
    suggest_tactics_for_goal,
    estimate_sorry_difficulty,
)

__all__ = [
    # Client
    "LeanClient",
    "LeanResult",
    # Parser
    "LeanParser",
    "LeanMessage",
    "MessageSeverity",
    # Tactics (original)
    "TacticMapper",
    "Tactic",
    "TacticCategory",
    # Tactics Database (lean4-skills)
    "TacticsDatabase",
    "GoalPattern",
    "get_tactics_database",
    # Sorry Filler
    "SorryFiller",
    "SorryType",
    "SorryContext",
    "ProofCandidate",
    "SorryFillingResult",
    "classify_goal_type",
    "suggest_tactics_for_goal",
    "estimate_sorry_difficulty",
]
