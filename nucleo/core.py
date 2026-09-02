"""
Nucleo Logico Evolutivo - Core
==============================

Orquestador principal del sistema Sigma_t = (L, CR_t, G_t, F)

Donde:
- L: Modelo de Lenguaje (Claude)
- CR_t: Red de Co-reguladores (Dinamica Global)
- G_t: Grafo Categorico de Skills
- F: Pilares Fundamentales

Este modulo coordina la interaccion entre todos los componentes.
La Dinamica Global reemplaza al agente RL monolitico con una
red de 4 co-reguladores autonomos (Seccion 8, paper v7.0).
"""

from __future__ import annotations

import asyncio
import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any, Callable
from datetime import datetime
from enum import Enum, auto

from nucleo.types import (
    Skill, Morphism, MorphismType, PillarType,
    State, Action, ActionType, Option,
    ExperienceRecord, CoRegulatorType,
)
from nucleo.config import NucleoConfig
from nucleo.graph.category import SkillCategory
from nucleo.graph.evolution import EvolutionarySystem
from nucleo.llm.client import LLMClient, LLMConfig
from nucleo.lean.client import LeanClient, LeanResult, LeanResultStatus
from nucleo.lean.tactics import TacticMapper
from nucleo.lean.solver_cascade import SolverCascade
from nucleo.lean.sorry_filler import SorryFiller, SorryContext
from nucleo.lean.sorry_analyzer import find_sorries_in_text
from nucleo.lean.parser import LeanParser, parse_error_structured
from nucleo.mes.patterns import PatternManager, ColimitBuilder
from nucleo.mes.memory import MESMemory
from nucleo.mes.co_regulators import CoRegulatorNetwork, GlobalDecision
from nucleo.pillars.math_domains import load_math_domains
from nucleo.eval.math_evaluator import MathEvaluator, EvaluationResult

logger = logging.getLogger(__name__)


class NucleoMode(Enum):
    """Modos de operacion del Nucleo."""
    INTERACTIVE = auto()   # Interaccion con usuario
    AUTONOMOUS = auto()    # Modo autonomo (entrenamiento)
    VERIFICATION = auto()  # Modo verificacion Lean


@dataclass
class NucleoState:
    """
    Estado interno del Nucleo.

    Corresponde a x = (c_L, g_Lean, G, h, m) del documento.
    """
    context: str = ""              # c_L: Contexto LLM
    lean_goal: Optional[str] = None  # g_Lean: Goal actual
    history: list[dict] = field(default_factory=list)  # h: Historial
    metadata: dict[str, Any] = field(default_factory=dict)  # m: Metadatos

    def to_state(self, graph: SkillCategory) -> State:
        """Convertir a State del MDP."""
        return State(
            llm_context=None,  # Se calcularia con embeddings
            lean_goal=self.lean_goal,
            graph_snapshot=graph.stats if graph else {},
            history=[],  # Simplificado por ahora
            metrics=self.metadata.copy()
        )


@dataclass
class NucleoResponse:
    """Respuesta del Nucleo a una interaccion."""
    content: str
    action_type: ActionType
    lean_result: Optional[LeanResult] = None
    suggested_skills: list[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)



# ── Referencias ancladas de Mathlib ─────────────────────────────────────
# Fuente de verdad que el LLM NO debe improvisar: nombres de lemas y modulos
# reales, comprobados con `lake env lean`. Se consultan tanto en la ruta de
# formalizacion como en la ruta educativa, para que ninguna respuesta cite
# Mathlib de memoria.
_MATHLIB_REFS: dict[tuple[str, ...], str] = {
    # Verificado con `lake env lean` (exit 0). Notas:
    #  - EuclideanSpace vive en PiL2, no en InnerProductSpace.Basic.
    #  - La notacion ⟪·,·⟫ exige `open scoped RealInnerProductSpace`.
    #  - norm_add_sq_real es la EXPANSION (deja el termino cruzado
    #    2*⟪a,b⟫); Pitagoras necesita ademas la hipotesis h.
    #  - norm_add_sq_eq_norm_sq_add_norm_sq_real se enuncia con
    #    producto (‖·‖*‖·‖), no con potencia: de ahi el `simpa [sq]`.
    ("pitagor", "pythag", "hipotenusa"): (
        "-- Teorema de Pitágoras en Lean 4 / Mathlib (versión norma)\n"
        "import Mathlib.Analysis.InnerProductSpace.PiL2\n"
        "open scoped RealInnerProductSpace\n\n"
        "example (a b : EuclideanSpace ℝ (Fin 2)) (h : ⟪a, b⟫ = 0) :\n"
        "    ‖a + b‖^2 = ‖a‖^2 + ‖b‖^2 := by\n"
        "  rw [norm_add_sq_real, h, mul_zero, add_zero]\n\n"
        "-- Vía el lema dedicado de Mathlib\n"
        "example (a b : EuclideanSpace ℝ (Fin 2)) (h : ⟪a, b⟫ = 0) :\n"
        "    ‖a + b‖^2 = ‖a‖^2 + ‖b‖^2 := by\n"
        "  simpa [sq] using norm_add_sq_eq_norm_sq_add_norm_sq_real h"
    ),
    ("yoneda",): (
        "import Mathlib.CategoryTheory.Yoneda\n"
        "-- yonedaEquiv : (yoneda.obj X ⟶ F) ≃ F.obj X\n"
        "#check CategoryTheory.yonedaEquiv"
    ),
    ("curry", "howard"): (
        "-- Propositions as types (Curry-Howard) en Lean 4\n"
        "example (P Q : Prop) (h : P → Q) (hp : P) : Q := h hp\n"
        "-- La implicación P → Q ES el tipo de funciones P → Q"
    ),
    ("irrac", "raiz cuadrada de 2", "sqrt 2"): (
        "import Mathlib.Data.Real.Irrational\n"
        "example : Irrational (Real.sqrt 2) := irrational_sqrt_two"
    ),
    # Teoría de categorías — definiciones clave
    ("cartesianamente cerrada", "ccc", "closed cartesian", "cartesian closed"): (
        "import Mathlib.CategoryTheory.Closed.Cartesian\n"
        "-- CartesianClosed: categoría con productos finitos y exponenciales\n"
        "#check CartesianClosed\n"
        "-- eval : B^A × A → B  (NO C^A — el exponencial es B^A)\n"
        "#check CategoryTheory.CartesianClosed.curry\n"
        "-- curry : Hom(C × A, B) ≅ Hom(C, B^A)"
    ),
    ("funtor", "functor"): (
        "import Mathlib.CategoryTheory.Functor.Basic\n"
        "#check CategoryTheory.Functor\n"
        "-- Functor C D : tipo de funtores entre categorías C y D\n"
        "#check CategoryTheory.Functor.map"
    ),
    ("colimite", "colimit", "colimits"): (
        "import Mathlib.CategoryTheory.Limits.HasLimits\n"
        "#check CategoryTheory.Limits.IsColimit\n"
        "-- IsColimit: propiedad universal del colímite"
    ),
    ("adjuncion", "adjoint", "adjunction"): (
        "import Mathlib.CategoryTheory.Adjunction.Basic\n"
        "#check CategoryTheory.Adjunction\n"
        "-- Adjunction F G : F ⊣ G  (F adjunto izquierdo de G)\n"
        "#check CategoryTheory.Adjunction.homEquiv"
    ),
    ("transformacion natural", "natural transformation"): (
        "import Mathlib.CategoryTheory.NatTrans\n"
        "#check CategoryTheory.NatTrans\n"
        "-- NatTrans F G : transformación natural entre funtores F y G"
    ),
    ("grupo", "group theory"): (
        "import Mathlib.Algebra.Group.Basic\n"
        "#check Group\n"
        "-- Group: tipo de grupos (mul, inv, one, axiomas)\n"
        "#check mul_comm  -- en grupos abelianos"
    ),
    ("anillo", "ring theory"): (
        "import Mathlib.Algebra.Ring.Basic\n"
        "#check Ring\n"
        "example (R : Type*) [Ring R] (a b : R) : a * b + b * a = b * a + a * b := by ring"
    ),
    ("espacio vectorial", "vector space", "modulo"): (
        "import Mathlib.Algebra.Module.Basic\n"
        "#check Module\n"
        "#check Submodule"
    ),
    ("topologia", "espacio topologico", "topological space"): (
        "import Mathlib.Topology.Basic\n"
        "#check TopologicalSpace\n"
        "#check IsOpen\n"
        "#check IsClosed"
    ),
}


def _mathlib_ref_for(texto_normalizado: str) -> str:
    """Devuelve el snippet Mathlib anclado para la consulta, o cadena vacia."""
    for claves, ref in _MATHLIB_REFS.items():
        if any(k in texto_normalizado for k in claves):
            return ref
    return ""

class Nucleo:
    """
    Nucleo Logico Evolutivo.

    Sistema adaptativo que coordina:
    - LLM (Claude) para procesamiento de lenguaje
    - Red de Co-reguladores (Dinamica Global) para decisiones
    - Grafo categorico de skills
    - Verificador Lean 4

    La Dinamica Global (Seccion 8, paper v7.0) reemplaza al agente RL
    con 4 co-reguladores autonomos que operan a diferentes escalas
    temporales y niveles jerarquicos.

    Example:
        nucleo = Nucleo()
        await nucleo.initialize()

        response = await nucleo.process(
            "Demuestra que todo grupo abeliano finito es producto de ciclicos"
        )
        print(response.content)
    """

    def __init__(self, config: Optional[NucleoConfig] = None):
        """
        Inicializar el Nucleo.

        Args:
            config: Configuracion del sistema
        """
        self.config = config or NucleoConfig()

        # Componentes
        self._graph: Optional[SkillCategory] = None
        self._llm: Optional[LLMClient] = None
        self._lean: Optional[LeanClient] = None

        # MES Components (v7.0) — Dinamica Global
        self._evolution: Optional[EvolutionarySystem] = None
        self._pattern_manager: Optional[PatternManager] = None
        self._colimit_builder: Optional[ColimitBuilder] = None
        self._memory: Optional[MESMemory] = None
        self._cr_network: Optional[CoRegulatorNetwork] = None

        # lean4-skills integration (v7.0 Phase 6)
        self._solver_cascade: Optional[SolverCascade] = None
        self._sorry_filler: Optional[SorryFiller] = None

        # Estado
        self._state = NucleoState()
        self._mode = NucleoMode.INTERACTIVE
        self._initialized = False
        self._last_decision: Optional[GlobalDecision] = None

        # Banco de ejemplos few-shot Lean (cargado desde lean_examples.json)
        self._lean_examples: dict = {}

        # Neural agent for live PPO learning (optional)
        self._neural_agent = None
        self._live_learning_steps = 0

        # Multi-agent orchestrator (14 specialized agents, one per category)
        self._multi_agent_orchestrator = None

        # Consultores Avanzados (optional module)
        self._consultores: Optional["ConsultoresModule"] = None

        # Huecos conceptuales: patrones con co-conos pero sin co-cono limite.
        # Los llena build_hierarchy_to_fixpoint en initialize().
        self._concept_gaps: list = []

        # La congruencia con la que se decide si un candidato es CO-CONO y no
        # solo cota superior. Fuera de la delgadez las dos cosas dejan de
        # coincidir, y sin ella el sistema volveria a contar como colimites los
        # que solo son alcanzables. La llena initialize().
        self._congruencia = None

        # Objetos con orden IRREDUCIBLE >= 2: los genuinamente emergentes.
        # Distinto de `max_cn`, que es una altura y puede estar inflada.
        self._emergentes: dict = {}

        # Feedback tracking — last experience for retroactive update
        self._last_experience_id: Optional[str] = None
        self._last_action_type = None

        # Math answer evaluator (MATH / GSM8K benchmarks)
        self._evaluator: MathEvaluator = MathEvaluator()

        # Cache perezosa del pilar formal de teoria de conjuntos, usada por
        # _formal_pillar_note para anclar el LLM a la formula exacta de ZFC.
        self._set_theory_pillar = None

        # Callbacks
        self._on_action: Optional[Callable] = None
        self._on_reward: Optional[Callable] = None

    async def initialize(self) -> None:
        """
        Inicializar todos los componentes.

        Carga:
        - Grafo de skills
        - Red de co-reguladores (Dinamica Global)
        - Cliente LLM
        - Cliente Lean
        - Memoria persistente (si existe)
        """
        if self._initialized:
            return

        logger.info("Inicializando Nucleo Logico Evolutivo...")

        # Grafo categorico
        self._graph = SkillCategory(name="NucleoSkillGraph")
        self._load_foundational_skills()

        # LLM Client — no sobreescribir si ya fue configurado via reconfigure_llm()
        if self._llm is None:
            llm_config = LLMConfig(
                model=self.config.llm.model,
                max_tokens=self.config.llm.max_tokens,
                temperature=self.config.llm.temperature,
                api_key=self.config.llm.api_key,
            )
            self._llm = LLMClient(llm_config)

        # Lean Client — project_path fijado al root del repo (donde está lakefile.toml)
        # independientemente de desde qué directorio se lanzó `streamlit run`.
        _lean_project = (
            Path(self.config.lean.project_path)
            if self.config.lean.project_path
            else Path(__file__).parent.parent  # nucleo/core.py → nucleo/ → repo root
        )
        self._lean = LeanClient(
            project_path=_lean_project,
            timeout_ms=self.config.lean.timeout_ms
        )


        # lean4-skills integration: Solver Cascade + Sorry Filler (graph-aware)
        self._solver_cascade = SolverCascade(self._lean, graph=self._graph)
        self._sorry_filler = SorryFiller(solver_cascade=self._solver_cascade)

        # Cargar banco de ejemplos Lean few-shot (miniF2F, seeded por seed_from_datasets.py)
        lean_ex_path = self.config.data_dir / "lean_examples.json"
        if lean_ex_path.exists():
            import json as _json
            with open(lean_ex_path, encoding="utf-8") as _f:
                self._lean_examples = _json.load(_f)
            n_ex = sum(len(v) for v in self._lean_examples.values())
            logger.info(f"lean_examples.json: {n_ex} ejemplos few-shot cargados")

        # MES Components (v7.0) — Dinamica Global
        self._pattern_manager = PatternManager()
        self._colimit_builder = ColimitBuilder(self._pattern_manager)
        self._memory = MESMemory(
            max_records=self.config.mes.max_records,
            consolidation_threshold=self.config.mes.consolidation_threshold,
            econcept_min_records=self.config.mes.econcept_min_records,
        )
        # Se comparten el gestor de patrones y el constructor de colimites con
        # los co-reguladores. Sin esto, el sistema evolutivo se creaba un
        # registro vacio propio y las ligaduras propuestas por los CRs no se
        # encontraban: la complejificacion se descartaba sin dejar rastro.
        self._evolution = EvolutionarySystem(
            self._graph,
            pattern_manager=self._pattern_manager,
            colimit_builder=self._colimit_builder,
        )
        self._cr_network = CoRegulatorNetwork(
            memory=self._memory,
            pattern_manager=self._pattern_manager,
            colimit_builder=self._colimit_builder,
            cr_org_frequency=self.config.mes.cr_org_frequency,
            cr_str_frequency=self.config.mes.cr_str_frequency,
            cr_int_frequency=self.config.mes.cr_int_period,
        )

        # Cargar memoria persistente si existe
        memory_path = self.config.data_dir / "memory.json"
        if memory_path.exists():
            self._memory.load(memory_path)

        # ── Jerarquia emergente: MEDIR el orden de complejidad ─────────────
        # ComplexityOrder.lean: cn(J) = 1 + max{cn(Pi)} para J = join[P].
        # Se escribe en skill.cn; skill.level (taxonomia curada) no se toca.
        #
        # Se DESCUBREN los co-conos limite que ya existen en el grafo; no se
        # fabrica ningun vertice. Por eso converge (punto fijo en la iteracion
        # 2) y no muta la estructura que analiza.
        #
        # Los patrones con co-conos pero SIN limite se devuelven como
        # ConceptGap: son los huecos conceptuales del grafo de conocimiento y
        # el disparador legitimo de complexificacion para el MES.
        #
        # Con 0 colimites el resultado correcto es cn = 0 para todos: nada ha
        # sido construido todavia, solo declarado. Ese 0 no es un fallo — es la
        # medicion de partida. max_cn y num_joins son el KPI de si el motor de
        # complejificacion esta produciendo algo.
        try:
            from nucleo.graph.complexity import (
                build_hierarchy_to_fixpoint, objetos_emergentes,
            )
            from nucleo.graph.no_delgado import congruencia_declarada

            # La congruencia se calcula UNA VEZ y se conserva: la
            # complexificacion le añade las relaciones constitutivas de los
            # objetos que inserta, y el siguiente punto fijo tiene que verlas.
            self._congruencia = congruencia_declarada(self._graph)

            _cn, self._concept_gaps = build_hierarchy_to_fixpoint(
                self._graph, self._pattern_manager, self._colimit_builder,
                cong=self._congruencia,
            )

            if self.config.complexificacion_automatica:
                self._complexificar_hasta_punto_fijo()

            # `max_cn` es una ALTURA (maximo sobre descomposiciones), no una
            # medida de emergencia: un objeto puede tener cn alto y ser
            # reducible a un colimite de objetos de base. Se publican las dos.
            emergentes = objetos_emergentes(self._graph, self._colimit_builder)
            self._emergentes = emergentes
            logger.info(
                f"Jerarquia emergente: max_cn={self._graph.stats['max_cn']}, "
                f"colimites={self._graph.stats['num_joins']}, "
                f"huecos conceptuales={len(self._concept_gaps)}, "
                f"skills={len(self._graph.skill_ids)}, "
                f"EMERGENTES (orden irreducible >= 2)={len(emergentes)}"
            )
        except Exception as e:
            logger.warning(
                f"build_hierarchy_to_fixpoint fallo (no bloqueante): {e}",
                exc_info=True,
            )
            self._concept_gaps = []
            if self._congruencia is None:
                from nucleo.graph.no_delgado import Congruencia
                self._congruencia = Congruencia()

        # Los huecos son el material de trabajo de CR_org y CR_str: cada uno
        # señala donde falta el concepto que unifica un patron.
        #
        # (ver `_complexificar_hasta_punto_fijo` para el paso que los cierra)
        #
        # Va en su propio try: cuando esto vivia dentro del bloque anterior,
        # un AttributeError aqui reseteaba self._concept_gaps a [] y los 26
        # huecos ya calculados desaparecian sin rastro visible.
        try:
            self._cr_network.set_concept_gaps(self._concept_gaps)
        except Exception as e:
            logger.warning(f"set_concept_gaps fallo: {e}", exc_info=True)

        # ── Neural agent con PPO (use_neural=True) ─────────────────────────
        from nucleo.rl.agent import NucleoAgent, AgentConfig
        from nucleo.rl.mdp import ExperienceBuffer

        neural_agent = NucleoAgent(
            self._graph,
            config=AgentConfig(),
            use_neural=True,
        )

        # Cargar pesos entrenados si existen
        weights_json = self.config.data_dir / "neural_agent.json"
        if weights_json.exists():
            try:
                neural_agent = NucleoAgent.load(str(weights_json), self._graph)
                logger.info("Pesos del neural agent cargados desde disco")
            except Exception as e:
                logger.warning(f"No se pudieron cargar pesos: {e}")

        # Cargar buffer de experiencias si existe
        buffer_path = self.config.data_dir / "experience_buffer.pkl"
        if buffer_path.exists():
            try:
                neural_agent.buffer = ExperienceBuffer.load(buffer_path)
                logger.info(
                    f"Buffer cargado: {len(neural_agent.buffer)} transiciones"
                )
            except Exception as e:
                logger.warning(f"No se pudo cargar buffer: {e}")

        # Conectar: live PPO + CR_tac usa GNN para clasificar queries
        self.set_neural_agent(neural_agent)
        self._cr_network.set_neural_agent(neural_agent)

        # ── Sistema multi-agente (14 especialistas por categoria) ──────────
        # Antes se construia pero nunca se activaba (set_multi_agent_orchestrator
        # no se llamaba desde ningun punto de la app). Los pesos por categoria
        # SI existen en disco (training/agents/best/*.pt), asi que activarlo
        # aporta sugerencias de tactica por memoria procedimental especifica
        # de cada area, ademas de la metadata de categoria ya expuesta en
        # las respuestas. No sobreescribe ningun checkpoint en disco.
        if self.config.enable_multi_agent:
            try:
                self.set_multi_agent_orchestrator()
            except Exception as e:
                logger.warning(f"MultiAgentOrchestrator no se pudo activar: {e}")

        self._initialized = True
        logger.info("Nucleo inicializado correctamente (PPO activo)")

    def _complexificar_hasta_punto_fijo(self, max_pasos: int = 5) -> list:
        """
        K -> K' -> K'' ... hasta que un paso no añada nada.

        Cada paso cierra los huecos que TIENEN cotas superiores insertando
        `eta(P)` como minimo entre ellas, y vuelve a calcular el punto fijo con
        la congruencia ampliada. Un hueco SIN cotas superiores no se puede
        cerrar asi —`eta(P)` seria el objeto maximo y colgaria de todo el
        grafo— y se deja abierto: el concepto que lo llena lo aporta la
        matematica, no la cirugia sobre el grafo.

        PRESERVACION. El objetivo (iii) de la opcion de Ehresmann exige no
        romper los colimites que ya existian. Se cumple por RETIRADA SELECTIVA:
        si un objeto insertado roba la minimalidad de un colimite previo, se
        retira ese objeto, no el paso entero. Antes era todo-o-nada y la
        complexificacion resultaba inerte —medido: 8 objetos cerraban 8 huecos
        y los 8 se tiraban por culpa de 1—.

        LO QUE NO HACE. No produce emergencia. `eta(P)` se inserta justo encima
        de las componentes de P, luego su orden irreducible es
        `1 + max(orden de las componentes)`; con componentes de orden 0 el
        resultado es orden 1, siempre. Para orden >= 2 hace falta cerrar un
        hueco cuyas componentes ya sean colimites, y los que hay de esos no
        tienen cotas superiores.

        Returns:
            La lista de `ResultadoComplexificacion`, un elemento por paso.
        """
        from nucleo.graph.complexity import build_hierarchy_to_fixpoint
        from nucleo.graph.complexificacion import complexificar

        pasos = []
        for i in range(max_pasos):
            res = complexificar(
                self._graph, self._pattern_manager, self._colimit_builder,
                self._concept_gaps, preservar=True, cong=self._congruencia,
            )
            pasos.append(res)
            logger.info(f"complexificacion paso {i + 1}: {res}")
            if not res.nuevos:
                break
            _cn, self._concept_gaps = build_hierarchy_to_fixpoint(
                self._graph, self._pattern_manager, self._colimit_builder,
                cong=self._congruencia,
            )
        return pasos

    def _load_foundational_skills(self) -> None:
        """Cargar skills fundamentales de los 4 pilares (nivel 0)."""
        # F_Set: Teoria de Conjuntos
        self._graph.add_skill(Skill(
            id="zfc-axioms", name="ZFC Axioms",
            description="Axiomas de Zermelo-Fraenkel con Eleccion",
            pillar=PillarType.SET, level=0,
        ))
        self._graph.add_skill(Skill(
            id="ordinals", name="Ordinals",
            description="Numeros ordinales y aritmetica ordinal",
            pillar=PillarType.SET, level=0,
        ))

        # F_Cat: Teoria de Categorias
        self._graph.add_skill(Skill(
            id="cat-basics", name="Category Basics",
            description="Objetos, morfismos, composicion",
            pillar=PillarType.CAT, level=0,
        ))
        self._graph.add_skill(Skill(
            id="functors", name="Functors",
            description="Funtores covariantes y contravariantes",
            pillar=PillarType.CAT, level=0,
        ))
        self._graph.add_skill(Skill(
            id="nat-trans", name="Natural Transformations",
            description="Transformaciones naturales entre funtores",
            pillar=PillarType.CAT, level=0,
        ))
        self._graph.add_skill(Skill(
            id="limits", name="Limits & Colimits",
            description="Limites y colimites categoricos",
            pillar=PillarType.CAT, level=0,
        ))

        # F_Log: Logica
        self._graph.add_skill(Skill(
            id="fol-deduction", name="FOL Deduction",
            description="Deduccion natural en logica de primer orden",
            pillar=PillarType.LOG, level=0,
        ))
        self._graph.add_skill(Skill(
            id="fol-metatheory", name="FOL Metatheory",
            description="Completitud, compacidad, Lowenheim-Skolem",
            pillar=PillarType.LOG, level=0,
        ))

        # F_Type: Teoria de Tipos
        self._graph.add_skill(Skill(
            id="cic", name="CIC",
            description="Calculo de Construcciones Inductivas",
            pillar=PillarType.TYPE, level=0,
        ))
        self._graph.add_skill(Skill(
            id="lean-kernel", name="Lean 4 Kernel",
            description="Kernel de verificacion de Lean 4",
            pillar=PillarType.TYPE, level=0,
        ))

        # Morfismos internos
        self._graph.add_morphism("zfc-axioms", "ordinals", MorphismType.DEPENDENCY)
        self._graph.add_morphism("cat-basics", "functors", MorphismType.DEPENDENCY)
        self._graph.add_morphism("functors", "nat-trans", MorphismType.DEPENDENCY)
        self._graph.add_morphism("functors", "limits", MorphismType.DEPENDENCY)
        self._graph.add_morphism("cic", "lean-kernel", MorphismType.DEPENDENCY)
        self._graph.add_morphism("fol-deduction", "fol-metatheory", MorphismType.DEPENDENCY)

        # Inter-pillar translations
        self._graph.add_morphism(
            "fol-deduction", "cic",
            MorphismType.TRANSLATION,
            metadata={"translation": "curry-howard"},
        )
        self._graph.add_morphism(
            "zfc-axioms", "cat-basics",
            MorphismType.ANALOGY,
            metadata={"analogy": "sets-as-categories"},
        )

        # Load mathematical domain skills (levels 1-2)
        result = load_math_domains(self._graph)
        logger.info(
            "Math domains loaded: %d added, %d skipped, %d translations",
            result["added"], result["skipped"], result["translations"],
        )

        # LA COBERTURA QUE FALTABA.
        #
        # Los 173 curados cubrian el 32,7 % de los teoremas de Mathlib, y el
        # hueco era sistematico: `Order` a cero, `Data` al 3,4 % — orden,
        # desigualdades y matematica elemental. Ante `(a+b)^2 = a^2+2ab+b^2` no
        # habia ningun nodo que recuperar, y ningun emparejador recupera lo que
        # no esta: tres estrategias distintas sacaron ~7 % en algebra mientras
        # acertaban 53-66 % en geometria, donde el nodo si existia.
        #
        # Estos 44 vienen leidos de la taxonomia de Mathlib y van marcados como
        # NO INTERPRETADOS: dicen donde vive algo, no que es categoricamente.
        from nucleo.pillars.math_domains import load_mathlib_coverage
        cobertura = load_mathlib_coverage(self._graph)
        logger.info(
            "Cobertura Mathlib: %d nodos, %d aristas",
            cobertura["added"], cobertura["links"],
        )

        # LA MULTIPLICIDAD QUE LEAN CERTIFICO.
        #
        # Sin esta llamada los seis morfismos demostrados distintos en Lean
        # —tres Ring -> Grp, tres Field -> Ring, cada uno con su teorema— vivian
        # solo en los tests, y el grafo del runtime era mas delgado que el que
        # se estaba midiendo. Medido antes de añadirla: 3 de 387 pares con
        # |Hom| > 1 en el runtime frente a 5 en la medicion. Es justo la
        # multiplicidad que costo demostrar, y no estaba llegando.
        from nucleo.graph.no_delgado import registrar_morfismos_certificados
        certificados = registrar_morfismos_certificados(self._graph)
        logger.info(
            "Morfismos certificados por Lean registrados: %d",
            len(certificados),
        )

    async def process(self, input_text: str) -> NucleoResponse:
        """
        Procesar entrada del usuario via Dinamica Global.

        Flujo (Seccion 8, paper v7.0):
        1. Actualizar contexto con input
        2. Red de CRs decide accion (protocolo de transicion global)
        3. Ejecutar accion (LLM, Lean, o reorganizacion)
        4. CRs evaluan resultado
        5. Registrar en memoria (enriquecimiento monotono)

        Args:
            input_text: Texto de entrada del usuario

        Returns:
            NucleoResponse con la respuesta
        """
        if not self._initialized:
            await self.initialize()

        # Actualizar contexto
        self._state.context = input_text
        self._state.history.append({
            "role": "user",
            "content": input_text,
            "timestamp": datetime.now().isoformat()
        })

        # Dinamica Global: CRs deciden accion
        decision = self._cr_network.decide(input_text, self._graph)
        self._last_decision = decision

        if self._on_action:
            self._on_action(decision)

        # Ejecutar accion segun decision de los CRs
        action = Action(action_type=decision.action_type)
        response = await self._execute_action(action, input_text)
        # Preservar confianza calculada por Lean; usar la de los CRs solo como fallback
        if response.confidence == 0.0:
            response.confidence = decision.confidence
        response.metadata["source_cr"] = decision.source_cr.name
        response.metadata["cr_proposals"] = decision.cr_proposals

        # Actualizar historial
        self._state.history.append({
            "role": "assistant",
            "content": response.content,
            "action": decision.action_type.name,
            "source_cr": decision.source_cr.name,
            "timestamp": datetime.now().isoformat()
        })

        # Evaluar resultado y registrar en memoria
        success = self._evaluate_result(decision, response)

        if self._on_reward:
            self._on_reward(success)

        # CRs evaluan post-ejecucion
        self._cr_network.record_result(decision, success, self._graph)

        # Registrar en memoria MES
        self._record_experience(input_text, decision, success)

        # Complejificacion del grafo. Va DESPUES de producir la respuesta para
        # que la consulta actual se resuelva sobre un grafo estable; los
        # cambios benefician a las siguientes.
        self._apply_structural_evolution()

        # Llenado de un hueco conceptual por interaccion. Cierra el ciclo MES:
        # CR_org/CR_str detectan donde falta el concepto que unifica un patron,
        # y aqui se intenta conseguirlo (LLM propone, Lean verifica). Hasta
        # ahora llenar_hueco_conceptual existia pero no lo llamaba nadie.
        await self._intentar_llenar_hueco()

        return response

    async def _execute_action(
        self,
        action: Action,
        input_text: str
    ) -> NucleoResponse:
        """Ejecutar la accion seleccionada."""

        if action.action_type == ActionType.RESPONSE:
            # Consulta matematica → Lean primero, LLM solo traduce
            if self._is_mathematical(input_text):
                # Enrutar al agente especializado si está disponible
                if self._multi_agent_orchestrator is not None:
                    category, _agent = self.get_specialized_agent(input_text)
                    if category:
                        logger.debug(f"Agente especializado: {category}")
                        # Registrar categoría en metadata para el response
                        self._state.metadata["math_category"] = category
                return await self._math_via_lean(input_text)

            # Conversacion pura → LLM directamente
            if self._llm is not None and self._llm.is_demo:
                # Incluso en conversacion, intentar dar contenido educativo
                return self._demo_educational_response(input_text)
            context = self._find_relevant_context(input_text, self._graph)
            context["mode"] = self._mode.name
            llm_response = await self._llm.generate(
                input_text,
                context=context,
            )
            return NucleoResponse(
                content=llm_response.content,
                action_type=ActionType.RESPONSE,
                confidence=0.8
            )

        elif action.action_type == ActionType.ASSIST:
            # CR_tac decidio ASSIST (usuario adjunto codigo Lean)
            return await self._assist_lean(input_text)

        elif action.action_type == ActionType.REORGANIZE:
            # Reorganizar grafo (accion interna)
            self._reorganize_graph()
            return NucleoResponse(
                content="[Grafo reorganizado internamente]",
                action_type=ActionType.REORGANIZE,
                confidence=0.5
            )

        # Default
        return NucleoResponse(
            content="Accion no reconocida",
            action_type=action.action_type,
            confidence=0.0
        )

    async def _assist_lean(self, input_text: str) -> NucleoResponse:
        """
        Asistir con prueba Lean.

        Estructura de la respuesta (en ambos casos):
          1. Explicación matemática didáctica (LLM, lenguaje natural)
          2. Código Lean 4 en bloque separado y limpio
          3. Estado de verificación
        """
        # Demo mode: skip Lean pipeline
        if self._llm is not None and self._llm.is_demo:
            return self._demo_educational_response(input_text)

        from nucleo.llm.client import LLMClient
        lean_system = LLMClient.LEAN_SYSTEM_PROMPT

        context = self._find_relevant_context(input_text, self._graph)
        context["task"] = "lean_formalization"

        # ── Caso A: usuario pide formalizacion sin adjuntar codigo ───────────
        # El pipeline Lean-primero aplica siempre: Lean verifica, LLM traduce.
        if "```lean" not in input_text:
            # Defensa en profundidad: la rama RESPONSE filtra por
            # _is_mathematical, pero ASSIST no lo hacia. Si el clasificador se
            # equivoca (o la red devuelve ASSIST para todo), un saludo acababa
            # formalizandose en Lean 4: una llamada al LLM y una ejecucion de
            # Lean tiradas para devolver un sinsentido.
            if not self._is_mathematical(input_text):
                context = self._find_relevant_context(input_text, self._graph)
                context["mode"] = self._mode.name
                llm_response = await self._llm.generate(input_text, context=context)
                return NucleoResponse(
                    content=llm_response.content,
                    action_type=ActionType.RESPONSE,
                    confidence=0.8,
                )
            return await self._math_via_lean(input_text)

        # ── Caso B: usuario envió código Lean → verificar, luego explicar ───
        code = self._extract_lean_code(input_text)

        result = await self._lean.check_code(code)

        if result.is_success:
            verification_line = "✓ **Verificado** — Lean 4 aceptó la prueba sin errores."
            confidence    = 0.95
            success_value = 1.0
            error_section = ""
        elif result.status == LeanResultStatus.SORRY:
            sorry_content, confidence, success_value = await self._try_solve_sorries(
                code, result
            )
            verification_line = f"⚠ **Sorry detectado** — {sorry_content}"
            error_section = ""
        else:
            error_info = self._analyze_lean_errors(result)
            first_err   = result.get_first_error() or "desconocido"
            mapper = TacticMapper()
            suggestions = (
                mapper.suggest_tactics(self._state.lean_goal)
                if self._state.lean_goal else []
            )
            verification_line = f"✗ **Error** (`{error_info.get('type', 'unknown')}`): {first_err}"
            error_section = (
                f"\n\n**Tácticas sugeridas:** {', '.join(f'`{t}`' for t in suggestions[:4])}"
                if suggestions else ""
            )
            confidence    = 0.5
            success_value = -0.5

        # El LLM genera SOLO la explicación didáctica (sin repetir el código)
        explain_prompt = (
            "Aquí hay una prueba en Lean 4. Tu tarea es explicarla en lenguaje natural.\n\n"
            f"```lean\n{code}\n```\n\n"
            f"Estado de la verificación: {verification_line}\n\n"
            "Estructura tu respuesta EXACTAMENTE así:\n\n"
            "## ¿Qué demuestra esta prueba?\n"
            "[Explica el enunciado matemático con tus palabras. Sin código.]\n\n"
            "## Idea central\n"
            "[La estrategia o intuición matemática que hace funcionar la prueba.]\n\n"
            "## Paso a paso\n"
            "[Explica cada táctica o bloque de código: qué hace y por qué se usa ahí. "
            "Puedes mencionar los nombres de las tácticas pero explica su significado.]\n\n"
            + (
                "## Cómo corregir los errores\n"
                "[Explica la causa del error y cómo solucionarlo.]\n"
                if success_value < 0 else
                "## Por qué es matemáticamente válida\n"
                "[Señala qué hace que la prueba sea correcta y completa.]\n"
            )
        )
        llm_response = await self._llm.generate(explain_prompt, system=lean_system, context=context)

        # Ensamblar: explicación LLM → código limpio → estado de verificación
        content = (
            f"{llm_response.content}\n\n"
            f"---\n\n"
            f"## Código Lean 4\n\n"
            f"```lean\n{code}\n```\n\n"
            f"{verification_line}{error_section}"
        )

        self._record_lean_experience("lean-tactics", success_value)

        return NucleoResponse(
            content=content,
            action_type=ActionType.ASSIST,
            lean_result=result,
            confidence=confidence,
        )

    # =========================================================================
    # LEAN-FIRST PIPELINE (v7.0 — arquitectura central)
    # =========================================================================

    _MATH_KEYWORDS = frozenset({
        # Español
        "teorema", "lema", "proposicion", "corolario", "demostracion",
        "prueba", "demostrar", "demuestra", "probar", "verifica", "verificar",
        "calcular", "hallar", "encontrar", "enuncia", "enunciar",
        "derivada", "integral", "limite", "serie", "sucesion",
        "convergencia", "divergencia", "continua", "diferenciable", "analitica",
        "grupo", "anillo", "campo", "espacio", "subespacio", "base", "dimension",
        "vector", "matriz", "determinante", "eigenvalor", "autovalor",
        "polinomio", "funcion", "biyeccion", "inyectiva", "sobreyectiva",
        "isomorfismo", "homomorfismo", "endomorfismo", "automorfismo",
        "conjunto", "subconjunto", "interseccion", "union", "complemento",
        "cardinalidad", "infinito", "infinitos", "axioma", "hipotesis", "conclusion",
        "logica", "cuantificador", "implicacion", "equivalencia", "negacion",
        "topologia", "metrica", "norma", "producto", "suma", "algebra",
        "geometria", "numero", "numeros", "primo", "primos", "divisible", "modulo", "congruencia",
        "categoria", "funtor", "transformacion", "natural", "adjunto",
        # Términos matemáticos comunes (con y sin acento)
        "irracional", "racional", "real", "complejo", "raiz", "raices",
        "pitagoras", "pitágoras", "yoneda", "curry", "howard", "fermat",
        "euler", "gauss", "riemann", "cantor", "galois", "noether",
        "demostracion", "induccion", "contradiccion", "absurdo",
        "inyectivo", "sobreyectivo", "biyectivo", "isomorfo",
        "triangulo", "angulo", "hipotenusa", "cateto", "rectangulo",
        # English
        "theorem", "lemma", "proposition", "corollary", "proof",
        "prove", "show", "verify", "compute", "find", "calculate",
        "derivative", "integral", "limit", "series", "sequence",
        "convergence", "continuous", "differentiable", "analytic",
        "group", "ring", "field", "space", "subspace", "basis", "dimension",
        "vector", "matrix", "determinant", "eigenvalue",
        "polynomial", "function", "bijection", "injection", "surjection",
        "isomorphism", "homomorphism", "endomorphism", "automorphism",
        "set", "subset", "intersection", "union", "complement", "cardinality",
        "axiom", "hypothesis", "logic", "quantifier", "implication",
        "topology", "metric", "norm", "algebra", "geometry",
        "prime", "divisible", "modulo", "congruence",
        "category", "functor", "adjoint",
        # Lean / formal
        "lean", "simp", "ring", "omega", "induction", "cases",
        "have", "intro", "apply", "exact", "rfl", "sorry",
    })

    _MATH_SYMBOLS = frozenset("∀∃∈∉⊆⊇⊂⊃∪∩∅∑∏∫∂∇∞αβγδεζηθλμνξρστφχψω")

    _MATH_LATEX = (
        r"\frac", r"\sum", r"\int", r"\forall", r"\exists",
        r"\in", r"\subset", r"\mathbb", r"\sqrt", r"\prod",
        r"\lim", r"\infty", r"\partial",
    )

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Quita acentos y pasa a minúsculas (para matching robusto)."""
        import unicodedata
        return "".join(
            c for c in unicodedata.normalize("NFD", text.lower())
            if unicodedata.category(c) != "Mn"
        )

    #: Formas ARITMÉTICAS Y ALGEBRAICAS que hacen matemática a una consulta.
    #:
    #: Cada patrón exige un operador ENTRE operandos. Un dígito suelto no basta
    #: —«tengo 2 gatos», «quedamos a las 3»— y por eso ninguna se dispara con
    #: un número aislado. Se evalúan sobre el texto normalizado (sin acentos).
    _MATH_FORMAS = (
        # 2 + 2 · 15*4 · 3.5 / 7 · 2^10
        r"\d\s*[+\-*/^]\s*\d",
        # x^2 · n^k — potencia; el acento circunflejo casi no aparece en prosa
        r"[a-z0-9]\s*\^\s*[a-z0-9]",
        # x = 5 · 2x + 1 = 0 · f(x)=... — ecuación con incógnita o número
        r"[a-z0-9)]\s*=\s*[-+]?\s*[a-z0-9(]",
        # desigualdades entre operandos
        r"[a-z0-9)]\s*(<=|>=|<|>)\s*[-+]?\s*[a-z0-9(]",
        # operadores escritos: 15 por 4 · 7 mas 3 · 20 entre 5 · 9 menos 2
        r"\d\s+(por|mas|menos|entre|dividido|multiplicado|elevado)\s+\d",
        # raiz/factorial/porcentaje aplicados a algo
        r"raiz\s+(cuadrada|cubica|de)",
        r"\d\s*!\B",
        r"\d\s*%",
        # notación de conjuntos o funciones con argumento
        r"[a-z]\s*\(\s*[a-z0-9]",
    )

    def _is_mathematical(self, text: str) -> bool:
        """
        Clasificar si una consulta es matematica.

        Criterios (cualquiera es suficiente):
        - Contiene vocabulario matematico formal (keywords)
        - Contiene simbolos matematicos Unicode
        - Contiene comandos LaTeX matematicos

        Excluye frases puramente conversacionales como saludo/despedida.
        """
        low = text.lower()
        # Versión sin acentos para matching más robusto
        normalized = self._normalize_text(text)

        # Frases puramente conversacionales → no matematico
        conversational_starters = (
            "hola", "buenos", "buenas", "gracias", "adios", "hasta",
            "como estas", "como te llamas", "que eres", "quien eres",
            "hi ", "hello", "thanks", "bye",
        )
        if any(normalized.strip().startswith(s) for s in conversational_starters):
            return False

        # Simbolos matematicos Unicode
        if any(ch in text for ch in self._MATH_SYMBOLS):
            return True

        # LaTeX matematico
        if any(cmd in text for cmd in self._MATH_LATEX):
            return True

        # Keywords: match sobre tokens (versión original y sin acentos)
        punct = "¿?.,;:!()[]{}\"'"
        tokens_raw = set(w.strip(punct) for w in low.split())
        tokens_norm = set(w.strip(punct) for w in normalized.split())
        if (tokens_raw | tokens_norm) & self._MATH_KEYWORDS:
            return True

        # Substring match para nombres propios y términos compuestos
        if any(kw in normalized for kw in (
            "pitagor", "pythag", "yoneda", "fermat", "euler", "gauss",
            "riemann", "cantor", "noether", "galois", "curry-howard",
            "irracional", "irracionalidad",
        )):
            return True

        # ARITMÉTICA Y ECUACIONES, que no tenían ninguna regla.
        #
        # El clasificador solo miraba VOCABULARIO —keywords, símbolos Unicode,
        # LaTeX— así que «¿cuánto es 2 + 2?» salía NO matemático y se iba a la
        # rama conversacional, saltándose Lean por completo. Es justo el caso
        # para el que existe el pipeline: `_lean_reward` del entrenamiento
        # trata explícitamente la forma `a OP b = N`.
        #
        # Se exige un OPERADOR ENTRE OPERANDOS, no solo la presencia de un
        # dígito: «tengo 2 gatos» no es una consulta matemática y no debe
        # entrar. Por eso ninguna de estas reglas se dispara con un número
        # suelto.
        if any(re.search(p, normalized) for p in self._MATH_FORMAS):
            return True

        return False

    def _demo_educational_response(self, input_text: str) -> "NucleoResponse":
        """
        Respuesta educativa para modo demo (sin API key).

        Clasifica la consulta usando el grafo de skills del NLE y construye
        una respuesta matemática estructurada que incluye:
        - Explicación del concepto/teorema
        - Plantilla Lean 4 con sorry
        - Nota sobre las capacidades completas del sistema
        """
        import unicodedata
        def _norm(s: str) -> str:
            """Quita acentos y pasa a minúsculas para matching robusto."""
            return "".join(
                c for c in unicodedata.normalize("NFD", s.lower())
                if unicodedata.category(c) != "Mn"
            )

        q = _norm(input_text)

        # ── Clasificar dominio y elegir contenido ─────────────────────────────
        # Diccionario: (keywords sin acento) → (título, explicación, lean_template)
        _KNOWN = {
            ("pitagor", "pythag", "hipotenusa", "cateto"): (
                "Teorema de Pitágoras",
                (
                    "El **Teorema de Pitágoras** establece que en todo triángulo rectángulo, "
                    "el cuadrado de la longitud de la hipotenusa $c$ es igual a la suma de los "
                    "cuadrados de los dos catetos $a$ y $b$:\n\n"
                    "$$a^2 + b^2 = c^2$$\n\n"
                    "**Prueba clásica (por álgebra de áreas):** Considera un cuadrado de lado "
                    "$(a+b)$. Su área es $(a+b)^2 = a^2 + 2ab + b^2$. Coloca cuatro triángulos "
                    "rectángulos iguales en sus esquinas: cada uno tiene área $\\frac{1}{2}ab$. "
                    "El cuadrado interior tiene lado $c$, así que $c^2 = (a+b)^2 - 4\\cdot\\frac{ab}{2} "
                    "= a^2 + b^2$. $\\blacksquare$\n\n"
                    "**En Mathlib (Lean 4):** El teorema está disponible como "
                    "`EuclideanGeometry.dist_sq_eq_dist_sq_add_dist_sq_of_angle_eq_pi_div_two` "
                    "o, para vectores, vía el producto interno."
                ),
                (
                    "import Mathlib.Geometry.Euclidean.Basic\n"
                    "import Mathlib.Analysis.InnerProductSpace.Basic\n\n"
                    "-- Pitágoras para vectores ortogonales en ℝ²\n"
                    "example (a b : ℝ) : (a, b).1 ^ 2 + (a, b).2 ^ 2 =\n"
                    "    ‖(a, b)‖ ^ 2 := by\n"
                    "  simp [Prod.norm_sq, sq_abs]\n\n"
                    "-- Para triángulos rectángulos reales:\n"
                    "-- ver Mathlib.Geometry.Euclidean.Angle.Sphere"
                ),
            ),
            ("yoneda",): (
                "Lema de Yoneda",
                (
                    "El **Lema de Yoneda** es uno de los resultados centrales de la Teoría de "
                    "Categorías. Dado un funtor $F : \\mathcal{C} \\to \\mathbf{Set}$ y un objeto "
                    "$A \\in \\mathcal{C}$, existe una biyección natural:\n\n"
                    "$$\\mathrm{Nat}(\\mathcal{C}(A, -),\\, F) \\cong F(A)$$\n\n"
                    "**Significado:** Un objeto queda completamente determinado por los morfismos "
                    "que salen de él. Dos objetos con los mismos funtores representables son "
                    "isomorfos (full faithfulness de la inmersión de Yoneda).\n\n"
                    "**Corolario clave:** La inmersión de Yoneda "
                    "$\\mathbf{y}: \\mathcal{C} \\hookrightarrow [\\mathcal{C}^{op}, \\mathbf{Set}]$ "
                    "es plena y fiel."
                ),
                (
                    "import Mathlib.CategoryTheory.Yoneda\n\n"
                    "open CategoryTheory\n\n"
                    "-- El lema de Yoneda está en Mathlib:\n"
                    "-- yonedaEquiv : (yoneda.obj X ⟶ F) ≃ F.obj X\n\n"
                    "example {C : Type*} [Category C] (X : C)\n"
                    "    (F : Cᵒᵖ ⥤ Type*) :\n"
                    "    (yoneda.obj X ⟶ F) ≃ F.obj (Opposite.op X) :=\n"
                    "  yonedaEquiv"
                ),
            ),
            ("curry", "howard", "curry-howard"): (
                "Correspondencia Curry-Howard",
                (
                    "La **Correspondencia Curry-Howard** (o isomorfismo proposiciones-tipos) "
                    "establece una equivalencia profunda entre:\n\n"
                    "| Lógica | Tipos |\n"
                    "|---|---|\n"
                    "| Proposición $P$ | Tipo $\\alpha$ |\n"
                    "| Prueba de $P$ | Término $t : \\alpha$ |\n"
                    "| $P \\Rightarrow Q$ | Función $\\alpha \\to \\beta$ |\n"
                    "| $P \\wedge Q$ | Par $(\\alpha \\times \\beta)$ |\n"
                    "| $P \\vee Q$ | Suma $\\alpha \\oplus \\beta$ |\n"
                    "| $\\bot$ (falso) | Tipo vacío `Empty` |\n\n"
                    "En Lean 4 (y Coq), las proposiciones **son** tipos. Una prueba de "
                    "`P → Q` es literalmente una función que convierte pruebas de `P` en pruebas de `Q`."
                ),
                (
                    "-- En Lean 4, proposiciones son tipos (Sort 0 = Prop)\n"
                    "-- Una prueba es un término del tipo correspondiente\n\n"
                    "-- Implicación = función\n"
                    "example (P Q : Prop) (h : P → Q) (hp : P) : Q := h hp\n\n"
                    "-- Conjunción = par\n"
                    "example (P Q : Prop) (hp : P) (hq : Q) : P ∧ Q := ⟨hp, hq⟩\n\n"
                    "-- Disyunción = suma\n"
                    "example (P Q : Prop) (hp : P) : P ∨ Q := Or.inl hp"
                ),
            ),
            ("irrac", "sqrt", "raiz", "irracional", "sqrt(2)", "raiz cuadrada"): (
                "Irracionalidad de √2",
                (
                    "**Teorema:** $\\sqrt{2}$ es irracional.\n\n"
                    "**Prueba (por contradicción):** Supón que $\\sqrt{2} = p/q$ con $p, q \\in \\mathbb{Z}$, "
                    "$\\gcd(p, q) = 1$. Entonces $2 = p^2/q^2$, por lo que $p^2 = 2q^2$. "
                    "Luego $p^2$ es par, entonces $p$ es par: $p = 2k$. Sustituyendo: "
                    "$4k^2 = 2q^2$, o sea $q^2 = 2k^2$, así $q$ es par. "
                    "Pero entonces $\\gcd(p,q) \\geq 2$, contradicción. $\\blacksquare$"
                ),
                (
                    "import Mathlib.Data.Real.Irrational\n\n"
                    "-- Disponible directamente en Mathlib:\n"
                    "example : Irrational (Real.sqrt 2) :=\n"
                    "  irrational_sqrt_two\n\n"
                    "-- Versión manual con norm_num:\n"
                    "example : ¬ ∃ (p q : ℤ), q ≠ 0 ∧ Real.sqrt 2 = p / q := by\n"
                    "  sorry  -- demostración completa requiere API key"
                ),
            ),
        }

        title, explanation, lean_template = (
            "Consulta matemática",
            "",
            "-- Formalización pendiente: conecta una API key para generar código Lean 4 real.",
        )

        for keywords, content in _KNOWN.items():
            if any(k in q for k in keywords):
                title, explanation, lean_template = content
                break

        if not explanation:
            # Sin plantilla conocida: describir lo que el grafo sí sabe de la consulta.
            ctx = self._find_relevant_context(input_text, self._graph)
            # Las claves son las que devuelve _find_relevant_context, no "skills".
            skills_found = ctx.get("relevant_skills", [])
            pilar = ctx.get("pillar") or "—"
            competencia = ctx.get("competencia_emergente")

            if not self._is_mathematical(input_text):
                title = "Modo demo"
                explanation = (
                    "Esta consulta no es matemática, así que el NLE no la envía a Lean. "
                    "Sin API key no hay conversación disponible: **conecta una clave** "
                    "(Anthropic, Google o Groq) en el panel lateral."
                )
                lean_template = "-- Sin formalización: la consulta no es matemática."
            else:
                lineas = [
                    f"El NLE clasificó la consulta en el pilar **{pilar}**.",
                    "",
                ]
                if skills_found:
                    lineas.append(
                        "Skills activados: "
                        + ", ".join(f"`{s}`" for s in skills_found[:4])
                    )
                else:
                    lineas.append(
                        "No se activó ningún skill concreto del grafo para esta consulta."
                    )
                if competencia:
                    lineas.append(f"Competencia emergente reconocida: **{competencia}**.")
                lineas += [
                    "",
                    "Para obtener enunciado preciso, demostración paso a paso y "
                    "código Lean 4 verificado con Mathlib, **conecta una API key** "
                    "en el panel lateral.",
                ]
                explanation = "\n".join(lineas)

        content = (
            f"## {title}\n\n"
            f"{explanation}\n\n"
            f"---\n\n"
            f"**Lean 4 — plantilla (modo demo)**\n\n"
            f"```lean\n{lean_template}\n```\n\n"
            f"> 🔑 **Modo demo activo.** Conecta una API key en el panel lateral "
            f"para obtener: formalización Lean 4 completa generada por el LLM, "
            f"verificación automática con Mathlib, y explicación detallada paso a paso."
        )
        return NucleoResponse(
            content=content,
            action_type=ActionType.ASSIST,
            confidence=0.7,
            metadata={"mode": "demo_educational"},
        )

    async def _math_educational_explanation(
        self, input_text: str, context: dict
    ) -> "NucleoResponse":
        """
        Respuesta educativa directa para queries históricas/geométricas/intuitivas.

        Usa el LLM para dar una respuesta en lenguaje natural rico (demostración
        geométrica, enunciado histórico, intuición), con Lean 4 como apéndice opcional.
        No fuerza la formalización Lean como paso principal.
        """
        from nucleo.llm.client import LLMClient
        edu_system = (
            "Eres un matemático y divulgador experto, con profundo conocimiento de "
            "la historia de las matemáticas y la demostración geométrica. "
            "Respondes en lenguaje natural claro y didáctico. "
            "Cuando explicas una demostración, la haces visual, paso a paso, con "
            "figuras descritas con palabras. No generes código Lean 4 a menos que "
            "el usuario lo pida explícitamente."
        )
        # Esta ruta NO ejecuta Lean (una prueba por reordenamiento de areas no
        # es formalizable directamente). Por eso el paso 4 es el punto debil:
        # si se le pide al LLM que hable de Mathlib sin material, improvisa
        # nombres de lemas. Se le ancla con la referencia verificada, y si no
        # hay ninguna se le prohibe nombrar lemas concretos.
        ref = _mathlib_ref_for(self._normalize_text(input_text))
        if ref:
            paso4 = (
                "4. **Nota Lean 4** (breve) — usa EXCLUSIVAMENTE la referencia "
                "verificada de abajo. No cites ningún otro nombre de lema ni de "
                "módulo, y no alteres los que aparecen ahí.\n\n"
                f"Referencia de Mathlib verificada con `lake env lean`:\n"
                f"```lean\n{ref}\n```\n"
            )
        else:
            paso4 = (
                "4. **Nota Lean 4** (breve) — describe en prosa CÓMO se abordaría "
                "la formalización. No inventes nombres de lemas, teoremas ni "
                "módulos de Mathlib: si no estás seguro de un nombre exacto, di "
                "que habría que localizarlo en Mathlib en vez de escribirlo.\n"
            )

        edu_prompt = (
            f"Responde a la siguiente pregunta matemática de forma educativa y completa:\n\n"
            f"{input_text}\n\n"
            "Estructura tu respuesta con:\n"
            "1. **Enunciado** — cómo se formula el resultado (con notación matemática $...$)\n"
            "2. **Contexto histórico** — si aplica, quién lo descubrió y cuándo\n"
            "3. **Demostración / Explicación** — paso a paso, geométrica/visual si se pide, "
            "con intuición clara\n"
            f"{paso4}\n"
            "Responde en el mismo idioma que el usuario."
        )
        resp = await self._llm.generate(edu_prompt, system=edu_system, context=context)
        return NucleoResponse(
            content=resp.content,
            action_type=ActionType.ASSIST,
            confidence=0.88,
            # sin_verificacion_lean: la UI debe poder avisar de que esta ruta
            # no paso por el verificador.
            metadata={"mode": "educational_explanation", "sin_verificacion_lean": True},
        )

    async def _review_document_for_errors(
        self, input_text: str, context: dict
    ) -> "NucleoResponse":
        """
        Revision critica de un documento/paper completo (no un objetivo unico).

        A diferencia de _math_via_lean (que formaliza UN enunciado puntual),
        aqui el LLM recorre TODO el texto adjunto — teoremas, corolarios,
        lemas, proposiciones — y lista errores concretos de cada uno, citando
        cual es el resultado afectado. No inventa ni sustituye un teorema
        distinto al pedido por el usuario.
        """
        from nucleo.llm.client import LLMClient

        if self._llm is not None and self._llm.is_demo:
            return self._demo_educational_response(input_text)

        review_system = (
            "Eres un revisor matematico riguroso (estilo referee de revista). "
            "Tu unica tarea es encontrar errores REALES en el documento que el "
            "usuario adjunta: errores logicos, definiciones mal planteadas, "
            "pasos de demostracion que no se siguen, hipotesis faltantes, "
            "notacion inconsistente, o enunciados formalmente vacios/triviales. "
            "Debes recorrer TODOS los teoremas, corolarios, lemas y "
            "proposiciones presentes en el texto adjunto, uno por uno — no "
            "selecciones solo uno ni inventes un enunciado distinto al que "
            "esta en el documento. Si un resultado esta correcto, dilo "
            "brevemente y sigue con el siguiente; no fuerces una critica "
            "donde no la hay. Cuando un error involucre codigo Lean 4, puedes "
            "citar el fragmento exacto, pero NO conviertas la respuesta en un "
            "intento de formalizar/probar el teorema desde cero."
        )
        review_prompt = (
            f"{input_text}\n\n"
            "Estructura tu respuesta como una lista, un item por cada "
            "teorema/corolario/lema/proposicion identificado en el documento:\n\n"
            "### [Nombre o numero del resultado]\n"
            "- **Enunciado**: (cita breve)\n"
            "- **Veredicto**: ✅ Correcto / ⚠️ Parcialmente correcto / ❌ Incorrecto\n"
            "- **Error encontrado**: (explicacion precisa y especifica; si no hay "
            "error, escribe 'Ninguno')\n\n"
            "Al final agrega un resumen general de cuantos resultados tienen "
            "errores y cuales son los mas graves."
        )
        resp = await self._llm.generate(review_prompt, system=review_system, context=context)
        return NucleoResponse(
            content=resp.content,
            action_type=ActionType.ASSIST,
            confidence=0.85,
            metadata={"mode": "document_review"},
        )

    async def _math_via_lean(self, input_text: str) -> "NucleoResponse":
        """
        Pipeline principal para consultas matematicas.

        Arquitectura (Lean-primero):
          1. LLM formaliza el enunciado en Lean 4   (rol: formalizador)
          2. Lean verifier comprueba la prueba        (fuente de verdad)
          3. Si hay sorry → solver cascade intenta llenarlos
          4. LLM traduce el resultado a lenguaje natural amable
             (rol: traductor, NO razonador)

        La verdad matematica viene de Lean, no del LLM.
        """
        # Demo mode: skip Lean pipeline, return structured educational content
        if self._llm is not None and self._llm.is_demo:
            self._log_motivo_demo("is_demo")
            return self._demo_educational_response(input_text)

        # Extra guard: provider package not installed → _get_client() falls back
        # to DemoLLMClient even when api_key is set (is_demo would be False).
        # Running the pipeline with DemoLLMClient produces garbled output.
        from nucleo.llm.client import LLMClient, DemoLLMClient as _DemoClient
        if self._llm is not None and isinstance(self._llm._get_client(), _DemoClient):
            self._log_motivo_demo("cliente_demo")
            return self._demo_educational_response(input_text)

        from nucleo.multi_agent.specialized_agent import classify_query
        from nucleo.multi_agent.colimit_agents import (
            domain_default_tactic, domain_tactic_order)
        lean_system = LLMClient.LEAN_SYSTEM_PROMPT
        context = self._find_relevant_context(input_text, self._graph)
        context["task"] = "lean_formalization"

        # ── Clasificación de área → táctica por defecto del ColimitAgent ─────
        # El join-envoltorio del área detectada provee la táctica de entrada
        # al SolverCascade (paper §3.5, Principio 3.1).
        _area = classify_query(input_text)
        # El ORDEN medido del area (ver CATEGORY_TACTIC_ORDER), no un nombre:
        # la cascada consume una secuencia, y `simp` gana en las once areas
        # medidas, asi que lo que distingue un area de otra esta en la cola.
        _domain_order = domain_tactic_order(_area)
        _domain_tactic = domain_default_tactic(_area)
        # Vacia mientras no haya experiencia real. Se rellena abajo solo si el
        # agente especializado recuerda una tactica que YA funciono aqui; solo
        # entonces adelanta al orden medido.
        _tactica_aprendida = ""

        # Si el sistema multi-agente esta activo, preferir una tactica
        # aprendida de exito real en esta categoria (memoria procedimental
        # del agente especializado) sobre el valor estatico por defecto.
        # query_best_tactic nunca inventa: si no hay experiencia previa
        # suficiente devuelve None y _domain_tactic no cambia.
        if self._multi_agent_orchestrator is not None:
            try:
                _learned = self._multi_agent_orchestrator.mes_bridge.query_best_tactic(
                    _area, input_text
                )
                if _learned:
                    logger.debug(
                        f"_math_via_lean: tactica aprendida '{_learned}' "
                        f"reemplaza default '{_domain_tactic}' para area={_area!r}"
                    )
                    _domain_tactic = _learned
                    _tactica_aprendida = _learned
            except Exception as e:
                logger.debug(f"query_best_tactic error (no bloqueante): {e}")

        logger.debug(f"_math_via_lean: area={_area!r}, domain_tactic={_domain_tactic!r}")

        # ── Clasificación del tipo de query ───────────────────────────────────
        # Lean es siempre la fuente de verdad. Solo bypass para demostraciones
        # EXPLÍCITAMENTE geométricas/visuales donde no hay código que verificar.
        q_lower = self._normalize_text(input_text)

        _visual_only = (
            "demostracion geometrica", "demostracion visual", "prueba visual",
            "prueba geometrica", "como lo haria euclides", "al estilo euclides",
            "geometricamente como", "prueba sin palabras",
        )
        if any(m in q_lower for m in _visual_only):
            return await self._math_educational_explanation(input_text, context)

        # Peticion de revision de documento/paper ("encuentra los errores", etc.):
        # NO es un objetivo unico para formalizar — es una revision sobre TODO
        # el texto adjunto. Forzar _math_via_lean aqui hace que el LLM invente
        # un unico teorema (a veces ajeno al pedido) y lo intente formalizar,
        # en vez de listar los errores reales del documento completo.
        _review_markers = (
            "encuentra los errores", "encuentra errores", "busca los errores",
            "busca errores", "errores que encuentres", "señala los errores",
            "señala errores", "identifica los errores", "identifica errores",
            "detecta los errores", "detecta errores", "que errores tiene",
            "revisa el documento", "revisa el paper", "revisa el archivo",
            "revisa este documento", "revisa este paper", "revisa este archivo",
            "encuentra los fallos", "encuentra fallos", "encuentra problemas",
            "find the errors", "find errors", "review this paper",
            "review this document", "what errors",
        )
        if any(m in q_lower for m in _review_markers):
            return await self._review_document_for_errors(input_text, context)

        # Detectar queries definitionales: "qué es X", "define X", "explícame X"
        # → Lean formaliza la DEFINICIÓN (no una prueba): #check, structure, class
        _definitional_markers = (
            "que es", "que son", "define ", "definicion de", "definir ",
            "explicame", "explicar ", "que significa", "como funciona",
            "que es un", "que es una", "que es el", "que es la",
            "que son los", "que son las", "describe ", "descripcion de",
            "what is", "what are", "definition of", "explain what",
            "what does", "how does", "describe ",
        )
        _is_definitional = any(m in q_lower for m in _definitional_markers)

        # ── Paso 1: LLM formaliza → Lean 4 ──────────────────────────────────
        # Construir ejemplos few-shot relevantes (miniF2F)
        few_shot_block = self._build_few_shot_context(input_text)

        # ── Referencias ancladas (verdad matemática anclada en Mathlib) ─────
        # Ver _MATHLIB_REFS: el LLM no debe inventar nombres de lemas.
        q_norm = self._normalize_text(input_text)
        _ref = _mathlib_ref_for(q_norm)
        extra_ref = (
            f"\nReferencia de Mathlib para este tema:\n```lean\n{_ref}\n```\n"
            if _ref else ""
        )

        # Detectar si el usuario solo quiere el enunciado (no la prueba)
        _enunciar = any(w in q_norm for w in ("enuncia", "enunciar", "enunciado", "que dice", "que establece", "que afirma"))
        _solo_enunciar_hint = (
            "- El usuario solo pide ENUNCIAR (no demostrar). Escribe ÚNICAMENTE el `theorem` con `sorry` en el cuerpo, sin intentar dar una prueba.\n"
            if _enunciar else ""
        )

        # ── Paso 1: Prompt de formalización — diferente para definiciones vs pruebas
        if _is_definitional:
            # Queries "qué es X" → Lean muestra la definición/tipo que ya existe
            # en Mathlib. El LLM NO inventa; Lean confirma que el tipo existe.
            formalize_prompt = (
                "Tu única tarea es escribir UN SOLO bloque de código Lean 4 que "
                "formalice la DEFINICIÓN o muestre el concepto en Mathlib.\n\n"
                f"Consulta: {input_text}\n\n"
                + (f"Referencias de Mathlib para este tema:\n```lean\n{extra_ref}\n```\n\n"
                   if extra_ref else "")
                + "Instrucciones OBLIGATORIAS:\n"
                "- Si el concepto existe en Mathlib, usa `#check NombreDelConcepto`.\n"
                "- Si es una estructura o clase, escribe la `structure`/`class` con sus campos.\n"
                "- Incluye los imports necesarios de Mathlib.\n"
                "- Para definiciones con propiedades universales, muestra la firma de la función\n"
                "  evaluación o la adjunción, con los tipos correctos.\n"
                "- NO intentes demostrar ningún teorema — solo formaliza la definición.\n"
                "- Usa `sorry` solo si necesitas un término auxiliar desconocido.\n"
                "- SOLO el bloque Lean 4, nada más.\n"
                "- CRITICAL: verifica que los tipos sean consistentes. Ejemplo correcto:\n"
                "  eval : B^A × A → B  (el exponencial es B^A, NO C^A ni ningún otro)."
            )
        else:
            # Queries de prueba → formalización estándar
            formalize_prompt = (
                "Tu única tarea es escribir UN SOLO bloque de código Lean 4 (no varios) que formalice "
                "el siguiente enunciado o pregunta matemática.\n\n"
                f"Enunciado: {input_text}\n\n"
                + extra_ref
                + (
                    f"Ejemplos de referencia en Lean 4 (LeanWorkbook, pruebas reales):\n"
                    f"{few_shot_block}\n\n"
                    if few_shot_block else ""
                )
                + "Instrucciones OBLIGATORIAS:\n"
                "- Escribe SOLO UN bloque de código Lean 4. Nada más.\n"
                "- El código debe ser autocontenido (con los imports necesarios).\n"
                "- Si es una afirmación, escríbela como `theorem` o `lemma`.\n"
                "- Si no sabes la prueba completa, usa `sorry` como marcador.\n"
                + _solo_enunciar_hint
                + "- PROHIBIDO: tomar la afirmación principal como hipótesis y concluirla trivialmente.\n"
                "  EJEMPLO PROHIBIDO: `(h : a^2+b^2=c^2) : c^2=a^2+b^2 := h.symm` — tautología.\n"
                + (("Nombres de Mathlib VERIFICADOS para esta consulta "
                    "(existen; comprobados con #check):\n"
                    + "\n".join("  %s: %s" % (k, v)
                                 for k, v in context["mathlib_verificado"].items())
                    + "\nUsa estos cuando encajen. Si necesitas otro que no esté "
                      "aquí, escríbelo igualmente, pero sé consciente de que no "
                      "está comprobado.\n\n")
                   if isinstance(context, dict) and context.get("mathlib_verificado")
                   else "")
                + "- PROHIBIDO: generar múltiples versiones del mismo resultado.\n"
                "- Si el enunciado que se te pide es FALSO, NO lo demuestres: formaliza su NEGACIÓN\n"
                "  y abre el bloque con la línea `-- REFUTACION: <por qué el enunciado es falso>`.\n"
                "- Usa los tipos y teoremas de Mathlib apropiados.\n"
                "- No pongas explicaciones fuera del bloque de código."
            )
        lean_gen = await self._llm.generate(
            formalize_prompt, system=lean_system, context=context
        , sin_historial=True)
        # Si DemoLLMClient fue usado (race condition con reconfigure()),
        # la respuesta no contiene código Lean — abortar el pipeline aquí.
        from nucleo.llm.client import DemoLLMClient as _DemoClientPipe
        if (
            isinstance(self._llm._get_client(), _DemoClientPipe)
            or "Modo demo activo" in lean_gen.content
        ):
            return self._demo_educational_response(input_text)
        lean_code = self._extract_lean_code(lean_gen.content)
        if not lean_code:
            lean_code = lean_gen.content.strip()

        # ── ¿El código DEMUESTRA algo, o Lean acepta un archivo vacío? ────
        def _prueba_algo(code: str) -> bool:
            """Un archivo sin proposiciones no puede estar «verificado».

            Lean procesa sin errores un archivo que solo tiene `import` y
            `#check`, y devuelve SUCCESS. El pipeline lo tomaba por bueno y
            estampaba la insignia. Medido en el banco de fidelidad, sobre
            «demuestra que la unión de dos abiertos es abierta»:

                import Mathlib
                #check @GrothendieckGroup
                #check @CategoryTheory.Limits.HasZeroMorphisms
                #check @Module.Projective
                #check @FredholmOperator

            Cero teoremas, cero relación con la pregunta, y respuesta con sello
            de verificada. `#check` consulta un tipo; no demuestra nada.

            Se exige una declaracion con CUERPO: `theorem`/`lemma`/`example`
            seguidos, mas adelante, de `:=`. Un `theorem ... := by sorry` sí
            cuenta aqui — que quede un `sorry` lo detecta el estado `parcial`,
            que es harina de otro costal.
            """
            import re
            # Fuera comentarios: un `-- theorem ...` o un docstring que hable
            # de teoremas no es un teorema. Y fuera la exigencia de inicio de
            # linea, que fallaba sobre codigo real por razones tontas
            # —indentacion, `namespace`, una declaracion partida—.
            limpio = re.sub(r"/-[\s\S]*?-/", " ", code)
            limpio = re.sub(r"--[^\n]*", " ", limpio)
            return bool(re.search(r"\b(theorem|lemma|example)\b[\s\S]*?:=",
                                  limpio))

        # ── ¿Lean va a verificar la NEGACIÓN de lo preguntado? ────────────
        def _es_refutacion(code: str) -> bool:
            """El formalizador marca con `-- REFUTACION:` los enunciados falsos.

            Es un canal explicito para algo que el modelo ya hacia por su
            cuenta —escribir en un comentario que el enunciado propuesto era
            falso— y que el pipeline no leia: veia SUCCESS y estampaba la
            insignia de verificado sobre una respuesta a otra pregunta.
            """
            import re
            return bool(re.search(r"REFUTACI[OÓ]N\s*:", code, re.I))

        # ── Detección de formalización trivial → regenerar ─────────────────
        def _is_trivial_lean(code: str) -> bool:
            """
            Detecta la tautologia real: la conclusion se prueba DEVOLVIENDO una
            hipotesis.

            LA VERSION ANTERIOR SE DISPARABA CASI SIEMPRE. Uno de sus patrones
            casaba con la forma `:= by` al final de linea —
            el idioma normal de Lean para una prueba tactica multilinea. Medido:
            `theorem add_127_458 : 127 + 458 = 585 := by norm_num` salia
            marcado como trivial, y no tiene ni una sola hipotesis.

            Ahora se exige lo que la palabra significa: que exista una hipotesis
            con nombre y que el CUERPO de la prueba sea exactamente ese nombre
            (o `h.symm`, o `by exact h`). Una prueba por tacticas nunca lo es.
            """
            import re

            cuerpo = code
            # nombres de hipotesis: los binders `(h : ...)` y `{h : ...}`
            hipotesis = set(re.findall(r"[({]\s*(\w+)\s*:", cuerpo))
            if not hipotesis:
                return False          # sin hipotesis no puede haber tautologia

            # el termino de prueba: lo que va tras el ULTIMO `:=`
            trozo = cuerpo.rsplit(":=", 1)
            if len(trozo) != 2:
                return False
            prueba = trozo[1].strip()

            # una prueba por tacticas no es una tautologia por devolver h
            if prueba.startswith("by"):
                cuerpo_tactico = prueba[2:].strip()
                m = re.fullmatch(r"exact\s+(\w+)(?:\.symm)?", cuerpo_tactico)
                return bool(m and m.group(1) in hipotesis)

            m = re.fullmatch(r"(\w+)(?:\.symm)?", prueba)
            return bool(m and m.group(1) in hipotesis)

        if _is_trivial_lean(lean_code):
            # Regenerar diciendo QUE esta mal, no QUE MATEMATICAS usar.
            #
            # El reintento llevaba cableado un dominio concreto —«usa la
            # geometria euclidiana o espacios con producto interior, con
            # inner_mul_le_norm_sq o norm_add_sq_real»—, escrito para un caso
            # de Pitagoras y aplicado a TODA consulta que disparase el
            # detector. Con el falso positivo de arriba, eso significaba que
            # «¿cuanto es 127 + 458?» se formalizaba como un teorema sobre
            # vectores ortogonales: Lean lo verificaba, la insignia decia
            # VERIFICADO, y el teorema no era el que nadie habia preguntado.
            #
            # Un reintento no debe elegir la matematica. Debe decir cual es el
            # defecto y devolver el problema al enunciado original.
            retry_prompt = (
                f"{formalize_prompt}\n\n"
                "ATENCIÓN: tu respuesta anterior era una TAUTOLOGÍA — tomaba la "
                "afirmación como hipótesis y la devolvía como prueba, así que no "
                "demuestra nada.\n"
                "Formaliza el enunciado ORIGINAL tal cual: el teorema debe decir "
                "lo que la pregunta pide, sin hipótesis que ya contengan la "
                "conclusión. No cambies de tema ni lo traduzcas a otra rama de "
                "las matemáticas. Si no sabes la prueba, escribe el enunciado "
                "correcto y cierra con `sorry`."
            )
            lean_gen2 = await self._llm.generate(
                retry_prompt, system=lean_system, context=context
            , sin_historial=True)
            lean_code2 = self._extract_lean_code(lean_gen2.content) or lean_gen2.content.strip()
            if not _is_trivial_lean(lean_code2):
                lean_code = lean_code2

        # ── Paso 2: Lean verifier ─────────────────────────────────────────
        # EL GRAFO ELIGE LOS IMPORTS.
        #
        # Las skills activadas se traducen a modulos de Mathlib mediante
        # `data/mathlib_modulos.json`, que se construye leyendo DONDE se
        # declara cada nombre en el fuente. Es el sitio donde el grafo influye
        # sobre lo que Lean ve, que era la idea original de ponerlo entre el
        # LLM y el verificador.
        try:
            self._lean.sugerir_imports(self._modulos_mathlib(context))
        except Exception:
            logger.debug("no se pudieron sugerir imports", exc_info=True)

        result = await self._lean.check_code(lean_code)

        # ── Paso 2b: reparacion de imports y reintento ────────────────────
        # El fallo mas comun de un LLM escribiendo Lean es usar un lema que
        # existe pero cuyo modulo no importa. En vez de mantener parches por
        # area, se busca la declaracion en las fuentes de Mathlib (~2 s) y se
        # reintenta una vez. Solo se acepta el reintento si mejora: no se
        # sustituye un resultado por otro peor.
        if result.status == LeanResultStatus.ERROR:
            _reparado = self._lean.repair_imports(
                lean_code, result.error_messages
            )
            if _reparado:
                _r2 = await self._lean.check_code(_reparado)
                _mejora = (
                    _r2.status in (LeanResultStatus.SUCCESS,
                                   LeanResultStatus.SORRY)
                    or len(_r2.error_messages) < len(result.error_messages)
                )
                if _mejora:
                    logger.info(
                        f"Lean: reparacion de imports efectiva "
                        f"({result.status.name} -> {_r2.status.name})"
                    )
                    lean_code, result = _reparado, _r2

        # ── Paso 2c: revision con el veredicto de Lean como realimentacion ──
        # Triaje por severidad. repair_imports solo arregla errores MECANICOS
        # (modulo que falta). Si el error es SEMANTICO —type mismatch, tactic
        # failed, unsolved goals— hay que reformular la prueba, y para eso el
        # generador necesita ver lo que Lean dijo.
        #
        # Antes ese diagnostico se calculaba y solo se imprimia para el usuario;
        # el intento moria ahi. Ahora vuelve al LLM, acotado a 2 rondas y
        # aceptando la revision solo si mejora.
        _rondas_revision = 0
        if result.status == LeanResultStatus.ERROR:
            _primer_err = (result.get_first_error() or "").lower()
            _es_mecanico = any(m in _primer_err for m in self._ERRORES_MECANICOS)
            if not _es_mecanico:
                lean_code, result, _rondas_revision = await self._revisar_con_lean(
                    lean_code, result, formalize_prompt, lean_system, context
                )

        if result.status == LeanResultStatus.NOT_AVAILABLE:
            # lake no instalado (despliegue en la nube) — no es un error de lógica
            verification_status = "sin_entorno"
            verification_note   = (
                "Lean 4 no está disponible en este servidor. "
                "El código fue generado por el NLE pero no ejecutado. "
                "Para verificarlo localmente: `lake init my_project && lake update`, "
                "luego pega el código en un archivo `.lean` del proyecto."
            )
            confidence    = 0.75
            success_value = 0.5

        elif result.is_success and not _prueba_algo(lean_code):
            # LEAN ACEPTO UN ARCHIVO QUE NO DEMUESTRA NADA.
            #
            # No es un exito: es una formalizacion fallida que Lean no puede
            # rechazar, porque un archivo de `#check` es sintacticamente
            # correcto. La unica lectura honesta es que no hay prueba.
            verification_status = "sin_teorema"
            verification_note = (
                "El código generado no contiene ningún teorema: Lean lo aceptó "
                "porque es sintácticamente válido, pero no demuestra nada."
            )
            confidence    = 0.30
            success_value = 0.0

        elif result.is_success and _es_refutacion(lean_code):
            # LEAN VERIFICO, PERO LA NEGACION DE LO QUE SE PREGUNTO.
            #
            # Sin esta rama, pedir «demuestra que la raiz de 4 es irracional»
            # —que es falso— devolvia una respuesta con sello de VERIFICADA. El
            # modelo hacia lo correcto: detectaba la falsedad, formalizaba la
            # negacion y lo decia en un comentario del codigo. Era el pipeline
            # el que no miraba: veia SUCCESS y estampaba la insignia.
            #
            # La respuesta esta igual de respaldada que cualquier otra —Lean la
            # verifico— pero responde OTRA COSA, y eso tiene que ir delante.
            verification_status = "refutado"
            verification_note = (
                "Lean 4 verificó la NEGACIÓN del enunciado: lo que se preguntó "
                "es falso."
            )
            confidence    = 0.95
            success_value = 1.0

        elif result.is_success:
            verification_status = "verificado"
            verification_note = (
                "La prueba fue verificada formalmente por Lean 4 sin errores."
            )
            confidence    = 0.95
            success_value = 1.0

        elif result.status == LeanResultStatus.SORRY:
            # ── Paso 3: Solver cascade intenta llenar los sorry ───────────
            # domain_tactic: táctica por defecto del ColimitAgent del área
            # detectada, colocada primera en la cascada (paper §3.5).
            sorry_msg, confidence, success_value = await self._try_solve_sorries(
                lean_code, result, domain_tactic=_tactica_aprendida,
                domain_order=_domain_order, area_premisas=_area,
            )
            verification_status = "parcial"
            verification_note = (
                f"Lean 4 aceptó la estructura de la prueba. {sorry_msg}"
            )

        elif result.status == LeanResultStatus.TIMEOUT:
            verification_status = "timeout"
            verification_note = (
                "Lean 4 tardó demasiado verificando con Mathlib. "
                "El código fue generado correctamente pero no se pudo verificar en el tiempo límite. "
                "Esto es normal en la primera ejecución del día mientras Lean carga Mathlib (~500 MB de .olean). "
                "Intenta de nuevo — la segunda verificación será mucho más rápida."
            )
            confidence    = 0.65
            success_value = 0.0

        else:
            error_info = self._analyze_lean_errors(result)
            first_err  = result.get_first_error() or "error desconocido"
            err_type   = error_info.get("type", "unknown")
            hint = self._lean_hint(first_err)
            verification_status = "no_verificado"
            _tras = (
                f" Tras {_rondas_revision} ronda(s) de revisión con el error de Lean."
                if _rondas_revision else ""
            )
            verification_note = (
                f"Lean 4 detectó un error de tipo `{err_type}`: {first_err}. "
                f"Diagnóstico: {hint}.{_tras}"
            )
            confidence    = 0.6
            success_value = 0.2

        # Cerrar el ciclo con el sistema multi-agente: sin esto, report_lean_result
        # existia pero nunca se llamaba, la memoria procedimental por categoria
        # se quedaba vacia para siempre y query_best_tactic() (arriba) jamas
        # tenia nada que devolver. "sin_entorno" se omite: no es un intento real.
        if self._multi_agent_orchestrator is not None and verification_status != "sin_entorno":
            _lean_outcome = {
                "verificado": "success",
                "parcial": "partial",
            }.get(verification_status, "failed")
            self.report_lean_result(input_text, _domain_tactic, _lean_outcome, success_value)

        # ── Paso 4: LLM traduce — el LLM es solo la boca, Lean es el cerebro ─
        _sin_entorno = verification_status == "sin_entorno"
        # Cuando lake no está disponible, el LLM NO debe ver el error de infraestructura.
        # Le pasamos un estado neutro para que se centre en el contenido matemático.
        _vn_for_llm = (
            "Código generado por el NLE, pendiente de ejecución local."
            if _sin_entorno else verification_note
        )
        if _is_definitional:
            translate_prompt = (
                self._REGLAS_TRADUCTOR
                +                 "Eres un matemático experto. Tu trabajo es explicar la definición "
                "matemática que Lean 4 acaba de formalizar.\n\n"
                "IMPORTANTE: El código Lean de abajo es la fuente de verdad. "
                "Tu explicación debe ser CONSISTENTE con los tipos que aparecen en él. "
                "Si el código dice `eval : B^A × A → B`, tu explicación debe usar exactamente eso.\n\n"
                + f"Pregunta original:\n> {input_text}\n\n"
                f"Código Lean 4 (formalización de la definición):\n```lean\n{lean_code}\n```\n\n"
                f"Estado: {_vn_for_llm}\n\n"
                "Estructura tu respuesta así:\n\n"
                "## Definición formal\n"
                "[Enuncia la definición con notación matemática $...$ exactamente "
                "como aparece en el código Lean — mismos tipos, mismas firmas.]\n\n"
                "## Intuición\n"
                "[Explica qué *significa* esta definición en palabras simples. "
                "Un ejemplo concreto siempre ayuda.]\n\n"
                "## Propiedades clave\n"
                "[Las 2-3 propiedades más importantes, ancladas en el código Lean.]\n\n"
                "## En Lean / Mathlib\n"
                f"[Cómo se llama en Mathlib y cómo usarlo.]\n\n"
                + (f"## Nota de verificación\n[{verification_note}]\n\n"
                   if verification_status not in ("verificado", "sin_entorno") else "")
            )
        else:
            translate_prompt = (
                self._REGLAS_TRADUCTOR
                +                 "Eres un traductor matemático experto. Tu trabajo es explicar el siguiente "
                "código Lean 4 en lenguaje natural claro, preciso y amable.\n\n"
                "IMPORTANTE: Si el código Lean toma la afirmación principal como hipótesis "
                "y la concluye trivialmente, indícalo y explica el teorema REAL.\n\n"
                + f"Pregunta original del usuario:\n> {input_text}\n\n"
                f"Código Lean 4 generado:\n```lean\n{lean_code}\n```\n\n"
                f"Estado: {_vn_for_llm}\n\n"
                "Escribe tu explicación con estas secciones:\n\n"
                "## ¿Qué dice este resultado?\n"
                "[Explica el enunciado con tus palabras.]\n\n"
                "## ¿Cómo lo demuestra Lean?\n"
                "[Estrategia de la prueba, sin copiar código.]\n\n"
                "## ¿Por qué es correcto?\n"
                "[Intuición matemática detrás del argumento.]"
                + (f"\n\n## Nota sobre la verificación\n[{verification_note}]"
                   if verification_status not in ("verificado", "sin_entorno") else "")
            )
        # Re-verificar que el cliente sigue siendo real antes de la traducción
        # (guard contra race condition con reconfigure() de otra sesión Streamlit)
        if isinstance(self._llm._get_client(), _DemoClientPipe):
            _translation_text = verification_note
        else:
            translation = await self._llm.generate(
                translate_prompt, system=lean_system, context=context
            , sin_historial=True)
            _translation_text = (
                translation.content
                if "Modo demo activo" not in translation.content
                else verification_note
            )

        # ── Ensamblaje final ───────────────────────────────────────────────
        # Badge diferenciado: definición vs prueba vs sin entorno
        if _sin_entorno:
            status_badge = f"**Lean 4 ☁ — código generado** · área: `{_area}`"
        elif verification_status == "timeout":
            status_badge = f"**Lean 4 ⏱ — timeout en primera carga de Mathlib** · área: `{_area}`"
        elif _is_definitional:
            status_badge = {
                "verificado":    f"**Lean 4 ✓ — definición verificada formalmente** · área: `{_area}`",
                "parcial":       f"**Lean 4 ~ — definición formalizada (parcial)** · área: `{_area}`",
                "no_verificado": f"**Lean 4 ↯ — definición pendiente de ajuste Mathlib** · área: `{_area}`",
                "refutado":      f"**Lean 4 ✓ — se verificó la NEGACIÓN del enunciado** · área: `{_area}`",
                "sin_teorema":   f"**Lean 4 ⊘ — el código no contiene ningún teorema** · área: `{_area}`",
            }.get(verification_status,
                  f"**Lean 4 — {verification_status}** · área: `{_area}`")
        else:
            status_badge = {
                "verificado":    f"**Lean 4 ✓ — prueba verificada formalmente** · área: `{_area}`",
                "parcial":       f"**Lean 4 ~ — estructura verificada (sorry parcial)** · área: `{_area}`",
                "no_verificado": f"**Lean 4 ↯ — formalización pendiente de ajuste** · área: `{_area}`",
                "refutado":      f"**Lean 4 ✓ — se verificó la NEGACIÓN del enunciado** · área: `{_area}`",
                "sin_teorema":   f"**Lean 4 ⊘ — el código no contiene ningún teorema** · área: `{_area}`",
            }.get(verification_status,
                  f"**Lean 4 — {verification_status}** · área: `{_area}`")

        # POR QUE `.get` Y NO INDEXACION DIRECTA.
        #
        # Estos dos diccionarios indexaban con `[...]`, asi que cada estado
        # nuevo reventaba la respuesta entera con un KeyError. Paso justo con
        # `refutado` y `sin_teorema`: los dos arreglos de fidelidad tumbaban
        # las mismas consultas que venian a arreglar, y la excepcion se
        # tragaba mas arriba dejando una respuesta sin `lean_result` — es
        # decir, sin ninguna senal de que Lean hubiera corrido.
        #
        # Lo encontro el banco de fidelidad, no los tests: 766 tests en verde
        # y las tres consultas de refutacion caidas.

        # ── Compuerta: el veredicto de Lean gobierna la FORMA de la respuesta
        #
        # Hasta ahora las cinco ramas —verificado, parcial, no_verificado,
        # timeout, sin_entorno— producian exactamente la misma estructura:
        # prosa del LLM, badge, codigo. Solo cambiaba una etiqueta. Una prueba
        # que Lean RECHAZO se entregaba con el mismo aspecto que una verificada,
        # y el diagnostico de Lean (verification_note, con el error literal y la
        # pista) no se mostraba en ninguna parte: se usaba para el prompt de
        # traduccion y se tiraba.
        #
        # Para un sistema cuya tesis es "la verdad matematica la produce Lean",
        # que su veredicto no cambie nada visible es una contradiccion interna.
        # Ahora, cuando Lean no verifica, el aviso va DELANTE de la prosa y el
        # motivo se muestra.
        _verificado = verification_status == "verificado"

        if _verificado:
            content = (
                f"{_translation_text}\n\n"
                f"---\n\n"
                f"{status_badge}\n\n"
                f"```lean\n{lean_code}\n```"
            )
        else:
            _titulo = {
                "sin_teorema": "❌ **No hay prueba.** El código generado no "
                               "contiene ningún teorema — Lean lo aceptó por "
                               "ser sintácticamente válido, pero no demuestra "
                               "nada. Lo que sigue no tiene respaldo formal.",
                "refutado": "🔍 **El enunciado que preguntaste es FALSO.** "
                            "Lean 4 verificó formalmente su negación — lo que "
                            "sigue explica el enunciado verdadero, no el que "
                            "pediste.",
                "parcial": "⚠️ **Verificación parcial** — Lean aceptó la estructura, "
                           "pero quedan pasos sin demostrar.",
                "no_verificado": "❌ **Lean 4 NO verificó esta prueba.** "
                                 "Lo que sigue es la explicación del modelo, "
                                 "sin respaldo formal.",
                "timeout": "⏱️ **Sin verificar** — Lean no terminó a tiempo. "
                           "La explicación no tiene respaldo formal todavía.",
                "sin_entorno": "☁️ **Sin verificar** — no hay Lean en este "
                               "servidor. El código está generado pero no ejecutado.",
            }.get(verification_status,
                  "⚠️ **Sin verificación formal.**")

            content = (
                f"{_titulo}\n\n"
                f"> {verification_note}\n\n"
                f"---\n\n"
                f"{_translation_text}\n\n"
                f"---\n\n"
                f"{status_badge}\n\n"
                f"```lean\n{lean_code}\n```"
            )

        self._record_lean_experience("lean-tactics", success_value)

        return NucleoResponse(
            content=content,
            action_type=ActionType.ASSIST,
            lean_result=result,
            confidence=confidence,
            metadata={
                "verification_status": verification_status,
                # Booleano explicito para que la interfaz pueda distinguir sin
                # tener que interpretar la cadena de estado.
                #
                # NO se marca aqui "sin_verificacion_lean": esa clave significa
                # que la respuesta NUNCA paso por el verificador (bypass
                # educativo/geometrico), y app.py le anade un aviso que dice
                # "el argumento no se formalizo ni lo comprobo el verificador".
                # Reutilizarla para "Lean rechazo" producia una respuesta que se
                # contradecia: la insignia decia que Lean corrio y fallo, y dos
                # lineas mas abajo que no se habia formalizado. Aqui Lean SI
                # corrio; el aviso correcto ya va delante de la explicacion.
                "verificado": _verificado,
                "area": _area,
                "rondas_revision": _rondas_revision,
            },
        )

    def _build_few_shot_context(self, query: str) -> str:
        """
        Buscar 2-3 ejemplos few-shot de miniF2F relevantes para la query.

        Usa el banco lean_examples.json (cargado en initialize).
        Selecciona por categoria y keyword overlap.
        """
        import re

        if not self._lean_examples:
            return ""

        query_lower = query.lower()
        tokens = set(query_lower.split())

        # Inferir categoria de la query
        cat_map = {
            "algebra":        {"algebra", "ecuacion", "polinomio", "equation", "polynomial"},
            "number_theory":  {"primo", "divisible", "modulo", "prime", "integer", "number"},
            "geometry":       {"geometria", "triangulo", "angulo", "geometry", "triangle"},
            "analysis":       {"limite", "continua", "integral", "limit", "continuous"},
            "combinatorics":  {"combinatoria", "permutacion", "combination", "counting"},
        }
        # Subcadena, no token exacto: con `tokens & keywords` la consulta
        # "numeros primos" no casaba con la clave "primo" (plural) y caia a la
        # categoria generica, sirviendo ejemplos de otra rama.
        best_cat = "general"
        best_score = 0
        for cat, keywords in cat_map.items():
            score = sum(1 for k in keywords if k in query_lower)
            if score > best_score:
                best_score = score
                best_cat = cat

        # Tomar ejemplos de la categoria inferida, o de competition_math como
        # fallback.
        candidates = (
            self._lean_examples.get(best_cat, [])
            or self._lean_examples.get("competition_math", [])
            or next(iter(self._lean_examples.values()), [])
        )
        if not candidates:
            return ""

        # Ordenar por afinidad. Antes se servian SIEMPRE los dos primeros de la
        # categoria, asi que la misma pareja acompanaba a cualquier consulta.
        #
        # La afinidad se mide sobre el ENUNCIADO FORMAL, no sobre el texto en
        # lenguaje natural: el banco esta en ingles y las consultas suelen venir
        # en español, asi que el solapamiento de palabras daba casi siempre cero
        # y el desempate quedaba al azar. Los simbolos matematicos, en cambio,
        # son los mismos en los dos idiomas.
        _SIMBOLOS = ("≤", "<", "≥", ">", "=", "^", "√", "∑", "∏", "∫",
                     "∀", "∃", "≡", "∣", "%")
        _q = query_lower
        _q_simbolos = {t for t in _SIMBOLOS if t in _q}
        _q_palabras = {
            t for t in re.findall(r"[a-záéíóúñ]{4,}", _q)
        }

        def _afinidad(ex: dict) -> int:
            formal = (ex.get("statement") or "")
            nl = (ex.get("nl") or "").lower()
            # Simbolos compartidos: senal fuerte y agnostica del idioma.
            p = 2 * sum(1 for t in _q_simbolos if t in formal)
            # Palabras largas del enunciado natural: ayuda cuando la consulta
            # viene en ingles.
            p += sum(1 for t in _q_palabras if t in nl)
            return p

        selected = sorted(candidates, key=_afinidad, reverse=True)[:2]
        if not selected:
            return ""

        # Renderizado en LEAN 4.
        #
        # Antes se envolvian las tacticas en `begin ... end`, que es Lean 3: el
        # propio renderizador inyectaba sintaxis obsoleta aunque el banco fuera
        # correcto. El banco tambien lo era —venia de miniF2F en Lean 3— y el
        # prompt terminaba pidiendo al modelo que tradujera de dialecto mientras
        # formalizaba. Ahora ambos son Lean 4 (scripts/seed_lean4_examples.py).
        lines = []
        for ex in selected:
            enunciado = (ex.get("statement") or "").strip()
            tacs = [t for t in (ex.get("tactics") or []) if t][:3]
            # El enunciado del banco termina en `:= by sorry`; se sustituye el
            # sorry por las tacticas reales.
            cuerpo = "\n  ".join(tacs) if tacs else "sorry"
            if enunciado.endswith("sorry"):
                enunciado = enunciado[: -len("sorry")].rstrip()
                bloque = f"{enunciado}\n  {cuerpo}"
            else:
                bloque = f"{enunciado} := by\n  {cuerpo}"
            # Cabecera SIN LaTeX: el enunciado natural del banco viene lleno de
            # `\left\{`, `\begin{aligned}`... que en un comentario `--` es ruido
            # puro y ademas ensucia el prompt con sintaxis que no es Lean.
            lines.append(f"-- {ex.get('name', 'ejemplo')}\n{bloque}")

        return "\n\n".join(lines)

    async def _try_solve_sorries(
        self, code: str, result: LeanResult, domain_tactic: str = "",
        domain_order: Optional[list[str]] = None, area_premisas: str = "",
    ) -> tuple[str, float, float]:
        """Try solver cascade on sorry-containing code.

        Args:
            code: Lean source with sorries
            result: LeanResult from prior check
            domain_tactic: Default tactic from the ColimitAgent of the
                detected area (paper §3.5). Placed first in the cascade
                via GoalAnalyzer.prioritize() → try_fill_sorry_smart().
        """
        sorries = find_sorries_in_text(code)
        if not sorries and self._solver_cascade:
            return (
                "Prueba contiene sorry pero no se pudo localizar.",
                0.4, -0.2
            )

        solved = []
        failed = []
        for sorry in sorries:
            ctx = SorryContext(
                file_path=sorry.file,
                line_number=sorry.line,
                goal=sorry.in_declaration or "",
                goal_type="",
                surrounding_code="\n".join(sorry.context_before),
            )
            filled = False
            cascade_already_ran = False
            # Smart cascade: domain_tactic placed first (paper §3.5)
            if self._solver_cascade and (domain_tactic or domain_order or ctx.goal):
                cascade_result = await self._solver_cascade.try_fill_sorry_smart(
                    code=code,
                    sorry_line=ctx.line_number,
                    goal_text=ctx.goal,
                    domain_tactic=domain_tactic,
                    domain_order=domain_order,
                    area_premisas=area_premisas,
                )
                cascade_already_ran = True
                if cascade_result.success:
                    solved.append(cascade_result.replacement_code or "")
                    filled = True
            if not filled and self._sorry_filler:
                # skip_cascade=True avoids re-running the same N solvers
                # in original order after smart cascade already tried them all
                fill_result = await self._sorry_filler.fill_sorry_with_cascade(
                    ctx, code, skip_cascade=cascade_already_ran
                )
                if fill_result.chosen_solution:
                    solved.append(fill_result.chosen_solution.code)
                else:
                    failed.append(sorry.line)
            elif not filled:
                failed.append(sorry.line)

        if solved and not failed:
            content = f"Todos los sorry resueltos: {', '.join(solved)}"
            return content, 0.95, 0.9
        elif solved:
            content = (
                f"Resueltos {len(solved)}/{len(sorries)} sorry. "
                f"Lineas pendientes: {failed}"
            )
            return content, 0.6, 0.3
        else:
            content = f"No se pudo resolver automaticamente {len(sorries)} sorry."
            return content, 0.3, -0.3

    def _analyze_lean_errors(self, result: LeanResult) -> dict:
        """Analyze Lean errors using structured parser."""
        messages = LeanParser.parse_messages(result.output)
        errors = [m for m in messages if m.is_error]
        if errors:
            structured = parse_error_structured(errors[0])
            return {
                "type": structured.error_type,
                "hash": structured.error_hash,
                "goal": structured.goal,
                "cascade_compatible": structured.is_cascade_compatible,
                "keywords": structured.suggestion_keywords,
            }
        return {"type": "unknown"}

    def _record_lean_experience(
        self, pattern_id: str, success_value: float
    ) -> None:
        """Record Lean verification result in MES memory."""
        if not self._memory:
            return

        record = ExperienceRecord(
            pattern_id=pattern_id,
            success_value=max(-1.0, min(1.0, success_value)),
        )
        self._memory.add_record(record)

        # Try to form E-concept
        self._memory.try_form_concept(pattern_id, CoRegulatorType.TACTICAL)

    # Diagnostico por tipo de error de Lean. Se usa DOS veces: como pista para
    # el usuario y —desde 2026-08-21— como realimentacion al generador.
    _LEAN_HINTS: dict[str, str] = {
        "unknown identifier": "posiblemente falta un `open` o un import de Mathlib.",
        "unknown constant": "ese nombre no existe en Mathlib; usa `exact?` o busca el lema real.",
        "type mismatch": "los tipos no coinciden; puede faltar una coerción o instancia.",
        "application type mismatch": "argumentos aplicados incorrectamente; revisa la aridad.",
        "failed to synthesize": "falta una instancia de typeclass (e.g., `Field ℝ`, `OrderedField`).",
        "function expected": "se usó algo como función que no lo es.",
        "tactic failed": "la táctica no cerró el goal; prueba `ring_nf` o `simp [*]` primero.",
        "unsolved goals": "la prueba no cierra todos los objetivos; faltan casos.",
    }

    # Errores que repair_imports puede arreglar solo: son de MODULO, no de
    # matematicas. El resto son semanticos y necesitan reformular la prueba.
    _ERRORES_MECANICOS = ("unknown identifier", "unknown constant", "unknown module")

    def _lean_hint(self, error: str) -> str:
        low = (error or "").lower()
        return next(
            (h for k, h in self._LEAN_HINTS.items() if k in low),
            "revisa la sintaxis Lean 4 y los imports de Mathlib.",
        )

    #: Una consulta de cada N intenta llenar un hueco. Cada intento cuesta una
    #: llamada al LLM mas una verificacion de Lean (~20 s), asi que no puede ir
    #: en todas: la respuesta del usuario ya se envio, pero el proceso sigue
    #: ocupado y la siguiente consulta esperaria.
    _CADA_CUANTAS_INTERACCIONES_LLENAR = 5

    async def _intentar_llenar_hueco(self) -> None:
        """
        Intenta convertir UN hueco conceptual en conocimiento verificado.

        Se ejecuta despues de responder, con el mismo criterio que la
        complexificacion: la consulta actual se resuelve sobre un grafo estable
        y los cambios benefician a las siguientes.

        Elige el hueco con mas co-conos: es donde mas cotas superiores hay sin
        una minima, o sea donde mas evidente resulta que falta el concepto.

        Nunca bloquea ni propaga: si el LLM no lo reconoce, si Lean lo rechaza o
        si el nodo no resulta ser el colimite, el hueco simplemente sigue
        abierto. Eso es un resultado honesto, no un error.
        """
        if not self._concept_gaps:
            return
        self._interacciones_desde_llenado = getattr(
            self, "_interacciones_desde_llenado", 0
        ) + 1
        if self._interacciones_desde_llenado < self._CADA_CUANTAS_INTERACCIONES_LLENAR:
            return
        self._interacciones_desde_llenado = 0

        # Sin LLM no hay concepto que proponer; no gastar el turno.
        if self._llm is None or self._llm.is_demo:
            return

        intentados = getattr(self, "_huecos_intentados", None)
        if intentados is None:
            intentados = self._huecos_intentados = set()

        pendientes = [
            g for g in self._concept_gaps
            if frozenset(g.component_ids) not in intentados
        ]
        if not pendientes:
            return

        gap = max(pendientes, key=lambda g: g.n_cocones)
        intentados.add(frozenset(gap.component_ids))

        try:
            res = await self.llenar_hueco_conceptual(gap)
        except Exception as e:
            logger.debug(f"_intentar_llenar_hueco: {type(e).__name__}: {e}")
            return

        if res.get("ok"):
            # El grafo cambio: el hueco dejo de serlo y puede haber colimites
            # nuevos. Se recalcula el orden de complejidad y se reparte.
            self._concept_gaps = [
                g for g in self._concept_gaps
                if frozenset(g.component_ids) != frozenset(gap.component_ids)
            ]
            try:
                from nucleo.graph.complexity import compute_complexity_order
                cn = compute_complexity_order(self._graph, self._colimit_builder)
                self._graph.apply_complexity_order(cn)
                self._cr_network.set_concept_gaps(self._concept_gaps)
            except Exception as e:
                logger.debug(f"recalculo de cn tras llenar hueco: {e}")
            logger.info(
                f"Hueco cerrado: {res['skill_id']} ('{res['nombre']}'), "
                f"quedan {len(self._concept_gaps)}"
            )
        else:
            logger.info(f"Hueco no cerrado: {res.get('motivo', '')}")

    def _log_motivo_demo(self, compuerta: str) -> None:
        """
        Registra POR QUE se entro en modo demo.

        Sin esto, una respuesta de demo con la clave puesta es indepurable: el
        usuario ve la plantilla y no hay forma de saber si fallo el proveedor,
        la clave, la variable de entorno o el paquete. Solo se registran
        LONGITUDES y nombres de clase — nunca el valor de la clave.
        """
        import os as _os
        try:
            cfg = self._llm.config
            env_name = self._llm._ENV_KEYS.get(cfg.provider, "")
            logger.warning(
                "MODO DEMO por '%s': provider=%s model=%s "
                "config.api_key_len=%d env[%s]_len=%d cliente=%s",
                compuerta,
                getattr(cfg.provider, "name", cfg.provider),
                cfg.model,
                len(cfg.api_key or ""),
                env_name or "-",
                len(_os.environ.get(env_name, "")) if env_name else 0,
                type(self._llm._get_client()).__name__,
            )
        except Exception as e:
            logger.warning("MODO DEMO por '%s' (diagnostico fallo: %s)", compuerta, e)

    #: Reglas de rol del traductor. Sin ellas el modelo respondia como un
    #: asistente suelto: "No tengo un compilador de Lean conectado en esta
    #: conversacion", "si quieres puedo mostrarte una prueba manual". Las dos
    #: frases son falsas y desmontan la arquitectura: Lean ESTA conectado, ya
    #: se ejecuto, y su veredicto es lo que se le pasa en Estado. El modelo no
    #: decide si algo esta verificado ni tiene un turno siguiente que ofrecer.
    _REGLAS_TRADUCTOR = (
        "REGLAS DE TU ROL (obligatorias):\n"
        "- Lean 4 con Mathlib YA SE EJECUTO sobre el codigo de abajo. El campo "
        "Estado es su veredicto real, no una suposicion.\n"
        "- NUNCA digas que no tienes Lean, que no puedes compilar o verificar "
        "en esta conversacion, ni que el codigo deberia tipar: ya se sabe si "
        "tipa, lo dice el Estado.\n"
        "- Si el Estado dice que Lean NO verifico, dilo con claridad y explica "
        "el porque a partir del error. No lo presentes como si estuviera bien.\n"
        "- No ofrezcas alternativas ni preguntes si el usuario quiere algo mas. "
        "Tu salida es la respuesta final.\n"
        "- No hables de ti ni de tus capacidades. Habla de las matematicas.\n\n"
    )

    async def _revisar_con_lean(
        self,
        lean_code: str,
        result: "LeanResult",
        formalize_prompt: str,
        lean_system: str,
        context: dict,
        max_rondas: int = 2,
    ) -> tuple[str, "LeanResult", int]:
        """
        Bucle de revision: realimenta el veredicto de Lean al generador.

        Este es el eslabon que faltaba respecto a un lazo generador-verificador
        clasico (Aletheia y similares): el sistema YA calculaba el diagnostico
        —tipo de error, mensaje de Lean, sugerencia de tactica— pero solo lo
        imprimia para el usuario. Nunca volvia al LLM, asi que un rechazo de
        Lean por `type mismatch` o `tactic failed` terminaba el intento.

        Triaje por severidad, sobre el VEREDICTO de Lean (no sobre una regex):

          SUCCESS / SORRY   -> no se toca (SORRY lo cubre SolverCascade)
          ERROR mecanico    -> ya lo intento repair_imports antes de llegar aqui
          ERROR semantico   -> REGENERAR con el error como contexto

        Solo se acepta la revision si MEJORA, con el mismo criterio que
        repair_imports: nunca se sustituye un resultado por otro peor.

        Args:
            max_rondas: cota dura. Cada ronda cuesta una llamada al LLM mas una
                verificacion de Lean (~20 s), asi que 2 es el limite util.

        Returns:
            (codigo, resultado, rondas_usadas) — el mejor par obtenido.
        """
        if result.status != LeanResultStatus.ERROR:
            return lean_code, result, 0

        mejor_code, mejor_res = lean_code, result

        for ronda in range(1, max_rondas + 1):
            errores = mejor_res.error_messages or []
            primero = (mejor_res.get_first_error() or "").strip()
            if not primero:
                break

            pista = self._lean_hint(primero)
            bloque_errores = "\n".join(f"  - {e.strip()[:300]}" for e in errores[:4])

            revise_prompt = (
                f"{formalize_prompt}\n\n"
                "─────────────────────────────────────────────\n"
                f"INTENTO {ronda}: Lean 4 RECHAZÓ tu código anterior.\n\n"
                "Código que enviaste:\n"
                f"```lean\n{mejor_code}\n```\n\n"
                "Errores exactos que devolvió Lean:\n"
                f"{bloque_errores}\n\n"
                f"Diagnóstico: {pista}\n\n"
                "Corrígelo. Instrucciones:\n"
                "- Arregla EXACTAMENTE los errores listados; no reescribas lo que ya funcionaba.\n"
                "- Si un lema no existe con ese nombre, usa otro de Mathlib o deja `sorry`.\n"
                "- `sorry` es preferible a un lema inventado: un `sorry` se detecta, "
                "un nombre falso hace fallar todo el archivo.\n"
                "- Devuelve SOLO el bloque Lean 4 corregido, completo y autocontenido."
            )

            try:
                gen = await self._llm.generate(
                    revise_prompt, system=lean_system, context=context
                )
            except Exception as e:
                logger.debug(f"_revisar_con_lean: fallo del LLM en ronda {ronda}: {e}")
                break

            code_n = self._extract_lean_code(gen.content) or gen.content.strip()
            if not code_n or code_n == mejor_code:
                break

            res_n = await self._lean.check_code(code_n)

            # Mismo criterio de mejora que repair_imports.
            mejora = (
                res_n.status in (LeanResultStatus.SUCCESS, LeanResultStatus.SORRY)
                or len(res_n.error_messages) < len(mejor_res.error_messages)
            )
            logger.info(
                f"_revisar_con_lean ronda {ronda}: "
                f"{mejor_res.status.name} -> {res_n.status.name} "
                f"({len(mejor_res.error_messages)} -> {len(res_n.error_messages)} errores), "
                f"{'aceptada' if mejora else 'descartada'}"
            )
            if not mejora:
                break

            mejor_code, mejor_res = code_n, res_n
            if mejor_res.status != LeanResultStatus.ERROR:
                return mejor_code, mejor_res, ronda

        rondas = 0 if mejor_res is result else max_rondas
        return mejor_code, mejor_res, rondas


    # =========================================================================
    # COMPLEXIFICACION QUE PRODUCE CONOCIMIENTO
    # =========================================================================

    async def llenar_hueco_conceptual(self, gap) -> dict:
        """
        Llena un hueco conceptual con un concepto matematico REAL.

        Un ConceptGap es un patron con co-conos pero sin co-cono limite: existen
        cotas superiores de las componentes pero ninguna es minimal, asi que el
        colimite no existe en G_n. Falta el concepto que las unifica.

        Ciclo (esto es lo que convierte la complexificacion en conocimiento en
        vez de topologia):

          1. El LLM PROPONE el concepto: nombre, definicion y su enunciado en
             Lean 4. No inventa un nodo "A + B" — nombra la matematica que
             realmente unifica las componentes.
          2. Lean VERIFICA que el concepto existe en Mathlib o que la definicion
             tipa. Si no verifica, no entra: el hueco sigue abierto, y eso es un
             resultado honesto.
          3. El nodo entra CON CONTENIDO (definicion + codigo Lean verificado) y
             con los morfismos DEPENDENCY del co-cono desde cada componente.
          4. Se RE-TESTEA el colimite con find_colimit. Si el nodo nuevo no
             resulta ser el co-cono limite, se REVIERTE: la propiedad universal
             es un test, y un nodo que no la cumple no se queda "por si acaso".

        Returns:
            dict con ok, motivo, skill_id, nombre, lean_code, lean_status.
        """
        from nucleo.graph.complexity import find_colimit
        from nucleo.llm.client import LLMClient as _LLMC, DemoLLMClient as _Demo
        from nucleo.types import Skill as _Skill, MorphismType as _MT
        import re

        comps = list(gap.component_ids)
        nombres = [
            (self._graph.get_skill(c).name if self._graph.get_skill(c) else c)
            for c in comps
        ]
        res = {
            "ok": False, "motivo": "", "skill_id": None, "nombre": None,
            "lean_code": None, "lean_status": None, "componentes": comps,
        }

        if self._llm is None or self._llm.is_demo or isinstance(
            self._llm._get_client(), _Demo
        ):
            res["motivo"] = "sin API key: el concepto lo debe proponer el LLM"
            return res

        # -- Paso 1: el LLM propone el concepto --------------------------------
        lineas = [
            "En un grafo de conocimiento matematico, estas areas forman un "
            "patron sin concepto unificador registrado:",
            "",
        ]
        lineas += [f"  - {n}" for n in nombres]
        lineas += [
            "",
            "Nombra la teoria matematica ESTABLECIDA que las unifica: la que un "
            "matematico reconoceria como el lugar donde estas areas convergen. "
            "Debe ser un area real y estandar, no un nombre inventado ni una "
            "yuxtaposicion de las anteriores.",
            "",
            "Responde EXACTAMENTE en este formato, sin nada mas:",
            "NOMBRE: <nombre del area>",
            "ID: <identificador-en-kebab-case>",
            "DEFINICION: <una frase: que estudia y por que unifica a las anteriores>",
            "LEAN:",
            "```lean",
            "<imports de Mathlib y un #check de una definicion central del area>",
            "```",
            "",
            "Si NO existe una teoria establecida que las unifique, responde "
            "unicamente: NINGUNA",
        ]
        prompt = "\n".join(lineas)

        try:
            gen = await self._llm.generate(prompt, system=_LLMC.LEAN_SYSTEM_PROMPT)
        except Exception as e:
            res["motivo"] = f"fallo del LLM: {e}"
            return res

        texto = gen.content.strip()
        if "NINGUNA" in texto[:40].upper():
            res["motivo"] = "el LLM no reconoce una teoria establecida que unifique"
            return res

        def _campo(clave: str) -> str:
            m = re.search(r"^" + clave + r":\s*(.+)$", texto, re.MULTILINE)
            return m.group(1).strip() if m else ""

        nombre = _campo("NOMBRE")
        sid = _campo("ID").lower().replace(" ", "-")
        definicion = _campo("DEFINICION")
        lean_code = self._extract_lean_code(texto)

        if not (nombre and sid and lean_code):
            res["motivo"] = "respuesta del LLM incompleta (falta NOMBRE/ID/LEAN)"
            return res
        if self._graph.get_skill(sid) is not None:
            res["motivo"] = f"el skill '{sid}' ya existe en el grafo"
            return res

        res["nombre"] = nombre
        res["lean_code"] = lean_code

        # -- Paso 2: Lean verifica --------------------------------------------
        try:
            lean_res = await self._lean.check_code(lean_code)
        except Exception as e:
            res["motivo"] = f"fallo al verificar con Lean: {e}"
            return res

        res["lean_status"] = lean_res.status.name
        if lean_res.status not in (
            LeanResultStatus.SUCCESS, LeanResultStatus.SORRY
        ):
            primer = (lean_res.get_first_error() or "")[:120]
            res["motivo"] = (
                f"Lean rechazo el concepto ({lean_res.status.name}): {primer}. "
                "El hueco sigue abierto."
            )
            return res

        # -- Paso 3: el nodo entra CON CONTENIDO ------------------------------
        try:
            pilar = self._dominant_pillar(comps)
        except Exception:
            pilar = None
        max_cn = max(
            (self._graph.get_skill(c).cn for c in comps if self._graph.get_skill(c)),
            default=0,
        )
        max_lv = max(
            (self._graph.get_skill(c).level for c in comps if self._graph.get_skill(c)),
            default=0,
        )

        nuevo = _Skill(
            id=sid,
            name=nombre,
            description=definicion or ("Concepto que unifica " + ", ".join(nombres)),
            pillar=pilar,
            level=max_lv,
            cn=max_cn + 1,
            pattern_ids=list(comps),
            content={"lean_code": lean_code, "lean_status": lean_res.status.name},
            metadata={
                "origen": "hueco_conceptual",
                "componentes": list(comps),
                "verificado_por_lean": True,
            },
        )
        self._graph.add_skill(nuevo)
        for c in comps:
            self._graph.add_morphism(
                c, sid, morphism_type=_MT.DEPENDENCY, weight=1.0,
                metadata={"is_cocone": True, "origen": "hueco_conceptual"},
            )

        # -- Paso 4: re-testear el colimite; si no lo es, revertir -------------
        apex = find_colimit(comps, self._graph, self._colimit_builder)
        if apex != sid:
            self._graph.remove_skill(sid)
            res["motivo"] = (
                f"'{nombre}' verifico en Lean pero NO resulta ser el co-cono "
                f"limite del patron (find_colimit dio {apex!r}). Revertido: la "
                "propiedad universal es un test, no una concesion."
            )
            return res

        res["ok"] = True
        res["skill_id"] = sid
        res["motivo"] = f"'{nombre}' verificado por Lean y confirmado como colimite"
        logger.info(
            f"Hueco llenado: {sorted(comps)} -> {sid} ('{nombre}'), "
            f"lean={lean_res.status.name}, cn={nuevo.cn}"
        )
        return res

    def _apply_structural_evolution(self) -> None:
        """Aplicar al grafo las opciones de los co-reguladores estructurales.

        Paper v7.0, Seccion 6.1: `Skill_{t+1} = Compl(Skill_t, Op_t)`.

        CR_org, CR_str y CR_int tienen como efector el GRAFO, no la respuesta
        (Def. 4.1: motor de reorganizacion, motor de complejificacion y sistema
        de reparacion de fracturas). Corren a su propia escala temporal, que
        `should_activate()` ya gobierna: CR_org cada k interacciones, CR_str
        cada K sesiones.

        Hasta ahora ejecutaban su ciclo en cada consulta y su Option se tiraba,
        porque `decide()` solo conserva el tipo de accion del ganador y
        `_reorganize_graph()` unicamente se invoca con la accion REORGANIZE,
        que en la practica no se elige nunca. Resultado: el grafo era
        `Skill_t -> Skill_t` y la complejificacion no ocurria jamas.

        CR_tac se excluye a proposito: su efector es la interfaz LLM<->Lean.
        """
        if not (self._evolution and self._cr_network):
            return
        resultados = getattr(self._cr_network, "_last_cycle_results", None) or []
        for cr_type, _accion, option in resultados:
            if cr_type == CoRegulatorType.TACTICAL:
                continue
            if not (option.bindings or option.absorptions or option.eliminations):
                continue
            try:
                antes = len(self._graph.skill_ids)
                self._evolution.apply_option(option)
                despues = len(self._graph.skill_ids)
                logger.info(
                    f"Complejificacion por {cr_type.name}: "
                    f"{antes} -> {despues} skills "
                    f"(ligaduras={len(option.bindings)}, "
                    f"absorciones={len(option.absorptions)}, "
                    f"eliminaciones={len(option.eliminations)})"
                )
            except Exception as exc:
                logger.warning(
                    f"Complejificacion de {cr_type.name} fallo: "
                    f"{type(exc).__name__}: {exc}"
                )

    def _reorganize_graph(self) -> None:
        """Reorganizar el grafo de skills via co-reguladores MES."""
        if self._cr_network and self._graph:
            cr_results = self._cr_network.step(self._graph)
            for cr_type, action_type, option in cr_results:
                if option.bindings or option.absorptions or option.eliminations:
                    if self._evolution:
                        self._evolution.apply_option(option)

    def _extract_lean_code(self, text: str) -> str:
        """Extraer codigo Lean del texto."""
        if "```lean" in text:
            start = text.find("```lean") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        return text

    def _evaluate_result(
        self,
        decision: GlobalDecision,
        response: NucleoResponse
    ) -> float:
        """
        Evaluar resultado de la accion (fase 4 del ciclo CR).

        Returns:
            Valor de exito en [-1, 1]
        """
        if decision.action_type == ActionType.RESPONSE:
            return 0.5 if len(response.content) > 50 else 0.1

        elif decision.action_type == ActionType.ASSIST:
            if response.lean_result and response.lean_result.is_success:
                return 1.0
            elif response.lean_result:
                return 0.3
            else:
                return 0.5

        elif decision.action_type == ActionType.REORGANIZE:
            return 0.2

        return 0.0

    def _record_experience(
        self,
        input_text: str,
        decision: GlobalDecision,
        success: float,
    ) -> None:
        """
        Registrar experiencia en memoria MES (Teorema 9.9).

        Enriquecimiento monotono: la memoria solo crece.
        Also feeds live PPO update if neural_agent is set.
        """
        if not self._memory:
            return

        record = ExperienceRecord(
            pattern_id=f"query-{decision.source_cr.name.lower()}",
            success_value=max(-1.0, min(1.0, success)),
        )
        self._memory.add_record(record)

        # Guardar ID del último registro para retroactive feedback
        self._last_experience_id = record.id
        self._last_action_type   = decision.action_type

        # Intentar formar E-concepto
        self._memory.try_form_concept(
            record.pattern_id, decision.source_cr
        )

        # Aprender procedimiento si fue exitoso
        if success > 0.3:
            self._memory.learn_procedure(
                record.pattern_id,
                [decision.action_type.name],
                success=(success > 0.5),
                query_text=input_text,
            )

        # Live PPO update: feed real interaction to neural agent
        if self._neural_agent is not None:
            try:
                from nucleo.rl.mdp import Transition
                state = State(lean_goal=input_text)
                action = Action(action_type=decision.action_type)
                transition = Transition(
                    state=state,
                    action=action,
                    reward=success,
                    next_state=State(),
                )
                self._neural_agent.update([transition])
                self._live_learning_steps += 1

                # Persistir a disco solo si se activa explicitamente
                # (config.live_learning_autosave). Por defecto el aprendizaje
                # online queda solo en memoria de la sesion, para no
                # sobreescribir el checkpoint validado con drift acumulado.
                if (
                    self.config.live_learning_autosave
                    and self._live_learning_steps % 10 == 0
                ):
                    self._save_neural_weights()
            except Exception as e:
                logger.warning(f"Live PPO update failed: {e}")

        # Persistir memoria periodicamente (cada 20 interacciones)
        if len(self._state.history) % 20 == 0:
            self._save_memory()

    def _save_neural_weights(self) -> None:
        """Save neural agent weights to disk."""
        if self._neural_agent is None or not self._neural_agent.has_network:
            return
        try:
            weights_path = str(self.config.data_dir / "neural_agent.json")
            self._neural_agent.save(weights_path)
            logger.info(f"Neural weights saved ({self._live_learning_steps} steps)")
        except Exception as e:
            logger.warning(f"Failed to save neural weights: {e}")

    def report_lean_result(
        self,
        query: str,
        tactic: str,
        lean_result: str,
        reward: float,
    ) -> None:
        """Reporta el resultado de Lean al sistema multi-agente (MES Bridge).

        Debe llamarse tras cada verificación Lean para que los agentes
        aprendan de las soluciones exitosas y detecten convergencias.

        Args:
            query:       Texto del problema
            tactic:      Táctica Lean usada
            lean_result: "success" | "partial" | "failed"
            reward:      Recompensa (0.0 - 1.0)
        """
        if self._multi_agent_orchestrator is None:
            return
        try:
            self._multi_agent_orchestrator.record_solution(
                query=query,
                tactic=tactic,
                lean_result=lean_result,
                reward=reward,
            )
        except Exception as e:
            logger.debug(f"report_lean_result error: {e}")

    def set_multi_agent_orchestrator(self, orchestrator=None) -> None:
        """
        Conecta el MultiAgentOrchestrator al Nucleo.

        Cuando está activo, las consultas matemáticas se enrutan al agente
        especializado de su categoría (algebra, geometry, etc.) en vez de
        usar el agente monolítico global.

        Args:
            orchestrator: instancia de MultiAgentOrchestrator,
                          o None para crear uno por defecto.
        """
        if orchestrator is None:
            try:
                from nucleo.multi_agent import MultiAgentOrchestrator
                # MultiAgentOrchestrator por defecto busca pesos en
                # <repo>/data/agents (vacio); los 14 pesos reales entrenados
                # por scripts/train_multiagent.py viven en
                # <repo>/training/agents/best/{categoria}.pt — hay que
                # apuntar ahi explicitamente o cada agente "especializado"
                # cae en silencio al checkpoint global colapsado.
                _weights_dir = Path(__file__).parent.parent / "training" / "agents" / "best"
                orchestrator = MultiAgentOrchestrator(
                    weights_dir=_weights_dir if _weights_dir.exists() else None,
                    lazy=True,
                    pattern_manager=self._pattern_manager,
                    colimit_builder=self._colimit_builder,
                    skill_graph=self._graph,
                )
            except ImportError:
                logger.warning("MultiAgentOrchestrator no disponible")
                return
        else:
            # Inyectar MES del Nucleo en el bridge existente
            if hasattr(orchestrator, "mes_bridge") and orchestrator.mes_bridge is not None:
                orchestrator.mes_bridge.pattern_manager = self._pattern_manager
                orchestrator.mes_bridge.colimit_builder = self._colimit_builder
                orchestrator.mes_bridge.skill_graph = self._graph

        self._multi_agent_orchestrator = orchestrator
        orchestrator._nucleo = self
        logger.info("MultiAgentOrchestrator integrado con Nucleo (MES Bridge conectado)")

    def get_specialized_agent(self, query: str):
        """Retorna el agente especializado para la categoría de query, o None."""
        if self._multi_agent_orchestrator is None:
            return None, None
        try:
            category, agent = self._multi_agent_orchestrator.route(query)
            return category, agent
        except Exception as e:
            logger.warning(f"Error al enrutar query: {e}")
            return None, None

    def set_neural_agent(self, agent) -> None:
        """
        Set neural agent for live PPO learning.

        When set, each interaction feeds a PPO update so the agent
        learns from real chat rewards. Also wires the GNNTacticRanker
        into the SolverCascade so tactic ordering uses learned embeddings
        (CoRegulatorNetwork.lean §VI.5, cascade_gnn_iff_exists).
        """
        self._neural_agent = agent
        if (
            agent is not None
            and getattr(agent, "has_network", False)
            and self._solver_cascade is not None
            and self._graph is not None
        ):
            try:
                from nucleo.lean.solver_cascade import GNNTacticRanker
                ranker = GNNTacticRanker(agent.network, self._graph)
                self._solver_cascade.set_gnn_ranker(ranker)
                logger.info("GNNTacticRanker wired into SolverCascade")
                # Rankeador entrenado sobre LeanWorkbook: tiene prioridad.
                from nucleo.lean.solver_cascade import TacticRanker
                _tr = TacticRanker()
                if _tr.disponible:
                    self._solver_cascade.set_tactic_ranker(_tr)
                    logger.info("TacticRanker entrenado conectado (top-3 88.1%)")
            except Exception as _exc:
                logger.warning("GNNTacticRanker setup failed: %s", _exc)

    # ------------------------------------------------------------------
    # Consultores Avanzados
    # ------------------------------------------------------------------

    def set_consultores_mode(self, n_candidates: int = 3) -> None:
        """
        Activar el módulo Consultores Avanzados.

        Reutiliza los mismos LLMClient, LeanClient, PatternManager y
        MESMemory ya instanciados. Requiere que initialize() haya sido
        llamado previamente.

        Args:
            n_candidates: Número de candidatos a generar (mínimo 1).
        """
        if not self._initialized:
            raise RuntimeError(
                "Nucleo no inicializado — llama initialize() primero."
            )
        from nucleo.consultores.orchestrator import ConsultoresModule
        self._consultores = ConsultoresModule(
            llm_client=self._llm,
            lean_client=self._lean,
            pattern_manager=self._pattern_manager,
            memory=self._memory,
            n_candidates=max(1, n_candidates),
        )
        logger.info(
            "Consultores Avanzados activado (n_candidates=%d)", n_candidates
        )

    def disable_consultores_mode(self) -> None:
        """Desactivar el módulo Consultores Avanzados."""
        self._consultores = None
        logger.info("Consultores Avanzados desactivado")

    @property
    def consultores_active(self) -> bool:
        """True si el módulo Consultores Avanzados está activo."""
        return self._consultores is not None

    def reconfigure_llm(
        self,
        provider: str,
        model: str,
        api_key: str,
        max_tokens: int = 1024,
    ) -> None:
        """
        Cambiar proveedor LLM en caliente.

        Llamado desde Streamlit antes de cada process_sync() para usar
        el proveedor/modelo/key seleccionados por el usuario en la UI.
        """
        from nucleo.llm.client import LLMProvider, LLMConfig
        try:
            prov = LLMProvider(provider)
        except ValueError:
            prov = LLMProvider.DEMO

        if self._llm is not None:
            self._llm.reconfigure(prov, model, api_key, max_tokens)
        else:
            self._llm = LLMClient(LLMConfig(
                provider=prov,
                model=model,
                api_key=api_key,
                max_tokens=max_tokens,
            ))

    def sync_conversation(self, history: list) -> None:
        """
        Sincronizar la conversacion interna del LLM con el historial de Streamlit.

        Llamado desde app.py antes de process_sync() para que el LLM tenga
        el contexto correcto de la sesion actual. Solo conserva los ultimos
        N turnos para evitar exceder limites de tokens.

        Args:
            history: Lista de items {"q": str, "a": str} ordenados del mas reciente
                     al mas antiguo (como en session_state.history).
        """
        if self._llm is None:
            return
        from nucleo.llm.client import LLMMessage, LLMRole
        # Tomar los ultimos 5 turnos (10 mensajes: 5 user + 5 assistant)
        recent = list(reversed(history))[-5:]
        self._llm._conversation.clear()
        for item in recent:
            self._llm._conversation.append(LLMMessage(LLMRole.USER, item["q"]))
            self._llm._conversation.append(LLMMessage(LLMRole.ASSISTANT, item["a"]))

    def apply_feedback(self, score: float) -> None:
        """
        Aplicar feedback explícito del usuario a la última interacción.

        score > 0  →  respuesta fue útil (👍)
        score < 0  →  respuesta no fue útil (👎)

        Actualiza el registro en MESMemory y lanza un PPO update adicional
        con la recompensa real.
        """
        if not self._memory or not self._last_experience_id:
            return

        score = max(-1.0, min(1.0, score))

        # Actualizar registro en memoria
        record = self._memory.get_record(self._last_experience_id)
        if record:
            record.success_value = score
            logger.info(
                f"Feedback aplicado al registro {self._last_experience_id}: {score:+.1f}"
            )

        # PPO update con recompensa real
        if self._neural_agent is not None and self._last_action_type is not None:
            try:
                from nucleo.rl.mdp import Transition
                from nucleo.types import State, Action
                t = Transition(
                    state=State(),
                    action=Action(action_type=self._last_action_type),
                    reward=score,
                    next_state=State(),
                )
                self._neural_agent.update([t])
                logger.info("PPO update con feedback del usuario")
            except Exception as e:
                logger.warning(f"Feedback PPO update falló: {e}")

    def evaluate_answer(
        self,
        prediction: str,
        reference: str,
        extract_answers: bool = True,
    ) -> EvaluationResult:
        """
        Verificar si una respuesta matematica es correcta.

        Usa MathEvaluator: extrae \\boxed{}, compara numerico/simbolico.

        Args:
            prediction: Respuesta generada (puede contener \\boxed{...})
            reference:  Respuesta de referencia
            extract_answers: Si extraer la respuesta del texto completo

        Returns:
            EvaluationResult con is_correct, match_type y detalles
        """
        return self._evaluator.evaluate(prediction, reference, extract_answers)

    def process_sync(self, input_text: str) -> "NucleoResponse":
        """
        Wrapper síncrono de process() para uso en Streamlit.

        Siempre crea un thread separado con su propio event loop para
        evitar conflictos con el loop de Tornado/Streamlit que ya corre
        en el hilo principal.
        """
        import asyncio
        import concurrent.futures

        def _run_in_thread() -> "NucleoResponse":
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.process(input_text))
            finally:
                loop.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_run_in_thread)
            return future.result(timeout=420)  # 7 min: Lean cold-start puede tardar ~100s

    # =========================================================================
    # PROPIEDADES
    # =========================================================================

    @property
    def concept_gaps(self) -> list:
        """
        Patrones con co-conos pero sin co-cono limite.

        Cada uno señala un lugar del grafo de conocimiento donde existen
        cotas superiores de un patron pero ninguna es minimal: falta el
        concepto que unifica las componentes, o falta una arista de orden
        en la base estructural.

        NO son errores. Son el disparador legitimo de complexificacion:
        el concepto que llena el hueco debe aportarlo la matematica
        (el LLM lo propone, Lean lo verifica), no la cirugia sobre el grafo.
        """
        return list(self._concept_gaps)

    @property
    def graph(self) -> SkillCategory:
        """Grafo de skills."""
        if not self._graph:
            raise RuntimeError("Nucleo no inicializado")
        return self._graph

    @property
    def cr_network(self) -> CoRegulatorNetwork:
        """Red de co-reguladores (Dinamica Global)."""
        if not self._cr_network:
            raise RuntimeError("Nucleo no inicializado")
        return self._cr_network

    @property
    def stats(self) -> dict[str, Any]:
        """Estadisticas del sistema."""
        result = {
            "initialized": self._initialized,
            "mode": self._mode.name,
            "num_skills": self._graph.stats["num_skills"] if self._graph else 0,
            "num_interactions": len(self._state.history),
        }
        # Jerarquia: taxonomia curada (level) vs construccion emergente (cn).
        # max_cn = 0 y num_joins = 0 significa que el sistema aun no ha
        # construido ningun concepto propio — es la metrica honesta del
        # motor de complejificacion, no un error.
        if self._graph:
            result["hierarchy"] = {
                "max_level": self._graph.stats.get("max_level", 0),
                "max_cn": self._graph.stats.get("max_cn", 0),
                "num_joins": self._graph.stats.get("num_joins", 0),
                "level_distribution": self._graph.get_level_distribution(),
                "cn_distribution": self._graph.get_cn_distribution(),
                "concept_gaps": len(self._concept_gaps),
            }
        # Dinamica Global stats (v7.0)
        if self._cr_network:
            result["co_regulators"] = self._cr_network.stats
        if self._memory:
            result["memory"] = self._memory.stats
        if self._evolution:
            result["evolution"] = self._evolution.stats
        if self._last_decision:
            result["last_decision"] = {
                "action": self._last_decision.action_type.name,
                "source_cr": self._last_decision.source_cr.name,
                "confidence": self._last_decision.confidence,
            }
        return result

    # =========================================================================
    # GRAPH-AWARE CONTEXT (Hierarchy → Reasoning connection)
    # =========================================================================

    def _find_relevant_context(
        self, query: str, graph: SkillCategory
    ) -> dict:
        """
        Find graph-relevant context for a query.

        Traverses the skill graph to find:
        1. Skills matching the query (by keyword overlap)
        2. Their dependency chain (prerequisites)
        3. Connected tactic/strategy skills
        4. Dominant pillar

        This replaces the naive `skill_ids[:10]` approach with
        structurally-informed context that helps the LLM reason better.
        """
        matched = self._match_skills_to_query(query, graph)

        deps: list[str] = []
        tactics: list[str] = []
        strategies: list[str] = []

        for sid in matched:
            # Traverse dependency chain
            for dep_id in graph.dependencies(sid):
                if dep_id not in deps:
                    deps.append(dep_id)

            # Find connected tactic and strategy skills
            for nbr_id in graph.neighbors(sid):
                if nbr_id.startswith("tactic-") and nbr_id not in tactics:
                    tactics.append(nbr_id)
                elif nbr_id.startswith("strategy-") and nbr_id not in strategies:
                    strategies.append(nbr_id)

        # Segundo salto: las estrategias dependen de tacticas, no de dominios,
        # asi que se alcanzan a traves de la tactica en vez de inventar aristas
        # dominio->estrategia que no estarian justificadas.
        for tid in tactics:
            for nbr_id in graph.neighbors(tid):
                if nbr_id.startswith("strategy-") and nbr_id not in strategies:
                    strategies.append(nbr_id)

        # ── Competencias emergentes ──────────────────────────────────────
        # Si una skill que casa con la consulta pertenece a un colimite, ese
        # colimite es el objeto por el que factoriza toda accion colectiva del
        # patron (Def. 2.2). Alcanzarlo cuesta un salto —el co-cono va de cada
        # componente al colimite— y desde el se recuperan los demas
        # componentes, que la consulta no habia nombrado.
        #
        # Aqui es donde la complejificacion deja de ser andamiaje: el sistema
        # recuerda que esos skills resuelven problemas juntos y los aporta
        # aunque el usuario solo haya mencionado uno.
        competencias: list[str] = []
        hermanos: list[str] = []
        for sid in matched:
            for nbr_id in graph.neighbors(sid):
                nbr = graph.get_skill(nbr_id)
                meta = (nbr.metadata or {}) if nbr else {}
                if not meta.get("emergent"):
                    continue
                if nbr.name not in competencias:
                    competencias.append(nbr.name)
                for comp in meta.get("components", []):
                    if comp not in matched and comp not in hermanos:
                        hermanos.append(comp)

        pillar = self._dominant_pillar(matched, graph)

        # Alimentar el paisaje de uso de CR_org: estos son los skills que han
        # trabajado juntos en esta consulta. Cuando un grupo se repite, CR_org
        # lo liga en un colimite (Def. 4.1 + Seccion 6.2).
        # getattr: `_find_relevant_context` se invoca tambien sobre instancias
        # construidas a medias (los tests de jerarquia lo hacen), donde el
        # atributo aun no existe.
        _red = getattr(self, "_cr_network", None)
        if _red is not None and matched:
            try:
                _red.record_activation(matched[:6])
            except Exception as exc:
                logger.debug(f"record_activation fallo: {exc}")

        ctx = {
            "relevant_skills": matched[:5],
            "prerequisites": deps[:5],
            "suggested_tactics": tactics,
            "proof_strategies": strategies,
            "pillar": pillar,
        }
        # Solo se anaden si existen: un bloque vacio en el prompt es ruido.
        if competencias:
            ctx["competencia_emergente"] = competencias[:2]
        if hermanos:
            ctx["skills_que_suelen_acompanar"] = hermanos[:5]

        formal_note = self._formal_pillar_note(matched)
        if formal_note:
            ctx["formal_definitions"] = formal_note

        # NOMBRES DE MATHLIB VERIFICADOS.
        #
        # Medido: de 28 nombres de Mathlib que el modelo propuso de memoria,
        # 21 NO EXISTEN — `tsum_geometric_two`, `Subgroup.isCyclic`,
        # `isOpen_union` siguen la convencion al dedillo y no estan. El
        # vocabulario del grafo acierta el 95%, y no de memoria: cada nombre
        # esta comprobado con `#check` contra Mathlib entero
        # (`scripts/verificar_vocabulario_grafo.py`).
        #
        # Darselos al modelo es sustituir RECUERDO por CONSULTA en lo unico
        # donde el recuerdo falla tres de cada cuatro veces.
        nombres = self._nombres_mathlib(matched)
        if nombres:
            ctx["mathlib_verificado"] = nombres

        return ctx

    #: Nombres que NO se ofrecen: namespaces y conceptos que esta version de
    #: Mathlib no tiene. Ofrecerlos seria reintroducir el problema que se
    #: viene a resolver.
    _MATHLIB_INVALIDOS = frozenset({
        "EuclideanGeometry", "Ideal.Quotient", "QuotientGroup",
        "RelCWComplex", "Turing.TM0", "Turing.TM1",
    })

    _MODULOS_CACHE = None

    def _modulos_mathlib(self, context) -> list:
        """Modulos de Mathlib para las skills activadas en esta consulta."""
        if not isinstance(context, dict):
            return []
        skills = context.get("relevant_skills") or []
        if not skills:
            return []
        if Nucleo._MODULOS_CACHE is None:
            # RUTA RELATIVA Y AVISO RUIDOSO.
            #
            # Esto era una ruta absoluta a E:/Metamatematico dentro de un
            # `try` cuyo `except` dejaba el cache en `{}` — que no es `None`,
            # asi que no se reintentaba nunca, y encima es atributo de clase.
            # El proyecto ya se movio una vez de sitio: si vuelve a pasar, el
            # grafo deja de elegir los modulos que importa Lean —uno de los
            # dos unicos puntos donde actua en caliente— y el unico rastro era
            # un `logger.debug`. Un fallo de infraestructura presentado como
            # funcionamiento normal, que es justo lo que este sistema existe
            # para no hacer.
            import json as _j
            from nucleo.rutas import dato as _dato
            ruta = _dato("mathlib_modulos.json")
            try:
                with open(ruta, encoding="utf-8") as _f:
                    Nucleo._MODULOS_CACHE = _j.load(_f)["por_skill"]
                logger.debug("mapa de modulos: %d skills",
                             len(Nucleo._MODULOS_CACHE))
            except Exception as _e:
                Nucleo._MODULOS_CACHE = {}
                logger.warning(
                    "SIN MAPA DE MODULOS (%s): %s. El grafo no podra elegir "
                    "que importa Lean y se usaran los imports genericos. "
                    "Regenerar con: python -m scripts.mapa_modulos_mathlib",
                    type(_e).__name__, ruta)
        fuera = []
        for s in skills[:4]:
            for m in Nucleo._MODULOS_CACHE.get(s, [])[:2]:
                if m not in fuera:
                    fuera.append(m)
        return fuera[:6]

    def _nombres_mathlib(self, skills: list[str]) -> dict[str, str]:
        """Los nombres Mathlib comprobados de estas skills.

        Solo salen los que `verificar_vocabulario_grafo.py` dio por buenos: si
        un nombre no existe en la version instalada, callarse es mejor que
        ofrecerlo — el modelo ya inventa suficientes por su cuenta.
        """
        try:
            from nucleo.graph.interpretacion import nombres_de_trabajo
        except Exception:
            return {}
        fuera: dict[str, str] = {}
        # LOS QUE NO APORTAN NOMBRES NO GASTAN CUPO.
        #
        # Antes se cogian las seis primeras skills y punto. Con los nodos de
        # cobertura en el grafo eso salia caro: ganan sitio en el top-k del
        # emparejador y hoy no inyectan nada —sus nombres estan deducidos, no
        # comprobados con `#check`— asi que ocupaban una de las seis plazas y
        # la dejaban vacia. Medido contra ProofNet: la cobertura caia de 14,2 %
        # a 12,6 % solo por eso.
        #
        # Ahora se recorren en orden y se llenan seis plazas CON NOMBRES.
        for s in skills:
            if len(fuera) >= 6:
                break
            # LA TEORIA, NO LA CATEGORIA.
            #
            # `Etiqueta.lean` dice que ES el nodo: para group-theory, la
            # categoria `GrpCat`. Ofrecerle eso al modelo ante «demuestra que
            # un grupo de orden primo es ciclico» es darle el vocabulario
            # equivocado — necesita `Subgroup` y `MonoidHom`, no la categoria
            # de todos los grupos. `nombres_de_trabajo` devuelve `teoria`
            # cuando las dos divergen, y `lean` cuando coinciden.
            nombres = nombres_de_trabajo(s)
            if not nombres:
                continue
            piezas = [p.strip() for p in nombres.replace("+", ",").split(",")
                      if p.strip() and p.strip() not in self._MATHLIB_INVALIDOS]
            if piezas:
                fuera[s] = ", ".join(piezas[:3])
        return fuera

    def _formal_pillar_note(self, matched_skill_ids: list[str]) -> Optional[str]:
        """
        Enriquecimiento con las formulas exactas de los 4 pilares formales
        (nucleo/pillars/{set_theory,category_theory,logic,type_theory}.py).
        Esas clases existian pero nada las consultaba: el grafo real usa
        Skill.description (texto libre), nunca las formulas/traductores que
        SI tienen SetTheoryPillar.describe_axiom, CurryHoward, etc. Aqui se
        ancla el prompt del LLM a la formula literal cuando la consulta toca
        una de esas skills, en vez de dejar que el LLM la recuerde de memoria.

        Devuelve None si ninguna skill emparejada tiene una nota formal
        conocida (caso comun) — no se inventa contenido para el resto.
        """
        if "zfc-axioms" not in matched_skill_ids:
            return None
        try:
            if self._set_theory_pillar is None:
                from nucleo.pillars.set_theory import SetTheoryPillar
                self._set_theory_pillar = SetTheoryPillar()
            from nucleo.pillars.set_theory import ZFCAxiom
            lines = [
                f"- {axiom.name}: {self._set_theory_pillar.describe_axiom(axiom)}"
                for axiom in ZFCAxiom
            ]
            return "Axiomas de ZFC (formula de primer orden exacta):\n" + "\n".join(lines)
        except Exception as e:
            logger.debug(f"_formal_pillar_note error (no bloqueante): {e}")
            return None

    def _match_skills_to_query(
        self, query: str, graph: SkillCategory
    ) -> list[str]:
        """
        Match skills in the graph to a query by keyword overlap.

        Tokenizes the query and compares against skill IDs and names.
        Returns skill IDs sorted by match relevance (most tokens matched first).
        """
        import re as _re_kw

        # Tokenize query: lowercase, split on whitespace and punctuation
        query_lower = query.lower()
        query_tokens = set(
            t for t in query_lower.replace("-", " ").replace("_", " ").split()
            if len(t) > 2  # Skip very short tokens
        )

        if not query_tokens:
            return []

        scored: list[tuple[str, int]] = []
        for skill_id in graph.skill_ids:
            skill = graph.get_skill(skill_id)
            if not skill:
                continue

            # Tokens from skill ID and name
            skill_tokens = set(
                skill_id.lower().replace("-", " ").split()
                + skill.name.lower().replace("-", " ").split()
            )

            overlap = len(query_tokens & skill_tokens)

            # Terminos declarados en la skill (ES + EN). Sin esto, los IDs y
            # nombres en ingles hacen que ninguna consulta en español case, y
            # todo acaba cayendo al mapa de palabras clave de get_viz_data().
            # Se comparan como frase completa delimitada por limites de
            # palabra, para no repetir el fallo de "prime" dentro de "primer".
            for kw in (skill.metadata or {}).get("keywords", []) or []:
                kw = kw.lower().strip()
                if not kw:
                    continue
                if " " in kw:
                    if _re_kw.search(rf"\b{_re_kw.escape(kw)}\b", query_lower):
                        overlap += 2   # una frase acierta mas que un token
                elif kw in query_tokens:
                    overlap += 2

            if overlap > 0:
                scored.append((skill_id, overlap))

        # Sort by overlap descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return [sid for sid, _ in scored[:10]]

    def _dominant_pillar(
        self, skill_ids: list[str], graph: SkillCategory
    ) -> str:
        """Determine the dominant pillar from a set of matched skills."""
        if not skill_ids:
            return "TYPE"  # Default to TYPE for Lean-related queries

        pillar_counts: dict[str, int] = {}
        for sid in skill_ids:
            skill = graph.get_skill(sid)
            if skill:
                p = skill.pillar.name
                pillar_counts[p] = pillar_counts.get(p, 0) + 1

        if not pillar_counts:
            return "TYPE"

        return max(pillar_counts, key=pillar_counts.get)


    def get_viz_data(self, query: str) -> dict:
        """
        Compute visualization data for the given query.

        Called by app.py after process_sync() to populate session_state["viz_data"]
        so that pages/1_Visualizaciones.py uses real graph/embedding/MES data
        instead of its hardcoded mock.
        """
        if not self._initialized or not self._graph:
            return {}

        import numpy as np
        from collections import Counter
        from nucleo.graph.embeddings import SkillEmbeddingModel

        graph = self._graph

        # 1. Graph nodes
        graph_nodes: list[dict] = []
        for node_data in graph._skills.values():
            skill = node_data.skill
            graph_nodes.append({
                "id":         skill.id,
                "name":       skill.name,
                "level":      skill.level,
                "pillar":     skill.pillar.name if skill.pillar else "SET",
                "category":   skill.metadata.get("category") or {"SET": "foundations", "CAT": "category-theory", "LOG": "logic", "TYPE": "foundations"}.get(skill.pillar.name if skill.pillar else "SET", "foundations"),
                "in_degree":  node_data.in_degree,
                "out_degree": node_data.out_degree,
            })

        # 2. Graph edges (skip identity loops)
        graph_edges: list[dict] = []
        for mor in graph.morphisms:
            if mor.morphism_type != MorphismType.IDENTITY and mor.source_id != mor.target_id:
                graph_edges.append({
                    "source":        mor.source_id,
                    "target":        mor.target_id,
                    "morphism_type": mor.morphism_type.name,
                })

        # 3. Matched / dependency / tactic sets
        matched = self._match_skills_to_query(query, graph)

        # Keyword fallback for multilingual queries (Spanish/English)
        if not matched:
            _VIZ_KW = {
                "irracional":   ["real-analysis", "elementary-number-theory", "zfc-axioms", "strategy-contradiction"],
                "raiz":         ["real-analysis", "elementary-number-theory"],
                "raíz":         ["real-analysis", "elementary-number-theory"],
                "primo":        ["elementary-number-theory", "algebraic-number-theory"],
                "prime":        ["elementary-number-theory", "algebraic-number-theory"],
                "grupo":        ["group-theory", "cat-basics"],
                "group":        ["group-theory", "cat-basics"],
                "anillo":       ["ring-theory"],
                "ring":         ["ring-theory"],
                "campo":        ["field-theory"],
                "field":        ["field-theory"],
                "modulo":       ["module-theory"],
                "módulo":       ["module-theory"],
                "module":       ["module-theory"],
                "yoneda":       ["cat-basics", "functors", "nat-trans", "limits"],
                "funtor":       ["functors", "cat-basics"],
                "functor":      ["functors", "cat-basics"],
                "categor":      ["cat-basics"],
                "colimite":     ["limits", "cat-basics", "functors"],
                "colimit":      ["limits", "cat-basics"],
                "límite":       ["limits"],
                "colímite":     ["limits", "cat-basics", "functors"],
                "limit":        ["limits"],
                "lean":         ["lean-kernel"],
                "simp":         ["lean-kernel"],
                "omega":        ["lean-kernel"],
                "exact":        ["lean-kernel"],
                "apply":        ["lean-kernel"],
                "induccion":    ["strategy-inductive", "lean-kernel"],
                "inducción":    ["strategy-inductive", "lean-kernel"],
                "induction":    ["strategy-inductive", "lean-kernel"],
                "curry":        ["cic", "proof-theory"],
                "howard":       ["cic", "proof-theory"],
                "tipos":        ["cic"],
                "type":         ["cic"],
                "hott":         ["homotopy-type-theory", "homotopy-theory"],
                "homotop":      ["homotopy-theory", "algebraic-topology"],
                "diferencial":  ["differential-geometry", "real-analysis"],
                "integral":     ["real-analysis", "complex-analysis"],
                "analisis":     ["real-analysis"],
                "análisis":     ["real-analysis"],
                "analysis":     ["real-analysis"],
                "topolog":      ["point-set-topology", "algebraic-topology"],
                "probabilidad": ["probability-theory"],
                "probability":  ["probability-theory"],
                "combinatoria": ["enumerative-combinatorics", "graph-theory"],
                "grafo":        ["graph-theory"],
                "graph":        ["graph-theory"],
                "demostr":      ["strategy-forward", "proof-theory"],
                "proof":        ["strategy-forward", "proof-theory"],
                "prueba":       ["strategy-forward", "proof-theory"],
                "contradiccion":["strategy-contradiction"],
                "contradicción":["strategy-contradiction"],
                "nat":          ["lean-kernel", "strategy-inductive"],
                "succ":         ["strategy-inductive", "lean-kernel"],
                "formal":       ["formal-verification", "lean-kernel"],
                "theorem":      ["proof-theory", "lean-kernel"],
                "lemma":        ["lean-kernel", "proof-theory"],
                "fol":          ["fol-deduction"],
                "logica":       ["fol-deduction", "model-theory"],
                "lógica":       ["fol-deduction", "model-theory"],
                "homolog":      ["homological-algebra", "algebraic-topology"],
                "geometria":    ["euclidean-geometry", "differential-geometry"],
                "geometry":     ["euclidean-geometry"],
                "algebr":       ["group-theory", "ring-theory", "field-theory"],
                # Teoria de grupos / homomorfismos
                "homomorf":     ["group-theory", "ring-theory"],
                "homomorph":    ["group-theory", "ring-theory"],
                "isomorf":      ["group-theory", "cat-basics"],
                "isomorph":     ["group-theory", "cat-basics"],
                "cociente":     ["group-theory"],
                "quotient":     ["group-theory"],
                "nucleo":       ["group-theory"],
                "núcleo":       ["group-theory"],
                "kernel":       ["group-theory"],
                # Aritmetica / factorizacion
                "aritmetica":   ["elementary-number-theory"],
                "aritmética":   ["elementary-number-theory"],
                "arithmetic":   ["elementary-number-theory"],
                "factoriz":     ["elementary-number-theory", "ring-theory"],
                "divisib":      ["elementary-number-theory"],
            }
            # Claves que son prefijos deliberados (deben casar "topolog" dentro
            # de "topologia"/"topological"). El resto se compara como palabra
            # completa: con subcadena cruda, "prime" casaba dentro de "primer"
            # y "el primer teorema de homomorfismo" acababa en teoria de numeros.
            _VIZ_STEMS = {
                "homolog", "topolog", "algebr", "demostr", "homotop",
                "categor", "homomorf", "homomorph", "isomorf", "isomorph",
                "factoriz", "divisib", "geometr",
            }
            import re as _re
            q_lower = query.lower()
            m_set: set[str] = set()
            for kw, sids in _VIZ_KW.items():
                patron = rf"\b{_re.escape(kw)}" if kw in _VIZ_STEMS else rf"\b{_re.escape(kw)}\b"
                if _re.search(patron, q_lower):
                    m_set.update(s for s in sids if graph.get_skill(s))
            if not m_set:
                m_set = {s for s in ["zfc-axioms", "fol-deduction", "strategy-contradiction", "proof-theory"]
                         if graph.get_skill(s)}
            matched = list(m_set)

        TACTIC_CATS = {"lean-tactics", "proof-strategies"}
        dep_skills: set[str] = set()
        tactic_skills: set[str] = set()

        # Separate matched skills into tactics vs regular
        matched_regular = []
        for sid in matched:
            sk = graph.get_skill(sid)
            if sk:
                cat = sk.metadata.get("category", "")
                if (cat in TACTIC_CATS or sid.startswith("tactic-")
                        or sid.startswith("strategy-")):
                    tactic_skills.add(sid)
                else:
                    matched_regular.append(sid)
            else:
                matched_regular.append(sid)
        matched = matched_regular  # Only keep non-tactic skills as "matched"

        for sid in matched:
            for dep_id in graph.dependencies(sid):
                if dep_id not in matched:
                    dep_skills.add(dep_id)
            for nbr_id in graph.neighbors(sid):
                if nbr_id not in matched:
                    nbr_skill = graph.get_skill(nbr_id)
                    if nbr_skill:
                        cat = nbr_skill.metadata.get("category", "")
                        if (cat in TACTIC_CATS
                                or nbr_id.startswith("tactic-")
                                or nbr_id.startswith("strategy-")):
                            tactic_skills.add(nbr_id)

        # 4. Embeddings (text hash + structural features)
        emb_model = SkillEmbeddingModel(text_dim=256, structure_dim=64, use_gnn=False)
        skill_ids_ordered = [s.id for s in graph.skills]
        embeddings: list[list[float]] = []
        for skill in graph.skills:
            emb = emb_model.embed_skill(skill, graph)
            vec = np.concatenate([emb.text_embedding, emb.structure_embedding])
            embeddings.append(vec.tolist())

        # Query embedding — mismo espacio semántico que los skills (BOW 256-dim)
        # Usa semantic_embed() idéntico al de los skills: el query aterrizará
        # geométricamente cerca de los skills cuyo vocabulario comparte.
        from nucleo.graph.embeddings import semantic_embed
        query_text_emb = semantic_embed(query, dim=256)   # 256-dim BOW semántico
        query_struct_emb = np.zeros(64, dtype=np.float32) # sin estructura de grafo
        query_embedding: list[float] = np.concatenate(
            [query_text_emb, query_struct_emb]
        ).tolist()

        # 5. Colimit / complexification info
        _pillar_cat = {"SET": "foundations", "CAT": "category-theory",
                       "LOG": "logic", "TYPE": "foundations"}
        cats = []
        for sid in matched:
            sk = graph.get_skill(sid)
            if sk:
                c = sk.metadata.get("category") or                     _pillar_cat.get(sk.pillar.name if sk.pillar else "SET", "foundations")
                cats.append(c)
        dominant_cat = Counter(cats).most_common(1)[0][0] if cats else "foundations"

        # 6. Last CR decision
        cr_info: dict = {}
        if self._last_decision:
            cr_info = {
                "source_cr":   self._last_decision.source_cr.name,
                "action_type": self._last_decision.action_type.name,
                "confidence":  self._last_decision.confidence,
            }

        return {
            "query":             query,
            "graph_nodes":       graph_nodes,
            "graph_edges":       graph_edges,
            "matched_skills":    matched,
            "dependency_skills": list(dep_skills),
            "tactic_skills":     list(tactic_skills),
            "skill_ids_ordered": skill_ids_ordered,
            "embeddings":        embeddings,
            "query_embedding":   query_embedding,
            "colimit_info": {
                "pattern_skills":    matched,
                "dominant_category": dominant_cat,
                "n_deps":            len(dep_skills),
                "n_tactics":         len(tactic_skills),
            },
            "cr_info": cr_info,
        }

    def _save_memory(self) -> None:
        """Persistir memoria y buffer de experiencias a disco."""
        if self._memory:
            memory_path = self.config.data_dir / "memory.json"
            try:
                self._memory.save(memory_path)
            except OSError as e:
                logger.warning(f"No se pudo guardar memoria: {e}")

        # Guardar buffer del neural agent para retomar entrenamiento
        if self._neural_agent is not None:
            buf_path = self.config.data_dir / "experience_buffer.pkl"
            try:
                self._neural_agent.buffer.save(buf_path)
            except Exception as e:
                logger.warning(f"No se pudo guardar buffer: {e}")

    # =========================================================================
    # CALLBACKS
    # =========================================================================

    def on_action(self, callback: Callable[[GlobalDecision], None]) -> None:
        """Registrar callback para decisiones de los CRs."""
        self._on_action = callback

    def on_reward(self, callback: Callable[[float], None]) -> None:
        """Registrar callback para evaluacion de resultado."""
        self._on_reward = callback
