# -*- coding: utf-8 -*-
"""Dos agujeros encontrados auditando el camino del veredicto.

Los dos son de la misma familia que los de esta semana: nadie daba error, y el
resultado salía con más autoridad de la que tenía.

1 · EL SELLO SOBRE UN ENUNCIADO VACÍO. `theorem t : True := trivial` compila
    con exit 0 y sin una sola línea de salida. `_prueba_algo` lo daba por
    bueno —tiene `theorem` y tiene cuerpo— y la respuesta salía con «Lean 4 ✓
    prueba verificada formalmente» sobre algo que no dice nada. Comprobado
    ejecutándolo, no razonándolo.

2 · EL TRIAJE POR SUBCADENA. `core.py` decidía si un error era mecánico
    buscando «unknown identifier» en el texto. Lean escribe ESE MISMO fallo de
    dos maneras:

        «Unknown identifier `Basis.exists_basis`»              (coincide)
        «The identifier `Basis` is unknown, y autoImplicit…»    (NO coincide)

    La segunda es la que aparece cuando `autoImplicit` convierte el nombre
    desconocido en una variable implícita — el caso real que se coló. Lean
    emite además un campo `kind` estructurado que llegaba entero en
    `messages` y no miraba nadie.
"""
from __future__ import annotations

import pathlib

import pytest

from nucleo.core import Nucleo, enunciado_vacuo
from nucleo.lean.client import LeanResult, LeanResultStatus

RAIZ = pathlib.Path(__file__).resolve().parent.parent


class TestEnunciadoVacuo:

    @pytest.mark.parametrize("code", [
        "import Mathlib\ntheorem t : True := trivial",
        "import Mathlib\ntheorem t (h : 2+2=5) : True := trivial",
        "import Mathlib\nlemma l : True := by trivial",
        "example : True := trivial",
        "theorem t : (True) := trivial",
    ])
    def test_caza_lo_que_no_dice_nada(self, code):
        assert enunciado_vacuo(code), code

    @pytest.mark.parametrize("code", [
        # LO QUE NO SE PUEDE ROMPER: `True` de relleno en el cuerpo de un ∃ es
        # legítimo — lo que se afirma es la existencia, no el True.
        "theorem t : ∃ (n : Nat), True := ⟨0, trivial⟩",
        "theorem t (K : Type*) : ∃ (i : Type _) (b : Module.Basis i K K), True := by sorry",
        "theorem t : 2 + 2 = 4 := by norm_num",
        "theorem t (h : p) : p := h",
        "import Mathlib\n#check @Nat.succ",
        "",
    ])
    def test_no_toca_lo_legitimo(self, code):
        assert not enunciado_vacuo(code), code

    def test_los_comentarios_no_cuentan(self):
        assert not enunciado_vacuo("-- theorem t : True := trivial\ntheorem u : 1=1 := rfl")
        assert not enunciado_vacuo("/- theorem t : True := trivial -/\ntheorem u : 1=1 := rfl")

    def test_la_regla_es_estrecha_y_se_dice(self):
        """No cubre `True ∧ True` ni `P → True`. Está escrito en el docstring
        para que nadie lo lea como garantía de no-vacuidad."""
        doc = enunciado_vacuo.__doc__ or ""
        assert "LO QUE NO CUBRE" in doc


class TestTriajeDeErrores:

    def _res(self, kind, data):
        return LeanResult(status=LeanResultStatus.ERROR,
                          messages=[{"severity": "error", "kind": kind,
                                     "data": data}])

    def test_error_kinds_expone_el_campo_de_lean(self):
        r = self._res("lean.unknownIdentifier._namedError", "Unknown identifier `X`")
        assert r.error_kinds == ["lean.unknownIdentifier._namedError"]

    def test_caza_la_redaccion_que_la_subcadena_perdia(self):
        """La forma de `autoImplicit`: el texto no lleva «unknown identifier»
        pero el `kind` sí lo dice."""
        n = Nucleo.__new__(Nucleo)
        r = self._res(
            "lean.unknownIdentifier._namedError",
            "Function expected at Basis. Hint: The identifier `Basis` is "
            "unknown, and Lean's autoImplicit option causes...")
        # la regla vieja, por subcadena, falla
        assert not any(m in (r.get_first_error() or "").lower()
                       for m in Nucleo._ERRORES_MECANICOS)
        # la nueva, por kind, acierta
        assert Nucleo._es_error_mecanico(n, r)

    def test_sigue_valiendo_la_subcadena_cuando_no_hay_kind(self):
        n = Nucleo.__new__(Nucleo)
        r = self._res("", "Unknown constant `Foo.bar`")
        assert Nucleo._es_error_mecanico(n, r)

    def test_un_error_semantico_no_es_mecanico(self):
        """Si se marcara como mecánico, el sistema NO haría la ronda de
        revisión con el LLM y se quedaría sin arreglarlo."""
        n = Nucleo.__new__(Nucleo)
        r = self._res("", "Application type mismatch: the argument s has type Set V")
        assert not Nucleo._es_error_mecanico(n, r)


def test_el_vacuo_se_comprueba_antes_que_sin_teorema():
    """Un enunciado vacuo SÍ tiene teorema: lo que no tiene es contenido. Si
    `sin_teorema` fuera primero, nunca se llegaría a la rama del vacuo."""
    fuente = (RAIZ / "nucleo" / "core.py").read_text(encoding="utf-8")
    i_vacuo = fuente.index("enunciado_vacuo(lean_code)")
    i_sin = fuente.index("not _prueba_algo(lean_code)")
    assert i_vacuo < i_sin
    assert '"vacuo"' in fuente
