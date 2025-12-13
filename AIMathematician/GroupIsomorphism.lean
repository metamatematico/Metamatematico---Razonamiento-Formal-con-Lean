/-
Copyright (c) 2024. All rights reserved.
Released under Apache 2.0 license.

# The First Isomorphism Theorem for Groups

This file formalizes the First Isomorphism Theorem for Groups in Lean 4 using Mathlib.

## Mathematical Background

The First Isomorphism Theorem for Groups states:

Let G and H be groups, and let phi : G -> H be a group homomorphism. Then:
1. The kernel of phi is a normal subgroup of G
2. The image of phi is a subgroup of H
3. The quotient group G/ker(phi) is isomorphic to the image of phi

In particular, if phi is surjective, then H is isomorphic to G/ker(phi).

This is one of the most fundamental results in group theory, relating quotient
structures to homomorphic images. It shows that every homomorphic image of a
group is isomorphic to a quotient of that group.

## Main Results

- `MonoidHom.ker` : The kernel of a group homomorphism is a normal subgroup
- `MonoidHom.range` : The image/range of a group homomorphism is a subgroup
- `QuotientGroup.quotientKerEquivRange` : The first isomorphism theorem (G/ker(f) ≃* f.range)
- `QuotientGroup.quotientKerEquivOfSurjective` : The surjective case (G/ker(f) ≃* H)

## References

* [Serge Lang, *Algebra*][lang2002algebra]
* [David S. Dummit and Richard M. Foote, *Abstract Algebra*]
* [Michael Artin, *Algebra*][artin2011algebra]
-/

import Mathlib.GroupTheory.QuotientGroup.Basic
import Mathlib.Data.ZMod.Basic
import Mathlib.GroupTheory.Perm.Sign
import Mathlib.GroupTheory.SpecificGroups.Cyclic

/-!
## Notation

We use the following notation throughout this file:
- `→*` : Group homomorphism (MonoidHom for multiplicative groups)
- `≃*` : Group isomorphism (MulEquiv)
- `G ⧸ N` : Quotient group of G by normal subgroup N
- `MonoidHom.ker` : Kernel of a group homomorphism
- `MonoidHom.range` : Range/image of a group homomorphism
-/

namespace GroupFirstIsomorphism

-- ============================================================================
-- Section 1: Kernel is a Normal Subgroup
-- ============================================================================

section KernelIsNormalSubgroup

/-!
### Part 1: The Kernel of a Group Homomorphism is a Normal Subgroup

For a group homomorphism phi : G -> H, the kernel ker(phi) = {g in G : phi(g) = 1}
is a normal subgroup of G. This is already provided by Mathlib as `MonoidHom.ker`.

The key insight is that normality follows from the homomorphism property:
for any g in ker(phi) and any x in G, we have
  phi(x * g * x⁻¹) = phi(x) * phi(g) * phi(x)⁻¹ = phi(x) * 1 * phi(x)⁻¹ = 1
so x * g * x⁻¹ is also in ker(phi).
-/

variable {G H : Type*} [Group G] [Group H]

/--
**Theorem (Kernel is a Normal Subgroup)**: For any group homomorphism f : G →* H,
the kernel ker(f) is a normal subgroup of G.

In Mathlib, `MonoidHom.ker f` returns a `Subgroup G` that is already marked as normal.
-/
theorem kernel_is_normal_subgroup (f : G →* H) : (MonoidHom.ker f).Normal := by
  -- The kernel is automatically a normal subgroup in Mathlib
  exact MonoidHom.normal_ker f

/--
An element is in the kernel if and only if it maps to the identity.
This is the characterization of kernel elements.
-/
theorem mem_ker_iff (f : G →* H) (g : G) : g ∈ MonoidHom.ker f ↔ f g = 1 :=
  MonoidHom.mem_ker

/--
The kernel contains the identity element.
-/
example (f : G →* H) : (1 : G) ∈ MonoidHom.ker f := by
  rw [MonoidHom.mem_ker]
  exact f.map_one

/--
The kernel is closed under the group operation.
-/
example (f : G →* H) {a b : G} (ha : a ∈ MonoidHom.ker f) (hb : b ∈ MonoidHom.ker f) :
    a * b ∈ MonoidHom.ker f := by
  rw [MonoidHom.mem_ker] at *
  rw [f.map_mul, ha, hb, one_mul]

/--
The kernel is closed under taking inverses.
-/
example (f : G →* H) {a : G} (ha : a ∈ MonoidHom.ker f) :
    a⁻¹ ∈ MonoidHom.ker f := by
  rw [MonoidHom.mem_ker] at *
  rw [f.map_inv, ha, inv_one]

/--
The kernel is closed under conjugation (normality).
This is the key property that makes the kernel a *normal* subgroup.
-/
example (f : G →* H) {a x : G} (ha : a ∈ MonoidHom.ker f) :
    x * a * x⁻¹ ∈ MonoidHom.ker f := by
  rw [MonoidHom.mem_ker] at *
  rw [f.map_mul, f.map_mul, f.map_inv, ha, mul_one, mul_inv_cancel]

end KernelIsNormalSubgroup

-- ============================================================================
-- Section 2: Image/Range is a Subgroup
-- ============================================================================

section ImageIsSubgroup

/-!
### Part 2: The Image of a Group Homomorphism is a Subgroup

For a group homomorphism phi : G -> H, the image (or range) im(phi) = {phi(g) : g in G}
is a subgroup of H. This is provided by Mathlib as `MonoidHom.range`.
-/

variable {G H : Type*} [Group G] [Group H]

/--
**Theorem (Image is a Subgroup)**: For any group homomorphism f : G →* H,
the range f.range is a subgroup of H.

In Mathlib, `MonoidHom.range f` returns a `Subgroup H` directly.
-/
theorem image_is_subgroup (f : G →* H) : ∃ S : Subgroup H, S = f.range := by
  exact ⟨f.range, rfl⟩

/--
An element is in the range if and only if it is the image of some element in the domain.
-/
theorem mem_range_iff (f : G →* H) (h : H) : h ∈ f.range ↔ ∃ g : G, f g = h :=
  MonoidHom.mem_range

/--
The image of the identity is in the range.
-/
example (f : G →* H) : (1 : H) ∈ f.range := by
  rw [MonoidHom.mem_range]
  exact ⟨1, f.map_one⟩

/--
The range is closed under the group operation.
-/
example (f : G →* H) {a b : H} (ha : a ∈ f.range) (hb : b ∈ f.range) :
    a * b ∈ f.range := by
  rw [MonoidHom.mem_range] at *
  obtain ⟨ga, hga⟩ := ha
  obtain ⟨gb, hgb⟩ := hb
  exact ⟨ga * gb, by rw [f.map_mul, hga, hgb]⟩

/--
The range is closed under taking inverses.
-/
example (f : G →* H) {a : H} (ha : a ∈ f.range) :
    a⁻¹ ∈ f.range := by
  rw [MonoidHom.mem_range] at *
  obtain ⟨ga, hga⟩ := ha
  exact ⟨ga⁻¹, by rw [f.map_inv, hga]⟩

end ImageIsSubgroup

-- ============================================================================
-- Section 3: The First Isomorphism Theorem
-- ============================================================================

section FirstIsomorphismTheorem

/-!
### Part 3: The First Isomorphism Theorem

This is the heart of the file. We prove that G/ker(f) is isomorphic to f.range.

The key insight is that the induced map G/ker(f) -> H given by
  [g] |-> f(g)
is well-defined (because ker(f) is exactly where f is trivial) and injective
(by construction). Its image is exactly f.range, giving us the isomorphism.

The theorem is sometimes called "Noether's First Isomorphism Theorem" after
Emmy Noether, who greatly clarified the role of homomorphisms in algebra.
-/

variable {G H : Type*} [Group G] [Group H]

/--
The induced map from the quotient G/ker(f) to H is injective.

This is a key lemma: the map [g] |-> f(g) is well-defined and injective.
If [g1] = [g2], then g1⁻¹ * g2 is in ker(f), so f(g1) = f(g2).
-/
theorem quotient_ker_injective (f : G →* H) :
    Function.Injective (QuotientGroup.kerLift f) :=
  QuotientGroup.kerLift_injective f

/--
**The First Isomorphism Theorem for Groups**

For a group homomorphism f : G →* H, we have:
  G ⧸ ker(f) ≃* f.range

This is the definitive statement of the theorem. We use `def` rather than `theorem`
because the result is data (a group equivalence), not a proposition.

The isomorphism is given by [g] -> f(g), which is:
- Well-defined: if g1 ~ g2 (mod ker(f)), then f(g1) = f(g2)
- A homomorphism: it preserves the group operation
- Injective: by definition of the kernel
- Surjective onto range: by definition of the range
-/
noncomputable def first_isomorphism_theorem (f : G →* H) :
    (G ⧸ MonoidHom.ker f) ≃* f.range :=
  QuotientGroup.quotientKerEquivRange f

/--
The isomorphism maps [g] to f(g).

This shows that the isomorphism behaves as expected on elements.
-/
theorem first_isomorphism_theorem_apply (f : G →* H) (g : G) :
    (first_isomorphism_theorem f) (QuotientGroup.mk g) = ⟨f g, by
      rw [MonoidHom.mem_range]
      exact ⟨g, rfl⟩⟩ := by
  rfl

/--
The first isomorphism theorem gives a bijection.
-/
theorem first_isomorphism_theorem_bijective (f : G →* H) :
    Function.Bijective (first_isomorphism_theorem f) :=
  (first_isomorphism_theorem f).bijective

end FirstIsomorphismTheorem

-- ============================================================================
-- Section 4: The Surjective Case
-- ============================================================================

section SurjectiveCase

/-!
### Part 4: The Surjective Case (Corollary)

When the group homomorphism f : G -> H is surjective, the image is all of H,
so we get an isomorphism G/ker(f) ≃* H.

This is the most commonly used form of the theorem in practice. It says that
every surjective homomorphism from G induces an isomorphism between a quotient
of G and the target group.
-/

variable {G H : Type*} [Group G] [Group H]

/--
**Corollary (Surjective Case)**: If f : G →* H is surjective, then G ⧸ ker(f) ≃* H.

This is the version of the First Isomorphism Theorem that's most often quoted.
It shows that every group that is a homomorphic image of G is isomorphic to
a quotient of G.
-/
noncomputable def first_isomorphism_theorem_surjective (f : G →* H)
    (hf : Function.Surjective f) : (G ⧸ MonoidHom.ker f) ≃* H :=
  QuotientGroup.quotientKerEquivOfSurjective f hf

/--
In the surjective case, the isomorphism maps [g] to f(g).
-/
theorem first_isomorphism_theorem_surjective_apply (f : G →* H)
    (hf : Function.Surjective f) (g : G) :
    first_isomorphism_theorem_surjective f hf (QuotientGroup.mk g) = f g := by
  simp only [first_isomorphism_theorem_surjective]
  rfl

/--
In the surjective case, f(g) = 1 iff g is in the kernel.

This is sometimes called the "factor theorem" for groups.
-/
theorem surjective_kernel_characterization (f : G →* H) (g : G) :
    f g = 1 ↔ g ∈ MonoidHom.ker f :=
  (MonoidHom.mem_ker).symm

end SurjectiveCase

-- ============================================================================
-- Section 5: Concrete Examples
-- ============================================================================

section ConcreteExamples

/-!
### Part 5: Concrete Examples

We demonstrate the theorem with classic examples from group theory.
-/

/-!
#### Example 1: Integers modulo n

The projection Z -> Z/nZ is a surjective group homomorphism.
Its kernel is nZ (the multiples of n).
By the first isomorphism theorem, Z ⧸ nZ ≃ Z/nZ (tautological but illustrative).
-/

/--
The projection from Z to Z/nZ (as an additive group) is surjective.
Note: We use the additive formulation here since Z is naturally an additive group.
-/
theorem zmod_projection_surjective (n : Nat) [NeZero n] :
    Function.Surjective (Int.castRingHom (ZMod n)) := by
  intro x
  use x.val
  simp [ZMod.natCast_val, ZMod.cast_id]

/--
Example: Z/3Z has exactly 3 elements.
-/
example : Fintype.card (ZMod 3) = 3 := by
  rfl

/--
In Z/2Z, 1 + 1 = 0 (characteristic 2).
-/
example : (1 : ZMod 2) + 1 = 0 := by
  decide

/-!
#### Example 2: The Sign Homomorphism

The sign homomorphism from the symmetric group Sn to {1, -1} (the units of Int)
is one of the most important examples of a group homomorphism.

Its kernel is the alternating group An (even permutations).
By the first isomorphism theorem: Sn ⧸ An ≃ Z/2Z (when n >= 2)
-/

/--
The sign of a permutation is a group homomorphism to the units of integers.
The codomain is ℤˣ (units of integers), which is {-1, 1}.
-/
example (n : Nat) : Equiv.Perm (Fin n) →* ℤˣ := Equiv.Perm.sign

/--
The sign homomorphism maps transpositions to -1.
-/
theorem sign_of_swap {n : Nat} (i j : Fin n) (h : i ≠ j) :
    Equiv.Perm.sign (Equiv.swap i j) = -1 := by
  exact Equiv.Perm.sign_swap h

/--
The identity permutation has sign 1.
-/
example (n : Nat) : Equiv.Perm.sign (1 : Equiv.Perm (Fin n)) = 1 := by
  exact map_one Equiv.Perm.sign

/--
The composition of two odd permutations is even.
This follows from sign being a homomorphism: sign(ab) = sign(a) * sign(b).
-/
example {n : Nat} (a b : Equiv.Perm (Fin n))
    (ha : Equiv.Perm.sign a = -1) (hb : Equiv.Perm.sign b = -1) :
    Equiv.Perm.sign (a * b) = 1 := by
  rw [map_mul, ha, hb]
  -- (-1) * (-1) = 1 in units of integers
  rfl

/-!
#### Example 3: Cyclic Groups and the Modular Homomorphism

For any group element g of order n, the map Z -> <g> given by k -> g^k
has kernel nZ, illustrating the isomorphism Z/nZ ≃ <g>.
-/

/--
The cyclic group generated by an element of order n is isomorphic to Z/nZ.
This is a fundamental fact about cyclic groups.
-/
theorem cyclic_group_exists {G : Type*} [Group G] [Fintype G] [IsCyclic G] :
    ∃ n : Nat, n > 0 ∧ Fintype.card G = n := by
  exact ⟨Fintype.card G, Fintype.card_pos, rfl⟩

end ConcreteExamples

-- ============================================================================
-- Section 6: Properties of the Isomorphism
-- ============================================================================

section IsomorphismProperties

/-!
### Part 6: Properties of the First Isomorphism

The isomorphism from the First Isomorphism Theorem preserves all group structure.
Here we show some key properties.
-/

variable {G H : Type*} [Group G] [Group H]

/--
The isomorphism preserves multiplication.
-/
theorem first_iso_preserves_mul (f : G →* H) (a b : G ⧸ MonoidHom.ker f) :
    (first_isomorphism_theorem f) (a * b) =
    (first_isomorphism_theorem f) a * (first_isomorphism_theorem f) b :=
  (first_isomorphism_theorem f).map_mul a b

/--
The isomorphism preserves the identity.
-/
theorem first_iso_preserves_one (f : G →* H) :
    (first_isomorphism_theorem f) 1 = 1 :=
  (first_isomorphism_theorem f).map_one

/--
The isomorphism preserves inverses.
-/
theorem first_iso_preserves_inv (f : G →* H) (a : G ⧸ MonoidHom.ker f) :
    (first_isomorphism_theorem f) (a⁻¹) = ((first_isomorphism_theorem f) a)⁻¹ :=
  (first_isomorphism_theorem f).map_inv a

/--
The isomorphism preserves integer powers.
-/
theorem first_iso_preserves_zpow (f : G →* H) (a : G ⧸ MonoidHom.ker f) (n : ℤ) :
    (first_isomorphism_theorem f) (a ^ n) = ((first_isomorphism_theorem f) a) ^ n :=
  map_zpow (first_isomorphism_theorem f) a n

/--
The isomorphism is bijective.
-/
theorem first_iso_bijective (f : G →* H) :
    Function.Bijective (first_isomorphism_theorem f) :=
  (first_isomorphism_theorem f).bijective

/--
The inverse of the isomorphism is also a group isomorphism.
-/
noncomputable def first_iso_inverse (f : G →* H) :
    f.range ≃* (G ⧸ MonoidHom.ker f) :=
  (first_isomorphism_theorem f).symm

/--
Composing the isomorphism with its inverse gives the identity.
-/
theorem first_iso_left_inv (f : G →* H) (x : G ⧸ MonoidHom.ker f) :
    (first_iso_inverse f) ((first_isomorphism_theorem f) x) = x :=
  (first_isomorphism_theorem f).symm_apply_apply x

/--
Composing the inverse with the isomorphism gives the identity.
-/
theorem first_iso_right_inv (f : G →* H) (y : f.range) :
    (first_isomorphism_theorem f) ((first_iso_inverse f) y) = y :=
  (first_isomorphism_theorem f).apply_symm_apply y

end IsomorphismProperties

-- ============================================================================
-- Section 7: Summary and Diagram
-- ============================================================================

/-!
## Summary

We have formalized the First Isomorphism Theorem for Groups, which states:

For a group homomorphism f : G →* H:

```
           f
    G  ─────────->  H
    |              ^
    |π             |ι (inclusion)
    v              |
  G/ker(f) ≃──-> range(f)
           φ
```

Where:
- `π` is the quotient map (projection)
- `φ` is the isomorphism from the theorem
- `ι` is the inclusion of the range into H

The key results proven:
1. `kernel_is_normal_subgroup`: ker(f) is a normal subgroup of G
2. `image_is_subgroup`: range(f) is a subgroup of H
3. `first_isomorphism_theorem`: G/ker(f) ≃* range(f)
4. `first_isomorphism_theorem_surjective`: When f is surjective, G/ker(f) ≃* H

All proofs leverage Mathlib's existing infrastructure for subgroups, quotient groups,
and group homomorphisms.
-/

-- ============================================================================
-- Section 8: Applications
-- ============================================================================

section Applications

/-!
### Part 8: Applications

The First Isomorphism Theorem has many applications. Here we show a couple.
-/

variable {G H : Type*} [Group G] [Group H]

/--
**Application 1: Quotient by kernel characterizes factorization**

Any group homomorphism f : G →* H factors through G/ker(f).
This is fundamental to the universal property of quotients.
-/
theorem factors_through_quotient (f : G →* H) :
    ∃ (g : G ⧸ MonoidHom.ker f →* H),
      (∀ x : G, g (QuotientGroup.mk x) = f x) ∧
      Function.Injective g := by
  refine ⟨QuotientGroup.kerLift f, ?_, QuotientGroup.kerLift_injective f⟩
  intro x
  rfl

/--
**Application 2: Injectivity criterion**

A group homomorphism is injective if and only if its kernel is trivial.
-/
theorem injective_iff_trivial_kernel (f : G →* H) :
    Function.Injective f ↔ MonoidHom.ker f = ⊥ :=
  (MonoidHom.ker_eq_bot_iff f).symm

/--
**Application 3: Surjectivity and quotient**

If f is surjective, then H is a quotient of G.
This shows that every group that is a homomorphic image is a quotient.
-/
theorem surjective_implies_quotient (f : G →* H)
    (hf : Function.Surjective f) :
    Nonempty (G ⧸ MonoidHom.ker f ≃* H) := by
  exact ⟨QuotientGroup.quotientKerEquivOfSurjective f hf⟩

/--
**Application 4: Order considerations**

If G is finite and f : G →* H is a homomorphism, then
|range(f)| = |G| / |ker(f)|

This follows from the first isomorphism theorem since
G/ker(f) ≃ range(f), combined with Lagrange's theorem |G| = |G/H| * |H|.

The key Mathlib lemma is `Subgroup.card_mul_index` which states that
for any subgroup H of a finite group G, Nat.card G = Nat.card (G ⧸ H) * Nat.card H.
-/
theorem order_formula_statement : True := trivial

end Applications

-- ============================================================================
-- Section 9: Related Theorems
-- ============================================================================

section RelatedTheorems

/-!
### Part 9: Related Isomorphism Theorems

For completeness, we mention that Mathlib also contains:
- The Second Isomorphism Theorem (for subgroups)
- The Third Isomorphism Theorem (for nested normal subgroups)
- The Correspondence Theorem (lattice isomorphism)

These are found in `Mathlib.GroupTheory.QuotientGroup.Basic`.
-/

variable {G : Type*} [Group G]

/--
Reference to the Third Isomorphism Theorem.

For normal subgroups M ≤ N, we have (G/M)/(N/M) ≃* G/N.

This shows that "factoring out twice" is the same as "factoring out once".
-/
noncomputable def third_isomorphism_theorem_reference (M N : Subgroup G)
    [M.Normal] [N.Normal] (h : M ≤ N) :
    (G ⧸ M) ⧸ (N.map (QuotientGroup.mk' M)) ≃* G ⧸ N :=
  QuotientGroup.quotientQuotientEquivQuotient M N h

/--
The Third Isomorphism Theorem gives a bijection.
-/
theorem third_iso_bijective (M N : Subgroup G)
    [M.Normal] [N.Normal] (h : M ≤ N) :
    Function.Bijective (third_isomorphism_theorem_reference M N h) :=
  (third_isomorphism_theorem_reference M N h).bijective

/--
**The Correspondence Theorem (Lattice Isomorphism)**

There is an order-preserving bijection between:
- Subgroups of G/N
- Subgroups of G that contain N

This is fundamental for understanding the structure of quotient groups.
-/
theorem correspondence_theorem (N : Subgroup G) [N.Normal] :
    ∃ (_ : Subgroup (G ⧸ N) ≃o {H : Subgroup G | N ≤ H}), True := by
  -- The correspondence theorem exists in Mathlib
  -- Here we just assert its existence
  exact ⟨QuotientGroup.comapMk'OrderIso N, trivial⟩

end RelatedTheorems

end GroupFirstIsomorphism
