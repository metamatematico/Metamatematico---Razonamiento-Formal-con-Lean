# Lean 4 Dependent Types Examples

Working code examples demonstrating dependent type patterns.

---

## Length-Indexed Vectors

```lean
-- Vector with length in type
inductive Vect (α : Type) : Nat → Type where
  | nil  : Vect α 0
  | cons : α → Vect α n → Vect α (n + 1)
  deriving Repr

-- Type-safe head: only works on non-empty vectors
def Vect.head : Vect α (n + 1) → α
  | .cons x _ => x

-- Type-safe tail
def Vect.tail : Vect α (n + 1) → Vect α n
  | .cons _ xs => xs

-- Map preserves length
def Vect.map (f : α → β) : Vect α n → Vect β n
  | .nil => .nil
  | .cons x xs => .cons (f x) (xs.map f)

-- Append: lengths add
def Vect.append : Vect α m → Vect α n → Vect α (m + n)
  | .nil, ys => ys
  | .cons x xs, ys => .cons x (xs.append ys)

-- Examples
def v3 : Vect Nat 3 := .cons 1 (.cons 2 (.cons 3 .nil))

#eval v3.head       -- 1
#eval v3.tail       -- cons 2 (cons 3 nil)
#eval v3.map (· * 2)  -- cons 2 (cons 4 (cons 6 nil))
```

---

## Safe Indexing with Fin

```lean
-- Fin n: natural numbers less than n
#check (0 : Fin 5)  -- Fin 5
#check (4 : Fin 5)  -- Fin 5
-- #check (5 : Fin 5)  -- Error! 5 is not less than 5

-- Safe array indexing
def arr := #[10, 20, 30, 40, 50]

-- Using Fin guarantees in-bounds
def getAt (i : Fin arr.size) : Nat := arr.get i

#eval getAt ⟨2, by decide⟩  -- 30

-- Iterate through all valid indices
def allIndices (n : Nat) : List (Fin n) :=
  match n with
  | 0 => []
  | n + 1 => ⟨0, Nat.zero_lt_succ n⟩ :: (allIndices n).map fun ⟨i, h⟩ =>
      ⟨i + 1, Nat.succ_lt_succ h⟩

#eval allIndices 5  -- [0, 1, 2, 3, 4] as Fin 5 values
```

---

## Vector Indexing with Fin

```lean
-- Safe indexing into vectors
def Vect.get : Vect α n → Fin n → α
  | .cons x _, ⟨0, _⟩ => x
  | .cons _ xs, ⟨i + 1, h⟩ => xs.get ⟨i, Nat.lt_of_succ_lt_succ h⟩

-- No bounds check needed at runtime!
#eval v3.get ⟨1, by decide⟩  -- 2

-- Set at index
def Vect.set : Vect α n → Fin n → α → Vect α n
  | .cons _ xs, ⟨0, _⟩, y => .cons y xs
  | .cons x xs, ⟨i + 1, h⟩, y => .cons x (xs.set ⟨i, Nat.lt_of_succ_lt_succ h⟩ y)
```

---

## Sigma Types (Dependent Pairs)

```lean
-- Pair where second type depends on first value
def SizedArray (α : Type) := (n : Nat) × Array α

-- Note: actual size may differ from n (this is just a demo)
-- For real use, add a proof: (n : Nat) × { arr : Array α // arr.size = n }

-- Creating sigma values
def mkSized (arr : Array α) : (n : Nat) × Array α :=
  ⟨arr.size, arr⟩

#eval mkSized #[1, 2, 3]  -- ⟨3, #[1, 2, 3]⟩

-- Existential: "there exists an n such that..."
def hasEven : (n : Nat) × (n % 2 = 0) := ⟨4, rfl⟩
```

---

## Tarski Universe for Type-Safe Schema

```lean
-- Column type codes
inductive ColType where
  | int
  | text
  | bool
  deriving Repr

-- Interpretation: code → type
def ColType.asType : ColType → Type
  | .int => Int
  | .text => String
  | .bool => Bool

-- Schema as list of column types
def Schema := List ColType

-- Row type depends on schema
def Row : Schema → Type
  | [] => Unit
  | t :: ts => t.asType × Row ts

-- Type-safe row creation
def schema1 : Schema := [.int, .text, .bool]

def row1 : Row schema1 := (42, ("Alice", (true, ())))

-- Generic row operations
def Row.get : (schema : Schema) → Row schema → (i : Fin schema.length) → schema[i].asType
  | _ :: _, (v, _), ⟨0, _⟩ => v
  | _ :: ts, (_, rest), ⟨i + 1, h⟩ => Row.get ts rest ⟨i, Nat.lt_of_succ_lt_succ h⟩

#eval Row.get schema1 row1 ⟨1, by decide⟩  -- "Alice"
```

---

## Subtype for Refinement

```lean
-- Positive natural numbers
def Pos := { n : Nat // n > 0 }

-- Creating positive numbers
def one : Pos := ⟨1, by decide⟩
def five : Pos := ⟨5, by decide⟩

-- Operations preserving positivity
def Pos.add (a b : Pos) : Pos :=
  ⟨a.val + b.val, Nat.add_pos_left a.property b.val⟩

def Pos.mul (a b : Pos) : Pos :=
  ⟨a.val * b.val, Nat.mul_pos a.property b.property⟩

-- Safe predecessor (Pos → Nat)
def Pos.pred (n : Pos) : Nat := n.val - 1

-- Non-empty list
def NonEmpty (α : Type) := { xs : List α // xs ≠ [] }

def NonEmpty.head : NonEmpty α → α
  | ⟨x :: _, _⟩ => x

def nel : NonEmpty Nat := ⟨[1, 2, 3], by decide⟩
#eval nel.head  -- 1
```

---

## Type-Safe State Machine

```lean
-- States as types
inductive DoorState where | open | closed | locked

-- Door indexed by state
structure Door (state : DoorState) where
  name : String

-- Operations that change state
def Door.close : Door .open → Door .closed
  | ⟨n⟩ => ⟨n⟩

def Door.open_ : Door .closed → Door .open
  | ⟨n⟩ => ⟨n⟩

def Door.lock : Door .closed → Door .locked
  | ⟨n⟩ => ⟨n⟩

def Door.unlock : Door .locked → Door .closed
  | ⟨n⟩ => ⟨n⟩

-- Can only call appropriate operations for state
def example1 : Door .locked :=
  let d : Door .open := ⟨"front"⟩
  let d := d.close
  let d := d.lock
  d

-- This won't compile: can't open a locked door
-- def bad : Door .open := (⟨"x"⟩ : Door .locked).open_
```

---

## Heterogeneous Lists

```lean
-- Type codes
inductive HCode where | nat | string | bool

def HCode.asType : HCode → Type
  | .nat => Nat
  | .string => String
  | .bool => Bool

-- Heterogeneous list indexed by type schema
inductive HList : List HCode → Type where
  | nil  : HList []
  | cons : t.asType → HList ts → HList (t :: ts)

-- Examples
def hlist1 : HList [.nat, .string, .bool] :=
  .cons 42 (.cons "hello" (.cons true .nil))

-- Type-safe access
def HList.head : HList (t :: ts) → t.asType
  | .cons x _ => x

#eval hlist1.head  -- 42 : Nat
```

---

## Proofs in Types

```lean
-- Sorted list (simplified)
inductive Sorted : List Nat → Prop where
  | nil : Sorted []
  | single : Sorted [x]
  | cons : x ≤ y → Sorted (y :: ys) → Sorted (x :: y :: ys)

-- Sorted list type
def SortedList := { xs : List Nat // Sorted xs }

-- Proof that [1, 2, 3] is sorted
def sorted123 : SortedList :=
  ⟨[1, 2, 3], Sorted.cons (by decide) (Sorted.cons (by decide) Sorted.single)⟩
```

---

## Universe Polymorphism

```lean
-- Works at any universe level
def id'.{u} {α : Type u} (x : α) : α := x

-- Using at different levels
#check id' 42       -- Nat (Type 0)
#check id' Nat      -- Type (Type 1)
#check id' Type     -- Type 1 (Type 2)

-- Polymorphic container
def Box.{u} (α : Type u) := α

#check Box.{0} Nat    -- Type
#check Box.{1} Type   -- Type 1
```

---

## Sources

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
