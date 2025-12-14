# Mathematical Proofs Dataset Schema v5.0

**Purpose:** Training LLMs as autoformalizers (NL → Lean 4 proofs)
**Format:** JSONL (source of truth) + Parquet (training)
**Updated:** 2025-12-14

---

## Design Philosophy

### Goal: Digitalization of Mathematics

This project aims to **digitalize mathematics** - converting human mathematical knowledge into verified formal proofs. The dataset serves as the bridge between natural language understanding and machine-checkable Lean 4 code.

### Two-Stage Pipeline

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Knowledge Base │    │  Proof Engineer │    │ Training Dataset│
│  (NL + Lean     │ → │  (Validation)   │ → │  (Verified)     │
│   templates)    │    │  compiles=?     │    │  compiles=true  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
     Stage 1                Stage 2               Final Output
```

**Stage 1: Knowledge Base Authoring**
- Human experts write NL statements + Lean *templates*
- Templates may contain `sorry`, incomplete proofs, or syntax issues
- Focus on mathematical content, not compilation

**Stage 2: Proof Engineer Validation**
- `proof-engineer` agent processes templates through Lean compiler
- Fixes syntax errors, resolves `sorry` placeholders
- Records all validation attempts with error history
- Only `proof.status: validated` enters training

**Benefits:**
- KBs can be updated without blocking on Lean compilation
- Clear separation of concerns (content vs. verification)
- Full audit trail of validation attempts
- Training data guaranteed valid

---

## Example: Autoformalization Task

```
Input:  "For any group homomorphism f: G → H, G/ker(f) is isomorphic to im(f)"
Output: theorem first_iso (f : G →* H) : G ⧸ MonoidHom.ker f ≃* MonoidHom.range f :=
          QuotientGroup.quotientKerEquivRange f
```

**NOT** designed for tactic generation (proof state → next tactic), which requires different data structures.

---

## File Organization

```
dataset/
├── dataset_schema.md           # This file - technical spec
├── rl_dataset_analysis.md      # Training strategy
├── raw/
│   ├── postulates.jsonl        # All postulates (templates + validated)
│   └── by_theory/
│       ├── set_theory.jsonl
│       ├── algebra.jsonl
│       └── ...
├── processed/
│   └── training.parquet        # Only validated records
└── validation_queue/
    └── pending.jsonl           # Awaiting proof-engineer
```

---

## Schema: `postulates.jsonl`

Each line is a JSON object representing one mathematical postulate.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `postulate_id` | string | Hierarchical ID: `{theory}.{name}` (e.g., `"set_theory.zfc_extensionality"`) |
| `type` | string | `"axiom"` \| `"theorem"` \| `"lemma"` \| `"definition"` \| `"corollary"` |
| `theory` | string | Parent theory: `"set_theory"`, `"algebra"`, etc. |
| `family` | string | Mathematical family: `"foundations"`, `"algebra"`, `"analysis"`, `"topology"`, `"geometry"`, `"discrete"` |
| `nl_statement` | string | Natural language statement |
| `lean_template` | string | Lean 4 code (may not compile) |
| `imports` | array[string] | Required Mathlib imports |
| `proof` | object | Proof validation status (see below) |

### Proof Object (Two-Stage Pipeline)

```json
{
  "proof": {
    "status": "template",
    "difficulty": "medium",
    "lean_validated": null,
    "validation_attempts": []
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"template"` \| `"pending_review"` \| `"validated"` \| `"failed"` |
| `difficulty` | string | `"easy"` \| `"medium"` \| `"hard"` |
| `lean_validated` | string \| null | Validated Lean code (filled when status=validated) |
| `validation_attempts` | array[object] | History of all validation attempts |

### Validation Attempt Object

```json
{
  "attempt": 1,
  "timestamp": "2025-12-14T10:00:00Z",
  "agent": "proof-engineer-v1",
  "result": "failed",
  "error": "unknown identifier 'X'",
  "lean_version": "v4.16.0",
  "mathlib_version": "v4.14.0"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `attempt` | int | Attempt number (1-indexed) |
| `timestamp` | string | ISO 8601 timestamp |
| `agent` | string | Agent/system that performed validation |
| `result` | string | `"validated"` \| `"failed"` |
| `error` | string \| null | Error message if failed |
| `lean_version` | string | Lean version used |
| `mathlib_version` | string | Mathlib version used |

### Status Flow

```
template → pending_review → validated (enters training)
                         ↘ failed → pending_review (retry)
                                  ↘ failed (after max retries)
```

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `latex` | string | LaTeX rendering of statement |
| `reasoning_trace` | object | Chain-of-thought reasoning |
| `reasoning_trace.mathematical_insight` | string | Core mathematical intuition |
| `reasoning_trace.proof_strategy` | string | High-level approach |
| `reasoning_trace.key_lemmas` | array[string] | Mathlib lemmas used |
| `alternative_proofs` | array[object] | Different proof styles |
| `dependencies` | object | Graph relationships |
| `dependencies.depends_on` | array[string] | Postulate IDs this depends on |
| `dependencies.used_by` | array[string] | Postulate IDs that depend on this |
| `dependencies.related` | array[string] | Semantically related postulates |
| `mathlib_coverage` | string | `"full"` \| `"partial"` \| `"none"` |
| `measurability_score` | int | 0-100 formalizability score |
| `created_at` | string | ISO 8601 timestamp |
| `updated_at` | string | ISO 8601 timestamp |

---

## Example Records

### Template (Stage 1 - Not Yet Validated)

```json
{
  "postulate_id": "set_theory.cantors_theorem",
  "type": "theorem",
  "theory": "set_theory",
  "family": "foundations",
  "nl_statement": "For any set X, there is no surjection from X onto its power set P(X).",
  "lean_template": "theorem cantors_theorem {α : Type*} : ¬ Function.Surjective (fun x : α => ({x} : Set α)) := sorry",
  "imports": ["Mathlib.Logic.Function.Basic", "Mathlib.Data.Set.Basic"],
  "proof": {
    "status": "template",
    "difficulty": "easy",
    "lean_validated": null,
    "validation_attempts": []
  },
  "mathlib_coverage": "full",
  "measurability_score": 98
}
```

### Failed Validation (Stage 2 - With Error)

```json
{
  "postulate_id": "set_theory.cantors_theorem",
  "type": "theorem",
  "theory": "set_theory",
  "family": "foundations",
  "nl_statement": "For any set X, there is no surjection from X onto its power set P(X).",
  "lean_template": "theorem cantors_theorem {α : Type*} : ¬ Function.Surjective (fun x : α => ({x} : Set α)) := sorry",
  "imports": ["Mathlib.Logic.Function.Basic", "Mathlib.Data.Set.Basic"],
  "proof": {
    "status": "failed",
    "difficulty": "easy",
    "lean_validated": null,
    "validation_attempts": [
      {
        "attempt": 1,
        "timestamp": "2025-12-14T10:00:00Z",
        "agent": "proof-engineer-v1",
        "result": "failed",
        "error": "declaration uses 'sorry'",
        "lean_version": "v4.16.0",
        "mathlib_version": "v4.14.0"
      }
    ]
  }
}
```

### Validated (Stage 2 - Ready for Training)

```json
{
  "postulate_id": "algebra.group_first_iso",
  "type": "theorem",
  "theory": "algebra",
  "family": "algebra",
  "nl_statement": "For any group homomorphism f: G → H, the quotient group G/ker(f) is isomorphic to the image of f.",
  "lean_template": "theorem first_isomorphism_theorem (f : G →* H) : G ⧸ MonoidHom.ker f ≃* MonoidHom.range f := sorry",
  "imports": ["Mathlib.GroupTheory.QuotientGroup.Basic"],
  "proof": {
    "status": "validated",
    "difficulty": "easy",
    "lean_validated": "theorem first_isomorphism_theorem (f : G →* H) : G ⧸ MonoidHom.ker f ≃* MonoidHom.range f := QuotientGroup.quotientKerEquivRange f",
    "validation_attempts": [
      {
        "attempt": 1,
        "timestamp": "2025-12-14T10:00:00Z",
        "agent": "proof-engineer-v1",
        "result": "failed",
        "error": "declaration uses 'sorry'",
        "lean_version": "v4.16.0",
        "mathlib_version": "v4.14.0"
      },
      {
        "attempt": 2,
        "timestamp": "2025-12-14T11:30:00Z",
        "agent": "proof-engineer-v1",
        "result": "validated",
        "error": null,
        "lean_version": "v4.16.0",
        "mathlib_version": "v4.14.0"
      }
    ]
  },
  "reasoning_trace": {
    "mathematical_insight": "The kernel quotient construction is universal for homomorphisms. The induced map on the quotient is injective by construction and surjective onto the range.",
    "proof_strategy": "Apply Mathlib's first isomorphism theorem directly",
    "key_lemmas": ["QuotientGroup.quotientKerEquivRange"]
  },
  "dependencies": {
    "depends_on": ["algebra.quotient_group_def", "algebra.kernel_def"],
    "used_by": ["algebra.second_iso"],
    "related": ["algebra.ring_first_iso"]
  }
}
```

---

## Difficulty Levels

| Level | Criteria | Proof Engineer Guidance |
|-------|----------|-------------------------|
| `easy` | Direct Mathlib lemma application | Should validate in 1-2 attempts |
| `medium` | Requires composition of 2-3 lemmas | May need tactic exploration |
| `hard` | Custom proof construction required | May require human review |

---

## Training Data Extraction

Only records with `proof.status: "validated"` are used for training.

### Input Format (to model)

```
Translate to Lean 4:
{nl_statement}

Available imports: {imports}
```

### Expected Output (from model)

```lean
{lean_validated}
```

### Filtering Query

```python
def get_training_records(postulates: list[dict]) -> list[dict]:
    return [p for p in postulates if p["proof"]["status"] == "validated"]
```

---

## Validation Rules

1. `postulate_id` must be unique and follow `{theory}.{name}` format
2. `type` must be one of: axiom, theorem, lemma, definition, corollary
3. `family` must be one of: foundations, algebra, analysis, topology, geometry, discrete
4. `proof.status` must be one of: template, pending_review, validated, failed
5. `imports` must be valid Mathlib4 paths
6. If `proof.status == "validated"`, `lean_validated` must be non-null
7. `validation_attempts` must be ordered by `attempt` number

---

## Schema Evolution

| Version | Changes |
|---------|---------|
| 1.0.0 | Initial schema |
| 2.0.0 | Added reasoning_trace, proof_metrics, verification |
| 3.0.0 | Added LIMO, DeepSeek, LeanDojo, AlphaProof fields |
| 4.0.0 | Simplified for autoformalization - removed tactic-generation fields |
| **5.0.0** | **Two-stage pipeline: proof object with validation_attempts history** |

### Why v5.0?

v4.0 had a simple `compiles: boolean` field. v5.0 introduces:
- **`proof.status`**: Tracks template → validated lifecycle
- **`validation_attempts`**: Full history of compilation attempts
- **`lean_validated`**: Separate from template (original preserved)
- **Hierarchical IDs**: `{theory}.{name}` for knowledge space navigation

This supports the **digitalization of mathematics** goal where:
1. Knowledge bases grow independently of Lean compilation
2. Proof-engineer agent processes validation queue
3. Training dataset contains only verified proofs

---

## Integration with Knowledge Space

This schema is designed to integrate with the Mathematical Knowledge Space (see `UNIVERSE_EXPANSION.md`):

- **`postulate_id`**: Graph node identifier
- **`theory`** / **`family`**: Graph hierarchy (PART_OF edges)
- **`dependencies`**: Graph relationships (DEPENDS_ON, RELATES_TO edges)
- **`measurability_score`**: Ordering for dataset generation priority

---

## References

- [UNIVERSE_EXPANSION.md](../UNIVERSE_EXPANSION.md) - Knowledge space architecture
- [rl_dataset_analysis.md](./rl_dataset_analysis.md) - Training strategy
- [Mathlib4 Documentation](https://leanprover-community.github.io/mathlib4_docs/)
- [100 Theorems in Lean](https://leanprover-community.github.io/100.html)
