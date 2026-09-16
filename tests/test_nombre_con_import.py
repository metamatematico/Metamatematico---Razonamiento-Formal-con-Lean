# -*- coding: utf-8 -*-
"""Si el grafo ofrece un nombre, el fichero que compila tiene que resolverlo.

EL FALLO QUE LO MOTIVA, reportado desde el chat
-----------------------------------------------
    demuestra que todo espacio vectorial tiene una base

    error: invalid binder annotation, type is not a class instance
      ?m.2

El grafo hizo su trabajo BIEN: emparejo `bases-and-dimension`, ofrecio
`Module.Basis` —el nombre correcto— y el modelo lo uso. Lo que fallo es que la
cabecera del fichero era Ring · Linarith · NormNum · Positivity · Order.Field ·
Data.Real, y ahi ni siquiera `Module` esta en el ambito. Comprobado con Lean:
esas seis lineas mas `[Module K V] : True := trivial` reproducen el error
palabra por palabra.

POR QUE PASABA
--------------
Estaban partidas en dos capacidades que el decisor gobierna por separado:

    nombres_de_mathlib_en_el_prompt   ENCENDIDA   22,8 % contra 1,45 %
    eleccion_de_imports               APAGADA     18 de 20 contra 18 de 20

La segunda se apago por no batir a su nulo, y esa decision es correcta DENTRO
DE SU BANCO. Lo que nadie midio es la INTERACCION. Medido despues
(`scripts/nombre_sin_import.py`): de las 284 consultas de ProofNet que reciben
algun nombre, **282 —el 99,3 %— reciben alguno cuyo modulo no se alcanza desde
la cabecera generica**. Con el arreglo, 0.

LA REGLA QUE ESTOS TESTS SOSTIENEN: ofrecer un nombre y poder importarlo es el
mismo acto. El modulo de un nombre ofrecido no es una optimizacion opcional,
es la precondicion de la capacidad que si esta encendida.
"""
import io
import os

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def nucleo_y_grafo():
    import sys
    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)
    sys.argv = ["x"]
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    return n, n._graph


#: Consultas con nombre cuyo modulo NO esta en la cabecera generica. La
#: primera es la que reporto el usuario.
CONSULTAS = [
    "prove that every vector space has a basis",
    "show that every subgroup of a cyclic group is cyclic",
    "prove that the square root of 2 is irrational",
]


@pytest.mark.parametrize("consulta", CONSULTAS)
def test_el_modulo_del_nombre_ofrecido_va_siempre(nucleo_y_grafo, consulta):
    """Todo nombre que llega al prompt trae su modulo, sin depender del decisor."""
    from nucleo.core import Nucleo
    n, g = nucleo_y_grafo
    ids = [getattr(x, "id", x)
           for x in Nucleo._match_skills_to_query(n, consulta, g)]
    noms = n._nombres_mathlib(ids, consulta, g)
    if not noms:
        pytest.skip("el grafo no ofrece nombres para esta consulta")

    ctx = {"relevant_skills": ids, "mathlib_verificado": noms}
    mods = n._modulos_de_los_nombres(ctx)
    assert mods, (
        "el grafo ofrece %s y no propone NINGUN modulo: el modelo recibe un "
        "nombre que su fichero no puede resolver" % sorted(noms))

    # y cada skill que aporto nombre tiene que estar representada
    from nucleo.rutas import dato
    import json
    mapa = json.load(io.open(dato("mathlib_modulos.json"),
                             encoding="utf-8"))["por_skill"]
    for sid in noms:
        esperados = mapa.get(sid) or []
        if not esperados:
            continue
        assert any(m in mods for m in esperados), (
            "`%s` aporta %r y ninguno de sus modulos %s entro en los imports"
            % (sid, noms[sid], esperados))


def test_no_vuelve_a_quedar_detras_del_decisor():
    """Que nadie reponga la puerta que causaba el fallo.

    La linea que hubo que quitar era exactamente esta:

        if "eleccion_de_imports" in _corre:
            self._lean.sugerir_imports(self._modulos_mathlib(context))

    Con ella, los modulos de los nombres ofrecidos solo llegaban si una
    capacidad DISTINTA —medida contra otro nulo y apagada— estaba encendida.
    """
    src = io.open(os.path.join(RAIZ, "nucleo", "core.py"),
                  encoding="utf-8").read()
    i = src.index("def _modulos_de_los_nombres")
    assert i > 0, "desaparecio `_modulos_de_los_nombres`"
    assert "self._modulos_de_los_nombres(context)" in src, (
        "nadie llama a `_modulos_de_los_nombres`: los nombres ofrecidos "
        "vuelven a salir sin su modulo")

    # Y CON `ast`, NO CON TEXTO: lo que importa no es que la cadena aparezca
    # cerca, sino que la llamada NO este dentro de un `if` que pregunte por
    # `eleccion_de_imports`. Buscarlo por ventanas de caracteres depende de
    # cuanto comentario haya alrededor, que es justo lo que cambia.
    import ast
    arbol = ast.parse(src)

    def _llama_a(nodo, nombre):
        return any(isinstance(x, ast.Attribute) and x.attr == nombre
                   for x in ast.walk(nodo))

    culpables = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.If):
            continue
        prueba = ast.dump(nodo.test)
        if "eleccion_de_imports" not in prueba:
            continue
        for hijo in nodo.body:
            if _llama_a(hijo, "_modulos_de_los_nombres"):
                culpables.append(nodo.lineno)
    assert not culpables, (
        "en %s la llamada a `_modulos_de_los_nombres` volvio a quedar dentro "
        "de un `if eleccion_de_imports`: los nombres ofrecidos solo traerian "
        "su modulo cuando otra capacidad, medida contra otro nulo y apagada, "
        "estuviera encendida" % culpables)
