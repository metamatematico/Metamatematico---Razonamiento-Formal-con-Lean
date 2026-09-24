"""
MultiAgentOrchestrator — enrutador de consultas a 14 agentes especializados.
=============================================================================

Flujo:
  consulta → classify_query() → SpecializedAgent[categoría] → Lean pipeline → respuesta

El orquestador mantiene los 14 agentes en memoria (lazy loading por categoría)
y registra estadísticas por agente.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from nucleo.multi_agent.specialized_agent import (
    SpecializedAgent,
    CATEGORIES,
    classify_query,
)
from nucleo.multi_agent.mes_bridge import MESBridge

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """Enrutador de consultas a 14 agentes matemáticos especializados.

    Uso básico::

        orch = MultiAgentOrchestrator()
        category, agent = orch.route("prove that sqrt(2) is irrational")
        action = agent.select_action(state)

    Uso desde Nucleo/core.py::

        orch = MultiAgentOrchestrator()
        orch.integrate_with_nucleo(nucleo_instance)
    """

    def __init__(
        self,
        lazy: bool = True,
        pattern_manager=None,
        colimit_builder=None,
        skill_graph=None,
    ):
        """
        Args:
            lazy:            Si True, los agentes se crean bajo demanda (ahorra RAM).
            pattern_manager: PatternManager del MES (opcional, para skills emergentes).
            colimit_builder: ColimitBuilder del MES (opcional).
            skill_graph:     SkillCategory global (opcional).
        """
        self.lazy = lazy

        # MES Bridge compartido por todos los agentes
        self.mes_bridge = MESBridge(
            pattern_manager=pattern_manager,
            colimit_builder=colimit_builder,
            skill_graph=skill_graph,
        )

        # Mapa categoría → agente (lazy)
        self._agents: Dict[str, SpecializedAgent] = {}

        if not lazy:
            for cat in CATEGORIES:
                self._get_agent(cat)

        logger.info(
            f"MultiAgentOrchestrator iniciado: {len(CATEGORIES)} categorías, "
            f"lazy={lazy}, MES Bridge activo"
        )

    def _get_agent(self, category: str) -> SpecializedAgent:
        """Obtiene (o crea) el agente para la categoría dada.
        Todos los agentes comparten el mismo MES Bridge.
        """
        if category not in self._agents:
            self._agents[category] = SpecializedAgent(
                category=category,
                mes_bridge=self.mes_bridge,   # Bridge MES compartido
            )
        return self._agents[category]

    def route(self, query: str) -> tuple[str, SpecializedAgent]:
        """Clasifica la consulta y retorna (categoría, agente).

        Args:
            query: Texto de la consulta matemática.

        Returns:
            Tupla (nombre_categoría, agente_especializado).
        """
        category = classify_query(query)
        agent = self._get_agent(category)
        logger.debug(f"Consulta enrutada a [{category}]: {query[:60]!r}")
        return category, agent

    def route_and_act(self, query: str, state) -> tuple[str, Any]:
        """Clasifica, obtiene agente y selecciona acción.

        Returns:
            Tupla (nombre_categoría, acción).
        """
        category, agent = self.route(query)
        action = agent.select_action(state)
        return category, action

    def record_solution(
        self,
        query: str,
        tactic: str,
        lean_result: str,
        reward: float,
        category: Optional[str] = None,
        skill_ids: Optional[List] = None,
    ) -> None:
        """Registra una solución en el MES Bridge.

        Detecta la categoría automáticamente si no se provee.
        Llama a SpecializedAgent.record_solution() que propaga al MES Bridge.

        Args:
            query:       Texto del problema
            tactic:      Táctica Lean usada
            lean_result: "success" | "partial" | "failed"
            reward:      Recompensa (0.0 - 1.0)
            category:    Categoría explícita (o None para auto-detectar)
            skill_ids:   Skills del grafo activadas
        """
        if category is None:
            category = classify_query(query)
        agent = self._get_agent(category)
        agent.record_solution(query, tactic, lean_result, reward, skill_ids)

    def update_agent(self, category: str, transitions: list) -> Dict[str, float]:
        """Pasa transiciones al agente de una categoría."""
        agent = self._get_agent(category)
        return agent.update(transitions)

    def load_all(self):
        """Fuerza la carga de todos los 14 agentes."""
        for cat in CATEGORIES:
            self._get_agent(cat)
        logger.info(f"14 agentes cargados en memoria")

    def stats(self) -> List[Dict[str, Any]]:
        """Retorna estadísticas de uso por agente."""
        result = []
        for cat in CATEGORIES:
            if cat in self._agents:
                result.append(self._agents[cat].stats())
            else:
                result.append({"category": cat, "calls": 0})
        return result

    def print_stats(self):
        """Imprime tabla de estadísticas."""
        print(f"\n{'Categoría':<20} {'Llamadas':>10}")
        print("-" * 32)
        for s in self.stats():
            print(f"{s['category']:<20} {s['calls']:>10}")

    def integrate_with_nucleo(self, nucleo):
        """Conecta el orquestador con una instancia de Nucleo.

        Reemplaza el agente único de Nucleo por el sistema multi-agente.
        El agente seleccionado depende de la categoría de cada consulta.

        Args:
            nucleo: Instancia de nucleo.core.Nucleo.
        """
        self._nucleo = nucleo
        # Guardar referencia en el nucleo para uso en core.py
        nucleo._multi_agent_orchestrator = self
        logger.info("MultiAgentOrchestrator integrado con Nucleo")

    def __repr__(self) -> str:
        loaded = len(self._agents)
        return f"MultiAgentOrchestrator(loaded={loaded}/{len(CATEGORIES)})"
