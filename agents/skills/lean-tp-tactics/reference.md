# Lean 4 Tactics Deep Dive

Extended reference for tactic mode mechanics and advanced patterns.

---

## Tactic Mode Architecture

### How Tactics Work

Tactics manipulate a **proof state** consisting of:
- **Goals**: What remains to prove (type)
- **Context**: Available hypotheses and their types
- **Metavariables**: Placeholders in incomplete proofs

Each tactic transforms the proof state:
```
Before: ⊢ P ∧ Q
After `constructor`: ⊢ P  and  ⊢ Q  (two goals)
```

### Goal Management

| Command | Effect |
|---------|--------|
| `· tactic` | Focus first goal |
| `next => tactic` | Same, alternative syntax |
| `all_goals tactic` | Apply to all goals |
| `any_goals tactic` | Apply to at least one |
| `first \| t1 \| t2` | Try t1, fallback to t2 |
| `repeat tactic` | Apply until failure |
| `try tactic` | Never fail (no-op if fails) |

---

## Tactic Combinators

### Sequential Composition

```lean
-- Semicolon: run on all generated goals
example (hp : p) (hq : q) : p ∧ q := by
  constructor; exact hp; exact hq

-- <;> : apply tactic to ALL goals from previous
example (h : p ∧ q) : q ∧ p := by
  constructor <;> (cases h; assumption)
```

### Conditional Tactics

```lean
-- first: try alternatives
example (n : Nat) : n = n := by
  first | rfl | simp

-- try: never fail
example : True := by
  try contradiction  -- Silently fails
  trivial
```

---

## Advanced Rewriting

### rw Mechanics

`rw [h]` rewrites left-to-right at **leftmost** occurrence in goal:

```lean
-- Only rewrites first occurrence
example (h : a = b) : a + a = b + b := by
  rw [h]     -- a + a → b + a
  rw [h]     -- b + a → b + b

-- Or specify location
example (h : a = b) : a + a = b + b := by
  rw [h, h]  -- Chains both
```

### simp Internals

`simp` applies a term rewriting system:

1. Collects lemmas from `@[simp]` database
2. Adds explicit lemmas from `simp [lemmas]`
3. Rewrites until fixed point
4. May unfold definitions tagged `@[simp]`

**Controlling simp**:
```lean
simp only [h1, h2]    -- ONLY these lemmas
simp [-nat_add]       -- Exclude specific lemma
simp [*]              -- Include all hypotheses
simp_all              -- Also simplify hypotheses
```

### conv Mode

Precise control over rewrite location:

```lean
example (h : a = b) : (a + c) + a = (a + c) + b := by
  conv =>
    lhs           -- Focus left-hand side
    rhs           -- Focus right argument of +
    rw [h]        -- Rewrite only there
```

**conv tactics**:
| Tactic | Effect |
|--------|--------|
| `lhs`/`rhs` | Focus left/right of relation |
| `arg i` | Focus i-th argument |
| `enter [1, 2]` | Path navigation |
| `ext x` | Introduce binder |
| `rw [h]` | Rewrite at focus |
| `simp` | Simplify at focus |

---

## Structural Tactics

### cases vs rcases vs obtain

```lean
-- cases: basic case split
cases h with
| inl hp => ...
| inr hq => ...

-- rcases: recursive with pattern
rcases h with ⟨a, ⟨b, c⟩⟩ | d

-- obtain: extract witness
obtain ⟨w, hw⟩ := existential_hyp
```

### Pattern Syntax (rcases/obtain)

| Pattern | Matches |
|---------|---------|
| `⟨a, b⟩` | Constructor with 2 args |
| `⟨a, b, c⟩` | 3 args |
| `a \| b` | Sum type alternative |
| `⟨⟩` | Unit/trivial |
| `-` | Discard |
| `rfl` | Equality proof (substitutes) |

---

## Induction Patterns

### Custom Induction

```lean
-- Named cases
induction n with
| zero => trivial
| succ m ih => simp [ih]

-- Pattern matching style
induction n
case zero => trivial
case succ m ih => simp [ih]
```

### Strong Induction

```lean
-- Using well-founded recursion
theorem div_add_mod (n k : Nat) : (n / k) * k + n % k = n := by
  induction n using Nat.strongInductionOn with
  | _ n ih => ...
```

### Generalization

```lean
-- Generalize before induction
example (m n : Nat) : m + n = n + m := by
  induction n generalizing m with
  | zero => simp
  | succ n ih => simp [Nat.add_succ, ih]
```

---

## Hypothesis Management

### Introducing and Reverting

```lean
intro x            -- Move ∀/→ binder to context
intros             -- Introduce all
revert x           -- Move back to goal
clear h            -- Remove hypothesis
rename h => h'     -- Rename hypothesis
```

### Specializing Hypotheses

```lean
have h' := h 5     -- Specialize ∀ to specific value
specialize h 5     -- In place specialization
```

### Obtaining New Facts

```lean
have h : P := proof       -- Add hypothesis
let x : T := value        -- Local definition
suffices h : Q by ...     -- Backward reasoning
```

---

## Automation Tactics

### decide

For decidable propositions (computable):
```lean
example : 2 + 2 = 4 := by decide
example : ¬(3 < 2) := by decide
```

### omega

Linear arithmetic over integers/naturals:
```lean
example (x y : Nat) (h : x < y) : x ≤ y := by omega
example (x : Int) (h : x > 0) : x ≥ 1 := by omega
```

### native_decide

Kernel-bypassing decision:
```lean
-- For expensive but decidable computations
example : isPrime 104729 := by native_decide
```

---

## Debugging Tactics

| Command | Purpose |
|---------|---------|
| `trace "{msg}"` | Print message |
| `dbg_trace "{msg}"` | Debug trace |
| `sorry` | Admit goal (leaves hole) |
| `admit` | Same as sorry |

---

## Sources

- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
- [Mathlib Tactics Documentation](https://leanprover-community.github.io/mathlib4_docs/)
