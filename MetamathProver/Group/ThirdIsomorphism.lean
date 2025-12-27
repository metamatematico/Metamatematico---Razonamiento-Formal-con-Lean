/-
Copyright (c) 2024. All rights reserved.
Released under Apache 2.0 license.

# The Third Isomorphism Theorem and Correspondence Theorem for Groups

This file formalizes the Third Isomorphism Theorem and the Correspondence (Lattice) Theorem
for Groups in Lean 4 using Mathlib.

## Mathematical Background

Let G be a group and N a normal subgroup of G. The theorems in this file describe the
relationship between subgroups of G containing N and subgroups of the quotient G/N.

### The Correspondence Theorem (Lattice Theorem / Fourth Isomorphism Theorem)

There is an order-preserving bijection between:
- Subgroups of G/N
- Subgroups of G that contain N

Moreover, this bijection preserves normality: K/N is normal in G/N if and only if K is
normal in G.

The four parts of the Correspondence Theorem:
1. If K is a subgroup of G with N ⊆ K ⊆ G, then K/N is a subgroup of G/N
2. Every subgroup of G/N has the form K/N for some subgroup K with N ⊆ K ⊆ G
3. If K is a normal subgroup of G with N ⊆ K ⊆ G, then K/N is normal in G/N
4. Every normal subgroup of G/N is of the form K/N for some normal subgroup K with N ⊆ K ⊆ G

### The Third Isomorphism Theorem

If K is a normal subgroup of G such that N ⊆ K ⊆ G, then:
  (G/N)/(K/N) ≃* G/K

Intuitively: "Factoring out twice is the same as factoring out once by the larger subgroup."

## Main Results

- `correspondence_theorem`: The lattice isomorphism between subgroups of G/N and
  subgroups of G containing N (Mathlib: `QuotientGroup.comapMk'OrderIso`)
- `thirdIsomorphismTheorem`: (G/N)/(K/N) ≃* G/K (Mathlib: `QuotientGroup.quotientQuotientEquivQuotient`)

## References

* [Serge Lang, *Algebra*][lang2002algebra]
* [David S. Dummit and Richard M. Foote, *Abstract Algebra*]
* [Michael Artin, *Algebra*][artin2011algebra]
-/

import Mathlib.GroupTheory.QuotientGroup.Basic
import Mathlib.Tactic.Group

/-!
## Notation

We use the following notation throughout this file:
- `→*` : Group homomorphism (MonoidHom for multiplicative groups)
- `≃*` : Group isomorphism (MulEquiv)
- `G ⧸ N` : Quotient group of G by normal subgroup N
- `Subgroup.map f H` : Image of subgroup H under homomorphism f
- `Subgroup.comap f H` : Preimage of subgroup H under homomorphism f
-/

namespace ThirdIsomorphismTheorem

variable {G : Type*} [Group G]

-- ============================================================================
-- Section 1: The Quotient Map and Its Properties
-- ============================================================================

section QuotientMapProperties

/-!
### The Quotient Map

The quotient map `mk' N : G →* G/N` is the canonical surjective homomorphism.
Its key properties are essential for understanding the correspondence and
isomorphism theorems.
-/

/--
The quotient map `G →* G/N` is surjective.
-/
theorem mk_surjective (N : Subgroup G) [N.Normal] :
    Function.Surjective (QuotientGroup.mk' N) :=
  QuotientGroup.mk'_surjective N

/--
The kernel of the quotient map is exactly N.
-/
theorem ker_mk_eq (N : Subgroup G) [N.Normal] :
    MonoidHom.ker (QuotientGroup.mk' N) = N :=
  QuotientGroup.ker_mk' N

/--
An element maps to 1 in the quotient iff it is in N.
-/
theorem mk_eq_one_iff (N : Subgroup G) [N.Normal] (g : G) :
    (QuotientGroup.mk' N) g = 1 ↔ g ∈ N :=
  QuotientGroup.eq_one_iff g

end QuotientMapProperties

-- ============================================================================
-- Section 2: Correspondence Theorem - Part 1 (Subgroups containing N map to subgroups)
-- ============================================================================

section CorrespondencePart1

/-!
### Part 1: If K is a subgroup of G with N ⊆ K, then K/N is a subgroup of G/N

When N is a normal subgroup of G and K is any subgroup containing N, the image
of K under the quotient map is a subgroup of G/N, denoted K/N.

In Mathlib, this is `Subgroup.map (QuotientGroup.mk' N) K`.
-/

/--
**Correspondence Theorem Part 1**: For a normal subgroup N and any subgroup K ≥ N,
the image K/N = Subgroup.map (mk' N) K is a subgroup of G/N.

This is automatic since `Subgroup.map` always produces a subgroup.
-/
theorem subgroup_maps_to_subgroup (N K : Subgroup G) [N.Normal] (_hNK : N ≤ K) :
    ∃ H : Subgroup (G ⧸ N), H = Subgroup.map (QuotientGroup.mk' N) K :=
  ⟨Subgroup.map (QuotientGroup.mk' N) K, rfl⟩

/--
The subgroup K/N is the image of K under the quotient map.
-/
def quotientSubgroup (N K : Subgroup G) [N.Normal] : Subgroup (G ⧸ N) :=
  Subgroup.map (QuotientGroup.mk' N) K

/--
An element is in K/N iff it has a representative in K.
-/
theorem mem_quotientSubgroup_iff (N K : Subgroup G) [N.Normal] (x : G ⧸ N) :
    x ∈ quotientSubgroup N K ↔ ∃ k : G, k ∈ K ∧ QuotientGroup.mk' N k = x := by
  simp only [quotientSubgroup, Subgroup.mem_map]

end CorrespondencePart1

-- ============================================================================
-- Section 3: Correspondence Theorem - Part 2 (Every subgroup of G/N comes from some K)
-- ============================================================================

section CorrespondencePart2

/-!
### Part 2: Every subgroup of G/N is of the form K/N for some K ≥ N

The preimage of any subgroup H of G/N under the quotient map is a subgroup K of G
that contains N, and the image of K is exactly H.
-/

/--
The preimage of a subgroup of G/N under mk' contains N.
-/
theorem le_comap_mk (N : Subgroup G) [N.Normal] (H : Subgroup (G ⧸ N)) :
    N ≤ Subgroup.comap (QuotientGroup.mk' N) H :=
  QuotientGroup.le_comap_mk' N H

/--
**Correspondence Theorem Part 2**: Every subgroup of G/N is of the form K/N
for some subgroup K of G with N ≤ K.
-/
theorem subgroup_of_quotient_from_subgroup (N : Subgroup G) [N.Normal]
    (H : Subgroup (G ⧸ N)) :
    ∃ K : Subgroup G, N ≤ K ∧ Subgroup.map (QuotientGroup.mk' N) K = H := by
  use Subgroup.comap (QuotientGroup.mk' N) H
  constructor
  · exact le_comap_mk N H
  · exact Subgroup.map_comap_eq_self_of_surjective (QuotientGroup.mk'_surjective N) H

/--
The preimage K and image H correspond bijectively.
-/
theorem comap_map_eq_self (N : Subgroup G) [N.Normal] (H : Subgroup (G ⧸ N)) :
    Subgroup.map (QuotientGroup.mk' N) (Subgroup.comap (QuotientGroup.mk' N) H) = H :=
  Subgroup.map_comap_eq_self_of_surjective (QuotientGroup.mk'_surjective N) H

end CorrespondencePart2

-- ============================================================================
-- Section 4: Correspondence Theorem - Part 3 (Normal subgroups map to normal)
-- ============================================================================

section CorrespondencePart3

/-!
### Part 3: If K is normal in G with N ≤ K, then K/N is normal in G/N

The image of a normal subgroup under a surjective homomorphism is normal in the
codomain. In particular, if K is normal in G and contains N, then K/N is normal in G/N.
-/

/--
**Correspondence Theorem Part 3**: If K is a normal subgroup of G with N ≤ K,
then K/N is a normal subgroup of G/N.

This follows from the fact that surjective homomorphisms preserve normality.
-/
instance normal_maps_to_normal (N K : Subgroup G) [N.Normal] [hK : K.Normal] :
    (Subgroup.map (QuotientGroup.mk' N) K).Normal :=
  hK.map (QuotientGroup.mk' N) (QuotientGroup.mk'_surjective N)

/--
The image of a normal subgroup under mk' is normal.
-/
theorem quotientSubgroup_normal (N K : Subgroup G) [N.Normal] [K.Normal] :
    (quotientSubgroup N K).Normal := by
  exact normal_maps_to_normal N K

end CorrespondencePart3

-- ============================================================================
-- Section 5: Correspondence Theorem - Part 4 (Normal in G/N comes from normal in G)
-- ============================================================================

section CorrespondencePart4

/-!
### Part 4: Every normal subgroup of G/N is of the form K/N for some normal K ≥ N

If H is a normal subgroup of G/N, then its preimage K under the quotient map is
normal in G (and contains N), and H = K/N.
-/

/--
The preimage of a normal subgroup of G/N under mk' is normal in G.
-/
instance comap_normal_of_normal (N : Subgroup G) [N.Normal] (H : Subgroup (G ⧸ N))
    [hH : H.Normal] :
    (Subgroup.comap (QuotientGroup.mk' N) H).Normal :=
  hH.comap (QuotientGroup.mk' N)

/--
**Correspondence Theorem Part 4**: Every normal subgroup of G/N is of the form K/N
for some normal subgroup K of G with N ≤ K.
-/
theorem normal_subgroup_of_quotient_from_normal (N : Subgroup G) [N.Normal]
    (H : Subgroup (G ⧸ N)) [hH : H.Normal] :
    ∃ K : Subgroup G, K.Normal ∧ N ≤ K ∧ Subgroup.map (QuotientGroup.mk' N) K = H := by
  let K := Subgroup.comap (QuotientGroup.mk' N) H
  have hK_normal : K.Normal := comap_normal_of_normal N H
  use K
  exact ⟨hK_normal, le_comap_mk N H, comap_map_eq_self N H⟩

end CorrespondencePart4

-- ============================================================================
-- Section 6: The Full Correspondence Theorem (Lattice Isomorphism)
-- ============================================================================

section FullCorrespondence

/-!
### The Correspondence Theorem (Lattice Isomorphism)

The four parts above combine into the full correspondence theorem: there is an
order-preserving bijection (lattice isomorphism) between subgroups of G/N and
subgroups of G containing N.

The bijection is:
- Forward: H ↦ comap (mk' N) H (preimage under quotient map)
- Backward: K ↦ map (mk' N) K (image under quotient map, i.e., K/N)
-/

/--
**The Correspondence Theorem (Lattice Isomorphism)**

There is an order isomorphism between:
- Subgroups of G/N
- Subgroups of G that contain N

This is Mathlib's `QuotientGroup.comapMk'OrderIso`.
-/
def correspondenceTheorem (N : Subgroup G) [N.Normal] :
    Subgroup (G ⧸ N) ≃o {K : Subgroup G // N ≤ K} :=
  QuotientGroup.comapMk'OrderIso N

/--
The correspondence preserves the order (inclusion of subgroups).
-/
theorem correspondence_preserves_order (N : Subgroup G) [N.Normal]
    (H₁ H₂ : Subgroup (G ⧸ N)) :
    H₁ ≤ H₂ ↔ Subgroup.comap (QuotientGroup.mk' N) H₁ ≤ Subgroup.comap (QuotientGroup.mk' N) H₂ := by
  exact (Subgroup.comap_le_comap_of_surjective (QuotientGroup.mk'_surjective N)).symm

/--
The correspondence maps the trivial subgroup of G/N to N itself.
-/
theorem correspondence_bot (N : Subgroup G) [N.Normal] :
    Subgroup.comap (QuotientGroup.mk' N) ⊥ = N := by
  ext g
  simp only [Subgroup.mem_comap, Subgroup.mem_bot]
  exact QuotientGroup.eq_one_iff g

/--
The correspondence maps G/N (as a subgroup of itself) to G.
-/
theorem correspondence_top (N : Subgroup G) [N.Normal] :
    Subgroup.comap (QuotientGroup.mk' N) ⊤ = ⊤ := by
  ext g
  simp only [Subgroup.mem_comap, Subgroup.mem_top]

end FullCorrespondence

-- ============================================================================
-- Section 7: The Third Isomorphism Theorem
-- ============================================================================

section ThirdIsomorphism

/-!
### The Third Isomorphism Theorem

This is the main theorem: if N ≤ K are both normal subgroups of G, then
(G/N)/(K/N) ≃* G/K.

The key insight is that K/N (the image of K under mk' N) is normal in G/N
(as shown in Part 3), so we can form the double quotient (G/N)/(K/N).

The isomorphism sends the coset (gN)(K/N) to the coset gK.
-/

variable (N K : Subgroup G) [N.Normal] [hK : K.Normal] (h : N ≤ K)

/--
The image of K under the quotient map G → G/N is normal in G/N.
This is needed to form the double quotient.
-/
instance K_mod_N_normal : (Subgroup.map (QuotientGroup.mk' N) K).Normal :=
  hK.map (QuotientGroup.mk' N) (QuotientGroup.mk'_surjective N)

/--
**The Third Isomorphism Theorem**

For normal subgroups N ≤ K of G:
  (G/N)/(K/N) ≃* G/K

where K/N = Subgroup.map (QuotientGroup.mk' N) K.

This shows that "factoring out twice" (first by N, then by K/N) is the same
as "factoring out once" (by K).
-/
noncomputable def thirdIsomorphismTheorem :
    (G ⧸ N) ⧸ (Subgroup.map (QuotientGroup.mk' N) K) ≃* G ⧸ K :=
  QuotientGroup.quotientQuotientEquivQuotient N K h

/--
The third isomorphism theorem is a bijection.
-/
theorem third_iso_bijective :
    Function.Bijective (thirdIsomorphismTheorem N K h) :=
  (thirdIsomorphismTheorem N K h).bijective

/--
The isomorphism sends (gN)(K/N) to gK.
-/
theorem third_iso_apply (g : G) :
    thirdIsomorphismTheorem N K h (QuotientGroup.mk (QuotientGroup.mk g)) =
    QuotientGroup.mk g := by
  simp only [thirdIsomorphismTheorem]
  rfl

end ThirdIsomorphism

-- ============================================================================
-- Section 8: The Inverse Isomorphism
-- ============================================================================

section InverseIsomorphism

/-!
### The Inverse of the Third Isomorphism

The inverse map sends gK to (gN)(K/N).
-/

variable (N K : Subgroup G) [N.Normal] [K.Normal] (h : N ≤ K)

/--
The inverse of the third isomorphism theorem.
Maps G/K → (G/N)/(K/N).
-/
noncomputable def third_iso_inverse :
    G ⧸ K ≃* (G ⧸ N) ⧸ (Subgroup.map (QuotientGroup.mk' N) K) :=
  (thirdIsomorphismTheorem N K h).symm

/--
Composing the isomorphism with its inverse gives the identity.
-/
theorem third_iso_left_inv
    (x : (G ⧸ N) ⧸ (Subgroup.map (QuotientGroup.mk' N) K)) :
    (third_iso_inverse N K h) ((thirdIsomorphismTheorem N K h) x) = x :=
  (thirdIsomorphismTheorem N K h).symm_apply_apply x

/--
Composing the inverse with the isomorphism gives the identity.
-/
theorem third_iso_right_inv (y : G ⧸ K) :
    (thirdIsomorphismTheorem N K h) ((third_iso_inverse N K h) y) = y :=
  (thirdIsomorphismTheorem N K h).apply_symm_apply y

end InverseIsomorphism

-- ============================================================================
-- Section 9: Order/Index Formula
-- ============================================================================

section IndexFormula

/-!
### Order and Index Formulas

For finite groups, the third isomorphism theorem implies:
  |G/K| = |(G/N)/(K/N)|

Or equivalently:
  [G : K] = [G/N : K/N]
-/

variable (N K : Subgroup G) [N.Normal] [K.Normal]

/--
For finite quotients, the cardinalities are equal.
-/
theorem order_formula (h : N ≤ K)
    [Fintype (G ⧸ K)]
    [Fintype ((G ⧸ N) ⧸ (Subgroup.map (QuotientGroup.mk' N) K))] :
    Fintype.card ((G ⧸ N) ⧸ (Subgroup.map (QuotientGroup.mk' N) K)) =
    Fintype.card (G ⧸ K) :=
  Fintype.card_eq.mpr ⟨(thirdIsomorphismTheorem N K h).toEquiv⟩

end IndexFormula

-- ============================================================================
-- Section 10: Composition of Quotient Maps
-- ============================================================================

section CompositionOfQuotients

/-!
### Composition of Quotient Maps

The third isomorphism theorem can also be understood through the composition
of quotient maps. The map G → G/K factors as G → G/N → (G/N)/(K/N) → G/K.
-/

variable (N K : Subgroup G) [N.Normal] [K.Normal]

/--
The composition of the two quotient maps.
-/
def double_quotient_map :
    G →* (G ⧸ N) ⧸ (Subgroup.map (QuotientGroup.mk' N) K) :=
  (QuotientGroup.mk' (Subgroup.map (QuotientGroup.mk' N) K)).comp (QuotientGroup.mk' N)

/--
The double quotient map is surjective.
-/
theorem double_quotient_map_surjective :
    Function.Surjective (double_quotient_map N K) := by
  unfold double_quotient_map
  exact (QuotientGroup.mk'_surjective (Subgroup.map (QuotientGroup.mk' N) K)).comp
    (QuotientGroup.mk'_surjective N)

/--
The kernel of the double quotient map is K when N ≤ K.
This follows from the third isomorphism theorem: the composition
G → G/N → (G/N)/(K/N) ≃ G/K has kernel K.
-/
theorem double_quotient_map_ker (h : N ≤ K) :
    MonoidHom.ker (double_quotient_map N K) = K := by
  -- Use the third isomorphism theorem and properties of kernels
  let iso := thirdIsomorphismTheorem N K h
  ext g
  rw [MonoidHom.mem_ker]
  simp only [double_quotient_map, MonoidHom.coe_comp, Function.comp_apply]
  -- g is in the kernel iff (mk' N g) maps to 1 in the double quotient
  -- iff iso((mk' N g)) = 1 in G/K (since iso is an isomorphism)
  -- iff g ∈ K
  rw [← iso.map_eq_one_iff]
  -- iso maps mk g (double quotient) to mk g (quotient by K)
  show iso (QuotientGroup.mk (QuotientGroup.mk g)) = 1 ↔ g ∈ K
  simp only [iso, third_iso_apply N K h g]
  exact QuotientGroup.eq_one_iff g

end CompositionOfQuotients

-- ============================================================================
-- Section 11: Summary and Diagram
-- ============================================================================

/-!
## Summary

We have formalized the Third Isomorphism Theorem and the Correspondence Theorem for Groups.

### The Correspondence Theorem (Lattice Theorem)

For a normal subgroup N of G, there is an order-preserving bijection:

```
  Subgroups of G/N  ⟷  Subgroups of G containing N
        H          ↦   comap (mk' N) H
   map (mk' N) K   ↤   K
```

Key properties:
1. K ↦ K/N is well-defined for K ≥ N (`subgroup_maps_to_subgroup`)
2. Every subgroup of G/N is some K/N (`subgroup_of_quotient_from_subgroup`)
3. K normal implies K/N normal (`normal_maps_to_normal`)
4. H normal in G/N implies its preimage is normal in G (`comap_normal_of_normal`)

### The Third Isomorphism Theorem

For normal subgroups N ≤ K of G:

```
        G
       / \
      /   \
    G/N   G/K
     |     ↑
     v     |
  (G/N)/(K/N) ≃* G/K
```

The diagram commutes: the quotient map G → G/K factors through
G → G/N → (G/N)/(K/N) followed by the isomorphism.

**Intuition**: "Factoring out twice is the same as factoring out once."
If we first mod out by N (the smaller normal subgroup) and then by K/N,
we get the same result as modding out by K directly.

### Main Definitions

- `correspondenceTheorem`: The lattice isomorphism (Mathlib: `QuotientGroup.comapMk'OrderIso`)
- `thirdIsomorphismTheorem`: (G/N)/(K/N) ≃* G/K (Mathlib: `QuotientGroup.quotientQuotientEquivQuotient`)

All proofs leverage Mathlib's infrastructure for quotient groups, normal subgroups,
and group homomorphisms.
-/

end ThirdIsomorphismTheorem
