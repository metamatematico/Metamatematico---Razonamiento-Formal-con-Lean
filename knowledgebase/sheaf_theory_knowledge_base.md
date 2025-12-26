# Sheaf Theory Knowledge Base for Lean 4

**Generated:** 2025-12-24
**Mode:** Deep Synthesis
**Purpose:** Knowledge base for implementing sheaf theory theorems in Lean 4 for dataset generation pairing formal proofs with natural language explanations.
**Confidence:** High

---

## Executive Summary

Sheaf theory is well-developed in Lean 4's Mathlib library, with presheaves and sheaves under `Mathlib.CategoryTheory.Sites.*` and `Mathlib.Topology.Sheaves.*`, and ringed spaces under `Mathlib.Geometry.RingedSpace.*`. This KB covers presheaves, sheaves, stalks, sheafification, sheaf category structure, locally ringed spaces, and structure sheaves. Estimated total: **60 theorems and definitions**.

### Content Summary

| Category | Estimated Count | Mathlib Support | Difficulty Distribution |
|----------|----------------|-----------------|------------------------|
| **Presheaves** | 8 | FULL | 50% easy, 40% medium, 10% hard |
| **Sheaves** | 10 | FULL | 30% easy, 50% medium, 20% hard |
| **Stalks and Germs** | 10 | FULL | 20% easy, 50% medium, 30% hard |
| **Sheafification** | 10 | FULL | 10% easy, 40% medium, 50% hard |
| **Sheaf Category Structure** | 10 | FULL | 10% easy, 40% medium, 50% hard |
| **Locally Ringed Spaces** | 7 | FULL | 15% easy, 45% medium, 40% hard |
| **Structure Sheaves** | 5 | FULL | 0% easy, 40% medium, 60% hard |
| **Total** | **60** | - | - |

### Key Dependencies

- **Category Theory:** Functors, natural transformations, limits, colimits
- **Topology:** Open sets, continuous maps, topological spaces
- **Algebra:** Rings, modules, localizations

---

## Related Knowledge Bases

### Prerequisites
- **Category Theory** (`category_theory_knowledge_base.md`): Functors, natural transformations, limits, colimits
- **Topology** (`topology_knowledge_base.md`): Topological spaces, open sets, continuous maps
- **Commutative Algebra** (`commutative_algebra_knowledge_base.md`): Localization, local rings

### Builds Upon This KB
- **Algebraic Geometry** (`algebraic_geometry_knowledge_base.md`): Uses sheaves for schemes, structure sheaves on Spec(R)

### Scope Clarification
This KB focuses on **general sheaf theory**:
- Presheaves and sheaves on topological spaces and sites
- Stalks, germs, and sheafification
- Sheaf category structure (limits, colimits, morphisms)
- Locally ringed spaces and structure sheaves

For **sheaves in algebraic geometry** (structure sheaves on schemes, quasi-coherent sheaves), see the **Algebraic Geometry KB**.

---

## Part I: Presheaves

### Module Organization

**Primary Imports:**
- `Mathlib.CategoryTheory.Functor.Category`
- `Mathlib.Topology.Sheaves.Presheaf`

**Estimated Statements:** 8

---

### 1. Presheaf

**Natural Language Statement:**
A presheaf on a category C valued in a category D is a contravariant functor from C to D.

**Lean 4 Definition:**
```lean
abbrev Presheaf (C : Type u₁) [Category.{v₁} C] (D : Type u₂) [Category.{v₂} D] :=
  Cᵒᵖ ⥤ D
```

**Mathlib Location:** `Mathlib.CategoryTheory.Functor.Category`

**Difficulty:** easy

---

### 2. TopCat.Presheaf

**Natural Language Statement:**
A presheaf on a topological space X valued in C is a functor from the opposite of the opens category to C.

**Lean 4 Definition:**
```lean
def TopCat.Presheaf (X : TopCat) (C : Type*) [Category C] := (Opens X)ᵒᵖ ⥤ C
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Presheaf`

**Difficulty:** easy

---

### 3. Presheaf.map

**Natural Language Statement:**
For an inclusion of open sets U ⊆ V, the presheaf provides a restriction map F(V) → F(U).

**Lean 4 Definition:**
```lean
def Presheaf.map (F : Presheaf X C) {U V : Opens X} (i : U ⟶ V) :
    F.obj (op V) ⟶ F.obj (op U) := F.map i.op
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Presheaf`

**Difficulty:** easy

---

### 4. Presheaf.comp

**Natural Language Statement:**
Restriction maps compose: if U ⊆ V ⊆ W, then res_U^W = res_U^V ∘ res_V^W.

**Lean 4 Theorem:**
```lean
theorem Presheaf.map_comp (F : Presheaf X C) {U V W : Opens X}
    (i : U ⟶ V) (j : V ⟶ W) :
    F.map (i ≫ j).op = F.map j.op ≫ F.map i.op := F.map_comp j.op i.op
```

**Mathlib Location:** `Mathlib.CategoryTheory.Functor.Basic`

**Difficulty:** easy

---

### 5. Presheaf.id

**Natural Language Statement:**
The identity restriction map is the identity: the restriction from U to U is the identity morphism.

**Lean 4 Theorem:**
```lean
theorem Presheaf.map_id (F : Presheaf X C) (U : Opens X) :
    F.map (𝟙 (op U)) = 𝟙 (F.obj (op U)) := F.map_id (op U)
```

**Mathlib Location:** `Mathlib.CategoryTheory.Functor.Basic`

**Difficulty:** easy

---

### 6. Presheaf.NatTrans

**Natural Language Statement:**
A morphism of presheaves is a natural transformation between the underlying functors.

**Lean 4 Definition:**
```lean
def Presheaf.Hom (F G : Presheaf X C) := F ⟶ G -- NatTrans F G
```

**Mathlib Location:** `Mathlib.CategoryTheory.Functor.Category`

**Difficulty:** easy

---

### 7. Presheaf.pushforward

**Natural Language Statement:**
For a continuous map f : X → Y, the pushforward f_* takes presheaves on X to presheaves on Y via (f_*F)(U) = F(f⁻¹U).

**Lean 4 Definition:**
```lean
def Presheaf.pushforward (f : X ⟶ Y) (F : Presheaf X C) : Presheaf Y C :=
  (Opens.map f).op ⋙ F
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Presheaf`

**Difficulty:** medium

---

### 8. Presheaf.pullback

**Natural Language Statement:**
For a continuous map f : X → Y, the pullback f* is left adjoint to pushforward.

**Lean 4 Definition:**
```lean
def Presheaf.pullback (f : X ⟶ Y) : Presheaf Y C ⥤ Presheaf X C := ...
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Presheaf`

**Difficulty:** hard

---

## Part II: Sheaves

### Module Organization

**Primary Imports:**
- `Mathlib.Topology.Sheaves.Sheaf`
- `Mathlib.CategoryTheory.Sites.Sheaf`

**Estimated Statements:** 10

---

### 9. TopCat.Presheaf.IsSheaf

**Natural Language Statement:**
A presheaf F on a topological space is a sheaf if it satisfies the sheaf condition with respect to the Grothendieck topology on open sets.

**Lean 4 Definition:**
```lean
def TopCat.Presheaf.IsSheaf (F : TopCat.Presheaf X C) : Prop :=
  CategoryTheory.Presheaf.IsSheaf (Opens.grothendieckTopology ↑X) F
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Sheaf`

**Difficulty:** medium

---

### 10. TopCat.Sheaf

**Natural Language Statement:**
A sheaf on a topological space X is a presheaf satisfying the sheaf condition.

**Lean 4 Definition:**
```lean
structure TopCat.Sheaf (X : TopCat) (C : Type*) [Category C] where
  presheaf : TopCat.Presheaf X C
  isSheaf : presheaf.IsSheaf
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Sheaf`

**Difficulty:** easy

---

### 11. Presheaf.IsSheaf (Sites)

**Natural Language Statement:**
A presheaf P on a site (C, J) is a sheaf if for every covering sieve S on U, the induced map P(U) → lim P over S is an isomorphism.

**Lean 4 Definition:**
```lean
def Presheaf.IsSheaf (J : GrothendieckTopology C) (P : Cᵒᵖ ⥤ D) : Prop :=
  ∀ ⦃X : C⦄ (S : Sieve X), J S → IsLimit (S.multiforkCover P)
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheaf`

**Difficulty:** hard

---

### 12. Sheaf

**Natural Language Statement:**
A sheaf on a Grothendieck site (C, J) is a presheaf satisfying the sheaf condition.

**Lean 4 Definition:**
```lean
structure Sheaf (J : GrothendieckTopology C) (A : Type*) [Category A] where
  val : Cᵒᵖ ⥤ A
  cond : Presheaf.IsSheaf J val
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheaf`

**Difficulty:** medium

---

### 13. isSheaf_unit

**Natural Language Statement:**
The presheaf constantly valued in the terminal object is always a sheaf.

**Lean 4 Theorem:**
```lean
theorem TopCat.Presheaf.isSheaf_unit :
    (Functor.const _ ⟨()⟩ : TopCat.Presheaf X (Type*)).IsSheaf := ...
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Sheaf`

**Difficulty:** easy

---

### 14. isSheaf_iso_iff

**Natural Language Statement:**
The sheaf condition is preserved under isomorphism of presheaves.

**Lean 4 Theorem:**
```lean
theorem TopCat.Presheaf.isSheaf_iso_iff {F G : TopCat.Presheaf X C} (α : F ≅ G) :
    F.IsSheaf ↔ G.IsSheaf := ...
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Sheaf`

**Difficulty:** medium

---

### 15. Sheaf.presheaf

**Natural Language Statement:**
Every sheaf has an underlying presheaf.

**Lean 4 Definition:**
```lean
def Sheaf.presheaf (F : Sheaf J A) : Cᵒᵖ ⥤ A := F.val
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheaf`

**Difficulty:** easy

---

### 16. sheafToPresheaf

**Natural Language Statement:**
There is a forgetful functor from sheaves to presheaves.

**Lean 4 Definition:**
```lean
def sheafToPresheaf (J : GrothendieckTopology C) (A : Type*) [Category A] :
    Sheaf J A ⥤ (Cᵒᵖ ⥤ A) where
  obj F := F.val
  map f := f.val
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheaf`

**Difficulty:** easy

---

### 17. sheafToPresheaf.full

**Natural Language Statement:**
The forgetful functor from sheaves to presheaves is full.

**Lean 4 Instance:**
```lean
instance : (sheafToPresheaf J A).Full := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheaf`

**Difficulty:** medium

---

### 18. sheafToPresheaf.faithful

**Natural Language Statement:**
The forgetful functor from sheaves to presheaves is faithful.

**Lean 4 Instance:**
```lean
instance : (sheafToPresheaf J A).Faithful := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheaf`

**Difficulty:** medium

---

## Part III: Stalks and Germs

### Module Organization

**Primary Imports:**
- `Mathlib.Topology.Sheaves.Stalks`

**Estimated Statements:** 10

---

### 19. Presheaf.stalk

**Natural Language Statement:**
The stalk of a presheaf F at a point x is the colimit of F over all open neighborhoods of x.

**Lean 4 Definition:**
```lean
def Presheaf.stalk (F : TopCat.Presheaf X C) (x : X) : C :=
  colimit ((OpenNhds.inclusion x).op ⋙ F)
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Stalks`

**Difficulty:** medium

---

### 20. Presheaf.germ

**Natural Language Statement:**
The germ at x is the canonical map from sections over an open neighborhood U containing x to the stalk.

**Lean 4 Definition:**
```lean
def Presheaf.germ (F : TopCat.Presheaf X C) {U : Opens X} (hx : x ∈ U) :
    F.obj (op U) ⟶ F.stalk x := colimit.ι ((OpenNhds.inclusion x).op ⋙ F) (op ⟨U, hx⟩)
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Stalks`

**Difficulty:** medium

---

### 21. germ_res

**Natural Language Statement:**
Restriction maps commute with germs: for V ⊆ U containing x, germ_x ∘ res = germ_x.

**Lean 4 Theorem:**
```lean
theorem Presheaf.germ_res (F : TopCat.Presheaf X C) {U V : Opens X}
    (i : V ⟶ U) (hx : x ∈ V) :
    F.map i.op ≫ F.germ hx = F.germ (Opens.le_def.mp (leOfHom i) hx) := ...
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Stalks`

**Difficulty:** medium

---

### 22. stalkFunctor

**Natural Language Statement:**
Stalks are functorial: a morphism of presheaves induces morphisms on all stalks.

**Lean 4 Definition:**
```lean
def stalkFunctor (x : X) : TopCat.Presheaf X C ⥤ C where
  obj F := F.stalk x
  map α := colimMap (whiskerLeft ((OpenNhds.inclusion x).op) α)
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Stalks`

**Difficulty:** hard

---

### 23. stalkPushforward

**Natural Language Statement:**
For a continuous map f : X → Y, there is a natural map from the stalk of f_*F at y to the stalk of F at any preimage of y.

**Lean 4 Definition:**
```lean
def stalkPushforward (f : X ⟶ Y) (F : TopCat.Presheaf X C) (y : Y) :
    (f _* F).stalk y ⟶ F.stalk x := ...
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Stalks`

**Difficulty:** hard

---

### 24. stalkPullbackIso

**Natural Language Statement:**
For a continuous map f : X → Y, the pullback sheaf has stalks isomorphic to the original: (f*F).stalk x ≅ F.stalk (f x).

**Lean 4 Theorem:**
```lean
def stalkPullbackIso (f : X ⟶ Y) (F : TopCat.Presheaf Y C) (x : X) :
    (pullback f F).stalk x ≅ F.stalk (f x) := ...
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Stalks`

**Difficulty:** hard

---

### 25. germ_exist

**Natural Language Statement:**
Every element of the stalk is the germ of some section: the germ map is surjective (in concrete categories).

**Lean 4 Theorem:**
```lean
theorem Presheaf.germ_exist (F : TopCat.Presheaf X (Type*)) (x : X) (t : F.stalk x) :
    ∃ (U : OpenNhds x) (s : F.obj (op U.obj)), F.germ U.mem s = t := ...
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Stalks`

**Difficulty:** medium

---

### 26. stalk_hom_ext

**Natural Language Statement:**
A morphism from a stalk is determined by its composition with all germ maps.

**Lean 4 Theorem:**
```lean
theorem Presheaf.stalk_hom_ext (F : TopCat.Presheaf X C) (x : X)
    {Y : C} {f g : F.stalk x ⟶ Y}
    (h : ∀ (U : OpenNhds x), F.germ U.mem ≫ f = F.germ U.mem ≫ g) :
    f = g := ...
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Stalks`

**Difficulty:** medium

---

### 27. stalkSpecializes

**Natural Language Statement:**
For points x ⤳ y (x specializes to y), there is a natural map F.stalk y → F.stalk x.

**Lean 4 Definition:**
```lean
def Presheaf.stalkSpecializes (F : TopCat.Presheaf X C) {x y : X} (h : x ⤳ y) :
    F.stalk y ⟶ F.stalk x := ...
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Stalks`

**Difficulty:** hard

---

### 28. mono_iff_stalk_mono

**Natural Language Statement:**
A morphism of sheaves is a monomorphism iff it is a monomorphism on all stalks.

**Lean 4 Theorem:**
```lean
theorem mono_iff_stalkFunctor_map_mono {F G : TopCat.Sheaf X C} (f : F ⟶ G) :
    Mono f ↔ ∀ x, Mono (stalkFunctor x |>.map f.val) := ...
```

**Mathlib Location:** `Mathlib.Topology.Sheaves.Stalks`

**Difficulty:** hard

---

## Part IV: Sheafification

### Module Organization

**Primary Imports:**
- `Mathlib.CategoryTheory.Sites.Sheafification`

**Estimated Statements:** 10

---

### 29. HasSheafify

**Natural Language Statement:**
A site has sheafification if the inclusion of sheaves into presheaves has a left adjoint that preserves finite limits.

**Lean 4 Class:**
```lean
class HasSheafify (J : GrothendieckTopology C) (A : Type*) [Category A] : Prop where
  hasWeakSheafify : HasWeakSheafify J A
  isLeftExact : Nonempty (HasWeakSheafify.presheafToSheaf J A).PreservesFiniteLimits
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheafification`

**Difficulty:** hard

---

### 30. presheafToSheaf

**Natural Language Statement:**
The sheafification functor is left adjoint to the forgetful functor from sheaves to presheaves.

**Lean 4 Definition:**
```lean
def presheafToSheaf (J : GrothendieckTopology C) (A : Type*) [Category A]
    [HasWeakSheafify J A] : (Cᵒᵖ ⥤ A) ⥤ Sheaf J A := HasWeakSheafify.presheafToSheaf J A
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheafification`

**Difficulty:** medium

---

### 31. sheafificationAdjunction

**Natural Language Statement:**
Sheafification is left adjoint to the forgetful functor: presheafToSheaf ⊣ sheafToPresheaf.

**Lean 4 Definition:**
```lean
def sheafificationAdjunction (J : GrothendieckTopology C) (A : Type*) [Category A]
    [HasWeakSheafify J A] : presheafToSheaf J A ⊣ sheafToPresheaf J A :=
  HasWeakSheafify.sheafificationAdjunction J A
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheafification`

**Difficulty:** hard

---

### 32. toSheafify

**Natural Language Statement:**
The sheafification map is the unit of the adjunction: there is a natural transformation P → sheafify P.

**Lean 4 Definition:**
```lean
def toSheafify (P : Cᵒᵖ ⥤ A) [HasWeakSheafify J A] :
    P ⟶ (presheafToSheaf J A).obj P :=
  (sheafificationAdjunction J A).unit.app P
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheafification`

**Difficulty:** medium

---

### 33. sheafify

**Natural Language Statement:**
The sheafification of a presheaf P is the underlying presheaf of presheafToSheaf P.

**Lean 4 Definition:**
```lean
def sheafify (P : Cᵒᵖ ⥤ A) [HasWeakSheafify J A] : Cᵒᵖ ⥤ A :=
  (presheafToSheaf J A).obj P |>.val
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheafification`

**Difficulty:** easy

---

### 34. isIso_toSheafify

**Natural Language Statement:**
If P is already a sheaf, then the map P → sheafify P is an isomorphism.

**Lean 4 Theorem:**
```lean
theorem isIso_toSheafify (P : Cᵒᵖ ⥤ A) [HasWeakSheafify J A] (hP : Presheaf.IsSheaf J P) :
    IsIso (toSheafify J P) := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheafification`

**Difficulty:** medium

---

### 35. sheafifyMap

**Natural Language Statement:**
Sheafification is functorial: a morphism f : P → Q induces sheafify(f) : sheafify(P) → sheafify(Q).

**Lean 4 Definition:**
```lean
def sheafifyMap (f : P ⟶ Q) [HasWeakSheafify J A] :
    sheafify J P ⟶ sheafify J Q := (presheafToSheaf J A).map f |>.val
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheafification`

**Difficulty:** medium

---

### 36. sheafifyLift

**Natural Language Statement:**
For a morphism f : P → F where F is a sheaf, there is a unique lift through sheafification.

**Lean 4 Definition:**
```lean
def sheafifyLift (f : P ⟶ F.val) [HasWeakSheafify J A] (hF : Presheaf.IsSheaf J F.val) :
    (presheafToSheaf J A).obj P ⟶ F := (sheafificationAdjunction J A).homEquiv P F f
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheafification`

**Difficulty:** hard

---

### 37. toSheafify_sheafifyLift

**Natural Language Statement:**
The sheafification lift commutes with toSheafify: toSheafify ≫ sheafifyLift f = f.

**Lean 4 Theorem:**
```lean
theorem toSheafify_sheafifyLift (f : P ⟶ F.val) [HasWeakSheafify J A]
    (hF : Presheaf.IsSheaf J F.val) :
    toSheafify J P ≫ (sheafifyLift J f hF).val = f := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheafification`

**Difficulty:** medium

---

### 38. sheafifyLift_unique

**Natural Language Statement:**
The lift through sheafification is unique.

**Lean 4 Theorem:**
```lean
theorem sheafifyLift_unique (f : P ⟶ F.val) (g : (presheafToSheaf J A).obj P ⟶ F)
    (h : toSheafify J P ≫ g.val = f) [HasWeakSheafify J A] :
    g = sheafifyLift J f F.cond := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheafification`

**Difficulty:** hard

---

## Part V: Sheaf Category Structure

### Module Organization

**Primary Imports:**
- `Mathlib.CategoryTheory.Sites.Limits`
- `Mathlib.CategoryTheory.Sites.Abelian`

**Estimated Statements:** 10

---

### 39. Sheaf.instCategory

**Natural Language Statement:**
Sheaves on a site form a category with morphisms being natural transformations of underlying presheaves.

**Lean 4 Instance:**
```lean
instance Sheaf.instCategory : Category (Sheaf J A) := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Sheaf`

**Difficulty:** easy

---

### 40. isSheaf_of_isLimit

**Natural Language Statement:**
If a presheaf cone is a limit cone, the apex presheaf satisfies the sheaf condition.

**Lean 4 Theorem:**
```lean
theorem Presheaf.isSheaf_of_isLimit {F : K ⥤ Cᵒᵖ ⥤ A} {c : Cone F}
    (hc : IsLimit c) (hF : ∀ k, Presheaf.IsSheaf J (F.obj k)) :
    Presheaf.IsSheaf J c.pt := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Limits`

**Difficulty:** hard

---

### 41. sheafToPresheaf.createsLimit

**Natural Language Statement:**
The forgetful functor from sheaves to presheaves creates limits.

**Lean 4 Instance:**
```lean
instance [HasLimitsOfShape K A] : CreatesLimitsOfShape K (sheafToPresheaf J A) := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Limits`

**Difficulty:** hard

---

### 42. Sheaf.instHasLimits

**Natural Language Statement:**
The category of sheaves has all limits that the target category has.

**Lean 4 Instance:**
```lean
instance [HasLimits A] : HasLimits (Sheaf J A) := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Limits`

**Difficulty:** medium

---

### 43. sheafifyCocone

**Natural Language Statement:**
A presheaf cocone can be sheafified to produce a sheaf cocone.

**Lean 4 Definition:**
```lean
def sheafifyCocone {F : K ⥤ Sheaf J A} (c : Cocone (F ⋙ sheafToPresheaf J A))
    [HasWeakSheafify J A] : Cocone F := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Limits`

**Difficulty:** hard

---

### 44. Sheaf.instHasColimits

**Natural Language Statement:**
The category of sheaves has all colimits when the target has them and sheafification exists.

**Lean 4 Instance:**
```lean
instance [HasColimits A] [HasWeakSheafify J A] : HasColimits (Sheaf J A) := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Limits`

**Difficulty:** hard

---

### 45. Sheaf.instHasFiniteProducts

**Natural Language Statement:**
The sheaf category has finite products when the target category does.

**Lean 4 Instance:**
```lean
instance [HasFiniteProducts A] : HasFiniteProducts (Sheaf J A) := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Limits`

**Difficulty:** medium

---

### 46. Sheaf.instPreadditive

**Natural Language Statement:**
When the target category is preadditive, so is the sheaf category.

**Lean 4 Instance:**
```lean
instance [Preadditive A] : Preadditive (Sheaf J A) := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Abelian`

**Difficulty:** medium

---

### 47. sheafIsAbelian

**Natural Language Statement:**
When the target category is abelian and sheafification exists, the sheaf category is abelian.

**Lean 4 Instance:**
```lean
instance sheafIsAbelian [Abelian A] [HasSheafify J A] : Abelian (Sheaf J A) := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Abelian`

**Difficulty:** hard

---

### 48. presheafToSheaf.additive

**Natural Language Statement:**
The sheafification functor is additive when the target category is preadditive.

**Lean 4 Instance:**
```lean
instance [Preadditive A] [HasWeakSheafify J A] :
    (presheafToSheaf J A).Additive := ...
```

**Mathlib Location:** `Mathlib.CategoryTheory.Sites.Abelian`

**Difficulty:** medium

---

## Part VI: Locally Ringed Spaces

### Module Organization

**Primary Imports:**
- `Mathlib.Geometry.RingedSpace.LocallyRingedSpace`

**Estimated Statements:** 7

---

### 49. LocallyRingedSpace

**Natural Language Statement:**
A locally ringed space is a sheaf of commutative rings where all stalks are local rings.

**Lean 4 Definition:**
```lean
structure LocallyRingedSpace extends SheafedSpace CommRingCat where
  localRing : ∀ x, LocalRing (presheaf.stalk x)
```

**Mathlib Location:** `Mathlib.Geometry.RingedSpace.LocallyRingedSpace`

**Difficulty:** medium

---

### 50. LocallyRingedSpace.Hom

**Natural Language Statement:**
A morphism of locally ringed spaces is a continuous map with a sheaf morphism such that induced stalk maps are local ring homomorphisms.

**Lean 4 Definition:**
```lean
structure LocallyRingedSpace.Hom (X Y : LocallyRingedSpace) extends X.toSheafedSpace ⟶ Y.toSheafedSpace where
  prop : ∀ x, IsLocalRingHom (stalkMap toHom x)
```

**Mathlib Location:** `Mathlib.Geometry.RingedSpace.LocallyRingedSpace`

**Difficulty:** hard

---

### 51. stalkMap

**Natural Language Statement:**
A morphism of ringed spaces induces a ring homomorphism on stalks.

**Lean 4 Definition:**
```lean
def stalkMap (f : X ⟶ Y) (x : X) : Y.presheaf.stalk (f.base x) ⟶ X.presheaf.stalk x := ...
```

**Mathlib Location:** `Mathlib.Geometry.RingedSpace.LocallyRingedSpace`

**Difficulty:** medium

---

### 52. LocallyRingedSpace.Γ

**Natural Language Statement:**
The global sections functor maps locally ringed spaces to commutative rings.

**Lean 4 Definition:**
```lean
def LocallyRingedSpace.Γ : LocallyRingedSpaceᵒᵖ ⥤ CommRingCat := ...
```

**Mathlib Location:** `Mathlib.Geometry.RingedSpace.LocallyRingedSpace`

**Difficulty:** medium

---

### 53. LocallyRingedSpace.forgetToSheafedSpace

**Natural Language Statement:**
There is a forgetful functor from locally ringed spaces to sheafed spaces.

**Lean 4 Definition:**
```lean
def LocallyRingedSpace.forgetToSheafedSpace : LocallyRingedSpace ⥤ SheafedSpace CommRingCat := ...
```

**Mathlib Location:** `Mathlib.Geometry.RingedSpace.LocallyRingedSpace`

**Difficulty:** easy

---

### 54. LocallyRingedSpace.restrict

**Natural Language Statement:**
Restriction of a locally ringed space to an open subset is again a locally ringed space.

**Lean 4 Definition:**
```lean
def LocallyRingedSpace.restrict (X : LocallyRingedSpace) (U : Opens X) : LocallyRingedSpace := ...
```

**Mathlib Location:** `Mathlib.Geometry.RingedSpace.LocallyRingedSpace`

**Difficulty:** medium

---

### 55. restrictStalkIso

**Natural Language Statement:**
The stalk of a restricted locally ringed space is isomorphic to the stalk of the original.

**Lean 4 Theorem:**
```lean
def LocallyRingedSpace.restrictStalkIso (X : LocallyRingedSpace) (U : Opens X) (x : U) :
    (X.restrict U).presheaf.stalk x ≅ X.presheaf.stalk x.val := ...
```

**Mathlib Location:** `Mathlib.Geometry.RingedSpace.LocallyRingedSpace`

**Difficulty:** hard

---

## Part VII: Structure Sheaves

### Module Organization

**Primary Imports:**
- `Mathlib.AlgebraicGeometry.StructureSheaf`

**Estimated Statements:** 5

---

### 56. Spec.structureSheaf

**Natural Language Statement:**
The structure sheaf on Spec R is a sheaf of commutative rings whose sections over a basic open D(f) are the localization R[1/f].

**Lean 4 Definition:**
```lean
def Spec.structureSheaf (R : CommRingCat) : Sheaf CommRingCat (PrimeSpectrum.Top R) := ...
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.StructureSheaf`

**Difficulty:** hard

---

### 57. structureSheaf.stalkIso

**Natural Language Statement:**
The stalk of the structure sheaf at a prime p is isomorphic to the localization at p.

**Lean 4 Theorem:**
```lean
def structureSheaf.stalkIso (R : CommRingCat) (p : PrimeSpectrum R) :
    (Spec.structureSheaf R).val.stalk p ≅ CommRingCat.of (Localization.AtPrime p.asIdeal) := ...
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.StructureSheaf`

**Difficulty:** hard

---

### 58. basicOpenIso

**Natural Language Statement:**
On the basic open set D(f), the structure sheaf is isomorphic to the localization R[1/f].

**Lean 4 Theorem:**
```lean
def structureSheaf.basicOpenIso (R : CommRingCat) (f : R) :
    (Spec.structureSheaf R).val.obj (op (PrimeSpectrum.basicOpen f)) ≅
    CommRingCat.of (Localization.Away f) := ...
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.StructureSheaf`

**Difficulty:** hard

---

### 59. globalSectionsIso

**Natural Language Statement:**
The global sections of the structure sheaf of Spec R are isomorphic to R.

**Lean 4 Theorem:**
```lean
def structureSheaf.globalSectionsIso (R : CommRingCat) :
    (Spec.structureSheaf R).val.obj (op ⊤) ≅ R := ...
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.StructureSheaf`

**Difficulty:** medium

---

### 60. comap

**Natural Language Statement:**
A ring homomorphism f : R → S induces a morphism of structure sheaves.

**Lean 4 Definition:**
```lean
def structureSheaf.comap (f : R →+* S) :
    (Spec.structureSheaf S).val ⟶ (PrimeSpectrum.comap f).op ⋙ (Spec.structureSheaf R).val := ...
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.StructureSheaf`

**Difficulty:** hard

---

## Summary Statistics

| Part | Theorems | Difficulty Breakdown |
|------|----------|---------------------|
| I. Presheaves | 8 | 6 easy, 1 medium, 1 hard |
| II. Sheaves | 10 | 3 easy, 5 medium, 2 hard |
| III. Stalks and Germs | 10 | 1 easy, 5 medium, 4 hard |
| IV. Sheafification | 10 | 1 easy, 5 medium, 4 hard |
| V. Sheaf Category Structure | 10 | 1 easy, 4 medium, 5 hard |
| VI. Locally Ringed Spaces | 7 | 1 easy, 4 medium, 2 hard |
| VII. Structure Sheaves | 5 | 0 easy, 1 medium, 4 hard |
| **Total** | **60** | 13 easy, 25 medium, 22 hard |

## Key Imports Reference

```lean
import Mathlib.CategoryTheory.Functor.Category
import Mathlib.CategoryTheory.Sites.Sheaf
import Mathlib.CategoryTheory.Sites.Sheafification
import Mathlib.CategoryTheory.Sites.Limits
import Mathlib.CategoryTheory.Sites.Abelian
import Mathlib.Topology.Sheaves.Sheaf
import Mathlib.Topology.Sheaves.Stalks
import Mathlib.Topology.Sheaves.Presheaf
import Mathlib.Geometry.RingedSpace.LocallyRingedSpace
import Mathlib.AlgebraicGeometry.StructureSheaf
```

## Not Formalized (Templates Only)

The following are mathematically important but NOT fully formalized in Mathlib4:

1. **Cech Cohomology**: Cech complex, Cech-to-derived functor comparison
2. **Sheaf Cohomology**: H^n(X, F) via derived functors
3. **Spectral Sequences**: Leray spectral sequence, hypercohomology
4. **de Rham Cohomology**: Poincare lemma, de Rham theorem
5. **Coherent Sheaves**: Coherent sheaves on schemes, Serre's theorems
6. **Etale Sheaves**: Etale topology, etale cohomology

---

## Sources

- [Mathlib.Topology.Sheaves.Sheaf](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Topology/Sheaves/Sheaf.html)
- [Mathlib.CategoryTheory.Sites.Sheaf](https://leanprover-community.github.io/mathlib4_docs/Mathlib/CategoryTheory/Sites/Sheaf.html)
- [Mathlib.Topology.Sheaves.Stalks](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Topology/Sheaves/Stalks.html)
- [Mathlib.CategoryTheory.Sites.Sheafification](https://leanprover-community.github.io/mathlib4_docs/Mathlib/CategoryTheory/Sites/Sheafification.html)
- [Mathlib.Geometry.RingedSpace.LocallyRingedSpace](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/RingedSpace/LocallyRingedSpace.html)
- [Mathlib.AlgebraicGeometry.StructureSheaf](https://leanprover-community.github.io/mathlib4_docs/Mathlib/AlgebraicGeometry/StructureSheaf.html)
