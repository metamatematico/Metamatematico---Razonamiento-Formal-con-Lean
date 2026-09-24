"""
Agente del Nucleo Logico
========================

Agente que elige entre responder, reorganizar el grafo o asistir con Lean:
epsilon-greedy al entrenar, la memoria procedimental cuando recuerda un patrón
probado, y una heurística en lo demás.

LA RED SE QUITÓ. Hubo una política GNN+PPO: se entrenó hasta el «100 %» sobre
«todo problema matemático -> ASSIST», que se satisface con una constante, y
eso aprendió —la misma acción para un teorema, un saludo y código Lean—. El
decisor la tenía apagada por no batir a su nulo; ahora el código tampoco está.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
import random
import os

from nucleo.types import State, Action, ActionType
from nucleo.graph.category import SkillCategory
from nucleo.rl.mdp import MDP, Transition, ExperienceBuffer
from nucleo.rl.rewards import RewardFunction, RewardConfig


# Tipos de accion en orden fijo
ACTION_TYPES = [ActionType.RESPONSE, ActionType.REORGANIZE, ActionType.ASSIST]


@dataclass
class AgentConfig:
    """Configuracion del agente."""
    gamma: float = 0.99

    # Exploracion
    epsilon_start: float = 1.0
    epsilon_end: float = 0.1
    epsilon_decay: float = 0.995


class BaseAgent(ABC):
    """Clase base para agentes."""

    @abstractmethod
    def select_action(self, state: State) -> Action:
        """Seleccionar accion dado estado."""
        pass

    @abstractmethod
    def update(self, transitions: List[Transition]) -> Dict[str, float]:
        """Actualizar politica con transiciones."""
        pass


class RandomAgent(BaseAgent):
    """
    Agente aleatorio (baseline).

    Selecciona acciones uniformemente al azar.
    """

    def __init__(self, action_space: List[ActionType]):
        self.action_space = action_space

    def select_action(self, state: State) -> Action:
        """Seleccionar accion aleatoria."""
        action_type = random.choice(self.action_space)

        if action_type == ActionType.RESPONSE:
            return Action.response("Random response")
        elif action_type == ActionType.REORGANIZE:
            op = random.choice(["add_node", "reweight", "merge"])
            return Action.reorganize(op)
        else:
            return Action.assist(tactic="simp", goal="?")

    def update(self, transitions: List[Transition]) -> Dict[str, float]:
        """Agente aleatorio no aprende."""
        return {"loss": 0.0}


class HeuristicAgent(BaseAgent):
    """
    Agente heuristico.

    Usa reglas simples para seleccionar acciones.
    Sirve como baseline mejorado.
    """

    def __init__(self, graph: SkillCategory):
        self.graph = graph

    def select_action(self, state: State) -> Action:
        """Seleccionar accion usando heuristicas."""
        # Si hay goal de Lean, intentar asistir
        if state.has_active_goal:
            tactic = self._suggest_tactic(state.lean_goal)
            return Action.assist(tactic=tactic, goal=state.lean_goal)

        # Si el grafo esta desbalanceado, reorganizar
        if self._should_reorganize():
            return self._suggest_reorganization()

        # Por defecto, responder
        return Action.response("Heuristic response")

    def _suggest_tactic(self, goal: str) -> str:
        """Sugerir tactica basada en patron del goal."""
        if not goal:
            return "sorry"

        # Heuristicas simples
        if "∀" in goal or "→" in goal:
            return "intro"
        if "∧" in goal:
            return "constructor"
        if "=" in goal:
            return "rfl"
        if "∨" in goal:
            return "left"  # o right

        return "simp"

    def _should_reorganize(self) -> bool:
        """Determinar si el grafo necesita reorganizacion."""
        stats = self.graph.stats

        # Reorganizar si hay muchos skills desconectados
        if not self.graph.is_connected():
            return True

        # Reorganizar si los pesos estan muy desbalanceados
        avg_weight = stats.get("avg_weight", 1.0)
        if avg_weight < 0.5 or avg_weight > 2.0:
            return True

        return False

    def _suggest_reorganization(self) -> Action:
        """Sugerir operacion de reorganizacion."""
        if not self.graph.is_connected():
            return Action.reorganize("add_edge")

        return Action.reorganize("reweight")

    def update(self, transitions: List[Transition]) -> Dict[str, float]:
        """Agente heuristico no aprende."""
        return {"loss": 0.0}


class NucleoAgent(BaseAgent):
    """
    Agente principal del Nucleo Logico.

    Combina:
    - Exploracion epsilon-greedy
    - La memoria procedimental, cuando recuerda un patron probado
    - Heuristicas en lo demas
    """

    def __init__(
        self,
        graph: SkillCategory,
        config: Optional[AgentConfig] = None,
    ):
        self.graph = graph
        self.config = config or AgentConfig()

        # Estado de entrenamiento
        self.epsilon = self.config.epsilon_start
        self.total_steps = 0
        self.training = True

        # Agentes auxiliares
        self._heuristic = HeuristicAgent(graph)
        self._random = RandomAgent([
            ActionType.RESPONSE,
            ActionType.REORGANIZE,
            ActionType.ASSIST
        ])

        # Buffer de experiencia
        self.buffer = ExperienceBuffer(capacity=10000)

        # Metricas
        self.metrics = {
            "episodes": 0,
            "total_reward": 0.0,
            "avg_reward": 0.0,
            "epsilon": self.epsilon,
        }

        self._procedural_memory = None  # Set externally for memory-guided decisions

    def select_action(self, state: State) -> Action:
        """
        Seleccionar accion.

        Usa epsilon-greedy durante entrenamiento; si la memoria procedimental
        recuerda un patron probado para esta consulta, lo usa; si no, la
        heuristica.
        """
        self.total_steps += 1

        # Exploracion epsilon-greedy
        if self.training and random.random() < self.epsilon:
            return self._random.select_action(state)

        recordada = self._select_memoria(state)
        if recordada is not None:
            return recordada
        return self._heuristic.select_action(state)

    def _select_memoria(self, state: State) -> Optional[Action]:
        """La accion de un patron que ya funciono (exito >= 0,8), o None."""
        if self._procedural_memory is None:
            return None
        query_text = state.lean_goal or ""
        best_proc = self._procedural_memory.get_best_for_query(query_text)
        if best_proc is None or best_proc.success_rate < 0.8:
            return None
        action_name = best_proc.action_sequence[0] if best_proc.action_sequence else "RESPONSE"
        try:
            chosen = ActionType[action_name]
        except KeyError:
            chosen = ActionType.RESPONSE
        best_proc.invoke()
        if chosen == ActionType.RESPONSE:
            return Action.response("Memory pattern: respond")
        if chosen == ActionType.REORGANIZE:
            return self._heuristic._suggest_reorganization()
        tactic = best_proc.tactic_used or self._heuristic._suggest_tactic(query_text)
        return Action.assist(tactic=tactic, goal=query_text)

    def update(self, transitions: List[Transition]) -> Dict[str, float]:
        """Anadir transiciones al buffer, acumular recompensa y decaer epsilon."""
        for t in transitions:
            self.buffer.push(t)

        total_reward = sum(t.reward for t in transitions)
        self.metrics["total_reward"] += total_reward

        self.epsilon = max(
            self.config.epsilon_end,
            self.epsilon * self.config.epsilon_decay
        )
        self.metrics["epsilon"] = self.epsilon

        return {
            "reward": total_reward,
            "buffer_size": len(self.buffer),
        }

    def train_episode(self, mdp: MDP, max_steps: int = 100) -> Dict[str, float]:
        """
        Entrenar un episodio completo.

        Args:
            mdp: MDP del nucleo
            max_steps: Pasos maximos por episodio

        Returns:
            Metricas del episodio
        """
        state = mdp.reset()
        transitions = []
        episode_reward = 0.0

        for step in range(max_steps):
            # Seleccionar y ejecutar accion
            action = self.select_action(state)
            transition = mdp.step(action)

            transitions.append(transition)
            episode_reward += transition.reward

            if transition.done:
                break

            state = transition.next_state

        # Actualizar
        update_metrics = self.update(transitions)

        self.metrics["episodes"] += 1
        self.metrics["avg_reward"] = (
            self.metrics["total_reward"] / self.metrics["episodes"]
        )

        return {
            "episode_reward": episode_reward,
            "episode_length": len(transitions),
            **update_metrics,
        }

    def eval_mode(self) -> None:
        """Cambiar a modo evaluacion."""
        self.training = False

    def train_mode(self) -> None:
        """Cambiar a modo entrenamiento."""
        self.training = True

    def save(self, path: str) -> None:
        """Guardar agente (config + metricas)."""
        import json
        with open(path, 'w', encoding="utf-8") as f:
            json.dump({
                "config": self.config.__dict__,
                "metrics": self.metrics,
                "epsilon": self.epsilon,
                "total_steps": self.total_steps,
            }, f, indent=2)

    @classmethod
    def load(cls, path: str, graph: SkillCategory) -> NucleoAgent:
        """Cargar agente (config + metricas). Ignora campos de la red retirada."""
        import json
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        campos = set(AgentConfig.__dataclass_fields__)
        config = AgentConfig(**{k: v for k, v in data["config"].items() if k in campos})
        agent = cls(graph, config)
        agent.metrics = data["metrics"]
        agent.epsilon = data["epsilon"]
        agent.total_steps = data["total_steps"]
        return agent
