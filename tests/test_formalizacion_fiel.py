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


# ---------------------------------------------------------------------------
# Lean verifica, pero LA NEGACIÓN de lo que se preguntó
# ---------------------------------------------------------------------------

class TestRefutacion:
    """Pedir algo falso no puede devolver una respuesta con sello de verificada.

    Lo destapó el banco de fidelidad con «demuestra que la raíz de 4 es
    irracional», que es falso. El modelo se comportó bien: detectó la falsedad,
    formalizó `¬ Irrational (Real.sqrt 4)` y lo dijo en un comentario del
    código. Era el pipeline el que no miraba — veía `SUCCESS` y estampaba la
    insignia sobre una respuesta a otra pregunta.

    Ahora el formalizador tiene un canal legible por máquina para lo que ya
    hacía por su cuenta, y hay un estado propio: la respuesta sigue estando
    respaldada por Lean, pero abre diciendo que el enunciado era falso.
    """

    @staticmethod
    def _detector():
        import re as _re

        def _p(code):
            # Misma logica que `_prueba_algo` en `_math_via_lean`: fuera
            # comentarios, y sin anclar en inicio de linea.
            limpio = _re.sub(r"/-[\s\S]*?-/", " ", code)
            limpio = _re.sub(r"--[^\n]*", " ", limpio)
            return bool(_re.search(r"\b(theorem|lemma|example)\b[\s\S]*?:=",
                                   limpio))
        return _p


    NO_PRUEBAN = [
        # el caso exacto del banco
        "import Mathlib\n#check @GrothendieckGroup\n#check @Module.Projective",
        "import Mathlib\n#eval 2 + 2\n#print axioms Nat",
        "import Mathlib\n-- solo un comentario",
        "import Mathlib\nopen Set Topology",
        "",
    ]

    PRUEBAN = [
        "import Mathlib\ntheorem t : 2 + 2 = 4 := by norm_num",
        "theorem t (a b : Set X) (ha : IsOpen a) (hb : IsOpen b) : IsOpen (a ∪ b) := ha.union hb",
        "lemma foo : True := trivial",
        "example : 1 = 1 := rfl",
        "@[simp]\ntheorem t : 1 = 1 := rfl",
        # con `sorry` SÍ cuenta como teorema: que quede un hueco lo detecta el
        # estado `parcial`, que es harina de otro costal
        "theorem t : IsOpen (∅ : Set ℕ) := by sorry",
    ]

    @pytest.mark.parametrize("code", NO_PRUEBAN)
    def test_reconoce_que_no_hay_prueba(self, code):
        assert not self._detector()(code), (
            "sin esto, Lean devuelve SUCCESS y la respuesta sale con sello de "
            "verificada sobre un archivo que no demuestra nada"
        )

    @pytest.mark.parametrize("code", PRUEBAN)
    def test_no_estorba_a_los_teoremas_de_verdad(self, code):
        assert self._detector()(code), (
            "un teorema legítimo marcado como «sin prueba» tiraría respuestas "
            "correctas"
        )


    NO_PRUEBAN_EXTRA = [
        # un comentario que MENCIONA teoremas no es un teorema
        "import Mathlib\n-- aqui iria un theorem, pero no lo hay\n#check Nat",
        "/-- docstring que habla de theorem y de := -/\nimport Mathlib",
    ]

    PRUEBAN_EXTRA = [
        # los que rompian la version anterior, anclada en inicio de linea
        "namespace Foo\n  theorem t : True := trivial\nend Foo",
        "theorem t\n    (a b : \u2115)\n    (h : a = b) :\n    b = a := h.symm",
    ]

    @pytest.mark.parametrize("code", NO_PRUEBAN_EXTRA)
    def test_los_comentarios_no_cuentan(self, code):
        """Un `-- theorem ...` o un docstring que hable de teoremas no es un
        teorema: por eso el detector limpia comentarios antes de mirar."""
        assert not self._detector()(code)

    @pytest.mark.parametrize("code", PRUEBAN_EXTRA)
    def test_no_exige_inicio_de_linea(self, code):
        """La version anterior anclaba en `^` y fallaba sobre codigo real por
        razones tontas —indentacion dentro de un `namespace`, una declaracion
        partida en varias lineas—, mandando a `sin_teorema` respuestas que si
        tenian teorema. Lo destapo el banco sobre la raiz de 4."""
        assert self._detector()(code)


    def test_el_pipeline_tiene_la_rama_y_va_antes_del_exito(self):
        """La rama debe evaluarse ANTES que la de éxito: si no, `is_success`
        gana y el archivo vacío vuelve a salir verificado."""
        import inspect
        fuente = inspect.getsource(Nucleo._math_via_lean)
        assert "_prueba_algo" in fuente
        i_sin = fuente.index('verification_status = "sin_teorema"')
        i_ok = fuente.index('verification_status = "verificado"')
        assert i_sin < i_ok, (
            "la rama de «sin teorema» va después de la de éxito: nunca se "
            "alcanza"
        )

    def test_no_se_presenta_como_verificado(self):
        import inspect
        fuente = inspect.getsource(Nucleo._math_via_lean)
        i = fuente.index("_titulo = {")
        bloque = fuente[i:i + 1200]
        assert '"sin_teorema"' in bloque, (
            "sin presentación propia cae en el genérico, que no dice lo que "
            "pasó: el código no contenía ningún teorema"
        )

    def test_la_confianza_baja(self):
        """A diferencia de la refutación —que sí está respaldada— aquí no hay
        nada demostrado, y la confianza tiene que reflejarlo."""
        import inspect
        fuente = inspect.getsource(Nucleo._math_via_lean)
        i = fuente.index('verification_status = "sin_teorema"')
        bloque = fuente[i:i + 400]
        assert "confidence    = 0.30" in bloque
        assert "success_value = 0.0" in bloque
