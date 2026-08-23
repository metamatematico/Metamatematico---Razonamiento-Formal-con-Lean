"""
El Principio de Multiplicidad, medido segun Ehresmann.

HALLAZGO
--------
`patterns.py::verify_multiplicity_principle` reporta `satisfies: True` sobre el
grafo real. Formalmente NO se cumple.

La causa es la definicion de homologia. Ehresmann: dos patrones son homologos
si tienen el MISMO COLIMITE —son dos descomposiciones del mismo objeto—. El
codigo usa una heuristica estructural: mismo numero de componentes, topologia
de enlaces parecida, pilares distintos. Su docstring lo dice ("Si no tienen
colimites, usa heuristica estructural").

Medido sobre los 18 colimites descubiertos:

    pares que el codigo llama homologos      1683
    ...de los cuales ambos tienen colimite     29
    ...y comparten el MISMO colimite            0

POR QUE IMPORTA
---------------
`multiplicidad_necesaria_para_complejidad` (EhresmannLinks.lean) demuestra que
sin Principio de Multiplicidad TODO compuesto de enlaces simples es simple. Es
decir: mientras cada colimite tenga una sola descomposicion, el sistema no
puede producir enlaces complejos. No hay emergencia en el sentido de Ehresmann.

Estos tests fijan el hecho medido. No arreglan el codigo: eso exige decidir si
`are_homologous` debe pasar a la definicion de Ehresmann, lo que cambiaria el
significado de verify_multiplicity_principle.
"""
import sys
from collections import defaultdict

import pytest


@pytest.fixture(scope="module")
def sistema():
    sys.argv = ["x"]
    from scripts.train_gnn_ppo import build_skill_graph
    from nucleo.mes.patterns import PatternManager, ColimitBuilder
    from nucleo.graph.complexity import build_hierarchy_to_fixpoint

    g = build_skill_graph()
    pm = PatternManager()
    cb = ColimitBuilder(pm)
    build_hierarchy_to_fixpoint(g, pm, cb)
    return g, pm, cb


def _descomposiciones(cb, pm):
    """objeto -> conjunto de descomposiciones (patrones con ese colimite)."""
    out = defaultdict(set)
    for c in cb.all_colimits:
        pat = pm.get_pattern(c.pattern_id) if c.pattern_id else None
        if pat and c.skill_id:
            out[c.skill_id].add(tuple(sorted(pat.component_ids)))
    return out


def test_hay_colimites_que_medir(sistema):
    g, pm, cb = sistema
    assert len(_descomposiciones(cb, pm)) >= 18


def test_ningun_colimite_tiene_dos_descomposiciones(sistema):
    """
    El hecho medido. Si algun dia deja de valer —porque el sistema descubra
    una segunda descomposicion— este test falla y hay que celebrarlo: seria la
    primera vez que el Principio de Multiplicidad se cumple de verdad.
    """
    g, pm, cb = sistema
    multi = {k: v for k, v in _descomposiciones(cb, pm).items() if len(v) > 1}
    assert not multi, (
        f"AHORA SI hay objetos con varias descomposiciones: {list(multi)}. "
        "El Principio de Multiplicidad podria cumplirse; revisa si ya hay "
        "enlaces complejos y actualiza este test."
    )


def test_el_verificador_de_python_discrepa(sistema):
    """
    Fija la discrepancia en vez de dejarla latente: el codigo dice que si, la
    medicion dice que no. Cuando se corrija `are_homologous`, este test falla y
    obliga a revisar el resto.
    """
    g, pm, cb = sistema
    r = pm.verify_multiplicity_principle(g, cb)
    hay_mp_real = any(len(v) > 1 for v in _descomposiciones(cb, pm).values())
    assert r["satisfies"] and not hay_mp_real, (
        "la discrepancia entre verify_multiplicity_principle y la homologia de "
        "Ehresmann ha cambiado; revisa cual de los dos se movio"
    )
