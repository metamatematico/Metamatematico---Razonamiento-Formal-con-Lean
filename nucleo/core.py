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

        # Neural agent for live PPO learning (optional)
        self._neural_agent = None
        self._live_learning_steps = 0

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

        self._initialized = True
        logger.info("Nucleo inicializado correctamente")

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
            # Generar respuesta con LLM using graph-relevant context
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
            # Asistir con prueba Lean
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

        Integration with lean4-skills (Phase 6):
        1. Check code with Lean
        2. If has sorries → use goal-aware solver cascade
        3. Record result as ExperienceRecord in MES memory
        4. Attempt E-concept formation
        """
        if "```lean" not in input_text and "theorem" not in input_text:
            # Sin codigo Lean, generar sugerencia con graph context
            context = self._find_relevant_context(input_text, self._graph)
            context["task"] = "formalization"
            llm_response = await self._llm.generate(
                f"Sugiere como formalizar en Lean 4: {input_text}",
                context=context,
            )
            return NucleoResponse(
                content=llm_response.content,
                action_type=ActionType.ASSIST,
                confidence=0.7
            )

        code = self._extract_lean_code(input_text)

        # Step 1: Verify with Lean
        result = await self._lean.check_code(code)

        if result.is_success:
            content = "La prueba es correcta."
            confidence = 0.9
            success_value = 1.0
        elif result.status == LeanResultStatus.SORRY:
            # Step 2: Try solver cascade on sorries
            content, confidence, success_value = await self._try_solve_sorries(
                code, result
            )
        else:
            # Parse errors with structured analysis
            error_info = self._analyze_lean_errors(result)
            mapper = TacticMapper()
            if self._state.lean_goal:
                suggestions = mapper.suggest_tactics(self._state.lean_goal)
                content = f"Tacticas sugeridas: {', '.join(suggestions[:5])}"
            else:
                content = f"Error ({error_info.get('type', 'unknown')}): {result.get_first_error() or 'desconocido'}"
            confidence = 0.5
            success_value = -0.5

        # Step 3: Record in MES memory
        self._record_lean_experience("lean-tactics", success_value)

        return NucleoResponse(
            content=content,
            action_type=ActionType.ASSIST,
            lean_result=result,
            confidence=confidence
        )

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

        # Intentar formar E-concepto
        self._memory.try_form_concept(
            record.pattern_id, decision.source_cr
        )

        # Aprender procedimiento si fue exitoso
        if success > 0.5:
            self._memory.learn_procedure(
                record.pattern_id,
                [decision.action_type.name],
                success=True,
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

    def set_neural_agent(self, agent) -> None:
        """
        Set neural agent for live PPO learning.

        When set, each interaction feeds a PPO update so the agent
        learns from real chat rewards.
        """
        self._neural_agent = agent

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

    def _save_memory(self) -> None:
        """Persistir memoria a disco."""
        if self._memory:
            memory_path = self.config.data_dir / "memory.json"
            try:
                self._memory.save(memory_path)
            except OSError as e:
                logger.warning(f"No se pudo guardar memoria: {e}")

    # =========================================================================
    # CALLBACKS
    # =========================================================================

    def on_action(self, callback: Callable[[GlobalDecision], None]) -> None:
        """Registrar callback para decisiones de los CRs."""
        self._on_action = callback

    def on_reward(self, callback: Callable[[float], None]) -> None:
        """Registrar callback para evaluacion de resultado."""
        self._on_reward = callback
