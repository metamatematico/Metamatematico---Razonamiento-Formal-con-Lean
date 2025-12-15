# Lean 4 Performance Examples

Working code examples demonstrating optimization patterns.

---

## Non-Tail vs Tail Recursive

```lean
-- ❌ Non-tail recursive: builds stack
def sum : List Nat → Nat
  | [] => 0
  | x :: xs => x + sum xs

-- ✓ Tail recursive: constant stack
def sumTR (xs : List Nat) : Nat :=
  go xs 0
where
  go : List Nat → Nat → Nat
  | [], acc => acc
  | x :: xs, acc => go xs (acc + x)

-- Test: sumTR handles millions, sum crashes
-- #eval sumTR (List.range 1000000)  -- Works
-- #eval sum (List.range 1000000)    -- Stack overflow
```

---

## Common Functions - Tail Recursive

```lean
-- Length
def lengthTR {α : Type} (xs : List α) : Nat :=
  go xs 0
where
  go : List α → Nat → Nat
  | [], n => n
  | _ :: xs, n => go xs (n + 1)

-- Reverse
def reverseTR {α : Type} (xs : List α) : List α :=
  go xs []
where
  go : List α → List α → List α
  | [], acc => acc
  | x :: xs, acc => go xs (x :: acc)

-- Map (note: builds result reversed, must reverse at end)
def mapTR {α β : Type} (f : α → β) (xs : List α) : List β :=
  go xs [] |>.reverseTR
where
  go : List α → List β → List β
  | [], acc => acc
  | x :: xs, acc => go xs (f x :: acc)

-- Filter
def filterTR {α : Type} (p : α → Bool) (xs : List α) : List α :=
  go xs [] |>.reverseTR
where
  go : List α → List α → List α
  | [], acc => acc
  | x :: xs, acc => if p x then go xs (x :: acc) else go xs acc
```

---

## Factorial - Tail Recursive

```lean
-- ❌ Not tail recursive
def factorial : Nat → Nat
  | 0 => 1
  | n + 1 => (n + 1) * factorial n

-- ✓ Tail recursive
def factorialTR (n : Nat) : Nat :=
  go n 1
where
  go : Nat → Nat → Nat
  | 0, acc => acc
  | n + 1, acc => go n ((n + 1) * acc)

#eval factorialTR 20  -- 2432902008176640000
```

---

## Fibonacci - Tail Recursive

```lean
-- ❌ Exponential time (not tail recursive AND recomputes)
def fib : Nat → Nat
  | 0 => 0
  | 1 => 1
  | n + 2 => fib n + fib (n + 1)

-- ✓ Linear time, tail recursive
def fibTR (n : Nat) : Nat :=
  go n 0 1
where
  go : Nat → Nat → Nat → Nat
  | 0, a, _ => a
  | n + 1, a, b => go n b (a + b)

#eval fibTR 50  -- 12586269025
-- #eval fib 50  -- Would take forever
```

---

## Array with Fin

```lean
-- Safe indexing with Fin - no runtime bounds check
def sumArray (arr : Array Nat) : Nat := Id.run do
  let mut sum := 0
  for i in [:arr.size] do
    let idx : Fin arr.size := ⟨i, by omega⟩
    sum := sum + arr.get idx
  pure sum

-- In-place array modification
def doubleArray (arr : Array Nat) : Array Nat := Id.run do
  let mut arr := arr
  for i in [:arr.size] do
    arr := arr.set ⟨i, by omega⟩ (arr[i]! * 2)
  pure arr

#eval doubleArray #[1, 2, 3, 4, 5]  -- #[2, 4, 6, 8, 10]
```

---

## Array Swap and Sort

```lean
-- Swap two elements
def swap (arr : Array α) (i j : Fin arr.size) : Array α :=
  let tmp := arr.get i
  let arr := arr.set i (arr.get j)
  arr.set j tmp

-- Simple bubble sort (in-place when array is unique)
def bubbleSort (arr : Array Nat) : Array Nat := Id.run do
  let mut arr := arr
  for i in [:arr.size] do
    for j in [:arr.size - 1 - i] do
      if h : j + 1 < arr.size then
        let jFin : Fin arr.size := ⟨j, Nat.lt_of_lt_of_le (Nat.lt_succ_self j) (Nat.le_of_lt h)⟩
        let j1Fin : Fin arr.size := ⟨j + 1, h⟩
        if arr.get jFin > arr.get j1Fin then
          arr := swap arr jFin j1Fin
  pure arr

#eval bubbleSort #[5, 2, 8, 1, 9]  -- #[1, 2, 5, 8, 9]
```

---

## ForIn Loop Patterns

```lean
-- Count matching elements
def count (p : α → Bool) (xs : Array α) : Nat := Id.run do
  let mut n := 0
  for x in xs do
    if p x then n := n + 1
  pure n

-- Find first matching
def findFirst (p : α → Bool) (xs : Array α) : Option α := Id.run do
  for x in xs do
    if p x then return some x
  pure none

-- All satisfy predicate
def all (p : α → Bool) (xs : Array α) : Bool := Id.run do
  for x in xs do
    if !p x then return false
  pure true

#eval count (· > 3) #[1, 2, 3, 4, 5]  -- 2
#eval findFirst (· > 3) #[1, 2, 3, 4, 5]  -- some 4
#eval all (· > 0) #[1, 2, 3]  -- true
```

---

## Proving Tail-Recursive Equivalence

```lean
-- Prove implementations are equivalent
theorem sum_eq_sumTR (xs : List Nat) : sum xs = sumTR xs := by
  unfold sumTR
  have h : ∀ acc, sum xs + acc = sumTR.go xs acc := by
    induction xs with
    | nil => simp [sum, sumTR.go]
    | cons x xs ih =>
      intro acc
      simp [sum, sumTR.go]
      rw [Nat.add_assoc, Nat.add_comm x acc, ← Nat.add_assoc]
      exact ih (acc + x)
  have := h 0
  simp at this
  exact this
```

---

## Avoiding Intermediate Allocations

```lean
-- ❌ Creates intermediate list
def sumSquaresEven (xs : List Nat) : Nat :=
  xs.filter (· % 2 == 0) |>.map (· ^ 2) |>.foldl (· + ·) 0

-- ✓ Single pass, no intermediate allocations
def sumSquaresEvenFused (xs : List Nat) : Nat :=
  go xs 0
where
  go : List Nat → Nat → Nat
  | [], acc => acc
  | x :: xs, acc =>
    if x % 2 == 0 then go xs (acc + x ^ 2)
    else go xs acc

-- Even better with ForIn
def sumSquaresEvenFor (xs : Array Nat) : Nat := Id.run do
  let mut sum := 0
  for x in xs do
    if x % 2 == 0 then sum := sum + x ^ 2
  pure sum
```

---

## Lazy Evaluation Pattern

```lean
-- Lazy list using thunks
inductive LazyList (α : Type) where
  | nil
  | cons : α → Thunk (LazyList α) → LazyList α

-- Infinite sequence
def nats : Nat → LazyList Nat
  | n => .cons n ⟨fun () => nats (n + 1)⟩

-- Take only what's needed
def LazyList.take : Nat → LazyList α → List α
  | 0, _ => []
  | _, .nil => []
  | n + 1, .cons x xs => x :: take n xs.get

#eval (nats 0).take 10  -- [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

---

## Termination Proofs

```lean
-- Division needs termination proof
def div (n k : Nat) : Nat :=
  if h : k > 0 ∧ n ≥ k then
    1 + div (n - k) k
  else
    0
termination_by n

-- GCD with termination
def gcd (a b : Nat) : Nat :=
  if b = 0 then a
  else gcd b (a % b)
termination_by b
decreasing_by
  simp_wf
  exact Nat.mod_lt a (Nat.pos_of_ne_zero ‹b ≠ 0›)

#eval gcd 48 18  -- 6
```

---

## Sources

- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
