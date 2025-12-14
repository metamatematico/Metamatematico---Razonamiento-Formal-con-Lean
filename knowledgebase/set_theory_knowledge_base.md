# Zermelo-Fraenkel Set Theory Knowledge Base for Lean 4

**Generated:** 2025-12-13
**Purpose:** Research knowledge base for implementing ZFC axioms in Lean 4 for dataset generation pairing formal proofs with natural language explanations.

---

## Overview

Zermelo-Fraenkel set theory (ZF/ZFC) provides the axiomatic foundation for virtually all of modern mathematics. This knowledge base catalogs the nine axioms that comprise ZFC plus three fundamental theorems, their formal definitions, intuitive meanings, and formalization approaches in Lean 4.

### Content Summary

| Category | Count | Description |
|----------|-------|-------------|
| **Axioms** | 9 | The foundational ZFC axioms |
| **Theorems** | 3 | Fundamental consequences (Cantor, Schroeder-Bernstein, Uncountability of ℝ) |
| **Total** | 12 | All formalized in Mathlib |

### System Variants

| System | Axioms Included | Notes |
|--------|-----------------|-------|
| **Z** (Zermelo) | 1-6, 8 | Original system, excludes Replacement |
| **ZF** (Zermelo-Fraenkel) | 1-8 | Standard foundation, excludes Choice |
| **ZFC** (with Choice) | 1-9 | Most widely used, includes Axiom of Choice |

### Mathlib Approach

Lean 4's Mathlib formalizes ZFC using a **quotient construction** over pre-sets:

```lean
-- Pre-sets: untyped, possibly non-well-founded sets
inductive PSet : Type
  | mk : (α : Type) → (α → PSet) → PSet

-- ZFC sets as quotient by extensional equivalence
def ZFSet := Quotient PSet.setoid
```

**Primary Import:** `Mathlib.SetTheory.ZFC.Basic`

---

## The Nine Axioms of ZFC

### 1. Axiom of Extensionality

**Natural Language Statement:**
Two sets are identical if and only if they contain exactly the same elements. Set identity is determined purely by membership, not by how the set is described or constructed.

**Formal Definition (First-Order Logic):**
```
∀X ∀Y [∀u(u ∈ X ⟺ u ∈ Y) ⟹ X = Y]
```

**Intuitive Explanation:**
This axiom establishes the fundamental principle that sets are completely determined by their members. For example, {1, 2, 3} = {3, 2, 1} = {1, 1, 2, 3} because all three descriptions refer to sets with identical membership. Order and repetition are irrelevant.

**Mathlib Support:** FULL
- **Key Theorem:** `ZFSet.ext_iff`
- **Import:** `Mathlib.SetTheory.ZFC.Basic`

**Difficulty:** easy

---

### 2. Axiom of Pairing

**Natural Language Statement:**
For any two sets a and b (which may be the same), there exists a set containing exactly those two elements and nothing else.

**Formal Definition (First-Order Logic):**
```
∀a ∀b ∃c ∀x [x ∈ c ⟺ (x = a ∨ x = b)]
```

**Intuitive Explanation:**
This axiom guarantees we can always form the set {a, b} from any two sets. As a special case, taking a = b gives us singleton sets {a}. This seemingly simple axiom is crucial for building ordered pairs and eventually functions.

**Mathlib Support:** FULL
- **Key Definitions:** `ZFSet.Insert`, `ZFSet.Singleton`
- **Import:** `Mathlib.SetTheory.ZFC.Basic`

**Difficulty:** easy

---

### 3. Axiom of Separation (Comprehension)

**Alternative Names:** Axiom of Subsets, Axiom Schema of Specification

**Natural Language Statement:**
Given any set X and any property φ (expressible in the language of set theory), there exists a subset of X containing precisely those elements of X that satisfy φ.

**Formal Definition (Axiom Schema):**
```
∀X ∀p ∃Y ∀u [u ∈ Y ⟺ (u ∈ X ∧ φ(u, p))]
```
where φ is a formula in the language of set theory with free variables u and p.

**Intuitive Explanation:**
This axiom allows "filtering" a set by any definable property. For example, from the set of natural numbers N, we can form the subset of even numbers using the property "n is divisible by 2." Crucially, we can only form subsets of *existing* sets - this restriction prevents Russell's paradox.

**Historical Note:**
The unrestricted comprehension axiom of naive set theory allowed forming {x : φ(x)} for any property, leading to Russell's paradox with φ(x) = "x ∉ x". Zermelo's restriction to subsets of existing sets resolves this.

**Mathlib Support:** FULL
- **Key Definition:** `ZFSet.sep`
- **Import:** `Mathlib.SetTheory.ZFC.Basic`

**Difficulty:** easy

---

### 4. Axiom of Union

**Alternative Names:** Axiom of the Sum Set

**Natural Language Statement:**
For any set X, there exists a set containing all elements that belong to at least one member of X. In other words, we can form the union ⋃X of a set of sets.

**Formal Definition (First-Order Logic):**
```
∀X ∃Y ∀u [u ∈ Y ⟺ ∃z(z ∈ X ∧ u ∈ z)]
```

**Intuitive Explanation:**
If X = {{1, 2}, {2, 3}, {4}}, then ⋃X = {1, 2, 3, 4}. We "flatten" one level of nesting by collecting all members of members. This operation is fundamental for combining sets and building larger structures.

**Mathlib Support:** FULL
- **Key Definition:** `ZFSet.sUnion`
- **Import:** `Mathlib.SetTheory.ZFC.Basic`

**Difficulty:** easy

---

### 5. Axiom of Power Set

**Natural Language Statement:**
For any set X, there exists a set containing all subsets of X (including the empty set and X itself).

**Formal Definition (First-Order Logic):**
```
∀X ∃Y ∀u [u ∈ Y ⟺ u ⊆ X]
```
where u ⊆ X means ∀v(v ∈ u ⟹ v ∈ X).

**Intuitive Explanation:**
The power set P(X) of X contains every possible subset. For example, if X = {1, 2}, then P(X) = {∅, {1}, {2}, {1, 2}}. If |X| = n, then |P(X)| = 2^n. The power set axiom is crucial for building function spaces and enables Cantor's theorem that P(X) is always strictly larger than X.

**Mathlib Support:** FULL
- **Key Definition:** `ZFSet.powerset`
- **Import:** `Mathlib.SetTheory.ZFC.Basic`

**Difficulty:** easy

---

### 6. Axiom of Infinity

**Natural Language Statement:**
There exists an infinite set. Specifically, there exists a set containing the empty set and closed under the successor operation S(x) = x ∪ {x}.

**Formal Definition (First-Order Logic):**
```
∃S [∅ ∈ S ∧ ∀x ∈ S (x ∪ {x} ∈ S)]
```

**Intuitive Explanation:**
This axiom ensures the existence of infinite sets by constructing the natural numbers via the von Neumann encoding:
- 0 = ∅
- 1 = {∅} = {0}
- 2 = {∅, {∅}} = {0, 1}
- 3 = {∅, {∅}, {∅, {∅}}} = {0, 1, 2}
- ...

The smallest set satisfying this axiom is ω, the set of all natural numbers. Without this axiom, ZF would only prove the existence of finite sets.

**Mathlib Support:** FULL
- **Key Definition:** `ZFSet.omega` (von Neumann ordinal ω)
- **Import:** `Mathlib.SetTheory.ZFC.Basic`

**Difficulty:** easy

---

### 7. Axiom Schema of Replacement

**Alternative Names:** Axiom Schema of Collection

**Natural Language Statement:**
If φ is a functional formula (relating each set x to a unique set y), then the image of any set under this "function" is also a set. In other words, applying a definable operation to all elements of a set produces a set.

**Formal Definition (Axiom Schema):**
```
∀x ∀y ∀z [φ(x, y, p) ∧ φ(x, z, p) ⟹ y = z]
  ⟹
∀X ∃Y ∀y [y ∈ Y ⟺ ∃x ∈ X φ(x, y, p)]
```
where φ is a formula with the functional property shown in the antecedent.

**Intuitive Explanation:**
If F is a definable "function" (not necessarily a set itself) and X is a set, then {F(x) : x ∈ X} is a set. This axiom is essential for transfinite recursion and building higher-order structures in set theory. It distinguishes ZF from Zermelo's original system Z.

**Historical Note:**
Added by Fraenkel and Skolem to overcome limitations in Zermelo's original system. Enables construction of large ordinals and transfinite hierarchies.

**Mathlib Support:** FULL
- **Implementation:** Implicit in `ZFSet.Definable` classes
- **Import:** `Mathlib.SetTheory.ZFC.Basic`

**Difficulty:** medium

---

### 8. Axiom of Regularity (Foundation)

**Alternative Names:** Axiom of Foundation

**Natural Language Statement:**
Every non-empty set contains an element that is disjoint from the set itself. Equivalently, there are no infinitely descending chains of membership.

**Formal Definition (First-Order Logic):**
```
∀S [S ≠ ∅ ⟹ ∃x ∈ S (S ∩ x = ∅)]
```

**Intuitive Explanation:**
This axiom prevents pathological situations like:
- Self-membership: x ∈ x is impossible
- Circular membership: x ∈ y ∧ y ∈ x is impossible
- Infinite descent: ... ∈ x₃ ∈ x₂ ∈ x₁ ∈ x₀ is impossible

It ensures that sets are "well-founded" - you can't chase the membership relation downward forever. This gives us a notion of the "rank" of a set in the cumulative hierarchy.

**Mathlib Support:** FULL
- **Key Theorem:** `ZFSet.regularity`
- **Supporting:** `ZFSet.mem_wf` (well-foundedness of membership)
- **Supporting:** `ZFSet.inductionOn` (induction principle)
- **Import:** `Mathlib.SetTheory.ZFC.Basic`

**Difficulty:** medium

---

### 9. Axiom of Choice

**Alternative Names:** AC

**Natural Language Statement:**
For any set X of non-empty sets, there exists a function (called a choice function) that selects exactly one element from each set in X.

**Formal Definition (First-Order Logic):**
```
∀X [∀a ∈ X (a ≠ ∅) ⟹ ∃f : X → ⋃X ∀a ∈ X (f(a) ∈ a)]
```

**Intuitive Explanation:**
If you have a collection of non-empty boxes, you can simultaneously pick one item from each box, even if there's no rule for making the choice. While this seems obvious for finite collections, it's highly non-constructive for infinite collections.

**Independence Results:**
- **Godel (1938):** Showed AC is consistent with ZF by constructing the constructible universe L where AC holds
- **Cohen (1963):** Showed ¬AC is consistent with ZF using forcing technique, proving independence

**Equivalent Formulations (in ZF):**
- **Zorn's Lemma:** Every partially ordered set in which every chain has an upper bound contains a maximal element
- **Well-Ordering Principle:** Every set can be well-ordered
- **Trichotomy:** For any cardinals α and β, either α ≤ β or β ≤ α

**Mathlib Support:** FULL
- **Key Theorem:** `ZFSet.choice` (proved from Lean's axiom of choice)
- **Note:** Lean's type theory includes choice by default
- **Import:** `Mathlib.SetTheory.ZFC.Basic`

**Difficulty:** hard (conceptually, due to non-constructive nature)

---

## Fundamental Theorems (Consequences of ZFC)

The following theorems are provable from the ZFC axioms and represent landmark results in set theory.

### 10. Cantor's Theorem

**100 Theorems List:** #63

**Natural Language Statement:**
For any set X, there is no surjection from X onto its power set P(X). Equivalently, the cardinality of P(X) is strictly greater than the cardinality of X.

**Formal Definition:**
```
∀X ∀f : X → P(X), ¬Surjective(f)
```

Equivalently: |X| < |P(X)| for all sets X.

**Proof Sketch (Diagonalization):**
1. Assume f : X → P(X) is surjective
2. Define D = {x ∈ X : x ∉ f(x)} (the "diagonal" set)
3. D ∈ P(X), so by surjectivity, ∃d ∈ X with f(d) = D
4. Ask: is d ∈ D?
   - If d ∈ D, then by definition d ∉ f(d) = D. Contradiction.
   - If d ∉ D, then by definition d ∈ f(d) = D. Contradiction.
5. Therefore f cannot be surjective

**Significance:**
- First proof that there are different "sizes" of infinity
- The power set operation always produces a strictly larger set
- Foundation for the hierarchy of infinite cardinals: ℵ₀ < 2^ℵ₀ < 2^(2^ℵ₀) < ...

**Mathlib Support:** FULL
- **Key Theorem:** `Function.cantor_surjective` - No surjection from type to its power type
- **Alternative:** `Cardinal.cantor` - |α| < 2^|α| for cardinals
- **Import:** `Mathlib.Logic.Function.Basic`, `Mathlib.SetTheory.Cardinal.Basic`

**Difficulty:** easy

---

### 11. Schroeder-Bernstein Theorem

**100 Theorems List:** #25

**Alternative Names:** Cantor-Bernstein-Schroeder theorem, CBS theorem

**Natural Language Statement:**
If there exist injective functions f : A → B and g : B → A between sets A and B, then there exists a bijection h : A → B. In terms of cardinality: if |A| ≤ |B| and |B| ≤ |A|, then |A| = |B|.

**Formal Definition:**
```
∀A, B : (∃f : A → B, Injective(f)) ∧ (∃g : B → A, Injective(g)) → (∃h : A → B, Bijective(h))
```

**Proof Sketch:**
1. Given injections f : A → B and g : B → A
2. Define sequences: A₀ = A \ g(B), Aₙ₊₁ = g(f(Aₙ))
3. Let A* = ⋃ₙ Aₙ (elements "originating" from A)
4. Define h : A → B by:
   - h(a) = f(a) if a ∈ A*
   - h(a) = g⁻¹(a) if a ∉ A*
5. Verify h is a bijection

**Significance:**
- Fundamental for comparing infinite cardinalities
- Does NOT require the Axiom of Choice (purely constructive)
- Establishes that cardinal comparison is antisymmetric

**Historical Note:**
Named after Ernst Schröder and Felix Bernstein. First stated by Cantor (1887), proved by Dedekind (1887, unpublished), Schröder (1898, flawed), and Bernstein (1898).

**Mathlib Support:** FULL
- **Key Theorem:** `Function.Embedding.schroeder_bernstein`
- **Statement:** Given injective f : α → β and g : β → α, produces bijection h : α → β
- **Import:** `Mathlib.SetTheory.Cardinal.SchroederBernstein`

**Difficulty:** medium

---

### 12. Non-Denumerability of the Continuum

**100 Theorems List:** #22

**Alternative Names:** Uncountability of the reals, Cantor's diagonal argument

**Natural Language Statement:**
The set of real numbers ℝ is uncountable. There is no bijection between ℕ and ℝ.

**Formal Definition:**
```
¬∃f : ℕ → ℝ, Bijective(f)
```

Equivalently: |ℕ| < |ℝ|, or ℵ₀ < 2^ℵ₀ = |ℝ|

**Proof Sketch (Cantor's Diagonal Argument, 1891):**
1. Assume f : ℕ → [0,1] is a bijection (suffices to show [0,1] is uncountable)
2. Write each f(n) as a decimal: f(n) = 0.d_{n,1}d_{n,2}d_{n,3}...
3. Construct x = 0.x₁x₂x₃... where xₙ ≠ d_{n,n} (and xₙ ∉ {0, 9} to avoid 0.999... = 1.000...)
4. Then x ∈ [0,1] but x ≠ f(n) for all n (differs at the n-th digit)
5. Contradiction: f is not surjective

**Alternative Proof (Using Cantor's Theorem):**
|ℝ| = |P(ℕ)| (via binary representations), and by Cantor's theorem |ℕ| < |P(ℕ)|.

**Significance:**
- First demonstration that not all infinite sets have the same cardinality
- ℝ has cardinality 2^ℵ₀ (the cardinality of the continuum)
- Led to the Continuum Hypothesis: Is there a cardinal strictly between ℵ₀ and 2^ℵ₀?

**Mathlib Support:** FULL
- **Key Theorem:** `Cardinal.not_countable_real` or `¬Set.Countable (Set.univ : Set ℝ)`
- **Import:** `Mathlib.Analysis.SpecificLimits.Basic`, `Mathlib.SetTheory.Cardinal.Continuum`

**Difficulty:** medium

---

## Axiom Dependencies and Relationships

### Logical Independence

The axioms are generally independent, meaning no subset of the axioms can prove another. However, there are subtle relationships:

1. **Extensionality** is foundational - it defines what equality means for sets
2. **Separation** requires existing sets to work on (uses other axioms)
3. **Replacement** strictly strengthens the system beyond axioms 1-6, 8
4. **Choice** is provably independent of axioms 1-8

### Historical Development

```
1908: Zermelo proposes axioms 1-6, 8 (system Z)
  ↓
1922: Fraenkel and Skolem independently add Replacement (axiom 7)
  ↓
Result: Zermelo-Fraenkel set theory (ZF)
  ↓
1940s: Axiom of Choice commonly added (ZFC becomes standard)
```

### System Hierarchy

```
Z ⊂ ZF ⊂ ZFC
│    │     │
│    │     └── Adds: Choice (independent)
│    └──────── Adds: Replacement (strictly stronger)
└────────────── Base: Extensionality, Pairing, Separation,
                      Union, Power Set, Infinity, Regularity
```

---

## Lean 4 Formalization Reference

### Import Statements

```lean
import Mathlib.SetTheory.ZFC.Basic      -- Core ZFC definitions
import Mathlib.SetTheory.ZFC.Class      -- Class theory
import Mathlib.SetTheory.Cardinal.Basic -- Cardinal arithmetic
```

### Key Definitions and Theorems by Axiom

| Axiom | Lean 4 Name | Type/Description |
|-------|-------------|------------------|
| Extensionality | `ZFSet.ext_iff` | Sets equal iff same members |
| Pairing | `ZFSet.Insert`, `ZFSet.Singleton` | Pair and singleton construction |
| Separation | `ZFSet.sep` | Subset by predicate |
| Union | `ZFSet.sUnion` | Set union ⋃ |
| Power Set | `ZFSet.powerset` | Power set P(X) |
| Infinity | `ZFSet.omega` | Von Neumann ordinal ω |
| Replacement | `ZFSet.Definable` | Definable functions |
| Regularity | `ZFSet.regularity`, `ZFSet.mem_wf` | Well-foundedness |
| Choice | `ZFSet.choice` | Choice function existence |

### Additional Components

- **Function representation:** `ZFSet.IsFunc` predicate
- **Class theory:** `Mathlib.SetTheory.ZFC.Class`
- **Ordinals:** Von Neumann ordinals formalized
- **Cardinals:** `Mathlib.SetTheory.Cardinal.Basic`

---

## Implementation Priority

### Phase 1: Axiom Statements (Easy)

Add all 9 axioms as theorem records with `proof_status: "unproven"` (axioms are assumptions, not proved):

| Axiom | `theorem_id` | Mathlib Reference |
|-------|--------------|-------------------|
| Extensionality | `zfc_extensionality` | `ZFSet.ext_iff` |
| Pairing | `zfc_pairing` | `ZFSet.Insert` |
| Separation | `zfc_separation` | `ZFSet.sep` |
| Union | `zfc_union` | `ZFSet.sUnion` |
| Power Set | `zfc_powerset` | `ZFSet.powerset` |
| Infinity | `zfc_infinity` | `ZFSet.omega` |
| Replacement | `zfc_replacement` | `ZFSet.Definable` |
| Regularity | `zfc_regularity` | `ZFSet.regularity` |
| Choice | `zfc_choice` | `ZFSet.choice` |

### Phase 2: Basic Consequences (Medium)

Lemmas derivable directly from axioms:

| Lemma | Description | Dependencies |
|-------|-------------|--------------|
| Empty set unique | There is exactly one set with no elements | Extensionality |
| Singleton existence | {a} exists for any set a | Pairing |
| Ordered pair | (a, b) = {{a}, {a, b}} is a set | Pairing |
| Binary union | A ∪ B exists | Union, Pairing |
| ω is ordinal | Natural numbers form an ordinal | Infinity |
| No self-membership | x ∉ x for all x | Regularity |

### Phase 3: Advanced Results (Hard)

| Theorem | Description | Key Technique |
|---------|-------------|---------------|
| Cantor's theorem | |P(X)| > |X| | Power Set, diagonalization |
| Schroder-Bernstein | A ≤ B ∧ B ≤ A ⟹ A ≃ B | (Does not require Choice) |
| Well-ordering theorem | Every set can be well-ordered | Choice |
| Zorn's lemma | Maximal elements in chains | Choice |

---

## Dataset Integration

### Example Theorem Record

```json
{
  "theorem_id": "zfc_extensionality",
  "mathematical_domain": "SetTheory",
  "theorem_name": "Axiom of Extensionality",
  "nl_statement": "Two sets are equal if and only if they have exactly the same elements.",
  "lean_statement": "axiom ZFSet.ext : ∀ (x y : ZFSet), (∀ z, z ∈ x ↔ z ∈ y) → x = y",
  "lean_proof_term": null,
  "lean_proof_tactic": null,
  "imports": ["Mathlib.SetTheory.ZFC.Basic"],
  "difficulty": "easy",
  "mathlib_support": "full",
  "reasoning_trace": {
    "mathematical_insight": "Set identity is determined purely by membership. This is the fundamental principle distinguishing sets from other mathematical objects.",
    "key_lemmas": ["ZFSet.ext_iff"],
    "proof_strategy": "Axiom - no proof required",
    "common_pitfalls": []
  },
  "proof_status": "unproven",
  "schema_version": "2.0.0"
}
```

### Example Lemma Record

```json
{
  "lemma_id": "empty_set_unique",
  "theorem_id": "zfc_extensionality",
  "lemma_name": "Empty Set is Unique",
  "nl_statement": "There is exactly one set with no elements.",
  "lean_statement": "theorem empty_unique : ∀ (x y : ZFSet), (∀ z, z ∉ x) → (∀ z, z ∉ y) → x = y",
  "lean_proof_term": "fun x y hx hy => ZFSet.ext x y (fun z => ⟨fun h => absurd h (hx z), fun h => absurd h (hy z)⟩)",
  "lean_proof_tactic": "by intro x y hx hy; exact ZFSet.ext x y (fun z => ⟨fun h => absurd h (hx z), fun h => absurd h (hy z)⟩)",
  "depends_on_lemmas": [],
  "imports": ["Mathlib.SetTheory.ZFC.Basic"],
  "proof_status": "complete",
  "schema_version": "2.0.0"
}
```

---

## References

### Primary Sources

- [Wikipedia: Zermelo-Fraenkel set theory](https://en.wikipedia.org/wiki/Zermelo%E2%80%93Fraenkel_set_theory)
- [Wikipedia: Cantor's theorem](https://en.wikipedia.org/wiki/Cantor%27s_theorem)
- [Wikipedia: Schröder-Bernstein theorem](https://en.wikipedia.org/wiki/Schr%C3%B6der%E2%80%93Bernstein_theorem)
- [Wikipedia: Cantor's diagonal argument](https://en.wikipedia.org/wiki/Cantor%27s_diagonal_argument)
- [Wolfram MathWorld: Zermelo-Fraenkel Axioms](https://mathworld.wolfram.com/Zermelo-FraenkelAxioms.html)
- [Stanford Encyclopedia of Philosophy: Set Theory](https://plato.stanford.edu/entries/set-theory/ZF.html)

### Lean 4 / Mathlib

- [Mathlib4 Docs: SetTheory.ZFC.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/SetTheory/ZFC/Basic.html)
- [Mathlib4 Docs: SetTheory.Cardinal.SchroederBernstein](https://leanprover-community.github.io/mathlib4_docs/Mathlib/SetTheory/Cardinal/SchroederBernstein.html)
- [Mathlib4 Docs: Logic.Function.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Logic/Function/Basic.html)
- [Mathlib4 GitHub: ZFC/Basic.lean](https://github.com/leanprover-community/mathlib4/blob/master/Mathlib/SetTheory/ZFC/Basic.lean)
- [100 Theorems in Lean](https://leanprover-community.github.io/100.html)

### Historical

- Zermelo, E. (1908). "Untersuchungen uber die Grundlagen der Mengenlehre I"
- Fraenkel, A. (1922). "Zu den Grundlagen der Cantor-Zermeloschen Mengenlehre"
- Cantor, G. (1891). "Über eine elementare Frage der Mannigfaltigkeitslehre" (diagonal argument)
- Godel, K. (1938). Consistency of AC with ZF
- Cohen, P. (1963). Independence of AC from ZF (Fields Medal work)

---

**End of Knowledge Base**
