"""
Tests de Propiedades Formales (Axiomas 8.1-8.4, Teoremas 8.5-8.7)
==================================================================

Verifica que el sistema NLE v7.0 satisface las propiedades formales
especificadas en el documento MES.

Axiomas:
- 8.1 Hierarchy: >= 2 niveles jerarquicos
- 8.2 Multiplicity: Principio de multiplicidad de pilares
- 8.3 Connectivity: Debilmente conexa + inter-pilar
- 8.4 Coverage: Todo skill cubierto por al menos un pilar

Teoremas:
- 8.5 Consistency: Complejificacion preserva axiomas
- 8.6 Emergence: Merge con enlace complejo produce emergencia
- 8.7 Coverage Preservation: Cobertura se mantiene bajo transicion
"""

import pytest

from nucleo.types import (
    Skill, Morphism, MorphismType, PillarType, Option, LinkComplexity,
)
from nucleo.graph.category import SkillCategory
from nucleo.graph.evolution import EvolutionarySystem
from nucleo.mes.patterns import PatternManager, ColimitBuilder, Pattern


# =============================================================================
# HELPERS
# =============================================================================

def _build_foundational_graph() -> SkillCategory:
    """Build a graph that satisfies all 4 axioms."""
    g = SkillCategory(name="TestGraph")

    # Level 0: foundational skills (4 pillars)
    g.add_skill(Skill(id="zfc", name="ZFC", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="cat", name="Category", pillar=PillarType.CAT, level=0))
    g.add_skill(Skill(id="fol", name="FOL", pillar=PillarType.LOG, level=0))
    g.add_skill(Skill(id="cic", name="CIC", pillar=PillarType.TYPE, level=0))

    # Level 1: derived skills
    g.add_skill(Skill(id="group-theory", name="Group Theory", pillar=PillarType.SET, level=1))
    g.add_skill(Skill(id="functor", name="Functor", pillar=PillarType.CAT, level=1))

    # Internal morphisms
    g.add_morphism("zfc", "group-theory", MorphismType.DEPENDENCY)
    g.add_morphism("cat", "functor", MorphismType.DEPENDENCY)

    # Inter-pillar translations (8.3 connectivity — must form a connected graph)
    g.add_morphism("fol", "cic", MorphismType.TRANSLATION,
                   metadata={"translation": "curry-howard"})
    g.add_morphism("zfc", "cat", MorphismType.ANALOGY,
                   metadata={"analogy": "sets-as-categories"})
    # Connect LOG/TYPE to SET/CAT to ensure weak connectivity
    g.add_morphism("cic", "cat", MorphismType.TRANSLATION,
                   metadata={"translation": "type-to-category"})

    # Connect derived to other pillars for coverage
    g.add_morphism("group-theory", "functor", MorphismType.ANALOGY)

    return g


def _build_minimal_graph() -> SkillCategory:
    """Build minimal graph with 2 levels, 2 pillars, connected."""
    g = SkillCategory(name="Minimal")

    g.add_skill(Skill(id="a", name="A", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="b", name="B", pillar=PillarType.LOG, level=1))

    g.add_morphism("a", "b", MorphismType.TRANSLATION)

    return g


# =============================================================================
# AXIOM 8.1: HIERARCHY
# =============================================================================

class TestAxiom81Hierarchy:
    """Axiom 8.1: G_t has >= 2 hierarchical levels."""

    def test_foundational_graph_has_hierarchy(self):
        """Foundational graph has >= 2 levels."""
        g = _build_foundational_graph()
        result = g._verify_hierarchy()
        assert result["satisfies"] is True
        assert result["num_levels"] >= 2

    def test_single_level_fails(self):
        """Single-level graph violates axiom."""
        g = SkillCategory(name="Flat")
        g.add_skill(Skill(id="a", name="A", pillar=PillarType.SET, level=0))
        g.add_skill(Skill(id="b", name="B", pillar=PillarType.LOG, level=0))
        g.add_morphism("a", "b", MorphismType.TRANSLATION)

        result = g._verify_hierarchy()
        assert result["satisfies"] is False
        assert result["num_levels"] == 1

    def test_categorical_axioms_checked(self):
        """Hierarchy check also verifies categorical axioms."""
        g = _build_foundational_graph()
        result = g._verify_hierarchy()
        assert "categorical_axioms" in result
        assert all(result["categorical_axioms"].values())


# =============================================================================
# AXIOM 8.2: MULTIPLICITY
# =============================================================================

class TestAxiom82Multiplicity:
    """Axiom 8.2: Pillar multiplicity principle holds."""

    def test_foundational_graph_has_multiplicity(self):
        """Foundational graph with translations satisfies multiplicity."""
        g = _build_foundational_graph()
        result = g.verify_pillar_multiplicity()
        assert result["satisfies"] is True
        assert result["num_pillars"] >= 2

    def test_single_pillar_fails(self):
        """Single pillar violates multiplicity."""
        g = SkillCategory(name="SinglePillar")
        g.add_skill(Skill(id="a", name="A", pillar=PillarType.SET, level=0))
        g.add_skill(Skill(id="b", name="B", pillar=PillarType.SET, level=1))
        g.add_morphism("a", "b", MorphismType.DEPENDENCY)

        result = g.verify_pillar_multiplicity()
        assert result["satisfies"] is False

    def test_translations_counted(self):
        """Translations between pillars are counted."""
        g = _build_foundational_graph()
        result = g.verify_pillar_multiplicity()
        assert result["num_translations"] > 0


# =============================================================================
# AXIOM 8.3: CONNECTIVITY
# =============================================================================

class TestAxiom83Connectivity:
    """Axiom 8.3: G_t is weakly connected with inter-pillar connections."""

    def test_foundational_graph_connected(self):
        """Foundational graph is weakly connected."""
        g = _build_foundational_graph()
        result = g._verify_connectivity_full()
        assert result["satisfies"] is True
        assert result["weakly_connected"] is True
        assert result["inter_pillar_connections"] > 0

    def test_disconnected_fails(self):
        """Disconnected graph violates axiom."""
        g = SkillCategory(name="Disconnected")
        g.add_skill(Skill(id="a", name="A", pillar=PillarType.SET, level=0))
        g.add_skill(Skill(id="b", name="B", pillar=PillarType.LOG, level=0))
        # No morphisms between them

        result = g._verify_connectivity_full()
        assert result["weakly_connected"] is False
        assert result["satisfies"] is False

    def test_no_inter_pillar_fails(self):
        """Connected but no inter-pillar connections violates axiom."""
        g = SkillCategory(name="NoInterPillar")
        g.add_skill(Skill(id="a", name="A", pillar=PillarType.SET, level=0))
        g.add_skill(Skill(id="b", name="B", pillar=PillarType.SET, level=1))
        g.add_morphism("a", "b", MorphismType.DEPENDENCY)

        result = g._verify_connectivity_full()
        assert result["weakly_connected"] is True
        assert result["inter_pillar_connections"] == 0
        assert result["satisfies"] is False


# =============================================================================
# AXIOM 8.4: COVERAGE
# =============================================================================

class TestAxiom84Coverage:
    """Axiom 8.4: Every skill covered by at least one pillar."""

    def test_foundational_graph_fully_covered(self):
        """All skills in foundational graph are covered."""
        g = _build_foundational_graph()
        result = g._verify_coverage()
        assert result["satisfies"] is True
        assert result["coverage_ratio"] == 1.0
        assert result["uncovered_skills"] == []

    def test_isolated_skill_uncovered(self):
        """Isolated skill with no pillar is not covered."""
        g = _build_foundational_graph()
        # Add an isolated skill (no pillar, no connections)
        g.add_skill(Skill(id="orphan", name="Orphan", level=0))

        result = g._verify_coverage()
        assert result["satisfies"] is False
        assert "orphan" in result["uncovered_skills"]

    def test_reachable_skill_covered(self):
        """Skill reachable from pillar skill is covered."""
        g = SkillCategory(name="Reachable")
        g.add_skill(Skill(id="zfc", name="ZFC", pillar=PillarType.SET, level=0))
        g.add_skill(Skill(id="derived", name="Derived", level=1))
        g.add_morphism("zfc", "derived", MorphismType.DEPENDENCY)

        result = g._verify_coverage()
        assert result["satisfies"] is True
        assert result["covered_skills"] == 2


# =============================================================================
# VERIFY ALL AXIOMS
# =============================================================================

class TestVerifyAllAxioms:
    """Test the combined axiom verification."""

    def test_foundational_graph_satisfies_all(self):
        """Foundational graph satisfies all 4 axioms."""
        g = _build_foundational_graph()
        result = g.verify_all_axioms()
        assert result["all_satisfied"] is True
        assert result["8.1_hierarchy"]["satisfies"] is True
        assert result["8.2_multiplicity"]["satisfies"] is True
        assert result["8.3_connectivity"]["satisfies"] is True
        assert result["8.4_coverage"]["satisfies"] is True

    def test_minimal_graph_satisfies_all(self):
        """Minimal graph with 2 levels + inter-pillar satisfies all."""
        g = _build_minimal_graph()
        result = g.verify_all_axioms()
        assert result["all_satisfied"] is True

    def test_empty_graph_fails(self):
        """Empty graph does not satisfy axioms."""
        g = SkillCategory(name="Empty")
        result = g.verify_all_axioms()
        assert result["all_satisfied"] is False


# =============================================================================
# THEOREM 8.5: CONSISTENCY
# =============================================================================

class TestTheorem85Consistency:
    """Thm 8.5: Complexification preserves axioms."""

    def test_initial_consistency(self):
        """Initial graph is consistent."""
        g = _build_foundational_graph()
        evo = EvolutionarySystem(g)
        result = evo.verify_consistency()
        assert result["satisfies"] is True

    def test_consistency_after_absorption(self):
        """Axioms hold after absorbing a new skill."""
        g = _build_foundational_graph()
        evo = EvolutionarySystem(g)

        new_skill = Skill(
            id="topology", name="Topology",
            pillar=PillarType.SET, level=1,
        )
        option = Option(absorptions=[new_skill])
        evo.apply_option(option)

        # Need to connect the new skill so coverage is maintained
        g.add_morphism("zfc", "topology", MorphismType.DEPENDENCY)

        result = evo.verify_consistency()
        assert result["satisfies"] is True

    def test_consistency_after_elimination(self):
        """Axioms hold after eliminating a skill (if still valid)."""
        g = _build_foundational_graph()
        evo = EvolutionarySystem(g)

        # Eliminate a non-critical level-1 skill
        option = Option(eliminations=["functor"])
        evo.apply_option(option)

        result = evo.verify_consistency()
        assert result["satisfies"] is True


# =============================================================================
# THEOREM 8.6: EMERGENCE
# =============================================================================

class TestTheorem86Emergence:
    """Thm 8.6: Merge with complex link produces emergence."""

    def test_emergence_at_t0(self):
        """Emergence is trivially satisfied at t=0."""
        g = _build_foundational_graph()
        evo = EvolutionarySystem(g)
        result = evo.verify_emergence_growth()
        assert result["satisfies"] is True

    def test_emergence_measured(self):
        """Emergence metrics are computed."""
        g = _build_foundational_graph()
        evo = EvolutionarySystem(g)
        result = evo.measure_emergence()
        assert "num_complex_links" in result
        assert "max_level" in result
        assert "emergence_ratio" in result

    def test_emergence_after_complexification(self):
        """After adding skills, emergence check passes."""
        g = _build_foundational_graph()
        evo = EvolutionarySystem(g)

        # Apply an option that adds structure
        new_skill = Skill(
            id="homological", name="Homological Algebra",
            pillar=PillarType.CAT, level=2,
        )
        option = Option(absorptions=[new_skill])
        evo.apply_option(option)
        g.add_morphism("functor", "homological", MorphismType.DEPENDENCY)

        result = evo.verify_emergence_growth()
        assert result["satisfies"] is True


# =============================================================================
# THEOREM 8.7: COVERAGE PRESERVATION
# =============================================================================

class TestTheorem87CoveragePreservation:
    """Thm 8.7: Coverage preserved under complexification."""

    def test_initial_coverage_preserved(self):
        """Coverage is maintained at t=0."""
        g = _build_foundational_graph()
        evo = EvolutionarySystem(g)
        result = evo.verify_coverage_preservation()
        assert result["satisfies"] is True
        assert result["coverage_ratio"] == 1.0

    def test_coverage_after_absorption(self):
        """Coverage holds after absorbing connected skill."""
        g = _build_foundational_graph()
        evo = EvolutionarySystem(g)

        new_skill = Skill(
            id="measure-theory", name="Measure Theory",
            pillar=PillarType.SET, level=1,
        )
        option = Option(absorptions=[new_skill])
        evo.apply_option(option)

        # Connect to existing skill
        g.add_morphism("zfc", "measure-theory", MorphismType.DEPENDENCY)

        result = evo.verify_coverage_preservation()
        assert result["satisfies"] is True

    def test_coverage_after_binding(self):
        """Coverage holds after binding (colimit creation)."""
        g = _build_foundational_graph()
        pm = PatternManager()
        evo = EvolutionarySystem(g, pattern_manager=pm)

        # Get the morphism ID linking zfc→cat for the pattern
        morph_ids = []
        pair_key = ("zfc", "cat")
        if pair_key in g._morphism_pairs:
            morph_ids.append(g._morphism_pairs[pair_key])

        # Create a pattern and bind it
        pattern = pm.create_pattern(
            component_ids=["zfc", "cat"],
            distinguished_links=morph_ids,
            graph=g,
        )
        option = Option(bindings=[pattern.id])
        evo.apply_option(option)

        result = evo.verify_coverage_preservation()
        assert result["satisfies"] is True


# =============================================================================
# VERIFY ALL THEOREMS
# =============================================================================

class TestVerifyAllTheorems:
    """Test the combined theorem verification."""

    def test_all_theorems_on_foundational_graph(self):
        """All theorems hold on foundational graph."""
        g = _build_foundational_graph()
        evo = EvolutionarySystem(g)
        result = evo.verify_all_theorems()
        assert result["all_satisfied"] is True
        assert result["8.5_consistency"]["satisfies"] is True
        assert result["8.6_emergence"]["satisfies"] is True
        assert result["8.7_coverage_preservation"]["satisfies"] is True

    def test_all_theorems_after_evolution(self):
        """All theorems hold after a round of evolution."""
        g = _build_foundational_graph()
        evo = EvolutionarySystem(g)

        # Evolution step 1: absorb
        option1 = Option(absorptions=[
            Skill(id="ring-theory", name="Ring Theory",
                  pillar=PillarType.SET, level=1),
        ])
        evo.apply_option(option1)
        g.add_morphism("zfc", "ring-theory", MorphismType.DEPENDENCY)

        result = evo.verify_all_theorems()
        assert result["all_satisfied"] is True
