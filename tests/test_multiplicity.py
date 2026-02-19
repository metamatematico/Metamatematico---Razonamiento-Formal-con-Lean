"""
Tests del Principio de Multiplicidad
======================================

Verifica la implementacion de Def 2.5, Axioma 8.2 y Prop 3.4 del documento v7.0:
- Homologia de patrones (campo operativo isomorfo)
- Principio de multiplicidad (patrones homologos no conectados)
- Multiplicidad via pilares fundacionales
"""

import pytest

from nucleo.types import Skill, MorphismType, PillarType, Pattern
from nucleo.graph.category import SkillCategory
from nucleo.mes.patterns import PatternManager, ColimitBuilder


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def graph_two_pillars():
    """
    Grafo con skills en SET y LOG que representan el mismo concepto.
    SET: s1 -> s2 (implicacion via conjuntos)
    LOG: l1 -> l2 (implicacion via logica)
    """
    g = SkillCategory(name="MultiplicityTest")
    # SET pillar
    g.add_skill(Skill(id="s1", name="SetPremise", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="s2", name="SetConclusion", pillar=PillarType.SET, level=0))
    g.add_morphism("s1", "s2", MorphismType.DEPENDENCY)
    # LOG pillar
    g.add_skill(Skill(id="l1", name="LogPremise", pillar=PillarType.LOG, level=0))
    g.add_skill(Skill(id="l2", name="LogConclusion", pillar=PillarType.LOG, level=0))
    g.add_morphism("l1", "l2", MorphismType.DEPENDENCY)
    return g


@pytest.fixture
def pm():
    return PatternManager()


@pytest.fixture
def cb(pm):
    return ColimitBuilder(pm)


# =============================================================================
# HOMOLOGY (Def 2.5)
# =============================================================================

class TestHomology:
    """Tests para verificacion de homologia."""

    def test_same_structure_different_pillars_are_homologous(
        self, graph_two_pillars, pm
    ):
        """Patrones con misma estructura y pilares distintos son homologos."""
        m_set = graph_two_pillars.hom("s1", "s2")[0]
        m_log = graph_two_pillars.hom("l1", "l2")[0]

        p_set = pm.create_pattern(
            ["s1", "s2"], [m_set.id], graph=graph_two_pillars
        )
        p_log = pm.create_pattern(
            ["l1", "l2"], [m_log.id], graph=graph_two_pillars
        )

        assert pm.are_homologous(p_set, p_log, graph_two_pillars) is True

    def test_same_components_not_homologous(self, graph_two_pillars, pm):
        """Patrones con exactamente los mismos componentes NO son homologos."""
        m_set = graph_two_pillars.hom("s1", "s2")[0]

        p1 = pm.create_pattern(
            ["s1", "s2"], [m_set.id], graph=graph_two_pillars
        )
        p2 = pm.create_pattern(
            ["s1", "s2"], [m_set.id], graph=graph_two_pillars
        )

        assert pm.are_homologous(p1, p2, graph_two_pillars) is False

    def test_different_size_not_homologous(self, graph_two_pillars, pm):
        """Patrones de tamanos distintos NO son homologos."""
        m_set = graph_two_pillars.hom("s1", "s2")[0]

        p1 = pm.create_pattern(
            ["s1", "s2"], [m_set.id], graph=graph_two_pillars
        )
        p2 = pm.create_pattern(
            ["l1"], [], graph=graph_two_pillars
        )

        assert pm.are_homologous(p1, p2, graph_two_pillars) is False

    def test_homologous_with_colimits(self, graph_two_pillars, pm, cb):
        """Homologia via campos operativos cuando hay colimites."""
        m_set = graph_two_pillars.hom("s1", "s2")[0]
        m_log = graph_two_pillars.hom("l1", "l2")[0]

        p_set = pm.create_pattern(
            ["s1", "s2"], [m_set.id], graph=graph_two_pillars
        )
        p_log = pm.create_pattern(
            ["l1", "l2"], [m_log.id], graph=graph_two_pillars
        )

        # Build colimits
        cb.build_colimit(p_set, graph_two_pillars)
        cb.build_colimit(p_log, graph_two_pillars)

        # Should still be homologous (same operational field structure)
        assert pm.are_homologous(
            p_set, p_log, graph_two_pillars, colimit_builder=cb
        ) is True

    def test_find_homologous_patterns(self, graph_two_pillars, pm):
        """find_homologous_patterns encuentra todos los pares."""
        m_set = graph_two_pillars.hom("s1", "s2")[0]
        m_log = graph_two_pillars.hom("l1", "l2")[0]

        p_set = pm.create_pattern(
            ["s1", "s2"], [m_set.id], graph=graph_two_pillars
        )
        p_log = pm.create_pattern(
            ["l1", "l2"], [m_log.id], graph=graph_two_pillars
        )

        homologous = pm.find_homologous_patterns(p_set, graph_two_pillars)
        assert len(homologous) == 1
        assert homologous[0].id == p_log.id


# =============================================================================
# MULTIPLICITY PRINCIPLE (Axioma 8.2)
# =============================================================================

class TestMultiplicityPrinciple:
    """Tests para el principio de multiplicidad."""

    def test_multiplicity_with_two_disconnected_patterns(
        self, graph_two_pillars, pm
    ):
        """Grafo con patrones homologos no conectados satisface multiplicidad."""
        m_set = graph_two_pillars.hom("s1", "s2")[0]
        m_log = graph_two_pillars.hom("l1", "l2")[0]

        pm.create_pattern(
            ["s1", "s2"], [m_set.id], graph=graph_two_pillars
        )
        pm.create_pattern(
            ["l1", "l2"], [m_log.id], graph=graph_two_pillars
        )

        result = pm.verify_multiplicity_principle(graph_two_pillars)
        assert result["satisfies"] is True
        assert len(result["homologous_pairs"]) >= 1
        assert len(result["disconnected_pairs"]) >= 1

    def test_multiplicity_fails_single_pattern(self, graph_two_pillars, pm):
        """Con un solo patron, multiplicidad no se satisface."""
        m_set = graph_two_pillars.hom("s1", "s2")[0]
        pm.create_pattern(
            ["s1", "s2"], [m_set.id], graph=graph_two_pillars
        )

        result = pm.verify_multiplicity_principle(graph_two_pillars)
        assert result["satisfies"] is False
        assert len(result["violations"]) > 0

    def test_multiplicity_fails_connected_patterns(self, graph_two_pillars, pm):
        """Patrones homologos conectados por cluster no satisfacen multiplicidad."""
        m_set = graph_two_pillars.hom("s1", "s2")[0]
        m_log = graph_two_pillars.hom("l1", "l2")[0]

        pm.create_pattern(
            ["s1", "s2"], [m_set.id], graph=graph_two_pillars
        )
        pm.create_pattern(
            ["l1", "l2"], [m_log.id], graph=graph_two_pillars
        )

        # Connect the two patterns via a cluster link
        graph_two_pillars.add_morphism(
            "s1", "l1", MorphismType.TRANSLATION
        )

        result = pm.verify_multiplicity_principle(graph_two_pillars)
        # Now they're connected, so disconnected_pairs should be empty
        assert result["satisfies"] is False


# =============================================================================
# PILLAR MULTIPLICITY (Prop 3.4)
# =============================================================================

class TestPillarMultiplicity:
    """Tests para multiplicidad via pilares."""

    def test_single_pillar_no_multiplicity(self):
        """Grafo con un solo pilar NO satisface multiplicidad de pilares."""
        g = SkillCategory(name="SinglePillar")
        g.add_skill(Skill(id="s1", name="A", pillar=PillarType.SET, level=0))
        g.add_skill(Skill(id="s2", name="B", pillar=PillarType.SET, level=0))
        g.add_morphism("s1", "s2", MorphismType.DEPENDENCY)

        result = g.verify_pillar_multiplicity()
        assert result["satisfies"] is False
        assert result["num_pillars"] == 1

    def test_two_pillars_no_translation(self):
        """Dos pilares sin traducciones NO satisfacen (falta conexion)."""
        g = SkillCategory(name="NoTranslation")
        g.add_skill(Skill(id="s1", name="A", pillar=PillarType.SET, level=0))
        g.add_skill(Skill(id="l1", name="B", pillar=PillarType.LOG, level=0))
        # DEPENDENCY, not TRANSLATION
        g.add_morphism("s1", "l1", MorphismType.DEPENDENCY)

        result = g.verify_pillar_multiplicity()
        assert result["satisfies"] is False

    def test_two_pillars_with_translation(self, graph_two_pillars):
        """Dos pilares con traduccion satisfacen multiplicidad de pilares."""
        graph_two_pillars.add_morphism(
            "s1", "l1", MorphismType.TRANSLATION
        )

        result = graph_two_pillars.verify_pillar_multiplicity()
        assert result["satisfies"] is True
        assert result["num_translations"] >= 1

    def test_two_pillars_with_analogy(self, graph_two_pillars):
        """Dos pilares con analogia satisfacen multiplicidad."""
        graph_two_pillars.add_morphism(
            "s1", "l1", MorphismType.ANALOGY
        )

        result = graph_two_pillars.verify_pillar_multiplicity()
        assert result["satisfies"] is True
        assert result["num_analogies"] >= 1

    def test_four_pillars_full(self):
        """Grafo con 4 pilares y traducciones: plena multiplicidad."""
        g = SkillCategory(name="FullPillars")
        for p in PillarType:
            g.add_skill(Skill(
                id=f"sk_{p.name}", name=f"Skill_{p.name}",
                pillar=p, level=0
            ))

        # Add translations between consecutive pillars
        pillars = list(PillarType)
        for i in range(len(pillars) - 1):
            g.add_morphism(
                f"sk_{pillars[i].name}",
                f"sk_{pillars[i+1].name}",
                MorphismType.TRANSLATION,
            )

        result = g.verify_pillar_multiplicity()
        assert result["satisfies"] is True
        assert result["num_pillars"] == 4
        assert result["num_translations"] >= 3
