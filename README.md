# METAMATEMÁTICO — Razonamiento Formal con Lean 4

[![Lean 4](https://img.shields.io/badge/Lean-4-blue.svg)](https://lean-lang.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://python.org/)
[![Tests](https://img.shields.io/badge/Tests-379_passing-brightgreen.svg)](#tests)
[![Skills](https://img.shields.io/badge/Skills-76-blueviolet.svg)](#grafo-de-skills)
[![GNN+PPO](https://img.shields.io/badge/GNN%2BPPO-546K_params-red.svg)](#gnn--ppo)
[![Streamlit](https://img.shields.io/badge/App-Streamlit-ff4b4b.svg)](#aplicacion-web)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Leonardo Jiménez Martínez · BIOMAT · Centro de Biomatemáticas**

Asistente de razonamiento matemático formal basado en el **Núcleo Lógico Evolutivo (NLE v7.0)**: un sistema que integra Memory Evolutive Systems, teoría de categorías, verificación en Lean 4 y aprendizaje por refuerzo en un único marco coherente.

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
  CR_tac enruta
       |
       v
  LLM formaliza  -->  Lean 4 verifica  -->  LLM traduce  -->  Respuesta
       |                    |
  (formalizador)      (fuente de verdad)
                            |
                   SolverCascade si hay sorry:
                   rfl -> simp -> ring -> omega -> aesop
```

---

## Arquitectura del Sistema

```
+-------------------------------------------------------------+
|              NUCLEO LOGICO EVOLUTIVO (NLE v7.0)             |
|                  Sigma_t = (L, CR_t, G_t, F)               |
+-------------------------------------------------------------+
|                                                             |
|  Usuario --> CR_tac --> [RESPONDER | ASISTIR_LEAN]          |
|                               |                             |
|              +----------------+----------------+            |
|              |                                 |            |
|         _is_mathematical()              Grafo de Skills     |
|         (80+ keywords, LaTeX,           (76 skills,         |
|          simbolos Unicode)               14 categorias)     |
|              |                                 |            |
|         Lean-first pipeline                    |            |
|         1. LLM formaliza                       |            |
|         2. Lean 4 verifica               MES Memory         |
|         3. SolverCascade                 (patrones de       |
|         4. LLM traduce                    exito previos)    |
|                                                             |
|  +-------------------------------------------------------+  |
|  |  Memory Evolutive Systems (Ehresmann)                 |  |
|  |  Patrones P -> Colimites cP -> Complexificacion K'   |  |
|  |  Axiomas 8.1-8.4 . Teoremas 8.5-8.7                 |  |
|  |  2371 patrones sembrados (ProofNet + NuminaMath)     |  |
|  +-------------------------------------------------------+  |
|                                                             |
|  +-------------------------------------------------------+  |
|  |  GNN + PPO (124K params)                              |  |
|  |  SkillGNN (3x GATConv) + ActorCriticNetwork          |  |
|  |  Aprendizaje vivo: cada interaccion alimenta PPO     |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
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
+-- nucleo/                       # Nucleo Logico Evolutivo (~12,800 LOC)
|   +-- core.py                   # Orquestador principal (Lean-first pipeline)
|   +-- config.py                 # Configuracion centralizada
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
|   |   +-- zfc.py                # Axiomas ZFC
|   |   +-- category_theory.py    # Teoria de categorias
|   |   +-- logic.py              # FOL + logica intuicionista
|   |   +-- type_theory.py        # Teoria de tipos
|   +-- eval/                     # Evaluacion de respuestas
|       +-- math_evaluator.py     # Extraccion \boxed{}, tolerancia numerica, sympy
|
+-- MetamathProver/               # Pruebas Lean 4 verificadas (8 archivos)
|
+-- scripts/                      # Utilidades de datos y evaluacion
|   +-- seed_from_datasets.py     # Conecta ProofNet/miniF2F/NuminaMath al NLE
|   +-- evaluate_benchmark.py     # Benchmark NLE-especifico (MATH/GSM8K)
|   +-- prepare_training_data.py  # Prepara splits de entrenamiento (MATH/GSM8K/NuminaMath/ProofNet)
|   +-- train_gnn_ppo.py          # Entrena GNN+PPO en dos fases (supervisado + PPO Lean)
|
+-- data/                         # Datos generados (no versionados excepto ejemplos)
|   +-- lean_examples.json        # 157 ejemplos few-shot miniF2F (versionado)
|
+-- tests/                        # 379 tests en 17 suites
+-- experiments/                  # Experimentos y cuadernos
+-- docs/                         # Paper NLE v7.0
```

---

## Datasets Conectados

El sistema usa cinco conjuntos de datos matematicos para alimentar el NLE:

| Dataset | Uso en el sistema | Cantidad |
|---|---|---|
| **ProofNet** | MES Memory: teoremas formales verificados | 371 registros |
| **miniF2F** | Few-shot Lean: ejemplos inyectados en el prompt de formalizacion | 157 con prueba real |
| **NuminaMath** | MES Memory: problemas con solucion para reconocimiento de patrones | 2000 problemas |
| **MATH** | Benchmark: evaluacion de respuestas (extraccion `\boxed{}`) | referencia |
| **GSM8K** | Benchmark: problemas de razonamiento numerico | referencia |

### Sembrar la memoria del NLE

```bash
# Conecta ProofNet + miniF2F + NuminaMath al sistema
python scripts/seed_from_datasets.py

# Solo proofnet, sin escritura
python scripts/seed_from_datasets.py --skip-numina --dry-run
```

### Ejecutar benchmark

```bash
# Evalua el sistema en MATH o GSM8K
python scripts/evaluate_benchmark.py --dataset math --n 50

# Metricas NLE (independientes del LLM):
#   skill_hit    - consulta matcheo al grafo de skills
#   cr_source    - que co-regulador enruto la consulta
#   lean_verified- Lean verifico la formalizacion
#   memory_hit   - encontro patron previo en MES Memory
```

---

## Metricas del Sistema

El benchmark distingue dos clases de metricas:

**Dependientes del LLM** (calidad de la traduccion):
- Exactitud de respuesta (tolerancia numerica 1e-4, comparacion simbolica sympy)
- Matching de `\boxed{}` vs referencia

**NLE-especificas** (independientes del LLM, miden el razonamiento del nucleo):
- `skill_hit`: el grafo de skills identifico la categoria matematica correcta
- `cr_source`: el co-regulador TACTICAL enruto la consulta apropiadamente
- `lean_verified`: Lean 4 verifico la formalizacion sin sorry
- `memory_hit`: MES Memory recupero un patron de exito previo

---

## Aplicacion Web

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

## Grafo de Skills

**76 skills** en jerarquia de 3 niveles y 14 categorias:

| Nivel | Descripcion | Skills |
|---|---|---|
| L0 | Fundamentos: ZFC, categorias, FOL, tipos, Lean | 10 |
| L1 | Dominios: algebra, geometria, analisis, topologia, logica, numeros, combinatoria, probabilidad, categorias avanzadas, computacion, optimizacion, tacticas Lean | 60 |
| L2 | Estrategias de prueba | 6 |

Morfismos: **dependencia**, **analogia**, **traduccion**.

---

## Memory Evolutive Systems

Implementacion de la teoria de Ehresmann para modelar el aprendizaje matematico:

- **Patron P: I -> K** — coleccion de skills relevantes para una consulta
- **Colimite cP** — skill emergente que sintetiza el patron (propiedad universal verificada)
- **Complexificacion K'** — el grafo evoluciona anadiendo cP y los co-conos

Axiomas formalmente verificados: jerarquia, multiplicidad, conectividad, cobertura de pilares.

La memoria procedimental almacena 2371 patrones sembrados desde ProofNet y NuminaMath, y crece con cada interaccion exitosa.

---

## GNN + PPO

Red neuronal para seleccion adaptativa de skills:

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

**Aprendizaje vivo**: cada interaccion alimenta PPO via `Transition`. La memoria procedimental guarda patrones exitosos para reutilizarlos sin red neuronal. Pesos guardados automaticamente cada 10 interacciones.

---

## Entrenamiento

El GNN+PPO se entrena en dos fases usando los datasets matematicos conectados al sistema.

### Fase 1 — Preentrenamiento supervisado

Ensena al agente a elegir siempre `ASSIST` (pipeline Lean) para cualquier problema matematico.

```bash
# Preparar splits (MATH + GSM8K + NuminaMath + ProofNet -> 71,663 ejemplos)
python scripts/prepare_training_data.py

# Entrenar Fase 1 (GPU: ~20 min en RTX 3050)
python scripts/train_gnn_ppo.py --epochs 10 --batch-size 256
```

**Resultados obtenidos**: `train_acc=100%`, `val_acc=100%`, `test_acc=100%` (convergencia en epoca 1).

### Fase 2 — Ajuste PPO con verificacion Lean real

Refina el modelo usando recompensas diferenciales de `lake env lean + Mathlib`:

| Caso | Reward |
|---|---|
| `\boxed{N}` encontrado + `norm_num` verifica | **+1.0** |
| Problema abstracto (sin respuesta numerica) | **+0.5** |
| Error / timeout de Lean | **+0.3** |
| Elige RESPONSE para problema matematico | **-0.5** |

```bash
# Requiere Lean 4 + Mathlib instalados (lake update)
python scripts/train_gnn_ppo.py --resume --with-lean --lean-samples 300 --epochs 0 --ppo-epochs 5
```

**Resultados obtenidos** (RTX 3050, ~4250s total):

| Epoca | Loss | Avg Reward | Assist% |
|---|---|---|---|
| 1 | 0.0746 | 0.573 | 100% |
| 3 | 0.0163 | 0.562 | 100% |
| 5 | 0.0172 | **0.578** | 100% |

El `avg_reward ≈ 0.57` refleja la distribucion real: ~70% problemas aritmeticos verificables (+1.0) y ~30% pruebas abstractas (+0.5). La discriminacion hace que el PPO aprenda a priorizar ASSIST para matematica computacional y a ser mas cauteloso con pruebas abstractas.

### Mecanismo de discriminacion (`_build_lean_snippet`)

Para cada problema de entrenamiento con solucion `\boxed{N}`:

1. Extrae `N` del campo `solution`
2. Busca en el texto un par `(a, b)` tal que `a + b = N`, `a - b = N` o `a * b = N`
3. Genera `import Mathlib.Tactic.NormNum\ntheorem check : a OP b = N := by norm_num`
4. Ejecuta `lake env lean --json` y mapea el resultado a reward

Problemas sin `\boxed{N}` (ProofNet, algebra abstracta) retornan `0.5` directamente sin llamar a Lean.

### Reanudar entrenamiento

```bash
# Continuar desde el ultimo checkpoint
python scripts/train_gnn_ppo.py --resume --epochs 5

# Solo Fase 2 PPO Lean (sin repetir Fase 1)
python scripts/train_gnn_ppo.py --resume --with-lean --lean-samples 300 --epochs 0 --ppo-epochs 5
```

Los pesos se guardan en `data/neural_agent.json.pt` y se cargan automaticamente por `NucleoAgent` al iniciar la aplicacion.

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

## Tests

```bash
python -m pytest tests/ -o "addopts=" -v
```

379 tests en 17 suites: colimites, evolucion, emergencia, multiplicidad, co-reguladores, GNN, PPO, Lean, memoria, aprendizaje vivo, CLI.

---

## Instalacion

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

## Fundamento Teorico

El NLE v7.0 esta basado en el articulo **"Nucleo Logico Evolutivo v7.0 — Memory Evolutive Systems y Razonamiento Formal"** (Jimenez Martinez, BIOMAT 2025), disponible en `docs/`.

El sistema modela el proceso cognitivo de un matematico experto siguiendo la teoria de **Memory Evolutive Systems** de A. Ehresmann: la memoria matematica se organiza como una categoria que evoluciona mediante complexificaciones sucesivas, donde cada nueva competencia emerge como colimite de competencias previas.

---

**Leonardo Jimenez Martinez · BIOMAT · Centro de Biomatematicas · 2025**
