# Mathematical Research System - Operational Workflows

> **Document Status**: Vision/Roadmap
> **Last Updated**: 2025-12-14

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Agents** | | |
| Proof Engineer | ✅ Implemented | See [`proof-engineer.md`](./proof-engineer.md) |
| Conjecture Engineer | 🔮 Planned | Pattern discovery agent |
| Reviewer | 🔮 Planned | Quality assurance agent |
| **Workflows** | | |
| 1. Theorem Proving | ⚡ Partial | Proof Eng (+ optional Reviewer) |
| 2. Proof Checking | 🔮 Planned | Reviewer (+ optional Proof Eng) |
| 3. Conjecture Validation | 🔮 Planned | Conj Eng + Reviewer |
| 4. Research & Discovery | 🔮 Planned | All 3 agents |
| 5. Hybrid Modes | 🔮 Planned | Various combinations |
| **Skills** | | |
| Lean TP/FP Skills | ✅ Implemented | 14 skills in [`skills/`](./skills/) |
| Pattern-finding | 🔮 Planned | For conjecture-engineer |
| Quality-assessment | 🔮 Planned | For reviewer |

**Legend**: ✅ Implemented | ⚡ Partial | 🔮 Planned

---

## Overview

The mathematical research system supports multiple operational workflows, each utilizing different combinations of the three core agents (Conjecture Engineer, Proof Engineer, Reviewer). This document describes each workflow, when to use it, and how to invoke it.

---

## Core Agents Reference

### Conjecture Engineer 🔮
- **Skills**: pattern-finding, hypothesis-formation
- **Purpose**: Discover patterns and formulate conjectures
- **Uses shared**: computational-verification, mathematical-notation

### Proof Engineer ✅
- **Skills**: proof-construction, proof-analysis
- **Purpose**: Attempt proofs and diagnose barriers
- **Uses shared**: theorem-library, mathematical-notation

### Reviewer 🔮
- **Skills**: quick-review, conjecture-critique, proof-critique, process-evaluation
- **Purpose**: Quality assurance and process optimization
- **Uses shared**: computational-verification, quality-assessment

---

## Workflow 1: Theorem Proving Mode ⚡

> **Status**: Partially available via `proof-engineer`

### When to Use
- Have a specific theorem to prove
- Statement is already well-formed
- Want focused proof attempt without pattern discovery
- Checking if known conjecture is provable

### Agents Involved
**Proof Engineer** (primary) + **Reviewer** (optional, 🔮 planned)

### Process Flow
```
You → Claude Code
    ↓ "Prove: [formal statement]"

Proof Engineer:
  1. Parse and understand statement
  2. Select proof techniques
  3. Attempt proof
  4. If fails: diagnose barrier
  5. Establish partial results if possible

Reviewer (optional, 🔮):
  6. Critique proof quality
  7. Verify logical soundness
  8. Identify gaps

Output:
  → Proof (if successful)
  → Partial result + barrier (if blocked)
  → Techniques attempted
  → Recommendations
```

### Command Syntax

```bash
# Direct theorem proving
prove "For all n > 2, there exist primes p, q such that n = p + q" \
  --known-as "Goldbach's Conjecture" \
  --domain number_theory \
  --techniques sieve,circle_method,analytic \
  --time-budget 10m

# With context
prove "If G is a connected planar graph, then χ(G) ≤ 4" \
  --known-as "Four Color Theorem" \
  --given-context "Graph is planar and connected" \
  --require-constructive-proof

# Explore proof techniques
prove "[statement]" \
  --explore-techniques \
  --report-all-attempts \
  --identify-barriers
```

### Example Session

**Input:**
```
prove "Every even integer greater than 2 can be expressed as the sum
of two primes" --known-as "Goldbach's Conjecture"
```

**Process:**
```
Proof Engineer:

Attempt 1: Hardy-Littlewood Circle Method
  → Got asymptotic formula
  → Cannot prove existence (only counts)
  → Status: Partial insight

Attempt 2: Sieve Methods
  → Can handle "almost all" cases
  → Cannot prove for ALL cases
  → Status: Partial result

Attempt 3: Probabilistic Heuristics
  → Suggests truth with high probability
  → Not rigorous proof
  → Status: Heuristic only

Diagnosis:
  Barrier: Additive vs. Multiplicative structure gap
  What's needed: Better control of primes in short intervals
  Related: Distribution in arithmetic progressions (open problem)
```

**Output:**
```
Status: BARRIER IDENTIFIED

Cannot prove with current techniques.

Partial Results:
  ✓ Weak Goldbach (odd numbers): PROVEN
  ✓ Computational verification: up to 4×10^18
  ✓ Conditional result: IF Riemann Hypothesis THEN true
  ✓ Almost all: True for all but o(N) numbers

Barrier: Core issue is additive problem structure vs.
         multiplicative nature of primes

Recommendation: Conjecture remains open. Best achievable
                with current techniques is "almost all" result.
```

### Output Artifacts
- `proof-attempt.md` - Full proof or partial result
- `techniques-tried.json` - What was attempted
- `barrier-analysis.md` - Why proof failed
- `partial-results.md` - What was achieved
- `recommendations.md` - Next steps

---

## Workflow 2: Proof Checking Mode 🔮

### When to Use
- Have an existing proof to verify
- Want to check proof from literature
- Student proof grading
- Verify your own proof before publication

### Agents Involved
**Reviewer** (primary) + **Proof Engineer** (optional for gap filling)

### Process Flow
```
You → Claude Code
    ↓ "Check proof: [proof text or file]"

Reviewer:
  1. Parse proof structure
  2. Verify logical flow
  3. Check each step justification
  4. Identify gaps or errors
  5. Assess rigor

Proof Engineer (if gaps found):
  6. Attempt to fill gaps
  7. Suggest corrections

Output:
  → Correctness assessment
  → Gap identification
  → Error detection
  → Suggested fixes
```

### Command Syntax

```bash
# Check a proof file
check-proof proofs/my_theorem.md \
  --verify-logic \
  --identify-gaps \
  --assess-rigor

# Check with gap filling
check-proof proofs/draft_proof.md \
  --fill-gaps \
  --suggest-corrections

# Quick correctness check
check-proof "[proof text]" \
  --quick-check \
  --output correctness_score
```

### Example Session

**Input:**
```
check-proof "Theorem: √2 is irrational
Proof: Assume √2 = p/q where gcd(p,q) = 1.
Then 2 = p²/q², so 2q² = p².
Therefore p² is even, so p is even.
Let p = 2k. Then 2q² = 4k², so q² = 2k².
Therefore q is even.
But this contradicts gcd(p,q) = 1. QED"
```

**Process:**
```
Reviewer:

Structure Analysis:
  ✓ Uses proof by contradiction
  ✓ Clear assumption stated
  ✓ Logical flow is present

Step-by-Step Verification:
  Step 1: "2q² = p²" ✓ Correct algebra
  Step 2: "p² even → p even" ✓ Valid (needs lemma)
  Step 3: "p = 2k" ✓ Definition of even
  Step 4: "q² = 2k²" ✓ Correct algebra
  Step 5: "q² even → q even" ✓ Valid (same lemma)
  Step 6: "Contradiction" ✓ Valid conclusion

Gap Analysis:
  ⚠ Missing: Proof that "n² even → n even"
  → This requires justification

Rigor Assessment:
  Overall: 8/10
  Gap: Minor (easily filled)
  Correctness: Valid modulo gap
```

**Output:**
```
Proof Status: CORRECT (with minor gap)

The proof is logically sound but requires one additional lemma:

MISSING LEMMA: If n² is even, then n is even.

Proof of lemma:
  Contrapositive: If n is odd, then n² is odd.
  If n = 2k+1, then n² = 4k² + 4k + 1 = 2(2k² + 2k) + 1
  Therefore n² is odd. QED.

With this lemma, your proof is complete and rigorous.

Rigor Score: 8/10 → 10/10 (with lemma)
Recommendation: ACCEPT (after adding lemma)
```

### Output Artifacts
- `proof-check-report.md` - Correctness assessment
- `gaps-identified.md` - Missing steps or justifications
- `errors-found.md` - Logical errors (if any)
- `filled-gaps.md` - Suggested fixes (if requested)
- `rigor-score.json` - Numerical assessment

---

## Workflow 3: Conjecture Validation Mode 🔮

### When to Use
- Have a conjecture from literature or intuition
- Want to validate it's well-formed before proving
- Need computational verification
- Want to assess quality before investing in proof

### Agents Involved
**Conjecture Engineer** (validation role) + **Reviewer**

### Process Flow
```
You → Claude Code
    ↓ "Validate: [conjecture statement]"

Conjecture Engineer:
  1. Parse statement structure
  2. Check precision (are variables defined?)
  3. Assess testability
  4. Perform computational verification
  5. Search for counterexamples

Reviewer:
  6. Critique conjecture quality
  7. Assess interestingness
  8. Compare to known results
  9. Recommend: ACCEPT / REVISE / REJECT

Output:
  → Quality assessment
  → Computational evidence
  → Revision suggestions (if needed)
```

### Command Syntax

```bash
# Validate a conjecture
validate "For all n > 100, π(n) < n/ln(n) + n/ln²(n)" \
  --check-precision \
  --verify-computationally \
  --range 100:1000000

# Deep validation with comparison
validate "[statement]" \
  --compare-to-literature \
  --assess-novelty \
  --check-against-known-results

# Quick quality check
validate "[statement]" \
  --quick-check \
  --output quality_score
```

### Example Session

**Input:**
```
validate "For all primes p > 3, there exists a prime q where
p < q < 2p"
```

**Process:**
```
Conjecture Engineer:

Precision Check:
  ✓ All variables defined (p, q are primes)
  ✓ Domain specified (p > 3)
  ✓ Condition clear (p < q < 2p)
  ✓ Conclusion explicit (existence)

Testability:
  ✓ Can generate test cases
  ✓ Verification is computable
  ✓ Falsification is possible

Computational Verification:
  → Testing p ∈ [4, 1000000]
  → Found prime q for all cases
  → No counterexamples
  → Confidence: 99.9%

Reviewer:

Known Result Check:
  ⚠ This is Bertrand's Postulate!
  ⚠ Already proven by Chebyshev (1850)
  ⚠ Refined by Ramanujan (1919)

Assessment:
  Precision: 9/10
  Testability: 10/10
  Novelty: 0/10 (known result)

Recommendation: REJECT as novel conjecture
                (It's already a proven theorem)
```

**Output:**
```
Validation Result: KNOWN THEOREM

Your statement is Bertrand's Postulate (1845).
Proven by Chebyshev (1850).

While well-formed, this is not a new conjecture.

Reference: Chebyshev, P. L. (1850). "Mémoire sur les
nombres premiers". Journal de mathématiques pures et
appliquées, 17, 366-390.
```

### Output Artifacts
- `validation-report.md` - Quality assessment
- `precision-analysis.md` - Statement structure analysis
- `computational-evidence.json` - Verification results
- `literature-check.md` - Known results comparison
- `recommendations.md` - Accept/Revise/Reject with reasoning

---

## Workflow 4: Research & Discovery Mode 🔮

### When to Use
- Exploring new mathematical territory
- Have observations/data but no clear conjecture yet
- Want system to discover patterns and prove them
- Open-ended research questions

### Agents Involved
**All three agents** in full collaboration:
- Conjecture Engineer (discovers patterns)
- Proof Engineer (attempts proofs)
- Reviewer (monitors quality)

### Process Flow
```
You → Claude Code
    ↓ "Investigate patterns in [domain]"

Iteration Loop:
  1. Conjecture Engineer finds patterns → forms hypothesis
  2. Proof Engineer analyzes → attempts proof
  3. Reviewer (quick) → signal: CONTINUE/PIVOT/TERMINATE
  [Repeat 2-5 iterations]

Deep Review:
  4. Reviewer evaluates conjecture quality
  5. Reviewer evaluates proof completeness
  6. Reviewer assesses collaboration efficiency

Output:
  → Conjecture with evidence
  → Proof attempt (complete/partial/barrier)
  → Quality scores
  → Learning signals
```

### Command Syntax

```bash
# Basic research directive
research "Investigate prime gaps near highly composite numbers" \
  --mode discovery \
  --domain number_theory \
  --max-iterations 5 \
  --time-budget 15m

# With data input
research "Find patterns in this graph data" \
  --mode discovery \
  --domain graph_theory \
  --data graphs/connectivity_data.csv \
  --focus "chromatic number patterns"

# Open-ended exploration
research "Explore relationships between Fibonacci numbers and primes" \
  --mode discovery \
  --exploratory \
  --max-iterations 8
```

### Example Session

**Input:**
```
"Investigate whether prime gaps are unusually large near highly
composite numbers. I have computational data suggesting a pattern."
```

**Process:**
```
Iteration 1:
  Conjecture Eng: "g(p) > log(h)²"
  Proof Eng: "Too strong, violates Cramer's"
  Reviewer: CONTINUE

Iteration 2:
  Conjecture Eng: "g(p) > 0.5·log(h)²"
  Proof Eng: "Partial proof at 0.3 coefficient"
  Reviewer: TERMINATE (convergence)

Deep Review:
  Quality: 7.3/10
  Recommendation: ACCEPT
```

**Output:**
```
Conjecture: For highly composite h > 100, g(p) > 0.5·log(h)²
Evidence: 387 cases verified, partial proof (0.3 bound)
Quality: 7.3/10 - ACCEPTED
Next steps: Formalize in Lean, extend verification
```

### Output Artifacts
- `conjecture.md` - Formal statement with notation
- `evidence.json` - Computational verification results
- `proof-attempt.md` - Proof sketch or partial result
- `review-report.json` - Quality assessment
- `learning-signals.json` - For episodic memory (future)

---

## Workflow 5: Hybrid Modes 🔮

### Mode 5a: Research with Pre-Existing Conjecture

**Use case:** Have a conjecture, want to find computational evidence AND prove it

**Agents:** Conjecture Engineer (verification only) + Proof Engineer + Reviewer

```bash
research "Prove or verify: For all highly composite h, g(p) > 0.5·log(h)²" \
  --mode hybrid \
  --verify-first \
  --then-prove
```

**Process:**
1. Conjecture Engineer verifies computationally
2. If evidence strong → Proof Engineer attempts proof
3. Reviewer monitors both
4. Output: Evidence + Proof attempt

### Mode 5b: Prove with Computational Backup

**Use case:** Attempting proof, but want computational evidence if proof fails

**Agents:** Proof Engineer (primary) + Conjecture Engineer (backup)

```bash
prove "[statement]" \
  --mode hybrid \
  --fallback-verification \
  --if-blocked compute-evidence
```

**Process:**
1. Proof Engineer attempts proof
2. If blocked → Conjecture Engineer runs computational verification
3. Output: Proof (if success) OR Evidence + Barrier analysis (if blocked)

### Mode 5c: Discovery with Literature Check

**Use case:** Research mode, but check novelty during process

**Agents:** All three + Literature search tool

```bash
research "Explore patterns in [domain]" \
  --mode discovery \
  --check-literature-each-iteration \
  --avoid-known-results
```

**Process:**
1. Standard research loop
2. After each conjecture: check if known
3. If known: report and pivot
4. If novel: continue
5. Output: Only novel conjectures

---

## Workflow Selection Guide

### Decision Tree

```
Do you have a clear statement?
│
├─ NO → Use Workflow 4: Research & Discovery 🔮
│
└─ YES → What do you want to do with it?
    │
    ├─ Prove it → Is it well-formed?
    │   │
    │   ├─ NOT SURE → Workflow 3: Validate first, then prove 🔮
    │   │
    │   └─ YES → Workflow 1: Theorem Proving ⚡
    │
    ├─ Already have proof → Workflow 2: Proof Checking 🔮
    │
    ├─ Check if it's good → Workflow 3: Conjecture Validation 🔮
    │
    └─ Find patterns/discover → Workflow 4: Research & Discovery 🔮
```

### Quick Reference Table

| Goal | Workflow | Agents Used | Status | Typical Time |
|------|----------|-------------|--------|--------------|
| Prove specific theorem | 1. Theorem Proving | Proof Eng (+ opt Reviewer) | ⚡ | 5-15 min |
| Check existing proof | 2. Proof Checking | Reviewer (+ opt Proof Eng) | 🔮 | 2-5 min |
| Validate conjecture quality | 3. Conjecture Validation | Conj Eng + Reviewer | 🔮 | 3-8 min |
| Explore & discover new conjectures | 4. Research & Discovery | All 3 | 🔮 | 10-20 min |
| Research with statement | 5a. Hybrid | Conj Eng + Proof Eng + Reviewer | 🔮 | 10-20 min |
| Prove with evidence backup | 5b. Hybrid | Proof Eng + Conj Eng | 🔮 | 8-15 min |

---

## Integration with Current System

### What's Available Now

The current implementation supports **basic theorem proving** via the `proof-engineer` agent:

```
Knowledge Base → proof-engineer → Training Dataset
(templates)      (validation)     (verified proofs)
```

**Capabilities:**
- Validate Lean 4 templates from knowledge bases
- 4-stage proof loop: Gather → Attempt → Verify → Refine
- Dynamic loading of 14 Lean skills
- Barrier analysis and error resolution

**Invoke via Claude Code:**
```python
task = Task(
    subagent_type="proof-engineer",
    prompt="Prove this theorem in Lean 4: [statement]"
)
```

### Roadmap to Full System

| Phase | Components | Timeline |
|-------|------------|----------|
| **Phase 1** (Current) | proof-engineer + Lean skills | ✅ Done |
| **Phase 2** | reviewer agent + quality-assessment skills | Planned |
| **Phase 3** | conjecture-engineer + pattern-finding skills | Planned |
| **Phase 4** | Workflow orchestration + CLI commands | Planned |
| **Phase 5** | Episodic memory + learning signals | Future |

---

## Output Formats

### Standard Output Structure

All workflows produce:
```
session_YYYYMMDD_NNN/
├── input.json              # What you provided
├── process-log.md          # What happened
├── result.md               # Main result (human-readable)
├── result.json             # Structured data
├── artifacts/              # Supporting files
│   ├── [workflow-specific files]
│   └── ...
└── metadata.json           # Session info, metrics
```

---

## Best Practices

### For Theorem Proving (Available Now)
1. Provide clear, well-formed Lean 4 statement
2. Include context (imports, known results)
3. Specify domain for skill loading
4. Use barrier analysis to understand blockers
5. Check partial results even if full proof fails

### For Future Workflows
1. Start with broad directive, let system explore
2. Provide any data/observations you have
3. Set realistic iteration limits (5-8 for complex problems)
4. Review quality scores before accepting
5. Use hybrid modes when unsure of approach

---

## Summary

This system supports flexible mathematical research through multiple operational modes (ordered by complexity):

1. **Theorem Proving** ⚡: Prove specific statement (Proof Engineer)
2. **Proof Checking** 🔮: Verify existing proof (Reviewer)
3. **Validation** 🔮: Check conjecture quality (Conjecture Engineer + Reviewer)
4. **Research & Discovery** 🔮: Discover + Prove (all agents)
5. **Hybrid** 🔮: Combinations of above

**Currently Available**: Basic theorem proving via `proof-engineer`

**Key Principle:** Same agents, different combinations, tailored to your specific mathematical task.
