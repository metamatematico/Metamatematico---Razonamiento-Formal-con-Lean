"""
Redes Actor-Critic para PPO
============================

Combina:
1. GNN embedding del grafo de skills
2. Query embedding (bag-of-keywords simple)
3. Goal embedding (hash determinista)
4. Actor head: logits para ActionType (3 clases)
5. Critic head: estimacion de valor escalar
"""

from __future__ import annotations

from typing import NamedTuple, Optional

import torch
import torch.nn as nn

from nucleo.rl.gnn import SkillGNN, EDGE_FEATURE_DIM


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

# Dimension del goal encoding
GOAL_DIM = 32


class ActorCriticOutput(NamedTuple):
    """Salida de la red actor-critic."""
    action_logits: torch.Tensor    # [batch, num_actions]
    value: torch.Tensor            # [batch, 1]
    graph_embedding: torch.Tensor  # [batch, hidden_dim]


def encode_query(query: str) -> torch.Tensor:
    """
    Bag-of-keywords encoding.

    Args:
        query: Texto del query

    Returns:
        Tensor [VOCAB_SIZE] con frecuencias normalizadas
    """
    counts = torch.zeros(VOCAB_SIZE)
    if not query:
        return counts

    tokens = query.lower().split()
    for token in tokens:
        if token in QUERY_VOCAB:
            idx = QUERY_VOCAB.index(token)
            counts[idx] += 1.0
        else:
            counts[-1] += 1.0  # UNK

    total = counts.sum()
    if total > 0:
        counts = counts / total
    return counts


def encode_goal(goal: str, dim: int = GOAL_DIM) -> torch.Tensor:
    """
    Encoding deterministico de un goal de Lean.

    Usa hash del texto para generar un vector pseudo-aleatorio reproducible.

    Args:
        goal: Texto del goal
        dim: Dimension del vector

    Returns:
        Tensor [dim]
    """
    if not goal:
        return torch.zeros(dim)

    # Usar hash para seed determinista
    h = hash(goal) & 0xFFFFFFFF
    gen = torch.Generator()
    gen.manual_seed(h)
    vec = torch.randn(dim, generator=gen)
    # Normalizar
    norm = vec.norm()
    if norm > 0:
        vec = vec / norm
    return vec


class ActorCriticNetwork(nn.Module):
    """
    Red Actor-Critic completa.

    Fusion = Linear(concat(graph_emb, query_emb, goal_emb))
    Actor = MLP -> num_actions logits
    Critic = MLP -> 1 valor
    """

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

        # 1. GNN encoder
        self.gnn = SkillGNN(
            hidden_dim=hidden_dim,
            num_layers=gnn_num_layers,
            num_heads=gnn_num_heads,
            dropout=gnn_dropout,
        )

        # 2. Query encoder
        self.query_encoder = nn.Sequential(
            nn.Linear(VOCAB_SIZE, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, hidden_dim),
        )

        # 3. Goal encoder
        self.goal_encoder = nn.Sequential(
            nn.Linear(goal_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, hidden_dim),
        )

        # 4. Fusion: concat(graph, query, goal) -> hidden_dim
        self.fusion = nn.Sequential(
            nn.Linear(3 * hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
        )

        # 5. Actor head (politica)
        self.actor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, num_actions),
        )

        # 6. Critic head (valor)
        self.critic = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(
        self,
        graph_data,
        query_emb: torch.Tensor,
        goal_emb: Optional[torch.Tensor] = None,
    ) -> ActorCriticOutput:
        """
        Forward pass.

        Args:
            graph_data: PyG Data del grafo
            query_emb: [batch, VOCAB_SIZE] embedding del query
            goal_emb: [batch, goal_dim] embedding del goal (opcional)

        Returns:
            ActorCriticOutput con logits, valor y graph embedding
        """
        # Encode grafo
        g_emb = self.gnn(graph_data)

        # Encode query
        q_emb = self.query_encoder(query_emb)

        # Encode goal
        if goal_emb is not None:
            gl_emb = self.goal_encoder(goal_emb)
        else:
            gl_emb = torch.zeros_like(g_emb)

        # Fusion
        fused = self.fusion(torch.cat([g_emb, q_emb, gl_emb], dim=-1))

        # Actor & Critic
        logits = self.actor(fused)
        value = self.critic(fused)

        return ActorCriticOutput(
            action_logits=logits,
            value=value,
            graph_embedding=g_emb,
        )
