# -*- coding: utf-8 -*-
"""El PDF es lo que el alumno se lleva: no puede estropear el código.

DOS FALLOS, LOS DOS VISTOS EN UN PDF REAL del teorema fundamental del cálculo.

1 · EL GUION BAJO SE TRATABA COMO CURSIVA SIEMPRE

    `_{1,2}([^_]+)_{1,2}` emparejaba cualquier par de guiones bajos:

        intervalIntegral.integral_eq_sub_of_hasDerivAt
          -> intervalIntegral.integraleqsubofhasDerivAt
        \\int_a^b f(x)\\,dx
          -> \\inta^b f(x)\\,dx

    El nombre del lema salía inservible —no se puede copiar— y además parece
    otro nombre, UNO QUE NO EXISTE. Un sistema que acaba de arreglar un
    diagnóstico por afirmar que un lema real no existía, imprimía en el PDF un
    lema inexistente. Y todos los subíndices de LaTeX se perdían, así que las
    fórmulas decían otra matemática.

2 · EL BLOQUE DE CODIGO ERA LO PEOR RENDERIZADO DEL DOCUMENTO

        theorem ftc_evaluation (f F : ? ? ?) (a b : ?)
          ? x in a..b, f x = F b - F a := by

    Se pintaba con `Courier` —fuente núcleo, sólo latin-1— y se codificaba con
    `encode('latin-1', errors='replace')` SIN pasar por la tabla de símbolos.
    La prosa de al lado leía `R -> R` perfectamente. O sea que la única pieza
    con respaldo formal de todo el PDF era la ilegible.
"""
import pytest

from nucleo.utils.pdf_export import _strip_markdown

LEMA = "intervalIntegral.integral_eq_sub_of_hasDerivAt"


class TestElGuionBajoNoEsSiempreCursiva:

    def test_el_nombre_del_lema_sobrevive(self):
        salida = _strip_markdown("se aplica %s con hderiv" % LEMA)
        assert LEMA in salida, (
            "el PDF imprimía un nombre de lema que NO EXISTE, que es justo lo "
            "que este sistema existe para no producir")

    @pytest.mark.parametrize("formula", [
        r"\int_a^b f(x)\,dx = F(b) - F(a)",
        r"\frac{1}{h}\int_x^{x+h} f(t)\,dt",
        r"\sum_{i=0}^n a_i",
    ])
    def test_los_subindices_de_latex_sobreviven(self, formula):
        assert _strip_markdown(formula) == formula

    def test_snake_case_cualquiera_sobrevive(self):
        t = "usa add_comm y mul_le_mul_of_nonneg_left"
        assert _strip_markdown(t) == t

    def test_la_cursiva_de_verdad_si_se_quita(self):
        """El arreglo no puede dejar de hacer su trabajo."""
        assert _strip_markdown("esto va en _cursiva_ aquí") == \
            "esto va en cursiva aquí"
        assert _strip_markdown("y en __negrita__ aquí") == "y en negrita aquí"

    def test_no_cruza_lineas(self):
        """Dos guiones lejanos en líneas distintas no son un par."""
        t = "primera var_uno\nsegunda var_dos"
        assert _strip_markdown(t) == t


class TestElCodigoLeanSaleLiteral:

    @pytest.fixture(scope="class")
    def texto_del_pdf(self):
        from nucleo.utils.pdf_export import generate_pdf
        lean = (
            "theorem ftc (f F : ℝ → ℝ) (a b : ℝ)\n"
            "    (h : ∀ x ∈ Set.uIcc a b, HasDerivAt F (f x) x) :\n"
            "    ∫ x in a..b, f x = F b - F a := by\n"
            "  exact %s h\n" % LEMA
        )
        datos = generate_pdf(query="el teorema fundamental del calculo",
                             response="usa `%s`" % LEMA,
                             lean_code=lean, confidence=0.95,
                             area="analysis", status="verificado")
        try:
            from pypdf import PdfReader
        except ImportError:                                     # pragma: no cover
            try:
                from PyPDF2 import PdfReader
            except ImportError:
                pytest.skip("sin pypdf: no se puede releer el PDF")
        import io as _io
        return "\n".join(p.extract_text() or ""
                         for p in PdfReader(_io.BytesIO(datos)).pages)

    def test_el_nombre_del_lema_esta_entero(self, texto_del_pdf):
        assert LEMA in texto_del_pdf

    @pytest.mark.parametrize("simbolo,nombre", [
        ("ℝ", "los reales"),
        ("→", "la flecha"),
        ("∫", "la integral"),
    ])
    def test_los_simbolos_de_lean_no_son_interrogantes(
            self, texto_del_pdf, simbolo, nombre):
        assert simbolo in texto_del_pdf, (
            "%s (%s) no aparece: el codigo que Lean verifico sale ilegible "
            "en el unico documento que el alumno se lleva" % (nombre, simbolo))


def test_solo_se_translitera_lo_que_la_fuente_no_tiene():
    """Ni todo ni nada: sólo los glifos ausentes.

    La alternativa que había era binaria —`?` para todo, o transliterar
    entero— y las dos estropean el código: la primera lo hace ilegible, la
    segunda produce algo que parece Lean y no compila.
    """
    from nucleo.utils.pdf_export import _solo_lo_que_falte
    # una fuente que tiene ASCII y la flecha, pero no la integral
    cubre = set(range(32, 127)) | {0x2192}
    out = _solo_lo_que_falte("f : A → B, ∫ x", cubre)
    assert "→" in out, "no se toca lo que la fuente SI sabe dibujar"
    assert "∫" not in out and "int" in out, (
        "lo que no sabe dibujar se translitera, no se deja en blanco")


def test_sin_saber_la_cobertura_se_es_conservador():
    from nucleo.utils.pdf_export import _solo_lo_que_falte
    assert "→" not in _solo_lo_que_falte("A → B", None)
