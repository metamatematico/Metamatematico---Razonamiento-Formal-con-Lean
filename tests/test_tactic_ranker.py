"""
Tests del rankeador de tacticas entrenado sobre LeanWorkbook.

Sustituye al ranking por similitud coseno del GNN, que daba cosenos de
0,01-0,09 —embeddings practicamente ortogonales al goal— porque la red se
entreno con etiqueta CONSTANTE (`todo -> ASSIST`) y nunca vio una senal
discriminativa. El efecto practico era el peor posible: mandaba `exact?` y
`apply?` —los dos solvers mas caros— al principio de la cascada, y `rfl`,
`linarith` y `nlinarith` —los mas baratos— al final, por no estar en el mapa
de skills. Invertia la cascada por coste.

El modelo actual se midio sobre 9.488 pares (state_before -> tactic):
    accuracy 59,7%  ·  base mayoritaria 31,8%  ·  top-3 88,1%
"""
import pytest

from nucleo.lean.solver_cascade import SOLVER_CASCADE, TacticRanker


@pytest.fixture(scope="module")
def ranker() -> TacticRanker:
    r = TacticRanker()
    if not r.disponible:
        pytest.skip("no hay data/tactic_ranker.pkl "
                    "(ejecuta scripts/train_tactic_ranker.py)")
    return r


class TestSoundness:
    """La propiedad de la que depende el teorema cascade_gnn_iff_exists."""

    def test_es_una_permutacion(self, ranker):
        """
        Reordenar no puede anadir ni quitar tacticas.

        Es la hipotesis del axioma `gnnRankTactics_perm`
        (CoRegulatorNetwork.lean): si el ranking es una permutacion, la
        soundness no depende del orden y este queda libre para optimizar.
        """
        base = list(SOLVER_CASCADE)
        goals = [
            "x : ℝ ⊢ x ^ 2 - 2 * x - 24 < 0",
            "n : ℕ ⊢ n % 2 = 0 ∨ n % 2 = 1",
            "a b : ℝ ⊢ (a + b) ^ 2 = a ^ 2 + 2 * a * b + b ^ 2",
            "",                      # goal vacio
            "texto que no es un goal de Lean",
        ]
        for g in goals:
            out = ranker.rank(g, base)
            assert sorted(n for n, _ in out) == sorted(n for n, _ in base), (
                f"el ranking no es una permutacion para {g!r}"
            )
            assert len(out) == len(base)

    def test_conserva_los_timeouts(self, ranker):
        base = list(SOLVER_CASCADE)
        out = ranker.rank("n : ℕ ⊢ n + 0 = n", base)
        assert dict(out) == dict(base)


class TestDiscriminacion:
    """Que el orden dependa del goal — lo que el GNN degenerado no hacia."""

    def test_ordenes_distintos_para_goals_distintos(self, ranker):
        base = list(SOLVER_CASCADE)
        ordenes = {
            tuple(n for n, _ in ranker.rank(g, base))
            for g in [
                "n : ℕ ⊢ n % 2 = 0 ∨ n % 2 = 1",
                "x : ℝ hx : x ≠ 0 ⊢ 1 / x * x = 1",
                "a b : ℝ ⊢ (a + b) ^ 2 = a ^ 2 + 2 * a * b + b ^ 2",
            ]
        }
        assert len(ordenes) >= 2, (
            "el rankeador devuelve el mismo orden para goals distintos: "
            "no esta discriminando"
        )

    @pytest.mark.parametrize("goal,esperada", [
        ("n : ℕ ⊢ n % 2 = 0 ∨ n % 2 = 1", "omega"),
        ("x : ℝ hx : x ≠ 0 ⊢ 1 / x * x = 1", "field_simp"),
    ])
    def test_elige_la_tactica_adecuada(self, ranker, goal, esperada):
        """La tactica correcta debe entrar en el top-3 (medido: 88,1%)."""
        top3 = [n for n, _ in ranker.rank(goal, list(SOLVER_CASCADE))[:3]]
        assert esperada in top3, f"{esperada} no esta en el top-3: {top3}"

    def test_no_hunde_los_solvers_fuera_del_vocabulario(self, ranker):
        """
        exact? y apply? no estan en el vocabulario del modelo, pero no deben
        caer siempre al fondo por ello: reciben la mediana, no cero.

        El ranker anterior daba 0.0 a los no mapeados y los hundia, que fue
        como `rfl` —el solver mas barato— acabo el ultimo.
        """
        base = list(SOLVER_CASCADE)
        posiciones = []
        for g in ["n : ℕ ⊢ n + 0 = n", "x : ℝ ⊢ x = x", "⊢ True"]:
            orden = [n for n, _ in ranker.rank(g, base)]
            posiciones.append(orden.index("exact?"))
        assert min(posiciones) < len(base) - 1, (
            "exact? queda siempre el ultimo: los solvers sin vocabulario se "
            "estan hundiendo en vez de recibir puntuacion neutra"
        )


class TestCascada:

    def test_la_cascada_incluye_las_tacticas_frecuentes(self):
        """
        norm_num, field_simp y ring_nf faltaban pese a ser de las mas usadas
        en LeanWorkbook (1.142, 1.306 y 447 usos sobre 18.985 pruebas).
        """
        nombres = {n for n, _ in SOLVER_CASCADE}
        for t in ("norm_num", "field_simp", "ring_nf"):
            assert t in nombres, f"la cascada no incluye {t}"

    def test_los_timeouts_son_razonables(self):
        for nombre, t in SOLVER_CASCADE:
            assert 0 < t <= 10, f"{nombre} tiene un timeout raro: {t}"
