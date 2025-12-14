# Real and Complex Analysis Knowledge Base for Lean 4

**Generated:** 2025-12-14
**Purpose:** Research knowledge base for implementing real and complex analysis in Lean 4 for dataset generation pairing formal proofs with natural language explanations.

---

## Overview

Real and complex analysis form the theoretical foundation for calculus, providing rigorous treatment of limits, derivatives, integrals, and analytic functions. This knowledge base catalogs core theorems from both fields as formalized in Lean 4's Mathlib.

### Content Summary

| Category | Count | Description |
|----------|-------|-------------|
| **Sequences & Series** | 6 | Convergence, limits, geometric series |
| **Continuity** | 4 | Epsilon-delta, uniform continuity |
| **Differentiation** | 7 | Derivatives, chain rule, MVT |
| **Integration** | 5 | FTC, substitution, integration by parts |
| **Complex Analysis** | 8 | Holomorphic functions, Cauchy theory |
| **Total** | 30 | Core theorems |

### Mathlib Approach

Mathlib uses filter-based definitions as the primary framework, with traditional epsilon-delta characterizations provided as theorems. Integration uses the measure-theoretic Bochner integral:

```lean
-- Filter-based limit definition
def Filter.Tendsto (f : α → β) (l₁ : Filter α) (l₂ : Filter β) : Prop :=
  Filter.map f l₁ ≤ l₂

-- Derivative via Fréchet differentiation
def HasDerivAt (f : 𝕜 → F) (f' : F) (x : 𝕜) : Prop :=
  HasFDerivAt f (ContinuousLinearMap.smulRight 1 f') x
```

**Primary Imports:** `Mathlib.Analysis.Calculus.Deriv.Basic`, `Mathlib.MeasureTheory.Integral.IntervalIntegral`

---

## Part I: Real Analysis

### 1. Convergence of Sequences

**Natural Language Statement:**
A sequence (aₙ) converges to limit L if for every ε > 0, there exists N such that for all n > N, |aₙ - L| < ε. Using filters, this is expressed as tendsto at_top (𝓝 L).

**Lean 4 Definition:**
```lean
-- Sequence convergence via filters
def Filter.Tendsto (f : ℕ → ℝ) (l : Filter ℝ) : Prop :=
  map f atTop ≤ l

-- Example: 1/n → 0
theorem tendsto_inverse_atTop_nhds_zero_nat :
  Tendsto (fun n : ℕ => (n : ℝ)⁻¹) atTop (𝓝 0)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.SpecificLimits.Basic`

**Key Theorems:**
```lean
-- Power sequences
theorem tendsto_pow_atTop_nhds_zero_of_norm_lt_one {r : 𝕜} (h : ‖r‖ < 1) :
  Tendsto (fun n => r ^ n) atTop (𝓝 0)

-- Uniqueness of limits (in Hausdorff spaces)
theorem tendsto_nhds_unique [T2Space α] {f : β → α} {l : Filter β} [l.NeBot]
  {a b : α} (ha : Tendsto f l (𝓝 a)) (hb : Tendsto f l (𝓝 b)) : a = b
```

**Difficulty:** easy

---

### 2. Geometric Series

**Natural Language Statement:**
For |r| < 1, the geometric series Σ rⁿ converges to 1/(1-r).

**Lean 4 Theorem:**
```lean
theorem hasSum_geometric_of_norm_lt_one {r : 𝕜} (h : ‖r‖ < 1) :
  HasSum (fun n : ℕ => r ^ n) (1 - r)⁻¹

theorem tsum_geometric_of_norm_lt_one {r : 𝕜} (h : ‖r‖ < 1) :
  ∑' n : ℕ, r ^ n = (1 - r)⁻¹
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.SpecificLimits.Normed`

**Difficulty:** easy

---

### 3. Epsilon-Delta Continuity

**Natural Language Statement:**
A function f: ℝ → ℝ is continuous at x₀ if for every ε > 0, there exists δ > 0 such that |x - x₀| < δ implies |f(x) - f(x₀)| < ε.

**Lean 4 Characterization:**
```lean
theorem Metric.continuous_iff {f : α → β} [MetricSpace α] [MetricSpace β] :
  Continuous f ↔ ∀ x, ∀ ε > 0, ∃ δ > 0, ∀ y, dist y x < δ → dist (f y) (f x) < ε

-- For real functions specifically
theorem continuous_iff_forall_epsilon_delta {f : ℝ → ℝ} :
  Continuous f ↔ ∀ x, ∀ ε > 0, ∃ δ > 0, ∀ y, |y - x| < δ → |f y - f x| < ε
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.MetricSpace.Basic`

**Difficulty:** easy

---

### 4. Uniform Continuity

**Natural Language Statement:**
A function f is uniformly continuous if for every ε > 0, there exists δ > 0 such that for ALL x, y with |x - y| < δ, we have |f(x) - f(y)| < ε. The key difference from pointwise continuity is that δ depends only on ε.

**Lean 4 Definition:**
```lean
def UniformContinuous {α β : Type*} [UniformSpace α] [UniformSpace β]
  (f : α → β) : Prop :=
  ∀ ⦃U : Set (β × β)⦄, U ∈ uniformity β →
    {p : α × α | (f p.1, f p.2) ∈ U} ∈ uniformity α
```

**Key Theorem (Heine-Cantor):**
```lean
theorem IsCompact.uniformContinuousOn_of_continuous {f : α → β}
  {s : Set α} (hs : IsCompact s) (hf : ContinuousOn f s) :
  UniformContinuousOn f s
```
*Continuous functions on compact sets are uniformly continuous*

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.UniformSpace.Basic`

**Difficulty:** medium

---

### 5. Intermediate Value Theorem

**100 Theorems List:** #79

**Natural Language Statement:**
If f is continuous on [a, b] and y is between f(a) and f(b), then there exists c ∈ [a, b] such that f(c) = y.

**Lean 4 Theorem:**
```lean
theorem IsPreconnected.intermediate_value {s : Set X} (hs : IsPreconnected s)
  {a b : X} (ha : a ∈ s) (hb : b ∈ s) {f : X → α} (hf : ContinuousOn f s) :
  Set.Icc (f a) (f b) ⊆ f '' s

-- Interval version
theorem intermediate_value_Icc {f : ℝ → ℝ} {a b : ℝ} (hab : a ≤ b)
  (hf : ContinuousOn f (Set.Icc a b)) :
  Set.Icc (f a) (f b) ⊆ f '' Set.Icc a b
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Order.IntermediateValue`

**Difficulty:** medium

---

### 6. Derivative Definition

**Natural Language Statement:**
The derivative of f at x is the limit of (f(x+h) - f(x))/h as h → 0, denoted f'(x). A function is differentiable at x if this limit exists.

**Lean 4 Definition:**
```lean
-- HasDerivAt: f has derivative f' at point x
def HasDerivAt (f : 𝕜 → F) (f' : F) (x : 𝕜) : Prop :=
  HasFDerivAt f (ContinuousLinearMap.smulRight 1 f') x

-- deriv: returns derivative value (0 if not differentiable)
noncomputable def deriv (f : 𝕜 → F) (x : 𝕜) : F :=
  fderiv 𝕜 f x 1

-- Differentiability implies continuity
theorem HasDerivAt.continuousAt {f : 𝕜 → F} (h : HasDerivAt f f' x) :
  ContinuousAt f x
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.Calculus.Deriv.Basic`

**Difficulty:** easy

---

### 7. Chain Rule

**Natural Language Statement:**
If g is differentiable at x and f is differentiable at g(x), then (f ∘ g)'(x) = f'(g(x)) · g'(x).

**Lean 4 Theorem:**
```lean
theorem HasDerivAt.comp {g : 𝕜 → 𝕜'} {f : 𝕜' → 𝕜'}
  (hf : HasDerivAt f f' (g x)) (hg : HasDerivAt g g' x) :
  HasDerivAt (f ∘ g) (f' * g') x

theorem deriv_comp {g : 𝕜 → 𝕜'} {f : 𝕜' → 𝕜'}
  (hf : DifferentiableAt 𝕜' f (g x)) (hg : DifferentiableAt 𝕜 g x) :
  deriv (f ∘ g) x = deriv f (g x) * deriv g x
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.Calculus.Deriv.Comp`

**Difficulty:** easy

---

### 8. Mean Value Theorem

**100 Theorems List:** #75

**Natural Language Statement:**
If f is continuous on [a, b] and differentiable on (a, b), there exists c ∈ (a, b) such that f'(c) = (f(b) - f(a))/(b - a).

**Lean 4 Theorem:**
```lean
theorem exists_hasDerivAt_eq_slope {f : ℝ → ℝ} {a b : ℝ} (hab : a < b)
  (hf : ContinuousOn f (Set.Icc a b))
  (hf' : ∀ x ∈ Set.Ioo a b, DifferentiableAt ℝ f x) :
  ∃ c ∈ Set.Ioo a b, deriv f c = (f b - f a) / (b - a)

-- Cauchy's generalized MVT
theorem exists_ratio_hasDerivAt_eq_ratio_slope {f g : ℝ → ℝ} {a b : ℝ} (hab : a < b)
  (hfc : ContinuousOn f (Set.Icc a b)) (hgc : ContinuousOn g (Set.Icc a b))
  (hf' : ∀ x ∈ Set.Ioo a b, DifferentiableAt ℝ f x)
  (hg' : ∀ x ∈ Set.Ioo a b, DifferentiableAt ℝ g x) :
  ∃ c ∈ Set.Ioo a b, (g b - g a) * deriv f c = (f b - f a) * deriv g c
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.Calculus.Deriv.MeanValue`

**Difficulty:** medium

---

### 9. Rolle's Theorem

**Natural Language Statement:**
If f is continuous on [a, b], differentiable on (a, b), and f(a) = f(b), then there exists c ∈ (a, b) such that f'(c) = 0.

**Lean 4 Theorem:**
```lean
theorem exists_hasDerivAt_eq_zero {f : ℝ → ℝ} {a b : ℝ} (hab : a < b)
  (hf : ContinuousOn f (Set.Icc a b))
  (hf' : ∀ x ∈ Set.Ioo a b, DifferentiableAt ℝ f x)
  (hfa : f a = f b) :
  ∃ c ∈ Set.Ioo a b, deriv f c = 0
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.Calculus.Deriv.MeanValue`

**Difficulty:** medium

---

### 10. Taylor's Theorem

**100 Theorems List:** #35

**Natural Language Statement:**
If f is n-times continuously differentiable, then f(x) equals its Taylor polynomial of degree n at x₀ plus a remainder term that is O((x - x₀)^(n+1)).

**Lean 4 Theorems:**
```lean
-- Little-o form
theorem taylor_isLittleO {f : ℝ → E} {x₀ : ℝ} {n : ℕ} {s : Set ℝ}
  (hs : Convex ℝ s) (hx₀s : x₀ ∈ s) (hf : ContDiffOn ℝ n f s) :
  (fun x => f x - taylorWithinEval f n s x₀ x) =o[𝓝[s] x₀] fun x => (x - x₀) ^ n

-- Lagrange remainder form
theorem taylor_mean_remainder_lagrange {f : ℝ → ℝ} {x x₀ : ℝ} {n : ℕ}
  (hx : x₀ < x) (hf : ContDiffOn ℝ n f (Set.Icc x₀ x))
  (hf' : DifferentiableOn ℝ (iteratedDerivWithin n f (Set.Icc x₀ x)) (Set.Ioo x₀ x)) :
  ∃ x' ∈ Set.Ioo x₀ x,
    f x - taylorWithinEval f n (Set.Icc x₀ x) x₀ x =
    iteratedDerivWithin (n + 1) f (Set.Icc x₀ x) x' * (x - x₀) ^ (n + 1) / (n + 1).factorial
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.Calculus.Taylor`

**Difficulty:** hard

---

### 11. Fundamental Theorem of Calculus (Part 1)

**100 Theorems List:** #15

**Natural Language Statement:**
If f is continuous at b, then the function F(x) = ∫ₐˣ f(t)dt is differentiable at b with F'(b) = f(b).

**Lean 4 Theorem:**
```lean
theorem integral_hasStrictDerivAt_right {f : ℝ → E} {a b : ℝ}
  (hf : IntervalIntegrable f volume a b)
  (hmeas : StronglyMeasurableAtFilter f (𝓝 b))
  (hb : Tendsto f (𝓝 b) (𝓝 c)) :
  HasStrictDerivAt (fun u => ∫ x in a..u, f x) c b
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.MeasureTheory.Integral.IntervalIntegral.FundThmCalculus`

**Difficulty:** hard

---

### 12. Fundamental Theorem of Calculus (Part 2)

**Natural Language Statement:**
If F is an antiderivative of f on [a, b] (meaning F' = f), then ∫ₐᵇ f(x)dx = F(b) - F(a).

**Lean 4 Theorem:**
```lean
theorem integral_eq_sub_of_hasDerivAt {f f' : ℝ → ℝ} {a b : ℝ}
  (hf : ContinuousOn f (Set.uIcc a b))
  (hf' : ∀ x ∈ Set.Ioo (min a b) (max a b), HasDerivAt f (f' x) x)
  (hf'_int : IntervalIntegrable f' volume a b) :
  ∫ x in a..b, f' x = f b - f a

-- Using deriv
theorem integral_deriv_eq_sub {f : ℝ → ℝ} {a b : ℝ}
  (hf : ContinuousOn f (Set.uIcc a b))
  (hf' : DifferentiableOn ℝ f (Set.Ioo (min a b) (max a b)))
  (hf'_int : IntervalIntegrable (deriv f) volume a b) :
  ∫ x in a..b, deriv f x = f b - f a
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.MeasureTheory.Integral.IntervalIntegral.FundThmCalculus`

**Difficulty:** hard

---

### 13. Integration by Parts

**Natural Language Statement:**
If u and v are differentiable functions with integrable derivatives, then ∫ u dv = uv - ∫ v du.

**Lean 4 Theorem:**
```lean
theorem integral_mul_deriv_eq_deriv_mul {u v : ℝ → ℝ} {a b : ℝ}
  (hu : ∀ x ∈ Set.uIcc a b, HasDerivAt u (u' x) x)
  (hv : ∀ x ∈ Set.uIcc a b, HasDerivAt v (v' x) x)
  (hu' : IntervalIntegrable u' volume a b)
  (hv' : IntervalIntegrable v' volume a b) :
  ∫ x in a..b, u x * v' x = u b * v b - u a * v a - ∫ x in a..b, u' x * v x
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.MeasureTheory.Integral.IntervalIntegral`

**Difficulty:** medium

---

### 14. L'Hôpital's Rule

**100 Theorems List:** #64

**Natural Language Statement:**
If f(a) = g(a) = 0 and lim f'(x)/g'(x) = L as x → a, then lim f(x)/g(x) = L as x → a.

**Lean 4 Theorem:**
```lean
theorem Filter.Tendsto.lhopital_zero_nhds {f g f' g' : ℝ → ℝ} {a L : ℝ}
  (hf : Tendsto f (𝓝 a) (𝓝 0))
  (hg : Tendsto g (𝓝 a) (𝓝 0))
  (hf' : ∀ᶠ x in 𝓝[≠] a, HasDerivAt f (f' x) x)
  (hg' : ∀ᶠ x in 𝓝[≠] a, HasDerivAt g (g' x) x)
  (hg'ne : ∀ᶠ x in 𝓝[≠] a, g' x ≠ 0)
  (hfg : Tendsto (fun x => f' x / g' x) (𝓝[≠] a) (𝓝 L)) :
  Tendsto (fun x => f x / g x) (𝓝[≠] a) (𝓝 L)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.Calculus.LHopital`

**Difficulty:** medium

---

### 15. Extreme Value Theorem

**Natural Language Statement:**
A continuous function on a compact set attains its maximum and minimum values.

**Lean 4 Theorem:**
```lean
theorem IsCompact.exists_isMinOn {f : α → β} {s : Set α}
  (hs : IsCompact s) (hne : s.Nonempty) (hf : ContinuousOn f s) :
  ∃ x ∈ s, IsMinOn f s x

theorem IsCompact.exists_isMaxOn {f : α → β} {s : Set α}
  (hs : IsCompact s) (hne : s.Nonempty) (hf : ContinuousOn f s) :
  ∃ x ∈ s, IsMaxOn f s x
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Algebra.Order.Compact`

**Difficulty:** medium

---

## Part II: Complex Analysis

### 16. Complex Differentiability (Holomorphic Functions)

**Natural Language Statement:**
A function f: ℂ → ℂ is holomorphic (complex differentiable) at z₀ if the limit lim_{h→0} (f(z₀+h) - f(z₀))/h exists in ℂ.

**Lean 4 Definition:**
```lean
-- Uses same HasDerivAt as real case, specialized to ℂ
def DifferentiableAt (𝕂 : Type*) [NontriviallyNormedField 𝕂]
  {E F : Type*} [NormedAddCommGroup E] [NormedSpace 𝕂 E]
  [NormedAddCommGroup F] [NormedSpace 𝕂 F] (f : E → F) (x : E) : Prop :=
  ∃ f' : E →L[𝕂] F, HasFDerivAt f f' x

-- Complex-specific: differentiability implies analyticity
theorem DifferentiableOn.analyticAt {f : ℂ → E} {s : Set ℂ}
  (hf : DifferentiableOn ℂ f s) (hs : IsOpen s) {z : ℂ} (hz : z ∈ s) :
  AnalyticAt ℂ f z
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.Complex.Basic`, `Mathlib.Analysis.Analytic.Basic`

**Difficulty:** medium

---

### 17. Cauchy Integral Theorem

**Natural Language Statement:**
If f is holomorphic in a simply connected domain D, then for any closed curve γ in D, ∮_γ f(z)dz = 0.

**Lean 4 Theorem:**
```lean
-- Circle version
theorem Complex.circleIntegral_eq_zero_of_differentiableOn {f : ℂ → E}
  {c : ℂ} {R : ℝ} (hR : 0 < R)
  (hf : DifferentiableOn ℂ f (Metric.closedBall c R)) :
  ∮ z in C(c, R), f z = 0
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.Complex.CauchyIntegral`

**Difficulty:** hard

---

### 18. Cauchy Integral Formula

**Natural Language Statement:**
If f is holomorphic inside and on a circle C centered at w, then f(w) = (1/2πi) ∮_C f(z)/(z-w) dz.

**Lean 4 Theorem:**
```lean
theorem Complex.two_pi_I_inv_smul_circleIntegral_sub_inv_smul_of_differentiable_on_off_countable
  {f : ℂ → E} {c w : ℂ} {R : ℝ} (hR : 0 < R) (hw : w ∈ Metric.ball c R)
  (hf : DifferentiableOn ℂ f (Metric.closedBall c R \ {w}))
  (hfc : ContinuousOn f (Metric.closedBall c R)) :
  (2 * π * I)⁻¹ • ∮ z in C(c, R), (z - w)⁻¹ • f z = f w
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.Complex.CauchyIntegral`

**Difficulty:** hard

---

### 19. Liouville's Theorem

**Natural Language Statement:**
Every bounded entire function (holomorphic on all of ℂ) is constant.

**Lean 4 Theorem:**
```lean
theorem Differentiable.apply_eq_apply_of_bounded {f : ℂ → E}
  (hf : Differentiable ℂ f) (hb : Bornology.IsBounded (Set.range f))
  (z w : ℂ) : f z = f w

-- Corollary: bounded entire functions are constant
theorem Differentiable.eq_const_of_bounded {f : ℂ → E}
  (hf : Differentiable ℂ f) (hb : Bornology.IsBounded (Set.range f)) :
  ∃ c, f = fun _ => c
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.Complex.Liouville`

**Difficulty:** hard

---

### 20. Maximum Modulus Principle

**Natural Language Statement:**
If f is holomorphic and non-constant on a connected open set, then |f| cannot attain a maximum in the interior of that set.

**Lean 4 Theorem:**
```lean
-- Local version
theorem Complex.norm_eventually_eq_of_isLocalMax {f : ℂ → ℂ} {c : ℂ}
  (hd : ∀ᶠ z in 𝓝 c, DifferentiableAt ℂ f z)
  (hc : IsLocalMax (norm ∘ f) c) :
  ∀ᶠ z in 𝓝 c, ‖f z‖ = ‖f c‖

-- Global version on compact sets
theorem Complex.eqOn_of_isPreconnected_of_isMaxOn_norm {f : ℂ → E}
  {U : Set ℂ} {c : ℂ}
  (hU : IsPreconnected U) (hUo : IsOpen U)
  (hd : DifferentiableOn ℂ f U) (hcU : c ∈ U)
  (hm : IsMaxOn (norm ∘ f) U c) :
  EqOn f (fun _ => f c) U
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.Complex.AbsMax`

**Difficulty:** hard

---

### 21. Schwarz Lemma

**Natural Language Statement:**
If f: D → D is holomorphic where D is the open unit disk, and f(0) = 0, then |f(z)| ≤ |z| for all z ∈ D, and |f'(0)| ≤ 1. Equality holds iff f is a rotation.

**Lean 4 Theorem:**
```lean
theorem Complex.abs_deriv_at_zero_le_one {f : ℂ → ℂ}
  (hf : DifferentiableOn ℂ f (Metric.ball 0 1))
  (h0 : f 0 = 0)
  (hb : ∀ z ∈ Metric.ball (0 : ℂ) 1, ‖f z‖ < 1) :
  ‖deriv f 0‖ ≤ 1

theorem Complex.norm_le_norm_of_mapsTo_ball {f : ℂ → ℂ}
  (hf : DifferentiableOn ℂ f (Metric.ball 0 1))
  (h0 : f 0 = 0)
  (hb : MapsTo f (Metric.ball 0 1) (Metric.ball 0 1))
  {z : ℂ} (hz : z ∈ Metric.ball (0 : ℂ) 1) :
  ‖f z‖ ≤ ‖z‖
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.Complex.Schwarz`

**Difficulty:** hard

---

### 22. Fundamental Theorem of Algebra

**100 Theorems List:** #16

**Natural Language Statement:**
Every non-constant polynomial with complex coefficients has at least one complex root.

**Lean 4 Theorem:**
```lean
theorem Complex.exists_root {p : Polynomial ℂ} (hp : 0 < p.degree) :
  ∃ z : ℂ, p.eval z = 0

-- Equivalently: ℂ is algebraically closed
instance Complex.instIsAlgClosed : IsAlgClosed ℂ
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.Complex.Polynomial.Basic`

**Difficulty:** hard

---

### 23. Power Series Representation

**Natural Language Statement:**
Every holomorphic function can be represented as a convergent power series in a neighborhood of any point in its domain.

**Lean 4 Theorem:**
```lean
theorem Complex.analyticOnNhd_iff_differentiableOn {f : ℂ → E} {s : Set ℂ}
  (hs : IsOpen s) :
  AnalyticOnNhd ℂ f s ↔ DifferentiableOn ℂ f s

-- Power series representation
theorem AnalyticAt.hasFPowerSeriesAt {f : ℂ → E} {z : ℂ}
  (hf : AnalyticAt ℂ f z) :
  ∃ p : FormalMultilinearSeries ℂ ℂ E, HasFPowerSeriesAt f p z
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Analysis.Analytic.Basic`

**Difficulty:** hard

---

## Part III: Notable Gaps

### Cauchy-Riemann Equations

**Status:** NOT FORMALIZED
**Natural Language Statement:**
A function f = u + iv is holomorphic iff ∂u/∂x = ∂v/∂y and ∂u/∂y = -∂v/∂x.

**Note:** This computational criterion for holomorphicity is a notable gap in Mathlib's complex analysis coverage.

---

### Residue Theorem

**Status:** NOT FORMALIZED
**Natural Language Statement:**
∮_γ f(z)dz = 2πi Σ Res(f, aₖ) where the sum is over poles inside γ.

**Note:** Essential for computing complex integrals.

---

### Green's Theorem (#21)

**100 Theorems List:** #21 - NOT FORMALIZED in Mathlib

**NL Statement**: "For a positively oriented, piecewise smooth, simple closed curve C bounding a region D in the plane, and vector field F = (P, Q) with continuous partial derivatives on an open region containing D:
∮_C (P dx + Q dy) = ∬_D (∂Q/∂x - ∂P/∂y) dA"

**Mathematical Significance**:
- Relates line integrals around closed curves to double integrals over enclosed regions
- Special case of the Generalized Stokes' Theorem (k=1, 2D)
- Foundation for circulation and flux in 2D fluid dynamics
- Connects to Cauchy integral theorem in complex analysis

**Expected Lean 4 Template**:
```lean
theorem greens_theorem
  {D : Set (ℝ × ℝ)} (hD : IsCompact D) (hD_nice : IsNiceRegion D)
  {P Q : ℝ × ℝ → ℝ}
  (hP : ContDiff ℝ 1 P) (hQ : ContDiff ℝ 1 Q)
  (h_on_D : ∀ p ∈ D, DifferentiableAt ℝ P p ∧ DifferentiableAt ℝ Q p) :
  ∮ C, (P • dx + Q • dy) = ∬ D, (∂Q/∂x - ∂P/∂y) dA := sorry
```

**Proof Approach**:
- Decompose region into type I and type II regions
- Apply Fubini's theorem
- Use Fundamental Theorem of Calculus on each component
- Combine via additivity

**Related Theorems**:
- **FTC Part 2**: Special case when path is horizontal/vertical segment
- **Divergence Theorem (2D)**: Flux form of Green's theorem
- **Cauchy Integral Theorem**: Complex analytic version

**Status**: NOT FORMALIZED - Requires:
- Line integral over curves
- Surface measure on 2D regions
- Boundary operator for regions

**Imports**: `Mathlib.MeasureTheory.Integral.IntervalIntegral`, `Mathlib.Analysis.Calculus.Deriv.Basic`

**Difficulty**: hard

---

## Lean 4 Formalization Reference

### Import Statements

```lean
import Mathlib.Analysis.SpecificLimits.Basic       -- Sequence limits
import Mathlib.Analysis.SpecificLimits.Normed      -- Normed space limits
import Mathlib.Topology.MetricSpace.Basic          -- Epsilon-delta
import Mathlib.Topology.Order.IntermediateValue    -- IVT
import Mathlib.Analysis.Calculus.Deriv.Basic       -- Derivatives
import Mathlib.Analysis.Calculus.Deriv.Comp        -- Chain rule
import Mathlib.Analysis.Calculus.Deriv.MeanValue   -- MVT, Rolle
import Mathlib.Analysis.Calculus.Taylor            -- Taylor's theorem
import Mathlib.Analysis.Calculus.LHopital          -- L'Hôpital
import Mathlib.MeasureTheory.Integral.IntervalIntegral.FundThmCalculus -- FTC
import Mathlib.Analysis.Complex.Basic              -- Complex analysis basics
import Mathlib.Analysis.Complex.CauchyIntegral     -- Cauchy theory
import Mathlib.Analysis.Complex.Liouville          -- Liouville's theorem
import Mathlib.Analysis.Complex.AbsMax             -- Maximum modulus
import Mathlib.Analysis.Complex.Schwarz            -- Schwarz lemma
```

### Key Definitions Summary

| Concept | Lean 4 Name | Import |
|---------|-------------|--------|
| Sequence limit | `Filter.Tendsto` | `Order.Filter.Basic` |
| Continuous | `Continuous` | `Topology.Basic` |
| Derivative | `HasDerivAt`, `deriv` | `Analysis.Calculus.Deriv.Basic` |
| Differentiable | `DifferentiableAt` | `Analysis.Calculus.Deriv.Basic` |
| Integral | `∫ x in a..b, f x` | `MeasureTheory.Integral.IntervalIntegral` |
| Holomorphic | `DifferentiableOn ℂ f s` | `Analysis.Complex.Basic` |
| Analytic | `AnalyticAt` | `Analysis.Analytic.Basic` |

---

## References

### Primary Sources

- [Wikipedia: Real analysis](https://en.wikipedia.org/wiki/Real_analysis)
- [Wikipedia: Complex analysis](https://en.wikipedia.org/wiki/Complex_analysis)
- [100 Theorems in Lean](https://leanprover-community.github.io/100.html)

### Lean 4 / Mathlib

- [Mathlib4 Docs: Analysis.Calculus](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/Calculus/)
- [Mathlib4 Docs: Analysis.Complex](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/Complex/)
- [Mathlib Analysis Overview](https://leanprover-community.github.io/theories/analysis.html)
- [Undergrad Math TODO](https://leanprover-community.github.io/undergrad_todo.html)

---

**End of Knowledge Base**
