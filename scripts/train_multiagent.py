"""
train_multiagent.py — Entrena 14 agentes especializados, uno por categoría.
===========================================================================

Tres fases independientes:
  Fase 1 — Fine-tuning supervisado desde pesos globales (routing ASSIST)
  Fase 2 — Supervisión de tácticas con etiquetas heurísticas (sin correr Lean)
  Fase 3 — PPO con recompensa Lean real (solo con --with-lean)

Uso:
    python scripts/train_multiagent.py
    python scripts/train_multiagent.py --categories algebra number-theory
    python scripts/train_multiagent.py --epochs 5 --tactic-epochs 10
    python scripts/train_multiagent.py --device cuda
    python scripts/train_multiagent.py --with-lean --ppo-epochs 3
    python scripts/train_multiagent.py --dry-run

Fuente de datos:
    E:/Metamatematico/training/by_category/<cat>/{train,val,test}.jsonl
    (generado por scripts/balance_datasets.py)

Salida:
    E:/Metamatematico/training/agents/<categoria>.pt     — pesos finales
    E:/Metamatematico/training/agents/<cat>_best.pt      — mejor checkpoint
    E:/Metamatematico/training/agents/training_summary.json
    E:/Metamatematico/training/logs/                     — logs por categoría
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

# ──────────────────────────────────────────────────────────────────────────────
# Rutas — todo en E:\Metamatematico\training\
# ──────────────────────────────────────────────────────────────────────────────

TRAINING_ROOT = Path("E:/Metamatematico/training")
DATA_DIR      = TRAINING_ROOT / "by_category"
AGENTS_DIR    = TRAINING_ROOT / "agents"
LOGS_DIR      = TRAINING_ROOT / "logs"
BASE_WEIGHTS  = Path("E:/Metamatematico/data/neural_agent.json.pt")

# Directorios anteriores como fallback si el usuario ya tiene splits ahí
ALT_DATA_DIR  = Path("E:/datadeentrenamientovalidacion_test/by_category")

CATEGORIES = [
    "algebra", "analysis", "category-theory", "combinatorics", "computation",
    "geometry", "lean-tactics", "logic", "number-theory", "optimization",
    "probability", "proof-strategies", "set-theory", "topology",
]

# Tácticas Lean disponibles para clasificación
TACTICS = [
    "norm_num", "ring", "omega", "simp", "exact",
    "tauto", "linarith", "decide", "aesop", "induction",
]
TACTIC_TO_IDX = {t: i for i, t in enumerate(TACTICS)}


# ──────────────────────────────────────────────────────────────────────────────
# Logging por categoría
# ──────────────────────────────────────────────────────────────────────────────

def get_logger(category: str) -> logging.Logger:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger(f"agent.{category}")
    if not log.handlers:
        fh = logging.FileHandler(LOGS_DIR / f"{category}.log", encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s", "%H:%M:%S"))
        log.addHandler(fh)
    return log


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train_multiagent")


# ──────────────────────────────────────────────────────────────────────────────
# Carga de datos
# ──────────────────────────────────────────────────────────────────────────────

def _find_data_dir() -> Path:
    """Busca el directorio de splits en E:\Metamatematico\training\ o el antiguo."""
    if DATA_DIR.exists() and any(DATA_DIR.iterdir()):
        return DATA_DIR
    if ALT_DATA_DIR.exists() and any(ALT_DATA_DIR.iterdir()):
        logger.info(f"Usando directorio alternativo: {ALT_DATA_DIR}")
        return ALT_DATA_DIR
    return DATA_DIR  # dejará que load_category_data avise que no hay datos


def load_category_data(category: str, split: str = "train",
                       data_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    data_root = data_root or _find_data_dir()
    path = data_root / category / f"{split}.jsonl"
    if not path.exists():
        logger.warning(f"  No existe: {path}")
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


# ──────────────────────────────────────────────────────────────────────────────
# Fase 2 — Inferencia heurística de tácticas (sin correr Lean)
# ──────────────────────────────────────────────────────────────────────────────

_BOXED_RE   = re.compile(r"\\boxed\{([^}]+)\}")
_NUMBER_RE  = re.compile(r"\d")
_RING_KWORDS = {"polynomial", "ring", "ideal", "commutative", "field",
                "monomial", "binomial", "expand", "(a+b)", "factor"}
_OMEGA_KWORDS = {"divisible", "remainder", "modulo", "mod ", "∣", "divides",
                 "even", "odd", "integer", "natural number", "ℕ", "induction step"}
_LINARITH_KWORDS = {"inequality", "≤", "≥", "<", ">", "less than", "greater than",
                    "nonnegative", "positive", "upper bound", "lower bound", "linarith"}
_TAUTO_KWORDS = {"tautology", "implies", "if and only if", "iff", "∧", "∨",
                 "contradiction", "modus ponens", "propositional"}
_SIMP_KWORDS = {"simplify", "rewrite", "substitute", "set", "union", "intersection",
                "belongs to", "subset", "∈", "∉", "commutes", "associative"}
_DECIDE_KWORDS = {"algorithm", "decidable", "computable", "halting", "regular language",
                  "automaton", "turing", "complexity"}
_INDUCTION_KWORDS = {"by induction", "inductive step", "base case", "for all n",
                     "∀ n", "prove that for every", "prove for all"}
_EXACT_KWORDS = {"exactly", "unique", "there exists a unique", "definition of",
                 "by definition", "trivially", "follows directly"}

# Tácticas por defecto si no se puede inferir
_CATEGORY_DEFAULT: Dict[str, str] = {
    "algebra":          "ring",
    "analysis":         "norm_num",
    "category-theory":  "simp",
    "combinatorics":    "omega",
    "computation":      "decide",
    "geometry":         "norm_num",
    "lean-tactics":     "simp",
    "logic":            "tauto",
    "number-theory":    "norm_num",
    "optimization":     "linarith",
    "probability":      "norm_num",
    "proof-strategies": "exact",
    "set-theory":       "simp",
    "topology":         "simp",
}


def _infer_tactic(rec: Dict[str, Any], category: str) -> str:
    """
    Infiere la táctica Lean más adecuada para un registro de dataset.

    Usa heurísticas sobre el texto del problema y la solución.
    No llama a Lean — es supervisión débil (weak supervision).

    Prioridad:
      1. Boxed numérico + operadores → norm_num
      2. Keywords de ring → ring
      3. Keywords de inducción → induction (omega)
      4. Keywords de linarith → linarith
      5. Keywords de tauto (lógica proposicional) → tauto
      6. Keywords de decide (computabilidad) → decide
      7. Keywords de simp (conjuntos, reescritura) → simp
      8. Default por categoría
    """
    problem  = (rec.get("problem", "") or rec.get("query", "") or "").lower()
    solution = (rec.get("solution", "") or rec.get("answer", "") or "").lower()
    text = problem + " " + solution

    # 1. \boxed{N} con número → norm_num
    m = _BOXED_RE.search(text)
    if m and _NUMBER_RE.search(m.group(1)):
        return "norm_num"

    # 2. Ring / polynomial
    if any(kw in text for kw in _RING_KWORDS):
        if category in ("algebra", "number-theory", "analysis"):
            return "ring"

    # 3. Inducción → omega (aritmética entera en Lean)
    if any(kw in text for kw in _INDUCTION_KWORDS):
        return "omega"

    # 4. Desigualdades → linarith
    if any(kw in text for kw in _LINARITH_KWORDS):
        return "linarith"

    # 5. Lógica proposicional → tauto
    if any(kw in text for kw in _TAUTO_KWORDS):
        return "tauto"

    # 6. Computabilidad → decide
    if any(kw in text for kw in _DECIDE_KWORDS):
        return "decide"

    # 7. Conjuntos / reescritura → simp
    if any(kw in text for kw in _SIMP_KWORDS):
        return "simp"

    # 8. "exact" cuando se pide algo por definición
    if any(kw in text for kw in _EXACT_KWORDS):
        return "exact"

    return _CATEGORY_DEFAULT.get(category, "simp")


# ──────────────────────────────────────────────────────────────────────────────
# Grafo de skills por categoría
# ──────────────────────────────────────────────────────────────────────────────

def build_category_skill_graph(category: str):
    from nucleo.graph.category import SkillCategory
    from nucleo.types import Skill

    graph = SkillCategory(name=f"agent_{category}")

    l0_skills = [
        ("parse_query",       "Parsear consulta",       0),
        ("identify_type",     "Identificar tipo",       0),
        ("select_strategy",   "Seleccionar estrategia", 0),
        ("call_lean",         "Llamar Lean",            0),
        ("interpret_result",  "Interpretar resultado",  0),
        ("format_response",   "Formatear respuesta",    0),
        ("check_validity",    "Verificar validez",      0),
        ("decompose_problem", "Descomponer problema",   0),
        ("apply_tactic",      "Aplicar tactica",        0),
        ("synthesize_proof",  "Sintetizar prueba",      0),
    ]
    for sid, name, level in l0_skills:
        graph.add_skill(Skill(id=sid, name=name, level=level))

    category_skills = {
        "algebra":          [("factor_poly","Factorizar",1),("group_theory","Grupos",1),("ring_ideal","Ideales",1),("linear_algebra","Algebra Lineal",1),("galois_theory","Galois",1)],
        "analysis":         [("compute_limit","Limites",1),("differentiate","Derivar",1),("integrate","Integrar",1),("series_conv","Series",1),("real_analysis","Analisis Real",1)],
        "category-theory":  [("define_functor","Functores",1),("nat_transform","Trans Natural",1),("colimit_const","Colimites",1),("adjunction","Adjunciones",1),("yoneda","Yoneda",1)],
        "combinatorics":    [("count_perm","Permutaciones",1),("binomial","Binomial",1),("graph_color","Coloracion",1),("partitions","Particiones",1),("pigeonhole","Palomar",1)],
        "computation":      [("complexity","Complejidad",1),("algo_design","Algoritmos",1),("decidability","Decidibilidad",1),("turing","Turing",1),("automata","Automatas",1)],
        "geometry":         [("euclidean","Euclidiana",1),("coord_geom","Coordenadas",1),("area_vol","Area y Volumen",1),("circles","Circulos",1),("triangles","Triangulos",1)],
        "lean-tactics":     [("tac_simp","simp",1),("tac_ring","ring",1),("tac_norm_num","norm_num",1),("tac_omega","omega",1),("tac_induction","induction",1)],
        "logic":            [("prop_logic","Logica Proposicional",1),("pred_logic","Logica Predicados",1),("sat","SAT",1),("modal","Modal",1),("proof_theory","Teoria Prueba",1)],
        "number-theory":    [("primality","Primalidad",1),("mod_arith","Aritmetica Modular",1),("diophantine","Diofanticas",1),("nt_theorems","Teoremas NT",1),("crypto_nt","NT Cripto",1)],
        "optimization":     [("linear_prog","Prog Lineal",1),("grad_descent","Descenso Gradiente",1),("convex","Convexa",1),("lagrange","Lagrange",1),("int_optim","Optimizacion Entera",1)],
        "probability":      [("basic_prob","Probabilidad Basica",1),("cond_prob","Prob Condicional",1),("expectation","Esperanza",1),("distributions","Distribuciones",1),("markov","Markov",1)],
        "proof-strategies": [("induction","Induccion",1),("contradiction","Contradiccion",1),("contrapositive","Contrapositiva",1),("construction","Constructiva",1),("cases","Por Casos",1)],
        "set-theory":       [("set_ops","Operaciones Conjuntos",1),("cardinality","Cardinalidad",1),("ordinals","Ordinales",1),("axiom_choice","Axioma Eleccion",1),("cantor","Cantor",1)],
        "topology":         [("open_closed","Abiertos Cerrados",1),("compactness","Compacidad",1),("connectedness","Conexidad",1),("homeomorphism","Homeomorfismo",1),("homotopy","Homotopia",1)],
    }
    for sid, name, level in category_skills.get(category, []):
        graph.add_skill(Skill(id=sid, name=name, level=level))

    return graph


# ──────────────────────────────────────────────────────────────────────────────
# Construcción de estado
# ──────────────────────────────────────────────────────────────────────────────

def record_to_state(rec: Dict[str, Any], graph, category: str):
    from nucleo.types import State
    query = rec.get("problem", rec.get("query", ""))
    goal  = rec.get("solution", rec.get("answer", ""))
    return State(
        lean_goal=query,          # query text stored in lean_goal for encode_query
        graph_snapshot={"category": category, "source": rec.get("source", "")},
        metrics={"expected_goal": hash(goal) % 1000},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Fase 1 — Fine-tuning supervisado (routing)
# ──────────────────────────────────────────────────────────────────────────────

def train_phase1_routing(
    category: str,
    agent,
    graph,
    train_data: List[Dict],
    val_data: List[Dict],
    args: argparse.Namespace,
    cat_log: logging.Logger,
) -> Tuple[float, List[Dict]]:
    """Fine-tuning para routing ASSIST. Retorna (best_val_acc, history)."""
    from nucleo.rl.mdp import Transition
    from nucleo.types import ActionType

    best_val_acc = 0.0
    history = []

    for epoch in range(1, args.epochs + 1):
        agent._network.train()
        np.random.shuffle(train_data)
        correct = total = 0
        total_loss = 0.0
        batches = [train_data[i:i+args.batch_size]
                   for i in range(0, len(train_data), args.batch_size)]

        for batch in batches:
            transitions = []
            for rec in batch:
                state  = record_to_state(rec, graph, category)
                action = agent.select_action(state)
                reward = 1.0 if action.action_type == ActionType.ASSIST else 0.0
                transitions.append(
                    Transition(state=state, action=action, reward=reward,
                               next_state=state, done=True)
                )
                correct += int(action.action_type == ActionType.ASSIST)
                total   += 1
            m = agent.update(transitions)
            total_loss += m.get("loss", 0.0)

        train_acc = correct / max(total, 1)
        avg_loss  = total_loss / max(len(batches), 1)

        val_acc = 0.0
        if val_data:
            agent._network.eval()
            val_correct = sum(
                1 for rec in val_data
                if agent.select_action(
                    record_to_state(rec, graph, category)
                ).action_type == ActionType.ASSIST
            )
            val_acc = val_correct / len(val_data)

        cat_log.info(f"[F1] Época {epoch}/{args.epochs} loss={avg_loss:.4f} "
                     f"train_acc={train_acc:.3f} val_acc={val_acc:.3f}")
        logger.info(f"  [{category}] F1 época {epoch}/{args.epochs} | "
                    f"loss={avg_loss:.4f} | train={train_acc:.3f} | val={val_acc:.3f}")

        best_val_acc = max(best_val_acc, val_acc)
        history.append({"phase": 1, "epoch": epoch, "loss": avg_loss,
                        "train_acc": train_acc, "val_acc": val_acc})

    return best_val_acc, history


# ──────────────────────────────────────────────────────────────────────────────
# Fase 2 — Supervisión de tácticas (weak supervision, sin Lean)
# ──────────────────────────────────────────────────────────────────────────────

def train_phase2_tactics(
    category: str,
    agent,
    graph,
    train_data: List[Dict],
    val_data: List[Dict],
    args: argparse.Namespace,
    cat_log: logging.Logger,
) -> Tuple[float, List[Dict]]:
    """
    Fase 2: entrena selección de tácticas usando etiquetas heurísticas.

    Convierte cada ejemplo en (query, tactic_label) y entrena el actor
    para predecir la táctica correcta vía cross-entropy.
    No requiere correr Lean — las etiquetas se infieren del texto.
    """
    import torch
    import torch.nn.functional as F
    from nucleo.rl.networks import encode_query

    best_tactic_acc = 0.0
    history = []

    # Pre-calcular etiquetas de táctica para todo el set
    def label_batch(records):
        labeled = []
        for rec in records:
            tactic = _infer_tactic(rec, category)
            idx    = TACTIC_TO_IDX.get(tactic, TACTIC_TO_IDX["simp"])
            labeled.append((rec, idx))
        return labeled

    train_labeled = label_batch(train_data)
    val_labeled   = label_batch(val_data) if val_data else []

    # Estadísticas de distribución de tácticas
    tactic_dist: Dict[str, int] = {}
    for _, idx in train_labeled:
        t = TACTICS[idx]
        tactic_dist[t] = tactic_dist.get(t, 0) + 1
    cat_log.info(f"[F2] Distribución de tácticas: {tactic_dist}")

    # Necesitamos la capa de salida de tácticas en el network
    # Si el network no tiene tactic_head, lo añadimos sobre la marcha
    network = agent._network
    from nucleo.rl.networks import VOCAB_SIZE as _VOCAB_SIZE
    if not hasattr(network, "tactic_head"):
        network.tactic_head = torch.nn.Linear(_VOCAB_SIZE, len(TACTICS))
        if args.device != "cpu":
            network.tactic_head = network.tactic_head.to(args.device)
        # Optimizador separado solo para la cabeza de tácticas
        tactic_optimizer = torch.optim.Adam(
            network.tactic_head.parameters(), lr=args.lr
        )
    else:
        tactic_optimizer = torch.optim.Adam(
            network.tactic_head.parameters(), lr=args.lr
        )

    for epoch in range(1, args.tactic_epochs + 1):
        network.train()
        np.random.shuffle(train_labeled)

        total_loss = 0.0
        correct = total = 0
        batches = [train_labeled[i:i+args.batch_size]
                   for i in range(0, len(train_labeled), args.batch_size)]

        for batch in batches:
            tactic_optimizer.zero_grad()
            batch_loss = 0.0

            for rec, tactic_idx in batch:
                state = record_to_state(rec, graph, category)
                # Obtener embedding del query desde el agente
                try:
                    emb = encode_query(state.lean_goal or "")
                    if emb is None:
                        continue
                    logits = network.tactic_head(emb.unsqueeze(0))
                    target = torch.tensor([tactic_idx], dtype=torch.long)
                    if args.device != "cpu":
                        logits = logits.to(args.device)
                        target = target.to(args.device)
                    loss = F.cross_entropy(logits, target)
                    batch_loss += loss
                    pred = logits.argmax(dim=-1).item()
                    correct += int(pred == tactic_idx)
                except Exception:
                    pass
                total += 1

            if total > 0 and batch_loss > 0:
                batch_loss.backward()
                tactic_optimizer.step()
                total_loss += batch_loss.item()

        train_tactic_acc = correct / max(total, 1)
        avg_loss = total_loss / max(len(batches), 1)

        # Validación de tácticas
        val_tactic_acc = 0.0
        if val_labeled:
            network.eval()
            vc = vt = 0
            with torch.no_grad():
                for rec, tactic_idx in val_labeled:
                    try:
                        state = record_to_state(rec, graph, category)
                        emb   = encode_query(state.lean_goal or "")
                        if emb is None:
                            continue
                        logits = network.tactic_head(emb.unsqueeze(0))
                        pred   = logits.argmax(dim=-1).item()
                        vc += int(pred == tactic_idx)
                    except Exception:
                        pass
                    vt += 1
            val_tactic_acc = vc / max(vt, 1)

        cat_log.info(f"[F2] Época {epoch}/{args.tactic_epochs} "
                     f"loss={avg_loss:.4f} tactic_acc_train={train_tactic_acc:.3f} "
                     f"tactic_acc_val={val_tactic_acc:.3f}")
        logger.info(f"  [{category}] F2 época {epoch}/{args.tactic_epochs} | "
                    f"loss={avg_loss:.4f} | tactic_train={train_tactic_acc:.3f} | "
                    f"tactic_val={val_tactic_acc:.3f}")

        best_tactic_acc = max(best_tactic_acc, val_tactic_acc)
        history.append({"phase": 2, "epoch": epoch, "loss": avg_loss,
                        "tactic_train": train_tactic_acc, "tactic_val": val_tactic_acc})

    return best_tactic_acc, history


# ──────────────────────────────────────────────────────────────────────────────
# Fase 3 — PPO con recompensa Lean real
# ──────────────────────────────────────────────────────────────────────────────

def train_phase3_ppo_lean(
    category: str,
    agent,
    graph,
    train_data: List[Dict],
    args: argparse.Namespace,
    cat_log: logging.Logger,
) -> Tuple[float, List[Dict]]:
    """PPO con recompensa real de Lean. Lento — solo para categorías con datos Lean."""
    try:
        from scripts.train_gnn_ppo import _lean_reward
    except ImportError:
        try:
            from train_gnn_ppo import _lean_reward
        except ImportError:
            cat_log.error("No se pudo importar _lean_reward. Saltando Fase 3.")
            return 0.0, []

    from nucleo.rl.mdp import Transition
    from nucleo.types import ActionType

    best_reward = 0.0
    history = []

    for epoch in range(1, args.ppo_epochs + 1):
        sample = train_data[:min(500, len(train_data))]
        np.random.shuffle(sample)

        transitions = []
        total_reward = 0.0
        for rec in sample:
            state  = record_to_state(rec, graph, category)
            action = agent.select_action(state)
            reward = _lean_reward(
                rec.get("problem", ""), lean_client=None, rec=rec
            )
            if action.action_type != ActionType.ASSIST:
                reward = min(reward - 0.5, 0.0)
            transitions.append(
                Transition(state=state, action=action, reward=reward,
                           next_state=state, done=True)
            )
            total_reward += reward

        agent.update(transitions)
        avg_reward = total_reward / max(len(sample), 1)

        cat_log.info(f"[F3] PPO época {epoch}/{args.ppo_epochs} avg_reward={avg_reward:.4f}")
        logger.info(f"  [{category}] F3 PPO época {epoch}/{args.ppo_epochs} | reward={avg_reward:.4f}")

        best_reward = max(best_reward, avg_reward)
        history.append({"phase": 3, "epoch": epoch, "avg_reward": avg_reward})

    return best_reward, history


# ──────────────────────────────────────────────────────────────────────────────
# Entrenamiento completo de una categoría
# ──────────────────────────────────────────────────────────────────────────────

def train_category(category: str, args: argparse.Namespace,
                   data_root: Optional[Path] = None) -> Dict[str, Any]:
    import torch
    from nucleo.rl.agent import NucleoAgent, AgentConfig

    cat_log = get_logger(category)
    logger.info(f"\n{'='*60}")
    logger.info(f"  AGENTE: {category.upper()}")
    logger.info(f"{'='*60}")

    # ── Cargar datos ──
    train_data = load_category_data(category, "train", data_root)
    val_data   = load_category_data(category, "val",   data_root)

    if not train_data:
        logger.warning(f"[{category}] Sin datos. Saltando.")
        return {"category": category, "skipped": True}

    logger.info(f"  [{category}] train={len(train_data)} val={len(val_data)}")

    # ── Construir grafo + agente ──
    graph  = build_category_skill_graph(category)
    config = AgentConfig(
        hidden_dim=256,
        learning_rate=args.lr,
        batch_size=args.batch_size,
    )
    agent = NucleoAgent(graph=graph, config=config, use_neural=True)

    # Mover red a GPU si está disponible
    if args.device != "cpu" and agent._network is not None:
        try:
            import torch
            agent._network = agent._network.to(args.device)
            logger.info(f"  [{category}] Red movida a {args.device}")
        except Exception as e:
            logger.warning(f"  [{category}] No se pudo mover a GPU: {e}")
            args.device = "cpu"

    # ── Cargar pesos base (global GNN+PPO) ──
    if BASE_WEIGHTS.exists():
        try:
            sd = torch.load(str(BASE_WEIGHTS), map_location=args.device)
            agent._network.load_state_dict(sd, strict=False)
            logger.info(f"  [{category}] Pesos globales cargados")
            cat_log.info(f"Pesos base cargados: {BASE_WEIGHTS}")
        except Exception as e:
            logger.warning(f"  [{category}] Sin pesos base: {e}")

    # ── Cargar checkpoint propio si existe ──
    best_ckpt = AGENTS_DIR / f"{category}_best.pt"
    if best_ckpt.exists():
        try:
            ckpt = torch.load(str(best_ckpt), map_location=args.device)
            agent._network.load_state_dict(ckpt.get("network", ckpt), strict=False)
            if "optimizer" in ckpt and hasattr(agent, "optimizer"):
                agent.optimizer.load_state_dict(ckpt["optimizer"])
            logger.info(f"  [{category}] Checkpoint propio cargado")
        except Exception as e:
            logger.warning(f"  [{category}] Sin checkpoint propio: {e}")

    all_history = []
    results: Dict[str, Any] = {"category": category, "train_samples": len(train_data)}

    # ── Fase 1: Fine-tuning routing ──
    if args.epochs > 0:
        best_acc, hist = train_phase1_routing(
            category, agent, graph, train_data, val_data, args, cat_log
        )
        results["phase1_val_acc"] = best_acc
        all_history.extend(hist)
        _save_checkpoint(agent, category, epoch=args.epochs,
                         metric=best_acc, metric_name="val_acc")

    # ── Fase 2: Supervisión de tácticas ──
    if args.tactic_epochs > 0:
        best_tac, hist = train_phase2_tactics(
            category, agent, graph, train_data, val_data, args, cat_log
        )
        results["phase2_tactic_acc"] = best_tac
        all_history.extend(hist)
        _save_checkpoint(agent, category, epoch=args.tactic_epochs,
                         metric=best_tac, metric_name="tactic_acc")

    # ── Fase 3: PPO Lean (opcional) ──
    if args.with_lean and args.ppo_epochs > 0:
        best_reward, hist = train_phase3_ppo_lean(
            category, agent, graph, train_data, args, cat_log
        )
        results["phase3_reward"] = best_reward
        all_history.extend(hist)
        _save_checkpoint(agent, category, epoch=args.ppo_epochs,
                         metric=best_reward, metric_name="ppo_reward")

    # ── Guardar pesos finales ──
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    final_path = AGENTS_DIR / f"{category}.pt"
    torch.save({
        "network":        agent._network.state_dict(),
        "category":       category,
        "history":        all_history,
        "tactic_to_idx":  TACTIC_TO_IDX,
        "results":        results,
    }, str(final_path))
    logger.info(f"  [{category}] Pesos finales → {final_path}")
    cat_log.info(f"Pesos finales guardados: {final_path}")

    # Log de historia completa
    history_path = LOGS_DIR / f"{category}_history.json"
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(all_history, f, indent=2, ensure_ascii=False)

    return results


def _save_checkpoint(agent, category: str, epoch: int,
                     metric: float, metric_name: str):
    import torch
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = AGENTS_DIR / f"{category}_best.pt"
    # Solo sobreescribe si mejora
    if path.exists():
        try:
            prev = torch.load(str(path), map_location="cpu")
            if prev.get(metric_name, -1) >= metric:
                return
        except Exception:
            pass
    torch.save({
        "network":    agent._network.state_dict(),
        "category":   category,
        "epoch":      epoch,
        metric_name:  metric,
    }, str(path))


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Entrenar 14 agentes especializados NLE v7.0",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--categories", nargs="*", default=None,
                   help="Categorías a entrenar (por defecto: todas)")
    p.add_argument("--epochs",        type=int,   default=5,    help="Épocas Fase 1 (routing)")
    p.add_argument("--tactic-epochs", type=int,   default=10,   help="Épocas Fase 2 (tácticas)")
    p.add_argument("--ppo-epochs",    type=int,   default=3,    help="Épocas Fase 3 (PPO Lean)")
    p.add_argument("--batch-size",    type=int,   default=128,  help="Tamaño de batch")
    p.add_argument("--lr",            type=float, default=3e-4, help="Learning rate")
    p.add_argument("--device",        type=str,   default="auto",
                   help="Dispositivo: auto | cuda | cpu")
    p.add_argument("--with-lean",     action="store_true",
                   help="Fase 3: PPO con recompensa Lean real (lento)")
    p.add_argument("--skip-phase1",   action="store_true", help="Saltar Fase 1 routing")
    p.add_argument("--skip-phase2",   action="store_true", help="Saltar Fase 2 tácticas")
    p.add_argument("--dry-run",       action="store_true", help="Solo mostrar info, no entrenar")
    return p.parse_args()


def resolve_device(device_arg: str) -> str:
    if device_arg == "auto":
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"
    return device_arg


def main():
    import torch
    args = parse_args()

    # Resolver dispositivo
    args.device = resolve_device(args.device)
    if args.device == "cuda":
        try:
            import torch
            logger.info(f"GPU: {torch.cuda.get_device_name(0)} "
                        f"({torch.cuda.get_device_properties(0).total_memory // 1024**2} MB VRAM)")
        except Exception:
            args.device = "cpu"
            logger.warning("GPU no disponible, usando CPU")
    logger.info(f"Dispositivo: {args.device}")

    # Ajustar epochs si se pide saltar fases
    if args.skip_phase1:
        args.epochs = 0
    if args.skip_phase2:
        args.tactic_epochs = 0

    # Categorías
    cats = args.categories if args.categories else CATEGORIES
    invalid = [c for c in cats if c not in CATEGORIES]
    if invalid:
        logger.error(f"Categorías inválidas: {invalid}. Válidas: {CATEGORIES}")
        sys.exit(1)

    # Detectar directorio de datos
    data_root = _find_data_dir()

    logger.info(f"\nDirectorio de datos: {data_root}")
    logger.info(f"Directorio de salida: {AGENTS_DIR}")
    logger.info(f"Logs: {LOGS_DIR}")
    logger.info(f"Categorías: {cats}")
    logger.info(f"Fases: F1={args.epochs}ep | F2={args.tactic_epochs}ep | "
                f"F3={'SÍ '+str(args.ppo_epochs)+'ep' if args.with_lean else 'NO'}")

    # Mostrar disponibilidad de datos
    logger.info("\nDisponibilidad de datos:")
    for cat in cats:
        train_path = data_root / cat / "train.jsonl"
        if train_path.exists():
            n = sum(1 for _ in open(train_path, encoding="utf-8"))
            logger.info(f"  {cat:<22}: {n:>6} ejemplos")
        else:
            logger.info(f"  {cat:<22}: *** SIN DATOS ***")

    if args.dry_run:
        logger.info("\nDry-run completado.")
        return

    # ── Entrenamiento ──
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []
    t0 = time.time()

    for cat in cats:
        try:
            result = train_category(cat, args, data_root)
            all_results.append(result)
        except Exception as e:
            logger.error(f"[{cat}] Error durante entrenamiento: {e}", exc_info=True)
            all_results.append({"category": cat, "error": str(e)})

    # ── Resumen final ──
    elapsed = time.time() - t0
    logger.info(f"\n{'='*65}")
    logger.info(f"  ENTRENAMIENTO COMPLETADO — {elapsed/60:.1f} min")
    logger.info(f"{'='*65}")
    logger.info(f"\n{'Categoría':<22} {'Train':>7} {'F1 acc':>8} {'F2 tac':>8} {'F3 rew':>8}")
    logger.info("-" * 58)
    for r in all_results:
        if r.get("skipped"):
            logger.info(f"  {r['category']:<20}  {'SIN DATOS':>10}")
        elif r.get("error"):
            logger.info(f"  {r['category']:<20}  {'ERROR':>10}")
        else:
            logger.info(
                f"  {r.get('category','?'):<20} "
                f"{r.get('train_samples',0):>7} "
                f"{r.get('phase1_val_acc', 0.0):>8.3f} "
                f"{r.get('phase2_tactic_acc', 0.0):>8.3f} "
                f"{r.get('phase3_reward', 0.0):>8.3f}"
            )

    # Guardar resumen JSON
    summary_path = AGENTS_DIR / "training_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    logger.info(f"\nResumen → {summary_path}")

    # ── Copiar mejores checkpoints a carpeta best/ para no perderlos ──
    import shutil
    best_dir = AGENTS_DIR / "best"
    best_dir.mkdir(exist_ok=True)
    copied = 0
    for r in all_results:
        if r.get("skipped") or r.get("error"):
            continue
        cat = r.get("category", "")
        src = AGENTS_DIR / f"{cat}_best.pt"
        if src.exists():
            shutil.copy2(str(src), str(best_dir / f"{cat}_best.pt"))
            copied += 1
    logger.info(f"Mejores checkpoints copiados a {best_dir}  ({copied} archivos)")


if __name__ == "__main__":
    main()
