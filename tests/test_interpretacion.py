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
    forma_de, admite_colimite, FORMA_COPRODUCTO, FORMA_PUSHOUT,
    SIN_PUSHOUT, PUSHOUT_SI_DETERMINISTA, RESTRICCIONES,
    DEGRADADAS, FUSIONES, SUBCATEGORIA_PLENA, NOTA_FUSION,
    cambia_de_valor, resolver, vertices_tras_fusionar,
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


class TestLasDosDecisiones:
    """
    Las dos elecciones de morfismos que el autor tomo, y su precio.

    Ninguna la podia tomar el codigo: cambian QUE colimites existen, no como
    se calculan.
    """

    def test_measure_theory_usa_nucleos(self):
        e = VEREDICTO["measure-theory"]
        assert "nucleo" in e.morfismos.lower()
        assert "MEDIBLE" in e.objeto, "el objeto ya no es un espacio de medida"

    def test_probability_es_subcategoria_ancha_de_measure(self):
        """Mismos objetos, nucleos de Markov contenidos en los nucleos."""
        assert "ancha" in VEREDICTO["probability-theory"].nota.lower()
        assert marca("probability-theory") == C
        assert marca("measure-theory") == C

    def test_homotopy_theory_es_la_localizacion(self):
        """Top[W^-1], no hTop. Lo imponen las aristas que ya salen del vertice.

        Todas —homology, cohomology, fundamental-group— invierten W, luego
        factorizan por la localizacion, que es el vertice inicial con esa
        propiedad.
        """
        e = VEREDICTO["homotopy-theory"]
        assert "RELATIVA" in e.objeto
        assert e.lean is None, "sin estructura de Quillen sobre Top en Mathlib"
        for arista in ("homology", "cohomology", "fundamental-group"):
            assert marca(arista) == F

    def test_solo_quedan_dos_sin_fijar(self):
        assert set(MORFISMO_SIN_FIJAR) == {"metric-spaces", "banach-spaces"}


class TestLaReglaDeLaForma:
    """La regla mira la FORMA del diagrama, no su contenido."""

    class _P:
        def __init__(self, links):
            self.index_morphisms = links

    def test_diagrama_discreto_es_coproducto(self):
        assert forma_de(self._P({})) == FORMA_COPRODUCTO

    def test_con_enlaces_distinguidos_es_pushout(self):
        assert forma_de(self._P({"d_0_1": ("0", "1")})) == FORMA_PUSHOUT

    def test_el_coproducto_existe_siempre(self):
        """Hom(coproducto, X) = producto de Hom(A_i, TX): sobrevive en nucleos."""
        for apex in ("homotopy-theory", "measure-theory", "cualquiera"):
            ok, _ = admite_colimite(self._P({}), apex)
            assert ok

    def test_el_pushout_no_existe_en_el_vertice_homotopico(self):
        """Ni hTop ni Top[W^-1] tienen pushouts.

        Y el resultado correcto no es «el colimite vale X» sino «este vertice
        no admite la operacion»: el colimite homotopico es otra operacion.
        """
        ok, motivo = admite_colimite(self._P({"d": ("0", "1")}), "homotopy-theory")
        assert ok is False
        assert "no admite la operacion" in motivo
        assert "homotopico" in motivo.lower()

    def test_el_pushout_en_medida_pide_flechas_deterministas(self):
        ok, motivo = admite_colimite(self._P({"d": ("0", "1")}), "measure-theory")
        assert ok is True
        assert "determinista" in motivo


class TestFormaDelGrafoReal:
    """Lo medido: las dos decisiones no invalidan nada de lo que ya habia."""

    @pytest.fixture(scope="class")
    def descomposiciones(self):
        sys.argv = ["x"]
        from nucleo.graph.category import SkillCategory
        from nucleo.pillars.math_domains import load_math_domains
        from nucleo.mes.patterns import PatternManager, ColimitBuilder
        from nucleo.graph.complexity import build_hierarchy_to_fixpoint
        from nucleo.graph.no_delgado import registrar_morfismos_certificados
        from nucleo.core import Nucleo
        n = Nucleo.__new__(Nucleo)
        g = SkillCategory(name="Forma")
        n._graph = g
        Nucleo._load_foundational_skills(n)
        load_math_domains(g)
        registrar_morfismos_certificados(g)
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        build_hierarchy_to_fixpoint(g, pm, cb)
        out = []
        for p in pm.all_patterns:
            col = cb.get_colimit_for_pattern(p.id)
            if col:
                out.append((p, col.skill_id))
        return out

    def test_casi_todas_son_coproducto(self, descomposiciones):
        formas = [forma_de(p) for p, _ in descomposiciones]
        assert formas.count(FORMA_COPRODUCTO) == 29
        assert formas.count(FORMA_PUSHOUT) == 2

    def test_ninguna_pierde_su_colimite_por_las_decisiones(self, descomposiciones):
        """Las cuatro que tocan un vertice decidido son de forma coproducto,
        luego las dos elecciones no cuestan ningun colimite de los que habia."""
        decididos = SIN_PUSHOUT | PUSHOUT_SI_DETERMINISTA
        for p, apex in descomposiciones:
            if (set(p.component_ids) | {apex}) & decididos:
                ok, _ = admite_colimite(p, apex)
                assert ok, f"{sorted(p.component_ids)} -> {apex} deja de admitir"


class TestDegradaciones:
    """`limits` y `nat-trans` no se borran: se degradan."""

    def test_las_dos_estan_degradadas(self):
        assert set(DEGRADADAS) == {"limits", "nat-trans"}

    def test_ninguna_era_vertice(self):
        """Por eso degradarlas no baja el recuento de vertices."""
        for k in DEGRADADAS:
            assert marca(k) == F

    def test_cada_una_dice_que_hacer_con_sus_aristas(self):
        for k, d in DEGRADADAS.items():
            assert d["entrantes"] and d["salientes"], (
                f"{k}: hay que repartir las aristas incidentes por direccion"
            )

    def test_limits_nombra_la_operacion_del_propio_grafo(self):
        """La razon de fondo: no fallaba por estar mal poblado."""
        assert "confusion de nivel" in VEREDICTO["limits"].nota


class TestFusiones:

    def test_los_alias_resuelven_a_un_superviviente(self):
        for retirada, superviviente in FUSIONES.items():
            assert resolver(retirada) == resolver(superviviente)
            assert superviviente not in FUSIONES or resolver(superviviente) != retirada

    def test_ninguna_etiqueta_se_borra(self, grafo):
        """Las retiradas quedan como alias: si se borraran, las 172 dejarian
        de mapear sobre el grafo."""
        for retirada in FUSIONES:
            assert retirada in VEREDICTO
            assert retirada in grafo.skill_ids

    def test_el_recuento_de_vertices(self):
        """87 -> 81. No 79 ni 76.

        De las once etiquetas que se retiran o degradan, CUATRO no eran
        vertices en el propio veredicto: proof-theory y recursion-theory son T,
        nat-trans y limits son F. Nunca estuvieron en los 87.
        """
        assert len(vertices()) == 87
        assert len(vertices_tras_fusionar()) == 81
        no_eran = [k for k in list(FUSIONES) + list(DEGRADADAS)
                   if marca(k) not in VERTICES]
        assert set(no_eran) == {"proof-theory", "recursion-theory",
                                "nat-trans", "limits"}


class TestNoFusionar:
    """La regla condicional, y por que se activo en dos de los tres grupos."""

    def test_las_dos_distinciones_se_respetan(self):
        assert set(SUBCATEGORIA_PLENA) == {"arithmetic-geometry", "number-fields"}

    def test_ninguna_subcategoria_plena_esta_fusionada(self):
        """Retirar la etiqueta y meter la inclusion arreglan igual el colimite;
        lo que no se puede es hacer las dos cosas."""
        for sub in SUBCATEGORIA_PLENA:
            assert sub not in FUSIONES

    def test_cada_una_declara_su_ambiente(self):
        for sub, (ambiente, porque) in SUBCATEGORIA_PLENA.items():
            assert marca(ambiente) in VERTICES
            assert porque


class TestElCocienteNoMueveNingunValor:
    """
    El aviso: una fusion es un cociente del diagrama indice, y el colimite del
    cociente no es el del original. Donde dos etiquetas fusionadas coexistian,
    lo que era un coproducto pasa a ser un coigualador.

    Aplicada la regla condicional, ninguna descomposicion queda en ese caso —
    que es precisamente para lo que sirve la regla.
    """

    @pytest.fixture(scope="class")
    def descomposiciones(self):
        sys.argv = ["x"]
        from nucleo.graph.category import SkillCategory
        from nucleo.pillars.math_domains import load_math_domains
        from nucleo.mes.patterns import PatternManager, ColimitBuilder
        from nucleo.graph.complexity import build_hierarchy_to_fixpoint
        from nucleo.graph.no_delgado import registrar_morfismos_certificados
        from nucleo.core import Nucleo
        n = Nucleo.__new__(Nucleo)
        g = SkillCategory(name="Cociente")
        n._graph = g
        Nucleo._load_foundational_skills(n)
        load_math_domains(g)
        registrar_morfismos_certificados(g)
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        build_hierarchy_to_fixpoint(g, pm, cb)
        return [(p, cb.get_colimit_for_pattern(p.id).skill_id)
                for p in pm.all_patterns if cb.get_colimit_for_pattern(p.id)]

    def test_ninguna_cambia_de_valor(self, descomposiciones):
        movidas = [(sorted(p.component_ids), ap, cambia_de_valor(p, ap))
                   for p, ap in descomposiciones if cambia_de_valor(p, ap)]
        assert movidas == [], (
            f"estas cambian de valor al fusionar y hay que recalcularlas: {movidas}"
        )

    def test_si_se_fusionara_arithmetic_geometry_si_cambiarian(self, descomposiciones):
        """Contraprueba: la regla no es decorativa.

        Con `arithmetic-geometry` fusionado en `algebraic-geometry`, tres
        descomposiciones tendrian el apice colapsado dentro de sus propias
        componentes.
        """
        colapsan = 0
        for p, ap in descomposiciones:
            nodos = set(p.component_ids) | {ap}
            if {"algebraic-geometry", "arithmetic-geometry"} <= nodos:
                colapsan += 1
        assert colapsan == 3
