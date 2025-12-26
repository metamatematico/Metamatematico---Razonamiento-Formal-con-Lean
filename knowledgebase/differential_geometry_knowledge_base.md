# Differential Geometry Knowledge Base

**Domain**: Geometric Structures on Manifolds (Lie Theory, Exterior Algebra, Riemannian Geometry)
**Lean 4 Coverage**: GOOD for algebraic structures (Lie algebras, exterior algebra); LIMITED for Riemannian geometry
**Source**: Mathlib4 `Algebra.Lie.*`, `LinearAlgebra.ExteriorAlgebra.*`, `Geometry.Manifold.Riemannian.*`
**Last Updated**: 2025-12-19
**Related KB**: `smooth_manifolds` (foundational manifold infrastructure)

---

## Executive Summary

This knowledge base covers geometric structures on smooth manifolds in Lean 4/Mathlib. It focuses on:
- **Lie Theory**: Lie rings, Lie algebras, classical Lie algebras - WELL FORMALIZED
- **Exterior Algebra**: Wedge products, exterior powers - WELL FORMALIZED
- **Riemannian Geometry**: Metrics, geodesics, curvature - PARTIALLY FORMALIZED

For foundational manifold infrastructure (ModelWithCorners, ChartedSpace, IsManifold, TangentBundle, mfderiv), see `smooth_manifolds_knowledge_base.md`.

**Key Gaps**: Differential forms as smooth sections, Stokes' theorem, de Rham cohomology, Levi-Civita connection, curvature tensors.

---

## Content Summary

| Part | Topic | Statements | Mathlib Coverage |
|------|-------|------------|------------------|
| 1 | Lie Rings and Algebras | 12 | Complete |
| 2 | Classical Lie Algebras | 8 | Good |
| 3 | Lie Algebra Morphisms | 6 | Complete |
| 4 | Exterior Algebra | 12 | Complete |
| 5 | Exterior Powers | 6 | Good |
| 6 | Riemannian Structures | 8 | Partial |
| 7 | Geodesics | 4 | Limited |
| 8 | Important Gaps (Unformalized) | 10 | — |
| **Total** | | **66** | **~70%** |

**Measurability Score**: 70 (algebraic foundations excellent; Riemannian structures limited)

---

## Related Knowledge Bases

### Prerequisites
- **Smooth Manifolds** (`smooth_manifolds_knowledge_base.md`): Manifold infrastructure, tangent bundles, smooth maps
- **Linear Algebra** (`linear_algebra_knowledge_base.md`): Vector spaces, tensor products, exterior powers
- **Topology** (`topology_knowledge_base.md`): Topological foundations for manifolds

### Builds Upon This KB
- **Algebraic Topology** (`algebraic_topology_knowledge_base.md`): de Rham cohomology, characteristic classes
- **Complex Geometry** (`complex_geometry_knowledge_base.md`): Kähler geometry, Hermitian structures
- **Fiber Bundles** (`fiber_bundles_knowledge_base.md`): Principal bundles, connections

### Related Topics
- **Lie Theory** (`lie_theory_knowledge_base.md`): Lie groups and their geometric actions
- **Representation Theory** (`representation_theory_knowledge_base.md`): Representations of Lie groups

### Scope Clarification
This KB focuses on **geometric structures on manifolds**:
- Lie rings and Lie algebras
- Exterior algebra and differential forms
- Riemannian metrics, geodesics, curvature

For **foundational manifold infrastructure** (ChartedSpace, TangentBundle), see **Smooth Manifolds KB**.
For **algebraic aspects of Lie theory**, see **Lie Theory KB**.

---

## Part 1: Lie Rings and Algebras

### 1.1 LieRing

**Concept**: Additive group with antisymmetric bracket satisfying Jacobi identity.

**NL Statement**: "A Lie ring is an additive commutative group L with a bracket operation ⁅·,·⁆ satisfying: (1) additivity in each argument, (2) skew-symmetry ⁅x, x⁆ = 0, and (3) the Jacobi identity ⁅x, ⁅y, z⁆⁆ + ⁅y, ⁅z, x⁆⁆ + ⁅z, ⁅x, y⁆⁆ = 0."

**Lean 4 Definition**:
```lean
class LieRing (L : Type u_1) extends AddCommGroup L, Bracket L L where
  add_lie : ∀ (x y z : L), ⁅x + y, z⁆ = ⁅x, z⁆ + ⁅y, z⁆
  lie_add : ∀ (x y z : L), ⁅x, y + z⁆ = ⁅x, y⁆ + ⁅x, z⁆
  lie_self : ∀ (x : L), ⁅x, x⁆ = 0
  leibniz_lie : ∀ (x y z : L), ⁅x, ⁅y, z⁆⁆ = ⁅⁅x, y⁆, z⁆ + ⁅y, ⁅x, z⁆⁆
```

**Imports**: `Mathlib.Algebra.Lie.Basic`
**Difficulty**: medium

---

### 1.2 Lie Bracket Antisymmetry

**NL Statement**: "In any Lie ring, the bracket is antisymmetric: ⁅x, y⁆ = -⁅y, x⁆."

**Lean 4 Theorem**:
```lean
theorem lie_skew (x y : L) : ⁅x, y⁆ = -⁅y, x⁆
```

**Imports**: `Mathlib.Algebra.Lie.Basic`
**Difficulty**: easy

---

### 1.3 LieAlgebra

**Concept**: Lie ring over a commutative ring with compatible scalar action.

**NL Statement**: "A Lie algebra L over commutative ring R is a Lie ring with R-module structure such that the bracket is R-linear in each argument: ⁅r • x, y⁆ = r • ⁅x, y⁆ and ⁅x, r • y⁆ = r • ⁅x, y⁆."

**Lean 4 Definition**:
```lean
class LieAlgebra (R : Type u) (L : Type v) [CommRing R] [LieRing L] extends Module R L where
  lie_smul : ∀ (t : R) (x y : L), ⁅x, t • y⁆ = t • ⁅x, y⁆
```

**Imports**: `Mathlib.Algebra.Lie.Basic`
**Difficulty**: medium

---

### 1.4 Abelian Lie Algebra

**NL Statement**: "A Lie algebra is abelian if all brackets are zero: ⁅x, y⁆ = 0 for all x, y."

**Lean 4 Definition**:
```lean
class IsLieAbelian (L : Type v) [Bracket L L] [Zero L] : Prop where
  trivial : ∀ (x y : L), ⁅x, y⁆ = 0
```

**Imports**: `Mathlib.Algebra.Lie.Basic`
**Difficulty**: easy

---

### 1.5 Lie Subalgebra

**NL Statement**: "A Lie subalgebra is an R-submodule that is closed under the bracket operation."

**Lean 4 Definition**:
```lean
structure LieSubalgebra (R : Type u) (L : Type v) [CommRing R] [LieRing L] [LieAlgebra R L]
    extends Submodule R L where
  lie_mem' : ∀ {x y : L}, x ∈ carrier → y ∈ carrier → ⁅x, y⁆ ∈ carrier
```

**Imports**: `Mathlib.Algebra.Lie.Subalgebra`
**Difficulty**: medium

---

### 1.6 Lie Ideal

**NL Statement**: "A Lie ideal is a subalgebra I such that ⁅L, I⁆ ⊆ I, meaning ⁅x, y⁆ ∈ I for all x ∈ L and y ∈ I."

**Lean 4 Definition**:
```lean
structure LieIdeal (R : Type u) (L : Type v) [CommRing R] [LieRing L] [LieAlgebra R L]
    extends LieSubalgebra R L where
  lie_mem : ∀ (x : L) {y : L}, y ∈ carrier → ⁅x, y⁆ ∈ carrier
```

**Imports**: `Mathlib.Algebra.Lie.Ideal`
**Difficulty**: medium

---

### 1.7 Center of a Lie Algebra

**NL Statement**: "The center of a Lie algebra L is the set of elements that bracket trivially with all of L: {x ∈ L | ⁅x, y⁆ = 0 for all y}."

**Lean 4 Definition**:
```lean
def LieAlgebra.center (R : Type u) (L : Type v) [CommRing R] [LieRing L] [LieAlgebra R L] :
    LieIdeal R L := ...
```

**Imports**: `Mathlib.Algebra.Lie.Ideal`
**Difficulty**: easy

---

### 1.8 Derived Series

**NL Statement**: "The derived series of a Lie algebra is L⁽⁰⁾ = L, L⁽ⁿ⁺¹⁾ = ⁅L⁽ⁿ⁾, L⁽ⁿ⁾⁆. A Lie algebra is solvable if some term of its derived series is zero."

**Lean 4 Definition**:
```lean
def LieAlgebra.derivedSeries (R : Type u) (L : Type v) [CommRing R] [LieRing L] [LieAlgebra R L] :
    ℕ → LieIdeal R L
  | 0 => ⊤
  | n + 1 => ⁅derivedSeries R L n, derivedSeries R L n⁆
```

**Imports**: `Mathlib.Algebra.Lie.Solvable`
**Difficulty**: hard

---

### 1.9 Lower Central Series

**NL Statement**: "The lower central series is L⁽⁰⁾ = L, L⁽ⁿ⁺¹⁾ = ⁅L, L⁽ⁿ⁾⁆. A Lie algebra is nilpotent if some term is zero."

**Lean 4 Definition**:
```lean
def LieAlgebra.lowerCentralSeries (R : Type u) (L : Type v) [CommRing R] [LieRing L] [LieAlgebra R L] :
    ℕ → LieIdeal R L
  | 0 => ⊤
  | n + 1 => ⁅⊤, lowerCentralSeries R L n⁆
```

**Imports**: `Mathlib.Algebra.Lie.Nilpotent`
**Difficulty**: hard

---

### 1.10 Solvability

**NL Statement**: "A Lie algebra L is solvable if its derived series reaches zero: L⁽ᵏ⁾ = 0 for some k."

**Lean 4 Definition**:
```lean
class LieAlgebra.IsSolvable (R : Type u) (L : Type v) [CommRing R] [LieRing L] [LieAlgebra R L] :
    Prop where
  solvable : ∃ k, LieAlgebra.derivedSeries R L k = ⊥
```

**Imports**: `Mathlib.Algebra.Lie.Solvable`
**Difficulty**: medium

---

### 1.11 Nilpotency

**NL Statement**: "A Lie algebra L is nilpotent if its lower central series reaches zero: L⁽ᵏ⁾ = 0 for some k."

**Lean 4 Definition**:
```lean
class LieAlgebra.IsNilpotent (R : Type u) (L : Type v) [CommRing R] [LieRing L] [LieAlgebra R L] :
    Prop where
  nilpotent : ∃ k, LieAlgebra.lowerCentralSeries R L k = ⊥
```

**Imports**: `Mathlib.Algebra.Lie.Nilpotent`
**Difficulty**: medium

---

### 1.12 Nilpotent Implies Solvable

**NL Statement**: "Every nilpotent Lie algebra is solvable."

**Lean 4 Theorem**:
```lean
instance LieAlgebra.isSolvableOfIsNilpotent [LieAlgebra.IsNilpotent R L] :
    LieAlgebra.IsSolvable R L
```

**Imports**: `Mathlib.Algebra.Lie.Nilpotent`
**Difficulty**: medium

---

## Part 2: Classical Lie Algebras

### 2.1 Matrix Lie Algebra

**NL Statement**: "The set of n×n matrices over a Lie ring forms a Lie algebra with bracket [A, B] = AB - BA (the commutator)."

**Lean 4 Instance**:
```lean
instance Matrix.instLieRing : LieRing (Matrix n n R)
instance Matrix.instLieAlgebra : LieAlgebra R (Matrix n n R)
```

**Imports**: `Mathlib.Algebra.Lie.OfAssociative`
**Difficulty**: medium

---

### 2.2 General Linear Lie Algebra gl(n)

**NL Statement**: "The general linear Lie algebra gl(n, R) is the Lie algebra of all n×n matrices with the commutator bracket."

**Lean 4**: Uses `Matrix n n R` with `LieAlgebra R (Matrix n n R)` instance.

**Imports**: `Mathlib.Algebra.Lie.Classical`
**Difficulty**: easy

---

### 2.3 Special Linear Lie Algebra sl(n)

**NL Statement**: "The special linear Lie algebra sl(n, R) consists of traceless n×n matrices."

**Lean 4 Definition**:
```lean
def specialLinearLieAlgebra (n : ℕ) (R : Type u) [CommRing R] :
    LieSubalgebra R (Matrix (Fin n) (Fin n) R) :=
  { carrier := { A | Matrix.trace A = 0 }
    ... }
```

**Imports**: `Mathlib.Algebra.Lie.Classical`
**Difficulty**: medium

---

### 2.4 Symplectic Lie Algebra sp(n)

**NL Statement**: "The symplectic Lie algebra sp(n, R) consists of 2n×2n matrices A satisfying Aᵀ J + J A = 0 where J is the standard symplectic form."

**Lean 4 Definition**:
```lean
def symplecticLieAlgebra (n : ℕ) (R : Type u) [CommRing R] :
    LieSubalgebra R (Matrix (Fin (2 * n)) (Fin (2 * n)) R)
```

**Imports**: `Mathlib.Algebra.Lie.Classical`
**Difficulty**: medium

---

### 2.5 Orthogonal Lie Algebra so(n)

**NL Statement**: "The orthogonal Lie algebra so(n, R) consists of skew-symmetric n×n matrices: Aᵀ = -A."

**Lean 4 Definition**:
```lean
def orthogonalLieAlgebra (n : ℕ) (R : Type u) [CommRing R] :
    LieSubalgebra R (Matrix (Fin n) (Fin n) R) :=
  { carrier := { A | Aᵀ = -A }
    ... }
```

**Imports**: `Mathlib.Algebra.Lie.Classical`
**Difficulty**: medium

---

### 2.6 Endomorphism Lie Algebra

**NL Statement**: "The endomorphism ring End(M) of an R-module M carries a Lie algebra structure with bracket [f, g] = f ∘ g - g ∘ f."

**Lean 4 Instance**:
```lean
instance Module.End.instLieAlgebra : LieAlgebra R (Module.End R M)
```

**Imports**: `Mathlib.Algebra.Lie.OfAssociative`
**Difficulty**: medium

---

### 2.7 Adjoint Representation

**NL Statement**: "For any Lie algebra L, the adjoint map ad: L → End(L) defined by ad(x)(y) = ⁅x, y⁆ is a Lie algebra homomorphism."

**Lean 4 Definition**:
```lean
def LieAlgebra.ad : L →ₗ⁅R⁆ Module.End R L where
  toFun x := { toFun := fun y => ⁅x, y⁆, ... }
  map_lie' := by simp [leibniz_lie]
```

**Imports**: `Mathlib.Algebra.Lie.Basic`
**Difficulty**: medium

---

### 2.8 Kernel of Adjoint is Center

**NL Statement**: "The kernel of the adjoint representation equals the center of the Lie algebra."

**Lean 4 Theorem**:
```lean
theorem LieAlgebra.ker_ad_eq_center :
    (LieAlgebra.ad R L).ker = LieAlgebra.center R L
```

**Imports**: `Mathlib.Algebra.Lie.Basic`
**Difficulty**: medium

---

## Part 3: Lie Algebra Morphisms

### 3.1 Lie Algebra Homomorphism

**NL Statement**: "A Lie algebra homomorphism f: L₁ → L₂ is an R-linear map that preserves brackets: f(⁅x, y⁆) = ⁅f(x), f(y)⁆."

**Lean 4 Definition**:
```lean
structure LieHom (R : Type u) (L : Type v) (L' : Type w)
    [CommRing R] [LieRing L] [LieAlgebra R L] [LieRing L'] [LieAlgebra R L']
    extends L →ₗ[R] L' where
  map_lie' : ∀ {x y : L}, toLinearMap ⁅x, y⁆ = ⁅toLinearMap x, toLinearMap y⁆
```

**Notation**: `L₁ →ₗ⁅R⁆ L₂`

**Imports**: `Mathlib.Algebra.Lie.Basic`
**Difficulty**: medium

---

### 3.2 Lie Algebra Equivalence

**NL Statement**: "A Lie algebra equivalence is a bijective homomorphism whose inverse is also a homomorphism."

**Lean 4 Definition**:
```lean
structure LieEquiv (R : Type u) (L : Type v) (L' : Type w)
    [CommRing R] [LieRing L] [LieRing L'] [LieAlgebra R L] [LieAlgebra R L']
    extends L ≃ₗ[R] L' where
  map_lie' : ∀ x y : L, toLinearEquiv ⁅x, y⁆ = ⁅toLinearEquiv x, toLinearEquiv y⁆
```

**Notation**: `L₁ ≃ₗ⁅R⁆ L₂`

**Imports**: `Mathlib.Algebra.Lie.Basic`
**Difficulty**: medium

---

### 3.3 Kernel of Lie Homomorphism

**NL Statement**: "The kernel of a Lie homomorphism f: L → L' is a Lie ideal of L."

**Lean 4 Definition**:
```lean
def LieHom.ker (f : L →ₗ⁅R⁆ L') : LieIdeal R L := ...
```

**Imports**: `Mathlib.Algebra.Lie.Ideal`
**Difficulty**: medium

---

### 3.4 Image of Lie Homomorphism

**NL Statement**: "The image of a Lie homomorphism f: L → L' is a Lie subalgebra of L'."

**Lean 4 Definition**:
```lean
def LieHom.range (f : L →ₗ⁅R⁆ L') : LieSubalgebra R L' := ...
```

**Imports**: `Mathlib.Algebra.Lie.Subalgebra`
**Difficulty**: medium

---

### 3.5 First Isomorphism Theorem for Lie Algebras

**NL Statement**: "For a Lie homomorphism f: L → L', the quotient L / ker(f) is isomorphic to the image of f."

**Lean 4 Theorem**:
```lean
def LieIdeal.quotientKerEquivRange (f : L →ₗ⁅R⁆ L') :
    (L ⧸ f.ker) ≃ₗ⁅R⁆ f.range
```

**Imports**: `Mathlib.Algebra.Lie.Quotient`
**Difficulty**: hard

---

### 3.6 Quotient Lie Algebra

**NL Statement**: "For a Lie ideal I ⊆ L, the quotient L/I carries a natural Lie algebra structure."

**Lean 4 Instance**:
```lean
instance LieIdeal.Quotient.instLieAlgebra (I : LieIdeal R L) :
    LieAlgebra R (L ⧸ I)
```

**Imports**: `Mathlib.Algebra.Lie.Quotient`
**Difficulty**: hard

---

## Part 4: Exterior Algebra

### 4.1 ExteriorAlgebra

**Concept**: Algebra of antisymmetric tensors, quotient of tensor algebra by m ⊗ m relations.

**NL Statement**: "The exterior algebra ⋀M over ring R is the quotient of the tensor algebra by the ideal generated by elements m ⊗ m, implemented in Mathlib as a Clifford algebra with zero quadratic form."

**Lean 4 Definition**:
```lean
abbrev ExteriorAlgebra (R : Type u1) [CommRing R]
    (M : Type u2) [AddCommGroup M] [Module R M] :
    Type (max u2 u1) :=
  CliffordAlgebra (0 : QuadraticForm R M)
```

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`
**Difficulty**: medium

---

### 4.2 Canonical Embedding ι

**NL Statement**: "The canonical linear map ι : M → ⋀M embeds the module into its exterior algebra."

**Lean 4 Definition**:
```lean
abbrev ExteriorAlgebra.ι (R : Type u1) [CommRing R]
    {M : Type u2} [AddCommGroup M] [Module R M] :
    M →ₗ[R] ExteriorAlgebra R M :=
  CliffordAlgebra.ι 0
```

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`
**Difficulty**: easy

---

### 4.3 Generators Square to Zero

**NL Statement**: "In the exterior algebra, every generator squares to zero: (ι m)² = 0."

**Lean 4 Theorem**:
```lean
theorem ExteriorAlgebra.ι_sq_zero {m : M} :
    (ι R) m * (ι R) m = 0
```

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`
**Difficulty**: easy

---

### 4.4 Anticommutativity

**NL Statement**: "Generators of the exterior algebra anticommute: ι(x) ∧ ι(y) = -ι(y) ∧ ι(x), equivalently ι(x) ∧ ι(y) + ι(y) ∧ ι(x) = 0."

**Lean 4 Theorem**:
```lean
theorem ExteriorAlgebra.ι_add_mul_swap {x y : M} :
    (ι R) x * (ι R) y + (ι R) y * (ι R) x = 0
```

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`
**Difficulty**: easy

---

### 4.5 Universal Property

**NL Statement**: "The exterior algebra satisfies a universal property: any linear map f: M → A to an R-algebra A satisfying f(m)² = 0 extends uniquely to an algebra homomorphism ⋀M → A."

**Lean 4 Definition**:
```lean
def ExteriorAlgebra.lift {A : Type u3} [Semiring A] [Algebra R A]
    (f : M →ₗ[R] A) (hf : ∀ m, f m * f m = 0) :
    ExteriorAlgebra R M →ₐ[R] A
```

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`
**Difficulty**: medium

---

### 4.6 Graded Structure

**NL Statement**: "The exterior algebra has a natural ℤ-grading with M in degree 1, R in degree 0, and ⋀ⁿM in degree n."

**Lean 4 Instance**:
```lean
instance ExteriorAlgebra.instGradedAlgebra :
    GradedAlgebra (ExteriorAlgebra.GradedPiece R M)
```

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Grading`
**Difficulty**: medium

---

### 4.7 Exterior Algebra of Free Module

**NL Statement**: "For a free module with basis, the exterior algebra has dimension 2ⁿ where n is the rank of the module."

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`
**Difficulty**: medium

---

### 4.8 Alternating Map Correspondence

**NL Statement**: "k-linear alternating maps M^k → N correspond bijectively to linear maps ⋀ᵏM → N."

**Lean 4 Definition**:
```lean
def AlternatingMap.curry :
    (AlternatingMap R M N (Fin k)) ≃ₗ[R] (⋀[R]^k M →ₗ[R] N)
```

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`
**Difficulty**: hard

---

### 4.9 Wedge Product

**NL Statement**: "The wedge product ∧ : ⋀ᵖM × ⋀ᵍM → ⋀ᵖ⁺ᵍM is the algebra multiplication, satisfying graded commutativity: α ∧ β = (-1)^{pq} β ∧ α."

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`
**Difficulty**: medium

---

### 4.10 Determinant via Exterior Algebra

**NL Statement**: "The determinant of a linear map f: M → M can be computed via its action on the top exterior power ⋀ⁿM."

**Lean 4 Theorem**:
```lean
theorem LinearMap.det_eq_exteriorPower_top_action
    [DecidableEq (Fin n)] {f : (Fin n → R) →ₗ[R] (Fin n → R)} :
    LinearMap.det f = ...
```

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`
**Difficulty**: hard

---

### 4.11 Exterior Algebra Functor

**NL Statement**: "The exterior algebra construction is functorial: a linear map f: M → N induces an algebra homomorphism ⋀f: ⋀M → ⋀N."

**Lean 4 Definition**:
```lean
def ExteriorAlgebra.map (f : M →ₗ[R] N) :
    ExteriorAlgebra R M →ₐ[R] ExteriorAlgebra R N
```

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`
**Difficulty**: medium

---

### 4.12 Exterior Algebra Over Field

**NL Statement**: "For a finite-dimensional vector space V over field K with dim(V) = n, we have dim(⋀ᵏV) = C(n,k) and dim(⋀V) = 2ⁿ."

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.OfFree`
**Difficulty**: medium

---

## Part 5: Exterior Powers

### 5.1 exteriorPower Definition

**Concept**: n-th exterior power as submodule of exterior algebra.

**NL Statement**: "The n-th exterior power ⋀ⁿM is the submodule of the exterior algebra spanned by products of exactly n elements from M."

**Lean 4 Definition**:
```lean
abbrev exteriorPower (R : Type u1) [CommRing R] (n : ℕ)
    (M : Type u2) [AddCommGroup M] [Module R M] :
    Submodule R (ExteriorAlgebra R M) :=
  LinearMap.range (ι R) ^ n
```

**Notation**: `⋀[R]^n M`

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`
**Difficulty**: medium

---

### 5.2 Zeroth Power

**NL Statement**: "The zeroth exterior power ⋀⁰M is isomorphic to R."

**Lean 4 Theorem**:
```lean
theorem exteriorPower_zero_eq_span_one :
    ⋀[R]^0 M = Submodule.span R {1}
```

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`
**Difficulty**: easy

---

### 5.3 First Power

**NL Statement**: "The first exterior power ⋀¹M is isomorphic to M itself."

**Lean 4 Theorem**:
```lean
def ExteriorAlgebra.ιOne : M ≃ₗ[R] ⋀[R]^1 M
```

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`
**Difficulty**: easy

---

### 5.4 Top Exterior Power

**NL Statement**: "For a free module of rank n, the top exterior power ⋀ⁿM is one-dimensional."

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.OfFree`
**Difficulty**: medium

---

### 5.5 Vanishing Above Rank

**NL Statement**: "For a module of rank n, the k-th exterior power ⋀ᵏM = 0 for all k > n."

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.OfFree`
**Difficulty**: medium

---

### 5.6 Exterior Power of Direct Sum

**NL Statement**: "The exterior power of a direct sum decomposes: ⋀ⁿ(M ⊕ N) ≅ ⊕_{i+j=n} ⋀ⁱM ⊗ ⋀ʲN."

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`
**Difficulty**: hard

---

## Part 6: Riemannian Structures

### 6.1 Inner Product Space

**Concept**: Vector space with positive-definite inner product.

**NL Statement**: "An inner product space is a real or complex vector space equipped with a sesquilinear form ⟪·, ·⟫ that is positive definite."

**Lean 4 Class**:
```lean
class InnerProductSpace (𝕜 : Type*) (E : Type*) [RCLike 𝕜] [NormedAddCommGroup E]
    extends NormedSpace 𝕜 E where
  inner : E → E → 𝕜
  norm_sq_eq_inner : ∀ x : E, ‖x‖ ^ 2 = re (inner x x)
  conj_symm : ∀ x y, inner y x = conj (inner x y)
  add_left : ∀ x y z, inner (x + y) z = inner x z + inner y z
  smul_left : ∀ x y r, inner (r • x) y = conj r * inner x y
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: medium

---

### 6.2 Hilbert Space

**NL Statement**: "A Hilbert space is a complete inner product space."

**Lean 4 Instance**:
```lean
-- A complete inner product space, expressed via CompleteSpace
class (InnerProductSpace 𝕜 E) [CompleteSpace E]
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: medium

---

### 6.3 Orthonormal Basis

**NL Statement**: "An orthonormal basis of an inner product space is a basis {eᵢ} satisfying ⟪eᵢ, eⱼ⟫ = δᵢⱼ."

**Lean 4 Definition**:
```lean
structure OrthonormalBasis (ι : Type*) (𝕜 : Type*) (E : Type*)
    [RCLike 𝕜] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E] where
  repr : E ≃ₗᵢ[𝕜] EuclideanSpace 𝕜 ι
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: medium

---

### 6.4 Riesz Representation

**NL Statement**: "In a Hilbert space, every continuous linear functional φ: E → 𝕜 has a unique representer v such that φ(x) = ⟪v, x⟫."

**Lean 4 Theorem**:
```lean
theorem InnerProductSpace.toDualEquiv_apply (x y : E) :
    toDualEquiv 𝕜 E x y = inner x y
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Dual`
**Difficulty**: hard

---

### 6.5 Projection Theorem

**NL Statement**: "For a closed convex subset C of a Hilbert space and any point x, there exists a unique closest point in C to x."

**Lean 4 Theorem**:
```lean
theorem exists_norm_eq_iInf_of_complete_convex
    {K : Set E} (hK : IsComplete K) (hK' : Convex ℝ K) (hne : K.Nonempty) (x : E) :
    ∃ y ∈ K, ‖x - y‖ = ⨅ z : K, ‖x - z‖
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Projection`
**Difficulty**: hard

---

### 6.6 Smooth Fiber Bundle

**NL Statement**: "A smooth fiber bundle is a fiber bundle where the total space, base, and fibers are smooth manifolds and the projection is smooth."

**Lean 4**: Smooth fiber bundles are constructed via `FiberBundle` with smooth structure.

**Imports**: `Mathlib.Geometry.Manifold.FiberBundle.Basic`
**Difficulty**: hard

---

### 6.7 Connection on Bundle (LIMITED)

**NL Statement**: "A connection on a vector bundle E → M specifies how to parallel transport vectors along paths."

**Status**: Connections have LIMITED formalization in Mathlib. The infrastructure for parallel transport and covariant derivatives is not fully developed.

**Difficulty**: very hard

---

### 6.8 Riemannian Metric (LIMITED)

**NL Statement**: "A Riemannian metric on a smooth manifold M is a smooth assignment of inner products to each tangent space TₓM."

**Status**: LIMITED. Mathlib has inner product spaces but integration with manifold tangent bundles for general Riemannian metrics is partial.

**Difficulty**: very hard

---

## Part 7: Geodesics

### 7.1 Geodesic Definition (LIMITED)

**NL Statement**: "A geodesic on a Riemannian manifold is a curve γ(t) that locally minimizes arc length, equivalently ∇_γ' γ' = 0."

**Status**: LIMITED. Mathlib does not have general geodesic formalization. Specific geodesics (e.g., great circles on spheres) may be proved ad hoc.

**Difficulty**: very hard

---

### 7.2 Geodesic Completeness

**NL Statement**: "A Riemannian manifold is geodesically complete if every geodesic can be extended indefinitely."

**Status**: NOT FORMALIZED

**Difficulty**: very hard

---

### 7.3 Hopf-Rinow Theorem

**NL Statement**: "For a connected Riemannian manifold: metric completeness ⟺ geodesic completeness ⟺ closed bounded sets are compact."

**Status**: NOT FORMALIZED

**Difficulty**: very hard

---

### 7.4 Exponential Map

**NL Statement**: "The exponential map exp_p : T_p M → M sends v ∈ T_p M to γ_v(1), where γ_v is the geodesic with γ(0) = p, γ'(0) = v."

**Status**: NOT FORMALIZED (depends on geodesics)

**Difficulty**: very hard

---

## Part 8: Important Gaps (Unformalized)

### 8.1 Generalized Stokes' Theorem (CRITICAL BRIDGE THEOREM)

**NL Statement**: "For a smooth n-dimensional manifold M with boundary ∂M and a smooth (n-1)-form ω with compact support: ∫_M dω = ∫_{∂M} ω"

**Mathematical Significance**: Unifies all fundamental theorems of calculus:
- n=1: Fundamental Theorem of Calculus
- n=2: Green's Theorem
- n=3 (curl): Classical Stokes' Theorem
- n=3 (div): Divergence Theorem (Gauss)

**Status**: NOT FORMALIZED - Requires differential forms as smooth sections and integration on manifolds.

**Difficulty**: very hard

---

### 8.2 Classical Stokes' Theorem (3D)

**NL Statement**: "For a smooth oriented surface S with boundary curve ∂S and vector field F: ∮_{∂S} F·dr = ∬_S (∇×F)·dS"

**Status**: NOT FORMALIZED

**Difficulty**: very hard

---

### 8.3 Divergence Theorem (Gauss)

**NL Statement**: "For a compact region V with smooth boundary S: ∬_S F·n dS = ∭_V (∇·F) dV"

**Status**: NOT FORMALIZED

**Difficulty**: very hard

---

### 8.4 de Rham Cohomology

**NL Statement**: "The de Rham cohomology groups H^k_dR(M) = ker(d) / im(d) measure closed forms modulo exact forms."

**Status**: NOT FORMALIZED - Requires exterior derivative on differential forms.

**Difficulty**: very hard

---

### 8.5 Riemann Curvature Tensor

**NL Statement**: "The Riemann curvature tensor R(X,Y)Z = ∇_X ∇_Y Z - ∇_Y ∇_X Z - ∇_{[X,Y]} Z measures failure of parallel transport to commute."

**Status**: LIMITED - Basic structures exist but full curvature tensor formalization incomplete.

**Difficulty**: very hard

---

### 8.6 Levi-Civita Connection

**NL Statement**: "On a Riemannian manifold, there is a unique torsion-free metric-compatible connection called the Levi-Civita connection."

**Status**: NOT FORMALIZED

**Difficulty**: very hard

---

### 8.7 Gauss-Bonnet Theorem

**NL Statement**: "For a compact oriented 2-manifold M without boundary: ∫_M K dA = 2π χ(M), relating total Gaussian curvature to Euler characteristic."

**Status**: NOT FORMALIZED

**Difficulty**: very hard

---

### 8.8 Poincaré Duality

**NL Statement**: "For a compact oriented n-manifold M: H^k(M; R) ≅ H_{n-k}(M; R)."

**Status**: NOT FORMALIZED (requires (co)homology theories)

**Difficulty**: very hard

---

### 8.9 Differential Forms

**NL Statement**: "A differential k-form on M is a smooth section of ⋀ᵏ T*M, the k-th exterior power of the cotangent bundle."

**Status**: PARTIAL - Exterior algebra formalized, but smooth sections of cotangent bundle not complete.

**Difficulty**: hard

---

### 8.10 Exterior Derivative

**NL Statement**: "The exterior derivative d: Ωᵏ(M) → Ωᵏ⁺¹(M) satisfies d² = 0 and the Leibniz rule d(α ∧ β) = dα ∧ β + (-1)ᵏ α ∧ dβ."

**Status**: NOT FORMALIZED as operator on manifold differential forms.

**Difficulty**: hard

---

## Standard Setup

**Lean 4 Imports**:
```lean
import Mathlib.Algebra.Lie.Basic
import Mathlib.Algebra.Lie.Classical
import Mathlib.Algebra.Lie.Subalgebra
import Mathlib.Algebra.Lie.Ideal
import Mathlib.Algebra.Lie.Quotient
import Mathlib.Algebra.Lie.Solvable
import Mathlib.Algebra.Lie.Nilpotent
import Mathlib.LinearAlgebra.ExteriorAlgebra.Basic
import Mathlib.LinearAlgebra.ExteriorAlgebra.Grading
import Mathlib.Analysis.InnerProductSpace.Basic
import Mathlib.Analysis.InnerProductSpace.Dual
import Mathlib.Analysis.InnerProductSpace.Projection
import Mathlib.Geometry.Manifold.FiberBundle.Basic

variable {R : Type*} [CommRing R]
variable {L : Type*} [LieRing L] [LieAlgebra R L]
variable {M : Type*} [AddCommGroup M] [Module R M]
```

---

## Notation Reference

| Math Notation | Lean 4 Notation | Description |
|---------------|-----------------|-------------|
| ⁅x, y⁆ | `Bracket.bracket x y` | Lie bracket |
| L →ₗ⁅R⁆ L' | `LieHom R L L'` | Lie algebra homomorphism |
| L ≃ₗ⁅R⁆ L' | `LieEquiv R L L'` | Lie algebra equivalence |
| L ⧸ I | `L ⧸ I` | Quotient by Lie ideal |
| ⋀M | `ExteriorAlgebra R M` | Exterior algebra |
| ⋀ⁿM | `exteriorPower R n M` | n-th exterior power |
| ⟪x, y⟫ | `inner x y` | Inner product |
| gl(n) | `Matrix n n R` with Lie structure | General linear Lie algebra |
| sl(n) | `specialLinearLieAlgebra n R` | Special linear Lie algebra |
| so(n) | `orthogonalLieAlgebra n R` | Orthogonal Lie algebra |
| sp(n) | `symplecticLieAlgebra n R` | Symplectic Lie algebra |

---

## Sources

- [Mathlib.Algebra.Lie.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Lie/Basic.html)
- [Mathlib.Algebra.Lie.Classical](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Lie/Classical.html)
- [Mathlib.Algebra.Lie.Subalgebra](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Lie/Subalgebra.html)
- [Mathlib.Algebra.Lie.Ideal](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Lie/Ideal.html)
- [Mathlib.Algebra.Lie.Quotient](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Lie/Quotient.html)
- [Mathlib.LinearAlgebra.ExteriorAlgebra.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/LinearAlgebra/ExteriorAlgebra/Basic.html)
- [Mathlib.Analysis.InnerProductSpace.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/InnerProductSpace/Basic.html)
