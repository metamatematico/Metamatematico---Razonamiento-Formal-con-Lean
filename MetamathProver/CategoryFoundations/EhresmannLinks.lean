/-
# Enlaces simples y complejos, en el sentido de Ehresmann

## Por qué este archivo existe

`SimpleComplexLinks.lean` formaliza una noción de enlace simple que NO es la de
Ehresmann. Allí «simple» significa *factoriza por un objeto que es clúster*:

    simple(a, b)  :=  ∃ c ∈ Clusters, a ≤ c ∧ c ≤ b

Con esa lectura se demuestra que los simples cierran por composición, y de ahí
se concluyó —erróneamente— que la emergencia no puede darse en el modelo. La
conclusión no se sigue, porque la definición era otra.

En Ehresmann y Vanbremeersch un enlace es simple cuando está **inducido por un
clúster entre descomposiciones**:

  · un patrón `P` es un diagrama; `cP` es su colímite (su *binding*);
  · un clúster `G : P → Q` es una familia coherente y maximal de enlaces entre
    componentes;
  · todo clúster induce un único enlace `colim G : cP → cQ`;
  · `f : cP → cQ` es **(P,Q)-simple** si `f = colim G` para algún clúster `G`;
  · `f` es **simple** si lo es para algunas descomposiciones de su fuente y su
    destino;
  · `f` es **complejo** si es composición de simples y no es simple.

La diferencia es esencial: lo primero es una condición sobre OBJETOS
intermedios; lo segundo, sobre la existencia de un clúster que induzca el
enlace. Un compuesto puede pasar por objetos-clúster y aun así no estar
inducido por ningún clúster.

## Qué se establece aquí

Las definiciones fieles, y los teoremas que se siguen de ellas sin necesidad de
un modelo concreto:

1. `simple_of_cluster` — la caracterización.
2. `composite_simple_of_same_decomposition` — si comparten la MISMA
   descomposición intermedia, el compuesto es simple.
3. `composite_simple_of_connected` — basta que las descomposiciones intermedias
   estén conectadas por un clúster.
4. `complex_needs_unconnected` — **el resultado central**: un enlace complejo
   solo puede aparecer cuando las descomposiciones intermedias NO están
   conectadas. Es decir, el Principio de Multiplicidad no es un adorno: es la
   condición necesaria para que exista complejidad.
5. `multiplicidad_necesaria_para_complejidad` — sin Principio de Multiplicidad
   en el objeto intermedio, todo compuesto de simples es simple.

Lo que NO se establece: que los enlaces complejos EXISTAN. Eso requiere exhibir
un modelo concreto con dos descomposiciones homólogas no conectadas, y es el
siguiente paso.

## Estatus

Ésta es una lectura de las definiciones de MES; se declara como tal. Los
teoremas son consecuencias de las definiciones aquí escritas, sean o no fieles
al original en cada detalle.
-/

import Mathlib.Order.Basic
import Mathlib.Data.Finset.Basic

namespace MetamathProver.EhresmannLinks

universe u

/-! ## 1. Patrones, clústeres y enlaces inducidos -/

variable {O : Type u}

/--
Estructura mínima para hablar de enlaces simples: qué objetos son colímite de
qué patrones, y qué clústeres hay entre patrones.

Se axiomatiza en vez de construirse porque lo que interesa aquí es qué se sigue
de las relaciones, no cómo se realizan.
-/
structure MESData (O : Type u) (Pat : Type u) where
  /-- `binding P` es el colímite del patrón `P`, su *binding*. -/
  binding : Pat → O
  /-- `Cluster P Q` : existe un clúster de `P` a `Q`. -/
  Cluster : Pat → Pat → Prop
  /-- Los clústeres componen: es la coherencia que Ehresmann exige. -/
  cluster_comp : ∀ {P Q R}, Cluster P Q → Cluster Q R → Cluster P R
  /-- Todo patrón tiene el clúster identidad. -/
  cluster_id : ∀ P, Cluster P P

variable {Pat : Type u} (M : MESData O Pat)

/--
`EsSimple f` : el enlace de `a` a `b` está inducido por un clúster entre
descomposiciones suyas.

`f` se representa por el par `(a, b)` porque en este nivel de abstracción lo
único que importa es qué pares están inducidos por un clúster.
-/
def EsSimple (a b : O) : Prop :=
  ∃ P Q : Pat, M.binding P = a ∧ M.binding Q = b ∧ M.Cluster P Q

/--
`Descomposiciones a` : los patrones cuyo colímite es `a`.

Que haya más de uno es exactamente el Principio de Multiplicidad.
-/
def Descomposicion (P : Pat) (a : O) : Prop := M.binding P = a

/-! ## 2. Lo que se sigue -/

theorem simple_of_cluster {a b : O} {P Q : Pat}
    (hP : M.binding P = a) (hQ : M.binding Q = b) (hG : M.Cluster P Q) :
    EsSimple M a b :=
  ⟨P, Q, hP, hQ, hG⟩

/-- Todo objeto que sea binding de algún patrón tiene enlace simple consigo. -/
theorem simple_refl {a : O} {P : Pat} (hP : M.binding P = a) :
    EsSimple M a a :=
  ⟨P, P, hP, hP, M.cluster_id P⟩

/--
**Teorema.** Si dos enlaces simples comparten la MISMA descomposición
intermedia, su composición es simple.

La demostración usa `cluster_comp`, es decir, la coherencia de los clústeres.
Nótese la hipótesis: no basta que el objeto intermedio sea el mismo, hace falta
que la DESCOMPOSICIÓN lo sea.
-/
theorem composite_simple_of_same_decomposition {a b c : O} {P Q R : Pat}
    (hP : M.binding P = a) (hQ : M.binding Q = b) (hR : M.binding R = c)
    (h1 : M.Cluster P Q) (h2 : M.Cluster Q R) :
    EsSimple M a c :=
  ⟨P, R, hP, hR, M.cluster_comp h1 h2⟩

/--
**Teorema.** Si las dos descomposiciones intermedias están conectadas por un
clúster, la composición vuelve a ser simple.

Es la forma general del anterior: no hace falta que `Q = Q'`, basta que haya un
clúster `Q → Q'`.
-/
theorem composite_simple_of_connected {a c : O} {P Q Q' R : Pat}
    (hP : M.binding P = a) (hR : M.binding R = c)
    (h1 : M.Cluster P Q) (hQQ' : M.Cluster Q Q') (h2 : M.Cluster Q' R) :
    EsSimple M a c :=
  ⟨P, R, hP, hR, M.cluster_comp h1 (M.cluster_comp hQQ' h2)⟩

/--
**Teorema central.** Un enlace complejo exige descomposiciones intermedias NO
conectadas.

Dicho al revés: si toda pareja de descomposiciones del objeto intermedio
estuviera conectada por un clúster, todo compuesto de simples sería simple y no
habría complejidad ninguna.

Éste es el contenido del Principio de Multiplicidad. No es un axioma decorativo
sobre robustez: es la condición NECESARIA para que el sistema pueda producir
enlaces que no se reducen a un solo clúster.
-/
theorem complex_needs_unconnected {a c : O} {P Q Q' R : Pat}
    (hP : M.binding P = a) (hR : M.binding R = c)
    (h1 : M.Cluster P Q) (h2 : M.Cluster Q' R)
    (hcomplejo : ¬ EsSimple M a c) :
    ¬ M.Cluster Q Q' :=
  fun hQQ' => hcomplejo (composite_simple_of_connected M hP hR h1 hQQ' h2)

/--
**Corolario.** Si el objeto intermedio tiene una sola descomposición, no puede
nacer complejidad al componer a través de él.
-/
theorem no_complexity_with_unique_decomposition {a b c : O} {P Q R : Pat}
    (hunica : ∀ Q' : Pat, M.binding Q' = b → Q' = Q)
    (hP : M.binding P = a) (hQ : M.binding Q = b) (hR : M.binding R = c)
    (h1 : M.Cluster P Q) (h2 : M.Cluster Q R) :
    EsSimple M a c :=
  composite_simple_of_same_decomposition M hP hQ hR h1 h2

/-! ## 3. El Principio de Multiplicidad -/

/--
`PrincipioDeMultiplicidad b` : el objeto `b` tiene dos descomposiciones
distintas que NO están conectadas por ningún clúster.

Es la hipótesis que `complex_needs_unconnected` identifica como necesaria.
-/
def PrincipioDeMultiplicidad (b : O) : Prop :=
  ∃ Q Q' : Pat, M.binding Q = b ∧ M.binding Q' = b ∧
    Q ≠ Q' ∧ ¬ M.Cluster Q Q'

/--
**Teorema.** El Principio de Multiplicidad es equivalente a que exista un
objeto con descomposiciones no conectadas —por definición— y por
`complex_needs_unconnected` es condición necesaria de toda complejidad que
pase por ese objeto.

Se enuncia como teorema y no como comentario porque es lo que justifica que el
principio sea un AXIOMA del sistema y no una propiedad deseable.
-/
theorem multiplicidad_necesaria_para_complejidad {a b c : O}
    (hsinMP : ¬ PrincipioDeMultiplicidad M b) {P Q Q' R : Pat}
    (hQ : M.binding Q = b) (hQ' : M.binding Q' = b)
    (hP : M.binding P = a) (hR : M.binding R = c)
    (h1 : M.Cluster P Q) (h2 : M.Cluster Q' R)
    (hdistintas : Q ≠ Q') :
    EsSimple M a c := by
  by_contra hno
  exact hsinMP ⟨Q, Q', hQ, hQ', hdistintas,
                complex_needs_unconnected M hP hR h1 h2 hno⟩

end MetamathProver.EhresmannLinks
