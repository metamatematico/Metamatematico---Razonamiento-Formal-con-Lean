"""
Tests de integración: _math_via_lean → domain_tactic → SolverCascade
=====================================================================

Verifica la cadena completa (paper §3.5, Principio 3.1):
  classify_query(text) → domain_default_tactic(area) → GoalAnalyzer.prioritize()
    → try_fill_sorry_smart(domain_tactic=...) → cascade con táctica del área primero

Todos los tests son síncronos o usan mocks — no requieren Lean instalado.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─── Clasificación de área ────────────────────────────────────────────────────

class TestClassifyQuery:
    def test_algebra_keywords_spanish(self):
        from nucleo.multi_agent.specialized_agent import classify_query
        assert classify_query("Demuestra que todo grupo abeliano es conmutativo") == "algebra"

    def test_algebra_keywords_english(self):
        from nucleo.multi_agent.specialized_agent import classify_query
        assert classify_query("Prove that every abelian group is commutative") == "algebra"

    def test_number_theory_keywords_spanish(self):
        from nucleo.multi_agent.specialized_agent import classify_query
        assert classify_query("Prueba que hay infinitos numeros primo") == "number-theory"

    def test_number_theory_keywords_english(self):
        from nucleo.multi_agent.specialized_agent import classify_query
        assert classify_query("Prove there are infinitely many prime numbers") == "number-theory"

    def test_logic_keywords_spanish(self):
        from nucleo.multi_agent.specialized_agent import classify_query
        assert classify_query("Demuestra usando logica de primer orden FOL deduccion logica") == "logic"

    def test_logic_keywords_english(self):
        from nucleo.multi_agent.specialized_agent import classify_query
        assert classify_query("Prove this using first-order logic FOL predicate") == "logic"

    def test_topology_keywords_spanish(self):
        from nucleo.multi_agent.specialized_agent import classify_query
        assert classify_query("Sea X un espacio topologico compacto hausdorff") == "topology"

    def test_lean_tactics_keywords(self):
        from nucleo.multi_agent.specialized_agent import classify_query
        result = classify_query("Como usar simp y ring en Lean 4 para cerrar goals")
        assert result == "lean-tactics"

    def test_optimization_keywords_spanish(self):
        from nucleo.multi_agent.specialized_agent import classify_query
        assert classify_query("Minimizar funcion con optimizacion y restricciones") == "optimization"

    def test_returns_valid_category(self):
        from nucleo.multi_agent.specialized_agent import classify_query, CATEGORIES
        for text in ["x", "integral convergencia", "grupo abeliano", "homotopia topologia"]:
            cat = classify_query(text)
            assert cat in CATEGORIES, f"classify_query({text!r}) = {cat!r} no es categoria valida"


# ─── domain_default_tactic ────────────────────────────────────────────────────

class TestDomainDefaultTactic:
    def test_known_categories(self):
        from nucleo.multi_agent.colimit_agents import domain_default_tactic, CATEGORY_DEFAULT_TACTICS
        for cat, expected in CATEGORY_DEFAULT_TACTICS.items():
            assert domain_default_tactic(cat) == expected

    def test_unknown_category_returns_simp(self):
        from nucleo.multi_agent.colimit_agents import domain_default_tactic
        assert domain_default_tactic("nonexistent-area") == "simp"

    def test_algebra_returns_ring(self):
        from nucleo.multi_agent.colimit_agents import domain_default_tactic
        assert domain_default_tactic("algebra") == "ring"

    def test_optimization_returns_linarith(self):
        from nucleo.multi_agent.colimit_agents import domain_default_tactic
        assert domain_default_tactic("optimization") == "linarith"

    def test_number_theory_returns_norm_num(self):
        from nucleo.multi_agent.colimit_agents import domain_default_tactic
        assert domain_default_tactic("number-theory") == "norm_num"

    def test_all_tactics_are_strings(self):
        from nucleo.multi_agent.colimit_agents import CATEGORY_DEFAULT_TACTICS
        for cat, tac in CATEGORY_DEFAULT_TACTICS.items():
            assert isinstance(tac, str) and tac, f"Táctica vacía para {cat!r}"


# ─── GoalAnalyzer.prioritize con domain_tactic ───────────────────────────────

class TestGoalAnalyzerPrioritize:
    def setup_method(self):
        from nucleo.lean.solver_cascade import GoalAnalyzer, SOLVER_CASCADE
        self.analyzer = GoalAnalyzer()
        self.all_names = {name for name, _ in SOLVER_CASCADE}

    def test_domain_tactic_placed_first(self):
        order = self.analyzer.prioritize("a * b = b * a", domain_tactic="ring")
        assert order[0][0] == "ring", f"Esperaba 'ring' primero, got {order[0][0]!r}"

    def test_domain_tactic_first_overrides_pattern(self):
        # El goal pattern detectaría "omega" para aritmética natural,
        # pero domain_tactic="linarith" debe ir primero
        order = self.analyzer.prioritize("n + 0 = n", domain_tactic="linarith")
        assert order[0][0] == "linarith"

    def test_unknown_domain_tactic_ignored(self):
        from nucleo.lean.solver_cascade import SOLVER_CASCADE
        order = self.analyzer.prioritize("a = b", domain_tactic="nonexistent")
        # Si la táctica no está en SOLVER_CASCADE, no aparece en la lista
        names = [n for n, _ in order]
        assert "nonexistent" not in names

    def test_all_cascade_solvers_present(self):
        from nucleo.lean.solver_cascade import SOLVER_CASCADE
        order = self.analyzer.prioritize("a + b = b + a", domain_tactic="ring")
        returned_names = {n for n, _ in order}
        # Todos los solvers del cascade deben estar presentes
        for name, _ in SOLVER_CASCADE:
            assert name in returned_names, f"Solver {name!r} desapareció del cascade"

    def test_no_domain_tactic_uses_pattern(self):
        # Sin domain_tactic, el patrón ring/nlinarith debe liderar para algebra
        order = self.analyzer.prioritize("a * b + c = d * e - f")
        assert order[0][0] in {"ring", "nlinarith", "linarith"}

    def test_empty_goal_no_domain_tactic_returns_default(self):
        from nucleo.lean.solver_cascade import SOLVER_CASCADE
        order = self.analyzer.prioritize("")
        assert order == list(SOLVER_CASCADE)


# ─── SolverCascade.try_fill_sorry_smart con domain_tactic ────────────────────

class TestSolverCascadeSmartDomainTactic:
    def _make_cascade(self, succeeds_on: str):
        """Crea SolverCascade con LeanClient mock que acepta `succeeds_on`."""
        from nucleo.lean.solver_cascade import SolverCascade, CascadeResult
        from nucleo.lean.client import LeanResult, LeanResultStatus

        tried = []

        async def fake_check(code: str) -> LeanResult:
            tried.append(code)
            # Éxito si el código contiene el solver esperado (reemplazó sorry)
            success = succeeds_on in code
            return LeanResult(
                status=LeanResultStatus.SUCCESS if success else LeanResultStatus.ERROR,
                output="",
            )

        lean_mock = MagicMock()
        lean_mock.check_code = fake_check

        cascade = SolverCascade(lean_client=lean_mock)
        cascade._tried = tried
        return cascade

    def test_domain_tactic_tried_before_others(self):
        cascade = self._make_cascade(succeeds_on="ring")
        code = "theorem t : a * b = b * a := by\n  sorry"

        result = asyncio.run(cascade.try_fill_sorry_smart(
            code=code,
            sorry_line=2,
            goal_text="a * b = b * a",
            domain_tactic="ring",
        ))

        assert result.success
        assert result.solver == "ring"
        # ring debe haber sido el primer intento (1 intento total si funciona)
        assert result.solvers_tried == 1

    def test_domain_tactic_fallback_if_first_fails(self):
        cascade = self._make_cascade(succeeds_on="omega")
        code = "theorem t : n + 0 = n := by\n  sorry"

        result = asyncio.run(cascade.try_fill_sorry_smart(
            code=code,
            sorry_line=2,
            goal_text="n + 0 = n",
            domain_tactic="ring",  # ring falla, omega tendrá que resolverlo
        ))

        assert result.success
        assert result.solver == "omega"
        assert result.solvers_tried > 1

    def test_no_domain_tactic_falls_back_to_try_fill_sorry(self):
        """Sin goal ni domain_tactic, delega a try_fill_sorry."""
        cascade = self._make_cascade(succeeds_on="simp")
        code = "theorem t : True := by\n  sorry"

        result = asyncio.run(cascade.try_fill_sorry_smart(
            code=code,
            sorry_line=2,
            goal_text="",
            domain_tactic="",
        ))

        assert result.success
        assert result.solver == "simp"


# ─── fill_sorry_with_cascade: skip_cascade evita redundancia ─────────────────

class TestFillSorryWithCascadeSkipCascade:
    def _make_filler(self):
        from nucleo.lean.sorry_filler import SorryFiller
        from nucleo.lean.solver_cascade import SolverCascade
        from nucleo.lean.client import LeanResult, LeanResultStatus

        cascade_calls = []

        async def fake_check(code: str) -> LeanResult:
            cascade_calls.append(code)
            return LeanResult(
                status=LeanResultStatus.ERROR, output=""
            )

        lean_mock = MagicMock()
        lean_mock.check_code = fake_check

        cascade = SolverCascade(lean_client=lean_mock)
        filler = SorryFiller(solver_cascade=cascade)
        return filler, cascade_calls

    def test_skip_cascade_true_skips_solver_attempts(self):
        from nucleo.lean.sorry_filler import SorryContext
        filler, calls = self._make_filler()

        ctx = SorryContext(
            file_path="test.lean", line_number=2,
            goal="a = a", goal_type="", surrounding_code=""
        )
        code = "theorem t : a = a := by\n  sorry"

        asyncio.run(filler.fill_sorry_with_cascade(ctx, code, skip_cascade=True))
        assert len(calls) == 0, f"skip_cascade=True no debe llamar al checker, llamó {len(calls)} veces"

    def test_skip_cascade_false_runs_solver_attempts(self):
        from nucleo.lean.sorry_filler import SorryContext
        filler, calls = self._make_filler()

        ctx = SorryContext(
            file_path="test.lean", line_number=2,
            goal="a = a", goal_type="", surrounding_code=""
        )
        code = "theorem t : a = a := by\n  sorry"

        asyncio.run(filler.fill_sorry_with_cascade(ctx, code, skip_cascade=False))
        assert len(calls) > 0, "skip_cascade=False debe intentar los solvers"


# ─── Pipeline completo: classify → tactic → cascade (mocked) ─────────────────

class TestDomainTacticPipelineIntegration:
    """
    Verifica que _try_solve_sorries pasa domain_tactic a try_fill_sorry_smart
    y que skip_cascade=True se pasa a fill_sorry_with_cascade cuando el
    smart cascade ya corrió.
    """

    def test_pipeline_algebra_uses_ring_first(self):
        from nucleo.multi_agent.specialized_agent import classify_query
        from nucleo.multi_agent.colimit_agents import domain_default_tactic
        from nucleo.lean.solver_cascade import GoalAnalyzer

        area = classify_query("Demuestra que los grupos abelianos son conmutativos")
        tactic = domain_default_tactic(area)
        assert tactic == "ring"

        order = GoalAnalyzer().prioritize("a * b = b * a", domain_tactic=tactic)
        assert order[0][0] == "ring"

    def test_pipeline_optimization_uses_linarith_first(self):
        from nucleo.multi_agent.specialized_agent import classify_query
        from nucleo.multi_agent.colimit_agents import domain_default_tactic
        from nucleo.lean.solver_cascade import GoalAnalyzer

        area = classify_query("Minimizar funcion convexa con optimizacion y restricciones")
        assert area == "optimization"
        tactic = domain_default_tactic(area)
        assert tactic == "linarith"

        order = GoalAnalyzer().prioritize("x >= 0 -> f x >= 0", domain_tactic=tactic)
        assert order[0][0] == "linarith"

    def test_skip_cascade_prevents_double_attempt(self):
        """
        Cuando try_fill_sorry_smart falla, fill_sorry_with_cascade con
        skip_cascade=True NO re-intenta los mismos solvers.
        """
        from nucleo.lean.sorry_filler import SorryFiller, SorryContext
        from nucleo.lean.solver_cascade import SolverCascade
        from nucleo.lean.client import LeanResult, LeanResultStatus

        total_checks = []

        async def always_fail(code: str) -> LeanResult:
            total_checks.append(code)
            return LeanResult(status=LeanResultStatus.ERROR, output="")

        lean_mock = MagicMock()
        lean_mock.check_code = always_fail

        cascade = SolverCascade(lean_client=lean_mock)
        filler = SorryFiller(solver_cascade=cascade)

        ctx = SorryContext(
            file_path="t.lean", line_number=2,
            goal="a = b", goal_type="", surrounding_code=""
        )
        code = "theorem t : a = b := by\n  sorry"

        # Simula lo que hace _try_solve_sorries:
        # 1. try_fill_sorry_smart (falla, N intentos)
        async def run():
            r1 = await cascade.try_fill_sorry_smart(
                code=code, sorry_line=2,
                goal_text="a = b", domain_tactic="ring"
            )
            n_smart = len(total_checks)
            assert not r1.success

            # 2. fill_sorry_with_cascade(skip_cascade=True) → 0 intentos extra
            r2 = await filler.fill_sorry_with_cascade(ctx, code, skip_cascade=True)
            n_total = len(total_checks)
            assert n_total == n_smart, (
                f"skip_cascade=True debe añadir 0 intentos, añadió {n_total - n_smart}"
            )

        asyncio.run(run())
