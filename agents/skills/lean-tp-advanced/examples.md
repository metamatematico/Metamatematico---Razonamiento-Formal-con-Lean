# Lean 4 Advanced Theorem Proving Examples

Working examples demonstrating classical logic, quotients, and axiom usage.

---

## Classical Logic Examples

```lean
-- Using excluded middle
open Classical in
example (p : Prop) : p ∨ ¬p := em p

-- Double negation elimination
open Classical in
example (h : ¬¬p) : p :=
  (em p).elim id (fun hnp => absurd hnp h)

-- Proof by contradiction
open Classical in
example (h : ¬p → False) : p :=
  byContradiction h

-- Alternative: by_contra tactic
example (p : Prop) [Decidable p] : p ∨ ¬p := by
  by_cases h : p
  · left; exact h
  · right; exact h
```

---

## De Morgan's Laws

```lean
-- ¬(p ∧ q) → ¬p ∨ ¬q (requires classical)
open Classical in
example (h : ¬(p ∧ q)) : ¬p ∨ ¬q := by
  by_cases hp : p
  · by_cases hq : q
    · exact absurd ⟨hp, hq⟩ h
    · exact Or.inr hq
  · exact Or.inl hp

-- ¬(p ∨ q) → ¬p ∧ ¬q (constructive)
example (h : ¬(p ∨ q)) : ¬p ∧ ¬q :=
  ⟨fun hp => h (Or.inl hp), fun hq => h (Or.inr hq)⟩

-- ¬p ∧ ¬q → ¬(p ∨ q) (constructive)
example (h : ¬p ∧ ¬q) : ¬(p ∨ q) :=
  fun hpq => hpq.elim h.left h.right
```

---

## Contraposition

```lean
-- Constructive contrapositive
example (hpq : p → q) : ¬q → ¬p :=
  fun hnq hp => hnq (hpq hp)

-- Classical reverse contrapositive
open Classical in
example (h : ¬q → ¬p) : p → q := by
  intro hp
  by_contra hnq
  exact h hnq hp

-- Using contrapose tactic
example (h : p → q) : ¬q → ¬p := by
  contrapose
  exact h
```

---

## Propositional Extensionality

```lean
-- Equal propositions have equal proofs (trivially)
example (h1 h2 : p) : h1 = h2 := rfl

-- propext: iff implies equality
example (hab : a ↔ b) : a = b := propext hab

-- True = True
example : True = True := propext ⟨id, id⟩

-- Using propext for equality
example (h : p ↔ q) (hp : p) : q :=
  (propext h).symm ▸ hp
```

---

## Quotient Type: Integers mod n

```lean
-- Define equivalence relation
def modEquiv (n : Nat) (a b : Int) : Prop :=
  a % n = b % n

-- Prove it's an equivalence
def modSetoid (n : Nat) : Setoid Int where
  r := modEquiv n
  iseqv := {
    refl := fun x => rfl
    symm := fun h => h.symm
    trans := fun h1 h2 => h1.trans h2
  }

-- Create quotient type
def ZMod (n : Nat) := Quotient (modSetoid n)

-- Constructor
def ZMod.mk (n : Nat) (a : Int) : ZMod n :=
  Quotient.mk (modSetoid n) a

-- Notation
notation:max "⟦" a "⟧" n => ZMod.mk n a
```

---

## Lifting Functions to Quotients

```lean
-- Addition on ZMod (must prove it respects equivalence)
def ZMod.add (n : Nat) : ZMod n → ZMod n → ZMod n :=
  Quotient.lift₂
    (fun a b => ⟦a + b⟧ n)
    (fun a₁ a₂ b₁ b₂ h1 h2 => by
      apply Quotient.sound
      simp only [modEquiv]
      simp [Int.add_emod, h1, h2])

-- Negation on ZMod
def ZMod.neg (n : Nat) : ZMod n → ZMod n :=
  Quotient.lift
    (fun a => ⟦-a⟧ n)
    (fun a b h => by
      apply Quotient.sound
      simp only [modEquiv] at *
      simp [Int.neg_emod, h])
```

---

## Quotient Induction

```lean
-- Prove property for all quotient elements
example (n : Nat) (q : ZMod n) : q = q := by
  induction q using Quotient.ind with
  | mk a => rfl

-- Prove equality using sound
example (n : Nat) (a : Int) : ⟦a⟧ n = ⟦a + n⟧ n := by
  apply Quotient.sound
  simp [modEquiv, Int.add_emod]

-- Quotient.exact: equality implies relation
example (n : Nat) (a b : Int) (h : ⟦a⟧ n = ⟦b⟧ n) : a % n = b % n :=
  Quotient.exact h
```

---

## Noncomputable Definitions

```lean
-- Classical.choose extracts witness
noncomputable def findWitness {α : Type} {p : α → Prop}
    (h : ∃ x, p x) : α :=
  Classical.choose h

-- The witness satisfies the property
theorem findWitness_spec {α : Type} {p : α → Prop}
    (h : ∃ x, p x) : p (findWitness h) :=
  Classical.choose_spec h

-- Partial inverse function
noncomputable def partialInverse [Inhabited α]
    (f : α → β) (b : β) : α :=
  if h : ∃ a, f a = b
  then Classical.choose h
  else default

-- Right inverse when preimage exists
theorem partialInverse_right [Inhabited α] {f : α → β} {b : β}
    (h : ∃ a, f a = b) : f (partialInverse f b) = b :=
  Classical.choose_spec (p := fun a => f a = b) h
```

---

## conv Mode Examples

```lean
-- Rewrite on left side only
example (h : a = b) : a + a = b + a := by
  conv => lhs; arg 1; rw [h]

-- Rewrite on right side only
example (h : a = b) : a + a = a + b := by
  conv => lhs; arg 2; rw [h]

-- Nested expression
example (h : a = b) : f (g a) = f (g b) := by
  conv => lhs; arg 1; arg 1; rw [h]

-- Simplify under lambda
example : (fun x : Nat => x + 0) = (fun x => x) := by
  conv => ext x; simp
```

---

## by_cases Examples

```lean
-- Case split on proposition
example (n : Nat) : n = 0 ∨ n ≠ 0 := by
  by_cases h : n = 0
  · left; exact h
  · right; exact h

-- Using case split in proof
example (n : Nat) : n ≤ n + 1 := by
  by_cases h : n = 0
  · simp [h]
  · omega

-- Nested case analysis
example (p q : Prop) : (p → q) ∨ (q → p) := by
  by_cases hp : p
  · by_cases hq : q
    · left; intro _; exact hq
    · right; intro hq'; exact absurd hq' hq
  · left; intro hp'; exact absurd hp' hp
```

---

## Choice and Decidability

```lean
-- Decidable: computable decision
instance : Decidable (2 < 5) := isTrue (by decide)

-- Using decidability
def classify (n : Nat) : String :=
  if n < 10 then "small" else "large"

-- Classical: non-computable decision
noncomputable def classicalDecide (p : Prop) : Decidable p :=
  if hp : p
  then isTrue hp
  else isFalse hp

-- Can't #eval noncomputable definitions
-- #eval classicalDecide True  -- Error!
```

---

## Contrapose Tactic

```lean
-- Simple contraposition
example (h : p → q) : ¬q → ¬p := by
  contrapose
  exact h

-- With additional work
example (h : p → q) (hq : ¬q) : ¬p := by
  contrapose! at h
  exact h hq

-- push_neg normalizes negations
example : ¬(∀ x : Nat, x > 0) ↔ ∃ x : Nat, x ≤ 0 := by
  push_neg
  rfl
```

---

## Practical Example: Function Inverse

```lean
-- A function is injective
def Injective (f : α → β) : Prop :=
  ∀ x y, f x = f y → x = y

-- A function is surjective
def Surjective (f : α → β) : Prop :=
  ∀ b, ∃ a, f a = b

-- Surjective functions have right inverses (requires choice)
noncomputable def rightInverse {α β : Type} [Inhabited α]
    (f : α → β) (hf : Surjective f) : β → α :=
  fun b => Classical.choose (hf b)

theorem rightInverse_spec {α β : Type} [Inhabited α]
    (f : α → β) (hf : Surjective f) (b : β) :
    f (rightInverse f hf b) = b :=
  Classical.choose_spec (hf b)
```

---

## Sources

- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
- [Axioms and Computation](https://lean-lang.org/theorem_proving_in_lean4/axioms_and_computation.html)
