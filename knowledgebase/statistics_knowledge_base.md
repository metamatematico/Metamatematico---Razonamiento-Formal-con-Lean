# Statistics Knowledge Base

## Overview
Statistics is the science of collecting, analyzing, interpreting, and presenting data. This knowledge base focuses on **statistical inference**: estimators, hypothesis testing, confidence intervals, and asymptotic theory. For foundational probability concepts (PMF, conditional probability, independence, distributions, limit theorems), see the **Probability Theory KB**.

**Mathlib4 Coverage**: Limited - Classical statistical inference (hypothesis testing, confidence intervals, regression, MLE) is not yet formalized in Mathlib4. This KB captures conceptual formalizations representing the expected Lean 4 API.

**Primary Coverage**: MSC 62 (Statistics)

---

## Related Knowledge Bases

### Prerequisites
- **Probability Theory** (`probability_theory_knowledge_base.md`): PMF, conditional probability, independence, distributions, Strong Law of Large Numbers
- **Measure Theory** (`measure_theory_knowledge_base.md`): Measure spaces, integration, probability measures
- **Real Analysis** (`real_analysis_knowledge_base.md`): Limits, convergence, continuity

### Foundational Content (See Probability Theory KB)
For foundational probability content used in statistical inference, see the **Probability Theory KB**:
- Probability mass functions and distributions
- Conditional probability and Bayes' theorem
- Independence of events and random variables
- Identical distributions and IdentDistrib
- Strong Law of Large Numbers

---

## Part I: Statistical Inference Concepts (Not Yet Formalized) (8 statements)

### 1. Sample Mean (Conceptual)
**NL**: The sample mean of observations x₁, ..., xₙ is x̄ = (1/n)∑ᵢxᵢ, an unbiased estimator of the population mean.

**Lean 4 (Sketch)**:
```lean
-- Not yet in Mathlib; conceptual formalization
def sampleMean {n : ℕ} (x : Fin n → ℝ) : ℝ :=
  (n : ℝ)⁻¹ * ∑ i, x i
```

### 2. Sample Variance (Conceptual)
**NL**: The sample variance s² = (1/(n-1))∑ᵢ(xᵢ - x̄)² is an unbiased estimator of population variance.

**Lean 4 (Sketch)**:
```lean
-- Not yet in Mathlib
def sampleVariance {n : ℕ} (hn : 2 ≤ n) (x : Fin n → ℝ) : ℝ :=
  ((n - 1 : ℕ) : ℝ)⁻¹ * ∑ i, (x i - sampleMean x) ^ 2
```

### 3. Confidence Interval (Conceptual)
**NL**: A 100(1-α)% confidence interval for a parameter θ is an interval [L, U] such that P(L ≤ θ ≤ U) = 1 - α.

**Lean 4 (Sketch)**:
```lean
-- Not yet in Mathlib
structure ConfidenceInterval (α : ℝ) (θ : ℝ) (μ : Measure Ω)
    (L U : Ω → ℝ) : Prop where
  coverage : μ {ω | L ω ≤ θ ∧ θ ≤ U ω} = 1 - α
```

### 4. Hypothesis Test (Conceptual)
**NL**: A hypothesis test at significance level α rejects the null hypothesis H₀ if the test statistic falls in a rejection region with probability α under H₀.

**Lean 4 (Sketch)**:
```lean
-- Not yet in Mathlib
structure HypothesisTest (H₀ : Prop) (α : ℝ) (reject : Ω → Bool)
    (μ₀ : Measure Ω) : Prop where
  type_I_error : μ₀ {ω | reject ω = true} ≤ α
```

### 5. Maximum Likelihood Estimator (Conceptual)
**NL**: The MLE θ̂ maximizes the likelihood function L(θ) = ∏ᵢf(xᵢ; θ) over all possible parameter values.

**Lean 4 (Sketch)**:
```lean
-- Not yet in Mathlib
def MLE {Θ : Type*} (L : Θ → ℝ) : Θ :=
  sorry -- argmax of L
```

### 6. Unbiased Estimator (Conceptual)
**NL**: An estimator θ̂ of parameter θ is unbiased if E[θ̂] = θ.

**Lean 4 (Sketch)**:
```lean
-- Not yet in Mathlib
def IsUnbiased (θ : ℝ) (θ̂ : Ω → ℝ) (μ : Measure Ω) : Prop :=
  ∫ ω, θ̂ ω ∂μ = θ
```

### 7. Consistent Estimator (Conceptual)
**NL**: An estimator sequence θ̂ₙ is consistent for θ if θ̂ₙ converges in probability to θ as n → ∞.

**Lean 4 (Sketch)**:
```lean
-- Not yet in Mathlib
def IsConsistent (θ : ℝ) (θ̂ : ℕ → Ω → ℝ) (μ : Measure Ω) : Prop :=
  ∀ ε > 0, Filter.Tendsto (fun n => μ {ω | |θ̂ n ω - θ| > ε})
    Filter.atTop (nhds 0)
```

### 8. Central Limit Theorem (Partial)
**NL**: For i.i.d. random variables with mean μ and variance σ², the standardized sample mean √n(X̄ - μ)/σ converges in distribution to N(0,1).

**Lean 4 (Sketch)**:
```lean
-- Partial in Mathlib; CLT versions exist for specific settings
-- Full CLT: Work in progress
theorem central_limit_theorem (X : ℕ → Ω → ℝ) (μ σ : ℝ) (hσ : 0 < σ)
    (hint : ∀ i, ∫ ω, X i ω ∂ℙ = μ)
    (hvar : ∀ i, variance (X i) ℙ = σ^2)
    (hindep : ∀ i j, i ≠ j → IndepFun (X i) (X j) ℙ) :
    sorry -- convergence in distribution to standard normal
```

---

## Summary

This knowledge base covers 8 statements on statistical inference:
- **Part I**: Statistical Inference Concepts (8 statements) - Sample mean/variance, confidence intervals, hypothesis testing, MLE, estimator properties, CLT

**Formalization Status**: Classical statistical inference (hypothesis testing, confidence intervals, regression) is not yet formalized in Mathlib4. This KB captures conceptual formalizations representing the expected Lean 4 API when these topics are added.

**Key Dependencies**: Probability Theory KB (for PMF, conditional probability, independence, distributions, SLLN), Measure Theory KB, Real Analysis KB
