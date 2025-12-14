# Mathematical Knowledge Space: Universe Expansion Plan

**Project**: AI Mathematician
**Created**: 2025-12-14
**Status**: Planning Complete - Ready for Implementation

---

## Executive Summary

Transform 17 knowledge bases (564 theorems) from a simple training dataset into a **navigable mathematical knowledge space** supporting:

1. **Autoformalization Training** - NL→Lean4 pairs (existing use case)
2. **Theory Exploration** - Navigate frontiers between mathematical theories
3. **Insight Generation** - Discover cross-domain connections via embeddings
4. **Incompleteness Detection** - Flag potentially undecidable statements (Gödel-relevant)
5. **Subagent Navigation** - AI agents query as datasource for research tasks

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│              MATHEMATICAL KNOWLEDGE SPACE                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   │
│  │ JSONL Store │   │ NetworkX    │   │ pgvector        │   │
│  │ (Primary)   │   │ (Relations) │   │ (Embeddings)    │   │
│  └──────┬──────┘   └──────┬──────┘   └────────┬────────┘   │
│         └─────────────────┴───────────────────┘            │
│                           │                                 │
│                 ┌─────────▼─────────┐                      │
│                 │ MathKnowledgeSpace│                      │
│                 │   (Query API)     │                      │
│                 └───────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

**Scale Thresholds**:
- Neo4j migration: >5,000 nodes
- Pinecone migration: >50,000 vectors

---

## Postulate Schema

Each mathematical postulate (theorem, axiom, lemma, corollary, definition) stored as:

```json
{
  "postulate_id": "set_theory.zfc_extensionality",
  "type": "axiom",
  "theory": "set_theory",
  "family": "foundations",
  "nl_statement": "Two sets are equal iff they have the same elements",
  "lean_template": "axiom ZFSet.ext : ∀ x y : ZFSet, (∀ z, z ∈ x ↔ z ∈ y) → x = y",
  "imports": ["Mathlib.SetTheory.ZFC.Basic"],
  "proof": {
    "status": "template",
    "difficulty": "easy",
    "lean_validated": null,
    "validation_attempts": []
  },
  "dependencies": {
    "depends_on": [],
    "used_by": ["set_theory.empty_unique", "set_theory.pairing"],
    "related": ["order_theory.antisymmetry"]
  },
  "mathlib_coverage": "full",
  "measurability_score": 98,
  "embedding": {
    "vector": [0.12, -0.34, ...],
    "model": "all-mpnet-base-v2"
  }
}
```

**Field Conventions**: snake_case, flat primary fields, nested metadata

**Full Schema**: See [`dataset/dataset_schema.md`](dataset/dataset_schema.md) for v5.0 specification with proof validation pipeline.

---

## Graph Structure

**Nodes**:
- `Postulate` (564 theorems/axioms)
- `Theory` (17 domains)
- `Family` (6 families: foundations, algebra, analysis, topology, geometry, discrete)

**Edges**:
- `DEPENDS_ON` - Theorem uses lemma in proof
- `PART_OF` - Postulate → Theory → Family
- `RELATES_TO` - Semantic similarity (cosine > 0.8)
- `GENERALIZES` - General case → Special case

**Example Frontier Query** (Cypher-style):
```cypher
MATCH (p1:Postulate)-[r:DEPENDS_ON]->(p2:Postulate)
WHERE p1.family <> p2.family
WITH p1.family AS f1, p2.family AS f2, COUNT(r) AS connections
WHERE connections < 5
RETURN f1, f2, connections ORDER BY connections
```

---

## Implementation Roadmap

### Phase 0: Dataset Documentation (Complete)

**Deliverables**: Updated schema and training pipeline docs

| File | Purpose |
|------|---------|
| [`dataset/dataset_schema.md`](dataset/dataset_schema.md) | v5.0 schema with two-stage pipeline |
| [`dataset/rl_dataset_analysis.md`](dataset/rl_dataset_analysis.md) | Training strategy + proof-engineer workflow |

**Key Design: Two-Stage Pipeline**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Knowledge Base │    │  Proof Engineer │    │ Training Dataset│
│  (NL + Lean     │ → │  (Validation)   │ → │  (Verified)     │
│   templates)    │    │  compiles=?     │    │  compiles=true  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

- **Stage 1**: KBs contain NL statements + Lean templates (may not compile)
- **Stage 2**: `proof-engineer` agent validates proofs via Lean compiler
- **Training**: Only `proof.status: validated` records enter training

See [`dataset/dataset_schema.md`](dataset/dataset_schema.md) for full schema specification.

---

### Phase 1: Schema Migration (Weeks 1-2)

**Deliverables**: `data/postulates/*.jsonl.gz` (17 files, ~564 records)

| Task | Description |
|------|-------------|
| Define Pydantic schema | Validate postulate structure with types |
| Build markdown parser | Regex-based extraction from KB files |
| Generate hierarchical IDs | Format: `{theory}.{theorem_name}` |
| Validate data quality | Schema compliance, uniqueness, referential integrity |
| Extract dependencies | Coarse-grained from Lean imports |

**Success Criteria**:
- All 564 postulates converted to JSONL
- Zero schema validation errors
- ID uniqueness verified

---

### Phase 2: Graph + Embeddings (Weeks 3-4)

**Deliverables**: NetworkX graph, pgvector indexed

| Task | Description |
|------|-------------|
| Build NetworkX DiGraph | 564 nodes, ~1,500 estimated edges |
| Generate embeddings | `all-mpnet-base-v2` on `"{domain} | {nl_statement}"` |
| Load to pgvector | PostgreSQL with HNSW index |
| Create evaluation set | 50 labeled pairs for similarity testing |

**Embedding Strategy** (ML Research Expert recommendation):
- **Model**: `sentence-transformers/all-mpnet-base-v2` (768-dim, open-source)
- **Input**: `"{theory} | {natural_language_statement}"`
- **Metric**: Cosine similarity
- **Hybrid**: Add Lean structural features IF P@5 < 0.7

**Success Criteria**:
- All postulates have embeddings
- Graph connectivity: 3-8 edges per node average
- HNSW index query latency < 50ms

---

### Phase 3: Query API (Weeks 5-6)

**Deliverables**: `MathKnowledgeSpace` Python class

```python
class MathKnowledgeSpace:
    def get_training_pairs(
        self,
        difficulty: str | None = None,
        theory: str | None = None,
        limit: int = 100
    ) -> List[TrainingPair]:
        """Get NL→Lean4 pairs for autoformalization training."""

    def find_frontiers(
        self,
        min_sparsity: float = 0.3
    ) -> List[TheoryPair]:
        """Find sparse connection regions between theories."""

    def find_similar(
        self,
        postulate_id: str,
        k: int = 10,
        exclude_same_theory: bool = True
    ) -> List[SimilarityMatch]:
        """Find semantically similar postulates across domains."""

    def get_dependencies(
        self,
        postulate_id: str,
        max_depth: int = 3
    ) -> DependencyTree:
        """Get dependency tree for a postulate."""

    def assess_undecidability(
        self,
        postulate_id: str
    ) -> IncompletenessSignals:
        """Analyze postulate for Gödel-relevant signals."""
```

**Caching Strategy** (Data Analyst recommendation):
- Dependencies: 24-hour cache
- Similarity queries: 1-hour cache
- Frontier analysis: 1-week cache

**Success Criteria**:
- All 5 methods implemented and tested
- Response time < 200ms for cached queries
- Python package installable via pip

---

### Phase 4: Frontier Analysis (Weeks 7-8)

**Deliverables**: Multi-method frontier detection, visualizations

| Method | Description |
|--------|-------------|
| Edge Density | Statistical significance test for sparse regions |
| Betweenness Gap | Nodes bridging disconnected components |
| Community Boundary | Louvain clustering + inter-community edges |

**Visualizations** (Data Analyst recommendation):
- **Heatmap**: Theory × Theory connection density (Seaborn)
- **Force Graph**: Interactive postulate relationships (Plotly)
- **Dependency Tree**: Hierarchical proof structure (D3.js)

**Centrality Metrics** (Data Science Modeler recommendation):
- PageRank (influence propagation)
- In-Degree (foundational importance)
- Eigenvector (connection to important nodes)
- **NOT** Betweenness (bias toward narrow bridges, problematic for foundational theorems)

**Success Criteria**:
- Frontiers identified with statistical confidence
- Interactive visualizations deployable
- Export to PDF/PNG for documentation

---

### Phase 5: Validation (Weeks 9-10)

**Deliverables**: Quality metrics, iteration backlog

| Metric | Target | Remediation if Failed |
|--------|--------|----------------------|
| P@5 (similarity) | > 0.7 | Add Lean structural features to embeddings |
| Dependency coverage | > 90% | Manual annotation for Tier 1 postulates |
| Connectivity | 3-8 edges/node | Adjust similarity threshold |
| Silhouette score | > 0.5 | Tune community detection parameters |

**Validation Process**:
1. Sample 50 postulates across all theories
2. Human evaluation of top-5 similar results
3. Expert review of identified frontiers
4. Subagent prototype: can agent navigate to relevant postulates?

**Success Criteria**:
- All metrics meet targets
- Expert validation of frontier accuracy
- Subagent successfully queries knowledge space

---

## Specialist Recommendations Summary

### Embeddings (ML Research Expert)
- Start with NL-only embeddings
- Use `all-mpnet-base-v2` (open, reproducible, 768-dim)
- Add Lean features only if P@5 < 0.7
- Fine-tune on Mathlib triplets if needed (5K-10K examples)

### Storage (Data Engineer)
- MVP: JSONL + pgvector + NetworkX
- Scale: Neo4j at 5K+ nodes, Pinecone at 50K+ vectors
- Dependencies: Hybrid (Lean imports + LeanDojo + manual for Tier 1)

### Queries (Data Analyst)
- Cache aggressively (24h dependencies, 1h similarity)
- Visualize with Plotly (interactive) and Seaborn (publication)
- Track KPIs: coverage, connectivity, silhouette

### Graph Modeling (Data Science Modeler)
- Property graph over RDF (simpler, sufficient)
- Multi-method frontier detection (edge density + betweenness + community)
- GENERALIZES edge: hybrid detection (substring + NER + embeddings + rules)

---

## File Structure

```
ai-mathematician/
├── UNIVERSE_EXPANSION.md          # This file
├── knowledgebase/
│   ├── kb_index.yaml              # Existing KB index
│   ├── README.md                  # KB documentation
│   └── *_knowledge_base.md        # 17 KB files
├── data/                          # NEW
│   ├── postulates/
│   │   ├── set_theory.jsonl.gz
│   │   ├── arithmetic.jsonl.gz
│   │   └── ... (17 files)
│   └── index/
│       └── postulate_index.json
├── src/                           # NEW
│   └── math_knowledge_space/
│       ├── __init__.py
│       ├── schema.py              # Pydantic models
│       ├── parser.py              # MD → JSONL
│       ├── graph.py               # NetworkX operations
│       ├── embeddings.py          # pgvector operations
│       ├── api.py                 # MathKnowledgeSpace class
│       └── visualizations.py      # Plotly/Seaborn
└── tests/
    └── test_knowledge_space.py
```

---

## References

### Research Document
Full research synthesis: `~/.claude/context/research/mathematical-knowledge-space-design-2025-12-14.md`

### External Inspirations
- **LeanDojo** - Lean 4 data extraction, premise retrieval
- **Lean Blueprint** - Dependency tracking (Terence Tao's PFR project)
- **MathGloss** - Mathematical knowledge graph from web sources
- **MMLKG** - Mizar library as knowledge graph
- **AutoMathKG** (2025) - LLM-augmented KG with synthetic data

### Current Assets
- 17 knowledge bases with 564 postulates
- `kb_index.yaml` with measurability ordering
- Mathlib4 as ground truth for Lean syntax

---

## Next Steps

1. **Approve Plan** - Review this document with stakeholders
2. **Set Up Infrastructure** - PostgreSQL + pgvector, Python environment
3. **Begin Phase 1** - Define Pydantic schema, build parser
4. **Weekly Checkpoints** - Review progress against success criteria

---

*Generated by AI Mathematician project planning process*
