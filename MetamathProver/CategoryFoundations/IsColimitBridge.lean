-- IsColimitBridge — Formal Bridge: IsJoin ↔ CategoryTheory.Limits.IsColimit
-- Imports must come first in Lean 4.
import Mathlib.CategoryTheory.Category.Preorder
import Mathlib.CategoryTheory.Limits.Cones
import Mathlib.CategoryTheory.Discrete.Basic
import MetamathProver.CategoryFoundations.JoinColimit
import Mathlib.Tactic

/-!
# IsColimitBridge — Formal Bridge: IsJoin ↔ CategoryTheory.Limits.IsColimit

## Purpose

This file closes the formal gap identified in the NLE v7.0 README:

> **"Conexión formal con `CategoryTheory.Limits.IsColimit` de Mathlib — Trabajo futuro"**

It proves — with **0 `sorry`** — that in any preorder `α` (viewed as a thin
category via Mathlib's `instCategoryPreorder`), the `IsJoin` predicate from
`JoinColimit.lean` is **equivalent** to Mathlib's categorical `IsColimit`.

## Main theorem (§V)

```
IsJoin S j  ↔  ∃ hub : ∀ s : ↥S, s.val ≤ j,
                 Nonempty (IsColimit (joinCocone S j hub))
```

(`IsColimit` is a `Type` in Mathlib, so we wrap it in `Nonempty` to stay in `Prop`.)

## Complete formal chain (0 sorry)

```
Python is_join(apex, pattern, graph)
    — decidable boolean
    ↕  soundness + completeness  (ColimitVerifier.lean)
isColimitInFiniteCategory G diagram apex = true
    — Bool in Fin n
    ↕  colimit_is_upper_bound / colimit_is_least_upper_bound / join_implies_colimit
IsJoin S apex                             ← gap was here
    — Prop: LUB in any preorder
    ↕  isJoin_iff_nonempty_isColimit  (§V, THIS FILE)
Nonempty (CategoryTheory.Limits.IsColimit (joinCocone S apex …))
    — Mathlib categorical colimit in the thin preorder category
```

## Mathematical setting

`Preorder α` → thin category via Mathlib's `instCategoryPreorder`.
Hom-sets `Hom a b = ULift (a ≤ b)` are subsingletons, so:
- `desc` is given by `homOfLE` + the LUB property.
- `fac` and `uniq` are free by `Subsingleton.elim`.
-/

namespace MetamathProver.IsColimitBridge

open CategoryTheory Limits MetamathProver.JoinColimit

variable {α : Type*} [Preorder α]

/-!
## §I. The pattern diagram

`patternDiagram S : Discrete ↥S ⥤ α` picks out each component of the pattern.
-/

/-- Discrete diagram of pattern `S` in the thin category `α`. -/
def patternDiagram (S : Finset α) : Discrete ↥S ⥤ α :=
  Discrete.functor (fun s : ↥S => s.val)

@[simp]
theorem patternDiagram_obj (S : Finset α) (s : ↥S) :
    (patternDiagram S).obj ⟨s⟩ = s.val := rfl

/-!
## §II. The join cocone

`joinCocone S j hub : Cocone (patternDiagram S)` has apex `j` and legs
`homOfLE (hub s) : s.val ⟶ j`.  Naturality is free (thin = subsingleton Hom-sets).
-/

/-- Cocone over `patternDiagram S` with apex `j`, given `j` is an upper bound. -/
def joinCocone (S : Finset α) (j : α) (hub : ∀ s : ↥S, s.val ≤ j) :
    Cocone (patternDiagram S) where
  pt := j
  ι  :=
    { app        := fun ⟨s⟩ => homOfLE (hub s)
      naturality := fun _ _ _ => Subsingleton.elim _ _ }

@[simp]
theorem joinCocone_pt (S : Finset α) (j : α) (hub : ∀ s : ↥S, s.val ≤ j) :
    (joinCocone S j hub).pt = j := rfl

/-!
## §III. IsJoin → IsColimit

The join cocone is a colimit.  All three fields reduce to subsingleton equalities.
-/

/-- Any cocone over `patternDiagram S` witnesses that its apex is an upper bound. -/
private theorem cocone_ub (S : Finset α) (c : Cocone (patternDiagram S))
    (x : α) (hx : x ∈ S) : x ≤ c.pt :=
  leOfHom (c.ι.app ⟨⟨x, hx⟩⟩)

/-- **IsJoin → IsColimit**: the join cocone is a categorical colimit. -/
def isColimit_of_isJoin (S : Finset α) (j : α) (h : IsJoin S j) :
    IsColimit (joinCocone S j (fun s => h.upper_bound s.val s.prop)) where
  desc  s   := homOfLE (h.least s.pt (cocone_ub S s))
  fac   _ _ := Subsingleton.elim _ _
  uniq  _ _ _ := Subsingleton.elim _ _

/-!
## §IV. IsColimit → IsJoin

A colimit apex is the least upper bound.
-/

/-- Auxiliary cocone with apex `k` built from an upper-bound proof. -/
private def ubCocone (S : Finset α) (k : α) (hk : ∀ x ∈ S, x ≤ k) :
    Cocone (patternDiagram S) where
  pt := k
  ι  :=
    { app        := fun ⟨s⟩ => homOfLE (hk s.val s.prop)
      naturality := fun _ _ _ => Subsingleton.elim _ _ }

/-- **IsColimit → IsJoin**: a colimit apex is the join of `S`. -/
theorem isJoin_of_isColimit (S : Finset α) (j : α)
    (hub : ∀ s : ↥S, s.val ≤ j)
    (h : IsColimit (joinCocone S j hub)) : IsJoin S j where
  upper_bound x hx := hub ⟨x, hx⟩
  least k hk       := leOfHom (h.desc (ubCocone S k hk))

/-!
## §V. Main equivalence — formal bridge  ✅ GAP CLOSED

`IsColimit` is a `Type` in Mathlib (it carries the actual mediating map as data),
so we use `Nonempty` to state the equivalence as a `Prop`-valued `↔`.
-/

/-- **MAIN THEOREM** — Formal bridge between `JoinColimit.lean` and Mathlib:

    In the thin category induced by a preorder,

    ```
    IsJoin S j  ↔  ∃ hub, Nonempty (CategoryTheory.Limits.IsColimit (joinCocone S j hub))
    ```

    Instantiate `α` with the reachability preorder on `Fin n` (the skill graph)
    to get the precise NLE v7.0 claim.

    **Gap closed**: "Conexión formal con `CategoryTheory.Limits.IsColimit` de Mathlib". -/
theorem isJoin_iff_nonempty_isColimit (S : Finset α) (j : α) :
    IsJoin S j ↔
    ∃ hub : ∀ s : ↥S, s.val ≤ j, Nonempty (IsColimit (joinCocone S j hub)) := by
  constructor
  · intro h
    exact ⟨fun s => h.upper_bound s.val s.prop,
           ⟨isColimit_of_isJoin S j h⟩⟩
  · rintro ⟨hub, ⟨hcol⟩⟩
    exact isJoin_of_isColimit S j hub hcol

/-- Convenience: constructive direction gives an actual `IsColimit` term.
    (`IsColimit` is a `Type`, not a `Prop`, so this is a `def`.) -/
def isJoin_gives_isColimit (S : Finset α) (j : α) (h : IsJoin S j) :
    IsColimit (joinCocone S j (fun s => h.upper_bound s.val s.prop)) :=
  isColimit_of_isJoin S j h

/-!
## §VI. Uniqueness of the colimit apex

In a partial order, two colimits of the same pattern have the same apex.
-/

/-- **Uniqueness**: colimit apex is unique in a partial order. -/
theorem isColimit_apex_unique {β : Type*} [PartialOrder β]
    (S : Finset β) (j₁ j₂ : β)
    (hub₁ : ∀ s : ↥S, s.val ≤ j₁)
    (hub₂ : ∀ s : ↥S, s.val ≤ j₂)
    (h₁ : IsColimit (joinCocone S j₁ hub₁))
    (h₂ : IsColimit (joinCocone S j₂ hub₂)) : j₁ = j₂ :=
  join_unique S j₁ j₂
    (isJoin_of_isColimit S j₁ hub₁ h₁)
    (isJoin_of_isColimit S j₂ hub₂ h₂)

/-!
## §VII. Summary

### Theorems proved in this file (0 sorry)

| Theorem | Statement |
|---------|-----------|
| `isJoin_iff_nonempty_isColimit` | `IsJoin S j ↔ ∃ hub, Nonempty (IsColimit (joinCocone S j hub))` |
| `isJoin_gives_isColimit` | Constructive: `IsJoin S j → IsColimit (joinCocone S j hub)` |
| `isJoin_of_isColimit` | `IsColimit (joinCocone S j hub) → IsJoin S j` |
| `isColimit_apex_unique` | Apex is unique in partial orders |

### The complete formal chain

```
ColimitVerifier.lean                IsColimitBridge.lean (this file)
────────────────────────────────    ──────────────────────────────────────
isColimitInFiniteCategory            isJoin_gives_isColimit /
  G diagram apex = true               isJoin_of_isColimit
    ↕ soundness/completeness              ↕
  IsJoin S apex            ←──────→  Nonempty (IsColimit (joinCocone S apex …))
  (in Bool / Fin n)                   (Mathlib categorical definition)
```

The gap **"Conexión formal con `CategoryTheory.Limits.IsColimit` de Mathlib"**
is now **formally closed** by `isJoin_iff_nonempty_isColimit`.
-/

end MetamathProver.IsColimitBridge
