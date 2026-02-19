"""
Tests del Sistema Evolutivo
============================

Verifica la implementacion de Def 3.2 y Thm 2.10 del documento v7.0:
- CategorySnapshot: captura inmutable del estado
- TransitionFunctor: mapeo entre snapshots
- EvolutionarySystem: evolucion via Options
- Compatibilidad de funtores: k_{t2,t3} . k_{t1,t2} = k_{t1,t3}
"""

import pytest

from nucleo.types import Skill, MorphismType, PillarType, Option
from nucleo.graph.category import SkillCategory
from nucleo.graph.evolution import (
    EvolutionarySystem,
    CategorySnapshot,
    TransitionFunctor,
)
from nucleo.mes.patterns import PatternManager


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def base_graph():
    """Grafo base con 3 skills: s1 -> s2 -> s3."""
    g = SkillCategory(name="EvoTest")
    g.add_skill(Skill(id="s1", name="Axiom1", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="s2", name="Axiom2", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="s3", name="Axiom3", pillar=PillarType.SET, level=0))
    g.add_morphism("s1", "s2", MorphismType.DEPENDENCY)
    g.add_morphism("s2", "s3", MorphismType.DEPENDENCY)
    return g


@pytest.fixture
def evo_system(base_graph):
    """Sistema evolutivo inicializado."""
    return EvolutionarySystem(base_graph)


# =============================================================================
# CATEGORY SNAPSHOT
# =============================================================================

class TestCategorySnapshot:
    """Tests para CategorySnapshot."""

    def test_initial_snapshot(self, evo_system):
        """Snapshot inicial captura el estado del grafo."""
        snap = evo_system.get_snapshot(0)
        assert snap is not None
        assert snap.timestamp == 0
        assert snap.num_skills == 3
        assert "s1" in snap.skills
        assert "s2" in snap.skills
        assert "s3" in snap.skills

    def test_snapshot_has_morphisms(self, evo_system):
        """Snapshot incluye morfismos (incluyendo identidades)."""
        snap = evo_system.get_snapshot(0)
        # 3 identidades + 2 dependency = 5
        assert snap.num_morphisms == 5

    def test_snapshot_is_copy(self, evo_system, base_graph):
        """Snapshot es una copia, no referencia al grafo."""
        snap = evo_system.get_snapshot(0)
        # Modificar grafo no afecta snapshot
        base_graph.add_skill(Skill(id="s4", name="New", level=0))
        assert snap.num_skills == 3
        assert not snap.has_skill("s4")

    def test_snapshot_has_stats(self, evo_system):
        """Snapshot incluye estadisticas."""
        snap = evo_system.get_snapshot(0)
        assert "num_skills" in snap.stats
        assert snap.stats["num_skills"] == 3


# =============================================================================
# TRANSITION FUNCTOR
# =============================================================================

class TestTransitionFunctor:
    """Tests para TransitionFunctor."""

    def test_identity_functor(self, evo_system):
        """Funtor identidad k_{t,t} es el mapeo identico."""
        k_00 = evo_system.get_functor(0, 0)
        assert k_00 is not None
        assert k_00.source_time == 0
        assert k_00.target_time == 0
        assert k_00.object_map["s1"] == "s1"
        assert k_00.object_map["s2"] == "s2"
        assert k_00.num_preserved == 3

    def test_functor_composition(self):
        """Composicion de funtores k_{1,2} . k_{0,1}."""
        k_01 = TransitionFunctor(
            source_time=0, target_time=1,
            object_map={"a": "a", "b": "b", "c": None},  # c eliminated
            morphism_map={"m1": "m1", "m2": None},
            absorbed_skills=["d"],
        )
        k_12 = TransitionFunctor(
            source_time=1, target_time=2,
            object_map={"a": "a", "b": None, "d": "d"},  # b eliminated
            morphism_map={"m1": "m1_new"},
            absorbed_skills=["e"],
        )

        composed = k_12.compose(k_01)

        assert composed.source_time == 0
        assert composed.target_time == 2
        assert composed.object_map["a"] == "a"
        assert composed.object_map["b"] is None  # eliminated in step 2
        assert composed.object_map["c"] is None  # eliminated in step 1
        assert composed.morphism_map["m1"] == "m1_new"
        assert composed.morphism_map["m2"] is None

    def test_functor_preserved_count(self):
        """Conteo de skills preservados vs eliminados."""
        k = TransitionFunctor(
            source_time=0, target_time=1,
            object_map={"a": "a", "b": "b", "c": None},
            absorbed_skills=["d", "e"],
        )
        assert k.num_preserved == 2
        assert k.num_eliminated == 1
        assert k.num_absorbed == 2


# =============================================================================
# EVOLUTION VIA OPTIONS
# =============================================================================

class TestEvolutionViaOptions:
    """Tests para evolucion via Options."""

    def test_absorption(self, evo_system, base_graph):
        """Option de absorcion: nuevo skill aparece."""
        new_skill = Skill(id="s4", name="NewSkill", pillar=PillarType.LOG, level=0)
        base_graph.add_skill(new_skill)

        option = Option(absorptions=["s4"])
        functor = evo_system.apply_option(option)

        assert evo_system.current_time == 1
        assert "s4" in functor.absorbed_skills
        snap = evo_system.get_snapshot(1)
        assert snap.has_skill("s4")

    def test_elimination(self, evo_system):
        """Option de eliminacion: skill desaparece."""
        option = Option(eliminations=["s3"])
        functor = evo_system.apply_option(option)

        assert functor.object_map["s3"] is None
        assert functor.num_eliminated == 1
        snap = evo_system.get_snapshot(1)
        assert not snap.has_skill("s3")

    def test_binding(self, evo_system, base_graph):
        """Option de ligadura: patron adquiere colimite."""
        pm = evo_system.pattern_manager
        m12 = base_graph.hom("s1", "s2")[0]
        pattern = pm.create_pattern(
            ["s1", "s2"], [m12.id], graph=base_graph
        )

        option = Option(bindings=[pattern.id])
        functor = evo_system.apply_option(option)

        assert evo_system.current_time == 1
        assert len(functor.absorbed_skills) > 0
        # Colimite exists
        assert evo_system.colimit_builder.has_colimit(pattern.id)

    def test_elimination_removes_morphisms(self, evo_system):
        """Eliminacion marca morfismos conectados como None."""
        option = Option(eliminations=["s2"])
        functor = evo_system.apply_option(option)

        # s1->s2 and s2->s3 morphisms should be eliminated
        eliminated_morphisms = sum(
            1 for v in functor.morphism_map.values() if v is None
        )
        # At least the 2 dependency morphisms + identity of s2
        assert eliminated_morphisms >= 3

    def test_multi_step_evolution(self, evo_system, base_graph):
        """Evolucion en multiples pasos."""
        # Step 1: Add s4
        s4 = Skill(id="s4", name="Extra", level=0)
        base_graph.add_skill(s4)
        evo_system.apply_option(Option(absorptions=["s4"]))

        # Step 2: Remove s1
        evo_system.apply_option(Option(eliminations=["s1"]))

        assert evo_system.current_time == 2
        snap_0 = evo_system.get_snapshot(0)
        snap_2 = evo_system.get_snapshot(2)

        assert snap_0.has_skill("s1")
        assert not snap_2.has_skill("s1")
        assert not snap_0.has_skill("s4")
        assert snap_2.has_skill("s4")


# =============================================================================
# COMPATIBILITY (Def 3.2)
# =============================================================================

class TestCompatibility:
    """Tests para compatibilidad de funtores."""

    def test_compatibility_two_steps(self, evo_system, base_graph):
        """k_{1,2} . k_{0,1} = k_{0,2}."""
        # Step 1: absorb s4
        s4 = Skill(id="s4", name="Extra", level=0)
        base_graph.add_skill(s4)
        evo_system.apply_option(Option(absorptions=["s4"]))

        # Step 2: eliminate s3
        evo_system.apply_option(Option(eliminations=["s3"]))

        # Verify compatibility
        assert evo_system.verify_compatibility(0, 1, 2) is True

    def test_compatibility_three_steps(self, evo_system, base_graph):
        """k_{1,2} . k_{0,1} = k_{0,2} y k_{2,3} . k_{0,2} = k_{0,3}."""
        # Three evolution steps
        s4 = Skill(id="s4", name="Extra1", level=0)
        base_graph.add_skill(s4)
        evo_system.apply_option(Option(absorptions=["s4"]))

        s5 = Skill(id="s5", name="Extra2", level=0)
        base_graph.add_skill(s5)
        evo_system.apply_option(Option(absorptions=["s5"]))

        evo_system.apply_option(Option(eliminations=["s1"]))

        assert evo_system.verify_compatibility(0, 1, 2) is True
        assert evo_system.verify_compatibility(1, 2, 3) is True
        assert evo_system.verify_compatibility(0, 1, 3) is True

    def test_get_composed_functor(self, evo_system, base_graph):
        """get_functor compone funtores consecutivos automaticamente."""
        s4 = Skill(id="s4", name="Extra", level=0)
        base_graph.add_skill(s4)
        evo_system.apply_option(Option(absorptions=["s4"]))
        evo_system.apply_option(Option(eliminations=["s3"]))

        k_02 = evo_system.get_functor(0, 2)
        assert k_02 is not None
        assert k_02.source_time == 0
        assert k_02.target_time == 2
        assert k_02.object_map["s1"] == "s1"
        assert k_02.object_map["s3"] is None


# =============================================================================
# STATS
# =============================================================================

class TestEvolutionStats:
    """Tests para estadisticas del sistema evolutivo."""

    def test_initial_stats(self, evo_system):
        """Estadisticas iniciales."""
        stats = evo_system.stats
        assert stats["current_time"] == 0
        assert stats["num_snapshots"] == 1
        assert stats["num_functors"] == 0
        assert stats["current_skills"] == 3

    def test_stats_after_evolution(self, evo_system, base_graph):
        """Estadisticas despues de evolucion."""
        s4 = Skill(id="s4", name="Extra", level=0)
        base_graph.add_skill(s4)
        evo_system.apply_option(Option(absorptions=["s4"]))

        stats = evo_system.stats
        assert stats["current_time"] == 1
        assert stats["num_snapshots"] == 2
        assert stats["num_functors"] == 1
        assert stats["current_skills"] == 4
