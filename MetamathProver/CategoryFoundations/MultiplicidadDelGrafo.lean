-- MultiplicidadDelGrafo.lean: los pares del grafo donde Hom tiene mas de un elemento
import Mathlib.Tactic
import Mathlib.Data.ZMod.Basic
import Mathlib.Data.ZMod.Units
import Mathlib.Data.Matrix.Basic
import Mathlib.RingTheory.Spectrum.Prime.Basic

/-!
# Multiplicidad certificada, par a par

`MorfismosGrupoAnillo.lean` certifico un par. Este archivo agota los demas del
grafo donde la certificacion es posible: la arista **ya existe** y la matematica
da dos o mas construcciones que Lean puede separar por computo.

## El criterio de inclusion

No todo par admite esto, y conviene decir por que antes de empezar. Un par entra
si cumple las tres:

  1. la arista existe ya en el grafo — certificar no debe inventar dependencias;
  2. hay dos construcciones clasicas, de las que nombraria cualquiera del area;
  3. algun invariante finito las separa, y el kernel lo comprueba.

Los pares que no cumplen (3) quedan fuera aunque cumplan (1) y (2). Por ejemplo
`ring-theory → polynomial-rings`: `R[X]` es infinito incluso con `R` finito, y
el cardinal no separa nada. No es que no haya multiplicidad — es que no se
certifica asi.

## El separador no siempre es el cardinal

`group-theory → group-actions` es el caso interesante: las tres acciones de un
grupo sobre si mismo tienen el MISMO conjunto subyacente, luego el cardinal no
distingue. Las separa el numero de puntos fijos. Sirve cualquier invariante
computable; el cardinal es solo el mas barato.
-/

namespace MetamathProver.MultiplicidadDelGrafo

open scoped Matrix

/-- `ZMod 5` es cuerpo solo con este hecho a mano. -/
instance : Fact (Nat.Prime 5) := ⟨by norm_num⟩

/-! ## `ring-theory → field-theory`

«field-theory requiere ring-theory»: ¿que anillo produce un cuerpo?
-/

/-- El anillo subyacente. -/
abbrev anilloSubyacente (K : Type*) [Field K] := K

/-- El anillo de matrices 2x2. -/
abbrev anilloMatrices (K : Type*) [Field K] := Matrix (Fin 2) (Fin 2) K

/-- El anillo trivial. -/
abbrev anilloTrivial (K : Type*) [Field K] := Unit

theorem card_anillo_subyacente : Fintype.card (anilloSubyacente (ZMod 5)) = 5 := by decide

theorem card_anillo_matrices :
    Fintype.card (anilloMatrices (ZMod 5)) = 625 := by
  simp [anilloMatrices, Matrix, Fintype.card_fun]

theorem card_anillo_trivial : Fintype.card (anilloTrivial (ZMod 5)) = 1 := rfl

/-- **`ring-theory → field-theory` no es delgado.** -/
theorem ring_field_no_delgado :
    Fintype.card (anilloSubyacente (ZMod 5)) ≠ Fintype.card (anilloMatrices (ZMod 5)) ∧
    Fintype.card (anilloSubyacente (ZMod 5)) ≠ Fintype.card (anilloTrivial (ZMod 5)) := by
  rw [card_anillo_subyacente, card_anillo_matrices, card_anillo_trivial]
  exact ⟨by decide, by decide⟩

/-! ## `ring-theory → module-theory`

«module-theory requiere ring-theory»: ¿que modulo produce un anillo?
-/

/-- El anillo como modulo sobre si mismo. -/
abbrev moduloRegular (R : Type*) [Ring R] := R

/-- El modulo libre de rango 2. -/
abbrev moduloLibre2 (R : Type*) [Ring R] := Fin 2 → R

/-- El modulo cero. -/
abbrev moduloCero (R : Type*) [Ring R] := PUnit

theorem card_modulo_regular : Fintype.card (moduloRegular (ZMod 5)) = 5 := by decide

theorem card_modulo_libre2 : Fintype.card (moduloLibre2 (ZMod 5)) = 25 := by decide

theorem card_modulo_cero : Fintype.card (moduloCero (ZMod 5)) = 1 := rfl

/-- **`ring-theory → module-theory` no es delgado.** -/
theorem ring_module_no_delgado :
    Fintype.card (moduloRegular (ZMod 5)) ≠ Fintype.card (moduloLibre2 (ZMod 5)) ∧
    Fintype.card (moduloRegular (ZMod 5)) ≠ Fintype.card (moduloCero (ZMod 5)) := by
  rw [card_modulo_regular, card_modulo_libre2, card_modulo_cero]
  exact ⟨by decide, by decide⟩

/-! ## `field-extensions → finite-fields`

«finite-fields requiere field-extensions»: los cuerpos primos son
construcciones distintas, una por caracteristica.
-/

theorem card_cuerpo_2 : Fintype.card (ZMod 2) = 2 := by decide
theorem card_cuerpo_3 : Fintype.card (ZMod 3) = 3 := by decide
theorem card_cuerpo_5 : Fintype.card (ZMod 5) = 5 := by decide

/-- **`field-extensions → finite-fields` no es delgado.** -/
theorem ext_finitos_no_delgado :
    Fintype.card (ZMod 2) ≠ Fintype.card (ZMod 3) ∧
    Fintype.card (ZMod 3) ≠ Fintype.card (ZMod 5) := by
  rw [card_cuerpo_2, card_cuerpo_3, card_cuerpo_5]
  exact ⟨by decide, by decide⟩

/-! ## `group-theory → group-actions`

«group-actions requiere group-theory»: ¿que accion produce un grupo sobre si
mismo? Tres clasicas, y aqui el cardinal NO sirve — las tres actuan sobre el
mismo conjunto. Las separa el numero de PUNTOS FIJOS.

Con `G = ZMod 4` (grupo aditivo de cuatro elementos):

  · traslacion `g · x = g + x`  — 0 puntos fijos: ninguno queda quieto ante
                                   TODO el grupo;
  · trivial    `g · x = x`       — 4 puntos fijos, todos;
  · paridad    `g` par actua como identidad, `g` impar intercambia `0 ↔ 1`
                                 — 2 puntos fijos, `{2, 3}`.

La tercera es el homomorfismo `ZMod 4 → ZMod 2 → S₄`, y es una accion porque la
paridad es aditiva.

Que el separador no sea el cardinal es lo que hace este par instructivo: la
multiplicidad no siempre se ve por el tamaño del resultado. Y el primer intento
fue mal: se propuso `g · x = 2g + x` esperando 2 puntos fijos, y el kernel
respondio que son 0 — para ser fijo hace falta que TODO `g` deje quieto al
punto, y `g = 1` mueve todos.
-/

/-- Traslacion: `g · x = g + x`. -/
def actTraslacion (g x : ZMod 4) : ZMod 4 := g + x

/-- Accion trivial: `g · x = x`. -/
def actTrivial (_ x : ZMod 4) : ZMod 4 := x

/-- El intercambio `0 ↔ 1`, dejando `2` y `3` quietos. -/
def swap01 (x : ZMod 4) : ZMod 4 := if x = 0 then 1 else if x = 1 then 0 else x

/-- Accion por paridad: los `g` impares intercambian, los pares no hacen nada. -/
def actParidad (g x : ZMod 4) : ZMod 4 :=
  if g = 1 ∨ g = 3 then swap01 x else x

/-- Los puntos fijos de una accion: los que NINGUN elemento mueve. -/
def puntosFijos (act : ZMod 4 → ZMod 4 → ZMod 4) : Finset (ZMod 4) :=
  Finset.univ.filter (fun x => ∀ g : ZMod 4, act g x = x)

/-! Las tres son acciones: identidad y compatibilidad con la suma. -/

theorem actTraslacion_es_accion :
    (∀ x, actTraslacion 0 x = x) ∧
    (∀ g h x, actTraslacion g (actTraslacion h x) = actTraslacion (g + h) x) := by
  decide

theorem actTrivial_es_accion :
    (∀ x, actTrivial 0 x = x) ∧
    (∀ g h x, actTrivial g (actTrivial h x) = actTrivial (g + h) x) := by
  decide

theorem actParidad_es_accion :
    (∀ x, actParidad 0 x = x) ∧
    (∀ g h x, actParidad g (actParidad h x) = actParidad (g + h) x) := by
  decide

/-! Y las separa el numero de puntos fijos. -/

theorem fijos_traslacion : (puntosFijos actTraslacion).card = 0 := by decide
theorem fijos_trivial    : (puntosFijos actTrivial).card = 4 := by decide
theorem fijos_paridad    : (puntosFijos actParidad).card = 2 := by decide

/--
**`group-theory → group-actions` no es delgado**, y el cardinal del conjunto
subyacente no lo habria detectado: las tres acciones viven sobre los mismos
cuatro elementos.
-/
theorem group_actions_no_delgado :
    (puntosFijos actTraslacion).card ≠ (puntosFijos actTrivial).card ∧
    (puntosFijos actTraslacion).card ≠ (puntosFijos actParidad).card ∧
    (puntosFijos actTrivial).card ≠ (puntosFijos actParidad).card := by
  rw [fijos_traslacion, fijos_trivial, fijos_paridad]
  exact ⟨by decide, by decide, by decide⟩

/-- Y en efecto el conjunto subyacente es el mismo en las tres. -/
theorem mismo_conjunto_subyacente :
    Fintype.card (ZMod 4) = 4 := by decide

/-! ## `commutative-algebra → algebraic-geometry`

«algebraic-geometry requiere commutative-algebra»: ¿que espacio produce un
anillo conmutativo? Es el unico par de esta lista que **participa en los
colimites del grafo**, y por tanto el primero cuya multiplicidad puede cambiar
un resultado.

Dos construcciones, ambas funtores `CommRing → Top`:

  · el **espectro primo** `Spec R` con la topologia de Zariski — el puente de
    la geometria algebraica;
  · el **conjunto subyacente con la topologia discreta**.

Sobre `ZMod 5` se separan de la forma mas limpia posible: un cuerpo tiene un
unico ideal primo —el cero—, luego `Spec` es un punto; el discreto tiene cinco.

Uno colapsa toda la informacion a un punto y el otro no colapsa nada. Que sean
funtores distintos no es un tecnicismo: es la diferencia entre mirar un anillo
por sus ideales o por sus elementos.
-/

/-- El espectro primo con la topologia de Zariski. -/
abbrev espacioSpec (R : Type*) [CommRing R] := PrimeSpectrum R

/-- El conjunto subyacente, con la topologia discreta. -/
abbrev espacioDiscreto (R : Type*) [CommRing R] := R

/-- Un cuerpo tiene un unico ideal primo: `Spec` de un cuerpo es un punto. -/
theorem card_spec : Fintype.card (espacioSpec (ZMod 5)) = 1 :=
  Fintype.card_unique

theorem card_discreto : Fintype.card (espacioDiscreto (ZMod 5)) = 5 := by decide

/--
**`commutative-algebra → algebraic-geometry` no es delgado.**

Y a diferencia de los cinco pares anteriores, este SI participa en las
descomposiciones del grafo: `algebraic-geometry` es colimite de
`{commutative-algebra, functors}`.
-/
theorem comm_alg_geom_no_delgado :
    Fintype.card (espacioSpec (ZMod 5)) ≠ Fintype.card (espacioDiscreto (ZMod 5)) := by
  rw [card_spec, card_discreto]
  decide

end MetamathProver.MultiplicidadDelGrafo
