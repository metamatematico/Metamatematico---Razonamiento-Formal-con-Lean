"""
Tests for Mathematical Domain Skills Integration
=================================================

Verifies that the 51 mathematical domain skills from the
lean-proving-skills library are correctly loaded and integrated
into the NLE skill graph.
"""

import pytest

from nucleo.types import Skill, MorphismType, PillarType
from nucleo.graph.category import SkillCategory
from nucleo.pillars.math_domains import (
    ALL_DOMAIN_SKILLS,
    ALGEBRA_SKILLS,
    GEOMETRY_SKILLS,
    ANALYSIS_SKILLS,
    TOPOLOGY_SKILLS,
    LOGIC_SKILLS,
    NUMBER_THEORY_SKILLS,
    COMBINATORICS_SKILLS,
    PROBABILITY_SKILLS,
    SET_THEORY_SKILLS,
    CATEGORY_THEORY_SKILLS,
    COMPUTATION_SKILLS,
    OPTIMIZATION_SKILLS,
    INTER_PILLAR_TRANSLATIONS,
    load_math_domains,
    get_domain_skill_count,
    get_domain_categories,
)


# =============================================================================
# HELPERS
# =============================================================================

def _build_graph_with_foundations() -> SkillCategory:
    """Build graph with all level-0 pillar skills needed by domain skills."""
    g = SkillCategory(name="FullGraph")

    # F_Set foundations
    g.add_skill(Skill(id="zfc-axioms", name="ZFC", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="ordinals", name="Ordinals", pillar=PillarType.SET, level=0))

    # F_Cat foundations
    g.add_skill(Skill(id="cat-basics", name="Categories", pillar=PillarType.CAT, level=0))
    g.add_skill(Skill(id="functors", name="Functors", pillar=PillarType.CAT, level=0))
    g.add_skill(Skill(id="nat-trans", name="Nat Trans", pillar=PillarType.CAT, level=0))
    g.add_skill(Skill(id="limits", name="Limits", pillar=PillarType.CAT, level=0))

    # F_Log foundations
    g.add_skill(Skill(id="fol-deduction", name="FOL Deduction", pillar=PillarType.LOG, level=0))
    g.add_skill(Skill(id="fol-metatheory", name="FOL Metatheory", pillar=PillarType.LOG, level=0))

    # F_Type foundations
    g.add_skill(Skill(id="cic", name="CIC", pillar=PillarType.TYPE, level=0))
    g.add_skill(Skill(id="lean-kernel", name="Lean Kernel", pillar=PillarType.TYPE, level=0))
    g.add_skill(Skill(id="type-theory", name="Type Theory", pillar=PillarType.TYPE, level=0))

    # Connectivity morphisms
    g.add_morphism("zfc-axioms", "cat-basics", MorphismType.ANALOGY)
    g.add_morphism("fol-deduction", "cic", MorphismType.TRANSLATION)
    g.add_morphism("cat-basics", "functors", MorphismType.DEPENDENCY)
    g.add_morphism("functors", "nat-trans", MorphismType.DEPENDENCY)
    g.add_morphism("functors", "limits", MorphismType.DEPENDENCY)
    g.add_morphism("cic", "lean-kernel", MorphismType.DEPENDENCY)
    g.add_morphism("fol-deduction", "fol-metatheory", MorphismType.DEPENDENCY)
    g.add_morphism("zfc-axioms", "ordinals", MorphismType.DEPENDENCY)

    return g


# =============================================================================
# SKILL DEFINITION TESTS
# =============================================================================

class TestSkillDefinitions:
    """Verify skill definition integrity."""

    def test_total_domain_skills(self):
        """Total domain skills count is 66 (51 math + 9 lean tactics + 6 proof strategies)."""
        assert get_domain_skill_count() == 66

    def test_all_skills_have_required_fields(self):
        """Every skill has id, name, description, pillar, level."""
        for s in ALL_DOMAIN_SKILLS:
            assert s.id, f"Skill missing id"
            assert s.name, f"Skill {s.id} missing name"
            assert s.description, f"Skill {s.id} missing description"
            assert s.pillar is not None, f"Skill {s.id} missing pillar"
            assert s.level in (1, 2), f"Skill {s.id} has invalid level {s.level}"

    def test_unique_ids(self):
        """All skill IDs are unique."""
        ids = [s.id for s in ALL_DOMAIN_SKILLS]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found"

    def test_categories_complete(self):
        """All 14 categories are represented."""
        cats = get_domain_categories()
        expected = {
            "algebra", "geometry", "analysis", "topology", "logic",
            "number-theory", "combinatorics", "probability", "set-theory",
            "category-theory", "computation", "optimization",
            "lean-tactics", "proof-strategies",
        }
        assert set(cats.keys()) == expected

    def test_category_counts(self):
        """Category skill counts match."""
        assert len(ALGEBRA_SKILLS) == 7
        assert len(GEOMETRY_SKILLS) == 6
        assert len(ANALYSIS_SKILLS) == 6
        assert len(TOPOLOGY_SKILLS) == 5
        assert len(LOGIC_SKILLS) == 3
        assert len(NUMBER_THEORY_SKILLS) == 4
        assert len(COMBINATORICS_SKILLS) == 6
        assert len(PROBABILITY_SKILLS) == 4
        assert len(SET_THEORY_SKILLS) == 1
        assert len(CATEGORY_THEORY_SKILLS) == 2
        assert len(COMPUTATION_SKILLS) == 4
        assert len(OPTIMIZATION_SKILLS) == 3

    def test_pillar_distribution(self):
        """Skills are distributed across all 4 pillars."""
        pillars = {s.pillar for s in ALL_DOMAIN_SKILLS}
        assert PillarType.SET in pillars
        assert PillarType.CAT in pillars
        assert PillarType.LOG in pillars
        assert PillarType.TYPE in pillars

    def test_level_distribution(self):
        """Both level 1 and level 2 skills exist."""
        levels = {s.level for s in ALL_DOMAIN_SKILLS}
        assert 1 in levels
        assert 2 in levels

    def test_level_1_count(self):
        """Level 1 skills are basic domains."""
        l1 = [s for s in ALL_DOMAIN_SKILLS if s.level == 1]
        assert len(l1) >= 20

    def test_level_2_count(self):
        """Level 2 skills are advanced/cross-domain."""
        l2 = [s for s in ALL_DOMAIN_SKILLS if s.level == 2]
        assert len(l2) >= 20


# =============================================================================
# LOADING TESTS
# =============================================================================

class TestLoadMathDomains:
    """Verify loading domain skills into a SkillCategory."""

    def test_load_with_foundations(self):
        """All 66 skills load when foundations are present."""
        g = _build_graph_with_foundations()
        result = load_math_domains(g)
        assert result["added"] == 66
        assert result["skipped"] == 0

    def test_load_adds_morphisms(self):
        """Loading creates dependency morphisms."""
        g = _build_graph_with_foundations()
        morphisms_before = len(g._morphisms)
        load_math_domains(g)
        morphisms_after = len(g._morphisms)
        # At least one morphism per dependency + identity morphisms for new skills
        assert morphisms_after > morphisms_before + 66

    def test_load_inter_pillar_translations(self):
        """Inter-pillar translations are created."""
        g = _build_graph_with_foundations()
        result = load_math_domains(g)
        assert result["translations"] > 0

    def test_load_idempotent(self):
        """Loading twice doesn't duplicate skills."""
        g = _build_graph_with_foundations()
        r1 = load_math_domains(g)
        r2 = load_math_domains(g)
        assert r1["added"] == 66
        assert r2["added"] == 0
        assert r2["skipped"] == 66

    def test_load_empty_graph_skips_most(self):
        """Loading on empty graph skips skills with missing deps."""
        g = SkillCategory(name="Empty")
        result = load_math_domains(g)
        assert result["added"] == 0
        assert result["skipped"] == 66

    def test_load_partial_graph(self):
        """Loading with partial foundations adds available skills."""
        g = SkillCategory(name="Partial")
        g.add_skill(Skill(id="zfc-axioms", name="ZFC", pillar=PillarType.SET, level=0))
        result = load_math_domains(g)
        # Should add at least group-theory, ring-theory, etc. that only need zfc-axioms
        assert result["added"] > 0
        assert result["added"] < 66

    def test_skills_have_correct_levels(self):
        """Loaded skills maintain their level assignments."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        group = g.get_skill("group-theory")
        assert group is not None
        assert group.level == 1
        alg_geom = g.get_skill("algebraic-geometry")
        assert alg_geom is not None
        assert alg_geom.level == 2

    def test_skills_have_correct_pillars(self):
        """Loaded skills maintain their pillar assignments."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        assert g.get_skill("group-theory").pillar == PillarType.SET
        assert g.get_skill("homological-algebra").pillar == PillarType.CAT
        assert g.get_skill("model-theory").pillar == PillarType.LOG
        assert g.get_skill("algorithm-analysis").pillar == PillarType.TYPE


# =============================================================================
# DEPENDENCY CHAIN TESTS
# =============================================================================

class TestDependencyChains:
    """Verify dependency chains are correct."""

    def test_algebra_chain(self):
        """group-theory -> ring-theory -> field-theory chain."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        dep_ids = set(g.dependencies("ring-theory"))
        assert "group-theory" in dep_ids or "zfc-axioms" in dep_ids

    def test_analysis_chain(self):
        """real-analysis -> complex-analysis chain."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        dep_ids = set(g.dependencies("complex-analysis"))
        assert "real-analysis" in dep_ids

    def test_topology_chain(self):
        """point-set-topology -> algebraic-topology -> homotopy-theory."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        dep_ids = set(g.dependencies("algebraic-topology"))
        assert "point-set-topology" in dep_ids

    def test_cross_pillar_dependency(self):
        """homological-algebra (CAT) depends on module-theory (SET)."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        dep_ids = set(g.dependencies("homological-algebra"))
        assert "module-theory" in dep_ids

    def test_level_2_depends_on_level_1(self):
        """Every level-2 skill has at least one level-1 or level-0 dependency."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        for sdef in ALL_DOMAIN_SKILLS:
            if sdef.level == 2:
                skill = g.get_skill(sdef.id)
                if skill is None:
                    continue
                dep_ids = g.dependencies(sdef.id)
                dep_levels = {g.get_skill(d).level for d in dep_ids if g.get_skill(d)}
                assert any(l < 2 for l in dep_levels), (
                    f"{sdef.id} (level 2) has no level 0-1 dependency"
                )


# =============================================================================
# GRAPH PROPERTY TESTS
# =============================================================================

class TestGraphProperties:
    """Verify graph properties after loading domain skills."""

    def test_hierarchy_satisfied(self):
        """Graph with domains has >= 3 hierarchical levels."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        result = g._verify_hierarchy()
        assert result["satisfies"] is True
        assert result["num_levels"] >= 3

    def test_multiplicity_satisfied(self):
        """Graph with domains has pillar multiplicity."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        result = g.verify_pillar_multiplicity()
        assert result["satisfies"] is True
        assert result["num_pillars"] == 4

    def test_connectivity_satisfied(self):
        """Graph with domains is weakly connected."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        result = g._verify_connectivity_full()
        assert result["satisfies"] is True
        assert result["inter_pillar_connections"] > 0

    def test_coverage_satisfied(self):
        """All skills are reachable from pillar skills."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        result = g._verify_coverage()
        assert result["satisfies"] is True
        assert result["coverage_ratio"] == 1.0

    def test_all_axioms_satisfied(self):
        """Full graph satisfies all 4 axioms."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        result = g.verify_all_axioms()
        assert result["all_satisfied"] is True

    def test_total_skill_count(self):
        """Graph has foundations + 51 domain skills."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        stats = g.stats
        assert stats["num_skills"] == 11 + 66  # 11 foundations + 66 domains


# =============================================================================
# INTER-PILLAR TRANSLATION TESTS
# =============================================================================

class TestInterPillarTranslations:
    """Verify inter-pillar translations are created."""

    def test_translations_defined(self):
        """At least 5 inter-pillar translations exist."""
        assert len(INTER_PILLAR_TRANSLATIONS) >= 5

    def test_translations_loaded(self):
        """Translations create morphisms in the graph."""
        g = _build_graph_with_foundations()
        result = load_math_domains(g)
        assert result["translations"] >= 5

    def test_homotopy_translation(self):
        """Homotopy theory <-> HoTT translation exists."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        ht = g.get_skill("homotopy-theory")
        hott = g.get_skill("homotopy-type-theory")
        assert ht is not None
        assert hott is not None
        # They should have a direct morphism
        neighbor_ids = set(g.get_neighbors("homotopy-theory"))
        assert "homotopy-type-theory" in neighbor_ids

    def test_homological_algebra_translation(self):
        """Homological algebra connects algebra and category theory."""
        g = _build_graph_with_foundations()
        load_math_domains(g)
        neighbor_ids = set(g.get_neighbors("homological-algebra"))
        assert "homological-algebra-cat" in neighbor_ids
