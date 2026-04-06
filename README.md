# METAMATEMÁTICO — Razonamiento Formal con Lean 4

[![Lean 4](https://img.shields.io/badge/Lean-4-blue.svg)](https://lean-lang.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://python.org/)
[![Tests](https://img.shields.io/badge/Tests-379_passing-brightgreen.svg)](#tests)
[![Agents](https://img.shields.io/badge/Agents-14_categor%C3%ADas-blueviolet.svg)](#sistema-multi-agente)
[![GNN+PPO](https://img.shields.io/badge/GNN%2BPPO-546K_params-red.svg)](#gnn--ppo)
[![Dataset](https://img.shields.io/badge/Dataset-2.29M_ejemplos-orange.svg)](#datasets)
[![Streamlit](https://img.shields.io/badge/App-Streamlit-ff4b4b.svg)](#aplicacion-web)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Leonardo Jiménez Martínez · BIOMAT · Centro de Biomatemáticas**

Asistente de razonamiento matemático formal basado en el **Núcleo Lógico Evolutivo (NLE v7.0)**: un sistema que integra Memory Evolutive Systems, teoría de categorías, verificación en Lean 4 y un sistema multi-agente de 18 colímites activos.

---

## Principio de diseño: Lean primero

**Toda consulta matemática pasa obligatoriamente por Lean 4 antes de producir una respuesta.**

El LLM actúa únicamente como:
1. **Formalizador**: traduce el enunciado en lenguaje natural a código Lean 4
2. **Traductor**: convierte el resultado verificado de Lean a lenguaje natural accesible

El NLE nunca responde matemáticas directamente desde el LLM. Lean es la fuente de verdad.

```
Consulta matematica
       |
       v
  MultiAgentOrchestrator (L3)
  classify_query() --> categoria matematica
       |
       v
  ColimitAgent[categoria] (L2)  <-- PillarAgent[pilar] (L1)
       |
       v
  LLM formaliza  -->  Lean 4 verifica  -->  LLM traduce  -->  Respuesta
                           |
                  SolverCascade si hay sorry:
                  rfl -> simp -> ring -> omega -> aesop
```

---

## Sistema Multi-Agente: Jerarquía de Colímites

El núcleo del sistema es una **jerarquía de 4 niveles** donde cada agente es literalmente el nodo colímite en el grafo categórico de skills. No son agentes externos que leen el grafo — son el grafo mismo.

```
L0: 31 skills atómicos de los pilares
    ZFC(8) · CatThy(8) · Logic(7) · TypeThy(8)
         │  co-conos
         ▼
L1: 4 PillarAgents  (colímites de L0)
    colim[ZFC]     colim[CatThy]
    colim[Logic]   colim[TypeThy]
         │  morfismos pilar → categoría
         ▼
L2: 14 ColimitAgents  (colímites de L1 + skills de dominio)
    colim[algebra]       colim[topology]     colim[logic]
    colim[number-theory] colim[analysis]     colim[combinatorics]
    colim[set-theory]    colim[probability]  colim[category-theory]
    colim[computation]   colim[geometry]     colim[optimization]
    colim[lean-tactics]  colim[proof-strategies]
         │  co-conos
         ▼
L3: MultiAgentOrchestrator  (colímite de colímites)
    Propiedad universal: mediating morphism único
```

### Pilares Fundacionales → Categorías

Cada pilar inyecta morfismos en las categorías que fundamenta:

| Pilar (L1) | Categorías que nutre (L2) |
|---|---|
| **ZFC** | algebra, set-theory, combinatorics, number-theory, probability, analysis |
| **Teoría de Categorías** | category-theory, topology, algebra, analysis |
| **Lógica (FOL+IL)** | logic, proof-strategies, lean-tactics, computation, set-theory |
| **Teoría de Tipos (Curry-Howard)** | lean-tactics, proof-strategies, computation, logic |

### MES Bridge — Convergencia Emergente

El **MES Bridge** conecta los 14 agentes al sistema de memoria evolutiva:

- Si 2+ agentes resuelven la misma consulta → **ColimitBuilder crea un skill emergente** en el grafo
- Cada solución exitosa se almacena en **ProceduralMemory** por categoría
- Los agentes consultan la memoria antes de la red neuronal (recuperación rápida O(1))
- El grafo evoluciona mediante complexificación cada vez que emerge un nuevo colímite

---

## Arquitectura Completa

```
+-----------------------------------------------------------------------+
|                    NUCLEO LOGICO EVOLUTIVO (NLE v7.0)                 |
|                       Sigma_t = (L, CR_t, G_t, F)                    |
+-----------------------------------------------------------------------+
|                                                                       |
|  Usuario --> MultiAgentOrchestrator (L3)                              |
|                    |                                                  |
|              classify_query()  (14 categorias)                        |
|                    |                                                  |
|         +----------+----------+                                       |
|         |                     |                                       |
|  ColimitAgent[cat] (L2)   PillarAgent[pilar] (L1)                    |
|  · select_tactic()        · inject_into_category_agent()             |
|  · record_result()        · record_usage()                            |
|  · absorb_new_skill()     · most_used_axioms()                        |
|  · mediate()                                                          |
|         |                                                             |
|  MES Bridge (compartido por los 14 agentes)                           |
|  · record_success() --> ProceduralMemory + PatternManager             |
|  · _handle_convergence() --> ColimitBuilder --> skill emergente        |
|  · query_best_tactic() --> memoria procedimental                      |
|                                                                       |
|  +-------------------------------------------------------------------+|
|  |  Memory Evolutive Systems (Ehresmann)                             ||
|  |  Patrones P -> Colimites cP -> Complexificacion K'               ||
|  |  Axiomas 8.1-8.4 . Teoremas 8.5-8.7                             ||
|  +-------------------------------------------------------------------+|
|                                                                       |
|  +-------------------------------------------------------------------+|
|  |  GNN + PPO (546K params)                                         ||
|  |  SkillGNN (3x GATConv) + ActorCriticNetwork                     ||
|  |  Aprendizaje vivo: cada interaccion alimenta PPO                 ||
|  +-------------------------------------------------------------------+|
|                                                                       |
|  +-------------------------------------------------------------------+|
|  |  Lean-first Pipeline                                             ||
|  |  LLM formaliza -> Lean 4 verifica -> SolverCascade -> traduccion||
|  +-------------------------------------------------------------------+|
+-----------------------------------------------------------------------+
```

---

## Estructura del Repositorio

```
metamath-prover/
|
+-- app.py                        # App Streamlit (interfaz de chat)
+-- pages/
|   +-- 1_Visualizaciones.py      # Grafos, embeddings, MES, traza de prueba
|
+-- nucleo/                       # Nucleo Logico Evolutivo (~13,500 LOC)
|   +-- core.py                   # Orquestador principal (Lean-first + multi-agente)
|   +-- config.py                 # Configuracion centralizada
|   |
|   +-- multi_agent/              # Sistema multi-agente (NUEVO)
|   |   +-- orchestrator.py       # MultiAgentOrchestrator: enruta a 14 agentes
|   |   +-- colimit_agents.py     # ColimitAgent (L2) + ColimitAgentSystem
|   |   +-- pillar_agents.py      # PillarAgent (L1) + PillarAgentSystem
|   |   +-- specialized_agent.py  # SpecializedAgent: GNN+PPO por categoria
|   |   +-- mes_bridge.py         # MESBridge: convergencia y skills emergentes
|   |
|   +-- graph/                    # Grafo categorico de skills
|   |   +-- category.py           # SkillCategory (NetworkX), links simples/complejos
|   |   +-- evolution.py          # Complexificacion, snapshots, functores de transicion
|   |   +-- math_domains.py       # 76 skills en 14 categorias matematicas
|   +-- mes/                      # Memory Evolutive Systems
|   |   +-- patterns.py           # Patrones, colimites, propiedad universal
|   |   +-- memory.py             # MES Memory, patrones procedimentales
|   |   +-- co_regulators.py      # 4 Co-reguladores activos (TAC/ORG/STR/INT)
|   +-- rl/                       # Aprendizaje por refuerzo
|   |   +-- agent.py              # NucleoAgent (PPO + memoria procedimental)
|   |   +-- gnn.py                # SkillGNN (3x GATConv)
|   |   +-- networks.py           # ActorCriticNetwork
|   |   +-- mdp.py                # MDP matematico
|   +-- lean/                     # Verificacion Lean 4
|   |   +-- client.py             # Cliente Lean 4 (UTF-8, timeout)
|   |   +-- solver_cascade.py     # rfl -> simp -> ring -> omega -> aesop
|   |   +-- sorry_analyzer.py     # Analisis de sorry en pruebas
|   +-- llm/                      # Cliente LLM multi-proveedor
|   |   +-- client.py             # Anthropic / Google / Groq / Demo
|   +-- pillars/                  # Fundamentos matematicos formales
|   |   +-- zfc.py                # Axiomas ZFC (8 skills L0)
|   |   +-- category_theory.py    # Teoria de categorias (8 skills L0)
|   |   +-- logic.py              # FOL + logica intuicionista (7 skills L0)
|   |   +-- type_theory.py        # Teoria de tipos Curry-Howard (8 skills L0)
|   +-- eval/                     # Evaluacion de respuestas
|       +-- math_evaluator.py     # Extraccion \boxed{}, tolerancia numerica, sympy
|
+-- MetamathProver/               # Pruebas Lean 4 verificadas (8 archivos)
|
+-- scripts/                      # Utilidades de datos y entrenamiento
|   +-- seed_from_datasets.py     # Conecta ProofNet/miniF2F/NuminaMath al NLE
|   +-- evaluate_benchmark.py     # Benchmark NLE-especifico (MATH/GSM8K)
|   +-- prepare_training_data.py  # Prepara splits de entrenamiento
|   +-- train_gnn_ppo.py          # Entrena GNN+PPO en dos fases
|   +-- balance_datasets.py       # Balancea 2.29M ejemplos en 14 categorias (NUEVO)
|   +-- train_multiagent.py       # Entrena los 14 agentes especializados (NUEVO)
|
+-- data/                         # Datos generados
|   +-- lean_examples.json        # 157 ejemplos few-shot miniF2F
|   +-- agents/                   # Pesos por categoria (14 archivos .pt)
|
+-- tests/                        # 379 tests en 17 suites
+-- experiments/                  # Experimentos y cuadernos
+-- docs/                         # Paper NLE v7.0
```

---

## Datasets

El sistema integra **2.29M ejemplos matemáticos** balanceados en 14 categorías:

| Dataset | Ejemplos | Uso |
|---|---|---|
| **NuminaMath** | 859,494 | Problemas de olimpiadas y competencias |
| **MetaMathQA** | 395,000 | QA matemático aumentado |
| **Autoformalization** | 327,000 | Pares lenguaje natural ↔ Lean |
| **OrcaMath** | 200,000 | Razonamiento paso a paso |
| **OpenR1Math** | 93,000 | Razonamiento con cadenas de pensamiento |
| **LeanWorkbook+Proofs** | 54,000 | Enunciados formalizados en Lean 4 |
| **HendrycksMath** | 12,500 | MATH de 5 dificultades |
| **BigBench Formal Fallacies** | 14,200 | Lógica formal |
| **OmniMath** | 4,400 | Olimpiadas internacionales |
| **ProofNet** | 371 | Pruebas formales verificadas |
| **GSM8K + MATH + ProofNet** | ~21,000 | Benchmark de referencia |

**Total: ~1.98M train · ~248K val · ~65K test** (splits 80/10/10 con upsampling por categoría)

### Balancear y preparar datasets

```bash
# Dry-run (solo estadisticas, sin escribir)
python scripts/balance_datasets.py --dry-run

# Balancear y escribir splits en data/balanced/
python scripts/balance_datasets.py --out data/balanced --target 5000
```

---

## Sistema Multi-Agente

### Entrenar los 14 agentes especializados

```bash
# Entrenar todas las categorias (supervisado)
python scripts/train_multiagent.py --epochs 5

# Solo algebra y logica
python scripts/train_multiagent.py --categories algebra logic --epochs 10

# Fase 2: PPO con recompensas reales de Lean (requiere Lean 4 + Mathlib)
python scripts/train_multiagent.py --with-lean --ppo-epochs 3

# Dry-run (verificar que los datos existen sin entrenar)
python scripts/train_multiagent.py --dry-run
```

### Usar el orquestador en codigo

```python
from nucleo.multi_agent import MultiAgentOrchestrator

orch = MultiAgentOrchestrator()

# Clasificar y enrutar
category, agent = orch.route("prove that sqrt(2) is irrational")
# category = "number-theory"

# Ver estadisticas de los 14 agentes
orch.print_stats()

# Guardar todos los pesos
orch.save_all()
```

### Construir la jerarquia completa de colimites

```python
from nucleo.multi_agent import ColimitAgentSystem, PillarAgentSystem

# Requiere graph, pattern_manager, colimit_builder del NLE
system = ColimitAgentSystem(graph, pattern_manager, colimit_builder)
system.build()          # L1: 4 pilares + L2: 14 categorias + L3: orquestador
system.print_hierarchy()  # visualiza la estructura de colimites
```

---

## Co-Reguladores

4 co-reguladores activos que coordinan el procesamiento:

| Co-regulador | Rol |
|---|---|
| **TACTICAL (CR_tac)** | Clasifica consultas y enruta al pipeline correcto (80% del trafico) |
| **ORGANIZATIONAL (CR_org)** | Organiza secuencias de tacticas |
| **STRATEGIC (CR_str)** | Decide estrategia de alto nivel (20% del trafico) |
| **INTEGRATIVE (CR_int)** | Integra resultados parciales |

---

## GNN + PPO

Red neuronal para selección adaptativa de skills:

```
SkillGNN:
  node_proj    ->  feat_dim x 64
  GATConv 1   ->  64 x 256 x 4 heads   ~ 66,560 params
  GATConv 2   ->  256 x 256 x 4 heads  ~262,144 params
  GATConv 3   ->  256 x 256 x 4 heads  ~262,144 params
  out_proj    ->  256 x 128             ~ 32,896 params

ActorCriticNetwork:
  shared_net  ->  384 x 256 x 128      ~148,736 params
  actor       ->  128 x 3 acciones     ~    387 params
  critic      ->  128 x 1              ~    129 params

Total: 546,820 parametros entrenables  |  2.2 MB
```

**Resultados de entrenamiento** (Fase 2 PPO con Lean real):

| Epoca | Loss | Avg Reward | Assist% |
|---|---|---|---|
| 1 | 0.0746 | 0.573 | 100% |
| 3 | 0.0163 | 0.562 | 100% |
| 5 | 0.0172 | **0.578** | 100% |

**Aprendizaje vivo**: cada interacción alimenta PPO via `Transition`. La memoria procedimental guarda patrones exitosos para reutilizarlos sin red neuronal. Pesos guardados automáticamente cada 10 interacciones.

---

## Entrenamiento del GNN+PPO global

```bash
# Preparar splits (MATH + GSM8K + NuminaMath + ProofNet)
python scripts/prepare_training_data.py

# Fase 1: supervisado (~20 min en RTX 3050)
python scripts/train_gnn_ppo.py --epochs 10 --batch-size 256

# Fase 2: PPO con Lean real (requiere Lean 4 + Mathlib)
python scripts/train_gnn_ppo.py --resume --with-lean --lean-samples 300 --epochs 0 --ppo-epochs 5
```

---

## Memory Evolutive Systems

Implementación de la teoría de Ehresmann para modelar el aprendizaje matemático:

- **Patrón P: I → K** — colección de skills relevantes para una consulta
- **Colímite cP** — skill emergente que sintetiza el patrón (propiedad universal verificada)
- **Complexificación K'** — el grafo evoluciona añadiendo cP y los co-conos

Axiomas formalmente verificados: jerarquía, multiplicidad, conectividad, cobertura de pilares.

La memoria procedimental almacena 2371 patrones sembrados desde ProofNet y NuminaMath, y crece con cada interacción exitosa. Cuando 2+ agentes convergen en la misma consulta, el MES Bridge crea automáticamente un skill emergente.

---

## Grafo de Skills

**76 skills** en jerarquía de 3 niveles + 31 skills de pilares L0:

| Nivel | Descripción | Skills |
|---|---|---|
| L0 | Skills atómicos de pilares: ZFC(8), CatThy(8), Logic(7), TypeThy(8) | 31 |
| L1 | Dominios: algebra, geometría, análisis, topología, lógica, números, combinatoria, probabilidad, categorías, computación, optimización, tácticas Lean | 60 |
| L2 | Estrategias de prueba | 6 |

Morfismos: **dependencia**, **analogía**, **traducción**, **pilar→categoría**.

---

## Aplicación Web

```bash
# Instalar dependencias
pip install -r requirements.txt

# Lanzar (Windows: incluir PYTHONIOENCODING para simbolos Unicode)
PYTHONIOENCODING=utf-8 streamlit run app.py
```

Abre en el navegador: `http://localhost:8501`

### Proveedores LLM soportados

| Proveedor | Modelos | Costo |
|---|---|---|
| **Google AI Studio** | Gemini 2.0 Flash, 1.5 Pro | Gratis (tier) |
| **Groq** | Llama 3.3 70B, Mixtral 8x7B | Gratis |
| **Anthropic** | Claude Haiku, Sonnet | De pago |
| **Demo** | Respuesta local | Sin API key |

---

## Tests

```bash
python -m pytest tests/ -o "addopts=" -v
```

379 tests en 17 suites: colímites, evolución, emergencia, multiplicidad, co-reguladores, GNN, PPO, Lean, memoria, aprendizaje vivo, CLI, multi-agente.

---

## Instalación

```bash
git clone https://github.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean.git
cd Metamatematico---Razonamiento-Formal-con-Lean

# Entorno recomendado
conda create -n metamat python=3.10
conda activate metamat

pip install -r requirements.txt

# Lanzar
PYTHONIOENCODING=utf-8 streamlit run app.py
```

### Dependencias principales

```
streamlit>=1.40
networkx>=3.0
numpy>=1.24
scikit-learn>=1.3
matplotlib>=3.7
torch>=2.0
torch-geometric>=2.4
anthropic / google-genai / groq  (segun proveedor elegido)
```

---

## Fundamento Teórico

El NLE v7.0 está basado en el artículo **"Núcleo Lógico Evolutivo v7.0 — Memory Evolutive Systems y Razonamiento Formal"** (Jiménez Martínez, BIOMAT 2025), disponible en `docs/`.

El sistema modela el proceso cognitivo de un matemático experto siguiendo la teoría de **Memory Evolutive Systems** de A. Ehresmann: la memoria matemática se organiza como una categoría que evoluciona mediante complexificaciones sucesivas, donde cada nueva competencia emerge como colímite de competencias previas.

La arquitectura multi-agente extiende este marco: cada agente especializado **es** el nodo colímite en el grafo, no un proceso externo. La jerarquía L0→L1→L2→L3 refleja la estructura matemática de los pilares fundacionales (ZFC, teoría de categorías, lógica, teoría de tipos) que fundamentan las 14 áreas matemáticas.

---

**Leonardo Jiménez Martínez · BIOMAT · Centro de Biomatemáticas · 2025**
