---
name: lean-tp-propositions
description: Curry-Howard correspondence and logical connectives. Use when constructing proofs, understanding proof terms, or working with And/Or/Not/implication.
allowed-tools: Read, Grep, Glob
---

# Lean 4 Propositions and Proofs

Curry-Howard correspondence and logical connectives in Lean. Use when constructing proofs of logical statements, understanding proof terms, or working with And/Or/Not.

**Trigger terms**: "proposition", "proof", "And", "Or", "Not", "implication", "Curry-Howard", "logical connective", "prove"

---

## Core Concept: Propositions as Types

**Curry-Howard correspondence**:
- Propositions are types in `Prop`
- Proofs are terms inhabiting those types
- To prove `p : Prop`, construct a term `t : p`

```lean
-- Proposition (a type)
#check (∀ p q : Prop, p → q → p) -- Prop

-- Proof (a term)
theorem t1 (p q : Prop) : p → q → p :=
  fun hp _ => hp
```

---

## Implication (→)

**Proof pattern**: Lambda abstraction (assume hypothesis, derive conclusion)

```lean
-- To prove p → q: assume p, construct q
example (hp : p) (hq : q) : p := hp

-- Lambda explicitly
example : p → q → p := fun hp _ => hp
```

---

## Conjunction (∧)

**Introduction** - Combine two proofs:
```lean
And.intro hp hq : p ∧ q
⟨hp, hq⟩ : p ∧ q          -- Anonymous constructor
```

**Elimination** - Extract components:
```lean
h.left  : p    -- And.left h
h.right : q    -- And.right h
```

**Example**:
```lean
example (h : p ∧ q) : q ∧ p := ⟨h.right, h.left⟩
```

---

## Disjunction (∨)

**Introduction** - Provide one side:
```lean
Or.inl hp : p ∨ q    -- From left
Or.inr hq : p ∨ q    -- From right
```

**Elimination** - Case analysis:
```lean
example (h : p ∨ q) : q ∨ p :=
  h.elim
    (fun hp => Or.inr hp)
    (fun hq => Or.inl hq)

-- Or with match
match h with
| Or.inl hp => Or.inr hp
| Or.inr hq => Or.inl hq
```

---

## Negation (¬)

**Definition**: `¬p := p → False`

**To prove ¬p**: Assume p, derive False
```lean
example (hpq : p → q) (hnq : ¬q) : ¬p :=
  fun hp => hnq (hpq hp)
```

**From contradiction**: Derive anything
```lean
absurd hp hnp : q    -- From hp : p and hnp : ¬p
False.elim hf : q    -- From hf : False
```

---

## Proof Constructs

**`have`** - Introduce intermediate step:
```lean
example (h : p ∧ q) : q ∧ p :=
  have hp : p := h.left
  have hq : q := h.right
  ⟨hq, hp⟩
```

**`show ... from`** - Explicit result type:
```lean
show q ∧ p from And.intro hq hp
```

**`suffices`** - Backward reasoning:
```lean
suffices h : intermediate from use_h
-- now prove intermediate
```

---

## Quick Reference

| Connective | Introduction | Elimination |
|------------|--------------|-------------|
| `p → q` | `fun hp => ...` | `f hp` (apply) |
| `p ∧ q` | `⟨hp, hq⟩` | `h.left`, `h.right` |
| `p ∨ q` | `Or.inl hp`, `Or.inr hq` | `h.elim f g` |
| `¬p` | `fun hp => ...False` | `absurd hp hnp` |
| `True` | `trivial` | - |
| `False` | - | `False.elim h` |

---

## Common Mistakes

**Forgetting to handle both Or cases**:
```lean
-- ❌ Incomplete
example (h : p ∨ q) : r := ...  -- Must handle both

-- ✓ Handle both
h.elim (fun hp => ...) (fun hq => ...)
```

**Confusing ∧ and →**:
```lean
-- ❌ p ∧ q is NOT p → q
-- ∧ means "both hold", → means "implies"

-- ✓ From p ∧ q you have both p AND q
-- From p → q you get q only IF you have p
```

---

## See Also

- `lean-tp-foundations` - Type theory background
- `lean-tp-quantifiers` - Universal and existential quantifiers
- `lean-tp-tactics` - Tactic mode proofs

**Source**: [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
