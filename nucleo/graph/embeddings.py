r"""
Embeddings de Skills
====================

Representaciones vectoriales de skills para:
- GNN (Graph Neural Network)
- Busqueda de similaridad
- Clustering

Arquitectura de red (Seccion 4.5)::

    c_L     g_Lean      G
     |        |         |
     v        v         v
Transformer Goal_Enc   GNN
     \        |        /
      \       |       /
       v      v      v
      Multi-Head Attention
             |
        +---------+
        |         |
        v         v
    Actor pi    Critic V
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import numpy as np

from nucleo.types import Skill
from nucleo.graph.category import SkillCategory


@dataclass
class SkillEmbedding:
    """
    Embedding de un skill.

    Combina:
    - Embedding textual (nombre + descripcion)
    - Embedding estructural (posicion en grafo)
    - Features adicionales
    """
    skill_id: str
    text_embedding: np.ndarray = field(default_factory=lambda: np.zeros(256))
    structure_embedding: np.ndarray = field(default_factory=lambda: np.zeros(64))
    features: Dict[str, float] = field(default_factory=dict)

    @property
    def combined(self) -> np.ndarray:
        """Embedding combinado."""
        return np.concatenate([
            self.text_embedding,
            self.structure_embedding,
            np.array(list(self.features.values()))
        ])

    @property
    def dim(self) -> int:
        """Dimension total del embedding."""
        return len(self.combined)


class SkillEmbeddingModel:
    """
    Modelo para generar embeddings de skills.

    Componentes:
    - Text encoder: Embeddings de texto (nombre, descripcion)
    - Structure encoder: Embeddings de estructura (GNN)
    - Feature extractor: Features adicionales
    """

    def __init__(
        self,
        text_dim: int = 256,
        structure_dim: int = 64,
        use_gnn: bool = False
    ):
        self.text_dim = text_dim
        self.structure_dim = structure_dim
        self.use_gnn = use_gnn
        self._embeddings: Dict[str, SkillEmbedding] = {}

    def embed_skill(
        self,
        skill: Skill,
        graph: Optional[SkillCategory] = None
    ) -> SkillEmbedding:
        """
        Generar embedding para un skill.

        Args:
            skill: Skill a embeber
            graph: Grafo categorico (para estructura)

        Returns:
            SkillEmbedding
        """
        # Text embedding (placeholder - usar modelo real)
        text = f"{skill.name} {skill.description}"
        text_emb = self._simple_text_embedding(text)

        # Structure embedding
        if graph and self.use_gnn:
            struct_emb = self._compute_structure_embedding(skill.id, graph)
        else:
            struct_emb = np.zeros(self.structure_dim)

        # Features
        features = self._extract_features(skill, graph)

        embedding = SkillEmbedding(
            skill_id=skill.id,
            text_embedding=text_emb,
            structure_embedding=struct_emb,
            features=features
        )

        self._embeddings[skill.id] = embedding
        return embedding

    def embed_graph(self, graph: SkillCategory) -> Dict[str, SkillEmbedding]:
        """
        Generar embeddings para todos los skills del grafo.
        """
        embeddings = {}
        for skill in graph.skills:
            embeddings[skill.id] = self.embed_skill(skill, graph)
        self._embeddings.update(embeddings)
        return embeddings

    def similarity(
        self,
        skill_id_1: str,
        skill_id_2: str
    ) -> float:
        """
        Calcular similaridad coseno entre dos skills.
        """
        emb1 = self._embeddings.get(skill_id_1)
        emb2 = self._embeddings.get(skill_id_2)

        if not emb1 or not emb2:
            return 0.0

        vec1 = emb1.combined
        vec2 = emb2.combined

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def find_similar(
        self,
        skill_id: str,
        top_k: int = 5
    ) -> List[tuple[str, float]]:
        """
        Encontrar skills mas similares.
        """
        if skill_id not in self._embeddings:
            return []

        similarities = []
        for other_id in self._embeddings:
            if other_id != skill_id:
                sim = self.similarity(skill_id, other_id)
                similarities.append((other_id, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _simple_text_embedding(self, text: str) -> np.ndarray:
        """
        Embedding de texto simple (placeholder).

        En produccion, usar sentence-transformers o similar.
        """
        # Hash simple para generar vector
        np.random.seed(hash(text) % (2**32))
        return np.random.randn(self.text_dim).astype(np.float32)

    def _compute_structure_embedding(
        self,
        skill_id: str,
        graph: SkillCategory
    ) -> np.ndarray:
        """
        Embedding de estructura del grafo.

        Features estructurales:
        - In-degree, out-degree
        - Clustering coefficient local
        - Distancia a pilares
        """
        node = graph._skills.get(skill_id)
        if not node:
            return np.zeros(self.structure_dim)

        # Features basicas
        in_deg = node.in_degree
        out_deg = node.out_degree
        total_deg = in_deg + out_deg

        # Normalizar y crear vector
        features = np.array([
            in_deg / max(1, graph.stats["num_skills"]),
            out_deg / max(1, graph.stats["num_skills"]),
            total_deg / max(1, 2 * graph.stats["num_skills"]),
        ])

        # Padding a dimension deseada
        result = np.zeros(self.structure_dim)
        result[:len(features)] = features

        return result.astype(np.float32)

    def _extract_features(
        self,
        skill: Skill,
        graph: Optional[SkillCategory]
    ) -> Dict[str, float]:
        """
        Extraer features adicionales del skill.
        """
        features = {}

        # Pilar (one-hot encoding)
        from nucleo.types import PillarType
        for pillar in PillarType:
            features[f"pillar_{pillar.name}"] = 1.0 if skill.pillar == pillar else 0.0

        # Status
        features["is_active"] = 1.0 if skill.status.name == "ACTIVE" else 0.0

        # Estructura (si hay grafo)
        if graph:
            features["num_dependencies"] = len(graph.dependencies(skill.id))
            features["num_dependents"] = len(graph.dependents(skill.id))

        return features


class GraphEmbedding:
    """
    Embedding del grafo completo.

    Usado para representar el estado G en el MDP.
    """

    def __init__(self, dim: int = 128):
        self.dim = dim

    def embed(self, graph: SkillCategory) -> np.ndarray:
        """
        Generar embedding del grafo completo.

        Agrega informacion de:
        - Estadisticas globales
        - Distribucion de grados
        - Estructura de clusters
        """
        stats = graph.stats

        features = np.array([
            stats["num_skills"] / 1000,  # Normalizado
            stats["num_morphisms"] / 10000,
            stats.get("avg_weight", 0),
        ])

        # Padding
        result = np.zeros(self.dim)
        result[:len(features)] = features

        return result.astype(np.float32)
