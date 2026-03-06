"""
Grafo Categorico de Skills
==========================

G_t = (S_t, Mor_t, w_t)

El grafo de skills es una categoria pequena enriquecida en R+:
- Objetos: Ob(Skill) = S (skills individuales)
- Morfismos: Hom(s, t) = transformaciones de s a t
- Composicion: ∘ : Hom(t, u) × Hom(s, t) → Hom(s, u)
- Identidad: id_s ∈ Hom(s, s)
- Pesos: w: Mor → R+ (fuerza/utilidad)

Tipos de morfismos:
- Dependencia (↪): t requiere s
- Especializacion (↠): t especializa s
- Analogia (↔): Isomorfismo parcial
- Traduccion (⇝): Entre pilares

Operaciones atomicas:
- add_node: O(1)
- add_edge: O(1)
- merge: O(d_max)
- split: O(d(s))
- reweight: O(1)

Axiomas:
- Conectividad: G_t es debilmente conexo
- Cobertura: Todo skill tiene camino a algun pilar
- Consistencia: Skills formales tienen traduccion verificada
"""

from nucleo.graph.category import SkillCategory, SkillGraph
from nucleo.graph.operations import GraphOperations
from nucleo.graph.embeddings import SkillEmbedding
from nucleo.graph.evolution import EvolutionarySystem, CategorySnapshot, TransitionFunctor

__all__ = [
    "SkillCategory",
    "SkillGraph",
    "GraphOperations",
    "SkillEmbedding",
    "EvolutionarySystem",
    "CategorySnapshot",
    "TransitionFunctor",
]
