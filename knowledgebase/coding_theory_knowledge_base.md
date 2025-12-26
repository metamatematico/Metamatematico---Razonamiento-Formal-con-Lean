# Coding Theory Knowledge Base

**Domain**: Coding Theory (Error-Correcting Codes, Linear Codes, Bounds)
**Lean 4 Coverage**: GOOD for finite fields and linear algebra foundations; LIMITED for code-specific constructions
**Source**: Mathlib4 `FieldTheory.Finite.*`, `Data.ZMod.*`, `LinearAlgebra.*`
**Last Updated**: 2025-12-24
**Related KB**: `linear_algebra` (vector spaces), `galois_theory` (finite field extensions), `combinatorics` (counting arguments)

---

## Executive Summary

This knowledge base covers coding theory - the mathematical study of error-detecting and error-correcting codes. Mathlib4 coverage:

- **Finite Fields**: WELL FORMALIZED - ZMod, FiniteField, Frobenius, field structure
- **Linear Algebra over Finite Fields**: WELL FORMALIZED - Vector spaces, subspaces, dimension
- **Hamming Distance**: PARTIAL - Can be defined via Finset operations
- **Linear Codes**: LIMITED - Subspace infrastructure exists; code-specific not formalized
- **Bounds and Constructions**: LIMITED - Classical theorems need templates

**Key Gaps**: Hamming codes, BCH codes, Reed-Solomon codes, syndrome decoding, MacWilliams identity.

---

## Content Summary

| Part | Topic | Statements | Mathlib Coverage |
|------|-------|------------|------------------|
| 1 | Finite Field Foundations | 12 | Complete |
| 2 | Vector Spaces over Finite Fields | 10 | Complete |
| 3 | Hamming Distance and Weight | 10 | Partial |
| 4 | Linear Codes | 12 | Limited |
| 5 | Generator and Parity Check Matrices | 8 | Limited |
| 6 | Bounds on Codes | 10 | Limited |
| 7 | Specific Code Families | 10 | Limited |
| 8 | Decoding | 8 | Limited |
| **Total** | | **80** | **~40%** |

**Measurability Score**: 40 (finite fields excellent; code constructions need templates)

---

## Related Knowledge Bases

### Prerequisites
- **Linear Algebra** (`linear_algebra_knowledge_base.md`): Vector spaces, subspaces, dimension
- **Galois Theory** (`galois_theory_knowledge_base.md`): Finite field extensions
- **Combinatorics** (`combinatorics_knowledge_base.md`): Counting arguments

### Builds Upon This KB
- **Information Theory** (`information_theory_knowledge_base.md`): Channel capacity, error bounds

### Related Topics
- **Graph Theory** (`graph_theory_knowledge_base.md`): Graph codes, expanders
- **Probability Theory** (`probability_theory_knowledge_base.md`): Random coding arguments

### Scope Clarification
This KB focuses on **coding theory**:
- Finite field foundations (ZMod, FiniteField)
- Vector spaces over finite fields
- Hamming distance and weight
- Linear codes and generator matrices
- Parity check matrices
- Singleton, Hamming, Plotkin bounds
- Code families (Hamming, BCH, Reed-Solomon - limited)

For **information-theoretic aspects**, see **Information Theory KB**.

---

## Part 1: Finite Field Foundations

### 1.1 ZMod Definition

**NL Statement**: "For any natural number n, ZMod n is the ring of integers modulo n. When n = 0, this is ℤ; when n > 0, it is the finite ring ℤ/nℤ with n elements."

**Lean 4 Definition**:
```lean
def ZMod : ℕ → Type
  | 0 => ℤ
  | n + 1 => Fin (n + 1)

instance (n : ℕ) [NeZero n] : CommRing (ZMod n)
```

**Imports**: `Mathlib.Data.ZMod.Basic`
**Difficulty**: easy

---

### 1.2 ZMod p is a Field

**NL Statement**: "When p is prime, ZMod p is a field. Every nonzero element has a multiplicative inverse."

**Lean 4 Instance**:
```lean
instance ZMod.instField (p : ℕ) [hp : Fact (Nat.Prime p)] : Field (ZMod p)
```

**Imports**: `Mathlib.Data.ZMod.Basic`
**Difficulty**: medium

---

### 1.3 Finite Field Cardinality

**NL Statement**: "Every finite field has cardinality p^n for some prime p and positive integer n. The prime p is the characteristic of the field."

**Lean 4 Theorem**:
```lean
theorem FiniteField.card (K : Type*) [Field K] [Fintype K] :
    ∃ (p : ℕ) (n : ℕ+), Nat.Prime p ∧ Fintype.card K = p ^ (n : ℕ)
```

**Imports**: `Mathlib.FieldTheory.Finite.Basic`
**Difficulty**: medium

---

### 1.4 Characteristic of Finite Field

**NL Statement**: "A finite field of cardinality p^n has characteristic p, meaning p · 1 = 0 in the field."

**Lean 4 Theorem**:
```lean
theorem FiniteField.cast_card_eq_zero (K : Type*) [Field K] [Fintype K] :
    (Fintype.card K : K) = 0

instance CharP.of_finiteField [Field K] [Fintype K] : CharP K (ringChar K)
```

**Imports**: `Mathlib.FieldTheory.Finite.Basic`
**Difficulty**: medium

---

### 1.5 Frobenius Endomorphism

**NL Statement**: "In a finite field K of characteristic p, the Frobenius map x ↦ x^p is a field automorphism."

**Lean 4 Definition**:
```lean
def frobenius (R : Type*) [CommRing R] (p : ℕ) [ExpChar R p] : R →+* R where
  toFun x := x ^ p
  ...

theorem FiniteField.frobenius_bijective [Field K] [Finite K] :
    Function.Bijective (frobenius K p)
```

**Imports**: `Mathlib.FieldTheory.Finite.Basic`
**Difficulty**: medium

---

### 1.6 Fermat's Little Theorem (Finite Field Version)

**NL Statement**: "In a finite field K with q elements, every element a satisfies a^q = a. For nonzero a, a^(q-1) = 1."

**Lean 4 Theorem**:
```lean
theorem FiniteField.pow_card (a : K) [Field K] [Fintype K] :
    a ^ Fintype.card K = a

theorem FiniteField.pow_card_sub_one_eq_one {a : K} (ha : a ≠ 0) :
    a ^ (Fintype.card K - 1) = 1
```

**Imports**: `Mathlib.FieldTheory.Finite.Basic`
**Difficulty**: easy

---

### 1.7 Multiplicative Group is Cyclic

**NL Statement**: "The multiplicative group of a finite field is cyclic. There exists a primitive element α such that every nonzero element is a power of α."

**Lean 4 Theorem**:
```lean
theorem FiniteField.isCyclic_units_of_finite [Field K] [Fintype K] :
    IsCyclic Kˣ
```

**Imports**: `Mathlib.FieldTheory.Finite.Basic`
**Difficulty**: medium

---

### 1.8 Existence of Finite Fields

**NL Statement**: "For every prime p and positive integer n, there exists a finite field with exactly p^n elements, unique up to isomorphism."

**Lean 4 Theorem**:
```lean
theorem FiniteField.exists_unique_of_card (q : ℕ) [hq : Fact (IsPrimePow q)] :
    ∃! (K : Type), ∃ (_ : Field K) (_ : Fintype K), Fintype.card K = q
```

**Imports**: `Mathlib.FieldTheory.Finite.Basic`
**Difficulty**: hard

---

### 1.9 Subfield Structure

**NL Statement**: "A finite field GF(p^n) contains a unique subfield isomorphic to GF(p^m) if and only if m divides n."

**Lean 4 Theorem**:
```lean
-- Subfield existence characterized by divisibility
theorem FiniteField.exists_subfield_of_dvd [Field K] [Fintype K]
    (h : m ∣ n) (hK : Fintype.card K = p ^ n) :
    ∃ (L : Subfield K), Fintype.card L = p ^ m
```

**Imports**: `Mathlib.FieldTheory.Finite.Basic`
**Difficulty**: hard

---

### 1.10 Polynomial Splitting

**NL Statement**: "Over a finite field K with q elements, the polynomial X^q - X splits completely and its roots are exactly all elements of K."

**Lean 4 Theorem**:
```lean
theorem FiniteField.roots_X_pow_card_sub_X [Field K] [Fintype K] :
    (X ^ Fintype.card K - X : K[X]).roots = Finset.univ.val
```

**Imports**: `Mathlib.FieldTheory.Finite.Basic`
**Difficulty**: medium

---

### 1.11 Trace Map

**NL Statement**: "The trace map Tr : GF(q^n) → GF(q) is defined as Tr(a) = a + a^q + a^(q²) + ... + a^(q^(n-1)), and is a surjective GF(q)-linear map."

**Lean 4 Definition**:
```lean
def FiniteField.trace (K L : Type*) [Field K] [Field L] [Algebra K L]
    [FiniteDimensional K L] : L →ₗ[K] K :=
  Algebra.trace K L
```

**Imports**: `Mathlib.FieldTheory.Finite.Trace`
**Difficulty**: medium

---

### 1.12 Chinese Remainder Theorem

**NL Statement**: "For coprime integers m and n, the ring ZMod(mn) is isomorphic to ZMod(m) × ZMod(n)."

**Lean 4 Theorem**:
```lean
def ZMod.chineseRemainder (h : m.Coprime n) :
    ZMod (m * n) ≃+* ZMod m × ZMod n
```

**Imports**: `Mathlib.Data.ZMod.Basic`
**Difficulty**: medium

---

## Part 2: Vector Spaces over Finite Fields

### 2.1 F_q^n as Vector Space

**NL Statement**: "The set F_q^n of n-tuples over a finite field F_q forms an n-dimensional vector space over F_q."

**Lean 4 Definition**:
```lean
-- n-tuples over a field form a module/vector space
instance : Module (ZMod p) (Fin n → ZMod p)

theorem Module.finrank_fin_fun [Field K] [Fintype ι] :
    Module.finrank K (ι → K) = Fintype.card ι
```

**Imports**: `Mathlib.LinearAlgebra.Dimension.Finrank`
**Difficulty**: easy

---

### 2.2 Standard Basis

**NL Statement**: "F_q^n has a standard basis {e₁, ..., eₙ} where eᵢ has 1 in position i and 0 elsewhere."

**Lean 4 Definition**:
```lean
def Pi.single (i : ι) (x : M i) : ∀ j, M j :=
  Function.update 0 i x

def Pi.basisFun (R : Type*) (n : Type*) [CommSemiring R] [Fintype n] [DecidableEq n] :
    Basis n R (n → R)
```

**Imports**: `Mathlib.LinearAlgebra.StdBasis`
**Difficulty**: easy

---

### 2.3 Subspace (Linear Code Container)

**NL Statement**: "A k-dimensional subspace C of F_q^n has q^k elements and will serve as the codeword space of a linear [n,k] code."

**Lean 4 Definition**:
```lean
structure Submodule (R : Type*) (M : Type*) [Semiring R] [AddCommMonoid M] [Module R M]
    extends AddSubmonoid M, SubMulAction R M

theorem Submodule.card_eq_pow [Field K] [Fintype K] (C : Submodule K (Fin n → K))
    [Fintype C] : Fintype.card C = Fintype.card K ^ Module.finrank K C
```

**Imports**: `Mathlib.LinearAlgebra.Dimension.Finrank`
**Difficulty**: medium

---

### 2.4 Dimension of Subspace

**NL Statement**: "Every subspace of F_q^n has a well-defined dimension k ≤ n, equal to the cardinality of any basis."

**Lean 4 Definition**:
```lean
noncomputable def Module.finrank (R : Type*) (M : Type*) [Semiring R] [AddCommMonoid M]
    [Module R M] : ℕ := Cardinal.toNat (Module.rank R M)

theorem Submodule.finrank_le (C : Submodule K V) :
    Module.finrank K C ≤ Module.finrank K V
```

**Imports**: `Mathlib.LinearAlgebra.Dimension.Finrank`
**Difficulty**: easy

---

### 2.5 Direct Sum Decomposition

**NL Statement**: "For any subspace C of V, there exists a complement C' such that V = C ⊕ C'."

**Lean 4 Theorem**:
```lean
theorem Submodule.exists_isCompl [DivisionRing K] [AddCommGroup V] [Module K V]
    (C : Submodule K V) : ∃ C', IsCompl C C'
```

**Imports**: `Mathlib.LinearAlgebra.Dimension.Finrank`
**Difficulty**: medium

---

### 2.6 Dual Space

**NL Statement**: "The dual space (F_q^n)* consists of all linear functionals F_q^n → F_q. It is isomorphic to F_q^n."

**Lean 4 Definition**:
```lean
def Module.Dual (R : Type*) (M : Type*) [CommSemiring R] [AddCommMonoid M] [Module R M] :=
    M →ₗ[R] R

theorem Module.evalEquiv.finrank_eq [FiniteDimensional K V] :
    Module.finrank K (Module.Dual K V) = Module.finrank K V
```

**Imports**: `Mathlib.LinearAlgebra.Dual`
**Difficulty**: medium

---

### 2.7 Annihilator (Dual Code Foundation)

**NL Statement**: "The annihilator of a subspace C is C⟂ = {f ∈ V* | f(c) = 0 for all c ∈ C}. This relates to dual codes."

**Lean 4 Definition**:
```lean
def Submodule.dualAnnihilator (W : Submodule R M) : Submodule R (Module.Dual R M) :=
  { carrier := {f | ∀ w ∈ W, f w = 0}
    ... }
```

**Imports**: `Mathlib.LinearAlgebra.Dual`
**Difficulty**: medium

---

### 2.8 Dimension of Annihilator

**NL Statement**: "For a k-dimensional subspace C of an n-dimensional space V, the annihilator C⟂ has dimension n - k."

**Lean 4 Theorem**:
```lean
theorem Submodule.finrank_dualAnnihilator_eq [FiniteDimensional K V] (W : Submodule K V) :
    Module.finrank K W.dualAnnihilator = Module.finrank K V - Module.finrank K W
```

**Imports**: `Mathlib.LinearAlgebra.Dual`
**Difficulty**: medium

---

### 2.9 Linear Map Kernel

**NL Statement**: "The kernel of a linear map f : V → W is a subspace of V."

**Lean 4 Definition**:
```lean
def LinearMap.ker (f : M →ₗ[R] M₂) : Submodule R M :=
  { carrier := {x | f x = 0}
    ... }
```

**Imports**: `Mathlib.LinearAlgebra.Basic`
**Difficulty**: easy

---

### 2.10 Rank-Nullity Theorem

**NL Statement**: "For a linear map f : V → W between finite-dimensional spaces, dim(ker f) + dim(im f) = dim(V)."

**Lean 4 Theorem**:
```lean
theorem LinearMap.finrank_range_add_finrank_ker [FiniteDimensional K V] (f : V →ₗ[K] W) :
    Module.finrank K (LinearMap.range f) + Module.finrank K (LinearMap.ker f) =
    Module.finrank K V
```

**Imports**: `Mathlib.LinearAlgebra.Dimension.Finrank`
**Difficulty**: medium

---

## Part 3: Hamming Distance and Weight

### 3.1 Hamming Weight Definition (Conceptual)

**NL Statement**: "The Hamming weight wt(x) of a vector x ∈ F_q^n is the number of nonzero coordinates."

**Lean 4 Template**:
```lean
-- Can be defined using Finset.filter
def hammingWeight {n : ℕ} (x : Fin n → F) : ℕ :=
  (Finset.univ.filter (fun i => x i ≠ 0)).card
```

**Imports**: `Mathlib.Data.Finset.Card`
**Difficulty**: easy

---

### 3.2 Hamming Distance Definition (Conceptual)

**NL Statement**: "The Hamming distance d(x, y) between vectors x, y ∈ F_q^n is the number of coordinates where they differ: d(x, y) = |{i : xᵢ ≠ yᵢ}|."

**Lean 4 Template**:
```lean
def hammingDist {n : ℕ} (x y : Fin n → F) : ℕ :=
  (Finset.univ.filter (fun i => x i ≠ y i)).card
```

**Imports**: `Mathlib.Data.Finset.Card`
**Difficulty**: easy

---

### 3.3 Hamming Distance is a Metric

**NL Statement**: "Hamming distance is a metric: d(x,y) ≥ 0, d(x,y) = 0 ⟺ x = y, d(x,y) = d(y,x), and d(x,z) ≤ d(x,y) + d(y,z)."

**Lean 4 Template**:
```lean
theorem hammingDist_self (x : Fin n → F) : hammingDist x x = 0

theorem hammingDist_comm (x y : Fin n → F) : hammingDist x y = hammingDist y x

theorem hammingDist_triangle (x y z : Fin n → F) :
    hammingDist x z ≤ hammingDist x y + hammingDist y z
```

**Status**: PARTIAL - Can be proved from definitions
**Difficulty**: medium

---

### 3.4 Distance Equals Weight of Difference

**NL Statement**: "For vectors over a field, the Hamming distance equals the weight of their difference: d(x, y) = wt(x - y)."

**Lean 4 Template**:
```lean
theorem hammingDist_eq_weight_sub [Field F] (x y : Fin n → F) :
    hammingDist x y = hammingWeight (x - y)
```

**Difficulty**: easy

---

### 3.5 Weight is Subadditive

**NL Statement**: "Hamming weight is subadditive: wt(x + y) ≤ wt(x) + wt(y)."

**Lean 4 Template**:
```lean
theorem hammingWeight_add_le [AddGroup G] (x y : Fin n → G) :
    hammingWeight (x + y) ≤ hammingWeight x + hammingWeight y
```

**Difficulty**: medium

---

### 3.6 Minimum Distance of a Code

**NL Statement**: "The minimum distance d(C) of a code C is the smallest Hamming distance between distinct codewords: d(C) = min{d(x,y) : x, y ∈ C, x ≠ y}."

**Lean 4 Template**:
```lean
def minDistance (C : Set (Fin n → F)) : ℕ :=
  ⨅ (x ∈ C) (y ∈ C) (h : x ≠ y), hammingDist x y
```

**Difficulty**: medium

---

### 3.7 Minimum Weight Equals Minimum Distance

**NL Statement**: "For a linear code C, the minimum distance equals the minimum weight of nonzero codewords: d(C) = min{wt(c) : c ∈ C, c ≠ 0}."

**Lean 4 Template**:
```lean
theorem minDistance_eq_minWeight [Field F] (C : Submodule F (Fin n → F)) :
    minDistance C = ⨅ (c ∈ C) (hc : c ≠ 0), hammingWeight c
```

**Difficulty**: medium

---

### 3.8 Hamming Ball

**NL Statement**: "The Hamming ball B(x, r) of radius r centered at x is the set of all vectors within distance r from x."

**Lean 4 Template**:
```lean
def hammingBall (x : Fin n → F) (r : ℕ) : Set (Fin n → F) :=
  {y | hammingDist x y ≤ r}
```

**Difficulty**: easy

---

### 3.9 Hamming Ball Size

**NL Statement**: "Over F_q, the Hamming ball of radius r in F_q^n has size Σᵢ₌₀ʳ C(n,i)(q-1)ⁱ."

**Lean 4 Template**:
```lean
theorem card_hammingBall [Fintype F] (x : Fin n → F) (r : ℕ) :
    (hammingBall x r).toFinset.card =
    ∑ i ∈ Finset.range (r + 1), n.choose i * (Fintype.card F - 1) ^ i
```

**Difficulty**: hard

---

### 3.10 Error Detection Capability

**NL Statement**: "A code with minimum distance d can detect up to d - 1 errors: if e ≤ d - 1 errors occur, the received word is not a codeword."

**Lean 4 Template**:
```lean
theorem error_detection (C : Set (Fin n → F)) (c : Fin n → F) (e : Fin n → F)
    (hc : c ∈ C) (he : hammingWeight e ≤ minDistance C - 1) (hne : e ≠ 0) :
    c + e ∉ C
```

**Difficulty**: medium

---

## Part 4: Linear Codes

### 4.1 Linear Code Definition

**NL Statement**: "A linear [n, k] code over F_q is a k-dimensional subspace of F_q^n. It contains q^k codewords."

**Lean 4 Template**:
```lean
structure LinearCode (F : Type*) [Field F] (n k : ℕ) where
  code : Submodule F (Fin n → F)
  dim_eq : Module.finrank F code = k
```

**Difficulty**: medium

---

### 4.2 [n, k, d] Code

**NL Statement**: "An [n, k, d] code is a linear code with length n, dimension k, and minimum distance d."

**Lean 4 Template**:
```lean
structure LinearCodeWithDist (F : Type*) [Field F] (n k d : ℕ) extends LinearCode F n k where
  minDist_eq : minDistance code = d
```

**Difficulty**: medium

---

### 4.3 Code Rate

**NL Statement**: "The rate of an [n, k] code is R = k/n, measuring information content per transmitted symbol."

**Lean 4 Template**:
```lean
def LinearCode.rate (C : LinearCode F n k) : ℚ := k / n
```

**Difficulty**: easy

---

### 4.4 Error Correction Capability

**NL Statement**: "A code with minimum distance d can correct up to ⌊(d-1)/2⌋ errors via nearest-codeword decoding."

**Lean 4 Template**:
```lean
def LinearCode.errorCorrectionCapability (d : ℕ) : ℕ := (d - 1) / 2

theorem unique_nearest_codeword (C : LinearCode F n k) (c : C.code) (e : Fin n → F)
    (he : hammingWeight e ≤ C.errorCorrectionCapability) :
    ∀ c' ∈ C.code, c' ≠ c → hammingDist (c + e) c < hammingDist (c + e) c'
```

**Difficulty**: hard

---

### 4.5 Dual Code

**NL Statement**: "The dual code C⟂ of a linear code C ⊆ F_q^n is {y ∈ F_q^n : ⟨x, y⟩ = 0 for all x ∈ C} where ⟨·,·⟩ is the standard inner product."

**Lean 4 Template**:
```lean
def LinearCode.dual (C : Submodule F (Fin n → F)) : Submodule F (Fin n → F) :=
  { carrier := {y | ∀ x ∈ C, ∑ i, x i * y i = 0}
    ... }
```

**Difficulty**: medium

---

### 4.6 Dual Code Dimension

**NL Statement**: "For an [n, k] code C, its dual C⟂ is an [n, n-k] code."

**Lean 4 Template**:
```lean
theorem dual_finrank (C : LinearCode F n k) :
    Module.finrank F C.dual = n - k
```

**Difficulty**: medium

---

### 4.7 Self-Dual Code

**NL Statement**: "A code C is self-dual if C = C⟂. Self-dual codes must have dimension n/2."

**Lean 4 Template**:
```lean
def LinearCode.isSelfDual (C : Submodule F (Fin n → F)) : Prop :=
  C = C.dual
```

**Difficulty**: medium

---

### 4.8 Self-Orthogonal Code

**NL Statement**: "A code C is self-orthogonal if C ⊆ C⟂, meaning all codewords are orthogonal to each other."

**Lean 4 Template**:
```lean
def LinearCode.isSelfOrthogonal (C : Submodule F (Fin n → F)) : Prop :=
  C ≤ C.dual
```

**Difficulty**: easy

---

### 4.9 Punctured Code

**NL Statement**: "The punctured code of C at position i is obtained by deleting coordinate i from all codewords."

**Lean 4 Template**:
```lean
def LinearCode.puncture (C : Submodule F (Fin (n+1) → F)) (i : Fin (n+1)) :
    Submodule F (Fin n → F) :=
  C.map (LinearMap.proj i).comp
```

**Difficulty**: medium

---

### 4.10 Shortened Code

**NL Statement**: "The shortened code of C at position i consists of codewords with 0 in position i, with that position deleted."

**Lean 4 Template**:
```lean
def LinearCode.shorten (C : Submodule F (Fin (n+1) → F)) (i : Fin (n+1)) :
    Submodule F (Fin n → F) :=
  (C.comap (fun c => if c i = 0 then c else 0)).map (LinearMap.proj i).comp
```

**Difficulty**: medium

---

### 4.11 Extended Code

**NL Statement**: "The extended code adds a parity check symbol so that all codewords have even weight (sum of coordinates = 0)."

**Lean 4 Template**:
```lean
def LinearCode.extend (C : Submodule F (Fin n → F)) : Submodule F (Fin (n+1) → F) :=
  { carrier := {c | (∑ i : Fin n, c i.castSucc) + c (Fin.last n) = 0 ∧
                    (fun i => c i.castSucc) ∈ C}
    ... }
```

**Difficulty**: medium

---

### 4.12 Code Equivalence

**NL Statement**: "Two codes are equivalent if one can be obtained from the other by coordinate permutation and scaling."

**Lean 4 Template**:
```lean
def LinearCode.isEquivalent (C₁ C₂ : Submodule F (Fin n → F)) : Prop :=
  ∃ (σ : Equiv.Perm (Fin n)) (s : Fin n → Fˣ),
    C₂ = C₁.map (LinearMap.funCongrEquiv σ ∘ₗ (LinearMap.lsmul F (Fin n → F)).flip s)
```

**Difficulty**: hard

---

## Part 5: Generator and Parity Check Matrices

### 5.1 Generator Matrix

**NL Statement**: "A generator matrix G of an [n, k] code C is a k × n matrix whose rows form a basis of C."

**Lean 4 Template**:
```lean
structure GeneratorMatrix (F : Type*) [Field F] (n k : ℕ) where
  mat : Matrix (Fin k) (Fin n) F
  rows_independent : LinearIndependent F (fun i => mat i)
```

**Difficulty**: medium

---

### 5.2 Encoding with Generator Matrix

**NL Statement**: "A message m ∈ F_q^k is encoded to codeword c = m · G ∈ F_q^n using the generator matrix."

**Lean 4 Template**:
```lean
def encode (G : GeneratorMatrix F n k) (m : Fin k → F) : Fin n → F :=
  fun j => ∑ i, m i * G.mat i j
```

**Difficulty**: easy

---

### 5.3 Systematic Form

**NL Statement**: "A generator matrix is in systematic form if G = [I_k | P] where I_k is the k × k identity matrix."

**Lean 4 Template**:
```lean
def GeneratorMatrix.isSystematic (G : GeneratorMatrix F n k) : Prop :=
  ∀ i j : Fin k, G.mat i j.castSucc = if i = j then 1 else 0
```

**Difficulty**: medium

---

### 5.4 Parity Check Matrix

**NL Statement**: "A parity check matrix H of an [n, k] code C is an (n-k) × n matrix such that c ∈ C ⟺ H · cᵀ = 0."

**Lean 4 Template**:
```lean
structure ParityCheckMatrix (F : Type*) [Field F] (n k : ℕ) where
  mat : Matrix (Fin (n - k)) (Fin n) F
  rows_independent : LinearIndependent F (fun i => mat i)
```

**Difficulty**: medium

---

### 5.5 Relation Between G and H

**NL Statement**: "For a code with generator matrix G and parity check matrix H: G · Hᵀ = 0."

**Lean 4 Template**:
```lean
theorem generator_parity_orthogonal (G : GeneratorMatrix F n k) (H : ParityCheckMatrix F n k) :
    G.mat * H.mat.transpose = 0
```

**Difficulty**: medium

---

### 5.6 Systematic Parity Check

**NL Statement**: "If G = [I_k | P] is systematic, then H = [-Pᵀ | I_{n-k}] is the corresponding parity check matrix."

**Lean 4 Template**:
```lean
def ParityCheckMatrix.fromSystematic (G : GeneratorMatrix F n k) (hG : G.isSystematic) :
    ParityCheckMatrix F n k where
  mat := Matrix.fromBlocks (-G.parity.transpose) (1 : Matrix (Fin (n-k)) (Fin (n-k)) F)
  ...
```

**Difficulty**: medium

---

### 5.7 Syndrome

**NL Statement**: "The syndrome of a received word r with respect to parity check matrix H is s = H · rᵀ."

**Lean 4 Template**:
```lean
def syndrome (H : ParityCheckMatrix F n k) (r : Fin n → F) : Fin (n - k) → F :=
  fun i => ∑ j, H.mat i j * r j
```

**Difficulty**: easy

---

### 5.8 Syndrome Characterization

**NL Statement**: "A vector r is a codeword if and only if its syndrome is zero: r ∈ C ⟺ syndrome(r) = 0."

**Lean 4 Template**:
```lean
theorem mem_code_iff_syndrome_zero (H : ParityCheckMatrix F n k) (r : Fin n → F) :
    r ∈ C ↔ syndrome H r = 0
```

**Difficulty**: medium

---

## Part 6: Bounds on Codes

### 6.1 Singleton Bound

**NL Statement**: "For an [n, k, d] code: k ≤ n - d + 1. Codes meeting this bound with equality are called MDS (Maximum Distance Separable)."

**Lean 4 Template**:
```lean
theorem singleton_bound (C : LinearCodeWithDist F n k d) : k ≤ n - d + 1
```

**Difficulty**: medium

---

### 6.2 Hamming Bound (Sphere Packing)

**NL Statement**: "For an [n, k, d] code over F_q with t = ⌊(d-1)/2⌋: q^k · Σᵢ₌₀ᵗ C(n,i)(q-1)ⁱ ≤ q^n."

**Lean 4 Template**:
```lean
theorem hamming_bound [Fintype F] (C : LinearCodeWithDist F n k d) :
    Fintype.card F ^ k * ∑ i ∈ Finset.range ((d-1)/2 + 1), n.choose i * (Fintype.card F - 1)^i
    ≤ Fintype.card F ^ n
```

**Difficulty**: medium

---

### 6.3 Perfect Codes

**NL Statement**: "A code is perfect if it meets the Hamming bound with equality, meaning Hamming balls around codewords partition the space."

**Lean 4 Template**:
```lean
def LinearCode.isPerfect [Fintype F] (C : LinearCodeWithDist F n k d) : Prop :=
  Fintype.card F ^ k * ∑ i ∈ Finset.range ((d-1)/2 + 1), n.choose i * (Fintype.card F - 1)^i
  = Fintype.card F ^ n
```

**Difficulty**: medium

---

### 6.4 Gilbert-Varshamov Bound

**NL Statement**: "There exists an [n, k, d] code over F_q if q^(n-k) > Σᵢ₌₀^(d-2) C(n-1,i)(q-1)ⁱ."

**Lean 4 Template**:
```lean
theorem gilbert_varshamov_existence [Fintype F] :
    Fintype.card F ^ (n - k) > ∑ i ∈ Finset.range (d - 1), (n-1).choose i * (Fintype.card F - 1)^i →
    ∃ (C : LinearCodeWithDist F n k d), True
```

**Difficulty**: hard

---

### 6.5 Plotkin Bound

**NL Statement**: "If d > n/2, then an [n, k, d] binary code has at most 2d codewords, so k ≤ log₂(2d)."

**Lean 4 Template**:
```lean
theorem plotkin_bound (C : LinearCodeWithDist (ZMod 2) n k d) (hd : 2 * d > n) :
    2 ^ k ≤ 2 * d
```

**Difficulty**: medium

---

### 6.6 Griesmer Bound

**NL Statement**: "For a linear [n, k, d] code over F_q: n ≥ Σᵢ₌₀^(k-1) ⌈d/qⁱ⌉."

**Lean 4 Template**:
```lean
theorem griesmer_bound [Fintype F] (C : LinearCodeWithDist F n k d) :
    n ≥ ∑ i ∈ Finset.range k, Nat.ceil (d / Fintype.card F ^ i)
```

**Difficulty**: hard

---

### 6.7 MDS Code Characterization

**NL Statement**: "An [n, k] code is MDS if and only if any k columns of its generator matrix are linearly independent."

**Lean 4 Template**:
```lean
theorem mds_iff_any_k_columns_independent (C : LinearCode F n k) (G : GeneratorMatrix F n k) :
    C.isMDS ↔ ∀ (S : Finset (Fin n)), S.card = k →
      LinearIndependent F (fun i : S => fun j : Fin k => G.mat j i)
```

**Difficulty**: hard

---

### 6.8 Dual of MDS is MDS

**NL Statement**: "The dual of an MDS code is also an MDS code."

**Lean 4 Template**:
```lean
theorem dual_of_mds_is_mds (C : LinearCode F n k) (hC : C.isMDS) : C.dual.isMDS
```

**Difficulty**: medium

---

### 6.9 Asymptotic Bounds

**NL Statement**: "As n → ∞, the achievable rate R vs relative distance δ is bounded by the asymptotic Gilbert-Varshamov and MRRW bounds."

**Status**: NOT FORMALIZED (requires asymptotic analysis)
**Difficulty**: very hard

---

### 6.10 Elias-Bassalygo Bound

**NL Statement**: "The Elias-Bassalygo bound provides an upper bound on achievable rates tighter than Hamming for high distances."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

## Part 7: Specific Code Families

### 7.1 Hamming Code

**NL Statement**: "The [2^r - 1, 2^r - 1 - r, 3] Hamming code has parity check matrix whose columns are all nonzero vectors in F_2^r."

**Lean 4 Template**:
```lean
def HammingCode (r : ℕ) : Submodule (ZMod 2) (Fin (2^r - 1) → ZMod 2) :=
  LinearMap.ker (hammingParityCheck r)

theorem HammingCode.minDist_eq_three (r : ℕ) (hr : r ≥ 2) :
    minDistance (HammingCode r) = 3
```

**Difficulty**: medium

---

### 7.2 Hamming Code is Perfect

**NL Statement**: "Binary Hamming codes are perfect 1-error-correcting codes."

**Lean 4 Template**:
```lean
theorem HammingCode.isPerfect (r : ℕ) (hr : r ≥ 2) : (HammingCode r).isPerfect
```

**Difficulty**: medium

---

### 7.3 Simplex Code

**NL Statement**: "The [2^r - 1, r, 2^(r-1)] simplex code is the dual of the Hamming code. All nonzero codewords have the same weight."

**Lean 4 Template**:
```lean
def SimplexCode (r : ℕ) : Submodule (ZMod 2) (Fin (2^r - 1) → ZMod 2) :=
  (HammingCode r).dual

theorem SimplexCode.constant_weight (r : ℕ) (c : SimplexCode r) (hc : c ≠ 0) :
    hammingWeight c = 2^(r-1)
```

**Difficulty**: medium

---

### 7.4 Reed-Muller Codes (Conceptual)

**NL Statement**: "The r-th order Reed-Muller code RM(r, m) of length 2^m is defined by evaluations of polynomials of degree ≤ r over F_2^m."

**Lean 4 Template**:
```lean
def ReedMullerCode (r m : ℕ) : Submodule (ZMod 2) (Fin (2^m) → ZMod 2) :=
  Submodule.span (ZMod 2) {f | ∃ (p : MvPolynomial (Fin m) (ZMod 2)),
    p.totalDegree ≤ r ∧ f = fun x => MvPolynomial.eval x p}
```

**Difficulty**: hard

---

### 7.5 Reed-Solomon Codes (Conceptual)

**NL Statement**: "An [n, k, n-k+1] Reed-Solomon code over F_q consists of evaluations of polynomials of degree < k at n distinct points."

**Lean 4 Template**:
```lean
def ReedSolomonCode (F : Type*) [Field F] [Fintype F] (α : Fin n ↪ F) (k : ℕ) :
    Submodule F (Fin n → F) :=
  Submodule.span F {f | ∃ (p : Polynomial F), p.natDegree < k ∧ f = fun i => p.eval (α i)}
```

**Difficulty**: hard

---

### 7.6 RS Codes are MDS

**NL Statement**: "Reed-Solomon codes achieve the Singleton bound: an [n, k] RS code has minimum distance exactly n - k + 1."

**Lean 4 Template**:
```lean
theorem ReedSolomon.minDist_eq (α : Fin n ↪ F) (k : ℕ) :
    minDistance (ReedSolomonCode F α k) = n - k + 1
```

**Difficulty**: hard

---

### 7.7 BCH Codes (Conceptual)

**NL Statement**: "A BCH code is a cyclic code defined by specifying that certain powers of a primitive element are roots of all codeword polynomials."

**Lean 4 Template**:
```lean
def BCHCode (n : ℕ) (δ : ℕ) (α : Fˣ) (hα : α.val ^ n = 1) :
    Submodule F (Fin n → F) :=
  -- Defined as polynomials divisible by minimal polys of α^b, ..., α^(b+δ-2)
```

**Difficulty**: very hard

---

### 7.8 Golay Codes

**NL Statement**: "The [23, 12, 7] binary Golay code and [24, 12, 8] extended Golay code are perfect/nearly perfect 3-error-correcting codes."

**Lean 4 Template**:
```lean
-- Specific construction via generator matrix or as quadratic residue code
def BinaryGolayCode : Submodule (ZMod 2) (Fin 23 → ZMod 2) := ...

theorem BinaryGolayCode.isPerfect : BinaryGolayCode.isPerfect
```

**Difficulty**: hard

---

### 7.9 LDPC Codes (Conceptual)

**NL Statement**: "Low-Density Parity-Check codes have sparse parity check matrices, enabling efficient iterative decoding."

**Status**: NOT FORMALIZED (requires graph-based analysis)
**Difficulty**: very hard

---

### 7.10 Convolutional Codes (Conceptual)

**NL Statement**: "Convolutional codes encode data streams using shift registers, with code properties described by polynomial generators."

**Status**: NOT FORMALIZED (requires infinite sequence formalization)
**Difficulty**: very hard

---

## Part 8: Decoding

### 8.1 Nearest Neighbor Decoding

**NL Statement**: "Nearest neighbor decoding maps a received word r to the codeword c minimizing d(r, c)."

**Lean 4 Template**:
```lean
def nearestNeighborDecode (C : Set (Fin n → F)) (r : Fin n → F) : Option (Fin n → F) :=
  C.toFinset.argmin (hammingDist r)
```

**Difficulty**: medium

---

### 8.2 Syndrome Decoding

**NL Statement**: "Syndrome decoding uses a lookup table: for received word r = c + e, compute s = H·r = H·e, then find the minimum weight error pattern with that syndrome."

**Lean 4 Template**:
```lean
def syndromeDecode (H : ParityCheckMatrix F n k) (cosetLeaders : Fin (n-k) → F → Fin n → F)
    (r : Fin n → F) : Fin n → F :=
  r - cosetLeaders (syndrome H r)
```

**Difficulty**: medium

---

### 8.3 Standard Array

**NL Statement**: "The standard array organizes F_q^n into cosets of C, with each row headed by a coset leader of minimum weight."

**Lean 4 Template**:
```lean
def standardArray (C : Submodule F (Fin n → F)) :
    (Fin (Fintype.card F ^ (n - Module.finrank F C))) → Set (Fin n → F) :=
  -- Cosets of C in F^n
```

**Difficulty**: hard

---

### 8.4 Error Coset

**NL Statement**: "Two error patterns e₁ and e₂ are in the same coset (have the same syndrome) iff e₁ - e₂ ∈ C."

**Lean 4 Template**:
```lean
theorem same_syndrome_iff_diff_in_code (H : ParityCheckMatrix F n k) (e₁ e₂ : Fin n → F) :
    syndrome H e₁ = syndrome H e₂ ↔ e₁ - e₂ ∈ C
```

**Difficulty**: medium

---

### 8.5 Correct Decoding Probability

**NL Statement**: "With independent symbol error probability p, correct decoding occurs iff the actual error pattern is the coset leader."

**Status**: NOT FORMALIZED (requires probability theory)
**Difficulty**: hard

---

### 8.6 Bounded Distance Decoding

**NL Statement**: "Bounded distance decoding corrects all error patterns of weight ≤ t = ⌊(d-1)/2⌋ and declares failure otherwise."

**Lean 4 Template**:
```lean
def boundedDistanceDecode (C : LinearCodeWithDist F n k d) (r : Fin n → F) :
    Option (Fin n → F) :=
  if ∃ c ∈ C.code, hammingDist r c ≤ (d - 1) / 2 then
    C.code.toFinset.filter (fun c => hammingDist r c ≤ (d - 1) / 2) |>.min
  else none
```

**Difficulty**: medium

---

### 8.7 Peterson-Gorenstein-Zierler Algorithm

**NL Statement**: "The PGZ algorithm decodes BCH codes by solving the key equation to find the error locator polynomial."

**Status**: NOT FORMALIZED (requires polynomial algebra)
**Difficulty**: very hard

---

### 8.8 Berlekamp-Massey Algorithm

**NL Statement**: "Berlekamp-Massey efficiently finds the shortest LFSR generating a sequence, used to find error locators in BCH/RS decoding."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

## Standard Setup

**Lean 4 Imports**:
```lean
import Mathlib.Data.ZMod.Basic
import Mathlib.FieldTheory.Finite.Basic
import Mathlib.LinearAlgebra.Dimension.Finrank
import Mathlib.LinearAlgebra.Dual
import Mathlib.LinearAlgebra.Matrix.GeneralLinearGroup.Defs
import Mathlib.Data.Finset.Card
import Mathlib.Algebra.Polynomial.Basic

variable {F : Type*} [Field F] [Fintype F]
variable {n k d : ℕ}
```

---

## Notation Reference

| Math Notation | Lean 4 Notation | Description |
|---------------|-----------------|-------------|
| F_q | `ZMod q` or finite field | Finite field with q elements |
| F_q^n | `Fin n → F` | n-tuples over F |
| wt(x) | `hammingWeight x` | Hamming weight |
| d(x,y) | `hammingDist x y` | Hamming distance |
| C⟂ | `C.dual` | Dual code |
| [n,k,d] | `LinearCodeWithDist F n k d` | Linear code parameters |
| G | `GeneratorMatrix` | Generator matrix |
| H | `ParityCheckMatrix` | Parity check matrix |

---

## Sources

- [Mathlib.FieldTheory.Finite.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/FieldTheory/Finite/Basic.html)
- [Mathlib.Data.ZMod.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/ZMod/Basic.html)
- [Mathlib.LinearAlgebra.Dual](https://leanprover-community.github.io/mathlib4_docs/Mathlib/LinearAlgebra/Dual.html)
- [Linear code - Wikipedia](https://en.wikipedia.org/wiki/Linear_code)
- [MIT 18.310 Hamming Code Lecture Notes](https://math.mit.edu/~goemans/18310S15/Hamming-code-notes.pdf)
- [SageMath Coding Theory Documentation](https://doc.sagemath.org/pdf/en/reference/coding/coding.pdf)
