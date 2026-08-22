"""
Tests del funtor cociente pi: Skills -> Agentes.

Las tres categorias que el diseño describe son en realidad dos: los skills
L1-L3 y las teorias/subteorias son el MISMO grafo. La categoria distinta es la
de agentes, y con 172 objetos frente a 15 no puede haber isomorfismo. Lo que
si hay es una proyeccion, y estos tests fijan que sea un FUNTOR — que es lo
que hace falta para que la estructura de Ehresmann baje de un nivel al otro.

Las contrapartes formales estan en
MetamathProver/CategoryFoundations/QuotientFunctor.lean (0 sorry).
"""
import pytest

from nucleo.graph.category import SkillCategory
from nucleo.graph.functor import (
    OBJETO_BASE,
    construir_funtor,
    verificar_functorialidad,
    verificar_preservacion_colimites,
)
from nucleo.types import MorphismType, PillarType, Skill


def _skill(sid, categoria=None):
    md = {"category": categoria} if categoria else {}
    return Skill(id=sid, name=sid, description=sid,
                 pillar=PillarType.SET, level=1, metadata=md)


@pytest.fixture
def grafo():
    """Grafo minimo con dos categorias y un fundacional sin categoria."""
    g = SkillCategory()
    for sid, cat in [("anillos", "algebra"), ("cuerpos", "algebra"),
                     ("variedades", "geometry"), ("zfc", None)]:
        g.add_skill(_skill(sid, cat))
    g.add_morphism("anillos", "cuerpos", MorphismType.DEPENDENCY)
    g.add_morphism("cuerpos", "variedades", MorphismType.DEPENDENCY)
    g.add_morphism("zfc", "anillos", MorphismType.DEPENDENCY)
    return g


class TestConstruccion:

    def test_todo_skill_tiene_imagen(self, grafo):
        """pi debe ser TOTAL: si no, no es funtor y nada de lo demas aplica."""
        pi = construir_funtor(grafo)
        for s in grafo.skills:
            assert s.id in pi.en_objetos, f"{s.id} sin imagen"

    def test_los_sin_categoria_van_al_objeto_base(self, grafo):
        """Excluir los fundacionales dejaria pi parcial. Van a un objeto real."""
        pi = construir_funtor(grafo)
        assert pi("zfc") == OBJETO_BASE
        assert OBJETO_BASE in pi.codominio.objetos

    def test_los_intra_categoria_colapsan_a_identidad(self, grafo):
        """anillos -> cuerpos vive dentro de 'algebra': su imagen es id."""
        pi = construir_funtor(grafo)
        assert pi.colapsados >= 1
        assert ("algebra", "algebra") not in pi.codominio.morfismos

    def test_los_que_cruzan_inducen_morfismo(self, grafo):
        """Es justo lo que faltaba: los cruces ya tienen destino."""
        pi = construir_funtor(grafo)
        assert pi.codominio.hay_flecha("algebra", "geometry")
        assert pi.codominio.hay_flecha(OBJETO_BASE, "algebra")

    def test_translation_no_entra_en_el_orden(self, grafo):
        """
        TRANSLATION va de las ramas a `lean-tactics`, que no es una rama sino
        COMO se demuestra. Arrastrarla produce las mismas uniones espurias que
        ORDER_MORPHISMS existe para evitar.
        """
        grafo.add_morphism("variedades", "anillos", MorphismType.TRANSLATION)
        pi = construir_funtor(grafo, solo_jerarquia=True)
        assert not pi.codominio.hay_flecha("geometry", "algebra")


class TestLeyesDeFuntor:

    def test_es_funtor(self, grafo):
        r = verificar_functorialidad(construir_funtor(grafo), grafo)
        assert r["F1_identidades_ok"], "falla la ley de identidades"
        assert r["F2_composicion_ok"], "falla la ley de composicion"
        assert r["es_funtor"]

    def test_ningun_morfismo_se_queda_sin_imagen(self, grafo):
        r = verificar_functorialidad(construir_funtor(grafo), grafo)
        assert r["morfismos_con_imagen"] == r["morfismos_considerados"]

    def test_sobre_el_grafo_real(self):
        """La verificacion que importa: el grafo que el sistema usa de verdad."""
        import sys
        sys.argv = ["x"]
        from scripts.train_gnn_ppo import build_skill_graph
        g = build_skill_graph()
        r = verificar_functorialidad(construir_funtor(g), g)
        assert r["objetos_sin_imagen"] == 0
        assert r["F2_fallos"] == 0
        assert r["es_funtor"], f"pi no es funtor sobre el grafo real: {r}"


class TestPreservacion:
    """
    Un funtor preserva CO-CONOS siempre, y la MINIMALIDAD casi nunca. Son dos
    propiedades distintas y los tests las separan igual que el codigo, porque
    confundirlas es afirmar que un cociente conserva colimites.
    """

    def test_el_cocono_se_preserva(self, grafo):
        pi = construir_funtor(grafo)
        r = verificar_preservacion_colimites(
            pi, grafo, [(["anillos", "cuerpos"], "variedades")])
        assert r["cocono_preservado"] == 1

    def test_componentes_de_la_misma_categoria_colapsan(self, grafo):
        pi = construir_funtor(grafo)
        r = verificar_preservacion_colimites(
            pi, grafo, [(["anillos", "cuerpos"], "cuerpos")])
        assert r["colapsados_a_un_punto"] == 1

    def test_la_minimalidad_puede_perderse(self):
        """
        Contraparte del contraejemplo de Lean. Hacen falta DOS representantes
        de la misma categoria: uno abre en el codominio un atajo que en el
        dominio no existe, y con el se cuela una cota superior menor que la
        imagen del join.
        """
        g = SkillCategory()
        for sid, cat in [("a", "A"), ("a2", "A"), ("b", "B"),
                         ("j", "J"), ("m", "M")]:
            g.add_skill(_skill(sid, cat))
        g.add_morphism("a", "j", MorphismType.DEPENDENCY)
        g.add_morphism("b", "j", MorphismType.DEPENDENCY)
        g.add_morphism("a2", "m", MorphismType.DEPENDENCY)
        g.add_morphism("b", "m", MorphismType.DEPENDENCY)

        pi = construir_funtor(g)
        r = verificar_preservacion_colimites(pi, g, [(["a", "b"], "j")])
        assert r["cocono_preservado"] == 1, "el co-cono siempre sobrevive"
        assert r["colimite_preservado"] == 0, (
            "M es cota superior de {A,B} y J no la alcanza: la minimalidad "
            "se pierde, tal como demuestra functor_not_preserves_join"
        )
