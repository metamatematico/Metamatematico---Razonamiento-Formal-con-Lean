"""
Complexity Order — Emergent Hierarchy for the NLE Skill Graph
=============================================================

Implements cn(X): the emergent hierarchical depth of a skill.

    cn(X) = 0           if X is not the colimit (join) of any pattern
    cn(X) = 1 + max{cn(P_i) | P_i ∈ components(X)}  if X = join[P]

The hierarchy is NOT assigned manually. It emerges from the colimit
structure of the skill graph (Ehresmann MES §2, v7.0).

In the thin category of skills (preorder):
  - colimit of a diagram = join (supremum in the preorder)
  - all diagrams commute automatically (at most one morphism between
    any two objects — proof irrelevance in Prop)
  - cn is computable in O(|colimits| × diameter) iterations
  - fixpoint is reached in at most diameter(graph) iterations

Lean foundations in ComplexityOrder.lean:
  - Theorem: colimits in thin categories are joins
  - Theorem (Fubini): join(join ∘ S) = join(⋃ S)   — stacked cocones commute
  - Theorem: cn is well-defined (fixpoint of Bellman-Ford)
"""

from __future__ import annotations

import logging
import uuid
from itertools import combinations as _combinations

#: Tope de predecesores para buscar descomposiciones alternativas por
#: subconjunto. Con k predecesores hay 2^k - k - 2 subconjuntos propios de
#: tamaño >= 2, y cada uno cuesta una llamada a `find_colimit`. Con 7 son 119;
#: mas alla no compensa. Ningun nodo del grafo real llega a ese numero.
_MAX_PREDS_SUBCONJUNTOS = 7
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from nucleo.types import Skill, MorphismType, PillarType

if TYPE_CHECKING:
    from nucleo.graph.category import SkillCategory
    from nucleo.mes.patterns import PatternManager, ColimitBuilder
    from nucleo.types import Pattern, Colimit

logger = logging.getLogger(__name__)


# =============================================================================
# CORE ALGORITHM
# =============================================================================

def orden_irreducible(
    graph: "SkillCategory",
    colimit_builder: "ColimitBuilder",
) -> dict[str, int]:
    """
    El orden que decide si hay EMERGENCIA: minimo sobre las descomposiciones.

    NO SUSTITUYE A `compute_complexity_order`, QUE ES OTRA COSA
    ----------------------------------------------------------
    `cn` toma el MAXIMO sobre las descomposiciones, y hace bien: es la altura
    que domina a las componentes de CADA descomposicion, esta respaldada por
    `cn_ge_of_mem_decomp` y `hierarchy_well_founded_multi`, y es la que da la
    buena fundacion que hace terminar la iteracion.

    Pero la altura no es la irreducibilidad. Para preguntar «¿es X emergente?»
    hace falta lo contrario: si X admite ALGUNA descomposicion cuyas
    componentes sean todas de orden 0, entonces X es un colimite simple de
    objetos de base y su orden de complejidad en el sentido de Ehresmann es 1,
    por muchas otras descomposiciones altas que tenga.

    Ahi es donde el Principio de Multiplicidad deja de ser decorativo: un
    objeto con varias descomposiciones puede ser mas simple de lo que su
    descomposicion mas alta sugiere, y solo mirando todas se sabe.

    Medido sobre el grafo real: de los tres objetos con `cn = 2`, uno
    (`homological-algebra-cat`) tiene orden irreducible 1 — su descomposicion
    `{homological-algebra, limits}` tiene las dos componentes en orden 0. Los
    otros dos si son irreducibles.

    Returns:
        dict skill_id -> orden irreducible (>= 0). 0 para los que no son
        colimite de nada.
    """
    pm = colimit_builder._pattern_manager

    # descomposiciones por objeto
    decomps: dict[str, list[list[str]]] = {}
    for col in colimit_builder.all_colimits:
        pat = pm.get_pattern(col.pattern_id) if col.pattern_id else None
        if pat is None or not pat.component_ids:
            continue
        decomps.setdefault(col.skill_id, []).append(list(pat.component_ids))

    orden: dict[str, int] = {sid: 0 for sid in graph.skill_ids}

    # Punto fijo descendente: se empieza por la altura `cn` (cota superior
    # valida) y se baja mientras alguna descomposicion permita menos. Baja de
    # forma monotona y esta acotada por 0, luego termina.
    for sid, alt in compute_complexity_order(graph, colimit_builder).items():
        orden[sid] = alt

    cambio = True
    vueltas = 0
    while cambio and vueltas <= len(graph.skill_ids) + 2:
        cambio = False
        vueltas += 1
        for obj, ds in decomps.items():
            mejor = min(
                1 + max((orden.get(c, 0) for c in comps), default=-1)
                for comps in ds
            )
            if mejor < orden.get(obj, 0):
                orden[obj] = mejor
                cambio = True
    return orden


def objetos_emergentes(
    graph: "SkillCategory",
    colimit_builder: "ColimitBuilder",
    minimo: int = 2,
) -> dict[str, int]:
    """
    Los objetos genuinamente emergentes: irreducibles a orden < `minimo`.

    Esta es la cifra que el sistema debe publicar cuando afirme emergencia, no
    `max_cn`. Un objeto con `cn = 2` puede tener orden irreducible 1, y
    entonces no es emergencia: es un colimite simple con una descomposicion
    alta al lado.
    """
    orden = orden_irreducible(graph, colimit_builder)
    return {k: v for k, v in orden.items() if v >= minimo}


def compute_complexity_order(
    graph: "SkillCategory",
    colimit_builder: "ColimitBuilder",
) -> dict[str, int]:
    """
    Compute cn(X) for all skills in the graph.

    Uses Bellman-Ford style fixpoint iteration:
      cn[join_id] = 1 + max{cn[c] for c in pattern.components}

    Iterates until no cn value changes (guaranteed to terminate since
    the graph is finite and the preorder is acyclic).

    Args:
        graph: The skill category (provides skill_ids, get_skill)
        colimit_builder: Provides access to all registered colimits

    Returns:
        dict mapping skill_id → complexity_order (≥ 0)
    """
    cn: dict[str, int] = {sid: 0 for sid in graph.skill_ids}

    changed = True
    iteration = 0
    max_iter = len(graph.skill_ids) + 2

    while changed:
        changed = False
        iteration += 1
        if iteration > max_iter:
            logger.warning(
                "compute_complexity_order: safety limit reached, stopping"
            )
            break

        for colimit in colimit_builder.all_colimits:
            join_id = colimit.skill_id
            if join_id not in cn:
                cn[join_id] = 0

            pattern = colimit_builder._pattern_manager.get_pattern(
                colimit.pattern_id
            )
            if pattern is None or not pattern.component_ids:
                continue

            max_comp = max(cn.get(c, 0) for c in pattern.component_ids)
            # MAXIMO sobre todas las descomposiciones, no asignacion.
            #
            # Con el Principio de Multiplicidad un objeto tiene VARIAS
            # descomposiciones. Asignar `max_comp + 1` hacia que el bucle
            # oscilara entre las alturas de unas y otras y no convergiera
            # nunca: se alcanzaba el limite de seguridad y se paraba a medias.
            #
            # Respaldo formal: `multiIter` y `hierarchy_well_founded_multi`
            # (ComplexityOrder.lean) generalizan la iteracion a varias
            # descomposiciones tomando el maximo, con lo que la sucesion es
            # monotona no decreciente y alcanza punto fijo en n rondas.
            # `cn_ge_of_mem_decomp` justifica por que el maximo: el cn debe
            # dominar a las componentes de CADA descomposicion.
            new_cn = max(cn[join_id], max_comp + 1)

            if cn[join_id] != new_cn:
                cn[join_id] = new_cn
                changed = True

    n_joins = sum(1 for v in cn.values() if v > 0)
    logger.debug(
        f"compute_complexity_order: {iteration} iter(s), "
        f"{n_joins} join-skills, max_cn={max(cn.values(), default=0)}"
    )
    return cn


# =============================================================================
# JOIN DISCOVERY
# =============================================================================

@dataclass
class ConceptGap:
    """
    Un patron que tiene CO-CONOS pero ningun CO-CONO LIMITE.

    Es decir: existen cotas superiores de las componentes, pero ninguna es
    minimal. Categoricamente, el colimite del patron NO existe en G_n.

    Esto NO es un defecto que parchear — es informacion. Significa que al
    grafo de conocimiento le falta el concepto que unifica las componentes,
    o que la base estructural esta incompleta (falta una arista de orden).

    Es el disparador legitimo de complexificacion (Ehresmann): el concepto
    nuevo debe aportarlo la matematica (LLM propone, Lean verifica), no la
    cirugia sobre el grafo. Fabricar un vertice y cablearlo para que cumpla
    la propiedad universal es asumir la conclusion.
    """
    component_ids: list[str]
    cocones: list[str]          # cotas superiores encontradas
    pattern_id: Optional[str] = None
    #: Por que no hay colimite. Distingue tres cosas que no son la misma:
    #:   "sin cotas superiores"  — no hay ni siquiera donde mirar
    #:   "minimal sin co-cono"   — hay minimal, pero ninguna eleccion de
    #:                             flechas conmuta con los enlaces del patron.
    #:                             Este caso solo existe fuera de la delgadez:
    #:                             es el hueco que la delgadez ocultaba.
    #:   "indecidible"           — la busqueda excedio su cota. NO es «no
    #:                             existe»: es «no se sabe», y confundirlos
    #:                             seria afirmar de mas.
    motivo: Optional[str] = None

    @property
    def n_cocones(self) -> int:
        return len(self.cocones)

    def __repr__(self) -> str:
        comps = ", ".join(self.component_ids[:3])
        resto = len(self.component_ids) - 3
        if resto > 0:
            comps += f" (+{resto})"
        return f"ConceptGap([{comps}], {len(self.cocones)} co-conos, sin limite)"


@dataclass
class TrivialColimit:
    """
    Un patron cuyo CO-CONO LIMITE es una de sus propias componentes.

    No es un hueco: el colimite EXISTE. `componente_puede_ser_colimite`
    (ColimitVerifier.lean) lo demuestra con el testigo `0 → 1`: el colimite de
    `[0, 1]` es `1`, que esta en el diagrama. Por `reachable_refl` toda
    componente es cota superior de si misma, asi que la componente que domina a
    las demas es el co-cono limite.

    Tampoco es una descomposicion utilizable: registrarla romperia
    `AciclicoMulti`, que exige toda componente ESTRICTAMENTE menor que el
    objeto. Ver `join_propio_rompe_aciclicidad` y `autoJoin_sin_punto_fijo`
    (ComplexityOrder.lean): con una descomposicion asi la iteracion de cn crece
    en cada ronda y no alcanza punto fijo.

    De ahi el tratamiento: se reconoce, se cuenta, y NO entra en cn ni en gaps.
    """
    component_ids: list[str]
    colimit_id: str             # la componente que resulta ser el colimite
    pattern_id: "Optional[str]" = None

    def __repr__(self) -> str:
        comps = ", ".join(self.component_ids[:3])
        resto = len(self.component_ids) - 3
        if resto > 0:
            comps += f" (+{resto})"
        return f"TrivialColimit([{comps}] -> {self.colimit_id}, es componente)"


def find_cocones(
    component_ids: list[str],
    graph: "SkillCategory",
) -> list[str]:
    """
    Encuentra los CO-CONOS del patron: los objetos X con Pi ≤ X para todo i.

    En una categoria thin, un co-cono sobre P con vertice X es exactamente una
    cota superior de las componentes: la familia {Pi → X} conmuta automaticamente
    porque Hom tiene a lo sumo un elemento (thin_unique_hom, ComplexityOrder.lean).

    NO filtra por minimalidad — eso es find_colimit. Puede devolver 0, 1 o muchos.
    No crea nada.

    LA RELACION ES REFLEXIVA, Y LAS COMPONENTES NO SE EXCLUYEN
    ---------------------------------------------------------
    `isCocone` (ColimitVerifier.lean) es `diagram.all (fun d => reachable d apex)`
    con `reachable` reflexiva (`reachable_refl`). No excluye nada.

    Esta funcion se desviaba de esa definicion por DOS caminos a la vez:

      1. usaba `graph.reachable_from`, que NO es reflexiva —devuelve las rutas
         de longitud >= 1—, mientras que `graph.is_preorder_leq` si lo es. El
         resto del sistema (`is_join`, `_connected_by_cluster`) usa la version
         reflexiva, asi que dos funciones del mismo repo discrepaban en la
         diagonal;
      2. ademas hacia `common.discard(c)` por cada componente, sin comentario.

    Consecuencia medida sobre el grafo real: 14 de los 27 "huecos conceptuales"
    tenian colimite —una de sus componentes— y `llenar_hueco_conceptual` pedia
    al LLM el concepto unificador de patrones que ya lo contenian. Contraste
    directo, mismo patron, mismo repo:

        is_join('functional-analysis', ['functional-analysis','real-analysis'])
            -> is_join=True, upper_bound=True, minimal=True
        find_colimit(['functional-analysis','real-analysis'])
            -> None   (y se archivaba como ConceptGap)

    Ahora se usa el up-set reflexivo. Los patrones cuyo colimite es una
    componente salen como TrivialColimit: tienen colimite, no son huecos, y no
    entran en la recursion de cn.
    """
    if not component_ids:
        return []
    _ORD = type(graph).ORDER_MORPHISMS
    # up(c) = {x : c <= x}, reflexivo — la definicion de isCocone.
    reachable_sets = [
        graph.reachable_from(c, _ORD) | {c} for c in component_ids
    ]
    common = reachable_sets[0].copy()
    for r in reachable_sets[1:]:
        common &= r
    return sorted(common)


def find_colimit(
    component_ids: list[str],
    graph: "SkillCategory",
    colimit_builder: "ColimitBuilder",
) -> Optional[str]:
    """
    Encuentra el CO-CONO LIMITE: el co-cono universal (inicial) del patron.

    Un skill J es el colimite de S iff:
      1. ∀ c ∈ S: c ≤ J          (J es co-cono / cota superior)
      2. ∀ X ∈ G_n: (∀c ≤ X) → J ≤ X   (J es minimal entre los co-conos)

    En la categoria thin esto es el join, y la unicidad del mediador es
    automatica (JoinColimit.lean, IsColimitBridge.lean).

    La universalidad es un TEST, nunca una construccion: si ningun objeto de
    G_n la cumple, el colimite no existe y se devuelve None. Ver ConceptGap.

    Returns:
        skill_id del colimite, o None si el patron no tiene co-cono limite.
    """
    cocones = find_cocones(component_ids, graph)
    if not cocones:
        return None

    # Minimalidad: apex ≤ X para toda cota superior X. Las cotas superiores son
    # EXACTAMENTE los co-conos, asi que basta comparar dentro de `cocones` en vez
    # de recorrer los 172 skills del grafo por candidato (que es lo que hace
    # is_join). Mismo resultado, O(|cocones|^2) en lugar de O(|cocones| * |G_n|).
    _ORD = type(graph).ORDER_MORPHISMS
    for apex in cocones:
        if all(
            graph.is_preorder_leq(apex, x, _ORD)
            for x in cocones if x != apex
        ):
            # Confirmacion con la verificacion completa (upper bound + minimalidad)
            if colimit_builder.is_join(apex, component_ids, graph)["is_join"]:
                return apex
    return None


def find_colimit_cong(
    pattern: "Pattern",
    graph: "SkillCategory",
    colimit_builder: "ColimitBuilder",
    cong=None,
) -> "tuple[Optional[str], Optional[str]]":
    """
    El colimite del patron exigiendo CO-CONO, no solo cota superior.

    QUE CAMBIA RESPECTO A `find_colimit`
    ------------------------------------
    `find_colimit` pregunta «¿es `apex` alcanzable desde toda componente?».
    Eso es una pregunta sobre VERTICES, y solo basta si la categoria es
    delgada: con `Hom(a,b)` booleano, elegida una flecha por componente la
    conmutacion `P(x) ; f_j = f_i` se cumple sola, porque solo hay un morfismo
    paralelo posible. Es `cocono_delgado_siempre` (Complexificacion.lean).

    Fuera de la delgadez eso deja de valer: hay que exhibir UNA ELECCION de
    flecha por componente que conmute con los enlaces del patron. Cota superior
    ya no implica co-cono — `cota_superior_no_implica_cocono`, con el testigo
    `Mon = {1,e}`.

    LA CONGRUENCIA
    --------------
    «Conmutar» solo tiene sentido relativo a que caminos se declaran iguales.
    Por defecto se usa `congruencia_automatica(graph)`: identifica aristas
    paralelas que difieren solo en el TIPO (dep/an/tr) y no declaran
    construccion, que es la semantica que el propio grafo ya afirmaba en
    `is_preorder_leq`. No identifica nada mas: dos morfismos con construccion
    distinta fueron demostrados distintos en Lean (`no_hay_iso`), y que dos
    caminos compuestos coincidan es un teorema sobre el dominio, no una
    convencion — eso sale por `pendientes_de_decidir`.

    Por `cocono_monotono_en_la_congruencia`, mas identificaciones solo pueden
    AÑADIR co-conos. Asi que este resultado es una cota inferior honesta: lo
    que sobrevive aqui sobrevive en cualquier congruencia mas fina.

    Returns:
        `(apex, motivo)`. `apex` es None si no hay colimite; `motivo` explica
        por que, y vale None cuando si lo hay. El motivo `"indecidible"` marca
        los casos en que la busqueda excedio su cota — no es «no existe», es
        «no se sabe», y el llamador no debe confundirlos.
    """
    from nucleo.graph.no_delgado import congruencia_automatica, hay_cocono_cong

    cong = cong if cong is not None else congruencia_automatica(graph)

    cocones = find_cocones(pattern.component_ids, graph)
    if not cocones:
        return None, "sin cotas superiores"

    _ORD = type(graph).ORDER_MORPHISMS
    indecidibles: list[str] = []

    for apex in cocones:
        if not all(
            graph.is_preorder_leq(apex, x, _ORD)
            for x in cocones if x != apex
        ):
            continue
        if not colimit_builder.is_join(apex, pattern.component_ids, graph)["is_join"]:
            continue

        # AQUI muerde la migracion: minimal entre las cotas superiores, si;
        # pero ademas tiene que existir una eleccion de flechas que conmute.
        veredicto = hay_cocono_cong(pattern, apex, graph, cong)
        if veredicto is True:
            return apex, None
        if veredicto is None:
            indecidibles.append(apex)

    if indecidibles:
        return None, "indecidible"
    return None, "minimal sin co-cono"


def find_existing_join(
    component_ids: list[str],
    graph: "SkillCategory",
    colimit_builder: "ColimitBuilder",
) -> Optional[str]:
    """Alias historico de find_colimit(). Mantener por compatibilidad."""
    return find_colimit(component_ids, graph, colimit_builder)


def build_join_for_pattern(
    pattern: "Pattern",
    graph: "SkillCategory",
    colimit_builder: "ColimitBuilder",
    cong=None,
) -> "Optional[Colimit] | ConceptGap":
    """
    Descubre y registra el CO-CONO LIMITE de un patron. Nunca lo fabrica.

    Pasos:
      1. Si el patron ya tiene colimite registrado, devolverlo.
      2. Buscar el co-cono limite entre los objetos de G_n (find_colimit).
      3. Si existe: registrarlo (operacion PURA, no muta el grafo).
      4. Si no existe: devolver ConceptGap con los co-conos encontrados.

    POR QUE NO SE FABRICA
    ---------------------
    La version anterior, cuando no encontraba colimite, creaba un skill nuevo
    y le añadia (a) morfismos co-cono desde las componentes y (b) morfismos
    salientes a todas las cotas superiores "para asegurar minimalidad".

    Eso tenia tres problemas:

    1. No es emergencia. Inventar un vertice y cablearlo para que cumpla la
       propiedad universal es asumir la conclusion. El colimite debe
       DESCUBRIRSE como el co-cono universal entre los que ya hay; la
       universalidad es un test, no una construccion.

    2. No terminaba. Cada nodo fabricado quedaba por encima de >= 2
       componentes, luego era un nuevo punto de convergencia, luego se
       fabricaba otro encima. Medido sobre el grafo real (172 skills):
       iter 1 -> 44 patrones, 41 joins, grafo 172->195;
       iter 2 -> 94 patrones. Crecia en vez de converger.

    3. Reescribia el objeto que analizaba. Insertar el nodo entre las
       componentes y sus cotas superiores reales cambia el preorden, asi que
       colimites que antes eran validos dejaban de ser minimales.

    Sin fabricacion la terminacion es estructural: no se añaden nodos, luego no
    aparecen puntos de convergencia nuevos, luego el conjunto de patrones es
    estable y el punto fijo llega en la iteracion 2. Y entonces si aplica
    `hierarchy_well_founded` de ComplexityOrder.lean, que mide cn sobre una
    estructura FIJA.

    Returns:
        Colimit        si el patron tiene co-cono limite propio en G_n.
        TrivialColimit si el co-cono limite es una de sus propias componentes.
        ConceptGap     si tiene co-conos pero ninguno es minimal.
        None           si el patron tiene menos de 2 componentes.
    """
    if len(pattern.component_ids) < 2:
        return None

    # Ya registrado?
    existing = colimit_builder.get_colimit_for_pattern(pattern.id)
    if existing is not None:
        return existing

    join_id, motivo = find_colimit_cong(pattern, graph, colimit_builder, cong)

    # Caso trivial: el colimite es una componente del propio patron.
    # Tiene colimite (no es hueco) pero no se registra: `AciclicoMulti` exige
    # toda componente estrictamente menor que el objeto, y aqui una de ellas ES
    # el objeto. Ver `join_propio_rompe_aciclicidad` (ComplexityOrder.lean).
    if join_id is not None and join_id in pattern.component_ids:
        logger.debug(
            f"TrivialColimit: el colimite de {list(pattern.component_ids)} es "
            f"'{join_id}', que es una de sus componentes — no se registra"
        )
        return TrivialColimit(
            component_ids=list(pattern.component_ids),
            colimit_id=join_id,
            pattern_id=pattern.id,
        )

    if join_id is not None:
        # Registro puro: construye el cocone_map desde morfismos existentes.
        # No añade skills ni aristas.
        return colimit_builder._register_existing_join(pattern, join_id, graph)

    # Sin co-cono limite: el colimite NO existe en G_n. Es un hueco conceptual,
    # no un fallo. Lo emitimos para que el MES lo trate (CR_org/CR_str proponen
    # la complexificacion; el concepto que la llena lo aporta la matematica).
    cocones = find_cocones(pattern.component_ids, graph)
    logger.debug(
        f"ConceptGap: patron {pattern.id} tiene {len(cocones)} cotas "
        f"superiores pero ninguna es co-cono limite ({motivo}) — no se "
        f"fabrica vertice"
    )
    return ConceptGap(
        component_ids=list(pattern.component_ids),
        cocones=cocones,
        pattern_id=pattern.id,
        motivo=motivo,
    )


# =============================================================================
# FIXPOINT BUILDER
# =============================================================================

def _detect_convergence_patterns(
    graph: "SkillCategory",
    pattern_manager: "PatternManager",
    colimit_builder: "Optional[ColimitBuilder]" = None,
) -> "list[Pattern]":
    """
    Detect convergence patterns: for each node X with ≥ 2 distinct
    direct predecessors, create pattern {A, B, ...} where A, B, ...
    are the non-identity predecessors of X.

    This is the canonical source of joins in the preorder:
      X is the join of its direct predecessor set iff X is the minimal
      element above all of them.  `is_join` will verify this property.

    Unlike `detect_pattern_in_graph` (BFS connected components),
    convergence patterns correctly capture the local structure of the
    preorder — each convergence point corresponds to one potential join.
    """
    from nucleo.types import MorphismType as _MT
    patterns: list = []
    seen: set[frozenset] = set()

    for skill_id in graph.skill_ids:
        preds = []
        for morph in graph.incoming_morphisms(skill_id):
            if (morph.morphism_type != _MT.IDENTITY
                    and morph.source_id != skill_id):
                preds.append(morph.source_id)
        preds = list(dict.fromkeys(preds))  # deduplicate, preserve insertion order

        if len(preds) < 2:
            continue

        key = frozenset(preds)
        if key in seen:
            continue
        seen.add(key)

        # ENLACES DISTINGUIDOS: los morfismos ENTRE COMPONENTES.
        #
        # Aqui se pasaban los morfismos `pred -> skill_id`, que son el CO-CONO
        # del patron, no sus enlaces distinguidos. Un patron es un funtor
        # `P : I -> K` y sus enlaces son `P(x) : P_i -> P_j`, entre componentes
        # (Def 2.1). `create_pattern` los descarta en silencio cuando el destino
        # no es componente, asi que `index_morphisms` salia VACIO en los 116
        # patrones: la categoria de indices no tenia morfismos y todo patron era
        # un diagrama DISCRETO.
        #
        # Consecuencia: la condicion de co-cono `P(x) ; f_j = f_i` no tenia
        # ningun `P(x)` sobre el que aplicarse, luego era vacua, luego co-cono y
        # cota superior coincidian por construccion — antes incluso de que la
        # delgadez lo forzara.
        links = []
        for a in preds:
            for b in preds:
                if a == b:
                    continue
                for morph in graph.hom(a, b):
                    if morph.morphism_type != _MT.IDENTITY:
                        links.append(morph.id)

        pattern = pattern_manager.create_pattern(preds, links, graph=graph)
        patterns.append(pattern)

        # ── Descomposiciones alternativas ────────────────────────────────
        #
        # Hasta aqui se emitia UN patron por nodo de convergencia: todos sus
        # predecesores. Con eso ningun objeto tiene nunca dos descomposiciones,
        # y el Principio de Multiplicidad no puede cumplirse por construccion.
        #
        # MP no es un adorno: `multiplicidad_necesaria_para_complejidad`
        # (EhresmannLinks.lean) demuestra que sin el TODO compuesto de enlaces
        # simples es simple, o sea que el sistema no puede producir enlaces
        # complejos. Y `MP_alcanzable_en_preorden` demuestra que un preorden si
        # lo admite, luego la limitacion era del algoritmo.
        #
        # Medido sobre el grafo real: hay 5 descomposiciones alternativas
        # ocultas y 3 parejas no conectadas por cluster, todas en `homology`.
        #
        # El coste esta acotado: solo se miran nodos con pocos predecesores, y
        # los subconjuntos se filtran exigiendo que su colimite sea el MISMO
        # nodo. No se fabrica nada.
        if 2 < len(preds) <= _MAX_PREDS_SUBCONJUNTOS:
            for k in range(2, len(preds)):
                for sub in _combinations(sorted(preds), k):
                    clave = frozenset(sub)
                    if clave in seen:
                        continue
                    if find_colimit(list(sub), graph, colimit_builder) != skill_id:
                        continue          # no es descomposicion de este objeto
                    seen.add(clave)
                    # MISMO CRITERIO QUE ARRIBA: enlaces ENTRE COMPONENTES.
                    #
                    # Aqui sobrevivia el bug que ya se habia corregido en la
                    # rama principal: se recogian los morfismos `pred ->
                    # skill_id`, que son las PATAS del co-cono, no los enlaces
                    # del patron. `create_pattern` los descarta en silencio
                    # porque su destino no es componente, asi que estos
                    # subpatrones salian DISCRETOS y su colimite era un
                    # coproducto — que se aplana siempre, delgado o no.
                    sub_links = []
                    for a in sub:
                        for b in sub:
                            if a == b:
                                continue
                            for morph in graph.hom(a, b):
                                if morph.morphism_type != _MT.IDENTITY:
                                    sub_links.append(morph.id)
                    patterns.append(
                        pattern_manager.create_pattern(
                            list(sub), sub_links, graph=graph)
                    )

    return patterns


def build_hierarchy_to_fixpoint(
    graph: "SkillCategory",
    pattern_manager: "PatternManager",
    colimit_builder: "ColimitBuilder",
    max_iterations: int = 20,
    cong=None,
) -> "tuple[dict[str, int], list[ConceptGap]]":
    """
    Descubre la jerarquia emergente hasta el punto fijo.

    En cada paso:
      1. Detecta patrones de convergencia (nodos con >= 2 predecesores).
      2. Para cada patron sin colimite registrado: busca su co-cono limite.
      3. Para en cuanto no se registra ningun colimite nuevo (punto fijo).

    Se usan patrones de convergencia —no componentes conexas arbitrarias—
    porque identifican correctamente los puntos JOIN del preorden: un nodo X
    con predecesores A, B es el join de {A, B} si es el minimal por encima de
    ambos. `is_join` verifica esa minimalidad (Thm 2.10).

    El NUMERO DE NIVELES no esta prefijado: emerge de la estructura.

    TERMINACION (estructural, desde 2026-08-21)
    -------------------------------------------
    Esta funcion ya NO fabrica vertices: `build_join_for_pattern` solo descubre
    colimites que ya existen en G_n, y su registro es puro. Como no se añaden
    skills, no aparecen puntos de convergencia nuevos, el conjunto de patrones
    es estable y el punto fijo llega en la iteracion 2.

    La version anterior si fabricaba, y no convergia: iter 1 -> 44 patrones,
    41 joins, grafo 172->195 skills; iter 2 -> 94 patrones. Ver el docstring
    de build_join_for_pattern.

    Tras el punto fijo se calcula cn para todos los skills y se escribe en
    skill.cn via apply_complexity_order. skill.level (taxonomia curada) no se
    toca — son magnitudes ortogonales.

    TRES DESENLACES POR PATRON, NO DOS
    ----------------------------------
      · Colimit        — co-cono limite propio: se registra y cuenta para cn.
      · TrivialColimit — el colimite es una de sus componentes. Tiene colimite,
                         luego NO es hueco; pero romperia `AciclicoMulti`,
                         luego NO entra en cn. Se cuenta y se registra en el log.
      · ConceptGap     — co-conos pero ninguno minimal: hueco de verdad.

    El tercer caso estaba absorbiendo al segundo porque `find_cocones` no era
    fiel a `isCocone`. Ver su docstring.

    Returns:
        (cn, gaps) donde
          cn   : dict skill_id -> orden de complejidad constructivo
          gaps : patrones con co-conos pero sin co-cono limite. NO son errores:
                 son los huecos conceptuales del grafo de conocimiento, y el
                 disparador legitimo de complexificacion para el MES.
    """
    logger.info("build_hierarchy_to_fixpoint: comenzando")
    gaps: dict[frozenset, ConceptGap] = {}
    triviales: dict[frozenset, TrivialColimit] = {}
    # Deduplicacion por CONJUNTO DE COMPONENTES, no por pattern.id.
    # _detect_convergence_patterns crea un Pattern nuevo (id nuevo) en cada
    # iteracion para el mismo conjunto, asi que get_colimit_for_pattern(id)
    # nunca acertaba: el mismo colimite se re-registraba una vez por iteracion
    # (360 registros para 18 joins distintos) y `nuevos` nunca llegaba a 0,
    # agotando las 20 iteraciones.
    resueltos: set[frozenset] = set()

    for iteration in range(max_iterations):
        patterns = _detect_convergence_patterns(graph, pattern_manager, colimit_builder)

        nuevos = 0
        for pattern in patterns:
            clave = frozenset(pattern.component_ids)
            if clave in resueltos or clave in gaps or clave in triviales:
                continue
            if colimit_builder.get_colimit_for_pattern(pattern.id) is not None:
                resueltos.add(clave)
                continue
            result = build_join_for_pattern(pattern, graph, colimit_builder, cong)
            if isinstance(result, ConceptGap):
                gaps[clave] = result
            elif isinstance(result, TrivialColimit):
                triviales[clave] = result
                resueltos.add(clave)
            elif result is not None:
                resueltos.add(clave)
                nuevos += 1

        logger.debug(
            f"  iter {iteration + 1}: {len(patterns)} patrones, "
            f"{nuevos} colimites nuevos, {len(gaps)} huecos"
        )

        if nuevos == 0:
            logger.info(
                f"build_hierarchy_to_fixpoint: punto fijo en iteracion {iteration + 1}"
            )
            break
    else:
        logger.warning(
            "build_hierarchy_to_fixpoint: max_iterations sin punto fijo"
        )

    cn = compute_complexity_order(graph, colimit_builder)
    graph.apply_complexity_order(cn)

    max_cn = max(cn.values(), default=0)
    n_joins = sum(1 for v in cn.values() if v > 0)
    logger.info(
        f"Jerarquia: {len(cn)} skills, max_cn={max_cn}, "
        f"colimites={n_joins}, huecos conceptuales={len(gaps)}, "
        f"colimites triviales={len(triviales)}"
    )
    for t in triviales.values():
        logger.debug(f"  {t}")
    return cn, list(gaps.values())


def _find_upper_bounds(
    component_ids: list[str],
    graph: "SkillCategory",
    exclude_id: str,
) -> list[str]:
    """
    Find all skills reachable from every component (upper bounds).
    Excludes the join itself and the components.
    """
    if not component_ids:
        return []
    reachable_sets = [graph.reachable_from(c) for c in component_ids]
    common = reachable_sets[0].copy()
    for r in reachable_sets[1:]:
        common &= r
    common.discard(exclude_id)
    for c in component_ids:
        common.discard(c)
    return list(common)


def _dominant_pillar(
    component_ids: list[str],
    graph: "SkillCategory",
) -> Optional[PillarType]:
    """Return the most frequent pillar among components."""
    counts: dict[PillarType, int] = {}
    for cid in component_ids:
        skill = graph.get_skill(cid)
        if skill and skill.pillar:
            counts[skill.pillar] = counts.get(skill.pillar, 0) + 1
    return max(counts, key=lambda p: counts[p]) if counts else None


def _join_name(component_ids: list[str], graph: "SkillCategory") -> str:
    """Generate a descriptive name for a join skill."""
    names = []
    for cid in component_ids[:3]:
        skill = graph.get_skill(cid)
        if skill:
            names.append(skill.name.split()[0])
    suffix = "…" if len(component_ids) > 3 else ""
    return f"Join[{' × '.join(names)}{suffix}]"
