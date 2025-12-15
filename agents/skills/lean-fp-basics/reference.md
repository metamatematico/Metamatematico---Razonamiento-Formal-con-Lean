# Lean 4 Basics Deep Dive

Extended reference for Lean 4 fundamentals, syntax patterns, and type system basics.

---

## Expression Evaluation

Lean expressions reduce to values via computation rules:

| Rule | Example | Result |
|------|---------|--------|
| Function application | `(fun x => x + 1) 5` | `6` |
| Arithmetic | `2 + 3 * 4` | `14` |
| String interpolation | `s!"Hello, {name}"` | `"Hello, World"` |
| Conditional | `if true then 1 else 2` | `1` |

**Evaluation order**: Lean is strict (eager) by default, not lazy.

---

## Type Inference

Lean infers types bidirectionally:

```lean
-- Forward: from arguments to result
def f x := x + 1  -- x : Nat inferred from +

-- Backward: from expected type
let xs : List Nat := []  -- [] given type from annotation
```

### When Inference Fails

```lean
-- ❌ Ambiguous - which numeric type?
def x := 5

-- ✓ Explicit annotation
def x : Nat := 5
def x : Int := 5
```

---

## Structure Mechanics

### Field Accessors

Each field generates an accessor function:

```lean
structure Point where
  x : Float
  y : Float

-- Auto-generated:
-- Point.x : Point → Float
-- Point.y : Point → Float
```

### Anonymous Constructor

```lean
def p : Point := ⟨1.0, 2.0⟩  -- Same as { x := 1.0, y := 2.0 }
```

### Nested Structures

```lean
structure Rect where
  topLeft : Point
  bottomRight : Point

def r : Rect := {
  topLeft := { x := 0, y := 10 },
  bottomRight := { x := 10, y := 0 }
}

-- Deep access
#eval r.topLeft.x  -- 0.0
```

### Default Values

```lean
structure Config where
  port : Nat := 8080
  host : String := "localhost"

def c : Config := {}  -- Uses defaults
def c2 : Config := { port := 3000 }  -- Override one
```

---

## Inductive Type Internals

### Recursors

Every inductive type generates a recursor for elimination:

```lean
-- For Nat, generates Nat.rec:
-- Nat.rec : {motive : Nat → Sort u} →
--           motive zero →
--           ((n : Nat) → motive n → motive (succ n)) →
--           (t : Nat) → motive t
```

### Structural Recursion

Functions must be structurally decreasing:

```lean
-- ✓ Structurally decreasing on n
def fact : Nat → Nat
  | 0 => 1
  | n + 1 => (n + 1) * fact n

-- ❌ Not structurally decreasing
def bad (n : Nat) : Nat := bad (n + 1)
```

---

## Pattern Matching Details

### Match Syntax Variants

```lean
-- Function definition patterns
def f : Nat → Bool
  | 0 => true
  | _ => false

-- Match expression
def g (n : Nat) : Bool :=
  match n with
  | 0 => true
  | _ => false

-- Lambda with pattern
let f := fun | 0 => true | _ => false
```

### Deep Patterns

```lean
def firstOfPair : List (Nat × Nat) → Option Nat
  | [] => none
  | (a, _) :: _ => some a  -- Nested pattern
```

### As-Patterns

```lean
def process : List Nat → String
  | [] => "empty"
  | xs@(x :: _) => s!"First: {x}, all: {xs}"
```

### Guards (if in pattern)

```lean
def classify (n : Nat) : String :=
  match n with
  | 0 => "zero"
  | n => if n < 10 then "small" else "large"
```

---

## Type Parameters

### Explicit vs Implicit

| Syntax | Meaning | When to Use |
|--------|---------|-------------|
| `(α : Type)` | Explicit | Caller must provide |
| `{α : Type}` | Implicit | Lean infers from usage |
| `[inst : C α]` | Instance | Lean finds type class instance |
| `{{α : Type}}` | Strict implicit | Never inferred from result type |

### Universe Polymorphism

```lean
def id.{u} {α : Type u} (x : α) : α := x

-- Works at any universe level
#check id 42       -- Type
#check id Nat      -- Type 1
#check id Type     -- Type 2
```

---

## Namespaces and Sections

### Namespace

```lean
namespace MyLib
  def helper := 1
  def public := helper + 1
end MyLib

#check MyLib.public
```

### Section (for temporary variables)

```lean
section
  variable (α : Type)
  variable [BEq α]

  def contains (xs : List α) (x : α) : Bool := ...
end
-- α and BEq constraint automatically added to contains
```

### Open

```lean
open List in  -- Local open
#check map

open List (map filter)  -- Import specific names
open List hiding map    -- Import all except
```

---

## Common Anti-Patterns

### Overly Explicit Types

```lean
-- ❌ Too verbose
def f (n : Nat) : Nat := (n : Nat) + (1 : Nat)

-- ✓ Let inference work
def f (n : Nat) := n + 1
```

### Ignoring Structure Updates

```lean
-- ❌ Rebuilding entire structure
def moveX (p : Point) (dx : Float) : Point :=
  { x := p.x + dx, y := p.y }

-- ✓ Functional update
def moveX (p : Point) (dx : Float) : Point :=
  { p with x := p.x + dx }
```

### Missing Deriving

```lean
-- ❌ No way to print
structure Foo where x : Nat

-- ✓ Add deriving for common uses
structure Foo where
  x : Nat
  deriving Repr, BEq, Hashable
```

---

## Sources

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
- [Lean 4 Manual](https://lean-lang.org/lean4/doc/)
