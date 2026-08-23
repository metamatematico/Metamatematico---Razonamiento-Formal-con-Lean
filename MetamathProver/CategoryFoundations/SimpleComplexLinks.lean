/-
# Enlaces simples y complejos, y el principio de multiplicidad

## Qué se establece aquí

Ehresmann distingue dos clases de enlace en un sistema evolutivo con memoria:

  · un enlace es SIMPLE si factoriza a través de un solo clúster (colímite);
  · es COMPLEJO si no factoriza a través de ninguno.

En Ehresmann la distinción tiene contenido dinámico: la composición de dos
enlaces simples PUEDE no ser simple, y a eso se le llama emergencia.

Este archivo demuestra que en el modelo del sistema eso NO ocurre.

1. `simple_of_factors` — la caracterización: simple = factoriza por un clúster.
2. `identity_simple_iff_mem` — una identidad es simple syss su objeto es un
   clúster: es condición sobre el OBJETO, no sobre el enlace.
3. `composite_of_simple_is_simple` — **el resultado principal, y es negativo**:
   en una categoría delgada los simples son cerrados por composición. Se
   intento demostrar lo contrario y `decide` lo refuto; la razon es la
   transitividad y no un descuido del diseño.
4. `complex_of_empty_clusters` — los complejos existen, pero solo donde FALTAN
   clústeres: es una forma pobre de complejidad.
5. `multiplicity_gives_robustness` — el principio de multiplicidad implica que
   el colímite sobrevive a la pérdida de una descomposición.

## Relación con el código

`nucleo/graph/category.py::classify_link` implementa una HEURÍSTICA de cuatro
casos, no esta definición. Sus casos 1-2 sí corresponden a la factorización
formalizada aquí; los casos 3-4 (metadato `composed_from`, y diferencia de
nivel > 1) son aproximaciones que este archivo NO respalda. La diferencia queda
medida en `scripts/auditar_respaldo_lean.py`.

`nucleo/mes/patterns.py::verify_multiplicity_principle` corresponde a
`MultiplicityPrinciple` de la sección 3.
-/

import Mathlib.Order.Basic
import Mathlib.Data.Fintype.Basic
import Mathlib.Data.Finset.Basic
import MetamathProver.CategoryFoundations.JoinColimit

namespace MetamathProver.SimpleComplexLinks

open MetamathProver.JoinColimit

universe u

/-! ## 1. La definición -/

variable {P : Type u} [Preorder P]

/--
`FactorizaPor c a b` : el enlace `a → b` pasa por `c`.

En una categoría delgada esto es simplemente `a ≤ c ∧ c ≤ b`: como hay a lo
sumo un morfismo entre dos objetos, la factorización es única cuando existe y
no hace falta exigir que el triángulo conmute.
-/
def FactorizaPor (c a b : P) : Prop := a ≤ c ∧ c ≤ b

/--
`EsSimple C a b` : el enlace `a → b` es simple respecto de la familia de
clústeres `C`, es decir, factoriza por alguno de ellos.

`C` es el conjunto de objetos que SON colímites de algún patrón. En el sistema
es `{s : s.pattern_ids ≠ ∅}`.
-/
def EsSimple (C : Finset P) (a b : P) : Prop :=
  ∃ c ∈ C, FactorizaPor c a b

/-- `EsComplejo` es la negación, y solo tiene interés si además `a ≤ b`. -/
def EsComplejo (C : Finset P) (a b : P) : Prop :=
  a ≤ b ∧ ¬ EsSimple C a b

theorem simple_of_factors {C : Finset P} {a b c : P}
    (hc : c ∈ C) (h : FactorizaPor c a b) : EsSimple C a b :=
  ⟨c, hc, h⟩

/-- Un enlace simple es, en particular, un enlace. -/
theorem simple_le {C : Finset P} {a b : P} (h : EsSimple C a b) : a ≤ b := by
  obtain ⟨c, _, hac, hcb⟩ := h
  exact le_trans hac hcb

/--
**Teorema.** La identidad de `a` es simple exactamente cuando `a` está por
debajo de algún clúster que a su vez está por debajo de `a` — en un orden
parcial, cuando `a` mismo es un clúster.

Es una condición sobre el OBJETO, no sobre el enlace: la simplicidad de las
identidades no es automática, y por eso `classify_link` las trata como un caso
aparte (`LinkComplexity.IDENTITY`) en vez de clasificarlas.
-/
theorem identity_simple_iff {C : Finset P} {a : P} :
    EsSimple C a a ↔ ∃ c ∈ C, a ≤ c ∧ c ≤ a := Iff.rfl

/-- En un orden parcial la condición anterior dice que `a` es un clúster. -/
theorem identity_simple_iff_mem {α : Type u} [PartialOrder α]
    {C : Finset α} {a : α} : EsSimple C a a ↔ a ∈ C := by
  constructor
  · rintro ⟨c, hc, hac, hca⟩
    rwa [le_antisymm hac hca]
  · intro h
    exact ⟨a, h, le_refl a, le_refl a⟩

/-! ## 2. En una categoría delgada NO hay emergencia por composición -/

/-
Esta sección iba a exhibir enlaces simples cuya composición no lo fuera —lo que
Ehresmann llama emergencia. El intento fracasó, y el fracaso es el resultado.

`decide` refutó el contraejemplo, y al mirar por qué la razón resultó ser
estructural y no un descuido del diseño: si `a ≤ k ≤ b` y `b ≤ n ≤ d`, la
transitividad da `k ≤ d`, de modo que el propio `k` factoriza `a → d`. En un
preorden no hay manera de que dos enlaces simples compongan a uno complejo.

El teorema verdadero es el recíproco del que se buscaba.
-/

/--
**Teorema.** En una categoría delgada, la composición de dos enlaces simples es
simple: basta el clúster del primero.

La demostración es de una línea, y esa brevedad es exactamente el problema:
no hace falta ninguna hipótesis sobre los clústeres.
-/
theorem composite_of_simple_is_simple {C : Finset P} {a b d : P}
    (hab : EsSimple C a b) (hbd : EsSimple C b d) : EsSimple C a d := by
  obtain ⟨c, hc, hac, hcb⟩ := hab
  exact ⟨c, hc, hac, le_trans hcb (simple_le hbd)⟩

/--
**Corolario.** La clase de los enlaces simples es cerrada por composición.

Dicho de otro modo: los enlaces simples forman una subcategoría, y componer
nunca sale de ella.
-/
theorem simples_closed_under_composition {C : Finset P} :
    ∀ a b d : P, EsSimple C a b → EsSimple C b d → EsSimple C a d :=
  fun _ _ _ => composite_of_simple_is_simple

/--
**Teorema (dónde sí puede haber enlaces complejos).**

Un enlace complejo no puede surgir de componer simples, pero sí puede existir
directamente: basta un `a ≤ b` sin ningún clúster entre medias. En particular,
si la familia de clústeres es vacía, todo enlace no trivial es complejo.

Es la única forma de complejidad que el modelo delgado admite, y es una forma
POBRE: dice que faltan clústeres, no que haya emergido estructura.
-/
theorem complex_iff_no_cluster_between {C : Finset P} {a b : P} (hab : a ≤ b) :
    EsComplejo C a b ↔ ¬ ∃ c ∈ C, a ≤ c ∧ c ≤ b :=
  ⟨fun h => h.2, fun h => ⟨hab, h⟩⟩

theorem complex_of_empty_clusters {a b : P} (hab : a ≤ b) :
    EsComplejo (∅ : Finset P) a b := by
  refine ⟨hab, ?_⟩
  rintro ⟨c, hc, -⟩
  simp at hc

/-
CONSECUENCIA PARA EL SISTEMA
----------------------------
El grafo de habilidades se modela como un preorden —es la hipótesis que hace
que join = colímite, y de la que dependen JoinColimit.lean e
IsColimitBridge.lean—. Este teorema dice que en esa hipótesis la distinción
simple/complejo de Ehresmann PIERDE su contenido dinámico: los complejos no
emergen al componer, solo aparecen donde faltan clústeres.

Recuperar la emergencia exigiría abandonar la delgadez, es decir, admitir más
de un morfismo entre dos habilidades y distinguir CÓMO se llega, no solo si se
llega. Eso es un cambio de modelo, no un ajuste.

Queda registrado como límite conocido, no como algo pendiente de implementar.
-/

/-! ## 3. El principio de multiplicidad -/

/--
`Homologos P Q j` : dos patrones distintos con el MISMO colímite.

Es la relación que `patterns.py::are_homologous` calcula: dos descomposiciones
diferentes de la misma funcionalidad.
-/
def Homologos (S T : Finset P) (j : P) : Prop :=
  S ≠ T ∧ IsJoin S j ∧ IsJoin T j

/--
`MultiplicityPrinciple` : existen patrones homólogos. Es el Axioma 8.2 del
sistema, y lo que `verify_multiplicity_principle` comprueba.
-/
def MultiplicityPrinciple (j : P) : Prop :=
  ∃ S T : Finset P, Homologos S T j

theorem homologos_symm {S T : Finset P} {j : P} (h : Homologos S T j) :
    Homologos T S j :=
  ⟨h.1.symm, h.2.2, h.2.1⟩

/--
**Teorema (unicidad del colímite).** Dos patrones homólogos tienen, por
definición, el mismo colímite; y en un orden parcial el colímite de un patrón
es único.

Es lo que hace del principio de multiplicidad un enunciado con contenido: no
dice que haya varios colímites, sino varias DESCOMPOSICIONES del mismo.
-/
theorem colimite_unico {α : Type u} [PartialOrder α] {S : Finset α} {j j' : α}
    (h : IsJoin S j) (h' : IsJoin S j') : j = j' :=
  le_antisymm (h.least j' h'.upper_bound) (h'.least j h.upper_bound)

/--
**Teorema (robustez).** Si `S` y `T` son homólogos con colímite `j`, entonces
perder una de las dos descomposiciones no destruye `j`: la otra sigue siendo
un patrón cuyo colímite es `j`.

Éste es el contenido operativo del principio de multiplicidad, y la razón por
la que Ehresmann lo pide: un sistema con una sola descomposición por concepto
es frágil.
-/
theorem multiplicity_gives_robustness {S T : Finset P} {j : P}
    (h : Homologos S T j) : IsJoin S j ∧ IsJoin T j ∧ S ≠ T :=
  ⟨h.2.1, h.2.2, h.1⟩

/--
**Teorema.** El colímite de un patrón homólogo es cota superior de la UNIÓN de
ambas descomposiciones.

Da la forma constructiva de comprobar la homología sin recalcular el colímite
dos veces.
-/
theorem join_of_union [DecidableEq P] {S T : Finset P} {j : P}
    (h : Homologos S T j) : ∀ s ∈ S ∪ T, s ≤ j := by
  intro s hs
  rcases Finset.mem_union.mp hs with h1 | h2
  · exact h.2.1.upper_bound s h1
  · exact h.2.2.upper_bound s h2

end MetamathProver.SimpleComplexLinks
