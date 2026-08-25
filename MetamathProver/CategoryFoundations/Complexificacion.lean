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

end MetamathProver.Complexificacion
