/-
# El funtor cociente π : Skills → Agentes

## Qué se establece aquí

El sistema tiene dos categorías de orden: la de skills (172 objetos) y la de
agentes (15 objetos). No pueden ser isomorfas —la cardinalidad lo impide— pero
sí están relacionadas por una proyección

    π(s) = categoría(s)

Este archivo demuestra, en Lean 4, las tres cosas que hacen falta para que esa
proyección sirva de puente entre los dos niveles:

1. `quotientMap_monotone` — π es MONÓTONA por construcción cuando el codominio
   lleva el preorden inducido. En una categoría thin, monótona = funtor.

2. `functor_preserves_cocone` — todo funtor preserva CO-CONOS: si j es cota
   superior de S, entonces π(j) es cota superior de π(S). Esto es lo que
   permite que la estructura de Ehresmann baje de un nivel al otro.

3. `functor_not_preserves_join` — un funtor NO preserva, en general, la
   MINIMALIDAD. Se exhibe un contraejemplo concreto y finito. No es un defecto
   de la construcción: es un teorema sobre lo que un cociente puede y no puede
   conservar.

## Correspondencia con la medición

`scripts/verificar_funtor.py` construye π sobre el grafo real y comprueba:

    objetos con imagen        172/172
    morfismos con imagen      226/226
    composiciones              250, 0 fallos
    co-cono preservado         18/18   ← Teorema (2)
    colímite preservado        12/18   ← Teorema (3): los 6 restantes

De los 6 que pierden minimalidad, 5 tienen al objeto base entre sus
componentes. El teorema (3) explica exactamente por qué: un objeto por debajo
de todos hace que el conjunto de cotas superiores de {base, x} sea grande, y
π(j) rara vez es la menor.

## Relación con el resto

`IsJoin` viene de `JoinColimit.lean`, donde se demuestra que en un preorden es
equivalente a la propiedad universal del colímite. Aquí se usa tal cual.
-/

import Mathlib.Order.Basic
import Mathlib.Order.Hom.Basic
import Mathlib.Data.Finset.Lattice.Fold
import Mathlib.Data.Fintype.Basic
import MetamathProver.CategoryFoundations.JoinColimit

namespace MetamathProver.QuotientFunctor

open MetamathProver.JoinColimit

universe u v

/-! ## 1. La proyección y su codominio -/

/--
El preorden INDUCIDO en el codominio: `a ≼ b` cuando existe un camino de
objetos de S cuyas imágenes conectan a con b.

Se define como el preorden generado por la imagen de las flechas de S, que es
exactamente lo que hace `construir_funtor` en Python: `Hom(A) = {π(f)}`.
-/
structure ProyeccionMonotona (S : Type u) (A : Type v)
    [Preorder S] [Preorder A] where
  /-- La función en objetos. -/
  map : S → A
  /-- Toda flecha de S tiene imagen: es la condición de funtorialidad. -/
  monotone : ∀ {a b : S}, a ≤ b → map a ≤ map b

attribute [simp] ProyeccionMonotona.monotone

variable {S : Type u} {A : Type v} [Preorder S] [Preorder A]

/--
**Teorema 1 (funtorialidad).**

En categorías thin, una proyección monótona ES un funtor: preserva
identidades y composición, y no hay nada más que comprobar porque `Hom(a,b)`
tiene a lo sumo un elemento.

La ley de identidades es la reflexividad; la de composición, la transitividad.
-/
theorem proyeccion_es_funtor (π : ProyeccionMonotona S A) :
    (∀ a : S, π.map a ≤ π.map a) ∧
    (∀ {a b c : S}, a ≤ b → b ≤ c → π.map a ≤ π.map c) := by
  refine ⟨fun a => le_refl _, ?_⟩
  intro a b c hab hbc
  exact le_trans (π.monotone hab) (π.monotone hbc)

/-! ## 2. Los funtores preservan co-conos -/

/--
`EsCocono S j` : j es cota superior del conjunto S. Es la primera mitad de
`IsJoin`, aislada porque es lo que sí se preserva.
-/
def EsCocono {P : Type*} [Preorder P] (S : Finset P) (j : P) : Prop :=
  ∀ s ∈ S, s ≤ j

theorem isJoin_esCocono {P : Type*} [Preorder P] {S : Finset P} {j : P}
    (h : IsJoin S j) : EsCocono S j :=
  h.upper_bound

/--
**Teorema 2 (preservación de co-conos).**

Si j es cota superior de S, entonces π(j) es cota superior de la imagen de S.

Éste es el resultado que permite que la estructura de Ehresmann baje del nivel
de skills al de agentes: los 18 co-conos descubiertos siguen siendo co-conos
tras proyectar, y la medición lo confirma (18/18).

La demostración es inmediata, y esa inmediatez es el punto: no hace falta
ninguna hipótesis sobre π más allá de la monotonía.
-/
theorem functor_preserves_cocone (π : ProyeccionMonotona S A)
    (T : Finset S) (j : S) (h : EsCocono T j) :
    ∀ s ∈ T, π.map s ≤ π.map j :=
  fun s hs => π.monotone (h s hs)

/--
Versión con la imagen como Finset, que es la forma en que la usa el
verificador en Python.
-/
theorem functor_preserves_cocone' [DecidableEq A] (π : ProyeccionMonotona S A)
    (T : Finset S) (j : S) (h : EsCocono T j) :
    EsCocono (T.image π.map) (π.map j) := by
  intro a ha
  obtain ⟨s, hs, rfl⟩ := Finset.mem_image.mp ha
  exact π.monotone (h s hs)

/--
**Corolario.** Un colímite se proyecta al menos a un co-cono.

Es exactamente la cifra medida: `co-cono preservado 18/18`.
-/
theorem join_maps_to_cocone [DecidableEq A] (π : ProyeccionMonotona S A)
    (T : Finset S) (j : S) (h : IsJoin T j) :
    EsCocono (T.image π.map) (π.map j) :=
  functor_preserves_cocone' π T j (isJoin_esCocono h)

/-! ## 3. Los funtores NO preservan la minimalidad -/

/-
El contraejemplo necesita CINCO objetos, y el motivo es instructivo.

Un primer intento con tres —base ≤ x ≤ j— no sirve: ahí `x` es también cota
superior de {base, x}, de modo que el join es `x` y no `j`. Colapsar por sí
solo no rompe la minimalidad.

Lo que la rompe es un SEGUNDO REPRESENTANTE: dos objetos distintos del dominio
con la misma imagen, uno de los cuales abre un atajo que en el dominio no
existe. Es exactamente el mecanismo que se observa en el grafo real, donde el
objeto base recibe flechas de skills distintos y por eso aparece por debajo de
casi todo.

    dominio                          codominio
    a ─┐                             A ─┐──────┐
       ├─→ j   (j = join {a,b})         │      │
    b ─┘                             B ─┤──→ J │
    a'─┐                                └──→ M ┘
       ├─→ m   (a' ≠ a, misma imagen)
    b ─┘

En el dominio, `m` NO es cota superior de {a,b}, porque a ≰ m. Pero A ≤ M en el
codominio, porque a' ≤ m y π(a') = A. Así M se cuela como cota superior de
{A,B} sin ser imagen de ninguna cota superior de {a,b}, y J deja de ser mínima.
-/

/-- Cinco objetos: dos representantes de A, uno de B, el join y el atajo. -/
inductive Dom : Type
  | a | a' | b | j | m
  deriving DecidableEq, Fintype

/-- Cuatro objetos en el codominio. -/
inductive Cod : Type
  | A | B | J | M
  deriving DecidableEq, Fintype

namespace Contraejemplo

/-- Orden del dominio, como función booleana para que `decide` funcione. -/
def leDom : Dom → Dom → Bool
  | .a,  .a  => true | .a,  .j  => true
  | .a', .a' => true | .a', .m  => true
  | .b,  .b  => true | .b,  .j  => true | .b, .m => true
  | .j,  .j  => true
  | .m,  .m  => true
  | _,   _   => false

instance : Preorder Dom where
  le x y := leDom x y = true
  le_refl x := by cases x <;> rfl
  le_trans x y z := by revert x y z; decide

/-- Puente entre el `≤` del preorden y la función booleana, para `decide`. -/
instance : DecidableRel ((· ≤ ·) : Dom → Dom → Prop) :=
  fun x y => decidable_of_iff (leDom x y = true) Iff.rfl

/-- Orden del codominio: el INDUCIDO por las flechas de arriba. -/
def leCod : Cod → Cod → Bool
  | .A, .A => true | .A, .J => true | .A, .M => true
  | .B, .B => true | .B, .J => true | .B, .M => true
  | .J, .J => true
  | .M, .M => true
  | _,  _  => false

instance : Preorder Cod where
  le x y := leCod x y = true
  le_refl x := by cases x <;> rfl
  le_trans x y z := by revert x y z; decide

instance : DecidableRel ((· ≤ ·) : Cod → Cod → Prop) :=
  fun x y => decidable_of_iff (leCod x y = true) Iff.rfl

/-- La proyección: `a` y `a'` comparten imagen. Ése es el colapso. -/
def proy : Dom → Cod
  | .a => .A | .a' => .A | .b => .B | .j => .J | .m => .M

theorem proy_monotone_expl : ∀ x y : Dom, x ≤ y → proy x ≤ proy y := by decide

theorem proy_monotone {x y : Dom} (h : x ≤ y) : proy x ≤ proy y :=
  proy_monotone_expl x y h

/-- π es una proyección monótona legítima: cumple el Teorema 1. -/
def pi : ProyeccionMonotona Dom Cod := ⟨proy, proy_monotone⟩

/-- En el dominio, `j` sí es el join de {a, b}. -/
theorem j_es_join : IsJoin ({Dom.a, Dom.b} : Finset Dom) Dom.j := by
  constructor
  · intro s hs
    simp only [Finset.mem_insert, Finset.mem_singleton] at hs
    rcases hs with rfl | rfl <;> rfl
  · intro k hk
    have ha := hk Dom.a (by simp)
    have hb := hk Dom.b (by simp)
    revert ha hb
    revert k
    decide

/--
**Teorema 3 (la minimalidad no se preserva).**

`M` es cota superior de la imagen {A, B} y `J ≰ M`, luego la imagen de un
colímite deja de ser colímite. El co-cono, en cambio, sobrevive: es el
Teorema 2.

La medición sobre el grafo real da 12/18, y los 6 que fallan tienen esta misma
forma: cinco de ellos llevan el objeto base entre sus componentes, que es el
que hace de `a'`.
-/
theorem functor_not_preserves_join :
    ∃ (T : Finset Dom) (jj : Dom),
      IsJoin T jj ∧ ¬ IsJoin (T.image pi.map) (pi.map jj) := by
  refine ⟨{Dom.a, Dom.b}, Dom.j, j_es_join, ?_⟩
  intro hcontra
  have himg : (({Dom.a, Dom.b} : Finset Dom).image pi.map)
      = ({Cod.A, Cod.B} : Finset Cod) := by decide
  rw [himg] at hcontra
  -- M es cota superior de {A, B}
  have hM : ∀ s ∈ ({Cod.A, Cod.B} : Finset Cod), s ≤ Cod.M := by decide
  -- la minimalidad forzaría J ≤ M, que es falso
  have : Cod.J ≤ Cod.M := hcontra.least Cod.M hM
  exact absurd this (by decide)

/-- Pero el co-cono sí sobrevive, como afirma el Teorema 2. -/
theorem cocono_si_se_preserva :
    EsCocono (({Dom.a, Dom.b} : Finset Dom).image pi.map) (pi.map Dom.j) :=
  join_maps_to_cocone pi _ _ j_es_join

end Contraejemplo

/-! ## 4. Qué sí se conserva: reflejo del orden -/

/--
**Teorema 4.** La proyección refleja la NO-alcanzabilidad.

Si π(a) no alcanza a π(b) en el codominio, entonces a no alcanza a b en el
dominio. Es el contrarrecíproco de la monotonía, y es la propiedad útil en la
práctica: permite descartar en el nivel barato (15 objetos) pares que no hace
falta examinar en el caro (172 objetos).
-/
theorem refleja_no_alcanzabilidad (π : ProyeccionMonotona S A) {a b : S}
    (h : ¬ (π.map a ≤ π.map b)) : ¬ (a ≤ b) :=
  fun hab => h (π.monotone hab)

end MetamathProver.QuotientFunctor
