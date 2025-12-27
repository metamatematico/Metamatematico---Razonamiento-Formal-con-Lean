# Model Research: Lean 4 Verifier/Reasoner Landscape

**Date:** 2025-12-14
**Purpose:** Assess novelty of training a mathematical autoformalizer for Lean 4

---

## Executive Summary

**Finding:** Training an **autoformalizer** (NL → complete Lean 4 proof) **IS novel**. Existing open-source models are **tactic generators** (given formal proof state → next tactic), NOT end-to-end autoformalizers.

### Critical Distinction

| Model Type | Input | Output | Exists? |
|------------|-------|--------|---------|
| **Tactic Generator** | Lean proof state | Next tactic | ✅ DeepSeek-Prover-V2, ReProver |
| **Autoformalizer** | NL math statement | Complete Lean 4 proof | ❌ No open-source model |

**Our goal (autoformalizer) is genuinely novel.**

---

## Existing Models (Tactic Generators, NOT Autoformalizers)

### What These Models Actually Do

All existing open-source models are **tactic generators**:
- **Input:** A formal Lean proof state (e.g., `⊢ ∀ x, P x → Q x`)
- **Output:** The next tactic to apply (e.g., `intro x; intro h; apply f h`)

They do **NOT**:
- Accept natural language math as input
- Generate complete Lean 4 code from scratch
- Translate informal proofs to formal proofs

### State-of-the-Art Tactic Generators (Open-Source)

| Model | Size | Performance | What It Does |
|-------|------|-------------|--------------|
| **DeepSeek-Prover-V2** | 7B, 671B | 88.9% miniF2F | Proof state → tactic |
| **ReProver/LeanDojo** | Encoder-decoder | Retrieval-augmented | Proof state → tactic (with premise retrieval) |
| **Llemma** | 7B, 34B | Math-specialized | Math reasoning + some tactic generation |
| **InternLM-Math** | Various | Bilingual | Math reasoning + tactic generation |

### Closed-Source (Reference Only)

| Model | What It Does | Owner |
|-------|--------------|-------|
| **AlphaProof** | Uses Gemini for autoformalization (NL → Lean), then MCTS for proving | Google DeepMind |
| **Aristotle** | R1-style reasoning + Lean verification | Harmonic (closed) |

**Note:** AlphaProof is the only system known to do autoformalization, but it's completely closed-source.

---

## Novelty Assessment

### What is NOT Novel (Tactic Generation)

| Approach | Why Duplicative |
|----------|-----------------|
| Tactic generator (proof state → tactic) | DeepSeek-Prover-V2 achieves 88.9% |
| Retrieval-augmented tactic generation | ReProver/LeanDojo established |
| Math-specialized base model | Llemma already available |

### What IS Novel (Autoformalization)

| Component | Novelty | Notes |
|-----------|---------|-------|
| **Open-source autoformalizer** | **VERY HIGH** | No open-source NL → Lean 4 proof model exists |
| **End-to-end formal proof generation** | **VERY HIGH** | Existing models need formal input |
| **Unified dataset schema v3.0** | HIGH | Supports autoformalization training |
| **Quality metrics for formal proofs** | HIGH | LIMO was informal math only |
| **R1 + Lean autoformalization** | HIGH | Open version of AlphaProof/Aristotle approach |

### The Autoformalization Gap

```
What EXISTS (Tactic Generators):
┌─────────────────────┐    ┌──────────────────┐    ┌─────────────┐
│ Lean Proof State    │ →  │ DeepSeek-Prover  │ →  │ Next Tactic │
│ ⊢ ∀ x, P x → Q x   │    │ ReProver, etc.   │    │ intro x     │
└─────────────────────┘    └──────────────────┘    └─────────────┘

What DOESN'T EXIST (Autoformalizers):
┌─────────────────────┐    ┌──────────────────┐    ┌─────────────────────────┐
│ Natural Language    │ →  │   ???            │ →  │ Complete Lean 4 Proof   │
│ "For any group      │    │ (OUR MODEL)      │    │ theorem first_iso ...   │
│  homomorphism..."   │    │                  │    │   := by exact ...       │
└─────────────────────┘    └──────────────────┘    └─────────────────────────┘
```

---

## Recommended Path (Autoformalization Focus)

### Our Goal

Fine-tune a model to be an **autoformalizer**:
- **Input:** Natural language mathematical statement + informal proof
- **Output:** Complete, verified Lean 4 theorem + proof

### Phase 1: Dataset Preparation (Current)

1. Build unified schema v3.0 supporting NL-FL pairs
2. Curate high-quality NL statements with corresponding Lean 4 proofs
3. Include reasoning traces (LIMO-style) for better learning

### Phase 2: Fine-Tune for Autoformalization

1. Start with reasoning-capable base model (DeepSeek R1 distilled, Qwen, etc.)
2. Fine-tune on NL → Lean 4 pairs using our dataset
3. Use Lean compiler verification as reward signal
4. Iterate with expert iteration (successful proofs → training data)

### Phase 3: Evaluation & Iteration

1. Measure autoformalization success rate (% of NL inputs → valid Lean proofs)
2. Compare to baseline (GPT-4, Claude prompting without fine-tuning)
3. Identify failure modes and expand dataset accordingly

### Why This Is Different from Existing Work

| Existing Models | Our Autoformalizer |
|-----------------|-------------------|
| Need formal Lean input | Accept natural language |
| Generate one tactic at a time | Generate complete proofs |
| Require proof state extraction | Work end-to-end |
| Can't be used by non-Lean experts | Accessible to mathematicians |

---

## Project Contribution Focus

Given the autoformalization gap, our contribution is **both dataset AND model**:

### Primary (Novel Autoformalizer Model)

1. **First open-source NL → Lean 4 autoformalizer**
2. **End-to-end proof generation** (no Lean expertise required to use)
3. **Open alternative to AlphaProof/Aristotle**

### Supporting (Dataset)

1. **Unified schema v3.0** - NL-FL pairs with reasoning traces
2. **Quality scoring** - LIMO-style metrics for training data curation
3. **Augmentation methodology** - Expand dataset while maintaining quality
4. **Verification integration** - Lean compiler as ground truth

---

## Key Questions to Clarify

Before proceeding, we should define:

1. **What does "verifier" mean for us?**
   - Verify proof correctness? (Lean already does this)
   - Score proof quality? (Novel application)
   - Find errors in informal proofs? (Novel application)
   - Generate proofs from NL? (Existing capability)

2. **Domain specificity:**
   - General mathematics? (Covered by existing models)
   - Specialized domain? (Potential novelty)
   - Educational use case? (Application novelty)

3. **Success criteria:**
   - Research contribution (paper)?
   - Applied tool (product)?
   - Learning exercise?

---

## Sources

- [DeepSeek-Prover-V2](https://arxiv.org/abs/2504.21801)
- [LeanDojo](https://leandojo.org/) | [Paper](https://arxiv.org/abs/2306.15626)
- [AlphaProof (Nature)](https://www.nature.com/articles/s41586-025-09833-y)
- [LIMO](https://arxiv.org/html/2502.03387v3)
- [Llemma](https://arxiv.org/abs/2310.10631)

---

## Schema Decision (2025-12-14)

**Simplified from v3.0 to v4.0** - The original schema was designed for tactic generation (like DeepSeek-Prover-V2), not autoformalization.

| Version | Fields | Purpose |
|---------|--------|---------|
| v3.0 | ~55 | Support 4 training approaches (LIMO, DeepSeek, LeanDojo, AlphaProof) |
| v4.0 | ~13 | Support autoformalization (NL → complete Lean proof) |

**Removed:** `state_tactic_pairs`, `proof_tree`, `premise_annotations`, `formal_variations`, `quality_metrics`, `subgoal_decomposition`

**Kept:** Core NL↔FL pairs, reasoning traces, verification status

---

## Related Research Files

- `context/research/theorem-proving-landscape-2025.md` - Dataset contribution validation
- `context/research/lean4-verifier-models-2025-12-13-deep.md` - Full model landscape analysis
- `dataset/dataset_schema.md` - Simplified schema v4.0
- `dataset/rl_dataset_analysis.md` - Autoformalization training analysis
