"""
Redes Actor-Critic para PPO
============================

torch y torch-geometric son opcionales. Si no están disponibles,
TORCH_AVAILABLE = False y las clases degradan graciosamente.
"""

from __future__ import annotations

from typing import NamedTuple, Optional

from nucleo.rl.gnn import SkillGNN, EDGE_FEATURE_DIM, TORCH_AVAILABLE

if TORCH_AVAILABLE:
    import torch
    import torch.nn as nn

# Vocabulario fijo para encoding de queries
QUERY_VOCAB = [
    "theorem", "proof", "lemma", "lean", "sorry", "tactic",
    "prove", "formalize", "induction", "simp", "exact", "apply",
    "set", "function", "group", "ring", "category", "functor",
    "natural", "transformation", "limit", "colimit", "morphism",
    "define", "what", "how", "explain", "compute", "calculate",
    "help", "show", "verify", "check",
]
VOCAB_SIZE = len(QUERY_VOCAB) + 1  # +1 para UNK
GOAL_DIM = 32


class ActorCriticOutput(NamedTuple):
    """Salida de la red actor-critic."""
    action_logits: object
    value: object
    graph_embedding: object


def encode_query(query: str):
    """Bag-of-keywords encoding. Retorna None si torch no está disponible."""
    if not TORCH_AVAILABLE:
        return None
    counts = torch.zeros(VOCAB_SIZE)
    if not query:
        return counts
    tokens = query.lower().split()
    for token in tokens:
        if token in QUERY_VOCAB:
            counts[QUERY_VOCAB.index(token)] += 1.0
        else:
            counts[-1] += 1.0
    total = counts.sum()
    if total > 0:
        counts = counts / total
    return counts


def encode_goal(goal: str, dim: int = GOAL_DIM):
    """Encoding deterministico de un goal de Lean. Retorna None si torch no disponible."""
    if not TORCH_AVAILABLE:
        return None
    if not goal:
        return torch.zeros(dim)
    h = hash(goal) & 0xFFFFFFFF
    gen = torch.Generator()
    gen.manual_seed(h)
    vec = torch.randn(dim, generator=gen)
    norm = vec.norm()
    if norm > 0:
        vec = vec / norm
    return vec


if TORCH_AVAILABLE:
    class ActorCriticNetwork(nn.Module):  # type: ignore[no-redef]
        """Red Actor-Critic completa: GNN + Query + Goal → logits + valor."""

        def __init__(
            self,
            hidden_dim: int = 256,
            gnn_num_layers: int = 3,
            gnn_num_heads: int = 4,
            gnn_dropout: float = 0.1,
            num_actions: int = 3,
            goal_dim: int = GOAL_DIM,
        ):
            super().__init__()
            self.hidden_dim = hidden_dim
            self.goal_dim = goal_dim

            self.gnn = SkillGNN(
                hidden_dim=hidden_dim,
                num_layers=gnn_num_layers,
                num_heads=gnn_num_heads,
                dropout=gnn_dropout,
            )
            self.query_encoder = nn.Sequential(
                nn.Linear(VOCAB_SIZE, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, hidden_dim),
            )
            self.goal_encoder = nn.Sequential(
                nn.Linear(goal_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, hidden_dim),
            )
            self.fusion = nn.Sequential(
                nn.Linear(3 * hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.LayerNorm(hidden_dim),
            )
            self.actor = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, num_actions),
            )
            self.critic = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, 1),
            )

        def forward(self, graph_data, query_emb, goal_emb=None) -> ActorCriticOutput:
            g_emb = self.gnn(graph_data)
            q_emb = self.query_encoder(query_emb)
            gl_emb = self.goal_encoder(goal_emb) if goal_emb is not None else torch.zeros_like(g_emb)
            fused = self.fusion(torch.cat([g_emb, q_emb, gl_emb], dim=-1))
            return ActorCriticOutput(
                action_logits=self.actor(fused),
                value=self.critic(fused),
                graph_embedding=g_emb,
            )

else:
    class ActorCriticNetwork:  # type: ignore[no-redef]
        """Stub sin torch."""
        def __init__(self, *args, **kwargs):
            raise ImportError("torch no instalado — ActorCriticNetwork no disponible")
