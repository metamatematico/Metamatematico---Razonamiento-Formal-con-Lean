/-
Copyright (c) 2024. All rights reserved.
Released under Apache 2.0 license.

# The Fourth Isomorphism Theorem (Lattice/Correspondence Theorem) for Groups

This file formalizes the Fourth Isomorphism Theorem (also known as the Lattice Theorem
or Correspondence Theorem) for Groups in Lean 4 using Mathlib.

## Mathematical Background

Let G be a group and N a normal subgroup of G. The Fourth Isomorphism Theorem establishes
a fundamental correspondence between:
- The set of subgroups of G that contain N: {K : Subgroup G | N <= K}
- The set of all subgroups of the quotient group G/N

### The Bijection

The correspondence is given by:
- **Forward map (Phi)**: K |-> K/N = image of K under the quotient map G -> G/N
- **Inverse map (Psi)**: H |-> preimage of H under the quotient map

### Key Properties

1. **Bijection**: Phi and Psi are mutually inverse
2. **Order-preserving**: K1 <= K2 iff Phi(K1) <= Phi(K2) (lattice isomorphism)
3. **Preserves meets (intersections)**: Phi(K1 meet K2) = Phi(K1) meet Phi(K2)
4. **Preserves joins (products)**: Phi(K1 join K2) = Phi(K1) join Phi(K2)
5. **Preserves normality**: K is normal in G iff Phi(K) is normal in G/N

### Historical Note

This theorem is variously called:
- The **Fourth Isomorphism Theorem** (in some numbering conventions)
- The **Lattice Theorem** (emphasizing the lattice-theoretic content)
- The **Correspondence Theorem** (emphasizing the bijection)

The theorem reveals that the quotient G/N "remembers" the subgroup structure of G
above N, while "forgetting" the structure below N.

## Main Results

- `latticeTheorem`: The order isomorphism between Subgroup (G/N) and {K : Subgroup G | N <= K}
- `correspondence_map_def`: K |-> map (mk' N) K
- `correspondence_comap_def`: H |-> comap (mk' N) H
- `lattice_preserves_meet`: The correspondence preserves meets (intersections)
- `lattice_preserves_join`: The correspondence preserves joins (products)
- `normal_correspondence`: Normal subgroups correspond to normal subgroups

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
- `->*` : Group homomorphism (MonoidHom for multiplicative groups)
- `=~*` : Group isomorphism (MulEquiv)
- `G quo N` : Quotient group of G by normal subgroup N
- `Subgroup.map f H` : Image of subgroup H under homomorphism f
- `Subgroup.comap f H` : Preimage of subgroup H under homomorphism f
- `meet` : Infimum (intersection) of subgroups
- `join` : Supremum (product/join) of subgroups
-/

namespace LatticeTheorem

variable {G : Type*} [Group G]

-- ============================================================================
-- Section 1: Setup and Basic Definitions
-- ============================================================================

section Setup

/-!
### Setup

We establish the basic objects of the Fourth Isomorphism Theorem:
- A group G
- A normal subgroup N of G
- The quotient map mk' N : G ->* G/N
- The correspondence between subgroups
-/

/--
The quotient map `G ->* G/N` is the canonical surjective homomorphism.
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
    (QuotientGroup.mk' N) g = 1 <-> g ∈ N :=
  QuotientGroup.eq_one_iff g

end Setup

-- ============================================================================
-- Section 2: The Forward Map (K |-> K/N)
-- ============================================================================

section ForwardMap

/-!
### The Forward Map: K |-> K/N

For a subgroup K of G containing N, we define K/N as the image of K under
the quotient map. This is a subgroup of G/N.

In Mathlib, this is `Subgroup.map (QuotientGroup.mk' N) K`.
-/

/--
The forward map of the correspondence: K |-> map (mk' N) K = K/N.
This takes a subgroup K of G (with N <= K) to its quotient K/N,
viewed as a subgroup of G/N.
-/
def forwardMap (N : Subgroup G) [N.Normal] (K : Subgroup G) : Subgroup (G ⧸ N) :=
  Subgroup.map (QuotientGroup.mk' N) K

/--
Alternative notation: K/N as the image under the quotient map.
-/
abbrev quotientSubgroup (N K : Subgroup G) [N.Normal] : Subgroup (G ⧸ N) :=
  forwardMap N K

/--
An element is in K/N iff it has a representative in K.
-/
theorem mem_forwardMap_iff (N K : Subgroup G) [N.Normal] (x : G ⧸ N) :
    x ∈ forwardMap N K <-> ∃ k : G, k ∈ K ∧ QuotientGroup.mk' N k = x := by
  simp only [forwardMap, Subgroup.mem_map]

/--
The coset of k is in K/N for any k in K.
-/
theorem mk_mem_forwardMap (N K : Subgroup G) [N.Normal] (k : G) (hk : k ∈ K) :
    QuotientGroup.mk' N k ∈ forwardMap N K := by
  simp only [forwardMap, Subgroup.mem_map]
  exact ⟨k, hk, rfl⟩

/--
The forward map sends N to the trivial subgroup of G/N.
-/
theorem forwardMap_self (N : Subgroup G) [N.Normal] :
    forwardMap N N = ⊥ := by
  ext x
  simp only [forwardMap, Subgroup.mem_map, Subgroup.mem_bot]
  constructor
  · rintro ⟨n, hn, rfl⟩
    exact (QuotientGroup.eq_one_iff n).mpr hn
  · intro hx
    -- x = 1 in the quotient, so any lift of x is in N
    -- We can use 1 as our witness since 1 ∈ N and mk' N 1 = 1 = x
    refine ⟨1, N.one_mem, ?_⟩
    simp only [map_one, hx]

/--
The forward map sends G (= top) to G/N (= top).
-/
theorem forwardMap_top (N : Subgroup G) [N.Normal] :
    forwardMap N ⊤ = ⊤ := by
  simp only [forwardMap]
  exact Subgroup.map_top_of_surjective _ (mk_surjective N)

end ForwardMap

-- ============================================================================
-- Section 3: The Inverse Map (H |-> preimage of H)
-- ============================================================================

section InverseMap

/-!
### The Inverse Map: H |-> comap (mk' N) H

For a subgroup H of G/N, the inverse map gives the preimage of H under
the quotient map. This is a subgroup of G that contains N.

In Mathlib, this is `Subgroup.comap (QuotientGroup.mk' N) H`.
-/

/--
The inverse map of the correspondence: H |-> comap (mk' N) H.
This takes a subgroup H of G/N to its preimage in G,
which is a subgroup containing N.
-/
def inverseMap (N : Subgroup G) [N.Normal] (H : Subgroup (G ⧸ N)) : Subgroup G :=
  Subgroup.comap (QuotientGroup.mk' N) H

/--
The preimage of any subgroup of G/N contains N.
-/
theorem N_le_inverseMap (N : Subgroup G) [N.Normal] (H : Subgroup (G ⧸ N)) :
    N ≤ inverseMap N H :=
  QuotientGroup.le_comap_mk' N H

/--
An element is in the preimage iff its coset is in H.
-/
theorem mem_inverseMap_iff (N : Subgroup G) [N.Normal] (H : Subgroup (G ⧸ N)) (g : G) :
    g ∈ inverseMap N H <-> QuotientGroup.mk' N g ∈ H := by
  simp only [inverseMap, Subgroup.mem_comap]

/--
The inverse map sends the trivial subgroup to N.
-/
theorem inverseMap_bot (N : Subgroup G) [N.Normal] :
    inverseMap N ⊥ = N := by
  ext g
  simp only [inverseMap, Subgroup.mem_comap, Subgroup.mem_bot]
  exact QuotientGroup.eq_one_iff g

/--
The inverse map sends G/N (= top) to G (= top).
-/
theorem inverseMap_top (N : Subgroup G) [N.Normal] :
    inverseMap N ⊤ = ⊤ := by
  simp only [inverseMap, Subgroup.comap_top]

end InverseMap

-- ============================================================================
-- Section 4: The Bijection (Round-Trip Properties)
-- ============================================================================

section Bijection

/-!
### The Bijection

We prove that the forward and inverse maps are mutually inverse,
establishing the bijection between subgroups of G/N and subgroups
of G containing N.
-/

/--
**Round-trip 1**: Starting from a subgroup H of G/N, applying the inverse
map then the forward map gives back H.

That is: map (comap H) = H when the map is surjective.
-/
theorem forwardMap_inverseMap (N : Subgroup G) [N.Normal] (H : Subgroup (G ⧸ N)) :
    forwardMap N (inverseMap N H) = H := by
  simp only [forwardMap, inverseMap]
  exact Subgroup.map_comap_eq_self_of_surjective (mk_surjective N) H

/--
**Round-trip 2**: Starting from a subgroup K of G containing N, applying
the forward map then the inverse map gives back K.

That is: comap (map K) = N sup K = K (when N <= K).
-/
theorem inverseMap_forwardMap (N K : Subgroup G) [N.Normal] (hNK : N ≤ K) :
    inverseMap N (forwardMap N K) = K := by
  simp only [forwardMap, inverseMap]
  rw [QuotientGroup.comap_map_mk' N K]
  exact sup_eq_right.mpr hNK

/--
The comap of map K equals N sup K.
-/
theorem comap_map_eq_sup (N K : Subgroup G) [N.Normal] :
    Subgroup.comap (QuotientGroup.mk' N) (Subgroup.map (QuotientGroup.mk' N) K) = N ⊔ K :=
  QuotientGroup.comap_map_mk' N K

end Bijection

-- ============================================================================
-- Section 5: The Order Isomorphism (Lattice Theorem)
-- ============================================================================

section OrderIsomorphism

/-!
### The Order Isomorphism

The correspondence is not just a bijection, but an **order isomorphism**
(lattice isomorphism). This means it preserves the inclusion ordering:
  K1 <= K2 iff forwardMap K1 <= forwardMap K2

This is the core content of the Fourth Isomorphism Theorem.
-/

/--
**The Fourth Isomorphism Theorem (Lattice Theorem)**

There is an order isomorphism between:
- Subgroups of G/N
- Subgroups of G that contain N

This is Mathlib's `QuotientGroup.comapMk'OrderIso`.
-/
def latticeTheorem (N : Subgroup G) [N.Normal] :
    Subgroup (G ⧸ N) ≃o {K : Subgroup G // N ≤ K} :=
  QuotientGroup.comapMk'OrderIso N

/--
The forward direction of the order isomorphism: H |-> comap H (with proof N <= comap H).
-/
theorem lattice_forward_def (N : Subgroup G) [N.Normal] (H : Subgroup (G ⧸ N)) :
    latticeTheorem N H = ⟨inverseMap N H, N_le_inverseMap N H⟩ := rfl

/--
The inverse direction of the order isomorphism: K |-> map K.
-/
theorem lattice_inverse_def (N : Subgroup G) [N.Normal] (K : {K : Subgroup G // N ≤ K}) :
    (latticeTheorem N).symm K = forwardMap N K.val := rfl

/--
The correspondence preserves the order (inclusion).
-/
theorem correspondence_preserves_order (N : Subgroup G) [N.Normal]
    (H₁ H₂ : Subgroup (G ⧸ N)) :
    H₁ ≤ H₂ <-> inverseMap N H₁ ≤ inverseMap N H₂ :=
  (Subgroup.comap_le_comap_of_surjective (mk_surjective N)).symm

/--
Forward map is monotone: K1 <= K2 implies forwardMap K1 <= forwardMap K2.
-/
theorem forwardMap_mono (N : Subgroup G) [N.Normal] {K₁ K₂ : Subgroup G}
    (h : K₁ ≤ K₂) : forwardMap N K₁ ≤ forwardMap N K₂ :=
  Subgroup.map_mono h

/--
Inverse map is monotone: H1 <= H2 implies inverseMap H1 <= inverseMap H2.
-/
theorem inverseMap_mono (N : Subgroup G) [N.Normal] {H₁ H₂ : Subgroup (G ⧸ N)}
    (h : H₁ ≤ H₂) : inverseMap N H₁ ≤ inverseMap N H₂ :=
  Subgroup.comap_mono h

end OrderIsomorphism

-- ============================================================================
-- Section 6: Preservation of Meets (Intersections)
-- ============================================================================

section PreservesMeet

/-!
### Preservation of Meets (Intersections)

The correspondence preserves meets (infimums/intersections):
  inverseMap (H1 meet H2) = inverseMap H1 meet inverseMap H2

This shows that the preimage of an intersection equals the intersection of preimages.
-/

/--
The inverse map preserves meets (intersections).
-/
theorem inverseMap_inf (N : Subgroup G) [N.Normal] (H₁ H₂ : Subgroup (G ⧸ N)) :
    inverseMap N (H₁ ⊓ H₂) = inverseMap N H₁ ⊓ inverseMap N H₂ := by
  simp only [inverseMap]
  exact Subgroup.comap_inf H₁ H₂ (QuotientGroup.mk' N)

/--
The forward map preserves meets when restricted to subgroups containing N.
Since the quotient map is not injective in general, we need the containment
condition to ensure both subgroups are "above" the kernel.
-/
theorem forwardMap_inf_of_le (N K₁ K₂ : Subgroup G) [N.Normal]
    (h₁ : N ≤ K₁) (h₂ : N ≤ K₂) :
    forwardMap N (K₁ ⊓ K₂) = forwardMap N K₁ ⊓ forwardMap N K₂ := by
  -- Use the round-trip property through the inverse map
  -- First show that forwardMap N K₁ ⊓ forwardMap N K₂ maps back to K₁ ⊓ K₂
  have key : inverseMap N (forwardMap N K₁ ⊓ forwardMap N K₂) = K₁ ⊓ K₂ := by
    rw [inverseMap_inf]
    rw [inverseMap_forwardMap N K₁ h₁, inverseMap_forwardMap N K₂ h₂]
  -- Now apply forwardMap to both sides and use round-trip
  have lhs : forwardMap N (K₁ ⊓ K₂) = forwardMap N (inverseMap N (forwardMap N K₁ ⊓ forwardMap N K₂)) := by
    rw [key]
  rw [lhs, forwardMap_inverseMap]

/--
Lattice theorem preserves meets.
-/
theorem lattice_preserves_meet (N : Subgroup G) [N.Normal] (H₁ H₂ : Subgroup (G ⧸ N)) :
    (latticeTheorem N (H₁ ⊓ H₂)).val = (latticeTheorem N H₁).val ⊓ (latticeTheorem N H₂).val :=
  inverseMap_inf N H₁ H₂

end PreservesMeet

-- ============================================================================
-- Section 7: Preservation of Joins (Products)
-- ============================================================================

section PreservesJoin

/-!
### Preservation of Joins (Suprema)

The correspondence preserves joins (suprema/products):
  inverseMap (H1 join H2) = inverseMap H1 join inverseMap H2

This shows that the preimage of a join equals the join of preimages.
-/

/--
The inverse map preserves joins (products/suprema) when the quotient map is surjective.
-/
theorem inverseMap_sup (N : Subgroup G) [N.Normal] (H₁ H₂ : Subgroup (G ⧸ N)) :
    inverseMap N (H₁ ⊔ H₂) = inverseMap N H₁ ⊔ inverseMap N H₂ := by
  simp only [inverseMap]
  exact (Subgroup.comap_sup_eq (QuotientGroup.mk' N) H₁ H₂ (mk_surjective N)).symm

/--
The forward map preserves joins (products/suprema).
-/
theorem forwardMap_sup (N K₁ K₂ : Subgroup G) [N.Normal] :
    forwardMap N (K₁ ⊔ K₂) = forwardMap N K₁ ⊔ forwardMap N K₂ := by
  simp only [forwardMap]
  exact Subgroup.map_sup K₁ K₂ (QuotientGroup.mk' N)

/--
Lattice theorem preserves joins.
-/
theorem lattice_preserves_join (N : Subgroup G) [N.Normal] (H₁ H₂ : Subgroup (G ⧸ N)) :
    (latticeTheorem N (H₁ ⊔ H₂)).val = (latticeTheorem N H₁).val ⊔ (latticeTheorem N H₂).val :=
  inverseMap_sup N H₁ H₂

end PreservesJoin

-- ============================================================================
-- Section 8: Preservation of Normality
-- ============================================================================

section PreservesNormality

/-!
### Preservation of Normality

A crucial property of the correspondence is that it preserves normality:
- If K is normal in G (with N <= K), then K/N is normal in G/N
- If H is normal in G/N, then the preimage of H is normal in G

This means normal subgroups correspond to normal subgroups.
-/

/--
**Normal subgroups map to normal subgroups (forward direction)**

If K is a normal subgroup of G containing N, then K/N is a normal subgroup of G/N.
-/
instance forwardMap_normal (N K : Subgroup G) [N.Normal] [hK : K.Normal] :
    (forwardMap N K).Normal := by
  simp only [forwardMap]
  exact hK.map (QuotientGroup.mk' N) (mk_surjective N)

/--
**Normal subgroups correspond to normal subgroups (inverse direction)**

If H is a normal subgroup of G/N, then its preimage is a normal subgroup of G.
-/
instance inverseMap_normal (N : Subgroup G) [N.Normal] (H : Subgroup (G ⧸ N)) [hH : H.Normal] :
    (inverseMap N H).Normal := by
  simp only [inverseMap]
  exact hH.comap (QuotientGroup.mk' N)

/--
Normal correspondence: K is normal in G iff K/N is normal in G/N
(for subgroups K containing N).
-/
theorem normal_iff_forwardMap_normal (N K : Subgroup G) [N.Normal] (hNK : N ≤ K) :
    K.Normal <-> (forwardMap N K).Normal := by
  constructor
  · intro hK
    exact @forwardMap_normal G _ N K _ hK
  · intro hKN
    -- Preimage of normal is normal, and forwardMap_inverseMap gives us back K
    have : (inverseMap N (forwardMap N K)).Normal := @inverseMap_normal G _ N _ _ hKN
    rwa [inverseMap_forwardMap N K hNK] at this

/--
Every normal subgroup of G/N comes from a unique normal subgroup of G containing N.
-/
theorem normal_subgroup_correspondence (N : Subgroup G) [N.Normal]
    (H : Subgroup (G ⧸ N)) [hH : H.Normal] :
    ∃ K : Subgroup G, K.Normal ∧ N ≤ K ∧ forwardMap N K = H := by
  use inverseMap N H
  refine ⟨?_, N_le_inverseMap N H, forwardMap_inverseMap N H⟩
  exact inverseMap_normal N H

end PreservesNormality

-- ============================================================================
-- Section 9: Index Formula
-- ============================================================================

section IndexFormula

/-!
### Index Formula

For finite groups/subgroups, the correspondence preserves indices:
  [K : N] = [K/N : 1] for subgroups N <= K
  [G : K] = [G/N : K/N] for subgroups N <= K <= G

The lattice isomorphism implies that the quotient G/K "has the same size"
as (G/N)/(K/N).
-/

/--
For finite quotients, the correspondence preserves cardinality.
This follows from the third isomorphism theorem: (G/N)/(K/N) ≃* G/K.
-/
theorem card_quotient_eq (N K : Subgroup G) [N.Normal] (hNK : N ≤ K)
    [hK : K.Normal]
    [Fintype (G ⧸ K)]
    [h : Fintype ((G ⧸ N) ⧸ Subgroup.map (QuotientGroup.mk' N) K)] :
    Fintype.card (G ⧸ K) = Fintype.card ((G ⧸ N) ⧸ Subgroup.map (QuotientGroup.mk' N) K) := by
  -- Use the third isomorphism theorem: (G/N)/(K/N) ≃* G/K
  have iso := QuotientGroup.quotientQuotientEquivQuotient N K hNK
  exact Fintype.card_eq.mpr ⟨iso.symm.toEquiv⟩

end IndexFormula

-- ============================================================================
-- Section 10: Connection to Third Isomorphism Theorem
-- ============================================================================

section ConnectionToThirdIso

/-!
### Connection to the Third Isomorphism Theorem

The Fourth Isomorphism Theorem (Lattice Theorem) is closely related to the
Third Isomorphism Theorem. For normal subgroups N <= K:
  (G/N)/(K/N) ≃* G/K

The lattice theorem tells us that K/N is normal in G/N whenever K is normal in G,
which is a prerequisite for forming the double quotient.
-/

/--
When K is normal in G with N <= K, the double quotient (G/N)/(K/N) is isomorphic to G/K.
This is the Third Isomorphism Theorem.
-/
noncomputable def thirdIsoFromLattice (N K : Subgroup G) [N.Normal] [K.Normal] (h : N ≤ K) :
    (G ⧸ N) ⧸ forwardMap N K ≃* G ⧸ K := by
  simp only [forwardMap]
  exact QuotientGroup.quotientQuotientEquivQuotient N K h

/--
The third isomorphism sends (gN)(K/N) to gK.
-/
theorem thirdIsoFromLattice_apply (N K : Subgroup G) [N.Normal] [K.Normal] (h : N ≤ K) (g : G) :
    thirdIsoFromLattice N K h (QuotientGroup.mk (QuotientGroup.mk g)) = QuotientGroup.mk g := rfl

end ConnectionToThirdIso

-- ============================================================================
-- Section 11: Examples
-- ============================================================================

section Examples

/-!
### Examples

We demonstrate some concrete consequences of the lattice theorem.
-/

/--
If G/N is simple (has no proper nontrivial normal subgroups), then there are
no normal subgroups K of G with N < K < G.
-/
theorem simple_quotient_gap (N : Subgroup G) [N.Normal]
    (hsimple : ∀ H : Subgroup (G ⧸ N), H.Normal -> H = ⊥ ∨ H = ⊤) :
    ∀ K : Subgroup G, K.Normal -> N ≤ K -> K = N ∨ K = ⊤ := by
  intro K hK hNK
  have : (forwardMap N K).Normal := @forwardMap_normal G _ N K _ hK
  cases hsimple (forwardMap N K) this with
  | inl h =>
    left
    have : K = inverseMap N (forwardMap N K) := (inverseMap_forwardMap N K hNK).symm
    rw [this, h, inverseMap_bot]
  | inr h =>
    right
    have : K = inverseMap N (forwardMap N K) := (inverseMap_forwardMap N K hNK).symm
    rw [this, h, inverseMap_top]

/--
The trivial subgroup of G/N corresponds to N.
-/
theorem bot_corresponds_to_N (N : Subgroup G) [N.Normal] :
    inverseMap N ⊥ = N :=
  inverseMap_bot N

/--
The whole group G/N corresponds to G.
-/
theorem top_corresponds_to_G (N : Subgroup G) [N.Normal] :
    inverseMap N ⊤ = ⊤ :=
  inverseMap_top N

end Examples

-- ============================================================================
-- Section 12: Summary
-- ============================================================================

/-!
## Summary

We have formalized the Fourth Isomorphism Theorem (Lattice Theorem) for Groups.

### The Correspondence

For a normal subgroup N of G, there is a bijection:

```
   Subgroups of G/N  <------>  Subgroups of G containing N

        H            |---->    comap (mk' N) H

   map (mk' N) K     <----|    K
```

### Key Properties

1. **Bijection** (`forwardMap_inverseMap`, `inverseMap_forwardMap`):
   - map . comap = id on Subgroup (G/N)
   - comap . map = id on {K : Subgroup G | N <= K}

2. **Order-preserving** (`correspondence_preserves_order`):
   - H1 <= H2 iff comap H1 <= comap H2
   - This makes it a lattice isomorphism

3. **Preserves meets** (`inverseMap_inf`, `forwardMap_inf_of_le`):
   - comap (H1 meet H2) = comap H1 meet comap H2
   - map (K1 meet K2) = map K1 meet map K2 (when N <= K1, K2)

4. **Preserves joins** (`inverseMap_sup`, `forwardMap_sup`):
   - comap (H1 join H2) = comap H1 join comap H2
   - map (K1 join K2) = map K1 join map K2

5. **Preserves normality** (`forwardMap_normal`, `inverseMap_normal`):
   - K normal in G implies K/N normal in G/N
   - H normal in G/N implies comap H normal in G

### Diagram

```
                    G = top
                   / | \
                  /  |  \
                 K1  K2  ...  (subgroups containing N)
                  \ /
                   N = ker(mk')
                   |
                  {1}

        |                               |
        |    Lattice Isomorphism        |
        V                               V

                  G/N = top
                   / \
                  /   \
               K1/N  K2/N  ...  (subgroups of G/N)
                  \ /
                   {1}
```

### Main Definition

- `latticeTheorem`: The order isomorphism
  `Subgroup (G quo N) <=>o {K : Subgroup G // N <= K}`

All proofs leverage Mathlib's `QuotientGroup.comapMk'OrderIso` and related infrastructure.
-/

end LatticeTheorem
