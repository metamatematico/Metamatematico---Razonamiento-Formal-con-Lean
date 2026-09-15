# Curación interna

> Generado por `scripts/hoja_de_curacion_interna.py`. **No editar a mano**: se regenera.


Las otras dos hojas miran hacia **afuera** — qué trozo de Mathlib no cubre el grafo. Ésta mira hacia **adentro**: de los 190 conceptos que ya están, cuáles no cumplen lo que su propia marca promete.

Son **48 decisiones**, y ninguna medición las había pedido nunca — porque ninguna medición mira ahí. Los bancos miden lo que el grafo **ofrece**; esto es lo que el grafo **promete**.

## El inventario completo, para que se vea qué parte es ésta

| montón | qué es | cuántos | dónde |
|---|---|---:|---|
| enunciados que fallan | los 62 que la cabecera fija no alcanzaba | **0** | agotado |
| cobertura de Mathlib | ramas que el grafo abrió y dejó finas | **24** | `CURACION_RAMAS.pdf` |
| **A · `lean=None` que puede haber caducado** | marca de vértice, cero nombres, y un «no existe» fechado en agosto | **10** | *aquí* |
| **B · vértices marcados fuera** | marca `T` y sin embargo son nodos | **36** | *aquí* |
| **C · marcados fuera y con voz** | marca `T` y además dan nombres | **2** | *aquí* |

Lo que **no** hay que curar, para acotar el trabajo: la cobertura de marca en la capa curada es del **100 %** (los 205 nodos del autor la tienen; los 147 sin marca son 125 módulos de Mathlib y 22 áreas, que no son suyos), las 15 tácticas y estrategias son `T` y está bien —una táctica no es un objeto—, `homology` y `cohomology` tienen veredicto `F` y no son nodo —correcto, son flechas— y **ningún concepto se ha quedado sin palabras clave**: ninguno es inalcanzable desde una consulta.

---

## Qué hay que decidir, y por qué no lo decide nadie más

Las marcas, otra vez, porque son lo que está en juego:

| | | |
|---|---|---|
| `C` | una categoría | **vértice** |
| `S` | una subcategoría plena | **vértice**, y la inclusión es arista |
| `F` | un funtor o clase de flechas | **arista** *en este ambiente* |
| `O` | un objeto individual | vértice degenerado |
| `T` | ni objetos ni flechas | **fuera** |

**En el montón A** no hay ninguna promesa rota: hay diez `lean=None`, que es una decisión escrita —*no existe en Mathlib*— fechada en agosto. La decisión es **si sigue siendo verdad**, y es la única de las tres que caduca sola: cada vez que Mathlib crece, un «no existe» se acerca un poco más a ser falso.

**En el montón B** la promesa rota es al revés: `T` dice *fuera* y el nodo está dentro, enrutando. Tres salidas, y conviene no confundirlas:

- **se retira** — si de verdad no pinta nada. La hoja dice cuántos hijos quedarían sueltos;
- **cambia de marca** — si el veredicto se equivocó. La hoja dice si hay un objeto esperando en Mathlib;
- **se queda, declarado enrutador** — un nodo sin voz que existe sólo para que las palabras clave lleguen a sus hijos. Es una decisión legítima, pero **hoy no está escrita en ningún sitio**, y ésa es justamente la diferencia.

> La tercera opción es la que más importa de las tres. Si es la correcta para la mayoría de los 36, entonces lo que falta no son 36 decisiones sino **una marca nueva** — algo como `R` de enrutador — y la hoja se cierra de golpe. Si no lo es, hay que ir uno por uno.

**En el montón C** la contradicción es exacta y no admite «se queda como está»: el veredicto dice que no son objetos y están alimentando plazas del prompt. Una de las dos mitades sobra.

### Qué valen los candidatos que trae cada ficha

Salen de un índice **léxico**: casan las palabras del nodo contra los nombres cortos de Mathlib. Donde el nodo tiene área, aciertan — a `homotopy-theory` le traen `ContinuousMap.Homotopy` y `Path.Homotopy`, que es exactamente lo que es. Donde no la tiene, **no saben**: a `fol-deduction` le traían seis `firstMap` porque «first order logic» empieza por «first».

No es un fallo que se pueda afinar. Es la misma frontera que mide todo el proyecto: el índice busca por palabras y el objeto se identifica por estructura. Así que las fichas marcan cuál de los dos casos es, y cuando no hay señal dan tres pistas en vez de seis. **Una lista vacía no demuestra que no haya objeto** — demuestra que por ahí no se encuentra.

---

## Montón A · 10 decisiones que pueden haber caducado

Marca de vértice —`C`, `S` u `O`— y **cero identificadores de Mathlib**.

**No son diez olvidos.** Los diez llevan `lean=None` en el veredicto, y eso no es la ausencia de una decisión sino una decisión escrita: *ese nombre no existe en Mathlib*. Así que la pregunta no es cuál falta, sino **si sigue siendo verdad**.

Y una decisión sobre lo que Mathlib **no** tiene caduca sola cada vez que Mathlib crece. El veredicto cita el árbol `05322f9` (28 ago 2026) y el índice es posterior. `homotopy-type-theory` no caduca nunca —Lean 4 no es HoTT, y el propio veredicto lo llama «la única etiqueta excluida por fundamento, no por biblioteca»—; `homotopy-theory` puede haber caducado ya.

Por eso van ordenados por caducidad y no por área: primero aquellos para los que el índice **sí** encuentra hoy algo en su propia rama.

### el índice **sí** encuentra algo en su área hoy — empezar por éstos

#### `planar-graphs` — Planar Graphs

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `S` | 3 | 4 | `graph-theory` | 3 | 0 |

> El veredicto dijo: «sin planaridad en Mathlib»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `IncidenceAlgebra.eulerChar` | def | 4 | `Combinatorics.Enumerative.IncidenceAlgebra` |

- [ ] **sigue sin nombre** — la decisión aguanta
- [ ] **ya no es verdad**, y el nombre que entra es: 
- [ ] **la marca era lo que estaba mal** → pasa a: `___`

#### `homotopy-type-theory` — Homotopy Type Theory

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `C` | 2 | 3 | `cic`, `homotopy-theory` | 3 | 0 |

> El veredicto dijo: «IMPOSIBLE en Lean 4: Eq vive en Prop, Prop tiene irrelevancia de pruebas definicional, luego UIP es teorema y la univalencia es inconsistente. UNICA etiqueta excluida por fundamento, no por biblioteca»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `FirstOrder.Language.LHom.onTheory` | def | 12 | `ModelTheory.Syntax` |
| `FirstOrder.Language.Theory` | abbrev | 10 | `ModelTheory.Syntax` |
| `FirstOrder.Language.Theory.Model` | class | 1 | `ModelTheory.Semantics` |
| `FirstOrder.Language.Theory.ModelType` | structure | 0 | `ModelTheory.Bundled` |
| `FirstOrder.Language.Theory.typeOf` | def | 0 | `ModelTheory.Types` |
| `FirstOrder.Language.completeTheory` | def | 0 | `ModelTheory.Semantics` |

- [ ] **sigue sin nombre** — la decisión aguanta
- [ ] **ya no es verdad**, y el nombre que entra es: 
- [ ] **la marca era lo que estaba mal** → pasa a: `___`

#### `geometric-topology` — Geometric Topology

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `C` | 2 | 4 | `algebraic-topology`, `point-set-topology` | 3 | 0 |

> El veredicto dijo: «una variedad de dimension baja»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `DiscreteTopology` | class | 197 | `Topology.Order` |
| `OrderTopology` | class | 196 | `Topology.Order.Basic` |
| `OrderClosedTopology` | class | 77 | `Topology.Order.OrderClosed` |
| `ClosedIciTopology` | class | 50 | `Topology.Order.OrderClosed` |
| `ClosedIicTopology` | class | 44 | `Topology.Order.OrderClosed` |
| `IsModuleTopology` | class | 23 | `Topology.Algebra.Module.ModuleTopology` |

- [ ] **sigue sin nombre** — la decisión aguanta
- [ ] **ya no es verdad**, y el nombre que entra es: 
- [ ] **la marca era lo que estaba mal** → pasa a: `___`

#### `homotopy-theory` — Homotopy Theory

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `C` | 2 | 2 | `algebraic-topology`, `functors` | 4 | 0 |

> El veredicto dijo: «DECIDIDO: Top[W^-1], no hTop. La razon esta en el propio grafo: todas las aristas que salen de este vertice —homology, cohomology, fundamental-group— invierten W, luego por la propiedad universal de la localizacion factorizan por Top[W^-1], que es el vertice INICIAL con esa propiedad. No es una eleccion libre: la imponen las aristas que ya hay. Con hTop los invariantes dejan de ser conservativos (hay equivalencias debiles que no son de homotopia) y el vertice deja de estar determinado.
Cierra ademas la arista con algebraic-topology: elegidos los CW-complejos, Whitehead mas aproximacion celular dan que hCW -> Top[W^-1] es una EQUIVALENCIA, luego la arista es comprobable, no declarativa.
PRECIO EN LEAN: Mathlib tiene MorphismProperty, calculo de fracciones y el marco ModelCategory, pero la unica instancia concreta es la estructura inyectiva sobre complejos de cocadenas. NO hay estructura de Quillen sobre Top ni sobre SSet, asi que un colimite homotopico sobre este vertice no se enuncia hoy. El analogo que si se enuncia vive en DerivedCategory, que es el vertice homological-algebra.»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `ContinuousMap.Homotopy` | structure | 67 | `Topology.Homotopy.Basic` |
| `Path.Homotopy` | abbrev | 67 | `Topology.Homotopy.Path` |
| `SSet.RelativeMorphism.Homotopy` | structure | 67 | `AlgebraicTopology.SimplicialSet.RelativeMorphism` |
| `SSet.Truncated.HomotopyCategory` | def | 50 | `AlgebraicTopology.SimplicialSet.HomotopyCat` |
| `HomotopicalAlgebra.LeftHomotopyRel` | def | 19 | `AlgebraicTopology.ModelCategory.LeftHomotopy` |
| `HomotopicalAlgebra.RightHomotopyRel` | def | 19 | `AlgebraicTopology.ModelCategory.RightHomotopy` |

- [ ] **sigue sin nombre** — la decisión aguanta
- [ ] **ya no es verdad**, y el nombre que entra es: 
- [ ] **la marca era lo que estaba mal** → pasa a: `___`

### el índice no encuentra nada en su área

#### `cic` — CIC

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `C` | 0 | 7 | `fol-deduction` | 15 | **3** |

> El veredicto dijo: «SIN NOMBRE, por decision de curacion. Mathlib no declara el calculo de construcciones inductivas: no hay nada que importar para hablar de el. `CategoryTheory.types` si existe —es la instancia de categoria sobre Type u, en Mathlib.CategoryTheory.Types.Basic— pero nombra OTRA COSA, la categoria de tipos, no el calculo. Ofrecerlo era darle al modelo un nombre que no responde a la pregunta»

Si se retira, quedan sueltos: `area-computability`, `lambda-calculus`, `lean-kernel`

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `CategoryTheory.ToType` | abbrev | 102 | `CategoryTheory.ConcreteCategory.Basic` |
| `Multiset.ToType` | def | 102 | `Data.Multiset.Fintype` |
| `OrderType.ToType` | def | 102 | `Order.Types.Defs` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] **sigue sin nombre** — la decisión aguanta
- [ ] **ya no es verdad**, y el nombre que entra es: 
- [ ] **la marca era lo que estaba mal** → pasa a: `___`

#### `fol-deduction` — FOL Deduction

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `C` | 0 | 8 | — | 10 | **4** |

> El veredicto dijo: «NO es tema: un sistema deductivo es una categoria (Lambek). Es el domicilio de las quince tacticas, que son generadores de flechas. Mathlib no tiene sistema deductivo sintactico; si el proyecto Foundation»

Si se retira, quedan sueltos: `area-logic`, `area-modeltheory`, `cic`, `zfc-axioms`

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `CategoryTheory.Equalizer.Presieve.Arrows.firstMap` | def | 8 | `CategoryTheory.Sites.EqualizerSheafCondition` |
| `CategoryTheory.Equalizer.Presieve.firstMap` | def | 8 | `CategoryTheory.Sites.EqualizerSheafCondition` |
| `CategoryTheory.Equalizer.Sieve.firstMap` | def | 8 | `CategoryTheory.Sites.EqualizerSheafCondition` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

<small>Descartadas por genéricas (tocan más de 300 declaraciones cada una): `order` (515). Si el objeto existe, hay que buscarlo a mano: sus palabras no distinguen.</small>

- [ ] **sigue sin nombre** — la decisión aguanta
- [ ] **ya no es verdad**, y el nombre que entra es: 
- [ ] **la marca era lo que estaba mal** → pasa a: `___`

#### `lambda-calculus` — Lambda Calculus

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `C` | 3 | 5 | `cic` | 3 | 0 |

> El veredicto dijo: «es el metanivel de Lean»

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `Nat.beta` | def | 6 | `Logic.Godel.GodelBetaFunction` |
| `ProbabilityTheory.beta` | def | 6 | `Probability.Distributions.Beta` |
| `ProbabilityTheory.betaPDF` | def | 6 | `Probability.Distributions.Beta` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] **sigue sin nombre** — la decisión aguanta
- [ ] **ya no es verdad**, y el nombre que entra es: 
- [ ] **la marca era lo que estaba mal** → pasa a: `___`

#### `symplectic-geometry` — Symplectic Geometry

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `C` | 2 | 3 | `differential-geometry`, `real-analysis` | 3 | 0 |

> El veredicto dijo: «solo SymplecticGroup»

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `Matrix.symplecticGroup` | def | 13 | `LinearAlgebra.SymplecticGroup` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] **sigue sin nombre** — la decisión aguanta
- [ ] **ya no es verdad**, y el nombre que entra es: 
- [ ] **la marca era lo que estaba mal** → pasa a: `___`

#### `sequent-calculus` — Sequent Calculus

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `C` | 3 | 6 | `proof-theory` | 3 | 0 |

> El veredicto dijo: «mismo vertice que fol-deduction»

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `MeasureTheory.Filtration.natural` | def | 1 | `Probability.Process.Filtration` |
| `CategoryTheory.PreGaloisCategory.IsNaturalSMul` | class | 0 | `CategoryTheory.Galois.IsFundamentalgroup` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] **sigue sin nombre** — la decisión aguanta
- [ ] **ya no es verdad**, y el nombre que entra es: 
- [ ] **la marca era lo que estaba mal** → pasa a: `___`

#### `brownian-motion` — Brownian Motion

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `O` | 3 | 5 | `stochastic-processes` | 3 | 0 |

> El veredicto dijo: «sin nombre en Mathlib 4.29.0-rc4»

**No hay ningún candidato en el índice.** Ni buscando por su nombre ni por sus palabras clave aparece un `structure`, `class`, `def` o `inductive` que pueda ser su objeto.

- [ ] **sigue sin nombre** — la decisión aguanta
- [ ] **ya no es verdad**, y el nombre que entra es: 
- [ ] **la marca era lo que estaba mal** → pasa a: `___`

---

## Montón B · 36 vértices marcados fuera

Marca `T` —«ni objetos ni flechas»— y sin embargo son nodos de pleno derecho.

El caso más fuerte está aquí: **`zfc-axioms` está marcado `T`** y de él salen **143 flechas**. Su hermano fundacional `fol-deduction` está marcado `C`. Los dos pilares del grafo recibieron marcas opuestas, y ninguna medición iba a notarlo.

### área `(fundacional)`

#### `lean-kernel` — Lean 4 Kernel

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 0 | 6 | `cic` | 10 | **1** |

> El veredicto dijo: «un programa concreto»

Si se retira, quedan sueltos: `formal-verification`

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `ProbabilityTheory.Kernel` | structure | 518 | `Probability.Kernel.Defs` |
| `CategoryTheory.Limits.HasKernel` | abbrev | 45 | `CategoryTheory.Limits.Shapes.Kernels` |
| `CategoryTheory.Limits.kernel` | abbrev | 18 | `CategoryTheory.Limits.Shapes.Kernels` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `zfc-axioms` — ZFC Axioms

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 0 | 9 | `fol-deduction` | 143 | **20** |

> El veredicto dijo: «enunciados; el universo V si es categoria: ZFSet»

Si se retira, quedan sueltos: `area-algebra`, `area-algebraicgeometry`, `area-algebraictopology`, `area-analysis`, `area-combinatorics`, `area-dynamics`, `area-fieldtheory`, `area-geometry`, `area-grouptheory`, `area-linearalgebra`, `area-measuretheory`, `area-numbertheory`, `area-ordertheory`, `area-probability`, `area-representationtheory`, `area-ringtheory`, `area-settheory`, `area-topology`, `cat-basics`, `enumerative-combinatorics`

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `Quotient.finChoice` | def | 4 | `Data.Fintype.Quotient` |
| `Trunc.finChoice` | def | 4 | `Data.Fintype.Quotient` |
| `CompactExhaustion.choice` | def | 3 | `Topology.Compactness.SigmaCompact` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

### área `algebra`

#### `canonical-forms` — Canonical Forms

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 4 | `eigen-theory` | 3 | 0 |

> El veredicto dijo: «clasificacion; el esqueleto de eigen-theory»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `LinearMap.BilinForm` | abbrev | 124 | `LinearAlgebra.BilinearMap` |
| `Cycle.formPerm` | def | 47 | `GroupTheory.Perm.Cycle.Concrete` |
| `List.formPerm` | def | 47 | `GroupTheory.Perm.List` |
| `Algebra.traceForm` | def | 44 | `RingTheory.Trace.Defs` |
| `LieModule.traceForm` | def | 44 | `Algebra.Lie.TraceForm` |
| `killingForm` | abbrev | 21 | `Algebra.Lie.TraceForm` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

### área `analysis`

#### `contour-integration` — Contour Integration

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 6 | `holomorphic-functions` | 4 | **1** |

> El veredicto dijo: «una tecnica; el emparejamiento H_1 x H^1_dR -> C»

Si se retira, quedan sueltos: `residue-theorem`

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `MeasureTheory.HasFiniteIntegral` | def | 85 | `MeasureTheory.Function.L1Space.HasFiniteIntegral` |
| `BoxIntegral.integral` | def | 52 | `Analysis.BoxIntegral.Basic` |
| `MeasureTheory.L1.SimpleFunc.integral` | def | 52 | `MeasureTheory.Integral.Bochner.L1` |
| `MeasureTheory.SimpleFunc.integral` | def | 52 | `MeasureTheory.Integral.Bochner.L1` |
| `BoxIntegral.IntegrationParams` | structure | 28 | `Analysis.BoxIntegral.Partition.Filter` |
| `Fourier.fourierIntegral` | def | 27 | `Analysis.Fourier.FourierTransform` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `pde-techniques` — PDE Techniques

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 2 | 3 | `functional-analysis`, `real-analysis` | 4 | 0 |

> El veredicto dijo: «tecnicas»

**No hay ningún candidato en el índice.** Ni buscando por su nombre ni por sus palabras clave aparece un `structure`, `class`, `def` o `inductive` que pueda ser su objeto.

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `residue-theorem` — Residue Theorem

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 8 | `contour-integration` | 3 | 0 |

> El veredicto dijo: «un teorema; via Complex.integral_circle»

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `IsLocalRing.ResidueField` | def | 26 | `RingTheory.LocalRing.ResidueField.Defs` |
| `Valued.ResidueField` | def | 26 | `Topology.Algebra.Valued.ValuedField` |
| `IsLocalRing.residue` | def | 24 | `RingTheory.LocalRing.ResidueField.Defs` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

### área `category-theory`

#### `universal-properties` — Universal Properties

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 3 | `limits` | 3 | 0 |

> El veredicto dijo: «el mecanismo, no un tema; Functor.Representable, IsInitial»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `CategoryTheory.CostructuredArrow.IsUniversal` | abbrev | 18 | `CategoryTheory.Comma.StructuredArrow.Basic` |
| `CategoryTheory.StructuredArrow.IsUniversal` | abbrev | 18 | `CategoryTheory.Comma.StructuredArrow.Basic` |
| `CategoryTheory.IsUniversalColimit` | def | 12 | `CategoryTheory.Limits.VanKampen` |
| `CategoryTheory.Idempotents.karoubiUniversal` | def | 2 | `CategoryTheory.Idempotents.FunctorExtension` |
| `CategoryTheory.Idempotents.karoubiUniversal₁` | def | 0 | `CategoryTheory.Idempotents.FunctorExtension` |
| `CategoryTheory.Idempotents.karoubiUniversal₂` | def | 0 | `CategoryTheory.Idempotents.FunctorExtension` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `yoneda-lemma` — Yoneda Lemma

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 3 | `functors` | 3 | 0 |

> El veredicto dijo: «un lema; el funtor y si es objeto: CategoryTheory.yoneda»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `CategoryTheory.GrothendieckTopology.yoneda` | def | 48 | `CategoryTheory.Sites.Canonical` |
| `CategoryTheory.Limits.IndObjectPresentation.yoneda` | def | 48 | `CategoryTheory.Limits.Indization.IndObject` |
| `CategoryTheory.yoneda` | def | 48 | `CategoryTheory.Yoneda` |
| `CategoryTheory.GrothendieckTopology.yonedaEquiv` | def | 19 | `CategoryTheory.Sites.Subcanonical` |
| `CategoryTheory.yonedaEquiv` | def | 19 | `CategoryTheory.Yoneda` |
| `CategoryTheory.OverPresheafAux.YonedaCollection` | def | 12 | `CategoryTheory.Comma.Presheaf.Basic` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

### área `combinatorics`

#### `algebraic-combinatorics` — Algebraic Combinatorics

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 2 | 1 | `enumerative-combinatorics`, `group-theory` | 4 | 0 |

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `Algebra.IsAlgebraic` | class | 201 | `RingTheory.Algebraic.Defs` |
| `FirstOrder.Language.IsAlgebraic` | abbrev | 116 | `ModelTheory.Basic` |
| `IsAlgebraic` | def | 116 | `RingTheory.Algebraic.Defs` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `enumerative-combinatorics` — Enumerative Combinatorics

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 1 | 10 | `zfc-axioms` | 10 | **1** |

> El veredicto dijo: «ambiente: FintypeCat»

Si se retira, quedan sueltos: `inclusion-exclusion`

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `Nat.factorial` | def | 21 | `Data.Nat.Factorial.Basic` |
| `Nat.ascFactorial` | def | 18 | `Data.Nat.Factorial.Basic` |
| `Nat.descFactorial` | def | 16 | `Data.Nat.Factorial.Basic` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `extremal-combinatorics` — Extremal Combinatorics

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 2 | 2 | `graph-theory` | 3 | 0 |

> El veredicto dijo: «una rama»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `SimpleGraph.extremalNumber` | def | 20 | `Combinatorics.SimpleGraph.Extremal.Basic` |
| `SimpleGraph.IsExtremal` | def | 1 | `Combinatorics.SimpleGraph.Extremal.Basic` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `inclusion-exclusion` — Inclusion-Exclusion

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 5 | `enumerative-combinatorics` | 3 | 0 |

> El veredicto dijo: «una tecnica; inversion de Mobius: IncidenceAlgebra»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `SimpleGraph.Subgraph.inclusion` | def | 169 | `Combinatorics.SimpleGraph.Subgraph` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `matching-theory` — Matching Theory

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 7 | `graph-theory` | 3 | 0 |

> El veredicto dijo: «familia de problemas; SimpleGraph.Subgraph.IsMatching»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `SimpleGraph.Subgraph.IsMatching` | def | 9 | `Combinatorics.SimpleGraph.Matching` |
| `SimpleGraph.Subgraph.IsPerfectMatching` | def | 2 | `Combinatorics.SimpleGraph.Matching` |
| `hallMatchingsOn` | def | 2 | `Combinatorics.Hall.Basic` |
| `SimpleGraph.IsMatchingFree` | def | 0 | `Combinatorics.SimpleGraph.Matching` |
| `SimpleGraph.Subgraph.IsMatching.toEdge` | def | 0 | `Combinatorics.SimpleGraph.Matching` |
| `hallMatchingsFunctor` | def | 0 | `Combinatorics.Hall.Basic` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `probabilistic-method` — Probabilistic Method

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 2 | 1 | `enumerative-combinatorics`, `probability-theory` | 3 | 0 |

**No hay ningún candidato en el índice.** Ni buscando por su nombre ni por sus palabras clave aparece un `structure`, `class`, `def` o `inductive` que pueda ser su objeto.

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `ramsey-theory` — Ramsey Theory

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 2 | 1 | `enumerative-combinatorics`, `graph-theory` | 3 | 0 |

> El veredicto dijo: «una rama; sin numeros de Ramsey en Mathlib»

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `FirstOrder.Language.LHom.onTheory` | def | 12 | `ModelTheory.Syntax` |
| `FirstOrder.Language.Theory` | abbrev | 10 | `ModelTheory.Syntax` |
| `FirstOrder.Language.Theory.Model` | class | 1 | `ModelTheory.Semantics` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

### área `computation`

#### `algorithm-analysis` — Algorithm Analysis

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 1 | 3 | `cic`, `proof-theory` | 3 | 0 |

> El veredicto dijo: «una disciplina»

**No hay ningún candidato en el índice.** Ni buscando por su nombre ni por sus palabras clave aparece un `structure`, `class`, `def` o `inductive` que pueda ser su objeto.

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `computability-theory` — Computability Theory

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 1 | 4 | `fol-metatheory`, `model-theory` | 7 | **2** |

> El veredicto dijo: «una rama; los grados de Turing son orden parcial: TuringDegree»

Si se retira, quedan sueltos: `computational-complexity`, `partial-functions`

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `FirstOrder.Language.LHom.onTheory` | def | 12 | `ModelTheory.Syntax` |
| `FirstOrder.Language.Theory` | abbrev | 10 | `ModelTheory.Syntax` |
| `FirstOrder.Language.Theory.Model` | class | 1 | `ModelTheory.Semantics` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `computational-complexity` — Computational Complexity

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 1 | 2 | `computability-theory` | 4 | **1** |

> El veredicto dijo: «una rama; las reducciones son un preorden»

Si se retira, quedan sueltos: `np-completeness`

**No hay ningún candidato en el índice.** Ni buscando por su nombre ni por sus palabras clave aparece un `structure`, `class`, `def` o `inductive` que pueda ser su objeto.

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `formal-verification` — Formal Verification

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 1 | 2 | `lean-kernel` | 3 | 0 |

> El veredicto dijo: «una actividad»

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `LinearPMap.IsFormalAdjoint` | def | 1 | `Analysis.InnerProductSpace.LinearPMap` |
| `CategoryTheory.Limits.FormalCoproduct` | structure | 0 | `CategoryTheory.Limits.FormalCoproducts.Basic` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `np-completeness` — NP-Completeness

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 8 | `computational-complexity` | 3 | 0 |

> El veredicto dijo: «una clase de problemas»

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `CompleteSpace` | class | 495 | `Topology.UniformSpace.Cauchy` |
| `CompleteLattice` | class | 149 | `Order.CompleteLattice.Defs` |
| `CauSeq.IsComplete` | class | 60 | `Algebra.Order.CauSeq.Completion` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `recursion-theory` — Recursion Theory

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 4 | `turing-machines` | 5 | 0 |

> El veredicto dijo: «sinonimo de computability-theory»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `TuringDegree` | abbrev | 1 | `Computability.TuringDegree` |
| `TuringEquivalent` | abbrev | 1 | `Computability.TuringDegree` |
| `TuringReducible` | abbrev | 0 | `Computability.TuringDegree` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

### área `geometry`

#### `circle-geometry` — Circle Geometry

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 7 | `euclidean-geometry` | 4 | 0 |

> El veredicto dijo: «un capitulo; objetos en EuclideanGeometry.Sphere»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `InnerProductGeometry.angle` | def | 115 | `Geometry.Euclidean.Angle.Unoriented.Basic` |
| `Affine.Simplex.ninePointCircle` | def | 2 | `Geometry.Euclidean.NinePointCircle` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

### área `logic`

#### `compactness-theorem` — Compactness and Lowenheim-Skolem

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 6 | `model-theory` | 4 | 0 |

> El veredicto dijo: «un teorema; Theory.isSatisfiable_iff_isFinitelySatisfiable»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `FirstOrder.Language.skolem₁` | def | 0 | `ModelTheory.Skolem` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `incompleteness` — Godel Incompleteness

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 7 | `proof-theory` | 3 | 0 |

> El veredicto dijo: «dos teoremas; en Foundation (Lean 4), no en Mathlib»

**No hay ningún candidato en el índice.** Ni buscando por su nombre ni por sus palabras clave aparece un `structure`, `class`, `def` o `inductive` que pueda ser su objeto.

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `proof-theory` — Proof Theory

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 1 | 4 | `fol-deduction`, `strategy-contradiction` | 6 | **2** |

> El veredicto dijo: «una rama; su objeto es la categoria de fol-deduction»

Si se retira, quedan sueltos: `incompleteness`, `sequent-calculus`

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `FirstOrder.Language.LHom.onTheory` | def | 12 | `ModelTheory.Syntax` |
| `FirstOrder.Language.Theory` | abbrev | 10 | `ModelTheory.Syntax` |
| `FirstOrder.Language.Theory.Model` | class | 1 | `ModelTheory.Semantics` |
| `FirstOrder.Language.completeTheory` | def | 0 | `ModelTheory.Semantics` |
| `FirstOrder.Language.infiniteTheory` | def | 0 | `ModelTheory.Syntax` |
| `FirstOrder.Language.linearOrderTheory` | def | 0 | `ModelTheory.Order` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

### área `number-theory`

#### `analytic-number-theory` — Analytic Number Theory

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 2 | 1 | `complex-analysis`, `elementary-number-theory` | 6 | **1** |

Si se retira, quedan sueltos: `prime-number-theorem`

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `AnalyticAt` | def | 213 | `Analysis.Analytic.Basic` |
| `AnalyticOnNhd` | def | 160 | `Analysis.Analytic.Basic` |
| `AnalyticOn` | def | 131 | `Analysis.Analytic.Basic` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `diophantine-equations` — Diophantine Equations

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 6 | `modular-arithmetic` | 3 | 0 |

> El veredicto dijo: «familia de problemas; X(Z) es el funtor de puntos»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `Pell.IsPell` | def | 9 | `NumberTheory.PellMatiyasevic` |
| `Pell.pellZd` | def | 9 | `NumberTheory.PellMatiyasevic` |
| `Pell.pell` | def | 1 | `NumberTheory.PellMatiyasevic` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `prime-factorization` — Prime Factorization

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 12 | `divisibility-gcd` | 3 | 0 |

> El veredicto dijo: «un teorema; UniqueFactorizationMonoid»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `ArithmeticFunction` | def | 105 | `NumberTheory.ArithmeticFunction.Defs` |
| `Subgroup.IsArithmetic` | class | 26 | `NumberTheory.ModularForms.ArithmeticSubgroups` |
| `Pell.IsFundamental` | def | 18 | `NumberTheory.Pell` |
| `NumberField.mixedEmbedding.fundamentalCone` | def | 13 | `NumberTheory.NumberField.CanonicalEmbedding.FundamentalCone` |
| `Nat.primesBelow` | def | 12 | `NumberTheory.SmoothNumbers` |
| `toArithmeticFunction` | def | 4 | `NumberTheory.LSeries.Convolution` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `prime-number-theorem` — Prime Number Theorem

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 4 | `analytic-number-theory` | 3 | 0 |

> El veredicto dijo: «un teorema; en PrimeNumberTheoremAnd, no en Mathlib»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `Nat.ProbablePrime` | def | 3 | `NumberTheory.FermatPsp` |
| `Nat.primeCounting` | def | 3 | `NumberTheory.PrimeCounting` |
| `Nat.primeCounting'` | def | 2 | `NumberTheory.PrimeCounting` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `quadratic-residues` — Quadratic Residues

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 7 | `modular-arithmetic` | 3 | 0 |

> El veredicto dijo: «un capitulo; el simbolo de Legendre es un caracter: legendreSym»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `jacobiTheta` | def | 53 | `NumberTheory.ModularForms.JacobiTheta.OneVariable` |
| `legendreSym` | def | 37 | `NumberTheory.LegendreSymbol.Basic` |
| `quadraticChar` | def | 23 | `NumberTheory.LegendreSymbol.QuadraticChar.Basic` |
| `MulChar.IsQuadratic` | def | 17 | `NumberTheory.MulChar.Basic` |
| `jacobiSum` | def | 15 | `NumberTheory.JacobiSum.Basic` |
| `ArithmeticFunction.vonMangoldt.residueClass` | abbrev | 12 | `NumberTheory.LSeries.PrimesInAP` |

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

### área `optimization`

#### `convex-optimization` — Convex Optimization

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 1 | 4 | `real-analysis` | 3 | **1** |

> El veredicto dijo: «una tecnica; conjuntos convexos con afines»

Si se retira, quedan sueltos: `linear-programming`

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `Convex` | def | 455 | `Analysis.Convex.Basic` |
| `ConvexOn` | def | 194 | `Analysis.Convex.Function` |
| `convexHull` | def | 126 | `Analysis.Convex.Hull` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `discrete-optimization` — Discrete Optimization

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 1 | 2 | `enumerative-combinatorics`, `graph-theory` | 1 | 0 |

> El veredicto dijo: «una tecnica»

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `DiscreteTopology` | class | 197 | `Topology.Order` |
| `CategoryTheory.Discrete` | structure | 139 | `CategoryTheory.Discrete.Basic` |
| `CategoryTheory.IsDiscrete` | class | 70 | `CategoryTheory.Discrete.Basic` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `linear-programming` — Linear Programming

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 3 | `convex-optimization` | 1 | 0 |

> El veredicto dijo: «una tecnica; la dualidad LP»

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `Affine.Simplex` | structure | 232 | `LinearAlgebra.AffineSpace.Simplex.Basic` |
| `SimplexCategory` | def | 124 | `AlgebraicTopology.SimplexCategory.Defs` |
| `SSet.Augmented.stdSimplex` | def | 67 | `AlgebraicTopology.SimplicialSet.StdSimplex` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

#### `variational-methods` — Variational Methods

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 2 | 3 | `functional-analysis`, `pde-techniques`, `real-analysis` | 1 | 0 |

> El veredicto dijo: «tecnicas; puntos criticos de funcionales»

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `ComplexShape.EulerCharSigns` | class | 4 | `Algebra.Homology.EulerCharacteristic` |
| `GradedObject.eulerChar` | def | 4 | `Algebra.Homology.EulerCharacteristic` |
| `HomologicalComplex.eulerChar` | abbrev | 4 | `Algebra.Homology.EulerCharacteristic` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

### área `probability`

#### `limit-theorems` — Limit Theorems

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 4 | `random-variables` | 3 | 0 |

> El veredicto dijo: «teoremas (LGN, TCL)»

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `ProbabilityTheory.centralMoment` | def | 6 | `Probability.Moments.Basic` |

<small>Descartadas por genéricas (tocan más de 300 declaraciones cada una): `limit` (591). Si el objeto existe, hay que buscarlo a mano: sus palabras no distinguen.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

### área `set-theory`

#### `forcing` — Forcing

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 4 | `cardinal-arithmetic` | 3 | 0 |

> El veredicto dijo: «una tecnica; el topos de prehaces sobre P. Flypitch quedo en Lean 3»

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `IsCyclotomicExtension` | class | 137 | `NumberTheory.Cyclotomic.Basic` |
| `CategoryTheory.Functor.WellOrderInductionData.Extension` | structure | 26 | `CategoryTheory.SmallObject.WellOrderInductionData` |
| `FiniteField.Extension` | def | 26 | `FieldTheory.Finite.Extension` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

---

## Montón C · 2 marcados fuera y con voz

Marca `T` **y además** ofrecen identificadores al prompt. Es la contradicción exacta, y la única del documento que no admite «se queda como está».

### área `analysis`

#### `limits-continuity` — Limits and Continuity

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 10 | `area-ordertheory`, `real-analysis` | 5 | 0 |

> El veredicto dijo: «dos nociones; continuidad = ser morfismo»

**Nombres que ya ofrece al prompt:** `Continuous`, `ContinuousAt`, `Filter.Tendsto`

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `CategoryTheory.Limits.HasLimitsOfShape` | class | 116 | `CategoryTheory.Limits.HasLimits` |
| `CategoryTheory.Limits.PreservesLimits` | abbrev | 59 | `CategoryTheory.Limits.Preserves.Basic` |
| `CategoryTheory.Limits.HasFiniteLimits` | class | 44 | `CategoryTheory.Limits.Shapes.FiniteLimits` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

<small>Descartadas por genéricas (tocan más de 300 declaraciones cada una): `limit` (591), `continuous` (340). Si el objeto existe, hay que buscarlo a mano: sus palabras no distinguen.</small>

- [ ] **la marca estaba mal** → pasa a `___`
- [ ] **la marca está bien** → se le quitan los nombres
- [ ] sus propias notas ya lo susurran; escribir cuál de las dos gana

### área `set-theory`

#### `cardinal-arithmetic` — Cardinal Arithmetic

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 13 | `area-settheory`, `zfc-axioms` | 5 | **1** |

> El veredicto dijo: «el sustrato Cardinal si es categoria delgada»

**Nombres que ya ofrece al prompt:** `Cardinal`, `Set.Countable`, `Nat.card`

Si se retira, quedan sueltos: `forcing`

**Candidatos en su área (existen; el módulo está verificado)**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `Cardinal` | def | 645 | `SetTheory.Cardinal.Defs` |
| `HasCardinalLT` | def | 57 | `SetTheory.Cardinal.HasCardinalLT` |
| `embeddingToCardinal` | def | 0 | `SetTheory.Cardinal.Order` |

- [ ] **la marca estaba mal** → pasa a `___`
- [ ] **la marca está bien** → se le quitan los nombres
- [ ] sus propias notas ya lo susurran; escribir cuál de las dos gana

---

## Antes de dar por buena cualquier respuesta

```
python -m scripts.recuperacion_contra_proofnet
python -m scripts.banco_docstrings
python -m scripts.banco_herald
```

**Baseline hoy: 22,8 % / 18,0 % contra ProofNet**, 5,0 % sobre Mathlib entero, 10,3 % contra Herald. Una tanda entra si sube su barrio y no baja el global.

Y aquí hay una asimetría que conviene tener presente: **quitar un nombre o retirar un nodo casi nunca baja la precisión**, así que el montón C y las retiradas del B se pueden medir barato. **Añadir** nombres sí tiene coste — la primera tanda bajó de 21,3 % a 19,9 % antes de que la puerta `_evidencia_declarada` lo arreglara. El montón A es el caro.
