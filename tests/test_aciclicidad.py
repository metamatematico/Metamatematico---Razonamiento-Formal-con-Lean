"""
El grafo de joins debe ser aciclico.

POR QUE
-------
`hierarchy_well_founded` y `cn_join_gt_component` estaban SIN DEMOSTRAR en Lean,
y al intentar cerrarlos resulto que no eran dificiles: eran FALSOS tal como
estaban enunciados. Con un ciclo `x = join[y]`, `y = join[x]` la iteracion crece
sin parar —(0,0) (1,1) (2,2) (3,3)…— y ninguna de las dos conclusiones vale.

Los enunciados verdaderos llevan ahora la hipotesis `Aciclico`, que sus propios
docstrings ya mencionaban pero que no pedian. Este test comprueba que el grafo
real la satisface: sin eso los teoremas son ciertos pero no aplican.
"""
import sys

import pytest


@pytest.fixture(scope="module")
def joins():
    """join_id -> componentes, tal como los descubre el sistema."""
    sys.argv = ["x"]
    from scripts.train_gnn_ppo import build_skill_graph
    from nucleo.mes.patterns import PatternManager, ColimitBuilder
    from nucleo.graph.complexity import build_hierarchy_to_fixpoint

    g = build_skill_graph()
    pm = PatternManager()
    cb = ColimitBuilder(pm)
    build_hierarchy_to_fixpoint(g, pm, cb)
    out = {}
    for col in cb.all_colimits:
        pat = pm.get_pattern(col.pattern_id) if col.pattern_id else None
        if pat and col.skill_id:
            out[col.skill_id] = list(pat.component_ids)
    return out


def _alcanzables(a, joins):
    vistos, pila = set(), [a]
    while pila:
        for c in joins.get(pila.pop(), []):
            if c not in vistos:
                vistos.add(c)
                pila.append(c)
    return vistos


def test_hay_joins_que_comprobar(joins):
    assert len(joins) >= 18, f"solo {len(joins)} joins; el test perderia sentido"


def test_ningun_join_se_alcanza_a_si_mismo(joins):
    """
    Es exactamente la hipotesis `Aciclico` de ComplexityOrder.lean. Si falla,
    `hierarchy_well_founded` y `cn_join_gt_component` dejan de aplicar al
    sistema, aunque sigan siendo ciertos.
    """
    ciclos = [j for j in joins if j in _alcanzables(j, joins)]
    assert not ciclos, (
        f"joins en un ciclo: {ciclos}. La iteracion de cn no alcanzaria punto "
        "fijo y `apply_complexity_order` pararia en n rondas sin justificacion."
    )


def test_cn_acotado_y_positivo(joins):
    """max(cn) = 2 significa que el sistema construyo conceptos de 2o orden."""
    sys.argv = ["x"]
    from scripts.train_gnn_ppo import build_skill_graph
    from nucleo.mes.patterns import PatternManager, ColimitBuilder
    from nucleo.graph.complexity import build_hierarchy_to_fixpoint

    g = build_skill_graph()
    pm = PatternManager()
    cb = ColimitBuilder(pm)
    cn, _ = build_hierarchy_to_fixpoint(g, pm, cb)
    assert cn, "no se calculo ningun cn"
    assert max(cn.values()) >= 2, (
        f"max(cn) = {max(cn.values())}: el motor de complexificacion no esta "
        "produciendo conceptos de segundo orden"
    )
