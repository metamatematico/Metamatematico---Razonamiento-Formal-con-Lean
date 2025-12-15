# Lean 4 Type Theory Examples

Working code examples demonstrating foundational concepts.

---

## Universe Examples

```lean
-- Universe hierarchy
#check Nat            -- Nat : Type
#check Type           -- Type : Type 1
#check Type 1         -- Type 1 : Type 2

-- Prop is special
#check Prop           -- Prop : Type
#check True           -- True : Prop
#check 1 = 1          -- Prop

-- Proper universe usage
def TypeWrapper : Type 1 := Type  -- ✓ Correct
-- def bad : Type := Type        -- ✗ Error: Type lives in Type 1
```

---

## Function Type Examples

```lean
-- Right associativity
def add : Nat → Nat → Nat := fun m n => m + n

-- Equivalent explicit version
def add' : Nat → (Nat → Nat) := fun m => fun n => m + n

-- Currying in action
def add5 : Nat → Nat := add 5
#eval add5 10  -- 15

-- Multiple parameters (curried)
def triple : Nat → Nat → Nat → Nat := fun a b c => a + b + c
#eval triple 1 2 3  -- 6
```

---

## Dependent Type Examples

```lean
-- Length-indexed vector (type depends on value)
def Vec (α : Type) : Nat → Type
  | 0     => Unit
  | n + 1 => α × Vec α n

-- Check the types
#check Vec Nat 0   -- Unit
#check Vec Nat 1   -- Nat × Unit
#check Vec Nat 3   -- Nat × (Nat × (Nat × Unit))

-- Create vectors
def vec0 : Vec Nat 0 := ()
def vec1 : Vec Nat 1 := (42, ())
def vec3 : Vec Nat 3 := (1, (2, (3, ())))

-- Type-safe head (only works on non-empty!)
def head {α : Type} {n : Nat} (v : Vec α (n + 1)) : α :=
  v.fst

#eval head vec3  -- 1
-- head vec0     -- ✗ Type error! Vec Nat 0 ≠ Vec Nat (n + 1)
```

---

## Implicit Argument Examples

```lean
-- Explicit type parameter (verbose)
def length_explicit (α : Type) (xs : List α) : Nat :=
  match xs with
  | [] => 0
  | _ :: ys => 1 + length_explicit α ys

-- Implicit type parameter (preferred)
def length_implicit {α : Type} (xs : List α) : Nat :=
  match xs with
  | [] => 0
  | _ :: ys => 1 + length_implicit ys

-- Usage
#eval length_explicit Nat [1, 2, 3]  -- Must provide type
#eval length_implicit [1, 2, 3]       -- Type inferred

-- Force implicit to be explicit
#eval length_implicit (α := Int) [1, 2, 3]
#eval @length_implicit Nat [1, 2, 3]
```

---

## Product Type Examples

```lean
-- Non-dependent product (Prod)
def pair1 : Nat × Bool := (42, true)
def pair2 : Prod Nat Bool := Prod.mk 42 true

-- Accessing components
#eval pair1.1      -- 42
#eval pair1.2      -- true
#eval pair1.fst    -- 42
#eval pair1.snd    -- true

-- Dependent product (Sigma)
-- The second type depends on the first value
def SizedList := (n : Nat) × Vec Nat n

-- Create instances
def sized0 : SizedList := ⟨0, ()⟩
def sized3 : SizedList := ⟨3, (1, (2, (3, ())))⟩

-- Access
#eval sized3.1  -- 3 (the size)
```

---

## Prop vs Type Examples

```lean
-- In Prop: propositions
#check 1 = 1           -- Prop
#check ∀ n : Nat, n = n  -- Prop
#check True            -- Prop
#check False           -- Prop

-- In Type: data
#check Nat             -- Type
#check List Nat        -- Type
#check Bool            -- Type

-- Proof irrelevance in Prop
theorem proof_irrel (h1 h2 : 1 = 1) : h1 = h2 := rfl

-- All proofs of same proposition are equal
-- This is why runtime erasure is safe
```

---

## Definitional Equality Examples

```lean
-- These work with rfl (definitionally equal)
example : 2 + 2 = 4 := rfl
example : (fun x => x) 5 = 5 := rfl
example : List.length [1, 2, 3] = 3 := rfl

-- These need proofs (propositionally equal)
example (n : Nat) : n + 0 = n := by simp
example (n : Nat) : 0 + n = n := rfl  -- But this IS definitional!
-- (Because + is defined by recursion on first argument)
```

---

## Universe Polymorphism Examples

```lean
-- Polymorphic identity function
def id' {α : Type u} (x : α) : α := x

-- Works at any universe level
#check id' 42          -- Nat (Type 0)
#check id' Nat         -- Type (Type 1)
#check id' Type        -- Type 1 (Type 2)

-- Polymorphic list
def myList.{u} (α : Type u) := List α

#check myList.{0} Nat     -- Type
#check myList.{1} Type    -- Type 1
```

---

## Sigma Type Practical Example

```lean
-- Database row with schema-dependent types
inductive DBType where
  | int | string | bool

def DBType.asType : DBType → Type
  | .int    => Int
  | .string => String
  | .bool   => Bool

-- A typed column value
def TypedValue := (t : DBType) × t.asType

def intVal : TypedValue := ⟨.int, 42⟩
def strVal : TypedValue := ⟨.string, "hello"⟩
def boolVal : TypedValue := ⟨.bool, true⟩
```
