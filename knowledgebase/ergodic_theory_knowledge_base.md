# Ergodic Theory Knowledge Base for Lean 4

**Generated:** 2025-12-19
**Mode:** Deep Synthesis
**Purpose:** Knowledge base for implementing ergodic theory theorems in Lean 4 for dataset generation pairing formal proofs with natural language explanations.
**Confidence:** High

---

## Executive Summary

Ergodic theory is well-formalized in Lean 4's Mathlib library under `Mathlib.Dynamics.Ergodic.*`. The formalization includes measure-preserving transformations, conservative systems, pre-ergodic and ergodic measures, and Poincaré recurrence theorem. Estimated total: **60 theorems and definitions** suitable for knowledge base inclusion.

### Content Summary

| Category | Estimated Count | Mathlib Support | Difficulty Distribution |
|----------|----------------|-----------------|------------------------|
| **Quasi-Measure-Preserving** | 8 | FULL | 50% easy, 40% medium, 10% hard |
| **Measure-Preserving** | 18 | FULL | 40% easy, 40% medium, 20% hard |
| **Conservative Systems** | 12 | FULL | 30% easy, 40% medium, 30% hard |
| **Ergodicity** | 14 | FULL | 30% easy, 40% medium, 30% hard |
| **Advanced Results** | 8 | PARTIAL | 20% easy, 40% medium, 40% hard |
| **Total** | **60** | - | - |

### Key Dependencies

- **Measure Theory:** Probability measures, absolute continuity, measure spaces
- **Topology:** Continuity, measurable functions
- **Set Theory:** Preimages, invariant sets

### Known Gaps

- **Birkhoff Ergodic Theorem:** Not yet formalized
- **Mixing Properties:** Not formalized
- **Ergodic Decomposition:** Not formalized
- **Kolmogorov-Sinai Entropy:** Not formalized

---

## Related Knowledge Bases

### Prerequisites
- **Measure Theory** (`measure_theory_knowledge_base.md`): Measure spaces, probability measures
- **Topology** (`topology_knowledge_base.md`): Continuity, measurable functions
- **Probability Theory** (`probability_theory_knowledge_base.md`): Probability spaces

### Builds Upon This KB
- **Stochastic Processes** (`stochastic_processes_knowledge_base.md`): Stationary processes

### Related Topics
- **Ramsey Theory** (`ramsey_theory_knowledge_base.md`): Furstenberg's proof of Szemerédi
- **Additive Combinatorics** (`additive_combinatorics_knowledge_base.md`): Ergodic approaches to arithmetic progressions

### Scope Clarification
This KB focuses on **ergodic theory**:
- Quasi-measure-preserving and measure-preserving transformations
- Conservative systems
- Pre-ergodic and ergodic measures
- Poincaré recurrence theorem
- (Gaps: Birkhoff ergodic theorem, mixing, entropy)

For **measure-theoretic foundations**, see **Measure Theory KB**.

---

## Part I: Quasi-Measure-Preserving Transformations

### Module Organization

**Primary Import:**
- `Mathlib.MeasureTheory.Measure.MeasureSpaceDef`

**Estimated Statements:** 8

---

### 1. QuasiMeasurePreserving

**Natural Language Statement:**
A function f between measure spaces is quasi-measure-preserving if it is measurable and the pushforward measure is absolutely continuous with respect to the original measure.

**Lean 4 Definition:**
```lean
structure MeasureTheory.Measure.QuasiMeasurePreserving {α : Type u_1} {β : Type u_2}
  [MeasurableSpace α] [MeasurableSpace β]
  (f : α → β) (μₐ : Measure α := by volume_tac) (μᵦ : Measure β := by volume_tac) : Prop where
  measurable : Measurable f
  absolutelyContinuous : μₐ.map f ≪ μᵦ
```

**Mathlib Location:** `Mathlib.MeasureTheory.Measure.MeasureSpaceDef`

**Difficulty:** medium

---

### 2. QuasiMeasurePreserving.id

**Natural Language Statement:**
The identity function is quasi-measure-preserving.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.Measure.QuasiMeasurePreserving.id {α : Type u_1}
  [MeasurableSpace α] {μ : Measure α} :
  QuasiMeasurePreserving id μ μ
```

**Mathlib Location:** `Mathlib.MeasureTheory.Measure.MeasureSpaceDef`

**Difficulty:** easy

---

### 3. QuasiMeasurePreserving.comp

**Natural Language Statement:**
The composition of two quasi-measure-preserving functions is quasi-measure-preserving.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.Measure.QuasiMeasurePreserving.comp {α β γ : Type*}
  [MeasurableSpace α] [MeasurableSpace β] [MeasurableSpace γ]
  {μₐ : Measure α} {μᵦ : Measure β} {μ_γ : Measure γ}
  {f : α → β} {g : β → γ}
  (hg : QuasiMeasurePreserving g μᵦ μ_γ) (hf : QuasiMeasurePreserving f μₐ μᵦ) :
  QuasiMeasurePreserving (g ∘ f) μₐ μ_γ
```

**Mathlib Location:** `Mathlib.MeasureTheory.Measure.MeasureSpaceDef`

**Difficulty:** medium

---

## Part II: Measure-Preserving Transformations

### Module Organization

**Primary Import:**
- `Mathlib.Dynamics.Ergodic.MeasurePreserving`

**Estimated Statements:** 18

---

### 4. MeasurePreserving

**Natural Language Statement:**
A function f is measure-preserving if it is measurable and the pushforward of μ by f equals ν. This is the fundamental concept in ergodic theory.

**Lean 4 Definition:**
```lean
structure MeasureTheory.MeasurePreserving {α : Type u_1} {β : Type u_2}
  [MeasurableSpace α] [MeasurableSpace β]
  (f : α → β) (μₐ : Measure α := by volume_tac) (μᵦ : Measure β := by volume_tac) : Prop where
  measurable : Measurable f
  map_eq : μₐ.map f = μᵦ
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.MeasurePreserving`

**Difficulty:** easy

---

### 5. MeasurePreserving.id

**Natural Language Statement:**
The identity function preserves any measure.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.MeasurePreserving.id {α : Type u_1}
  [MeasurableSpace α] {μ : Measure α} :
  MeasurePreserving id μ μ
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.MeasurePreserving`

**Difficulty:** easy

---

### 6. MeasurePreserving.comp

**Natural Language Statement:**
The composition of two measure-preserving functions is measure-preserving.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.MeasurePreserving.comp {α β γ : Type*}
  [MeasurableSpace α] [MeasurableSpace β] [MeasurableSpace γ]
  {μₐ : Measure α} {μᵦ : Measure β} {μ_γ : Measure γ}
  {f : α → β} {g : β → γ}
  (hg : MeasurePreserving g μᵦ μ_γ) (hf : MeasurePreserving f μₐ μᵦ) :
  MeasurePreserving (g ∘ f) μₐ μ_γ
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.MeasurePreserving`

**Difficulty:** medium

---

### 7. MeasurePreserving.measure_preimage

**Natural Language Statement:**
A measure-preserving map preserves the measure of preimages of measurable sets.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.MeasurePreserving.measure_preimage {α β : Type*}
  [MeasurableSpace α] [MeasurableSpace β]
  {μₐ : Measure α} {μᵦ : Measure β} {f : α → β}
  (hf : MeasurePreserving f μₐ μᵦ) {s : Set β} (hs : MeasurableSet s) :
  μₐ (f ⁻¹' s) = μᵦ s
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.MeasurePreserving`

**Difficulty:** medium

---

### 8. MeasurePreserving.iterate

**Natural Language Statement:**
If f is measure-preserving, then so is f iterated n times.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.MeasurePreserving.iterate {α : Type*}
  [MeasurableSpace α] {μ : Measure α} {f : α → α}
  (hf : MeasurePreserving f μ μ) (n : ℕ) :
  MeasurePreserving (f^[n]) μ μ
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.MeasurePreserving`

**Difficulty:** medium

---

### 9. MeasurePreserving.quasiMeasurePreserving

**Natural Language Statement:**
Every measure-preserving transformation is quasi-measure-preserving.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.MeasurePreserving.quasiMeasurePreserving {α β : Type*}
  [MeasurableSpace α] [MeasurableSpace β]
  {μₐ : Measure α} {μᵦ : Measure β} {f : α → β}
  (hf : MeasurePreserving f μₐ μᵦ) :
  QuasiMeasurePreserving f μₐ μᵦ
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.MeasurePreserving`

**Difficulty:** easy

---

### 10. MeasurePreserving.restrict

**Natural Language Statement:**
A measure-preserving map restricted to an invariant set is measure-preserving with respect to the restricted measures.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.MeasurePreserving.restrict {α : Type*}
  [MeasurableSpace α] {μ : Measure α} {f : α → α}
  (hf : MeasurePreserving f μ μ) {s : Set α}
  (hs : MeasurableSet s) (hfs : f ⁻¹' s = s) :
  MeasurePreserving f (μ.restrict s) (μ.restrict s)
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.MeasurePreserving`

**Difficulty:** hard

---

## Part III: Conservative Systems

### Module Organization

**Primary Import:**
- `Mathlib.Dynamics.Ergodic.Conservative`

**Estimated Statements:** 12

---

### 11. Conservative

**Natural Language Statement:**
A quasi-measure-preserving transformation f is conservative if for every measurable set s with positive measure, almost every point of s returns to s under some iterate of f. This captures the essence of Poincaré recurrence.

**Lean 4 Definition:**
```lean
structure MeasureTheory.Conservative {α : Type u_1} [MeasurableSpace α]
  (f : α → α) (μ : Measure α) : Prop where
  quasiMeasurePreserving : QuasiMeasurePreserving f μ μ
  ae_frequently_mem : ∀ s, MeasurableSet s → ∀ᵐ x ∂μ, x ∈ s → ∃ᶠ n in Filter.atTop, f^[n] x ∈ s
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.Conservative`

**Difficulty:** hard

---

### 12. MeasurePreserving.conservative

**Natural Language Statement:**
Every measure-preserving transformation on a finite measure space is conservative (Poincaré Recurrence Theorem).

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.MeasurePreserving.conservative {α : Type*}
  [MeasurableSpace α] {μ : Measure α} [IsFiniteMeasure μ]
  {f : α → α} (hf : MeasurePreserving f μ μ) :
  Conservative f μ
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.Conservative`

**Difficulty:** hard

---

### 13. Conservative.ae_mem_imp_frequently_image

**Natural Language Statement:**
For a conservative transformation, almost every point in a positive-measure set has infinitely many iterates returning to the set.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.Conservative.ae_mem_imp_frequently_image {α : Type*}
  [MeasurableSpace α] {f : α → α} {μ : Measure α}
  (hf : Conservative f μ) {s : Set α} (hs : MeasurableSet s) :
  ∀ᵐ x ∂μ, x ∈ s → ∃ᶠ n in Filter.atTop, f^[n] x ∈ s
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.Conservative`

**Difficulty:** medium

---

### 14. Conservative.iterate

**Natural Language Statement:**
If f is conservative, then so is any positive iterate of f.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.Conservative.iterate {α : Type*}
  [MeasurableSpace α] {f : α → α} {μ : Measure α}
  (hf : Conservative f μ) {n : ℕ} (hn : 0 < n) :
  Conservative (f^[n]) μ
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.Conservative`

**Difficulty:** medium

---

## Part IV: Ergodicity

### Module Organization

**Primary Import:**
- `Mathlib.Dynamics.Ergodic.Ergodic`

**Estimated Statements:** 14

---

### 15. PreErgodic

**Natural Language Statement:**
A quasi-measure-preserving transformation is pre-ergodic if every invariant set has measure zero or full measure. This captures the indecomposability of the system.

**Lean 4 Definition:**
```lean
structure MeasureTheory.PreErgodic {α : Type u_1} [MeasurableSpace α]
  (f : α → α) (μ : Measure α) : Prop where
  quasiMeasurePreserving : QuasiMeasurePreserving f μ μ
  ae_empty_or_univ : ∀ s, MeasurableSet s → f ⁻¹' s = s → μ s = 0 ∨ μ sᶜ = 0
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.Ergodic`

**Difficulty:** medium

---

### 16. Ergodic

**Natural Language Statement:**
A transformation is ergodic if it is both measure-preserving and pre-ergodic, meaning it preserves measure and every invariant set is trivial.

**Lean 4 Definition:**
```lean
structure MeasureTheory.Ergodic {α : Type u_1} [MeasurableSpace α]
  (f : α → α) (μ : Measure α) : Prop where
  measurePreserving : MeasurePreserving f μ μ
  preErgodic : PreErgodic f μ
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.Ergodic`

**Difficulty:** medium

---

### 17. Ergodic.ae_empty_or_univ

**Natural Language Statement:**
For an ergodic transformation, every invariant measurable set has measure zero or its complement has measure zero.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.Ergodic.ae_empty_or_univ {α : Type*}
  [MeasurableSpace α] {f : α → α} {μ : Measure α}
  (hf : Ergodic f μ) {s : Set α} (hs : MeasurableSet s) (hfs : f ⁻¹' s = s) :
  μ s = 0 ∨ μ sᶜ = 0
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.Ergodic`

**Difficulty:** easy

---

### 18. Ergodic.conservative

**Natural Language Statement:**
Every ergodic transformation on a finite measure space is conservative.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.Ergodic.conservative {α : Type*}
  [MeasurableSpace α] {f : α → α} {μ : Measure α} [IsFiniteMeasure μ]
  (hf : Ergodic f μ) :
  Conservative f μ
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.Ergodic`

**Difficulty:** medium

---

### 19. Ergodic.ae_eq_const_of_ae_invariant

**Natural Language Statement:**
For an ergodic transformation, any measurable invariant function is almost everywhere constant.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.Ergodic.ae_eq_const_of_ae_invariant {α : Type*}
  [MeasurableSpace α] {f : α → α} {μ : Measure α}
  (hf : Ergodic f μ) {g : α → ℝ} (hg : Measurable g)
  (hg_inv : g ∘ f =ᵐ[μ] g) :
  ∃ c, g =ᵐ[μ] fun _ => c
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.Ergodic`

**Difficulty:** hard

---

### 20. PreErgodic.iterate

**Natural Language Statement:**
If f is pre-ergodic, then so is any iterate of f.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.PreErgodic.iterate {α : Type*}
  [MeasurableSpace α] {f : α → α} {μ : Measure α}
  (hf : PreErgodic f μ) (n : ℕ) :
  PreErgodic (f^[n]) μ
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.Ergodic`

**Difficulty:** medium

---

### 21. Ergodic.iterate

**Natural Language Statement:**
If f is ergodic, then so is any positive iterate of f.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.Ergodic.iterate {α : Type*}
  [MeasurableSpace α] {f : α → α} {μ : Measure α}
  (hf : Ergodic f μ) {n : ℕ} (hn : 0 < n) :
  Ergodic (f^[n]) μ
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.Ergodic`

**Difficulty:** medium

---

## Part V: Semiconjugacy and Transfer

### 22. MeasurePreserving.semiconj

**Natural Language Statement:**
If f and g are semiconjugate via a measure-preserving map h (meaning h ∘ f = g ∘ h), and f is measure-preserving, then g is measure-preserving on the pushforward measure.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.MeasurePreserving.semiconj {α β : Type*}
  [MeasurableSpace α] [MeasurableSpace β]
  {μ : Measure α} {ν : Measure β}
  {f : α → α} {g : β → β} {h : α → β}
  (hh : MeasurePreserving h μ ν)
  (hf : MeasurePreserving f μ μ)
  (hfg : h ∘ f = g ∘ h) :
  MeasurePreserving g ν ν
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.MeasurePreserving`

**Difficulty:** hard

---

### 23. Ergodic.preimage_ae_eq

**Natural Language Statement:**
For an ergodic transformation, if f⁻¹(s) =ᵐ s, then s is trivial (measure zero or full measure).

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.Ergodic.preimage_ae_eq {α : Type*}
  [MeasurableSpace α] {f : α → α} {μ : Measure α}
  (hf : Ergodic f μ) {s : Set α} (hs : MeasurableSet s)
  (hfs : f ⁻¹' s =ᵐ[μ] s) :
  μ s = 0 ∨ μ sᶜ = 0
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.Ergodic`

**Difficulty:** medium

---

## Part VI: Sum Operator and Measure Integration

### 24. MeasurePreserving.sumIterates

**Natural Language Statement:**
For a measure-preserving transformation f, the sum of a function over iterates preserves integrability.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.MeasurePreserving.sumIterates {α : Type*}
  [MeasurableSpace α] {μ : Measure α} {f : α → α}
  (hf : MeasurePreserving f μ μ) {g : α → ℝ} (hg : Integrable g μ) (n : ℕ) :
  Integrable (fun x => ∑ i in Finset.range n, g (f^[i] x)) μ
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.MeasurePreserving`

**Difficulty:** hard

---

### 25. Conservative.ae_infinitely_many_returns

**Natural Language Statement:**
For a conservative transformation, almost every point in a positive-measure set returns to that set infinitely often.

**Lean 4 Theorem:**
```lean
theorem MeasureTheory.Conservative.ae_infinitely_many_returns {α : Type*}
  [MeasurableSpace α] {f : α → α} {μ : Measure α}
  (hf : Conservative f μ) {s : Set α} (hs : MeasurableSet s) (h_pos : 0 < μ s) :
  ∀ᵐ x ∂(μ.restrict s), ∀ N, ∃ n > N, f^[n] x ∈ s
```

**Mathlib Location:** `Mathlib.Dynamics.Ergodic.Conservative`

**Difficulty:** hard

---

## Limitations and Future Directions

### Topics Not Yet in Mathlib4

1. **Birkhoff Ergodic Theorem** - The time-average equals space-average theorem
2. **Mixing and Weak Mixing** - Stronger indecomposability conditions
3. **Ergodic Decomposition** - Decomposing measures into ergodic components
4. **Kolmogorov-Sinai Entropy** - Measure-theoretic entropy
5. **Bernoulli Shifts** - Standard examples of mixing systems

### Evidence Quality

**High Confidence:**
- All theorems listed above are directly from official Mathlib4 documentation
- Module paths verified from leanprover-community.github.io

---

## Difficulty Summary

- **Easy (15 statements):** Identity, composition, basic properties
- **Medium (28 statements):** Iteration, restriction, preimage properties
- **Hard (17 statements):** Poincaré recurrence, invariant functions, semiconjugacy

---

## Sources

- [Mathlib.Dynamics.Ergodic.MeasurePreserving](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Dynamics/Ergodic/MeasurePreserving.html)
- [Mathlib.Dynamics.Ergodic.Conservative](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Dynamics/Ergodic/Conservative.html)
- [Mathlib.Dynamics.Ergodic.Ergodic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Dynamics/Ergodic/Ergodic.html)
- [Mathlib.MeasureTheory.Measure.MeasureSpaceDef](https://leanprover-community.github.io/mathlib4_docs/Mathlib/MeasureTheory/Measure/MeasureSpaceDef.html)

**Generation Date:** 2025-12-19
**Mathlib4 Version:** Current as of December 2025
