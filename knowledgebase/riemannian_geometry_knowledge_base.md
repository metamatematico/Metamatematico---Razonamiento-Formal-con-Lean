# Riemannian Geometry Knowledge Base

**Domain**: Riemannian Geometry (Metric Geometry, Curvature, Geodesics)
**Lean 4 Coverage**: GOOD for inner product spaces and metric spaces; LIMITED for curvature and geodesics
**Source**: Mathlib4 `Analysis.InnerProductSpace.*`, `Topology.MetricSpace.*`, `Geometry.Manifold.*`
**Last Updated**: 2025-12-24
**Related KB**: `differential_geometry` (Lie theory, exterior algebra), `smooth_manifolds` (manifold infrastructure)

---

## Executive Summary

This knowledge base covers Riemannian geometry - the study of smooth manifolds equipped with inner products on tangent spaces. Mathlib4 coverage:

- **Inner Product Spaces**: WELL FORMALIZED - Cauchy-Schwarz, orthogonality, projections
- **Metric Spaces**: WELL FORMALIZED - Completeness, compactness, distance functions
- **Spectral Theory**: WELL FORMALIZED - Self-adjoint operators, eigenvalue theory
- **Riemannian Metrics**: PARTIAL - Inner products exist but full metric tensor integration limited
- **Curvature/Geodesics**: LIMITED - Foundational definitions only, major theorems unformalized

**Key Gaps**: Levi-Civita connection, curvature tensors, exponential map, Hopf-Rinow theorem.

---

## Content Summary

| Part | Topic | Statements | Mathlib Coverage |
|------|-------|------------|------------------|
| 1 | Inner Product Fundamentals | 12 | Complete |
| 2 | Orthogonality and Projections | 10 | Complete |
| 3 | Metric Space Theory | 10 | Complete |
| 4 | Spectral Theory | 8 | Good |
| 5 | Riemannian Metric Foundations | 8 | Partial |
| 6 | Curvature Concepts | 10 | Limited |
| 7 | Geodesics and Exponential Map | 8 | Limited |
| 8 | Classical Riemannian Theorems | 9 | Limited |
| **Total** | | **75** | **~45%** |

**Measurability Score**: 45 (inner product/metric space excellent; curvature/geodesics need templates)

---

## Related Knowledge Bases

### Prerequisites
- **Linear Algebra** (`linear_algebra_knowledge_base.md`): Inner product spaces
- **Smooth Manifolds** (`smooth_manifolds_knowledge_base.md`): Manifold infrastructure, tangent bundles
- **Topology** (`topology_knowledge_base.md`): Metric spaces

### Builds Upon This KB
- **Algebraic Topology** (`algebraic_topology_knowledge_base.md`): Topological aspects of Riemannian manifolds
- **Complex Geometry** (`complex_geometry_knowledge_base.md`): Kähler geometry

### Related Topics
- **Differential Geometry** (`differential_geometry_knowledge_base.md`): Lie theory, exterior algebra
- **Classical Geometry** (`classical_geometry_knowledge_base.md`): Euclidean case
- **Calculus of Variations** (`calculus_of_variations_knowledge_base.md`): Geodesics as variational problems

### Scope Clarification
This KB focuses on **Riemannian geometry**:
- Inner product fundamentals (Cauchy-Schwarz, orthogonality)
- Projections and orthogonal complements
- Metric space theory
- Spectral theory for self-adjoint operators
- Riemannian metric foundations
- (Gaps: Levi-Civita connection, curvature tensors, exponential map, Hopf-Rinow)

For **Lie-theoretic aspects**, see **Differential Geometry KB**.

---

## Part 1: Inner Product Fundamentals

### 1.1 Inner Product Definition

**NL Statement**: "An inner product on a vector space E over field K (real or complex) is a sesquilinear form ⟪·,·⟫ : E × E → K satisfying conjugate symmetry ⟪x,y⟫ = conj(⟪y,x⟫), linearity in the second argument, and positive-definiteness ⟪x,x⟫ > 0 for x ≠ 0."

**Lean 4 Definition**:
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

### 1.2 Norm from Inner Product

**NL Statement**: "In an inner product space, the norm is induced by the inner product via ‖x‖² = Re⟪x,x⟫, equivalently ‖x‖ = √Re⟪x,x⟫."

**Lean 4 Theorem**:
```lean
theorem inner_self_eq_norm_sq (x : E) : re ⟪x, x⟫_𝕜 = ‖x‖ ^ 2
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: easy

---

### 1.3 Cauchy-Schwarz Inequality

**NL Statement**: "For any vectors x, y in an inner product space: |⟪x,y⟫| ≤ ‖x‖·‖y‖, with equality if and only if x and y are linearly dependent."

**Lean 4 Theorem**:
```lean
theorem inner_mul_le_norm_mul_norm (x y : E) : ‖⟪x, y⟫_𝕜‖ ≤ ‖x‖ * ‖y‖

theorem abs_inner_le_norm (x y : E) : |⟪x, y⟫_ℝ| ≤ ‖x‖ * ‖y‖
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: medium

---

### 1.4 Cauchy-Schwarz Equality Condition

**NL Statement**: "Equality holds in Cauchy-Schwarz if and only if the vectors are linearly dependent: |⟪x,y⟫| = ‖x‖·‖y‖ ⟺ ∃ r, x = r • y or y = 0."

**Lean 4 Theorem**:
```lean
theorem inner_mul_eq_norm_mul_norm_iff_of_ne_zero (hx : x ≠ 0) :
    ‖⟪x, y⟫_𝕜‖ = ‖x‖ * ‖y‖ ↔ ∃ r : 𝕜, y = r • x
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: medium

---

### 1.5 Parallelogram Law

**NL Statement**: "In any inner product space: ‖x + y‖² + ‖x - y‖² = 2(‖x‖² + ‖y‖²). This characterizes norms arising from inner products."

**Lean 4 Theorem**:
```lean
theorem parallelogram_law (x y : E) :
    ‖x + y‖ ^ 2 + ‖x - y‖ ^ 2 = 2 * (‖x‖ ^ 2 + ‖y‖ ^ 2)
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: medium

---

### 1.6 Polarization Identity (Real)

**NL Statement**: "In a real inner product space, the inner product can be recovered from the norm: ⟪x,y⟫ = (‖x+y‖² - ‖x-y‖²)/4."

**Lean 4 Theorem**:
```lean
theorem real_inner_eq_norm_sq_sub_norm_sq_div_four (x y : F) :
    ⟪x, y⟫_ℝ = (‖x + y‖ ^ 2 - ‖x - y‖ ^ 2) / 4
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: medium

---

### 1.7 Polarization Identity (Complex)

**NL Statement**: "In a complex inner product space: ⟪x,y⟫ = (‖x+y‖² - ‖x-y‖² + i‖x-iy‖² - i‖x+iy‖²)/4."

**Lean 4 Theorem**:
```lean
theorem inner_eq_sum_norm_sq_div_four (x y : E) :
    ⟪x, y⟫_ℂ = (‖x + y‖ ^ 2 - ‖x - y‖ ^ 2 + I * ‖x - I • y‖ ^ 2 - I * ‖x + I • y‖ ^ 2) / 4
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: hard

---

### 1.8 Pythagorean Theorem

**NL Statement**: "If x and y are orthogonal (⟪x,y⟫ = 0), then ‖x + y‖² = ‖x‖² + ‖y‖²."

**Lean 4 Theorem**:
```lean
theorem norm_add_sq_eq_norm_sq_add_norm_sq (h : ⟪x, y⟫_𝕜 = 0) :
    ‖x + y‖ ^ 2 = ‖x‖ ^ 2 + ‖y‖ ^ 2
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: easy

---

### 1.9 Triangle Inequality from Inner Product

**NL Statement**: "The triangle inequality ‖x + y‖ ≤ ‖x‖ + ‖y‖ follows from Cauchy-Schwarz."

**Lean 4 Theorem**:
```lean
-- Follows from norm structure, which requires triangle inequality
theorem norm_add_le (x y : E) : ‖x + y‖ ≤ ‖x‖ + ‖y‖
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: easy

---

### 1.10 Inner Product Continuity

**NL Statement**: "The inner product is jointly continuous: if xₙ → x and yₙ → y, then ⟪xₙ, yₙ⟫ → ⟪x, y⟫."

**Lean 4 Theorem**:
```lean
theorem continuous_inner : Continuous (fun p : E × E => ⟪p.1, p.2⟫_𝕜)
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: medium

---

### 1.11 Inner Product Positive Definite

**NL Statement**: "For any nonzero vector x: ⟪x, x⟫ > 0. Equivalently, ⟪x, x⟫ = 0 implies x = 0."

**Lean 4 Theorem**:
```lean
theorem inner_self_eq_zero {x : E} : ⟪x, x⟫_𝕜 = 0 ↔ x = 0

theorem inner_self_pos {x : E} (hx : x ≠ 0) : 0 < re ⟪x, x⟫_𝕜
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: easy

---

### 1.12 Real Part of Inner Product

**NL Statement**: "For real inner product spaces, the inner product equals its real part. For complex spaces, Re⟪x,y⟫ gives the real inner product of the underlying real space."

**Lean 4 Theorem**:
```lean
theorem inner_re_symm (x y : E) : re ⟪x, y⟫_𝕜 = re ⟪y, x⟫_𝕜
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: easy

---

## Part 2: Orthogonality and Projections

### 2.1 Orthogonality Definition

**NL Statement**: "Two vectors x and y are orthogonal, written x ⟂ y, if and only if ⟪x, y⟫ = 0."

**Lean 4 Definition**:
```lean
def Orthogonal (x y : E) : Prop := ⟪x, y⟫_𝕜 = 0
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: easy

---

### 2.2 Orthogonality is Symmetric

**NL Statement**: "Orthogonality is symmetric: x ⟂ y if and only if y ⟂ x."

**Lean 4 Theorem**:
```lean
theorem inner_eq_zero_symm {x y : E} : ⟪x, y⟫_𝕜 = 0 ↔ ⟪y, x⟫_𝕜 = 0
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: easy

---

### 2.3 Orthogonal Complement

**NL Statement**: "The orthogonal complement of a subset S ⊆ E is S⟂ = {y ∈ E | ∀ x ∈ S, ⟪x, y⟫ = 0}."

**Lean 4 Definition**:
```lean
def Submodule.orthogonal (K : Submodule 𝕜 E) : Submodule 𝕜 E where
  carrier := { v | ∀ u ∈ K, ⟪u, v⟫_𝕜 = 0 }
  ...
```

**Notation**: `Kᗮ`

**Imports**: `Mathlib.Analysis.InnerProductSpace.Orthogonal.Basic`
**Difficulty**: medium

---

### 2.4 Orthogonal Complement is Closed

**NL Statement**: "For any subset S, its orthogonal complement S⟂ is a closed subspace."

**Lean 4 Theorem**:
```lean
theorem Submodule.isClosed_orthogonal (K : Submodule 𝕜 E) : IsClosed (Kᗮ : Set E)
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Orthogonal.Basic`
**Difficulty**: medium

---

### 2.5 Double Orthogonal Complement

**NL Statement**: "For a closed subspace K, (K⟂)⟂ = K."

**Lean 4 Theorem**:
```lean
theorem Submodule.orthogonal_orthogonal_eq_closure (K : Submodule 𝕜 E) :
    Kᗮᗮ = K.topologicalClosure
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Orthogonal.Basic`
**Difficulty**: medium

---

### 2.6 Orthogonal Projection Existence

**NL Statement**: "For a complete subspace K of a Hilbert space and any x, there exists a unique closest point in K, called the orthogonal projection of x onto K."

**Lean 4 Theorem**:
```lean
theorem exists_norm_eq_iInf_of_complete_subspace (K : Submodule 𝕜 E) [CompleteSpace K]
    (x : E) : ∃ y ∈ K, ‖x - y‖ = ⨅ z : K, ‖x - z‖
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Projection`
**Difficulty**: hard

---

### 2.7 Orthogonal Projection Characterization

**NL Statement**: "The orthogonal projection P_K(x) is characterized by: P_K(x) ∈ K and x - P_K(x) ⟂ K."

**Lean 4 Theorem**:
```lean
theorem orthogonalProjection_mem_subspace (K : Submodule 𝕜 E) [CompleteSpace K] (x : E) :
    orthogonalProjection K x ∈ K

theorem sub_orthogonalProjection_mem_orthogonal (K : Submodule 𝕜 E) [CompleteSpace K] (x : E) :
    x - orthogonalProjection K x ∈ Kᗮ
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Projection`
**Difficulty**: medium

---

### 2.8 Orthogonal Decomposition

**NL Statement**: "In a Hilbert space, every vector x decomposes uniquely as x = y + z where y ∈ K and z ∈ K⟂ for any closed subspace K."

**Lean 4 Theorem**:
```lean
theorem Submodule.exists_sum_mem_mem_orthogonal [CompleteSpace E]
    (K : Submodule 𝕜 E) [CompleteSpace K] (x : E) :
    ∃ y ∈ K, ∃ z ∈ Kᗮ, x = y + z
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Projection`
**Difficulty**: medium

---

### 2.9 Bessel's Inequality

**NL Statement**: "For an orthonormal family {eᵢ} and any vector x: Σᵢ |⟪x, eᵢ⟫|² ≤ ‖x‖²."

**Lean 4 Theorem**:
```lean
theorem Orthonormal.inner_left_finset_sum_le (hon : Orthonormal 𝕜 v) (x : E) (s : Finset ι) :
    ∑ i ∈ s, ‖⟪v i, x⟫_𝕜‖ ^ 2 ≤ ‖x‖ ^ 2
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Projection`
**Difficulty**: medium

---

### 2.10 Parseval's Identity

**NL Statement**: "For an orthonormal basis {eᵢ} of a Hilbert space: ‖x‖² = Σᵢ |⟪x, eᵢ⟫|² for all x."

**Lean 4 Theorem**:
```lean
theorem OrthonormalBasis.sum_inner_sq_eq_norm_sq (b : OrthonormalBasis ι 𝕜 E) (x : E) :
    ∑ i, ‖⟪b i, x⟫_𝕜‖ ^ 2 = ‖x‖ ^ 2
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Projection`
**Difficulty**: hard

---

## Part 3: Metric Space Theory

### 3.1 Metric Space Definition

**NL Statement**: "A metric space is a set X with distance function d: X × X → ℝ≥0 satisfying: d(x,y) = 0 ⟺ x = y, d(x,y) = d(y,x), and d(x,z) ≤ d(x,y) + d(y,z)."

**Lean 4 Definition**:
```lean
class MetricSpace (α : Type u) extends PseudoMetricSpace α where
  eq_of_dist_eq_zero : ∀ {x y : α}, dist x y = 0 → x = y
```

**Imports**: `Mathlib.Topology.MetricSpace.Basic`
**Difficulty**: medium

---

### 3.2 Metric Induces Topology

**NL Statement**: "Every metric space has a natural topology where open balls B(x,r) = {y | d(x,y) < r} form a basis."

**Lean 4 Theorem**:
```lean
theorem Metric.isOpen_ball {x : α} {r : ℝ} : IsOpen (Metric.ball x r)

theorem Metric.isTopologicalBasis_ball :
    IsTopologicalBasis { B | ∃ x r, B = Metric.ball x r }
```

**Imports**: `Mathlib.Topology.MetricSpace.Basic`
**Difficulty**: medium

---

### 3.3 Inner Product Space is Metric Space

**NL Statement**: "Every inner product space is a metric space with d(x,y) = ‖x - y‖."

**Lean 4 Instance**:
```lean
-- Automatic instance chain: InnerProductSpace → NormedSpace → MetricSpace
instance InnerProductSpace.toMetricSpace [InnerProductSpace 𝕜 E] : MetricSpace E
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: easy

---

### 3.4 Complete Metric Space

**NL Statement**: "A metric space is complete if every Cauchy sequence converges."

**Lean 4 Definition**:
```lean
class CompleteSpace (α : Type*) [UniformSpace α] : Prop where
  complete : ∀ f : Filter α, Cauchy f → ∃ x, f ≤ nhds x
```

**Imports**: `Mathlib.Topology.UniformSpace.Completion`
**Difficulty**: medium

---

### 3.5 Hilbert Space Completeness

**NL Statement**: "A Hilbert space is a complete inner product space."

**Lean 4 Instance**:
```lean
-- A Hilbert space: inner product space + complete
variable [InnerProductSpace 𝕜 E] [CompleteSpace E]
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Basic`
**Difficulty**: medium

---

### 3.6 Lipschitz Functions

**NL Statement**: "A function f: X → Y between metric spaces is Lipschitz with constant K ≥ 0 if d(f(x), f(y)) ≤ K · d(x, y) for all x, y."

**Lean 4 Definition**:
```lean
def LipschitzWith (K : ℝ≥0) (f : α → β) : Prop :=
  ∀ x y, dist (f x) (f y) ≤ K * dist x y
```

**Imports**: `Mathlib.Topology.MetricSpace.Lipschitz`
**Difficulty**: medium

---

### 3.7 Lipschitz Implies Uniform Continuity

**NL Statement**: "Every Lipschitz function is uniformly continuous."

**Lean 4 Theorem**:
```lean
theorem LipschitzWith.uniformContinuous (hf : LipschitzWith K f) : UniformContinuous f
```

**Imports**: `Mathlib.Topology.MetricSpace.Lipschitz`
**Difficulty**: easy

---

### 3.8 Isometry Definition

**NL Statement**: "An isometry is a distance-preserving map: d(f(x), f(y)) = d(x, y) for all x, y."

**Lean 4 Definition**:
```lean
def Isometry (f : α → β) : Prop := ∀ x y, dist (f x) (f y) = dist x y
```

**Imports**: `Mathlib.Topology.MetricSpace.Isometry`
**Difficulty**: easy

---

### 3.9 Isometry is Injective

**NL Statement**: "Every isometry is injective."

**Lean 4 Theorem**:
```lean
theorem Isometry.injective (h : Isometry f) : Function.Injective f
```

**Imports**: `Mathlib.Topology.MetricSpace.Isometry`
**Difficulty**: easy

---

### 3.10 Compact Metric Spaces

**NL Statement**: "A metric space is compact if and only if it is complete and totally bounded."

**Lean 4 Theorem**:
```lean
theorem Metric.compactSpace_iff_isCompact_univ :
    CompactSpace α ↔ IsCompact (Set.univ : Set α)

theorem isCompact_iff_totallyBounded_isComplete {s : Set α} :
    IsCompact s ↔ TotallyBounded s ∧ IsComplete s
```

**Imports**: `Mathlib.Topology.MetricSpace.Basic`
**Difficulty**: medium

---

## Part 4: Spectral Theory

### 4.1 Self-Adjoint Operator

**NL Statement**: "A linear operator T on an inner product space is self-adjoint if ⟪Tx, y⟫ = ⟪x, Ty⟫ for all x, y."

**Lean 4 Definition**:
```lean
def LinearMap.IsSelfAdjoint (T : E →ₗ[𝕜] E) : Prop :=
  ∀ x y, ⟪T x, y⟫_𝕜 = ⟪x, T y⟫_𝕜
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Adjoint`
**Difficulty**: medium

---

### 4.2 Self-Adjoint Eigenvalues are Real

**NL Statement**: "The eigenvalues of a self-adjoint operator are real."

**Lean 4 Theorem**:
```lean
theorem LinearMap.IsSymmetric.hasEigenvalue_isReal
    (hT : T.IsSymmetric) (hμ : Module.End.HasEigenvalue T μ) : μ.im = 0
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Spectrum`
**Difficulty**: medium

---

### 4.3 Orthogonality of Eigenspaces

**NL Statement**: "Eigenspaces of a self-adjoint operator corresponding to distinct eigenvalues are orthogonal."

**Lean 4 Theorem**:
```lean
theorem LinearMap.IsSymmetric.orthogonalFamily_eigenspaces (hT : T.IsSymmetric) :
    OrthogonalFamily 𝕜 (fun μ => eigenspace T μ) fun μ => (eigenspace T μ).subtypeₗᵢ
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Spectrum`
**Difficulty**: medium

---

### 4.4 Spectral Theorem (Finite Dimensional)

**NL Statement**: "Every self-adjoint operator on a finite-dimensional inner product space has an orthonormal basis of eigenvectors."

**Lean 4 Theorem**:
```lean
theorem LinearMap.IsSymmetric.eigenvectorBasis_apply [FiniteDimensional 𝕜 E]
    (hT : T.IsSymmetric) : ∃ (b : OrthonormalBasis (Fin n) 𝕜 E) (d : Fin n → ℝ),
    ∀ i, T (b i) = d i • b i
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Spectrum`
**Difficulty**: hard

---

### 4.5 Positive Operators

**NL Statement**: "A self-adjoint operator T is positive if ⟪Tx, x⟫ ≥ 0 for all x."

**Lean 4 Definition**:
```lean
def LinearMap.IsPositive (T : E →ₗ[𝕜] E) : Prop :=
  ∀ x, 0 ≤ re ⟪T x, x⟫_𝕜
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Positive`
**Difficulty**: medium

---

### 4.6 Positive Eigenvalues

**NL Statement**: "The eigenvalues of a positive operator are non-negative."

**Lean 4 Theorem**:
```lean
theorem LinearMap.IsPositive.eigenvalue_nonneg (hT : T.IsPositive)
    (hμ : Module.End.HasEigenvalue T μ) : 0 ≤ μ
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Spectrum`
**Difficulty**: medium

---

### 4.7 Riesz Representation Theorem

**NL Statement**: "Every continuous linear functional on a Hilbert space H has a unique representer: for each φ ∈ H*, there exists unique v ∈ H such that φ(x) = ⟪v, x⟫."

**Lean 4 Theorem**:
```lean
def InnerProductSpace.toDual [CompleteSpace E] : E ≃ₗᵢ⋆[𝕜] NormedSpace.Dual 𝕜 E :=
  { toFun := fun v => ⟨fun x => ⟪v, x⟫_𝕜, continuous_inner.comp continuous_const.prod_mk⟩
    ... }
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.Dual`
**Difficulty**: hard

---

### 4.8 Lax-Milgram Theorem

**NL Statement**: "For a coercive continuous bilinear form B on a Hilbert space and any f ∈ H*, there exists unique u ∈ H with B(u, v) = f(v) for all v."

**Lean 4 Theorem**:
```lean
-- IsCoercive condition: ∃ C > 0, ∀ u, C * ‖u‖² ≤ re (B u u)
theorem IsCoercive.unique_solution [CompleteSpace E] (hB : IsCoercive B)
    (f : E →L[𝕜] 𝕜) : ∃! u, ∀ v, B u v = f v
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.LaxMilgram`
**Difficulty**: hard

---

## Part 5: Riemannian Metric Foundations

### 5.1 Tangent Space

**NL Statement**: "The tangent space TₓM at a point x of a smooth manifold M is a vector space modeling infinitesimal directions from x."

**Lean 4 Definition**:
```lean
abbrev TangentSpace (I : ModelWithCorners 𝕜 E H) (x : M) : Type* := E
```

**Imports**: `Mathlib.Geometry.Manifold.VectorBundle.Tangent`
**Difficulty**: medium

---

### 5.2 Tangent Bundle

**NL Statement**: "The tangent bundle TM is the disjoint union of all tangent spaces: TM = ⊔ₓ TₓM, with natural smooth structure."

**Lean 4 Definition**:
```lean
abbrev TangentBundle (I : ModelWithCorners 𝕜 E H) (M : Type*) :=
  Bundle.TotalSpace E (TangentSpace I : M → Type*)
```

**Imports**: `Mathlib.Geometry.Manifold.VectorBundle.Tangent`
**Difficulty**: medium

---

### 5.3 Riemannian Metric (Conceptual)

**NL Statement**: "A Riemannian metric on a smooth manifold M is a smooth assignment x ↦ gₓ where each gₓ is an inner product on TₓM."

**Lean 4 Template** (NOT YET FORMALIZED):
```lean
-- Conceptual structure, not in Mathlib4
structure RiemannianMetric (I : ModelWithCorners ℝ E H) (M : Type*) [SmoothManifoldWithCorners I M] where
  metric : ∀ x : M, InnerProductSpace ℝ (TangentSpace I x)
  smooth : ContMDiff I (I.prod I) ⊤ (fun (v, w) => metric v.1 v.2 w.2)
```

**Status**: PARTIAL - Inner product spaces exist; metric on manifold not complete
**Imports**: `Mathlib.Geometry.Manifold.VectorBundle.Tangent`
**Difficulty**: very hard

---

### 5.4 Induced Distance

**NL Statement**: "A Riemannian metric induces a distance function d(x,y) = inf{L(γ) | γ connects x to y} where L is arc length."

**Lean 4 Template** (NOT YET FORMALIZED):
```lean
-- Conceptual: distance from metric via path length
def RiemannianMetric.dist (g : RiemannianMetric I M) (x y : M) : ℝ :=
  ⨅ (γ : Path x y), g.length γ
```

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 5.5 Length of a Curve

**NL Statement**: "The length of a piecewise smooth curve γ: [a,b] → M with respect to Riemannian metric g is L(γ) = ∫ₐᵇ √(g(γ'(t), γ'(t))) dt."

**Lean 4 Template** (NOT YET FORMALIZED):
```lean
-- Conceptual arc length integral
def RiemannianMetric.length (g : RiemannianMetric I M) (γ : Path x y) : ℝ :=
  ∫ t in (0:ℝ)..1, Real.sqrt (g.metric (γ t) (γ.deriv t) (γ.deriv t))
```

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 5.6 Euclidean Space as Riemannian Manifold

**NL Statement**: "Euclidean space ℝⁿ with the standard inner product is the prototypical Riemannian manifold with flat metric."

**Lean 4 Instance**:
```lean
instance : InnerProductSpace ℝ (EuclideanSpace ℝ (Fin n))
```

**Imports**: `Mathlib.Analysis.InnerProductSpace.PiL2`
**Difficulty**: easy

---

### 5.7 Sphere as Riemannian Manifold

**NL Statement**: "The unit sphere Sⁿ ⊂ ℝⁿ⁺¹ inherits a Riemannian metric from the ambient Euclidean space."

**Lean 4 Reference**:
```lean
-- Sphere inherits smooth manifold structure
instance : SmoothManifoldWithCorners (𝓡 n) (Sphere (0 : EuclideanSpace ℝ (Fin (n + 1))) 1)
```

**Imports**: `Mathlib.Geometry.Manifold.Instances.Sphere`
**Difficulty**: medium

---

### 5.8 Metric Compatibility (Conceptual)

**NL Statement**: "A connection ∇ is compatible with Riemannian metric g if X(g(Y,Z)) = g(∇ₓY, Z) + g(Y, ∇ₓZ) for all vector fields X, Y, Z."

**Status**: NOT FORMALIZED - Requires connection infrastructure
**Difficulty**: very hard

---

## Part 6: Curvature Concepts

### 6.1 Levi-Civita Connection (Conceptual)

**NL Statement**: "The Levi-Civita connection is the unique torsion-free connection compatible with the Riemannian metric."

**Lean 4 Template** (NOT YET FORMALIZED):
```lean
-- Conceptual: unique metric-compatible torsion-free connection
structure LeviCivitaConnection (g : RiemannianMetric I M) where
  conn : Connection I M
  torsion_free : ∀ X Y, conn X Y - conn Y X = LieBracket X Y
  metric_compatible : ∀ X Y Z, X (g Y Z) = g (conn X Y) Z + g Y (conn X Z)
```

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 6.2 Riemann Curvature Tensor (Conceptual)

**NL Statement**: "The Riemann curvature tensor R(X,Y)Z = ∇ₓ∇ᵧZ - ∇ᵧ∇ₓZ - ∇_{[X,Y]}Z measures the non-commutativity of covariant differentiation."

**Lean 4 Template** (NOT YET FORMALIZED):
```lean
-- Conceptual curvature operator
def RiemannCurvature (∇ : Connection I M) (X Y Z : VectorField I M) : VectorField I M :=
  ∇ X (∇ Y Z) - ∇ Y (∇ X Z) - ∇ (LieBracket X Y) Z
```

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 6.3 Curvature Tensor Symmetries (Conceptual)

**NL Statement**: "The Riemann tensor satisfies: (1) R(X,Y) = -R(Y,X), (2) g(R(X,Y)Z, W) = -g(R(X,Y)W, Z), (3) First Bianchi: R(X,Y)Z + R(Y,Z)X + R(Z,X)Y = 0."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 6.4 Sectional Curvature (Conceptual)

**NL Statement**: "The sectional curvature K(P) of a 2-plane P ⊂ TₓM spanned by orthonormal vectors u, v is K(P) = g(R(u,v)v, u)."

**Lean 4 Template** (NOT YET FORMALIZED):
```lean
-- Conceptual sectional curvature
def sectionalCurvature (g : RiemannianMetric I M) (x : M) (u v : TangentSpace I x)
    (hou : g.norm u = 1) (hov : g.norm v = 1) (horth : g.inner u v = 0) : ℝ :=
  g.inner (R g u v v) u
```

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 6.5 Ricci Curvature (Conceptual)

**NL Statement**: "The Ricci curvature Ric(X,Y) is the trace of the map Z ↦ R(Z,X)Y."

**Lean 4 Template** (NOT YET FORMALIZED):
```lean
-- Conceptual: Ricci as contraction of Riemann
def RicciCurvature (g : RiemannianMetric I M) (x : M) (X Y : TangentSpace I x) : ℝ :=
  ∑ i, g.inner (R g (e i) X Y) (e i)  -- where e is orthonormal basis
```

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 6.6 Scalar Curvature (Conceptual)

**NL Statement**: "The scalar curvature S = Σᵢ Ric(eᵢ, eᵢ) is the trace of the Ricci tensor."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 6.7 Constant Curvature Spaces

**NL Statement**: "A Riemannian manifold has constant curvature k if K(P) = k for all 2-planes P at all points. Examples: Sⁿ (k=1), ℝⁿ (k=0), Hⁿ (k=-1)."

**Status**: NOT FORMALIZED (specific examples may have ad-hoc proofs)
**Difficulty**: very hard

---

### 6.8 Einstein Manifolds (Conceptual)

**NL Statement**: "A Riemannian manifold is Einstein if Ric = λg for some constant λ."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 6.9 Flat Manifolds

**NL Statement**: "A Riemannian manifold is flat if R = 0, equivalently if it is locally isometric to Euclidean space."

**Status**: NOT FORMALIZED (Euclidean space has trivial curvature by construction)
**Difficulty**: hard

---

### 6.10 Gauss-Bonnet Formula (2D)

**NL Statement**: "For a compact oriented 2-manifold M: ∫_M K dA = 2π χ(M), relating total curvature to Euler characteristic."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

## Part 7: Geodesics and Exponential Map

### 7.1 Geodesic Definition (Conceptual)

**NL Statement**: "A geodesic is a curve γ(t) satisfying ∇_{γ'} γ' = 0, meaning the tangent vector is parallel transported along the curve."

**Lean 4 Template** (NOT YET FORMALIZED):
```lean
-- Conceptual: geodesic as autoparallel curve
def IsGeodesic (∇ : Connection I M) (γ : ℝ → M) : Prop :=
  ∀ t, ∇ (γ.deriv t) (γ.deriv) = 0
```

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 7.2 Geodesic Equation

**NL Statement**: "In local coordinates, geodesics satisfy γ̈ᵏ + Γᵏᵢⱼ γ̇ⁱ γ̇ʲ = 0 where Γ are Christoffel symbols."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 7.3 Geodesic Uniqueness

**NL Statement**: "Given a point p and tangent vector v ∈ TₚM, there exists a unique maximal geodesic γ with γ(0) = p and γ'(0) = v."

**Status**: NOT FORMALIZED (would follow from ODE theory)
**Difficulty**: very hard

---

### 7.4 Exponential Map (Conceptual)

**NL Statement**: "The exponential map expₚ : TₚM → M sends v to γᵥ(1) where γᵥ is the geodesic with γ(0) = p, γ'(0) = v."

**Lean 4 Template** (NOT YET FORMALIZED):
```lean
-- Conceptual exponential map
def expMap (g : RiemannianMetric I M) (p : M) (v : TangentSpace I p) : M :=
  geodesic g p v 1
```

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 7.5 Exponential Map is Local Diffeomorphism

**NL Statement**: "The exponential map is a local diffeomorphism near the origin: there exists r > 0 such that expₚ : B(0,r) → M is a diffeomorphism onto its image."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 7.6 Geodesic Completeness (Conceptual)

**NL Statement**: "A Riemannian manifold is geodesically complete if every geodesic can be extended to all of ℝ."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 7.7 Normal Coordinates

**NL Statement**: "Normal coordinates at p are defined via expₚ: the coordinate of expₚ(v) is v. In these coordinates, Christoffel symbols vanish at p."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 7.8 Geodesics Minimize Length Locally

**NL Statement**: "Every geodesic is locally length-minimizing: for sufficiently small ε, γ|_{[0,ε]} minimizes length among curves from γ(0) to γ(ε)."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

## Part 8: Classical Riemannian Theorems

### 8.1 Hopf-Rinow Theorem (Conceptual)

**NL Statement**: "For a connected Riemannian manifold, the following are equivalent: (1) Metrically complete, (2) Geodesically complete, (3) Closed bounded sets are compact, (4) expₚ is defined on all of TₚM for some p."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 8.2 Cartan-Hadamard Theorem (Conceptual)

**NL Statement**: "A simply connected complete Riemannian manifold with non-positive sectional curvature is diffeomorphic to ℝⁿ via the exponential map."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 8.3 Bonnet-Myers Theorem (Conceptual)

**NL Statement**: "If a complete Riemannian manifold has Ricci curvature Ric ≥ (n-1)k for some k > 0, then its diameter is at most π/√k and the fundamental group is finite."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 8.4 Synge's Theorem (Conceptual)

**NL Statement**: "An even-dimensional orientable compact Riemannian manifold with positive sectional curvature is simply connected."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 8.5 Hadamard's Theorem (Surfaces)

**NL Statement**: "A complete simply connected surface with non-positive Gaussian curvature is diffeomorphic to ℝ²."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 8.6 Myers' Diameter Theorem (Conceptual)

**NL Statement**: "If Ric ≥ (n-1)k > 0 on a complete manifold, then diam(M) ≤ π/√k."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 8.7 Cheeger's Inequality (Conceptual)

**NL Statement**: "For compact Riemannian manifolds, the first eigenvalue of the Laplacian satisfies λ₁ ≥ h²/4 where h is the Cheeger isoperimetric constant."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 8.8 Comparison Theorems (Conceptual)

**NL Statement**: "Rauch, Toponogov, and Bishop-Gromov comparison theorems relate geometric quantities (Jacobi fields, triangles, volumes) to model spaces of constant curvature."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 8.9 Nash Embedding Theorem

**NL Statement**: "Every Riemannian manifold can be isometrically embedded into some Euclidean space ℝᴺ."

**Status**: NOT FORMALIZED (deep result requiring hard analysis)
**Difficulty**: very hard

---

## Standard Setup

**Lean 4 Imports**:
```lean
import Mathlib.Analysis.InnerProductSpace.Basic
import Mathlib.Analysis.InnerProductSpace.Dual
import Mathlib.Analysis.InnerProductSpace.Projection
import Mathlib.Analysis.InnerProductSpace.Spectrum
import Mathlib.Analysis.InnerProductSpace.Orthogonal.Basic
import Mathlib.Topology.MetricSpace.Basic
import Mathlib.Topology.MetricSpace.Isometry
import Mathlib.Topology.MetricSpace.Lipschitz
import Mathlib.Geometry.Manifold.VectorBundle.Tangent
import Mathlib.Geometry.Manifold.Instances.Sphere

variable {𝕜 : Type*} [RCLike 𝕜]
variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace 𝕜 E]
variable {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F]
variable {α : Type*} [MetricSpace α]
```

---

## Notation Reference

| Math Notation | Lean 4 Notation | Description |
|---------------|-----------------|-------------|
| ⟪x, y⟫ | `inner x y` or `⟪x, y⟫_𝕜` | Inner product |
| ‖x‖ | `norm x` or `‖x‖` | Norm |
| d(x, y) | `dist x y` | Distance |
| K⟂ | `Kᗮ` | Orthogonal complement |
| TₓM | `TangentSpace I x` | Tangent space at x |
| TM | `TangentBundle I M` | Tangent bundle |

---

## Sources

- [Mathlib.Analysis.InnerProductSpace.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/InnerProductSpace/Basic.html)
- [Mathlib.Analysis.InnerProductSpace.Projection](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/InnerProductSpace/Projection.html)
- [Mathlib.Analysis.InnerProductSpace.Spectrum](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/InnerProductSpace/Spectrum.html)
- [Mathlib.Topology.MetricSpace.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Topology/MetricSpace/Basic.html)
- [Mathlib.Geometry.Manifold.VectorBundle.Tangent](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/VectorBundle/Tangent.html)
- [Ved Datar's Riemannian Geometry Lectures](https://math.iisc.ac.in/~vvdatar/Lecture_Notes/RG_Lectures_typesett_published.pdf)
- [David Tong's General Relativity Notes - Riemannian Geometry](https://www.damtp.cam.ac.uk/user/tong/gr/grhtml/S3.html)
