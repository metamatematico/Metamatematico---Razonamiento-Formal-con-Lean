# -*- coding: utf-8 -*-
"""El contexto que un teorema de Mathlib tiene activo en su fichero.

Lo usan los bancos que sacan teoremas de Mathlib para cerrarlos con la cascada
(`scripts/cascada_contra_lean.py`, `scripts/cascada_por_estado.py`). Si el
contexto está mal, el enunciado deja de ser el de Mathlib y el banco mide
otra cosa: con la versión anterior, NINGUNO de 25 casos cerraba en ninguna
rama, y el resultado parecía una medición.
"""
from scripts.cascada_contra_lean import contexto_vigente


def test_una_seccion_cerrada_no_deja_sus_variables():
    """El caso de `mul_neg_one`: instancias de secciones ya cerradas."""
    ls = ["section A", "variable [Add α]", "end A",
          "section B", "variable [Mul α]"]
    assert contexto_vigente(ls) == ["section B", "variable [Mul α]"]


def test_el_namespace_se_conserva():
    ls = ["namespace Int", "open Nat", "theorem x : True := trivial"]
    assert contexto_vigente(ls) == ["namespace Int", "open Nat"]


def test_ambitos_anidados_y_globales():
    ls = ["universe u", "namespace N", "section S", "variable (a : Nat)",
          "end S", "variable (b : Nat)"]
    assert contexto_vigente(ls) == ["universe u", "namespace N", "variable (b : Nat)"]


def test_una_variable_de_varias_lineas_va_entera():
    ls = ["section", "variable {α : Type*}", "    [Ring α] [Nontrivial α]"]
    assert contexto_vigente(ls) == ["section",
                                    "variable {α : Type*} [Ring α] [Nontrivial α]"]


def test_lo_sangrado_no_abre_ni_cierra_ambito():
    """Un `end` o un `section` dentro de una prueba no es del fichero."""
    ls = ["section S", "theorem t : True := by", "  trivial",
          "  end", "variable (x : Nat)"]
    assert contexto_vigente(ls) == ["section S", "variable (x : Nat)"]


def test_un_end_de_mas_no_revienta():
    assert contexto_vigente(["end", "open Real"]) == ["open Real"]
