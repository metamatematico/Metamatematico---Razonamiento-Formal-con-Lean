# -*- coding: utf-8 -*-
"""Viajar por la fibración: trasladar un concepto al área que lo sostiene.

QUE SE VIGILA AQUI, Y POR QUE NO ES LO MISMO QUE `test_fibracion.py`
--------------------------------------------------------------------
`test_fibracion.py` comprueba la CONDICION —si cada par admite levantamiento
cartesiano—. Estos tests comprueban el USO: que `viaje.py` devuelva el
traslado correcto cuando existe, y que se NIEGUE con su motivo cuando no.

La segunda mitad es la que importa. π no es una fibración —102 de 1436 pares,
7,1 %, contra un nulo de 6,8 %— así que la mayoría de las preguntas no tienen
respuesta, y un módulo de viajes que devolviera «lo más parecido» convertiría
ese 93 % en respuestas plausibles sin soporte. Es exactamente lo que este
sistema existe para no hacer, y por eso se testea el NO.
"""
import pytest

from nucleo.graph.category import SkillCategory
from nucleo.graph.functor import construir_funtor
from nucleo.graph.viaje import (BaseDirecta, Cobertura, base_directa,
                                cobertura, destinos, ruta, viajar)
from nucleo.types import MorphismType, PillarType, Skill


def _skill(sid, area):
    return Skill(id=sid, name=sid, description=sid,
                 pillar=PillarType.SET, level=1,
                 metadata={"sort": "CONCEPTO", "area": area})


@pytest.fixture
def cadena():
    """base_a -> medio_a -> cima_b. El viaje de `cima_b` a A da `medio_a`."""
    g = SkillCategory()
    for sid, ar in (("base_a", "A"), ("medio_a", "A"), ("cima_b", "B")):
        g.add_skill(_skill(sid, ar))
    g.add_morphism("base_a", "medio_a", MorphismType.DEPENDENCY)
    g.add_morphism("medio_a", "cima_b", MorphismType.DEPENDENCY)
    return g


@pytest.fixture
def tres_pisos():
    """a -> b -> c con tres areas, para encadenar dos viajes."""
    g = SkillCategory()
    for sid, ar in (("raiz_a", "A"), ("medio_b", "B"), ("cima_c", "C")):
        g.add_skill(_skill(sid, ar))
    g.add_morphism("raiz_a", "medio_b", MorphismType.DEPENDENCY)
    g.add_morphism("medio_b", "cima_c", MorphismType.DEPENDENCY)
    return g


class TestViajeSimple:

    def test_el_viaje_devuelve_el_soporte(self, cadena):
        v = viajar(cadena, "cima_b", "A")
        assert v, v.motivo
        assert v.soporte == "medio_a", "el cartesiano es el MAYOR, no `base_a`"
        assert v.area_origen == "B"

    def test_es_verdadero_o_falso_segun_exista(self, cadena):
        assert viajar(cadena, "cima_b", "A")
        assert not viajar(cadena, "cima_b", "Z")

    def test_negarse_a_un_area_que_la_base_no_afirma(self, cadena):
        """El caso que NO puede contestarse con una aproximacion."""
        v = viajar(cadena, "cima_b", "Z")
        assert v.soporte is None
        assert "no es un area" in v.motivo

    def test_no_se_viaja_al_area_propia(self, cadena):
        v = viajar(cadena, "cima_b", "B")
        assert not v and "ya vive" in v.motivo

    def test_un_nodo_que_no_existe_no_revienta(self, cadena):
        v = viajar(cadena, "no-existe", "A")
        assert not v and "no esta en el grafo" in v.motivo


class TestLaBaseEsLaDirecta:
    """Viajar por la clausura seria afirmar un soporte que nadie induce."""

    def test_la_base_directa_no_cierra(self, tres_pisos):
        pi = construir_funtor(tres_pisos)
        # cerrada: desde A se llega a B y a C
        assert pi.codominio.alcanzables_desde("A") >= {"A", "B", "C"}
        # directa: desde A solo a B
        d = base_directa(pi)
        assert d.codominio.alcanzables_desde("A") == {"A", "B"}
        assert isinstance(d.codominio, BaseDirecta)

    def test_no_se_viaja_por_una_relacion_solo_de_la_clausura(self, tres_pisos):
        """`A ≼ C` existe en la clausura y NINGUN morfismo la induce.

        Es la diferencia entre 69 flechas y 462 relaciones en el grafo real.
        Contestar por una de las 393 inventadas seria dar un soporte que el
        grafo no tiene.
        """
        v = viajar(tres_pisos, "cima_c", "A")
        assert not v
        assert "la base no afirma" in v.motivo

    def test_pero_si_por_la_flecha_directa(self, tres_pisos):
        assert viajar(tres_pisos, "cima_c", "B").soporte == "medio_b"


class TestDestinos:

    def test_destinos_solo_devuelve_viajes_que_existen(self, cadena):
        ds = destinos(cadena, "cima_b")
        assert [v.destino for v in ds] == ["A"]
        assert all(bool(v) for v in ds), (
            "destinos() no puede devolver un viaje sin soporte: es la lista "
            "que se le enseña a alguien, y cada fila es una promesa")

    def test_desde_un_nodo_sin_area_no_hay_destinos(self, cadena):
        assert destinos(cadena, "no-existe") == []


class TestRuta:
    """`reindexado_compuesto`: encadenar traslados no depende del camino."""

    def test_encadena_cuando_no_hay_flecha_directa(self, tres_pisos):
        r = ruta(tres_pisos, "cima_c", "A")
        assert [v.destino for v in r] == ["B", "A"], (
            "de C a A hay que pasar por B: la base no relaciona A y C "
            "directamente")
        assert r[0].soporte == "medio_b"
        assert r[1].soporte == "raiz_a"

    def test_la_ruta_de_un_solo_paso_es_el_viaje(self, tres_pisos):
        r = ruta(tres_pisos, "cima_c", "B")
        assert len(r) == 1 and r[0].soporte == "medio_b"

    def test_sin_ruta_devuelve_vacio(self, cadena):
        assert ruta(cadena, "cima_b", "Z") == []

    def test_el_tope_corta_la_cadena(self, tres_pisos):
        """Una cadena larga traslada tan lejos que deja de responder."""
        assert ruta(tres_pisos, "cima_c", "A", tope=1) == []


class TestCobertura:
    """Toda lista de viajes se publica con cuantos de los prometidos existen."""

    def test_la_cadena_entera_se_cubre(self, cadena):
        c = cobertura(cadena)
        assert c.pares == 1 and c.con_viaje == 1
        assert c.tasa == 1.0

    def test_cuenta_los_pares_que_la_base_afirma_y_no_se_cumplen(self):
        """El caso del grafo real: la base afirma y el total no lo sostiene."""
        g = SkillCategory()
        for sid, ar in (("solo_a", "A"), ("cima_b", "B"), ("huerfano_b", "B")):
            g.add_skill(_skill(sid, ar))
        g.add_morphism("solo_a", "cima_b", MorphismType.DEPENDENCY)
        c = cobertura(g)
        assert c.pares == 2, "la base afirma A ≼ B para LOS DOS de B"
        assert c.con_viaje == 1, "y solo `cima_b` tiene soporte"
        assert not viajar(g, "huerfano_b", "A")

    def test_una_cobertura_vacia_no_divide_por_cero(self):
        assert Cobertura().tasa == 0.0
