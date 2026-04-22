"""
GNN Encoder para el Grafo Categorico de Skills
===============================================

Convierte SkillCategory -> torch_geometric.data.Data
y produce un embedding vectorial del grafo completo.

Arquitectura:
- Node features: pillar (one-hot 4) + level (norm) + in_deg + out_deg
                  + is_colimit + is_active = dim 9
- Edge features: morphism_type (one-hot 5) + weight = dim 6
- 3 capas GATConv con edge_attr
- Global mean pooling -> graph embedding (hidden_dim)

Nota: torch y torch-geometric son opcionales. Si no están disponibles,
TORCH_AVAILABLE = False y las clases/funciones degradan graciosamente.
"""

from __future__ import annotations

import math

try:
    import torch
    import torch.nn as nn
    from torch_geometric.nn import GATConv, global_mean_pool
    from torch_geometric.data import Data as PyGData
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from nucleo.graph.category import SkillCategory
from nucleo.types import PillarType, MorphismType, SkillStatus


# Dimensiones de features
NODE_FEATURE_DIM = 9   # pillar(4) + level(1) + in_deg(1) + out_deg(1) + is_colimit(1) + is_active(1)
EDGE_FEATURE_DIM = 6   # morphism_type(5) + weight(1)

_PILLAR_INDEX = {
    PillarType.SET: 0,
    PillarType.CAT: 1,
    PillarType.LOG: 2,
    PillarType.TYPE: 3,
}

_MORPH_INDEX = {
    MorphismType.IDENTITY: 0,
    MorphismType.DEPENDENCY: 1,
    MorphismType.SPECIALIZATION: 2,
    MorphismType.ANALOGY: 3,
    MorphismType.TRANSLATION: 4,
}


def _safe_log(value: int) -> float:
    return math.log1p(value)


def graph_to_pyg(graph: SkillCategory):
    """Convierte SkillCategory a PyG Data. Retorna None si torch no está disponible."""
    if not TORCH_AVAILABLE:
        return None

    skills = graph.skills
    num_nodes = len(skills)

    if num_nodes == 0:
        return PyGData(
            x=torch.zeros((0, NODE_FEATURE_DIM)),
            edge_index=torch.zeros((2, 0), dtype=torch.long),
            edge_attr=torch.zeros((0, EDGE_FEATURE_DIM)),
        )

    skill_id_to_idx = {s.id: i for i, s in enumerate(skills)}
    max_level = max(s.level for s in skills) or 1

    x = torch.zeros((num_nodes, NODE_FEATURE_DIM))
    for i, skill in enumerate(skills):
        node = graph._skills[skill.id]
        if skill.pillar and skill.pillar in _PILLAR_INDEX:
            x[i, _PILLAR_INDEX[skill.pillar]] = 1.0
        x[i, 4] = skill.level / max_level
        x[i, 5] = _safe_log(node.in_degree)
        x[i, 6] = _safe_log(node.out_degree)
        x[i, 7] = 1.0 if skill.pattern_ids else 0.0
        x[i, 8] = 1.0 if skill.status == SkillStatus.ACTIVE else 0.0

    src_list, tgt_list, edge_attrs = [], [], []
    for morphism in graph.morphisms:
        if morphism.morphism_type == MorphismType.IDENTITY:
            continue
        if morphism.source_id not in skill_id_to_idx:
            continue
        if morphism.target_id not in skill_id_to_idx:
            continue
        src_list.append(skill_id_to_idx[morphism.source_id])
        tgt_list.append(skill_id_to_idx[morphism.target_id])
        attr = torch.zeros(EDGE_FEATURE_DIM)
        if morphism.morphism_type in _MORPH_INDEX:
            attr[_MORPH_INDEX[morphism.morphism_type]] = 1.0
        attr[5] = morphism.weight
        edge_attrs.append(attr)

    if src_list:
        edge_index = torch.tensor([src_list, tgt_list], dtype=torch.long)
        edge_attr = torch.stack(edge_attrs)
    else:
        edge_index = torch.zeros((2, 0), dtype=torch.long)
        edge_attr = torch.zeros((0, EDGE_FEATURE_DIM))

    return PyGData(x=x, edge_index=edge_index, edge_attr=edge_attr)


if TORCH_AVAILABLE:
    class SkillGNN(nn.Module):
        """GNN Encoder del grafo de skills usando GATConv con edge features."""

        def __init__(
            self,
            hidden_dim: int = 256,
            num_layers: int = 3,
            num_heads: int = 4,
            dropout: float = 0.1,
        ):
            super().__init__()
            self.hidden_dim = hidden_dim
            self.input_proj = nn.Linear(NODE_FEATURE_DIM, hidden_dim)
            self.convs = nn.ModuleList()
            self.norms = nn.ModuleList()
            for _ in range(num_layers):
                self.convs.append(
                    GATConv(
                        in_channels=hidden_dim,
                        out_channels=hidden_dim // num_heads,
                        heads=num_heads,
                        edge_dim=EDGE_FEATURE_DIM,
                        dropout=dropout,
                        concat=True,
                    )
                )
                self.norms.append(nn.LayerNorm(hidden_dim))
            self.dropout = nn.Dropout(dropout)

        def forward(self, data) -> "torch.Tensor":
            if data.x.size(0) == 0:
                return torch.zeros(1, self.hidden_dim, device=data.x.device)
            x = self.input_proj(data.x)
            for conv, norm in zip(self.convs, self.norms):
                x_res = x
                x = conv(x, data.edge_index, edge_attr=data.edge_attr)
                x = norm(x + x_res)
                x = torch.relu(x)
                x = self.dropout(x)
            batch = getattr(data, 'batch', None)
            if batch is None:
                batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
            return global_mean_pool(x, batch)

else:
    class SkillGNN:  # type: ignore[no-redef]
        """Stub sin torch — GNN deshabilitado."""
        def __init__(self, *args, **kwargs):
            raise ImportError("torch/torch-geometric no instalado — GNN no disponible en este entorno")
