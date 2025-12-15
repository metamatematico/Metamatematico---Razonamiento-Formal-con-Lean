# Lean 4 Performance Deep Dive

Extended reference for optimization techniques and runtime behavior.

---

## Tail Recursion Mechanics

### What Makes It Tail Recursive

```lean
-- The recursive call must be the LAST operation
def f x =
  if cond then
    f (x - 1)      -- ✓ Tail: nothing after f
  else
    x

def g x =
  if cond then
    1 + g (x - 1)  -- ✗ Not tail: + happens after g
  else
    x
```

### Accumulator Pattern

```lean
-- Generic pattern:
-- 1. Add accumulator parameter
-- 2. Initialize to identity element
-- 3. Build result in accumulator

-- Original
def foldRight (f : α → β → β) (init : β) : List α → β
  | [] => init
  | x :: xs => f x (foldRight f init xs)  -- Not tail

-- Tail recursive (but reverses order!)
def foldLeft (f : β → α → β) (init : β) : List α → β
  | [] => init
  | x :: xs => foldLeft f (f init x) xs   -- Tail

-- For operations that need right-to-left:
-- Either reverse input or reverse output
```

---

## Memory and Stack

### Stack Overflow Mechanics

```lean
-- Each non-tail call creates a stack frame:
sum [1, 2, 3, 4]
→ 1 + sum [2, 3, 4]           -- Frame 1
→ 1 + (2 + sum [3, 4])        -- Frame 2
→ 1 + (2 + (3 + sum [4]))     -- Frame 3
→ 1 + (2 + (3 + (4 + sum []))) -- Frame 4
→ 1 + (2 + (3 + (4 + 0)))     -- Unwind begins

-- Tail recursive uses constant stack:
sumTR [1, 2, 3, 4] 0
→ sumTR [2, 3, 4] 1    -- Reuse same frame
→ sumTR [3, 4] 3       -- Reuse same frame
→ sumTR [4] 6          -- Reuse same frame
→ sumTR [] 10          -- Reuse same frame
→ 10
```

### Memory Allocation

```lean
-- List cons allocates on heap
x :: xs  -- New cell pointing to x and xs

-- Array operations can reuse memory when unique
arr.set i v  -- In-place if arr is unique reference
```

---

## Array Optimization

### Reference Counting

Lean uses reference counting for memory management:

```lean
-- Unique reference: modification is in-place
let arr := #[1, 2, 3]
let arr := arr.set ⟨0, by decide⟩ 10  -- Mutates in place

-- Shared reference: must copy
let arr := #[1, 2, 3]
let arr2 := arr
let arr3 := arr.set ⟨0, by decide⟩ 10  -- Must copy
```

### ForIn for Efficient Loops

```lean
-- ForIn provides efficient iteration
def sumArray (arr : Array Nat) : Nat := Id.run do
  let mut sum := 0
  for x in arr do
    sum := sum + x
  pure sum

-- Compiled to efficient loop, no intermediate allocations
```

---

## Proving Termination

### Structural Recursion

```lean
-- Lean accepts when argument gets structurally smaller
def length : List α → Nat
  | [] => 0
  | _ :: xs => 1 + length xs  -- xs smaller than input
```

### termination_by

```lean
-- When structural recursion isn't obvious
def div (n k : Nat) : Nat :=
  if k > 0 && n ≥ k then
    1 + div (n - k) k
  else
    0
termination_by n  -- n decreases each call
```

### Well-Founded Recursion

```lean
-- For complex termination arguments
def ack : Nat → Nat → Nat
  | 0, m => m + 1
  | n + 1, 0 => ack n 1
  | n + 1, m + 1 => ack n (ack (n + 1) m)
termination_by n m => (n, m)  -- Lexicographic ordering
```

---

## Fusion and Deforestation

### The Problem

```lean
-- Creates intermediate list
xs.map f |>.filter p |>.map g

-- Traverses list 3 times, allocates 2 intermediate lists
```

### Manual Fusion

```lean
-- Combine operations manually
def mapFilterMap (f : α → β) (p : β → Bool) (g : β → γ) : List α → List γ
  | [] => []
  | x :: xs =>
    let y := f x
    if p y then g y :: mapFilterMap f p g xs
    else mapFilterMap f p g xs
```

### Stream Fusion (Conceptual)

```lean
-- Represent operations as transformers
-- Only materialize at end
-- (Lean doesn't have automatic fusion like Haskell)
```

---

## Strictness and Laziness

### Lean is Strict

```lean
-- Arguments evaluated before function body
def f (x : Nat) (y : Nat) := x  -- y still evaluated

-- Use thunks for laziness
def f (x : Nat) (y : Unit → Nat) := x  -- y not evaluated

-- Or Thunk type
def f (x : Nat) (y : Thunk Nat) := x
```

### Lazy Patterns

```lean
-- Lazy list
inductive LazyList (α : Type) where
  | nil
  | cons : α → Thunk (LazyList α) → LazyList α

-- Take only what's needed
def take : Nat → LazyList α → List α
  | 0, _ => []
  | _, .nil => []
  | n + 1, .cons x xs => x :: take n xs.get
```

---

## Benchmarking

### Time Measurement

```lean
-- In IO monad
def timeit (name : String) (action : IO α) : IO α := do
  let start ← IO.monoMsNow
  let result ← action
  let stop ← IO.monoMsNow
  IO.println s!"{name}: {stop - start}ms"
  pure result
```

### Comparing Implementations

```lean
def benchmark : IO Unit := do
  let large := List.range 1000000

  timeit "non-tail" do
    let _ := sum large  -- Might stack overflow
    pure ()

  timeit "tail-recursive" do
    let _ := sumTR large
    pure ()
```

---

## Common Optimizations

| Technique | When to Apply |
|-----------|---------------|
| Tail recursion | Deep recursion, large lists |
| Array instead of List | Random access needed |
| ForIn loops | Iteration with mutation |
| Inline small functions | Hot paths |
| Avoid intermediate structures | Chained transformations |
| Use Fin | Bounds-checked indexing |

---

## Compiler Annotations

```lean
-- Inline always
@[inline] def small (x : Nat) := x + 1

-- Specialize for type parameters
@[specialize] def generic [Add α] (x y : α) := x + y

-- Compiler hints
@[noinline] def large (x : Nat) := ...
```

---

## Sources

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
- [Performance chapter](https://lean-lang.org/functional_programming_in_lean/programs-proofs/tail-recursion.html)
