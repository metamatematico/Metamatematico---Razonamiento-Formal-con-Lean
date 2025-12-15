# Lean 4 Functor and Applicative Examples

Working code examples demonstrating functional abstraction patterns.

---

## Functor Examples

```lean
-- Basic mapping
#eval (· + 1) <$> some 5           -- some 6
#eval (· + 1) <$> none             -- none
#eval (· + 1) <$> [1, 2, 3, 4, 5]  -- [2, 3, 4, 5, 6]

-- Composition of maps
#eval (toString ∘ (· * 2)) <$> some 21  -- some "42"
#eval toString <$> ((· * 2) <$> some 21)  -- same result

-- Mapping over nested structures
def data : Option (List Nat) := some [1, 2, 3]
#eval (·.map (· + 10)) <$> data  -- some [11, 12, 13]

-- Replacing all values
def void : Functor f → f α → f Unit := fun _ x => () <$ x
#eval () <$ some 42        -- some ()
#eval "x" <$ [1, 2, 3]     -- ["x", "x", "x"]
```

---

## Applicative Examples

```lean
-- Combining Option values
#eval pure (· + ·) <*> some 3 <*> some 4      -- some 7
#eval pure (· + ·) <*> some 3 <*> none        -- none
#eval pure (· + ·) <*> none <*> some 4        -- none

-- Multi-argument functions
def fullName (first last : String) := s!"{first} {last}"
#eval pure fullName <*> some "John" <*> some "Doe"  -- some "John Doe"

-- Alternative syntax with <$>
#eval fullName <$> some "John" <*> some "Doe"  -- some "John Doe"

-- Three arguments
def volume (l w h : Float) := l * w * h
#eval volume <$> some 2.0 <*> some 3.0 <*> some 4.0  -- some 24.0
```

---

## List Applicative (Cartesian Product)

```lean
-- Lists produce all combinations
#eval [(· + 1), (· * 2)] <*> [10, 20, 30]
-- [11, 21, 31, 20, 40, 60]

-- Generate pairs
#eval (·, ·) <$> [1, 2] <*> ["a", "b"]
-- [(1, "a"), (1, "b"), (2, "a"), (2, "b")]

-- Comprehension-like syntax
def pairs : List (Nat × Nat) := do
  let x ← [1, 2, 3]
  let y ← [10, 20]
  pure (x, y)
-- [(1, 10), (1, 20), (2, 10), (2, 20), (3, 10), (3, 20)]

-- Filter with guard
def pythagoreanTriples (n : Nat) : List (Nat × Nat × Nat) := do
  let a ← List.range n
  let b ← List.range n
  let c ← List.range n
  guard (a * a + b * b == c * c)
  guard (a < b)
  pure (a, b, c)

#eval pythagoreanTriples 15  -- [(3, 4, 5), (5, 12, 13), (6, 8, 10)]
```

---

## Alternative Examples

```lean
-- orElse: try alternatives
#eval none <|> some 5        -- some 5
#eval some 3 <|> some 5      -- some 3
#eval none <|> none <|> some 7  -- some 7

-- First successful lookup
def findFirst (keys : List String) (db : List (String × Nat)) : Option Nat :=
  keys.foldl (fun acc k => acc <|> db.lookup k) none

#eval findFirst ["c", "b", "a"] [("a", 1), ("b", 2)]  -- some 2

-- guard for conditional failure
def evenOnly (n : Nat) : Option Nat :=
  if n % 2 == 0 then some n else none

#eval do
  let n ← some 4
  guard (n % 2 == 0)
  pure (n * 2)  -- some 8

#eval do
  let n ← some 3
  guard (n % 2 == 0)
  pure (n * 2)  -- none
```

---

## Validate Pattern Examples

```lean
-- Error type
inductive FormError where
  | emptyName : FormError
  | invalidAge : String → FormError
  | invalidEmail : String → FormError
  deriving Repr

-- NonEmptyList helper
structure NonEmptyList (α : Type) where
  head : α
  tail : List α
  deriving Repr

def NonEmptyList.singleton (x : α) : NonEmptyList α := ⟨x, []⟩
def NonEmptyList.append (xs ys : NonEmptyList α) : NonEmptyList α :=
  ⟨xs.head, xs.tail ++ [ys.head] ++ ys.tail⟩

instance : Append (NonEmptyList α) where
  append := NonEmptyList.append

-- Validate type
inductive Validate (ε α : Type) where
  | ok : α → Validate ε α
  | errors : NonEmptyList ε → Validate ε α
  deriving Repr

def Validate.error (e : ε) : Validate ε α :=
  .errors (NonEmptyList.singleton e)

instance : Functor (Validate ε) where
  map f
    | .ok x => .ok (f x)
    | .errors es => .errors es

instance : Applicative (Validate ε) where
  pure := .ok
  seq f x :=
    match f, x () with
    | .ok g, .ok y => .ok (g y)
    | .ok _, .errors es => .errors es
    | .errors es, .ok _ => .errors es
    | .errors es1, .errors es2 => .errors (es1 ++ es2)

-- Validation functions
def validateName (name : String) : Validate FormError String :=
  if name.isEmpty then Validate.error .emptyName
  else .ok name

def validateAge (age : String) : Validate FormError Nat :=
  match age.toNat? with
  | some n => if n < 150 then .ok n else Validate.error (.invalidAge age)
  | none => Validate.error (.invalidAge age)

def validateEmail (email : String) : Validate FormError String :=
  if email.containsSubstr "@" then .ok email
  else Validate.error (.invalidEmail email)

-- User validation - accumulates ALL errors
structure User where
  name : String
  age : Nat
  email : String
  deriving Repr

def validateUser (name age email : String) : Validate FormError User :=
  User.mk <$> validateName name <*> validateAge age <*> validateEmail email

#eval validateUser "John" "30" "john@example.com"
-- ok (User "John" 30 "john@example.com")

#eval validateUser "" "abc" "invalid"
-- errors [emptyName, invalidAge "abc", invalidEmail "invalid"]
```

---

## sequenceA and traverse

```lean
-- sequenceA: List (Option α) → Option (List α)
def sequenceA [Applicative f] : List (f α) → f (List α)
  | [] => pure []
  | x :: xs => List.cons <$> x <*> sequenceA xs

#eval sequenceA [some 1, some 2, some 3]  -- some [1, 2, 3]
#eval sequenceA [some 1, none, some 3]    -- none (short-circuits)

-- traverse: apply function and collect results
def traverse [Applicative f] (fn : α → f β) : List α → f (List β)
  | [] => pure []
  | x :: xs => List.cons <$> fn x <*> traverse fn xs

def safeDivide (x : Nat) : Option Nat :=
  if x == 0 then none else some (100 / x)

#eval traverse safeDivide [2, 4, 5]   -- some [50, 25, 20]
#eval traverse safeDivide [2, 0, 5]   -- none
```

---

## seqLeft and seqRight

```lean
-- <* : run both, keep left
#eval some 3 <* some 5     -- some 3 (ran both, kept 3)
#eval some 3 <* none       -- none (second failed)

-- *> : run both, keep right
#eval some 3 *> some 5     -- some 5 (ran both, kept 5)
#eval none *> some 5       -- none (first failed)

-- Useful for sequencing effects
def logAndReturn (msg : String) (x : Nat) : IO Nat := do
  IO.println msg
  pure x

-- Run logging, return value
def example : IO Nat :=
  IO.println "Starting" *> pure 42 <* IO.println "Done"
```

---

## Lifting Functions

```lean
-- lift2: lift binary function into Applicative
def lift2 [Applicative f] (fn : α → β → γ) (a : f α) (b : f β) : f γ :=
  fn <$> a <*> b

#eval lift2 (· + ·) (some 3) (some 4)     -- some 7
#eval lift2 String.append (some "Hi") (some " there")  -- some "Hi there"

-- lift3
def lift3 [Applicative f] (fn : α → β → γ → δ)
    (a : f α) (b : f β) (c : f γ) : f δ :=
  fn <$> a <*> b <*> c

#eval lift3 (fun a b c => a + b + c) (some 1) (some 2) (some 3)  -- some 6
```

---

## Sources

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
