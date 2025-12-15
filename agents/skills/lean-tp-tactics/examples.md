# Lean 4 Tactics Examples

Working code examples demonstrating tactic usage patterns.

---

## Basic Proof Structure

```lean
-- Minimal tactic proof
theorem trivial_true : True := by trivial

-- Multi-step proof
theorem and_comm (hp : p) (hq : q) : q ∧ p := by
  constructor
  · exact hq
  · exact hp

-- Same with semicolons
theorem and_comm' (hp : p) (hq : q) : q ∧ p := by
  constructor; exact hq; exact hp
```

---

## Rewriting Examples

```lean
-- Basic rewrite
example (h : x = y) : x + z = y + z := by rw [h]

-- Reverse direction
example (h : x = y) : y + z = x + z := by rw [← h]

-- Chain multiple rewrites
example (h1 : a = b) (h2 : b = c) (h3 : c = d) : a = d := by
  rw [h1, h2, h3]

-- Rewrite in hypothesis
example (h1 : a = b) (h2 : a + c = e) : b + c = e := by
  rw [← h1] at h2
  exact h2

-- simp with custom lemmas
example (h : a = b) (h2 : c = d) : a + c = b + d := by
  simp [h, h2]
```

---

## Case Analysis Examples

```lean
-- Or elimination
example (h : p ∨ q) : q ∨ p := by
  cases h with
  | inl hp => right; exact hp
  | inr hq => left; exact hq

-- And elimination
example (h : p ∧ q) : p := by
  cases h with
  | intro hp hq => exact hp

-- Shorter: obtain pattern
example (h : p ∧ q) : q := by
  obtain ⟨hp, hq⟩ := h
  exact hq

-- Boolean cases
example (b : Bool) : b = true ∨ b = false := by
  cases b
  · right; rfl
  · left; rfl
```

---

## Induction Examples

```lean
-- Natural number induction
theorem add_zero (n : Nat) : n + 0 = n := by
  induction n with
  | zero => rfl
  | succ n ih =>
    simp [Nat.add_succ]
    exact ih

-- List induction
theorem length_append (xs ys : List α) :
    (xs ++ ys).length = xs.length + ys.length := by
  induction xs with
  | nil => simp
  | cons x xs ih => simp [ih, Nat.add_assoc]

-- With generalization
theorem add_comm (m n : Nat) : m + n = n + m := by
  induction n generalizing m with
  | zero => simp
  | succ n ih =>
    simp [Nat.add_succ, Nat.succ_add]
    exact ih m
```

---

## Working with Existentials

```lean
-- Proving existence
example : ∃ x : Nat, x > 0 := by
  use 1
  decide

-- Witness with property
example : ∃ x : Nat, x + x = 10 := by
  use 5
  rfl

-- Extracting witness
example (h : ∃ x, x > 0 ∧ P x) : ∃ x, P x := by
  obtain ⟨x, hpos, hpx⟩ := h
  use x
  exact hpx
```

---

## conv Mode Examples

```lean
-- Rewrite specific occurrence
example (h : a = b) : a + a = b + a := by
  conv => lhs; arg 1; rw [h]

-- Navigate nested expression
example (h : a = b) : f (g a) = f (g b) := by
  conv =>
    lhs
    arg 1      -- Focus on (g a)
    arg 1      -- Focus on a
    rw [h]

-- Simplify just part of goal
example : (a + 0) * b = a * b := by
  conv => lhs; arg 1; simp
```

---

## Tactic Combinators Examples

```lean
-- Apply same tactic to all goals
example (hp : p) (hq : q) (hr : r) : p ∧ q ∧ r := by
  refine ⟨?_, ?_, ?_⟩ <;> assumption

-- Try alternatives
example (n : Nat) : n = n := by
  first | rfl | simp | trivial

-- Repeat until done
example (h1 : p → q) (h2 : q → r) (h3 : r → s) (hp : p) : s := by
  repeat apply_assumption

-- Safe attempt (never fails)
example : True := by
  try contradiction  -- Fails silently
  trivial
```

---

## Calc Proofs

```lean
-- Step-by-step equality chain
example (h1 : a = b) (h2 : b = c + 1) : a = c + 1 := by
  calc a = b     := h1
       _ = c + 1 := h2

-- With justifications
example (x : Nat) : (x + 1) * 2 = x * 2 + 2 := by
  calc (x + 1) * 2
      = x * 2 + 1 * 2 := by ring
    _ = x * 2 + 2     := by simp
```

---

## have and suffices

```lean
-- Introduce helper fact (forward reasoning)
example (hp : p) (hpq : p → q) (hqr : q → r) : r := by
  have hq : q := hpq hp
  have hr : r := hqr hq
  exact hr

-- Backward reasoning with suffices
example (hp : p) (hpq : p → q) (hqr : q → r) : r := by
  suffices hq : q by exact hqr hq
  exact hpq hp
```

---

## omega Examples

```lean
-- Linear arithmetic
example (x y : Nat) (h : x < y) : x ≤ y := by omega

example (x : Int) (h1 : x > 0) (h2 : x < 10) : x ≥ 1 ∧ x ≤ 9 := by
  omega

-- With equations
example (x y z : Nat) (h : x + y = z) (h2 : z < 10) : x < 10 := by
  omega
```

---

## contradiction and absurd

```lean
-- From False
example (h : False) : P := by contradiction

-- From contradictory hypotheses
example (h1 : p) (h2 : ¬p) : q := by contradiction

-- Explicit absurd
example (hp : p) (hnp : ¬p) : q := by
  exact absurd hp hnp
```

---

## Pattern: Proof by Cases with by_cases

```lean
-- Classical case split
example (p : Prop) : p ∨ ¬p := by
  by_cases h : p
  · left; exact h
  · right; exact h

-- Decidable case split
example (n : Nat) : n = 0 ∨ n > 0 := by
  cases n with
  | zero => left; rfl
  | succ n => right; omega
```

---

## rcases Deep Pattern Matching

```lean
-- Nested destructuring
example (h : ∃ x, ∃ y, x + y = 10) : ∃ z, z = 10 := by
  rcases h with ⟨x, ⟨y, hxy⟩⟩
  use x + y
  exact hxy

-- Alternatives
example (h : (p ∧ q) ∨ r) : p ∨ r := by
  rcases h with ⟨hp, _⟩ | hr
  · left; exact hp
  · right; exact hr
```

---

## Sources

- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
- [Mathlib Tactics](https://leanprover-community.github.io/mathlib4_docs/)
