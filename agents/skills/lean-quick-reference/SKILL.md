---
name: lean-quick-reference
description: Consolidated cheatsheets for Lean 4 syntax, tactics, type classes, monads, and common patterns. Use for quick lookup or when you need a reminder.
allowed-tools: Read, Grep, Glob
---

# Lean 4 Quick Reference

Consolidated cheatsheets for Lean 4 syntax, tactics, type classes, and common patterns. Use for quick lookup of syntax or when you need a reminder.

**Trigger terms**: "lean syntax", "cheatsheet", "quick reference", "lean help", "how to lean"

---

## Type Definition Syntax

```lean
-- Structure (product type)
structure Point where
  x : Float
  y : Float
  deriving Repr

-- Inductive (sum type)
inductive Option (α : Type) where
  | none : Option α
  | some : α → Option α

-- Type alias
abbrev Nat2 := Nat × Nat
```

---

## Function Definition

```lean
-- Basic
def add (x y : Nat) : Nat := x + y

-- Pattern matching
def isZero : Nat → Bool
  | 0 => true
  | _ => false

-- Where clause
def f (x : Nat) : Nat := helper x
where helper n := n + 1

-- Lambda
fun x => x + 1
λ x => x + 1
```

---

## Type Class Quick Reference

| Class | Provides | Infix |
|-------|----------|-------|
| `Add` | `add` | `+` |
| `Mul` | `mul` | `*` |
| `BEq` | `beq` | `==` |
| `Ord` | `compare` | `<`, `≤` |
| `ToString` | `toString` | - |
| `Repr` | `repr` | - |
| `Functor` | `map` | `<$>` |
| `Applicative` | `pure`, `seq` | `<*>` |
| `Monad` | `pure`, `bind` | `>>=` |
| `Alternative` | `failure`, `orElse` | `<|>` |

---

## Monad Cheatsheet

| Monad | Purpose | Create | Fail |
|-------|---------|--------|------|
| `Option` | Maybe value | `some x` | `none` |
| `Except ε` | Error handling | `Except.ok x` | `Except.error e` |
| `State σ` | Mutable state | `pure x` | - |
| `Reader ρ` | Environment | `pure x` | - |
| `IO` | Side effects | `pure x` | `throw` |

**do-notation**:
```lean
do let x ← action1    -- bind
   let y := expr       -- let
   action2             -- sequence
   pure result         -- return
```

---

## Tactic Cheatsheet

| Tactic | Purpose | Example |
|--------|---------|---------|
| `rfl` | Reflexive equality | `example : 1 = 1 := by rfl` |
| `exact` | Provide proof term | `exact hp` |
| `apply` | Apply lemma | `apply And.intro` |
| `intro` | Introduce hypothesis | `intro hp` |
| `constructor` | Apply constructor | Splits `∧` goals |
| `left/right` | Choose `∨` branch | `left; exact hp` |
| `cases` | Case analysis | `cases h` |
| `induction` | Induction | `induction n` |
| `rw` | Rewrite | `rw [h]` |
| `simp` | Simplify | `simp [lemmas]` |
| `decide` | Decidable props | `by decide` |
| `omega` | Linear arithmetic | `by omega` |
| `trivial` | Prove `True` | `trivial` |
| `contradiction` | From contradictions | `contradiction` |
| `have` | Introduce fact | `have h : T := proof` |
| `show` | Clarify goal | `show T` |

---

## Logical Connectives

| Connective | Type | Intro | Elim |
|------------|------|-------|------|
| `→` | Function | `fun hp => ...` | `f hp` |
| `∧` | `And` | `⟨hp, hq⟩` | `h.left`, `h.right` |
| `∨` | `Or` | `Or.inl hp` | `cases h` |
| `¬` | `Not` | `fun hp => ...` | `absurd hp hnp` |
| `∀` | `Pi` | `fun x => ...` | `h x` |
| `∃` | `Exists` | `⟨w, hw⟩` | `obtain ⟨w, hw⟩ := h` |
| `↔` | `Iff` | `⟨mp, mpr⟩` | `h.mp`, `h.mpr` |

---

## Commands

| Command | Purpose |
|---------|---------|
| `#check expr` | Show type |
| `#eval expr` | Evaluate |
| `#print name` | Show definition |
| `#reduce expr` | Reduce to normal form |
| `example : T := proof` | Anonymous theorem |
| `theorem name : T := proof` | Named theorem |
| `def name : T := expr` | Definition |

---

## Common Patterns

**Safe indexing**:
```lean
arr.get ⟨i, by decide⟩  -- Fin for bounds proof
arr[i]?                  -- Option result
arr[i]!                  -- Panic if invalid
```

**Pattern matching**:
```lean
match x with
| pattern1 => result1
| pattern2 => result2
```

**If-then-else with hypothesis**:
```lean
if h : condition then
  -- h : condition available here
else
  -- h : ¬condition available here
```

---

## File Structure

```lean
import Lean           -- Import module
namespace MySpace     -- Open namespace
section MySection     -- Scoped section
variable (x : Nat)    -- Implicit parameter
open OtherSpace       -- Bring names into scope
end MySpace
```

---

## See Also

Skills for detailed coverage:
- `lean-fp-basics` - Language fundamentals
- `lean-fp-monads` - Monad details
- `lean-tp-tactics` - Tactic details
- `lean-tp-tactic-selection` - Decision trees

**Sources**:
- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
