# K-Theory Knowledge Base

## Overview
K-theory is a branch of mathematics that studies vector bundles and projective modules through the construction of abelian groups (K-groups). This knowledge base covers both topological K-theory (classifying vector bundles) and algebraic K-theory (studying projective modules over rings). Mathlib4 provides foundations through vector bundle theory, fiber bundles, and free module theory, though K-groups themselves are not yet formalized.

**Mathlib4 Coverage**: Limited - Vector bundle foundations, fiber bundles, free modules; K-groups (K₀, K₁, K₂), Grothendieck groups, and Bott periodicity not yet formalized.

**Primary Coverage**: MSC 19 (K-theory)

---

## Related Knowledge Bases

### Prerequisites
- **Fiber Bundles** (`fiber_bundles_knowledge_base.md`): Vector bundles, trivializations
- **Linear Algebra** (`linear_algebra_knowledge_base.md`): Projective modules, free modules
- **Algebraic Topology** (`algebraic_topology_knowledge_base.md`): Homotopy theory

### Builds Upon This KB
- (Advanced K-theory applications)

### Related Topics
- **Category Theory** (`category_theory_knowledge_base.md`): Grothendieck groups, functors
- **Homological Algebra** (`homological_algebra_knowledge_base.md`): Projective resolutions
- **Operator Algebras** (`operator_algebras_knowledge_base.md`): C*-algebra K-theory

### Scope Clarification
This KB focuses on **K-theory foundations**:
- Vector bundle definitions and constructions
- Coordinate changes and transition functions
- Free modules over rings
- Whitney sum and tensor product operations
- (Gaps: K₀, K₁, K₂ groups, Grothendieck construction, Bott periodicity)

For **vector bundle theory**, see **Fiber Bundles KB**.

---

## Part I: Vector Bundles (10 statements)

### 1. Vector Bundle Definition
**NL**: A vector bundle over a topological space B with fiber F is a continuous family of vector spaces parameterized by B, locally trivializable as products B × F with linear coordinate changes.

**Lean 4**:
```lean
class VectorBundle (R : Type*) {B : Type*} (F : Type*) (E : B → Type*)
    [NontriviallyNormedField R] [∀ x, AddCommMonoid (E x)] [∀ x, Module R (E x)]
    [NormedAddCommGroup F] [NormedSpace R F] [TopologicalSpace B]
    [TopologicalSpace (Bundle.TotalSpace F E)] [∀ x, TopologicalSpace (E x)]
    [FiberBundle F E] : Prop where
  trivialization_linear' : ∀ e ∈ trivializationAtlas F E, e.IsLinear R
```

### 2. Vector Bundle Core Construction
**NL**: A vector bundle can be constructed from coordinate change data: an indexing set, base spaces for each index, and transition functions between overlapping trivializations.

**Lean 4**:
```lean
structure VectorBundleCore (R : Type*) (B : Type*) (F : Type*) (ι : Type*)
    [NontriviallyNormedField R] [NormedAddCommGroup F] [NormedSpace R F]
    [TopologicalSpace B] extends FiberBundleCore ι B F where
  coordChange_linear : ∀ i j b, b ∈ baseSet i ∩ baseSet j →
    coordChange i j b ∈ ContinuousLinearMap.range (ContinuousLinearMap.id R F)
```

### 3. Coordinate Change as Linear Equivalence
**NL**: The coordinate change between two trivializations of a vector bundle at a point b is a continuous linear equivalence F ≃L[R] F.

**Lean 4**:
```lean
def Trivialization.coordChangeL (R : Type*) [NontriviallyNormedField R]
    {B : Type*} {F : Type*} [NormedAddCommGroup F] [NormedSpace R F]
    {E : B → Type*} [∀ x, AddCommMonoid (E x)] [∀ x, Module R (E x)]
    [TopologicalSpace B] [TopologicalSpace (Bundle.TotalSpace F E)]
    (e e' : Trivialization F (π F E)) [e.IsLinear R] [e'.IsLinear R] (b : B) :
    F ≃L[R] F
```

### 4. Continuous Coordinate Changes
**NL**: The coordinate change functions in a vector bundle vary continuously with the base point.

**Lean 4**:
```lean
theorem VectorBundle.continuousOn_coordChange [NontriviallyNormedField R]
    [NormedAddCommGroup F] [NormedSpace R F] [TopologicalSpace B]
    [VectorBundle R F E] (e e' : Trivialization F (π F E))
    [e.IsLinear R] [e'.IsLinear R] :
    ContinuousOn (fun b => e.coordChangeL R e' b) (e.baseSet ∩ e'.baseSet)
```

### 5. Linear Trivialization at a Point
**NL**: At each point b in the base space, a vector bundle admits a local trivialization that is linear on fibers.

**Lean 4**:
```lean
theorem VectorBundle.trivialization_at_isLinear [NontriviallyNormedField R]
    [NormedAddCommGroup F] [NormedSpace R F] [TopologicalSpace B]
    [VectorBundle R F E] (b : B) :
    (trivializationAt F E b).IsLinear R
```

### 6. Fiberwise Linear Map Construction
**NL**: A trivialization induces a fiberwise linear map from fibers to the model fiber F, which is a linear equivalence over the trivialization's base set.

**Lean 4**:
```lean
def Trivialization.continuousLinearEquivAt (R : Type*) [NontriviallyNormedField R]
    {B : Type*} {F : Type*} [NormedAddCommGroup F] [NormedSpace R F]
    {E : B → Type*} [∀ x, AddCommMonoid (E x)] [∀ x, Module R (E x)]
    [∀ x, TopologicalSpace (E x)] [TopologicalSpace B]
    (e : Trivialization F (π F E)) [e.IsLinear R] {b : B} (hb : b ∈ e.baseSet) :
    E b ≃L[R] F
```

### 7. Total Space Topology
**NL**: The total space of a vector bundle carries a topology making the projection continuous and ensuring local triviality.

**Lean 4**:
```lean
theorem VectorBundle.continuous_proj (R : Type*) [NontriviallyNormedField R]
    (B : Type*) (F : Type*) [NormedAddCommGroup F] [NormedSpace R F]
    (E : B → Type*) [TopologicalSpace B] [TopologicalSpace (Bundle.TotalSpace F E)]
    [VectorBundle R F E] :
    Continuous (Bundle.TotalSpace.proj : Bundle.TotalSpace F E → B)
```

### 8. Coordinate Change Composition
**NL**: Coordinate changes in a vector bundle satisfy the cocycle condition: the composition of coordinate changes (i→j) and (j→k) equals the coordinate change (i→k).

**Lean 4**:
```lean
theorem VectorBundleCore.coordChange_comp (Z : VectorBundleCore R B F ι)
    {i j k : ι} {b : B} (hi : b ∈ Z.baseSet i) (hj : b ∈ Z.baseSet j)
    (hk : b ∈ Z.baseSet k) :
    Z.coordChange j k b ∘L Z.coordChange i j b = Z.coordChange i k b
```

### 9. Trivial Vector Bundle
**NL**: The product bundle B × F with the identity transition functions is a vector bundle (the trivial bundle).

**Lean 4**:
```lean
instance Bundle.Trivial.vectorBundle (R B F : Type*) [NontriviallyNormedField R]
    [TopologicalSpace B] [NormedAddCommGroup F] [NormedSpace R F] :
    VectorBundle R F (Bundle.Trivial B F)
```

### 10. Vector Bundle Morphism in Coordinates
**NL**: A morphism between vector bundles can be represented in local coordinates as a continuous family of linear maps between the model fibers.

**Lean 4**:
```lean
def ContinuousLinearMap.inCoordinates (R : Type*) [NontriviallyNormedField R]
    {B : Type*} {B' : Type*} {F : Type*} {F' : Type*}
    [NormedAddCommGroup F] [NormedSpace R F] [NormedAddCommGroup F'] [NormedSpace R F']
    {E : B → Type*} {E' : B' → Type*} [TopologicalSpace B] [TopologicalSpace B']
    (e : Trivialization F (π F E)) (e' : Trivialization F' (π F' E'))
    [e.IsLinear R] [e'.IsLinear R] (f : ∀ b, E b →L[R] E' (σ b)) (b : B) :
    F →L[R] F'
```

---

## Part II: Free Modules (10 statements)

### 11. Free Module Definition
**NL**: An R-module M is free if it admits a basis, i.e., there exists an indexing type I and a basis indexed by I.

**Lean 4**:
```lean
class Module.Free (R : Type u) (M : Type v) [Semiring R] [AddCommMonoid M]
    [Module R M] : Prop where
  exists_basis : Nonempty ((I : Type v) × Basis I R M)
```

### 12. Basis Implies Free
**NL**: If a module admits a basis indexed by any type, then it is a free module.

**Lean 4**:
```lean
theorem Module.Free.of_basis {R : Type*} {M : Type*} [Semiring R]
    [AddCommMonoid M] [Module R M] {ι : Type*} (b : Basis ι R M) :
    Module.Free R M
```

### 13. Free Module Has Basis
**NL**: Every free module admits a canonical choice of basis (noncomputably selected).

**Lean 4**:
```lean
noncomputable def Module.Free.chooseBasis (R : Type*) (M : Type*)
    [Semiring R] [AddCommMonoid M] [Module R M] [Module.Free R M] :
    Basis (Module.Free.ChooseBasisIndex R M) R M
```

### 14. Set-Indexed Basis Characterization
**NL**: A module is free if and only if it has a basis indexed by a subset of the module itself.

**Lean 4**:
```lean
theorem Module.free_iff_set (R : Type*) (M : Type*) [Semiring R]
    [AddCommMonoid M] [Module R M] :
    Module.Free R M ↔ ∃ (S : Set M), Nonempty (Basis (↑S) R M)
```

### 15. Universal Property of Free Modules
**NL**: Linear maps from a free module M to any module N correspond bijectively to functions from the basis of M to N.

**Lean 4**:
```lean
noncomputable def Module.Free.constr (R : Type*) (M : Type*) (N : Type*)
    [Semiring R] [AddCommMonoid M] [Module R M] [Module.Free R M]
    [AddCommMonoid N] [Module R N] {S : Type*} [Semiring S] [Module S N]
    [SMulCommClass R S N] :
    (Module.Free.ChooseBasisIndex R M → N) ≃ₗ[S] M →ₗ[R] N
```

### 16. Free Module Preserved by Equivalence
**NL**: If M is a free R-module and M ≃ₗ[R] N is a linear equivalence, then N is also free.

**Lean 4**:
```lean
theorem Module.Free.of_equiv {R : Type*} {M : Type*} {N : Type*}
    [Semiring R] [AddCommMonoid M] [Module R M] [Module.Free R M]
    [AddCommMonoid N] [Module R N] (e : M ≃ₗ[R] N) :
    Module.Free R N
```

### 17. Free Modules over Domains Have No Zero Divisors
**NL**: A free module over a domain has no zero-divisor scalar multiplication: if r·m = 0 with r ≠ 0, then m = 0.

**Lean 4**:
```lean
instance Module.Free.noZeroSMulDivisors (R : Type*) (M : Type*)
    [Semiring R] [AddCommMonoid M] [Module R M] [Module.Free R M]
    [NoZeroDivisors R] :
    NoZeroSMulDivisors R M
```

### 18. Free Module over Infinite Ring
**NL**: A nontrivial free module over an infinite ring is itself infinite.

**Lean 4**:
```lean
theorem Module.Free.infinite (R : Type*) (M : Type*) [Semiring R]
    [AddCommMonoid M] [Module R M] [Module.Free R M] [Infinite R]
    [Nontrivial M] :
    Infinite M
```

### 19. Submodule Generated by Set
**NL**: The submodule generated by a set S consists of all finite linear combinations of elements from S.

**Lean 4**:
```lean
theorem Submodule.mem_span {R : Type*} {M : Type*} [Semiring R]
    [AddCommMonoid M] [Module R M] {s : Set M} {x : M} :
    x ∈ Submodule.span R s ↔ ∀ p : Submodule R M, s ⊆ p → x ∈ p
```

### 20. Ring as Free Module over Itself
**NL**: Any ring R is a free module over itself with basis {1}.

**Lean 4**:
```lean
instance Module.Free.self (R : Type*) [Semiring R] : Module.Free R R :=
  ⟨⟨Unit, ⟨Basis.singleton Unit R⟩⟩⟩
```

---

## Part III: Fiber Bundles (8 statements)

### 21. Fiber Bundle Definition
**NL**: A fiber bundle over base B with fiber F is a topological space E with a continuous projection π: E → B such that each fiber π⁻¹(b) is homeomorphic to F, with local triviality.

**Lean 4**:
```lean
class FiberBundle {B : Type*} (F : Type*) [TopologicalSpace B]
    [TopologicalSpace F] (E : B → Type*)
    [TopologicalSpace (Bundle.TotalSpace F E)]
    [∀ b, TopologicalSpace (E b)] : Prop where
  totalSpaceMk_inducing' : ∀ b, Inducing (Bundle.TotalSpace.mk b : E b → Bundle.TotalSpace F E)
  trivializationAtlas' : Set (Trivialization F (Bundle.TotalSpace.proj : Bundle.TotalSpace F E → B))
  trivializationAt' : B → Trivialization F Bundle.TotalSpace.proj
  mem_trivializationAt' : ∀ b, b ∈ (trivializationAt' b).baseSet
  trivialization_mem_atlas' : ∀ b, trivializationAt' b ∈ trivializationAtlas'
```

### 22. Projection is Continuous
**NL**: The projection map from the total space of a fiber bundle to the base space is continuous.

**Lean 4**:
```lean
theorem FiberBundle.continuous_proj (B : Type*) (F : Type*) (E : B → Type*)
    [TopologicalSpace B] [TopologicalSpace F]
    [TopologicalSpace (Bundle.TotalSpace F E)] [∀ b, TopologicalSpace (E b)]
    [FiberBundle F E] :
    Continuous (Bundle.TotalSpace.proj : Bundle.TotalSpace F E → B)
```

### 23. Projection is Open Map
**NL**: The projection map from a fiber bundle is an open map.

**Lean 4**:
```lean
theorem FiberBundle.isOpenMap_proj (B : Type*) (F : Type*) (E : B → Type*)
    [TopologicalSpace B] [TopologicalSpace F]
    [TopologicalSpace (Bundle.TotalSpace F E)] [∀ b, TopologicalSpace (E b)]
    [FiberBundle F E] :
    IsOpenMap (Bundle.TotalSpace.proj : Bundle.TotalSpace F E → B)
```

### 24. Projection is Surjective
**NL**: If the fiber F is nonempty, the projection of a fiber bundle is surjective.

**Lean 4**:
```lean
theorem FiberBundle.surjective_proj (B : Type*) (F : Type*) (E : B → Type*)
    [TopologicalSpace B] [TopologicalSpace F]
    [TopologicalSpace (Bundle.TotalSpace F E)] [∀ b, TopologicalSpace (E b)]
    [FiberBundle F E] [Nonempty F] :
    Function.Surjective (Bundle.TotalSpace.proj : Bundle.TotalSpace F E → B)
```

### 25. Fiber Bundle Core Construction
**NL**: A fiber bundle can be constructed from an indexing set, base sets covering B, and coordinate change homeomorphisms satisfying the cocycle condition.

**Lean 4**:
```lean
structure FiberBundleCore (ι : Type*) (B : Type*) (F : Type*)
    [TopologicalSpace B] [TopologicalSpace F] where
  baseSet : ι → Set B
  isOpen_baseSet : ∀ i, IsOpen (baseSet i)
  indexAt : B → ι
  mem_baseSet_at : ∀ b, b ∈ baseSet (indexAt b)
  coordChange : ι → ι → B → F → F
  coordChange_self : ∀ i, ∀ᵐ b ∂· ∈ baseSet i, ∀ x, coordChange i i b x = x
  continuousOn_coordChange : ∀ i j, ContinuousOn (fun p => coordChange i j p.1 p.2)
    ((baseSet i ∩ baseSet j) ×ˢ Set.univ)
  coordChange_comp : ∀ i j k, ∀ᵐ b ∂· ∈ baseSet i ∩ baseSet j ∩ baseSet k,
    ∀ x, coordChange j k b (coordChange i j b x) = coordChange i k b x
```

### 26. Local Trivialization Existence
**NL**: At each point of the base space, a fiber bundle admits a local trivialization defined on a neighborhood.

**Lean 4**:
```lean
def FiberBundle.trivializationAt (F : Type*) (E : B → Type*)
    [TopologicalSpace B] [TopologicalSpace F]
    [TopologicalSpace (Bundle.TotalSpace F E)] [∀ b, TopologicalSpace (E b)]
    [FiberBundle F E] (b : B) :
    Trivialization F (Bundle.TotalSpace.proj : Bundle.TotalSpace F E → B)
```

### 27. Continuity via Local Trivialization
**NL**: A function into the total space of a fiber bundle is continuous at a point iff its composition with projection is continuous and its trivialized form is continuous.

**Lean 4**:
```lean
theorem FiberBundle.continuousAt_totalSpace (F : Type*) {X : Type*}
    [TopologicalSpace X] {B : Type*} [TopologicalSpace B] [TopologicalSpace F]
    {E : B → Type*} [TopologicalSpace (Bundle.TotalSpace F E)]
    [∀ b, TopologicalSpace (E b)] [FiberBundle F E]
    (f : X → Bundle.TotalSpace F E) {x₀ : X} :
    ContinuousAt f x₀ ↔
      ContinuousAt (fun x => (f x).proj) x₀ ∧
      ContinuousAt (fun x => (trivializationAt F E (f x₀).proj (f x)).2) x₀
```

### 28. Fiber Bundle from Core
**NL**: A FiberBundleCore canonically induces a fiber bundle structure on its associated total space.

**Lean 4**:
```lean
instance FiberBundleCore.fiberBundle (ι : Type*) (B : Type*) (F : Type*)
    [TopologicalSpace B] [TopologicalSpace F] (Z : FiberBundleCore ι B F) :
    FiberBundle F Z.Fiber
```

---

## Part IV: Module Categories (8 statements)

### 29. Module Category Definition
**NL**: The category ModuleCat R has R-modules as objects and R-linear maps as morphisms.

**Lean 4**:
```lean
structure ModuleCat (R : Type u) [Ring R] : Type (max u (v + 1)) where
  carrier : Type v
  [isAddCommGroup : AddCommGroup carrier]
  [isModule : Module R carrier]
```

### 30. Module Category Object Construction
**NL**: Any type with an R-module structure can be viewed as an object in the module category.

**Lean 4**:
```lean
abbrev ModuleCat.of (R : Type u) [Ring R] (X : Type v)
    [AddCommGroup X] [Module R X] : ModuleCat.{v} R :=
  ⟨X⟩
```

### 31. Morphisms are Linear Maps
**NL**: Morphisms in the module category are exactly the R-linear maps between the underlying modules.

**Lean 4**:
```lean
instance ModuleCat.instLinearMapClass (R : Type*) [Ring R] (M N : ModuleCat R) :
    LinearMapClass (M ⟶ N) R M N
```

### 32. Module Category is Preadditive
**NL**: The module category is preadditive: the hom-sets are abelian groups and composition is bilinear.

**Lean 4**:
```lean
instance ModuleCat.instPreadditive (R : Type u) [Ring R] :
    CategoryTheory.Preadditive (ModuleCat.{v} R)
```

### 33. Linear Equivalence vs Isomorphism
**NL**: Linear equivalences between R-modules correspond bijectively to isomorphisms in the module category.

**Lean 4**:
```lean
def linearEquivIsoModuleIso (R : Type*) [Ring R] {X Y : Type*}
    [AddCommGroup X] [AddCommGroup Y] [Module R X] [Module R Y] :
    (X ≃ₗ[R] Y) ≅ (ModuleCat.of R X ≅ ModuleCat.of R Y)
```

### 34. Endomorphism Ring
**NL**: The endomorphisms of an object in the module category form a ring isomorphic to the ring of linear endomorphisms.

**Lean 4**:
```lean
def ModuleCat.endRingEquiv (R : Type*) [Ring R] (M : ModuleCat R) :
    End M ≃+* (↑M →ₗ[R] ↑M)
```

### 35. Forgetful Functor to AddCommGroup
**NL**: There is a forgetful functor from the category of R-modules to the category of abelian groups that forgets the R-action.

**Lean 4**:
```lean
instance ModuleCat.hasForget₂ToAddCommGroup (R : Type*) [Ring R] :
    HasForget₂ (ModuleCat R) AddCommGrp
```

### 36. Scalar Multiplication as Natural Transformation
**NL**: For each element r ∈ R, scalar multiplication by r defines a natural transformation from the forgetful functor to itself.

**Lean 4**:
```lean
def ModuleCat.smulNatTrans (R : Type u) [Ring R] :
    R →+* End (forget₂ (ModuleCat R) AddCommGrp)
```

---

## Part V: Exact Sequences (7 statements)

### 37. Exact Sequence Definition
**NL**: A sequence of maps M →f N →g P is exact at N if the image of f equals the kernel of g: im(f) = ker(g).

**Lean 4**:
```lean
def Function.Exact {M N P : Type*} [Zero P] (f : M → N) (g : N → P) : Prop :=
  ∀ y, g y = 0 ↔ y ∈ Set.range f
```

### 38. Exactness for Linear Maps
**NL**: For linear maps, exactness is equivalent to the kernel of g equaling the range of f as submodules.

**Lean 4**:
```lean
theorem LinearMap.exact_iff {R : Type*} [Ring R] {M N P : Type*}
    [AddCommGroup M] [AddCommGroup N] [AddCommGroup P]
    [Module R M] [Module R N] [Module R P]
    (f : M →ₗ[R] N) (g : N →ₗ[R] P) :
    Function.Exact f g ↔ LinearMap.ker g = LinearMap.range f
```

### 39. Submodule and Quotient Exactness
**NL**: For any submodule Q of M, the sequence Q ↪ M → M/Q is exact.

**Lean 4**:
```lean
theorem LinearMap.exact_subtype_mkQ {R : Type*} [Ring R] {M : Type*}
    [AddCommGroup M] [Module R M] (Q : Submodule R M) :
    Function.Exact (Submodule.subtype Q) (Submodule.mkQ Q)
```

### 40. Range and Quotient Exactness
**NL**: For any linear map f: M → N, the sequence M →f N → N/range(f) is exact.

**Lean 4**:
```lean
theorem LinearMap.exact_map_mkQ_range {R : Type*} [Ring R] {M N : Type*}
    [AddCommGroup M] [AddCommGroup N] [Module R M] [Module R N]
    (f : M →ₗ[R] N) :
    Function.Exact f (LinearMap.range f).mkQ
```

### 41. Splitting Lemma (Conditions Equivalent)
**NL**: For an exact sequence with injective f and surjective g, the following are equivalent: (1) g has a section, (2) f has a retraction, (3) N ≅ M × P.

**Lean 4**:
```lean
theorem Function.Exact.split_tfae' {R : Type*} [Ring R] {M N P : Type*}
    [AddCommGroup M] [AddCommGroup N] [AddCommGroup P]
    [Module R M] [Module R N] [Module R P]
    (f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : Function.Exact f g) :
    [Function.Injective f ∧ ∃ l : P →ₗ[R] N, g ∘ₗ l = LinearMap.id,
     Function.Surjective g ∧ ∃ l : N →ₗ[R] M, l ∘ₗ f = LinearMap.id,
     ∃ e : N ≃ₗ[R] M × P, f = e.symm ∘ₗ LinearMap.inl R M P ∧
       g = LinearMap.snd R M P ∘ₗ e].TFAE
```

### 42. Split Exact Sequence Equivalence
**NL**: If an exact sequence splits (g has a section), then N is linearly equivalent to the direct sum M ⊕ P.

**Lean 4**:
```lean
def Function.Exact.linearEquivOfSurjective {R : Type*} [Ring R] {M N P : Type*}
    [AddCommGroup M] [AddCommGroup N] [AddCommGroup P]
    [Module R M] [Module R N] [Module R P]
    (f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : Function.Exact f g)
    (hg : Function.Surjective g) :
    (N ⧸ LinearMap.range f) ≃ₗ[R] P
```

### 43. Exactness Preserved by Equivalence
**NL**: If M →f N →g P is exact and we have equivalences M ≃ M', N ≃ N', P ≃ P', then the conjugated sequence is also exact.

**Lean 4**:
```lean
theorem LinearEquiv.conj_exact_iff_exact {R : Type*} [Ring R]
    {M N P M' N' P' : Type*}
    [AddCommGroup M] [AddCommGroup N] [AddCommGroup P]
    [AddCommGroup M'] [AddCommGroup N'] [AddCommGroup P']
    [Module R M] [Module R N] [Module R P]
    [Module R M'] [Module R N'] [Module R P']
    (eM : M ≃ₗ[R] M') (eN : N ≃ₗ[R] N') (eP : P ≃ₗ[R] P')
    (f : M →ₗ[R] N) (g : N →ₗ[R] P) :
    Function.Exact (eN ∘ₗ f ∘ₗ eM.symm) (eP ∘ₗ g ∘ₗ eN.symm) ↔
      Function.Exact f g
```

---

## Part VI: Projective Spaces and Modules (7 statements)

### 44. Projectivization Definition
**NL**: The projectivization of a vector space V is the set of lines through the origin, i.e., equivalence classes of nonzero vectors under scalar multiplication.

**Lean 4**:
```lean
def Projectivization (K : Type*) (V : Type*) [DivisionRing K] [AddCommGroup V]
    [Module K V] : Type* :=
  { v : V // v ≠ 0 } ⧸ (MulAction.orbitRel Kˣ { v : V // v ≠ 0 })
```

### 45. Projective Points from Nonzero Vectors
**NL**: Every nonzero vector determines a point in projective space; two vectors give the same point iff they differ by a nonzero scalar.

**Lean 4**:
```lean
theorem Projectivization.mk_eq_mk_iff {K V : Type*} [DivisionRing K]
    [AddCommGroup V] [Module K V] {v w : V} (hv : v ≠ 0) (hw : w ≠ 0) :
    Projectivization.mk K v hv = Projectivization.mk K w hw ↔
      ∃ (a : Kˣ), a • w = v
```

### 46. Submodule of a Projective Point
**NL**: Each point of projective space corresponds to a rank-1 submodule (a line through the origin).

**Lean 4**:
```lean
theorem Projectivization.finrank_submodule {K V : Type*} [DivisionRing K]
    [AddCommGroup V] [Module K V] [FiniteDimensional K V]
    (p : Projectivization K V) :
    FiniteDimensional.finrank K (Projectivization.submodule p) = 1
```

### 47. Submodule Map is Injective
**NL**: The map from projective space to rank-1 submodules is injective: distinct projective points have distinct associated lines.

**Lean 4**:
```lean
theorem Projectivization.submodule_injective {K V : Type*} [DivisionRing K]
    [AddCommGroup V] [Module K V] :
    Function.Injective (Projectivization.submodule : Projectivization K V → Submodule K V)
```

### 48. Representative of Projective Point
**NL**: Each projective point has a (noncomputably chosen) nonzero representative vector.

**Lean 4**:
```lean
theorem Projectivization.rep_nonzero {K V : Type*} [DivisionRing K]
    [AddCommGroup V] [Module K V] (p : Projectivization K V) :
    Projectivization.rep p ≠ 0
```

### 49. Induced Map on Projective Space
**NL**: An injective semilinear map between vector spaces induces a well-defined map between their projectivizations.

**Lean 4**:
```lean
def Projectivization.map {K K' V V' : Type*} [DivisionRing K] [DivisionRing K']
    [AddCommGroup V] [Module K V] [AddCommGroup V'] [Module K' V']
    {σ : K →+* K'} (f : V →ₛₗ[σ] V') (hf : Function.Injective f) :
    Projectivization K V → Projectivization K' V'
```

### 50. Projectivization Respects Composition
**NL**: The projectivization functor respects composition: (g ∘ f)* = g* ∘ f* for injective linear maps.

**Lean 4**:
```lean
theorem Projectivization.map_comp {K K' K'' V V' V'' : Type*}
    [DivisionRing K] [DivisionRing K'] [DivisionRing K'']
    [AddCommGroup V] [Module K V] [AddCommGroup V'] [Module K' V']
    [AddCommGroup V''] [Module K'' V'']
    {σ : K →+* K'} {τ : K' →+* K''} {ρ : K →+* K''}
    [RingHomCompTriple σ τ ρ]
    (f : V →ₛₗ[σ] V') (g : V' →ₛₗ[τ] V'')
    (hf : Function.Injective f) (hg : Function.Injective g) :
    Projectivization.map (g ∘ₛₗ f) (hg.comp hf) =
      Projectivization.map g hg ∘ Projectivization.map f hf
```

---

## Part VII: K-Theory Concepts (Not Yet Formalized) (5 statements)

### 51. Grothendieck Group (Conceptual)
**NL**: The Grothendieck group K₀(R) of a ring R is the abelian group generated by isomorphism classes [P] of finitely generated projective R-modules, with relation [P ⊕ Q] = [P] + [Q].

**Lean 4 (Sketch)**:
```lean
-- Not yet in Mathlib; conceptual formalization
def GrothendieckGroup (R : Type*) [Ring R] : Type* :=
  sorry -- Quotient of formal differences [P] - [Q]
  -- with [P ⊕ M] - [Q ⊕ M] = [P] - [Q]
```

### 52. K₀ of a Field (Conceptual)
**NL**: For a field k, K₀(k) ≅ ℤ, generated by the class of the 1-dimensional vector space.

**Lean 4 (Sketch)**:
```lean
-- Not yet in Mathlib
theorem K0_of_field (k : Type*) [Field k] :
    GrothendieckGroup k ≃+ ℤ :=
  sorry -- [V] ↦ dim V
```

### 53. Topological K-Theory K⁰(X) (Conceptual)
**NL**: For a compact Hausdorff space X, K⁰(X) is the Grothendieck group of isomorphism classes of complex vector bundles over X.

**Lean 4 (Sketch)**:
```lean
-- Not yet in Mathlib
def TopologicalKTheory (X : Type*) [TopologicalSpace X] [CompactSpace X]
    [T2Space X] : Type* :=
  sorry -- Grothendieck group of VectorBundle ℂ X
```

### 54. Bott Periodicity (Conceptual)
**NL**: Bott periodicity states that K⁰(X × S²) ≅ K⁰(X) ⊕ K⁰(X), or equivalently, the K-theory spectrum is 2-periodic.

**Lean 4 (Sketch)**:
```lean
-- Not yet in Mathlib
theorem BottPeriodicity (X : Type*) [TopologicalSpace X] [CompactSpace X]
    [T2Space X] :
    TopologicalKTheory (X × sphere 2) ≃+ TopologicalKTheory X × TopologicalKTheory X :=
  sorry
```

### 55. K₁ of a Ring (Conceptual)
**NL**: K₁(R) is defined as the abelianization of the infinite general linear group GL(R) = colim GL_n(R), which measures "stable" invertible matrices.

**Lean 4 (Sketch)**:
```lean
-- Not yet in Mathlib
def K1 (R : Type*) [Ring R] : Type* :=
  sorry -- Abelianization of colim GL_n(R)
  -- K₁(R) = GL(R)^ab
```

---

## Summary

This knowledge base covers 55 statements on K-theory foundations:
- **Part I**: Vector Bundles (10 statements) - Core topological K-theory infrastructure
- **Part II**: Free Modules (10 statements) - Algebraic K-theory foundations
- **Part III**: Fiber Bundles (8 statements) - Topological bundle theory
- **Part IV**: Module Categories (8 statements) - Categorical framework
- **Part V**: Exact Sequences (7 statements) - Tools for K-group computations
- **Part VI**: Projective Spaces and Modules (7 statements) - Geometric perspective
- **Part VII**: K-Theory Concepts (5 statements) - Not yet formalized

**Formalization Status**: Mathlib4 provides strong foundations (vector bundles, fiber bundles, free modules, exact sequences) but K-groups themselves (K₀, K₁, K₂), Grothendieck groups, and Bott periodicity remain unformalized.

**Key Dependencies**: Topology (bundle theory), Algebra (module theory, rings), CategoryTheory (module categories)
