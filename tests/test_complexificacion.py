"""
Tests de la complexificacion de Ehresmann (paso K -> K').

QUE SE COMPRUEBA
----------------
Las cuatro propiedades que `Complexificacion.lean` demuestra, sobre el codigo
que las realiza:

  · eta_es_colimite            -> el hueco queda cerrado: eta(P) ES el colimite
  · eta_eq_iota_of_isLUB       -> lo que ya tenia colimite no recibe objeto nuevo
  · SC_homologos_mismo_colimite-> dos huecos con las mismas cotas comparten objeto
  · (preservacion, §9.4)       -> los colimites previos siguen siendolo, o se revierte

Y la terminacion, que es lo que hizo que se retirara la fabricacion de nodos en
su momento: complexificar es UN paso explicito, no un bucle.
"""
import pytest

from nucleo.types import Skill, MorphismType, PillarType
from nucleo.graph.category import SkillCategory
from nucleo.mes.patterns import PatternManager, ColimitBuilder
from nucleo.graph.complexity import (
    build_hierarchy_to_fixpoint, build_join_for_pattern,
    find_colimit, ConceptGap,
)
from nucleo.graph.complexificacion import complexificar, ObjetoEmergente


def _grafo(*ids: str) -> SkillCategory:
    g = SkillCategory(name="ComplTest")
    for sid in ids:
        g.add_skill(Skill(id=sid, name=sid, pillar=PillarType.SET, level=0))
    return g


def _dep(g, a, b):
    g.add_morphism(a, b, MorphismType.DEPENDENCY)


def _hueco(g, comps):
    """Construye el ConceptGap del patron, comprobando que de verdad lo es."""
    pm = PatternManager()
    cb = ColimitBuilder(pm)
    r = build_join_for_pattern(pm.create_pattern(list(comps), [], graph=g), g, cb)
    assert isinstance(r, ConceptGap), f"no es hueco: {r!r}"
    return pm, cb, r


# ---------------------------------------------------------------------------
# El hueco se cierra
# ---------------------------------------------------------------------------

class TestCierreDeHuecos:

    def test_hueco_con_dos_cotas_incomparables_se_cierra(self):
        """A,B ≤ X y A,B ≤ Y con X,Y incomparables: no hay minima en K.

        En K' se inserta eta(P) por debajo de ambas y por encima de A y B, y
        pasa a ser el colimite. Es `eta_es_colimite`.
        """
        g = _grafo("A", "B", "X", "Y")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        pm, cb, gap = _hueco(g, ["A", "B"])
        assert find_colimit(["A", "B"], g, cb) is None      # en K no hay

        r = complexificar(g, pm, cb, [gap])

        assert len(r.nuevos) == 1
        assert r.huecos_cerrados == 1
        nuevo = r.nuevos[0].skill_id
        assert find_colimit(["A", "B"], g, cb) == nuevo     # en K' si

    def test_el_objeto_nuevo_esta_entre_las_componentes_y_las_cotas(self):
        """Las aristas son las que hacen de eta(P) la MINIMA cota superior."""
        g = _grafo("A", "B", "X", "Y")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        pm, cb, gap = _hueco(g, ["A", "B"])

        nuevo = complexificar(g, pm, cb, [gap]).nuevos[0].skill_id
        ORD = SkillCategory.ORDER_MORPHISMS

        for c in ("A", "B"):
            assert g.is_preorder_leq(c, nuevo, ORD), "cota superior"
        for x in ("X", "Y"):
            assert g.is_preorder_leq(nuevo, x, ORD), "minimal entre las cotas"
        assert not g.is_preorder_leq("X", nuevo, ORD), "no puede estar por encima"

    def test_hueco_sin_cotas_no_se_cierra_en_un_paso(self):
        """Sin ninguna cota superior, eta(P) seria el maximo del grafo entero.

        Se deja abierto y se dice, en vez de colgar un nodo de todo.
        """
        g = _grafo("A", "B")
        pm, cb, gap = _hueco(g, ["A", "B"])
        assert gap.cocones == []

        r = complexificar(g, pm, cb, [gap])

        assert r.nuevos == []
        assert len(g.skills) == 2


# ---------------------------------------------------------------------------
# Preservacion
# ---------------------------------------------------------------------------

class TestPreservacion:

    def test_lo_que_ya_tenia_colimite_no_recibe_objeto_nuevo(self):
        """`eta_eq_iota_of_isLUB`: si P ya tenia join, no aparece nada."""
        g = _grafo("A", "B", "C")
        _dep(g, "A", "C"); _dep(g, "B", "C")
        pm = PatternManager(); cb = ColimitBuilder(pm)
        cn, gaps = build_hierarchy_to_fixpoint(g, pm, cb)
        assert find_colimit(["A", "B"], g, cb) == "C"

        antes = len(g.skills)
        r = complexificar(g, pm, cb, gaps)

        assert r.nuevos == []
        assert len(g.skills) == antes

    def test_los_colimites_previos_se_reverifican(self):
        """La insercion puede quitarle minimalidad a otro colimite (§9.4)."""
        g = _grafo("A", "B", "X", "Y", "P", "Q", "R")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        _dep(g, "P", "R"); _dep(g, "Q", "R")
        pm = PatternManager(); cb = ColimitBuilder(pm)
        cn, gaps = build_hierarchy_to_fixpoint(g, pm, cb)

        r = complexificar(g, pm, cb, gaps)

        # R sigue siendo el join de {P,Q}: la insercion no lo toca
        assert "R" in r.colimites_preservados
        assert r.colimites_rotos == []
        assert r.preserva

    def test_preservar_revierte_el_paso_entero(self):
        """Con preservar=True un colimite roto deja el grafo intacto."""
        g = _grafo("A", "B", "X", "Y")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        pm, cb, gap = _hueco(g, ["A", "B"])

        # Se falsea un colimite previo que la insercion va a romper: se declara
        # que X es el join de {A,B}, cosa que dejara de ser cierta en cuanto
        # eta(P) se meta por debajo.
        pat = pm.create_pattern(["A", "B"], [], graph=g)
        cb._register_existing_join(pat, "X", g)

        antes_skills = len(g.skills)
        antes_morf = len(g.morphisms)
        r = complexificar(g, pm, cb, [gap], preservar=True)

        assert r.revertida
        assert r.nuevos == []
        assert len(g.skills) == antes_skills
        assert len(g.morphisms) == antes_morf

    def test_sin_preservar_se_aplica_y_se_reporta(self):
        g = _grafo("A", "B", "X", "Y")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        pm, cb, gap = _hueco(g, ["A", "B"])
        pat = pm.create_pattern(["A", "B"], [], graph=g)
        cb._register_existing_join(pat, "X", g)

        r = complexificar(g, pm, cb, [gap], preservar=False)

        assert not r.revertida
        assert len(r.nuevos) == 1
        assert "X" in r.colimites_rotos


# ---------------------------------------------------------------------------
# Condicion suplementaria (SC)
# ---------------------------------------------------------------------------

class TestCondicionSuplementaria:

    def test_dos_huecos_con_las_mismas_cotas_comparten_objeto(self):
        """`SC_homologos_mismo_colimite`, en el codigo.

        El id del objeto se deriva del CONJUNTO DE COTAS, no de las
        componentes. Si dependiera de las componentes, dos patrones homologos
        recibirian objetos distintos — la deficiencia (b) de §3.2.
        """
        g = _grafo("A", "B", "C", "D", "X", "Y")
        for s in ("A", "B", "C", "D"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        pm = PatternManager(); cb = ColimitBuilder(pm)
        g1 = build_join_for_pattern(pm.create_pattern(["A", "B"], [], graph=g), g, cb)
        g2 = build_join_for_pattern(pm.create_pattern(["C", "D"], [], graph=g), g, cb)
        assert isinstance(g1, ConceptGap) and isinstance(g2, ConceptGap)
        assert set(g1.cocones) == set(g2.cocones)

        r = complexificar(g, pm, cb, [g1, g2])

        assert len(r.nuevos) == 1, "homologos deben compartir el colimite"
        assert set(r.nuevos[0].component_ids) == {"A", "B", "C", "D"}

    def test_huecos_con_cotas_distintas_reciben_objetos_distintos(self):
        g = _grafo("A", "B", "C", "D", "X", "Y", "Z", "W")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        for s in ("C", "D"):
            _dep(g, s, "Z"); _dep(g, s, "W")
        pm = PatternManager(); cb = ColimitBuilder(pm)
        g1 = build_join_for_pattern(pm.create_pattern(["A", "B"], [], graph=g), g, cb)
        g2 = build_join_for_pattern(pm.create_pattern(["C", "D"], [], graph=g), g, cb)

        r = complexificar(g, pm, cb, [g1, g2])

        assert len(r.nuevos) == 2
        assert r.nuevos[0].skill_id != r.nuevos[1].skill_id


# ---------------------------------------------------------------------------
# Terminacion
# ---------------------------------------------------------------------------

class TestTerminacion:

    def test_complexificar_es_un_paso_no_un_bucle(self):
        """La razon por la que se retiro la fabricacion de nodos era que cada
        nodo nuevo era un punto de convergencia nuevo y el bucle crecia. Aqui
        no hay bucle: se añade un objeto por clase de huecos y se para.
        """
        g = _grafo("A", "B", "X", "Y")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        pm, cb, gap = _hueco(g, ["A", "B"])

        r = complexificar(g, pm, cb, [gap])
        assert len(g.skills) == 5

        # repetirlo con los MISMOS huecos no vuelve a crecer: el objeto ya existe
        r2 = complexificar(g, pm, cb, [gap])
        assert len(g.skills) == 5

    def test_el_objeto_nuevo_no_entra_en_cn_como_componente_de_si_mismo(self):
        """La aciclicidad se mantiene tras complexificar."""
        g = _grafo("A", "B", "X", "Y")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        pm, cb, gap = _hueco(g, ["A", "B"])
        complexificar(g, pm, cb, [gap])

        pm2 = PatternManager(); cb2 = ColimitBuilder(pm2)
        build_hierarchy_to_fixpoint(g, pm2, cb2)

        for col in cb2.all_colimits:
            pat = pm2.get_pattern(col.pattern_id)
            if pat:
                assert col.skill_id not in pat.component_ids
