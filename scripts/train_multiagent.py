"""
train_multiagent.py — Entrena 14 agentes especializados, uno por categoría.
===========================================================================

Uso:
    python scripts/train_multiagent.py
    python scripts/train_multiagent.py --categories algebra number-theory
    python scripts/train_multiagent.py --epochs 10 --batch-size 128
    python scripts/train_multiagent.py --with-lean          # PPO con recompensa Lean real
    python scripts/train_multiagent.py --category algebra   # solo una categoría

Fuente de datos:
    E:/datadeentrenamientovalidacion_test/by_category/<cat>/train.jsonl
    (generado por scripts/balance_datasets.py)

Salida:
    data/agents/<categoria>.pt  — pesos de cada agente
    E:/chechkpointsmetamatematico/multiagent_<cat>_best.pt  — mejores checkpoints
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

# Asegurar imports del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train_multiagent")

# ──────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────
DATA_DIR = Path("E:/datadeentrenamientovalidacion_test/by_category")
WEIGHTS_DIR = Path(__file__).parent.parent / "data" / "agents"
CHECKPOINT_DIR = Path("E:/chechkpointsmetamatematico")
BASE_WEIGHTS = Path(__file__).parent.parent / "data" / "neural_agent.json.pt"

CATEGORIES = [
    "algebra", "analysis", "category-theory", "combinatorics", "computation",
    "geometry", "lean-tactics", "logic", "number-theory", "optimization",
    "probability", "proof-strategies", "set-theory", "topology",
]


# ──────────────────────────────────────────────
# Carga de datos
# ──────────────────────────────────────────────

def load_category_data(category: str, split: str = "train") -> List[Dict[str, Any]]:
    """Carga registros JSONL para una categoría y split."""
    path = DATA_DIR / category / f"{split}.jsonl"
    if not path.exists():
        logger.warning(f"  No existe {path}")
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


# ──────────────────────────────────────────────
# Construcción del grafo de skills por categoría
# ──────────────────────────────────────────────

def build_category_skill_graph(category: str):
    """Construye un SkillCategory con skills L0 + skills de la categoría."""
    from nucleo.graph.category import SkillCategory
    from nucleo.graph.skills import SkillNode, SkillLevel

    graph = SkillCategory(name=f"agent_{category}")

    # Skills L0 (fundacionales — siempre presentes)
    l0_skills = [
        ("parse_query", "Parsear consulta", SkillLevel.L0),
        ("identify_type", "Identificar tipo de problema", SkillLevel.L0),
        ("select_strategy", "Seleccionar estrategia", SkillLevel.L0),
        ("call_lean", "Llamar verificador Lean", SkillLevel.L0),
        ("interpret_result", "Interpretar resultado Lean", SkillLevel.L0),
        ("format_response", "Formatear respuesta", SkillLevel.L0),
        ("check_validity", "Verificar validez lógica", SkillLevel.L0),
        ("decompose_problem", "Descomponer problema", SkillLevel.L0),
        ("apply_tactic", "Aplicar táctica", SkillLevel.L0),
        ("synthesize_proof", "Sintetizar prueba", SkillLevel.L0),
    ]
    for skill_id, name, level in l0_skills:
        graph.add_skill(SkillNode(skill_id=skill_id, name=name, level=level))

    # Skills L1 específicas por categoría
    category_skills = {
        "algebra": [
            ("factor_poly", "Factorizar polinomio", SkillLevel.L1),
            ("solve_equation", "Resolver ecuación", SkillLevel.L1),
            ("group_theory", "Teoría de grupos", SkillLevel.L1),
            ("ring_ideal", "Ideales en anillos", SkillLevel.L1),
            ("linear_algebra", "Álgebra lineal", SkillLevel.L1),
        ],
        "analysis": [
            ("compute_limit", "Calcular límite", SkillLevel.L1),
            ("differentiate", "Derivar función", SkillLevel.L1),
            ("integrate", "Integrar función", SkillLevel.L1),
            ("series_convergence", "Convergencia de series", SkillLevel.L1),
            ("real_analysis", "Análisis real", SkillLevel.L1),
        ],
        "category-theory": [
            ("define_functor", "Definir funtor", SkillLevel.L1),
            ("natural_transform", "Transformación natural", SkillLevel.L1),
            ("colimit_construction", "Construir colímite", SkillLevel.L1),
            ("adjunction", "Adjunción", SkillLevel.L1),
            ("yoneda_lemma", "Lema de Yoneda", SkillLevel.L1),
        ],
        "combinatorics": [
            ("count_permutations", "Contar permutaciones", SkillLevel.L1),
            ("binomial_coeff", "Coeficientes binomiales", SkillLevel.L1),
            ("graph_coloring", "Coloración de grafos", SkillLevel.L1),
            ("partition_theory", "Teoría de particiones", SkillLevel.L1),
            ("pigeonhole", "Principio del palomar", SkillLevel.L1),
        ],
        "computation": [
            ("complexity_analysis", "Análisis de complejidad", SkillLevel.L1),
            ("algorithm_design", "Diseño de algoritmos", SkillLevel.L1),
            ("decidability", "Decidibilidad", SkillLevel.L1),
            ("turing_reduction", "Reducción de Turing", SkillLevel.L1),
            ("automata_theory", "Teoría de autómatas", SkillLevel.L1),
        ],
        "geometry": [
            ("euclidean_proof", "Prueba euclidiana", SkillLevel.L1),
            ("coordinate_geom", "Geometría coordenada", SkillLevel.L1),
            ("area_volume", "Área y volumen", SkillLevel.L1),
            ("circle_theorems", "Teoremas de círculos", SkillLevel.L1),
            ("triangle_props", "Propiedades de triángulos", SkillLevel.L1),
        ],
        "lean-tactics": [
            ("tactic_simp", "Táctica simp", SkillLevel.L1),
            ("tactic_ring", "Táctica ring", SkillLevel.L1),
            ("tactic_norm_num", "Táctica norm_num", SkillLevel.L1),
            ("tactic_omega", "Táctica omega", SkillLevel.L1),
            ("tactic_induction", "Táctica induction", SkillLevel.L1),
        ],
        "logic": [
            ("propositional_logic", "Lógica proposicional", SkillLevel.L1),
            ("predicate_logic", "Lógica de predicados", SkillLevel.L1),
            ("sat_solving", "Resolución SAT", SkillLevel.L1),
            ("modal_logic", "Lógica modal", SkillLevel.L1),
            ("proof_theory", "Teoría de la prueba", SkillLevel.L1),
        ],
        "number-theory": [
            ("primality_test", "Test de primalidad", SkillLevel.L1),
            ("modular_arith", "Aritmética modular", SkillLevel.L1),
            ("diophantine_eq", "Ecuaciones diofánticas", SkillLevel.L1),
            ("number_theorems", "Teoremas de teoría de números", SkillLevel.L1),
            ("cryptographic_nt", "TN criptográfica", SkillLevel.L1),
        ],
        "optimization": [
            ("linear_program", "Programación lineal", SkillLevel.L1),
            ("gradient_descent", "Descenso del gradiente", SkillLevel.L1),
            ("convex_optim", "Optimización convexa", SkillLevel.L1),
            ("lagrange_mult", "Multiplicadores de Lagrange", SkillLevel.L1),
            ("integer_optim", "Optimización entera", SkillLevel.L1),
        ],
        "probability": [
            ("basic_probability", "Probabilidad básica", SkillLevel.L1),
            ("conditional_prob", "Probabilidad condicional", SkillLevel.L1),
            ("expectation_var", "Esperanza y varianza", SkillLevel.L1),
            ("distributions", "Distribuciones estadísticas", SkillLevel.L1),
            ("markov_chains", "Cadenas de Markov", SkillLevel.L1),
        ],
        "proof-strategies": [
            ("proof_induction", "Prueba por inducción", SkillLevel.L1),
            ("proof_contradiction", "Prueba por contradicción", SkillLevel.L1),
            ("proof_contrapositive", "Prueba por contrapositiva", SkillLevel.L1),
            ("proof_construction", "Prueba constructiva", SkillLevel.L1),
            ("proof_cases", "Prueba por casos", SkillLevel.L1),
        ],
        "set-theory": [
            ("set_operations", "Operaciones de conjuntos", SkillLevel.L1),
            ("cardinality", "Cardinalidad", SkillLevel.L1),
            ("ordinal_theory", "Teoría ordinal", SkillLevel.L1),
            ("axiom_choice", "Axioma de elección", SkillLevel.L1),
            ("cantor_theorem", "Teorema de Cantor", SkillLevel.L1),
        ],
        "topology": [
            ("open_closed_sets", "Conjuntos abiertos/cerrados", SkillLevel.L1),
            ("compactness", "Compacidad", SkillLevel.L1),
            ("connectedness", "Conexidad", SkillLevel.L1),
            ("homeomorphism", "Homeomorfismo", SkillLevel.L1),
            ("homotopy_theory", "Teoría de homotopía", SkillLevel.L1),
        ],
    }

    for skill_id, name, level in category_skills.get(category, []):
        graph.add_skill(SkillNode(skill_id=skill_id, name=name, level=level))

    return graph


# ──────────────────────────────────────────────
# Estado simulado para entrenamiento supervisado
# ──────────────────────────────────────────────

def record_to_state(rec: Dict[str, Any], graph, category: str):
    """Convierte un registro JSONL en un State para el agente."""
    from nucleo.types import State

    query = rec.get("problem", rec.get("query", ""))
    goal = rec.get("solution", rec.get("answer", ""))

    state = State(
        query=query,
        goal=goal,
        skill_graph=graph,
        context={"category": category, "source": rec.get("source", "")},
    )
    return state


# ──────────────────────────────────────────────
# Entrenamiento supervisado por categoría
# ──────────────────────────────────────────────

def train_category(
    category: str,
    args: argparse.Namespace,
) -> Dict[str, float]:
    """Entrena el agente de una categoría. Retorna métricas finales."""
    import torch
    from nucleo.rl.agent import NucleoAgent, AgentConfig
    from nucleo.rl.mdp import Transition
    from nucleo.types import ActionType

    logger.info(f"\n{'='*60}")
    logger.info(f"Entrenando agente: {category.upper()}")
    logger.info(f"{'='*60}")

    # Cargar datos
    train_data = load_category_data(category, "train")
    val_data = load_category_data(category, "val")

    if not train_data:
        logger.warning(f"[{category}] Sin datos de entrenamiento, saltando.")
        return {"skipped": True}

    logger.info(f"[{category}] Train: {len(train_data)} | Val: {len(val_data)}")

    # Construir grafo + agente
    graph = build_category_skill_graph(category)
    config = AgentConfig(
        hidden_dim=256,
        learning_rate=args.lr,
        batch_size=args.batch_size,
    )
    agent = NucleoAgent(skill_graph=graph, config=config, use_neural=True)

    # Cargar pesos base si existen
    if BASE_WEIGHTS.exists():
        try:
            state_dict = torch.load(str(BASE_WEIGHTS), map_location="cpu")
            agent.network.load_state_dict(state_dict, strict=False)
            logger.info(f"[{category}] Pesos base cargados desde {BASE_WEIGHTS}")
        except Exception as e:
            logger.warning(f"[{category}] No se cargaron pesos base: {e}")

    # Cargar checkpoint específico si existe
    cat_checkpoint = CHECKPOINT_DIR / f"multiagent_{category}_best.pt"
    if cat_checkpoint.exists():
        try:
            ckpt = torch.load(str(cat_checkpoint), map_location="cpu")
            agent.network.load_state_dict(ckpt.get("network", ckpt), strict=False)
            if "optimizer" in ckpt:
                agent.optimizer.load_state_dict(ckpt["optimizer"])
            logger.info(f"[{category}] Checkpoint propio cargado")
        except Exception as e:
            logger.warning(f"[{category}] No se cargó checkpoint propio: {e}")

    best_val_acc = 0.0
    metrics_history = []

    for epoch in range(1, args.epochs + 1):
        # ── Fase supervisada ──
        agent.network.train()
        np.random.shuffle(train_data)
        epoch_correct = 0
        epoch_total = 0
        epoch_loss = 0.0

        batches = [
            train_data[i : i + args.batch_size]
            for i in range(0, len(train_data), args.batch_size)
        ]

        for batch in batches:
            transitions = []
            for rec in batch:
                state = record_to_state(rec, graph, category)
                action = agent.select_action(state)
                # Recompensa: ASSIST siempre correcto para matemáticas
                reward = 1.0 if action.action_type == ActionType.ASSIST else 0.0
                next_state = state  # simplificado
                transitions.append(
                    Transition(
                        state=state,
                        action=action,
                        reward=reward,
                        next_state=next_state,
                        done=True,
                    )
                )
                epoch_correct += int(action.action_type == ActionType.ASSIST)
                epoch_total += 1

            metrics = agent.update(transitions)
            epoch_loss += metrics.get("loss", 0.0)

        train_acc = epoch_correct / max(epoch_total, 1)
        avg_loss = epoch_loss / max(len(batches), 1)

        # ── Validación ──
        val_acc = 0.0
        if val_data:
            agent.network.eval()
            val_correct = sum(
                1
                for rec in val_data
                if agent.select_action(
                    record_to_state(rec, graph, category)
                ).action_type == ActionType.ASSIST
            )
            val_acc = val_correct / len(val_data)

        logger.info(
            f"[{category}] Época {epoch}/{args.epochs} | "
            f"loss={avg_loss:.4f} | train_acc={train_acc:.3f} | val_acc={val_acc:.3f}"
        )

        # ── Guardar mejor checkpoint ──
        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
            torch.save(
                {
                    "network": agent.network.state_dict(),
                    "optimizer": agent.optimizer.state_dict(),
                    "epoch": epoch,
                    "val_acc": val_acc,
                    "category": category,
                },
                str(cat_checkpoint),
            )

        metrics_history.append(
            {"epoch": epoch, "loss": avg_loss, "train_acc": train_acc, "val_acc": val_acc}
        )

    # ── Guardar pesos finales en data/agents/ ──
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    final_path = WEIGHTS_DIR / f"{category}.pt"
    torch.save(
        {
            "network": agent.network.state_dict(),
            "optimizer": agent.optimizer.state_dict(),
            "category": category,
            "best_val_acc": best_val_acc,
        },
        str(final_path),
    )
    logger.info(f"[{category}] Pesos finales guardados: {final_path}")
    logger.info(f"[{category}] Mejor val_acc: {best_val_acc:.3f}")

    return {
        "category": category,
        "train_samples": len(train_data),
        "best_val_acc": best_val_acc,
        "epochs": args.epochs,
    }


# ──────────────────────────────────────────────
# Entrenamiento PPO con recompensa Lean (Fase 2)
# ──────────────────────────────────────────────

def train_category_ppo_lean(category: str, args: argparse.Namespace) -> Dict[str, float]:
    """PPO con recompensa real de Lean (more expensive, more accurate)."""
    # Importar función de recompensa del script principal
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from train_gnn_ppo import _lean_reward
    except ImportError:
        logger.error("No se pudo importar _lean_reward de train_gnn_ppo.py")
        return train_category(category, args)

    import torch
    from nucleo.rl.agent import NucleoAgent, AgentConfig
    from nucleo.rl.mdp import Transition
    from nucleo.types import ActionType

    train_data = load_category_data(category, "train")
    if not train_data:
        return {"skipped": True}

    graph = build_category_skill_graph(category)
    config = AgentConfig(learning_rate=args.lr, batch_size=args.batch_size)
    agent = NucleoAgent(skill_graph=graph, config=config, use_neural=True)

    # Cargar checkpoint propio si existe
    cat_checkpoint = CHECKPOINT_DIR / f"multiagent_{category}_best.pt"
    if cat_checkpoint.exists():
        ckpt = torch.load(str(cat_checkpoint), map_location="cpu")
        agent.network.load_state_dict(ckpt.get("network", ckpt), strict=False)

    best_reward = 0.0

    for epoch in range(1, args.ppo_epochs + 1):
        transitions = []
        total_reward = 0.0
        sample = train_data[: min(500, len(train_data))]  # 500 por época PPO

        for rec in sample:
            state = record_to_state(rec, graph, category)
            action = agent.select_action(state)

            problem = rec.get("problem", "")
            reward = _lean_reward(problem, lean_client=None, rec=rec)
            if action.action_type != ActionType.ASSIST:
                reward = min(reward - 0.5, 0.0)

            transitions.append(
                Transition(state=state, action=action, reward=reward, next_state=state, done=True)
            )
            total_reward += reward

        agent.update(transitions)
        avg_reward = total_reward / max(len(sample), 1)
        logger.info(f"[{category}] PPO época {epoch}/{args.ppo_epochs} | avg_reward={avg_reward:.4f}")

        if avg_reward > best_reward:
            best_reward = avg_reward
            CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
            torch.save(
                {"network": agent.network.state_dict(), "category": category, "reward": avg_reward},
                str(cat_checkpoint),
            )

    # Guardar pesos finales
    final_path = WEIGHTS_DIR / f"{category}.pt"
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    torch.save({"network": agent.network.state_dict(), "category": category}, str(final_path))

    return {"category": category, "best_reward": best_reward}


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Entrenar 14 agentes especializados NLE v7.0")
    p.add_argument(
        "--categories", nargs="*", default=None,
        help="Categorías a entrenar. Por defecto: todas.",
    )
    p.add_argument("--epochs", type=int, default=10, help="Épocas de entrenamiento supervisado")
    p.add_argument("--ppo-epochs", type=int, default=5, help="Épocas PPO con Lean (solo con --with-lean)")
    p.add_argument("--batch-size", type=int, default=128, help="Tamaño de batch")
    p.add_argument("--lr", type=float, default=3e-4, help="Learning rate")
    p.add_argument("--with-lean", action="store_true", help="PPO con recompensa Lean real (lento)")
    p.add_argument("--dry-run", action="store_true", help="Mostrar info sin entrenar")
    return p.parse_args()


def main():
    args = parse_args()

    categories_to_train = args.categories if args.categories else CATEGORIES

    # Validar categorías
    invalid = [c for c in categories_to_train if c not in CATEGORIES]
    if invalid:
        logger.error(f"Categorías inválidas: {invalid}")
        sys.exit(1)

    logger.info(f"Categorías a entrenar: {categories_to_train}")
    logger.info(f"Épocas: {args.epochs} | Batch: {args.batch_size} | LR: {args.lr}")
    if args.with_lean:
        logger.info(f"PPO con Lean: {args.ppo_epochs} épocas")

    # Verificar datos disponibles
    logger.info("\nDisponibilidad de datos:")
    for cat in categories_to_train:
        train_path = DATA_DIR / cat / "train.jsonl"
        n = sum(1 for _ in open(train_path, encoding="utf-8")) if train_path.exists() else 0
        logger.info(f"  {cat:<20}: {n:>6} ejemplos de entrenamiento")

    if args.dry_run:
        logger.info("\nDry-run completado. No se entrenó ningún agente.")
        return

    # Entrenar
    all_results = []
    t0 = time.time()

    for cat in categories_to_train:
        if args.with_lean:
            results = train_category_ppo_lean(cat, args)
        else:
            results = train_category(cat, args)
        all_results.append(results)

    # Resumen final
    elapsed = time.time() - t0
    logger.info(f"\n{'='*60}")
    logger.info(f"ENTRENAMIENTO COMPLETADO en {elapsed/60:.1f} min")
    logger.info(f"{'='*60}")
    logger.info(f"\n{'Categoría':<22} {'Train':<8} {'Val Acc':>8}")
    logger.info("-" * 42)
    for r in all_results:
        if r.get("skipped"):
            logger.info(f"  {r.get('category', '?'):<20} {'SIN DATOS':>10}")
        else:
            logger.info(
                f"  {r.get('category', '?'):<20} "
                f"{r.get('train_samples', 0):>8} "
                f"{r.get('best_val_acc', r.get('best_reward', 0)):.3f}"
            )

    # Guardar resumen JSON
    summary_path = WEIGHTS_DIR / "training_summary.json"
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    logger.info(f"\nResumen guardado en {summary_path}")


if __name__ == "__main__":
    main()
