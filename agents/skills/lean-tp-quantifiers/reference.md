# Lean 4 Quantifiers and Equality Deep Dive

Extended reference for predicate logic and equational reasoning.

---

## Universal Quantifier (∀)

### Formal Definition

```lean
-- ∀ x : α, p x is function type
#check (∀ x : Nat, x = x)  -- Prop

-- Equivalent notations
(x : α) → p x
∀ (x : α), p x
∀ x, p x  -- Type inferred
```

### Introduction

```lean
-- Term mode: lambda
theorem all_eq : ∀ x : Nat, x = x := fun x => rfl

-- Tactic mode: intro
theorem all_eq' : ∀ x : Nat, x = x := by
  intro x
  rfl

-- Multiple quantifiers
theorem all_comm : ∀ x y : Nat, x + y = y + x :=
  fun x y => Nat.add_comm x y
```

### Elimination (Specialization)

```lean
-- Apply to specific value
example (h : ∀ x, p x) (t : α) : p t := h t

-- Chain of applications
example (h : ∀ x y, p x y) (a b : α) : p a b := h a b
```

---

## Existential Quantifier (∃)

### Formal Definition

```lean
-- Exists is inductive
inductive Exists {α : Type} (p : α → Prop) : Prop where
  | intro (w : α) (h : p w) : Exists p

-- Notation: ∃ x, p x
```

### Introduction (Providing Witness)

```lean
-- Anonymous constructor
example : ∃ x : Nat, x > 5 := ⟨6, by decide⟩

-- Exists.intro
example : ∃ x : Nat, x > 5 := Exists.intro 6 (by decide)

-- use tactic
example : ∃ x : Nat, x > 5 := by
  use 6
  decide
```

### Elimination (Extracting Witness)

```lean
-- obtain pattern
example (h : ∃ x, p x) : q := by
  obtain ⟨w, hw⟩ := h
  -- w : α, hw : p w available
  sorry

-- match expression
example (h : ∃ x, p x) : q := by
  match h with
  | ⟨w, hw⟩ => sorry

-- Exists.elim
example (h : ∃ x, p x) : q :=
  Exists.elim h (fun w hw => sorry)
```

### Nested Existentials

```lean
-- Multiple witnesses
example (h : ∃ x y, p x y) : ∃ y x, p x y := by
  obtain ⟨x, y, hxy⟩ := h
  exact ⟨y, x, hxy⟩
```

---

## Equality Type

### Definition

```lean
-- Eq is indexed inductive
inductive Eq {α : Type} (a : α) : α → Prop where
  | refl : Eq a a

-- Notation: a = b
```

### Definitional vs Propositional

```lean
-- Definitional: computation gives same value
#check (2 + 2 = 4 : Prop)        -- rfl works
#check ((fun x => x) 5 = 5 : Prop)  -- rfl works

-- Propositional: needs proof
example : n + 0 = n := Nat.add_zero n  -- Not definitional!
```

### Core Lemmas

```lean
Eq.refl (a : α) : a = a                    -- rfl
Eq.symm (h : a = b) : b = a                -- h.symm
Eq.trans (h1 : a = b) (h2 : b = c) : a = c -- h1.trans h2

-- Substitution
Eq.subst (h : a = b) (hp : p a) : p b     -- h ▸ hp
```

---

## Congruence Lemmas

### congrArg

```lean
-- If a = b, then f a = f b
congrArg (f : α → β) (h : a = b) : f a = f b

example (h : x = y) : x + 1 = y + 1 := congrArg (· + 1) h
```

### congrFun

```lean
-- If f = g, then f a = g a
congrFun (h : f = g) (a : α) : f a = g a

example (h : f = g) : f 5 = g 5 := congrFun h 5
```

### congr

```lean
-- If f = g and a = b, then f a = g b
congr (hf : f = g) (ha : a = b) : f a = g b

example (hf : f = g) (hx : x = y) : f x = g y := congr hf hx
```

---

## calc Proofs

### Basic Structure

```lean
calc a = b := proof₁
     _ = c := proof₂
     _ = d := proof₃
```

### With Inequalities

```lean
calc a ≤ b := h1
     _ < c := h2
     _ ≤ d := h3
-- Result: a < d (combines correctly)
```

### Mixing Tactics

```lean
example (h : a = b) : a + c = b + c :=
  calc a + c = b + c := by rw [h]
```

### Multi-step Example

```lean
example (h1 : a = b) (h2 : c = d) : a + c = b + d :=
  calc a + c = b + c := by rw [h1]
           _ = b + d := by rw [h2]
```

---

## Substitution Patterns

### ▸ Operator

```lean
-- h ▸ hp substitutes using h
-- Direction: h : a = b replaces a with b

example (h : a = b) (hp : p a) : p b := h ▸ hp
example (h : a = b) (hp : p b) : p a := h.symm ▸ hp
```

### Eq.mpr and Eq.mp

```lean
-- More explicit substitution
Eq.mpr (h : a = b) (hb : b) : a  -- "move" from b to a
Eq.mp (h : a = b) (ha : a) : b   -- "move" from a to b
```

---

## Quantifier Manipulation

### Swapping Quantifiers

```lean
-- ∀∀ → ∀∀ (order doesn't matter for universal)
example (h : ∀ x y, p x y) : ∀ y x, p x y :=
  fun y x => h x y

-- ∃∃ → ∃∃ (order doesn't matter for existential)
example (h : ∃ x y, p x y) : ∃ y x, p x y := by
  obtain ⟨x, y, hxy⟩ := h
  exact ⟨y, x, hxy⟩
```

### Bounded Quantifiers

```lean
-- ∀ x < n, p x
-- Same as: ∀ x, x < n → p x

-- ∃ x < n, p x
-- Same as: ∃ x, x < n ∧ p x
```

---

## Decidable Equality

```lean
-- For computable equality checks
class DecidableEq (α : Type) where
  decEq : ∀ (a b : α), Decidable (a = b)

-- Usage with if-then-else
def f (x y : Nat) : Nat :=
  if x = y then 1 else 0

-- Works because Nat has DecidableEq
```

---

## Common Patterns

### Proving ∀ x, ∃ y, p x y

```lean
-- For each x, provide a witness y depending on x
example : ∀ n : Nat, ∃ m, m > n := fun n => ⟨n + 1, Nat.lt_succ_self n⟩
```

### Using ∃ x, ∀ y, p x y

```lean
-- Find one x that works for all y
example (h : ∃ x, ∀ y, p x y) (t : α) : ∃ x, p x t := by
  obtain ⟨x, hx⟩ := h
  exact ⟨x, hx t⟩
```

---

## Sources

- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
- [Quantifiers and Equality chapter](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html)
