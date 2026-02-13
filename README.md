# Metamath Prover

[![Lean 4](https://img.shields.io/badge/Lean-4-blue.svg)](https://lean-lang.org/)
[![Mathlib](https://img.shields.io/badge/Mathlib-4-orange.svg)](https://github.com/leanprover-community/mathlib4)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://python.org/)
[![Tests](https://img.shields.io/badge/Tests-379_passing-brightgreen.svg)](#tests)
[![Skills](https://img.shields.io/badge/Skills-76-blueviolet.svg)](#conceptos-fundamentales)
[![GNN+PPO](https://img.shields.io/badge/GNN%2BPPO-124K_params-red.svg)](#7-red-neuronal-gnn--ppo)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Descripcion General

Este proyecto tiene dos componentes principales:

1. **MetamathProver/** — Pruebas verificadas por maquina en Lean 4 (grupos, anillos)
2. **nucleo/** — Sistema adaptativo de razonamiento matematico (NLE v7.0, ~12,800 LOC Python)

El objetivo es construir una **IA matematica** capaz de:
- Comprender consultas matematicas en lenguaje natural
- Generar pruebas formales en Lean 4
- Aprender y mejorar mediante interaccion via Memory Evolutive Systems

El NLE v7.0 recibe consultas en lenguaje natural, las clasifica mediante un co-regulador tactico (CR_tac) que consulta un grafo categorico de 76 skills organizados en 4 pilares (Conjuntos, Categorias, Logica, Tipos), y decide si responder con explicacion o asistir con prueba formal en Lean 4. Cuando asiste, un GoalAnalyzer analiza la estructura del goal para reordenar un cascade de 9 tacticas automaticas (rfl, simp, ring, omega, etc.) priorizando las mas relevantes segun patrones regex y las conexiones del grafo (por ejemplo, un goal algebraico va directo a `ring`), mientras el LLM (Claude) recibe contexto extraido del grafo — skills relevantes, prerequisitos, tacticas sugeridas y pilar dominante — en vez de datos aleatorios. Todo esto se retroalimenta: cada interaccion alimenta una red neuronal GNN+PPO (124K parametros) que aprende a seleccionar mejores skills, y una memoria procedural que guarda patrones exitosos (query, tactica, goal) para reutilizarlos sin necesidad de la red neuronal, formando un ciclo evolutivo modelado segun los Memory Evolutive Systems de Ehresmann donde el grafo crece por complexificacion (patrones → colimites → emergencia de nuevos niveles) manteniendo axiomas formales verificados (jerarquia, multiplicidad, conectividad, cobertura).

---

## Arquitectura

```
┌──────────────────────────────────────────────────────────────────────┐
│                     NUCLEO LOGICO EVOLUTIVO (NLE v7.0)               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────────────┐  │
│  │   Usuario    │───>│     LLM      │───>│      Lean 4           │  │
│  │  (consulta)  │    │   (Claude)   │    │  (solver cascade +    │  │
│  └──────────────┘    └──────────────┘    │   GoalAnalyzer +      │  │
│         │                   │            │   sorry analyzer)     │  │
│         v                   v                      │                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              GRAFO CATEGORICO DE SKILLS (76 skills)          │   │
│  │                                                              │   │
│  │   Nivel 3: o Competencias (verificacion Lean)               │   │
│  │             |                                                │   │
│  │   Nivel 2: o---o Habilidades + Estrategias de prueba (6)    │   │
│  │             |   |                                            │   │
│  │   Nivel 1: o---o---o Clusters + Tacticas Lean (9)           │   │
│  │             |   |   |                                        │   │
│  │   Nivel 0: o---o---o---o Atomos (axiomas basicos)           │   │
│  │                                                              │   │
│  │   4 Pilares: SET | CAT | LOG | TYPE                         │   │
│  │                                                              │   │
│  │   Integracion activa:                                       │   │
│  │   - GoalAnalyzer: goal → regex + grafo → orden de tacticas  │   │
│  │   - CR_tac: query → keywords + grafo → ASSIST/RESPONSE     │   │
│  │   - Contexto: query → skills → deps + tacticas → LLM       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│         │                                                           │
│         v                                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │          GNN + PPO  (124,420 parametros entrenables)         │   │
│  │                                                              │   │
│  │  SkillGNN (3x GATConv) ──> Actor-Critic ──> PPO + GAE      │   │
│  │  Embeddings por nodo       Politica          Aprendizaje     │   │
│  │                                              en vivo         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│         │                                                           │
│         v                                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              RED DE CO-REGULADORES (MES)                     │   │
│  │                                                              │   │
│  │  CR_tac ──> CR_org ──> CR_str ──> CR_int                   │   │
│  │  (graph-aware) (medio) (lento)    (integridad)              │   │
│  │                                                              │   │
│  │  Memoria: Empirica -> Procedural -> Semantica -> E-conceptos│   │
│  │           (con query_text, tactic_used, lean_goal)           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Propiedades Formales Verificadas:                                   │
│  Axiomas 8.1-8.4 (Jerarquia, Multiplicidad, Conectividad, Cobertura)│
│  Teoremas 8.5-8.7 (Consistencia, Emergencia, Preservacion)          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Estructura del Repositorio

```
metamath-prover/
│
├── MetamathProver/              # Pruebas Lean 4 verificadas
│   ├── Group/                   #   Teoria de grupos
│   └── Ring/                    #   Teoria de anillos
│
├── nucleo/                      # Sistema NLE v7.0 (~12,800 LOC)
│   ├── core.py                  #   Orquestador principal (Nucleo + contexto de grafo)
│   ├── cli.py                   #   CLI + chat interactivo con Claude
│   ├── __main__.py              #   Punto de entrada: python -m nucleo
│   ├── types.py                 #   Tipos: Skill, Morphism, Pattern, Colimit, Option
│   ├── config.py                #   Configuracion e hiperparametros
│   │
│   ├── graph/                   #   Categoria de Skills
│   │   ├── category.py          #     Grafo jerarquico + axiomas formales (8.1-8.4)
│   │   ├── evolution.py         #     Sistema evolutivo + teoremas (8.5-8.7)
│   │   ├── operations.py        #     Operaciones de grafo
│   │   └── embeddings.py        #     Embeddings de skills
│   │
│   ├── mes/                     #   Memory Evolutive Systems
│   │   ├── co_regulators.py     #     4 co-reguladores (tac graph-aware/org/str/int)
│   │   ├── memory.py            #     Memoria: E-equivalencia, E-conceptos
│   │   └── patterns.py          #     Patrones, colimites, multiplicidad
│   │
│   ├── lean/                    #   Integracion Lean 4
│   │   ├── client.py            #     Cliente Lean 4 (check/eval)
│   │   ├── solver_cascade.py    #     Cascade APOLLO + GoalAnalyzer (graph-aware)
│   │   ├── sorry_analyzer.py    #     Analisis estatico de sorries
│   │   ├── sorry_filler.py      #     Generacion de pruebas (cascade + LLM)
│   │   ├── parser.py            #     Parser de errores estructurados
│   │   ├── tactics.py           #     Mapeo de tacticas
│   │   └── tactics_db.py        #     Base de datos de tacticas Lean 4
│   │
│   ├── rl/                      #   Aprendizaje por Refuerzo + GNN+PPO
│   │   ├── agent.py             #     Agente RL + PPO con memoria procedural
│   │   ├── gnn.py               #     SkillGNN (3x GATConv, 4 cabezas de atencion)
│   │   ├── networks.py          #     Actor-Critic (124,420 parametros)
│   │   ├── mdp.py               #     Proceso de decision de Markov
│   │   └── rewards.py           #     Funcion de recompensa (6 componentes)
│   │
│   ├── pillars/                 #   4 Pilares + 66 dominios matematicos
│   │   ├── set_theory.py        #     ZFC (Teoria de Conjuntos)
│   │   ├── category_theory.py   #     CAT (Teoria de Categorias)
│   │   ├── logic.py             #     LOG (FOL + Logica Intuicionista)
│   │   ├── type_theory.py       #     TYPE (CIC / Lean 4)
│   │   └── math_domains.py      #     66 dominios (algebra, tacticas Lean, estrategias, ...)
│   │
│   ├── llm/                     #   Integracion LLM
│   │   ├── client.py            #     Cliente Claude API
│   │   └── prompts.py           #     Templates de prompts
│   │
│   └── eval/                    #   Evaluacion
│       └── math_evaluator.py    #     Verificacion de respuestas
│
├── tests/                       #   379 tests (17 suites)
│   ├── test_graph.py            #     Categoria de skills
│   ├── test_evolution.py        #     Sistema evolutivo
│   ├── test_colimits.py         #     Patrones y colimites
│   ├── test_emergence.py        #     Links simples/complejos, emergencia
│   ├── test_multiplicity.py     #     Homologia, principio de multiplicidad
│   ├── test_coregulators.py     #     Red de co-reguladores
│   ├── test_memory.py           #     Memoria MES, E-conceptos
│   ├── test_lean_integration.py #     Solver cascade, sorry analyzer, parser
│   ├── test_formal_properties.py#     Axiomas 8.1-8.4, Teoremas 8.5-8.7
│   ├── test_math_domains.py     #     66 dominios matematicos, cadenas de deps
│   ├── test_gnn.py              #     Codificador GNN (19 tests)
│   ├── test_ppo.py              #     PPO + Actor-Critic (25 tests)
│   ├── test_live_learning.py    #     Aprendizaje en vivo (24 tests)
│   ├── test_pillars.py          #     4 pilares fundacionales
│   ├── test_hierarchy_integration.py #  GoalAnalyzer, contexto de grafo, CR_tac
│   ├── test_cli.py              #     CLI + chat interactivo
│   └── test_types.py            #     Tipos basicos
│
├── docs/                        #   Documentacion
│   ├── NLE_v7_MES_Ehresmann.pdf #     Fundamentos MES (Ehresmann)
│   ├── NLE_v7_Unificado_MES.pdf #     Documento unificado MES
│   ├── MEJORAS_RECIENTES.pdf    #     Mejoras recientes
│   └── Integracion_Jerarquia_Razonamiento.pdf  # Integracion jerarquia-razonamiento
│
├── examples/                    #   Ejemplos de uso
│   ├── basic_usage.py
│   ├── complete_flow.py
│   ├── demo_external_skills.py
│   └── lean_integration.py
│
├── scripts/                     #   Utilidades
│   ├── visualize_embeddings.py  #     Visualizacion t-SNE de embeddings GNN
│   └── generate_hierarchy_pdf.py#     Generador de PDF de integracion jerarquica
├── PLAN.md                      #   Plan de implementacion (fases 0-7)
└── IMPLEMENTATION_PLAN.md       #   Plan detallado original
```

---

## Conceptos Fundamentales

### 1. Categoria Jerarquica de Skills

Los skills (unidades de conocimiento) se organizan en una jerarquia categorica:

| Nivel | Nombre | Ejemplo |
|-------|--------|---------|
| 0 | Atomos | Axioma de extensionalidad, modus ponens |
| 1 | Clusters | ZFC-axiomas, FOL-reglas, Type-reglas |
| 2 | Habilidades | Induccion matematica, Curry-Howard |
| 3 | Competencias | Verificacion Lean, Forcing |
| 4+ | Meta-skills | Traducciones inter-pilar |

Cuatro **pilares** fundacionales organizan el conocimiento: SET (ZFC), CAT (Teoria de Categorias), LOG (FOL + LI), TYPE (CIC/Lean 4). El sistema incluye **76 skills matematicos**: 10 fundacionales (nivel 0) + 66 de dominio (niveles 1-2) en 14 categorias.

#### Skills de Dominio (66 skills, 14 categorias)

| Categoria | Skills | Nivel 1 | Nivel 2 |
|-----------|--------|---------|---------|
| Algebra | 7 | group-theory, ring-theory, field-theory, linear-algebra, module-theory | commutative-algebra, homological-algebra |
| Geometria | 6 | euclidean-geometry, differential-geometry, projective-geometry | algebraic-geometry, riemannian-geometry, symplectic-geometry |
| Analisis | 6 | real-analysis, complex-analysis, measure-theory | functional-analysis, harmonic-analysis, pde-theory |
| Topologia | 5 | point-set-topology, algebraic-topology | differential-topology, homotopy-theory, knot-theory |
| Logica | 3 | model-theory | proof-theory, homotopy-type-theory |
| Teoria de Numeros | 4 | elementary-number-theory, algebraic-number-theory | analytic-number-theory, arithmetic-geometry |
| Combinatoria | 6 | enumerative-combinatorics, graph-theory, matroid-theory | extremal-combinatorics, additive-combinatorics, combinatorial-optimization |
| Probabilidad | 4 | probability-theory, stochastic-processes | ergodic-theory, stochastic-calculus |
| Teoria de Conjuntos | 1 | descriptive-set-theory | |
| Teoria de Categorias | 2 | topos-theory | homological-algebra-cat |
| Computacion | 4 | algorithm-analysis, formal-languages | computational-complexity, type-theory-advanced |
| Optimizacion | 3 | convex-optimization | variational-methods, optimal-control |
| **Tacticas Lean** | **9** | simp, rewrite, exact, apply, induction, omega, ring, aesop, calc | |
| **Estrategias de Prueba** | **6** | | backward, forward, contradiction, cases, inductive, construction |

```python
from nucleo.graph.category import SkillCategory
from nucleo.types import Skill, PillarType, MorphismType

cat = SkillCategory("MathKnowledge")

# Agregar skills en diferentes niveles
cat.add_skill(Skill(id="zfc", name="ZFC", pillar=PillarType.SET, level=0))
cat.add_skill(Skill(id="group-theory", name="Group Theory", pillar=PillarType.SET, level=1))
cat.add_morphism("zfc", "group-theory", MorphismType.DEPENDENCY)

# Verificar axiomas formales (8.1-8.4)
result = cat.verify_all_axioms()
print(result["all_satisfied"])  # True si jerarquia + multiplicidad + conectividad + cobertura
```

### 2. Red de Co-Reguladores

Cuatro co-reguladores operan a diferentes escalas temporales:

| Co-Regulador | Nivel | Frecuencia | Funcion |
|--------------|-------|------------|---------|
| **CR_tac** (Tactico) | 0-1 | Cada paso | Seleccionar tacticas, responder |
| **CR_org** (Organizativo) | 1-2 | Cada 10 pasos | Reorganizar grafo, crear puentes |
| **CR_str** (Estrategico) | 2-3 | Cada 100 pasos | Crear colimites, nuevos niveles |
| **CR_int** (Integridad) | Todos | Periodico | Verificar axiomas, reparar |

```python
from nucleo.mes.co_regulators import CoRegulatorNetwork

network = CoRegulatorNetwork(cr_org_frequency=10, cr_str_frequency=100)
results = network.step(cat)
for cr_type, action, option in results:
    print(f"{cr_type.name}: {action.name}")
```

### 3. Patrones y Colimites

Un **patron** es un grupo de skills que trabajan juntos. Su **colimite** es un nuevo skill que los integra (emergencia):

```python
from nucleo.mes.patterns import PatternManager, ColimitBuilder

pm = PatternManager()
pattern = pm.create_pattern(
    component_ids=["skill_1", "skill_2", "skill_3"],
    distinguished_links=["morph_1_2", "morph_2_3"],
    graph=cat,
)

cb = ColimitBuilder(pm)
new_skill, colimit = cb.build_colimit(pattern, cat)
# new_skill esta en max(niveles_componentes) + 1
# El colimite satisface la propiedad universal
```

### 4. Evolucion y Propiedades Formales

El sistema evoluciona mediante **complexificacion** (Opciones con absorciones, eliminaciones, ligaduras):

```python
from nucleo.graph.evolution import EvolutionarySystem
from nucleo.types import Option, Skill

evo = EvolutionarySystem(cat)

# Aplicar paso de evolucion
option = Option(absorptions=[
    Skill(id="topology", name="Topology", pillar=PillarType.SET, level=1)
])
functor = evo.apply_option(option)

# Verificar que los teoremas se mantienen despues de la evolucion
result = evo.verify_all_theorems()
assert result["8.5_consistency"]["satisfies"]   # Axiomas preservados
assert result["8.6_emergence"]["satisfies"]     # Complejidad crece
assert result["8.7_coverage_preservation"]["satisfies"]  # Cobertura mantenida
```

### 5. Integracion Lean 4 (Solver Cascade + GoalAnalyzer)

Cascade de solvers inspirado en APOLLO que prueba 9 tacticas automaticas antes de recurrir al LLM.
**GoalAnalyzer** reordena el cascade segun la estructura del goal y el contexto del grafo:

```
Por defecto: rfl -> simp -> ring -> linarith -> nlinarith -> omega -> exact? -> apply? -> aesop
Inteligente: goal "a * b + c = c + b * a" → ring -> nlinarith -> linarith -> rfl -> simp -> ...
Con grafo:   skill ring-theory → vecinos → tactic-ring, tactic-simp → priorizar ring, simp
```

```python
from nucleo.lean.solver_cascade import SolverCascade, GoalAnalyzer

# Ordenamiento de tacticas consciente del goal
analyzer = GoalAnalyzer()
ordered = analyzer.prioritize("a * b + c = c + b * a")  # ring primero
ordered = analyzer.prioritize("Nat.succ n ≤ n + 1")     # omega primero
ordered = analyzer.prioritize("P ∧ Q → Q ∧ P")          # simp primero

# Con contexto de grafo: skills de dominio → tacticas conectadas
ordered = analyzer.prioritize("ring homomorphism", graph=skill_graph)
# ring-theory → tactic-ring, tactic-simp → ring, simp priorizados

# Cascade inteligente: try_fill_sorry_smart reordena antes de probar
result = await cascade.try_fill_sorry_smart(code, sorry_line, goal_text="a * b = b * a")
```

### 6. Memoria MES

Cuatro tipos de memoria con E-equivalencia y formacion de E-conceptos:

| Tipo | Descripcion | Ejemplo |
|------|-------------|---------|
| **Empirica** | Experiencias concretas | "Use `simp` para resolver x + 0 = x" |
| **Procedural** | Secuencias exitosas | "Para forall, usar `intro` y luego `apply`" |
| **Semantica** | E-conceptos abstractos | "Induccion es util para N" |
| **Consolidada** | Conocimiento reforzado | Skills usados 3+ veces |

### 7. Red Neuronal GNN + PPO

El sistema usa una Red Neuronal de Grafos con Optimizacion de Politica Proximal para seleccion inteligente de skills:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   SkillGNN      │────>│  Actor-Critic    │────>│  PPO + GAE      │
│                 │     │                  │     │                 │
│  3x GATConv     │     │  Actor: π(a|s)   │     │  clip ratio     │
│  4 cab. atencion│     │  Critic: V(s)    │     │  bonus entropia │
│  edge_attr      │     │  124,420 params  │     │  λ-retornos     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

```python
from nucleo.rl.gnn import SkillGNN, graph_to_pyg
from nucleo.rl.networks import ActorCriticNetwork
from nucleo.rl.agent import NucleoAgent

# Crear agente neuronal
agent = NucleoAgent(num_skills=76, use_neural=True)

# El agente selecciona skills usando embeddings GNN + politica PPO
action = agent.select_action(state, query="Demuestra por induccion sobre n")
```

### 8. Aprendizaje en Vivo desde el Chat

Cada interaccion de chat alimenta el ciclo de entrenamiento PPO:

```
Usuario pregunta ──> Claude responde ──> Recompensa calculada ──> PPO update
                                              │
                                              v
                                    Memoria Procedural
                                    (query, tactica, goal)
                                              │
                                              v
                                    Pesos guardados cada 10 pasos
```

El agente consulta patrones probados en la memoria procedural antes de recurrir a la red neuronal, creando un sistema hibrido de decision memoria+neuronal.

```python
from nucleo.core import Nucleo

nucleo = Nucleo()
nucleo.set_neural_agent(agent)  # Habilitar aprendizaje PPO en vivo
# Ahora cada interaccion de chat entrena la red neuronal
```

### 9. Integracion Jerarquia-Razonamiento

El grafo categorico de skills influye activamente en la generacion de pruebas en 3 puntos de integracion:

**A. GoalAnalyzer** (`solver_cascade.py`): Analiza el texto del goal con patrones regex + recorrido del grafo para reordenar el cascade de tacticas. Un goal como `a * b + c = c + b * a` prioriza `ring` en vez de perder tiempo con `rfl`, `simp`.

**B. Contexto Graph-Aware** (`core.py`): Las consultas se comparan contra nombres de skills en el grafo. Para cada coincidencia, se recorren dependencias y skills de tactica/estrategia conectados para construir contexto relevante para el LLM, reemplazando el recorte aleatorio de skill IDs.

**C. CR_tac Graph-Informed** (`co_regulators.py`): El co-regulador tactico ahora tiene una cadena de clasificacion de 3 niveles: agente neuronal → busqueda de keywords → matching de skills en el grafo. Una consulta sobre "ring homomorphism" activa ASSIST porque `ring-theory` se conecta a `tactic-ring` via morfismos TRANSLATION.

```
Consulta: "ring homomorphism"
  → CR_tac: match en grafo → ring-theory → vecino tactic-ring → ASSIST
  → GoalAnalyzer: patron ring → ring, nlinarith, linarith primero
  → Contexto: ring-theory → deps [zfc-axioms] + tacticas [ring, simp] → LLM
```

### 10. Visualizacion del Grafo de Skills

Visualizar embeddings de la GNN con proyeccion t-SNE:

```bash
python scripts/visualize_embeddings.py          # Guardar en data/skill_embeddings.png
python scripts/visualize_embeddings.py --show    # Ventana interactiva
```

Genera 4 paneles: estructura del grafo, embeddings t-SNE por pilar, clusters por categoria y mapa de calor de distancias entre pilares.

---

## Propiedades Formales

El sistema verifica las propiedades formales de la especificacion MES:

### Axiomas (verificados en SkillCategory)

| Axioma | Propiedad | Condicion |
|--------|-----------|-----------|
| 8.1 | Jerarquia | >= 2 niveles jerarquicos |
| 8.2 | Multiplicidad | >= 2 pilares con traducciones inter-pilar |
| 8.3 | Conectividad | Debilmente conexo + conexiones inter-pilar |
| 8.4 | Cobertura | Todo skill alcanzable desde un skill de pilar |

### Teoremas (verificados en EvolutionarySystem)

| Teorema | Propiedad | Condicion |
|---------|-----------|-----------|
| 8.5 | Consistencia | La complexificacion preserva todos los axiomas |
| 8.6 | Emergencia | La complejidad crece o se estabiliza con el tiempo |
| 8.7 | Preservacion de Cobertura | La cobertura se mantiene bajo evolucion |

---

## Pruebas Lean 4 Verificadas

El directorio `MetamathProver/` contiene pruebas verificadas por maquina:

| Teorema | Enunciado | Directorio |
|---------|-----------|------------|
| Primer Isomorfismo (Grupos) | G / ker(f) ~=* im(f) | `Group/` |
| Primer Isomorfismo (Anillos) | R / ker(f) ~=+* im(f) | `Ring/` |
| Kernel es Subgrupo Normal | ker(f) normal en G | `Group/` |
| Kernel es Ideal Bilateral | ker(f) es ideal | `Ring/` |

---

## Instalacion

### Requisitos

```bash
# Python 3.10+
python --version  # Debe ser 3.10 o superior

# Dependencias
pip install pyyaml rich anthropic

# Red neuronal (GNN + PPO)
pip install torch torch-geometric

# (Opcional) Lean 4 para verificacion de pruebas
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh
```

### Clonar y Compilar

```bash
git clone https://github.com/metamatematico/Demostrador-de-enunciados-matem-ticos.git
cd Demostrador-de-enunciados-matem-ticos

# (Opcional) Descargar cache de Mathlib
lake exe cache get
lake build
```

### Verificar Instalacion

```bash
python -c "
from nucleo.graph.category import SkillCategory
from nucleo.graph.evolution import EvolutionarySystem
from nucleo.mes.co_regulators import CoRegulatorNetwork
print('NLE v7.0 instalado correctamente')
"
```

### Chat Interactivo con Claude

```bash
# Configurar la API key de Anthropic
set ANTHROPIC_API_KEY=sk-ant-...          # Windows CMD
$env:ANTHROPIC_API_KEY="sk-ant-..."       # PowerShell
export ANTHROPIC_API_KEY=sk-ant-...       # Linux/Mac

# Iniciar sesion interactiva
python -m nucleo chat

# Con modelo mas rapido/economico
python -m nucleo chat --model claude-haiku-4-5-20251001

# Con informacion de depuracion (acciones RL)
python -m nucleo chat --verbose
```

Comandos dentro del chat: `/help`, `/stats`, `/skills`, `/axioms`, `/clear`, `/quit`

Ejemplo de sesion:
```
┌─── Chat Interactivo ───┐
│ NLE v7.0 — Nucleo Logico Evolutivo      │
│ Modelo: claude-haiku-4-5-20251001       │
└─────────────────────────┘
Listo. 76 skills cargados.

Tu > Que es un grupo en algebra abstracta?
[RESPONSE | confianza: 0.80]
Un **grupo** es una estructura algebraica (G, ·) donde G es un conjunto
con una operacion binaria · que es asociativa, tiene elemento neutro e,
y todo elemento tiene inverso.

Tu > Formaliza eso en Lean 4
[RESPONSE | confianza: 0.80]
class Group (G : Type u) where
  mul : G → G → G
  one : G
  inv : G → G
  mul_assoc : ∀ a b c : G, mul (mul a b) c = mul a (mul b c)
  ...

Tu > /skills
┌──────────────────────────────┐
│ 76 skills en 4 pilares       │
└──────────────────────────────┘

Tu > /quit
Adios!
```

---

## Tests

379 tests en 17 suites de prueba:

```bash
python -m pytest tests/ -v
```

| Suite | Tests | Cobertura |
|-------|-------|-----------|
| test_types | 10 | Tipos, Skill, Morphism, State, Action |
| test_graph | 12 | SkillCategory, axiomas, serializacion |
| test_pillars | 16 | Pilares SET, CAT, LOG, TYPE |
| test_evolution | 10 | Snapshots, funtores de transicion, compatibilidad |
| test_colimits | 26 | Patrones, coconos, propiedad universal, colimites |
| test_emergence | 14 | Clasificacion de links, deteccion de emergencia |
| test_multiplicity | 10 | Homologia, principio de multiplicidad |
| test_coregulators | 19 | 4 co-reguladores, red, recursos compartidos |
| test_memory | 16 | E-equivalencia, E-conceptos, memoria procedural |
| test_lean_integration | 48 | Solver cascade, sorry analyzer, errores estructurados |
| test_formal_properties | 26 | Axiomas 8.1-8.4, Teoremas 8.5-8.7 |
| test_math_domains | 32 | 66 dominios matematicos, cadenas de dependencias |
| test_gnn | 19 | SkillGNN, GATConv, graph_to_pyg, embeddings |
| test_ppo | 25 | Actor-Critic, actualizacion PPO, GAE, encode_query |
| test_live_learning | 24 | Tacticas Lean, estrategias de prueba, memoria, PPO en vivo |
| test_hierarchy_integration | 27 | GoalAnalyzer, contexto de grafo, CR_tac graph-aware |
| test_cli | 10 | Estructura CLI, comando chat, __main__.py |
| **Total** | **379** | |

---

## Estado de Implementacion

| Fase | Descripcion | Estado |
|------|-------------|--------|
| 0 | Correccion de bugs (4 criticos) | Hecho |
| 1 | Colimites (propiedad universal, co-conos) | Hecho |
| 2 | Evolucion (snapshots, funtores de transicion) | Hecho |
| 3 | Emergencia (clasificacion de links, deteccion) | Hecho |
| 4 | Multiplicidad (homologia, multiplicidad de pilares) | Hecho |
| 5 | Co-Reguladores + Memoria (E-equivalencia, core.py) | Hecho |
| 6 | Skills Lean (solver cascade, sorry analyzer) | Hecho |
| 7 | Propiedades formales (axiomas 8.1-8.4, teoremas 8.5-8.7) | Hecho |

### Progreso: ~95%

Las 8 fases completas. Infraestructura GNN+PPO construida (124,420 parametros), aprendizaje en vivo conectado.

### Trabajo Pendiente

- Dataset de entrenamiento (se necesita corpus de problemas matematicos para entrenamiento offline)
- Uso real para acumular patrones de memoria procedural
- Pipeline de evaluacion end-to-end

---

## Referencias

### Lean y Mathlib
- [Documentacion Mathlib4](https://leanprover-community.github.io/mathlib4_docs/)
- [Demostracion de Teoremas en Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)

### Memory Evolutive Systems (MES)
- Ehresmann, A. C., & Vanbremeersch, J. P. (2007). *Memory Evolutive Systems: Hierarchy, Emergence, Cognition*. Elsevier.
- Ehresmann, A. C. (2012). MENS, a mathematical model for cognitive systems. *Journal of Mind Theory*, 0(2).

### Solver Cascade
- Wang et al. (2025). APOLLO: Automated LLM and Lean Collaboration for Mathematical Reasoning. *arXiv:2505.05758*.

### Aprendizaje por Refuerzo y GNN
- Schulman, J. et al. (2017). Proximal Policy Optimization Algorithms. *arXiv:1707.06347*.
- Velickovic, P. et al. (2018). Graph Attention Networks. *ICLR 2018*.
- Fey, M. & Lenssen, J. E. (2019). Fast Graph Representation Learning with PyTorch Geometric. *ICLR Workshop on Representation Learning on Graphs*.

---

## Autor

**Leonardo Jimenez Martinez** — UNAM

---

## Licencia

Licencia MIT. Ver [LICENSE](LICENSE) para detalles.
