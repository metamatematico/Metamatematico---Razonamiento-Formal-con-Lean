"""
Tests for the emergent complexity order (cn) hierarchy.

Verifies that:
  - cn(X) = 0 for atomic skills (no colimit registration)
  - cn(X) = k+1 for join-skills whose components have max cn = k
  - Stacked joins produce cn = 2
  - build_hierarchy_to_fixpoint updates graph skill levels correctly
  - find_existing_join correctly identifies the join in simple preorders
  - No join is found when the graph has no upper bounds
"""
import pytest

from nucleo.types import Skill, Colimit, MorphismType, PillarType
from nucleo.graph.category import SkillCategory
from nucleo.mes.patterns import PatternManager, ColimitBuilder
from nucleo.graph.complexity import (
    compute_complexity_order,
    find_existing_join,
    build_join_for_pattern,
    build_hierarchy_to_fixpoint,
    find_cocones,
    find_colimit,
    ConceptGap,
    TrivialColimit,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _graph(*skill_ids: str) -> SkillCategory:
    g = SkillCategory()
    for sid in skill_ids:
        g.add_skill(Skill(id=sid, name=sid, pillar=PillarType.SET, level=0))
    return g


def _pm_cb(graph: SkillCategory):
    pm = PatternManager()
    cb = ColimitBuilder(pm)
    return pm, cb


def _register_colimit(cb: ColimitBuilder, pm: PatternManager,
                      comp_ids: list[str], join_id: str) -> Colimit:
    """Helper: register a colimit without graph verification."""
    pattern = pm.create_pattern(comp_ids, [])
    col = Colimit(pattern_id=pattern.id, skill_id=join_id)
    cb._colimits[col.id] = col
    cb._pattern_to_colimit[pattern.id] = col.id
    return col


# ---------------------------------------------------------------------------
# TestComputeComplexityOrder
# ---------------------------------------------------------------------------

class TestComputeComplexityOrder:
    def test_no_colimits_all_zero(self):
        g = _graph("A", "B", "C")
        pm, cb = _pm_cb(g)
        cn = compute_complexity_order(g, cb)
        assert all(v == 0 for v in cn.values())

    def test_cn_one_for_direct_join(self):
        g = _graph("A", "B", "C")
        pm, cb = _pm_cb(g)
        _register_colimit(cb, pm, ["A", "B"], "C")
        cn = compute_complexity_order(g, cb)
        assert cn["C"] == 1
        assert cn["A"] == 0
        assert cn["B"] == 0

    def test_cn_two_for_stacked_join(self):
        # A, B → C (cn=1);  C, A → D (cn=2)
        g = _graph("A", "B", "C", "D")
        pm, cb = _pm_cb(g)
        _register_colimit(cb, pm, ["A", "B"], "C")
        _register_colimit(cb, pm, ["C", "A"], "D")
        cn = compute_complexity_order(g, cb)
        assert cn["C"] == 1
        assert cn["D"] == 2

    def test_fixpoint_idempotent(self):
        g = _graph("A", "B", "C")
        pm, cb = _pm_cb(g)
        _register_colimit(cb, pm, ["A", "B"], "C")
        cn1 = compute_complexity_order(g, cb)
        cn2 = compute_complexity_order(g, cb)
        assert cn1 == cn2

    def test_missing_skill_in_graph_ignored(self):
        g = _graph("A", "B")
        pm, cb = _pm_cb(g)
        # Register colimit for skill "C" that is NOT in the graph
        _register_colimit(cb, pm, ["A", "B"], "C")
        cn = compute_complexity_order(g, cb)
        # "C" gets added to cn but with value 1; no crash
        assert cn.get("C", -1) == 1


# ---------------------------------------------------------------------------
# TestFindExistingJoin
# ---------------------------------------------------------------------------

class TestFindExistingJoin:
    def test_finds_sole_upper_bound(self):
        # A → C, B → C — C is the only upper bound, so it is the join
        g = _graph("A", "B", "C")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        join_id = find_existing_join(["A", "B"], g, cb)
        assert join_id == "C"

    def test_returns_none_when_no_upper_bound(self):
        # No morphisms → no upper bound
        g = _graph("A", "B")
        pm, cb = _pm_cb(g)
        join_id = find_existing_join(["A", "B"], g, cb)
        assert join_id is None

    def test_returns_minimal_upper_bound(self):
        # A → C, B → C, C → D: C is minimal upper bound, D is not
        g = _graph("A", "B", "C", "D")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        g.add_morphism("C", "D", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        join_id = find_existing_join(["A", "B"], g, cb)
        # D is also above A and B (via C), but C ≤ D so D is not minimal
        assert join_id == "C"

    def test_componente_dominante_es_el_colimite(self):
        """Si una componente domina a las demas, ELLA es el colimite.

        Este test afirmaba lo contrario —`assert join_id is None`— con el
        comentario "B is a component, excluded". Codificaba una desviacion de
        la definicion: `isCocone` (ColimitVerifier.lean) no excluye nada y
        `reachable_refl` hace que toda componente sea cota superior de si
        misma. El testigo formal es literalmente este grafo:

            componente_puede_ser_colimite :
              isColimitInFiniteCategory testigoDominante [0, 1] 1 = true

        con `testigoDominante` = la unica arista `0 → 1`. Aqui: A → B, y el
        colimite de {A, B} es B.
        """
        g = _graph("A", "B", "C")
        g.add_morphism("A", "B", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        join_id = find_existing_join(["A", "B"], g, cb)
        assert join_id == "B"

    def test_find_cocones_incluye_las_componentes(self):
        """`isCocone` es reflexiva y no excluye el diagrama."""
        g = _graph("A", "B")
        g.add_morphism("A", "B", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        # B es cota superior de A (arista) y de si mismo (reflexividad).
        assert find_cocones(["A", "B"], g) == ["B"]

    def test_is_join_y_find_colimit_coinciden(self):
        """Las dos rutas del repo no pueden discrepar sobre el mismo patron.

        Antes: is_join(B, [A,B]) = True mientras find_colimit([A,B]) = None.
        """
        g = _graph("A", "B")
        g.add_morphism("A", "B", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        assert cb.is_join("B", ["A", "B"], g)["is_join"] is True
        assert find_colimit(["A", "B"], g, cb) == "B"


# ---------------------------------------------------------------------------
# TestBuildJoinForPattern
# ---------------------------------------------------------------------------

class TestBuildJoinForPattern:
    def test_uses_existing_join(self):
        g = _graph("A", "B", "C")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        pattern = pm.create_pattern(["A", "B"], [], graph=g)
        result = build_join_for_pattern(pattern, g, cb)
        assert result is not None
        assert result.skill_id == "C"
        # No new skills added
        assert len(g.skills) == 3

    def test_sin_colimite_no_fabrica_vertice(self):
        """A y B sin cota superior: se emite ConceptGap, NO se inventa un nodo.

        Fabricar el vertice y cablearlo para que cumpla la propiedad universal
        es asumir la conclusion, y era la causa de la no-terminacion.
        """
        g = _graph("A", "B")
        pm, cb = _pm_cb(g)
        pattern = pm.create_pattern(["A", "B"], [], graph=g)

        result = build_join_for_pattern(pattern, g, cb)

        assert isinstance(result, ConceptGap)
        assert len(g.skills) == 2          # el grafo NO crecio
        assert result.cocones == []        # ni siquiera hay co-conos
        assert set(result.component_ids) == {"A", "B"}

    def test_cocones_sin_minimal_dan_gap(self):
        """Con co-conos pero ninguno minimal: ConceptGap que los reporta."""
        # A,B ≤ X y A,B ≤ Y, con X e Y incomparables → no hay minimo
        g = _graph("A", "B", "X", "Y")
        for src in ("A", "B"):
            g.add_morphism(src, "X", MorphismType.DEPENDENCY)
            g.add_morphism(src, "Y", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        pattern = pm.create_pattern(["A", "B"], [], graph=g)

        result = build_join_for_pattern(pattern, g, cb)

        assert isinstance(result, ConceptGap)
        assert len(g.skills) == 4                   # nada fabricado
        assert set(result.cocones) == {"X", "Y"}    # los co-conos SI se reportan
        assert result.n_cocones == 2

    def test_idempotent_on_second_call(self):
        """Descubrir el colimite dos veces da el mismo, sin duplicar skills."""
        g = _graph("A", "B", "C")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        pattern = pm.create_pattern(["A", "B"], [], graph=g)

        r1 = build_join_for_pattern(pattern, g, cb)
        r2 = build_join_for_pattern(pattern, g, cb)

        assert r1.skill_id == r2.skill_id == "C"
        assert len(g.skills) == 3

    def test_gap_es_idempotente_y_no_muta(self):
        """Repetir sobre un patron sin colimite nunca hace crecer el grafo."""
        g = _graph("A", "B")
        pm, cb = _pm_cb(g)
        pattern = pm.create_pattern(["A", "B"], [], graph=g)

        for _ in range(5):
            r = build_join_for_pattern(pattern, g, cb)
            assert isinstance(r, ConceptGap)
        assert len(g.skills) == 2

    def test_single_component_returns_none(self):
        g = _graph("A")
        pm, cb = _pm_cb(g)
        pattern = pm.create_pattern(["A"], [])
        result = build_join_for_pattern(pattern, g, cb)
        assert result is None

    def test_colimite_que_es_componente_no_es_hueco(self):
        """El colimite existe: no puede archivarse como hueco conceptual.

        Era el caso de 14 de los 27 huecos medidos sobre el grafo real, y
        `llenar_hueco_conceptual` pedia al LLM el concepto unificador de
        patrones que ya lo contenian entre sus componentes.
        """
        g = _graph("A", "B")
        g.add_morphism("A", "B", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        pattern = pm.create_pattern(["A", "B"], [], graph=g)

        result = build_join_for_pattern(pattern, g, cb)

        assert isinstance(result, TrivialColimit)
        assert not isinstance(result, ConceptGap)
        assert result.colimit_id == "B"
        assert result.colimit_id in result.component_ids
        assert len(g.skills) == 2          # no se fabrico nada

    def test_trivial_no_se_registra_como_descomposicion(self):
        """Registrarlo romperia `AciclicoMulti` y con ella la terminacion de cn.

        `join_propio_rompe_aciclicidad` (ComplexityOrder.lean): si una
        descomposicion de x contiene a x, la aciclicidad falla. Y
        `autoJoin_sin_punto_fijo` exhibe la divergencia concreta.
        """
        g = _graph("A", "B")
        g.add_morphism("A", "B", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        pattern = pm.create_pattern(["A", "B"], [], graph=g)

        build_join_for_pattern(pattern, g, cb)

        assert cb.get_colimit_for_pattern(pattern.id) is None
        cn = compute_complexity_order(g, cb)
        assert cn["B"] == 0, "un colimite trivial no aporta nivel"
        assert cn["A"] == 0

    def test_trivial_es_idempotente(self):
        g = _graph("A", "B")
        g.add_morphism("A", "B", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        pattern = pm.create_pattern(["A", "B"], [], graph=g)
        for _ in range(5):
            r = build_join_for_pattern(pattern, g, cb)
            assert isinstance(r, TrivialColimit)
        assert len(g.skills) == 2


# ---------------------------------------------------------------------------
# TestBuildHierarchyToFixpoint
# ---------------------------------------------------------------------------

class TestBuildHierarchyToFixpoint:
    def test_atomic_graph_all_cn_zero(self):
        g = _graph("A", "B")
        pm, cb = _pm_cb(g)
        cn, gaps = build_hierarchy_to_fixpoint(g, pm, cb, max_iterations=3)
        assert cn["A"] == 0
        assert cn["B"] == 0

    def test_levels_emerge_from_morphisms(self):
        # A → C, B → C, C → D
        g = _graph("A", "B", "C", "D")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        g.add_morphism("C", "D", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        cn, gaps = build_hierarchy_to_fixpoint(g, pm, cb, max_iterations=5)
        assert cn["A"] == 0
        assert cn["B"] == 0
        assert cn["C"] >= 1   # C is above A and B
        # D is above C, so cn(D) >= cn(C) + 1 if D is registered as join
        # (D might or might not be a join depending on pattern detection)

    def test_skill_levels_updated_in_graph(self):
        g = _graph("A", "B", "C")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        nivel_antes = g.get_skill("C").level
        build_hierarchy_to_fixpoint(g, pm, cb, max_iterations=3)
        c_skill = g.get_skill("C")
        assert c_skill is not None
        assert c_skill.cn == 1                  # C es el colimite de {A, B}
        assert c_skill.level == nivel_antes     # la taxonomia NO se toca

    def test_max_level_increases_with_depth(self):
        # Two levels: A, B → C → D with explicit join at C
        g = _graph("A", "B", "C", "D")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        g.add_morphism("C", "D", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        cn, gaps = build_hierarchy_to_fixpoint(g, pm, cb, max_iterations=5)
        max_cn = max(cn.values(), default=0)
        assert max_cn >= 1

    def test_fubini_invariant_holds(self):
        """
        Stacked joins: join(A, B) = C at cn=1; join(C, D) = E at cn=2.
        The cn of E must equal 2 (not 3), because:
          E = join[C, D] = join[join[A, B], D]
          Fubini: this equals join[A, B, D] directly.
          max{cn(C), cn(D)} + 1 = max{1, 0} + 1 = 2
        """
        g = _graph("A", "B", "C", "D", "E")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        g.add_morphism("C", "E", MorphismType.DEPENDENCY)
        g.add_morphism("D", "E", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        _register_colimit(cb, pm, ["A", "B"], "C")
        _register_colimit(cb, pm, ["C", "D"], "E")
        cn = compute_complexity_order(g, cb)
        assert cn["C"] == 1
        assert cn["E"] == 2   # not 3 — Fubini invariant

    def test_returns_complete_dict(self):
        g = _graph("A", "B", "C")
        pm, cb = _pm_cb(g)
        cn, gaps = build_hierarchy_to_fixpoint(g, pm, cb, max_iterations=3)
        for sid in ["A", "B", "C"]:
            assert sid in cn


# ---------------------------------------------------------------------------
# TestLevelCnSeparation
#
# level y cn son magnitudes ORTOGONALES y no deben pisarse:
#   level = profundidad taxonomica (curada por el humano, estatica)
#   cn    = orden de complejidad constructivo (emergente, lo fija el sistema)
#
# Antes, apply_complexity_order escribia cn dentro de level. Con 0 colimites
# registrados eso aplanaba los 172 skills del grafo real al nivel 0, destruyendo
# la taxonomia y moviendo de paso la clasificacion simple/complejo, el alcance
# de los co-reguladores (level <= 1) y la feature 4 del GNN.
# ---------------------------------------------------------------------------

class TestLevelCnSeparation:

    def test_skill_defaults_cn_zero(self):
        """Un skill declarado es atomico para el sistema: cn = 0."""
        s = Skill(id="x", name="x", level=3)
        assert s.level == 3
        assert s.cn == 0

    def test_apply_complexity_order_no_toca_level(self):
        """La taxonomia curada sobrevive al calculo de cn."""
        g = SkillCategory()
        g.add_skill(Skill(id="A", name="A", level=0))
        g.add_skill(Skill(id="B", name="B", level=2))
        g.add_skill(Skill(id="C", name="C", level=3))
        niveles_antes = {s: g.get_skill(s).level for s in g.skill_ids}

        g.apply_complexity_order({"A": 0, "B": 1, "C": 2})

        assert {s: g.get_skill(s).level for s in g.skill_ids} == niveles_antes
        assert g.get_skill("B").cn == 1
        assert g.get_skill("C").cn == 2

    def test_cn_cero_sin_colimites(self):
        """Sin colimites registrados, cn = 0 aunque la taxonomia sea profunda."""
        g = SkillCategory()
        for sid, lvl in [("A", 1), ("B", 2), ("C", 3)]:
            g.add_skill(Skill(id=sid, name=sid, level=lvl))
        pm, cb = _pm_cb(g)

        cn = compute_complexity_order(g, cb)
        g.apply_complexity_order(cn)

        assert set(cn.values()) == {0}
        assert g.stats["max_cn"] == 0
        assert g.stats["num_joins"] == 0
        assert g.stats["max_level"] == 3   # la taxonomia sigue viva

    def test_join_lleva_cn_de_componentes_no_de_level(self):
        """cn del join = 1 + max(cn componentes), NO 1 + max(level)."""
        g = SkillCategory()
        # componentes taxonomicamente profundos pero constructivamente atomicos
        g.add_skill(Skill(id="A", name="A", level=3, cn=0))
        g.add_skill(Skill(id="B", name="B", level=3, cn=0))
        g.add_skill(Skill(id="J", name="J", level=0, cn=0))
        g.add_morphism("A", "J", MorphismType.DEPENDENCY)
        g.add_morphism("B", "J", MorphismType.DEPENDENCY)
        pm, cb = _pm_cb(g)
        _register_colimit(cb, pm, ["A", "B"], "J")

        cn = compute_complexity_order(g, cb)

        assert cn["J"] == 1        # 1 + max(cn) = 1 + 0,  NO 1 + max(level) = 4

    def test_indices_y_distribuciones_separados(self):
        g = SkillCategory()
        g.add_skill(Skill(id="A", name="A", level=1))
        g.add_skill(Skill(id="B", name="B", level=1))
        g.apply_complexity_order({"A": 0, "B": 2})

        assert g.get_level_distribution() == {1: 2}
        assert g.get_cn_distribution() == {0: 1, 2: 1}
        assert [s.id for s in g.get_skills_at_cn(2)] == ["B"]
        assert g.stats["num_joins"] == 1
