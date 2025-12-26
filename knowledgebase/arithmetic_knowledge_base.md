# Foundational Arithmetic Knowledge Base for Lean 4

**Generated:** 2025-12-13
**Purpose:** Research knowledge base for implementing arithmetic axioms in Lean 4 for dataset generation pairing formal proofs with natural language explanations.

---

## Overview

This knowledge base catalogs the axiomatic foundations for the fundamental number systems: natural numbers (ℕ), integers (ℤ), rational numbers (ℚ), and real numbers (ℝ). Each system builds on its predecessor through rigorous mathematical construction, plus four fundamental theorems that demonstrate key properties of these number systems.

### Content Summary

| Category | Count | Description |
|----------|-------|-------------|
| **Peano Axioms** | 5 | Foundation for ℕ |
| **Ring Axioms** | 7 | Structure of ℤ |
| **Field Axioms** | 9 | Structure of ℚ |
| **Real Axioms** | 14 | Complete ordered field ℝ |
| **Theorems** | 4 | Well-ordering, √2 irrational, ℚ denumerable, Archimedean |
| **Total** | 39 | All formalized in Mathlib |

### Number System Hierarchy

```
N (Peano axioms)
  |  embedding
  v
Z (ring axioms)
  |  quotient construction
  v
Q (field axioms)
  |  completion (Cauchy sequences)
  v
R (complete ordered field)
```

### Quick Reference

| System | Key Structure | Axiom Count | Lean 4 Type |
|--------|--------------|-------------|-------------|
| **N** | Peano axioms | 5 | `Nat` |
| **Z** | Commutative ring | 7 | `Int` |
| **Q** | Field | 9 | `Rat` |
| **R** | Complete ordered field | 14 | `Real` |

---

## Related Knowledge Bases

### Prerequisites
- **Logic & Model Theory** (`logic_model_theory_knowledge_base.md`): First-order logic, axiomatics
- **Set Theory** (`set_theory_knowledge_base.md`): Set-theoretic foundations

### Builds Upon This KB
- **Real/Complex Analysis** (`real_complex_analysis_knowledge_base.md`): Analysis on ℝ and ℂ
- **Measure Theory** (`measure_theory_knowledge_base.md`): Lebesgue measure on ℝ
- **Galois Theory** (`galois_theory_knowledge_base.md`): Field extensions from ℚ

### Related Topics
- **Algebraic Number Theory** (`algebraic_number_theory_knowledge_base.md`): Algebraic extensions of ℚ
- **P-adic Numbers** (`p_adic_numbers_knowledge_base.md`): Alternative completions of ℚ
- **Combinatorics** (`combinatorics_knowledge_base.md`): Counting over ℕ

### Scope Clarification
This KB focuses on **foundational number systems**:
- Peano axioms for ℕ
- Ring axioms for ℤ
- Field axioms for ℚ
- Complete ordered field axioms for ℝ
- Fundamental theorems (well-ordering, √2 irrational, ℚ denumerable, Archimedean)

For **advanced number theory**, see **Algebraic Number Theory KB**.

---

## 1. Peano Axioms (Natural Numbers)

The Peano axioms provide a rigorous foundation for arithmetic, number theory, and all higher mathematics built on natural numbers.

### Axiom P1: Zero Exists

**Natural Language Statement:**
There exists a natural number called zero.

**Formal Definition:**
```
0 ∈ N
```

**Mathlib Support:** FULL
- **Lean 4:** `Nat.zero : Nat`

**Difficulty:** easy

---

### Axiom P2: Successor Function

**Natural Language Statement:**
Every natural number has a successor in the natural numbers.

**Formal Definition:**
```
∀n ∈ N : S(n) ∈ N
```

**Intuitive Explanation:**
The successor function S gives us the "next" natural number: S(0) = 1, S(1) = 2, S(2) = 3, etc.

**Mathlib Support:** FULL
- **Lean 4:** `Nat.succ : Nat → Nat`

**Difficulty:** easy

---

### Axiom P3: Zero is Not a Successor

**Natural Language Statement:**
Zero is not the successor of any natural number.

**Formal Definition:**
```
∀n ∈ N : S(n) ≠ 0
```

**Intuitive Explanation:**
This axiom prevents circular chains and ensures 0 is the "first" natural number with no predecessor.

**Mathlib Support:** FULL
- **Lean 4:** `Nat.succ_ne_zero`

**Difficulty:** easy

---

### Axiom P4: Successor is Injective

**Natural Language Statement:**
If the successor of two natural numbers is the same, then the two original numbers are the same.

**Formal Definition:**
```
∀m, n ∈ N : S(m) = S(n) ⟹ m = n
```

**Intuitive Explanation:**
Different natural numbers have different successors. This prevents "collisions" and ensures the successor function creates a proper sequence.

**Mathlib Support:** FULL
- **Lean 4:** `Nat.succ_injective`

**Difficulty:** easy

---

### Axiom P5: Principle of Mathematical Induction

**Natural Language Statement:**
If a property holds for 0 and is preserved by the successor operation, then it holds for all natural numbers.

**Formal Definition (Second-Order):**
```
∀K ⊆ N : [0 ∈ K ∧ (∀n ∈ K : S(n) ∈ K)] ⟹ K = N
```

**Formal Definition (First-Order Schema):**
```
For any formula φ(n):
[φ(0) ∧ (∀n : φ(n) ⟹ φ(S(n)))] ⟹ ∀n : φ(n)
```

**Intuitive Explanation:**
To prove a property holds for all natural numbers:
1. Prove it holds for 0 (base case)
2. Prove if it holds for n, it also holds for S(n) (inductive step)

**Mathlib Support:** FULL
- **Lean 4:** `Nat.rec` (recursion/induction principle)

**Difficulty:** easy

---

### Second-Order vs First-Order Formulations

**Second-Order (Categorical):**
- Quantifies over all subsets of N
- Uniquely characterizes the natural numbers (up to isomorphism)
- Less amenable to automated reasoning

**First-Order (Peano Arithmetic):**
- Uses an induction schema (infinitely many axioms, one per formula)
- Admits non-standard models (Lowenheim-Skolem theorem)
- Better suited for automated theorem proving

---

### Lean 4 Formalization

```lean
-- Natural numbers defined as inductive type
inductive Nat : Type
  | zero : Nat
  | succ : Nat → Nat

-- Induction principle (automatically generated)
Nat.rec {motive : Nat → Sort u}
  (zero : motive Nat.zero)
  (succ : (n : Nat) → motive n → motive n.succ)
  (t : Nat) : motive t
```

**Key Theorems:**

| Theorem | Lean Name | Statement |
|---------|-----------|-----------|
| Zero not successor | `Nat.succ_ne_zero` | `∀n, Nat.succ n ≠ 0` |
| Successor injective | `Nat.succ_injective` | `Nat.succ m = Nat.succ n → m = n` |
| Addition commutative | `Nat.add_comm` | `a + b = b + a` |
| Multiplication commutative | `Nat.mul_comm` | `a * b = b * a` |

**Import:** `Mathlib.Data.Nat.Basic`

---

## 2. Integer Axioms (Ring Structure)

The integers Z extend the natural numbers by adding negative numbers. Integers form a commutative ring.

### Construction from Natural Numbers

Integers are constructed as equivalence classes of ordered pairs (a, b) representing "a - b":

```
(a, b) ~ (c, d)  ⟺  a + d = b + c
Z = (N × N) / ~
```

**Examples:**
- (5, 2) ~ (4, 1) ~ (10, 7) all represent 3
- (2, 5) ~ (1, 4) all represent -3
- (3, 3) ~ (0, 0) all represent 0

---

### Ring Axioms

#### Addition Axioms (Abelian Group)

**A1. Associativity of Addition:**
```
∀a, b, c ∈ Z : (a + b) + c = a + (b + c)
```

**A2. Commutativity of Addition:**
```
∀a, b ∈ Z : a + b = b + a
```

**A3. Additive Identity:**
```
∃0 ∈ Z : ∀a ∈ Z : a + 0 = a
```

**A4. Additive Inverse:**
```
∀a ∈ Z : ∃(-a) ∈ Z : a + (-a) = 0
```

#### Multiplication Axioms (Monoid)

**M1. Associativity of Multiplication:**
```
∀a, b, c ∈ Z : (a · b) · c = a · (b · c)
```

**M2. Commutativity of Multiplication:**
```
∀a, b ∈ Z : a · b = b · a
```

**M3. Multiplicative Identity:**
```
∃1 ∈ Z, 1 ≠ 0 : ∀a ∈ Z : a · 1 = a
```

#### Distributive Law

**D1. Distributivity:**
```
∀a, b, c ∈ Z : a · (b + c) = (a · b) + (a · c)
```

---

### Additional Property: Integral Domain

**No Zero Divisors:**
```
∀a, b ∈ Z : a · b = 0 ⟹ (a = 0 ∨ b = 0)
```

This makes Z an integral domain, not just a ring.

---

### Lean 4 Formalization

```lean
-- Integers defined inductively
inductive Int : Type
  | ofNat : Nat → Int      -- non-negative integers
  | negSucc : Nat → Int    -- negative integers: negSucc n = -(n+1)

-- Ring instance
instance : CommRing Int := ...
```

**Key Theorems:**

| Property | Lean Name |
|----------|-----------|
| Addition associative | `Int.add_assoc` |
| Addition commutative | `Int.add_comm` |
| Additive identity | `Int.add_zero` |
| Additive inverse | `Int.add_left_neg` |
| Distributivity | `Int.mul_add` |

**Import:** `Mathlib.Data.Int.Basic`

---

## 3. Rational Number Axioms (Field Structure)

The rational numbers Q extend the integers by adding multiplicative inverses for non-zero elements. Rationals form a field.

### Construction from Integers

Rationals are constructed as equivalence classes of pairs (a, b) where b ≠ 0, representing "a/b":

```
(a, b) ~ (c, d)  ⟺  a · d = b · c
Q = {(a, b) : a ∈ Z, b ∈ Z, b ≠ 0} / ~
```

**Examples:**
- (1, 2) ~ (2, 4) ~ (3, 6) all represent 1/2
- (3, 1) ~ (6, 2) all represent 3
- (0, 1) ~ (0, 5) all represent 0

---

### Field Axioms

All ring axioms (A1-A4, M1-M3, D1) plus:

**F8. Multiplicative Inverse:**
```
∀a ∈ Q, a ≠ 0 : ∃a⁻¹ ∈ Q : a · a⁻¹ = 1
```

This is the key axiom distinguishing fields from rings.

---

### Lean 4 Formalization

```lean
-- Rationals as reduced fractions
structure Rat where
  num : Int
  den : Nat
  den_nz : den ≠ 0
  reduced : num.gcd den = 1

-- Field instance
instance : Field Rat := ...
```

**Import:** `Mathlib.Data.Rat.Basic`

---

## 4. Real Number Axioms (Complete Ordered Field)

The real numbers R extend the rationals to fill in the "gaps" (irrational numbers). The reals are uniquely characterized as the complete ordered field.

### The 14 Axioms for Real Numbers

#### Field Axioms (F1-F9)

Same as rational field axioms:
- F1-F4: Addition is an abelian group
- F5-F7: Multiplication is commutative with identity
- F8: Non-zero elements have multiplicative inverses
- F9: Distributivity

#### Order Axioms (O1-O4)

**O1. Trichotomy:**
```
∀a, b ∈ R : exactly one holds: a < b, a = b, or b < a
```

**O2. Transitivity:**
```
∀a, b, c ∈ R : (a < b ∧ b < c) ⟹ a < c
```

**O3. Addition Preserves Order:**
```
∀a, b, c ∈ R : a < b ⟹ a + c < b + c
```

**O4. Multiplication by Positives Preserves Order:**
```
∀a, b, c ∈ R : (a < b ∧ c > 0) ⟹ a · c < b · c
```

#### Completeness Axiom (C1)

**C1. Least Upper Bound Property:**

**Natural Language Statement:**
Every non-empty set of real numbers that is bounded above has a least upper bound (supremum).

**Formal Definition:**
```
∀A ⊆ R : [A ≠ ∅ ∧ (∃M ∈ R : ∀a ∈ A : a ≤ M)] ⟹ (∃L ∈ R : L = sup A)
```

where L = sup A means:
1. L is an upper bound: ∀a ∈ A : a ≤ L
2. L is the least upper bound: ∀M : (∀a ∈ A : a ≤ M) ⟹ L ≤ M

**Intuitive Explanation:**
This is what distinguishes R from Q. The set {x ∈ Q : x² < 2} is bounded above but has no least upper bound in Q. In R, sup = √2.

**Mathlib Support:** FULL
- **Lean 4:** `sSup : Set R → R` with properties `le_csSup`, `csSup_le`

**Difficulty:** medium

---

### Uniqueness Theorem

**Theorem (Huntington, 1903):**
The real numbers are, up to isomorphism, the unique complete ordered field.

All complete ordered fields are essentially the same - they are all isomorphic to R.

---

### Construction of Real Numbers

**Cauchy Sequences (Lean 4 approach):**
Real numbers are equivalence classes of Cauchy sequences of rationals:
- A Cauchy sequence (aₙ) satisfies: ∀ε > 0 : ∃N : ∀m, n > N : |aₘ - aₙ| < ε
- Two sequences are equivalent if their difference converges to zero

**Dedekind Cuts (alternative):**
A Dedekind cut is a partition of Q into two sets A and B where every element of A is less than every element of B.

---

### Lean 4 Formalization

```lean
-- Real numbers as quotient of Cauchy sequences
def Real := Quotient CauSeq.equiv

-- Complete ordered field instance
instance : ConditionallyCompleteLinearOrderedField Real := ...

-- Key completeness functions
sSup : Set R → R  -- supremum
sInf : Set R → R  -- infimum
```

**Key Type Class:**
```lean
class ConditionallyCompleteLinearOrderedField (α : Type*) extends
  Field α,
  ConditionallyCompleteLinearOrder α,
  IsStrictOrderedRing α
```

**Key Theorems:**

| Property | Lean Name |
|----------|-----------|
| Completeness | `Real.sSup_def` |
| Archimedean property | `Real.archimedean` |
| Existence of √2 | `Real.sqrt_two` |
| Existence of π | `Real.pi` |

**Import Statements:**
```lean
import Mathlib.Data.Real.Basic
import Mathlib.Data.Real.Sqrt
import Mathlib.Algebra.Order.CompleteField
import Mathlib.Order.ConditionallyCompleteLattice.Basic
```

---

## 5. Fundamental Theorems (Consequences of the Axioms)

The following theorems are provable from the axioms above and represent landmark results about number systems.

### Well-Ordering Principle for Natural Numbers

**Natural Language Statement:**
Every non-empty subset of the natural numbers contains a least element.

**Formal Definition:**
```
∀S ⊆ ℕ : S ≠ ∅ → (∃m ∈ S : ∀n ∈ S, m ≤ n)
```

**Proof Sketch:**
By strong induction. If S has no least element, show by induction that no natural number can be in S, contradicting S ≠ ∅.

**Significance:**
- Equivalent to the principle of strong induction
- Equivalent to the principle of mathematical induction (Axiom P5)
- Foundation for proof by infinite descent
- Key property distinguishing ℕ from other ordered sets

**Mathlib Support:** FULL
- **Key Theorem:** `Nat.lt_wfRel` - Well-foundedness of < on ℕ
- **Alternative:** `Nat.find` - Finds least element satisfying a predicate
- **Import:** `Mathlib.Data.Nat.Basic`

**Difficulty:** easy

---

### Irrationality of √2

**100 Theorems List:** #1

**Natural Language Statement:**
The square root of 2 is irrational. That is, there do not exist integers p and q (with q ≠ 0) such that (p/q)² = 2.

**Formal Definition:**
```
¬∃p, q ∈ ℤ : q ≠ 0 ∧ p² = 2q²
```

Equivalently: √2 ∉ ℚ

**Proof Sketch (Classic, by infinite descent):**
1. Assume √2 = p/q with gcd(p,q) = 1 (lowest terms)
2. Then p² = 2q²
3. So p² is even, hence p is even (say p = 2k)
4. Then 4k² = 2q², so q² = 2k²
5. So q² is even, hence q is even
6. But then gcd(p,q) ≥ 2, contradicting lowest terms

**Historical Significance:**
- Discovered by the Pythagoreans (c. 500 BC)
- First proof that irrational numbers exist
- Allegedly kept secret because it contradicted Pythagorean philosophy
- Led to the development of the real number system

**Mathlib Support:** FULL
- **Key Theorem:** `irrational_sqrt_two` or `Irrational (Real.sqrt 2)`
- **Import:** `Mathlib.NumberTheory.Irrational.Sqrt`

**Difficulty:** easy

---

### Denumerability of the Rationals

**100 Theorems List:** #3

**Natural Language Statement:**
The set of rational numbers ℚ is countably infinite (denumerable). There exists a bijection between ℕ and ℚ.

**Formal Definition:**
```
∃f : ℕ → ℚ, Bijective(f)
```

Equivalently: |ℚ| = |ℕ| = ℵ₀

**Proof Sketch (Cantor's pairing argument):**
1. List all fractions p/q in a grid (p on rows, q on columns)
2. Traverse the grid diagonally, skipping duplicates (reduced fractions)
3. This gives an enumeration: 0, 1, -1, 2, 1/2, -2, -1/2, 3, 1/3, ...
4. The enumeration is a bijection ℕ → ℚ

**Significance:**
- Contrasts sharply with the uncountability of ℝ
- Shows ℚ is "small" despite being dense in ℝ
- Foundation for understanding different sizes of infinity
- Key result in Cantor's development of set theory

**Mathlib Support:** FULL
- **Key Instance:** `Denumerable ℚ` - Rationals are denumerable
- **Supporting:** `Rat.denumerable`
- **Import:** `Mathlib.Data.Rat.Denumerable`

**Difficulty:** easy

---

### Archimedean Property

**Natural Language Statement:**
For any real number x, there exists a natural number n greater than x. Equivalently, for any positive real ε, there exists a natural number n such that 1/n < ε.

**Formal Definition:**
```
∀x ∈ ℝ : ∃n ∈ ℕ : x < n
```

Equivalently:
```
∀x, y ∈ ℝ : x > 0 → ∃n ∈ ℕ : y < n · x
```

**Proof Sketch:**
By completeness. If no such n exists, then ℕ is bounded above in ℝ. By the least upper bound property, let s = sup(ℕ). Then s - 1 is not an upper bound, so ∃n ∈ ℕ with s - 1 < n. But then n + 1 > s, contradicting s = sup(ℕ).

**Significance:**
- Connects the natural numbers to the real numbers
- Shows there are no "infinitely large" real numbers
- Shows there are no "infinitesimals" (positive reals smaller than all 1/n)
- Key property for analysis (limits, convergence)
- Named after Archimedes (c. 287-212 BC), though known earlier

**Mathlib Support:** FULL
- **Key Instance:** `Archimedean ℝ` - Reals are Archimedean
- **Key Theorem:** `exists_nat_gt` - For any real, there's a larger natural
- **Import:** `Mathlib.Algebra.Order.Archimedean`

**Difficulty:** easy

---

## Implementation Priority

### Phase 1: Axiom Statements (Easy)

Add all axioms as theorem records:
- 5 Peano axioms
- 7 ring axioms for integers
- 9 field axioms for rationals
- 14 axioms for reals (9 field + 4 order + 1 completeness)

### Phase 2: Basic Consequences (Medium)

| Theorem | Domain | Difficulty |
|---------|--------|------------|
| n + 0 = n | Nat | easy |
| Addition commutative | Nat | easy |
| Multiplication commutative | Nat | easy |
| Induction examples | Nat | medium |
| Ring properties | Int | easy |
| Field properties | Rat | easy |

### Phase 3: Advanced Results (Hard)

| Theorem | Domain | Difficulty |
|---------|--------|------------|
| Fundamental theorem of arithmetic | Nat | hard |
| Irrationality of √2 | Real | medium |
| Density of rationals in R | Real | medium |
| Intermediate value theorem | Real | hard |
| Bolzano-Weierstrass theorem | Real | hard |

---

## Dataset Integration

### Example Theorem Record (Peano Induction)

```json
{
  "theorem_id": "peano_induction",
  "mathematical_domain": "NumberTheory",
  "theorem_name": "Peano Axiom 5: Principle of Mathematical Induction",
  "nl_statement": "If a property holds for 0 and is preserved by the successor function, then it holds for all natural numbers.",
  "lean_statement": "theorem Nat.rec {motive : Nat → Sort u} (zero : motive 0) (succ : ∀ n, motive n → motive n.succ) : ∀ n, motive n",
  "lean_proof_term": null,
  "lean_proof_tactic": null,
  "imports": ["Mathlib.Data.Nat.Basic"],
  "difficulty": "easy",
  "mathlib_support": "full",
  "proof_status": "unproven",
  "schema_version": "2.0.0"
}
```

### Example Theorem Record (Completeness)

```json
{
  "theorem_id": "real_completeness",
  "mathematical_domain": "Analysis",
  "theorem_name": "Completeness Axiom: Least Upper Bound Property",
  "nl_statement": "Every non-empty set of real numbers that is bounded above has a least upper bound (supremum).",
  "lean_statement": "theorem Real.sSup_exists {s : Set R} (hne : s.Nonempty) (hbdd : BddAbove s) : ∃ x, IsLUB s x",
  "lean_proof_term": null,
  "lean_proof_tactic": null,
  "imports": ["Mathlib.Data.Real.Basic", "Mathlib.Order.ConditionallyCompleteLattice.Basic"],
  "difficulty": "medium",
  "mathlib_support": "full",
  "proof_status": "unproven",
  "schema_version": "2.0.0"
}
```

---

## References

### Peano Axioms
- [Wikipedia: Peano axioms](https://en.wikipedia.org/wiki/Peano_axioms)
- [Wikipedia: Well-ordering principle](https://en.wikipedia.org/wiki/Well-ordering_principle)
- [nLab: Peano arithmetic](https://ncatlab.org/nlab/show/Peano+arithmetic)
- [Encyclopedia of Mathematics: Peano axioms](https://encyclopediaofmath.org/wiki/Peano_axioms)

### Real Number Axioms and Theorems
- [Wikipedia: Completeness of the real numbers](https://en.wikipedia.org/wiki/Completeness_of_the_real_numbers)
- [Wikipedia: Square root of 2 - Irrationality](https://en.wikipedia.org/wiki/Square_root_of_2#Proofs_of_irrationality)
- [Wikipedia: Countable set - Rationals](https://en.wikipedia.org/wiki/Countable_set#The_set_of_rational_numbers_is_countable)
- [Wikipedia: Archimedean property](https://en.wikipedia.org/wiki/Archimedean_property)
- [University of Washington: Axioms for Real Numbers](https://sites.math.washington.edu/~hart/m524/realprop.pdf)

### Lean 4 / Mathlib
- [Lean Documentation: Natural Numbers](https://lean-lang.org/doc/reference/latest/Basic-Types/Natural-Numbers/)
- [Mathlib4: Data.Nat.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/Nat/Basic.html)
- [Mathlib4: Data.Rat.Denumerable](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/Rat/Denumerable.html)
- [Mathlib4: NumberTheory.Irrational.Sqrt](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/Irrational/Sqrt.html)
- [Mathlib4: Algebra.Order.Archimedean](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Order/Archimedean.html)
- [Mathlib4: Data.Real.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/Real/Basic.html)
- [Mathlib4: Algebra.Order.CompleteField](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Order/CompleteField.html)
- [100 Theorems in Lean](https://leanprover-community.github.io/100.html)

---

**End of Knowledge Base**
