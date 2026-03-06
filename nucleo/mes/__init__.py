"""
Memory Evolutive Systems (MES) Module
======================================

Implementacion del marco teorico de Ehresmann & Vanbremeersch
para el Nucleo Logico Evolutivo v7.0.

Componentes:
- CoRegulator: Red de co-reguladores (tactico, organizativo, estrategico, integridad)
- Memory: Sistema de memoria (empirica, procedimental, semantica, consolidada)
- Complexification: Operaciones de complejificacion
- Patterns: Patrones y colimites

Reference:
- Ehresmann, A. C. & Vanbremeersch, J.-P. (2007). Memory Evolutive Systems.
"""

from nucleo.mes.co_regulators import (
    CoRegulator,
    TacticalCoRegulator,
    OrganizationalCoRegulator,
    StrategicCoRegulator,
    IntegrityCoRegulator,
    CoRegulatorNetwork,
)
from nucleo.mes.memory import (
    MESMemory,
    ProceduralMemory,
    SemanticMemory,
)
from nucleo.mes.patterns import (
    PatternManager,
    ColimitBuilder,
)

__all__ = [
    # Co-regulators
    "CoRegulator",
    "TacticalCoRegulator",
    "OrganizationalCoRegulator",
    "StrategicCoRegulator",
    "IntegrityCoRegulator",
    "CoRegulatorNetwork",
    # Memory
    "MESMemory",
    "ProceduralMemory",
    "SemanticMemory",
    # Patterns
    "PatternManager",
    "ColimitBuilder",
]
