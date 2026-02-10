"""
Mathematical Domain Skills
==========================

Higher-level mathematical domain skills (levels 1-2) that build on
the foundational pillar skills (level 0).

Adapted from the lean-proving-skills library which covers 13 categories
of mathematical knowledge for Lean 4 proof automation.

Categories:
  Algebra, Geometry, Analysis, Topology, Logic, Number Theory,
  Combinatorics, Probability, Set Theory, Category Theory,
  Computation, Optimization

Each skill is assigned:
  - A primary pillar (SET, CAT, LOG, TYPE)
  - A hierarchical level (1 = basic domain, 2 = advanced/cross-domain)
  - Dependencies on foundational pillar skills (level 0)
  - Dependencies on other domain skills where applicable
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from nucleo.types import Skill, MorphismType, PillarType
from nucleo.graph.category import SkillCategory


# =========================================================================
# SKILL DEFINITIONS
# =========================================================================

@dataclass
class DomainSkillDef:
    """Definition of a mathematical domain skill."""
    id: str
    name: str
    description: str
    pillar: PillarType
    level: int
    dependencies: list[str] = field(default_factory=list)
    category: str = ""


# -- Algebra (7 skills) ---------------------------------------------------

ALGEBRA_SKILLS = [
    DomainSkillDef(
        id="group-theory", name="Group Theory",
        description="Groups, subgroups, homomorphisms, Sylow theorems, classification",
        pillar=PillarType.SET, level=1,
        dependencies=["zfc-axioms"],
        category="algebra",
    ),
    DomainSkillDef(
        id="ring-theory", name="Ring Theory",
        description="Rings, ideals, quotients, PIDs, UFDs, polynomial rings",
        pillar=PillarType.SET, level=1,
        dependencies=["zfc-axioms", "group-theory"],
        category="algebra",
    ),
    DomainSkillDef(
        id="field-theory", name="Field Theory",
        description="Field extensions, Galois theory, algebraic closure, splitting fields",
        pillar=PillarType.SET, level=1,
        dependencies=["ring-theory"],
        category="algebra",
    ),
    DomainSkillDef(
        id="module-theory", name="Module Theory",
        description="Modules, exact sequences, tensor products, flatness",
        pillar=PillarType.SET, level=1,
        dependencies=["ring-theory"],
        category="algebra",
    ),
    DomainSkillDef(
        id="commutative-algebra", name="Commutative Algebra",
        description="Noetherian rings, localization, primary decomposition, Krull dimension",
        pillar=PillarType.SET, level=1,
        dependencies=["ring-theory", "module-theory"],
        category="algebra",
    ),
    DomainSkillDef(
        id="homological-algebra", name="Homological Algebra",
        description="Chain complexes, derived functors, Ext, Tor, spectral sequences",
        pillar=PillarType.CAT, level=2,
        dependencies=["module-theory", "functors"],
        category="algebra",
    ),
    DomainSkillDef(
        id="representation-theory", name="Representation Theory",
        description="Group representations, characters, Schur's lemma, Maschke's theorem",
        pillar=PillarType.SET, level=2,
        dependencies=["group-theory", "module-theory"],
        category="algebra",
    ),
]

# -- Geometry (6 skills) --------------------------------------------------

GEOMETRY_SKILLS = [
    DomainSkillDef(
        id="euclidean-geometry", name="Euclidean Geometry",
        description="Metric spaces, inner product spaces, convexity, classical constructions",
        pillar=PillarType.SET, level=1,
        dependencies=["zfc-axioms"],
        category="geometry",
    ),
    DomainSkillDef(
        id="projective-geometry", name="Projective Geometry",
        description="Projective spaces, duality, cross-ratio, homogeneous coordinates",
        pillar=PillarType.SET, level=1,
        dependencies=["euclidean-geometry"],
        category="geometry",
    ),
    DomainSkillDef(
        id="differential-geometry", name="Differential Geometry",
        description="Manifolds, tangent bundles, connections, curvature, Riemannian geometry",
        pillar=PillarType.SET, level=2,
        dependencies=["real-analysis", "point-set-topology"],
        category="geometry",
    ),
    DomainSkillDef(
        id="algebraic-geometry", name="Algebraic Geometry",
        description="Varieties, schemes, sheaves, cohomology, divisors",
        pillar=PillarType.CAT, level=2,
        dependencies=["commutative-algebra", "functors"],
        category="geometry",
    ),
    DomainSkillDef(
        id="symplectic-geometry", name="Symplectic Geometry",
        description="Symplectic manifolds, Hamiltonian mechanics, moment maps",
        pillar=PillarType.SET, level=2,
        dependencies=["differential-geometry", "real-analysis"],
        category="geometry",
    ),
    DomainSkillDef(
        id="complex-geometry", name="Complex Geometry",
        description="Complex manifolds, Kahler geometry, Hodge theory",
        pillar=PillarType.SET, level=2,
        dependencies=["complex-analysis", "differential-geometry"],
        category="geometry",
    ),
]

# -- Analysis (6 skills) --------------------------------------------------

ANALYSIS_SKILLS = [
    DomainSkillDef(
        id="real-analysis", name="Real Analysis",
        description="Limits, continuity, differentiation, integration, measure theory",
        pillar=PillarType.SET, level=1,
        dependencies=["zfc-axioms"],
        category="analysis",
    ),
    DomainSkillDef(
        id="complex-analysis", name="Complex Analysis",
        description="Holomorphic functions, Cauchy theory, residues, conformal maps",
        pillar=PillarType.SET, level=1,
        dependencies=["real-analysis"],
        category="analysis",
    ),
    DomainSkillDef(
        id="functional-analysis", name="Functional Analysis",
        description="Banach/Hilbert spaces, bounded operators, spectral theory, distributions",
        pillar=PillarType.SET, level=2,
        dependencies=["real-analysis", "point-set-topology"],
        category="analysis",
    ),
    DomainSkillDef(
        id="harmonic-analysis", name="Harmonic Analysis",
        description="Fourier analysis, singular integrals, Littlewood-Paley, wavelets",
        pillar=PillarType.SET, level=2,
        dependencies=["real-analysis", "functional-analysis"],
        category="analysis",
    ),
    DomainSkillDef(
        id="pde-techniques", name="PDE Techniques",
        description="Elliptic/parabolic/hyperbolic PDEs, Sobolev spaces, weak solutions",
        pillar=PillarType.SET, level=2,
        dependencies=["real-analysis", "functional-analysis"],
        category="analysis",
    ),
    DomainSkillDef(
        id="operator-theory", name="Operator Theory",
        description="Bounded/unbounded operators, C*-algebras, von Neumann algebras",
        pillar=PillarType.CAT, level=2,
        dependencies=["functional-analysis", "functors"],
        category="analysis",
    ),
]

# -- Topology (5 skills) --------------------------------------------------

TOPOLOGY_SKILLS = [
    DomainSkillDef(
        id="point-set-topology", name="Point-Set Topology",
        description="Topological spaces, compactness, connectedness, separation axioms",
        pillar=PillarType.SET, level=1,
        dependencies=["zfc-axioms"],
        category="topology",
    ),
    DomainSkillDef(
        id="algebraic-topology", name="Algebraic Topology",
        description="Fundamental group, homology, cohomology, exact sequences",
        pillar=PillarType.CAT, level=2,
        dependencies=["point-set-topology", "functors"],
        category="topology",
    ),
    DomainSkillDef(
        id="differential-topology", name="Differential Topology",
        description="Smooth manifolds, transversality, Morse theory, cobordism",
        pillar=PillarType.SET, level=2,
        dependencies=["point-set-topology", "differential-geometry"],
        category="topology",
    ),
    DomainSkillDef(
        id="homotopy-theory", name="Homotopy Theory",
        description="Homotopy groups, fibrations, cofibrations, model categories",
        pillar=PillarType.CAT, level=2,
        dependencies=["algebraic-topology", "functors"],
        category="topology",
    ),
    DomainSkillDef(
        id="geometric-topology", name="Geometric Topology",
        description="3-manifolds, knot theory, surgery theory, mapping class groups",
        pillar=PillarType.SET, level=2,
        dependencies=["point-set-topology", "algebraic-topology"],
        category="topology",
    ),
]

# -- Logic (3 new skills) -------------------------------------------------
# (mathematical-logic and type-theory already covered by pillar level-0)

LOGIC_SKILLS = [
    DomainSkillDef(
        id="model-theory", name="Model Theory",
        description="Structures, elementary equivalence, ultraproducts, types, stability",
        pillar=PillarType.LOG, level=1,
        dependencies=["fol-metatheory"],
        category="logic",
    ),
    DomainSkillDef(
        id="proof-theory", name="Proof Theory",
        description="Cut elimination, ordinal analysis, proof complexity, normalization",
        pillar=PillarType.LOG, level=1,
        dependencies=["fol-deduction"],
        category="logic",
    ),
    DomainSkillDef(
        id="homotopy-type-theory", name="Homotopy Type Theory",
        description="Univalence axiom, higher inductive types, synthetic homotopy theory",
        pillar=PillarType.TYPE, level=2,
        dependencies=["cic", "homotopy-theory"],
        category="logic",
    ),
]

# -- Number Theory (4 skills) ---------------------------------------------

NUMBER_THEORY_SKILLS = [
    DomainSkillDef(
        id="elementary-number-theory", name="Elementary Number Theory",
        description="Divisibility, primes, congruences, quadratic reciprocity",
        pillar=PillarType.SET, level=1,
        dependencies=["zfc-axioms"],
        category="number-theory",
    ),
    DomainSkillDef(
        id="algebraic-number-theory", name="Algebraic Number Theory",
        description="Number fields, rings of integers, ideals, class groups, Dirichlet units",
        pillar=PillarType.SET, level=2,
        dependencies=["ring-theory", "field-theory"],
        category="number-theory",
    ),
    DomainSkillDef(
        id="analytic-number-theory", name="Analytic Number Theory",
        description="Zeta functions, L-functions, prime number theorem, sieve methods",
        pillar=PillarType.SET, level=2,
        dependencies=["complex-analysis", "elementary-number-theory"],
        category="number-theory",
    ),
    DomainSkillDef(
        id="arithmetic-geometry", name="Arithmetic Geometry",
        description="Elliptic curves, modular forms, Langlands program, etale cohomology",
        pillar=PillarType.SET, level=2,
        dependencies=["algebraic-geometry", "algebraic-number-theory", "field-theory"],
        category="number-theory",
    ),
]

# -- Combinatorics (6 skills) ---------------------------------------------

COMBINATORICS_SKILLS = [
    DomainSkillDef(
        id="enumerative-combinatorics", name="Enumerative Combinatorics",
        description="Counting, generating functions, inclusion-exclusion, Polya theory",
        pillar=PillarType.SET, level=1,
        dependencies=["zfc-axioms"],
        category="combinatorics",
    ),
    DomainSkillDef(
        id="graph-theory", name="Graph Theory",
        description="Graph coloring, planarity, matching, flow, spectral graph theory",
        pillar=PillarType.SET, level=1,
        dependencies=["zfc-axioms"],
        category="combinatorics",
    ),
    DomainSkillDef(
        id="ramsey-theory", name="Ramsey Theory",
        description="Ramsey numbers, Hales-Jewett, Szemeredi regularity",
        pillar=PillarType.SET, level=2,
        dependencies=["enumerative-combinatorics", "graph-theory"],
        category="combinatorics",
    ),
    DomainSkillDef(
        id="extremal-combinatorics", name="Extremal Combinatorics",
        description="Turan-type problems, extremal graph/set theory, VC dimension",
        pillar=PillarType.SET, level=2,
        dependencies=["graph-theory"],
        category="combinatorics",
    ),
    DomainSkillDef(
        id="algebraic-combinatorics", name="Algebraic Combinatorics",
        description="Symmetric functions, Young tableaux, matroids, posets",
        pillar=PillarType.SET, level=2,
        dependencies=["group-theory", "enumerative-combinatorics"],
        category="combinatorics",
    ),
    DomainSkillDef(
        id="probabilistic-method", name="Probabilistic Method",
        description="Lovasz Local Lemma, second moment method, entropy method",
        pillar=PillarType.SET, level=2,
        dependencies=["probability-theory", "enumerative-combinatorics"],
        category="combinatorics",
    ),
]

# -- Probability (4 skills) -----------------------------------------------

PROBABILITY_SKILLS = [
    DomainSkillDef(
        id="probability-theory", name="Probability Theory",
        description="Measure-theoretic probability, convergence, CLT, large deviations",
        pillar=PillarType.SET, level=1,
        dependencies=["real-analysis"],
        category="probability",
    ),
    DomainSkillDef(
        id="stochastic-processes", name="Stochastic Processes",
        description="Brownian motion, Markov chains, Poisson processes, Ito calculus",
        pillar=PillarType.SET, level=2,
        dependencies=["probability-theory"],
        category="probability",
    ),
    DomainSkillDef(
        id="martingale-theory", name="Martingale Theory",
        description="Martingale convergence, optional stopping, Doob inequalities",
        pillar=PillarType.SET, level=2,
        dependencies=["probability-theory"],
        category="probability",
    ),
    DomainSkillDef(
        id="ergodic-theory", name="Ergodic Theory",
        description="Ergodic theorems, mixing, entropy, symbolic dynamics",
        pillar=PillarType.SET, level=2,
        dependencies=["probability-theory", "point-set-topology"],
        category="probability",
    ),
]

# -- Set Theory (1 new skill) ---------------------------------------------
# (axiomatic-set-theory, ordinals-cardinals, forcing already at level 0)

SET_THEORY_SKILLS = [
    DomainSkillDef(
        id="descriptive-set-theory", name="Descriptive Set Theory",
        description="Borel/analytic sets, determinacy, large cardinals, Polish spaces",
        pillar=PillarType.SET, level=1,
        dependencies=["ordinals", "point-set-topology"],
        category="set-theory",
    ),
]

# -- Category Theory (2 new skills) ---------------------------------------
# (category basics through topos already at level 0)

CATEGORY_THEORY_SKILLS = [
    DomainSkillDef(
        id="higher-category-theory", name="Higher Category Theory",
        description="2-categories, bicategories, infinity-categories, quasi-categories",
        pillar=PillarType.CAT, level=2,
        dependencies=["functors", "nat-trans"],
        category="category-theory",
    ),
    DomainSkillDef(
        id="homological-algebra-cat", name="Categorical Homological Algebra",
        description="Abelian categories, derived categories, triangulated categories",
        pillar=PillarType.CAT, level=2,
        dependencies=["functors", "limits"],
        category="category-theory",
    ),
]

# -- Computation (4 skills) -----------------------------------------------

COMPUTATION_SKILLS = [
    DomainSkillDef(
        id="computability-theory", name="Computability Theory",
        description="Turing machines, recursive functions, halting problem, degrees",
        pillar=PillarType.LOG, level=1,
        dependencies=["fol-metatheory"],
        category="computation",
    ),
    DomainSkillDef(
        id="computational-complexity", name="Computational Complexity",
        description="P, NP, PSPACE, circuit complexity, communication complexity",
        pillar=PillarType.LOG, level=1,
        dependencies=["computability-theory"],
        category="computation",
    ),
    DomainSkillDef(
        id="algorithm-analysis", name="Algorithm Analysis",
        description="Correctness proofs, termination, amortized analysis, data structures",
        pillar=PillarType.TYPE, level=1,
        dependencies=["cic"],
        category="computation",
    ),
    DomainSkillDef(
        id="formal-verification", name="Formal Verification",
        description="Program logics, Hoare logic, separation logic, refinement types",
        pillar=PillarType.TYPE, level=1,
        dependencies=["lean-kernel"],
        category="computation",
    ),
]

# -- Optimization (3 skills) ----------------------------------------------

OPTIMIZATION_SKILLS = [
    DomainSkillDef(
        id="convex-optimization", name="Convex Optimization",
        description="Convex sets/functions, duality, KKT conditions, interior point methods",
        pillar=PillarType.SET, level=1,
        dependencies=["real-analysis"],
        category="optimization",
    ),
    DomainSkillDef(
        id="discrete-optimization", name="Discrete Optimization",
        description="Integer programming, network flow, submodular functions, matroids",
        pillar=PillarType.SET, level=1,
        dependencies=["graph-theory", "enumerative-combinatorics"],
        category="optimization",
    ),
    DomainSkillDef(
        id="variational-methods", name="Variational Methods",
        description="Calculus of variations, Euler-Lagrange, Gamma-convergence",
        pillar=PillarType.SET, level=2,
        dependencies=["functional-analysis", "pde-techniques", "real-analysis"],
        category="optimization",
    ),
]


# =========================================================================
# ALL DOMAIN SKILLS
# =========================================================================

ALL_DOMAIN_SKILLS: list[DomainSkillDef] = (
    ALGEBRA_SKILLS
    + GEOMETRY_SKILLS
    + ANALYSIS_SKILLS
    + TOPOLOGY_SKILLS
    + LOGIC_SKILLS
    + NUMBER_THEORY_SKILLS
    + COMBINATORICS_SKILLS
    + PROBABILITY_SKILLS
    + SET_THEORY_SKILLS
    + CATEGORY_THEORY_SKILLS
    + COMPUTATION_SKILLS
    + OPTIMIZATION_SKILLS
)

# Inter-pillar translation morphisms between domain skills
INTER_PILLAR_TRANSLATIONS = [
    # Algebra <-> Category Theory
    ("homological-algebra", "algebraic-topology", MorphismType.ANALOGY,
     {"analogy": "homology-in-algebra-and-topology"}),
    ("homological-algebra", "homological-algebra-cat", MorphismType.TRANSLATION,
     {"translation": "module-to-abelian-category"}),
    # Geometry <-> Category Theory
    ("algebraic-geometry", "homological-algebra-cat", MorphismType.DEPENDENCY,
     {"relation": "sheaf-cohomology-via-derived-categories"}),
    # Topology <-> Type Theory
    ("homotopy-theory", "homotopy-type-theory", MorphismType.TRANSLATION,
     {"translation": "spaces-as-types"}),
    # Analysis <-> Category Theory
    ("operator-theory", "homological-algebra-cat", MorphismType.ANALOGY,
     {"analogy": "operator-algebras-categorical-structure"}),
    # Logic <-> Type Theory
    ("proof-theory", "algorithm-analysis", MorphismType.TRANSLATION,
     {"translation": "proofs-as-programs"}),
    ("model-theory", "computability-theory", MorphismType.ANALOGY,
     {"analogy": "definability-computability"}),
    # Number Theory cross-connections
    ("arithmetic-geometry", "algebraic-topology", MorphismType.ANALOGY,
     {"analogy": "etale-cohomology"}),
    # Combinatorics <-> Algebra
    ("algebraic-combinatorics", "representation-theory", MorphismType.ANALOGY,
     {"analogy": "symmetric-group-representations"}),
]


# =========================================================================
# LOADING FUNCTION
# =========================================================================

def get_domain_skill_count() -> int:
    """Return the total number of domain skills."""
    return len(ALL_DOMAIN_SKILLS)


def get_domain_categories() -> dict[str, int]:
    """Return skill count by category."""
    cats: dict[str, int] = {}
    for s in ALL_DOMAIN_SKILLS:
        cats[s.category] = cats.get(s.category, 0) + 1
    return cats


def load_math_domains(graph: SkillCategory) -> dict[str, int]:
    """
    Load all mathematical domain skills into a SkillCategory.

    Only adds skills whose dependencies are already present in the graph.
    Skills are added in topological order (level 1 first, then level 2)
    so that intra-domain dependencies resolve correctly.

    Args:
        graph: The SkillCategory to populate.

    Returns:
        Dict with counts: added, skipped, translations.
    """
    existing_ids = set(graph._skills.keys())
    added = 0
    skipped = 0

    # Sort by level to ensure dependencies are added before dependents
    sorted_skills = sorted(ALL_DOMAIN_SKILLS, key=lambda s: s.level)

    for sdef in sorted_skills:
        if sdef.id in existing_ids:
            skipped += 1
            continue

        # Check that at least one dependency exists (graceful degradation)
        has_dep = not sdef.dependencies or any(
            d in existing_ids for d in sdef.dependencies
        )
        if not has_dep:
            skipped += 1
            continue

        skill = Skill(
            id=sdef.id,
            name=sdef.name,
            description=sdef.description,
            pillar=sdef.pillar,
            level=sdef.level,
            metadata={"category": sdef.category},
        )
        graph.add_skill(skill)
        existing_ids.add(sdef.id)

        # Add dependency morphisms
        for dep_id in sdef.dependencies:
            if dep_id in existing_ids:
                graph.add_morphism(dep_id, sdef.id, MorphismType.DEPENDENCY)

        added += 1

    # Add inter-pillar translations
    translations = 0
    for src, tgt, mtype, meta in INTER_PILLAR_TRANSLATIONS:
        if src in existing_ids and tgt in existing_ids:
            result = graph.add_morphism(src, tgt, mtype, metadata=meta)
            if result:
                translations += 1

    return {"added": added, "skipped": skipped, "translations": translations}
