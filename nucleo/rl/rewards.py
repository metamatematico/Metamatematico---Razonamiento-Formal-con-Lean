"""
Funcion de Recompensa - MES v7.0
================================

R(x, a) = r_task + lambda_1*r_e + lambda_2*r_org + lambda_3*r_emerge
                 + lambda_4*r_hierarchy + lambda_5*r_memory

Componentes (Definicion 4.3 + MES v7.0):
- r_task in {-5, -1, +1, +5, +10}: Exito de tarea
- r_e = -alpha*|S'| - beta*Dt: Eficiencia
- r_org = delta*DC(G) + epsilon*Dk(G): Organizacion
- r_emerge = eta*1[patron_nuevo]: Emergencia
- r_hierarchy: Calidad de jerarquia de niveles (MES)
- r_memory: Consolidacion de memoria (MES)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

from nucleo.types import State, Action, ActionType, RewardComponents
from nucleo.graph.category import SkillCategory


class TaskResult(Enum):
    """Resultados de tarea con recompensas fijas."""
    CRITICAL_FAILURE = -5   # Error grave
    FAILURE = -1            # Fallo menor
    NEUTRAL = 0             # Sin efecto
    SUCCESS = 1             # Exito parcial
    GOOD_SUCCESS = 5        # Buen exito
    EXCELLENT = 10          # Exito completo


@dataclass
class RewardConfig:
    """Configuracion de recompensas (v6.0 + MES v7.0)."""
    # Pesos lambda (v6.0)
    lambda_1: float = 0.1   # Eficiencia
    lambda_2: float = 0.05  # Organizacion
    lambda_3: float = 0.2   # Emergencia

    # Pesos lambda (MES v7.0)
    lambda_4: float = 0.1   # Jerarquia de niveles
    lambda_5: float = 0.08  # Consolidacion memoria

    # Penalizaciones
    alpha: float = 0.1      # Por skill usado
    beta: float = 0.01      # Por tiempo

    # Bonuses organizacion
    delta: float = 0.5      # Coherencia
    epsilon: float = 0.3    # Cobertura

    # Bonus emergencia
    eta: float = 2.0        # Patron nuevo

    # Bonuses MES v7.0
    zeta: float = 1.5       # Por nuevo nivel alcanzado
    theta: float = 1.0      # Por E-concepto formado


class RewardFunction:
    """
    Funcion de recompensa del Nucleo (MES v7.0).

    Calcula R(x, a) combinando los seis componentes:
    - r_task, r_efficiency, r_organization, r_emergence (v6.0)
    - r_hierarchy, r_memory (MES v7.0)
    """

    def __init__(self, config: Optional[RewardConfig] = None):
        self.config = config or RewardConfig()
        self._prev_max_level = 0
        self._prev_num_econcepts = 0

    def compute(
        self,
        state: State,
        action: Action,
        next_state: State,
        graph: SkillCategory,
        task_result: Optional[TaskResult] = None,
        skills_used: int = 0,
        time_delta: float = 0.0,
        new_pattern_detected: bool = False,
        new_level_reached: bool = False,
        econcept_formed: bool = False,
        pattern_coverage: float = 0.0,
    ) -> RewardComponents:
        """
        Calcular componentes de recompensa.

        Args:
            state: Estado anterior
            action: Accion ejecutada
            next_state: Estado resultante
            graph: Grafo categorico
            task_result: Resultado de la tarea
            skills_used: Numero de skills usados
            time_delta: Tiempo transcurrido
            new_pattern_detected: Si se detecto patron nuevo
            new_level_reached: Si se alcanzo nuevo nivel jerarquico (MES)
            econcept_formed: Si se formo nuevo E-concepto (MES)
            pattern_coverage: Proporcion de skills cubiertos por patrones (MES)

        Returns:
            RewardComponents con todos los componentes
        """
        # r_task: Recompensa de tarea
        r_task = self._compute_task_reward(action, task_result)

        # r_e: Eficiencia
        r_e = self._compute_efficiency_reward(skills_used, time_delta)

        # r_org: Organizacion
        r_org = self._compute_organization_reward(state, next_state, graph)

        # r_emerge: Emergencia
        r_emerge = self._compute_emergence_reward(new_pattern_detected)

        # r_hierarchy: Jerarquia (MES v7.0)
        r_hierarchy = self._compute_hierarchy_reward(
            graph, new_level_reached
        )

        # r_memory: Memoria (MES v7.0)
        r_memory = self._compute_memory_reward(
            graph, econcept_formed, pattern_coverage
        )

        return RewardComponents(
            r_task=r_task,
            r_efficiency=r_e,
            r_organization=r_org,
            r_emergence=r_emerge,
            r_hierarchy=r_hierarchy,
            r_memory=r_memory,
        )

    def _compute_task_reward(
        self,
        action: Action,
        task_result: Optional[TaskResult]
    ) -> float:
        """
        r_task ∈ {-5, -1, +1, +5, +10}
        """
        if task_result is not None:
            return float(task_result.value)

        # Recompensas por defecto segun tipo de accion
        default_rewards = {
            ActionType.RESPONSE: TaskResult.SUCCESS.value,
            ActionType.REORGANIZE: TaskResult.NEUTRAL.value,
            ActionType.ASSIST: TaskResult.SUCCESS.value,
        }

        return float(default_rewards.get(action.action_type, 0))

    def _compute_efficiency_reward(
        self,
        skills_used: int,
        time_delta: float
    ) -> float:
        """
        r_e = -α|S'| - β·Δt

        Penaliza usar muchos skills y tardar mucho.
        """
        penalty_skills = self.config.alpha * skills_used
        penalty_time = self.config.beta * time_delta

        return -(penalty_skills + penalty_time)

    def _compute_organization_reward(
        self,
        state: State,
        next_state: State,
        graph: SkillCategory
    ) -> float:
        """
        r_org = δ·ΔC(G) + ε·Δκ(G)

        Recompensa mejoras en coherencia y cobertura.
        """
        # Metricas de organizacion
        coherence = self._compute_coherence(graph)
        coverage = self._compute_coverage(graph)

        # Por ahora, usar metricas directas
        # TODO: Calcular deltas respecto al estado anterior
        r_coherence = self.config.delta * coherence
        r_coverage = self.config.epsilon * coverage

        return r_coherence + r_coverage

    def _compute_emergence_reward(
        self,
        new_pattern_detected: bool
    ) -> float:
        """
        r_emerge = eta*1[patron_nuevo]

        Bonus por descubrir patrones nuevos.
        """
        if new_pattern_detected:
            return self.config.eta
        return 0.0

    def _compute_hierarchy_reward(
        self,
        graph: SkillCategory,
        new_level_reached: bool
    ) -> float:
        """
        r_hierarchy (MES v7.0): Calidad de estructura jerarquica.

        Componentes:
        1. Score de jerarquia del grafo
        2. Bonus por alcanzar nuevo nivel
        """
        # Score base de jerarquia
        hierarchy_score = graph.get_hierarchy_score()

        # Bonus por nuevo nivel
        level_bonus = 0.0
        if new_level_reached:
            level_bonus = self.config.zeta

        return hierarchy_score + level_bonus

    def _compute_memory_reward(
        self,
        graph: SkillCategory,
        econcept_formed: bool,
        pattern_coverage: float
    ) -> float:
        """
        r_memory (MES v7.0): Consolidacion de memoria.

        Componentes:
        1. Score de memoria del grafo
        2. Bonus por formacion de E-concepto
        """
        # Score base de memoria
        memory_score = graph.get_memory_score(pattern_coverage)

        # Bonus por E-concepto
        econcept_bonus = 0.0
        if econcept_formed:
            econcept_bonus = self.config.theta

        return memory_score + econcept_bonus

    def _compute_coherence(self, graph: SkillCategory) -> float:
        """
        Calcular coherencia del grafo.

        C(G) = clustering_coefficient
        """
        # Simplificado: proporcion de conexiones
        num_skills = graph.stats["num_skills"]
        num_morphisms = graph.stats["num_morphisms"]

        if num_skills <= 1:
            return 1.0

        # Maximo posible de morfismos (sin identidades)
        max_morphisms = num_skills * (num_skills - 1)

        if max_morphisms == 0:
            return 1.0

        # Normalizar (restar identidades)
        actual = max(0, num_morphisms - num_skills)
        return min(1.0, actual / max_morphisms)

    def _compute_coverage(self, graph: SkillCategory) -> float:
        """
        Calcular cobertura fundacional.

        κ(G) = proporcion de skills conectados a pilares
        """
        # Simplificado: verificar conectividad
        if graph.is_connected():
            return 1.0

        # TODO: Calcular cobertura real por pilares
        return 0.5


def compute_reward(
    state: State,
    action: Action,
    next_state: State,
    graph: SkillCategory,
    config: Optional[RewardConfig] = None,
    **kwargs
) -> float:
    """
    Funcion de conveniencia para calcular recompensa total.

    Args:
        state: Estado anterior
        action: Accion ejecutada
        next_state: Estado resultante
        graph: Grafo categorico
        config: Configuracion de recompensas
        **kwargs: Argumentos adicionales para RewardFunction.compute

    Returns:
        Recompensa total (incluyendo terminos MES v7.0)
    """
    reward_fn = RewardFunction(config)
    components = reward_fn.compute(
        state=state,
        action=action,
        next_state=next_state,
        graph=graph,
        **kwargs
    )

    cfg = config or RewardConfig()
    return components.total(
        lambda_1=cfg.lambda_1,
        lambda_2=cfg.lambda_2,
        lambda_3=cfg.lambda_3,
        lambda_4=cfg.lambda_4,
        lambda_5=cfg.lambda_5,
    )
