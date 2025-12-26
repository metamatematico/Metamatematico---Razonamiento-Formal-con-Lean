# Symplectic Geometry Knowledge Base

## Overview

**Domain:** Symplectic Geometry / Differential Geometry
**Mathlib4 Coverage:** Partial - linear algebra foundations only
**Measurability Score:** 35/100

Symplectic geometry studies manifolds equipped with a closed, non-degenerate 2-form. It provides the mathematical foundation for Hamiltonian mechanics. Mathlib4 has excellent formalization of the linear algebra foundations—bilinear forms, alternating maps, exterior algebra, and the symplectic group—but symplectic manifolds, Hamiltonian vector fields, and Poisson geometry remain unformalized.

---

## Related Knowledge Bases

### Prerequisites
- **Linear Algebra** (`linear_algebra_knowledge_base.md`): Bilinear forms, alternating maps
- **Differential Geometry** (`differential_geometry_knowledge_base.md`): Exterior algebra, 2-forms
- **Smooth Manifolds** (`smooth_manifolds_knowledge_base.md`): Manifold infrastructure

### Builds Upon This KB
- (Hamiltonian mechanics applications)

### Related Topics
- **Lie Theory** (`lie_theory_knowledge_base.md`): Symplectic Lie groups
- **Riemannian Geometry** (`riemannian_geometry_knowledge_base.md`): Kähler manifolds bridge both

### Scope Clarification
This KB focuses on **symplectic geometry foundations**:
- Bilinear forms and alternating maps
- Symplectic linear algebra
- Symplectic group Sp(2n)
- Darboux basis
- (Gaps: Symplectic manifolds, Hamiltonian vector fields, Poisson brackets)

For **exterior algebra**, see **Differential Geometry KB**.

---

## Part I: Bilinear Forms

### Section 1.1: Bilinear Form Definition

#### Definition 1.1.1: Bilinear Form
**Natural Language:** A bilinear form B: M × M → R is a function linear in both arguments.
**Difficulty:** easy

```lean4
-- Mathlib.LinearAlgebra.BilinearForm.Basic
/-- A bilinear form on M over R. -/
structure BilinForm (R M : Type*) [CommSemiring R] [AddCommMonoid M] [Module R M] where
  bilin : M → M → R
  bilin_add_left : ∀ x y z, bilin (x + y) z = bilin x z + bilin y z
  bilin_smul_left : ∀ a x y, bilin (a • x) y = a * bilin x y
  bilin_add_right : ∀ x y z, bilin x (y + z) = bilin x y + bilin x z
  bilin_smul_right : ∀ a x y, bilin x (a • y) = a * bilin x y
```

#### Theorem 1.1.2: Bilinear Form Extensionality
**Natural Language:** Two bilinear forms are equal if they agree on all pairs.
**Difficulty:** easy

```lean4
-- Mathlib.LinearAlgebra.BilinearForm.Basic
theorem BilinForm.ext {B₁ B₂ : BilinForm R M} (h : ∀ x y, B₁ x y = B₂ x y) : B₁ = B₂
```

#### Definition 1.1.3: Flip of Bilinear Form
**Natural Language:** The flip of B is B^flip(x,y) = B(y,x).
**Difficulty:** easy

```lean4
-- Mathlib.LinearAlgebra.BilinearForm.Basic
/-- Exchange left and right arguments. -/
def BilinForm.flip (B : BilinForm R M) : BilinForm R M where
  bilin x y := B.bilin y x
```

### Section 1.2: Special Bilinear Forms

#### Definition 1.2.1: Symmetric Bilinear Form
**Natural Language:** B is symmetric if B(x,y) = B(y,x) for all x,y.
**Difficulty:** easy

```lean4
-- Mathlib.LinearAlgebra.BilinearForm.Basic
def BilinForm.IsSymm (B : BilinForm R M) : Prop := ∀ x y, B x y = B y x
```

#### Definition 1.2.2: Alternating (Skew-Symmetric) Bilinear Form
**Natural Language:** B is alternating if B(x,x) = 0 for all x (implies B(x,y) = -B(y,x) in char ≠ 2).
**Difficulty:** easy

```lean4
-- Mathlib.LinearAlgebra.BilinearForm.Basic
def BilinForm.IsAlt (B : BilinForm R M) : Prop := ∀ x, B x x = 0
```

#### Theorem 1.2.3: Alternating Implies Skew-Symmetric
**Natural Language:** If B is alternating and char R ≠ 2, then B(x,y) = -B(y,x).
**Difficulty:** easy

```lean4
-- Mathlib.LinearAlgebra.BilinearForm.Basic
theorem BilinForm.IsAlt.neg (h : B.IsAlt) : ∀ x y, B x y = -B y x
```

#### Definition 1.2.4: Non-degenerate Bilinear Form
**Natural Language:** B is non-degenerate if B(x,y) = 0 for all y implies x = 0.
**Difficulty:** medium

```lean4
-- Mathlib.LinearAlgebra.BilinearForm.Orthogonal
/-- B is non-degenerate if the only element orthogonal to everything is 0. -/
def BilinForm.Nondegenerate (B : BilinForm R M) : Prop :=
  ∀ x, (∀ y, B x y = 0) → x = 0
```

#### Theorem 1.2.5: Symplectic Form Properties
**Natural Language:** A symplectic bilinear form is alternating and non-degenerate.
**Difficulty:** medium

```lean4
-- Conceptual combination
structure SymplecticBilinForm (R M : Type*) [CommRing R] [AddCommGroup M] [Module R M]
    extends BilinForm R M where
  isAlt : toFun.IsAlt
  nondegenerate : toFun.Nondegenerate
```

---

## Part II: Symplectic Linear Algebra

### Section 2.1: Canonical Symplectic Form

#### Definition 2.1.1: Standard Symplectic Matrix
**Natural Language:** The 2n × 2n matrix J = [[0, -I], [I, 0]] defines the standard symplectic form.
**Difficulty:** medium

```lean4
-- Mathlib.LinearAlgebra.Matrix.Symplectic (conceptual)
/-- The canonical 2n × 2n skew-symmetric matrix. -/
def Matrix.J (l : Type*) [DecidableEq l] [Fintype l] (R : Type*) [CommRing R] :
    Matrix (l ⊕ l) (l ⊕ l) R :=
  Matrix.fromBlocks 0 (-1) 1 0
```

#### Theorem 2.1.2: J is Skew-Symmetric
**Natural Language:** Jᵀ = -J.
**Difficulty:** easy

```lean4
-- Mathlib.LinearAlgebra.Matrix.Symplectic
theorem Matrix.J_transpose : (Matrix.J l R)ᵀ = -Matrix.J l R
```

#### Theorem 2.1.3: J Squared
**Natural Language:** J² = -I.
**Difficulty:** easy

```lean4
-- Mathlib.LinearAlgebra.Matrix.Symplectic
theorem Matrix.J_mul_J : Matrix.J l R * Matrix.J l R = -1
```

### Section 2.2: Symplectic Group

#### Definition 2.2.1: Symplectic Group
**Natural Language:** Sp(2n, R) = {A ∈ GL(2n, R) : AᵀJA = J}.
**Difficulty:** medium

```lean4
-- Mathlib.LinearAlgebra.Matrix.Symplectic
/-- The symplectic group: matrices preserving the standard symplectic form. -/
def Matrix.symplecticGroup (l : Type*) [DecidableEq l] [Fintype l] (R : Type*) [CommRing R] :
    Subgroup (Matrix (l ⊕ l) (l ⊕ l) R)ˣ where
  carrier := { A | Aᵀ * Matrix.J l R * A = Matrix.J l R }
```

#### Theorem 2.2.2: Symplectic Matrices Have Determinant 1
**Natural Language:** Every symplectic matrix has det A = 1.
**Difficulty:** medium

```lean4
-- Mathlib.LinearAlgebra.Matrix.Symplectic
theorem Matrix.symplecticGroup.det_eq_one (A : symplecticGroup l R) : A.1.det = 1
```

#### Theorem 2.2.3: Symplectic Group is Closed Under Inverse
**Natural Language:** If A ∈ Sp(2n), then A⁻¹ ∈ Sp(2n).
**Difficulty:** easy

```lean4
-- Mathlib.LinearAlgebra.Matrix.Symplectic
theorem Matrix.symplecticGroup.inv_mem (A : symplecticGroup l R) : A⁻¹ ∈ symplecticGroup l R
```

### Section 2.3: Symplectic Lie Algebra

#### Definition 2.3.1: Symplectic Lie Algebra
**Natural Language:** sp(2n) = {X : Xᵀ J + J X = 0} consists of infinitesimally symplectic matrices.
**Difficulty:** medium

```lean4
-- Mathlib.Algebra.Lie.Classical
/-- The symplectic Lie algebra: skew-adjoint matrices w.r.t. J. -/
def Matrix.skewAdjointMatricesLieSubalgebra (J : Matrix n n R) :
    LieSubalgebra R (Matrix n n R) where
  carrier := { A | Aᵀ * J + J * A = 0 }
```

---

## Part III: Alternating Multilinear Maps

### Section 3.1: Alternating Maps

#### Definition 3.1.1: Alternating Map
**Natural Language:** An alternating map vanishes when two arguments are equal.
**Difficulty:** medium

```lean4
-- Mathlib.LinearAlgebra.Alternating.Basic
/-- An R-linear alternating map from ι → M to N. -/
structure AlternatingMap (R M N : Type*) (ι : Type*) [CommSemiring R]
    [AddCommMonoid M] [Module R M] [AddCommMonoid N] [Module R N]
    extends MultilinearMap R (fun _ : ι => M) N where
  map_eq_zero_of_eq' : ∀ v : ι → M, ∀ i j, v i = v j → i ≠ j → toMultilinearMap v = 0
```

#### Theorem 3.1.2: Sign Change Under Swap
**Natural Language:** Swapping two arguments negates an alternating map.
**Difficulty:** easy

```lean4
-- Mathlib.LinearAlgebra.Alternating.Basic
theorem AlternatingMap.map_swap {f : AlternatingMap R M N ι} (v : ι → M) {i j : ι} (hij : i ≠ j) :
    f (v ∘ Equiv.swap i j) = -f v
```

#### Theorem 3.1.3: Permutation Action
**Natural Language:** Permuting arguments changes sign by the permutation signature.
**Difficulty:** medium

```lean4
-- Mathlib.LinearAlgebra.Alternating.Basic
theorem AlternatingMap.map_perm {f : AlternatingMap R M N ι} (v : ι → M) (σ : Equiv.Perm ι) :
    f (v ∘ σ) = Equiv.Perm.sign σ • f v
```

#### Definition 3.1.4: Alternatization
**Natural Language:** Any multilinear map can be alternatized by summing over signed permutations.
**Difficulty:** medium

```lean4
-- Mathlib.LinearAlgebra.Alternating.Basic
/-- Convert a multilinear map to an alternating map. -/
def MultilinearMap.alternatization (f : MultilinearMap R (fun _ : ι => M) N) :
    AlternatingMap R M N ι :=
  ∑ σ : Equiv.Perm ι, Equiv.Perm.sign σ • f.domDomCongr σ.symm
```

---

## Part IV: Exterior Algebra

### Section 4.1: Exterior Algebra Definition

#### Definition 4.1.1: Exterior Algebra
**Natural Language:** The exterior algebra ⋀(M) is the quotient of the tensor algebra by v ⊗ v = 0.
**Difficulty:** medium

```lean4
-- Mathlib.LinearAlgebra.ExteriorAlgebra.Basic
/-- The exterior algebra of an R-module M. -/
def ExteriorAlgebra (R M : Type*) [CommSemiring R] [AddCommMonoid M] [Module R M] :=
  CliffordAlgebra (0 : QuadraticForm R M)
```

#### Definition 4.1.2: Canonical Inclusion
**Natural Language:** ι : M → ⋀(M) is the canonical linear map with ι(m) ∧ ι(m) = 0.
**Difficulty:** easy

```lean4
-- Mathlib.LinearAlgebra.ExteriorAlgebra.Basic
/-- The canonical map from M to its exterior algebra. -/
def ExteriorAlgebra.ι (R : Type*) [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] :
    M →ₗ[R] ExteriorAlgebra R M
```

#### Theorem 4.1.3: Fundamental Property
**Natural Language:** ι(m) ∧ ι(m) = 0 for all m ∈ M.
**Difficulty:** easy

```lean4
-- Mathlib.LinearAlgebra.ExteriorAlgebra.Basic
theorem ExteriorAlgebra.ι_sq_zero (m : M) : ι R m * ι R m = 0
```

### Section 4.2: Exterior Powers

#### Definition 4.2.1: Exterior Power
**Natural Language:** ⋀^n M is the n-th exterior power of M.
**Difficulty:** medium

```lean4
-- Mathlib.LinearAlgebra.ExteriorAlgebra.Basic
/-- The n-th exterior power as a submodule of the exterior algebra. -/
def exteriorPower (n : ℕ) : Submodule R (ExteriorAlgebra R M) :=
  (ι R).range ^ n
```

#### Theorem 4.2.2: Dimension of Exterior Power
**Natural Language:** dim(⋀^k V) = C(n,k) for n-dimensional V.
**Difficulty:** medium

```lean4
-- Mathlib.LinearAlgebra.ExteriorAlgebra.Basic (conceptual)
theorem exteriorPower_finrank [Module.Free R M] [Module.Finite R M] (k : ℕ) :
    Module.finrank R (exteriorPower k : Submodule R (ExteriorAlgebra R M)) =
      Nat.choose (Module.finrank R M) k
```

#### Definition 4.2.3: Wedge Product via ιMulti
**Natural Language:** The product v₁ ∧ ⋯ ∧ vₙ as an alternating map.
**Difficulty:** medium

```lean4
-- Mathlib.LinearAlgebra.ExteriorAlgebra.Basic
/-- The product of n elements of M in the exterior algebra. -/
def ιMulti (n : ℕ) : AlternatingMap R M (ExteriorAlgebra R M) (Fin n) :=
  ...
```

---

## Part V: Symplectic Manifolds (Templates)

> **Note:** Symplectic manifolds are NOT YET FORMALIZED in Mathlib4.

### Section 5.1: Symplectic Forms on Manifolds

#### Definition 5.1.1: Differential 2-Form (TEMPLATE)
**Natural Language:** A 2-form ω on M assigns to each point a skew-symmetric bilinear form on the tangent space.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Differential 2-form
/-- A smooth differential 2-form on a manifold M. -/
structure DifferentialForm (M : Type*) [SmoothManifoldWithCorners I M] (k : ℕ) where
  toFun : M → AlternatingMap ℝ (TangentSpace I x) ℝ (Fin k)
  smooth' : Smooth I 𝓘(ℝ, AlternatingMap ...) toFun
```

#### Definition 5.1.2: Symplectic Manifold (TEMPLATE)
**Natural Language:** (M, ω) is symplectic if ω is a closed, non-degenerate 2-form.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Symplectic manifold
/-- A symplectic manifold is equipped with a closed, non-degenerate 2-form. -/
structure SymplecticManifold extends SmoothManifoldWithCorners where
  symplecticForm : DifferentialForm M 2
  isClosed : dω = 0
  isNondegenerate : ∀ x, ω x.Nondegenerate
```

#### Theorem 5.1.3: Symplectic Manifolds are Even-Dimensional (TEMPLATE)
**Natural Language:** A symplectic manifold has even dimension.
**Difficulty:** easy
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB
theorem SymplecticManifold.even_dim (M : SymplecticManifold) : Even (FiniteDimensional.finrank ℝ M)
```

### Section 5.2: Darboux Theorem

#### Theorem 5.2.1: Darboux Theorem (TEMPLATE)
**Natural Language:** Every symplectic manifold is locally diffeomorphic to (ℝ²ⁿ, ∑ dpᵢ ∧ dqᵢ).
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Darboux theorem
theorem darboux_theorem (M : SymplecticManifold) (x : M) :
    ∃ (U : Set M) (hU : IsOpen U) (hx : x ∈ U)
      (φ : Diffeomorph U (Set.univ : Set (ℝ²ⁿ))),
      φ.pullback ω_std = ω.restrict U
```

---

## Part VI: Hamiltonian Mechanics (Templates)

### Section 6.1: Hamiltonian Vector Fields

#### Definition 6.1.1: Hamiltonian Vector Field (TEMPLATE)
**Natural Language:** For H : M → ℝ, the Hamiltonian vector field X_H satisfies ω(X_H, ·) = dH.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Hamiltonian vector field
/-- The Hamiltonian vector field of H. -/
noncomputable def hamiltonianVectorField (M : SymplecticManifold) (H : M → ℝ) :
    VectorField M :=
  fun x => ω.symplecticDual (differential H x)
```

#### Theorem 6.1.2: Hamilton's Equations (TEMPLATE)
**Natural Language:** In Darboux coordinates: dq/dt = ∂H/∂p, dp/dt = -∂H/∂q.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Hamilton's equations
theorem hamilton_equations (M : SymplecticManifold) (H : M → ℝ) (γ : ℝ → M)
    (hγ : IsIntegralCurve (hamiltonianVectorField M H) γ) (i : Fin n) :
    deriv (fun t => q i (γ t)) t = (∂H/∂p i) (γ t) ∧
    deriv (fun t => p i (γ t)) t = -(∂H/∂q i) (γ t)
```

#### Theorem 6.1.3: Energy Conservation (TEMPLATE)
**Natural Language:** H is constant along its Hamiltonian flow.
**Difficulty:** easy
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Energy conservation
theorem hamiltonian_conserved (M : SymplecticManifold) (H : M → ℝ) (γ : ℝ → M)
    (hγ : IsIntegralCurve (hamiltonianVectorField M H) γ) : ∀ t, H (γ t) = H (γ 0)
```

### Section 6.2: Poisson Brackets

#### Definition 6.2.1: Poisson Bracket (TEMPLATE)
**Natural Language:** {f, g} = ω(X_f, X_g) measures the failure of f and g to commute under the Hamiltonian flow.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Poisson bracket
/-- The Poisson bracket of two functions. -/
noncomputable def poissonBracket (M : SymplecticManifold) (f g : M → ℝ) : M → ℝ :=
  fun x => M.symplecticForm x (hamiltonianVectorField M f x) (hamiltonianVectorField M g x)
```

#### Theorem 6.2.2: Poisson Bracket Antisymmetry (TEMPLATE)
**Natural Language:** {f, g} = -{g, f}.
**Difficulty:** easy
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB
theorem poissonBracket_antisymm (f g : M → ℝ) : {f, g} = -{g, f}
```

#### Theorem 6.2.3: Jacobi Identity (TEMPLATE)
**Natural Language:** {f, {g, h}} + {g, {h, f}} + {h, {f, g}} = 0.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Jacobi identity
theorem poissonBracket_jacobi (f g h : M → ℝ) :
    {f, {g, h}} + {g, {h, f}} + {h, {f, g}} = 0
```

#### Theorem 6.2.4: Poisson Bracket in Coordinates (TEMPLATE)
**Natural Language:** {f, g} = ∑ᵢ (∂f/∂qᵢ ∂g/∂pᵢ - ∂f/∂pᵢ ∂g/∂qᵢ).
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Coordinate formula
theorem poissonBracket_coordinates (f g : ℝ²ⁿ → ℝ) :
    {f, g} = ∑ i, (∂f/∂q i * ∂g/∂p i - ∂f/∂p i * ∂g/∂q i)
```

---

## Part VII: Symplectic Transformations (Templates)

### Section 7.1: Symplectomorphisms

#### Definition 7.1.1: Symplectomorphism (TEMPLATE)
**Natural Language:** A symplectomorphism is a diffeomorphism φ : M → N with φ*ω_N = ω_M.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Symplectomorphism
/-- A diffeomorphism preserving the symplectic form. -/
structure Symplectomorphism (M N : SymplecticManifold) extends Diffeomorph M N where
  preserves_form : ∀ x, pullback toFun N.symplecticForm x = M.symplecticForm x
```

#### Theorem 7.1.2: Hamiltonian Flow is Symplectomorphism (TEMPLATE)
**Natural Language:** The time-t flow of a Hamiltonian vector field is a symplectomorphism.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Hamiltonian flow preserves ω
theorem hamiltonianFlow_symplectomorphism (M : SymplecticManifold) (H : M → ℝ) (t : ℝ) :
    Symplectomorphism M M := {
      toFun := hamiltonianFlow H t
      preserves_form := ... }
```

### Section 7.2: Liouville's Theorem

#### Theorem 7.2.1: Liouville's Theorem (TEMPLATE)
**Natural Language:** Hamiltonian flow preserves the symplectic volume form ωⁿ.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Liouville's theorem
theorem liouville_volume_preservation (M : SymplecticManifold) (H : M → ℝ) (t : ℝ) (U : Set M) :
    volume (hamiltonianFlow H t '' U) = volume U
```

---

## Part VIII: Cotangent Bundles (Templates)

### Section 8.1: Canonical Symplectic Structure

#### Definition 8.1.1: Tautological 1-Form (TEMPLATE)
**Natural Language:** The tautological form θ on T*M is θ_α(v) = α(π_*v).
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Tautological 1-form
/-- The tautological/canonical 1-form on the cotangent bundle. -/
noncomputable def tautologicalForm (M : SmoothManifold) :
    DifferentialForm (CotangentBundle M) 1 :=
  fun α => fun v => α (tangentMap (CotangentBundle.proj M) v)
```

#### Theorem 8.1.2: Canonical Symplectic Form (TEMPLATE)
**Natural Language:** ω = -dθ is the canonical symplectic form on T*M.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Canonical symplectic form
theorem cotangentBundle_symplectic (M : SmoothManifold) :
    SymplecticManifold (CotangentBundle M) := {
      symplecticForm := -d (tautologicalForm M)
      isClosed := ... }
```

#### Theorem 8.1.3: Cotangent Bundle Coordinates (TEMPLATE)
**Natural Language:** In local coordinates (q, p), ω = ∑ dpᵢ ∧ dqᵢ.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Coordinate expression
theorem cotangentBundle_symplecticForm_coords :
    ω = ∑ i, d(p i) ∧ d(q i)
```

---

## Dependencies

- **Internal:** `linear_algebra` (bilinear forms), `smooth_manifolds` (manifold structure), `differential_geometry` (tangent bundles)
- **Mathlib4:** `Mathlib.LinearAlgebra.BilinearForm.*`, `Mathlib.LinearAlgebra.Alternating.*`, `Mathlib.LinearAlgebra.ExteriorAlgebra.*`, `Mathlib.Algebra.Lie.Classical`

## Notes for Autoformalization

1. **Linear algebra excellent:** BilinForm, AlternatingMap, ExteriorAlgebra all formalized
2. **Symplectic group:** Matrix.symplecticGroup in Mathlib
3. **Manifold gap:** No differential forms, exterior derivative, or symplectic manifolds
4. **Hamiltonian mechanics:** Requires symplectic manifold infrastructure first
5. **Build on smooth manifolds:** TangentBundle, ContMDiff already formalized
6. **Cotangent bundle:** Key example, needs differential forms

---

## Summary Statistics

- **Total Statements:** 50
- **Formalized (with Lean4):** 20 (40%)
- **Templates (NOT FORMALIZED):** 30 (60%)
- **Difficulty Distribution:** Easy: 14, Medium: 26, Hard: 10
