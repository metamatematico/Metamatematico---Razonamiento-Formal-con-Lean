"""
Tests de Colimites y Propiedad Universal
=========================================

Verifica la implementacion de Def 2.1-2.2 y Teorema 2.10 del documento v7.0:
- Patron como funtor P: I -> K (datos de funtor)
- Co-cono valido (Def 2.2a: conmutatividad)
- Propiedad universal (Def 2.2b: existencia de morfismo mediador unico)
- Complejificacion (Thm 2.10)
"""

import pytest

from nucleo.types import Skill, Morphism, MorphismType, PillarType, Pattern, Colimit
from nucleo.graph.category import SkillCategory
from nucleo.mes.patterns import PatternManager, ColimitBuilder


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def graph():
    """Grafo base con 3 skills conectados: s1 -> s2 -> s3."""
    g = SkillCategory(name="TestColimit")
    s1 = Skill(id="s1", name="Axiom1", pillar=PillarType.SET, level=0)
    s2 = Skill(id="s2", name="Axiom2", pillar=PillarType.SET, level=0)
    s3 = Skill(id="s3", name="Axiom3", pillar=PillarType.SET, level=0)
    g.add_skill(s1)
    g.add_skill(s2)
    g.add_skill(s3)
    g.add_morphism("s1", "s2", MorphismType.DEPENDENCY)
    g.add_morphism("s2", "s3", MorphismType.DEPENDENCY)
    return g


@pytest.fixture
def pattern_mgr():
    """PatternManager limpio."""
    return PatternManager()


@pytest.fixture
def colimit_builder(pattern_mgr):
    """ColimitBuilder con PatternManager."""
    return ColimitBuilder(pattern_mgr)


# =============================================================================
# PATTERN AS DIAGRAM (Def 2.1)
# =============================================================================

class TestPatternAsDiagram:
    """Tests para Pattern como funtor P: I -> K."""

    def test_pattern_without_graph_has_no_diagram(self, pattern_mgr):
        """Pattern sin graph no tiene datos de funtor."""
        p = pattern_mgr.create_pattern(["s1", "s2"], ["m1"])
        assert not p.is_diagram
        assert p.index_objects == []
        assert p.functor_map_objects == {}

    def test_pattern_with_graph_is_diagram(self, graph, pattern_mgr):
        """Pattern con graph tiene datos de funtor completos."""
        m12 = graph.hom("s1", "s2")[0]
        p = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )
        assert p.is_diagram
        assert len(p.index_objects) == 2
        assert "0" in p.functor_map_objects
        assert "1" in p.functor_map_objects
        assert p.functor_map_objects["0"] == "s1"
        assert p.functor_map_objects["1"] == "s2"

    def test_pattern_functor_morphisms(self, graph, pattern_mgr):
        """Los datos de funtor incluyen los morfismos del diagrama."""
        m12 = graph.hom("s1", "s2")[0]
        p = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )
        assert len(p.index_morphisms) == 1
        d_name = "d_0_1"
        assert d_name in p.index_morphisms
        assert p.index_morphisms[d_name] == ("0", "1")
        assert p.functor_map_morphisms[d_name] == m12.id

    def test_pattern_three_components(self, graph, pattern_mgr):
        """Patron de 3 componentes con datos de funtor."""
        m12 = graph.hom("s1", "s2")[0]
        m23 = graph.hom("s2", "s3")[0]
        p = pattern_mgr.create_pattern(
            ["s1", "s2", "s3"], [m12.id, m23.id], graph=graph
        )
        assert p.is_diagram
        assert len(p.index_objects) == 3
        assert len(p.index_morphisms) == 2
        assert p.functor_map_objects["0"] == "s1"
        assert p.functor_map_objects["1"] == "s2"
        assert p.functor_map_objects["2"] == "s3"

    def test_pattern_size_property(self, pattern_mgr):
        """Property size devuelve el numero de componentes."""
        p = pattern_mgr.create_pattern(["a", "b", "c"], [])
        assert p.size == 3


# =============================================================================
# COCONE VERIFICATION (Def 2.2a)
# =============================================================================

class TestCoconeVerification:
    """Tests para verificacion de co-cono."""

    def test_valid_cocone_simple(self, graph, pattern_mgr, colimit_builder):
        """Co-cono valido para patron {s1 -> s2}."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )

        # Crear colimite manualmente
        colimit_skill = Skill(id="cP", name="colimit", level=1, pillar=PillarType.SET)
        graph.add_skill(colimit_skill)
        c1 = graph.add_morphism("s1", "cP", MorphismType.SPECIALIZATION)
        c2 = graph.add_morphism("s2", "cP", MorphismType.SPECIALIZATION)
        cocone_map = {"s1": c1.id, "s2": c2.id}

        assert colimit_builder.verify_cocone(pattern, "cP", cocone_map, graph) is True

    def test_cocone_missing_component(self, graph, pattern_mgr, colimit_builder):
        """Co-cono invalido: falta morfismo para un componente."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )

        colimit_skill = Skill(id="cP", name="colimit", level=1)
        graph.add_skill(colimit_skill)
        c1 = graph.add_morphism("s1", "cP", MorphismType.SPECIALIZATION)
        cocone_map = {"s1": c1.id}  # Missing s2

        assert colimit_builder.verify_cocone(pattern, "cP", cocone_map, graph) is False

    def test_cocone_wrong_target(self, graph, pattern_mgr, colimit_builder):
        """Co-cono invalido: morfismo apunta a skill incorrecto."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )

        colimit_skill = Skill(id="cP", name="colimit", level=1)
        graph.add_skill(colimit_skill)
        c1 = graph.add_morphism("s1", "cP", MorphismType.SPECIALIZATION)
        # c2 points to s3 instead of cP
        c2 = graph.add_morphism("s2", "s3", MorphismType.SPECIALIZATION)
        cocone_map = {"s1": c1.id, "s2": c2.id}

        assert colimit_builder.verify_cocone(pattern, "cP", cocone_map, graph) is False

    def test_cocone_without_diagram_data(self, graph, pattern_mgr, colimit_builder):
        """Co-cono sin datos de funtor: solo verifica estructura."""
        pattern = pattern_mgr.create_pattern(["s1", "s2"], ["fake_link"])
        assert not pattern.is_diagram

        colimit_skill = Skill(id="cP", name="colimit", level=1)
        graph.add_skill(colimit_skill)
        c1 = graph.add_morphism("s1", "cP", MorphismType.SPECIALIZATION)
        c2 = graph.add_morphism("s2", "cP", MorphismType.SPECIALIZATION)
        cocone_map = {"s1": c1.id, "s2": c2.id}

        # Passes because no functor data to check commutativity
        assert colimit_builder.verify_cocone(pattern, "cP", cocone_map, graph) is True


# =============================================================================
# UNIVERSAL PROPERTY (Def 2.2b)
# =============================================================================

class TestUniversalProperty:
    """Tests para propiedad universal del colimite."""

    def test_universal_property_vacuous(self, graph, pattern_mgr, colimit_builder):
        """Propiedad universal vacuamente verdadera (sin B candidatos)."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )

        colimit_skill = Skill(id="cP", name="colimit", level=1)
        graph.add_skill(colimit_skill)
        c1 = graph.add_morphism("s1", "cP", MorphismType.SPECIALIZATION)
        c2 = graph.add_morphism("s2", "cP", MorphismType.SPECIALIZATION)
        cocone_map = {"s1": c1.id, "s2": c2.id}

        # No B exists with morphisms from both s1 and s2 (other than cP)
        assert colimit_builder.verify_universal_property(
            pattern, "cP", cocone_map, graph
        ) is True

    def test_universal_property_with_compatible_target(self, graph, pattern_mgr, colimit_builder):
        """Propiedad universal con un B que recibe de todos los componentes."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )

        # Create B and morphisms g1: s1->B, g2: s2->B
        b = Skill(id="B", name="Target", level=0)
        graph.add_skill(b)
        graph.add_morphism("s1", "B", MorphismType.DEPENDENCY)
        graph.add_morphism("s2", "B", MorphismType.DEPENDENCY)

        # Create colimit
        colimit_skill = Skill(id="cP", name="colimit", level=1)
        graph.add_skill(colimit_skill)
        c1 = graph.add_morphism("s1", "cP", MorphismType.SPECIALIZATION)
        c2 = graph.add_morphism("s2", "cP", MorphismType.SPECIALIZATION)
        cocone_map = {"s1": c1.id, "s2": c2.id}

        # Without h: cP -> B, UP should fail
        assert colimit_builder.verify_universal_property(
            pattern, "cP", cocone_map, graph
        ) is False

        # Now add h: cP -> B
        graph.add_morphism("cP", "B", MorphismType.DEPENDENCY,
                           metadata={"is_universal": True})

        # Now UP should pass
        assert colimit_builder.verify_universal_property(
            pattern, "cP", cocone_map, graph
        ) is True

    def test_build_universal_morphisms(self, graph, pattern_mgr, colimit_builder):
        """build_colimit crea automaticamente los morfismos universales."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )

        # Add target B that both components map to
        b = Skill(id="B", name="Target", level=0)
        graph.add_skill(b)
        graph.add_morphism("s1", "B", MorphismType.DEPENDENCY)
        graph.add_morphism("s2", "B", MorphismType.DEPENDENCY)

        # Build colimit — should auto-create h: cP -> B
        skill, colimit = colimit_builder.build_colimit(pattern, graph)

        assert colimit.universal_property_verified is True
        assert "B" in colimit.universal_morphisms
        h = graph.get_morphism(colimit.universal_morphisms["B"])
        assert h is not None
        assert h.source_id == skill.id
        assert h.target_id == "B"
        assert h.metadata.get("is_universal") is True


# =============================================================================
# BUILD COLIMIT (Integration)
# =============================================================================

class TestBuildColimit:
    """Tests integrales de construccion de colimites."""

    def test_basic_colimit(self, graph, pattern_mgr, colimit_builder):
        """Construir colimite basico de {s1 -> s2}."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )

        skill, colimit = colimit_builder.build_colimit(pattern, graph)

        # Skill colimite creado
        assert skill is not None
        assert skill.level == 1  # max(0, 0) + 1
        assert skill.pillar == PillarType.SET

        # Colimite tiene co-cono
        assert len(colimit.cocone_morphisms) == 2
        assert len(colimit.cocone_map) == 2
        assert "s1" in colimit.cocone_map
        assert "s2" in colimit.cocone_map

        # Verificaciones pasaron
        assert colimit.cocone_verified is True
        assert colimit.universal_property_verified is True

    def test_colimit_level_hierarchy(self, graph, pattern_mgr, colimit_builder):
        """Colimite tiene nivel max(componentes) + 1."""
        # Modify s2 to level 2
        s2 = graph.get_skill("s2")
        s2.level = 2

        m12 = graph.hom("s1", "s2")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )

        skill, colimit = colimit_builder.build_colimit(pattern, graph)
        assert skill.level == 3  # max(0, 2) + 1

    def test_colimit_mixed_pillar(self, pattern_mgr, colimit_builder):
        """Colimite de componentes con pilares distintos es meta-skill (None)."""
        g = SkillCategory(name="MixedPillar")
        s1 = Skill(id="s1", name="Set Axiom", pillar=PillarType.SET, level=0)
        s2 = Skill(id="s2", name="Log Rule", pillar=PillarType.LOG, level=0)
        g.add_skill(s1)
        g.add_skill(s2)
        m = g.add_morphism("s1", "s2", MorphismType.TRANSLATION)

        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m.id], graph=g
        )

        skill, colimit = colimit_builder.build_colimit(pattern, g)
        assert skill.pillar is None  # Mixed pillar -> meta-skill

    def test_colimit_idempotent(self, graph, pattern_mgr, colimit_builder):
        """Construir colimite dos veces devuelve el mismo."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )

        skill1, colimit1 = colimit_builder.build_colimit(pattern, graph)
        skill2, colimit2 = colimit_builder.build_colimit(pattern, graph)

        assert skill1.id == skill2.id
        assert colimit1.id == colimit2.id

    def test_three_component_colimit(self, graph, pattern_mgr, colimit_builder):
        """Colimite de patron con 3 componentes."""
        m12 = graph.hom("s1", "s2")[0]
        m23 = graph.hom("s2", "s3")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2", "s3"], [m12.id, m23.id], graph=graph
        )

        skill, colimit = colimit_builder.build_colimit(pattern, graph)

        assert skill is not None
        assert len(colimit.cocone_morphisms) == 3
        assert colimit.cocone_verified is True
        assert colimit.universal_property_verified is True

    def test_colimit_cocone_morphisms_structure(self, graph, pattern_mgr, colimit_builder):
        """Los morfismos del co-cono apuntan al colimite."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )

        skill, colimit = colimit_builder.build_colimit(pattern, graph)

        for comp_id, morph_id in colimit.cocone_map.items():
            morph = graph.get_morphism(morph_id)
            assert morph is not None
            assert morph.source_id == comp_id
            assert morph.target_id == skill.id
            assert morph.metadata.get("is_cocone") is True

    def test_colimit_pattern_ids_stored(self, graph, pattern_mgr, colimit_builder):
        """El skill colimite almacena los IDs de los componentes."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )

        skill, colimit = colimit_builder.build_colimit(pattern, graph)
        assert "s1" in skill.pattern_ids
        assert "s2" in skill.pattern_ids


# =============================================================================
# COMPLEXIFICATION (Thm 2.10)
# =============================================================================

class TestComplexification:
    """Tests para complejificacion."""

    def test_complexify_single_pattern(self, graph, pattern_mgr, colimit_builder):
        """Complejificar con un solo patron."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )

        results = colimit_builder.complexify(graph, [pattern])

        assert len(results) == 1
        skill, colimit = results[0]
        assert skill is not None
        assert colimit.cocone_verified is True

    def test_complexify_multiple_patterns(self, pattern_mgr, colimit_builder):
        """Complejificar con multiples patrones independientes."""
        g = SkillCategory(name="MultiPattern")
        # Two disconnected pairs
        for sid in ["a1", "a2", "b1", "b2"]:
            g.add_skill(Skill(id=sid, name=sid, pillar=PillarType.SET, level=0))
        ma = g.add_morphism("a1", "a2", MorphismType.DEPENDENCY)
        mb = g.add_morphism("b1", "b2", MorphismType.DEPENDENCY)

        p1 = pattern_mgr.create_pattern(["a1", "a2"], [ma.id], graph=g)
        p2 = pattern_mgr.create_pattern(["b1", "b2"], [mb.id], graph=g)

        results = colimit_builder.complexify(g, [p1, p2])

        assert len(results) == 2
        # Both should have verified colimits
        for skill, colimit in results:
            assert colimit.cocone_verified is True
            assert colimit.universal_property_verified is True

    def test_complexify_skip_existing(self, graph, pattern_mgr, colimit_builder):
        """Complejificar salta patrones que ya tienen colimite."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )

        # Build colimit first
        colimit_builder.build_colimit(pattern, graph)

        # Complexify should return empty (already has colimit)
        results = colimit_builder.complexify(graph, [pattern])
        assert len(results) == 0


# =============================================================================
# DETECT PATTERNS WITH DIAGRAM DATA
# =============================================================================

class TestDetectPatterns:
    """Tests para deteccion de patrones con datos de funtor."""

    def test_detect_produces_diagrams(self, graph, pattern_mgr):
        """detect_pattern_in_graph produce patrones con datos de funtor."""
        patterns = pattern_mgr.detect_pattern_in_graph(graph, min_size=2)

        assert len(patterns) >= 1
        for p in patterns:
            assert p.is_diagram
            assert len(p.index_objects) == len(p.component_ids)
            assert len(p.functor_map_objects) == len(p.component_ids)

    def test_detect_and_build(self, graph, pattern_mgr, colimit_builder):
        """Detectar patron y construir colimite."""
        patterns = pattern_mgr.detect_pattern_in_graph(graph, min_size=2, max_size=3)

        for pattern in patterns:
            skill, colimit = colimit_builder.build_colimit(pattern, graph)
            assert colimit.cocone_verified is True
            assert colimit.universal_property_verified is True


# =============================================================================
# STATS
# =============================================================================

class TestStats:
    """Tests para estadisticas."""

    def test_pattern_stats_include_diagrams(self, graph, pattern_mgr):
        """Stats de patron incluyen numero de diagramas."""
        # Create pattern without graph
        pattern_mgr.create_pattern(["s1", "s2"], ["x"])
        # Create pattern with graph
        m12 = graph.hom("s1", "s2")[0]
        pattern_mgr.create_pattern(["s1", "s2"], [m12.id], graph=graph)

        stats = pattern_mgr.stats
        assert stats["num_patterns"] == 2
        assert stats["num_diagrams"] == 1

    def test_colimit_stats_include_verification(self, graph, pattern_mgr, colimit_builder):
        """Stats de colimite incluyen conteos de verificacion."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pattern_mgr.create_pattern(
            ["s1", "s2"], [m12.id], graph=graph
        )
        colimit_builder.build_colimit(pattern, graph)

        stats = colimit_builder.stats
        assert stats["num_colimits"] == 1
        assert stats["cocone_verified"] == 1
        assert stats["universal_property_verified"] == 1
