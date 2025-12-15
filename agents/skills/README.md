# Lean Skills

Claude Code skill definitions for Lean 4 development. These skills are loaded dynamically by the `proof-engineer` agent based on error patterns and proof requirements.

## Categories

### Functional Programming (lean-fp-*)

| Skill | Purpose |
|-------|---------|
| `lean-fp-basics` | Lean 4 fundamentals: syntax, structures, inductive types, polymorphism |
| `lean-fp-dependent-types` | Vect, Fin, indexed families, universes, type-safe APIs |
| `lean-fp-functor-applicative` | Functor, Applicative, Alternative classes |
| `lean-fp-monads` | Option, Except, State, Reader, do-notation |
| `lean-fp-performance` | Tail recursion, array mutation, optimization patterns |
| `lean-fp-transformers` | StateT, ExceptT, ReaderT, combining effects |
| `lean-fp-type-classes` | Ad-hoc polymorphism, instances, deriving, coercions |

### Theorem Proving (lean-tp-*)

| Skill | Purpose |
|-------|---------|
| `lean-tp-foundations` | Dependent type theory, universes, Type/Prop, CIC |
| `lean-tp-tactics` | Core tactics: apply, exact, intro, rw, simp, cases, induction |
| `lean-tp-advanced` | Axioms, classical logic, quotients, noncomputable definitions |
| `lean-tp-propositions` | Logical connectives: →, ∧, ∨, ¬, ↔ |
| `lean-tp-quantifiers` | Universal (∀) and existential (∃) quantification |
| `lean-tp-tactic-selection` | Decision trees for choosing tactics based on goal structure |

### Reference

| Skill | Purpose |
|-------|---------|
| `lean-quick-reference` | Consolidated cheatsheets for syntax, tactics, type classes |

## Skill Structure

Each skill directory contains:

```
lean-<category>-<name>/
├── SKILL.md        # Metadata (name, description, allowed-tools)
├── reference.md    # Technical content
└── examples.md     # Code examples (most skills)
```

### SKILL.md Format

```yaml
---
name: lean-tp-tactics
description: Core tactics for theorem proving...
allowed-tools: Read, Grep, Glob
---
```

## Installation

To use with Claude Code, copy to your global config:

```bash
cp -r skills/lean-* ~/.claude/skills/
```

## Sync Workflow

1. Edit skill definitions in this repo
2. Submit PR for review
3. After merge, copy to `~/.claude/skills/`

## Dynamic Loading

The `proof-engineer` agent loads skills based on error patterns:

| Error Pattern | Skills Loaded |
|---------------|---------------|
| Type mismatch | `lean-tp-foundations`, `lean-fp-type-classes` |
| Unknown tactic | `lean-tp-tactics`, `lean-tp-tactic-selection` |
| Failed to synthesize | `lean-fp-type-classes` |
| Universe issues | `lean-tp-foundations`, `lean-tp-advanced` |
| Proof stuck | `lean-tp-propositions`, `lean-tp-quantifiers` |

## Related

- [`proof-engineer.md`](../proof-engineer.md) - Agent that uses these skills
- [Mathlib4 Documentation](https://leanprover-community.github.io/mathlib4_docs/)
- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
