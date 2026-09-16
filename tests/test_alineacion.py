# -*- coding: utf-8 -*-
"""Guardia de alineacion: que las piezas digan lo MISMO entre si.

POR QUE ESTE FICHERO EXISTE APARTE DE LOS OTROS 1094 TESTS
----------------------------------------------------------
Los demas comprueban que cada pieza cumple SU contrato, y eso no basta.
`FUSIONES` declaraba OCHO fusiones y no se habia aplicado NINGUNA: las ocho
seguian siendo nodo vivo. Ningun test fallaba, y con razon — la tabla
declaraba bien y el grafo cargaba bien. Lo que nadie preguntaba era si una
cosa correspondia con la otra.

Esa clase de fallo no rompe nada al ejecutar. Se manifiesta mas tarde, cuando
alguien lee una cifra de un `data/*.json` que se quedo en un grafo anterior, o
cuando un documento publicado nombra nodos que ya no existen. Aparecio con el
veredicto sobre las 48: al aplicarlo quedaron cinco desalineaciones de ese
tipo, y ninguna suite las vio.

LO QUE NO HACE, y es deliberado: no exige que todo id retirado desaparezca.
El veredicto es un dato editorial y `interpretacion.py` conserva las filas
retiradas a proposito. Lo que exige es que no se CONSULTEN. Ver
`scripts/alineacion.py`, que distingue historia de referencia viva parseando
con `ast` en vez de con grep.
"""
import sys

import pytest

from scripts.alineacion import (
    RETIRADAS_GLOBALES, ids_retirados_vivos, datos_derivados_al_dia,
    publicados_con_ids_muertos, declarado_sin_aplicar,
    veredicto_contra_grafo, ramas_mudas, _grafo,
)


@pytest.fixture(scope="module")
def g():
    sys.argv = ["x"]
    return _grafo()


def test_ningun_id_retirado_se_consulta_desde_codigo_vivo():
    """Un id retirado en prosa es historia; en un `dict` que alguien mira, no.

    `scripts/verificar_teoria_faltante.py` tenia
    `"cardinal-arithmetic": ["Cardinal"]` despues de que ese nodo se
    renombrara. La propuesta era buena —el veredicto la adopto— pero la
    entrada apuntaba a un nodo que ya no existe, asi que no se habria
    verificado nunca mas y nadie se habria enterado.
    """
    fallos, _avisos = ids_retirados_vivos(RETIRADAS_GLOBALES())
    assert not fallos, "ids retirados consultados desde codigo vivo: %s" % (
        ["%s:%d %s" % f for f in fallos],)


def test_los_datos_derivados_no_citan_nodos_muertos(g):
    """Un `data/*.json` que nombra un nodo retirado describe otro grafo.

    Y cualquier cifra que salga de el —o cualquier documento que la cite—
    esta describiendo ese otro grafo sin decirlo.
    """
    fallos = datos_derivados_al_dia(g)
    assert not fallos, "datos derivados sin regenerar: %s" % (fallos,)


def test_lo_publicado_no_nombra_nodos_muertos(g):
    """Las actas quedan fuera: describen una fecha, no el estado de hoy."""
    fallos, _avisos = publicados_con_ids_muertos(g)
    assert not fallos, "documentos publicados con nodos muertos: %s" % (fallos,)


def test_lo_declarado_o_se_aplica_o_dice_por_que_no(g):
    """La guardia que habria cazado las ocho fusiones sin aplicar.

    No exige aplicarlas: exige que se sepa cual es cual. Una declaracion que
    documenta una equivalencia es legitima; una que nadie recuerda si se hizo
    es deuda silenciosa.
    """
    fallos = declarado_sin_aplicar(g)
    assert not fallos, "declarado y sin aplicar, sin motivo escrito: %s" % (
        fallos,)


def test_el_veredicto_y_el_grafo_se_nombran_igual(g):
    fallos = veredicto_contra_grafo(g)
    assert not fallos, "la tabla y el grafo no se corresponden: %s" % (fallos,)


def test_ninguna_rama_toma_nombre():
    """La regla del rol, otra vez y desde fuera.

    Ya esta en `test_interpretacion.py`; se repite aqui a proposito porque es
    la unica de las seis que puede romperse editando un fichero DISTINTO del
    que la declara — basta con darle un `lean=` a una rama.
    """
    fallos = ramas_mudas()
    assert not fallos, "ramas que ofrecen nombre: %s" % (fallos,)


def test_cada_medicion_sabe_sobre_que_grafo_se_hizo():
    """Una cifra sin su grafo no se puede citar como actual.

    `banco_herald.json` decia «10,3 % de precision» y la documentacion lo
    citaba como la cifra de hoy. Se midio sobre un grafo de 352 nodos que
    todavia tenia `sequent-calculus`, `recursion-theory` y
    `cardinal-arithmetic`.

    Ni el fichero ni la documentacion mentian por separado: el fichero decia
    lo que midio y la documentacion lo copiaba bien. Faltaba la pregunta «¿y
    esto sobre que grafo?», que nadie podia hacerse porque el dato no estaba
    escrito en ningun sitio. Es la disciplina del modelo nulo una vuelta mas
    arriba: cada cifra con SU GRAFO.
    """
    from scripts.alineacion import mediciones_del_grafo_de_hoy
    fallos = mediciones_del_grafo_de_hoy()
    assert not fallos, (
        "mediciones que no describen el grafo de hoy: %s. Volver a correr su "
        "banco antes de citar sus cifras." % (fallos,))
