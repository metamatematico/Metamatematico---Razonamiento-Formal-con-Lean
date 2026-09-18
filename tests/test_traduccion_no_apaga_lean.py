# -*- coding: utf-8 -*-
"""La puerta a Lean se pregunta sobre lo que escribio el alumno.

EL FALLO, encontrado corriendo la bateria de humo
--------------------------------------------------
    «Demuestra que la raiz cuadrada de 2 es irracional»

El traductor —`Helsinki-NLP/opus-mt-es-en`— la convierte en

    «It shows that the square root of 2 is irrational.»

El IMPERATIVO «demuestra» se vuelve DECLARATIVO «it shows that», y sobre esa
frase `_is_mathematical` contesta False. Como la puerta a `_math_via_lean` se
evaluaba sobre la TRADUCCION, la consulta canonica del proyecto —la
irracionalidad de raiz de 2— nunca llegaba a Lean: devolvia prosa plausible
sin verificar, que es exactamente lo que este sistema existe para no hacer.

POR QUE NO LO VIO NADIE. Las dos piezas estaban bien por separado: el
traductor traduce y el clasificador clasifica. Los 1124 tests las comprueban
una a una y ninguno las pone en fila. Lo que estaba mal era el ORDEN — se le
preguntaba al clasificador sobre un texto que el alumno no escribio.

Medido con `scripts/traduccion_apaga_lean.py`: 2 de 12 consultas en español
cambiaban de veredicto al traducirse, y las 2 son la misma — la insignia del
proyecto.
"""
import sys

import pytest


@pytest.fixture(scope="module")
def n():
    sys.argv = ["x"]
    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)
    from nucleo.core import Nucleo
    return Nucleo.__new__(Nucleo)


#: (lo que escribe el alumno, lo que sale del traductor)
#:
#: La traduccion va escrita a mano y no se calcula: cargar el traductor son
#: 258 pesos y ~2 s, y lo que este test comprueba no es el traductor sino la
#: PUERTA. Si algun dia el traductor mejora y ya no rompe el imperativo, este
#: test sigue valiendo: comprueba que la puerta no depende de que lo haga bien.
CASOS = [
    ("Demuestra que la raiz cuadrada de 2 es irracional",
     "It shows that the square root of 2 is irrational."),
    ("Demuestra que la raíz cuadrada de 2 es irracional",
     "It shows that the square root of 2 is irrational."),
]


@pytest.mark.parametrize("original,traducida", CASOS)
def test_la_traduccion_no_puede_apagar_lean(n, original, traducida):
    from nucleo.core import Nucleo

    # la premisa del test: el traductor SI rompe estas
    assert Nucleo._is_mathematical(n, original), (
        "el clasificador ya no reconoce el original: el caso perdio sentido")

    n._consulta_original = original
    assert Nucleo._es_consulta_matematica(n, traducida), (
        "la puerta a Lean contesta NO sobre la traduccion de una consulta "
        "matematica. Es el fallo que apagaba la irracionalidad de raiz de 2: "
        "el alumno recibe prosa sin verificar y sin saberlo")


def test_sin_original_se_comporta_como_antes(n):
    """Sin traduccion —consulta en ingles— la puerta es la de siempre."""
    from nucleo.core import Nucleo
    n._consulta_original = None
    assert Nucleo._es_consulta_matematica(
        n, "Prove that the square root of 2 is irrational")
    assert not Nucleo._es_consulta_matematica(n, "hello, who are you")


def test_un_saludo_sigue_sin_formalizarse(n):
    """El arreglo no puede volverse una puerta abierta.

    Se pregunta por las dos formas, asi que hay que comprobar que NINGUNA
    abre: un saludo traducido sigue siendo un saludo, y formalizarlo gasta una
    llamada al modelo y una compilacion de Lean para devolver un sinsentido.
    """
    from nucleo.core import Nucleo
    n._consulta_original = "Hola, quien eres y para que sirves"
    assert not Nucleo._es_consulta_matematica(
        n, "Hello, who are you and what are you for")


def test_las_puertas_del_pipeline_usan_la_version_bilingue():
    """Que nadie vuelva a poner `_is_mathematical` en el camino.

    El metodo original se queda —lo usan los tests y mide UNA cadena— pero las
    puertas del pipeline tienen que preguntar por las dos.
    """
    import ast
    import io
    import os
    ruta = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "nucleo", "core.py")
    arbol = ast.parse(io.open(ruta, encoding="utf-8").read())

    PUERTAS = {"_execute_action", "_assist_lean",
               "_demo_educational_response"}

    culpables = []
    vistas = set()
    for f in ast.walk(arbol):
        if not isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if f.name not in PUERTAS:
            continue
        vistas.add(f.name)
        for x in ast.walk(f):
            if (isinstance(x, ast.Call)
                    and isinstance(x.func, ast.Attribute)
                    and x.func.attr == "_is_mathematical"):
                culpables.append((f.name, x.lineno))
    assert not culpables, (
        "estas puertas del pipeline preguntan por la traduccion y no por lo "
        "que escribio el alumno: %s. Usar `_es_consulta_matematica`."
        % culpables)

    # UN TEST QUE BUSCA POR NOMBRE ES VACUO EN CUANTO EL NOMBRE CAMBIA: si
    # alguien renombra `_assist_lean`, el bucle de arriba no la visita, no
    # encuentra culpables y este fichero se pone verde sin haber mirado nada.
    # Ya paso una vez en este repo, con un global mutable que dejaba sin
    # contenido su propia comprobacion.
    assert vistas == PUERTAS, (
        "no se encontraron estas puertas en core.py: %s. O se renombraron —y "
        "hay que actualizar la lista— o desaparecieron, y entonces la "
        "comprobacion llevaba tiempo sin mirar nada." % sorted(PUERTAS - vistas))
