---
name: lean-tp-tactic-selection
description: Decision trees for choosing tactics based on goal type and proof strategy. Use when unsure which tactic to apply or planning proof approach.
allowed-tools: Read, Grep, Glob
---

# Lean 4 Tactic Selection

Decision trees for choosing the right tactic based on goal type and proof strategy. Use when unsure which tactic to apply.

**Trigger terms**: "which tactic", "tactic choice", "proof strategy", "how to prove", "tactic decision"

---

## Tactic Selection by Goal Type

```
Goal type?
├─ a = b (equality)
│  ├─ Definitional equality? → rfl
│  ├─ Have proof h : a = b? → exact h
│  ├─ Need rewriting? → rw [lemmas]
│  └─ Complex chain? → calc
│
├─ p ∧ q (conjunction)
│  ├─ Have both proofs? → exact ⟨hp, hq⟩
│  └─ Need to derive each? → constructor
│
├─ p ∨ q (disjunction)
│  ├─ Have p? → left; exact hp
│  ├─ Have q? → right; exact hq
│  └─ Case split on h : p ∨ q? → cases h
│
├─ p → q (implication)
│  └─ Introduce assumption → intro hp
│
├─ ∀ x, p x (universal)
│  └─ Introduce variable → intro x
│
├─ ∃ x, p x (existential)
│  └─ Provide witness → use w
│
├─ ¬p (negation = p → False)
│  └─ Introduce and derive False → intro hp
│
├─ Inductive type
│  ├─ Single constructor? → constructor
│  ├─ Multiple constructors? → cases h
│  └─ Recursive proof? → induction h
│
├─ Contradictory hypotheses?
│  └─ contradiction
│
├─ Goal is in context?
│  └─ assumption
│
└─ Complex expression?
   └─ simp / simp_all
```

---

## Proof Strategy Decision Tree

```
What's your approach?
├─ Direct construction
│  └─ exact <term> / apply <lemma>
│
├─ Case analysis
│  ├─ On hypothesis h : P ∨ Q → cases h
│  └─ On decidable prop → by_cases h : P
│
├─ Induction
│  └─ induction n with | base => ... | step ih => ...
│
├─ Rewriting
│  ├─ Simple substitution → rw [h]
│  ├─ Repeated/normalized → simp
│  └─ Precise location → conv
│
├─ Backward reasoning ("suffices to show X")
│  └─ suffices h : X by use_h; prove_X
│
├─ Forward reasoning ("we have X")
│  └─ have h : X := proof
│
├─ Contradiction
│  └─ exfalso / contradiction
│
└─ Classical (excluded middle)
   └─ by_cases h : P
```

---

## Quick Decision Table

| Situation | Tactic |
|-----------|--------|
| Goal exactly matches hypothesis | `assumption` or `exact h` |
| Goal is `a = a` or computes to equality | `rfl` |
| Goal is `True` | `trivial` |
| Goal is conjunction `P ∧ Q` | `constructor` |
| Goal is disjunction, have left | `left` |
| Goal is disjunction, have right | `right` |
| Goal is implication/universal | `intro` |
| Goal is existential | `use witness` |
| Have equality, need to substitute | `rw [h]` |
| Complex arithmetic | `omega` |
| Decidable by computation | `decide` |
| Need to case split | `cases h` |
| Need induction | `induction n` |
| Hypotheses contradict | `contradiction` |
| Simplify with lemmas | `simp [lemmas]` |

---

## When rw vs simp vs conv

| Use | When |
|-----|------|
| `rw [h]` | Single specific rewrite, leftmost match |
| `rw [← h]` | Rewrite right-to-left |
| `simp` | Apply all @[simp] lemmas to simplify |
| `simp [h]` | Include h as additional simp lemma |
| `simp only [h]` | Use ONLY specified lemmas |
| `conv => ...` | Precise control over WHERE to rewrite |

---

## Common Tactic Errors

**"unknown identifier"**: Hypothesis name typo or not in scope
**"type mismatch"**: Term doesn't match goal type
**"tactic 'assumption' failed"**: No matching hypothesis
**"goals remain"**: Forgot to prove all cases

---

## See Also

- `lean-tp-tactics` - Detailed tactic reference
- `lean-tp-propositions` - Logical connectives
- `lean-tp-foundations` - Type theory

**Source**: [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
