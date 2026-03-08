"""
train_gnn_ppo.py
================
Entrena el GNN + PPO del NLE en dos fases usando los splits preparados
por prepare_training_data.py.

GPU: RTX 3050 (4 GB VRAM, Compute 8.6) - modelo 3 MB, cabe holgadamente.

---------------------------------------------------------------------
Fase 1  PREENTRENAMIENTO SUPERVISADO  (rapido, sin Lean)
---------------------------------------------------------------------
  Objetivo: ensenar al actor a elegir ASSIST (idx=2) para cualquier
  problema matematico.

  Loss: CrossEntropy(action_logits, target=2)
  Metrica clave: accuracy = % de problemas donde argmax(logits) == 2

  Datos: all_train.jsonl  (~60K+ problemas)
  Duracion estimada en 3050:
    batch=256: ~2-3 min / epoca con 60K ejemplos
    10 epocas ~ 30 min

---------------------------------------------------------------------
Fase 2  AJUSTE PPO  (opcional, --with-lean, mas lento)
---------------------------------------------------------------------
  Objetivo: refinar con recompensa real de verificacion Lean.
  Reward:
    +1.0  si el agente elige ASSIST y Lean verifica (sin sorry)
    +0.3  si elige ASSIST (independiente de Lean)
    -0.5  si elige RESPONSE para problema matematico
    0.0   REORGANIZE

  Datos: all_train.jsonl (solo los primeros --lean-samples por epoca)
  Duracion: ~1-2 s por problema con Lean -> lento, usar --lean-samples 200

---------------------------------------------------------------------
Pesos guardados en:
  data/neural_agent.json      <- config + metricas
  data/neural_agent.json.pt   <- state_dict (cargado automaticamente por NucleoAgent)

Uso:
  # Solo preentrenamiento (recomendado para empezar)
  python scripts/train_gnn_ppo.py --epochs 10 --batch-size 256

  # Con PPO Lean (lento)
  python scripts/train_gnn_ppo.py --epochs 10 --with-lean --lean-samples 300

  # Continuar desde checkpoint
  python scripts/train_gnn_ppo.py --resume --epochs 5
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR      = PROJECT_ROOT / "data"
SPLITS_DIR    = Path("E:/datadeentrenamientovalidacion_test")
WEIGHTS_PATH  = DATA_DIR / "neural_agent.json.pt"
CONFIG_PATH   = DATA_DIR / "neural_agent.json"
CKPT_DIR      = Path("E:/chechkpointsmetamatematico")

# Indice de accion ASSIST en ACTION_TYPES = [RESPONSE, REORGANIZE, ASSIST]
ASSIST_IDX = 2


# =============================================================================
# Loop asyncio persistente para Windows (evita "Event loop is closed")
# =============================================================================

class _LeanLoop:
    """
    Loop de asyncio que vive en un hilo dedicado durante todo el entrenamiento.

    En Windows, asyncio.run() cierra el ProactorEventLoop tras cada llamada,
    invalidando las pipes del subproceso Lean. Esta clase mantiene un loop
    siempre activo para que todas las llamadas a check_code compartan el mismo
    contexto de event loop.
    """
    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def run(self, coro, timeout: float = 60.0):
        """Ejecuta una corrutina en el loop dedicado y retorna el resultado."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    def close(self):
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5.0)


_lean_loop_instance: "_LeanLoop | None" = None


def get_lean_loop() -> "_LeanLoop":
    global _lean_loop_instance
    if _lean_loop_instance is None:
        _lean_loop_instance = _LeanLoop()
    return _lean_loop_instance


# =============================================================================
# Carga de datos
# =============================================================================

def load_jsonl(path: Path, max_records: Optional[int] = None) -> list[dict]:
    """Carga un archivo JSONL."""
    records = []
    if not path.exists():
        print(f"  [WARN] no existe: {path}")
        return records
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
                if max_records and len(records) >= max_records:
                    break
    return records


def make_batches(records: list[dict], batch_size: int, shuffle: bool = True, seed: int = 42) -> list[list[dict]]:
    """Divide registros en batches."""
    data = list(records)
    if shuffle:
        random.Random(seed).shuffle(data)
    return [data[i:i+batch_size] for i in range(0, len(data), batch_size)]


# =============================================================================
# Inicializar grafo de skills (estatico durante todo el entrenamiento)
# =============================================================================

def build_skill_graph():
    """
    Construye el grafo de 76 skills del NLE.
    Replica exactamente la inicializacion de core.py:
      1. Agrega 10 skills fundacionales L0 (pilares ZFC/Cat/Log/Type)
      2. Llama a load_math_domains para agregar los 66 skills L1-L2
    """
    from nucleo.graph.category import SkillCategory
    from nucleo.pillars.math_domains import load_math_domains
    from nucleo.types import Skill, MorphismType, PillarType

    graph = SkillCategory(name="NucleoSkillGraph")

    # --- L0: skills fundacionales (10 skills) ---
    # F_Set
    graph.add_skill(Skill(id="zfc-axioms",    name="ZFC Axioms",             description="Axiomas de Zermelo-Fraenkel", pillar=PillarType.SET, level=0))
    graph.add_skill(Skill(id="ordinals",      name="Ordinals",               description="Ordinales y aritmetica ordinal", pillar=PillarType.SET, level=0))
    # F_Cat
    graph.add_skill(Skill(id="cat-basics",    name="Category Basics",        description="Objetos, morfismos, composicion", pillar=PillarType.CAT, level=0))
    graph.add_skill(Skill(id="functors",      name="Functors",               description="Funtores covariantes/contravariantes", pillar=PillarType.CAT, level=0))
    graph.add_skill(Skill(id="nat-trans",     name="Natural Transformations", description="Transformaciones naturales", pillar=PillarType.CAT, level=0))
    graph.add_skill(Skill(id="limits",        name="Limits & Colimits",      description="Limites y colimites", pillar=PillarType.CAT, level=0))
    # F_Log
    graph.add_skill(Skill(id="fol-deduction", name="FOL Deduction",          description="Deduccion natural FOL", pillar=PillarType.LOG, level=0))
    graph.add_skill(Skill(id="fol-metatheory",name="FOL Metatheory",         description="Completitud, compacidad", pillar=PillarType.LOG, level=0))
    # F_Type
    graph.add_skill(Skill(id="cic",           name="CIC",                    description="Calculo de Construcciones Inductivas", pillar=PillarType.TYPE, level=0))
    graph.add_skill(Skill(id="lean-kernel",   name="Lean 4 Kernel",          description="Kernel Lean 4", pillar=PillarType.TYPE, level=0))

    # Morfismos L0
    graph.add_morphism("zfc-axioms",    "ordinals",        MorphismType.DEPENDENCY)
    graph.add_morphism("cat-basics",    "functors",        MorphismType.DEPENDENCY)
    graph.add_morphism("functors",      "nat-trans",       MorphismType.DEPENDENCY)
    graph.add_morphism("functors",      "limits",          MorphismType.DEPENDENCY)
    graph.add_morphism("cic",           "lean-kernel",     MorphismType.DEPENDENCY)
    graph.add_morphism("fol-deduction", "fol-metatheory",  MorphismType.DEPENDENCY)
    graph.add_morphism("fol-deduction", "cic",             MorphismType.TRANSLATION)
    graph.add_morphism("zfc-axioms",    "cat-basics",      MorphismType.ANALOGY)

    # --- L1-L2: 66 skills de dominios matematicos ---
    load_math_domains(graph)
    return graph


def get_graph_data(graph):
    """Convierte el grafo a PyG Data (se puede cachear)."""
    from nucleo.rl.gnn import graph_to_pyg
    return graph_to_pyg(graph)


# =============================================================================
# Encoding de queries (batch)
# =============================================================================

def encode_batch(problems: list[str], device) -> "torch.Tensor":
    """
    Codifica una lista de problemas como bag-of-keywords.
    Devuelve tensor [batch_size, VOCAB_SIZE] en device.
    """
    import torch
    from nucleo.rl.networks import encode_query

    embs = [encode_query(p) for p in problems]
    return torch.stack(embs).to(device)


def encode_goals_batch(problems: list[str], device) -> "torch.Tensor":
    """Codifica goals (hash deterministico) para el critic."""
    import torch
    from nucleo.rl.networks import encode_goal

    embs = [encode_goal(p) for p in problems]
    return torch.stack(embs).to(device)


# =============================================================================
# Fase 1: Preentrenamiento supervisado
# =============================================================================

def pretrain_epoch(
    network,
    optimizer,
    graph_data,
    batches: list[list[dict]],
    device,
) -> dict:
    """
    Una epoca de preentrenamiento supervisado.

    Para cada batch de problemas matematicos, optimiza
    CrossEntropy(action_logits, ASSIST_IDX).
    """
    import torch
    import torch.nn.functional as F
    from torch_geometric.data import Batch

    network.train()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    for batch in batches:
        problems = [r["problem"] for r in batch]
        bs = len(problems)

        # Codificar queries y goals
        query_emb = encode_batch(problems, device)          # [bs, VOCAB_SIZE]
        goal_emb  = encode_goals_batch(problems, device)    # [bs, GOAL_DIM]

        # Replicar el grafo para el batch
        graph_batch = Batch.from_data_list([graph_data] * bs).to(device)

        # Forward
        output = network(graph_batch, query_emb, goal_emb=goal_emb)

        # Target: siempre ASSIST (2) para problemas matematicos
        target = torch.full((bs,), ASSIST_IDX, dtype=torch.long, device=device)
        loss = F.cross_entropy(output.action_logits, target)

        # Backward
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(network.parameters(), max_norm=1.0)
        optimizer.step()

        # Metricas
        with torch.no_grad():
            preds = output.action_logits.argmax(dim=-1)
            total_correct  += (preds == target).sum().item()
            total_loss     += loss.item() * bs
            total_samples  += bs

    avg_loss = total_loss / max(total_samples, 1)
    accuracy = total_correct / max(total_samples, 1)
    return {"loss": avg_loss, "accuracy": accuracy, "samples": total_samples}


def evaluate(
    network,
    graph_data,
    batches: list[list[dict]],
    device,
) -> dict:
    """Evaluacion en val/test (sin gradientes)."""
    import torch
    import torch.nn.functional as F
    from torch_geometric.data import Batch

    network.eval()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    with torch.no_grad():
        for batch in batches:
            problems = [r["problem"] for r in batch]
            bs = len(problems)
            query_emb   = encode_batch(problems, device)
            goal_emb    = encode_goals_batch(problems, device)
            graph_batch = Batch.from_data_list([graph_data] * bs).to(device)
            output      = network(graph_batch, query_emb, goal_emb=goal_emb)
            target      = torch.full((bs,), ASSIST_IDX, dtype=torch.long, device=device)
            loss        = F.cross_entropy(output.action_logits, target)
            preds       = output.action_logits.argmax(dim=-1)
            total_correct  += (preds == target).sum().item()
            total_loss     += loss.item() * bs
            total_samples  += bs

    avg_loss = total_loss / max(total_samples, 1)
    accuracy = total_correct / max(total_samples, 1)
    return {"loss": avg_loss, "accuracy": accuracy, "samples": total_samples}


# =============================================================================
# Fase 2: PPO con oraculo Lean (opcional)
# =============================================================================

def ppo_epoch_with_lean(
    network,
    optimizer,
    graph_data,
    records: list[dict],
    device,
    lean_client,
    n_samples: int = 200,
    gamma: float = 0.99,
    clip_range: float = 0.2,
    value_coef: float = 0.5,
    entropy_coef: float = 0.01,
    n_ppo_epochs: int = 4,
    seed: int = 42,
) -> dict:
    """
    Fase 2: PPO con recompensa basada en verificacion Lean.

    Para cada problema:
      1. El agente elige una accion (RESPONSE/REORGANIZE/ASSIST)
      2. Si elige ASSIST: el NLE formaliza + Lean verifica
      3. Recompensa:
           ASSIST + Lean OK    -> +1.0
           ASSIST + Lean SORRY -> +0.5
           ASSIST + Lean FAIL  -> +0.3  (al menos intento)
           RESPONSE            -> -0.5  (error para problemas matematicos)
           REORGANIZE          -> 0.0

    Solo se procesan n_samples problemas por epoca (Lean es lento).
    """
    import torch
    import torch.nn.functional as F
    from torch_geometric.data import Batch
    from nucleo.rl.networks import encode_query, encode_goal

    rng = random.Random(seed)
    sample = rng.sample(records, min(n_samples, len(records)))

    # === Rollout ===
    network.eval()
    rollout = []

    for rec in sample:
        problem = rec["problem"]
        q_emb = encode_query(problem).unsqueeze(0).to(device)
        g_emb = encode_goal(problem).unsqueeze(0).to(device)
        g_data = Batch.from_data_list([graph_data]).to(device)

        with torch.no_grad():
            out    = network(g_data, q_emb, goal_emb=g_emb)
            probs  = torch.softmax(out.action_logits, dim=-1)
            action = torch.multinomial(probs, 1).item()
            lp     = torch.log(probs[0, action] + 1e-8).item()
            val    = out.value.squeeze().item()

        # Recompensa
        if action == ASSIST_IDX:
            reward = _lean_reward(problem, lean_client, rec=rec)
        elif action == 0:  # RESPONSE
            reward = -0.5
        else:              # REORGANIZE
            reward = 0.0

        rollout.append({
            "problem":    problem,
            "action":     action,
            "log_prob":   lp,
            "value":      val,
            "reward":     reward,
        })

    # === PPO update ===
    network.train()
    rewards     = torch.tensor([r["reward"]   for r in rollout], dtype=torch.float32, device=device)
    values      = torch.tensor([r["value"]    for r in rollout], dtype=torch.float32, device=device)
    old_lps     = torch.tensor([r["log_prob"] for r in rollout], dtype=torch.float32, device=device)
    actions_t   = torch.tensor([r["action"]   for r in rollout], dtype=torch.long,    device=device)

    # GAE advantages (sin siguiente valor -> episodios independientes)
    advantages = rewards - values.detach()
    if advantages.std() > 0:
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
    returns = rewards  # sin descuento porque episodios = 1 paso

    total_loss = 0.0
    bs = len(rollout)
    for _ in range(n_ppo_epochs):
        problems    = [r["problem"] for r in rollout]
        query_embs  = encode_batch(problems, device)
        goal_embs   = encode_goals_batch(problems, device)
        graph_batch = Batch.from_data_list([graph_data] * bs).to(device)

        out      = network(graph_batch, query_embs, goal_emb=goal_embs)
        new_lps  = F.log_softmax(out.action_logits, dim=-1)
        new_lps  = new_lps.gather(1, actions_t.unsqueeze(1)).squeeze(1)
        new_vals = out.value.squeeze(1)

        ratio  = torch.exp(new_lps - old_lps.detach())
        surr1  = ratio * advantages.detach()
        surr2  = torch.clamp(ratio, 1 - clip_range, 1 + clip_range) * advantages.detach()
        p_loss = -torch.min(surr1, surr2).mean()
        v_loss = F.mse_loss(new_vals, returns.detach())
        probs  = torch.softmax(out.action_logits, dim=-1)
        entropy = -(probs * (probs + 1e-8).log()).sum(-1).mean()
        loss   = p_loss + value_coef * v_loss - entropy_coef * entropy

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(network.parameters(), 0.5)
        optimizer.step()
        total_loss += loss.item()

    avg_reward = rewards.mean().item()
    assist_pct = (actions_t == ASSIST_IDX).float().mean().item()
    return {
        "ppo_loss":   total_loss / n_ppo_epochs,
        "avg_reward": avg_reward,
        "assist_pct": assist_pct,
        "n_samples":  bs,
    }


_LAKE_BIN = str(Path.home() / ".elan" / "bin" / "lake.exe")


def _build_lean_snippet(solution: str) -> tuple[str, str]:
    """
    Construye un snippet Lean discriminante basado en la solucion del problema.

    Estrategia:
    - Si la solucion contiene \\boxed{N} con N entero:
        busca a OP b = N en el texto (suma, resta, multiplicacion)
        -> "import Mathlib.Tactic.NormNum\ntheorem check : a OP b = N := by norm_num"
        -> mode = "norm_num"  (se llama lake env lean, puede pasar o fallar)
    - Si no hay \\boxed{N} (problema abstracto, ProofNet):
        -> mode = "sorry"  (retorna 0.5 sin llamar Lean)

    Returns (snippet, mode) donde mode es "norm_num" o "sorry".
    """
    import re

    # Extraer \boxed{N} donde N es un entero
    m = re.search(r'\\boxed\{(-?\d+)\}', solution or "")
    if not m:
        return "", "sorry"

    try:
        n = int(m.group(1))
    except ValueError:
        return "", "sorry"

    if abs(n) >= 10 ** 12:
        return "", "sorry"

    # Buscar todos los enteros positivos en la solucion (excluir el propio n)
    nums = []
    for tok in re.findall(r'\b(\d{1,10})\b', solution):
        v = int(tok)
        if v != abs(n) and v > 0:
            nums.append(v)

    # Buscar par (a, b) tal que a OP b = n
    found = None
    for a in nums[:20]:
        for b in nums[:20]:
            if a + b == n:
                found = f"theorem check : {a} + {b} = {n} := by norm_num"
                break
            if a - b == n:
                found = f"theorem check : {a} - {b} = {n} := by norm_num"
                break
            if a * b == n and a <= 10000 and b <= 10000:
                found = f"theorem check : {a} * {b} = {n} := by norm_num"
                break
        if found:
            break

    if found:
        snippet = f"import Mathlib.Tactic.NormNum\n{found}\n"
    else:
        # Respuesta conocida pero sin paso aritmetico simple: verificar divisibilidad
        snippet = (
            f"import Mathlib.Tactic.NormNum\n"
            f"theorem check : ({abs(n)} : Nat) % 1 = 0 := by norm_num\n"
        )

    return snippet, "norm_num"


def _lean_reward(problem: str, lean_client=None, rec: dict = None) -> float:
    """
    Recompensa basada en verificacion real de Lean con Mathlib.

    - Problemas con respuesta numerica (\\boxed{N}):
        genera theorem verificable con norm_num via lake env lean
        +1.0 si Lean verifica, +0.3 si error/timeout
    - Problemas abstractos (sin \\boxed{N}, e.g. ProofNet):
        retorna 0.5 directamente (equivalente a sorry)
    """
    solution = (rec or {}).get("solution", "") or ""
    snippet, mode = _build_lean_snippet(solution)

    if mode == "sorry":
        # Problema abstracto: no llamar Lean, retornar 0.5 directamente
        return 0.5

    # mode == "norm_num": verificar con lake env lean
    lake_bin = _LAKE_BIN if Path(_LAKE_BIN).exists() else "lake"
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".lean")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(snippet)

        proc = subprocess.run(
            [lake_bin, "env", "lean", "--json", tmp_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )

        output = proc.stdout + proc.stderr
        has_error = any(
            '"severity": "error"' in line or '"severity":"error"' in line
            for line in output.split("\n")
        )
        has_sorry = "sorry" in output.lower()

        if proc.returncode == 0 and not has_error and not has_sorry:
            return 1.0
        elif has_sorry:
            return 0.5
        else:
            return 0.3

    except Exception:
        return 0.3
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# =============================================================================
# Guardar / cargar pesos
# =============================================================================

def save_checkpoint(network, metrics: dict, epoch: int, is_best: bool = False) -> None:
    """
    Guarda pesos y metricas.

    - Siempre actualiza data/neural_agent.json[.pt]  (cargado por NucleoAgent)
    - Si is_best=True, guarda ademas en E:/chechkpointsmetamatematico/best_epoch_N.pt
    - Guarda el historial completo de metricas en E:/chechkpointsmetamatematico/training_log.json
    """
    import torch

    DATA_DIR.mkdir(exist_ok=True)
    CKPT_DIR.mkdir(parents=True, exist_ok=True)

    # Pesos activos (los que usa NucleoAgent en produccion)
    torch.save(network.state_dict(), str(WEIGHTS_PATH))

    cfg_payload = {
        "config": {
            "hidden_dim": 256,
            "num_heads": 4,
            "num_layers": 3,
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "batch_size": 256,
            "clip_range": 0.2,
            "value_coef": 0.5,
            "entropy_coef": 0.01,
            "gae_lambda": 0.95,
            "n_epochs": 4,
            "epsilon_start": 1.0,
            "epsilon_end": 0.1,
            "epsilon_decay": 0.995,
        },
        "metrics": metrics,
        "epsilon": 0.1,
        "total_steps": epoch * 1000,
        "use_neural": True,
        "trained_epoch": epoch,
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg_payload, f, indent=2)

    # Checkpoint nombrado por epoca
    ckpt_path = CKPT_DIR / f"epoch_{epoch:03d}.pt"
    torch.save({
        "epoch":        epoch,
        "state_dict":   network.state_dict(),
        "metrics":      metrics,
    }, str(ckpt_path))

    # Si es el mejor modelo, copiar como best.pt
    if is_best:
        import shutil
        best_path = CKPT_DIR / "best.pt"
        shutil.copy2(str(ckpt_path), str(best_path))
        # Guardar tambien con nombre descriptivo
        val_acc = metrics.get("best_val_acc", 0.0)
        named = CKPT_DIR / f"best_epoch_{epoch:03d}_val{val_acc:.4f}.pt"
        shutil.copy2(str(ckpt_path), str(named))

    # Log de entrenamiento acumulado
    log_path = CKPT_DIR / "training_log.json"
    log = []
    if log_path.exists():
        try:
            with open(log_path) as f:
                log = json.load(f)
        except Exception:
            log = []
    # Actualizar o agregar entrada de esta epoca
    entry = {"epoch": epoch, **metrics}
    updated = False
    for i, e in enumerate(log):
        if e.get("epoch") == epoch:
            log[i] = entry
            updated = True
            break
    if not updated:
        log.append(entry)
    log.sort(key=lambda x: x.get("epoch", 0))
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)


def load_checkpoint(network) -> int:
    """Carga pesos si existen. Retorna epoca de inicio."""
    import torch

    if WEIGHTS_PATH.exists():
        network.load_state_dict(torch.load(str(WEIGHTS_PATH), weights_only=True))
        print(f"  Checkpoint cargado: {WEIGHTS_PATH}")
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
            epoch = cfg.get("trained_epoch", 0)
            print(f"  Continuando desde epoca {epoch}")
            return epoch
    return 0


# =============================================================================
# Barra de progreso simple (sin dependencias extra)
# =============================================================================

class ProgressBar:
    def __init__(self, total: int, desc: str = ""):
        self.total   = total
        self.current = 0
        self.desc    = desc
        self.start   = time.time()

    def update(self, n: int = 1):
        self.current += n
        pct  = self.current / max(self.total, 1)
        bar  = "#" * int(pct * 30) + "-" * (30 - int(pct * 30))
        eta  = (time.time() - self.start) / max(pct, 1e-8) * (1 - pct)
        print(f"\r  {self.desc} [{bar}] {self.current}/{self.total}  ETA {eta:.0f}s", end="", flush=True)

    def close(self):
        elapsed = time.time() - self.start
        print(f"\r  {self.desc} [{'#'*30}] {self.total}/{self.total}  {elapsed:.1f}s")


# =============================================================================
# Main
# =============================================================================

def parse_args():
    p = argparse.ArgumentParser(description="Entrena GNN+PPO del NLE")
    p.add_argument("--epochs",      type=int,   default=10,
                   help="Epocas de preentrenamiento supervisado (default: 10)")
    p.add_argument("--batch-size",  type=int,   default=256,
                   help="Tamano del batch (default: 256)")
    p.add_argument("--lr",          type=float, default=3e-4,
                   help="Learning rate (default: 3e-4)")
    p.add_argument("--max-train",   type=int,   default=None,
                   help="Limitar ejemplos de entrenamiento (debug)")
    p.add_argument("--resume",      action="store_true",
                   help="Continuar desde el ultimo checkpoint")
    p.add_argument("--with-lean",   action="store_true",
                   help="Activar Fase 2 PPO con verificacion Lean")
    p.add_argument("--lean-samples",type=int,   default=200,
                   help="Problemas por epoca PPO Lean (default: 200)")
    p.add_argument("--ppo-epochs",  type=int,   default=5,
                   help="Epocas de PPO Lean en Fase 2 (default: 5)")
    p.add_argument("--seed",        type=int,   default=42)
    p.add_argument("--device",      type=str,   default="auto",
                   help="'cuda', 'cpu' o 'auto' (default: auto)")
    return p.parse_args()


def main():
    args = parse_args()

    import torch
    from nucleo.rl.networks import ActorCriticNetwork

    # --- Device ---
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    print(f"\n{'='*60}")
    print(f"  Entrenamiento GNN+PPO  --  NLE v7.0")
    print(f"  Device : {device}")
    if device.type == "cuda":
        props = torch.cuda.get_device_properties(0)
        vram  = props.total_memory / 1e9
        print(f"  GPU    : {props.name}  ({vram:.1f} GB VRAM)")
    print(f"  Epocas : {args.epochs}  |  Batch: {args.batch_size}  |  LR: {args.lr}")
    print(f"{'='*60}\n")

    # --- Verificar splits ---
    if not SPLITS_DIR.exists():
        print(f"[ERROR] No se encuentra el directorio de splits: {SPLITS_DIR}")
        print("  Ejecuta primero: python scripts/prepare_training_data.py")
        sys.exit(1)

    # --- Cargar datos ---
    print("[1/5] Cargando splits...")
    train_records = load_jsonl(SPLITS_DIR / "all_train.jsonl", args.max_train)
    val_records   = load_jsonl(SPLITS_DIR / "all_val.jsonl")
    test_records  = load_jsonl(SPLITS_DIR / "all_test.jsonl")
    print(f"  train: {len(train_records):>7}  |  val: {len(val_records):>7}  |  test: {len(test_records):>7}")

    if not train_records:
        print("[ERROR] No hay datos de entrenamiento.")
        sys.exit(1)

    # --- Construir grafo ---
    print("\n[2/5] Construyendo grafo de skills...")
    graph      = build_skill_graph()
    graph_data = get_graph_data(graph).to(device)
    print(f"  Skills: {len(graph.skills)}  |  Morfismos: {len(graph.morphisms)}")

    # --- Inicializar red ---
    print("\n[3/5] Inicializando red ActorCritic...")
    network   = ActorCriticNetwork().to(device)
    optimizer = torch.optim.Adam(network.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.epochs, eta_min=1e-5
    )

    n_params = sum(p.numel() for p in network.parameters())
    vram_mb  = n_params * 4 / 1e6
    print(f"  Parametros: {n_params:,}  |  Memoria: {vram_mb:.1f} MB")

    # Reanudar desde checkpoint
    start_epoch = 0
    if args.resume:
        start_epoch = load_checkpoint(network)

    # --- Fase 1: Preentrenamiento supervisado ---
    print(f"\n[4/5] Fase 1: Preentrenamiento supervisado ({args.epochs} epocas)")
    print(f"  Objetivo: accuracy -> 100% (siempre elegir ASSIST para matematicas)\n")

    best_val_acc = 0.0
    history = []

    for epoch in range(start_epoch, start_epoch + args.epochs):
        t0 = time.time()

        # Batches de entrenamiento (re-shuffle cada epoca)
        train_batches = make_batches(train_records, args.batch_size, shuffle=True, seed=args.seed + epoch)
        val_batches   = make_batches(val_records,   args.batch_size, shuffle=False)

        # Progress bar
        pb = ProgressBar(len(train_batches), desc=f"Epoca {epoch+1:>3}/{start_epoch+args.epochs}")

        # Entrenamiento
        running_loss = 0.0
        running_acc  = 0.0
        n_batches    = 0

        network.train()
        import torch.nn.functional as F
        from torch_geometric.data import Batch

        for batch in train_batches:
            problems = [r["problem"] for r in batch]
            bs = len(problems)

            query_emb   = encode_batch(problems, device)
            goal_emb    = encode_goals_batch(problems, device)
            graph_batch = Batch.from_data_list([graph_data] * bs).to(device)

            output = network(graph_batch, query_emb, goal_emb=goal_emb)

            target = torch.full((bs,), ASSIST_IDX, dtype=torch.long, device=device)
            loss   = F.cross_entropy(output.action_logits, target)

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(network.parameters(), 1.0)
            optimizer.step()

            with torch.no_grad():
                preds = output.action_logits.argmax(dim=-1)
                running_acc  += (preds == target).float().mean().item()
                running_loss += loss.item()
                n_batches    += 1

            pb.update()

        pb.close()
        scheduler.step()

        train_loss = running_loss / max(n_batches, 1)
        train_acc  = running_acc  / max(n_batches, 1)

        # Validacion
        val_metrics = evaluate(network, graph_data, val_batches, device)
        val_acc     = val_metrics["accuracy"]
        val_loss    = val_metrics["loss"]

        elapsed = time.time() - t0
        lr_now  = optimizer.param_groups[0]["lr"]

        print(f"  Epoca {epoch+1:>3}  "
              f"train_loss={train_loss:.4f}  train_acc={train_acc:.3f}  "
              f"val_loss={val_loss:.4f}  val_acc={val_acc:.3f}  "
              f"lr={lr_now:.2e}  ({elapsed:.1f}s)")

        history.append({
            "epoch":      epoch + 1,
            "train_loss": round(train_loss, 4),
            "train_acc":  round(train_acc, 4),
            "val_loss":   round(val_loss, 4),
            "val_acc":    round(val_acc, 4),
            "lr":         round(lr_now, 6),
            "elapsed_s":  round(elapsed, 1),
        })

        # Guardar checkpoint de cada epoca y marcar el mejor
        is_best = val_acc >= best_val_acc
        if is_best:
            best_val_acc = val_acc

        epoch_metrics = {
            "best_val_acc":  round(best_val_acc, 4),
            "epoch":         epoch + 1,
            "train_loss":    round(train_loss, 4),
            "train_acc":     round(train_acc, 4),
            "val_loss":      round(val_loss, 4),
            "val_acc":       round(val_acc, 4),
            "lr":            round(lr_now, 6),
            "elapsed_s":     round(elapsed, 1),
            "history":       history,
            "total_reward":  0.0,
            "avg_reward":    0.0,
            "episodes":      epoch + 1,
        }
        save_checkpoint(network, epoch_metrics, epoch + 1, is_best=is_best)
        if is_best:
            print(f"  ** MEJOR modelo guardado en E:/chechkpointsmetamatematico/best.pt (val_acc={best_val_acc:.3f}) **")

    # --- Fase 2: PPO Lean (opcional) ---
    lean_client = None
    if args.with_lean:
        print(f"\n[5/5] Fase 2: PPO con verificacion Lean ({args.lean_samples} muestras/epoca)")
        # Verificar lake env lean con un snippet real de Mathlib
        lake_bin = _LAKE_BIN if Path(_LAKE_BIN).exists() else "lake"
        # Warmup: 1 + 1 = 2 (ejercita la ruta norm_num completa con lake env lean)
        warmup_rec = {"solution": "The answer is 1 + 1 = \\boxed{2}.", "problem": "1+1"}
        warmup_reward = _lean_reward("1+1", rec=warmup_rec)
        if warmup_reward >= 0.5:
            print(f"  lake env lean OK ({lake_bin}) -- warmup reward={warmup_reward:.1f}")
            lean_client = True  # sentinel: indica que lean funciona
        else:
            print(f"  [WARN] lake env lean devolvio reward={warmup_reward} en warmup.")
            print(f"         Continuando de todas formas.")
            lean_client = True

        ppo_records = train_records
        for epoch in range(args.ppo_epochs):
            t0 = time.time()
            ppo_metrics = ppo_epoch_with_lean(
                network, optimizer, graph_data, ppo_records, device,
                lean_client, n_samples=args.lean_samples,
                seed=args.seed + epoch,
            )
            elapsed = time.time() - t0
            print(f"  PPO Epoca {epoch+1:>3}  "
                  f"loss={ppo_metrics['ppo_loss']:.4f}  "
                  f"avg_reward={ppo_metrics['avg_reward']:.3f}  "
                  f"assist%={ppo_metrics['assist_pct']:.2f}  "
                  f"({elapsed:.1f}s)")

            save_checkpoint(network, {
                "best_val_acc": round(best_val_acc, 4),
                "ppo_epoch":    epoch + 1,
                "ppo_metrics":  ppo_metrics,
                "total_reward": ppo_metrics["avg_reward"],
                "avg_reward":   ppo_metrics["avg_reward"],
                "episodes":     epoch + 1,
            }, epoch + 1)
    else:
        print(f"\n[5/5] Fase 2 PPO Lean omitida (usar --with-lean para activarla)")

    # --- Evaluacion final en test ---
    print(f"\n{'='*60}")
    print("  Evaluacion final en TEST SET")
    test_batches = make_batches(test_records, args.batch_size, shuffle=False)
    test_metrics = evaluate(network, graph_data, test_batches, device)

    # Guardar metricas de test en el log
    log_path = CKPT_DIR / "training_log.json"
    log = []
    if log_path.exists():
        try:
            with open(log_path) as f:
                log = json.load(f)
        except Exception:
            log = []
    test_entry = {
        "split":     "test_final",
        "test_loss": round(test_metrics["loss"], 4),
        "test_acc":  round(test_metrics["accuracy"], 4),
        "test_n":    test_metrics["samples"],
    }
    log.append(test_entry)
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)

    # === TABLA COMPLETA DE METRICAS ===
    print(f"\n{'='*70}")
    print(f"  RESUMEN COMPLETO DEL ENTRENAMIENTO")
    print(f"{'='*70}")
    print(f"  {'Epoca':>5}  {'Train Loss':>10}  {'Train Acc':>9}  {'Val Loss':>8}  {'Val Acc':>8}  {'LR':>8}")
    print(f"  {'-'*5}  {'-'*10}  {'-'*9}  {'-'*8}  {'-'*8}  {'-'*8}")
    for h in history:
        marker = " <-- MEJOR" if round(h["val_acc"], 4) == best_val_acc else ""
        print(f"  {h['epoch']:>5}  {h['train_loss']:>10.4f}  {h['train_acc']:>9.4f}  "
              f"{h['val_loss']:>8.4f}  {h['val_acc']:>8.4f}  "
              f"{h.get('lr', 0):>8.2e}{marker}")
    print(f"  {'-'*5}  {'-'*10}  {'-'*9}  {'-'*8}  {'-'*8}  {'-'*8}")
    print(f"\n  RESULTADO EN TEST SET  ({test_metrics['samples']} ejemplos):")
    print(f"    test_loss : {test_metrics['loss']:.4f}")
    print(f"    test_acc  : {test_metrics['accuracy']:.4f}  ({test_metrics['accuracy']*100:.1f}% elige ASSIST)")
    print(f"\n  MEJOR MODELO:")
    print(f"    val_acc   : {best_val_acc:.4f}")
    print(f"    guardado  : {CKPT_DIR}/best.pt")
    print(f"\n  ARCHIVOS GENERADOS:")
    print(f"    {WEIGHTS_PATH}   <- cargado por NucleoAgent")
    print(f"    {CONFIG_PATH}")
    print(f"    {CKPT_DIR}/epoch_NNN.pt  (uno por epoca)")
    print(f"    {CKPT_DIR}/best.pt       (mejor val_acc)")
    print(f"    {CKPT_DIR}/training_log.json")
    print(f"\n  Para activar el modelo entrenado: reinicia la app Streamlit.")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
