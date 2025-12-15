# Lean 4 Monads Deep Dive

Extended reference for monad mechanics, laws, and advanced patterns.

---

## Monad Laws

Every lawful Monad must satisfy:

```lean
-- Left identity: pure a >>= f  ≡  f a
-- Right identity: m >>= pure   ≡  m
-- Associativity: (m >>= f) >>= g  ≡  m >>= (fun x => f x >>= g)
```

**Why laws matter**:
- Refactoring safety - restructure do-blocks without changing behavior
- Composability - monad transformers rely on laws
- Reasoning - proofs about monadic code

---

## do-Notation Desugaring (Complete)

### Basic Desugaring

| do-notation | Desugars to |
|-------------|-------------|
| `do E` | `E` |
| `do let x ← E; rest` | `E >>= fun x => do rest` |
| `do E; rest` | `E >>= fun () => do rest` |
| `do let x := E; rest` | `let x := E; do rest` |

### Early Return

```lean
-- do-notation with early return
def example (n : Nat) : Option Nat := do
  if n == 0 then return none  -- Early exit
  pure (n + 1)

-- Desugars using a return monad transformer
```

### Mutation Syntax

```lean
-- In StateT or IO
do x ← getState
   setState (x + 1)

-- Mutation shorthand (IO/StateT)
do modify (· + 1)
```

---

## Option Monad Details

### Operations

```lean
none : Option α               -- Failure
some x : Option α             -- Success
opt.getD default : α          -- Get or default
opt.get! : α                  -- Get or panic
opt.map f : Option β          -- Apply to inner
opt.bind f : Option β         -- Chain
opt.isSome : Bool
opt.isNone : Bool
```

### Short-Circuit Semantics

```lean
do let a ← none       -- Entire do-block returns none
   let b ← some 1     -- Never reached
   pure (a + b)
```

### Option.map vs bind

```lean
-- map: transform inner value (if any)
(some 5).map (· + 1)  -- some 6

-- bind: chain computations that may fail
(some 5).bind (fun x => if x > 0 then some x else none)
```

---

## Except Monad Details

### Creating Errors

```lean
Except.error "message" : Except String α   -- Fail with error
Except.ok value : Except String α          -- Success
throw "message"                            -- In do-block
```

### Catching Errors

```lean
def safe : Except String Nat := do
  try
    risky
  catch e =>
    pure 0  -- Default on error

-- Or with tryCatch
Except.tryCatch risky (fun e => pure 0)
```

### Custom Error Types

```lean
inductive MyError where
  | notFound : String → MyError
  | invalid : Nat → MyError

def lookup (key : String) : Except MyError Value := ...
```

---

## State Monad Details

### Core Operations

```lean
get : State σ σ                    -- Read state
set (s : σ) : State σ Unit         -- Replace state
modify (f : σ → σ) : State σ Unit  -- Transform state
modifyGet (f : σ → α × σ) : State σ α  -- Transform and return
```

### Running State

```lean
def computation : State Nat String := do
  let n ← get
  modify (· + 1)
  pure s!"Was {n}"

-- Run with initial state
let (finalState, result) := computation.run 0
-- finalState = 1, result = "Was 0"
```

### State vs StateT

```lean
-- State is actually:
def State (σ α : Type) := StateT σ Id α

-- StateT allows combining with other monads
def StateT (σ : Type) (m : Type → Type) (α : Type) := σ → m (α × σ)
```

---

## Reader Monad Details

### Core Operations

```lean
read : Reader ρ ρ                        -- Get environment
local (f : ρ → ρ) (action) : Reader ρ α  -- Modify env locally
```

### Running Reader

```lean
def computation : Reader Config String := do
  let cfg ← read
  pure s!"Port: {cfg.port}"

let result := computation.run myConfig
```

### ReaderT Pattern

```lean
def ReaderT (ρ : Type) (m : Type → Type) (α : Type) := ρ → m α

-- Common: ReaderT over IO
def App (α : Type) := ReaderT AppConfig IO α
```

---

## Writer Monad

**When to use**: Accumulate output (logs, traces) alongside computation.

```lean
def Writer (ω α : Type) := α × ω

def tell (w : ω) : Writer ω Unit := ((), w)

-- Requires Monoid on ω for combining outputs
instance [Monoid ω] : Monad (Writer ω) where
  pure x := (x, Monoid.one)
  bind (x, w) f :=
    let (y, w') := f x
    (y, Monoid.append w w')
```

---

## IO Monad

### Special Properties

- Not a transformer (wraps runtime)
- Cannot escape (no `run`)
- Supports mutation, exceptions, FFI

### Common IO Operations

```lean
IO.print : String → IO Unit
IO.println : String → IO Unit
IO.getLine : IO String
IO.readFile : FilePath → IO String
IO.writeFile : FilePath → String → IO Unit
```

### Error Handling in IO

```lean
def risky : IO Unit := do
  try
    IO.writeFile "test.txt" "hello"
  catch e =>
    IO.eprintln s!"Error: {e}"
```

---

## Monad Comparison Table

| Monad | Effect | Create Failure | Handle Failure |
|-------|--------|----------------|----------------|
| `Option` | May fail | `none` | `match`, `getD` |
| `Except ε` | Fail with error | `throw e` | `try/catch` |
| `State σ` | Mutable state | N/A | N/A |
| `Reader ρ` | Environment | N/A | N/A |
| `IO` | Real world | `throw e` | `try/catch` |

---

## Common Patterns

### Chaining with `>>=`

```lean
safeLookup xs 0 >>= fun a =>
safeLookup xs 1 >>= fun b =>
pure (a + b)
```

### Sequence with `>>`

```lean
action1 >> action2  -- Ignore result of action1
-- Same as: action1 >>= fun _ => action2
```

### mapM / forM

```lean
-- Apply monadic function to list
List.mapM f [a, b, c]  -- m [f a, f b, f c]

-- For side effects only
List.forM [a, b, c] action  -- m Unit
```

---

## Sources

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
- [Monad chapter](https://lean-lang.org/functional_programming_in_lean/monads.html)
