---
name: lean-fp-monads
description: Monadic effect handling in Lean including Option, Except, State, Reader, and do-notation. Use when chaining computations that may fail, need state, or require environment access.
allowed-tools: Read, Grep, Glob
---

# Lean 4 Monads

Monadic effect handling in Lean: Option, Except, State, Reader, and do-notation. Use when chaining computations that may fail, need state, or require environment access.

**Trigger terms**: "monad", "Option", "Except", "State", "Reader", "do notation", "bind", ">>=", "effect", "error handling"

---

## The Monad Type Class

```lean
class Monad (m : Type → Type) where
  pure : α → m α                    -- Wrap value
  bind : m α → (α → m β) → m β      -- Chain operations

-- Infix: >>= is bind
action >>= continuation
```

---

## Option Monad

**When to use**: Computation may fail, no error details needed.

```lean
instance : Monad Option where
  pure x := some x
  bind opt next := match opt with
    | none => none
    | some x => next x

-- Example: Safe lookup
def safeLookup (xs : List α) (i : Nat) : Option α := xs[i]?

def example := do
  let first ← safeLookup xs 0
  let second ← safeLookup xs 1
  pure (first, second)
```

---

## Except Monad

**When to use**: Need error messages or distinct failure modes.

```lean
instance : Monad (Except ε) where
  pure x := Except.ok x
  bind result next := match result with
    | Except.error e => Except.error e
    | Except.ok x => next x

-- Example: Division with error
def safeDiv (x y : Int) : Except String Int :=
  if y == 0 then Except.error s!"Division by zero: {x}/{y}"
  else pure (x / y)
```

---

## State Monad

**When to use**: Thread mutable state through computations.

```lean
def State (σ α : Type) := σ → (σ × α)

def get : State σ σ := fun s => (s, s)
def set (s : σ) : State σ Unit := fun _ => (s, ())
def modify (f : σ → σ) : State σ Unit := fun s => (f s, ())

-- Example: Counter
def increment : State Nat Unit := modify (· + 1)
```

---

## Reader Monad

**When to use**: Read-only configuration/environment.

```lean
def Reader (ρ α : Type) := ρ → α

def read : Reader ρ ρ := fun env => env

-- Example: Config access
def getPort : Reader Config Nat := do
  let cfg ← read
  pure cfg.port
```

---

## do-Notation

Desugars to `>>=` (bind):

```lean
-- do-notation
do let x ← action1
   let y ← action2
   pure (x + y)

-- Desugars to:
action1 >>= fun x =>
action2 >>= fun y =>
pure (x + y)
```

**Desugaring rules**:
- `do E` → `E`
- `do let x ← E; ...` → `E >>= fun x => do ...`
- `do E; ...` → `E >>= fun () => do ...`
- `do let x := E; ...` → `let x := E; do ...`

---

## Monad Selection Decision Tree

```
Does your computation need:
├─ May fail silently? → Option
├─ May fail with error info? → Except ε
├─ Read-only environment? → Reader ρ
├─ Mutable state? → State σ
├─ Real I/O effects? → IO
└─ Multiple effects? → Monad transformers
```

---

## Common Mistakes

**Using Monad when Applicative suffices**:
```lean
-- ❌ Forces sequential (loses parallelism info)
do let a ← actionA
   let b ← actionB
   pure (f a b)

-- ✓ Use Applicative when independent
f <$> actionA <*> actionB
```

**Forgetting short-circuit behavior**:
```lean
-- Option short-circuits on first none
-- Except short-circuits on first error
-- Both sides won't execute if left fails!
```

---

## See Also

- `lean-fp-functor-applicative` - Functor, Applicative
- `lean-fp-transformers` - Combining effects
- `lean-fp-basics` - Language fundamentals

**Source**: [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
