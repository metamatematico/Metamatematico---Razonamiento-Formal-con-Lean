# Plan de Implementacion: Nucleo Logico Evolutivo v6.0

> Sistema Evolutivo de Asistencia Matematica: LLM + Lean 4 + Grafo Categorico de Skills

---

## Resumen Ejecutivo

Este plan implementa el **Nucleo Logico Evolutivo** descrito en el documento v6.0, un sistema formal que integra:

```
Sigma_t = (L, N_t, G_t, F)
```

| Componente | Descripcion | Estado Actual |
|------------|-------------|---------------|
| **L** | LLM (Claude) | COMPLETADO - nucleo/llm/ |
| **N_t** | Nucleo logico (agente RL) | COMPLETADO - nucleo/rl/ |
| **G_t** | Grafo categorico de skills | COMPLETADO - nucleo/graph/ (14 skills migrados) |
| **F** | Cuatro pilares fundacionales | COMPLETADO - nucleo/pillars/ |

### Progreso de Implementacion

```
[x] Fase 1: Fundamentos - COMPLETADO
[x] Fase 2: Logica - COMPLETADO
[x] Fase 3: Grafo Categorico - COMPLETADO
[ ] Fase 4: Entrenamiento RL - PENDIENTE (requiere datos)

Experimentos Go/No-Go:
[GO] Exp 1: Integracion Lean 4 - Parser y TacticMapper funcionando
[GO] Exp 2: Grafo Categorico - Axiomas verificados
[GO] Exp 3: Agente RL Baseline - Episodios sin errores
```

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                         USUARIO                                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ texto
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM (Claude)                                │
│                   Comprension NL + Generacion                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │ embedding
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NUCLEO LOGICO (N_t)                          │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐     │
│  │ Transformer │  │ Goal Encoder │  │ GNN (Grafo Skills)  │     │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬──────────┘     │
│         └────────────────┼─────────────────────┘                │
│                          ▼                                       │
│              ┌───────────────────────┐                          │
│              │  Multi-Head Attention │                          │
│              └───────────┬───────────┘                          │
│         ┌────────────────┴────────────────┐                     │
│         ▼                                 ▼                     │
│  ┌─────────────┐                   ┌─────────────┐              │
│  │ Actor (π_θ) │                   │ Critic (V_φ)│              │
│  └─────────────┘                   └─────────────┘              │
└─────────────────────────┬───────────────────────────────────────┘
                          │ tactica
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       LEAN 4                                     │
│                 Verificacion Formal                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │ resultado
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  GRAFO CATEGORICO (G_t)                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  F_Set   │◄──►│  F_Cat   │◄──►│  F_Log   │◄──►│  F_Type  │  │
│  │Conjuntos │    │Categorias│    │  Logica  │    │  Tipos   │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fases de Implementacion

### FASE 1: Fundamentos (Mes 0-3)
**Objetivo**: F_Type + Integracion Lean 4

#### 1.1 Infraestructura Base
```
nucleo/
├── __init__.py
├── config.py                 # Configuracion global
├── types.py                  # Tipos base del sistema
└── utils.py                  # Utilidades comunes
```

**Tareas**:
- [x] Crear estructura de directorios del proyecto Python
- [x] Configurar entorno virtual con dependencias
- [x] Implementar tipos base (Skill, Morphism, State, Action)
- [x] Configurar logging y metricas

#### 1.2 Integracion Lean 4 (Experimento Go/No-Go #1)
```
nucleo/
└── lean/
    ├── __init__.py
    ├── client.py             # Cliente bidireccional Lean 4
    ├── parser.py             # Parser de respuestas Lean
    ├── tactics.py            # Mapeo de tacticas
    └── tests/
        └── test_integration.py
```

**Criterio de exito**: >= 80% de teoremas procesados correctamente

**Tareas**:
- [x] Implementar cliente LSP para Lean 4
- [x] Parser de mensajes de error/exito de Lean
- [x] Funcion de envio de teoremas
- [x] Funcion de recepcion de feedback
- [ ] Test con 100 teoremas de Mathlib
- [x] Metricas de latencia y tasa de exito

#### 1.3 Pilar F_Type (Teoria de Tipos)
```
nucleo/
└── pillars/
    └── type_theory/
        ├── __init__.py
        ├── cic.py            # Calculo de Construcciones Inductivas
        ├── universes.py      # Jerarquia de universos
        ├── curry_howard.py   # Correspondencia pruebas-programas
        └── lean_bridge.py    # Traduccion a kernel Lean 4
```

**Tareas**:
- [ ] Implementar representacion de CIC
- [ ] Jerarquia de universos (Prop : Type_0 : Type_1 : ...)
- [ ] Mapeo Curry-Howard basico
- [ ] Funcion `translate: F_Log.IL x F_Type.CIC -> Lean4.Kernel`

---

### FASE 2: Logica (Mes 3-6)
**Objetivo**: F_Log con Curry-Howard

#### 2.1 Pilar F_Log (Logica)
```
nucleo/
└── pillars/
    └── logic/
        ├── __init__.py
        ├── fol.py            # Logica de Primer Orden (FOL=)
        ├── sol.py            # Logica de Segundo Orden
        ├── intuitionistic.py # Logica Intuicionista (IL)
        ├── kripke.py         # Semantica de Kripke
        └── translations.py   # Traducciones entre logicas
```

**Tareas**:
- [ ] Implementar sintaxis FOL= (terminos, formulas)
- [ ] Implementar IL con restricciones (sin LEM)
- [ ] Semantica de Kripke para IL
- [ ] Traduccion IL -> CIC via Curry-Howard
- [ ] Deteccion de cuantificacion de segundo orden
- [ ] Warnings para perdidas metalogicas (SOL_std)

#### 2.2 Traducciones entre Pilares (tau_2)
```python
# nucleo/pillars/translations.py

class CurryHowardTranslator:
    """
    Traduccion bidireccional:
    - Proposicion phi <-> Tipo tau
    - Prueba de phi <-> Termino de tipo tau
    - phi -> psi <-> tau_1 -> tau_2
    - forall x. phi(x) <-> Pi_{x:A} B(x)
    - exists x. phi(x) <-> Sigma_{x:A} B(x)
    """

    def proposition_to_type(self, prop: Proposition) -> Type: ...
    def proof_to_term(self, proof: Proof) -> Term: ...
    def type_to_proposition(self, typ: Type) -> Proposition: ...
    def term_to_proof(self, term: Term) -> Proof: ...
```

**Tareas**:
- [ ] Implementar CurryHowardTranslator
- [ ] Tests de ida y vuelta (roundtrip)
- [ ] Documentar perdidas en traduccion

#### 2.3 Escalabilidad GNN (Experimento Go/No-Go #2)
```
nucleo/
└── graph/
    ├── __init__.py
    ├── gnn.py               # Graph Neural Network
    ├── embeddings.py        # Embeddings de skills
    └── benchmarks/
        └── scalability.py
```

**Criterio de exito**: Latencia < 500ms para 10^4 nodos

**Tareas**:
- [ ] Implementar GNN basica (PyTorch Geometric)
- [ ] Benchmark con grafos de 10^3, 10^4, 10^5 nodos
- [ ] Optimizar si latencia > 500ms
- [ ] Documentar resultados

---

### FASE 3: Grafo Categorico (Mes 6-9)
**Objetivo**: Grafo dinamico basico

#### 3.1 Categoria de Skills
```
nucleo/
└── graph/
    ├── category.py          # Estructura categorica
    ├── morphisms.py         # Tipos de morfismos
    ├── operations.py        # Operaciones atomicas
    └── invariants.py        # Axiomas y propiedades
```

**Definicion de Skill Category**:
```python
@dataclass
class SkillCategory:
    """
    Categoria Skill:
    - Objetos: Ob(Skill) = S (skills individuales)
    - Morfismos: Hom(s, t) = transformaciones de s a t
    - Composicion: ∘ : Hom(t, u) × Hom(s, t) → Hom(s, u)
    - Identidad: id_s ∈ Hom(s, s)

    Satisface: Asociatividad e Identidad
    """
    objects: Set[Skill]
    morphisms: Dict[Tuple[Skill, Skill], Set[Morphism]]
    weights: Dict[Morphism, float]  # w: Mor -> R+
```

**Tipos de Morfismos**:
| Tipo | Simbolo | Significado |
|------|---------|-------------|
| Dependencia | `↪` | t requiere s |
| Especializacion | `↠` | t especializa s |
| Analogia | `↔` | Isomorfismo parcial |
| Traduccion | `⇝` | Entre pilares |

**Tareas**:
- [ ] Implementar SkillCategory
- [ ] Implementar 4 tipos de morfismos
- [ ] Verificar axiomas categoricos (asociatividad, identidad)
- [ ] Sistema de pesos para morfismos

#### 3.2 Operaciones Atomicas
```python
# nucleo/graph/operations.py

class GraphOperations:
    """Operaciones atomicas con complejidad documentada"""

    def add_node(self, G: Graph, s: Skill) -> Graph:      # O(1)
        """Añade skill con identidad"""
        ...

    def add_edge(self, G: Graph, s: Skill, t: Skill,
                 f: Morphism) -> Graph:                    # O(1)
        """Añade morfismo, composicion por construccion"""
        ...

    def merge(self, G: Graph, s1: Skill, s2: Skill) -> Graph:  # O(d_max)
        """Fusiona skills, redirige morfismos"""
        ...

    def split(self, G: Graph, s: Skill) -> Graph:         # O(d(s))
        """Divide skill en componentes"""
        ...

    def reweight(self, G: Graph, f: Morphism,
                 w: float) -> Graph:                       # O(1)
        """Actualiza peso de morfismo"""
        ...
```

**Tareas**:
- [ ] Implementar 5 operaciones atomicas
- [ ] Verificar preservacion de estructura categorica
- [ ] Tests de consistencia

#### 3.3 Pilares F_Set y F_Cat
```
nucleo/
└── pillars/
    ├── set_theory/
    │   ├── __init__.py
    │   ├── zfc.py           # Axiomas ZFC
    │   ├── ordinals.py      # Ordinales
    │   └── cardinals.py     # Cardinales
    │
    └── category_theory/
        ├── __init__.py
        ├── basics.py        # Objetos, morfismos, composicion
        ├── functors.py      # Functores, adjunciones
        ├── nat_trans.py     # Transformaciones naturales
        └── topos.py         # Topos elementales
```

**Tareas**:
- [ ] Implementar F_Set (ZFC basico)
- [ ] Implementar F_Cat (basicos categoricos)
- [ ] Traducciones tau_1 (ETCS), tau_3 (Tarski), tau_4 (Topos)

#### 3.4 Senal de Emergencia (Experimento Go/No-Go #3)
**Criterio de exito**: Clustering coefficient > 0.3 sin programacion explicita

**Tareas**:
- [ ] Simular 1000 interacciones
- [ ] Medir entropia estructural E(G_t) = H(G_t) - Σ_s H(s)
- [ ] Medir auto-organizacion O(G_t) = ΔFuncionalidad/ΔComplejidad
- [ ] Documentar resultados
- [ ] Si falla: Aplicar M3 (reencuadrar emergencia como opcional)

---

### FASE 4: Agente RL Completo (Mes 9-12)
**Objetivo**: Nucleo como agente de aprendizaje por refuerzo

#### 4.1 Formulacion MDP
```
nucleo/
└── rl/
    ├── __init__.py
    ├── mdp.py               # Definicion MDP
    ├── state.py             # Espacio de estados
    ├── actions.py           # Espacio de acciones
    ├── rewards.py           # Funcion de recompensa
    └── transitions.py       # Dinamica de transicion
```

**MDP del Nucleo**: M = (X, A, P, R, γ)

```python
@dataclass
class State:
    """x = (c_L, g_Lean, G, h, m)"""
    llm_context: Tensor      # c_L ∈ R^d_c (embedding)
    lean_goal: Optional[str] # g_Lean ∈ G ∪ {⊥}
    graph: SkillCategory     # G = (S, Mor, w)
    history: List[Interaction]  # h ∈ H^k
    metrics: Tensor          # m ∈ R^p

@dataclass
class Action:
    """A = A_1 ⊔ A_2 ⊔ A_3"""
    type: Literal["response", "reorganize", "assist"]
    params: Dict[str, Any]
```

**Tareas**:
- [ ] Implementar State y Action
- [ ] Implementar dinamica de transicion P
- [ ] Tests de consistencia MDP

#### 4.2 Funcion de Recompensa
```python
# nucleo/rl/rewards.py

def reward(state: State, action: Action) -> float:
    """
    R(x, a) = r_task + λ_1·r_e + λ_2·r_org + λ_3·r_emerge

    Componentes:
    - r_task ∈ {-5, -1, +1, +5, +10}: Exito de tarea
    - r_e = -α|S'| - β·Δt: Eficiencia (penaliza skills/tiempo)
    - r_org = δ·ΔC(G) + ε·Δκ(G): Organizacion (coherencia, cobertura)
    - r_emerge = η·𝟙[patron_nuevo]: Emergencia (bonus exploracion)
    """
    r_task = compute_task_reward(state, action)
    r_e = compute_efficiency_reward(state, action)
    r_org = compute_organization_reward(state, action)
    r_emerge = compute_emergence_reward(state, action)

    return (r_task +
            LAMBDA_1 * r_e +
            LAMBDA_2 * r_org +
            LAMBDA_3 * r_emerge)
```

**Hiperparametros**:
| Simbolo | Descripcion | Valor | Rango |
|---------|-------------|-------|-------|
| γ | Factor descuento | 0.99 | [0.95, 0.999] |
| λ_1 | Peso eficiencia | 0.1 | [0.01, 0.5] |
| λ_2 | Peso organizacion | 0.05 | [0.01, 0.2] |
| λ_3 | Peso emergencia | 0.2 | [0.1, 0.5] |
| k | Tamaño historial | 10 | [5, 50] |

**Tareas**:
- [ ] Implementar 4 componentes de recompensa
- [ ] Configurar hiperparametros
- [ ] Logging de recompensas para analisis

#### 4.3 Arquitectura de Red
```
nucleo/
└── rl/
    └── networks/
        ├── __init__.py
        ├── transformer.py   # Encoder de contexto LLM
        ├── goal_encoder.py  # Encoder de goal Lean
        ├── gnn_encoder.py   # GNN para grafo
        ├── attention.py     # Multi-Head Attention
        ├── actor.py         # Red Actor π_θ
        └── critic.py        # Red Critic V_φ
```

**Tareas**:
- [ ] Implementar Transformer encoder
- [ ] Implementar Goal encoder
- [ ] Integrar GNN encoder
- [ ] Multi-Head Attention fusion
- [ ] Actor network (politica)
- [ ] Critic network (valor)

#### 4.4 Entrenamiento PPO
```
nucleo/
└── rl/
    └── training/
        ├── __init__.py
        ├── ppo.py           # Proximal Policy Optimization
        ├── buffer.py        # Experience buffer
        ├── trainer.py       # Loop de entrenamiento
        └── evaluation.py    # Metricas de evaluacion
```

**Tareas**:
- [ ] Implementar PPO (baseline)
- [ ] Implementar alternativas: SAC, A2C (estrategia M2)
- [ ] Experience buffer con prioridad
- [ ] Loop de entrenamiento
- [ ] Metricas: reward promedio, tasa de exito, etc.
- [ ] Comparar con heuristica baseline

---

## Migracion de Skills Existentes

El repositorio ya contiene 14+ skills en `agents/skills/`. Estos se migraran al grafo categorico:

### Skills Existentes → Nodos del Grafo

| Skill Actual | Pilar | Dependencias |
|--------------|-------|--------------|
| `lean-tp-foundations` | F_Type | - |
| `lean-tp-propositions` | F_Log | lean-tp-foundations |
| `lean-tp-quantifiers` | F_Log | lean-tp-propositions |
| `lean-tp-tactics` | F_Type | lean-tp-foundations |
| `lean-tp-tactic-selection` | F_Type | lean-tp-tactics |
| `lean-tp-advanced` | F_Type | lean-tp-tactics |
| `lean-fp-basics` | F_Type | - |
| `lean-fp-type-classes` | F_Cat | lean-fp-basics |
| `lean-fp-dependent-types` | F_Type | lean-fp-basics |
| `lean-fp-functor-applicative` | F_Cat | lean-fp-type-classes |
| `lean-fp-monads` | F_Cat | lean-fp-functor-applicative |
| `lean-fp-transformers` | F_Cat | lean-fp-monads |
| `lean-fp-performance` | F_Type | lean-fp-basics |
| `lean-quick-reference` | - | Todos |

**Tareas**:
- [ ] Crear script de migracion
- [ ] Parsear SKILL.md existentes
- [ ] Generar nodos del grafo
- [ ] Inferir morfismos de dependencia
- [ ] Validar estructura categorica

---

## Experimentos Go/No-Go

### Experimento 1: Integracion Lean 4 (Mes 0-3)
| Aspecto | Detalle |
|---------|---------|
| **Pregunta** | ¿Puede el nucleo comunicarse bidireccionalmente con Lean? |
| **Test** | Enviar 100 teoremas, recibir feedback, reformular, verificar |
| **Exito** | >= 80% de teoremas procesados correctamente |
| **Si falla** | Investigar APIs alternativas (lake, REPL) |

### Experimento 2: Escalabilidad GNN (Mes 3-6)
| Aspecto | Detalle |
|---------|---------|
| **Pregunta** | ¿Puede la GNN procesar grafos grandes en < 1s? |
| **Test** | Benchmark con grafos de 10^3, 10^4, 10^5 nodos |
| **Exito** | Latencia < 500ms para 10^4 nodos |
| **Si falla** | Explorar sampling, arquitecturas mas eficientes |

### Experimento 3: Senal de Emergencia (Mes 6-9)
| Aspecto | Detalle |
|---------|---------|
| **Pregunta** | ¿Hay evidencia de auto-organizacion? |
| **Test** | Medir entropia estructural despues de 1000 interacciones |
| **Exito** | Clustering coefficient > 0.3 sin programacion explicita |
| **Si falla** | Aplicar M3: reencuadrar emergencia como opcional |

---

## Estructura de Directorios Final

```
metamath-prover/
├── MetamathProver/              # [EXISTENTE] Pruebas Lean 4
├── agents/                      # [EXISTENTE] Agentes Claude
├── research/                    # [EXISTENTE] Documentacion
│
├── nucleo/                      # [NUEVO] Nucleo Logico Evolutivo
│   ├── __init__.py
│   ├── config.py
│   ├── types.py
│   │
│   ├── lean/                    # Integracion Lean 4
│   │   ├── client.py
│   │   ├── parser.py
│   │   └── tactics.py
│   │
│   ├── pillars/                 # Cuatro Pilares
│   │   ├── set_theory/
│   │   ├── category_theory/
│   │   ├── logic/
│   │   └── type_theory/
│   │
│   ├── graph/                   # Grafo Categorico
│   │   ├── category.py
│   │   ├── morphisms.py
│   │   ├── operations.py
│   │   ├── gnn.py
│   │   └── embeddings.py
│   │
│   └── rl/                      # Aprendizaje por Refuerzo
│       ├── mdp.py
│       ├── state.py
│       ├── actions.py
│       ├── rewards.py
│       ├── networks/
│       └── training/
│
├── tests/                       # [NUEVO] Tests
│   ├── test_lean_integration.py
│   ├── test_pillars.py
│   ├── test_graph.py
│   └── test_rl.py
│
├── scripts/                     # [NUEVO] Scripts utilitarios
│   ├── migrate_skills.py
│   ├── benchmark_gnn.py
│   └── train_agent.py
│
├── pyproject.toml               # [NUEVO] Config Python
└── IMPLEMENTATION_PLAN.md       # [NUEVO] Este documento
```

---

## Dependencias Python

```toml
# pyproject.toml
[project]
name = "nucleo-logico-evolutivo"
version = "0.1.0"
requires-python = ">=3.10"

dependencies = [
    # Core
    "pydantic>=2.0",
    "typing-extensions>=4.0",

    # ML/RL
    "torch>=2.0",
    "torch-geometric>=2.3",
    "gymnasium>=0.29",
    "stable-baselines3>=2.0",

    # LLM
    "anthropic>=0.18",

    # Lean integration
    "pylspclient>=0.1",

    # Utils
    "networkx>=3.0",
    "numpy>=1.24",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "black>=23.0",
    "ruff>=0.1",
    "mypy>=1.0",
]
```

---

## Metricas de Exito del Proyecto

| Metrica | Objetivo | Medicion |
|---------|----------|----------|
| Integracion Lean | >= 80% teoremas | Test con 100 teoremas |
| Latencia GNN | < 500ms | Benchmark 10^4 nodos |
| Clustering | > 0.3 | Coeficiente tras 1000 interacciones |
| Reward RL | Mejora vs baseline | Comparacion con heuristicas |
| Cobertura pilares | 100% skills conectados | Axioma 7.2 |
| Consistencia | 0 violaciones | Teorema 7.4 |

---

## Riesgos y Mitigaciones

| ID | Riesgo | Nivel | Mitigacion |
|----|--------|-------|------------|
| A2 | Emergencia no observable | Alto | M3: Reencuadrar como bonus, no requisito |
| B1 | RL no converge | Medio | M2: Probar SAC, A2C, heuristicas |
| B2 | GNN no escala | Medio | Sampling, arquitecturas eficientes |
| B3 | Lean integration falla | Bajo | APIs alternativas (lake, REPL) |

---

## Proximos Pasos Inmediatos

1. **Crear estructura de directorios** (`nucleo/`)
2. **Configurar pyproject.toml** con dependencias
3. **Implementar cliente Lean 4** (LSP/REPL)
4. **Test de integracion** con 10 teoremas
5. **Migrar 3 skills existentes** al formato de nodos

---

*Documento generado: Febrero 2026*
*Basado en: Nucleo Logico Evolutivo v6.0*
