# Lean 4 Propositions Examples

Working proof examples demonstrating propositional logic patterns.

---

## Basic Implication

```lean
-- Identity: p → p
example : p → p := fun hp => hp

-- K combinator: p → q → p
example : p → q → p := fun hp _ => hp

-- S combinator (composition)
example : (p → q → r) → (p → q) → p → r :=
  fun hpqr hpq hp => hpqr hp (hpq hp)
```

---

## Conjunction (And)

```lean
-- And introduction
example (hp : p) (hq : q) : p ∧ q := ⟨hp, hq⟩

-- And elimination
example (h : p ∧ q) : p := h.left
example (h : p ∧ q) : q := h.right

-- And commutativity
example (h : p ∧ q) : q ∧ p := ⟨h.right, h.left⟩

-- And associativity
example (h : (p ∧ q) ∧ r) : p ∧ (q ∧ r) :=
  ⟨h.left.left, h.left.right, h.right⟩

-- Curry: (p ∧ q) → r ↔ p → q → r
example (h : p ∧ q → r) : p → q → r :=
  fun hp hq => h ⟨hp, hq⟩

example (h : p → q → r) : p ∧ q → r :=
  fun ⟨hp, hq⟩ => h hp hq
```

---

## Disjunction (Or)

```lean
-- Or introduction (left)
example (hp : p) : p ∨ q := Or.inl hp

-- Or introduction (right)
example (hq : q) : p ∨ q := Or.inr hq

-- Or elimination (case analysis)
example (h : p ∨ q) : q ∨ p :=
  h.elim (fun hp => Or.inr hp) (fun hq => Or.inl hq)

-- Using match
example (h : p ∨ q) : q ∨ p :=
  match h with
  | Or.inl hp => Or.inr hp
  | Or.inr hq => Or.inl hq

-- Or associativity
example (h : (p ∨ q) ∨ r) : p ∨ (q ∨ r) :=
  match h with
  | Or.inl (Or.inl hp) => Or.inl hp
  | Or.inl (Or.inr hq) => Or.inr (Or.inl hq)
  | Or.inr hr => Or.inr (Or.inr hr)
```

---

## Negation

```lean
-- Proving negation: assume p, derive False
example (hpq : p → q) (hnq : ¬q) : ¬p :=
  fun hp => hnq (hpq hp)

-- From contradiction, derive anything
example (hp : p) (hnp : ¬p) : q := absurd hp hnp

-- Alternative: False.elim
example (hp : p) (hnp : ¬p) : q := False.elim (hnp hp)

-- Not not introduction (constructive)
example (hp : p) : ¬¬p :=
  fun hnp => hnp hp

-- Contraposition
example (hpq : p → q) : ¬q → ¬p :=
  fun hnq hp => hnq (hpq hp)
```

---

## Iff (If and Only If)

```lean
-- Iff introduction
example (hab : a → b) (hba : b → a) : a ↔ b := ⟨hab, hba⟩

-- Using Iff.intro
example (hab : a → b) (hba : b → a) : a ↔ b := Iff.intro hab hba

-- Iff elimination
example (h : a ↔ b) (ha : a) : b := h.mp ha
example (h : a ↔ b) (hb : b) : a := h.mpr hb

-- Iff is symmetric
example (h : a ↔ b) : b ↔ a := ⟨h.mpr, h.mp⟩

-- Iff is transitive
example (h1 : a ↔ b) (h2 : b ↔ c) : a ↔ c :=
  ⟨fun ha => h2.mp (h1.mp ha), fun hc => h1.mpr (h2.mpr hc)⟩
```

---

## Complex Proofs

```lean
-- Distribution: p ∧ (q ∨ r) ↔ (p ∧ q) ∨ (p ∧ r)
example : p ∧ (q ∨ r) ↔ (p ∧ q) ∨ (p ∧ r) :=
  ⟨fun ⟨hp, hqr⟩ => hqr.elim (fun hq => Or.inl ⟨hp, hq⟩)
                              (fun hr => Or.inr ⟨hp, hr⟩),
   fun h => h.elim (fun ⟨hp, hq⟩ => ⟨hp, Or.inl hq⟩)
                   (fun ⟨hp, hr⟩ => ⟨hp, Or.inr hr⟩)⟩

-- De Morgan (constructive direction)
example : ¬p ∧ ¬q → ¬(p ∨ q) :=
  fun ⟨hnp, hnq⟩ hpq => hpq.elim hnp hnq

-- Another De Morgan
example : ¬(p ∧ q) → ¬p ∨ ¬q := by
  intro h
  by_cases hp : p
  · by_cases hq : q
    · exact absurd ⟨hp, hq⟩ h
    · exact Or.inr hq
  · exact Or.inl hp
```

---

## With have and show

```lean
-- Using have for intermediate steps
example (h : p ∧ q) : q ∧ p := by
  have hp : p := h.left
  have hq : q := h.right
  show q ∧ p
  exact ⟨hq, hp⟩

-- Term mode with have
example (h : p ∧ q) : q ∧ p :=
  have hp : p := h.left
  have hq : q := h.right
  ⟨hq, hp⟩

-- suffices: backward reasoning
example (hp : p) (hpq : p → q) (hqr : q → r) : r := by
  suffices hq : q by exact hqr hq
  exact hpq hp
```

---

## Proof by Cases

```lean
-- Case analysis on Or
example (h : p ∨ q) (hpr : p → r) (hqr : q → r) : r :=
  h.elim hpr hqr

-- Nested case analysis
example (h : (p ∨ q) ∨ r) (hp : p → s) (hq : q → s) (hr : r → s) : s :=
  h.elim (fun hpq => hpq.elim hp hq) hr
```

---

## Classical Logic Examples

```lean
open Classical in
-- Excluded middle
example (p : Prop) : p ∨ ¬p := em p

open Classical in
-- Double negation elimination
example (h : ¬¬p) : p :=
  (em p).elim id (fun hnp => absurd hnp h)

open Classical in
-- Proof by contradiction
example (h : ¬p → False) : p :=
  byContradiction (fun hnp => h hnp)

open Classical in
-- De Morgan (classical)
example : ¬(p ∧ q) → ¬p ∨ ¬q :=
  fun h => (em p).elim
    (fun hp => (em q).elim
      (fun hq => absurd ⟨hp, hq⟩ h)
      Or.inr)
    Or.inl
```

---

## Tactic Mode Equivalents

```lean
-- Conjunction
example (hp : p) (hq : q) : p ∧ q := by
  constructor
  · exact hp
  · exact hq

-- Disjunction (left)
example (hp : p) : p ∨ q := by left; exact hp

-- Disjunction (case split)
example (h : p ∨ q) : q ∨ p := by
  cases h with
  | inl hp => right; exact hp
  | inr hq => left; exact hq

-- Negation
example (hp : p) (hnp : ¬p) : q := by
  contradiction
```

---

## True and False

```lean
-- True is trivially provable
example : True := trivial
example : True := True.intro

-- False can prove anything
example (h : False) : p := False.elim h
example (h : False) : p := h.elim

-- Not false is true
example : ¬False := fun h => h
```

---

## Sources

- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
