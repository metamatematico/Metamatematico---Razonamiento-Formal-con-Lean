"""
Tests de Live Learning y Skills de Lean/Pruebas
================================================

Verifica:
- Skills de tacticas Lean se cargan correctamente
- Skills de estrategias de prueba se cargan
- Dependencias L2 resuelven a L1
- Live PPO update via Nucleo
- Procedimientos guardan contexto (query, tactic)
- get_best_for_query encuentra coincidencias
- Agente prioriza patrones exitosos de memoria
"""

import pytest

from nucleo.types import Skill, MorphismType, PillarType, State, Action, ActionType
from nucleo.graph.category import SkillCategory
from nucleo.pillars.math_domains import (
    LEAN_TACTICS_SKILLS,
    PROOF_STRATEGY_SKILLS,
    ALL_DOMAIN_SKILLS,
    load_math_domains,
)
from nucleo.mes.memory import Procedure, ProceduralMemory
from nucleo.rl.mdp import Transition


@pytest.fixture
def graph_with_foundations():
    """Grafo con skills L0 necesarios para cargar dominios."""
    g = SkillCategory(name="TestLiveLearning")
    for sid in ["zfc-axioms", "category-basics", "fol-deduction", "type-theory"]:
        g.add_skill(Skill(id=sid, name=sid, pillar=PillarType.SET, level=0))
    return g


class TestLeanTacticSkills:
    """Tests para skills de tacticas Lean."""

    def test_lean_tactic_skills_count(self):
        assert len(LEAN_TACTICS_SKILLS) == 9

    def test_lean_tactic_skills_loaded(self, graph_with_foundations):
        load_math_domains(graph_with_foundations)
        for skill_def in LEAN_TACTICS_SKILLS:
            assert skill_def.id in graph_with_foundations._skills, (
                f"Skill {skill_def.id} not loaded"
            )

    def test_lean_tactics_are_type_pillar(self):
        for s in LEAN_TACTICS_SKILLS:
            assert s.pillar == PillarType.TYPE

    def test_lean_tactics_level_1(self):
        for s in LEAN_TACTICS_SKILLS:
            assert s.level == 1

    def test_lean_tactics_depend_on_type_theory(self):
        for s in LEAN_TACTICS_SKILLS:
            assert "type-theory" in s.dependencies

    def test_lean_tactics_category(self):
        for s in LEAN_TACTICS_SKILLS:
            assert s.category == "lean-tactics"


class TestProofStrategySkills:
    """Tests para skills de estrategias de prueba."""

    def test_proof_strategy_skills_count(self):
        assert len(PROOF_STRATEGY_SKILLS) == 6

    def test_proof_strategy_skills_loaded(self, graph_with_foundations):
        load_math_domains(graph_with_foundations)
        for skill_def in PROOF_STRATEGY_SKILLS:
            assert skill_def.id in graph_with_foundations._skills, (
                f"Skill {skill_def.id} not loaded"
            )

    def test_proof_strategies_are_log_pillar(self):
        for s in PROOF_STRATEGY_SKILLS:
            assert s.pillar == PillarType.LOG

    def test_proof_strategies_level_2(self):
        for s in PROOF_STRATEGY_SKILLS:
            assert s.level == 2

    def test_skill_dependencies_resolved(self, graph_with_foundations):
        """L2 skills depend on L1 skills that exist."""
        load_math_domains(graph_with_foundations)
        for skill_def in PROOF_STRATEGY_SKILLS:
            # At least one dependency should exist
            has_dep = any(
                d in graph_with_foundations._skills
                for d in skill_def.dependencies
            )
            assert has_dep, f"{skill_def.id} has no resolved dependencies"

    def test_total_skills_increased(self):
        """ALL_DOMAIN_SKILLS includes lean tactics and proof strategies."""
        tactic_ids = {s.id for s in LEAN_TACTICS_SKILLS}
        strategy_ids = {s.id for s in PROOF_STRATEGY_SKILLS}
        all_ids = {s.id for s in ALL_DOMAIN_SKILLS}
        assert tactic_ids.issubset(all_ids)
        assert strategy_ids.issubset(all_ids)


class TestProcedureContext:
    """Tests para campos enriquecidos de Procedure."""

    def test_procedure_stores_query_text(self):
        mem = ProceduralMemory()
        proc = mem.add_procedure(
            "test-pattern", ["RESPONSE"],
            success=True,
            query_text="prove x = x",
        )
        assert proc.query_text == "prove x = x"

    def test_procedure_stores_tactic(self):
        mem = ProceduralMemory()
        proc = mem.add_procedure(
            "test-pattern", ["ASSIST"],
            success=True,
            tactic_used="simp",
            lean_goal="x = x",
        )
        assert proc.tactic_used == "simp"
        assert proc.lean_goal == "x = x"

    def test_procedure_update_preserves_context(self):
        mem = ProceduralMemory()
        mem.add_procedure(
            "p1", ["RESPONSE"],
            success=True,
            query_text="prove theorem",
        )
        # Update same procedure
        proc = mem.add_procedure(
            "p1", ["RESPONSE"],
            success=True,
            query_text="prove another theorem",
        )
        assert proc.query_text == "prove another theorem"
        assert proc.invocation_count == 2


class TestBestForQuery:
    """Tests para get_best_for_query."""

    def test_finds_matching_procedure(self):
        mem = ProceduralMemory()
        mem.add_procedure(
            "p1", ["ASSIST"],
            success=True,
            query_text="prove theorem by induction",
        )
        result = mem.get_best_for_query("prove by induction")
        assert result is not None
        assert result.pattern_id == "p1"

    def test_returns_none_for_no_match(self):
        mem = ProceduralMemory()
        mem.add_procedure(
            "p1", ["ASSIST"],
            success=True,
            query_text="prove theorem",
        )
        result = mem.get_best_for_query("completely unrelated xyz abc")
        assert result is None

    def test_respects_min_success(self):
        mem = ProceduralMemory()
        mem.add_procedure(
            "p1", ["ASSIST"],
            success=False,  # 0.0 success rate
            query_text="prove theorem",
        )
        result = mem.get_best_for_query("prove theorem", min_success=0.8)
        assert result is None

    def test_returns_none_for_empty_query(self):
        mem = ProceduralMemory()
        result = mem.get_best_for_query("")
        assert result is None

    def test_prefers_higher_success_rate(self):
        mem = ProceduralMemory()
        mem.add_procedure(
            "p1", ["RESPONSE"],
            success=True,
            query_text="prove lemma about groups",
        )
        proc2 = mem.add_procedure(
            "p2", ["ASSIST"],
            success=True,
            query_text="prove lemma about groups different",
        )
        # Invoke p2 multiple times to boost score
        for _ in range(5):
            proc2.invoke()
            proc2.success_rate = 1.0

        result = mem.get_best_for_query("prove lemma about groups")
        assert result is not None
        assert result.pattern_id == "p2"


class TestAgentMemoryIntegration:
    """Tests para integracion agente-memoria."""

    def test_agent_uses_memory_pattern(self):
        g = SkillCategory(name="MemTest")
        g.add_skill(Skill(id="s1", name="A", pillar=PillarType.SET, level=0))
        g.add_skill(Skill(id="s2", name="B", pillar=PillarType.LOG, level=0))
        g.add_morphism("s1", "s2", MorphismType.DEPENDENCY)

        from nucleo.rl.agent import NucleoAgent

        agent = NucleoAgent(g, use_neural=True)
        agent.eval_mode()

        # Set up procedural memory with a proven pattern
        mem = ProceduralMemory()
        proc = mem.add_procedure(
            "proven", ["ASSIST"],
            success=True,
            query_text="prove x equals x",
            tactic_used="simp",
        )
        # Boost success and invocations
        for _ in range(5):
            proc.invoke()
            proc.success_rate = 1.0

        agent._procedural_memory = mem

        # Agent should use memory pattern for matching query
        state = State(lean_goal="prove x equals x by simp")
        action = agent.select_action(state)
        assert action.action_type == ActionType.ASSIST

    def test_agent_falls_back_to_neural(self):
        g = SkillCategory(name="MemTest")
        g.add_skill(Skill(id="s1", name="A", pillar=PillarType.SET, level=0))
        g.add_skill(Skill(id="s2", name="B", pillar=PillarType.LOG, level=0))
        g.add_morphism("s1", "s2", MorphismType.DEPENDENCY)

        from nucleo.rl.agent import NucleoAgent

        agent = NucleoAgent(g, use_neural=True)
        agent.eval_mode()

        # Empty memory - should fall back to neural
        agent._procedural_memory = ProceduralMemory()
        state = State(lean_goal="something completely new")
        action = agent.select_action(state)
        # Should still return a valid action (from neural net)
        assert action.action_type in [
            ActionType.RESPONSE, ActionType.REORGANIZE, ActionType.ASSIST
        ]


class TestLivePPOUpdate:
    """Tests para live PPO update en core.py."""

    def test_nucleo_accepts_neural_agent(self):
        from nucleo.core import Nucleo

        nucleo = Nucleo()
        assert nucleo._neural_agent is None
        assert nucleo._live_learning_steps == 0

    def test_set_neural_agent(self):
        from nucleo.core import Nucleo

        nucleo = Nucleo()
        # Use a mock agent
        nucleo.set_neural_agent("mock_agent")
        assert nucleo._neural_agent == "mock_agent"
