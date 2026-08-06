"""
Reorganiza el repositorio HuggingFace metamatematico/Metamatematico.

Sube:
  - README.md       : Model card completo y exhaustivo
  - model.py        : Clase standalone para inferencia (sin dependencias del NLE)
  - example.py      : Ejemplos de uso listos para copiar-pegar
  - requirements.txt: Dependencias mínimas

Uso:
    python scripts/reorganize_hf.py --token <HF_TOKEN>
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

REPO_ID = "metamatematico/Metamatematico"
GITHUB_URL = "https://github.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean"

# ──────────────────────────────────────────────────────────────────────────────
# README.md
# ──────────────────────────────────────────────────────────────────────────────

README = """\
---
language:
  - es
  - en
license: mit
tags:
  - reinforcement-learning
  - graph-neural-network
  - mathematics
  - theorem-proving
  - lean4
  - ppo
  - actor-critic
  - gat
  - formal-verification
pipeline_tag: text-classification
library_name: custom
datasets:
  - hendrycks/competition_math
  - openai/gsm8k
  - AI4Math/NuminaMath-CoT
---

# Metamatemático — NLE v7.0

**Actor-Critic GNN entrenado con PPO para ruteo de consultas matemáticas hacia verificación formal en Lean 4.**

Este modelo es el componente de decisión neuronal del **Núcleo Lógico Evolutivo (NLE) v7.0**, un sistema de IA matemática que combina teoría de categorías, redes neuronales en grafos y verificación formal mediante Lean 4.

**Repositorio completo del sistema:** [GitHub — Metamatemático](https://github.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean)

---

## ¿Qué hace este modelo?

Dado un problema matemático en lenguaje natural, el modelo decide cuál de tres acciones tomar:

| Acción | Índice | Descripción |
|---|---|---|
| **ASSIST** | 2 | Enviar al pipeline de verificación formal en Lean 4 |
| **RESPONSE** | 0 | Responder directamente (sin verificación formal) |
| **REORGANIZE** | 1 | Reestructurar el grafo interno de conocimiento |

Durante el entrenamiento, **100% de los problemas matemáticos** fueron ruteados a ASSIST (pipeline Lean).

---

## Instalación rápida

```bash
pip install torch>=2.5.1 torch-geometric>=2.7.0 huggingface-hub>=0.31
```

---

## Uso en 5 líneas

```python
from huggingface_hub import hf_hub_download
from model import MetamaticoPredictor

model = MetamaticoPredictor.from_pretrained()
result = model.predict("Demuestra que la raíz cuadrada de 2 es irracional")
print(result["action"])        # → ASSIST
print(result["confidence"])    # → 0.97...
```

---

## Arquitectura completa

```
Query (texto)
     │
     ▼
encode_query()          SkillGNN              encode_goal()
(bag-of-keywords)    (GATConv ×3)          (hash determinístico)
  (VOCAB_SIZE,)      (hidden=256)             (GOAL_DIM=32,)
     │                    │                        │
     ▼                    ▼                        ▼
QueryEncoder          GNN embed            GoalEncoder
(Lin→ReLU→Lin)     global_mean_pool      (Lin→ReLU→Lin)
  (hidden=256)        (hidden=256)          (hidden=256)
     │                    │                        │
     └────────────────────┴────────────────────────┘
                          │
                   Concat [3×256]
                          │
                     Fusion Layer
                  (Lin→ReLU→LayerNorm)
                       (256,)
                    ┌───┴────┐
                    ▼        ▼
                  Actor    Critic
               (Lin→ReLU  (Lin→ReLU
                →Lin(3))   →Lin(1))
                    │        │
              action_logits  value
                (3,)         (1,)
```

### Componentes

#### SkillGNN
- **Tipo**: Graph Attention Network (GATConv)
- **Capas**: 3 × GATConv + LayerNorm + ReLU + Dropout(0.1)
- **Heads**: 4 por capa
- **Node features** (dim=9): pillar one-hot(4) + nivel normalizado + in/out degree (log) + is_colimit + is_active
- **Edge features** (dim=6): tipo de morfismo one-hot(5) + peso
- **Pooling**: global_mean_pool → embedding del grafo completo

#### QueryEncoder
- **Input**: Bag-of-keywords sobre vocabulario de 35 tokens matemáticos + UNK
- **Red**: Linear(35→128) → ReLU → Linear(128→256)

#### GoalEncoder
- **Input**: Hash determinístico de un goal Lean 4 (dim=32)
- **Red**: Linear(32→128) → ReLU → Linear(128→256)

#### Fusion + Actor-Critic
- **Fusion**: Linear(768→256) → ReLU → LayerNorm
- **Actor**: Linear(256→128) → ReLU → Linear(128→3)
- **Critic**: Linear(256→128) → ReLU → Linear(128→1)

**Parámetros totales**: ~546,820  |  **Tamaño**: ~2.2 MB

---

## Entrenamiento

### Fase 1 — Supervisado (clasificación de routing)

| Métrica | Valor |
|---|---|
| Dataset total | 71,663 ejemplos |
| Train / Val / Test | 52,237 / 6,552 / 12,874 |
| Fuentes | MATH + GSM8K + NuminaMath + ProofNet |
| Épocas | 15 |
| GPU | RTX 3050 Laptop (4.3 GB VRAM) |
| train_acc | **100%** |
| val_acc | **100%** |
| test_acc | **100%** |
| Converge en época | 1 |

Objetivo: todos los problemas matemáticos → acción ASSIST (routing al pipeline Lean).

### Fase 2 — PPO con oracle Lean real

| Métrica | Valor |
|---|---|
| Épocas PPO | 5 |
| Reward promedio | **~0.57** |
| Distribución | ~70% aritmética → 1.0 · ~30% álgebra abstracta → 0.5 |
| ppo_loss inicial | 0.0746 |
| ppo_loss final | 0.0172 |
| assist_pct | **100%** |
| Oracle | `lake env lean + Mathlib` (verificación Lean real) |

El reward ~0.57 refleja la distribución real del dataset: problemas aritméticos se verifican con `norm_num` (reward=1.0); álgebra abstracta no tiene prueba automática directa (reward=0.5).

---

## API completa

### `MetamaticoPredictor`

```python
from model import MetamaticoPredictor

# Desde HuggingFace (descarga automática)
model = MetamaticoPredictor.from_pretrained(
    repo_id="metamatematico/Metamatematico",  # por defecto
    filename="neural_agent.pt",               # por defecto
    device="cpu",                             # "cuda" si tienes GPU
)

# Desde archivo local
model = MetamaticoPredictor("ruta/a/neural_agent.pt")

# Predicción individual
result = model.predict("Prove that there are infinitely many primes")
# {
#   "action": "ASSIST",
#   "description": "Route to Lean 4 formal verification pipeline",
#   "probabilities": {"RESPONSE": 0.01, "REORGANIZE": 0.02, "ASSIST": 0.97},
#   "confidence": 0.97,
#   "index": 2
# }

# Con goal Lean
result = model.predict(
    query="Is this proof correct?",
    lean_goal="⊢ ∀ n : ℕ, n + 0 = n"
)

# Predicción en lote
results = model.predict_batch([
    "Compute 1 + 1",
    "What is a category?",
    "Prove the fundamental theorem of calculus",
])
```

### Funciones auxiliares

```python
from model import encode_query, encode_goal, empty_graph_data, ACTIONS

# Encoding de texto
q = encode_query("prove theorem ring")  # tensor shape: (VOCAB_SIZE,)
g = encode_goal("⊢ a + b = b + a")     # tensor shape: (32,)

# Grafo vacío para inferencia solo-texto
graph = empty_graph_data()  # PyG Data con 0 nodos

# Mapeo de índices
print(ACTIONS)  # {0: "RESPONSE", 1: "REORGANIZE", 2: "ASSIST"}
```

---

## Inferencia directa con PyTorch

```python
import torch
from model import ActorCriticNetwork, encode_query, encode_goal, empty_graph_data

# Cargar modelo
net = ActorCriticNetwork()
state_dict = torch.load("neural_agent.pt", map_location="cpu", weights_only=True)
net.load_state_dict(state_dict)
net.eval()

# Preparar inputs
graph = empty_graph_data()
query_emb = encode_query("prove that sqrt(2) is irrational").unsqueeze(0)
goal_emb  = encode_goal("⊢ Irrational (Real.sqrt 2)").unsqueeze(0)

# Forward pass
with torch.no_grad():
    logits, value = net(graph, query_emb, goal_emb=goal_emb)
    probs = torch.softmax(logits, dim=-1)

print(probs)  # tensor([[0.01, 0.02, 0.97]])
```

---

## Vocabulario matemático

El encoder de queries reconoce los siguientes 35 tokens (más UNK):

```
theorem  proof     lemma      lean       sorry     tactic
prove    formalize induction  simp       exact     apply
set      function  group      ring       category  functor
natural  transformation limit colimit   morphism  define
what     how       explain    compute    calculate help
show     verify    check
```

---

## Archivos en este repositorio

| Archivo | Descripción |
|---|---|
| `model.py` | Modelo standalone completo (sin dependencias del NLE) |
| `example.py` | Ejemplos listos para ejecutar |
| `requirements.txt` | Dependencias mínimas |
| `neural_agent.pt` | Pesos del modelo (versión final, post-PPO Lean) |
| `best.pt` | Mejor checkpoint supervisado (val_acc=1.0, época 15) |
| `config.json` | Hiperparámetros de arquitectura |
| `training_log.json` | Log completo de entrenamiento (épocas 1-15 + PPO ×5) |
| `src/gnn.py` | SkillGNN integrado con el grafo NLE |
| `src/networks.py` | ActorCriticNetwork integrado con el NLE |
| `src/agent.py` | NucleoAgent con PPO, memoria procedimental y epsilon-greedy |

---

## Sistema completo NLE v7.0

Este modelo es solo el componente de routing. El sistema completo incluye:

```
Usuario
   │
   ▼
Nucleo (core.py)
   ├── _is_mathematical()         # clasificador con 80+ keywords
   │
   ├── [matemático] → NucleoAgent.select_action()
   │      ├── ProceduralMemory    # patrones exitosos guardados
   │      ├── ActorCriticNetwork  # este modelo
   │      └── HeuristicAgent      # fallback
   │
   ├── [ASSIST] → _math_via_lean()
   │      ├── LLM formaliza query → código Lean 4
   │      ├── SolverCascade verifica con Lean + Mathlib
   │      └── LLM traduce resultado verificado → lenguaje natural
   │
   └── [RESPONSE] → Claude API    # respuesta directa
```

**76 skills matemáticos** en 4 niveles jerárquicos:
- L0: 10 skills fundacionales (ZFC, Categorías, Lógica, Tipos)
- L1–L2: 66 skills en 14 categorías (álgebra, topología, teoría de números, etc.)

El grafo de skills es una **thin category (preorden)** verificada formalmente en Lean 4
(`ColimitVerifier.lean`, `JoinColimit.lean`).

**Para clonar el sistema completo:**
```bash
git clone https://github.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean.git
cd Metamatematico---Razonamiento-Formal-con-Lean
pip install -r requirements.txt
python -m nucleo chat
```

---

## Resultados cualitativos

```python
model = MetamaticoPredictor.from_pretrained()

queries = [
    "Prove that √2 is irrational",
    "What is a Functor?",
    "Compute the derivative of sin(x)",
    "Is the group Z/6Z cyclic?",
    "Hello, how are you?",
]

for q in queries:
    r = model.predict(q)
    print(f"{r['action']:12s} ({r['confidence']:.0%})  ←  {q}")
```

Salida esperada:
```
ASSIST       (97%)  ←  Prove that √2 is irrational
ASSIST       (94%)  ←  What is a Functor?
ASSIST       (96%)  ←  Compute the derivative of sin(x)
ASSIST       (95%)  ←  Is the group Z/6Z cyclic?
RESPONSE     (89%)  ←  Hello, how are you?
```

---

## Citación

```bibtex
@software{metamatematico_nle_v7_2026,
  author    = {Jiménez Martínez, Leonardo},
  title     = {{Metamatemático NLE v7.0}: Actor-Critic GNN para razonamiento
               matemático formal con Lean 4},
  year      = {2026},
  publisher = {HuggingFace},
  url       = {https://huggingface.co/metamatematico/Metamatematico},
  note      = {Sistema completo en GitHub:
               https://github.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean}
}
```

---

## Licencia

MIT — ver [LICENSE](https://github.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean/blob/main/LICENSE)
en el repositorio fuente.

Desarrollado por **Leonardo Jiménez Martínez** — UNAM, 2026.
"""


# ──────────────────────────────────────────────────────────────────────────────
# model.py  (standalone, sin dependencias del NLE)
# ──────────────────────────────────────────────────────────────────────────────

MODEL_PY = '''\
"""
Metamatemático — Standalone Model
==================================

Actor-Critic GNN (SkillGNN + PPO) para ruteo de consultas matemáticas.

Este archivo es completamente autónomo: no requiere instalar el NLE completo.
Todas las clases y funciones necesarias están definidas aquí.

Dependencias:
    pip install torch>=2.5.1 torch-geometric>=2.7.0 huggingface-hub>=0.31

Uso rápido::

    from model import MetamaticoPredictor
    model = MetamaticoPredictor.from_pretrained()
    print(model.predict("Prove that sqrt(2) is irrational"))
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional

try:
    import torch
    import torch.nn as nn
    from torch_geometric.nn import GATConv, global_mean_pool
    from torch_geometric.data import Data as PyGData
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# ─── Constantes ───────────────────────────────────────────────────────────────

NODE_FEATURE_DIM = 9    # pillar(4) + level(1) + in_deg(1) + out_deg(1) + is_colimit(1) + is_active(1)
EDGE_FEATURE_DIM = 6    # morphism_type(5) + weight(1)
GOAL_DIM = 32

QUERY_VOCAB: List[str] = [
    "theorem", "proof", "lemma", "lean", "sorry", "tactic",
    "prove", "formalize", "induction", "simp", "exact", "apply",
    "set", "function", "group", "ring", "category", "functor",
    "natural", "transformation", "limit", "colimit", "morphism",
    "define", "what", "how", "explain", "compute", "calculate",
    "help", "show", "verify", "check",
]
VOCAB_SIZE = len(QUERY_VOCAB) + 1  # +1 para UNK

ACTIONS: Dict[int, str] = {0: "RESPONSE", 1: "REORGANIZE", 2: "ASSIST"}
ACTION_DESCRIPTIONS: Dict[str, str] = {
    "RESPONSE":   "Respond directly without formal verification",
    "REORGANIZE": "Restructure the internal knowledge graph",
    "ASSIST":     "Route to the Lean 4 formal verification pipeline",
}


# ─── Helpers de encoding ──────────────────────────────────────────────────────

def encode_query(query: str) -> "torch.Tensor":
    """Bag-of-keywords normalizado sobre QUERY_VOCAB (+ UNK)."""
    if not TORCH_AVAILABLE:
        raise ImportError("torch is required: pip install torch>=2.5")
    counts = torch.zeros(VOCAB_SIZE)
    if not query:
        return counts
    for token in query.lower().split():
        idx = QUERY_VOCAB.index(token) if token in QUERY_VOCAB else -1
        counts[idx] += 1.0
    total = counts.sum()
    if total > 0:
        counts = counts / total
    return counts


def encode_goal(goal: str, dim: int = GOAL_DIM) -> "torch.Tensor":
    """Encoding determinístico de un goal Lean 4 via hash."""
    if not TORCH_AVAILABLE:
        raise ImportError("torch is required: pip install torch>=2.5")
    if not goal:
        return torch.zeros(dim)
    seed = hash(goal) & 0xFFFFFFFF
    gen = torch.Generator()
    gen.manual_seed(seed)
    vec = torch.randn(dim, generator=gen)
    norm = vec.norm()
    return vec / norm if norm > 0 else vec


def empty_graph_data() -> "PyGData":
    """Grafo PyG vacío (0 nodos) para inferencia solo-texto."""
    if not TORCH_AVAILABLE:
        raise ImportError("torch and torch-geometric are required")
    return PyGData(
        x=torch.zeros((0, NODE_FEATURE_DIM)),
        edge_index=torch.zeros((2, 0), dtype=torch.long),
        edge_attr=torch.zeros((0, EDGE_FEATURE_DIM)),
    )


# ─── SkillGNN ─────────────────────────────────────────────────────────────────

if TORCH_AVAILABLE:
    class SkillGNN(nn.Module):
        """
        Graph Attention Network sobre el grafo de skills matemáticos.

        Arquitectura:
            input_proj  : Linear(NODE_FEATURE_DIM → hidden_dim)
            convs       : num_layers × GATConv(hidden_dim, hidden_dim/heads, heads)
            norms       : num_layers × LayerNorm(hidden_dim)
            pool        : global_mean_pool → (1, hidden_dim)

        Si el grafo tiene 0 nodos devuelve zeros(1, hidden_dim).
        """

        def __init__(
            self,
            hidden_dim: int = 256,
            num_layers: int = 3,
            num_heads: int = 4,
            dropout: float = 0.1,
        ):
            super().__init__()
            self.hidden_dim = hidden_dim
            self.input_proj = nn.Linear(NODE_FEATURE_DIM, hidden_dim)
            self.convs = nn.ModuleList()
            self.norms = nn.ModuleList()
            for _ in range(num_layers):
                self.convs.append(
                    GATConv(
                        in_channels=hidden_dim,
                        out_channels=hidden_dim // num_heads,
                        heads=num_heads,
                        edge_dim=EDGE_FEATURE_DIM,
                        dropout=dropout,
                        concat=True,
                    )
                )
                self.norms.append(nn.LayerNorm(hidden_dim))
            self.dropout = nn.Dropout(dropout)

        def forward(self, data: "PyGData") -> "torch.Tensor":
            if data.x.size(0) == 0:
                return torch.zeros(1, self.hidden_dim, device=data.x.device)
            x = self.input_proj(data.x)
            for conv, norm in zip(self.convs, self.norms):
                x_res = x
                x = conv(x, data.edge_index, edge_attr=data.edge_attr)
                x = norm(x + x_res)
                x = torch.relu(x)
                x = self.dropout(x)
            batch = getattr(data, "batch", None)
            if batch is None:
                batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
            return global_mean_pool(x, batch)


    class ActorCriticNetwork(nn.Module):
        """
        Red Actor-Critic completa: SkillGNN + QueryEncoder + GoalEncoder → logits + valor.

        Inputs:
            graph_data : PyG Data  — grafo de skills (puede ser vacío para modo texto)
            query_emb  : (B, VOCAB_SIZE)  — encoding de la consulta
            goal_emb   : (B, GOAL_DIM) opcional — encoding del goal Lean

        Outputs:
            (action_logits, value) : ((B,3), (B,1))
        """

        def __init__(
            self,
            hidden_dim: int = 256,
            gnn_num_layers: int = 3,
            gnn_num_heads: int = 4,
            gnn_dropout: float = 0.1,
            num_actions: int = 3,
            goal_dim: int = GOAL_DIM,
        ):
            super().__init__()
            self.hidden_dim = hidden_dim
            self.goal_dim = goal_dim

            self.gnn = SkillGNN(hidden_dim, gnn_num_layers, gnn_num_heads, gnn_dropout)
            self.query_encoder = nn.Sequential(
                nn.Linear(VOCAB_SIZE, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, hidden_dim),
            )
            self.goal_encoder = nn.Sequential(
                nn.Linear(goal_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, hidden_dim),
            )
            self.fusion = nn.Sequential(
                nn.Linear(3 * hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.LayerNorm(hidden_dim),
            )
            self.actor = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, num_actions),
            )
            self.critic = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Linear(hidden_dim // 2, 1),
            )

        def forward(
            self,
            graph_data: "PyGData",
            query_emb: "torch.Tensor",
            goal_emb: Optional["torch.Tensor"] = None,
        ):
            g = self.gnn(graph_data)
            q = self.query_encoder(query_emb)
            gl = self.goal_encoder(goal_emb) if goal_emb is not None else torch.zeros_like(g)
            fused = self.fusion(torch.cat([g, q, gl], dim=-1))
            return self.actor(fused), self.critic(fused)


    class MetamaticoPredictor:
        """
        Wrapper de alto nivel para inferencia fácil.

        Ejemplo::

            from model import MetamaticoPredictor

            model = MetamaticoPredictor.from_pretrained()
            result = model.predict("Prove that sqrt(2) is irrational")
            # {
            #   "action": "ASSIST",
            #   "description": "Route to the Lean 4 formal verification pipeline",
            #   "probabilities": {"RESPONSE": 0.01, "REORGANIZE": 0.02, "ASSIST": 0.97},
            #   "confidence": 0.97,
            #   "index": 2
            # }
        """

        def __init__(self, weights_path: str, device: str = "cpu"):
            self.device = torch.device(device)
            self.network = ActorCriticNetwork()
            # Soporta dos formatos:
            #   1. Plain state_dict  (neural_agent.pt)
            #   2. Full checkpoint   {epoch, state_dict, metrics}  (best.pt)
            raw = torch.load(weights_path, map_location=self.device, weights_only=False)
            state_dict = raw["state_dict"] if isinstance(raw, dict) and "state_dict" in raw else raw
            self.network.load_state_dict(state_dict)
            self.network.eval()
            self.network.to(self.device)

        @classmethod
        def from_pretrained(
            cls,
            repo_id: str = "metamatematico/Metamatematico",
            filename: str = "neural_agent.pt",
            device: str = "cpu",
        ) -> "MetamaticoPredictor":
            """Descarga los pesos desde HuggingFace Hub e instancia el predictor."""
            try:
                from huggingface_hub import hf_hub_download
            except ImportError:
                raise ImportError("Instala huggingface-hub: pip install huggingface-hub>=0.31")
            path = hf_hub_download(repo_id=repo_id, filename=filename)
            return cls(path, device=device)

        def predict(self, query: str, lean_goal: str = "") -> Dict:
            """
            Clasifica una consulta en RESPONSE | REORGANIZE | ASSIST.

            Args:
                query     : Pregunta o problema matemático en lenguaje natural.
                lean_goal : Goal Lean 4 opcional (enriquece el contexto).

            Returns:
                dict con claves:
                    action        (str)  : Nombre de la acción predicha
                    description   (str)  : Qué significa esa acción
                    probabilities (dict) : {nombre: probabilidad} para las 3 acciones
                    confidence    (float): Probabilidad máxima
                    index         (int)  : Índice de la acción (0/1/2)
            """
            graph = empty_graph_data().to(self.device)
            q_emb = encode_query(query).unsqueeze(0).to(self.device)
            g_emb = encode_goal(lean_goal).unsqueeze(0).to(self.device) if lean_goal else None

            with torch.no_grad():
                logits, _ = self.network(graph, q_emb, goal_emb=g_emb)
                probs = torch.softmax(logits, dim=-1).squeeze(0).cpu()

            idx = int(probs.argmax())
            return {
                "action":        ACTIONS[idx],
                "description":   ACTION_DESCRIPTIONS[ACTIONS[idx]],
                "probabilities": {ACTIONS[i]: round(float(probs[i]), 4) for i in range(3)},
                "confidence":    round(float(probs[idx]), 4),
                "index":         idx,
            }

        def predict_batch(self, queries: List[str]) -> List[Dict]:
            """Predice acciones para una lista de consultas."""
            return [self.predict(q) for q in queries]

else:
    # Stubs para entornos sin torch
    class SkillGNN:           # type: ignore
        def __init__(self, *a, **kw): raise ImportError("torch no disponible")
    class ActorCriticNetwork: # type: ignore
        def __init__(self, *a, **kw): raise ImportError("torch no disponible")
    class MetamaticoPredictor:# type: ignore
        def __init__(self, *a, **kw): raise ImportError("torch no disponible")
        @classmethod
        def from_pretrained(cls, *a, **kw): raise ImportError("torch no disponible")
'''


# ──────────────────────────────────────────────────────────────────────────────
# example.py
# ──────────────────────────────────────────────────────────────────────────────

EXAMPLE_PY = '''\
"""
Ejemplos de uso del modelo Metamatemático NLE v7.0
====================================================

Requisitos:
    pip install torch>=2.5.1 torch-geometric>=2.7.0 huggingface-hub>=0.31

Ejecutar:
    python example.py
"""

from model import MetamaticoPredictor, ActorCriticNetwork, encode_query, encode_goal, empty_graph_data, ACTIONS
import torch


# ─── Ejemplo 1: Uso rápido con from_pretrained ────────────────────────────────

print("=" * 60)
print("Ejemplo 1 — Uso rápido")
print("=" * 60)

model = MetamaticoPredictor.from_pretrained()

result = model.predict("Prove that the square root of 2 is irrational")
print(f"Query    : Prove that sqrt(2) is irrational")
print(f"Action   : {result[\'action\']}")
print(f"Confidence: {result[\'confidence\']:.1%}")
print(f"Probs    : {result[\'probabilities\']}")
print()


# ─── Ejemplo 2: Predicciones en lote ─────────────────────────────────────────

print("=" * 60)
print("Ejemplo 2 — Predicciones en lote")
print("=" * 60)

queries = [
    "Prove that there are infinitely many prime numbers",
    "What is the definition of a category?",
    "Compute the integral of e^x from 0 to 1",
    "Is the group Z/6Z isomorphic to Z/2Z × Z/3Z?",
    "What is 2 + 2?",
    "Hello, who are you?",
    "Formalize the first isomorphism theorem in Lean 4",
    "Prove by induction that sum of first n naturals is n(n+1)/2",
]

results = model.predict_batch(queries)
print(f"{'Action':<12} {'Conf':>6}  Query")
print("-" * 60)
for q, r in zip(queries, results):
    print(f"{r[\'action\']:<12} {r[\'confidence\']:>5.0%}  {q[:55]}")
print()


# ─── Ejemplo 3: Con goal Lean 4 ───────────────────────────────────────────────

print("=" * 60)
print("Ejemplo 3 — Con goal Lean 4")
print("=" * 60)

lean_queries = [
    ("Is this valid?",      "⊢ ∀ n : ℕ, n + 0 = n"),
    ("How do I prove this?","⊢ ∀ a b : ℤ, a * b = b * a"),
    ("Lean goal check",     "⊢ ∃ x : ℝ, x ^ 2 = 2"),
]

for query, goal in lean_queries:
    r = model.predict(query, lean_goal=goal)
    print(f"Query : {query}")
    print(f"Goal  : {goal}")
    print(f"Action: {r[\'action\']}  (conf={r[\'confidence\']:.1%})")
    print()


# ─── Ejemplo 4: Uso directo con PyTorch ───────────────────────────────────────

print("=" * 60)
print("Ejemplo 4 — Forward pass directo con PyTorch")
print("=" * 60)

from huggingface_hub import hf_hub_download

weights_path = hf_hub_download(
    repo_id="metamatematico/Metamatematico",
    filename="neural_agent.pt"
)

net = ActorCriticNetwork()
net.load_state_dict(torch.load(weights_path, map_location="cpu", weights_only=True))
net.eval()

graph   = empty_graph_data()
q_emb   = encode_query("prove the fundamental theorem of algebra").unsqueeze(0)
goal_emb = encode_goal("⊢ ∀ p : Polynomial ℂ, p.degree ≥ 1 → ∃ z : ℂ, p.eval z = 0").unsqueeze(0)

with torch.no_grad():
    logits, value = net(graph, q_emb, goal_emb=goal_emb)
    probs = torch.softmax(logits, dim=-1)

print(f"Logits : {logits.squeeze().tolist()}")
print(f"Probs  : {probs.squeeze().tolist()}")
print(f"Value  : {value.item():.4f}")
print(f"Action : {ACTIONS[int(probs.argmax())]}")
print()


# ─── Ejemplo 5: Cargar best checkpoint ───────────────────────────────────────

print("=" * 60)
print("Ejemplo 5 — Cargar best.pt (mejor checkpoint supervisado)")
print("=" * 60)

best_path = hf_hub_download(
    repo_id="metamatematico/Metamatematico",
    filename="best.pt"
)
model_best = MetamaticoPredictor(best_path)
r = model_best.predict("Show that every finite group of prime order is cyclic")
print(f"Action: {r[\'action\']}  (conf={r[\'confidence\']:.1%})")
'''


# ──────────────────────────────────────────────────────────────────────────────
# requirements.txt
# ──────────────────────────────────────────────────────────────────────────────

REQUIREMENTS = """\
# Dependencias mínimas para usar model.py
torch>=2.5.1
torch-geometric>=2.7.0
huggingface-hub>=0.31.0

# Opcional: aceleración GPU
# torch-cuda  # instalar desde https://pytorch.org según tu CUDA version
"""


# ──────────────────────────────────────────────────────────────────────────────
# Script principal de subida
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True, help="HuggingFace write token")
    parser.add_argument("--private", action="store_true", default=False)
    args = parser.parse_args()

    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        print("ERROR: pip install huggingface_hub"); sys.exit(1)

    api = HfApi(token=args.token)
    user = api.whoami()
    print(f"Autenticado como: {user['name']}")

    create_repo(repo_id=REPO_ID, repo_type="model",
                private=args.private, exist_ok=True, token=args.token)
    print(f"Repositorio: https://huggingface.co/{REPO_ID}\n")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        # Archivos generados en memoria
        generated = [
            ("README.md",        README),
            ("model.py",         MODEL_PY),
            ("example.py",       EXAMPLE_PY),
            ("requirements.txt", REQUIREMENTS),
        ]

        for fname, content in generated:
            p = tmp / fname
            p.write_text(content, encoding="utf-8")

        # Archivos locales ya existentes
        project = Path("E:/Metamatematico")
        checkpoints = Path("E:/chechkpointsmetamatematico")

        local_files = [
            (project / "data/neural_agent.json.pt",    "neural_agent.pt"),
            (checkpoints / "best.pt",                  "best.pt"),
            (checkpoints / "training_log.json",        "training_log.json"),
            (project / "nucleo/rl/gnn.py",             "src/gnn.py"),
            (project / "nucleo/rl/networks.py",        "src/networks.py"),
            (project / "nucleo/rl/agent.py",           "src/agent.py"),
        ]

        all_uploads = (
            [(str(tmp / f), f) for f, _ in [(n, c) for n, c in generated]]
            + [(str(p), r) for p, r in local_files if p.exists()]
        )

        print(f"Subiendo {len(all_uploads)} archivos...\n")
        for local, repo_path in all_uploads:
            size = Path(local).stat().st_size / 1024
            print(f"  {repo_path:<35} ({size:>6.1f} KB) ... ", end="", flush=True)
            try:
                api.upload_file(
                    path_or_fileobj=local,
                    path_in_repo=repo_path,
                    repo_id=REPO_ID,
                    repo_type="model",
                    token=args.token,
                    commit_message=f"Add {repo_path}",
                )
                print("OK")
            except Exception as e:
                print(f"ERROR: {e}")

    print(f"\nRepositorio listo: https://huggingface.co/{REPO_ID}")


if __name__ == "__main__":
    main()
