# Lean 4 Tactic Selection Deep Dive

Extended reference for tactic decision-making and proof strategies.

---

## Goal-Driven Selection

### By Goal Structure

```
Goal: a = b
├─ Definitionally equal (computes to same)? → rfl
├─ Have hypothesis h : a = b? → exact h
├─ Have h : c = d where c/d appear in goal? → rw [h]
├─ Complex arithmetic? → omega, ring, linarith
└─ Need chain of equalities? → calc

Goal: P ∧ Q
├─ Have hp : P and hq : Q? → exact ⟨hp, hq⟩
└─ Need to prove each separately? → constructor

Goal: P ∨ Q
├─ Can prove P? → left; prove P
├─ Can prove Q? → right; prove Q
└─ Building from h : P ∨ Q? → cases h

Goal: P → Q
└─ Always: intro hp (get hp : P, prove Q)

Goal: ¬P (which is P → False)
└─ intro hp (get hp : P, prove False)

Goal: ∀ x, P x
└─ intro x (get x, prove P x)

Goal: ∃ x, P x
└─ use witness (then prove P witness)

Goal: True
└─ trivial
```

---

## Hypothesis-Driven Selection

### By Hypothesis Structure

```
Hypothesis h : P ∧ Q
├─ Need P? → h.left or obtain ⟨hp, hq⟩ := h
└─ Need Q? → h.right

Hypothesis h : P ∨ Q
└─ cases h with | inl hp => ... | inr hq => ...

Hypothesis h : P → Q and hp : P
└─ h hp gives Q

Hypothesis h : ∀ x, P x
└─ h t gives P t for specific t

Hypothesis h : ∃ x, P x
└─ obtain ⟨w, hw⟩ := h

Hypothesis h : False
└─ exact h.elim or contradiction

Hypothesis h : a = b
├─ Substitute in goal → rw [h]
├─ Substitute in hypothesis → rw [h] at hp
└─ Use for subst → h ▸ term
```

---

## Automation Tactics Decision

| Situation | Tactic |
|-----------|--------|
| Linear arithmetic (Nat/Int) | `omega` |
| Ring operations | `ring` |
| Linear inequalities | `linarith` |
| Boolean/finite decidable | `decide` |
| With simp lemmas | `simp` |
| Simplify everything | `simp_all` |
| Any combination | `aesop` |

---

## rw vs simp vs conv

### rw (Rewrite)

```lean
-- Single substitution, leftmost match
rw [h]           -- Left to right
rw [← h]         -- Right to left
rw [h1, h2, h3]  -- Chain
rw [h] at hyp    -- In hypothesis
```

**Use when**: Specific, targeted substitution.

### simp (Simplify)

```lean
simp              -- Use @[simp] lemmas
simp [h1, h2]     -- Add extra lemmas
simp only [h1]    -- ONLY these lemmas
simp [-lemma]     -- Exclude lemma
simp [*]          -- Include all hypotheses
simp_all          -- Simplify goal AND hypotheses
```

**Use when**: Want aggressive simplification.

### conv (Conversion)

```lean
conv =>
  lhs            -- Focus left side of equality
  rhs            -- Focus right side
  arg 1          -- Focus first argument
  enter [1, 2]   -- Path into expression
  rw [h]         -- Rewrite at focus
```

**Use when**: Need precise control over WHERE to rewrite.

---

## Proof Structure Tactics

### Forward Reasoning

```lean
have h : T := proof       -- Introduce fact
let x := value            -- Local definition
suffices h : S by tac     -- Prove S → Goal first
```

### Backward Reasoning

```lean
apply lemma              -- Match goal with lemma conclusion
refine ⟨?_, ?_⟩         -- Partial construction
exact term               -- Complete proof term
```

---

## Case Analysis Tactics

### cases

```lean
cases h with
| constructor1 args => ...
| constructor2 args => ...
```

**Use for**: Inductive types, Or, Option, etc.

### rcases (Recursive cases)

```lean
rcases h with ⟨a, b⟩       -- And pattern
rcases h with ha | hb      -- Or pattern
rcases h with ⟨a, ⟨b, c⟩⟩  -- Nested
```

### obtain

```lean
obtain ⟨w, hw⟩ := h  -- Destructure existential
```

### by_cases

```lean
by_cases hp : P
· -- hp : P branch
· -- hp : ¬P branch
```

**Use for**: Classical case split on any Prop.

---

## Induction Tactics

### Basic Induction

```lean
induction n with
| zero => ...
| succ m ih => ...
```

### Strong Induction

```lean
induction n using Nat.strongInductionOn with
| _ n ih => ...
```

### Generalization

```lean
induction n generalizing m with ...
```

---

## Debugging and Navigation

### See Current State

```lean
trace "{msg}"          -- Print message
show T                 -- Clarify goal type
change T               -- Rewrite goal to definitionally equal T
```

### Focus Management

```lean
· tac                  -- Focus first goal
next => tac            -- Alternative focus
all_goals tac          -- Apply to all goals
any_goals tac          -- Apply to at least one
```

---

## Common Mistake Patterns

### "unknown identifier"
**Cause**: Typo or hypothesis not in scope
**Fix**: Check hypothesis names, ensure intro was called

### "type mismatch"
**Cause**: Term doesn't match expected type
**Fix**: Check types with `#check`, may need cast or different approach

### "failed to synthesize instance"
**Cause**: Missing type class instance
**Fix**: Add `[Instance]` parameter or derive instance

### "tactic 'assumption' failed"
**Cause**: No hypothesis matches goal
**Fix**: Use `exact h` with specific hypothesis

### "goals still remain"
**Cause**: Incomplete proof
**Fix**: Check all branches are covered, use `sorry` to find gaps

---

## Tactic Combinator Reference

| Combinator | Effect |
|------------|--------|
| `tac1 <;> tac2` | Apply tac2 to all goals from tac1 |
| `tac1; tac2` | Sequence |
| `first \| t1 \| t2` | Try t1, then t2 |
| `try tac` | Apply tac, never fail |
| `repeat tac` | Apply until failure |

---

## Sources

- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
- [Mathlib Tactics](https://leanprover-community.github.io/mathlib4_docs/)
