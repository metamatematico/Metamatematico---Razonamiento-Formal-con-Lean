---
name: lean-tp-tactics
description: Core tactics for theorem proving including apply, exact, intro, rw, simp, cases, and induction. Use when constructing proofs step-by-step in tactic mode.
allowed-tools: Read, Grep, Glob
---

# Lean 4 Tactics

Core tactics for theorem proving in Lean. Use when constructing proofs step-by-step rather than writing proof terms directly.

**Trigger terms**: "tactic", "apply", "exact", "intro", "rw", "simp", "cases", "induction", "by", "proof"

---

## Entering Tactic Mode

```lean
theorem example (hp : p) (hq : q) : p ∧ q := by
  apply And.intro
  exact hp
  exact hq
```

**Separators**: newlines, semicolons (`;`), or `<;>` (apply to all goals)

---

## Core Tactics

### apply

Apply a lemma/constructor whose conclusion matches the goal:

```lean
example (hp : p) (hq : q) : p ∧ q := by
  apply And.intro   -- Creates two subgoals: p and q
  exact hp
  exact hq
```

### exact

Provide a term that exactly solves the goal:

```lean
example (hp : p) : p := by exact hp
```

### intro / intros

Introduce hypotheses from `→` or `∀`:

```lean
example : p → q → p := by
  intro hp hq    -- hp : p, hq : q in context
  exact hp

example : ∀ x : Nat, x = x := by
  intro x
  rfl
```

### constructor / left / right

Apply constructor of inductive type:

```lean
example (hp : p) (hq : q) : p ∧ q := by
  constructor    -- Splits into two goals
  exact hp
  exact hq

example (hp : p) : p ∨ q := by left; exact hp
example (hq : q) : p ∨ q := by right; exact hq
```

---

## Rewriting

### rw / rewrite

Rewrite using equalities (left-to-right):

```lean
example (h : a = b) : a + c = b + c := by rw [h]

-- Reverse direction with ←
example (h : a = b) : b = a := by rw [← h]

-- Multiple rewrites
example (h1 : a = b) (h2 : b = c) : a = c := by rw [h1, h2]
```

### simp

Simplify using lemmas tagged `@[simp]`:

```lean
example : 0 + a = a := by simp

-- Use specific lemmas
example (h : a = b) : a = b := by simp [h]

-- Aggressive simplification
example : complex_expr := by simp_all
```

---

## Case Analysis

### cases

Destruct hypothesis into cases:

```lean
example (h : p ∨ q) : q ∨ p := by
  cases h with
  | inl hp => right; exact hp
  | inr hq => left; exact hq
```

### induction

Prove by induction on inductive type:

```lean
example (n : Nat) : 0 + n = n := by
  induction n with
  | zero => rfl
  | succ n ih => simp [Nat.add_succ, ih]
```

---

## Other Essential Tactics

| Tactic | Purpose |
|--------|---------|
| `rfl` | Prove reflexive equality |
| `trivial` | Prove `True` |
| `decide` | Prove decidable propositions |
| `omega` | Linear arithmetic |
| `assumption` | Find matching hypothesis |
| `contradiction` | Derive from contradictory hypotheses |
| `have h : T := proof` | Introduce auxiliary fact |
| `show T` | Clarify expected goal type |
| `sorry` | Placeholder (admits anything) |

---

## Tactic Selection Quick Reference

| Goal Type | Typical Tactic |
|-----------|----------------|
| `P → Q` | `intro hp` |
| `∀ x, P x` | `intro x` |
| `P ∧ Q` | `constructor` |
| `P ∨ Q` | `left` or `right` |
| `¬P` | `intro hp` (prove `False`) |
| `∃ x, P x` | `use w` |
| `a = b` | `rfl`, `rw`, `simp` |
| Hypothesis `h : P ∨ Q` | `cases h` |
| Inductive type | `induction` or `cases` |

---

## Common Mistakes

**Using `apply` when `exact` is clearer**:
```lean
-- ❌ Less clear intent
example (hp : p) : p := by apply hp

-- ✓ Clearer
example (hp : p) : p := by exact hp
```

**Forgetting `rw` needs equality**:
```lean
-- ❌ h is not an equality
example (h : p) : q := by rw [h]  -- Error!

-- ✓ rw is for a = b style hypotheses
example (h : a = b) : f a = f b := by rw [h]
```

---

## See Also

- `lean-tp-tactic-selection` - Decision trees for choosing tactics
- `lean-tp-propositions` - Logical connectives
- `lean-tp-foundations` - Type theory background

**Source**: [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
