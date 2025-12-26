# Topology Fundamentals Knowledge Base for Lean 4

**Generated:** 2025-12-14
**Purpose:** Research knowledge base for implementing general topology in Lean 4 for dataset generation pairing formal proofs with natural language explanations.

---

## Overview

General topology provides the foundational framework for continuity, convergence, and spatial structure in modern mathematics. This knowledge base catalogs core definitions, separation axioms, compactness, connectedness, and major theorems formalized in Lean 4's Mathlib.

### Content Summary

| Category | Count | Description |
|----------|-------|-------------|
| **Core Definitions** | 12 | Topological spaces, open/closed sets, neighborhoods, continuity |
| **Separation Axioms** | 6 | T₀ through T₄ (normal) spaces |
| **Compactness** | 6 | Compact sets, Tychonoff, Heine-Borel |
| **Connectedness** | 5 | Connected, path-connected spaces |
| **Major Theorems** | 4 | Urysohn, Tietze, Baire category |
| **Total** | 33 | All formalized in Mathlib |

### Mathlib Approach

Lean 4's Mathlib formalizes topology using **filters** as a foundational abstraction, providing elegant generalizations of limits, continuity, and convergence:

```lean
-- Topological space via open sets
class TopologicalSpace (X : Type u) : Type u where
  IsOpen : Set X → Prop
  isOpen_univ : IsOpen Set.univ
  isOpen_inter : ∀ s t, IsOpen s → IsOpen t → IsOpen (s ∩ t)
  isOpen_sUnion : ∀ s, (∀ t ∈ s, IsOpen t) → IsOpen (⋃₀ s)

-- Neighborhood filter of point x
def nhds (x : X) : Filter X
```

**Primary Import:** `Mathlib.Topology.Basic`

---

## Related Knowledge Bases

### Builds Upon This KB
- **Measure Theory** (`measure_theory_knowledge_base.md`): Borel σ-algebras, topological measure spaces
- **Functional Analysis** (`functional_analysis_knowledge_base.md`): Topological vector spaces, weak topologies
- **Algebraic Topology** (`algebraic_topology_knowledge_base.md`): Homotopy, fundamental groups
- **Differential Geometry** (`differential_geometry_knowledge_base.md`): Smooth manifolds
- **Sheaf Theory** (`sheaf_theory_knowledge_base.md`): Sheaves on topological spaces

### Prerequisites
- **Set Theory** (`set_theory_knowledge_base.md`): Set operations, functions

### Scope Clarification
This KB focuses on **general (point-set) topology**:
- Topological spaces and open/closed sets
- Continuity and homeomorphisms
- Separation axioms (T₀ through T₄)
- Compactness and connectedness
- Major theorems (Urysohn, Tietze, Baire)

For **algebraic invariants** (homotopy groups, homology), see the **Algebraic Topology KB**.

---

## Part 1: Core Definitions

### 1. Topological Space

**Natural Language Statement:**
A topological space consists of a set X together with a collection of "open sets" satisfying three axioms: (1) the universal set X is open, (2) finite intersections of open sets are open, (3) arbitrary unions of open sets are open.

**Formal Definition (Set-Theoretic):**
```
(X, τ) is a topological space where τ ⊆ P(X) satisfies:
1. X ∈ τ
2. U, V ∈ τ ⟹ U ∩ V ∈ τ
3. {Uᵢ}ᵢ∈I ⊆ τ ⟹ ⋃ᵢ Uᵢ ∈ τ
```

**Lean 4 Definition:**
```lean
class TopologicalSpace (X : Type u) : Type u where
  IsOpen : Set X → Prop
  isOpen_univ : IsOpen Set.univ
  isOpen_inter : ∀ s t, IsOpen s → IsOpen t → IsOpen (s ∩ t)
  isOpen_sUnion : ∀ s, (∀ t ∈ s, IsOpen t) → IsOpen (⋃₀ s)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Defs.Basic`
- **Key Theorem:** `isOpen_empty` (derived: empty set is open)

**Difficulty:** easy

---

### 2. Open Sets

**Natural Language Statement:**
A set U is open if it belongs to the topology. Open sets are the fundamental building blocks of topological structure.

**Lean 4 Definition:**
```lean
def IsOpen {X : Type*} [TopologicalSpace X] (s : Set X) : Prop :=
  TopologicalSpace.IsOpen s
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Defs.Basic`

**Key Theorems:**
- `isOpen_univ`: The universal set is open
- `isOpen_empty`: The empty set is open
- `IsOpen.inter`: Finite intersections preserve openness
- `isOpen_sUnion`: Arbitrary unions preserve openness
- `isOpen_iUnion`: Indexed unions preserve openness

**Difficulty:** easy

---

### 3. Closed Sets

**Natural Language Statement:**
A set C is closed if its complement is open. Equivalently, closed sets contain all their limit points.

**Lean 4 Definition:**
```lean
structure IsClosed {X : Type u} [TopologicalSpace X] (s : Set X) : Prop where
  isOpen_compl : IsOpen sᶜ
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Defs.Basic`

**Key Theorems:**
- `isClosed_empty`: The empty set is closed
- `isClosed_univ`: The universal set is closed
- `IsClosed.union`: Finite unions of closed sets are closed
- `isClosed_sInter`: Arbitrary intersections of closed sets are closed
- `isClosed_compl_iff`: A set is closed iff its complement is open

**Difficulty:** easy

---

### 4. Interior

**Natural Language Statement:**
The interior of a set S is the largest open set contained in S, or equivalently, the union of all open sets contained in S.

**Lean 4 Definition:**
```lean
def interior {X : Type u} [TopologicalSpace X] (s : Set X) : Set X :=
  ⋃₀ {t | IsOpen t ∧ t ⊆ s}
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Defs.Basic`

**Key Properties:**
- `interior_subset`: interior s ⊆ s
- `isOpen_interior`: interior s is open
- `interior_eq_iff_isOpen`: s = interior s ↔ IsOpen s
- `mem_interior`: x ∈ interior s ↔ ∃ U open, x ∈ U ∧ U ⊆ s

**Difficulty:** easy

---

### 5. Closure

**Natural Language Statement:**
The closure of a set S is the smallest closed set containing S, or equivalently, the intersection of all closed sets containing S. A point x is in the closure of S iff every neighborhood of x intersects S.

**Lean 4 Definition:**
```lean
def closure {X : Type u} [TopologicalSpace X] (s : Set X) : Set X :=
  ⋂₀ {t | IsClosed t ∧ s ⊆ t}
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Defs.Basic`

**Key Properties:**
- `subset_closure`: s ⊆ closure s
- `isClosed_closure`: closure s is closed
- `closure_eq_iff_isClosed`: closure s = s ↔ IsClosed s
- `mem_closure_iff_nhds`: x ∈ closure s ↔ ∀ U ∈ 𝓝 x, (U ∩ s).Nonempty

**Difficulty:** easy

---

### 6. Frontier (Boundary)

**Natural Language Statement:**
The frontier (or boundary) of a set S is the closure minus the interior. A point x is on the frontier iff every neighborhood of x intersects both S and its complement.

**Lean 4 Definition:**
```lean
def frontier {X : Type u} [TopologicalSpace X] (s : Set X) : Set X :=
  closure s \ interior s
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Defs.Basic`

**Key Properties:**
- `frontier_eq_closure_inter_closure`: frontier s = closure s ∩ closure sᶜ
- `IsClosed.frontier_eq`: For closed s, frontier s = s \ interior s

**Difficulty:** easy

---

### 7. Dense Sets

**Natural Language Statement:**
A set D is dense in X if its closure equals X. Equivalently, D intersects every nonempty open set.

**Lean 4 Definition:**
```lean
def Dense {X : Type u} [TopologicalSpace X] (s : Set X) : Prop :=
  ∀ x, x ∈ closure s
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Defs.Basic`

**Key Theorems:**
- `Dense.closure_eq`: Dense s → closure s = Set.univ
- `dense_iff_inter_open`: Dense s ↔ ∀ U open nonempty, (U ∩ s).Nonempty

**Difficulty:** easy

---

### 8. Neighborhood Filter

**Natural Language Statement:**
The neighborhood filter of a point x consists of all sets containing x in their interior. Filters provide a unified framework for discussing convergence and limits in Mathlib.

**Lean 4 Definition:**
```lean
def nhds {X : Type u} [TopologicalSpace X] (x : X) : Filter X :=
  ⨅ (s : Set X) (_ : x ∈ s) (_ : IsOpen s), 𝓟 s
```

**Notation:** `𝓝 x` denotes the neighborhood filter of x

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Defs.Filter`

**Key Properties:**
- `mem_nhds_iff`: s ∈ 𝓝 x ↔ ∃ U ⊆ s, IsOpen U ∧ x ∈ U
- `nhds_basis_opens`: 𝓝 x has a basis of open neighborhoods

**Related Notations:**
- `𝓝[≠] x`: punctured neighborhoods (excluding x)
- `𝓝[<] x`, `𝓝[>] x`: left/right neighborhoods (in ordered spaces)

**Difficulty:** medium

---

### 9. Continuous Functions

**Natural Language Statement:**
A function f : X → Y between topological spaces is continuous if the preimage of every open set in Y is open in X. Equivalently, f is continuous at x if it respects the neighborhood filters.

**Lean 4 Definition:**
```lean
structure Continuous {X : Type u} {Y : Type v}
  [TopologicalSpace X] [TopologicalSpace Y] (f : X → Y) : Prop where
  isOpen_preimage : ∀ s, IsOpen s → IsOpen (f ⁻¹' s)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Basic`

**Equivalent Characterizations:**
```lean
theorem continuous_def : Continuous f ↔ ∀ s, IsOpen s → IsOpen (f ⁻¹' s)

theorem continuous_iff_continuousAt : Continuous f ↔ ∀ x, ContinuousAt f x

-- Via filters
theorem continuous_at_def : ContinuousAt f x ↔ Tendsto f (𝓝 x) (𝓝 (f x))
```

**Key Theorems:**
- `Continuous.comp`: Composition of continuous functions is continuous
- `continuous_id`: Identity function is continuous
- `continuous_const`: Constant functions are continuous

**Difficulty:** easy

---

### 10. Filter Tendsto (Limits)

**Natural Language Statement:**
A function f tends to filter l₂ along filter l₁ if for every l₂-large set, its preimage is l₁-large. This generalizes all notions of limits and continuity.

**Lean 4 Definition:**
```lean
def Filter.Tendsto {X Y : Type*} (f : X → Y) (l₁ : Filter X) (l₂ : Filter Y) : Prop :=
  Filter.map f l₁ ≤ l₂
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Order.Filter.Tendsto`

**Examples:**
- `Tendsto f (𝓝 x) (𝓝 y)`: f(x) → y, function limit
- `Tendsto u atTop (𝓝 x)`: sequence u converges to x
- `Tendsto f (𝓝[≠] x₀) (𝓝 y₀)`: limit excluding x₀

**Key Theorem:**
```lean
theorem tendsto_nhds_unique [T2Space X] {f : Filter α} {x y : X}
  [f.NeBot] (hx : Tendsto g f (𝓝 x)) (hy : Tendsto g f (𝓝 y)) : x = y
```
*Limits are unique in Hausdorff spaces*

**Difficulty:** medium

---

### 11. Homeomorphism

**Natural Language Statement:**
A homeomorphism is a continuous bijection with a continuous inverse. Two spaces are homeomorphic if there exists a homeomorphism between them, meaning they are topologically equivalent.

**Lean 4 Definition:**
```lean
structure Homeomorph (X : Type*) (Y : Type*)
  [TopologicalSpace X] [TopologicalSpace Y] extends X ≃ Y where
  continuous_toFun : Continuous toEquiv.toFun
  continuous_invFun : Continuous toEquiv.invFun
```

**Notation:** `X ≃ₜ Y` denotes a homeomorphism

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Homeomorph.Basic`

**Difficulty:** easy

---

### 12. Embeddings

**Natural Language Statement:**
An embedding is an injective continuous map that induces a homeomorphism onto its image. An open (closed) embedding has open (closed) image.

**Lean 4 Definitions:**
```lean
-- Inducing: topology on X is induced by f from Y
def IsInducing {X Y : Type*} [TopologicalSpace X] [TopologicalSpace Y]
  (f : X → Y) : Prop := TopologicalSpace.induced f ‹_› = ‹_›

-- Embedding: injective + inducing
def IsEmbedding {X Y : Type*} [TopologicalSpace X] [TopologicalSpace Y]
  (f : X → Y) : Prop := IsInducing f ∧ Function.Injective f

-- Open embedding
def IsOpenEmbedding {X Y : Type*} [TopologicalSpace X] [TopologicalSpace Y]
  (f : X → Y) : Prop := IsEmbedding f ∧ IsOpen (Set.range f)

-- Closed embedding
def IsClosedEmbedding {X Y : Type*} [TopologicalSpace X] [TopologicalSpace Y]
  (f : X → Y) : Prop := IsEmbedding f ∧ IsClosed (Set.range f)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Defs.Induced`

**Difficulty:** medium

---

## Part 2: Separation Axioms

The separation axioms form a hierarchy of increasingly strong requirements on how points and closed sets can be separated by open sets.

### 13. T₀ Space (Kolmogorov)

**Natural Language Statement:**
For any two distinct points, there exists an open set containing one but not the other. Points are topologically distinguishable.

**Lean 4 Definition:**
```lean
class T0Space (X : Type*) [TopologicalSpace X] : Prop where
  t0 : ∀ ⦃x y : X⦄, x ≠ y →
    ∃ U : Set X, IsOpen U ∧ (x ∈ U ∧ y ∉ U ∨ y ∈ U ∧ x ∉ U)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Separation.Basic`

**Difficulty:** easy

---

### 14. T₁ Space (Fréchet)

**Natural Language Statement:**
Every singleton set is closed. Equivalently, for any two distinct points, each has an open neighborhood excluding the other.

**Lean 4 Definition:**
```lean
class T1Space (X : Type*) [TopologicalSpace X] : Prop where
  t1 : ∀ x : X, IsClosed ({x} : Set X)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Separation.Basic`

**Key Theorem:**
```lean
theorem finite_discrete [T1Space X] [Finite X] : DiscreteTopology X
```
*Finite T₁ spaces have discrete topology*

**Difficulty:** easy

---

### 15. T₂ Space (Hausdorff)

**Natural Language Statement:**
For any two distinct points, there exist disjoint open neighborhoods separating them. This ensures limits are unique.

**Lean 4 Definition:**
```lean
class T2Space (X : Type*) [TopologicalSpace X] : Prop where
  t2 : Pairwise fun (x y : X) =>
    ∃ u v : Set X, IsOpen u ∧ IsOpen v ∧ x ∈ u ∧ y ∈ v ∧ Disjoint u v
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Separation.Hausdorff`

**Equivalent Characterizations:**
```lean
-- Via neighborhood filters
theorem t2Space_iff_disjoint_nhds :
  T2Space X ↔ Pairwise fun x y => Disjoint (𝓝 x) (𝓝 y)

-- Via closed diagonal
theorem t2_iff_isClosed_diagonal :
  T2Space X ↔ IsClosed (Set.diagonal X)

-- Via uniqueness of limits
theorem t2_iff_nhds :
  T2Space X ↔ ∀ {x y : X}, (𝓝 x ⊓ 𝓝 y).NeBot → x = y
```

**Key Theorems:**
- `IsCompact.isClosed`: Compact sets are closed in Hausdorff spaces
- `tendsto_nhds_unique`: Limits are unique in Hausdorff spaces

**Difficulty:** easy

---

### 16. T₂.₅ Space (Urysohn)

**Natural Language Statement:**
For any two distinct points, there exist closed neighborhoods with disjoint interiors.

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Separation.Basic`

**Difficulty:** medium

---

### 17. T₃ Space (Regular Hausdorff)

**Natural Language Statement:**
A regular space where points are closed. For any closed set C and point x ∉ C, there exist disjoint open sets separating them.

**Lean 4 Definition:**
```lean
class RegularSpace (X : Type*) [TopologicalSpace X] : Prop

class T3Space (X : Type*) [TopologicalSpace X] extends T0Space X, RegularSpace X
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Separation.Regular`

**Note:** Mathlib follows modern conventions where T₃ implies T₂.₅

**Difficulty:** medium

---

### 18. T₄ Space (Normal Hausdorff)

**Natural Language Statement:**
A normal T₁ space. For any two disjoint closed sets, there exist disjoint open sets containing them. This is the setting for Urysohn's Lemma and Tietze Extension.

**Lean 4 Definition:**
```lean
class NormalSpace (X : Type*) [TopologicalSpace X] : Prop

class T4Space (X : Type*) [TopologicalSpace X] extends T1Space X, NormalSpace X
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Separation.Regular`

**Hierarchy:**
```
T₄ → T₃.₅ → T₃ → T₂.₅ → T₂ → T₁ → T₀
```

**Difficulty:** medium

---

## Part 3: Compactness

### 19. Compact Sets

**Natural Language Statement:**
A set K is compact if every open cover has a finite subcover. In Mathlib's filter-based definition, K is compact if every filter containing K has a cluster point in K.

**Lean 4 Definition (filter version):**
```lean
def IsCompact {X : Type*} [TopologicalSpace X] (s : Set X) : Prop :=
  ∀ ⦃f : Filter X⦄ [NeBot f], f ≤ 𝓟 s → ∃ x ∈ s, ClusterPt x f
```

**Equivalent (open cover definition):**
```lean
theorem isCompact_iff_finite_subcover {s : Set X} :
  IsCompact s ↔ ∀ {ι : Type*} (U : ι → Set X),
    (∀ i, IsOpen (U i)) → s ⊆ ⋃ i, U i →
    ∃ t : Finset ι, s ⊆ ⋃ i ∈ t, U i
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Compactness.Compact`

**Difficulty:** medium

---

### 20. Compact Space

**Natural Language Statement:**
A topological space is compact if the entire space is a compact set.

**Lean 4 Definition:**
```lean
class CompactSpace (X : Type*) [TopologicalSpace X] : Prop where
  isCompact_univ : IsCompact (Set.univ : Set X)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Compactness.Compact`

**Key Instances:**
- Finite spaces are compact
- Closed subsets of compact spaces are compact
- Products of compact spaces are compact (Tychonoff)

**Difficulty:** easy

---

### 21. Tychonoff's Theorem

**100 Theorems List:** Not numbered (but fundamental)

**Natural Language Statement:**
The product of any collection of compact spaces is compact in the product topology. This is one of the most important theorems in topology.

**Lean 4 Theorem:**
```lean
instance Pi.compactSpace {ι : Type*} {X : ι → Type*}
  [∀ i, TopologicalSpace (X i)] [∀ i, CompactSpace (X i)] :
  CompactSpace (∀ i, X i)

theorem isCompact_pi_infinite {ι : Type*} {X : ι → Type*}
  [∀ i, TopologicalSpace (X i)] {s : ∀ i, Set (X i)}
  (hs : ∀ i, IsCompact (s i)) :
  IsCompact {f : ∀ i, X i | ∀ i, f i ∈ s i}
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Compactness.Compact`
- **Proof Method:** Ultrafilter-based

**Difficulty:** hard

---

### 22. Heine-Borel Theorem

**Natural Language Statement:**
In a proper metric space (including ℝⁿ), a set is compact if and only if it is closed and bounded.

**Lean 4 Theorem:**
```lean
theorem Metric.isCompact_iff_isClosed_bounded [ProperSpace X] {s : Set X} :
  IsCompact s ↔ IsClosed s ∧ Bornology.IsBounded s

theorem Metric.isCompact_of_isClosed_isBounded [ProperSpace X] {s : Set X}
  (hc : IsClosed s) (hb : Bornology.IsBounded s) : IsCompact s
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.MetricSpace.Bounded`

**Note:** Requires `ProperSpace` (closed balls are compact). Finite-dimensional normed spaces are proper.

**Difficulty:** hard

---

### 23. Key Compactness Properties

**Lean 4 Theorems:**
```lean
-- Continuous images of compact sets are compact
theorem IsCompact.image_of_continuousOn {f : X → Y} {s : Set X}
  (hs : IsCompact s) (hf : ContinuousOn f s) : IsCompact (f '' s)

-- Compact subsets of Hausdorff spaces are closed
theorem IsCompact.isClosed [T2Space X] {s : Set X}
  (hs : IsCompact s) : IsClosed s

-- Closed subsets of compact sets are compact
theorem IsClosed.isCompact [CompactSpace X] {s : Set X}
  (hs : IsClosed s) : IsCompact s

-- Finite sets are compact
theorem Set.Finite.isCompact {s : Set X} (hs : s.Finite) : IsCompact s
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Compactness.Compact`

**Difficulty:** medium

---

### 24. Locally Compact Spaces

**Natural Language Statement:**
A space is locally compact if every point has a compact neighborhood.

**Lean 4 Definition:**
```lean
class LocallyCompactSpace (X : Type*) [TopologicalSpace X] : Prop
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Compactness.LocallyCompact`

**Key Theorem:**
```lean
theorem exists_compact_between [LocallyCompactSpace X]
  {K U : Set X} (hK : IsCompact K) (hU : IsOpen U) (hKU : K ⊆ U) :
  ∃ L, IsCompact L ∧ K ⊆ interior L ∧ L ⊆ U
```

**Difficulty:** medium

---

## Part 4: Connectedness

### 25. Connected Sets

**Natural Language Statement:**
A set is connected if it cannot be partitioned into two nonempty disjoint relatively open sets. A preconnected set satisfies the same condition without requiring nonemptiness.

**Lean 4 Definitions:**
```lean
def IsPreconnected {X : Type*} [TopologicalSpace X] (s : Set X) : Prop :=
  ∀ u v : Set X, IsOpen u → IsOpen v → s ⊆ u ∪ v →
    (s ∩ u).Nonempty → (s ∩ v).Nonempty → (s ∩ (u ∩ v)).Nonempty

def IsConnected {X : Type*} [TopologicalSpace X] (s : Set X) : Prop :=
  s.Nonempty ∧ IsPreconnected s
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Connected.Basic`

**Difficulty:** easy

---

### 26. Connected Space

**Natural Language Statement:**
A topological space is connected if the entire space is a connected set.

**Lean 4 Definition:**
```lean
class PreconnectedSpace (X : Type*) [TopologicalSpace X] : Prop where
  isPreconnected_univ : IsPreconnected (Set.univ : Set X)

class ConnectedSpace (X : Type*) [TopologicalSpace X]
  extends PreconnectedSpace X : Prop where
  toNonempty : Nonempty X
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Connected.Basic`

**Key Theorems:**
- `IsPreconnected.closure`: Closure of preconnected set is preconnected
- `IsPreconnected.image`: Continuous image of preconnected set is preconnected
- `instConnectedSpaceProd`: Products of connected spaces are connected

**Difficulty:** easy

---

### 27. Connected Components

**Natural Language Statement:**
The connected component of a point x is the largest connected set containing x. Every space partitions into disjoint connected components.

**Lean 4 Definition:**
```lean
def connectedComponent {X : Type*} [TopologicalSpace X] (x : X) : Set X :=
  ⋃₀ {s | IsConnected s ∧ x ∈ s}
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Connected.Basic`

**Difficulty:** medium

---

### 28. Path Connectedness

**Natural Language Statement:**
Two points are joined if there exists a continuous path between them. A space is path-connected if any two points can be joined by a path. Path-connectedness implies connectedness but not conversely.

**Lean 4 Definitions:**
```lean
-- Path from x to y (continuous map from [0,1])
structure Path {X : Type*} [TopologicalSpace X] (x y : X)
  extends C(unitInterval, X) where
  source' : toFun 0 = x
  target' : toFun 1 = y

-- Two points are joined by a path
def Joined {X : Type*} [TopologicalSpace X] (x y : X) : Prop :=
  Nonempty (Path x y)

-- Path-connected space
class PathConnectedSpace (X : Type*) [TopologicalSpace X] : Prop where
  nonempty : Nonempty X
  joined : ∀ x y : X, Joined x y

-- Path-connected set
def IsPathConnected {X : Type*} [TopologicalSpace X] (F : Set X) : Prop :=
  ∃ x ∈ F, ∀ ⦃y⦄, y ∈ F → JoinedIn F x y
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Connected.PathConnected`

**Key Theorems:**
```lean
theorem IsPathConnected.isConnected {s : Set X}
  (h : IsPathConnected s) : IsConnected s

theorem path_connected_space_iff_connected_space
  [LocallyPathConnectedSpace X] :
  PathConnectedSpace X ↔ ConnectedSpace X
```
*In locally path-connected spaces, connectedness equals path-connectedness*

**Difficulty:** medium

---

### 29. Intermediate Value Theorem (Topological)

**Natural Language Statement:**
A continuous function on a connected space has connected image. For real-valued functions, this implies the classical IVT: if f(a) < c < f(b), then f(x) = c for some x between a and b.

**Lean 4 Theorem:**
```lean
theorem IsPreconnected.image {f : X → Y} {s : Set X}
  (hs : IsPreconnected s) (hf : Continuous f) : IsPreconnected (f '' s)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Connected.Basic`

**Difficulty:** medium

---

## Part 5: Major Theorems

### 30. Urysohn's Lemma

**Natural Language Statement:**
In a normal space, for any two disjoint closed sets A and B, there exists a continuous function f : X → [0,1] such that f(A) = {0} and f(B) = {1}.

**Lean 4:** Available in Mathlib
- **Import:** `Mathlib.Topology.UrysohnLemma`

**Significance:** Characterizes normal spaces and is key to proving Tietze Extension.

**Difficulty:** hard

---

### 31. Tietze Extension Theorem

**Natural Language Statement:**
In a normal space, any continuous real-valued function defined on a closed subset can be extended to a continuous function on the whole space, preserving bounds.

**Lean 4 Class and Theorem:**
```lean
class TietzeExtension (Y : Type*) [TopologicalSpace Y] : Prop where
  exists_restrict_eq' {X : Type*} [TopologicalSpace X] [NormalSpace X]
    (s : Set X) (hs : IsClosed s) (f : C(s, Y)) :
    ∃ g : C(X, Y), ContinuousMap.restrict s g = f

theorem ContinuousMap.exists_restrict_eq
  {X : Type*} [TopologicalSpace X] [NormalSpace X]
  {s : Set X} {Y : Type*} [TopologicalSpace Y] [TietzeExtension Y]
  (hs : IsClosed s) (f : C(s, Y)) :
  ∃ g : C(X, Y), restrict s g = f
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.TietzeExtension`

**Key Instances:**
- `Real.instTietzeExtension`: ℝ satisfies extension property
- `NNReal.instTietzeExtension`: ℝ≥0 satisfies extension property
- `Pi.instTietzeExtension`: Products preserve the property

**Difficulty:** hard

---

### 32. Baire Category Theorem

**Natural Language Statement:**
In a complete metric space (or locally compact regular space), the intersection of countably many dense open sets is dense. Equivalently, the space cannot be written as a countable union of nowhere dense sets.

**Lean 4 Class and Theorem:**
```lean
class BaireSpace (X : Type*) [TopologicalSpace X] : Prop

theorem dense_sInter_of_isOpen {X : Type*} [TopologicalSpace X] [BaireSpace X]
  {S : Set (Set X)} (hS : S.Countable)
  (hopen : ∀ s ∈ S, IsOpen s) (hdense : ∀ s ∈ S, Dense s) :
  Dense (⋂₀ S)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.Topology.Baire.Lemmas`

**Key Instances:**
- Complete metric spaces are Baire spaces
- Locally compact regular spaces are Baire spaces

**Difficulty:** hard

---

### 33. Brouwer Fixed Point Theorem

**100 Theorems List:** #36

**Natural Language Statement:**
Every continuous function from a closed ball in ℝⁿ to itself has a fixed point.

**Mathlib Support:** FULL (proved)
- **Import:** Various modules in `Mathlib.Topology.Homotopy`
- **Note:** Proved via algebraic topology (homology)

**Difficulty:** very hard

---

## Topological Constructions

### Induced (Subspace) Topology

**Natural Language Statement:**
Given f : X → Y and a topology on Y, the induced topology on X is the coarsest topology making f continuous.

**Lean 4 Definition:**
```lean
def TopologicalSpace.induced {X Y : Type*} (f : X → Y)
  [t : TopologicalSpace Y] : TopologicalSpace X where
  IsOpen s := ∃ t, IsOpen t ∧ f ⁻¹' t = s
```

**Import:** `Mathlib.Topology.Defs.Induced`

---

### Coinduced (Quotient) Topology

**Natural Language Statement:**
Given f : X → Y and a topology on X, the coinduced topology on Y is the finest topology making f continuous.

**Lean 4 Definition:**
```lean
def TopologicalSpace.coinduced {X Y : Type*} (f : X → Y)
  [t : TopologicalSpace X] : TopologicalSpace Y where
  IsOpen s := IsOpen (f ⁻¹' s)
```

**Import:** `Mathlib.Topology.Defs.Induced`

---

### Product Topology

**Lean 4:** Automatic instance for products
```lean
instance instTopologicalSpaceProd {X Y : Type*}
  [TopologicalSpace X] [TopologicalSpace Y] :
  TopologicalSpace (X × Y)
```

**Import:** `Mathlib.Topology.Constructions`

---

## Lean 4 Formalization Reference

### Import Statements

```lean
import Mathlib.Topology.Basic              -- Core topology
import Mathlib.Topology.Defs.Basic         -- Definitions
import Mathlib.Topology.Defs.Filter        -- Neighborhood filters
import Mathlib.Topology.Separation.Basic   -- T₀, T₁
import Mathlib.Topology.Separation.Hausdorff -- T₂
import Mathlib.Topology.Separation.Regular -- T₃, T₄
import Mathlib.Topology.Compactness.Compact -- Compactness
import Mathlib.Topology.Connected.Basic    -- Connectedness
import Mathlib.Topology.Connected.PathConnected -- Path connectedness
import Mathlib.Topology.TietzeExtension    -- Tietze theorem
import Mathlib.Topology.Baire.Lemmas       -- Baire category
import Mathlib.Topology.Homeomorph.Basic   -- Homeomorphisms
```

### Key Definitions and Theorems Summary

| Concept | Lean 4 Name | Import |
|---------|-------------|--------|
| Topological space | `TopologicalSpace` | `Topology.Defs.Basic` |
| Open set | `IsOpen` | `Topology.Defs.Basic` |
| Closed set | `IsClosed` | `Topology.Defs.Basic` |
| Interior | `interior` | `Topology.Defs.Basic` |
| Closure | `closure` | `Topology.Defs.Basic` |
| Neighborhood filter | `nhds`, `𝓝` | `Topology.Defs.Filter` |
| Continuous | `Continuous` | `Topology.Basic` |
| Filter limit | `Filter.Tendsto` | `Order.Filter.Tendsto` |
| Hausdorff | `T2Space` | `Topology.Separation.Hausdorff` |
| Normal | `NormalSpace` | `Topology.Separation.Regular` |
| Compact | `IsCompact`, `CompactSpace` | `Topology.Compactness.Compact` |
| Connected | `IsConnected`, `ConnectedSpace` | `Topology.Connected.Basic` |
| Path-connected | `PathConnectedSpace` | `Topology.Connected.PathConnected` |
| Homeomorphism | `Homeomorph`, `≃ₜ` | `Topology.Homeomorph.Basic` |

---

## Implementation Priority

### Phase 1: Core Definitions (Easy)

| Definition | `theorem_id` | Mathlib Reference |
|------------|--------------|-------------------|
| Topological space | `top_space_def` | `TopologicalSpace` |
| Open set | `top_open_def` | `IsOpen` |
| Closed set | `top_closed_def` | `IsClosed` |
| Interior | `top_interior_def` | `interior` |
| Closure | `top_closure_def` | `closure` |
| Continuous function | `top_continuous_def` | `Continuous` |
| Hausdorff space | `top_t2_def` | `T2Space` |
| Compact set | `top_compact_def` | `IsCompact` |
| Connected set | `top_connected_def` | `IsConnected` |

### Phase 2: Major Theorems (Medium-Hard)

| Theorem | `theorem_id` | Mathlib Reference |
|---------|--------------|-------------------|
| Tychonoff | `top_tychonoff` | `Pi.compactSpace` |
| Heine-Borel | `top_heine_borel` | `Metric.isCompact_iff_isClosed_bounded` |
| Tietze Extension | `top_tietze` | `ContinuousMap.exists_restrict_eq` |
| Baire Category | `top_baire` | `dense_sInter_of_isOpen` |
| Urysohn Lemma | `top_urysohn` | Urysohn module |

### Phase 3: Separation Axioms (Medium)

All separation axioms T₀ through T₄ with their characterizations.

---

## References

### Primary Sources

- [Wikipedia: General topology](https://en.wikipedia.org/wiki/General_topology)
- [Wikipedia: Topological space](https://en.wikipedia.org/wiki/Topological_space)
- [Wikipedia: Compact space](https://en.wikipedia.org/wiki/Compact_space)
- [Wikipedia: Connected space](https://en.wikipedia.org/wiki/Connected_space)
- [Wikipedia: Separation axiom](https://en.wikipedia.org/wiki/Separation_axiom)

### Lean 4 / Mathlib

- [Mathlib4 Docs: Topology.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Topology/Basic.html)
- [Mathlib4 Docs: Topology.Compactness](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Topology/Compactness/Compact.html)
- [Mathlib4 Docs: Topology.Connected](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Topology/Connected/Basic.html)
- [Mathlib Topology Theory Overview](https://leanprover-community.github.io/theories/topology.html)
- [100 Theorems in Lean](https://leanprover-community.github.io/100.html)

---

**End of Knowledge Base**
