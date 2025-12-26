# Category Theory Knowledge Base for Lean 4

**Generated:** 2025-12-13
**Purpose:** Research knowledge base for implementing category theory axioms and theorems in Lean 4 for dataset generation pairing formal proofs with natural language explanations.

---

## Overview

Category Theory is extensively formalized in Lean 4's Mathlib library under `Mathlib.CategoryTheory.*`. The formalization includes foundational axioms, functors, natural transformations, limits/colimits, adjunctions, Yoneda lemma, monads, and advanced topics like abelian categories and derived categories (formalized in 2025).

### Content Summary

| Category | Count | Description |
|----------|-------|-------------|
| **Category Axioms** | 3 | Left/right identity, associativity |
| **Functor Axioms** | 2 | Identity preservation, composition preservation |
| **Natural Transformation** | 1 | Naturality condition |
| **Key Theorems** | 5+ | Yoneda lemma, adjunctions, limits/colimits |
| **Advanced Topics** | 4+ | Monads, abelian categories, derived categories |

### Key Insight

Mathlib uses a typeclass-based approach where `Category` extends `CategoryStruct` which provides `Hom`, `id`, and `comp`. The axioms are methods of the `Category` class.

### Mathlib Approach

Categories are defined via typeclass:

```lean
class Category (obj : Type u) extends CategoryStruct.{v, u} obj : Type (max u (v + 1)) where
  id_comp : ∀ {X Y : obj} (f : X ⟶ Y), 𝟙 X ≫ f = f
  comp_id : ∀ {X Y : obj} (f : X ⟶ Y), f ≫ 𝟙 Y = f
  assoc   : ∀ {W X Y Z : obj} (f : W ⟶ X) (g : X ⟶ Y) (h : Y ⟶ Z), (f ≫ g) ≫ h = f ≫ (g ≫ h)
```

**Primary Import:** `Mathlib.CategoryTheory.Category.Basic`

---

## Related Knowledge Bases

### Builds Upon This KB
- **Homological Algebra** (`homological_algebra_knowledge_base.md`): Chain complexes, derived functors
- **Algebraic Topology** (`algebraic_topology_knowledge_base.md`): Simplicial sets, homotopy theory
- **Sheaf Theory** (`sheaf_theory_knowledge_base.md`): Presheaves, sheaves, sheafification
- **Algebraic Geometry** (`algebraic_geometry_knowledge_base.md`): Schemes as locally ringed spaces

### Related Topics
- **Order Theory** (`order_theory_knowledge_base.md`): Categories from posets

### Scope Clarification
This KB focuses on **abstract category theory**:
- Categories, functors, natural transformations
- Limits and colimits
- Adjunctions and the Yoneda lemma
- Monads and abelian categories

For **homological applications** (chain complexes, derived functors), see the **Homological Algebra KB**.

---

## Category Axioms

### 1. Category Structure Definition

**Location:** `Mathlib.CategoryTheory.Category.Basic`

**Natural Language Statement:**
A category C consists of objects and morphisms (arrows) between objects, together with an identity morphism for each object and a composition operation for compatible morphisms, satisfying associativity and identity laws.

**Formal Definition:**
```lean
class CategoryStruct (obj : Type u) : Type (max u (v + 1)) where
  Hom : obj → obj → Type v
  id : ∀ (X : obj), Hom X X
  comp : ∀ {X Y Z : obj}, Hom X Y → Hom Y Z → Hom X Z
```

**Notation:**
- `X ⟶ Y` for `Hom X Y`
- `𝟙 X` for `id X`
- `f ≫ g` for `comp f g` (diagrammatic order: f then g)

**Universe Levels:**
- Objects live in `Type u`
- Morphisms live in `Type v`
- Two abbreviations:
  - **LargeCategory:** `Category.{u, u+1}` (objects one level above morphisms)
  - **SmallCategory:** `Category.{u, u}` (objects and morphisms in same universe)

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Category.Basic`

**Difficulty:** easy

---

### 2. Left Identity Axiom (id_comp)

**Location:** `Mathlib.CategoryTheory.Category.Basic`

**Natural Language Statement:**
Identity morphisms are left identities for composition: composing the identity on X with any morphism f : X → Y yields f.

**Formal Definition:**
```lean
id_comp {X Y : obj} (f : X ⟶ Y) : 𝟙 X ≫ f = f
```

**Mathematical Statement:**
For any morphism f : X → Y, id_X ∘ f = f

**Mathlib Support:** FULL (axiom of Category class)
- **Import:** `Mathlib.CategoryTheory.Category.Basic`
- **Simp Lemma:** Yes (used in automation)

**Difficulty:** easy

---

### 3. Right Identity Axiom (comp_id)

**Location:** `Mathlib.CategoryTheory.Category.Basic`

**Natural Language Statement:**
Identity morphisms are right identities for composition: composing any morphism f : X → Y with the identity on Y yields f.

**Formal Definition:**
```lean
comp_id {X Y : obj} (f : X ⟶ Y) : f ≫ 𝟙 Y = f
```

**Mathematical Statement:**
For any morphism f : X → Y, f ∘ id_Y = f

**Mathlib Support:** FULL (axiom of Category class)
- **Import:** `Mathlib.CategoryTheory.Category.Basic`
- **Simp Lemma:** Yes (used in automation)

**Difficulty:** easy

---

### 4. Associativity Axiom (assoc)

**Location:** `Mathlib.CategoryTheory.Category.Basic`

**Natural Language Statement:**
Composition in a category is associative: for any compatible morphisms f, g, h, we have (f ≫ g) ≫ h = f ≫ (g ≫ h).

**Formal Definition:**
```lean
assoc {W X Y Z : obj} (f : W ⟶ X) (g : X ⟶ Y) (h : Y ⟶ Z) :
  (f ≫ g) ≫ h = f ≫ (g ≫ h)
```

**Mathematical Statement:**
For morphisms f : W → X, g : X → Y, h : Y → Z, we have (h ∘ g) ∘ f = h ∘ (g ∘ f)

**Mathlib Support:** FULL (axiom of Category class)
- **Import:** `Mathlib.CategoryTheory.Category.Basic`
- **Simp Lemma:** Yes (used in automation)

**Difficulty:** easy

---

## Functor Axioms

### 5. Functor Definition

**Location:** `Mathlib.CategoryTheory.Functor.Basic`

**Natural Language Statement:**
A functor F : C → D between categories is a structure-preserving map sending objects to objects and morphisms to morphisms, preserving identity morphisms and composition.

**Formal Definition:**
```lean
structure Functor (C : Type u₁) [Category.{v₁} C] (D : Type u₂) [Category.{v₂} D] where
  obj : C → D
  map : ∀ {X Y : C}, (X ⟶ Y) → (obj X ⟶ obj Y)
  map_id : ∀ (X : C), map (𝟙 X) = 𝟙 (obj X)
  map_comp : ∀ {X Y Z : C} (f : X ⟶ Y) (g : Y ⟶ Z), map (f ≫ g) = map f ≫ map g
```

**Notation:**
- `C ⥤ D` for `Functor C D`
- `F.obj X` for object mapping
- `F.map f` for morphism mapping

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Functor.Basic`

**Difficulty:** easy

---

### 6. Identity Preservation (map_id)

**Location:** `Mathlib.CategoryTheory.Functor.Basic`

**Natural Language Statement:**
A functor preserves identity morphisms: F(id_X) = id_{F(X)} for all objects X.

**Formal Definition:**
```lean
map_id (X : C) : F.map (𝟙 X) = 𝟙 (F.obj X)
```

**Mathematical Statement:**
F(id_X) = id_{F(X)}

**Mathlib Support:** FULL (field of Functor structure)
- **Import:** `Mathlib.CategoryTheory.Functor.Basic`
- **Simp Lemma:** Yes

**Difficulty:** easy

---

### 7. Composition Preservation (map_comp)

**Location:** `Mathlib.CategoryTheory.Functor.Basic`

**Natural Language Statement:**
A functor preserves composition: F(f ≫ g) = F(f) ≫ F(g) for all composable morphisms.

**Formal Definition:**
```lean
map_comp {X Y Z : C} (f : X ⟶ Y) (g : Y ⟶ Z) :
  F.map (f ≫ g) = F.map f ≫ F.map g
```

**Mathematical Statement:**
F(g ∘ f) = F(g) ∘ F(f)

**Mathlib Support:** FULL (field of Functor structure)
- **Import:** `Mathlib.CategoryTheory.Functor.Basic`
- **Simp Lemma:** Yes

**Difficulty:** easy

---

### 8. Special Functors

**Identity Functor (𝟭):**
```lean
def Functor.id (C : Type u) [Category.{v} C] : C ⥤ C where
  obj := id
  map := id
```
Satisfies: `F ⋙ 𝟭 D = F` and `𝟭 C ⋙ F = F`

**Functor Composition (⋙):**
```lean
def Functor.comp (F : C ⥤ D) (G : D ⥤ E) : C ⥤ E where
  obj := G.obj ∘ F.obj
  map := G.map ∘ F.map
```

**Location:** `Mathlib.CategoryTheory.Functor.Basic`

**Difficulty:** easy

---

## Natural Transformations

### 9. Natural Transformation Definition

**Location:** `Mathlib.CategoryTheory.NatTrans`

**Natural Language Statement:**
A natural transformation α between functors F, G : C → D is a family of morphisms α_X : F(X) → G(X) for each object X in C, satisfying the naturality condition: for any morphism f : X → Y, we have F(f) ≫ α_Y = α_X ≫ G(f).

**Formal Definition:**
```lean
structure NatTrans {C : Type u₁} [Category.{v₁} C] {D : Type u₂} [Category.{v₂} D]
    (F G : C ⥤ D) : Type (max u₁ v₂) where
  app : ∀ X : C, F.obj X ⟶ G.obj X
  naturality : ∀ {X Y : C} (f : X ⟶ Y), F.map f ≫ app Y = app X ≫ G.map f
```

**Notation:**
- `F ⟶ G` for `NatTrans F G` (in functor category context)
- `α.app X` for component at object X

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.NatTrans`

**Difficulty:** intermediate

---

### 10. Naturality Condition

**Location:** `Mathlib.CategoryTheory.NatTrans`

**Natural Language Statement:**
Natural transformations commute with morphisms: for any f : X → Y in C and natural transformation α : F → G, the naturality square commutes.

**Formal Definition:**
```lean
naturality {X Y : C} (f : X ⟶ Y) : F.map f ≫ α.app Y = α.app X ≫ G.map f
```

**Diagram:**
```
F(X) --α_X--> G(X)
 |              |
F(f)          G(f)
 |              |
 v              v
F(Y) --α_Y--> G(Y)
```

**Mathlib Support:** FULL (field of NatTrans structure)
- **Import:** `Mathlib.CategoryTheory.NatTrans`
- **Simp Lemma:** Yes

**Difficulty:** intermediate

---

### 11. Functor Categories

**Location:** `Mathlib.CategoryTheory.Functor.Category`

**Natural Language Statement:**
Given categories C and D, the functor category [C, D] has functors F : C → D as objects and natural transformations as morphisms.

**Formal Definition:**
```lean
instance Functor.category : Category.{max u₁ v₂} (C ⥤ D) where
  Hom := NatTrans
  id := NatTrans.id
  comp := NatTrans.vcomp
```

**Composition Operations:**
- **Vertical Composition:** `α ≫ β` composes natural transformations sequentially
- **Horizontal Composition:** `α ◫ β` for whiskering

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Functor.Category`

**Difficulty:** intermediate

---

## Key Theorems

### 12. Yoneda Lemma

**Location:** `Mathlib.CategoryTheory.Yoneda`

**Natural Language Statement:**
For any category C, object X in C, and presheaf F : Cᵒᵖ → Type, there is a natural bijection between natural transformations from the representable functor Hom(-, X) to F and elements of F(X). The Yoneda embedding is fully faithful.

**Mathematical Statement:**
```
(yoneda.obj X ⟶ F) ≃ F.obj (op X)
```

**Formal Definition:**
```lean
def yoneda : C ⥤ (Cᵒᵖ ⥤ Type v₁) where
  obj := fun X => {
    obj := fun Y => unop Y ⟶ X
    map := fun f g => g ≫ f.unop
  }
  map := fun f => { app := fun Y g => g ≫ f }

def yonedaEquiv {X : C} {F : Cᵒᵖ ⥤ Type v₁} : (yoneda.obj X ⟶ F) ≃ F.obj (op X)
```

**Key Properties:**
- `Yoneda.fullyFaithful` - The Yoneda embedding is fully faithful
- `Yoneda.ext` - Two objects are isomorphic iff their hom-functors are naturally isomorphic

**Proof Sketch:**
1. Forward: Given α : yoneda.obj X ⟶ F, return α.app X (𝟙 X)
2. Backward: Given u ∈ F.obj (op X), define α.app Y (f) = F.map f u
3. Verify naturality and bijection using functor laws

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Yoneda`
- **Related:** `Mathlib.CategoryTheory.Limits.Yoneda` (limit preservation)

**Difficulty:** hard

---

### 13. Isomorphism Characterization via Yoneda

**Location:** `Mathlib.CategoryTheory.Yoneda`

**Natural Language Statement:**
A morphism f : X → Y is an isomorphism if and only if for all objects T, composition with f gives a bijection Hom(T, X) → Hom(T, Y).

**Formal Definition:**
```lean
theorem isIso_iff_yoneda_map_bijective {X Y : C} (f : X ⟶ Y) :
  IsIso f ↔ ∀ T : C, Function.Bijective (fun (x : T ⟶ X) => x ≫ f)
```

**Proof Sketch:**
1. (⇒) If f is iso with inverse g, then (- ≫ g) is inverse to (- ≫ f)
2. (⇐) Take T = Y, get g : Y → X with gf = id. Take T = X to get fg = id

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Yoneda`

**Difficulty:** intermediate

---

## Limits and Colimits

### 14. Limits

**Location:** `Mathlib.CategoryTheory.Limits.IsLimit`

**Natural Language Statement:**
A limit of a diagram F : J → C is a universal cone over F: an object L with morphisms π_j : L → F(j) for each j ∈ J, such that for any other cone with vertex X, there exists a unique morphism u : X → L making all triangles commute.

**Key Structures:**

**Cone:**
```lean
structure Cone (F : J ⥤ C) where
  pt : C
  π : (const J).obj pt ⟶ F
```

**Limit:**
```lean
structure IsLimit {F : J ⥤ C} (t : Cone F) where
  lift : ∀ (s : Cone F), s.pt ⟶ t.pt
  fac : ∀ (s : Cone F) (j : J), lift s ≫ t.π.app j = s.π.app j
  uniq : ∀ (s : Cone F) (m : s.pt ⟶ t.pt), (∀ j, m ≫ t.π.app j = s.π.app j) → m = lift s
```

**Special Cases:**
- **Products:** `X ⨯ Y` - limit of discrete two-object diagram
- **Pullbacks:** limit of cospan `X → Z ← Y`
- **Equalizers:** limit of parallel pair `f, g : X ⇒ Y`
- **Terminal Object:** limit of empty diagram

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Limits.IsLimit`
- **Related:** `Mathlib.CategoryTheory.Limits.Shapes.Pullback.HasPullback`

**Difficulty:** intermediate

---

### 15. Colimits

**Location:** `Mathlib.CategoryTheory.Limits.IsLimit`

**Natural Language Statement:**
A colimit of a diagram F : J → C is a universal cocone under F: an object L with morphisms ι_j : F(j) → L for each j ∈ J, such that for any other cocone with vertex X, there exists a unique morphism u : L → X making all triangles commute.

**Key Structures:**

**Cocone:**
```lean
structure Cocone (F : J ⥤ C) where
  pt : C
  ι : F ⟶ (const J).obj pt
```

**Colimit:**
```lean
structure IsColimit {F : J ⥤ C} (t : Cocone F) where
  desc : ∀ (s : Cocone F), t.pt ⟶ s.pt
  fac : ∀ (s : Cocone F) (j : J), t.ι.app j ≫ desc s = s.ι.app j
  uniq : ∀ (s : Cocone F) (m : t.pt ⟶ s.pt), (∀ j, t.ι.app j ≫ m = s.ι.app j) → m = desc s
```

**Special Cases:**
- **Coproducts:** `X ⨿ Y` or `X ⊕ Y` - colimit of discrete two-object diagram
- **Pushouts:** colimit of span `Y ← X → Z`
- **Coequalizers:** colimit of parallel pair `f, g : X ⇒ Y`
- **Initial Object:** colimit of empty diagram

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Limits.IsLimit`

**Difficulty:** intermediate

---

### 16. Limit Uniqueness

**Location:** `Mathlib.CategoryTheory.Limits.IsLimit`

**Natural Language Statement:**
Limits are unique up to unique isomorphism: if L₁ and L₂ are both limits of diagram F, then there exists a unique isomorphism L₁ ≅ L₂ commuting with the cone morphisms.

**Formal Definition:**
```lean
def IsLimit.conePointUniqueUpToIso {t₁ t₂ : Cone F}
    (h₁ : IsLimit t₁) (h₂ : IsLimit t₂) : t₁.pt ≅ t₂.pt
```

**Proof Sketch:**
1. By universal property of L₁: ∃! u : L₂ → L₁ with compatible projections
2. By universal property of L₂: ∃! v : L₁ → L₂ with compatible projections
3. Then u ≫ v = id and v ≫ u = id by uniqueness

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Limits.IsLimit`

**Difficulty:** intermediate

---

## Adjunctions and Equivalences

### 17. Adjunctions

**Location:** `Mathlib.CategoryTheory.Adjunction.Basic`

**Natural Language Statement:**
An adjunction between categories C and D consists of functors F : C → D (left adjoint) and G : D → C (right adjoint), with natural bijections Hom_D(F(X), Y) ≅ Hom_C(X, G(Y)).

**Notation:** `F ⊣ G`

**Formal Definition:**
```lean
structure Adjunction (F : C ⥤ D) (G : D ⥤ C) where
  homEquiv : ∀ X Y, (F.obj X ⟶ Y) ≃ (X ⟶ G.obj Y)
  homEquiv_naturality_left_symm : ...
  homEquiv_naturality_right : ...
```

**Equivalent Formulation (Unit-Counit):**
- Unit: `η : 𝟭 C ⟶ F ⋙ G`
- Counit: `ε : G ⋙ F ⟶ 𝟭 D`
- Triangle identities hold

**Key Properties:**
- Left adjoints preserve colimits
- Right adjoints preserve limits
- Every adjunction induces a monad (on C) and comonad (on D)

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Adjunction.Basic`

**Difficulty:** hard

---

### 18. Equivalences of Categories

**Location:** `Mathlib.CategoryTheory.Equivalence`

**Natural Language Statement:**
An equivalence of categories consists of functors F : C → D and G : D → C with natural isomorphisms η : 𝟭_C ≅ G ∘ F and ε : F ∘ G ≅ 𝟭_D. Mathlib uses "half-adjoint equivalences" where one triangle identity is satisfied.

**Formal Definition:**
```lean
structure Equivalence (C : Type u₁) [Category.{v₁} C]
    (D : Type u₂) [Category.{v₂} D] where
  functor : C ⥤ D
  inverse : D ⥤ C
  unitIso : 𝟭 C ≅ functor ⋙ inverse
  counitIso : inverse ⋙ functor ≅ 𝟭 D
  functor_unitIso_comp : ...  -- one triangle identity
```

**Key Properties:**
- Every equivalence gives an adjunction
- An adjunction is an equivalence iff unit and counit are pointwise isos

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Equivalence`

**Difficulty:** hard

---

### 19. Mates and Conjugates

**Location:** `Mathlib.CategoryTheory.Adjunction.Mates`

**Natural Language Statement:**
Given two adjunctions L₁ ⊣ R₁ and L₂ ⊣ R₂, there is a bijection between natural transformations L₂ → L₁ and natural transformations R₁ → R₂. These corresponding transformations are called "mates" or "conjugates."

**Formal Definition:**
```lean
def conjugateEquiv {L₁ R₁ L₂ R₂ : C ⥤ D}
    (adj₁ : L₁ ⊣ R₁) (adj₂ : L₂ ⊣ R₂) : (L₂ ⟶ L₁) ≃ (R₁ ⟶ R₂)
```

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Adjunction.Mates`

**Difficulty:** hard

---

## Monads and Comonads

### 20. Monads

**Location:** `Mathlib.CategoryTheory.Monad.Basic`

**Natural Language Statement:**
A monad on category C consists of an endofunctor T : C → C with unit η : 𝟭 → T and multiplication μ : T ∘ T → T, satisfying associativity and unit laws.

**Note:** These are category-theoretic monads, not programmer's monads (though related).

**Formal Definition:**
```lean
structure Monad (C : Type u) [Category.{v} C] extends C ⥤ C where
  η : 𝟭 C ⟶ toFunctor
  μ : toFunctor ⋙ toFunctor ⟶ toFunctor
  assoc : ...  -- μ ∘ Tμ = μ ∘ μT
  left_unit : ...  -- μ ∘ ηT = id
  right_unit : ...  -- μ ∘ Tη = id
```

**From Adjunction:**
```lean
def Adjunction.toMonad {F : C ⥤ D} {G : D ⥤ C} (adj : F ⊣ G) : Monad C
```
- Endofunctor: T = G ∘ F
- Unit: from adjunction unit
- Multiplication: from R(ε_L) where ε is counit

**Related Constructions:**
- **Eilenberg-Moore Category:** Category of T-algebras
- **Kleisli Category:** `Kleisli T` - objects of C, morphisms X → T(Y)
- **Monads are Monoids:** See `Mathlib.CategoryTheory.Monad.EquivMon`

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Monad.Basic`
- **Related:** `Mathlib.CategoryTheory.Monad.Algebra`, `Mathlib.CategoryTheory.Monad.Kleisli`

**Difficulty:** hard

---

### 21. Comonads

**Location:** `Mathlib.CategoryTheory.Monad.Basic`

**Natural Language Statement:**
A comonad on category C consists of an endofunctor G : C → C with counit ε : G → 𝟭 and comultiplication δ : G → G ∘ G, satisfying coassociativity and counit laws.

**Formal Definition:**
```lean
structure Comonad (C : Type u) [Category.{v} C] extends C ⥤ C where
  ε : toFunctor ⟶ 𝟭 C
  δ : toFunctor ⟶ toFunctor ⋙ toFunctor
  coassoc : ...
  left_counit : ...
  right_counit : ...
```

**From Adjunction:**
```lean
def Adjunction.toComonad {F : C ⥤ D} {G : D ⥤ C} (adj : F ⊣ G) : Comonad D
```
- Endofunctor: U = F ∘ G
- Counit: from adjunction counit
- Comultiplication: from L(η_R) where η is unit

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Monad.Basic`

**Difficulty:** hard

---

## Advanced Topics

### 22. Abelian Categories

**Location:** `Mathlib.CategoryTheory.Abelian.Basic`

**Natural Language Statement:**
An abelian category is preadditive (hom-sets are abelian groups, composition is bilinear), has finite products, kernels and cokernels, and every monomorphism/epimorphism is normal.

**Formal Definition:**
```lean
class Abelian (C : Type u) [Category.{v} C] extends Preadditive C where
  -- has finite limits and colimits
  -- every mono is kernel of its cokernel
  -- every epi is cokernel of its kernel
```

**Key Properties:**
- Mono + Epi = Iso
- Images and coimages canonically isomorphic
- Freyd-Mitchell embedding into module category

**Examples:**
- Category of abelian groups (`Ab`)
- Category of R-modules (`ModuleCat R`)
- Sheaves of modules

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Abelian.Basic`
- **Related:** `Mathlib.CategoryTheory.Abelian.Images`, `Mathlib.CategoryTheory.Abelian.FreydMitchell`

**Difficulty:** very hard

---

### 23. Derived Categories (2025 Formalization)

**Location:** Mathlib4 (as of 2025)

**Natural Language Statement:**
The derived category D(C) of an abelian category C is obtained by formally inverting quasi-isomorphisms in the category of chain complexes. It has a triangulated structure.

**Recent Formalization:**
Joël Riou (Université Paris-Saclay) published formalization in July 2025 in Annals of Formalized Mathematics.

**Key Achievement:**
D(C) formalized as localization of unbounded cochain complexes with respect to quasi-isomorphisms, endowed with triangulated structure.

**Mathlib Support:** FULL (as of 2025)
- **Reference:** [HAL](https://hal.science/hal-04546712)

**Difficulty:** expert

---

### 24. Monoidal Categories

**Location:** `Mathlib.CategoryTheory.Monoidal.*`

**Natural Language Statement:**
A monoidal category is equipped with tensor product ⊗ : C × C → C, unit object I, and coherence isomorphisms (associator, unitors) satisfying pentagon and triangle equations.

**Coverage:**
- Monoidal categories
- Braided monoidal categories
- Symmetric monoidal categories
- Cartesian closed categories
- Mac Lane coherence theorem

**Mathlib Support:** FULL
- **Import:** `Mathlib.CategoryTheory.Monoidal.Functor` (and submodules)

**Difficulty:** very hard

---

## Notation Reference

### Core Notation

| Symbol | Unicode Input | Meaning |
|--------|---------------|---------|
| `⟶` | `\hom` or `\->` | Morphism |
| `𝟙` | `\b1` | Identity morphism |
| `≫` | `\gg` | Composition (diagrammatic: f then g) |
| `⊚` | `\oo` | Composition (classical: g then f) |
| `⥤` | `\func` | Functor type |
| `⋙` | `\ggg` | Functor composition |
| `𝟭` | `\b1` | Identity functor |
| `≅` | `\iso` | Isomorphism |
| `⊣` | `\dashv` | Adjunction |

### Natural Transformations

| Symbol | Meaning |
|--------|---------|
| `α.app X` | Component at object X |
| `F ⟶ G` | Natural transformation type |
| `σ ≫ τ` | Vertical composition |
| `σ ◫ τ` | Horizontal composition |

### Limits/Colimits

| Symbol | Meaning |
|--------|---------|
| `⨯` | Product |
| `⨿` or `⊕` | Coproduct |
| `⊓` | Inf/intersection |
| `⊔` | Sup/join |

### Opposites

| Symbol | Meaning |
|--------|---------|
| `Cᵒᵖ` | Opposite category |
| `op X` | Object in opposite |
| `unop X` | Unwrap opposite |

---

## Proof Automation

### Category-Specific Tactics

1. **`category`** - Discharges easy category theory goals
   - Defaults to `aesop_cat` (wrapper around aesop)
   - Set `mathlib.tactic.category.grind` to use grind tactic

2. **`@[simps]`** - Auto-generate simp lemmas for structures

3. **`simp`** with category lemmas:
   - `id_comp`, `comp_id`, `assoc` are simp lemmas
   - Naturality conditions often in simp normal form

4. **`ext`** - Extensionality for natural transformations

### Common Proof Patterns

**Universal Property:**
```lean
-- Use lift/desc with data, verify with hom_ext
```

**Naturality:**
```lean
-- Apply ext, use naturality lemma, simp with functor.map_comp
```

**Yoneda:**
```lean
-- Apply Yoneda.ext, construct natural isomorphism both ways
```

---

## Mathlib Import Paths

### Core

```lean
import Mathlib.CategoryTheory.Category.Basic    -- Category typeclass
import Mathlib.CategoryTheory.Functor.Basic     -- Functors
import Mathlib.CategoryTheory.Functor.Category  -- Functor categories
import Mathlib.CategoryTheory.NatTrans          -- Natural transformations
import Mathlib.CategoryTheory.Iso               -- Isomorphisms
import Mathlib.CategoryTheory.Equivalence       -- Equivalences
```

### Examples

```lean
import Mathlib.CategoryTheory.Types.Basic       -- Category of types
import Mathlib.CategoryTheory.Groupoid          -- Groupoids
```

### Universal Constructions

```lean
import Mathlib.CategoryTheory.Limits.IsLimit                         -- Limits/colimits
import Mathlib.CategoryTheory.Limits.Shapes.Pullback.HasPullback     -- Pullbacks
import Mathlib.CategoryTheory.Limits.Constructions.Pullbacks         -- Construction
import Mathlib.CategoryTheory.Limits.Preserves.Filtered              -- Filtered colimits
```

### Adjunctions and Yoneda

```lean
import Mathlib.CategoryTheory.Adjunction.Basic  -- Adjunctions
import Mathlib.CategoryTheory.Adjunction.Mates  -- Mates/conjugates
import Mathlib.CategoryTheory.Yoneda            -- Yoneda lemma
import Mathlib.CategoryTheory.Limits.Yoneda     -- Yoneda and limits
```

### Monads

```lean
import Mathlib.CategoryTheory.Monad.Basic       -- Monads and comonads
import Mathlib.CategoryTheory.Monad.Algebra     -- Eilenberg-Moore
import Mathlib.CategoryTheory.Monad.Adjunction  -- Monad from adjunction
import Mathlib.CategoryTheory.Monad.Kleisli     -- Kleisli category
import Mathlib.CategoryTheory.Monad.Types       -- Connection to programmer monads
import Mathlib.CategoryTheory.Monad.EquivMon    -- Monads are monoids
```

### Abelian and Homological

```lean
import Mathlib.CategoryTheory.Preadditive.Basic           -- Preadditive
import Mathlib.CategoryTheory.Abelian.Basic               -- Abelian categories
import Mathlib.CategoryTheory.Abelian.Images              -- Images/coimages
import Mathlib.CategoryTheory.Abelian.FreydMitchell       -- Embedding theorem
```

---

## Difficulty Classification

### Beginner (100+ examples recommended)

- Category axioms verification
- Functor axioms verification
- Identity and composition laws
- Simple functor examples (identity, constant, Type category)
- Basic natural transformations

### Intermediate (50+ examples)

- Naturality condition proofs
- Functor category constructions
- Products, coproducts, pullbacks, pushouts
- Limit/colimit definitions
- Isomorphism characterizations

### Hard (30+ examples)

- Yoneda lemma and applications
- Adjunction constructions
- Equivalence of categories
- Representable functors
- Limit uniqueness

### Very Hard / Expert (10-20 examples)

- Monad/comonad theory
- Mates and conjugates
- Abelian categories
- Kan extensions
- Freyd-Mitchell embedding
- Derived categories

---

## Sources

### Official Documentation

- [Mathlib4 Category.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/CategoryTheory/Category/Basic.html)
- [Mathlib4 Functor.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/CategoryTheory/Functor/Basic.html)
- [Mathlib4 NatTrans](https://leanprover-community.github.io/mathlib4_docs/Mathlib/CategoryTheory/NatTrans.html)
- [Mathlib4 Yoneda](https://leanprover-community.github.io/mathlib4_docs/Mathlib/CategoryTheory/Yoneda.html)
- [Mathlib4 Adjunction.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/CategoryTheory/Adjunction/Basic.html)
- [Maths in Lean: Category Theory](https://leanprover-community.github.io/theories/category_theory.html)

### Research Papers

- [Derived Categories (Riou, 2025)](https://hal.science/hal-04546712)
- [∞-Categorical Yoneda (Kudasov, 2024)](https://dl.acm.org/doi/10.1145/3636501.3636945)

### Textbooks

- [Categories for the Working Mathematician - Mac Lane](https://en.wikipedia.org/wiki/Categories_for_the_Working_Mathematician)
- [Category Theory - Awodey](http://files.farka.eu/pub/Awodey_S._Category_Theory(en)(305s).pdf)
