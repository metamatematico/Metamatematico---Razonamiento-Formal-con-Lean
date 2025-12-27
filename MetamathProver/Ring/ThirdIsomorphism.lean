/-
Copyright (c) 2024. All rights reserved.
Released under Apache 2.0 license.

# The Third Isomorphism Theorem for Rings

This file formalizes the Third Isomorphism Theorem for Rings in Lean 4 using Mathlib.

## Mathematical Background

Let R be a ring, and I an ideal of R. Then:
1. If A is a subring of R such that I <= A <= R, then A/I is a subring of R/I
2. Every subring of R/I is of the form A/I for some subring A with I <= A
3. If J is an ideal of R such that I <= J <= R, then J/I is an ideal of R/I
4. Every ideal of R/I is of the form J/I for some ideal J with I <= J
5. **Main theorem**: If J is an ideal with I <= J, then **(R/I)/(J/I) iso R/J**

The main theorem (part 5) is the Third Isomorphism Theorem proper. Parts 1-4 are
properties of the correspondence between ideals/subrings in R containing I and
ideals/subrings in R/I.

### Intuition

"Factoring out twice is the same as factoring out once by the larger ideal."

If we first mod out by I (the smaller ideal) and then by J/I, we get the same
result as modding out by J directly.

## Main Results

- `ideal_maps_to_ideal`: If I <= J, then J.map (mk I) is an ideal of R/I
- `ideal_of_quotient_from_ideal`: Every ideal of R/I is J.map (mk I) for some J >= I
- `thirdIsomorphismTheorem`: (R/I)/(J/I) iso R/J for ideals I <= J

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
- `Ideal.map f J` : Image of ideal J under homomorphism f
- `Ideal.comap f J` : Preimage of ideal J under homomorphism f
-/

namespace RingThirdIsomorphism

variable {R : Type*} [CommRing R]

-- ============================================================================
-- Section 1: The Quotient Map and Its Properties
-- ============================================================================

section QuotientMapProperties

/-!
### The Quotient Map

The quotient map `mk I : R ->+* R/I` is the canonical surjective homomorphism.
Its key properties are essential for understanding the correspondence and
isomorphism theorems.
-/

/--
The quotient map `R ->+* R/I` is surjective.
-/
theorem mk_surjective (I : Ideal R) :
    Function.Surjective (Ideal.Quotient.mk I) :=
  Ideal.Quotient.mk_surjective

/--
The kernel of the quotient map is exactly I.
-/
theorem ker_mk_eq (I : Ideal R) :
    RingHom.ker (Ideal.Quotient.mk I) = I :=
  Ideal.mk_ker

/--
An element maps to 0 in the quotient iff it is in I.
-/
theorem mk_eq_zero_iff (I : Ideal R) (r : R) :
    Ideal.Quotient.mk I r = 0 ↔ r ∈ I :=
  Ideal.Quotient.eq_zero_iff_mem

end QuotientMapProperties

-- ============================================================================
-- Section 2: Correspondence Part 1 - Ideals Containing I Map to Ideals
-- ============================================================================

section CorrespondencePart1

/-!
### Part 1: If J is an ideal with I <= J, then J/I is an ideal of R/I

When I is an ideal of R and J is an ideal containing I, the image of J under
the quotient map is an ideal of R/I, denoted J/I.

In Mathlib, this is `Ideal.map (Ideal.Quotient.mk I) J`.
-/

/--
**Correspondence Part 1**: For ideals I <= J of R, the image J/I = J.map (mk I)
is an ideal of R/I.

This is automatic since `Ideal.map` always produces an ideal.
-/
theorem ideal_maps_to_ideal (I J : Ideal R) (_hIJ : I ≤ J) :
    ∃ K : Ideal (R ⧸ I), K = Ideal.map (Ideal.Quotient.mk I) J :=
  ⟨Ideal.map (Ideal.Quotient.mk I) J, rfl⟩

/--
The ideal J/I is the image of J under the quotient map.
-/
def quotientIdeal (I J : Ideal R) : Ideal (R ⧸ I) :=
  Ideal.map (Ideal.Quotient.mk I) J

/--
An element is in J/I iff it has a representative in J.
-/
theorem mem_quotientIdeal_iff (I J : Ideal R) (x : R ⧸ I) :
    x ∈ quotientIdeal I J ↔ ∃ j : R, j ∈ J ∧ Ideal.Quotient.mk I j = x := by
  simp only [quotientIdeal, Ideal.mem_map_iff_of_surjective _ (mk_surjective I)]

/--
The coset of j is in J/I for any j in J.
-/
theorem mk_mem_quotientIdeal (I J : Ideal R) (j : R) (hj : j ∈ J) :
    Ideal.Quotient.mk I j ∈ quotientIdeal I J := by
  simp only [quotientIdeal, Ideal.mem_map_iff_of_surjective _ (mk_surjective I)]
  exact ⟨j, hj, rfl⟩

/--
When I <= J, the quotient ideal J/I contains the zero ideal of R/I.
-/
theorem bot_le_quotientIdeal (I J : Ideal R) (_hIJ : I ≤ J) :
    ⊥ ≤ quotientIdeal I J := by
  intro x hx
  simp only [Ideal.mem_bot] at hx
  rw [hx]
  exact Ideal.zero_mem _

end CorrespondencePart1

-- ============================================================================
-- Section 3: Correspondence Part 2 - Every Ideal of R/I Comes from Some J
-- ============================================================================

section CorrespondencePart2

/-!
### Part 2: Every ideal of R/I is of the form J/I for some J >= I

The preimage of any ideal K of R/I under the quotient map is an ideal J of R
that contains I, and the image of J is exactly K.
-/

/--
The preimage of an ideal of R/I under mk contains I.
-/
theorem I_le_comap_mk (I : Ideal R) (K : Ideal (R ⧸ I)) :
    I ≤ Ideal.comap (Ideal.Quotient.mk I) K := by
  intro r hr
  simp only [Ideal.mem_comap]
  rw [Ideal.Quotient.eq_zero_iff_mem.mpr hr]
  exact K.zero_mem

/--
**Correspondence Part 2**: Every ideal of R/I is of the form J/I
for some ideal J of R with I <= J.
-/
theorem ideal_of_quotient_from_ideal (I : Ideal R) (K : Ideal (R ⧸ I)) :
    ∃ J : Ideal R, I ≤ J ∧ Ideal.map (Ideal.Quotient.mk I) J = K := by
  use Ideal.comap (Ideal.Quotient.mk I) K
  constructor
  · exact I_le_comap_mk I K
  · exact Ideal.map_comap_of_surjective _ (mk_surjective I) K

/--
The preimage J and image K correspond bijectively.
-/
theorem comap_map_eq_self (I : Ideal R) (K : Ideal (R ⧸ I)) :
    Ideal.map (Ideal.Quotient.mk I) (Ideal.comap (Ideal.Quotient.mk I) K) = K :=
  Ideal.map_comap_of_surjective _ (mk_surjective I) K

/--
For ideals J containing I, map then comap gives J + I = J (since I <= J).
-/
theorem map_comap_eq_self_of_le (I J : Ideal R) (hIJ : I ≤ J) :
    Ideal.comap (Ideal.Quotient.mk I) (Ideal.map (Ideal.Quotient.mk I) J) = J := by
  have h : Ideal.comap (Ideal.Quotient.mk I) ⊥ = I := by
    ext x
    simp only [Ideal.mem_comap, Ideal.mem_bot, Ideal.Quotient.eq_zero_iff_mem]
  rw [Ideal.comap_map_of_surjective _ (mk_surjective I), h]
  rw [sup_comm]
  exact sup_eq_right.mpr hIJ

end CorrespondencePart2

-- ============================================================================
-- Section 4: Correspondence Preserves Inclusion
-- ============================================================================

section CorrespondencePreservesOrder

/-!
### The Correspondence Preserves Order

The correspondence between ideals of R/I and ideals of R containing I
preserves inclusion: J1 <= J2 iff J1/I <= J2/I.
-/

/--
The correspondence preserves order (forward direction).
If J1 <= J2, then J1/I <= J2/I.
-/
theorem quotientIdeal_mono (I : Ideal R) {J1 J2 : Ideal R}
    (h : J1 ≤ J2) : quotientIdeal I J1 ≤ quotientIdeal I J2 :=
  Ideal.map_mono h

/--
The correspondence preserves order (backward direction via comap).
If K1 <= K2 in R/I, then comap K1 <= comap K2 in R.
-/
theorem comap_mono (I : Ideal R) {K1 K2 : Ideal (R ⧸ I)}
    (h : K1 ≤ K2) : Ideal.comap (Ideal.Quotient.mk I) K1 ≤ Ideal.comap (Ideal.Quotient.mk I) K2 :=
  Ideal.comap_mono h

end CorrespondencePreservesOrder

-- ============================================================================
-- Section 5: The Third Isomorphism Theorem
-- ============================================================================

section ThirdIsomorphism

/-!
### The Third Isomorphism Theorem

This is the main theorem: if I <= J are ideals of R, then
(R/I)/(J/I) iso R/J.

The key insight is that J/I (the image of J under mk I) is an ideal of R/I,
so we can form the double quotient (R/I)/(J/I).

The isomorphism sends the coset (r + I) + (J/I) to the coset r + J.
-/

variable (I J : Ideal R) (h : I ≤ J)

/--
The image of J under the quotient map G -> G/I is an ideal of R/I.
This is needed to form the double quotient.
-/
theorem J_mod_I_is_ideal :
    ∃ K : Ideal (R ⧸ I), K = Ideal.map (Ideal.Quotient.mk I) J :=
  ⟨Ideal.map (Ideal.Quotient.mk I) J, rfl⟩

/--
**The Third Isomorphism Theorem**

For ideals I <= J of R:
  (R/I)/(J/I) iso R/J

where J/I = Ideal.map (Ideal.Quotient.mk I) J.

This shows that "factoring out twice" (first by I, then by J/I) is the same
as "factoring out once" (by J).

In Mathlib, this is `DoubleQuot.quotQuotEquivQuotOfLE`.
-/
noncomputable def thirdIsomorphismTheorem :
    (R ⧸ I) ⧸ Ideal.map (Ideal.Quotient.mk I) J ≃+* R ⧸ J :=
  DoubleQuot.quotQuotEquivQuotOfLE h

/--
The third isomorphism theorem is a bijection.
-/
theorem third_iso_bijective :
    Function.Bijective (thirdIsomorphismTheorem I J h) :=
  (thirdIsomorphismTheorem I J h).bijective

/--
The isomorphism sends ((r + I) + J/I) to (r + J).
-/
theorem third_iso_apply (r : R) :
    thirdIsomorphismTheorem I J h (DoubleQuot.quotQuotMk I J r) =
    Ideal.Quotient.mk J r :=
  DoubleQuot.quotQuotEquivQuotOfLE_quotQuotMk r h

end ThirdIsomorphism

-- ============================================================================
-- Section 6: The Inverse Isomorphism
-- ============================================================================

section InverseIsomorphism

/-!
### The Inverse of the Third Isomorphism

The inverse map sends (r + J) to ((r + I) + J/I).
-/

variable (I J : Ideal R) (h : I ≤ J)

/--
The inverse of the third isomorphism theorem.
Maps R/J -> (R/I)/(J/I).
-/
noncomputable def third_iso_inverse :
    R ⧸ J ≃+* (R ⧸ I) ⧸ Ideal.map (Ideal.Quotient.mk I) J :=
  (thirdIsomorphismTheorem I J h).symm

/--
Composing the isomorphism with its inverse gives the identity.
-/
theorem third_iso_left_inv
    (x : (R ⧸ I) ⧸ Ideal.map (Ideal.Quotient.mk I) J) :
    (third_iso_inverse I J h) ((thirdIsomorphismTheorem I J h) x) = x :=
  (thirdIsomorphismTheorem I J h).symm_apply_apply x

/--
Composing the inverse with the isomorphism gives the identity.
-/
theorem third_iso_right_inv (y : R ⧸ J) :
    (thirdIsomorphismTheorem I J h) ((third_iso_inverse I J h) y) = y :=
  (thirdIsomorphismTheorem I J h).apply_symm_apply y

/--
The inverse sends (r + J) to ((r + I) + J/I).
-/
theorem third_iso_inverse_apply (r : R) :
    third_iso_inverse I J h (Ideal.Quotient.mk J r) = DoubleQuot.quotQuotMk I J r :=
  DoubleQuot.quotQuotEquivQuotOfLE_symm_mk r h

end InverseIsomorphism

-- ============================================================================
-- Section 7: Order/Index Formula
-- ============================================================================

section OrderFormula

/-!
### Order and Index Formulas

For finite quotients, the third isomorphism theorem implies:
  |R/J| = |(R/I)/(J/I)|
-/

variable (I J : Ideal R)

/--
For finite quotients, the cardinalities are equal.
-/
theorem order_formula (h : I ≤ J)
    [Fintype (R ⧸ J)]
    [Fintype ((R ⧸ I) ⧸ Ideal.map (Ideal.Quotient.mk I) J)] :
    Fintype.card ((R ⧸ I) ⧸ Ideal.map (Ideal.Quotient.mk I) J) =
    Fintype.card (R ⧸ J) :=
  Fintype.card_eq.mpr ⟨(thirdIsomorphismTheorem I J h).toEquiv⟩

end OrderFormula

-- ============================================================================
-- Section 8: Composition of Quotient Maps
-- ============================================================================

section CompositionOfQuotients

/-!
### Composition of Quotient Maps

The third isomorphism theorem can also be understood through the composition
of quotient maps. The map R -> R/J factors as R -> R/I -> (R/I)/(J/I) -> R/J.
-/

variable (I J : Ideal R)

/--
The composition of the two quotient maps.
-/
def double_quotient_map :
    R →+* (R ⧸ I) ⧸ Ideal.map (Ideal.Quotient.mk I) J :=
  DoubleQuot.quotQuotMk I J

/--
The double quotient map is surjective.
-/
theorem double_quotient_map_surjective :
    Function.Surjective (double_quotient_map I J) := by
  unfold double_quotient_map DoubleQuot.quotQuotMk
  exact (Ideal.Quotient.mk_surjective).comp (Ideal.Quotient.mk_surjective)

/--
The kernel of the double quotient map is I + J = J when I <= J.
This follows from the third isomorphism theorem.
-/
theorem double_quotient_map_ker (h : I ≤ J) :
    RingHom.ker (double_quotient_map I J) = J := by
  rw [double_quotient_map, DoubleQuot.ker_quotQuotMk, sup_eq_right.mpr h]

end CompositionOfQuotients

-- ============================================================================
-- Section 9: Summary and Diagram
-- ============================================================================

/-!
## Summary

We have formalized the Third Isomorphism Theorem for Rings.

### The Correspondence Properties

For an ideal I of R, there is a bijection between:
- Ideals of R/I
- Ideals of R containing I

The bijection is given by:
- Forward: K |-> comap (mk I) K (preimage)
- Backward: J |-> map (mk I) J (image, i.e., J/I)

Key properties:
1. J |-> J/I is well-defined for ideals J >= I (`ideal_maps_to_ideal`)
2. Every ideal of R/I is some J/I (`ideal_of_quotient_from_ideal`)
3. The correspondence preserves inclusion (`quotientIdeal_mono`, `comap_mono`)

### The Third Isomorphism Theorem

For ideals I <= J of R:

```
        R
       / \
      /   \
    R/I   R/J
     |     ^
     v     |
  (R/I)/(J/I) iso R/J
```

The diagram commutes: the quotient map R -> R/J factors through
R -> R/I -> (R/I)/(J/I) followed by the isomorphism.

**Intuition**: "Factoring out twice is the same as factoring out once."
If we first mod out by I (the smaller ideal) and then by J/I,
we get the same result as modding out by J directly.

### Main Definition

- `thirdIsomorphismTheorem`: (R/I)/(J/I) iso R/J
  (Mathlib: `DoubleQuot.quotQuotEquivQuotOfLE`)

All proofs leverage Mathlib's `DoubleQuot` module and quotient ring infrastructure.
-/

end RingThirdIsomorphism
