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

    def test_algebra_returns_simp(self):
        """Era `ring`, y `ring` no cierra NI UNA prueba de algebra en Mathlib.

        Medido sobre las pruebas que se cierran en una linea, restringido a las
        tacticas que SOLVER_CASCADE ofrece: simp 93 %, aesop 5 %, rfl 2 %, ring
        0 %. El valor viejo no era una opinion discutible: era falso.
        """
        from nucleo.multi_agent.colimit_agents import domain_default_tactic
        assert domain_default_tactic("algebra") == "simp"

    def test_optimization_returns_linarith(self):
        from nucleo.multi_agent.colimit_agents import domain_default_tactic
        assert domain_default_tactic("optimization") == "linarith"

    def test_number_theory_returns_simp(self):
        """`norm_num` era la 4a de 4 en su propia area, con un 3 %."""
        from nucleo.multi_agent.colimit_agents import domain_default_tactic
        assert domain_default_tactic("number-theory") == "simp"

    def test_optimization_sigue_sin_medir(self):
        """Mathlib no tiene esta area: se conserva lo que habia, y se declara.

        Que viva en CATEGORY_TACTIC_ORDER_SIN_MEDIR y no en la tabla medida es
        la diferencia entre «comprobado» y «no hay nada mejor». Meterla con las
        demas borraria esa distincion.
        """
        from nucleo.multi_agent.colimit_agents import (
            CATEGORY_TACTIC_ORDER, CATEGORY_TACTIC_ORDER_SIN_MEDIR)
        assert "optimization" in CATEGORY_TACTIC_ORDER_SIN_MEDIR
        assert "optimization" not in CATEGORY_TACTIC_ORDER

    def test_el_orden_medido_empieza_por_simp(self):
        """`simp` gana en las ONCE areas medidas, sin excepcion.

        Por eso el area no discrimina en la cabeza, y por eso la tabla es una
        LISTA: lo que distingue un area de otra esta en la cola.
        """
        from nucleo.multi_agent.colimit_agents import CATEGORY_TACTIC_ORDER
        malas = [a for a, o in CATEGORY_TACTIC_ORDER.items() if o[0] != "simp"]
        assert not malas, "areas medidas que no empiezan por simp: %s" % malas

    def test_todo_el_orden_medido_esta_en_la_cascada(self):
        """Proponer una tactica que la cascada no ofrece es no proponer nada.

        Asi eran inertes `tauto` (logic) y `decide` (computation): la tabla
        vieja las nombraba y `prioritize` las descartaba en silencio, con lo
        que esas dos areas creian tener prior y no tenian ninguno.
        """
        from nucleo.lean.solver_cascade import SOLVER_CASCADE
        from nucleo.multi_agent.colimit_agents import (
            CATEGORY_TACTIC_ORDER, CATEGORY_TACTIC_ORDER_SIN_MEDIR)
        disponibles = {n for n, _ in SOLVER_CASCADE}
        fuera = [(a, t)
                 for tabla in (CATEGORY_TACTIC_ORDER,
                               CATEGORY_TACTIC_ORDER_SIN_MEDIR)
                 for a, orden in tabla.items() for t in orden
                 if t not in disponibles]
        assert not fuera, "tacticas que la cascada no puede ofrecer: %s" % fuera

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

    def test_domain_tactic_cuando_el_goal_no_dice_nada(self):
        """Sin patron que case, el prior del area es lo unico que hay."""
        order = self.analyzer.prioritize("n + 0 = n", domain_tactic="linarith")
        assert order[0][0] == "linarith"

    def test_el_goal_manda_sobre_el_area(self):
        """LA INVERSION QUE SE ARREGLO.

        `domain_tactic` iba primero, por delante de los patrones del objetivo.
        Como el prior del area estaba mal en 7 de 11 areas, desplazaba a la
        unica senal que discrimina — y cada intento fallido cuesta una
        invocacion de Lean.
        """
        order = [n for n, _ in self.analyzer.prioritize(
            "2 + 3 = 5", domain_tactic="aesop")]
        assert order[0] != "aesop", "el area volvio a colarse delante del goal"
        assert "aesop" in order, "y sin embargo debe seguir estando, detras"
        assert order.index("omega") < order.index("aesop")

    def test_la_aprendida_va_delante_del_orden_medido(self):
        """Exito real en este sistema pesa mas que la frecuencia en Mathlib."""
        order = [n for n, _ in self.analyzer.prioritize(
            "P x", domain_tactic="omega", domain_order=["simp", "ring"])]
        assert order.index("omega") < order.index("simp")

    def test_el_orden_del_area_se_respeta_entero(self):
        order = [n for n, _ in self.analyzer.prioritize(
            "P x", domain_order=["aesop", "ring", "linarith"])]
        assert order.index("aesop") < order.index("ring") < order.index("linarith")

    def test_reordenar_es_una_permutacion(self):
        """La soundness no depende del orden, pero perder un solver si duele.

        Se comprueba que ninguno desaparezca ni se duplique: es lo unico que
        podria hacer que la cascada dejara de intentar algo que antes probaba.
        """
        from nucleo.lean.solver_cascade import SOLVER_CASCADE
        for kwargs in ({"domain_tactic": "ring"},
                       {"domain_order": ["simp", "aesop"]},
                       {"domain_tactic": "omega", "domain_order": ["simp"]},
                       {}):
            order = self.analyzer.prioritize("a * b + c = d * e", **kwargs)
            assert sorted(order) == sorted(SOLVER_CASCADE), kwargs

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
            # Y LA MARCA que Lean imprime desde la rama ganadora: con las doce
            # tacticas en un solo `first |`, todos los nombres estan en el
            # codigo y «contiene `ring`» ya no identifica a la ganadora.
            return LeanResult(
                status=LeanResultStatus.SUCCESS if success else LeanResultStatus.ERROR,
                messages=([{"severity": "information",
                            "data": "ELEGIDA:" + succeeds_on}] if success else []),
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
        from nucleo.multi_agent.colimit_agents import (
            domain_default_tactic, domain_tactic_order)
        from nucleo.lean.solver_cascade import GoalAnalyzer

        area = classify_query("Demuestra que los grupos abelianos son conmutativos")
        assert domain_default_tactic(area) == "simp"   # medido; antes "ring"

        # Y aun asi `ring` sale primera, porque `a * b = b * a` es una
        # identidad de anillo y el PATRON DEL OBJETIVO la detecta. Esa es la
        # diferencia entre saberlo por el area (mal) y por el objetivo (bien).
        order = GoalAnalyzer().prioritize(
            "a * b = b * a", domain_order=domain_tactic_order(area))
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
