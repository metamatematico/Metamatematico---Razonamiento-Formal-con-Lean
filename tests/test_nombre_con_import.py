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


# ─────────────────────────────────────────────────────────────────────────
# Y NO BASTA CON QUE EL NOMBRE EXISTA E IMPORTE: hay que decir QUE ES.
# ─────────────────────────────────────────────────────────────────────────
#
# Segundo fallo reportado desde el chat, con los imports ya arreglados:
#
#     ∃ (i : Type _) (b : i → V), Module.Basis i K V
#     -> Type mismatch: `Module.Basis i K V` has type Type ...
#        but is expected to have type Prop
#
# El nombre era correcto, existia y se importaba. Lo que el modelo no sabia
# es que `Module.Basis` es un `structure` —un tipo de DATOS— y lo puso donde
# Lean espera una proposicion. «Existe una base» se escribe
# `Nonempty (Module.Basis i K V)`.

def test_ningun_nombre_ofrecido_es_un_teorema():
    """El grafo aporta SUSTANTIVOS, y por eso hay que decir que lo son.

    Es la razon de la linea de guia del prompt: si alguno de los nombres
    ofrecidos fuese un teorema, decir «esto es data, no una proposicion»
    seria falso para el. Hoy no lo es para ninguno.
    """
    import json
    from nucleo.rutas import dato
    clases = json.load(io.open(dato("mathlib_modulos.json"),
                               encoding="utf-8")).get("clase_por_nombre") or {}
    assert clases, "el mapa no trae `clase_por_nombre`: regenerarlo con " \
                   "python -m scripts.mapa_modulos_mathlib"
    proposiciones = {n: c for n, c in clases.items()
                     if c in ("theorem", "lemma", "instance")}
    assert not proposiciones, (
        "estos nombres ofrecidos son proposiciones, asi que la guia del "
        "prompt («esto es data, no una proposicion») dejo de ser cierta "
        "para ellos: %s" % proposiciones)


def test_el_prompt_dice_de_que_clase_es_cada_nombre(nucleo_y_grafo):
    """Sin la clase, el modelo no puede saber donde cabe el nombre."""
    n, _g = nucleo_y_grafo
    anotado = n._con_su_clase("Module.Basis, LinearIndependent")
    assert "(structure)" in anotado, (
        "`Module.Basis` es un structure y el prompt no lo dice: %s" % anotado)
    assert "(def)" in anotado, anotado

    # un nombre desconocido se deja tal cual: callarse antes que inventar
    assert n._con_su_clase("NoExisteEsteNombre") == "NoExisteEsteNombre"


def test_la_guia_de_data_vs_proposicion_sigue_en_el_prompt():
    """Que nadie la quite por ahorrar dos lineas de prompt."""
    src = io.open(os.path.join(RAIZ, "nucleo", "core.py"),
                  encoding="utf-8").read()
    assert "is DATA, not a" in src and "Nonempty (X ...)" in src, (
        "desaparecio del prompt la guia que distingue un tipo de datos de una "
        "proposicion — es la que evita `exists ..., Module.Basis i K V`")


# ─────────────────────────────────────────────────────────────────────────
# TERCERA CAPA: el modelo no sabia QUE FORMA tiene el lema que usa.
# ─────────────────────────────────────────────────────────────────────────
#
# Con los imports puestos y la clase dicha, el modelo escribio:
#
#     ∃ (i : Type _), Nonempty (Module.Basis i K V) := by
#       obtain ⟨s, hs⟩ := Module.Basis.exists_basis K V
#       exact ⟨s, ⟨hs⟩⟩
#
# y fallo DOS rondas de revision con el error delante. Los dos defectos salen
# de lo mismo: el enunciado real es
#
#     Module.Basis.exists_basis : ∃ s : Set V, Nonempty (Basis s K V)
#
# o sea que el indice es un `Set V` —no un `Type _`, de ahi el choque de
# universos— y `hs` YA es un `Nonempty`, de ahi el doble envoltorio.
# Verificado con Lean: cambiando esas dos cosas, la prueba pasa.

def test_el_indice_sabe_el_enunciado_de_lo_que_ofrece():
    """El dato que faltaba en la revision estaba en el repositorio."""
    from nucleo.lean import nombres as N
    d = N.enunciados_de({"Module.Basis.exists_basis"})
    assert "Module.Basis.exists_basis" in d, (
        "el indice ya no sabe el enunciado de `exists_basis`: la revision "
        "vuelve a pedirle al modelo que adivine la forma del lema")
    assert "Set V" in d["Module.Basis.exists_basis"], d


def test_la_revision_enseña_las_firmas_reales():
    """Que nadie quite el bloque: es lo que convierte «te equivocaste» en
    «esto es lo que hay»."""
    src = io.open(os.path.join(RAIZ, "nucleo", "core.py"),
                  encoding="utf-8").read()
    assert "bloque_firmas" in src, (
        "desaparecio de la revision el bloque de firmas reales")
    assert "enunciados_de(candidatos)" in src, (
        "la revision ya no busca los enunciados de los nombres del codigo")
    i = src.index("revise_prompt = (")
    j = src.index("Fix it. Instructions:", i)
    assert "bloque_firmas" in src[i:j], (
        "`bloque_firmas` se calcula y NO entra en el prompt de revision — "
        "que es exactamente el fallo que este fichero persigue: tener el "
        "dato y no pasarlo")
