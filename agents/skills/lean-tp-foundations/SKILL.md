---
name: lean-tp-foundations
description: Dependent type theory fundamentals for theorem proving. Use when understanding universes, Type/Prop, dependent types, or the Calculus of Constructions foundation.
allowed-tools: Read, Grep, Glob
---

# Lean 4 Theorem Proving Foundations

Dependent type theory fundamentals for theorem proving in Lean 4. Use when understanding type universes, dependent types, or the theoretical foundation of proofs.

**Trigger terms**: "dependent type", "universe", "Type", "Prop", "type theory", "calculus of constructions", "Lean foundations"

---

## Core Concept

Lean is based on the **Calculus of Constructions with inductive types** - a dependent type theory where:
- Types are first-class objects with their own types
- Propositions are types in `Prop`
- Proofs are terms inhabiting proposition types

---

## Universe Hierarchy

Types have types, organized in levels to avoid paradoxes:

```lean
#check Nat       -- Nat : Type
#check Type      -- Type : Type 1
#check Type 1    -- Type 1 : Type 2
-- Type n : Type (n+1)  for all n

#check Prop      -- Prop : Type (special universe for propositions)
```

**Key distinction**: `Prop` is proof-irrelevant (all proofs of same proposition are equal).

---

## Function Types (Right-Associative)

```lean
-- These are equivalent (currying):
Nat → Nat → Nat
Nat → (Nat → Nat)

-- Partial application:
def add : Nat → Nat → Nat := fun m n => m + n
def add5 : Nat → Nat := add 5
```

---

## Dependent Types

Return type depends on argument value:

```lean
-- Length-indexed vector
def Vec (α : Type) : Nat → Type
  | 0     => Unit
  | n + 1 => α × Vec α n

#check Vec Nat 0   -- Unit
#check Vec Nat 3   -- Nat × (Nat × (Nat × Unit))

-- Dependent function type
-- Π (n : Nat), Vec Nat n  (or ∀ (n : Nat), Vec Nat n)
```

**When to use**: Type-safe operations on length-indexed structures, refined types, proof-carrying data.

---

## Universe Polymorphism

```lean
-- Definition works at any universe level
def List.{u} (α : Type u) : Type u := ...

#check List.{0} Nat     -- List in Type
#check List.{1} Type    -- List of Types
```

---

## Commands

| Command | Purpose |
|---------|---------|
| `#check expr` | Display type |
| `#eval expr` | Evaluate computationally |
| `#print name` | Show definition |
| `#reduce expr` | Reduce to normal form |

---

## When to Use

| Pattern | Use Case |
|---------|----------|
| Simple types | `Nat`, `Bool` - ordinary data |
| Function types | `α → β` - computations, implications |
| Product types | `α × β` - pairs, conjunctions |
| Dependent types | `(x : α) → β x` - length-indexed, refined |
| Universe polymorphism | Generic across all type levels |

---

## Common Mistakes

**Mixing universe levels**:
```lean
-- ❌ Type mismatch
def bad : Type := Type

-- ✓ Proper universe
def good : Type 1 := Type
```

**Forgetting right-associativity**:
```lean
-- ❌ Misunderstanding
-- Nat → Nat → Nat is NOT (Nat → Nat) → Nat

-- ✓ Remember: Nat → Nat → Nat = Nat → (Nat → Nat)
-- This is a curried two-argument function
```

---

## See Also

- `lean-tp-propositions` - Propositions and proofs
- `lean-tp-tactics` - Tactic mode for proofs
- `lean-fp-basics` - Programming fundamentals

**Source**: [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
