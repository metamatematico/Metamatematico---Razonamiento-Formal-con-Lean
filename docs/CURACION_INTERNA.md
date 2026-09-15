# Curación interna

> Generado por `scripts/hoja_de_curacion_interna.py`. **No editar a mano**: se regenera.


Las otras dos hojas miran hacia **afuera** — qué trozo de Mathlib no cubre el grafo. Ésta mira hacia **adentro**: de los 189 conceptos que ya están, cuáles no cumplen lo que su propia marca promete.

Son **9 decisiones**, y ninguna medición las había pedido nunca — porque ninguna medición mira ahí. Los bancos miden lo que el grafo **ofrece**; esto es lo que el grafo **promete**.

## El inventario completo, para que se vea qué parte es ésta

| montón | qué es | cuántos | dónde |
|---|---|---:|---|
| enunciados que fallan | los 62 que la cabecera fija no alcanzaba | **0** | agotado |
| cobertura de Mathlib | ramas que el grafo abrió y dejó finas | **24** | `CURACION_RAMAS.pdf` |
| **A · `lean=None` que puede haber caducado** | marca de vértice, cero nombres, y un «no existe» fechado en agosto | **8** | *aquí* |
| **B · vértices marcados fuera** | marca `T` y sin embargo son nodos | **1** | *aquí* |
| **C · marcados fuera y con voz** | marca `T` y además dan nombres | **0** | *aquí* |

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

> La tercera opción es la que más importa de las tres. Si es la correcta para la mayoría de los 1, entonces lo que falta no son 1 decisiones sino **una marca nueva** — algo como `R` de enrutador — y la hoja se cierra de golpe. Si no lo es, hay que ir uno por uno.

**En el montón C** la contradicción es exacta y no admite «se queda como está»: el veredicto dice que no son objetos y están alimentando plazas del prompt. Una de las dos mitades sobra.

### Qué valen los candidatos que trae cada ficha

Salen de un índice **léxico**: casan las palabras del nodo contra los nombres cortos de Mathlib. Donde el nodo tiene área, aciertan — a `homotopy-theory` le traen `ContinuousMap.Homotopy` y `Path.Homotopy`, que es exactamente lo que es. Donde no la tiene, **no saben**: a `fol-deduction` le traían seis `firstMap` porque «first order logic» empieza por «first».

No es un fallo que se pueda afinar. Es la misma frontera que mide todo el proyecto: el índice busca por palabras y el objeto se identifica por estructura. Así que las fichas marcan cuál de los dos casos es, y cuando no hay señal dan tres pistas en vez de seis. **Una lista vacía no demuestra que no haya objeto** — demuestra que por ahí no se encuentra.

---

## Montón A · 8 decisiones que pueden haber caducado

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
| `FirstOrder.Language.Theory.ModelType` | structure | 0 | `ModelTheory.Bundled` |
| `FirstOrder.Language.Theory.typeOf` | def | 0 | `ModelTheory.Types` |

<small>Descartadas por genéricas (tocan más de 300 declaraciones cada una): `theory` (48). Si el objeto existe, hay que buscarlo a mano: sus palabras no distinguen.</small>

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

<small>Descartadas por genéricas (tocan más de 300 declaraciones cada una): `theory` (48). Si el objeto existe, hay que buscarlo a mano: sus palabras no distinguen.</small>

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

<small>Descartadas por genéricas (tocan más de 300 declaraciones cada una): `theory` (48). Si el objeto existe, hay que buscarlo a mano: sus palabras no distinguen.</small>

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

---

## Montón B · 1 vértices marcados fuera

Marca `T` —«ni objetos ni flechas»— y sin embargo son nodos de pleno derecho.

El caso más fuerte está aquí: **`zfc-axioms` está marcado `T`** y de él salen **143 flechas**. Su hermano fundacional `fol-deduction` está marcado `C`. Los dos pilares del grafo recibieron marcas opuestas, y ninguna medición iba a notarlo.

### área `analysis`

#### `limits-continuity` — Limits and Continuity

| marca | nivel | palabras clave | padres | hijos | hijos que quedarían sueltos |
|---|---|---:|---|---:|---:|
| `T` | 3 | 10 | `area-ordertheory`, `real-analysis` | 5 | 0 |

> El veredicto dijo: «dos nociones; continuidad = ser morfismo»

**Ninguno en su área. Pistas léxicas, probablemente ninguna sirve**

| identificador | tipo | citas | módulo |
|---|---|---:|---|
| `CategoryTheory.Limits.HasLimitsOfShape` | class | 116 | `CategoryTheory.Limits.HasLimits` |
| `CategoryTheory.Limits.PreservesLimits` | abbrev | 59 | `CategoryTheory.Limits.Preserves.Basic` |
| `CategoryTheory.Limits.HasFiniteLimits` | class | 44 | `CategoryTheory.Limits.Shapes.FiniteLimits` |

<small>El índice casa palabras contra nombres. Sin señal de área no sabe, y estas tres salen de que alguna palabra del nodo aparece en el nombre — nada más.</small>

<small>Descartadas por genéricas (tocan más de 300 declaraciones cada una): `limit` (591), `continuous` (340). Si el objeto existe, hay que buscarlo a mano: sus palabras no distinguen.</small>

- [ ] se **retira** del grafo
- [ ] **cambia de marca** a `___` y toma el nombre: 
- [ ] se queda como **enrutador declarado**: sin voz, sólo para que sus palabras clave lleguen a los hijos

---

## Montón C · 0 marcados fuera y con voz

Marca `T` **y además** ofrecen identificadores al prompt. Es la contradicción exacta, y la única del documento que no admite «se queda como está».

---

## Antes de dar por buena cualquier respuesta

```
python -m scripts.recuperacion_contra_proofnet
python -m scripts.banco_docstrings
python -m scripts.banco_herald
```

**Baseline hoy: 22,8 % / 18,0 % contra ProofNet**, 5,0 % sobre Mathlib entero, 10,3 % contra Herald. Una tanda entra si sube su barrio y no baja el global.

Y aquí hay una asimetría que conviene tener presente: **quitar un nombre o retirar un nodo casi nunca baja la precisión**, así que el montón C y las retiradas del B se pueden medir barato. **Añadir** nombres sí tiene coste — la primera tanda bajó de 21,3 % a 19,9 % antes de que la puerta `_evidencia_declarada` lo arreglara. El montón A es el caro.
