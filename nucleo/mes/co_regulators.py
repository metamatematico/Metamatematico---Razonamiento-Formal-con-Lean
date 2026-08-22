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

    # Keywords unambiguously Lean-specific (never appear in normal math prose)
    ASSIST_KEYWORDS = {
        "lean", "sorry", "rfl", "simp",
        "linarith", "norm_num", "aesop",
        "native_decide", "#check", "#eval", "```lean",
    }

    # Multi-word phrases that explicitly request Lean formalization
    # (single words like "ring", "apply", "exact", "decide" are too ambiguous
    # — they appear in everyday math prose like "ring theory" or "apply theorem")
    ASSIST_PHRASES = (
        "en lean", "in lean", "lean 4", "lean4",
        "formaliza", "formalize",
        "prueba formal", "formal proof",
        "escribe el proof", "write the proof",
        "código lean", "lean code",
        "ring tactic", "apply tactic",
        "exact tactic", "decide tactic",
    )

    # If query starts with or contains these, classify as RESPONSE
    # regardless of other signals (prevents false ASSIST)
    RESPONSE_OVERRIDE = (
        "qué es", "que es", "what is", "what are",
        "explica", "explain", "describe",
        "cómo funciona", "como funciona", "how does",
        "cuál es", "cual es", "por qué", "porque", "why",
        "definición", "definition", "define",
        "ejemplo", "example", "dame un ejemplo",
        "intuición", "intuicion", "intuition",
        "cuándo", "cuando", "when",
    )

    def __init__(
        self,
        frequency: int = 1,
        memory: Optional[MESMemory] = None,
        pattern_manager: Optional[PatternManager] = None,
        colimit_builder: Optional[ColimitBuilder] = None,
        neural_agent=None,
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
        self._neural_agent = neural_agent
        self._relevant_skills: list[str] = []  # Skills matched by last query

    #: Cota del paisaje. No es un corte de nivel: primero entran los skills que
    #: la consulta activo, despues sus vecinos, y solo al final se rellena.
    _MAX_PAISAJE = 60

    def build_landscape(self, graph: SkillCategory) -> Landscape:
        """
        Paisaje tactico: los skills RELEVANTES a la consulta, de cualquier nivel.

        Antes el criterio era `skill.level <= 1`, un corte de nivel arbitrario:
        con 172 skills en el grafo eso dejaba fuera 129 —los 34 de L2 y los 95
        de L3— y ademas truncaba a 50. CR_tac, que es el co-regulador que de
        hecho decide la accion de cada consulta, era ciego a tres cuartas partes
        del grafo, y en particular a las sub-ramas L3, que son justamente las que
        llevan keywords ES+EN para que las consultas en español encuentren skill.

        Un paisaje es "una vista PARCIAL del sistema que el co-regulador usa para
        decidir" (Def. 2.13). Lo que la hace parcial debe ser la RELEVANCIA a la
        consulta, no la altura en la taxonomia.

        Orden de llenado:
          1. skills que la consulta activo (classify_query -> _relevant_skills)
          2. sus vecinos inmediatos: el contexto que hace falta para decidir
          3. si aun no hay consulta, los fundacionales como base
        """
        relevant: list[str] = []
        vistos: set[str] = set()

        def _anadir(sid: str) -> None:
            if sid not in vistos and graph.get_skill(sid) is not None:
                vistos.add(sid)
                relevant.append(sid)

        # 1. Lo que activo la consulta — de cualquier nivel.
        for sid in (self._relevant_skills or []):
            _anadir(sid)

        # 2. Sus vecinos: sin ellos el paisaje no tiene contexto para decidir.
        for sid in list(relevant):
            for nbr in graph.neighbors(sid):
                if len(relevant) >= self._MAX_PAISAJE:
                    break
                _anadir(nbr)

        # 3. Sin consulta todavia: los fundacionales son la base del grafo.
        if not relevant:
            for sid in graph.skill_ids:
                sk = graph.get_skill(sid)
                if sk and sk.level == 0:
                    _anadir(sid)

        relevant = relevant[: self._MAX_PAISAJE]

        relevant_patterns: list[str] = []
        if self._pattern_manager:
            for sid in relevant:
                for pat in self._pattern_manager.get_patterns_containing(sid):
                    if pat.id not in relevant_patterns:
                        relevant_patterns.append(pat.id)

        # Metricas por nivel, TODOS los niveles. Contar solo 0 y 1 hacia que un
        # paisaje lleno de sub-ramas L3 se reportara como vacio.
        por_nivel: dict[int, int] = {}
        for sid in relevant:
            sk = graph.get_skill(sid)
            if sk:
                por_nivel[sk.level] = por_nivel.get(sk.level, 0) + 1

        metrics = {f"num_skills_{k}": float(v) for k, v in sorted(por_nivel.items())}
        metrics["num_relevantes"] = float(len(relevant))
        metrics["cobertura"] = (
            len(relevant) / max(len(graph.skill_ids), 1)
        )

        return Landscape(
            co_regulator_type=self.cr_type,
            relevant_skills=relevant,
            relevant_patterns=relevant_patterns,
            metrics=metrics,
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
                if best_proc and best_proc.success_rate > 0.3:
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
        return (
            MESActionType.ASSIST
            if self._is_lean_query(self._current_query)
            else MESActionType.RESPONSE
        )

    def _is_lean_query(self, query: str) -> bool:
        """True solo si el query solicita explícitamente código/prueba Lean."""
        q = query.lower()
        if any(phrase in q for phrase in self.RESPONSE_OVERRIDE):
            return False
        if any(kw in q for kw in self.ASSIST_KEYWORDS):
            return True
        if any(phrase in q for phrase in self.ASSIST_PHRASES):
            return True
        return False

    # Sonda deliberadamente heterogenea: matematica, saludo, hecho no
    # matematico y codigo Lean explicito. Una red util no puede dar la misma
    # accion a las cuatro.
    _DEGENERACY_PROBE = (
        "Demuestra que la raiz de 2 es irracional",
        "Hola, como estas",
        "Cual es la capital de Francia",
        "```lean\ntheorem t : 1 = 1 := rfl\n```",
    )

    def _neural_agent_is_degenerate(self) -> bool:
        """True si la red devuelve siempre la misma accion (no discrimina).

        Se evalua una sola vez por agente y se cachea: es una propiedad de los
        pesos, no de la consulta.
        """
        agent = self._neural_agent
        if agent is None:
            return True
        cached = getattr(agent, "_degenerate_cache", None)
        if cached is not None:
            return cached

        from nucleo.types import State
        try:
            acciones = {
                agent._select_neural(State(lean_goal=q)).action_type
                for q in self._DEGENERACY_PROBE
            }
            degenerada = len(acciones) <= 1
        except Exception:
            degenerada = True   # si no se puede evaluar, no confiar en ella

        if degenerada:
            logger.warning(
                "Red neuronal degenerada (misma accion para toda la sonda): "
                "se ignora y se usa la heuristica de CR_tac"
            )
        agent._degenerate_cache = degenerada
        return degenerada

    def classify_query(
        self, query: str, graph: Optional[SkillCategory] = None
    ) -> ActionType:
        """
        Clasificar un query en tipo de accion (Seccion 4.3 v7.0).

        Classification chain:
        1. Neural agent (GNN+PPO) if available
        2. Keyword heuristic (fast path)
        3. Graph-based: match skills, check tactic connections

        Args:
            query: User query text
            graph: Optional skill graph for domain-aware classification
        """
        self._current_query = query
        self._relevant_skills = []

        # Clasificacion neuronal, con dos compuertas.
        #
        # (1) La red tiene que saber algo: pesos entrenados desde disco, o
        #     >= 50 transiciones acumuladas en esta sesion. Un agente recien
        #     inicializado devuelve REORGANIZE para todo y rompe el routing.
        #
        # (2) La red no puede ser DEGENERADA. Medido el 2026-08-05: los pesos
        #     actuales devuelven ASSIST para *cualquier* entrada — incluido
        #     "Hola, como estas" y "Cual es la capital de Francia". Se entreno
        #     con el objetivo "todo problema matematico -> ASSIST", asi que
        #     aprendio la constante. Una constante no enruta: aporta cero y
        #     ademas se salta la heuristica, que si distingue. Se comprueba con
        #     una sonda fija y, si colapsa, se ignora la red.
        _trained = (
            getattr(self._neural_agent, "weights_pretrained", False)
            or len(getattr(self._neural_agent, "buffer", [])) >= 50
        )
        if (self._neural_agent is not None
                and self._neural_agent.has_network
                and _trained
                and not self._neural_agent_is_degenerate()):
            from nucleo.types import State
            state = State(lean_goal=query)
            action = self._neural_agent._select_neural(state)
            # Solo aceptar RESPONSE/ASSIST; REORGANIZE es acción interna
            if action.action_type in (ActionType.RESPONSE, ActionType.ASSIST):
                return action.action_type

        # Heurística: keywords y frases Lean explícitas
        query_lower = query.lower()
        if self._is_lean_query(query):
            return ActionType.ASSIST

        # Graph-based: solo identificar skills relevantes para contexto,
        # NO redirigir a ASSIST por tener vecinos tactic/strategy —
        # esa heurística era demasiado agresiva.
        if graph is not None:
            matched = self._match_graph_skills(query_lower, graph)
            if matched:
                self._relevant_skills = matched

        return ActionType.RESPONSE

    def _match_graph_skills(
        self, query_lower: str, graph: SkillCategory
    ) -> list[str]:
        """
        Empareja skills del grafo con la consulta.

        Dos vias, en este orden:
          1. KEYWORDS de metadata — es la unica via que funciona en español.
             Los ids y los nombres del grafo estan en ingles
             (`tensor-products`, "Module Theory"), asi que una consulta como
             "producto tensorial de modulos" no casaba con nada. Las 95
             sub-ramas L3 llevan keywords ES+EN precisamente para esto.
          2. Solapamiento de tokens con id y nombre, para las consultas en
             ingles y los skills sin keywords.

        Antes solo existia la via 2, asi que _relevant_skills quedaba vacio en
        practicamente toda consulta en español y el paisaje tactico caia
        siempre al conjunto de respaldo. Es la misma logica que usa
        Nucleo._match_skills_to_query; test_paisaje_tactico verifica que las dos
        no se separen.
        """
        import re as _re

        matched: list[str] = []
        vistos: set[str] = set()

        # 1. Keywords (ES + EN), por palabra completa.
        for skill_id in graph.skill_ids:
            skill = graph.get_skill(skill_id)
            if not skill:
                continue
            for kw in (skill.metadata or {}).get("keywords", []) or []:
                kw = (kw or "").lower().strip()
                if len(kw) < 4:
                    continue
                if _re.search(rf"\b{_re.escape(kw)}\b", query_lower):
                    if skill_id not in vistos:
                        vistos.add(skill_id)
                        matched.append(skill_id)
                    break

        # 2. Tokens de id y nombre.
        query_tokens = {
            t for t in query_lower.replace("-", " ").replace("_", " ").split()
            if len(t) > 3
        }
        if query_tokens:
            for skill_id in graph.skill_ids:
                if skill_id in vistos:
                    continue
                skill = graph.get_skill(skill_id)
                if not skill:
                    continue
                skill_tokens = set(
                    skill_id.lower().replace("-", " ").split()
                    + skill.name.lower().replace("-", " ").split()
                )
                if query_tokens & skill_tokens:
                    vistos.add(skill_id)
                    matched.append(skill_id)

        return matched

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

    # Coactivaciones observadas: frozenset de skills -> veces que aparecieron
    # juntos resolviendo una consulta. Es el "paisaje de estadisticas de uso"
    # de la Def. 4.1, y la materia prima del procedimiento `merge`: skills que
    # el sistema usa siempre a la vez son candidatos a ligarse en un colimite
    # (Seccion 6.2, merge como ligadura de patron).
    _MIN_COACTIVACIONES = 3
    _MIN_SKILLS_PATRON = 2

    def record_activation(self, skill_ids: list[str]) -> None:
        """Registrar que estos skills resolvieron juntos una consulta."""
        if not hasattr(self, "_coactivaciones"):
            self._coactivaciones: dict[frozenset, int] = {}
        utiles = [s for s in skill_ids if s]
        if len(utiles) < self._MIN_SKILLS_PATRON:
            return
        clave = frozenset(utiles[:6])       # cota: patrones manejables
        self._coactivaciones[clave] = self._coactivaciones.get(clave, 0) + 1

    def build_landscape(self, graph: SkillCategory) -> Landscape:
        """Construir paisaje organizativo: estadisticas y coherencia."""
        stats = graph.stats
        num_unbound = 0
        if self._pattern_manager and self._colimit_builder:
            num_unbound = sum(
                1 for p in self._pattern_manager.all_patterns
                if not self._colimit_builder.has_colimit(p.id)
            )

        # Huecos conceptuales: patrones con co-conos pero sin co-cono limite.
        # Son el material de trabajo propio de CR_org — señalan donde al grafo
        # de conocimiento le falta el concepto que unifica un patron.
        gaps = getattr(self, "_concept_gaps", None) or []
        gap_skills: list[str] = []
        for g in gaps[:10]:
            gap_skills.extend(g.component_ids)

        return Landscape(
            co_regulator_type=self.cr_type,
            relevant_skills=list(dict.fromkeys(gap_skills))[:50],
            metrics={
                "num_skills": stats.get("num_skills", 0),
                "num_morphisms": stats.get("num_morphisms", 0),
                "avg_degree": (
                    stats.get("num_morphisms", 0)
                    / max(stats.get("num_skills", 1), 1)
                ),
                "num_unbound_patterns": float(num_unbound),
                "num_concept_gaps": float(len(gaps)),
            }
        )

    def set_concept_gaps(self, gaps: list) -> None:
        """Recibir los huecos conceptuales detectados por el punto fijo."""
        self._concept_gaps = list(gaps or [])

    def select_objectives(self, landscape: Landscape) -> Option:
        """
        Seleccionar reorganizaciones necesarias (Seccion 4.3 v7.0).

        1. Detecta patrones sin colimite y propone ligaduras
        2. Detecta skills debiles y propone eliminacion
        """
        graph = self._current_graph
        if not graph:
            return Option()

        # 0.a Huecos conceptuales primero (Seccion 6.1, ligadura).
        #
        # Un ConceptGap es un patron con co-conos pero sin co-cono limite: el
        # colimite NO existe en G_n. Es exactamente "un patron que debe adquirir
        # colimite" (Def. 2.9, ligadura), asi que se propone como binding.
        #
        # La ligadura solo tendra exito cuando el concepto que unifica las
        # componentes exista con contenido matematico. De eso se encarga
        # Nucleo._llenar_hueco_conceptual: LLM propone, Lean verifica, y solo
        # entonces entra el nodo. Aqui CR_org unicamente señala DONDE.
        _gaps = getattr(self, "_concept_gaps", None) or []
        if _gaps and self._pattern_manager and self._colimit_builder:
            _propuestos = getattr(self, "_gaps_propuestos", None)
            if _propuestos is None:
                _propuestos = self._gaps_propuestos = set()
            for gap in sorted(_gaps, key=lambda g: -g.n_cocones):
                clave = frozenset(gap.component_ids)
                if clave in _propuestos:
                    continue
                presentes = [s for s in gap.component_ids if graph.get_skill(s)]
                if len(presentes) < self._MIN_SKILLS_PATRON:
                    continue
                link_ids = [
                    m.id for m in graph.morphisms
                    if m.morphism_type != MorphismType.IDENTITY
                    and m.source_id in presentes and m.target_id in presentes
                ]
                pattern = self._pattern_manager.create_pattern(
                    presentes, link_ids, graph=graph
                )
                _propuestos.add(clave)
                logger.info(
                    f"CR_org: hueco conceptual {sorted(presentes)} "
                    f"({gap.n_cocones} co-conos, sin limite) -> ligadura"
                )
                return Option(bindings=[pattern.id])

        # 0.b Ligar coactivaciones frecuentes (procedimiento `merge`).
        #
        # Este es el trabajo propio de CR_org segun la Def. 4.1: su paisaje son
        # las estadisticas de uso. Si un grupo de skills resuelve consultas
        # juntos de forma repetida, ese grupo ES un patron con enlaces
        # colectivos, y ligarlo produce el skill compuesto que integra su
        # funcionalidad (Seccion 2.1). Antes CR_org solo ligaba patrones que
        # otro co-regulador hubiera creado, asi que nunca aportaba nada propio.
        coact = getattr(self, "_coactivaciones", None) or {}
        if coact and self._pattern_manager and self._colimit_builder:
            frecuentes = sorted(
                (g for g, n in coact.items() if n >= self._MIN_COACTIVACIONES),
                key=lambda g: -coact[g],
            )
            ya_ligados = getattr(self, "_grupos_ligados", None)
            if ya_ligados is None:
                ya_ligados = self._grupos_ligados = set()

            for grupo in frecuentes:
                # `create_pattern` acuña un id nuevo en cada llamada, asi que
                # `has_colimit(pattern.id)` siempre da False y el mismo grupo
                # se ligaria una y otra vez, haciendo crecer el grafo sin
                # limite con colimites duplicados. Se lleva registro del grupo,
                # no del patron.
                if grupo in ya_ligados:
                    continue
                presentes = [s for s in grupo if graph.get_skill(s)]
                if len(presentes) < self._MIN_SKILLS_PATRON:
                    continue

                # Cerrar el grupo con sus puentes a un salto. Dos skills que
                # se coactivan rara vez tienen arista directa: group-theory y
                # quotient-groups se conectan a traves de group-homomorphisms.
                # Sin el intermediario el patron queda inconexo y sin enlaces
                # distinguidos, y no habria nada que ligar.
                puentes = []
                for cand in graph.skill_ids:
                    if cand in presentes:
                        continue
                    vecinos = set(graph.neighbors(cand))
                    if len(vecinos & set(presentes)) >= 2:
                        puentes.append(cand)
                componentes = presentes + puentes[:2]

                link_ids = [
                    m.id for m in graph.morphisms
                    if m.morphism_type != MorphismType.IDENTITY
                    and m.source_id in componentes and m.target_id in componentes
                ]
                if not link_ids:
                    # Un patron sobre una categoria indice discreta es valido
                    # (Def. 2.1): los enlaces colectivos son la coactivacion
                    # misma. Se liga igual.
                    logger.debug(
                        f"CR_org: patron discreto sobre {sorted(presentes)}"
                    )
                presentes = componentes
                pattern = self._pattern_manager.create_pattern(
                    presentes, link_ids, graph=graph
                )
                if self._colimit_builder.has_colimit(pattern.id):
                    continue
                ya_ligados.add(grupo)
                logger.info(
                    f"CR_org: coactivacion x{coact[grupo]} de "
                    f"{sorted(presentes)} -> patron {pattern.id}"
                )
                return Option(bindings=[pattern.id])

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
        _stats = graph.stats
        _gaps = getattr(self, "_concept_gaps", None) or []

        return Landscape(
            co_regulator_type=self.cr_type,
            metrics={
                "max_level": max(level_counts.keys()) if level_counts else 0,
                "level_distribution": level_counts,
                "num_complex_links": float(num_complex),
                # cn es la magnitud que le toca vigilar a CR_str: mide si el
                # sistema esta CONSTRUYENDO conceptos propios, no cuantos se
                # le declararon. max_cn = 0 significa que no ha construido nada.
                "max_cn": float(_stats.get("max_cn", 0)),
                "num_joins": float(_stats.get("num_joins", 0)),
                "num_concept_gaps": float(len(_gaps)),
            }
        )

    def set_concept_gaps(self, gaps: list) -> None:
        """Recibir los huecos conceptuales detectados por el punto fijo."""
        self._concept_gaps = list(gaps or [])

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

        # El patron se construye DESDE los enlaces, no cortando skills sueltos.
        #
        # Antes se tomaban 5 skills arbitrarios del conjunto y luego se exigia
        # que ambos extremos de un enlace cayeran dentro de esos cinco. Con
        # 151 enlaces complejos repartidos por decenas de skills eso salia
        # vacio casi siempre, y cuando salia era por el orden azaroso del set:
        # la complejificacion dependia de un golpe de suerte.
        #
        # Ahora se toman los primeros enlaces complejos y se usan SUS extremos
        # como componentes: el sub-grafo resultante es conexo por construccion
        # y link_ids nunca queda vacio.
        enlaces_semilla = complex_links[:4]
        skill_list = []
        for m in enlaces_semilla:
            for sid in (m.source_id, m.target_id):
                if sid not in skill_list:
                    skill_list.append(sid)
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
        cr_int_frequency: int = 50,
        neural_agent=None,
    ):
        self.tactical = TacticalCoRegulator(
            frequency=1,
            memory=memory,
            pattern_manager=pattern_manager,
            colimit_builder=colimit_builder,
            neural_agent=neural_agent,
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

    def set_neural_agent(self, agent) -> None:
        """Propagar neural agent al CR_tac para clasificación GNN+PPO."""
        self.tactical._neural_agent = agent

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

    def set_concept_gaps(self, gaps: list) -> None:
        """
        Distribuir los huecos conceptuales a los CRs estructurales.

        Llamado por Nucleo tras build_hierarchy_to_fixpoint. CR_tac no los
        recibe: su efector es la interfaz LLM<->Lean, no el grafo.
        """
        self._concept_gaps = list(gaps or [])
        for cr in (self.organizational, self.strategic):
            if hasattr(cr, "set_concept_gaps"):
                cr.set_concept_gaps(self._concept_gaps)

    def record_activation(self, skill_ids: list[str]) -> None:
        """Informar a CR_org de que estos skills resolvieron juntos una consulta.

        Alimenta su paisaje de estadisticas de uso (Def. 4.1), que es de donde
        salen los patrones a ligar con `merge`.
        """
        org = getattr(self, "organizational", None)
        if org is not None and hasattr(org, "record_activation"):
            org.record_activation(skill_ids)

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
        # Fase 1: CR_tac clasifica el query (graph-aware)
        action_type = self.tactical.classify_query(query, graph=graph)

        # Fase 2: Recoger propuestas de todos los CRs activos
        proposals = self.step(graph)
        # Se conservan los resultados completos del ciclo. decide() solo
        # devuelve el tipo de accion del ganador, asi que las Option de los
        # co-reguladores estructurales se perdian aqui: calculaban su objetivo
        # en cada ciclo y nadie lo aplicaba nunca al grafo. El nucleo las lee
        # despues para ejecutar la complejificacion (paper v7.0, Seccion 6.1).
        self._last_cycle_results = proposals
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

        # CR_tac es autoritativo para la clasificacion del query.
        # Solo CR_int con REPAIR_FRACTURE puede sobreescribir (Axioma 9.5).
        # CRs estructurales (CR_str, CR_org) hacen mantenimiento en background
        # sobre el GRAFO —lo aplica _apply_structural_evolution— pero no
        # cambian el tipo de accion del query del usuario.
        #
        # `decidor` es el CR que realmente determino final_action. Antes se
        # reportaba `winner_cr` como source_cr Y su confianza, aunque su accion
        # se hubiera descartado: se veian decisiones con source_cr=STRATEGIC y
        # confidence=0.85 sobre una accion que la eligio CR_tac. La confianza
        # mostrada al usuario no correspondia a quien decidio.
        if (winner_cr == CoRegulatorType.INTEGRITY
                and winner_action == MESActionType.REPAIR_FRACTURE):
            final_action = ActionType.REORGANIZE
            decidor = CoRegulatorType.INTEGRITY
        else:
            final_action = action_type
            decidor = CoRegulatorType.TACTICAL

        # Confidence del CR que decidio la accion, no del ganador del arbitraje.
        confidence_map = {
            CoRegulatorType.INTEGRITY: 0.95,
            CoRegulatorType.STRATEGIC: 0.85,
            CoRegulatorType.ORGANIZATIONAL: 0.75,
            CoRegulatorType.TACTICAL: 0.8,
        }

        return GlobalDecision(
            action_type=final_action,
            source_cr=decidor,
            option=winner_option,
            confidence=confidence_map.get(decidor, 0.7),
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
