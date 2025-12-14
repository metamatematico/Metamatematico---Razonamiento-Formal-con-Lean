# Knowledge Bases

Mathematical knowledge bases pairing natural language explanations with Lean 4/Mathlib4 formal definitions. Used for autoformalization dataset generation.

## Quick Stats

| Metric | Count |
|--------|-------|
| **Knowledge Bases** | 20 |
| **Mathematical Families** | 6 |
| **Theorems** | ~390 |
| **Definitions** | ~250 |
| **Axioms** | ~97 |
| **Lemmas** | ~50 |
| **Corollaries** | ~5 |
| **Total Statements** | ~800+ |

*Counts are approximate (grep-based). Rigorous analysis pending.*

## Index

See **[kb_index.yaml](kb_index.yaml)** for:
- All 20 KBs ordered by measurability score
- Dependencies between KBs
- Mathlib coverage status
- Dataset generation priority

## Quick Reference

| Priority | KBs | Measurability |
|----------|-----|---------------|
| 1 | set_theory, arithmetic, order_theory, isomorphism_theorems | 90-98 |
| 2 | linear_algebra, category_theory, topology, measure_theory, combinatorics, real_complex_analysis, logic_model_theory | 82-92 |
| 3 | galois_theory, probability_theory, homological_algebra, graph_theory, prime_number_theorems, representation_theory | 70-80 |
| 4 | classical_geometry, algebraic_topology, differential_geometry | 50-60 |

## Usage

```python
import yaml

with open('knowledgebase/kb_index.yaml') as f:
    index = yaml.safe_load(f)

# Process in measurability order
for kb in sorted(index['knowledge_bases'],
                 key=lambda x: x['measurability']['score'],
                 reverse=True):
    print(f"{kb['id']}: {kb['measurability']['score']}")
```

## KB Format

Each knowledge base follows this structure:

```markdown
# Topic Knowledge Base

**Domain**: ...
**Lean 4 Coverage**: FULL/PARTIAL
**Source**: Mathlib4 modules
**Last Updated**: YYYY-MM-DD

## Section N: Topic
### N.M Definition/Theorem Name
**NL Statement**: Plain English explanation
**Lean 4**: Formal definition/theorem
**Imports**: Mathlib path
**Difficulty**: easy/medium/hard
```

## Mathematical Families

| Family | KBs | Avg Score |
|--------|-----|-----------|
| **Foundations** | set_theory (98), arithmetic (96), order_theory (95), logic_model_theory (82) | **93** |
| **Algebra** | linear_algebra (92), isomorphism_theorems (90), category_theory (88), galois_theory (80), homological_algebra (78), representation_theory (70) | **83** |
| **Analysis** | measure_theory (85), real_complex_analysis (82), probability_theory (78) | **82** |
| **Discrete** | combinatorics (85), graph_theory (75), prime_number_theorems (72) | **77** |
| **Topology** | topology (88), algebraic_topology (55) | **72** |
| **Geometry** | classical_geometry (60), differential_geometry (50) | **55** |

## Measurability Score Methodology

The **measurability score** (0-100) estimates how readily a KB's theorems can be formalized in Lean 4 using Mathlib. Higher scores indicate easier formalization.

### Scoring Criteria

| Factor | Weight | Description |
|--------|--------|-------------|
| **Mathlib Coverage** | 40% | Percentage of theorems already in Mathlib or with direct analogs |
| **Gap Severity** | 25% | Impact of missing theorems (core vs. peripheral) |
| **Verification Ease** | 20% | Complexity of proof tactics required (simp vs. custom automation) |
| **Type Class Maturity** | 15% | Stability of underlying algebraic hierarchy (e.g., Ring, Module instances) |

### Score Bands

| Band | Range | Interpretation |
|------|-------|----------------|
| **FULL** | 90-100 | All theorems directly available in Mathlib |
| **HIGH** | 80-89 | Most theorems available, minor gaps fillable |
| **GOOD** | 70-79 | Core theorems available, some significant gaps |
| **PARTIAL** | 50-69 | Key theorems missing or require substantial work |
| **LIMITED** | <50 | Major infrastructure gaps, research-level formalization |

### Why These Scores?

**Foundations (93 avg)**: ZFC axioms, Peano arithmetic, and order theory are Mathlib's bedrock. These are the most stable, thoroughly tested parts of the library.

**Algebra (83 avg)**: Strong typeclass infrastructure for groups, rings, modules. Isomorphism theorems and linear algebra are well-supported. Advanced topics (Galois, representation theory) have gaps.

**Analysis (82 avg)**: Measure theory and real analysis have excellent Bochner integral framework. Probability theory lags due to CLT complexity.

**Discrete (77 avg)**: Combinatorics has good BigOperators support. Graph theory and number theory have notable gaps (Four Color Theorem external, PNT in progress).

**Topology (72 avg)**: General topology is excellent (filter-based). Algebraic topology drags down the average due to missing singular homology and homotopy groups.

**Geometry (55 avg)**: Euclidean geometry works via inner product spaces, but many classical theorems (Ceva, Desargues) are missing. Differential geometry has manifold infrastructure but lacks Stokes' theorem and de Rham cohomology.
