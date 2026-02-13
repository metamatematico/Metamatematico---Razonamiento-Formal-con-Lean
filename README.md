# Metamath Prover

[![Lean 4](https://img.shields.io/badge/Lean-4-blue.svg)](https://lean-lang.org/)
[![Mathlib](https://img.shields.io/badge/Mathlib-4-orange.svg)](https://github.com/leanprover-community/mathlib4)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://python.org/)
[![Tests](https://img.shields.io/badge/Tests-379_passing-brightgreen.svg)](#tests)
[![Skills](https://img.shields.io/badge/Skills-76-blueviolet.svg)](#core-concepts)
[![GNN+PPO](https://img.shields.io/badge/GNN%2BPPO-124K_params-red.svg)](#7-gnn--ppo-neural-network)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Overview

This project has two main components:

1. **MetamathProver/** — Machine-verified proofs in Lean 4 (groups, rings)
2. **nucleo/** — Adaptive mathematical reasoning system (NLE v7.0, ~12,800 LOC Python)

The goal is to build a **mathematical AI** that can:
- Understand mathematical queries in natural language
- Generate formal proofs in Lean 4
- Learn and improve through interaction via Memory Evolutive Systems

---

## Architecture

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
│  Axiomas 8.1-8.4 (Hierarchy, Multiplicity, Connectivity, Coverage)  │
│  Teoremas 8.5-8.7 (Consistency, Emergence, Coverage Preservation)   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
metamath-prover/
│
├── MetamathProver/              # Pruebas Lean 4 verificadas
│   ├── Group/                   #   Teoria de grupos
│   └── Ring/                    #   Teoria de anillos
│
├── nucleo/                      # Sistema NLE v7.0 (~12,800 LOC)
│   ├── core.py                  #   Orquestador principal (Nucleo + graph context)
│   ├── cli.py                   #   CLI + chat interactivo con Claude
│   ├── __main__.py              #   Entry point: python -m nucleo
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
│   │   ├── gnn.py               #     SkillGNN (3x GATConv, 4 attention heads)
│   │   ├── networks.py          #     Actor-Critic (124,420 params)
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
│   ├── test_gnn.py              #     GNN encoder (19 tests)
│   ├── test_ppo.py              #     PPO + Actor-Critic (25 tests)
│   ├── test_live_learning.py    #     Aprendizaje en vivo (24 tests)
│   ├── test_pillars.py          #     4 pilares fundacionales
│   ├── test_hierarchy_integration.py #  GoalAnalyzer, graph context, CR_tac graph-aware
│   ├── test_cli.py              #     CLI + chat interactivo
│   └── test_types.py            #     Tipos basicos
│
├── examples/                    #   Ejemplos de uso
│   ├── basic_usage.py
│   ├── complete_flow.py
│   ├── demo_external_skills.py
│   └── lean_integration.py
│
├── scripts/                     #   Utilidades
│   ├── visualize_embeddings.py  #     Visualizacion t-SNE de embeddings GNN
│   └── generate_pdf.py          #     Generador de PDF de mejoras
├── PLAN.md                      #   Plan de implementacion (fases 0-7)
└── IMPLEMENTATION_PLAN.md       #   Plan detallado original
```

---

## Core Concepts

### 1. Hierarchical Skill Category

Skills (knowledge units) are organized in a categorical hierarchy:

| Level | Name | Example |
|-------|------|---------|
| 0 | Atoms | Axiom of extensionality, modus ponens |
| 1 | Clusters | ZFC-axioms, FOL-rules, Type-rules |
| 2 | Skills | Mathematical induction, Curry-Howard |
| 3 | Competences | Lean verification, Forcing |
| 4+ | Meta-skills | Inter-pillar translations |

Four foundational **pillars** organize knowledge: SET (ZFC), CAT (Category Theory), LOG (FOL + IL), TYPE (CIC/Lean 4). The system includes **76 mathematical skills**: 10 foundational (level 0) + 66 domain skills (levels 1-2) across 14 categories.

#### Domain Skills (66 skills, 14 categories)

| Category | Skills | Level 1 | Level 2 |
|----------|--------|---------|---------|
| Algebra | 7 | group-theory, ring-theory, field-theory, linear-algebra, module-theory | commutative-algebra, homological-algebra |
| Geometry | 6 | euclidean-geometry, differential-geometry, projective-geometry | algebraic-geometry, riemannian-geometry, symplectic-geometry |
| Analysis | 6 | real-analysis, complex-analysis, measure-theory | functional-analysis, harmonic-analysis, pde-theory |
| Topology | 5 | point-set-topology, algebraic-topology | differential-topology, homotopy-theory, knot-theory |
| Logic | 3 | model-theory | proof-theory, homotopy-type-theory |
| Number Theory | 4 | elementary-number-theory, algebraic-number-theory | analytic-number-theory, arithmetic-geometry |
| Combinatorics | 6 | enumerative-combinatorics, graph-theory, matroid-theory | extremal-combinatorics, additive-combinatorics, combinatorial-optimization |
| Probability | 4 | probability-theory, stochastic-processes | ergodic-theory, stochastic-calculus |
| Set Theory | 1 | descriptive-set-theory | |
| Category Theory | 2 | topos-theory | homological-algebra-cat |
| Computation | 4 | algorithm-analysis, formal-languages | computational-complexity, type-theory-advanced |
| Optimization | 3 | convex-optimization | variational-methods, optimal-control |
| **Lean Tactics** | **9** | simp, rewrite, exact, apply, induction, omega, ring, aesop, calc | |
| **Proof Strategies** | **6** | | backward, forward, contradiction, cases, inductive, construction |

```python
from nucleo.graph.category import SkillCategory
from nucleo.types import Skill, PillarType, MorphismType

cat = SkillCategory("MathKnowledge")

# Add skills at different levels
cat.add_skill(Skill(id="zfc", name="ZFC", pillar=PillarType.SET, level=0))
cat.add_skill(Skill(id="group-theory", name="Group Theory", pillar=PillarType.SET, level=1))
cat.add_morphism("zfc", "group-theory", MorphismType.DEPENDENCY)

# Verify formal axioms (8.1-8.4)
result = cat.verify_all_axioms()
print(result["all_satisfied"])  # True if hierarchy + multiplicity + connectivity + coverage hold
```

### 2. Co-Regulator Network

Four co-regulators operate at different timescales:

| Co-Regulator | Level | Frequency | Function |
|--------------|-------|-----------|----------|
| **CR_tac** (Tactical) | 0-1 | Every step | Select tactics, respond |
| **CR_org** (Organizational) | 1-2 | Every 10 steps | Reorganize graph, create bridges |
| **CR_str** (Strategic) | 2-3 | Every 100 steps | Create colimits, new levels |
| **CR_int** (Integrity) | All | Periodic | Verify axioms, repair |

```python
from nucleo.mes.co_regulators import CoRegulatorNetwork

network = CoRegulatorNetwork(cr_org_frequency=10, cr_str_frequency=100)
results = network.step(cat)
for cr_type, action, option in results:
    print(f"{cr_type.name}: {action.name}")
```

### 3. Patterns and Colimits

A **pattern** is a group of skills that work together. Its **colimit** is a new skill that integrates them (emergence):

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
# new_skill is at max(component_levels) + 1
# Colimit satisfies universal property
```

### 4. Evolution and Formal Properties

The system evolves through **complexification** (Options with absorptions, eliminations, bindings):

```python
from nucleo.graph.evolution import EvolutionarySystem
from nucleo.types import Option, Skill

evo = EvolutionarySystem(cat)

# Apply evolution step
option = Option(absorptions=[
    Skill(id="topology", name="Topology", pillar=PillarType.SET, level=1)
])
functor = evo.apply_option(option)

# Verify theorems hold after evolution
result = evo.verify_all_theorems()
assert result["8.5_consistency"]["satisfies"]   # Axioms preserved
assert result["8.6_emergence"]["satisfies"]     # Complexity grows
assert result["8.7_coverage_preservation"]["satisfies"]  # Coverage maintained
```

### 5. Lean 4 Integration (Solver Cascade + GoalAnalyzer)

APOLLO-inspired solver cascade tries 9 automated tactics before falling back to LLM.
**GoalAnalyzer** reorders the cascade based on goal structure and graph context:

```
Default:  rfl -> simp -> ring -> linarith -> nlinarith -> omega -> exact? -> apply? -> aesop
Smart:    goal "a * b + c = c + b * a" → ring -> nlinarith -> linarith -> rfl -> simp -> ...
Graph:    ring-theory skill → neighbors → tactic-ring, tactic-simp → prioritize ring, simp
```

```python
from nucleo.lean.solver_cascade import SolverCascade, GoalAnalyzer

# Goal-aware tactic ordering
analyzer = GoalAnalyzer()
ordered = analyzer.prioritize("a * b + c = c + b * a")  # ring first
ordered = analyzer.prioritize("Nat.succ n ≤ n + 1")     # omega first
ordered = analyzer.prioritize("P ∧ Q → Q ∧ P")          # simp first

# With graph context: domain skills → connected tactics
ordered = analyzer.prioritize("ring homomorphism", graph=skill_graph)
# ring-theory → tactic-ring, tactic-simp → ring, simp prioritized

# Smart cascade: try_fill_sorry_smart reorders before trying
result = await cascade.try_fill_sorry_smart(code, sorry_line, goal_text="a * b = b * a")
```

### 6. MES Memory

Four types of memory with E-equivalence and E-concept formation:

| Type | Description | Example |
|------|-------------|---------|
| **Empirical** | Concrete experiences | "Used `simp` to solve x + 0 = x" |
| **Procedural** | Successful sequences | "For forall, use `intro` then `apply`" |
| **Semantic** | Abstract E-concepts | "Induction is useful for N" |
| **Consolidated** | Reinforced knowledge | Skills used 3+ times |

### 7. GNN + PPO Neural Network

The system uses a Graph Neural Network with Proximal Policy Optimization for intelligent skill selection:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   SkillGNN      │────>│  Actor-Critic    │────>│  PPO + GAE      │
│                 │     │                  │     │                 │
│  3x GATConv     │     │  Actor: π(a|s)   │     │  clip ratio     │
│  4 attn heads   │     │  Critic: V(s)    │     │  entropy bonus  │
│  edge_attr      │     │  124,420 params  │     │  λ-returns      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

```python
from nucleo.rl.gnn import SkillGNN, graph_to_pyg
from nucleo.rl.networks import ActorCriticNetwork
from nucleo.rl.agent import NucleoAgent

# Create neural agent
agent = NucleoAgent(num_skills=76, use_neural=True)

# Agent selects skills using GNN embeddings + PPO policy
action = agent.select_action(state, query="Prove by induction on n")
```

### 8. Live Learning from Chat

Every chat interaction feeds the PPO training loop:

```
Usuario pregunta ──> Claude responde ──> Reward calculada ──> PPO update
                                              │
                                              v
                                    Procedural Memory
                                    (query, tactic, goal)
                                              │
                                              v
                                    Weights guardados cada 10 pasos
```

The agent checks proven patterns in procedural memory before falling back to the neural network, creating a hybrid memory+neural decision system.

```python
from nucleo.core import Nucleo

nucleo = Nucleo()
nucleo.set_neural_agent(agent)  # Enable live PPO learning
# Now every chat interaction trains the neural network
```

### 9. Hierarchy-Reasoning Integration

The categorical skill graph actively influences proof generation at 3 integration points:

**A. GoalAnalyzer** (`solver_cascade.py`): Analyzes goal text with regex patterns + graph traversal to reorder the tactic cascade. A goal like `a * b + c = c + b * a` prioritizes `ring` instead of wasting time with `rfl`, `simp`.

**B. Graph-Aware Context** (`core.py`): Queries are matched against skill names in the graph. For each match, dependencies and connected tactic/strategy skills are traversed to build relevant context for the LLM, replacing random skill ID slicing.

**C. Graph-Informed CR_tac** (`co_regulators.py`): The tactical co-regulator now has a 3-level classification chain: neural agent → keyword matching → graph skill matching. A query about "ring homomorphism" triggers ASSIST because `ring-theory` connects to `tactic-ring` via TRANSLATION morphisms.

```
Query: "ring homomorphism"
  → CR_tac: graph match → ring-theory → neighbor tactic-ring → ASSIST
  → GoalAnalyzer: ring pattern → ring, nlinarith, linarith first
  → Context: ring-theory → deps [zfc-axioms] + tactics [ring, simp] → LLM
```

### 10. Skill Graph Visualization

Visualize GNN embeddings with t-SNE projection:

```bash
python scripts/visualize_embeddings.py          # Save to data/skill_embeddings.png
python scripts/visualize_embeddings.py --show    # Interactive window
```

Generates 4 panels: graph structure, t-SNE embeddings by pillar, category clusters, and pillar distance heatmap.

---

## Formal Properties

The system verifies the formal properties from the MES specification:

### Axioms (verified on SkillCategory)

| Axiom | Property | Condition |
|-------|----------|-----------|
| 8.1 | Hierarchy | >= 2 hierarchical levels |
| 8.2 | Multiplicity | >= 2 pillars with inter-pillar translations |
| 8.3 | Connectivity | Weakly connected + inter-pillar connections |
| 8.4 | Coverage | Every skill reachable from a pillar skill |

### Theorems (verified on EvolutionarySystem)

| Theorem | Property | Condition |
|---------|----------|-----------|
| 8.5 | Consistency | Complexification preserves all axioms |
| 8.6 | Emergence | Complexity grows or stabilizes over time |
| 8.7 | Coverage Preservation | Coverage maintained under evolution |

---

## Verified Lean 4 Proofs

The `MetamathProver/` directory contains machine-verified proofs:

| Theorem | Statement | Directory |
|---------|-----------|-----------|
| First Isomorphism (Groups) | G / ker(f) ~=* im(f) | `Group/` |
| First Isomorphism (Rings) | R / ker(f) ~=+* im(f) | `Ring/` |
| Kernel is Normal Subgroup | ker(f) normal in G | `Group/` |
| Kernel is Bilateral Ideal | ker(f) is ideal | `Ring/` |

---

## Installation

### Requirements

```bash
# Python 3.10+
python --version  # Must be 3.10 or higher

# Dependencies
pip install pyyaml rich anthropic

# Neural network (GNN + PPO)
pip install torch torch-geometric

# (Optional) Lean 4 for proof verification
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh
```

### Clone and Build

```bash
git clone https://github.com/ai-enhanced-engineer/metamath-prover.git
cd metamath-prover

# (Optional) Download Mathlib cache
lake exe cache get
lake build
```

### Verify Installation

```bash
python -c "
from nucleo.graph.category import SkillCategory
from nucleo.graph.evolution import EvolutionarySystem
from nucleo.mes.co_regulators import CoRegulatorNetwork
print('NLE v7.0 installed correctly')
"
```

### Interactive Chat with Claude

```bash
# Set your Anthropic API key
set ANTHROPIC_API_KEY=sk-ant-...          # Windows CMD
$env:ANTHROPIC_API_KEY="sk-ant-..."       # PowerShell
export ANTHROPIC_API_KEY=sk-ant-...       # Linux/Mac

# Start interactive session
python -m nucleo chat

# With faster/cheaper model
python -m nucleo chat --model claude-haiku-4-5-20251001

# With debug info (RL actions)
python -m nucleo chat --verbose
```

Commands inside chat: `/help`, `/stats`, `/skills`, `/axioms`, `/clear`, `/quit`

Example session:
```
┌─── Chat Interactivo ───┐
│ NLE v7.0 — Nucleo Logico Evolutivo      │
│ Modelo: claude-haiku-4-5-20251001       │
└─────────────────────────┘
Listo. 76 skills cargados.

Tu > Que es un grupo en algebra abstracta?
[RESPONSE | confianza: 0.80]
Un **grupo** es una estructura algebraica (G, ·) donde G es un conjunto
con una operación binaria · que es asociativa, tiene elemento neutro e,
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
│ 76 skills across 4 pillars   │
└──────────────────────────────┘

Tu > /quit
Adios!
```

---

## Tests

379 tests across 17 test suites:

```bash
python -m pytest tests/ -v
```

| Suite | Tests | Coverage |
|-------|-------|----------|
| test_types | 10 | Types, Skill, Morphism, State, Action |
| test_graph | 12 | SkillCategory, axioms, serialization |
| test_pillars | 16 | SET, CAT, LOG, TYPE pillars |
| test_evolution | 10 | Snapshots, transition functors, compatibility |
| test_colimits | 26 | Patterns, cocones, universal property, colimits |
| test_emergence | 14 | Link classification, emergence detection |
| test_multiplicity | 10 | Homology, multiplicity principle |
| test_coregulators | 19 | 4 co-regulators, network, shared resources |
| test_memory | 16 | E-equivalence, E-concepts, procedural memory |
| test_lean_integration | 48 | Solver cascade, sorry analyzer, structured errors |
| test_formal_properties | 26 | Axioms 8.1-8.4, Theorems 8.5-8.7 |
| test_math_domains | 32 | 66 domain skills, dependency chains, inter-pillar translations |
| test_gnn | 19 | SkillGNN, GATConv, graph_to_pyg, embeddings |
| test_ppo | 25 | Actor-Critic, PPO update, GAE, encode_query |
| test_live_learning | 24 | Lean tactics, proof strategies, procedural memory, live PPO |
| test_hierarchy_integration | 27 | GoalAnalyzer, graph context, CR_tac graph-aware |
| test_cli | 10 | CLI structure, chat command, __main__.py |
| **Total** | **379** | |

---

## Implementation Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Bugfixes (4 critical) | Done |
| 1 | Colimits (universal property, co-cones) | Done |
| 2 | Evolution (snapshots, transition functors) | Done |
| 3 | Emergence (link classification, detection) | Done |
| 4 | Multiplicity (homology, pillar multiplicity) | Done |
| 5 | Co-Regulators + Memory (E-equivalence, core.py) | Done |
| 6 | Lean skills (solver cascade, sorry analyzer) | Done |
| 7 | Formal properties (axioms 8.1-8.4, theorems 8.5-8.7) | Done |

### Progress: ~95%

All 8 phases complete. GNN+PPO infrastructure built (124,420 params), live learning connected.

### Remaining Work

- Training dataset (need math problem corpus for offline training)
- Real-world usage to accumulate procedural memory patterns
- End-to-end evaluation pipeline

---

## References

### Lean & Mathlib
- [Mathlib4 Documentation](https://leanprover-community.github.io/mathlib4_docs/)
- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)

### Memory Evolutive Systems (MES)
- Ehresmann, A. C., & Vanbremeersch, J. P. (2007). *Memory Evolutive Systems: Hierarchy, Emergence, Cognition*. Elsevier.
- Ehresmann, A. C. (2012). MENS, a mathematical model for cognitive systems. *Journal of Mind Theory*, 0(2).

### Solver Cascade
- Wang et al. (2025). APOLLO: Automated LLM and Lean Collaboration for Mathematical Reasoning. *arXiv:2505.05758*.

### Reinforcement Learning & GNN
- Schulman, J. et al. (2017). Proximal Policy Optimization Algorithms. *arXiv:1707.06347*.
- Velickovic, P. et al. (2018). Graph Attention Networks. *ICLR 2018*.
- Fey, M. & Lenssen, J. E. (2019). Fast Graph Representation Learning with PyTorch Geometric. *ICLR Workshop on Representation Learning on Graphs*.

---

## Author

**Leonardo Jimenez Martinez** — UNAM

---

## License

MIT License. See [LICENSE](LICENSE) for details.
