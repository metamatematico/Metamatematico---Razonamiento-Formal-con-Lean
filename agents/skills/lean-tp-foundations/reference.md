# Lean 4 Type Theory Deep Dive

Extended reference for dependent type theory concepts in Lean 4.

---

## Calculus of Constructions

Lean is based on the **Calculus of Constructions with inductive types**, a powerful dependent type theory system:

- Types are first-class objects
- Functions can depend on values (dependent types)
- Propositions are types (`Prop`)
- Proofs are terms

---

## Universe Levels in Detail

### The Hierarchy

```lean
#check Nat          -- Nat : Type
#check Type         -- Type : Type 1
#check Type 1       -- Type 1 : Type 2
#check Type 2       -- Type 2 : Type 3
-- Type n : Type (n+1) for all n

#check Prop         -- Prop : Type
-- Prop is special: proof-irrelevant
```

### Why Universes?

Without universe stratification, we could write:

```lean
-- IMPOSSIBLE in Lean (would cause paradox)
def Russell := { x : Type | x ∉ x }
```

The hierarchy prevents self-referential paradoxes.

### Universe Polymorphism

```lean
-- Polymorphic across all universe levels
def List.{u} (α : Type u) : Type u := ...

-- Instantiate at specific levels
#check List.{0} Nat     -- List Nat : Type
#check List.{1} Type    -- List Type : Type 1
#check @List.{0}        -- explicit universe annotation
```

---

## Dependent Function Types

### Pi Types (Π)

The general form of function types where return type depends on argument:

```lean
-- Non-dependent (ordinary function)
Nat → Bool

-- Dependent (return type varies with input)
Π (n : Nat), Vec Nat n
-- or equivalently
∀ (n : Nat), Vec Nat n
(n : Nat) → Vec Nat n
```

### Implicit Arguments

```lean
-- Explicit: must provide at call site
def length (α : Type) (xs : List α) : Nat := ...

-- Implicit: Lean infers
def length {α : Type} (xs : List α) : Nat := ...

-- Force explicit when needed
length (α := Int) myList
@length Int myList
```

### Instance Arguments

```lean
-- [brackets] for type class instances
def toString {α : Type} [ToString α] (x : α) : String := ...

-- Lean finds instance automatically
#eval toString 42  -- finds ToString Nat instance
```

---

## Prop vs Type

| Property | `Prop` | `Type` |
|----------|--------|--------|
| Purpose | Propositions/proofs | Data/computation |
| Proof irrelevance | Yes (all proofs equal) | No (values distinguished) |
| Erasure | Erased at runtime | Kept at runtime |
| Extraction | Cannot extract data | Can extract data |

### Proof Irrelevance Example

```lean
-- In Prop: any two proofs are definitionally equal
theorem proof_irrel (p : Prop) (h1 h2 : p) : h1 = h2 := rfl

-- This is why you can't pattern match on Prop to get data
-- (unless using decidability)
```

### Subsingleton Elimination

```lean
-- Can eliminate Prop to Prop
example (h : ∃ x, P x) : ∃ x, P x := h

-- Cannot eliminate Prop to Type (data extraction blocked)
-- WRONG: def witness (h : ∃ x, P x) : α := ...
-- Need decidability or Classical.choice
```

---

## Product Types

### Non-Dependent (Prod)

```lean
structure Prod (α : Type u) (β : Type v) where
  fst : α
  snd : β

-- Notation
#check (1, true)        -- Nat × Bool
#check Prod.mk 1 true   -- Same thing
```

### Dependent (Sigma)

```lean
structure Sigma {α : Type u} (β : α → Type v) where
  fst : α
  snd : β fst

-- Notation
#check (n : Nat) × Vec Nat n  -- Sigma type
#check ⟨3, v3⟩                -- Where v3 : Vec Nat 3
```

---

## Sum Types

### Non-Dependent (Sum)

```lean
inductive Sum (α : Type u) (β : Type v) where
  | inl : α → Sum α β
  | inr : β → Sum α β

-- Notation: α ⊕ β
```

### Pattern Matching

```lean
def analyze : Nat ⊕ Bool → String
  | Sum.inl n => s!"Got number {n}"
  | Sum.inr b => s!"Got bool {b}"
```

---

## Definitional vs Propositional Equality

### Definitional (Computational)

```lean
-- These are definitionally equal (reduce to same term)
example : 2 + 2 = 4 := rfl
example : (fun x => x + 1) 5 = 6 := rfl
```

### Propositional (Requires Proof)

```lean
-- These need proofs (not definitionally equal)
example (n : Nat) : n + 0 = n := by simp
example (n m : Nat) : n + m = m + n := Nat.add_comm n m
```

---

## Lean Commands Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `#check` | Show type | `#check Nat` |
| `#eval` | Evaluate | `#eval 2 + 3` |
| `#print` | Show definition | `#print Nat.add` |
| `#reduce` | Reduce to normal form | `#reduce (fun x => x + 1) 5` |
| `example` | Anonymous theorem | `example : 1 = 1 := rfl` |
| `theorem` | Named theorem | `theorem foo : P := proof` |
| `def` | Definition | `def f (x : Nat) := x + 1` |

---

## Sources

- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
