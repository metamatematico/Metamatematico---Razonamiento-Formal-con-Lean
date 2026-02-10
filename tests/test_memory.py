"""
Tests de Memoria MES con E-equivalencia
========================================

Verifica la implementacion de Def 5.1-5.4 del documento v7.0:
- E-equivalencia funcional (Def 5.3)
- Formacion de E-conceptos (Thm 5.4)
- Memoria procedural y consolidacion
- Integracion MESMemory
"""

import pytest

from nucleo.types import (
    ExperienceRecord, EConcept, CoRegulatorType, MemoryType,
)
from nucleo.mes.memory import (
    MESMemory, SemanticMemory, ProceduralMemory,
)


# =============================================================================
# E-EQUIVALENCE (Def 5.3)
# =============================================================================

class TestEEquivalence:
    """Tests para E-equivalencia funcional."""

    def test_same_pattern_similar_success_equivalent(self):
        """Registros con mismo patron y exito similar son E-equivalentes."""
        sem = SemanticMemory()
        r1 = ExperienceRecord(id="r1", pattern_id="p1", success_value=0.8)
        r2 = ExperienceRecord(id="r2", pattern_id="p1", success_value=0.85)
        assert sem._is_e_equivalent(r1, r2) is True

    def test_different_pattern_not_equivalent(self):
        """Registros con patrones distintos NO son E-equivalentes."""
        sem = SemanticMemory()
        r1 = ExperienceRecord(id="r1", pattern_id="p1", success_value=0.8)
        r2 = ExperienceRecord(id="r2", pattern_id="p2", success_value=0.8)
        assert sem._is_e_equivalent(r1, r2) is False

    def test_different_success_not_equivalent(self):
        """Registros con exito muy diferente NO son E-equivalentes."""
        sem = SemanticMemory()
        r1 = ExperienceRecord(id="r1", pattern_id="p1", success_value=0.9)
        r2 = ExperienceRecord(id="r2", pattern_id="p1", success_value=0.3)
        assert sem._is_e_equivalent(r1, r2) is False

    def test_opposite_success_not_equivalent(self):
        """Registros con signos opuestos de exito NO son E-equivalentes."""
        sem = SemanticMemory()
        r1 = ExperienceRecord(id="r1", pattern_id="p1", success_value=0.1)
        r2 = ExperienceRecord(id="r2", pattern_id="p1", success_value=-0.1)
        assert sem._is_e_equivalent(r1, r2) is False

    def test_boundary_equivalence(self):
        """Registros al limite del umbral (0.1)."""
        sem = SemanticMemory()
        r1 = ExperienceRecord(id="r1", pattern_id="p1", success_value=0.5)
        r2 = ExperienceRecord(id="r2", pattern_id="p1", success_value=0.6)
        # diff = 0.1, just at threshold
        assert sem._is_e_equivalent(r1, r2) is True

    def test_just_over_threshold(self):
        """Registros justo sobre el umbral."""
        sem = SemanticMemory()
        r1 = ExperienceRecord(id="r1", pattern_id="p1", success_value=0.5)
        r2 = ExperienceRecord(id="r2", pattern_id="p1", success_value=0.61)
        assert sem._is_e_equivalent(r1, r2) is False


# =============================================================================
# SEMANTIC MEMORY WITH E-EQUIVALENCE
# =============================================================================

class TestSemanticMemoryEEquivalence:
    """Tests para memoria semantica con E-equivalencia real."""

    def test_is_similar_uses_e_equivalence(self):
        """_is_similar compara via E-equivalencia contra representantes."""
        mem = MESMemory()

        # Add representative records
        r1 = ExperienceRecord(id="r1", pattern_id="p1", success_value=0.8)
        r2 = ExperienceRecord(id="r2", pattern_id="p1", success_value=0.85)
        mem.add_record(r1)
        mem.add_record(r2)

        # Form E-concept manually
        econcept = EConcept(
            representative_records=["r1", "r2"],
            co_regulator_type=CoRegulatorType.TACTICAL,
        )
        mem.semantic.add_econcept(econcept)

        # Test: similar record should match
        r3 = ExperienceRecord(id="r3", pattern_id="p1", success_value=0.82)
        assert mem.semantic._is_similar(r3, econcept) is True

        # Test: different pattern should not match
        r4 = ExperienceRecord(id="r4", pattern_id="p2", success_value=0.8)
        assert mem.semantic._is_similar(r4, econcept) is False

    def test_find_similar_econcept(self):
        """find_similar_econcept usa E-equivalencia."""
        mem = MESMemory()

        r1 = ExperienceRecord(id="r1", pattern_id="p1", success_value=0.7)
        mem.add_record(r1)

        econcept = EConcept(
            representative_records=["r1"],
            co_regulator_type=CoRegulatorType.TACTICAL,
        )
        mem.semantic.add_econcept(econcept)

        # Should find for same pattern + similar success
        query = ExperienceRecord(id="q", pattern_id="p1", success_value=0.75)
        found = mem.semantic.find_similar_econcept(query, CoRegulatorType.TACTICAL)
        assert found is not None
        assert found.id == econcept.id

        # Should not find for different cr_type
        not_found = mem.semantic.find_similar_econcept(
            query, CoRegulatorType.ORGANIZATIONAL
        )
        assert not_found is None

    def test_are_equivalent_pairwise(self):
        """_are_equivalent verifica equivalencia pairwise."""
        sem = SemanticMemory()

        r1 = ExperienceRecord(id="r1", pattern_id="p1", success_value=0.8)
        r2 = ExperienceRecord(id="r2", pattern_id="p1", success_value=0.85)
        r3 = ExperienceRecord(id="r3", pattern_id="p1", success_value=0.82)
        assert sem._are_equivalent([r1, r2, r3], CoRegulatorType.TACTICAL) is True

    def test_are_equivalent_fails_mixed_patterns(self):
        """_are_equivalent falla con patrones mixtos."""
        sem = SemanticMemory()

        r1 = ExperienceRecord(id="r1", pattern_id="p1", success_value=0.8)
        r2 = ExperienceRecord(id="r2", pattern_id="p2", success_value=0.8)
        assert sem._are_equivalent([r1, r2], CoRegulatorType.TACTICAL) is False

    def test_are_equivalent_needs_two_records(self):
        """_are_equivalent necesita al menos 2 registros."""
        sem = SemanticMemory()
        r1 = ExperienceRecord(id="r1", pattern_id="p1", success_value=0.8)
        assert sem._are_equivalent([r1], CoRegulatorType.TACTICAL) is False


# =============================================================================
# E-CONCEPT FORMATION (Thm 5.4)
# =============================================================================

class TestEConceptFormation:
    """Tests para formacion de E-conceptos."""

    def test_form_econcept_from_equivalent_records(self):
        """Forma E-concepto de registros equivalentes."""
        mem = MESMemory(econcept_min_records=3)

        # Add 3 equivalent records
        for i in range(3):
            r = ExperienceRecord(
                id=f"r{i}", pattern_id="p1", success_value=0.8 + i * 0.02
            )
            mem.add_record(r)

        econcept = mem.try_form_concept("p1", CoRegulatorType.TACTICAL)
        assert econcept is not None
        assert len(econcept.representative_records) == 3

    def test_no_econcept_insufficient_records(self):
        """No forma E-concepto con registros insuficientes."""
        mem = MESMemory(econcept_min_records=5)

        for i in range(3):
            r = ExperienceRecord(id=f"r{i}", pattern_id="p1", success_value=0.8)
            mem.add_record(r)

        econcept = mem.try_form_concept("p1", CoRegulatorType.TACTICAL)
        assert econcept is None

    def test_no_econcept_non_equivalent_records(self):
        """No forma E-concepto de registros no equivalentes."""
        mem = MESMemory(econcept_min_records=2)

        # Records with different patterns
        mem.add_record(ExperienceRecord(id="r1", pattern_id="p1", success_value=0.8))
        mem.add_record(ExperienceRecord(id="r2", pattern_id="p2", success_value=0.8))

        econcept = mem.try_form_concept("p1", CoRegulatorType.TACTICAL)
        assert econcept is None  # Only 1 record for p1, need 2


# =============================================================================
# PROCEDURAL MEMORY
# =============================================================================

class TestProceduralMemory:
    """Tests para memoria procedural."""

    def test_learn_and_recall(self):
        """Aprender y recuperar procedimiento."""
        mem = MESMemory()
        proc = mem.learn_procedure("p1", ["select", "compose"], success=True)
        assert proc.success_rate == 1.0
        assert proc.invocation_count == 1

        best = mem.procedural.get_best_procedure("p1")
        assert best is not None
        assert best.id == proc.id

    def test_update_success_rate(self):
        """Tasa de exito se actualiza con invocaciones."""
        mem = MESMemory()
        mem.learn_procedure("p1", ["select"], success=True)
        mem.learn_procedure("p1", ["select"], success=False)

        best = mem.procedural.get_best_procedure("p1")
        assert best.success_rate == 0.5
        assert best.invocation_count == 2

    def test_no_procedure_for_unknown_pattern(self):
        """No hay procedimiento para patron desconocido."""
        mem = MESMemory()
        assert mem.procedural.get_best_procedure("unknown") is None


# =============================================================================
# CONSOLIDATION
# =============================================================================

class TestConsolidation:
    """Tests para consolidacion de memoria."""

    def test_consolidation_threshold(self):
        """Registro se consolida al alcanzar umbral."""
        mem = MESMemory(consolidation_threshold=3)
        r = ExperienceRecord(id="r1", pattern_id="p1", success_value=0.8)
        mem.add_record(r)

        for _ in range(3):
            mem.consolidate_record("r1")

        record = mem.get_record("r1")
        assert record.memory_type == MemoryType.CONSOLIDATED

    def test_recall_similar(self):
        """Recuperar registros similares por patron."""
        mem = MESMemory()
        for i in range(5):
            r = ExperienceRecord(
                id=f"r{i}", pattern_id="p1",
                success_value=0.5 + i * 0.1
            )
            mem.add_record(r)

        similar = mem.recall_similar("p1", limit=3)
        assert len(similar) == 3
        # Should be sorted by success (descending)
        assert similar[0].success_value >= similar[1].success_value


# =============================================================================
# MES MEMORY STATS
# =============================================================================

class TestMESMemoryStats:
    """Tests para estadisticas de MESMemory."""

    def test_stats_initial(self):
        """Estadisticas iniciales."""
        mem = MESMemory()
        stats = mem.stats
        assert stats["total_records"] == 0
        assert stats["procedural"]["num_procedures"] == 0
        assert stats["semantic"]["num_econcepts"] == 0

    def test_stats_after_operations(self):
        """Estadisticas despues de operaciones."""
        mem = MESMemory(econcept_min_records=2)

        mem.add_record(ExperienceRecord(id="r1", pattern_id="p1", success_value=0.8))
        mem.add_record(ExperienceRecord(id="r2", pattern_id="p1", success_value=0.85))
        mem.learn_procedure("p1", ["select"], success=True)

        stats = mem.stats
        assert stats["total_records"] == 2
        assert stats["procedural"]["num_procedures"] == 1
