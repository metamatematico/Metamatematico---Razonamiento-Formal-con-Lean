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
    # Terminos (ES + EN) para emparejar consultas con esta skill. Los nombres
    # e IDs estan en ingles, asi que sin esto ninguna consulta en español
    # encuentra la skill y el grafo de la vista Visual sale equivocado.
    keywords: list[str] = field(default_factory=list)


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


# -- Lean Tactics (9 skills) ------------------------------------------------

# Las tacticas dependen de `cic` + `lean-kernel`, que son las skills
# fundacionales reales de core._load_foundational_skills(). Antes ponia
# "type-theory", un nombre que no existe: el cargador descartaba las 9 tacticas
# y, en cascada, 5 de las 6 estrategias — los "14 skipped" que aparecian en
# cada arranque. Sin ellas el grafo no tenia capa tactica y `suggested_tactics`
# salia siempre vacio en el prompt del LLM.
LEAN_TACTICS_SKILLS = [
    DomainSkillDef(
        id="tactic-simp", name="Simplification",
        description="simp, simp_all, norm_num — automated simplification",
        pillar=PillarType.TYPE, level=1,
        dependencies=["cic", "lean-kernel"],
        category="lean-tactics",
    ),
    DomainSkillDef(
        id="tactic-rewrite", name="Rewriting",
        description="rw, conv, simp with lemmas — term rewriting",
        pillar=PillarType.TYPE, level=1,
        dependencies=["cic", "lean-kernel"],
        category="lean-tactics",
    ),
    DomainSkillDef(
        id="tactic-exact", name="Exact Proof",
        description="exact, refine, use — provide exact proof terms",
        pillar=PillarType.TYPE, level=1,
        dependencies=["cic", "lean-kernel"],
        category="lean-tactics",
    ),
    DomainSkillDef(
        id="tactic-apply", name="Apply Rule",
        description="apply, have, suffices — rule application and intermediate goals",
        pillar=PillarType.TYPE, level=1,
        dependencies=["cic", "lean-kernel"],
        category="lean-tactics",
    ),
    DomainSkillDef(
        id="tactic-induction", name="Induction",
        description="induction, cases, rcases — structural induction and case analysis",
        pillar=PillarType.TYPE, level=1,
        dependencies=["cic", "lean-kernel"],
        category="lean-tactics",
    ),
    DomainSkillDef(
        id="tactic-omega", name="Arithmetic",
        description="omega, linarith, norm_num — linear arithmetic decision procedures",
        pillar=PillarType.TYPE, level=1,
        dependencies=["cic", "lean-kernel"],
        category="lean-tactics",
    ),
    DomainSkillDef(
        id="tactic-ring", name="Ring Algebra",
        description="ring, ring_nf, field_simp — algebraic normalization",
        pillar=PillarType.TYPE, level=1,
        dependencies=["cic", "lean-kernel"],
        category="lean-tactics",
    ),
    DomainSkillDef(
        id="tactic-aesop", name="Automation",
        description="aesop, decide, tauto — automated proof search",
        pillar=PillarType.TYPE, level=1,
        dependencies=["cic", "lean-kernel"],
        category="lean-tactics",
    ),
    DomainSkillDef(
        id="tactic-calc", name="Calculation",
        description="calc blocks — step-by-step equational reasoning",
        pillar=PillarType.TYPE, level=1,
        dependencies=["cic", "lean-kernel"],
        category="lean-tactics",
    ),
]


# -- Proof Strategies (6 skills) --------------------------------------------

PROOF_STRATEGY_SKILLS = [
    DomainSkillDef(
        id="strategy-backward", name="Backward Reasoning",
        description="Goal-directed reasoning, working from conclusion to hypotheses",
        pillar=PillarType.LOG, level=2,
        dependencies=["tactic-apply", "tactic-exact"],
        category="proof-strategies",
    ),
    DomainSkillDef(
        id="strategy-forward", name="Forward Reasoning",
        description="Hypothesis-driven reasoning, deriving consequences toward goal",
        pillar=PillarType.LOG, level=2,
        dependencies=["tactic-apply", "tactic-rewrite"],
        category="proof-strategies",
    ),
    DomainSkillDef(
        id="strategy-contradiction", name="Contradiction",
        description="by_contra, absurd — proof by contradiction or contrapositive",
        pillar=PillarType.LOG, level=2,
        dependencies=["tactic-exact", "fol-deduction"],
        category="proof-strategies",
    ),
    DomainSkillDef(
        id="strategy-cases", name="Case Analysis",
        description="Split on disjunctions, exhaustive case enumeration",
        pillar=PillarType.LOG, level=2,
        dependencies=["tactic-induction", "tactic-simp"],
        category="proof-strategies",
    ),
    DomainSkillDef(
        id="strategy-inductive", name="Inductive Proof",
        description="Induction pattern: establish base case, prove inductive step",
        pillar=PillarType.LOG, level=2,
        dependencies=["tactic-induction", "tactic-simp"],
        category="proof-strategies",
    ),
    DomainSkillDef(
        id="strategy-construction", name="Construction",
        description="Exhibit witness or construct object satisfying goal",
        pillar=PillarType.LOG, level=2,
        dependencies=["tactic-exact", "tactic-apply"],
        category="proof-strategies",
    ),
]


# =========================================================================
# ALL DOMAIN SKILLS
# =========================================================================

# -- Sub-ramas (nivel 3) ----------------------------------------------------
# Granularidad fina dentro de cada campo. Los `keywords` se comparan como
# palabra completa, asi que las variantes (singular/plural, ES/EN) van
# explicitas: es lo que permite que "homomorfismo" encuentre la skill.

def _sb(id, name, desc, deps, cat, kw, pillar=PillarType.SET, level=3):
    return DomainSkillDef(id=id, name=name, description=desc, pillar=pillar,
                          level=level, dependencies=deps, category=cat,
                          keywords=kw)


SUBBRANCH_SKILLS = [
    # ---- Algebra lineal (faltaba por completo) ----------------------------
    _sb("linear-algebra", "Linear Algebra",
        "Vector spaces, linear maps, matrices, determinants, rank",
        ["zfc-axioms"], "algebra",
        ["algebra lineal", "lineal", "vectorial", "vector", "vectores",
         "matriz", "matrices", "determinante", "determinantes", "rango",
         "linear", "matrix", "determinant"], level=1),
    _sb("eigen-theory", "Eigenvalues and Eigenvectors",
        "Eigenvalues, eigenvectors, diagonalization, characteristic polynomial",
        ["linear-algebra"], "algebra",
        ["autovalor", "autovalores", "autovector", "autovectores",
         "valor propio", "valores propios", "diagonalizacion", "diagonalizable",
         "eigenvalue", "eigenvalues", "eigenvector", "eigenvectors"]),
    _sb("canonical-forms", "Canonical Forms",
        "Jordan normal form, rational canonical form, invariant factors",
        ["eigen-theory"], "algebra",
        ["jordan", "forma canonica", "formas canonicas", "canonical form"]),
    _sb("inner-product-spaces", "Inner Product Spaces",
        "Inner products, orthogonality, Gram-Schmidt, spectral theorem",
        ["linear-algebra"], "algebra",
        ["producto interior", "producto interno", "ortogonal", "ortogonalidad",
         "ortonormal", "gram-schmidt", "inner product", "orthogonal"]),
    _sb("bilinear-forms", "Bilinear and Quadratic Forms",
        "Bilinear forms, quadratic forms, signature, Sylvester's law",
        ["linear-algebra"], "algebra",
        ["forma bilineal", "formas bilineales", "forma cuadratica",
         "formas cuadraticas", "bilinear", "quadratic form", "sylvester"]),

    # ---- Teoria de grupos -------------------------------------------------
    _sb("subgroups-cosets", "Subgroups and Cosets",
        "Subgroups, cosets, index, Lagrange's theorem",
        ["group-theory"], "algebra",
        ["subgrupo", "subgrupos", "clase lateral", "clases laterales",
         "coclase", "lagrange", "indice", "subgroup", "subgroups", "coset",
         "cosets"]),
    _sb("group-homomorphisms", "Group Homomorphisms",
        "Homomorphisms, kernel, image, the isomorphism theorems",
        ["group-theory"], "algebra",
        ["homomorfismo", "homomorfismos", "isomorfismo", "isomorfismos",
         "nucleo", "kernel", "imagen", "epimorfismo", "monomorfismo",
         "endomorfismo", "automorfismo",
         "homomorphism", "homomorphisms", "isomorphism", "isomorphisms",
         "image"]),
    _sb("quotient-groups", "Quotient Groups",
        "Normal subgroups, quotient groups, correspondence theorem",
        ["group-homomorphisms"], "algebra",
        ["cociente", "cocientes", "grupo cociente", "grupos cociente",
         "subgrupo normal", "subgrupos normales", "quotient", "quotients"]),
    _sb("group-actions", "Group Actions",
        "Actions, orbits, stabilizers, orbit-stabilizer, Burnside's lemma",
        ["group-theory"], "algebra",
        ["accion", "acciones", "orbita", "orbitas", "estabilizador",
         "burnside", "action", "actions", "orbit", "orbits", "stabilizer"]),
    _sb("sylow-theory", "Sylow Theory",
        "p-groups, Sylow's theorems, classification of finite groups",
        ["group-actions"], "algebra",
        ["sylow", "p-grupo", "p-grupos", "p-group"]),
    _sb("abelian-groups", "Abelian Groups",
        "Structure theorem for finitely generated abelian groups",
        ["group-theory"], "algebra",
        ["abeliano", "abeliana", "abelianos", "conmutativo", "abelian"]),
    _sb("free-groups", "Free Groups and Presentations",
        "Free groups, generators and relations, group presentations",
        ["group-theory"], "algebra",
        ["grupo libre", "grupos libres", "generadores", "presentacion",
         "free group", "generators", "presentation"]),
    _sb("solvable-groups", "Solvable and Nilpotent Groups",
        "Solvable, nilpotent, composition series, Jordan-Holder theorem",
        ["quotient-groups"], "algebra",
        ["soluble", "resoluble", "nilpotente", "serie de composicion",
         "jordan-holder", "solvable", "nilpotent"]),

    # ---- Teoria de anillos ------------------------------------------------
    _sb("ideals-quotient-rings", "Ideals and Quotient Rings",
        "Ideals, quotient rings, prime and maximal ideals",
        ["ring-theory"], "algebra",
        ["ideal", "ideales", "ideal primo", "ideal maximal", "anillo cociente",
         "ideals", "prime ideal", "maximal ideal"]),
    _sb("polynomial-rings", "Polynomial Rings",
        "Polynomial rings, division algorithm, Gauss's lemma, irreducibility",
        ["ring-theory"], "algebra",
        ["polinomio", "polinomios", "polinomial", "irreducible",
         "eisenstein", "polynomial", "polynomials"]),
    _sb("unique-factorization", "Unique Factorization Domains",
        "UFDs, PIDs, Euclidean domains, unique factorization",
        ["ideals-quotient-rings"], "algebra",
        ["factorizacion", "factorizacion unica", "dfu", "dip", "euclideo",
         "dominio euclideo", "ufd", "pid", "factorization"]),
    _sb("localization", "Localization",
        "Localization, local rings, field of fractions",
        ["ideals-quotient-rings"], "algebra",
        ["localizacion", "anillo local", "cuerpo de fracciones",
         "localization", "local ring"]),
    _sb("noetherian-rings", "Noetherian and Artinian Rings",
        "Noetherian and Artinian conditions, Hilbert basis theorem",
        ["ideals-quotient-rings"], "algebra",
        ["noetheriano", "artiniano", "hilbert", "noetherian", "artinian"]),

    # ---- Teoria de cuerpos ------------------------------------------------
    _sb("field-extensions", "Field Extensions",
        "Algebraic and transcendental extensions, degree, tower law",
        ["field-theory"], "algebra",
        ["extension", "extensiones", "extension de cuerpos", "grado",
         "algebraico", "trascendente", "field extension", "degree"]),
    _sb("galois-theory", "Galois Theory",
        "Galois groups, fundamental theorem, solvability by radicals",
        ["field-extensions", "solvable-groups"], "algebra",
        ["galois", "radicales", "resoluble por radicales", "solvability"]),
    _sb("finite-fields", "Finite Fields",
        "Finite fields, Frobenius endomorphism, existence and uniqueness",
        ["field-extensions"], "algebra",
        ["cuerpo finito", "cuerpos finitos", "campo finito", "frobenius",
         "finite field", "finite fields"]),
    _sb("splitting-fields", "Splitting Fields and Algebraic Closure",
        "Splitting fields, algebraic closure, separability, normality",
        ["field-extensions"], "algebra",
        ["cuerpo de descomposicion", "clausura algebraica", "separable",
         "splitting field", "algebraic closure"]),

    # ---- Modulos y homologica ---------------------------------------------
    _sb("exact-sequences", "Exact Sequences",
        "Exact sequences, five lemma, snake lemma, splitting",
        ["module-theory"], "algebra",
        ["sucesion exacta", "sucesiones exactas", "secuencia exacta",
         "lema de la serpiente", "exact sequence", "snake lemma"]),
    _sb("tensor-products", "Tensor Products",
        "Tensor products, bilinear maps, base change, flatness",
        ["module-theory"], "algebra",
        ["producto tensorial", "productos tensoriales", "tensor", "tensorial",
         "tensor product"]),
    _sb("projective-injective-modules", "Projective and Injective Modules",
        "Free, projective, injective and flat modules, resolutions",
        ["module-theory"], "algebra",
        ["proyectivo", "inyectivo", "modulo libre", "resolucion",
         "projective", "injective", "resolution"]),
    _sb("character-theory", "Character Theory",
        "Characters of representations, orthogonality relations",
        ["representation-theory"], "algebra",
        ["caracter", "caracteres", "tabla de caracteres", "character",
         "characters"]),

    # ---- Teoria de numeros ------------------------------------------------
    _sb("divisibility-gcd", "Divisibility and GCD",
        "Divisibility, gcd and lcm, Bezout's identity, Euclidean algorithm",
        ["elementary-number-theory"], "number-theory",
        # La paridad es divisibilidad por 2: se indexa aqui. Se evita el termino
        # suelto "par" (colisiona con "un par de ..."); "pares"/"impar" bastan.
        ["divisibilidad", "divisor", "divisores", "multiplo", "mcd", "mcm",
         "maximo comun divisor", "bezout", "euclides", "algoritmo de euclides",
         "divisibility", "gcd", "lcm", "euclidean algorithm",
         "pares", "impar", "impares", "paridad", "numero par", "numero impar",
         "even", "odd", "parity"]),
    _sb("prime-factorization", "Prime Factorization",
        "Primes, the fundamental theorem of arithmetic, sieves",
        ["divisibility-gcd"], "number-theory",
        ["primo", "primos", "numero primo", "numeros primos", "factorizacion",
         "criba", "eratostenes", "aritmetica", "prime", "primes",
         "fundamental theorem of arithmetic", "sieve"]),
    _sb("modular-arithmetic", "Modular Arithmetic",
        "Congruences, Chinese remainder theorem, Fermat and Euler theorems",
        ["divisibility-gcd"], "number-theory",
        ["congruencia", "congruencias", "modular", "modulo", "resto",
         "teorema chino", "fermat", "euler", "congruence", "modular arithmetic",
         "chinese remainder"]),
    _sb("diophantine-equations", "Diophantine Equations",
        "Linear and Pell equations, integer solutions, descent",
        ["modular-arithmetic"], "number-theory",
        ["diofantica", "diofanticas", "diofantina", "pell", "descenso",
         "diophantine"]),
    _sb("quadratic-residues", "Quadratic Residues",
        "Legendre symbol, quadratic reciprocity, Jacobi symbol",
        ["modular-arithmetic"], "number-theory",
        ["residuo cuadratico", "residuos cuadraticos", "legendre",
         "reciprocidad", "jacobi", "quadratic residue", "reciprocity"]),
    _sb("number-fields", "Number Fields",
        "Number fields, rings of integers, discriminants, units",
        ["algebraic-number-theory", "field-extensions"], "number-theory",
        ["cuerpo de numeros", "cuerpos de numeros", "anillo de enteros",
         "discriminante", "number field", "ring of integers"]),
    _sb("ideal-class-group", "Ideal Class Group",
        "Class groups, unique factorization of ideals, Dedekind domains",
        ["number-fields"], "number-theory",
        ["grupo de clases", "clase de ideales", "dedekind", "class group"]),
    _sb("p-adic-valuations", "p-adic Numbers and Valuations",
        "p-adic numbers, valuations, local fields, Hensel's lemma",
        ["number-fields"], "number-theory",
        ["p-adico", "p-adicos", "valuacion", "valuaciones", "hensel",
         "cuerpo local", "p-adic", "valuation"]),
    _sb("prime-number-theorem", "Prime Number Theorem",
        "PNT, Chebyshev bounds, zero-free regions, prime counting",
        ["analytic-number-theory"], "number-theory",
        ["teorema de los numeros primos", "chebyshev", "distribucion de primos",
         "prime number theorem"]),
    _sb("riemann-zeta", "Riemann Zeta and L-functions",
        "Riemann zeta, Dirichlet series, Euler products, functional equation",
        ["analytic-number-theory"], "number-theory",
        ["zeta", "riemann", "dirichlet", "funcion l", "producto de euler",
         "hipotesis de riemann", "l-function"]),

    # ---- Analisis real ----------------------------------------------------
    _sb("sequences-series", "Sequences and Series",
        "Convergence, Cauchy sequences, series tests, power series",
        ["real-analysis"], "analysis",
        ["sucesion", "sucesiones", "serie", "series", "convergencia",
         "convergente", "divergente", "cauchy", "serie de potencias",
         "sequence", "sequences", "convergence"]),
    _sb("limits-continuity", "Limits and Continuity",
        "Limits, continuity, uniform continuity, intermediate value theorem",
        ["real-analysis"], "analysis",
        ["limite", "limites", "continuidad", "continua", "continuo",
         "uniformemente continua", "bolzano", "limit", "continuity",
         "continuous"]),
    _sb("differentiation", "Differentiation",
        "Derivatives, mean value theorem, Taylor's theorem, L'Hopital",
        ["limits-continuity"], "analysis",
        ["derivada", "derivadas", "derivable", "diferenciable",
         "valor medio", "taylor", "lhopital", "derivative", "differentiable"]),
    _sb("riemann-integration", "Riemann Integration",
        "Riemann integral, fundamental theorem of calculus",
        ["limits-continuity"], "analysis",
        ["integral", "integrales", "integracion", "riemann", "primitiva",
         "teorema fundamental del calculo", "integration"]),
    _sb("metric-spaces", "Metric Spaces",
        "Metric spaces, completeness, Baire category, contraction mapping",
        ["real-analysis"], "analysis",
        ["espacio metrico", "espacios metricos", "metrica", "completitud",
         "completo", "baire", "banach fijo", "metric space", "completeness"]),
    _sb("measure-theory", "Measure Theory",
        "Sigma-algebras, measures, measurable functions, Borel sets",
        ["real-analysis"], "analysis",
        ["medida", "medidas", "sigma-algebra", "medible", "borel",
         "lebesgue", "measure", "measurable"]),
    _sb("lebesgue-integration", "Lebesgue Integration",
        "Lebesgue integral, convergence theorems, Lp spaces, Fubini",
        ["measure-theory"], "analysis",
        ["integral de lebesgue", "convergencia dominada", "fatou", "fubini",
         "espacios lp", "lebesgue integral"]),

    # ---- Analisis complejo y funcional ------------------------------------
    _sb("holomorphic-functions", "Holomorphic Functions",
        "Cauchy-Riemann equations, analyticity, power series expansions",
        ["complex-analysis"], "analysis",
        ["holomorfa", "holomorfas", "analitica", "cauchy-riemann",
         "holomorphic", "analytic"]),
    _sb("contour-integration", "Contour Integration",
        "Cauchy's theorem and formula, Morera, Liouville, maximum modulus",
        ["holomorphic-functions"], "analysis",
        ["contorno", "integral de contorno", "cauchy", "liouville", "morera",
         "contour"]),
    _sb("residue-theorem", "Residue Theorem",
        "Residues, poles, argument principle, Rouche's theorem",
        ["contour-integration"], "analysis",
        ["residuo", "residuos", "polo", "polos", "rouche", "residue",
         "residues", "pole"]),
    _sb("conformal-maps", "Conformal Mappings",
        "Conformal maps, Mobius transformations, Riemann mapping theorem",
        ["holomorphic-functions"], "analysis",
        ["conforme", "conformes", "mobius", "aplicacion conforme",
         "conformal"]),
    _sb("banach-spaces", "Banach Spaces",
        "Banach spaces, Hahn-Banach, open mapping, closed graph theorems",
        ["functional-analysis"], "analysis",
        ["banach", "hahn-banach", "espacio normado", "norma", "normed"]),
    _sb("hilbert-spaces", "Hilbert Spaces",
        "Hilbert spaces, orthonormal bases, Riesz representation",
        ["functional-analysis"], "analysis",
        ["hilbert", "riesz", "base ortonormal", "espacio de hilbert"]),
    _sb("spectral-theory", "Spectral Theory",
        "Spectrum, compact and self-adjoint operators, spectral theorem",
        ["hilbert-spaces"], "analysis",
        ["espectro", "espectral", "autoadjunto", "operador compacto",
         "spectrum", "spectral", "self-adjoint"]),

    # ---- Topologia --------------------------------------------------------
    _sb("compactness", "Compactness",
        "Compact spaces, Heine-Borel, Tychonoff, local compactness",
        ["point-set-topology"], "topology",
        ["compacto", "compacta", "compacidad", "heine-borel", "tychonoff",
         "compact", "compactness"]),
    _sb("connectedness", "Connectedness",
        "Connected and path-connected spaces, components",
        ["point-set-topology"], "topology",
        ["conexo", "conexa", "conexidad", "arcoconexo", "componente conexa",
         "connected", "connectedness"]),
    _sb("separation-axioms", "Separation Axioms",
        "Hausdorff, regular, normal spaces, Urysohn's lemma",
        ["point-set-topology"], "topology",
        ["hausdorff", "separacion", "axioma de separacion", "urysohn",
         "espacio regular", "espacio normal", "separation"]),
    _sb("fundamental-group", "Fundamental Group",
        "The fundamental group, homotopy of paths, van Kampen theorem",
        ["algebraic-topology"], "topology",
        ["grupo fundamental", "van kampen", "lazo", "camino",
         "fundamental group"]),
    _sb("covering-spaces", "Covering Spaces",
        "Covering maps, deck transformations, universal cover",
        ["fundamental-group"], "topology",
        ["recubrimiento", "revestimiento", "espacio recubridor",
         "covering space", "deck transformation"]),
    _sb("homology", "Homology",
        "Singular and simplicial homology, Mayer-Vietoris, Euler characteristic",
        ["algebraic-topology", "exact-sequences"], "topology",
        ["homologia", "homologico", "mayer-vietoris", "caracteristica de euler",
         "homology"]),
    _sb("cohomology", "Cohomology",
        "Cohomology, cup product, Poincare duality, de Rham",
        ["homology"], "topology",
        ["cohomologia", "producto cup", "poincare", "de rham", "cohomology"]),

    # ---- Geometria --------------------------------------------------------
    _sb("smooth-manifolds", "Smooth Manifolds",
        "Charts, atlases, smooth maps, tangent and cotangent bundles",
        ["differential-geometry"], "geometry",
        ["variedad", "variedades", "carta", "atlas", "tangente", "fibrado",
         "manifold", "manifolds", "tangent bundle"]),
    _sb("riemannian-geometry", "Riemannian Geometry",
        "Riemannian metrics, geodesics, curvature, Levi-Civita connection",
        ["smooth-manifolds"], "geometry",
        ["riemanniana", "metrica riemanniana", "geodesica", "geodesicas",
         "curvatura", "conexion", "riemannian", "geodesic", "curvature"]),
    _sb("differential-forms", "Differential Forms",
        "Differential forms, exterior derivative, Stokes' theorem",
        ["smooth-manifolds"], "geometry",
        ["forma diferencial", "formas diferenciales", "derivada exterior",
         "stokes", "differential form"]),
    _sb("affine-varieties", "Affine Varieties",
        "Affine varieties, Nullstellensatz, coordinate rings, Zariski topology",
        ["algebraic-geometry", "ideals-quotient-rings"], "geometry",
        ["variedad afin", "variedades afines", "nullstellensatz", "zariski",
         "affine variety"]),
    _sb("projective-varieties", "Projective Varieties",
        "Projective space, homogeneous ideals, Bezout's theorem",
        ["affine-varieties"], "geometry",
        ["variedad proyectiva", "espacio proyectivo", "bezout",
         "projective variety"]),
    _sb("schemes", "Schemes",
        "Schemes, sheaves, morphisms of schemes, spectra of rings",
        ["projective-varieties"], "geometry",
        ["esquema", "esquemas", "haz", "haces", "gavilla", "espectro",
         "scheme", "schemes", "sheaf"]),
    _sb("triangle-geometry", "Triangle Geometry",
        "Congruence, similarity, Pythagorean theorem, classical centres",
        ["euclidean-geometry"], "geometry",
        ["triangulo", "triangulos", "congruencia", "semejanza", "pitagoras",
         "hipotenusa", "baricentro", "triangle", "pythagorean"]),
    _sb("circle-geometry", "Circle Geometry",
        "Circles, inscribed angles, power of a point, cyclic quadrilaterals",
        ["euclidean-geometry"], "geometry",
        ["circulo", "circunferencia", "angulo inscrito", "cuerda", "tangente",
         "circle", "inscribed angle"]),

    # ---- Teoria de categorias ---------------------------------------------
    _sb("yoneda-lemma", "Yoneda Lemma",
        "The Yoneda embedding and lemma, representable functors",
        ["functors"], "category-theory",
        ["yoneda", "representable", "encaje de yoneda"],
        pillar=PillarType.CAT),
    _sb("adjunctions", "Adjunctions",
        "Adjoint functors, unit and counit, free-forgetful adjunctions",
        ["functors"], "category-theory",
        ["adjuncion", "adjunciones", "adjunto", "adjunta", "adjoint",
         "adjunction"],
        pillar=PillarType.CAT),
    _sb("universal-properties", "Universal Properties",
        "Universal properties, representability, uniqueness up to isomorphism",
        ["limits"], "category-theory",
        ["propiedad universal", "propiedades universales", "universal property"],
        pillar=PillarType.CAT),
    _sb("monads", "Monads",
        "Monads, algebras over a monad, Kleisli and Eilenberg-Moore categories",
        ["adjunctions"], "category-theory",
        ["monada", "monadas", "kleisli", "eilenberg-moore", "monad", "monads"],
        pillar=PillarType.CAT),
    _sb("abelian-categories", "Abelian Categories",
        "Additive and abelian categories, kernels, cokernels, exactness",
        ["limits", "exact-sequences"], "category-theory",
        ["categoria abeliana", "categorias abelianas", "aditiva", "conucleo",
         "abelian category"],
        pillar=PillarType.CAT),
    _sb("kan-extensions", "Kan Extensions",
        "Left and right Kan extensions, ends and coends",
        ["adjunctions"], "category-theory",
        ["extension de kan", "extensiones de kan", "kan"],
        pillar=PillarType.CAT),
    _sb("topos-theory", "Topos Theory",
        "Elementary topoi, subobject classifier, internal logic",
        ["adjunctions"], "category-theory",
        ["topos", "clasificador de subobjetos", "logica interna"],
        pillar=PillarType.CAT),

    # ---- Logica y fundamentos ---------------------------------------------
    _sb("compactness-theorem", "Compactness and Lowenheim-Skolem",
        "Compactness theorem, Lowenheim-Skolem theorems, elementary embeddings",
        ["model-theory"], "logic",
        ["compacidad", "lowenheim", "skolem", "modelo", "modelos",
         "compactness theorem"],
        pillar=PillarType.LOG),
    _sb("ultraproducts", "Ultraproducts",
        "Ultrafilters, ultraproducts, Los's theorem",
        ["compactness-theorem"], "logic",
        ["ultrafiltro", "ultrafiltros", "ultraproducto", "ultraproductos",
         "ultraproduct", "teorema de los"],
        pillar=PillarType.LOG),
    _sb("sequent-calculus", "Sequent Calculus",
        "Sequent calculus, natural deduction, cut elimination",
        ["proof-theory"], "logic",
        ["secuente", "secuentes", "deduccion natural", "eliminacion de corte",
         "sequent", "cut elimination"],
        pillar=PillarType.LOG),
    _sb("incompleteness", "Godel Incompleteness",
        "Godel numbering, first and second incompleteness theorems",
        ["proof-theory"], "logic",
        ["incompletitud", "godel", "goedel", "indecidible", "consistencia",
         "incompleteness", "undecidable"],
        pillar=PillarType.LOG),
    _sb("cardinal-arithmetic", "Cardinal Arithmetic",
        "Cardinals, cofinality, continuum hypothesis, cardinal exponentiation",
        ["zfc-axioms"], "set-theory",
        ["cardinal", "cardinales", "cardinalidad", "cofinalidad",
         "hipotesis del continuo", "cardinality"]),
    _sb("forcing", "Forcing",
        "Forcing, generic extensions, independence results",
        ["cardinal-arithmetic"], "set-theory",
        ["forcing", "forzamiento", "independencia", "extension generica"]),
    _sb("large-cardinals", "Large Cardinals",
        "Inaccessible, measurable and other large cardinal axioms",
        ["cardinal-arithmetic"], "set-theory",
        ["cardinal grande", "cardinales grandes", "inaccesible", "medible",
         "large cardinal"]),

    # ---- Combinatoria -----------------------------------------------------
    _sb("generating-functions", "Generating Functions",
        "Ordinary and exponential generating functions, recurrences",
        ["enumerative-combinatorics"], "combinatorics",
        ["funcion generatriz", "funciones generatrices", "recurrencia",
         "generating function"]),
    _sb("inclusion-exclusion", "Inclusion-Exclusion",
        "Inclusion-exclusion principle, derangements, Mobius inversion",
        ["enumerative-combinatorics"], "combinatorics",
        ["inclusion-exclusion", "desarreglo", "desarreglos", "mobius",
         "inclusion exclusion"]),
    _sb("partitions", "Integer Partitions",
        "Integer partitions, Young diagrams, partition identities",
        ["enumerative-combinatorics"], "combinatorics",
        ["particion", "particiones", "young", "partition", "partitions"]),
    _sb("graph-coloring", "Graph Coloring",
        "Chromatic number, four colour theorem, chromatic polynomial",
        ["graph-theory"], "combinatorics",
        ["coloracion", "cromatico", "numero cromatico", "cuatro colores",
         "coloring", "chromatic"]),
    _sb("matching-theory", "Matching Theory",
        "Matchings, Hall's marriage theorem, Konig's theorem, flows",
        ["graph-theory"], "combinatorics",
        ["emparejamiento", "apareamiento", "hall", "konig", "flujo",
         "matching", "matchings"]),
    _sb("planar-graphs", "Planar Graphs",
        "Planarity, Euler's formula, Kuratowski's theorem",
        ["graph-theory"], "combinatorics",
        ["planar", "grafo planar", "kuratowski", "formula de euler"]),

    # ---- Probabilidad -----------------------------------------------------
    _sb("random-variables", "Random Variables",
        "Random variables, distributions, expectation, variance, independence",
        ["probability-theory"], "probability",
        ["variable aleatoria", "variables aleatorias", "esperanza", "varianza",
         "distribucion", "independencia", "random variable", "expectation"]),
    _sb("limit-theorems", "Limit Theorems",
        "Laws of large numbers, central limit theorem, characteristic functions",
        ["random-variables"], "probability",
        ["ley de los grandes numeros", "teorema central del limite",
         "funcion caracteristica", "central limit theorem"]),
    _sb("conditional-expectation", "Conditional Expectation",
        "Conditioning, conditional expectation, filtrations",
        ["random-variables", "measure-theory"], "probability",
        ["esperanza condicional", "condicionada", "filtracion",
         "conditional expectation"]),
    _sb("markov-chains", "Markov Chains",
        "Markov chains, transition matrices, stationary distributions",
        ["stochastic-processes"], "probability",
        ["markov", "cadena de markov", "cadenas de markov", "estacionaria",
         "markov chain"]),
    _sb("brownian-motion", "Brownian Motion",
        "Brownian motion, Ito calculus, stochastic differential equations",
        ["stochastic-processes"], "probability",
        ["browniano", "movimiento browniano", "ito", "wiener",
         "brownian motion"]),

    # ---- Computacion ------------------------------------------------------
    _sb("turing-machines", "Turing Machines",
        "Turing machines, the halting problem, Church-Turing thesis",
        ["computability-theory"], "computation",
        ["turing", "maquina de turing", "problema de la parada", "church",
         "halting problem"],
        pillar=PillarType.TYPE),
    _sb("recursion-theory", "Recursion Theory",
        "Recursive and recursively enumerable sets, Turing degrees",
        ["turing-machines"], "computation",
        ["recursivo", "recursividad", "grado de turing", "recursion theory"],
        pillar=PillarType.TYPE),
    _sb("np-completeness", "NP-Completeness",
        "P vs NP, polynomial reductions, Cook-Levin theorem",
        ["computational-complexity"], "computation",
        ["np", "np-completo", "npcompleto", "reduccion", "cook", "levin",
         "np-complete", "np-completeness"],
        pillar=PillarType.TYPE),
    _sb("lambda-calculus", "Lambda Calculus",
        "Untyped and typed lambda calculus, beta reduction, normalization",
        ["cic"], "computation",
        ["lambda", "calculo lambda", "beta", "normalizacion",
         "lambda calculus"],
        pillar=PillarType.TYPE),

    # ---- Optimizacion -----------------------------------------------------
    _sb("linear-programming", "Linear Programming",
        "Linear programs, simplex method, LP duality",
        ["convex-optimization"], "optimization",
        ["programacion lineal", "simplex", "linear programming"]),
    _sb("duality-theory", "Duality Theory",
        "Lagrangian duality, KKT conditions, strong duality",
        ["convex-optimization"], "optimization",
        ["dualidad", "lagrangiano", "kkt", "duality"]),
]


ALL_DOMAIN_SKILLS: list[DomainSkillDef] = (
    ALGEBRA_SKILLS
    + SUBBRANCH_SKILLS
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
    + LEAN_TACTICS_SKILLS
    + PROOF_STRATEGY_SKILLS
)

# Terminos ES+EN para las skills originales (L1-L2), que se definieron sin
# `keywords`. Sin esto solo las 96 sub-ramas eran localizables y consultas
# corrientes como "raiz de 2 irracional" o "numero complejo" dejaban el
# contexto del grafo completamente vacio en el prompt.
# Se aplica en load_math_domains() y NO pisa los keywords ya declarados.
EXTRA_KEYWORDS: dict[str, list[str]] = {
    # Algebra
    "group-theory":       ["grupo", "grupos", "group", "groups"],
    "ring-theory":        ["anillo", "anillos", "ring", "rings"],
    "field-theory":       ["cuerpo", "cuerpos", "campo", "campos", "field"],
    "module-theory":      ["modulo", "modulos", "module", "modules"],
    "commutative-algebra": ["algebra conmutativa", "conmutativa"],
    "representation-theory": ["representacion", "representaciones",
                              "representation"],
    "homological-algebra": ["algebra homologica", "homologica"],
    # Analisis
    "real-analysis":      ["analisis real", "real", "reales", "irracional",
                           "irracionales", "racional", "racionales",
                           "raiz cuadrada", "supremo", "infimo", "irrational"],
    "complex-analysis":   ["complejo", "complejos", "numero complejo",
                           "imaginario", "complex"],
    "functional-analysis": ["analisis funcional", "funcional", "functional"],
    "harmonic-analysis":  ["fourier", "armonico", "harmonic", "wavelet"],
    "operator-theory":    ["operador", "operadores", "operator"],
    "pde-techniques":     ["ecuacion en derivadas parciales", "edp", "pde"],
    # Geometria
    "euclidean-geometry": ["euclidiana", "euclides", "euclidean", "angulo",
                           "angulos", "grados"],
    "projective-geometry": ["proyectiva", "projective"],
    "differential-geometry": ["geometria diferencial", "green", "stokes",
                              "divergencia", "rotacional", "flujo"],
    "algebraic-geometry": ["geometria algebraica"],
    "complex-geometry":   ["geometria compleja", "kahler"],
    "symplectic-geometry": ["simplectica", "symplectic", "hamiltoniano"],
    # Topologia
    "point-set-topology": ["topologia", "topologico", "topologica", "abierto",
                           "cerrado", "entorno", "topology"],
    "algebraic-topology": ["topologia algebraica"],
    "differential-topology": ["topologia diferencial"],
    "geometric-topology": ["topologia geometrica", "nudo", "nudos", "knot"],
    "homotopy-theory":    ["homotopia", "homotopy"],
    # Logica y conjuntos
    "model-theory":       ["teoria de modelos", "modelo", "modelos",
                           "satisfacibilidad", "model theory"],
    "proof-theory":       ["teoria de la demostracion", "demostracion",
                           "prueba", "proof theory"],
    "homotopy-type-theory": ["hott", "univalencia", "univalence"],
    "descriptive-set-theory": ["conjunto", "conjuntos", "numerable",
                               "contable", "no numerable", "axioma de eleccion",
                               "eleccion", "zorn", "set", "countable"],
    # Numeros
    "elementary-number-theory": ["teoria de numeros", "entero", "enteros",
                                 "number theory", "integer"],
    "algebraic-number-theory": ["teoria algebraica de numeros"],
    "analytic-number-theory": ["teoria analitica de numeros"],
    "arithmetic-geometry": ["geometria aritmetica", "curva eliptica",
                            "elliptic curve"],
    # Combinatoria
    "enumerative-combinatorics": ["combinatoria", "binomio", "binomial",
                                  "newton", "combinacion", "combinaciones",
                                  "permutacion", "permutaciones", "factorial",
                                  "combinatorics"],
    "graph-theory":       ["grafo", "grafos", "vertice", "arista", "graph"],
    "extremal-combinatorics": ["combinatoria extremal", "extremal"],
    "ramsey-theory":      ["ramsey"],
    "probabilistic-method": ["metodo probabilistico"],
    "algebraic-combinatorics": ["combinatoria algebraica"],
    # Probabilidad
    "probability-theory": ["probabilidad", "aleatorio", "aleatoria",
                           "probability"],
    "stochastic-processes": ["proceso estocastico", "estocastico",
                             "stochastic"],
    "martingale-theory":  ["martingala", "martingale"],
    "ergodic-theory":     ["ergodico", "ergodica", "ergodic"],
    # Categorias
    "higher-category-theory": ["categoria superior", "infinito-categoria",
                               "n-categoria"],
    "homological-algebra-cat": ["categoria derivada", "derived category"],
    # Computacion
    "computability-theory": ["computabilidad", "decidible", "indecidible",
                             "computability"],
    "computational-complexity": ["complejidad", "complexity"],
    "algorithm-analysis": ["algoritmo", "algoritmos", "algorithm"],
    "formal-verification": ["verificacion formal", "verification"],
    # Optimizacion
    "convex-optimization": ["optimizacion", "convexo", "convexa", "convex"],
    "discrete-optimization": ["optimizacion discreta", "entera"],
    "variational-methods": ["variacional", "variational", "euler-lagrange"],
}


# Tactica Lean por defecto de cada area matematica.
#
# Espeja CATEGORY_DEFAULT_TACTICS de multi_agent/colimit_agents.py, pero
# apuntando a las skills que EXISTEN en el grafo: los nombres sueltos del
# diccionario original ("norm_num", "linarith", "decide", "tauto") no son
# nodos, sino tacticas documentadas dentro de tactic-omega y tactic-aesop.
#
# Por que importa: ese conocimiento vivia en un diccionario de Python, al lado
# del grafo y no dentro. `_find_relevant_context` recorre vecinos, y como
# ningun morfismo unia un dominio con su tactica, `suggested_tactics` salia
# vacio en todos los prompts. Con estos morfismos el saber pasa a circular por
# la estructura categorica, que es lo que el paper afirma.
#
# El tipo es TRANSLATION y no DEPENDENCY a proposito: las tacticas son del
# pilar TYPE y los dominios de SET/CAT/LOG, asi que el morfismo cruza pilares
# (Definicion 4.2: TRANSLATION = transformacion entre pilares fundacionales).
CATEGORY_TACTIC_SKILL: dict[str, str] = {
    "algebra":         "tactic-ring",    # ring, ring_nf, field_simp
    "analysis":        "tactic-omega",   # norm_num, linarith
    "category-theory": "tactic-simp",
    "combinatorics":   "tactic-omega",   # omega
    "computation":     "tactic-aesop",   # decide
    "geometry":        "tactic-omega",   # norm_num
    "logic":           "tactic-aesop",   # tauto
    "number-theory":   "tactic-omega",   # norm_num
    "optimization":    "tactic-omega",   # linarith
    "probability":     "tactic-omega",   # norm_num
    "set-theory":      "tactic-simp",
    "topology":        "tactic-simp",
}


# Inter-pillar translation morphisms between domain skills
INTER_PILLAR_TRANSLATIONS = [
    # -- Orden faltante entre teorias de nivel medio (revision 2026-08-21) ----
    # Solo aristas inequivocas: el algebra homologica es prerrequisito real de
    # la (co)homologia y de su version categorica. Se anaden como DEPENDENCY
    # porque son relaciones de ORDEN (teoria ⊃ subteoria), no traducciones.
    #
    # NO se anaden aristas para "cerrar" los huecos [module+ring theory] ni
    # [functors+module theory]: exigirian commutative-algebra <= tensor-products
    # o homological-algebra <= abelian-categories, que son FALSAS (los productos
    # tensoriales y las categorias abelianas son mas primitivos). Esos huecos
    # son genuinos: el patron no tiene minima cota superior porque la matematica
    # se ramifica ahi. Forzarlos seria justo el error que se elimino de
    # build_join_for_pattern.
    ("homological-algebra", "cohomology", MorphismType.DEPENDENCY,
     {"relation": "derived-functors-give-cohomology"}),
    ("homological-algebra", "homology", MorphismType.DEPENDENCY,
     {"relation": "chain-complexes-give-homology"}),
    ("homological-algebra", "homological-algebra-cat", MorphismType.DEPENDENCY,
     {"relation": "module-version-precedes-categorical-version"}),
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
    # Lean Tactics <-> Proof Strategies
    ("tactic-apply", "strategy-backward", MorphismType.DEPENDENCY,
     {"relation": "apply-enables-backward-reasoning"}),
    ("tactic-induction", "strategy-inductive", MorphismType.DEPENDENCY,
     {"relation": "induction-tactic-enables-inductive-strategy"}),
    ("strategy-contradiction", "proof-theory", MorphismType.ANALOGY,
     {"analogy": "contradiction-as-proof-theoretic-method"}),
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
            metadata={
                "category": sdef.category,
                # Los keywords propios mandan; EXTRA_KEYWORDS solo rellena las
                # definiciones antiguas que se escribieron sin ellos.
                "keywords": sdef.keywords or EXTRA_KEYWORDS.get(sdef.id, []),
            },
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

    # Conectar cada skill de dominio con la tactica Lean por defecto de su area.
    # Sin estos morfismos el grafo tiene capa tactica pero nadie llega a ella:
    # `_find_relevant_context` mira los vecinos de las skills que casan con la
    # consulta, y ninguno era una tactica.
    tactic_links = 0
    for sdef in ALL_DOMAIN_SKILLS:
        tactic_id = CATEGORY_TACTIC_SKILL.get(sdef.category)
        if not tactic_id or sdef.id == tactic_id:
            continue
        if sdef.id in existing_ids and tactic_id in existing_ids:
            result = graph.add_morphism(
                sdef.id, tactic_id, MorphismType.TRANSLATION,
                metadata={"translation": "area-to-default-tactic"},
            )
            if result:
                tactic_links += 1

    return {
        "added": added,
        "skipped": skipped,
        "translations": translations,
        "tactic_links": tactic_links,
    }
