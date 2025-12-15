---
name: lean-tp-quantifiers
description: Universal/existential quantifiers and equality reasoning. Use when proving forall/exists, equational reasoning with rfl, calc chains, or substitution.
allowed-tools: Read, Grep, Glob
---

# Lean 4 Quantifiers and Equality

Universal/existential quantifiers and equality reasoning. Use when proving properties for all values, existence claims, or equational reasoning.

**Trigger terms**: "forall", "exists", "∀", "∃", "equality", "rfl", "calc", "rewrite", "subst"

---

## Universal Quantifier (∀)

**Syntax**: `∀ x : α, p x` (same as `(x : α) → p x`)

**Introduction** - Prove for arbitrary value:
```lean
example : ∀ x : Nat, x + 0 = x := fun x => rfl

-- In tactic mode
example : ∀ x : Nat, x + 0 = x := by
  intro x
  rfl
```

**Elimination** - Apply to specific term:
```lean
-- Given h : ∀ x, p x and t : Nat
-- Get: h t : p t
```

---

## Existential Quantifier (∃)

**Syntax**: `∃ x : α, p x`

**Introduction** - Provide witness:
```lean
example : ∃ x : Nat, x > 0 := ⟨1, Nat.one_pos⟩

-- Or use 'use' tactic
example : ∃ x : Nat, x > 0 := by
  use 1
  decide
```

**Elimination** - Extract witness:
```lean
example (h : ∃ x, p x) : q := by
  match h with
  | ⟨w, hw⟩ => -- w is witness, hw : p w
    ...

-- Or with obtain
example (h : ∃ x, p x) : q := by
  obtain ⟨w, hw⟩ := h
  ...
```

---

## Equality

**Reflexivity** - `rfl` proves `a = a`:
```lean
example : 2 + 3 = 5 := rfl
example (f : α → β) (a : α) : (fun x => f x) a = f a := rfl
```

**Symmetry and Transitivity**:
```lean
Eq.symm (h : a = b) : b = a
Eq.trans (h1 : a = b) (h2 : b = c) : a = c

-- Dot notation
h.symm : b = a
```

---

## Substitution

Replace equals with equals:

```lean
-- Triangle notation (▸)
example (h : a = b) (hp : p a) : p b := h ▸ hp

-- Eq.subst
example (h : a = b) (hp : p a) : p b := Eq.subst h hp
```

**Direction**: `h : a = b` replaces `a` with `b`

---

## Calculational Proofs (calc)

Chain equalities:

```lean
example (h1 : a = b) (h2 : b = c) (h3 : c = d) : a = d :=
  calc a = b := h1
    _ = c := h2
    _ = d := h3

-- With rewrites
example (h : a = b + 1) : a + c = b + 1 + c :=
  calc a + c = (b + 1) + c := by rw [h]
    _ = b + 1 + c := rfl
```

**Placeholder `_`**: Previous right-hand side.

---

## Congruence

Equality through functions:

```lean
congrArg (f : α → β) (h : a = b) : f a = f b
congrFun (h : f = g) (a : α) : f a = g a
congr (hf : f = g) (ha : a = b) : f a = g b
```

---

## Quick Reference

| Need | Use |
|------|-----|
| Prove `∀ x, p x` | `intro x` then prove `p x` |
| Use `h : ∀ x, p x` | Apply: `h t` gives `p t` |
| Prove `∃ x, p x` | `use w` with witness |
| Use `h : ∃ x, p x` | `obtain ⟨w, hw⟩ := h` |
| Prove `a = a` | `rfl` |
| Reverse equality | `h.symm` |
| Chain equalities | `calc` |
| Substitute in goal | `rw [h]` |
| Substitute in hyp | `h ▸ hp` |

---

## Common Mistakes

**Wrong substitution direction**:
```lean
-- h : a = b, goal: p b, have: hp : p a
example (h : a = b) (hp : p a) : p b := h ▸ hp  -- ✓

-- h : a = b, goal: p a, have: hp : p b
example (h : a = b) (hp : p b) : p a := h.symm ▸ hp  -- Need symm!
```

**Forgetting rfl works with computation**:
```lean
-- ❌ Too complex
example : 2 + 3 = 5 := by omega

-- ✓ Just use rfl (computes to same value)
example : 2 + 3 = 5 := rfl
```

---

## See Also

- `lean-tp-propositions` - Logical connectives
- `lean-tp-tactics` - Rewriting tactics
- `lean-tp-tactic-selection` - Choosing tactics

**Source**: [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
