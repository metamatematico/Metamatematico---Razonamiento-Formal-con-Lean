# Fiber Bundles Knowledge Base

**Domain**: Fiber Bundles (Topological and Smooth Vector Bundles, Bundle Constructions)
**Lean 4 Coverage**: GOOD for topological/vector bundles; LIMITED for principal bundles
**Source**: Mathlib4 `Topology.FiberBundle.*`, `Topology.VectorBundle.*`, `Geometry.Manifold.VectorBundle.*`
**Last Updated**: 2025-12-24
**Related KB**: `smooth_manifolds` (manifold infrastructure, tangent bundle basics), `differential_geometry` (Lie theory)

---

## Executive Summary

This knowledge base covers fiber bundle theory - the study of spaces that locally look like products but may have non-trivial global structure. Mathlib4 coverage:

- **Topological Fiber Bundles**: WELL FORMALIZED - FiberBundle, Trivialization, FiberBundleCore
- **Vector Bundles**: WELL FORMALIZED - VectorBundle, linear trivializations, coordinate changes
- **Smooth Vector Bundles**: GOOD - ContMDiffVectorBundle, smooth transition functions
- **Bundle Constructions**: GOOD - Trivial, pullback, product bundles
- **Bundle Morphisms**: GOOD - Continuous linear maps between bundles
- **Principal Bundles**: LIMITED - No dedicated formalization (conceptual templates)

**Key Gaps**: Principal bundles, associated bundles, characteristic classes, connections on bundles.

---

## Content Summary

| Part | Topic | Statements | Mathlib Coverage |
|------|-------|------------|------------------|
| 1 | Fiber Bundle Foundations | 12 | Complete |
| 2 | Trivialization Theory | 10 | Complete |
| 3 | Vector Bundle Structure | 12 | Complete |
| 4 | Smooth Vector Bundles | 8 | Good |
| 5 | Bundle Constructions | 10 | Good |
| 6 | Bundle Morphisms | 8 | Good |
| 7 | Principal Bundles | 8 | Limited |
| 8 | Classical Examples | 7 | Good |
| **Total** | | **75** | **~65%** |

**Measurability Score**: 65 (topological/vector bundles excellent; principal bundles need templates)

---

## Related Knowledge Bases

### Prerequisites
- **Topology** (`topology_knowledge_base.md`): Topological spaces, local triviality
- **Smooth Manifolds** (`smooth_manifolds_knowledge_base.md`): Manifold structure, tangent bundle basics
- **Linear Algebra** (`linear_algebra_knowledge_base.md`): Vector spaces, linear maps

### Builds Upon This KB
- **Differential Geometry** (`differential_geometry_knowledge_base.md`): Connections, curvature
- **Algebraic Topology** (`algebraic_topology_knowledge_base.md`): Characteristic classes, classifying spaces
- **K-Theory** (`k_theory_knowledge_base.md`): Vector bundle K-groups

### Related Topics
- **Lie Theory** (`lie_theory_knowledge_base.md`): Lie groups as structure groups
- **Complex Geometry** (`complex_geometry_knowledge_base.md`): Holomorphic bundles

### Scope Clarification
This KB focuses on **fiber bundle theory**:
- Fiber bundle foundations (FiberBundle, FiberBundleCore)
- Trivialization theory
- Vector bundle structure
- Smooth vector bundles
- Bundle constructions (pullback, product)
- Bundle morphisms
- (Gaps: Principal bundles, connections, characteristic classes)

For **tangent bundle specifics**, see **Smooth Manifolds KB**.

---

## Part 1: Fiber Bundle Foundations

### 1.1 Total Space

**NL Statement**: "The total space of a bundle with base B and fiber family E is the dependent sum Bundle.TotalSpace F E consisting of pairs (x, v) where x : B and v : E x."

**Lean 4 Definition**:
```lean
structure Bundle.TotalSpace (F : Type*) (E : B → Type*) where
  proj : B
  snd : E proj
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: easy

---

### 1.2 Projection Map

**NL Statement**: "The projection π : E → B maps each point in the total space to its base point. For a fiber bundle, this map is continuous, open, and surjective."

**Lean 4 Definition**:
```lean
def Bundle.TotalSpace.proj : Bundle.TotalSpace F E → B := fun p => p.proj

theorem FiberBundle.continuous_proj [FiberBundle F E] :
    Continuous (Bundle.TotalSpace.proj : Bundle.TotalSpace F E → B)
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: easy

---

### 1.3 Fiber at a Point

**NL Statement**: "The fiber over a point x ∈ B is the preimage π⁻¹(x), which is homeomorphic to the model fiber F in a fiber bundle."

**Lean 4 Definition**:
```lean
-- The fiber E x at point x
def Bundle.TotalSpace.mk (x : B) : E x → Bundle.TotalSpace F E :=
  fun v => ⟨x, v⟩
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: easy

---

### 1.4 Fiber Bundle Definition

**NL Statement**: "A fiber bundle with fiber F over base B is a total space E with projection π : E → B such that each fiber is homeomorphic to F and there exists a local trivialization around each point."

**Lean 4 Definition**:
```lean
class FiberBundle (F : Type*) [TopologicalSpace F]
    (E : B → Type*) [TopologicalSpace (Bundle.TotalSpace F E)]
    [∀ x, TopologicalSpace (E x)] where
  totalSpaceMk_inducing : ∀ x : B, Inducing (Bundle.TotalSpace.mk (E := E) x)
  trivializationAtlas : Set (Trivialization F (π F E))
  trivializationAt : B → Trivialization F (π F E)
  mem_trivializationAtlas : ∀ x, trivializationAt x ∈ trivializationAtlas
  trivializationAt_mem_baseSet : ∀ x, x ∈ (trivializationAt x).baseSet
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: medium

---

### 1.5 FiberBundleCore

**NL Statement**: "A fiber bundle core encodes a fiber bundle via transition functions: an open cover {Uᵢ} of B and continuous maps φᵢⱼ : Uᵢ ∩ Uⱼ → Homeo(F, F) satisfying the cocycle condition φᵢⱼ ∘ φⱼₖ = φᵢₖ."

**Lean 4 Definition**:
```lean
structure FiberBundleCore (ι : Type*) (B : Type*) [TopologicalSpace B]
    (F : Type*) [TopologicalSpace F] where
  baseSet : ι → Set B
  isOpen_baseSet : ∀ i, IsOpen (baseSet i)
  indexAt : B → ι
  mem_baseSet_at : ∀ x, x ∈ baseSet (indexAt x)
  coordChange : ι → ι → B → F → F
  coordChange_self : ∀ i x ∈ baseSet i, ∀ v, coordChange i i x v = v
  continuousOn_coordChange : ∀ i j, ContinuousOn (fun p => coordChange i j p.1 p.2)
      ((baseSet i ∩ baseSet j) ×ˢ Set.univ)
  coordChange_comp : ∀ i j k x ∈ baseSet i ∩ baseSet j ∩ baseSet k,
      ∀ v, coordChange j k x (coordChange i j x v) = coordChange i k x v
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: hard

---

### 1.6 Cocycle Condition

**NL Statement**: "The cocycle condition for transition functions states: φᵢⱼ(x) ∘ φⱼₖ(x) = φᵢₖ(x) for all x in the triple overlap Uᵢ ∩ Uⱼ ∩ Uₖ."

**Lean 4 Theorem**:
```lean
-- In FiberBundleCore
coordChange_comp : ∀ i j k x ∈ baseSet i ∩ baseSet j ∩ baseSet k,
    ∀ v, coordChange j k x (coordChange i j x v) = coordChange i k x v
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: medium

---

### 1.7 Bundle from Core

**NL Statement**: "Given a FiberBundleCore, one can construct a fiber bundle with the appropriate topology making local trivializations into homeomorphisms."

**Lean 4 Instance**:
```lean
instance FiberBundleCore.fiberBundle : FiberBundle F Z.Fiber where
  -- Constructed from the core data
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: hard

---

### 1.8 Projection is Open Map

**NL Statement**: "The projection map of a fiber bundle is an open map: it maps open sets to open sets."

**Lean 4 Theorem**:
```lean
theorem FiberBundle.isOpenMap_proj [FiberBundle F E] :
    IsOpenMap (Bundle.TotalSpace.proj : Bundle.TotalSpace F E → B)
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: medium

---

### 1.9 Projection is Quotient Map

**NL Statement**: "When the fiber F is nonempty, the projection of a fiber bundle is a quotient map."

**Lean 4 Theorem**:
```lean
theorem FiberBundle.quotientMap_proj [Nonempty F] [FiberBundle F E] :
    QuotientMap (Bundle.TotalSpace.proj : Bundle.TotalSpace F E → B)
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: medium

---

### 1.10 Fiber Inclusion is Embedding

**NL Statement**: "The inclusion of each fiber into the total space is a topological embedding."

**Lean 4 Theorem**:
```lean
theorem FiberBundle.inducing_totalSpaceMk [FiberBundle F E] (x : B) :
    Inducing (Bundle.TotalSpace.mk (E := E) x : E x → Bundle.TotalSpace F E)
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: medium

---

### 1.11 Continuity into Total Space

**NL Statement**: "A map into a fiber bundle's total space is continuous if and only if both its projection to the base and its trivialized fiber component are continuous."

**Lean 4 Theorem**:
```lean
theorem FiberBundle.continuous_totalSpaceMk [FiberBundle F E] {f : X → B} {g : ∀ x, E (f x)}
    (hf : Continuous f) (hg : ∀ e : Trivialization F (π F E), e ∈ trivializationAtlas F E →
      ContinuousOn (fun x => (e (Bundle.TotalSpace.mk (f x) (g x))).2) (f ⁻¹' e.baseSet)) :
    Continuous fun x => Bundle.TotalSpace.mk (f x) (g x)
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: hard

---

### 1.12 Fiber Prebundle

**NL Statement**: "A fiber prebundle provides minimal data to construct a fiber bundle: pretrivializations as partial equivalences satisfying compatibility conditions."

**Lean 4 Definition**:
```lean
structure FiberPrebundle (F : Type*) [TopologicalSpace F]
    (E : B → Type*) where
  pretrivializationAtlas : Set (Pretrivialization F (π F E))
  pretrivializationAt : B → Pretrivialization F (π F E)
  mem_pretrivializationAtlas : ∀ x, pretrivializationAt x ∈ pretrivializationAtlas
  pretrivialization_mem_source : ∀ x, (⟨x, pretrivializationAt x x.2⟩ : Bundle.TotalSpace F E) ∈
      (pretrivializationAt x).source
  continuous_trivChange : ...
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: hard

---

## Part 2: Trivialization Theory

### 2.1 Trivialization Definition

**NL Statement**: "A local trivialization of a fiber bundle over an open set U ⊆ B is a homeomorphism φ : π⁻¹(U) → U × F that commutes with projection to U."

**Lean 4 Definition**:
```lean
structure Trivialization (F : Type*) {B : Type*} [TopologicalSpace F] [TopologicalSpace B]
    (proj : Z → B) extends PartialHomeomorph Z (B × F) where
  baseSet : Set B
  open_baseSet : IsOpen baseSet
  source_eq : source = proj ⁻¹' baseSet
  target_eq : target = baseSet ×ˢ Set.univ
  proj_toFun : ∀ p ∈ source, (toPartialHomeomorph p).1 = proj p
```

**Imports**: `Mathlib.Topology.FiberBundle.Trivialization`
**Difficulty**: medium

---

### 2.2 Trivialization Source and Target

**NL Statement**: "The source of a trivialization is the preimage of the base set, and the target is the product of the base set with the entire fiber."

**Lean 4 Theorem**:
```lean
theorem Trivialization.source_eq : e.source = proj ⁻¹' e.baseSet

theorem Trivialization.target_eq : e.target = e.baseSet ×ˢ Set.univ
```

**Imports**: `Mathlib.Topology.FiberBundle.Trivialization`
**Difficulty**: easy

---

### 2.3 Trivialization Preserves Projection

**NL Statement**: "A trivialization φ preserves the projection: if φ(p) = (b, v), then π(p) = b."

**Lean 4 Theorem**:
```lean
theorem Trivialization.coe_fst (hp : p ∈ e.source) : (e p).1 = proj p
```

**Imports**: `Mathlib.Topology.FiberBundle.Trivialization`
**Difficulty**: easy

---

### 2.4 Trivialization is Fiberwise Homeomorphism

**NL Statement**: "Restricted to each fiber, a trivialization gives a homeomorphism between the fiber E_x and the model fiber F."

**Lean 4 Definition**:
```lean
def Trivialization.preimageSingletonHomeomorph (hx : x ∈ e.baseSet) :
    proj ⁻¹' {x} ≃ₜ F
```

**Imports**: `Mathlib.Topology.FiberBundle.Trivialization`
**Difficulty**: medium

---

### 2.5 Coordinate Change

**NL Statement**: "Given two trivializations e and e' with overlapping base sets, the coordinate change is the map e' ∘ e⁻¹ : (U ∩ U') × F → (U ∩ U') × F."

**Lean 4 Definition**:
```lean
def Trivialization.coordChange (e e' : Trivialization F proj) (x : B) : F → F :=
  fun v => (e' (e.symm (x, v))).2
```

**Imports**: `Mathlib.Topology.FiberBundle.Trivialization`
**Difficulty**: medium

---

### 2.6 Coordinate Change Continuity

**NL Statement**: "The coordinate change between trivializations is continuous on the overlap of their base sets."

**Lean 4 Theorem**:
```lean
theorem Trivialization.continuousOn_coordChange (e e' : Trivialization F proj) :
    ContinuousOn (fun p : B × F => e.coordChange e' p.1 p.2)
      ((e.baseSet ∩ e'.baseSet) ×ˢ Set.univ)
```

**Imports**: `Mathlib.Topology.FiberBundle.Trivialization`
**Difficulty**: medium

---

### 2.7 Pretrivialization

**NL Statement**: "A pretrivialization is a partial equivalence that may become a trivialization once the topology is defined, used in bundle construction."

**Lean 4 Definition**:
```lean
structure Pretrivialization (F : Type*) {B : Type*} [TopologicalSpace F] [TopologicalSpace B]
    (proj : Z → B) extends PartialEquiv Z (B × F) where
  baseSet : Set B
  open_baseSet : IsOpen baseSet
  source_eq : source = proj ⁻¹' baseSet
  target_eq : target = baseSet ×ˢ Set.univ
  proj_toFun : ∀ p ∈ source, (toPartialEquiv p).1 = proj p
```

**Imports**: `Mathlib.Topology.FiberBundle.Trivialization`
**Difficulty**: medium

---

### 2.8 Trivialization at Point

**NL Statement**: "In a fiber bundle, every point has a trivialization whose base set contains that point."

**Lean 4 Theorem**:
```lean
theorem FiberBundle.trivializationAt_mem_baseSet [FiberBundle F E] (x : B) :
    x ∈ (trivializationAt F E x).baseSet
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: easy

---

### 2.9 Trivialization Atlas

**NL Statement**: "A fiber bundle comes with an atlas of trivializations covering the entire base space."

**Lean 4 Definition**:
```lean
-- In FiberBundle class
trivializationAtlas : Set (Trivialization F (π F E))
trivializationAt : B → Trivialization F (π F E)
mem_trivializationAtlas : ∀ x, trivializationAt x ∈ trivializationAtlas
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: easy

---

### 2.10 Symm of Trivialization

**NL Statement**: "The inverse of a trivialization maps (x, v) ∈ U × F back to the corresponding point in π⁻¹(U)."

**Lean 4 Definition**:
```lean
def Trivialization.symm : PartialHomeomorph (B × F) Z := e.toPartialHomeomorph.symm

theorem Trivialization.symm_apply (hx : x ∈ e.baseSet) :
    e.symm (x, v) = e.toPartialHomeomorph.symm (x, v)
```

**Imports**: `Mathlib.Topology.FiberBundle.Trivialization`
**Difficulty**: easy

---

## Part 3: Vector Bundle Structure

### 3.1 Vector Bundle Definition

**NL Statement**: "A vector bundle is a fiber bundle where each fiber is a vector space and the trivializations are fiberwise linear."

**Lean 4 Definition**:
```lean
class VectorBundle (R : Type*) [Semiring R] (F : Type*) [TopologicalSpace F]
    [AddCommMonoid F] [Module R F] (E : B → Type*)
    [TopologicalSpace (Bundle.TotalSpace F E)] [∀ x, AddCommMonoid (E x)]
    [∀ x, Module R (E x)] [∀ x, TopologicalSpace (E x)] [FiberBundle F E] where
  trivialization_linear' : ∀ e ∈ trivializationAtlas F E, e.IsLinear R
  continuousOn_coordChange' : ∀ e e' ∈ trivializationAtlas F E,
      ContinuousOn (fun x => e.coordChangeL R e' x) (e.baseSet ∩ e'.baseSet)
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: medium

---

### 3.2 Linear Trivialization

**NL Statement**: "A trivialization is linear if it restricts to a linear isomorphism on each fiber."

**Lean 4 Definition**:
```lean
class Trivialization.IsLinear (e : Trivialization F (π F E)) where
  linear : ∀ x ∈ e.baseSet, IsLinearMap R (fun v => (e ⟨x, v⟩).2)
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: medium

---

### 3.3 Linear Equivalence at Point

**NL Statement**: "For a linear trivialization, the restriction to each fiber is a linear equivalence E_x ≃ₗ[R] F."

**Lean 4 Definition**:
```lean
def Trivialization.linearEquivAt (e : Trivialization F (π F E)) [e.IsLinear R]
    (x : B) (hx : x ∈ e.baseSet) : E x ≃ₗ[R] F
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: medium

---

### 3.4 Continuous Linear Equivalence

**NL Statement**: "In a topological vector bundle, the fiberwise linear equivalence is also continuous, giving E_x ≃L[R] F."

**Lean 4 Definition**:
```lean
def Trivialization.continuousLinearEquivAt [VectorBundle R F E]
    (e : Trivialization F (π F E)) (he : e ∈ trivializationAtlas F E)
    (x : B) (hx : x ∈ e.baseSet) : E x ≃L[R] F
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: medium

---

### 3.5 Coordinate Change is Linear

**NL Statement**: "The coordinate change between vector bundle trivializations is a continuous linear map at each point of the overlap."

**Lean 4 Definition**:
```lean
def Trivialization.coordChangeL (e e' : Trivialization F (π F E)) [e.IsLinear R] [e'.IsLinear R]
    (x : B) : F →L[R] F :=
  if hx : x ∈ e.baseSet ∩ e'.baseSet then
    (e'.continuousLinearEquivAt R x hx.2).toContinuousLinearMap.comp
      (e.continuousLinearEquivAt R x hx.1).symm.toContinuousLinearMap
  else 0
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: hard

---

### 3.6 Coordinate Change Continuity (Vector Bundle)

**NL Statement**: "In a vector bundle, coordinate changes vary continuously with the base point in the operator norm topology."

**Lean 4 Theorem**:
```lean
theorem VectorBundle.continuousOn_coordChange [VectorBundle R F E]
    (e e' : Trivialization F (π F E)) (he : e ∈ trivializationAtlas F E)
    (he' : e' ∈ trivializationAtlas F E) :
    ContinuousOn (fun x => e.coordChangeL R e' x) (e.baseSet ∩ e'.baseSet)
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: medium

---

### 3.7 VectorBundleCore

**NL Statement**: "A vector bundle core specifies a vector bundle via linear coordinate changes: open sets, and continuous linear transition functions satisfying the cocycle condition."

**Lean 4 Definition**:
```lean
structure VectorBundleCore (R : Type*) [Semiring R] (ι : Type*) (B : Type*)
    [TopologicalSpace B] (F : Type*) [TopologicalSpace F]
    [AddCommMonoid F] [Module R F] where
  baseSet : ι → Set B
  isOpen_baseSet : ∀ i, IsOpen (baseSet i)
  indexAt : B → ι
  mem_baseSet_at : ∀ x, x ∈ baseSet (indexAt x)
  coordChange : ι → ι → B → F →L[R] F
  coordChange_self : ∀ i x ∈ baseSet i, coordChange i i x = ContinuousLinearMap.id R F
  coordChange_comp : ∀ i j k x ∈ baseSet i ∩ baseSet j ∩ baseSet k,
      (coordChange j k x).comp (coordChange i j x) = coordChange i k x
  continuousOn_coordChange : ∀ i j, ContinuousOn (coordChange i j) (baseSet i ∩ baseSet j)
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: hard

---

### 3.8 Zero Section

**NL Statement**: "Every vector bundle has a canonical zero section s₀ : B → E mapping each point to the zero vector in its fiber."

**Lean 4 Definition**:
```lean
def Bundle.zeroSection (F : Type*) (E : B → Type*) [∀ x, Zero (E x)] :
    B → Bundle.TotalSpace F E :=
  fun x => ⟨x, 0⟩

theorem Bundle.continuous_zeroSection [VectorBundle R F E] :
    Continuous (Bundle.zeroSection F E)
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: easy

---

### 3.9 Fiber Addition

**NL Statement**: "In a vector bundle, fibers have addition: for v, w ∈ E_x, their sum v + w ∈ E_x is well-defined."

**Lean 4 Instance**:
```lean
-- Fiber inherits AddCommMonoid structure
instance [∀ x, AddCommMonoid (E x)] (x : B) : AddCommMonoid (E x)
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: easy

---

### 3.10 Fiber Scalar Multiplication

**NL Statement**: "In a vector bundle over ring R, each fiber is an R-module with scalar multiplication r • v for r : R and v ∈ E_x."

**Lean 4 Instance**:
```lean
-- Fiber inherits Module structure
instance [∀ x, Module R (E x)] (x : B) : Module R (E x)
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: easy

---

### 3.11 Vector Bundle from Core

**NL Statement**: "A VectorBundleCore determines a vector bundle with the constructed topology and linear structure."

**Lean 4 Instance**:
```lean
instance VectorBundleCore.vectorBundle [TopologicalSpace F] [AddCommMonoid F] [Module R F] :
    VectorBundle R F Z.Fiber
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: hard

---

### 3.12 Rank of Vector Bundle

**NL Statement**: "The rank of a vector bundle is the dimension of its fiber F as a vector space."

**Lean 4 Definition**:
```lean
-- For finite-rank bundles with fiber F
-- rank = Module.finrank R F
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: easy

---

## Part 4: Smooth Vector Bundles

### 4.1 Smooth Vector Bundle Definition

**NL Statement**: "A Cⁿ vector bundle is a vector bundle over a smooth manifold with Cⁿ transition functions between trivializations."

**Lean 4 Definition**:
```lean
class ContMDiffVectorBundle (n : ℕ∞) (F : Type*) [NormedAddCommGroup F] [NormedSpace 𝕜 F]
    (E : B → Type*) [∀ x, AddCommMonoid (E x)] [∀ x, Module 𝕜 (E x)]
    [∀ x, TopologicalSpace (E x)] [FiberBundle F E] [VectorBundle 𝕜 F E]
    [∀ x, TopologicalAddGroup (E x)] [∀ x, ContinuousSMul 𝕜 (E x)] where
  contMDiff_coordChange : ∀ e e' ∈ trivializationAtlas F E,
      ContMDiff I 𝓘(𝕜, F →L[𝕜] F) n (fun x => e.coordChangeL 𝕜 e' x)
```

**Imports**: `Mathlib.Geometry.Manifold.VectorBundle.Basic`
**Difficulty**: hard

---

### 4.2 Smooth Bundle is Smooth Manifold

**NL Statement**: "A Cⁿ vector bundle is naturally a Cⁿ manifold, with the total space inheriting smooth structure from base and fiber."

**Lean 4 Theorem**:
```lean
theorem ContMDiffVectorBundle.isManifold [ContMDiffVectorBundle n F E] :
    IsManifold (I.prod 𝓘(𝕜, F)) n (Bundle.TotalSpace F E)
```

**Imports**: `Mathlib.Geometry.Manifold.VectorBundle.Basic`
**Difficulty**: hard

---

### 4.3 Smooth Transition Functions

**NL Statement**: "In a smooth vector bundle, the coordinate change functions are smooth maps from the overlap to the space of continuous linear maps."

**Lean 4 Theorem**:
```lean
theorem ContMDiffVectorBundle.contMDiff_coordChange [ContMDiffVectorBundle n F E]
    (e e' : Trivialization F (π F E)) (he : e ∈ trivializationAtlas F E)
    (he' : e' ∈ trivializationAtlas F E) :
    ContMDiff I 𝓘(𝕜, F →L[𝕜] F) n (fun x => e.coordChangeL 𝕜 e' x)
```

**Imports**: `Mathlib.Geometry.Manifold.VectorBundle.Basic`
**Difficulty**: medium

---

### 4.4 Trivial Bundle is Smooth

**NL Statement**: "The trivial bundle B × F over a smooth manifold B is a smooth vector bundle."

**Lean 4 Instance**:
```lean
instance Bundle.Trivial.contMDiffVectorBundle :
    ContMDiffVectorBundle n F (Bundle.Trivial B F)
```

**Imports**: `Mathlib.Geometry.Manifold.VectorBundle.Basic`
**Difficulty**: easy

---

### 4.5 Tangent Bundle is Smooth

**NL Statement**: "The tangent bundle of a Cⁿ⁺¹ manifold is a Cⁿ vector bundle."

**Lean 4 Theorem**:
```lean
instance TangentBundle.contMDiffVectorBundle :
    ContMDiffVectorBundle n E (TangentSpace I : M → Type*)
```

**Imports**: `Mathlib.Geometry.Manifold.VectorBundle.Tangent`
**Difficulty**: hard

---

### 4.6 Smooth Section

**NL Statement**: "A section s : B → E of a vector bundle is smooth if the composite map B → E → B × F (via any trivialization) is smooth."

**Lean 4 Definition**:
```lean
def ContMDiff.section (s : ∀ x, E x) : Prop :=
  ContMDiff I (I.prod 𝓘(𝕜, F)) n (fun x => Bundle.TotalSpace.mk x (s x))
```

**Imports**: `Mathlib.Geometry.Manifold.VectorBundle.Basic`
**Difficulty**: medium

---

### 4.7 Direct Sum of Smooth Bundles

**NL Statement**: "The direct sum of two Cⁿ vector bundles is again a Cⁿ vector bundle."

**Lean 4 Instance**:
```lean
instance Bundle.Prod.contMDiffVectorBundle [ContMDiffVectorBundle n F₁ E₁]
    [ContMDiffVectorBundle n F₂ E₂] :
    ContMDiffVectorBundle n (F₁ × F₂) (E₁ ×ᵇ E₂)
```

**Imports**: `Mathlib.Geometry.Manifold.VectorBundle.Basic`
**Difficulty**: medium

---

### 4.8 Charted Space Structure

**NL Statement**: "A fiber bundle over a charted space is naturally a charted space modeled on B × F."

**Lean 4 Instance**:
```lean
instance FiberBundle.chartedSpace [FiberBundle F E] :
    ChartedSpace (ModelProd H F) (Bundle.TotalSpace F E)
```

**Imports**: `Mathlib.Geometry.Manifold.VectorBundle.Basic`
**Difficulty**: medium

---

## Part 5: Bundle Constructions

### 5.1 Trivial Bundle

**NL Statement**: "The trivial bundle over B with fiber F is the product space B × F with projection onto the first factor."

**Lean 4 Definition**:
```lean
def Bundle.Trivial (B : Type*) (F : Type*) : B → Type* := fun _ => F

instance Bundle.Trivial.fiberBundle : FiberBundle F (Bundle.Trivial B F)
```

**Imports**: `Mathlib.Topology.FiberBundle.Constructions`
**Difficulty**: easy

---

### 5.2 Pullback Bundle

**NL Statement**: "Given a bundle E → B and a map f : B' → B, the pullback bundle f*E → B' has fiber (f*E)_x = E_{f(x)}."

**Lean 4 Definition**:
```lean
def Bundle.Pullback (f : B' → B) (E : B → Type*) : B' → Type* := fun x => E (f x)

instance Bundle.Pullback.fiberBundle [FiberBundle F E] (f : B' → B) (hf : Continuous f) :
    FiberBundle F (Bundle.Pullback f E)
```

**Imports**: `Mathlib.Topology.FiberBundle.Constructions`
**Difficulty**: medium

---

### 5.3 Pullback Preserves Vector Bundle

**NL Statement**: "The pullback of a vector bundle is again a vector bundle with the same fiber structure."

**Lean 4 Instance**:
```lean
instance Bundle.Pullback.vectorBundle [VectorBundle R F E] (f : B' → B) (hf : Continuous f) :
    VectorBundle R F (Bundle.Pullback f E)
```

**Imports**: `Mathlib.Topology.VectorBundle.Pullback`
**Difficulty**: medium

---

### 5.4 Fiberwise Product

**NL Statement**: "Given bundles E₁ and E₂ over B, the fiberwise product E₁ ×ᵇ E₂ has fiber (E₁ ×ᵇ E₂)_x = (E₁)_x × (E₂)_x."

**Lean 4 Definition**:
```lean
def Bundle.Prod (E₁ : B → Type*) (E₂ : B → Type*) : B → Type* :=
  fun x => E₁ x × E₂ x

instance Bundle.Prod.fiberBundle [FiberBundle F₁ E₁] [FiberBundle F₂ E₂] :
    FiberBundle (F₁ × F₂) (E₁ ×ᵇ E₂)
```

**Imports**: `Mathlib.Topology.FiberBundle.Constructions`
**Difficulty**: medium

---

### 5.5 Fiberwise Product is Vector Bundle

**NL Statement**: "The fiberwise product of vector bundles is a vector bundle with componentwise operations."

**Lean 4 Instance**:
```lean
instance Bundle.Prod.vectorBundle [VectorBundle R F₁ E₁] [VectorBundle R F₂ E₂] :
    VectorBundle R (F₁ × F₂) (E₁ ×ᵇ E₂)
```

**Imports**: `Mathlib.Topology.VectorBundle.Constructions`
**Difficulty**: medium

---

### 5.6 Restriction to Subspace

**NL Statement**: "A fiber bundle over B restricts to a fiber bundle over any open subspace U ⊆ B."

**Lean 4 Theorem**:
```lean
-- Restriction via pullback along inclusion
instance (U : Opens B) : FiberBundle F (Bundle.Pullback (↑· : U → B) E)
```

**Imports**: `Mathlib.Topology.FiberBundle.Constructions`
**Difficulty**: easy

---

### 5.7 Hom Bundle

**NL Statement**: "For vector bundles E₁ and E₂ over B, the Hom bundle has fiber Hom(E₁_x, E₂_x), the space of linear maps between fibers."

**Lean 4 Definition**:
```lean
def Bundle.ContinuousLinearMap (E₁ : B → Type*) (E₂ : B → Type*) : B → Type* :=
  fun x => E₁ x →L[R] E₂ x

instance Bundle.ContinuousLinearMap.vectorBundle [VectorBundle R F₁ E₁] [VectorBundle R F₂ E₂] :
    VectorBundle R (F₁ →L[R] F₂) (Bundle.ContinuousLinearMap R E₁ E₂)
```

**Imports**: `Mathlib.Topology.VectorBundle.Hom`
**Difficulty**: hard

---

### 5.8 Dual Bundle

**NL Statement**: "The dual bundle E* of a vector bundle E has fiber (E*)_x = (E_x)*, the continuous dual of each fiber."

**Lean 4 Definition**:
```lean
-- Special case of Hom bundle with E₂ = trivial R bundle
def Bundle.Dual (E : B → Type*) : B → Type* :=
  fun x => NormedSpace.Dual R (E x)
```

**Imports**: `Mathlib.Topology.VectorBundle.Hom`
**Difficulty**: medium

---

### 5.9 Tensor Product Bundle

**NL Statement**: "For vector bundles E₁ and E₂, their tensor product bundle has fiber (E₁ ⊗ E₂)_x = (E₁)_x ⊗ (E₂)_x."

**Lean 4 Definition**:
```lean
-- Defined via bilinear maps
def Bundle.TensorProduct (E₁ : B → Type*) (E₂ : B → Type*) : B → Type* :=
  fun x => E₁ x ⊗[R] E₂ x
```

**Imports**: `Mathlib.Topology.VectorBundle.Constructions`
**Difficulty**: hard

---

### 5.10 Exterior Power Bundle

**NL Statement**: "The k-th exterior power bundle ⋀ᵏE has fiber (⋀ᵏE)_x = ⋀ᵏ(E_x)."

**Lean 4 Definition**:
```lean
-- Defined via alternating maps
def Bundle.ExteriorPower (k : ℕ) (E : B → Type*) : B → Type* :=
  fun x => ExteriorAlgebra.exteriorPower R k (E x)
```

**Imports**: `Mathlib.Topology.VectorBundle.Constructions`
**Difficulty**: hard

---

## Part 6: Bundle Morphisms

### 6.1 Bundle Morphism

**NL Statement**: "A bundle morphism from E → B to E' → B' consists of maps f : B → B' and φ : E → E' such that φ covers f (the diagram commutes)."

**Lean 4 Definition**:
```lean
structure BundleMorphism (E : B → Type*) (E' : B' → Type*) where
  baseMap : B → B'
  totalMap : Bundle.TotalSpace F E → Bundle.TotalSpace F' E'
  covers : ∀ p, (totalMap p).proj = baseMap p.proj
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: medium

---

### 6.2 Fiberwise Linear Map

**NL Statement**: "A vector bundle morphism over the identity is a family of linear maps φ_x : E_x → E'_x varying continuously with x."

**Lean 4 Definition**:
```lean
-- Family of continuous linear maps between fibers
def Bundle.ContinuousLinearMapSection (E E' : B → Type*) [VectorBundle R F E] [VectorBundle R F' E'] :=
  ∀ x, E x →L[R] E' x
```

**Imports**: `Mathlib.Topology.VectorBundle.Hom`
**Difficulty**: medium

---

### 6.3 Bundle Isomorphism

**NL Statement**: "A bundle isomorphism is a bundle morphism with an inverse that is also a bundle morphism."

**Lean 4 Definition**:
```lean
structure BundleEquiv (E : B → Type*) (E' : B → Type*) extends
    Bundle.TotalSpace F E ≃ Bundle.TotalSpace F' E' where
  covers : ∀ p, (toEquiv p).proj = p.proj
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: medium

---

### 6.4 Continuous Linear Map at Point

**NL Statement**: "For a fiberwise linear map, evaluation at a point gives a continuous linear map between fibers."

**Lean 4 Definition**:
```lean
def Trivialization.continuousLinearMapAt (e : Trivialization F (π F E)) [e.IsLinear R]
    (x : B) : E x →L[R] F :=
  if hx : x ∈ e.baseSet then (e.continuousLinearEquivAt R x hx).toContinuousLinearMap else 0
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: medium

---

### 6.5 Bundle Map Continuity

**NL Statement**: "A fiberwise linear map φ = (φ_x) is continuous if and only if it is continuous in local trivializations."

**Lean 4 Theorem**:
```lean
theorem Trivialization.continuous_linearMapAt (e : Trivialization F (π F E)) [e.IsLinear R]
    (e' : Trivialization F' (π F' E')) [e'.IsLinear R]
    (φ : ∀ x, E x →L[R] E' x) :
    Continuous (fun p : Bundle.TotalSpace F E => Bundle.TotalSpace.mk p.proj (φ p.proj p.snd)) ↔
    ContinuousOn (fun x => e'.continuousLinearMapAt R x ∘L φ x ∘L (e.continuousLinearMapAt R x).symm)
      (e.baseSet ∩ e'.baseSet)
```

**Imports**: `Mathlib.Topology.VectorBundle.Hom`
**Difficulty**: hard

---

### 6.6 Composition of Bundle Maps

**NL Statement**: "Bundle morphisms compose: if φ : E → E' and ψ : E' → E'' are bundle morphisms, so is ψ ∘ φ."

**Lean 4 Theorem**:
```lean
-- Composition of fiberwise maps
def BundleMorphism.comp (ψ : BundleMorphism E' E'') (φ : BundleMorphism E E') :
    BundleMorphism E E'' where
  baseMap := ψ.baseMap ∘ φ.baseMap
  totalMap := ψ.totalMap ∘ φ.totalMap
  covers := ...
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: medium

---

### 6.7 Identity Bundle Map

**NL Statement**: "The identity map on a bundle is a bundle isomorphism."

**Lean 4 Definition**:
```lean
def BundleEquiv.refl (E : B → Type*) : BundleEquiv E E where
  toEquiv := Equiv.refl _
  covers := fun _ => rfl
```

**Imports**: `Mathlib.Topology.FiberBundle.Basic`
**Difficulty**: easy

---

### 6.8 Kernel and Image Bundles

**NL Statement**: "For a bundle morphism φ : E → E', the kernel bundle ker(φ) has fiber ker(φ_x) ⊆ E_x at each point."

**Lean 4 Definition**:
```lean
-- Kernel subbundle
def Bundle.ker (φ : ∀ x, E x →L[R] E' x) : B → Type* :=
  fun x => (φ x).ker
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: medium

---

## Part 7: Principal Bundles

### 7.1 Principal Bundle Definition (Conceptual)

**NL Statement**: "A principal G-bundle is a fiber bundle with fiber a Lie group G acting freely and transitively on each fiber by right multiplication."

**Lean 4 Template** (NOT YET FORMALIZED):
```lean
-- Conceptual structure
structure PrincipalBundle (G : Type*) [Group G] [TopologicalGroup G]
    (P : Type*) [TopologicalSpace P] (B : Type*) [TopologicalSpace B] where
  proj : P → B
  action : P → G → P
  action_free : ∀ p g, action p g = p → g = 1
  action_transitive : ∀ p q, proj p = proj q → ∃ g, action p g = q
  locally_trivial : ∀ x : B, ∃ U : Set B, x ∈ U ∧ IsOpen U ∧
    ∃ φ : proj ⁻¹' U ≃ U × G, ∀ p ∈ proj ⁻¹' U, (φ p).1 = proj p
```

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 7.2 Structure Group

**NL Statement**: "The structure group G of a principal bundle acts on the fibers by right multiplication, and transition functions take values in G."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 7.3 Principal Bundle Transition Functions

**NL Statement**: "Transition functions of a principal G-bundle are maps gᵢⱼ : Uᵢ ∩ Uⱼ → G satisfying the cocycle condition gᵢⱼ · gⱼₖ = gᵢₖ."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 7.4 Associated Vector Bundle (Conceptual)

**NL Statement**: "Given a principal G-bundle P and a representation ρ : G → GL(V), the associated bundle P ×_G V = (P × V) / G is a vector bundle with fiber V."

**Lean 4 Template** (NOT YET FORMALIZED):
```lean
-- Conceptual: associated bundle construction
def AssociatedBundle (P : PrincipalBundle G) (V : Type*) [AddCommGroup V] [Module R V]
    (ρ : G →* (V ≃ₗ[R] V)) : B → Type* :=
  fun x => Quotient (associatedEquivRel P V ρ x)
```

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 7.5 Frame Bundle (Conceptual)

**NL Statement**: "The frame bundle Fr(E) of a rank-n vector bundle E → B is a principal GL(n)-bundle whose fiber at x is the set of all bases of E_x."

**Lean 4 Template** (NOT YET FORMALIZED):
```lean
-- Conceptual frame bundle
def FrameBundle (E : B → Type*) [VectorBundle R F E] [FiniteDimensional R F] : B → Type* :=
  fun x => Basis (Fin n) R (E x)
```

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 7.6 Reduction of Structure Group (Conceptual)

**NL Statement**: "A reduction of structure group from G to H ⊆ G is a principal H-subbundle of a principal G-bundle."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 7.7 Gauge Transformations (Conceptual)

**NL Statement**: "A gauge transformation of a principal G-bundle P is a G-equivariant automorphism of P covering the identity on B."

**Lean 4 Template** (NOT YET FORMALIZED):
```lean
-- Conceptual gauge transformation
structure GaugeTransformation (P : PrincipalBundle G B) where
  map : P → P
  equivariant : ∀ p g, map (action p g) = action (map p) g
  covers_id : ∀ p, proj (map p) = proj p
```

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

### 7.8 Connection on Principal Bundle (Conceptual)

**NL Statement**: "A connection on a principal G-bundle is a G-equivariant splitting of the tangent bundle TP = HP ⊕ VP into horizontal and vertical subbundles."

**Status**: NOT FORMALIZED
**Difficulty**: very hard

---

## Part 8: Classical Examples

### 8.1 Tangent Bundle

**NL Statement**: "The tangent bundle TM of a smooth manifold M is a vector bundle with fiber T_xM ≅ ℝⁿ at each point."

**Lean 4 Definition**:
```lean
abbrev TangentBundle (I : ModelWithCorners 𝕜 E H) (M : Type*) :=
  Bundle.TotalSpace E (TangentSpace I : M → Type*)

instance TangentSpace.fiberBundle : FiberBundle E (TangentSpace I : M → Type*)

instance TangentSpace.vectorBundle : VectorBundle 𝕜 E (TangentSpace I : M → Type*)
```

**Imports**: `Mathlib.Geometry.Manifold.VectorBundle.Tangent`
**Difficulty**: medium

---

### 8.2 Cotangent Bundle

**NL Statement**: "The cotangent bundle T*M is the dual of the tangent bundle, with fiber (T*M)_x = (T_xM)*, the space of linear forms on the tangent space."

**Lean 4 Definition**:
```lean
-- Cotangent bundle as dual of tangent bundle
abbrev CotangentSpace (I : ModelWithCorners 𝕜 E H) (x : M) := NormedSpace.Dual 𝕜 (TangentSpace I x)

abbrev CotangentBundle (I : ModelWithCorners 𝕜 E H) (M : Type*) :=
  Bundle.TotalSpace (NormedSpace.Dual 𝕜 E) (CotangentSpace I : M → Type*)
```

**Imports**: `Mathlib.Geometry.Manifold.VectorBundle.Cotangent`
**Difficulty**: medium

---

### 8.3 Trivial Line Bundle

**NL Statement**: "The trivial line bundle over B is B × ℝ (or B × ℂ), the simplest example of a rank-1 vector bundle."

**Lean 4 Instance**:
```lean
instance : VectorBundle ℝ ℝ (Bundle.Trivial B ℝ)
```

**Imports**: `Mathlib.Topology.VectorBundle.Basic`
**Difficulty**: easy

---

### 8.4 Möbius Band as Line Bundle

**NL Statement**: "The Möbius band is a non-trivial line bundle over S¹, the simplest example of a non-orientable bundle."

**Status**: PARTIAL - Can be constructed via FiberBundleCore with appropriate transition
**Difficulty**: medium

---

### 8.5 Hopf Fibration

**NL Statement**: "The Hopf fibration S³ → S² is a principal S¹-bundle, exhibiting S³ as a circle bundle over S²."

**Status**: NOT FORMALIZED (requires principal bundle infrastructure)
**Difficulty**: very hard

---

### 8.6 Tautological Bundle

**NL Statement**: "The tautological line bundle over projective space ℙⁿ has fiber at a line ℓ the line ℓ itself."

**Status**: PARTIAL - Projective space exists but tautological bundle not formalized
**Difficulty**: hard

---

### 8.7 Normal Bundle

**NL Statement**: "For a submanifold N ⊆ M, the normal bundle ν(N) has fiber at x the quotient T_xM / T_xN."

**Status**: PARTIAL - Requires submanifold formalization
**Difficulty**: hard

---

## Standard Setup

**Lean 4 Imports**:
```lean
import Mathlib.Topology.FiberBundle.Basic
import Mathlib.Topology.FiberBundle.Trivialization
import Mathlib.Topology.FiberBundle.Constructions
import Mathlib.Topology.VectorBundle.Basic
import Mathlib.Topology.VectorBundle.Hom
import Mathlib.Topology.VectorBundle.Pullback
import Mathlib.Geometry.Manifold.VectorBundle.Basic
import Mathlib.Geometry.Manifold.VectorBundle.Tangent

variable {B : Type*} [TopologicalSpace B]
variable {F : Type*} [TopologicalSpace F]
variable {E : B → Type*} [TopologicalSpace (Bundle.TotalSpace F E)]
variable [∀ x, TopologicalSpace (E x)]
variable {R : Type*} [Semiring R]
```

---

## Notation Reference

| Math Notation | Lean 4 Notation | Description |
|---------------|-----------------|-------------|
| E → B | `Bundle.TotalSpace F E` | Total space of bundle |
| π : E → B | `Bundle.TotalSpace.proj` | Projection map |
| E_x | `E x` | Fiber over x |
| E ×_B E' | `E ×ᵇ E'` or `Bundle.Prod E E'` | Fiberwise product |
| f*E | `Bundle.Pullback f E` | Pullback bundle |
| Hom(E, E') | `Bundle.ContinuousLinearMap R E E'` | Bundle of linear maps |
| TM | `TangentBundle I M` | Tangent bundle |
| T*M | `CotangentBundle I M` | Cotangent bundle |

---

## Sources

- [Mathlib.Topology.FiberBundle.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Topology/FiberBundle/Basic.html)
- [Mathlib.Topology.VectorBundle.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Topology/VectorBundle/Basic.html)
- [Mathlib.Geometry.Manifold.VectorBundle.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/VectorBundle/Basic.html)
- [Fiber bundle - Wikipedia](https://en.wikipedia.org/wiki/Fiber_bundle)
- [Principal bundle - Wikipedia](https://en.wikipedia.org/wiki/Principal_bundle)
- [Ralph Cohen's Fiber Bundle Lecture Notes](http://math.stanford.edu/~ralph/fiber.pdf)
