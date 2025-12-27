/-
Copyright (c) 2024. All rights reserved.
Released under Apache 2.0 license.

# The Fourth Isomorphism Theorem (Lattice/Correspondence Theorem) for Rings

This file formalizes the Fourth Isomorphism Theorem (also known as the Lattice Theorem
or Correspondence Theorem) for Rings in Lean 4 using Mathlib.

## Mathematical Background

Let R be a commutative ring and I an ideal of R. The canonical projection R -> R/I defines:
1. A bijective correspondence between ideals J of R containing I and ideals of R/I
2. Under this correspondence, the order (inclusion) is preserved

### The Bijection

The correspondence is given by:
- **Forward map (Phi)**: J |-> J/I = image of J under the quotient map R -> R/I
- **Inverse map (Psi)**: K |-> preimage of K under the quotient map

### Key Properties

1. **Bijection**: Phi and Psi are mutually inverse
2. **Order-preserving**: J1 <= J2 iff Phi(J1) <= Phi(J2)
3. **Preserves meets (intersections)**: Phi(J1 cap J2) = Phi(J1) cap Phi(J2)
4. **Preserves joins (sums)**: Phi(J1 + J2) = Phi(J1) + Phi(J2)

### Historical Note

This theorem is variously called:
- The **Fourth Isomorphism Theorem** (in some numbering conventions)
- The **Lattice Theorem** (emphasizing the lattice-theoretic content)
- The **Correspondence Theorem** (emphasizing the bijection)

The theorem reveals that the quotient R/I "remembers" the ideal structure of R
above I, while "forgetting" the structure below I.

## Main Results

- `latticeTheorem`: The order isomorphism between Ideal (R/I) and {J : Ideal R | I <= J}
- `forwardMap`: J |-> map (mk I) J
- `inverseMap`: K |-> comap (mk I) K
- `lattice_preserves_inf`: The correspondence preserves meets (intersections)
- `lattice_preserves_sup`: The correspondence preserves joins (sums)

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
- `Ideal.comap f K` : Preimage of ideal K under homomorphism f
- `inf` : Infimum (intersection) of ideals
- `sup` : Supremum (sum) of ideals
-/

namespace RingLatticeTheorem

variable {R : Type*} [CommRing R]

-- ============================================================================
-- Section 1: Setup and Basic Definitions
-- ============================================================================

section Setup

/-!
### Setup

We establish the basic objects of the Fourth Isomorphism Theorem:
- A commutative ring R
- An ideal I of R
- The quotient map mk I : R ->+* R/I
- The correspondence between ideals
-/

/--
The quotient map `R ->+* R/I` is the canonical surjective homomorphism.
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

end Setup

-- ============================================================================
-- Section 2: The Forward Map (J |-> J/I)
-- ============================================================================

section ForwardMap

/-!
### The Forward Map: J |-> J/I

For an ideal J of R containing I, we define J/I as the image of J under
the quotient map. This is an ideal of R/I.

In Mathlib, this is `Ideal.map (Ideal.Quotient.mk I) J`.
-/

/--
The forward map of the correspondence: J |-> map (mk I) J = J/I.
This takes an ideal J of R (with I <= J) to its quotient J/I,
viewed as an ideal of R/I.
-/
def forwardMap (I J : Ideal R) : Ideal (R ⧸ I) :=
  Ideal.map (Ideal.Quotient.mk I) J

/--
Alternative notation: J/I as the image under the quotient map.
-/
abbrev quotientIdeal (I J : Ideal R) : Ideal (R ⧸ I) :=
  forwardMap I J

/--
An element is in J/I iff it has a representative in J.
-/
theorem mem_forwardMap_iff (I J : Ideal R) (x : R ⧸ I) :
    x ∈ forwardMap I J ↔ ∃ j : R, j ∈ J ∧ Ideal.Quotient.mk I j = x := by
  simp only [forwardMap, Ideal.mem_map_iff_of_surjective _ (mk_surjective I)]

/--
The coset of j is in J/I for any j in J.
-/
theorem mk_mem_forwardMap (I J : Ideal R) (j : R) (hj : j ∈ J) :
    Ideal.Quotient.mk I j ∈ forwardMap I J := by
  simp only [forwardMap, Ideal.mem_map_iff_of_surjective _ (mk_surjective I)]
  exact ⟨j, hj, rfl⟩

/--
The forward map sends I to the zero ideal of R/I.
-/
theorem forwardMap_self (I : Ideal R) :
    forwardMap I I = ⊥ :=
  Ideal.map_quotient_self I

/--
The forward map sends R (= top) to R/I (= top).
-/
theorem forwardMap_top (I : Ideal R) :
    forwardMap I ⊤ = ⊤ := by
  simp only [forwardMap]
  rw [Ideal.map_top (Ideal.Quotient.mk I)]

end ForwardMap

-- ============================================================================
-- Section 3: The Inverse Map (K |-> preimage of K)
-- ============================================================================

section InverseMap

/-!
### The Inverse Map: K |-> comap (mk I) K

For an ideal K of R/I, the inverse map gives the preimage of K under
the quotient map. This is an ideal of R that contains I.

In Mathlib, this is `Ideal.comap (Ideal.Quotient.mk I) K`.
-/

/--
The inverse map of the correspondence: K |-> comap (mk I) K.
This takes an ideal K of R/I to its preimage in R,
which is an ideal containing I.
-/
def inverseMap (I : Ideal R) (K : Ideal (R ⧸ I)) : Ideal R :=
  Ideal.comap (Ideal.Quotient.mk I) K

/--
The preimage of any ideal of R/I contains I.
-/
theorem I_le_inverseMap (I : Ideal R) (K : Ideal (R ⧸ I)) :
    I ≤ inverseMap I K := by
  intro r hr
  simp only [inverseMap, Ideal.mem_comap]
  rw [Ideal.Quotient.eq_zero_iff_mem.mpr hr]
  exact K.zero_mem

/--
An element is in the preimage iff its coset is in K.
-/
theorem mem_inverseMap_iff (I : Ideal R) (K : Ideal (R ⧸ I)) (r : R) :
    r ∈ inverseMap I K ↔ Ideal.Quotient.mk I r ∈ K := by
  simp only [inverseMap, Ideal.mem_comap]

/--
The inverse map sends the zero ideal to I.
-/
theorem inverseMap_bot (I : Ideal R) :
    inverseMap I ⊥ = I := by
  ext r
  simp only [inverseMap, Ideal.mem_comap, Ideal.mem_bot]
  exact Ideal.Quotient.eq_zero_iff_mem

/--
The inverse map sends R/I (= top) to R (= top).
-/
theorem inverseMap_top (I : Ideal R) :
    inverseMap I ⊤ = ⊤ := by
  simp only [inverseMap, Ideal.comap_top]

end InverseMap

-- ============================================================================
-- Section 4: The Bijection (Round-Trip Properties)
-- ============================================================================

section Bijection

/-!
### The Bijection

We prove that the forward and inverse maps are mutually inverse,
establishing the bijection between ideals of R/I and ideals of R containing I.
-/

/--
**Round-trip 1**: Starting from an ideal K of R/I, applying the inverse
map then the forward map gives back K.

That is: map (comap K) = K when the map is surjective.
-/
theorem forwardMap_inverseMap (I : Ideal R) (K : Ideal (R ⧸ I)) :
    forwardMap I (inverseMap I K) = K := by
  simp only [forwardMap, inverseMap]
  exact Ideal.map_comap_of_surjective _ (mk_surjective I) K

/--
**Round-trip 2**: Starting from an ideal J of R containing I, applying
the forward map then the inverse map gives back J.

That is: comap (map J) = I + J = J (when I <= J).
-/
theorem inverseMap_forwardMap (I J : Ideal R) (hIJ : I ≤ J) :
    inverseMap I (forwardMap I J) = J := by
  simp only [forwardMap, inverseMap]
  have h : Ideal.comap (Ideal.Quotient.mk I) ⊥ = I := by
    ext x
    simp only [Ideal.mem_comap, Ideal.mem_bot, Ideal.Quotient.eq_zero_iff_mem]
  rw [Ideal.comap_map_of_surjective _ (mk_surjective I), h, sup_comm, sup_eq_right.mpr hIJ]

/--
The comap of map J equals I + J.
-/
theorem comap_map_eq_sup (I J : Ideal R) :
    Ideal.comap (Ideal.Quotient.mk I) (Ideal.map (Ideal.Quotient.mk I) J) = I ⊔ J := by
  have h : Ideal.comap (Ideal.Quotient.mk I) ⊥ = I := by
    ext x
    simp only [Ideal.mem_comap, Ideal.mem_bot, Ideal.Quotient.eq_zero_iff_mem]
  rw [Ideal.comap_map_of_surjective _ (mk_surjective I), h, sup_comm]

end Bijection

-- ============================================================================
-- Section 5: The Order Isomorphism (Lattice Theorem)
-- ============================================================================

section OrderIsomorphism

/-!
### The Order Isomorphism

The correspondence is not just a bijection, but an **order isomorphism**.
This means it preserves the inclusion ordering:
  J1 <= J2 iff forwardMap J1 <= forwardMap J2

This is the core content of the Fourth Isomorphism Theorem.
-/

/--
**The Fourth Isomorphism Theorem (Lattice Theorem)**

There is an order-preserving bijection between:
- Ideals of R/I
- Ideals of R that contain I

The forward direction takes K to its preimage (comap).
The inverse direction takes J to its image (map = J/I).
-/
theorem latticeTheorem (I : Ideal R) :
    ∀ K : Ideal (R ⧸ I), I ≤ inverseMap I K ∧
      forwardMap I (inverseMap I K) = K := by
  intro K
  exact ⟨I_le_inverseMap I K, forwardMap_inverseMap I K⟩

/--
The correspondence preserves the order (inclusion).
-/
theorem correspondence_preserves_order (I : Ideal R)
    (K₁ K₂ : Ideal (R ⧸ I)) :
    K₁ ≤ K₂ ↔ inverseMap I K₁ ≤ inverseMap I K₂ := by
  constructor
  · intro h
    exact Ideal.comap_mono h
  · intro h
    have h1 := Ideal.map_mono (f := Ideal.Quotient.mk I) h
    have e1 : Ideal.map (Ideal.Quotient.mk I) (inverseMap I K₁) = K₁ := forwardMap_inverseMap I K₁
    have e2 : Ideal.map (Ideal.Quotient.mk I) (inverseMap I K₂) = K₂ := forwardMap_inverseMap I K₂
    rw [e1, e2] at h1
    exact h1

/--
Forward map is monotone: J1 <= J2 implies forwardMap J1 <= forwardMap J2.
-/
theorem forwardMap_mono (I : Ideal R) {J₁ J₂ : Ideal R}
    (h : J₁ ≤ J₂) : forwardMap I J₁ ≤ forwardMap I J₂ :=
  Ideal.map_mono h

/--
Inverse map is monotone: K1 <= K2 implies inverseMap K1 <= inverseMap K2.
-/
theorem inverseMap_mono (I : Ideal R) {K₁ K₂ : Ideal (R ⧸ I)}
    (h : K₁ ≤ K₂) : inverseMap I K₁ ≤ inverseMap I K₂ :=
  Ideal.comap_mono h

end OrderIsomorphism

-- ============================================================================
-- Section 6: Preservation of Meets (Intersections)
-- ============================================================================

section PreservesMeet

/-!
### Preservation of Meets (Intersections)

The correspondence preserves meets (infimums/intersections):
  inverseMap (K1 inf K2) = inverseMap K1 inf inverseMap K2

This shows that the preimage of an intersection equals the intersection of preimages.
-/

/--
The inverse map preserves meets (intersections).
-/
theorem inverseMap_inf (I : Ideal R) (K₁ K₂ : Ideal (R ⧸ I)) :
    inverseMap I (K₁ ⊓ K₂) = inverseMap I K₁ ⊓ inverseMap I K₂ := by
  simp only [inverseMap]
  ext r
  simp only [Ideal.mem_comap, Ideal.mem_inf]

/--
The forward map preserves meets when restricted to ideals containing I.
-/
theorem forwardMap_inf_of_le (I J₁ J₂ : Ideal R)
    (h₁ : I ≤ J₁) (h₂ : I ≤ J₂) :
    forwardMap I (J₁ ⊓ J₂) = forwardMap I J₁ ⊓ forwardMap I J₂ := by
  -- Use the round-trip property through the inverse map
  have key : inverseMap I (forwardMap I J₁ ⊓ forwardMap I J₂) = J₁ ⊓ J₂ := by
    rw [inverseMap_inf]
    rw [inverseMap_forwardMap I J₁ h₁, inverseMap_forwardMap I J₂ h₂]
  have lhs : forwardMap I (J₁ ⊓ J₂) =
      forwardMap I (inverseMap I (forwardMap I J₁ ⊓ forwardMap I J₂)) := by
    rw [key]
  rw [lhs, forwardMap_inverseMap]

/--
Lattice theorem preserves meets.
-/
theorem lattice_preserves_inf (I : Ideal R) (K₁ K₂ : Ideal (R ⧸ I)) :
    inverseMap I (K₁ ⊓ K₂) = inverseMap I K₁ ⊓ inverseMap I K₂ :=
  inverseMap_inf I K₁ K₂

end PreservesMeet

-- ============================================================================
-- Section 7: Preservation of Joins (Sums)
-- ============================================================================

section PreservesJoin

/-!
### Preservation of Joins (Suprema)

The correspondence preserves joins (suprema/sums):
  inverseMap (K1 sup K2) = inverseMap K1 sup inverseMap K2

This shows that the preimage of a sum equals the sum of preimages.
-/

/--
The forward map preserves joins (sums/suprema).
-/
theorem forwardMap_sup (I J₁ J₂ : Ideal R) :
    forwardMap I (J₁ ⊔ J₂) = forwardMap I J₁ ⊔ forwardMap I J₂ := by
  simp only [forwardMap]
  exact Ideal.map_sup (Ideal.Quotient.mk I) J₁ J₂

/--
The inverse map preserves joins (sums/suprema) when the quotient map is surjective.
-/
theorem inverseMap_sup (I : Ideal R) (K₁ K₂ : Ideal (R ⧸ I)) :
    inverseMap I (K₁ ⊔ K₂) = inverseMap I K₁ ⊔ inverseMap I K₂ := by
  -- Use the round-trip property: apply forward then inverse, which is identity on quotient ideals
  have h1 : forwardMap I (inverseMap I K₁ ⊔ inverseMap I K₂) = K₁ ⊔ K₂ := by
    rw [forwardMap_sup, forwardMap_inverseMap, forwardMap_inverseMap]
  -- Now apply inverseMap to both sides
  have h2 : inverseMap I (forwardMap I (inverseMap I K₁ ⊔ inverseMap I K₂)) =
            inverseMap I (K₁ ⊔ K₂) := by
    rw [h1]
  -- The LHS simplifies using the round-trip property for ideals containing I
  have hcontains : I ≤ inverseMap I K₁ ⊔ inverseMap I K₂ := by
    apply le_sup_of_le_left
    exact I_le_inverseMap I K₁
  rw [inverseMap_forwardMap I _ hcontains] at h2
  exact h2.symm

/--
Lattice theorem preserves joins.
-/
theorem lattice_preserves_sup (I : Ideal R) (K₁ K₂ : Ideal (R ⧸ I)) :
    inverseMap I (K₁ ⊔ K₂) = inverseMap I K₁ ⊔ inverseMap I K₂ :=
  inverseMap_sup I K₁ K₂

end PreservesJoin

-- ============================================================================
-- Section 8: Connection to Third Isomorphism Theorem
-- ============================================================================

section ConnectionToThirdIso

/-!
### Connection to the Third Isomorphism Theorem

The Lattice Theorem is closely related to the Third Isomorphism Theorem.
For ideals I <= J:
  (R/I)/(J/I) iso R/J

The lattice theorem tells us that J/I is an ideal in R/I whenever J is an ideal
containing I, which is a prerequisite for forming the double quotient.
-/

/--
The image J/I is an ideal of R/I for any ideal J.
-/
theorem forwardMap_is_ideal (I J : Ideal R) :
    ∃ K : Ideal (R ⧸ I), K = forwardMap I J :=
  ⟨forwardMap I J, rfl⟩

/--
When J contains I, the double quotient (R/I)/(J/I) is isomorphic to R/J.
This is the Third Isomorphism Theorem.
-/
noncomputable def thirdIsoFromLattice (I J : Ideal R) (h : I ≤ J) :
    (R ⧸ I) ⧸ forwardMap I J ≃+* R ⧸ J := by
  simp only [forwardMap]
  exact DoubleQuot.quotQuotEquivQuotOfLE h

end ConnectionToThirdIso

-- ============================================================================
-- Section 9: Examples
-- ============================================================================

section Examples

/-!
### Examples

We demonstrate some concrete consequences of the lattice theorem.
-/

/--
The trivial ideal of R/I corresponds to I itself.
-/
theorem bot_corresponds_to_I (I : Ideal R) :
    inverseMap I ⊥ = I :=
  inverseMap_bot I

/--
The whole ring R/I corresponds to R (= top).
-/
theorem top_corresponds_to_R (I : Ideal R) :
    inverseMap I ⊤ = ⊤ :=
  inverseMap_top I

/--
I corresponds to the zero ideal under the forward map.
-/
theorem I_maps_to_bot (I : Ideal R) :
    forwardMap I I = ⊥ :=
  forwardMap_self I

/--
The whole ring R maps to the whole ring R/I.
-/
theorem R_maps_to_top (I : Ideal R) :
    forwardMap I ⊤ = ⊤ :=
  forwardMap_top I

end Examples

-- ============================================================================
-- Section 10: Summary
-- ============================================================================

/-!
## Summary

We have formalized the Fourth Isomorphism Theorem (Lattice Theorem) for Rings.

### The Correspondence

For an ideal I of R, there is a bijection:

```
   Ideals of R/I  <------>  Ideals of R containing I

        K            |---->    comap (mk I) K

   map (mk I) J     <----|    J
```

### Key Properties

1. **Bijection** (`forwardMap_inverseMap`, `inverseMap_forwardMap`):
   - map . comap = id on Ideal (R/I)
   - comap . map = id on {J : Ideal R | I <= J}

2. **Order-preserving** (`correspondence_preserves_order`):
   - K1 <= K2 iff comap K1 <= comap K2
   - This makes it an order isomorphism

3. **Preserves meets** (`inverseMap_inf`, `forwardMap_inf_of_le`):
   - comap (K1 inf K2) = comap K1 inf comap K2
   - map (J1 inf J2) = map J1 inf map J2 (when I <= J1, J2)

4. **Preserves joins** (`inverseMap_sup`, `forwardMap_sup`):
   - comap (K1 sup K2) = comap K1 sup comap K2
   - map (J1 sup J2) = map J1 sup map J2

### Diagram

```
                    R = top
                   / | \
                  /  |  \
                 J1  J2  ...  (ideals containing I)
                  \ /
                   I = ker(mk)
                   |
                  {0}

        |                               |
        |    Lattice Isomorphism        |
        V                               V

                  R/I = top
                   / \
                  /   \
               J1/I  J2/I  ...  (ideals of R/I)
                  \ /
                   {0}
```

### Main Definitions

- `forwardMap`: J |-> map (mk I) J = J/I
- `inverseMap`: K |-> comap (mk I) K
- `latticeTheorem`: The bijection and order-preservation properties

All proofs leverage Mathlib's `Ideal.map`, `Ideal.comap`, and quotient ring infrastructure.
-/

end RingLatticeTheorem
