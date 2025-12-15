---
name: lean-tp-advanced
description: Axioms, classical logic, quotients, and noncomputable definitions. Use for excluded middle, proof by contradiction, quotient types, or understanding Lean's foundational axioms.
allowed-tools: Read, Grep, Glob
---

# Lean 4 Advanced Theorem Proving

Axioms, classical logic, quotients, and computational considerations. Use when needing excluded middle, working with quotient types, or understanding Lean's foundations.

**Trigger terms**: "axiom", "classical", "excluded middle", "quotient", "propext", "choice", "noncomputable"

---

## Classical vs Constructive

**Constructive** (default): Proofs are programs, must compute witnesses.

**Classical**: Allows non-computational proofs via axioms.

---

## Classical Axioms

### Excluded Middle

```lean
-- Every proposition is true or false
axiom Classical.em (p : Prop) : p ∨ ¬p

-- Proof by contradiction
theorem byContradiction (h : ¬p → False) : p :=
  (Classical.em p).elim id (fun hnp => absurd (h hnp) hnp)
```

### Propositional Extensionality

```lean
-- Props with same truth value are equal
axiom propext : (a ↔ b) → a = b
```

### Choice

```lean
-- Extract witness from existence proof
axiom Classical.choice : Nonempty α → α

-- Indefinite description
noncomputable def Classical.choose (h : ∃ x, p x) : α
```

---

## Using Classical Logic

```lean
open Classical in
theorem dne (h : ¬¬p) : p :=
  (em p).elim id (fun hnp => absurd hnp h)

-- by_cases: case split on decidability
example (p : Prop) : p ∨ ¬p := by
  by_cases h : p
  · left; exact h
  · right; exact h
```

---

## Quotient Types

Identify elements via equivalence relation:

```lean
-- Define equivalence
def mySetoid : Setoid α where
  r := myRelation
  iseqv := ⟨refl, symm, trans⟩

-- Create quotient
def MyQuotient := Quotient mySetoid

-- Lift functions to quotient
def lift (f : α → β) (h : ∀ a b, a ≈ b → f a = f b) : MyQuotient → β :=
  Quotient.lift f h
```

---

## Noncomputable Definitions

Mark definitions using choice:

```lean
noncomputable def inverse [Inhabited α] (f : α → β) (b : β) : α :=
  if h : ∃ a, f a = b
  then Classical.choose h
  else default
```

**Why noncomputable**: `Classical.choice` doesn't compute—can't run with `#eval`.

---

## When to Use Classical

| Pattern | Use |
|---------|-----|
| Proof by contradiction | `Classical.byContradiction` |
| Case split without decidability | `by_cases` |
| Extract witness non-constructively | `Classical.choose` |
| Prove prop equality | `propext` |

**Avoid classical when**: You need computational content, want to extract programs.

---

## Axiom Compatibility

Lean's axioms are consistent:

| Axiom | Purpose | Computational? |
|-------|---------|----------------|
| `propext` | Prop equality from ↔ | Yes (props erased) |
| `Quot.sound` | Quotient equality | Yes |
| `Classical.choice` | Witness extraction | No |

---

## Common Mistakes

**Using choice when not needed**:
```lean
-- ❌ Noncomputable unnecessarily
noncomputable def double (n : Nat) := n + n

-- ✓ Keep computable when possible
def double (n : Nat) := n + n
```

**Forgetting `open Classical`**:
```lean
-- ❌ em not in scope
example : p ∨ ¬p := em p

-- ✓ Open namespace
open Classical in
example : p ∨ ¬p := em p
```

---

## Conversion Mode (conv)

Precise rewriting control:

```lean
-- Rewrite specific occurrence
example (h : a = b) : a + a = a + b := by
  conv =>
    lhs       -- Focus on left-hand side
    rhs       -- Then right argument of +
    rw [h]    -- Rewrite there only
```

**conv tactics**: `lhs`, `rhs`, `arg n`, `enter [path]`, `rw`, `simp`

---

## See Also

- `lean-tp-foundations` - Type theory basics
- `lean-tp-tactics` - General tactics
- `lean-tp-propositions` - Logical connectives

**Source**: [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
