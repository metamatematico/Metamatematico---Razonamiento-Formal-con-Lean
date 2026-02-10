"""
Proceso de Decision de Markov (MDP)
===================================

Formulacion formal del problema de decision del Nucleo.

Definicion 5.1: M = (X, A, P, R, γ)

Estado x = (c_L, g_Lean, G, h, m):
- c_L: Embedding del contexto LLM
- g_Lean: Goal de Lean actual
- G: Configuracion del grafo
- h: Historial de interacciones
- m: Metricas acumuladas

Acciones A = A_1 ⊔ A_2 ⊔ A_3:
- A_1: Responder al usuario
- A_2: Reorganizar el grafo
- A_3: Asistir con prueba Lean
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Any, Callable
from enum import Enum, auto
import numpy as np

from nucleo.types import State, Action, ActionType, Interaction
from nucleo.graph.category import SkillCategory


@dataclass
class Transition:
    """
    Transicion en el MDP.

    (s, a, r, s', done)
    """
    state: State
    action: Action
    reward: float
    next_state: State
    done: bool = False
    info: dict[str, Any] = field(default_factory=dict)


class MDP:
    """
    Proceso de Decision de Markov del Nucleo.

    Implementa:
    - Espacio de estados
    - Espacio de acciones
    - Dinamica de transicion
    - Funcion de recompensa
    """

    def __init__(
        self,
        graph: SkillCategory,
        gamma: float = 0.99,
        history_size: int = 10,
    ):
        """
        Inicializar MDP.

        Args:
            graph: Grafo categorico de skills
            gamma: Factor de descuento
            history_size: Tamaño del historial
        """
        self.graph = graph
        self.gamma = gamma
        self.history_size = history_size

        # Estado actual
        self._current_state: Optional[State] = None
        self._episode_reward: float = 0.0
        self._step_count: int = 0

    def reset(self) -> State:
        """
        Reiniciar el MDP.

        Returns:
            Estado inicial
        """
        self._current_state = State(
            llm_context=None,
            lean_goal=None,
            graph_snapshot=self.graph.to_dict(),
            history=[],
            metrics={
                "total_reward": 0.0,
                "steps": 0,
                "successes": 0,
                "failures": 0,
            }
        )
        self._episode_reward = 0.0
        self._step_count = 0

        return self._current_state

    def step(self, action: Action) -> Transition:
        """
        Ejecutar un paso en el MDP.

        Args:
            action: Accion a ejecutar

        Returns:
            Transicion (s, a, r, s', done)
        """
        if self._current_state is None:
            raise ValueError("MDP no inicializado. Llama reset() primero.")

        old_state = self._current_state

        # Ejecutar accion
        next_state, reward, done, info = self._execute_action(action)

        # Crear transicion
        transition = Transition(
            state=old_state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done,
            info=info
        )

        # Actualizar estado
        self._current_state = next_state
        self._episode_reward += reward
        self._step_count += 1

        return transition

    def _execute_action(
        self,
        action: Action
    ) -> Tuple[State, float, bool, dict]:
        """
        Ejecutar accion y calcular siguiente estado.

        Returns:
            (next_state, reward, done, info)
        """
        reward = 0.0
        done = False
        info = {"action_type": action.action_type.name}

        # Copiar estado actual
        new_history = list(self._current_state.history)
        new_metrics = dict(self._current_state.metrics)
        new_metrics["steps"] = self._step_count + 1

        if action.action_type == ActionType.RESPONSE:
            # Accion de respuesta
            reward = self._compute_response_reward(action)
            info["response"] = action.params.get("content", "")

            # Registrar interaccion
            interaction = Interaction(
                query="",  # Se llena externamente
                response=action.params.get("content", ""),
                success=reward > 0
            )
            new_history.append(interaction)

            # Limitar historial
            if len(new_history) > self.history_size:
                new_history = new_history[-self.history_size:]

        elif action.action_type == ActionType.REORGANIZE:
            # Accion de reorganizacion
            reward = self._compute_reorganize_reward(action)
            info["operation"] = action.params.get("operation", "")

        elif action.action_type == ActionType.ASSIST:
            # Accion de asistencia Lean
            reward = self._compute_assist_reward(action)
            info["tactic"] = action.params.get("tactic", "")
            info["goal"] = action.params.get("goal", "")

            # Si la prueba se completa, episodio termina
            if action.params.get("proof_complete", False):
                done = True
                new_metrics["successes"] += 1

        # Actualizar metricas
        new_metrics["total_reward"] = self._episode_reward + reward

        # Crear nuevo estado
        next_state = State(
            llm_context=self._current_state.llm_context,
            lean_goal=action.params.get("new_goal", self._current_state.lean_goal),
            graph_snapshot=self.graph.to_dict(),
            history=new_history,
            metrics=new_metrics
        )

        return next_state, reward, done, info

    def _compute_response_reward(self, action: Action) -> float:
        """Calcular recompensa por respuesta."""
        # Recompensa base por responder
        return 1.0

    def _compute_reorganize_reward(self, action: Action) -> float:
        """Calcular recompensa por reorganizacion."""
        operation = action.params.get("operation", "")

        # Recompensas por tipo de operacion
        rewards = {
            "add_node": 0.5,
            "add_edge": 0.3,
            "merge": 0.8,
            "split": 0.6,
            "reweight": 0.1,
        }

        return rewards.get(operation, 0.0)

    def _compute_assist_reward(self, action: Action) -> float:
        """Calcular recompensa por asistencia Lean."""
        # Exito de prueba
        if action.params.get("proof_complete", False):
            return 10.0

        # Progreso parcial
        if action.params.get("goals_reduced", False):
            return 5.0

        # Tactica valida pero sin progreso
        if action.params.get("tactic_valid", True):
            return 1.0

        # Tactica invalida
        return -1.0

    @property
    def current_state(self) -> Optional[State]:
        """Estado actual."""
        return self._current_state

    @property
    def episode_reward(self) -> float:
        """Recompensa acumulada del episodio."""
        return self._episode_reward

    def get_valid_actions(self) -> List[Action]:
        """
        Obtener acciones validas en el estado actual.

        Returns:
            Lista de acciones validas
        """
        actions = []

        # Siempre puede responder
        actions.append(Action(action_type=ActionType.RESPONSE))

        # Puede reorganizar si hay skills
        if self.graph.stats["num_skills"] > 0:
            actions.append(Action.reorganize("reweight"))

            if self.graph.stats["num_skills"] >= 2:
                actions.append(Action.reorganize("merge"))

        # Puede asistir si hay goal activo
        if self._current_state and self._current_state.has_active_goal:
            actions.append(Action(action_type=ActionType.ASSIST))

        return actions


class ExperienceBuffer:
    """
    Buffer de experiencias para entrenamiento.

    Almacena transiciones (s, a, r, s', done) para
    entrenamiento por lotes.
    """

    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.buffer: List[Transition] = []
        self.position = 0

    def push(self, transition: Transition) -> None:
        """Añadir transicion al buffer."""
        if len(self.buffer) < self.capacity:
            self.buffer.append(transition)
        else:
            self.buffer[self.position] = transition

        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int) -> List[Transition]:
        """Muestrear batch aleatorio."""
        indices = np.random.choice(
            len(self.buffer),
            size=min(batch_size, len(self.buffer)),
            replace=False
        )
        return [self.buffer[i] for i in indices]

    def __len__(self) -> int:
        return len(self.buffer)

    def clear(self) -> None:
        """Limpiar buffer."""
        self.buffer.clear()
        self.position = 0
