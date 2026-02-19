"""
Categoria de Skills - MES v7.0
==============================

Implementacion de la categoria jerarquica de skills G_t = (S_t, Mor_t, w_t).

Definicion 2.1 (v7.0):
La categoria Skill es una categoria pequena jerarquica donde:
(a) Objetos: Ob(Skill) = S (skills en niveles 0-N)
(b) Morfismos: Hom(s, t) = transformaciones de s a t
(c) Composicion: o : Hom(t, u) x Hom(s, t) -> Hom(s, u)
(d) Identidad: id_s in Hom(s, s)
(e) Nivel: level: S -> N asigna nivel jerarquico

Niveles (Def. 2.3 v7.0):
- Nivel 0: Atomos (skills primitivos)
- Nivel 1: Clusters (agrupaciones basicas)
- Nivel 2: Habilidades (competencias locales)
- Nivel 3: Competencias (capacidades globales)
- Nivel 4+: Meta-skills

Satisface:
- Asociatividad: h o (g o f) = (h o g) o f
- Identidad: f o id_s = f = id_t o f
- Principio de Multiplicidad: Skills pueden tener patrones homologos
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, Iterator, Any
from datetime import datetime
import json
import uuid

from nucleo.types import Skill, Morphism, MorphismType, PillarType, LinkComplexity

logger = logging.getLogger(__name__)


@dataclass
class SkillNode:
    """
    Nodo en el grafo de skills.

    Wrapper alrededor de Skill con metadatos del grafo.
    Incluye informacion de nivel jerarquico (MES v7.0).
    """
    skill: Skill
    in_degree: int = 0
    out_degree: int = 0
    cluster_id: Optional[str] = None  # Para clustering
    pattern_ids: list[str] = field(default_factory=list)  # Patrones donde participa


class SkillCategory:
    """
    Categoria de Skills (MES v7.0).

    Implementa una categoria pequena jerarquica con:
    - Objetos: Skills organizados por niveles
    - Morfismos: Relaciones entre skills
    - Pesos: w: Mor -> R+
    - Niveles: Jerarquia 0-N
    """

    def __init__(self, name: str = "SkillCategory", max_levels: int = 10):
        self.name = name
        self.created_at = datetime.now()
        self.max_levels = max_levels

        # Almacenamiento
        self._skills: dict[str, SkillNode] = {}
        self._morphisms: dict[str, Morphism] = {}

        # Indices para busqueda rapida
        self._outgoing: dict[str, set[str]] = {}  # skill_id -> {morphism_ids}
        self._incoming: dict[str, set[str]] = {}  # skill_id -> {morphism_ids}
        self._identities: dict[str, str] = {}     # skill_id -> identity_morphism_id

        # Indices MES v7.0
        self._by_level: dict[int, set[str]] = defaultdict(set)  # level -> {skill_ids}
        self._by_pillar: dict[PillarType, set[str]] = defaultdict(set)  # pillar -> {skill_ids}
        self._morphism_pairs: dict[tuple[str, str], str] = {}  # (src, tgt) -> morphism_id

        # Metricas
        self._stats = {
            "num_skills": 0,
            "num_morphisms": 0,
            "total_weight": 0.0,
            "max_level": 0,
        }

    # =========================================================================
    # OBJETOS (SKILLS)
    # =========================================================================

    def add_skill(self, skill: Skill) -> None:
        """
        Anadir skill a la categoria.

        Complejidad: O(1)

        Crea automaticamente el morfismo identidad.
        Actualiza indices de nivel y pilar.
        """
        if skill.id in self._skills:
            return  # Ya existe

        # Crear nodo
        node = SkillNode(skill=skill)
        self._skills[skill.id] = node

        # Inicializar indices
        self._outgoing[skill.id] = set()
        self._incoming[skill.id] = set()

        # Indices MES v7.0
        self._by_level[skill.level].add(skill.id)
        if skill.pillar:
            self._by_pillar[skill.pillar].add(skill.id)

        # Actualizar nivel maximo
        if skill.level > self._stats["max_level"]:
            self._stats["max_level"] = skill.level

        # Crear morfismo identidad
        identity = Morphism(
            id=f"id_{skill.id}",
            source_id=skill.id,
            target_id=skill.id,
            morphism_type=MorphismType.IDENTITY,
            weight=1.0,
            metadata={"is_identity": True}
        )
        self._add_morphism_internal(identity)
        self._identities[skill.id] = identity.id

        self._stats["num_skills"] += 1
        logger.debug(f"Anadido skill {skill.name} (nivel {skill.level})")

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Obtener skill por ID."""
        node = self._skills.get(skill_id)
        return node.skill if node else None

    def remove_skill(self, skill_id: str) -> bool:
        """
        Eliminar skill de la categoria.

        Tambien elimina todos los morfismos conectados
        y actualiza los indices MES.
        """
        if skill_id not in self._skills:
            return False

        node = self._skills[skill_id]
        skill = node.skill

        # Eliminar morfismos salientes
        for mor_id in list(self._outgoing.get(skill_id, [])):
            self._remove_morphism_internal(mor_id)

        # Eliminar morfismos entrantes
        for mor_id in list(self._incoming.get(skill_id, [])):
            self._remove_morphism_internal(mor_id)

        # Limpiar indices MES v7.0
        self._by_level[skill.level].discard(skill_id)
        if skill.pillar and skill_id in self._by_pillar.get(skill.pillar, set()):
            self._by_pillar[skill.pillar].discard(skill_id)

        # Eliminar skill
        del self._skills[skill_id]
        del self._outgoing[skill_id]
        del self._incoming[skill_id]
        if skill_id in self._identities:
            del self._identities[skill_id]

        self._stats["num_skills"] -= 1

        # Recalcular nivel maximo si es necesario
        if skill.level == self._stats["max_level"]:
            self._stats["max_level"] = max(
                (s.skill.level for s in self._skills.values()),
                default=0
            )

        return True

    @property
    def skills(self) -> list[Skill]:
        """Lista de todos los skills."""
        return [node.skill for node in self._skills.values()]

    @property
    def skill_ids(self) -> list[str]:
        """Lista de IDs de skills."""
        return list(self._skills.keys())

    # =========================================================================
    # MORFISMOS
    # =========================================================================

    def add_morphism(
        self,
        source_id: str,
        target_id: str,
        morphism_type: MorphismType = MorphismType.DEPENDENCY,
        weight: float = 1.0,
        metadata: Optional[dict] = None
    ) -> Optional[Morphism]:
        """
        Añadir morfismo entre skills.

        Complejidad: O(1)

        Args:
            source_id: ID del skill origen
            target_id: ID del skill destino
            morphism_type: Tipo de morfismo
            weight: Peso del morfismo
            metadata: Metadatos adicionales

        Returns:
            Morfismo creado o None si skills no existen
        """
        if source_id not in self._skills or target_id not in self._skills:
            return None

        morphism = Morphism(
            id=str(uuid.uuid4()),
            source_id=source_id,
            target_id=target_id,
            morphism_type=morphism_type,
            weight=weight,
            metadata=metadata or {}
        )

        self._add_morphism_internal(morphism)
        return morphism

    def _add_morphism_internal(self, morphism: Morphism) -> None:
        """Anadir morfismo (interno)."""
        self._morphisms[morphism.id] = morphism
        self._outgoing[morphism.source_id].add(morphism.id)
        self._incoming[morphism.target_id].add(morphism.id)

        # Indice de pares para busqueda rapida
        pair = (morphism.source_id, morphism.target_id)
        self._morphism_pairs[pair] = morphism.id

        # Actualizar grados
        self._skills[morphism.source_id].out_degree += 1
        self._skills[morphism.target_id].in_degree += 1

        self._stats["num_morphisms"] += 1
        self._stats["total_weight"] += morphism.weight

    def _remove_morphism_internal(self, morphism_id: str) -> None:
        """Eliminar morfismo (interno)."""
        if morphism_id not in self._morphisms:
            return

        morphism = self._morphisms[morphism_id]

        self._outgoing[morphism.source_id].discard(morphism_id)
        self._incoming[morphism.target_id].discard(morphism_id)

        # Limpiar indice de pares
        pair = (morphism.source_id, morphism.target_id)
        if pair in self._morphism_pairs:
            del self._morphism_pairs[pair]

        if morphism.source_id in self._skills:
            self._skills[morphism.source_id].out_degree -= 1
        if morphism.target_id in self._skills:
            self._skills[morphism.target_id].in_degree -= 1

        self._stats["num_morphisms"] -= 1
        self._stats["total_weight"] -= morphism.weight

        del self._morphisms[morphism_id]

    def get_morphism(self, morphism_id: str) -> Optional[Morphism]:
        """Obtener morfismo por ID."""
        return self._morphisms.get(morphism_id)

    @property
    def morphisms(self) -> list[Morphism]:
        """Lista de todos los morfismos."""
        return list(self._morphisms.values())

    # =========================================================================
    # OPERACIONES CATEGORICAS
    # =========================================================================

    def hom(self, source_id: str, target_id: str) -> list[Morphism]:
        """
        Obtener Hom(source, target).

        Todos los morfismos de source a target.
        """
        result = []
        for mor_id in self._outgoing.get(source_id, []):
            mor = self._morphisms[mor_id]
            if mor.target_id == target_id:
                result.append(mor)
        return result

    def identity(self, skill_id: str) -> Optional[Morphism]:
        """Obtener morfismo identidad de un skill."""
        id_mor_id = self._identities.get(skill_id)
        return self._morphisms.get(id_mor_id) if id_mor_id else None

    def compose(self, g_id: str, f_id: str) -> Optional[Morphism]:
        """
        Componer morfismos: g ∘ f

        Requiere: target(f) = source(g)

        Leyes de identidad:
        - g ∘ id_s = g
        - id_t ∘ f = f

        Reglas de tipo para composición:
        - Mismo tipo ∘ Mismo tipo = Mismo tipo (subcategoría cerrada)
        - Tipos mixtos → DEPENDENCY (tipo más general)

        Complejidad: O(1)
        """
        f = self._morphisms.get(f_id)
        g = self._morphisms.get(g_id)

        if not f or not g:
            return None

        if f.target_id != g.source_id:
            return None

        # Leyes de identidad: g ∘ id = g, id ∘ f = f
        if f.morphism_type == MorphismType.IDENTITY:
            return g
        if g.morphism_type == MorphismType.IDENTITY:
            return f

        # Determinar tipo del morfismo compuesto
        if f.morphism_type == g.morphism_type:
            composed_type = f.morphism_type
        else:
            composed_type = MorphismType.DEPENDENCY

        composed = Morphism(
            id=str(uuid.uuid4()),
            source_id=f.source_id,
            target_id=g.target_id,
            morphism_type=composed_type,
            weight=f.weight * g.weight,
            metadata={"composed_from": [f_id, g_id]}
        )

        self._add_morphism_internal(composed)
        return composed

    # =========================================================================
    # CONSULTAS
    # =========================================================================

    def outgoing_morphisms(self, skill_id: str) -> list[Morphism]:
        """Morfismos salientes de un skill."""
        return [
            self._morphisms[mid]
            for mid in self._outgoing.get(skill_id, [])
        ]

    def incoming_morphisms(self, skill_id: str) -> list[Morphism]:
        """Morfismos entrantes a un skill."""
        return [
            self._morphisms[mid]
            for mid in self._incoming.get(skill_id, [])
        ]

    def neighbors(self, skill_id: str) -> list[str]:
        """Skills adyacentes (tanto entrantes como salientes)."""
        neighbors = set()

        for mor in self.outgoing_morphisms(skill_id):
            if mor.target_id != skill_id:  # Excluir identidad
                neighbors.add(mor.target_id)

        for mor in self.incoming_morphisms(skill_id):
            if mor.source_id != skill_id:
                neighbors.add(mor.source_id)

        return list(neighbors)

    def dependencies(self, skill_id: str) -> list[str]:
        """Skills de los que depende este skill."""
        deps = []
        for mor in self.incoming_morphisms(skill_id):
            if (mor.morphism_type == MorphismType.DEPENDENCY and
                mor.source_id != skill_id):
                deps.append(mor.source_id)
        return deps

    def dependents(self, skill_id: str) -> list[str]:
        """Skills que dependen de este skill."""
        deps = []
        for mor in self.outgoing_morphisms(skill_id):
            if (mor.morphism_type == MorphismType.DEPENDENCY and
                mor.target_id != skill_id):
                deps.append(mor.target_id)
        return deps

    def get_neighbors(self, skill_id: str) -> list[str]:
        """
        Obtener vecinos de un skill (alias de neighbors).

        Usado por PatternManager para deteccion de patrones.
        """
        return self.neighbors(skill_id)

    def has_morphism(self, source_id: str, target_id: str) -> bool:
        """
        Verificar si existe morfismo entre dos skills.

        Complejidad: O(1) gracias al indice de pares.
        """
        return (source_id, target_id) in self._morphism_pairs

    def get_morphism_between(
        self,
        source_id: str,
        target_id: str
    ) -> Optional[Morphism]:
        """
        Obtener morfismo entre dos skills especificos.

        Complejidad: O(1)
        """
        pair = (source_id, target_id)
        mor_id = self._morphism_pairs.get(pair)
        return self._morphisms.get(mor_id) if mor_id else None

    # =========================================================================
    # CONSULTAS JERARQUICAS (MES v7.0)
    # =========================================================================

    def get_skills_at_level(self, level: int) -> list[Skill]:
        """
        Obtener todos los skills en un nivel especifico.

        Args:
            level: Nivel jerarquico (0=atomos, 1=clusters, etc.)

        Returns:
            Lista de skills en ese nivel
        """
        skill_ids = self._by_level.get(level, set())
        return [self._skills[sid].skill for sid in skill_ids if sid in self._skills]

    def get_skills_by_pillar(self, pillar: PillarType) -> list[Skill]:
        """
        Obtener todos los skills de un pilar especifico.

        Args:
            pillar: Tipo de pilar

        Returns:
            Lista de skills de ese pilar
        """
        skill_ids = self._by_pillar.get(pillar, set())
        return [self._skills[sid].skill for sid in skill_ids if sid in self._skills]

    def get_level_distribution(self) -> dict[int, int]:
        """
        Obtener distribucion de skills por nivel.

        Returns:
            Diccionario {nivel: cantidad}
        """
        return {
            level: len(skills)
            for level, skills in self._by_level.items()
            if skills
        }

    def get_pillar_distribution(self) -> dict[str, int]:
        """
        Obtener distribucion de skills por pilar.

        Returns:
            Diccionario {pilar: cantidad}
        """
        return {
            pillar.name: len(skills)
            for pillar, skills in self._by_pillar.items()
            if skills
        }

    def get_atoms(self) -> list[Skill]:
        """Obtener skills atomicos (nivel 0)."""
        return self.get_skills_at_level(0)

    def get_clusters(self) -> list[Skill]:
        """Obtener clusters (nivel 1)."""
        return self.get_skills_at_level(1)

    def get_colimits(self) -> list[Skill]:
        """Obtener skills que son colimites (tienen pattern_ids)."""
        return [
            node.skill for node in self._skills.values()
            if node.skill.pattern_ids
        ]

    def count_at_level(self, level: int) -> int:
        """Contar skills en un nivel."""
        return len(self._by_level.get(level, set()))

    # =========================================================================
    # PESOS
    # =========================================================================

    def reweight(self, morphism_id: str, new_weight: float) -> bool:
        """
        Actualizar peso de un morfismo.

        Complejidad: O(1)
        """
        if morphism_id not in self._morphisms:
            return False

        morphism = self._morphisms[morphism_id]
        old_weight = morphism.weight
        morphism.weight = new_weight

        self._stats["total_weight"] += (new_weight - old_weight)
        return True

    def decay_weights(self, factor: float = 0.99) -> None:
        """Aplicar decaimiento a todos los pesos."""
        for morphism in self._morphisms.values():
            self._stats["total_weight"] -= morphism.weight
            morphism.weight *= factor
            self._stats["total_weight"] += morphism.weight

    # =========================================================================
    # VERIFICACION
    # =========================================================================

    def verify_axioms(self) -> dict[str, bool]:
        """
        Verificar axiomas categóricos.

        Verifica:
        1. Existencia de identidades: todo objeto tiene id_s
        2. Identidad izquierda: id_t ∘ f = f para todo f: s → t
        3. Identidad derecha: f ∘ id_s = f para todo f: s → t
        4. Composabilidad: si f: s→t y g: t→u, entonces g∘f existe

        Returns:
            Dict con resultado de cada verificación
        """
        results = {
            "identities_exist": True,
            "identity_left": True,
            "identity_right": True,
            "composability": True,
        }

        # 1. Verificar que cada skill tiene identidad
        for skill_id in self._skills:
            if skill_id not in self._identities:
                results["identities_exist"] = False
                break

        # 2-3. Verificar leyes de identidad para morfismos no-identidad
        non_identity = [
            m for m in self._morphisms.values()
            if m.morphism_type != MorphismType.IDENTITY
        ]

        for f in non_identity[:50]:  # Limitar para performance
            # Identidad derecha: f ∘ id_source = f
            id_s = self._identities.get(f.source_id)
            if id_s:
                result = self.compose(f.id, id_s)
                if result is None:
                    results["identity_right"] = False
                elif result.id != f.id and (
                    result.source_id != f.source_id or
                    result.target_id != f.target_id
                ):
                    results["identity_right"] = False

            # Identidad izquierda: id_target ∘ f = f
            id_t = self._identities.get(f.target_id)
            if id_t:
                result = self.compose(id_t, f.id)
                if result is None:
                    results["identity_left"] = False
                elif result.id != f.id and (
                    result.source_id != f.source_id or
                    result.target_id != f.target_id
                ):
                    results["identity_left"] = False

        return results

    def is_connected(self) -> bool:
        """
        Verificar si el grafo es debilmente conexo.

        Axioma 7.1: G_t es debilmente conexo ∀t
        """
        if not self._skills:
            return True

        # BFS desde cualquier nodo
        start = next(iter(self._skills.keys()))
        visited = {start}
        queue = [start]

        while queue:
            current = queue.pop(0)
            for neighbor in self.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return len(visited) == len(self._skills)

    # =========================================================================
    # CLASIFICACION DE ENLACES (Def 6.3 v7.0)
    # =========================================================================

    def classify_link(self, morphism_id: str) -> LinkComplexity:
        """
        Clasificar la complejidad de un enlace (Def 6.3 v7.0).

        - IDENTITY: Morfismo identidad
        - SIMPLE: Factoriza a traves de un unico colimite (cluster)
        - COMPLEX: No factoriza a traves de ningun cluster individual

        Un enlace f: A -> B es simple si existe un colimite C tal que
        A -> C -> B (factorizacion por cluster). Es complejo si es una
        composicion de simples que no factoriza globalmente.

        Args:
            morphism_id: ID del morfismo a clasificar

        Returns:
            LinkComplexity del enlace
        """
        morph = self._morphisms.get(morphism_id)
        if not morph:
            return LinkComplexity.SIMPLE  # Default safe

        # Identidad
        if morph.morphism_type == MorphismType.IDENTITY:
            return LinkComplexity.IDENTITY

        source = morph.source_id
        target = morph.target_id

        # Caso 1: Source o target ES un colimite → enlace simple
        # (directamente conectado a un cluster)
        source_skill = self.get_skill(source)
        target_skill = self.get_skill(target)

        if source_skill and source_skill.pattern_ids:
            return LinkComplexity.SIMPLE
        if target_skill and target_skill.pattern_ids:
            return LinkComplexity.SIMPLE

        # Caso 2: Existe colimite intermedio C tal que A→C y C→B existen
        for sid, node in self._skills.items():
            if sid == source or sid == target:
                continue
            if not node.skill.pattern_ids:
                continue  # No es colimite
            if self.has_morphism(source, sid) and self.has_morphism(sid, target):
                return LinkComplexity.SIMPLE

        # Caso 3: El morfismo fue compuesto (metadata lo indica)
        if morph.metadata.get("composed_from"):
            return LinkComplexity.COMPLEX

        # Caso 4: Enlace entre niveles no adyacentes → potencialmente complejo
        if source_skill and target_skill:
            level_diff = abs(source_skill.level - target_skill.level)
            if level_diff > 1:
                return LinkComplexity.COMPLEX

        # Default: enlace directo entre skills del mismo nivel → simple
        return LinkComplexity.SIMPLE

    def get_complex_links(self) -> list[Morphism]:
        """
        Obtener todos los enlaces complejos en el grafo.

        Los enlaces complejos representan propiedades emergentes
        que no se reducen a un solo cluster (Thm 8.6).

        Returns:
            Lista de morfismos clasificados como COMPLEX
        """
        return [
            m for m in self._morphisms.values()
            if self.classify_link(m.id) == LinkComplexity.COMPLEX
        ]

    # =========================================================================
    # PRINCIPIO DE MULTIPLICIDAD (Prop 3.4 v7.0)
    # =========================================================================

    def verify_pillar_multiplicity(self) -> dict[str, Any]:
        """
        Verificar que los pilares fundacionales proveen multiplicidad (Prop 3.4).

        Las traducciones entre los 4 pilares (SET, CAT, LOG, TYPE) aseguran
        que existen descomposiciones multiples para conceptos matematicos.

        Verifica:
        1. Existen al menos 2 pilares representados
        2. Existen traducciones (TRANSLATION morphisms) entre pilares
        3. Existen skills analogos en pilares distintos (ANALOGY morphisms)

        Returns:
            Dict con resultado de la verificacion
        """
        pillar_dist = self.get_pillar_distribution()
        num_pillars = len(pillar_dist)

        # Encontrar traducciones inter-pilar
        translations = []
        analogies = []
        for morph in self._morphisms.values():
            if morph.morphism_type == MorphismType.IDENTITY:
                continue
            src = self.get_skill(morph.source_id)
            tgt = self.get_skill(morph.target_id)
            if not src or not tgt:
                continue
            if src.pillar and tgt.pillar and src.pillar != tgt.pillar:
                if morph.morphism_type == MorphismType.TRANSLATION:
                    translations.append({
                        "from": src.pillar.name,
                        "to": tgt.pillar.name,
                        "morphism_id": morph.id,
                    })
                elif morph.morphism_type == MorphismType.ANALOGY:
                    analogies.append({
                        "from": src.pillar.name,
                        "to": tgt.pillar.name,
                        "morphism_id": morph.id,
                    })

        satisfies = num_pillars >= 2 and (len(translations) > 0 or len(analogies) > 0)

        violations = []
        if num_pillars < 2:
            violations.append(
                f"Solo {num_pillars} pilar(es) representado(s), se necesitan >= 2"
            )
        if not translations and not analogies:
            violations.append(
                "No existen traducciones ni analogias entre pilares"
            )

        return {
            "satisfies": satisfies,
            "num_pillars": num_pillars,
            "pillar_distribution": pillar_dist,
            "num_translations": len(translations),
            "num_analogies": len(analogies),
            "translations": translations,
            "analogies": analogies,
            "violations": violations,
        }

    # =========================================================================
    # FORMAL PROPERTIES (Axioms 8.1-8.4, v7.0)
    # =========================================================================

    def verify_all_axioms(self) -> dict[str, Any]:
        """
        Verify all formal axioms (8.1-8.4) of the MES specification.

        Axiom 8.1 (Hierarchy): G_t has >= 2 hierarchical levels
        Axiom 8.2 (Multiplicity): Pillar multiplicity principle holds
        Axiom 8.3 (Connectivity): G_t is weakly connected + inter-pillar
        Axiom 8.4 (Coverage): Every skill is covered by at least one pillar

        Returns:
            Dict with status of each axiom and details
        """
        hierarchy = self._verify_hierarchy()
        multiplicity = self.verify_pillar_multiplicity()
        connectivity = self._verify_connectivity_full()
        coverage = self._verify_coverage()

        all_satisfied = (
            hierarchy["satisfies"]
            and multiplicity["satisfies"]
            and connectivity["satisfies"]
            and coverage["satisfies"]
        )

        return {
            "all_satisfied": all_satisfied,
            "8.1_hierarchy": hierarchy,
            "8.2_multiplicity": multiplicity,
            "8.3_connectivity": connectivity,
            "8.4_coverage": coverage,
        }

    def _verify_hierarchy(self) -> dict[str, Any]:
        """
        Axiom 8.1: G_t is a hierarchical category with >= 2 levels.
        """
        level_dist = self.get_level_distribution()
        num_levels = len(level_dist)
        satisfies = num_levels >= 2

        violations = []
        if num_levels < 2:
            violations.append(
                f"Only {num_levels} level(s), need >= 2"
            )

        # Also check categorical axioms
        cat_axioms = self.verify_axioms()
        if not all(cat_axioms.values()):
            failed = [k for k, v in cat_axioms.items() if not v]
            violations.append(f"Categorical axioms violated: {failed}")
            satisfies = False

        return {
            "satisfies": satisfies,
            "num_levels": num_levels,
            "level_distribution": level_dist,
            "categorical_axioms": cat_axioms,
            "violations": violations,
        }

    def _verify_connectivity_full(self) -> dict[str, Any]:
        """
        Axiom 8.3: G_t is weakly connected with inter-pillar connections.
        """
        weakly_connected = self.is_connected()

        # Check inter-pillar connections
        inter_pillar_count = 0
        pillar_pairs = set()
        for morph in self._morphisms.values():
            if morph.morphism_type == MorphismType.IDENTITY:
                continue
            src = self.get_skill(morph.source_id)
            tgt = self.get_skill(morph.target_id)
            if src and tgt and src.pillar and tgt.pillar and src.pillar != tgt.pillar:
                inter_pillar_count += 1
                pair = tuple(sorted([src.pillar.name, tgt.pillar.name]))
                pillar_pairs.add(pair)

        has_inter_pillar = inter_pillar_count > 0
        satisfies = weakly_connected and has_inter_pillar

        violations = []
        if not weakly_connected:
            violations.append("Graph is not weakly connected")
        if not has_inter_pillar:
            violations.append("No inter-pillar connections found")

        return {
            "satisfies": satisfies,
            "weakly_connected": weakly_connected,
            "inter_pillar_connections": inter_pillar_count,
            "pillar_pairs_connected": list(pillar_pairs),
            "violations": violations,
        }

    def _verify_coverage(self) -> dict[str, Any]:
        """
        Axiom 8.4: Every skill is covered by at least one foundational pillar.

        A skill is 'covered' if:
        - It belongs to a pillar directly, OR
        - It is reachable from a pillar skill via morphisms
        """
        uncovered = []
        covered_count = 0

        # Skills that directly belong to a pillar
        pillar_skills = set()
        for pillar in PillarType:
            for sid in self._by_pillar.get(pillar, set()):
                pillar_skills.add(sid)

        # BFS from all pillar skills to find reachable skills
        reachable = set(pillar_skills)
        queue = list(pillar_skills)
        while queue:
            current = queue.pop(0)
            for neighbor in self.neighbors(current):
                if neighbor not in reachable:
                    reachable.add(neighbor)
                    queue.append(neighbor)

        for skill_id in self._skills:
            if skill_id in reachable:
                covered_count += 1
            else:
                uncovered.append(skill_id)

        total = len(self._skills)
        satisfies = len(uncovered) == 0

        return {
            "satisfies": satisfies,
            "total_skills": total,
            "covered_skills": covered_count,
            "uncovered_skills": uncovered,
            "coverage_ratio": covered_count / max(total, 1),
            "violations": (
                [f"{len(uncovered)} skill(s) not covered by any pillar"]
                if uncovered else []
            ),
        }

    # =========================================================================
    # SERIALIZACION
    # =========================================================================

    def to_dict(self) -> dict[str, Any]:
        """Serializar a diccionario (incluye info MES v7.0)."""
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "max_levels": self.max_levels,
            "skills": [
                {
                    "id": node.skill.id,
                    "name": node.skill.name,
                    "description": node.skill.description,
                    "pillar": node.skill.pillar.name if node.skill.pillar else None,
                    "level": node.skill.level,
                    "pattern_ids": node.skill.pattern_ids,
                }
                for node in self._skills.values()
            ],
            "morphisms": [
                {
                    "id": mor.id,
                    "source_id": mor.source_id,
                    "target_id": mor.target_id,
                    "type": mor.morphism_type.name,
                    "weight": mor.weight,
                    "metadata": mor.metadata,
                }
                for mor in self._morphisms.values()
                if not mor.metadata.get("is_identity")
            ],
            "stats": self.stats,
            "hierarchy": {
                "level_distribution": self.get_level_distribution(),
                "pillar_distribution": self.get_pillar_distribution(),
                "hierarchy_score": self.get_hierarchy_score(),
            },
        }

    def to_json(self) -> str:
        """Serializar a JSON."""
        return json.dumps(self.to_dict(), indent=2)

    @property
    def stats(self) -> dict[str, Any]:
        """Estadisticas del grafo (incluyendo metricas MES v7.0)."""
        level_dist = self.get_level_distribution()
        pillar_dist = self.get_pillar_distribution()

        return {
            **self._stats,
            "avg_weight": (
                self._stats["total_weight"] / self._stats["num_morphisms"]
                if self._stats["num_morphisms"] > 0 else 0
            ),
            # Metricas MES v7.0
            "level_distribution": level_dist,
            "pillar_distribution": pillar_dist,
            "num_atoms": self.count_at_level(0),
            "num_clusters": self.count_at_level(1),
            "num_colimits": len(self.get_colimits()),
        }

    def get_hierarchy_score(self) -> float:
        """
        Calcular score de jerarquia para recompensa r_hierarchy.

        Mide que tan bien estructurada esta la jerarquia:
        - Penaliza niveles vacios intermedios
        - Premia distribucion equilibrada
        - Considera conectividad entre niveles

        Returns:
            Score entre 0 y 1
        """
        if self._stats["num_skills"] == 0:
            return 0.0

        max_level = self._stats["max_level"]
        if max_level == 0:
            return 0.5  # Solo atomos

        # Factor 1: Cobertura de niveles (no hay huecos)
        non_empty_levels = sum(1 for l in range(max_level + 1) if self.count_at_level(l) > 0)
        coverage = non_empty_levels / (max_level + 1)

        # Factor 2: Forma piramidal (mas skills en niveles bajos)
        pyramid_score = 0.0
        for level in range(max_level):
            count_current = self.count_at_level(level)
            count_next = self.count_at_level(level + 1)
            if count_current > 0 and count_next <= count_current:
                pyramid_score += 1.0
        pyramid_score = pyramid_score / max(max_level, 1)

        # Factor 3: Proporcion de colimites
        colimit_ratio = len(self.get_colimits()) / max(self._stats["num_skills"], 1)
        colimit_score = min(colimit_ratio * 5, 1.0)  # Hasta 20% de colimites es optimo

        return (coverage * 0.4 + pyramid_score * 0.4 + colimit_score * 0.2)

    def get_memory_score(self, pattern_coverage: float = 0.0) -> float:
        """
        Calcular score de memoria para recompensa r_memory.

        Args:
            pattern_coverage: Proporcion de skills cubiertos por patrones

        Returns:
            Score entre 0 y 1
        """
        if self._stats["num_skills"] == 0:
            return 0.0

        # Factor 1: Conectividad
        connectivity = self._stats["num_morphisms"] / max(self._stats["num_skills"], 1)
        conn_score = min(connectivity / 3.0, 1.0)  # 3 morfismos por skill es optimo

        # Factor 2: Cobertura de patrones
        pattern_score = pattern_coverage

        # Factor 3: Diversidad de pilares
        pillars_used = len([p for p, s in self._by_pillar.items() if s])
        pillar_score = pillars_used / 3.0  # 3 pilares principales

        return (conn_score * 0.4 + pattern_score * 0.3 + pillar_score * 0.3)


# Alias para compatibilidad
SkillGraph = SkillCategory
