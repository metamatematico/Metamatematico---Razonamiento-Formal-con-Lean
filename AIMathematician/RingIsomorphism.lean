/-
Copyright (c) 2024. All rights reserved.
Released under Apache 2.0 license.

# The First Isomorphism Theorem for Rings

This file formalizes the First Isomorphism Theorem for Rings in Lean 4 using Mathlib.

## Mathematical Background

The First Isomorphism Theorem for Rings states:

Let R and S be rings, and let phi : R -> S be a ring homomorphism. Then:
1. The kernel of phi is an ideal of R
2. The image of phi is a subring of S
3. The quotient ring R/ker(phi) is isomorphic to the image of phi

In particular, if phi is surjective, then S is isomorphic to R/ker(phi).

## Main Results

- `RingHom.ker` : The kernel of a ring homomorphism is an ideal
- `RingHom.range` : The image/range of a ring homomorphism is a subring
- `RingHom.quotientKerEquivRange` : The first isomorphism theorem (R/ker(f) ≃+* f.range)
- `RingHom.quotientKerEquivOfSurjective` : The surjective case (R/ker(f) ≃+* S)

## References

* [Serge Lang, *Algebra*][lang2002algebra]
* [Michael Artin, *Algebra*][artin2011algebra]
-/

import Mathlib.RingTheory.Ideal.Quotient.Operations
import Mathlib.Algebra.Ring.Subring.Basic
import Mathlib.Data.ZMod.Basic

/-!
## Notation

We use the following notation throughout this file:
- `→+*` : Ring homomorphism (RingHom)
- `≃+*` : Ring isomorphism (RingEquiv)
- `R ⧸ I` : Quotient ring of R by ideal I
-/

-- ============================================================================
-- Section 1: Kernel is an Ideal
-- ============================================================================

section KernelIsIdeal

/-!
### Part 1: The Kernel of a Ring Homomorphism is an Ideal

For a ring homomorphism phi : R -> S, the kernel ker(phi) = {r in R : phi(r) = 0}
is an ideal of R. This is already provided by Mathlib as `RingHom.ker`.
-/

variable {R S : Type*} [CommRing R] [CommRing S]

/--
**Theorem (Kernel is an Ideal)**: For any ring homomorphism f : R →+* S,
the kernel ker(f) is an ideal of R.

In Mathlib, `RingHom.ker f` returns an `Ideal R` directly.
-/
theorem kernel_is_ideal (f : R →+* S) : ∃ I : Ideal R, I = RingHom.ker f := by
  -- The kernel is already defined as an ideal in Mathlib
  exact ⟨RingHom.ker f, rfl⟩

/--
An element is in the kernel if and only if it maps to zero.
This is the characterization of kernel elements.
-/
theorem mem_ker_iff (f : R →+* S) (r : R) : r ∈ RingHom.ker f ↔ f r = 0 :=
  RingHom.mem_ker

/--
The kernel contains zero.
-/
example (f : R →+* S) : (0 : R) ∈ RingHom.ker f := by
  rw [RingHom.mem_ker]
  exact f.map_zero

/--
The kernel is closed under addition.
-/
example (f : R →+* S) {a b : R} (ha : a ∈ RingHom.ker f) (hb : b ∈ RingHom.ker f) :
    a + b ∈ RingHom.ker f := by
  rw [RingHom.mem_ker] at *
  rw [f.map_add, ha, hb, add_zero]

/--
The kernel is closed under multiplication by any ring element (ideal property).
-/
example (f : R →+* S) {a r : R} (ha : a ∈ RingHom.ker f) :
    r * a ∈ RingHom.ker f := by
  rw [RingHom.mem_ker] at *
  rw [f.map_mul, ha, mul_zero]

end KernelIsIdeal

-- ============================================================================
-- Section 2: Image/Range is a Subring
-- ============================================================================

section ImageIsSubring

/-!
### Part 2: The Image of a Ring Homomorphism is a Subring

For a ring homomorphism phi : R -> S, the image (or range) im(phi) = {phi(r) : r in R}
is a subring of S. This is provided by Mathlib as `RingHom.range`.
-/

variable {R S : Type*} [Ring R] [Ring S]

/--
**Theorem (Image is a Subring)**: For any ring homomorphism f : R →+* S,
the range f.range is a subring of S.

In Mathlib, `RingHom.range f` returns a `Subring S` directly.
-/
theorem image_is_subring (f : R →+* S) : ∃ T : Subring S, T = f.range := by
  exact ⟨f.range, rfl⟩

/--
An element is in the range if and only if it is the image of some element in the domain.
-/
theorem mem_range_iff (f : R →+* S) (s : S) : s ∈ f.range ↔ ∃ r : R, f r = s :=
  RingHom.mem_range

/--
The image of 0 is in the range.
-/
example (f : R →+* S) : (0 : S) ∈ f.range := by
  rw [RingHom.mem_range]
  exact ⟨0, f.map_zero⟩

/--
The image of 1 is in the range.
-/
example (f : R →+* S) : (1 : S) ∈ f.range := by
  rw [RingHom.mem_range]
  exact ⟨1, f.map_one⟩

/--
The range is closed under addition.
-/
example (f : R →+* S) {a b : S} (ha : a ∈ f.range) (hb : b ∈ f.range) :
    a + b ∈ f.range := by
  rw [RingHom.mem_range] at *
  obtain ⟨ra, hra⟩ := ha
  obtain ⟨rb, hrb⟩ := hb
  exact ⟨ra + rb, by rw [f.map_add, hra, hrb]⟩

/--
The range is closed under multiplication.
-/
example (f : R →+* S) {a b : S} (ha : a ∈ f.range) (hb : b ∈ f.range) :
    a * b ∈ f.range := by
  rw [RingHom.mem_range] at *
  obtain ⟨ra, hra⟩ := ha
  obtain ⟨rb, hrb⟩ := hb
  exact ⟨ra * rb, by rw [f.map_mul, hra, hrb]⟩

end ImageIsSubring

-- ============================================================================
-- Section 3: The First Isomorphism Theorem
-- ============================================================================

section FirstIsomorphismTheorem

/-!
### Part 3: The First Isomorphism Theorem

This is the heart of the file. We prove that R/ker(f) is isomorphic to f.range.

The key insight is that the induced map R/ker(f) -> S given by
  [r] |-> f(r)
is well-defined (because ker(f) is exactly where f is zero) and injective
(by construction). Its image is exactly f.range, giving us the isomorphism.
-/

variable {R S : Type*} [CommRing R] [CommRing S]

/--
The induced map from the quotient R/ker(f) to S is injective.

This is a key lemma: the map [r] |-> f(r) is well-defined and injective.
-/
theorem quotient_ker_injective (f : R →+* S) :
    Function.Injective (RingHom.kerLift f) :=
  RingHom.kerLift_injective f

/--
**The First Isomorphism Theorem for Rings**

For a ring homomorphism f : R →+* S, we have:
  R / ker(f) ≃+* f.range

This is the definitive statement of the theorem. We use `def` rather than `theorem`
because the result is data (a ring equivalence), not a proposition.
-/
noncomputable def first_isomorphism_theorem (f : R →+* S) :
    (R ⧸ RingHom.ker f) ≃+* f.range :=
  RingHom.quotientKerEquivRange f

/--
The isomorphism maps [r] to f(r).

This shows that the isomorphism behaves as expected on elements.
-/
theorem first_isomorphism_theorem_apply (f : R →+* S) (r : R) :
    (first_isomorphism_theorem f) (Ideal.Quotient.mk (RingHom.ker f) r) = ⟨f r, by
      rw [RingHom.mem_range]
      exact ⟨r, rfl⟩⟩ := by
  rfl

/--
The first isomorphism theorem gives a bijection.
-/
theorem first_isomorphism_theorem_bijective (f : R →+* S) :
    Function.Bijective (first_isomorphism_theorem f) :=
  (first_isomorphism_theorem f).bijective

end FirstIsomorphismTheorem

-- ============================================================================
-- Section 4: The Surjective Case
-- ============================================================================

section SurjectiveCase

/-!
### Part 4: The Surjective Case (Corollary)

When the ring homomorphism f : R -> S is surjective, the image is all of S,
so we get an isomorphism R/ker(f) ≃+* S.

This is the most commonly used form of the theorem in practice.
-/

variable {R S : Type*} [CommRing R] [CommRing S]

/--
**Corollary (Surjective Case)**: If f : R →+* S is surjective, then R / ker(f) ≃+* S.

This is the version of the First Isomorphism Theorem that's most often quoted.
-/
noncomputable def first_isomorphism_theorem_surjective (f : R →+* S)
    (hf : Function.Surjective f) : (R ⧸ RingHom.ker f) ≃+* S :=
  RingHom.quotientKerEquivOfSurjective hf

/--
In the surjective case, the isomorphism maps [r] to f(r).
-/
theorem first_isomorphism_theorem_surjective_apply (f : R →+* S)
    (hf : Function.Surjective f) (r : R) :
    first_isomorphism_theorem_surjective f hf (Ideal.Quotient.mk (RingHom.ker f) r) = f r := by
  rfl

/--
In the surjective case, f(r) = 0 iff r is in the kernel.

This is sometimes called the "factor theorem" for rings.
-/
theorem surjective_kernel_characterization (f : R →+* S) (r : R) :
    f r = 0 ↔ r ∈ RingHom.ker f :=
  (RingHom.mem_ker).symm

end SurjectiveCase

-- ============================================================================
-- Section 5: Concrete Example - Integers modulo n
-- ============================================================================

section IntegerExample

/-!
### Part 5: Concrete Example - Integers mod n

We demonstrate the theorem with a classic example:
  - Let f : Z -> Z/nZ be the canonical projection
  - Then ker(f) = nZ (the multiples of n)
  - The theorem says Z / nZ ≃+* Z/nZ (tautologically, but illustrative)

More interestingly, consider evaluating polynomials at a specific point.
-/

/--
The projection from Z to Z/nZ is surjective.
-/
theorem zmod_projection_surjective (n : Nat) [NeZero n] :
    Function.Surjective (Int.castRingHom (ZMod n)) := by
  intro x
  -- Every element of ZMod n is the image of some integer
  -- We use that every element of ZMod n can be lifted to a natural number
  use x.val
  simp [ZMod.natCast_val, ZMod.cast_id]

/--
Example: Z/3Z has exactly 3 elements: 0, 1, 2.
-/
example : Fintype.card (ZMod 3) = 3 := by
  rfl

/--
In Z/2Z, 1 + 1 = 0 (characteristic 2).
-/
example : (1 : ZMod 2) + 1 = 0 := by
  decide

/--
The kernel of the projection Z -> Z/nZ consists of multiples of n.
This demonstrates the relationship between divisibility and the kernel.
-/
theorem zmod_ker_characterization (n : Nat) [NeZero n] (k : Int) :
    k ∈ RingHom.ker (Int.castRingHom (ZMod n)) ↔ (n : Int) ∣ k := by
  rw [RingHom.mem_ker]
  constructor
  · intro h
    exact CharP.intCast_eq_zero_iff (ZMod n) n k |>.mp h
  · intro h
    exact CharP.intCast_eq_zero_iff (ZMod n) n k |>.mpr h

end IntegerExample

-- ============================================================================
-- Section 6: Properties of the Isomorphism
-- ============================================================================

section IsomorphismProperties

/-!
### Part 6: Properties of the First Isomorphism

The isomorphism from the First Isomorphism Theorem preserves all ring structure.
Here we show some key properties.
-/

variable {R S : Type*} [CommRing R] [CommRing S]

/--
The isomorphism preserves addition.
-/
theorem first_iso_preserves_add (f : R →+* S) (a b : R ⧸ RingHom.ker f) :
    (first_isomorphism_theorem f) (a + b) =
    (first_isomorphism_theorem f) a + (first_isomorphism_theorem f) b :=
  (first_isomorphism_theorem f).map_add a b

/--
The isomorphism preserves multiplication.
-/
theorem first_iso_preserves_mul (f : R →+* S) (a b : R ⧸ RingHom.ker f) :
    (first_isomorphism_theorem f) (a * b) =
    (first_isomorphism_theorem f) a * (first_isomorphism_theorem f) b :=
  (first_isomorphism_theorem f).map_mul a b

/--
The isomorphism preserves the multiplicative identity.
-/
theorem first_iso_preserves_one (f : R →+* S) :
    (first_isomorphism_theorem f) 1 = 1 :=
  (first_isomorphism_theorem f).map_one

/--
The isomorphism preserves the additive identity.
-/
theorem first_iso_preserves_zero (f : R →+* S) :
    (first_isomorphism_theorem f) 0 = 0 :=
  (first_isomorphism_theorem f).map_zero

/--
The isomorphism is bijective.
-/
theorem first_iso_bijective (f : R →+* S) :
    Function.Bijective (first_isomorphism_theorem f) :=
  (first_isomorphism_theorem f).bijective

/--
The inverse of the isomorphism is also a ring isomorphism.
-/
noncomputable def first_iso_inverse (f : R →+* S) :
    f.range ≃+* (R ⧸ RingHom.ker f) :=
  (first_isomorphism_theorem f).symm

end IsomorphismProperties

-- ============================================================================
-- Section 7: Summary and Diagram
-- ============================================================================

/-!
## Summary

We have formalized the First Isomorphism Theorem for Rings, which states:

For a ring homomorphism f : R →+* S:

```
           f
    R  ─────────→  S
    │              ↑
    │π             │ι (inclusion)
    ↓              │
  R/ker(f) ≃──→ range(f)
           φ
```

Where:
- `π` is the quotient map (projection)
- `φ` is the isomorphism from the theorem
- `ι` is the inclusion of the range into S

The key results proven:
1. `kernel_is_ideal`: ker(f) is an ideal of R
2. `image_is_subring`: range(f) is a subring of S
3. `first_isomorphism_theorem`: R/ker(f) ≃+* range(f)
4. `first_isomorphism_theorem_surjective`: When f is surjective, R/ker(f) ≃+* S

All proofs leverage Mathlib's existing infrastructure for ideals, quotient rings,
and ring homomorphisms.
-/

-- ============================================================================
-- Section 8: Additional Applications
-- ============================================================================

section Applications

/-!
### Part 8: Applications

The First Isomorphism Theorem has many applications. Here we show a couple.
-/

variable {R : Type*} [CommRing R]

/--
**Application 1: Quotient by kernel characterizes factorization**

Any ring homomorphism f : R →+* S factors through R/ker(f).
-/
theorem factors_through_quotient {S : Type*} [CommRing S] (f : R →+* S) :
    ∃ (g : R ⧸ RingHom.ker f →+* S),
      (∀ r : R, g (Ideal.Quotient.mk (RingHom.ker f) r) = f r) ∧
      Function.Injective g := by
  refine ⟨RingHom.kerLift f, ?_, RingHom.kerLift_injective f⟩
  intro r
  rfl

/--
**Application 2: Injectivity criterion**

A ring homomorphism is injective if and only if its kernel is trivial.
-/
theorem injective_iff_trivial_kernel {S : Type*} [Ring S] (f : R →+* S) :
    Function.Injective f ↔ RingHom.ker f = ⊥ :=
  RingHom.injective_iff_ker_eq_bot f

/--
**Application 3: Surjectivity and quotient**

If f is surjective, then S is a quotient of R.
-/
theorem surjective_implies_quotient {S : Type*} [CommRing S] (f : R →+* S)
    (hf : Function.Surjective f) :
    Nonempty (R ⧸ RingHom.ker f ≃+* S) := by
  exact ⟨RingHom.quotientKerEquivOfSurjective hf⟩

end Applications

-- ============================================================================
-- Section 9: Related Theorems
-- ============================================================================

section RelatedTheorems

/-!
### Part 9: Related Isomorphism Theorems

For completeness, we mention that Mathlib also contains:
- The Second Isomorphism Theorem (for ideals)
- The Third Isomorphism Theorem (for nested ideals)
- The Chinese Remainder Theorem (for coprime ideals)

These are found in `Mathlib.RingTheory.Ideal.Quotient.Operations`.
-/

variable {R : Type*} [CommRing R]

/--
Reference to the Third Isomorphism Theorem.

For ideals I ⊆ J, we have (R/I)/(J/I) ≃+* R/J.
-/
noncomputable def third_isomorphism_theorem_reference (I J : Ideal R) (h : I ≤ J) :
    ((R ⧸ I) ⧸ J.map (Ideal.Quotient.mk I)) ≃+* R ⧸ J :=
  DoubleQuot.quotQuotEquivQuotOfLE h

/--
Reference to the Chinese Remainder Theorem.

For coprime ideals I and J, we have R/(I ∩ J) ≃+* (R/I) × (R/J).
-/
noncomputable def chinese_remainder_theorem_reference (I J : Ideal R) (h : IsCoprime I J) :
    (R ⧸ I ⊓ J) ≃+* (R ⧸ I) × (R ⧸ J) :=
  Ideal.quotientInfEquivQuotientProd I J h

/--
The Third Isomorphism Theorem gives a bijection.
-/
theorem third_iso_bijective (I J : Ideal R) (h : I ≤ J) :
    Function.Bijective (third_isomorphism_theorem_reference I J h) :=
  (third_isomorphism_theorem_reference I J h).bijective

/--
The Chinese Remainder Theorem gives a bijection.
-/
theorem crt_bijective (I J : Ideal R) (h : IsCoprime I J) :
    Function.Bijective (chinese_remainder_theorem_reference I J h) :=
  (chinese_remainder_theorem_reference I J h).bijective

end RelatedTheorems
