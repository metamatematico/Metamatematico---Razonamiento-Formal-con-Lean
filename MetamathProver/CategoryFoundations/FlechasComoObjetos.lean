/-
# Una flecha puede ser un objeto: la marca `F` es RELATIVA AL AMBIENTE

## El problema que este archivo corrige

`nucleo/graph/interpretacion.py` clasifica cada etiqueta del grafo con una
marca, y la documenta así:

    F   un funtor, una construcción o una clase de flechas  ->  ARISTA, no vértice

Dicho sin más, eso es **falso como principio**. Hay categorías cuyos objetos
son flechas, y categorías cuyos objetos son funtores:

* la **categoría de flechas** `Arrow C`: sus objetos son los morfismos de `C`,
  y sus morfismos son cuadrados conmutativos;
* la **categoría de funtores** `C ⥤ D`: sus objetos son funtores, y sus
  morfismos son transformaciones naturales.

Así que «ser flecha» no es una propiedad de la cosa: es una propiedad de la
cosa **en un ambiente**. `homology` es un morfismo en la categoría de
complejos, y es un objeto en la categoría de funtores donde vive. Las dos
lecturas son correctas y no se contradicen — hablan de categorías distintas.

Este archivo lo demuestra, en vez de argumentarlo, y da la generalización:
ambas son casos de la **categoría coma**.

## Qué NO dice

No dice que la marca `F` esté mal puesta. Dice que está puesta **respecto de
un ambiente que el grafo no declara**. El proyecto ya sabía que el ambiente
manda —está escrito que `metric-spaces` con contracciones tiene colímites que
no tiene con continuas— y esto es el mismo hecho en otro sitio.

Sin `sorry`.
-/
import Mathlib.CategoryTheory.Comma.Arrow
import Mathlib.CategoryTheory.Functor.Category
import Mathlib.CategoryTheory.Comma.Basic
-- OJO: `Mathlib.CategoryTheory.Types` ya no existe con ese nombre; la
-- instancia `LargeCategory (Type u)` vive en `...Types.Basic`. Es el mismo
-- fallo que el sistema comete con los usuarios: un modulo plausible que no
-- esta, y Lean dice «object file does not exist», no «no existe el modulo».
import Mathlib.CategoryTheory.Types.Basic

namespace MetamathProver.FlechasComoObjetos

open CategoryTheory

universe v₁ v₂ u₁ u₂

variable {C : Type u₁} [Category.{v₁} C]
variable {D : Type u₂} [Category.{v₂} D]

/-! ## 1 · Los objetos de `Arrow C` SON las flechas de `C` -/

/-- De cada flecha de `C` sale un objeto de `Arrow C`. Esto es lo que hace
falsa la lectura absoluta de la marca `F`: la misma cosa que allí es un
morfismo, aquí es un vértice. -/
def objetoDesdeFlecha {X Y : C} (f : X ⟶ Y) : Arrow C := Arrow.mk f

/-- Y el objeto RECUERDA su flecha: no se pierde nada al cambiar de ambiente.
La correspondencia flecha ↦ objeto es fiel en los tres componentes. -/
theorem objetoDesdeFlecha_recuerda {X Y : C} (f : X ⟶ Y) :
    (objetoDesdeFlecha f).left = X ∧ (objetoDesdeFlecha f).right = Y := by
  exact ⟨rfl, rfl⟩

/-- El componente `hom` del objeto es, literalmente, la flecha de partida. -/
theorem objetoDesdeFlecha_hom {X Y : C} (f : X ⟶ Y) :
    (objetoDesdeFlecha f).hom = f := rfl

/-- Y al revés: todo objeto de `Arrow C` ES una flecha de `C`. La
correspondencia va en los dos sentidos, así que «objetos de Arrow C» y
«flechas de C» es la misma colección. -/
theorem todo_objeto_es_flecha (a : Arrow C) :
    ∃ (X Y : C) (f : X ⟶ Y), Arrow.mk f = a :=
  ⟨a.left, a.right, a.hom, rfl⟩

/-! ## 2 · Los morfismos de `Arrow C` son cuadrados conmutativos -/

/-- Un morfismo de `Arrow C` conmuta. Es la condición que hace de `Arrow C`
una categoría y no una colección suelta de flechas. -/
theorem morfismo_conmuta {a b : Arrow C} (φ : a ⟶ b) :
    a.hom ≫ φ.right = φ.left ≫ b.hom := by
  simpa using (Arrow.w φ).symm

/-- La identidad de un objeto de `Arrow C`, que existe porque `Arrow C` es una
categoría de pleno derecho. -/
example (a : Arrow C) : a ⟶ a := 𝟙 a

/-! ## 3 · Los objetos de `C ⥤ D` son FUNTORES, y sus morfismos
     transformaciones naturales

Este es el caso que importa para el grafo: `homology`, `tensor-products`,
`localization` están marcados `F` porque son funtores. En la categoría de
funtores son objetos. -/

/-- Un funtor es un objeto de la categoría de funtores. -/
def objetoDesdeFuntor (F : C ⥤ D) : C ⥤ D := F

/-- Y los morfismos ENTRE funtores son exactamente las transformaciones
naturales: el tipo de morfismos de `C ⥤ D` es `NatTrans`. -/
theorem morfismos_son_transformaciones_naturales (F G : C ⥤ D) :
    (F ⟶ G) = NatTrans F G := rfl

/-- Una transformación natural da un morfismo de la categoría de funtores, y
la componente en cada objeto se recupera. -/
theorem natTrans_da_morfismo {F G : C ⥤ D} (α : NatTrans F G) (X : C) :
    (α : F ⟶ G).app X = α.app X := rfl

/-! ## 4 · La generalización: ambas son categorías coma

`Arrow C` no es un caso especial inventado: es `Comma (𝟭 C) (𝟭 C)`. La
categoría coma es la construcción de la que salen la categoría de flechas, las
rebanadas `Over`/`Under` y muchas más. Eso es lo que el usuario señalaba con
«y eso se puede generalizar». -/

/-- `Arrow C` es, por definición en Mathlib, la categoría coma de la identidad
consigo misma. La igualdad es literal: `rfl` la cierra. -/
theorem arrow_es_coma : Arrow C = Comma (𝟭 C) (𝟭 C) := rfl

/-- Un objeto de una categoría coma tiene también sus dos extremos y su
flecha: la misma forma que `Arrow`, con dominios distintos. -/
example {A B : Type u₁} [Category.{v₁} A] [Category.{v₁} B]
    (L : A ⥤ C) (R : B ⥤ C) (x : Comma L R) :
    L.obj x.left ⟶ R.obj x.right := x.hom

/-! ## 5 · El enunciado que corrige el criterio del grafo

Lo de arriba, junto. El primer intento de escribir esto fue

    ∃ a : Arrow C, a.hom = f ∧ a.left = X ∧ a.right = Y

y Lean lo rechazó: `a.hom` vive en `a.left ⟶ a.right`, y mientras no se sepa
que `a.left = X` esa ecuación ni siquiera tipa. El rechazo tiene contenido:
obliga a decir la cosa correcta, que no es «existe un objeto que es esta
flecha» sino que las dos COLECCIONES coinciden. -/

/-- **Las flechas de `C` son exactamente los objetos de `Arrow C`.** No es una
analogía ni una codificación con pérdida: es una biyección, y sus dos
composiciones son la identidad por definición (`rfl` en ambos lados).

Este es el enunciado que hace relativa la marca `F` del grafo: la misma
colección es «las flechas» en un ambiente y «los objetos» en otro. -/
def flechasSonObjetos : (Σ X : C, Σ Y : C, X ⟶ Y) ≃ Arrow C where
  toFun p := Arrow.mk p.2.2
  invFun a := ⟨a.left, a.right, a.hom⟩
  left_inv _ := rfl
  right_inv _ := rfl

/-- El ambiente en el que una flecha es objeto es una categoría de pleno
derecho, no una colección suelta: tiene identidades y composición. -/
example : Category (Arrow C) := inferInstance

/-- **Un funtor es un objeto de alguna categoría**, y esa categoría es la de
funtores: su tipo de objetos ES `C ⥤ D`, sin codificación de por medio. Es el
caso que le toca al grafo — `homology`, `localization`, `tensor-products`
están marcados `F` por ser funtores, y aquí son vértices. -/
example : Category (C ⥤ D) := inferInstance

/-! ## 6 · Un ejemplo concreto: `Set^→`

El que motivó todo esto. En `Type`, una función es un objeto de `Arrow Type`.
-/

/-- Una función entre tipos, vista como objeto de la categoría de flechas. -/
def funcionComoObjeto {X Y : Type u₁} (f : X → Y) : Arrow (Type u₁) :=
  Arrow.mk f

/-- Y sigue siendo la misma función. -/
theorem funcionComoObjeto_hom {X Y : Type u₁} (f : X → Y) :
    (funcionComoObjeto f).hom = f := rfl

/-- `Arrow (Type u)` es una categoría: tiene identidades y composición. Que
esto tipe es la afirmación. -/
example (a : Arrow (Type u₁)) : a ⟶ a := 𝟙 a

example {a b c : Arrow (Type u₁)} (φ : a ⟶ b) (ψ : b ⟶ c) : a ⟶ c := φ ≫ ψ

end MetamathProver.FlechasComoObjetos
