---
name: lean-fp-type-classes
description: Ad-hoc polymorphism and operator overloading in Lean. Use when defining type classes, creating instances, implementing interfaces, deriving, or working with coercions.
allowed-tools: Read, Grep, Glob
---

# Lean 4 Type Classes

Ad-hoc polymorphism and operator overloading in Lean. Use when defining overloaded operations, implementing interfaces, or working with standard classes like Add, Repr, BEq.

**Trigger terms**: "type class", "instance", "overload", "Add", "Repr", "BEq", "deriving", "coercion"

---

## Defining Type Classes

```lean
class Plus (α : Type) where
  plus : α → α → α

-- Usage with bracket notation
#check (Plus.plus : {α : Type} → [Plus α] → α → α → α)
```

---

## Creating Instances

```lean
instance : Plus Nat where
  plus := Nat.add

instance : Plus String where
  plus := String.append

-- Now works with any Plus type
def double [Plus α] (x : α) : α := Plus.plus x x
```

---

## Standard Type Classes

| Class | Operations | Infix |
|-------|------------|-------|
| `Add α` | `add : α → α → α` | `+` |
| `Mul α` | `mul : α → α → α` | `*` |
| `BEq α` | `beq : α → α → Bool` | `==` |
| `Ord α` | `compare : α → α → Ordering` | `<`, `≤` |
| `ToString α` | `toString : α → String` | - |
| `Repr α` | `repr : α → String` | - |
| `Inhabited α` | `default : α` | - |
| `Hashable α` | `hash : α → UInt64` | - |

---

## Deriving Instances

```lean
structure Point where
  x : Float
  y : Float
  deriving Repr, BEq, Inhabited

-- Automatically generates instances!
#eval (Point.mk 1.0 2.0 : Point)  -- Uses Repr
#eval Point.mk 1.0 2.0 == Point.mk 1.0 2.0  -- Uses BEq
```

---

## Coercions

Automatic type conversions:

```lean
-- Coe: basic coercion
instance : Coe Bool Nat where
  coe b := if b then 1 else 0

-- CoeFun: callable coercion
instance : CoeFun (Reader ρ α) (fun _ => ρ → α) where
  coe r := r
```

**Types of coercion**:
- `Coe α β` — basic type conversion
- `CoeDep α (x : α) β` — dependent on value
- `CoeSort α β` — coerce to sort (type)
- `CoeFun α (fun _ => β)` — coerce to function

---

## When to Use Type Classes

**Use when:**
- Same operation needed for multiple types
- Want overloaded syntax (`+`, `*`, `==`)
- Building generic algorithms
- Extending standard library patterns

**Don't use when:**
- Single type, no polymorphism needed
- Different semantics per type (use explicit functions)
- Runtime dispatch needed (use sum types)

---

## Instance Search

Lean finds instances automatically:

```lean
-- [Plus α] means "find a Plus instance for α"
def triple [Plus α] (x : α) : α :=
  Plus.plus x (Plus.plus x x)

-- Lean resolves Plus Nat automatically
#eval triple 5  -- 15
```

**Explicit instance**: `@function (instance := myInstance) args`

---

## Common Mistakes

**Orphan instances**:
```lean
-- ❌ Defining instance in wrong module
-- Can cause coherence issues

-- ✓ Define instances in:
--   - Same module as type, OR
--   - Same module as class
```

**Missing instance**:
```lean
-- ❌ Error: failed to synthesize instance
def f [MyClass α] (x : α) := ...
f someValue  -- No MyClass instance!

-- ✓ Provide instance or derive
```

---

## See Also

- `lean-fp-basics` - Type fundamentals
- `lean-fp-monads` - Monad class
- `lean-tp-foundations` - Type theory background

**Source**: [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
