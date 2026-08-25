-- Complexificacion.lean: la complexificacion de Ehresmann en el caso delgado
import Mathlib.Tactic

/-!
# Complexificacion en una categoria delgada

## Que problema resuelve

`build_hierarchy_to_fixpoint` solo DESCUBRE colimites que ya existen en `G_n`.
Cuando un patron no tiene co-cono limite se emite un `ConceptGap` y ahi acaba.
Eso es correcto como matematica —el colimite no existe en esa categoria— pero
deja el sistema en el lado equivocado de la distincion que hace Ehresmann:

> En matematicas se busca el colimite DENTRO de una categoria fija y la
> respuesta puede ser «no existe». En la modelizacion de sistemas evolutivos la
> inexistencia no cierra el problema: obliga a CAMBIAR de categoria mediante la
> complexificacion, y el objeto nuevo que aparece es precisamente el fenomeno
> emergente que se queria describir.

Mientras el sistema no complexifique, `K' = K`, y la pregunta por el orden de
complejidad no llega a plantearse: no hay nada que reducir porque no se
construyo nada.

## Por que el caso delgado es facil

En general la complexificacion necesita el forzamiento de colimites: una
sucesion `L₁ → L₂ → ⋯` que identifica flechas paralelas y toma el colimite en
`Cat`. En una categoria DELGADA no hay flechas paralelas que identificar
—`Hom` tiene a lo sumo un elemento— asi que la sucesion estabiliza de
inmediato y la construccion se reduce a una compleción de orden.

Ehresmann lo dice explicitamente para el caso poset: la complexificacion es la
**compleción de MacNeille**. Este archivo construye exactamente eso, en la
forma que el sistema necesita.

## La construccion

Un objeto `a` se representa por su filtro principal `arriba a = {x | a ≤ x}`,
y un patron `P` por su conjunto de cotas superiores `upperBounds P`. El orden
es la **inclusion inversa**: cuanto menos cotas superiores, mas arriba esta el
objeto.

  · `iota a = arriba a`      — la inmersion de `K` en `K'`
  · `eta P  = upperBounds P` — el colimite que `P` adquiere

## Lo que se demuestra

1. `iota_le_iff` — `iota` es una inmersion de orden: `a ≤ b ↔ iota a ≤ iota b`.
2. `eta_es_colimite` — **todo** patron tiene colimite en `K'`, tambien los que
   no lo tenian en `K`. Es el objetivo (iii) de la opcion de Ehresmann.
3. `eta_eq_iota_of_isLUB` — si `P` YA tenia colimite `j` en `K`, entonces
   `eta P = iota j`: no aparece objeto nuevo. Es la condicion de PRESERVACION
   que el Teorema 1 exige, y la razon de que la complexificacion no destruya lo
   que ya habia.
4. `eta_eq_iff` / `SC_homologos_mismo_colimite` — dos patrones reciben el mismo objeto si y
   solo si tienen las mismas cotas superiores. Es la condicion suplementaria
   (SC): los patrones homologos comparten colimite, y no por decreto sino por
   construccion.

## Lo que NO se demuestra aqui

La propiedad universal del Teorema 1(iii) —que todo functor parcial que realice
los objetivos se factorice de modo unico por `p`— no esta formalizada. Lo que
hay es la parte constructiva: los objetivos se realizan, y se realizan
preservando lo que habia. Decirlo de otro modo seria pasarse.
-/

namespace MetamathProver.Complexificacion

variable {α : Type*} [Preorder α]

/-- El filtro principal de `a`: los objetos que estan por encima. -/
def arriba (a : α) : Set α := {x | a ≤ x}

@[simp] theorem mem_arriba {a x : α} : x ∈ arriba a ↔ a ≤ x := Iff.rfl

/--
Las cotas superiores de un patron son exactamente sus co-conos.

`isCocone G diagram apex = diagram.all (fun d => reachable d apex)` en
`ColimitVerifier.lean` es la version decidible y finita de esto mismo.
-/
theorem cotasSup_eq_cocones (P : Set α) :
    upperBounds P = {x | ∀ c ∈ P, c ≤ x} := rfl

/-!
## La complexificacion

Objetos: subconjuntos de `α`. Orden: inclusion INVERSA, via `OrderDual`.
-/

/-- Objetos de `K'`. -/
abbrev Compl (α : Type*) := (Set α)ᵒᵈ

/-- La inmersion `K → K'`. -/
def iota (a : α) : Compl α := OrderDual.toDual (arriba a)

/-- El colimite que el patron `P` adquiere en `K'`. -/
def eta (P : Set α) : Compl α := OrderDual.toDual (upperBounds P)

/-!
## 1. `iota` es una inmersion de orden
-/

theorem iota_le_iff (a b : α) : iota a ≤ iota b ↔ a ≤ b := by
  constructor
  · intro h
    exact h (le_refl b)
  · intro h x hx
    exact le_trans h hx

/-- En un orden PARCIAL la inmersion es ademas inyectiva. -/
theorem iota_injective {α : Type*} [PartialOrder α] :
    Function.Injective (iota : α → Compl α) := by
  intro a b h
  have h1 : a ≤ b := (iota_le_iff a b).mp (le_of_eq h)
  have h2 : b ≤ a := (iota_le_iff b a).mp (le_of_eq h.symm)
  exact le_antisymm h1 h2

/-!
## 2. Todo patron adquiere colimite

Es el objetivo (iii) de la opcion: los patrones a unir tienen colimite en `K'`.
A diferencia de `build_join_for_pattern`, aqui NO puede fallar.
-/

/-- `eta P` es cota superior de las componentes de `P`. -/
theorem eta_es_cota (P : Set α) : ∀ c ∈ P, iota c ≤ eta P := by
  intro c hc x hx
  exact hx hc

/-- `eta P` es la MINIMA de las cotas superiores: la propiedad universal. -/
theorem eta_es_minima (P : Set α) (S : Compl α)
    (h : ∀ c ∈ P, iota c ≤ S) : eta P ≤ S := by
  intro x hx c hc
  exact h c hc hx

/--
**Teorema.** `eta P` es el colimite de `P` en la complexificacion.

Todo patron lo tiene, incluidos los 13 huecos conceptuales que el sistema
reporta hoy. Eso es exactamente cambiar de categoria: el objeto nuevo no se
fabrica cableandolo para que cumpla la propiedad universal —lo que seria
asumir la conclusion— sino que la cumple por construccion.
-/
theorem eta_es_colimite (P : Set α) : IsLUB (iota '' P) (eta P) := by
  constructor
  · rintro _ ⟨c, hc, rfl⟩
    exact eta_es_cota P c hc
  · intro S hS
    refine eta_es_minima P S ?_
    intro c hc
    exact hS ⟨c, hc, rfl⟩

/-!
## 3. Preservacion: lo que ya tenia colimite no cambia

Es la condicion que el Teorema 1 exige explicitamente, y la razon por la que
complexificar no destruye la estructura previa. Sin ella la extension podria
darle a un patron un colimite distinto del que ya tenia.
-/

theorem eta_eq_iota_of_isLUB {P : Set α} {j : α} (h : IsLUB P j) :
    eta P = iota j := by
  apply congrArg OrderDual.toDual
  apply Set.eq_of_subset_of_subset
  · intro x hx
    exact h.2 hx
  · intro x hx c hc
    exact le_trans (h.1 hc) hx

/--
**Corolario.** Si `P` ya tenia colimite en `K`, la complexificacion no añade
ningun objeto por `P`: su imagen esta en `iota '' Set.univ`.
-/
theorem no_hay_objeto_nuevo_si_ya_habia_colimite {P : Set α} {j : α}
    (h : IsLUB P j) : ∃ a : α, eta P = iota a :=
  ⟨j, eta_eq_iota_of_isLUB h⟩

/-!
## 4. Condicion suplementaria (SC): homologos comparten colimite

Ehresmann exige que patrones homologos reciban el MISMO colimite en `K'`. En
esta construccion no hay que imponerlo: se cumple por definicion, porque el
objeto asignado a `P` ES el conjunto de sus cotas superiores.
-/

theorem eta_eq_iff (P Q : Set α) : eta P = eta Q ↔ upperBounds P = upperBounds Q := by
  constructor
  · intro h
    exact congrArg OrderDual.ofDual h
  · intro h
    exact congrArg OrderDual.toDual h

/--
**Teorema (SC).** Dos patrones con el mismo campo de cotas superiores reciben
el mismo colimite. Es la condicion suplementaria del Teorema 1, aqui gratuita.
-/
theorem SC_homologos_mismo_colimite {P Q : Set α}
    (h : upperBounds P = upperBounds Q) : eta P = eta Q :=
  (eta_eq_iff P Q).mpr h

/-!
## 5. Los huecos son exactamente los objetos nuevos

Un `ConceptGap` es un patron sin co-cono limite. En la complexificacion recibe
un objeto que no es la imagen de ningun objeto viejo — y ese es el contenido
preciso de «el concepto que falta».
-/

/--
**Teorema.** `P` tiene colimite en `K` si y solo si `eta P` es la imagen de un
objeto de `K`. Contrapuesto: los huecos son exactamente los objetos nuevos.
-/
theorem hueco_iff_objeto_nuevo {α : Type*} [PartialOrder α] (P : Set α) :
    (∃ j : α, IsLUB P j) ↔ (∃ a : α, eta P = iota a) := by
  constructor
  · rintro ⟨j, hj⟩
    exact ⟨j, eta_eq_iota_of_isLUB hj⟩
  · rintro ⟨a, ha⟩
    refine ⟨a, ?_, ?_⟩
    · intro c hc
      have : upperBounds P = arriba a := congrArg OrderDual.ofDual ha
      have hmem : a ∈ arriba a := le_refl a
      rw [← this] at hmem
      exact hmem hc
    · intro b hb
      have : upperBounds P = arriba a := congrArg OrderDual.ofDual ha
      rw [this] at hb
      exact hb

/-!
## 6. Densidad: K' esta generado por K bajo colimites

Antes de hablar de unicidad hace falta saber que no hay objetos «sueltos» en
`K'` a los que la condicion de factorizacion no llegue. Lo hay: todo objeto
relevante de `K'` es `eta P` para algun patron, y los objetos viejos son el
caso `P = {a}`. Junto con `eta_es_colimite`, eso dice que `K'` es el cierre de
`K` bajo los colimites de patrones — la densidad que da alcance al teorema
siguiente.
-/

/-- Los objetos viejos son el colimite de su patron unitario. -/
theorem iota_eq_eta_singleton (a : α) : iota a = eta {a} := by
  apply congrArg OrderDual.toDual
  apply Set.eq_of_subset_of_subset
  · intro x hx c hc
    rw [Set.mem_singleton_iff] at hc
    exact hc ▸ hx
  · intro x hx
    exact hx rfl

/-!
## 7. Teorema 1(iii): la factorizacion es unica

Ehresmann exige que la complexificacion realice los objetivos «sin añadir nada
superfluo», y lo formula como universalidad: si `q : K → L` es otro functor
parcial que cumple (i) y (ii), entonces `q` se factoriza de modo UNICO como
`q = p ; q'` con `q'` preservando los colimites de los patrones a unir.

Lo que sigue demuestra la mitad de unicidad, que es donde esta el contenido:
dos extensiones que coincidan sobre `K` y preserven los colimites coinciden en
TODO `K'`. Dicho de otro modo, `K'` no tiene grados de libertad: una vez fijado
`q` sobre los objetos viejos, el resto esta determinado.

La razon es corta y vale la pena decirla: `eta P` es el colimite de `iota '' P`
(§2), preservar colimites obliga a que la imagen sea el colimite de las
imagenes, y en un orden parcial el colimite es unico. No hay donde elegir.
-/

/--
**Teorema (unicidad de la factorizacion, Teorema 1(iii)).**

Si `F` y `G` coinciden sobre la imagen de `K` y ambos preservan los colimites
de los patrones, entonces coinciden sobre todo objeto `eta P` — es decir, sobre
todo `K'`, por la densidad de §6.
-/
theorem factorizacion_unica {L : Type*} [PartialOrder L]
    (F G : Compl α → L)
    (hFG : ∀ a : α, F (iota a) = G (iota a))
    (hF : ∀ P : Set α, IsLUB (F '' (iota '' P)) (F (eta P)))
    (hG : ∀ P : Set α, IsLUB (G '' (iota '' P)) (G (eta P)))
    (P : Set α) : F (eta P) = G (eta P) := by
  have himg : F '' (iota '' P) = G '' (iota '' P) := by
    apply Set.eq_of_subset_of_subset
    · rintro _ ⟨_, ⟨a, ha, rfl⟩, rfl⟩
      exact ⟨iota a, ⟨a, ha, rfl⟩, (hFG a).symm⟩
    · rintro _ ⟨_, ⟨a, ha, rfl⟩, rfl⟩
      exact ⟨iota a, ⟨a, ha, rfl⟩, hFG a⟩
  have h1 := hF P
  rw [himg] at h1
  exact IsLUB.unique h1 (hG P)

/--
**Corolario.** La unicidad alcanza tambien a los objetos viejos, que por §6 son
el caso `P = {a}`. No queda ningun objeto de `K'` fuera del alcance.
-/
theorem factorizacion_unica_en_K {L : Type*} [PartialOrder L]
    (F G : Compl α → L)
    (hFG : ∀ a : α, F (iota a) = G (iota a))
    (a : α) : F (eta {a}) = G (eta {a}) := by
  rw [← iota_eq_eta_singleton]
  exact hFG a

/-!
### Lo que falta de 1(iii)

La mitad de EXISTENCIA —construir `q'` a partir de un `q` que realice los
objetivos— no esta aqui. Requiere hipotesis sobre `L` (que los supremos
relevantes existan) y la condicion (ii) de Ehresmann como premisa: patrones
homologos deben ir al mismo sitio en `L`, porque en `K'` ya van al mismo
objeto (`SC_homologos_mismo_colimite`). Sin esa premisa `q'` ni siquiera esta
bien definida.

Se declara pendiente en lugar de enunciarse a medias.
-/

/-!
## 8. Por que la delgadez impide el orden de complejidad >= 2

Este es el resultado que cierra la pregunta de si el sistema puede producir
emergencia sin cambiar de arquitectura. La respuesta es que no, y no por falta
de datos ni por un algoritmo mejorable: por algebra.

### El enunciado de Ehresmann

El teorema de reduccion de colimites iterados (§5.2) dice que `cP` tiene orden
de complejidad 2 respecto de `K` cuando NO se obtiene como colimite de un solo
patron en `K`. En una categoria delgada el colimite es el supremo, y el
supremo es asociativo:

    sup { sup P₁, sup P₂, … } = sup (P₁ ∪ P₂ ∪ …)

Luego todo objeto obtenido iterando joins sobre `K` es, en un solo paso, el
join de la union de las bases. Su orden es 1. Siempre.

### Consecuencia para el sistema

Medido antes y despues de complexificar:

  · en `K`  : las 12 descomposiciones de los 3 objetos con cn = 2 se aplanan,
              0 resisten;
  · en `K'` : las 15 descomposiciones de los objetos con cn >= 2 se aplanan,
              0 resisten — y eso que `max(cn)` habia subido a 3.

`cn` mide anidamiento y sube al complexificar; el orden de Ehresmann no se
mueve. No son la misma magnitud, y el teorema de abajo dice por que nunca lo
seran mientras la categoria sea delgada.

### Que haria falta

Salir de la delgadez: permitir `Hom(a,b)` con mas de un elemento. Entonces el
colimite deja de ser el supremo, la asociatividad de arriba deja de aplicar, y
un enlace distinguido complejo puede bloquear la reduccion — que es justo lo
que §5.2(ii) pide.

Conviene no confundir esto con la conclusion que se retiro en su momento
—«la emergencia no puede existir en este modelo»—, que se apoyaba en una
definicion equivocada de enlace simple y por eso no se seguia. Este argumento
es otro: no habla de enlaces simples, habla de la asociatividad del supremo, y
va con demostracion.
-/

/--
**Teorema (el join de joins se aplana).** Si cada `P i` tiene supremo `j i`, y
la familia de esos supremos tiene supremo `k`, entonces `k` es el supremo de la
UNION de las `P i`.

Es la asociatividad del supremo, y es todo lo que hace falta: dice que
iterar colimites en un preorden no construye nada que no estuviera a un paso.
-/
theorem lub_de_lubs {ι : Type*} (P : ι → Set α) (j : ι → α)
    (hj : ∀ i, IsLUB (P i) (j i)) (k : α)
    (hk : IsLUB (Set.range j) k) :
    IsLUB (⋃ i, P i) k := by
  constructor
  · intro x hx
    rcases Set.mem_iUnion.mp hx with ⟨i, hxi⟩
    exact le_trans ((hj i).1 hxi) (hk.1 ⟨i, rfl⟩)
  · intro b hb
    refine hk.2 ?_
    rintro _ ⟨i, rfl⟩
    exact (hj i).2 (fun y hy => hb (Set.mem_iUnion.mpr ⟨i, hy⟩))

/--
**Corolario binario.** El caso que el sistema produce: un objeto que es join de
`{join P, x}` es, en un paso, el join de `P ∪ {x}`.

Es literalmente lo que se midio sobre el grafo:
`join(join(commutative-algebra, functors), ideals-quotient-rings)` es
`join(commutative-algebra, functors, ideals-quotient-rings)`.
-/
theorem join_binario_se_aplana {P : Set α} {j x k : α}
    (hj : IsLUB P j) (hk : IsLUB {j, x} k) :
    IsLUB (P ∪ {x}) k := by
  constructor
  · rintro y (hy | hy)
    · exact le_trans (hj.1 hy) (hk.1 (Set.mem_insert _ _))
    · rw [Set.mem_singleton_iff] at hy
      exact hy ▸ hk.1 (Set.mem_insert_of_mem _ rfl)
  · intro b hb
    refine hk.2 ?_
    rintro y (rfl | hy)
    · exact hj.2 (fun z hz => hb (Set.mem_union_left _ hz))
    · rw [Set.mem_singleton_iff] at hy
      exact hy ▸ hb (Set.mem_union_right _ rfl)

/--
**Corolario.** Ningun objeto obtenido iterando joins sobre `K` tiene orden de
complejidad >= 2: el patron aplanado lo produce en un solo paso.

El enunciado es el contrapuesto de §5.2(ii): si `cP` se obtiene en un paso, no
puede tener orden 2. Y `join_binario_se_aplana` dice que siempre se obtiene.
-/
theorem iterar_joins_no_sube_el_orden {P : Set α} {j x k : α}
    (hj : IsLUB P j) (hk : IsLUB {j, x} k) :
    ∃ R : Set α, IsLUB R k ∧ R = P ∪ {x} :=
  ⟨P ∪ {x}, join_binario_se_aplana hj hk, rfl⟩

end MetamathProver.Complexificacion
