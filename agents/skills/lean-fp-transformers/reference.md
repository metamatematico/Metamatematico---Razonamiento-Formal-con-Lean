# Lean 4 Monad Transformers Deep Dive

Extended reference for transformer mechanics, stacking semantics, and effect patterns.

---

## Transformer Anatomy

A monad transformer takes a monad and returns a new monad with additional capabilities:

```lean
-- Pattern: Transformer m α = m (SomeWrapper α)
def OptionT (m : Type → Type) (α : Type) := m (Option α)
def ExceptT (ε m : Type → Type) (α : Type) := m (Except ε α)
def StateT (σ : Type) (m : Type → Type) (α : Type) := σ → m (α × σ)
def ReaderT (ρ : Type) (m : Type → Type) (α : Type) := ρ → m α
def WriterT (ω : Type) (m : Type → Type) (α : Type) := m (α × ω)
```

---

## Transformer Implementations

### OptionT Complete

```lean
def OptionT (m : Type → Type) (α : Type) := m (Option α)

namespace OptionT
  def mk (x : m (Option α)) : OptionT m α := x
  def run (x : OptionT m α) : m (Option α) := x

  instance [Monad m] : Monad (OptionT m) where
    pure x := mk (pure (some x))
    bind x f := mk do
      match ← x.run with
      | none => pure none
      | some v => (f v).run

  def fail [Monad m] : OptionT m α := mk (pure none)
end OptionT
```

### ExceptT Complete

```lean
def ExceptT (ε : Type) (m : Type → Type) (α : Type) := m (Except ε α)

namespace ExceptT
  def mk (x : m (Except ε α)) : ExceptT ε m α := x
  def run (x : ExceptT ε m α) : m (Except ε α) := x

  instance [Monad m] : Monad (ExceptT ε m) where
    pure x := mk (pure (Except.ok x))
    bind x f := mk do
      match ← x.run with
      | Except.error e => pure (Except.error e)
      | Except.ok v => (f v).run

  def throw [Monad m] (e : ε) : ExceptT ε m α :=
    mk (pure (Except.error e))

  def tryCatch [Monad m] (x : ExceptT ε m α)
      (handler : ε → ExceptT ε m α) : ExceptT ε m α := mk do
    match ← x.run with
    | Except.error e => (handler e).run
    | Except.ok v => pure (Except.ok v)
end ExceptT
```

### StateT Complete

```lean
def StateT (σ : Type) (m : Type → Type) (α : Type) := σ → m (α × σ)

namespace StateT
  def mk (f : σ → m (α × σ)) : StateT σ m α := f
  def run (x : StateT σ m α) (s : σ) : m (α × σ) := x s

  instance [Monad m] : Monad (StateT σ m) where
    pure x := mk fun s => pure (x, s)
    bind x f := mk fun s => do
      let (a, s') ← x.run s
      (f a).run s'

  def get [Monad m] : StateT σ m σ := mk fun s => pure (s, s)
  def set [Monad m] (s : σ) : StateT σ m Unit := mk fun _ => pure ((), s)
  def modify [Monad m] (f : σ → σ) : StateT σ m Unit :=
    mk fun s => pure ((), f s)
  def modifyGet [Monad m] (f : σ → (α × σ)) : StateT σ m α :=
    mk fun s => let (a, s') := f s; pure (a, s')
end StateT
```

### ReaderT Complete

```lean
def ReaderT (ρ : Type) (m : Type → Type) (α : Type) := ρ → m α

namespace ReaderT
  def mk (f : ρ → m α) : ReaderT ρ m α := f
  def run (x : ReaderT ρ m α) (env : ρ) : m α := x env

  instance [Monad m] : Monad (ReaderT ρ m) where
    pure x := mk fun _ => pure x
    bind x f := mk fun env => do
      let a ← x.run env
      (f a).run env

  def read [Monad m] : ReaderT ρ m ρ := mk pure
  def local [Monad m] (f : ρ → ρ) (x : ReaderT ρ m α) : ReaderT ρ m α :=
    mk fun env => x.run (f env)
end ReaderT
```

---

## Stacking Semantics Deep Dive

### ExceptT (StateT ...) vs StateT (ExceptT ...)

```lean
-- Type 1: ExceptT ε (StateT σ Id)
-- Unwraps to: σ → (Except ε α × σ)
-- On error: state IS updated (inner monad commits)

-- Type 2: StateT σ (ExceptT ε Id)
-- Unwraps to: σ → Except ε (α × σ)
-- On error: state is LOST (error wraps everything)
```

### Concrete Example

```lean
def action1 : ExceptT String (StateT Nat Id) Unit := do
  StateT.modify (· + 1)  -- State: 0 → 1
  ExceptT.throw "error"  -- Error thrown
  StateT.modify (· + 1)  -- Never runs

-- Running: state = 1 (persisted before error)
let result := (action1.run.run 0)
-- result = (Except.error "error", 1)

def action2 : StateT Nat (ExceptT String Id) Unit := do
  StateT.modify (· + 1)  -- Would update state
  MonadExcept.throw "error"  -- Error thrown
  StateT.modify (· + 1)  -- Never runs

-- Running: state = 0 (error discards all state changes)
let result := action2.run 0
-- result = Except.error "error"
```

---

## MonadLift and MonadLiftT

### Lifting Basics

```lean
class MonadLift (m : Type → Type) (n : Type → Type) where
  monadLift : m α → n α

-- Auto-generated for transformers
instance [Monad m] : MonadLift m (StateT σ m) where
  monadLift x := fun s => do let a ← x; pure (a, s)
```

### Transitive Lifting

```lean
-- MonadLiftT for transitive closure
class MonadLiftT (m n : Type → Type) where
  monadLift : m α → n α

-- Allows lifting through multiple layers
def liftIO [MonadLiftT IO m] (x : IO α) : m α := MonadLiftT.monadLift x
```

---

## Effect Type Classes

### MonadState

```lean
class MonadState (σ : Type) (m : Type → Type) where
  get : m σ
  set : σ → m Unit
  modifyGet : (σ → α × σ) → m α

-- Derived operations
def modify [MonadState σ m] [Monad m] (f : σ → σ) : m Unit := do
  let s ← MonadState.get
  MonadState.set (f s)
```

### MonadExcept

```lean
class MonadExcept (ε : Type) (m : Type → Type) where
  throw : ε → m α
  tryCatch : m α → (ε → m α) → m α

-- Derived operations
def catch [MonadExcept ε m] (x : m α) (h : ε → m α) : m α :=
  MonadExcept.tryCatch x h
```

### MonadReader

```lean
class MonadReader (ρ : Type) (m : Type → Type) where
  read : m ρ

-- Using local
class MonadReaderOf (ρ : Type) (m : Type → Type) extends MonadReader ρ m where
  local : (ρ → ρ) → m α → m α
```

---

## Common App Monad Stacks

### Web App Stack

```lean
structure AppConfig where
  dbUrl : String
  logLevel : Nat

structure AppState where
  requestCount : Nat

inductive AppError where
  | notFound : AppError
  | unauthorized : AppError

-- Stack: Config → State → Error → IO
abbrev AppM := ReaderT AppConfig (StateT AppState (ExceptT AppError IO))

-- Using the stack
def handleRequest : AppM String := do
  let cfg ← read
  modify fun s => { s with requestCount := s.requestCount + 1 }
  if cfg.logLevel > 0 then
    liftIO (IO.println "Processing request")
  pure "Response"
```

### Parser Stack

```lean
structure ParseState where
  input : String
  position : Nat

abbrev Parser := StateT ParseState (Except String)

def char (expected : Char) : Parser Char := do
  let s ← StateT.get
  if h : s.position < s.input.length then
    let c := s.input.get ⟨s.position, h⟩
    if c == expected then
      StateT.set { s with position := s.position + 1 }
      pure c
    else
      throw s!"Expected '{expected}', got '{c}'"
  else
    throw "Unexpected end of input"
```

---

## Best Practices

### Put Exceptions on the Outside

```lean
-- Usually: ExceptT wrapping everything else
-- Why: Clean error handling at top level

abbrev App := ExceptT AppError (StateT AppState (ReaderT Config IO))

-- Easy to pattern match on result
match ← app.run.run initialState config with
| Except.ok (result, finalState) => ...
| Except.error e => ...
```

### Use Type Classes for Generic Code

```lean
-- ❌ Specific to one stack
def inc : StateT Nat (ExceptT String IO) Unit := ...

-- ✓ Works with any stack providing these effects
def inc [Monad m] [MonadState Nat m] : m Unit := do
  modify (· + 1)
```

---

## Sources

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
- [Monad Transformers chapter](https://lean-lang.org/functional_programming_in_lean/monad-transformers.html)
