"""
Agente del Nucleo Logico
========================

Agente de RL que aprende a:
1. Seleccionar skills relevantes
2. Reorganizar el grafo
3. Asistir con pruebas Lean

Arquitectura:
- Encoder de contexto (Transformer)
- Encoder de goal (Goal Encoder)
- Encoder de grafo (GNN)
- Fusion (Multi-Head Attention)
- Actor-Critic (PPO)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
import random

from nucleo.types import State, Action, ActionType
from nucleo.graph.category import SkillCategory
from nucleo.rl.mdp import MDP, Transition, ExperienceBuffer
from nucleo.rl.rewards import RewardFunction, RewardConfig


@dataclass
class AgentConfig:
    """Configuracion del agente."""
    # Arquitectura
    hidden_dim: int = 256
    num_heads: int = 8
    num_layers: int = 3

    # Entrenamiento
    learning_rate: float = 3e-4
    gamma: float = 0.99
    batch_size: int = 64

    # PPO
    clip_range: float = 0.2
    value_coef: float = 0.5
    entropy_coef: float = 0.01

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
    - Politica aprendida (cuando este entrenado)
    - Heuristicas como fallback
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

    def select_action(self, state: State) -> Action:
        """
        Seleccionar accion.

        Usa epsilon-greedy durante entrenamiento.
        """
        self.total_steps += 1

        # Exploracion
        if self.training and random.random() < self.epsilon:
            return self._random.select_action(state)

        # Explotacion: usar heuristica por ahora
        # TODO: Usar red neuronal entrenada
        return self._heuristic.select_action(state)

    def update(self, transitions: List[Transition]) -> Dict[str, float]:
        """
        Actualizar politica con transiciones.

        Por ahora, solo actualiza metricas.
        TODO: Implementar PPO completo.
        """
        # Añadir al buffer
        for t in transitions:
            self.buffer.push(t)

        # Calcular metricas
        total_reward = sum(t.reward for t in transitions)
        self.metrics["total_reward"] += total_reward

        # Decay epsilon
        self.epsilon = max(
            self.config.epsilon_end,
            self.epsilon * self.config.epsilon_decay
        )
        self.metrics["epsilon"] = self.epsilon

        return {
            "loss": 0.0,  # TODO: Calcular loss real
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
        """
        Guardar agente.

        TODO: Guardar pesos de red.
        """
        import json
        with open(path, 'w') as f:
            json.dump({
                "config": self.config.__dict__,
                "metrics": self.metrics,
                "epsilon": self.epsilon,
                "total_steps": self.total_steps,
            }, f, indent=2)

    @classmethod
    def load(cls, path: str, graph: SkillCategory) -> NucleoAgent:
        """
        Cargar agente.

        TODO: Cargar pesos de red.
        """
        import json
        with open(path) as f:
            data = json.load(f)

        config = AgentConfig(**data["config"])
        agent = cls(graph, config)
        agent.metrics = data["metrics"]
        agent.epsilon = data["epsilon"]
        agent.total_steps = data["total_steps"]

        return agent
