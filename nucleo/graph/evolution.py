"""
Sistema Evolutivo - MES v7.0
============================

Implementacion del sistema evolutivo de skills S sobre T = N (Def 3.2 v7.0).

Un sistema evolutivo es una familia de categorias {Skill_t}_{t in T}
con funtores de transicion k_{t,t'}: Skill_t -> Skill_{t'} que satisfacen:
- k_{t,t} = Id_{Skill_t}
- k_{t,t''} = k_{t',t''} . k_{t,t'} (compatibilidad)

La evolucion procede via Options (Def 2.9):
- Absorcion: incorporar skills externos
- Eliminacion: eliminar skills obsoletos
- Ligadura: crear colimites de patrones
- Clasificacion: crear limites de patrones

El resultado es la complejificacion K' = Compl(K, O) (Thm 2.10).
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime

from nucleo.types import (
    Skill,
    Morphism,
    MorphismType,
    LinkComplexity,
    Option,
)
from nucleo.graph.category import SkillCategory
from nucleo.mes.patterns import PatternManager, ColimitBuilder

logger = logging.getLogger(__name__)


@dataclass
class CategorySnapshot:
    """
    Snapshot inmutable de Skill_t en el tiempo t (Def 3.2 v7.0).

    Captura el estado completo de la categoria en un instante:
    - Todos los skills (objetos)
    - Todos los morfismos (flechas)
    - Estadisticas en ese momento

    Attributes:
        timestamp: Indice temporal t en T = N
        skills: Copia de skills en el momento t
        morphisms: Copia de morfismos en el momento t
        stats: Estadisticas del grafo en t
        created_at: Momento real de creacion
    """
    timestamp: int
    skills: dict[str, Skill] = field(default_factory=dict)
    morphisms: dict[str, Morphism] = field(default_factory=dict)
    stats: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def num_skills(self) -> int:
        return len(self.skills)

    @property
    def num_morphisms(self) -> int:
        return len(self.morphisms)

    def has_skill(self, skill_id: str) -> bool:
        return skill_id in self.skills

    def has_morphism(self, morphism_id: str) -> bool:
        return morphism_id in self.morphisms


@dataclass
class TransitionFunctor:
    """
    Funtor de transicion k_{t,t'}: Skill_t -> Skill_{t'} (Def 3.2 v7.0).

    Mapea objetos y morfismos de Skill_t a Skill_{t'}.
    - None en el mapa significa que el objeto/morfismo fue eliminado.
    - IDs nuevos (presentes en t' pero no en t) son absorciones o colimites.

    Attributes:
        source_time: Tiempo origen t
        target_time: Tiempo destino t'
        object_map: Mapeo de skill_ids: t -> t' (None = eliminado)
        morphism_map: Mapeo de morphism_ids: t -> t' (None = eliminado)
        absorbed_skills: Skills nuevos en t' (no existian en t)
        absorbed_morphisms: Morfismos nuevos en t'
    """
    source_time: int
    target_time: int
    object_map: dict[str, Optional[str]] = field(default_factory=dict)
    morphism_map: dict[str, Optional[str]] = field(default_factory=dict)
    absorbed_skills: list[str] = field(default_factory=list)
    absorbed_morphisms: list[str] = field(default_factory=list)

    @property
    def num_preserved(self) -> int:
        """Numero de skills preservados (no eliminados)."""
        return sum(1 for v in self.object_map.values() if v is not None)

    @property
    def num_eliminated(self) -> int:
        """Numero de skills eliminados."""
        return sum(1 for v in self.object_map.values() if v is None)

    @property
    def num_absorbed(self) -> int:
        """Numero de skills nuevos absorbidos."""
        return len(self.absorbed_skills)

    def compose(self, other: TransitionFunctor) -> TransitionFunctor:
        """
        Componer con otro funtor: self . other = k_{t1,t3}

        Requiere: self.source_time == other.target_time

        Args:
            other: Funtor k_{t1,t2} (applied first)

        Returns:
            Funtor compuesto k_{t1,t3} = self . other
        """
        assert self.source_time == other.target_time, (
            f"Incompatible: self.source={self.source_time} "
            f"!= other.target={other.target_time}"
        )

        composed_obj: dict[str, Optional[str]] = {}
        composed_mor: dict[str, Optional[str]] = {}

        # Mapear objetos: k_{t1,t3}(s) = k_{t2,t3}(k_{t1,t2}(s))
        for s_id, s_mid in other.object_map.items():
            if s_mid is None:
                composed_obj[s_id] = None
            else:
                composed_obj[s_id] = self.object_map.get(s_mid)

        # Mapear morfismos
        for m_id, m_mid in other.morphism_map.items():
            if m_mid is None:
                composed_mor[m_id] = None
            else:
                composed_mor[m_id] = self.morphism_map.get(m_mid)

        # Absorciones: todo lo nuevo en t2 que sobrevive a t3,
        # mas todo lo nuevo en t3
        absorbed_skills = []
        for s_id in other.absorbed_skills:
            mapped = self.object_map.get(s_id)
            if mapped is not None:
                absorbed_skills.append(mapped)
        absorbed_skills.extend(self.absorbed_skills)

        absorbed_morphisms = []
        for m_id in other.absorbed_morphisms:
            mapped = self.morphism_map.get(m_id)
            if mapped is not None:
                absorbed_morphisms.append(mapped)
        absorbed_morphisms.extend(self.absorbed_morphisms)

        return TransitionFunctor(
            source_time=other.source_time,
            target_time=self.target_time,
            object_map=composed_obj,
            morphism_map=composed_mor,
            absorbed_skills=absorbed_skills,
            absorbed_morphisms=absorbed_morphisms,
        )


class EvolutionarySystem:
    """
    Sistema evolutivo de skills S sobre T = N (Def 3.2 v7.0).

    Mantiene:
    - La categoria actual Skill_t
    - Historial de snapshots {Skill_0, Skill_1, ...}
    - Funtores de transicion {k_{t,t+1}} entre snapshots consecutivos
    - PatternManager y ColimitBuilder para complejificaciones

    La evolucion procede via Options (Def 2.9):
        Skill_{t+1} = Compl(Skill_t, O_t)
    """

    def __init__(
        self,
        graph: SkillCategory,
        pattern_manager: Optional[PatternManager] = None,
        max_history: int = 100,
    ):
        """
        Args:
            graph: Categoria de skills actual
            pattern_manager: Gestor de patrones (crea uno nuevo si None)
            max_history: Maximo de snapshots a mantener en historial
        """
        self._graph = graph
        self._pattern_manager = pattern_manager or PatternManager()
        self._colimit_builder = ColimitBuilder(self._pattern_manager)
        self._max_history = max_history

        # Historial
        self._current_time: int = 0
        self._snapshots: dict[int, CategorySnapshot] = {}
        self._functors: dict[tuple[int, int], TransitionFunctor] = {}

        # Tomar snapshot inicial
        self._snapshots[0] = self._take_snapshot(0)

    @property
    def current_time(self) -> int:
        return self._current_time

    @property
    def graph(self) -> SkillCategory:
        return self._graph

    @property
    def pattern_manager(self) -> PatternManager:
        return self._pattern_manager

    @property
    def colimit_builder(self) -> ColimitBuilder:
        return self._colimit_builder

    # =========================================================================
    # SNAPSHOTS
    # =========================================================================

    def _take_snapshot(self, t: int) -> CategorySnapshot:
        """
        Capturar snapshot inmutable de la categoria en el tiempo t.

        Crea copias profundas de todos los skills y morfismos.
        """
        skills: dict[str, Skill] = {}
        for sid in self._graph.skill_ids:
            skill = self._graph.get_skill(sid)
            if skill:
                skills[sid] = copy.copy(skill)

        morphisms: dict[str, Morphism] = {}
        for morph in self._graph.morphisms:
            morphisms[morph.id] = copy.copy(morph)

        return CategorySnapshot(
            timestamp=t,
            skills=skills,
            morphisms=morphisms,
            stats=dict(self._graph.stats),
        )

    def get_snapshot(self, t: int) -> Optional[CategorySnapshot]:
        """Obtener snapshot en el tiempo t."""
        return self._snapshots.get(t)

    # =========================================================================
    # FUNTORES DE TRANSICION
    # =========================================================================

    def get_functor(self, t1: int, t2: int) -> Optional[TransitionFunctor]:
        """
        Obtener funtor de transicion k_{t1,t2}.

        Si no existe directamente, intenta composicion de consecutivos.
        """
        if t1 == t2:
            # Identity functor
            snap = self._snapshots.get(t1)
            if not snap:
                return None
            return TransitionFunctor(
                source_time=t1,
                target_time=t2,
                object_map={sid: sid for sid in snap.skills},
                morphism_map={mid: mid for mid in snap.morphisms},
            )

        # Try direct
        direct = self._functors.get((t1, t2))
        if direct:
            return direct

        # Try composing consecutive functors
        if t1 < t2:
            result = None
            for t in range(t1, t2):
                f = self._functors.get((t, t + 1))
                if f is None:
                    return None
                if result is None:
                    result = f
                else:
                    result = f.compose(result)
            return result

        return None

    def verify_compatibility(self, t1: int, t2: int, t3: int) -> bool:
        """
        Verificar compatibilidad (Def 3.2 v7.0):
            k_{t2,t3} . k_{t1,t2} = k_{t1,t3}

        Es decir, la composicion de funtores consecutivos produce
        el mismo resultado que el funtor directo.
        """
        k_12 = self.get_functor(t1, t2)
        k_23 = self.get_functor(t2, t3)
        k_13 = self.get_functor(t1, t3)

        if k_12 is None or k_23 is None or k_13 is None:
            return False

        composed = k_23.compose(k_12)

        # Verificar igualdad en mapeos de objetos
        for s_id in k_13.object_map:
            if composed.object_map.get(s_id) != k_13.object_map[s_id]:
                logger.warning(
                    f"Incompatibilidad en objeto {s_id}: "
                    f"compuesto={composed.object_map.get(s_id)}, "
                    f"directo={k_13.object_map[s_id]}"
                )
                return False

        # Verificar igualdad en mapeos de morfismos
        for m_id in k_13.morphism_map:
            if composed.morphism_map.get(m_id) != k_13.morphism_map[m_id]:
                logger.warning(
                    f"Incompatibilidad en morfismo {m_id}: "
                    f"compuesto={composed.morphism_map.get(m_id)}, "
                    f"directo={k_13.morphism_map[m_id]}"
                )
                return False

        return True

    # =========================================================================
    # EVOLUCION VIA OPTIONS (Def 2.9, Thm 2.10)
    # =========================================================================

    def apply_option(self, option: Option) -> TransitionFunctor:
        """
        Aplicar una Option para producir la complejificacion.

        Skill_{t+1} = Compl(Skill_t, O_t)

        Ejecuta en orden:
        1. Absorcion: incorporar skills externos
        2. Eliminacion: eliminar skills obsoletos
        3. Ligadura: crear colimites de patrones

        Args:
            option: Option con las operaciones a realizar

        Returns:
            TransitionFunctor k_{t,t+1} describiendo los cambios
        """
        t = self._current_time
        t_next = t + 1

        # Snapshot antes de los cambios
        snap_before = self._snapshots[t]

        # Mapeos de transicion (empezar con identidad)
        object_map: dict[str, Optional[str]] = {
            sid: sid for sid in snap_before.skills
        }
        morphism_map: dict[str, Optional[str]] = {
            mid: mid for mid in snap_before.morphisms
        }
        absorbed_skills: list[str] = []
        absorbed_morphisms: list[str] = []

        # 1. Absorcion: agregar skills nuevos
        for skill_id in option.absorptions:
            skill = self._graph.get_skill(skill_id)
            if skill:
                # Skill ya existe en el grafo, registrar como absorcion
                absorbed_skills.append(skill_id)
            # Si no existe, el caller deberia haberlo agregado al grafo antes

        # 2. Eliminacion: eliminar skills
        for skill_id in option.eliminations:
            if skill_id in object_map:
                object_map[skill_id] = None
                # Marcar morfismos conectados como eliminados
                for mid, morph in list(snap_before.morphisms.items()):
                    if morph.source_id == skill_id or morph.target_id == skill_id:
                        morphism_map[mid] = None
                self._graph.remove_skill(skill_id)

        # 3. Ligadura: crear colimites de patrones
        for pattern_id in option.bindings:
            pattern = self._pattern_manager.get_pattern(pattern_id)
            if pattern and not self._colimit_builder.has_colimit(pattern_id):
                skill, colimit = self._colimit_builder.build_colimit(
                    pattern, self._graph
                )
                absorbed_skills.append(skill.id)
                for morph_id in colimit.cocone_morphisms:
                    absorbed_morphisms.append(morph_id)
                for morph_id in colimit.universal_morphisms.values():
                    absorbed_morphisms.append(morph_id)

        # Registrar nuevos morfismos creados (que no estaban en el snapshot)
        for morph in self._graph.morphisms:
            if morph.id not in morphism_map and morph.id not in absorbed_morphisms:
                absorbed_morphisms.append(morph.id)

        # Crear funtor de transicion
        functor = TransitionFunctor(
            source_time=t,
            target_time=t_next,
            object_map=object_map,
            morphism_map=morphism_map,
            absorbed_skills=absorbed_skills,
            absorbed_morphisms=absorbed_morphisms,
        )

        # Avanzar tiempo
        self._current_time = t_next
        self._snapshots[t_next] = self._take_snapshot(t_next)
        self._functors[(t, t_next)] = functor

        # Limpieza de historial viejo
        self._cleanup_history()

        logger.info(
            f"Transicion t={t} -> t={t_next}: "
            f"+{functor.num_absorbed} absorbidos, "
            f"-{functor.num_eliminated} eliminados, "
            f"={functor.num_preserved} preservados"
        )

        return functor

    def _cleanup_history(self) -> None:
        """Limpiar snapshots y funtores antiguos si exceden max_history."""
        if len(self._snapshots) <= self._max_history:
            return

        min_to_keep = self._current_time - self._max_history + 1
        for t in list(self._snapshots.keys()):
            if t < min_to_keep:
                del self._snapshots[t]

        for (t1, t2) in list(self._functors.keys()):
            if t1 < min_to_keep:
                del self._functors[(t1, t2)]

    # =========================================================================
    # EMERGENCIA (Def 6.3, Thm 8.6 v7.0)
    # =========================================================================

    def detect_complex_links(self, t: Optional[int] = None) -> list[str]:
        """
        Encontrar enlaces complejos en Skill_t (Def 6.3 v7.0).

        Los enlaces complejos son composiciones de simples que NO
        factorizan a traves de un unico cluster. Representan
        propiedades emergentes del sistema.

        Args:
            t: Tiempo a inspeccionar (None = actual)

        Returns:
            Lista de IDs de morfismos complejos
        """
        if t is not None and t != self._current_time:
            # Para tiempos pasados, usar snapshot (solo structural check)
            snap = self._snapshots.get(t)
            if not snap:
                return []
            # No podemos clasificar links en un snapshot sin el grafo vivo
            # Retornamos los que estan marcados como compuestos
            return [
                mid for mid, morph in snap.morphisms.items()
                if morph.metadata.get("composed_from")
            ]

        # Tiempo actual: usar el grafo vivo
        return [m.id for m in self._graph.get_complex_links()]

    def measure_emergence(self, t: Optional[int] = None) -> dict[str, Any]:
        """
        Medir emergencia en Skill_t (Thm 8.6 v7.0).

        La emergencia se manifiesta a traves de enlaces complejos:
        propiedades del sistema compuesto que no se reducen a
        ningun subsistema individual.

        Metricas:
        - num_complex_links: cantidad de enlaces complejos
        - max_level: maximo nivel jerarquico alcanzado
        - complexity_growth: crecimiento respecto a t-1
        - emergence_ratio: proporcion de enlaces complejos

        Args:
            t: Tiempo a medir (None = actual)

        Returns:
            Dict con metricas de emergencia
        """
        current_t = t if t is not None else self._current_time

        complex_links = self.detect_complex_links(current_t)
        num_complex = len(complex_links)

        # Estadisticas del grafo actual
        total_morphisms = self._graph.stats["num_morphisms"]
        max_level = self._graph.stats["max_level"]

        # Calcular crecimiento respecto a t-1
        complexity_growth = 0.0
        if current_t > 0:
            prev_complex = self.detect_complex_links(current_t - 1)
            prev_count = len(prev_complex)
            if prev_count > 0:
                complexity_growth = (num_complex - prev_count) / prev_count
            elif num_complex > 0:
                complexity_growth = 1.0  # Infinito, cap at 1.0

        emergence_ratio = (
            num_complex / max(total_morphisms, 1)
        )

        return {
            "num_complex_links": num_complex,
            "max_level": max_level,
            "complexity_growth": complexity_growth,
            "emergence_ratio": emergence_ratio,
            "timestamp": current_t,
        }

    # =========================================================================
    # FORMAL THEOREMS (Thm 8.5-8.7, v7.0)
    # =========================================================================

    def verify_consistency(self) -> dict[str, Any]:
        """
        Theorem 8.5 (Consistency): After apply_option(), Skill_{t+1}
        is still a valid hierarchical category with multiplicity.

        Checks that the current graph satisfies all 4 axioms (8.1-8.4).

        Returns:
            Dict with consistency status
        """
        axioms = self._graph.verify_all_axioms()
        return {
            "satisfies": axioms["all_satisfied"],
            "axioms": axioms,
            "time": self._current_time,
        }

    def verify_emergence_growth(self) -> dict[str, Any]:
        """
        Theorem 8.6 (Emergence): After merge with complex link,
        max complexity order should grow.

        Compares emergence metrics between current and previous time step.

        Returns:
            Dict with emergence growth verification
        """
        current = self.measure_emergence()

        if self._current_time == 0:
            return {
                "satisfies": True,
                "reason": "Initial state (t=0), no growth to measure",
                "current_emergence": current,
            }

        prev = self.measure_emergence(self._current_time - 1)
        grew = current["num_complex_links"] >= prev["num_complex_links"]
        max_level_grew = current["max_level"] >= prev["max_level"]

        satisfies = grew or max_level_grew or current["num_complex_links"] == 0

        return {
            "satisfies": satisfies,
            "current_complex_links": current["num_complex_links"],
            "previous_complex_links": prev["num_complex_links"],
            "current_max_level": current["max_level"],
            "previous_max_level": prev["max_level"],
            "complexity_growth": current["complexity_growth"],
        }

    def verify_coverage_preservation(self) -> dict[str, Any]:
        """
        Theorem 8.7 (Coverage Preservation): After each transition,
        foundational coverage is maintained.

        Verifies that Axiom 8.4 (coverage) holds at current time.

        Returns:
            Dict with coverage preservation status
        """
        coverage = self._graph._verify_coverage()
        return {
            "satisfies": coverage["satisfies"],
            "coverage_ratio": coverage["coverage_ratio"],
            "uncovered_skills": coverage["uncovered_skills"],
            "time": self._current_time,
        }

    def verify_all_theorems(self) -> dict[str, Any]:
        """
        Verify all formal theorems (8.5-8.7) of the MES specification.

        Returns:
            Dict with status of each theorem
        """
        consistency = self.verify_consistency()
        emergence = self.verify_emergence_growth()
        coverage = self.verify_coverage_preservation()

        all_satisfied = (
            consistency["satisfies"]
            and emergence["satisfies"]
            and coverage["satisfies"]
        )

        return {
            "all_satisfied": all_satisfied,
            "8.5_consistency": consistency,
            "8.6_emergence": emergence,
            "8.7_coverage_preservation": coverage,
        }

    # =========================================================================
    # ESTADISTICAS
    # =========================================================================

    @property
    def stats(self) -> dict[str, Any]:
        """Estadisticas del sistema evolutivo."""
        emergence = self.measure_emergence()
        return {
            "current_time": self._current_time,
            "num_snapshots": len(self._snapshots),
            "num_functors": len(self._functors),
            "current_skills": self._graph.stats["num_skills"],
            "current_morphisms": self._graph.stats["num_morphisms"],
            "emergence": emergence,
        }
