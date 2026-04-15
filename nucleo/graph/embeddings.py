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


# ─── Vocabulario semántico para embeddings ────────────────────────────────────
# 64 términos matemáticos organizados por dominio.
# Un skill que menciona "group" y "ring" quedará cerca de otros de álgebra;
# un query que mencione "topology" quedará cerca de los skills topológicos.
_SEMANTIC_VOCAB: List[str] = [
    # Fundamentos / Teoría de conjuntos (0-7)
    "set", "zfc", "axiom", "ordinal", "cardinal", "logic", "formal", "proof",
    # Teoría de categorías (8-15)
    "category", "functor", "morphism", "natural", "adjoint", "colimit", "limit", "topos",
    # Álgebra (16-23)
    "group", "ring", "field", "module", "algebra", "homomorphism", "ideal", "quotient",
    # Álgebra lineal / Representaciones (24-27)
    "linear", "vector", "matrix", "representation",
    # Análisis (28-35)
    "analysis", "real", "complex", "convergence", "integral", "derivative", "continuous", "norm",
    # Topología (36-43)
    "topology", "open", "compact", "homeomorphism", "homotopy", "homology", "manifold", "bundle",
    # Teoría de números (44-51)
    "number", "prime", "integer", "rational", "modular", "arithmetic", "elliptic", "divisibility",
    # Geometría (52-55)
    "geometry", "euclidean", "differential", "curvature",
    # Combinatoria / Probabilidad (56-59)
    "combinatorics", "graph", "probability", "stochastic",
    # Tipos / Lean / Tácticas (60-63)
    "type", "lean", "tactic", "induction",
]
_VOCAB_LEN = len(_SEMANTIC_VOCAB)  # 64

# Índice de categorías (para señal estructural que fuerza agrupación por dominio)
_CAT_TO_IDX: Dict[str, int] = {
    "foundations": 0,    "algebra": 1,       "geometry": 2,      "analysis": 3,
    "topology": 4,       "logic": 5,         "number-theory": 6, "combinatorics": 7,
    "probability": 8,    "category-theory": 9, "computation": 10, "optimization": 11,
    "lean-tactics": 12,  "proof-strategies": 13,
}
_N_CATS = 14


def semantic_embed(text: str, category: str = "", level: int = 1, dim: int = 256) -> np.ndarray:
    """
    Embedding semántico de texto matemático usando BOW sobre vocabulario fijo.

    Produce vectores donde skills con vocabulario similar (del mismo dominio)
    son geométricamente cercanos. Funciona igual para skills y para queries:
    una consulta sobre "grupos" aterrizará cerca de los skills de álgebra.

    Estructura del vector (256 dims por defecto):
      dims  0-63  → presencia de términos en el vocabulario matemático (BOW)
      dims 64-77  → señal de categoría × 5.0 (fuerza agrupación por dominio)
      dims 78-80  → nivel del skill (0=fundamentos, 1=dominio, 2=estrategias)
      dims 81-255 → relleno con cero

    Args:
        text:     Nombre + descripción del skill, o texto de una consulta
        category: Categoría del skill (ej. "algebra", "analysis")
        level:    Nivel del skill (0, 1 o 2); ignorado para queries
        dim:      Dimensión total del vector (default 256)

    Returns:
        ndarray float32 de dimensión `dim`
    """
    text_lower = text.lower().replace("-", " ").replace("_", " ")
    tokens = set(text_lower.split())

    emb = np.zeros(dim, dtype=np.float32)

    # ── Segmento 1: BOW (dims 0-63) ─────────────────────────────────────────
    for i, term in enumerate(_SEMANTIC_VOCAB):
        if i >= dim:
            break
        if term in tokens or term in text_lower:
            emb[i] = 1.0

    # Normalizar segmento BOW para que la magnitud no dependa del tamaño del texto
    bow_norm = np.linalg.norm(emb[:min(_VOCAB_LEN, dim)])
    if bow_norm > 0:
        emb[:min(_VOCAB_LEN, dim)] /= bow_norm

    # ── Segmento 2: señal de categoría (dims 64-77) ──────────────────────────
    # Peso 5.0 para que skills del mismo dominio se agrupen fuertemente en t-SNE
    cat_key = category.lower().replace(" ", "-")
    cat_idx = _CAT_TO_IDX.get(cat_key, -1)
    if 0 <= cat_idx < _N_CATS:
        target_dim = 64 + cat_idx
        if target_dim < dim:
            emb[target_dim] = 5.0

    # ── Segmento 3: nivel del skill (dims 78-80) ─────────────────────────────
    if 0 <= level <= 2:
        target_dim = 78 + level
        if target_dim < dim:
            emb[target_dim] = 3.0

    return emb


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
        # Text embedding semántico — BOW sobre vocabulario matemático
        text = f"{skill.name} {skill.description or ''}"
        category = skill.metadata.get("category", "") if skill.metadata else ""
        text_emb = self._simple_text_embedding(text, category=category, level=skill.level)

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

    def _simple_text_embedding(self, text: str, category: str = "", level: int = 1) -> np.ndarray:
        """
        Embedding semántico basado en BOW sobre vocabulario matemático fijo.

        Skills del mismo dominio quedan geométricamente cercanos porque
        comparten vocabulario técnico. Compatible con proyecciones t-SNE/PCA.
        """
        return semantic_embed(text, category=category, level=level, dim=self.text_dim)

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
