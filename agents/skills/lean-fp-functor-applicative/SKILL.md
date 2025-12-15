---
name: lean-fp-functor-applicative
description: Functor, Applicative, Alternative, and the abstraction hierarchy. Use when transforming values in containers, combining independent computations, or choosing abstraction level.
allowed-tools: Read, Grep, Glob
---

# Lean 4 Functor and Applicative

Functor, Applicative, and the abstraction hierarchy. Use when transforming values in containers, combining independent computations, or choosing the right abstraction level.

**Trigger terms**: "Functor", "Applicative", "map", "<$>", "<*>", "pure", "Validate", "Alternative"

---

## Functor

Transform values inside a container:

```lean
class Functor (f : Type → Type) where
  map : (α → β) → f α → f β

-- Infix: <$>
-- f <$> x = Functor.map f x

-- Example
#eval (· + 1) <$> some 5      -- some 6
#eval (· + 1) <$> [1, 2, 3]   -- [2, 3, 4]
```

**Functor Laws**:
- Identity: `id <$> x = x`
- Composition: `(g ∘ f) <$> x = g <$> (f <$> x)`

---

## Applicative

Combine independent computations:

```lean
class Applicative (f : Type → Type) extends Functor f where
  pure : α → f α
  seq : f (α → β) → (Unit → f α) → f β

-- Infix: <*>
-- ff <*> fx applies function in ff to value in fx

-- Example
#eval pure (· + ·) <*> some 3 <*> some 4  -- some 7
```

**Applicative Laws**:
- Identity: `pure id <*> v = v`
- Homomorphism: `pure f <*> pure x = pure (f x)`
- Interchange: `u <*> pure y = pure (· y) <*> u`

---

## Monad vs Applicative

| Applicative | Monad |
|-------------|-------|
| Independent computations | Dependent computations |
| Structure known statically | Structure depends on values |
| Can parallelize | Must sequence |
| `f <$> a <*> b` | `do x ← a; y ← b x; ...` |

**Choose Applicative when**: Results don't depend on each other.
**Choose Monad when**: Later computation needs earlier result.

---

## The Validate Pattern

Accumulate ALL errors instead of short-circuiting:

```lean
inductive Validate (ε α : Type) where
  | ok : α → Validate ε α
  | errors : NonEmptyList ε → Validate ε α

instance : Applicative (Validate ε) where
  pure := .ok
  seq f x :=
    match f, x () with
    | .ok g, .ok y => .ok (g y)
    | .ok _, .errors e => .errors e
    | .errors e, .ok _ => .errors e
    | .errors e1, .errors e2 => .errors (e1 ++ e2)  -- Combine!
```

**Use case**: Form validation where you want ALL errors, not just first.

---

## Alternative

Try alternatives on failure:

```lean
class Alternative (f : Type → Type) extends Applicative f where
  failure : f α
  orElse : f α → (Unit → f α) → f α

-- Infix: <|>
#eval none <|> some 5  -- some 5
#eval some 3 <|> some 5  -- some 3
```

**guard**: Conditionally fail
```lean
def guard [Alternative f] (b : Bool) : f Unit :=
  if b then pure () else failure
```

---

## Abstraction Level Decision Tree

```
Do your computations:
├─ Need to transform values in container?
│  └─ Functor (map / <$>)
│
├─ Combine independent values?
│  ├─ First failure stops? → Applicative
│  └─ Accumulate all errors? → Validate pattern
│
├─ Later depends on earlier result?
│  └─ Monad (bind / >>=)
│
└─ Need fallback on failure?
   └─ Alternative (<|>)
```

---

## Common Mistakes

**Using Monad when Applicative suffices**:
```lean
-- ❌ Suggests dependency that doesn't exist
do let x ← actionA
   let y ← actionB  -- y doesn't use x!
   pure (f x y)

-- ✓ Shows independence
f <$> actionA <*> actionB
```

**Confusing <*> argument order**:
```lean
-- <*> applies wrapped function to wrapped value
-- pure f <*> x <*> y = f applied to x then y
```

---

## See Also

- `lean-fp-monads` - Monad abstraction
- `lean-fp-type-classes` - Type class basics
- `lean-fp-transformers` - Combining effects

**Source**: [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
