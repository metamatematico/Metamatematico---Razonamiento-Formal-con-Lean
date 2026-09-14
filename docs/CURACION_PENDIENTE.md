# Curación pendiente

> Generado por `scripts/hoja_de_curacion.py`. **No editar a mano**: se regenera.


**No queda nada pendiente.** Los 10 módulos que `lo_que_falta_emerge` seguía marcando «sin nodo» están todos decididos.

**Fuera no es lo mismo que `T`.** La decisión —los diez fuera— la tomó la medición; el **motivo** es lo único que viaja al futuro, porque es lo que va a decidir el próximo módulo parecido. Cada uno tiene un **disparador de revisión distinto**, y `T` es la marca que no se revisa nunca: archivar bajo `T` algo que sí hay que revisar equivale a perderlo.

| motivo | qué es | cuándo se revisa |
|---|---|---|
| **alias** | una presentacion del objeto de un nodo que YA existe; su nombre va en el campo `lean` de ese nodo, no en uno nuevo | si cambia el nodo padre |
| **huerfano** | objeto legitimo cuya AREA no esta en el grafo: sin padre la arista no existiria y el nombre quedaria suelto | si entra el area |
| **politica** | TIENE objetos, pero es metalenguaje y su vocabulario es caro: sus tokens salen en media biblioteca | nunca, salvo decision explicita |
| **cubierto** | el nombre ya esta en el campo `lean` de un nodo: el alias ya aplicado | si cambia ese nodo |
| **T** | ni objetos ni flechas | nunca |

| módulo | motivo | por qué |
|---|---|---|
| `AlgebraicTopology.SimplexCategory.GeneratorsRelations.Basic` | **alias** | `SimplexCategoryGenRel` (linea 75) es SimplexCategory presentada por generadores y relaciones. AVISO: la equivalencia `SimplexCategoryGenRel ≌ SimplexCategory` NO esta probada en Mathlib —solo el funtor `toSimplexCategory` (251) y las piezas de EpiMono y NormalForms—, asi que «la misma categoria con otro nombre» es una conjetura, no un hecho verificado, y el alias apuntaria a traves de un funtor del que aun no se sabe que sea equivalencia |
| `SetTheory.Ordinal.Notation` | **alias** | `ONote` (40) y `NONote` (1129) son la forma normal de Cantor como dato computable, y `repr` (69) es la flecha canonica de evaluacion hacia `Ordinal`. NO es la identidad: es una presentacion del objeto del nodo `ordinals`, que ya existe |
| `Topology.Category.TopCat.Basic` | **cubierto** | `structure TopCat` (32) ya es la identidad de `point-set-topology`. La convencion del proyecto pone el envoltorio categorico en el campo `lean` del concepto (group-theory lleva GrpCat), no en un nodo aparte |
| `Computability.AkraBazzi.SumTransform` | **huerfano** | `structure AkraBazziRecurrence` (60) empaqueta la recurrencia con sus hipotesis: hay objeto. La analogia con `prime-factorization` NO se sostiene —aquel es un teorema sin estructura empaquetada—. Lo que falta es el padre: `algorithm-analysis` esta marcado T y sin nombre |
| `Order.PFilter` | **huerfano** | `PFilter` (45) es una estructura con `instance : PartialOrder` (77): objeto de pleno derecho. Lo que falta es el PADRE — no hay ni un concepto curado de teoria de ordenes, solo nodos generados y el area. Y el area ya esta medio dentro sin nombre: `divisibility-gcd`, `subgroups-cosets` e `ideals-quotient-rings` son reticulos y preordenes colgando de otro sitio. AVISO PARA CUANDO ENTRE: su token es `filter`, de los mas frecuentes de Mathlib; sin keyword declarada bajaria la precision como hizo `different` |
| `Control.Bitraversable.Basic` | **politica** | `class Bitraversable` (48) es un objeto. Fuera por metalenguaje: es la interfaz de efectos de Lean |
| `Control.Fix` | **politica** | `class Fix` (35) es un objeto. Fuera porque su token seria `fix`, que sale en media biblioteca |
| `Control.Functor.Multivariate` | **politica** | `class MvFunctor` (32) es un objeto. Su token seria `functor` |
| `Control.Monad.Cont` | **politica** | `class MonadCont` (33) y `def ContT` (48) son objetos. Su token seria `cont` |
| `Data.TypeVec` | **politica** | EL CASO QUE REFUTA LA MARCA DE FRENTE: define objetos (`TypeVec`, 41), flechas con notacion propia (`Arrow`, 52, con `⟹`), identidad (`id`, 71) y composicion. Fuera por metalenguaje y porque su token seria `type`. La puerta de las plazas ya lo para sin prohibirlo: no se le declara ninguna keyword, y esa es la razon |

Reparto: 2 alias, 1 cubierto, 2 huerfano, 5 politica. **Ninguno queda en `T`** — nueve de los diez declaran objetos, y `Data.TypeVec` declara además flechas, identidad y composición en el propio fichero. Siguen apareciendo como «sin nodo» en la medición, y es correcto: no hay nodo. Lo que no son es trabajo.

Si mañana la medición destapa módulos nuevos, esta hoja vuelve a llenarse sola.

---

## Qué hay que decidir en cada uno

**1 · La marca.** Es lo que sostiene el grafo y no lo decide nada automático:

| | | |
|---|---|---|
| `C` | una categoría | **vértice** |
| `S` | una subcategoría plena | **vértice**, y la inclusión es arista |
| `F` | un funtor o clase de flechas | **arista** *en este ambiente* |
| `O` | un objeto individual | vértice degenerado |
| `T` | ni objetos ni flechas | **fuera** |

`F` **no** dice «esto no puede ser un vértice nunca». Eso es falso, y está demostrado que lo es en `FlechasComoObjetos.lean`: las flechas de `C` son exactamente los objetos de `Arrow C`, y los funtores son los objetos de `C ⥤ D`. Lo que dice es que **en este grafo** —cuyos objetos son conceptos y cuyas flechas son dependencias— la etiqueta nombra una flecha.

`homology` es `F`: aquí no es una colección que se pueda colimitar, es el funtor *a lo largo del cual* se colimita. `prime-factorization` es `T`: es un teorema, no un objeto.

**2 · El padre.** De qué concepto es especialización. La flecha va del general al específico.

**3 · Cuál de los nombres.** Que exista no lo hace correcto: `Nat.Prime` es la noción de primo, `Nat.minFac` no.

Lo que **no** hay que decidir, porque ya está verificado: si el nombre existe, en qué módulo vive, cuál es el canónico (las citas) y el DAG de imports.

---

---

## Antes de dar por buena una tanda

```
python -m scripts.recuperacion_contra_proofnet
```

Precisión y cobertura contra 371 formalizaciones de oro, con su modelo nulo y sin gastar API.

**Baseline hoy: 22,8 % / 18,0 % contra 1,45 % / 3,3 % — 15,7×.** Si la precisión baja, esa tanda no entra.

Y la regla tiene una letra pequeña que costó descubrir. La primera tanda de 31 nodos **bajaba la precisión a 19,9 %** sin mover la cobertura, y la causa no era ningún veredicto equivocado —los 47 nombres los acepta `#check`— sino que el emparejador tokeniza el **id y el nombre** de cada nodo: `different-ideal` aportaba el token `different`, que sale en media biblioteca, y con eso gastaba una de las dos plazas del prompt. La puerta que lo arregla —*sólo se ocupa plaza con una keyword declarada*— subió la línea base de 21,3 % a 22,8 %. Si una tanda baja la precisión, mira primero si sus nodos entran en plaza por su nombre.

Ya pasó: ofrecer los sustantivos de los nodos generados bajaba de 14,0 % a 11,5 %. Añadir vocabulario tiene coste.
