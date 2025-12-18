# AI Mathematician: Research Program

**Project**: AI Mathematician
**Status**: Validated Research Program
**Date**: 2025-12-14
**Impact Assessment**: 7.5/10 (High - with strategic positioning)

---

## I. Vision: The Digitalization of Mathematics

> *"The most urgent priority of metamathematicians was to determine the true nature of mathematical reasoning... This would require a complete codification of the universally acceptable modes of human reasoning."*
> — Douglas Hofstadter, *Gödel, Escher, Bach* (1979)

Mathematics exists primarily in natural language—textbooks, papers, lectures—where ambiguity is inherent and verification is manual. The **AI Mathematician** project aims to **digitalize mathematics**: converting human mathematical knowledge into machine-verifiable formal proofs organized as a navigable knowledge graph.

This is not merely dataset creation. We propose a computational realization of Hofstadter's metamathematical program, where:

1. **Structure is preserved** — Mathematical theories form a graph, not a flat list
2. **Verification is deterministic** — The Lean compiler is the ultimate arbiter of correctness
3. **Discovery is systematic** — Agents explore frontiers between theories
4. **Limits are detectable** — Gödel's incompleteness manifests as observable patterns

### The Gap We Address

| Current Open-Source SOTA | Our Target |
|--------------------------|------------|
| Autoformalization: 15-26% success | **50-60% success** |
| Flat datasets (LeanDojo, miniF2F) | **Navigable knowledge graph** |
| Tactic generation focus | **End-to-end autoformalization** |
| Closed systems dominate (AlphaProof) | **Open-source alternative** |

---

## II. Research Directions

### Priority Structure

| Priority | Papers | Focus |
|----------|--------|-------|
| **MVP (Year 1)** | 1, 2, 4 | Core infrastructure + flagship contribution |
| **Phase 2 (Year 2)** | 5, 7 | Advanced applications |
| **Long-term** | 8 | Aspirational research |
| **Fold into core** | 3, 6 | Methodology sections, not standalone |

### Overview

| # | Direction | Core Contribution | Priority |
|---|-----------|-------------------|----------|
| **1** | Mathematical Knowledge Graph | Mathematics as navigable structure | **MVP** |
| **2** | Compiler-Driven Proof Generation | Deterministic iteration with formal verification | **MVP** |
| **3** | Dataset Projection Framework | Graph → multiple training formats | *Fold into 1/4* |
| **4** | Autoformalization Modeling | NL → complete proof (novel task) | **MVP** |
| **5** | Proactive Discovery Agents | Autonomous frontier exploration | Phase 2 |
| **6** | Measurability Framework | Quantifying formalizability | *Fold into 1* |
| **7** | Cross-Domain Transfer | Structural analogies across fields | Phase 2 |
| **8** | Incompleteness Detection | Gödel-aware mathematical AI | Long-term |

---

## III. MVP Papers (Deep Focus)

### Paper 1: Mathematical Knowledge Graph

**Title**: *A Graph-Theoretic Representation of Mathematical Knowledge for Machine Reasoning*

**Target Venues**: ITP 2026, AKBC, NeurIPS

#### Thesis

Mathematics possesses inherent structure—dependencies, generalizations, analogies—that flat datasets destroy. Existing knowledge graphs (MMLKG, AutoMathKG) focus on *retrieval* for tactic generation. We focus on **navigation**: enabling AI agents to explore theory boundaries, detect frontiers, and support curriculum learning.

#### Formal Schema

**Nodes** (Mathematical Postulates):

| Type | Definition |
|------|------------|
| `Axiom` | Foundational assumption, not proven |
| `Definition` | Introduces a mathematical object or concept |
| `Theorem` | Statement proven from axioms and prior theorems |
| `Lemma` | Auxiliary result used in proofs |
| `Corollary` | Direct consequence of a theorem |

**Edges** (Relationships):

| Edge Type | Semantics | Example |
|-----------|-----------|---------|
| `DEPENDS_ON` | A requires B in its proof | First Isomorphism → Kernel Definition |
| `GENERALIZES` | A is a special case of B | Abelian Group → Group |
| `RELATES_TO` | Semantic similarity (cosine > θ) | Group First Iso ↔ Ring First Iso |
| `PART_OF` | Hierarchical containment | Theorem → Theory → Family |

**Hierarchy**:

```
Family (6)
  └── Theory (20)
        └── Postulate (~800)
```

#### Novelty Claim

> **Distinction from prior work**: MMLKG (2023) and AutoMathKG (2025) optimize for *premise retrieval*. Our graph optimizes for *navigation*—curriculum generation, frontier detection, and agent exploration.

#### Current Assets

| Asset | Status |
|-------|--------|
| 20 Knowledge Bases | Complete (Markdown) |
| ~800 Statements | NL + Lean templates |
| Measurability Scores | 0-100 per theory |
| Dependency Schema | Defined |

#### Gaps to Address

1. Graph database implementation (NetworkX MVP, Neo4j at scale)
2. Formal graph property analysis (degree distribution, centrality)
3. Embedding generation for `RELATES_TO` edges
4. Community validation with Lean ecosystem

---

### Paper 2: Compiler-Driven Proof Generation

**Title**: *Deterministic Proof Synthesis via Compiler-in-the-Loop Iteration*

**Target Venues**: CADE 2027, ICML, ITP

#### Thesis

Existing neural theorem provers treat proof search as **probabilistic**—sampling tactics, exploring proof trees. We propose a **deterministic** alternative: the Lean compiler as oracle, providing exact error feedback that guides targeted refinement.

This is not search. It is **iterative compilation** with structured error analysis.

#### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PROOF-ENGINEER AGENT                  │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐ │
│  │ GATHER  │ → │ ATTEMPT │ → │ VERIFY  │ → │ REFINE  │ │
│  │ context │   │ proof   │   │ compile │   │ fix     │ │
│  └─────────┘   └─────────┘   └────┬────┘   └────┬────┘ │
│                                   │              │      │
│                              ┌────▼────┐    ┌───▼────┐ │
│                              │  Lean   │    │ Skills │ │
│                              │Compiler │    │ (14)   │ │
│                              └─────────┘    └────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Error → Skill Mapping**:

| Error Pattern | Activated Skill |
|---------------|-----------------|
| `unknown identifier` | lean-tp-tactics (import resolution) |
| `type mismatch` | lean-fp-type-classes (coercion) |
| `failed to synthesize` | lean-fp-dependent-types (instance) |
| `sorry` placeholder | lean-tp-tactic-selection (proof search) |

#### Novelty Claim

> **Distinction from prior work**: ReProver uses best-first search. AlphaProof uses RL with test-time search. We use **deterministic skill-based iteration**—interpretable, debuggable, modular. Complements RL approaches for systematic error handling.

| Aspect | Search (ReProver, LIMO) | RL (AlphaProof) | Ours |
|--------|------------------------|-----------------|------|
| Mechanism | Sample tactics, explore tree | Learn policy, value functions | Compile, analyze error, fix |
| Feedback | Binary (success/fail) | Reward signal | Structured (error type, location) |
| Strength | Creative exploration | Novel problem solving | Systematic debugging |

#### Current Assets

| Asset | Status |
|-------|--------|
| proof-engineer agent | Defined (agents/proof-engineer.md) |
| 14 Lean skills | Complete (agents/skills/) |
| Two-stage pipeline | Documented (dataset_schema.md) |
| Error taxonomy | Defined (7 categories) |

#### Gaps to Address

1. Quantitative evaluation on 500+ theorems
2. Ablation studies (skills, iterations)
3. Comparison with search-based methods
4. Throughput measurement (critical for scaling)

---

### Paper 4: Autoformalization Modeling

**Title**: *Open-Source Autoformalization: From Natural Language to Verified Lean Proofs*

**Target Venues**: NeurIPS 2026 Datasets & Benchmarks, EMNLP

#### Thesis

**Autoformalization** (NL → complete formal proof) is fundamentally different from **tactic generation** (proof state → next tactic). Existing open-source work focuses on tactics; closed systems (AlphaProof) dominate autoformalization. We provide an open-source alternative.

#### Task Definition

```
Input:  "For any group homomorphism f: G → H, G/ker(f) is isomorphic to im(f)"
Output: theorem first_iso (f : G →* H) : G ⧸ MonoidHom.ker f ≃* MonoidHom.range f :=
          QuotientGroup.quotientKerEquivRange f
```

This is **NOT** tactic generation:
- Input is natural language, not proof state
- Output is complete proof, not single tactic
- No interactive refinement assumed

#### Novelty Claim

> **This is the #1 community need** (Terence Tao's AI for Math Fund, Dec 2024). Open-source autoformalization success rates are 15-26%. Reaching 50-60% on our benchmark would be a significant contribution.

#### Competitive Landscape

| System | Type | Performance | Status |
|--------|------|-------------|--------|
| AlphaProof | RL + Autoformalization | IMO Gold (via Seed-Prover) | **Closed** |
| FormaRL | RL Autoformalization | 26% ProofNet | Open |
| GPT-4/Claude | Zero-shot | 15-25% | Commercial |
| **Ours (target)** | KB + Compiler-driven | **50-60%** | **Open** |

#### Current Assets

| Asset | Status |
|-------|--------|
| 800 NL-Lean pairs | Templates ready |
| Validation pipeline | Designed (v5.0 schema) |
| Training strategy | Documented |

#### Gaps to Address

1. Validate 500+ theorems via proof-engineer
2. Fine-tune base model (DeepSeek-R1 or similar)
3. Measure success rate (target: >50%)
4. Baseline comparisons (GPT-4, Claude, DeepSeek-Prover)

---

## IV. Phase 2 Papers (Outlines)

### Paper 5: Proactive Discovery Agents

Subagent systems that autonomously explore the mathematical knowledge graph, identifying frontiers (sparse inter-theory connections), suggesting new theorems, and proposing analogies. **Depends on**: Papers 1, 2, 4 validated.

### Paper 7: Cross-Domain Transfer

Structural analogies between mathematical fields (group theory ↔ ring theory). Embeddings that respect graph structure enable transfer learning. **Aligns with Tao's vision**: "AI connecting mathematical fields."

---

## V. Long-Term Research

### Paper 8: Incompleteness Detection

The Gödel frontier. Can we detect statements that may be undecidable? Self-referential patterns, independence results, statements at the edge of axiomatic systems.

**Status**: Aspirational. No comparable work exists (likely because extremely hard). Requires Papers 1-7 as foundation.

---

## VI. Research Roadmap

```
                    ┌──────────────────┐
                    │  Paper 1:        │
                    │  Knowledge Graph │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │  Paper 2:   │  │  Paper 4:   │  │  (Paper 6:  │
    │  Proof Gen  │  │  Autoformal │  │  Measurable)│
    └──────┬──────┘  └──────┬──────┘  └─────────────┘
           │                │               ↑
           │                │         Fold into P1
           ▼                ▼
    ┌─────────────┐  ┌─────────────┐
    │  Paper 5:   │  │  Paper 7:   │
    │  Discovery  │  │  Transfer   │
    └──────┬──────┘  └──────┬──────┘
           │                │
           └───────┬────────┘
                   ▼
           ┌─────────────┐
           │  Paper 8:   │
           │ Incomplete  │
           └─────────────┘
```

### Timeline

| Milestone | Target | Venue |
|-----------|--------|-------|
| KB + Graph deployed | Q2 2025 | — |
| Proof-engineer validates 500 theorems | Q3 2025 | — |
| Autoformalization model trained | Q4 2025 | — |
| **Paper 1 submitted** | Q1 2026 | ITP 2026 |
| **Paper 4 submitted** | Q2 2026 | NeurIPS 2026 D&B |
| **Paper 2 submitted** | Q3 2026 | CADE 2027 |

---

## VII. Positioning

### Strategic Framing

**DO:**
- "Open-source alternative to closed mega-models"
- "Structured mathematical knowledge for AI agents"
- "Complements RL approaches with systematic debugging"

**DON'T:**
- Compete head-to-head with AlphaProof (resource asymmetry)
- Overpromise on Gödel work (high risk, unclear path)
- Ignore existing work (build on MMLKG, LeanDojo)

### Competitive Comparison

| Aspect | AlphaProof | DeepSeek-Prover | LeanDojo | **Ours** |
|--------|------------|-----------------|----------|----------|
| Availability | Closed | Open | Open | **Open** |
| Task | Autoformalization | Tactic gen | Tactic gen | **Autoformalization** |
| Structure | Unknown | Flat | Flat | **Knowledge graph** |
| Approach | RL + search | RL + search | Retrieval | **Compiler-driven** |

---

## VIII. Risk Assessment

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Proof-engineer doesn't scale to 5K+ | 30% | Start with 500, measure throughput early |
| Model plateaus at 30-40% (not 50-60%) | 40% | Hybrid approach (model + retrieval + symbolic) |
| Community doesn't adopt KBs | 25% | Open-source day 1, unique value (navigation API) |
| KG novelty questioned by reviewers | 50% | Clear differentiation (navigation vs. retrieval) |

---

## IX. Funding Opportunities

### AI for Math Fund (Terence Tao, Dec 2024)

- **Amount**: $9.2M initial funding
- **Focus**: Autoformalization, proof assistants, infrastructure
- **Our Fit**: Excellent (Papers 1, 4 directly address priorities)
- **Action**: Check Renaissance Philanthropy + XTX Markets for application

### Google DeepMind AI for Math Initiative (Dec 2024)

- **Resources**: Funding + access to Gemini Deep Think
- **Our Fit**: Good (may require academic affiliation)

---

## X. References

### Project Documentation

- [`README.md`](../README.md) — Project overview
- [`UNIVERSE_EXPANSION.md`](../UNIVERSE_EXPANSION.md) — Knowledge space architecture
- [`dataset/dataset_schema.md`](../dataset/dataset_schema.md) — v5.0 schema
- [`agents/proof-engineer.md`](../agents/proof-engineer.md) — Proof agent

### Key External References

- Hofstadter, D. (1979). *Gödel, Escher, Bach*
- AlphaProof (Nature, Jan 2025). *Olympiad-level formal mathematical reasoning with RL*
- LeanDojo (NeurIPS 2023). *Theorem Proving with Retrieval-Augmented LMs*
- Autoformalization Survey (arXiv 2025). *Autoformalization in the Era of LLMs*
- Tao, T. (Dec 2024). *AI for Math Fund announcement*

### Existing Knowledge Graph Work

- MMLKG (Nature 2023). *Mizar Mathematical Library Knowledge Graph*
- AutoMathKG (arXiv 2025). *LLM-augmented mathematical KG*

---

*This document defines the validated research program for AI Mathematician. Papers 1, 2, 4 form the MVP; Papers 5, 7 extend to advanced applications; Paper 8 is long-term aspirational research toward Gödel-aware mathematical AI.*
