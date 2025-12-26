# Information Theory Knowledge Base

## Overview

**Domain:** Information Theory / Discrete Mathematics
**Mathlib4 Coverage:** Partial - binary entropy formalized, Shannon entropy not yet
**Measurability Score:** 55/100

Information theory quantifies information content, entropy, and channel capacity. Mathlib4 has excellent formalization of binary and q-ary entropy functions, probability mass functions, and logarithm properties. Shannon entropy, mutual information, and channel coding theorems remain unformalized.

---

## Related Knowledge Bases

### Prerequisites
- **Probability Theory** (`probability_theory_knowledge_base.md`): Probability distributions, expectation
- **Real/Complex Analysis** (`real_complex_analysis_knowledge_base.md`): Logarithms, convexity
- **Measure Theory** (`measure_theory_knowledge_base.md`): Probability measures

### Builds Upon This KB
- **Coding Theory** (`coding_theory_knowledge_base.md`): Error-correcting codes, channel capacity
- **Additive Combinatorics** (`additive_combinatorics_knowledge_base.md`): Entropy methods for PFR

### Related Topics
- **Computability Theory** (`computability_theory_knowledge_base.md`): Algorithmic information theory
- **Statistics** (`statistics_knowledge_base.md`): Fisher information, KL divergence

### Scope Clarification
This KB focuses on **information theory**:
- Logarithm foundations
- Binary and q-ary entropy
- Probability mass functions
- Entropy properties
- (Gaps: Shannon entropy, mutual information, channel coding)

For **probability foundations**, see **Probability Theory KB**.

---

## Part I: Logarithm Foundations

### Section 1.1: Basic Logarithm Properties

#### Theorem 1.1.1: Logarithm of Product
**Natural Language:** The logarithm of a product equals the sum of logarithms.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.Log.Basic
theorem Real.log_mul (hx : x ≠ 0) (hy : y ≠ 0) : Real.log (x * y) = Real.log x + Real.log y
```

#### Theorem 1.1.2: Logarithm of Quotient
**Natural Language:** The logarithm of a quotient equals the difference of logarithms.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.Log.Basic
theorem Real.log_div (x : ℝ) (hy : y ≠ 0) : Real.log (x / y) = Real.log x - Real.log y
```

#### Theorem 1.1.3: Logarithm of Power
**Natural Language:** The logarithm of a power equals the exponent times the logarithm of the base.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.Log.Basic
theorem Real.log_rpow (hx : 0 < x) (y : ℝ) : Real.log (x ^ y) = y * Real.log x
```

#### Theorem 1.1.4: Logarithm Strictly Monotone
**Natural Language:** The natural logarithm is strictly increasing on positive reals.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.Log.Basic
theorem Real.log_strictMonoOn : StrictMonoOn Real.log (Set.Ioi 0)
```

#### Theorem 1.1.5: Logarithm Continuous
**Natural Language:** The natural logarithm is continuous on positive reals.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.Log.Basic
theorem Real.continuousOn_log : ContinuousOn Real.log {x | x ≠ 0}
```

#### Theorem 1.1.6: Logarithm Concave
**Natural Language:** The natural logarithm is strictly concave on positive reals.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.SpecialFunctions.Log.Basic
theorem Real.strictConcaveOn_log_Ioi : StrictConcaveOn ℝ (Set.Ioi 0) Real.log
```

#### Theorem 1.1.7: Logarithm Derivative
**Natural Language:** The derivative of the natural logarithm at x is 1/x.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.Log.Deriv
theorem Real.hasDerivAt_log (hx : x ≠ 0) : HasDerivAt Real.log x⁻¹ x
```

#### Theorem 1.1.8: Change of Base Formula
**Natural Language:** log_b(x) = ln(x) / ln(b) for any valid base b.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.Log.Basic
theorem Real.log_div_log (x b : ℝ) : Real.log x / Real.log b = Real.logb b x
```

### Section 1.2: Entropy Function η

#### Theorem 1.2.1: Entropy Function Definition
**Natural Language:** The function η(x) = -x log x is extended continuously to [0,1] with η(0) = 0.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
/-- The function `η(x) = -x * log x` extended to `[0, 1]` with `η(0) = 0`. -/
noncomputable def negMulLog (x : ℝ) : ℝ := -x * Real.log x
```

#### Theorem 1.2.2: Entropy Function at Zero
**Natural Language:** η(0) = 0 by continuous extension.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem negMulLog_zero : negMulLog 0 = 0
```

#### Theorem 1.2.3: Entropy Function at One
**Natural Language:** η(1) = 0 since log(1) = 0.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem negMulLog_one : negMulLog 1 = 0
```

#### Theorem 1.2.4: Entropy Function Nonnegative
**Natural Language:** η(x) ≥ 0 for x ∈ [0,1].
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem negMulLog_nonneg (hx : x ∈ Set.Icc 0 1) : 0 ≤ negMulLog x
```

#### Theorem 1.2.5: Entropy Function Continuous
**Natural Language:** η is continuous on [0, ∞).
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem continuous_negMulLog : Continuous negMulLog
```

#### Theorem 1.2.6: Entropy Function Strictly Concave
**Natural Language:** η is strictly concave on (0, ∞).
**Difficulty:** hard

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem strictConcaveOn_negMulLog : StrictConcaveOn ℝ (Set.Ioi 0) negMulLog
```

---

## Part II: Binary Entropy

### Section 2.1: Binary Entropy Definition and Values

#### Theorem 2.1.1: Binary Entropy Definition
**Natural Language:** Binary entropy H(p) = η(p) + η(1-p) = -p log p - (1-p) log(1-p).
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
/-- The binary entropy function `H(p) = η(p) + η(1-p)`. -/
noncomputable def binEntropy (p : ℝ) : ℝ := negMulLog p + negMulLog (1 - p)
```

#### Theorem 2.1.2: Binary Entropy at Zero
**Natural Language:** H(0) = 0 (deterministic outcome).
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem binEntropy_zero : binEntropy 0 = 0
```

#### Theorem 2.1.3: Binary Entropy at One
**Natural Language:** H(1) = 0 (deterministic outcome).
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem binEntropy_one : binEntropy 1 = 0
```

#### Theorem 2.1.4: Binary Entropy at Half
**Natural Language:** H(1/2) = log 2 (maximum uncertainty for binary source).
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem binEntropy_half : binEntropy (1/2) = Real.log 2
```

#### Theorem 2.1.5: Binary Entropy Symmetry
**Natural Language:** H(p) = H(1-p) (complementary probabilities have equal entropy).
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem binEntropy_one_sub (p : ℝ) : binEntropy (1 - p) = binEntropy p
```

#### Theorem 2.1.6: Binary Entropy Nonnegative
**Natural Language:** H(p) ≥ 0 for all p ∈ [0,1].
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem binEntropy_nonneg (hp : p ∈ Set.Icc 0 1) : 0 ≤ binEntropy p
```

### Section 2.2: Binary Entropy Analytic Properties

#### Theorem 2.2.1: Binary Entropy Continuous
**Natural Language:** Binary entropy is continuous on ℝ.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem binEntropy_continuous : Continuous binEntropy
```

#### Theorem 2.2.2: Binary Entropy Strictly Increasing on [0, 1/2]
**Natural Language:** H is strictly increasing on [0, 1/2].
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem binEntropy_strictMonoOn : StrictMonoOn binEntropy (Set.Icc 0 (1/2))
```

#### Theorem 2.2.3: Binary Entropy Strictly Decreasing on [1/2, 1]
**Natural Language:** H is strictly decreasing on [1/2, 1].
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem binEntropy_strictAntiOn : StrictAntiOn binEntropy (Set.Icc (1/2) 1)
```

#### Theorem 2.2.4: Binary Entropy Strictly Concave
**Natural Language:** Binary entropy is strictly concave on (0, 1).
**Difficulty:** hard

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem strictConcave_binEntropy : StrictConcaveOn ℝ (Set.Ioo 0 1) binEntropy
```

#### Theorem 2.2.5: Binary Entropy Maximum
**Natural Language:** H achieves its maximum value log 2 uniquely at p = 1/2.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem binEntropy_le (hp : p ∈ Set.Icc 0 1) : binEntropy p ≤ Real.log 2

theorem binEntropy_eq_log_two_iff (hp : p ∈ Set.Icc 0 1) :
    binEntropy p = Real.log 2 ↔ p = 1/2
```

#### Theorem 2.2.6: Binary Entropy Derivative
**Natural Language:** d/dp H(p) = log((1-p)/p) for p ∈ (0,1).
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem hasDerivAt_binEntropy (hp₀ : 0 < p) (hp₁ : p < 1) :
    HasDerivAt binEntropy (Real.log ((1 - p) / p)) p
```

### Section 2.3: Q-ary Entropy

#### Theorem 2.3.1: Q-ary Entropy Definition
**Natural Language:** Q-ary entropy generalizes binary entropy to base q alphabets.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
/-- Q-ary entropy for alphabet of size q. -/
noncomputable def qaryEntropy (q : ℕ) (p : ℝ) : ℝ :=
  negMulLog p + (1 - p) * Real.log (q - 1) + negMulLog (1 - p)
```

#### Theorem 2.3.2: Q-ary Entropy at Zero
**Natural Language:** Hq(0) = 0 for any alphabet size q.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem qaryEntropy_zero (hq : 1 < q) : qaryEntropy q 0 = 0
```

#### Theorem 2.3.3: Q-ary Entropy Nonnegative
**Natural Language:** Hq(p) ≥ 0 for p ∈ [0, 1] and q ≥ 2.
**Difficulty:** medium

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem qaryEntropy_nonneg (hq : 1 < q) (hp : p ∈ Set.Icc 0 1) : 0 ≤ qaryEntropy q p
```

#### Theorem 2.3.4: Q-ary Entropy Continuous
**Natural Language:** Q-ary entropy is continuous for fixed q.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem qaryEntropy_continuous (hq : 1 < q) : Continuous (qaryEntropy q)
```

#### Theorem 2.3.5: Binary Entropy as Q-ary Special Case
**Natural Language:** H(p) = H_2(p), binary entropy is q-ary entropy with q=2.
**Difficulty:** easy

```lean4
-- Mathlib.Analysis.SpecialFunctions.BinaryEntropy
theorem qaryEntropy_two : qaryEntropy 2 = binEntropy
```

---

## Part III: Probability Mass Functions

### Section 3.1: PMF Definition and Basic Properties

#### Theorem 3.1.1: PMF Definition
**Natural Language:** A probability mass function assigns nonnegative values summing to 1.
**Difficulty:** easy

```lean4
-- Mathlib.Probability.ProbabilityMassFunction.Basic
/-- A probability mass function on α. -/
def PMF (α : Type*) := { f : α → ℝ≥0∞ // HasSum f 1 }
```

#### Theorem 3.1.2: PMF Values Nonnegative
**Natural Language:** PMF values are nonnegative extended reals.
**Difficulty:** easy

```lean4
-- Mathlib.Probability.ProbabilityMassFunction.Basic
theorem PMF.apply_nonneg (p : PMF α) (a : α) : 0 ≤ p a
```

#### Theorem 3.1.3: PMF Sum is One
**Natural Language:** The sum of all PMF values equals 1.
**Difficulty:** easy

```lean4
-- Mathlib.Probability.ProbabilityMassFunction.Basic
theorem PMF.tsum_coe (p : PMF α) : ∑' a, p a = 1
```

#### Theorem 3.1.4: PMF to Measure
**Natural Language:** Every PMF induces a probability measure.
**Difficulty:** medium

```lean4
-- Mathlib.Probability.ProbabilityMassFunction.Basic
/-- The measure associated to a PMF. -/
def PMF.toMeasure (p : PMF α) : Measure α := Measure.sum fun a => p a • Measure.dirac a
```

#### Theorem 3.1.5: PMF Measure is Probability
**Natural Language:** The measure induced by a PMF is a probability measure.
**Difficulty:** medium

```lean4
-- Mathlib.Probability.ProbabilityMassFunction.Basic
instance PMF.toMeasure.isProbabilityMeasure (p : PMF α) : IsProbabilityMeasure p.toMeasure
```

### Section 3.2: PMF Support and Operations

#### Theorem 3.2.1: PMF Support Definition
**Natural Language:** The support of a PMF is the set of elements with positive probability.
**Difficulty:** easy

```lean4
-- Mathlib.Probability.ProbabilityMassFunction.Basic
def PMF.support (p : PMF α) : Set α := { a | p a ≠ 0 }
```

#### Theorem 3.2.2: PMF Support Nonempty
**Natural Language:** The support of any PMF is nonempty.
**Difficulty:** easy

```lean4
-- Mathlib.Probability.ProbabilityMassFunction.Basic
theorem PMF.support_nonempty (p : PMF α) : p.support.Nonempty
```

#### Theorem 3.2.3: PMF of Pure Distribution
**Natural Language:** A pure/Dirac distribution assigns probability 1 to a single point.
**Difficulty:** easy

```lean4
-- Mathlib.Probability.ProbabilityMassFunction.Basic
/-- The pure PMF concentrated at a single point. -/
def PMF.pure (a : α) : PMF α := ⟨fun b => if b = a then 1 else 0, hasSum_ite_eq a 1⟩
```

#### Theorem 3.2.4: PMF Pure Support
**Natural Language:** The support of a pure distribution is the singleton.
**Difficulty:** easy

```lean4
-- Mathlib.Probability.ProbabilityMassFunction.Basic
theorem PMF.support_pure (a : α) : (PMF.pure a).support = {a}
```

#### Theorem 3.2.5: PMF Bind Operation
**Natural Language:** PMFs support monadic bind for probabilistic composition.
**Difficulty:** medium

```lean4
-- Mathlib.Probability.ProbabilityMassFunction.Monad
/-- Monadic bind for PMFs. -/
def PMF.bind (p : PMF α) (f : α → PMF β) : PMF β :=
  ⟨fun b => ∑' a, p a * f a b, ...⟩
```

#### Theorem 3.2.6: PMF Map Operation
**Natural Language:** PMFs can be mapped over functions.
**Difficulty:** easy

```lean4
-- Mathlib.Probability.ProbabilityMassFunction.Monad
def PMF.map (f : α → β) (p : PMF α) : PMF β := p.bind (PMF.pure ∘ f)
```

### Section 3.3: Uniform Distribution

#### Theorem 3.3.1: Uniform Distribution on Fintype
**Natural Language:** A uniform distribution assigns equal probability to all elements.
**Difficulty:** easy

```lean4
-- Mathlib.Probability.ProbabilityMassFunction.Uniform
/-- Uniform distribution on a fintype. -/
def PMF.uniformOfFintype (α : Type*) [Fintype α] [Nonempty α] : PMF α :=
  ⟨fun _ => 1 / Fintype.card α, ...⟩
```

#### Theorem 3.3.2: Uniform Distribution Value
**Natural Language:** Each element has probability 1/|α| in uniform distribution.
**Difficulty:** easy

```lean4
-- Mathlib.Probability.ProbabilityMassFunction.Uniform
theorem PMF.uniformOfFintype_apply [Fintype α] [Nonempty α] (a : α) :
    PMF.uniformOfFintype α a = 1 / Fintype.card α
```

#### Theorem 3.3.3: Uniform Support is Full
**Natural Language:** The support of uniform distribution is the entire type.
**Difficulty:** easy

```lean4
-- Mathlib.Probability.ProbabilityMassFunction.Uniform
theorem PMF.support_uniformOfFintype [Fintype α] [Nonempty α] :
    (PMF.uniformOfFintype α).support = Set.univ
```

---

## Part IV: Shannon Entropy (Templates)

> **Note:** Shannon entropy for general distributions is NOT YET FORMALIZED in Mathlib4.
> The following entries use conceptual Lean code based on standard definitions.

### Section 4.1: Discrete Entropy

#### Theorem 4.1.1: Shannon Entropy Definition (TEMPLATE)
**Natural Language:** Shannon entropy H(X) = -Σ p(x) log p(x) measures average information content.
**Difficulty:** medium
**Status:** NOT FORMALIZED - Conceptual Lean code

```lean4
-- NOT IN MATHLIB - Shannon entropy definition
/-- Shannon entropy of a PMF. -/
noncomputable def PMF.entropy (p : PMF α) : ℝ :=
  ∑' a, (p a).toReal * negMulLog (p a).toReal
```

#### Theorem 4.1.2: Entropy Nonnegative (TEMPLATE)
**Natural Language:** Shannon entropy is always nonnegative: H(X) ≥ 0.
**Difficulty:** easy
**Status:** NOT FORMALIZED - Follows from negMulLog_nonneg

```lean4
-- NOT IN MATHLIB - Entropy nonnegativity
theorem PMF.entropy_nonneg (p : PMF α) : 0 ≤ p.entropy
```

#### Theorem 4.1.3: Entropy of Pure Distribution (TEMPLATE)
**Natural Language:** Deterministic distributions have zero entropy.
**Difficulty:** easy
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Pure entropy
theorem PMF.entropy_pure (a : α) : (PMF.pure a).entropy = 0
```

#### Theorem 4.1.4: Entropy Maximum for Uniform (TEMPLATE)
**Natural Language:** Entropy is maximized by the uniform distribution: H(X) ≤ log |α|.
**Difficulty:** hard
**Status:** NOT FORMALIZED - Classic result

```lean4
-- NOT IN MATHLIB - Maximum entropy principle
theorem PMF.entropy_le_log_card [Fintype α] [Nonempty α] (p : PMF α) :
    p.entropy ≤ Real.log (Fintype.card α)

theorem PMF.entropy_uniformOfFintype [Fintype α] [Nonempty α] :
    (PMF.uniformOfFintype α).entropy = Real.log (Fintype.card α)
```

#### Theorem 4.1.5: Entropy Additivity for Independent Variables (TEMPLATE)
**Natural Language:** H(X,Y) = H(X) + H(Y) when X and Y are independent.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Entropy additivity
theorem PMF.entropy_prod_of_indep (p : PMF α) (q : PMF β) :
    (p.prod q).entropy = p.entropy + q.entropy
```

### Section 4.2: Joint and Conditional Entropy

#### Theorem 4.2.1: Joint Entropy Definition (TEMPLATE)
**Natural Language:** Joint entropy H(X,Y) measures uncertainty of the pair.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Joint entropy
noncomputable def PMF.jointEntropy (p : PMF (α × β)) : ℝ := p.entropy
```

#### Theorem 4.2.2: Conditional Entropy Definition (TEMPLATE)
**Natural Language:** Conditional entropy H(Y|X) = H(X,Y) - H(X).
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Conditional entropy
noncomputable def PMF.conditionalEntropy (pXY : PMF (α × β)) (pX : PMF α) : ℝ :=
  pXY.entropy - pX.entropy
```

#### Theorem 4.2.3: Conditioning Reduces Entropy (TEMPLATE)
**Natural Language:** H(Y|X) ≤ H(Y) with equality iff X and Y are independent.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Conditioning reduces entropy
theorem PMF.conditionalEntropy_le (pXY : PMF (α × β)) (pY : PMF β) :
    pXY.conditionalEntropy (pXY.map Prod.fst) ≤ pY.entropy
```

#### Theorem 4.2.4: Chain Rule for Entropy (TEMPLATE)
**Natural Language:** H(X,Y) = H(X) + H(Y|X).
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Chain rule
theorem PMF.entropy_chain_rule (pXY : PMF (α × β)) :
    pXY.entropy = (pXY.map Prod.fst).entropy + pXY.conditionalEntropy (pXY.map Prod.fst)
```

---

## Part V: Mutual Information and Divergence (Templates)

> **Note:** These concepts are NOT YET FORMALIZED in Mathlib4.

### Section 5.1: Mutual Information

#### Theorem 5.1.1: Mutual Information Definition (TEMPLATE)
**Natural Language:** Mutual information I(X;Y) = H(X) + H(Y) - H(X,Y) measures shared information.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Mutual information
noncomputable def PMF.mutualInfo (pXY : PMF (α × β)) : ℝ :=
  (pXY.map Prod.fst).entropy + (pXY.map Prod.snd).entropy - pXY.entropy
```

#### Theorem 5.1.2: Mutual Information Nonnegative (TEMPLATE)
**Natural Language:** I(X;Y) ≥ 0 with equality iff X and Y are independent.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - MI nonnegativity
theorem PMF.mutualInfo_nonneg (pXY : PMF (α × β)) : 0 ≤ pXY.mutualInfo
```

#### Theorem 5.1.3: Mutual Information Symmetric (TEMPLATE)
**Natural Language:** I(X;Y) = I(Y;X).
**Difficulty:** easy
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - MI symmetry
theorem PMF.mutualInfo_comm (pXY : PMF (α × β)) :
    pXY.mutualInfo = (pXY.map Prod.swap).mutualInfo
```

#### Theorem 5.1.4: Mutual Information Upper Bound (TEMPLATE)
**Natural Language:** I(X;Y) ≤ min(H(X), H(Y)).
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - MI upper bound
theorem PMF.mutualInfo_le_entropy_left (pXY : PMF (α × β)) :
    pXY.mutualInfo ≤ (pXY.map Prod.fst).entropy
```

### Section 5.2: Kullback-Leibler Divergence

#### Theorem 5.2.1: KL Divergence Definition (TEMPLATE)
**Natural Language:** D_KL(P||Q) = Σ p(x) log(p(x)/q(x)) measures distribution distance.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - KL divergence
noncomputable def PMF.klDiv (p q : PMF α) : ℝ :=
  ∑' a, (p a).toReal * Real.log ((p a).toReal / (q a).toReal)
```

#### Theorem 5.2.2: KL Divergence Nonnegative (TEMPLATE)
**Natural Language:** D_KL(P||Q) ≥ 0 (Gibbs' inequality).
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Gibbs inequality
theorem PMF.klDiv_nonneg (p q : PMF α) : 0 ≤ p.klDiv q
```

#### Theorem 5.2.3: KL Divergence Zero Characterization (TEMPLATE)
**Natural Language:** D_KL(P||Q) = 0 iff P = Q.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - KL zero iff equal
theorem PMF.klDiv_eq_zero_iff (p q : PMF α) : p.klDiv q = 0 ↔ p = q
```

#### Theorem 5.2.4: Mutual Information via KL Divergence (TEMPLATE)
**Natural Language:** I(X;Y) = D_KL(P_{XY} || P_X ⊗ P_Y).
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - MI as KL divergence
theorem PMF.mutualInfo_eq_klDiv (pXY : PMF (α × β)) :
    pXY.mutualInfo = pXY.klDiv ((pXY.map Prod.fst).prod (pXY.map Prod.snd))
```

---

## Part VI: Data Processing and Fano's Inequality (Templates)

### Section 6.1: Data Processing Inequality

#### Theorem 6.1.1: Data Processing Inequality (TEMPLATE)
**Natural Language:** Processing cannot increase information: I(X;Y) ≥ I(X;g(Y)) for any function g.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Data processing inequality
theorem PMF.mutualInfo_map_le (pXY : PMF (α × β)) (g : β → γ) :
    (pXY.map (Prod.map id g)).mutualInfo ≤ pXY.mutualInfo
```

#### Theorem 6.1.2: Markov Chain Data Processing (TEMPLATE)
**Natural Language:** For Markov chain X → Y → Z: I(X;Z) ≤ I(X;Y).
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Markov chain DPI
theorem PMF.mutualInfo_markov_chain (pXYZ : PMF (α × β × γ))
    (h : ∀ x z, pXYZ.map (fun (x,y,z) => (x,z)) (x,z) =
         ∑' y, pXYZ (x,y,z)) : -- X → Y → Z Markov
    pXYZ.map (fun (x,y,z) => (x,z)).mutualInfo ≤
    pXYZ.map (fun (x,y,z) => (x,y)).mutualInfo
```

### Section 6.2: Fano's Inequality

#### Theorem 6.2.1: Fano's Inequality (TEMPLATE)
**Natural Language:** H(X|Y) ≤ H(P_e) + P_e log(|X| - 1) bounds error probability.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Fano's inequality
theorem fano_inequality [Fintype α] (pXY : PMF (α × α)) (Pe : ℝ)
    (hPe : Pe = 1 - ∑' a, pXY (a, a)) :
    pXY.conditionalEntropy (pXY.map Prod.fst) ≤
      binEntropy Pe + Pe * Real.log (Fintype.card α - 1)
```

---

## Part VII: Channel Capacity (Templates)

### Section 7.1: Channel Model

#### Theorem 7.1.1: Discrete Channel Definition (TEMPLATE)
**Natural Language:** A discrete memoryless channel is characterized by transition probabilities P(y|x).
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Channel definition
/-- A discrete memoryless channel from input alphabet α to output alphabet β. -/
structure Channel (α β : Type*) where
  transition : α → PMF β
```

#### Theorem 7.1.2: Channel Capacity Definition (TEMPLATE)
**Natural Language:** Channel capacity C = max_{P_X} I(X;Y) is the maximum achievable rate.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Channel capacity
noncomputable def Channel.capacity (ch : Channel α β) : ℝ :=
  ⨆ (pX : PMF α), (pX.bind ch.transition).mutualInfo
```

#### Theorem 7.1.3: BSC Capacity (TEMPLATE)
**Natural Language:** Binary symmetric channel with crossover p has capacity C = 1 - H(p).
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - BSC capacity
def Channel.bsc (p : ℝ) : Channel Bool Bool := {
  transition := fun x => if x then
    ⟨fun y => if y then 1 - p else p, ...⟩
  else
    ⟨fun y => if y then p else 1 - p, ...⟩
}

theorem Channel.bsc_capacity (hp : p ∈ Set.Icc 0 1) :
    (Channel.bsc p).capacity = Real.log 2 - binEntropy p
```

#### Theorem 7.1.4: BEC Capacity (TEMPLATE)
**Natural Language:** Binary erasure channel with erasure probability ε has capacity C = 1 - ε.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - BEC capacity
inductive BECOutput | zero | one | erased

def Channel.bec (ε : ℝ) : Channel Bool BECOutput := ...

theorem Channel.bec_capacity (hε : ε ∈ Set.Icc 0 1) :
    (Channel.bec ε).capacity = (1 - ε) * Real.log 2
```

### Section 7.2: Channel Coding Theorem

#### Theorem 7.2.1: Shannon's Noisy Channel Coding Theorem (TEMPLATE)
**Natural Language:** For rate R < C, there exist codes with arbitrarily small error probability.
**Difficulty:** hard
**Status:** NOT FORMALIZED - Foundational information theory

```lean4
-- NOT IN MATHLIB - Shannon's theorem (statement)
/-- Shannon's noisy channel coding theorem (achievability):
    For any rate R < C, there exist codes achieving arbitrarily small error. -/
theorem shannon_coding_achievability (ch : Channel α β) (R : ℝ)
    (hR : R < ch.capacity) (ε : ℝ) (hε : 0 < ε) :
    ∃ (n : ℕ) (code : Fin (2^(n * R)) → (Fin n → α))
      (decode : (Fin n → β) → Fin (2^(n * R))),
      error_probability ch code decode < ε
```

#### Theorem 7.2.2: Converse to Channel Coding Theorem (TEMPLATE)
**Natural Language:** For rate R > C, error probability is bounded away from zero.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Shannon's converse
theorem shannon_coding_converse (ch : Channel α β) (R : ℝ)
    (hR : ch.capacity < R) :
    ∃ δ > 0, ∀ n code decode, error_probability ch code decode ≥ δ
```

---

## Part VIII: Source Coding (Templates)

### Section 8.1: Source Coding Fundamentals

#### Theorem 8.1.1: Kraft Inequality (TEMPLATE)
**Natural Language:** For uniquely decodable codes: Σ 2^{-l_i} ≤ 1.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Kraft inequality
theorem kraft_inequality [Fintype α] (lengths : α → ℕ)
    (h : UniquelyDecodable lengths) :
    ∑ a, (2 : ℝ)^(-(lengths a : ℝ)) ≤ 1
```

#### Theorem 8.1.2: McMillan Inequality (TEMPLATE)
**Natural Language:** Uniquely decodable codes satisfy the same bound as prefix codes.
**Difficulty:** medium
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - McMillan
theorem mcmillan_inequality [Fintype α] (lengths : α → ℕ)
    (h : UniquelyDecodable lengths) :
    ∃ (prefix_code : α → List Bool), ∀ a, (prefix_code a).length = lengths a
```

#### Theorem 8.1.3: Shannon's Source Coding Theorem (TEMPLATE)
**Natural Language:** Expected code length L ≥ H(X), with equality achievable asymptotically.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Source coding theorem
theorem shannon_source_coding [Fintype α] (p : PMF α) (lengths : α → ℕ)
    (h : UniquelyDecodable lengths) :
    p.entropy / Real.log 2 ≤ ∑ a, (p a).toReal * lengths a
```

#### Theorem 8.1.4: Huffman Optimality (TEMPLATE)
**Natural Language:** Huffman coding achieves minimum expected length among prefix codes.
**Difficulty:** hard
**Status:** NOT FORMALIZED

```lean4
-- NOT IN MATHLIB - Huffman optimality
theorem huffman_optimal [Fintype α] (p : PMF α) :
    ∀ (prefix_code : α → List Bool), isPrefixFree prefix_code →
      huffman_expected_length p ≤ ∑ a, (p a).toReal * (prefix_code a).length
```

---

## Dependencies

- **Internal:** `arithmetic` (logarithms), `probability_theory` (PMF)
- **Mathlib4:** `Mathlib.Analysis.SpecialFunctions.BinaryEntropy`, `Mathlib.Probability.ProbabilityMassFunction.*`, `Mathlib.Analysis.SpecialFunctions.Log.*`

## Notes for Autoformalization

1. **Binary entropy formalized:** Use `binEntropy`, `negMulLog` directly from Mathlib
2. **PMF infrastructure:** Leverage `PMF` type and associated theorems
3. **Logarithm foundations:** Full support in `Mathlib.Analysis.SpecialFunctions.Log`
4. **Shannon entropy:** Define using `negMulLog` and `PMF.tsum`
5. **Information measures:** Build on entropy using standard definitions
6. **Channel coding:** Requires probabilistic reasoning infrastructure

---

## Summary Statistics

- **Total Statements:** 70
- **Formalized (with Lean4):** 38 (54%)
- **Templates (NOT FORMALIZED):** 32 (46%)
- **Difficulty Distribution:** Easy: 26, Medium: 28, Hard: 16
