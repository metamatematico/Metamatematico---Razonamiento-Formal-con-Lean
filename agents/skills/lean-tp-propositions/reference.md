# Lean 4 Propositions Deep Dive

Extended reference for propositional logic, proof construction, and logical reasoning.

---

## Curry-Howard Correspondence

The fundamental correspondence between logic and type theory:

| Logic | Type Theory |
|-------|-------------|
| Proposition | Type |
| Proof | Term |
| p → q | Function type |
| p ∧ q | Product type |
| p ∨ q | Sum type |
| ¬p | p → False |
| ∀x.P(x) | Dependent function type |
| ∃x.P(x) | Dependent pair type |

---

## The Prop Universe

### Prop vs Type

```lean
#check (True : Prop)        -- True : Prop
#check (1 = 1 : Prop)       -- Prop
#check (Nat : Type)         -- Nat : Type

-- Prop lives in Type
#check (Prop : Type 1)      -- Prop : Type
```

### Proof Irrelevance

All proofs of the same proposition are definitionally equal:

```lean
-- Any two proofs of p are equal
theorem proof_irrel (p : Prop) (h1 h2 : p) : h1 = h2 := rfl

-- This is why Prop is special - no data extraction
```

---

## Logical Connectives (Formal)

### True and False

```lean
-- True has one constructor
inductive True : Prop where
  | intro : True

-- False has no constructors
inductive False : Prop where

-- Ex falso quodlibet
theorem False.elim : False → α := fun h => nomatch h
```

### And (Conjunction)

```lean
structure And (a b : Prop) : Prop where
  intro :: (left : a) (right : b)

-- Notation: a ∧ b

-- Construction
And.intro hp hq  : p ∧ q
⟨hp, hq⟩         : p ∧ q

-- Destruction
And.left h   : p
And.right h  : q
h.1 or h.left  : p
h.2 or h.right : q
```

### Or (Disjunction)

```lean
inductive Or (a b : Prop) : Prop where
  | inl : a → Or a b
  | inr : b → Or a b

-- Notation: a ∨ b

-- Construction
Or.inl hp : p ∨ q
Or.inr hq : p ∨ q

-- Elimination (case analysis)
Or.elim h (f : a → c) (g : b → c) : c
```

### Not (Negation)

```lean
def Not (a : Prop) := a → False

-- Notation: ¬a

-- Proving negation: assume a, derive False
example (hp : p) (hnp : ¬p) : False := hnp hp

-- From contradiction, derive anything
theorem absurd (h : a) (hn : ¬a) : b := False.elim (hn h)
```

---

## Implication and Functions

### Implication as Function

```lean
-- p → q is function type from p to q
-- Proof: construct function

-- Lambda introduction
example : p → q → p := fun hp _ => hp

-- Function application (modus ponens)
example (hpq : p → q) (hp : p) : q := hpq hp
```

### Multiple Implications

```lean
-- Right associative: a → b → c = a → (b → c)
example : p → q → r → p ∧ q ∧ r :=
  fun hp hq hr => ⟨hp, hq, hr⟩
```

---

## Proof Terms Anatomy

### Building Proofs

```lean
-- Simple implication
theorem t1 : p → p := fun hp => hp

-- Conjunction introduction
theorem t2 (hp : p) (hq : q) : p ∧ q := ⟨hp, hq⟩

-- Conjunction elimination + or introduction
theorem t3 (h : p ∧ q) : p ∨ q := Or.inl h.left

-- Chain reasoning
theorem t4 (h1 : p → q) (h2 : q → r) : p → r :=
  fun hp => h2 (h1 hp)
```

### With have and show

```lean
theorem complex (h : p ∧ q) : q ∧ p := by
  have hp : p := h.left
  have hq : q := h.right
  show q ∧ p
  exact ⟨hq, hp⟩
```

---

## Propositional Equivalence (↔)

### Definition

```lean
structure Iff (a b : Prop) : Prop where
  intro :: (mp : a → b) (mpr : b → a)

-- Notation: a ↔ b
```

### Using Iff

```lean
-- Construction
example (hab : a → b) (hba : b → a) : a ↔ b := ⟨hab, hba⟩

-- Destruction
example (h : a ↔ b) (ha : a) : b := h.mp ha
example (h : a ↔ b) (hb : b) : a := h.mpr hb

-- Rewrite with Iff
example (h : a ↔ b) (ha : a) : b := h.1 ha
```

---

## Classical vs Constructive

### Decidable Propositions

```lean
-- Decidable: can compute truth value
class Decidable (p : Prop) where
  decide : Bool
  decide_eq : (decide = true) ↔ p

-- Example: equality on Nat is decidable
example : Decidable (5 = 5) := inferInstance
```

### Classical Axioms

```lean
-- Excluded middle (classical)
axiom Classical.em : ∀ p : Prop, p ∨ ¬p

-- Double negation elimination
theorem Classical.byContradiction (h : ¬¬p) : p := ...
```

---

## De Morgan's Laws

```lean
-- Constructively valid
theorem not_or_of_and_not : ¬p ∧ ¬q → ¬(p ∨ q) :=
  fun ⟨hnp, hnq⟩ h => h.elim hnp hnq

-- Requires classical logic
theorem not_and_of_or_not : ¬p ∨ ¬q → ¬(p ∧ q) :=
  fun h ⟨hp, hq⟩ => h.elim (fun hnp => hnp hp) (fun hnq => hnq hq)
```

---

## Proof Patterns

### Modus Ponens

```lean
-- If p → q and p, then q
example (hpq : p → q) (hp : p) : q := hpq hp
```

### Modus Tollens

```lean
-- If p → q and ¬q, then ¬p
example (hpq : p → q) (hnq : ¬q) : ¬p :=
  fun hp => hnq (hpq hp)
```

### Contraposition

```lean
-- (p → q) → (¬q → ¬p)
example (hpq : p → q) : ¬q → ¬p :=
  fun hnq hp => hnq (hpq hp)
```

### Disjunctive Syllogism

```lean
-- If p ∨ q and ¬p, then q (requires classical)
example (h : p ∨ q) (hnp : ¬p) : q :=
  h.elim (fun hp => absurd hp hnp) id
```

---

## Common Lemmas

```lean
-- And is commutative
theorem and_comm : p ∧ q ↔ q ∧ p := ⟨fun ⟨hp, hq⟩ => ⟨hq, hp⟩, fun ⟨hq, hp⟩ => ⟨hp, hq⟩⟩

-- Or is commutative
theorem or_comm : p ∨ q ↔ q ∨ p :=
  ⟨fun h => h.elim Or.inr Or.inl, fun h => h.elim Or.inr Or.inl⟩

-- Distribution
theorem and_or_distrib : p ∧ (q ∨ r) ↔ (p ∧ q) ∨ (p ∧ r) := ...
```

---

## Sources

- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
- [Propositions and Proofs chapter](https://lean-lang.org/theorem_proving_in_lean4/propositions_and_proofs.html)
