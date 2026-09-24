# -*- coding: utf-8 -*-
"""Lo que destapó una consulta real: «demuestra el teorema de compacidad».

El modelo escribió `T0.IsSatisfiable` con `T0 : L.Sentence → Prop` y Lean
contestó:

    Invalid field IsSatisfiable: The environment does not contain
    Function.IsSatisfiable, so it is not possible to project the field
    IsSatisfiable from an expression ↑T0 of type L.Sentence → Prop

El sistema contestó «Lean 4 detectó un error de tipo `unknown`. Diagnóstico:
revisa la sintaxis Lean 4 y los imports de Mathlib», que no dice nada — y ese
mismo diagnóstico es el que `_revisar_con_lean` le devuelve al modelo para que
repare, así que la ronda de reparación salió a ciegas.

El índice de 217 419 nombres, preguntado, contesta en un milisegundo:
`IsSatisfiable` existe, es `FirstOrder.Language.Theory.IsSatisfiable`, vive en
`Mathlib.ModelTheory.Satisfiability`. El dato estaba y no se pasaba, que es la
misma familia de fallo que ya mordió tres veces a este repositorio.
"""

import pytest

from nucleo.core import Nucleo
from nucleo.lean.parser import classify_error

ERROR = (
    "Invalid field IsSatisfiable: The environment does not contain "
    "Function.IsSatisfiable, so it is not possible to project the field "
    "IsSatisfiable from an expression ↑T0 of type L.Sentence → Prop"
)


@pytest.fixture
def n():
    return Nucleo.__new__(Nucleo)


class TestSeClasifica:
    """Sin patrón, el tipo era `unknown` y el mensaje lo decía en crudo."""

    def test_el_campo_invalido_tiene_su_clase(self):
        assert classify_error(ERROR) == "invalid_field"

    def test_la_clase_se_dice_en_castellano(self):
        assert Nucleo._TIPO_DE_ERROR["invalid_field"] == "un campo que ese tipo no tiene"

    def test_ninguna_clase_del_parser_se_queda_sin_castellano(self):
        """Si alguien añade un patrón, que traiga su nombre legible.

        El fallo no fue no tener el patrón: fue que el mensaje al alumno
        imprimiera el identificador interno del clasificador.
        """
        from nucleo.lean.parser import _EXTENDED_ERROR_PATTERNS
        faltan = [t for _, t in _EXTENDED_ERROR_PATTERNS
                  if t not in Nucleo._TIPO_DE_ERROR]
        assert not faltan, (
            "estas clases de error no tienen nombre en castellano y saldrían "
            "en crudo en el chat: %s" % faltan)


class TestElIndiceContesta:
    """El diagnóstico ya no manda «revisar los imports»: dice el nombre."""

    def test_dice_donde_vive_el_campo_de_verdad(self, n):
        hint = Nucleo._lean_hint(n, ERROR)
        assert "FirstOrder.Language.Theory.IsSatisfiable" in hint, (
            "el índice lo sabe; el alumno y el bucle de reparación tienen "
            "que saberlo también")
        assert "Mathlib.ModelTheory.Satisfiability" in hint

    def test_explica_la_causa_y_no_solo_el_nombre(self, n):
        """`.IsSatisfiable` falla por el TIPO del término, no por el nombre."""
        hint = Nucleo._lean_hint(n, ERROR)
        assert "TIPO" in hint
        assert "L.Sentence" in hint and "Function.IsSatisfiable" in hint

    def test_no_cae_en_el_mensaje_generico(self, n):
        assert "revisa la sintaxis" not in Nucleo._lean_hint(n, ERROR)

    def test_un_campo_que_no_existe_en_ninguna_parte_no_inventa(self, n):
        hint = Nucleo._lean_hint(
            n, "invalid field 'noExisteEsteCampoJamas': the environment does "
               "not contain Foo.noExisteEsteCampoJamas")
        assert "no se puede proyectar" in hint
        assert "existe en Mathlib" not in hint, (
            "sin candidato real, el diagnóstico no puede afirmar que exista")


class TestLoQueLeeElAlumno:
    """Dos defectos de redacción que salieron en la misma pantalla."""

    def test_el_plural_de_las_rondas(self):
        """Decía «reintentó 1 vez/veces», con la barra incluida."""
        fuente = _fuente_core()
        assert "vez/veces" not in fuente, (
            "el mensaje del veredicto no puede dejar la barra del plural")
        assert '"vez" if _rondas_revision == 1 else "veces"' in fuente

    def test_el_tipo_de_error_no_sale_en_crudo(self):
        """Decía «un error de tipo `unknown`»: el nombre interno y el caso
        en que no clasificó nada, los dos a la vez."""
        fuente = _fuente_core()
        assert "error de tipo `{err_type}`" not in fuente
        assert "_TIPO_DE_ERROR.get(err_type" in fuente

    def test_la_lectura_elegida_sale_en_el_idioma_de_la_pregunta(self):
        """Ante una pregunta en español, la lectura salía en inglés.

        «ℹ️ La pregunta admitía varias lecturas. Se ha tomado ésta: The
        compactness theorem of first-order logic» — media frase en cada
        idioma, y la mitad inglesa es justo la que lleva el contenido.
        """
        fuente = _fuente_core()
        i = fuente.index("-- READING:")
        ventana = fuente[i:i + 1200]
        assert "SPANISH" in ventana and "_respuesta_en_espanol" in ventana, (
            "la instrucción de escribir la lectura en el idioma del alumno "
            "tiene que ir pegada a la que pide la línea READING")


def _fuente_core():
    from nucleo.rutas import RAIZ
    return (RAIZ / "nucleo" / "core.py").read_text(encoding="utf-8")


class TestElGrafoNoTieneLaCulpa:
    """Y lo que este caso NO es: un fallo del vocabulario que se pueda tapar.

    Para «teorema de compacidad» el grafo engancha `compactness-theorem`, que
    está marcado `T` —es un teorema, no un objeto de la categoría— y por regla
    no ofrece nombres; el segundo que engancha es `compactness`, que es la
    compacidad TOPOLÓGICA. Dar nombres a los nodos `T` ya se midió contra
    ProofNet y PIERDE (21,0 % → 20,1 % de precisión), porque sólo hay dos
    plazas en el prompt y los teoremas desplazan a los objetos.

    Este test no arregla eso: fija que la regla sigue en pie, para que nadie
    la cambie sin volver a medir.
    """

    def test_los_nodos_teorema_no_ofrecen_nombres(self):
        from nucleo.graph.interpretacion import nombres_de_trabajo
        assert nombres_de_trabajo("compactness-theorem") == ""

    def test_y_el_nombre_bueno_esta_escrito_en_su_nota(self):
        """Quien cure ese nodo algún día no tiene que buscarlo otra vez."""
        from nucleo.graph.interpretacion import VEREDICTO
        nota = (VEREDICTO["compactness-theorem"].nota or "")
        assert "isSatisfiable_iff_isFinitelySatisfiable" in nota
