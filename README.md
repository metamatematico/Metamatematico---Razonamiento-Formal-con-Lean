# METAMATEMÁTICO — Razonamiento Formal con Lean 4

[![Lean 4](https://img.shields.io/badge/Lean-4-blue.svg)](https://lean-lang.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://python.org/)
[![Tests](https://img.shields.io/badge/Tests-1089_passing-brightgreen.svg)](#7-tests-y-guardianes)
[![Fidelidad](https://img.shields.io/badge/Banco_de_fidelidad-8%2F8_medidos-brightgreen.svg)](#6-lo-que-está-medido)
[![Hechos](https://img.shields.io/badge/Hechos_indexados-183_433-8b5cf6.svg)](#4-la-lista-183-433-hechos)
[![Grafo](https://img.shields.io/badge/Grafo-352_nodos-8b5cf6.svg)](#3-el-grafo-de-qué-consta)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Leonardo Jiménez Martínez · BIOMAT · Centro de Biomatemáticas**

Una IA matemática que **no confía en el modelo de lenguaje para decidir si algo
es cierto**. El LLM formaliza en Lean 4, el kernel verifica, y sólo entonces se
traduce el resultado.

Alrededor de esa cadena hay **dos capas de conocimiento** con trabajos
distintos: un grafo pequeño y curado que dice *de qué habla* algo, y una lista
grande y extraída de Mathlib que dice *qué es cierto*. Ninguna de las dos
decide la verdad — eso es Lean, siempre.

> **Documentación visual completa** — [Metamatemático por dentro](https://claude.ai/code/artifact/8907db6a-017e-41ff-a434-b1eaf4ac0631):
> las dos capas, el grafo dibujado, lo que está medido, **lo que se midió y no
> sirve**, y los doce instrumentos rotos que hubo que cazar por el camino.
> Fuente en [`docs/arquitectura_nle.html`](docs/arquitectura_nle.html).

---

## Índice

1. [El flujo, de la entrada a la salida](#1-el-flujo-de-la-entrada-a-la-salida)
2. [Las dos capas](#2-las-dos-capas)
3. [El grafo: de qué consta](#3-el-grafo-de-qué-consta)
4. [La lista: 183 433 hechos](#4-la-lista-183-433-hechos)
5. [Lean: cuatro caminos, ocho veredictos](#5-lean-cuatro-caminos-ocho-veredictos)
6. [Lo que está medido](#6-lo-que-está-medido)
7. [Tests y guardianes](#7-tests-y-guardianes)
8. [Lo que se midió y no sirve](#8-lo-que-se-midió-y-no-sirve)
9. [Instalación y uso](#9-instalación-y-uso)
10. [Estructura del repositorio](#10-estructura-del-repositorio)
11. [Lo que no está](#11-lo-que-no-está)

---

## 1. El flujo, de la entrada a la salida

Todo pasa por `Nucleo.process(texto)`. **Los alumnos preguntan en español y
todo el aparato es inglés**, así que el flujo empieza y acaba en una frontera de
idioma.

<p align="center">
  <img src="docs/img/00-flujo-real.svg" alt="Flujo del sistema de la entrada a la salida. La consulta entra en español o en inglés y cruza la frontera del idioma: si viene en español se traduce al inglés con un modelo local protegiendo la notación, y el inglés pasa directo. Después pasa por un clasificador que decide si es matemática; si no lo es va al LLM conversacional, que responde sin verificación formal. Si lo es, el grafo aporta al prompt los conceptos activados con sus nombres de Mathlib verificados. El LLM formaliza. Antes de verificar, el grafo elige los módulos de Mathlib que Lean importará. Lean verifica y abre cuatro caminos: si falta un módulo se repara el encabezado y se reintenta una vez; si el error es semántico el error vuelve al modelo, máximo dos rondas; si queda un sorry entra la cascada de tácticas del grafo; y si Lean acepta se pasa directo al veredicto. Los caminos confluyen en un veredicto final de siete estados, que el LLM traduce antes de la respuesta, con el veredicto siempre delante del texto." width="100%">
</p>

| paso | quién | qué hace | ¿aporta? |
|---|---|---|---|
| 1 | **grafo** | nombres de Mathlib verificados al prompt | **sí — 15,7× sobre el azar** |
| 2 | LLM | escribe Lean 4 — no juzga si es correcto | — |
| 3 | **grafo** | elige qué módulos importa Lean | **inerte** |
| 4 | **Lean** | verifica · su veredicto es inapelable | — |
| 5 | **grafo** | ordena las tácticas si queda un `sorry` | **no bate al nulo** |
| 6 | LLM | traduce el código que Lean aceptó | — |

La última columna sale de medir cada punto por separado. **No hay un veredicto
único sobre «el núcleo»**: aporta en **uno** de sus tres puntos de actuación, es
inerte en otro, y en el tercero **no bate a su modelo nulo**. El detalle está en la [sección 6](#6-lo-que-está-medido) y los
negativos en la [8](#8-lo-que-se-midió-y-no-sirve).

### La frontera del idioma

Los seis pasos no llevan idioma propio: **lo llevan sus datos, y son todos
ingleses** — las 4 302 palabras clave del grafo, los 183 433 hechos de Mathlib,
los ejemplos few-shot de miniF2F y el propio Lean. Un alumno que escribe
«¿Es 17 un número primo?» no toca ninguna de esas palabras.

Así que la consulta se traduce **una vez, al entrar**, con un modelo local
(`Helsinki-NLP/opus-mt-es-en`, 74 M de parámetros, sin API), y el inglés pasa
directo.

```
                            antes    después
activan alguna skill         9/24      11/24     ← 24 consultas reales
abren alguna área            3/24       9/24
```

**La notación se protege, y no era opcional.** Medido sobre el modelo desnudo:

```
$x^2 - 5x + 6$          →  $x^2 - 5x + $6
\mathbb{R}$             →  \mathbb{R$
\int_0^\infty ... dx$   →  int_0=infty ... dx$    (destruido)
\sin x                  →  \without x
```

El último lo explica todo: `\sin` es el seno, y «sin» en español es una
preposición. Se saca la notación, se sustituye por marcas que sobreviven al
tokenizador, y se devuelve a su sitio.

**Y la frontera se cruza de vuelta.** Si preguntó en español, la respuesta sale
en español — hay que fijarlo en el prompt, porque el enunciado que el modelo
tiene delante ya está en inglés y una instrucción como «responde en el mismo
idioma que el usuario» le haría contestar en inglés. Lo que se le enseña como
«pregunta original» es **la suya**, no la traducción, y el historial guarda lo
que él escribió.

---

## 2. Las dos capas

|  | el grafo | la lista |
|---|---|---|
| **qué guarda** | conceptos — *de qué habla* | hechos — *qué es cierto* |
| **tamaño** | 352 nodos | 183 433 entradas |
| **cómo se hizo** | 205 a mano + 125 generados | extraída del fuente, entera |
| **¿puede equivocarse?** | **sí** — es curación humana | no sobre sí misma |
| **estructura** | categórica: colímites, orden, pilares | plana, indexada |
| **en el flujo** | pasos 1, 3 y 5 — *el 3 reusa el emparejamiento del 1* | alimenta el índice de premisas, y se alcanza por `classify_query`, **no** por el grafo |

**El puente existe en los datos, pero no está tendido en el código.** Cada
hecho de la lista lleva su `concepto` —`Algebra.Order`, `Data.Set`— y ésos son
exactamente los identificadores de los 125 nodos generados. La correspondencia
no hay que inventarla: está en la ruta del módulo.

Pero en el runtime **las dos capas no se hablan**. Medido: `nucleo/lean/premisas.py`
tiene *cero* menciones del grafo. Su único parámetro de contexto es un nombre de
área, y ese nombre sale de `classify_query()` — un clasificador de palabras clave
que no toca el grafo en ningún punto.

Y **tenderlo al grafo lo empeoraría**, que es la parte que no era obvia. Medido
sobre 3 000 consultas etiquetadas, con su modelo nulo al lado:

| | exactitud cruda | exactitud equilibrada |
|---|---|---|
| `classify_query` | 61,2 % | **58,7 %** |
| área de la 1ª skill del grafo | 34,3 % | 40,9 % |
| *nulo: responder siempre «algebra», sin leer el enunciado* | *88,6 %* | *33,3 %* |

El nulo es la fila que hay que mirar primero, y durante meses no estuvo puesta:
**el banco es 89 % `algebra`**, así que una constante gana a las dos medidas en
crudo. La cifra que dice algo es la equilibrada —la media de los aciertos
dentro de cada área—, donde el nulo se hunde al 33,3 % y `classify_query` se
pone veinticinco puntos por encima.

La conclusión no cambia, se refuerza: conectar la lista al grafo sería cambiar
el clasificador bueno por el malo, y con la medida honesta la distancia entre
los dos es *mayor* (58,7 contra 40,9), no menor. Lo que falta no es el cable,
es un motivo medido para tenderlo.

### Por qué hacen falta las dos

Medido: de los 169 nombres que el grafo inyecta hoy, **3 son teoremas o lemas y
166 son tipos, estructuras y clases**. El grafo da los sustantivos.

Y ahí no es donde el modelo falla. De los 28 nombres que propuso de memoria, los
21 inexistentes eran *todos* lemas — `tsum_geometric_two`, `Subgroup.isCyclic`,
`isOpen_union`. El modelo acierta razonablemente los sustantivos e inventa los
hechos. **La lista existe para cubrir esa mitad.**

Y la otra mitad estaba casi vacía. El extractor de hechos justificaba dejar
fuera `def`, `structure` y `class` con «son sustantivos y *ya los cubre el
grafo*». Contado sobre el fuente: Mathlib tiene **34 084 sustantivos** y el
grafo inyecta 169 — el **0,50 %**. La frase estaba equivocada por un factor de
200, justo en la mitad donde el reparto dice que el grafo aporta.

`data/sustantivos_mathlib.jsonl` la construye, y los nombres se **leen de la
declaración** en vez de deducirse de la ruta: `#check` sobre una muestra da
**200 de 200 existentes**, frente al 77,4 % de los deducidos. Lo que no
funciona es la vía de inyectarlos — el módulo de un nodo generado es un rincón
de su área, y a volumen igualado pierde. Está medido en §7 del reporte.

---

## 3. El grafo: de qué consta

<p align="center">
  <img src="docs/img/10-grafo-real.svg" alt="El grafo del runtime dibujado como árbol radial: 352 nodos que salen de los cuatro pilares fundacionales del centro hacia las sub-ramas de fuera, con el ángulo repartido por tamaño de subárbol para que ningún nodo tape a otro. Los 125 generados desde Mathlib y los 22 de área van en tono más claro porque no están interpretados categóricamente. Las nueve tácticas se dibujan aparte abajo porque son sumideros: reciben 453 aristas y no emiten ninguna." width="100%">
</p>

| pieza | cuántos | qué es |
|---|---|---|
| nodos curados | 205 | con veredicto categórico: «un objeto es un grupo, las flechas son homomorfismos» |
| nodos de área | 22 | la **puerta de entrada**: `Algebra`, `Topology`, `OrderTheory`… Entrar por una poda a 10 nodos de mediana |
| nodos generados | 125 | leídos de la taxonomía de Mathlib. Dicen *dónde vive* algo, no qué es. Marcados `interpretado=False` |
| dependencias | 684 | prerrequisitos, y **acíclicas**: eran 1156 con 4 ciclos, el mayor de 80 nodos |
| traducciones | 535 | entre pilares — Curry-Howard, conjuntos↔categorías |
| analogías | 7 | correspondencias débiles, marcadas como tales |
| identidades | 352 | una por objeto, como exige la definición de categoría |

```bash
python scripts/dibujar_grafo.py     # regenera la figura desde el grafo real
```

### Las nueve tácticas son sumideros

`tactic-simp`, `tactic-ring` y las otras siete reciben **453 aristas y no emiten
ninguna**. Por eso están dibujadas aparte: dentro convertían el grafo en un
embudo donde cualquier recorrido terminaba.

Es una categoría-error del mismo tipo que se corrigió con la homología. Una
táctica no es una *cosa*, es una transformación de estado de prueba: como nodo
es un sumidero, como flecha compondría y tendría dominio y codominio.
**Identificado y sin arreglar.**

### Eran dos grafos, y ahora son uno

Medido: **cero aristas** entre los 174 curados y los 125 generados, sin contar
el enganche al pilar. `mathlib-linearalgebra-basis` alcanzaba 81 nodos hacia
arriba y **ni uno era curado** — no pasaba por `linear-algebra`, ni por
`module-theory`, ni por `ring-theory`, que existen.

La jerarquía ya estaba escrita en el **anidamiento de módulos** de Mathlib, y va
de lo general a lo especial — la misma dirección que el grafo curado seguía con
`group-theory → ring-theory → field-theory`.

```
                              antes    después
aristas que cruzan                0        125
generados con ancestro común   0/125    109/125
la lógica alcanza               158     278 de 320
```

**Dos de esas cifras bajaron al arreglar la puerta, y es correcto que bajen.**
`124 de 125` se midió cuando el grafo tenía 4 ciclos y una componente fuerte de
80 nodos: casi todo alcanzaba a casi todo. Los 16 que ahora no llegan a un área
con curados están en `computability`, `logic` y `ordertheory`, que **no tienen
ni un solo nodo hecho a mano**. Es un hueco de los 174 curados, y ahora se ve.

Y faltaba **`fol-deduction → zfc-axioms`**: ZFC es una teoría de primer orden,
sus axiomas son fórmulas de primer orden con igualdad. Sin esa arista, media
matemática del grafo no tenía la lógica detrás. Una arista en vez de
trescientas. Es *curada*, no derivada — Mathlib no construye ZFC sobre
`Logic.Basic`.

**Lo que el esqueleto no da:** generados y curados son *hermanos* bajo un área,
no descendientes. La profundidad del módulo no ordena la generalidad —
`LinearAlgebra.Basis` está a profundidad 2 y `LinearAlgebra.Matrix.Defs` a 3, y
sin embargo el álgebra lineal es más general que la noción de base.

### El grafo tiene ciclos, y no son de la matemática

134 ciclos, todos entre los nodos generados; entre los 174 curados hay cero. Y
la causa es la agregación: el DAG oficial de Mathlib es **acíclico** —Lean
prohíbe imports circulares— pero al colapsar 7 747 módulos en conceptos de dos
niveles, aparecen.

```
Topology.Instances → Analysis.Asymptotics → Analysis.Complex → Topology.Instances
```

Son tres desarrollos distintos, no un recorrido. **El ciclo marca dónde la
división en ramas deja de funcionar.**

> **Un resultado negativo sobre las «áreas».** Se intentó definirlas por
> componentes fuertemente conexas, para que el corte lo dictara la estructura.
> No funciona: da una mega-área con 918 de los 1 358 conceptos. A nivel de
> fichero Mathlib es un DAG limpio; en cuanto se agrupa por ramas, casi todo
> queda entrelazado. **La descomposición en ramas no es recuperable de las
> dependencias** — el orden de construcción no respeta la frontera entre
> álgebra, topología y análisis.

---

## 4. La lista: 183 433 hechos

```
121 756  theorem        54 MB en disco
 50 835  lemma          1 102 conceptos distintos
 10 842  instance       3 sin enunciado utilizable (0,0 %)
```

```bash
python scripts/construir_lista_lemas.py --escribir
python scripts/construir_banco_lemas.py          # el banco de evaluación
```

### El DAG oficial, que no hubo que reconstruir

Mathlib trae la herramienta hecha, en `.lake/packages/importGraph`:

| comando | qué da |
|---|---|
| `lake exe graph` | el DAG completo — 21 446 aristas, 7 747 módulos, **0 ciclos** |
| `#min_imports` | los imports mínimos que necesita una declaración |
| `#find_home` | en qué módulo debería vivir una declaración |
| `#import_diff` | diferencia entre dos conjuntos de imports |

Al compararlo con el extractor propio apareció un fallo: el lector del fuente
metía unas 2 800 aristas falsas y con ellas un ciclo imposible de 1 244 módulos.
El oficial da cero, como debe.

### Mathlib no etiqueta por rama — etiqueta por táctica

Se buscó una anotación de área y no existe. Lo que sí hay, en 83 111 líneas y
162 atributos distintos, es qué herramienta puede usar cada lema:

```
@[simp]        40 736      @[gcongr]       575      @[continuity]  255
@[norm_cast]    2 257      @[grind]        547      @[mono]        244
@[fun_prop]     1 796      @[aesop]        286      @[measurability]
```

Es un índice *herramienta → lemas* curado por los mantenedores, y sirve: el
**42,1 %** de las premisas que citan las pruebas ya llevan `@[simp]`, y `simp`
las conoce sin que nadie se las pase. Filtrarlas movió la selección de premisas
de empatar con un prior de frecuencia (9,4 % contra 9,2 %) a superarlo
(14,0 % contra 11,7 %).

---

## 5. Lean: cuatro caminos, ocho veredictos

Hay que separar dos cosas que se confundían. Lo que Lean dice abre **cuatro
caminos**, y tres de ellos siguen trabajando; sólo al final hay un veredicto.

| lo que dice Lean | qué pasa después |
|---|---|
| falta un módulo | se repara el encabezado y se reintenta **una vez** |
| error semántico | el error vuelve al LLM, **máximo 2 rondas** |
| queda un `sorry` | entra la cascada de 12 tácticas del paso 5 |
| acepta el archivo | pasa directo al veredicto |

Los dos reintentos **sólo se aceptan si mejoran**: nunca se sustituye un
resultado por otro peor.

Y que Lean compile no significa que haya demostrado lo que se preguntó. El
veredicto final tiene siete estados, y va **delante** del texto.

| veredicto | qué significa |
|---|---|
| **`verificado`** | hay teorema, lo prueba, y es el que se preguntó |
| **`parcial`** | la estructura compila; la cascada intentó cerrar el `sorry` |
| **`refutado`** | Lean verificó la **negación** del enunciado |
| **`sin_teorema`** | Lean aceptó el archivo, pero no contiene ningún teorema |
| **`vacuo`** | hay teorema y compila, pero su conclusión es `True`: no dice nada |
| `no_verificado` | Lean rechazó y los reintentos no lo arreglaron |
| `timeout` | Lean no terminó dentro del límite |
| `sin_entorno` | no hay `lake` instalado — no es un fallo de lógica |

`sin_teorema`, `refutado` y `vacuo` existen porque los tres se dieron: el sistema llegó a estampar
«verificado» sobre un archivo de `#check` sin teoremas, sobre la negación de lo
que se había pedido, y sobre `theorem t : True := trivial` — que compila con
exit 0 y sin una sola línea de salida. Ninguna la encontraron los tests: las dos
primeras las encontró correr el sistema contra un banco de consultas reales, y la
tercera una auditoría del camino del veredicto.

---

## 6. Lo que está medido

Cada cifra con su método y su **modelo nulo**. Sin modelo nulo un porcentaje no
dice nada: *61 % de acierto* suena bien hasta que se sabe que responder siempre
lo mismo acierta el 79 %.

| qué | resultado | modelo nulo | veredicto |
|---|---|---|---|
| Vocabulario contra ProofNet<br><sub>371 ejercicios con formalización de oro · `concepto`, k=2</sub> | 22,8 % precisión<br>18,0 % cobertura | 1,45 %<br>3,3 % | **15,7× · aporta** |
| Dependencias **curadas** contra el DAG real<br><sub>154 aristas `skill→skill` medibles · DAG de 24 209 aristas</sub> | 72,7 % confirmadas<br><sub>112/154</sub> | 31,9 %<br><sub>nulo emparejado</sub> | **2,28× · aporta** |
| Costura de **cobertura** contra el DAG<br><sub>9 aristas `skill→módulo` medibles</sub> | 100 % confirmadas<br><sub>9/9</sub> | **100 %** | **1,00× · no dice nada** |
| Orden de tácticas<br><sub>1 600 pruebas de Mathlib · partición de prueba</sub> | 1,26 posiciones | **1,09** | **no bate al nulo** |
| Selección de premisas<br><sub>sin los `@[simp]`, que simp ya tiene</sub> | 14,0 % cobertura | 11,7 % | mejora pequeña |
| Elección de imports<br><sub>20 enunciados, Lean como juez · azar 14/20</sub> | 18/20 elabora | 18/20 fijo | **inerte** |
| Banco de fidelidad<br><sub>banco de 24 · corrida registrada: muestra rápida de 8</sub> | 8/8 medidos | — | **0 infieles** |
| Nombres de los nodos generados<br><sub>447 identificadores con `#check`</sub> | 346 existen | — | **95 no existen** |
| Poda por área antes de elegir<br><sub>con localización perfecta — el techo</sub> | 6,8 % | 9,8 % | **no llega al nulo** |
| Revisión de sintaxis de la consulta<br><sub>23 243 enunciados de LeanWorkbook, todos correctos</sub> | 3,6 % falsos positivos<br>60,8 % de caza | 3,6 % (moneda) | **+57,3 puntos · aporta** |
| N-gramas **+** rasgos del árbol → premisas<br><sub>22 117 enunciados · el 80,9 % es de LAS DOS juntas: los 68 rasgos añaden +4,1 puntos sobre los n-gramas solos (76,8 %)</sub> | 80,9 % cobertura | 56,6 % (los 6 más citados) | **1,43× · aporta** |
| Fibración π : Skills → Áreas<br><sub>860 pares (objeto, área debajo)</sub> | 0,3 % se levanta | 6,1 % (áreas al azar) | **peor que el azar** |

```bash
python scripts/recuperacion_contra_proofnet.py    # vocabulario
python scripts/funtor_dag_mathlib.py              # dependencias
python scripts/efecto_orden_cascada.py            # tácticas
python scripts/premisas_sin_simp.py               # premisas
python scripts/imports_del_grafo_contra_lean.py   # imports
python -m scripts.banco_fidelidad                 # fidelidad (usa API)
```

Todas sin API salvo la última.

### Respaldo formal

```
62/63  operaciones del Python con teorema Lean que las respalda
    0  sorry en todo el corpus (preguntado al compilador, no con grep)
  387  teoremas en 22 archivos Lean
```

`collectAxioms` confirma que ninguna constante depende de `sorryAx`.

Esos 387 teoremas son los **generales**: valen para cualquier grafo y se
prueban una vez. No dicen si *este* nodo es colímite de *este* patrón en el
grafo de hoy, que es una afirmación sobre una instancia finita — y por finita,
**decidible**. Para eso está la confirmación con el kernel:

```python
skill, col = builder.build_colimit(patron, grafo, con_lean=True)
col.lean_verified   # True | False | None
```

Genera el enunciado en Lean sin `import Mathlib` —para que compile en
segundos, no en minutos— y lo cierra con `decide`, que lo comprueba el
**kernel** y no el compilador; `native_decide` metería a este último en la
base de confianza sin necesidad.

**`None` no es `False`.** `True` es «el kernel lo comprobó», `False` es «lo
**refutó**: hay un co-cono sin mediador», y `None` es «no se sabe» — no había
Lean, o no pudo terminar. La distinción no es teórica: a escala real el kernel
agotaba la profundidad de recursión, y sin separarlas eso se leía como que el
grafo incumplía la propiedad.

Va apagado por defecto porque cuesta un compilado, y el coste es asimétrico:
refutar es barato —`decide` se para en el primer contraejemplo— y confirmar
obliga a reducir la conjunción entera. Medido sobre tres colímites reales del
grafo de 352 nodos: 2,6 s, 3,4 s y 15,3 s, los tres confirmados.

El verificador se comprueba a sí mismo en `tests/test_colimite_en_lean.py`:
con `a→i`, `b→i`, `i→x` confirma, y quitando sólo `i→x` —con lo que `x` pasa a
ser co-cono sin mediador— refuta. Un verificador que no separe esos dos casos
no está verificando nada.

---

### El orden de tácticas no batía a su modelo nulo, y nadie lo había preguntado

Esta medición comparaba dos reglas entre sí —2,59 y 1,29— y de ahí salía
«**APORTA · 2,4× menos intentos**», que este repositorio publicaba como el punto
mejor medido del grafo. **Nunca preguntó contra qué suelo.**

El suelo se ve en cuanto se mira la distribución de los 1 600 casos:

```
simp       1532  (95,8 %)
aesop        34  ( 2,1 %)
rfl          23  ( 1,4 %)
norm_num      5  ( 0,3 %)
linarith      5  ( 0,3 %)
ring          1  ( 0,1 %)
```

Con eso, el modelo nulo es «probar `simp` primero y no mirar nada más». Medido
en una partición de prueba del 20 %:

| orden | posición media | 1er intento | en los 3 |
|---|---|---|---|
| viejo | 2,58 | 27,2 % | 92,2 % |
| **regla de hoy** | **1,26** | 88,4 % | 94,4 % |
| **MODELO NULO** | **1,09** | 94,4 % | 99,4 % |
| clasificador entrenado | 1,06 | 95,9 % | 99,4 % |

**La regla pierde contra el nulo en 24 casos y gana en 2**, con una diferencia
media de +0,172 posiciones e intervalo de confianza del 95 % en
`[+0,094, +0,253]` — entero por encima de cero. Es real.

Y el mecanismo se ve en los casos: los patrones del objetivo **desplazan a
`simp`** justo en objetivos que `simp` cierra.

```
: card α < ⊤ ↔ Finite α                    set-theory  ->  simp
: ⁅x, m - n⁆ = ⁅x, m⁆ - ⁅x, n⁆             algebra     ->  simp
: (pure a : Filter α) * pure b = pure (a * b)  set-theory -> simp
```

**Lo que sigue siendo cierto:** pasar de 2,59 a 1,29 es una mejora real sobre el
orden viejo. Lo que no se sostiene es leerla como que el grafo aporta ahí.

**Y el clasificador tampoco se cablea.** 1,06 frente a 1,09 no es nada sobre 320
casos. El banco no puede distinguir: con el 95,8 % en una sola clase, casi
cualquier cosa que ponga `simp` primero da lo mismo. La conclusión honesta no es
«el orden de tácticas es malo», sino **este banco no puede decidirlo**.

`efecto_orden_cascada.py` calcula ahora su modelo nulo y lo imprime, para que la
cifra no se pueda volver a citar sola.

---

### La sintaxis dice qué hechos hacen falta

Lo que este repositorio llamaba «sintaxis» no lo era: eran n-gramas de 1 a 4
caracteres sobre el texto sin palabras. Una bolsa de fragmentos de símbolos no
sabe cuál es la relación principal del enunciado, ni si hay cuantificadores, ni
qué es hipótesis y qué es tesis.

La relación sintaxis–semántica sí se puede medir aquí sin metáforas, porque hay
las dos mitades: **el enunciado en Lean** es un objeto puramente simbólico, y
**los lemas que su prueba usó** son lo que hizo falta en el universo matemático.
22 117 pares, 100 lemas con suficientes ejemplos:

| | rasgos | cobertura | acierta alguno |
|---|---|---|---|
| modelo nulo — los 6 más citados | — | 56,6 % | 80,3 % |
| n-gramas de caracteres | 40 000 | 76,8 % | 94,7 % |
| **estructura sintáctica** | **68** | **76,3 %** | **94,9 %** |
| **las dos juntas** | 40 068 | **80,9 %** | **96,8 %** |

**Sesenta y ocho rasgos igualan a cuarenta mil**, y juntos suman cuatro puntos:
no son la misma información. Los n-gramas estaban aproximando la estructura de
forma cara e ilegible.

Y lo que se aprende se lee, que es lo que una bolsa de n-gramas no da nunca:

| lema | el rasgo **sintáctico** que lo predice | qué dice |
|---|---|---|
| `sq_nonneg` | relación principal `≤`/`≥` (+2,92) · **en contra** `=` (−2,54) | los cuadrados sirven para desigualdades, no para igualdades |
| `mul_pos` | `<` o `>` **en las hipótesis** (+2,90) | hace falta cuando el signo viene supuesto |
| `Real.sqrt_nonneg` | `√` en la conclusión (+1,67) · en contra tipo `ℤ` (−1,92) | no hay raíces sobre los enteros |
| `mul_comm` | tipo `ℂ` y relación `=` · en contra `¬` y `%` | no es lo que se usa en aritmética modular |

**Las advertencias, porque el número solo engaña.** El corpus es `lean_workbook`
y está dominado por desigualdades: `sq_nonneg` aparece en el 72 % de las
pruebas, y por eso el modelo nulo ya llega al 56,6 %. Esto mide *recuperar
premisas*, no *cerrar pruebas*. Y son 100 lemas de los 809 que aparecen — los
que tienen al menos 30 ejemplos.

**Todavía no está en el camino.** Es una medición, no una pieza conectada.

---

### 6bis. El decisor: qué corre, decidido por la medición

La tabla de arriba tenía filas que decían **«no bate al nulo»** y, aun así,
esas capacidades seguían ejecutándose: el hallazgo estaba escrito en el
informe y el `if` seguía en el código. `nucleo/decisor.py` cierra ese hueco.

**La regla, y es una sola.** Una capacidad corre si (1) su guarda aplica a
esta consulta **y** (2) su evidencia gana a su modelo nulo. La (2) no se
negocia. Sin evidencia, sólo corre si es gratis: no se gasta una llamada al
modelo ni un compilado de Lean en algo que nadie ha medido.

**El veredicto se lee, no se recuerda.** Se guarda la *ruta* al número dentro
del fichero de medición, no el número. Volver a medir cambia la decisión sola.
Si una ruta deja de resolver, un test lo caza: una capacidad que se apaga en
silencio es peor que no tener decisor.

Qué apaga hoy:

| capacidad | real | nulo |
|---|---|---|
| orden de cascada por área — *estaba en producción* | 1,262 | 1,091 |
| dos etapas: localizar y elegir | 0,42 | 0,93 |
| recuperación léxica de lemas | 0,065 | 7,78 |
| emparejador semántico — *nunca se adoptó* | 13,1 % precisión | 1,6 % |

La última fila decía «12 % contra 61 %», y ese 61 % **no era un nulo**: era el
emparejador léxico. Comparar un candidato contra la versión que ya tienes no es
medirlo, y encima las dos cifras eran crudas sobre el banco 89 % `algebra`,
donde una constante le gana a las dos. La fila de ahora es la de ProofNet, que
sí trae formalizaciones de oro y por tanto un nulo de verdad: el semántico da
13,1 % de precisión y **2,4 % de cobertura**, frente a 21,0 % y 14,8 % del
léxico. Se apaga por eso, y además cuesta una llamada al modelo.

Su propio modelo nulo es «ejecutarlo todo», y está implementado. Coste por
consulta: el decisor 0 llamadas al modelo y 1 compilado de Lean; el nulo 1 y 2.

Verificar con Lean **no** pasa por esta regla, y se dice por qué: el nulo de
«verificar» sería «no verificar», que es otro sistema, no una versión más
barata de éste.

```bash
python scripts/decisor_del_sistema.py     # la tabla, recalculada
```

### 6ter. La sintaxis de la consulta

Lo que había era una regex, y una regex no puede reconocer una expresión
porque una expresión es un **árbol**. Partía `(a+b)^2 = a^2 + 2ab + b^2` por
la mitad y no encontraba nada en `∀x ∈ ℝ, x² ≥ 0`: el alumno que escribe con
símbolos era invisible.

`nucleo/sintaxis/` la parsea por precedencia y dice si está bien formada. La
primera versión rechazaba el **22,3 %** de los enunciados correctos de
LeanWorkbook; las doce correcciones que lo bajaron al **3,6 %** salieron todas
de mirar qué rechazaba —intervalos `[0,∞)`, `\mathbb{R^+}`, el espaciado
`\;`, el guion de «Cauchy-Schwarz»—. El instrumento estaba mal, no los datos.

Sólo se avisa al alumno de **delimitadores** (0,6 % de falsos positivos, 99 %
de caza), que además es el error más caro: un paréntesis sin cerrar hace que
el modelo formalice *otra* fórmula, Lean verifica ésa, y la respuesta sale con
el sello de «verificado» sobre un enunciado que nadie pidió. Nunca bloquea.

### 6quater. La fibración: el funtor existe, la fibración no

Que π : Skills → Áreas sea funtor está verificado y **no basta**: un funtor
que manda todo a un punto también cumple las dos leyes. La condición que dice
que la base *sirve* es la de fibración, demostrada en
`MetamathProver/CategoryFoundations/Fibracion.lean` (0 sorry).

Sobre el grafo real **no se cumple**: 3 de 860 pares (0,3 %), contra el 6,1 %
de barajar las áreas al azar. Y la causa no es la que parecía.

**La base no es un orden.** Se construye como la imagen de las flechas del
grafo y luego se cierra transitivamente, y las flechas directas entre áreas
forman una **componente fuertemente conexa de 21 de las 23 áreas** — sólo
`Computability` y `OrderTheory` quedan fuera. Al cerrar, 63 relaciones directas
se convierten en **462 de las 506 posibles: el 91 %**.

Y los ciclos son matemática correcta, no errores de curación:

```
Algebra ↔ Analysis        área-algebra → spectral-theory
                          área-analysis → inner-product-spaces
Algebra ↔ CategoryTheory  exact-sequences → abelian-categories
                          functors → homological-algebra
Geometry ↔ Topology       differential-geometry → differential-topology
                          point-set-topology → differential-geometry
```

Sobre un preorden con una clase de equivalencia de 21 áreas, la fibración
exige que *todo* objeto de cualquiera de ellas se levante a cualquier otra — y
eso es falso: no todo concepto de álgebra depende de uno de probabilidad.

**Añadir morfismos que crucen de área no puede arreglarlo**, y está
comprobado: la clausura transitiva es monótona, así que una arista nueva sólo
puede añadir relaciones. Con 60 aristas cruzadas más, la clausura llega al
100 % y la componente se traga las 23 áreas.

Es el mismo hallazgo que dio `areas_por_estructura.py` sobre la taxonomía de
Mathlib —una mega-área con 918 de 1 358 conceptos— con otro disfraz: **la
descomposición en ramas no es recuperable de las dependencias**. El
«supergrafo unificado por un funtor» tiene el funtor; la fibración pide una
base que ordene la matemática, y el área no la ordena.

```bash
python -m scripts.base_no_es_un_orden      # el diagnóstico, con su prueba
```


## 7. Tests y guardianes

**1089 tests en 53 suites.** Los que más valen no comprueban que el código
funcione, sino que **no vuelva a mentir**:

| guardián | qué impide |
|---|---|
| `test_cobertura_consultas` | que el grafo deje de engancharse con las consultas reales sin avisar |
| `test_interpretacion` | que un nodo generado se cuele como si estuviera interpretado |
| `test_domain_tactic_pipeline` | que el prior del área vuelva a adelantar al objetivo |
| rutas absolutas | que un `except` mudo degrade el sistema en silencio |
| cifras declaradas | que la documentación anuncie números que ya no son ciertos |

```bash
python -m pytest tests/ -o "addopts="
```

---

## 8. Lo que se midió y no sirve

Estos resultados costaron tanto trabajo como los positivos. Están aquí para que
nadie los repita.

**La elección de imports no aporta, y no queda margen.** Un conjunto fijo de
tres módulos hace elaborar el 92,5 % de los enunciados; añadirle lo del grafo da
el mismo 92,5 %. De 40 casos fallan 3: uno necesita `open Real`, otro usa
sintaxis vieja, y sólo uno es de imports. **Margen real: 2,5 puntos.**

**Las premisas no cierran pruebas.** Añadir tácticas con premisas costó 231
invocaciones extra de Lean y cerró **cero**. La razón es aritmética: la
cobertura es del 14 %, o sea una de cada siete, y una prueba las necesita
*todas*. Una métrica de recuperación **no se traduce en cierres**.

**Tres emparejadores fallaron, y la causa no era el emparejador.** Búsqueda
plana 43,9 %, descenso anclado en pilares 11,8 %, embeddings 11,9 % — los tres
por debajo del 79,4 % de decir siempre «álgebra». Para `(a+b)² = a²+2ab+b²`
**no existía el nodo**: las 35 skills de álgebra eran todas álgebra abstracta.

**Podar por área tampoco sirve, ni acertando el área.** Con localización
*perfecta* la cobertura sube de 6,0 % a 6,8 %; el modelo nulo da 9,8 %. Afinar
a sub-área empeora: el espacio se divide por cuarenta, el techo sube 0,3 puntos
y acertar es la mitad de fácil. Y una sospecha mía era falsa — el **77,1 %** de
las premisas está en la misma área que el teorema, así que la poda no tira lo
que hace falta: simplemente no ayuda.

**95 de los 447 nombres generados no existen en Mathlib.** Estaban *deducidos*
de la ruta del módulo; el filtro dejaba pasar `Basic` —un nombre de fichero—
igual que `Polynomial` —un tipo—. Sólo Lean distingue. Cuatro nodos se quedan
sin ningún nombre válido.

**La recuperación de lemas por contenido pierde contra la moda.** Sobre 23 243
pruebas reales: contenido 0,6 % de cobertura, ofrecer siempre los 20 lemas más
citados, 77 %. `sq_nonneg` no aparece en el enunciado ni tiene por qué — es una
*herramienta*, no un concepto del que el problema hable.

---

### El bucle que no cuesta dinero

El modelo formaliza una consulta **una vez**, se graba, y todo lo que el sistema
hace después —imports, reparación, cascada, premisas— se reejecuta con Lean de
juez y coste cero.

```bash
METAMAT_GRABAR=1 python -m nucleo chat     # graba mientras trabajas
python scripts/replay.py                   # reproduce, sin API
```

La frontera está donde tiene que estar: se graba el código del LLM *antes* de
que Lean lo vea. Si el gancho se moviera detrás, el replay mediría el sistema
contra su propia salida — hay un test que lo impide.

---

## 9. Instalación y uso

```bash
git clone https://github.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean.git
cd Metamatematico
pip install -r requirements.txt

# Lean 4 + Mathlib
lake update && lake build          # 20-30 min la primera vez

# la clave de API, en .env (gitignored)
echo "ANTHROPIC_API_KEY=sk-..." > .env

streamlit run app.py               # interfaz
python -m nucleo chat              # REPL
```

Los índices derivados de Mathlib se reconstruyen con:

```bash
python -m scripts.mapa_modulos_mathlib
python scripts/construir_lista_lemas.py --escribir
python scripts/construir_indice_premisas.py
lake exe graph --to Mathlib data/mathlib_imports.dot
```

---

## 10. Estructura del repositorio

```
nucleo/
  core.py                 el orquestador: Nucleo.process()
  rutas.py                dónde está cada cosa, sin rutas absolutas
  graph/                  la categoría de conceptos
    interpretacion.py     el veredicto: qué es cada nodo, y su `teoria`
    complexity.py         colímites, orden, emergencia
  lean/
    client.py             habla con Lean
    solver_cascade.py     las 12 tácticas y su orden
    premisas.py           qué lemas citar cuando la táctica desnuda no basta
  pillars/
    math_domains.py       los 163 conceptos curados
    mathlib_taxonomy.py   los 125 generados (GENERADO — no editar a mano)

scripts/                  cada medición, con su método en el docstring
MetamathProver/           387 teoremas Lean · 22 archivos
tests/                    1089 tests en 53 suites
data/                     índices derivados (los grandes van en .gitignore)
```

---

## 11. Lo que no está

**Sin respuesta todavía.** Si el vocabulario del paso 1 se traduce en más
verificaciones. Es la única pregunta que necesita llamar al modelo, y está
bloqueada por presupuesto. Lo que hay: en 8 casos fáciles apagar el núcleo
entero no cambia ningún veredicto y el sistema completo tarda más — n=8 con
efecto techo, no concluyente.

**Identificado y sin arreglar.**

- ~~El emparejamiento consulta→concepto: 15 de 24 consultas reales no activan
  ninguna skill.~~ **Arreglado** — el silencio pasó del 27,1 % al 5,8 % sobre
  3 000 consultas. Lo que queda: no hay lematización, así que `primos` sigue sin
  casar con `primo`.
- **Los pasos 1 y 3 no son independientes.** El 3 reusa el `context` del 1
  (`core.py:1858`), así que si el emparejamiento falla, el 3 hereda el fallo. Se
  venían describiendo como tres actuaciones separadas y son dos más una.
- Las tácticas como nodos: 453 aristas entrando en 9 sumideros.
- Los nombres de los 125 nodos generados están *deducidos* de la ruta del
  módulo, no comprobados con `#check`. Por eso no se inyectan: al activarlos la
  precisión caía por debajo del azar.
- Seis dependencias siguen bajo sospecha de ir al revés.

**Lo que el sistema no hace.**

- No demuestra teoremas por sí solo: formaliza y verifica.
- El grafo no decide qué es cierto en ningún punto. Eso es Lean, siempre.
- Sin API no hay formalización, ni chat, ni banco de fidelidad. Lo que sigue
  vivo sin ella es validar y mejorar el núcleo.

---

**Licencia MIT** · Leonardo Jiménez Martínez, BIOMAT — Centro de Biomatemáticas
