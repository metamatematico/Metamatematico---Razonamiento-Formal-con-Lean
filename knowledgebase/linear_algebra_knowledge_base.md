# Linear Algebra Knowledge Base for Lean 4

**Generated:** 2025-12-13
**Purpose:** Research knowledge base for implementing linear algebra axioms and theorems in Lean 4 for dataset generation pairing formal proofs with natural language explanations.

---

## Overview

Linear Algebra is extensively formalized in Lean 4's Mathlib library under `Mathlib.LinearAlgebra.*`. Mathlib approaches vector spaces through a unified `Module` typeclass system rather than separate axioms, with 82 of Wiedijk's 100 theorems formalized including key linear algebra results like Cayley-Hamilton (#49) and Cramer's Rule (#97).

### Content Summary

| Category | Count | Description |
|----------|-------|-------------|
| **Vector Space Axioms** | 8 | Via Module typeclass composition |
| **Linear Map Axioms** | 2 | Additivity and homogeneity |
| **Core Theorems** | 3 | Cayley-Hamilton, Cramer's Rule, Rank-Nullity |
| **Additional Structures** | 7+ | Basis, determinants, eigenvalues, dual, tensor, quotient, inner product |

### Key Insight

Mathlib uses typeclass composition (`AddCommGroup` + `DivisionRing` + `Module`) instead of explicit vector space axioms, enabling broader generality and avoiding instance diamonds.

### Mathlib Approach

Vector spaces are modules over division rings:

```lean
-- A vector space is just a module over a field/division ring
[DivisionRing K] [AddCommGroup V] [Module K V]
```

**Primary Import:** `Mathlib.Algebra.Module.Defs`

---

## Vector Space Axioms (via Module Structure)

### 1. Module Typeclass Definition

**Location:** `Mathlib.Algebra.Module.Defs`

**Formal Definition:**
```lean
class Module (R : Type u) (M : Type v)
  [Semiring R] [AddCommMonoid M] extends DistribMulAction R M where
  add_smul : ∀ (r s : R) (x : M), (r + s) • x = r • x + s • x
  zero_smul : ∀ x : M, (0 : R) • x = 0
```

**The Traditional 8 Vector Space Axioms** are encoded through typeclass composition:

| # | Axiom | Typeclass Source | Lean Property |
|---|-------|------------------|---------------|
| 1 | Addition Closure | `AddCommGroup V` | Implicit in type |
| 2 | Addition Associativity | `AddCommGroup V` | `add_assoc` |
| 3 | Additive Identity | `AddCommGroup V` | `zero_add`, `add_zero` |
| 4 | Additive Inverse | `AddCommGroup V` | `add_neg_cancel` |
| 5 | Scalar Mult Closure | `Module K V` | Implicit in SMul |
| 6 | Scalar Distributivity (over +ᵥ) | `DistribMulAction` | `smul_add` |
| 7 | Scalar Distributivity (over +ₖ) | `Module K V` | `add_smul` |
| 8 | Scalar Compatibility | `DistribMulAction` | `mul_smul` |

**Mathlib Support:** FULL
- **Key Theorems:** `Module.Free.of_divisionRing`, `Module.Basis.ofVectorSpace`
- **Import:** `Mathlib.Algebra.Module.Defs`

**Difficulty:** easy

---

## Linear Map Axioms

### 2. Linear Map Definition

**Location:** `Mathlib.Algebra.Module.LinearMap.Defs`

**Natural Language Statement:**
A linear map (linear transformation) between vector spaces preserves vector addition and scalar multiplication.

**Formal Definition:**
```lean
structure LinearMap (R : Type u) (M : Type v) (M₂ : Type w)
  [Semiring R] [AddCommMonoid M] [AddCommMonoid M₂]
  [Module R M] [Module R M₂] extends M →+ M₂ where
  map_smul' : ∀ (r : R) (x : M), toFun (r • x) = r • toFun x
```

**Notation:** `M →ₗ[R] M₂`

### 3. Additivity Axiom (map_add)

**Natural Language Statement:**
A linear map preserves vector addition: for vectors u, v, f(u + v) = f(u) + f(v).

**Formal Definition:**
```lean
map_add : ∀ (x y : M), f (x + y) = f x + f y
```

**Mathlib Support:** FULL
- **Key Theorem:** `LinearMap.map_add`
- **Import:** `Mathlib.Algebra.Module.LinearMap.Defs`

**Difficulty:** easy

---

### 4. Homogeneity Axiom (map_smul)

**Natural Language Statement:**
A linear map preserves scalar multiplication: for scalar r and vector v, f(r·v) = r·f(v).

**Formal Definition:**
```lean
map_smul : ∀ (r : R) (x : M), f (r • x) = r • f x
```

**Mathlib Support:** FULL
- **Key Theorem:** `LinearMap.map_smul`
- **Import:** `Mathlib.Algebra.Module.LinearMap.Defs`

**Difficulty:** easy

---

## Key Theorems from Wiedijk's 100 List

### 5. Cayley-Hamilton Theorem (#49)

**Natural Language Statement:**
The characteristic polynomial of a matrix, when evaluated at the matrix itself, equals zero. Every square matrix satisfies its own characteristic equation.

**Mathematical Statement:**
For matrix M over commutative ring R: p(M) = 0, where p(t) = det(tI - M).

**Lean 4 Formalization:**
```lean
theorem Matrix.aeval_self_charpoly
  {R : Type u_1} [CommRing R] {n : Type u_4}
  [DecidableEq n] [Fintype n] (M : Matrix n n R) :
  (Polynomial.aeval M) M.charpoly = 0
```

**100 Theorems List:** #49 - Fully formalized

**Mathlib Support:** FULL
- **Key Definitions:** `Matrix.charmatrix`, `Matrix.charpoly`
- **Import:** `Mathlib.LinearAlgebra.Matrix.Charpoly.Basic`
- **Author:** Kim Morrison

**Related Theorems:**
- `Matrix.charpoly_diagonal` - For diagonal matrices
- `Matrix.charpoly_of_upperTriangular` - For triangular matrices
- `LinearMap.aeval_self_charpoly` - For linear maps

**Difficulty:** hard

**Proof Approach:** Follows proof from Dror Bar-Natan's paper.

---

### 6. Cramer's Rule (#97)

**Natural Language Statement:**
For a system of linear equations Ax = b, if A is invertible, then xᵢ = det(Aᵢ) / det(A), where Aᵢ is A with column i replaced by b.

**Lean 4 Formalization:**
```lean
theorem Matrix.mulVec_cramer
  {n : Type v} {α : Type w} [DecidableEq n]
  [Fintype n] [CommRing α] (A : Matrix n n α) (b : n → α) :
  A.mulVec (A.cramer b) = A.det • b
```

**100 Theorems List:** #97 - Fully formalized

**Mathlib Support:** FULL
- **Key Definitions:** `cramerMap`, `cramer`, `adjugate`
- **Import:** `Mathlib.LinearAlgebra.Matrix.Adjugate`
- **Author:** Anne Baanen

**Related Theorems:**
- `mul_adjugate` - A * adj(A) = det(A) • 1
- `adjugate_mul` - adj(A) * A = det(A) • 1
- `det_adjugate` - det(adj(A)) = det(A)^(n-1)

**Difficulty:** medium-hard

---

### 7. Rank-Nullity Theorem

**Natural Language Statement:**
For a linear map f: V → W between finite-dimensional vector spaces, dim(ker f) + dim(range f) = dim(V). The dimension of the domain equals the nullity plus the rank.

**Lean 4 Formalization (Finite Dimensional):**
```lean
theorem LinearMap.finrank_range_add_finrank_ker
  {K : Type u} {V : Type v} [DivisionRing K]
  [AddCommGroup V] [Module K V]
  {V₂ : Type v'} [AddCommGroup V₂] [Module K V₂]
  [FiniteDimensional K V] (f : V →ₗ[K] V₂) :
  FiniteDimensional.finrank K (range f) +
  FiniteDimensional.finrank K (ker f) =
  FiniteDimensional.finrank K V
```

**Lean 4 Formalization (Cardinal Version):**
```lean
theorem LinearMap.rank_range_add_rank_ker
  {R : Type*} [Ring R] {M M₁ : Type*}
  [AddCommGroup M] [Module R M]
  [AddCommGroup M₁] [Module R M₁]
  (f : M →ₗ[R] M₁) :
  Module.rank R (range f) + Module.rank R (ker f) =
  Module.rank R M
```

**Mathlib Support:** FULL
- **Key Class:** `HasRankNullity`
- **Import:** `Mathlib.LinearAlgebra.Dimension.RankNullity`

**Related Theorems:**
- `Submodule.rank_quotient_add_rank` - For quotient spaces
- `Submodule.finrank_quotient` - finrank version

**Difficulty:** medium

---

## Core Concepts

### 8. Basis and Dimension

**Natural Language Statement:**
A basis of a vector space is a linearly independent spanning set. Every vector space has a basis, and all bases have the same cardinality (dimension).

**Location:** `Mathlib.LinearAlgebra.Basis`

**Key Definitions:**
```lean
-- A basis for a module M indexed by ι
structure Basis (ι : Type*) (R : Type*) (M : Type*)
  [Semiring R] [AddCommMonoid M] [Module R M]

-- Module rank (dimension) as a cardinal
def Module.rank (R : Type u) (M : Type v)
  [Semiring R] [AddCommGroup M] [Module R M] : Cardinal

-- Finite rank as a natural number
def FiniteDimensional.finrank (R : Type u) (M : Type v)
  [DivisionRing R] [AddCommGroup M] [Module R M] : ℕ
```

**Linear Independence:**
```lean
def LinearIndependent {ι : Type*} (R : Type*) {M : Type*}
  [Semiring R] [AddCommGroup M] [Module R M]
  (v : ι → M) : Prop
```

**Key Theorems:**
- Every vector space has a basis: `Module.Basis.ofVectorSpace`
- Dimension uniqueness: Any two bases have the same cardinality
- `Module.finBasis` - Finite-dimensional spaces have Fin-indexed basis

**Mathlib Imports:**
- `Mathlib.LinearAlgebra.Basis`
- `Mathlib.LinearAlgebra.Dimension.Basic`
- `Mathlib.LinearAlgebra.Dimension.Finrank`
- `Mathlib.LinearAlgebra.FiniteDimensional.Defs`

**Difficulty:** medium

---

### 9. Determinants

**Location:** `Mathlib.LinearAlgebra.Matrix.Determinant.Basic`

**Definition (Leibniz Formula):**
```lean
def Matrix.det {n : Type*} [DecidableEq n] [Fintype n]
  {R : Type*} [CommRing R] (M : Matrix n n R) : R :=
  ∑ σ : Equiv.Perm n,
    Equiv.Perm.sign σ • ∏ i : n, M (σ i) i
```

**Key Properties:**
- Multilinearity in rows/columns
- Alternating property (row swap changes sign)
- Multiplicativity: `det(AB) = det(A) * det(B)`
- Transpose: `det(A^T) = det(A)`

**Mathlib Imports:**
- `Mathlib.LinearAlgebra.Matrix.Determinant.Basic`
- `Mathlib.LinearAlgebra.Matrix.Adjugate`
- `Mathlib.LinearAlgebra.Matrix.Charpoly.Basic`

**Difficulty:** medium

---

### 10. Eigenvalues and Eigenvectors

**Location:** `Mathlib.LinearAlgebra.Eigenspace.Basic`

**Key Definitions:**
```lean
-- Eigenspace (k=1 case of generalized eigenspace)
abbrev Module.End.eigenspace
  {R : Type v} {M : Type w} [CommRing R]
  [AddCommGroup M] [Module R M]
  (f : End R M) (μ : R) : Submodule R M :=
  (f.genEigenspace μ) 1

-- Has eigenvector: nonzero element in eigenspace
abbrev Module.End.HasEigenvector
  (f : End R M) (μ : R) (x : M) : Prop :=
  x ≠ 0 ∧ x ∈ f.eigenspace μ

-- Has eigenvalue: eigenspace is nontrivial
abbrev Module.End.HasEigenvalue
  (f : End R M) (a : R) : Prop :=
  f.eigenspace a ≠ ⊥
```

**Key Theorems:**
- Eigenvalues are roots of minimal polynomial
- Over algebraically closed fields, every endomorphism has an eigenvalue: `Module.End.exists_eigenvalue`
- Generalized eigenspaces span the space: `Module.End.iSup_genEigenspace_eq_top`

**Mathlib Imports:**
- `Mathlib.LinearAlgebra.Eigenspace.Basic`
- `Mathlib.LinearAlgebra.Eigenspace.Minpoly`
- `Mathlib.LinearAlgebra.Eigenspace.IsAlgClosed`

**Difficulty:** medium-hard

---

### 11. Dual Spaces

**Location:** `Mathlib.LinearAlgebra.Dual.Defs`

**Key Definitions:**
```lean
-- Dual space: R-linear maps M → R
abbrev Module.Dual (R : Type u) (M : Type v)
  [Semiring R] [AddCommGroup M] [Module R M] : Type v :=
  M →ₗ[R] R

-- Evaluation map to double dual
def Module.Dual.eval (R : Type u) (M : Type v)
  [CommSemiring R] [AddCommGroup M] [Module R M] :
  M →ₗ[R] Dual R (Dual R M)

-- Dual basis (for finite bases)
def Basis.dualBasis {ι : Type*} [Fintype ι]
  (b : Basis ι R M) : Basis ι R (Dual R M)
```

**Key Theorems:**
- Reflexive modules: `Module.IsReflexive`
- Finite-dimensional vector spaces are reflexive
- Erdős-Kaplansky: Vector space isomorphic to dual iff finite-dimensional

**Mathlib Imports:**
- `Mathlib.LinearAlgebra.Dual.Defs`
- `Mathlib.LinearAlgebra.Dual.Basis`
- `Mathlib.LinearAlgebra.Dual.Lemmas`

**Difficulty:** medium-hard

---

### 12. Inner Product Spaces

**Location:** `Mathlib.Analysis.InnerProductSpace.Defs`

**Note:** Inner product spaces are in the `Analysis` hierarchy, not `LinearAlgebra`, as they require normed space structure.

**Key Definition:**
```lean
class InnerProductSpace (𝕜 : Type*) (E : Type*)
  [RCLike 𝕜] [NormedAddCommGroup E]
  extends NormedSpace 𝕜 E, Inner 𝕜 E where
  norm_sq_eq_inner : ∀ x : E, ‖x‖^2 = re ⟪x, x⟫
```

**Notation:**
- Real inner product: `⟪·, ·⟫_ℝ`
- Complex inner product: `⟪·, ·⟫_ℂ`

**Key Theorems:**
- Cauchy-Schwarz inequality
- Parallelogram law
- Orthogonal projection exists and is unique
- Riesz representation theorem

**Hilbert Spaces:** `[RCLike 𝕜] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E] [CompleteSpace E]`

**Mathlib Imports:**
- `Mathlib.Analysis.InnerProductSpace.Defs`
- `Mathlib.Analysis.InnerProductSpace.Basic`
- `Mathlib.Analysis.InnerProductSpace.Projection`

**Difficulty:** hard

---

### 13. Tensor Products

**Location:** `Mathlib.LinearAlgebra.TensorProduct.Basic`

**Key Definitions:**
```lean
-- Tensor product of R-modules
def TensorProduct (R : Type u) (M : Type v) (N : Type w)
  [CommSemiring R] [AddCommMonoid M] [AddCommMonoid N]
  [Module R M] [Module R N] : Type (max v w)
```

**Notation:**
- `M ⊗[R] N` - Tensor product space
- `m ⊗ₜ[R] n` - Tensor product of elements

**Universal Property:**
```lean
def TensorProduct.lift
  {P : Type*} [AddCommMonoid P] [Module R P]
  (f : M →ₗ[R] N →ₗ[R] P) :
  TensorProduct R M N →ₗ[R] P
```

**Key Theorems:**
- Associativity: `(M ⊗ N) ⊗ P ≃ₗ[R] M ⊗ (N ⊗ P)`
- Distributivity over products and direct sums

**Mathlib Imports:**
- `Mathlib.LinearAlgebra.TensorProduct.Basic`
- `Mathlib.LinearAlgebra.TensorProduct.Associator`

**Difficulty:** hard

---

### 14. Quotient Spaces

**Location:** `Mathlib.LinearAlgebra.Quotient.Defs`

**Key Definitions:**
```lean
-- Quotient module M ⧸ p for submodule p
def Submodule.Quotient (p : Submodule R M) : Type* :=
  Quotient (Submodule.quotientRel p)

-- Quotient map (as linear map)
def Submodule.mkQ (p : Submodule R M) : M →ₗ[R] M ⧸ p
```

**Key Theorems:**
- First isomorphism theorem: `M ⧸ ker(f) ≃ₗ[R] range(f)`
- Dimension formula: `finrank(M ⧸ N) = finrank(M) - finrank(N)`

**Mathlib Imports:**
- `Mathlib.LinearAlgebra.Quotient.Defs`
- `Mathlib.LinearAlgebra.Quotient.Basic`

**Difficulty:** medium

---

### 15. Isomorphism Theorems for Modules

**Location:** `Mathlib.LinearAlgebra.Quotient.Basic`

**First Isomorphism Theorem:**
For a linear map `f : M →ₗ[R] M₂`:
```lean
M ⧸ ker(f) ≃ₗ[R] range(f)
```

**Second Isomorphism Theorem:**
For submodules `p, q : Submodule R M`:
```lean
p ⧸ (p ⊓ q) ≃ₗ[R] (p ⊔ q) ⧸ q
```

**Third Isomorphism Theorem:**
For submodules `p ≤ q`:
```lean
(M ⧸ p) ⧸ (q ⧸ p) ≃ₗ[R] M ⧸ q
```

**Difficulty:** medium

---

## Notation Reference

| Notation | Meaning | Context |
|----------|---------|---------|
| `M →ₗ[R] N` | R-linear map from M to N | Linear maps |
| `M ≃ₗ[R] N` | R-linear isomorphism | Isomorphisms |
| `M ⊗[R] N` | Tensor product over R | Tensor products |
| `m ⊗ₜ[R] n` | Tensor product of elements | Tensor elements |
| `M ⧸ N` | Quotient module | Quotient spaces |
| `r • m` | Scalar multiplication | Module action |
| `⟪x, y⟫` | Inner product | Inner product spaces |
| `End R M` | Endomorphisms of M | Linear endomorphisms |
| `Dual R M` | Dual space (M →ₗ[R] R) | Dual spaces |
| `ker f` | Kernel of f | Linear maps |
| `range f` | Range (image) of f | Linear maps |

---

## Difficulty Classification

### Easy (Foundational)
- Vector space axioms verification
- Linear map axioms verification
- Basic subspace properties
- Linear independence of simple examples

### Medium
- Rank-nullity theorem
- Basis existence and uniqueness
- Dimension theorems
- Quotient space properties
- Determinant properties
- Dual space basics
- Isomorphism theorems

### Hard
- Cayley-Hamilton theorem
- Cramer's rule (full generality)
- Spectral theorems
- Tensor product universal property
- Inner product space theory
- Minimal polynomial results

### Very Hard
- Structure theorems for finitely generated modules
- Jordan normal form
- Spectral theorem for normal operators
- Erdős-Kaplansky theorem

---

## Quick Reference - Key Imports

```lean
-- Core module theory
import Mathlib.Algebra.Module.Defs
import Mathlib.Algebra.Module.LinearMap.Defs

-- Basis and dimension
import Mathlib.LinearAlgebra.Basis
import Mathlib.LinearAlgebra.Dimension.Basic
import Mathlib.LinearAlgebra.Dimension.Finrank
import Mathlib.LinearAlgebra.FiniteDimensional.Defs

-- Major theorems
import Mathlib.LinearAlgebra.Dimension.RankNullity  -- Rank-nullity
import Mathlib.LinearAlgebra.Matrix.Charpoly.Basic  -- Cayley-Hamilton
import Mathlib.LinearAlgebra.Matrix.Adjugate        -- Cramer's rule

-- Advanced structures
import Mathlib.LinearAlgebra.Eigenspace.Basic       -- Eigenvalues
import Mathlib.LinearAlgebra.Dual.Defs              -- Dual spaces
import Mathlib.LinearAlgebra.TensorProduct.Basic    -- Tensor products
import Mathlib.LinearAlgebra.Quotient.Defs          -- Quotient spaces

-- Inner products (requires Analysis)
import Mathlib.Analysis.InnerProductSpace.Defs
```

---

## References

### Primary Sources
1. [Mathlib4 GitHub Repository](https://github.com/leanprover-community/mathlib4)
2. [Mathlib4 Documentation](https://leanprover-community.github.io/mathlib4_docs/index.html)
3. [Maths in Lean: Linear Algebra](https://leanprover-community.github.io/theories/linear_algebra.html)
4. [100 Theorems in Lean](https://leanprover-community.github.io/100.html)
5. [Mathematics in Lean v4.19.0](https://leanprover-community.github.io/mathematics_in_lean/)

### Secondary Sources
6. [The Lean Mathematical Library (arXiv:1910.09336)](https://arxiv.org/pdf/1910.09336)
7. [Linear Algebra in Lean 4 - Tutorial](https://www.jacobserfaty.com/linear-algebra-in-lean-4)

---

**Document Status:** Ready for dataset generation
**Mathlib Version:** v4.19.0
**Confidence:** High (all claims sourced and verified)
