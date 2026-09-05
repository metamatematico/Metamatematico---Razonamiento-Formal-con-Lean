# -*- coding: utf-8 -*-
"""Tests de la fibración π : Skills → Áreas.

Que π sea funtor —lo fija `test_funtor.py`— dice que está bien definida, no
que la base sirva: un funtor constante también cumple las dos leyes. La
condición que sí lo dice es la de FIBRACIÓN, y estos tests la fijan.

Las contrapartes formales están en
`MetamathProver/CategoryFoundations/Fibracion.lean` (0 sorry; los tres
teoremas de reindexado no dependen de ningún axioma). El orden de trabajo del
proyecto —primero Lean, después Python— se siguió: los teoremas se
demostraron antes de escribir `nucleo/graph/fibracion.py`.

EL ÚLTIMO TEST ES EL QUE IMPORTA. Fija el diagnóstico medido sobre el grafo
real: sólo 29 de 230 morfismos de orden cruzan de área, y por eso el 93 % de
los pares no tiene ni un skill del área de abajo por debajo. Está escrito para
FALLAR si alguien añade morfismos que crucen —que es la mejora que hace falta—
y obligar así a volver a medir en vez de dejar la conclusión vieja en pie.
"""
from __future__ import annotations

import pytest

from nucleo.graph.category import SkillCategory
from nucleo.graph.fibracion import levantar, verificar_fibracion
from nucleo.graph.functor import OBJETO_BASE, construir_funtor
from nucleo.types import MorphismType, PillarType, Skill

ORD = SkillCategory.ORDER_MORPHISMS


def _skill(sid, area):
    """Un skill ya TIPADO, que es como los deja `areas.py`."""
    return Skill(id=sid, name=sid, description=sid,
                 pillar=PillarType.SET, level=1,
                 metadata={"sort": "CONCEPTO", "area": area})


@pytest.fixture
def cadena():
    """Un grafo donde la condición SÍ se cumple.

        base_a ──▶ medio_a ──▶ cima_b

    `base_a` es el único skill de A por debajo de `cima_b`... salvo `medio_a`,
    que también es de A y está por encima de él. El mayor de los dos es
    `medio_a`, vive en A, y por tanto es el levantamiento cartesiano.
    """
    g = SkillCategory()
    g.add_skill(_skill("base_a", "A"))
    g.add_skill(_skill("medio_a", "A"))
    g.add_skill(_skill("cima_b", "B"))
    g.add_morphism("base_a", "medio_a", MorphismType.DEPENDENCY)
    g.add_morphism("medio_a", "cima_b", MorphismType.DEPENDENCY)
    return g


@pytest.fixture
def sin_soporte():
    """Y uno donde NO, que es el caso del grafo real.

        solo_a ──▶ cima_b        y aparte, huerfano_b

    La base dice `A ≼ B` por culpa de la primera flecha, pero `huerfano_b` no
    tiene ni un skill de A debajo. La base AFIRMA DE MÁS.
    """
    g = SkillCategory()
    g.add_skill(_skill("solo_a", "A"))
    g.add_skill(_skill("cima_b", "B"))
    g.add_skill(_skill("huerfano_b", "B"))
    g.add_morphism("solo_a", "cima_b", MorphismType.DEPENDENCY)
    return g


class TestLevantamiento:

    def test_el_cartesiano_es_el_mayor_no_uno_cualquiera(self, cadena):
        """`debajo` y `sobre` los cumplen los dos skills de A; `universal`
        sólo el de arriba. Sin la tercera condición la construcción no
        elegiría nada."""
        pi = construir_funtor(cadena)
        r = levantar(pi, cadena, "cima_b", "A", ORD)
        assert r.cartesiano == "medio_a"
        assert r.soporte == 2, "los dos de A son candidatos"

    def test_las_tres_condiciones_de_EsCartesiano(self, cadena):
        """Las mismas tres del `structure EsCartesiano` de Lean."""
        pi = construir_funtor(cadena)
        e, b = "cima_b", "A"
        lift = levantar(pi, cadena, e, b, ORD).cartesiano
        assert pi.en_objetos[lift] == b                       # sobre
        assert cadena.is_preorder_leq(lift, e, ORD)           # debajo
        for x in ("base_a",):                                 # universal
            assert cadena.is_preorder_leq(x, lift, ORD)

    def test_sin_soporte_se_nombra_aparte(self, sin_soporte):
        """«No hay ni un skill del área de abajo» es un problema distinto de
        «hay varios y ninguno domina»: el primero se arregla añadiendo
        morfismos al grafo, el segundo no."""
        pi = construir_funtor(sin_soporte)
        r = levantar(pi, sin_soporte, "huerfano_b", "A", ORD)
        assert not r
        assert r.soporte == 0
        assert "no hay ningun skill" in r.motivo


class TestVerificacion:

    def test_una_cadena_completa_es_fibracion(self, cadena):
        inf = verificar_fibracion(construir_funtor(cadena), cadena, tipos=ORD)
        assert inf.pares >= 1
        assert inf.es_fibracion, inf.fallos

    def test_un_huerfano_la_rompe(self, sin_soporte):
        pi = construir_funtor(sin_soporte)
        inf = verificar_fibracion(pi, sin_soporte, tipos=ORD)
        assert not inf.es_fibracion
        assert any(e == "huerfano_b" for e, _b, _m, _n in inf.fallos)

    def test_los_pares_triviales_no_cuentan(self, cadena):
        """`b' = π(e)` se levanta solo y no dice nada; contarlo inflaría la
        tasa."""
        pi = construir_funtor(cadena)
        inf = verificar_fibracion(pi, cadena, tipos=ORD)
        for _e, b, _m, _n in inf.fallos:
            assert b != OBJETO_BASE


class TestReindexado:
    """El pago de la condición: `reindexado_monotono` de Fibracion.lean."""

    def test_el_reindexado_conserva_el_orden(self):
        """Si `e1 ≤ e2` en la fibra de arriba, sus levantamientos conservan el
        orden en la de abajo. Es lo que permite trasladar una pregunta de un
        área a otra, y NO existe sin la condición cartesiana."""
        g = SkillCategory()
        for sid, area in [("a1", "A"), ("a2", "A"),
                          ("e1", "B"), ("e2", "B")]:
            g.add_skill(_skill(sid, area))
        g.add_morphism("a1", "a2", MorphismType.DEPENDENCY)
        g.add_morphism("a1", "e1", MorphismType.DEPENDENCY)
        g.add_morphism("a2", "e2", MorphismType.DEPENDENCY)
        g.add_morphism("e1", "e2", MorphismType.DEPENDENCY)
        pi = construir_funtor(g)
        l1 = levantar(pi, g, "e1", "A", ORD)
        l2 = levantar(pi, g, "e2", "A", ORD)
        assert l1 and l2
        assert g.is_preorder_leq(l1.cartesiano, l2.cartesiano, ORD), (
            "e1 <= e2 pero sus levantamientos no")


class TestElGrafoReal:
    """El diagnóstico medido, y el guardián que obliga a re-medirlo."""

    @pytest.fixture(scope="class")
    def real(self):
        try:
            from scripts.train_gnn_ppo import build_skill_graph
        except Exception:                                   # pragma: no cover
            pytest.skip("no se puede construir el grafo real")
        g = build_skill_graph()
        return g, construir_funtor(g)

    def test_pi_sigue_siendo_funtor(self, real):
        """La fibración es una condición ADEMÁS de la funtorialidad, no en su
        lugar."""
        from nucleo.graph.functor import verificar_functorialidad
        g, pi = real
        assert verificar_functorialidad(pi, g)["es_funtor"]

    def test_el_cuello_de_botella_son_los_morfismos_QUE_CRUZAN(self, real):
        """Medido: 29 de 230 morfismos de orden cruzan de área, y esos 29
        generan 74 relaciones entre áreas por clausura transitiva. De ahí que
        el 93 % de los pares no tenga soporte y la tasa sea del 0,3 %.

        ESTE TEST ESTÁ ESCRITO PARA FALLAR SI EL GRAFO MEJORA. Si alguien
        añade morfismos que crucen de área —que es justo lo que hace falta
        para que el supergrafo se sostenga— el número sube, el test cae, y
        obliga a volver a correr `scripts/fibracion_del_grafo.py` en vez de
        dejar en pie una conclusión que ya no vale.
        """
        g, pi = real
        cruzan = total = 0
        for m in g.morphisms:
            if m.morphism_type not in ORD:
                continue
            total += 1
            x = pi.en_objetos.get(m.source_id)
            y = pi.en_objetos.get(m.target_id)
            if x != y and OBJETO_BASE not in (x, y):
                cruzan += 1
        assert total > 100, "el grafo real no se cargó"
        assert cruzan / total < 0.20, (
            "los morfismos que cruzan de área han subido a %.1f %% (eran el "
            "12,6 %%). Vuelve a correr scripts/fibracion_del_grafo.py: la "
            "conclusión sobre la fibración puede haber cambiado."
            % (100 * cruzan / total))
