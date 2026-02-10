"""
Operaciones Atomicas del Grafo
==============================

Definicion 4.3 del documento v6.0:

| Operacion    | Signatura              | Complejidad |
|--------------|------------------------|-------------|
| add_node     | G_t × s_new → G_{t+1}  | O(1)        |
| add_edge     | G_t × (s,t,f) → G_{t+1}| O(1)        |
| merge        | G_t × (s1,s2) → G_{t+1}| O(d_max)    |
| split        | G_t × s → G_{t+1}      | O(d(s))     |
| reweight     | G_t × (f,w') → G_{t+1} | O(1)        |

Teorema 7.4: Si G_t es categoria valida, G_{t+1} tambien lo es.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Tuple
import uuid

from nucleo.types import Skill, Morphism, MorphismType, PillarType
from nucleo.graph.category import SkillCategory


@dataclass
class OperationResult:
    """Resultado de una operacion sobre el grafo."""
    success: bool
    message: str = ""
    affected_skills: list[str] = None
    affected_morphisms: list[str] = None

    def __post_init__(self):
        if self.affected_skills is None:
            self.affected_skills = []
        if self.affected_morphisms is None:
            self.affected_morphisms = []


class GraphOperations:
    """
    Operaciones atomicas sobre el grafo categorico.

    Todas las operaciones preservan la estructura categorica:
    - Asociatividad de composicion
    - Existencia de identidades
    """

    @staticmethod
    def add_node(
        graph: SkillCategory,
        name: str,
        description: str = "",
        pillar: Optional[PillarType] = None,
        **metadata
    ) -> OperationResult:
        """
        Añadir nuevo skill al grafo.

        Complejidad: O(1)

        Args:
            graph: Grafo categorico
            name: Nombre del skill
            description: Descripcion del skill
            pillar: Pilar fundacional
            **metadata: Metadatos adicionales

        Returns:
            OperationResult con ID del skill creado
        """
        skill = Skill(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            pillar=pillar,
            metadata=metadata
        )

        graph.add_skill(skill)

        return OperationResult(
            success=True,
            message=f"Skill '{name}' added",
            affected_skills=[skill.id]
        )

    @staticmethod
    def add_edge(
        graph: SkillCategory,
        source_id: str,
        target_id: str,
        morphism_type: MorphismType = MorphismType.DEPENDENCY,
        weight: float = 1.0
    ) -> OperationResult:
        """
        Añadir morfismo entre skills.

        Complejidad: O(1)

        Args:
            graph: Grafo categorico
            source_id: ID del skill origen
            target_id: ID del skill destino
            morphism_type: Tipo de morfismo
            weight: Peso del morfismo

        Returns:
            OperationResult con ID del morfismo creado
        """
        morphism = graph.add_morphism(
            source_id=source_id,
            target_id=target_id,
            morphism_type=morphism_type,
            weight=weight
        )

        if morphism is None:
            return OperationResult(
                success=False,
                message="Source or target skill not found"
            )

        return OperationResult(
            success=True,
            message=f"Morphism added: {source_id} -> {target_id}",
            affected_morphisms=[morphism.id]
        )

    @staticmethod
    def merge(
        graph: SkillCategory,
        skill_id_1: str,
        skill_id_2: str,
        new_name: Optional[str] = None
    ) -> OperationResult:
        """
        Fusionar dos skills en uno.

        Complejidad: O(d_max) donde d_max es el grado maximo

        El nuevo skill hereda todos los morfismos de ambos skills.

        Args:
            graph: Grafo categorico
            skill_id_1: ID del primer skill
            skill_id_2: ID del segundo skill
            new_name: Nombre del skill fusionado

        Returns:
            OperationResult con ID del nuevo skill
        """
        skill_1 = graph.get_skill(skill_id_1)
        skill_2 = graph.get_skill(skill_id_2)

        if not skill_1 or not skill_2:
            return OperationResult(
                success=False,
                message="One or both skills not found"
            )

        # Crear skill fusionado
        merged_name = new_name or f"{skill_1.name}+{skill_2.name}"
        merged_skill = Skill(
            id=str(uuid.uuid4()),
            name=merged_name,
            description=f"Merged: {skill_1.description} | {skill_2.description}",
            pillar=skill_1.pillar or skill_2.pillar,
            metadata={
                "merged_from": [skill_id_1, skill_id_2]
            }
        )
        graph.add_skill(merged_skill)

        affected_morphisms = []

        # Redirigir morfismos entrantes
        for mor in graph.incoming_morphisms(skill_id_1):
            if mor.source_id not in [skill_id_1, skill_id_2]:
                new_mor = graph.add_morphism(
                    source_id=mor.source_id,
                    target_id=merged_skill.id,
                    morphism_type=mor.morphism_type,
                    weight=mor.weight
                )
                if new_mor:
                    affected_morphisms.append(new_mor.id)

        for mor in graph.incoming_morphisms(skill_id_2):
            if mor.source_id not in [skill_id_1, skill_id_2]:
                new_mor = graph.add_morphism(
                    source_id=mor.source_id,
                    target_id=merged_skill.id,
                    morphism_type=mor.morphism_type,
                    weight=mor.weight
                )
                if new_mor:
                    affected_morphisms.append(new_mor.id)

        # Redirigir morfismos salientes
        for mor in graph.outgoing_morphisms(skill_id_1):
            if mor.target_id not in [skill_id_1, skill_id_2]:
                new_mor = graph.add_morphism(
                    source_id=merged_skill.id,
                    target_id=mor.target_id,
                    morphism_type=mor.morphism_type,
                    weight=mor.weight
                )
                if new_mor:
                    affected_morphisms.append(new_mor.id)

        for mor in graph.outgoing_morphisms(skill_id_2):
            if mor.target_id not in [skill_id_1, skill_id_2]:
                new_mor = graph.add_morphism(
                    source_id=merged_skill.id,
                    target_id=mor.target_id,
                    morphism_type=mor.morphism_type,
                    weight=mor.weight
                )
                if new_mor:
                    affected_morphisms.append(new_mor.id)

        # Eliminar skills originales
        graph.remove_skill(skill_id_1)
        graph.remove_skill(skill_id_2)

        return OperationResult(
            success=True,
            message=f"Merged {skill_1.name} and {skill_2.name} into {merged_name}",
            affected_skills=[merged_skill.id],
            affected_morphisms=affected_morphisms
        )

    @staticmethod
    def split(
        graph: SkillCategory,
        skill_id: str,
        names: List[str],
        distribution: Optional[List[float]] = None
    ) -> OperationResult:
        """
        Dividir un skill en multiples.

        Complejidad: O(d(s)) donde d(s) es el grado del skill

        Args:
            graph: Grafo categorico
            skill_id: ID del skill a dividir
            names: Nombres de los nuevos skills
            distribution: Distribucion de pesos (debe sumar 1.0)

        Returns:
            OperationResult con IDs de los nuevos skills
        """
        skill = graph.get_skill(skill_id)
        if not skill:
            return OperationResult(
                success=False,
                message="Skill not found"
            )

        n = len(names)
        if distribution is None:
            distribution = [1.0 / n] * n

        if len(distribution) != n:
            return OperationResult(
                success=False,
                message="Distribution length must match names length"
            )

        # Crear nuevos skills
        new_skills = []
        for i, name in enumerate(names):
            new_skill = Skill(
                id=str(uuid.uuid4()),
                name=name,
                description=f"Split from {skill.name}",
                pillar=skill.pillar,
                metadata={
                    "split_from": skill_id,
                    "split_weight": distribution[i]
                }
            )
            graph.add_skill(new_skill)
            new_skills.append(new_skill)

        affected_morphisms = []

        # Duplicar morfismos a todos los nuevos skills
        incoming = list(graph.incoming_morphisms(skill_id))
        outgoing = list(graph.outgoing_morphisms(skill_id))

        for new_skill in new_skills:
            weight_factor = distribution[new_skills.index(new_skill)]

            for mor in incoming:
                if mor.source_id != skill_id:
                    new_mor = graph.add_morphism(
                        source_id=mor.source_id,
                        target_id=new_skill.id,
                        morphism_type=mor.morphism_type,
                        weight=mor.weight * weight_factor
                    )
                    if new_mor:
                        affected_morphisms.append(new_mor.id)

            for mor in outgoing:
                if mor.target_id != skill_id:
                    new_mor = graph.add_morphism(
                        source_id=new_skill.id,
                        target_id=mor.target_id,
                        morphism_type=mor.morphism_type,
                        weight=mor.weight * weight_factor
                    )
                    if new_mor:
                        affected_morphisms.append(new_mor.id)

        # Añadir dependencias entre los nuevos skills (relacionados)
        for i, s1 in enumerate(new_skills):
            for j, s2 in enumerate(new_skills):
                if i < j:
                    mor = graph.add_morphism(
                        source_id=s1.id,
                        target_id=s2.id,
                        morphism_type=MorphismType.ANALOGY,
                        weight=0.5
                    )
                    if mor:
                        affected_morphisms.append(mor.id)

        # Eliminar skill original
        graph.remove_skill(skill_id)

        return OperationResult(
            success=True,
            message=f"Split {skill.name} into {names}",
            affected_skills=[s.id for s in new_skills],
            affected_morphisms=affected_morphisms
        )

    @staticmethod
    def reweight(
        graph: SkillCategory,
        morphism_id: str,
        new_weight: float
    ) -> OperationResult:
        """
        Actualizar peso de un morfismo.

        Complejidad: O(1)
        """
        success = graph.reweight(morphism_id, new_weight)

        if not success:
            return OperationResult(
                success=False,
                message="Morphism not found"
            )

        return OperationResult(
            success=True,
            message=f"Weight updated to {new_weight}",
            affected_morphisms=[morphism_id]
        )

    @staticmethod
    def connect_to_pillar(
        graph: SkillCategory,
        skill_id: str,
        pillar_skill_id: str
    ) -> OperationResult:
        """
        Conectar skill a un skill del pilar fundacional.

        Axioma 7.2: Todo skill debe tener camino a algun pilar.
        """
        morphism = graph.add_morphism(
            source_id=pillar_skill_id,
            target_id=skill_id,
            morphism_type=MorphismType.DEPENDENCY,
            weight=1.0
        )

        if morphism is None:
            return OperationResult(
                success=False,
                message="Failed to connect to pillar"
            )

        return OperationResult(
            success=True,
            message=f"Connected to pillar skill {pillar_skill_id}",
            affected_morphisms=[morphism.id]
        )
