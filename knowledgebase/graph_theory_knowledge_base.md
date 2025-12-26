# Graph Theory Knowledge Base for Lean 4

**Generated:** 2025-12-14
**Purpose:** Research knowledge base for implementing graph theory in Lean 4 for dataset generation pairing formal proofs with natural language explanations.

---

## Overview

Graph theory studies structures consisting of vertices connected by edges. This knowledge base catalogs core definitions, structural theory, connectivity, coloring, and extremal results as formalized in Lean 4's Mathlib.

### Content Summary

| Category | Count | Description |
|----------|-------|-------------|
| **Core Definitions** | 6 | Simple graphs, adjacency, degree, special graphs |
| **Subgraphs & Morphisms** | 4 | Subgraphs, embeddings, homomorphisms |
| **Walks & Connectivity** | 5 | Walks, paths, trails, reachability |
| **Degree Theory** | 3 | Handshaking lemma and corollaries |
| **Bipartite Graphs** | 3 | Definition, characterization, properties |
| **Coloring** | 3 | Chromatic number, colorings |
| **Extremal Theory** | 2 | Turán's theorem |
| **Total** | 26 | Core graph theory |

### Mathlib Approach

Mathlib represents simple graphs as symmetric, irreflexive adjacency relations:

```lean
structure SimpleGraph (V : Type u) where
  Adj : V → V → Prop
  symm : Symmetric Adj
  loopless : Irreflexive Adj
```

**Primary Import:** `Mathlib.Combinatorics.SimpleGraph.Basic`

---

## Related Knowledge Bases

### Prerequisites
- **Set Theory** (`set_theory_knowledge_base.md`): Set operations, finiteness
- **Combinatorics** (`combinatorics_knowledge_base.md`): Counting principles, binomial coefficients

### Builds Upon This KB
- **Ramsey Theory** (`ramsey_theory_knowledge_base.md`): Graph Ramsey numbers
- **Additive Combinatorics** (`additive_combinatorics_knowledge_base.md`): Cayley graphs

### Related Topics
- **Algebraic Topology** (`algebraic_topology_knowledge_base.md`): Simplicial complexes from graphs
- **Coding Theory** (`coding_theory_knowledge_base.md`): Graph codes

### Scope Clarification
This KB focuses on **graph theory**:
- Simple graphs and adjacency
- Subgraphs and morphisms
- Walks, paths, and connectivity
- Degree theory and handshaking lemma
- Bipartite graphs
- Graph coloring
- Extremal results (Turán)

For **Ramsey-theoretic properties**, see **Ramsey Theory KB**.

---

## Part I: Core Definitions

### 1. Simple Graph

**Natural Language Statement:**
A simple graph G on vertex type V is defined by a symmetric, irreflexive adjacency relation. Edges are undirected (if u is adjacent to v, then v is adjacent to u) and there are no self-loops.

**Lean 4 Definition:**
```lean
structure SimpleGraph (V : Type u) where
  Adj : V → V → Prop
  symm : Symmetric Adj := by aesop_graph
  loopless : Irreflexive Adj := by aesop_graph
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Basic`

**Difficulty:** easy

---

### 2. Adjacency and Neighbors

**Natural Language Statement:**
Two vertices u and v are adjacent if there is an edge between them. The neighbor set of a vertex v is the set of all vertices adjacent to v.

**Lean 4 Definitions:**
```lean
-- Adjacency is the core relation from the structure
-- G.Adj u v means u and v are adjacent

def SimpleGraph.neighborSet (G : SimpleGraph V) (v : V) : Set V :=
  {w : V | G.Adj v w}

def SimpleGraph.edgeSet (G : SimpleGraph V) : Set (Sym2 V) :=
  Sym2.fromRel G.symm
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Basic`

**Note:** Edges are represented as unordered pairs using `Sym2` type.

**Difficulty:** easy

---

### 3. Degree

**Natural Language Statement:**
The degree of a vertex v is the number of edges incident to v, equivalently the number of neighbors of v.

**Lean 4 Definition:**
```lean
def SimpleGraph.degree [Fintype V] [DecidableRel G.Adj]
  (G : SimpleGraph V) (v : V) : ℕ :=
  (G.neighborFinset v).card
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Basic`

**Note:** Requires finite vertex type and decidable adjacency.

**Difficulty:** easy

---

### 4. Complete Graph

**Natural Language Statement:**
The complete graph on V has every pair of distinct vertices connected by an edge.

**Lean 4 Definition:**
```lean
instance : Top (SimpleGraph V) where
  top := { Adj := Ne, symm := fun _ _ => Ne.symm, loopless := fun _ => absurd rfl }

def completeGraph (V : Type*) : SimpleGraph V := ⊤
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Basic`

**Difficulty:** easy

---

### 5. Empty Graph

**Natural Language Statement:**
The empty graph on V has no edges between any vertices.

**Lean 4 Definition:**
```lean
instance : Bot (SimpleGraph V) where
  bot := { Adj := ⊥, symm := fun _ _ => id, loopless := fun _ => id }
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Basic`

**Difficulty:** easy

---

### 6. Complete Bipartite Graph

**Natural Language Statement:**
The complete bipartite graph on V and W has edges between every vertex in V and every vertex in W, but no edges within V or within W.

**Lean 4 Definition:**
```lean
def completeBipartiteGraph (V W : Type*) : SimpleGraph (V ⊕ W) where
  Adj := fun v w => (v.isLeft ∧ w.isRight) ∨ (v.isRight ∧ w.isLeft)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Basic`

**Difficulty:** easy

---

## Part II: Subgraphs and Morphisms

### 7. Subgraph

**Natural Language Statement:**
A subgraph H of graph G consists of a subset of vertices and a subset of edges such that endpoints of every edge in H are vertices of H, and every edge of H is an edge of G.

**Lean 4 Definition:**
```lean
structure SimpleGraph.Subgraph (G : SimpleGraph V) where
  verts : Set V
  Adj : V → V → Prop
  adj_sub : ∀ {v w}, Adj v w → G.Adj v w
  edge_vert : ∀ {v w}, Adj v w → v ∈ verts
  symm : Symmetric Adj := by aesop_graph
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Subgraph`

**Difficulty:** medium

---

### 8. Spanning and Induced Subgraphs

**Natural Language Statement:**
A subgraph is spanning if it contains all vertices of G. The induced subgraph on a vertex set S contains all edges of G whose endpoints are both in S.

**Lean 4 Definitions:**
```lean
def SimpleGraph.Subgraph.IsSpanning (H : G.Subgraph) : Prop :=
  H.verts = Set.univ

def SimpleGraph.Subgraph.IsInduced (H : G.Subgraph) : Prop :=
  ∀ {v w}, v ∈ H.verts → w ∈ H.verts → (H.Adj v w ↔ G.Adj v w)

def SimpleGraph.induce (G : SimpleGraph V) (s : Set V) : SimpleGraph s where
  Adj := fun v w => G.Adj v.val w.val
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Subgraph`

**Difficulty:** medium

---

### 9. Graph Homomorphism

**Natural Language Statement:**
A graph homomorphism f: G → H is a function on vertices that preserves adjacency: if u and v are adjacent in G, then f(u) and f(v) are adjacent in H.

**Lean 4 Definition:**
```lean
abbrev SimpleGraph.Hom (G : SimpleGraph V) (H : SimpleGraph W) :=
  RelHom G.Adj H.Adj

notation:25 G " →g " H => SimpleGraph.Hom G H
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Maps`

**Difficulty:** medium

---

### 10. Graph Embedding and Isomorphism

**Natural Language Statement:**
A graph embedding is an injective homomorphism that reflects adjacency (adjacent iff images adjacent). A graph isomorphism is a bijective embedding.

**Lean 4 Definitions:**
```lean
structure SimpleGraph.Embedding (G : SimpleGraph V) (H : SimpleGraph W)
  extends G →g H where
  inj' : Function.Injective toHom.toFun

notation:25 G " ↪g " H => SimpleGraph.Embedding G H

structure SimpleGraph.Iso (G : SimpleGraph V) (H : SimpleGraph W)
  extends G ↪g H where
  right_inv' : Function.RightInverse inv toEmbedding.toHom.toFun

notation:25 G " ≃g " H => SimpleGraph.Iso G H
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Maps`

**Difficulty:** medium

---

## Part III: Walks and Connectivity

### 11. Walk

**Natural Language Statement:**
A walk from u to v is a finite sequence of adjacent vertices starting at u and ending at v. Walks can repeat vertices and edges.

**Lean 4 Definition:**
```lean
inductive SimpleGraph.Walk (G : SimpleGraph V) : V → V → Type u
  | nil {u : V} : Walk G u u
  | cons {u v w : V} (h : G.Adj u v) (p : Walk G v w) : Walk G u w
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Connectivity.Walk`

**Difficulty:** medium

---

### 12. Path and Trail

**Natural Language Statement:**
A trail is a walk with no repeated edges. A path is a walk with no repeated vertices.

**Lean 4 Definitions:**
```lean
def SimpleGraph.Walk.IsTrail (p : G.Walk u v) : Prop :=
  p.edges.Nodup

def SimpleGraph.Walk.IsPath (p : G.Walk u v) : Prop :=
  p.support.Nodup
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Trails`, `Mathlib.Combinatorics.SimpleGraph.Path`

**Difficulty:** medium

---

### 13. Cycle

**Natural Language Statement:**
A cycle is a non-trivial closed trail (starts and ends at the same vertex, visits every edge at most once).

**Lean 4 Definition:**
```lean
def SimpleGraph.Walk.IsCycle (p : G.Walk u u) : Prop :=
  p.IsTrail ∧ p ≠ Walk.nil ∧ p.support.tail.Nodup
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Trails`

**Difficulty:** medium

---

### 14. Reachability

**Natural Language Statement:**
Vertex v is reachable from u if there exists a walk from u to v.

**Lean 4 Definition:**
```lean
def SimpleGraph.Reachable (G : SimpleGraph V) (u v : V) : Prop :=
  Nonempty (G.Walk u v)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Connectivity`

**Difficulty:** easy

---

### 15. Connected Graph

**Natural Language Statement:**
A graph is connected if every pair of vertices is reachable from each other.

**Lean 4 Definition:**
```lean
def SimpleGraph.Connected (G : SimpleGraph V) : Prop :=
  ∀ u v : V, G.Reachable u v

def SimpleGraph.ConnectedComponent (G : SimpleGraph V) : Type* :=
  Quotient G.Reachable.setoid
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Connectivity`

**Difficulty:** easy

---

## Part IV: Degree Theory

### 16. Handshaking Lemma

**Natural Language Statement:**
The sum of all vertex degrees equals twice the number of edges. Each edge contributes 1 to the degree of each of its two endpoints.

**Lean 4 Theorem:**
```lean
theorem SimpleGraph.sum_degrees_eq_twice_card_edges
  (G : SimpleGraph V) [Fintype V] [DecidableRel G.Adj] :
  ∑ v, G.degree v = 2 * G.edgeFinset.card
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.DegreeSum`

**Difficulty:** medium

---

### 17. Even Number of Odd-Degree Vertices

**Natural Language Statement:**
In any finite graph, the number of vertices with odd degree is even.

**Lean 4 Theorem:**
```lean
theorem SimpleGraph.even_card_odd_degree_vertices
  (G : SimpleGraph V) [Fintype V] [DecidableRel G.Adj] :
  Even (Finset.filter (fun v => Odd (G.degree v)) Finset.univ).card
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.DegreeSum`

**Difficulty:** medium

---

### 18. Existence of Paired Odd-Degree Vertices

**Natural Language Statement:**
If a graph has a vertex with odd degree, it must have at least one other vertex with odd degree.

**Lean 4 Theorem:**
```lean
theorem SimpleGraph.exists_ne_odd_degree_of_exists_odd_degree
  (G : SimpleGraph V) [Fintype V] [DecidableRel G.Adj]
  (v : V) (h : Odd (G.degree v)) :
  ∃ w, w ≠ v ∧ Odd (G.degree w)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.DegreeSum`

**Difficulty:** medium

---

## Part V: Bipartite Graphs

### 19. Bipartite Graph Definition

**Natural Language Statement:**
A graph is bipartite if its vertices can be partitioned into two disjoint sets such that every edge connects vertices from different sets.

**Lean 4 Definition:**
```lean
def SimpleGraph.IsBipartiteWith (G : SimpleGraph V) (s t : Set V) : Prop :=
  Disjoint s t ∧ ∀ {u v}, G.Adj u v → (u ∈ s ∧ v ∈ t) ∨ (u ∈ t ∧ v ∈ s)

def SimpleGraph.IsBipartite (G : SimpleGraph V) : Prop :=
  G.Colorable 2
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Bipartite`

**Difficulty:** medium

---

### 20. Bipartite Characterization

**Natural Language Statement:**
A graph is bipartite if and only if it is 2-colorable.

**Lean 4 Theorem:**
```lean
theorem SimpleGraph.isBipartite_iff_exists_isBipartiteWith :
  G.IsBipartite ↔ ∃ (s t : Set V), G.IsBipartiteWith s t
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Bipartite`

**Difficulty:** medium

---

### 21. Degree Sum in Bipartite Graphs

**Natural Language Statement:**
In a bipartite graph with parts S and T, the sum of degrees in S equals the sum of degrees in T, both equaling the number of edges.

**Lean 4 Theorem:**
```lean
theorem SimpleGraph.isBipartiteWith_sum_degrees_eq
  {s t : Finset V} [G.LocallyFinite]
  (h : G.IsBipartiteWith ↑s ↑t) :
  ∑ v ∈ s, G.degree v = ∑ w ∈ t, G.degree w
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Bipartite`

**Difficulty:** medium

---

## Part VI: Graph Coloring

### 22. Graph Coloring

**Natural Language Statement:**
A coloring of a graph assigns colors to vertices such that adjacent vertices have different colors. A graph is n-colorable if it admits a coloring with n colors.

**Lean 4 Definitions:**
```lean
-- A coloring is a homomorphism to the complete graph
abbrev SimpleGraph.Coloring (G : SimpleGraph V) (α : Type*) :=
  G →g completeGraph α

def SimpleGraph.Colorable (G : SimpleGraph V) (n : ℕ) : Prop :=
  Nonempty (G.Coloring (Fin n))
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Coloring`

**Difficulty:** medium

---

### 23. Chromatic Number

**Natural Language Statement:**
The chromatic number of a graph is the minimum number of colors needed to properly color it.

**Lean 4 Definition:**
```lean
noncomputable def SimpleGraph.chromaticNumber (G : SimpleGraph V) : ℕ∞ :=
  ⨅ n ∈ {n : ℕ | G.Colorable n}, (n : ℕ∞)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Coloring`

**Key Theorems:**
```lean
theorem two_le_chromaticNumber_of_adj {u v : V} (h : G.Adj u v) :
  2 ≤ G.chromaticNumber

theorem IsClique.card_le_chromaticNumber {s : Finset V}
  (h : G.IsClique ↑s) : ↑s.card ≤ G.chromaticNumber

theorem chromaticNumber_bot [Nonempty V] :
  (⊥ : SimpleGraph V).chromaticNumber = 1
```

**Difficulty:** medium

---

### 24. Coloring Validity

**Natural Language Statement:**
In a proper coloring, adjacent vertices must receive different colors.

**Lean 4 Theorem:**
```lean
theorem SimpleGraph.Coloring.valid (C : G.Coloring α)
  {v w : V} (h : G.Adj v w) : C v ≠ C w
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Coloring`

**Difficulty:** easy

---

## Part VII: Extremal Graph Theory

### 25. Turán Graph

**Natural Language Statement:**
The Turán graph T(n,r) is the complete r-partite graph on n vertices with part sizes as equal as possible.

**Lean 4 Definition:**
```lean
def turanGraph (n r : ℕ) : SimpleGraph (Fin n) where
  Adj := fun v w => v % r ≠ w % r
  symm := fun _ _ h => h.symm
  loopless := fun _ h => h rfl
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Extremal.Turan`

**Difficulty:** medium

---

### 26. Turán's Theorem

**Natural Language Statement:**
Among all graphs on n vertices that do not contain K_{r+1} as a subgraph, the Turán graph T(n,r) has the maximum number of edges.

**Lean 4 Theorems:**
```lean
def SimpleGraph.IsTuranMaximal (G : SimpleGraph V) [Fintype V] (r : ℕ) : Prop :=
  G.CliqueFree (r + 1) ∧
  ∀ H : SimpleGraph V, H.CliqueFree (r + 1) → H.edgeFinset.card ≤ G.edgeFinset.card

theorem isTuranMaximal_iff_nonempty_iso_turanGraph
  {G : SimpleGraph V} [Fintype V] {r : ℕ} (h : 0 < r) :
  G.IsTuranMaximal r ↔ Nonempty (G ≃g turanGraph (Fintype.card V) r)

-- Edge count bound
theorem CliqueFree.card_edgeFinset_le [Fintype V] [DecidableEq V]
  {G : SimpleGraph V} [DecidableRel G.Adj] {r : ℕ}
  (hG : G.CliqueFree (r + 1)) :
  G.edgeFinset.card ≤ (turanGraph (Fintype.card V) r).edgeFinset.card
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Combinatorics.SimpleGraph.Extremal.Turan`

**Difficulty:** hard

---

## Part VIII: Notable Gaps

### Euler's Formula (V - E + F = 2)

**100 Theorems List:** #13

**Status:** NOT FORMALIZED
**Reason:** Requires planar graph theory, face definitions, and topological embedding.

---

### Four Color Theorem (#32)

**100 Theorems List:** #32 - NOT FORMALIZED in Lean

**NL Statement**: "Every planar graph is 4-colorable. Equivalently, the vertices of any map can be colored with at most four colors such that no two adjacent regions share the same color."

**Mathematical Significance**:
- Most famous theorem in graph theory
- First major theorem proved with computer assistance (1976, Appel-Haken)
- Required checking ~1,936 reducible configurations
- Formalized in Coq by Georges Gonthier (2005-2008)

**Expected Lean 4 Template** (when infrastructure available):
```lean
-- Requires planar graph definition first
def SimpleGraph.IsPlanar (G : SimpleGraph V) : Prop := sorry

theorem four_color_theorem
  {V : Type*} [Fintype V] [DecidableEq V]
  {G : SimpleGraph V} [DecidableRel G.Adj]
  (hplanar : G.IsPlanar) :
  G.Colorable 4 := sorry
```

**Proof Approach (Appel-Haken)**:
1. Reducibility: Show 1,936 configurations are reducible
2. Discharging: Prove any minimal counterexample contains a reducible configuration
3. Unavoidability: Combinatorial argument using Euler's formula

**Why Not Yet in Lean**:
- Requires formal definition of planar graphs
- Needs graph embedding in plane/sphere
- Proof is computer-assisted with massive case analysis
- Coq proof exists but translation to Lean nontrivial

**External Formalization**:
- Coq proof: [Gonthier 2008 - Formal Proof of Four Color Theorem](https://www.ams.org/notices/200811/tx081101382p.pdf)
- ~60,000 lines of Coq code

**Imports**: `Mathlib.Combinatorics.SimpleGraph.Coloring` (for Colorable)

**Difficulty**: very hard (formalization requires significant infrastructure)

---

### Trees and Forests

**Status:** UNCLEAR
**Note:** Basic infrastructure exists but explicit tree predicates not confirmed.

---

### Hamiltonian Paths

**Status:** NOT FORMALIZED
**Note:** NP-complete problem with no simple characterization.

---

## Lean 4 Formalization Reference

### Import Statements

```lean
import Mathlib.Combinatorics.SimpleGraph.Basic        -- Core definitions
import Mathlib.Combinatorics.SimpleGraph.Subgraph     -- Subgraphs
import Mathlib.Combinatorics.SimpleGraph.Maps         -- Homomorphisms
import Mathlib.Combinatorics.SimpleGraph.Connectivity -- Walks, connectivity
import Mathlib.Combinatorics.SimpleGraph.Trails       -- Trails, cycles
import Mathlib.Combinatorics.SimpleGraph.DegreeSum    -- Handshaking lemma
import Mathlib.Combinatorics.SimpleGraph.Bipartite    -- Bipartite graphs
import Mathlib.Combinatorics.SimpleGraph.Coloring     -- Colorings
import Mathlib.Combinatorics.SimpleGraph.Extremal.Turan -- Turán's theorem
```

### Key Definitions Summary

| Concept | Lean 4 Name | Import |
|---------|-------------|--------|
| Simple graph | `SimpleGraph` | `SimpleGraph.Basic` |
| Adjacency | `G.Adj u v` | `SimpleGraph.Basic` |
| Degree | `G.degree v` | `SimpleGraph.Basic` |
| Subgraph | `G.Subgraph` | `SimpleGraph.Subgraph` |
| Homomorphism | `G →g H` | `SimpleGraph.Maps` |
| Embedding | `G ↪g H` | `SimpleGraph.Maps` |
| Walk | `G.Walk u v` | `SimpleGraph.Connectivity` |
| Path | `p.IsPath` | `SimpleGraph.Path` |
| Trail | `p.IsTrail` | `SimpleGraph.Trails` |
| Connected | `G.Connected` | `SimpleGraph.Connectivity` |
| Bipartite | `G.IsBipartite` | `SimpleGraph.Bipartite` |
| Chromatic number | `G.chromaticNumber` | `SimpleGraph.Coloring` |
| Clique-free | `G.CliqueFree k` | `SimpleGraph.Clique` |

---

## References

### Primary Sources

- [Wikipedia: Graph theory](https://en.wikipedia.org/wiki/Graph_theory)
- [Wikipedia: Turán's theorem](https://en.wikipedia.org/wiki/Tur%C3%A1n%27s_theorem)
- [100 Theorems in Lean](https://leanprover-community.github.io/100.html)

### Lean 4 / Mathlib

- [Mathlib4 Docs: SimpleGraph.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/SimpleGraph/Basic.html)
- [Mathlib4 Docs: DegreeSum](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/SimpleGraph/DegreeSum.html)
- [Mathlib4 Docs: Coloring](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/SimpleGraph/Coloring.html)
- [Mathlib4 Docs: Turan](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Combinatorics/SimpleGraph/Extremal/Turan.html)

---

**End of Knowledge Base**
