"""
Agente del Nucleo Logico
========================

Agente de RL que aprende a:
1. Seleccionar skills relevantes
2. Reorganizar el grafo
3. Asistir con pruebas Lean

Arquitectura:
- Encoder de grafo (GNN con GATConv)
- Encoder de query (bag-of-keywords)
- Encoder de goal (hash determinista)
- Fusion (concat + Linear)
- Actor-Critic (PPO con GAE)
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


# Tipos de accion en orden fijo (indices para la red neuronal)
ACTION_TYPES = [ActionType.RESPONSE, ActionType.REORGANIZE, ActionType.ASSIST]


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
    gae_lambda: float = 0.95
    n_epochs: int = 4

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
    - Politica aprendida via PPO con GNN (cuando use_neural=True)
    - Heuristicas como fallback
    """

    def __init__(
        self,
        graph: SkillCategory,
        config: Optional[AgentConfig] = None,
        use_neural: bool = False,
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

        # Red neuronal (opt-in)
        self._use_neural = use_neural
        self._network = None
        self._optimizer = None
        self._procedural_memory = None  # Set externally for memory-guided decisions

        if use_neural:
            self._init_network()

    def _init_network(self) -> None:
        """Inicializar red neuronal actor-critic."""
        import torch
        from nucleo.rl.networks import ActorCriticNetwork

        self._network = ActorCriticNetwork(
            hidden_dim=self.config.hidden_dim,
            gnn_num_layers=self.config.num_layers,
            gnn_num_heads=self.config.num_heads,
        )
        self._optimizer = torch.optim.Adam(
            self._network.parameters(),
            lr=self.config.learning_rate,
        )

    @property
    def has_network(self) -> bool:
        """Verificar si la red neuronal esta disponible."""
        return self._network is not None

    def select_action(self, state: State) -> Action:
        """
        Seleccionar accion.

        Usa epsilon-greedy durante entrenamiento.
        Si hay red neuronal, la usa para explotacion.
        """
        self.total_steps += 1

        # Exploracion epsilon-greedy
        if self.training and random.random() < self.epsilon:
            return self._random.select_action(state)

        # Explotacion con red neuronal
        if self._network is not None:
            return self._select_neural(state)

        # Fallback a heuristica
        return self._heuristic.select_action(state)

    def _select_neural(self, state: State) -> Action:
        """Seleccionar accion usando memoria de patrones o red neuronal."""
        # Check procedural memory first for proven patterns
        if self._procedural_memory is not None:
            query_text = state.lean_goal or ""
            best_proc = self._procedural_memory.get_best_for_query(query_text)
            if best_proc is not None and best_proc.success_rate >= 0.8:
                # Use proven action from memory
                action_name = best_proc.action_sequence[0] if best_proc.action_sequence else "RESPONSE"
                try:
                    chosen = ActionType[action_name]
                except KeyError:
                    chosen = ActionType.RESPONSE
                best_proc.invoke()
                if chosen == ActionType.RESPONSE:
                    return Action.response("Memory pattern: respond")
                elif chosen == ActionType.REORGANIZE:
                    return self._heuristic._suggest_reorganization()
                else:
                    tactic = best_proc.tactic_used or self._heuristic._suggest_tactic(query_text)
                    return Action.assist(tactic=tactic, goal=query_text)

        # Fall back to neural network
        import torch
        from nucleo.rl.gnn import graph_to_pyg
        from nucleo.rl.networks import encode_query, encode_goal

        self._network.eval()
        with torch.no_grad():
            graph_data = graph_to_pyg(self.graph)
            query_text = state.lean_goal or ""
            query_emb = encode_query(query_text).unsqueeze(0)

            goal_emb = None
            if state.lean_goal:
                goal_emb = encode_goal(state.lean_goal).unsqueeze(0)

            output = self._network(graph_data, query_emb, goal_emb=goal_emb)
            probs = torch.softmax(output.action_logits, dim=-1)
            action_idx = torch.multinomial(probs, 1).item()

        chosen = ACTION_TYPES[action_idx]

        # Delegar parametros especificos a la heuristica
        if chosen == ActionType.RESPONSE:
            return Action.response("Neural policy: respond")
        elif chosen == ActionType.REORGANIZE:
            return self._heuristic._suggest_reorganization()
        else:
            tactic = self._heuristic._suggest_tactic(state.lean_goal or "")
            return Action.assist(tactic=tactic, goal=state.lean_goal or "")

    def update(self, transitions: List[Transition]) -> Dict[str, float]:
        """
        Actualizar politica con transiciones.

        Si la red neuronal esta disponible y hay suficientes datos,
        ejecuta actualizacion PPO.
        """
        # Anadir al buffer
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

        # PPO update si hay red y suficientes transiciones
        ppo_loss = 0.0
        if self._network is not None and len(transitions) >= 2:
            ppo_loss = self._ppo_update(transitions)

        return {
            "loss": ppo_loss,
            "reward": total_reward,
            "buffer_size": len(self.buffer),
        }

    def _ppo_update(self, transitions: List[Transition]) -> float:
        """
        Actualizacion PPO con GAE.

        1. Calcular ventajas via GAE(lambda)
        2. Multiples epocas de minibatch
        3. Clipped surrogate objective
        4. Value loss + entropy bonus
        """
        import torch
        import torch.nn.functional as F
        from nucleo.rl.gnn import graph_to_pyg
        from nucleo.rl.networks import encode_query, encode_goal

        self._network.train()
        gamma = self.config.gamma
        gae_lambda = self.config.gae_lambda

        # Preparar datos del rollout
        graph_data = graph_to_pyg(self.graph)
        rewards = torch.tensor([t.reward for t in transitions], dtype=torch.float32)
        dones = torch.tensor([t.done for t in transitions], dtype=torch.float32)

        # Codificar queries para cada transicion
        query_embs = []
        goal_embs = []
        action_indices = []
        for t in transitions:
            q_text = t.state.lean_goal or ""
            query_embs.append(encode_query(q_text))
            goal_embs.append(encode_goal(q_text))
            action_indices.append(ACTION_TYPES.index(t.action.action_type))

        query_batch = torch.stack(query_embs)
        goal_batch = torch.stack(goal_embs)
        action_batch = torch.tensor(action_indices, dtype=torch.long)

        # Expandir graph_data para el batch (mismo grafo para todas las transiciones)
        from torch_geometric.data import Batch
        batch_size = len(transitions)
        graph_batch = Batch.from_data_list([graph_data] * batch_size)

        # Forward pass para obtener old log_probs y values
        with torch.no_grad():
            output = self._network(graph_batch, query_batch, goal_emb=goal_batch)
            old_log_probs = F.log_softmax(output.action_logits, dim=-1)
            old_log_probs = old_log_probs.gather(1, action_batch.unsqueeze(1)).squeeze(1)
            values = output.value.squeeze(1)

        # Calcular GAE
        advantages = torch.zeros_like(rewards)
        returns = torch.zeros_like(rewards)
        gae = 0.0
        next_value = 0.0

        for t in reversed(range(len(transitions))):
            delta = rewards[t] + gamma * next_value * (1 - dones[t]) - values[t]
            gae = delta + gamma * gae_lambda * (1 - dones[t]) * gae
            advantages[t] = gae
            returns[t] = advantages[t] + values[t]
            next_value = values[t]

        # Normalizar ventajas
        if advantages.std() > 0:
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # PPO epochs
        total_loss = 0.0
        for _ in range(self.config.n_epochs):
            output = self._network(graph_batch, query_batch, goal_emb=goal_batch)
            new_log_probs = F.log_softmax(output.action_logits, dim=-1)
            new_log_probs = new_log_probs.gather(1, action_batch.unsqueeze(1)).squeeze(1)
            new_values = output.value.squeeze(1)

            # Ratio
            ratio = torch.exp(new_log_probs - old_log_probs.detach())

            # Clipped surrogate
            surr1 = ratio * advantages.detach()
            surr2 = torch.clamp(ratio, 1.0 - self.config.clip_range, 1.0 + self.config.clip_range) * advantages.detach()
            policy_loss = -torch.min(surr1, surr2).mean()

            # Value loss
            value_loss = F.mse_loss(new_values, returns.detach())

            # Entropy bonus
            probs = torch.softmax(output.action_logits, dim=-1)
            entropy = -(probs * probs.clamp(min=1e-8).log()).sum(dim=-1).mean()

            # Loss total
            loss = (
                policy_loss
                + self.config.value_coef * value_loss
                - self.config.entropy_coef * entropy
            )

            self._optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self._network.parameters(), 0.5)
            self._optimizer.step()

            total_loss += loss.item()

        return total_loss / self.config.n_epochs

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
        """Guardar agente (config + metricas + pesos de red)."""
        import json
        with open(path, 'w') as f:
            json.dump({
                "config": self.config.__dict__,
                "metrics": self.metrics,
                "epsilon": self.epsilon,
                "total_steps": self.total_steps,
                "use_neural": self._use_neural,
            }, f, indent=2)

        # Guardar pesos de la red neuronal
        if self._network is not None:
            import torch
            torch.save(self._network.state_dict(), path + ".pt")

    @classmethod
    def load(cls, path: str, graph: SkillCategory) -> NucleoAgent:
        """Cargar agente (config + metricas + pesos de red)."""
        import json
        with open(path) as f:
            data = json.load(f)

        use_neural = data.get("use_neural", False)
        config = AgentConfig(**data["config"])
        agent = cls(graph, config, use_neural=use_neural)
        agent.metrics = data["metrics"]
        agent.epsilon = data["epsilon"]
        agent.total_steps = data["total_steps"]

        # Cargar pesos si existen
        pt_path = path + ".pt"
        if os.path.exists(pt_path) and agent._network is not None:
            import torch
            agent._network.load_state_dict(
                torch.load(pt_path, weights_only=True)
            )

        return agent
