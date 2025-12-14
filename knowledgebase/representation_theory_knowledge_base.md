# Representation Theory Knowledge Base

**Domain**: Representation Theory of Finite Groups
**Lean 4 Coverage**: GOOD (core definitions, Maschke, Schur, characters complete)
**Source**: Mathlib4 `RepresentationTheory.*` modules
**Last Updated**: 2025-12-14

---

## Overview

This knowledge base covers representation theory formalization in Lean 4/Mathlib, including group representations, characters, Maschke's theorem, Schur's lemma, and character orthogonality. Coverage focuses on finite groups over fields of good characteristic.

**Key Gap**: Wedderburn decomposition not formalized. Number of irreducibles = conjugacy classes not proven. Character tables infrastructure incomplete.

---

## 1. BASIC DEFINITIONS

### 1.1 Group Representation

**Concept**: Linear action of a group on a vector space.

**NL Statement**: "A representation of a monoid G over a commutative semiring k on a module V is a monoid homomorphism from G to the k-linear endomorphisms of V."

**Lean 4 Definition**:
```lean
abbrev Representation (k G V : Type*) [CommSemiring k] [Monoid G]
    [AddCommMonoid V] [Module k V] := G →* (V →ₗ[k] V)
```

**Key Properties**:
- Works for arbitrary monoids, not just groups
- `Representation.asGroupHom`: Group homomorphism perspective when G is a group
- `Representation.apply_bijective`: Elements act bijectively

**Imports**: `Mathlib.RepresentationTheory.Basic`

**Difficulty**: easy

---

### 1.2 G-Module Structure

**Concept**: Equivalence between representations and group algebra modules.

**NL Statement**: "A G-module is a k-module M with compatible G-action, equivalent to M being a module over the group algebra k[G]."

**Lean 4 Definition**:
```lean
-- Representation → k[G]-module
def Representation.asModule (ρ : Representation k G V) :
    Module (MonoidAlgebra k G) V := ...

-- k[G]-module → Representation
def Representation.ofModule (M : Type*) [AddCommMonoid M] [Module k M]
    [Module (MonoidAlgebra k G) M] [IsScalarTower k (MonoidAlgebra k G) M] :
    Representation k G M := ...
```

**Imports**: `Mathlib.RepresentationTheory.Basic`

**Difficulty**: medium

---

### 1.3 Subrepresentation

**Concept**: G-invariant submodule.

**NL Statement**: "A subrepresentation of (V, ρ) is a submodule W ⊆ V such that ρ(g)(W) ⊆ W for all g ∈ G."

**Lean 4 Definition**:
```lean
def Representation.subrepresentation {k G V : Type*} [CommSemiring k] [Monoid G]
    [AddCommMonoid V] [Module k V] (ρ : Representation k G V)
    (W : Submodule k V) (h : ∀ g : G, W ≤ Submodule.comap (ρ g) W) :
    Representation k G W := ...
```

**Related**:
- `Representation.quotient`: Quotient representation V ⧸ W
- `Representation.ofQuotient`: Factorization through quotient

**Imports**: `Mathlib.RepresentationTheory.Basic`

**Difficulty**: medium

---

### 1.4 Irreducible Representation (Simple Module)

**Concept**: Representation with no proper nontrivial subrepresentations.

**NL Statement**: "A representation is irreducible if its only G-invariant subspaces are {0} and V, equivalently if V is a simple k[G]-module."

**Lean 4 Definition**:
```lean
class IsSimpleModule (R M : Type*) [Semiring R] [AddCommMonoid M]
    [Module R M] : Prop where
  nontrivial : Nontrivial M
  eq_bot_or_eq_top : ∀ (N : Submodule R M), N = ⊥ ∨ N = ⊤

-- Lattice characterization
theorem isSimpleModule_iff_isAtom : IsSimpleModule R M ↔ IsAtom (⊤ : Submodule R M)
```

**Imports**: `Mathlib.RingTheory.SimpleModule.Basic`

**Difficulty**: medium

---

### 1.5 Character

**Concept**: Trace function of a representation.

**NL Statement**: "The character of a finite-dimensional representation assigns to each group element the trace of its action: χ_V(g) = tr(ρ_V(g))."

**Lean 4 Definition**:
```lean
def FDRep.character (V : FDRep k G) : G → k :=
  fun g => LinearMap.trace k V (V.ρ g)
```

**Key Properties**:
- `FDRep.char_one`: χ_V(1) = dim(V)
- `FDRep.char_mul_comm`: χ(gh) = χ(hg) (class function)
- `FDRep.char_conj`: χ(hgh⁻¹) = χ(g)
- `FDRep.char_tensor`: χ_{V⊗W}(g) = χ_V(g) · χ_W(g)
- `FDRep.char_dual`: χ_{V*}(g) = χ_V(g⁻¹)
- `FDRep.char_iso`: Isomorphic representations have equal characters

**Imports**: `Mathlib.RepresentationTheory.Character`

**Difficulty**: easy

---

## 2. KEY CONSTRUCTIONS

### 2.1 Group Algebra

**Concept**: Free k-module with basis G and multiplication from group operation.

**NL Statement**: "The group algebra k[G] is the k-vector space with basis G, where multiplication extends the group operation linearly."

**Lean 4 Definition**:
```lean
-- MonoidAlgebra is the general construction
def MonoidAlgebra (k G : Type*) [CommSemiring k] [Monoid G] :=
  G →₀ k  -- finitely supported functions G → k

-- Multiplication by convolution
instance : Mul (MonoidAlgebra k G) where
  mul f g := Finsupp.sum f fun a₁ b₁ =>
             Finsupp.sum g fun a₂ b₂ =>
             Finsupp.single (a₁ * a₂) (b₁ * b₂)
```

**Imports**: `Mathlib.Algebra.MonoidAlgebra.Basic`

**Difficulty**: medium

---

### 2.2 Direct Sum of Representations

**Concept**: Componentwise action on direct sum.

**NL Statement**: "Given representations (V_i, ρ_i), the direct sum ⨁ V_i carries the representation where g acts componentwise."

**Lean 4 Definition**:
```lean
def Representation.directSum {k G ι : Type*} [CommSemiring k] [Monoid G]
    (V : ι → Type*) [∀ i, AddCommMonoid (V i)] [∀ i, Module k (V i)]
    (ρ : ∀ i, Representation k G (V i)) :
    Representation k G (⨁ i, V i) := ...
```

**Imports**: `Mathlib.RepresentationTheory.Basic`

**Difficulty**: medium

---

### 2.3 Tensor Product of Representations

**Concept**: Diagonal action on tensor product.

**NL Statement**: "Given representations V and W, their tensor product V ⊗ W carries the diagonal action: g·(v ⊗ w) = (g·v) ⊗ (g·w)."

**Lean 4 Definition**:
```lean
def Representation.tprod (ρV : Representation k G V)
    (ρW : Representation k G W) :
    Representation k G (V ⊗[k] W) := ...
```

**Character Property**: χ_{V⊗W}(g) = χ_V(g) · χ_W(g)

**Imports**: `Mathlib.RepresentationTheory.Basic`

**Difficulty**: medium

---

### 2.4 FDRep Category

**Concept**: Category of finite-dimensional representations.

**NL Statement**: "FDRep k G is the category of finite-dimensional k-linear representations of G, a k-linear abelian monoidal category."

**Lean 4 Definition**:
```lean
abbrev FDRep (k G : Type*) [CommRing k] [Monoid G] :=
  Action (FGModuleCat k) G

-- Instances
instance : CoeSort (FDRep k G) (Type*) := ...
instance (V : FDRep k G) : Module k V := ...
instance (V : FDRep k G) : FiniteDimensional k V := ...

def FDRep.ρ (V : FDRep k G) : G →* (V →ₗ[k] V) := ...
```

**Category Properties**:
- k-linear
- Has all finite limits (when k is a field)
- Monoidal with tensor product
- Right rigid (when G is a group)

**Imports**: `Mathlib.RepresentationTheory.FDRep`

**Difficulty**: medium

---

## 3. FUNDAMENTAL THEOREMS

### 3.1 Maschke's Theorem

**Concept**: Complete reducibility when characteristic doesn't divide group order.

**NL Statement**: "If G is a finite group and k is a field with char(k) ∤ |G|, then every k[G]-submodule has a G-invariant complement. Equivalently, every representation is completely reducible."

**Lean 4 Theorem**:
```lean
theorem MonoidAlgebra.Submodule.exists_isCompl
    [Fintype G] [Invertible (Fintype.card G : k)]
    (W : Submodule (MonoidAlgebra k G) V) :
    ∃ W' : Submodule (MonoidAlgebra k G) V, IsCompl W W' := ...
```

**Proof Technique**: Averaging construction
1. Given k-linear retraction π : W → V
2. Average over G: π' = (1/|G|) · ∑_{g∈G} g⁻¹ · π · g
3. Show π' is G-linear and still a retraction

**Derived Instances**:
- `IsSemisimpleModule (MonoidAlgebra k G) V`
- `IsSemisimpleRing (MonoidAlgebra k G)`

**Imports**: `Mathlib.RepresentationTheory.Maschke`

**Difficulty**: hard

---

### 3.2 Schur's Lemma

**Concept**: Hom spaces between irreducibles.

**NL Statement**: "For irreducible representations V and W over an algebraically closed field: dim Hom_G(V, W) = 0 if V ≄ W, and dim Hom_G(V, W) = 1 if V ≅ W."

**Lean 4 Theorem**:
```lean
theorem FDRep.finrank_hom_simple_simple
    [IsAlgClosed k] [Fintype G]
    (V W : FDRep k G) [Simple V] [Simple W] :
    finrank k (V ⟶ W) = if Nonempty (V ≅ W) then 1 else 0 := ...
```

**Imports**: `Mathlib.RepresentationTheory.FDRep`

**Difficulty**: hard

---

### 3.3 Character Orthogonality

**Concept**: Inner product of irreducible characters.

**NL Statement**: "For irreducible representations V and W over an algebraically closed field of good characteristic: ⟨χ_V, χ_W⟩ = (1/|G|) ∑_{g∈G} χ_V(g) · χ_W(g⁻¹) equals 1 if V ≅ W and 0 otherwise."

**Lean 4 Theorem**:
```lean
theorem FDRep.char_orthonormal
    [IsAlgClosed k] [Fintype G] [Invertible (Fintype.card G : k)]
    (V W : FDRep k G) [Simple V] [Simple W] :
    ⟪V.character, W.character⟫ = if Nonempty (V ≅ W) then 1 else 0 := ...
```

**Corollaries**:
- Characters of irreducibles form orthonormal set
- Can decompose representations using character inner products
- Character determines representation up to isomorphism

**Imports**: `Mathlib.RepresentationTheory.Character`

**Difficulty**: hard

---

## 4. ADVANCED TOPICS

### 4.1 Induced Representations

**Concept**: Extension of representation along group homomorphism.

**NL Statement**: "Given φ: G → H and G-representation A, the induced representation Ind_G^H(A) is the H-representation on the coinvariants (k[H] ⊗_k A)_G."

**Lean 4 Definition**:
```lean
def Representation.IndV (φ : G →* H) (ρ : Representation k G A) :
    Type* := ...  -- (k[H] ⊗[k] A)_G

def Representation.ind (φ : G →* H) (ρ : Representation k G A) :
    Representation k H (IndV φ ρ) := ...

def Rep.indFunctor (φ : G →* H) : Rep k G ⥤ Rep k H := ...
```

**Imports**: `Mathlib.RepresentationTheory.Induced`

**Difficulty**: hard

---

### 4.2 Restriction

**Concept**: Restriction of representation along group homomorphism.

**NL Statement**: "Given φ: G → H, restriction Res_φ: Rep(H) → Rep(G) restricts H-action to G via φ."

**Lean 4 Definition**:
```lean
def Action.res (φ : G →* H) : Action (ModuleCat k) H ⥤ Action (ModuleCat k) G := ...
```

**Imports**: `Mathlib.RepresentationTheory.Induced`

**Difficulty**: hard

---

### 4.3 Frobenius Reciprocity

**Concept**: Adjunction between induction and restriction.

**NL Statement**: "Induction and restriction form an adjoint pair: Hom_H(Ind_G^H(A), B) ≅ Hom_G(A, Res_G^H(B))."

**Lean 4 Theorem**:
```lean
def Rep.indResAdjunction (φ : G →* H) :
    Rep.indFunctor k φ ⊣ Action.res (ModuleCat k) φ := ...
```

**Significance**:
- Universal property of induced representations
- Tool for computing Hom spaces
- Foundation for character induction formulas

**Imports**: `Mathlib.RepresentationTheory.Induced`

**Difficulty**: hard

---

## 5. MISSING THEOREMS

### 5.1 Number of Irreducibles = Conjugacy Classes - NOT FORMALIZED

**NL Statement**: "For a finite group G over field k with char(k) ∤ |G|, the number of inequivalent irreducible representations equals the number of conjugacy classes."

**Mathematical Proof Sketch**:
1. dim Z(k[G]) = # conjugacy classes
2. Via Wedderburn: k[G] ≅ ⊕_i End(V_i) implies Z(k[G]) ≅ ⊕_i k
3. Therefore # irreducibles = # conjugacy classes

**Status**: NOT FORMALIZED (requires Wedderburn decomposition)

**Difficulty**: hard

---

### 5.2 Dimension Sum Formula - NOT FORMALIZED

**NL Statement**: "The sum of squares of dimensions of irreducible representations equals the group order: ∑_i dim(V_i)² = |G|."

**Status**: NOT FORMALIZED (requires Wedderburn decomposition)

**Difficulty**: hard

---

### 5.3 Wedderburn Decomposition - NOT FORMALIZED

**NL Statement**: "For finite group G over algebraically closed k with char(k) ∤ |G|: k[G] ≅ ⊕_i End(V_i) where V_i are the irreducible representations."

**Status**: NOT FORMALIZED

**Difficulty**: very hard

---

## 6. STANDARD SETUP

**NL Statement**: "Standard imports and variable declarations for representation theory work."

**Lean 4**:
```lean
import Mathlib.RepresentationTheory.Basic
import Mathlib.RepresentationTheory.Character
import Mathlib.RepresentationTheory.FDRep
import Mathlib.RepresentationTheory.Maschke
import Mathlib.RepresentationTheory.Induced
import Mathlib.Algebra.MonoidAlgebra.Basic
import Mathlib.RingTheory.SimpleModule.Basic

variable {k : Type*} [Field k]
variable {G : Type*} [Group G] [Fintype G]
variable [Invertible (Fintype.card G : k)]
```

**Difficulty**: easy

---

## 7. NOTATION REFERENCE

| Math Notation | Lean 4 Notation | Description |
|---------------|-----------------|-------------|
| ρ : G → GL(V) | `Representation k G V` | Representation |
| k[G] | `MonoidAlgebra k G` | Group algebra |
| χ_V(g) | `V.character g` | Character at g |
| ⟨χ, ψ⟩ | `⟪χ, ψ⟫` | Character inner product |
| V ⊗ W | `Representation.tprod` | Tensor product |
| V ⊕ W | `Representation.directSum` | Direct sum |
| Ind_G^H(V) | `Representation.ind` | Induced representation |
| Res_G^H(V) | `Action.res` | Restriction |
| FDRep k G | `FDRep k G` | Finite-dimensional representations |

---

## 8. KEY MODULES REFERENCE

### Core Definitions
- `Mathlib.RepresentationTheory.Basic` - Representations, subrepresentations
- `Mathlib.RepresentationTheory.Character` - Characters, orthogonality
- `Mathlib.RepresentationTheory.FDRep` - Finite-dimensional category, Schur
- `Mathlib.Algebra.MonoidAlgebra.Basic` - Group algebra k[G]

### Major Theorems
- `Mathlib.RepresentationTheory.Maschke` - Complete reducibility
- `Mathlib.RepresentationTheory.Induced` - Induction, Frobenius reciprocity

### Supporting Infrastructure
- `Mathlib.RingTheory.SimpleModule.Basic` - Simple modules (irreducibles)
- `Mathlib.CategoryTheory.Monoidal.Basic` - Monoidal structure

---

## Sources

- [Mathlib.RepresentationTheory.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RepresentationTheory/Basic.html)
- [Mathlib.RepresentationTheory.Character](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RepresentationTheory/Character.html)
- [Mathlib.RepresentationTheory.FDRep](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RepresentationTheory/FDRep.html)
- [Mathlib.RepresentationTheory.Maschke](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RepresentationTheory/Maschke.html)
- [Mathlib.RepresentationTheory.Induced](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RepresentationTheory/Induced.html)
- [Mathematics in Mathlib](https://leanprover-community.github.io/mathlib-overview.html)
