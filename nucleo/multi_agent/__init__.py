"""
Multi-Agent System for NLE v7.0
================================

14 specialized agents, one per mathematical category.
"""

from nucleo.multi_agent.orchestrator import MultiAgentOrchestrator
from nucleo.multi_agent.specialized_agent import SpecializedAgent, CATEGORIES
from nucleo.multi_agent.mes_bridge import MESBridge
from nucleo.multi_agent.colimit_agents import ColimitAgent, ColimitAgentSystem
from nucleo.multi_agent.pillar_agents import PillarAgent, PillarAgentSystem, PILLARS

__all__ = [
    "MultiAgentOrchestrator",
    "SpecializedAgent",
    "CATEGORIES",
    "MESBridge",
    "ColimitAgent",
    "ColimitAgentSystem",
    "PillarAgent",
    "PillarAgentSystem",
    "PILLARS",
]
