# Lean 4 Monad Transformers Examples

Working code examples demonstrating transformer patterns.

---

## Basic OptionT

```lean
-- OptionT adds failure to any monad
def safeHead [Monad m] (xs : List α) : OptionT m α :=
  match xs with
  | [] => failure
  | x :: _ => pure x

-- OptionT over IO
def readFirstLine : OptionT IO String := do
  let contents ← liftIO (IO.FS.readFile "test.txt")
  safeHead (contents.splitOn "\n")

-- Running
def main : IO Unit := do
  match ← readFirstLine.run with
  | none => IO.println "No first line"
  | some line => IO.println s!"First line: {line}"
```

---

## Basic ExceptT

```lean
-- Custom error type
inductive AppError where
  | notFound : String → AppError
  | invalidInput : String → AppError
  deriving Repr

-- ExceptT over IO
def readConfig : ExceptT AppError IO String := do
  try
    liftIO (IO.FS.readFile "config.json")
  catch _ =>
    throw (.notFound "config.json")

def parsePort (config : String) : ExceptT AppError IO Nat := do
  match config.toNat? with
  | some n => pure n
  | none => throw (.invalidInput "port must be a number")

-- Chaining
def getPort : ExceptT AppError IO Nat := do
  let config ← readConfig
  parsePort config

-- Running with error handling
def main : IO Unit := do
  match ← getPort.run with
  | Except.ok port => IO.println s!"Port: {port}"
  | Except.error e => IO.println s!"Error: {repr e}"
```

---

## Basic StateT

```lean
-- Counter with StateT
def tick : StateT Nat IO Unit := do
  let n ← get
  liftIO (IO.println s!"Current count: {n}")
  set (n + 1)

def runCounter : IO Unit := do
  let ((), finalState) ← (do tick; tick; tick).run 0
  IO.println s!"Final count: {finalState}"

#eval runCounter
-- Current count: 0
-- Current count: 1
-- Current count: 2
-- Final count: 3
```

---

## Basic ReaderT

```lean
-- Configuration
structure Config where
  apiUrl : String
  timeout : Nat
  debug : Bool

-- ReaderT for config access
def apiCall (endpoint : String) : ReaderT Config IO String := do
  let cfg ← read
  if cfg.debug then
    liftIO (IO.println s!"Calling {cfg.apiUrl}/{endpoint}")
  pure s!"Response from {endpoint}"

-- Temporarily modify config
def withTimeout (t : Nat) (action : ReaderT Config IO α) : ReaderT Config IO α :=
  ReaderT.adapt (fun cfg => { cfg with timeout := t }) action

-- Running
def runWithConfig : IO Unit := do
  let config : Config := { apiUrl := "https://api.example.com", timeout := 30, debug := true }
  let result ← apiCall "users".run config
  IO.println result
```

---

## Stacking: StateT + ExceptT

```lean
-- State preserved on error
abbrev StatefulExcept := StateT Nat (Except String)

def incrementAndMayFail (shouldFail : Bool) : StatefulExcept Unit := do
  modify (· + 1)
  if shouldFail then throw "Failed!"
  modify (· + 1)

-- Running
#eval (incrementAndMayFail false).run 0  -- Except.ok ((), 2)
#eval (incrementAndMayFail true).run 0   -- Except.error "Failed!"
-- Note: state is LOST on error with this stacking

-- Alternative: ExceptT (StateT ...)
abbrev StatefulExcept' := ExceptT String (StateT Nat Id)

def incrementAndMayFail' (shouldFail : Bool) : StatefulExcept' Unit := do
  StateT.modify (· + 1)
  if shouldFail then ExceptT.throw "Failed!"
  StateT.modify (· + 1)

-- Running
#eval (incrementAndMayFail' false).run.run 0  -- (Except.ok (), 2)
#eval (incrementAndMayFail' true).run.run 0   -- (Except.error "Failed!", 1)
-- Note: state IS preserved even on error!
```

---

## Complete App Stack

```lean
-- A realistic application stack
structure AppConfig where
  serviceName : String
  logLevel : Nat

structure AppState where
  requestCount : Nat
  errors : List String

inductive AppError where
  | configError : String → AppError
  | runtimeError : String → AppError

-- Stack: ReaderT Config (StateT State (ExceptT Error IO))
abbrev AppM := ReaderT AppConfig (StateT AppState (ExceptT AppError IO))

-- Helpers
def getConfig : AppM AppConfig := read
def getState : AppM AppState := StateT.get
def modifyState (f : AppState → AppState) : AppM Unit := StateT.modify f
def logError (msg : String) : AppM Unit :=
  modifyState fun s => { s with errors := msg :: s.errors }
def fail (e : AppError) : AppM α := ExceptT.throw e
def liftIO' (x : IO α) : AppM α := liftIO x

-- Business logic
def processRequest (req : String) : AppM String := do
  let cfg ← getConfig
  modifyState fun s => { s with requestCount := s.requestCount + 1 }

  if cfg.logLevel > 0 then
    liftIO' (IO.println s!"[{cfg.serviceName}] Processing: {req}")

  if req.isEmpty then
    logError "Empty request"
    fail (.runtimeError "Request cannot be empty")

  pure s!"Processed: {req}"

-- Running the full stack
def runApp (action : AppM α) (config : AppConfig) (state : AppState) : IO (Except AppError (α × AppState)) :=
  (action.run config).run state

def example : IO Unit := do
  let config : AppConfig := { serviceName := "MyApp", logLevel := 1 }
  let state : AppState := { requestCount := 0, errors := [] }

  match ← runApp (processRequest "hello") config state with
  | Except.ok (result, finalState) =>
    IO.println s!"Result: {result}"
    IO.println s!"Request count: {finalState.requestCount}"
  | Except.error e =>
    IO.println s!"Error: {repr e}"
```

---

## Parser Example

```lean
-- Parser state
structure ParseState where
  input : String
  pos : Nat
  deriving Repr

-- Parser monad
abbrev Parser := StateT ParseState (Except String)

-- Basic combinators
def peek : Parser (Option Char) := do
  let s ← get
  if h : s.pos < s.input.length then
    pure (some (s.input.get ⟨s.pos, h⟩))
  else
    pure none

def advance : Parser Unit := modify fun s => { s with pos := s.pos + 1 }

def expect (c : Char) : Parser Char := do
  match ← peek with
  | none => throw s!"Unexpected EOF, expected '{c}'"
  | some actual =>
    if actual == c then
      advance
      pure c
    else
      throw s!"Expected '{c}', got '{actual}'"

def digit : Parser Nat := do
  match ← peek with
  | none => throw "Unexpected EOF, expected digit"
  | some c =>
    if c.isDigit then
      advance
      pure (c.toNat - '0'.toNat)
    else
      throw s!"Expected digit, got '{c}'"

def number : Parser Nat := do
  let mut result := 0
  while (← peek).any Char.isDigit do
    let d ← digit
    result := result * 10 + d
  pure result

-- Running parser
def runParser (p : Parser α) (input : String) : Except String α :=
  Prod.fst <$> p.run { input, pos := 0 }

#eval runParser number "123abc"  -- Except.ok 123
#eval runParser (expect 'x') "abc"  -- Except.error "Expected 'x', got 'a'"
```

---

## Lifting Operations

```lean
-- Explicit lifting through layers
abbrev Stack := ReaderT String (StateT Nat (ExceptT String IO))

def stackExample : Stack Unit := do
  -- Lift IO operation
  let _ ← liftIO (IO.println "IO action")

  -- Access reader
  let name ← read

  -- Modify state
  StateT.modify (· + 1)

  -- Throw error
  if name.isEmpty then
    ExceptT.throw "Empty name"

  pure ()
```

---

## Sources

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
