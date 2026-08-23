"""
Guardian de la auditoria de respaldo formal.

`scripts/auditar_respaldo_lean.py` mapea cada operacion categorica de Python al
teorema de Lean que la respalda. Ese mapeo puede pudrirse de dos formas:

  1. alguien renombra un teorema en Lean y el mapeo apunta al vacio;
  2. el porcentaje de respaldo baja sin que nadie se entere.

Estos tests hacen que las dos fallen ruidosamente.
"""
import pytest

from scripts.auditar_respaldo_lean import MAPEO, declaraciones_lean

#: Cota inferior. Subirla al cerrar huecos; NUNCA bajarla para que pase el test.
RESPALDO_MINIMO = 38


@pytest.fixture(scope="module")
def decls():
    return declaraciones_lean()


def test_ningun_mapeo_apunta_a_un_teorema_inexistente(decls):
    rotas = [(m, o, t) for m, o, t, _ in MAPEO if t is not None and t not in decls]
    assert not rotas, (
        "el mapeo apunta a teoremas que ya no existen en Lean: "
        + ", ".join(f"{m}::{o} -> {t}" for m, o, t in rotas)
    )


def test_el_respaldo_no_retrocede(decls):
    n = sum(1 for _, _, t, _ in MAPEO if t is not None and t in decls)
    assert n >= RESPALDO_MINIMO, (
        f"el respaldo formal bajo de {RESPALDO_MINIMO} a {n} operaciones"
    )


def test_lo_que_falta_esta_declarado():
    """
    Lo que no tiene respaldo debe estar registrado como tal, no ausente del
    mapeo. Un hueco sin anotar es indistinguible de un hueco olvidado.
    """
    sin = {o for _, o, t, _ in MAPEO if t is None}
    assert sin == {"campos_operativos_isomorfos"}, (
        f"cambio el conjunto de operaciones sin respaldo: {sorted(sin)}. "
        "Si cerraste un hueco, sube RESPALDO_MINIMO; si abriste uno, dilo aqui."
    )


def test_toda_operacion_auditada_es_unica():
    claves = [(m, o) for m, o, _, _ in MAPEO]
    assert len(claves) == len(set(claves)), "hay entradas duplicadas en el mapeo"


def test_ninguna_operacion_es_fantasma():
    """
    El MAPEO debe nombrar funciones que EXISTAN en Python. La auditoria validaba
    solo el lado de Lean, y por eso paso desapercibido que `complexify`,
    `transition_functor` y `detect_emergence` no existian: figuraban como "sin
    respaldo" mientras las reales no se auditaban.
    """
    from scripts.auditar_respaldo_lean import MAPEO, operaciones_python
    ops = operaciones_python()
    fantasma = [
        (m, o) for m, o, _, _ in MAPEO
        if ops.get(m) is not None
        and o.split(".")[0].split(" ")[0] not in ops[m]
    ]
    assert not fantasma, (
        "el mapeo nombra operaciones inexistentes: "
        + ", ".join(f"{m}::{o}" for m, o in fantasma)
    )
