# Curación por cobertura

> Generado por `scripts/hoja_de_curacion.py`. **No editar a mano**: se regenera.


El banco de enunciados que fallan **está agotado**: los 41 módulos que destapó se curaron y los 10 que quedaban están decididos. Esta hoja sale de otro sitio — de mirar directamente qué partes de Mathlib no cubre el grafo.

Son **24 módulos en dos grupos**, y son dos apuestas distintas que conviene no mezclar.

**Grupo 1 · seguir la tanda** — 12 módulos. La curación anterior metió el primer nodo de varias ramas y se paró ahí. `Algebra.Lie` tiene **1 228 teoremas en 50 ficheros y el grafo toca uno**: un álgebra de Lie sin subálgebras, sin ideales y sin pesos. Son rincones —poco volumen— pero el barrio se mide limpio y son los conceptos que busca quien investiga.

**Grupo 2 · el núcleo** — 12 módulos. El mismo criterio sobre Mathlib entero da **161 ramas abiertas y finas**, y las mayores no son las de la tanda:

| rama | teoremas | módulos | cubiertos |
|---|---:|---:|---:|
| `Algebra.Order` | 5140 | 208 | 1 |
| `Algebra.Group` | 4102 | 148 | 4 |
| `Analysis.SpecialFunctions` | 3906 | 98 | 1 |
| `Analysis.Calculus` | 3607 | 122 | 2 |
| `Analysis.Normed` | 3485 | 151 | 3 |

Ahí es donde caen las consultas de un alumno, y explica el **5,0 % de precisión sobre Mathlib entero**: el grafo es fino en casi todas partes, no sólo en los rincones.

> **Una pregunta extra para el grupo 2.** Ahí el grafo ya tiene nodo de cabecera —`group-theory`, `ring-theory`, `real-analysis`— y lo que falta son los módulos finos de debajo. Puede que la respuesta correcta **no sea un nodo nuevo sino más nombres en el que ya hay**, que es una decisión distinta y más barata. Si es el caso, escríbelo en vez de la marca.

Y ahora hay con qué decidir, que es lo que faltó la vez anterior: `banco_docstrings.py` y `banco_herald.py` **sí ven** estos temas. Sobre la primera tanda, sus módulos pasaron de 3,9 % a 16,9 % y de 4,0 % a 20,6 % de precisión sin mover el global. **Una tanda entra si sube su barrio y no baja el global.**

Repartidos por rama:

| rama | módulos |
|---|---|
| Algebra | 7 |
| Computability | 4 |
| Data | 4 |
| Analysis | 3 |
| Dynamics | 2 |
| SetTheory | 2 |
| NumberTheory | 1 |
| Order | 1 |

---

## Qué hay que decidir en cada uno

**1 · La marca.** Es lo que sostiene el grafo y no lo decide nada automático:

| | | |
|---|---|---|
| `C` | una categoría | **vértice** |
| `S` | una subcategoría plena | **vértice**, y la inclusión es arista |
| `F` | un funtor o clase de flechas | **arista** *en este ambiente* |
| `O` | un objeto individual | vértice degenerado |
| `T` | ni objetos ni flechas | **fuera** |

`F` **no** dice «esto no puede ser un vértice nunca». Eso es falso, y está demostrado que lo es en `FlechasComoObjetos.lean`: las flechas de `C` son exactamente los objetos de `Arrow C`, y los funtores son los objetos de `C ⥤ D`. Lo que dice es que **en este grafo** —cuyos objetos son conceptos y cuyas flechas son dependencias— la etiqueta nombra una flecha.

`homology` es `F`: aquí no es una colección que se pueda colimitar, es el funtor *a lo largo del cual* se colimita. `prime-factorization` es `T`: es un teorema, no un objeto.

**2 · El padre.** De qué concepto es especialización. La flecha va del general al específico.

**3 · Cuál de los nombres.** Que exista no lo hace correcto: `Nat.Prime` es la noción de primo, `Nat.minFac` no.

Lo que **no** hay que decidir, porque ya está verificado: si el nombre existe, en qué módulo vive, cuál es el canónico (las citas) y el DAG de imports.

---

## Algebra  ·  área `algebra`

Padres candidatos ya en el grafo: `abelian-groups`, `bases-and-dimension`, `bilinear-forms`, `canonical-forms`, `character-modules`, `character-theory`, `commutative-algebra`, `derivations`, `derived-category`, `different-ideal`, `eigen-theory`, `exact-sequences`, `field-extensions`, `field-theory`

### `Algebra.Group.Basic`  ·  *grupo 2 · el núcleo*

Sin sustantivos propios: sólo aporta teoremas. El grafo aporta **sustantivos** —de sus 176 identificadores ninguno es un teorema—, así que probablemente no le toca.

### `Algebra.Group.Pointwise.Finset.Basic`  ·  *grupo 2 · el núcleo*

| identificador | tipo | citas |
|---|---|---|
| `Finset.coeMonoidHom` | def | 5 |
| `Finset.singletonMulHom` | def | 4 |
| `Finset.zpow` | def | 4 |
| `Finset.singletonMonoidHom` | def | 4 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Algebra.Lie.Nilpotent`  ·  *grupo 1 · seguir la tanda*

| identificador | tipo | citas |
|---|---|---|
| `LieModule.IsNilpotent` | class | 251 |
| `LieModule.lowerCentralSeries` | def | 57 |
| `LieRing.IsNilpotent` | abbrev | 10 |
| `LieAlgebra.maxNilpotentIdeal` | def | 5 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Algebra.Lie.Subalgebra`  ·  *grupo 1 · seguir la tanda*

| identificador | tipo | citas |
|---|---|---|
| `LieHom.range` | def | 2184 |
| `LieSubalgebra.comap` | def | 1132 |
| `LieSubalgebra.inclusion` | def | 169 |
| `LieSubalgebra` | structure | 77 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Algebra.Lie.Submodule`  ·  *grupo 1 · seguir la tanda*

| identificador | tipo | citas |
|---|---|---|
| `LieModuleHom.range` | def | 2184 |
| `LieSubmodule.comap` | def | 1132 |
| `LieSubmodule.inclusion` | def | 169 |
| `LieSubmodule` | structure | 107 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Algebra.Order.Monoid.Unbundled.Basic`  ·  *grupo 2 · el núcleo*

| identificador | tipo | citas |
|---|---|---|
| `MulLECancellable` | def | 20 |
| `Contravariant.toLeftCancelSemigroup` | def | 0 |
| `Contravariant.toRightCancelSemigroup` | def | 0 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Algebra.Order.ToIntervalMod`  ·  *grupo 2 · el núcleo*

| identificador | tipo | citas |
|---|---|---|
| `toIocMod` | def | 106 |
| `toIcoMod` | def | 99 |
| `toIcoDiv` | def | 66 |
| `toIocDiv` | def | 66 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## Computability  ·  área `computation`

Padres candidatos ya en el grafo: `algorithm-analysis`, `computability-theory`, `computational-complexity`, `finite-automata`, `formal-languages`, `formal-verification`, `lambda-calculus`, `np-completeness`, `partial-functions`, `partial-recursive-functions`, `primitive-recursive-functions`, `recursion-theory`, `turing-machines`

### `Computability.Primrec.List`  ·  *grupo 1 · seguir la tanda*

| identificador | tipo | citas |
|---|---|---|
| `Nat.Primrec'` | inductive | 23 |
| `Nat.Primrec'.Vec` | def | 0 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Computability.Reduce`  ·  *grupo 1 · seguir la tanda*

| identificador | tipo | citas |
|---|---|---|
| `toNat` | def | 93 |
| `ManyOneDegree.liftOn` | abbrev | 17 |
| `ManyOneEquiv` | def | 16 |
| `ManyOneDegree` | def | 12 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Computability.TMToPartrec`  ·  *grupo 1 · seguir la tanda*

| identificador | tipo | citas |
|---|---|---|
| `Turing.PartrecToTM2.head` | def | 153 |
| `Turing.PartrecToTM2.init` | def | 49 |
| `Turing.PartrecToTM2.Supports` | def | 22 |
| `Turing.PartrecToTM2.trNormal` | def | 17 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Computability.Tape`  ·  *grupo 1 · seguir la tanda*

| identificador | tipo | citas |
|---|---|---|
| `Turing.proj` | def | 183 |
| `Turing.ListBlank` | def | 45 |
| `Turing.Tape` | structure | 16 |
| `Turing.Tape.mk'` | def | 14 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## Data  ·  **sin área en el grafo**

> Mathlib no organiza esta rama como un área del grafo. Puede que estos conceptos sean `T`.

### `Data.Finset.Lattice.Fold`  ·  *grupo 2 · el núcleo*

| identificador | tipo | citas |
|---|---|---|
| `Finset.sup'` | def | 31 |
| `Finset.inf'` | def | 25 |
| `Finset.sup` | def | 7 |
| `Finset.inf` | def | 0 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Data.Set.Function`  ·  *grupo 2 · el núcleo*

| identificador | tipo | citas |
|---|---|---|
| `Function.invFunOn` | def | 17 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Data.Set.Image`  ·  *grupo 2 · el núcleo*

Sin sustantivos propios: sólo aporta teoremas. El grafo aporta **sustantivos** —de sus 176 identificadores ninguno es un teorema—, así que probablemente no le toca.

### `Data.Set.Lattice`  ·  *grupo 2 · el núcleo*

| identificador | tipo | citas |
|---|---|---|
| `Set.sigmaToiUnion` | def | 3 |
| `Set.unionEqSigmaOfDisjoint` | def | 2 |
| `Set.sigmaEquiv` | def | 1 |
| `Set.sUnionPowersetGI` | def | 0 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## Analysis  ·  área `analysis`

Padres candidatos ya en el grafo: `banach-spaces`, `complex-analysis`, `conformal-maps`, `contour-integration`, `differentiation`, `functional-analysis`, `harmonic-analysis`, `hilbert-spaces`, `holder-continuity`, `holomorphic-functions`, `lebesgue-integration`, `limits-continuity`, `measure-theory`, `metric-spaces`

### `Analysis.Normed.Group.Basic`  ·  *grupo 2 · el núcleo*

| identificador | tipo | citas |
|---|---|---|
| `normGroupSeminorm` | def | 1 |
| `normGroupNorm` | def | 1 |
| `SeminormedGroup.induced` | abbrev | 0 |
| `SeminormedCommGroup.induced` | abbrev | 0 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Analysis.SpecialFunctions.Pow.NNReal`  ·  *grupo 2 · el núcleo*

| identificador | tipo | citas |
|---|---|---|
| `NNReal.rpow` | def | 5 |
| `ENNReal.rpow` | def | 5 |
| `NNReal.orderIsoRpow` | def | 2 |
| `ENNReal.orderIsoRpow` | def | 2 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Analysis.SpecialFunctions.Pow.Real`  ·  *grupo 2 · el núcleo*

| identificador | tipo | citas |
|---|---|---|
| `Real.rpow` | def | 5 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## Dynamics  ·  área `probability`

Padres candidatos ya en el grafo: `brownian-motion`, `conditional-expectation`, `ergodic-theory`, `flows`, `limit-theorems`, `markov-chains`, `martingale-theory`, `probability-theory`, `random-variables`, `rotation-number`, `stochastic-processes`

### `Dynamics.PeriodicPts.Defs`  ·  *grupo 1 · seguir la tanda*

| identificador | tipo | citas |
|---|---|---|
| `Function.minimalPeriod` | def | 57 |
| `Function.IsPeriodicPt` | def | 49 |
| `Function.periodicPts` | def | 29 |
| `MulAction.period` | def | 23 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `Dynamics.TopologicalEntropy.CoverEntropy`  ·  *grupo 1 · seguir la tanda*

| identificador | tipo | citas |
|---|---|---|
| `Dynamics.coverMincard` | def | 22 |
| `Dynamics.coverEntropy` | def | 22 |
| `Dynamics.IsDynCoverOf` | def | 20 |
| `Dynamics.coverEntropyEntourage` | def | 18 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## SetTheory  ·  área `set-theory`

Padres candidatos ya en el grafo: `cardinal-arithmetic`, `descriptive-set-theory`, `forcing`, `hereditarily-finite-sets`, `large-cardinals`, `zfc-classes`, `zfc-sets`

### `SetTheory.ZFC.Ordinal`  ·  *grupo 1 · seguir la tanda*

| identificador | tipo | citas |
|---|---|---|
| `ZFSet.IsOrdinal` | structure | 9 |
| `ZFSet.IsTransitive` | def | 8 |
| `Ordinal.toZFSet` | def | 8 |
| `Ordinal.toPSet` | def | 0 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

### `SetTheory.ZFC.PSet`  ·  *grupo 1 · seguir la tanda*

| identificador | tipo | citas |
|---|---|---|
| `PSet.Nonempty` | def | 2513 |
| `PSet.insert` | def | 922 |
| `PSet.Equiv` | def | 518 |
| `PSet.image` | def | 415 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## NumberTheory  ·  área `number-theory`

Padres candidatos ya en el grafo: `algebraic-number-theory`, `analytic-number-theory`, `arithmetic-geometry`, `diophantine-equations`, `divisibility-gcd`, `elementary-number-theory`, `ideal-class-group`, `infinite-places`, `modular-arithmetic`, `modular-forms`, `number-fields`, `p-adic-valuations`, `prime-factorization`, `prime-number-theorem`

### `NumberTheory.ModularForms.QExpansion`  ·  *grupo 1 · seguir la tanda*

| identificador | tipo | citas |
|---|---|---|
| `SlashInvariantFormClass.cuspFunction` | def | 39 |
| `ModularFormClass.qExpansion` | def | 24 |
| `UpperHalfPlane.valueAtInfty` | def | 5 |
| `ModularFormClass.qExpansionFormalMultilinearSeries` | def | 4 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

## Order  ·  **sin área en el grafo**

> Mathlib no organiza esta rama como un área del grafo. Puede que estos conceptos sean `T`.

### `Order.Filter.Map`  ·  *grupo 2 · el núcleo*

| identificador | tipo | citas |
|---|---|---|
| `Filter.kernMap` | def | 6 |
| `Filter.monad` | def | 0 |

- [ ] marca: `C` / `S` / `F` / `O` / `T`
- [ ] padre:
- [ ] identificadores que se quedan:

---

## Antes de dar por buena una tanda

```
python -m scripts.recuperacion_contra_proofnet
```

Precisión y cobertura contra 371 formalizaciones de oro, con su modelo nulo y sin gastar API.

**Baseline hoy: 22,8 % / 18,0 % contra 1,45 % / 3,3 % — 15,7×.** Si la precisión baja, esa tanda no entra.

Y la regla tiene una letra pequeña que costó descubrir. La primera tanda de 31 nodos **bajaba la precisión a 19,9 %** sin mover la cobertura, y la causa no era ningún veredicto equivocado —los 47 nombres los acepta `#check`— sino que el emparejador tokeniza el **id y el nombre** de cada nodo: `different-ideal` aportaba el token `different`, que sale en media biblioteca, y con eso gastaba una de las dos plazas del prompt. La puerta que lo arregla —*sólo se ocupa plaza con una keyword declarada*— subió la línea base de 21,3 % a 22,8 %. Si una tanda baja la precisión, mira primero si sus nodos entran en plaza por su nombre.

Ya pasó: ofrecer los sustantivos de los nodos generados bajaba de 14,0 % a 11,5 %. Añadir vocabulario tiene coste.
