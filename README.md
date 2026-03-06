# METAMATEMÁTICO — Razonamiento Formal con Lean 4

[![Lean 4](https://img.shields.io/badge/Lean-4-blue.svg)](https://lean-lang.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://python.org/)
[![Tests](https://img.shields.io/badge/Tests-379_passing-brightgreen.svg)](#tests)
[![Skills](https://img.shields.io/badge/Skills-76-blueviolet.svg)](#grafo-de-skills)
[![GNN+PPO](https://img.shields.io/badge/GNN%2BPPO-124K_params-red.svg)](#gnn--ppo)
[![Streamlit](https://img.shields.io/badge/App-Streamlit-ff4b4b.svg)](#aplicacion-web)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**BIOMAT · Centro de Biomatemáticas · UNAM**

Asistente de razonamiento matemático formal basado en el **Núcleo Lógico Evolutivo (NLE v7.0)**: un sistema que integra Memory Evolutive Systems, teoría de categorías, verificación en Lean 4 y aprendizaje por refuerzo en un único marco coherente.

---

## Aplicación Web

Interfaz de chat clásica construida con Streamlit:

- **Input fijo al fondo** — el área de escritura siempre visible
- **Historial persistente** — la conversación se conserva al navegar a las visualizaciones y regresar
- **Visualizaciones conectadas** — grafos de embeddings, complexificación MES y traza de prueba reflejan datos reales del Núcleo, no maquetas

### Ejecutar localmente

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Lanzar la app
streamlit run app.py
```

Abre en el navegador: `http://localhost:8501`

### Proveedores soportados

| Proveedor | Modelos | Costo |
|---|---|---|
| **Google AI Studio** | Gemini 2.0 Flash, 1.5 Pro | Gratis (tier) |
| **Groq** | Llama 3.3 70B, Mixtral 8x7B | Gratis |
| **Anthropic** | Claude Haiku, Sonnet | De pago |
| **Demo** | Respuesta local | Sin API key |

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│              NUCLEO LOGICO EVOLUTIVO (NLE v7.0)             │
│                  Σ_t = (L, CR_t, G_t, F)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Usuario → CR_tac → [RESPONDER | ASISTIR]                  │
│                           │                                 │
│              ┌────────────┴────────────┐                    │
│              │                         │                    │
│         GoalAnalyzer            Grafo de Skills             │
│         (orden tácticas)        (76 skills, 14 cats)        │
│              │                         │                    │
│              └────────────┬────────────┘                    │
│                           │                                 │
│                    LLM (contexto enriquecido)               │
│                           │                                 │
│                    Lean 4 SolverCascade                     │
│              rfl → simp → ring → omega → aesop              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Memory Evolutive Systems (Ehresmann)               │   │
│  │  Patrones P → Colímites cP → Complexificación K'   │   │
│  │  Axiomas 8.1–8.4 · Teoremas 8.5–8.7               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  GNN + PPO (124K params)                            │   │
│  │  SkillGNN (3x GATConv) + ActorCriticNetwork        │   │
│  │  Aprendizaje vivo: cada interacción alimenta PPO   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Subsistemas (`nucleo/`)

| Módulo | Descripción |
|---|---|
| `core.py` | Orquestador principal `Nucleo` |
| `graph/` | `SkillCategory` (NetworkX), embeddings, evolución |
| `mes/` | Patrones, colímites, co-reguladores, memoria |
| `rl/` | GNN (`SkillGNN`), PPO (`NucleoAgent`), recompensas |
| `lean/` | Cliente Lean 4, solver cascade, sorry analyzer |
| `llm/` | Cliente LLM multi-proveedor |
| `pillars/` | ZFC, categorías, lógica, teoría de tipos |
| `eval/` | Evaluador de respuestas matemáticas |

---

## Grafo de Skills

**76 skills** organizados en una jerarquía de 3 niveles y 14 categorías matemáticas:

| Nivel | Descripción | Skills |
|---|---|---|
| L0 | Fundamentos (ZFC, categorías, FOL, tipos, Lean) | 10 |
| L1 | Dominios: álgebra, geometría, análisis, topología, lógica, números, combinatoria, probabilidad, categorías avanzadas, computación, optimización, tácticas Lean | 60 |
| L2 | Estrategias de prueba | 6 |

Morfismos entre skills: **dependencia**, **analogía**, **traducción**.

---

## Memory Evolutive Systems

Implementación de la teoría de Ehresmann para modelar el aprendizaje matemático:

- **Patrón P: I → K** — colección de skills relevantes para una consulta
- **Colímite cP** — skill emergente que sintetiza el patrón (propiedad universal verificada)
- **Complexificación K'** — el grafo evoluciona añadiendo cP y los co-conos

Axiomas formalmente verificados: jerarquía de skills, multiplicidad, conectividad, cobertura de pilares.

---

## GNN + PPO

Red neuronal para selección adaptativa de skills:

```
SkillGNN:
  node_proj    →  feat_dim × 64
  GATConv 1   →  64 × 64 × 4 heads     ≈ 16,640 params
  GATConv 2   →  64 × 64 × 4 heads     ≈ 16,640 params
  GATConv 3   →  64 × 64 × 4 heads     ≈ 16,640 params
  out_proj    →  128 × 64              ≈  8,192 params

ActorCriticNetwork:
  shared_net  →  256 × 128 × 2        ≈ 33,024 params
  actor       →  128 × num_skills     ≈  9,728 params
  critic      →  128 × 1             ≈    129 params

Total: ~124,420 parámetros entrenables
```

**Aprendizaje vivo**: cada interacción con el chat alimenta el agente PPO via `Transition`. La memoria procedimental guarda los patrones exitosos para reutilizarlos sin necesidad de la red neuronal.

---

## Visualizaciones

La página de visualizaciones muestra datos reales del Núcleo (no maquetas):

| Pestaña | Contenido |
|---|---|
| Grafo de Skills | Red categórica completa — nodos resaltados según la consulta activa |
| Espacio de Embeddings | Proyección t-SNE / PCA de los vectores reales (320 dim) |
| Arquitectura NLE | Diagrama de bloques del sistema completo |
| Complexificación MES | Patrón P → colímite cP → K' con skills reales de la consulta |
| Pipeline | Flujo de procesamiento de consulta a respuesta |
| GNN + Estadísticas | Arquitectura de la red neuronal |
| Traza de Prueba | Subred de skills activada para un teorema concreto |

---

## Tests

```bash
python -m pytest tests/ -o "addopts=" -v
```

379 tests en 17 suites — colímites, evolución, emergencia, multiplicidad, co-reguladores, GNN, PPO, Lean, memoria, aprendizaje vivo, CLI.

---

## Estructura del Proyecto

```
metamath-prover/
├── app.py                    # App Streamlit (chat + navegación)
├── pages/
│   └── 1_Visualizaciones.py  # Grafos, embeddings, MES, traza
├── nucleo/                   # Núcleo Lógico Evolutivo (~12,800 LOC)
│   ├── core.py               # Orquestador principal
│   ├── graph/                # Grafo categórico de skills
│   ├── mes/                  # Memory Evolutive Systems
│   ├── rl/                   # GNN + PPO
│   ├── lean/                 # Verificación Lean 4
│   ├── llm/                  # Cliente LLM
│   └── pillars/              # Fundamentos matemáticos
├── MetamathProver/           # Pruebas Lean 4 verificadas
├── tests/                    # 379 tests
├── experiments/              # Experimentos y benchmarks
└── docs/                     # Papers NLE v7.0
```

---

## Instalación

```bash
git clone https://github.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean.git
cd Metamatematico---Razonamiento-Formal-con-Lean

# Entorno recomendado: conda
conda create -n metamat python=3.10
conda activate metamat

pip install -r requirements.txt

# Lanzar la app
streamlit run app.py
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
anthropic / google-genai / groq  (según proveedor elegido)
```

---

## Fundamento Teórico

El NLE v7.0 está basado en el artículo **"Núcleo Lógico Evolutivo v7.0 — Memory Evolutive Systems y Razonamiento Formal"** (Jiménez Martínez, BIOMAT 2025), disponible en `docs/`.

El sistema modela el proceso cognitivo de un matemático experto siguiendo la teoría de **Memory Evolutive Systems** de A. Ehresmann: la memoria matemática se organiza como una categoría que evoluciona mediante complexificaciones sucesivas, donde cada nueva competencia emerge como colímite de competencias previas.

---

**BIOMAT · Centro de Biomatemáticas · UNAM · 2025**
