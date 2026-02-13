"""
Tests for Hierarchy-Reasoning Integration
==========================================

Tests that the categorical skill graph actually influences
proof generation and tactic selection, not just exists as
an inert data structure.

Three integration points tested:
1. GoalAnalyzer: goal structure → tactic ordering
2. Relevant Context: query → graph traversal → LLM context
3. CR_tac Graph-Aware: query → skill match → ASSIST/RESPONSE
"""

import pytest

from nucleo.types import Skill, PillarType, MorphismType, ActionType
from nucleo.graph.category import SkillCategory
from nucleo.lean.solver_cascade import GoalAnalyzer, SOLVER_CASCADE, SolverCascade
from nucleo.mes.co_regulators import TacticalCoRegulator


# =========================================================================
# Helpers
# =========================================================================


def _build_test_graph() -> SkillCategory:
    """Build a small graph with foundations, domain skills, and tactics."""
    g = SkillCategory(name="TestHierarchy")

    # Level 0 foundations
    g.add_skill(Skill(id="zfc-axioms", name="ZFC Axioms", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="cic", name="CIC", pillar=PillarType.TYPE, level=0))
    g.add_skill(Skill(id="fol-deduction", name="FOL Deduction", pillar=PillarType.LOG, level=0))
    g.add_skill(Skill(id="type-theory", name="Type Theory", pillar=PillarType.TYPE, level=0))

    # Level 1 domain skills
    g.add_skill(Skill(id="group-theory", name="Group Theory", pillar=PillarType.SET, level=1))
    g.add_skill(Skill(id="ring-theory", name="Ring Theory", pillar=PillarType.SET, level=1))
    g.add_skill(Skill(id="real-analysis", name="Real Analysis", pillar=PillarType.SET, level=1))
    g.add_skill(Skill(id="point-set-topology", name="Point-Set Topology", pillar=PillarType.SET, level=1))

    # Dependencies: domain → foundation
    g.add_morphism("zfc-axioms", "group-theory", MorphismType.DEPENDENCY)
    g.add_morphism("zfc-axioms", "ring-theory", MorphismType.DEPENDENCY)
    g.add_morphism("group-theory", "ring-theory", MorphismType.DEPENDENCY)
    g.add_morphism("zfc-axioms", "real-analysis", MorphismType.DEPENDENCY)
    g.add_morphism("zfc-axioms", "point-set-topology", MorphismType.DEPENDENCY)

    # Level 1 tactic skills (TYPE pillar)
    g.add_skill(Skill(id="tactic-simp", name="Simplification", pillar=PillarType.TYPE, level=1))
    g.add_skill(Skill(id="tactic-ring", name="Ring Algebra", pillar=PillarType.TYPE, level=1))
    g.add_skill(Skill(id="tactic-omega", name="Arithmetic", pillar=PillarType.TYPE, level=1))
    g.add_skill(Skill(id="tactic-exact", name="Exact Proof", pillar=PillarType.TYPE, level=1))
    g.add_skill(Skill(id="tactic-apply", name="Apply Rule", pillar=PillarType.TYPE, level=1))
    g.add_skill(Skill(id="tactic-induction", name="Induction", pillar=PillarType.TYPE, level=1))
    g.add_skill(Skill(id="tactic-aesop", name="Automation", pillar=PillarType.TYPE, level=1))

    # Tactic dependencies
    g.add_morphism("type-theory", "tactic-simp", MorphismType.DEPENDENCY)
    g.add_morphism("type-theory", "tactic-ring", MorphismType.DEPENDENCY)
    g.add_morphism("type-theory", "tactic-omega", MorphismType.DEPENDENCY)
    g.add_morphism("type-theory", "tactic-exact", MorphismType.DEPENDENCY)
    g.add_morphism("type-theory", "tactic-apply", MorphismType.DEPENDENCY)
    g.add_morphism("type-theory", "tactic-induction", MorphismType.DEPENDENCY)
    g.add_morphism("type-theory", "tactic-aesop", MorphismType.DEPENDENCY)

    # Domain ↔ tactic connections (the key integration!)
    g.add_morphism("ring-theory", "tactic-ring", MorphismType.TRANSLATION)
    g.add_morphism("ring-theory", "tactic-simp", MorphismType.TRANSLATION)
    g.add_morphism("group-theory", "tactic-simp", MorphismType.TRANSLATION)
    g.add_morphism("group-theory", "tactic-apply", MorphismType.TRANSLATION)
    g.add_morphism("real-analysis", "tactic-simp", MorphismType.TRANSLATION)
    g.add_morphism("real-analysis", "tactic-omega", MorphismType.TRANSLATION)

    # Level 2 strategy skills (LOG pillar)
    g.add_skill(Skill(id="strategy-backward", name="Backward Reasoning", pillar=PillarType.LOG, level=2))
    g.add_skill(Skill(id="strategy-inductive", name="Inductive Proof", pillar=PillarType.LOG, level=2))

    g.add_morphism("tactic-apply", "strategy-backward", MorphismType.DEPENDENCY)
    g.add_morphism("tactic-induction", "strategy-inductive", MorphismType.DEPENDENCY)

    return g


# =========================================================================
# GoalAnalyzer Tests
# =========================================================================


class TestGoalAnalyzer:
    """Tests for goal-aware tactic ordering."""

    def setup_method(self):
        self.analyzer = GoalAnalyzer()
        self.graph = _build_test_graph()

    def test_ring_goal_prioritizes_ring(self):
        """Algebraic goal should prioritize ring tactic."""
        goal = "a * b + c = c + b * a"
        ordered = self.analyzer.prioritize(goal)
        solver_names = [s for s, _ in ordered]
        assert solver_names[0] == "ring"

    def test_arithmetic_goal_prioritizes_omega(self):
        """Nat arithmetic inequality should prioritize omega."""
        goal = "Nat.succ n ≤ Nat.succ (n + 1)"
        ordered = self.analyzer.prioritize(goal)
        solver_names = [s for s, _ in ordered]
        assert solver_names[0] == "omega"

    def test_simple_equality_keeps_rfl_first(self):
        """Non-matching goal keeps default order (rfl first)."""
        goal = "x = x"
        ordered = self.analyzer.prioritize(goal)
        solver_names = [s for s, _ in ordered]
        assert solver_names[0] == "rfl"

    def test_logic_goal_prioritizes_simp(self):
        """Logical connectives should prioritize simp."""
        goal = "P ∧ Q → Q ∧ P"
        ordered = self.analyzer.prioritize(goal)
        solver_names = [s for s, _ in ordered]
        assert solver_names[0] == "simp"

    def test_unknown_goal_default_order(self):
        """Random text should return default cascade order."""
        goal = "something completely different"
        ordered = self.analyzer.prioritize(goal)
        assert ordered == list(SOLVER_CASCADE)

    def test_with_graph_uses_tactic_skills(self):
        """Graph context should add tactics from connected domain skills."""
        # "ring" in goal should match ring-theory skill,
        # which connects to tactic-ring and tactic-simp
        goal = "ring homomorphism preserves addition"
        ordered = self.analyzer.prioritize(goal, graph=self.graph)
        solver_names = [s for s, _ in ordered]
        # ring should be prioritized (either via pattern or graph)
        assert "ring" in solver_names[:4]

    def test_empty_goal_default(self):
        """Empty goal should return default cascade."""
        ordered = self.analyzer.prioritize("")
        assert ordered == list(SOLVER_CASCADE)

    def test_all_solvers_present(self):
        """Reordered list should contain all 9 solvers."""
        goal = "a * b + c = c + b * a"
        ordered = self.analyzer.prioritize(goal)
        solver_names = set(s for s, _ in ordered)
        default_names = set(s for s, _ in SOLVER_CASCADE)
        assert solver_names == default_names

    def test_numeric_arithmetic(self):
        """Pure numeric expressions should prioritize omega/simp."""
        goal = "2 + 3 = 5"
        ordered = self.analyzer.prioritize(goal)
        solver_names = [s for s, _ in ordered]
        assert solver_names[0] in ("omega", "simp", "ring")


# =========================================================================
# Relevant Context Tests (core.py)
# =========================================================================


class TestRelevantContext:
    """Tests for graph-aware context finding in Nucleo."""

    def setup_method(self):
        # We test the methods directly without full Nucleo initialization
        from nucleo.core import Nucleo
        self.nucleo = Nucleo.__new__(Nucleo)
        self.graph = _build_test_graph()

    def test_group_query_matches_skills(self):
        """Query about 'group theory' should match group-theory skill."""
        matched = self.nucleo._match_skills_to_query(
            "What is group theory?", self.graph
        )
        assert "group-theory" in matched

    def test_ring_query_matches_skills(self):
        """Query about 'ring' should match ring-theory skill."""
        matched = self.nucleo._match_skills_to_query(
            "Prove this ring homomorphism", self.graph
        )
        assert "ring-theory" in matched

    def test_induction_query_matches_tactic(self):
        """Query mentioning 'induction' should match tactic-induction."""
        matched = self.nucleo._match_skills_to_query(
            "Prove by induction on n", self.graph
        )
        assert "tactic-induction" in matched

    def test_dependencies_traversed(self):
        """Relevant context should include dependency chain."""
        ctx = self.nucleo._find_relevant_context(
            "ring theory question", self.graph
        )
        # ring-theory depends on zfc-axioms and group-theory
        assert "zfc-axioms" in ctx["prerequisites"] or "group-theory" in ctx["prerequisites"]

    def test_tactics_found(self):
        """Skills connected to tactic skills should appear in suggested_tactics."""
        ctx = self.nucleo._find_relevant_context(
            "ring theory question", self.graph
        )
        # ring-theory connects to tactic-ring and tactic-simp
        assert len(ctx["suggested_tactics"]) > 0
        assert any("ring" in t or "simp" in t for t in ctx["suggested_tactics"])

    def test_unknown_query_empty(self):
        """Random text should return empty/minimal context."""
        ctx = self.nucleo._find_relevant_context(
            "xyzzy plugh", self.graph
        )
        assert ctx["relevant_skills"] == []

    def test_pillar_detection_set(self):
        """Query matching SET-pillar skills should detect SET pillar."""
        pillar = self.nucleo._dominant_pillar(
            ["group-theory", "ring-theory"], self.graph
        )
        assert pillar == "SET"

    def test_pillar_detection_type(self):
        """Query matching TYPE-pillar skills should detect TYPE pillar."""
        pillar = self.nucleo._dominant_pillar(
            ["tactic-simp", "tactic-ring"], self.graph
        )
        assert pillar == "TYPE"

    def test_pillar_default_when_empty(self):
        """No matched skills should default to TYPE."""
        pillar = self.nucleo._dominant_pillar([], self.graph)
        assert pillar == "TYPE"


# =========================================================================
# CR_tac Graph-Aware Tests
# =========================================================================


class TestCRTacGraphAware:
    """Tests for graph-informed tactical co-regulator."""

    def setup_method(self):
        self.cr_tac = TacticalCoRegulator()
        self.graph = _build_test_graph()

    def test_keyword_assist_still_works(self):
        """ASSIST_KEYWORDS should still trigger ASSIST without graph."""
        result = self.cr_tac.classify_query("prove this theorem")
        assert result == ActionType.ASSIST

    def test_keyword_response_without_graph(self):
        """Non-keyword query without graph should be RESPONSE."""
        result = self.cr_tac.classify_query("hello world")
        assert result == ActionType.RESPONSE

    def test_graph_skill_with_tactics_returns_assist(self):
        """Query matching a skill connected to tactics should → ASSIST."""
        # "ring theory" matches ring-theory, which connects to tactic-ring
        result = self.cr_tac.classify_query("ring theory question", graph=self.graph)
        assert result == ActionType.ASSIST

    def test_graph_skill_without_tactics_returns_response(self):
        """Query matching a skill NOT connected to tactics → RESPONSE."""
        # "topology" matches point-set-topology, which has no tactic connections
        result = self.cr_tac.classify_query(
            "what is point set topology about", graph=self.graph
        )
        assert result == ActionType.RESPONSE

    def test_relevant_skills_stored(self):
        """After classify, _relevant_skills should contain matched skills."""
        self.cr_tac.classify_query("group theory basics", graph=self.graph)
        assert len(self.cr_tac._relevant_skills) > 0
        assert "group-theory" in self.cr_tac._relevant_skills

    def test_relevant_skills_empty_for_keywords(self):
        """Keyword-based ASSIST should not populate _relevant_skills."""
        self.cr_tac.classify_query("prove this")
        # Keywords take the fast path, no graph matching
        assert self.cr_tac._relevant_skills == []

    def test_graph_none_falls_back(self):
        """Passing graph=None should not crash, falls back to keywords."""
        result = self.cr_tac.classify_query("ring theory", graph=None)
        # "ring" is not in ASSIST_KEYWORDS (only specific Lean keywords are)
        # so without graph, this should be RESPONSE
        assert result == ActionType.RESPONSE


# =========================================================================
# Integration Tests
# =========================================================================


class TestIntegration:
    """End-to-end tests for hierarchy-reasoning integration."""

    def test_smart_cascade_ring_goal(self):
        """Full smart cascade with ring goal should try ring early."""
        analyzer = GoalAnalyzer()
        graph = _build_test_graph()

        goal = "a * b + c = c + a * b"
        ordered = analyzer.prioritize(goal, graph=graph)
        solver_names = [s for s, _ in ordered]

        # ring should be in the first 2 positions
        ring_idx = solver_names.index("ring")
        assert ring_idx <= 1, f"ring at index {ring_idx}, expected <= 1"

    def test_cr_tac_feeds_context_pipeline(self):
        """CR_tac graph classification + context finding should work together."""
        from nucleo.core import Nucleo

        graph = _build_test_graph()
        cr_tac = TacticalCoRegulator()

        # 1. CR_tac classifies with graph
        action = cr_tac.classify_query("ring theory question", graph=graph)
        assert action == ActionType.ASSIST

        # 2. Context finder uses same graph
        nucleo = Nucleo.__new__(Nucleo)
        ctx = nucleo._find_relevant_context("ring theory question", graph)
        assert "ring-theory" in ctx["relevant_skills"]
        assert len(ctx["suggested_tactics"]) > 0
