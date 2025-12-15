---
name: lean-fp-dependent-types
description: Dependent types for type-safe APIs and compile-time guarantees. Use for Vect, Fin, indexed families, universes, or making illegal states unrepresentable.
allowed-tools: Read, Grep, Glob
---

# Lean 4 Dependent Types for Programming

Using dependent types for type-safe APIs and compile-time guarantees. Use when you need length-indexed vectors, type-safe database queries, or refined types.

**Trigger terms**: "dependent type", "Vect", "Fin", "indexed family", "type-safe", "compile-time", "universe"

---

## Core Concept

Types that depend on values:

```lean
-- Vector with length in the type
def Vec (α : Type) : Nat → Type
  | 0     => Unit
  | n + 1 => α × Vec α n

#check Vec Nat 0   -- Unit
#check Vec Nat 3   -- Nat × (Nat × (Nat × Unit))
```

---

## Indexed Families

Types parameterized by values:

```lean
inductive Vect (α : Type) : Nat → Type where
  | nil  : Vect α 0
  | cons : α → Vect α n → Vect α (n + 1)

-- Type-safe head: can only call on non-empty!
def head : Vect α (n + 1) → α
  | .cons x _ => x

-- No runtime check needed - empty case impossible
```

---

## The Fin Type

Bounded natural numbers for safe indexing:

```lean
-- Fin n represents numbers 0, 1, ..., n-1
structure Fin (n : Nat) where
  val : Nat
  isLt : val < n

-- Safe array indexing (no bounds check at runtime!)
def Array.get (arr : Array α) (i : Fin arr.size) : α

-- Usage
def arr := #[1, 2, 3]
#eval arr.get ⟨1, by decide⟩  -- 2
```

---

## Tarski-Style Universes

Define types from codes:

```lean
inductive DBType where
  | int | string | bool

def DBType.asType : DBType → Type
  | .int    => Int
  | .string => String
  | .bool   => Bool

-- Type-safe row based on schema
def Row (schema : List DBType) : Type :=
  match schema with
  | []      => Unit
  | t :: ts => t.asType × Row ts
```

---

## When to Use Dependent Types

**Use when:**
- Compile-time guarantees prevent runtime errors
- Type encodes important invariants (length, bounds)
- Want to make illegal states unrepresentable
- Building DSLs with type-safe embedding

**Don't use when:**
- Simple types suffice
- Proof burden exceeds benefit
- Dynamic length/size needed at runtime
- Prototyping (add later for hardening)

---

## Decision: Dependent vs Simple Types

```
Does your type need:
├─ Length in type? → Vect α n / indexed family
├─ Bounded index? → Fin n
├─ Type from runtime value? → Tarski universe
├─ Proof of property? → Subtype / refinement
└─ None of above? → Simple types (List, Array)
```

---

## Common Patterns

**Subtype (refinement type)**:
```lean
def Pos := { n : Nat // n > 0 }

def safePred (n : Pos) : Nat := n.val - 1
```

**Sigma type (dependent pair)**:
```lean
-- Pair where second component's type depends on first
def SizedArray (α : Type) := (n : Nat) × Array α
```

---

## Common Mistakes

**Exposing implementation through types**:
```lean
-- ❌ Internal structure leaks to API
def process : Vect α (complex_computation n) → ...

-- ✓ Keep types simple at boundaries
def process : Vect α n → ...
```

**Definitional equality surprises**:
```lean
-- ❌ n + 0 and n look different to Lean
def f : Vect α (n + 0) → Vect α n  -- Type error!

-- ✓ Prove they're equal
def f (v : Vect α (n + 0)) : Vect α n :=
  cast (by simp) v
```

**Overusing dependent types**:
```lean
-- ❌ Everything indexed
-- Proof obligations everywhere!

-- ✓ Use at boundaries, simple types internally
```

---

## See Also

- `lean-tp-foundations` - Type theory background
- `lean-fp-basics` - Simple types
- `lean-fp-performance` - Fin for array optimization

**Source**: [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
