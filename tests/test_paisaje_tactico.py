"""
Tests del paisaje tactico de CR_tac y del emparejamiento de skills.

CR_tac es el co-regulador que de hecho decide la accion de cada consulta. Su
paisaje se construia con `skill.level <= 1`, un corte de nivel arbitrario que
con 172 skills dejaba fuera 129 —los 34 de L2 y los 95 de L3—, y ademas
truncaba a 50. Un paisaje es "una vista PARCIAL que el co-regulador usa para
decidir" (Def. 2.13): lo que la hace parcial debe ser la RELEVANCIA a la
consulta, no la altura en la taxonomia.

Y habia una segunda causa, mas silenciosa: _match_graph_skills solo comparaba
con ids y nombres, que estan en ingles. Ninguna consulta en español activaba
nada, asi que el paisaje caia SIEMPRE al conjunto de respaldo.
"""
import pytest

from nucleo.types import Skill, MorphismType, PillarType
from nucleo.graph.category import SkillCategory
from nucleo.mes.co_regulators import TacticalCoRegulator


def _grafo() -> SkillCategory:
    """Grafo minimo con skills en los 4 niveles y keywords ES+EN."""
    g = SkillCategory()
    datos = [
        ("zfc-axioms", "ZFC Axioms", 0, ["zfc", "axiomas"]),
        ("module-theory", "Module Theory", 1, ["modulo", "modulos", "module"]),
        ("ring-theory", "Ring Theory", 1, ["anillo", "anillos", "ring"]),
        ("tensor-products", "Tensor Products", 2,
         ["producto tensorial", "tensor", "tensorial"]),
        ("exact-sequences", "Exact Sequences", 3,
         ["sucesion exacta", "sucesiones exactas", "exact sequence"]),
    ]
    for sid, nombre, lvl, kws in datos:
        g.add_skill(Skill(id=sid, name=nombre, level=lvl,
                          pillar=PillarType.SET,
                          metadata={"keywords": kws, "category": "algebra"}))
    g.add_morphism("module-theory", "tensor-products", MorphismType.DEPENDENCY)
    g.add_morphism("ring-theory", "module-theory", MorphismType.DEPENDENCY)
    return g


def _cr(g: SkillCategory) -> TacticalCoRegulator:
    cr = TacticalCoRegulator()
    cr._current_graph = g
    return cr


# ---------------------------------------------------------------------------
# Emparejamiento
# ---------------------------------------------------------------------------

class TestEmparejamiento:

    def test_consulta_en_espanol_activa_skills(self):
        """El caso que estaba roto: ids y nombres en ingles, consulta en español."""
        g = _grafo()
        cr = _cr(g)

        matched = cr._match_graph_skills("producto tensorial de modulos", g)

        assert "tensor-products" in matched, (
            "una consulta en español no activa el skill correspondiente: "
            "el emparejamiento no esta usando metadata['keywords']"
        )
        assert "module-theory" in matched

    def test_consulta_en_ingles_sigue_funcionando(self):
        g = _grafo()
        matched = _cr(g)._match_graph_skills("ring theory and modules", g)
        assert "ring-theory" in matched

    def test_no_empareja_subcadenas_sueltas(self):
        """'anillos' no debe activarse desde 'anilla' ni al reves."""
        g = _grafo()
        matched = _cr(g)._match_graph_skills("la anilla del mosqueton", g)
        assert "ring-theory" not in matched

    def test_sin_keywords_cae_a_tokens(self):
        g = SkillCategory()
        g.add_skill(Skill(id="galois-theory", name="Galois Theory", level=1))
        matched = _cr(g)._match_graph_skills("explica galois", g)
        assert "galois-theory" in matched


# ---------------------------------------------------------------------------
# Paisaje
# ---------------------------------------------------------------------------

class TestPaisajeTactico:

    def test_no_excluye_skills_por_nivel(self):
        """
        El paisaje debe poder contener skills de L2 y L3.

        Con `level <= 1` las sub-ramas —que son las que llevan las keywords en
        español— nunca entraban.
        """
        g = _grafo()
        cr = _cr(g)
        cr.classify_query("sucesiones exactas y producto tensorial", graph=g)

        ls = cr.build_landscape(g)
        niveles = {
            g.get_skill(s).level for s in ls.relevant_skills if g.get_skill(s)
        }

        assert "exact-sequences" in ls.relevant_skills   # L3
        assert "tensor-products" in ls.relevant_skills   # L2
        assert max(niveles) >= 2, f"el paisaje se quedo en niveles {niveles}"

    def test_metricas_cubren_todos_los_niveles(self):
        """Contar solo num_skills_0/1 reportaba como vacio un paisaje de L3."""
        g = _grafo()
        cr = _cr(g)
        cr.classify_query("sucesiones exactas", graph=g)

        m = cr.build_landscape(g).metrics

        assert "num_relevantes" in m
        assert "cobertura" in m
        assert any(k.startswith("num_skills_3") for k in m), (
            f"las metricas no reflejan el nivel 3: {sorted(m)}"
        )

    def test_incluye_vecinos_como_contexto(self):
        g = _grafo()
        cr = _cr(g)
        cr.classify_query("producto tensorial", graph=g)

        ls = cr.build_landscape(g)

        # tensor-products entra por keyword; module-theory es su vecino.
        assert "tensor-products" in ls.relevant_skills
        assert "module-theory" in ls.relevant_skills

    def test_sin_consulta_usa_los_fundacionales(self):
        g = _grafo()
        cr = _cr(g)
        cr._relevant_skills = []

        ls = cr.build_landscape(g)

        assert ls.relevant_skills == ["zfc-axioms"]

    def test_respeta_la_cota(self):
        g = SkillCategory()
        for i in range(200):
            g.add_skill(Skill(id=f"s{i}", name=f"Skill {i}", level=1,
                              metadata={"keywords": ["comun"]}))
        cr = _cr(g)
        cr.classify_query("tema comun", graph=g)

        ls = cr.build_landscape(g)

        assert len(ls.relevant_skills) <= cr._MAX_PAISAJE
