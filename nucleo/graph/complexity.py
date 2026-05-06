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
            new_cn = max_comp + 1

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

def find_existing_join(
    component_ids: list[str],
    graph: "SkillCategory",
    colimit_builder: "ColimitBuilder",
) -> Optional[str]:
    """
    Find a skill already in the graph that is the join of component_ids.

    A skill J is the join of S iff:
      1. ∀ c ∈ S: c ≤ J  (J is an upper bound)
      2. ∀ X ∈ G_n: (∀ c ≤ X) → J ≤ X  (J is the minimal upper bound)

    Returns the skill_id if found, None otherwise.
    """
    for skill_id in graph.skill_ids:
        if skill_id in component_ids:
            continue
        result = colimit_builder.is_join(skill_id, component_ids, graph)
        if result["is_join"]:
            return skill_id
    return None


def build_join_for_pattern(
    pattern: "Pattern",
    graph: "SkillCategory",
    colimit_builder: "ColimitBuilder",
) -> Optional["Colimit"]:
    """
    Find or create the join skill for a pattern.

    Steps:
      1. Check if a join already exists in the graph (is_join check).
      2. If yes: register it as a colimit and return.
      3. If no: create a new join skill, add cocone morphisms (comp → join),
         then add outgoing morphisms to all existing upper bounds to ensure
         minimality (join ≤ X for every upper bound X).

    In the thin category, the join is the minimal upper bound.

    Returns:
        Colimit object if successful, None if pattern has < 2 components
        or the join already has a registered colimit.
    """
    if len(pattern.component_ids) < 2:
        return None

    # Already registered?
    if colimit_builder.get_colimit_for_pattern(pattern.id) is not None:
        return colimit_builder.get_colimit_for_pattern(pattern.id)

    # Step 1: look for an existing join in the graph
    existing_join_id = find_existing_join(
        pattern.component_ids, graph, colimit_builder
    )
    if existing_join_id:
        return colimit_builder._register_existing_join(
            pattern, existing_join_id, graph
        )

    # Step 2: create a new join skill
    dominant_pillar = _dominant_pillar(pattern.component_ids, graph)
    max_level = max(
        (graph.get_skill(c).level if graph.get_skill(c) else 0)
        for c in pattern.component_ids
    )

    join_skill = Skill(
        id=f"join_{uuid.uuid4().hex[:8]}",
        name=_join_name(pattern.component_ids, graph),
        description=(
            "Emergent join — complexity order cn="
            + str(max_level + 1)
            + " (auto-computed by build_hierarchy_to_fixpoint)"
        ),
        pillar=dominant_pillar,
        level=max_level + 1,  # preliminary; overwritten by apply_complexity_order
        pattern_ids=list(pattern.component_ids),
        metadata={
            "is_emergent_join": True,
            "pattern_id": pattern.id,
            "cn_estimate": max_level + 1,
        },
    )
    graph.add_skill(join_skill)

    # Step 3: cocone morphisms — component → join
    cocone_map: dict[str, str] = {}
    for comp_id in pattern.component_ids:
        morph = graph.add_morphism(
            comp_id,
            join_skill.id,
            morphism_type=MorphismType.DEPENDENCY,
            weight=1.0,
            metadata={"is_cocone": True, "pattern_id": pattern.id},
        )
        if morph:
            cocone_map[comp_id] = morph.id

    # Step 4: outgoing morphisms to all existing upper bounds
    # This enforces minimality: join ≤ X for every upper bound X.
    # (In the preorder, "join ≤ X" = there is a morphism join → X.)
    upper_bounds = _find_upper_bounds(
        pattern.component_ids, graph, join_skill.id
    )
    for ub_id in upper_bounds:
        if not graph.has_morphism(join_skill.id, ub_id):
            graph.add_morphism(
                join_skill.id,
                ub_id,
                morphism_type=MorphismType.DEPENDENCY,
                weight=1.0,
                metadata={"universal_mediator": True},
            )

    # Step 5: register as colimit (with verification)
    return colimit_builder._register_new_colimit(
        pattern, join_skill.id, cocone_map, graph
    )


# =============================================================================
# FIXPOINT BUILDER
# =============================================================================

def _detect_convergence_patterns(
    graph: "SkillCategory",
    pattern_manager: "PatternManager",
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

        links = []
        for pred_id in preds:
            morph = graph.get_morphism_between(pred_id, skill_id)
            if morph:
                links.append(morph.id)

        pattern = pattern_manager.create_pattern(preds, links, graph=graph)
        patterns.append(pattern)

    return patterns


def build_hierarchy_to_fixpoint(
    graph: "SkillCategory",
    pattern_manager: "PatternManager",
    colimit_builder: "ColimitBuilder",
    max_iterations: int = 20,
) -> dict[str, int]:
    """
    Build the emergent skill hierarchy iteratively until fixpoint.

    At each step:
      1. Detect convergence patterns (nodes with ≥ 2 direct predecessors).
      2. For each pattern without a registered join: find or build one.
      3. Stop when no new joins are created (fixpoint).

    Convergence patterns — not arbitrary connected components — are used
    because they correctly identify the JOIN points in the preorder:
    a node X with predecessors A, B is the join of {A, B} if X is the
    minimal element above both.  This matches the MES definition of
    complejificación (Thm 2.10).

    After fixpoint, compute cn for all skills and update skill.level
    in the graph via apply_complexity_order.

    The NUMBER OF LEVELS is not predetermined — it emerges from the
    structure of the colimit construction. The iteration terminates
    because each new join skill is strictly "above" its components
    in the preorder, so no infinite chains can form in a finite graph.

    Args:
        graph: The skill category
        pattern_manager: Detects and stores patterns
        colimit_builder: Builds and registers colimits
        max_iterations: Safety limit (default 20; depth rarely exceeds 5)

    Returns:
        dict mapping skill_id → cn (complexity order)
    """
    logger.info("build_hierarchy_to_fixpoint: starting")

    for iteration in range(max_iterations):
        # Detect convergence patterns (local join candidates)
        new_patterns = _detect_convergence_patterns(graph, pattern_manager)

        new_joins = 0
        for pattern in new_patterns:
            if colimit_builder.get_colimit_for_pattern(pattern.id) is not None:
                continue
            result = build_join_for_pattern(pattern, graph, colimit_builder)
            if result is not None:
                new_joins += 1

        logger.debug(
            f"  iter {iteration + 1}: "
            f"{len(new_patterns)} patterns, {new_joins} new joins"
        )

        if new_joins == 0:
            logger.info(
                f"build_hierarchy_to_fixpoint: fixpoint at iteration {iteration + 1}"
            )
            break
    else:
        logger.warning(
            "build_hierarchy_to_fixpoint: max_iterations reached without fixpoint"
        )

    # Compute cn and update graph
    cn = compute_complexity_order(graph, colimit_builder)
    graph.apply_complexity_order(cn)

    max_cn = max(cn.values(), default=0)
    distribution = {
        k: sum(1 for v in cn.values() if v == k)
        for k in range(max_cn + 1)
    }
    logger.info(
        f"Hierarchy built: {len(cn)} skills, "
        f"{max_cn + 1} emergent level(s), "
        f"distribution={distribution}"
    )
    return cn


# =============================================================================
# HELPERS
# =============================================================================

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
