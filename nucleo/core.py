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
import logging
from dataclasses import dataclass, field
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

        # Feedback tracking — last experience for retroactive update
        self._last_experience_id: Optional[str] = None
        self._last_action_type = None

        # Math answer evaluator (MATH / GSM8K benchmarks)
        self._evaluator: MathEvaluator = MathEvaluator()

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

        # LLM Client
        llm_config = LLMConfig(
            model=self.config.llm.model,
            max_tokens=self.config.llm.max_tokens,
            temperature=self.config.llm.temperature,
            api_key=self.config.llm.api_key,
        )
        self._llm = LLMClient(llm_config)

        # Lean Client
        self._lean = LeanClient(
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
        self._evolution = EvolutionarySystem(self._graph)
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

        # Activar multi-agente con los 14 agentes especializados (lazy load)
        try:
            self.set_multi_agent_orchestrator()
            logger.info("MultiAgentOrchestrator activado con pesos en training/agents/best/")
        except Exception as e:
            logger.warning(f"MultiAgentOrchestrator no disponible: {e}")

        self._initialized = True
        logger.info("Nucleo inicializado correctamente (PPO activo)")

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
            # Respuesta genérica pero útil para cualquier consulta matemática
            ctx = self._find_relevant_context(input_text, self._graph)
            skills_found = ctx.get("skills", [])
            skills_str = (
                ", ".join(f"`{s}`" for s in skills_found[:4])
                if skills_found else "skills matemáticos relevantes"
            )
            category = ctx.get("category", "matemáticas")
            explanation = (
                f"El NLE identificó esta consulta como relacionada con **{category}** "
                f"(skills: {skills_str}).\n\n"
                f"Para obtener una respuesta completa que incluya:\n"
                f"- Enunciado preciso del resultado\n"
                f"- Demostración paso a paso\n"
                f"- Código Lean 4 verificado con Mathlib\n\n"
                f"**conecta una API key** (Anthropic, Google o Groq) en el panel lateral. "
                f"El Núcleo Lógico Evolutivo usará su GNN+PPO para enrutar tu consulta al "
                f"agente especializado correcto y generará una prueba formal verificada por Lean 4."
            )

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
        edu_prompt = (
            f"Responde a la siguiente pregunta matemática de forma educativa y completa:\n\n"
            f"{input_text}\n\n"
            "Estructura tu respuesta con:\n"
            "1. **Enunciado** — cómo se formula el resultado (con notación matemática $...$)\n"
            "2. **Contexto histórico** — si aplica, quién lo descubrió y cuándo\n"
            "3. **Demostración / Explicación** — paso a paso, geométrica/visual si se pide, "
            "con intuición clara\n"
            "4. **Nota Lean 4** (breve) — cómo se formaliza en Mathlib, sin código extenso\n\n"
            "Responde en el mismo idioma que el usuario."
        )
        resp = await self._llm.generate(edu_prompt, system=edu_system, context=context)
        return NucleoResponse(
            content=resp.content,
            action_type=ActionType.ASSIST,
            confidence=0.88,
            metadata={"mode": "educational_explanation"},
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
            return self._demo_educational_response(input_text)

        from nucleo.llm.client import LLMClient
        lean_system = LLMClient.LEAN_SYSTEM_PROMPT
        context = self._find_relevant_context(input_text, self._graph)
        context["task"] = "lean_formalization"

        # ── Detección de queries educativas/históricas (no necesitan Lean primero) ──
        q_lower = self._normalize_text(input_text)
        _educational_markers = (
            "como lo enuncio", "como lo enuncio pitagoras", "como lo enuncio euclides",
            "como lo dijo", "historicamente", "geometricamente como",
            "demostracion geometrica", "demostracion visual", "demostracion clasica",
            "prueba geometrica", "prueba visual", "prueba clasica",
            "como lo haria euclides", "al estilo euclides", "segun pitagoras",
            "segun euclides", "intuicion", "idea intuitiva", "explicacion intuitiva",
        )
        _is_educational_query = any(m in q_lower for m in _educational_markers)

        if _is_educational_query:
            return await self._math_educational_explanation(input_text, context)

        # ── Paso 1: LLM formaliza → Lean 4 ──────────────────────────────────
        # Construir ejemplos few-shot relevantes (miniF2F)
        few_shot_block = self._build_few_shot_context(input_text)

        # ── Referencia hardcoded para teoremas clásicos ───────────────────
        _HARDCODED_REFS = {
            ("pitagor", "pythag", "hipotenusa"): (
                "-- REFERENCIA: Teorema de Pitágoras en Lean 4 / Mathlib\n"
                "-- El teorema NO toma a²+b²=c² como hipótesis; usa geometría.\n"
                "-- Versión algebraica con norma (‖·‖²):\n"
                "import Mathlib.Analysis.InnerProductSpace.Basic\n"
                "-- ‖a‖² + ‖b‖² = ‖c‖² cuando ⟪a, b⟫ = 0\n"
                "-- Mathlib: inner_mul_le_norm_mul_iff, norm_add_sq_real\n"
                "-- Para enunciar: usa real_inner_eq_zero y norm_sq\n"
                "example (a b : EuclideanSpace ℝ (Fin 2))\n"
                "    (h : ⟪a, b⟫_ℝ = 0) :\n"
                "    ‖a + b‖^2 = ‖a‖^2 + ‖b‖^2 := by\n"
                "  rw [norm_add_sq_real, h, mul_zero, mul_comm, mul_zero, add_zero]"
            ),
            ("yoneda",): (
                "import Mathlib.CategoryTheory.Yoneda\n"
                "-- yonedaEquiv : (yoneda.obj X ⟶ F) ≃ F.obj X"
            ),
            ("curry", "howard"): (
                "-- Propositions as types en Lean 4\n"
                "example (P Q : Prop) (h : P → Q) (hp : P) : Q := h hp"
            ),
            ("irrac", "sqrt", "raiz cuadrada de 2", "sqrt(2)"): (
                "import Mathlib.Data.Real.Irrational\n"
                "example : Irrational (Real.sqrt 2) := irrational_sqrt_two"
            ),
        }

        extra_ref = ""
        q_norm = self._normalize_text(input_text)
        for kws, ref in _HARDCODED_REFS.items():
            if any(k in q_norm for k in kws):
                extra_ref = f"\nReferencia de Mathlib para este tema:\n```lean\n{ref}\n```\n"
                break

        # Detectar si el usuario solo quiere el enunciado (no la prueba)
        q_norm = self._normalize_text(input_text)
        _enunciar = any(w in q_norm for w in ("enuncia", "enunciar", "enunciado", "que dice", "que establece", "que afirma"))
        _solo_enunciar_hint = (
            "- El usuario solo pide ENUNCIAR (no demostrar). Escribe ÚNICAMENTE el `theorem` con `sorry` en el cuerpo, sin intentar dar una prueba.\n"
            if _enunciar else ""
        )

        formalize_prompt = (
            "Tu única tarea es escribir UN SOLO bloque de código Lean 4 (no varios) que formalice "
            "el siguiente enunciado o pregunta matemática.\n\n"
            f"Enunciado: {input_text}\n\n"
            + extra_ref
            + (
                f"Ejemplos de referencia (Lean 3 — adapta la sintaxis a Lean 4):\n"
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
            "  EJEMPLO PROHIBIDO: `(h : a^2+b^2=c^2) : c^2=a^2+b^2 := h.symm` — esto es una tautología.\n"
            "- PROHIBIDO: generar múltiples versiones del mismo resultado.\n"
            "- Usa los tipos y teoremas de Mathlib apropiados (InnerProductSpace, EuclideanSpace, etc.).\n"
            "- No pongas explicaciones fuera del bloque de código."
        )
        lean_gen = await self._llm.generate(
            formalize_prompt, system=lean_system, context=context
        )
        lean_code = self._extract_lean_code(lean_gen.content)
        if not lean_code:
            lean_code = lean_gen.content.strip()

        # ── Detección de formalización trivial → regenerar ─────────────────
        def _is_trivial_lean(code: str) -> bool:
            """Detecta el patrón tautológico: hipótesis = conclusión."""
            import re
            # Patrón: (h : X) : Y := h o h.symm donde X ≅ Y
            trivial_patterns = [
                r":\s*\w[\w\s\^+*=]+:=\s*\w+\.symm",   # h.symm
                r":=\s*by\s+exact\s+\w+$",               # exact h (un solo paso)
                r":=\s*\w+\s*$",                          # := h (único término)
            ]
            # Si hay solo una hipótesis que es la ecuación principal
            has_trivial_hyp = bool(re.search(
                r"\(\w+\s*:\s*\w+\^2\s*\+\s*\w+\^2\s*=\s*\w+\^2\)", code
            ))
            is_short = len([l for l in code.strip().splitlines() if l.strip()]) <= 5
            if has_trivial_hyp and is_short:
                return True
            for pat in trivial_patterns:
                # Solo trivial si el cuerpo es SOLO la hipótesis
                if re.search(pat, code, re.MULTILINE) and is_short:
                    return True
            return False

        if _is_trivial_lean(lean_code):
            # Regenerar con prompt más fuerte
            retry_prompt = (
                f"{formalize_prompt}\n\n"
                "ATENCIÓN: Tu respuesta anterior fue trivial (tomaste la ecuación como hipótesis). "
                "Genera una formalización REAL usando la geometría euclidiana o espacios con producto interior. "
                "Usa `inner_mul_le_norm_sq` o `norm_add_sq_real` de Mathlib, con `sorry` si no sabes la táctica exacta."
            )
            lean_gen2 = await self._llm.generate(
                retry_prompt, system=lean_system, context=context
            )
            lean_code2 = self._extract_lean_code(lean_gen2.content) or lean_gen2.content.strip()
            if not _is_trivial_lean(lean_code2):
                lean_code = lean_code2

        # ── Paso 2: Lean verifier ─────────────────────────────────────────
        result = await self._lean.check_code(lean_code)

        if result.is_success:
            verification_status = "verificado"
            verification_note = (
                "La prueba fue verificada formalmente por Lean 4 sin errores."
            )
            confidence    = 0.95
            success_value = 1.0

        elif result.status == LeanResultStatus.SORRY:
            # ── Paso 3: Solver cascade intenta llenar los sorry ───────────
            sorry_msg, confidence, success_value = await self._try_solve_sorries(
                lean_code, result
            )
            verification_status = "parcial"
            verification_note = (
                f"Lean 4 aceptó la estructura de la prueba. {sorry_msg}"
            )

        else:
            error_info = self._analyze_lean_errors(result)
            first_err  = result.get_first_error() or "error desconocido"
            err_type   = error_info.get("type", "unknown")
            # Mensajes de diagnóstico específicos según el tipo de error
            _LEAN_HINTS = {
                "unknown identifier": "posiblemente falta un `open` o un import de Mathlib.",
                "type mismatch":      "los tipos no coinciden; puede faltar una coerción o instancia.",
                "application type mismatch": "argumentos aplicados incorrectamente; revisa la aridad.",
                "failed to synthesize": "falta una instancia de typeclass (e.g., `Field ℝ`, `OrderedField`).",
                "function expected":  "se usó algo como función que no lo es.",
                "tactic failed":      "la táctica no cerró el goal; prueba `ring_nf` o `simp [*]` primero.",
            }
            hint = next(
                (h for k, h in _LEAN_HINTS.items() if k in first_err.lower()),
                "revisa la sintaxis Lean 4 y los imports de Mathlib."
            )
            verification_status = "no_verificado"
            verification_note = (
                f"Lean 4 detectó un error de tipo `{err_type}`: {first_err}. "
                f"Diagnóstico: {hint}"
            )
            confidence    = 0.6
            success_value = 0.2

        # ── Paso 4: LLM traduce a lenguaje natural amable ─────────────────
        translate_prompt = (
            "Eres un traductor matemático experto. Tu trabajo es explicar el siguiente "
            "código Lean 4 en lenguaje natural claro, preciso y amable.\n\n"
            "IMPORTANTE: Si el código Lean toma la afirmación principal como hipótesis "
            "y la concluye trivialmente (e.g., `h_right_triangle : a^2 + b^2 = c^2` → "
            "`c^2 = a^2 + b^2`), indícalo explícitamente y explica el teorema REAL "
            "usando tu conocimiento matemático, no el código trivial.\n\n"
            f"Pregunta original del usuario:\n> {input_text}\n\n"
            f"Código Lean 4 generado:\n```lean\n{lean_code}\n```\n\n"
            f"Estado de verificación: {verification_note}\n\n"
            "Escribe tu explicación con estas secciones:\n\n"
            "## ¿Qué dice este resultado?\n"
            "[Explica el enunciado con tus palabras, como si hablaras con "
            "alguien que sabe matemáticas pero no conoce Lean.]\n\n"
            "## ¿Cómo lo demuestra Lean?\n"
            "[Explica la estrategia de la prueba y qué hace cada táctica "
            "importante. Sin copiar el código — solo en palabras.]\n\n"
            "## ¿Por qué es correcto?\n"
            "[Explica la intuición matemática detrás de la prueba. "
            "¿Qué hace que este argumento sea válido?]"
            + (
                "\n\n## Nota sobre la verificación\n"
                f"[{verification_note}]"
                if verification_status != "verificado" else ""
            )
        )
        translation = await self._llm.generate(
            translate_prompt, system=lean_system, context=context
        )

        # ── Ensamblaje final ───────────────────────────────────────────────
        status_badge = {
            "verificado":    "**Lean 4: verificado formalmente**",
            "parcial":       "**Lean 4: estructura verificada (sorry parcial)**",
            "no_verificado": "**Lean 4: formalización pendiente de ajuste**",
        }[verification_status]

        content = (
            f"{translation.content}\n\n"
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
        )

    def _build_few_shot_context(self, query: str) -> str:
        """
        Buscar 2-3 ejemplos few-shot de miniF2F relevantes para la query.

        Usa el banco lean_examples.json (cargado en initialize).
        Selecciona por categoria y keyword overlap.
        """
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
        best_cat = "general"
        best_score = 0
        for cat, keywords in cat_map.items():
            score = len(tokens & keywords)
            if score > best_score:
                best_score = score
                best_cat = cat

        # Tomar ejemplos de la categoria inferida, o de competition_math como fallback
        candidates = (
            self._lean_examples.get(best_cat, [])
            or self._lean_examples.get("competition_math", [])
            or next(iter(self._lean_examples.values()), [])
        )

        # Seleccionar los 2 primeros (ya estan filtrados por has_proof=True)
        selected = candidates[:2]
        if not selected:
            return ""

        lines = []
        for ex in selected:
            tac_str = "\n  ".join(ex.get("tactics", [])[:3])
            lines.append(
                f"-- Ejemplo: {ex['name']} ({best_cat})\n"
                f"{ex['statement']}\nbegin\n  {tac_str}\nend"
            )

        return "\n\n".join(lines)

    async def _try_solve_sorries(
        self, code: str, result: LeanResult
    ) -> tuple[str, float, float]:
        """Try solver cascade on sorry-containing code."""
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
            if self._sorry_filler:
                fill_result = await self._sorry_filler.fill_sorry_with_cascade(
                    ctx, code
                )
                if fill_result.chosen_solution:
                    solved.append(fill_result.chosen_solution.code)
                else:
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

                # Save weights periodically
                if self._live_learning_steps % 10 == 0:
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
                orchestrator = MultiAgentOrchestrator(
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
        learns from real chat rewards.
        """
        self._neural_agent = agent

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
            return future.result(timeout=120)  # 2 min timeout

    # =========================================================================
    # PROPIEDADES
    # =========================================================================

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

        pillar = self._dominant_pillar(matched, graph)

        return {
            "relevant_skills": matched[:5],
            "prerequisites": deps[:5],
            "suggested_tactics": tactics,
            "proof_strategies": strategies,
            "pillar": pillar,
        }

    def _match_skills_to_query(
        self, query: str, graph: SkillCategory
    ) -> list[str]:
        """
        Match skills in the graph to a query by keyword overlap.

        Tokenizes the query and compares against skill IDs and names.
        Returns skill IDs sorted by match relevance (most tokens matched first).
        """
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
            }
            q_lower = query.lower()
            m_set: set[str] = set()
            for kw, sids in _VIZ_KW.items():
                if kw in q_lower:
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
