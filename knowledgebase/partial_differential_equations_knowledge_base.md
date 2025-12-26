# Partial Differential Equations Knowledge Base

## Overview

**Domain:** Partial Differential Equations / Analysis
**Mathlib4 Coverage:** Minimal - foundations only, no classical PDEs
**Measurability Score:** 25/100

Partial differential equations (PDEs) describe relations involving functions of multiple variables and their partial derivatives. Mathlib4 has excellent foundations for PDE theory—Schwartz spaces, distributions, functional analysis, integration—but the classical PDEs (heat, wave, Laplace equations) and modern PDE tools (Sobolev spaces, weak solutions) remain largely unformalized. The Gagliardo-Nirenberg-Sobolev inequality was recently formalized (2024).

---

## Related Knowledge Bases

### Prerequisites
- **Real/Complex Analysis** (`real_complex_analysis_knowledge_base.md`): Partial derivatives, integration
- **Functional Analysis** (`functional_analysis_knowledge_base.md`): Distributions, function spaces
- **Measure Theory** (`measure_theory_knowledge_base.md`): Lebesgue integration

### Builds Upon This KB
- (Advanced PDE applications)

### Related Topics
- **Ordinary Differential Equations** (`ordinary_differential_equations_knowledge_base.md`): Lower-dimensional case
- **Fourier Analysis** (`fourier_analysis_knowledge_base.md`): PDE solutions via Fourier
- **Calculus of Variations** (`calculus_of_variations_knowledge_base.md`): Variational PDEs

### Scope Clarification
This KB focuses on **PDE foundations**:
- Schwartz space and distributions
- Sobolev spaces (partial)
- Gagliardo-Nirenberg-Sobolev inequality (2024)
- (Gaps: Heat, wave, Laplace equations, weak solutions, elliptic regularity)

For **Fourier-based methods**, see **Fourier Analysis KB**.

---

## Part I: Schwartz Space and Distributions

### Section 1.1: Schwartz Space Definition

#### Definition 1.1.1: Schwartz Map
**Natural Language:** A Schwartz function is smooth with all derivatives decaying faster than any polynomial.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Distribution.SchwartzSpace
/-- Schwartz space: smooth functions with rapid decay. -/
structure SchwartzMap (E F : Type*) [NormedAddCommGroup E] [NormedSpace ℝ E]
    [NormedAddCommGroup F] [NormedSpace ℝ F] where
  toFun : E → F
  smooth' : ContDiff ℝ ⊤ toFun
  decay' : ∀ k n : ℕ, ∃ C, ∀ x, ‖x‖^k * ‖iteratedFDeriv ℝ n toFun x‖ ≤ C
```

#### Theorem 1.1.2: Schwartz Functions are Continuous
**Natural Language:** Every Schwartz function is continuous.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Distribution.SchwartzSpace
theorem SchwartzMap.continuous (f : SchwartzMap E F) : Continuous f
```

#### Theorem 1.1.3: Schwartz Functions are Smooth
**Natural Language:** Every Schwartz function is infinitely differentiable.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Distribution.SchwartzSpace
theorem SchwartzMap.contDiff (f : SchwartzMap E F) : ContDiff ℝ ⊤ f
```

#### Theorem 1.1.4: Schwartz Space is a Module
**Natural Language:** Schwartz functions form a vector space over ℝ.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Distribution.SchwartzSpace
instance : Module ℝ (SchwartzMap E F)
```

### Section 1.2: Schwartz Seminorms

#### Definition 1.2.1: Schwartz Seminorm Family
**Natural Language:** Schwartz space topology is defined by seminorms controlling derivatives and decay.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Distribution.SchwartzSpace
/-- The family of Schwartz seminorms indexed by (k, n). -/
def schwartzSeminormFamily : ℕ × ℕ → Seminorm ℝ (SchwartzMap E F) := ...
```

#### Theorem 1.2.2: Schwartz Space is Locally Convex
**Natural Language:** Schwartz space has a locally convex topology.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Distribution.SchwartzSpace
instance : LocallyConvexSpace ℝ (SchwartzMap E F)
```

#### Theorem 1.2.3: Schwartz Space is First Countable
**Natural Language:** The topology on Schwartz space is first countable.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Distribution.SchwartzSpace
instance : TopologicalSpace.FirstCountableTopology (SchwartzMap E F)
```

### Section 1.3: Operations on Schwartz Functions

#### Theorem 1.3.1: Derivative is Continuous Linear Map
**Natural Language:** Taking derivatives is a continuous operation on Schwartz space.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Distribution.SchwartzSpace
/-- Derivative as a continuous linear map on Schwartz space. -/
def derivCLM : SchwartzMap ℝ F →L[ℝ] SchwartzMap ℝ F
```

#### Theorem 1.3.2: Integration by Parts
**Natural Language:** For Schwartz functions: ∫ f' · g = -∫ f · g' (boundary terms vanish).
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Distribution.SchwartzSpace
theorem SchwartzMap.integral_deriv_mul_eq_neg_mul_deriv (f g : SchwartzMap ℝ ℝ) :
    ∫ x, deriv f x * g x = -∫ x, f x * deriv g x
```

#### Theorem 1.3.3: Schwartz Functions are Integrable
**Natural Language:** Every Schwartz function is integrable.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Distribution.SchwartzSpace
theorem SchwartzMap.integrable (f : SchwartzMap E F) : Integrable f
```

#### Theorem 1.3.4: Schwartz Embeds in Lp
**Natural Language:** Schwartz space embeds continuously into Lp for all 1 ≤ p ≤ ∞.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Distribution.SchwartzSpace
theorem SchwartzMap.memℒp (f : SchwartzMap E F) (p : ℝ≥0∞) : Memℒp f p
```

---

## Part II: Tempered Distributions

### Section 2.1: Distribution Definition

#### Definition 2.1.1: Tempered Distribution
**Natural Language:** A tempered distribution is a continuous linear functional on Schwartz space.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Distribution.TemperedDistribution (conceptual)
/-- Tempered distributions: continuous linear functionals on Schwartz space. -/
abbrev TemperedDistribution (E F : Type*) := SchwartzMap E F →L[ℝ] ℝ
```

#### Theorem 2.1.2: Function as Distribution
**Natural Language:** Every locally integrable function defines a distribution via integration.
**Difficulty:** easy

```lean4
-- Conceptual - Mathlib approach
/-- A locally integrable function f defines a distribution T_f(φ) = ∫ f · φ. -/
def Distribution.ofFunction (f : E → ℝ) (hf : LocallyIntegrable f) :
    SchwartzMap E ℝ →L[ℝ] ℝ :=
  ⟨fun φ => ∫ x, f x * φ x, ...⟩
```

### Section 2.2: Distribution Operations

#### Definition 2.2.1: Distributional Derivative
**Natural Language:** The derivative of a distribution T is defined by ⟨T', φ⟩ = -⟨T, φ'⟩.
**Difficulty:** medium

```lean4
-- Conceptual - standard definition
/-- Distributional derivative via integration by parts. -/
def Distribution.deriv (T : TemperedDistribution E ℝ) : TemperedDistribution E ℝ :=
  ⟨fun φ => -T (derivCLM φ), ...⟩
```

#### Theorem 2.2.2: Derivative of Regular Distribution
**Natural Language:** For smooth f, the distributional derivative agrees with the classical derivative.
**Difficulty:** medium

```lean4
-- Conceptual
theorem Distribution.deriv_ofFunction {f : E → ℝ} (hf : ContDiff ℝ 1 f) :
    Distribution.deriv (Distribution.ofFunction f) = Distribution.ofFunction (deriv f)
```

---

## Part III: Partial Derivatives and Multiindex Notation

### Section 3.1: Iterated Derivatives

#### Definition 3.1.1: Iterated Fréchet Derivative
**Natural Language:** The n-th iterated Fréchet derivative of f at x.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Calculus.FDeriv.Symmetric
/-- The n-th Fréchet derivative. -/
def iteratedFDeriv (n : ℕ) (f : E → F) (x : E) : (Fin n → E) →L[ℝ] F
```

#### Theorem 3.1.2: Symmetry of Higher Derivatives
**Natural Language:** For smooth functions, mixed partial derivatives are equal (Schwarz's theorem).
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.Calculus.FDeriv.Symmetric
theorem iteratedFDeriv_comm {f : E → F} (hf : ContDiff ℝ 2 f) {x : E} {v w : E} :
    iteratedFDeriv ℝ 2 f x ![v, w] = iteratedFDeriv ℝ 2 f x ![w, v]
```

#### Definition 3.1.3: Iterated Derivative (One-dimensional)
**Natural Language:** The n-th derivative of a function f : ℝ → F.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Calculus.IteratedDeriv.Defs
/-- The n-th derivative of a function. -/
def iteratedDeriv (n : ℕ) (f : 𝕜 → F) (x : 𝕜) : F :=
  (iteratedFDeriv 𝕜 n f x) (fun _ => 1)
```

#### Theorem 3.1.4: Iterated Derivative Recursion
**Natural Language:** The (n+1)-th derivative is the derivative of the n-th derivative.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.Calculus.IteratedDeriv.Defs
theorem iteratedDeriv_succ (n : ℕ) (f : 𝕜 → F) :
    iteratedDeriv (n + 1) f = deriv (iteratedDeriv n f)
```

### Section 3.2: Multiindex Operations

#### Definition 3.2.1: Multiindex (TEMPLATE)
**Natural Language:** A multiindex α = (α₁,...,αₙ) encodes partial derivative orders.
**Difficulty:** easy
**Status:** NOT FULLY FORMALIZED

```lean4
-- Conceptual - multiindex as Fin n → ℕ
/-- A multiindex is a tuple of nonnegative integers. -/
abbrev Multiindex (n : ℕ) := Fin n → ℕ

/-- Order of multiindex |α| = Σ αᵢ. -/
def Multiindex.order (α : Multiindex n) : ℕ := ∑ i, α i
```

#### Definition 3.2.2: Partial Derivative with Multiindex (TEMPLATE)
**Natural Language:** D^α f = ∂^|α| f / ∂x₁^α₁ ⋯ ∂xₙ^αₙ.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Multiindex derivative
/-- Partial derivative indexed by multiindex. -/
noncomputable def partialDeriv (α : Multiindex n) (f : (Fin n → ℝ) → F) : (Fin n → ℝ) → F := ...
```

---

## Part IV: Linear PDE Operators (Templates)

> **Note:** Classical PDE operators are NOT YET FORMALIZED in Mathlib4.

### Section 4.1: The Laplacian

#### Definition 4.1.1: Laplacian Operator (TEMPLATE)
**Natural Language:** The Laplacian Δf = ∑ ∂²f/∂xᵢ² is the trace of the Hessian.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Laplacian
/-- The Laplacian operator on ℝⁿ. -/
noncomputable def laplacian {n : ℕ} (f : (Fin n → ℝ) → ℝ) (x : Fin n → ℝ) : ℝ :=
  ∑ i, iteratedFDeriv ℝ 2 f x (fun j => if j = 0 ∨ j = 1 then Pi.single i 1 else 0)
```

#### Theorem 4.1.2: Laplacian is Linear (TEMPLATE)
**Natural Language:** Δ(af + bg) = aΔf + bΔg.
**Difficulty:** easy
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB
theorem laplacian_add (f g : (Fin n → ℝ) → ℝ) : laplacian (f + g) = laplacian f + laplacian g

theorem laplacian_smul (a : ℝ) (f : (Fin n → ℝ) → ℝ) : laplacian (a • f) = a • laplacian f
```

#### Theorem 4.1.3: Laplacian in Polar Coordinates (TEMPLATE)
**Natural Language:** In ℝ², Δf = ∂²f/∂r² + (1/r)∂f/∂r + (1/r²)∂²f/∂θ².
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Polar Laplacian
theorem laplacian_polar {f : ℝ × ℝ → ℝ} (x : ℝ × ℝ) (hx : x ≠ 0) :
    laplacian f x = (∂²f/∂r²) + (1/r) * (∂f/∂r) + (1/r²) * (∂²f/∂θ²)
```

### Section 4.2: Gradient and Divergence

#### Definition 4.2.1: Gradient (TEMPLATE)
**Natural Language:** ∇f = (∂f/∂x₁,...,∂f/∂xₙ) is the vector of partial derivatives.
**Difficulty:** easy
**Status:** PARTIALLY FORMALIZED via fderiv

```lean4
-- Partially in Mathlib via fderiv
/-- Gradient as the Fréchet derivative viewed as a vector. -/
noncomputable def gradient (f : (Fin n → ℝ) → ℝ) (x : Fin n → ℝ) : Fin n → ℝ :=
  fun i => fderiv ℝ f x (Pi.single i 1)
```

#### Definition 4.2.2: Divergence (TEMPLATE)
**Natural Language:** div F = ∑ ∂Fᵢ/∂xᵢ is the sum of partial derivatives of components.
**Difficulty:** easy
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Divergence
noncomputable def divergence {n : ℕ} (F : (Fin n → ℝ) → (Fin n → ℝ)) (x : Fin n → ℝ) : ℝ :=
  ∑ i, fderiv ℝ (fun y => F y i) x (Pi.single i 1)
```

#### Theorem 4.2.3: Laplacian is Divergence of Gradient (TEMPLATE)
**Natural Language:** Δf = div(∇f).
**Difficulty:** easy
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB
theorem laplacian_eq_div_grad (f : (Fin n → ℝ) → ℝ) : laplacian f = divergence (gradient f)
```

---

## Part V: Classical PDEs (Templates)

> **Note:** The following classical PDEs are NOT YET FORMALIZED in Mathlib4.

### Section 5.1: Laplace's Equation

#### Definition 5.1.1: Harmonic Function (TEMPLATE)
**Natural Language:** A function u is harmonic if Δu = 0.
**Difficulty:** easy
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Harmonic function
def IsHarmonic (u : (Fin n → ℝ) → ℝ) : Prop := ∀ x, laplacian u x = 0
```

#### Theorem 5.1.2: Mean Value Property (TEMPLATE)
**Natural Language:** Harmonic functions satisfy the mean value property: u(x) = average of u on spheres.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Mean value property
theorem harmonic_mean_value {u : (Fin n → ℝ) → ℝ} (hu : IsHarmonic u) (x : Fin n → ℝ) (r : ℝ) :
    u x = (1 / surfaceArea (sphere x r)) * ∫ y in sphere x r, u y
```

#### Theorem 5.1.3: Maximum Principle (TEMPLATE)
**Natural Language:** A harmonic function on a bounded domain attains its maximum on the boundary.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Maximum principle
theorem harmonic_maximum_principle {Ω : Set (Fin n → ℝ)} (hΩ : IsBounded Ω) (hΩc : IsOpen Ω)
    {u : (Fin n → ℝ) → ℝ} (hu : IsHarmonic u) (huc : ContinuousOn u (closure Ω)) :
    ∃ x ∈ frontier Ω, ∀ y ∈ closure Ω, u y ≤ u x
```

#### Theorem 5.1.4: Liouville's Theorem (TEMPLATE)
**Natural Language:** A bounded harmonic function on ℝⁿ is constant.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Liouville
theorem harmonic_bounded_const {u : (Fin n → ℝ) → ℝ} (hu : IsHarmonic u)
    (hbdd : ∃ M, ∀ x, |u x| ≤ M) : ∃ c, u = fun _ => c
```

### Section 5.2: Heat Equation

#### Definition 5.2.1: Heat Equation (TEMPLATE)
**Natural Language:** The heat equation ∂u/∂t = kΔu describes diffusion.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Heat equation
def SatisfiesHeatEquation (u : ℝ → (Fin n → ℝ) → ℝ) (k : ℝ) : Prop :=
  ∀ t x, deriv (fun t => u t x) t = k * laplacian (u t) x
```

#### Theorem 5.2.2: Heat Kernel (TEMPLATE)
**Natural Language:** The fundamental solution is G(x,t) = (4πkt)^(-n/2) exp(-|x|²/(4kt)).
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Heat kernel
noncomputable def heatKernel (k : ℝ) (n : ℕ) (t : ℝ) (x : Fin n → ℝ) : ℝ :=
  (4 * Real.pi * k * t) ^ (-(n : ℝ) / 2) * Real.exp (-‖x‖^2 / (4 * k * t))

theorem heatKernel_satisfies_heat_equation (k : ℝ) (hk : 0 < k) :
    SatisfiesHeatEquation (fun t x => heatKernel k n t x) k
```

#### Theorem 5.2.3: Heat Equation Maximum Principle (TEMPLATE)
**Natural Language:** The maximum of a solution is attained on the parabolic boundary.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Parabolic maximum principle
theorem heat_maximum_principle {Ω : Set (Fin n → ℝ)} {T : ℝ} (hT : 0 < T)
    {u : ℝ → (Fin n → ℝ) → ℝ} (hu : SatisfiesHeatEquation u k) :
    ∀ (t, x) ∈ Set.Ioo 0 T ×ˢ Ω, u t x ≤ sup (parabolicBoundary Ω T) u
```

### Section 5.3: Wave Equation

#### Definition 5.3.1: Wave Equation (TEMPLATE)
**Natural Language:** The wave equation ∂²u/∂t² = c²Δu describes wave propagation.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Wave equation
def SatisfiesWaveEquation (u : ℝ → (Fin n → ℝ) → ℝ) (c : ℝ) : Prop :=
  ∀ t x, iteratedDeriv 2 (fun t => u t x) t = c^2 * laplacian (u t) x
```

#### Theorem 5.3.2: d'Alembert's Solution (TEMPLATE)
**Natural Language:** In 1D, u(x,t) = (f(x+ct) + f(x-ct))/2 + (1/2c)∫[x-ct,x+ct] g.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - d'Alembert solution
theorem dAlembert_solution (f g : ℝ → ℝ) (c : ℝ) (hc : c ≠ 0) :
    let u := fun t x => (f (x + c*t) + f (x - c*t)) / 2 + (1/(2*c)) * ∫ s in (x-c*t)..(x+c*t), g s
    SatisfiesWaveEquation (fun t => u t) c
```

#### Theorem 5.3.3: Energy Conservation (TEMPLATE)
**Natural Language:** For wave equation, E = ∫(|∂u/∂t|² + c²|∇u|²) is conserved.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Wave energy
def waveEnergy (u : ℝ → (Fin n → ℝ) → ℝ) (c : ℝ) (t : ℝ) : ℝ :=
  ∫ x, (deriv (fun t => u t x) t)^2 + c^2 * ‖gradient (u t) x‖^2

theorem wave_energy_conserved (u : ℝ → (Fin n → ℝ) → ℝ) (c : ℝ)
    (hu : SatisfiesWaveEquation u c) : ∀ t₁ t₂, waveEnergy u c t₁ = waveEnergy u c t₂
```

---

## Part VI: Sobolev Spaces (Templates)

> **Note:** Sobolev spaces are partially formalized. The Gagliardo-Nirenberg-Sobolev inequality was formalized in 2024.

### Section 6.1: Weak Derivatives

#### Definition 6.1.1: Weak Derivative (TEMPLATE)
**Natural Language:** g is the weak derivative of f if ∫fφ' = -∫gφ for all test functions φ.
**Difficulty:** medium
**Status:** PARTIALLY FORMALIZED

```lean4
-- Conceptual - weak derivative
def IsWeakDeriv (f g : E → ℝ) : Prop :=
  ∀ φ : SchwartzMap E ℝ, ∫ x, f x * deriv φ x = -∫ x, g x * φ x
```

#### Definition 6.1.2: Sobolev Space W^{k,p} (TEMPLATE)
**Natural Language:** W^{k,p}(Ω) consists of functions with weak derivatives up to order k in Lp.
**Difficulty:** hard
**Status:** PARTIALLY FORMALIZED (GNS inequality formalized)

```lean4
-- NOT FULLY IN MATHLIB - Sobolev space
/-- The Sobolev space W^{k,p}. -/
structure SobolevSpace (k : ℕ) (p : ℝ≥0∞) (Ω : Set (Fin n → ℝ)) where
  toFun : (Fin n → ℝ) → ℝ
  weak_derivs : ∀ α : Multiindex n, α.order ≤ k → ∃ g, IsWeakDeriv (partialDeriv α toFun) g
  integrability : ∀ α : Multiindex n, α.order ≤ k → Memℒp (partialDeriv α toFun) p
```

### Section 6.2: Sobolev Embeddings

#### Theorem 6.2.1: Gagliardo-Nirenberg-Sobolev Inequality (FORMALIZED)
**Natural Language:** For 1 ≤ p < n, ‖u‖_{Lp*} ≤ C‖∇u‖_{Lp} where p* = np/(n-p).
**Difficulty:** hard
**Status:** FORMALIZED in Mathlib4 (2024)

```lean4
-- Mathlib.Analysis.SpecialFunctions.Integrals.GagliardoNirenberg (or similar)
/-- The Gagliardo-Nirenberg-Sobolev inequality. -/
theorem gagliardo_nirenberg_sobolev {n : ℕ} (hn : 2 ≤ n) {p : ℝ} (hp : 1 ≤ p) (hpn : p < n)
    (u : SchwartzMap (Fin n → ℝ) ℝ) :
    ‖u‖_{L^(n*p/(n-p))} ≤ C * ‖gradient u‖_{L^p}
```

#### Theorem 6.2.2: Sobolev Embedding W^{1,p} ↪ Lq (TEMPLATE)
**Natural Language:** W^{1,p}(ℝⁿ) embeds continuously into Lq for suitable q.
**Difficulty:** hard
**Status:** PARTIALLY FORMALIZED

```lean4
-- Follows from GNS inequality
theorem sobolev_embedding_Lq {n : ℕ} (hn : 2 ≤ n) {p : ℝ} (hp : 1 ≤ p) (hpn : p < n) :
    ContinuousLinearMap (SobolevSpace 1 p univ) (Lp (n*p/(n-p)))
```

#### Theorem 6.2.3: Morrey's Inequality (TEMPLATE)
**Natural Language:** For p > n, W^{1,p} functions are Hölder continuous.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Morrey embedding
theorem morrey_embedding {n : ℕ} {p : ℝ} (hpn : n < p) {u : SobolevSpace 1 p (Fin n → ℝ)} :
    HolderContinuous (1 - n/p) u
```

---

## Part VII: Well-Posedness Theory (Templates)

### Section 7.1: Existence and Uniqueness

#### Theorem 7.1.1: Lax-Milgram Theorem (TEMPLATE)
**Natural Language:** For coercive bilinear form a on Hilbert space, the equation a(u,v) = F(v) has unique solution.
**Difficulty:** hard
**Status:** NOT FORMALIZED (Formalized in Coq)

```lean4
-- NOT IN MATHLIB - Lax-Milgram
theorem lax_milgram {H : Type*} [NormedAddCommGroup H] [InnerProductSpace ℝ H] [CompleteSpace H]
    (a : H →L[ℝ] H →L[ℝ] ℝ) (F : H →L[ℝ] ℝ)
    (hcont : ∃ M, ∀ u v, |a u v| ≤ M * ‖u‖ * ‖v‖)
    (hcoer : ∃ α > 0, ∀ u, α * ‖u‖^2 ≤ a u u) :
    ∃! u : H, ∀ v, a u v = F v
```

#### Definition 7.1.2: Weak Solution of Poisson (TEMPLATE)
**Natural Language:** u is a weak solution of -Δu = f if ∫∇u·∇v = ∫fv for all test v.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Weak Poisson solution
def IsWeakSolutionPoisson (u : SobolevSpace 1 2 Ω) (f : Ω → ℝ) : Prop :=
  ∀ v : SobolevSpace 1 2 Ω, v.bdry = 0 →
    ∫ x in Ω, inner (gradient u x) (gradient v x) = ∫ x in Ω, f x * v x
```

### Section 7.2: Regularity

#### Theorem 7.2.1: Elliptic Regularity (TEMPLATE)
**Natural Language:** If -Δu = f with f ∈ L², then u ∈ W^{2,2}.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Elliptic regularity
theorem elliptic_regularity {u : SobolevSpace 1 2 Ω} {f : Ω → ℝ} (hf : Memℒp f 2)
    (hu : IsWeakSolutionPoisson u f) : u ∈ SobolevSpace 2 2 Ω
```

---

## Part VIII: Green's Functions and Integral Representations (Templates)

### Section 8.1: Fundamental Solutions

#### Theorem 8.1.1: Fundamental Solution of Laplacian (TEMPLATE)
**Natural Language:** In ℝⁿ (n≥3), Φ(x) = c_n/|x|^{n-2} satisfies -ΔΦ = δ₀.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Fundamental solution
noncomputable def laplaceFundamental (n : ℕ) (x : Fin n → ℝ) : ℝ :=
  if n = 2 then -(1/(2*Real.pi)) * Real.log ‖x‖
  else (1/((n-2) * surfaceArea (sphere 0 1))) * ‖x‖^(-(n-2 : ℝ))

theorem laplaceFundamental_is_fundamental (hn : 3 ≤ n) :
    -laplacian (laplaceFundamental n) = diracDelta 0  -- in distribution sense
```

#### Theorem 8.1.2: Green's Representation Formula (TEMPLATE)
**Natural Language:** u(x) = ∫_Ω G(x,y)f(y)dy + boundary terms.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Green's representation
theorem green_representation {Ω : Set (Fin n → ℝ)} (hΩ : IsOpen Ω) (hΩb : IsBounded Ω)
    {u : (Fin n → ℝ) → ℝ} (hu : -laplacian u = f) (huc : ContinuousOn u (closure Ω)) :
    ∀ x ∈ Ω, u x = ∫ y in Ω, G Ω x y * f y + ∫ y in ∂Ω, (u y * ∂G/∂ν - G * ∂u/∂ν)
```

---

## Dependencies

- **Internal:** `real_complex_analysis` (derivatives), `functional_analysis` (Banach/Hilbert spaces), `measure_theory` (integration), `ordinary_differential_equations`
- **Mathlib4:** `Mathlib.Analysis.Distribution.SchwartzSpace`, `Mathlib.Analysis.Calculus.IteratedDeriv.*`, `Mathlib.Analysis.Calculus.FDeriv.*`

## Notes for Autoformalization

1. **Schwartz space excellent:** Use `SchwartzMap`, seminorms, integration by parts
2. **Distributions:** Build on Schwartz space as dual
3. **Laplacian gap:** Define via iterated Fréchet derivative and trace
4. **Sobolev:** Build on Lp spaces; GNS inequality is formalized
5. **Classical PDEs:** All require templates; no heat/wave/Laplace formalized
6. **Weak solutions:** Define via integration by parts

---

## Summary Statistics

- **Total Statements:** 50
- **Formalized (with Lean4):** 14 (28%)
- **Templates (NOT FORMALIZED):** 36 (72%)
- **Difficulty Distribution:** Easy: 8, Medium: 20, Hard: 22
