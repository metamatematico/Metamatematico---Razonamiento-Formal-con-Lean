# Metamath Prover

[![Lean 4](https://img.shields.io/badge/Lean-4-blue.svg)](https://lean-lang.org/)
[![Mathlib](https://img.shields.io/badge/Mathlib-4-orange.svg)](https://github.com/leanprover-community/mathlib4)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Part of [metamathematics.ai](https://metamathematics.ai)** — Machine-verified proofs and research toward automating mathematical formalization.

---

## Vision

This project explores the **digitalization of mathematics**: converting human mathematical knowledge into machine-verifiable Lean 4 proofs. We develop verified proofs, research methodologies, and agent-based tools for automated theorem proving.

**Related Repository:** The mathematical knowledge bases and extraction pipeline are in [metamath-knowledge-space](https://github.com/ai-enhanced-engineer/math-knowledge-space).

---

## Repository Structure

```
metamath-prover/
├── MetamathProver/               # Verified Lean 4 proofs
│   ├── Group/                    # Group theory proofs
│   └── Ring/                     # Ring theory proofs
│
├── research/                     # Research documentation
│   ├── PROJECT_PROPOSAL.md       # Formal research proposal
│   ├── RESEARCH_PROPOSALS.md     # Research program overview
│   ├── rl_dataset_analysis.md    # Training pipeline strategy
│   └── *.md                      # Foundational research
│
├── agents/                       # Claude Code Agent Definitions
│   ├── proof-engineer.md         # Lean 4 theorem proving agent
│   ├── skills/                   # 14 Lean skills for tactics
│   └── WORKFLOWS.md              # Agent workflows
│
├── lakefile.toml                 # Lake build configuration
├── lean-toolchain                # Lean version
└── justfile                      # Command runner
```

---

## Verified Proofs

The `MetamathProver/` directory contains machine-verified Lean 4 proofs:

| Theorem | Statement | Location |
|---------|-----------|----------|
| First Isomorphism (Groups) | G / ker(f) ≃* im(f) | `Group/` |
| First Isomorphism (Rings) | R / ker(f) ≃+* im(f) | `Ring/` |
| Kernel is Normal Subgroup | ker(f) ⊲ G | `Group/` |
| Kernel is Two-Sided Ideal | ker(f) is ideal | `Ring/` |

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
git clone https://github.com/ai-enhanced-engineer/metamath-prover.git
cd metamath-prover

# Download Mathlib cache (recommended)
lake exe cache get

# Build
just build
```

### Commands

| Command | Description |
|---------|-------------|
| `just build` | Build the Lean project |
| `just update` | Update lake dependencies |
| `just clean` | Clean and rebuild from scratch |
| `just cache` | Download Mathlib cache |
| `just docs` | Generate research documentation (HTML/PDF) |

---

## Research

The `research/` directory contains:

| Document | Description |
|----------|-------------|
| `PROJECT_PROPOSAL.md` | Formal research proposal for AI mathematician |
| `RESEARCH_PROPOSALS.md` | Research program and priorities |
| `rl_dataset_analysis.md` | Training pipeline for autoformalization |
| `MODERN_FOUNDATIONS_OF_MATHEMATICS.md` | Foundational systems context |
| `LEAN_SOUNDNESS_SUMMARY.md` | Lean type-checking guarantees |

---

## Proof Engineer Agent

The [`agents/proof-engineer.md`](agents/proof-engineer.md) defines a Claude Code agent for automated theorem proving with 14 specialized Lean skills:

- Tactic selection and application
- Error diagnosis and resolution
- Proof construction strategies
- Mathlib lemma discovery

See [`agents/README.md`](agents/README.md) for usage.

---

## Related Projects

| Repository | Purpose |
|------------|---------|
| [math-knowledge-space](https://github.com/ai-enhanced-engineer/math-knowledge-space) | 51 mathematical knowledge bases, extraction pipeline, postulate data |

---

## Contributing

### Adding Verified Proofs
1. Create a `.lean` file in `MetamathProver/`
2. Import in `MetamathProver.lean`
3. Ensure `just build` passes

### Research Contributions
1. Add documentation to `research/`
2. Follow existing format and citation style

---

## References

- [Mathlib4 Documentation](https://leanprover-community.github.io/mathlib4_docs/)
- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
- [100 Theorems in Lean](https://leanprover-community.github.io/100.html)

---

## License

MIT License. See [LICENSE](LICENSE) for details.
