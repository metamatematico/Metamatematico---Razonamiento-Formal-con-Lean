# Probability Theory Knowledge Base

**Domain**: Probability Theory & Stochastic Processes
**Lean 4 Coverage**: High (measure-theoretic probability)
**Source**: Mathlib4 `Probability.*` and `MeasureTheory.*` modules
**Last Updated**: 2025-12-14

---

## Overview

This knowledge base covers probability theory formalization in Lean 4/Mathlib, built on measure theory foundations. Includes probability spaces, random variables, expectation, variance, convergence modes, limit theorems, and common distributions.

**Key Gap**: Central Limit Theorem not yet formalized (as of Dec 2024).

---

## Related Knowledge Bases

### Prerequisites
- **Measure Theory** (`measure_theory_knowledge_base.md`): σ-algebras, measures, integration, convergence theorems

### Builds Upon This KB
- **Statistics** (`statistics_knowledge_base.md`): Statistical inference (conceptual)
- **Stochastic Processes** (`stochastic_processes_knowledge_base.md`): Filtrations, martingales, stopping times

### Related Topics
- **Real/Complex Analysis** (`real_complex_analysis_knowledge_base.md`): Convergence, integration

### Scope Clarification
This KB focuses on **measure-theoretic probability**:
- Probability spaces and measures
- Random variables and distributions
- Expectation, variance, moments
- Independence and conditional probability
- Convergence modes and limit theorems (SLLN, partial CLT)

For **statistical inference** (hypothesis testing, confidence intervals), see the **Statistics KB**.

---

## 1. PROBABILITY SPACES

### 1.1 Probability Measure

**Concept**: A measure `μ` on measurable space `Ω` with `μ(Ω) = 1`.

**NL Statement**: "A probability measure is a normalized measure where the total probability equals 1."

**Lean 4 Definition**:
```lean
class IsProbabilityMeasure {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω) : Prop where
  measure_univ : μ Set.univ = 1
```

**Imports**: `Mathlib.MeasureTheory.Measure.ProbabilityMeasure`

**Difficulty**: easy

---

### 1.2 ProbabilityMeasure Type

**Concept**: Subtype of all probability measures on `Ω`.

**NL Statement**: "The type of all probability measures on a measurable space, equipped with weak convergence topology."

**Lean 4 Definition**:
```lean
def ProbabilityMeasure (Ω : Type u₁) [MeasurableSpace Ω] : Type u₁ :=
  {μ : Measure Ω // IsProbabilityMeasure μ}
```

**Key Theorems**:
```lean
theorem coeFn_univ (ν : ProbabilityMeasure Ω) : ν Set.univ = 1
theorem apply_le_one (μ : ProbabilityMeasure Ω) (s : Set Ω) : μ s ≤ 1
```

**Imports**: `Mathlib.MeasureTheory.Measure.ProbabilityMeasure`

**Design Note**: Use `{P : Measure Ω} [IsProbabilityMeasure P]` unless working with topology of measures.

**Difficulty**: medium

---

### 1.3 Standard Setup

**NL Statement**: "Standard imports and namespace opens for probability theory work."

**Lean 4**:
```lean
import Mathlib.Probability.ProbabilityMassFunction.Basic
import Mathlib.Probability.Independence.Basic
import Mathlib.MeasureTheory.Measure.ProbabilityMeasure

open MeasureTheory ProbabilityTheory
open scoped ENNReal

variable {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
```

**Difficulty**: easy

---

## 2. RANDOM VARIABLES

### 2.1 Random Variable Definition

**Concept**: Random variable as measurable function.

**NL Statement**: "A random variable from probability space (Ω, P) to measurable space E is a measurable function X: Ω → E."

**Lean 4**:
```lean
variable {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω} [IsProbabilityMeasure P]
variable {E : Type*} [MeasurableSpace E]
variable (X : Ω → E) (hX : Measurable X)
```

**Imports**: `Mathlib.MeasureTheory.MeasurableSpace.Defs`

**Difficulty**: easy

---

### 2.2 Distribution of Random Variable

**Concept**: Law/distribution as pushforward measure.

**NL Statement**: "The distribution (law) of random variable X under measure P is the pushforward measure P.map X on the target space E."

**Lean 4**:
```lean
-- Distribution: P.map X : Measure E
-- For measurable set s ⊆ E:  (P.map X) s = P (X ⁻¹' s)
```

**Key Theorem**:
```lean
theorem Measure.map_apply {f : Ω → E} (hf : Measurable f) {s : Set E}
  (hs : MeasurableSet s) : (μ.map f) s = μ (f ⁻¹' s)
```

**Imports**: `Mathlib.MeasureTheory.Measure.MeasureSpace`

**Difficulty**: medium

---

### 2.3 Identical Distribution

**Concept**: Two RVs with same distribution.

**NL Statement**: "Random variables X and Y (possibly on different probability spaces) are identically distributed if their distributions coincide."

**Lean 4**:
```lean
def IdentDistrib {Ω Ω' E : Type*} [MeasurableSpace Ω] [MeasurableSpace Ω']
  [MeasurableSpace E] (X : Ω → E) (Y : Ω' → E) (P : Measure Ω) (Q : Measure Ω') : Prop
```

**Key Theorems**:
```lean
theorem IdentDistrib.measure_mem_eq : IdentDistrib X Y P Q →
  ∀ {s : Set E}, MeasurableSet s → P (X ⁻¹' s) = Q (Y ⁻¹' s)

theorem IdentDistrib.integral_eq : IdentDistrib X Y P Q →
  ∫ ω, f (X ω) ∂P = ∫ ω, f (Y ω) ∂Q
```

**Imports**: `Mathlib.Probability.IdentDistrib`

**Difficulty**: medium

---

### 2.4 Independence of Random Variables

**Concept**: Independence via measure factorization.

**NL Statement**: "Random variables X and Y are independent if for all measurable sets A and B, P(X ∈ A ∩ Y ∈ B) = P(X ∈ A) · P(Y ∈ B)."

**Lean 4**:
```lean
-- Two RVs
def IndepFun {Ω β γ : Type*} {_mΩ : MeasurableSpace Ω}
  [MeasurableSpace β] [MeasurableSpace γ]
  (f : Ω → β) (g : Ω → γ) (μ : Measure Ω) : Prop

-- Family of RVs
def iIndepFun {Ω ι : Type*} {_mΩ : MeasurableSpace Ω}
  {β : ι → Type*} [m : ∀ x, MeasurableSpace (β x)]
  (f : ∀ x, Ω → β x) (μ : Measure Ω) : Prop
```

**Typical Usage**:
```lean
variable {X : Ω → ℝ} {Y : Ω → ℕ}
         (hX : Measurable X) (hY : Measurable Y) (hXY : IndepFun X Y P)
```

**Imports**: `Mathlib.Probability.Independence.Basic`

**Difficulty**: medium

---

## 3. EXPECTATION AND MOMENTS

### 3.1 Expected Value

**Concept**: Expectation as Bochner integral.

**NL Statement**: "The expectation of X is its Bochner integral with respect to the probability measure P."

**Lean 4 Notations**:
```lean
-- General: ∫ ω, X ω ∂P
-- Compact: P[X]
-- MeasureSpace: 𝔼[X]
```

**Setup**:
```lean
variable {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
variable (X : Ω → E)
-- Expectation: ∫ ω, X ω ∂P
```

**Constraint**: Works for normed spaces. For `ℝ≥0∞`, use Lebesgue integral: `∫⁻ ω, Y ω ∂P`.

**Imports**: `Mathlib.MeasureTheory.Integral.Bochner.Basic`

**Difficulty**: easy (usage), medium (theory)

---

### 3.2 Variance

**Concept**: Variance as second central moment.

**NL Statement**: "The variance of X is the expected squared deviation from the mean: Var[X] = 𝔼[(X - 𝔼[X])²]."

**Lean 4 Definitions**:
```lean
def ProbabilityTheory.evariance {Ω : Type*} {mΩ : MeasurableSpace Ω}
  (X : Ω → ℝ) (μ : Measure Ω) : ENNReal :=
  ∫⁻ (ω : Ω), ‖X ω - ∫ (x : Ω), X x ∂μ‖ₑ ^ 2 ∂μ

def ProbabilityTheory.variance {Ω : Type*} {mΩ : MeasurableSpace Ω}
  (X : Ω → ℝ) (μ : Measure Ω) : ℝ :=
  (ProbabilityTheory.evariance X μ).toReal
```

**Usage**: `variance X P`

**Key Theorems**:
```lean
theorem variance_nonneg (X : Ω → ℝ) (μ : Measure Ω) : 0 ≤ variance X μ

theorem IndepFun.variance_add {X Y : Ω → ℝ}
  (hX : MemLp X 2 μ) (hY : MemLp Y 2 μ) (h : IndepFun X Y μ) :
  variance (X + Y) μ = variance X μ + variance Y μ
```

**Imports**: `Mathlib.Probability.Moments.Variance`

**Difficulty**: medium

---

### 3.3 Moments and Central Moments

**Concept**: Higher-order expectations.

**NL Statement**: "The p-th moment is 𝔼[X^p]. The p-th central moment is 𝔼[(X - 𝔼[X])^p]."

**Lean 4**:
```lean
def ProbabilityTheory.moment (X : Ω → ℝ) (p : ℕ) (μ : Measure Ω) : ℝ
def ProbabilityTheory.centralMoment (X : Ω → ℝ) (p : ℕ) (μ : Measure Ω) : ℝ
```

**Key Property**:
```lean
centralMoment X 2 μ = variance X μ
```

**Imports**: `Mathlib.Probability.Moments`

**Difficulty**: medium

---

### 3.4 Conditional Expectation

**Concept**: Best L² approximation in sub-σ-algebra.

**NL Statement**: "The conditional expectation 𝔼[X|m] is the m-measurable function that best approximates X in L²."

**Lean 4**:
```lean
def MeasureTheory.condExp {Ω : Type*} {mΩ : MeasurableSpace Ω}
  (m : MeasurableSpace Ω) (μ : Measure Ω) (f : Ω → E) : Ω → E
```

**Notation**: `μ[f|m]` or `P[Y|m]`

**Defining Property**:
```lean
theorem setIntegral_condExp (hf : Integrable f μ) (hs : MeasurableSet[m] s) :
  ∫ x in s, condExp m μ f x ∂μ = ∫ x in s, f x ∂μ
```

**Imports**: `Mathlib.MeasureTheory.Function.ConditionalExpectation.Basic`

**Difficulty**: hard

---

## 4. CONVERGENCE MODES

### 4.1 Almost Sure Convergence

**Concept**: Pointwise convergence except on null set.

**NL Statement**: "X_n converges to X almost surely if P({ω | X_n(ω) → X(ω)}) = 1."

**Lean 4**:
```lean
∀ᵐ (ω : Ω) ∂μ, Filter.Tendsto (fun n => X n ω) Filter.atTop (nhds (X ω))
```

**Imports**: `Mathlib.MeasureTheory.Function.AEEqFun`

**Difficulty**: medium

---

### 4.2 Convergence in Probability

**Concept**: Probability of large deviation vanishes.

**NL Statement**: "X_n converges to X in probability if for all ε > 0, P(|X_n - X| ≥ ε) → 0."

**Lean 4**:
```lean
def MeasureTheory.TendstoInMeasure {α ι : Type*} [MeasurableSpace α]
  (μ : Measure α) (f : ι → α → E) (l : Filter ι) (g : α → E) : Prop :=
  ∀ (ε : ℝ), 0 < ε →
    Filter.Tendsto (fun i => μ {x | ε ≤ dist (f i x) (g x)}) l (nhds 0)
```

**Key Theorems**:
```lean
theorem tendstoInMeasure_of_tendsto_eLpNorm  -- Lp → probability
theorem tendstoInMeasure_of_tendsto_ae       -- a.e. → probability (finite μ)
theorem TendstoInMeasure.exists_seq_tendsto_ae  -- subsequence → a.e.
```

**Imports**: `Mathlib.MeasureTheory.Function.ConvergenceInMeasure`

**Difficulty**: medium

---

### 4.3 Convergence in Lᵖ

**Concept**: Lp-norm convergence.

**NL Statement**: "X_n converges to X in Lᵖ if ‖X_n - X‖_p → 0."

**Lean 4**:
```lean
Filter.Tendsto (fun n => eLpNorm (X n - X) p μ) Filter.atTop (nhds 0)
```

**Imports**: `Mathlib.MeasureTheory.Function.LpSeminorm.Basic`

**Difficulty**: medium

---

### 4.4 Convergence in Distribution

**Concept**: Weak convergence of measures.

**NL Statement**: "X_n converges to X in distribution if P(X_n ∈ A) → P(X ∈ A) for continuity sets A."

**Lean 4**:
```lean
def MeasureTheory.TendstoInDistribution
  (μs : ι → Measure Ω) (l : Filter ι) (μ : Measure Ω) : Prop
```

**Imports**: `Mathlib.MeasureTheory.Function.ConvergenceInDistribution`

**Difficulty**: hard

---

## 5. LIMIT THEOREMS

### 5.1 Strong Law of Large Numbers (SLLN)

**Concept**: Sample mean converges almost surely.

**NL Statement**: "If X_n are i.i.d. integrable random variables, then (1/n)∑_{i<n} X_i → 𝔼[X_0] almost surely."

**Lean 4 (Banach space version)**:
```lean
theorem ProbabilityTheory.strong_law_ae
  {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}
  {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
  [MeasurableSpace E] [BorelSpace E]
  (X : ℕ → Ω → E)
  (hint : Integrable (X 0) μ)
  (hindep : Pairwise (Function.onFun (fun x1 x2 => IndepFun x1 x2 μ) X))
  (hident : ∀ i, IdentDistrib (X i) (X 0) μ μ) :
  ∀ᵐ (ω : Ω) ∂μ, Filter.Tendsto (fun n => (↑n)⁻¹ • ∑ i ∈ Finset.range n, X i ω)
    Filter.atTop (nhds (∫ x, X 0 x ∂μ))
```

**Lean 4 (ℝ version)**:
```lean
theorem ProbabilityTheory.strong_law_ae_real
  {Ω : Type*} {m : MeasurableSpace Ω} {μ : Measure Ω}
  (X : ℕ → Ω → ℝ)
  (hint : Integrable (X 0) μ)
  (hindep : Pairwise (Function.onFun (fun x1 x2 => IndepFun x1 x2 μ) X))
  (hident : ∀ i, IdentDistrib (X i) (X 0) μ μ) :
  ∀ᵐ (ω : Ω) ∂μ, Filter.Tendsto (fun n => (∑ i ∈ Finset.range n, X i ω) / ↑n)
    Filter.atTop (nhds (∫ x, X 0 x ∂μ))
```

**Proof Method**: Etemadi's approach (pairwise independence suffices)

**Author**: Sébastien Gouëzel

**Imports**: `Mathlib.Probability.StrongLaw`

**100 Theorems**: Included ✓

**Difficulty**: hard

---

### 5.2 Lᵖ Law of Large Numbers

**Concept**: Sample mean converges in Lp norm.

**NL Statement**: "If X_n are i.i.d. with X_0 ∈ Lᵖ, then (1/n)∑_{i<n} X_i → 𝔼[X_0] in Lᵖ."

**Lean 4**:
```lean
theorem ProbabilityTheory.strong_law_Lp
  {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}
  {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
  [MeasurableSpace E] [BorelSpace E]
  {p : ENNReal} (hp : 1 ≤ p) (hp' : p ≠ ⊤)
  (X : ℕ → Ω → E)
  (hℒp : MemLp (X 0) p μ)
  (hindep : Pairwise (Function.onFun (fun x1 x2 => IndepFun x1 x2 μ) X))
  (hident : ∀ i, IdentDistrib (X i) (X 0) μ μ) :
  Filter.Tendsto (fun n => eLpNorm
    (fun ω => (↑n)⁻¹ • ∑ i ∈ Finset.range n, X i ω - ∫ x, X 0 x ∂μ) p μ)
    Filter.atTop (nhds 0)
```

**Imports**: `Mathlib.Probability.StrongLaw`

**Difficulty**: hard

---

### 5.3 Weak Law of Large Numbers

**Concept**: Sample mean converges in probability.

**NL Statement**: "If X_n are i.i.d. integrable, then (1/n)∑_{i<n} X_i → 𝔼[X_0] in probability."

**Status**: Implied by SLLN + (a.e. convergence → convergence in measure)

**Derivable From**: `Mathlib.Probability.StrongLaw` + `Mathlib.MeasureTheory.Function.ConvergenceInMeasure`

**Difficulty**: medium

---

### 5.4 Central Limit Theorem (#47)

**100 Theorems**: Theorem #47 - Missing from Lean (as of Dec 2024)

**Status**: NOT FULLY FORMALIZED - Active development

**NL Statement**: "If X_n are independent identically distributed random variables with mean μ and finite variance σ², then the standardized sum (∑X_i - nμ)/(σ√n) converges in distribution to the standard normal distribution N(0,1)."

**Expected Lean 4 Template** (when formalized):
```lean
theorem central_limit_theorem
  {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω}
  (X : ℕ → Ω → ℝ)
  (hident : ∀ i, IdentDistrib (X i) (X 0) μ μ)
  (hindep : iIndepFun (fun _ => inferInstance) X μ)
  (hμ : ∫ ω, X 0 ω ∂μ = m)
  (hσ : variance (X 0) μ = σ² ∧ 0 < σ²) :
  TendstoInDistribution
    (fun n => (∑ i ∈ Finset.range n, X i - n • m) / (σ * √n))
    atTop
    (gaussianReal 0 1) := sorry
```

**Mathematical Significance**:
- Foundational result in probability theory
- Explains why normal distribution appears in nature
- Basis for statistical inference and confidence intervals

**Proof Approach**:
- Characteristic functions (Fourier transform)
- Lévy's continuity theorem
- Taylor expansion of characteristic function

**Imports**: `Mathlib.Probability.Distributions.Gaussian`, `Mathlib.Probability.IdentDistrib`

**Note**: While not fully formalized, the building blocks (Gaussian distribution, convergence in distribution, characteristic functions) are available in Mathlib.

**Difficulty**: hard

---

## 6. CONCENTRATION INEQUALITIES

### 6.1 Markov's Inequality

**Concept**: Tail bound using expectation.

**NL Statement**: "For nonnegative random variable X and ε > 0, P(X ≥ ε) ≤ E[X] / ε."

**Lean 4**:
```lean
theorem MeasureTheory.mul_meas_ge_le_lintegral₀
  {α : Type*} [MeasurableSpace α] {μ : Measure α}
  {f : α → ENNReal} (hf : AEMeasurable f μ) (ε : ENNReal) :
  ε * μ {x | ε ≤ f x} ≤ ∫⁻ a, f a ∂μ

-- Division form
theorem MeasureTheory.meas_ge_le_lintegral_div
  {α : Type*} [MeasurableSpace α] {μ : Measure α}
  {f : α → ENNReal} (hf : AEMeasurable f μ)
  {ε : ENNReal} (hε : ε ≠ 0) (hε' : ε ≠ ⊤) :
  μ {x | ε ≤ f x} ≤ (∫⁻ a, f a ∂μ) / ε
```

**Imports**: `Mathlib.MeasureTheory.Integral.Lebesgue.Markov`

**Difficulty**: medium

---

### 6.2 Chebyshev's Inequality

**Concept**: Tail bound using variance.

**NL Statement**: "For X with finite variance and c > 0, P(|X - E[X]| ≥ c) ≤ Var[X] / c²."

**Lean 4**:
```lean
theorem ProbabilityTheory.meas_ge_le_variance_div_sq
  {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}
  [IsFiniteMeasure μ] {X : Ω → ℝ}
  (hX : MemLp X 2 μ) {c : ℝ} (hc : 0 < c) :
  μ {ω | c ≤ |X ω - ∫ x, X x ∂μ|} ≤
    ENNReal.ofReal (variance X μ / c ^ 2)
```

**Imports**: `Mathlib.Probability.Moments.Variance`

**Difficulty**: medium

---

### 6.3 Kolmogorov's 0-1 Law

**Concept**: Tail events have probability 0 or 1.

**NL Statement**: "Any event in the tail σ-algebra of an independent sequence of σ-algebras has probability 0 or 1."

**Lean 4**:
```lean
theorem ProbabilityTheory.measure_zero_or_one_of_measurableSet_limsup_atTop
  {Ω ι : Type*} {s : ι → MeasurableSpace Ω}
  {m0 : MeasurableSpace Ω} {μ : Measure Ω}
  [SemilatticeSup ι] [NoMaxOrder ι] [Nonempty ι]
  (h_le : ∀ n, s n ≤ m0)
  (h_indep : iIndep s μ)
  {t : Set Ω} (ht_tail : MeasurableSet t) :
  -- Result: μ t = 0 ∨ μ t = 1
```

**Tail σ-algebra**: `limsup s atTop = ⋂ n, ⋃ i ≥ n, s i`

**Imports**: `Mathlib.Probability.Independence.ZeroOne`

**Difficulty**: hard

---

## 7. PROBABILITY DISTRIBUTIONS

### 7.1 Probability Mass Function (PMF)

**Concept**: Discrete probability distribution.

**NL Statement**: "A probability mass function is a function α → ℝ≥0∞ with sum 1."

**Lean 4**:
```lean
structure PMF (α : Type*) where
  val : α → ℝ≥0∞
  sum_eq_one : ∑' a, val a = 1
```

**Imports**: `Mathlib.Probability.ProbabilityMassFunction.Basic`

**Difficulty**: easy

---

### 7.2 Bernoulli Distribution

**Concept**: Single trial with success probability p.

**NL Statement**: "The Bernoulli distribution on Bool with success probability p."

**Lean 4**:
```lean
def PMF.bernoulli (p : NNReal) (h : p ≤ 1) : PMF Bool
```

**Imports**: `Mathlib.Probability.ProbabilityMassFunction.Constructions`

**Difficulty**: easy

---

### 7.3 Binomial Distribution

**Concept**: Count of successes in n trials.

**NL Statement**: "The binomial distribution: probability of exactly i successes in n independent Bernoulli(p) trials."

**Lean 4**:
```lean
def PMF.binomial (p : NNReal) (h : p ≤ 1) (n : ℕ) : PMF (Fin (n + 1))
```

**Mass Function**: `p^i * (1-p)^(n-i) * C(n,i)`

**Key Theorems**:
```lean
theorem PMF.binomial_apply_zero         -- P(0) = (1-p)^n
theorem PMF.binomial_apply_last         -- P(n) = p^n
theorem PMF.binomial_one_eq_bernoulli   -- n=1 case
```

**Imports**: `Mathlib.Probability.ProbabilityMassFunction.Binomial`

**Difficulty**: medium

---

### 7.4 Poisson Distribution

**Concept**: Rare events in fixed interval.

**NL Statement**: "The Poisson distribution with rate parameter λ."

**Status**: Included in Mathlib

**Imports**: `Mathlib.Probability.Distributions.Poisson`

**Difficulty**: medium

---

### 7.5 Gaussian (Normal) Distribution

**Concept**: Continuous bell curve distribution.

**NL Statement**: "The Gaussian distribution on ℝ with mean μ and variance v."

**Lean 4**:
```lean
def gaussianReal (μ : ℝ) (v : ℝ≥0) : Measure ℝ

instance : IsProbabilityMeasure (gaussianReal μ v)
```

**Special Case**: When `v = 0`, equals Dirac measure at `μ`

**Limitation**: Only formalized for `ℝ`, not `ℝⁿ`

**Imports**: `Mathlib.Probability.Distributions.Gaussian`

**Difficulty**: medium

---

### 7.6 Other Distributions

**Available**: Exponential, Gamma, Geometric, Pareto, Uniform

**Location**: `Mathlib.Probability.Distributions.*`

**Difficulty**: easy-medium

---

## 8. TRAINING DATA EXAMPLES

### Example 1: Variance of Sum (Easy)

```json
{
  "theorem_id": "prob_variance_sum_indep",
  "nl_statement": "The variance of the sum of two independent random variables equals the sum of their variances.",
  "lean_statement": "theorem IndepFun.variance_add {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} {X Y : Ω → ℝ} (hX : MemLp X 2 μ) (hY : MemLp Y 2 μ) (h : IndepFun X Y μ) : variance (X + Y) μ = variance X μ + variance Y μ",
  "lean_proof": "IndepFun.variance_add hX hY h",
  "imports": ["Mathlib.Probability.Moments.Variance"],
  "mathematical_domain": "Probability",
  "difficulty": "easy",
  "compiles": true
}
```

### Example 2: Markov's Inequality (Medium)

```json
{
  "theorem_id": "prob_markov_inequality",
  "nl_statement": "For a nonnegative random variable X and positive ε, the probability that X is at least ε is at most the expected value of X divided by ε.",
  "lean_statement": "theorem meas_ge_le_lintegral_div {α : Type*} [MeasurableSpace α] {μ : Measure α} {f : α → ENNReal} (hf : AEMeasurable f μ) {ε : ENNReal} (hε : ε ≠ 0) (hε' : ε ≠ ⊤) : μ {x | ε ≤ f x} ≤ (∫⁻ a, f a ∂μ) / ε",
  "lean_proof": "meas_ge_le_lintegral_div hf hε hε'",
  "imports": ["Mathlib.MeasureTheory.Integral.Lebesgue.Markov"],
  "mathematical_domain": "Probability",
  "difficulty": "medium",
  "compiles": true
}
```

### Example 3: Strong Law of Large Numbers (Hard)

```json
{
  "theorem_id": "prob_slln_real",
  "nl_statement": "For a sequence of independent identically distributed integrable real-valued random variables X_n, the sample mean (1/n)∑X_i converges almost surely to the expected value of X_0.",
  "lean_statement": "theorem strong_law_ae_real {Ω : Type*} {m : MeasurableSpace Ω} {μ : Measure Ω} (X : ℕ → Ω → ℝ) (hint : Integrable (X 0) μ) (hindep : Pairwise (Function.onFun (fun x1 x2 => IndepFun x1 x2 μ) X)) (hident : ∀ i, IdentDistrib (X i) (X 0) μ μ) : ∀ᵐ (ω : Ω) ∂μ, Filter.Tendsto (fun n => (∑ i ∈ Finset.range n, X i ω) / ↑n) Filter.atTop (nhds (∫ x, X 0 x ∂μ))",
  "lean_proof": "ProbabilityTheory.strong_law_ae_real X hint hindep hident",
  "imports": ["Mathlib.Probability.StrongLaw"],
  "mathematical_domain": "Probability",
  "difficulty": "hard",
  "compiles": true,
  "reasoning_trace": {
    "mathematical_insight": "The SLLN is proved using Etemadi's approach, which only requires pairwise independence rather than full mutual independence.",
    "proof_strategy": "Apply the formalized theorem directly from Mathlib",
    "key_lemmas": ["ProbabilityTheory.strong_law_ae_real"]
  }
}
```

---

## 9. DIFFICULTY CLASSIFICATION

| Level | Concepts |
|-------|----------|
| **easy** | Events, probability measures, Bernoulli, basic expectation, PMF |
| **medium** | Independence, variance, Markov/Chebyshev inequalities, convergence in probability, binomial/Poisson/Gaussian, moments, identical distribution |
| **hard** | SLLN, conditional expectation, Kolmogorov's 0-1 law, convergence in distribution, PDF, kernels, Lp law of large numbers |

---

## 10. GAPS AND FUTURE WORK

### Not Yet Formalized
1. **Central Limit Theorem** - Theorem #47 on 100 theorems list
2. **Multivariate Normal Distribution** - Only ℝ version exists
3. **Weak Law of Large Numbers** - May exist implicitly but not as named theorem

### High-Priority for Training Data
- SLLN variants (most important limit theorem available)
- Convergence mode relationships
- Independence properties
- Distribution transformations

---

## Sources

1. [Basic probability in Mathlib](https://leanprover-community.github.io/blog/posts/basic-probability-in-mathlib/)
2. [Mathlib4 Probability Documentation](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Probability/)
3. [Lean 100 Theorems Tracker](https://leanprover-community.github.io/100.html)
4. [Deep Research Synthesis](file:///Users/lkronecker/.claude/context/research/lean4-probability-theory-2025-12-14-deep.md)
