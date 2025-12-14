# Differential Geometry Knowledge Base

**Domain**: Smooth Manifolds & Differential Geometry
**Lean 4 Coverage**: GOOD (manifolds, tangent bundles, Lie groups complete; Riemannian partial)
**Source**: Mathlib4 `Geometry.Manifold.*` and `Algebra.Lie.*` modules
**Last Updated**: 2025-12-14

---

## Overview

This knowledge base covers differential geometry formalization in Lean 4/Mathlib using the "manifolds with corners" framework. Coverage includes smooth manifolds, tangent bundles, manifold derivatives, vector fields, Lie groups/algebras, integral curves, and basic exterior algebra.

**Key Gap**: Differential forms as smooth sections incomplete, Riemannian curvature tensors limited, Stokes' theorem not formalized, de Rham cohomology missing.

---

## 1. SMOOTH MANIFOLDS

### 1.1 ModelWithCorners

**Concept**: Local model for manifolds, embedding topological space H into normed vector space E.

**NL Statement**: "A model with corners is a structure embedding a topological space H into a normed vector space E, capturing the local model for manifolds possibly with boundary or corners."

**Lean 4 Definition**:
```lean
structure ModelWithCorners (𝕜 : Type u₁) [NontriviallyNormedField 𝕜]
    (E : Type u₂) [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    (H : Type u₃) [TopologicalSpace H]
    extends PartialEquiv H E
```

**Key Properties**:
- Continuous in both directions
- Convex range (for ℝ-like fields)
- Nonempty interior

**Imports**: `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Difficulty**: medium

---

### 1.2 modelWithCornersSelf

**Concept**: Trivial model where vector space embeds into itself.

**NL Statement**: "The identity model where a vector space E embeds into itself via the identity map, used for manifolds without boundary."

**Lean 4 Definition**:
```lean
def modelWithCornersSelf (𝕜 : Type u₁) [NontriviallyNormedField 𝕜]
    (E : Type u₂) [NormedAddCommGroup E] [NormedSpace 𝕜 E] :
    ModelWithCorners 𝕜 E E
```

**Imports**: `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Difficulty**: easy

---

### 1.3 PartialEquiv (Charts Foundation)

**Concept**: Local equivalences between subsets, foundation for charts.

**NL Statement**: "A partial equivalence consists of a function toFun : α → β with partial inverse invFun, defined on source ⊆ α and target ⊆ β, with left and right inverse properties on their respective domains."

**Lean 4 Definition**:
```lean
structure PartialEquiv (α : Type u_5) (β : Type u_6) : Type (max u_5 u_6) where
  toFun : α → β
  invFun : β → α
  source : Set α
  target : Set β
  map_source' : MapsTo toFun source target
  map_target' : MapsTo invFun target source
  left_inv' : ∀ x ∈ source, invFun (toFun x) = x
  right_inv' : ∀ x ∈ target, toFun (invFun x) = x
```

**Imports**: `Mathlib.Logic.Equiv.PartialEquiv`

**Difficulty**: medium

---

### 1.4 ChartedSpace

**Concept**: Type equipped with atlas of charts.

**NL Statement**: "A charted space is a type equipped with an atlas of charts (local homeomorphisms to a model space H). If changes of charts are smooth, the space becomes a smooth manifold."

**Imports**: `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Difficulty**: medium

---

### 1.5 contDiffGroupoid

**Concept**: Groupoid of C^n-smooth transformations.

**NL Statement**: "The groupoid of C^n-smooth transformations for manifold coordinate changes, where n can be finite, ∞ (smooth), or ω (analytic)."

**Lean 4 Definition**:
```lean
def contDiffGroupoid (n : WithTop ℕ∞)
    {𝕜 : Type u₁} [NontriviallyNormedField 𝕜]
    {E : Type u₂} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type u₃} [TopologicalSpace H]
    (I : ModelWithCorners 𝕜 E H) :
    StructureGroupoid H
```

**Imports**: `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Difficulty**: hard

---

### 1.6 IsManifold

**Concept**: Type class for C^n manifolds.

**NL Statement**: "A charted space M is a C^n manifold with respect to model I if all chart transitions are C^n smooth."

**Lean 4 Definition**:
```lean
class IsManifold
    {𝕜 : Type u₁} [NontriviallyNormedField 𝕜]
    {E : Type u₂} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type u₃} [TopologicalSpace H]
    (I : ModelWithCorners 𝕜 E H)
    (n : WithTop ℕ∞)
    (M : Type u₄) [TopologicalSpace M] [ChartedSpace H M]
    extends HasGroupoid M (contDiffGroupoid n I)
```

**Common Instantiations**:
- `IsManifold I ∞ M` — smooth manifold
- `IsManifold I 0 M` — topological manifold
- `IsManifold I ω M` — analytic manifold

**Imports**: `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Difficulty**: hard

---

## 2. TANGENT SPACES AND BUNDLES

### 2.1 TangentSpace

**Concept**: Tangent space at a point, type synonym for model space.

**NL Statement**: "The tangent space at point x on manifold M is defined as a type synonym for the model vector space E, enabling operations like derivatives between tangent spaces."

**Lean 4 Definition**:
```lean
def TangentSpace
    {𝕜 : Type u₁} [NontriviallyNormedField 𝕜]
    {E : Type u} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type u₂} [TopologicalSpace H]
    (I : ModelWithCorners 𝕜 E H)
    {M : Type u₃} [TopologicalSpace M] [ChartedSpace H M]
    (x : M) : Type u :=
  E
```

**Design Note**: Type synonym (not subtype) for flexibility with propositional equality.

**Imports**: `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Difficulty**: medium

---

### 2.2 TangentBundle

**Concept**: Total space of tangent bundle as dependent sum.

**NL Statement**: "The tangent bundle TM is the dependent sum over all points x of the tangent space at x, i.e., Σ (x : M), TangentSpace I x."

**Lean 4 Definition**:
```lean
abbrev TangentBundle
    {𝕜 : Type u₁} [NontriviallyNormedField 𝕜]
    {E : Type u₂} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type u₃} [TopologicalSpace H]
    (I : ModelWithCorners 𝕜 E H)
    (M : Type u₄) [TopologicalSpace M] [ChartedSpace H M] :
    Type (max u₄ u₂) :=
  Bundle.TotalSpace E (TangentSpace I)
```

**Imports**: `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Difficulty**: medium

---

### 2.3 Vector Fields

**Concept**: Section of tangent bundle.

**NL Statement**: "A vector field on M is a function assigning to each point x a tangent vector in TangentSpace I x, i.e., a section (x : M) → TangentSpace I x."

**Type**: `(x : M) → TangentSpace I x`

**Imports**: `Mathlib.Geometry.Manifold.VectorField.LieBracket`

**Difficulty**: medium

---

## 3. MANIFOLD DERIVATIVES

### 3.1 MDifferentiableAt

**Concept**: Differentiability of maps between manifolds.

**NL Statement**: "A map f : M → M' is differentiable at x if it is differentiable when read through charts."

**Lean 4 Definition**:
```lean
def MDifferentiableAt
    {𝕜 : Type u₁} [NontriviallyNormedField 𝕜]
    {E : Type u₂} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type u₃} [TopologicalSpace H]
    (I : ModelWithCorners 𝕜 E H)
    {M : Type u₄} [TopologicalSpace M] [ChartedSpace H M]
    {E' : Type u₅} [NormedAddCommGroup E'] [NormedSpace 𝕜 E']
    {H' : Type u₆} [TopologicalSpace H']
    (I' : ModelWithCorners 𝕜 E' H')
    {M' : Type u₇} [TopologicalSpace M'] [ChartedSpace H' M']
    (f : M → M') (x : M) : Prop
```

**Imports**: `Mathlib.Geometry.Manifold.MFDeriv.Defs`

**Difficulty**: medium

---

### 3.2 mfderiv (Manifold Derivative)

**Concept**: Derivative of f as continuous linear map between tangent spaces.

**NL Statement**: "The manifold derivative mfderiv I I' f x is the derivative of f at x, a continuous linear map from TangentSpace I x to TangentSpace I' (f x). Returns 0 if f is not differentiable."

**Lean 4 Definition**:
```lean
def mfderiv
    {𝕜 : Type u₁} [NontriviallyNormedField 𝕜]
    {E : Type u₂} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type u₃} [TopologicalSpace H]
    (I : ModelWithCorners 𝕜 E H)
    {M : Type u₄} [TopologicalSpace M] [ChartedSpace H M]
    {E' : Type u₅} [NormedAddCommGroup E'] [NormedSpace 𝕜 E']
    {H' : Type u₆} [TopologicalSpace H']
    (I' : ModelWithCorners 𝕜 E' H')
    {M' : Type u₇} [TopologicalSpace M'] [ChartedSpace H' M']
    (f : M → M') (x : M) :
    TangentSpace I x →L[𝕜] TangentSpace I' (f x)
```

**Imports**: `Mathlib.Geometry.Manifold.MFDeriv.Defs`

**Difficulty**: hard

---

### 3.3 HasMFDerivAt

**Concept**: Asserts specific derivative value.

**NL Statement**: "HasMFDerivAt I I' f x f' asserts that f' is the derivative of f at x."

**Lean 4 Definition**:
```lean
def HasMFDerivAt
    {𝕜 : Type u₁} [NontriviallyNormedField 𝕜]
    -- ... type parameters ...
    (f : M → M') (x : M)
    (f' : TangentSpace I x →L[𝕜] TangentSpace I' (f x)) : Prop
```

**Imports**: `Mathlib.Geometry.Manifold.MFDeriv.Defs`

**Difficulty**: hard

---

## 4. LIE ALGEBRAS

### 4.1 LieRing

**Concept**: Additive group with bracket operation.

**NL Statement**: "A Lie ring is an additive commutative group with a bracket operation ⁅·,·⁆ satisfying: (1) bilinearity, (2) skew-symmetry ⁅x, x⁆ = 0, and (3) the Jacobi identity."

**Jacobi Identity**:
```lean
⁅x, ⁅y, z⁆⁆ = ⁅⁅x, y⁆, z⁆ + ⁅y, ⁅x, z⁆⁆
```

**Imports**: `Mathlib.Algebra.Lie.Basic`

**Difficulty**: medium

---

### 4.2 LieAlgebra

**Concept**: Lie ring over a commutative ring.

**NL Statement**: "A Lie algebra L over commutative ring R is a Lie ring with R-module structure such that the bracket is R-linear: ⁅x, t • y⁆ = t • ⁅x, y⁆."

**Imports**: `Mathlib.Algebra.Lie.Basic`

**Difficulty**: medium

---

### 4.3 Lie Algebra Morphisms

**Concept**: Structure-preserving maps between Lie algebras.

**NL Statement**: "A Lie algebra homomorphism is a linear map preserving brackets. A Lie algebra equivalence is a bijective homomorphism with inverse also a homomorphism."

**Lean 4 Notations**:
- `L₁ →ₗ⁅R⁆ L₂` — Lie homomorphism
- `L₁ ≃ₗ⁅R⁆ L₂` — Lie equivalence

**Imports**: `Mathlib.Algebra.Lie.Basic`

**Difficulty**: medium

---

### 4.4 Classical Lie Algebras

**Concept**: Standard matrix Lie algebras.

**NL Statement**: "The symplectic Lie algebra sp(n) consists of matrices skew-adjoint with respect to the canonical skew-symmetric form. The orthogonal Lie algebra so(n) consists of skew-symmetric matrices."

**Imports**: `Mathlib.Algebra.Lie.Classical`

**Difficulty**: medium

---

## 5. LIE GROUPS

### 5.1 GroupLieAlgebra

**Concept**: Lie algebra of a Lie group.

**NL Statement**: "The Lie algebra of a Lie group G is the tangent space at the identity element, equipped with a bracket operation defined via left-invariant vector fields."

**Lean 4 Definition**:
```lean
abbrev GroupLieAlgebra
    (I : ModelWithCorners 𝕜 E H) (G : Type u_4) : Type u_3 :=
  TangentSpace I 1
```

**Imports**: `Mathlib.Geometry.Manifold.GroupLieAlgebra`

**Difficulty**: hard

---

### 5.2 Lie Bracket on GroupLieAlgebra

**Concept**: Bracket via left-invariant vector fields.

**NL Statement**: "For vectors v, w in the Lie algebra (tangent space at identity), their bracket is computed by extending to left-invariant vector fields, taking their Lie bracket as vector fields, and evaluating at identity."

**Lean 4 Instance**:
```lean
instance instBracketGroupLieAlgebra :
  Bracket (GroupLieAlgebra I G) (GroupLieAlgebra I G) where
  bracket := fun (v w : GroupLieAlgebra I G) =>
    VectorField.mlieBracket I
      (mulInvariantVectorField v)
      (mulInvariantVectorField w)
      1
```

**Imports**: `Mathlib.Geometry.Manifold.GroupLieAlgebra`

**Difficulty**: hard

---

## 6. VECTOR FIELDS AND LIE BRACKETS

### 6.1 mlieBracket (Lie Bracket of Vector Fields)

**Concept**: Bracket measuring noncommutativity of vector fields.

**NL Statement**: "The Lie bracket [V, W] of vector fields V and W at point x₀ measures their noncommutativity as differential operators, computed as the pullback of the bracket in model space through extended charts."

**Lean 4 Definition**:
```lean
def VectorField.mlieBracket
    {𝕜 : Type u₁} [NontriviallyNormedField 𝕜]
    {H : Type u₂} [TopologicalSpace H]
    {E : Type u₃} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    (I : ModelWithCorners 𝕜 E H)
    {M : Type u₄} [TopologicalSpace M] [ChartedSpace H M]
    (V W : (x : M) → TangentSpace I x) (x₀ : M) :
    TangentSpace I x₀
```

**Imports**: `Mathlib.Geometry.Manifold.VectorField.LieBracket`

**Difficulty**: hard

---

### 6.2 Jacobi Identity for Vector Fields

**Concept**: Lie algebra axiom for vector field brackets.

**NL Statement**: "For C² vector fields U, V, W, the Jacobi identity holds: [U, [V, W]] = [[U, V], W] + [V, [U, W]]."

**Theorem Name**: `leibniz_identity_mlieBracket`

**Imports**: `Mathlib.Geometry.Manifold.VectorField.LieBracket`

**Difficulty**: hard

---

## 7. INTEGRAL CURVES

### 7.1 IsMIntegralCurve (Global)

**Concept**: Curve whose tangent equals vector field.

**NL Statement**: "A curve γ : ℝ → M is a global integral curve of vector field v if γ'(t) = v(γ(t)) for all t, i.e., the curve's velocity always equals the vector field evaluated at the curve's position."

**Lean 4 Definition**:
```lean
def IsMIntegralCurve
    {E : Type u₁} [NormedAddCommGroup E] [NormedSpace ℝ E]
    {H : Type u₂} [TopologicalSpace H]
    {I : ModelWithCorners ℝ E H}
    {M : Type u₃} [TopologicalSpace M] [ChartedSpace H M]
    (γ : ℝ → M) (v : (x : M) → TangentSpace I x) : Prop :=
  ∀ (t : ℝ), HasMFDerivAt (modelWithCornersSelf ℝ ℝ) I γ t
    (ContinuousLinearMap.smulRight 1 (v (γ t)))
```

**Imports**: `Mathlib.Geometry.Manifold.IntegralCurve.Basic`

**Difficulty**: hard

---

### 7.2 IsMIntegralCurveOn (Local)

**Concept**: Integral curve on time subset.

**NL Statement**: "A curve γ is an integral curve of v on time subset s ⊆ ℝ if γ'(t) = v(γ(t)) for all t ∈ s."

**Lean 4 Definition**:
```lean
def IsMIntegralCurveOn
    (γ : ℝ → M) (v : (x : M) → TangentSpace I x) (s : Set ℝ) : Prop :=
  ∀ t ∈ s, HasMFDerivWithinAt (modelWithCornersSelf ℝ ℝ) I γ s t
    (ContinuousLinearMap.smulRight 1 (v (γ t)))
```

**Imports**: `Mathlib.Geometry.Manifold.IntegralCurve.Basic`

**Difficulty**: hard

---

### 7.3 Existence and Uniqueness

**Concept**: Picard-Lindelöf theorem for integral curves.

**NL Statement**: "For Lipschitz vector fields, integral curves exist locally and are unique. This follows from the Picard-Lindelöf theorem for ODEs."

**Key Modules**:
- `Mathlib.Geometry.Manifold.IntegralCurve.ExistUnique`
- `Mathlib.Analysis.ODE.PicardLindelof`

**Imports**: `Mathlib.Geometry.Manifold.IntegralCurve.ExistUnique`

**Difficulty**: hard

---

## 8. EXTERIOR ALGEBRA

### 8.1 ExteriorAlgebra

**Concept**: Algebra of antisymmetric tensors.

**NL Statement**: "The exterior algebra ⋀M over ring R is the quotient of the tensor algebra by the ideal generated by elements m ⊗ m, implemented as Clifford algebra with zero quadratic form."

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

### 8.2 ι (Canonical Embedding)

**Concept**: Embedding module into exterior algebra.

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

### 8.3 Key Properties

**Concept**: Fundamental exterior algebra identities.

**NL Statement**: "In the exterior algebra: (1) generators square to zero: (ι m)² = 0, and (2) generators anticommute: ι x ∧ ι y = -ι y ∧ ι x."

**Lean 4 Theorems**:
```lean
theorem ι_sq_zero {m : M} :
  (ι R) m * (ι R) m = 0

theorem ι_add_mul_swap {x y : M} :
  (ι R) x * (ι R) y + (ι R) y * (ι R) x = 0
```

**Imports**: `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`

**Difficulty**: easy

---

### 8.4 exteriorPower

**Concept**: n-th exterior power as submodule.

**NL Statement**: "The n-th exterior power ⋀ⁿM is the submodule of the exterior algebra generated by products of n elements."

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

## 9. KEY THEOREMS

### 9.1 Inverse Function Theorem

**Concept**: Local invertibility from invertible derivative.

**NL Statement**: "If f has an invertible strict derivative at a, then f is locally invertible and the inverse has derivative (f')⁻¹."

**Lean 4 Theorem**:
```lean
theorem HasStrictFDerivAt.to_localInverse
    {𝕜 : Type u₁} [NontriviallyNormedField 𝕜]
    {E : Type u₂} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {F : Type u₃} [NormedAddCommGroup F] [NormedSpace 𝕜 F]
    {f : E → F} {f' : E ≃L[𝕜] F} {a : E}
    [CompleteSpace E]
    (hf : HasStrictFDerivAt f (↑f') a) :
  HasStrictFDerivAt (localInverse f f' a hf) (↑f'.symm) (f a)
```

**Imports**: `Mathlib.Analysis.Calculus.InverseFunctionTheorem.FDeriv`

**Difficulty**: hard

---

### 9.2 Implicit Function Theorem

**Concept**: Solving equations near known solutions.

**NL Statement**: "For f : E → F with surjective derivative at a and complemented kernel, there exists a function φ defined near f(a) such that f(φ(y, z)) determines solutions to f(x) = y locally."

**Lean 4 Definition**:
```lean
def HasStrictFDerivAt.implicitFunction
    {f : E → F} {f' : E →L[𝕜] F} {a : E}
    (hf : HasStrictFDerivAt f f' a)
    (hf' : LinearMap.range f' = ⊤) :
  F → ↥(LinearMap.ker f') → E
```

**Imports**: `Mathlib.Analysis.Calculus.Implicit`

**Difficulty**: hard

---

## 10. MISSING THEOREMS & BRIDGE THEOREMS

### 10.1 Generalized Stokes' Theorem (CRITICAL BRIDGE THEOREM)

**NL Statement**: "For a smooth n-dimensional manifold M with boundary ∂M and a smooth (n-1)-form ω with compact support, the integral of the exterior derivative dω over M equals the integral of ω over the boundary: ∫_M dω = ∫_{∂M} ω"

**Mathematical Significance - UNIFYING THEOREM**:
The Generalized Stokes' Theorem unifies ALL fundamental theorems of calculus:

| k-value | Dimension | Classical Theorem | Form |
|---------|-----------|-------------------|------|
| 0 | 1D | **Fundamental Theorem of Calculus** | ∫_a^b f'(x)dx = f(b) - f(a) |
| 1 | 2D | **Green's Theorem** | ∮_C (P dx + Q dy) = ∬_D (∂Q/∂x - ∂P/∂y) dA |
| 1 | 3D | **Classical Stokes' Theorem** | ∮_C F·dr = ∬_S (∇×F)·dS |
| 2 | 3D | **Divergence Theorem (Gauss)** | ∬_S F·dS = ∭_V (∇·F) dV |

**Expected Lean 4 Template**:
```lean
-- The generalized Stokes' theorem
theorem generalized_stokes
  {n : ℕ} (M : Type*) [SmoothManifoldWithCorners I M] [CompactSpace M]
  (hM : HasBoundary M)
  (ω : DifferentialForm (n-1) M)
  (hω : ContMDiff I ⊤ ω) :
  ∫ x in M, exteriord ω x = ∫ y in ∂M, ω y := sorry

-- Where exteriord is the exterior derivative
-- ∂M denotes the boundary manifold with induced orientation
```

**Dependencies**:
- Exterior algebra (formalized: `Mathlib.LinearAlgebra.ExteriorAlgebra`)
- Differential forms as smooth sections (partially formalized)
- Integration on manifolds (limited)
- Boundary operator for manifolds with corners (available)

**Proof Approach**:
1. Local version on standard cube via Fubini
2. Partition of unity to globalize
3. Orientation compatibility at boundary
4. Sum contributions via Stokes on each chart

**Cross-KB Connections**:
- **real_complex_analysis**: FTC, Cauchy integral theorem
- **topology**: Boundary operator, orientation
- **measure_theory**: Integration on manifolds

**Status**: NOT FORMALIZED - Major infrastructure requirement

**Imports**: `Mathlib.Geometry.Manifold.IsManifold.Basic`, `Mathlib.LinearAlgebra.ExteriorAlgebra.Basic`

**Difficulty**: very hard

---

### 10.2 Classical Stokes' Theorem (3D Vector Calculus)

**NL Statement**: "For a smooth oriented surface S with boundary curve ∂S and vector field F, the circulation of F around ∂S equals the flux of curl(F) through S: ∮_{∂S} F·dr = ∬_S (∇×F)·dS"

**Expected Lean 4 Template**:
```lean
theorem classical_stokes
  {S : Set (EuclideanSpace ℝ 3)} (hS : IsNiceSurface S)
  {F : EuclideanSpace ℝ 3 → EuclideanSpace ℝ 3}
  (hF : ContDiff ℝ 1 F) :
  ∮ ∂S, F · dr = ∬ S, (curl F) · dS := sorry
```

**Status**: NOT FORMALIZED

**Difficulty**: very hard

---

### 10.3 Divergence Theorem (Gauss)

**NL Statement**: "For a compact region V with smooth boundary surface S and outward normal n, and smooth vector field F: ∬_S F·n dS = ∭_V (∇·F) dV"

**Expected Lean 4 Template**:
```lean
theorem divergence_theorem
  {V : Set (EuclideanSpace ℝ 3)} (hV : IsCompact V) (hV_nice : HasSmoothBoundary V)
  {F : EuclideanSpace ℝ 3 → EuclideanSpace ℝ 3}
  (hF : ContDiff ℝ 1 F) :
  ∬ ∂V, F · outwardNormal dS = ∭ V, div F dV := sorry
```

**Status**: NOT FORMALIZED

**Difficulty**: very hard

---

### 10.4 de Rham Cohomology - NOT FORMALIZED

**NL Statement**: "The de Rham cohomology groups H^k_dR(M) = ker(d) / im(d) measure closed forms modulo exact forms."

**Status**: Requires exterior derivative and integration on manifolds.

**Difficulty**: very hard

---

### 10.5 Riemannian Curvature Tensor - LIMITED

**NL Statement**: "The Riemann curvature tensor R(X,Y)Z measures the failure of parallel transport to commute."

**Status**: Basic Riemannian metric defined, but curvature tensors have limited formalization.

**Difficulty**: very hard

---

## 11. STANDARD SETUP

**NL Statement**: "Standard imports and variable declarations for differential geometry work."

**Lean 4**:
```lean
import Mathlib.Geometry.Manifold.IsManifold.Basic
import Mathlib.Geometry.Manifold.MFDeriv.Defs
import Mathlib.Geometry.Manifold.VectorField.LieBracket
import Mathlib.Geometry.Manifold.IntegralCurve.Basic
import Mathlib.Geometry.Manifold.GroupLieAlgebra
import Mathlib.Algebra.Lie.Basic
import Mathlib.LinearAlgebra.ExteriorAlgebra.Basic
import Mathlib.Analysis.Calculus.InverseFunctionTheorem.FDeriv
import Mathlib.Analysis.Calculus.Implicit

variable {𝕜 : Type*} [NontriviallyNormedField 𝕜]
variable {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
variable {H : Type*} [TopologicalSpace H]
variable (I : ModelWithCorners 𝕜 E H)
variable {M : Type*} [TopologicalSpace M] [ChartedSpace H M] [IsManifold I ∞ M]
```

**Difficulty**: easy

---

## 12. NOTATION REFERENCE

| Math Notation | Lean 4 Notation | Description |
|---------------|-----------------|-------------|
| T_x M | `TangentSpace I x` | Tangent space at x |
| TM | `TangentBundle I M` | Tangent bundle |
| df_x | `mfderiv I I' f x` | Manifold derivative |
| ⁅v, w⁆ | `Bracket.bracket v w` | Lie bracket |
| [V, W] | `mlieBracket I V W` | Lie bracket of vector fields |
| ⋀M | `ExteriorAlgebra R M` | Exterior algebra |
| ⋀ⁿM | `exteriorPower R n M` | n-th exterior power |
| C^∞(M, N) | `MDifferentiable I I' ∞ f` | Smooth maps |

---

## Sources

- [Mathlib.Geometry.Manifold.IsManifold.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/IsManifold/Basic.html)
- [Mathlib.Geometry.Manifold.MFDeriv.Defs](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/MFDeriv/Defs.html)
- [Mathlib.Algebra.Lie.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Lie/Basic.html)
- [Mathlib.Geometry.Manifold.GroupLieAlgebra](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/GroupLieAlgebra.html)
- [Mathlib.Geometry.Manifold.VectorField.LieBracket](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/VectorField/LieBracket.html)
- [Mathlib.Geometry.Manifold.IntegralCurve.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/IntegralCurve/Basic.html)
- [Mathlib.Analysis.Calculus.Implicit](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/Calculus/Implicit.html)
- [Elements of Differential Geometry in Lean](https://arxiv.org/pdf/2108.00484)
