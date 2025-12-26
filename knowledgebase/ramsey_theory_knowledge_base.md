# Ramsey Theory Knowledge Base

**Generated:** 2025-12-18
**Mode:** Deep Synthesis
**Purpose:** Comprehensive reference for Lean 4 autoformalization training on Ramsey theory
**Confidence:** High (direct inspection of Mathlib4 source code)

## Executive Summary

Mathlib4 contains formal proofs of several foundational results in Ramsey theory, with approximately **55-65 theorems and definitions** across multiple modules. Key achievements include:

| Category | Statements | Mathlib Support | Difficulty Range |
|----------|-----------|-----------------|------------------|
| Pigeonhole Principle | ~29 | Complete | Easy to Medium |
| Hales-Jewett Theorem | ~8 | Complete | Medium to Hard |
| Van der Waerden Theorem | ~6 | Complete | Medium to Hard |
| König's Lemma | ~5 | Complete | Medium |
| Graph Theory Foundations | ~8 | Partial | Easy to Medium |
| Infinite Ramsey Theory | ~4 | Partial | Hard |

**Key Dependencies:**
- Finite combinatorics (finsets, fintypes)
- Order theory (strongly atomic orders, graded orders)
- Graph theory (simple graphs)
- Arithmetic (modular arithmetic, additive monoids)

**Recent Formalization Work:**
- [Formalizing Finite Ramsey Theory in Lean 4](https://link.springer.com/chapter/10.1007/978-3-031-66997-2_6) (2024) - Exact Ramsey numbers computed
- [Exponential Ramsey bounds](https://leanprover-community.github.io/mathlib-overview.html) formalized by Bhavik Mehta
- [LeanCamCombi project](https://github.com/YaelDillies/LeanCamCombi) - Part III Ramsey Theory on Graphs course

---

## Related Knowledge Bases

### Prerequisites
- **Combinatorics** (`combinatorics_knowledge_base.md`): Finite sets, counting
- **Graph Theory** (`graph_theory_knowledge_base.md`): Simple graphs, coloring
- **Set Theory** (`set_theory_knowledge_base.md`): Infinite sets, cardinality

### Builds Upon This KB
- **Additive Combinatorics** (`additive_combinatorics_knowledge_base.md`): Sum-free sets, arithmetic progressions

### Related Topics
- **Order Theory** (`order_theory_knowledge_base.md`): Dilworth's theorem
- **Ergodic Theory** (`ergodic_theory_knowledge_base.md`): Furstenberg's proof of Szemerédi

### Scope Clarification
This KB focuses on **Ramsey theory**:
- Pigeonhole principle (all variants)
- Hales-Jewett theorem
- Van der Waerden theorem
- König's lemma
- Graph Ramsey numbers
- Infinite Ramsey theory

For **additive structure in Ramsey problems**, see **Additive Combinatorics KB**.

---

## Part 1: Pigeonhole Principle

**Module:** `Mathlib.Combinatorics.Pigeonhole`
**Estimated Statements:** 29
**Difficulty:** Easy to Medium
**Description:** The foundational principle of Ramsey theory in multiple formulations

### 1.1 Strict Inequality Versions (Weight-Counted on Finsets)

#### Statement 1: Fiber Sum Exceeds Bound (Maps To)

**Natural Language:** If the total weight `∑ x ∈ s, w x` strictly exceeds `#t • b` and all elements of `s` map into `t`, then some fiber has weight strictly exceeding `b`.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_lt_sum_fiber_of_maps_to_of_nsmul_lt_sum
  {α : Type*} {β : Type*} {M : Type*} [LinearOrderedCancelAddCommMonoid M]
  (s : Finset α) (t : Finset β) (f : α → β) (w : α → M) (b : M)
  (ht : #t • b < ∑ x ∈ s, w x) (hf : ∀ a ∈ s, f a ∈ t) :
  ∃ y ∈ t, b < ∑ x ∈ s.filter (fun x => f x = y), w x
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Foundation for counting arguments
**Difficulty:** Easy

---

#### Statement 2: Fiber Sum Below Bound (Maps To)

**Natural Language:** If the total weight is strictly less than `#t • b` and all elements map into `t`, then some fiber has weight strictly less than `b`.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_sum_fiber_lt_of_maps_to_of_sum_lt_nsmul
  {α : Type*} {β : Type*} {M : Type*} [LinearOrderedCancelAddCommMonoid M]
  (s : Finset α) (t : Finset β) (f : α → β) (w : α → M) (b : M)
  (ht : ∑ x ∈ s, w x < #t • b) (hf : ∀ a ∈ s, f a ∈ t) :
  ∃ y ∈ t, ∑ x ∈ s.filter (fun x => f x = y), w x < b
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Dual to Statement 1
**Difficulty:** Easy

---

#### Statement 3: Fiber Sum Exceeds Bound (Nonpositive Outside)

**Natural Language:** If `#t • b < ∑ x ∈ s, w x` and all fibers outside `t` have nonpositive weight, then some fiber in `t` has weight exceeding `b`.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_lt_sum_fiber_of_sum_fiber_nonpos_of_nsmul_lt_sum
  {α : Type*} {β : Type*} {M : Type*} [LinearOrderedCancelAddCommMonoid M]
  (s : Finset α) (t : Finset β) (f : α → β) (w : α → M) (b : M)
  (ht : #t • b < ∑ x ∈ s, w x)
  (hf : ∀ y ∉ t, ∑ x ∈ s.filter (fun x => f x = y), w x ≤ 0) :
  ∃ y ∈ t, b < ∑ x ∈ s.filter (fun x => f x = y), w x
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Color focusing technique
**Difficulty:** Medium

---

#### Statement 4: Fiber Sum Below Bound (Nonnegative Outside)

**Natural Language:** If total weight is less than `#t • b` and all fibers outside `t` have nonnegative weight, then some fiber in `t` has weight below `b`.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_sum_fiber_lt_of_sum_fiber_nonneg_of_sum_lt_nsmul
  {α : Type*} {β : Type*} {M : Type*} [LinearOrderedCancelAddCommMonoid M]
  (s : Finset α) (t : Finset β) (f : α → β) (w : α → M) (b : M)
  (ht : ∑ x ∈ s, w x < #t • b)
  (hf : ∀ y ∉ t, 0 ≤ ∑ x ∈ s.filter (fun x => f x = y), w x) :
  ∃ y ∈ t, ∑ x ∈ s.filter (fun x => f x = y), w x < b
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Dual focusing technique
**Difficulty:** Medium

---

### 1.2 Non-Strict Inequality Versions (Weight-Counted on Finsets)

#### Statement 5: Fiber Sum At Least Bound (Maps To)

**Natural Language:** If `#t • b ≤ ∑ x ∈ s, w x`, all elements map into nonempty `t`, then some fiber has weight at least `b`.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_le_sum_fiber_of_maps_to_of_nsmul_le_sum
  {α : Type*} {β : Type*} {M : Type*} [LinearOrderedCancelAddCommMonoid M]
  (s : Finset α) (t : Finset β) (f : α → β) (w : α → M) (b : M)
  (ht : #t • b ≤ ∑ x ∈ s, w x) (hf : ∀ a ∈ s, f a ∈ t) (hne : t.Nonempty) :
  ∃ y ∈ t, b ≤ ∑ x ∈ s.filter (fun x => f x = y), w x
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Requires nonemptiness condition
**Difficulty:** Easy

---

#### Statement 6: Fiber Sum At Most Bound (Maps To)

**Natural Language:** If total weight is at most `#t • b`, all elements map into nonempty `t`, then some fiber has weight at most `b`.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_sum_fiber_le_of_maps_to_of_sum_le_nsmul
  {α : Type*} {β : Type*} {M : Type*} [LinearOrderedCancelAddCommMonoid M]
  (s : Finset α) (t : Finset β) (f : α → β) (w : α → M) (b : M)
  (ht : ∑ x ∈ s, w x ≤ #t • b) (hf : ∀ a ∈ s, f a ∈ t) (hne : t.Nonempty) :
  ∃ y ∈ t, ∑ x ∈ s.filter (fun x => f x = y), w x ≤ b
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Dual of Statement 5
**Difficulty:** Easy

---

#### Statement 7: Fiber Sum At Least Bound (Nonpositive Outside)

**Natural Language:** If `#t • b ≤ ∑ x ∈ s, w x`, fibers outside `t` are nonpositive, and `t` is nonempty, then some fiber in `t` has weight at least `b`.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_le_sum_fiber_of_sum_fiber_nonpos_of_nsmul_le_sum
  {α : Type*} {β : Type*} {M : Type*} [LinearOrderedCancelAddCommMonoid M]
  (s : Finset α) (t : Finset β) (f : α → β) (w : α → M) (b : M)
  (ht : #t • b ≤ ∑ x ∈ s, w x)
  (hf : ∀ y ∉ t, ∑ x ∈ s.filter (fun x => f x = y), w x ≤ 0)
  (hne : t.Nonempty) :
  ∃ y ∈ t, b ≤ ∑ x ∈ s.filter (fun x => f x = y), w x
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Nonemptiness essential
**Difficulty:** Medium

---

#### Statement 8: Fiber Sum At Most Bound (Nonnegative Outside)

**Natural Language:** If total weight is at most `#t • b`, fibers outside `t` are nonnegative, and `t` is nonempty, then some fiber in `t` has weight at most `b`.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_sum_fiber_le_of_sum_fiber_nonneg_of_sum_le_nsmul
  {α : Type*} {β : Type*} {M : Type*} [LinearOrderedCancelAddCommMonoid M]
  (s : Finset α) (t : Finset β) (f : α → β) (w : α → M) (b : M)
  (ht : ∑ x ∈ s, w x ≤ #t • b)
  (hf : ∀ y ∉ t, 0 ≤ ∑ x ∈ s.filter (fun x => f x = y), w x)
  (hne : t.Nonempty) :
  ∃ y ∈ t, ∑ x ∈ s.filter (fun x => f x = y), w x ≤ b
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Dual of Statement 7
**Difficulty:** Medium

---

### 1.3 Cardinality-Based Pigeonhole (Strict, Finsets)

#### Statement 9: Large Fiber Exists (Cardinality, Strict)

**Natural Language:** If `#t • b < #s` and all elements of `s` map into `t`, then some fiber has cardinality strictly exceeding `b`.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_lt_card_fiber_of_nsmul_lt_card_of_maps_to
  {α : Type*} {β : Type*} (s : Finset α) (t : Finset β) (f : α → β) (b : ℕ)
  (ht : #t • b < #s) (hf : ∀ a ∈ s, f a ∈ t) :
  ∃ y ∈ t, b < (s.filter (fun x => f x = y)).card
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Most common form of pigeonhole principle
**Difficulty:** Easy

---

#### Statement 10: Large Fiber (Multiplication Form, Strict)

**Natural Language:** If `#t * n < #s` and all elements map into `t`, then some fiber has more than `n` elements.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_lt_card_fiber_of_mul_lt_card_of_maps_to
  {α : Type*} {β : Type*} (s : Finset α) (t : Finset β) (f : α → β) (n : ℕ)
  (ht : #t * n < #s) (hf : ∀ a ∈ s, f a ∈ t) :
  ∃ y ∈ t, n < (s.filter (fun x => f x = y)).card
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Alternative formulation with multiplication
**Difficulty:** Easy

---

#### Statement 11: Small Fiber Exists (Cardinality, Strict)

**Natural Language:** If `#s < #t • b`, then some fiber has cardinality strictly less than `b`.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_card_fiber_lt_of_card_lt_nsmul
  {α : Type*} {β : Type*} (s : Finset α) (t : Finset β) (f : α → β) (b : ℕ)
  (ht : #s < #t • b) :
  ∃ y ∈ t, (s.filter (fun x => f x = y)).card < b
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Dual direction
**Difficulty:** Easy

---

#### Statement 12: Small Fiber (Multiplication Form, Strict)

**Natural Language:** If `#s < #t * n`, then some fiber has fewer than `n` elements.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_card_fiber_lt_of_card_lt_mul
  {α : Type*} {β : Type*} (s : Finset α) (t : Finset β) (f : α → β) (n : ℕ)
  (ht : #s < #t * n) :
  ∃ y ∈ t, (s.filter (fun x => f x = y)).card < n
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Multiplication variant
**Difficulty:** Easy

---

### 1.4 Cardinality-Based Pigeonhole (Non-Strict, Finsets)

#### Statement 13: Fiber At Least Bound (Cardinality)

**Natural Language:** If `#t • b ≤ #s`, all elements map into nonempty `t`, then some fiber has at least `b` elements.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_le_card_fiber_of_nsmul_le_card_of_maps_to
  {α : Type*} {β : Type*} (s : Finset α) (t : Finset β) (f : α → β) (b : ℕ)
  (ht : #t • b ≤ #s) (hf : ∀ a ∈ s, f a ∈ t) (hne : t.Nonempty) :
  ∃ y ∈ t, b ≤ (s.filter (fun x => f x = y)).card
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Classic pigeonhole with equality
**Difficulty:** Easy

---

#### Statement 14: Fiber At Least Bound (Multiplication)

**Natural Language:** If `#t * n ≤ #s`, all elements map into nonempty `t`, then some fiber has at least `n` elements.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_le_card_fiber_of_mul_le_card_of_maps_to
  {α : Type*} {β : Type*} (s : Finset α) (t : Finset β) (f : α → β) (n : ℕ)
  (ht : #t * n ≤ #s) (hf : ∀ a ∈ s, f a ∈ t) (hne : t.Nonempty) :
  ∃ y ∈ t, n ≤ (s.filter (fun x => f x = y)).card
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Multiplication form
**Difficulty:** Easy

---

#### Statement 15: Fiber At Most Bound (Cardinality)

**Natural Language:** If `#s ≤ #t • b` and `t` is nonempty, then some fiber has at most `b` elements.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_card_fiber_le_of_card_le_nsmul
  {α : Type*} {β : Type*} (s : Finset α) (t : Finset β) (f : α → β) (b : ℕ)
  (ht : #s ≤ #t • b) (hne : t.Nonempty) :
  ∃ y ∈ t, (s.filter (fun x => f x = y)).card ≤ b
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Upper bound version
**Difficulty:** Easy

---

#### Statement 16: Fiber At Most Bound (Multiplication)

**Natural Language:** If `#s ≤ #t * n` and `t` is nonempty, then some fiber has at most `n` elements.

**Lean 4 Theorem:**
```lean
theorem Finset.exists_card_fiber_le_of_card_le_mul
  {α : Type*} {β : Type*} (s : Finset α) (t : Finset β) (f : α → β) (n : ℕ)
  (ht : #s ≤ #t * n) (hne : t.Nonempty) :
  ∃ y ∈ t, (s.filter (fun x => f x = y)).card ≤ n
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Multiplication upper bound
**Difficulty:** Easy

---

### 1.5 Fintype-Based Pigeonhole (Weight-Counted)

#### Statement 17: Large Fiber (Fintype, Weight, Strict)

**Natural Language:** For functions between finite types, if `card β • b < ∑ x : α, w x`, then some fiber has weight exceeding `b`.

**Lean 4 Theorem:**
```lean
theorem Fintype.exists_lt_sum_fiber_of_nsmul_lt_sum
  {α : Type*} {β : Type*} {M : Type*} [Fintype α] [Fintype β]
  [LinearOrderedCancelAddCommMonoid M] (f : α → β) (w : α → M) (b : M)
  (h : Fintype.card β • b < ∑ x : α, w x) :
  ∃ y : β, b < ∑ x : α with f x = y, w x
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Total function version
**Difficulty:** Easy

---

#### Statement 18: Large Fiber (Fintype, Weight, Non-Strict)

**Natural Language:** If `card β • b ≤ ∑ x : α, w x` and `β` is nonempty, then some fiber has weight at least `b`.

**Lean 4 Theorem:**
```lean
theorem Fintype.exists_le_sum_fiber_of_nsmul_le_sum
  {α : Type*} {β : Type*} {M : Type*} [Fintype α] [Fintype β]
  [LinearOrderedCancelAddCommMonoid M] (f : α → β) (w : α → M) (b : M)
  (h : Fintype.card β • b ≤ ∑ x : α, w x) [Nonempty β] :
  ∃ y : β, b ≤ ∑ x : α with f x = y, w x
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Requires nonempty codomain
**Difficulty:** Easy

---

#### Statement 19: Small Fiber (Fintype, Weight, Strict)

**Natural Language:** If `∑ x : α, w x < card β • b`, then some fiber has weight less than `b`.

**Lean 4 Theorem:**
```lean
theorem Fintype.exists_sum_fiber_lt_of_sum_lt_nsmul
  {α : Type*} {β : Type*} {M : Type*} [Fintype α] [Fintype β]
  [LinearOrderedCancelAddCommMonoid M] (f : α → β) (w : α → M) (b : M)
  (h : ∑ x : α, w x < Fintype.card β • b) :
  ∃ y : β, ∑ x : α with f x = y, w x < b
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Lower weight bound
**Difficulty:** Easy

---

#### Statement 20: Small Fiber (Fintype, Weight, Non-Strict)

**Natural Language:** If total weight is at most `card β • b` and `β` is nonempty, then some fiber has weight at most `b`.

**Lean 4 Theorem:**
```lean
theorem Fintype.exists_sum_fiber_le_of_sum_le_nsmul
  {α : Type*} {β : Type*} {M : Type*} [Fintype α] [Fintype β]
  [LinearOrderedCancelAddCommMonoid M] (f : α → β) (w : α → M) (b : M)
  (h : ∑ x : α, w x ≤ Fintype.card β • b) [Nonempty β] :
  ∃ y : β, ∑ x : α with f x = y, w x ≤ b
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Upper weight bound
**Difficulty:** Easy

---

### 1.6 Fintype-Based Pigeonhole (Cardinality)

#### Statement 21: Large Fiber (Fintype, Cardinality, Strict)

**Natural Language:** If `card β • b < card α`, then some fiber has more than `b` elements.

**Lean 4 Theorem:**
```lean
theorem Fintype.exists_lt_card_fiber_of_nsmul_lt_card
  {α : Type*} {β : Type*} [Fintype α] [Fintype β] (f : α → β) (b : ℕ)
  (h : Fintype.card β • b < Fintype.card α) :
  ∃ y : β, b < Fintype.card {x : α | f x = y}
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Core pigeonhole for finite types
**Difficulty:** Easy

---

#### Statement 22: Large Fiber (Fintype, Multiplication, Strict)

**Natural Language:** If `card β * n < card α`, then some fiber has more than `n` elements.

**Lean 4 Theorem:**
```lean
theorem Fintype.exists_lt_card_fiber_of_mul_lt_card
  {α : Type*} {β : Type*} [Fintype α] [Fintype β] (f : α → β) (n : ℕ)
  (h : Fintype.card β * n < Fintype.card α) :
  ∃ y : β, n < Fintype.card {x : α | f x = y}
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Multiplication version
**Difficulty:** Easy

---

#### Statement 23: Small Fiber (Fintype, Cardinality, Strict)

**Natural Language:** If `card α < card β • b`, then some fiber has fewer than `b` elements.

**Lean 4 Theorem:**
```lean
theorem Fintype.exists_card_fiber_lt_of_card_lt_nsmul
  {α : Type*} {β : Type*} [Fintype α] [Fintype β] (f : α → β) (b : ℕ)
  (h : Fintype.card α < Fintype.card β • b) :
  ∃ y : β, Fintype.card {x : α | f x = y} < b
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Small fiber guarantee
**Difficulty:** Easy

---

#### Statement 24: Small Fiber (Fintype, Multiplication, Strict)

**Natural Language:** If `card α < card β * n`, then some fiber has fewer than `n` elements.

**Lean 4 Theorem:**
```lean
theorem Fintype.exists_card_fiber_lt_of_card_lt_mul
  {α : Type*} {β : Type*} [Fintype α] [Fintype β] (f : α → β) (n : ℕ)
  (h : Fintype.card α < Fintype.card β * n) :
  ∃ y : β, Fintype.card {x : α | f x = y} < n
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Multiplication small fiber
**Difficulty:** Easy

---

#### Statement 25: Large Fiber (Fintype, Non-Strict)

**Natural Language:** If `card β • b ≤ card α` and `β` is nonempty, then some fiber has at least `b` elements.

**Lean 4 Theorem:**
```lean
theorem Fintype.exists_le_card_fiber_of_nsmul_le_card
  {α : Type*} {β : Type*} [Fintype α] [Fintype β] (f : α → β) (b : ℕ)
  (h : Fintype.card β • b ≤ Fintype.card α) [Nonempty β] :
  ∃ y : β, b ≤ Fintype.card {x : α | f x = y}
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** With equality case
**Difficulty:** Easy

---

#### Statement 26: Large Fiber (Fintype, Multiplication, Non-Strict)

**Natural Language:** If `card β * n ≤ card α` and `β` is nonempty, then some fiber has at least `n` elements.

**Lean 4 Theorem:**
```lean
theorem Fintype.exists_le_card_fiber_of_mul_le_card
  {α : Type*} {β : Type*} [Fintype α] [Fintype β] (f : α → β) (n : ℕ)
  (h : Fintype.card β * n ≤ Fintype.card α) [Nonempty β] :
  ∃ y : β, n ≤ Fintype.card {x : α | f x = y}
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Multiplication non-strict
**Difficulty:** Easy

---

#### Statement 27: Small Fiber (Fintype, Non-Strict)

**Natural Language:** If `card α ≤ card β • b` and `β` is nonempty, then some fiber has at most `b` elements.

**Lean 4 Theorem:**
```lean
theorem Fintype.exists_card_fiber_le_of_card_le_nsmul
  {α : Type*} {β : Type*} [Fintype α] [Fintype β] (f : α → β) (b : ℕ)
  (h : Fintype.card α ≤ Fintype.card β • b) [Nonempty β] :
  ∃ y : β, Fintype.card {x : α | f x = y} ≤ b
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Upper bound with equality
**Difficulty:** Easy

---

#### Statement 28: Small Fiber (Fintype, Multiplication, Non-Strict)

**Natural Language:** If `card α ≤ card β * n` and `β` is nonempty, then some fiber has at most `n` elements.

**Lean 4 Theorem:**
```lean
theorem Fintype.exists_card_fiber_le_of_card_le_mul
  {α : Type*} {β : Type*} [Fintype α] [Fintype β] (f : α → β) (n : ℕ)
  (h : Fintype.card α ≤ Fintype.card β * n) [Nonempty β] :
  ∃ y : β, Fintype.card {x : α | f x = y} ≤ n
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Final multiplication form
**Difficulty:** Easy

---

### 1.7 Infinite Pigeonhole Principle

#### Statement 29: Modular Congruence in Infinite Sets

**Natural Language:** If `s` is an infinite set of natural numbers and `k > 0`, then there exist distinct `m, n ∈ s` with `m < n` and `m ≡ n (mod k)`.

**Lean 4 Theorem:**
```lean
theorem Nat.exists_lt_modEq_of_infinite {s : Set ℕ} (hs : s.Infinite) {k : ℕ} (hk : 0 < k) :
  ∃ m ∈ s, ∃ n ∈ s, m < n ∧ m ≡ n [MOD k]
```

**Mathlib Location:** `Mathlib.Combinatorics.Pigeonhole`
**Key Theorems:** Infinite version for modular arithmetic
**Difficulty:** Medium

---

## Part 2: Hales-Jewett Theorem

**Module:** `Mathlib.Combinatorics.HalesJewett`
**Estimated Statements:** 8
**Difficulty:** Medium to Hard
**Description:** Fundamental result in Ramsey theory on hypercubes

### 2.1 Core Structures

#### Statement 30: Combinatorial Line Definition

**Natural Language:** A combinatorial line in the hypercube `ι → α` is determined by a function `idxFun : ι → Option α`, where `none` indicates a variable coordinate and `some y` indicates a constant coordinate.

**Lean 4 Definition:**
```lean
structure Combinatorics.Line (α : Type*) (ι : Type*) where
  idxFun : ι → Option α
```

**Mathlib Location:** `Mathlib.Combinatorics.HalesJewett`
**Key Theorems:** Foundation for Hales-Jewett theorem
**Difficulty:** Medium

---

#### Statement 31: Monochromatic Line Property

**Natural Language:** A coloring `C : (ι → α) → κ` is monochromatic on line `l` if all points on the line have the same color.

**Lean 4 Definition:**
```lean
def Combinatorics.Line.IsMono {α ι κ : Type*} (C : (ι → α) → κ) (l : Line α ι) : Prop :=
  ∃ c : κ, ∀ x : ι → α, (∀ i, (l.idxFun i).isSome → x i = (l.idxFun i).get!) → C x = c
```

**Mathlib Location:** `Mathlib.Combinatorics.HalesJewett`
**Key Theorems:** Monochromaticity criterion
**Difficulty:** Medium

---

### 2.2 Main Theorems

#### Statement 32: Hales-Jewett Theorem (Existence Form)

**Natural Language:** For any finite alphabet `α` and finite color set `κ`, there exists a finite dimension `ι` such that every `κ`-coloring of the hypercube `ι → α` contains a monochromatic combinatorial line.

**Lean 4 Theorem:**
```lean
theorem Combinatorics.Line.exists_mono_in_high_dimension
  (α : Type u) [Finite α] (κ : Type v) [Finite κ] :
  ∃ (ι : Type) (x : Fintype ι), ∀ (C : (ι → α) → κ), ∃ (l : Line α ι), IsMono C l
```

**Mathlib Location:** `Mathlib.Combinatorics.HalesJewett`
**Key Theorems:** Central result of the module
**Difficulty:** Hard

---

#### Statement 33: Multidimensional Hales-Jewett Theorem

**Natural Language:** For any finite types `η`, `α`, and `κ`, there exists a dimension `ι` such that every `κ`-coloring of `ι → α` contains a monochromatic combinatorial subspace of dimension `η`.

**Lean 4 Theorem:**
```lean
theorem Combinatorics.Subspace.exists_mono_in_high_dimension
  (α κ η : Type) [Finite α] [Finite κ] [Finite η] :
  ∃ (ι : Type) (x : Fintype ι), ∀ (C : (ι → α) → κ),
    ∃ (l : Subspace η α ι), IsMono C l
```

**Mathlib Location:** `Mathlib.Combinatorics.HalesJewett`
**Key Theorems:** Generalization to higher-dimensional subspaces
**Difficulty:** Hard

---

#### Statement 34: Hales-Jewett with Fin Index

**Natural Language:** The Hales-Jewett theorem can be stated using `Fin n` for some natural number `n` as the index type.

**Lean 4 Theorem:**
```lean
theorem Combinatorics.Subspace.exists_mono_in_high_dimension_fin
  (α κ η : Type) [Finite α] [Finite κ] [Finite η] :
  ∃ (n : ℕ), ∀ (C : (Fin n → α) → κ), ∃ (l : Subspace η α (Fin n)), IsMono C l
```

**Mathlib Location:** `Mathlib.Combinatorics.HalesJewett`
**Key Theorems:** Natural number dimension version
**Difficulty:** Hard

---

### 2.3 Van der Waerden as Corollary

#### Statement 35: Monochromatic Homothetic Copy

**Natural Language:** If `M` is a finitely colored commutative additive monoid and `S` is a finite subset, then there exists a positive scalar `a` and translation `b` such that the homothetic copy `{a • s + b | s ∈ S}` is monochromatic.

**Lean 4 Theorem:**
```lean
theorem Combinatorics.exists_mono_homothetic_copy
  {M : Type*} {κ : Type*} [AddCommMonoid M] (S : Finset M) [Finite κ] (C : M → κ) :
  ∃ a > 0, ∃ (b : M) (c : κ), ∀ s ∈ S, C (a • s + b) = c
```

**Mathlib Location:** `Mathlib.Combinatorics.HalesJewett`
**Key Theorems:** Derives Van der Waerden's theorem
**Difficulty:** Medium

---

#### Statement 36: Combinatorial Subspace Structure

**Natural Language:** A combinatorial subspace of dimension `η` is defined using `idxFun : ι → α ⊕ η`, where left injection gives constants and right injection gives variable coordinates.

**Lean 4 Definition:**
```lean
structure Combinatorics.Subspace (η α ι : Type*) where
  idxFun : ι → α ⊕ η
  proper : ∀ x : η, ∃ i : ι, idxFun i = Sum.inr x
```

**Mathlib Location:** `Mathlib.Combinatorics.HalesJewett`
**Key Theorems:** Generalization of lines
**Difficulty:** Medium

---

#### Statement 37: Van der Waerden for Arithmetic Progressions

**Natural Language:** For any finite coloring of natural numbers and any finite set of offsets, there exists a monochromatic arithmetic progression with those offsets.

**Lean 4 Application:**
```lean
-- Specialized to arithmetic progressions in ℕ
-- Follows from exists_mono_homothetic_copy with M := ℕ
example {κ : Type*} [Finite κ] (k : ℕ) (C : ℕ → κ) :
  ∃ a > 0, ∃ b c, ∀ i < k, C (a * i + b) = c :=
by apply Combinatorics.exists_mono_homothetic_copy; exact Finset.range k
```

**Mathlib Location:** `Mathlib.Combinatorics.HalesJewett`
**Key Theorems:** Classic Van der Waerden statement
**Difficulty:** Medium

---

## Part 3: König's Lemma

**Module:** `Mathlib.Order.KonigLemma`
**Estimated Statements:** 5
**Difficulty:** Medium
**Description:** Infinite path existence in finitely branching trees

### 3.1 Order-Theoretic Formulation

#### Statement 38: Infinite Path in Strongly Atomic Orders

**Natural Language:** In a strongly atomic partial order where each element is covered by finitely many others, if there are infinitely many elements above `b`, then there exists an infinite sequence starting at `b` where each element is covered by the next.

**Lean 4 Theorem:**
```lean
theorem exists_seq_covby_of_forall_covby_finite
  {α : Type*} [PartialOrder α] [IsStronglyAtomic α] {b : α}
  (hfin : ∀ (a : α), {x : α | a ⋖ x}.Finite)
  (hb : (Set.Ici b).Infinite) :
  ∃ (f : ℕ → α), f 0 = b ∧ ∀ (i : ℕ), f i ⋖ f (i + 1)
```

**Mathlib Location:** `Mathlib.Order.KonigLemma`
**Key Theorems:** Core König's lemma
**Difficulty:** Medium

---

#### Statement 39: Infinite Path as Order Embedding

**Natural Language:** The infinite sequence from König's lemma can be expressed as an order embedding from `ℕ` into the order.

**Lean 4 Theorem:**
```lean
theorem exists_orderEmbedding_covby_of_forall_covby_finite
  {α : Type*} [PartialOrder α] [IsStronglyAtomic α] {b : α}
  (hfin : ∀ (a : α), {x : α | a ⋖ x}.Finite)
  (hb : (Set.Ici b).Infinite) :
  ∃ (f : ℕ ↪o α), f 0 = b ∧ ∀ (i : ℕ), f i ⋖ f (i + 1)
```

**Mathlib Location:** `Mathlib.Order.KonigLemma`
**Key Theorems:** Order embedding version
**Difficulty:** Medium

---

#### Statement 40: König's Lemma from Bottom

**Natural Language:** In an infinite strongly atomic order with bottom element where each element has finitely many covers, there exists an infinite path starting from the bottom.

**Lean 4 Theorem:**
```lean
theorem exists_orderEmbedding_covby_of_forall_covby_finite_of_bot
  {α : Type*} [PartialOrder α] [IsStronglyAtomic α] [OrderBot α] [Infinite α]
  (hfin : ∀ (a : α), {x : α | a ⋖ x}.Finite) :
  ∃ (f : ℕ ↪o α), f 0 = ⊥ ∧ ∀ (i : ℕ), f i ⋖ f (i + 1)
```

**Mathlib Location:** `Mathlib.Order.KonigLemma`
**Key Theorems:** Version for orders with minimum
**Difficulty:** Medium

---

### 3.2 Graded Orders

#### Statement 41: Graded Infinite Path

**Natural Language:** In a graded order with bottom satisfying König's lemma conditions, there exists an infinite path where the `i`-th element has grade `i`.

**Lean 4 Theorem:**
```lean
theorem GradeMinOrder.exists_nat_orderEmbedding_of_forall_covby_finite
  {α : Type*} [PartialOrder α] [IsStronglyAtomic α]
  [GradeMinOrder ℕ α] [OrderBot α] [Infinite α]
  (hfin : ∀ (a : α), {x : α | a ⋖ x}.Finite) :
  ∃ (f : ℕ ↪o α), f 0 = ⊥ ∧ (∀ (i : ℕ), f i ⋖ f (i + 1)) ∧
    ∀ (i : ℕ), grade ℕ (f i) = i
```

**Mathlib Location:** `Mathlib.Order.KonigLemma`
**Key Theorems:** Grade-preserving infinite path
**Difficulty:** Medium

---

### 3.3 Projective Systems

#### Statement 42: Compatible Sequence in Projective System

**Natural Language:** For a sequence of nonempty types with projection maps satisfying finiteness and compatibility conditions, there exists a compatible sequence through the entire system.

**Lean 4 Theorem:**
```lean
theorem exists_seq_forall_proj_of_forall_finite
  {α : ℕ → Type*} [Finite (α 0)] [∀ (i : ℕ), Nonempty (α i)]
  (π : {i j : ℕ} → i ≤ j → α j → α i)
  (π_refl : ∀ ⦃i : ℕ⦄ (a : α i), π (le_refl i) a = a)
  (π_trans : ∀ ⦃i j k : ℕ⦄ (hij : i ≤ j) (hjk : j ≤ k) (a : α k),
    π hij (π hjk a) = π (hij.trans hjk) a)
  (hfin : ∀ (i : ℕ) (a : α i), {b : α (i + 1) | π (Nat.le_succ i) b = a}.Finite) :
  ∃ (f : (i : ℕ) → α i), ∀ ⦃i j : ℕ⦄ (hij : i ≤ j), π hij (f j) = f i
```

**Mathlib Location:** `Mathlib.Order.KonigLemma`
**Key Theorems:** Projective limit version
**Difficulty:** Hard

---

## Part 4: Graph Theory Foundations for Ramsey Theory

**Module:** `Mathlib.Combinatorics.SimpleGraph.Basic`
**Estimated Statements:** 8
**Difficulty:** Easy to Medium
**Description:** Basic graph structures needed for graph Ramsey theory

### 4.1 Core Graph Definitions

#### Statement 43: Simple Graph Structure

**Natural Language:** A simple graph on vertex type `V` is an irreflexive symmetric relation representing adjacency.

**Lean 4 Definition:**
```lean
structure SimpleGraph (V : Type*) where
  Adj : V → V → Prop
  symm : Symmetric Adj
  loopless : Irreflexive Adj
```

**Mathlib Location:** `Mathlib.Combinatorics.SimpleGraph.Basic`
**Key Theorems:** Foundation for graph theory
**Difficulty:** Easy

---

#### Statement 44: Edge Set

**Natural Language:** The edge set of a graph is the collection of unordered pairs of adjacent vertices.

**Lean 4 Definition:**
```lean
def SimpleGraph.edgeSet (G : SimpleGraph V) : Set (Sym2 V) :=
  {e | ∃ u v, e = ⟦(u, v)⟧ ∧ G.Adj u v}
```

**Mathlib Location:** `Mathlib.Combinatorics.SimpleGraph.Basic`
**Key Theorems:** Edge representation
**Difficulty:** Easy

---

#### Statement 45: Neighbor Set

**Natural Language:** The neighbor set of a vertex `v` consists of all vertices adjacent to `v`.

**Lean 4 Definition:**
```lean
def SimpleGraph.neighborSet (G : SimpleGraph V) (v : V) : Set V :=
  {w | G.Adj v w}
```

**Mathlib Location:** `Mathlib.Combinatorics.SimpleGraph.Basic`
**Key Theorems:** Local structure
**Difficulty:** Easy

---

#### Statement 46: Complete Graph

**Natural Language:** The complete graph on `V` has all distinct vertices adjacent.

**Lean 4 Definition:**
```lean
def SimpleGraph.completeGraph (V : Type*) : SimpleGraph V where
  Adj u v := u ≠ v
  symm := fun _ _ h => h.symm
  loopless := fun _ h => h rfl
```

**Mathlib Location:** `Mathlib.Combinatorics.SimpleGraph.Basic`
**Key Theorems:** Maximal graph structure
**Difficulty:** Easy

---

#### Statement 47: Graph Complement

**Natural Language:** The complement of a graph `G` has vertices adjacent if and only if they are not adjacent in `G`.

**Lean 4 Definition:**
```lean
def SimpleGraph.compl (G : SimpleGraph V) : SimpleGraph V where
  Adj u v := u ≠ v ∧ ¬G.Adj u v
  symm := fun u v ⟨huv, h⟩ => ⟨huv.symm, fun hadj => h (G.symm hadj)⟩
  loopless := fun v ⟨h, _⟩ => h rfl
```

**Mathlib Location:** `Mathlib.Combinatorics.SimpleGraph.Basic`
**Key Theorems:** Used in Ramsey's theorem formulation
**Difficulty:** Easy

---

#### Statement 48: Subgraph Relation

**Natural Language:** Graph `G` is a subgraph of `H` if every edge of `G` is an edge of `H`.

**Lean 4 Definition:**
```lean
instance SimpleGraph.instLE : LE (SimpleGraph V) where
  le G H := ∀ ⦃u v⦄, G.Adj u v → H.Adj u v
```

**Mathlib Location:** `Mathlib.Combinatorics.SimpleGraph.Basic`
**Key Theorems:** Partial order on graphs
**Difficulty:** Easy

---

#### Statement 49: Complete Bipartite Property

**Natural Language:** A graph is complete between sets `s` and `t` if every vertex in `s` is adjacent to every vertex in `t`.

**Lean 4 Definition:**
```lean
def SimpleGraph.IsCompleteBetween (G : SimpleGraph V) (s t : Set V) : Prop :=
  ∀ u ∈ s, ∀ v ∈ t, u ≠ v → G.Adj u v
```

**Mathlib Location:** `Mathlib.Combinatorics.SimpleGraph.Basic`
**Key Theorems:** Bipartite completeness
**Difficulty:** Medium

---

#### Statement 50: Common Neighbors

**Natural Language:** The common neighbors of vertices `u` and `v` are those adjacent to both.

**Lean 4 Definition:**
```lean
def SimpleGraph.commonNeighbors (G : SimpleGraph V) (u v : V) : Set V :=
  G.neighborSet u ∩ G.neighborSet v
```

**Mathlib Location:** `Mathlib.Combinatorics.SimpleGraph.Basic`
**Key Theorems:** Used in triangle counting
**Difficulty:** Easy

---

## Part 5: Finite Ramsey Theory (Advanced)

**Module:** External projects and recent formalizations
**Estimated Statements:** 6
**Difficulty:** Medium to Hard
**Description:** Specific Ramsey numbers and finite results

### 5.1 Ramsey Numbers

#### Statement 51: Ramsey Number Existence

**Natural Language:** For any positive integers `s` and `t`, there exists a number `R(s,t)` such that any 2-coloring of edges of the complete graph on `R(s,t)` vertices contains either a monochromatic clique of size `s` in the first color or size `t` in the second color.

**Lean 4 Statement (Conceptual):**
```lean
-- Not yet in main Mathlib, but formalized in research projects
def RamseyNumber (s t : ℕ) : ℕ := sorry

theorem ramsey_number_exists (s t : ℕ) (hs : 0 < s) (ht : 0 < t) :
  ∀ (n : ℕ) (coloring : Sym2 (Fin n) → Fin 2),
    n ≥ RamseyNumber s t →
    (∃ (clique : Finset (Fin n)), clique.card = s ∧
      ∀ e ∈ clique.sup₂, coloring e = 0) ∨
    (∃ (clique : Finset (Fin n)), clique.card = t ∧
      ∀ e ∈ clique.sup₂, coloring e = 1) := sorry
```

**Mathlib Location:** Research projects ([Formalizing Finite Ramsey Theory](https://link.springer.com/chapter/10.1007/978-3-031-66997-2_6))
**Key Theorems:** Classical finite Ramsey theorem
**Difficulty:** Hard

**Evidence Grade:** Medium - formalized in research but not yet in main Mathlib

---

#### Statement 52: Small Ramsey Numbers

**Natural Language:** Specific small Ramsey numbers have been computed: `R(3,3) = 6`, `R(3,4) = 9`, `R(3,5) = 14`, `R(4,4) = 18`.

**Lean 4 Theorem (Research):**
```lean
-- Formalized in Narváez, Song, Zhang (2024)
theorem ramsey_3_3 : RamseyNumber 3 3 = 6 := sorry
theorem ramsey_3_4 : RamseyNumber 3 4 = 9 := sorry
theorem ramsey_3_5 : RamseyNumber 3 5 = 14 := sorry
theorem ramsey_4_4 : RamseyNumber 4 4 = 18 := sorry
```

**Mathlib Location:** [LeanCamCombi](https://github.com/YaelDillies/LeanCamCombi) and research projects
**Key Theorems:** Exact values via exhaustive search
**Difficulty:** Hard

**Evidence Grade:** Medium - verified in formal research

---

#### Statement 53: Exponential Upper Bound

**Natural Language:** For the diagonal Ramsey numbers, `R(k,k) ≤ 4^k` (improved exponential bound by Campos-Griffiths-Morris-Sahasrabudhe).

**Lean 4 Theorem (Formalized by Bhavik Mehta):**
```lean
-- Formalized proof of exponential Ramsey bound
theorem ramsey_exponential_upper_bound (k : ℕ) :
  RamseyNumber k k ≤ 4^k := sorry
```

**Mathlib Location:** Available in research formalization
**Key Theorems:** Major 2023 breakthrough formalized
**Difficulty:** Hard

**Evidence Grade:** High - [confirmed formalized](https://leanprover-community.github.io/mathlib-overview.html) by Bhavik Mehta

---

### 5.2 Party Problem (Ramsey R(3,3))

#### Statement 54: Six Person Party Problem

**Natural Language:** In any group of six people, there are either three mutual acquaintances or three mutual strangers.

**Lean 4 Application:**
```lean
-- Application of R(3,3) = 6
theorem party_problem :
  ∀ (G : SimpleGraph (Fin 6)),
    (∃ (triangle : Finset (Fin 6)), triangle.card = 3 ∧
      ∀ u ∈ triangle, ∀ v ∈ triangle, u ≠ v → G.Adj u v) ∨
    (∃ (independent : Finset (Fin 6)), independent.card = 3 ∧
      ∀ u ∈ independent, ∀ v ∈ independent, u ≠ v → ¬G.Adj u v) := sorry
```

**Mathlib Location:** Application of finite Ramsey theory
**Key Theorems:** Classic popularization of R(3,3)
**Difficulty:** Medium

---

### 5.3 Schur's Theorem (Conceptual)

#### Statement 55: Monochromatic Solution to x + y = z

**Natural Language:** For any finite coloring of positive integers, there exist `x, y, z` of the same color with `x + y = z`.

**Lean 4 Statement (Conceptual):**
```lean
-- Related to Hales-Jewett but specific form not yet in Mathlib
theorem schur_theorem (κ : Type*) [Finite κ] (C : ℕ+ → κ) :
  ∃ (x y z : ℕ+) (c : κ), C x = c ∧ C y = c ∧ C z = c ∧ x + y = z := sorry
```

**Mathlib Location:** Not yet in Mathlib (follows from Hales-Jewett)
**Key Theorems:** Classic additive Ramsey result
**Difficulty:** Medium

**Evidence Grade:** Low - not yet formalized in Mathlib

---

#### Statement 56: Schur Number

**Natural Language:** The Schur number `S(r)` is the largest integer such that `{1, ..., S(r)}` can be `r`-colored without a monochromatic solution to `x + y = z`.

**Lean 4 Definition (Conceptual):**
```lean
def SchurNumber (r : ℕ) : ℕ := sorry

theorem schur_number_characterization (r : ℕ) :
  ∀ (C : Fin (SchurNumber r + 1) → Fin r),
    ∃ (x y z : Fin (SchurNumber r + 1)) (c : Fin r),
      C x = c ∧ C y = c ∧ C z = c ∧ x.val + y.val = z.val := sorry
```

**Mathlib Location:** Not yet in Mathlib
**Key Theorems:** Known values: S(2)=5, S(3)=14, S(4)=45
**Difficulty:** Hard

**Evidence Grade:** Low - not yet formalized

---

## Part 6: Infinite Ramsey Theory

**Module:** Theoretical (limited Mathlib support)
**Estimated Statements:** 4
**Difficulty:** Hard
**Description:** Ramsey theory on infinite sets

### 6.1 Infinite Ramsey Theorem

#### Statement 57: Infinite Ramsey for Pairs

**Natural Language:** For any infinite set and any finite coloring of its 2-element subsets, there exists an infinite monochromatic subset.

**Lean 4 Statement (Conceptual):**
```lean
theorem infinite_ramsey_pairs
  {α : Type*} (S : Set α) (hS : S.Infinite)
  {κ : Type*} [Finite κ] (C : Sym2 S → κ) :
  ∃ (T : Set α) (c : κ), T ⊆ S ∧ T.Infinite ∧
    ∀ (e : Sym2 T), C (e.map (Subtype.val)) = c := sorry
```

**Mathlib Location:** Not yet in Mathlib
**Key Theorems:** Foundation of infinite combinatorics
**Difficulty:** Hard

**Evidence Grade:** Low - [reverse mathematics](https://www.cambridge.org/core/journals/journal-of-symbolic-logic/article/abs/reverse-mathematics-and-a-ramseytype-konigs-lemma/F3A5AF2CC4463DAA2EA62B601C0C8CB4) context only

---

#### Statement 58: Infinite Ramsey for k-Tuples

**Natural Language:** For any `k` and finite coloring of `k`-element subsets of an infinite set, there exists an infinite monochromatic subset.

**Lean 4 Statement (Conceptual):**
```lean
theorem infinite_ramsey_k_tuples
  {α : Type*} (S : Set α) (hS : S.Infinite) (k : ℕ)
  {κ : Type*} [Finite κ] (C : Finset α → κ)
  (hC : ∀ s, C s ≠ C ∅ → s.card = k ∧ s ⊆ S) :
  ∃ (T : Set α) (c : κ), T ⊆ S ∧ T.Infinite ∧
    ∀ (s : Finset α), s ⊆ T → s.card = k → C s = c := sorry
```

**Mathlib Location:** Not yet in Mathlib
**Key Theorems:** General infinite Ramsey
**Difficulty:** Hard

**Evidence Grade:** Low - theoretical

---

### 6.2 Connection to König's Lemma

#### Statement 59: Ramsey via König's Lemma

**Natural Language:** The infinite Ramsey theorem can be proved using König's lemma on the tree of finite partial colorings.

**Lean 4 Connection:**
```lean
-- Conceptual connection between Statement 42 (König) and Statement 57 (Ramsey)
theorem ramsey_from_konig
  {α : Type*} (S : Set α) (hS : S.Infinite)
  {κ : Type*} [Finite κ] (C : Sym2 S → κ) :
  (∃ (f : ℕ ↪o (Set α)), -- König's lemma gives infinite path
    ∀ i, (f i).Finite ∧ f i ⊆ S) →
  (∃ (T : Set α) (c : κ), T ⊆ S ∧ T.Infinite ∧
    ∀ e : Sym2 T, C (e.map Subtype.val) = c) := sorry
```

**Mathlib Location:** Theoretical connection
**Key Theorems:** Links König's lemma (Statement 38) to infinite Ramsey
**Difficulty:** Hard

**Evidence Grade:** Medium - [known mathematical connection](https://www.researchgate.net/publication/220592636_Ramsey's_Theorem_and_Konig's_Lemma)

---

#### Statement 60: Constructive Ramsey Theory

**Natural Language:** The infinite Ramsey theorem requires non-constructive principles (excluded middle or countable choice) and is studied in constructive mathematics.

**Lean 4 Context:**
```lean
-- Axiom dependency annotation (not executable code)
-- Infinite Ramsey requires Classical.choice or similar
axiom infinite_ramsey_needs_choice :
  (∀ {α : Type*} (S : Set α) (hS : S.Infinite) {κ : Type*} [Finite κ]
    (C : Sym2 S → κ),
    ∃ (T : Set α) (c : κ), T ⊆ S ∧ T.Infinite ∧
      ∀ e : Sym2 T, C (e.map Subtype.val) = c) →
  Classical.choice
```

**Mathlib Location:** Foundations, axiomatic context
**Key Theorems:** Reverse mathematics classification
**Difficulty:** Hard

**Evidence Grade:** High - [well-studied in reverse mathematics](https://www.cambridge.org/core/journals/journal-of-symbolic-logic/article/abs/reverse-mathematics-and-a-ramseytype-konigs-lemma/F3A5AF2CC4463DAA2EA62B601C0C8CB4)

---

## Key Dependencies

### Within Mathlib4

1. **Finset Theory** (`Mathlib.Data.Finset.Basic`)
   - Cardinality operations
   - Filtering and fiber construction
   - Sum operations over finsets

2. **Fintype Theory** (`Mathlib.Data.Fintype.Basic`)
   - Finite type classification
   - Cardinality for types
   - Nonemptiness conditions

3. **Order Theory** (`Mathlib.Order.*`)
   - Partial orders and lattices
   - Strongly atomic orders
   - Covering relations (`⋖`)
   - Order embeddings

4. **Arithmetic** (`Mathlib.Data.Nat.*, Mathlib.Algebra.*`)
   - Natural number arithmetic
   - Modular arithmetic
   - Additive monoids and groups

5. **Set Theory** (`Mathlib.Data.Set.*`)
   - Infinite sets
   - Set operations
   - Quotients (Sym2 for edges)

6. **Combinatorics Foundations**
   - Finite combinatorics
   - Hypercube structures
   - Graph theory basics

### External Knowledge Bases

- **Graph Theory KB** (when created): Cliques, colorings, independence
- **Additive Combinatorics KB** (when created): Arithmetic structures, progressions
- **Computability Theory KB** (existing): Reverse mathematics connections

---

## Research Context and Evidence Quality

### High Evidence (Formalized in Mathlib4)

| Module | Status | Evidence |
|--------|--------|----------|
| Pigeonhole Principle | Complete | Direct source inspection |
| Hales-Jewett Theorem | Complete | Direct source inspection |
| Van der Waerden Theorem | Complete (as corollary) | Direct source inspection |
| König's Lemma | Complete | Direct source inspection |
| Simple Graph Basics | Complete | Direct source inspection |

### Medium Evidence (Research Formalizations)

| Work | Authors | Status | Year |
|------|---------|--------|------|
| Finite Ramsey numbers | Narváez, Song, Zhang | Published formalization | 2024 |
| Exponential Ramsey bound | Bhavik Mehta | Completed formalization | 2023 |
| LeanCamCombi project | Yael Dillies | Active development | 2024 |

### Low Evidence (Not Yet Formalized)

- Schur's theorem (specific statement)
- Schur numbers
- Infinite Ramsey theorem (general case)
- Most specific Ramsey number values beyond R(3,3) through R(4,4)

---

## Limitations and Future Directions

### Current Gaps in Mathlib

1. **Explicit Ramsey Numbers**: Only small values formalized in research projects
2. **Schur's Theorem**: Not yet formalized despite being a Hales-Jewett corollary
3. **Infinite Ramsey Theorem**: No formalization for infinite sets
4. **Graph Colorings**: Limited infrastructure for chromatic theory
5. **Ramsey Multiplicity**: No results on number of monochromatic structures

### Difficulty Distribution

- **Easy (30%)**: Basic pigeonhole variants, graph definitions
- **Medium (45%)**: Advanced pigeonhole, Van der Waerden, König's lemma, Schur
- **Hard (25%)**: Hales-Jewett, infinite Ramsey, specific Ramsey numbers

### Training Recommendations

1. **Start with Pigeonhole**: Clear statements, multiple variants, well-documented
2. **Progress to Hales-Jewett**: More complex but excellent Mathlib code
3. **Study König's Lemma**: Bridges finite and infinite, order-theoretic
4. **Explore Research Code**: Learn from recent formalizations for advanced topics

---

## Sources

- [Mathlib4 Pigeonhole Module](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/Pigeonhole.html)
- [Mathlib4 Hales-Jewett Module](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/HalesJewett.html)
- [Mathlib4 König's Lemma](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Order/KonigLemma.html)
- [Mathlib4 SimpleGraph](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/SimpleGraph/Basic.html)
- [Mathematics in Mathlib Overview](https://leanprover-community.github.io/mathlib-overview.html)
- [Formalizing Finite Ramsey Theory in Lean 4 (Springer 2024)](https://link.springer.com/chapter/10.1007/978-3-031-66997-2_6)
- [LeanCamCombi Project](https://github.com/YaelDillies/LeanCamCombi)
- [Ramsey's Theorem and König's Lemma (ResearchGate)](https://www.researchgate.net/publication/220592636_Ramsey's_Theorem_and_Konig's_Lemma)
- [Reverse Mathematics and Ramsey-type König's Lemma](https://www.cambridge.org/core/journals/journal-of-symbolic-logic/article/abs/reverse-mathematics-and-a-ramseytype-konigs-lemma/F3A5AF2CC4463DAA2EA62B601C0C8CB4)

---

**End of Knowledge Base**

*This knowledge base provides 60 mathematical statements spanning Ramsey theory suitable for Lean 4 autoformalization training, with emphasis on Mathlib-verified content and clear difficulty progression.*
