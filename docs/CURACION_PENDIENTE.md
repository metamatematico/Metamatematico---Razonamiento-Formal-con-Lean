# Curación pendiente

> Generado por `scripts/hoja_de_curacion.py`. **No editar a mano**: se regenera.


**No queda nada pendiente.** Los 10 módulos que `lo_que_falta_emerge` seguía marcando «sin nodo» están todos decididos.

| módulo | decisión |
|---|---|
| `AlgebraicTopology.SimplexCategory.GeneratorsRelations.Basic` | T · es SimplexCategory presentada por generadores: la misma categoria con otro nombre, y dos nombres para un objeto gastan dos plazas |
| `Computability.AkraBazzi.SumTransform` | T · es el teorema de Akra-Bazzi y sus piezas de demostracion, no un objeto: el mismo caso que prime-factorization |
| `Control.Bitraversable.Basic` | T · interfaz de efectos de Lean: endofuntores sobre Type, y un lazo no es una dependencia |
| `Control.Fix` | T · Part.fix es el punto fijo con el que Lean define funciones parciales: maquinaria de definicion |
| `Control.Functor.Multivariate` | T · la misma rama de efectos |
| `Control.Monad.Cont` | T · la misma rama de efectos |
| `Data.TypeVec` | T · vectores de tipos para inductivos multivariados: infraestructura |
| `Order.PFilter` | T · un PFilter es un filtro sobre un preorden, pero `Order` no es area del grafo y un nodo solo no la justifica: sin padre la arista no existiria. Primer candidato si algun dia entra la teoria de ordenes |
| `SetTheory.Ordinal.Notation` | T · ONote y NONote son la forma normal de Cantor como dato computable: notacion, no objeto. El nodo `ordinals` ya existe |
| `Topology.Category.TopCat.Basic` | CUBIERTO · `TopCat` ya es la identidad de `point-set-topology`. La convencion del proyecto pone el envoltorio categorico en el campo `lean` del concepto (group-theory lleva GrpCat), no en un nodo aparte |

Nueve son marca `T` —ni objetos ni flechas, así que no entran— y uno ya está cubierto por un nodo existente. Siguen apareciendo como «sin nodo» en la medición, y es correcto: no hay nodo. Lo que no son es trabajo.

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
