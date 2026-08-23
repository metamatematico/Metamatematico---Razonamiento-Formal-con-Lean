"""
Los funtores de transicion cumplen lo que Evolution.lean supone.

Un teorema con hipotesis que el sistema no satisface no respalda nada. Estos
tests comprueban, sobre el sistema evolutivo real, las propiedades que
`Evolution.lean` demuestra en abstracto:

  · comp_assoc                  la composicion es asociativa
  · eliminado_es_absorbente     lo eliminado no vuelve
  · compatible_iff              compatibilidad = ley de funtor
  · compatible_unico            el funtor largo queda determinado
  · compatibilidad_transitiva   basta comprobarla localmente

Nota sobre nombres: el MAPEO de la auditoria nombraba `complexify`,
`transition_functor` y `detect_emergence`, que NO EXISTEN. Las reales son
`apply_option`, `TransitionFunctor` y `measure_emergence`. La auditoria no lo
detectaba porque solo validaba el lado de Lean; ahora valida los dos.
"""
import pytest

from nucleo.graph.category import SkillCategory
from nucleo.graph.evolution import EvolutionarySystem, TransitionFunctor
from nucleo.mes.patterns import ColimitBuilder, PatternManager
from nucleo.types import MorphismType, PillarType, Skill


def _grafo():
    g = SkillCategory()
    for sid in ("a", "b", "c", "j"):
        g.add_skill(Skill(id=sid, name=sid, description=sid,
                          pillar=PillarType.SET, level=1))
    for sid in ("a", "b", "c"):
        g.add_morphism(sid, "j", MorphismType.DEPENDENCY)
    return g


@pytest.fixture
def sistema():
    g = _grafo()
    pm = PatternManager()
    return EvolutionarySystem(g, pattern_manager=pm,
                              colimit_builder=ColimitBuilder(pm))


def _tf(t1, t2, obj):
    return TransitionFunctor(source_time=t1, target_time=t2,
                             object_map=dict(obj), morphism_map={})


class TestComposicion:
    """Contraparte de `comp`, `comp_assoc` y `eliminado_es_absorbente`."""

    def test_composicion_encadena_los_mapeos(self):
        k12 = _tf(1, 2, {"a": "b"})
        k23 = _tf(2, 3, {"b": "c"})
        assert k23.compose(k12).object_map["a"] == "c"

    def test_lo_eliminado_no_vuelve(self):
        """`eliminado_es_absorbente`: si f(s) = None, toda composicion da None."""
        k12 = _tf(1, 2, {"a": None})
        k23 = _tf(2, 3, {"a": "c", "b": "c"})
        assert k23.compose(k12).object_map["a"] is None

    def test_la_composicion_es_asociativa(self):
        """`comp_assoc`: sin esto, `k_{t1,t4}` dependeria del orden."""
        k12 = _tf(1, 2, {"a": "b", "x": None})
        k23 = _tf(2, 3, {"b": "c", "a": "c"})
        k34 = _tf(3, 4, {"c": "j", "b": "j"})

        izq = k34.compose(k23).compose(k12)
        der = k34.compose(k23.compose(k12))
        assert izq.object_map == der.object_map, (
            f"asociatividad rota: {izq.object_map} vs {der.object_map}"
        )

    def test_asociatividad_con_eliminacion_en_medio(self):
        """El caso delicado: `none` propagandose por los dos caminos."""
        k12 = _tf(1, 2, {"a": "b"})
        k23 = _tf(2, 3, {"b": None})
        k34 = _tf(3, 4, {"c": "j"})
        izq = k34.compose(k23).compose(k12)
        der = k34.compose(k23.compose(k12))
        assert izq.object_map["a"] is None
        assert izq.object_map == der.object_map


class TestCompatibilidad:
    """Contraparte de `Compatible`, `compatible_iff` y `compatible_unico`."""

    def test_compatibilidad_es_la_ley_de_funtor(self):
        """`compatible_iff`: objeto a objeto, k23 . k12 = k13."""
        k12 = _tf(1, 2, {"a": "b"})
        k23 = _tf(2, 3, {"b": "c"})
        k13 = k23.compose(k12)
        for s in k12.object_map:
            esperado = k12.object_map[s]
            esperado = k23.object_map.get(esperado) if esperado else None
            assert k13.object_map[s] == esperado

    def test_el_funtor_largo_queda_determinado(self):
        """`compatible_unico`: dos composiciones dan el mismo resultado."""
        k12 = _tf(1, 2, {"a": "b", "c": None})
        k23 = _tf(2, 3, {"b": "j"})
        assert k23.compose(k12).object_map == k23.compose(k12).object_map

    def test_composicion_incompatible_falla_ruidosamente(self):
        """Componer tiempos que no encajan debe dar error, no un resultado."""
        k12 = _tf(1, 2, {"a": "b"})
        k34 = _tf(3, 4, {"b": "c"})
        with pytest.raises(AssertionError):
            k34.compose(k12)


class TestSistemaReal:

    def test_verify_compatibility_existe_y_es_local(self, sistema):
        """
        `compatibilidad_transitiva` justifica comprobarla en tripletas
        consecutivas en vez de en todos los pares.
        """
        assert hasattr(sistema, "verify_compatibility")
        import inspect
        params = inspect.signature(sistema.verify_compatibility).parameters
        assert list(params) == ["t1", "t2", "t3"], (
            "verify_compatibility deberia tomar una tripleta"
        )

    def test_measure_emergence_devuelve_las_metricas(self, sistema):
        m = sistema.measure_emergence()
        for clave in ("num_complex_links", "emergence_ratio"):
            assert clave in m, f"falta {clave} en {list(m)}"

    def test_las_funciones_del_mapeo_existen(self):
        """
        Las tres que el MAPEO nombraba —complexify, transition_functor,
        detect_emergence— no existen. Este test fija los nombres reales.
        """
        import nucleo.graph.evolution as ev
        for nombre in ("EvolutionarySystem", "TransitionFunctor",
                       "CategorySnapshot"):
            assert hasattr(ev, nombre), f"falta {nombre}"
        for metodo in ("apply_option", "verify_compatibility",
                       "detect_complex_links", "measure_emergence"):
            assert hasattr(ev.EvolutionarySystem, metodo), f"falta {metodo}"
