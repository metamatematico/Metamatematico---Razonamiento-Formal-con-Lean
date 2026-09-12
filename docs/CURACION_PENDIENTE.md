# Curación pendiente

> Generado por `scripts/hoja_de_curacion.py`. **No editar a mano**: se regenera.


De 203 enunciados reales de Mathlib tomados al azar, **62 nombran algo que la cabecera fija no alcanza**. De esos, en **43 el grafo no tiene ningún nodo** que lo cubra — el 69 %. Ningún recorrido recupera lo que no está.

Son **41 módulos distintos**, repartidos así:

| rama | módulos |
|---|---|
| Computability | 5 |
| RingTheory | 4 |
| Topology | 4 |
| Control | 4 |
| SetTheory | 4 |
| Algebra | 3 |
| NumberTheory | 3 |
| AlgebraicTopology | 2 |
| Analysis | 2 |
| Data | 2 |
| Dynamics | 2 |
| Geometry | 2 |
| AlgebraicGeometry | 1 |
| LinearAlgebra | 1 |
| ModelTheory | 1 |
| Order | 1 |

---

## Qué hay que decidir en cada uno

**1 · La marca.** Es lo que sostiene el grafo y no lo decide nada automático:

| | | |
|---|---|---|
| `C` | una categoría | **vértice** |
| `S` | una subcategoría plena | **vértice**, y la inclusión es arista |
| `F` | un funtor o clase de flechas | **arista**, no vértice |
| `O` | un objeto individual | vértice degenerado |
| `T` | ni objetos ni flechas | **fuera** |

`homology` es `F`: no es una colección que se pueda colimitar, es el funtor *a lo largo del cual* se colimita. `prime-factorization` es `T`: es un teorema, no un objeto.

**2 · El padre.** De qué concepto es especialización. La flecha va del general al específico.

**3 · Cuál de los nombres.** Que exista no lo hace correcto: `Nat.Prime` es la noción de primo, `Nat.minFac` no.

Lo que **no** hay que decidir, porque ya está verificado: si el nombre existe, en qué módulo vive, cuál es el canónico (las citas) y el DAG de imports.

---

## Computability  ·  área `computation`

Padres candidatos ya en el grafo: `algorithm-analysis`, `computability-theory`, `computational-complexity`, `formal-verification`, `lambda-calculus`, `np-completeness`, `recursion-theory`, `turing-machines`

### `Computability.AkraBazzi.SumTransform`

| identificador | tipo | citas |
|---|---|---|
| `AkraBazziRecurrence.asympBound` | def | 10 |
| `AkraBazziRecurrence.min_bi` | def | 4 |
| `AkraBazziRecurrence.sumTransform` | def | 4 |
| `AkraBazziRecurrence.max_bi` | def | 1 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Computability.DFA`

| identificador | tipo | citas |
|---|---|---|
| `DFA.comap` | def | 1132 |
| `DFA.eval` | def | 829 |
| `Language.IsRegular` | def | 216 |
| `DFA.reindex` | def | 79 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Computability.Language`

| identificador | tipo | citas |
|---|---|---|
| `Language.reverse` | def | 164 |
| `Language` | def | 122 |
| `Symbol` | inductive | 21 |
| `Language.map` | def | 1 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Computability.Partrec`

| identificador | tipo | citas |
|---|---|---|
| `Computable` | def | 85 |
| `Nat.Partrec` | inductive | 39 |
| `Partrec` | def | 39 |
| `Nat.rfind` | def | 7 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Computability.Primrec.Basic`

| identificador | tipo | citas |
|---|---|---|
| `Nat.Primrec` | inductive | 181 |
| `Primrec` | def | 181 |
| `Primcodable.subtype` | def | 135 |
| `Primcodable` | class | 70 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## RingTheory  ·  área `algebra`

Padres candidatos ya en el grafo: `abelian-groups`, `bases-and-dimension`, `bilinear-forms`, `canonical-forms`, `character-theory`, `commutative-algebra`, `derived-category`, `eigen-theory`, `exact-sequences`, `field-extensions`, `field-theory`, `finite-fields`, `free-groups`, `galois-theory`

### `RingTheory.DedekindDomain.Different`

| identificador | tipo | citas |
|---|---|---|
| `FractionalIdeal.dual` | def | 110 |
| `differentIdeal` | def | 31 |
| `Submodule.traceDual` | def | 2 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `RingTheory.Derivation.Basic`

| identificador | tipo | citas |
|---|---|---|
| `Derivation.restrictScalars` | def | 216 |
| `Derivation` | structure | 53 |
| `Derivation.coeFnAddMonoidHom` | def | 13 |
| `Derivation.llcomp` | def | 4 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `RingTheory.GradedAlgebra.Homogeneous.Ideal`

| identificador | tipo | citas |
|---|---|---|
| `HomogeneousIdeal` | abbrev | 42 |
| `Ideal.IsHomogeneous` | abbrev | 6 |
| `Ideal.homogeneousHull` | def | 5 |
| `HomogeneousIdeal.irrelevant` | def | 3 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `RingTheory.GradedAlgebra.HomogeneousLocalization`

| identificador | tipo | citas |
|---|---|---|
| `HomogeneousLocalization.NumDenSameDeg.embedding` | def | 53 |
| `HomogeneousLocalization` | def | 43 |
| `HomogeneousLocalization.NumDenSameDeg` | structure | 36 |
| `HomogeneousLocalization.awayMap` | def | 21 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## Topology  ·  área `topology`

Padres candidatos ya en el grafo: `algebraic-topology`, `compactness`, `connectedness`, `covering-spaces`, `differential-topology`, `fundamental-group`, `geometric-topology`, `homotopy-theory`, `point-set-topology`, `separation-axioms`, `sheafed-space-complexes`

### `Topology.Category.TopCat.Basic`

| identificador | tipo | citas |
|---|---|---|
| `TopCat.ofHom` | abbrev | 231 |
| `TopCat` | structure | 214 |
| `TopCat.trivial` | def | 49 |
| `TopCat.Hom.hom` | abbrev | 42 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Topology.MetricSpace.Congruence`

| identificador | tipo | citas |
|---|---|---|
| `Congruent` | def | 7 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Topology.MetricSpace.Holder`

| identificador | tipo | citas |
|---|---|---|
| `HolderOnWith` | def | 40 |
| `HolderWith` | def | 38 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Topology.MetricSpace.Similarity`

| identificador | tipo | citas |
|---|---|---|
| `Similar` | def | 10 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## Control  ·  **sin área en el grafo**

> Mathlib no organiza esta rama como un área del grafo. Puede que estos conceptos sean `T`.

### `Control.Bitraversable.Basic`

| identificador | tipo | citas |
|---|---|---|
| `Bitraversable` | class | 2 |
| `LawfulBitraversable` | class | 2 |
| `bisequence` | def | 0 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Control.Fix`

| identificador | tipo | citas |
|---|---|---|
| `Fix` | class | 17 |
| `Part.fix` | def | 9 |
| `Part.Fix.approx` | def | 3 |
| `Part.fixAux` | def | 0 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Control.Functor.Multivariate`

| identificador | tipo | citas |
|---|---|---|
| `MvFunctor.supp` | def | 33 |
| `MvFunctor.ofEquiv` | def | 11 |
| `MvFunctor` | class | 9 |
| `MvFunctor.LiftP` | def | 7 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Control.Monad.Cont`

| identificador | tipo | citas |
|---|---|---|
| `Cont` | abbrev | 7 |
| `ContT` | def | 5 |
| `ContT.monadLift` | def | 5 |
| `OptionT.mkLabel` | def | 2 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## SetTheory  ·  área `set-theory`

Padres candidatos ya en el grafo: `cardinal-arithmetic`, `descriptive-set-theory`, `forcing`, `large-cardinals`

### `SetTheory.Lists`

| identificador | tipo | citas |
|---|---|---|
| `Lists'.cons` | def | 358 |
| `Lists'.toList` | def | 130 |
| `Lists.toList` | def | 130 |
| `Lists'.ofList` | def | 55 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `SetTheory.Ordinal.Notation`

| identificador | tipo | citas |
|---|---|---|
| `ONote.ofNat` | def | 409 |
| `NONote.ofNat` | def | 409 |
| `ONote.repr` | def | 159 |
| `NONote.repr` | def | 159 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `SetTheory.ZFC.Basic`

| identificador | tipo | citas |
|---|---|---|
| `ZFSet.Nonempty` | def | 2513 |
| `ZFSet.range` | def | 2184 |
| `ZFSet.prod` | def | 1046 |
| `ZFSet.image` | def | 415 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `SetTheory.ZFC.Class`

| identificador | tipo | citas |
|---|---|---|
| `Class.univ` | def | 1539 |
| `Class.powerset` | def | 47 |
| `Class` | def | 38 |
| `Class.ofSet` | def | 21 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## Algebra  ·  área `algebra`

Padres candidatos ya en el grafo: `abelian-groups`, `bases-and-dimension`, `bilinear-forms`, `canonical-forms`, `character-theory`, `commutative-algebra`, `derived-category`, `eigen-theory`, `exact-sequences`, `field-extensions`, `field-theory`, `finite-fields`, `free-groups`, `galois-theory`

### `Algebra.Lie.Basic`

| identificador | tipo | citas |
|---|---|---|
| `LieEquiv.symm` | def | 2247 |
| `LieModuleEquiv.symm` | def | 2247 |
| `LieHom.comp` | def | 1617 |
| `LieModuleHom.comp` | def | 1617 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Algebra.Module.CharacterModule`

| identificador | tipo | citas |
|---|---|---|
| `CharacterModule.uncurry` | def | 165 |
| `CharacterModule.dual` | def | 110 |
| `CharacterModule.congr` | def | 103 |
| `CharacterModule.homEquiv` | def | 72 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Algebra.Module.Injective`

| identificador | tipo | citas |
|---|---|---|
| `Module.Injective` | class | 16 |
| `Module.Baer` | def | 16 |
| `Module.Baer.ExtensionOf` | structure | 7 |
| `Module.Baer.extensionOfMax` | def | 6 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## NumberTheory  ·  área `number-theory`

Padres candidatos ya en el grafo: `algebraic-number-theory`, `analytic-number-theory`, `arithmetic-geometry`, `diophantine-equations`, `divisibility-gcd`, `elementary-number-theory`, `ideal-class-group`, `modular-arithmetic`, `number-fields`, `p-adic-valuations`, `prime-factorization`, `prime-number-theorem`, `quadratic-residues`, `riemann-zeta`

### `NumberTheory.ModularForms.Basic`

| identificador | tipo | citas |
|---|---|---|
| `ModularForm.prod` | def | 1046 |
| `ModularForm.const` | def | 322 |
| `ModularForm` | structure | 47 |
| `ModularFormClass` | class | 38 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `NumberTheory.ModularForms.SlashInvariantForms`

| identificador | tipo | citas |
|---|---|---|
| `SlashInvariantForm.prod` | def | 1046 |
| `SlashInvariantForm.const` | def | 322 |
| `SlashInvariantForm` | structure | 27 |
| `SlashInvariantForm.coeHom` | def | 11 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `NumberTheory.NumberField.InfinitePlace.Basic`

| identificador | tipo | citas |
|---|---|---|
| `NumberField.InfinitePlace` | def | 181 |
| `NumberField.InfinitePlace.IsReal` | def | 59 |
| `NumberField.InfinitePlace.embedding` | def | 53 |
| `NumberField.InfinitePlace.IsComplex` | def | 50 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## AlgebraicTopology  ·  área `topology`

Padres candidatos ya en el grafo: `algebraic-topology`, `compactness`, `connectedness`, `covering-spaces`, `differential-topology`, `fundamental-group`, `geometric-topology`, `homotopy-theory`, `point-set-topology`, `separation-axioms`, `sheafed-space-complexes`

### `AlgebraicTopology.SimplexCategory.Defs`

| identificador | tipo | citas |
|---|---|---|
| `SimplexCategory.Hom.comp` | def | 1617 |
| `SimplexCategory.Truncated.inclusion` | abbrev | 169 |
| `SimplexCategory` | def | 124 |
| `SimplexCategory.Truncated.incl` | def | 19 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `AlgebraicTopology.SimplexCategory.GeneratorsRelations.Basic`

| identificador | tipo | citas |
|---|---|---|
| `FreeSimplexQuiver.homRel` | inductive | 19 |
| `SimplexCategoryGenRel` | def | 13 |
| `SimplexCategoryGenRel.generators` | abbrev | 4 |
| `FreeSimplexQuiver` | def | 1 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## Analysis  ·  área `analysis`

Padres candidatos ya en el grafo: `banach-spaces`, `complex-analysis`, `conformal-maps`, `contour-integration`, `differentiation`, `functional-analysis`, `harmonic-analysis`, `hilbert-spaces`, `holomorphic-functions`, `lebesgue-integration`, `limits-continuity`, `measure-theory`, `metric-spaces`, `operator-theory`

### `Analysis.Complex.Circle`

| identificador | tipo | citas |
|---|---|---|
| `Circle` | def | 58 |
| `Circle.coeHom` | def | 11 |
| `Circle.toUnits` | def | 10 |
| `Circle.exp` | def | 9 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Analysis.Complex.UpperHalfPlane.Basic`

| identificador | tipo | citas |
|---|---|---|
| `UpperHalfPlane` | structure | 10 |
| `UpperHalfPlane.im` | def | 1 |
| `UpperHalfPlane.I` | def | 0 |
| `UpperHalfPlane.re` | def | 0 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## Data  ·  **sin área en el grafo**

> Mathlib no organiza esta rama como un área del grafo. Puede que estos conceptos sean `T`.

### `Data.PFun`

| identificador | tipo | citas |
|---|---|---|
| `PFun.comp` | def | 1617 |
| `PFun.restrict` | def | 702 |
| `PFun.lift` | def | 618 |
| `PFun.image` | def | 415 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Data.TypeVec`

| identificador | tipo | citas |
|---|---|---|
| `TypeVec.comp` | def | 1617 |
| `TypeVec.prod` | def | 1046 |
| `TypeVec.const` | def | 322 |
| `TypeVec.last` | def | 155 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## Dynamics  ·  área `probability`

Padres candidatos ya en el grafo: `brownian-motion`, `conditional-expectation`, `ergodic-theory`, `limit-theorems`, `markov-chains`, `martingale-theory`, `probability-theory`, `random-variables`, `stochastic-processes`

### `Dynamics.Circle.RotationNumber.TranslationNumber`

| identificador | tipo | citas |
|---|---|---|
| `CircleDeg1Lift` | structure | 33 |
| `CircleDeg1Lift.translate` | def | 9 |
| `CircleDeg1Lift.toOrderIso` | def | 4 |
| `CircleDeg1Lift.transnumAuxSeq` | def | 0 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Dynamics.Flow`

| identificador | tipo | citas |
|---|---|---|
| `Flow.restrict` | def | 702 |
| `Flow.reverse` | def | 164 |
| `Flow.orbit` | def | 63 |
| `IsInvariant` | def | 9 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## Geometry  ·  área `geometry`

Padres candidatos ya en el grafo: `affine-varieties`, `algebraic-geometry`, `circle-geometry`, `complex-geometry`, `differential-forms`, `differential-geometry`, `euclidean-geometry`, `projective-geometry`, `projective-varieties`, `riemannian-geometry`, `schemes`, `smooth-manifolds`, `symplectic-geometry`, `triangle-geometry`

### `Geometry.Manifold.Algebra.LeftInvariantDerivation`

| identificador | tipo | citas |
|---|---|---|
| `LeftInvariantDerivation.coeFnAddMonoidHom` | def | 13 |
| `LeftInvariantDerivation` | structure | 6 |
| `LeftInvariantDerivation.evalAt` | def | 6 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Geometry.Manifold.Algebra.LieGroup`

| identificador | tipo | citas |
|---|---|---|
| `LieGroup` | class | 6 |
| `LieAddGroup` | class | 2 |
| `ContMDiffInv₀` | class | 0 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## AlgebraicGeometry  ·  área `geometry`

Padres candidatos ya en el grafo: `affine-varieties`, `algebraic-geometry`, `circle-geometry`, `complex-geometry`, `differential-forms`, `differential-geometry`, `euclidean-geometry`, `projective-geometry`, `projective-varieties`, `riemannian-geometry`, `schemes`, `smooth-manifolds`, `symplectic-geometry`, `triangle-geometry`

### `AlgebraicGeometry.ProjectiveSpectrum.Topology`

| identificador | tipo | citas |
|---|---|---|
| `ProjectiveSpectrum.zeroLocus` | def | 139 |
| `ProjectiveSpectrum.basicOpen` | def | 91 |
| `ProjectiveSpectrum.vanishingIdeal` | def | 71 |
| `ProjectiveSpectrum` | structure | 46 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## LinearAlgebra  ·  área `algebra`

Padres candidatos ya en el grafo: `abelian-groups`, `bases-and-dimension`, `bilinear-forms`, `canonical-forms`, `character-theory`, `commutative-algebra`, `derived-category`, `eigen-theory`, `exact-sequences`, `field-extensions`, `field-theory`, `finite-fields`, `free-groups`, `galois-theory`

### `LinearAlgebra.AffineSpace.FiniteDimensional`

| identificador | tipo | citas |
|---|---|---|
| `Collinear` | def | 70 |
| `Coplanar` | def | 13 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## ModelTheory  ·  área `logic`

Padres candidatos ya en el grafo: `compactness-theorem`, `homotopy-type-theory`, `incompleteness`, `model-theory`, `proof-theory`, `sequent-calculus`, `ultraproducts`

### `ModelTheory.Arithmetic.Presburger.Semilinear.Defs`

| identificador | tipo | citas |
|---|---|---|
| `IsSemilinearSet` | def | 42 |
| `IsLinearSet` | def | 18 |
| `IsProperSemilinearSet` | def | 10 |
| `IsProperLinearSet` | def | 6 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## Order  ·  **sin área en el grafo**

> Mathlib no organiza esta rama como un área del grafo. Puede que estos conceptos sean `T`.

### `Order.PFilter`

| identificador | tipo | citas |
|---|---|---|
| `Order.PFilter.principal` | def | 16 |
| `Order.PFilter` | structure | 6 |
| `Order.IsPFilter` | def | 2 |
| `Order.IsPFilter.toPFilter` | def | 0 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

---

## Antes de dar por buena una tanda

```
python -m scripts.recuperacion_contra_proofnet
```

Precisión y cobertura contra 371 formalizaciones de oro, con su modelo nulo y sin gastar API.

**Baseline hoy: 21,3 % / 18,4 % contra 1,45 % / 3,3 % — 14,7×.** Si la precisión baja, esa tanda no entra.

Ya pasó: ofrecer los sustantivos de los nodos generados bajaba de 14,0 % a 11,5 %. Añadir vocabulario tiene coste.
