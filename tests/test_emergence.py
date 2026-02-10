"""
Tests de Enlaces Simples/Complejos y Emergencia
=================================================

Verifica la implementacion de Def 6.3 y Thm 8.6 del documento v7.0:
- Clasificacion de enlaces: IDENTITY, SIMPLE, COMPLEX
- Deteccion de enlaces complejos (emergencia)
- Medicion de emergencia
"""

import pytest

from nucleo.types import (
    Skill, MorphismType, PillarType, LinkComplexity, Option,
)
from nucleo.graph.category import SkillCategory
from nucleo.graph.evolution import EvolutionarySystem
from nucleo.mes.patterns import PatternManager, ColimitBuilder


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def graph():
    """Grafo con skills en niveles 0 y 1."""
    g = SkillCategory(name="EmergenceTest")
    g.add_skill(Skill(id="s1", name="Atom1", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="s2", name="Atom2", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="s3", name="Atom3", pillar=PillarType.SET, level=0))
    g.add_morphism("s1", "s2", MorphismType.DEPENDENCY)
    g.add_morphism("s2", "s3", MorphismType.DEPENDENCY)
    return g


# =============================================================================
# LINK CLASSIFICATION (Def 6.3)
# =============================================================================

class TestLinkClassification:
    """Tests para clasificacion de enlaces."""

    def test_identity_link(self, graph):
        """Morfismo identidad es IDENTITY."""
        identity = graph.identity("s1")
        assert graph.classify_link(identity.id) == LinkComplexity.IDENTITY

    def test_direct_link_is_simple(self, graph):
        """Enlace directo s1->s2 es SIMPLE (sin colimite, pero directo)."""
        m = graph.hom("s1", "s2")[0]
        assert graph.classify_link(m.id) == LinkComplexity.SIMPLE

    def test_link_to_colimit_is_simple(self, graph):
        """Enlace a un colimite es SIMPLE."""
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        m12 = graph.hom("s1", "s2")[0]
        pattern = pm.create_pattern(["s1", "s2"], [m12.id], graph=graph)
        colimit_skill, colimit = cb.build_colimit(pattern, graph)

        # Cocone morphisms (s1 -> cP, s2 -> cP) are SIMPLE
        for morph_id in colimit.cocone_morphisms:
            assert graph.classify_link(morph_id) == LinkComplexity.SIMPLE

    def test_link_through_colimit_is_simple(self, graph):
        """Enlace que factoriza a traves de colimite es SIMPLE."""
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        m12 = graph.hom("s1", "s2")[0]
        pattern = pm.create_pattern(["s1", "s2"], [m12.id], graph=graph)
        colimit_skill, colimit = cb.build_colimit(pattern, graph)

        # Add another skill B that colimit maps to
        b = Skill(id="B", name="Target", level=0)
        graph.add_skill(b)
        graph.add_morphism(colimit_skill.id, "B", MorphismType.DEPENDENCY)

        # s1 also connects to B
        m_s1_b = graph.add_morphism("s1", "B", MorphismType.DEPENDENCY)

        # s1 -> B should be SIMPLE because s1 -> cP -> B factors through colimit
        assert graph.classify_link(m_s1_b.id) == LinkComplexity.SIMPLE

    def test_composed_link_without_colimit_is_complex(self, graph):
        """Composicion sin colimite intermedio es COMPLEX."""
        # Compose s1->s2->s3 (no colimits exist)
        f = graph.hom("s1", "s2")[0]
        g = graph.hom("s2", "s3")[0]
        composed = graph.compose(g.id, f.id)

        assert composed is not None
        assert graph.classify_link(composed.id) == LinkComplexity.COMPLEX

    def test_cross_level_link_is_complex(self, graph):
        """Enlace entre niveles no adyacentes es COMPLEX."""
        # Add a level-2 skill
        s_high = Skill(id="s_high", name="HighLevel", level=2)
        graph.add_skill(s_high)
        m = graph.add_morphism("s1", "s_high", MorphismType.DEPENDENCY)

        assert graph.classify_link(m.id) == LinkComplexity.COMPLEX

    def test_get_complex_links(self, graph):
        """get_complex_links retorna todos los enlaces complejos."""
        # Initially no complex links
        assert len(graph.get_complex_links()) == 0

        # Compose to create complex link
        f = graph.hom("s1", "s2")[0]
        g = graph.hom("s2", "s3")[0]
        graph.compose(g.id, f.id)

        complex_links = graph.get_complex_links()
        assert len(complex_links) == 1


# =============================================================================
# EMERGENCE DETECTION (Thm 8.6)
# =============================================================================

class TestEmergenceDetection:
    """Tests para deteccion de emergencia."""

    def test_no_emergence_initially(self, graph):
        """Sin emergencia en un grafo basico."""
        evo = EvolutionarySystem(graph)
        emergence = evo.measure_emergence()
        assert emergence["num_complex_links"] == 0
        assert emergence["emergence_ratio"] == 0.0

    def test_emergence_after_composition(self, graph):
        """Emergencia detectada despues de crear composicion."""
        evo = EvolutionarySystem(graph)

        # Create a composed morphism (complex link)
        f = graph.hom("s1", "s2")[0]
        g = graph.hom("s2", "s3")[0]
        graph.compose(g.id, f.id)

        emergence = evo.measure_emergence()
        assert emergence["num_complex_links"] == 1
        assert emergence["emergence_ratio"] > 0

    def test_emergence_growth_tracking(self, graph):
        """Crecimiento de emergencia entre pasos temporales."""
        evo = EvolutionarySystem(graph)

        # Step 1: add new skills and compose
        s4 = Skill(id="s4", name="Extra", level=0)
        graph.add_skill(s4)
        graph.add_morphism("s3", "s4", MorphismType.DEPENDENCY)
        evo.apply_option(Option(absorptions=["s4"]))

        # Step 2: create composition (complex link)
        f = graph.hom("s1", "s2")[0]
        g = graph.hom("s2", "s3")[0]
        graph.compose(g.id, f.id)
        evo.apply_option(Option())  # Empty option to advance time

        emergence = evo.measure_emergence()
        assert emergence["num_complex_links"] >= 1
        assert emergence["complexity_growth"] >= 0

    def test_detect_complex_links_current(self, graph):
        """detect_complex_links en tiempo actual."""
        evo = EvolutionarySystem(graph)

        f = graph.hom("s1", "s2")[0]
        g = graph.hom("s2", "s3")[0]
        graph.compose(g.id, f.id)

        complex_ids = evo.detect_complex_links()
        assert len(complex_ids) == 1

    def test_emergence_in_stats(self, graph):
        """Metricas de emergencia incluidas en stats."""
        evo = EvolutionarySystem(graph)
        stats = evo.stats
        assert "emergence" in stats
        assert "num_complex_links" in stats["emergence"]


# =============================================================================
# COLIMIT EMERGENCE INTERACTION
# =============================================================================

class TestColimitEmergence:
    """Tests para interaccion entre colimites y emergencia."""

    def test_colimit_reduces_complexity(self, graph):
        """Crear colimite puede simplificar enlaces (factorizacion)."""
        pm = PatternManager()
        cb = ColimitBuilder(pm)

        # Create a pattern and colimit
        m12 = graph.hom("s1", "s2")[0]
        pattern = pm.create_pattern(["s1", "s2"], [m12.id], graph=graph)
        colimit_skill, colimit = cb.build_colimit(pattern, graph)

        # Links to/from colimit are SIMPLE
        for mid in colimit.cocone_morphisms:
            assert graph.classify_link(mid) == LinkComplexity.SIMPLE

    def test_binding_option_adds_emergence_structure(self, graph):
        """Option de ligadura agrega estructura que permite emergencia."""
        evo = EvolutionarySystem(graph)
        pm = evo.pattern_manager

        m12 = graph.hom("s1", "s2")[0]
        pattern = pm.create_pattern(["s1", "s2"], [m12.id], graph=graph)

        evo.apply_option(Option(bindings=[pattern.id]))

        # Colimit should exist now
        assert evo.colimit_builder.has_colimit(pattern.id)

        # The new colimit skill should be at level 1
        colimit_obj = evo.colimit_builder.get_colimit_for_pattern(pattern.id)
        colimit_skill = graph.get_skill(colimit_obj.skill_id)
        assert colimit_skill.level == 1
