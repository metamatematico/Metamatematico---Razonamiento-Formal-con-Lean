"""
Tests de Integracion lean4-skills
==================================

Verifica la integracion del NLE con lean4-skills (Fase 6):
- SolverCascade: cascada automatica de tacticas
- SorryAnalyzer: analisis estatico de sorries
- Parser estructurado: clasificacion de errores
- SorryFiller + cascade: flujo completo
- MES memory: registro de experiencias Lean
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from nucleo.lean.client import LeanClient, LeanResult, LeanResultStatus
from nucleo.lean.solver_cascade import (
    SolverCascade, CascadeResult, SOLVER_CASCADE, SKIP_ERROR_TYPES,
)
from nucleo.lean.sorry_analyzer import (
    find_sorries_in_text, SorryInfo, SorryReport, analyze_sorries,
)
from nucleo.lean.parser import (
    LeanParser, LeanMessage, MessageSeverity, Position,
    StructuredError, classify_error, extract_goal, extract_local_context,
    extract_suggestion_keywords, compute_error_hash, parse_error_structured,
)
from nucleo.lean.sorry_filler import (
    SorryFiller, SorryContext, SorryType, ProofCandidate, SorryFillingResult,
)
from nucleo.mes.memory import MESMemory
from nucleo.types import ExperienceRecord, CoRegulatorType


def _run(coro):
    """Run async coroutine synchronously for testing."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# =============================================================================
# SOLVER CASCADE
# =============================================================================

class TestSolverCascade:
    """Tests para SolverCascade."""

    def _make_lean_client(self, success_on: str = None) -> LeanClient:
        """Create mock LeanClient that succeeds on a specific solver."""
        client = MagicMock(spec=LeanClient)

        async def mock_check(code):
            if success_on and success_on in code:
                return LeanResult(status=LeanResultStatus.SUCCESS)
            return LeanResult(
                status=LeanResultStatus.ERROR,
                messages=[{"severity": "error", "message": "fail"}],
            )

        client.check_code = AsyncMock(side_effect=mock_check)
        return client

    def test_cascade_constants(self):
        """Cascade has expected solvers in order."""
        solver_names = [s[0] for s in SOLVER_CASCADE]
        assert solver_names[0] == "rfl"
        assert "simp" in solver_names
        assert "aesop" in solver_names
        assert solver_names[-1] == "aesop"

    def test_skip_error_types(self):
        """Known error types are skipped."""
        assert "unknown_ident" in SKIP_ERROR_TYPES
        assert "synth_implicit" in SKIP_ERROR_TYPES
        assert "recursion_depth" in SKIP_ERROR_TYPES

    def test_cascade_succeeds_on_rfl(self):
        """Cascade finds rfl as solution."""
        client = self._make_lean_client(success_on="rfl")
        cascade = SolverCascade(client)

        result = _run(cascade.try_fill_sorry(
            code="theorem foo : 1 = 1 := by\n  sorry",
            sorry_line=2,
        ))

        assert result.success is True
        assert result.solver == "rfl"
        assert result.solvers_tried == 1

    def test_cascade_succeeds_on_simp(self):
        """Cascade tries rfl first, then finds simp."""
        client = self._make_lean_client(success_on="simp")
        cascade = SolverCascade(client)

        result = _run(cascade.try_fill_sorry(
            code="theorem foo : x + 0 = x := by\n  sorry",
            sorry_line=2,
        ))

        assert result.success is True
        assert result.solver == "simp"
        assert result.solvers_tried == 2  # rfl failed, simp succeeded

    def test_cascade_exhausted(self):
        """Cascade returns failure when all solvers fail."""
        client = self._make_lean_client(success_on=None)
        cascade = SolverCascade(client)

        result = _run(cascade.try_fill_sorry(
            code="theorem foo : Complex := by\n  sorry",
            sorry_line=2,
        ))

        assert result.success is False
        assert result.solvers_tried == len(SOLVER_CASCADE)

    def test_cascade_skips_incompatible_errors(self):
        """Cascade skips for incompatible error types."""
        client = self._make_lean_client(success_on="rfl")
        cascade = SolverCascade(client)

        result = _run(cascade.try_fill_sorry(
            code="theorem foo := by\n  sorry",
            sorry_line=2,
            error_type="unknown_ident",
        ))

        assert result.success is False
        assert result.solvers_tried == 0

    def test_cascade_no_sorry_on_line(self):
        """Cascade returns failure if no sorry on target line."""
        client = self._make_lean_client(success_on="rfl")
        cascade = SolverCascade(client)

        result = _run(cascade.try_fill_sorry(
            code="theorem foo : 1 = 1 := by\n  rfl",
            sorry_line=2,  # 'rfl' not 'sorry'
        ))

        assert result.success is False
        assert result.solvers_tried == 0

    def test_cascade_invalid_line(self):
        """Cascade handles invalid line numbers."""
        client = self._make_lean_client()
        cascade = SolverCascade(client)

        result = _run(cascade.try_fill_sorry(
            code="theorem foo := by\n  sorry",
            sorry_line=99,
        ))

        assert result.success is False

    def test_try_fill_theorem(self):
        """try_fill_theorem tries solvers on a bare theorem."""
        client = self._make_lean_client(success_on="omega")
        cascade = SolverCascade(client)

        result = _run(cascade.try_fill_theorem(
            name="nat_pos",
            statement="0 < 1",
        ))

        assert result.success is True
        assert result.solver == "omega"

    def test_try_multiple_sorries(self):
        """try_multiple_sorries handles multiple sorry locations."""
        client = self._make_lean_client(success_on="simp")
        cascade = SolverCascade(client)

        code = "theorem a : True := by\n  sorry\ntheorem b : True := by\n  sorry"
        results = _run(cascade.try_multiple_sorries(code, [2, 4]))

        assert len(results) == 2


# =============================================================================
# SORRY ANALYZER
# =============================================================================

class TestSorryAnalyzer:
    """Tests para sorry_analyzer."""

    def test_find_sorries_in_text_basic(self):
        """Find sorry in simple code."""
        code = "theorem foo : 1 = 1 := by\n  sorry"
        sorries = find_sorries_in_text(code)
        assert len(sorries) == 1
        assert sorries[0].line == 2

    def test_find_sorries_with_declaration(self):
        """Extract declaration name containing sorry."""
        code = "theorem important_theorem : P := by\n  sorry"
        sorries = find_sorries_in_text(code)
        assert len(sorries) == 1
        assert sorries[0].in_declaration == "theorem important_theorem"

    def test_find_sorries_with_lemma(self):
        """Extract lemma name."""
        code = "lemma helper_lemma : Q := by\n  intro h\n  sorry"
        sorries = find_sorries_in_text(code)
        assert len(sorries) == 1
        assert sorries[0].in_declaration == "lemma helper_lemma"

    def test_find_sorries_multiple(self):
        """Find multiple sorries."""
        code = (
            "theorem a : P := by sorry\n"
            "theorem b : Q := by sorry\n"
            "theorem c : R := by sorry\n"
        )
        sorries = find_sorries_in_text(code)
        assert len(sorries) == 3

    def test_find_sorries_ignores_comments(self):
        """Sorry in comments is ignored."""
        code = "-- sorry this is a comment\ntheorem foo : P := by rfl"
        sorries = find_sorries_in_text(code)
        assert len(sorries) == 0

    def test_find_sorries_extracts_context(self):
        """Context before and after is captured."""
        code = "import Mathlib\n\ntheorem foo : 1 = 1 := by\n  sorry\n\n-- done"
        sorries = find_sorries_in_text(code)
        assert len(sorries) == 1
        assert len(sorries[0].context_before) > 0
        assert len(sorries[0].context_after) > 0

    def test_find_sorries_with_documentation(self):
        """Documentation comments after sorry are captured."""
        code = "theorem foo : P := by\n  sorry\n  -- TODO: prove using induction"
        sorries = find_sorries_in_text(code)
        assert len(sorries) == 1
        assert len(sorries[0].documentation) == 1
        assert "induction" in sorries[0].documentation[0]

    def test_empty_code(self):
        """No sorries in empty code."""
        assert find_sorries_in_text("") == []
        assert find_sorries_in_text("-- no lean code") == []

    def test_sorry_info_to_dict(self):
        """SorryInfo serializes to dict."""
        info = SorryInfo(file="test.lean", line=5)
        d = info.to_dict()
        assert d["file"] == "test.lean"
        assert d["line"] == 5

    def test_sorry_report_by_file(self):
        """SorryReport groups by file."""
        sorries = [
            SorryInfo(file="a.lean", line=1),
            SorryInfo(file="a.lean", line=5),
            SorryInfo(file="b.lean", line=3),
        ]
        report = SorryReport(total_count=3, sorries=sorries, files_scanned=2)
        by_file = report.by_file
        assert len(by_file["a.lean"]) == 2
        assert len(by_file["b.lean"]) == 1

    def test_sorry_report_declarations(self):
        """SorryReport lists declarations with sorry."""
        sorries = [
            SorryInfo(file="a.lean", line=1, in_declaration="theorem foo"),
            SorryInfo(file="a.lean", line=5, in_declaration=None),
        ]
        report = SorryReport(total_count=2, sorries=sorries)
        decls = report.declarations_with_sorry
        assert len(decls) == 1
        assert decls[0] == "theorem foo"


# =============================================================================
# STRUCTURED ERROR PARSER
# =============================================================================

class TestStructuredErrorParser:
    """Tests para parser estructurado de errores."""

    def test_classify_type_mismatch(self):
        """Classify type mismatch error."""
        assert classify_error("type mismatch at foo") == "type_mismatch"

    def test_classify_unsolved_goals(self):
        """Classify unsolved goals error."""
        assert classify_error("unsolved goals\n⊢ True") == "unsolved_goals"

    def test_classify_unknown_ident(self):
        """Classify unknown identifier error."""
        assert classify_error("unknown identifier 'foo'") == "unknown_ident"

    def test_classify_sorry_present(self):
        """Classify sorry present."""
        assert classify_error("declaration uses 'sorry'") == "sorry_present"

    def test_classify_timeout(self):
        """Classify timeout."""
        assert classify_error("deterministic timeout") == "timeout"

    def test_classify_unknown(self):
        """Unknown error type."""
        assert classify_error("something weird happened") == "unknown"

    def test_classify_app_type_mismatch(self):
        """Classify application type mismatch."""
        assert classify_error("application type mismatch") == "app_type_mismatch"

    def test_classify_synth_instance(self):
        """Classify instance synthesis failure."""
        assert classify_error("failed to synthesize instance") == "synth_instance"

    def test_extract_goal(self):
        """Extract goal from error text."""
        text = "unsolved goals\nh : Nat\n⊢ h > 0"
        goal = extract_goal(text)
        assert goal == "h > 0"

    def test_extract_goal_none(self):
        """No goal when not present."""
        assert extract_goal("type mismatch at foo") is None

    def test_extract_local_context(self):
        """Extract hypotheses from error context."""
        text = "context:\nh1 : Measurable f\nh2 : Integrable f μ\n⊢ Continuous f"
        ctx = extract_local_context(text)
        assert len(ctx) == 2
        assert "h1 : Measurable f" in ctx

    def test_extract_suggestion_keywords(self):
        """Extract keywords from error message."""
        msg = "unknown identifier 'Continuous' in 'Continuous f'"
        keywords = extract_suggestion_keywords(msg)
        assert "Continuous" in keywords

    def test_compute_error_hash_deterministic(self):
        """Error hash is deterministic."""
        h1 = compute_error_hash("type_mismatch", "Foo.lean", 42)
        h2 = compute_error_hash("type_mismatch", "Foo.lean", 42)
        assert h1 == h2
        assert len(h1) == 12

    def test_compute_error_hash_differs(self):
        """Different inputs produce different hashes."""
        h1 = compute_error_hash("type_mismatch", "Foo.lean", 42)
        h2 = compute_error_hash("unsolved_goals", "Foo.lean", 42)
        assert h1 != h2

    def test_parse_error_structured(self):
        """Parse LeanMessage into StructuredError."""
        msg = LeanMessage(
            severity=MessageSeverity.ERROR,
            message="type mismatch at term\nhas type Nat\nbut expected Bool",
            position=Position(line=10, column=5),
            source="Foo.lean",
        )
        structured = parse_error_structured(msg)
        assert structured.error_type == "type_mismatch"
        assert structured.file == "Foo.lean"
        assert structured.line == 10
        assert structured.column == 5
        assert len(structured.error_hash) == 12

    def test_structured_error_cascade_compatible(self):
        """Cascade compatibility check."""
        msg_ok = LeanMessage(
            severity=MessageSeverity.ERROR,
            message="unsolved goals",
        )
        msg_skip = LeanMessage(
            severity=MessageSeverity.ERROR,
            message="unknown identifier 'foo'",
        )
        assert parse_error_structured(msg_ok).is_cascade_compatible is True
        assert parse_error_structured(msg_skip).is_cascade_compatible is False

    def test_structured_error_without_position(self):
        """StructuredError handles missing position gracefully."""
        msg = LeanMessage(
            severity=MessageSeverity.ERROR,
            message="some error",
        )
        structured = parse_error_structured(msg)
        assert structured.line == 0
        assert structured.column == 0
        assert structured.file == ""


# =============================================================================
# SORRY FILLER + CASCADE INTEGRATION
# =============================================================================

class TestSorryFillerCascade:
    """Tests para integracion SorryFiller + SolverCascade."""

    def _make_cascade(self, success_solver: str = None) -> SolverCascade:
        """Create mock SolverCascade."""
        cascade = MagicMock(spec=SolverCascade)

        async def mock_fill(code, sorry_line, **kwargs):
            if success_solver:
                return CascadeResult(
                    success=True,
                    solver=success_solver,
                    replacement_code=success_solver,
                    solvers_tried=1,
                )
            return CascadeResult(success=False, solvers_tried=9)

        cascade.try_fill_sorry = AsyncMock(side_effect=mock_fill)
        return cascade

    def test_fill_sorry_cascade_success(self):
        """SorryFiller uses cascade and succeeds."""
        cascade = self._make_cascade(success_solver="simp")
        filler = SorryFiller(solver_cascade=cascade)

        ctx = SorryContext(
            file_path="test.lean",
            line_number=2,
            goal="x + 0 = x",
            goal_type="equality",
        )
        result = _run(filler.fill_sorry_with_cascade(
            ctx, "theorem foo := by\n  sorry"
        ))

        assert result.chosen_solution is not None
        assert result.chosen_solution.strategy == "solver_cascade"
        assert result.chosen_solution.code == "simp"
        assert result.cascade_result is not None
        assert result.cascade_result.success is True

    def test_fill_sorry_cascade_fails_generates_candidates(self):
        """When cascade fails, candidates are generated."""
        cascade = self._make_cascade(success_solver=None)
        filler = SorryFiller(solver_cascade=cascade)

        ctx = SorryContext(
            file_path="test.lean",
            line_number=2,
            goal="Complex P Q R",
            goal_type="unknown",
        )
        result = _run(filler.fill_sorry_with_cascade(
            ctx, "theorem foo := by\n  sorry"
        ))

        assert result.chosen_solution is None
        assert len(result.candidates) > 0
        assert result.cascade_result is not None
        assert result.cascade_result.success is False

    def test_fill_sorry_without_cascade(self):
        """SorryFiller works without cascade (None)."""
        filler = SorryFiller(solver_cascade=None)

        ctx = SorryContext(
            file_path="test.lean",
            line_number=2,
            goal="1 = 1",
            goal_type="equality",
        )
        result = _run(filler.fill_sorry_with_cascade(
            ctx, "theorem foo := by\n  sorry"
        ))

        assert result.cascade_result is None
        assert len(result.candidates) > 0

    def test_sorry_filler_classify(self):
        """Classify sorry type correctly."""
        filler = SorryFiller()

        ctx = SorryContext(
            file_path="", line_number=0,
            goal="Continuous f", goal_type="",
        )
        assert filler.classify_sorry(ctx) == SorryType.MATHLIB_EXISTS

        ctx2 = SorryContext(
            file_path="", line_number=0,
            goal="x = x", goal_type="",
        )
        assert filler.classify_sorry(ctx2) == SorryType.NEEDS_TACTIC

    def test_sorry_filler_generate_candidates(self):
        """Generate candidates for different goal types."""
        filler = SorryFiller()

        ctx = SorryContext(
            file_path="test.lean",
            line_number=1,
            goal="1 = 1",
            goal_type="equality",
        )
        candidates = filler.generate_candidates(ctx)
        assert len(candidates) > 0
        assert any(c.strategy == "direct" for c in candidates)


# =============================================================================
# MES MEMORY + LEAN EXPERIENCE
# =============================================================================

class TestLeanMESIntegration:
    """Tests para integracion Lean -> MES memory."""

    def test_lean_success_recorded(self):
        """Successful Lean verification recorded as experience."""
        mem = MESMemory(econcept_min_records=2)

        record = ExperienceRecord(
            pattern_id="lean-tactics",
            success_value=1.0,
        )
        mem.add_record(record)

        stats = mem.stats
        assert stats["total_records"] == 1

    def test_lean_failure_recorded(self):
        """Failed Lean verification recorded with negative value."""
        mem = MESMemory()

        record = ExperienceRecord(
            pattern_id="lean-tactics",
            success_value=-0.5,
        )
        mem.add_record(record)

        records = mem.get_records_for_pattern("lean-tactics")
        assert len(records) == 1
        assert records[0].success_value == -0.5

    def test_econcept_from_lean_successes(self):
        """E-concept formed from multiple Lean successes."""
        mem = MESMemory(econcept_min_records=3)

        for i in range(3):
            record = ExperienceRecord(
                id=f"lean_{i}",
                pattern_id="lean-tactics",
                success_value=0.8 + i * 0.02,
            )
            mem.add_record(record)

        econcept = mem.try_form_concept(
            "lean-tactics", CoRegulatorType.TACTICAL
        )
        assert econcept is not None
        assert len(econcept.representative_records) == 3

    def test_lean_results_in_recall(self):
        """Lean results can be recalled by pattern."""
        mem = MESMemory()

        for val in [0.9, 0.7, 0.5, 0.3]:
            mem.add_record(ExperienceRecord(
                pattern_id="lean-tactics",
                success_value=val,
            ))

        similar = mem.recall_similar("lean-tactics", limit=2)
        assert len(similar) == 2
        assert similar[0].success_value >= similar[1].success_value

    def test_mixed_lean_patterns_separate(self):
        """Different Lean patterns don't interfere."""
        mem = MESMemory()

        mem.add_record(ExperienceRecord(
            pattern_id="lean-tactics", success_value=0.9,
        ))
        mem.add_record(ExperienceRecord(
            pattern_id="lean-sorry-fill", success_value=0.5,
        ))

        tactics_records = mem.get_records_for_pattern("lean-tactics")
        sorry_records = mem.get_records_for_pattern("lean-sorry-fill")
        assert len(tactics_records) == 1
        assert len(sorry_records) == 1
