/-
# La fibración π : Skills → Áreas

## Qué se establece aquí, y por qué no basta con que π sea funtor

`QuotientFunctor.lean` demuestra que π es monótona, o sea funtor entre
categorías thin. Eso dice que la proyección está BIEN DEFINIDA, pero no dice
nada sobre si la base sirve para algo: un funtor que manda todo a un punto es
perfectamente funtorial y no informa de nada.

Lo que hace falta para el supergrafo es más fuerte. Si en la base vale
`b' ≼ b` —«el álgebra conmutativa alimenta a la geometría algebraica»— eso
tiene que poder LEVANTARSE al total: dado un skill `e` de geometría algebraica,
tiene que existir el skill de álgebra conmutativa que lo sostiene, y tiene que
ser EL que lo sostiene, no uno cualquiera. Esa es la condición de fibración, y
es la que convierte una etiqueta de área en una estructura utilizable.

## Las cuatro cosas que se demuestran

1. `cartesiano_unico` — el levantamiento cartesiano es único salvo
   equivalencia. En un preorden eso es lo mejor que se puede pedir, y es
   suficiente: lo que se usa de él no distingue elementos equivalentes.

2. `reindexado_monotono` — EL PAGO. En una fibración, cada flecha `b' ≼ b` de
   la base induce una aplicación MONÓTONA `fibra(b) → fibra(b')`. Es decir:
   una fibración da, gratis, la manera de trasladar una pregunta de un área a
   otra conservando el orden. Sin la condición de fibración no existe esa
   aplicación, y «unificar los mundos con un funtor» se queda en la etiqueta.

3. `reindexado_compuesto` — trasladar de `b` a `b'` y luego a `b''` da lo
   mismo que trasladar de `b` a `b''` directamente. Es lo que autoriza a
   encadenar restricciones de área sin que el resultado dependa del camino.

4. `no_toda_monotona_es_fibracion` — un contraejemplo finito y concreto. Sin
   él, los tres teoremas de arriba serían enunciados sobre el conjunto vacío
   de casos interesantes: hay que saber que la condición PUEDE fallar para
   que comprobarla sobre el grafo real signifique algo.

## Correspondencia con la medición

`nucleo/graph/fibracion.py` comprueba la hipótesis de (2) y (3) sobre el grafo
real, y `scripts/fibracion_del_grafo.py` publica el número contra un modelo
nulo. Un teorema cuyas hipótesis el grafo no cumple no respalda nada, así que
el número es parte del enunciado, no un adorno.

## Relación con el resto

El preorden y la noción de thin vienen de `JoinColimit.lean`; π y su
monotonía, de `QuotientFunctor.lean`. Aquí sólo se le pide una condición más.
-/

import Mathlib.Order.Basic
import Mathlib.Data.Fin.Basic
import MetamathProver.CategoryFoundations.QuotientFunctor

namespace MetamathProver.Fibracion

open MetamathProver.QuotientFunctor

universe u v

variable {S : Type u} {A : Type v} [Preorder S] [Preorder A]

/-! ## 1. Levantamiento cartesiano -/

/--
`e'` es un levantamiento cartesiano de `e` a lo largo de `b' ≼ π e`.

Las tres condiciones dicen, en orden: `e'` vive en la fibra de `b'`; está por
debajo de `e`; y es EL MAYOR de los que cumplen las dos cosas. La tercera es
la que hace «cartesiano» y no simplemente «alguno»: sin ella cualquier objeto
suelto de la fibra serviría, y la construcción no elegiría nada.
-/
structure EsCartesiano (p : ProyeccionMonotona S A) (e e' : S) (b' : A) :
    Prop where
  /-- `e'` está en la fibra de `b'`. -/
  sobre : p.map e' = b'
  /-- `e'` está por debajo de `e`, que es la flecha que se levanta. -/
  debajo : e' ≤ e
  /-- Y es el mayor con esa propiedad: todo otro candidato pasa por él. -/
  universal : ∀ x : S, x ≤ e → p.map x ≤ b' → x ≤ e'

/--
π es una FIBRACIÓN cuando toda flecha de la base se levanta a todo objeto que
esté encima de su destino.
-/
def EsFibracion (p : ProyeccionMonotona S A) : Prop :=
  ∀ (e : S) (b' : A), b' ≤ p.map e → ∃ e', EsCartesiano p e e' b'

/-! ## 2. Unicidad -/

/--
Dos levantamientos cartesianos de la misma flecha en el mismo objeto son
equivalentes en el preorden.

En un preorden no se puede pedir igualdad —`≤` en las dos direcciones no la
implica—, y tampoco hace falta: todo lo que se usa del levantamiento está
enunciado con `≤`, y por tanto no distingue equivalentes.
-/
theorem cartesiano_unico {p : ProyeccionMonotona S A} {e e₁ e₂ : S} {b' : A}
    (h₁ : EsCartesiano p e e₁ b') (h₂ : EsCartesiano p e e₂ b') :
    e₁ ≤ e₂ ∧ e₂ ≤ e₁ := by
  refine ⟨h₂.universal e₁ h₁.debajo ?_, h₁.universal e₂ h₂.debajo ?_⟩
  · exact le_of_eq h₁.sobre
  · exact le_of_eq h₂.sobre

/-! ## 3. El reindexado: lo que una fibración da y un funtor cualquiera no -/

section Reindexado

variable {p : ProyeccionMonotona S A}

/--
EL PAGO DE LA CONDICIÓN. Si `e₁ ≤ e₂` están los dos encima de `b'`, entonces
sus levantamientos a `b'` conservan el orden.

En palabras del sistema: si un skill depende de otro dentro de un área, sus
soportes en el área de abajo dependen igual. Esa es la aplicación
`fibra(b) → fibra(b')` que el supergrafo necesita para que las dos semánticas
—skills y áreas— hablen entre sí, y NO existe sin la condición cartesiana.
-/
theorem reindexado_monotono {e₁ e₂ e₁' e₂' : S} {b' : A}
    (h₁ : EsCartesiano p e₁ e₁' b') (h₂ : EsCartesiano p e₂ e₂' b')
    (h : e₁ ≤ e₂) : e₁' ≤ e₂' :=
  h₂.universal e₁' (le_trans h₁.debajo h) (le_of_eq h₁.sobre)

/--
Restringir de `b` a `b'` y luego a `b''` es lo mismo que restringir
directamente de `b` a `b''`, siempre que `b'' ≼ b'`.

Es lo que autoriza a encadenar restricciones de área: el resultado no depende
del camino que se tome por la base.
-/
theorem reindexado_compuesto {e e' e'' d : S} {b' b'' : A}
    (hb : b'' ≤ b')
    (h' : EsCartesiano p e e' b') (h'' : EsCartesiano p e' e'' b'')
    (hd : EsCartesiano p e d b'') : e'' ≤ d ∧ d ≤ e'' := by
  constructor
  · -- e'' está debajo de e' y e' debajo de e, y vive sobre b''
    exact hd.universal e'' (le_trans h''.debajo h'.debajo) (le_of_eq h''.sobre)
  · -- d está debajo de e y sobre b'' ≼ b', luego pasa por e'; y de ahí por e''
    have hde' : d ≤ e' :=
      h'.universal d hd.debajo (le_trans (le_of_eq hd.sobre) hb)
    exact h''.universal d hde' (le_of_eq hd.sobre)

end Reindexado

/-! ## 4. La condición puede fallar -/

/--
La proyección de un punto a la cadena de dos elementos, mandando el punto
arriba, es monótona y NO es fibración.

Hace falta exhibirlo: si toda monótona fuera fibración, comprobar la condición
sobre el grafo real no distinguiría nada y el número no significaría nada.
-/
def puntoArriba : ProyeccionMonotona (Fin 1) (Fin 2) where
  map := fun _ => 1
  monotone := fun _ => le_refl 1

theorem no_toda_monotona_es_fibracion : ¬ EsFibracion puntoArriba := by
  intro h
  -- 0 ≼ 1 = π(e) para el único objeto e, así que la fibración daría un
  -- levantamiento; pero su imagen tendría que ser 0, y π sólo toma el valor 1.
  obtain ⟨e', he'⟩ := h 0 0 (by decide)
  have : (1 : Fin 2) = 0 := he'.sobre
  exact absurd this (by decide)

/--
Y la identidad sí lo es, de modo que la condición tampoco es vacua por el otro
lado: hay fibraciones.
-/
def identidad : ProyeccionMonotona S S where
  map := id
  monotone := fun h => h

theorem identidad_es_fibracion : EsFibracion (identidad (S := S)) := by
  intro e b' hb
  refine ⟨b', ⟨rfl, hb, ?_⟩⟩
  intro x _ hx
  exact hx

end MetamathProver.Fibracion
