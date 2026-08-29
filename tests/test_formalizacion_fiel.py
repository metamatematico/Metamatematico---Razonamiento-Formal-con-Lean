"""
El teorema que Lean verifica tiene que ser el que se preguntó.

Este archivo existe por un defecto que ninguna suite habría encontrado: el
sistema respondía «VERIFICADO» a teoremas que nadie había preguntado. La cadena
funcionaba —el LLM formalizaba, Lean verificaba, el LLM traducía— y el resultado
era correcto como matemática y falso como respuesta.

Cadena medida sobre «¿Cuánto es 127 + 458?»:

  1. el LLM formaliza bien:  `theorem : 127 + 458 = 585 := by norm_num`
  2. el detector de tautologías lo marca como TRIVIAL — falso positivo
  3. el reintento le ordena usar «geometría euclidiana o espacios con producto
     interior», que estaba CABLEADO en el prompt
  4. Lean verifica el teorema sobre vectores ortogonales, que es cierto
  5. la respuesta sale con insignia de verificada

El paso 2 fallaba por un patrón que casa con `:= by` al final de línea, o sea
con toda prueba táctica multilínea. El paso 3 convertía cada falso positivo en
un cambio de rama matemática.
"""
import sys

import pytest

sys.argv = ["x"]
from nucleo.core import Nucleo


def _trivial(code: str) -> bool:
    """Llama al detector, que vive dentro de `_math_via_lean`."""
    import inspect
    import re as _re
    fuente = inspect.getsource(Nucleo._math_via_lean)
    ini = fuente.index("def _is_trivial_lean")
    fin = fuente.index("if _is_trivial_lean(lean_code):")
    cuerpo = "\n".join(l[8:] if l.startswith(" " * 8) else l
                       for l in fuente[ini:fin].splitlines())
    ns: dict = {}
    exec(cuerpo, {"re": _re}, ns)
    return ns["_is_trivial_lean"](code)


# ---------------------------------------------------------------------------
# Lo que NO es una tautología, y se marcaba como tal
# ---------------------------------------------------------------------------

NO_TRIVIALES = [
    # el caso exacto que disparó el fallo
    "import Mathlib\n\ntheorem add_127_458 : 127 + 458 = 585 := by\n  norm_num",
    # cualquier prueba táctica multilínea
    "theorem t (a b : ℕ) : (a+b)^2 = a^2+2*a*b+b^2 := by\n  ring",
    "theorem t : 2 + 2 = 4 := by decide",
    # con hipótesis, pero probado de verdad
    "theorem t (h : 0 < n) : n ≠ 0 := by\n  omega",
    "theorem t (ha : 0 < a) (hb : 0 < b) : 0 < a * b := by\n  positivity",
    # sin hipótesis en absoluto: imposible que sea tautología
    "theorem t : Irrational (Real.sqrt 2) := by\n  exact irrational_sqrt_two",
]

TRIVIALES = [
    # devolver la hipótesis tal cual
    "theorem t (h : a^2 + b^2 = c^2) : a^2 + b^2 = c^2 := h",
    # devolverla con symm
    "theorem t (h : a^2 + b^2 = c^2) : c^2 = a^2 + b^2 := h.symm",
    # lo mismo, envuelto en una táctica
    "theorem t (h : x = y) : x = y := by exact h",
    "theorem t (h : x = y) : y = x := by exact h.symm",
]


@pytest.mark.parametrize("code", NO_TRIVIALES)
def test_no_marca_trivial_lo_que_no_lo_es(code):
    assert not _trivial(code), (
        "falso positivo: el reintento se dispara y cambia de tema, y la "
        "respuesta sale verificada sobre un teorema que nadie preguntó"
    )


@pytest.mark.parametrize("code", TRIVIALES)
def test_si_marca_las_tautologias_de_verdad(code):
    assert _trivial(code), "una tautología pasó el filtro"


def test_por_by_al_final_de_linea_no_basta():
    """El patrón concreto que rompía todo: `:= by` cerrando la línea."""
    assert not _trivial("theorem t : 1 = 1 := by\n  rfl")
    assert not _trivial("theorem t (n : ℕ) : n + 0 = n := by\n  simp")


# ---------------------------------------------------------------------------
# El reintento no puede elegir la matemática
# ---------------------------------------------------------------------------

class TestElReintentoNoCambiaDeTema:

    @staticmethod
    def _prompt_del_reintento() -> str:
        """Solo el literal del prompt — sin comentarios.

        Los comentarios del arreglo NOMBRAN los términos que estaban cableados,
        para que se entienda qué se rompió; escanear el fuente entero los
        confundiría con el defecto.
        """
        import ast
        import inspect
        fuente = inspect.getsource(Nucleo._math_via_lean)
        arbol = ast.parse("if True:" + chr(10) + fuente)
        for nodo in ast.walk(arbol):
            if (isinstance(nodo, ast.Assign)
                    and any(getattr(t, "id", "") == "retry_prompt"
                            for t in nodo.targets)):
                return ast.unparse(nodo.value)
        raise AssertionError("no encuentro retry_prompt")

    def test_no_hay_dominio_cableado_en_el_prompt(self):
        retry = self._prompt_del_reintento()
        for cableado in ("geometría euclidiana", "geometria euclidiana",
                         "producto interior", "inner_mul_le_norm_sq",
                         "norm_add_sq_real", "EuclideanSpace"):
            assert cableado not in retry, (
                f"«{cableado}» está cableado en el reintento: cada falso "
                "positivo del detector arrastra la consulta a esa rama"
            )

    def test_el_reintento_manda_volver_al_enunciado(self):
        retry = self._prompt_del_reintento()
        assert "ORIGINAL" in retry
        assert "No cambies de tema" in retry
