---
name: lean-fp-transformers
description: Combining multiple effects with monad transformers including StateT, ExceptT, ReaderT, and OptionT. Use when you need error handling AND state, or multiple effects together.
allowed-tools: Read, Grep, Glob
---

# Lean 4 Monad Transformers

Combining multiple effects with monad transformers. Use when you need both error handling AND state, or multiple effects together.

**Trigger terms**: "monad transformer", "StateT", "ExceptT", "ReaderT", "OptionT", "lift", "stack"

---

## The Problem

Need both state AND error handling:

```lean
-- Can't use State AND Except separately
-- Need to combine them!
```

---

## OptionT

Add optionality to any monad:

```lean
def OptionT (m : Type → Type) (α : Type) := m (Option α)

instance [Monad m] : Monad (OptionT m) where
  pure x := pure (some x)
  bind x f := do
    match ← x with
    | none => pure none
    | some v => f v
```

---

## ExceptT

Add exceptions to any monad:

```lean
def ExceptT (ε : Type) (m : Type → Type) (α : Type) := m (Except ε α)

instance [Monad m] : Monad (ExceptT ε m) where
  pure x := pure (Except.ok x)
  bind x f := do
    match ← x with
    | Except.error e => pure (Except.error e)
    | Except.ok v => f v

-- Throw and catch
def throw (e : ε) : ExceptT ε m α := pure (Except.error e)
def tryCatch (x : ExceptT ε m α) (handle : ε → ExceptT ε m α) : ExceptT ε m α
```

---

## StateT

Add state to any monad:

```lean
def StateT (σ : Type) (m : Type → Type) (α : Type) := σ → m (α × σ)

instance [Monad m] : Monad (StateT σ m) where
  pure x := fun s => pure (x, s)
  bind x f := fun s => do
    let (v, s') ← x s
    f v s'

-- State operations
def get : StateT σ m σ := fun s => pure (s, s)
def set (s : σ) : StateT σ m Unit := fun _ => pure ((), s)
def modify (f : σ → σ) : StateT σ m Unit := fun s => pure ((), f s)
```

---

## MonadLift

Lift base monad operations:

```lean
class MonadLift (m n : Type → Type) where
  monadLift : m α → n α

-- Automatic lifting with liftM
def liftM [MonadLift m n] (x : m α) : n α := MonadLift.monadLift x
```

---

## Stacking Order Matters!

```lean
-- ExceptT outside StateT: error discards state changes
ExceptT String (StateT Nat Id) α

-- StateT outside ExceptT: state persists across errors
StateT Nat (ExceptT String Id) α
```

**Decision guide**:
```
Should errors:
├─ Discard state changes? → ExceptT (StateT ...)
└─ Preserve state? → StateT (ExceptT ...)
```

---

## Type Class Effects

Use type classes for effect operations:

```lean
class MonadState (σ : Type) (m : Type → Type) where
  get : m σ
  set : σ → m Unit

class MonadExcept (ε : Type) (m : Type → Type) where
  throw : ε → m α
  tryCatch : m α → (ε → m α) → m α

-- Generic code works with any stack providing these effects
def increment [Monad m] [MonadState Nat m] : m Unit := do
  let n ← MonadState.get
  MonadState.set (n + 1)
```

---

## Common Stack Patterns

| Need | Stack |
|------|-------|
| State + Errors (errors reset state) | `ExceptT ε (StateT σ m)` |
| State + Errors (state persists) | `StateT σ (ExceptT ε m)` |
| Config + State | `ReaderT ρ (StateT σ m)` |
| Config + Errors | `ReaderT ρ (ExceptT ε m)` |
| All three | `ReaderT ρ (ExceptT ε (StateT σ m))` |

---

## Common Mistakes

**Wrong stacking order**:
```lean
-- ❌ Unexpected behavior
-- ExceptT (StateT ...) vs StateT (ExceptT ...)
-- These behave DIFFERENTLY on errors!

-- ✓ Think about: what happens to state when error occurs?
```

**Forgetting to lift**:
```lean
-- ❌ Type error in nested monad
def f : StateT Nat (ExceptT String Id) Unit := do
  throw "error"  -- Won't work without lift!

-- ✓ Use MonadExcept or explicit lift
def f : StateT Nat (ExceptT String Id) Unit := do
  MonadExcept.throw "error"
```

---

## See Also

- `lean-fp-monads` - Base monad concepts
- `lean-fp-type-classes` - Type class system
- `lean-fp-functor-applicative` - Abstraction hierarchy

**Source**: [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
