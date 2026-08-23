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

LA CAUSA
--------
No es el modelo. `MP_alcanzable_en_preorden` (EhresmannLinks.lean) demuestra que
en un preorden finito de cinco objetos MP se cumple, luego modelar el grafo como
preorden no lo impide.

Es el ALGORITMO. `_detect_convergence_patterns` toma, para cada nodo X, TODOS
sus predecesores directos y genera UN patron. Su propio docstring lo dice: "each
convergence point corresponds to one potential join" —uno, en singular—. Por
construccion nunca produce dos descomposiciones del mismo objeto.

Y la multiplicidad ESTA AHI, sin descubrir: mirando subconjuntos de los
componentes aparecen 5 descomposiciones alternativas, y tres parejas de ellas no
estan conectadas por ningun cluster. `homology` tiene tres descomposiciones
mutuamente inconexas. Eso es MP, en el grafo real.
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


class TestMultiplicidadDisponible:
    """
    La multiplicidad existe en el grafo; el algoritmo no la busca. Estos tests
    lo miden, para que la decision de cambiar `_detect_convergence_patterns` se
    tome sobre datos y no sobre intuicion.
    """

    def _descomposiciones_por_subconjunto(self, sistema):
        import itertools
        from nucleo.graph.complexity import find_colimit
        g, pm, cb = sistema
        out = {}
        for c in cb.all_colimits:
            p = pm.get_pattern(c.pattern_id) if c.pattern_id else None
            if not (p and c.skill_id):
                continue
            comps = sorted(p.component_ids)
            D = {tuple(comps)}
            for k in range(2, len(comps)):
                for sub in itertools.combinations(comps, k):
                    if find_colimit(list(sub), g, cb) == c.skill_id:
                        D.add(sub)
            if len(D) > 1:
                out[c.skill_id] = D
        return out

    def test_hay_descomposiciones_alternativas_sin_descubrir(self, sistema):
        d = self._descomposiciones_por_subconjunto(sistema)
        assert d, (
            "ya no hay descomposiciones alternativas ocultas; si el algoritmo "
            "cambio para descubrirlas, actualiza test_multiplicidad entero"
        )
        assert "homology" in d, f"esperaba homology entre {list(d)}"

    def test_hay_parejas_no_conectadas(self, sistema):
        """
        Lo decisivo: sin parejas inconexas no habria MP aunque hubiera varias
        descomposiciones. Hay tres, todas en `homology`.
        """
        import itertools
        from nucleo.graph.category import SkillCategory
        g, pm, cb = sistema
        ORD = SkillCategory.ORDER_MORPHISMS

        def leq(a, b):
            return a == b or b in g.reachable_from(a, morphism_types=ORD)

        def conectados(S, T):
            return all(any(leq(s, t) for t in T) for s in S)

        libres = [
            (j, S, T)
            for j, D in self._descomposiciones_por_subconjunto(sistema).items()
            for S, T in itertools.combinations(sorted(D), 2)
            if not conectados(S, T) and not conectados(T, S)
        ]
        assert len(libres) >= 3, (
            f"parejas no conectadas: {len(libres)}, esperaba al menos 3. "
            "Si bajo, el grafo perdio multiplicidad disponible."
        )
