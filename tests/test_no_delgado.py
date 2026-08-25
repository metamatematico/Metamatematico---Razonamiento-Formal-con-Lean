"""
Tests de la salida de la delgadez.

QUE SE COMPRUEBA
----------------
Los teoremas de `Complexificacion.lean §9-§10` y `MorfismosGrupoAnillo.lean`,
sobre el codigo que los realiza:

  · `Hom(a,b)` puede tener mas de un elemento — indexado por CONSTRUCCION;
  · `cota_superior_no_implica_cocono` — el caso donde el cociente delgado
    concede un co-cono que no lo es;
  · `delgado_cocono_automatico` — y por que con un solo enlace nunca discrepan;
  · los tres morfismos certificados de group-theory a ring-theory.
"""
import pytest

from nucleo.types import Skill, MorphismType, PillarType
from nucleo.graph.category import SkillCategory
from nucleo.mes.patterns import PatternManager, ColimitBuilder
from nucleo.graph.no_delgado import (
    multiplicidad, caminos, es_cocono_libre, hay_cocono_libre,
    comparar_cocono, registrar_morfismos_certificados,
    MORFISMOS_CERTIFICADOS,
)


def _g(*ids: str) -> SkillCategory:
    g = SkillCategory(name="NoDelgado")
    for sid in ids:
        g.add_skill(Skill(id=sid, name=sid, pillar=PillarType.SET, level=0))
    return g


# ---------------------------------------------------------------------------
# Hom deja de ser un booleano
# ---------------------------------------------------------------------------

class TestHomComoConjunto:

    def test_dos_construcciones_son_dos_morfismos(self):
        g = _g("a", "b")
        m1 = g.add_morphism("a", "b", MorphismType.DEPENDENCY,
                            construccion="grupo-aditivo")
        m2 = g.add_morphism("a", "b", MorphismType.DEPENDENCY,
                            construccion="grupo-unidades")
        assert m1.id != m2.id
        assert multiplicidad(g).pares_multiples == 1
        assert not multiplicidad(g).es_delgado

    def test_la_misma_construccion_no_se_duplica(self):
        g = _g("a", "b")
        m1 = g.add_morphism("a", "b", MorphismType.DEPENDENCY, construccion="x")
        m2 = g.add_morphism("a", "b", MorphismType.DEPENDENCY, construccion="x")
        assert m1.id == m2.id
        assert multiplicidad(g).es_delgado

    def test_grafo_sin_multiplicidad_es_delgado(self):
        g = _g("a", "b", "c")
        g.add_morphism("a", "b", MorphismType.DEPENDENCY)
        g.add_morphism("b", "c", MorphismType.DEPENDENCY)
        assert multiplicidad(g).es_delgado


# ---------------------------------------------------------------------------
# El co-cono deja de ser "cota superior"
# ---------------------------------------------------------------------------

class TestCoconoNoDelgado:

    def _testigo(self):
        """
        Dos enlaces distinguidos PARALELOS `A ⇉ B`, y un apice `C` por encima
        de ambos.

            A ══(x, y)══> B
             \\           /
              \\         /
               v       v
                   C

        El cociente delgado dice «C es cota superior de {A,B}» y concede
        co-cono. La condicion de Ehresmann exige `x ; f_B = f_A` Y
        `y ; f_B = f_A`, luego `x ; f_B = y ; f_B`, que con `x ≠ y` es falso.

        Contraparte formal: `cota_superior_no_implica_cocono`.
        """
        g = _g("A", "B", "C")
        x = g.add_morphism("A", "B", MorphismType.DEPENDENCY, construccion="x")
        y = g.add_morphism("A", "B", MorphismType.DEPENDENCY, construccion="y")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        pm = PatternManager()
        p = pm.create_pattern(["A", "B"], [x.id, y.id], graph=g)
        return g, pm, p, x, y

    def test_los_enlaces_paralelos_no_colapsan(self):
        """La categoria de indices tambien tiene que dejar de ser delgada.

        `create_pattern` indexaba por `d_{i}_{j}`, asi que el segundo enlace
        paralelo sobreescribia al primero: el grafo podia ser no delgado y el
        indice seguia siendolo.
        """
        _, _, p, _, _ = self._testigo()
        assert len(p.index_morphisms) == 2

    def test_delgado_concede_lo_que_libre_niega(self):
        """El caso que separa las dos lecturas."""
        g, _, p, _, _ = self._testigo()
        r = comparar_cocono(p, "C", g)

        assert r["delgado"] is True, "C es cota superior de A y B"
        assert r["libre"] is False, "pero ninguna eleccion conmuta"
        assert r["discrepan"] is True

    def test_con_un_solo_enlace_nunca_discrepan(self):
        """Con un enlace la familia queda determinada por propagacion.

        Es la razon de que sobre el grafo real, hoy, no haya ninguna
        discrepancia: los patrones con enlaces distinguidos tienen uno solo.
        Contraparte formal: `delgado_cocono_automatico`.
        """
        g = _g("A", "B", "C")
        x = g.add_morphism("A", "B", MorphismType.DEPENDENCY, construccion="x")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        pm = PatternManager()
        p = pm.create_pattern(["A", "B"], [x.id], graph=g)

        r = comparar_cocono(p, "C", g)
        assert r["delgado"] is True
        assert r["libre"] is True
        assert r["discrepan"] is False

    def test_sin_enlaces_distinguidos_la_condicion_es_vacua(self):
        """Un diagrama DISCRETO no impone nada: es el estado anterior."""
        g = _g("A", "B", "C")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        pm = PatternManager()
        p = pm.create_pattern(["A", "B"], [], graph=g)

        assert p.index_morphisms == {}
        assert es_cocono_libre(p, {"A": (), "B": ()}, g) is True

    def test_sin_cota_no_hay_cocono(self):
        g = _g("A", "B", "C")
        pm = PatternManager()
        p = pm.create_pattern(["A", "B"], [], graph=g)
        assert hay_cocono_libre(p, "C", g) is False


# ---------------------------------------------------------------------------
# Caminos: Hom en la categoria libre
# ---------------------------------------------------------------------------

class TestCaminos:

    def test_dos_paralelos_dan_dos_caminos(self):
        g = _g("a", "b")
        g.add_morphism("a", "b", MorphismType.DEPENDENCY, construccion="x")
        g.add_morphism("a", "b", MorphismType.DEPENDENCY, construccion="y")
        assert len(caminos(g, "a", "b")) == 2

    def test_identidad_es_el_camino_vacio(self):
        g = _g("a")
        assert caminos(g, "a", "a") == [()]

    def test_se_respeta_la_cota_de_longitud(self):
        g = _g("a", "b", "c", "d")
        g.add_morphism("a", "b", MorphismType.DEPENDENCY)
        g.add_morphism("b", "c", MorphismType.DEPENDENCY)
        g.add_morphism("c", "d", MorphismType.DEPENDENCY)
        assert caminos(g, "a", "d", max_longitud=2) == []
        assert len(caminos(g, "a", "d", max_longitud=3)) == 1


# ---------------------------------------------------------------------------
# Los morfismos certificados en Lean
# ---------------------------------------------------------------------------

class TestMorfismosCertificados:

    def test_se_registran_los_tres(self):
        g = _g("group-theory", "ring-theory")
        registrar_morfismos_certificados(g)

        hs = [h for h in g.hom("group-theory", "ring-theory")
              if h.morphism_type != MorphismType.IDENTITY]
        constrs = {h.metadata.get("construccion") for h in hs}
        assert constrs == {"grupo-aditivo", "grupo-unidades", "grupo-trivial"}

    def test_cada_uno_cita_su_teorema(self):
        g = _g("group-theory", "ring-theory")
        registrar_morfismos_certificados(g)
        for h in g.hom("group-theory", "ring-theory"):
            if h.metadata.get("certificado"):
                assert h.metadata["teorema_lean"].startswith("MorfismosGrupoAnillo.")

    def test_el_par_deja_de_ser_delgado(self):
        g = _g("group-theory", "ring-theory")
        assert multiplicidad(g).es_delgado
        registrar_morfismos_certificados(g)
        assert not multiplicidad(g).es_delgado

    def test_es_idempotente(self):
        g = _g("group-theory", "ring-theory")
        registrar_morfismos_certificados(g)
        n1 = len(g.morphisms)
        registrar_morfismos_certificados(g)
        assert len(g.morphisms) == n1

    def test_no_falla_si_faltan_los_skills(self):
        g = _g("otra-cosa")
        assert registrar_morfismos_certificados(g) == []

    def test_el_mapeo_declara_teorema_para_cada_uno(self):
        for origen, destino, constr, teorema, afirma in MORFISMOS_CERTIFICADOS:
            assert origen and destino and constr
            assert teorema.startswith("MorfismosGrupoAnillo.")
            assert afirma
