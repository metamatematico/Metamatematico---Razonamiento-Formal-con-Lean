/-
# Colimit Verifier — Finite Decidable Universal Property

## The key mathematical insight

For a **finite category** (finite objects, finite morphisms), the universal property
of colimits is **decidable**: we can check ∀ co-cones X, ∃! mediating morphism
by enumerating all finite possibilities.

This file formalizes:
1. Reachability in a finite directed graph (transitive closure)
2. The co-cone condition (∀ diagram component d, ∃ morphism d → apex)
3. The full colimit universal property (∃! mediating morphism for every co-cone)
4. A decision procedure checking both existence AND uniqueness of the mediating map
5. A soundness statement connecting the decision procedure to the categorical definition

## Mathematical setting

We work with a **finite presented category** G_n = (V_n, E_n) where:
- V_n = Fin n  (n skills, indexed by natural numbers)
- E_n ⊆ V_n × V_n  (morphism_matrix[i][j] = there is a morphism i → j)
- Morphism composition = path composition
- The category is interpreted as a THIN CATEGORY (preorder):
    Hom(i, j) has at most one element (witnessed by reachability)

## Why the thin / preorder interpretation is correct

The Python `SkillCategory._morphism_pairs` dictionary stores at most ONE morphism
per (source, target) pair (later additions overwrite earlier ones). This means the
implementation already imposes a thin-category structure. The multiple MorphismKind
labels (dependency, analogy, translation) are LABELS on the unique morphism, not
genuinely distinct morphisms. Consequently, the correct categorical claim is:

  "The skill category is a finite PREORDER (thin category).
   Colimits in this preorder = JOINS (least upper bounds).
   Joins are decidable and formally verified here."
-/

import Mathlib.Data.Fin.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Data.Bool.Basic
import Mathlib.Tactic

namespace MetamathProver.ColimitVerifier

/-!
## Finite skill graph representation

n skills, morphism_matrix[i][j] = true iff there is a direct morphism i → j.
The identity morphisms (i → i) are implicit and always present.
-/

/-- A finite skill graph with n skills -/
structure FinSkillGraph (n : ℕ) where
  /-- morphism_matrix[i][j] = true iff there is a direct (non-identity) morphism i → j -/
  morphism_matrix : Fin n → Fin n → Bool
  /-- No self-loops in the base relation (identities are separate) -/
  no_self_loops : ∀ i, morphism_matrix i i = false

/-!
## Transitive closure (reachability)

`reachable G i j` = true iff there exists a finite path from i to j
(possibly of length 0, which only holds when i = j).

We compute reachability by iterating the adjacency relation n times:
the longest simple path in a graph of n nodes has at most n-1 edges.
-/

/-- Single-step or zero-step reachability -/
def FinSkillGraph.step {n : ℕ} (G : FinSkillGraph n) (i j : Fin n) : Bool :=
  i == j || G.morphism_matrix i j

/-- Reachability in at most `k` steps -/
def reach_in {n : ℕ} (G : FinSkillGraph n) (i j : Fin n) : ℕ → Bool
  | 0       => G.step i j
  | k + 1   => G.step i j ||
                Finset.univ.any (fun mid => G.morphism_matrix i mid && reach_in G mid j k)

/-- Full reachability: ∃ finite path i → j (includes i = j) -/
def FinSkillGraph.reachable {n : ℕ} (G : FinSkillGraph n) (i j : Fin n) : Bool :=
  reach_in G i j n

/-!
## Basic reachability properties
-/

theorem reachable_refl {n : ℕ} (G : FinSkillGraph n) (i : Fin n) :
    G.reachable i i = true := by
  simp [FinSkillGraph.reachable, reach_in, FinSkillGraph.step]

theorem reachable_of_edge {n : ℕ} (G : FinSkillGraph n) (i j : Fin n)
    (h : G.morphism_matrix i j = true) : G.reachable i j = true := by
  simp [FinSkillGraph.reachable, reach_in, FinSkillGraph.step, h]

/-!
## The preorder / thin-category interpretation

The reachability relation `G.reachable i j` defines a PREORDER on Fin n:
- Reflexive: by reachable_refl
- Transitive: if i can reach j and j can reach k, then i can reach k

In the induced thin category:
  Hom(i, j) = {tt}  if G.reachable i j = true
  Hom(i, j) = {}    otherwise

A CO-CONE over diagram D with apex X is: ∀ d ∈ D, G.reachable d X = true
A COLIMIT is the LEAST such X: ∀ Y, (∀ d ∈ D, G.reachable d Y) → G.reachable X Y
-/

/-!
## Co-cone condition
-/

/-- diagram is a list of "source" skills (the pattern components) -/
def isCocone {n : ℕ} (G : FinSkillGraph n)
    (diagram : List (Fin n))
    (apex : Fin n) : Bool :=
  diagram.all (fun d => G.reachable d apex)

/-!
## Universal property: existence AND uniqueness of mediating morphism

In the thin category, "mediating morphism X → Y" = G.reachable X Y.
Uniqueness is automatic in a thin category (at most one morphism between any two objects).

Therefore, for the thin-category / preorder interpretation:
  isColimit G diagram apex
  ⟺ apex is an upper bound of diagram  (co-cone)
    ∧ apex is the LEAST upper bound     (universal property = minimality)
-/

/-- apex is a colimit of diagram in the finite thin category G -/
def isColimitInFiniteCategory {n : ℕ} (G : FinSkillGraph n)
    (diagram : List (Fin n))
    (apex : Fin n) : Bool :=
  -- Condition 1: apex is a co-cone (upper bound)
  isCocone G diagram apex &&
  -- Condition 2: apex is the LEAST upper bound
  -- For every X that is also a co-cone, there must be a morphism apex → X
  -- In the thin category, this is exactly: G.reachable apex X = true
  Finset.univ.all (fun x =>
    !isCocone G diagram x ||   -- X is not a co-cone: no obligation
    G.reachable apex x          -- X is a co-cone: apex ≤ X (mediating morphism exists)
  )

/-!
## Note on uniqueness in thin categories

In a thin (preorder) category, there is AT MOST ONE morphism between any two objects.
Therefore the "∃!" (unique existence) condition reduces to "∃" — uniqueness is free.

This is the key mathematical simplification:
  In a general category: colimit requires ∃! mediating morphism
  In a thin category: colimit requires ∃ mediating morphism (uniqueness is automatic)

The Python code's uniqueness check in verify_universal_property (introduced in the
2026-04 fix) correctly filters multiple morphisms when the implementation deviates
from the thin-category model (e.g., if two morphism types are added between the same
pair of skills). The Lean check here is the MATHEMATICAL SPECIFICATION; the Python
check is the COMPUTATIONAL ENFORCEMENT.
-/

/-!
## Soundness theorem

If `isColimitInFiniteCategory G diagram apex = true`, then apex is a colimit
of `diagram` in the finite thin category defined by G.

In the preorder/thin-category setting, this means:
1. apex is an upper bound: ∀ d ∈ diagram, d ≤ apex
2. apex is the least upper bound: ∀ x, (∀ d ∈ diagram, d ≤ x) → apex ≤ x

We state and prove both conditions directly from the decision procedure.
-/

theorem colimit_is_upper_bound {n : ℕ} (G : FinSkillGraph n)
    (diagram : List (Fin n)) (apex : Fin n)
    (h : isColimitInFiniteCategory G diagram apex = true) :
    ∀ d ∈ diagram, G.reachable d apex = true := by
  simp [isColimitInFiniteCategory, isCocone, Bool.and_eq_true, List.all_iff_forall] at h
  exact h.1

theorem colimit_is_least_upper_bound {n : ℕ} (G : FinSkillGraph n)
    (diagram : List (Fin n)) (apex : Fin n)
    (h : isColimitInFiniteCategory G diagram apex = true) :
    ∀ x : Fin n, (∀ d ∈ diagram, G.reachable d x = true) → G.reachable apex x = true := by
  simp [isColimitInFiniteCategory, isCocone, Bool.and_eq_true,
        Finset.all_iff_forall, Bool.or_eq_true, Bool.not_eq_true'] at h
  intro x hx
  have := h.2 x
  simp [List.all_iff_forall, hx] at this
  exact this

/-!
## Completeness theorem

If apex is a join (least upper bound) of diagram in the preorder, then
`isColimitInFiniteCategory` returns true. This shows the procedure is complete.
-/

theorem join_implies_colimit {n : ℕ} (G : FinSkillGraph n)
    (diagram : List (Fin n)) (apex : Fin n)
    (hUB : ∀ d ∈ diagram, G.reachable d apex = true)
    (hLUB : ∀ x : Fin n, (∀ d ∈ diagram, G.reachable d x = true) → G.reachable apex x = true) :
    isColimitInFiniteCategory G diagram apex = true := by
  simp [isColimitInFiniteCategory, isCocone, Bool.and_eq_true,
        Finset.all_iff_forall, Bool.or_eq_true, Bool.not_eq_true', List.all_iff_forall]
  refine ⟨hUB, fun x => ?_⟩
  by_cases hxCone : ∀ d ∈ diagram, G.reachable d x = true
  · right; exact hLUB x hxCone
  · left; push_neg at hxCone; simp [List.all_iff_forall]; exact hxCone

/-!
## Summary

We have proven that for a FINITE THIN CATEGORY:
1. `isColimitInFiniteCategory` is a SOUND decision procedure (soundness theorems)
2. `isColimitInFiniteCategory` is a COMPLETE decision procedure (completeness theorem)
3. It checks BOTH conditions of the colimit universal property:
   - Co-cone (upper bound)
   - Minimality (least upper bound / mediating morphism exists)

The honest mathematical claim for the Python system is:
  "skill I is a colimit of pattern P in the finite thin category G_n of currently
   known skills" (where n = current number of skills, typically ~76-100)

This is verified decidably by `isColimitInFiniteCategory` above.
-/

end MetamathProver.ColimitVerifier
