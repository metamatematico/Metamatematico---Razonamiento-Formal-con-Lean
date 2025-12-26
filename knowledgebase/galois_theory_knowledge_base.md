# Galois Theory Knowledge Base

**Domain**: Galois Theory & Field Extensions
**Lean 4 Coverage**: High (finite and infinite Galois theory)
**Source**: Mathlib4 `FieldTheory.*` and `RingTheory.*` modules
**Last Updated**: 2025-12-14

---

## Overview

This knowledge base covers Galois Theory formalization in Lean 4/Mathlib, including field extensions, separability, normality, splitting fields, algebraic closures, and the fundamental theorem. Built on the algebraic hierarchy with fields, algebras, and polynomial rings.

**Key Gap**: Angle trisection impossibility (#8 on 100 theorems) and constructible numbers theory not yet formalized.

---

## Related Knowledge Bases

### Prerequisites
- **Group Theory** (`group_theory_knowledge_base.md`): Subgroups, normal subgroups, quotients
- **Linear Algebra** (`linear_algebra_knowledge_base.md`): Vector spaces, dimension theory

### Builds Upon This KB
- **Algebraic Number Theory** (`algebraic_number_theory_knowledge_base.md`): Number field extensions, algebraic integers
- **P-adic Numbers** (`p_adic_numbers_knowledge_base.md`): Local field extensions

### Related Topics
- **Arithmetic** (`arithmetic_knowledge_base.md`): Finite fields, cyclotomic fields
- **Number Theory** (`number_theory_knowledge_base.md`): Algebraic integers, class field theory connections

### Scope Clarification
This KB focuses on **Galois theory and field extensions**:
- Intermediate fields and tower law
- Separability, normality, splitting fields
- Algebraic closures
- The fundamental theorem of Galois theory
- Solvability by radicals

For **applications to number fields**, see **Algebraic Number Theory KB**.

---

## 1. FIELD EXTENSIONS

### 1.1 Intermediate Field

**Concept**: A subfield of L containing K in a field extension L/K.

**NL Statement**: "An intermediate field in a tower L/K is a subfield of L that contains K, forming a subalgebra closed under field operations."

**Lean 4 Definition**:
```lean
structure IntermediateField (K : Type u₁) (L : Type u₂)
  [Field K] [Field L] [Algebra K L] extends Subalgebra K L : Type u₂ where
  inv_mem' : ∀ x ∈ carrier, x⁻¹ ∈ carrier
```

**Key Theorem**:
```lean
theorem IntermediateField.ext {K L : Type*} [Field K] [Field L] [Algebra K L]
  {S T : IntermediateField K L} (h : ∀ x : L, x ∈ S ↔ x ∈ T) : S = T
```

**Imports**: `Mathlib.FieldTheory.IntermediateField.Basic`

**Difficulty**: medium

---

### 1.2 Degree of Extension

**Concept**: The dimension of E as an F-vector space.

**NL Statement**: "The degree [E:F] of a field extension E/F is the dimension of E viewed as a vector space over F."

**Lean 4 Definition**:
```lean
noncomputable def Module.finrank (R : Type u₁) (M : Type u₂)
  [Semiring R] [AddCommMonoid M] [Module R M] : ℕ
```

**Usage**: For field extension E/F, write `Module.finrank F E` to get [E:F].

**Key Property**: Returns 0 by convention when dimension is infinite.

**Imports**: `Mathlib.LinearAlgebra.Dimension.Finrank`

**Difficulty**: medium

---

### 1.3 Finite-Dimensional Extension

**Concept**: Extension where E is finite-dimensional over F.

**NL Statement**: "A field extension E/F is finite-dimensional if E has finite dimension as an F-vector space."

**Lean 4 Definition**:
```lean
class FiniteDimensional (K V : Type*) [DivisionRing K] [AddCommGroup V] [Module K V] : Prop where
  out : Module.Finite K V
```

**Imports**: `Mathlib.LinearAlgebra.FiniteDimensional.Defs`

**Difficulty**: easy

---

## 2. ALGEBRAIC ELEMENTS

### 2.1 Algebraic Element

**Concept**: An element that is a root of some nonzero polynomial.

**NL Statement**: "An element x of an algebra A over ring R is algebraic if it is a root of some nonzero polynomial with coefficients in R."

**Lean 4 Definition**:
```lean
def IsAlgebraic (R : Type u) {A : Type v}
  [CommRing R] [Ring A] [Algebra R A] (x : A) : Prop :=
  ∃ (p : Polynomial R), p ≠ 0 ∧ (Polynomial.aeval x) p = 0
```

**Imports**: `Mathlib.RingTheory.Algebraic.Defs`

**Difficulty**: easy

---

### 2.2 Transcendental Element

**Concept**: An element that is not algebraic.

**NL Statement**: "An element is transcendental if it is not a root of any nonzero polynomial over the base ring."

**Lean 4 Definition**:
```lean
def Transcendental (R : Type u) {A : Type v}
  [CommRing R] [Ring A] [Algebra R A] (x : A) : Prop :=
  ¬IsAlgebraic R x
```

**Imports**: `Mathlib.RingTheory.Algebraic.Defs`

**Difficulty**: easy

---

### 2.3 Algebraic Extension

**Concept**: An extension where every element is algebraic.

**NL Statement**: "An algebra A over R is algebraic if every element of A is algebraic over R."

**Lean 4 Definition**:
```lean
class Algebra.IsAlgebraic (R : Type u) (A : Type v)
  [CommRing R] [Ring A] [Algebra R A] : Prop where
  isAlgebraic (x : A) : IsAlgebraic R x
```

**Imports**: `Mathlib.RingTheory.Algebraic.Defs`

**Difficulty**: medium

---

### 2.4 Minimal Polynomial

**Concept**: The unique monic polynomial of minimal degree having x as a root.

**NL Statement**: "The minimal polynomial of an element x over field F is the unique monic irreducible polynomial that has x as a root."

**Key Properties**:
```lean
-- minpoly F x divides any polynomial p with x as a root
-- minpoly F x is irreducible (and prime)
-- Minimal polynomial of 0 is X
-- Minimal polynomial of 1 is X - 1
```

**Imports**: `Mathlib.FieldTheory.Minpoly.Field`

**Difficulty**: medium

---

## 3. SEPARABILITY

### 3.1 Separable Element

**Concept**: An element whose minimal polynomial is separable.

**NL Statement**: "An element x is separable over F if its minimal polynomial is separable (coprime with its formal derivative)."

**Lean 4 Definition**:
```lean
def IsSeparable (F : Type u₁) {K : Type u₃}
  [CommRing F] [Ring K] [Algebra F K] (x : K) : Prop :=
  (minpoly F x).Separable
```

**Imports**: `Mathlib.FieldTheory.Separable`

**Difficulty**: medium

---

### 3.2 Separable Extension

**Concept**: An extension where every element is separable.

**NL Statement**: "A field extension E/F is separable if every element of E is separable over F. In Mathlib, this implies the extension is algebraic."

**Lean 4 Definition**:
```lean
class Algebra.IsSeparable (F : Type u₁) (K : Type u₃)
  [CommRing F] [Ring K] [Algebra F K] : Prop where
  isSeparable' (x : K) : IsSeparable F x
```

**Key Equivalence**:
```lean
theorem Algebra.isSeparable_iff {F K : Type*} [CommRing F] [Ring K] [Algebra F K] :
  Algebra.IsSeparable F K ↔ ∀ (x : K), IsIntegral F x ∧ IsSeparable F x
```

**Imports**: `Mathlib.FieldTheory.Separable`

**Difficulty**: medium

---

## 4. NORMALITY

### 4.1 Normal Extension

**Concept**: An extension where minimal polynomials of all elements split completely.

**NL Statement**: "A field extension E/F is normal if the minimal polynomial of every element in E splits completely in E. For finite extensions, this is equivalent to being a splitting field."

**Lean 4 Characterization**:
```lean
theorem Normal.of_isSplittingField {F E : Type*} [Field F] [Field E] [Algebra F E]
  (p : Polynomial F) [hFEp : Polynomial.IsSplittingField F E p] :
  Normal F E

theorem Normal.exists_isSplittingField (F K : Type*) [Field F] [Field K]
  [Algebra F K] [h : Normal F K] [FiniteDimensional F K] :
  ∃ (p : Polynomial F), Polynomial.IsSplittingField F K p
```

**Imports**: `Mathlib.FieldTheory.Normal.Basic`

**Difficulty**: hard

---

## 5. SPLITTING FIELDS

### 5.1 Splitting Field Predicate

**Concept**: A field extension where a polynomial splits completely and is generated by its roots.

**NL Statement**: "A field extension L/K is a splitting field for polynomial f if f splits completely in L and L is generated over K by the roots of f."

**Lean 4 Definition**:
```lean
class Polynomial.IsSplittingField (K : Type v) (L : Type w)
  [Field K] [Field L] [Algebra K L] (f : Polynomial K) : Prop where
  splits' : (Polynomial.map (algebraMap K L) f).Splits
  adjoin_rootSet' : Algebra.adjoin K (f.rootSet L) = ⊤
```

**Imports**: `Mathlib.FieldTheory.SplittingField.IsSplittingField`

**Difficulty**: hard

---

### 5.2 Splitting Field Construction

**Concept**: Constructing a splitting field for any polynomial.

**NL Statement**: "For any polynomial f over field K, there exists a splitting field, and all splitting fields of f are isomorphic."

**Lean 4 Definition**:
```lean
def Polynomial.SplittingField (f : Polynomial K) : Type*
```

**Key Theorem**:
```lean
-- Polynomial.IsSplittingField.algEquiv
-- Every splitting field of polynomial f is isomorphic to SplittingField f
```

**Imports**: `Mathlib.FieldTheory.SplittingField.Construction`

**Difficulty**: hard

---

## 6. ALGEBRAIC CLOSURE

### 6.1 Algebraically Closed Field

**Concept**: A field where every polynomial splits.

**NL Statement**: "A field k is algebraically closed if every polynomial over k splits into linear factors."

**Lean 4 Definition**:
```lean
class IsAlgClosed (k : Type u) [Field k] : Prop where
  splits (p : Polynomial k) : p.Splits
```

**Key Theorems**:
```lean
-- Every nonconstant polynomial has a root
theorem IsAlgClosed.exists_root {k : Type*} [Field k] [IsAlgClosed k]
  {p : Polynomial k} (hp : 0 < p.degree) : ∃ x, p.IsRoot x

-- Every irreducible polynomial is linear
theorem IsAlgClosed.degree_eq_one_of_irreducible {k : Type*} [Field k] [IsAlgClosed k]
  {p : Polynomial k} (hp : Irreducible p) : p.degree = 1
```

**Imports**: `Mathlib.FieldTheory.IsAlgClosed.Basic`

**Difficulty**: medium

---

### 6.2 Algebraic Closure

**Concept**: A field that is both algebraically closed and algebraic over the base.

**NL Statement**: "A field K is an algebraic closure of R if K is algebraically closed and algebraic over R. Any two algebraic closures are isomorphic."

**Lean 4 Definition**:
```lean
class IsAlgClosure (R : Type u) (K : Type v)
  [CommRing R] [Field K] [Algebra R K] [NoZeroSMulDivisors R K] : Prop where
  isAlgClosed : IsAlgClosed K
  isAlgebraic : Algebra.IsAlgebraic R K
```

**Construction**:
```lean
def AlgebraicClosure (k : Type u) [Field k] : Type u :=
  (MvPolynomial (Vars k) k) ⧸ (maxIdeal k)
```

**Imports**: `Mathlib.FieldTheory.IsAlgClosed.AlgebraicClosure`

**Difficulty**: hard

---

## 7. GALOIS EXTENSIONS

### 7.1 Galois Extension Definition

**Concept**: An extension that is both separable and normal.

**NL Statement**: "A field extension E/F is Galois if it is both separable and normal. Equivalently, E is the splitting field of a separable polynomial over F."

**Lean 4 Definition**:
```lean
class IsGalois (F : Type u₁) [Field F] (E : Type u₂) [Field E]
  [Algebra F E] : Prop where
  to_isSeparable : Algebra.IsSeparable F E
  to_normal : Normal F E
```

**Equivalence**:
```lean
theorem isGalois_iff {F E : Type*} [Field F] [Field E] [Algebra F E] :
  IsGalois F E ↔ Algebra.IsSeparable F E ∧ Normal F E
```

**Imports**: `Mathlib.FieldTheory.Galois.Basic`

**Difficulty**: hard

---

### 7.2 Galois Extension Characterizations (TFAE)

**Concept**: Equivalent conditions for being Galois.

**NL Statement**: "For finite-dimensional extensions, being Galois is equivalent to: (1) fixed field of all automorphisms is base field, (2) |Aut(E/F)| = [E:F], (3) E is splitting field of separable polynomial."

**Lean 4 Theorem**:
```lean
theorem IsGalois.tfae [FiniteDimensional F E] :
  [IsGalois F E,
   IntermediateField.fixedField ⊤ = ⊥,
   Nat.card (E ≃ₐ[F] E) = Module.finrank F E,
   ∃ p : Polynomial F, p.Separable ∧ Polynomial.IsSplittingField F E p
  ].TFAE
```

**Imports**: `Mathlib.FieldTheory.Galois.Basic`

**Difficulty**: hard

---

### 7.3 Separable Splitting Fields are Galois

**Concept**: A splitting field of a separable polynomial is Galois.

**NL Statement**: "If E is the splitting field of a separable polynomial p over F, then E/F is a Galois extension."

**Lean 4 Theorem**:
```lean
theorem IsGalois.of_separable_splitting_field {p : Polynomial F}
  [Polynomial.IsSplittingField F E p] (hp : p.Separable) :
  IsGalois F E
```

**Imports**: `Mathlib.FieldTheory.Galois.Basic`

**Difficulty**: hard

---

### 7.4 Key Galois Instances

**Concept**: Important automatic Galois instances.

**NL Statement**: "Every field is Galois over itself. In a tower E/K/F, if E is Galois over F, then E is Galois over K. Separable quadratic extensions are Galois."

**Lean 4 Instances**:
```lean
-- Self-Galois
instance IsGalois.self (F : Type u₁) [Field F] : IsGalois F F

-- Tower property
instance IsGalois.tower_top_of_isGalois [IsGalois F E] : IsGalois K E

-- Quadratic extensions
instance Algebra.IsQuadraticExtension.isGalois
  [IsQuadraticExtension F K] [Algebra.IsSeparable F K] : IsGalois F K
```

**Imports**: `Mathlib.FieldTheory.Galois.Basic`

**Difficulty**: medium

---

## 8. GALOIS GROUPS AND AUTOMORPHISMS

### 8.1 Galois Group

**Concept**: The group of F-algebra automorphisms of E.

**NL Statement**: "The Galois group Gal(E/F) is the group of all F-algebra automorphisms of E, which are field automorphisms of E that fix every element of F."

**Lean 4 Notation**: `E ≃ₐ[F] E` represents `AlgEquiv F E E`

**Key Theorem**:
```lean
theorem IsGalois.card_aut_eq_finrank [FiniteDimensional F E] [IsGalois F E] :
  Nat.card (E ≃ₐ[F] E) = Module.finrank F E
```

**Imports**: `Mathlib.Algebra.Algebra.Equiv`

**Difficulty**: hard

---

### 8.2 Fixed Field

**Concept**: Elements fixed by a subgroup of automorphisms.

**NL Statement**: "The fixed field of a subgroup H of Gal(E/F) is the set of elements in E that are fixed by every automorphism in H."

**Lean 4 Definition**:
```lean
def IntermediateField.fixedField (H : Subgroup (E ≃ₐ[F] E)) : IntermediateField F E
```

**Imports**: `Mathlib.FieldTheory.Galois.Basic`

**Difficulty**: hard

---

### 8.3 Fixing Subgroup

**Concept**: Automorphisms that fix an intermediate field.

**NL Statement**: "The fixing subgroup of an intermediate field K is the set of automorphisms in Gal(E/F) that fix every element of K."

**Lean 4 Definition**:
```lean
def IntermediateField.fixingSubgroup (K : IntermediateField F E) : Subgroup (E ≃ₐ[F] E)
```

**Imports**: `Mathlib.FieldTheory.Galois.Basic`

**Difficulty**: hard

---

## 9. FUNDAMENTAL THEOREM OF GALOIS THEORY

### 9.1 Galois Correspondence (Finite Case)

**Concept**: Order-reversing bijection between intermediate fields and subgroups.

**NL Statement**: "For finite-dimensional Galois extensions E/F, there is an order-reversing bijection between intermediate fields F ⊆ K ⊆ E and subgroups of Gal(E/F). Larger intermediate fields correspond to smaller subgroups."

**Lean 4 Definition**:
```lean
def IsGalois.intermediateFieldEquivSubgroup [FiniteDimensional F E] [IsGalois F E] :
  IntermediateField F E ≃o (Subgroup (E ≃ₐ[F] E))ᵒᵈ
```

**Note**: The `ᵒᵈ` indicates order-dual (contravariant correspondence).

**Imports**: `Mathlib.FieldTheory.Galois.Basic`

**Difficulty**: hard

---

### 9.2 Fixed Field of Fixing Subgroup

**Concept**: The bijection property: recovering K from its fixing subgroup.

**NL Statement**: "In a finite Galois extension, the fixed field of the fixing subgroup of an intermediate field K is K itself."

**Lean 4 Theorem**:
```lean
theorem IsGalois.fixedField_fixingSubgroup (K : IntermediateField F E)
  [FiniteDimensional F E] [IsGalois F E] :
  IntermediateField.fixedField K.fixingSubgroup = K
```

**Imports**: `Mathlib.FieldTheory.Galois.Basic`

**Difficulty**: hard

---

### 9.3 Fixing Subgroup of Fixed Field

**Concept**: The bijection property: recovering H from its fixed field.

**NL Statement**: "In a finite-dimensional extension, the fixing subgroup of the fixed field of H recovers H."

**Lean 4 Theorem**:
```lean
theorem IntermediateField.fixingSubgroup_fixedField (H : Subgroup (E ≃ₐ[F] E))
  [FiniteDimensional F E] :
  (IntermediateField.fixedField H).fixingSubgroup = H
```

**Imports**: `Mathlib.FieldTheory.Galois.Basic`

**Difficulty**: hard

---

### 9.4 Normal Subgroups and Normal Extensions

**Concept**: Normal subgroups correspond to Galois intermediate extensions.

**NL Statement**: "If H is a normal subgroup of Gal(E/F), then the fixed field of H is Galois over F, and Gal(fixed field/F) is isomorphic to Gal(E/F)/H."

**Key Result**:
```lean
-- IsGalois.normalAutEquivQuotient
-- For normal closed subgroups H of Gal(E/F):
-- Gal(fixedField H / F) ≅ Gal(E/F) / H
```

**Imports**: `Mathlib.FieldTheory.Galois.Basic`

**Difficulty**: very hard

---

## 10. INFINITE GALOIS THEORY

### 10.1 Galois Correspondence (Infinite Case)

**Concept**: For infinite extensions, closed subgroups replace arbitrary subgroups.

**NL Statement**: "For infinite Galois extensions, the Galois correspondence relates intermediate fields to closed subgroups of the Galois group with respect to the Krull topology."

**Key Theorems**:
```lean
-- fixingSubgroup_isClosed
-- The subgroup fixing L (i.e., Gal(K/L)) is closed

-- fixedField_fixingSubgroup
-- For closed subgroups H: fixingSubgroup(fixedField H) = H

-- fixingSubgroup_fixedField
-- For intermediate fields L: fixedField(fixingSubgroup L) = L
```

**Imports**: `Mathlib.FieldTheory.Galois.Infinite`

**Difficulty**: very hard

---

### 10.2 Topological Characterizations

**Concept**: Open and normal subgroups have special meanings.

**NL Statement**: "A fixing subgroup is open if and only if the intermediate field is finite-dimensional. A fixing subgroup is normal if and only if the intermediate field is Galois."

**Key Theorems**:
```lean
-- isOpen_iff_finite
-- A fixing subgroup is open iff the intermediate field is finite-dimensional

-- normal_iff_isGalois
-- A fixing subgroup is normal iff the intermediate field is Galois
```

**Imports**: `Mathlib.FieldTheory.Galois.Infinite`

**Difficulty**: very hard

---

## 11. CYCLOTOMIC THEORY

### 11.1 Cyclotomic Polynomials

**Concept**: The minimal polynomial of primitive roots of unity.

**NL Statement**: "The n-th cyclotomic polynomial Φₙ(X) is the product of (X - ζ) where ζ ranges over primitive n-th roots of unity. Its degree is φ(n) (Euler's totient)."

**Key Theorems**:
```lean
-- Polynomial.degree_cyclotomic
-- The degree of cyclotomic n is totient n: deg(Φₙ) = φ(n)

-- Polynomial.prod_cyclotomic_eq_X_pow_sub_one
-- X^n - 1 = ∏_{d|n} Φ_d(X)
```

**Imports**: `Mathlib.RingTheory.Polynomial.Cyclotomic.Basic`

**Difficulty**: hard

---

## 12. STANDARD SETUP

**NL Statement**: "Standard imports and variable declarations for Galois theory work."

**Lean 4**:
```lean
import Mathlib.FieldTheory.Galois.Basic
import Mathlib.FieldTheory.IntermediateField.Basic
import Mathlib.FieldTheory.SplittingField.IsSplittingField
import Mathlib.FieldTheory.IsAlgClosed.AlgebraicClosure
import Mathlib.FieldTheory.Separable
import Mathlib.FieldTheory.Normal.Basic

open Polynomial IntermediateField

variable {F : Type*} [Field F]
variable {E : Type*} [Field E] [Algebra F E]
variable [FiniteDimensional F E] [IsGalois F E]
```

**Difficulty**: easy

---

## 13. NOTATION REFERENCE

| Math Notation | Lean 4 Notation | Description |
|---------------|-----------------|-------------|
| E/F | `[Field F] [Field E] [Algebra F E]` | Field extension |
| [E:F] | `Module.finrank F E` | Degree of extension |
| Gal(E/F) | `E ≃ₐ[F] E` | Galois group (automorphisms) |
| F(α) | `IntermediateField.adjoin F {α}` | Simple extension |
| K̄ | `AlgebraicClosure K` | Algebraic closure |
| Φₙ(X) | `Polynomial.cyclotomic n R` | Cyclotomic polynomial |
| minpoly_F(α) | `minpoly F α` | Minimal polynomial |

---

## 14. GAPS AND LIMITATIONS

### Not Yet Formalized
1. **Impossibility of angle trisection** - Theorem #8 on 100 theorems list
2. **Constructible numbers theory** - Foundation for classical impossibility results
3. **Complete Abel-Ruffini theorem** - Only one direction currently formalized

### Well-Covered Areas
1. Fundamental theorem of Galois theory (finite and infinite)
2. Splitting fields (existence and uniqueness)
3. Algebraic closures (construction and properties)
4. Separability and normality
5. Field extension towers
6. Cyclotomic polynomials

---

## Sources

- [Mathlib.FieldTheory.Galois.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/FieldTheory/Galois/Basic.html)
- [Mathlib.FieldTheory.Galois.Infinite](https://leanprover-community.github.io/mathlib4_docs/Mathlib/FieldTheory/Galois/Infinite.html)
- [Mathlib.FieldTheory.IntermediateField.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/FieldTheory/IntermediateField/Basic.html)
- [Mathlib.FieldTheory.SplittingField.IsSplittingField](https://leanprover-community.github.io/mathlib4_docs/Mathlib/FieldTheory/SplittingField/IsSplittingField.html)
- [Mathlib.FieldTheory.IsAlgClosed.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/FieldTheory/IsAlgClosed/Basic.html)
- [Mathematics in mathlib](https://leanprover-community.github.io/mathlib-overview.html)
- [100 theorems in Lean](https://leanprover-community.github.io/100.html)
