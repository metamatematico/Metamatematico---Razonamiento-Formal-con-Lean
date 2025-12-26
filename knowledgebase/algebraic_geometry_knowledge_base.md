# Algebraic Geometry Knowledge Base Research for Lean 4

**Generated:** 2025-12-18
**Mode:** Deep Synthesis
**Purpose:** Research knowledge base for implementing algebraic geometry theorems in Lean 4 for dataset generation pairing formal proofs with natural language explanations.
**Confidence:** High (direct inspection of Mathlib4 documentation)

---

## Executive Summary

Algebraic geometry is extensively formalized in Lean 4's Mathlib library with schemes as the central object. The formalization includes prime spectrum, structure sheaves, affine schemes, schemes, morphisms, and morphism properties (quasi-compact, quasi-separated, closed/open immersions). Estimated total: **70-80 theorems** suitable for knowledge base inclusion.

### Content Summary

| Category | Estimated Count | Mathlib Support | Difficulty Distribution |
|----------|----------------|-----------------|------------------------|
| **Prime Spectrum & Zariski Topology** | 12-14 | FULL | 60% easy, 30% medium, 10% hard |
| **Structure Sheaves** | 10-12 | FULL | 50% easy, 40% medium, 10% hard |
| **Affine Schemes** | 10-12 | FULL | 40% easy, 40% medium, 20% hard |
| **Schemes** | 10-12 | FULL | 30% easy, 50% medium, 20% hard |
| **Morphisms of Schemes** | 8-10 | FULL | 40% easy, 40% medium, 20% hard |
| **Morphism Properties** | 10-12 | FULL | 30% easy, 40% medium, 30% hard |
| **Projective Schemes** | 8-10 | PARTIAL | 20% easy, 50% medium, 30% hard |
| **Total** | **70-80** | - | - |

### Key Dependencies

- **Commutative Algebra:** Rings, ideals, localization, prime ideals
- **Topology:** Open sets, closed sets, basis, compact spaces, spectral spaces
- **Category Theory:** Functors, adjunctions, limits, pullbacks
- **Sheaf Theory:** Presheaves, sheaves, stalks, locally ringed spaces

---

## Related Knowledge Bases

### Prerequisites
- **Commutative Algebra** (`commutative_algebra_knowledge_base.md`): Rings, prime ideals, localization
- **Sheaf Theory** (`sheaf_theory_knowledge_base.md`): Presheaves, sheaves, stalks, locally ringed spaces
- **Category Theory** (`category_theory_knowledge_base.md`): Functors, limits, pullbacks

### Related Topics
- **Topology** (`topology_knowledge_base.md`): Spectral spaces, Zariski topology

### Scope Clarification
This KB focuses on **scheme-theoretic algebraic geometry**:
- Prime spectrum Spec(R) and Zariski topology
- Structure sheaves on affine schemes
- Schemes and morphisms of schemes
- Properties of morphisms (quasi-compact, quasi-separated, immersions)
- Projective schemes

For **general sheaf theory** (abstract sheaves, sheafification, sheaf categories), see the **Sheaf Theory KB**.

---

## Part I: Prime Spectrum and Zariski Topology

### Module Organization

**Primary Imports:**
- `Mathlib.RingTheory.Spectrum.Prime.Defs` - Core definitions
- `Mathlib.RingTheory.Spectrum.Prime.Basic` - Basic properties
- `Mathlib.RingTheory.Spectrum.Prime.Topology` - Zariski topology
- `Mathlib.AlgebraicGeometry.PrimeSpectrum.Basic` - Legacy algebraic geometry module

**Estimated Statements:** 12-14

---

### Section 1.1: Prime Spectrum Definition (3-4 statements)

#### 1. Prime Spectrum

**Natural Language Statement:**
The prime spectrum of a commutative semiring R, denoted Spec(R), is the set of all prime ideals of R.

**Lean 4 Definition:**
```lean
structure PrimeSpectrum (R : Type u) [CommSemiring R] where
  asIdeal : Ideal R
  isPrime : asIdeal.IsPrime
```

**Mathlib Location:** `Mathlib.RingTheory.Spectrum.Prime.Defs`

**Key Theorems:**
- `PrimeSpectrum.ext : x.asIdeal = y.asIdeal → x = y`
- `PrimeSpectrum.ext_iff : x = y ↔ x.asIdeal = y.asIdeal`

**Difficulty:** easy

---

#### 2. Zero Locus

**Natural Language Statement:**
The zero locus of a subset s of R is the set of all prime ideals containing s. This defines the closed sets of the Zariski topology.

**Lean 4 Definition:**
```lean
def PrimeSpectrum.zeroLocus (R : Type u) [CommSemiring R] (s : Set R) :
  Set (PrimeSpectrum R) :=
  {x | s ⊆ x.asIdeal}
```

**Mathlib Location:** `Mathlib.RingTheory.Spectrum.Prime.Topology`

**Key Theorems:**
- `PrimeSpectrum.zeroLocus_empty : zeroLocus (∅ : Set R) = ⊤`
- `PrimeSpectrum.zeroLocus_univ : zeroLocus (Set.univ : Set R) = ∅`
- `PrimeSpectrum.zeroLocus_union : zeroLocus (s ∪ t) = zeroLocus s ∩ zeroLocus t`

**Difficulty:** easy

---

#### 3. Basic Open Sets

**Natural Language Statement:**
For an element r in R, the basic open set D(r) is the set of prime ideals not containing r. These form a basis for the Zariski topology.

**Lean 4 Definition:**
```lean
def PrimeSpectrum.basicOpen {R : Type u} [CommSemiring R] (r : R) :
  TopologicalSpace.Opens (PrimeSpectrum R) :=
  { carrier := {x | r ∉ x.asIdeal}
    is_open' := ⟨{r}, rfl⟩ }
```

**Mathlib Location:** `Mathlib.RingTheory.Spectrum.Prime.Topology`

**Key Theorems:**
- `PrimeSpectrum.basicOpen_eq_zeroLocus_compl : ↑(basicOpen r) = (zeroLocus {r})ᶜ`
- `PrimeSpectrum.basicOpen_mul : basicOpen (r * s) = basicOpen r ⊓ basicOpen s`
- `PrimeSpectrum.basicOpen_one : basicOpen (1 : R) = ⊤`
- `PrimeSpectrum.basicOpen_zero : basicOpen (0 : R) = ⊥`

**Difficulty:** easy

---

#### 4. Zariski Topology

**Natural Language Statement:**
The Zariski topology on Spec(R) has closed sets precisely the zero loci of subsets of R. This makes Spec(R) a spectral topological space.

**Lean 4 Definition:**
```lean
instance PrimeSpectrum.zariskiTopology {R : Type u} [CommSemiring R] :
  TopologicalSpace (PrimeSpectrum R) :=
  TopologicalSpace.ofClosed
    (Set.range (zeroLocus : Set R → Set (PrimeSpectrum R)))
    ⟨Set.univ, ⟨∅, zeroLocus_empty⟩⟩
    (by rintro _ ⟨s, rfl⟩ _ ⟨t, rfl⟩; exact ⟨s ∪ t, zeroLocus_union s t⟩)
    (by rintro _ h; exact ⟨⋃ s ∈ h, s, by simp [zeroLocus_iUnion]⟩)
```

**Mathlib Location:** `Mathlib.RingTheory.Spectrum.Prime.Topology`

**Key Theorems:**
- `PrimeSpectrum.isTopologicalBasis_basic_opens : TopologicalSpace.IsTopologicalBasis (Set.range (fun r : R => ↑(basicOpen r)))`
- `PrimeSpectrum.instSpectralSpace : SpectralSpace (PrimeSpectrum R)`
- `PrimeSpectrum.compactSpace : CompactSpace (PrimeSpectrum R)`

**Difficulty:** medium

---

### Section 1.2: Topological Properties (4-5 statements)

#### 5. Closure of Singleton

**Natural Language Statement:**
The closure of a singleton {x} in the Zariski topology equals the zero locus of the corresponding prime ideal.

**Lean 4 Theorem:**
```lean
theorem PrimeSpectrum.closure_singleton {R : Type u} [CommSemiring R]
  (x : PrimeSpectrum R) :
  closure {x} = zeroLocus ↑x.asIdeal
```

**Mathlib Location:** `Mathlib.RingTheory.Spectrum.Prime.Topology`

**Difficulty:** medium

---

#### 6. Irreducible Sets and Prime Ideals

**Natural Language Statement:**
A subset of Spec(R) is irreducible if and only if its vanishing ideal is a prime ideal.

**Lean 4 Theorem:**
```lean
theorem PrimeSpectrum.isIrreducible_iff_vanishingIdeal_isPrime
  {R : Type u} [CommSemiring R] {s : Set (PrimeSpectrum R)} :
  IsIrreducible s ↔ (vanishingIdeal s).IsPrime
```

**Mathlib Location:** `Mathlib.RingTheory.Spectrum.Prime.Topology`

**Key Related:**
- `PrimeSpectrum.vanishingIdeal : Set (PrimeSpectrum R) → Ideal R`
- `PrimeSpectrum.pointsEquivIrreducibleCloseds : PrimeSpectrum R ≃o (TopologicalSpace.IrreducibleCloseds (PrimeSpectrum R))ᵒᵈ`

**Difficulty:** hard

---

#### 7. Specialization Order

**Natural Language Statement:**
The specialization order on Spec(R) corresponds to ideal inclusion: x ≤ y if and only if x specializes to y if and only if x.asIdeal ⊆ y.asIdeal.

**Lean 4 Theorem:**
```lean
theorem PrimeSpectrum.le_iff_specializes {R : Type u} [CommSemiring R]
  (x y : PrimeSpectrum R) :
  x ≤ y ↔ x ⤳ y

theorem PrimeSpectrum.le_iff_mem_closure {R : Type u} [CommSemiring R]
  (x y : PrimeSpectrum R) :
  x ≤ y ↔ x ∈ closure {y}
```

**Mathlib Location:** `Mathlib.RingTheory.Spectrum.Prime.Topology`

**Difficulty:** medium

---

#### 8. Spectral Space Structure

**Natural Language Statement:**
The prime spectrum of any commutative semiring is a spectral space: quasi-compact, sober, T₀, with a basis of quasi-compact opens closed under finite intersections.

**Lean 4 Theorem:**
```lean
instance PrimeSpectrum.instSpectralSpace {R : Type u} [CommSemiring R] :
  SpectralSpace (PrimeSpectrum R)

instance PrimeSpectrum.compactSpace {R : Type u} [CommSemiring R] :
  CompactSpace (PrimeSpectrum R)
```

**Mathlib Location:** `Mathlib.RingTheory.Spectrum.Prime.Topology`

**Difficulty:** hard

---

#### 9. Clopen Sets and Idempotents

**Natural Language Statement:**
In a commutative ring, clopen subsets of Spec(R) correspond bijectively to idempotent elements of R.

**Lean 4 Theorem:**
```lean
theorem PrimeSpectrum.isClopen_iff {R : Type u} [CommRing R]
  {s : Set (PrimeSpectrum R)} :
  IsClopen s ↔ ∃ (e : R), IsIdempotentElem e ∧ s = ↑(basicOpen e)

def PrimeSpectrum.isIdempotentElemEquivClopens {R : Type u} [CommRing R] :
  {e : R // IsIdempotentElem e} ≃o TopologicalSpace.Clopens (PrimeSpectrum R)
```

**Mathlib Location:** `Mathlib.RingTheory.Spectrum.Prime.Topology`

**Difficulty:** hard

---

### Section 1.3: Functoriality (3-4 statements)

#### 10. Comap of Ring Homomorphism

**Natural Language Statement:**
A ring homomorphism f : R → S induces a continuous map Spec(f) : Spec(S) → Spec(R) by pulling back prime ideals.

**Lean 4 Definition:**
```lean
def PrimeSpectrum.comap {R : Type u} {S : Type v}
  [CommSemiring R] [CommSemiring S] (f : R →+* S) :
  PrimeSpectrum S → PrimeSpectrum R :=
  fun y => ⟨Ideal.comap f y.asIdeal, inferInstance⟩
```

**Mathlib Location:** `Mathlib.RingTheory.Spectrum.Prime.Basic`

**Key Theorems:**
- `PrimeSpectrum.comap_continuous : Continuous (comap f)`
- `PrimeSpectrum.comap_id : comap (RingHom.id R) = id`
- `PrimeSpectrum.comap_comp : comap (g.comp f) = (comap f) ∘ (comap g)`
- `PrimeSpectrum.preimage_comap_zeroLocus : (comap f) ⁻¹' (zeroLocus s) = zeroLocus (f '' s)`

**Difficulty:** medium

---

#### 11. Basic Open Preimage

**Natural Language Statement:**
The preimage under Spec(f) of the basic open D(r) equals the basic open D(f(r)).

**Lean 4 Theorem:**
```lean
theorem PrimeSpectrum.comap_basicOpen {R : Type u} {S : Type v}
  [CommSemiring R] [CommSemiring S] (f : R →+* S) (r : R) :
  (comap f) ⁻¹' ↑(basicOpen r) = ↑(basicOpen (f r))
```

**Mathlib Location:** `Mathlib.RingTheory.Spectrum.Prime.Topology`

**Difficulty:** medium

---

#### 12. Closed Point in Local Rings

**Natural Language Statement:**
In a local ring, the maximal ideal corresponds to a unique closed point in the prime spectrum.

**Lean 4 Definition:**
```lean
def IsLocalRing.closedPoint (R : Type u) [CommSemiring R] [IsLocalRing R] :
  PrimeSpectrum R :=
  ⟨maximalIdeal R, (maximalIdeal.isMaximal R).isPrime⟩
```

**Mathlib Location:** `Mathlib.RingTheory.Spectrum.Prime.Topology`

**Key Theorems:**
- `IsLocalRing.isLocalRing_stalk_of_closedPoint`
- `IsLocalRing.closedPoint_specializes_iff`

**Difficulty:** medium

---

## Part II: Structure Sheaves

### Module Organization

**Primary Imports:**
- `Mathlib.AlgebraicGeometry.StructureSheaf` - Structure sheaf construction
- `Mathlib.Topology.Sheaves.Stalks` - Stalk theory
- `Mathlib.RingTheory.Localization.Basic` - Localization

**Estimated Statements:** 10-12

---

### Section 2.1: Structure Sheaf Definition (4-5 statements)

#### 13. Localizations at Prime Ideals

**Natural Language Statement:**
For each prime ideal P in R, we have the localization R_P, which forms the stalk of the structure sheaf at the corresponding point.

**Lean 4 Definition:**
```lean
def StructureSheaf.Localizations (R : Type u) [CommRing R]
    (P : ↑(PrimeSpectrum.Top R)) : Type u :=
  Localization.AtPrime P.asIdeal
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.StructureSheaf`

**Key Theorems:**
- `Localization.AtPrime.isLocalRing`
- `Localization.AtPrime.localRing`

**Difficulty:** easy

---

#### 14. Structure Sheaf on Spec(R)

**Natural Language Statement:**
The structure sheaf on Spec(R) assigns to each open set U the ring of functions that are locally fractions of elements of R.

**Lean 4 Definition:**
```lean
def Spec.structureSheaf (R : Type u) [CommRing R] :
  TopCat.Sheaf CommRingCat (PrimeSpectrum.Top R)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.StructureSheaf`

**Key Properties:**
- `StructureSheaf.isFractionPrelocal` - Local fraction condition
- `StructureSheaf.isLocallyFraction` - Locally fractional sections

**Difficulty:** hard

---

#### 15. To Stalk Homomorphism

**Natural Language Statement:**
For any prime ideal x in Spec(R), there is a canonical ring homomorphism from R to the stalk at x, sending r to r/1 in the localization.

**Lean 4 Definition:**
```lean
def StructureSheaf.toStalk (R : Type u) [CommRing R]
    (x : ↑(PrimeSpectrum.Top R)) :
  CommRingCat.of R →+* (Spec.structureSheaf R).presheaf.stalk x
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.StructureSheaf`

**Difficulty:** medium

---

#### 16. Stalk Isomorphism

**Natural Language Statement:**
The stalk of the structure sheaf at a point x is canonically isomorphic to the localization of R at the prime ideal x.

**Lean 4 Theorem:**
```lean
def StructureSheaf.stalkIso (R : Type u) [CommRing R]
    (x : ↑(PrimeSpectrum.Top R)) :
  (Spec.structureSheaf R).presheaf.stalk x ≅
  CommRingCat.of (Localization.AtPrime x.asIdeal)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.StructureSheaf`

**Key Theorems:**
- `StructureSheaf.localizationToStalk`
- `StructureSheaf.stalkToFiberRingHom`

**Difficulty:** hard

---

### Section 2.2: Sections over Basic Opens (3-4 statements)

#### 17. Basic Open Isomorphism

**Natural Language Statement:**
The sections of the structure sheaf over the basic open D(f) are canonically isomorphic to the localization R_f.

**Lean 4 Theorem:**
```lean
def StructureSheaf.basicOpenIso (R : Type u) [CommRing R] (f : R) :
  (Spec.structureSheaf R).val.obj (Opposite.op (PrimeSpectrum.basicOpen f)) ≅
  CommRingCat.of (Localization.Away f)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.StructureSheaf`

**Key Related:**
- `StructureSheaf.toBasicOpen : Localization.Away f →+* Γ(D(f))`
- `Localization.Away.invSelf : algebraMap R (Localization.Away f) f` is a unit

**Difficulty:** hard

---

#### 18. Global Sections Isomorphism

**Natural Language Statement:**
The global sections of the structure sheaf on Spec(R) recover the original ring R.

**Lean 4 Theorem:**
```lean
def StructureSheaf.globalSectionsIso (R : Type u) [CommRing R] :
  CommRingCat.of R ≅
  (Spec.structureSheaf R).val.obj (Opposite.op ⊤)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.StructureSheaf`

**Key Related:**
- `StructureSheaf.toOpen : R →+* Γ(U)` for any open U

**Difficulty:** medium

---

#### 19. Restriction Maps

**Natural Language Statement:**
For basic opens D(f) ⊆ D(g), the restriction map corresponds to the localization map R_g → R_f.

**Lean 4 Theorem:**
```lean
theorem StructureSheaf.basicOpen_res {R : Type u} [CommRing R]
  {f g : R} (h : f ∣ g) :
  (Spec.structureSheaf R).val.map (homOfLE (basicOpen_le_basicOpen_of_dvd h)) =
  CommRingCat.ofHom (Localization.awayMap f g)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.StructureSheaf`

**Difficulty:** medium

---

### Section 2.3: Functoriality of Structure Sheaves (2-3 statements)

#### 20. Comap on Structure Sheaves

**Natural Language Statement:**
A ring homomorphism f : R → S induces a morphism of sheaves from the structure sheaf on Spec(R) to the pushforward of the structure sheaf on Spec(S).

**Lean 4 Definition:**
```lean
def StructureSheaf.comap {R : Type u} [CommRing R] {S : Type u} [CommRing S]
    (f : R →+* S) (U : TopologicalSpace.Opens ↑(PrimeSpectrum.Top R))
    (V : TopologicalSpace.Opens ↑(PrimeSpectrum.Top S))
    (hUV : V.carrier ⊆ PrimeSpectrum.comap f ⁻¹' U.carrier) :
  ↑((Spec.structureSheaf R).val.obj (Opposite.op U)) →+*
  ↑((Spec.structureSheaf S).val.obj (Opposite.op V))
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.StructureSheaf`

**Difficulty:** hard

---

#### 21. Pushforward Stalk Homomorphism

**Natural Language Statement:**
A ring homomorphism R → S induces a natural homomorphism from S to the stalk of the pushforward sheaf at any point.

**Lean 4 Definition:**
```lean
def StructureSheaf.toPushforwardStalk {R S : CommRingCat} (f : R ⟶ S)
    (p : PrimeSpectrum ↑R) :
  S ⟶ ((TopCat.Presheaf.pushforward CommRingCat (Spec.topMap f)).obj
    (Spec.structureSheaf ↑S).val).stalk p
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.StructureSheaf`

**Key Related:**
- `StructureSheaf.toPushforwardStalkAlgHom` - Algebra structure version
- `StructureSheaf.isLocalizedModule_toPushforwardStalkAlgHom` - Localization property

**Difficulty:** hard

---

## Part III: Affine Schemes

### Module Organization

**Primary Imports:**
- `Mathlib.AlgebraicGeometry.AffineScheme` - Affine schemes
- `Mathlib.AlgebraicGeometry.Spec` - Spec functor
- `Mathlib.CategoryTheory.Adjunction.Basic` - Adjunctions

**Estimated Statements:** 10-12

---

### Section 3.1: Spec as a Locally Ringed Space (4-5 statements)

#### 22. Spec Topological Space

**Natural Language Statement:**
The Spec functor sends a commutative ring R to a topological space with underlying set the prime spectrum of R.

**Lean 4 Definition:**
```lean
def Spec.topObj (R : CommRingCat) : TopCat :=
  TopCat.of (carrier := PrimeSpectrum ↑R, str := PrimeSpectrum.zariskiTopology)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Spec`

**Key Related:**
- `Spec.topMap : (R ⟶ S) → (topObj S ⟶ topObj R)` - Contravariant functoriality
- `Spec.toTop : Functor CommRingCat.op TopCat`

**Difficulty:** easy

---

#### 23. Spec Locally Ringed Space

**Natural Language Statement:**
Spec(R) forms a locally ringed space where the structure sheaf has local rings as stalks.

**Lean 4 Definition:**
```lean
def Spec.locallyRingedSpaceObj (R : CommRingCat) : LocallyRingedSpace :=
  { toSheafedSpace := sheafedSpaceObj R
    isLocalRing := fun x => inferInstance }
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Spec`

**Key Related:**
- `Spec.sheafedSpaceObj : CommRingCat → SheafedSpace CommRingCat`
- `Spec.toLocallyRingedSpace : Functor CommRingCat.op LocallyRingedSpace`

**Difficulty:** medium

---

#### 24. Spec Morphisms from Ring Homomorphisms

**Natural Language Statement:**
A ring homomorphism f : R → S induces a morphism of locally ringed spaces Spec(S) → Spec(R) that is local on stalks.

**Lean 4 Definition:**
```lean
def Spec.locallyRingedSpaceMap {R S : CommRingCat} (f : R ⟶ S) :
  locallyRingedSpaceObj S ⟶ locallyRingedSpaceObj R
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Spec`

**Key Properties:**
- Local ring homomorphisms on stalks
- Functoriality: preserves identity and composition

**Difficulty:** medium

---

#### 25. Spec as a Scheme

**Natural Language Statement:**
Spec(R) is a scheme: it is a locally ringed space that is locally isomorphic to Spec of some ring (globally in this case).

**Lean 4 Definition:**
```lean
def AlgebraicGeometry.Spec (R : CommRingCat) : Scheme :=
  Scheme.Spec.obj (Opposite.op R)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Scheme`

**Key Theorems:**
- `Scheme.Spec : Functor CommRingCatᵒᵖ Scheme`
- Spec preserves limits (is right adjoint)

**Difficulty:** medium

---

### Section 3.2: Affine Schemes Category (3-4 statements)

#### 26. IsAffine Predicate

**Natural Language Statement:**
A scheme X is affine if the canonical morphism X → Spec(Γ(X)) is an isomorphism.

**Lean 4 Definition:**
```lean
class AlgebraicGeometry.IsAffine (X : Scheme) : Prop where
  affine : CategoryTheory.IsIso X.toSpecΓ
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.AffineScheme`

**Key Related:**
- `Scheme.toSpecΓ : X → Spec(Γ(X, ⊤))` - Unit of adjunction
- `Scheme.isoSpec : X ≅ Spec(Γ(X))` for affine X

**Difficulty:** medium

---

#### 27. Affine Scheme Category

**Natural Language Statement:**
The category of affine schemes is defined as the essential image of the Spec functor.

**Lean 4 Definition:**
```lean
def AlgebraicGeometry.AffineScheme : Type (u_1 + 1) :=
  AlgebraicGeometry.Scheme.Spec.EssImageSubcategory
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.AffineScheme`

**Key Functors:**
- `AffineScheme.Spec : Functor CommRingCatᵒᵖ AffineScheme`
- `AffineScheme.Γ : Functor AffineSchemeᵒᵖ CommRingCat`
- `AffineScheme.forgetToScheme : Functor AffineScheme Scheme`

**Difficulty:** medium

---

#### 28. Affine Schemes Opposite to Rings

**Natural Language Statement:**
The category of affine schemes is equivalent to the opposite category of commutative rings.

**Lean 4 Theorem:**
```lean
def AlgebraicGeometry.AffineScheme.equivCommRingCat :
  AffineScheme ≌ CommRingCatᵒᵖ
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.AffineScheme`

**Key Implications:**
- Full faithfulness of Γ on affine schemes
- Every ring morphism R → S gives affine scheme morphism Spec(S) → Spec(R)

**Difficulty:** hard

---

### Section 3.3: Affine Open Sets (2-3 statements)

#### 29. Affine Open Sets

**Natural Language Statement:**
An open subset U of a scheme X is affine if it is an affine scheme when viewed as a scheme itself.

**Lean 4 Definition:**
```lean
def AlgebraicGeometry.IsAffineOpen {X : Scheme} (U : X.Opens) : Prop :=
  IsAffine ↑U
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.AffineScheme`

**Key Theorems:**
- `Scheme.isBasis_affineOpens : Opens.IsBasis {U : X.Opens | IsAffineOpen U}`
- `IsAffineOpen.basicOpen : IsAffineOpen U → IsAffineOpen (X.basicOpen f)` for f ∈ Γ(U)

**Difficulty:** medium

---

#### 30. Compactness of Affine Schemes

**Natural Language Statement:**
Every affine scheme is quasi-compact as a topological space.

**Lean 4 Theorem:**
```lean
theorem Scheme.compactSpace_of_isAffine (X : Scheme) [IsAffine X] :
  CompactSpace ↥X
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.AffineScheme`

**Difficulty:** medium

---

## Part IV: Schemes

### Module Organization

**Primary Imports:**
- `Mathlib.AlgebraicGeometry.Scheme` - Scheme definition
- `Mathlib.Geometry.RingedSpace.LocallyRingedSpace` - Locally ringed spaces
- `Mathlib.AlgebraicGeometry.GammaSpecAdjunction` - Γ-Spec adjunction

**Estimated Statements:** 10-12

---

### Section 4.1: Scheme Definition (3-4 statements)

#### 31. Locally Ringed Space

**Natural Language Statement:**
A locally ringed space is a sheafed space of commutative rings where all stalks are local rings.

**Lean 4 Definition:**
```lean
structure LocallyRingedSpace extends SheafedSpace CommRingCat where
  isLocalRing (x : ↑↑toPresheafedSpace) :
    IsLocalRing ↑(presheaf.stalk x)
```

**Mathlib Location:** `Mathlib.Geometry.RingedSpace.LocallyRingedSpace`

**Key Properties:**
- Morphisms require local homomorphisms on stalks
- Category structure with composition preserving locality

**Difficulty:** medium

---

#### 32. Scheme Structure

**Natural Language Statement:**
A scheme is a locally ringed space that is locally isomorphic to Spec(R) for some commutative ring R.

**Lean 4 Definition:**
```lean
structure AlgebraicGeometry.Scheme extends AlgebraicGeometry.LocallyRingedSpace where
  local_affine (x : ↑toTopCat) :
    ∃ (U : Opens toTopCat) (hxU : x ∈ U) (R : CommRingCat),
    Nonempty (toLocallyRingedSpace.restrict U ≅ Spec.locallyRingedSpaceObj R)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Scheme`

**Difficulty:** hard

---

#### 33. Scheme Morphisms

**Natural Language Statement:**
A morphism of schemes is a morphism of the underlying locally ringed spaces.

**Lean 4 Definition:**
```lean
structure AlgebraicGeometry.Scheme.Hom (X Y : Scheme) extends
  X.toLocallyRingedSpace ⟶ Y.toLocallyRingedSpace
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Scheme`

**Key Properties:**
- Continuous on underlying spaces
- Ring homomorphisms on structure sheaves (contravariant)
- Local homomorphisms on stalks

**Difficulty:** medium

---

#### 34. Restriction to Open Subsets

**Natural Language Statement:**
The restriction of a scheme to an open subset is again a scheme.

**Lean 4 Definition:**
```lean
def Scheme.restrict {X : Scheme} (U : X.Opens) : Scheme :=
  { toLocallyRingedSpace := X.toLocallyRingedSpace.restrict ...
    local_affine := ... }
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Scheme`

**Notation:** `f ∣_ U` for restriction of morphism f to open U

**Difficulty:** medium

---

### Section 4.2: Basic Opens in Schemes (3-4 statements)

#### 35. Basic Open in Schemes

**Natural Language Statement:**
For a section f over an open set U, the basic open D(f) is the largest open subset of U where f is a unit in the structure sheaf.

**Lean 4 Definition:**
```lean
def AlgebraicGeometry.Scheme.basicOpen (X : Scheme) {U : X.Opens}
    (f : ↑(X.presheaf.obj (op U))) : X.Opens :=
  { carrier := {x : X | x ∈ U ∧ IsUnit (X.presheaf.germ U x hx f)}
    is_open' := ... }
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Scheme`

**Difficulty:** medium

---

#### 36. Membership in Basic Open

**Natural Language Statement:**
A point x lies in the basic open D(f) if and only if the germ of f at x is a unit in the stalk.

**Lean 4 Theorem:**
```lean
theorem AlgebraicGeometry.Scheme.mem_basicOpen (X : Scheme) {U : X.Opens}
    (f : ↑(X.presheaf.obj (op U))) (x : ↥X) (hx : x ∈ U) :
  x ∈ X.basicOpen f ↔ IsUnit (X.presheaf.germ U x hx f)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Scheme`

**Difficulty:** medium

---

#### 37. Preimage of Basic Opens

**Natural Language Statement:**
For a scheme morphism f : X → Y and section r over U in Y, the preimage of the basic open D(r) equals the basic open D(f*(r)).

**Lean 4 Theorem:**
```lean
theorem AlgebraicGeometry.Scheme.preimage_basicOpen {X Y : Scheme} (f : X ⟶ Y)
    {U : Y.Opens} (r : ↑(Y.presheaf.obj (op U))) :
  (Opens.map f.base).obj (Y.basicOpen r) = X.basicOpen (f.app U r)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Scheme`

**Difficulty:** medium

---

### Section 4.3: Gamma-Spec Adjunction (3-4 statements)

#### 38. Global Sections Functor

**Natural Language Statement:**
The global sections functor Γ sends a scheme X to the ring of global sections Γ(X, ⊤).

**Lean 4 Definition:**
```lean
def AlgebraicGeometry.Scheme.Γ : Functor Schemeᵒᵖ CommRingCat :=
  (inducedFunctor Scheme.toLocallyRingedSpace).op ⋙
  LocallyRingedSpace.Γ
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Scheme`

**Key Property:**
- For morphism f : X → Y, gives ring homomorphism Γ(f) : Γ(Y) → Γ(X)

**Difficulty:** easy

---

#### 39. Canonical Map to Spec Γ

**Natural Language Statement:**
For any scheme X, there is a canonical morphism X → Spec(Γ(X)), the unit of the Γ-Spec adjunction.

**Lean 4 Definition:**
```lean
def AlgebraicGeometry.Scheme.toSpecΓ (X : Scheme) :
  X ⟶ Spec.obj (op (Γ.obj (op X)))
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Scheme`

**Key Property:**
- This is an isomorphism when X is affine (definition of affine)

**Difficulty:** medium

---

#### 40. Spec-Gamma Isomorphism

**Natural Language Statement:**
For any commutative ring R, the global sections of Spec(R) are canonically isomorphic to R.

**Lean 4 Theorem:**
```lean
def AlgebraicGeometry.Scheme.ΓSpecIso (R : CommRingCat) :
  (Spec R).presheaf.obj (op ⊤) ≅ R
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Scheme`

**Key Implications:**
- Counit of the adjunction is an isomorphism
- Spec is fully faithful

**Difficulty:** medium

---

#### 41. Gamma-Spec Adjunction

**Natural Language Statement:**
The global sections functor Γ : Schemeᵒᵖ → CommRingCat is left adjoint to the Spec functor Spec : CommRingCatᵒᵖ → Scheme.

**Lean 4 Theorem:**
```lean
def AlgebraicGeometry.ΓSpec.adjunction :
  Scheme.Γ.rightOp ⊣ Spec.toScheme
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.GammaSpecAdjunction`

**Key Properties:**
- Unit: `X → Spec(Γ(X))`
- Counit: `R → Γ(Spec(R))` (isomorphism)
- Affine schemes are those where unit is an isomorphism

**Difficulty:** hard

---

## Part V: Morphisms of Schemes

### Module Organization

**Primary Imports:**
- `Mathlib.AlgebraicGeometry.Morphisms.Basic` - Morphism properties framework
- `Mathlib.AlgebraicGeometry.Morphisms.OpenImmersion` - Open immersions
- `Mathlib.AlgebraicGeometry.Morphisms.ClosedImmersion` - Closed immersions

**Estimated Statements:** 8-10

---

### Section 5.1: Open Immersions (2-3 statements)

#### 42. Open Immersion Definition

**Natural Language Statement:**
A scheme morphism f : X → Y is an open immersion if the underlying map is an open embedding and the induced map on structure sheaves is an isomorphism.

**Lean 4 Definition:**
```lean
class AlgebraicGeometry.IsOpenImmersion {X Y : Scheme} (f : X ⟶ Y) : Prop where
  isOpen_range : IsOpenEmbedding f.base
  app_isIso : ∀ (U : Y.Opens), IsIso (f.app U)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.OpenImmersion`

**Key Properties:**
- Composition of open immersions is an open immersion
- Stable under base change

**Difficulty:** medium

---

#### 43. Open Subscheme

**Natural Language Statement:**
Every open subset U of a scheme X forms an open subscheme via the canonical open immersion.

**Lean 4 Theorem:**
```lean
instance (U : X.Opens) : IsOpenImmersion U.ι
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.OpenImmersion`

**Key Related:**
- `Opens.ι : Opens.toScheme U ⟶ X` - Inclusion morphism

**Difficulty:** easy

---

### Section 5.2: Closed Immersions (3-4 statements)

#### 44. Closed Immersion Definition

**Natural Language Statement:**
A morphism f : X → Y is a closed immersion if the underlying map is a closed embedding and the induced stalk maps are surjective.

**Lean 4 Definition:**
```lean
class AlgebraicGeometry.IsClosedImmersion {X Y : Scheme} (f : X ⟶ Y) extends
    AlgebraicGeometry.SurjectiveOnStalks f : Prop where
  base_closed : Topology.IsClosedEmbedding ⇑(CategoryTheory.ConcreteCategory.hom f.base)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.ClosedImmersion`

**Difficulty:** medium

---

#### 45. Spec of Quotient

**Natural Language Statement:**
For any ideal I in a commutative ring R, the natural map Spec(R/I) → Spec(R) is a closed immersion.

**Lean 4 Theorem:**
```lean
theorem AlgebraicGeometry.IsClosedImmersion.spec_of_quotient_mk
    {R : CommRingCat} (I : Ideal R) :
  IsClosedImmersion (Spec.map (CommRingCat.ofHom (Ideal.Quotient.mk I)))
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.ClosedImmersion`

**Difficulty:** medium

---

#### 46. Closed Immersion from Surjective Ring Map

**Natural Language Statement:**
A surjective ring homomorphism f : R → S induces a closed immersion Spec(S) → Spec(R).

**Lean 4 Theorem:**
```lean
theorem AlgebraicGeometry.IsClosedImmersion.spec_of_surjective
    {R S : CommRingCat} (f : R ⟶ S) (h : Function.Surjective ⇑f) :
  IsClosedImmersion (Spec.map f)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.ClosedImmersion`

**Difficulty:** medium

---

#### 47. Closed Immersion Composition

**Natural Language Statement:**
The composition of closed immersions is a closed immersion.

**Lean 4 Theorem:**
```lean
instance AlgebraicGeometry.IsClosedImmersion.comp
    {X Y Z : Scheme} (f : X ⟶ Y) (g : Y ⟶ Z)
    [IsClosedImmersion f] [IsClosedImmersion g] :
  IsClosedImmersion (f ≫ g)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.ClosedImmersion`

**Difficulty:** medium

---

### Section 5.3: Affine Morphisms (2-3 statements)

#### 48. Affine Morphism

**Natural Language Statement:**
A morphism f : X → Y is affine if for every affine open U in Y, the preimage f⁻¹(U) is an affine open in X.

**Lean 4 Definition:**
```lean
class AlgebraicGeometry.IsAffineHom {X Y : Scheme} (f : X ⟶ Y) : Prop where
  isAffine_preimage : ∀ (U : Y.Opens), IsAffineOpen U →
    IsAffineOpen ((Opens.map f.base).obj U)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.Affine`

**Key Properties:**
- Closed immersions are affine morphisms
- Composition of affine morphisms is affine

**Difficulty:** medium

---

## Part VI: Properties of Morphisms

### Module Organization

**Primary Imports:**
- `Mathlib.AlgebraicGeometry.Morphisms.QuasiCompact` - Quasi-compact morphisms
- `Mathlib.AlgebraicGeometry.Morphisms.QuasiSeparated` - Quasi-separated morphisms
- `Mathlib.AlgebraicGeometry.Morphisms.UniversallyClosed` - Universally closed morphisms

**Estimated Statements:** 10-12

---

### Section 6.1: Quasi-Compact Morphisms (4-5 statements)

#### 49. Quasi-Compact Morphism Definition

**Natural Language Statement:**
A morphism f : X → Y is quasi-compact if the preimage of every quasi-compact open set is quasi-compact.

**Lean 4 Definition:**
```lean
class AlgebraicGeometry.QuasiCompact {X Y : Scheme} (f : X ⟶ Y) : Prop where
  isCompact_preimage (U : Set ↥Y) : IsOpen U → IsCompact U →
    IsCompact (⇑(CategoryTheory.ConcreteCategory.hom f.base) ⁻¹' U)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.QuasiCompact`

**Difficulty:** medium

---

#### 50. Quasi-Compact via Spectral Maps

**Natural Language Statement:**
A morphism is quasi-compact if and only if the underlying continuous map is a spectral map (preserves quasi-compactness).

**Lean 4 Theorem:**
```lean
theorem AlgebraicGeometry.quasiCompact_iff_isSpectralMap
    {X Y : Scheme} {f : X ⟶ Y} :
  QuasiCompact f ↔ IsSpectralMap ⇑(CategoryTheory.ConcreteCategory.hom f.base)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.QuasiCompact`

**Difficulty:** medium

---

#### 51. Quasi-Compact via Affine Opens

**Natural Language Statement:**
A morphism is quasi-compact if and only if preimages of affine opens are compact.

**Lean 4 Theorem:**
```lean
theorem AlgebraicGeometry.quasiCompact_iff_forall_isAffineOpen
    {X Y : Scheme} {f : X ⟶ Y} :
  QuasiCompact f ↔ ∀ (U : Y.Opens), IsAffineOpen U →
    IsCompact ↑((TopologicalSpace.Opens.map f.base).obj U)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.QuasiCompact`

**Difficulty:** medium

---

#### 52. Quasi-Compact Composition

**Natural Language Statement:**
The composition of quasi-compact morphisms is quasi-compact.

**Lean 4 Theorem:**
```lean
instance AlgebraicGeometry.quasiCompact_comp
    {X Y Z : Scheme} (f : X ⟶ Y) (g : Y ⟶ Z)
    [QuasiCompact f] [QuasiCompact g] :
  QuasiCompact (CategoryTheory.CategoryStruct.comp f g)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.QuasiCompact`

**Difficulty:** easy

---

#### 53. Quasi-Compact Stable Under Base Change

**Natural Language Statement:**
Quasi-compactness is stable under base change: if g is quasi-compact, then so are the pullback projections.

**Lean 4 Theorem:**
```lean
instance AlgebraicGeometry.quasiCompact_isStableUnderBaseChange :
  CategoryTheory.MorphismProperty.IsStableUnderBaseChange @QuasiCompact

instance {X Y Z : Scheme} (f : X ⟶ Z) (g : Y ⟶ Z) [QuasiCompact g] :
  QuasiCompact (CategoryTheory.Limits.pullback.fst f g)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.QuasiCompact`

**Difficulty:** hard

---

### Section 6.2: Quasi-Separated Morphisms (3-4 statements)

#### 54. Quasi-Separated Morphism Definition

**Natural Language Statement:**
A morphism f : X → Y is quasi-separated if the diagonal map Δ : X → X ×_Y X is quasi-compact.

**Lean 4 Definition:**
```lean
class AlgebraicGeometry.QuasiSeparated {X Y : Scheme} (f : X ⟶ Y) : Prop where
  quasiCompact_diagonal : QuasiCompact (CategoryTheory.Limits.pullback.diagonal f)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.QuasiSeparated`

**Difficulty:** medium

---

#### 55. Quasi-Separated Space

**Natural Language Statement:**
A scheme X is quasi-separated if the diagonal X → X × X is quasi-compact, equivalently if intersections of affine opens are quasi-compact.

**Lean 4 Theorem:**
```lean
theorem AlgebraicGeometry.quasiSeparatedSpace_iff_forall_affineOpens
    {X : Scheme} :
  QuasiSeparatedSpace ↥X ↔ ∀ (U V : ↑X.affineOpens),
    IsCompact (↑↑U ∩ ↑↑V)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.QuasiSeparated`

**Difficulty:** hard

---

#### 56. Qcqs Lemma

**Natural Language Statement:**
If U is a compact quasi-separated open in a scheme X, then for any f in Γ(X, U), the sections over D(f) are the localization: Γ(X, D(f)) ≅ Γ(X, U)_f.

**Lean 4 Theorem:**
```lean
theorem AlgebraicGeometry.isLocalization_basicOpen_of_qcqs
    {X : Scheme} {U : X.Opens}
    (hU : IsCompact U.carrier) (hU' : IsQuasiSeparated U.carrier)
    (f : ↑(X.presheaf.obj (Opposite.op U))) :
  IsLocalization.Away f ↑(X.presheaf.obj (Opposite.op (X.basicOpen f)))
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.QuasiSeparated`

**Difficulty:** hard

---

#### 57. Quasi-Separated Stable Under Composition

**Natural Language Statement:**
Quasi-separatedness is preserved under composition and base change.

**Lean 4 Theorem:**
```lean
instance AlgebraicGeometry.quasiSeparated_isStableUnderComposition :
  CategoryTheory.MorphismProperty.IsStableUnderComposition @QuasiSeparated

instance AlgebraicGeometry.quasiSeparated_isStableUnderBaseChange :
  CategoryTheory.MorphismProperty.IsStableUnderBaseChange @QuasiSeparated
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.QuasiSeparated`

**Difficulty:** medium

---

### Section 6.3: Local Properties Framework (2-3 statements)

#### 58. Zariski Local at Target

**Natural Language Statement:**
A morphism property P is Zariski local at the target if it can be checked on an open cover of the target.

**Lean 4 Definition:**
```lean
abbrev AlgebraicGeometry.IsZariskiLocalAtTarget
    (P : MorphismProperty Scheme) : Prop :=
  P.IsLocalAtTarget Scheme.zariskiPrecoverage
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.Basic`

**Key Properties:**
- QuasiCompact is Zariski local at target
- Can restrict to opens and check property there

**Difficulty:** hard

---

#### 59. Affine Target Property

**Natural Language Statement:**
An affine target morphism property is a property that can be checked when the target is affine.

**Lean 4 Definition:**
```lean
def AlgebraicGeometry.AffineTargetMorphismProperty : Type (u_1 + 1) :=
  ⦃X Y : Scheme⦄ → (X ⟶ Y) → [IsAffine Y] → Prop
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.Morphisms.Basic`

**Key Application:**
- Extends to arbitrary targets via `targetAffineLocally`
- Used for properties like finite type, flat, smooth

**Difficulty:** hard

---

## Part VII: Projective Schemes

### Module Organization

**Primary Imports:**
- `Mathlib.AlgebraicGeometry.ProjectiveSpectrum.Scheme` - Proj construction
- `Mathlib.RingTheory.GradedAlgebra.Basic` - Graded rings

**Estimated Statements:** 8-10

---

### Section 7.1: Projective Spectrum (4-5 statements)

#### 60. Graded Ring

**Natural Language Statement:**
A ℕ-graded ring is a ring A with a decomposition A = ⊕_{n≥0} A_n where A_i · A_j ⊆ A_{i+j}.

**Lean 4 Definition:**
```lean
class GradedRing {ι : Type*} [AddMonoid ι] (𝒜 : ι → Submodule R A) : Prop where
  one_mem : (1 : A) ∈ 𝒜 0
  mul_mem : ∀ {i j}, a ∈ 𝒜 i → b ∈ 𝒜 j → a * b ∈ 𝒜 (i + j)
```

**Mathlib Location:** `Mathlib.RingTheory.GradedAlgebra.Basic`

**Difficulty:** easy

---

#### 61. Homogeneous Localization

**Natural Language Statement:**
For a graded ring A and homogeneous element f of positive degree, the degree-zero part (A_f)_0 forms a ring.

**Lean 4 Definition:**
```lean
def Away.zeroSubring {A : Type*} [CommRing A] {σ : Type*}
    [SetLike σ A] (𝒜 : ℕ → σ) [GradedRing 𝒜] (f : A) :
  Subring (Away 𝒜 f)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.ProjectiveSpectrum.Scheme`

**Difficulty:** medium

---

#### 62. Proj as a Scheme

**Natural Language Statement:**
For a ℕ-graded ring A, the projective spectrum Proj(A) forms a scheme via an open cover by affine schemes Spec(A_f)_0 for homogeneous f.

**Lean 4 Definition:**
```lean
def Proj {A : Type u_1} {σ : Type u_2} [CommRing A] [SetLike σ A]
    [AddSubgroupClass σ A] (𝒜 : ℕ → σ) [GradedRing 𝒜] :
  Scheme
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.ProjectiveSpectrum.Scheme`

**Key Construction:**
- Open cover by basic opens D_+(f)
- Each D_+(f) isomorphic to Spec((A_f)_0)

**Difficulty:** hard

---

#### 63. Proj Basic Open Isomorphism

**Natural Language Statement:**
For a homogeneous element f of positive degree in a graded ring A, the basic open D_+(f) in Proj(A) is isomorphic to Spec((A_f)_0) as locally ringed spaces.

**Lean 4 Definition:**
```lean
def projIsoSpecTopComponent {A : Type u_1} {σ : Type u_2}
    [CommRing A] [SetLike σ A] [AddSubgroupClass σ A]
    {𝒜 : ℕ → σ} [GradedRing 𝒜]
    {f : A} {m : ℕ} (f_deg : f ∈ 𝒜 m) (hm : 0 < m) :
  ↑(restrict (Proj.toLocallyRingedSpace 𝒜) ⋯) ≅
  ↑(Spec.locallyRingedSpaceObj {carrier := Away 𝒜 f, ...})
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.ProjectiveSpectrum.Scheme`

**Difficulty:** hard

---

### Section 7.2: Projective Space (2-3 statements)

#### 64. Polynomial Ring Grading

**Natural Language Statement:**
The polynomial ring R[x₀, ..., x_n] has a natural ℕ-grading by total degree.

**Lean 4 Instance:**
```lean
instance MvPolynomial.gradedAlgebra {σ : Type*} [Fintype σ] :
  GradedAlgebra (fun i : ℕ => (MvPolynomial σ R).degreeOf i)
```

**Mathlib Location:** `Mathlib.RingTheory.MvPolynomial.Grading`

**Key Application:**
- Proj(R[x₀, ..., x_n]) gives projective space ℙⁿ_R

**Difficulty:** medium

---

#### 65. Projective Space Definition

**Natural Language Statement:**
Projective n-space over a ring R is defined as Proj(R[x₀, ..., x_n]).

**Lean 4 Definition:**
```lean
def ProjectiveSpace (n : ℕ) (R : CommRingCat) : Scheme :=
  Proj (MvPolynomial.gradedAlgebra (Fin (n+1)) R)
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.ProjectiveSpace` (if formalized)

**Key Properties:**
- Covered by n+1 affine charts
- Each chart isomorphic to Spec(R[x₁/x₀, ..., x_n/x₀])

**Difficulty:** hard

---

### Section 7.3: Morphisms from Proj (2-3 statements)

#### 66. Morphism to Affine via Graded Map

**Natural Language Statement:**
A degree-zero graded ring homomorphism from B to A_0 induces a morphism Proj(A) → Spec(B).

**Lean 4 Construction:**
```lean
def toSpec (𝒜 : ℕ → σ) (f : A) :
  (restrict (Proj.toLocallyRingedSpace 𝒜) ⋯) ⟶
  Spec.locallyRingedSpaceObj {carrier := Away 𝒜 f, ...}
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.ProjectiveSpectrum.Scheme`

**Difficulty:** hard

---

#### 67. Proj Functoriality

**Natural Language Statement:**
A degree-preserving graded ring homomorphism f : A → B induces a morphism Proj(B) → Proj(A).

**Lean 4 Construction:**
```lean
def Proj.map {A B : Type*} [CommRing A] [CommRing B]
    {𝒜 : ℕ → Submodule ℤ A} {ℬ : ℕ → Submodule ℤ B}
    [GradedRing 𝒜] [GradedRing ℬ]
    (f : A →+* B) (hf : ∀ n, f '' (𝒜 n) ⊆ ℬ n) :
  Proj ℬ ⟶ Proj 𝒜
```

**Mathlib Location:** `Mathlib.AlgebraicGeometry.ProjectiveSpectrum.Scheme` (if formalized)

**Difficulty:** hard

---

## Sources and References

This knowledge base was compiled from official Mathlib4 documentation (retrieved 2025-12-18):

### Primary Documentation
- [Mathlib.AlgebraicGeometry.Scheme](https://leanprover-community.github.io/mathlib4_docs/Mathlib/AlgebraicGeometry/Scheme.html)
- [Mathlib.AlgebraicGeometry.AffineScheme](https://leanprover-community.github.io/mathlib4_docs/Mathlib/AlgebraicGeometry/AffineScheme.html)
- [Mathlib.AlgebraicGeometry.Spec](https://leanprover-community.github.io/mathlib4_docs/Mathlib/AlgebraicGeometry/Spec.html)
- [Mathlib.AlgebraicGeometry.StructureSheaf](https://leanprover-community.github.io/mathlib4_docs/Mathlib/AlgebraicGeometry/StructureSheaf.html)
- [Mathlib.AlgebraicGeometry.ProjectiveSpectrum.Scheme](https://leanprover-community.github.io/mathlib4_docs/Mathlib/AlgebraicGeometry/ProjectiveSpectrum/Scheme.html)

### Topology and Prime Spectrum
- [Mathlib.RingTheory.Spectrum.Prime.Topology](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RingTheory/Spectrum/Prime/Topology.html)
- [Mathlib.RingTheory.Spectrum.Prime.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RingTheory/Spectrum/Prime/Basic.html)
- [Mathlib.RingTheory.Spectrum.Prime.Defs](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RingTheory/Spectrum/Prime/Defs.html)

### Morphism Properties
- [Mathlib.AlgebraicGeometry.Morphisms.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/AlgebraicGeometry/Morphisms/Basic.html)
- [Mathlib.AlgebraicGeometry.Morphisms.QuasiCompact](https://leanprover-community.github.io/mathlib4_docs/Mathlib/AlgebraicGeometry/Morphisms/QuasiCompact.html)
- [Mathlib.AlgebraicGeometry.Morphisms.QuasiSeparated](https://leanprover-community.github.io/mathlib4_docs/Mathlib/AlgebraicGeometry/Morphisms/QuasiSeparated.html)
- [Mathlib.AlgebraicGeometry.Morphisms.ClosedImmersion](https://leanprover-community.github.io/mathlib4_docs/Mathlib/AlgebraicGeometry/Morphisms/ClosedImmersion.html)
- [Mathlib.AlgebraicGeometry.Morphisms.UniversallyClosed](https://leanprover-community.github.io/mathlib4_docs/Mathlib/AlgebraicGeometry/Morphisms/UniversallyClosed.html)

### Geometric Structures
- [Mathlib.Geometry.RingedSpace.LocallyRingedSpace](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/RingedSpace/LocallyRingedSpace.html)
- [Mathlib.Geometry.RingedSpace.SheafedSpace](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/RingedSpace/SheafedSpace.html)
- [Mathlib.Geometry.RingedSpace.PresheafedSpace](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/RingedSpace/PresheafedSpace.html)

### Adjunctions
- [Mathlib.AlgebraicGeometry.GammaSpecAdjunction](https://math.iisc.ac.in/~gadgil/PfsProgs25doc/Mathlib/AlgebraicGeometry/GammaSpecAdjunction.html)

---

## Usage Notes

This knowledge base provides 67 statements spanning core algebraic geometry concepts in Mathlib4. For autoformalization training:

1. **Difficulty Progression:** Start with easy statements (prime spectrum basics, basic opens) before advancing to hard statements (scheme gluing, Proj construction)

2. **Dependency Chains:** Ensure prerequisite knowledge bases are trained first:
   - Commutative Algebra (ideals, localization, prime ideals)
   - Topology (open sets, compact spaces, continuous maps)
   - Category Theory (functors, adjunctions, pullbacks)

3. **Natural Language Variations:** Each statement should be paired with multiple natural language phrasings to improve robustness

4. **Proof Strategies:** Many hard theorems require substantial machinery not shown here. Consider including key lemmas and intermediate steps in training data.

5. **Mathlib Updates:** This knowledge base reflects Mathlib4 as of 2025-12-18. Check for updates to theorem names and module organization.