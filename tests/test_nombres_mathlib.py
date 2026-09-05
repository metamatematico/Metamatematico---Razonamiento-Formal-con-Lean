# -*- coding: utf-8 -*-
"""Guardián de las afirmaciones sobre nombres de Mathlib.

DE DONDE SALE. Ante «todo espacio vectorial tiene una base», el sistema
respondió:

    «El error es claro: la constante `Module.Basis.exists_basis` no existe en
     Mathlib con ese nombre — es una invención o un nombre desactualizado.»

Y es falso. `#check` sobre el Mathlib instalado devuelve la firma del lema, y
el error real de Lean era otro:

    Application type mismatch: the argument `s` has type `Set V` … expected
    `Type u_3`  in the application  Exists.intro s

El lema existe; lo que no encajaba era el enunciado que se intentó probar con
él. El traductor inventó el diagnóstico y lo presentó como «el error es
claro», mandando a quien lo leyera a buscar el nombre correcto de un lema que
ya lo tenía.

En un sistema cuya tesis es que la verdad la produce Lean y el modelo es sólo
la boca, eso rompe la tesis en el único punto donde el usuario la comprueba.
"""
from __future__ import annotations

import pathlib

import pytest

from nucleo.lean import nombres as N

RAIZ = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module", autouse=True)
def _hay_banco():
    if not N.disponible():
        pytest.skip("falta data/lemas_mathlib.jsonl")


class TestExistencia:

    def test_conoce_los_lemas_no_solo_los_sustantivos(self):
        """`sustantivos.existe` sólo cubre tipos y clases —34 084— y para un
        LEMA diría que no. Ése es justo el error que se persigue, así que este
        módulo tiene que ir sobre los 183 351."""
        assert N.cuantos() > 150000
        assert N.existe("Module.Basis.exists_basis")
        from nucleo.lean import sustantivos
        assert not sustantivos.existe("Module.Basis.exists_basis"), (
            "si sustantivos empieza a conocer lemas, este test sobra — pero "
            "hay que enterarse, no descubrirlo por casualidad")

    def test_el_sufijo_cuenta_como_existente(self):
        """Con `open Module` delante, `Basis.exists_basis` resuelve."""
        assert N.existe("Basis.exists_basis")
        assert N.nombre_completo("Basis.exists_basis") == "Module.Basis.exists_basis"

    def test_lo_que_no_esta_no_esta(self):
        assert not N.existe("Foo.bar_completamente_inventado")
        assert N.nombre_completo("Foo.bar_completamente_inventado") == ""

    def test_para_lo_que_falta_hay_candidatos(self):
        assert N.parecidos("Module.Basis.exists_basis", 3)


class TestAfirmaciones:

    #: La nota literal que produjo el sistema.
    NOTA = (
        "Nota sobre la verificación\n"
        "Lean 4 no verificó este código. El error es claro: la constante "
        "Module.Basis.exists_basis no existe en Mathlib con ese nombre — es "
        "una invención o un nombre desactualizado. El fallo no es matemático "
        "(el teorema es verdadero y está en Mathlib), sino de referencia: se "
        "necesita localizar el lema correcto (algo como Basis.exists_basis en "
        "el namespace adecuado, posiblemente derivado de exists_isBasis o "
        "construido vía Module.Free / Basis.ofVectorSpace)."
    )

    def test_caza_la_afirmacion_falsa_que_lo_motivo(self):
        f = N.revisar_afirmaciones(self.NOTA)
        assert [x["nombre"] for x in f] == ["Module.Basis.exists_basis"]
        assert "no existe" in N.aviso_de_correccion(f)

    def test_no_desmiente_lo_que_es_cierto(self):
        """Si el nombre de verdad no está, quien lo negaba tenía razón y
        corregirlo sería cambiar un error por otro."""
        assert N.revisar_afirmaciones(
            "El lema Foo.bar_inventado no existe en Mathlib.") == []

    def test_el_sufijo_no_basta_para_desmentir(self):
        """`Basis.exists_basis` a pelo devuelve «Unknown identifier»: sólo
        resuelve con `open Module`. Marcar esa negación como falsa sería
        pasarse de listo."""
        f = N.revisar_afirmaciones("`Basis.exists_basis` no existe en Mathlib.")
        assert f == []

    def test_una_mencion_sin_negacion_no_se_toca(self):
        assert N.revisar_afirmaciones(
            "Usamos Module.Basis.exists_basis para cerrar la prueba.") == []

    def test_el_punto_del_identificador_no_parte_la_frase(self):
        """LA TRAMPA QUE TUVO LA PRIMERA VERSIÓN.

        Partía el texto en frases por `.`, y los identificadores de Lean
        LLEVAN PUNTOS: `Module.Basis.exists_basis` quedaba troceado y el
        fragmento con «no existe» se quedaba sin identificador que comprobar.
        Detectaba cero afirmaciones falsas sobre el texto que la motivó.
        """
        assert N.revisar_afirmaciones(self.NOTA), (
            "vuelve a partir por puntos: el identificador se trocea")

    def test_texto_vacio_o_sin_nombres(self):
        for t in ("", "   ", "No existe ninguna prueba de eso.",
                  "no existe", "Mathlib"):
            assert N.revisar_afirmaciones(t) == []


def test_core_antepone_la_correccion():
    """Sin el cableado el módulo sería un informe que nadie lee."""
    fuente = (RAIZ / "nucleo" / "core.py").read_text(encoding="utf-8")
    assert "from nucleo.lean import nombres" in fuente
    assert "revisar_afirmaciones(content)" in fuente
    linea = next((l for l in fuente.splitlines()
                  if "aviso_de_correccion(_correcciones)" in l), "")
    assert linea, "no se ensambla el aviso"
    assert '"nombres_desmentidos"' in fuente, (
        "hay que dejar rastro en los metadatos: que deje de estar vacio es la "
        "senal de que el traductor inventa diagnosticos")


class TestLosDosIndices:
    """Los dos ficheros son complementarios y ninguno basta solo."""

    def test_lemas_y_sustantivos_se_necesitan(self):
        """Medido:

            Module.Basis                lemas=NO   sustantivos=SI  (estructura)
            Module.Basis.exists_basis   lemas=SI   sustantivos=NO  (teorema)

        La primera version de `nombres.py` leia solo los lemas, asi que habria
        dicho que `Module.Basis` no existe — exactamente el error que este
        modulo existe para cazar.
        """
        assert N.existe("Module.Basis"), "falta el indice de sustantivos"
        assert N.existe("Module.Basis.exists_basis"), "falta el de lemas"
        assert N.cuantos() > 200000, "no se estan uniendo los dos ficheros"

    def test_el_nombre_corto_no_desmiente(self):
        """`Basis` a pelo da «unknown identifier» en Lean, aunque exista
        `QuaternionAlgebra.Basis`. Quien diga que no existe tiene razon, y
        corregirle seria mentir.

        `sustantivos.existe` SI acepta el corto —legitimo para su uso, que es
        la puerta previa a Lean bajo un `open`— y por eso aqui no se reutiliza
        esa funcion sino que se leen los nombres cualificados.
        """
        assert N.revisar_afirmaciones("El identificador Basis no existe.") == []
        f = N.revisar_afirmaciones("La estructura Module.Basis no existe.")
        assert [x["nombre"] for x in f] == ["Module.Basis"]
