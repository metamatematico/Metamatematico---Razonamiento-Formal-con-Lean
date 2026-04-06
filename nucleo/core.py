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
        "prueba", "demostrar", "probar", "verificar", "calcular", "hallar",
        "encontrar", "derivada", "integral", "limite", "serie", "sucesion",
        "convergencia", "divergencia", "continua", "diferenciable", "analitica",
        "grupo", "anillo", "campo", "espacio", "subespacio", "base", "dimension",
        "vector", "matriz", "determinante", "eigenvalor", "autovalor",
        "polinomio", "funcion", "biyeccion", "inyectiva", "sobreyectiva",
        "isomorfismo", "homomorfismo", "endomorfismo", "automorfismo",
        "conjunto", "subconjunto", "interseccion", "union", "complemento",
        "cardinalidad", "infinito", "axioma", "hipotesis", "conclusion",
        "logica", "cuantificador", "implicacion", "equivalencia", "negacion",
        "topologia", "metrica", "norma", "producto", "suma", "algebra",
        "geometria", "numero", "primo", "divisible", "modulo", "congruencia",
        "categoria", "funtor", "transformacion", "natural", "adjunto",
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

        # Frases puramente conversacionales → no matematico
        conversational_starters = (
            "hola", "buenos", "buenas", "gracias", "adios", "hasta",
            "como estas", "como te llamas", "que eres", "quien eres",
            "hi ", "hello", "thanks", "bye",
        )
        if any(low.strip().startswith(s) for s in conversational_starters):
            return False

        # Simbolos matematicos Unicode
        if any(ch in text for ch in self._MATH_SYMBOLS):
            return True

        # LaTeX matematico
        if any(cmd in text for cmd in self._MATH_LATEX):
            return True

        # Keywords: al menos 1 match sobre tokens de la query
        tokens = set(
            w.strip("¿?.,;:!()[]{}\"'") for w in low.split()
        )
        if tokens & self._MATH_KEYWORDS:
            return True

        return False

    async def _math_via_lean(self, input_text: str) -> NucleoResponse:
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
        from nucleo.llm.client import LLMClient
        lean_system = LLMClient.LEAN_SYSTEM_PROMPT
        context = self._find_relevant_context(input_text, self._graph)
        context["task"] = "lean_formalization"

        # ── Paso 1: LLM formaliza → Lean 4 ──────────────────────────────────
        # Construir ejemplos few-shot relevantes (miniF2F)
        few_shot_block = self._build_few_shot_context(input_text)

        formalize_prompt = (
            "Tu única tarea es escribir código Lean 4 que formalice el siguiente "
            "enunciado o pregunta matemática.\n\n"
            f"Enunciado: {input_text}\n\n"
            + (
                f"Ejemplos de referencia (Lean 3 — adapta la sintaxis a Lean 4):\n"
                f"{few_shot_block}\n\n"
                if few_shot_block else ""
            )
            + "Instrucciones:\n"
            "- Escribe SOLO el bloque de código Lean 4. Nada más.\n"
            "- El código debe ser autocontenido (con los imports necesarios).\n"
            "- Si es una afirmación, escríbela como `theorem` o `lemma`.\n"
            "- Si es una definición, usa `def` o `structure`.\n"
            "- Si no sabes la prueba completa, usa `sorry` como marcador.\n"
            "- No pongas explicaciones fuera del bloque de código."
        )
        lean_gen = await self._llm.generate(
            formalize_prompt, system=lean_system, context=context
        )
        lean_code = self._extract_lean_code(lean_gen.content)
        if not lean_code:
            # Si el LLM no produjo un bloque, usar su respuesta completa
            lean_code = lean_gen.content.strip()

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
            verification_status = "no_verificado"
            verification_note = (
                f"Lean 4 reportó un error (`{error_info.get('type', 'unknown')}`): "
                f"{first_err}. La formalización puede requerir ajustes."
            )
            confidence    = 0.6
            success_value = 0.2

        # ── Paso 4: LLM traduce a lenguaje natural amable ─────────────────
        translate_prompt = (
            "Eres un traductor matemático. Tu trabajo es explicar el siguiente "
            "código Lean 4 en lenguaje natural claro, preciso y amable. "
            "No tienes que razonar ni inventar — solo explicar lo que Lean dice.\n\n"
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
