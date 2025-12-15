# Lean 4 Type Classes Examples

Working code examples demonstrating type class patterns.

---

## Defining a Type Class

```lean
-- Simple type class
class Printable (α : Type) where
  format : α → String

-- Instances for common types
instance : Printable Nat where
  format n := s!"Nat({n})"

instance : Printable String where
  format s := s!"\"{s}\""

instance : Printable Bool where
  format b := if b then "true" else "false"

-- Generic function using the class
def print [Printable α] (x : α) : IO Unit :=
  IO.println (Printable.format x)

#eval print 42        -- Nat(42)
#eval print "hello"   -- "hello"
#eval print true      -- true
```

---

## Deriving Standard Instances

```lean
structure Person where
  name : String
  age : Nat
  deriving Repr, BEq, Inhabited, Hashable

-- Now these all work:
#eval (Person.mk "Alice" 30)                    -- Repr
#eval Person.mk "Alice" 30 == Person.mk "Alice" 30  -- BEq
#eval (default : Person)                        -- Inhabited
#eval hash (Person.mk "Alice" 30)               -- Hashable

-- Derive Ord for sorting
structure Score where
  value : Nat
  deriving Repr, Ord

def scores : List Score := [⟨85⟩, ⟨92⟩, ⟨78⟩]
#eval scores.mergeSort  -- Sorted by Ord instance
```

---

## Implementing Standard Classes

```lean
structure Point where
  x : Float
  y : Float

-- Manual Repr instance
instance : Repr Point where
  reprPrec p _ := s!"Point({p.x}, {p.y})"

-- Manual BEq instance
instance : BEq Point where
  beq a b := a.x == b.x && a.y == b.y

-- Add instance for points
instance : Add Point where
  add a b := ⟨a.x + b.x, a.y + b.y⟩

-- HMul for scalar multiplication
instance : HMul Float Point Point where
  hMul s p := ⟨s * p.x, s * p.y⟩

-- Now we can use operators
def p1 : Point := ⟨1.0, 2.0⟩
def p2 : Point := ⟨3.0, 4.0⟩

#eval p1 + p2        -- Point(4.0, 6.0)
#eval 2.0 * p1       -- Point(2.0, 4.0)
#eval p1 == p2       -- false
```

---

## Polymorphic Instances

```lean
-- Instance for Option when inner type has instance
instance [Printable α] : Printable (Option α) where
  format
    | none => "none"
    | some x => s!"some({Printable.format x})"

-- Instance for List
instance [Printable α] : Printable (List α) where
  format xs :=
    let inner := xs.map Printable.format |>.intersperse ", "
    s!"[{String.join inner}]"

-- Instance for pairs
instance [Printable α] [Printable β] : Printable (α × β) where
  format (a, b) := s!"({Printable.format a}, {Printable.format b})"

#eval Printable.format (some 42)        -- some(Nat(42))
#eval Printable.format [1, 2, 3]        -- [Nat(1), Nat(2), Nat(3)]
#eval Printable.format (1, "hi")        -- (Nat(1), "hi")
```

---

## Coercion Examples

```lean
-- Basic coercion
structure UserId where
  value : Nat

instance : Coe UserId Nat where
  coe u := u.value

def processId (n : Nat) : String := s!"User #{n}"

def myId : UserId := ⟨42⟩
#eval processId myId  -- Coerces UserId → Nat: "User #42"

-- Function coercion
structure Validator where
  check : String → Bool

instance : CoeFun Validator (fun _ => String → Bool) where
  coe v := v.check

def nonEmpty : Validator := ⟨fun s => !s.isEmpty⟩

#eval nonEmpty "hello"  -- true (used as function)
#eval nonEmpty ""       -- false
```

---

## Class with Multiple Methods

```lean
class Measurable (α : Type) where
  size : α → Nat
  isEmpty : α → Bool := fun x => size x == 0  -- Default impl

instance : Measurable String where
  size s := s.length

instance : Measurable (List α) where
  size xs := xs.length

instance : Measurable (Array α) where
  size arr := arr.size

-- Generic function
def describe [Measurable α] (x : α) : String :=
  if Measurable.isEmpty x then "empty"
  else s!"size: {Measurable.size x}"

#eval describe "hello"  -- size: 5
#eval describe ([] : List Nat)  -- empty
```

---

## Class Hierarchy

```lean
-- Base class
class Eq' (α : Type) where
  eq : α → α → Bool

-- Extended class
class Ord' (α : Type) extends Eq' α where
  lt : α → α → Bool
  le : α → α → Bool := fun a b => lt a b || eq a b

-- Instance provides both
instance : Ord' Nat where
  eq := (· == ·)
  lt := (· < ·)

-- Both methods available
#eval Eq'.eq 1 1   -- true (from base class)
#eval Ord'.lt 1 2  -- true (from extended class)
```

---

## Named and Scoped Instances

```lean
-- Named instance
instance natAddInstance : Add Nat where
  add := Nat.add

-- Use specific instance
#eval @Add.add natAddInstance 1 2

-- Scoped instance (only in scope when namespace open)
namespace StringOps
  scoped instance : Add String where
    add := String.append
end StringOps

-- Only works with open:
open StringOps in
#eval "hello" + " world"  -- "hello world"
```

---

## Multi-Parameter Type Class

```lean
-- Conversion between types
class Convert (α β : Type) where
  convert : α → β

instance : Convert Nat String where
  convert n := toString n

instance : Convert String (List Char) where
  convert s := s.toList

instance : Convert Bool Nat where
  convert b := if b then 1 else 0

def toTarget [Convert α β] (x : α) : β :=
  Convert.convert x

#eval (toTarget 42 : String)       -- "42"
#eval (toTarget "hi" : List Char)  -- ['h', 'i']
#eval (toTarget true : Nat)        -- 1
```

---

## outParam for Type Inference

```lean
-- β is determined by α
class DefaultValue (α : Type) (β : outParam Type) where
  default : β

instance : DefaultValue Nat Nat where
  default := 0

instance : DefaultValue String String where
  default := ""

-- β inferred from α
def getDefault (α : Type) [DefaultValue α β] : β :=
  DefaultValue.default

#eval (getDefault Nat)     -- 0 (β inferred as Nat)
#eval (getDefault String)  -- "" (β inferred as String)
```

---

## Instance with Proofs

```lean
-- Type class with law
class Semigroup' (α : Type) where
  op : α → α → α
  assoc : ∀ a b c : α, op (op a b) c = op a (op b c)

-- Instance with proof
instance : Semigroup' Nat where
  op := Nat.add
  assoc := Nat.add_assoc
```

---

## Sources

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
