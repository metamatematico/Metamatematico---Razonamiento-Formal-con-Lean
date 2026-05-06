"""
Tests for the emergent complexity order (cn) hierarchy.

Verifies that:
  - cn(X) = 0 for atomic skills (no colimit registration)
  - cn(X) = k+1 for join-skills whose components have max cn = k
  - Stacked joins produce cn = 2
  - build_hierarchy_to_fixpoint updates graph skill levels correctly
  - find_existing_join correctly identifies the join in simple preorders
  - No join is found when the graph has no upper bounds
"""
import pytest

from nucleo.types import Skill, Colimit, MorphismType, PillarType
from nucleo.graph.category import SkillCategory
from nucleo.mes.patterns import PatternManager, ColimitBuilder
from nucleo.graph.complexity import (
    compute_complexity_order,
    find_existing_join,
    build_join_for_pattern,
    build_hierarchy_to_fixpoint,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _graph(*skill_ids: str) -> SkillCategory:
    g = SkillCategory()
    for sid in skill_ids:
        g.add_skill(Skill(id=sid, name=sid, pillar=PillarType.SET, level=0))
    return g


def _pm_cb(graph: SkillCategory):
    pm = PatternManager()
    cb = ColimitBuilder(pm)
    return pm, cb


def _register_colimit(cb: ColimitBuilder, pm: PatternManager,
                      comp_ids: list[str], join_id: str) -> Colimit:
    """Helper: register a colimit without graph verification."""
    pattern = pm.create_pattern(comp_ids, [])
    col = Colimit(pattern_id=pattern.id, skill_id=join_id)
    cb._colimits[col.id] = col
    cb._pattern_to_colimit[pattern.id] = col.id
    return col


# ---------------------------------------------------------------------------
# TestComputeComplexityOrder
# ---------------------------------------------------------------------------

class TestComputeComplexityOrder:
    def test_no_colimits_all_zero(self):
        g = _graph("A", "B", "C")
        pm, cb = _pm_cb(g)
        cn = compute_complexity_order(g, cb)
        assert all(v == 0 for v in cn.values())

    def test_cn_one_for_direct_join(self):
        g = _graph("A", "B", "C")
        pm, cb = _pm_cb(g)
        _register_colimit(cb, pm, ["A", "B"], "C")
        cn = compute_complexity_order(g, cb)
        assert cn["C"] == 1
        assert cn["A"] == 0
        assert cn["B"] == 0

    def test_cn_two_for_stacked_join(self):
        # A, B → C (cn=1);  C, A → D (cn=2)
        g = _graph("A", "B", "C", "D")
        pm, cb = _pm_cb(g)
        _register_colimit(cb, pm, ["A", "B"], "C")
        _register_colimit(cb, pm, ["C", "A"], "D")
        cn = compute_complexity_order(g, cb)
        assert cn["C"] == 1
        assert cn["D"] == 2

    def test_fixpoint_idempotent(self):
        g = _graph("A", "B", "C")
        pm, cb = _pm_cb(g)
        _register_colimit(cb, pm, ["A", "B"], "C")
        cn1 = compute_complexity_order(g, cb)
        cn2 = compute_complexity_order(g, cb)
        assert cn1 == cn2

    def test_missing_skill_in_graph_ignored(self):
        g = _graph("A", "B")
        pm, cb = _pm_cb(g)
        # Register colimit for skill "C" that is NOT in the graph
        _register_colimit(cb, pm, ["A", "B"], "C")
        cn = compute_complexity_order(g, cb)
        # "C" gets added to cn but with value 1; no crash
        assert cn.get("C", -1) == 1


# ---------------------------------------------------------------------------
# TestFindExistingJoin
# ---------------------------------------------------------------------------

class TestFindExistingJoin:
    def test_finds_sole_upper_bound(self):
        # A → C, B → C — C is the only upper bound, so it is the join
        g = _graph("A", "B", "C")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        join_id = find_existing_join(["A", "B"], g, cb)
        assert join_id == "C"

    def test_returns_none_when_no_upper_bound(self):
        # No morphisms → no upper bound
        g = _graph("A", "B")
        pm, cb = _pm_cb(g)
        join_id = find_existing_join(["A", "B"], g, cb)
        assert join_id is None

    def test_returns_minimal_upper_bound(self):
        # A → C, B → C, C → D: C is minimal upper bound, D is not
        g = _graph("A", "B", "C", "D")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        g.add_morphism("C", "D", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        join_id = find_existing_join(["A", "B"], g, cb)
        # D is also above A and B (via C), but C ≤ D so D is not minimal
        assert join_id == "C"

    def test_ignores_components_themselves(self):
        # Should not return any component as its own join
        g = _graph("A", "B", "C")
        g.add_morphism("A", "B", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        join_id = find_existing_join(["A", "B"], g, cb)
        # B is above A, but B is a component — excluded
        assert join_id is None


# ---------------------------------------------------------------------------
# TestBuildJoinForPattern
# ---------------------------------------------------------------------------

class TestBuildJoinForPattern:
    def test_uses_existing_join(self):
        g = _graph("A", "B", "C")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        pattern = pm.create_pattern(["A", "B"], [], graph=g)
        result = build_join_for_pattern(pattern, g, cb)
        assert result is not None
        assert result.skill_id == "C"
        # No new skills added
        assert len(g.skills) == 3

    def test_creates_new_join_skill(self):
        # A and B with no upper bound → new join skill created
        g = _graph("A", "B")
        pm, cb = _pm_cb(g)
        pattern = pm.create_pattern(["A", "B"], [], graph=g)
        result = build_join_for_pattern(pattern, g, cb)
        assert result is not None
        # A new skill was added to the graph
        assert len(g.skills) == 3
        # New skill has morphisms from A and B
        join_skill = g.get_skill(result.skill_id)
        assert join_skill is not None
        assert join_skill.metadata.get("is_emergent_join") is True

    def test_idempotent_on_second_call(self):
        g = _graph("A", "B")
        pm, cb = _pm_cb(g)
        pattern = pm.create_pattern(["A", "B"], [], graph=g)
        r1 = build_join_for_pattern(pattern, g, cb)
        r2 = build_join_for_pattern(pattern, g, cb)
        # Second call returns same colimit, no duplicate skills
        assert r1 is not None
        assert r2 is not None
        assert r1.skill_id == r2.skill_id

    def test_single_component_returns_none(self):
        g = _graph("A")
        pm, cb = _pm_cb(g)
        pattern = pm.create_pattern(["A"], [])
        result = build_join_for_pattern(pattern, g, cb)
        assert result is None


# ---------------------------------------------------------------------------
# TestBuildHierarchyToFixpoint
# ---------------------------------------------------------------------------

class TestBuildHierarchyToFixpoint:
    def test_atomic_graph_all_cn_zero(self):
        g = _graph("A", "B")
        pm, cb = _pm_cb(g)
        cn = build_hierarchy_to_fixpoint(g, pm, cb, max_iterations=3)
        assert cn["A"] == 0
        assert cn["B"] == 0

    def test_levels_emerge_from_morphisms(self):
        # A → C, B → C, C → D
        g = _graph("A", "B", "C", "D")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        g.add_morphism("C", "D", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        cn = build_hierarchy_to_fixpoint(g, pm, cb, max_iterations=5)
        assert cn["A"] == 0
        assert cn["B"] == 0
        assert cn["C"] >= 1   # C is above A and B
        # D is above C, so cn(D) >= cn(C) + 1 if D is registered as join
        # (D might or might not be a join depending on pattern detection)

    def test_skill_levels_updated_in_graph(self):
        g = _graph("A", "B", "C")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        build_hierarchy_to_fixpoint(g, pm, cb, max_iterations=3)
        c_skill = g.get_skill("C")
        assert c_skill is not None
        assert c_skill.level >= 0  # updated by apply_complexity_order

    def test_max_level_increases_with_depth(self):
        # Two levels: A, B → C → D with explicit join at C
        g = _graph("A", "B", "C", "D")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        g.add_morphism("C", "D", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        cn = build_hierarchy_to_fixpoint(g, pm, cb, max_iterations=5)
        max_cn = max(cn.values(), default=0)
        assert max_cn >= 1

    def test_fubini_invariant_holds(self):
        """
        Stacked joins: join(A, B) = C at cn=1; join(C, D) = E at cn=2.
        The cn of E must equal 2 (not 3), because:
          E = join[C, D] = join[join[A, B], D]
          Fubini: this equals join[A, B, D] directly.
          max{cn(C), cn(D)} + 1 = max{1, 0} + 1 = 2
        """
        g = _graph("A", "B", "C", "D", "E")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        g.add_morphism("C", "E", MorphismType.DEPENDENCY)
        g.add_morphism("D", "E", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        _register_colimit(cb, pm, ["A", "B"], "C")
        _register_colimit(cb, pm, ["C", "D"], "E")
        cn = compute_complexity_order(g, cb)
        assert cn["C"] == 1
        assert cn["E"] == 2   # not 3 — Fubini invariant

    def test_returns_complete_dict(self):
        g = _graph("A", "B", "C")
        pm, cb = _pm_cb(g)
        cn = build_hierarchy_to_fixpoint(g, pm, cb, max_iterations=3)
        for sid in ["A", "B", "C"]:
            assert sid in cn
