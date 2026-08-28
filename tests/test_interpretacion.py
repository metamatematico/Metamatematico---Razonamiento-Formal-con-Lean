"""
Guardia de la interpretacion del grafo.

El veredicto del autor sobre las 172 etiquetas es un dato editorial: si el
grafo cambia y la tabla no, o al reves, el desajuste tiene que saltar aqui y no
descubrirse tres pasos despues.
"""
import sys

import pytest

from nucleo.graph.interpretacion import (
    VEREDICTO, DUPLICADOS, MORFISMO_SIN_FIJAR, VERTICES,
    C, S, F, O, T, marca, vertices, aristas, recuento,
)


@pytest.fixture(scope="module")
def grafo():
    sys.argv = ["x"]
    from nucleo.graph.category import SkillCategory
    from nucleo.pillars.math_domains import load_math_domains
    from nucleo.core import Nucleo
    n = Nucleo.__new__(Nucleo)
    g = SkillCategory(name="Interp")
    n._graph = g
    Nucleo._load_foundational_skills(n)
    load_math_domains(g)
    return g


class TestCobertura:

    def test_todas_las_etiquetas_tienen_veredicto(self, grafo):
        faltan = sorted(set(grafo.skill_ids) - set(VEREDICTO))
        assert not faltan, f"sin veredicto: {faltan}"

    def test_no_hay_veredictos_inventados(self, grafo):
        sobran = sorted(set(VEREDICTO) - set(grafo.skill_ids))
        assert not sobran, f"no estan en el grafo: {sobran}"

    def test_el_recuento_cuadra_con_el_documento(self):
        """Las cifras del veredicto, tal como las publico el autor."""
        assert recuento() == {C: 73, S: 14, F: 28, O: 4, T: 53}

    def test_87_vertices_28_aristas(self):
        assert len(vertices()) == 87
        assert len(aristas()) == 28


class TestCoherencia:

    def test_toda_marca_es_valida(self):
        assert {e.marca for e in VEREDICTO.values()} <= {C, S, F, O, T}

    def test_los_vertices_declaran_objetos_y_morfismos(self):
        """Un vertice sin morfismos declarados no sirve: la categoria son las
        flechas tanto como los objetos."""
        for k, e in VEREDICTO.items():
            if e.marca in VERTICES:
                assert e.objeto, f"{k} es vertice y no dice que es un objeto"

    def test_las_aristas_declaran_su_funtor(self):
        for k, e in VEREDICTO.items():
            if e.marca == F:
                assert e.morfismos, f"{k} es arista y no dice que funtor es"

    def test_los_duplicados_tienen_veredicto(self, grafo):
        for nombre, ids in DUPLICADOS:
            for i in ids:
                assert i in VEREDICTO, f"{i} en DUPLICADOS sin veredicto"
                assert i in grafo.skill_ids, f"{i} no esta en el grafo"

    def test_las_marcas_dentro_de_un_grupo_pueden_diferir(self):
        """DUPLICADOS agrupa etiquetas que DENOTAN la misma categoria, no
        que compartan marca.

        `proof-theory` denota la categoria deductiva pero es T —nombra
        una rama—; `nat-trans` denota [C,D] pero es F —nombra la capa
        de flechas—. Confundir las dos relaciones fue un error de este
        test, no de la tabla.
        """
        grupos = {n: ids for n, ids in DUPLICADOS}
        assert marca("proof-theory") == T
        assert marca("fol-deduction") == C
        assert {"proof-theory", "fol-deduction"} <= set(
            grupos["categoria deductiva"])
        assert marca("nat-trans") == F
        assert marca("functors") == C

    def test_cuantos_vertices_redundantes_hay(self):
        """El hallazgo: hay grupos con MAS DE UN vertice legitimo.

        Un colimite sobre dos vertices que nombran la misma categoria sale
        degenerado. Esta cifra es la medida del problema, y el test existe para
        que no cambie en silencio.
        """
        redundantes = sum(
            max(0, sum(1 for i in ids if marca(i) in VERTICES) - 1)
            for _, ids in DUPLICADOS
        )
        assert redundantes == 8

    def test_las_de_morfismo_sin_fijar_son_vertices(self):
        for i in MORFISMO_SIN_FIJAR:
            assert marca(i) in VERTICES, (
                f"{i} no es vertice; no tiene sentido decir que le falta el morfismo"
            )


class TestHallazgos:
    """Las tres cosas que el veredicto descubrio y que conviene no perder."""

    def test_homotopy_type_theory_es_la_unica_imposible_por_fundamento(self):
        e = VEREDICTO["homotopy-type-theory"]
        assert e.lean is None
        assert "IMPOSIBLE en Lean 4" in e.nota

    def test_fol_deduction_no_es_tema(self):
        """Un sistema deductivo es una categoria (Lambek), y es el domicilio de
        las quince tacticas."""
        assert marca("fol-deduction") == C
        assert VEREDICTO["fol-deduction"].lean is None, "Mathlib no lo tiene"

    def test_las_tacticas_y_estrategias_estan_fuera(self, grafo):
        tacticas = [i for i in grafo.skill_ids
                    if i.startswith(("tactic-", "strategy-"))]
        assert len(tacticas) == 15
        assert all(marca(i) == T for i in tacticas)

    def test_homology_y_limits_son_aristas(self):
        """Eran los dos vertices del bloque 1 que resultaron ser funtores."""
        assert marca("homology") == F
        assert marca("limits") == F
