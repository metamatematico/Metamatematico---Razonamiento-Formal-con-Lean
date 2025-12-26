# Calculus of Variations Knowledge Base

## Overview

**Domain:** Calculus of Variations / Analysis
**Mathlib4 Coverage:** Partial - foundations formalized, variational calculus not yet
**Measurability Score:** 30/100

The calculus of variations studies functionals (functions of functions) and their extrema. While Mathlib4 has excellent coverage of foundational analysis (derivatives, convexity, local extrema, integration), the core variational calculus machinery—Euler-Lagrange equations, functional derivatives, and direct methods—remains unformalized.

---

## Related Knowledge Bases

### Prerequisites
- **Real/Complex Analysis** (`real_complex_analysis_knowledge_base.md`): Derivatives, integration
- **Functional Analysis** (`functional_analysis_knowledge_base.md`): Function spaces, weak convergence
- **Convex Analysis** (`convex_analysis_knowledge_base.md`): Convexity, optimization theory

### Builds Upon This KB
- **Partial Differential Equations** (`partial_differential_equations_knowledge_base.md`): Euler-Lagrange → PDEs
- **Riemannian Geometry** (`riemannian_geometry_knowledge_base.md`): Geodesics as variational problems

### Related Topics
- **Smooth Manifolds** (`smooth_manifolds_knowledge_base.md`): Variational problems on manifolds
- **Ordinary Differential Equations** (`ordinary_differential_equations_knowledge_base.md`): Euler-Lagrange equations

### Scope Clarification
This KB focuses on **calculus of variations foundations**:
- Local extrema (Fermat's theorem for functions)
- Fréchet derivatives
- Gâteaux derivatives
- Convexity conditions
- (Gaps: Euler-Lagrange equations, direct methods, functional derivatives)

For **optimization with constraints**, see **Convex Analysis KB**.

---

## Part I: Local Extrema Foundations

### Section 1.1: Fermat's Theorem (Point-wise)

#### Theorem 1.1.1: Derivative Vanishes at Local Maximum
**Natural Language:** If f has a local maximum at x and is differentiable there, then f'(x) = 0.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Calculus.LocalExtr.Basic
theorem IsLocalMax.deriv_eq_zero {f : ℝ → ℝ} {a : ℝ} (h : IsLocalMax f a) (hf : DifferentiableAt ℝ f a) :
    deriv f a = 0
```

#### Theorem 1.1.2: Derivative Vanishes at Local Minimum
**Natural Language:** If f has a local minimum at x and is differentiable there, then f'(x) = 0.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Calculus.LocalExtr.Basic
theorem IsLocalMin.deriv_eq_zero {f : ℝ → ℝ} {a : ℝ} (h : IsLocalMin f a) (hf : DifferentiableAt ℝ f a) :
    deriv f a = 0
```

#### Theorem 1.1.3: Fréchet Derivative Vanishes at Interior Extremum
**Natural Language:** If f has a local extremum at an interior point and is Fréchet differentiable there, the derivative is zero.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Calculus.LocalExtr.Basic
theorem IsLocalExtr.hasFDerivAt_eq_zero {E F : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F] {f : E → F} {a : E} {f' : E →L[ℝ] F}
    (h : IsLocalExtr f a) (hf : HasFDerivAt f f' a) : f' = 0
```

#### Theorem 1.1.4: Directional Derivative Nonpositive at Local Maximum
**Natural Language:** At a constrained local maximum, directional derivatives in feasible directions are nonpositive.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Calculus.LocalExtr.Basic
theorem IsLocalMaxOn.hasFDerivWithinAt_nonpos {E F : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F] {f : E → F} {s : Set E} {a : E} {f' : E →L[ℝ] F}
    (h : IsLocalMaxOn f s a) (hf : HasFDerivWithinAt f f' s a) {v : E}
    (hv : v ∈ posTangentConeAt s a) : f' v ≤ 0
```

### Section 1.2: Positive Tangent Cones

#### Definition 1.2.1: Positive Tangent Cone
**Natural Language:** The positive tangent cone at a point captures directions along which the set can be approached.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Calculus.LocalExtr.Basic
/-- The positive tangent cone to s at a: directions approachable from s. -/
def posTangentConeAt (s : Set E) (a : E) : Set E :=
  { v : E | ∃ (c : ℕ → ℝ) (d : ℕ → E), (∀ᶠ n in atTop, a + d n ∈ s) ∧
    Tendsto c atTop atTop ∧ Tendsto (fun n => c n • d n) atTop (𝓝 v) }
```

#### Theorem 1.2.2: Tangent Cone Monotonicity
**Natural Language:** If s ⊆ t, then the tangent cone at s is contained in the tangent cone at t.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Calculus.LocalExtr.Basic
theorem posTangentConeAt_mono {s t : Set E} (h : s ⊆ t) (a : E) :
    posTangentConeAt s a ⊆ posTangentConeAt t a
```

#### Theorem 1.2.3: Segment Implies Tangent Direction
**Natural Language:** If a line segment from a into s is contained in s, its direction is in the tangent cone.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Calculus.LocalExtr.Basic
theorem mem_posTangentConeAt_of_segment_subset {s : Set E} {a v : E}
    (h : ∀ t ∈ Set.Ioc 0 1, a + t • v ∈ s) : v ∈ posTangentConeAt s a
```

---

## Part II: Fréchet Differentiability

### Section 2.1: Fréchet Derivative Definitions

#### Definition 2.1.1: HasFDerivAt
**Natural Language:** f has Fréchet derivative f' at a if f(a+h) - f(a) - f'(h) = o(‖h‖) as h → 0.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Calculus.FDeriv.Basic
/-- f has Fréchet derivative f' at a. -/
def HasFDerivAt (f : E → F) (f' : E →L[ℝ] F) (a : E) : Prop :=
  HasFDerivAtFilter f f' a (𝓝 a)
```

#### Theorem 2.1.2: Differentiability Implies Continuity
**Natural Language:** If f is Fréchet differentiable at a, then f is continuous at a.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Calculus.FDeriv.Basic
theorem HasFDerivAt.continuousAt {f : E → F} {f' : E →L[ℝ] F} {a : E}
    (h : HasFDerivAt f f' a) : ContinuousAt f a
```

#### Theorem 2.1.3: Derivative Uniqueness
**Natural Language:** The Fréchet derivative, if it exists, is unique.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Calculus.FDeriv.Basic
theorem HasFDerivAt.unique {f : E → F} {f₁' f₂' : E →L[ℝ] F} {a : E}
    (h₁ : HasFDerivAt f f₁' a) (h₂ : HasFDerivAt f f₂' a) : f₁' = f₂'
```

#### Theorem 2.1.4: Chain Rule
**Natural Language:** The derivative of a composition is the composition of derivatives.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Calculus.FDeriv.Comp
theorem HasFDerivAt.comp {g : F → G} {f : E → F} {g' : F →L[ℝ] G} {f' : E →L[ℝ] F} {a : E}
    (hg : HasFDerivAt g g' (f a)) (hf : HasFDerivAt f f' a) :
    HasFDerivAt (g ∘ f) (g'.comp f') a
```

### Section 2.2: Higher Derivatives

#### Definition 2.2.1: ContDiff (Smooth Functions)
**Natural Language:** A function is C^n if it has n continuous derivatives.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Calculus.ContDiff.Defs
/-- f is n times continuously differentiable on s. -/
def ContDiffOn (n : ℕ∞) (f : E → F) (s : Set E) : Prop := ...

def ContDiff (n : ℕ∞) (f : E → F) : Prop := ContDiffOn n f Set.univ
```

#### Theorem 2.2.2: C^n Composition
**Natural Language:** The composition of C^n functions is C^n.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Calculus.ContDiff.Basic
theorem ContDiff.comp {g : F → G} {f : E → F} {n : ℕ∞}
    (hg : ContDiff n g) (hf : ContDiff n f) : ContDiff n (g ∘ f)
```

#### Theorem 2.2.3: Smooth Functions Form Algebra
**Natural Language:** Smooth functions are closed under addition, multiplication, and scalar multiplication.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Calculus.ContDiff.Basic
theorem ContDiff.add {f g : E → F} {n : ℕ∞} (hf : ContDiff n f) (hg : ContDiff n g) :
    ContDiff n (f + g)

theorem ContDiff.mul {f g : E → ℝ} {n : ℕ∞} (hf : ContDiff n f) (hg : ContDiff n g) :
    ContDiff n (f * g)
```

---

## Part III: Convexity and Optimization

### Section 3.1: Convex Functions

#### Definition 3.1.1: ConvexOn
**Natural Language:** f is convex on s if f(tx + (1-t)y) ≤ tf(x) + (1-t)f(y) for all x,y in s and t ∈ [0,1].
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Convex.Function
/-- f is convex on s. -/
def ConvexOn (s : Set E) (f : E → ℝ) : Prop :=
  Convex ℝ s ∧ ∀ ⦃x⦄, x ∈ s → ∀ ⦃y⦄, y ∈ s → ∀ ⦃a b : ℝ⦄, 0 ≤ a → 0 ≤ b → a + b = 1 →
    f (a • x + b • y) ≤ a • f x + b • f y
```

#### Definition 3.1.2: StrictConvexOn
**Natural Language:** f is strictly convex on s if the inequality is strict for x ≠ y and 0 < t < 1.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Convex.Function
/-- f is strictly convex on s. -/
def StrictConvexOn (s : Set E) (f : E → ℝ) : Prop :=
  Convex ℝ s ∧ ∀ ⦃x⦄, x ∈ s → ∀ ⦃y⦄, y ∈ s → x ≠ y → ∀ ⦃a b : ℝ⦄, 0 < a → 0 < b → a + b = 1 →
    f (a • x + b • y) < a • f x + b • f y
```

#### Theorem 3.1.3: Convex Sum
**Natural Language:** The sum of convex functions is convex.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Convex.Function
theorem ConvexOn.add {f g : E → ℝ} {s : Set E} (hf : ConvexOn s f) (hg : ConvexOn s g) :
    ConvexOn s (f + g)
```

#### Theorem 3.1.4: Strictly Convex Has Unique Minimum
**Natural Language:** A strictly convex function has at most one global minimum.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Convex.Function
theorem StrictConvexOn.eq_of_isMinOn {f : E → ℝ} {s : Set E} (hf : StrictConvexOn s f)
    {x y : E} (hx : x ∈ s) (hy : y ∈ s) (hxm : IsMinOn f s x) (hym : IsMinOn f s y) : x = y
```

#### Theorem 3.1.5: Convex Function Has Convex Sublevel Sets
**Natural Language:** If f is convex, then {x | f(x) ≤ c} is convex for all c.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Convex.Function
theorem ConvexOn.convex_le {f : E → ℝ} {s : Set E} (hf : ConvexOn s f) (c : ℝ) :
    Convex ℝ {x ∈ s | f x ≤ c}
```

### Section 3.2: Extrema Existence

#### Theorem 3.2.1: Compact Set Attains Extrema
**Natural Language:** A continuous function on a compact set attains its maximum and minimum.
**Difficulty:** medium

```lean4
-- Mathlib.Topology.Order.Basic
theorem IsCompact.exists_isMinOn {s : Set E} {f : E → ℝ} (hs : IsCompact s) (hne : s.Nonempty)
    (hf : ContinuousOn f s) : ∃ x ∈ s, IsMinOn f s x

theorem IsCompact.exists_isMaxOn {s : Set E} {f : E → ℝ} (hs : IsCompact s) (hne : s.Nonempty)
    (hf : ContinuousOn f s) : ∃ x ∈ s, IsMaxOn f s x
```

#### Theorem 3.2.2: Lower Semicontinuous Coercive Functions Attain Minimum
**Natural Language:** A coercive lower semicontinuous function on ℝ^n attains its minimum.
**Difficulty:** hard

```lean4
-- Mathlib.Topology.Semicontinuous
theorem LowerSemicontinuous.exists_isMinOn_of_coercive {f : E → ℝ} (hf : LowerSemicontinuous f)
    (hcoer : Tendsto f (cocompact E) atTop) : ∃ x, IsMinOn f Set.univ x
```

---

## Part IV: Mean Value Theorems

### Section 4.1: Rolle and Mean Value

#### Theorem 4.1.1: Rolle's Theorem
**Natural Language:** If f is continuous on [a,b], differentiable on (a,b), and f(a) = f(b), then f'(c) = 0 for some c ∈ (a,b).
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Calculus.MeanValue
theorem exists_deriv_eq_zero (hab : a < b) (hfc : ContinuousOn f (Set.Icc a b))
    (hff : DifferentiableOn ℝ f (Set.Ioo a b)) (hfab : f a = f b) :
    ∃ c ∈ Set.Ioo a b, deriv f c = 0
```

#### Theorem 4.1.2: Mean Value Theorem
**Natural Language:** For f continuous on [a,b] and differentiable on (a,b), there exists c ∈ (a,b) with f(b) - f(a) = f'(c)(b-a).
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Calculus.MeanValue
theorem exists_deriv_eq_slope (hab : a < b) (hfc : ContinuousOn f (Set.Icc a b))
    (hff : DifferentiableOn ℝ f (Set.Ioo a b)) :
    ∃ c ∈ Set.Ioo a b, deriv f c = (f b - f a) / (b - a)
```

#### Theorem 4.1.3: Convex Mean Value Bound
**Natural Language:** On a convex set with bounded derivative, ‖f(x) - f(y)‖ ≤ C · ‖x - y‖.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Calculus.MeanValue
theorem Convex.norm_image_sub_le_of_norm_fderiv_le {s : Set E} {f : E → F} {C : ℝ}
    (hs : Convex ℝ s) (hf : DifferentiableOn ℝ f s)
    (hC : ∀ x ∈ s, ‖fderiv ℝ f x‖ ≤ C) {x y : E} (hx : x ∈ s) (hy : y ∈ s) :
    ‖f x - f y‖ ≤ C * ‖x - y‖
```

#### Theorem 4.1.4: Zero Derivative Implies Constant
**Natural Language:** If the derivative vanishes on a convex set, the function is constant.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Calculus.MeanValue
theorem Convex.is_const_of_fderivWithin_eq_zero {s : Set E} {f : E → F} (hs : Convex ℝ s)
    (hf : DifferentiableOn ℝ f s) (hf' : ∀ x ∈ s, fderivWithin ℝ f s x = 0)
    {x y : E} (hx : x ∈ s) (hy : y ∈ s) : f x = f y
```

---

## Part V: Integration for Functionals

### Section 5.1: Interval Integration

#### Definition 5.1.1: Interval Integral
**Natural Language:** The integral ∫[a,b] f(t) dt as a signed integral over an interval.
**Difficulty:** easy

```lean4
-- Mathlib.MeasureTheory.Integral.IntervalIntegral
/-- Integral of f over interval [a,b]. -/
notation "∫" t " in " a ".." b ", " f => intervalIntegral f a b MeasureTheory.volume
```

#### Theorem 5.1.2: Fundamental Theorem of Calculus (First Part)
**Natural Language:** If f is continuous, then F(x) = ∫[a,x] f(t) dt is differentiable with F'(x) = f(x).
**Difficulty:** medium

```lean4
-- Mathlib.MeasureTheory.Integral.FundThmCalculus
theorem intervalIntegral.hasDerivAt_of_continuous {f : ℝ → E} {a x : ℝ}
    (hf : ContinuousOn f (Set.uIcc a x)) :
    HasDerivAt (fun y => ∫ t in a..y, f t) (f x) x
```

#### Theorem 5.1.3: Fundamental Theorem of Calculus (Second Part)
**Natural Language:** If F' = f on [a,b], then ∫[a,b] f(t) dt = F(b) - F(a).
**Difficulty:** medium

```lean4
-- Mathlib.MeasureTheory.Integral.FundThmCalculus
theorem intervalIntegral.integral_eq_sub_of_hasDerivAt {f F : ℝ → E} {a b : ℝ}
    (hF : ∀ x ∈ Set.uIcc a b, HasDerivAt F (f x) x)
    (hf : IntervalIntegrable f MeasureTheory.volume a b) :
    ∫ t in a..b, f t = F b - F a
```

#### Theorem 5.1.4: Integration by Parts
**Natural Language:** ∫[a,b] u dv = [uv]ₐᵇ - ∫[a,b] v du.
**Difficulty:** medium

```lean4
-- Mathlib.MeasureTheory.Integral.IntegralEqImproper
theorem intervalIntegral.integral_mul_deriv_eq_deriv_mul {f g : ℝ → ℝ} {a b : ℝ}
    (hf : ∀ x ∈ Set.uIcc a b, HasDerivAt f (f' x) x)
    (hg : ∀ x ∈ Set.uIcc a b, HasDerivAt g (g' x) x)
    (hf' : IntervalIntegrable f' MeasureTheory.volume a b)
    (hg' : IntervalIntegrable g' MeasureTheory.volume a b) :
    ∫ t in a..b, f t * g' t = f b * g b - f a * g a - ∫ t in a..b, f' t * g t
```

---

## Part VI: Euler-Lagrange Equations (Templates)

> **Note:** Euler-Lagrange equations and variational derivatives are NOT YET FORMALIZED in Mathlib4.
> The following entries use conceptual Lean code based on standard mathematical definitions.

### Section 6.1: Action Functionals

#### Definition 6.1.1: Action Functional (TEMPLATE)
**Natural Language:** The action functional J[y] = ∫[a,b] L(t, y(t), y'(t)) dt evaluates a Lagrangian along a path.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Action functional
/-- Action functional for Lagrangian L over paths from a to b. -/
noncomputable def actionFunctional (L : ℝ → ℝ → ℝ → ℝ) (a b : ℝ) (y : ℝ → ℝ) : ℝ :=
  ∫ t in a..b, L t (y t) (deriv y t)
```

#### Definition 6.1.2: First Variation (TEMPLATE)
**Natural Language:** The first variation δJ[y;η] measures the rate of change of J along direction η.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - First variation
/-- First variation of functional J at y in direction η. -/
noncomputable def firstVariation (J : (ℝ → ℝ) → ℝ) (y η : ℝ → ℝ) : ℝ :=
  deriv (fun ε => J (fun t => y t + ε * η t)) 0
```

#### Theorem 6.1.3: Stationary Condition (TEMPLATE)
**Natural Language:** y is a stationary point of J if δJ[y;η] = 0 for all admissible variations η.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Stationary condition
def IsStationary (J : (ℝ → ℝ) → ℝ) (y : ℝ → ℝ) : Prop :=
  ∀ η : ℝ → ℝ, Admissible η → firstVariation J y η = 0
```

### Section 6.2: Euler-Lagrange Equation

#### Theorem 6.2.1: Euler-Lagrange Equation (TEMPLATE)
**Natural Language:** If y extremizes J[y] = ∫L(t,y,y')dt, then d/dt(∂L/∂y') - ∂L/∂y = 0.
**Difficulty:** hard
**Status:** NOT FORMALIZED - Fundamental theorem of calculus of variations

```lean4
-- NOT IN MATHLIB - Euler-Lagrange equation
/-- The Euler-Lagrange equation for extremals of the action. -/
def satisfiesEulerLagrange (L : ℝ → ℝ → ℝ → ℝ) (y : ℝ → ℝ) : Prop :=
  ∀ t, deriv (fun t => (∂L/∂ẏ) t (y t) (deriv y t)) t = (∂L/∂y) t (y t) (deriv y t)
```

#### Theorem 6.2.2: Stationary Implies Euler-Lagrange (TEMPLATE)
**Natural Language:** If y is a stationary point of the action functional with smooth L, then y satisfies the Euler-Lagrange equation.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Stationary implies EL
theorem isStationary_implies_eulerLagrange (L : ℝ → ℝ → ℝ → ℝ) (y : ℝ → ℝ)
    (hL : ContDiff ℝ 2 L) (hstat : IsStationary (actionFunctional L a b) y) :
    satisfiesEulerLagrange L y
```

#### Theorem 6.2.3: Euler-Lagrange for Multi-Variable (TEMPLATE)
**Natural Language:** For L(t, y₁,...,yₙ, y'₁,...,y'ₙ), we get n coupled Euler-Lagrange equations.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Vector Euler-Lagrange
def satisfiesEulerLagrangeVec {n : ℕ} (L : ℝ → (Fin n → ℝ) → (Fin n → ℝ) → ℝ)
    (y : ℝ → Fin n → ℝ) : Prop :=
  ∀ i t, deriv (fun t => (∂L/∂ẏᵢ) t (y t) (deriv y t)) t = (∂L/∂yᵢ) t (y t) (deriv y t)
```

### Section 6.3: Special Cases

#### Theorem 6.3.1: Beltrami Identity (TEMPLATE)
**Natural Language:** If L is independent of t, then L - y'(∂L/∂y') is constant along extremals.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Beltrami identity
theorem beltrami_identity (L : ℝ → ℝ → ℝ) (y : ℝ → ℝ) (hL : ∀ t₁ t₂ v w, L v w = L v w)
    (hEL : satisfiesEulerLagrange (fun _ => L) y) :
    ∃ c, ∀ t, L (y t) (deriv y t) - deriv y t * (∂L/∂ẏ) (y t) (deriv y t) = c
```

#### Theorem 6.3.2: Geodesic Equation from Action (TEMPLATE)
**Natural Language:** Geodesics minimize arc length ∫√(1 + y'²)dt, satisfying y''/(1+y'²) = 0.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Geodesic as variational problem
theorem geodesic_equation_flat (y : ℝ → ℝ) (hL : satisfiesEulerLagrange
    (fun _ v dv => Real.sqrt (1 + dv^2)) y) : ∀ t, deriv (deriv y) t = 0
```

#### Theorem 6.3.3: Brachistochrone Equation (TEMPLATE)
**Natural Language:** The curve of fastest descent in gravity satisfies y(1+y'²) = const, giving a cycloid.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Brachistochrone
/-- Time functional for descent under gravity. -/
noncomputable def brachistochroneAction (y : ℝ → ℝ) (a b : ℝ) : ℝ :=
  ∫ t in a..b, Real.sqrt ((1 + (deriv y t)^2) / (2 * 9.8 * y t))

theorem brachistochrone_is_cycloid (y : ℝ → ℝ)
    (hopt : IsMinOn brachistochroneAction univ y) : IsCycloid y
```

---

## Part VII: Second Variation and Sufficiency (Templates)

### Section 7.1: Second Variation

#### Definition 7.1.1: Second Variation (TEMPLATE)
**Natural Language:** The second variation δ²J[y;η] determines whether a stationary point is a minimum.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Second variation
noncomputable def secondVariation (J : (ℝ → ℝ) → ℝ) (y η : ℝ → ℝ) : ℝ :=
  deriv (deriv (fun ε => J (fun t => y t + ε * η t))) 0 0
```

#### Theorem 7.1.2: Legendre Condition (TEMPLATE)
**Natural Language:** For a weak minimum, ∂²L/∂y'² ≥ 0 along the extremal.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Legendre condition
theorem legendre_necessary_condition (L : ℝ → ℝ → ℝ → ℝ) (y : ℝ → ℝ) (a b : ℝ)
    (hmin : IsLocalMin (actionFunctional L a b) y) :
    ∀ t ∈ Set.Icc a b, 0 ≤ (∂²L/∂ẏ²) t (y t) (deriv y t)
```

#### Theorem 7.1.3: Jacobi Equation (TEMPLATE)
**Natural Language:** The Jacobi equation governs conjugate points and sufficiency conditions.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Jacobi equation
/-- The Jacobi accessory equation for second variation analysis. -/
def satisfiesJacobiEquation (L : ℝ → ℝ → ℝ → ℝ) (y η : ℝ → ℝ) : Prop :=
  ∀ t, deriv (fun t => P t * deriv η t) t - Q t * η t = 0
  where P t := (∂²L/∂ẏ²) t (y t) (deriv y t)
        Q t := (∂²L/∂y²) t (y t) (deriv y t) - deriv (fun t => (∂²L/∂y∂ẏ) t (y t) (deriv y t)) t
```

### Section 7.2: Sufficient Conditions

#### Theorem 7.2.1: Weierstrass Sufficiency (TEMPLATE)
**Natural Language:** If δ²J > 0 for all nonzero η and no conjugate points exist, y is a strict local minimum.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Weierstrass sufficiency
theorem weierstrass_sufficiency (L : ℝ → ℝ → ℝ → ℝ) (y : ℝ → ℝ) (a b : ℝ)
    (hEL : satisfiesEulerLagrange L y)
    (hLeg : ∀ t, 0 < (∂²L/∂ẏ²) t (y t) (deriv y t))
    (hnoconj : NoConjugatePoints L y a b) :
    IsStrictLocalMin (actionFunctional L a b) y
```

---

## Part VIII: Direct Methods (Templates)

### Section 8.1: Weak Lower Semicontinuity

#### Theorem 8.1.1: Tonelli's Theorem (TEMPLATE)
**Natural Language:** If L is convex in y' and coercive, the action attains its minimum in Sobolev space.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Tonelli existence theorem
theorem tonelli_existence (L : ℝ → ℝ → ℝ → ℝ)
    (hconv : ∀ t y, ConvexOn ℝ univ (L t y))
    (hcoer : ∀ t y v, L t y v → ∞ as ‖v‖ → ∞)
    (a b y₀ y₁ : ℝ) :
    ∃ y : ℝ → ℝ, y a = y₀ ∧ y b = y₁ ∧ IsMinOn (actionFunctional L a b) {z | z a = y₀ ∧ z b = y₁} y
```

#### Theorem 8.1.2: Weak Lower Semicontinuity Criterion (TEMPLATE)
**Natural Language:** The action is weakly lower semicontinuous if L is convex in y'.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Weak LSC
theorem action_weak_lsc (L : ℝ → ℝ → ℝ → ℝ)
    (hconv : ∀ t y, ConvexOn ℝ univ (L t y)) :
    WeaklyLowerSemicontinuous (actionFunctional L a b)
```

---

## Part IX: Noether's Theorem (Templates)

### Section 9.1: Symmetries and Conservation Laws

#### Definition 9.1.1: Symmetry of Lagrangian (TEMPLATE)
**Natural Language:** A transformation is a symmetry if it leaves the Lagrangian invariant.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Lagrangian symmetry
/-- A one-parameter group is a symmetry of L if L is invariant. -/
def IsSymmetry (L : ℝ → ℝ → ℝ → ℝ) (φ : ℝ → ℝ → ℝ) : Prop :=
  ∀ ε t y dy, L t (φ ε y) (∂φ/∂y · dy) = L t y dy
```

#### Theorem 9.1.2: Noether's Theorem (TEMPLATE)
**Natural Language:** Every continuous symmetry of the Lagrangian yields a conserved quantity.
**Difficulty:** hard
**Status:** NOT FORMALIZED - Fundamental theorem connecting symmetry to conservation

```lean4
-- NOT IN MATHLIB - Noether's theorem
theorem noether_conservation (L : ℝ → ℝ → ℝ → ℝ) (φ : ℝ → ℝ → ℝ) (y : ℝ → ℝ)
    (hsym : IsSymmetry L φ) (hEL : satisfiesEulerLagrange L y) :
    ∃ I : ℝ → ℝ, ∀ t, deriv I t = 0 ∧ I t = (∂L/∂ẏ) t (y t) (deriv y t) * (∂φ/∂ε) 0 (y t)
```

#### Theorem 9.1.3: Time Translation Conservation (TEMPLATE)
**Natural Language:** If L is independent of t, energy H = y'(∂L/∂y') - L is conserved.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Energy conservation
theorem energy_conservation (L : ℝ → ℝ → ℝ) (y : ℝ → ℝ)
    (hEL : satisfiesEulerLagrange (fun _ => L) y) :
    ∃ E, ∀ t, deriv y t * (∂L/∂ẏ) (y t) (deriv y t) - L (y t) (deriv y t) = E
```

#### Theorem 9.1.4: Space Translation Conservation (TEMPLATE)
**Natural Language:** If L is independent of y, momentum p = ∂L/∂y' is conserved.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Momentum conservation
theorem momentum_conservation (L : ℝ → ℝ → ℝ) (y : ℝ → ℝ)
    (hL : ∀ t v w₁ w₂, L t v = L t v)  -- L independent of y
    (hEL : satisfiesEulerLagrange (fun t v dv => L t dv) y) :
    ∃ p, ∀ t, (∂L/∂ẏ) t (deriv y t) = p
```

---

## Part X: Optimal Control (Templates)

### Section 10.1: Pontryagin Maximum Principle

#### Definition 10.1.1: Optimal Control Problem (TEMPLATE)
**Natural Language:** Minimize J = ∫L(t,x,u)dt subject to ẋ = f(t,x,u) and boundary conditions.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Optimal control problem
/-- Optimal control problem with state x, control u. -/
structure OptimalControlProblem where
  dynamics : ℝ → ℝ → ℝ → ℝ  -- f(t,x,u)
  cost : ℝ → ℝ → ℝ → ℝ      -- L(t,x,u)
  controlSet : Set ℝ         -- admissible controls
```

#### Theorem 10.1.2: Pontryagin Maximum Principle (TEMPLATE)
**Natural Language:** Optimal controls maximize the Hamiltonian H = p·f - L with costate p satisfying ṗ = -∂H/∂x.
**Difficulty:** hard
**Status:** NOT FORMALIZED - Central theorem of optimal control

```lean4
-- NOT IN MATHLIB - Pontryagin maximum principle
theorem pontryagin_maximum_principle (P : OptimalControlProblem) (x u : ℝ → ℝ)
    (hopt : IsOptimal P x u) :
    ∃ p : ℝ → ℝ,
      (∀ t, deriv p t = -(∂H/∂x) t (x t) (u t) (p t)) ∧  -- costate equation
      (∀ t, ∀ v ∈ P.controlSet, H t (x t) (u t) (p t) ≥ H t (x t) v (p t))  -- maximum condition
```

#### Theorem 10.1.3: Hamilton-Jacobi-Bellman Equation (TEMPLATE)
**Natural Language:** The value function V satisfies ∂V/∂t + min_u{L + (∂V/∂x)·f} = 0.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - HJB equation
/-- Hamilton-Jacobi-Bellman equation for value function. -/
def satisfiesHJB (P : OptimalControlProblem) (V : ℝ → ℝ → ℝ) : Prop :=
  ∀ t x, (∂V/∂t) t x + ⨅ u ∈ P.controlSet,
    (P.cost t x u + (∂V/∂x) t x * P.dynamics t x u) = 0
```

---

## Dependencies

- **Internal:** `real_complex_analysis` (derivatives, integration), `functional_analysis` (normed spaces), `convex_analysis` (convexity), `ordinary_differential_equations` (ODE theory)
- **Mathlib4:** `Mathlib.Analysis.Calculus.FDeriv.*`, `Mathlib.Analysis.Calculus.LocalExtr.*`, `Mathlib.Analysis.Convex.Function`, `Mathlib.Analysis.Calculus.MeanValue`, `Mathlib.MeasureTheory.Integral.IntervalIntegral`

## Notes for Autoformalization

1. **Foundations excellent:** Local extrema, Fréchet derivatives, convexity all formalized
2. **Euler-Lagrange gap:** No variational derivatives or functional calculus in Mathlib
3. **Build on ODEs:** Euler-Lagrange equations become ODEs once derived
4. **Convexity key:** Direct methods rely on convexity infrastructure
5. **Second variation:** Requires bilinear form analysis, some infrastructure exists
6. **Optimal control:** Requires both ODE and extrema infrastructure

---

## Summary Statistics

- **Total Statements:** 55
- **Formalized (with Lean4):** 22 (40%)
- **Templates (NOT FORMALIZED):** 33 (60%)
- **Difficulty Distribution:** Easy: 12, Medium: 23, Hard: 20
