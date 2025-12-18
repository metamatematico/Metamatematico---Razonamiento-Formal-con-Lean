# Lean Soundness Summary for AI Mathematician Proposal

**Quick Reference Document**
**Date**: 2025-12-17

---

## The Bottom Line

**Question**: Is it true that if a proof compiles in Lean, it is valid?

**Answer**: **YES, with qualifications**. A type-checked proof is valid relative to:
1. Lean's trusted computing base (kernel + axioms)
2. Exclusion of `sorry` and unsafe user axioms
3. Acceptance of Classical logic

---

## For Section 1.1 of the Proposal

### Current Claim
> "The Lean 4 type checker serves as a verification oracle: a proof term is valid if and only if it type-checks—that is, if the term inhabits the corresponding type."

### Status: ACCURATE ✅

This claim is fundamentally correct for the research proposal's purposes.

### Optional Precision Enhancement

If you want to be maximally precise, consider this revision:

> "The Lean 4 type checker serves as a verification oracle: a proof term is valid if and only if it type-checks (inhabits the corresponding type), excluding intentional holes (`sorry`) and unsound user axioms. Soundness is guaranteed relative to a small trusted computing base and Lean's equiconsistency with ZFC + countably many inaccessible cardinals (Carneiro 2019)."

**Or, more concisely**:

> "The Lean 4 type checker serves as a verification oracle: a proof term is valid if and only if it type-checks, modulo a small trusted base (kernel, core axioms, metatheory)."

---

## Key Technical Facts

### What Type-Checking Guarantees

When a term `t : P` type-checks in Lean's kernel:
- ✅ Valid derivation in Lean's type theory (CIC + extensions)
- ✅ All inference rules followed correctly
- ✅ Sound relative to ZFC + ω inaccessible cardinals
- ✅ Axiom dependencies tracked (`#print axioms`)

### What You Must Trust

1. **Kernel Implementation**: ~10K lines of C++ (being verified by Lean4Lean project)
2. **Core Axioms**:
   - `Classical.choice` (enables excluded middle, non-constructive)
   - `Quot.sound` (quotient types)
   - `propext` (propositional extensionality)
   - `funext` (function extensionality)
3. **Metatheory**: ZFC + countably many inaccessible cardinals (Carneiro 2019)

### What Breaks Soundness

- ❌ `sorry` - produces terms of any type (intentional holes)
- ❌ `axiom my_false : False` - user-added inconsistent axioms
- ❌ `unsafe` code in proof path (should be tracked)

**Detection**: All tracked by `#print axioms` command

---

## Soundness Track Record

| Lean Version | Soundness Bugs | Status |
|--------------|----------------|--------|
| **Lean 3** | Zero (spotless record) | Stable |
| **Lean 4** | Several (being fixed) | Active development + verification |

**Recent Lean 4 Issues**:
- `Nat.pow` reduction bug (fixed in 4.20.0)
- `reduceBool` axiom tracking (ongoing)
- `@[csimp]` can smuggle unsafe code (being addressed)

**Mitigation**: Lean4Lean project (Carneiro 2024) is building a verified type-checker in Lean, already finding and fixing bugs.

---

## Comparison with Other Proof Assistants

| System | Foundation | Soundness Guarantee | Verification Status |
|--------|------------|---------------------|---------------------|
| **Lean 4** | CIC + impredicative Prop | ZFC + ω inaccessibles | In progress (Lean4Lean) |
| **Coq** | pCIC (predicative) | Similar to Lean | In progress (MetaCoq) |
| **Isabelle/HOL** | Classical HOL | Simpler metatheory | Partial |

**All three** use LCF-style kernels and have comparable trustworthiness.

---

## Recommendations for Your System

### 1. Automatic Axiom Auditing
```lean
#print axioms generated_theorem
-- Whitelist: [Classical.choice, Quot.sound, propext, funext]
-- Reject: [sorry, unexpected axioms]
```

### 2. Track Axiom Dependencies in Knowledge Graph
```
Theorem: First Isomorphism Theorem
├─ Status: Verified ✓
├─ Axioms: Classical.choice, Quot.sound
├─ Confidence: High
└─ Constructive: No (uses Classical.choice)
```

### 3. Distinguish Constructive vs Classical Proofs
- Proofs **without** `Classical.choice` → constructive, computable
- Proofs **with** `Classical.choice` → classical, may be non-computable

---

## Addressing Potential Concerns

### "Can Lean prove its own consistency?"

**No** (Gödel's Second Incompleteness Theorem). Soundness is relative:
- Carneiro proves: ZFC + ω inaccessibles ⊢ Con(Lean)
- Cannot prove without stronger assumptions
- **This is not a weakness**—same limitation applies to all formal systems

### "What about soundness bugs?"

- Lean 3: zero bugs (excellent record)
- Lean 4: some bugs, being systematically addressed
- Lean4Lean verification ongoing (already fixing issues)
- **Practical impact**: Extremely rare, quickly fixed when found

### "Is the kernel verified?"

- Kernel: ~10K LOC C++ (not yet fully verified)
- Lean4Lean: External verifier in Lean (20-50% slower, verifies all Mathlib)
- **Status**: Verification in progress, already productive

---

## Optional Footnote for Proposal

> **On Soundness Guarantees**: Lean's type checker provides soundness relative to its metatheory (ZFC + countably many inaccessible cardinals, proven by Carneiro 2019). The Lean4Lean project is formalizing a verified type-checker, addressing soundness issues in Lean 4's kernel. This provides comparable confidence to other widely-used proof assistants (Coq, Isabelle/HOL). Proofs are audited for dependencies on `sorry` (intentional holes) or unsafe axioms via the `#print axioms` command.

---

## Further Reading

**Essential**:
- [Lean4Lean Paper (Carneiro 2024)](https://arxiv.org/abs/2403.14064)
- [Lean 4 Docs: Axioms and Computation](https://lean-lang.org/theorem_proving_in_lean4/axioms_and_computation.html)

**Detailed Analysis**:
- See `/Users/lkronecker/.claude/context/research/lean-soundness-guarantees-2025-12-17-deep.md`

---

**Conclusion**: Your claim is accurate and can be used confidently. Lean provides a robust verification oracle for mathematical proofs, with guarantees comparable to other state-of-the-art proof assistants.
