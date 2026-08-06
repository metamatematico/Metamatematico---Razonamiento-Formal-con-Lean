"""
Script para subir el modelo Metamatematico a HuggingFace Hub.
Uso: python scripts/upload_to_hf.py --token <HF_TOKEN>
"""

import argparse
import json
import sys
import os
import shutil
import tempfile
from pathlib import Path

REPO_ID = "metamatematico/Metamatematico"

MODEL_CARD = """---
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
- gat
pipeline_tag: text-classification
---

# Metamatematico — NLE v7.0

**Actor-Critic GNN con PPO para routing de problemas matemáticos y generación de pruebas Lean 4.**

Desarrollado por Leonardo Jiménez Martínez (UNAM) como parte del **Núcleo Lógico Evolutivo (NLE) v7.0**,
un sistema de IA matemática basado en Memory Evolutive Systems (Ehresmann).

## Arquitectura

El modelo combina tres encoders fusionados:

| Componente | Descripción |
|---|---|
| **SkillGNN** | 3 capas GATConv con edge features (dim 6), hidden=256, heads=4 |
| **QueryEncoder** | Bag-of-keywords → MLP 2 capas, hidden=256 |
| **GoalEncoder** | Hash determinístico de goal Lean → MLP 2 capas, hidden=256 |
| **Fusion** | Concat(3×256) → Linear → ReLU → LayerNorm |
| **Actor** | Linear → ReLU → Linear(3 acciones) |
| **Critic** | Linear → ReLU → Linear(1) |

**Parámetros totales**: ~546K  |  **Tamaño**: ~2.2 MB

### Acciones
- `0 — ASSIST`: Rutear al pipeline Lean (formalizar → verificar → traducir)
- `1 — RESPONSE`: Responder directamente con Claude
- `2 — SEARCH`: Buscar en memoria de patrones matemáticos

## Entrenamiento

### Fase 1 — Supervisado (routing)
- **Dataset**: 71,663 ejemplos (MATH + GSM8K + NuminaMath + ProofNet)
  - Train: 52,237 | Val: 6,552 | Test: 12,874
- **Épocas**: 15 | **GPU**: RTX 3050 Laptop (4.3 GB VRAM)
- **Resultado**: train_acc=100%, val_acc=100%, test_acc=100% (converge en época 1)

### Fase 2 — PPO con verificación Lean real
- **5 épocas** PPO con oracle `lake env lean + Mathlib`
- **avg_reward ≈ 0.57** (~70% aritmética → 1.0, ~30% álgebra abstracta → 0.5)
- **ppo_loss**: 0.0746 → 0.0172 (convergencia confirmada)
- **assist_pct = 100%** (todos los problemas matemáticos → pipeline Lean)

## Uso

```python
import torch
from huggingface_hub import hf_hub_download

# Descargar pesos
weights_path = hf_hub_download(
    repo_id="metamatematico/Metamatematico",
    filename="neural_agent.pt"
)

# Cargar config
import json
config_path = hf_hub_download(
    repo_id="metamatematico/Metamatematico",
    filename="config.json"
)
with open(config_path) as f:
    config = json.load(f)

# Instanciar modelo (requiere torch + torch-geometric)
# Ver nucleo/rl/networks.py para la clase ActorCriticNetwork
checkpoint = torch.load(weights_path, map_location="cpu")
print("Claves del checkpoint:", list(checkpoint.keys()))
```

## Contexto del Sistema NLE

Este modelo es el componente de decisión del **NLE v7.0**:

```
Query → _is_mathematical() → NucleoAgent.select_action()
    ├── ProceduralMemory (lookup por similitud)
    ├── SkillGNN + ActorCriticNetwork (si use_neural=True)
    └── Acción → pipeline Lean / respuesta Claude / búsqueda
```

El grafo de skills tiene **76 habilidades matemáticas** (10 L0 + 66 L1-L2) en 14 categorías,
representado como una categoría delgada (thin category / preorden) verificada formalmente en Lean 4.

## Archivos en este repositorio

| Archivo | Descripción |
|---|---|
| `neural_agent.pt` | Pesos del modelo (última versión con PPO Lean) |
| `best.pt` | Mejor checkpoint (val_acc=1.0, epoch 15) |
| `config.json` | Hiperparámetros de arquitectura |
| `training_log.json` | Log completo del entrenamiento |
| `gnn.py` | Arquitectura SkillGNN (GATConv) |
| `networks.py` | ActorCriticNetwork completo |
| `agent.py` | NucleoAgent (PPO + ProceduralMemory) |

## Cita

```
@software{nle_v7_2026,
  author = {Jiménez Martínez, Leonardo},
  title  = {NLE v7.0: Núcleo Lógico Evolutivo — Actor-Critic GNN para razonamiento matemático formal},
  year   = {2026},
  url    = {https://huggingface.co/metamatematico/Metamatematico}
}
```

## Licencia

MIT — ver LICENSE en el repositorio fuente.
"""

CONFIG = {
    "model_type": "ActorCriticGNN",
    "architecture": {
        "hidden_dim": 256,
        "gnn_num_layers": 3,
        "gnn_num_heads": 4,
        "gnn_dropout": 0.1,
        "num_actions": 3,
        "goal_dim": 32,
        "node_feature_dim": 9,
        "edge_feature_dim": 6
    },
    "vocab": [
        "theorem", "proof", "lemma", "lean", "sorry", "tactic",
        "prove", "formalize", "induction", "simp", "exact", "apply",
        "set", "function", "group", "ring", "category", "functor",
        "natural", "transformation", "limit", "colimit", "morphism",
        "define", "what", "how", "explain", "compute", "calculate",
        "help", "show", "verify", "check"
    ],
    "actions": {
        "0": "ASSIST",
        "1": "RESPONSE",
        "2": "SEARCH"
    },
    "training": {
        "phase1_epochs": 15,
        "phase1_dataset_size": 71663,
        "phase1_train_acc": 1.0,
        "phase1_val_acc": 1.0,
        "phase1_test_acc": 1.0,
        "phase2_ppo_epochs": 5,
        "phase2_avg_reward": 0.577,
        "phase2_ppo_loss_final": 0.0172,
        "phase2_assist_pct": 1.0
    },
    "framework": "NLE v7.0",
    "author": "Leonardo Jiménez Martínez (UNAM)",
    "total_params_approx": 546000
}


def main():
    parser = argparse.ArgumentParser(description="Sube el modelo Metamatematico a HuggingFace Hub")
    parser.add_argument("--token", required=True, help="Token de acceso de HuggingFace (write)")
    parser.add_argument("--private", action="store_true", default=False, help="Repositorio privado")
    args = parser.parse_args()

    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        print("ERROR: huggingface_hub no instalado. Ejecuta: pip install huggingface_hub")
        sys.exit(1)

    api = HfApi(token=args.token)

    # Verificar token
    try:
        user = api.whoami()
        print(f"Autenticado como: {user['name']}")
    except Exception as e:
        print(f"ERROR de autenticacion: {e}")
        sys.exit(1)

    # Crear repositorio si no existe
    print(f"\nCreando/verificando repositorio: {REPO_ID}")
    try:
        create_repo(
            repo_id=REPO_ID,
            repo_type="model",
            private=args.private,
            exist_ok=True,
            token=args.token,
        )
        print(f"Repositorio listo: https://huggingface.co/{REPO_ID}")
    except Exception as e:
        print(f"ERROR creando repositorio: {e}")
        sys.exit(1)

    # Rutas de archivos
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    checkpoints_dir = Path("E:/chechkpointsmetamatematico")
    data_dir = project_root / "data"
    rl_dir = project_root / "nucleo" / "rl"

    files_to_upload = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # 1. Model card
        readme = tmp / "README.md"
        readme.write_text(MODEL_CARD, encoding="utf-8")
        files_to_upload.append((str(readme), "README.md"))

        # 2. Config
        config_file = tmp / "config.json"
        config_file.write_text(json.dumps(CONFIG, indent=2, ensure_ascii=False), encoding="utf-8")
        files_to_upload.append((str(config_file), "config.json"))

        # 3. Pesos principales
        weights = data_dir / "neural_agent.json.pt"
        if weights.exists():
            files_to_upload.append((str(weights), "neural_agent.pt"))
        else:
            print(f"ADVERTENCIA: No encontrado {weights}")

        # 4. Best checkpoint
        best = checkpoints_dir / "best.pt"
        if best.exists():
            files_to_upload.append((str(best), "best.pt"))
        else:
            print(f"ADVERTENCIA: No encontrado {best}")

        # 5. Training log
        log = checkpoints_dir / "training_log.json"
        if log.exists():
            files_to_upload.append((str(log), "training_log.json"))

        # 6. Código fuente de arquitectura
        for fname in ["gnn.py", "networks.py", "agent.py"]:
            src = rl_dir / fname
            if src.exists():
                files_to_upload.append((str(src), f"src/{fname}"))
            else:
                print(f"ADVERTENCIA: No encontrado {src}")

        # Subir todos los archivos
        print(f"\nSubiendo {len(files_to_upload)} archivos a {REPO_ID}...")
        for local_path, repo_path in files_to_upload:
            size_mb = Path(local_path).stat().st_size / 1024 / 1024
            print(f"  [{size_mb:.2f} MB] {repo_path} ...", end=" ", flush=True)
            try:
                api.upload_file(
                    path_or_fileobj=local_path,
                    path_in_repo=repo_path,
                    repo_id=REPO_ID,
                    repo_type="model",
                    token=args.token,
                    commit_message=f"Upload {repo_path}",
                )
                print("OK")
            except Exception as e:
                print(f"ERROR: {e}")

    print(f"\nSubida completa.")
    print(f"Repositorio: https://huggingface.co/{REPO_ID}")


if __name__ == "__main__":
    main()
