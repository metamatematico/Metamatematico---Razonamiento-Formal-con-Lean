-- ComplexityOrder.lean: Formal Foundations for the NLE Emergent Skill Hierarchy
-- (Imports must precede the module docstring in Lean 4.29+)

import Mathlib.Tactic

/-!
# ComplexityOrder.lean

## Formal Foundations for the NLE Emergent Skill Hierarchy

This file proves the mathematical results that justify the emergent
hierarchy construction in `nucleo/graph/complexity.py`.

### The NLE claim (precise version)

The skill graph G_n is a **finite thin category** (preorder):
  - Objects: skills  s₁, s₂, …, sₙ
  - Morphisms: Hom(s, t) = {*}  if s ≤ t,  ∅  otherwise
  - Composition: trivial (unique morphisms)

In this category, **colimits = joins** (Lemma `colimit_eq_join`).

A skill J has **complexity order** `cn(J) = k` iff:
  - J = join[P]  for some pattern P  (J is not atomic), and
  - k = 1 + max{cn(P_i) | Pᵢ ∈ components(P)}

The NUMBER OF LEVELS is not preset — it emerges from the fixpoint of
the Bellman-Ford iteration in `compute_complexity_order`.

### Key theorems proved here

1. **`thin_unique_hom`**: Proof irrelevance in preorders — all diagrams commute.
2. **`join_iff_colimit`**: In a finite semilattice, join ↔ colimit.
3. **`fubini_joins`**: join(join ∘ S) = join(⋃ S) — stacked cocones commute.
4. **`cn_strict_increase`**: cn(join[P]) > cn(Pᵢ) for all components Pᵢ.
5. **`hierarchy_well_founded`**: The cn iteration terminates.

### Connection to Python

The Python function `build_hierarchy_to_fixpoint` implements the
constructive version of Theorem `hierarchy_well_founded`:
it runs at most diameter(G_n) iterations before reaching a fixpoint.
-/

/-! ## §1  Thin categories: all diagrams commute -/

/-- In a preorder, any two proofs of `a ≤ b` are definitionally equal.
    This is the categorical statement: Hom(a, b) is either empty or a
    singleton, so there is *at most one* morphism between any two objects. -/
theorem thin_unique_hom {α : Type*} [Preorder α] {a b : α}
    (h₁ h₂ : a ≤ b) : h₁ = h₂ :=
  Subsingleton.elim h₁ h₂

/-- Corollary: every diagram in a thin category commutes.
    Any two parallel paths a → b yield the same morphism. -/
theorem thin_all_diagrams_commute {α : Type*} [Preorder α]
    {a b : α} (path₁ path₂ : a ≤ b) : path₁ = path₂ :=
  thin_unique_hom path₁ path₂

/-! ## §2  Joins as colimits in finite preorders -/

/-- The join (supremum) of a finite set is the colimit of the
    corresponding discrete diagram in the preorder. -/
theorem join_is_upper_bound {α : Type*} [SemilatticeSup α] [OrderBot α]
    (s : Finset α) (a : α) (ha : a ∈ s) : a ≤ s.sup id := by
  exact Finset.le_sup (f := id) ha

/-- Universal property: the join is the SMALLEST upper bound. -/
theorem join_is_minimal_upper_bound {α : Type*} [SemilatticeSup α] [OrderBot α]
    (s : Finset α) (x : α) (hx : ∀ a ∈ s, a ≤ x) : s.sup id ≤ x :=
  Finset.sup_le hx

/-- The join characterizes the colimit: an element c is the join of s
    iff it is an upper bound and every upper bound is above c. -/
theorem join_iff_colimit {α : Type*} [SemilatticeSup α] [OrderBot α]
    (s : Finset α) (c : α) :
    c = s.sup id ↔
    (∀ a ∈ s, a ≤ c) ∧ (∀ x, (∀ a ∈ s, a ≤ x) → c ≤ x) := by
  constructor
  · intro h
    subst h
    exact ⟨fun a ha => Finset.le_sup (f := id) ha,
           fun x hx => Finset.sup_le hx⟩
  · intro ⟨hub, hmin⟩
    apply le_antisymm
    · exact hmin _ (fun a ha => Finset.le_sup (f := id) ha)
    · exact Finset.sup_le hub

/-! ## §3  Fubini theorem for joins — stacked cocones commute -/

/-- **Fubini for joins**: the join of joins equals the join of the union.

    Categorically: given a two-level diagram
        { Pᵢⱼ }  ──colim_j──▶  Jᵢ  ──colim_i──▶  J

    the element J equals the join of all base elements ⋃ᵢ Pᵢⱼ.

    This is the key theorem that ensures the NLE stacked-cocone
    construction is coherent: cn-levels are consistent across depths.

    **Proof**: direct from `Finset.sup_biUnion` in Mathlib. -/
-- Lean 4.29+: Finset.biUnion requires DecidableEq on the element type
theorem fubini_joins {α : Type*} [SemilatticeSup α] [OrderBot α] [DecidableEq α]
    (S : Finset (Finset α)) :
    S.sup (fun t => t.sup id) = (S.biUnion id).sup id := by
  simp [Finset.sup_biUnion]

/-- Corollary: a two-step join equals a one-step join over the union.
    This is the Python `build_hierarchy_to_fixpoint` invariant. -/
theorem two_step_join_eq_flat {α : Type*} [SemilatticeSup α] [OrderBot α] [DecidableEq α]
    (P Q : Finset α) :
    (({P, Q} : Finset (Finset α)).sup (fun t => t.sup id)) =
    (P ∪ Q).sup id := by
  rw [fubini_joins]
  congr 1
  simp [Finset.biUnion_insert]

/-! ## §4  Complexity order -/

/-- Iterative computation of the complexity order (Bellman-Ford style).

    `complexityOrderIter n isJoinOf k` runs `k` rounds of:
      cn[x] = 0                              if x is not a join
      cn[x] = 1 + max{cn[c] | c ∈ comps(x)}  if x = join[comps(x)]

    After `n` rounds (where n = number of skills), the values stabilize. -/
def complexityOrderIter {n : ℕ}
    (isJoinOf : Fin n → Option (List (Fin n))) : ℕ → (Fin n → ℕ)
  | 0     => fun _ => 0
  | k + 1 =>
    let prev := complexityOrderIter isJoinOf k
    fun x =>
      match isJoinOf x with
      | none        => 0
      | some comps  => 1 + comps.foldr (fun c acc => max (prev c) acc) 0

/-- The complexity order after `n` rounds (guaranteed fixpoint for
    any acyclic join structure on `n` nodes). -/
def complexityOrder {n : ℕ}
    (isJoinOf : Fin n → Option (List (Fin n))) : Fin n → ℕ :=
  complexityOrderIter isJoinOf n

/-- Ecuacion de un paso, para desplegar sin que `simp` siga hacia dentro. -/
theorem iter_succ {n : ℕ} (isJoinOf : Fin n → Option (List (Fin n)))
    (k : ℕ) (x : Fin n) :
    complexityOrderIter isJoinOf (k + 1) x =
      (match isJoinOf x with
       | none => 0
       | some comps =>
         1 + comps.foldr (fun c acc => max (complexityOrderIter isJoinOf k c) acc) 0) :=
  rfl

theorem foldr_ge {n : ℕ} (prev : Fin n → ℕ) (comps : List (Fin n))
    {c : Fin n} (hc : c ∈ comps) :
    prev c ≤ comps.foldr (fun c acc => max (prev c) acc) 0 := by
  induction comps with
  | nil => cases hc
  | cons a t ih =>
    rcases List.mem_cons.mp hc with rfl | ht
    · exact le_max_left _ _
    · exact le_trans (ih ht) (le_max_right _ _)

/-- Si dos asignaciones coinciden en las componentes, su maximo coincide. -/
theorem foldr_congr {n : ℕ} {p q : Fin n → ℕ} (comps : List (Fin n))
    (h : ∀ c ∈ comps, p c = q c) :
    comps.foldr (fun c acc => max (p c) acc) 0 =
    comps.foldr (fun c acc => max (q c) acc) 0 := by
  induction comps with
  | nil => rfl
  | cons a t ih =>
    simp only [List.foldr_cons]
    rw [h a List.mem_cons_self]
    exact congrArg _ (ih fun c hc => h c (List.mem_cons_of_mem a hc))

/--
`Aciclico` : las componentes de un join son estrictamente anteriores.

Es la hipotesis que los docstrings originales mencionaban ("for any acyclic
join structure") pero que los enunciados no pedian. Sin ella los dos teoremas
de esta seccion son FALSOS, y la seccion siguiente lo demuestra.

En el sistema se cumple por construccion: `build_hierarchy_to_fixpoint` solo
descubre colimites entre objetos que ya existen, nunca crea ciclos.
-/
def Aciclico {n : ℕ} (isJoinOf : Fin n → Option (List (Fin n))) : Prop :=
  ∀ x comps, isJoinOf x = some comps → ∀ c ∈ comps, c < x

/-! ### Los enunciados sin aciclicidad son falsos -/

/-- Un ciclo: `0` es join de `[1]` y `1` es join de `[0]`. -/
def cicloTestigo : Fin 2 → Option (List (Fin 2))
  | 0 => some [1]
  | 1 => some [0]

/--
**Teorema (refutacion).** Sin la hipotesis de aciclicidad, la iteracion no
alcanza punto fijo: con `cicloTestigo` los valores crecen indefinidamente.

Es el motivo por el que `hierarchy_well_founded` estaba sin demostrar: el
enunciado era falso, no dificil.
-/
theorem no_fixpoint_sin_aciclicidad :
    complexityOrderIter cicloTestigo 2 0 ≠ complexityOrderIter cicloTestigo 3 0 := by
  decide

/--
**Teorema (refutacion).** Sin aciclicidad, el cn de un join tampoco domina
estrictamente al de sus componentes: con el ciclo ambos valen lo mismo.
-/
theorem no_gt_sin_aciclicidad :
    ¬ (complexityOrderIter cicloTestigo 2 1 <
       complexityOrderIter cicloTestigo 2 0) := by
  decide

theorem cicloTestigo_no_aciclico : ¬ Aciclico cicloTestigo := by
  intro h
  have := h 0 [1] rfl 1 (List.mem_singleton_self 1)
  exact absurd this (by decide)

/-! ### Los enunciados verdaderos, bajo aciclicidad -/

/--
**Lema de estabilizacion.** Bajo aciclicidad, el valor de `x` deja de cambiar
a partir de la ronda `x + 1`.

La induccion es fuerte sobre `x`: el valor de `x` en la ronda `k+1` solo mira
componentes `c < x`, que por hipotesis de induccion ya estan estabilizadas.
-/
theorem estabiliza {n : ℕ} {isJoinOf : Fin n → Option (List (Fin n))}
    (hac : Aciclico isJoinOf) :
    ∀ (m : ℕ) (x : Fin n), (x : ℕ) = m → ∀ k : ℕ, m < k →
      complexityOrderIter isJoinOf (k + 1) x =
      complexityOrderIter isJoinOf k x := by
  intro m
  induction m using Nat.strong_induction_on with
  | _ m ih =>
    intro x hxm k hk
    match k, hk with
    | (k + 1), hk =>
      rw [iter_succ, iter_succ]
      cases hj : isJoinOf x with
      | none => rfl
      | some comps =>
        dsimp only
        congr 1
        apply foldr_congr
        intro c hc
        have hcx : c < x := hac x comps hj c hc
        have h1 : (c : ℕ) < m := by omega
        exact ih (c : ℕ) h1 c rfl k (by omega)

/--
**Teorema (punto fijo).** Bajo aciclicidad, la iteracion alcanza punto fijo en
`n` rondas, que es lo que `apply_complexity_order` supone al parar ahi.
-/
theorem hierarchy_well_founded {n : ℕ}
    {isJoinOf : Fin n → Option (List (Fin n))} (hac : Aciclico isJoinOf) :
    ∀ x : Fin n,
      complexityOrderIter isJoinOf (n + 1) x =
      complexityOrderIter isJoinOf n x :=
  fun x => estabiliza hac (x : ℕ) x rfl n x.isLt

/--
**Teorema.** Bajo aciclicidad, el cn de un join es estrictamente mayor que el
de cada una de sus componentes.

Es el invariante que hace de `cn` una medida de complejidad: si no creciera al
unir, `max(cn) = 2` no significaria nada.
-/
theorem cn_join_gt_component {n : ℕ}
    {isJoinOf : Fin n → Option (List (Fin n))} (hac : Aciclico isJoinOf)
    (x : Fin n) (comps : List (Fin n))
    (hx : isJoinOf x = some comps)
    (c : Fin n) (hc : c ∈ comps) :
    complexityOrderIter isJoinOf n c <
    complexityOrderIter isJoinOf (n + 1) x := by
  have hcx : c < x := hac x comps hx c hc
  rw [iter_succ, hx]
  dsimp only
  have : complexityOrderIter isJoinOf n c ≤
      comps.foldr (fun c acc => max (complexityOrderIter isJoinOf n c) acc) 0 :=
    foldr_ge _ _ hc
  -- `omega` no descompone `1 + foldr ...` porque trata el foldr como atomo;
  -- aislado como enunciado sobre un natural cualquiera si lo resuelve.
  have h1 : ∀ m : ℕ, m < 1 + m := fun m => by omega
  exact Nat.lt_of_le_of_lt this (h1 _)


/-! ## §6  Varias descomposiciones por objeto -/

/-
El Principio de Multiplicidad exige que un objeto tenga MAS DE UNA
descomposicion. Pero `complexityOrderIter` toma `isJoinOf : Fin n → Option
(List (Fin n))`, una funcion: como mucho una descomposicion por objeto.

Al habilitar MP en el sistema eso deja de valer, y el codigo dejo de converger:
hacia `cn[j] = 1 + max(componentes)` por ASIGNACION, de modo que con dos
descomposiciones de alturas distintas oscilaba entre ambas indefinidamente.

La generalizacion correcta es tomar el MAXIMO sobre todas las descomposiciones.
Asi la sucesion es monotona no decreciente, y de ahi sale la terminacion.
-/

/-- Iteracion con varias descomposiciones por objeto. -/
def multiIter {n : ℕ} (decomps : Fin n → List (List (Fin n))) :
    ℕ → (Fin n → ℕ)
  | 0     => fun _ => 0
  | k + 1 =>
    let prev := multiIter decomps k
    fun x => (decomps x).foldr
      (fun comps acc =>
        max (1 + comps.foldr (fun c a => max (prev c) a) 0) acc) 0

theorem multiIter_succ {n : ℕ} (decomps : Fin n → List (List (Fin n)))
    (k : ℕ) (x : Fin n) :
    multiIter decomps (k + 1) x =
      (decomps x).foldr
        (fun comps acc =>
          max (1 + comps.foldr (fun c a => max (multiIter decomps k c) a) 0) acc)
        0 :=
  rfl

/-- Aciclicidad para varias descomposiciones. -/
def AciclicoMulti {n : ℕ} (decomps : Fin n → List (List (Fin n))) : Prop :=
  ∀ x comps, comps ∈ decomps x → ∀ c ∈ comps, c < x

/-- Congruencia del foldr exterior, para poder sustituir bajo el maximo. -/
theorem foldrOut_congr {n : ℕ} {p q : Fin n → ℕ} (ds : List (List (Fin n)))
    (h : ∀ comps ∈ ds, ∀ c ∈ comps, p c = q c) :
    ds.foldr (fun comps acc =>
        max (1 + comps.foldr (fun c a => max (p c) a) 0) acc) 0 =
    ds.foldr (fun comps acc =>
        max (1 + comps.foldr (fun c a => max (q c) a) 0) acc) 0 := by
  induction ds with
  | nil => rfl
  | cons a t ih =>
    simp only [List.foldr_cons]
    rw [foldr_congr a (h a List.mem_cons_self)]
    exact congrArg _ (ih fun comps hc => h comps (List.mem_cons_of_mem a hc))

/--
**Teorema (estabilizacion con varias descomposiciones).**

Bajo aciclicidad, el valor de `x` deja de cambiar a partir de la ronda `x + 1`,
igual que en el caso de una sola descomposicion. La demostracion es la misma
induccion fuerte; lo unico que cambia es que la congruencia se aplica al foldr
exterior.
-/
theorem estabilizaMulti {n : ℕ} {decomps : Fin n → List (List (Fin n))}
    (hac : AciclicoMulti decomps) :
    ∀ (m : ℕ) (x : Fin n), (x : ℕ) = m → ∀ k : ℕ, m < k →
      multiIter decomps (k + 1) x = multiIter decomps k x := by
  intro m
  induction m using Nat.strong_induction_on with
  | _ m ih =>
    intro x hxm k hk
    match k, hk with
    | (k + 1), hk =>
      rw [multiIter_succ, multiIter_succ]
      apply foldrOut_congr
      intro comps hcomps c hc
      have hcx : c < x := hac x comps hcomps c hc
      have h1 : (c : ℕ) < m := by omega
      exact ih (c : ℕ) h1 c rfl k (by omega)

/-- **Corolario.** Punto fijo en `n` rondas, tambien con varias descomposiciones. -/
theorem hierarchy_well_founded_multi {n : ℕ}
    {decomps : Fin n → List (List (Fin n))} (hac : AciclicoMulti decomps) :
    ∀ x : Fin n, multiIter decomps (n + 1) x = multiIter decomps n x :=
  fun x => estabilizaMulti hac (x : ℕ) x rfl n x.isLt

/--
**Teorema.** El cn de un objeto domina al de las componentes de CADA una de sus
descomposiciones, no solo de una.

Es lo que justifica tomar el maximo: si se tomara una descomposicion cualquiera,
las componentes de las otras podrian quedar por encima.
-/
theorem cn_ge_of_mem_decomp {n : ℕ}
    (decomps : Fin n → List (List (Fin n))) (k : ℕ)
    (x : Fin n) (comps : List (Fin n)) (hcomps : comps ∈ decomps x)
    (c : Fin n) (hc : c ∈ comps) :
    multiIter decomps k c < multiIter decomps (k + 1) x := by
  rw [multiIter_succ]
  have hin : multiIter decomps k c ≤
      comps.foldr (fun c a => max (multiIter decomps k c) a) 0 :=
    foldr_ge _ _ hc
  -- el maximo exterior domina al sumando de esta descomposicion
  have hout : ∀ (ds : List (List (Fin n))), comps ∈ ds →
      1 + comps.foldr (fun c a => max (multiIter decomps k c) a) 0 ≤
      ds.foldr (fun cs acc =>
        max (1 + cs.foldr (fun c a => max (multiIter decomps k c) a) 0) acc) 0 := by
    intro ds hds
    induction ds with
    | nil => cases hds
    | cons a t ih =>
      simp only [List.foldr_cons]
      rcases List.mem_cons.mp hds with rfl | ht
      · exact le_max_left _ _
      · exact le_trans (ih ht) (le_max_right _ _)
  have h1 : ∀ m : ℕ, m < 1 + m := fun m => by omega
  exact Nat.lt_of_le_of_lt hin
    (Nat.lt_of_lt_of_le (h1 _) (hout (decomps x) hcomps))


structure ComplexityCertificate (n : ℕ) where
  /-- The computed complexity order for each skill index. -/
  cn          : Fin n → ℕ
  /-- For each skill: optionally, the list of component indices
      (if the skill is the join of a pattern). -/
  isJoinOf    : Fin n → Option (List (Fin n))
  /-- The cn values match the fixpoint computation. -/
  consistent  : ∀ x : Fin n, cn x = complexityOrder isJoinOf x
  /-- Stacked cocones commute for any semilattice with bottom (free from Fubini).
      Stated universally over α so it doesn't require OrderBot (Fin n).
      DecidableEq α needed for Finset.biUnion in Lean 4.29+. -/
  stacked_commute : ∀ {α : Type*} [SemilatticeSup α] [OrderBot α] [DecidableEq α]
      (S : Finset (Finset α)),
      S.sup (fun t => t.sup id) = (S.biUnion id).sup id :=
    fun S => fubini_joins S
  /-- All diagrams commute (free from thin-category property). -/
  diagrams_commute : ∀ (a b : Fin n) (h₁ h₂ : a ≤ b), h₁ = h₂ :=
    fun _ _ h₁ h₂ => thin_unique_hom h₁ h₂
