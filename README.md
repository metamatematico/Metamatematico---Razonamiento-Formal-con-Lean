# Demostrador de Enunciados Matemáticos

[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://python.org/)
[![Tests](https://img.shields.io/badge/Tests-284_passing-brightgreen.svg)](#tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Sistema de razonamiento matemático con IA** — NLE v7.0 (Núcleo Lógico Evolutivo)

📚 **Documentación**: [Instalación](INSTALACION.md) | [Ejemplos](EJEMPLOS.md) | [Inicio Rápido](INICIO_RAPIDO.md) | [Fundamentos Teóricos](FUNDAMENTOS_TEORICOS.md)

---

## ¿Qué es este sistema?

Este es un **asistente matemático inteligente** que puede:

✅ **Responder preguntas matemáticas** en lenguaje natural
✅ **Generar demostraciones formales** en Lean 4
✅ **Aprender de la interacción** usando Sistemas de Memoria Evolutiva (MES)
✅ **Razonar sobre 61 dominios matemáticos** (álgebra, topología, análisis, etc.)

### Ejemplo de uso

```
Tu > ¿Qué es un grupo en álgebra abstracta?
[IA] Un grupo es una estructura algebraica (G, ·) donde:
     - G es un conjunto con una operación binaria ·
     - Es asociativa: (a·b)·c = a·(b·c)
     - Tiene elemento neutro e: a·e = e·a = a
     - Todo elemento tiene inverso: a·a⁻¹ = e

Tu > Formaliza eso en Lean 4
[IA] class Group (G : Type u) where
       mul : G → G → G
       one : G
       inv : G → G
       mul_assoc : ∀ a b c, mul (mul a b) c = mul a (mul b c)
       mul_one : ∀ a, mul a one = a
       ...
```

---

## Arquitectura del Sistema

El sistema NLE v7.0 está basado en **Memory Evolutive Systems** (Ehresmann & Vanbremeersch, 2007) y consta de 4 subsistemas principales:

```
┌─────────────────────────────────────────────────────────────────┐
│                    NÚCLEO LÓGICO EVOLUTIVO v7.0                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Usuario ──> Claude AI ──> Agente RL ──> Lean 4 (verificación) │
│                                │                                │
│                                v                                │
│              ┌─────────────────────────────────┐                │
│              │  GRAFO CATEGÓRICO DE SKILLS     │                │
│              │                                 │                │
│              │  61 skills matemáticos:         │                │
│              │  - 10 fundamentales (nivel 0)   │                │
│              │  - 51 de dominio (niveles 1-2)  │                │
│              │                                 │                │
│              │  4 Pilares:                     │                │
│              │  SET | CAT | LOG | TYPE         │                │
│              └─────────────────────────────────┘                │
│                                │                                │
│                                v                                │
│              ┌─────────────────────────────────┐                │
│              │  RED DE CO-REGULADORES (MES)    │                │
│              │                                 │                │
│              │  • CR_tac: Táctico (rápido)     │                │
│              │  • CR_org: Organizacional       │                │
│              │  • CR_str: Estratégico          │                │
│              │  • CR_int: Integridad           │                │
│              │                                 │                │
│              │  Memoria: Empírica → Semántica  │                │
│              └─────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

### Los 4 Pilares del Conocimiento

| Pilar | Qué es | Ejemplos |
|-------|--------|----------|
| **SET** | Teoría de Conjuntos (ZFC) | Axiomas ZFC, ordinales, cardinales |
| **CAT** | Teoría de Categorías | Funtores, transformaciones naturales, límites |
| **LOG** | Lógica (FOL + Intuicionista) | Deducción natural, metateoría, completitud |
| **TYPE** | Teoría de Tipos (CIC/Lean 4) | Cálculo de construcciones, Lean 4 kernel |

### Los 61 Skills Matemáticos

El sistema tiene conocimiento estructurado de 61 habilidades matemáticas organizadas en 12 categorías:

| Categoría | Skills (Nivel 1) | Skills (Nivel 2) |
|-----------|------------------|------------------|
| **Álgebra** (7) | Teoría de grupos, anillos, campos, álgebra lineal | Álgebra conmutativa, homológica |
| **Geometría** (6) | Euclidiana, diferencial, proyectiva | Algebraica, Riemanniana, simpléctica |
| **Análisis** (6) | Real, complejo, teoría de la medida | Funcional, armónico, EDPs |
| **Topología** (5) | Topología de puntos, algebraica | Diferencial, homotopía, nudos |
| **Lógica** (3) | Teoría de modelos | Teoría de la demostración, HoTT |
| **Teoría de Números** (4) | Elemental, algebraica | Analítica, geometría aritmética |
| **Combinatoria** (6) | Enumerativa, grafos, matroides | Extremal, aditiva, optimización |
| **Probabilidad** (4) | Teoría de probabilidad, procesos estocásticos | Teoría ergódica, cálculo estocástico |
| **Teoría de Conjuntos** (1) | Teoría descriptiva de conjuntos | |
| **Teoría de Categorías** (2) | Topos | Álgebra homológica categórica |
| **Computación** (4) | Análisis de algoritmos, lenguajes formales | Complejidad, teoría de tipos avanzada |
| **Optimización** (3) | Optimización convexa | Métodos variacionales, control óptimo |

---

## Instalación

### Requisitos Previos

- **Python 3.10 o superior**
- **Cuenta de Anthropic** (para usar Claude AI)
- *(Opcional)* Lean 4 instalado para verificación formal

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/metamatematico/Demostrador-de-enunciados-matem-ticos.git
cd Demostrador-de-enunciados-matem-ticos
```

### Paso 2: Instalar dependencias

```bash
pip install pyyaml rich anthropic
```

**Dependencias:**
- `pyyaml`: Configuración del sistema
- `rich`: Interfaz de terminal con colores y formato
- `anthropic`: Cliente oficial de Claude AI

### Paso 3: Configurar API key de Anthropic

Necesitas una API key de Anthropic (https://console.anthropic.com):

**Windows CMD:**
```cmd
set ANTHROPIC_API_KEY=sk-ant-tu-clave-aqui
```

**Windows PowerShell:**
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-tu-clave-aqui"
```

**Linux/Mac:**
```bash
export ANTHROPIC_API_KEY=sk-ant-tu-clave-aqui
```

### Paso 4: Verificar instalación

```bash
python -c "from nucleo.core import Nucleo; print('Instalación correcta')"
```

Si ves `Instalación correcta`, todo está listo.

---

## Uso del Sistema

### Chat Interactivo con Claude

El modo más sencillo de usar el sistema es el chat interactivo:

```bash
python -m nucleo chat
```

Esto abrirá una sesión interactiva:

```
┌─────────────────────────────────┐
│ NLE v7.0 — Núcleo Lógico Evolutivo │
│ Modelo: claude-sonnet-4-20250514   │
└─────────────────────────────────┘
Inicializando sistema...
Listo. 61 skills cargados.

Tu >
```

### Comandos Especiales del Chat

Dentro del chat, puedes usar estos comandos:

| Comando | Función |
|---------|---------|
| `/help` | Muestra ayuda |
| `/stats` | Estadísticas del sistema (skills, memoria, agente RL) |
| `/skills` | Lista los 61 skills matemáticos por pilar |
| `/axioms` | Verifica los axiomas formales del sistema (8.1-8.4) |
| `/clear` | Limpia el historial de conversación |
| `/quit` | Salir del chat |

### Opciones del Chat

```bash
# Usar modelo más rápido y económico
python -m nucleo chat --model claude-haiku-4-5-20251001

# Modo verbose (ver decisiones del agente RL)
python -m nucleo chat --verbose
```

### Ejemplos de Consultas

**Definiciones básicas:**
```
Tu > ¿Qué es un espacio vectorial?
Tu > Define un anillo conmutativo
Tu > Explica el teorema fundamental del álgebra
```

**Demostraciones:**
```
Tu > Demuestra que todo grupo de orden primo es cíclico
Tu > Prueba que la raíz de 2 es irracional
Tu > Demuestra el teorema de Lagrange para grupos
```

**Formalización en Lean 4:**
```
Tu > Formaliza la definición de grupo en Lean 4
Tu > Escribe en Lean el teorema de isomorfismo
Tu > Cómo se define un espacio métrico en Lean?
```

---

## Uso Programático (Python)

También puedes usar el sistema directamente desde código Python:

```python
import asyncio
from nucleo.core import Nucleo
from nucleo.config import NucleoConfig

async def main():
    # Configurar
    config = NucleoConfig()
    config.llm.model = "claude-haiku-4-5-20251001"

    # Inicializar
    nucleo = Nucleo(config=config)
    await nucleo.initialize()

    # Poner en modo evaluación (no entrenamiento)
    nucleo.agent.eval_mode()

    # Hacer consulta
    response = await nucleo.process("¿Qué es un grupo abeliano?")

    print(f"Acción: {response.action_type.name}")
    print(f"Confianza: {response.confidence:.2f}")
    print(f"Respuesta:\n{response.content}")

asyncio.run(main())
```

### Estadísticas del Sistema

```python
stats = nucleo.stats
print(f"Skills cargados: {stats['num_skills']}")
print(f"Niveles jerárquicos: {stats['num_levels']}")
print(f"Pilares activos: {stats['num_pillars']}")
```

---

## Estructura del Proyecto

```
Demostrador-de-enunciados-matematicos/
│
├── nucleo/                      # Sistema NLE v7.0 (~12,800 líneas)
│   ├── core.py                  #   Orquestador principal
│   ├── cli.py                   #   Interfaz de línea de comandos
│   ├── __main__.py              #   Entry point: python -m nucleo
│   ├── types.py                 #   Tipos: Skill, Morphism, Pattern, etc.
│   ├── config.py                #   Configuración
│   │
│   ├── graph/                   #   Grafo categórico de skills
│   │   ├── category.py          #     Categoría jerárquica + axiomas
│   │   ├── evolution.py         #     Sistema evolutivo + teoremas
│   │   ├── operations.py        #     Operaciones sobre el grafo
│   │   └── embeddings.py        #     Embeddings de skills
│   │
│   ├── mes/                     #   Memory Evolutive Systems
│   │   ├── co_regulators.py     #     4 co-reguladores
│   │   ├── memory.py            #     Memoria con E-equivalencia
│   │   └── patterns.py          #     Patrones, colímites
│   │
│   ├── lean/                    #   Integración con Lean 4
│   │   ├── client.py            #     Cliente Lean 4
│   │   ├── solver_cascade.py    #     9 solvers automáticos
│   │   ├── sorry_analyzer.py    #     Análisis de sorry's
│   │   └── ...
│   │
│   ├── rl/                      #   Aprendizaje por Refuerzo
│   │   ├── agent.py             #     Agente RL (epsilon-greedy)
│   │   ├── mdp.py               #     Proceso de decisión de Markov
│   │   └── rewards.py           #     Función de recompensa
│   │
│   ├── pillars/                 #   4 Pilares + 51 dominios
│   │   ├── set_theory.py        #     ZFC
│   │   ├── category_theory.py   #     Teoría de Categorías
│   │   ├── logic.py             #     Lógica (FOL + IL)
│   │   ├── type_theory.py       #     Teoría de Tipos (CIC/Lean)
│   │   └── math_domains.py      #     51 dominios matemáticos
│   │
│   ├── llm/                     #   Integración con Claude
│   │   ├── client.py            #     Cliente API de Anthropic
│   │   └── prompts.py           #     Plantillas de prompts
│   │
│   └── eval/                    #   Evaluación
│       └── math_evaluator.py    #     Verificación de respuestas
│
├── tests/                       #   284 tests (13 suites)
│   ├── test_graph.py
│   ├── test_evolution.py
│   ├── test_colimits.py
│   ├── test_memory.py
│   ├── test_lean_integration.py
│   └── ...
│
├── examples/                    #   Ejemplos de uso
│   ├── basic_usage.py
│   ├── complete_flow.py
│   └── lean_integration.py
│
├── nucleo_config.yaml           #   Configuración por defecto
├── pyproject.toml               #   Metadata del proyecto
├── LICENSE                      #   Licencia MIT
└── README.md                    #   Este archivo
```

---

## Conceptos Técnicos Avanzados

### 1. Categoría Jerárquica de Skills

Los skills están organizados en una jerarquía categórica con 5 niveles:

```
Nivel 4+: Meta-skills (traducciones inter-pilar)
    │
Nivel 3:  Competencias (verificación en Lean)
    │
Nivel 2:  Habilidades (inducción matemática, Curry-Howard)
    │
Nivel 1:  Clusters (ZFC-axioms, FOL-rules, Type-rules)
    │
Nivel 0:  Átomos (axioma de extensionalidad, modus ponens)
```

**Morfismos entre skills:**
- `DEPENDENCY`: skill A necesita skill B
- `TRANSLATION`: traducción entre pilares (ej: Curry-Howard: FOL → TYPE)
- `ANALOGY`: analogía estructural (ej: conjuntos como categorías)

### 2. Red de Co-Reguladores (MES)

Cuatro co-reguladores operan a diferentes escalas temporales:

| Co-Regulador | Nivel | Frecuencia | Función |
|--------------|-------|------------|---------|
| **CR_tac** | 0-1 | Cada paso | Seleccionar tácticas, responder |
| **CR_org** | 1-2 | Cada 10 pasos | Reorganizar grafo, crear puentes |
| **CR_str** | 2-3 | Cada 100 pasos | Crear colímites, nuevos niveles |
| **CR_int** | Todos | Periódico | Verificar axiomas, reparar |

### 3. Patrones y Colímites

Un **patrón** es un grupo de skills que trabajan juntos. Su **colímite** es un nuevo skill que los integra:

```python
from nucleo.mes.patterns import PatternManager, ColimitBuilder

pm = PatternManager()
pattern = pm.create_pattern(
    component_ids=["group-theory", "ring-theory", "field-theory"],
    distinguished_links=["morph_1", "morph_2"],
    graph=cat
)

cb = ColimitBuilder(pm)
new_skill, colimit = cb.build_colimit(pattern, cat)
# new_skill está en nivel max(component_levels) + 1
```

### 4. Sistema Evolutivo

El sistema evoluciona mediante **complexificación** (Opciones con absorciones, eliminaciones, enlaces):

```python
from nucleo.graph.evolution import EvolutionarySystem
from nucleo.types import Option, Skill

evo = EvolutionarySystem(cat)

# Aplicar evolución
option = Option(absorptions=[
    Skill(id="topology", name="Topology", pillar=PillarType.SET, level=1)
])
functor = evo.apply_option(option)

# Verificar teoremas después de evolución
result = evo.verify_all_theorems()
assert result["8.5_consistency"]["satisfies"]   # Axiomas preservados
assert result["8.6_emergence"]["satisfies"]     # Complejidad crece
```

### 5. Propiedades Formales Verificadas

El sistema verifica formalmente:

**Axiomas (en SkillCategory):**
- **8.1 Jerarquía**: >= 2 niveles jerárquicos
- **8.2 Multiplicidad**: >= 2 pilares con traducciones inter-pilar
- **8.3 Conectividad**: Débilmente conexo + conexiones inter-pilar
- **8.4 Cobertura**: Todo skill alcanzable desde un skill de pilar

**Teoremas (en EvolutionarySystem):**
- **8.5 Consistencia**: Complexificación preserva axiomas
- **8.6 Emergencia**: Complejidad crece o se estabiliza
- **8.7 Preservación de Cobertura**: Cobertura se mantiene bajo evolución

### 6. Memoria con E-equivalencia

Cuatro tipos de memoria:

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| **Empírica** | Experiencias concretas | "Usé `simp` para resolver x + 0 = x" |
| **Procedural** | Secuencias exitosas | "Para ∀, usar `intro` y luego `apply`" |
| **Semántica** | E-conceptos abstractos | "Inducción es útil para ℕ" |
| **Consolidada** | Conocimiento reforzado | Skills usados 3+ veces |

---

## Tests

El sistema incluye 284 tests que verifican todas las funcionalidades:

```bash
python -m pytest tests/ -v
```

| Suite | Tests | Qué prueba |
|-------|-------|------------|
| test_types | 10 | Tipos básicos (Skill, Morphism, State, Action) |
| test_graph | 12 | Categoría de skills, axiomas, serialización |
| test_pillars | 16 | 4 pilares fundamentales |
| test_evolution | 10 | Snapshots, funtores de transición |
| test_colimits | 26 | Patrones, co-conos, propiedad universal |
| test_emergence | 14 | Links simples/complejos, emergencia |
| test_multiplicity | 10 | Homología, multiplicidad |
| test_coregulators | 19 | Red de co-reguladores |
| test_memory | 16 | E-equivalencia, E-conceptos |
| test_lean_integration | 48 | Cascade de solvers, analizador de sorry's |
| test_formal_properties | 26 | Axiomas 8.1-8.4, Teoremas 8.5-8.7 |
| test_math_domains | 32 | 51 dominios matemáticos |
| test_cli | 10 | CLI, chat interactivo |
| **Total** | **284** | |

---

## Preguntas Frecuentes (FAQ)

### ¿Necesito saber programación para usar el sistema?

**No.** El sistema tiene un chat interactivo muy simple:
```bash
python -m nucleo chat
```
Solo escribe tus preguntas en español y el sistema responde.

### ¿Cuánto cuesta usar Claude AI?

Depende del modelo:
- **claude-haiku-4-5-20251001**: ~$0.25 por millón de tokens (muy barato)
- **claude-sonnet-4-20250514**: ~$3 por millón de tokens (calidad alta)

Una sesión típica de chat (10-20 preguntas) cuesta menos de $0.10 USD.

### ¿Qué tipo de matemáticas entiende el sistema?

El sistema cubre 61 dominios matemáticos:
- Álgebra (grupos, anillos, campos, álgebra lineal)
- Análisis (real, complejo, funcional)
- Topología (punto-conjunto, algebraica, diferencial)
- Geometría (euclidiana, diferencial, algebraica)
- Lógica (teoría de modelos, teoría de la demostración)
- Teoría de números (elemental, algebraica, analítica)
- Y más...

### ¿Puede generar demostraciones formales verificables?

**Sí**, pero con limitaciones:
- Genera código Lean 4 sintácticamente correcto
- Para verificar formalmente necesitas Lean 4 instalado
- Las demostraciones generadas pueden requerir ajustes manuales

### ¿El sistema aprende de mis consultas?

**Parcialmente**:
- Durante una sesión, el sistema recuerda el contexto
- La memoria se reinicia al cerrar el chat
- **Futuro**: Memoria persistente entre sesiones

### ¿Funciona sin conexión a Internet?

**No**, porque necesita Claude AI de Anthropic, que es un servicio en la nube.

### ¿Puedo usar otro LLM en lugar de Claude?

Actualmente solo funciona con Claude. Soporte para otros LLMs (GPT-4, Gemini) está planeado.

---

## Solución de Problemas

### Error: "ANTHROPIC_API_KEY not found"

**Solución:**
```bash
# Windows CMD
set ANTHROPIC_API_KEY=sk-ant-tu-clave

# PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-tu-clave"

# Linux/Mac
export ANTHROPIC_API_KEY=sk-ant-tu-clave
```

### Error: "Your credit balance is too low"

**Solución:** Tu cuenta de Anthropic no tiene créditos. Ve a https://console.anthropic.com → Plans & Billing → agrega créditos (mínimo $5 USD).

### Error: "No module named 'nucleo'"

**Solución:** Asegúrate de estar en la carpeta correcta:
```bash
cd Demostrador-de-enunciados-matematicos
python -m nucleo chat
```

### El chat muestra caracteres raros (�)

**Solución:** Problema de encoding en Windows. El sistema usa UTF-8 automáticamente, pero si persiste:
```cmd
chcp 65001
python -m nucleo chat
```

### Los tests fallan

**Solución:**
```bash
# Instalar pytest si no lo tienes
pip install pytest

# Correr tests con configuración correcta
python -m pytest tests/ -o "addopts=" -v
```

---

## Desarrollo y Contribuciones

### Estado del Proyecto

| Fase | Descripción | Estado |
|------|-------------|--------|
| 0 | Bugfixes críticos | ✅ Completado |
| 1 | Colímites y propiedad universal | ✅ Completado |
| 2 | Sistema evolutivo | ✅ Completado |
| 3 | Emergencia | ✅ Completado |
| 4 | Multiplicidad | ✅ Completado |
| 5 | Co-reguladores + Memoria | ✅ Completado |
| 6 | Integración Lean | ✅ Completado |
| 7 | Propiedades formales | ✅ Completado |

**Progreso global: ~88%**

### Trabajo Pendiente

- [ ] Red neuronal (PPO policy, GNN embeddings)
- [ ] Dataset de entrenamiento
- [ ] Pipeline de evaluación end-to-end
- [ ] Memoria persistente entre sesiones
- [ ] Soporte para otros LLMs (GPT-4, Gemini)

### Cómo Contribuir

1. Haz fork del repositorio
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Haz tus cambios y tests
4. Asegúrate que los 284 tests pasen: `pytest tests/`
5. Haz commit: `git commit -m "feat: descripción"`
6. Push: `git push origin feature/nueva-funcionalidad`
7. Abre un Pull Request

---

## Referencias

### Fundamentos Teóricos

**Memory Evolutive Systems (MES):**
- Ehresmann, A. C., & Vanbremeersch, J. P. (2007). *Memory Evolutive Systems: Hierarchy, Emergence, Cognition*. Elsevier.
- Ehresmann, A. C. (2012). MENS, a mathematical model for cognitive systems. *Journal of Mind Theory*, 0(2).

**Solver Cascade (APOLLO):**
- Wang et al. (2025). APOLLO: Automated LLM and Lean Collaboration for Mathematical Reasoning. *arXiv:2505.05758*.

**Lean 4 y Mathlib:**
- [Mathlib4 Documentation](https://leanprover-community.github.io/mathlib4_docs/)
- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)

### Teoría de Categorías

- Mac Lane, S. (1978). *Categories for the Working Mathematician*. Springer.
- Awodey, S. (2010). *Category Theory*. Oxford University Press.

---

## Autor

**Leonardo Jiménez Martínez**
Universidad Nacional Autónoma de México (UNAM)

---

## Licencia

MIT License. Ver [LICENSE](LICENSE) para detalles.

---

## Agradecimientos

- **Anthropic** por Claude AI
- **Lean Community** por Mathlib4
- **Andrée Ehresmann** por la teoría MES
