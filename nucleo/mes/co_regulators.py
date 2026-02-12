"""
Co-Regulators Network - MES v7.0
================================

Red de co-reguladores que implementa la Dinamica Global.
Cada co-regulador opera a su propio nivel y escala temporal.

Definicion 4.1 (v7.0):
- CR_tac (Tactico): Nivel 0-1, cada interaccion
- CR_org (Organizativo): Nivel 1-2, cada k interacciones
- CR_str (Estrategico): Nivel 2-3, cada K sesiones
- CR_int (Integridad): Transversal, periodico

Axioma 9.5 (Prioridad): CR_int > CR_str > CR_org > CR_tac
Protocolo de transicion global (Seccion 8):
  CRs proponen opciones -> CR_int filtra conflictos -> complejificacion
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

from nucleo.types import (
    ActionType,
    CoRegulatorType,
    MESActionType,
    MorphismType,
    Option,
    Fracture,
    FractureType,
)

if TYPE_CHECKING:
    from nucleo.graph.category import SkillCategory
    from nucleo.mes.memory import MESMemory
    from nucleo.mes.patterns import PatternManager, ColimitBuilder

logger = logging.getLogger(__name__)


@dataclass
class Landscape:
    """
    Paisaje de un co-regulador (Def. 2.13 v7.0).

    Vista parcial del sistema que el co-regulador usa para tomar decisiones.
    No es parte del sistema, sino un modelo interno.
    """
    co_regulator_type: CoRegulatorType
    timestamp: datetime = field(default_factory=datetime.now)
    relevant_skills: list[str] = field(default_factory=list)
    relevant_patterns: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    anticipated_next: Optional[dict[str, Any]] = None


@dataclass
class CoRegulatorState:
    """Estado interno de un co-regulador."""
    step_count: int = 0
    last_activation: Optional[datetime] = None
    pending_options: list[Option] = field(default_factory=list)
    detected_fractures: list[Fracture] = field(default_factory=list)


@dataclass
class GlobalDecision:
    """
    Resultado del protocolo de transicion global (Seccion 8 v7.0).

    Encapsula la decision colectiva de los co-reguladores.

    Attributes:
        action_type: Accion a ejecutar (RESPONSE, ASSIST, REORGANIZE)
        source_cr: Co-regulador que origino la decision
        option: Opcion seleccionada
        confidence: Confianza en la decision [0, 1]
        cr_proposals: Propuestas individuales de cada CR activo
    """
    action_type: ActionType
    source_cr: CoRegulatorType
    option: Option = field(default_factory=Option)
    confidence: float = 0.8
    cr_proposals: dict[str, MESActionType] = field(default_factory=dict)


class CoRegulator(ABC):
    """
    Co-regulador base (Def. 4.1 v7.0).

    Cada co-regulador ejecuta un ciclo de 4 fases (Seccion 4.3):
    1. Construccion del paisaje (decodificacion)
    2. Seleccion de objetivos
    3. Codificacion del procedimiento
    4. Evaluacion

    Attributes:
        cr_type: Tipo de co-regulador
        level_range: Rango de niveles en que opera (min, max)
        frequency: Cada cuantos pasos se activa
    """

    def __init__(
        self,
        cr_type: CoRegulatorType,
        level_range: tuple[int, int],
        frequency: int = 1,
        memory: Optional[MESMemory] = None,
        pattern_manager: Optional[PatternManager] = None,
        colimit_builder: Optional[ColimitBuilder] = None,
    ):
        self.cr_type = cr_type
        self.level_range = level_range
        self.frequency = frequency
        self._state = CoRegulatorState()
        self._memory = memory
        self._pattern_manager = pattern_manager
        self._colimit_builder = colimit_builder
        self._current_graph: Optional[SkillCategory] = None

    @property
    def step_count(self) -> int:
        return self._state.step_count

    def should_activate(self) -> bool:
        """Determinar si el co-regulador debe activarse."""
        return self._state.step_count % self.frequency == 0

    def tick(self) -> None:
        """Incrementar contador de pasos."""
        self._state.step_count += 1

    @abstractmethod
    def build_landscape(self, graph: SkillCategory) -> Landscape:
        """
        Fase 1: Construir paisaje desde el grafo.

        Args:
            graph: Grafo de skills actual

        Returns:
            Paisaje con vista parcial relevante
        """
        pass

    @abstractmethod
    def select_objectives(self, landscape: Landscape) -> Option:
        """
        Fase 2: Seleccionar objetivos basados en el paisaje.

        Args:
            landscape: Paisaje actual

        Returns:
            Opcion con objetivos seleccionados
        """
        pass

    @abstractmethod
    def encode_procedure(self, option: Option) -> MESActionType:
        """
        Fase 3: Codificar procedimiento para ejecutar.

        Args:
            option: Opcion seleccionada

        Returns:
            Tipo de accion MES a ejecutar
        """
        pass

    @abstractmethod
    def evaluate(
        self,
        anticipated: Landscape,
        actual: Landscape
    ) -> float:
        """
        Fase 4: Evaluar resultado comparando paisajes.

        Args:
            anticipated: Paisaje anticipado
            actual: Paisaje real

        Returns:
            Score de evaluacion
        """
        pass

    def run_cycle(self, graph: SkillCategory) -> tuple[MESActionType, Option]:
        """
        Ejecutar ciclo completo del co-regulador.

        Returns:
            Tupla (accion, opcion) a ejecutar
        """
        if not self.should_activate():
            self.tick()
            return MESActionType.RESPONSE, Option()

        # Guardar referencia al grafo para select_objectives
        self._current_graph = graph

        # Fase 1: Construir paisaje
        landscape = self.build_landscape(graph)

        # Fase 2: Seleccionar objetivos
        option = self.select_objectives(landscape)

        # Fase 3: Codificar procedimiento
        action = self.encode_procedure(option)

        # Guardar paisaje anticipado para evaluacion posterior
        landscape.anticipated_next = {"action": action, "option": option}

        self._state.last_activation = datetime.now()
        self.tick()

        return action, option


class TacticalCoRegulator(CoRegulator):
    """
    Co-regulador tactico (CR_tac).

    - Nivel: 0-1 (atomos y clusters)
    - Escala temporal: Rapida (cada interaccion)
    - Procedimientos: select, compose, translate
    - Efectores: Interfaz LLM <-> Lean 4

    Seleccion de procedimiento (Seccion 4.3):
    - Busqueda por similitud en memoria procedural
    - Si no hay match, heuristica basada en contenido del query
    """

    # Keywords that indicate a Lean/formal query
    ASSIST_KEYWORDS = {
        "lean", "theorem", "proof", "lemma", "sorry", "tactic",
        "formaliza", "formalize", "demuestra", "prove", "```lean",
        "induction", "rfl", "simp", "exact", "apply",
    }

    def __init__(
        self,
        frequency: int = 1,
        memory: Optional[MESMemory] = None,
        pattern_manager: Optional[PatternManager] = None,
        colimit_builder: Optional[ColimitBuilder] = None,
    ):
        super().__init__(
            cr_type=CoRegulatorType.TACTICAL,
            level_range=(0, 1),
            frequency=frequency,
            memory=memory,
            pattern_manager=pattern_manager,
            colimit_builder=colimit_builder,
        )
        self._current_query: str = ""

    def build_landscape(self, graph: SkillCategory) -> Landscape:
        """Construir paisaje tactico: skills de nivel 0-1 y patrones relevantes."""
        relevant = []
        relevant_patterns: list[str] = []

        for skill_id in graph.skill_ids:
            skill = graph.get_skill(skill_id)
            if skill and skill.level <= 1:
                relevant.append(skill_id)
                # Collect patterns containing this skill
                if self._pattern_manager:
                    for pat in self._pattern_manager.get_patterns_containing(skill_id):
                        if pat.id not in relevant_patterns:
                            relevant_patterns.append(pat.id)

        return Landscape(
            co_regulator_type=self.cr_type,
            relevant_skills=relevant[:50],
            relevant_patterns=relevant_patterns,
            metrics={
                "num_skills_0": sum(
                    1 for s in relevant if graph.get_skill(s).level == 0
                ),
                "num_skills_1": sum(
                    1 for s in relevant if graph.get_skill(s).level == 1
                ),
            }
        )

    def select_objectives(self, landscape: Landscape) -> Option:
        """
        Seleccionar skills para respuesta (Seccion 4.3 v7.0).

        Consulta memoria procedural para procedimientos exitosos.
        Si encuentra uno con buena tasa de exito, lo reutiliza.
        """
        if self._memory and landscape.relevant_patterns:
            for pattern_id in landscape.relevant_patterns:
                best_proc = self._memory.procedural.get_best_procedure(pattern_id)
                if best_proc and best_proc.success_rate > 0.5:
                    logger.debug(
                        f"CR_tac: Procedimiento {best_proc.id} encontrado "
                        f"(exito={best_proc.success_rate:.2f})"
                    )
                    return Option(
                        bindings=[pattern_id],
                        metadata={"procedure_id": best_proc.id},
                    )

        return Option()

    def encode_procedure(self, option: Option) -> MESActionType:
        """Codificar como respuesta o asistencia basado en el query."""
        query_lower = self._current_query.lower()
        if any(kw in query_lower for kw in self.ASSIST_KEYWORDS):
            return MESActionType.ASSIST
        return MESActionType.RESPONSE

    def classify_query(self, query: str) -> ActionType:
        """
        Clasificar un query en tipo de accion (Seccion 4.3 v7.0).

        Usa keywords como heuristica. En futuro, se puede usar
        embedding similarity contra memoria procedural.
        """
        self._current_query = query
        query_lower = query.lower()
        if any(kw in query_lower for kw in self.ASSIST_KEYWORDS):
            return ActionType.ASSIST
        return ActionType.RESPONSE

    def evaluate(self, anticipated: Landscape, actual: Landscape) -> float:
        """Evaluar si la respuesta fue exitosa."""
        return 1.0 if actual.metrics.get("success", False) else 0.0


class OrganizationalCoRegulator(CoRegulator):
    """
    Co-regulador organizativo (CR_org).

    - Nivel: 1-2 (clusters y habilidades)
    - Escala temporal: Media (cada k interacciones)
    - Procedimientos: merge, split, reweight, add_bridge
    - Efectores: Motor de reorganizacion
    """

    def __init__(
        self,
        frequency: int = 10,
        memory: Optional[MESMemory] = None,
        pattern_manager: Optional[PatternManager] = None,
        colimit_builder: Optional[ColimitBuilder] = None,
    ):
        super().__init__(
            cr_type=CoRegulatorType.ORGANIZATIONAL,
            level_range=(1, 2),
            frequency=frequency,
            memory=memory,
            pattern_manager=pattern_manager,
            colimit_builder=colimit_builder,
        )

    def build_landscape(self, graph: SkillCategory) -> Landscape:
        """Construir paisaje organizativo: estadisticas y coherencia."""
        stats = graph.stats
        num_unbound = 0
        if self._pattern_manager and self._colimit_builder:
            num_unbound = sum(
                1 for p in self._pattern_manager.all_patterns
                if not self._colimit_builder.has_colimit(p.id)
            )

        return Landscape(
            co_regulator_type=self.cr_type,
            metrics={
                "num_skills": stats.get("num_skills", 0),
                "num_morphisms": stats.get("num_morphisms", 0),
                "avg_degree": (
                    stats.get("num_morphisms", 0)
                    / max(stats.get("num_skills", 1), 1)
                ),
                "num_unbound_patterns": float(num_unbound),
            }
        )

    def select_objectives(self, landscape: Landscape) -> Option:
        """
        Seleccionar reorganizaciones necesarias (Seccion 4.3 v7.0).

        1. Detecta patrones sin colimite y propone ligaduras
        2. Detecta skills debiles y propone eliminacion
        """
        graph = self._current_graph
        if not graph:
            return Option()

        # 1. Bind unbound patterns
        if self._pattern_manager and self._colimit_builder:
            unbound = [
                p for p in self._pattern_manager.all_patterns
                if not self._colimit_builder.has_colimit(p.id)
            ]
            if unbound:
                bindings = [p.id for p in unbound[:3]]
                logger.debug(
                    f"CR_org: {len(unbound)} patrones sin colimite, "
                    f"ligando {len(bindings)}"
                )
                return Option(bindings=bindings)

        # 2. Eliminate weak skills (low morphism weight)
        weak_threshold = 0.5
        weak: list[str] = []
        for skill_id in graph.skill_ids:
            skill = graph.get_skill(skill_id)
            if not skill or skill.level > 0:
                continue  # Only evaluate atoms
            max_weight = 0.0
            for morph in graph.outgoing_morphisms(skill_id):
                if morph.morphism_type != MorphismType.IDENTITY:
                    max_weight = max(max_weight, morph.weight)
            if 0 < max_weight < weak_threshold:
                weak.append(skill_id)

        if weak:
            eliminations = weak[:2]
            logger.debug(
                f"CR_org: {len(weak)} skills debiles, "
                f"eliminando {len(eliminations)}"
            )
            return Option(eliminations=eliminations)

        return Option()

    def encode_procedure(self, option: Option) -> MESActionType:
        """Codificar como reorganizacion si hay trabajo, noop si no."""
        if option.bindings:
            return MESActionType.COMPLEXIFY
        if option.eliminations:
            return MESActionType.REORGANIZE
        return MESActionType.RESPONSE

    def evaluate(self, anticipated: Landscape, actual: Landscape) -> float:
        """Evaluar mejora en organizacion."""
        prev_degree = anticipated.metrics.get("avg_degree", 0)
        curr_degree = actual.metrics.get("avg_degree", 0)
        return 1.0 if curr_degree >= prev_degree else 0.5


class StrategicCoRegulator(CoRegulator):
    """
    Co-regulador estrategico (CR_str).

    - Nivel: 2-3 (habilidades y competencias)
    - Escala temporal: Lenta (cada K sesiones)
    - Procedimientos: create_level, complexify, form_concept
    - Efectores: Motor de complejificacion
    """

    def __init__(
        self,
        frequency: int = 100,
        memory: Optional[MESMemory] = None,
        pattern_manager: Optional[PatternManager] = None,
        colimit_builder: Optional[ColimitBuilder] = None,
    ):
        super().__init__(
            cr_type=CoRegulatorType.STRATEGIC,
            level_range=(2, 3),
            frequency=frequency,
            memory=memory,
            pattern_manager=pattern_manager,
            colimit_builder=colimit_builder,
        )

    def build_landscape(self, graph: SkillCategory) -> Landscape:
        """Construir paisaje estrategico: niveles y patrones emergentes."""
        level_counts: dict[int, int] = {}
        for skill_id in graph.skill_ids:
            skill = graph.get_skill(skill_id)
            if skill:
                level = skill.level
                level_counts[level] = level_counts.get(level, 0) + 1

        num_complex = len(graph.get_complex_links())

        return Landscape(
            co_regulator_type=self.cr_type,
            metrics={
                "max_level": max(level_counts.keys()) if level_counts else 0,
                "level_distribution": level_counts,
                "num_complex_links": float(num_complex),
            }
        )

    def select_objectives(self, landscape: Landscape) -> Option:
        """
        Seleccionar complejificaciones estrategicas (Seccion 4.3 v7.0).

        Busca enlaces complejos (emergencia) y crea patrones
        para complejificar, creando nuevos niveles jerarquicos.
        """
        graph = self._current_graph
        if not graph or not self._pattern_manager:
            return Option()

        complex_links = graph.get_complex_links()
        if not complex_links:
            return Option()

        # Group skills connected by complex links
        skills_in_complex: set[str] = set()
        for morph in complex_links:
            skills_in_complex.add(morph.source_id)
            skills_in_complex.add(morph.target_id)

        if len(skills_in_complex) < 2:
            return Option()

        skill_list = list(skills_in_complex)[:5]
        link_ids = [
            m.id for m in complex_links
            if m.source_id in skill_list and m.target_id in skill_list
        ]

        if link_ids:
            pattern = self._pattern_manager.create_pattern(
                skill_list, link_ids, graph=graph
            )
            logger.debug(
                f"CR_str: {len(complex_links)} enlaces complejos, "
                f"patron {pattern.id} para complejificacion"
            )
            return Option(bindings=[pattern.id])

        return Option()

    def encode_procedure(self, option: Option) -> MESActionType:
        """Codificar como complejificacion si hay bindings, noop si no."""
        if option.bindings:
            return MESActionType.COMPLEXIFY
        return MESActionType.RESPONSE

    def evaluate(self, anticipated: Landscape, actual: Landscape) -> float:
        """Evaluar emergencia de nuevos niveles."""
        prev_max = anticipated.metrics.get("max_level", 0)
        curr_max = actual.metrics.get("max_level", 0)
        return 2.0 if curr_max > prev_max else 1.0


class IntegrityCoRegulator(CoRegulator):
    """
    Co-regulador de integridad (CR_int).

    - Nivel: Transversal (todos)
    - Escala temporal: Periodica
    - Procedimientos: verify_connectivity, check_coverage, validate_consistency
    - Efectores: Sistema de reparacion
    """

    def __init__(
        self,
        frequency: int = 50,
        memory: Optional[MESMemory] = None,
        pattern_manager: Optional[PatternManager] = None,
        colimit_builder: Optional[ColimitBuilder] = None,
    ):
        super().__init__(
            cr_type=CoRegulatorType.INTEGRITY,
            level_range=(0, 10),
            frequency=frequency,
            memory=memory,
            pattern_manager=pattern_manager,
            colimit_builder=colimit_builder,
        )

    def build_landscape(self, graph: SkillCategory) -> Landscape:
        """
        Construir paisaje de integridad: invariantes del sistema.

        Incluye verificacion de:
        - Conectividad (Axioma 8.3)
        - Cobertura de pilares (Axioma 8.4)
        - Axiomas categoricos
        - Multiplicidad (Axioma 8.2) via PatternManager
        """
        # Verificar conectividad real (Axioma 8.3)
        is_connected = graph.is_connected() if graph.skill_ids else False

        # Verificar cobertura de pilares (Axioma 8.4)
        pillar_dist = graph.get_pillar_distribution()
        has_pillars = len(pillar_dist) >= 2

        # Verificar axiomas categoricos
        axiom_results = graph.verify_axioms()
        axioms_ok = all(axiom_results.values())

        # Verificar multiplicidad (Axioma 8.2)
        multiplicity_holds = False
        if self._pattern_manager:
            mult_result = self._pattern_manager.verify_multiplicity_principle(
                graph, self._colimit_builder
            )
            multiplicity_holds = mult_result["satisfies"]

        return Landscape(
            co_regulator_type=self.cr_type,
            metrics={
                "is_connected": float(is_connected),
                "has_all_pillars": float(has_pillars),
                "axioms_satisfied": float(axioms_ok),
                "multiplicity_holds": float(multiplicity_holds),
                "num_fractures": float(len(self._state.detected_fractures)),
            }
        )

    def select_objectives(self, landscape: Landscape) -> Option:
        """
        Seleccionar reparaciones necesarias (Def 7.4 v7.0).

        Si hay fracturas no reparadas, intenta detectar nuevos
        patrones para restaurar multiplicidad.
        """
        unrepaired = [f for f in self._state.detected_fractures if not f.repaired]
        if not unrepaired:
            return Option()

        graph = self._current_graph
        if not graph:
            return Option()

        for fracture in unrepaired:
            actual = fracture.actual_state
            # If multiplicity lost, try to detect new patterns
            if actual.get("multiplicity_holds", 1.0) == 0 and self._pattern_manager:
                detected = self._pattern_manager.detect_pattern_in_graph(graph)
                if detected:
                    logger.debug(
                        f"CR_int: Reparando multiplicidad con "
                        f"{len(detected)} patrones nuevos"
                    )
                    return Option(bindings=[p.id for p in detected[:2]])

        return Option()

    def encode_procedure(self, option: Option) -> MESActionType:
        """Codificar como reparacion si hay fracturas."""
        if self._state.detected_fractures:
            return MESActionType.REPAIR_FRACTURE
        return MESActionType.RESPONSE

    def evaluate(self, anticipated: Landscape, actual: Landscape) -> float:
        """Evaluar integridad del sistema."""
        connected = actual.metrics.get("is_connected", 0)
        pillars = actual.metrics.get("has_all_pillars", 0)
        return (connected + pillars) / 2.0

    def resolve_conflicts(
        self,
        proposals: list[tuple[CoRegulatorType, MESActionType, Option]],
    ) -> tuple[CoRegulatorType, MESActionType, Option]:
        """
        Resolver conflictos entre propuestas de CRs (Axioma 9.5 v7.0).

        Prioridad: CR_int > CR_str > CR_org > CR_tac.
        Si CR_int tiene propuesta activa (reparacion), toma precedencia.
        """
        priority = {
            CoRegulatorType.INTEGRITY: 4,
            CoRegulatorType.STRATEGIC: 3,
            CoRegulatorType.ORGANIZATIONAL: 2,
            CoRegulatorType.TACTICAL: 1,
        }

        # Filter out no-op proposals (empty options with RESPONSE)
        active = [
            (cr_type, action, option)
            for cr_type, action, option in proposals
            if option.bindings or option.absorptions or option.eliminations
            or action != MESActionType.RESPONSE
        ]

        if not active:
            # All no-ops: return tactical default
            for cr_type, action, option in proposals:
                if cr_type == CoRegulatorType.TACTICAL:
                    return cr_type, action, option
            return proposals[0] if proposals else (
                CoRegulatorType.TACTICAL, MESActionType.RESPONSE, Option()
            )

        # Sort by priority (highest first)
        active.sort(key=lambda x: priority.get(x[0], 0), reverse=True)
        winner = active[0]
        logger.debug(
            f"CR_int: Conflicto resuelto -> {winner[0].name} "
            f"(accion={winner[1].name})"
        )
        return winner

    def detect_fracture(
        self,
        anticipated: Landscape,
        actual: Landscape
    ) -> Optional[Fracture]:
        """
        Detectar fractura estructural comparando paisajes (Def. 7.4 v7.0).

        Una fractura se detecta cuando un invariante que se cumplia
        deja de cumplirse (transicion de True a False).

        Returns:
            Fractura si se detecta, None en caso contrario
        """
        for key in ["axioms_satisfied", "multiplicity_holds", "is_connected"]:
            anticipated_val = anticipated.metrics.get(key, 1.0)
            actual_val = actual.metrics.get(key, 1.0)
            if anticipated_val > 0 and actual_val == 0:
                fracture = Fracture(
                    fracture_type=FractureType.STRUCTURAL,
                    co_regulator=self.cr_type,
                    anticipated_state=anticipated.metrics,
                    actual_state=actual.metrics,
                )
                self._state.detected_fractures.append(fracture)
                logger.warning(
                    f"CR_int: Fractura detectada - {key} "
                    f"paso de {anticipated_val} a {actual_val}"
                )
                return fracture
        return None


class CoRegulatorNetwork:
    """
    Red de co-reguladores del NLE (Def. 4.1 v7.0).

    Coordina los 4 co-reguladores operando a diferentes escalas.
    Recibe recursos compartidos (memoria, patrones, colimites) y
    los distribuye a cada co-regulador.
    """

    def __init__(
        self,
        memory: Optional[MESMemory] = None,
        pattern_manager: Optional[PatternManager] = None,
        colimit_builder: Optional[ColimitBuilder] = None,
        cr_org_frequency: int = 10,
        cr_str_frequency: int = 100,
        cr_int_frequency: int = 50
    ):
        self.tactical = TacticalCoRegulator(
            frequency=1,
            memory=memory,
            pattern_manager=pattern_manager,
            colimit_builder=colimit_builder,
        )
        self.organizational = OrganizationalCoRegulator(
            frequency=cr_org_frequency,
            memory=memory,
            pattern_manager=pattern_manager,
            colimit_builder=colimit_builder,
        )
        self.strategic = StrategicCoRegulator(
            frequency=cr_str_frequency,
            memory=memory,
            pattern_manager=pattern_manager,
            colimit_builder=colimit_builder,
        )
        self.integrity = IntegrityCoRegulator(
            frequency=cr_int_frequency,
            memory=memory,
            pattern_manager=pattern_manager,
            colimit_builder=colimit_builder,
        )

        self._regulators = [
            self.tactical,
            self.organizational,
            self.strategic,
            self.integrity
        ]

    def step(self, graph: SkillCategory) -> list[tuple[CoRegulatorType, MESActionType, Option]]:
        """
        Ejecutar un paso de todos los co-reguladores.

        Returns:
            Lista de (tipo, accion, opcion) para cada co-regulador activo
        """
        results = []
        for cr in self._regulators:
            if cr.should_activate():
                action, option = cr.run_cycle(graph)
                results.append((cr.cr_type, action, option))
            else:
                cr.tick()
        return results

    def decide(self, query: str, graph: SkillCategory) -> GlobalDecision:
        """
        Protocolo de transicion global (Seccion 8 v7.0).

        Ejecuta la Dinamica Global:
        1. CR_tac clasifica el query (RESPONSE vs ASSIST)
        2. Todos los CRs activos proponen opciones
        3. CR_int resuelve conflictos (Axioma 9.5)
        4. Retorna decision global

        Args:
            query: Texto de entrada del usuario
            graph: Grafo de skills actual

        Returns:
            GlobalDecision con la accion a ejecutar
        """
        # Fase 1: CR_tac clasifica el query
        action_type = self.tactical.classify_query(query)

        # Fase 2: Recoger propuestas de todos los CRs activos
        proposals = self.step(graph)
        cr_proposals = {
            cr_type.name: action.name
            for cr_type, action, _ in proposals
        }

        if not proposals:
            return GlobalDecision(
                action_type=action_type,
                source_cr=CoRegulatorType.TACTICAL,
                confidence=0.7,
                cr_proposals=cr_proposals,
            )

        # Fase 3: CR_int resuelve conflictos
        winner_cr, winner_action, winner_option = (
            self.integrity.resolve_conflicts(proposals)
        )

        # Map MESActionType back to ActionType for the decision
        mes_to_action = {
            MESActionType.RESPONSE: ActionType.RESPONSE,
            MESActionType.ASSIST: ActionType.ASSIST,
            MESActionType.REORGANIZE: ActionType.REORGANIZE,
            MESActionType.COMPLEXIFY: ActionType.REORGANIZE,
            MESActionType.FORM_CONCEPT: ActionType.REORGANIZE,
            MESActionType.REPAIR_FRACTURE: ActionType.REORGANIZE,
        }

        # If winner is tactical, use the query-based classification
        if winner_cr == CoRegulatorType.TACTICAL:
            final_action = action_type
        else:
            final_action = mes_to_action.get(
                winner_action, ActionType.RESPONSE
            )

        # Confidence based on source
        confidence_map = {
            CoRegulatorType.INTEGRITY: 0.95,
            CoRegulatorType.STRATEGIC: 0.85,
            CoRegulatorType.ORGANIZATIONAL: 0.75,
            CoRegulatorType.TACTICAL: 0.8,
        }

        return GlobalDecision(
            action_type=final_action,
            source_cr=winner_cr,
            option=winner_option,
            confidence=confidence_map.get(winner_cr, 0.7),
            cr_proposals=cr_proposals,
        )

    def record_result(
        self,
        decision: GlobalDecision,
        success: float,
        graph: SkillCategory,
    ) -> None:
        """
        Fase de evaluacion post-ejecucion (Seccion 4.3 fase 4).

        Cada CR activo evalua el resultado comparando paisajes.
        CR_int detecta fracturas si hay invariantes violados.

        Args:
            decision: Decision que se ejecuto
            success: Valor de exito [-1, 1]
            graph: Grafo actual post-ejecucion
        """
        for cr in self._regulators:
            if cr.should_activate():
                actual_landscape = cr.build_landscape(graph)
                actual_landscape.metrics["success"] = success > 0

                # CR_int checks for fractures
                if cr.cr_type == CoRegulatorType.INTEGRITY:
                    anticipated = cr.build_landscape(graph)
                    anticipated.metrics["success"] = True
                    self.integrity.detect_fracture(anticipated, actual_landscape)

        logger.debug(
            f"Resultado registrado: CR={decision.source_cr.name}, "
            f"exito={success:.2f}"
        )

    def get_active_regulators(self) -> list[CoRegulator]:
        """Obtener co-reguladores que deben activarse."""
        return [cr for cr in self._regulators if cr.should_activate()]

    @property
    def stats(self) -> dict[str, Any]:
        """Estadisticas de la red."""
        return {
            "tactical_steps": self.tactical.step_count,
            "organizational_steps": self.organizational.step_count,
            "strategic_steps": self.strategic.step_count,
            "integrity_steps": self.integrity.step_count,
            "detected_fractures": len(self.integrity._state.detected_fractures),
        }
