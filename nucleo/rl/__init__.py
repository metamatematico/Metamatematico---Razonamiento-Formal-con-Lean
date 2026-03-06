"""
Aprendizaje por Refuerzo del Nucleo
===================================

El Nucleo como Agente de Aprendizaje por Refuerzo.

Formulacion MDP (Definicion 5.1):
    M = (X, A, P, R, γ)

Donde:
- X: Espacio de estados
- A = A_1 ⊔ A_2 ⊔ A_3: Espacio de acciones
- P: X × A × X → [0, 1]: Dinamica de transicion
- R: X × A → R: Funcion de recompensa
- γ ∈ [0, 1): Factor de descuento

Arquitectura de Red:
    c_L     g_Lean      G
     |        |         |
     v        v         v
Transformer Goal_Enc   GNN
     \\        |        /
      \\       |       /
       v      v      v
      Multi-Head Attention
             |
        +---------+
        |         |
        v         v
    Actor π_θ  Critic V_φ
"""

from nucleo.rl.mdp import MDP, Transition
from nucleo.rl.rewards import RewardFunction, compute_reward
from nucleo.rl.agent import NucleoAgent
from nucleo.rl.gnn import SkillGNN, graph_to_pyg
from nucleo.rl.networks import ActorCriticNetwork, encode_query

__all__ = [
    "MDP",
    "Transition",
    "RewardFunction",
    "compute_reward",
    "NucleoAgent",
    "SkillGNN",
    "graph_to_pyg",
    "ActorCriticNetwork",
    "encode_query",
]
