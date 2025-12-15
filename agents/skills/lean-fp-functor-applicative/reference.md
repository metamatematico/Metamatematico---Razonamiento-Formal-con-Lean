# Lean 4 Functor and Applicative Deep Dive

Extended reference for the abstraction hierarchy and functional patterns.

---

## The Abstraction Hierarchy

```
Functor ─────────────────────┐
    │                        │
    ▼                        ▼
Applicative            SeqLeft/SeqRight
    │
    ├──────────────────┐
    │                  │
    ▼                  ▼
  Monad            Alternative
```

Each level adds capabilities:
- **Functor**: Transform contents
- **Applicative**: Combine independent computations
- **Monad**: Chain dependent computations
- **Alternative**: Handle failure with fallbacks

---

## Functor Laws (Formal)

```lean
-- Identity: mapping id is identity
functor_id : ∀ (x : f α), id <$> x = x

-- Composition: mapping composition distributes
functor_comp : ∀ (g : β → γ) (h : α → β) (x : f α),
  (g ∘ h) <$> x = g <$> (h <$> x)
```

**Why laws matter**:
- Refactoring safety: `f <$> (g <$> x)` ↔ `(f ∘ g) <$> x`
- Predictable behavior: mapping doesn't change structure

---

## Applicative Laws (Formal)

```lean
-- Identity
applicative_id : pure id <*> v = v

-- Homomorphism
applicative_hom : pure f <*> pure x = pure (f x)

-- Interchange
applicative_inter : u <*> pure y = pure (· y) <*> u

-- Composition
applicative_comp : pure (· ∘ ·) <*> u <*> v <*> w = u <*> (v <*> w)
```

---

## Applicative Internals

### seq vs seqLeft vs seqRight

```lean
class Applicative (f : Type → Type) extends Functor f where
  pure : α → f α
  seq : f (α → β) → (Unit → f α) → f β  -- <*>
  seqLeft : f α → (Unit → f β) → f α    -- <*
  seqRight : f α → (Unit → f β) → f β   -- *>

-- <* runs both, keeps left result
-- *> runs both, keeps right result
```

### Why `Unit → f α`?

The thunk delays evaluation:
```lean
-- Without thunk: both computed even if first fails
-- With thunk: second only computed if needed

some 1 <*> (fun () => expensiveComputation)
```

---

## Functor Variants

### Contravariant Functor

```lean
-- Contravariant: flips the arrow
class Contravariant (f : Type → Type) where
  contramap : (β → α) → f α → f β

-- Example: Predicate is contravariant
structure Predicate (α : Type) where
  test : α → Bool

instance : Contravariant Predicate where
  contramap f p := ⟨p.test ∘ f⟩
```

### Bifunctor

```lean
-- Two type parameters, both covariant
class Bifunctor (f : Type → Type → Type) where
  bimap : (α → γ) → (β → δ) → f α β → f γ δ

-- Example: Pair
instance : Bifunctor Prod where
  bimap f g (a, b) := (f a, g b)
```

---

## Alternative Internals

```lean
class Alternative (f : Type → Type) extends Applicative f where
  failure : f α
  orElse : f α → (Unit → f α) → f α

-- guard: conditional failure
def guard [Alternative f] (b : Bool) : f Unit :=
  if b then pure () else failure

-- many: zero or more
partial def many [Alternative f] (p : f α) : f (List α) :=
  some' <|> pure []
  where some' := List.cons <$> p <*> many p

-- some: one or more
partial def some [Alternative f] (p : f α) : f (List α) :=
  List.cons <$> p <*> many p
```

---

## The Validate Pattern (Complete)

### Implementation

```lean
inductive Validate (ε α : Type) where
  | ok : α → Validate ε α
  | errors : NonEmptyList ε → Validate ε α

-- Helper
def Validate.error (e : ε) : Validate ε α :=
  .errors ⟨e, []⟩

-- Functor instance
instance : Functor (Validate ε) where
  map f
    | .ok x => .ok (f x)
    | .errors es => .errors es

-- Applicative instance (key: accumulates errors)
instance : Applicative (Validate ε) where
  pure := .ok
  seq f x :=
    match f, x () with
    | .ok g, .ok y => .ok (g y)
    | .ok _, .errors es => .errors es
    | .errors es, .ok _ => .errors es
    | .errors es1, .errors es2 => .errors (es1 ++ es2)
```

### When to Use Validate vs Except

| Validate | Except |
|----------|--------|
| Form validation | File parsing |
| User input | Configuration |
| Show all errors | Stop on first |
| Independent checks | Dependent checks |

---

## Applicative Lifting Patterns

### lift2

```lean
def lift2 [Applicative f] (fn : α → β → γ) (a : f α) (b : f β) : f γ :=
  fn <$> a <*> b

-- Usage
#eval lift2 (· + ·) (some 3) (some 4)  -- some 7
```

### sequenceA

```lean
def sequenceA [Applicative f] : List (f α) → f (List α)
  | [] => pure []
  | x :: xs => List.cons <$> x <*> sequenceA xs

#eval sequenceA [some 1, some 2, some 3]  -- some [1, 2, 3]
#eval sequenceA [some 1, none, some 3]    -- none
```

### traverse

```lean
def traverse [Applicative f] (fn : α → f β) : List α → f (List β)
  | [] => pure []
  | x :: xs => List.cons <$> fn x <*> traverse fn xs

-- sequenceA = traverse id
```

---

## Combining Alternative with Applicative

```lean
-- Try alternatives until one succeeds
def firstSuccess [Alternative f] : List (f α) → f α
  | [] => failure
  | x :: xs => x <|> firstSuccess xs

-- Optional: succeed with none if fails
def optional [Alternative f] (p : f α) : f (Option α) :=
  some <$> p <|> pure none

-- Choice with default
def withDefault [Alternative f] (p : f α) (d : α) : f α :=
  p <|> pure d
```

---

## Applicative vs Monad (Technical)

```lean
-- Applicative: structure is static
-- Both effects happen regardless of values
pure f <*> actionA <*> actionB

-- Monad: structure depends on values
-- actionB may or may not run depending on x
do x ← actionA
   if condition x then actionB else actionC
```

**Practical implication**: Applicative can be parallelized, Monad cannot.

---

## Common Instances

### Option

```lean
instance : Functor Option where
  map f o := match o with
    | none => none
    | some x => some (f x)

instance : Applicative Option where
  pure := some
  seq f x := match f with
    | none => none
    | some g => g <$> x ()
```

### List

```lean
instance : Applicative List where
  pure x := [x]
  seq fs xs := fs.flatMap (fun f => f <$> xs ())

-- Cartesian product behavior!
#eval [(· + 1), (· * 2)] <*> [10, 20]
-- [11, 21, 20, 40]
```

---

## Sources

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
- [Applicatives chapter](https://lean-lang.org/functional_programming_in_lean/functor-applicative-monad.html)
