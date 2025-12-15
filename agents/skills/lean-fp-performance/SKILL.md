---
name: lean-fp-performance
description: Tail recursion, array mutation, Fin, and performance patterns. Use when optimizing recursive functions, avoiding stack overflow, or working with large data.
allowed-tools: Read, Grep, Glob
---

# Lean 4 Performance Optimization

Tail recursion, array mutation, and performance patterns. Use when optimizing recursive functions, avoiding stack overflow, or working with large data.

**Trigger terms**: "tail recursion", "performance", "stack overflow", "array mutation", "optimization", "Fin"

---

## The Problem

Non-tail-recursive functions can overflow the stack:

```lean
-- ❌ Not tail recursive - builds up stack
def sum : List Nat → Nat
  | [] => 0
  | x :: xs => x + sum xs  -- + happens AFTER recursion
```

---

## Tail Recursion Pattern

Last action is the recursive call:

```lean
-- ✓ Tail recursive with accumulator
def sumTR (xs : List Nat) : Nat :=
  go xs 0
where
  go : List Nat → Nat → Nat
  | [], acc => acc
  | x :: xs, acc => go xs (acc + x)  -- recursion IS last action
```

**Pattern**: Move result-building into accumulator parameter.

---

## When Tail Recursion Matters

| List Size | Non-Tail | Tail |
|-----------|----------|------|
| 1,000 | OK | OK |
| 100,000 | Stack overflow | OK |
| 1,000,000 | Crash | OK |

**Use tail recursion when**: Processing large collections, performance-critical code.

---

## Converting to Tail Recursive

```lean
-- Original: result = f(recursive_result)
def length : List α → Nat
  | [] => 0
  | _ :: xs => 1 + length xs

-- Tail recursive: accumulate result
def lengthTR (xs : List α) : Nat :=
  go xs 0
where
  go : List α → Nat → Nat
  | [], n => n
  | _ :: xs, n => go xs (n + 1)
```

**Steps**:
1. Add accumulator parameter
2. Initialize accumulator to identity (0 for +, 1 for *, [] for ++)
3. Update accumulator instead of composing with result

---

## Array Mutation with Fin

Safe in-place updates:

```lean
-- Fin ensures index is valid
def Array.set (arr : Array α) (i : Fin arr.size) (v : α) : Array α

-- Safe swap
def swap (arr : Array α) (i j : Fin arr.size) : Array α :=
  let tmp := arr.get i
  let arr := arr.set i (arr.get j)
  arr.set j tmp
```

**Benefit**: No bounds check at runtime - proven at compile time!

---

## Proving Tail-Recursive Equivalence

```lean
-- Prove TR version equals simple version
theorem sum_eq_sumTR : sum xs = sumTR xs := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simp [sum, sumTR, sumTR.go, ih]
```

---

## Performance Patterns

| Pattern | When to Use |
|---------|-------------|
| Tail recursion | Large lists, deep recursion |
| Array + Fin | Random access, in-place updates |
| Lazy evaluation | Avoid computing unused values |
| Fusion | Avoid intermediate data structures |

---

## Common Mistakes

**Forgetting accumulator reversal**:
```lean
-- ❌ Result is reversed!
def mapTR (f : α → β) (xs : List α) : List β :=
  go xs []
where
  go : List α → List β → List β
  | [], acc => acc  -- Wrong order!
  | x :: xs, acc => go xs (f x :: acc)

-- ✓ Reverse at end (or use different structure)
def mapTR (f : α → β) (xs : List α) : List β :=
  (go xs []).reverse
where ...
```

**Non-tail position**:
```lean
-- ❌ + is after recursion
go xs (acc + x)  -- This IS tail (go is last)
x + go xs acc    -- This is NOT (+ is last)
```

---

## Checking Tail Recursion

```lean
-- Lean warns if function isn't tail recursive
-- when using `partial` or `termination_by`

-- Use #check to verify compiled form
```

---

## See Also

- `lean-fp-basics` - Recursion fundamentals
- `lean-fp-dependent-types` - Fin type
- `lean-tp-tactics` - Proving equivalence

**Source**: [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
