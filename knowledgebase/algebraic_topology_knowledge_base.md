# Algebraic Topology Knowledge Base

**Domain**: Algebraic Topology (Homotopy Theory, Simplicial Sets, Topological Methods)
**Lean 4 Coverage**: GOOD (homotopy theory and simplicial sets well-covered)
**Source**: Mathlib4 `Topology.Homotopy.*` and `AlgebraicTopology.*` modules
**Last Updated**: 2025-12-24

---

## Overview

This knowledge base covers algebraic topology formalization in Lean 4/Mathlib, focusing on **homotopy theory, simplicial sets, and chain homotopy**.

**Key Gap**: CW complexes, singular homology, Mayer-Vietoris sequence, and Brouwer fixed point theorem (#36) not yet formalized. Fundamental group computations require external library (ComputationalPathsLean).

---

## Related Knowledge Bases

### Prerequisites
- **Homological Algebra** (`homological_algebra_knowledge_base.md`): Chain complexes, exact sequences, snake lemma, derived functors
- **Category Theory** (`category_theory_knowledge_base.md`): Functors, natural transformations, limits/colimits
- **Topology** (`topology_knowledge_base.md`): Continuous maps, compact spaces, connectedness

### Foundational Content (See Homological Algebra KB)

For chain complex theory and exact sequences, see the **Homological Algebra KB** which provides comprehensive coverage of:
- ComplexShape, HomologicalComplex, Chain/Cochain complexes
- Homology groups via ShortComplex machinery
- ShortComplex, Exactness, Short exact sequences
- Snake lemma, Five lemma, Diagram lemmas

---

## 1. HOMOTOPY THEORY

### 1.1 Homotopy Between Maps

**Concept**: Continuous deformation between two maps.

**NL Statement**: "Two continuous maps f₀, f₁ : X → Y are homotopic if there exists a continuous map H : [0,1] × X → Y such that H(0, x) = f₀(x) and H(1, x) = f₁(x)."

**Lean 4 Definition**:
```lean
structure ContinuousMap.Homotopy (f₀ f₁ : C(X, Y)) extends C(I × X, Y) where
  map_zero_left : ∀ x, toFun (0, x) = f₀ x
  map_one_left : ∀ x, toFun (1, x) = f₁ x

-- Homotopy as a relation
def ContinuousMap.Homotopic (f₀ f₁ : C(X, Y)) : Prop :=
  Nonempty (Homotopy f₀ f₁)
```

**Imports**: `Mathlib.Topology.Homotopy.Basic`

**Difficulty**: medium

---

### 1.2 Homotopy Equivalence

**Concept**: Two spaces have the same homotopy type.

**NL Statement**: "Spaces X and Y are homotopy equivalent (X ≃ₕ Y) if there exist continuous maps f : X → Y and g : Y → X such that g ∘ f ≃ id_X and f ∘ g ≃ id_Y."

**Lean 4 Definition**:
```lean
structure ContinuousMap.HomotopyEquiv (X : Type*) (Y : Type*)
    [TopologicalSpace X] [TopologicalSpace Y] where
  toFun : C(X, Y)
  invFun : C(Y, X)
  left_inv : (invFun.comp toFun).Homotopic (ContinuousMap.id X)
  right_inv : (toFun.comp invFun).Homotopic (ContinuousMap.id Y)

notation:25 X " ≃ₕ " Y => ContinuousMap.HomotopyEquiv X Y
```

**Imports**: `Mathlib.Topology.Homotopy.Equiv`

**Difficulty**: medium

---

### 1.3 Homotopy is an Equivalence Relation

**Concept**: Homotopy satisfies reflexivity, symmetry, and transitivity.

**NL Statement**: "The homotopy relation ~ on continuous maps is an equivalence relation: every map is homotopic to itself, homotopy can be reversed, and homotopies can be composed."

**Lean 4 Theorem**:
```lean
instance : Reflexive (ContinuousMap.Homotopic : C(X, Y) → C(X, Y) → Prop)
instance : Symmetric (ContinuousMap.Homotopic : C(X, Y) → C(X, Y) → Prop)
instance : Transitive (ContinuousMap.Homotopic : C(X, Y) → C(X, Y) → Prop)

-- Explicit constructions:
def ContinuousMap.Homotopy.refl (f : C(X, Y)) : Homotopy f f
def ContinuousMap.Homotopy.symm {f₀ f₁ : C(X, Y)} : Homotopy f₀ f₁ → Homotopy f₁ f₀
def ContinuousMap.Homotopy.trans {f₀ f₁ f₂ : C(X, Y)} :
    Homotopy f₀ f₁ → Homotopy f₁ f₂ → Homotopy f₀ f₂
```

**Imports**: `Mathlib.Topology.Homotopy.Basic`

**Difficulty**: medium

---

### 1.4 Relative Homotopy

**Concept**: Homotopy that keeps a subset fixed.

**NL Statement**: "Two maps f₀, f₁ : X → Y are homotopic relative to S ⊆ X if the homotopy H satisfies H(t, x) = f₀(x) = f₁(x) for all t ∈ [0,1] and x ∈ S."

**Lean 4 Definition**:
```lean
def ContinuousMap.HomotopyRel (f₀ f₁ : C(X, Y)) (S : Set X) :=
  ContinuousMap.HomotopyWith f₀ f₁ (fun f => ∀ x ∈ S, f x = f₀ x)

def ContinuousMap.HomotopicRel (f₀ f₁ : C(X, Y)) (S : Set X) : Prop :=
  Nonempty (HomotopyRel f₀ f₁ S)
```

**Imports**: `Mathlib.Topology.Homotopy.Basic`

**Difficulty**: medium

---

### 1.5 Path Homotopy

**Concept**: Homotopy between paths with fixed endpoints.

**NL Statement**: "Two paths p, q : [0,1] → X from a to b are path homotopic if there is a continuous deformation keeping the endpoints a and b fixed throughout."

**Lean 4 Definition**:
```lean
-- Path homotopy is relative homotopy with S = {0, 1}
def Path.Homotopic (p q : Path x y) : Prop :=
  p.toContinuousMap.HomotopicRel q.toContinuousMap {0, 1}
```

**Imports**: `Mathlib.Topology.Homotopy.Path`

**Difficulty**: medium

---

## 2. SIMPLICIAL SETS

### 2.1 Simplicial Set

**Concept**: Combinatorial model for topological spaces.

**NL Statement**: "A simplicial set is a contravariant functor from the simplex category Δ to Type, i.e., a sequence of sets with face and degeneracy maps satisfying simplicial identities."

**Lean 4 Definition**:
```lean
-- SSet is an abbreviation for simplicial objects in Type
def SSet : Type (u + 1) := SimplicialObject (Type u)

-- SimplicialObject C := Δᵒᵖ ⥤ C
```

**Imports**: `Mathlib.AlgebraicTopology.SimplicialSet.Basic`

**Difficulty**: medium

---

### 2.2 Simplex Category

**Concept**: Category of finite ordinals and order-preserving maps.

**NL Statement**: "The simplex category Δ has objects [n] = {0, 1, ..., n} for n ∈ ℕ and morphisms are order-preserving functions."

**Lean 4 Definition**:
```lean
-- SimplexCategory.mk n represents [n]
-- Morphisms are order-preserving maps
structure SimplexCategory where
  len : ℕ

-- Face and degeneracy maps
def SimplexCategory.δ (n : ℕ) (i : Fin (n + 2)) :
    SimplexCategory.mk n ⟶ SimplexCategory.mk (n + 1)

def SimplexCategory.σ (n : ℕ) (i : Fin (n + 1)) :
    SimplexCategory.mk (n + 1) ⟶ SimplexCategory.mk n
```

**Imports**: `Mathlib.AlgebraicTopology.SimplexCategory`

**Difficulty**: medium

---

### 2.3 Standard Simplex

**Concept**: Representable functor in simplicial sets.

**NL Statement**: "The n-th standard simplex Δ[n] is the representable functor (Yoneda embedding), where k-simplices are order-preserving maps [k] → [n]."

**Lean 4 Definition**:
```lean
-- The n-simplex as Yoneda embedding
def standardSimplex (n : ℕ) : SSet := yoneda.obj (SimplexCategory.mk n)
```

**Imports**: `Mathlib.AlgebraicTopology.SimplicialSet.Basic`

**Difficulty**: medium

---

### 2.4 Face and Degeneracy Maps

**Concept**: Structure maps in simplicial objects.

**NL Statement**: "Face maps δᵢ : [n-1] → [n] skip the i-th vertex. Degeneracy maps σᵢ : [n+1] → [n] repeat the i-th vertex. They satisfy simplicial identities."

**Lean 4 Properties**:
```lean
-- Simplicial identities (key relations):
-- δⱼ ∘ δᵢ = δᵢ ∘ δⱼ₋₁  (if i < j)
-- σⱼ ∘ σᵢ = σᵢ ∘ σⱼ₊₁  (if i ≤ j)
-- Plus mixed relations for δ ∘ σ
```

**Imports**: `Mathlib.AlgebraicTopology.SimplexCategory`

**Difficulty**: medium

---

## 3. CHAIN HOMOTOPY

### 3.1 Chain Map

**Concept**: Morphism between chain complexes.

**NL Statement**: "A chain map f : C → D between chain complexes is a family of morphisms fₙ : Cₙ → Dₙ commuting with the differentials: fₙ₋₁ ∘ ∂ = ∂ ∘ fₙ."

**Lean 4 Definition**:
```lean
-- Chain maps are morphisms in the category of HomologicalComplex
-- f : HomologicalComplex C c ⟶ HomologicalComplex C c
-- satisfying naturality with differentials
```

**Imports**: `Mathlib.Algebra.Homology.HomologicalComplex`

**Difficulty**: medium

---

### 3.2 Chain Homotopy

**Concept**: Two chain maps inducing same map on homology.

**NL Statement**: "Chain maps f, g : C → D are chain homotopic if there exist maps hₙ : Cₙ → Dₙ₊₁ such that f - g = ∂h + h∂."

**Lean 4 Definition**:
```lean
-- Homotopy between chain maps
structure Homotopy (f g : K ⟶ L) where
  hom : ∀ i j, K.X i ⟶ L.X j
  zero : ∀ i j, ¬c.Rel j i → hom i j = 0
  comm : ∀ i, f.f i - g.f i = d_next i (hom i) + prev_d i (hom i)
```

**Imports**: `Mathlib.Algebra.Homology.Homotopy`

**Difficulty**: hard

---

### 3.3 Homotopy Equivalence of Complexes

**Concept**: Chain complexes with same homology up to isomorphism.

**NL Statement**: "Chain complexes C and D are homotopy equivalent if there exist chain maps f : C → D and g : D → C such that g ∘ f and f ∘ g are chain homotopic to the respective identities."

**Lean 4 Definition**:
```lean
structure HomotopyEquiv (C D : HomologicalComplex V c) where
  hom : C ⟶ D
  inv : D ⟶ C
  homotopyHomInvId : Homotopy (hom ≫ inv) (𝟙 C)
  homotopyInvHomId : Homotopy (inv ≫ hom) (𝟙 D)
```

**Imports**: `Mathlib.Algebra.Homology.Homotopy`

**Difficulty**: hard

---

## 4. MISSING PRIORITY THEOREMS (GAPS)

### 4.1 Brouwer Fixed Point Theorem (#36) - IN PROGRESS

**NL Statement**: "Every continuous map f : Dⁿ → Dⁿ from the n-ball to itself has a fixed point."

**Mathematical Formulation**:
- Uses homology to show no retraction Dⁿ → Sⁿ⁻¹ exists
- Contradiction from Hₙ₋₁(Sⁿ⁻¹) ≅ ℤ but Hₙ₋₁(Dⁿ) = 0

**Status**: IN PROGRESS (Brendan Murphy's formalization)

**Difficulty**: very hard

---

### 4.2 Mayer-Vietoris Sequence - NOT FORMALIZED

**NL Statement**: "Given X = U ∪ V (interior union), there is a long exact sequence: ... → Hₙ(U ∩ V) → Hₙ(U) ⊕ Hₙ(V) → Hₙ(X) → Hₙ₋₁(U ∩ V) → ..."

**Status**: NOT FORMALIZED (requires singular homology)

**Difficulty**: very hard

---

### 4.3 CW Complexes - NOT FORMALIZED

**NL Statement**: "A CW complex is built inductively by attaching n-cells via maps ∂Dⁿ → Xⁿ⁻¹ to the (n-1)-skeleton."

**Status**: NOT FORMALIZED (major gap in algebraic topology)

**Difficulty**: very hard

---

### 4.4 Fundamental Group - EXTERNAL LIBRARY

**NL Statement**: "The fundamental group π₁(X, x₀) consists of homotopy classes of loops based at x₀, with group operation given by path concatenation."

**Status**: Available in ComputationalPathsLean (external library)
- π₁(S¹) ≅ ℤ formalized
- π₁(T²) ≅ ℤ × ℤ formalized
- π₁(Klein bottle) ≅ ℤ ⋊ ℤ formalized

**Difficulty**: very hard

---

## 7. STANDARD SETUP

**NL Statement**: "Standard imports and variable declarations for algebraic topology work."

**Lean 4**:
```lean
import Mathlib.Algebra.Homology.HomologicalComplex
import Mathlib.Algebra.Homology.ShortComplex.Basic
import Mathlib.Algebra.Homology.ShortComplex.Exact
import Mathlib.Algebra.Homology.ShortComplex.SnakeLemma
import Mathlib.Algebra.Homology.Homotopy
import Mathlib.Topology.Homotopy.Basic
import Mathlib.Topology.Homotopy.Equiv
import Mathlib.Topology.Homotopy.Path
import Mathlib.AlgebraicTopology.SimplicialSet.Basic
import Mathlib.AlgebraicTopology.SimplexCategory

open CategoryTheory

variable {C : Type*} [Category C] [Abelian C]
variable {ι : Type*} (c : ComplexShape ι)
variable {X Y : Type*} [TopologicalSpace X] [TopologicalSpace Y]
```

**Difficulty**: easy

---

## 8. NOTATION REFERENCE

| Math Notation | Lean 4 Notation | Description |
|---------------|-----------------|-------------|
| Hₙ(C) | `C.homology n` | Homology at index n |
| d² = 0 | `d_comp_d'` | Differential squares to zero |
| f ≃ g | `Homotopic f g` | Maps are homotopic |
| X ≃ₕ Y | `HomotopyEquiv X Y` | Homotopy equivalence |
| Δ[n] | `standardSimplex n` | Standard n-simplex |
| δᵢ | `SimplexCategory.δ` | Face map |
| σᵢ | `SimplexCategory.σ` | Degeneracy map |
| ShortComplex | `ShortComplex C` | Three-term sequence |

---

## 9. KEY MODULES REFERENCE

### Homological Algebra
- `Mathlib.Algebra.Homology.ComplexShape` - Shape theory
- `Mathlib.Algebra.Homology.HomologicalComplex` - Main definitions
- `Mathlib.Algebra.Homology.Homotopy` - Chain homotopy
- `Mathlib.Algebra.Homology.ShortComplex.*` - Exact sequences, snake lemma
- `Mathlib.Algebra.Homology.DerivedCategory.Basic` - Derived categories

### Topology
- `Mathlib.Topology.Homotopy.Basic` - Homotopy definitions
- `Mathlib.Topology.Homotopy.Equiv` - Homotopy equivalence
- `Mathlib.Topology.Homotopy.Path` - Path homotopy

### Algebraic Topology
- `Mathlib.AlgebraicTopology.SimplexCategory` - Simplex category
- `Mathlib.AlgebraicTopology.SimplicialSet.Basic` - Simplicial sets
- `Mathlib.AlgebraicTopology.SimplicialObject` - General simplicial objects

---

## Sources

- [Mathlib.Algebra.Homology.HomologicalComplex](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Homology/HomologicalComplex.html)
- [Mathlib.Topology.Homotopy.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Topology/Homotopy/Basic.html)
- [Mathlib.AlgebraicTopology.SimplicialSet.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/AlgebraicTopology/SimplicialSet/Basic.html)
- [100 theorems in Lean](https://leanprover-community.github.io/100.html)
- [Joël Riou - Derived Categories Formalization](https://hal.science/hal-04546712v4)
- [ComputationalPathsLean](https://arxiv.org/html/2511.19142) - Fundamental group computations
