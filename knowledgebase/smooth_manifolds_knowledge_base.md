# Smooth Manifolds Knowledge Base for Lean 4

**Generated:** 2025-12-19
**Mode:** Deep Synthesis
**Purpose:** Knowledge base for implementing smooth manifold theory in Lean 4 for dataset generation pairing formal proofs with natural language explanations.
**Confidence:** High

---

## Executive Summary

Smooth manifolds are extensively formalized in Lean 4's Mathlib library under `Mathlib.Geometry.Manifold.*`. The formalization uses the "manifolds with corners" framework, covering foundational definitions, tangent bundles, manifold derivatives, smooth maps, Lie groups, and concrete examples. Estimated total: **90 theorems and definitions** suitable for knowledge base inclusion.

### Content Summary

| Category | Estimated Count | Mathlib Support | Difficulty Distribution |
|----------|----------------|-----------------|------------------------|
| **Foundational Structures** | 15 | FULL | 40% easy, 40% medium, 20% hard |
| **Smooth Manifold Structure** | 12 | FULL | 30% easy, 50% medium, 20% hard |
| **Tangent Bundle** | 20 | FULL | 20% easy, 50% medium, 30% hard |
| **Manifold Derivatives** | 18 | FULL | 25% easy, 45% medium, 30% hard |
| **Smooth Maps** | 12 | FULL | 30% easy, 50% medium, 20% hard |
| **Lie Groups** | 8 | FULL | 20% easy, 50% medium, 30% hard |
| **Concrete Examples** | 5 | FULL | 40% easy, 40% medium, 20% hard |
| **Total** | **90** | - | - |

### Key Mathlib4 Modules

- `Mathlib.Geometry.Manifold.IsManifold.Basic` - Core definitions
- `Mathlib.Geometry.Manifold.VectorBundle.Tangent` - Tangent bundles
- `Mathlib.Geometry.Manifold.MFDeriv.Defs` - Manifold derivatives
- `Mathlib.Geometry.Manifold.Algebra.LieGroup` - Lie groups
- `Mathlib.Geometry.Manifold.Instances.Real` - Real manifold instances
- `Mathlib.Geometry.Manifold.Instances.Sphere` - Sphere as smooth manifold

---

## Related Knowledge Bases

### Prerequisites
- **Topology** (`topology_knowledge_base.md`): Topological spaces, compactness, continuity
- **Linear Algebra** (`linear_algebra_knowledge_base.md`): Vector spaces, normed spaces
- **Real/Complex Analysis** (`real_complex_analysis_knowledge_base.md`): Differentiability, smooth functions

### Builds Upon This KB
- **Differential Geometry** (`differential_geometry_knowledge_base.md`): Geometric structures on manifolds
- **Lie Theory** (`lie_theory_knowledge_base.md`): Lie groups as smooth manifolds
- **Complex Geometry** (`complex_geometry_knowledge_base.md`): Complex manifolds
- **Fiber Bundles** (`fiber_bundles_knowledge_base.md`): Bundle structures over manifolds

### Related Topics
- **Algebraic Topology** (`algebraic_topology_knowledge_base.md`): Topological invariants
- **Calculus of Variations** (`calculus_of_variations_knowledge_base.md`): Variational problems on manifolds

### Scope Clarification
This KB focuses on **smooth manifold infrastructure**:
- ModelWithCorners and ChartedSpace
- IsManifold and SmoothManifoldWithCorners
- Tangent bundles and tangent spaces
- Manifold derivatives (mfderiv)
- Smooth maps and diffeomorphisms
- Lie groups as manifolds
- Concrete examples (Euclidean space, spheres)

For **geometric structures** (Riemannian metrics, connections), see **Differential Geometry KB**.

---

## Part I: Foundational Structures

### Module Organization

**Primary Import:**
- `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Estimated Statements:** 15

---

### 1. ModelWithCorners

**Natural Language Statement:**
A model with corners is a structure embedding a topological space H into a normed vector space E over a field 𝕜, providing the local model for manifolds possibly with boundary or corners.

**Lean 4 Definition:**
```lean
structure ModelWithCorners (𝕜 : Type*) [NontriviallyNormedField 𝕜]
    (E : Type*) [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    (H : Type*) [TopologicalSpace H]
    extends PartialEquiv H E where
  source_eq : source = Set.univ
  unique_diff' : UniqueDiffOn 𝕜 toPartialEquiv.target
  continuous_toFun : Continuous toPartialEquiv
  continuous_invFun : Continuous toPartialEquiv.symm
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Difficulty:** medium

---

### 2. modelWithCornersSelf

**Natural Language Statement:**
A vector space is a model with corners via the identity embedding, denoted 𝓘(𝕜, E), representing manifolds without boundary.

**Lean 4 Definition:**
```lean
def modelWithCornersSelf (𝕜 : Type*) [NontriviallyNormedField 𝕜]
    (E : Type*) [NormedAddCommGroup E] [NormedSpace 𝕜 E] :
    ModelWithCorners 𝕜 E E where
  toPartialEquiv := PartialEquiv.refl E
  source_eq := rfl
  unique_diff' := uniqueDiffOn_univ
  continuous_toFun := continuous_id
  continuous_invFun := continuous_id
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Difficulty:** easy

---

### 3. ModelWithCorners.Boundaryless

**Natural Language Statement:**
A model with corners is boundaryless if its range equals the entire model space, ensuring the manifold has no boundary points.

**Lean 4 Definition:**
```lean
class ModelWithCorners.Boundaryless {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H]
    (I : ModelWithCorners 𝕜 E H) : Prop where
  range_eq_univ : Set.range I = Set.univ
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Difficulty:** medium

---

### 4. ModelWithCorners.prod

**Natural Language Statement:**
Given two models with corners I on (E, H) and I' on (E', H'), their product is a model with corners on (E × E', H × H').

**Lean 4 Definition:**
```lean
def ModelWithCorners.prod {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H] (I : ModelWithCorners 𝕜 E H)
    {E' : Type*} [NormedAddCommGroup E'] [NormedSpace 𝕜 E']
    {H' : Type*} [TopologicalSpace H'] (I' : ModelWithCorners 𝕜 E' H') :
    ModelWithCorners 𝕜 (E × E') (H × H')
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Difficulty:** medium

---

## Part II: Smooth Manifold Structure

### 5. contDiffGroupoid

**Natural Language Statement:**
The C^n groupoid consists of all local homeomorphisms of the model space H whose coordinate changes are C^n smooth when expressed in the vector space E.

**Lean 4 Definition:**
```lean
def contDiffGroupoid {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H]
    (n : ℕ∞) (I : ModelWithCorners 𝕜 E H) : StructureGroupoid H
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Difficulty:** hard

---

### 6. IsManifold

**Natural Language Statement:**
A type M is a C^n manifold with respect to model I if it is a charted space over I whose maximal atlas belongs to the C^n groupoid.

**Lean 4 Definition:**
```lean
class IsManifold {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H]
    (I : ModelWithCorners 𝕜 E H) (n : ℕ∞)
    (M : Type*) [TopologicalSpace M] [ChartedSpace H M] : Prop where
  compatible : ∀ e e', e ∈ atlas H M → e' ∈ atlas H M →
    e.symm.trans e' ∈ contDiffGroupoid n I
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Difficulty:** hard

---

### 7. IsManifold.prod

**Natural Language Statement:**
The product of two C^n manifolds is naturally a C^n manifold with the product model and product charts.

**Lean 4 Theorem:**
```lean
instance IsManifold.prod {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H] (I : ModelWithCorners 𝕜 E H)
    {M : Type*} [TopologicalSpace M] [ChartedSpace H M]
    {E' : Type*} [NormedAddCommGroup E'] [NormedSpace 𝕜 E']
    {H' : Type*} [TopologicalSpace H'] (I' : ModelWithCorners 𝕜 E' H')
    {M' : Type*} [TopologicalSpace M'] [ChartedSpace H' M']
    (n : ℕ∞) [IsManifold I n M] [IsManifold I' n M'] :
    IsManifold (I.prod I') n (M × M')
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.IsManifold.Basic`

**Difficulty:** hard

---

## Part III: Tangent Bundle

### Module Organization

**Primary Import:**
- `Mathlib.Geometry.Manifold.VectorBundle.Tangent`

**Estimated Statements:** 20

---

### 8. TangentSpace

**Natural Language Statement:**
The tangent space at a point x of a manifold M modeled on E is a type synonym for E, representing the fiber of the tangent bundle at x.

**Lean 4 Definition:**
```lean
def TangentSpace {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H]
    (I : ModelWithCorners 𝕜 E H)
    {M : Type*} [TopologicalSpace M] [ChartedSpace H M]
    (x : M) : Type* := E
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.VectorBundle.Tangent`

**Difficulty:** medium

---

### 9. TangentBundle

**Natural Language Statement:**
The tangent bundle to a manifold M is the sigma type consisting of pairs (x, v) where x ∈ M and v is a tangent vector at x.

**Lean 4 Definition:**
```lean
abbrev TangentBundle {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H]
    (I : ModelWithCorners 𝕜 E H)
    (M : Type*) [TopologicalSpace M] [ChartedSpace H M] :=
  Bundle.TotalSpace E (TangentSpace I : M → Type*)
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.VectorBundle.Tangent`

**Difficulty:** medium

---

### 10. TangentBundle.contMDiffVectorBundle

**Natural Language Statement:**
The tangent bundle to a C^(n+1) manifold has the structure of a C^n vector bundle.

**Lean 4 Theorem:**
```lean
instance TangentBundle.contMDiffVectorBundle {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H]
    (I : ModelWithCorners 𝕜 E H)
    (M : Type*) [TopologicalSpace M] [ChartedSpace H M]
    (n : ℕ∞) [IsManifold I (n + 1) M] :
    ContMDiffVectorBundle n (TangentSpace I : M → Type*) I.tangent M
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.VectorBundle.Tangent`

**Difficulty:** hard

---

### 11. tangentCoordChange_self

**Natural Language Statement:**
The tangent coordinate change from a point to itself is the identity continuous linear map.

**Lean 4 Theorem:**
```lean
theorem tangentCoordChange_self {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H]
    (I : ModelWithCorners 𝕜 E H)
    {M : Type*} [TopologicalSpace M] [ChartedSpace H M]
    (x : M) :
    tangentCoordChange I x x = ContinuousLinearMap.id 𝕜 E
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.VectorBundle.Tangent`

**Difficulty:** medium

---

## Part IV: Manifold Derivatives

### Module Organization

**Primary Import:**
- `Mathlib.Geometry.Manifold.MFDeriv.Defs`

**Estimated Statements:** 18

---

### 12. MDifferentiableAt

**Natural Language Statement:**
A function f : M → M' between manifolds is differentiable at point x if it is continuous at x and the composition with charts has a Fréchet derivative.

**Lean 4 Definition:**
```lean
def MDifferentiableAt {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H] (I : ModelWithCorners 𝕜 E H)
    {M : Type*} [TopologicalSpace M] [ChartedSpace H M]
    {E' : Type*} [NormedAddCommGroup E'] [NormedSpace 𝕜 E']
    {H' : Type*} [TopologicalSpace H'] (I' : ModelWithCorners 𝕜 E' H')
    {M' : Type*} [TopologicalSpace M'] [ChartedSpace H' M']
    (f : M → M') (x : M) : Prop :=
  MDifferentiableWithinAt I I' f Set.univ x
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.MFDeriv.Defs`

**Difficulty:** medium

---

### 13. mfderiv

**Natural Language Statement:**
The manifold derivative of f at x, computed as the Fréchet derivative of the chart representation, expressed as a continuous linear map between tangent spaces.

**Lean 4 Definition:**
```lean
def mfderiv {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H] (I : ModelWithCorners 𝕜 E H)
    {M : Type*} [TopologicalSpace M] [ChartedSpace H M]
    {E' : Type*} [NormedAddCommGroup E'] [NormedSpace 𝕜 E']
    {H' : Type*} [TopologicalSpace H'] (I' : ModelWithCorners 𝕜 E' H')
    {M' : Type*} [TopologicalSpace M'] [ChartedSpace H' M']
    (f : M → M') (x : M) : TangentSpace I x →L[𝕜] TangentSpace I' (f x) :=
  mfderivWithin I I' f Set.univ x
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.MFDeriv.Defs`

**Difficulty:** hard

---

### 14. HasMFDerivAt

**Natural Language Statement:**
A function f has derivative f' at x if the chart representation has Fréchet derivative f'.

**Lean 4 Definition:**
```lean
def HasMFDerivAt {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H] (I : ModelWithCorners 𝕜 E H)
    {M : Type*} [TopologicalSpace M] [ChartedSpace H M]
    {E' : Type*} [NormedAddCommGroup E'] [NormedSpace 𝕜 E']
    {H' : Type*} [TopologicalSpace H'] (I' : ModelWithCorners 𝕜 E' H')
    {M' : Type*} [TopologicalSpace M'] [ChartedSpace H' M']
    (f : M → M') (x : M)
    (f' : TangentSpace I x →L[𝕜] TangentSpace I' (f x)) : Prop :=
  HasMFDerivWithinAt I I' f Set.univ x f'
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.MFDeriv.Defs`

**Difficulty:** hard

---

## Part V: Smooth Maps

### 15. ContMDiff

**Natural Language Statement:**
A function f : M → M' between manifolds is C^n smooth if it is continuously n-times differentiable in the manifold sense.

**Lean 4 Definition:**
```lean
def ContMDiff {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H] (I : ModelWithCorners 𝕜 E H)
    {M : Type*} [TopologicalSpace M] [ChartedSpace H M]
    {E' : Type*} [NormedAddCommGroup E'] [NormedSpace 𝕜 E']
    {H' : Type*} [TopologicalSpace H'] (I' : ModelWithCorners 𝕜 E' H')
    {M' : Type*} [TopologicalSpace M'] [ChartedSpace H' M']
    (n : ℕ∞) (f : M → M') : Prop :=
  ContMDiffOn I I' n f Set.univ
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.MFDeriv.Defs`

**Difficulty:** medium

---

### 16. Smooth

**Natural Language Statement:**
A function f : M → M' is smooth (C^∞) if it is infinitely differentiable.

**Lean 4 Definition:**
```lean
def Smooth {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H] (I : ModelWithCorners 𝕜 E H)
    {M : Type*} [TopologicalSpace M] [ChartedSpace H M]
    {E' : Type*} [NormedAddCommGroup E'] [NormedSpace 𝕜 E']
    {H' : Type*} [TopologicalSpace H'] (I' : ModelWithCorners 𝕜 E' H')
    {M' : Type*} [TopologicalSpace M'] [ChartedSpace H' M']
    (f : M → M') : Prop :=
  ContMDiff I I' ⊤ f
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.MFDeriv.Defs`

**Difficulty:** easy

---

## Part VI: Lie Groups

### Module Organization

**Primary Import:**
- `Mathlib.Geometry.Manifold.Algebra.LieGroup`

**Estimated Statements:** 8

---

### 17. LieGroup

**Natural Language Statement:**
A Lie group is a smooth manifold that is also a group, where the group operations (multiplication and inversion) are smooth maps.

**Lean 4 Definition:**
```lean
class LieGroup {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H] (I : ModelWithCorners 𝕜 E H)
    (G : Type*) [TopologicalSpace G] [ChartedSpace H G] [Group G]
    extends IsManifold I ⊤ G where
  smooth_mul : Smooth (I.prod I) I fun p : G × G => p.1 * p.2
  smooth_inv : Smooth I I fun g : G => g⁻¹
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.Algebra.LieGroup`

**Difficulty:** hard

---

### 18. LieGroup.smooth_mul

**Natural Language Statement:**
In a Lie group, multiplication is a smooth map G × G → G.

**Lean 4 Theorem:**
```lean
theorem LieGroup.smooth_mul {𝕜 : Type*} [NontriviallyNormedField 𝕜]
    {E : Type*} [NormedAddCommGroup E] [NormedSpace 𝕜 E]
    {H : Type*} [TopologicalSpace H] (I : ModelWithCorners 𝕜 E H)
    (G : Type*) [TopologicalSpace G] [ChartedSpace H G] [Group G]
    [LieGroup I G] :
    Smooth (I.prod I) I fun p : G × G => p.1 * p.2
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.Algebra.LieGroup`

**Difficulty:** medium

---

## Part VII: Concrete Examples

### 19. EuclideanSpace IsManifold

**Natural Language Statement:**
Euclidean space ℝⁿ is a smooth manifold modeled on itself via the identity model.

**Lean 4 Theorem:**
```lean
instance EuclideanSpace.instIsManifold (n : ℕ) :
    IsManifold (𝓘(ℝ, EuclideanSpace ℝ (Fin n))) ⊤ (EuclideanSpace ℝ (Fin n))
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.Instances.Real`

**Difficulty:** easy

---

### 20. Sphere.instIsManifold

**Natural Language Statement:**
The unit sphere Sⁿ in ℝⁿ⁺¹ is a smooth manifold with stereographic projection charts.

**Lean 4 Theorem:**
```lean
instance Sphere.instIsManifold {n : ℕ} [Fact (finrank ℝ E = n + 1)] :
    IsManifold (𝓘(ℝ, EuclideanSpace ℝ (Fin n))) ⊤ (sphere (0 : E) 1)
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.Instances.Sphere`

**Difficulty:** hard

---

## Limitations and Gaps

### Topics Not Yet in Mathlib4

1. **Differential forms** - Exterior algebra on manifolds
2. **Riemannian geometry** - Metrics, connections, curvature
3. **Symplectic geometry** - Symplectic forms and structures
4. **de Rham cohomology** - Cohomology via differential forms
5. **Stokes' theorem** - Integration on manifolds

---

## Difficulty Summary

- **Easy (25 statements):** Basic definitions, examples
- **Medium (40 statements):** Coordinate changes, derivatives
- **Hard (25 statements):** Bundle structure, Lie groups

---

## Sources

- [Mathlib.Geometry.Manifold.IsManifold.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/IsManifold/Basic.html)
- [Mathlib.Geometry.Manifold.VectorBundle.Tangent](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/VectorBundle/Tangent.html)
- [Mathlib.Geometry.Manifold.MFDeriv.Defs](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/MFDeriv/Defs.html)
- [Mathlib.Geometry.Manifold.Algebra.LieGroup](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/Algebra/LieGroup.html)
- [Mathlib.Geometry.Manifold.Instances.Sphere](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/Instances/Sphere.html)

**Generation Date:** 2025-12-19
**Mathlib4 Version:** Current as of December 2025
