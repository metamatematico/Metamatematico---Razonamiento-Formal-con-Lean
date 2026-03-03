# METAMATEMÁTICO
#Demostrador de Enunciados Matemáticos

**METAMATEMATICO NLE v7.0 — Evolutionary Logical Core**

> Sistema de razonamiento matemático formal basado en *Memory Evolutive Systems* (Ehresmann).
> Demuestra teoremas, explica conceptos y genera código Lean 4 a partir de lenguaje natural.

---

**Autor:** Leonardo Jiménez Martínez
**Institución:** BIOMAT 
**Año:** 2025

---

## ¿Qué es este sistema?

NLE v7.0 es un asistente matemático que combina:

- **76 skills matemáticos** organizados en un grafo categórico jerárquico (álgebra, análisis, topología, lógica, teoría de tipos...)
- **Razonamiento formal** mediante co-reguladores tácticos inspirados en los *Memory Evolutive Systems* de Ehresmann
- **Generación de pruebas Lean 4** con cascada de tácticas (`rfl → simp → ring → linarith → omega → aesop`)
- **Aprendizaje por refuerzo** (GNN + PPO) que mejora la selección de tácticas con cada interacción
- **Visualización** del grafo de skills, embeddings semánticos, arquitectura y traza de prueba

Está diseñado para estudiantes e investigadores de matemáticas que quieran explorar la formalización automática de enunciados.

---

## Instalación local (3 pasos)

Cada usuario corre el sistema en **su propia computadora**. No se necesita servidor externo.

### Requisitos previos
- Python 3.9 o superior
- `pip` actualizado

### Paso 1 — Clona el repositorio

```bash
git clone https://github.com/metamatematico/Demostrador-de-enunciados-matem-ticos.git
cd Demostrador-de-enunciados-matem-ticos
```

### Paso 2 — Instala las dependencias

```bash
pip install -r requirements.txt
```

### Paso 3 — Ejecuta el sistema

```bash
streamlit run app.py
```

Se abrirá automáticamente en tu navegador en `http://localhost:8501`

---

## Primeros pasos en la app

### Sin API key (modo demo)
Selecciona **"Demo (sin API key)"** en el panel lateral y prueba directamente.

### Con modelo real (respuestas completas)
Obtén una clave gratuita en alguno de estos proveedores:

| Proveedor | Modelo recomendado | Dónde obtener la key |
|-----------|-------------------|----------------------|
| **Google AI Studio** | `gemini-2.0-flash` | [aistudio.google.com](https://aistudio.google.com) — sin tarjeta |
| **Groq** | `llama-3.3-70b-versatile` | [console.groq.com](https://console.groq.com) — sin tarjeta |
| **Anthropic** | `claude-haiku-4-5` | [console.anthropic.com](https://console.anthropic.com) |

Introduce tu key en el **panel lateral izquierdo** de la app. No se almacena en ningún servidor.

---

## Qué puedes hacer

### 🧮 Pestaña: Demostrador
Escribe cualquier problema o enunciado matemático en lenguaje natural:

```
Demuestra que √2 es irracional
Explica el Lema de Yoneda
example (n : Nat) : n + 0 = n := by ?
¿Qué es la correspondencia Curry-Howard?
```

El sistema clasifica el dominio matemático, enriquece el contexto y genera una respuesta estructurada con notación formal y código Lean 4 cuando es pertinente.

### 📊 Pestaña: Visualizaciones

| Tab | Descripción |
|-----|-------------|
| ⬡ **Grafo de Skills** | Los 76 skills como grafo dirigido, coloreado por dominio matemático |
| ◎ **Espacio de Embeddings** | Proyección t-SNE / PCA de los vectores semánticos de cada skill |
| ⚙ **Arquitectura NLE** | Diagrama de bloques del sistema completo |
| ◈ **Complexificación MES** | Cómo emergen nuevos skills mediante colímites categoriales |
| → **Pipeline** | Flujo de una consulta desde el texto hasta la respuesta |
| ⊛ **GNN + Estadísticas** | Red neuronal de atención (GATConv × 3) y parámetros del agente PPO |
| 🔍 **Traza de Prueba** | Subred de skills activada específicamente para tu teorema |

---

## Estructura del repositorio

```
.
├── app.py                    # Aplicación principal Streamlit
├── pages/
│   └── 1_Visualizaciones.py  # Página de visualizaciones (7 tabs)
├── .streamlit/
│   └── config.toml           # Tema oscuro y configuración del servidor
├── requirements.txt          # Dependencias Python
└── README.md
```

---

## Arquitectura del sistema

```
Consulta (lenguaje natural)
        │
        ▼
   CR_tac — Co-regulador táctico (MES)
   ┌──────┴──────┐
   │             │
RESPONDER    ASISTIR
   │             │
   ▼             ▼
Grafo de    GoalAnalyzer
Skills      (ordena tácticas)
   │             │
   └──────┬──────┘
          │
          ▼
         LLM  ←──── Cascada Lean 4
          │         rfl → simp → ring
          │         linarith → omega → aesop
          ▼
      Respuesta
          │
          ▼
     GNN + PPO  (aprende de cada interacción)
     Memoria procedimental (guarda patrones exitosos)
```

**Base teórica:** Axiomas 8.1–8.4 y Teoremas 8.5–8.7 del paper NLE v7.0 (BIOMAT–UNAM, 2025).
**Verificación formal:** 379 tests automatizados.

---

## Fundamento matemático

El sistema organiza el conocimiento matemático como una **categoría K** donde:

- Los **objetos** son skills matemáticos (ZFC, grupos, análisis, tácticas Lean...)
- Los **morfismos** son relaciones de dependencia, traducción y analogía entre skills
- Los **colímites** modelan la emergencia de nuevos skills a partir de patrones existentes (complexificación)
- Los **co-reguladores** (CR_tac, CR_mem, CR_neuro) controlan qué acción tomar ante cada consulta

Este formalismo está inspirado en los *Memory Evolutive Systems* de Andrée Ehresmann.

---

*BIOMAT — Centro de Biomatemáticas · 2025*
*Leonardo Jiménez Martínez*
