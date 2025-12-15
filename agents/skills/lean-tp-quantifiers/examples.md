# Lean 4 Quantifiers and Equality Examples

Working proof examples demonstrating quantifier and equality reasoning.

---

## Universal Quantifier Examples

```lean
-- Basic forall introduction
example : ∀ x : Nat, x = x := fun x => rfl

-- With tactic
example : ∀ x : Nat, x = x := by intro x; rfl

-- Multiple quantifiers
example : ∀ x y : Nat, x + y = y + x := fun x y => Nat.add_comm x y

-- Applying forall hypothesis
example (h : ∀ x, x > 0 → p x) (n : Nat) (hn : n > 0) : p n := h n hn

-- Chained application
example (h : ∀ x y z, x + y + z = z + y + x) : 1 + 2 + 3 = 3 + 2 + 1 :=
  h 1 2 3
```

---

## Existential Quantifier Examples

```lean
-- Providing witness
example : ∃ x : Nat, x > 5 := ⟨6, by decide⟩

-- Multiple witnesses
example : ∃ x y : Nat, x + y = 10 := ⟨3, 7, rfl⟩

-- Using use tactic
example : ∃ x : Nat, x * x = 16 := by
  use 4
  rfl

-- Extracting witness
example (h : ∃ x, x > 0 ∧ p x) : ∃ x, p x := by
  obtain ⟨x, _, hpx⟩ := h
  exact ⟨x, hpx⟩

-- Transforming existential
example (h : ∃ x, p x) : ∃ x, p x ∨ q x := by
  obtain ⟨x, hpx⟩ := h
  exact ⟨x, Or.inl hpx⟩
```

---

## Equality with rfl

```lean
-- Simple computations
example : 2 + 3 = 5 := rfl
example : 10 * 10 = 100 := rfl
example : [1, 2, 3].length = 3 := rfl

-- Function application reduces
example : (fun x => x + 1) 5 = 6 := rfl

-- List operations
example : [1, 2] ++ [3, 4] = [1, 2, 3, 4] := rfl

-- Nested structures
example : (1, 2).fst = 1 := rfl
```

---

## Symmetry and Transitivity

```lean
-- Symmetry
example (h : a = b) : b = a := h.symm
example (h : a = b) : b = a := Eq.symm h

-- Transitivity
example (h1 : a = b) (h2 : b = c) : a = c := h1.trans h2
example (h1 : a = b) (h2 : b = c) : a = c := Eq.trans h1 h2

-- Chain
example (h1 : a = b) (h2 : b = c) (h3 : c = d) : a = d :=
  h1.trans (h2.trans h3)
```

---

## Substitution Examples

```lean
-- Basic substitution
example (h : a = b) (hp : p a) : p b := h ▸ hp

-- Reverse direction
example (h : a = b) (hp : p b) : p a := h.symm ▸ hp

-- In complex expressions
example (h : x = y) (hp : x + z = w) : y + z = w :=
  h ▸ hp

-- Substituting in function position
example (h : f = g) (x : α) : f x = g x :=
  congrFun h x
```

---

## calc Proofs

```lean
-- Simple chain
example (h1 : a = b) (h2 : b = c) : a = c :=
  calc a = b := h1
       _ = c := h2

-- With computation
example : (1 + 2) * 3 = 9 :=
  calc (1 + 2) * 3 = 3 * 3 := by rfl
                 _ = 9     := by rfl

-- With lemmas
example (x : Nat) : x + 0 + 0 = x :=
  calc x + 0 + 0 = x + 0 := Nat.add_zero (x + 0)
               _ = x     := Nat.add_zero x

-- Mixed relations
example (h1 : a ≤ b) (h2 : b < c) (h3 : c ≤ d) : a < d :=
  calc a ≤ b := h1
       _ < c := h2
       _ ≤ d := h3
```

---

## Congruence Examples

```lean
-- congrArg: f a = f b from a = b
example (h : x = y) : x + 1 = y + 1 := congrArg (· + 1) h
example (h : x = y) : [x] = [y] := congrArg (fun z => [z]) h

-- congrFun: f a = g a from f = g
example (h : (· + 1) = (· + 1 : Nat → Nat)) : 5 + 1 = 5 + 1 := congrFun h 5

-- congr: f a = g b from f = g and a = b
example (hf : f = g) (hx : x = y) : f x = g y := congr hf hx

-- In practice
example (h : a = b) : a + c = b + c := by
  exact congrArg (· + c) h
```

---

## Combined Quantifier Examples

```lean
-- ∀ with ∃
example : ∀ n : Nat, ∃ m, m > n := fun n => ⟨n + 1, Nat.lt_succ_self n⟩

-- ∃ implying ∃
example (h : ∃ x, p x ∧ q x) : ∃ x, p x := by
  obtain ⟨x, hpx, _⟩ := h
  exact ⟨x, hpx⟩

-- Swap quantifiers
example (h : ∃ x, ∀ y, p x y) : ∀ y, ∃ x, p x y := by
  intro y
  obtain ⟨x, hx⟩ := h
  exact ⟨x, hx y⟩

-- Negating quantifiers (constructive)
example (h : ∀ x, ¬p x) : ¬∃ x, p x := by
  intro ⟨x, hpx⟩
  exact h x hpx
```

---

## Rewrite Examples

```lean
-- Basic rewrite
example (h : x = y) : x + z = y + z := by rw [h]

-- Reverse rewrite
example (h : x = y) : y + z = x + z := by rw [← h]

-- Multiple rewrites
example (h1 : a = b) (h2 : c = d) : a + c = b + d := by
  rw [h1, h2]

-- Rewrite in hypothesis
example (h1 : a = b) (h2 : a + c = d) : b + c = d := by
  rw [← h1]
  exact h2

-- Rewrite at specific location
example (h : x = y) : x + x = y + y := by
  rw [h]  -- Rewrites both occurrences
```

---

## Classical Quantifier Reasoning

```lean
open Classical in
-- ¬∀ → ∃¬
example (h : ¬∀ x, p x) : ∃ x, ¬p x := by
  byContradiction hc
  apply h
  intro x
  byContradiction hnpx
  exact hc ⟨x, hnpx⟩

open Classical in
-- ¬∃ → ∀¬
example (h : ¬∃ x, p x) : ∀ x, ¬p x := by
  intro x hpx
  exact h ⟨x, hpx⟩
```

---

## Bounded Quantifiers

```lean
-- ∀ x < n means ∀ x, x < n → p x
example : ∀ x < 5, x < 10 := by
  intro x hx
  omega

-- ∃ x < n means ∃ x, x < n ∧ p x
example : ∃ x < 10, x > 5 := ⟨7, by omega, by omega⟩

-- Using bounded quantifiers
example (h : ∀ x < 10, p x) : p 5 := h 5 (by omega)
```

---

## Decidable Equality

```lean
-- Using if-then-else with equality
def contains (xs : List Nat) (n : Nat) : Bool :=
  match xs with
  | [] => false
  | x :: xs => if x = n then true else contains xs n

-- Splitting on equality
example (x y : Nat) : x = y ∨ x ≠ y := by
  by_cases h : x = y
  · left; exact h
  · right; exact h
```

---

## Sources

- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
