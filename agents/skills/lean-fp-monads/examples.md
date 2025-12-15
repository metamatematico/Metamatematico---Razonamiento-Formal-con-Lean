# Lean 4 Monads Examples

Working code examples demonstrating monadic patterns.

---

## Option Monad Examples

```lean
-- Safe list operations
def safeHead {α : Type} : List α → Option α
  | [] => none
  | x :: _ => some x

def safeTail {α : Type} : List α → Option (List α)
  | [] => none
  | _ :: xs => some xs

-- Chaining with do-notation
def secondElement {α : Type} (xs : List α) : Option α := do
  let tail ← safeTail xs
  safeHead tail

#eval secondElement [1, 2, 3]  -- some 2
#eval secondElement [1]        -- none
#eval secondElement ([] : List Nat)  -- none

-- Alternative using bind directly
def secondElement' {α : Type} (xs : List α) : Option α :=
  safeTail xs >>= safeHead
```

---

## Except Monad Examples

```lean
-- Error type
inductive CalcError where
  | divisionByZero : CalcError
  | negativeInput : CalcError
  deriving Repr

-- Safe operations
def safeDiv (a b : Int) : Except CalcError Int :=
  if b == 0 then throw .divisionByZero
  else pure (a / b)

def safeSqrt (n : Int) : Except CalcError Int :=
  if n < 0 then throw .negativeInput
  else pure (Int.sqrt n.toNat)

-- Chaining
def compute (a b : Int) : Except CalcError Int := do
  let quotient ← safeDiv a b
  safeSqrt quotient

#eval compute 100 10    -- Except.ok 3
#eval compute 100 0     -- Except.error divisionByZero
#eval compute (-100) 10 -- Except.error negativeInput

-- Error handling
def computeSafe (a b : Int) : Int :=
  match compute a b with
  | .ok n => n
  | .error _ => 0
```

---

## State Monad Examples

```lean
-- Counter state
def tick : StateM Nat Unit := modify (· + 1)

def getThenIncrement : StateM Nat Nat := do
  let n ← get
  tick
  pure n

-- Running state
#eval (getThenIncrement.run 5)  -- (6, 5)

-- Multiple operations
def countdown : StateM Nat (List Nat) := do
  let mut result := []
  while (← get) > 0 do
    result := (← get) :: result
    modify (· - 1)
  pure result.reverse

#eval (countdown.run 5)  -- (0, [5, 4, 3, 2, 1])
```

---

## State Monad: Stack Example

```lean
abbrev Stack α := List α
abbrev StackM α β := StateM (Stack α) β

def push {α : Type} (x : α) : StackM α Unit :=
  modify (x :: ·)

def pop {α : Type} : StackM α (Option α) := do
  match ← get with
  | [] => pure none
  | x :: xs =>
    set xs
    pure (some x)

def peek {α : Type} : StackM α (Option α) := do
  match ← get with
  | [] => pure none
  | x :: _ => pure (some x)

-- Example usage
def stackOps : StackM Nat Nat := do
  push 1
  push 2
  push 3
  let _ ← pop     -- Removes 3
  let top ← peek  -- Sees 2
  pure top.getD 0

#eval (stackOps.run [])  -- ([], 2)
```

---

## Reader Monad Examples

```lean
-- Configuration
structure AppConfig where
  debug : Bool
  maxRetries : Nat
  baseUrl : String

abbrev AppM := ReaderT AppConfig Id

def getBaseUrl : AppM String := do
  let cfg ← read
  pure cfg.baseUrl

def logIfDebug (msg : String) : AppM Unit := do
  let cfg ← read
  if cfg.debug then
    dbg_trace msg

-- Local modification
def withDebug (action : AppM α) : AppM α :=
  ReaderT.adapt (fun cfg => { cfg with debug := true }) action

-- Running
def config : AppConfig := { debug := false, maxRetries := 3, baseUrl := "https://api.example.com" }
#eval (getBaseUrl.run config)  -- "https://api.example.com"
```

---

## Combining Monads with do-notation

```lean
-- Multiple operations
def processNumbers (nums : List Nat) : Option Nat := do
  let first ← nums[0]?
  let second ← nums[1]?
  guard (second != 0)  -- Fails if false
  pure (first / second)

#eval processNumbers [10, 2]   -- some 5
#eval processNumbers [10, 0]   -- none (guard failed)
#eval processNumbers [10]      -- none (no second element)
```

---

## mapM and forM

```lean
-- mapM: transform each element with monadic action
def lookupAll (keys : List String) (db : List (String × Nat)) : Option (List Nat) :=
  keys.mapM (fun k => db.lookup k)

#eval lookupAll ["a", "b"] [("a", 1), ("b", 2), ("c", 3)]  -- some [1, 2]
#eval lookupAll ["a", "d"] [("a", 1), ("b", 2), ("c", 3)]  -- none

-- forM: execute for side effects
def printAll (msgs : List String) : IO Unit :=
  msgs.forM IO.println
```

---

## Early Return Pattern

```lean
-- Using early return in do-blocks
def findFirst (p : α → Bool) (xs : List α) : Option α := do
  for x in xs do
    if p x then return some x
  none

-- More complex example with validation
def validateUser (name : String) (age : Nat) : Except String Unit := do
  if name.isEmpty then throw "Name cannot be empty"
  if age < 18 then throw "Must be 18 or older"
  if age > 150 then throw "Invalid age"
  pure ()
```

---

## Monad Comprehension Style

```lean
-- List-like syntax works for any monad with Alternative
def combinations : List (Nat × Nat) := do
  let x ← [1, 2, 3]
  let y ← [10, 20]
  pure (x, y)

#eval combinations  -- [(1, 10), (1, 20), (2, 10), (2, 20), (3, 10), (3, 20)]

-- With guard
def pairs : List (Nat × Nat) := do
  let x ← [1, 2, 3, 4, 5]
  let y ← [1, 2, 3, 4, 5]
  guard (x < y)
  pure (x, y)

#eval pairs  -- [(1,2), (1,3), (1,4), (1,5), (2,3), (2,4), (2,5), ...]
```

---

## IO Monad Examples

```lean
-- Basic IO
def greet : IO Unit := do
  IO.println "What's your name?"
  let name ← IO.getLine
  IO.println s!"Hello, {name.trim}!"

-- File operations
def copyFile (src dst : String) : IO Unit := do
  let contents ← IO.FS.readFile src
  IO.FS.writeFile dst contents

-- Error handling
def safeRead (path : String) : IO (Option String) := do
  try
    let contents ← IO.FS.readFile path
    pure (some contents)
  catch _ =>
    pure none
```

---

## Sources

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
