---
name: lean-fp-basics
description: Lean 4 fundamentals including syntax, structures, inductive types, and polymorphism. Use when writing basic Lean code, defining custom data types, pattern matching, or learning core language patterns.
allowed-tools: Read, Grep, Glob
---

# Lean 4 Functional Programming Basics

Lean 4 fundamentals: syntax, structures, inductive types, and polymorphism. Use when writing basic Lean code, defining custom data types, or learning core language patterns.

**Trigger terms**: "lean syntax", "define type", "structure", "inductive", "pattern matching", "polymorphism", "Lean basics"

---

## Function Definition

```lean
def add1 (n : Nat) : Nat := n + 1

def maximum (n k : Nat) : Nat :=
  if n < k then k else n
```

**Commands**: `#check` (show type), `#eval` (evaluate), `#print` (show definition)

---

## Structures (Product Types)

```lean
structure Point where
  x : Float
  y : Float
  deriving Repr

def origin : Point := { x := 0.0, y := 0.0 }

-- Update syntax (functional update)
def zeroX (p : Point) : Point := { p with x := 0 }
```

**When to use**: Fixed collection of named fields, all fields always present, want `.field` accessor syntax.

---

## Inductive Types (Sum Types)

```lean
inductive Sign where
  | pos | neg | zero

inductive Nat where
  | zero : Nat
  | succ (n : Nat) : Nat
```

**Pattern Matching**:
```lean
def isZero : Nat → Bool
  | .zero => true
  | .succ _ => false
```

**When to use**: Multiple constructors, different shapes, recursive data, need pattern matching.

---

## Decision: Structure vs Inductive

```
Does your type need:
├─ Multiple constructors? → inductive
├─ Recursive definition? → inductive
├─ Different shapes per variant? → inductive
└─ Fixed fields always present? → structure
```

---

## Polymorphism

```lean
-- Explicit type parameter
def replaceX (α : Type) (p : PPoint α) (x : α) : PPoint α := { p with x }

-- Implicit (preferred) - compiler infers
def length {α : Type} (xs : List α) : Nat :=
  match xs with
  | [] => 0
  | _ :: ys => 1 + length ys

-- Provide implicit explicitly when needed
#check ([] : List Int)
#check List.length (α := Int)
```

**Use implicit `{α}`**: When type is inferrable from arguments.
**Use explicit `(α)`**: When type only in return, or empty containers.

---

## Common Mistakes

**Forgetting pattern exhaustiveness**:
```lean
-- ❌ Missing case
def f : Option Nat → Nat
  | some n => n

-- ✓ Handle all cases
def f : Option Nat → Nat
  | some n => n
  | none => 0
```

**Structures aren't mutable**:
```lean
-- ❌ Won't compile
p.x := 5

-- ✓ Create new with update
{ p with x := 5 }
```

---

## See Also

- `lean-fp-type-classes` - Overloading with type classes
- `lean-fp-monads` - Effect handling
- `lean-tp-foundations` - Type theory background

**Source**: [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
