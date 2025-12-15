# Lean 4 Advanced Theorem Proving Deep Dive

Extended reference for classical logic, axioms, quotients, and computational considerations.

---

## Lean's Foundational Axioms

### The Axiom Hierarchy

```
propext (Propositional Extensionality)
    ↓ uses
funext (Function Extensionality) -- derived from propext
    ↓ uses
Classical.choice (Axiom of Choice)
    ↓ marks definitions
noncomputable (No computational content)
```

### Propositional Extensionality

```lean
-- If a ↔ b, then a = b as types
axiom propext : {a b : Prop} → (a ↔ b) → a = b

-- Consequence: Props with same truth value are equal
example (ha : a ↔ b) : a = b := propext ha

-- Proof irrelevance follows
theorem proof_irrelevant (h1 h2 : p) : h1 = h2 := rfl
-- All proofs of a Prop are definitionally equal
```

### Function Extensionality

```lean
-- Derived from propext via quotients
theorem funext {f g : α → β} (h : ∀ x, f x = g x) : f = g :=
  -- Uses quotient and propext internally

-- Usage
example (h : ∀ x, f x = g x) : f = g := funext h
```

### Axiom of Choice

```lean
-- Extract element from nonempty type
axiom Classical.choice : {α : Type u} → Nonempty α → α

-- Derived: indefinite description
noncomputable def Classical.choose {α} {p : α → Prop}
    (h : ∃ x, p x) : α :=
  choice (nonempty_of_exists h)

-- Property of chosen element
theorem Classical.choose_spec {α} {p : α → Prop}
    (h : ∃ x, p x) : p (choose h)
```

---

## Classical Logic

### Excluded Middle

```lean
-- Core classical axiom
theorem Classical.em (p : Prop) : p ∨ ¬p

-- Proof by contradiction
theorem byContradiction {p : Prop} (h : ¬p → False) : p :=
  (em p).elim id (fun hnp => False.elim (h hnp))

-- Double negation elimination
theorem Classical.dne {p : Prop} (h : ¬¬p) : p :=
  (em p).elim id (fun hnp => absurd hnp h)
```

### Classical Tactics

| Tactic | Effect |
|--------|--------|
| `by_cases h : p` | Split on p ∨ ¬p |
| `by_contra h` | Assume ¬goal, derive False |
| `push_neg` | Push negation inward |
| `contrapose` | Prove contrapositive |

### De Morgan's Laws (Classical)

```lean
-- Require classical logic
open Classical in
theorem not_and_iff_or_not : ¬(p ∧ q) ↔ ¬p ∨ ¬q := by
  constructor
  · intro h
    by_cases hp : p
    · by_cases hq : q
      · exact absurd ⟨hp, hq⟩ h
      · exact Or.inr hq
    · exact Or.inl hp
  · intro h ⟨hp, hq⟩
    h.elim (absurd hp) (absurd hq)

open Classical in
theorem not_or_iff_and_not : ¬(p ∨ q) ↔ ¬p ∧ ¬q := by
  constructor
  · intro h
    exact ⟨fun hp => h (Or.inl hp), fun hq => h (Or.inr hq)⟩
  · intro ⟨hnp, hnq⟩ hpq
    hpq.elim hnp hnq
```

---

## Quotient Types

### Setoid Definition

```lean
-- Setoid bundles type with equivalence relation
class Setoid (α : Type u) where
  r : α → α → Prop
  iseqv : Equivalence r

-- Equivalence requires reflexivity, symmetry, transitivity
structure Equivalence (r : α → α → Prop) where
  refl : ∀ x, r x x
  symm : ∀ {x y}, r x y → r y x
  trans : ∀ {x y z}, r x y → r y z → r x z
```

### Creating Quotients

```lean
-- Quotient constructor
#check (Quotient : {α : Type u} → Setoid α → Type u)

-- Create quotient element
#check (Quotient.mk : {α : Type u} → {s : Setoid α} → α → Quotient s)

-- Quotient equality from equivalence
axiom Quot.sound : ∀ {α} {r : α → α → Prop} {a b : α},
  r a b → Quot.mk r a = Quot.mk r b
```

### Lifting Functions

```lean
-- Lift to quotient (must respect equivalence)
def Quotient.lift {α : Type u} {β : Sort v} {s : Setoid α}
    (f : α → β)
    (h : ∀ a b, a ≈ b → f a = f b) :
    Quotient s → β

-- Lift binary functions
def Quotient.lift₂ {α β : Type u} {γ : Sort v}
    {sa : Setoid α} {sb : Setoid β}
    (f : α → β → γ)
    (h : ∀ a₁ a₂ b₁ b₂, a₁ ≈ a₂ → b₁ ≈ b₂ → f a₁ b₁ = f a₂ b₂) :
    Quotient sa → Quotient sb → γ
```

### Quotient Induction

```lean
-- Prove property for all quotient elements
theorem Quotient.ind {α : Type u} {s : Setoid α} {motive : Quotient s → Prop}
    (h : ∀ a, motive (Quotient.mk s a)) :
    ∀ q, motive q

-- Usage pattern
example (q : MyQuotient) : P q := by
  induction q using Quotient.ind with
  | mk a => -- prove P (⟦a⟧)
```

---

## Noncomputable Definitions

### When Required

```lean
-- Using Classical.choose requires noncomputable
noncomputable def extractWitness {p : α → Prop}
    (h : ∃ x, p x) : α :=
  Classical.choose h

-- Using em for construction (not proof)
noncomputable def decideClassically (p : Prop) : Bool :=
  if Classical.em p then true else false
```

### Partial Inverse Example

```lean
noncomputable def inverse [Inhabited α] (f : α → β) (b : β) : α :=
  if h : ∃ a, f a = b
  then Classical.choose h
  else default

-- Verify it's a right inverse when possible
theorem inverse_spec [Inhabited α] {f : α → β} {b : β}
    (h : ∃ a, f a = b) : f (inverse f b) = b :=
  Classical.choose_spec h
```

### Decidable vs Classical

```lean
-- Decidable: computational decision procedure
class Decidable (p : Prop) where
  decide : Bool
  decide_spec : decide = true ↔ p

-- Classical: non-computational
-- decPropToBool p requires Decidable p
-- Classical.em p gives Bool but noncomputable

-- Prefer Decidable when available
def isEven (n : Nat) : Bool := n % 2 == 0  -- computable
```

---

## conv Tactic Mode

### Navigation

```lean
conv =>
  lhs        -- Left side of equality/relation
  rhs        -- Right side
  arg n      -- nth argument (1-indexed)
  enter [1, 2, 1]  -- Path into nested expression
  ext x      -- Introduce binder (for ∀, fun)
```

### Operations in conv

```lean
conv =>
  rw [lemma]     -- Rewrite at focus
  simp           -- Simplify at focus
  ring           -- Ring operations at focus
  change expr    -- Replace with defeq expr
  tactic => tac  -- Run arbitrary tactic
```

### Practical Examples

```lean
-- Rewrite only second occurrence
example (h : a = b) : a + a = a + b := by
  conv => rhs; rhs; rw [← h]
  rfl

-- Simplify under binder
example : (fun x : Nat => x + 0) = (fun x => x) := by
  conv => ext x; simp

-- Rewrite inside function
example (h : f = g) : (fun x => f x + 1) = (fun x => g x + 1) := by
  conv => ext x; lhs; rw [h]
```

---

## Computational Considerations

### What's Computational?

| Feature | Computes? |
|---------|-----------|
| Functions on data | Yes |
| Pattern matching | Yes |
| Proofs (Prop) | Erased at runtime |
| Decidable instances | Yes |
| Classical.choice | No |
| Quotient.lift | Yes (if f computes) |

### Runtime Erasure

```lean
-- Proofs are erased
def f (n : Nat) (h : n > 0) : Nat := n - 1
-- At runtime: just (n : Nat) → Nat

-- Subtype computes (erases proof)
def g (n : {n : Nat // n > 0}) : Nat := n.val - 1
-- At runtime: just Nat → Nat
```

---

## Sources

- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
- [Axioms and Computation](https://lean-lang.org/theorem_proving_in_lean4/axioms_and_computation.html)
