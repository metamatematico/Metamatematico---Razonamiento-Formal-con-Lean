# AI Mathematician

[![Lean 4](https://img.shields.io/badge/Lean-4-blue.svg)](https://lean-lang.org/)
[![Mathlib](https://img.shields.io/badge/Mathlib-4-orange.svg)](https://github.com/leanprover-community/mathlib4)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Digitalization of Mathematics** — A structured representation of mathematical knowledge designed for autoformalization, discovery, and training AI systems to reason formally.

---

## Vision

Mathematics exists primarily in natural language—textbooks, papers, lectures. This project aims to **digitalize mathematics**: converting human mathematical knowledge into machine-verifiable Lean 4 proofs organized as a queryable knowledge graph.

The result is a **Mathematical Knowledge Space** where:
- Theorems, definitions, and axioms are nodes
- Dependencies and relationships are edges
- Each statement has natural language, LaTeX, and Lean 4 representations
- Formalization readiness is measured and tracked

---

## Motivation: The Metamathematical Program

> *"The study of mathematics itself became known as metamathematics—or occasionally, metalogic, since mathematics and logic are so intertwined. The most urgent priority of metamathematicians was to determine the true nature of mathematical reasoning. What is a legal method of procedure, and what is an illegal one? Since mathematical reasoning had always been done in "natural language" (e.g., French or Latin or some language for normal communication), there was always a lot of possible ambiguity. Words had different meanings to different people, conjured up different images, and so forth. It seemed reasonable and even important to establish a single uniform notation in which all mathematical work could be done, and with the aid of which any two mathematicians could resolve disputes over whether a suggested proof was valid or not. This would require a complete codification of the universally acceptable modes of human reasoning, at least as far as they applied to mathematics."*
>
> — Douglas Hofstadter, *Gödel, Escher, Bach: An Eternal Golden Braid* (1979)

### The Problem Hofstadter Identified

| Problem | Our Solution |
|---------|--------------|
| Ambiguity of natural language | Dual representation: NL for humans, Lean 4 for machines |
| Words mean different things to different people | Type system enforces precise, unambiguous definitions |
| Need for uniform notation | Mathlib provides standardized mathematical vocabulary |
| Disputes over proof validity | The Lean compiler is the ultimate arbiter—no ambiguity remains |

### What We Add: Beyond Codification

The metamathematicians of the early 20th century—Frege, Russell, Hilbert, Gödel—worked by hand. We extend their program with:

- **Organization** (Knowledge Graph) — How do proofs relate to each other?
- **Measurement** (Measurability Scores) — What is formalizable now vs. later?
- **Discovery** (Frontier Analysis) — Where are the gaps between mathematical branches?
- **Scale** (Automation) — 36 knowledge bases, ~1,600 statements, continuous validation

The `proof-engineer` agent continuously asks Hofstadter's question: *"Is this a legal method of procedure?"*

When Lean accepts a proof, it certifies that every step follows from the rules of type theory. When it rejects, the reasoning was "illegal." This is applied metamathematics at industrial scale.

---

## Knowledge Space Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                   Mathematical Knowledge Space                        │
├──────────────────────────────────────────────────────────────────────┤
│  Families (7)                                                        │
│    ├── Foundations: set_theory, arithmetic, order_theory, logic,     │
│    │                computability_theory                             │
│    ├── Algebra: linear_algebra, groups, rings, categories,          │
│    │            commutative_algebra, algebraic_number_theory,        │
│    │            lie_theory, algebraic_geometry                       │
│    ├── Analysis: real/complex, measure theory, probability,         │
│    │             functional_analysis, fourier_analysis,              │
│    │             convex_analysis, stochastic_processes, operator     │
│    ├── Dynamics: ergodic_theory, ordinary_differential_equations     │
│    ├── Topology: general topology, algebraic topology                │
│    ├── Geometry: classical, smooth_manifolds, differential           │
│    └── Discrete: graph theory, number theory, combinatorics,        │
│                  ramsey_theory, additive_combinatorics, p-adic       │
│                                                                      │
│  Theories (36 Knowledge Bases)                                       │
│    └── Postulates (~1,600 statements)                                │
│          └── Dependencies (DEPENDS_ON, GENERALIZES, RELATES_TO)      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Quick Stats

| Metric | Count |
|--------|-------|
| **Knowledge Bases** | 36 |
| **Mathematical Families** | 7 |
| **Theorems** | ~800 |
| **Definitions** | ~500 |
| **Axioms** | ~130 |
| **Total Statements** | ~1,600+ |

See [`knowledgebase/README.md`](knowledgebase/README.md) for detailed coverage and measurability scores.

---

## Two-Stage Pipeline

We separate **content authoring** from **Lean validation** to enable rapid knowledge base growth:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Knowledge Base │    │  Proof Engineer │    │ Training Dataset│
│  (NL + Lean     │ → │  (Validation)   │ → │  (Verified)     │
│   templates)    │    │  compiles=?     │    │  compiles=true  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
     Stage 1                Stage 2               Final Output
```

**Stage 1**: Experts write natural language statements + Lean templates (may use `sorry`)

**Stage 2**: The [`proof-engineer`](agents/proof-engineer.md) agent validates templates through the Lean compiler, using 14 specialized [Lean skills](agents/skills/) for tactic selection, error resolution, and proof construction

**Result**: Only verified proofs enter the training dataset

The agent and skills in [`agents/`](agents/) are the foundation for transforming mathematical knowledge into machine-verified proofs. See [`dataset/dataset_schema.md`](dataset/dataset_schema.md) for the v5.0 schema specification.

---

## Use Cases

### Autoformalization Training
Train models to translate natural language math → Lean 4 proofs:
```
Input:  "For any group homomorphism f: G → H, G/ker(f) is isomorphic to im(f)"
Output: theorem first_iso (f : G →* H) : G ⧸ MonoidHom.ker f ≃* MonoidHom.range f :=
          QuotientGroup.quotientKerEquivRange f
```

### Mathematical Discovery
- **Frontier Analysis**: Identify sparse connections between mathematical branches
- **Gap Detection**: Find theorems in literature not yet formalized
- **Dependency Mapping**: Understand theorem prerequisites

### Proof Assistance
- Provide context for theorem proving agents
- Suggest relevant lemmas via semantic similarity
- Track which results are available in Mathlib

---

## Repository Structure

```
ai-mathematician/
├── AIMathematician/              # Verified Lean 4 proofs
│   ├── Basic.lean                # Educational group definitions
│   ├── GroupIsomorphism.lean     # First Isomorphism Theorem (groups)
│   └── RingIsomorphism.lean      # First Isomorphism Theorem (rings)
│
├── knowledgebase/                # Mathematical Knowledge Bases
│   ├── kb_index.yaml             # Index of all 36 KBs with measurability
│   ├── README.md                 # KB documentation and methodology
│   └── *_knowledge_base.md       # 36 domain-specific KBs
│
├── dataset/                      # Dataset Schema & Training Strategy
│   ├── dataset_schema.md         # v5.0 JSONL schema specification
│   └── rl_dataset_analysis.md    # Training pipeline and evaluation
│
├── agents/                       # Claude Code Agent & Skill Definitions
│   ├── README.md                 # Usage and sync instructions
│   ├── proof-engineer.md         # Lean 4 theorem proving agent
│   └── skills/                   # Lean skill definitions
│       ├── README.md             # Skill documentation
│       └── lean-*/               # 14 Lean FP & theorem proving skills
│
├── lakefile.toml                 # Lake build configuration
├── lean-toolchain                # Lean version (reproducibility)
└── justfile                      # Command runner recipes
```

---

## Mathematical Families

| Family | Avg Score | KBs |
|--------|-----------|-----|
| **Foundations** | 90 | set_theory, arithmetic, order_theory, logic_model_theory, computability_theory |
| **Algebra** | 80 | linear_algebra, isomorphism_theorems, category_theory, galois_theory, homological_algebra, representation_theory, commutative_algebra, algebraic_number_theory, lie_theory, algebraic_geometry |
| **Analysis** | 82 | measure_theory, real_complex_analysis, probability_theory, functional_analysis, fourier_analysis, convex_analysis, stochastic_processes, operator_theory |
| **Dynamics** | 84 | ergodic_theory, ordinary_differential_equations |
| **Discrete** | 75 | combinatorics, graph_theory, prime_number_theorems, ramsey_theory, additive_combinatorics, p_adic_numbers |
| **Topology** | 72 | topology, algebraic_topology |
| **Geometry** | 75 | classical_geometry, smooth_manifolds, differential_geometry, algebraic_geometry |

*Scores indicate Mathlib coverage and formalization readiness (0-100)*

---

## Getting Started

### Prerequisites

```bash
# Install elan (Lean version manager)
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh

# Install just (command runner)
brew install just  # macOS
```

### Build

```bash
# Clone and enter
git clone https://github.com/yourusername/ai-mathematician.git
cd ai-mathematician

# Download Mathlib cache (recommended)
lake exe cache get

# Build
just build
```

### Available Commands

| Command | Description |
|---------|-------------|
| `just build` | Build the Lean project |
| `just update` | Update lake dependencies |
| `just clean` | Clean build artifacts |
| `just fresh` | Clean rebuild from scratch |

---

## Key Theorems (Verified)

The `AIMathematician/` directory contains machine-verified proofs:

| Theorem | Statement | File |
|---------|-----------|------|
| First Isomorphism (Groups) | G / ker(f) ≃ im(f) | `GroupIsomorphism.lean` |
| First Isomorphism (Rings) | R / ker(f) ≃+* im(f) | `RingIsomorphism.lean` |
| Kernel is Normal | ker(f) ⊲ G | `GroupIsomorphism.lean` |
| Kernel is Ideal | ker(f) is two-sided ideal | `RingIsomorphism.lean` |

---

## Contributing

### Adding Knowledge Base Content
1. Edit the relevant `knowledgebase/*_knowledge_base.md` file
2. Follow the existing format (NL statement, Lean template, imports, difficulty)
3. Update `kb_index.yaml` if adding new theorems

### Adding Verified Proofs
1. Create a `.lean` file in `AIMathematician/`
2. Import from `AIMathematician.lean`
3. Ensure `just build` passes

### Suggesting Theorems
Open an issue with:
- Natural language statement
- Mathematical domain
- Reference (if available)

---

## References

### Project Documentation
- [`knowledgebase/README.md`](knowledgebase/README.md) — KB coverage and measurability methodology
- [`dataset/dataset_schema.md`](dataset/dataset_schema.md) — v5.0 schema for JSONL records
- [`dataset/rl_dataset_analysis.md`](dataset/rl_dataset_analysis.md) — Training strategy and evaluation

### External Resources
- [Mathlib4 Documentation](https://leanprover-community.github.io/mathlib4_docs/)
- [100 Theorems in Lean](https://leanprover-community.github.io/100.html)
- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
- [LeanDojo](https://leandojo.org/) — Lean data extraction

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

*This project is part of an exploration into AI-assisted formal mathematics, combining human mathematical intuition with machine verification.*
