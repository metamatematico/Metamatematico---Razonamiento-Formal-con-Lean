# Curación pendiente — veredicto sobre los diez

Verificado contra Mathlib4, commit `17019dc` (14 sep 2026). Las líneas citadas están leídas de la
declaración en el árbol, no deducidas de la ruta.

---

## El resultado

Los diez se quedan fuera. Esa parte está bien y no hay que tocar ni un nodo.

Lo que no está bien son nueve de las diez razones. En una hoja que se regenera sola, la razón es lo
único que viaja al futuro: la decisión ya la tomó la medición, pero la razón es la que va a decidir
el próximo módulo parecido. Tu §1 define **T** como «ni objetos ni flechas»; nueve de estos diez
tienen objetos, y uno de ellos tiene además flechas, identidad y composición declaradas en el
propio fichero.

| módulo | marca | mi marca | evidencia leída |
|---|---|---|---|
| `AlgebraicTopology.SimplexCategory.GeneratorsRelations.Basic` | T | **ALIAS** | `def SimplexCategoryGenRel := Quotient FreeSimplexQuiver.homRel` (75); `def toSimplexCategory : SimplexCategoryGenRel ⥤ SimplexCategory` (250) |
| `Computability.AkraBazzi.SumTransform` | T | **HUÉRFANO** | `structure AkraBazziRecurrence` (60), en ese mismo fichero |
| `Control.Bitraversable.Basic` | T | **POLÍTICA** | `class Bitraversable (t : Type u → Type u → Type u)` (48) |
| `Control.Fix` | T | **POLÍTICA** | `class Fix (α : Type*)` (35) |
| `Control.Functor.Multivariate` | T | **POLÍTICA** | `class MvFunctor {n : ℕ} (F : TypeVec n → Type*)` (32) |
| `Control.Monad.Cont` | T | **POLÍTICA** | `class MonadCont` (33); `def ContT` (48) |
| `Data.TypeVec` | T | **POLÍTICA** | `def TypeVec` (41), `def Arrow` (52) con notación `⟹`, `def id` (71), y composición |
| `Order.PFilter` | T | **HUÉRFANO** | `structure PFilter (P) [Preorder P]` (45); `instance : PartialOrder (PFilter P)` (77) |
| `SetTheory.Ordinal.Notation` | T | **ALIAS** | `inductive ONote` (40); `repr : ONote → Ordinal` (69); `NONote` (1129) |
| `Topology.Category.TopCat.Basic` | CUBIERTO | CUBIERTO | `structure TopCat` (32) |

---

## Los cuatro motivos que T está mezclando

Cada uno tiene un disparador de revisión distinto, y esa es toda la diferencia: T es la marca que
no se revisa nunca, así que archivar bajo T algo que sí hay que revisar equivale a perderlo.

| motivo | qué es | cuándo se revisa |
|---|---|---|
| **ALIAS** | una presentación del objeto de un nodo que ya existe | si cambia el nodo padre |
| **HUÉRFANO** | objeto legítimo cuyo área no está en el grafo | si entra el área |
| **POLÍTICA** | tiene objetos, pero es metalenguaje y su vocabulario es caro | nunca, salvo decisión explícita |
| **T** | ni objetos ni flechas | nunca |

### ALIAS — dos presentaciones

`SimplexCategoryGenRel` y `ONote` son presentaciones: una por generadores y relaciones, la otra
por forma normal de Cantor. En ninguno de los dos casos la relación con el objeto ya existente es
la identidad: es una flecha canónica de evaluación, `toSimplexCategory` y `repr`. Por tu propia
convención eso va en el campo `lean` del nodo, igual que `TopCat` en `point-set-topology`. Es la
decisión de la última fila de la hoja, escrita con la marca de otra.

Un aviso sobre la primera: **no encontré probada en Mathlib la equivalencia
`SimplexCategoryGenRel ≌ SimplexCategory`**, solo el funtor de comparación y las piezas que
llevarían a ella (`EpiMono.lean`, `NormalForms.lean`). Mientras no esté, «la misma categoría con
otro nombre» es una conjetura y no un hecho verificado, y el alias apunta a través de un funtor
del que aún no se sabe que sea equivalencia.

### HUÉRFANO — dos objetos sin padre

En la celda de `PFilter` ya habías escrito la razón correcta —«sin padre la arista no
existiría»— y luego la archivaste bajo T. El día que entre la teoría de órdenes, nadie va a releer
la lista de los T.

Y el área ya está medio dentro sin nombre: `divisibility-gcd`, `subgroups-cosets` e
`ideals-quotient-rings` son retículos y preórdenes, tres nodos huérfanos del mismo padre ausente.
Es el tercer vértice que falta, después de la categoría derivada y los espacios anillados.

`AkraBazzi.SumTransform` es huérfano por lo mismo, no T: el objeto está declarado y lo que falta es
el padre, porque `algorithm-analysis` es T en el veredicto de las 172. La analogía con
`prime-factorization` no se sostiene: aquél es un teorema sin estructura empaquetada, éste empaqueta
la recurrencia con sus hipótesis en un `structure`.

### POLÍTICA — los cinco de efectos

No están fuera por no tener objetos: los tienen. Están fuera porque son metalenguaje y porque su
vocabulario es caro, que es tu propio hallazgo medido. `Control.Fix` aporta el token `fix`,
`Control.Monad.Cont` aporta `cont`, `Data.TypeVec` aporta `type`, `Control.Functor.Multivariate`
aporta `functor`: son exactamente el fallo de `different-ideal`, y de los peores, porque salen en
media biblioteca y gastarían una de las dos plazas sin aportar nada.

La puerta que ya construiste los para sin necesidad de prohibirlos: solo se ocupa plaza con una
keyword declarada. Basta con no declararles ninguna y dejar escrito que ésa es la razón.

`Data.TypeVec` merece una nota aparte, porque es el caso que refuta la marca de manera más
directa: define objetos, flechas con notación propia, identidad y composición. Sea cual sea el
motivo para dejarlo fuera, «ni objetos ni flechas» no puede serlo.

### T — ninguno

Estrictamente, de los diez no queda ninguno en T.

---

## Un aviso para el día que entre `PFilter`

Su token es `filter`, que en Mathlib está entre los más frecuentes que existen. Si entra sin
keyword declarada bajará la precisión, y la causa no será el veredicto sino la plaza, igual que
pasó con `different`.

---

## Lo que cambia en el script

Una sola cosa: la tabla de decisiones pasa de un valor a dos —marca y motivo de exclusión— con los
motivos `alias`, `huérfano`, `política` y `T`.

Los nueve reetiquetados no mueven ningún nodo del grafo, no tocan la línea base de 22,8 % / 18,0 %
y no obligan a recalcular nada. Sirven para que la hoja siga diciendo la verdad cuando la medición
destape módulos nuevos, que es para lo que la escribiste.
