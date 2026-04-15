# METAMATEMÁTICO — Razonamiento Formal con Lean 4

[![Lean 4](https://img.shields.io/badge/Lean-4-blue.svg)](https://lean-lang.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://python.org/)
[![Tests](https://img.shields.io/badge/Tests-352_passing-brightgreen.svg)](#8-tests)
[![Agentes](https://img.shields.io/badge/Agentes-18_col%C3%ADmites-blueviolet.svg)](#3-sistema-multi-agente-jerarquía-de-colímites)
[![GNN+PPO](https://img.shields.io/badge/GNN%2BPPO-546K_params-red.svg)](#5-red-neuronal-gnn--ppo)
[![Dataset](https://img.shields.io/badge/Dataset-5.4M_ejemplos-orange.svg)](#datasets)
[![Streamlit](https://img.shields.io/badge/App-Streamlit-ff4b4b.svg)](#9-aplicación-web)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Leonardo Jiménez Martínez · BIOMAT · Centro de Biomatemáticas · UNAM**

---

## Índice

1. [Qué es este sistema](#1-qué-es-este-sistema)
2. [Por qué Lean como fuente de verdad](#2-por-qué-lean-como-fuente-de-verdad)
3. [Sistema Multi-Agente: Jerarquía de Colímites](#3-sistema-multi-agente-jerarquía-de-colímites)
4. [Memory Evolutive Systems (MES)](#4-memory-evolutive-systems-mes)
5. [Red Neuronal GNN + PPO](#5-red-neuronal-gnn--ppo)
6. [Co-Reguladores](#6-co-reguladores)
7. [Cómo funciona: flujo completo de una consulta](#7-cómo-funciona-flujo-completo-de-una-consulta)
8. [Tests](#8-tests)
9. [Datasets](#datasets)
10. [Aplicación Web](#10-aplicación-web)
11. [Entrenamiento](#11-entrenamiento)
12. [Estructura del Repositorio](#12-estructura-del-repositorio)
13. [Instalación](#13-instalación)
14. [Fundamento Teórico](#14-fundamento-teórico)

---

## 1. Qué es este sistema

**Metamatemático** es un asistente de razonamiento matemático formal. A diferencia de un LLM convencional que genera texto plausible, este sistema **verifica matemáticamente** cada respuesta antes de producirla: toda afirmación matemática pasa por el demostrador de teoremas Lean 4 antes de llegar al usuario.

El núcleo se llama **NLE v7.0 (Núcleo Lógico Evolutivo)** y es un sistema que combina cuatro disciplinas:

| Disciplina | Rol en el sistema |
|---|---|
| **Teoría de categorías** | Organiza el conocimiento matemático como un grafo categórico donde los conceptos son objetos y sus relaciones son morfismos |
| **Memory Evolutive Systems** | Modela cómo el sistema *aprende*: el grafo evoluciona añadiendo nuevos nodos emergentes (colímites) cuando detecta patrones recurrentes |
| **Aprendizaje por refuerzo** | Un agente GNN+PPO selecciona qué tácticas Lean aplicar, mejorando con cada interacción |
| **Verificación formal (Lean 4)** | Es la fuente de verdad. Ninguna respuesta matemática sale del sistema sin pasar por Lean |

### El flujo completo de una consulta

```
Usuario: "demuestra que √2 es irracional"
         │
         ▼
  MultiAgentOrchestrator  ←─── clasifica la consulta
  classify_query()         ─→   categoría: "number-theory"
         │
         ▼
  ColimitAgent[number-theory]  ←── recibe señal del PillarAgent[ZFC]
  select_tactic()          ─→   táctica sugerida: "norm_num"
         │
         ▼
  LLM (formalizador)
  "Lean 4: theorem sqrt2_irrational : Irrational (Real.sqrt 2) := by..."
         │
         ▼
  Lean 4 verifica  ──── ¿compila sin sorry? ────┐
         │                                        │
     [falla]                                  [éxito]
         │                                        │
  SolverCascade                            LLM traduce resultado
  rfl → simp → ring                       a lenguaje natural
  → omega → aesop                                │
         │                                        │
         └──────────────────────────────────────►─┘
                                                  │
                                                  ▼
                              "√2 es irracional. Demostración verificada por Lean 4."
```

El LLM interviene **solo dos veces**: para formalizar el enunciado en Lean, y para traducir el resultado verificado a lenguaje natural. Nunca produce matemáticas por sí solo.

---

## 2. Por qué Lean como fuente de verdad

Los modelos de lenguaje pueden generar demostraciones matemáticas que *suenan* correctas pero contienen errores sutiles. Lean 4 es un lenguaje de programación con un sistema de tipos dependientes que actúa como verificador formal: si un programa Lean compila sin errores, la demostración es matemáticamente correcta.

**Principio de diseño fundamental**: el sistema nunca responde matemáticas directamente desde el LLM. Lean es quien decide si una afirmación es verdadera.

### SolverCascade — recuperación automática de pruebas

Cuando la formalización del LLM falla o contiene `sorry` (un placeholder que Lean acepta pero que marca una prueba incompleta), el sistema intenta automáticamente una cascada de tácticas:

```
rfl      → identidades triviales (a = a)
simp     → simplificación por reglas
ring     → identidades de anillo (álgebra)
omega    → aritmética lineal sobre enteros
aesop    → búsqueda heurística de prueba
```

Si ninguna táctica cierra la prueba, el sistema reporta el fallo con información estructurada sobre qué parte de la demostración queda abierta.

---

## 3. Sistema Multi-Agente: Jerarquía de Colímites

### ¿Qué es un colímite y por qué los agentes son colímites?

En teoría de categorías, dado un diagrama de objetos y morfismos, el **colímite** es el objeto universal que los "resume" a todos: hay un morfismo canónico desde cada objeto del diagrama hacia el colímite, y cualquier otro objeto que también reciba morfismos de todos ellos se factoriza de manera única a través del colímite.

En este sistema, los **skills** (competencias matemáticas) son los objetos del diagrama, y los **agentes son literalmente el nodo colímite** construido sobre ellos. Esto tiene consecuencias concretas:

- El agente no es un proceso externo que *lee* el grafo — es un *nodo del grafo mismo*
- Los co-conos (morfismos skill → agente) son aristas reales en el grafo NetworkX
- La **propiedad universal** garantiza que si dos agentes resuelven el mismo problema, existe un morfismo mediador único entre ellos — lo que el sistema usa para propagar tácticas entre categorías

### La jerarquía de 4 niveles

```
L0: 31 skills atómicos de los pilares fundacionales
    ┌─────────────────────────────────────────────────┐
    │  ZFC (8)  │  CatThy (8)  │  Logic (7)  │  TypeThy (8)  │
    │ naive-sets│ cat-basics   │ propositional│ stlc          │
    │ zfc-axioms│ functors     │ fol-syntax  │ system-f      │
    │ ordinals  │ nat-trans    │ fol-semant. │ dep-types     │
    │ cardinals │ limits       │ sequent-calc│ prop-types    │
    │ ...       │ ...          │ ...         │ ...           │
    └─────────────────────────────────────────────────┘
         │  co-conos (morfismos L0 → L1 en el grafo)
         ▼
L1: 4 PillarAgents  — colímites de sus skills L0
    colim[ZFC]            colim[CatThy]
    colim[Logic]          colim[TypeThy]

    Cada pilar inyecta morfismos (peso 0.8) en las categorías que fundamenta.
    Durante inferencia, select_tactic() lee estos morfismos del grafo
    y los usa para sugerir tácticas basadas en el pilar dominante de la query.
         │  morfismos L1 → L2 (pilares nutren categorías)
         ▼
L2: 14 ColimitAgents  — colímites de skills de dominio + señales de pilares
    colim[algebra]         colim[analysis]        colim[category-theory]
    colim[combinatorics]   colim[computation]     colim[geometry]
    colim[lean-tactics]    colim[logic]            colim[number-theory]
    colim[optimization]    colim[probability]     colim[proof-strategies]
    colim[set-theory]      colim[topology]
         │  co-conos (morfismos L2 → L3 en el grafo)
         ▼
L3: MultiAgentOrchestrator  — colímite de los 14 colímites
    Propiedad universal: morfismo mediador único entre agentes
```

### Qué pilares fundamentan cada categoría

| Pilar L1 | Categorías L2 que nutre | Por qué |
|---|---|---|
| **ZFC** | algebra, set-theory, combinatorics, number-theory, probability, analysis | Toda la matemática discreta y continua clásica se construye sobre conjuntos |
| **Teoría de Categorías** | category-theory, topology, algebra, analysis | Los espacios topológicos, functores y transformaciones naturales son objetos categóricos |
| **Lógica (FOL+IL)** | logic, proof-strategies, lean-tactics, computation, set-theory | Las reglas de deducción y los sistemas de prueba dependen de la lógica formal |
| **Teoría de Tipos (Curry-Howard)** | lean-tactics, proof-strategies, computation, logic | Lean 4 está basado en el Cálculo de Construcciones — las pruebas son programas |

### Cómo un agente selecciona una táctica Lean

`select_tactic(query)` sigue una cascada de 5 pasos, todos activos sin necesidad de reentrenamiento:

| Paso | Fuente | Descripción |
|---|---|---|
| **1** | Memoria procedimental | Busca por hash de query: si este problema exacto fue resuelto antes, devuelve la táctica exitosa |
| **2** | Morfismo mediador | Si otro agente resolvió una query similar con una táctica compartida, esa táctica está guardada en `_mediating_memory` |
| **3** | Co-cono ponderado | Activa los skills del patrón relevantes para la query, ponderados por el peso de su morfismo hacia el colímite en el grafo |
| **4** | Señal de pilar (L1→L2) | Lee los morfismos L1→L2 del grafo, detecta keywords del pilar en la query y sugiere la táctica asociada al pilar dominante |
| **5** | Default por categoría | Tabla estática: algebra→`ring`, logic→`tauto`, number-theory→`norm_num`, computation→`decide`, etc. |

### MES Bridge — detección de convergencia y skills emergentes

El **MES Bridge** es el bus compartido que conecta los 14 agentes al sistema de memoria evolutiva:

```
Agente[algebra]  ──→┐
Agente[number-theory]──→┤ MES Bridge
Agente[...]      ──→┘
                        │
              record_success(query, tactic, reward)
                        │
               ┌────────┴────────┐
               │                 │
         ProceduralMemory    PatternManager
         por categoría       detecta convergencia:
         (O(1) lookup)       ¿2+ agentes resolvieron
                             la misma query?
                                 │
                                 ▼
                          ColimitBuilder
                          crea skill emergente
                          en el grafo
                          (complexificación)
```

Cuando 2 o más agentes resuelven la misma consulta, su táctica compartida se convierte en un **skill emergente**: un nuevo nodo colímite que el grafo añade automáticamente. Los morfismos mediadores quedan registrados en ambos agentes para queries futuras.

---

## 4. Memory Evolutive Systems (MES)

Los Memory Evolutive Systems son una teoría matemática desarrollada por A. Ehresmann para modelar sistemas cognitivos complejos. El sistema la implementa para modelar cómo el conocimiento matemático crece y se organiza.

### Los tres conceptos clave

**Patrón P: I → K**
Un patrón es una selección de skills relevantes para resolver un tipo de problema. Formalmente es un funtor de una categoría índice I hacia el grafo de skills K. Por ejemplo, para demostrar propiedades de números primos, el patrón incluiría skills de teoría de números, lógica y ZFC.

**Colímite cP**
El colímite de un patrón es el skill emergente que los sintetiza todos. Satisface la propiedad universal: cualquier otro skill que reciba morfismos de todos los componentes del patrón se factoriza de manera única a través de cP. El sistema verifica esta propiedad explícitamente mediante co-conos.

**Complexificación K'**
Cuando el sistema añade cP al grafo junto con sus co-conos, el grafo pasa de K a K'. Esta es la complexificación: el conocimiento crece sin perder la estructura anterior. Es el mecanismo formal del aprendizaje en este sistema.

### Axiomas implementados (8.1–8.4) y Teoremas (8.5–8.7)

| Axioma/Teorema | Descripción | Verificación |
|---|---|---|
| **8.1** Jerarquía | Los skills se organizan en niveles L0 < L1 < L2 | `tests/test_patterns.py` |
| **8.2** Multiplicidad | Un skill puede ser componente de múltiples patrones | `tests/test_patterns.py` |
| **8.3** Conectividad | Los patrones son conexos en el grafo | `tests/test_patterns.py` |
| **8.4** Cobertura | Los pilares cubren todas las categorías | `tests/test_pillar_agents.py` |
| **8.5** Emergencia | Si el patrón existe, el colímite existe y es único | `tests/test_colimit_agents.py` |
| **8.6** Absorción | Nuevos skills se integran sin destruir colímites previos | `tests/test_colimit_agents.py` |
| **8.7** Mediación | Entre dos colímites con solución común existe morfismo mediador único | `tests/test_colimit_agents.py` |

### Memoria procedimental

La memoria procedimental guarda qué tácticas funcionaron para qué tipos de problemas:

```python
# Cada entrada en memoria contiene:
{
    "query_text": "prove that n^2 + n is even",
    "tactic_used": "omega",
    "lean_goal": "⊢ ∀ n : ℕ, 2 ∣ n^2 + n",
    "reward": 1.0,
    "category": "number-theory"
}
```

Sembrada inicialmente con **2,371 patrones** de ProofNet y NuminaMath. Crece con cada interacción exitosa.

---

## 5. Red Neuronal GNN + PPO

### Por qué una GNN (Graph Neural Network)

El grafo de skills es heterogéneo: los nodos tienen diferentes tipos (L0, L1, L2) y los morfismos tienen diferentes tipos (dependencia, analogía, traducción, pilar→categoría). Las redes convencionales no aprovechan esta estructura. Una **GNN con atención** (GAT - Graph Attention Network) puede propagar información a través de los morfismos del grafo, de modo que el estado de un skill influye en sus vecinos.

Esto es especialmente relevante porque los PillarAgents (L1) inyectan información en los ColimitAgents (L2) a través de morfismos reales en el grafo — la GNN puede leer estos morfismos durante el forward pass.

### Por qué PPO (Proximal Policy Optimization)

El agente toma decisiones secuenciales: elegir qué hacer con una consulta matemática. PPO es un algoritmo de policy gradient que:
- Garantiza que cada actualización no se aleje demasiado de la política anterior (la "región de confianza" o *clip*)
- Usa GAE (Generalized Advantage Estimation) para estimar cuánto mejor es una acción respecto al estado promedio
- Es estable y funciona bien con muestras escasas — crítico cuando las recompensas Lean son lentas de obtener

### Arquitectura completa

```
Entrada: query (texto) + grafo de skills (PyG)
         │
         ▼
  encode_query()          encode_goal()
  TF-IDF → 256-dim        "prove ..." → 128-dim
         │                      │
         └──────────┬───────────┘
                    │  concat → 384-dim
                    ▼
  SkillGNN (lee el grafo con atención):
    node_proj  →  feat_dim × 64
    GATConv 1  →  64  × 256  × 4 heads   ~  66,560 params
    GATConv 2  →  256 × 256  × 4 heads   ~ 262,144 params
    GATConv 3  →  256 × 256  × 4 heads   ~ 262,144 params
    out_proj   →  256 × 128              ~  32,896 params
                    │  graph_embedding 128-dim
                    │
  ActorCriticNetwork:
    shared_net →  384 × 256 × 128        ~ 148,736 params
         │
    ┌────┴────┐
    │         │
  actor     critic
  128×3      128×1
  ~387p      ~129p
    │
    ▼
  Acción:  ASSIST_LEAN | RESPOND_DIRECT | REQUEST_CLARIFICATION
```

**Total: 546,820 parámetros entrenables — 2.2 MB en disco**

### Resultados de entrenamiento

**Fase 1 — Supervisado** (todos los problemas → ASSIST):

| Métrica | Resultado |
|---|---|
| Dataset | 52,237 train · 6,552 val · 12,874 test |
| Convergencia | Época 1 |
| train_acc / val_acc / test_acc | **100% / 100% / 100%** |

**Fase 2 — PPO con recompensas reales de Lean** (5 épocas, RTX 3050):

| Época | Loss | Avg Reward | Assist% |
|---|---|---|---|
| 1 | 0.0746 | 0.573 | 100% |
| 3 | 0.0163 | 0.562 | 100% |
| 5 | 0.0172 | **0.578** | 100% |

El reward promedio de ~0.57 refleja la distribución real del dataset: ~70% problemas aritméticos donde `norm_num` verifica (+1.0) y ~30% álgebra abstracta donde no hay respuesta numérica (+0.5 base). Esta discriminación es la señal que el PPO aprende.

> **Checkpoint activo**: `data/neural_agent.json.pt` contiene los pesos de la Fase 2 (`epoch_005`, avg_reward=0.578). Se cargan automáticamente al iniciar el sistema. Los pesos de Fase 1 (supervisado puro) están disponibles en `data/neural_agent.json.pt.phase1_backup`.

### Aprendizaje vivo

Cada interacción del usuario alimenta el ciclo de aprendizaje:

```
Usuario hace consulta
        │
  ColimitAgent.select_tactic()
        │
  Lean verifica
        │
  record_result(reward)
        │
  ┌─────┴─────┐
  │           │
memoria    Transition
procedi-   → PPO buffer
mental     → cada 10 interacciones:
             agent.update()
             save weights
```

---

## 6. Co-Reguladores

Los co-reguladores son el mecanismo de control de flujo del NLE, inspirados en la teoría MES de Ehresmann donde los co-reguladores son subsistemas que regulan la actividad de la categoría sin ser parte de su contenido.

En la práctica, los 4 co-reguladores son filtros/enrutadores que procesan cada consulta antes de llegar a los agentes especializados:

| Co-regulador | Umbral de activación | Función |
|---|---|---|
| **TACTICAL (CR_tac)** | 80% del tráfico | Clasifica la consulta y decide si ir al pipeline Lean o responder directamente. Es el primer filtro. |
| **ORGANIZATIONAL (CR_org)** | Consultas multi-paso | Cuando la demostración requiere varios pasos, organiza la secuencia de tácticas |
| **STRATEGIC (CR_str)** | 20% del tráfico | Decide la estrategia de alto nivel: ¿backward reasoning? ¿casos? ¿inducción? |
| **INTEGRATIVE (CR_int)** | Resultados parciales | Integra resultados de múltiples sub-demostraciones en una prueba coherente |

---

## 7. Cómo funciona: flujo completo de una consulta

Esta sección explica, paso a paso y sin asumir conocimientos previos de IA, qué ocurre dentro del sistema desde el momento en que el usuario escribe una pregunta hasta que aparece la respuesta en pantalla.

---

### El principio fundamental

> **El sistema nunca inventa matemáticas.** El LLM (Claude, Gemini, etc.) se usa únicamente como traductor — para convertir lenguaje natural en código Lean y para volver a convertir el resultado de Lean en palabras entendibles. La decisión de si algo es matemáticamente correcto la toma siempre Lean 4.

Piénsalo con esta analogía de tres actores:

| Actor | Rol en la analogía | Rol real en el sistema |
|---|---|---|
| **NLE — Núcleo Lógico Evolutivo** | El **director de orquesta**: recibe la consulta, decide qué experto debe atenderla, coordina todos los pasos, aprende de cada interacción y gestiona la memoria del sistema | `nucleo/core.py` — orquesta CRs, agentes, Lean y LLM |
| **LLM** (Claude, Gemini…) | El **intérprete bilingüe**: traduce la pregunta del usuario al lenguaje formal de Lean, y al final traduce el resultado de Lean de vuelta a palabras entendibles | Formalización → Lean 4; traducción → lenguaje natural |
| **Lean 4** | El **juez inapelable**: recibe el código y dice "correcto" o "incorrecto". No negocia ni opina — solo verifica | Verificador formal, fuente de verdad matemática |

El NLE es quien dirige: sin él, el LLM y Lean son herramientas sin conexión. El NLE decide *cuándo* llamar al LLM, *qué* enviar a Lean, *qué hacer* si Lean rechaza el código, *cómo* aprender del resultado y *qué* mostrarle finalmente al usuario.

---

### Vista panorámica

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                        USUARIO                                      │
 │   "demuestra que la raíz de 2 es irracional"                        │
 └──────────────────────┬──────────────────────────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  PASO 1 — ¿Es una pregunta matemática?                               │
 │  El sistema busca símbolos (∀ ∃ ∈ ℝ), LaTeX (\sqrt) y 80+           │
 │  palabras clave, incluyendo nombres propios y variantes con acento   │
 │  (pitágoras/pitagoras, raíz/raiz, irracional…)                       │
 │                                                                      │
 │  SÍ → Paso 1b                                                        │
 │  NO → responde directamente con el LLM (saludo, pregunta general)    │
 └──────────────────────┬───────────────────────────────────────────────┘
                        │ (es matemática)
                        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  PASO 1b — ¿Es una consulta educativa/histórica/visual?              │
 │                                                                      │
 │  Si contiene patrones como "demostración geométrica",                │
 │  "como lo enunció [autor]", "al estilo de Euclides",                 │
 │  "prueba clásica", "intuición"… el sistema detecta que              │
 │  el usuario quiere una explicación visual o histórica,               │
 │  no un bloque de Lean 4.                                             │
 │                                                                      │
 │  SÍ → _math_educational_explanation()                                │
 │        LLM responde en lenguaje natural rico con:                    │
 │        1. Enunciado formal (LaTeX), 2. Contexto histórico,           │
 │        3. Demostración geométrica/visual, 4. Nota Lean (breve)       │
 │                                                                      │
 │  NO → pipeline matemático Lean-primero (pasos 2–8)                   │
 └──────────────────────┬───────────────────────────────────────────────┘
                        │ (es matemática)
                        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  PASO 2 — Co-Reguladores votan la estrategia                         │
 │                                                                      │
 │  CR_tac  → "¿contiene código Lean ya escrito?" → ASSIST o RESPONSE   │
 │  CR_org  → "¿es multi-paso?"                                         │
 │  CR_str  → "¿qué estrategia global conviene?"                        │
 │  CR_int  → árbitro: elige la opción con mayor consenso               │
 └──────────────────────┬───────────────────────────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  PASO 3 — Agente especializado (GNN + PPO)                           │
 │                                                                      │
 │  El MultiAgentOrchestrator clasifica la pregunta en una de           │
 │  14 categorías (álgebra, análisis, topología, teoría de números…)    │
 │  y activa el agente entrenado para esa categoría.                    │
 │                                                                      │
 │  Ejemplo: "raíz de 2 irracional" → agente number-theory             │
 └──────────────────────┬───────────────────────────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  PASO 4 — Búsqueda de ejemplos similares (few-shot)                  │
 │                                                                      │
 │  El sistema busca en su banco de 157 pruebas de miniF2F              │
 │  ejemplos parecidos al problema actual. Estos ejemplos se            │
 │  incluyen en el prompt para que el LLM tenga referencias concretas.  │
 └──────────────────────┬───────────────────────────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  PASO 5 — LLM formaliza el enunciado en Lean 4                       │
 │                                                                      │
 │  El LLM actúa como "formalizador": su única tarea es escribir        │
 │  UN SOLO bloque de código Lean 4 con el enunciado y, si puede,       │
 │  la prueba. El prompt incluye referencias hardcoded de Mathlib       │
 │  para los teoremas clásicos más pedidos.                             │
 │                                                                      │
 │  Entrada: "demuestra que √2 es irracional"                           │
 │  Salida:  theorem sqrt2_irrat : Irracional (Real.sqrt 2) := by ...   │
 │                                                                      │
 │  Si el LLM no sabe la prueba completa, usa `sorry` como marcador.   │
 │                                                                      │
 │  ⚠ Guardia anti-tautología: si el LLM genera código trivial         │
 │  (toma la ecuación principal como hipótesis y la concluye           │
 │  por simetría), el sistema detecta el patrón y regenera con         │
 │  un prompt más estricto que exige tipos de Mathlib reales.          │
 └──────────────────────┬───────────────────────────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  PASO 5b — Normalización del código (automática)                     │
 │                                                                      │
 │  Antes de enviar a Lean, el sistema repara el código automáticamente:│
 │  • Inyecta imports de Mathlib faltantes según el contenido           │
 │    (InnerProductSpace, Topology, Calculus, etc.)                     │
 │  • Renombra lemas obsoletos a sus nombres actuales                   │
 │  • Añade la cabecera base con Ring, Linarith, NormNum, Omega         │
 └──────────────────────┬───────────────────────────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  PASO 6 — Lean 4 verifica el código                                  │
 │                                                                      │
 │  Lean compila el código. Hay tres posibles resultados:               │
 │                                                                      │
 │  ✅ ÉXITO    → la prueba es correcta, confianza: 95%                 │
 │  ⚠ SORRY   → la estructura es válida pero hay huecos → Paso 6b      │
 │  ❌ ERROR   → la prueba tiene errores → se diagnostica y reporta     │
 └──────────────────┬───────────────┬──────────────────────────────────-┘
                    │(sorry)        │(error)
                    ▼               ▼
 ┌──────────────────────┐  ┌────────────────────────────────────────────┐
 │  PASO 6b             │  │  Diagnóstico de error                      │
 │  SolverCascade       │  │                                            │
 │  intenta tácticas    │  │  El sistema identifica el tipo de error:   │
 │  automáticamente:    │  │  • unknown identifier → falta un import    │
 │                      │  │  • type mismatch → tipos incompatibles     │
 │  rfl   (trivial)     │  │  • failed to synthesize → falta typeclass  │
 │  simp  (simplificar) │  │  • tactic failed → táctica no cierra goal  │
 │  ring  (álgebra)     │  │                                            │
 │  omega (aritmética)  │  │  Esta información se incluye en la         │
 │  aesop (heurística)  │  │  respuesta para que el usuario entienda    │
 │                      │  │  qué necesita corregirse.                  │
 └──────────┬───────────┘  └────────────────────────────────────────────┘
            │
            ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  PASO 7 — LLM traduce el resultado a lenguaje natural                │
 │                                                                      │
 │  El LLM ahora actúa como "traductor": recibe el código Lean          │
 │  y el estado de verificación, y genera una explicación en tres       │
 │  secciones:                                                          │
 │                                                                      │
 │  ## ¿Qué dice este resultado?                                        │
 │  [En tus palabras, sin jerga técnica]                                │
 │                                                                      │
 │  ## ¿Cómo lo demuestra Lean?                                         │
 │  [Qué hace cada táctica importante]                                  │
 │                                                                      │
 │  ## ¿Por qué es correcto?                                            │
 │  [La intuición matemática detrás del argumento]                      │
 └──────────────────────┬───────────────────────────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  PASO 8 — Aprendizaje y memoria                                      │
 │                                                                      │
 │  El resultado se registra en la memoria MES del sistema:             │
 │  • ¿La prueba fue exitosa? → refuerzo positivo en PPO                │
 │  • El patrón (query → táctica → resultado) se guarda                 │
 │  • Si el mismo tipo de problema aparece de nuevo, el sistema         │
 │    ya tiene experiencia previa y mejora su respuesta                 │
 │  • Los pesos del agente se actualizan cada 10 interacciones          │
 └──────────────────────┬───────────────────────────────────────────────┘
                        │
                        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  RESPUESTA AL USUARIO                                                │
 │                                                                      │
 │  [Explicación en lenguaje natural]                                   │
 │  ──────────────────────────────                                      │
 │  ✅ Lean 4: verificado formalmente                                   │
 │                                                                      │
 │  ```lean                                                             │
 │  theorem sqrt2_irrat : Irrational (Real.sqrt 2) := by               │
 │    exact irrational_sqrt_two                                         │
 │  ```                                                                 │
 └──────────────────────────────────────────────────────────────────────┘
```

---

### ¿Qué ocurre si no es una pregunta matemática?

Si el usuario escribe "hola" o "¿qué eres?", el sistema detecta que no hay contenido matemático y responde directamente con el LLM usando el contexto del grafo de skills, sin invocar Lean. El tiempo de respuesta es mucho menor en este caso.

---

### ¿Qué muestra la pestaña de Visualizaciones?

Después de cada consulta, el botón **"📊 Ver grafo · embeddings…"** abre un panel con:

| Pestaña | Qué muestra |
|---|---|
| **Grafo de Skills** | Los 76 nodos del grafo categórico. Los skills activados por tu consulta se resaltan en amarillo; sus dependencias en morado; las tácticas usadas en verde. |
| **Embeddings** | Proyección t-SNE/PCA de los 76 skills en 2D. Las **estrellas naranjas** son tus consultas del chat, proyectadas en el mismo espacio vectorial — su posición indica qué dominio matemático el sistema asoció a cada pregunta. |
| **MES / Complexificación** | El patrón P que activó tu consulta y el colímite resultante — cómo el sistema sintetizó conocimientos para responder. |
| **Pipeline** | El diagrama de flujo completo del sistema en tiempo real. |
| **Agentes** | El árbol jerárquico de los 14 agentes especializados y sus métricas de entrenamiento (F1/F2). |

---

## 9. Datasets

El sistema integra **5.4M+ ejemplos matemáticos** de datasets públicos, organizados en 14 categorías balanceadas:

| Dataset | Ejemplos | Categorías principales |
|---|---|---|
| **OpenMathReasoning** | 3,201,061 | algebra, number-theory, analysis, competition math |
| **NuminaMath** | 859,494 | algebra, combinatorics, number-theory, geometry |
| **MetaMathQA** | 395,000 | algebra, arithmetic (aumentado con parafraseo) |
| **Autoformalization** | 327,000 | lean-tactics (pares NL ↔ Lean) |
| **OrcaMath** | 200,000 | algebra, arithmetic (razonamiento paso a paso) |
| **OpenR1Math** | 93,000 | proof-strategies (cadenas de pensamiento largas) |
| **LeanWorkbook + Proofs** | 54,000 | lean-tactics (enunciados + pruebas Lean reales) |
| **BigBench Formal Fallacies** | 14,200 | logic (detección de falacias formales) |
| **HendrycksMath** | 12,500 | algebra, calculus, statistics (5 niveles de dificultad) |
| **OmniMath** | 4,400 | competencias internacionales (IMO, APMO, Putnam) |
| **ProofNet** | 371 | proof-strategies, lean-tactics (pruebas formales verificadas) |
| **GSM8K + MATH + miniF2F** | ~21,000 | aritmética, álgebra (benchmark de referencia) |

Los splits balanceados (80/10/10 con upsampling para categorías pequeñas como `computation`) se generan con `scripts/balance_datasets.py`.

---

## 8. Tests

```bash
python -m pytest tests/ -o "addopts=" -v
```

379 tests en 17 suites, organizadas por subsistema:

| Suite | Tests | Qué verifica |
|---|---|---|
| `test_colimits.py` | 28 | Propiedad universal, co-conos, morfismo mediador |
| `test_evolution.py` | 22 | Complexificación, snapshots, functores de transición |
| `test_emergence.py` | 18 | Clasificación de links simples/complejos, detección de emergencia |
| `test_multiplicity.py` | 15 | Principio de multiplicidad de Ehresmann |
| `test_co_regulators.py` | 20 | 4 CRs activos, E-equivalencia |
| `test_gnn.py` | 25 | SkillGNN forward pass, graph_to_pyg() |
| `test_ppo.py` | 18 | PPO update, GAE, clipping |
| `test_lean.py` | 30 | Cliente Lean 4, SolverCascade, sorry analyzer |
| `test_memory.py` | 22 | MES Memory, patrones procedimentales |
| `test_live_learning.py` | 10 | Chat → PPO → weights update ciclo completo |
| `test_cli.py` | 10 | `python -m nucleo chat` REPL |
| `test_multi_agent.py` | 35 | ColimitAgent, PillarAgent, MES Bridge, classify_query() |
| `test_patterns.py` | 26 | Axiomas 8.1-8.4, Teoremas 8.5-8.7 |
| `test_math_domains.py` | 32 | 76 skills en 14 categorías |
| + 3 suites auxiliares | ~68 | Config, types, eval, graph base |

---

## 10. Aplicación Web

La interfaz Streamlit permite usar el sistema sin escribir código:

```bash
pip install -r requirements.txt

# Windows: necesario para caracteres Unicode matemáticos (∀, ∃, ∈, ⊢...)
PYTHONIOENCODING=utf-8 streamlit run app.py
```

Abre en: `http://localhost:8501`

### Diseño visual

La interfaz usa una paleta cálida oscura (inspirada en plataformas de juegos de estrategia clásica): fondo carbón-marrón `#1c1917`, acentos ámbar/dorado `#d4a853`, tipografía Sora. El hero central incluye una textura de cuadrícula y una animación de pulso suave que enfatiza el carácter de sistema vivo y evolutivo.

### Funcionalidades de la interfaz

| Funcionalidad | Descripción |
|---|---|
| **Chat multi-turno** | Conversación continua con historial de sesión. El contexto se sincroniza con la memoria interna del NLE. |
| **Adjuntar archivos (📎)** | Botón paperclip bajo la barra de chat. Soporta `.txt`, `.tex` y `.pdf`. El sistema extrae el texto y lanza un pipeline de verificación matemática de 6 pasos: identificar el tipo de resultado, verificar la demostración, evaluar conjeturas abiertas, sugerir Lean 4 y dar un veredicto. |
| **Ejemplos rápidos** | 4 botones de ejemplo preconfigurados en la parte superior (√2 irracional, Lema de Yoneda, Lean 4 directo, Curry-Howard). |
| **Visualizaciones** | Botón "📊 Ver grafo · embeddings · traza categórica" que abre el panel de visualización tras cada consulta. |
| **Enrutamiento educativo** | Cuando el usuario pide una "demostración geométrica", "como lo enunció [autor]" o "al estilo de Euclides", el sistema detecta la intención histórica/visual y responde en lenguaje natural enriquecido antes de presentar el Lean 4. |

### Modo Demo (sin API key)

Si no se configura ninguna API key, el sistema entra en **modo demo**: en lugar de respuestas genéricas, entrega contenido matemático real estructurado que incluye enunciado formal, demostración clásica, código Lean 4 funcional con Mathlib, y referencias. Actualmente cubre: Teorema de Pitágoras, irracionalidad de √2, Lema de Yoneda, Correspondencia Curry-Howard.

### Proveedores LLM soportados

| Proveedor | Modelos | Costo |
|---|---|---|
| **Google AI Studio** | Gemini 2.0 Flash, Gemini 1.5 Pro | Gratis (con cuota) |
| **Groq** | Llama 3.3 70B, Mixtral 8x7B | Gratis |
| **Anthropic** | Claude Haiku 4.5, Claude Sonnet 4.6 | De pago |
| **Demo** | Contenido matemático local | Sin key |

La visualización (`pages/1_Visualizaciones.py`) muestra el grafo de skills en tiempo real, los morfismos activos, el historial de complexificaciones y la traza de la última prueba Lean.

---

## 11. Entrenamiento

El entrenamiento del sistema tiene tres etapas independientes. Pueden correrse por separado.

### Etapa A — Balancear datasets (prerequisito de B)

Extrae, clasifica y balancea todos los datasets en splits por categoría:

```bash
# Estadísticas sin escribir nada
python scripts/balance_datasets.py --dry-run

# Generar splits balanceados (target: 5000 ejemplos por categoría)
# Salida: E:/datadeentrenamientovalidacion_test/by_category/<cat>/{train,val,test}.jsonl
python scripts/balance_datasets.py --target 5000
```

### Etapa B — Entrenar los 14 agentes especializados

Requiere que Etapa A haya generado los splits:

```bash
# Entrenar los 14 agentes (supervisado, ~1h en RTX 3050)
python scripts/train_multiagent.py --epochs 5

# Solo algunas categorías
python scripts/train_multiagent.py --categories algebra number-theory logic --epochs 10

# Fase PPO con recompensas reales de Lean (requiere lake + Mathlib)
python scripts/train_multiagent.py --with-lean --ppo-epochs 3

# Verificar que los datos existen sin entrenar
python scripts/train_multiagent.py --dry-run
```

Los pesos de cada agente se guardan en `data/agents/<categoria>.pt`.

### Etapa C — Entrenar el GNN+PPO global

El agente global (que decide ASSIST vs RESPOND para cualquier consulta):

```bash
# Preparar splits globales (MATH + GSM8K + NuminaMath + ProofNet)
python scripts/prepare_training_data.py

# Fase 1: supervisado (~20 min en RTX 3050)
python scripts/train_gnn_ppo.py --epochs 10 --batch-size 256

# Fase 2: PPO con Lean real (slow — cada ejemplo llama a lake env lean)
python scripts/train_gnn_ppo.py --resume --with-lean --lean-samples 300 --epochs 0 --ppo-epochs 5

# Reanudar desde checkpoint
python scripts/train_gnn_ppo.py --resume --epochs 5
```

Los pesos globales se guardan en `data/neural_agent.json.pt` y se cargan automáticamente al iniciar el sistema.

### Etapa D — Sembrar la memoria procedimental

Conecta ProofNet y NuminaMath a la memoria MES antes del primer uso:

```bash
python scripts/seed_from_datasets.py
```

Esto guarda 2,371 patrones iniciales en `data/memory.json`.

---

## 12. Estructura del Repositorio

```
Metamatematico/
│
├── app.py                         # App Streamlit — interfaz de chat
├── pages/
│   └── 1_Visualizaciones.py       # Grafos, embeddings, MES, traza de prueba
│
├── nucleo/                        # Núcleo Lógico Evolutivo (~13,500 LOC)
│   ├── core.py                    # Orquestador principal: Lean-first + multi-agente
│   ├── config.py                  # Configuración centralizada (rutas, modelos, thresholds)
│   │
│   ├── multi_agent/               # Sistema multi-agente de colímites
│   │   ├── orchestrator.py        # MultiAgentOrchestrator (L3): classify + route
│   │   ├── colimit_agents.py      # ColimitAgent (L2) + ColimitAgentSystem
│   │   ├── pillar_agents.py       # PillarAgent (L1) + PillarAgentSystem
│   │   ├── specialized_agent.py   # SpecializedAgent: GNN+PPO por categoría
│   │   └── mes_bridge.py          # MESBridge: convergencia → skills emergentes
│   │
│   ├── graph/                     # Grafo categórico de skills
│   │   ├── category.py            # SkillCategory (NetworkX): nodos, morfismos, links
│   │   ├── evolution.py           # Complexificación, snapshots, functores de transición
│   │   └── math_domains.py        # 76 skills en 14 categorías matemáticas
│   │
│   ├── mes/                       # Memory Evolutive Systems
│   │   ├── patterns.py            # Patrones, colímites, propiedad universal verificada
│   │   ├── memory.py              # MES Memory: patrones procedimentales, snapshots
│   │   └── co_regulators.py       # 4 Co-reguladores activos (TAC/ORG/STR/INT)
│   │
│   ├── rl/                        # Aprendizaje por refuerzo
│   │   ├── agent.py               # NucleoAgent: PPO + GAE + memoria procedimental
│   │   ├── gnn.py                 # SkillGNN: 3× GATConv + graph_to_pyg()
│   │   ├── networks.py            # ActorCriticNetwork (546K params)
│   │   └── mdp.py                 # MDP matemático: estados, acciones, recompensas
│   │
│   ├── lean/                      # Verificación formal Lean 4
│   │   ├── client.py              # Cliente Lean 4 (subprocess, UTF-8, timeout)
│   │   ├── solver_cascade.py      # rfl → simp → ring → omega → aesop
│   │   └── sorry_analyzer.py      # Análisis estructurado de pruebas incompletas
│   │
│   ├── llm/                       # Cliente LLM multi-proveedor
│   │   └── client.py              # Anthropic / Google / Groq / Demo
│   │
│   ├── pillars/                   # Pilares fundacionales (skills L0)
│   │   ├── zfc.py                 # 8 skills: naive-sets, zfc-axioms, ordinals...
│   │   ├── category_theory.py     # 8 skills: cat-basics, functors, nat-trans...
│   │   ├── logic.py               # 7 skills: propositional, fol-syntax, sequent-calc...
│   │   └── type_theory.py         # 8 skills: stlc, system-f, dependent-types...
│   │
│   └── eval/                      # Evaluación de respuestas
│       └── math_evaluator.py      # \boxed{} extraction, tolerancia numérica, sympy
│
├── MetamathProver/                # Pruebas Lean 4 verificadas (8 archivos .lean)
│
├── scripts/                       # Entrenamiento y utilidades de datos
│   ├── balance_datasets.py        # Etapa A: 5.4M ejemplos → splits por categoría
│   ├── train_multiagent.py        # Etapa B: entrena 14 agentes especializados
│   ├── prepare_training_data.py   # Etapa C: splits para GNN+PPO global
│   ├── train_gnn_ppo.py           # Etapa C: entrena GNN+PPO (2 fases)
│   ├── seed_from_datasets.py      # Etapa D: siembra 2371 patrones en MES Memory
│   └── evaluate_benchmark.py      # Evalúa el sistema en MATH/GSM8K
│
├── data/                          # Datos generados (no todos versionados)
│   ├── lean_examples.json         # 157 ejemplos few-shot miniF2F (versionado)
│   ├── memory.json                # MES Memory sembrada (versionado)
│   ├── neural_agent.json.pt       # Pesos GNN+PPO entrenados (versionado)
│   └── agents/                    # Pesos por categoría: <categoria>.pt (14 archivos)
│
├── tests/                         # 379 tests en 17 suites
├── docs/                          # Paper NLE v7.0 (Jiménez Martínez, BIOMAT 2025)
└── experiments/                   # Cuadernos y experimentos explorativos
```

---

## 13. Instalación

```bash
git clone https://github.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean.git
cd Metamatematico---Razonamiento-Formal-con-Lean

# Entorno recomendado (Python 3.10)
conda create -n metamat python=3.10
conda activate metamat

pip install -r requirements.txt
```

### Lean 4 + Mathlib (opcional, necesario para verificación real)

```bash
# Instalar elan (gestor de versiones de Lean)
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh

# Descargar Mathlib (tarda 20-30 min la primera vez)
lake update
```

> **Nota**: Sin Lean instalado, el sistema funciona en modo degradado: las respuestas matemáticas pasan por el LLM sin verificación formal.

### Dependencias principales

```
torch>=2.0              # GNN + PPO
torch-geometric>=2.4    # GATConv, PyG graph format
networkx>=3.0           # Grafo categórico de skills
streamlit>=1.40         # Interfaz web
numpy>=1.24
scikit-learn>=1.3       # TF-IDF para encode_query
sympy>=1.12             # Evaluación simbólica de respuestas
anthropic               # (o google-genai, o groq — según proveedor)
```

### Lanzar la aplicación

```bash
# Windows (necesario para símbolos Unicode matemáticos)
PYTHONIOENCODING=utf-8 streamlit run app.py

# CLI interactivo (sin Streamlit)
python -m nucleo chat
```

---

## 14. Fundamento Teórico

El NLE v7.0 está basado en el artículo **"Núcleo Lógico Evolutivo v7.0 — Memory Evolutive Systems y Razonamiento Formal"** (Jiménez Martínez, BIOMAT 2025), disponible en `docs/`.

### La intuición central

Un matemático experto no reapende álgebra de cero cada vez que resuelve un problema. Su conocimiento está organizado en **competencias** (skills) que se activan según el contexto, y cuando resuelve un problema nuevo, sintetiza competencias previas en una competencia nueva (emergente). Esta es exactamente la estructura que los Memory Evolutive Systems formalizan.

La jerarquía L0→L1→L2→L3 en este sistema refleja esa estructura:
- L0 son los **axiomas** (ZFC, lógica, tipos, categorías) — el conocimiento más fundamental
- L1 son los **pilares** — síntesis de los axiomas de cada fundamento
- L2 son las **áreas matemáticas** — síntesis de skills de dominio + señales de pilares
- L3 es el **sistema completo** — síntesis de todas las áreas, punto de entrada único

Cada nivel es un colímite del nivel anterior. Esta es la implementación computacional directa del Teorema 2.10 (Complexificación) de Ehresmann.

### Por qué teoría de categorías y no otra formalización

La teoría de categorías es el lenguaje natural de las matemáticas modernas: expresa relaciones entre estructuras (morfismos) con la misma precisión que las estructuras mismas (objetos). Usar categorías para organizar el conocimiento matemático es coherente con el dominio que el sistema maneja. No es una elección arbitraria — es la misma formalización que los matemáticos usan para relacionar álgebra, topología, lógica y computación entre sí.

---

**Leonardo Jiménez Martínez · BIOMAT · Centro de Biomatemáticas · UNAM · 2025**
