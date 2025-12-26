# Complex Geometry Knowledge Base

## Overview

**Domain:** Complex Geometry / Analysis
**Mathlib4 Coverage:** Good for complex analysis, partial for complex manifolds
**Measurability Score:** 50/100

Complex geometry studies complex manifolds—manifolds with holomorphic transition functions. Mathlib4 has excellent formalization of complex analysis (Cauchy integral, analyticity, maximum modulus) and foundational complex manifold theory (holomorphic functions, compactness results). Kähler geometry, complex differential forms, and advanced structures remain unformalized.

---

## Related Knowledge Bases

### Prerequisites
- **Real/Complex Analysis** (`real_complex_analysis_knowledge_base.md`): Complex analysis, holomorphic functions
- **Smooth Manifolds** (`smooth_manifolds_knowledge_base.md`): Manifold infrastructure
- **Topology** (`topology_knowledge_base.md`): Topological foundations

### Builds Upon This KB
- **Algebraic Geometry** (`algebraic_geometry_knowledge_base.md`): Connections via GAGA

### Related Topics
- **Differential Geometry** (`differential_geometry_knowledge_base.md`): Riemannian aspects of Kähler geometry
- **Fiber Bundles** (`fiber_bundles_knowledge_base.md`): Holomorphic bundles
- **Lie Theory** (`lie_theory_knowledge_base.md`): Complex Lie groups

### Scope Clarification
This KB focuses on **complex geometry**:
- Complex numbers and analysis basics
- Holomorphic functions on complex manifolds
- Complex manifold structure
- Cauchy integral theory
- Maximum modulus principle
- (Gaps: Kähler geometry, complex differential forms)

For **algebraic-geometric aspects**, see **Algebraic Geometry KB**.

---

## Part I: Complex Numbers and Analysis Basics

### Section 1.1: Complex Field Structure

#### Definition 1.1.1: Complex Numbers as Normed Field
**Natural Language:** ℂ is a complete normed field extending ℝ.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Complex.Basic
instance : NormedField ℂ := ...
instance : CompleteSpace ℂ := ...
```

#### Theorem 1.1.2: Real-Complex Equivalence
**Natural Language:** ℂ is linearly isomorphic to ℝ² as a real vector space.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Complex.Basic
/-- ℂ is equivalent to ℝ × ℝ as topological vector spaces. -/
def Complex.equivRealProdCLM : ℂ ≃L[ℝ] ℝ × ℝ
```

#### Theorem 1.1.3: Real and Imaginary Parts
**Natural Language:** The real and imaginary parts are continuous linear projections.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Complex.Basic
/-- Real part as continuous linear map. -/
def Complex.reCLM : ℂ →L[ℝ] ℝ

/-- Imaginary part as continuous linear map. -/
def Complex.imCLM : ℂ →L[ℝ] ℝ
```

#### Theorem 1.1.4: Complex Conjugation
**Natural Language:** Conjugation is a continuous linear isometry.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Complex.Basic
/-- Complex conjugation as a linear isometry equivalence. -/
def Complex.conjLIE : ℂ ≃ₗᵢ[ℝ] ℂ

/-- Continuous linear equivalence version. -/
def Complex.conjCLE : ℂ ≃L[ℝ] ℂ
```

#### Theorem 1.1.5: Only Continuous Automorphisms
**Natural Language:** The only continuous ring automorphisms of ℂ are identity and conjugation.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Complex.Basic
theorem Complex.ringEquiv_eq_id_or_conj (e : ℂ ≃+* ℂ) (he : Continuous e) :
    e = RingEquiv.refl ℂ ∨ e = starRingEquiv
```

### Section 1.2: Slit Plane and Logarithm

#### Definition 1.2.1: Slit Plane
**Natural Language:** The slit plane is ℂ minus the closed negative real axis.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Complex.Basic
/-- The complex plane with negative real axis removed. -/
def Complex.slitPlane : Set ℂ := {z | 0 < z.re ∨ z.im ≠ 0}
```

#### Theorem 1.2.2: Slit Plane Properties
**Natural Language:** The open unit ball around 1 is contained in the slit plane.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Complex.Basic
theorem Complex.ball_one_subset_slitPlane : Metric.ball 1 1 ⊆ slitPlane

theorem Complex.slitPlane_ne_zero {z : ℂ} (hz : z ∈ slitPlane) : z ≠ 0
```

---

## Part II: Complex Differentiability

### Section 2.1: Holomorphic Functions

#### Definition 2.1.1: Complex Differentiability
**Natural Language:** f : ℂ → ℂ is complex differentiable at z if the limit (f(z+h) - f(z))/h exists.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Calculus.FDeriv.Basic (complex case)
/-- f is complex differentiable at z. -/
def DifferentiableAt (f : ℂ → ℂ) (z : ℂ) : Prop :=
  ∃ f' : ℂ →L[ℂ] ℂ, HasFDerivAt f f' z
```

#### Theorem 2.1.2: Cauchy-Riemann Equations
**Natural Language:** f = u + iv is holomorphic iff ∂u/∂x = ∂v/∂y and ∂u/∂y = -∂v/∂x.
**Difficulty:** medium

```lean4
-- Follows from ℂ-linear Fréchet derivative
-- A ℂ-linear map ℂ → ℂ is multiplication by a complex number
theorem Complex.hasFDerivAt_iff_exists_complex_deriv {f : ℂ → ℂ} {z : ℂ} {f' : ℂ →L[ℂ] ℂ} :
    HasFDerivAt f f' z ↔ ∃ c : ℂ, f' = c • ContinuousLinearMap.id ℂ ℂ
```

### Section 2.2: Analytic Functions

#### Definition 2.2.1: Analytic Function
**Natural Language:** f is analytic on S if it equals a convergent power series in a neighborhood of each point.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Analytic.Basic
/-- f is analytic at a point. -/
def AnalyticAt (f : ℂ → ℂ) (z : ℂ) : Prop :=
  ∃ p : FormalMultilinearSeries ℂ ℂ ℂ, HasFPowerSeriesAt f p z
```

#### Theorem 2.2.2: Holomorphic Implies Analytic
**Natural Language:** On open sets, differentiable functions are analytic.
**Difficulty:** hard

```lean4
-- Mathlib.Analysis.Complex.CauchyIntegral
theorem DifferentiableOn.analyticAt {f : ℂ → ℂ} {s : Set ℂ} (hf : DifferentiableOn ℂ f s)
    {z : ℂ} (hz : s ∈ 𝓝 z) : AnalyticAt ℂ f z
```

#### Theorem 2.2.3: Analytic Iff Differentiable
**Natural Language:** For open sets, analyticity and differentiability are equivalent.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Complex.CauchyIntegral
theorem analyticAt_iff_differentiableAt {f : ℂ → ℂ} {z : ℂ} :
    AnalyticAt ℂ f z ↔ ∃ s ∈ 𝓝 z, DifferentiableOn ℂ f s
```

---

## Part III: Cauchy Integral Theory

### Section 3.1: Cauchy-Goursat Theorem

#### Theorem 3.1.1: Cauchy-Goursat for Rectangles
**Natural Language:** The integral of a holomorphic function over a rectangle boundary is zero.
**Difficulty:** hard

```lean4
-- Mathlib.Analysis.Complex.CauchyIntegral
/-- Integral over rectangle boundary vanishes for differentiable functions. -/
theorem Complex.integral_boundary_rect_eq_zero {f : ℂ → ℂ} {z w : ℂ}
    (hf : DifferentiableOn ℂ f (Set.Icc z.re w.re ×ˢ Set.Icc z.im w.im)) :
    ∮ ζ in C(z, w), f ζ = 0
```

#### Theorem 3.1.2: Cauchy-Goursat for Annulus
**Natural Language:** For a function differentiable on an annulus, integrals over both boundary circles are equal.
**Difficulty:** hard

```lean4
-- Mathlib.Analysis.Complex.CauchyIntegral
theorem circleIntegral_eq_of_differentiableOn_annulus {f : ℂ → ℂ} {c : ℂ} {r₁ r₂ : ℝ}
    (hr : r₁ ≤ r₂) (hf : DifferentiableOn ℂ f (Metric.closedBall c r₂ \ Metric.ball c r₁)) :
    ∮ z in C(c, r₂), f z = ∮ z in C(c, r₁), f z
```

### Section 3.2: Cauchy Integral Formula

#### Theorem 3.2.1: Cauchy Integral Formula
**Natural Language:** For w inside a circle: f(w) = (1/2πi) ∮ f(z)/(z-w) dz.
**Difficulty:** hard

```lean4
-- Mathlib.Analysis.Complex.CauchyIntegral
theorem Complex.two_pi_I_inv_smul_circleIntegral_sub_inv_smul_of_differentiable_on_off_countable
    {f : ℂ → ℂ} {c : ℂ} {R : ℝ} (hR : 0 < R) {w : ℂ} (hw : w ∈ Metric.ball c R)
    (hf : DifferentiableOn ℂ f (Metric.closedBall c R)) :
    (2 * π * I)⁻¹ • ∮ z in C(c, R), (z - w)⁻¹ • f z = f w
```

#### Theorem 3.2.2: Higher Derivative Formula
**Natural Language:** f^(n)(w) = n!/(2πi) ∮ f(z)/(z-w)^{n+1} dz.
**Difficulty:** hard

```lean4
-- Mathlib.Analysis.Complex.CauchyIntegral
theorem Complex.hasFPowerSeriesOnBall_of_differentiable_off_countable {f : ℂ → ℂ} {c : ℂ} {R : ℝ}
    (hf : DifferentiableOn ℂ f (Metric.closedBall c R)) :
    HasFPowerSeriesOnBall f (cauchyPowerSeries f c R) c (ENNReal.ofReal R)
```

---

## Part IV: Classical Complex Analysis Theorems

### Section 4.1: Maximum Modulus

#### Theorem 4.1.1: Maximum Modulus Principle (Local)
**Natural Language:** If |f| has a local maximum at an interior point, f is locally constant.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Complex.AbsMax
theorem Complex.norm_eventually_eq_of_isLocalMax {f : ℂ → ℂ} {z : ℂ}
    (hf : DifferentiableAt ℂ f z) (hz : IsLocalMax (norm ∘ f) z) :
    ∀ᶠ w in 𝓝 z, ‖f w‖ = ‖f z‖
```

#### Theorem 4.1.2: Maximum Modulus Principle (Connected)
**Natural Language:** On a connected open set, if |f| attains its maximum, f is constant.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Complex.AbsMax
theorem DifferentiableOn.norm_eqOn_of_isPreconnected_of_isMaxOn {f : ℂ → ℂ} {s : Set ℂ}
    (hf : DifferentiableOn ℂ f s) (hs : IsPreconnected s) (ho : IsOpen s)
    {w : ℂ} (hw : w ∈ s) (hmax : IsMaxOn (norm ∘ f) s w) : ∀ z ∈ s, ‖f z‖ = ‖f w‖
```

### Section 4.2: Liouville and Identity

#### Theorem 4.2.1: Liouville's Theorem
**Natural Language:** A bounded entire function is constant.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Complex.Liouville
theorem Differentiable.apply_eq_apply_of_bounded {f : ℂ → ℂ} (hf : Differentiable ℂ f)
    (hbdd : IsBounded (Set.range f)) (z w : ℂ) : f z = f w
```

#### Theorem 4.2.2: Identity Theorem
**Natural Language:** If two holomorphic functions agree on a set with accumulation point, they are equal.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Analytic.IsolatedZeros
theorem AnalyticAt.eventually_eq_of_frequently_eq {f g : ℂ → ℂ} {z : ℂ}
    (hf : AnalyticAt ℂ f z) (hg : AnalyticAt ℂ g z)
    (h : ∃ᶠ w in 𝓝[≠] z, f w = g w) : f =ᶠ[𝓝 z] g
```

### Section 4.3: Schwarz Lemma

#### Theorem 4.3.1: Schwarz Lemma
**Natural Language:** For f : 𝔻 → 𝔻 holomorphic with f(0) = 0, |f(z)| ≤ |z| and |f'(0)| ≤ 1.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Complex.Schwarz
theorem Complex.abs_deriv_le_one_of_mapsTo_ball {f : ℂ → ℂ} (hf : DifferentiableAt ℂ f 0)
    (h : Set.MapsTo f (Metric.ball 0 1) (Metric.ball 0 1)) (h0 : f 0 = 0) :
    ‖deriv f 0‖ ≤ 1
```

---

## Part V: Complex Manifolds

### Section 5.1: Complex Manifold Structure

#### Definition 5.1.1: Complex Manifold via mdifferentiable
**Natural Language:** A complex manifold has charts to ℂⁿ with holomorphic transition functions.
**Difficulty:** medium

```lean4
-- Mathlib.Geometry.Manifold.Complex (using smooth manifold infrastructure)
-- Complex manifolds use I = 𝓘(ℂ) or 𝓘(ℂ, E) for model
-- mdifferentiable captures holomorphicity

/-- f is holomorphic between complex manifolds. -/
def MDifferentiable (f : M → N) : Prop :=
  ∀ x, MDifferentiableAt I I' f x
```

#### Theorem 5.1.2: Holomorphic Functions on Compact Manifolds
**Natural Language:** A holomorphic function on a compact complex manifold is locally constant.
**Difficulty:** hard

```lean4
-- Mathlib.Geometry.Manifold.Complex
theorem MDifferentiable.isLocallyConstant {M : Type*} [TopologicalSpace M] [ChartedSpace ℂ M]
    [SmoothManifoldWithCorners 𝓘(ℂ) M] [CompactSpace M]
    {f : M → ℂ} (hf : MDifferentiable 𝓘(ℂ) 𝓘(ℂ) f) : IsLocallyConstant f
```

#### Theorem 5.1.3: Holomorphic = Constant on Compact Connected
**Natural Language:** A holomorphic function on a compact connected complex manifold is constant.
**Difficulty:** hard

```lean4
-- Mathlib.Geometry.Manifold.Complex
theorem MDifferentiable.apply_eq_of_compactSpace {M : Type*} [TopologicalSpace M]
    [ChartedSpace ℂ M] [SmoothManifoldWithCorners 𝓘(ℂ) M]
    [CompactSpace M] [PreconnectedSpace M]
    {f : M → ℂ} (hf : MDifferentiable 𝓘(ℂ) 𝓘(ℂ) f) (x y : M) : f x = f y
```

### Section 5.2: Maximum Modulus on Manifolds

#### Theorem 5.2.1: Maximum Modulus for Complex Manifolds
**Natural Language:** If a holomorphic function's norm has a local max at a point, the norm is locally constant.
**Difficulty:** hard

```lean4
-- Mathlib.Geometry.Manifold.Complex
theorem Complex.norm_eventually_eq_of_mdifferentiableAt_of_isLocalMax {M : Type*}
    [TopologicalSpace M] [ChartedSpace ℂ M] [SmoothManifoldWithCorners 𝓘(ℂ) M]
    {f : M → ℂ} {x : M} (hf : MDifferentiableAt 𝓘(ℂ) 𝓘(ℂ) f x)
    (hmax : IsLocalMax (norm ∘ f) x) : ∀ᶠ y in 𝓝 x, ‖f y‖ = ‖f x‖
```

---

## Part VI: Kähler Geometry (Templates)

> **Note:** Kähler geometry is NOT YET FORMALIZED in Mathlib4.

### Section 6.1: Almost Complex Structures

#### Definition 6.1.1: Almost Complex Structure (TEMPLATE)
**Natural Language:** An almost complex structure J on M is an endomorphism with J² = -Id.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Almost complex structure
/-- An almost complex structure on a real vector bundle. -/
structure AlmostComplexStructure (M : Type*) [SmoothManifoldWithCorners 𝓘(ℝ, E) M] where
  J : ∀ x : M, TangentSpace 𝓘(ℝ, E) x →L[ℝ] TangentSpace 𝓘(ℝ, E) x
  J_sq_neg : ∀ x, J x ∘L J x = -ContinuousLinearMap.id ℝ _
```

#### Theorem 6.1.2: Integrability via Nijenhuis Tensor (TEMPLATE)
**Natural Language:** J is integrable (comes from complex structure) iff Nijenhuis tensor N_J = 0.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Newlander-Nirenberg theorem
def nijenhuisTensor (J : AlmostComplexStructure M) : ... := ...

theorem newlander_nirenberg {J : AlmostComplexStructure M} :
    (∃ (atlas : ComplexAtlas M), J = atlas.inducedJ) ↔ nijenhuisTensor J = 0
```

### Section 6.2: Kähler Manifolds

#### Definition 6.2.1: Hermitian Metric (TEMPLATE)
**Natural Language:** A Hermitian metric h on a complex manifold satisfies h(Jv, Jw) = h(v, w).
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Hermitian metric
/-- A Hermitian metric on a complex manifold. -/
structure HermitianMetric (M : ComplexManifold) where
  metric : ∀ x, TangentSpace x →L[ℝ] TangentSpace x →L[ℝ] ℝ
  symmetric : ∀ x v w, metric x v w = metric x w v
  positive : ∀ x v, v ≠ 0 → 0 < metric x v v
  J_invariant : ∀ x v w, metric x (J v) (J w) = metric x v w
```

#### Definition 6.2.2: Kähler Form (TEMPLATE)
**Natural Language:** The Kähler form ω(v, w) = h(Jv, w) is a closed (1,1)-form.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Kähler form
noncomputable def kaehlerForm (h : HermitianMetric M) : DifferentialForm M 2 :=
  fun x v w => h.metric x (J v) w
```

#### Definition 6.2.3: Kähler Manifold (TEMPLATE)
**Natural Language:** (M, h) is Kähler if the Kähler form is closed: dω = 0.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Kähler manifold
structure KaehlerManifold extends ComplexManifold where
  hermitianMetric : HermitianMetric toComplexManifold
  kaehler_closed : d (kaehlerForm hermitianMetric) = 0
```

#### Theorem 6.2.4: Kähler Potential (TEMPLATE)
**Natural Language:** Locally, ω = i∂∂̄φ for some real function φ (the Kähler potential).
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Kähler potential
theorem kaehler_potential_exists (M : KaehlerManifold) (x : M) :
    ∃ (U : Set M) (hU : IsOpen U) (hx : x ∈ U) (φ : U → ℝ),
      kaehlerForm M.hermitianMetric.restrict U = i * ∂ ∂̄ φ
```

---

## Part VII: Hodge Theory (Templates)

### Section 7.1: Dolbeault Cohomology

#### Definition 7.1.1: (p,q)-Forms (TEMPLATE)
**Natural Language:** A (p,q)-form has p holomorphic and q antiholomorphic indices.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - (p,q)-forms
/-- The space of (p,q)-forms on a complex manifold. -/
def DolbeaultForm (M : ComplexManifold) (p q : ℕ) : Type* := ...
```

#### Definition 7.1.2: Dolbeault Operators (TEMPLATE)
**Natural Language:** ∂ : Ωᵖ'ᵍ → Ωᵖ⁺¹'ᵍ and ∂̄ : Ωᵖ'ᵍ → Ωᵖ'ᵍ⁺¹ with d = ∂ + ∂̄.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Dolbeault operators
def dolbeault_del : DolbeaultForm M p q →L[ℂ] DolbeaultForm M (p+1) q := ...
def dolbeault_delbar : DolbeaultForm M p q →L[ℂ] DolbeaultForm M p (q+1) := ...

theorem d_eq_del_add_delbar : d = dolbeault_del + dolbeault_delbar
```

#### Theorem 7.1.3: ∂̄∂̄ = 0 (TEMPLATE)
**Natural Language:** The Dolbeault operator squares to zero.
**Difficulty:** easy
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB
theorem dolbeault_delbar_sq_zero : dolbeault_delbar ∘ dolbeault_delbar = 0
```

### Section 7.2: Hodge Decomposition

#### Theorem 7.2.1: Hodge Decomposition for Kähler (TEMPLATE)
**Natural Language:** On a compact Kähler manifold, Hᵏ(M, ℂ) = ⊕_{p+q=k} Hᵖ'ᵍ(M).
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Hodge decomposition
theorem hodge_decomposition (M : CompactKaehlerManifold) (k : ℕ) :
    deRhamCohomology M k ℂ ≃ₗ[ℂ] ⨁ p q : ℕ, (p + q = k) → dolbeaultCohomology M p q
```

---

## Part VIII: Riemann Surfaces and Uniformization (Templates)

### Section 8.1: Riemann Surfaces

#### Definition 8.1.1: Riemann Surface (TEMPLATE)
**Natural Language:** A Riemann surface is a 1-dimensional complex manifold.
**Difficulty:** medium
**Status:** PARTIALLY FORMALIZED (as 1-dim complex manifold)

```lean4
-- Can be defined via ChartedSpace ℂ
/-- A Riemann surface is a connected 1-dimensional complex manifold. -/
structure RiemannSurface extends ChartedSpace ℂ, SmoothManifoldWithCorners 𝓘(ℂ) where
  connected : PreconnectedSpace toType
```

#### Theorem 8.1.2: Genus and Euler Characteristic (TEMPLATE)
**Natural Language:** For a compact Riemann surface: χ(M) = 2 - 2g where g is the genus.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Euler characteristic
theorem euler_characteristic_genus (M : CompactRiemannSurface) :
    M.eulerCharacteristic = 2 - 2 * M.genus
```

### Section 8.2: Uniformization

#### Theorem 8.2.1: Uniformization Theorem (TEMPLATE)
**Natural Language:** Every simply connected Riemann surface is biholomorphic to ℂ̂, ℂ, or 𝔻.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Uniformization theorem
theorem uniformization (M : SimplyConnectedRiemannSurface) :
    (Biholomorphic M riemannSphere) ∨ (Biholomorphic M ℂ) ∨ (Biholomorphic M unitDisc)
```

---

## Dependencies

- **Internal:** `real_complex_analysis` (complex analysis), `smooth_manifolds` (manifold structure), `differential_geometry` (tangent bundles)
- **Mathlib4:** `Mathlib.Analysis.Complex.*`, `Mathlib.Geometry.Manifold.Complex`, `Mathlib.Analysis.Analytic.*`

## Notes for Autoformalization

1. **Complex analysis excellent:** Cauchy integral, analyticity, maximum modulus fully formalized
2. **Complex manifolds:** Basic holomorphicity via mdifferentiable, compactness results
3. **Kähler gap:** No Hermitian metrics, Kähler forms, or Hodge theory
4. **Almost complex:** Not formalized, needed for Kähler
5. **Riemann surfaces:** Can model as 1D complex manifolds
6. **Build on:** Analysis.Complex.*, Geometry.Manifold.*

---

## Summary Statistics

- **Total Statements:** 50
- **Formalized (with Lean4):** 25 (50%)
- **Templates (NOT FORMALIZED):** 25 (50%)
- **Difficulty Distribution:** Easy: 10, Medium: 24, Hard: 16
