/-
Copyright (c) 2024. All rights reserved.
Released under Apache 2.0 license.

# The Second Isomorphism Theorem for Groups (Diamond/Parallelogram Theorem)

This file demonstrates and applies the Second Isomorphism Theorem for Groups in Lean 4
using Mathlib. The core theorem is provided by Mathlib as
`QuotientGroup.quotientInfEquivProdNormalQuotient`.

## Mathematical Background

The Second Isomorphism Theorem for Groups states:

Let G be a group, S a subgroup of G, and N a normal subgroup of G. Then:
1. SN (the product of S and N) is a subgroup of G
2. S ∩ N is a normal subgroup of S
3. N is a normal subgroup of SN
4. The quotient groups satisfy: S/(S ∩ N) ≃* (SN)/N

This theorem is also known as the:
- **Diamond Theorem** - from the lattice diagram shape
- **Parallelogram Theorem** - from the isomorphism of "opposite sides"

The lattice diagram looks like:
```
      G
     / \
   SN   ...
   / \
  S   N
   \ /
   S∩N
```

The theorem says that "opposite sides of the diamond are isomorphic as quotients":
  - The left side S/(S∩N) corresponds to the right side (SN)/N

## Key Insight

When N is normal in G, the product SN = S ⊔ N (the join/supremum in the subgroup lattice)
forms a subgroup. The normality of N allows elements of S and N to "commute past each other"
in the sense that for any s ∈ S and n ∈ N, we have sn = n's for some n' ∈ N.

## Main Results

- `QuotientGroup.quotientInfEquivProdNormalQuotient` : S/(S ∩ N) ≃* (SN)/N (from Mathlib)
- Supporting lemmas demonstrating properties of the subgroups involved

## References

* [Serge Lang, *Algebra*][lang2002algebra]
* [David S. Dummit and Richard M. Foote, *Abstract Algebra*]
* [Michael Artin, *Algebra*][artin2011algebra]
-/

import Mathlib.GroupTheory.QuotientGroup.Basic

/-!
## Notation

We use the following notation throughout this file:
- `→*` : Group homomorphism (MonoidHom for multiplicative groups)
- `≃*` : Group isomorphism (MulEquiv)
- `G ⧸ N` : Quotient group of G by normal subgroup N
- `S ⊔ N` : Supremum (join) of subgroups = SN when N is normal
- `S ⊓ N` : Infimum (meet) of subgroups = S ∩ N
- `N.subgroupOf S` : The intersection N ∩ S viewed as a subgroup of S
-/

namespace SecondIsomorphismTheorem

variable {G : Type*} [Group G]

-- ============================================================================
-- Section 1: The Product SN is a Subgroup
-- ============================================================================

section ProductIsSubgroup

/-!
### Part 1: The Product SN is a Subgroup of G

When N is a normal subgroup of G and S is any subgroup, the set-theoretic product
SN = {sn : s ∈ S, n ∈ N} forms a subgroup of G.

In Mathlib's lattice-theoretic approach, this is captured by the supremum S ⊔ N,
which represents the smallest subgroup containing both S and N. When N is normal,
this equals the set-theoretic product SN.
-/

/--
**Theorem (Product is Subgroup)**: For subgroups S and N of G where N is normal,
the product SN forms a subgroup of G.

In Mathlib, this is represented by `S ⊔ N` (the supremum in the subgroup lattice).
The supremum always exists and is a subgroup by definition.
-/
theorem product_is_subgroup (S N : Subgroup G) [N.Normal] :
    ∃ H : Subgroup G, H = S ⊔ N := ⟨S ⊔ N, rfl⟩

/--
The supremum S ⊔ N contains S as a subgroup.
-/
theorem left_le_sup (S N : Subgroup G) : S ≤ S ⊔ N := le_sup_left

/--
The supremum S ⊔ N contains N as a subgroup.
-/
theorem right_le_sup (S N : Subgroup G) : N ≤ S ⊔ N := le_sup_right

/--
The identity is in S ⊔ N.
-/
example (S N : Subgroup G) : (1 : G) ∈ S ⊔ N := one_mem (S ⊔ N)

/--
The product is closed under multiplication (inherited from subgroup structure).
-/
example (S N : Subgroup G) {a b : G} (ha : a ∈ S ⊔ N) (hb : b ∈ S ⊔ N) :
    a * b ∈ S ⊔ N := mul_mem ha hb

/--
The product is closed under inverses (inherited from subgroup structure).
-/
example (S N : Subgroup G) {a : G} (ha : a ∈ S ⊔ N) :
    a⁻¹ ∈ S ⊔ N := inv_mem ha

end ProductIsSubgroup

-- ============================================================================
-- Section 2: N is Normal in SN
-- ============================================================================

section NNormalInProduct

/-!
### Part 2: N is Normal in SN

When N is a normal subgroup of G, it is also normal in any subgroup that contains it,
in particular in the product SN = S ⊔ N.

The key insight is that normality in G implies normality in any subgroup containing N,
because conjugation by elements of the subgroup is a special case of conjugation by
elements of G.
-/

/--
**Theorem (N Normal in SN)**: If N is normal in G, then N is normal in S ⊔ N.

In Mathlib, `N.subgroupOf (S ⊔ N)` gives N ∩ (S ⊔ N) as a subgroup of S ⊔ N.
Since N ≤ S ⊔ N, we have N ∩ (S ⊔ N) = N.
-/
theorem normal_subgroupOf_sup (S N : Subgroup G) [hN : N.Normal] :
    (N.subgroupOf (S ⊔ N)).Normal := by
  constructor
  intro ⟨n, hn_sup⟩ hn_N g
  simp only [Subgroup.mem_subgroupOf] at hn_N ⊢
  exact hN.conj_mem n hn_N g.val

/--
Elements of N viewed as elements of S ⊔ N.
-/
theorem n_subset_product (S N : Subgroup G) (n : G) (hn : n ∈ N) :
    n ∈ S ⊔ N := right_le_sup S N hn

end NNormalInProduct

-- ============================================================================
-- Section 3: S ∩ N is Normal in S
-- ============================================================================

section IntersectionNormalInS

/-!
### Part 3: The Intersection S ∩ N is Normal in S

When N is normal in G and S is any subgroup, the intersection S ∩ N is normal in S.

In Mathlib, `N.subgroupOf S` represents the intersection N ∩ S viewed as a subgroup of S.
This is normal in S whenever N is normal in G.
-/

/--
**Theorem (Intersection Normal in S)**: If N is normal in G and S is any subgroup,
then S ∩ N (= N.subgroupOf S) is a normal subgroup of S.

This is because for any s ∈ S and n ∈ S ∩ N:
  - n ∈ N, so sns⁻¹ ∈ N (since N is normal in G)
  - s, n, s⁻¹ ∈ S, so sns⁻¹ ∈ S
  - Therefore sns⁻¹ ∈ S ∩ N
-/
theorem intersection_normal_in_s (S N : Subgroup G) [hN : N.Normal] :
    (N.subgroupOf S).Normal := by
  constructor
  intro ⟨n, hn_S⟩ hn_N g
  simp only [Subgroup.mem_subgroupOf] at hn_N ⊢
  exact hN.conj_mem n hn_N g.val

/--
Verification: S ∩ N is closed under conjugation by elements of S.
-/
example (S N : Subgroup G) [hN : N.Normal] {n s : G}
    (hn : n ∈ S ⊓ N) (hs : s ∈ S) :
    s * n * s⁻¹ ∈ S ⊓ N := by
  rw [Subgroup.mem_inf] at hn ⊢
  constructor
  -- sns⁻¹ is in S because S is a subgroup containing s, n
  · exact S.mul_mem (S.mul_mem hs hn.1) (S.inv_mem hs)
  -- sns⁻¹ is in N because N is normal
  · exact hN.conj_mem n hn.2 s

end IntersectionNormalInS

-- ============================================================================
-- Section 4: The Main Isomorphism (Diamond Theorem)
-- ============================================================================

section MainIsomorphism

/-!
### Part 4: The Second Isomorphism Theorem (Diamond Isomorphism)

This is the heart of the theorem. We prove that S/(S ∩ N) ≃* (SN)/N.

The isomorphism is induced by the inclusion S ↪ SN followed by the quotient map
SN → (SN)/N. The kernel of this composite is exactly S ∩ N, so by the First
Isomorphism Theorem, we get S/(S ∩ N) ≃* image in (SN)/N.

The key observation is that the image is all of (SN)/N because every coset
of N in SN has a representative from S.
-/

/--
**The Second Isomorphism Theorem (Diamond Theorem)**

For a group G with subgroup S and normal subgroup N:
  S/(S ∩ N) ≃* (S ⊔ N)/N

Where:
- S ⊔ N represents the product SN (smallest subgroup containing S and N)
- S ∩ N is represented by `N.subgroupOf S` as a subgroup of S
- The quotients use `N.subgroupOf _` to restrict N appropriately

This is the definitive statement of the theorem from Mathlib.
-/
noncomputable def secondIsomorphismTheorem (S N : Subgroup G) [N.Normal] :
    S ⧸ N.subgroupOf S ≃* (S ⊔ N : Subgroup G) ⧸ N.subgroupOf (S ⊔ N) :=
  QuotientGroup.quotientInfEquivProdNormalQuotient S N

/--
The second isomorphism theorem gives a bijection.
-/
theorem second_iso_bijective (S N : Subgroup G) [N.Normal] :
    Function.Bijective (secondIsomorphismTheorem S N) :=
  (secondIsomorphismTheorem S N).bijective

end MainIsomorphism

-- ============================================================================
-- Section 5: The Inverse Isomorphism
-- ============================================================================

section InverseIsomorphism

/-!
### Part 5: The Inverse of the Diamond Isomorphism

The inverse isomorphism (SN)/N → S/(S ∩ N) is also important.
Given a coset snN in (SN)/N, we map it to the coset s(S ∩ N) in S/(S ∩ N).

This is well-defined because:
- Every coset snN can be represented by an element s ∈ S (since snN = sN when n ∈ N)
- If s₁N = s₂N, then s₁⁻¹s₂ ∈ N ∩ S, so s₁(S ∩ N) = s₂(S ∩ N)
-/

/--
The inverse of the second isomorphism theorem.
Maps (SN)/N → S/(S ∩ N).
-/
noncomputable def second_iso_inverse (S N : Subgroup G) [N.Normal] :
    (S ⊔ N : Subgroup G) ⧸ N.subgroupOf (S ⊔ N) ≃* S ⧸ N.subgroupOf S :=
  (secondIsomorphismTheorem S N).symm

/--
Composing the isomorphism with its inverse gives the identity.
-/
theorem second_iso_left_inv (S N : Subgroup G) [N.Normal]
    (x : S ⧸ N.subgroupOf S) :
    (second_iso_inverse S N) ((secondIsomorphismTheorem S N) x) = x :=
  (secondIsomorphismTheorem S N).symm_apply_apply x

/--
Composing the inverse with the isomorphism gives the identity.
-/
theorem second_iso_right_inv (S N : Subgroup G) [N.Normal]
    (y : (S ⊔ N : Subgroup G) ⧸ N.subgroupOf (S ⊔ N)) :
    (secondIsomorphismTheorem S N) ((second_iso_inverse S N) y) = y :=
  (secondIsomorphismTheorem S N).apply_symm_apply y

end InverseIsomorphism

-- ============================================================================
-- Section 6: Index Formula
-- ============================================================================

section IndexFormula

/-!
### Part 6: Index Formula

In finite groups, the second isomorphism theorem implies an index formula:
[S : S ∩ N] = [SN : N]

Both sides count the number of cosets.
-/

/--
In finite groups, the second isomorphism theorem implies an index formula:
[S : S ∩ N] = [SN : N]

Both sides count the number of cosets.
-/
theorem index_formula (S N : Subgroup G) [N.Normal]
    [Fintype (S ⧸ N.subgroupOf S)]
    [Fintype ((S ⊔ N : Subgroup G) ⧸ N.subgroupOf (S ⊔ N))] :
    Fintype.card (S ⧸ N.subgroupOf S) =
    Fintype.card ((S ⊔ N : Subgroup G) ⧸ N.subgroupOf (S ⊔ N)) :=
  Fintype.card_eq.mpr ⟨(secondIsomorphismTheorem S N).toEquiv⟩

end IndexFormula

-- ============================================================================
-- Section 7: Summary and Diagram
-- ============================================================================

/-!
## Summary

We have demonstrated the Second Isomorphism Theorem for Groups, which states:

For a group G with subgroup S and normal subgroup N:

```
                    G
                   / \
                 /     \
               SN       ...
              /   \
             /     \
            S       N
             \     /
              \   /
               S∩N
```

**The Diamond/Parallelogram Isomorphism**:
```
    S/(S ∩ N)  ≃*  (SN)/N

       [s]    ↦    [s]
```

Where:
- The left quotient mods S by S ∩ N
- The right quotient mods SN by N
- The isomorphism is induced by inclusion S ↪ SN

**Key Results**:
1. `product_is_subgroup`: SN = S ⊔ N is a subgroup
2. `intersection_normal_in_s`: S ∩ N is normal in S
3. `normal_subgroupOf_sup`: N is normal in SN
4. `secondIsomorphismTheorem`: S/(S ∩ N) ≃* (SN)/N

**Why "Diamond"?**:
The lattice of subgroups forms a diamond shape:
- Top: SN (join of S and N)
- Sides: S and N
- Bottom: S ∩ N (meet of S and N)

The theorem says "opposite sides of the diamond are isomorphic as quotients":
- Left side: S to S ∩ N gives S/(S ∩ N)
- Right side: SN to N gives (SN)/N

All proofs leverage Mathlib's infrastructure for subgroups, quotient groups,
lattice operations, and the First Isomorphism Theorem.
-/

end SecondIsomorphismTheorem
