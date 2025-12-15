# Lean 4 Tactic Selection Examples

Working examples demonstrating tactic choice for different proof situations.

---

## Equality Goals

```lean
-- rfl: definitionally equal
example : 2 + 3 = 5 := by rfl
example : (fun x => x + 1) 5 = 6 := by rfl

-- exact: have the proof
example (h : x = y) : x = y := by exact h

-- rw: substitute
example (h : x = y) : x + z = y + z := by rw [h]

-- omega: linear arithmetic
example (n : Nat) (h : n > 0) : n ≥ 1 := by omega

-- calc: chain of equalities
example (h1 : a = b) (h2 : b = c) : a = c := by
  calc a = b := h1
       _ = c := h2
```

---

## Conjunction Goals

```lean
-- constructor: split the goal
example (hp : p) (hq : q) : p ∧ q := by
  constructor
  · exact hp
  · exact hq

-- exact with anonymous constructor
example (hp : p) (hq : q) : p ∧ q := by exact ⟨hp, hq⟩

-- And.intro
example (hp : p) (hq : q) : p ∧ q := by exact And.intro hp hq
```

---

## Disjunction Goals

```lean
-- left: prove left side
example (hp : p) : p ∨ q := by left; exact hp

-- right: prove right side
example (hq : q) : p ∨ q := by right; exact hq

-- Using Or.inl/inr
example (hp : p) : p ∨ q := by exact Or.inl hp
```

---

## Implication Goals

```lean
-- intro: assume hypothesis
example : p → q → p := by
  intro hp _
  exact hp

-- Multiple intros
example : ∀ x y : Nat, x + y = y + x := by
  intro x y
  exact Nat.add_comm x y
```

---

## Negation Goals

```lean
-- intro and derive False
example (hpq : p → q) (hnq : ¬q) : ¬p := by
  intro hp
  exact hnq (hpq hp)

-- Using absurd
example (hp : p) (hnp : ¬p) : q := by
  exact absurd hp hnp
```

---

## Existential Goals

```lean
-- use: provide witness
example : ∃ x : Nat, x > 5 := by
  use 10
  omega

-- With constructor
example : ∃ x : Nat, x + x = 10 := by
  use 5
  rfl
```

---

## Case Analysis on Hypotheses

```lean
-- cases on Or
example (h : p ∨ q) : q ∨ p := by
  cases h with
  | inl hp => right; exact hp
  | inr hq => left; exact hq

-- cases on And (less common, usually use h.left/h.right)
example (h : p ∧ q) : q := by
  cases h with
  | intro hp hq => exact hq

-- obtain on existential
example (h : ∃ x, p x) : ∃ x, p x ∨ q x := by
  obtain ⟨x, hpx⟩ := h
  exact ⟨x, Or.inl hpx⟩

-- rcases for nested patterns
example (h : ∃ x, ∃ y, p x y) : ∃ y x, p x y := by
  rcases h with ⟨x, y, hxy⟩
  exact ⟨y, x, hxy⟩
```

---

## Induction Examples

```lean
-- Natural number induction
example (n : Nat) : n + 0 = n := by
  induction n with
  | zero => rfl
  | succ n ih => simp [Nat.add_succ, ih]

-- List induction
example (xs ys : List α) : (xs ++ ys).length = xs.length + ys.length := by
  induction xs with
  | nil => simp
  | cons x xs ih => simp [ih, Nat.add_assoc]

-- With generalization
example (m n : Nat) : m + n = n + m := by
  induction n generalizing m with
  | zero => simp
  | succ n ih => simp [Nat.add_succ, Nat.succ_add, ih]
```

---

## Rewriting Examples

```lean
-- Basic rw
example (h : x = y) : x + 1 = y + 1 := by rw [h]

-- Reverse direction
example (h : x = y) : y + 1 = x + 1 := by rw [← h]

-- Multiple rewrites
example (h1 : a = b) (h2 : c = d) : a + c = b + d := by rw [h1, h2]

-- Rewrite in hypothesis
example (h1 : a = b) (h2 : a = c) : b = c := by
  rw [← h1]
  exact h2
```

---

## simp Examples

```lean
-- Basic simp
example (n : Nat) : n + 0 = n := by simp

-- With custom lemma
example (h : a = b) : a + 1 = b + 1 := by simp [h]

-- simp_all (simplify hypotheses too)
example (h : a = b) (h2 : a + 1 = c) : b + 1 = c := by simp_all

-- simp only (explicit lemmas only)
example (n : Nat) : n + 0 = n := by simp only [Nat.add_zero]
```

---

## conv Examples

```lean
-- Rewrite only on left side
example (h : a = b) : a + a = b + a := by
  conv => lhs; arg 1; rw [h]

-- Rewrite on right side
example (h : a = b) : a + a = a + b := by
  conv => lhs; arg 2; rw [h]

-- Enter nested expression
example (h : a = b) : f (g a) = f (g b) := by
  conv => lhs; arg 1; arg 1; rw [h]
```

---

## Automation Examples

```lean
-- omega for linear arithmetic
example (x y : Nat) (h : x < y) : x ≤ y := by omega
example (x : Int) (h : x > 0) : x ≥ 1 := by omega

-- decide for decidable propositions
example : 5 < 10 := by decide
example : "hello".length = 5 := by decide

-- ring for ring operations
example (x y : Int) : (x + y) ^ 2 = x^2 + 2*x*y + y^2 := by ring

-- contradiction for contradictory hypotheses
example (hp : p) (hnp : ¬p) : q := by contradiction
```

---

## Tactic Combinators

```lean
-- <;> apply to all goals
example (hp : p) (hq : q) : p ∧ q ∧ p := by
  refine ⟨?_, ?_, ?_⟩ <;> assumption

-- try (never fails)
example : True := by
  try contradiction
  trivial

-- first (try alternatives)
example (n : Nat) : n = n := by
  first | rfl | simp | trivial

-- repeat
example (h1 : p → q) (h2 : q → r) (h3 : r → s) (hp : p) : s := by
  repeat (apply_assumption || assumption)
```

---

## by_cases for Classical Reasoning

```lean
-- Case split on any Prop
example (p : Prop) : p ∨ ¬p := by
  by_cases hp : p
  · left; exact hp
  · right; exact hp

-- Useful for decidable conditions
example (n : Nat) : n = 0 ∨ n > 0 := by
  by_cases h : n = 0
  · left; exact h
  · right; omega
```

---

## Sources

- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
