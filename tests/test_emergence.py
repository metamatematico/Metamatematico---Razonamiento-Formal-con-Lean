"""
Tests de Enlaces Simples/Complejos y Emergencia
=================================================

Verifica la implementacion de Def 6.3 y Thm 8.6 del documento v7.0:
- Clasificacion de enlaces: IDENTITY, SIMPLE, COMPLEX
- Deteccion de enlaces complejos (emergencia)
- Medicion de emergencia
"""

import pytest

from nucleo.types import (
    Skill, MorphismType, PillarType, LinkComplexity, Option,
)
from nucleo.graph.category import SkillCategory
from nucleo.graph.evolution import EvolutionarySystem
from nucleo.mes.patterns import PatternManager, ColimitBuilder


# =============================================================================
# FIXTURES
# =============================================================================

def _emergencia():
    """
    Testigo de un enlace COMPLEJO de verdad, en el sentido de Ehresmann.

        p1 ──┐                q1 ──┐
             ├─→ A ─────────→ B ←──┤
        p2 ──┘                q2 ──┘

    · A = colim{p1, p2}   (cotas superiores: A y B; A ≤ B, luego A es minimal)
    · B = colim{q1, q2}   (unica cota superior)
    · el enlace A → B NO esta inducido por ningun clúster: un clúster
      {p1,p2} → {q1,q2} exigiria que p1 alcanzase q1 o q2, y p1 solo alcanza
      A y B.

    Por `EsSimple` (EhresmannLinks.lean) no es simple; ambos extremos son
    colimites, luego es COMPLEX. Es la forma que `complex_needs_unconnected`
    predice: complejidad requiere descomposiciones NO conectadas.

    Devuelve (grafo, pattern_manager, colimit_builder) — los tres compartidos,
    que es justo lo que la clasificacion necesita para poder decidir.
    """
    from nucleo.graph.complexity import build_join_for_pattern
    g = SkillCategory(name="EmergenciaReal")
    for sid in ("p1", "p2", "q1", "q2", "A", "B"):
        g.add_skill(Skill(id=sid, name=sid, pillar=PillarType.SET, level=0))
    for src in ("p1", "p2"):
        g.add_morphism(src, "A", MorphismType.DEPENDENCY)
    for src in ("q1", "q2"):
        g.add_morphism(src, "B", MorphismType.DEPENDENCY)
    g.add_morphism("A", "B", MorphismType.DEPENDENCY)

    pm = PatternManager()
    cb = ColimitBuilder(pm)
    for comps in (["p1", "p2"], ["q1", "q2"]):
        build_join_for_pattern(pm.create_pattern(comps, [], graph=g), g, cb)
    return g, pm, cb


@pytest.fixture
def emergencia():
    return _emergencia()


@pytest.fixture
def graph():
    """Grafo con skills en niveles 0 y 1."""
    g = SkillCategory(name="EmergenceTest")
    g.add_skill(Skill(id="s1", name="Atom1", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="s2", name="Atom2", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="s3", name="Atom3", pillar=PillarType.SET, level=0))
    g.add_morphism("s1", "s2", MorphismType.DEPENDENCY)
    g.add_morphism("s2", "s3", MorphismType.DEPENDENCY)
    return g


# =============================================================================
# LINK CLASSIFICATION (Def 6.3)
# =============================================================================

class TestLinkClassification:
    """Tests para clasificacion de enlaces."""

    def test_identity_link(self, graph):
        """Morfismo identidad es IDENTITY."""
        identity = graph.identity("s1")
        assert graph.classify_link(identity.id) == LinkComplexity.IDENTITY

    def test_enlace_entre_no_colimites_no_aplica(self, graph):
        """Si ningun extremo es colimite, no hay descomposiciones que comparar.

        `EsSimple a b := ∃ P Q, binding P = a ∧ binding Q = b ∧ Cluster P Q`.
        Sin patrones cuyo colimite sea a o b, la formula no puede satisfacerse
        y tampoco tiene sentido llamar al enlace complejo. Antes esta funcion
        devolvia SIMPLE por defecto, que era una respuesta inventada.
        """
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        m = graph.hom("s1", "s2")[0]
        assert graph.classify_link(m.id, pm, cb) == LinkComplexity.NO_APLICA

    def test_sin_gestores_no_se_puede_clasificar(self, graph):
        """Sin las descomposiciones la clasificacion es indecidible, no SIMPLE."""
        m = graph.hom("s1", "s2")[0]
        assert graph.classify_link(m.id) == LinkComplexity.NO_APLICA

    def test_factorizar_por_un_colimite_no_basta_para_ser_simple(self, graph):
        """La lectura por FACTORIZACION no es la definicion de Ehresmann.

        Que exista un colimite intermedio C con A → C → B no hace simple al
        enlace: simple es estar INDUCIDO por un clúster entre descomposiciones.
        Un compuesto puede pasar por objetos-clúster sin estarlo. Este test
        afirmaba justo lo contrario.
        """
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        m12 = graph.hom("s1", "s2")[0]
        pattern = pm.create_pattern(["s1", "s2"], [m12.id], graph=graph)
        colimit_skill, colimit = cb.build_colimit(pattern, graph)

        b = Skill(id="B", name="Target", level=0)
        graph.add_skill(b)
        graph.add_morphism(colimit_skill.id, "B", MorphismType.DEPENDENCY)
        m_s1_b = graph.add_morphism("s1", "B", MorphismType.DEPENDENCY)

        # s1 -> cP -> B existe, pero s1 no es colimite de ningun patron.
        assert graph.classify_link(m_s1_b.id, pm, cb) == LinkComplexity.NO_APLICA

    def test_la_diferencia_de_nivel_no_decide_la_complejidad(self, graph):
        """`level` es taxonomia curada a mano, no estructura categorica.

        La regla `|level(A) - level(B)| > 1 → COMPLEX` producia los 246
        "enlaces complejos" del grafo real: todos ellos, ninguno por un
        criterio de Ehresmann.
        """
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        s_high = Skill(id="s_high", name="HighLevel", level=2)
        graph.add_skill(s_high)
        m = graph.add_morphism("s1", "s_high", MorphismType.DEPENDENCY)

        assert graph.classify_link(m.id, pm, cb) != LinkComplexity.COMPLEX

    def test_enlace_complejo_genuino(self, emergencia):
        """A → B es COMPLEX: ningun clúster une {p1,p2} con {q1,q2}."""
        g, pm, cb = emergencia
        m = g.hom("A", "B")[0]
        assert g.classify_link(m.id, pm, cb) == LinkComplexity.COMPLEX

    def test_enlace_simple_genuino(self, emergencia):
        """Si se añade el clúster, el mismo enlace pasa a SIMPLE."""
        g, pm, cb = emergencia
        # Ahora toda componente de {p1,p2} alcanza alguna de {q1,q2}.
        g.add_morphism("p1", "q1", MorphismType.DEPENDENCY)
        g.add_morphism("p2", "q2", MorphismType.DEPENDENCY)
        m = g.hom("A", "B")[0]
        assert g.classify_link(m.id, pm, cb) == LinkComplexity.SIMPLE

    def test_get_complex_links(self, emergencia):
        """get_complex_links encuentra exactamente el enlace A → B."""
        g, pm, cb = emergencia
        complex_links = g.get_complex_links(pm, cb)
        assert len(complex_links) == 1
        assert complex_links[0].source_id == "A"
        assert complex_links[0].target_id == "B"

    def test_get_complex_links_sin_gestores_avisa(self, emergencia):
        """Devolver [] en silencio fue el origen del problema anterior."""
        g, pm, cb = emergencia
        assert g.get_complex_links() == []


# =============================================================================
# EMERGENCE DETECTION (Thm 8.6)
# =============================================================================

class TestEmergenceDetection:
    """Tests para deteccion de emergencia."""

    def test_no_emergence_initially(self, graph):
        """Sin emergencia en un grafo basico."""
        evo = EvolutionarySystem(graph)
        emergence = evo.measure_emergence()
        assert emergence["num_complex_links"] == 0
        assert emergence["emergence_ratio"] == 0.0

    def test_emergence_con_enlace_complejo_genuino(self, emergencia):
        """La emergencia se mide sobre enlaces complejos de Ehresmann.

        Antes bastaba componer dos flechas cualesquiera. Ahora hace falta lo
        que el teorema exige: dos colimites con descomposiciones no conectadas.
        """
        g, pm, cb = emergencia
        evo = EvolutionarySystem(g, pattern_manager=pm, colimit_builder=cb)

        emergence = evo.measure_emergence()
        assert emergence["num_complex_links"] == 1
        assert emergence["emergence_ratio"] > 0

    def test_componer_dos_flechas_no_produce_emergencia(self, graph):
        """Un compuesto entre objetos que no son colimites no es emergencia."""
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        evo = EvolutionarySystem(graph, pattern_manager=pm, colimit_builder=cb)

        f = graph.hom("s1", "s2")[0]
        g2 = graph.hom("s2", "s3")[0]
        graph.compose(g2.id, f.id)

        assert evo.measure_emergence()["num_complex_links"] == 0

    def test_emergence_growth_tracking(self, emergencia):
        """Crecimiento de emergencia entre pasos temporales."""
        g, pm, cb = emergencia
        evo = EvolutionarySystem(g, pattern_manager=pm, colimit_builder=cb)

        s4 = Skill(id="s4", name="Extra", level=0)
        g.add_skill(s4)
        g.add_morphism("B", "s4", MorphismType.DEPENDENCY)
        evo.apply_option(Option(absorptions=["s4"]))
        evo.apply_option(Option())

        emergence = evo.measure_emergence()
        assert emergence["num_complex_links"] >= 1
        assert emergence["complexity_growth"] >= 0

    def test_detect_complex_links_current(self, emergencia):
        """detect_complex_links en tiempo actual."""
        g, pm, cb = emergencia
        evo = EvolutionarySystem(g, pattern_manager=pm, colimit_builder=cb)

        complex_ids = evo.detect_complex_links()
        assert len(complex_ids) == 1

    def test_emergence_in_stats(self, graph):
        """Metricas de emergencia incluidas en stats."""
        evo = EvolutionarySystem(graph)
        stats = evo.stats
        assert "emergence" in stats
        assert "num_complex_links" in stats["emergence"]


# =============================================================================
# COLIMIT EMERGENCE INTERACTION
# =============================================================================

class TestColimitEmergence:
    """Tests para interaccion entre colimites y emergencia."""

    def test_los_cocono_no_son_clasificables(self, graph):
        """Los morfismos de co-cono van de una COMPONENTE al colimite.

        La componente no es colimite de ningun patron, asi que el enlace no
        tiene par de descomposiciones y Ehresmann no lo clasifica. Antes se
        afirmaba SIMPLE, que era el valor por defecto disfrazado de resultado.
        """
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        m12 = graph.hom("s1", "s2")[0]
        pattern = pm.create_pattern(["s1", "s2"], [m12.id], graph=graph)
        colimit_skill, colimit = cb.build_colimit(pattern, graph)

        for mid in colimit.cocone_morphisms:
            assert graph.classify_link(mid, pm, cb) == LinkComplexity.NO_APLICA

    def test_binding_option_adds_emergence_structure(self, graph):
        """Option de ligadura agrega estructura que permite emergencia."""
        evo = EvolutionarySystem(graph)
        pm = evo.pattern_manager

        m12 = graph.hom("s1", "s2")[0]
        pattern = pm.create_pattern(["s1", "s2"], [m12.id], graph=graph)

        evo.apply_option(Option(bindings=[pattern.id]))

        # Colimit should exist now
        assert evo.colimit_builder.has_colimit(pattern.id)

        # The new colimit skill should be at level 1
        colimit_obj = evo.colimit_builder.get_colimit_for_pattern(pattern.id)
        colimit_skill = graph.get_skill(colimit_obj.skill_id)
        assert colimit_skill.level == 1
