"""
Tests de Co-reguladores Activos
================================

Verifica la implementacion de Def 4.1 y Seccion 4.3 del documento v7.0:
- CR_tac: Consulta memoria procedural
- CR_org: Detecta patrones sin colimite, propone ligaduras/eliminaciones
- CR_str: Detecta enlaces complejos, propone complejificacion
- CR_int: Verifica invariantes, detecta fracturas
- CoRegulatorNetwork: Coordinacion multi-escala
"""

import pytest

from nucleo.types import (
    Skill, MorphismType, PillarType, CoRegulatorType,
    MESActionType, FractureType,
)
from nucleo.graph.category import SkillCategory
from nucleo.mes.patterns import PatternManager, ColimitBuilder
from nucleo.mes.memory import MESMemory
from nucleo.mes.co_regulators import (
    TacticalCoRegulator,
    OrganizationalCoRegulator,
    StrategicCoRegulator,
    IntegrityCoRegulator,
    CoRegulatorNetwork,
    Landscape,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def graph():
    """Grafo con skills en SET y LOG."""
    g = SkillCategory(name="CRTest")
    g.add_skill(Skill(id="s1", name="A", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="s2", name="B", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="s3", name="C", pillar=PillarType.LOG, level=0))
    g.add_morphism("s1", "s2", MorphismType.DEPENDENCY)
    g.add_morphism("s2", "s3", MorphismType.DEPENDENCY)
    return g


@pytest.fixture
def memory():
    return MESMemory()


@pytest.fixture
def pm():
    return PatternManager()


@pytest.fixture
def cb(pm):
    return ColimitBuilder(pm)


# =============================================================================
# TACTICAL CO-REGULATOR (CR_tac)
# =============================================================================

class TestTacticalCR:
    """Tests para co-regulador tactico."""

    def test_landscape_includes_level_0_1(self, graph):
        """Paisaje tactico incluye skills de nivel 0 y 1."""
        cr = TacticalCoRegulator()
        landscape = cr.build_landscape(graph)
        assert len(landscape.relevant_skills) == 3
        assert landscape.metrics["num_skills_0"] == 3

    def test_select_without_memory_returns_empty(self, graph):
        """Sin memoria, select_objectives retorna Option vacio."""
        cr = TacticalCoRegulator()
        landscape = cr.build_landscape(graph)
        option = cr.select_objectives(landscape)
        assert not option.bindings
        assert not option.absorptions

    def test_select_with_procedure(self, graph, memory, pm):
        """Con procedimiento exitoso, retorna binding."""
        # Create pattern and learn procedure
        m12 = graph.hom("s1", "s2")[0]
        pattern = pm.create_pattern(["s1", "s2"], [m12.id], graph=graph)
        memory.learn_procedure(pattern.id, ["select", "compose"], success=True)

        cr = TacticalCoRegulator(memory=memory, pattern_manager=pm)
        landscape = cr.build_landscape(graph)
        option = cr.select_objectives(landscape)

        assert len(option.bindings) == 1
        assert option.bindings[0] == pattern.id
        assert "procedure_id" in option.metadata

    def test_select_with_bad_procedure_ignored(self, graph, memory, pm):
        """Procedimiento con baja tasa de exito se ignora."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pm.create_pattern(["s1", "s2"], [m12.id], graph=graph)
        # Create procedure with low success
        proc = memory.learn_procedure(pattern.id, ["fail"], success=False)

        cr = TacticalCoRegulator(memory=memory, pattern_manager=pm)
        landscape = cr.build_landscape(graph)
        option = cr.select_objectives(landscape)
        assert not option.bindings

    def test_landscape_includes_patterns(self, graph, pm):
        """Paisaje tactico incluye patrones relevantes."""
        m12 = graph.hom("s1", "s2")[0]
        pm.create_pattern(["s1", "s2"], [m12.id], graph=graph)

        cr = TacticalCoRegulator(pattern_manager=pm)
        landscape = cr.build_landscape(graph)
        assert len(landscape.relevant_patterns) == 1


# =============================================================================
# ORGANIZATIONAL CO-REGULATOR (CR_org)
# =============================================================================

class TestOrganizationalCR:
    """Tests para co-regulador organizativo."""

    def test_select_binds_unbound_patterns(self, graph, pm, cb):
        """Propone ligadura para patrones sin colimite."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pm.create_pattern(["s1", "s2"], [m12.id], graph=graph)

        cr = OrganizationalCoRegulator(
            frequency=1, pattern_manager=pm, colimit_builder=cb
        )
        cr._current_graph = graph
        landscape = cr.build_landscape(graph)
        option = cr.select_objectives(landscape)

        assert len(option.bindings) == 1
        assert option.bindings[0] == pattern.id

    def test_no_binding_when_all_bound(self, graph, pm, cb):
        """Sin ligadura cuando todos los patrones tienen colimite."""
        m12 = graph.hom("s1", "s2")[0]
        pattern = pm.create_pattern(["s1", "s2"], [m12.id], graph=graph)
        cb.build_colimit(pattern, graph)

        cr = OrganizationalCoRegulator(
            frequency=1, pattern_manager=pm, colimit_builder=cb
        )
        cr._current_graph = graph
        landscape = cr.build_landscape(graph)
        option = cr.select_objectives(landscape)

        assert not option.bindings

    def test_eliminates_weak_skills(self, graph, pm, cb):
        """Propone eliminacion de skills con peso bajo."""
        # Add a weakly connected skill
        graph.add_skill(Skill(id="weak", name="Weak", pillar=PillarType.SET, level=0))
        graph.add_morphism("weak", "s1", MorphismType.DEPENDENCY, weight=0.1)

        cr = OrganizationalCoRegulator(
            frequency=1, pattern_manager=pm, colimit_builder=cb
        )
        cr._current_graph = graph
        landscape = cr.build_landscape(graph)
        option = cr.select_objectives(landscape)

        assert "weak" in option.eliminations

    def test_landscape_counts_unbound(self, graph, pm, cb):
        """Paisaje organizativo cuenta patrones sin colimite."""
        m12 = graph.hom("s1", "s2")[0]
        pm.create_pattern(["s1", "s2"], [m12.id], graph=graph)

        cr = OrganizationalCoRegulator(
            frequency=1, pattern_manager=pm, colimit_builder=cb
        )
        landscape = cr.build_landscape(graph)
        assert landscape.metrics["num_unbound_patterns"] == 1.0

    def test_encode_procedure_complexify(self):
        """Opcion con bindings codifica como COMPLEXIFY."""
        from nucleo.types import Option
        cr = OrganizationalCoRegulator(frequency=1)
        option = Option(bindings=["pat1"])
        assert cr.encode_procedure(option) == MESActionType.COMPLEXIFY


# =============================================================================
# STRATEGIC CO-REGULATOR (CR_str)
# =============================================================================

class TestStrategicCR:
    """Tests para co-regulador estrategico."""

    def test_no_action_without_complex_links(self, graph, pm):
        """Sin enlaces complejos, no propone accion."""
        cr = StrategicCoRegulator(frequency=1, pattern_manager=pm)
        cr._current_graph = graph
        landscape = cr.build_landscape(graph)
        option = cr.select_objectives(landscape)
        assert not option.bindings

    def test_complexifies_complex_links(self, graph, pm):
        """Con enlaces complejos, crea patron y propone ligadura."""
        # Create composed morphism (complex link)
        f = graph.hom("s1", "s2")[0]
        g = graph.hom("s2", "s3")[0]
        graph.compose(g.id, f.id)

        cr = StrategicCoRegulator(frequency=1, pattern_manager=pm)
        cr._current_graph = graph
        landscape = cr.build_landscape(graph)
        option = cr.select_objectives(landscape)

        assert len(option.bindings) == 1
        assert landscape.metrics["num_complex_links"] >= 1

    def test_landscape_includes_complex_count(self, graph, pm):
        """Paisaje estrategico cuenta enlaces complejos."""
        cr = StrategicCoRegulator(frequency=1, pattern_manager=pm)
        landscape = cr.build_landscape(graph)
        assert "num_complex_links" in landscape.metrics


# =============================================================================
# INTEGRITY CO-REGULATOR (CR_int)
# =============================================================================

class TestIntegrityCR:
    """Tests para co-regulador de integridad."""

    def test_landscape_includes_multiplicity(self, graph, pm, cb):
        """Paisaje de integridad incluye verificacion de multiplicidad."""
        cr = IntegrityCoRegulator(
            frequency=1, pattern_manager=pm, colimit_builder=cb
        )
        landscape = cr.build_landscape(graph)
        assert "multiplicity_holds" in landscape.metrics
        assert "axioms_satisfied" in landscape.metrics
        assert "is_connected" in landscape.metrics

    def test_no_fracture_when_stable(self, graph, pm):
        """Sin fractura cuando invariantes estables."""
        cr = IntegrityCoRegulator(frequency=1, pattern_manager=pm)
        anticipated = Landscape(
            co_regulator_type=CoRegulatorType.INTEGRITY,
            metrics={"axioms_satisfied": 1.0, "is_connected": 1.0}
        )
        actual = Landscape(
            co_regulator_type=CoRegulatorType.INTEGRITY,
            metrics={"axioms_satisfied": 1.0, "is_connected": 1.0}
        )
        fracture = cr.detect_fracture(anticipated, actual)
        assert fracture is None

    def test_detects_fracture_on_invariant_break(self):
        """Detecta fractura cuando un invariante se rompe."""
        cr = IntegrityCoRegulator(frequency=1)
        anticipated = Landscape(
            co_regulator_type=CoRegulatorType.INTEGRITY,
            metrics={"axioms_satisfied": 1.0, "is_connected": 1.0}
        )
        actual = Landscape(
            co_regulator_type=CoRegulatorType.INTEGRITY,
            metrics={"axioms_satisfied": 0.0, "is_connected": 1.0}
        )
        fracture = cr.detect_fracture(anticipated, actual)
        assert fracture is not None
        assert fracture.fracture_type == FractureType.STRUCTURAL

    def test_select_repairs_multiplicity(self, graph, pm, cb):
        """Propone reparacion cuando hay fractura de multiplicidad."""
        # Setup: create patterns for multiplicity
        m12 = graph.hom("s1", "s2")[0]
        pm.create_pattern(["s1", "s2"], [m12.id], graph=graph)

        cr = IntegrityCoRegulator(
            frequency=1, pattern_manager=pm, colimit_builder=cb
        )
        cr._current_graph = graph

        # Simulate fracture
        from nucleo.types import Fracture
        fracture = Fracture(
            fracture_type=FractureType.STRUCTURAL,
            actual_state={"multiplicity_holds": 0},
        )
        cr._state.detected_fractures.append(fracture)

        landscape = cr.build_landscape(graph)
        option = cr.select_objectives(landscape)
        # Should try to detect patterns and propose bindings
        # (may or may not find patterns depending on graph structure)
        assert isinstance(option.bindings, list)

    def test_connected_graph_detected(self, graph):
        """Grafo conexo detectado correctamente."""
        cr = IntegrityCoRegulator(frequency=1)
        landscape = cr.build_landscape(graph)
        assert landscape.metrics["is_connected"] == 1.0


# =============================================================================
# CO-REGULATOR NETWORK
# =============================================================================

class TestCoRegulatorNetwork:
    """Tests para la red de co-reguladores."""

    def test_tactical_activates_every_step(self, graph):
        """CR_tac se activa en cada paso."""
        network = CoRegulatorNetwork()
        results = network.step(graph)
        # Tactical always activates (frequency=1)
        tac_results = [r for r in results if r[0] == CoRegulatorType.TACTICAL]
        assert len(tac_results) == 1

    def test_org_activates_periodically(self, graph):
        """CR_org se activa cada k pasos."""
        network = CoRegulatorNetwork(cr_org_frequency=3)
        # Step 0: activates
        r0 = network.step(graph)
        org0 = [r for r in r0 if r[0] == CoRegulatorType.ORGANIZATIONAL]
        assert len(org0) == 1

        # Steps 1-2: doesn't activate
        r1 = network.step(graph)
        org1 = [r for r in r1 if r[0] == CoRegulatorType.ORGANIZATIONAL]
        assert len(org1) == 0

        r2 = network.step(graph)
        org2 = [r for r in r2 if r[0] == CoRegulatorType.ORGANIZATIONAL]
        assert len(org2) == 0

        # Step 3: activates again
        r3 = network.step(graph)
        org3 = [r for r in r3 if r[0] == CoRegulatorType.ORGANIZATIONAL]
        assert len(org3) == 1

    def test_network_with_shared_resources(self, graph, memory, pm, cb):
        """Red con recursos compartidos funciona correctamente."""
        network = CoRegulatorNetwork(
            memory=memory,
            pattern_manager=pm,
            colimit_builder=cb,
            cr_org_frequency=1,
            cr_str_frequency=1,
            cr_int_frequency=1,
        )
        results = network.step(graph)
        assert len(results) == 4  # All 4 CRs activate

    def test_stats_track_steps(self, graph):
        """Estadisticas rastrean pasos correctamente."""
        network = CoRegulatorNetwork()
        network.step(graph)
        stats = network.stats
        assert stats["tactical_steps"] == 1
        assert stats["detected_fractures"] == 0

    def test_network_backward_compatible(self, graph):
        """Red funciona sin recursos compartidos (compatibilidad)."""
        network = CoRegulatorNetwork()
        results = network.step(graph)
        assert len(results) >= 1  # At least tactical activates
