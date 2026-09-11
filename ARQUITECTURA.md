# La arquitectura de Metamatemático

**Qué es este documento.** La descripción de cómo está organizado el sistema,
por qué está organizado así, y qué muestra cada pieza. Cada afirmación lleva su
medición o dice explícitamente que no la tiene.

**La regla que gobierna todo lo demás:** una capacidad se ejecuta si y sólo si
su evidencia gana a un modelo nulo explícito. No es una aspiración: está
implementada en `nucleo/decisor.py`, que lee el veredicto de los ficheros de
medición y apaga lo que no lo supera.

---

## 1. El principio de reparto: la frontera de la formalización

El sistema y Lean hacen búsquedas distintas, y durante mucho tiempo compitieron
sin saberlo. La diferencia no es de calidad: es de **tipo de entrada**.

| | clave de indexación | necesita |
|---|---|---|
| **el grafo** | palabras humanas, ES/EN | prosa |
| **Lean** (`exact?`, `apply?`, `aesop`) | estructura del tipo, árboles de discriminación sobre ~200 000 declaraciones | un objetivo formal |

Eso parte el sistema en dos mitades con dueños distintos, y **la frontera es el
momento en que existe un enunciado formal**.

### La evidencia que lo sostiene

Antes de formalizar, con la consulta en prosa:

```
grafo curado (320 nodos)                       21.0 %  precisión
índice completo de Mathlib (217 419 nombres)    1.53 %
modelo nulo                                     1.63 %
```

Buscar en la estructura de resolución completa con lenguaje natural **no supera
al azar**. El grafo la bate 13×.

Después de formalizar, con un objetivo formal:

```
recuperación de lemas, método léxico    0.64 %  cobertura
recuperación de lemas, método semántico 0.37 %
modelo nulo (los lemas más citados)    77.05 %
```

Ahí la búsqueda del grafo pierde por dos órdenes de magnitud.

### Lo que esto explica

El decisor descubrió esta frontera empíricamente, capacidad por capacidad,
antes de que nadie la nombrara. Toda capacidad **del grafo** que actúa antes de
formalizar gana; toda la que actúa después pierde o empata:

| capacidad | actúa | medida vs nulo | |
|---|---|---|---|
| clasificación de área | antes | 58.7 vs 33.3 | ✓ |
| nombres de Mathlib en el prompt | antes | 21.6 vs 1.5 | ✓ |
| revisión de sintaxis | antes | 0.61 vs 0.04 | ✓ |
| elección de imports | después | 18 vs 18 | empate |
| orden de cascada por área | después | 1.26 vs 1.09 | ✗ |
| recuperación léxica de lemas | después | 0.065 vs 7.78 | ✗✗ |
| localizar y elegir en dos etapas | después | 0.42 vs 0.93 | ✗ |

---

## 2. Las cinco capas

```
                          consulta (ES/EN)
                                │
 ┌──────────────────────────────┼──────────────────── ANTES DE FORMALIZAR
 │  L0  LENGUA         keywords ES/EN → concepto
 │  L1  CONCEPTO       158 curados · vocabulario verificado con #check
 │  L2  TERRITORIO     147 generados desde Mathlib · dónde vive
 └──────────────────────────────┼────────────────────
                                ▼
                        ENUNCIADO FORMAL          ← la frontera
                                │
 ┌──────────────────────────────┼──────────────────── DESPUÉS DE FORMALIZAR
 │  L3  EVIDENCIA      forma del objetivo → qué lo cierra
 │      Lean actúa: exact? apply? aesop · cascada rankeada
 │                                │
 │  L4  EMERGENCIA     colímites sobre teoremas que Lean aceptó
 └──────────────────────────────┴────────────────────
```

### L0 — Lengua

**Por qué.** Es lo único que Lean no puede hacer: leer una frase. Un índice de
217 419 nombres formales no contiene la correspondencia «grupo → `Group`,
`Subgroup`, `MonoidHom`»; esa la escribió una persona.

**Qué hace.** Empareja la consulta con competencias por solapamiento léxico
sobre identificadores, nombres y palabras clave declaradas en español e inglés.
Rechaza los solapamientos que consisten sólo en palabras genéricas.

**Qué muestra.** 58.7 % de acierto de área equilibrado contra 33.3 % de
responder siempre la clase mayoritaria.

### L1 — Concepto

**Por qué.** El modelo inventa **21 de cada 28** identificadores de Mathlib
cuando tira de memoria. Sustituir recuerdo por consulta es la única aportación
del grafo que bate a su nulo por un factor grande.

**Qué hace.** 158 conceptos curados a mano; 113 llevan nombres de Mathlib
comprobados uno a uno con `#check` contra la biblioteca completa. De las
competencias emparejadas se toman las dos primeras **que aporten nombres**, y
esos nombres entran en el prompt de formalización.

**Qué muestra.** 180 de 186 nombres existen (96.8 %). Los seis restantes son
espacios de nombres y están filtrados antes del prompt: la etiqueta «verificado»
es cierta para todo lo que el sistema ofrece. Contra ProofNet: precisión 21.6 %
y cobertura 18.3 %, frente a 1.5 % y 3.3 % del nulo.

**Lo que NO muestra.** Que eso haga verificar más a Lean. Se midió: 3 rescates
y 2 roturas sobre 20 casos, *p* = 1.0. Es puntería, no resultado.

### L2 — Territorio

**Por qué.** El grafo curado nombra 158 conceptos; la taxonomía de Mathlib tiene
1 139. Los 147 objetos generados dan alcance para reconocer temas que L1 no
nombra.

**Qué hace.** Aporta reconocimiento temático, **no vocabulario**, y rankea
detrás de los conceptos curados.

**Qué muestra.** Que su vocabulario no transfiere, por tres vías medidas:

```
sólo curado (base)                21.64 %  precisión
(1) añadir generados, sin criba   17.45 %
(2) criba por uso en Mathlib      20.77 %
(3) cuota separada                20.18 %
```

La vía (2) usa un criterio independiente del banco y repara la precisión de
forma monótona, lo que confirma el diagnóstico — pero no vuelve a la base. La
razón: el módulo de un objeto generado es un **rincón** de su área, no su
centro, y lo que sobrevive a la criba son tipos universales, que es lo que
ofrece un modelo nulo.

### L3 — Evidencia

**Por qué.** Tras la frontera, la pregunta ya no es «de qué trata» sino «qué
cierra esto». Y esa se decide por la **forma del objetivo**: una igualdad se
cierra con `ring`, una desigualdad con `nlinarith`. Cada intento fallido cuesta
una compilación de Lean de 12 a 30 segundos, que es el recurso más caro del
sistema.

**Qué hace.** Un clasificador ordena la cascada de solvers según el estado de
prueba. Combina dos vistas del mismo estado:

- **n-gramas de carácter**, que ven los símbolos (`⊢ ℝ ≤ ∑`);
- **74 rasgos estructurales** (`nucleo/lean/rasgos_estado.py`), que ven la
  forma: qué relación gobierna el objetivo, qué tipos aparecen, cuántas
  hipótesis hay, si es simétrico.

**Qué muestra.** Las dos vistas no son redundantes:

```
                   acierto   equilibrado
n-gramas            60.53 %     34.14 %
estructura          61.14 %     36.26 %
las dos juntas      67.11 %     47.65 %
```

Y medido con el modelo de producción contra el orden fijo real de la cascada,
sobre 1 530 casos que no vio:

```
                        posición media   1er intento   en los 3
fijo (SOLVER_CASCADE)        5.79           0.0 %       36.0 %
NULO: por frecuencia         2.44          42.5 %       78.5 %
RANKEADOR                    1.57          71.0 %       93.5 %
```

**3.7× menos invocaciones de Lean** que el orden fijo, y bate al nulo fuerte por
0.87 posiciones.

**Detalle de ingeniería que importa.** El extractor de rasgos vive en `nucleo/`
y no en `scripts/` porque el modelo se serializa con `pickle` y se carga en
caliente: un `Pipeline` guarda la *referencia* a sus transformadores, así que
desde un guion la deserialización fallaría en producción, en silencio y sólo por
el camino real.

### L4 — Emergencia

**Por qué.** `record_activation` alimenta el paisaje de CR_org, de donde salen
los patrones que se ligan en colímites. Pero se alimentaba de lo que el
**emparejador léxico adivinó**: el grafo llevaba la cuenta de sus propias
conjeturas, un lazo cerrado sin verdad dentro.

**Qué hace.** Sustituye la fuente. Dos conceptos coocurren si un teorema que
Lean aceptó habla de los dos. El material son los 40 025 teoremas de Mathlib
con enunciado, y se corrige por frecuencia: el exceso es log₂(observado ÷
esperado).

**Qué muestra.** Los pares que emergen son relaciones matemáticas genuinas:

```
  +6.74  derived-category + homological-algebra
  +6.23  measure-theory + random-variables
  +5.03  hilbert-spaces + inner-product-spaces
  +4.95  ideals-quotient-rings + ring-theory
  +4.56  complex-analysis + holomorphic-functions
  +4.32  group-theory + subgroups-cosets
  +3.93  field-theory + finite-fields
  +3.13  compactness + separation-axioms
```

Y la corrección por frecuencia es la que lo hace fiable. En crudo, el cuarto par
más frecuente es `cic + linear-algebra` con 134 coocurrencias — pero su exceso
es **+0.11**, azar puro: `cic` declara `Type`, que aparece en todos los
enunciados. Sin esa corrección el paisaje se llenaría de hubs.

**Dos decisiones que costaron una medición fallida cada una.**

*El material es el enunciado, no las premisas.* Cruzar el vocabulario del grafo
con las premisas citadas dio **cero** coincidencias exactas sobre 40 025
teoremas. No era un fallo del código: el grafo nombra **objetos** (`Group`,
`MonoidHom`) y las pruebas citan **lemas sobre** esos objetos
(`cardinalMk_lift_le_mul`). Son conjuntos disjuntos por construcción. Los tipos
viven en el enunciado.

*El emparejado es exacto, sin expandir a la raíz del namespace.* Con expansión,
los cuatro pares más frecuentes eran artefactos: `Nat.card`, `Nat` y
`Nat.Partition` comparten la raíz `Nat`, así que cualquier prueba que citara
algo de `Nat.` activaba tres conceptos a la vez.

---

## 3. Qué parte busca y qué parte explica

Las capas no hacen todas lo mismo, y confundirlo lleva a pedirle a una lo que
sólo puede dar otra. Hay **dos funciones distintas** y una capa puede servir a
las dos, a una o —esto importa— a ninguna de forma medible.

- **Buscar** = encontrar antes, más rápido o mejor lo que hace falta para que
  Lean acepte. Se mide en aciertos y en compilaciones ahorradas.
- **Explicar** = poder decir, con recibo, por qué el sistema hizo lo que hizo y
  qué relación matemática lo sostiene. Se mide en si la afirmación es
  comprobable, no en si acelera.

### El reparto, con su evidencia

| capa / pieza | busca | explica | evidencia |
|---|---|---|---|
| **L0** lengua | **sí** | poco | 58.7 % vs 33.3 % de acierto de área |
| **L1** vocabulario | **sí, y no llega al final** | **sí, mucho** | 21.6 % vs 1.5 % en recuperación; **p = 1.0** sobre la verificación |
| **L2** territorio | reconoce temas | poco | su vocabulario no transfiere (3 vías medidas) |
| **L3** rankeador | **sí, es la más efectiva** | poco | **3.7×** menos compilaciones de Lean |
| **L4** coocurrencia | no | **sí, mucho** | pares con exceso hasta +6.74 sobre azar |
| cualificación de nombres | **sí** | sí | evita compilaciones gastadas en nombres que no existen |
| reparación con el modelo | **sí (lo más fuerte)** | no | 42 % → 60 % (no aislado) |
| 387 teoremas Lean | no | **sí, es el fundamento** | 62 de 63 operaciones con teorema que las respalda |
| decisor | ahorra coste | **sí, se explica a sí mismo** | 2 llamadas → 0, 2 compilados → 1 |
| complejificación | no | sí, estructura del dominio | 2 pasos a punto fijo, 22 colímites preservados |

**Las tres lecturas que hay que sacar de esa tabla.**

**L3 es la pieza que más mejora la búsqueda.** No el grafo de conceptos: el
rankeador del estado de prueba. Reduce las invocaciones de Lean de 5.79 a 1.57,
y cada una cuesta entre 12 y 30 segundos.

**L1 busca bien y no llega al resultado.** Recupera los identificadores
correctos catorce veces mejor que su nulo, y su efecto sobre lo que Lean acepta
no se distingue del ruido (3 rescates, 2 roturas, *p* = 1.0). Su valor real es
el otro: que los nombres que el sistema afirma sean ciertos.

**L4 no busca nada, y es de lo más valioso para explicar.** No entra en el
prompt ni ordena tácticas. Lo que aporta es poder decir «estos dos conceptos
aparecen juntos en 206 teoremas que Lean aceptó, 20 veces más de lo esperado
por azar».

### Qué se le explicaría a un alumno

Traza real del sistema para *«Demuestra que todo subgrupo de un grupo cíclico
es cíclico»*:

> **Qué conceptos vi.** `group-theory` y `subgroups-cosets`, porque tu
> enunciado dice «grupo» y «subgrupo».
>
> **Qué nombres de Mathlib te doy, y por qué puedes fiarte.** `Group`,
> `Subgroup`, `MonoidHom`. Los tres existen: están comprobados uno a uno con
> `#check` contra Mathlib completo. Esto importa porque un modelo de lenguaje
> **inventa 21 de cada 28** nombres cuando tira de memoria.
>
> **Qué hace falta saber antes.** Los axiomas de ZFC y la teoría de grupos:
> son los prerrequisitos de estos conceptos en el grafo.
>
> **Qué suele ir junto con esto.** Grupos y subgrupos aparecen juntos en **206
> teoremas** de Mathlib que Lean ya aceptó. No es una impresión: es un recuento.
>
> **Por dónde va a intentarlo Lean, y por qué en ese orden.** `norm_num`,
> `simp`, `ring_nf`… — ordenado según la forma de tu objetivo, no por una lista
> fija. El orden fijo empezaría por `rfl`.
>
> **Y el veredicto lo da Lean, no yo.** Si no lo acepta, te digo que no lo
> aceptó.

Lo que un alumno se lleva: **qué vocabulario formal corresponde a lo que
escribió**, que ese vocabulario es real y no inventado, qué conceptos hacen
falta antes, y qué compañía suele tener el problema.

### Qué se le explicaría a un matemático

Lo mismo, más los recibos que a un alumno no le hacen falta:

> **La agrupación de conceptos no es una heurística.** El grafo es una
> categoría delgada, y en ella el colímite de un diagrama coincide con el
> supremo de sus objetos en el preorden inducido. Está demostrado en
> `JoinColimit.lean` y conectado con `CategoryTheory.Limits.IsColimit` de
> Mathlib en `IsColimitBridge.lean`, sin `sorry`.
>
> **El orden del grafo no es arbitrario.** Coincide con el orden real de
> *imports* de Mathlib en el **78.1 %** de los 73 pares comparables, contra un
> **40.1 %** esperado por azar.
>
> **La coocurrencia está corregida por frecuencia.** `derived-category` y
> `homological-algebra` aparecen juntos sólo 6 veces, pero **64× más** de lo
> esperado. Mientras que `cic + linear-algebra`, con 134 coocurrencias, tiene
> exceso **+0.11**: azar puro, porque `cic` declara `Type`.
>
> **Y hay emergencia en sentido técnico, no metafórico.** Cuatro objetos tienen
> orden irreducible ≥ 2 — el *mínimo* sobre sus descomposiciones, no el máximo.
> La distinción decide: de los objetos con altura 2, uno resulta tener orden
> irreducible 1 y por tanto **no** es emergente.

### Lo que NO se explica, y conviene decirlo

- **Por qué el modelo escribió *ese* enunciado.** La formalización la hace un
  modelo de lenguaje y no es auditable paso a paso. Lo auditable es el
  resultado: Lean lo acepta o no.
- **Por qué el rankeador propone ese orden.** Es una regresión logística sobre
  74 rasgos y n-gramas; se pueden inspeccionar los pesos, pero no da una razón
  matemática.
- **Que los conceptos ofrecidos sean los que la prueba necesita.** Se mide y la
  cobertura es del 18.3 %.

---

## 4. Lo que está conectado, y lo que no

| pieza | estado | nota |
|---|---|---|
| Verificación con Lean | **conectada** | es el propósito |
| Vocabulario en el prompt (L1) | **conectada** | 180/186 verificados |
| Rankeador de la cascada (L3) | **conectada** | 3.7× menos compilaciones |
| Reparación con el modelo | **conectada** | hasta dos rondas |
| Cualificación de nombres | **conectada** | índice de 217 419 |
| Coocurrencia verificada (L4) | **conectada** | 28 pares sembrados |
| Premisas híbridas | **conectada** | margen estrecho: 1.24 vs 1.04 |
| Colímites y emergencia | calculados, no inyectados al prompt | sin evidencia |
| Complejificación | implementada, desactivada | inserta objetos sin nombre |
| Elección de imports | apagada por medición | empata con una constante |
| Reconocedor de área | no cableado | gana en su banco, no en el real |
| Red neuronal (GNN/PPO) | **descartada en ejecución** | degenerada; el sistema la detecta |
| Fibración sobre áreas | **no existe** | 0.35 % contra un nulo de 6.08 % |

---

## 5. El resultado de punta a punta

Sobre veinte enunciados en español con Lean como único juez:

```
modelo solo         4 de 20  (20 %)   una llamada, sin sistema
sin vocabulario    11 de 20  (55 %)   el sistema menos el grafo
sistema completo   12 de 20  (60 %)   configuración servida
```

| comparación | rescata | rompe | *p* (McNemar exacto) |
|---|---|---|---|
| sistema frente a modelo solo | 8 | 0 | **0.0078** |
| con frente a sin vocabulario | 3 | 2 | 1.0000 |

**El aparato triplica al modelo aislado y es significativo. El grafo, dentro de
él, no se distingue del ruido.** Las dos cosas son verdad y confundirlas es
fácil: comparar el sistema con y sin grafo responde si el grafo aporta, no si el
sistema aporta.

---

## 6. El método

Cuatro reglas que no se negocian, y las cuatro nacieron de un error concreto.

**Todo se compara contra un modelo nulo explícito, y el nulo debe ser fuerte.**
Para la recuperación de nombres el nulo no es «no ofrecer nada» sino «ofrecer
los identificadores más frecuentes de Mathlib sin mirar la consulta». Para
reemplazar un modelo en producción, el nulo es **el modelo que ya corre**, no la
clase mayoritaria.

**Los diseños son pareados, y el signo importa tanto como el número.** Rescatar
ocho y romper cero no es lo mismo que rescatar tres y romper dos aunque la
diferencia neta se parezca.

**Un resultado idéntico a la línea base no es un empate: es la firma de una
medición que no está midiendo.** Ha ocurrido cuatro veces en este proyecto:

1. La primera medición contra ProofNet dio 0.0 % en *todas* las variantes,
   incluido el nulo: faltaba el normalizador entre Lean 3 y Mathlib 4.
2. Reordenar premisas con el orden del grafo dio cifras idénticas a la base: el
   filtro alcanzaba el 0.05 % de los candidatos.
3. La primera campaña de grabación registró veredictos vacíos durante una tanda
   entera por leer un atributo inexistente.
4. La primera versión de L4 dio excesos negativos en *todos* los pares, que es
   la firma de un denominador mal puesto, no de una anticorrelación universal.

**Un banco sin variedad en la variable que se predice no puede contestar.** Se
intentó predecir la estrategia de prueba con LeanWorkbook y el reparto era 81 %
`forward` y **cero** casos de inducción: al filtrar quedaban dos clases. Con
ProofNet (cinco estrategias con masa) la señal existe pero es demasiado débil
para desplegar: gana al azar (*p* = 0.010) y pierde en acierto crudo contra la
clase mayoritaria.

---

## 7. Reproducir

Ninguno de estos guiones gasta servicios de pago salvo donde se indica.

| guion | pregunta que contesta | costo |
|---|---|---|
| `recuperacion_contra_proofnet` | ¿ofrece el grafo los nombres correctos? | — |
| `verificar_vocabulario_grafo` | ¿existen los nombres que ofrece? | — |
| `ranker_en_la_cascada` | ¿ahorra compilaciones el rankeador? | — |
| `l4_coocurrencia_verificada` | ¿qué conceptos trabajan juntos de verdad? | — |
| `el_grafo_generado_complementa` | ¿complementa el vocabulario generado? | — |
| `orden_del_grafo_en_premisas` | ¿sirve el orden para premisas? | — |
| `rasgos_predicen_estrategia` | ¿se puede predecir la estrategia? | — |
| `replay` | ¿aporta la maquinaria posterior al modelo? | — |
| `decisor_del_sistema` | ¿qué corre y por qué? | — |
| `linea_base_llm` | ¿qué hace el modelo solo? | $0.03 |
| `campana_de_grabacion` | ¿aporta el vocabulario a la verificación? | $3.42 |

---

## 8. Lo que falta

- **Aislar las rondas de reparación.** El replay sin ellas da 42 % y en vivo se
  llega al 60 %: esos 18 puntos son la pieza que la evidencia señala como
  responsable del efecto del aparato, y no está medida por separado.
- **Un banco en español con premisas de referencia.** No existe, ni aquí ni
  públicamente. Sin él, el idioma de uso real no se puede evaluar — y el bug de
  flexión (`abiertos` no empareja, `abierto` sí) es invisible.
- **Elevar el tamaño muestral** a unos doscientos pares para acotar el efecto
  del grafo en lugar de sólo no detectarlo.
- **Decidir sobre las 1 604 líneas del subsistema neuronal**, hoy descartado en
  ejecución.
