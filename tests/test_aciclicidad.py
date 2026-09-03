"""
El grafo de joins debe ser aciclico.

POR QUE
-------
`hierarchy_well_founded` y `cn_join_gt_component` estaban SIN DEMOSTRAR en Lean,
y al intentar cerrarlos resulto que no eran dificiles: eran FALSOS tal como
estaban enunciados. Con un ciclo `x = join[y]`, `y = join[x]` la iteracion crece
sin parar —(0,0) (1,1) (2,2) (3,3)…— y ninguna de las dos conclusiones vale.

Los enunciados verdaderos llevan ahora la hipotesis `Aciclico`, que sus propios
docstrings ya mencionaban pero que no pedian. Este test comprueba que el grafo
real la satisface: sin eso los teoremas son ciertos pero no aplican.
"""
import sys

import pytest


@pytest.fixture(scope="module")
def joins():
    """join_id -> componentes, tal como los descubre el sistema."""
    sys.argv = ["x"]
    from scripts.train_gnn_ppo import build_skill_graph
    from nucleo.mes.patterns import PatternManager, ColimitBuilder
    from nucleo.graph.complexity import build_hierarchy_to_fixpoint

    g = build_skill_graph()
    pm = PatternManager()
    cb = ColimitBuilder(pm)
    build_hierarchy_to_fixpoint(g, pm, cb)
    out = {}
    for col in cb.all_colimits:
        pat = pm.get_pattern(col.pattern_id) if col.pattern_id else None
        if pat and col.skill_id:
            out[col.skill_id] = list(pat.component_ids)
    return out


def _alcanzables(a, joins):
    vistos, pila = set(), [a]
    while pila:
        for c in joins.get(pila.pop(), []):
            if c not in vistos:
                vistos.add(c)
                pila.append(c)
    return vistos


def test_hay_joins_que_comprobar(joins):
    # Eran 18 cuando el detector admitia como componentes etiquetas que no
    # nombran objetos. Al exigir que lo sean, los joins espurios se van.
    assert len(joins) >= 14, f"solo {len(joins)} joins; el test perderia sentido"


def test_ningun_join_se_alcanza_a_si_mismo(joins):
    """
    Es exactamente la hipotesis `Aciclico` de ComplexityOrder.lean. Si falla,
    `hierarchy_well_founded` y `cn_join_gt_component` dejan de aplicar al
    sistema, aunque sigan siendo ciertos.
    """
    ciclos = [j for j in joins if j in _alcanzables(j, joins)]
    assert not ciclos, (
        f"joins en un ciclo: {ciclos}. La iteracion de cn no alcanzaria punto "
        "fijo y `apply_complexity_order` pararia en n rondas sin justificacion."
    )


def test_cn_acotado_y_positivo(joins):
    """max(cn) >= 2 significa que hay joins anidados. NO es orden 2 de Ehresmann.

    `cn` es la recursion propia del sistema: cn(J) = 1 + max cn(componentes).
    El orden de complejidad de Ehresmann (§5.2) es otra cosa: exige que el
    colimite NO se obtenga en un solo paso desde la base, y eso solo lo impide
    un enlace distinguido COMPLEJO en el patron superior.

    Medido: los 3 objetos con cn=2 se aplanan a un unico paso —
    join(join(a,b), c) = join(a,b,c)— porque el supremo es asociativo en un
    orden parcial. Su orden de Ehresmann es 1, no 2.

    Este test sigue siendo util como guardia de que la recursion de cn produce
    algo; no como evidencia de emergencia.
    """
    sys.argv = ["x"]
    from scripts.train_gnn_ppo import build_skill_graph
    from nucleo.mes.patterns import PatternManager, ColimitBuilder
    from nucleo.graph.complexity import build_hierarchy_to_fixpoint

    g = build_skill_graph()
    pm = PatternManager()
    cb = ColimitBuilder(pm)
    cn, _ = build_hierarchy_to_fixpoint(g, pm, cb)
    assert cn, "no se calculo ningun cn"
    assert max(cn.values()) >= 2, (
        f"max(cn) = {max(cn.values())}: el motor de complexificacion no esta "
        "produciendo conceptos de segundo orden"
    )


# ---------------------------------------------------------------------------
# Y la relacion DEPENDENCY entera, no solo la de joins
# ---------------------------------------------------------------------------

def test_la_dependencia_del_grafo_real_es_un_orden():
    """El grafo dice ser una categoria delgada. Tenia 4 ciclos.

    La maquinaria de colimites de `patterns.py` y la prueba de
    `ColimitVerifier.lean` se apoyan en que la alcanzabilidad por DEPENDENCY
    sea un PREORDEN. Medido con networkx: habia 4 componentes fuertemente
    conexas, la mayor de 80 nodos. En una categoria delgada eso afirma que
    esos 80 objetos son mutuamente isomorfos, y es falso.

    Las 618 aristas culpables eran los imports de Mathlib AGREGADOS a los 125
    nodos generados. Agregar un DAG no da un DAG: si un modulo del grupo A
    importa uno de B y otro de B importa uno de A, el agregado tiene un
    2-ciclo. Y el ciclo 15 restante era `cat-basics` figurando entre los
    miembros del area que el mismo sostiene.

    Nadie leia esas aristas, pero rompian ademas la puerta de entrada:
    `area-algebra` alcanzaba 178 de 315 nodos y un nodo pertenecia a 4,3 areas
    de media, asi que entrar por area no podaba nada.
    """
    import networkx as nx
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.types import MorphismType

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)

    G = nx.DiGraph()
    for s in n._graph.skills:
        G.add_node(s.id)
    for m in n._graph.morphisms:
        if (m.morphism_type == MorphismType.DEPENDENCY
                and m.source_id != m.target_id):
            G.add_edge(m.source_id, m.target_id)

    ciclos = [sorted(c) for c in nx.strongly_connected_components(G)
              if len(c) > 1]
    assert not ciclos, (
        "la dependencia tiene %d ciclos; el mayor con %d nodos: %s. "
        "Una categoria delgada con un ciclo afirma que sus objetos son "
        "mutuamente isomorfos, y los colimites dejan de estar justificados."
        % (len(ciclos), max(len(c) for c in ciclos), ciclos[0][:6]))


def test_entrar_por_un_area_poda_de_verdad():
    """Los conos de area tienen que SEPARAR, o la puerta no sirve de nada.

    Con las aristas de import agregado, `area-algebra` alcanzaba el 56 % del
    grafo y los conos se solapaban entre el 62 % y el 77 %. Un clasificador
    podia acertar el area y no servir para nada, porque el area acertada abria
    media matematica. Esta guardia fija el criterio: ningun cono puede pasar
    de un tercio del grafo, y un nodo no puede estar de media en mas de dos
    areas.
    """
    import networkx as nx
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.types import MorphismType

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph

    G = nx.DiGraph()
    for s in g.skills:
        G.add_node(s.id)
    for m in g.morphisms:
        if (m.morphism_type == MorphismType.DEPENDENCY
                and m.source_id != m.target_id):
            G.add_edge(m.source_id, m.target_id)

    areas = [s.id for s in g.skills
             if (s.metadata or {}).get("category") == "area"]
    assert areas, "el grafo ya no tiene capa de areas"

    conos = {a: nx.descendants(G, a) for a in areas}
    mayor = max(conos.items(), key=lambda kv: len(kv[1]))
    assert len(mayor[1]) <= len(G) // 3, (
        "%s alcanza %d de %d nodos: entrar por ahi no poda nada"
        % (mayor[0], len(mayor[1]), len(G)))

    media = sum(len(c) for c in conos.values()) / len(G)
    assert media <= 2.0, (
        "un nodo pertenece a %.1f areas de media: los conos se solapan tanto "
        "que no separan" % media)
