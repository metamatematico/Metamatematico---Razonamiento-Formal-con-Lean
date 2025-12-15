# Lean 4 Type Classes Deep Dive

Extended reference for type class mechanics, instance resolution, and advanced patterns.

---

## Type Class Anatomy

```lean
class MyClass (α : Type) where
  operation : α → α → α
  identity : α
  law : ∀ x, operation x identity = x  -- Optional: include laws
```

**Components**:
- **Parameters**: Types the class is polymorphic over
- **Methods**: Operations the class provides
- **Default implementations**: Optional method implementations
- **Laws**: Proof obligations (rarely enforced)

---

## Instance Resolution Algorithm

Lean uses **backward chaining** to find instances:

1. Check local instances (function parameters)
2. Search registered instances in scope
3. Try instance constructors recursively
4. Fail if no unique instance found

### Resolution Order

```lean
-- Local takes precedence
def f [inst : Add α] (x : α) : α :=
  -- `inst` used here, not any global instance
  x + x

-- Explicit override
@Add.add (inst := customInstance) a b
```

### Avoiding Ambiguity

```lean
-- ❌ Ambiguous: two instances in scope
instance instA : MyClass Nat := ...
instance instB : MyClass Nat := ...

-- ✓ Use scoped instances
scoped instance : MyClass Nat := ...

-- Or explicit selection
@myFunction (inst := instA) args
```

---

## Deriving Mechanism

### Built-in Derivable Classes

| Class | What it generates |
|-------|------------------|
| `Repr` | String representation for `#eval` |
| `BEq` | Structural equality |
| `Ord` | Lexicographic ordering |
| `Hashable` | Hash function |
| `Inhabited` | Default value |
| `DecidableEq` | Decidable equality proofs |
| `Nonempty` | Existence proof |

### Deriving Strategies

```lean
-- Derive at definition
structure Foo where
  x : Nat
  deriving Repr, BEq

-- Derive later
deriving instance Repr for Foo

-- With handler (advanced)
deriving instance Repr, BEq, Hashable for MyType
```

---

## Coercion Types Explained

### Coe (Basic Coercion)

```lean
instance : Coe Nat Int where
  coe n := Int.ofNat n

-- Automatic: Nat → Int
def f (x : Int) := x + 1
#eval f 5  -- 5 coerced to Int
```

### CoeDep (Dependent Coercion)

```lean
-- Coercion depends on the value
instance : CoeDep (List α) (x :: xs) (NonEmptyList α) where
  coe := ⟨x, xs⟩

-- Only works for non-empty lists
def nel : NonEmptyList Nat := [1, 2, 3]
```

### CoeSort (Sort Coercion)

```lean
-- Coerce value to a type
structure Wrapper where
  inner : Type

instance : CoeSort Wrapper Type where
  coe w := w.inner

-- Use wrapper as type
def w : Wrapper := ⟨Nat⟩
def x : w := 42  -- w coerced to Nat
```

### CoeFun (Function Coercion)

```lean
structure Adder where
  n : Nat

instance : CoeFun Adder (fun _ => Nat → Nat) where
  coe a := (· + a.n)

-- Use adder as function
def add5 : Adder := ⟨5⟩
#eval add5 10  -- 15
```

---

## Multi-Parameter Type Classes

```lean
class Convert (α β : Type) where
  convert : α → β

instance : Convert Nat Int where
  convert := Int.ofNat

instance : Convert String (List Char) where
  convert := String.toList

-- Functional dependencies (outParam)
class Cast (α : Type) (β : outParam Type) where
  cast : α → β
-- β determined by α
```

### outParam vs Explicit

```lean
-- With outParam: β inferred from α
class FromNat (α : Type) (n : outParam Nat) where
  fromNat : α

-- Without: must specify both
class Convert (α β : Type) where
  convert : α → β
```

---

## Class Hierarchies

### Extending Classes

```lean
class Semigroup (α : Type) where
  op : α → α → α
  assoc : ∀ a b c, op (op a b) c = op a (op b c)

class Monoid (α : Type) extends Semigroup α where
  e : α
  left_id : ∀ a, op e a = a
  right_id : ∀ a, op a e = a

-- Monoid instance automatically provides Semigroup
```

### Standard Hierarchy

```
Functor ← Applicative ← Monad
                ↑
           Alternative
```

---

## Named Instances

```lean
-- Anonymous (preferred for unique instances)
instance : Add Nat where ...

-- Named (when multiple instances possible)
instance addNat : Add Nat where ...
instance mulNat : HMul Nat Nat Nat where ...

-- Reference named instance
#check (addNat : Add Nat)
@Add.add addNat 1 2
```

---

## Instance Priority

```lean
-- Higher priority = checked first (default 1000)
instance (priority := high) : MyClass Nat where ...
instance (priority := low) : MyClass Nat where ...

-- Priority levels
-- default := 1000
-- low := 100
-- high := 10000
```

---

## Scoped Instances

```lean
namespace MyModule
  scoped instance : Add String where
    add := String.append
end MyModule

-- Only available when MyModule is open
open MyModule in
#eval "a" + "b"  -- "ab"
```

---

## Common Patterns

### Decidable Equality

```lean
-- For types where equality is computable
instance [DecidableEq α] : DecidableEq (Option α) :=
  fun a b => match a, b with
  | none, none => isTrue rfl
  | some x, some y =>
    if h : x = y then isTrue (congrArg some h)
    else isFalse (fun h' => h (Option.some.inj h'))
  | _, _ => isFalse (fun h => Option.noConfusion h)
```

### Heterogeneous Operations

```lean
-- HAdd allows different types
class HAdd (α β γ : Type) where
  hAdd : α → β → γ

instance : HAdd Nat Float Float where
  hAdd n f := Float.ofNat n + f
```

---

## Debugging Instance Search

```lean
-- Show instance search trace
set_option trace.Meta.synthInstance true in
#check (inferInstance : Add Nat)

-- Check what instance was found
#check (inferInstance : Add Nat)
#print Add.add  -- Shows the definition
```

---

## Sources

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
- [Type Classes chapter](https://lean-lang.org/functional_programming_in_lean/type-classes.html)
