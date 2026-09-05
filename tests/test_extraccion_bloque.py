# -*- coding: utf-8 -*-
"""Guardián de la extracción del bloque de código Lean.

DE DÓNDE SALE. Lean respondió «unexpected token; expected command» sobre una
línea suelta que contenía un `4`, justo detrás de la cabecera. No era culpa del
modelo: era del extractor.

    start = text.find("```lean") + 7

7 son exactamente las letras de «```lean». Con la etiqueta más habitual

    ```lean4

el corte caía DETRÁS de `lean` y el `4` entraba en el código como una línea
suelta. Y el prompt dice «write ONE Lean 4 code block», con lo que `lean4` es
la etiqueta más probable de todas.

CON `Lean4` ERA PEOR: la `L` mayúscula no casaba con `"```lean"`, la función
caía a `return text` y mandaba LA PROSA ENTERA al verificador.
"""
from __future__ import annotations

import pytest

from nucleo.core import Nucleo

CODIGO = "import Mathlib\ntheorem t : 1 = 1 := rfl"


@pytest.fixture
def nucleo():
    return Nucleo.__new__(Nucleo)


@pytest.mark.parametrize("etiqueta", [
    "lean", "lean4", "Lean4", "LEAN", "lean 4", "Lean 4", "lean-4", "",
])
def test_la_etiqueta_se_consume_entera(nucleo, etiqueta):
    """Sea cual sea la etiqueta, el código que sale es el código."""
    texto = ("Explicación previa.\n"
             "```%s\n%s\n```\n"
             "Y algo después." % (etiqueta, CODIGO))
    assert Nucleo._extract_lean_code(nucleo, texto) == CODIGO


def test_el_cuatro_no_se_cuela(nucleo):
    """El caso literal que lo destapó."""
    salida = Nucleo._extract_lean_code(
        nucleo, "```lean4\n%s\n```" % CODIGO)
    assert not salida.startswith("4"), "el 4 de la etiqueta entra en el codigo"
    assert "\n4\n" not in salida


def test_una_L_mayuscula_no_manda_la_prosa_al_verificador(nucleo):
    """El fallo más caro de los dos: sin bloque reconocido, la función
    devolvía el texto entero y eso acababa en Lean."""
    texto = ("Voy a demostrarlo. El teorema es cierto porque toda sucesión "
             "de Cauchy converge.\n```Lean4\n%s\n```" % CODIGO)
    salida = Nucleo._extract_lean_code(nucleo, texto)
    assert salida == CODIGO
    assert "Cauchy converge" not in salida


def test_bloque_sin_cerrar(nucleo):
    """Una respuesta truncada no puede perder el código."""
    assert Nucleo._extract_lean_code(
        nucleo, "```lean4\n%s" % CODIGO) == CODIGO


def test_se_prefiere_el_bloque_de_lean(nucleo):
    """Si hay varios, manda el etiquetado como Lean."""
    texto = ("```python\nprint('hola')\n```\n"
             "```lean4\n%s\n```" % CODIGO)
    assert Nucleo._extract_lean_code(nucleo, texto) == CODIGO


def test_sin_ningun_bloque_se_devuelve_el_texto(nucleo):
    """Es la rama peligrosa —manda prosa al verificador— así que va la última,
    no la primera. Se conserva porque hay modelos que responden sin vallas."""
    assert Nucleo._extract_lean_code(nucleo, "  solo prosa  ") == "solo prosa"


def test_texto_vacio(nucleo):
    assert Nucleo._extract_lean_code(nucleo, "") == ""
    assert Nucleo._extract_lean_code(nucleo, None) == ""
