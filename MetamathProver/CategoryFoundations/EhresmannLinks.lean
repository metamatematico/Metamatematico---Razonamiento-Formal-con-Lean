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
import Mathlib.Data.Fintype.Basic
import Mathlib.Tactic.DeriveFintype

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


/-! ## 4. Un modelo concreto: los enlaces complejos existen -/

/-
Lo anterior dice bajo qué condición PUEDE haber complejidad. No dice que la
haya. Esta sección exhibe el modelo más pequeño en que la hay, y lo comprueba
por decisión exhaustiva.

    objetos    A ──simple──▶ B ──simple──▶ C
                             │
    patrones   P ─▶ Q        Q'─▶ R        Q ≠ Q',  ambos con binding B
                    ╰── sin clúster ──╯

`A → B` es simple porque el clúster `P → Q` lo induce. `B → C` es simple porque
lo induce `Q' → R`. Pero para que `A → C` fuera simple haría falta un clúster
entre una descomposición de A y una de C, es decir `P → R`, y no lo hay: el
camino pasaría por `Q → Q'`, que es justamente lo que falta.
-/

inductive Obj : Type
  | A | B | C
  deriving DecidableEq, Fintype

inductive Pat3 : Type
  | P | Q | Q' | R
  deriving DecidableEq, Fintype

namespace Modelo

/-- Q y Q' son dos descomposiciones DISTINTAS del mismo objeto B. -/
def bind : Pat3 → Obj
  | .P => .A
  | .Q => .B
  | .Q' => .B
  | .R => .C

/-- Los clústeres, como función booleana para poder decidir. -/
def clus : Pat3 → Pat3 → Bool
  | .P,  .P  => true | .P,  .Q => true
  | .Q,  .Q  => true
  | .Q', .Q' => true | .Q', .R => true
  | .R,  .R  => true
  | _,   _   => false

theorem clus_trans : ∀ p q r : Pat3, clus p q = true → clus q r = true →
    clus p r = true := by decide

theorem clus_refl : ∀ p : Pat3, clus p p = true := by decide

def Mod : MESData Obj Pat3 where
  binding := bind
  Cluster p q := clus p q = true
  cluster_comp {p q r} h1 h2 := clus_trans p q r h1 h2
  cluster_id := clus_refl

/-
Nota tecnica: `Mod.Cluster p q` es acceso a un campo de la estructura, y la
busqueda de instancias no lo reduce sola a `clus p q = true`. Por eso las
pruebas despliegan `Mod` explicitamente en vez de invocar `decide` a secas.
-/

/-- `A → B` es simple: lo induce el clúster `P → Q`. -/
theorem AB_simple : EsSimple Mod Obj.A Obj.B :=
  ⟨Pat3.P, Pat3.Q, rfl, rfl, rfl⟩

/-- `B → C` es simple: lo induce el clúster `Q' → R`. -/
theorem BC_simple : EsSimple Mod Obj.B Obj.C :=
  ⟨Pat3.Q', Pat3.R, rfl, rfl, rfl⟩

/--
**Teorema.** `A → C` NO es simple.

La única descomposición de `A` es `P` y la única de `C` es `R`, y no hay clúster
`P → R`. Se comprueban los 16 pares de patrones.
-/
theorem AC_no_simple : ¬ EsSimple Mod Obj.A Obj.C := by
  rintro ⟨p, r, hp, hr, hc⟩
  cases p <;> cases r <;> simp_all [Mod, bind, clus]

/--
**Teorema (existencia de enlaces complejos).**

Hay dos enlaces simples cuya composición no es simple. Es exactamente la
emergencia de Ehresmann, y existe.
-/
theorem enlaces_complejos_existen :
    EsSimple Mod Obj.A Obj.B ∧ EsSimple Mod Obj.B Obj.C ∧
    ¬ EsSimple Mod Obj.A Obj.C :=
  ⟨AB_simple, BC_simple, AC_no_simple⟩

/--
**Teorema.** Y el objeto intermedio cumple el Principio de Multiplicidad, tal
como `complex_needs_unconnected` exige.
-/
theorem B_cumple_MP : PrincipioDeMultiplicidad Mod Obj.B := by
  refine ⟨Pat3.Q, Pat3.Q', rfl, rfl, by decide, ?_⟩
  intro h
  simp [Mod, clus] at h

/-! ### El recíproco: añadir el clúster que falta elimina la complejidad -/

/--
El mismo modelo, pero con las dos descomposiciones de `B` conectadas y el
cierre transitivo.

Hacen falta AMBOS sentidos, `Q → Q'` y `Q' → Q`: con uno solo el par (Q', Q)
sigue sin conectar y el Principio de Multiplicidad se cumple igual. Lo detectó
Lean al dejar sin cerrar el caso `Q'.Q`.
-/
def clusConectado : Pat3 → Pat3 → Bool
  | .P,  .P  => true | .P,  .Q  => true | .P, .Q' => true | .P, .R => true
  | .Q,  .Q  => true | .Q,  .Q' => true | .Q, .R  => true
  | .Q', .Q  => true | .Q', .Q' => true | .Q', .R => true
  | .R,  .R  => true
  | _,   _   => false

theorem clusConectado_trans : ∀ p q r : Pat3,
    clusConectado p q = true → clusConectado q r = true →
    clusConectado p r = true := by decide

theorem clusConectado_refl : ∀ p : Pat3, clusConectado p p = true := by decide

def ModConectado : MESData Obj Pat3 where
  binding := bind
  Cluster p q := clusConectado p q = true
  cluster_comp {p q r} h1 h2 := clusConectado_trans p q r h1 h2
  cluster_id := clusConectado_refl

/--
**Teorema.** Con el clúster `Q → Q'` presente, `A → C` vuelve a ser simple.

Comprueba que la hipótesis de `complex_needs_unconnected` es la que hace el
trabajo, y no una condición accesoria: es lo único que cambia entre los dos
modelos.
-/
theorem sin_MP_no_hay_complejidad : EsSimple ModConectado Obj.A Obj.C :=
  ⟨Pat3.P, Pat3.R, rfl, rfl, rfl⟩

/-- Y en efecto ese modelo ya no cumple el Principio de Multiplicidad en `B`. -/
theorem ModConectado_no_cumple_MP_en_B :
    ¬ PrincipioDeMultiplicidad ModConectado Obj.B := by
  rintro ⟨q, q', hq, hq', hne, hnc⟩
  cases q <;> cases q' <;> simp_all [ModConectado, bind, clusConectado]

end Modelo


/-! ## 5. ¿Es alcanzable el Principio de Multiplicidad en un preorden? -/

/-
La pregunta importa porque el grafo de habilidades ES un preorden. Si en un
preorden MP fuera imposible, la discusión estaría cerrada: el sistema nunca
podría tener enlaces complejos, y no habría nada que decidir.

No es el caso. Esta sección lo demuestra construyendo el testigo.

En un preorden, un patrón es un conjunto finito de objetos y su colímite es el
join. Un clúster `S → T` es la condición de que toda componente de `S` tenga
alguna componente de `T` por encima:

    Conectados S T  :=  ∀ s ∈ S, ∃ t ∈ T, s ≤ t

Dos descomposiciones del mismo objeto pueden fallar esa condición, y entonces
MP se cumple.
-/

namespace EnPreorden

variable {P : Type u} [Preorder P] [DecidableEq P]

/-- Clúster entre patrones en un preorden: cada componente de `S` queda por
    debajo de alguna de `T`. -/
def Conectados (S T : Finset P) : Prop := ∀ s ∈ S, ∃ t ∈ T, s ≤ t

theorem conectados_refl (S : Finset P) : Conectados S S :=
  fun s hs => ⟨s, hs, le_refl s⟩

/--
**Teorema.** Añadir a un patrón cualquier objeto por debajo de su join da otro
patrón con el MISMO join.

Es la fuente natural de descomposiciones homólogas: todo patrón con colímite
genera muchas. Que el sistema no las encuentre es cosa del algoritmo de
descubrimiento, no de la estructura.
-/
theorem join_estable_al_añadir {S : Finset P} {j x : P}
    (hub : ∀ s ∈ S, s ≤ j) (hleast : ∀ k, (∀ s ∈ S, s ≤ k) → j ≤ k)
    (hx : x ≤ j) :
    (∀ s ∈ insert x S, s ≤ j) ∧
    (∀ k, (∀ s ∈ insert x S, s ≤ k) → j ≤ k) := by
  constructor
  · intro s hs
    rcases Finset.mem_insert.mp hs with rfl | h
    · exact hx
    · exact hub s h
  · intro k hk
    exact hleast k fun s hs => hk s (Finset.mem_insert_of_mem hs)

end EnPreorden

/-! ### Testigo: un preorden finito donde MP se cumple -/

inductive Pre : Type
  | a | b | c | d | j
  deriving DecidableEq, Fintype

namespace Testigo

/-- `a, b, c, d` son incomparables dos a dos; todos por debajo de `j`. -/
def le5 : Pre → Pre → Bool
  | .a, .a => true | .a, .j => true
  | .b, .b => true | .b, .j => true
  | .c, .c => true | .c, .j => true
  | .d, .d => true | .d, .j => true
  | .j, .j => true
  | _,  _  => false

instance : Preorder Pre where
  le x y := le5 x y = true
  le_refl x := by cases x <;> rfl
  le_trans x y z := by revert x y z; decide

instance : DecidableRel ((· ≤ ·) : Pre → Pre → Prop) :=
  fun x y => decidable_of_iff (le5 x y = true) Iff.rfl

/-- Dos descomposiciones distintas de `j`. -/
def S : Finset Pre := {Pre.a, Pre.b}
def T : Finset Pre := {Pre.c, Pre.d}

theorem S_ne_T : S ≠ T := by decide

/-- Ambas tienen a `j` por join: es cota superior y es la menor. -/
theorem S_join_j : (∀ s ∈ S, s ≤ Pre.j) ∧
    (∀ k, (∀ s ∈ S, s ≤ k) → Pre.j ≤ k) := by decide

theorem T_join_j : (∀ s ∈ T, s ≤ Pre.j) ∧
    (∀ k, (∀ s ∈ T, s ≤ k) → Pre.j ≤ k) := by decide

/--
**Teorema.** Y NO están conectadas por un clúster: `a` no queda por debajo de
`c` ni de `d`.
-/
theorem no_conectados : ¬ EnPreorden.Conectados S T := by
  -- `Conectados` cuantifica sobre un Finset y Lean no sintetiza su
  -- decidibilidad sola; basta con exhibir el testigo `a`.
  intro h
  obtain ⟨t, ht, hat⟩ := h Pre.a (by decide)
  have : t = Pre.c ∨ t = Pre.d := by simpa [T] using ht
  rcases this with rfl | rfl <;> exact absurd hat (by decide)

/--
**Teorema (MP es alcanzable en un preorden).**

`j` tiene dos descomposiciones distintas, ambas con `j` por join, no conectadas
por ningún clúster. Es exactamente el Principio de Multiplicidad, en un
preorden finito de cinco objetos.

Consecuencia para el sistema: que MP no se cumpla hoy NO es una limitación de
modelar el grafo como preorden. Es una propiedad del algoritmo que descubre los
patrones.
-/
theorem MP_alcanzable_en_preorden :
    S ≠ T ∧
    ((∀ s ∈ S, s ≤ Pre.j) ∧ (∀ k, (∀ s ∈ S, s ≤ k) → Pre.j ≤ k)) ∧
    ((∀ s ∈ T, s ≤ Pre.j) ∧ (∀ k, (∀ s ∈ T, s ≤ k) → Pre.j ≤ k)) ∧
    ¬ EnPreorden.Conectados S T :=
  ⟨S_ne_T, S_join_j, T_join_j, no_conectados⟩

end Testigo

end MetamathProver.EhresmannLinks
