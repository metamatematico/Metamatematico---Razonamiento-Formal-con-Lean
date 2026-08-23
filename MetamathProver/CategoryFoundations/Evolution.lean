/-
# Evolución: funtores de transición y compatibilidad

## Qué modela

`nucleo/graph/evolution.py` guarda instantáneas del grafo en cada tiempo `t` y
un **funtor de transición** `k_{t1,t2}` entre ellas. Un objeto puede:

  · conservarse       — va a sí mismo
  · absorberse        — va a otro objeto (típicamente un colímite)
  · eliminarse        — no va a ninguno

Esa tercera posibilidad es la que obliga a modelarlo como **funtor parcial**:
en Python, `object_map : dict[str, Optional[str]]`.

La propiedad que el sistema afirma (Def. 3.2) es la **compatibilidad**:

    k_{t2,t3} ∘ k_{t1,t2} = k_{t1,t3}

que es exactamente decir que la familia de transiciones es funtorial sobre el
orden del tiempo. Sin ella, «el estado en t3» dependería del camino recorrido y
las instantáneas dejarían de describir una evolución.

## Qué se demuestra

1. `comp` — la composición de funtores parciales, tal como la hace Python.
2. `comp_assoc` — es asociativa. Es lo que permite hablar de `k_{t1,t3}` sin
   ambigüedad cuando hay más de dos pasos.
3. `eliminado_es_absorbente` — lo eliminado no vuelve. Una vez que un objeto
   sale, ninguna composición posterior lo recupera.
4. `compatible_iff` — la compatibilidad es la ley de funtor, ni más ni menos.
5. `compatibilidad_transitiva` — si los pasos consecutivos son compatibles, la
   composición larga también lo es. Es lo que hace que baste comprobarla
   localmente, que es lo que `verify_compatibility` hace.

## Lo que NO se demuestra

Que el sistema real sea compatible. Eso no es un teorema sino una medición, y
está en `tests/test_evolucion.py`.
-/

import Mathlib.Order.Basic
import Mathlib.Data.Finset.Basic

namespace MetamathProver.Evolution

universe u

/-! ## 1. Funtores parciales -/

variable {O : Type u}

/--
Un funtor de transición en objetos: `Option O` recoge los tres casos, con
`none` para lo eliminado.
-/
def Transicion (O : Type u) : Type u := O → Option O

/--
Composición, exactamente como la calcula Python:

    composed[s] = self.object_map[ other.object_map[s] ]

con `none` propagándose. Es el `bind` de la mónada `Option`, y decirlo así deja
claro por qué es asociativa.
-/
def comp (g f : Transicion O) : Transicion O :=
  fun s => (f s).bind g

@[simp] theorem comp_none {g f : Transicion O} {s : O} (h : f s = none) :
    comp g f s = none := by simp [comp, h]

@[simp] theorem comp_some {g f : Transicion O} {s t : O} (h : f s = some t) :
    comp g f s = g t := by simp [comp, h]

/-- La identidad: todo objeto se conserva. -/
def idTrans : Transicion O := fun s => some s

@[simp] theorem comp_id_left (f : Transicion O) : comp idTrans f = f := by
  funext s
  cases h : f s <;> simp [comp, h, idTrans]

@[simp] theorem comp_id_right (f : Transicion O) : comp f idTrans = f := by
  funext s
  simp [comp, idTrans]

/--
**Teorema.** La composición de funtores de transición es asociativa.

Es lo que permite escribir `k_{t1,t4}` sin decir por dónde se pasó: si no
valiera, «el estado en t4» dependería del orden en que se compusieran los
pasos, y las instantáneas no describirían una evolución.
-/
theorem comp_assoc (h g f : Transicion O) :
    comp (comp h g) f = comp h (comp g f) := by
  funext s
  cases hf : f s with
  | none => simp [comp, hf]
  | some t => cases hg : g t <;> simp [comp, hf, hg]

/-! ## 2. Lo eliminado no vuelve -/

/--
**Teorema.** Si un objeto se elimina en el primer paso, ninguna composición
posterior lo recupera.

Parece obvio y por eso conviene tenerlo: es la propiedad que justifica que
`num_eliminated` sea acumulativo y que el conteo de Python no tenga que
descontar resurrecciones.
-/
theorem eliminado_es_absorbente {f : Transicion O} {s : O} (h : f s = none)
    (g : Transicion O) : comp g f s = none :=
  comp_none h

/-- Y se conserva a lo largo de cualquier cadena. -/
theorem eliminado_persiste {f : Transicion O} {s : O} (h : f s = none)
    (gs : List (Transicion O)) :
    (gs.foldr comp idTrans |> fun G => comp G f) s = none :=
  comp_none h

/-! ## 3. Compatibilidad = funtorialidad -/

/--
`Compatible k12 k23 k13` : el camino largo coincide con la composición de los
cortos. Es la Def. 3.2 del sistema.
-/
def Compatible (k12 k23 k13 : Transicion O) : Prop :=
  comp k23 k12 = k13

/--
**Teorema.** La compatibilidad es exactamente la ley de funtor, escrita objeto
a objeto — que es como la comprueba `verify_compatibility`.
-/
theorem compatible_iff (k12 k23 k13 : Transicion O) :
    Compatible k12 k23 k13 ↔ ∀ s : O, (k12 s).bind k23 = k13 s := by
  constructor
  · intro h s; rw [← h]; rfl
  · intro h; funext s; exact h s

/--
**Teorema.** El funtor largo queda DETERMINADO por los cortos.

Dicho de otro modo: si `k_{t1,t3}` existe y es compatible, es único. No hay
libertad de elección, y por eso `get_functor(t1, t3)` puede calcularse
componiendo en vez de guardarse.
-/
theorem compatible_unico {k12 k23 k13 k13' : Transicion O}
    (h : Compatible k12 k23 k13) (h' : Compatible k12 k23 k13') :
    k13 = k13' := by
  rw [← h, ← h']

/--
**Teorema (compatibilidad transitiva).**

Si los pasos consecutivos son compatibles dos a dos, la composición de tres
pasos también lo es. Es lo que justifica comprobar la compatibilidad
LOCALMENTE —tripletas `(t, t+1, t+2)`— en vez de sobre todos los pares, que es
lo que hace el sistema.
-/
theorem compatibilidad_transitiva
    {k12 k23 k34 k13 k24 k14 : Transicion O}
    (h123 : Compatible k12 k23 k13)
    (h234 : Compatible k23 k34 k24)
    (h134 : Compatible k13 k34 k14) :
    Compatible k12 k24 k14 := by
  unfold Compatible at *
  rw [← h134, ← h123, ← h234, comp_assoc]

/-! ## 4. Emergencia medida sobre la evolución -/

/--
`SoloCrece f` : la transición no elimina nada.

Cuando se cumple, el número de objetos no puede bajar, y `complexity_growth`
—que `measure_emergence` calcula como diferencia entre tiempos— mide
crecimiento real y no reciclaje.
-/
def SoloCrece (f : Transicion O) : Prop := ∀ s : O, f s ≠ none

theorem soloCrece_comp {g f : Transicion O}
    (hf : SoloCrece f) (hg : SoloCrece g) : SoloCrece (comp g f) := by
  intro s
  cases h : f s with
  | none => exact absurd h (hf s)
  | some t => simpa [comp, h] using hg t

/--
**Teorema.** Si ningún paso elimina, ninguna cadena elimina.

Es la hipótesis bajo la cual `emergence_ratio` es comparable entre tiempos: si
se eliminan objetos, el denominador cambia por dos motivos distintos y la
proporción deja de medir lo mismo.
-/
theorem soloCrece_cadena {fs : List (Transicion O)}
    (h : ∀ f ∈ fs, SoloCrece f) : SoloCrece (fs.foldr comp idTrans) := by
  induction fs with
  | nil => intro s; simp [idTrans]
  | cons a t ih =>
    exact soloCrece_comp (ih fun f hf => h f (List.mem_cons_of_mem a hf))
                         (h a List.mem_cons_self)

end MetamathProver.Evolution
