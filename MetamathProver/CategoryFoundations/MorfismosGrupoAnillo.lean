-- MorfismosGrupoAnillo.lean: cuantos morfismos hay de group-theory a ring-theory
import Mathlib.Tactic
import Mathlib.Data.ZMod.Basic
import Mathlib.Data.ZMod.Units

/-!
# ¿Cuantos morfismos hay de `group-theory` a `ring-theory`?

## Por que esta pregunta

`Complexificacion.lean §9` demuestra que el sistema no puede producir orden de
complejidad >= 2 mientras `Hom(a,b)` tenga a lo sumo un elemento, y exhibe el
testigo abstracto de que perder esa propiedad basta. Queda la pregunta
practica: en el grafo real, ¿hay de verdad dos morfismos distintos entre dos
habilidades concretas, o la delgadez es fiel al dominio?

Este archivo la contesta para el par mas citado del grafo.

## Que puede y que no puede decir Lean

NO puede enumerarlos todos. «Los funtores `Ring ⥤ Grp`» no es una pregunta
decidible; ni siquiera es un conjunto. Cualquiera que prometa la lista completa
esta prometiendo algo que no existe.

SI puede lo que hace falta: **certificar candidatos concretos y demostrar que
son distintos**. Para romper la delgadez basta exhibir dos, y que Lean confirme
que no se pueden identificar.

## Los dos candidatos

En el grafo, la arista `group-theory → ring-theory` es de tipo DEPENDENCY, que
se lee «ring-theory requiere group-theory». Su contenido matematico es: ¿de que
modos usa la teoria de anillos a la de grupos? Es decir, ¿que grupo produce un
anillo?

Hay al menos dos respuestas clasicas, y son genuinamente distintas:

  1. **El grupo aditivo** `(R, +)`. Todo anillo es un grupo abeliano bajo la
     suma. Es una interpretacion por terminos: la operacion de grupo se define
     con una operacion del anillo.

  2. **El grupo de unidades** `Rˣ`. Los elementos invertibles bajo el producto
     forman un grupo. NO es una interpretacion por terminos —las unidades se
     recortan con una condicion, no con una ecuacion— pero es un funtor
     perfectamente legitimo.

Que sean distintos no es una impresion: se separa con una cuenta.
-/

namespace MetamathProver.MorfismosGrupoAnillo

/-! ## Los dos morfismos, sobre un anillo cualquiera -/

/-- Morfismo 1: el grupo aditivo del anillo, visto multiplicativamente. -/
abbrev grupoAditivo (R : Type*) [Ring R] := Multiplicative R

/-- Morfismo 2: el grupo de unidades del anillo. -/
abbrev grupoUnidades (R : Type*) [Ring R] := Rˣ

example (R : Type*) [Ring R] : Group (grupoAditivo R) := inferInstance
example (R : Type*) [Ring R] : Group (grupoUnidades R) := inferInstance

/-! ## La separacion: `ZMod 5`

Un anillo finito basta para distinguirlos. Sobre `ZMod 5`:

  · el grupo aditivo tiene 5 elementos;
  · el grupo de unidades tiene 4 —todos menos el cero, porque `ZMod 5` es
    cuerpo—.

Cinco no es cuatro. Luego no hay biyeccion, luego no hay isomorfismo, luego los
dos morfismos no se pueden identificar.
-/

theorem card_aditivo : Fintype.card (grupoAditivo (ZMod 5)) = 5 := by decide

theorem card_unidades : Fintype.card (grupoUnidades (ZMod 5)) = 4 := by decide

/--
**Teorema.** Los dos morfismos no son isomorfos: sobre `ZMod 5` producen grupos
de cardinal distinto.
-/
theorem no_hay_iso :
    IsEmpty (grupoAditivo (ZMod 5) ≃ grupoUnidades (ZMod 5)) := by
  rw [← not_nonempty_iff, ← Fintype.card_eq, card_aditivo, card_unidades]
  decide

/--
**Corolario — lo que el sistema necesita.**

`Hom(group-theory, ring-theory)` tiene **al menos dos** elementos genuinamente
distintos. Luego el par no es delgado, luego la hipotesis de `lub_de_lubs` falla
para el, luego la barrera del orden >= 2 no aplica aqui.

No dice cuantos hay en total —esa pregunta no tiene respuesta computable— sino
lo unico que hacia falta: que hay mas de uno.
-/
theorem hom_no_es_delgado :
    Fintype.card (grupoAditivo (ZMod 5)) ≠ Fintype.card (grupoUnidades (ZMod 5)) := by
  rw [card_aditivo, card_unidades]
  decide

/-! ## Un tercero, para que no parezca un accidente

El grupo trivial es tambien un morfismo legitimo —el funtor constante— y
tampoco coincide con los otros dos. Con el son tres, y no hay razon para pensar
que ahi se acaben: `GL₂(R)`, el centro de `Rˣ`, el grupo aditivo de `R[x]`…

Lo que importa no es la cuenta, que no se puede cerrar, sino que sea > 1.
-/

/-- Morfismo 3: el funtor constante al grupo trivial. -/
abbrev grupoTrivial (R : Type*) [Ring R] := Unit

theorem card_trivial : Fintype.card (grupoTrivial (ZMod 5)) = 1 := rfl

theorem tres_morfismos_distintos_dos_a_dos :
    Fintype.card (grupoAditivo (ZMod 5)) ≠ Fintype.card (grupoUnidades (ZMod 5)) ∧
    Fintype.card (grupoAditivo (ZMod 5)) ≠ Fintype.card (grupoTrivial (ZMod 5)) ∧
    Fintype.card (grupoUnidades (ZMod 5)) ≠ Fintype.card (grupoTrivial (ZMod 5)) := by
  refine ⟨?_, ?_, ?_⟩ <;>
    simp only [card_aditivo, card_unidades, card_trivial] <;> decide

/-! ## Enumerar de verdad: acotar la clase la vuelve decidible

«Todos los morfismos» no se puede. «Todos los morfismos de una clase acotada»
si, y es una pregunta que Lean contesta ejecutandola.

Tomemos la clase mas natural: las estructuras de grupo sobre un anillo cuya
operacion se define con un **termino afin del anillo**,

    f(x, y) = a·x + b·y + c

Sobre `ZMod 5` hay 125 candidatos (`a`, `b`, `c` recorren el anillo). Se
comprueban los axiomas de grupo en cada uno y se cuentan los que pasan. Todo el
proceso es finito y decidible, asi que el kernel lo hace entero.
-/

/-- Operacion binaria afin `f(x,y) = a·x + b·y + c`. -/
def afin (a b c x y : ZMod 5) : ZMod 5 := a * x + b * y + c

/-- Los axiomas de grupo para `afin a b c`, todos con cuantificadores finitos. -/
def esGrupo (a b c : ZMod 5) : Prop :=
  (∀ x y z : ZMod 5,
      afin a b c (afin a b c x y) z = afin a b c x (afin a b c y z)) ∧
  (∃ e : ZMod 5,
      (∀ x : ZMod 5, afin a b c e x = x ∧ afin a b c x e = x) ∧
      (∀ x : ZMod 5, ∃ y : ZMod 5,
          afin a b c x y = e ∧ afin a b c y x = e))

instance (a b c : ZMod 5) : Decidable (esGrupo a b c) := by
  unfold esGrupo; infer_instance

/-- Los 125 candidatos que de verdad son grupos. -/
def gruposAfines : Finset (ZMod 5 × ZMod 5 × ZMod 5) :=
  Finset.univ.filter (fun p => esGrupo p.1 p.2.1 p.2.2)

/--
**Teorema (enumeracion completa de la clase afin).** De los 125 candidatos,
exactamente **5** son grupos.

Y son precisamente `f(x,y) = x + y + c`, uno por cada `c`: todos isomorfos al
grupo aditivo, trasladados. Es decir, **dentro de la clase afin el grupo aditivo
es el unico**, salvo traslacion.
-/
theorem hay_cinco_grupos_afines : gruposAfines.card = 5 := by decide

set_option maxRecDepth 8000 in
/-- Y son exactamente los de la forma `x + y + c`. -/
theorem los_afines_son_la_suma_trasladada :
    ∀ p ∈ gruposAfines, p.1 = 1 ∧ p.2.1 = 1 := by decide

/-- Los 125 candidatos, por una ruta computable (para poder LISTARLOS). -/
def candidatos : List (ZMod 5 × ZMod 5 × ZMod 5) :=
  (List.range 5).flatMap (fun a =>
    (List.range 5).flatMap (fun b =>
      (List.range 5).map (fun c => ((a : ZMod 5), (b : ZMod 5), (c : ZMod 5)))))

set_option maxRecDepth 4000 in
theorem hay_125_candidatos : candidatos.length = 125 := by decide

set_option maxRecDepth 40000 in
/--
**Teorema (la lista, explicita).** No solo cuantos: cuales.

    [(1,1,0), (1,1,1), (1,1,2), (1,1,3), (1,1,4)]

Los cinco tienen `a = b = 1`. La operacion es `f(x,y) = x + y + c`: la suma
del anillo, trasladada. Ninguna otra combinacion afin da un grupo.
-/
theorem la_lista_completa :
    candidatos.filter (fun p => decide (esGrupo p.1 p.2.1 p.2.2))
      = [(1, 1, 0), (1, 1, 1), (1, 1, 2), (1, 1, 3), (1, 1, 4)] := by
  decide

/-!
### Lo que esto dice, que es mas interesante de lo que parece

La enumeracion acotada devuelve **uno solo** —el grupo aditivo— y eso no
contradice a `hom_no_es_delgado`: lo explica.

El grupo de unidades `Rˣ` **no aparece en la lista** porque no es de esa clase:
las unidades no se definen con un termino, se recortan con una condicion
(«existe inverso»). Por eso escapa a la enumeracion afin, y por eso es un
morfismo genuinamente de otra naturaleza — no una variante del primero.

O sea: los dos morfismos que separan el par no solo son distintos, son de
especies distintas. Uno es una interpretacion por terminos; el otro no puede
serlo. Eso es exactamente la clase de multiplicidad que hace falta.

### Y el limite honesto

Ampliar la clase —polinomios de grado 2, terminos con inverso, funtores
arbitrarios— hace crecer la busqueda hasta que deja de ser finita. La
enumeracion total no existe. Lo que si se puede, y es lo que el sistema
necesita, es **certificar** cada morfismo que alguien proponga y **demostrar**
que es distinto de los ya registrados. Eso es decidible caso a caso, y es todo
lo que hace falta para que `Hom(a,b)` deje de ser un booleano.
-/

/-!
## Conclusion para el grafo de habilidades

El dominio NO es delgado. La arista `group-theory → ring-theory` del grafo esta
representando con un solo morfismo algo que tiene al menos tres, y dos de ellos
—grupo aditivo y grupo de unidades— son los que cualquier algebrista nombraria
primero.

Eso responde la pregunta que quedaba abierta: la delgadez del modelo no es
fidelidad al dominio, es una perdida de informacion. Y la informacion que se
pierde es exactamente la que hace falta para que la emergencia de Ehresmann sea
posible.

Lo que este archivo NO establece: que el sistema sepa usarla. Para eso
`Hom(a,b)` tiene que dejar de ser un booleano en `category.py`, y eso es el
cambio de arquitectura que sigue pendiente.
-/

end MetamathProver.MorfismosGrupoAnillo
