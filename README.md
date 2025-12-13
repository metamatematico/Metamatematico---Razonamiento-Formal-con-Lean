# AI Mathematician

[![Lean 4](https://img.shields.io/badge/Lean-4-blue.svg)](https://lean-lang.org/)
[![Mathlib](https://img.shields.io/badge/Mathlib-4-orange.svg)](https://github.com/leanprover-community/mathlib4)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A Lean 4 project containing **machine-verified formal proofs** of fundamental theorems in abstract algebra. These proofs are not just validated by tests or peer review—they are checked by a proof assistant, guaranteeing mathematical correctness.

---

## Table of Contents

- [Overview](#overview)
- [Theorems Proved](#theorems-proved)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Building the Project](#building-the-project)
- [Project Structure](#project-structure)
- [Mathematical Background](#mathematical-background)
- [Contributing](#contributing)

---

## Overview

This project demonstrates formal theorem proving in Lean 4 using the Mathlib library. It contains rigorous, machine-checked proofs of core isomorphism theorems from abstract algebra, including:

- **First Isomorphism Theorem for Groups**
- **First Isomorphism Theorem for Rings**
- **Fundamental properties of algebraic structures**

Each theorem is formalized using dependent type theory, ensuring that the proofs are constructive and verifiable by the Lean compiler.

---

## Theorems Proved

### 1. First Isomorphism Theorem for Groups

**File:** `AIMathematician/GroupIsomorphism.lean`

For any group homomorphism `f : G → H`:

| Result | Mathematical Statement | Lean Type |
|--------|------------------------|-----------|
| Kernel is normal | ker(f) is a normal subgroup of G | `Subgroup.Normal (MonoidHom.ker f)` |
| Image is subgroup | im(f) is a subgroup of H | `Subgroup H` |
| First Isomorphism Theorem | G / ker(f) ≅ im(f) | `G ⧸ ker(f) ≃* range(f)` |
| Surjective case | If f is surjective: G / ker(f) ≅ H | `G ⧸ ker(f) ≃* H` |

### 2. First Isomorphism Theorem for Rings

**File:** `AIMathematician/RingIsomorphism.lean`

For any ring homomorphism `f : R → S`:

| Result | Mathematical Statement | Lean Type |
|--------|------------------------|-----------|
| Kernel is ideal | ker(f) is a two-sided ideal of R | `Ideal R` |
| Image is subring | im(f) is a subring of S | `Subring S` |
| First Isomorphism Theorem | R / ker(f) ≅ im(f) | `R ⧸ ker(f) ≃+* range(f)` |
| Surjective case | If f is surjective: R / ker(f) ≅ S | `R ⧸ ker(f) ≃+* S` |

### 3. Abelian Group Properties

**File:** `AIMathematician/Basic.lean`

Educational custom definitions demonstrating:

| Result | Description |
|--------|-------------|
| Custom group structure | Self-contained group axioms without Mathlib |
| Abelian group definition | Extension with commutativity |
| Commutativity proof | Proof that abelian groups satisfy `a * b = b * a` |

---

## Prerequisites

Before building this project, ensure you have the following installed:

### 1. elan (Lean Version Manager)

```bash
# macOS / Linux
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh

# Verify installation
elan --version
```

### 2. Lean 4

Lean 4 will be automatically installed by elan based on the `lean-toolchain` file.

```bash
# Verify Lean is available
lean --version
```

### 3. just (Command Runner)

```bash
# macOS
brew install just

# Linux (cargo)
cargo install just

# Verify installation
just --version
```

---

## Installation

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/ai-mathematician.git
cd ai-mathematician
```

2. **Install Lean toolchain:**

```bash
# elan will read lean-toolchain and install the correct version
lake update
```

3. **Download Mathlib cache (recommended):**

```bash
lake exe cache get
```

This downloads pre-built Mathlib artifacts, significantly speeding up the first build.

---

## Building the Project

This project uses `just` as a command runner for common tasks.

### Available Commands

| Command | Description |
|---------|-------------|
| `just` | Build the project (default) |
| `just build` | Build the project |
| `just update` | Update lake dependencies |
| `just clean` | Clean build artifacts |
| `just fresh` | Clean and rebuild from scratch |
| `just run` | Run the executable |
| `just info` | Show project info |
| `just files` | List all Lean files |

### Quick Start

```bash
# First time setup
just update

# Build the project
just build

# If you encounter issues, try a fresh build
just fresh
```

### Manual Lake Commands

If you prefer using Lake directly:

```bash
# Update dependencies
lake update

# Build the project
lake build

# Clean build artifacts
lake clean
```

---

## Project Structure

```
ai-mathematician/
├── AIMathematician/
│   ├── Basic.lean              # Educational group/abelian group definitions
│   ├── GroupIsomorphism.lean   # First Isomorphism Theorem for Groups
│   └── RingIsomorphism.lean    # First Isomorphism Theorem for Rings
├── AIMathematician.lean        # Root import file
├── Main.lean                   # Executable entry point
├── lakefile.toml               # Lake build configuration
├── lake-manifest.json          # Dependency lock file
├── lean-toolchain              # Lean version specification
├── justfile                    # Command runner recipes
└── README.md                   # This file
```

### Key Files

- **`lakefile.toml`**: Defines the project name, dependencies (Mathlib4), and build targets
- **`lean-toolchain`**: Specifies the exact Lean 4 version for reproducibility
- **`lake-manifest.json`**: Locks dependency versions for reproducible builds

---

## Mathematical Background

### The First Isomorphism Theorem

The First Isomorphism Theorem is a cornerstone of abstract algebra, providing a canonical way to understand the structure of homomorphic images.

#### For Groups

Given a group homomorphism `f : G → H`:

```
         f
    G ───────→ H
    │          ↑
    │ π        │ ι (injection)
    ↓          │
  G/ker(f) ──→ im(f)
           ≃
```

**Statement:** The quotient group `G/ker(f)` is isomorphic to the image `im(f)`.

In symbols: **G / ker(f) ≃ im(f)**

When `f` is surjective: **G / ker(f) ≃ H**

#### For Rings

The ring version preserves both addition and multiplication:

**Statement:** The quotient ring `R/ker(f)` is ring-isomorphic to the image `im(f)`.

In symbols: **R / ker(f) ≃+* im(f)**

The notation `≃+*` indicates a ring isomorphism (preserving both `+` and `*`).

### Why Formal Proofs Matter

Traditional mathematical proofs rely on human verification, which can miss subtle errors. Formal proofs in Lean provide:

1. **Machine-checked correctness**: Every logical step is verified by the Lean kernel
2. **No hidden assumptions**: All dependencies are explicit
3. **Constructive content**: Proofs can be extracted as algorithms when applicable
4. **Reusability**: Theorems can be composed to prove more complex results

---

## Contributing

Contributions are welcome! Here are some ways to help:

### Adding New Theorems

1. Create a new `.lean` file in `AIMathematician/`
2. Import it from `AIMathematician.lean`
3. Follow Mathlib conventions for naming and style
4. Ensure `just build` passes before submitting

### Theorem Ideas

- Second and Third Isomorphism Theorems
- Lagrange's Theorem
- Cayley's Theorem
- Structure theorems for finitely generated abelian groups
- Fundamental theorem of Galois theory

### Style Guidelines

- Use Mathlib's existing definitions and theorems where possible
- Provide docstrings for public definitions
- Include both term-mode and tactic-mode proofs where instructive

---

## References

- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
- [Mathlib Documentation](https://leanprover-community.github.io/mathlib4_docs/)
- [Functional Programming in Lean](https://lean-lang.org/functional_programming_in_lean/)
- [Abstract Algebra (Dummit and Foote)](https://www.wiley.com/en-us/Abstract+Algebra%2C+3rd+Edition-p-9780471433347)

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

**Note:** This project is part of an exploration into AI-assisted formal mathematics, combining human mathematical intuition with machine verification.
