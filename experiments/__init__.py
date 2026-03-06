"""
Experimentos Go/No-Go del Nucleo Logico Evolutivo.

Puntos de decision criticos para validar el sistema.
"""

from experiments.base import Experiment, ExperimentResult, ExperimentStatus
from experiments.exp1_lean import LeanIntegrationExperiment
from experiments.exp2_graph import GraphValidationExperiment
from experiments.exp3_agent import AgentBaselineExperiment

__all__ = [
    "Experiment",
    "ExperimentResult",
    "ExperimentStatus",
    "LeanIntegrationExperiment",
    "GraphValidationExperiment",
    "AgentBaselineExperiment",
]
