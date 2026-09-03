# -*- coding: utf-8 -*-
r"""La sintaxis del enunciado: lo que separa hipótesis de tesis.

POR QUE ESTO TIENE GUARDIA. Lo que el sistema llamaba «sintaxis» eran n-gramas
de 1 a 4 caracteres sobre el texto sin palabras: una bolsa de fragmentos de
símbolos, que no sabe cuál es la relación principal ni qué se supone y qué se
demuestra. Medido en `scripts/sintaxis_contra_premisas.py` sobre 22 117
enunciados de Lean con las premisas que su prueba usó de verdad:

    nulo (los 6 más citados)         56,6 %  de cobertura
    n-gramas, 40 000 rasgos          76,8 %
    ESTRUCTURA, 68 rasgos            76,3 %
    las dos juntas                   80,9 %

Sesenta y ocho rasgos de estructura igualan a cuarenta mil n-gramas, y juntos
suman: no son la misma información.

Todo eso descansa en `parte_en_dos`, que corta el enunciado por el ÚLTIMO `:` a
profundidad cero. Si ese corte se rompe, los rasgos siguen calculándose y el
número sigue saliendo — sólo que sobre basura. Es justo la clase de fallo
silencioso que ya ha aparecido varias veces en este proyecto.
"""
import sys

import pytest

sys.path.insert(0, "scripts")


@pytest.fixture(scope="module")
def sx():
    from sintaxis_contra_premisas import parte_en_dos, rasgos
    return parte_en_dos, rasgos


class TestCorteHipotesisTesis:

    def test_no_corta_por_el_primer_dos_puntos(self, sx):
        """`(a b : ℝ)` ya trae un `:` dentro. Cortar por el primero da basura."""
        parte_en_dos, _ = sx
        hip, con = parte_en_dos("(a b : ℝ) : a + b = b + a")
        assert "ℝ" in hip, "el binder se fue a la conclusión"
        assert "a + b = b + a" in con

    def test_separa_las_hipotesis_de_verdad(self, sx):
        parte_en_dos, _ = sx
        hip, con = parte_en_dos(
            "(a b : ℝ) (h₁ : 0 < a ∧ 0 < b) (h₂ : a ≥ 2 * b) : a ^ 2 / b ≥ 9 * a / 4")
        assert "h₁" in hip and "h₂" in hip
        assert "h₁" not in con and "≥ 9 * a / 4" in con

    def test_sin_hipotesis_todo_es_conclusion(self, sx):
        parte_en_dos, _ = sx
        hip, con = parte_en_dos("2 + 2 = 4")
        assert not hip.strip()
        assert "2 + 2 = 4" in con


class TestRasgos:

    def test_la_relacion_principal_sale_de_la_CONCLUSION(self, sx):
        """Una hipótesis con `=` no hace que la tesis sea una igualdad.

        Es la distinción que da todo el rendimiento: `sq_nonneg` se predice con
        +2,92 cuando la relación principal es `≤`, y con −2,54 cuando es `=`.
        """
        _, rasgos = sx
        r = rasgos("(a b : ℝ) (h : a = b) : a ^ 2 ≥ 0")
        assert r.get("rel=≥") == 1, "la relación principal debería ser ≥"
        assert r.get("rel==", 0) == 0, "se leyó la igualdad de la hipótesis"
        assert r["hip_tiene_="] == 1, "la hipótesis sí trae una igualdad"

    def test_distingue_donde_esta_cada_relacion(self, sx):
        """`mul_pos` se predice por `<` EN LAS HIPÓTESIS (+2,90), no en la tesis."""
        _, rasgos = sx
        r = rasgos("(a b : ℝ) (ha : 0 < a) (hb : 0 < b) : 0 < a * b")
        assert r["hip_tiene_<"] == 1 and r["con_tiene_<"] == 1

    def test_los_tipos_se_leen_del_enunciado_entero(self, sx):
        _, rasgos = sx
        r = rasgos("(n : ℤ) : n ^ 2 ≥ 0")
        assert r["tipo_ℤ"] == 1 and r["tipo_ℝ"] == 0

    def test_la_simetria_es_de_la_conclusion(self, sx):
        _, rasgos = sx
        assert rasgos("(a b : ℝ) : a + b = b + a")["simetrica"] == 1
        assert rasgos("(a b : ℝ) : a + 2 * b + b = 0")["simetrica"] == 0

    def test_ningun_rasgo_es_constante_sobre_enunciados_distintos(self, sx):
        """Un rasgo que nunca cambia no informa, y sería un bug silencioso."""
        _, rasgos = sx
        muestras = [
            "(a b : ℝ) : a + b = b + a",
            "(a b : ℝ) (h : 0 < a) : 0 < a * b",
            "(n : ℤ) : n ^ 2 ≥ 0",
            "(x : ℝ) (h : 0 ≤ x) : Real.sqrt x ≥ 0",
            "(s : Finset ℕ) : s.card ≥ 0",
        ]
        rs = [rasgos(m) for m in muestras]
        claves = set(rs[0])
        varian = {k for k in claves if len({r.get(k) for r in rs}) > 1}
        assert len(varian) >= 15, (
            "sólo %d rasgos varían entre cinco enunciados muy distintos: el "
            "extractor está devolviendo casi lo mismo para todo" % len(varian))
