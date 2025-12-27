# Dataset Analysis for Autoformalization Training

**Purpose:** Training LLMs to translate natural language math → Lean 4 proofs
**Updated:** 2025-12-14
**Related:** See `dataset_schema.md` for v5.0 schema

---

## Executive Summary

We are building an **autoformalizer**: a model that translates natural language mathematical statements into complete, verified Lean 4 proofs.

```
Input:  "For any group homomorphism f: G → H, G/ker(f) is isomorphic to im(f)"
Output: theorem first_iso (f : G →* H) : G ⧸ MonoidHom.ker f ≃* MonoidHom.range f :=
          QuotientGroup.quotientKerEquivRange f
```

This is **different from tactic generation** (DeepSeek-Prover-V2, ReProver), which generates tactics step-by-step given a formal proof state.

---

## Proof Validation Pipeline

### Two-Stage Architecture

The dataset follows a two-stage pipeline separating content authoring from Lean validation:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Knowledge Base │    │  Proof Engineer │    │ Training Dataset│
│  (NL + Lean     │ → │  (Validation)   │ → │  (Verified)     │
│   templates)    │    │  compiles=?     │    │  compiles=true  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
     Stage 1                Stage 2               Final Output
```

### Stage 1: Knowledge Base Authoring

Human experts (or AI assistants) create knowledge base entries:
- Natural language statement
- Lean template (may use `sorry`, may not compile)
- Imports, difficulty, metadata

**Output:** Records with `proof.status: "template"`

### Stage 2: Proof Engineer Validation

The `proof-engineer` agent processes the validation queue:

```python
# Pseudocode for proof-engineer workflow
async def validate_postulate(postulate: dict) -> dict:
    # 1. Extract template
    lean_code = postulate["lean_template"]

    # 2. Attempt compilation
    result = await lean_compiler.check(lean_code, imports=postulate["imports"])

    # 3. Record attempt
    attempt = {
        "attempt": len(postulate["proof"]["validation_attempts"]) + 1,
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "proof-engineer-v1",
        "result": "validated" if result.success else "failed",
        "error": result.error if not result.success else None,
        "lean_version": LEAN_VERSION,
        "mathlib_version": MATHLIB_VERSION
    }
    postulate["proof"]["validation_attempts"].append(attempt)

    # 4. Update status
    if result.success:
        postulate["proof"]["status"] = "validated"
        postulate["proof"]["lean_validated"] = lean_code
    else:
        # Try to fix common issues
        fixed_code = await attempt_fix(lean_code, result.error)
        if fixed_code:
            postulate["lean_template"] = fixed_code
            postulate["proof"]["status"] = "pending_review"
        else:
            postulate["proof"]["status"] = "failed"

    return postulate
```

### Validation Queue Management

```
dataset/
└── validation_queue/
    ├── pending.jsonl       # status: pending_review
    ├── failed.jsonl        # status: failed (needs human review)
    └── processed.log       # Audit trail
```

**Queue Priority:**
1. `easy` difficulty first (quick wins)
2. `medium` difficulty second
3. `hard` difficulty last (may need human intervention)

### Common Validation Errors

| Error Pattern | Frequency | Auto-Fix Strategy |
|---------------|-----------|-------------------|
| `declaration uses 'sorry'` | 45% | Search Mathlib for direct lemma |
| `unknown identifier` | 25% | Add missing imports |
| `type mismatch` | 15% | Adjust type annotations |
| `failed to synthesize instance` | 10% | Add typeclass constraints |
| Other | 5% | Flag for human review |

---

## Training Pipeline

### What We Need

| Component | Purpose | Source |
|-----------|---------|--------|
| NL statement | Model input | `nl_statement` field |
| Lean code | Model output | `proof.lean_validated` field |
| Imports | Context for model | `imports` field |
| Reasoning trace | Optional CoT for training | `reasoning_trace` field |

### What We DON'T Need

| Component | Why Not Needed |
|-----------|----------------|
| State-tactic pairs | For tactic gen, not autoformalization |
| Proof trees | For tactic gen, not autoformalization |
| Premise annotations | For retrieval-augmented tactic gen |
| LIMO quality scores | Over-engineered for our use case |

---

## Training Phases

### Phase 1: Supervised Fine-Tuning (SFT)

Train on (NL statement, imports) → (Lean validated code) pairs.

```python
# Training format
def format_training_example(postulate: dict) -> dict:
    # Only use validated records
    assert postulate["proof"]["status"] == "validated"

    input_text = f"""Translate to Lean 4:
{postulate["nl_statement"]}

Available imports: {postulate["imports"]}"""

    output_text = postulate["proof"]["lean_validated"]

    return {"input": input_text, "output": output_text}
```

### Phase 2: Reinforcement Learning (Optional)

Use Lean compiler as verifier:
- **Reward = 1.0** if output compiles
- **Reward = 0.0** if output fails

No need for graded rewards since we output complete proofs, not individual tactics.

```python
async def compute_reward(generated_lean: str, imports: list[str]) -> float:
    result = await lean_compiler.check(generated_lean, imports=imports)
    return 1.0 if result.success else 0.0
```

---

## Data Augmentation

### Prioritize Low-Correlation Methods

| Method | Correlation (ρ) | Effective Multiplier | Implementation |
|--------|-----------------|---------------------|----------------|
| Proof style variants | 0.35 | 0.65 | term ↔ tactic mode |
| Type instantiation | 0.40 | 0.60 | Generic → concrete types |

### Minimize High-Correlation Methods

| Method | Correlation (ρ) | Effective Multiplier | Notes |
|--------|-----------------|---------------------|-------|
| NL paraphrasing | 0.85 | 0.15 | Little added signal |
| Variable renaming | 0.90 | 0.10 | Avoid |

### Effective Sample Size

**Critical insight:** Augmented samples are correlated, reducing effective dataset size.

Formula: `Effective N ≈ N × (1 - ρ)`

Example:
- 50 base theorems × 20 augmentations = 1000 raw samples
- With ρ = 0.7 (high correlation): Effective N ≈ 300
- With ρ = 0.4 (low correlation): Effective N ≈ 600

**Recommendation:** Prioritize expanding base theorem count over heavy augmentation.

---

## Dataset Scale

### Current Status

| Metric | Value |
|--------|-------|
| Knowledge bases | 17 |
| Total postulates | ~564 |
| Status: template | ~560 (estimated) |
| Status: validated | ~4 (estimated) |
| Status: failed | ~0 |

### Target Scale

| Phase | Validated Records | Purpose |
|-------|-------------------|---------|
| Cold-start | 100-500 | Initial fine-tuning feasibility |
| MVP | 1,000-2,000 | Reliable autoformalization |
| Full | 5,000-10,000 | Robust generalization |

### Validation Throughput

| Difficulty | Est. Success Rate | Avg. Attempts | Records/Hour |
|------------|-------------------|---------------|--------------|
| Easy | 85% | 1.2 | 50 |
| Medium | 60% | 2.5 | 20 |
| Hard | 30% | 5+ | 5 |

---

## Proof Engineer Compute Costs

### Per-Validation Cost

| Component | Time | Cost |
|-----------|------|------|
| Lean compilation | ~5s | CPU only |
| Agent reasoning | ~10s | ~$0.01 (API call) |
| Fix attempt | ~30s | ~$0.05 (if needed) |

### Batch Processing Estimate

| Records | Est. Time | Est. Cost |
|---------|-----------|-----------|
| 100 | 2 hours | $5-10 |
| 500 | 10 hours | $25-50 |
| 1000 | 20 hours | $50-100 |

### Optimization Strategies

1. **Batch by imports**: Group postulates with same imports to share Lean environment
2. **Easy first**: Validate easy records first for quick wins
3. **Parallel workers**: Run multiple Lean environments in parallel
4. **Cache Mathlib**: Pre-build Mathlib cache, share across validations

---

## Validation Metrics

### Primary Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| Validation rate | validated / (validated + failed) | > 70% |
| First-attempt success | validated on attempt 1 / total | > 50% |
| Avg attempts to success | mean(attempts) for validated | < 2.0 |

### Error Analysis

Track error categories to improve templates:

```python
error_categories = {
    "sorry": 0,
    "unknown_identifier": 0,
    "type_mismatch": 0,
    "instance_synthesis": 0,
    "other": 0
}

def categorize_error(error_msg: str) -> str:
    if "sorry" in error_msg:
        return "sorry"
    elif "unknown identifier" in error_msg:
        return "unknown_identifier"
    # ... etc
```

---

## Training Infrastructure

### Recommended Stack

- **Base model:** DeepSeek R1 distilled (7B-32B) or similar reasoning model
- **Fine-tuning:** LoRA/QLoRA for efficiency
- **Verification:** Lean 4 compiler (parallel workers)
- **Format:** JSONL → Parquet for training

### Cost Estimate (Full Training)

| Component | Estimated Cost |
|-----------|---------------|
| GPU compute (A100 spot) | $300-500 |
| Proof-engineer validation | $50-100 |
| Storage | $50 |
| **Total** | **$400-650** |

---

## Evaluation

### Primary Metric

**Autoformalization success rate:** % of NL inputs that produce valid Lean proofs

```python
def evaluate_model(model, test_set: list[dict]) -> float:
    successes = 0
    for example in test_set:
        generated = model.generate(example["input"])
        result = lean_compiler.check(generated, imports=example["imports"])
        if result.success:
            successes += 1
    return successes / len(test_set)
```

### Baseline Comparison

| Model | Expected Success Rate |
|-------|----------------------|
| GPT-4 zero-shot | ~15-25% |
| Claude zero-shot | ~15-25% |
| Fine-tuned (ours) | Target: >60% |

### Test Set Construction

- Hold out 10% of validated records
- Stratify by theory and difficulty
- No augmentation leakage (hold out original + all augmentations)

---

## Integration with Knowledge Space

The training pipeline integrates with the [math-knowledge-space](https://github.com/ai-enhanced-engineer/math-knowledge-space) repository:

1. **Measurability ordering**: Process high-score theories first
2. **Dependency awareness**: Validate dependencies before dependents
3. **Frontier exploration**: Generated proofs can inform frontier analysis

---

## References

- [math-knowledge-space](https://github.com/ai-enhanced-engineer/math-knowledge-space) - Knowledge bases and extraction pipeline
- [dataset_schema.md](https://github.com/ai-enhanced-engineer/math-knowledge-space/blob/main/docs/dataset_schema.md) - v5.0 schema specification
- [DeepSeek-R1](https://arxiv.org/abs/2501.12948) - Reasoning via RL
- [AlphaProof](https://www.nature.com/articles/s41586-025-09833-y) - Autoformalization approach
- [TheoremLlama](https://arxiv.org/abs/2407.03203) - NL-FL alignment
