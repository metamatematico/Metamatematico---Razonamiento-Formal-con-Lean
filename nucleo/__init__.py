"""
Nucleo Logico Evolutivo
=======================

Interfaz Adaptativa entre LLM, Lean 4 y Grafo Categorico de Skills.

Sistema Evolutivo de Asistencia Matematica:
    Sigma_t = (L, N_t, G_t, F)

Componentes:
    - L: Modelo de Lenguaje (LLM)
    - N_t: Nucleo Logico (Agente RL)
    - G_t: Grafo Categorico de Skills
    - F: Cuatro Pilares Fundacionales
        - F_Set: Teoria de Conjuntos
        - F_Cat: Teoria de Categorias
        - F_Log: Logica
        - F_Type: Teoria de Tipos

Autor: Leonardo Jiménez Martínez (BIOMAT · Centro de Biomatemáticas) & Claude (Anthropic)
Version: 0.1.0
"""

__version__ = "0.1.0"
__author__ = "Leonardo Jiménez Martínez"

from nucleo.types import (
    Skill,
    Morphism,
    MorphismType,
    State,
    Action,
    ActionType,
)
from nucleo.config import NucleoConfig

__all__ = [
    # Version
    "__version__",
    # Types
    "Skill",
    "Morphism",
    "MorphismType",
    "State",
    "Action",
    "ActionType",
    # Config
    "NucleoConfig",
]
