/-
Copyright (c) 2024. All rights reserved.
Released under Apache 2.0 license.

# The Second Isomorphism Theorem for Rings (Diamond/Parallelogram Theorem)

This file formalizes the Second Isomorphism Theorem for Rings in Lean 4 using Mathlib.

## Mathematical Background

The Second Isomorphism Theorem for Rings states:

Let R be a commutative ring. Let S be a subring of R, and let I be an ideal of R. Then:
1. The intersection S cap I is an ideal of S
2. The quotient ring S/(S cap I) is isomorphic to the image of S in R/I

More precisely, if we restrict the quotient map R -> R/I to the subring S,
then by the First Isomorphism Theorem:
  S/(S cap I) iso range(S -> R/I)

This theorem is also known as the:
- **Diamond Theorem** - from the lattice diagram shape
- **Parallelogram Theorem** - from the isomorphism of "opposite sides"

## Key Insight

The key to the Second Isomorphism Theorem is the First Isomorphism Theorem.
When we restrict the quotient map R -> R/I to the subring S, we get:
- A ring homomorphism f : S -> R/I
- The kernel of f is exactly S cap I
- Therefore S/ker(f) iso range(f)

## Main Results

- `intersectionIdeal`: S cap I as an ideal of S
- `quotientMapRestrict`: The restriction of R -> R/I to S
- `ker_quotientMapRestrict`: The kernel is S cap I
- `secondIsomorphismTheorem`: S/(S cap I) iso range(f)

## References

* [Serge Lang, *Algebra*][lang2002algebra]
* [David S. Dummit and Richard M. Foote, *Abstract Algebra*]
* [Michael Artin, *Algebra*][artin2011algebra]
-/

import Mathlib.RingTheory.Ideal.Quotient.Operations
import Mathlib.Algebra.Ring.Subring.Basic

/-!
## Notation

We use the following notation throughout this file:
- `->+*` : Ring homomorphism (RingHom)
- `iso+*` : Ring isomorphism (RingEquiv)
- `R quo I` : Quotient ring of R by ideal I
- `S cap I` : Intersection of subring S and ideal I
-/

namespace RingSecondIsomorphism

variable {R : Type*} [CommRing R]

-- ============================================================================
-- Section 1: The Intersection S cap I is an Ideal of S
-- ============================================================================

section IntersectionIsIdeal

/-!
### Part 1: The Intersection S cap I is an Ideal of S

When I is an ideal of R and S is any subring, the intersection S cap I
is an ideal of S (not just of R).

In Mathlib, `I.comap S.subtype` gives the preimage of I under the inclusion
S -> R, which is exactly S cap I viewed as an ideal of S.
-/

/--
**Theorem (Intersection is Ideal of Subring)**: For an ideal I of R and
subring S, the intersection S cap I is an ideal of S.

In Mathlib, this is `I.comap S.subtype` - the preimage of I under inclusion.
-/
theorem intersection_is_ideal_of_subring (S : Subring R) (I : Ideal R) :
    ∃ J : Ideal S, ∀ x : S, x ∈ J ↔ (x : R) ∈ I := by
  use I.comap S.subtype
  intro x
  rfl

/--
The comap ideal `I.comap S.subtype` represents S cap I as an ideal of S.
-/
def intersectionIdeal (S : Subring R) (I : Ideal R) : Ideal S :=
  I.comap S.subtype

/--
An element of S is in the intersection ideal iff it is in I.
-/
theorem mem_intersectionIdeal_iff (S : Subring R) (I : Ideal R) (x : S) :
    x ∈ intersectionIdeal S I ↔ (x : R) ∈ I :=
  Iff.rfl

/--
The intersection ideal contains zero.
-/
theorem intersectionIdeal_zero_mem (S : Subring R) (I : Ideal R) :
    (0 : S) ∈ intersectionIdeal S I := by
  simp only [intersectionIdeal, Ideal.mem_comap]
  exact I.zero_mem

/--
The intersection ideal is closed under addition.
-/
theorem intersectionIdeal_add_mem (S : Subring R) (I : Ideal R) {a b : S}
    (ha : a ∈ intersectionIdeal S I) (hb : b ∈ intersectionIdeal S I) :
    a + b ∈ intersectionIdeal S I := by
  simp only [intersectionIdeal, Ideal.mem_comap] at *
  exact I.add_mem ha hb

/--
The intersection ideal is closed under multiplication by elements of S.
-/
theorem intersectionIdeal_mul_mem (S : Subring R) (I : Ideal R) {a : S} {r : S}
    (ha : a ∈ intersectionIdeal S I) :
    r * a ∈ intersectionIdeal S I := by
  simp only [intersectionIdeal, Ideal.mem_comap] at *
  exact I.mul_mem_left r ha

end IntersectionIsIdeal

-- ============================================================================
-- Section 2: The Restriction of the Quotient Map
-- ============================================================================

section QuotientMapRestriction

/-!
### Part 2: The Restriction of the Quotient Map

The quotient map `R -> R/I` when restricted to S gives a ring homomorphism
`S -> R/I` whose kernel is exactly S cap I.

This is the key to the Second Isomorphism Theorem: by the First Isomorphism
Theorem, S/(S cap I) is isomorphic to the image of S in R/I.
-/

/--
The restriction of the quotient map to the subring S.
This is a ring homomorphism from S to R/I.
-/
def quotientMapRestrict (S : Subring R) (I : Ideal R) : S →+* R ⧸ I :=
  (Ideal.Quotient.mk I).comp S.subtype

/--
The kernel of the restricted quotient map is S cap I.
-/
theorem ker_quotientMapRestrict (S : Subring R) (I : Ideal R) :
    RingHom.ker (quotientMapRestrict S I) = intersectionIdeal S I := by
  ext x
  simp only [RingHom.mem_ker, quotientMapRestrict, RingHom.coe_comp, Function.comp_apply,
    Ideal.Quotient.eq_zero_iff_mem, intersectionIdeal, Ideal.mem_comap]

/--
An element maps to zero in the quotient iff it is in the intersection.
-/
theorem quotientMapRestrict_eq_zero_iff (S : Subring R) (I : Ideal R) (x : S) :
    quotientMapRestrict S I x = 0 ↔ (x : R) ∈ I := by
  simp only [quotientMapRestrict, RingHom.coe_comp, Function.comp_apply,
    Ideal.Quotient.eq_zero_iff_mem, Subring.coe_subtype]

/--
The restricted quotient map is the composition of inclusion and projection.
-/
theorem quotientMapRestrict_apply (S : Subring R) (I : Ideal R) (x : S) :
    quotientMapRestrict S I x = Ideal.Quotient.mk I x := rfl

end QuotientMapRestriction

-- ============================================================================
-- Section 3: The Main Isomorphism (Second Isomorphism Theorem)
-- ============================================================================

section MainIsomorphism

/-!
### Part 3: The Second Isomorphism Theorem

This is the heart of the theorem. We prove that S/(S cap I) iso range(f),
where f : S -> R/I is the restricted quotient map.

By the First Isomorphism Theorem:
- The kernel of f is S cap I
- Therefore S/ker(f) = S/(S cap I) is isomorphic to the range of f

The range of f consists of all cosets [s] for s in S.
-/

/--
**The Second Isomorphism Theorem**

For a commutative ring R with subring S and ideal I:
  S/(S cap I) iso range(quotientMapRestrict S I)

Where:
- S cap I is represented by `I.comap S.subtype` as an ideal of S
- The range is the image of S in R/I under the quotient map

The isomorphism is induced by the restricted quotient map S -> R/I.
By the First Isomorphism Theorem, S/ker(f) iso range(f).
-/
noncomputable def secondIsomorphismTheorem (S : Subring R) (I : Ideal R) :
    S ⧸ intersectionIdeal S I ≃+* (quotientMapRestrict S I).range := by
  -- Apply the First Isomorphism Theorem for the restricted quotient map
  have h : RingHom.ker (quotientMapRestrict S I) = intersectionIdeal S I :=
    ker_quotientMapRestrict S I
  exact (Ideal.quotEquivOfEq h.symm).trans (RingHom.quotientKerEquivRange (quotientMapRestrict S I))

/--
The second isomorphism theorem gives a bijection.
-/
theorem second_iso_bijective (S : Subring R) (I : Ideal R) :
    Function.Bijective (secondIsomorphismTheorem S I) :=
  (secondIsomorphismTheorem S I).bijective

/--
The range of the restricted quotient map consists of cosets [s] for s in S.
-/
theorem range_quotientMapRestrict (S : Subring R) (I : Ideal R) :
    ∀ x ∈ (quotientMapRestrict S I).range, ∃ s : S, quotientMapRestrict S I s = x := by
  intro x hx
  exact hx

/--
Every element of S maps to an element in the range.
-/
theorem mem_range_of_subring (S : Subring R) (I : Ideal R) (s : S) :
    quotientMapRestrict S I s ∈ (quotientMapRestrict S I).range := by
  exact RingHom.mem_range_self (quotientMapRestrict S I) s

end MainIsomorphism

-- ============================================================================
-- Section 4: The Inverse Isomorphism
-- ============================================================================

section InverseIsomorphism

/-!
### Part 4: The Inverse of the Second Isomorphism

The inverse isomorphism range(f) -> S/(S cap I) is also important.
Given an element [s] in the range (where s in S), we map it to the coset [s] in S/(S cap I).
-/

/--
The inverse of the second isomorphism theorem.
Maps range(quotientMapRestrict) -> S/(S cap I).
-/
noncomputable def second_iso_inverse (S : Subring R) (I : Ideal R) :
    (quotientMapRestrict S I).range ≃+* S ⧸ intersectionIdeal S I :=
  (secondIsomorphismTheorem S I).symm

/--
Composing the isomorphism with its inverse gives the identity.
-/
theorem second_iso_left_inv (S : Subring R) (I : Ideal R)
    (x : S ⧸ intersectionIdeal S I) :
    (second_iso_inverse S I) ((secondIsomorphismTheorem S I) x) = x :=
  (secondIsomorphismTheorem S I).symm_apply_apply x

/--
Composing the inverse with the isomorphism gives the identity.
-/
theorem second_iso_right_inv (S : Subring R) (I : Ideal R)
    (y : (quotientMapRestrict S I).range) :
    (secondIsomorphismTheorem S I) ((second_iso_inverse S I) y) = y :=
  (secondIsomorphismTheorem S I).apply_symm_apply y

end InverseIsomorphism

-- ============================================================================
-- Section 5: Properties of the Isomorphism
-- ============================================================================

section IsomorphismProperties

/-!
### Part 5: Properties of the Second Isomorphism

The isomorphism from the Second Isomorphism Theorem preserves all ring structure.
-/

/--
The isomorphism preserves addition.
-/
theorem second_iso_preserves_add (S : Subring R) (I : Ideal R)
    (a b : S ⧸ intersectionIdeal S I) :
    (secondIsomorphismTheorem S I) (a + b) =
    (secondIsomorphismTheorem S I) a + (secondIsomorphismTheorem S I) b :=
  (secondIsomorphismTheorem S I).map_add a b

/--
The isomorphism preserves multiplication.
-/
theorem second_iso_preserves_mul (S : Subring R) (I : Ideal R)
    (a b : S ⧸ intersectionIdeal S I) :
    (secondIsomorphismTheorem S I) (a * b) =
    (secondIsomorphismTheorem S I) a * (secondIsomorphismTheorem S I) b :=
  (secondIsomorphismTheorem S I).map_mul a b

/--
The isomorphism preserves the multiplicative identity.
-/
theorem second_iso_preserves_one (S : Subring R) (I : Ideal R) :
    (secondIsomorphismTheorem S I) 1 = 1 :=
  (secondIsomorphismTheorem S I).map_one

/--
The isomorphism preserves the additive identity.
-/
theorem second_iso_preserves_zero (S : Subring R) (I : Ideal R) :
    (secondIsomorphismTheorem S I) 0 = 0 :=
  (secondIsomorphismTheorem S I).map_zero

end IsomorphismProperties

-- ============================================================================
-- Section 6: Index Formula
-- ============================================================================

section IndexFormula

/-!
### Part 6: Index Formula

For finite quotients, the second isomorphism theorem implies an equality
of cardinalities.
-/

/--
For finite quotients, the cardinalities are equal.
-/
theorem index_formula (S : Subring R) (I : Ideal R)
    [Fintype (S ⧸ intersectionIdeal S I)]
    [Fintype (quotientMapRestrict S I).range] :
    Fintype.card (S ⧸ intersectionIdeal S I) =
    Fintype.card (quotientMapRestrict S I).range :=
  Fintype.card_eq.mpr ⟨(secondIsomorphismTheorem S I).toEquiv⟩

end IndexFormula

-- ============================================================================
-- Section 7: Summary and Diagram
-- ============================================================================

/-!
## Summary

We have formalized the Second Isomorphism Theorem for Rings, which states:

For a commutative ring R with subring S and ideal I:

```
                    R
                   / \
                 /     \
               S+I       ...
              /   \
             /     \
            S       I
             \     /
              \   /
              S cap I
```

**The Second Isomorphism Theorem**:
```
    S/(S cap I)  iso  range(S -> R/I)

       [s]    |->    [s]
```

Where:
- The left quotient mods S by S cap I
- The right side is the image of S in R/I under the quotient map
- The isomorphism is induced by the restricted quotient map

**Key Results**:
1. `intersection_is_ideal_of_subring`: S cap I is an ideal of S
2. `ker_quotientMapRestrict`: The kernel of S -> R/I is S cap I
3. `secondIsomorphismTheorem`: S/(S cap I) iso range(S -> R/I)

**Mathematical Interpretation**:
The theorem says that modding out a subring by its intersection with an ideal
is the same as looking at the image of that subring in the quotient ring.

All proofs leverage Mathlib's infrastructure for ideals, subrings, quotient rings,
and the First Isomorphism Theorem.
-/

end RingSecondIsomorphism
