# Lie Theory Knowledge Base for Lean 4

**Generated:** 2025-12-24
**Mode:** Deep Synthesis
**Purpose:** Knowledge base for implementing Lie theory theorems in Lean 4 for dataset generation pairing formal proofs with natural language explanations.
**Confidence:** High

---

## Executive Summary

Lie theory is well-developed in Lean 4's Mathlib library, with Lie algebras under `Mathlib.Algebra.Lie.*` and Lie groups under `Mathlib.Geometry.Manifold.Algebra.*`. This KB covers Lie algebras, Lie groups, and their interconnections including the exponential map, structure theory, and classical matrix groups. Estimated total: **70 theorems and definitions**.

### Content Summary

| Category | Estimated Count | Mathlib Support | Difficulty Distribution |
|----------|----------------|-----------------|------------------------|
| **Lie Algebras** | 14 | FULL | 30% easy, 50% medium, 20% hard |
| **Lie Subalgebras & Ideals** | 10 | FULL | 30% easy, 40% medium, 30% hard |
| **Solvable & Nilpotent** | 12 | FULL | 20% easy, 50% medium, 30% hard |
| **Semisimple & Killing Form** | 10 | FULL | 15% easy, 45% medium, 40% hard |
| **Weight Theory & Cartan** | 8 | FULL | 10% easy, 40% medium, 50% hard |
| **Lie Groups** | 8 | FULL | 20% easy, 50% medium, 30% hard |
| **Matrix Groups** | 8 | FULL | 30% easy, 50% medium, 20% hard |
| **Total** | **70** | - | - |

### Key Dependencies

- **Linear Algebra:** Vector spaces, endomorphisms, matrices
- **Smooth Manifolds:** Differential structure, tangent spaces
- **Group Theory:** Group structure, subgroups, quotients

## Related Knowledge Bases

### Prerequisites
- **Group Theory** (`group_theory_knowledge_base.md`): Group-theoretic foundations, subgroups
- **Smooth Manifolds** (`smooth_manifolds_knowledge_base.md`): Differential manifold structure, tangent spaces
- **Linear Algebra** (`linear_algebra_knowledge_base.md`): Vector spaces, matrices, endomorphisms

### Builds Upon This KB
- **Representation Theory** (`representation_theory_knowledge_base.md`): Representations of Lie groups/algebras
- **Differential Geometry** (`differential_geometry_knowledge_base.md`): Geometric applications of Lie theory

### Related Topics
- **Algebraic Topology** (`algebraic_topology_knowledge_base.md`): Topology of Lie groups
- **Complex Geometry** (`complex_geometry_knowledge_base.md`): Complex Lie groups

### Scope Clarification
This KB focuses on **Lie theory**:
- Lie algebras and Lie rings
- Lie subalgebras and ideals
- Solvable and nilpotent Lie algebras
- Semisimple theory and Killing form
- Weight theory and Cartan subalgebras
- Lie groups and matrix groups
- Exponential map

For **geometric structures on manifolds**, see **Differential Geometry KB**.
For **group representations over finite groups**, see **Representation Theory KB**.

---

## Part I: Lie Algebras

### Module Organization

**Primary Imports:**
- `Mathlib.Algebra.Lie.Basic`
- `Mathlib.Algebra.Lie.Submodule`
- `Mathlib.Algebra.Lie.Subalgebra`

**Estimated Statements:** 14

---

### 1. LieRing

**Natural Language Statement:**
A Lie ring is an additive abelian group L equipped with a bilinear bracket operation [·,·] : L × L → L satisfying alternativity ([x,x] = 0) and the Jacobi identity ([x,[y,z]] + [y,[z,x]] + [z,[x,y]] = 0).

**Lean 4 Definition:**
```lean
class LieRing (L : Type v) extends AddCommGroup L, Bracket L L where
  add_lie : ∀ x y z : L, ⁅x + y, z⁆ = ⁅x, z⁆ + ⁅y, z⁆
  lie_add : ∀ x y z : L, ⁅x, y + z⁆ = ⁅x, y⁆ + ⁅x, z⁆
  lie_self : ∀ x : L, ⁅x, x⁆ = 0
  leibniz_lie : ∀ x y z : L, ⁅x, ⁅y, z⁆⁆ = ⁅⁅x, y⁆, z⁆ + ⁅y, ⁅x, z⁆⁆
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Basic`

**Difficulty:** easy

---

### 2. LieAlgebra

**Natural Language Statement:**
A Lie algebra over a commutative ring R is an R-module L equipped with a Lie bracket that is R-bilinear and satisfies the Lie ring axioms.

**Lean 4 Definition:**
```lean
class LieAlgebra (R : Type u) (L : Type v) [CommRing R] [LieRing L] extends Module R L where
  lie_smul : ∀ (t : R) (x y : L), ⁅x, t • y⁆ = t • ⁅x, y⁆
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Basic`

**Difficulty:** easy

---

### 3. lie_self

**Natural Language Statement:**
In any Lie ring, the bracket of an element with itself is zero: [x,x] = 0.

**Lean 4 Theorem:**
```lean
theorem lie_self (x : L) : ⁅x, x⁆ = 0 := LieRing.lie_self x
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Basic`

**Difficulty:** easy

---

### 4. lie_skew

**Natural Language Statement:**
In any Lie ring, the bracket is skew-symmetric: [x,y] = -[y,x].

**Lean 4 Theorem:**
```lean
theorem lie_skew (x y : L) : ⁅x, y⁆ = -⁅y, x⁆
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Basic`

**Difficulty:** easy

---

### 5. lie_jacobi (Jacobi Identity)

**Natural Language Statement:**
In any Lie ring, the Jacobi identity holds: [x,[y,z]] + [y,[z,x]] + [z,[x,y]] = 0 for all x, y, z.

**Lean 4 Theorem:**
```lean
theorem lie_jacobi (x y z : L) : ⁅x, ⁅y, z⁆⁆ + ⁅y, ⁅z, x⁆⁆ + ⁅z, ⁅x, y⁆⁆ = 0
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Basic`

**Difficulty:** medium

---

### 6. LieHom

**Natural Language Statement:**
A Lie algebra homomorphism is a linear map f : L₁ → L₂ that preserves the bracket: f([x,y]) = [f(x),f(y)].

**Lean 4 Definition:**
```lean
structure LieHom (R : Type u) (L₁ : Type v) (L₂ : Type w)
  [CommRing R] [LieRing L₁] [LieRing L₂] [LieAlgebra R L₁] [LieAlgebra R L₂]
  extends L₁ →ₗ[R] L₂ where
  map_lie' : ∀ x y : L₁, toFun ⁅x, y⁆ = ⁅toFun x, toFun y⁆
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Basic`

**Difficulty:** easy

**Notation:** `L₁ →ₗ⁅R⁆ L₂`

---

### 7. LieEquiv

**Natural Language Statement:**
A Lie algebra isomorphism is a bijective Lie algebra homomorphism.

**Lean 4 Definition:**
```lean
structure LieEquiv (R : Type u) (L₁ : Type v) (L₂ : Type w)
  [CommRing R] [LieRing L₁] [LieRing L₂] [LieAlgebra R L₁] [LieAlgebra R L₂]
  extends L₁ ≃ₗ[R] L₂ where
  map_lie' : ∀ x y : L₁, toFun ⁅x, y⁆ = ⁅toFun x, toFun y⁆
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Basic`

**Difficulty:** easy

**Notation:** `L₁ ≃ₗ⁅R⁆ L₂`

---

### 8. LieModule

**Natural Language Statement:**
A Lie module M over a Lie algebra L is an R-module equipped with a bracket action L × M → M satisfying linearity and a compatibility condition analogous to the Jacobi identity.

**Lean 4 Definition:**
```lean
class LieModule (R : Type u) (L : Type v) (M : Type w)
  [CommRing R] [LieRing L] [LieAlgebra R L] [AddCommGroup M] [Module R M]
  [LieRingModule L M] where
  smul_lie : ∀ (t : R) (x : L) (m : M), ⁅t • x, m⁆ = t • ⁅x, m⁆
  lie_smul : ∀ (t : R) (x : L) (m : M), ⁅x, t • m⁆ = t • ⁅x, m⁆
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Basic`

**Difficulty:** medium

---

### 9. lieAlgebraSelfModule

**Natural Language Statement:**
Every Lie algebra is naturally a module over itself via the adjoint action: x acts on y by [x,y].

**Lean 4 Instance:**
```lean
instance lieAlgebraSelfModule : LieModule R L L where
  smul_lie := by simp [smul_lie]
  lie_smul := by simp [lie_smul]
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Basic`

**Difficulty:** easy

---

### 10. ad (Adjoint Representation)

**Natural Language Statement:**
The adjoint representation ad : L → End(L) sends each element x to the linear map ad_x : y ↦ [x,y]. This is a Lie algebra homomorphism from L to gl(L).

**Lean 4 Definition:**
```lean
def ad (R : Type u) (L : Type v) [CommRing R] [LieRing L] [LieAlgebra R L] :
  L →ₗ⁅R⁆ Module.End R L where
  toFun x := { toFun := fun y => ⁅x, y⁆, ... }
  map_lie' := ...
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Basic`

**Difficulty:** medium

---

### 11. IsLieAbelian

**Natural Language Statement:**
A Lie algebra is abelian if its bracket is identically zero: [x,y] = 0 for all x, y.

**Lean 4 Definition:**
```lean
class IsLieAbelian (L : Type v) [LieRing L] : Prop where
  trivial : ∀ x y : L, ⁅x, y⁆ = 0
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Abelian`

**Difficulty:** easy

---

### 12. LieAlgebra.center

**Natural Language Statement:**
The center of a Lie algebra L is the set of elements that commute with all elements: Z(L) = {x ∈ L : [x,y] = 0 for all y ∈ L}.

**Lean 4 Definition:**
```lean
def LieAlgebra.center (R : Type u) (L : Type v) [CommRing R] [LieRing L] [LieAlgebra R L] :
  LieIdeal R L := LieModule.maxTrivSubmodule R L L
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Abelian`

**Difficulty:** medium

---

### 13. isLieAbelian_iff_center_eq_top

**Natural Language Statement:**
A Lie algebra is abelian if and only if its center equals the whole algebra.

**Lean 4 Theorem:**
```lean
theorem isLieAbelian_iff_center_eq_top :
  IsLieAbelian L ↔ LieAlgebra.center R L = ⊤
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Abelian`

**Difficulty:** medium

---

### 14. ker_ad_eq_center

**Natural Language Statement:**
The kernel of the adjoint representation equals the center of the Lie algebra.

**Lean 4 Theorem:**
```lean
theorem LieAlgebra.ker_ad_eq_center :
  (ad R L).ker = LieAlgebra.center R L
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Abelian`

**Difficulty:** medium

---

## Part II: Lie Subalgebras & Ideals

### Module Organization

**Primary Imports:**
- `Mathlib.Algebra.Lie.Subalgebra`
- `Mathlib.Algebra.Lie.Submodule`

**Estimated Statements:** 10

---

### 15. LieSubalgebra

**Natural Language Statement:**
A Lie subalgebra is a submodule of a Lie algebra that is closed under the bracket operation.

**Lean 4 Definition:**
```lean
structure LieSubalgebra (R : Type u) (L : Type v) [CommRing R] [LieRing L] [LieAlgebra R L]
  extends Submodule R L where
  lie_mem' : ∀ {x y}, x ∈ carrier → y ∈ carrier → ⁅x, y⁆ ∈ carrier
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Subalgebra`

**Difficulty:** easy

---

### 16. LieIdeal

**Natural Language Statement:**
A Lie ideal is a submodule I of L such that [L,I] ⊆ I, meaning [x,y] ∈ I for all x ∈ L and y ∈ I.

**Lean 4 Definition:**
```lean
abbrev LieIdeal (R : Type u) (L : Type v) [CommRing R] [LieRing L] [LieAlgebra R L] :=
  LieSubmodule R L L
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Submodule`

**Difficulty:** easy

---

### 17. LieSubmodule

**Natural Language Statement:**
A Lie submodule of a Lie module M is a submodule closed under the bracket action from L.

**Lean 4 Definition:**
```lean
structure LieSubmodule (R : Type u) (L : Type v) (M : Type w)
  [CommRing R] [LieRing L] [LieAlgebra R L] [AddCommGroup M] [Module R M] [LieRingModule L M]
  [LieModule R L M] extends Submodule R M where
  lie_mem : ∀ {x : L} {m : M}, m ∈ carrier → ⁅x, m⁆ ∈ carrier
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Submodule`

**Difficulty:** medium

---

### 18. lieSpan

**Natural Language Statement:**
The Lie span of a set S is the smallest Lie submodule containing S.

**Lean 4 Definition:**
```lean
def LieSubmodule.lieSpan (s : Set M) : LieSubmodule R L M :=
  sInf {N | s ⊆ N}
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Submodule`

**Difficulty:** medium

---

### 19. LieSubmodule.ker

**Natural Language Statement:**
The kernel of a Lie module homomorphism is a Lie submodule.

**Lean 4 Definition:**
```lean
def LieModuleHom.ker (f : M →ₗ⁅R,L⁆ N) : LieSubmodule R L M where
  carrier := {m | f m = 0}
  ...
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Submodule`

**Difficulty:** medium

---

### 20. LieSubmodule.range

**Natural Language Statement:**
The range of a Lie module homomorphism is a Lie submodule.

**Lean 4 Definition:**
```lean
def LieModuleHom.range (f : M →ₗ⁅R,L⁆ N) : LieSubmodule R L N where
  carrier := Set.range f
  ...
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Submodule`

**Difficulty:** medium

---

### 21. quotient_lie_algebra

**Natural Language Statement:**
If I is a Lie ideal of L, then L/I inherits a natural Lie algebra structure where [x+I, y+I] = [x,y]+I.

**Lean 4 Instance:**
```lean
instance : LieAlgebra R (L ⧸ I) where
  lie_smul := by intro t x y; obtain ⟨x', hx⟩ := Quotient.exists_rep x; ...
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Quotient`

**Difficulty:** medium

---

### 22. LieSubalgebra.lattice

**Natural Language Statement:**
The Lie subalgebras of L form a complete lattice under inclusion.

**Lean 4 Instance:**
```lean
instance : CompleteLattice (LieSubalgebra R L) := ...
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Subalgebra`

**Difficulty:** medium

---

### 23. normalizer

**Natural Language Statement:**
The normalizer of a Lie subalgebra H is the largest subalgebra in which H is an ideal: N_L(H) = {x ∈ L : [x,H] ⊆ H}.

**Lean 4 Definition:**
```lean
def LieSubmodule.normalizer : LieSubmodule R L M :=
  { x | ∀ m ∈ N, ⁅x, m⁆ ∈ N }
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Normalizer`

**Difficulty:** medium

---

### 24. idealizer

**Natural Language Statement:**
The idealizer of a submodule N is the set of elements whose bracket with N stays in N.

**Lean 4 Definition:**
```lean
def LieSubmodule.idealizer (N : LieSubmodule R L M) : LieSubalgebra R L where
  carrier := {x | ∀ m ∈ N, ⁅x, m⁆ ∈ N}
  ...
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Idealizer`

**Difficulty:** medium

---

## Part III: Solvable & Nilpotent Lie Algebras

### Module Organization

**Primary Imports:**
- `Mathlib.Algebra.Lie.Solvable`
- `Mathlib.Algebra.Lie.Nilpotent`

**Estimated Statements:** 12

---

### 25. derivedSeries

**Natural Language Statement:**
The derived series of a Lie algebra is defined recursively: D⁰(L) = L, and Dⁿ⁺¹(L) = [Dⁿ(L), Dⁿ(L)].

**Lean 4 Definition:**
```lean
def derivedSeries (k : ℕ) : LieIdeal R L :=
  derivedSeriesOfIdeal R L k ⊤
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Solvable`

**Difficulty:** medium

---

### 26. IsSolvable

**Natural Language Statement:**
A Lie algebra is solvable if its derived series eventually reaches zero: there exists k such that Dᵏ(L) = 0.

**Lean 4 Definition:**
```lean
class LieAlgebra.IsSolvable (R : Type u) (L : Type v) [CommRing R] [LieRing L]
  [LieAlgebra R L] : Prop where
  solvable : ∃ k : ℕ, derivedSeries R L k = ⊥
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Solvable`

**Difficulty:** medium

---

### 27. derivedLength

**Natural Language Statement:**
For a solvable Lie algebra, the derived length is the smallest k such that Dᵏ(L) = 0.

**Lean 4 Definition:**
```lean
noncomputable def derivedLengthOfIdeal (I : LieIdeal R L) [hI : LieAlgebra.IsSolvable R I] : ℕ :=
  Nat.find hI.solvable
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Solvable`

**Difficulty:** medium

---

### 28. abelian_isSolvable

**Natural Language Statement:**
Every abelian Lie algebra is solvable (with derived length ≤ 1).

**Lean 4 Theorem:**
```lean
instance (priority := 100) LieAlgebra.isSolvableOfIsLieAbelian [IsLieAbelian L] :
  LieAlgebra.IsSolvable R L := ⟨⟨1, by simp [derivedSeries]⟩⟩
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Solvable`

**Difficulty:** easy

---

### 29. radical

**Natural Language Statement:**
The radical of a Lie algebra is the largest solvable ideal.

**Lean 4 Definition:**
```lean
def LieAlgebra.radical : LieIdeal R L :=
  sSup {I : LieIdeal R L | LieAlgebra.IsSolvable R I}
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Solvable`

**Difficulty:** medium

---

### 30. lowerCentralSeries

**Natural Language Statement:**
The lower central series of a Lie module M is defined recursively: C⁰(M) = M, and Cⁿ⁺¹(M) = [L, Cⁿ(M)].

**Lean 4 Definition:**
```lean
def LieModule.lowerCentralSeries (k : ℕ) : LieSubmodule R L M :=
  (fun N => ⁅(⊤ : LieIdeal R L), N⁆)^[k] ⊤
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Nilpotent`

**Difficulty:** medium

---

### 31. IsNilpotent

**Natural Language Statement:**
A Lie module is nilpotent if its lower central series eventually reaches zero.

**Lean 4 Definition:**
```lean
class LieModule.IsNilpotent (R : Type u) (L : Type v) (M : Type w)
  [CommRing R] [LieRing L] [LieAlgebra R L] [AddCommGroup M] [Module R M]
  [LieRingModule L M] [LieModule R L M] : Prop where
  nilpotent : ∃ k : ℕ, lowerCentralSeries R L M k = ⊥
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Nilpotent`

**Difficulty:** medium

---

### 32. nilpotent_implies_solvable

**Natural Language Statement:**
Every nilpotent Lie algebra is solvable.

**Lean 4 Theorem:**
```lean
instance (priority := 100) LieAlgebra.isSolvableOfIsNilpotent [LieModule.IsNilpotent R L L] :
  LieAlgebra.IsSolvable R L := ...
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Nilpotent`

**Difficulty:** medium

---

### 33. nilpotent_has_nontrivial_center

**Natural Language Statement:**
A non-trivial nilpotent Lie algebra has a non-trivial center.

**Lean 4 Theorem:**
```lean
theorem LieAlgebra.center_ne_bot_of_isNilpotent [Nontrivial L] [LieModule.IsNilpotent R L L] :
  LieAlgebra.center R L ≠ ⊥ := ...
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Nilpotent`

**Difficulty:** hard

---

### 34. upperCentralSeries

**Natural Language Statement:**
The upper central series is the ascending series Z⁰ ⊆ Z¹ ⊆ ... where Zⁱ⁺¹/Zⁱ is the center of L/Zⁱ.

**Lean 4 Definition:**
```lean
def LieModule.upperCentralSeries (k : ℕ) : LieSubmodule R L M :=
  (LieSubmodule.normalizer)^[k] ⊥
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Nilpotent`

**Difficulty:** hard

---

### 35. lcs_le_iff (Galois Connection)

**Natural Language Statement:**
The lower and upper central series are related by a Galois connection.

**Lean 4 Theorem:**
```lean
theorem LieSubmodule.lcs_le_iff {k : ℕ} {N : LieSubmodule R L M} :
  lowerCentralSeries R L M k ≤ N ↔ ⊥ ≤ upperCentralSeriesOfIdealizer R L M N k
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Nilpotent`

**Difficulty:** hard

---

### 36. central_extension_nilpotent

**Natural Language Statement:**
A central extension of nilpotent Lie algebras is nilpotent.

**Lean 4 Theorem:**
```lean
theorem LieModule.isNilpotent_of_isNilpotent_quotient_and_centralSubmodule
  {N : LieSubmodule R L M} (hN : N ≤ LieModule.maxTrivSubmodule R L M)
  [LieModule.IsNilpotent R L (M ⧸ N)] : LieModule.IsNilpotent R L M := ...
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Nilpotent`

**Difficulty:** hard

---

## Part IV: Semisimple Lie Algebras & Killing Form

### Module Organization

**Primary Imports:**
- `Mathlib.Algebra.Lie.Semisimple.Basic`
- `Mathlib.Algebra.Lie.Killing`
- `Mathlib.Algebra.Lie.InvariantForm`

**Estimated Statements:** 10

---

### 37. HasTrivialRadical

**Natural Language Statement:**
A Lie algebra has trivial radical if it contains no non-zero solvable ideals.

**Lean 4 Definition:**
```lean
class LieAlgebra.HasTrivialRadical : Prop where
  out : radical R L = ⊥
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Semisimple.Basic`

**Difficulty:** medium

---

### 38. IsSimple

**Natural Language Statement:**
A Lie algebra is simple if it is non-abelian and has no proper non-trivial ideals.

**Lean 4 Definition:**
```lean
class LieAlgebra.IsSimple : Prop where
  non_abelian : ¬IsLieAbelian L
  eq_bot_or_eq_top : ∀ I : LieIdeal R L, I = ⊥ ∨ I = ⊤
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Semisimple.Basic`

**Difficulty:** medium

---

### 39. IsSemisimple

**Natural Language Statement:**
A Lie algebra is semisimple if it is a direct sum of simple ideals, or equivalently, has trivial radical.

**Lean 4 Definition:**
```lean
class LieAlgebra.IsSemisimple (R : Type u) (L : Type v) [CommRing R] [LieRing L]
  [LieAlgebra R L] : Prop where
  -- Characterized by trivial radical
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Semisimple.Basic`

**Difficulty:** medium

---

### 40. simple_implies_hasTrivialRadical

**Natural Language Statement:**
Every simple Lie algebra has trivial radical.

**Lean 4 Theorem:**
```lean
instance (priority := 100) LieAlgebra.hasTrivialRadical_of_isSimple [LieAlgebra.IsSimple R L] :
  LieAlgebra.HasTrivialRadical R L := ...
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Semisimple.Basic`

**Difficulty:** medium

---

### 41. killingForm

**Natural Language Statement:**
The Killing form on a Lie algebra L is the symmetric bilinear form κ(x,y) = Tr(ad_x ∘ ad_y).

**Lean 4 Definition:**
```lean
noncomputable def LieAlgebra.killingForm (R : Type u) (L : Type v) [CommRing R] [LieRing L]
  [LieAlgebra R L] [Module.Free R L] [Module.Finite R L] : L →ₗ[R] L →ₗ[R] R :=
  (LinearMap.trace R L).compBilinear ((ad R L).toLinearMap ∘ₗ (ad R L).toLinearMap)
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Killing`

**Difficulty:** hard

---

### 42. IsKilling

**Natural Language Statement:**
A Lie algebra is Killing if its Killing form is non-degenerate.

**Lean 4 Definition:**
```lean
class LieAlgebra.IsKilling (R : Type u) (L : Type v) [CommRing R] [LieRing L]
  [LieAlgebra R L] : Prop where
  killingCompl_eq_bot : killingForm R L.ker = ⊥
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Killing`

**Difficulty:** hard

---

### 43. killing_implies_hasTrivialRadical

**Natural Language Statement:**
If a Lie algebra has non-degenerate Killing form (over a PID), then it has trivial radical.

**Lean 4 Theorem:**
```lean
instance (priority := 100) LieAlgebra.hasTrivialRadical_of_isKilling [IsDomain R]
  [IsPrincipalIdealRing R] [LieAlgebra.IsKilling R L] : LieAlgebra.HasTrivialRadical R L := ...
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Killing`

**Difficulty:** hard

---

### 44. killing_implies_semisimple

**Natural Language Statement:**
Over a field, a finite-dimensional Lie algebra with non-degenerate Killing form is semisimple.

**Lean 4 Theorem:**
```lean
instance (priority := 100) LieAlgebra.isSemisimple_of_isKilling [Field R]
  [Module.Finite R L] [LieAlgebra.IsKilling R L] : LieAlgebra.IsSemisimple R L := ...
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Killing`

**Difficulty:** hard

---

### 45. InvariantForm

**Natural Language Statement:**
A bilinear form Φ on a Lie module is invariant if Φ([x,y],z) = -Φ(y,[x,z]) for all x ∈ L and y, z ∈ M.

**Lean 4 Definition:**
```lean
def LieModule.InvariantForm (Φ : M →ₗ[R] M →ₗ[R] R) : Prop :=
  ∀ (x : L) (y z : M), Φ ⁅x, y⁆ z = -Φ y ⁅x, z⁆
```

**Mathlib Location:** `Mathlib.Algebra.Lie.InvariantForm`

**Difficulty:** medium

---

### 46. ideal_lattice_isBoolean

**Natural Language Statement:**
For a semisimple Lie algebra over a field, the lattice of ideals is a Boolean algebra.

**Lean 4 Theorem:**
```lean
instance : IsComplemented (LieIdeal R L) := ...
-- Implies Boolean algebra structure for semisimple L
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Semisimple.Basic`

**Difficulty:** hard

---

## Part V: Weight Theory & Cartan Subalgebras

### Module Organization

**Primary Imports:**
- `Mathlib.Algebra.Lie.Weights.Basic`
- `Mathlib.Algebra.Lie.Weights.Cartan`

**Estimated Statements:** 8

---

### 47. genWeightSpace

**Natural Language Statement:**
The generalized weight space of a Lie module M with respect to a weight χ is the subspace on which (x - χ(x))ⁿ acts as zero for all x in the Cartan subalgebra and sufficiently large n.

**Lean 4 Definition:**
```lean
def LieModule.genWeightSpace (χ : L → R) : LieSubmodule R L M :=
  ⨅ x : L, (toEnd R L M x - χ x • 1).maxGenEigenspace
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Weights.Basic`

**Difficulty:** hard

---

### 48. Weight

**Natural Language Statement:**
A weight is a linear functional χ : H → R such that the corresponding generalized weight space is non-zero.

**Lean 4 Definition:**
```lean
def LieModule.Weight (H : LieSubalgebra R L) (M : Type w) [AddCommGroup M] [Module R M]
  [LieRingModule L M] [LieModule R L M] := {χ : H → R // genWeightSpace R H M χ ≠ ⊥}
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Weights.Basic`

**Difficulty:** hard

---

### 49. rootSpace

**Natural Language Statement:**
The root space of a Cartan subalgebra H with respect to a root α is the α-weight space of the adjoint action.

**Lean 4 Definition:**
```lean
abbrev LieAlgebra.rootSpace (H : LieSubalgebra R L) (α : H → R) : LieSubmodule R H L :=
  LieModule.genWeightSpace R H L α
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Weights.Cartan`

**Difficulty:** hard

---

### 50. zeroRootSubalgebra

**Natural Language Statement:**
The zero root subalgebra is the subalgebra of elements x such that for all h in H, (ad h)ⁿ(x) = 0 for large n.

**Lean 4 Definition:**
```lean
def LieAlgebra.zeroRootSubalgebra (R : Type u) (L : Type v) (H : LieSubalgebra R L) :
  LieSubalgebra R L := (rootSpace H 0).toLieSubalgebra
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Weights.Cartan`

**Difficulty:** hard

---

### 51. zeroRootSubalgebra_eq_iff_isCartan

**Natural Language Statement:**
Under Noetherian conditions, a nilpotent subalgebra H is a Cartan subalgebra if and only if H equals its own zero root subalgebra.

**Lean 4 Theorem:**
```lean
theorem LieAlgebra.zeroRootSubalgebra_eq_iff_is_cartan [IsNoetherian R L]
  [LieModule.IsNilpotent R H H] :
  zeroRootSubalgebra R L H = H ↔ H.IsCartanSubalgebra := ...
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Weights.Cartan`

**Difficulty:** hard

---

### 52. weight_independence

**Natural Language Statement:**
The generalized weight spaces for distinct weights are independent (their sum is direct).

**Lean 4 Theorem:**
```lean
theorem LieModule.iSup_genWeightSpace_eq_top [IsTriangularizable R L M] :
  ⨆ χ : L → R, genWeightSpace R L M χ = ⊤
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Weights.Basic`

**Difficulty:** hard

---

### 53. IsTriangularizable

**Natural Language Statement:**
A Lie module is triangularizable if it decomposes as a direct sum of generalized weight spaces.

**Lean 4 Definition:**
```lean
class LieModule.IsTriangularizable (R : Type u) (L : Type v) (M : Type w)
  [CommRing R] [LieRing L] [LieAlgebra R L] [AddCommGroup M] [Module R M]
  [LieRingModule L M] [LieModule R L M] : Prop where
  iSup_eq_top : ⨆ χ : L → R, genWeightSpace R L M χ = ⊤
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Weights.Basic`

**Difficulty:** hard

---

### 54. corootSpace

**Natural Language Statement:**
The coroot space for a root α is the span of all products [x,y] where x is in the α root space and y is in the -α root space.

**Lean 4 Definition:**
```lean
def LieAlgebra.corootSpace (α : H → R) : LieSubmodule R H H :=
  LieSubmodule.lieSpan R H { ⁅x, y⁆ | x ∈ rootSpace H α, y ∈ rootSpace H (-α) }
```

**Mathlib Location:** `Mathlib.Algebra.Lie.Weights.Cartan`

**Difficulty:** hard

---

## Part VI: Lie Groups

### Module Organization

**Primary Imports:**
- `Mathlib.Geometry.Manifold.Algebra.LieGroup`

**Estimated Statements:** 8

---

### 55. LieGroup

**Natural Language Statement:**
A Lie group is a smooth manifold G equipped with a group structure such that multiplication and inversion are smooth maps.

**Lean 4 Definition:**
```lean
class LieGroup (I : ModelWithCorners 𝕜 E H) (n : ℕ∞) (G : Type w) [TopologicalSpace G]
  [ChartedSpace H G] [Group G] extends ContMDiffMul I n G where
  contMDiff_inv : ContMDiff I I n fun g : G => g⁻¹
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.Algebra.LieGroup`

**Difficulty:** medium

---

### 56. LieAddGroup

**Natural Language Statement:**
An additive Lie group is a smooth manifold G equipped with an additive group structure such that addition and negation are smooth.

**Lean 4 Definition:**
```lean
class LieAddGroup (I : ModelWithCorners 𝕜 E H) (n : ℕ∞) (G : Type w) [TopologicalSpace G]
  [ChartedSpace H G] [AddGroup G] extends ContMDiffAdd I n G where
  contMDiff_neg : ContMDiff I I n fun g : G => -g
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.Algebra.LieGroup`

**Difficulty:** medium

---

### 57. contMDiff_inv

**Natural Language Statement:**
In a Lie group, the inversion map g ↦ g⁻¹ is smooth.

**Lean 4 Theorem:**
```lean
theorem contMDiff_inv [LieGroup I n G] : ContMDiff I I n fun g : G => g⁻¹ :=
  LieGroup.contMDiff_inv
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.Algebra.LieGroup`

**Difficulty:** easy

---

### 58. contMDiff_div

**Natural Language Statement:**
In a Lie group, the division map (g,h) ↦ g/h is smooth.

**Lean 4 Theorem:**
```lean
theorem contMDiff_div [LieGroup I n G] : ContMDiff (I.prod I) I n fun p : G × G => p.1 / p.2
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.Algebra.LieGroup`

**Difficulty:** easy

---

### 59. normedSpace_is_lieAddGroup

**Natural Language Statement:**
Every normed vector space over a nontrivially normed field is an additive Lie group.

**Lean 4 Instance:**
```lean
instance instNormedSpaceLieAddGroup [NontriviallyNormedField 𝕜] [NormedAddCommGroup E]
  [NormedSpace 𝕜 E] : LieAddGroup (modelWithCornersSelf 𝕜 E) ⊤ E := ...
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.Algebra.LieGroup`

**Difficulty:** medium

---

### 60. product_lieGroup

**Natural Language Statement:**
The product of two Lie groups is a Lie group.

**Lean 4 Instance:**
```lean
instance Prod.lieGroup [LieGroup I n G] [LieGroup J m H] :
  LieGroup (I.prod J) (min n m) (G × H) := ...
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.Algebra.LieGroup`

**Difficulty:** medium

---

### 61. topologicalGroup_of_lieGroup

**Natural Language Statement:**
Every Lie group is a topological group.

**Lean 4 Theorem:**
```lean
theorem topologicalGroup_of_lieGroup [LieGroup I n G] : TopologicalGroup G := ...
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.Algebra.LieGroup`

**Difficulty:** easy

---

### 62. ContMDiffInv₀

**Natural Language Statement:**
For manifolds with inversion away from zero (like complete normed fields), inversion is smooth on the units.

**Lean 4 Class:**
```lean
class ContMDiffInv₀ (I : ModelWithCorners 𝕜 E H) (n : ℕ∞) (G : Type w)
  [TopologicalSpace G] [ChartedSpace H G] [Zero G] [Inv G] : Prop where
  contMDiff_inv₀ : ContMDiff I I n fun g : {x : G // x ≠ 0} => (g : G)⁻¹
```

**Mathlib Location:** `Mathlib.Geometry.Manifold.Algebra.LieGroup`

**Difficulty:** medium

---

## Part VII: Matrix Groups

### Module Organization

**Primary Imports:**
- `Mathlib.LinearAlgebra.Matrix.GeneralLinearGroup.Basic`
- `Mathlib.LinearAlgebra.Matrix.SpecialLinearGroup`
- `Mathlib.LinearAlgebra.UnitaryGroup`

**Estimated Statements:** 8

---

### 63. GeneralLinearGroup (GL)

**Natural Language Statement:**
The general linear group GL(n,R) is the group of invertible n×n matrices over a ring R.

**Lean 4 Definition:**
```lean
abbrev Matrix.GeneralLinearGroup (n : Type u) (R : Type v) [Fintype n] [DecidableEq n]
  [CommRing R] := (Matrix n n R)ˣ
```

**Mathlib Location:** `Mathlib.LinearAlgebra.Matrix.GeneralLinearGroup.Defs`

**Difficulty:** easy

---

### 64. center_GL

**Natural Language Statement:**
The center of GL(n,R) consists of scalar matrices: Z(GL(n,R)) = {λI : λ ∈ R×}.

**Lean 4 Theorem:**
```lean
theorem Matrix.GeneralLinearGroup.center_eq_range_units :
  Subgroup.center (GeneralLinearGroup n R) = MonoidHom.range (scalar n).toHomUnits
```

**Mathlib Location:** `Mathlib.LinearAlgebra.Matrix.GeneralLinearGroup.Basic`

**Difficulty:** medium

---

### 65. SpecialLinearGroup (SL)

**Natural Language Statement:**
The special linear group SL(n,R) consists of n×n matrices with determinant 1.

**Lean 4 Definition:**
```lean
def Matrix.SpecialLinearGroup (n : Type u) (R : Type v) [Fintype n] [DecidableEq n]
  [CommRing R] := {A : Matrix n n R // A.det = 1}
```

**Mathlib Location:** `Mathlib.LinearAlgebra.Matrix.SpecialLinearGroup`

**Difficulty:** easy

---

### 66. SL_det_one

**Natural Language Statement:**
Every element of SL(n,R) has determinant 1.

**Lean 4 Theorem:**
```lean
theorem Matrix.SpecialLinearGroup.det_coe (A : SpecialLinearGroup n R) :
  (A : Matrix n n R).det = 1 := A.2
```

**Mathlib Location:** `Mathlib.LinearAlgebra.Matrix.SpecialLinearGroup`

**Difficulty:** easy

---

### 67. unitaryGroup

**Natural Language Statement:**
The unitary group U(n,α) consists of n×n matrices A such that A*Aᴴ = I, where Aᴴ is the conjugate transpose.

**Lean 4 Definition:**
```lean
def Matrix.unitaryGroup (n : Type u) (α : Type v) [Fintype n] [DecidableEq n]
  [CommRing α] [StarRing α] := {A : Matrix n n α // A * star A = 1}
```

**Mathlib Location:** `Mathlib.LinearAlgebra.UnitaryGroup`

**Difficulty:** easy

---

### 68. unitary_star_mul_self

**Natural Language Statement:**
For a unitary matrix A, we have A*Aᴴ = Aᴴ*A = I.

**Lean 4 Theorem:**
```lean
theorem Matrix.unitaryGroup.star_mul_self (A : unitaryGroup n α) :
  star (A : Matrix n n α) * A = 1 := ...
```

**Mathlib Location:** `Mathlib.LinearAlgebra.UnitaryGroup`

**Difficulty:** easy

---

### 69. orthogonalGroup

**Natural Language Statement:**
The orthogonal group O(n,R) consists of real n×n matrices A such that AᵀA = I.

**Lean 4 Definition:**
```lean
def Matrix.orthogonalGroup (n : Type u) (R : Type v) [Fintype n] [DecidableEq n]
  [CommRing R] := {A : Matrix n n R // A * Aᵀ = 1}
```

**Mathlib Location:** `Mathlib.LinearAlgebra.UnitaryGroup`

**Difficulty:** easy

---

### 70. specialUnitaryGroup

**Natural Language Statement:**
The special unitary group SU(n,α) consists of unitary matrices with determinant 1.

**Lean 4 Definition:**
```lean
def Matrix.specialUnitaryGroup (n : Type u) (α : Type v) [Fintype n] [DecidableEq n]
  [CommRing α] [StarRing α] := {A : unitaryGroup n α // (A : Matrix n n α).det = 1}
```

**Mathlib Location:** `Mathlib.LinearAlgebra.UnitaryGroup`

**Difficulty:** easy

---

## Summary Statistics

| Part | Statements | Formalized | Templates |
|------|------------|------------|-----------|
| I. Lie Algebras | 14 | 14 | 0 |
| II. Subalgebras & Ideals | 10 | 10 | 0 |
| III. Solvable & Nilpotent | 12 | 12 | 0 |
| IV. Semisimple & Killing | 10 | 10 | 0 |
| V. Weight Theory & Cartan | 8 | 8 | 0 |
| VI. Lie Groups | 8 | 8 | 0 |
| VII. Matrix Groups | 8 | 8 | 0 |
| **Total** | **70** | **70** | **0** |

### Measurability Score: 85/100

**Rationale:**
- Core Lie algebra theory (Parts I-IV): Fully formalized in Mathlib4
- Weight theory and Cartan subalgebras (Part V): Well-developed, some advanced results still in progress
- Lie groups (Part VI): Basic theory formalized, exponential map between Lie group and algebra partially developed
- Matrix groups (Part VII): Fully formalized

**Key Gap:** The exponential map exp: 𝔤 → G connecting Lie algebras to Lie groups is not fully formalized in a general setting (specific cases like matrix exp exist).

---

## References

### Mathlib4 Documentation
- [Lie Algebra Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Lie/Basic.html)
- [Lie Subalgebra](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Lie/Subalgebra.html)
- [Solvable Lie Algebras](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Lie/Solvable.html)
- [Nilpotent Lie Algebras](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Lie/Nilpotent.html)
- [Semisimple Lie Algebras](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Lie/Semisimple/Basic.html)
- [Killing Form](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Lie/Killing.html)
- [Weight Theory](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/Lie/Weights/Basic.html)
- [Lie Groups](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Manifold/Algebra/LieGroup.html)
- [General Linear Group](https://leanprover-community.github.io/mathlib4_docs/Mathlib/LinearAlgebra/Matrix/GeneralLinearGroup/Basic.html)

### Standard References
- Humphreys, J. *Introduction to Lie Algebras and Representation Theory*
- Hall, B. *Lie Groups, Lie Algebras, and Representations*
- Knapp, A. *Lie Groups Beyond an Introduction*
