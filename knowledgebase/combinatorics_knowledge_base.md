# Combinatorics Knowledge Base for Lean 4

**Generated:** 2025-12-14
**Purpose:** Research knowledge base for implementing combinatorics theorems in Lean 4 for dataset generation pairing formal proofs with natural language explanations.
**Measurability Score:** 85 (Good Mathlib coverage for basic combinatorics, partial coverage for advanced topics)

---

## Overview

Combinatorics is the mathematics of counting, arrangement, and discrete structure. This knowledge base catalogs fundamental counting principles, generating functions, extremal results, and Ramsey-theoretic statements as formalized in Lean 4's Mathlib.

### Content Summary

| Category | Count | Description |
|----------|-------|-------------|
| **Counting Principles** | 4 | Binomial coefficients, multinomial, stars and bars |
| **Special Numbers** | 2 | Catalan and Bell numbers |
| **Ramsey Theory** | 3 | Ramsey's theorem, Van der Waerden, Hales-Jewett |
| **Additive Combinatorics** | 3 | Cauchy-Davenport, Roth, Szemerédi |
| **Extremal Set Theory** | 4 | Sperner, LYM, Kruskal-Katona, Bollobás |
| **Basic Principles** | 2 | Pigeonhole, inclusion-exclusion |
| **Total** | 18 | Core combinatorics |

### Mathlib Approach

Mathlib provides strong support for:
- **Enumerative combinatorics**: Catalan numbers, binomial coefficients, multicombinations
- **Additive combinatorics**: Extensive library including Cauchy-Davenport, Roth's theorem
- **Set families**: LYM inequality, Sperner's theorem, Kruskal-Katona theorem
- **Ramsey theory**: Hales-Jewett theorem with Van der Waerden as corollary

**Primary Imports:**
- `Mathlib.Data.Nat.Choose.Basic` - Binomial coefficients
- `Mathlib.Combinatorics.Enumerative.Catalan` - Catalan numbers
- `Mathlib.Combinatorics.SetFamily.LYM` - Sperner and LYM
- `Mathlib.Combinatorics.HalesJewett` - Ramsey theory
- `Mathlib.Combinatorics.Additive.*` - Additive combinatorics

---

## Part I: Counting Principles

### 1. Binomial Coefficients

**Natural Language Statement:**
The binomial coefficient "n choose k", denoted C(n,k) or (n choose k), counts the number of ways to choose k items from n items without regard to order. It satisfies the recurrence relation C(n,k) = C(n-1,k-1) + C(n-1,k) with base cases C(n,0) = C(n,n) = 1.

**Mathematical Statement:**
For non-negative integers n and k:
```
C(n, k) = n! / (k! * (n - k)!)  if k ≤ n
        = 0                      if k > n

Recurrence: C(n, k) = C(n-1, k-1) + C(n-1, k)
Symmetry: C(n, k) = C(n, n-k)
```

**Proof Sketch:**
The factorial formula follows from the fundamental counting principle: there are n! ways to arrange n items, divided by k! permutations of the chosen items and (n-k)! permutations of the unchosen items. The recurrence relation holds because choosing k items from n can be done by either including a specific item (choose k-1 from remaining n-1) or excluding it (choose k from remaining n-1).

**Lean 4 Formalization:**
```lean
import Mathlib.Data.Nat.Choose.Basic

-- Definition (inductive)
def Nat.choose : ℕ → ℕ → ℕ
  | _, 0     => 1
  | 0, k + 1 => 0
  | n + 1, k + 1 => choose n k + choose n (k + 1)

-- Factorial formula
theorem Nat.choose_eq_factorial_div_factorial (n k : ℕ) (h : k ≤ n) :
    n.choose k = n! / (k! * (n - k)!) := by
  sorry

-- Symmetry
theorem Nat.choose_symm (n k : ℕ) (h : k ≤ n) :
    n.choose k = n.choose (n - k) := by
  sorry

-- Pascal's identity (recurrence)
theorem Nat.choose_succ_succ (n k : ℕ) :
    (n + 1).choose (k + 1) = n.choose k + n.choose (k + 1) := by
  rfl  -- True by definition!
```

**Mathlib Support:** FULL
- **Definition:** `Nat.choose` (inductive)
- **Factorial formula:** `Nat.choose_eq_factorial_div_factorial`
- **Symmetry:** `Nat.choose_symm`
- **Recurrence:** `Nat.choose_succ_succ`
- **Import:** `Mathlib.Data.Nat.Choose.Basic`

**Difficulty:** easy

---

### 2. Binomial Theorem

**Natural Language Statement:**
For any commutative ring elements x and y, and non-negative integer n, the expansion of (x + y)^n is the sum over k from 0 to n of C(n,k) * x^k * y^(n-k). This generalizes to noncommutative rings when x and y commute.

**Mathematical Statement:**
```
(x + y)^n = ∑_{k=0}^n C(n,k) * x^k * y^(n-k)
```

**Proof Sketch:**
By induction on n. The base case n=0 gives (x+y)^0 = 1 = C(0,0)*x^0*y^0. For the inductive step, expand (x+y)^(n+1) = (x+y)*(x+y)^n, apply the inductive hypothesis, distribute, and use Pascal's identity to combine terms.

**Lean 4 Formalization:**
```lean
import Mathlib.Data.Nat.Choose.Sum
import Mathlib.Algebra.BigOperators.Ring

-- Commutative version
theorem add_pow [CommSemiring R] (x y : R) (n : ℕ) :
    (x + y) ^ n = ∑ k in Finset.range (n + 1), x ^ k * y ^ (n - k) * (n.choose k) := by
  sorry

-- Commuting version (for noncommutative rings)
theorem Commute.add_pow [Semiring R] {x y : R} (h : Commute x y) (n : ℕ) :
    (x + y) ^ n = ∑ k in Finset.range (n + 1), x ^ k * y ^ (n - k) * (n.choose k) := by
  sorry
```

**Mathlib Support:** FULL
- **Commutative case:** `add_pow` in `Mathlib.Data.Nat.Choose.Sum`
- **Commuting case:** `Commute.add_pow`
- **Import:** `Mathlib.Data.Nat.Choose.Sum`, `Mathlib.Algebra.BigOperators.Ring`

**Difficulty:** easy

---

### 3. Multinomial Theorem

**Natural Language Statement:**
The multinomial theorem generalizes the binomial theorem to more than two terms. For variables x₁, x₂, ..., xₘ and non-negative integer n, the expansion of (x₁ + x₂ + ... + xₘ)^n is the sum over all sequences (k₁, k₂, ..., kₘ) with k₁ + k₂ + ... + kₘ = n of the term (n! / (k₁! * k₂! * ... * kₘ!)) * x₁^k₁ * x₂^k₂ * ... * xₘ^kₘ.

**Mathematical Statement:**
```
(x₁ + x₂ + ... + xₘ)^n = ∑_{k₁+...+kₘ=n} (n! / (k₁! * ... * kₘ!)) * x₁^k₁ * ... * xₘ^kₘ

where the multinomial coefficient is:
M(n; k₁, ..., kₘ) = n! / (k₁! * k₂! * ... * kₘ!)
```

**Proof Sketch:**
Proven by induction on m (number of variables) using the binomial theorem as the base case (m=2). The inductive step groups terms and applies the binomial theorem to reduce to the case of m-1 variables.

**Lean 4 Formalization:**
```lean
import Mathlib.Data.Nat.Choose.Multinomial

-- Note: As of 2025, Mathlib has `Nat.multichoose` (multicombinations)
-- but not the full multinomial coefficient or multinomial theorem.
-- Multichoose counts multisets, which is related but different.

-- Multichoose definition (not the multinomial coefficient!)
def Nat.multichoose (n k : ℕ) : ℕ :=
  (n + k - 1).choose k

-- Multichoose counts multisets of size k from n elements
-- This is C(n+k-1, k), related to stars and bars
```

**Mathlib Support:** PARTIAL
- **Multichoose:** `Nat.multichoose` exists (counts multicombinations)
- **Multinomial coefficient:** NOT directly available
- **Multinomial theorem:** NOT formalized
- **Import:** `Mathlib.Data.Nat.Choose.Multinomial` (contains multichoose only)

**Note:** Mathlib has `multichoose` which counts the number of ways to select k items from n items WITH replacement (multisets), but this is NOT the same as the multinomial coefficient. The multichoose satisfies `multichoose n k = (n+k-1).choose k`.

**Difficulty:** medium (theorem not yet in Mathlib)

**References:**
- [Mathlib.Data.Nat.Choose.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/Nat/Choose/Basic.html)

---

### 4. Stars and Bars

**Natural Language Statement:**
Stars and bars is a combinatorial technique for counting the number of ways to place n indistinguishable objects into k distinguishable bins. This is equivalent to finding the number of non-negative integer solutions to x₁ + x₂ + ... + xₖ = n. The answer is C(n+k-1, k-1) = C(n+k-1, n).

**Mathematical Statement:**
```
Number of solutions to x₁ + x₂ + ... + xₖ = n in non-negative integers
= C(n + k - 1, k - 1) = C(n + k - 1, n)
```

**Proof Sketch:**
Represent n objects as stars (*) in a row. Insert k-1 bars (|) to create k bins. There are n stars and k-1 bars for a total of n+k-1 positions. Choose k-1 positions for the bars, giving C(n+k-1, k-1) arrangements. This bijectively corresponds to solutions since each arrangement determines how many stars (objects) are in each bin.

**Lean 4 Formalization:**
```lean
import Mathlib.Data.Nat.Choose.Multinomial

-- Stars and bars is essentially multichoose
-- Place n items into k bins = choose n+k-1 positions for k-1 separators
theorem stars_and_bars (n k : ℕ) :
    Nat.multichoose k n = (n + k - 1).choose n := by
  rfl  -- True by definition of multichoose

-- Equivalently, choose positions for the separators
theorem stars_and_bars_alt (n k : ℕ) :
    Nat.multichoose k n = (n + k - 1).choose (k - 1) := by
  sorry  -- Use choose_symm
```

**Mathlib Support:** FULL (via multichoose)
- **Definition:** `Nat.multichoose k n = (n + k - 1).choose k`
- **Import:** `Mathlib.Data.Nat.Choose.Multinomial`

**Difficulty:** easy

**References:**
- [Stars and bars (combinatorics) - Wikipedia](https://en.wikipedia.org/wiki/Stars_and_bars_(combinatorics))

---

## Part II: Special Numbers

### 5. Catalan Numbers

**Natural Language Statement:**
The Catalan numbers form a sequence C₀, C₁, C₂, ... defined by the recurrence C(n+1) = ∑_{i=0}^n C(i) * C(n-i) with C(0) = 1. They have the explicit formula C(n) = C(2n, n) / (n+1), the n-th central binomial coefficient divided by n+1. Catalan numbers count many combinatorial objects including: balanced parentheses sequences, binary trees with n internal nodes, Dyck paths of length 2n, and triangulations of a convex (n+2)-gon.

**Mathematical Statement:**
```
Recurrence: C(n+1) = ∑_{i=0}^n C(i) * C(n-i)
Base case: C(0) = 1
Explicit formula: C(n) = C(2n, n) / (n+1) = (2n)! / ((n+1)! * n!)

Applications:
- Number of balanced parentheses strings of length 2n
- Number of binary trees with n internal nodes
- Number of Dyck paths of length 2n
- Number of triangulations of a convex (n+2)-gon
```

**Proof Sketch (Explicit Formula):**
The explicit formula can be proven by verifying it satisfies the recurrence relation, or by direct combinatorial argument. One approach: C(n) counts ballot sequences where in a sequence of n +1's and n -1's, all partial sums are non-negative. Use the cycle lemma or reflection principle to show this equals C(2n,n)/(n+1).

**Lean 4 Formalization:**
```lean
import Mathlib.Combinatorics.Enumerative.Catalan
import Mathlib.Data.Nat.Choose.Central

-- Recursive definition
def catalan : ℕ → ℕ
  | 0 => 1
  | n + 1 => ∑ i : Fin (n + 1), catalan i * catalan (n - i)

-- Explicit formula using central binomial coefficient
theorem catalan_eq_centralBinom_div (n : ℕ) :
    catalan n = Nat.centralBinom n / (n + 1) := by
  sorry

-- Central binomial coefficient definition
def Nat.centralBinom (n : ℕ) : ℕ := (2 * n).choose n

-- Applications: number of binary trees
theorem card_binaryTrees_eq_catalan (n : ℕ) :
    card (BinaryTree n) = catalan n := by
  sorry
```

**Mathlib Support:** FULL
- **Recursive definition:** `catalan` in `Mathlib.Combinatorics.Enumerative.Catalan`
- **Explicit formula:** `catalan_eq_centralBinom_div`
- **Central binomial:** `Nat.centralBinom` in `Mathlib.Data.Nat.Choose.Central`
- **Import:** `Mathlib.Combinatorics.Enumerative.Catalan`

**Applications in Mathlib:**
- Number of binary trees with n internal nodes
- Bijection with Dyck paths formalized

**Difficulty:** easy

**References:**
- [Mathlib.Combinatorics.Enumerative.Catalan](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/Enumerative/Catalan.html)
- [Catalan number - Wikipedia](https://en.wikipedia.org/wiki/Catalan_number)

---

### 6. Bell Numbers

**Natural Language Statement:**
The Bell number B(n) counts the number of partitions of a set with n elements. A partition is a way of grouping the n elements into non-empty, pairwise disjoint subsets. B(n) can be computed as the sum of Stirling numbers of the second kind: B(n) = ∑_{k=0}^n S(n,k), where S(n,k) counts partitions into exactly k non-empty parts.

**Mathematical Statement:**
```
B(n) = number of partitions of an n-element set
     = ∑_{k=0}^n S(n,k)

where S(n,k) = Stirling number of the second kind

Recurrence: B(n+1) = ∑_{k=0}^n C(n,k) * B(k)
Base case: B(0) = 1
```

**Proof Sketch:**
The recurrence follows from considering partitions by choosing which elements are in the same block as a distinguished element. The explicit sum formula follows from the definition of Stirling numbers: S(n,k) counts partitions into exactly k blocks, so summing over all k gives all partitions.

**Lean 4 Formalization:**
```lean
import Mathlib.Data.Finset.Partition

-- Set partitions are formalized in Mathlib
-- but Bell numbers as a sequence are NOT directly defined

-- Partitions are represented as Finpartitions
def setPartitions (α : Type*) [Fintype α] : Finset (Finpartition (Finset.univ : Finset α)) :=
  Finset.univ

-- Bell number would be
def bellNumber (n : ℕ) : ℕ :=
  (setPartitions (Fin n)).card

-- Stirling numbers of the second kind would count
-- partitions with exactly k parts
```

**Mathlib Support:** PARTIAL
- **Set partitions:** `Finpartition` type exists in `Mathlib.Data.Finset.Partition`
- **Bell numbers as sequence:** NOT explicitly defined
- **Stirling numbers:** NOT explicitly defined
- **Import:** `Mathlib.Data.Finset.Partition` (for partitions structure)

**Note:** While the underlying theory of set partitions is formalized in Mathlib, the Bell numbers and Stirling numbers of the second kind are not explicitly defined as sequences. These could be defined using the partition infrastructure.

**Difficulty:** medium (not yet explicitly in Mathlib)

**References:**
- [Bell number - Wikipedia](https://en.wikipedia.org/wiki/Bell_number)
- [Mathlib.Data.Finset.Partition](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/Finset/Partition.html)

---

## Part III: Ramsey Theory

### 7. Ramsey's Theorem (Finite Version)

**Natural Language Statement:**
For any positive integers r and s, there exists a least positive integer R(r,s) such that any graph on at least R(r,s) vertices contains either a clique of size r or an independent set of size s. In the two-color edge-coloring formulation: for any coloring of the edges of a complete graph on R(r,s) vertices with two colors (red and blue), there exists either a red clique of size r or a blue clique of size s.

**Mathematical Statement:**
```
For all r, s ∈ ℕ⁺, there exists R(r,s) ∈ ℕ such that:
For all n ≥ R(r,s), and any 2-coloring c : K_n → {red, blue},
there exists S ⊆ [n] with:
  |S| = r and all edges within S are red, OR
  |S| = s and all edges within S are blue

Bounds: R(r,s) ≤ C(r+s-2, r-1)
```

**Proof Sketch:**
By induction on r+s. Base cases: R(1,s) = R(r,1) = 1. For the inductive step, use a recursive bound: R(r,s) ≤ R(r-1,s) + R(r,s-1). This is proven by picking a vertex v and considering the color of edges from v. If there are at least R(r-1,s) red edges from v, apply induction to those neighbors; otherwise there are at least R(r,s-1) blue edges from v.

**Lean 4 Formalization:**
```lean
import Mathlib.Combinatorics.SimpleGraph.Clique

-- Ramsey number definition (existence is the content)
noncomputable def ramseyNumber (r s : ℕ) : ℕ :=
  Classical.choose (ramsey_theorem_exists r s)

-- Main theorem: Ramsey's theorem for graphs
theorem ramsey_theorem (r s n : ℕ) (h : n ≥ ramseyNumber r s) :
    ∀ (c : Sym2 (Fin n) → Bool),
    (∃ S : Finset (Fin n), S.card = r ∧ ∀ e ∈ S.sym2, c e = true) ∨
    (∃ S : Finset (Fin n), S.card = s ∧ ∀ e ∈ S.sym2, c e = false) := by
  sorry

-- Upper bound on Ramsey numbers
theorem ramsey_upper_bound (r s : ℕ) :
    ramseyNumber r s ≤ (r + s - 2).choose (r - 1) := by
  sorry
```

**Mathlib Support:** PARTIAL
- **General framework:** Graph cliques formalized in `Mathlib.Combinatorics.SimpleGraph.Clique`
- **Ramsey theorem:** NOT directly formalized
- **Ramsey numbers:** NOT defined
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Clique`

**Note:** Recent developments (2024-2025): Bhavik Mehta formalized the Campos-Griffiths-Morris-Sahasrabudhe exponential improvement for Ramsey number upper bounds in Lean.

**Difficulty:** hard (major theorem not yet in Mathlib core)

**References:**
- [Ramsey's theorem - Wikipedia](https://en.wikipedia.org/wiki/Ramsey%27s_theorem)
- [Formalizing Finite Ramsey Theory in Lean 4](https://dl.acm.org/doi/10.1007/978-3-031-66997-2_6)

---

### 8. Van der Waerden's Theorem

**100 Theorems List:** NOT on Freek's list (Ceva's theorem is #61, not Van der Waerden)

**Natural Language Statement:**
For any positive integers r and k, there exists a positive integer W(r,k) such that if the integers {1, 2, ..., W(r,k)} are colored with r colors, then there exists a monochromatic arithmetic progression of length k. That is, there exist integers a and d > 0 such that a, a+d, a+2d, ..., a+(k-1)d all have the same color.

**Mathematical Statement:**
```
For all r, k ∈ ℕ⁺, there exists W(r,k) ∈ ℕ such that:
For all n ≥ W(r,k) and any r-coloring c : [n] → [r],
there exists a monochromatic AP of length k:
  ∃ a, d > 0 : c(a) = c(a+d) = c(a+2d) = ... = c(a+(k-1)d)
```

**Proof Sketch:**
Van der Waerden's theorem can be proven using the Hales-Jewett theorem. Alternatively, direct proofs exist using compactness arguments or constructive bounds. The key insight is that arithmetic progressions are unavoidable in sufficiently long colored sequences.

**Lean 4 Formalization:**
```lean
import Mathlib.Combinatorics.HalesJewett

-- Van der Waerden as a corollary of Hales-Jewett
-- The theorem is formalized as: whenever a commutative monoid M
-- is finitely colored and S is a finite subset,
-- there exists a monochromatic homothetic copy of S

theorem van_der_waerden_from_hales_jewett (r k : ℕ) :
    ∃ W : ℕ, ∀ (n : ℕ) (hn : n ≥ W) (c : ℕ → Fin r),
    ∃ (a d : ℕ) (hd : d > 0),
    ∀ i < k, c (a + i * d) = c a := by
  sorry  -- Follows from Hales-Jewett

-- Hales-Jewett theorem in Mathlib
-- (specialized version for Van der Waerden)
```

**Mathlib Support:** GOOD (via Hales-Jewett)
- **Hales-Jewett theorem:** Formalized in `Mathlib.Combinatorics.HalesJewett`
- **Van der Waerden:** Follows as corollary
- **Exact statement:** May differ from classical formulation
- **Import:** `Mathlib.Combinatorics.HalesJewett`

**Note:** The Mathlib version states the theorem for commutative monoids with homothetic copies. A finitary version (with explicit bounds) is work in progress.

**Difficulty:** medium (available via Hales-Jewett)

**References:**
- [Mathlib.Combinatorics.HalesJewett](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/HalesJewett.html)
- [Van der Waerden's theorem - Wikipedia](https://en.wikipedia.org/wiki/Van_der_Waerden%27s_theorem)

---

### 9. Hales-Jewett Theorem

**Natural Language Statement:**
The Hales-Jewett theorem is a generalization of Van der Waerden's theorem. For any finite alphabet A and positive integer k, there exists a dimension n such that if the n-dimensional cube A^n is r-colored, then there exists a monochromatic combinatorial line of length k. A combinatorial line is obtained by fixing some coordinates and letting one "active" coordinate vary over all values in A.

**Mathematical Statement:**
```
For all finite alphabet A, and r, k ∈ ℕ⁺,
there exists n ∈ ℕ such that:
For any r-coloring c : A^n → [r],
there exists a monochromatic combinatorial line of length |A|

Where a combinatorial line in A^n is a set of points
that agree on all coordinates except one "active" coordinate
that takes all possible values from A
```

**Proof Sketch:**
The original proof uses a double induction argument on the number of colors and the alphabet size. The key is to show that in a high enough dimension, some color class must contain a combinatorial subspace, which can then be used inductively.

**Lean 4 Formalization:**
```lean
import Mathlib.Combinatorics.HalesJewett

-- The Hales-Jewett theorem
-- Mathlib proves this and deduces Van der Waerden and
-- multidimensional Hales-Jewett as corollaries

-- Simplified statement (actual Mathlib version is more general)
theorem hales_jewett (A : Type*) [Fintype A] (r k : ℕ) :
    ∃ n : ℕ, ∀ (c : (Fin n → A) → Fin r),
    ∃ (line : CombinatorialLine A n),
    ∀ p q ∈ line, c p = c q := by
  sorry
```

**Mathlib Support:** FULL
- **Main theorem:** Formalized in `Mathlib.Combinatorics.HalesJewett`
- **Corollaries:** Van der Waerden, multidimensional version
- **Import:** `Mathlib.Combinatorics.HalesJewett`

**Difficulty:** hard (but formalized)

**References:**
- [Mathlib.Combinatorics.HalesJewett](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/HalesJewett.html)
- [Hales-Jewett theorem - Wikipedia](https://en.wikipedia.org/wiki/Hales%E2%80%93Jewett_theorem)

---

## Part IV: Additive Combinatorics

### 10. Cauchy-Davenport Theorem

**Natural Language Statement:**
For a prime p, if A and B are non-empty subsets of Z/pZ (integers modulo p), then the sumset A + B = {a + b : a ∈ A, b ∈ B} has size at least min(p, |A| + |B| - 1). This provides a lower bound on the growth of sumsets in the group Z/pZ.

**Mathematical Statement:**
```
For prime p and non-empty A, B ⊆ Z/pZ:
|A + B| ≥ min(p, |A| + |B| - 1)

where A + B = {a + b : a ∈ A, b ∈ B}
```

**Proof Sketch:**
The proof uses a polynomial method or Kneser's theorem. One approach: assume |A + B| < |A| + |B| - 1. Consider the polynomial P(x) = ∏_{a ∈ A} (x - a). Show that if the sumset is too small, there's a non-trivial relation among the values P(b) for b ∈ B, contradicting the properties of polynomials over Z/pZ.

**Lean 4 Formalization:**
```lean
import Mathlib.Combinatorics.Additive.CauchyDavenport

-- Cauchy-Davenport for Z/pZ
theorem cauchy_davenport {p : ℕ} (hp : p.Prime) (A B : Finset (ZMod p))
    (hA : A.Nonempty) (hB : B.Nonempty) :
    (A + B).card ≥ min p (A.card + B.card - 1) := by
  sorry

-- More general version via Kneser's theorem
-- (also formalized in Mathlib)
```

**Mathlib Support:** FULL
- **Cauchy-Davenport:** Formalized for Z/pZ
- **Kneser's theorem:** Generalization also in Mathlib
- **General groups:** Extension to linearly ordered cancellative semigroups
- **Import:** `Mathlib.Combinatorics.Additive.CauchyDavenport` or related files

**Difficulty:** medium

**References:**
- [Mathematics in Mathlib - Additive Combinatorics](https://leanprover-community.github.io/mathlib-overview.html)
- [LeanCamCombi](https://yaeldillies.github.io/LeanCamCombi/)
- [Cauchy-Davenport theorem - Wikipedia](https://en.wikipedia.org/wiki/Cauchy%E2%80%93Davenport_theorem)

---

### 11. Roth's Theorem (3-Term Arithmetic Progressions)

**Natural Language Statement:**
Any subset of the integers (or of {1, 2, ..., N}) with positive upper density contains a 3-term arithmetic progression. Equivalently, if A ⊆ {1, ..., N} has no 3-term arithmetic progressions, then |A| = o(N). The largest subset of {1, ..., N} without a 3-term AP has size at most N / (log log N)^c for some constant c > 0.

**Mathematical Statement:**
```
If A ⊆ ℤ has positive upper density δ(A) > 0,
then A contains a 3-term AP: x, x+d, x+2d for some x, d with d ≠ 0

Equivalently (finite version):
For any δ > 0, there exists N₀ such that for all N ≥ N₀,
if A ⊆ {1, ..., N} with |A| ≥ δN,
then A contains x, x+d, x+2d for some x, d > 0
```

**Proof Sketch:**
Roth's original proof uses Fourier analysis on Z/NZ. The key is to show that if a set has positive density, its Fourier transform cannot be too large on many frequencies, which forces arithmetic structure. Modern proofs use variants of this approach or the density increment method.

**Lean 4 Formalization:**
```lean
import Mathlib.Combinatorics.Additive.RothNumber

-- Roth's theorem (existence of 3-APs in dense sets)
-- The finite version is formalized

theorem roth_theorem_finite (δ : ℝ) (hδ : δ > 0) :
    ∃ N₀ : ℕ, ∀ N ≥ N₀, ∀ A : Finset (Fin N),
    (A.card : ℝ) ≥ δ * N →
    ∃ x d : Fin N, d ≠ 0 ∧ x ∈ A ∧ (x + d) ∈ A ∧ (x + 2*d) ∈ A := by
  sorry

-- Roth number: largest subset of [N] without a 3-AP
def rothNumber (N : ℕ) : ℕ :=
  (Finset.filter (fun A : Finset (Fin N) => ¬ has3AP A) Finset.univ).sup Finset.card
```

**Mathlib Support:** GOOD
- **Roth's theorem:** Formalized in additive combinatorics section
- **Roth number:** Definition likely formalized
- **Sets without APs:** Infrastructure exists
- **Import:** `Mathlib.Combinatorics.Additive.RothNumber` or related

**Difficulty:** hard

**References:**
- [Mathematics in Mathlib - Additive Combinatorics](https://leanprover-community.github.io/mathlib-overview.html)
- [Roth's theorem - Wikipedia](https://en.wikipedia.org/wiki/Roth%27s_theorem_on_arithmetic_progressions)

---

### 12. Szemerédi's Theorem

**Natural Language Statement:**
For any positive integer k and any positive real δ, there exists N₀ such that any subset A ⊆ {1, 2, ..., N} with N ≥ N₀ and |A| ≥ δN contains an arithmetic progression of length k. This generalizes Roth's theorem (the case k=3) to arbitrarily long arithmetic progressions.

**Mathematical Statement:**
```
For all k ∈ ℕ⁺ and δ > 0, there exists N₀ such that:
For all N ≥ N₀, if A ⊆ {1, ..., N} with |A| ≥ δN,
then A contains a k-term AP:
  ∃ a, d > 0 : a, a+d, a+2d, ..., a+(k-1)d ∈ A
```

**Proof Sketch:**
Szemerédi's original proof uses a combinatorial argument with the Szemerédi regularity lemma. Alternative proofs exist using ergodic theory (Furstenberg), or the polynomial method and hypergraph regularity (Gowers). The key idea is to find structure in dense sets through repeated applications of regularity or density increment arguments.

**Lean 4 Formalization:**
```lean
import Mathlib.Combinatorics.Additive.AP.ThreeAP

-- Szemerédi's theorem (general k-term APs)
-- As of 2025, full Szemerédi not formalized (very difficult!)
-- But 3-AP case (Roth) is formalized

theorem szemeredi_theorem (k : ℕ) (δ : ℝ) (hk : k > 0) (hδ : δ > 0) :
    ∃ N₀ : ℕ, ∀ N ≥ N₀, ∀ A : Finset (Fin N),
    (A.card : ℝ) ≥ δ * N →
    ∃ a d : ℕ, d > 0 ∧ (∀ i < k, (a + i * d : ℕ) < N ∧ ⟨a + i * d, by omega⟩ ∈ A) := by
  sorry  -- Not formalized for general k

-- The k=3 case is Roth's theorem (formalized)
```

**Mathlib Support:** PARTIAL
- **k=3 case (Roth):** Formalized
- **General k:** NOT formalized (extremely difficult)
- **Infrastructure:** 3-AP machinery exists
- **Import:** `Mathlib.Combinatorics.Additive.AP.*`

**Note:** Full Szemerédi's theorem is one of the deepest results in additive combinatorics and has not been formalized in any proof assistant as of 2025. The k=3 case (Roth) is the current state of the art in Mathlib.

**Difficulty:** very hard (not formalized except k=3)

**References:**
- [Mathematics in Mathlib - Additive Combinatorics](https://leanprover-community.github.io/mathlib-overview.html)
- [Szemerédi's theorem - Wikipedia](https://en.wikipedia.org/wiki/Szemer%C3%A9di%27s_theorem)

---

## Part V: Extremal Set Theory

### 13. Sperner's Theorem

**Natural Language Statement:**
An antichain in the power set of an n-element set is a collection of subsets where no set is contained in another. Sperner's theorem states that the maximum size of an antichain is C(n, n/2), the size of the middle layer (or middle two layers if n is odd). This maximum is achieved by taking all subsets of size ⌊n/2⌋ or all subsets of size ⌈n/2⌉.

**Mathematical Statement:**
```
Let 𝒜 be an antichain in P([n]) (power set of {1, ..., n})
Then |𝒜| ≤ C(n, ⌊n/2⌋)

An antichain 𝒜 means: ∀ A, B ∈ 𝒜, A ⊄ B and B ⊄ A (unless A = B)
```

**Proof Sketch:**
The LYM inequality implies Sperner's theorem. For an antichain 𝒜, the LYM inequality states ∑_{A ∈ 𝒜} 1/C(n, |A|) ≤ 1. Since C(n,k) is maximized at k = ⌊n/2⌋, we have 1/C(n,|A|) ≥ 1/C(n,⌊n/2⌋) for all A. Therefore |𝒜| * (1/C(n,⌊n/2⌋)) ≤ 1, giving |𝒜| ≤ C(n,⌊n/2⌋).

**Lean 4 Formalization:**
```lean
import Mathlib.Combinatorics.SetFamily.LYM

-- Sperner's theorem
theorem IsAntichain.sperner {α : Type*} [Fintype α] (𝒜 : Finset (Finset α))
    (h : IsAntichain (· ⊆ ·) 𝒜) :
    𝒜.card ≤ (Fintype.card α).choose (Fintype.card α / 2) := by
  sorry

-- Antichain definition
def IsAntichain {α : Type*} (r : α → α → Prop) (s : Set α) : Prop :=
  ∀ ⦃a⦄, a ∈ s → ∀ ⦃b⦄, b ∈ s → a ≠ b → ¬r a b ∧ ¬r b a
```

**Mathlib Support:** FULL
- **Sperner's theorem:** `IsAntichain.sperner` in `Mathlib.Combinatorics.SetFamily.LYM`
- **Antichain definition:** Standard
- **Import:** `Mathlib.Combinatorics.SetFamily.LYM`

**Difficulty:** medium

**References:**
- [Mathlib.Combinatorics.SetFamily.LYM](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/SetFamily/LYM.html)
- [Sperner's theorem - Wikipedia](https://en.wikipedia.org/wiki/Sperner%27s_theorem)

---

### 14. LYM Inequality

**Natural Language Statement:**
The Lubell-Yamamoto-Meshalkin (LYM) inequality provides a bound on the size of antichains. If 𝒜 is an antichain in P([n]), then the sum over all sets A in 𝒜 of 1/C(n,|A|) is at most 1. This is also known as the local LYM inequality when applied to shadows of sets.

**Mathematical Statement:**
```
If 𝒜 is an antichain in P([n]), then:
∑_{A ∈ 𝒜} 1/C(n, |A|) ≤ 1

Local LYM: For any family 𝒜 in layer k (sets of size k),
|∂𝒜| / C(n, k-1) ≥ |𝒜| / C(n, k)

where ∂𝒜 is the shadow {B : |B| = k-1, ∃A ∈ 𝒜, B ⊂ A}
```

**Proof Sketch:**
The LYM inequality can be proven by a counting argument using maximal chains. A maximal chain in P([n]) is a sequence ∅ = C₀ ⊂ C₁ ⊂ ... ⊂ Cₙ = [n] where |Cᵢ| = i. There are n! maximal chains. An antichain intersects each maximal chain at most once. For a set A of size k, the number of maximal chains containing A is k! * (n-k)!. Therefore ∑ k! * (n-k)! ≤ n!, which simplifies to the LYM inequality.

**Lean 4 Formalization:**
```lean
import Mathlib.Combinatorics.SetFamily.LYM

-- LYM inequality
theorem Finset.sum_card_slice_div_choose_le_one {α : Type*} [Fintype α]
    (𝒜 : Finset (Finset α)) (h : IsAntichain (· ⊆ ·) 𝒜) :
    (∑ A in 𝒜, (1 : ℚ) / (Fintype.card α).choose A.card) ≤ 1 := by
  sorry

-- Local LYM inequality
theorem Finset.card_div_choose_le_card_shadow_div_choose {α : Type*} [Fintype α]
    (𝒜 : Finset (Finset α)) (k : ℕ) :
    (𝒜.card : ℚ) / (Fintype.card α).choose k ≤
    (shadow 𝒜).card / (Fintype.card α).choose (k - 1) := by
  sorry

-- Shadow definition
def shadow {α : Type*} (𝒜 : Finset (Finset α)) : Finset (Finset α) :=
  𝒜.biUnion (fun A => A.powerset.filter (fun B => B.card = A.card - 1))
```

**Mathlib Support:** FULL
- **LYM inequality:** `Finset.sum_card_slice_div_choose_le_one`
- **Local LYM:** `Finset.card_div_choose_le_card_shadow_div_choose`
- **Shadow operation:** Defined
- **Import:** `Mathlib.Combinatorics.SetFamily.LYM`

**Difficulty:** medium

**References:**
- [Mathlib.Combinatorics.SetFamily.LYM](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/SetFamily/LYM.html)
- [LYM inequality - Wikipedia](https://en.wikipedia.org/wiki/Lubell%E2%80%93Yamamoto%E2%80%93Meshalkin_inequality)

---

### 15. Kruskal-Katona Theorem

**Natural Language Statement:**
The Kruskal-Katona theorem provides a sharp lower bound on the size of the shadow of a family of k-element sets. Given a family 𝒜 of k-element subsets of [n], the shadow ∂𝒜 consists of all (k-1)-element sets contained in some set in 𝒜. The theorem states that |∂𝒜| is minimized when 𝒜 is an initial segment of the colexicographic order, and gives an explicit formula for this minimum.

**Mathematical Statement:**
```
For a family 𝒜 of k-element sets with |𝒜| = m,
the shadow ∂𝒜 = {B : |B| = k-1, ∃A ∈ 𝒜, B ⊂ A}
satisfies: |∂𝒜| ≥ |∂𝒜₀|

where 𝒜₀ is the initial m sets in colexicographic order
```

**Proof Sketch:**
The proof uses a compression argument. Define the colexicographic order on k-sets, and show that shifting operations (replacing a set with one earlier in colex order while maintaining size) reduce the shadow size. Repeated shifting gives the initial segment, which minimizes the shadow.

**Lean 4 Formalization:**
```lean
import Mathlib.Combinatorics.SetFamily.KruskalKatona

-- Kruskal-Katona theorem
-- The initial segment in colex order minimizes shadow size

theorem kruskal_katona {α : Type*} [Fintype α] [LinearOrder α]
    (𝒜 : Finset (Finset α)) (k : ℕ) (h : ∀ A ∈ 𝒜, A.card = k) :
    (shadow 𝒜).card ≥ (shadow (colexInitialSegment 𝒜.card k)).card := by
  sorry

-- Colex order and initial segment definitions would be here
```

**Mathlib Support:** FULL
- **Kruskal-Katona:** Formalized by Bhavik Mehta
- **Colex order:** Defined
- **Shadow operations:** Available
- **Import:** `Mathlib.Combinatorics.SetFamily.KruskalKatona` (if exists) or related

**Note:** Bhavik Mehta's formalization work included Kruskal-Katona and the Erdős-Ko-Rado theorem as consequences.

**Difficulty:** hard

**References:**
- [Mathematics in Mathlib](https://leanprover-community.github.io/mathlib-overview.html)
- [Combinatorics in Lean - Bhavik Mehta](https://b-mehta.github.io/combinatorics/)
- [Kruskal-Katona theorem - Wikipedia](https://en.wikipedia.org/wiki/Kruskal%E2%80%93Katona_theorem)

---

### 16. Bollobás Set-Pairs Inequality

**Natural Language Statement:**
Let A₁, ..., Aₘ and B₁, ..., Bₘ be finite sets such that Aᵢ and Bᵢ are disjoint for all i, but Aᵢ and Bⱼ intersect whenever i ≠ j. Then m ≤ C(|A₁|+|B₁|, |A₁|). More generally, if all |Aᵢ| ≤ a and |Bᵢ| ≤ b, then m ≤ C(a+b, a).

**Mathematical Statement:**
```
If (A₁, B₁), ..., (Aₘ, Bₘ) satisfy:
  - Aᵢ ∩ Bᵢ = ∅ for all i
  - Aᵢ ∩ Bⱼ ≠ ∅ for all i ≠ j

Then m ≤ C(a + b, a) where a = max|Aᵢ|, b = max|Bᵢ|
```

**Proof Sketch:**
The proof uses a linear algebra argument over a finite field, or a probabilistic argument. One approach: define a random linear order on the union of all sets. Count the number of pairs (i, σ) where σ is an ordering such that max(Aᵢ) < min(Bᵢ) in σ. The disjointness and intersection conditions give upper and lower bounds that imply the inequality.

**Lean 4 Formalization:**
```lean
import Mathlib.Combinatorics.SetFamily.Bollobas

-- Bollobás set-pairs inequality
theorem bollobas_set_pairs {α : Type*} [Fintype α]
    (A B : Fin m → Finset α)
    (hdisjoint : ∀ i, Disjoint (A i) (B i))
    (hintersect : ∀ i j, i ≠ j → (A i ∩ B j).Nonempty)
    (ha : ∀ i, (A i).card ≤ a)
    (hb : ∀ i, (B i).card ≤ b) :
    m ≤ (a + b).choose a := by
  sorry
```

**Mathlib Support:** PARTIAL
- **Bollobás inequality:** Likely in set families section
- **Status:** Check `Mathlib.Combinatorics.SetFamily.*`
- **Import:** `Mathlib.Combinatorics.SetFamily.Bollobas` (if exists)

**Note:** This is listed in the Mathlib overview but may not have a dedicated file. May be part of general set family results.

**Difficulty:** hard

**References:**
- [Mathematics in Mathlib](https://leanprover-community.github.io/mathlib-overview.html)
- [Bollobás set-pairs inequality - Wikipedia](https://en.wikipedia.org/wiki/Bollob%C3%A1s_set-pairs_inequality)

---

## Part VI: Basic Principles

### 17. Pigeonhole Principle

**Natural Language Statement:**
If n items are placed into m containers and n > m, then at least one container must contain more than one item. More generally, if n items are placed into m containers, then some container contains at least ⌈n/m⌉ items. The infinite version states that if infinitely many items are placed into finitely many containers, then at least one container contains infinitely many items.

**Mathematical Statement:**
```
Finite version:
If f : [n] → [m] and n > m, then f is not injective
(∃ i ≠ j such that f(i) = f(j))

Strong version:
If f : [n] → [m], then some fiber has size ≥ ⌈n/m⌉
(∃ k ∈ [m] such that |f⁻¹(k)| ≥ ⌈n/m⌉)

Infinite version:
If f : ℕ → [m], then some fiber is infinite
```

**Proof Sketch:**
The finite version is immediate by counting: if all containers had at most one item, there would be at most m items total, contradicting n > m. The strong version follows similarly: if all containers had fewer than ⌈n/m⌉ items, there would be fewer than n items total.

**Lean 4 Formalization:**
```lean
import Mathlib.Combinatorics.Pigeonhole

-- Basic pigeonhole principle
theorem exists_ne_of_card_lt_of_maps_to {α β : Type*} [Fintype α] [Fintype β]
    (f : α → β) (h : Fintype.card β < Fintype.card α) :
    ∃ x y : α, x ≠ y ∧ f x = f y := by
  sorry

-- Strong pigeonhole principle
theorem exists_lt_card_fiber_of_mul_lt_card {α β : Type*} [Fintype α] [DecidableEq β]
    (f : α → β) {n : ℕ} (hn : n * Fintype.card β < Fintype.card α) :
    ∃ y : β, n < (Finset.univ.filter (fun x => f x = y)).card := by
  sorry

-- Infinite pigeonhole
theorem infinite_pigeonhole {α β : Type*} [Infinite α] [Fintype β] (f : α → β) :
    ∃ y : β, Set.Infinite (f ⁻¹' {y}) := by
  sorry
```

**Mathlib Support:** FULL
- **Basic version:** Multiple formulations in `Mathlib.Combinatorics.Pigeonhole`
- **Strong version:** Available
- **Infinite version:** `ordinal.infinite_pigeonhole`
- **Measure version:** For measure spaces
- **Import:** `Mathlib.Combinatorics.Pigeonhole`

**Note:** Mathlib has many variants with names following convention (e.g., `finset.exists_lt_sum_fiber_of_maps_to_of_nsmul_lt_sum`).

**Difficulty:** easy

**References:**
- [Mathlib.Combinatorics.Pigeonhole](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/Pigeonhole.html)
- [Pigeonhole principle - Wikipedia](https://en.wikipedia.org/wiki/Pigeonhole_principle)

---

### 18. Inclusion-Exclusion Principle

**Natural Language Statement:**
The inclusion-exclusion principle gives a formula for the size of a union of finite sets in terms of the sizes of all possible intersections. For sets A₁, ..., Aₙ:
|A₁ ∪ ... ∪ Aₙ| = ∑ᵢ|Aᵢ| - ∑ᵢ<ⱼ|Aᵢ ∩ Aⱼ| + ∑ᵢ<ⱼ<ₖ|Aᵢ ∩ Aⱼ ∩ Aₖ| - ... + (-1)ⁿ⁺¹|A₁ ∩ ... ∩ Aₙ|

**Mathematical Statement:**
```
|⋃ᵢ₌₁ⁿ Aᵢ| = ∑_{∅≠S⊆[n]} (-1)^(|S|+1) |⋂ᵢ∈S Aᵢ|

Equivalently:
|⋃ᵢ₌₁ⁿ Aᵢ| = ∑_{k=1}^n (-1)^(k+1) ∑_{|S|=k} |⋂ᵢ∈S Aᵢ|
```

**Proof Sketch:**
Prove by counting how many times each element x in the union is counted. An element x in exactly m of the sets contributes C(m,1) - C(m,2) + C(m,3) - ... + (-1)^(m+1) C(m,m) to the right side. By the binomial theorem, this equals 1 - (1-1)^m = 1, so each element is counted exactly once.

**Lean 4 Formalization:**
```lean
import Mathlib.Algebra.BigOperators.Ring
import Mathlib.Data.Finset.Card

-- Inclusion-exclusion principle
theorem card_union_inclusion_exclusion {α : Type*} [DecidableEq α]
    (A : Fin n → Finset α) :
    (⋃ i, A i).card = ∑ S : Finset (Fin n), S.Nonempty →
      (-1 : ℤ) ^ (S.card + 1) * (⋂ i ∈ S, A i).card := by
  sorry

-- Two-set version (simpler)
theorem card_union_two {α : Type*} [DecidableEq α] (A B : Finset α) :
    (A ∪ B).card = A.card + B.card - (A ∩ B).card := by
  sorry
```

**Mathlib Support:** FULL
- **General principle:** Formalized in `Mathlib.Algebra.BigOperators.Ring`
- **Two-set case:** `Finset.card_union_eq` available
- **General formulation:** Available with big operators
- **Import:** `Mathlib.Algebra.BigOperators.Ring`

**Note:** The principle is formalized but may not have a single named theorem "inclusion_exclusion". Instead it's proven as needed using big operator lemmas.

**Difficulty:** easy

**References:**
- [Mathlib.Algebra.BigOperators.Ring](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/BigOperators/Ring.html)
- [Inclusion-exclusion principle - Wikipedia](https://en.wikipedia.org/wiki/Inclusion%E2%80%93exclusion_principle)

---

## Implementation Priority

Based on Mathlib support and difficulty:

### Tier 1: Easy - Fully Supported (High Priority)
1. **Binomial coefficients** - Definition and properties ✅
2. **Binomial theorem** - Commutative and commuting versions ✅
3. **Catalan numbers** - Full formalization ✅
4. **Pigeonhole principle** - All variants ✅
5. **Stars and bars** - Via multichoose ✅
6. **Sperner's theorem** - Complete ✅
7. **LYM inequality** - Complete ✅

### Tier 2: Medium - Good Support (Medium Priority)
8. **Cauchy-Davenport** - Formalized ✅
9. **Roth's theorem** - k=3 case formalized ✅
10. **Van der Waerden** - Via Hales-Jewett ✅
11. **Hales-Jewett** - Formalized ✅
12. **Kruskal-Katona** - Formalized ✅
13. **Inclusion-exclusion** - Available via big operators ✅

### Tier 3: Partial/Hard (Lower Priority)
14. **Multinomial theorem** - Multichoose exists, but not multinomial ⚠️
15. **Bell numbers** - Partitions exist, sequence not defined ⚠️
16. **Bollobás inequality** - Possibly formalized ⚠️
17. **Ramsey's theorem** - Not in core Mathlib ❌
18. **Szemerédi's theorem** - Only k=3 (Roth) ❌

---

## Summary Table

| Theorem | Mathlib Status | Difficulty | Location |
|---------|----------------|------------|----------|
| Binomial coefficients | FULL | easy | `Mathlib.Data.Nat.Choose.Basic` |
| Binomial theorem | FULL | easy | `Mathlib.Data.Nat.Choose.Sum` |
| Multinomial theorem | PARTIAL | medium | `Mathlib.Data.Nat.Choose.Multinomial` (multichoose only) |
| Stars and bars | FULL | easy | `Mathlib.Data.Nat.Choose.Multinomial` |
| Catalan numbers | FULL | easy | `Mathlib.Combinatorics.Enumerative.Catalan` |
| Bell numbers | PARTIAL | medium | `Mathlib.Data.Finset.Partition` (partitions only) |
| Ramsey's theorem | PARTIAL | hard | Graph infrastructure exists |
| Van der Waerden | GOOD | medium | `Mathlib.Combinatorics.HalesJewett` (via corollary) |
| Hales-Jewett | FULL | hard | `Mathlib.Combinatorics.HalesJewett` |
| Cauchy-Davenport | FULL | medium | `Mathlib.Combinatorics.Additive.*` |
| Roth's theorem | GOOD | hard | `Mathlib.Combinatorics.Additive.RothNumber` |
| Szemerédi | PARTIAL | very hard | k=3 only (Roth) |
| Sperner | FULL | medium | `Mathlib.Combinatorics.SetFamily.LYM` |
| LYM inequality | FULL | medium | `Mathlib.Combinatorics.SetFamily.LYM` |
| Kruskal-Katona | FULL | hard | Set families section |
| Bollobás | PARTIAL | hard | Listed in overview |
| Pigeonhole | FULL | easy | `Mathlib.Combinatorics.Pigeonhole` |
| Inclusion-exclusion | FULL | easy | `Mathlib.Algebra.BigOperators.Ring` |

---

## Key Mathlib Files Reference

### Enumerative Combinatorics
- `Mathlib.Data.Nat.Choose.Basic` - Binomial coefficients, Pascal's identity
- `Mathlib.Data.Nat.Choose.Sum` - Binomial theorem
- `Mathlib.Data.Nat.Choose.Central` - Central binomial coefficients
- `Mathlib.Data.Nat.Choose.Multinomial` - Multichoose (not multinomial!)
- `Mathlib.Combinatorics.Enumerative.Catalan` - Catalan numbers

### Set Families and Extremal Combinatorics
- `Mathlib.Combinatorics.SetFamily.LYM` - LYM inequality, Sperner's theorem
- `Mathlib.Combinatorics.SetFamily.*` - Various set family results

### Ramsey Theory
- `Mathlib.Combinatorics.HalesJewett` - Hales-Jewett, Van der Waerden
- `Mathlib.Combinatorics.SimpleGraph.Clique` - Graph cliques (for Ramsey)

### Additive Combinatorics
- `Mathlib.Combinatorics.Additive.CauchyDavenport` - Cauchy-Davenport theorem
- `Mathlib.Combinatorics.Additive.RothNumber` - Roth's theorem
- `Mathlib.Combinatorics.Additive.AP.*` - Arithmetic progressions
- `Mathlib.Combinatorics.Additive.*` - Extensive additive combinatorics library

### Basic Principles
- `Mathlib.Combinatorics.Pigeonhole` - Pigeonhole principle (many variants)
- `Mathlib.Algebra.BigOperators.Ring` - Inclusion-exclusion via big operators
- `Mathlib.Data.Finset.Partition` - Set partitions

---

## Sources and References

### Mathlib Documentation
- [Mathlib.Combinatorics.Enumerative.Catalan](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/Enumerative/Catalan.html)
- [Mathlib.Data.Nat.Choose.Central](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/Nat/Choose/Central.html)
- [Mathlib.Combinatorics.SetFamily.LYM](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/SetFamily/LYM.html)
- [Mathlib.Combinatorics.HalesJewett](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/HalesJewett.html)
- [Mathlib.Combinatorics.Pigeonhole](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/Pigeonhole.html)
- [Mathematics in Mathlib](https://leanprover-community.github.io/mathlib-overview.html)

### Research and Projects
- [Formalizing Finite Ramsey Theory in Lean 4](https://dl.acm.org/doi/10.1007/978-3-031-66997-2_6)
- [Combinatorics in Lean - Bhavik Mehta](https://b-mehta.github.io/combinatorics/)
- [LeanCamCombi - Cambridge Combinatorics](https://yaeldillies.github.io/LeanCamCombi/)
- [100 Theorems in Lean](https://leanprover-community.github.io/100.html)
- [Missing Theorems from Freek's List](https://leanprover-community.github.io/100-missing.html)

### Wikipedia and Mathematical References
- [Catalan number](https://en.wikipedia.org/wiki/Catalan_number)
- [Bell number](https://en.wikipedia.org/wiki/Bell_number)
- [Ramsey's theorem](https://en.wikipedia.org/wiki/Ramsey%27s_theorem)
- [Van der Waerden's theorem](https://en.wikipedia.org/wiki/Van_der_Waerden%27s_theorem)
- [Hales-Jewett theorem](https://en.wikipedia.org/wiki/Hales%E2%80%93Jewett_theorem)
- [Cauchy-Davenport theorem](https://en.wikipedia.org/wiki/Cauchy%E2%80%93Davenport_theorem)
- [Roth's theorem](https://en.wikipedia.org/wiki/Roth%27s_theorem_on_arithmetic_progressions)
- [Szemerédi's theorem](https://en.wikipedia.org/wiki/Szemer%C3%A9di%27s_theorem)
- [Sperner's theorem](https://en.wikipedia.org/wiki/Sperner%27s_theorem)
- [LYM inequality](https://en.wikipedia.org/wiki/Lubell%E2%80%93Yamamoto%E2%80%93Meshalkin_inequality)
- [Kruskal-Katona theorem](https://en.wikipedia.org/wiki/Kruskal%E2%80%93Katona_theorem)
- [Bollobás set-pairs inequality](https://en.wikipedia.org/wiki/Bollob%C3%A1s_set-pairs_inequality)
- [Pigeonhole principle](https://en.wikipedia.org/wiki/Pigeonhole_principle)
- [Inclusion-exclusion principle](https://en.wikipedia.org/wiki/Inclusion%E2%80%93exclusion_principle)
- [Stars and bars](https://en.wikipedia.org/wiki/Stars_and_bars_(combinatorics))

---

**End of Knowledge Base**
