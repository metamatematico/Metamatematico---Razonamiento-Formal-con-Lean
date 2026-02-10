"""
Patterns and Colimits - MES v7.0
================================

Gestion de patrones y colimites en la categoria de skills.

Seccion 2 del documento v7.0:
- Patron: Funtor P: I -> K desde categoria de indices (Def 2.1)
- Colimite: Objeto universal con co-cono (Def 2.2)
- Principio de Multiplicidad: Patrones homologos no conectados (Def 2.5)
- Complejificacion: Teorema 2.10
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING
import uuid

from nucleo.types import (
    Pattern,
    Colimit,
    Skill,
    Morphism,
    MorphismType,
    PillarType,
)

if TYPE_CHECKING:
    from nucleo.graph.category import SkillCategory

logger = logging.getLogger(__name__)


class PatternManager:
    """
    Gestor de patrones en la categoria de skills.

    Un patron P: I -> K representa un sub-grafo de skills
    interconectados que actuan coherentemente.
    """

    def __init__(self):
        self._patterns: dict[str, Pattern] = {}
        self._by_component: dict[str, list[str]] = {}  # skill_id -> pattern_ids

    def create_pattern(
        self,
        component_ids: list[str],
        distinguished_links: list[str],
        metadata: Optional[dict[str, Any]] = None,
        graph: Optional[SkillCategory] = None,
    ) -> Pattern:
        """
        Crear un nuevo patron como funtor P: I -> K (Def 2.1 v7.0).

        Si se proporciona `graph`, construye los datos del funtor
        (categoria de indices I y mapeos P) a partir de los componentes
        y enlaces distinguidos. Sin graph, crea un patron sin datos
        de funtor (compatibilidad con codigo existente).

        Args:
            component_ids: IDs de skills componentes (objetos P_i)
            distinguished_links: IDs de morfismos distinguidos
            metadata: Metadatos opcionales
            graph: Grafo de skills (para construir datos de funtor)

        Returns:
            Patron creado con datos de funtor si graph fue proporcionado
        """
        # Build functor data if graph is provided
        index_objects: list[str] = []
        index_morphisms: dict[str, tuple[str, str]] = {}
        functor_map_objects: dict[str, str] = {}
        functor_map_morphisms: dict[str, str] = {}

        if graph:
            # Create index objects: one per component
            comp_id_to_idx: dict[str, str] = {}
            for i, comp_id in enumerate(component_ids):
                idx = str(i)
                index_objects.append(idx)
                functor_map_objects[idx] = comp_id
                comp_id_to_idx[comp_id] = idx

            # Create index morphisms from distinguished links
            for link_id in distinguished_links:
                morph = graph.get_morphism(link_id)
                if morph and morph.source_id in comp_id_to_idx and morph.target_id in comp_id_to_idx:
                    src_idx = comp_id_to_idx[morph.source_id]
                    tgt_idx = comp_id_to_idx[morph.target_id]
                    idx_morph_name = f"d_{src_idx}_{tgt_idx}"
                    index_morphisms[idx_morph_name] = (src_idx, tgt_idx)
                    functor_map_morphisms[idx_morph_name] = link_id

        pattern = Pattern(
            id=f"pat_{uuid.uuid4().hex[:8]}",
            component_ids=component_ids,
            distinguished_links=distinguished_links,
            metadata=metadata or {},
            index_objects=index_objects,
            index_morphisms=index_morphisms,
            functor_map_objects=functor_map_objects,
            functor_map_morphisms=functor_map_morphisms,
        )

        self._patterns[pattern.id] = pattern
        for comp_id in component_ids:
            if comp_id not in self._by_component:
                self._by_component[comp_id] = []
            self._by_component[comp_id].append(pattern.id)

        logger.debug(
            f"Creado patron {pattern.id} con {len(component_ids)} componentes"
            f"{' (diagrama)' if pattern.is_diagram else ''}"
        )
        return pattern

    def get_pattern(self, pattern_id: str) -> Optional[Pattern]:
        """Obtener patron por ID."""
        return self._patterns.get(pattern_id)

    def get_patterns_containing(self, skill_id: str) -> list[Pattern]:
        """Obtener patrones que contienen un skill."""
        pattern_ids = self._by_component.get(skill_id, [])
        return [self._patterns[pid] for pid in pattern_ids if pid in self._patterns]

    def find_homologous_patterns(
        self,
        pattern: Pattern,
        graph: SkillCategory,
        similarity_threshold: float = 0.7
    ) -> list[Pattern]:
        """
        Buscar patrones homologos (Def. 2.5 v7.0).

        Dos patrones son homologos si sus campos operativos son isomorfos,
        es decir, son funcionalmente equivalentes aunque tengan componentes
        distintos.

        Args:
            pattern: Patron de referencia
            graph: Grafo de skills
            similarity_threshold: Umbral de similitud

        Returns:
            Lista de patrones homologos
        """
        homologous = []

        for other_id, other in self._patterns.items():
            if other_id == pattern.id:
                continue

            # Verificar isomorfismo de campos operativos
            if self._are_homologous(pattern, other, graph, similarity_threshold):
                # Verificar que no esten conectados por cluster
                if not self._connected_by_cluster(pattern, other, graph):
                    homologous.append(other)
                    if pattern.id not in other.is_homologous_to:
                        other.is_homologous_to.append(pattern.id)
                    if other.id not in pattern.is_homologous_to:
                        pattern.is_homologous_to.append(other.id)

        return homologous

    def are_homologous(
        self,
        p1: Pattern,
        p2: Pattern,
        graph: SkillCategory,
        colimit_builder: Optional[ColimitBuilder] = None,
    ) -> bool:
        """
        Verificar si dos patrones son homologos (Def 2.5 v7.0).

        Dos patrones P, P' son homologos si sus campos operativos
        son isomorfos: los conjuntos de enlaces colectivos desde
        sus colimites hacia el resto del grafo tienen la misma
        estructura (biyeccion que preserva targets por nivel/tipo).

        Si no tienen colimites, usa heuristica estructural:
        mismo numero de componentes, misma topologia de enlaces,
        pilares distintos.

        Args:
            p1, p2: Patrones a comparar
            graph: Grafo de skills
            colimit_builder: Builder de colimites (para acceder a campos operativos)

        Returns:
            True si son homologos
        """
        # Deben tener componentes distintos
        if set(p1.component_ids) == set(p2.component_ids):
            return False

        # Deben tener misma estructura interna
        if len(p1.component_ids) != len(p2.component_ids):
            return False
        if len(p1.distinguished_links) != len(p2.distinguished_links):
            return False

        # Si tenemos colimites, comparar campos operativos
        if colimit_builder:
            col1 = colimit_builder.get_colimit_for_pattern(p1.id)
            col2 = colimit_builder.get_colimit_for_pattern(p2.id)

            if col1 and col2:
                return self._operational_fields_isomorphic(
                    col1, col2, graph
                )

        # Fallback: heuristica estructural
        pillars1 = self._get_pillar_signature(p1, graph)
        pillars2 = self._get_pillar_signature(p2, graph)

        # Misma estructura de enlaces + pilares distintos = homologos
        return pillars1 != pillars2

    def _operational_fields_isomorphic(
        self,
        col1: Colimit,
        col2: Colimit,
        graph: SkillCategory,
    ) -> bool:
        """
        Verificar si dos colimites tienen campos operativos isomorfos.

        El campo operativo de un colimite cP es el conjunto de morfismos
        salientes de cP que NO son parte del co-cono (enlaces colectivos).
        """
        of1 = self._get_operational_field(col1, graph)
        of2 = self._get_operational_field(col2, graph)

        if len(of1) != len(of2):
            return False

        if not of1 and not of2:
            # Sin campo operativo externo: comparar estructura interna
            return len(col1.cocone_morphisms) == len(col2.cocone_morphisms)

        # Comparar firmas de targets: (level, pillar, morphism_type)
        sig1 = sorted(of1)
        sig2 = sorted(of2)
        return sig1 == sig2

    def _get_operational_field(
        self,
        colimit: Colimit,
        graph: SkillCategory,
    ) -> list[tuple]:
        """
        Obtener campo operativo de un colimite.

        Returns:
            Lista de firmas (target_level, target_pillar_name, morph_type_name)
        """
        cocone_set = set(colimit.cocone_morphisms)
        field = []
        for morph in graph.outgoing_morphisms(colimit.skill_id):
            if morph.id in cocone_set:
                continue
            if morph.morphism_type == MorphismType.IDENTITY:
                continue
            target = graph.get_skill(morph.target_id)
            if target:
                sig = (
                    target.level,
                    target.pillar.name if target.pillar else "None",
                    morph.morphism_type.name,
                )
                field.append(sig)
        return field

    # Keep the old name as alias for backward compatibility
    def _are_homologous(
        self,
        p1: Pattern,
        p2: Pattern,
        graph: SkillCategory,
        threshold: float
    ) -> bool:
        """Backward-compatible wrapper for are_homologous."""
        return self.are_homologous(p1, p2, graph)

    def _get_pillar_signature(self, pattern: Pattern, graph: SkillCategory) -> set:
        """Obtener firma de pilares de un patron."""
        pillars = set()
        for comp_id in pattern.component_ids:
            skill = graph.get_skill(comp_id)
            if skill and skill.pillar:
                pillars.add(skill.pillar)
        return pillars

    def verify_multiplicity_principle(
        self,
        graph: SkillCategory,
        colimit_builder: Optional[ColimitBuilder] = None,
    ) -> dict[str, Any]:
        """
        Verificar Principio de Multiplicidad (Axioma 8.2 v7.0).

        Deben existir patrones homologos P, P' con colim P = colim P'
        que NO estan conectados por un cluster.

        Esto asegura robustez del sistema: multiples descomposiciones
        para la misma funcionalidad.

        Args:
            graph: Grafo de skills
            colimit_builder: Builder de colimites

        Returns:
            Dict con {satisfies, homologous_pairs, violations}
        """
        result: dict[str, Any] = {
            "satisfies": False,
            "homologous_pairs": [],
            "disconnected_pairs": [],
            "violations": [],
        }

        patterns = list(self._patterns.values())
        if len(patterns) < 2:
            result["violations"].append(
                "Menos de 2 patrones: multiplicidad imposible"
            )
            return result

        # Encontrar todos los pares homologos
        for i, p1 in enumerate(patterns):
            for p2 in patterns[i + 1:]:
                if self.are_homologous(p1, p2, graph, colimit_builder):
                    result["homologous_pairs"].append((p1.id, p2.id))
                    if not self._connected_by_cluster(p1, p2, graph):
                        result["disconnected_pairs"].append((p1.id, p2.id))

        if result["disconnected_pairs"]:
            result["satisfies"] = True
        else:
            if not result["homologous_pairs"]:
                result["violations"].append(
                    "No se encontraron patrones homologos"
                )
            else:
                result["violations"].append(
                    "Todos los patrones homologos estan conectados por cluster"
                )

        return result

    def _connected_by_cluster(
        self,
        p1: Pattern,
        p2: Pattern,
        graph: SkillCategory
    ) -> bool:
        """Verificar si dos patrones estan conectados por un cluster."""
        # Buscar morfismos directos entre componentes de ambos patrones
        for c1 in p1.component_ids:
            for c2 in p2.component_ids:
                if graph.has_morphism(c1, c2) or graph.has_morphism(c2, c1):
                    return True
        return False

    def detect_pattern_in_graph(
        self,
        graph: SkillCategory,
        min_size: int = 2,
        max_size: int = 5
    ) -> list[Pattern]:
        """
        Detectar patrones potenciales en el grafo.

        Busca subgrafos fuertemente conectados que podrian
        formar patrones para colimites. Construye datos de funtor
        completos para cada patron detectado.

        Args:
            graph: Grafo de skills
            min_size: Tamano minimo del patron
            max_size: Tamano maximo del patron

        Returns:
            Lista de patrones detectados (con datos de funtor)
        """
        detected = []

        # Estrategia simple: buscar clusters de skills conectados
        visited = set()
        for skill_id in graph.skill_ids:
            if skill_id in visited:
                continue

            # BFS para encontrar componente conectado
            component = []
            queue = [skill_id]
            while queue and len(component) < max_size:
                current = queue.pop(0)
                if current in visited:
                    continue
                visited.add(current)
                component.append(current)

                # Agregar vecinos
                for neighbor in graph.get_neighbors(current):
                    if neighbor not in visited:
                        queue.append(neighbor)

            # Verificar si forma patron valido
            if min_size <= len(component) <= max_size:
                # Obtener enlaces distinguidos
                links = []
                for i, c1 in enumerate(component):
                    for c2 in component[i+1:]:
                        morph = graph.get_morphism_between(c1, c2)
                        if morph:
                            links.append(morph.id)
                        else:
                            morph = graph.get_morphism_between(c2, c1)
                            if morph:
                                links.append(morph.id)

                if links:  # Al menos un enlace
                    pattern = self.create_pattern(
                        component, links, graph=graph
                    )
                    detected.append(pattern)

        return detected

    @property
    def all_patterns(self) -> list[Pattern]:
        """Todos los patrones registrados."""
        return list(self._patterns.values())

    @property
    def stats(self) -> dict[str, Any]:
        """Estadisticas de patrones."""
        sizes = [len(p.component_ids) for p in self._patterns.values()]
        diagrams = sum(1 for p in self._patterns.values() if p.is_diagram)
        return {
            "num_patterns": len(self._patterns),
            "num_diagrams": diagrams,
            "avg_pattern_size": sum(sizes) / max(len(sizes), 1),
            "max_pattern_size": max(sizes) if sizes else 0,
        }


class ColimitBuilder:
    """
    Constructor de colimites (Def. 2.2 y Teorema 2.10 v7.0).

    El colimite de un patron P es el skill compuesto que integra
    la funcionalidad colectiva del patron.

    Implementa:
    - Construccion de co-cono con verificacion (Def 2.2a)
    - Propiedad universal con morfismos mediadores (Def 2.2b)
    - Complejificacion preservando multiplicidad (Thm 2.10)
    """

    def __init__(self, pattern_manager: PatternManager):
        self._pattern_manager = pattern_manager
        self._colimits: dict[str, Colimit] = {}
        self._pattern_to_colimit: dict[str, str] = {}

    # =========================================================================
    # VERIFICACION DE CO-CONO (Def 2.2a)
    # =========================================================================

    def verify_cocone(
        self,
        pattern: Pattern,
        cocone_skill_id: str,
        cocone_map: dict[str, str],
        graph: SkillCategory,
    ) -> bool:
        """
        Verificar condicion de co-cono (Def 2.2a v7.0).

        Para todo morfismo d: i -> j en I, se cumple:
            c_j . P(d) = c_i
        donde c_i es el morfismo del co-cono desde P(i) al colimite.

        Cuando la igualdad de morfismos no es decidible (categoria libre),
        verificamos compatibilidad estructural: las composiciones deben
        tener el mismo source y target.

        Args:
            pattern: Patron (debe tener datos de funtor)
            cocone_skill_id: ID del skill colimite
            cocone_map: Mapeo component_id -> cocone_morphism_id
            graph: Grafo de skills

        Returns:
            True si el co-cono es valido
        """
        # Verificacion estructural basica: todo componente tiene cocone
        for comp_id in pattern.component_ids:
            if comp_id not in cocone_map:
                logger.warning(f"Componente {comp_id} sin morfismo de co-cono")
                return False
            morph = graph.get_morphism(cocone_map[comp_id])
            if not morph:
                logger.warning(f"Morfismo de co-cono {cocone_map[comp_id]} no encontrado")
                return False
            if morph.source_id != comp_id or morph.target_id != cocone_skill_id:
                logger.warning(
                    f"Co-cono {morph.id}: esperado {comp_id} -> {cocone_skill_id}, "
                    f"encontrado {morph.source_id} -> {morph.target_id}"
                )
                return False

        # Si no hay datos de funtor, solo verificacion estructural
        if not pattern.is_diagram:
            return True

        # Verificacion de conmutatividad del co-cono
        for d_name, (src_idx, tgt_idx) in pattern.index_morphisms.items():
            # P(d): morfismo en K de P(src_idx) a P(tgt_idx)
            pd_id = pattern.functor_map_morphisms.get(d_name)
            if not pd_id:
                logger.warning(f"Morfismo de funtor {d_name} no encontrado")
                return False
            pd = graph.get_morphism(pd_id)
            if not pd:
                logger.warning(f"Morfismo {pd_id} no existe en el grafo")
                return False

            # Componentes
            src_comp_id = pattern.functor_map_objects.get(src_idx)
            tgt_comp_id = pattern.functor_map_objects.get(tgt_idx)

            # Co-cono de source y target
            c_src_id = cocone_map.get(src_comp_id)
            c_tgt_id = cocone_map.get(tgt_comp_id)
            if not c_src_id or not c_tgt_id:
                return False

            c_src = graph.get_morphism(c_src_id)
            c_tgt = graph.get_morphism(c_tgt_id)
            if not c_src or not c_tgt:
                return False

            # Verificar composabilidad: c_tgt . P(d) requiere target(P(d)) = source(c_tgt)
            if pd.target_id != c_tgt.source_id:
                logger.warning(
                    f"Co-cono no composable: P(d).target={pd.target_id} "
                    f"!= c_tgt.source={c_tgt.source_id}"
                )
                return False

            # Verificar: c_tgt . P(d) tiene source = P(src_idx) = c_src.source
            if pd.source_id != c_src.source_id:
                logger.warning(
                    f"Co-cono no conmuta: P(d).source={pd.source_id} "
                    f"!= c_src.source={c_src.source_id}"
                )
                return False

            # Verificar: c_tgt . P(d) tiene target = colimit = c_src.target
            if c_tgt.target_id != c_src.target_id:
                logger.warning(
                    f"Co-cono no conmuta: c_tgt.target={c_tgt.target_id} "
                    f"!= c_src.target={c_src.target_id}"
                )
                return False

        return True

    # =========================================================================
    # PROPIEDAD UNIVERSAL (Def 2.2b)
    # =========================================================================

    def verify_universal_property(
        self,
        pattern: Pattern,
        cocone_skill_id: str,
        cocone_map: dict[str, str],
        graph: SkillCategory,
    ) -> bool:
        """
        Verificar propiedad universal del colimite (Def 2.2b v7.0).

        Para todo objeto B y familia compatible (g_i: P_i -> B),
        existe unico h: cP -> B tal que h . c_i = g_i para todo i.

        "Compatible" significa: para todo d: i -> j en I, g_j . P(d) = g_i.

        En la practica, verificamos para todo B existente en el grafo
        que tenga morfismos entrantes desde TODOS los componentes del patron.

        Args:
            pattern: Patron con datos de funtor
            cocone_skill_id: ID del skill colimite
            cocone_map: Mapeo component_id -> cocone_morphism_id
            graph: Grafo de skills

        Returns:
            True si la propiedad universal se satisface
        """
        # Encontrar todos los B candidatos: skills que reciben morfismos
        # de TODOS los componentes del patron
        candidate_targets = self._find_compatible_targets(
            pattern, cocone_skill_id, graph
        )

        if not candidate_targets:
            # Sin candidatos: propiedad universal vacuamente verdadera
            return True

        for b_id, g_morphisms in candidate_targets.items():
            # Verificar compatibilidad de la familia si hay datos de funtor
            if pattern.is_diagram:
                if not self._is_compatible_family(pattern, g_morphisms, graph):
                    continue  # Familia no compatible, no aplica

            # Verificar: existe h: cP -> B
            h = graph.get_morphism_between(cocone_skill_id, b_id)
            if h is None:
                logger.warning(
                    f"Propiedad universal falla: no existe h: {cocone_skill_id} -> {b_id}"
                )
                return False

            # Verificar: h . c_i tiene misma estructura que g_i para todo i
            for comp_id in pattern.component_ids:
                c_i = graph.get_morphism(cocone_map.get(comp_id, ""))
                g_i = g_morphisms.get(comp_id)
                if not c_i or not g_i:
                    continue

                # h . c_i debe tener: source=comp_id, target=b_id
                # c_i: comp_id -> cocone_skill_id
                # h: cocone_skill_id -> b_id
                # h . c_i: comp_id -> b_id (misma estructura que g_i)
                if c_i.target_id != h.source_id:
                    return False
                if c_i.source_id != g_i.source_id:
                    return False
                if h.target_id != g_i.target_id:
                    return False

        return True

    def _find_compatible_targets(
        self,
        pattern: Pattern,
        cocone_skill_id: str,
        graph: SkillCategory,
    ) -> dict[str, dict[str, Morphism]]:
        """
        Encontrar objetos B que reciben morfismos de todos los componentes.

        Returns:
            Dict {b_id: {comp_id: morphism}} para cada B candidato
        """
        # Para cada componente, obtener targets alcanzables (no-triviales)
        targets_per_component: list[dict[str, Morphism]] = []
        for comp_id in pattern.component_ids:
            comp_targets: dict[str, Morphism] = {}
            for morph in graph.outgoing_morphisms(comp_id):
                tid = morph.target_id
                if tid != comp_id and tid != cocone_skill_id:
                    if morph.morphism_type != MorphismType.IDENTITY:
                        comp_targets[tid] = morph
            targets_per_component.append(comp_targets)

        if not targets_per_component:
            return {}

        # Interseccion: B debe ser alcanzable desde TODOS los componentes
        common_targets = set(targets_per_component[0].keys())
        for comp_targets in targets_per_component[1:]:
            common_targets &= set(comp_targets.keys())

        result: dict[str, dict[str, Morphism]] = {}
        for b_id in common_targets:
            family: dict[str, Morphism] = {}
            for i, comp_id in enumerate(pattern.component_ids):
                family[comp_id] = targets_per_component[i][b_id]
            result[b_id] = family

        return result

    def _is_compatible_family(
        self,
        pattern: Pattern,
        g_morphisms: dict[str, Morphism],
        graph: SkillCategory,
    ) -> bool:
        """
        Verificar que una familia (g_i: P_i -> B) es compatible con el diagrama.

        Compatible significa: para todo d: i -> j en I, g_j . P(d) = g_i
        (verificado estructuralmente).
        """
        for d_name, (src_idx, tgt_idx) in pattern.index_morphisms.items():
            pd_id = pattern.functor_map_morphisms.get(d_name)
            if not pd_id:
                continue
            pd = graph.get_morphism(pd_id)
            if not pd:
                continue

            src_comp = pattern.functor_map_objects.get(src_idx)
            tgt_comp = pattern.functor_map_objects.get(tgt_idx)
            g_src = g_morphisms.get(src_comp)
            g_tgt = g_morphisms.get(tgt_comp)

            if not g_src or not g_tgt:
                return False

            # g_tgt . P(d) debe tener misma estructura que g_src
            # P(d): P(src) -> P(tgt), g_tgt: P(tgt) -> B
            # g_tgt . P(d): P(src) -> B = g_src
            if pd.target_id != g_tgt.source_id:
                return False
            if pd.source_id != g_src.source_id:
                return False
            if g_tgt.target_id != g_src.target_id:
                return False

        return True

    # =========================================================================
    # CONSTRUCCION DE COLIMITE
    # =========================================================================

    def build_colimit(
        self,
        pattern: Pattern,
        graph: SkillCategory,
        name: Optional[str] = None,
        verify: bool = True,
    ) -> tuple[Skill, Colimit]:
        """
        Construir colimite de un patron (Complejificacion simple, Def 2.2).

        Crea:
        1. Un nuevo skill s_new = colim P
        2. Un co-cono (c_i: P_i -> s_new) verificado
        3. Morfismos universales h: s_new -> B para familias compatibles
        4. Verificacion de propiedad universal

        Args:
            pattern: Patron a ligar
            graph: Grafo de skills
            name: Nombre opcional para el colimite
            verify: Si True, verifica co-cono y propiedad universal

        Returns:
            Tupla (skill colimite, objeto colimite)

        Raises:
            ValueError: Si la verificacion falla y verify=True
        """
        # Verificar que el patron no tenga colimite ya
        if pattern.id in self._pattern_to_colimit:
            existing = self._colimits[self._pattern_to_colimit[pattern.id]]
            existing_skill = graph.get_skill(existing.skill_id)
            return existing_skill, existing

        # Determinar nivel del colimite
        max_component_level = 0
        component_pillars = set()
        for comp_id in pattern.component_ids:
            skill = graph.get_skill(comp_id)
            if skill:
                max_component_level = max(max_component_level, skill.level)
                if skill.pillar:
                    component_pillars.add(skill.pillar)

        colimit_level = max_component_level + 1

        # Determinar pilar del colimite
        # Si todos los componentes son del mismo pilar, heredar
        # Si son de pilares diferentes, es None (meta-skill)
        colimit_pillar = None
        if len(component_pillars) == 1:
            colimit_pillar = list(component_pillars)[0]

        # Crear skill colimite
        colimit_name = name or f"colim_{pattern.id}"
        colimit_skill = Skill(
            id=f"skill_{uuid.uuid4().hex[:8]}",
            name=colimit_name,
            description=f"Colimite del patron {pattern.id}",
            pillar=colimit_pillar,
            level=colimit_level,
            pattern_ids=pattern.component_ids.copy(),
            metadata={"pattern_id": pattern.id},
        )

        # Agregar skill al grafo
        graph.add_skill(colimit_skill)

        # Crear morfismos del co-cono y cocone_map
        cocone_morphisms = []
        cocone_map: dict[str, str] = {}
        for comp_id in pattern.component_ids:
            morph = graph.add_morphism(
                source_id=comp_id,
                target_id=colimit_skill.id,
                morphism_type=MorphismType.SPECIALIZATION,
                metadata={"is_cocone": True, "pattern_id": pattern.id}
            )
            cocone_morphisms.append(morph.id)
            cocone_map[comp_id] = morph.id

        # Verificar co-cono
        cocone_ok = self.verify_cocone(
            pattern, colimit_skill.id, cocone_map, graph
        )
        if verify and not cocone_ok:
            # Rollback: remove the skill and morphisms
            graph.remove_skill(colimit_skill.id)
            raise ValueError(
                f"Verificacion de co-cono fallo para patron {pattern.id}"
            )

        # Construir morfismos universales (Def 2.2b)
        universal_morphisms = self._build_universal_morphisms(
            pattern, colimit_skill.id, cocone_map, graph
        )

        # Verificar propiedad universal
        up_ok = self.verify_universal_property(
            pattern, colimit_skill.id, cocone_map, graph
        )
        if verify and not up_ok:
            graph.remove_skill(colimit_skill.id)
            raise ValueError(
                f"Verificacion de propiedad universal fallo para patron {pattern.id}"
            )

        # Crear objeto Colimit
        colimit = Colimit(
            pattern_id=pattern.id,
            skill_id=colimit_skill.id,
            cocone_morphisms=cocone_morphisms,
            cocone_map=cocone_map,
            universal_morphisms=universal_morphisms,
            cocone_verified=cocone_ok,
            universal_property_verified=up_ok,
        )

        self._colimits[colimit.id] = colimit
        self._pattern_to_colimit[pattern.id] = colimit.id

        logger.info(
            f"Construido colimite {colimit_skill.name} (nivel {colimit_level}) "
            f"para patron de {len(pattern.component_ids)} componentes "
            f"[cocone={'OK' if cocone_ok else 'FAIL'}, "
            f"UP={'OK' if up_ok else 'FAIL'}]"
        )

        return colimit_skill, colimit

    def _build_universal_morphisms(
        self,
        pattern: Pattern,
        cocone_skill_id: str,
        cocone_map: dict[str, str],
        graph: SkillCategory,
    ) -> dict[str, str]:
        """
        Construir morfismos universales h: cP -> B para cada familia compatible.

        Para cada B en el grafo que reciba morfismos de todos los componentes
        del patron (formando una familia compatible), crea el unico
        morfismo mediador h: cP -> B tal que h . c_i = g_i.

        Returns:
            Dict {target_id: morphism_id} de morfismos universales creados
        """
        universal_morphisms: dict[str, str] = {}

        candidates = self._find_compatible_targets(
            pattern, cocone_skill_id, graph
        )

        for b_id, g_morphisms in candidates.items():
            # Verificar compatibilidad si hay datos de funtor
            if pattern.is_diagram:
                if not self._is_compatible_family(pattern, g_morphisms, graph):
                    continue

            # Verificar que no exista ya un morfismo cP -> B
            existing = graph.get_morphism_between(cocone_skill_id, b_id)
            if existing:
                universal_morphisms[b_id] = existing.id
                continue

            # Crear morfismo mediador h: cP -> B
            h = graph.add_morphism(
                source_id=cocone_skill_id,
                target_id=b_id,
                morphism_type=MorphismType.DEPENDENCY,
                metadata={
                    "is_universal": True,
                    "pattern_id": pattern.id,
                    "mediates_for": list(g_morphisms.keys()),
                }
            )
            if h:
                universal_morphisms[b_id] = h.id
                logger.debug(
                    f"Creado morfismo universal h: {cocone_skill_id} -> {b_id}"
                )

        return universal_morphisms

    # =========================================================================
    # CONSULTAS
    # =========================================================================

    def get_colimit_for_pattern(self, pattern_id: str) -> Optional[Colimit]:
        """Obtener colimite de un patron."""
        colimit_id = self._pattern_to_colimit.get(pattern_id)
        if colimit_id:
            return self._colimits.get(colimit_id)
        return None

    def has_colimit(self, pattern_id: str) -> bool:
        """Verificar si un patron tiene colimite."""
        return pattern_id in self._pattern_to_colimit

    def get_colimit(self, colimit_id: str) -> Optional[Colimit]:
        """Obtener colimite por ID."""
        return self._colimits.get(colimit_id)

    # =========================================================================
    # COMPLEJIFICACION (Thm 2.10)
    # =========================================================================

    def complexify(
        self,
        graph: SkillCategory,
        patterns_to_bind: list[Pattern],
        verify: bool = True,
    ) -> list[tuple[Skill, Colimit]]:
        """
        Complejificar el grafo ligando multiples patrones.

        Teorema 2.10: La complejificacion satisface propiedad universal
        y preserva el principio de multiplicidad.

        Args:
            graph: Grafo de skills
            patterns_to_bind: Patrones que deben adquirir colimite
            verify: Si True, verifica cada colimite

        Returns:
            Lista de (skill, colimit) creados
        """
        results = []

        for pattern in patterns_to_bind:
            if not self.has_colimit(pattern.id):
                skill, colimit = self.build_colimit(
                    pattern, graph, verify=verify
                )
                results.append((skill, colimit))

        return results

    @property
    def stats(self) -> dict[str, Any]:
        """Estadisticas de colimites."""
        verified_cocone = sum(
            1 for c in self._colimits.values() if c.cocone_verified
        )
        verified_up = sum(
            1 for c in self._colimits.values() if c.universal_property_verified
        )
        return {
            "num_colimits": len(self._colimits),
            "patterns_with_colimit": len(self._pattern_to_colimit),
            "cocone_verified": verified_cocone,
            "universal_property_verified": verified_up,
        }
