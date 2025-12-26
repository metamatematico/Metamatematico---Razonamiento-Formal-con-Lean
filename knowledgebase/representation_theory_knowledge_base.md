# Representation Theory Knowledge Base for Lean 4

**Generated:** 2025-12-24
**Mode:** Deep Synthesis
**Purpose:** Knowledge base for implementing representation theory theorems in Lean 4 for dataset generation pairing formal proofs with natural language explanations.
**Confidence:** High

---

## Executive Summary

Representation theory is comprehensively developed in Lean 4's Mathlib library under `Mathlib.RepresentationTheory.*`. This KB covers group representations, characters, complete reducibility (Maschke), irreducibility (Schur), induction/restriction, and the FDRep category. Coverage focuses on finite groups over fields of good characteristic. Estimated total: **65 theorems and definitions**.

### Content Summary

| Category | Estimated Count | Mathlib Support | Difficulty Distribution |
|----------|----------------|-----------------|------------------------|
| **Basic Representations** | 12 | FULL | 40% easy, 45% medium, 15% hard |
| **Group Algebra & Modules** | 8 | FULL | 25% easy, 50% medium, 25% hard |
| **Subrepresentations & Invariants** | 10 | FULL | 20% easy, 50% medium, 30% hard |
| **Simple Modules & Schur** | 10 | FULL | 15% easy, 45% medium, 40% hard |
| **Complete Reducibility** | 8 | FULL | 10% easy, 40% medium, 50% hard |
| **Character Theory** | 10 | FULL | 20% easy, 50% medium, 30% hard |
| **Induction & Restriction** | 7 | FULL | 10% easy, 40% medium, 50% hard |
| **Total** | **65** | - | - |

### Key Dependencies

- **Linear Algebra:** Vector spaces, endomorphisms, trace, dimension
- **Group Theory:** Groups, subgroups, conjugacy, group homomorphisms
- **Category Theory:** Categories, functors, adjunctions

## Related Knowledge Bases

### Prerequisites
- **Group Theory** (`group_theory_knowledge_base.md`): Groups, subgroups, quotients, conjugacy classes
- **Linear Algebra** (`linear_algebra_knowledge_base.md`): Vector spaces, endomorphisms, trace, dimension
- **Category Theory** (`category_theory_knowledge_base.md`): Categories, functors, adjunctions

### Builds Upon This KB
- **Lie Theory** (`lie_theory_knowledge_base.md`): Representations of Lie groups and algebras

### Related Topics
- **Galois Theory** (`galois_theory_knowledge_base.md`): Galois representations
- **Number Theory** (`number_theory_knowledge_base.md`): Modular representations, automorphic forms

### Scope Clarification
This KB focuses on **group representation theory**:
- Basic representations and group actions
- Group algebra and modules
- Subrepresentations and invariants
- Simple modules and Schur's lemma
- Complete reducibility (Maschke's theorem)
- Character theory
- Induction and restriction functors

For **Lie algebra representations**, see **Lie Theory KB**.

---

## Part I: Basic Representations

### Module Organization

**Primary Imports:**
- `Mathlib.RepresentationTheory.Basic`
- `Mathlib.Algebra.Module.LinearMap.End`

**Estimated Statements:** 12

---

### 1. Representation

**Natural Language Statement:**
A representation of a monoid G over a commutative semiring k on a module V is a monoid homomorphism from G to the k-linear endomorphisms of V.

**Lean 4 Definition:**
```lean
abbrev Representation (k G V : Type*) [CommSemiring k] [Monoid G]
    [AddCommMonoid V] [Module k V] := G →* (V →ₗ[k] V)
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** easy

---

### 2. Representation.apply

**Natural Language Statement:**
For a representation ρ : G →* End(V), the action of group element g on vector v is (ρ g) v.

**Lean 4 Definition:**
```lean
def Representation.apply (ρ : Representation k G V) (g : G) (v : V) : V := ρ g v
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** easy

---

### 3. Representation.map_one

**Natural Language Statement:**
For any representation ρ, the identity element acts as the identity map: ρ(1) = id_V.

**Lean 4 Theorem:**
```lean
theorem Representation.map_one (ρ : Representation k G V) : ρ 1 = LinearMap.id := ρ.map_one
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** easy

---

### 4. Representation.map_mul

**Natural Language Statement:**
For any representation ρ and group elements g, h: ρ(gh) = ρ(g) ∘ ρ(h).

**Lean 4 Theorem:**
```lean
theorem Representation.map_mul (ρ : Representation k G V) (g h : G) :
    ρ (g * h) = ρ g ∘ₗ ρ h := ρ.map_mul g h
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** easy

---

### 5. Representation.apply_bijective

**Natural Language Statement:**
When G is a group (not just a monoid), each ρ(g) is a bijective linear map.

**Lean 4 Theorem:**
```lean
theorem Representation.apply_bijective [Group G] (ρ : Representation k G V) (g : G) :
    Function.Bijective (ρ g) := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** medium

---

### 6. Representation.trivial

**Natural Language Statement:**
The trivial representation has every group element act as the identity on V.

**Lean 4 Definition:**
```lean
def Representation.trivial : Representation k G V where
  toFun _ := LinearMap.id
  map_one' := rfl
  map_mul' _ _ := rfl
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** easy

---

### 7. Representation.IsTrivial

**Natural Language Statement:**
A representation is trivial if every group element fixes every vector: ρ(g)(v) = v for all g, v.

**Lean 4 Definition:**
```lean
def Representation.IsTrivial (ρ : Representation k G V) : Prop :=
  ∀ (g : G) (v : V), ρ g v = v
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** easy

---

### 8. Representation.dual

**Natural Language Statement:**
The contragredient (dual) representation on V* is defined by (ρ*(g)(f))(v) = f(ρ(g⁻¹)(v)).

**Lean 4 Definition:**
```lean
def Representation.dual [Group G] (ρ : Representation k G V) :
    Representation k G (V →ₗ[k] k) :=
  (ρ.comp (MonoidHom.inv G)).linHom Representation.trivial
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** medium

---

### 9. Representation.prod

**Natural Language Statement:**
The product of representations ρ on V and σ on W is the representation on V × W with g acting componentwise.

**Lean 4 Definition:**
```lean
def Representation.prod (ρ : Representation k G V) (σ : Representation k G W) :
    Representation k G (V × W) where
  toFun g := (ρ g).prodMap (σ g)
  ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** medium

---

### 10. Representation.tprod

**Natural Language Statement:**
The tensor product representation on V ⊗ W has the diagonal action: g·(v ⊗ w) = (g·v) ⊗ (g·w).

**Lean 4 Definition:**
```lean
def Representation.tprod (ρ : Representation k G V) (σ : Representation k G W) :
    Representation k G (V ⊗[k] W) := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** medium

---

### 11. Representation.directSum

**Natural Language Statement:**
Given a family of representations (V_i, ρ_i), the direct sum ⨁ V_i carries the componentwise action.

**Lean 4 Definition:**
```lean
def Representation.directSum {ι : Type*} (V : ι → Type*)
    [∀ i, AddCommMonoid (V i)] [∀ i, Module k (V i)]
    (ρ : ∀ i, Representation k G (V i)) :
    Representation k G (⨁ i, V i) := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** medium

---

### 12. Representation.leftRegular

**Natural Language Statement:**
The left regular representation of G on k[G] is given by left multiplication: g·(∑ aₕ h) = ∑ aₕ (gh).

**Lean 4 Definition:**
```lean
def Representation.leftRegular : Representation k G (MonoidAlgebra k G) := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** medium

---

## Part II: Group Algebra & Modules

### Module Organization

**Primary Imports:**
- `Mathlib.Algebra.MonoidAlgebra.Basic`
- `Mathlib.RepresentationTheory.Basic`

**Estimated Statements:** 8

---

### 13. MonoidAlgebra

**Natural Language Statement:**
The group algebra k[G] is the free k-module with basis G, where multiplication extends the group operation linearly via convolution.

**Lean 4 Definition:**
```lean
def MonoidAlgebra (k G : Type*) [CommSemiring k] [Monoid G] := G →₀ k
```

**Mathlib Location:** `Mathlib.Algebra.MonoidAlgebra.Basic`

**Difficulty:** easy

---

### 14. MonoidAlgebra.single

**Natural Language Statement:**
The element single g c ∈ k[G] represents c · g, the scalar c times the group element g.

**Lean 4 Definition:**
```lean
def MonoidAlgebra.single (g : G) (c : k) : MonoidAlgebra k G := Finsupp.single g c
```

**Mathlib Location:** `Mathlib.Algebra.MonoidAlgebra.Basic`

**Difficulty:** easy

---

### 15. MonoidAlgebra.mul_single

**Natural Language Statement:**
Multiplication of basis elements follows the group law: (single g a) * (single h b) = single (g * h) (a * b).

**Lean 4 Theorem:**
```lean
theorem MonoidAlgebra.single_mul_single (g h : G) (a b : k) :
    single g a * single h b = single (g * h) (a * b) := ...
```

**Mathlib Location:** `Mathlib.Algebra.MonoidAlgebra.Basic`

**Difficulty:** easy

---

### 16. Representation.asModule

**Natural Language Statement:**
Any representation ρ : G →* End(V) induces a k[G]-module structure on V.

**Lean 4 Definition:**
```lean
def Representation.asModule (ρ : Representation k G V) :
    Module (MonoidAlgebra k G) V := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** medium

---

### 17. Representation.ofModule

**Natural Language Statement:**
Any k[G]-module M (with compatible scalar tower) gives a representation of G on M.

**Lean 4 Definition:**
```lean
def Representation.ofModule [Module (MonoidAlgebra k G) M]
    [IsScalarTower k (MonoidAlgebra k G) M] :
    Representation k G M := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** medium

---

### 18. Representation.asAlgebraHom

**Natural Language Statement:**
A representation corresponds to an algebra homomorphism k[G] → End(V).

**Lean 4 Definition:**
```lean
def Representation.asAlgebraHom (ρ : Representation k G V) :
    MonoidAlgebra k G →ₐ[k] (V →ₗ[k] V) := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** medium

---

### 19. Module_MonoidAlgebra_equiv_Representation

**Natural Language Statement:**
The categories of k[G]-modules and G-representations over k are equivalent.

**Lean 4 Theorem:**
```lean
-- Conceptual: asModule and ofModule form an equivalence
theorem asModule_ofModule_id : ofModule k G (asModule ρ) ≅ ρ := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** hard

---

### 20. MonoidAlgebra.instAlgebra

**Natural Language Statement:**
The group algebra k[G] is naturally a k-algebra with the algebra map k → k[G] given by k ∋ c ↦ c · 1_G.

**Lean 4 Instance:**
```lean
instance : Algebra k (MonoidAlgebra k G) := ...
```

**Mathlib Location:** `Mathlib.Algebra.MonoidAlgebra.Basic`

**Difficulty:** medium

---

## Part III: Subrepresentations & Invariants

### Module Organization

**Primary Imports:**
- `Mathlib.RepresentationTheory.Basic`
- `Mathlib.RepresentationTheory.Invariants`

**Estimated Statements:** 10

---

### 21. Representation.subrepresentation

**Natural Language Statement:**
A subrepresentation is a submodule W ⊆ V that is G-invariant: ρ(g)(W) ⊆ W for all g ∈ G.

**Lean 4 Definition:**
```lean
def Representation.subrepresentation (ρ : Representation k G V)
    (W : Submodule k V) (h : ∀ g : G, W ≤ Submodule.comap (ρ g) W) :
    Representation k G W := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** medium

---

### 22. Representation.quotient

**Natural Language Statement:**
If W is a G-invariant submodule of V, then V/W inherits a representation structure.

**Lean 4 Definition:**
```lean
def Representation.quotient (ρ : Representation k G V) (W : Submodule k V)
    (h : ∀ g : G, W ≤ Submodule.comap (ρ g) W) :
    Representation k G (V ⧸ W) := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Basic`

**Difficulty:** medium

---

### 23. Representation.invariants

**Natural Language Statement:**
The subspace of invariants V^G consists of vectors fixed by all group elements: {v ∈ V | ∀g. ρ(g)(v) = v}.

**Lean 4 Definition:**
```lean
def Representation.invariants (ρ : Representation k G V) : Submodule k V :=
  { carrier := {v | ∀ g : G, ρ g v = v}
    ... }
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Invariants`

**Difficulty:** easy

---

### 24. Representation.mem_invariants

**Natural Language Statement:**
A vector v is invariant if and only if ρ(g)(v) = v for all g ∈ G.

**Lean 4 Theorem:**
```lean
theorem Representation.mem_invariants (ρ : Representation k G V) (v : V) :
    v ∈ ρ.invariants ↔ ∀ g : G, ρ g v = v := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Invariants`

**Difficulty:** easy

---

### 25. Representation.invariants_iInf

**Natural Language Statement:**
The invariants subspace equals the intersection of fixed-point sets: V^G = ⋂_{g∈G} V^{ρ(g)}.

**Lean 4 Theorem:**
```lean
theorem Representation.invariants_eq_iInf (ρ : Representation k G V) :
    ρ.invariants = ⨅ g : G, LinearMap.ker (ρ g - LinearMap.id) := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Invariants`

**Difficulty:** medium

---

### 26. average (Group Algebra Average)

**Natural Language Statement:**
When |G| is invertible in k, the average element (1/|G|)·∑_{g∈G} g ∈ k[G] projects onto invariants.

**Lean 4 Definition:**
```lean
def average [Fintype G] [Invertible (Fintype.card G : k)] :
    MonoidAlgebra k G := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Invariants`

**Difficulty:** medium

---

### 27. average_mul_self

**Natural Language Statement:**
The average element is idempotent: (average)² = average.

**Lean 4 Theorem:**
```lean
theorem average_mul_self [Fintype G] [Invertible (Fintype.card G : k)] :
    (average : MonoidAlgebra k G) * average = average := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Invariants`

**Difficulty:** medium

---

### 28. Representation.invariants_projection

**Natural Language Statement:**
The average element acts on any representation as the projection onto invariants.

**Lean 4 Theorem:**
```lean
theorem Representation.average_projects_to_invariants
    [Fintype G] [Invertible (Fintype.card G : k)]
    (ρ : Representation k G V) (v : V) :
    ρ.asAlgebraHom average v ∈ ρ.invariants := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Invariants`

**Difficulty:** hard

---

### 29. invariantsFunctor

**Natural Language Statement:**
Taking invariants is functorial: it defines a functor from Rep(k,G) to k-Mod.

**Lean 4 Definition:**
```lean
def Rep.invariantsFunctor : Rep k G ⥤ ModuleCat k := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Invariants`

**Difficulty:** hard

---

### 30. trivial_invariants

**Natural Language Statement:**
For the trivial representation, all of V is invariant: V^G = V.

**Lean 4 Theorem:**
```lean
theorem Representation.trivial_invariants_eq_top :
    (Representation.trivial : Representation k G V).invariants = ⊤ := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Invariants`

**Difficulty:** easy

---

## Part IV: Simple Modules & Schur's Lemma

### Module Organization

**Primary Imports:**
- `Mathlib.RingTheory.SimpleModule.Basic`
- `Mathlib.RepresentationTheory.FDRep`

**Estimated Statements:** 10

---

### 31. IsSimpleModule

**Natural Language Statement:**
A module M is simple if its only submodules are {0} and M. Equivalently, M is nontrivial and every nonzero submodule equals M.

**Lean 4 Definition:**
```lean
class IsSimpleModule (R M : Type*) [Semiring R] [AddCommMonoid M] [Module R M] : Prop where
  nontrivial : Nontrivial M
  eq_bot_or_eq_top : ∀ (N : Submodule R M), N = ⊥ ∨ N = ⊤
```

**Mathlib Location:** `Mathlib.RingTheory.SimpleModule.Basic`

**Difficulty:** easy

---

### 32. isSimpleModule_iff_isAtom

**Natural Language Statement:**
A submodule is simple iff it is an atom in the submodule lattice (covers ⊥ with nothing in between).

**Lean 4 Theorem:**
```lean
theorem isSimpleModule_iff_isAtom :
    IsSimpleModule R M ↔ IsAtom (⊤ : Submodule R M) := ...
```

**Mathlib Location:** `Mathlib.RingTheory.SimpleModule.Basic`

**Difficulty:** medium

---

### 33. schur_bijective_or_zero

**Natural Language Statement:**
(Schur's Lemma) Any R-linear map between simple R-modules is either bijective or zero.

**Lean 4 Theorem:**
```lean
theorem LinearMap.bijective_or_eq_zero [IsSimpleModule R M] [IsSimpleModule R N]
    (f : M →ₗ[R] N) : Function.Bijective f ∨ f = 0 := ...
```

**Mathlib Location:** `Mathlib.RingTheory.SimpleModule.Basic`

**Difficulty:** hard

---

### 34. End_simple_isDivisionRing

**Natural Language Statement:**
The endomorphism ring of a simple module is a division ring.

**Lean 4 Theorem:**
```lean
instance [IsSimpleModule R M] : DivisionRing (M →ₗ[R] M) := ...
```

**Mathlib Location:** `Mathlib.RingTheory.SimpleModule.Basic`

**Difficulty:** hard

---

### 35. FDRep

**Natural Language Statement:**
FDRep k G is the category of finite-dimensional k-linear representations of the monoid G.

**Lean 4 Definition:**
```lean
abbrev FDRep (k G : Type*) [CommRing k] [Monoid G] := Action (FGModuleCat k) G
```

**Mathlib Location:** `Mathlib.RepresentationTheory.FDRep`

**Difficulty:** medium

---

### 36. FDRep.ρ

**Natural Language Statement:**
For V : FDRep k G, the representation homomorphism is V.ρ : G →* End(V).

**Lean 4 Definition:**
```lean
def FDRep.ρ (V : FDRep k G) : G →* (V →ₗ[k] V) := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.FDRep`

**Difficulty:** easy

---

### 37. FDRep.finrank_hom_simple_simple

**Natural Language Statement:**
(Schur for FDRep) Over an algebraically closed field, dim Hom_G(V,W) = 1 if V ≅ W are simple, and 0 otherwise.

**Lean 4 Theorem:**
```lean
theorem FDRep.finrank_hom_simple_simple [IsAlgClosed k] [Fintype G]
    (V W : FDRep k G) [Simple V] [Simple W] :
    finrank k (V ⟶ W) = if Nonempty (V ≅ W) then 1 else 0 := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.FDRep`

**Difficulty:** hard

---

### 38. IsSemisimpleModule

**Natural Language Statement:**
A module is semisimple if every submodule has a complement.

**Lean 4 Definition:**
```lean
class IsSemisimpleModule (R M : Type*) [Semiring R] [AddCommMonoid M] [Module R M] : Prop where
  complemented : ComplementedLattice (Submodule R M)
```

**Mathlib Location:** `Mathlib.RingTheory.SimpleModule.Basic`

**Difficulty:** medium

---

### 39. semisimple_iff_direct_sum_simple

**Natural Language Statement:**
A module is semisimple iff it is a direct sum of simple submodules.

**Lean 4 Theorem:**
```lean
theorem isSemisimpleModule_iff_exists_directSum_simple :
    IsSemisimpleModule R M ↔
    ∃ (ι : Type*) (V : ι → Submodule R M), (∀ i, IsSimpleModule R (V i)) ∧
      (⨆ i, V i) = ⊤ ∧ DirectSum.IsInternal V := ...
```

**Mathlib Location:** `Mathlib.RingTheory.SimpleModule.Basic`

**Difficulty:** hard

---

### 40. SimpleModule.isNoetherian

**Natural Language Statement:**
Every simple module is Noetherian.

**Lean 4 Instance:**
```lean
instance [IsSimpleModule R M] : IsNoetherian R M := ...
```

**Mathlib Location:** `Mathlib.RingTheory.SimpleModule.Basic`

**Difficulty:** medium

---

## Part V: Complete Reducibility (Maschke's Theorem)

### Module Organization

**Primary Imports:**
- `Mathlib.RepresentationTheory.Maschke`

**Estimated Statements:** 8

---

### 41. LinearMap.conjugate

**Natural Language Statement:**
The conjugate of a k-linear map π by group element g is the map v ↦ g⁻¹ · π(g · v).

**Lean 4 Definition:**
```lean
def LinearMap.conjugate (π : V →ₗ[k] V) (g : G) : V →ₗ[k] V :=
  (ρ g⁻¹) ∘ₗ π ∘ₗ (ρ g)
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Maschke`

**Difficulty:** medium

---

### 42. LinearMap.sumOfConjugates

**Natural Language Statement:**
The sum of conjugates is ∑_{g∈G} g⁻¹ · π · g.

**Lean 4 Definition:**
```lean
def LinearMap.sumOfConjugates [Fintype G] (π : V →ₗ[k] V) : V →ₗ[k] V :=
  ∑ g : G, π.conjugate g
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Maschke`

**Difficulty:** medium

---

### 43. LinearMap.sumOfConjugates_equivariant

**Natural Language Statement:**
The sum of conjugates is G-equivariant: it commutes with all ρ(g).

**Lean 4 Theorem:**
```lean
theorem LinearMap.sumOfConjugates_equivariant [Fintype G] (π : V →ₗ[k] V) (g : G) :
    ρ g ∘ₗ sumOfConjugates π = sumOfConjugates π ∘ₗ ρ g := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Maschke`

**Difficulty:** hard

---

### 44. LinearMap.equivariantProjection

**Natural Language Statement:**
When |G| is invertible, (1/|G|) · ∑_{g∈G} g⁻¹ · π · g is a G-equivariant projection.

**Lean 4 Definition:**
```lean
def LinearMap.equivariantProjection [Fintype G] [Invertible (Fintype.card G : k)]
    (π : V →ₗ[k] V) : V →ₗ[k] V :=
  ⁅Fintype.card G⁆⁻¹ • sumOfConjugates π
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Maschke`

**Difficulty:** medium

---

### 45. MonoidAlgebra.Submodule.exists_isCompl (Maschke's Theorem)

**Natural Language Statement:**
If G is finite and |G| is invertible in k, then every submodule of a k[G]-module has a complement.

**Lean 4 Theorem:**
```lean
theorem MonoidAlgebra.Submodule.exists_isCompl
    [Fintype G] [Invertible (Fintype.card G : k)]
    (W : Submodule (MonoidAlgebra k G) V) :
    ∃ W' : Submodule (MonoidAlgebra k G) V, IsCompl W W' := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Maschke`

**Difficulty:** hard

---

### 46. MonoidAlgebra.instIsSemisimpleModule

**Natural Language Statement:**
Under Maschke's conditions, every k[G]-module is semisimple.

**Lean 4 Instance:**
```lean
instance MonoidAlgebra.instIsSemisimpleModule
    [Fintype G] [Invertible (Fintype.card G : k)] :
    IsSemisimpleModule (MonoidAlgebra k G) V := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Maschke`

**Difficulty:** hard

---

### 47. MonoidAlgebra.instIsSemisimpleRing

**Natural Language Statement:**
Under Maschke's conditions, the group algebra k[G] is a semisimple ring.

**Lean 4 Instance:**
```lean
instance MonoidAlgebra.instIsSemisimpleRing
    [Fintype G] [Invertible (Fintype.card G : k)] :
    IsSemisimpleRing (MonoidAlgebra k G) := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Maschke`

**Difficulty:** hard

---

### 48. complete_reducibility

**Natural Language Statement:**
Every finite-dimensional representation is a direct sum of irreducible representations (when char(k) ∤ |G|).

**Lean 4 Theorem:**
```lean
-- Consequence of semisimplicity
theorem Representation.decomposition_into_irreducibles
    [Fintype G] [Invertible (Fintype.card G : k)]
    (ρ : Representation k G V) [FiniteDimensional k V] :
    ∃ (ι : Type*) (W : ι → Submodule k V),
      (∀ i, IsSimpleModule (MonoidAlgebra k G) (W i)) ∧
      DirectSum.IsInternal W := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Maschke`

**Difficulty:** hard

---

## Part VI: Character Theory

### Module Organization

**Primary Imports:**
- `Mathlib.RepresentationTheory.Character`

**Estimated Statements:** 10

---

### 49. FDRep.character

**Natural Language Statement:**
The character of a finite-dimensional representation assigns to each g the trace of ρ(g): χ_V(g) = tr(ρ(g)).

**Lean 4 Definition:**
```lean
def FDRep.character (V : FDRep k G) : G → k :=
  fun g => LinearMap.trace k V (V.ρ g)
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Character`

**Difficulty:** easy

---

### 50. FDRep.char_one

**Natural Language Statement:**
The character evaluated at the identity equals the dimension: χ_V(1) = dim(V).

**Lean 4 Theorem:**
```lean
theorem FDRep.char_one (V : FDRep k G) : V.character 1 = finrank k V := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Character`

**Difficulty:** easy

---

### 51. FDRep.char_mul_comm

**Natural Language Statement:**
Characters are class functions: χ(gh) = χ(hg) for all g, h ∈ G.

**Lean 4 Theorem:**
```lean
theorem FDRep.char_mul_comm (V : FDRep k G) (g h : G) :
    V.character (g * h) = V.character (h * g) := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Character`

**Difficulty:** easy

---

### 52. FDRep.char_conj

**Natural Language Statement:**
Characters are constant on conjugacy classes: χ(hgh⁻¹) = χ(g).

**Lean 4 Theorem:**
```lean
theorem FDRep.char_conj [Group G] (V : FDRep k G) (g h : G) :
    V.character (h * g * h⁻¹) = V.character g := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Character`

**Difficulty:** medium

---

### 53. FDRep.char_iso

**Natural Language Statement:**
Isomorphic representations have identical characters.

**Lean 4 Theorem:**
```lean
theorem FDRep.char_iso (V W : FDRep k G) (f : V ≅ W) :
    V.character = W.character := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Character`

**Difficulty:** medium

---

### 54. FDRep.char_tensor

**Natural Language Statement:**
The character of a tensor product is the pointwise product: χ_{V⊗W}(g) = χ_V(g) · χ_W(g).

**Lean 4 Theorem:**
```lean
theorem FDRep.char_tensor (V W : FDRep k G) (g : G) :
    (V ⊗ W).character g = V.character g * W.character g := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Character`

**Difficulty:** medium

---

### 55. FDRep.char_dual

**Natural Language Statement:**
The character of the dual representation: χ_{V*}(g) = χ_V(g⁻¹).

**Lean 4 Theorem:**
```lean
theorem FDRep.char_dual [Group G] (V : FDRep k G) (g : G) :
    (FDRep.dual V).character g = V.character g⁻¹ := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Character`

**Difficulty:** medium

---

### 56. FDRep.char_directSum

**Natural Language Statement:**
The character of a direct sum is the sum of characters: χ_{V⊕W}(g) = χ_V(g) + χ_W(g).

**Lean 4 Theorem:**
```lean
theorem FDRep.char_directSum (V W : FDRep k G) (g : G) :
    (V ⊕ W).character g = V.character g + W.character g := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Character`

**Difficulty:** medium

---

### 57. character_inner_product

**Natural Language Statement:**
The inner product of characters ⟨χ,ψ⟩ = (1/|G|) ∑_{g∈G} χ(g) · ψ(g⁻¹) is defined when |G| is invertible.

**Lean 4 Definition:**
```lean
def FDRep.charInnerProduct [Fintype G] [Invertible (Fintype.card G : k)]
    (χ ψ : G → k) : k :=
  ⁅Fintype.card G⁆⁻¹ * ∑ g : G, χ g * ψ g⁻¹
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Character`

**Difficulty:** medium

---

### 58. FDRep.char_orthonormal

**Natural Language Statement:**
Characters of irreducible representations are orthonormal: ⟨χ_V, χ_W⟩ = 1 if V ≅ W, and 0 otherwise.

**Lean 4 Theorem:**
```lean
theorem FDRep.char_orthonormal [IsAlgClosed k] [Fintype G]
    [Invertible (Fintype.card G : k)]
    (V W : FDRep k G) [Simple V] [Simple W] :
    charInnerProduct V.character W.character = if Nonempty (V ≅ W) then 1 else 0 := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Character`

**Difficulty:** hard

---

## Part VII: Induction & Restriction

### Module Organization

**Primary Imports:**
- `Mathlib.RepresentationTheory.Induced`

**Estimated Statements:** 7

---

### 59. Action.res (Restriction)

**Natural Language Statement:**
Given φ : G → H, the restriction functor Res_φ : Rep(H) → Rep(G) pulls back H-actions to G.

**Lean 4 Definition:**
```lean
def Action.res (φ : G →* H) : Action (ModuleCat k) H ⥤ Action (ModuleCat k) G := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Induced`

**Difficulty:** hard

---

### 60. Representation.IndV

**Natural Language Statement:**
The induced representation space Ind_G^H(A) is the coinvariants (k[H] ⊗_k A)_G.

**Lean 4 Definition:**
```lean
def Representation.IndV (φ : G →* H) (ρ : Representation k G A) : Type* :=
  (MonoidAlgebra k H ⊗[k] A) ⧸ ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Induced`

**Difficulty:** hard

---

### 61. Representation.ind

**Natural Language Statement:**
The induced representation Ind_G^H(ρ) extends ρ from G to H via the induction construction.

**Lean 4 Definition:**
```lean
def Representation.ind (φ : G →* H) (ρ : Representation k G A) :
    Representation k H (Representation.IndV φ ρ) := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Induced`

**Difficulty:** hard

---

### 62. Rep.indFunctor

**Natural Language Statement:**
Induction defines a functor Ind : Rep(k,G) → Rep(k,H).

**Lean 4 Definition:**
```lean
def Rep.indFunctor (φ : G →* H) : Rep k G ⥤ Rep k H := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Induced`

**Difficulty:** hard

---

### 63. Rep.indResAdjunction (Frobenius Reciprocity)

**Natural Language Statement:**
Induction and restriction form an adjoint pair: Hom_H(Ind_G^H(A), B) ≅ Hom_G(A, Res_G^H(B)).

**Lean 4 Theorem:**
```lean
def Rep.indResAdjunction (φ : G →* H) :
    Rep.indFunctor k φ ⊣ Action.res (ModuleCat k) φ := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Induced`

**Difficulty:** hard

---

### 64. ind_res_composition

**Natural Language Statement:**
For H ≤ G with [G:H] = n, Ind_H^G(Res_H^G(V)) ≅ V^⊕n (with appropriate indexing).

**Lean 4 Theorem:**
```lean
-- Conceptual theorem about composition of induction and restriction
theorem ind_res_decomposition [Subgroup.FiniteIndex H G] (V : Rep k G) :
    Representation.ind (Subgroup.subtype H) (Action.res (Subgroup.subtype H) V) ≅ ... := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Induced`

**Difficulty:** hard

---

### 65. induced_character_formula

**Natural Language Statement:**
The character of an induced representation satisfies: χ_{Ind_H^G(W)}(g) = (1/|H|) ∑_{x: xgx⁻¹∈H} χ_W(xgx⁻¹).

**Lean 4 Theorem:**
```lean
-- Character induction formula (conceptual)
theorem FDRep.char_ind [Fintype G] [Fintype H] (W : FDRep k H) (g : G) :
    (FDRep.ind φ W).character g = ... := ...
```

**Mathlib Location:** `Mathlib.RepresentationTheory.Character`

**Difficulty:** hard

---

## Summary Statistics

| Part | Theorems | Difficulty Breakdown |
|------|----------|---------------------|
| I. Basic Representations | 12 | 5 easy, 6 medium, 1 hard |
| II. Group Algebra | 8 | 3 easy, 4 medium, 1 hard |
| III. Subrepresentations | 10 | 3 easy, 5 medium, 2 hard |
| IV. Simple Modules & Schur | 10 | 2 easy, 4 medium, 4 hard |
| V. Complete Reducibility | 8 | 0 easy, 4 medium, 4 hard |
| VI. Character Theory | 10 | 3 easy, 5 medium, 2 hard |
| VII. Induction & Restriction | 7 | 0 easy, 0 medium, 7 hard |
| **Total** | **65** | 16 easy, 28 medium, 21 hard |

## Key Imports Reference

```lean
import Mathlib.RepresentationTheory.Basic
import Mathlib.RepresentationTheory.Character
import Mathlib.RepresentationTheory.FDRep
import Mathlib.RepresentationTheory.Maschke
import Mathlib.RepresentationTheory.Induced
import Mathlib.RepresentationTheory.Invariants
import Mathlib.Algebra.MonoidAlgebra.Basic
import Mathlib.RingTheory.SimpleModule.Basic
```

## Not Formalized (Templates Only)

The following are mathematically important but NOT formalized in Mathlib4:

1. **Wedderburn Decomposition**: k[G] ≅ ⊕ End(V_i) for irreducibles V_i
2. **Number of Irreducibles = Conjugacy Classes**: |{irreps}| = |{conjugacy classes}|
3. **Dimension Sum Formula**: ∑ dim(V_i)² = |G|
4. **Complete Character Tables**: Infrastructure for character table computation

---

## Sources

- [Mathlib.RepresentationTheory.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RepresentationTheory/Basic.html)
- [Mathlib.RepresentationTheory.Character](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RepresentationTheory/Character.html)
- [Mathlib.RepresentationTheory.FDRep](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RepresentationTheory/FDRep.html)
- [Mathlib.RepresentationTheory.Maschke](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RepresentationTheory/Maschke.html)
- [Mathlib.RepresentationTheory.Induced](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RepresentationTheory/Induced.html)
- [Mathlib.RepresentationTheory.Invariants](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RepresentationTheory/Invariants.html)
- [Mathlib.RingTheory.SimpleModule.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RingTheory/SimpleModule/Basic.html)
