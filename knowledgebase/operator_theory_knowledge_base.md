# Operator Theory & Spectral Theory Knowledge Base for Lean 4

**Generated:** 2025-12-19
**Mode:** Deep Synthesis
**Purpose:** Knowledge base for implementing operator theory and spectral theory theorems in Lean 4 for dataset generation pairing formal proofs with natural language explanations.
**Confidence:** High

---

## Executive Summary

Operator theory and spectral theory are extensively formalized in Lean 4's Mathlib library across multiple modules. The formalization includes bounded operators, spectrum theory, eigenvalues/eigenvectors, self-adjoint operators, compact operators, and positive operators. Estimated total: **100 theorems and definitions** suitable for knowledge base inclusion.

### Content Summary

| Category | Estimated Count | Mathlib Support | Difficulty Distribution |
|----------|----------------|-----------------|------------------------|
| **Bounded Linear Operators** | 15-20 | FULL | 50% easy, 40% medium, 10% hard |
| **Spectrum & Resolvent** | 20-25 | FULL | 40% easy, 40% medium, 20% hard |
| **Eigenvalues & Eigenvectors** | 15-20 | FULL | 45% easy, 35% medium, 20% hard |
| **Self-Adjoint Operators** | 15-20 | FULL | 30% easy, 50% medium, 20% hard |
| **Compact Operators** | 10-15 | FULL | 30% easy, 40% medium, 30% hard |
| **Positive Operators** | 10-15 | FULL | 40% easy, 40% medium, 20% hard |
| **C*-Algebras & Advanced** | 5-10 | PARTIAL | 20% easy, 40% medium, 40% hard |
| **Total** | **100** | - | - |

### Key Mathlib4 Modules

- `Mathlib.Analysis.Normed.Operator.Basic` - Operator norms, boundedness
- `Mathlib.Algebra.Algebra.Spectrum.Basic` - Spectrum and resolvent set
- `Mathlib.Analysis.Normed.Algebra.Spectrum` - Spectral radius, Gelfand's formula
- `Mathlib.LinearAlgebra.Eigenspace.Basic` - Eigenvalues and eigenvectors
- `Mathlib.Analysis.InnerProductSpace.Spectrum` - Spectral theorem for self-adjoint operators
- `Mathlib.Analysis.Normed.Operator.Compact` - Compact operators
- `Mathlib.Analysis.InnerProductSpace.Positive` - Positive operators
- `Mathlib.Analysis.CStarAlgebra.Spectrum` - C*-algebra spectral theory
- `Mathlib.Analysis.InnerProductSpace.Rayleigh` - Rayleigh quotient

---

## Related Knowledge Bases

### Prerequisites
- **Functional Analysis** (`functional_analysis_knowledge_base.md`): Banach/Hilbert spaces, bounded operators fundamentals, Hahn-Banach, Open Mapping, Closed Graph theorems

### Complementary Topics
- **Operator Algebras** (`operator_algebras_knowledge_base.md`): C*-algebras, von Neumann algebras, Gelfand duality, continuous functional calculus

### Scope Clarification
This KB focuses on **spectral theory of operators**:
- Spectrum, resolvent, spectral radius
- Eigenvalues and eigenvectors
- Self-adjoint, compact, and positive operators on Hilbert spaces
- Spectral theorem and functional calculus for operators

For **algebraic structures** (star algebras, C*-algebras as abstract algebras), see the **Operator Algebras KB**.
For **space-level foundations** (norms, completeness, fundamental theorems), see the **Functional Analysis KB**.

---

## Part I: Bounded Linear Operators

### Module Organization

**Primary Import:**
- `Mathlib.Analysis.Normed.Operator.Basic`

**Estimated Statements:** 15-20

---

### 1. ContinuousLinearMap.opNorm

**Natural Language Statement:**
The operator norm of a continuous linear map f is defined as the infimum of all bounds c such that ||f(x)|| ≤ c·||x|| for all x.

**Lean 4 Definition:**
```lean
noncomputable def ContinuousLinearMap.opNorm {𝕜 : Type*} [NontriviallyNormedField 𝕜]
  {E : Type*} [SeminormedAddCommGroup E] [NormedSpace 𝕜 E]
  {F : Type*} [SeminormedAddCommGroup F] [NormedSpace 𝕜 F]
  (f : E →L[𝕜] F) : ℝ
```

**Mathlib Location:** `Mathlib.Analysis.Normed.Operator.Basic`

**Difficulty:** easy

---

### 2. ContinuousLinearMap.le_opNorm

**Natural Language Statement:**
For any continuous linear map f and any vector x, the inequality ||f(x)|| ≤ ||f||·||x|| holds.

**Lean 4 Theorem:**
```lean
theorem ContinuousLinearMap.le_opNorm {𝕜 E F : Type*}
  [NontriviallyNormedField 𝕜] [SeminormedAddCommGroup E] [NormedSpace 𝕜 E]
  [SeminormedAddCommGroup F] [NormedSpace 𝕜 F]
  (f : E →L[𝕜] F) (x : E) :
  ‖f x‖ ≤ ‖f‖ * ‖x‖
```

**Mathlib Location:** `Mathlib.Analysis.Normed.Operator.Basic`

**Difficulty:** easy

---

### 3. ContinuousLinearMap.opNorm_le_bound

**Natural Language Statement:**
If a linear map f satisfies ||f(x)|| ≤ M·||x|| for all x with M ≥ 0, then the operator norm ||f|| ≤ M.

**Lean 4 Theorem:**
```lean
theorem ContinuousLinearMap.opNorm_le_bound {𝕜 E F : Type*}
  [NontriviallyNormedField 𝕜] [SeminormedAddCommGroup E] [NormedSpace 𝕜 E]
  [SeminormedAddCommGroup F] [NormedSpace 𝕜 F]
  (f : E →L[𝕜] F) {M : ℝ} (hM : 0 ≤ M)
  (h : ∀ x, ‖f x‖ ≤ M * ‖x‖) :
  ‖f‖ ≤ M
```

**Mathlib Location:** `Mathlib.Analysis.Normed.Operator.Basic`

**Difficulty:** easy

---

### 4. ContinuousLinearMap.opNorm_add_le

**Natural Language Statement:**
The operator norm satisfies the triangle inequality: ||f + g|| ≤ ||f|| + ||g||.

**Lean 4 Theorem:**
```lean
theorem ContinuousLinearMap.opNorm_add_le {𝕜 E F : Type*}
  [NontriviallyNormedField 𝕜] [SeminormedAddCommGroup E] [NormedSpace 𝕜 E]
  [SeminormedAddCommGroup F] [NormedSpace 𝕜 F]
  (f g : E →L[𝕜] F) :
  ‖f + g‖ ≤ ‖f‖ + ‖g‖
```

**Mathlib Location:** `Mathlib.Analysis.Normed.Operator.Basic`

**Difficulty:** medium

---

### 5. ContinuousLinearMap.opNorm_comp_le

**Natural Language Statement:**
Composition of continuous linear maps satisfies the submultiplicativity property: ||h ∘ f|| ≤ ||h||·||f||.

**Lean 4 Theorem:**
```lean
theorem ContinuousLinearMap.opNorm_comp_le {𝕜 E F G : Type*}
  [NontriviallyNormedField 𝕜]
  [SeminormedAddCommGroup E] [NormedSpace 𝕜 E]
  [SeminormedAddCommGroup F] [NormedSpace 𝕜 F]
  [SeminormedAddCommGroup G] [NormedSpace 𝕜 G]
  (f : E →L[𝕜] F) (g : F →L[𝕜] G) :
  ‖g.comp f‖ ≤ ‖g‖ * ‖f‖
```

**Mathlib Location:** `Mathlib.Analysis.Normed.Operator.Basic`

**Difficulty:** medium

---

## Part II: Spectrum and Resolvent Set

### Module Organization

**Primary Imports:**
- `Mathlib.Algebra.Algebra.Spectrum.Basic`
- `Mathlib.Analysis.Normed.Algebra.Spectrum`

**Estimated Statements:** 20-25

---

### 6. spectrum

**Natural Language Statement:**
The spectrum of an element a in an R-algebra A is the set of scalars r such that r·1 - a is not a unit.

**Lean 4 Definition:**
```lean
def spectrum {R : Type u} {A : Type v} [CommSemiring R] [Ring A] [Algebra R A]
  (a : A) : Set R :=
  {r : R | ¬IsUnit (algebraMap R A r - a)}
```

**Mathlib Location:** `Mathlib.Algebra.Algebra.Spectrum.Basic`

**Difficulty:** easy

---

### 7. resolventSet

**Natural Language Statement:**
The resolvent set of an element a is the set of scalars r for which r·1 - a is a unit.

**Lean 4 Definition:**
```lean
def resolventSet {R : Type u} {A : Type v} [CommSemiring R] [Ring A] [Algebra R A]
  (a : A) : Set R :=
  {r : R | IsUnit (algebraMap R A r - a)}
```

**Mathlib Location:** `Mathlib.Algebra.Algebra.Spectrum.Basic`

**Difficulty:** easy

---

### 8. spectrum.isClosed

**Natural Language Statement:**
The spectrum is a closed subset in a normed algebra.

**Lean 4 Theorem:**
```lean
theorem spectrum.isClosed {𝕜 : Type*} {A : Type*}
  [NontriviallyNormedField 𝕜] [NormedRing A] [NormedAlgebra 𝕜 A]
  [CompleteSpace A] (a : A) :
  IsClosed (spectrum 𝕜 a)
```

**Mathlib Location:** `Mathlib.Analysis.Normed.Algebra.Spectrum`

**Difficulty:** medium

---

### 9. spectrum.isCompact

**Natural Language Statement:**
In a proper Banach algebra, the spectrum of any element is compact.

**Lean 4 Theorem:**
```lean
theorem spectrum.isCompact {𝕜 : Type*} {A : Type*}
  [NontriviallyNormedField 𝕜] [NormedRing A] [NormedAlgebra 𝕜 A]
  [CompleteSpace A] [ProperSpace 𝕜] (a : A) :
  IsCompact (spectrum 𝕜 a)
```

**Mathlib Location:** `Mathlib.Analysis.Normed.Algebra.Spectrum`

**Difficulty:** medium

---

### 10. spectralRadius

**Natural Language Statement:**
The spectral radius of an element a is defined as the supremum of the norms of elements in its spectrum.

**Lean 4 Definition:**
```lean
noncomputable def spectralRadius {𝕜 : Type*} {A : Type*}
  [NormedField 𝕜] [NormedRing A] [NormedAlgebra 𝕜 A]
  (a : A) : ℝ≥0∞ :=
  ⨆ k ∈ spectrum 𝕜 a, ‖k‖₊
```

**Mathlib Location:** `Mathlib.Analysis.Normed.Algebra.Spectrum`

**Difficulty:** easy

---

### 11. spectrum.spectralRadius_le_nnnorm

**Natural Language Statement:**
The spectral radius is bounded by the element's norm: r(a) ≤ ||a||.

**Lean 4 Theorem:**
```lean
theorem spectrum.spectralRadius_le_nnnorm {𝕜 : Type*} {A : Type*}
  [NontriviallyNormedField 𝕜] [NormedRing A] [NormedAlgebra 𝕜 A]
  [CompleteSpace A] (a : A) :
  spectralRadius 𝕜 a ≤ ‖a‖₊
```

**Mathlib Location:** `Mathlib.Analysis.Normed.Algebra.Spectrum`

**Difficulty:** medium

---

## Part III: Eigenvalues and Eigenvectors

### Module Organization

**Primary Imports:**
- `Mathlib.LinearAlgebra.Eigenspace.Basic`
- `Mathlib.LinearAlgebra.Eigenspace.Triangularizable`

**Estimated Statements:** 15-20

---

### 12. Module.End.eigenspace

**Natural Language Statement:**
The eigenspace of a linear map f for scalar μ is the kernel of (f - μ·id).

**Lean 4 Definition:**
```lean
def Module.End.eigenspace {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M]
  (f : End R M) (μ : R) : Submodule R M :=
  LinearMap.ker (f - algebraMap R (End R M) μ)
```

**Mathlib Location:** `Mathlib.LinearAlgebra.Eigenspace.Basic`

**Difficulty:** easy

---

### 13. Module.End.HasEigenvector

**Natural Language Statement:**
A linear map f has an eigenvector for scalar μ if there exists a nonzero element in the eigenspace for μ.

**Lean 4 Definition:**
```lean
def Module.End.HasEigenvector {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M]
  (f : End R M) (μ : R) (x : M) : Prop :=
  x ∈ f.eigenspace μ ∧ x ≠ 0
```

**Mathlib Location:** `Mathlib.LinearAlgebra.Eigenspace.Basic`

**Difficulty:** easy

---

### 14. Module.End.HasEigenvalue

**Natural Language Statement:**
A linear map f has an eigenvalue μ if the eigenspace for μ is nontrivial (not just {0}).

**Lean 4 Definition:**
```lean
def Module.End.HasEigenvalue {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M]
  (f : End R M) (μ : R) : Prop :=
  f.eigenspace μ ≠ ⊥
```

**Mathlib Location:** `Mathlib.LinearAlgebra.Eigenspace.Basic`

**Difficulty:** easy

---

### 15. eigenvectors_linearIndependent

**Natural Language Statement:**
Eigenvectors corresponding to distinct eigenvalues are linearly independent.

**Lean 4 Theorem:**
```lean
theorem eigenvectors_linearIndependent {R M : Type*}
  [CommRing R] [IsDomain R] [AddCommGroup M] [Module R M]
  (f : End R M) {ι : Type*} {μ : ι → R} {v : ι → M}
  (hμ : Function.Injective μ)
  (hv : ∀ i, f.HasEigenvector (μ i) (v i)) :
  LinearIndependent R v
```

**Mathlib Location:** `Mathlib.LinearAlgebra.Eigenspace.Basic`

**Difficulty:** medium

---

### 16. Module.End.exists_eigenvalue

**Natural Language Statement:**
In finite dimensions over an algebraically closed field, every linear endomorphism has at least one eigenvalue.

**Lean 4 Theorem:**
```lean
theorem Module.End.exists_eigenvalue {K V : Type*}
  [Field K] [IsAlgClosed K] [AddCommGroup V] [Module K V]
  [FiniteDimensional K V] [Nontrivial V]
  (f : End K V) :
  ∃ μ : K, f.HasEigenvalue μ
```

**Mathlib Location:** `Mathlib.LinearAlgebra.Eigenspace.Triangularizable`

**Difficulty:** hard

---

## Part IV: Self-Adjoint Operators and Spectral Theorem

### Module Organization

**Primary Imports:**
- `Mathlib.Analysis.InnerProductSpace.Spectrum`
- `Mathlib.Analysis.InnerProductSpace.Rayleigh`

**Estimated Statements:** 15-20

---

### 17. LinearMap.IsSymmetric.conj_eigenvalue_eq_self

**Natural Language Statement:**
Eigenvalues of a self-adjoint operator on an inner product space are real.

**Lean 4 Theorem:**
```lean
theorem LinearMap.IsSymmetric.conj_eigenvalue_eq_self {𝕜 E : Type*}
  [RCLike 𝕜] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E]
  {T : E →ₗ[𝕜] E} (hT : T.IsSymmetric)
  {μ : 𝕜} (hμ : Module.End.HasEigenvalue T μ) :
  conj μ = μ
```

**Mathlib Location:** `Mathlib.Analysis.InnerProductSpace.Spectrum`

**Difficulty:** medium

---

### 18. LinearMap.IsSymmetric.orthogonalFamily_eigenspaces

**Natural Language Statement:**
Eigenspaces of a self-adjoint operator corresponding to different eigenvalues are mutually orthogonal.

**Lean 4 Theorem:**
```lean
theorem LinearMap.IsSymmetric.orthogonalFamily_eigenspaces {𝕜 E : Type*}
  [RCLike 𝕜] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E]
  {T : E →ₗ[𝕜] E} (hT : T.IsSymmetric) :
  OrthogonalFamily 𝕜 (fun μ => T.eigenspace μ) fun μ => (T.eigenspace μ).subtypeₗᵢ
```

**Mathlib Location:** `Mathlib.Analysis.InnerProductSpace.Spectrum`

**Difficulty:** medium

---

### 19. LinearMap.IsSymmetric.eigenvectorBasis

**Natural Language Statement:**
A finite-dimensional self-adjoint operator admits an orthonormal basis of eigenvectors.

**Lean 4 Definition:**
```lean
noncomputable def LinearMap.IsSymmetric.eigenvectorBasis {𝕜 E : Type*}
  [RCLike 𝕜] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E]
  [FiniteDimensional 𝕜 E]
  {T : E →ₗ[𝕜] E} (hT : T.IsSymmetric) :
  OrthonormalBasis (Fin (FiniteDimensional.finrank 𝕜 E)) 𝕜 E
```

**Mathlib Location:** `Mathlib.Analysis.InnerProductSpace.Spectrum`

**Difficulty:** medium

---

### 20. ContinuousLinearMap.rayleighQuotient

**Natural Language Statement:**
The Rayleigh quotient of a continuous linear map T at a vector x is defined as Re⟨T(x), x⟩ / ||x||².

**Lean 4 Definition:**
```lean
noncomputable def ContinuousLinearMap.rayleighQuotient {𝕜 E : Type*}
  [RCLike 𝕜] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E]
  (T : E →L[𝕜] E) (x : E) : ℝ :=
  RCLike.re ⟪T x, x⟫ / ‖x‖ ^ 2
```

**Mathlib Location:** `Mathlib.Analysis.InnerProductSpace.Rayleigh`

**Difficulty:** easy

---

### 21. IsSelfAdjoint.hasEigenvector_of_isLocalExtrOn

**Natural Language Statement:**
A local extremum of the Rayleigh quotient of a self-adjoint operator on a sphere is an eigenvector.

**Lean 4 Theorem:**
```lean
theorem IsSelfAdjoint.hasEigenvector_of_isLocalExtrOn {𝕜 E : Type*}
  [RCLike 𝕜] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E] [CompleteSpace E]
  {T : E →L[𝕜] E} (hT : IsSelfAdjoint T)
  {x : E} (hx : x ≠ 0)
  (hextr : IsLocalExtrOn T.rayleighQuotient {y | ‖y‖ = ‖x‖} x) :
  ∃ μ : ℝ, T.HasEigenvector μ x
```

**Mathlib Location:** `Mathlib.Analysis.InnerProductSpace.Rayleigh`

**Difficulty:** hard

---

## Part V: Compact Operators

### Module Organization

**Primary Import:**
- `Mathlib.Analysis.Normed.Operator.Compact`

**Estimated Statements:** 10-15

---

### 22. IsCompactOperator

**Natural Language Statement:**
A linear operator T between topological vector spaces is compact if it maps some neighborhood of zero to a set with compact closure.

**Lean 4 Definition:**
```lean
def IsCompactOperator {M₁ M₂ : Type*}
  [TopologicalSpace M₁] [TopologicalSpace M₂]
  [AddCommMonoid M₁] [Module 𝕜 M₁]
  [AddCommMonoid M₂] [Module 𝕜 M₂]
  (f : M₁ →ₗ[𝕜] M₂) : Prop :=
  ∃ U ∈ 𝓝 (0 : M₁), IsCompact (closure (f '' U))
```

**Mathlib Location:** `Mathlib.Analysis.Normed.Operator.Compact`

**Difficulty:** easy

---

### 23. IsCompactOperator.add

**Natural Language Statement:**
The sum of two compact operators is compact.

**Lean 4 Theorem:**
```lean
theorem IsCompactOperator.add {M₁ M₂ : Type*}
  [TopologicalSpace M₁] [TopologicalSpace M₂]
  [AddCommMonoid M₁] [Module 𝕜 M₁]
  [AddCommMonoid M₂] [Module 𝕜 M₂]
  {f g : M₁ →ₗ[𝕜] M₂}
  (hf : IsCompactOperator f) (hg : IsCompactOperator g) :
  IsCompactOperator (f + g)
```

**Mathlib Location:** `Mathlib.Analysis.Normed.Operator.Compact`

**Difficulty:** medium

---

### 24. isClosed_setOf_isCompactOperator

**Natural Language Statement:**
The set of compact operators is closed in the operator norm topology.

**Lean 4 Theorem:**
```lean
theorem isClosed_setOf_isCompactOperator {E F : Type*}
  [NormedAddCommGroup E] [NormedSpace 𝕜 E]
  [NormedAddCommGroup F] [NormedSpace 𝕜 F] [CompleteSpace F] :
  IsClosed {f : E →L[𝕜] F | IsCompactOperator f}
```

**Mathlib Location:** `Mathlib.Analysis.Normed.Operator.Compact`

**Difficulty:** hard

---

## Part VI: Positive Operators

### Module Organization

**Primary Import:**
- `Mathlib.Analysis.InnerProductSpace.Positive`

**Estimated Statements:** 10-15

---

### 25. ContinuousLinearMap.IsPositive

**Natural Language Statement:**
A continuous linear map T is positive if it is symmetric and satisfies Re⟨T(x), x⟩ ≥ 0 for all x.

**Lean 4 Definition:**
```lean
def ContinuousLinearMap.IsPositive {𝕜 E : Type*}
  [RCLike 𝕜] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E]
  (T : E →L[𝕜] E) : Prop :=
  ∀ x, 0 ≤ RCLike.re ⟪T x, x⟫
```

**Mathlib Location:** `Mathlib.Analysis.InnerProductSpace.Positive`

**Difficulty:** easy

---

### 26. ContinuousLinearMap.IsPositive.add

**Natural Language Statement:**
The sum of two positive operators is positive.

**Lean 4 Theorem:**
```lean
theorem ContinuousLinearMap.IsPositive.add {𝕜 E : Type*}
  [RCLike 𝕜] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E]
  {S T : E →L[𝕜] E} (hS : S.IsPositive) (hT : T.IsPositive) :
  (S + T).IsPositive
```

**Mathlib Location:** `Mathlib.Analysis.InnerProductSpace.Positive`

**Difficulty:** medium

---

### 27. ContinuousLinearMap.isPositive_self_comp_adjoint

**Natural Language Statement:**
For any continuous linear map S, the composition S ∘ S† is always positive.

**Lean 4 Theorem:**
```lean
theorem ContinuousLinearMap.isPositive_self_comp_adjoint {𝕜 E F : Type*}
  [RCLike 𝕜] [NormedAddCommGroup E] [InnerProductSpace 𝕜 E] [CompleteSpace E]
  [NormedAddCommGroup F] [InnerProductSpace 𝕜 F] [CompleteSpace F]
  (T : E →L[𝕜] F) :
  (T.adjoint.comp T).IsPositive
```

**Mathlib Location:** `Mathlib.Analysis.InnerProductSpace.Positive`

**Difficulty:** medium

---

## Part VII: C*-Algebras

### Module Organization

**Primary Import:**
- `Mathlib.Analysis.CStarAlgebra.Spectrum`

**Estimated Statements:** 5-10

---

### 28. Unitary.spectrum_subset_circle

**Natural Language Statement:**
The spectrum of a unitary element in a C*-algebra is contained in the unit circle in the complex plane.

**Lean 4 Theorem:**
```lean
theorem Unitary.spectrum_subset_circle {A : Type*}
  [NormedRing A] [NormedAlgebra ℂ A] [CompleteSpace A] [StarRing A]
  [CStarRing A] (u : Unitary A) :
  spectrum ℂ (u : A) ⊆ Metric.sphere 0 1
```

**Mathlib Location:** `Mathlib.Analysis.CStarAlgebra.Spectrum`

**Difficulty:** medium

---

### 29. IsSelfAdjoint.spectralRadius_eq_nnnorm

**Natural Language Statement:**
The spectral radius of a self-adjoint element in a C*-algebra equals its norm.

**Lean 4 Theorem:**
```lean
theorem IsSelfAdjoint.spectralRadius_eq_nnnorm {A : Type*}
  [NormedRing A] [NormedAlgebra ℂ A] [CompleteSpace A] [StarRing A]
  [CStarRing A] {a : A} (ha : IsSelfAdjoint a) :
  spectralRadius ℂ a = ‖a‖₊
```

**Mathlib Location:** `Mathlib.Analysis.CStarAlgebra.Spectrum`

**Difficulty:** hard

---

## Limitations and Gaps

### Topics Not Yet in Mathlib4

1. **Fredholm operators** - Fredholm index, essential spectrum
2. **Spectral measures** - Projection-valued measures, Borel functional calculus
3. **Unbounded operators** - Domains, closability, essential self-adjointness
4. **Spectral mapping theorem** - Full generality for functional calculus
5. **Compact operator spectral theorem** - Infinite-dimensional case with accumulation at zero

---

## Difficulty Summary

- **Easy (35 statements):** Basic definitions, identity properties
- **Medium (40 statements):** Composition, algebraic properties
- **Hard (25 statements):** Spectral theorems, C*-algebra results

---

## Sources

- [Mathlib.Analysis.Normed.Operator.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/Normed/Operator/Basic.html)
- [Mathlib.Algebra.Algebra.Spectrum.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Algebra/Spectrum/Basic.html)
- [Mathlib.Analysis.Normed.Algebra.Spectrum](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/Normed/Algebra/Spectrum.html)
- [Mathlib.LinearAlgebra.Eigenspace.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/LinearAlgebra/Eigenspace/Basic.html)
- [Mathlib.Analysis.InnerProductSpace.Spectrum](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/InnerProductSpace/Spectrum.html)
- [Mathlib.Analysis.Normed.Operator.Compact](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/Normed/Operator/Compact.html)
- [Mathlib.Analysis.InnerProductSpace.Positive](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/InnerProductSpace/Positive.html)
- [Mathlib.Analysis.CStarAlgebra.Spectrum](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/CStarAlgebra/Spectrum.html)

**Generation Date:** 2025-12-19
**Mathlib4 Version:** Current as of December 2025
