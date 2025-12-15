# Lean 4 Quick Reference - Extended Tables

Additional lookup tables and patterns for Lean 4 development.

---

## String Interpolation

```lean
let name := "world"
s!"Hello, {name}!"           -- String interpolation
m!"Message: {msg}"           -- MessageData (for errors)
f!"Formatted: {n:05}"        -- With format specifiers
```

---

## Collection Operations

### List Operations

| Function | Type | Example |
|----------|------|---------|
| `[]` | `List α` | Empty list |
| `[a, b, c]` | `List α` | Literal |
| `a :: xs` | `α → List α → List α` | Cons |
| `xs ++ ys` | `List α → List α → List α` | Append |
| `xs.length` | `Nat` | Length |
| `xs.map f` | `List β` | Map function |
| `xs.filter p` | `List α` | Keep matching |
| `xs.foldl f init` | `β` | Left fold |
| `xs.head?` | `Option α` | Safe head |
| `xs.tail?` | `Option (List α)` | Safe tail |
| `xs.get? i` | `Option α` | Safe index |
| `xs.reverse` | `List α` | Reverse |
| `xs.zip ys` | `List (α × β)` | Pair up |

### Array Operations

| Function | Type | Notes |
|----------|------|-------|
| `#[]` | `Array α` | Empty |
| `#[a, b, c]` | `Array α` | Literal |
| `arr.push x` | `Array α` | Add element |
| `arr.pop` | `Array α` | Remove last |
| `arr.size` | `Nat` | Length |
| `arr[i]` | `α` | Index (with proof) |
| `arr[i]?` | `Option α` | Safe index |
| `arr[i]!` | `α` | Panic if invalid |

---

## Option and Except

### Option Combinators

```lean
x.map f           -- Apply f if some
x.bind f          -- Monadic bind
x.getD default    -- Get or default
x.get!            -- Panic if none
x.isSome          -- Bool check
x.isNone          -- Bool check
x.toList          -- [] or [a]
```

### Except Combinators

```lean
Except.ok x       -- Success
Except.error e    -- Failure
x.map f           -- Map success
x.mapError f      -- Map error
x.bind f          -- Chain
x.toOption        -- Discard error
```

---

## Control Flow

### Conditionals

```lean
if cond then a else b          -- Standard if
if h : cond then ... else ...  -- With hypothesis

-- Match expressions
match x with
| pattern1 => result1
| pattern2 => result2
| _ => default
```

### Loops (in do blocks)

```lean
for x in xs do action          -- For loop
while cond do action           -- While loop
repeat action until cond       -- Repeat until
```

---

## Attribute Reference

| Attribute | Purpose |
|-----------|---------|
| `@[simp]` | Add to simp database |
| `@[inline]` | Inline function |
| `@[specialize]` | Specialize for types |
| `@[extern "name"]` | FFI binding |
| `@[reducible]` | Always unfold |
| `@[irreducible]` | Never unfold |
| `@[instance]` | Type class instance |
| `@[class]` | Declare type class |
| `@[macro]` | Syntax macro |
| `@[elab_rules]` | Elaboration rules |

---

## Proof Term Syntax

Direct proof construction without tactics:

```lean
-- Function introduction
fun x => body
λ x => body

-- Application
f x y

-- Constructor application
And.intro hp hq
⟨hp, hq⟩               -- Anonymous constructor

-- Match
match h with
| Or.inl hp => ...
| Or.inr hq => ...

-- Absurd
absurd hp hnp          -- p → ¬p → q
False.elim h           -- False → α
```

---

## Implicit Argument Patterns

```lean
{α : Type}             -- Implicit (inferred)
[inst : Class α]       -- Instance (searched)
(α : Type)             -- Explicit (provided)
{{α : Type}}           -- Strict implicit
⦃α : Type⦄             -- Same, alternate syntax
```

**Accessing implicits**:
```lean
f (α := Nat)           -- Named implicit
@f Nat                 -- All explicit
```

---

## Namespace Commands

```lean
namespace Foo          -- Enter namespace
  def bar := 1
end Foo

open Foo               -- Bring names into scope
open Foo (bar)         -- Only specific names
open Foo hiding bar    -- Except specific names
open Foo renaming bar → baz

export Foo (bar)       -- Re-export from current namespace
```

---

## Section and Variables

```lean
section MySection
  variable (α : Type) [inst : BEq α]  -- Implicit in section

  def foo (x y : α) := x == y         -- Uses variable
end MySection
-- foo : {α : Type} → [inst : BEq α] → α → α → Bool
```

---

## Error Handling in IO

```lean
-- Try/catch
try
  riskyOperation
catch e =>
  IO.eprintln s!"Error: {e}"

-- OrElse
x <|> y                -- Try x, if fails try y

-- Option to IO
match opt with
| some x => pure x
| none => throw (IO.userError "not found")
```

---

## Decidability

```lean
-- Decidable propositions can compute
instance : Decidable (n < m) := ...

-- Using decidability
if n < m then ... else ...
decide : Decidable p → Bool
```

---

## Common Type Aliases

| Alias | Expands To |
|-------|------------|
| `Nat` | Natural numbers (0, 1, 2, ...) |
| `Int` | Integers |
| `Float` | 64-bit float |
| `String` | UTF-8 string |
| `Char` | Unicode scalar |
| `Unit` | Single value `()` |
| `Empty` | No values (uninhabited) |
| `Fin n` | Numbers 0..n-1 |
| `UInt8/16/32/64` | Fixed-width unsigned |
| `ByteArray` | Byte sequence |

---

## Sources

- [Lean Manual](https://lean-lang.org/lean4/doc/)
- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
