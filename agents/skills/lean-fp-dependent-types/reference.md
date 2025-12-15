# Lean 4 Dependent Types Deep Dive

Extended reference for dependent type patterns and programming techniques.

---

## Dependent Type Theory Basics

### Pi Types (Π)

Functions where return type depends on argument value:

```lean
-- Non-dependent function
Nat → Bool  -- Same as ∀ (_ : Nat), Bool

-- Dependent function
∀ (n : Nat), Vect α n  -- Return type mentions n

-- Notation equivalences
(n : Nat) → Vect α n   -- Explicit argument
{n : Nat} → Vect α n   -- Implicit argument
∀ n, Vect α n          -- Implicit (common in proofs)
```

### Sigma Types (Σ)

Pairs where second component's type depends on first:

```lean
-- Sigma type definition
structure Sigma {α : Type} (β : α → Type) where
  fst : α
  snd : β fst

-- Notation: (a : α) × β a
def SizedList := (n : Nat) × Vect String n

-- Creating sigma values
def example : SizedList := ⟨3, Vect.cons "a" (Vect.cons "b" (Vect.cons "c" Vect.nil))⟩
```

---

## Indexed Families Explained

### Parameter vs Index

```lean
-- Parameter (α): same for all constructors
-- Index (n : Nat): varies per constructor
inductive Vect (α : Type) : Nat → Type where
  | nil  : Vect α 0           -- Index is 0
  | cons : α → Vect α n → Vect α (n + 1)  -- Index is n + 1
```

**Parameter**: Fixed before the colon
**Index**: Varies, after the colon

### Equality Type as Indexed Family

```lean
-- Eq is indexed by two values
inductive Eq {α : Type} (a : α) : α → Prop where
  | refl : Eq a a

-- Only one constructor, and it constrains the index to equal a
```

---

## The Fin Type in Detail

### Definition

```lean
structure Fin (n : Nat) where
  val : Nat
  isLt : val < n

-- Fin 3 has three values:
-- ⟨0, proof⟩, ⟨1, proof⟩, ⟨2, proof⟩
```

### Construction

```lean
-- Literal syntax (when n is known)
#check (2 : Fin 5)  -- Works, proof generated

-- Manual construction
def two : Fin 5 := ⟨2, by decide⟩

-- From Nat with bound check
def Fin.ofNat? (i : Nat) (n : Nat) : Option (Fin n) :=
  if h : i < n then some ⟨i, h⟩ else none
```

### Operations

```lean
-- Successor (wrapping)
def Fin.succ : Fin n → Fin (n + 1) := fun ⟨i, h⟩ => ⟨i + 1, Nat.succ_lt_succ h⟩

-- Casting when bounds change
def Fin.castLe (h : n ≤ m) : Fin n → Fin m := fun ⟨i, lt⟩ => ⟨i, Nat.lt_of_lt_of_le lt h⟩

-- All values of Fin n
def Fin.range (n : Nat) : List (Fin n) := ...
```

---

## Tarski Universes Pattern

### Basic Pattern

```lean
-- 1. Define code type
inductive TyCode where
  | nat | bool | prod : TyCode → TyCode → TyCode

-- 2. Interpretation function
def TyCode.interp : TyCode → Type
  | .nat => Nat
  | .bool => Bool
  | .prod a b => a.interp × b.interp

-- 3. Use in dependent types
def Value (code : TyCode) := code.interp

def example : Value (.prod .nat .bool) := (42, true)
```

### Database Schema Pattern

```lean
inductive ColType where
  | int | text | bool | nullable : ColType → ColType

def ColType.asType : ColType → Type
  | .int => Int
  | .text => String
  | .bool => Bool
  | .nullable t => Option t.asType

def Schema := List (String × ColType)

def Row : Schema → Type
  | [] => Unit
  | (_, t) :: rest => t.asType × Row rest

-- Type-safe row construction
def exampleRow : Row [("id", .int), ("name", .text), ("active", .bool)] :=
  (42, ("Alice", (true, ())))
```

---

## Subtype and Refinement

### Subtype Definition

```lean
-- Subtype carves out values satisfying a predicate
structure Subtype {α : Type} (p : α → Prop) where
  val : α
  property : p val

-- Notation: { x : α // p x }
def Pos := { n : Nat // n > 0 }
def NonEmpty (α : Type) := { xs : List α // xs ≠ [] }
```

### Working with Subtypes

```lean
-- Creating
def five : Pos := ⟨5, by decide⟩

-- Extracting
def pred (n : Pos) : Nat := n.val - 1

-- Preserving property
def double (n : Pos) : Pos := ⟨n.val * 2, by omega⟩
```

---

## Decidability and Proof Terms

### When Proofs Are Needed

```lean
-- Array indexing needs proof i < arr.size
def arr := #[1, 2, 3]

-- Option 1: Literal (proof auto-generated)
#eval arr.get ⟨1, by decide⟩

-- Option 2: Safe access returning Option
#eval arr[1]?

-- Option 3: Proof from context
def getFirst {α : Type} (arr : Array α) (h : 0 < arr.size) : α :=
  arr.get ⟨0, h⟩
```

### decide Tactic

```lean
-- `decide` works for decidable propositions
example : 5 < 10 := by decide  -- Computes at compile time

-- Can use in term mode
def bounded : Fin 10 := ⟨5, by decide⟩
```

---

## Type-Level Computation

### Definitional Equality

```lean
-- These are definitionally equal (same after reduction)
#check (Vect Nat 2 : Type)  -- Nat × (Nat × Unit)

-- These require proof
example : n + 0 = n := Nat.add_zero n
```

### cast and Heterogeneous Equality

```lean
-- When types are propositionally but not definitionally equal
def cast {α β : Type} (h : α = β) (a : α) : β :=
  h ▸ a

-- Usage
def reindex (v : Vect α (n + 0)) : Vect α n :=
  cast (by simp) v
```

---

## Universe Levels

### Basic Hierarchy

```lean
#check Nat           -- Nat : Type
#check Type          -- Type : Type 1
#check Type 1        -- Type 1 : Type 2

-- Type is shorthand for Type 0
```

### Universe Polymorphism

```lean
def List.{u} (α : Type u) : Type u := ...

-- Instantiate at different levels
#check List.{0} Nat    -- Type
#check List.{1} Type   -- Type 1
```

---

## Common Patterns Summary

| Pattern | Use Case | Example |
|---------|----------|---------|
| Indexed Family | Length/size in type | `Vect α n` |
| Fin | Bounded indices | `Fin n` for array indexing |
| Subtype | Refined values | `{ n : Nat // n > 0 }` |
| Sigma | Dependent pairs | `(n : Nat) × Vect α n` |
| Tarski Universe | Type from code | `DBType.asType` |

---

## Sources

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
- [Dependent Types chapter](https://lean-lang.org/functional_programming_in_lean/dependent-types.html)
