"""
Lo que solo aparece al ARRANCAR el sistema, no al probar sus piezas.

Los dos defectos que fija este archivo pasaron desapercibidos a 681 tests que
verificaban cada modulo por separado. Salieron de encender el sistema entero y
mirar dos cosas: cuantos nodos tiene el grafo antes y despues de tres
consultas, y que responde el clasificador a «¿cuanto es 2 + 2?».
"""
import logging
import sys

import pytest

logging.disable(logging.CRITICAL)


@pytest.fixture(scope="module")
def nucleo_frio():
    """Un Nucleo sin inicializar: basta para los metodos puros."""
    sys.argv = ["x"]
    from nucleo.core import Nucleo
    return Nucleo.__new__(Nucleo)


# ---------------------------------------------------------------------------
# El clasificador no reconocia la aritmetica
# ---------------------------------------------------------------------------

class TestClasificadorMatematico:
    """`_is_mathematical` solo miraba VOCABULARIO.

    Keywords, simbolos Unicode y LaTeX. Ninguna regla para la FORMA, asi que
    «¿cuanto es 2 + 2?» salia NO matematico y se iba a la rama conversacional
    saltandose Lean — que es justo el caso para el que existe el pipeline.
    """

    MATEMATICAS = [
        "¿Cuánto es 2 + 2?", "2+2", "cuanto es 15 por 4",
        "resuelve x^2 - 4 = 0", "calcula 3.5 / 7", "x = 5", "2x + 1 = 0",
        "20 entre 5", "7 mas 3", "n^k", "el 20% de 300", "f(x) = x^2",
        "demuestra que a <= b", "raiz cuadrada de 144",
        "demuestra que raiz de 2 es irracional", "¿Qué es un grupo abeliano?",
    ]

    #: Un digito suelto NO basta, y es deliberado: exigir un operador entre
    #: operandos es lo que impide que «tengo 2 gatos» entre al pipeline.
    NO_MATEMATICAS = [
        "Hola, ¿qué tal estás?", "buenos días", "gracias por todo",
        "¿quién eres?", "tengo 2 gatos", "quedamos a las 3", "adios",
        "hello there", "me llamo Leonardo", "cuéntame un chiste",
        "¿qué tiempo hace?",
    ]

    @pytest.mark.parametrize("q", MATEMATICAS)
    def test_reconoce_la_matematica(self, nucleo_frio, q):
        from nucleo.core import Nucleo
        assert Nucleo._is_mathematical(nucleo_frio, q), (
            f"«{q}» no llega a Lean: se va a la rama conversacional"
        )

    @pytest.mark.parametrize("q", NO_MATEMATICAS)
    def test_no_manda_a_lean_lo_que_no_es(self, nucleo_frio, q):
        from nucleo.core import Nucleo
        assert not Nucleo._is_mathematical(nucleo_frio, q), (
            f"«{q}» acabaría formalizándose en Lean: una llamada al LLM y una "
            "ejecución de Lean tiradas para devolver un sinsentido"
        )

    def test_un_numero_suelto_no_basta(self, nucleo_frio):
        """La propiedad que hace segura la regla de formas."""
        from nucleo.core import Nucleo
        for q in ["tengo 2 gatos", "capitulo 7", "son las 5", "vivo en el 3"]:
            assert not Nucleo._is_mathematical(nucleo_frio, q)


# ---------------------------------------------------------------------------
# El grafo crecia durante las consultas
# ---------------------------------------------------------------------------

class TestElGrafoNoCreceAlUsarlo:
    """`apply_option` fabricaba un vertice por cada patron que un co-regulador
    propusiera ligar.

    Es el camino que `build_join_for_pattern` habia retirado por principio
    —inventar un nodo y cablearlo hasta que cumpla la propiedad universal es
    asumir la conclusion— entrando por el lado de los co-reguladores. Medido:
    tres consultas cualesquiera llevaban el grafo de 173 a 175 nodos.
    """

    def test_apply_option_descubre_no_fabrica(self):
        import inspect
        from nucleo.graph import evolution
        fuente = inspect.getsource(evolution.EvolutionarySystem.apply_option)
        assert "find_colimit_cong" in fuente, (
            "apply_option dejó de descubrir el colímite"
        )
        assert "build_colimit(" not in fuente, (
            "apply_option volvió a fabricar vértices"
        )

    def test_ligar_un_patron_sin_colimite_no_inventa_nada(self):
        """El caso que producía los `skill_<uuid>`: un patrón sin co-cono
        límite. Antes se le fabricaba uno; ahora se deja como hueco."""
        sys.argv = ["x"]
        from nucleo.graph.category import SkillCategory
        from nucleo.graph.evolution import EvolutionarySystem
        from nucleo.mes.patterns import PatternManager, ColimitBuilder
        from nucleo.types import Skill, PillarType, MorphismType, Option

        g = SkillCategory(name="Sin")
        for i in "abxy":
            g.add_skill(Skill(id=i, name=i, pillar=PillarType.SET, level=0))
        # a y b tienen DOS cotas superiores incomparables: no hay mínima
        for c in "ab":
            for t in "xy":
                g.add_morphism(c, t, MorphismType.DEPENDENCY)

        pm = PatternManager()
        cb = ColimitBuilder(pm)
        p = pm.create_pattern(["a", "b"], [], graph=g)
        ev = EvolutionarySystem(g, pm, colimit_builder=cb)

        antes = set(g.skill_ids)
        ev.apply_option(Option(bindings=[p.id]))
        assert set(g.skill_ids) == antes, (
            f"se fabricaron {sorted(set(g.skill_ids) - antes)}: el patrón no "
            "tiene co-cono límite y eso es un hueco, no un fallo"
        )
        assert not cb.has_colimit(p.id)


# ---------------------------------------------------------------------------
# La multiplicidad certificada no llegaba al runtime
# ---------------------------------------------------------------------------

class TestLoCertificadoLlegaAlRuntime:
    """Los seis morfismos que Lean demostro distintos vivian solo en los tests.

    `registrar_morfismos_certificados` no lo llamaba nadie en `core.py`, asi
    que el grafo del runtime era mas delgado que el que se estaba midiendo:
    3 pares con |Hom| > 1 en vez de 5.
    """

    def test_core_registra_los_certificados(self):
        import inspect
        from nucleo.core import Nucleo
        fuente = inspect.getsource(Nucleo._load_foundational_skills)
        assert "registrar_morfismos_certificados" in fuente, (
            "el runtime volvió a quedarse sin la multiplicidad que Lean "
            "certificó: es justo la que costó demostrar"
        )
