# Lean 4 Basics Examples

Working code examples demonstrating fundamental patterns.

---

## Basic Definitions

```lean
-- Simple function
def double (n : Nat) : Nat := n * 2

-- Multiple parameters
def add (a b : Nat) : Nat := a + b

-- With default argument
def greet (name : String := "World") : String := s!"Hello, {name}!"

#eval double 5         -- 10
#eval add 3 4          -- 7
#eval greet            -- "Hello, World!"
#eval greet "Lean"     -- "Hello, Lean!"
```

---

## Structure Examples

```lean
-- Basic structure
structure Point where
  x : Float
  y : Float
  deriving Repr

-- Create instances
def origin : Point := { x := 0.0, y := 0.0 }
def p1 : Point := ⟨1.0, 2.0⟩  -- Anonymous constructor

-- Access fields
#eval origin.x  -- 0.0
#eval p1.y      -- 2.0

-- Functional update
def moveRight (p : Point) (d : Float) : Point :=
  { p with x := p.x + d }

#eval moveRight origin 5.0  -- { x := 5.0, y := 0.0 }
```

---

## Structure with Defaults

```lean
structure ServerConfig where
  host : String := "localhost"
  port : Nat := 8080
  maxConnections : Nat := 100
  deriving Repr

-- Use all defaults
def defaultConfig : ServerConfig := {}

-- Override some
def devConfig : ServerConfig := { port := 3000 }

-- Override all
def prodConfig : ServerConfig := {
  host := "0.0.0.0",
  port := 443,
  maxConnections := 10000
}
```

---

## Inductive Types

```lean
-- Simple enumeration
inductive Color where
  | red | green | blue
  deriving Repr

-- With data
inductive Shape where
  | circle : Float → Shape
  | rectangle : Float → Float → Shape
  | triangle : Float → Float → Float → Shape
  deriving Repr

-- Pattern match
def area : Shape → Float
  | .circle r => 3.14159 * r * r
  | .rectangle w h => w * h
  | .triangle a b c =>
    let s := (a + b + c) / 2
    Float.sqrt (s * (s - a) * (s - b) * (s - c))

#eval area (.circle 2.0)           -- ~12.57
#eval area (.rectangle 3.0 4.0)    -- 12.0
```

---

## Recursive Types

```lean
-- Linked list
inductive MyList (α : Type) where
  | nil : MyList α
  | cons : α → MyList α → MyList α
  deriving Repr

-- Recursive functions
def myLength {α : Type} : MyList α → Nat
  | .nil => 0
  | .cons _ xs => 1 + myLength xs

def myMap {α β : Type} (f : α → β) : MyList α → MyList β
  | .nil => .nil
  | .cons x xs => .cons (f x) (myMap f xs)

-- Example usage
def nums : MyList Nat := .cons 1 (.cons 2 (.cons 3 .nil))
#eval myLength nums           -- 3
#eval myMap (· + 10) nums     -- cons 11 (cons 12 (cons 13 nil))
```

---

## Polymorphic Functions

```lean
-- Implicit type parameter
def first {α : Type} (xs : List α) : Option α :=
  match xs with
  | [] => none
  | x :: _ => some x

#eval first [1, 2, 3]         -- some 1
#eval first ([] : List Nat)   -- none

-- Explicit when needed
def empty (α : Type) : List α := []

#eval empty Nat    -- []
#eval empty String -- []

-- Force implicit to explicit
#check @first Nat [1, 2]
#check first (α := String) ["a", "b"]
```

---

## Pattern Matching Patterns

```lean
-- Multiple patterns per case
def isWeekend : String → Bool
  | "Saturday" | "Sunday" => true
  | _ => false

-- Nested patterns
def sumPairs : List (Nat × Nat) → Nat
  | [] => 0
  | (a, b) :: rest => a + b + sumPairs rest

-- With guards
def classify (n : Nat) : String :=
  match n with
  | 0 => "zero"
  | 1 => "one"
  | n => if n < 10 then "small" else "large"

-- As-patterns
def describeList {α : Type} [Repr α] : List α → String
  | [] => "empty"
  | [x] => s!"singleton: {repr x}"
  | xs@(_ :: _ :: _) => s!"multiple elements: {repr xs}"
```

---

## Nested Structures

```lean
structure Address where
  street : String
  city : String
  zip : String
  deriving Repr

structure Person where
  name : String
  age : Nat
  address : Address
  deriving Repr

def alice : Person := {
  name := "Alice",
  age := 30,
  address := {
    street := "123 Main St",
    city := "Springfield",
    zip := "12345"
  }
}

-- Deep access
#eval alice.address.city  -- "Springfield"

-- Deep update (manual)
def updateCity (p : Person) (newCity : String) : Person :=
  { p with address := { p.address with city := newCity } }
```

---

## Option Type

```lean
-- Safe division
def safeDiv (a b : Nat) : Option Nat :=
  if b == 0 then none else some (a / b)

-- Chaining with match
def divTwice (a b c : Nat) : Option Nat :=
  match safeDiv a b with
  | none => none
  | some r => safeDiv r c

-- Using getD (get with default)
#eval (safeDiv 10 2).getD 0  -- 5
#eval (safeDiv 10 0).getD 0  -- 0
```

---

## Local Definitions

```lean
-- let ... in
def circleArea (r : Float) : Float :=
  let pi := 3.14159
  let rSquared := r * r
  pi * rSquared

-- where clause
def quadratic (a b c x : Float) : Float := result
  where
    result := a * x * x + b * x + c

-- Local recursive function
def factorial (n : Nat) : Nat :=
  let rec go acc n :=
    match n with
    | 0 => acc
    | n + 1 => go (acc * (n + 1)) n
  go 1 n
```

---

## Sources

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
