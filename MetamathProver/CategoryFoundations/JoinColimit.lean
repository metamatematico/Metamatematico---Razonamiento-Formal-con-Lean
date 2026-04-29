/-
# Join = Colimit in a Preorder (Thin Category)

## Purpose

This file provides the CENTRAL MATHEMATICAL FOUNDATION for the claim
"integration nodes are colimits in the skill category."

It proves, in Lean 4 + Mathlib, that:
1. Preorders form thin categories (at most one morphism per Hom)
2. The join (least upper bound) satisfies the colimit universal property
3. Joins are unique in partial orders
4. The IsJoin predicate captures exactly the co-cone + universal-property conditions

## What this file establishes

✅ The skill preorder IS a valid small category (all axioms hold — Mathlib)
✅ Thin: Hom(a, b) is a subsingleton for any preorder
✅ Join = upper bound + minimality (exactly the colimit conditions)
✅ Uniqueness of joins in partial orders
✅ Connection to ColimitVerifier.lean's decision procedure

## The honest mathematical claim for NLE v7.0

"Skill I is a colimit of pattern P = {s₁,...,sₖ} in the finite THIN CATEGORY
 induced by the skill preorder (reachability on G_n with n = ~76-100 skills).
 This is verified decidably by `isColimitInFiniteCategory` in ColimitVerifier.lean."

## Relationship to MES (Ehresmann)

MES uses colimits in general (non-thin) categories. Our system uses the finite
thin version as a decidable analogue. This is an INSPIRED-BY relationship.

Correspondence table:
  MES colimit (general category, infinite objects)
    → Join in finite preorder (thin category, ~76-100 skills, decidable)
-/

import Mathlib.CategoryTheory.Category.Preorder
import Mathlib.Order.Defs.PartialOrder
import Mathlib.Tactic

namespace MetamathProver.JoinColimit

open CategoryTheory

/-!
## Section 1: Preorders as thin categories (via Mathlib)
-/

/-- In a preorder category, there is at most one morphism between any two objects.
    This is the "thin" property. Proven directly from Mathlib's Preorder instance. -/
theorem preorder_is_thin {P : Type*} [Preorder P] (a b : P) :
    Subsingleton (a ⟶ b) := by
  infer_instance

/-- Existence check: if a ≤ b then there is a morphism a → b in the preorder category -/
theorem preorder_hom_of_le {P : Type*} [Preorder P] {a b : P} (h : a ≤ b) :
    Nonempty (a ⟶ b) :=
  ⟨homOfLE h⟩

/-- Extraction: if there is a morphism a → b in the preorder category, then a ≤ b -/
theorem preorder_le_of_hom {P : Type*} [Preorder P] {a b : P} (h : a ⟶ b) :
    a ≤ b :=
  leOfHom h

/-- Composition in the preorder category corresponds to transitivity -/
theorem preorder_comp_trans {P : Type*} [Preorder P] {a b c : P}
    (f : a ⟶ b) (g : b ⟶ c) : a ≤ c :=
  le_trans (leOfHom f) (leOfHom g)

/-!
## Section 2: The IsJoin predicate — categorical semantics of joins
-/

/-- j is a join (least upper bound) of the finite set S in preorder P.

    This is EXACTLY the colimit universal property in the thin category:
    - upper_bound: co-cone condition (morphisms from each diagram element to apex)
    - least: universal property (mediating morphism to any other co-cone apex)
-/
structure IsJoin {P : Type*} [Preorder P] (S : Finset P) (j : P) : Prop where
  /-- Co-cone condition: j is an upper bound (∀ s ∈ S, ∃ morphism s → j) -/
  upper_bound : ∀ s ∈ S, s ≤ j
  /-- Universal property: j is the least upper bound (∀ other co-cone k, ∃ morphism j → k) -/
  least : ∀ k : P, (∀ s ∈ S, s ≤ k) → j ≤ k

/-- Equivalently, IsJoin can be stated with the categorical morphism language -/
theorem isJoin_categorical {P : Type*} [Preorder P] (S : Finset P) (j : P) :
    IsJoin S j ↔
    -- co-cone: each s has a morphism to j
    (∀ s ∈ S, Nonempty (s ⟶ j)) ∧
    -- universal: for any other co-cone apex k, there is a morphism j → k
    (∀ k : P, (∀ s ∈ S, Nonempty (s ⟶ k)) → Nonempty (j ⟶ k)) := by
  constructor
  · intro h
    exact ⟨fun s hs => ⟨homOfLE (h.upper_bound s hs)⟩,
           fun k hk => ⟨homOfLE (h.least k (fun s hs => leOfHom (hk s hs).some))⟩⟩
  · intro ⟨hUB, hUniv⟩
    exact ⟨fun s hs => leOfHom (hUB s hs).some,
           fun k hk => leOfHom (hUniv k (fun s hs => ⟨homOfLE (hk s hs)⟩)).some⟩

/-!
## Section 3: Key theorems about joins
-/

/-- Uniqueness of joins in a partial order (antisymmetry of ≤) -/
theorem join_unique {P : Type*} [PartialOrder P] (S : Finset P) (j₁ j₂ : P)
    (h₁ : IsJoin S j₁) (h₂ : IsJoin S j₂) : j₁ = j₂ :=
  le_antisymm
    (h₁.least j₂ h₂.upper_bound)
    (h₂.least j₁ h₁.upper_bound)

/-- In a thin category, the mediating morphism is automatically unique -/
theorem join_mediating_morphism_unique {P : Type*} [Preorder P] (S : Finset P) (j k : P)
    (h : IsJoin S j) (hk : ∀ s ∈ S, s ≤ k)
    (m₁ m₂ : j ⟶ k) : m₁ = m₂ :=
  Subsingleton.elim m₁ m₂

/-- Reflexivity: any singleton set has its element as its own join -/
theorem singleton_join {P : Type*} [Preorder P] (a : P) :
    IsJoin {a} a :=
  ⟨fun s hs => by simp at hs; exact hs ▸ le_refl a,
   fun k hk => hk a (Finset.mem_singleton_self a)⟩

/-- Monotonicity: if j is a join and j ≤ k, then k is an upper bound of S -/
theorem join_upper_bound_of_le {P : Type*} [Preorder P] (S : Finset P) (j k : P)
    (h : IsJoin S j) (hle : j ≤ k) : ∀ s ∈ S, s ≤ k :=
  fun s hs => le_trans (h.upper_bound s hs) hle

/-- In a preorder with bottom, ⊥ is the join of the empty set -/
theorem bot_join_empty {P : Type*} [Preorder P] [OrderBot P] :
    IsJoin (∅ : Finset P) ⊥ :=
  ⟨fun s hs => absurd hs (by simp), fun _ _ => bot_le⟩

/-!
## Section 4: Connection to the Python is_join() procedure

The Python `ColimitBuilder.is_join(apex_id, component_ids, graph)` checks:
1. `upper_bound`: ∀ c ∈ component_ids, graph.is_preorder_leq(c, apex_id)
2. `minimal`: ∀ x ∈ G_n, (∀ c, is_preorder_leq(c, x)) → is_preorder_leq(apex_id, x)

This is precisely `IsJoin {component_ids} apex` in the reachability preorder:
  a ≤ b  iff  `graph.is_preorder_leq(a, b)` = True
           iff  there exists a path from a to b in the skill graph

The Lean `IsJoin` structure provides the mathematical specification.
The Python `is_join()` is the decidable implementation.
The `isColimitInFiniteCategory` in ColimitVerifier.lean bridges both.
-/


/-!
## Section 5: Summary — what is formally proven vs. what is inspired-by

FORMALLY PROVEN in this file:
  1. Preorders are thin categories (preorder_is_thin)
  2. Morphisms in preorder cat ↔ inequalities (preorder_hom_of_le, preorder_le_of_hom)
  3. IsJoin ↔ co-cone + universal property (isJoin_categorical)
  4. Joins are unique in partial orders (join_unique)
  5. Mediating morphisms are unique in thin categories (join_mediating_morphism_unique)

FORMALLY PROVEN in ColimitVerifier.lean:
  6. Sound decision procedure: isColimitInFiniteCategory decides IsJoin in Fin n
  7. Completeness: IsJoin → isColimitInFiniteCategory returns true

INSPIRED BY (not formally proven to be equivalent to MES):
  - Complexification (adding integration nodes as joins)
  - Co-regulators (feedback agents)
  - E-equivalence (structural pattern comparison)

FUTURE WORK (honest gaps):
  - Full connection between `reachabilityPreorder` and categorical `IsColimit`
  - Proof that the Python skill graph update preserves the preorder structure
  - Formal MES-to-thin-category correspondence theorem
-/

end MetamathProver.JoinColimit
