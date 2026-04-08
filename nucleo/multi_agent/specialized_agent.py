"""
SpecializedAgent — agente especializado en una categoría matemática.
====================================================================

Cada instancia es un NucleoAgent (GNN+PPO) entrenado exclusivamente
en problemas de su categoría. Carga pesos propios si existen.
"""

from __future__ import annotations

import os
import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# 14 categorías NLE — deben coincidir con balance_datasets.py
CATEGORIES: List[str] = [
    "algebra",
    "analysis",
    "category-theory",
    "combinatorics",
    "computation",
    "geometry",
    "lean-tactics",
    "logic",
    "number-theory",
    "optimization",
    "probability",
    "proof-strategies",
    "set-theory",
    "topology",
]

# Palabras clave para clasificación rápida (subconjunto compacto)
_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "algebra": ["polynomial", "ring", "field", "group", "linear", "matrix", "vector",
                "equation", "factor", "root", "eigenvalue", "ideal", "module"],
    "analysis": ["limit", "continuity", "derivative", "integral", "series", "convergence",
                 "measure", "metric", "sequence", "cauchy", "real analysis", "complex"],
    "category-theory": ["functor", "morphism", "category", "adjoint", "topos", "natural transformation",
                        "colimit", "pushout", "pullback", "yoneda", "monad"],
    "combinatorics": ["combinat", "permutation", "combination", "graph coloring", "chromatic",
                      "partition", "enumerat", "pigeonhole", "binomial", "catalan"],
    "computation": ["algorithm", "complexity", "computab", "turing", "automaton", "recursion",
                    "decidab", "halting", "polynomial time", "np-hard"],
    "geometry": ["triangle", "circle", "angle", "polygon", "area", "volume", "euclidean",
                 "coordinate", "distance", "convex", "conic", "perpendicular"],
    "lean-tactics": ["lean", "mathlib", "lean4", "tactic", "simp", "ring_nf",
                     "norm_num", "omega", "linarith", "cases", "exact", "apply", "rw", "have",
                     "lean proof", "lean theorem", "by simp", "by ring"],
    "logic": ["propositional", "predicate", "satisfiab", "validity", "inference", "entailment",
              "modal", "boolean", "truth table", "quantifier", "axiom", "implication",
              "logical formula", "tautology", "first-order"],
    "number-theory": ["prime", "divisib", "congruence", "modular", "diophantine", "gcd", "lcm",
                      "euler", "fermat", "number theory", "arithmetic", "integer",
                      "irrational", "rational number", "sqrt(2)", "floor", "ceiling",
                      "perfect square", "fibonacci", "pythagorean"],
    "optimization": ["maximiz", "minimiz", "gradient", "convex optim", "linear program",
                     "constraint", "lagrange", "objective", "optim", "loss function"],
    "probability": ["probability", "random variable", "expectation", "variance", "distribution",
                    "markov", "bayes", "stochastic", "statistic", "sample space",
                    "p(a|b)", "p(a", "bernoulli", "binomial distribution", "normal distribution",
                    "expected value", "random walk"],
    "proof-strategies": ["induction", "contradiction", "contrapositive", "direct proof",
                         "existence", "uniqueness", "well-ordering", "pigeonhole"],
    "set-theory": ["set", "subset", "union", "intersection", "cardinality", "ordinal",
                   "zfc", "axiom of choice", "cantor", "power set", "bijection"],
    "topology": ["topology", "open set", "closed set", "compact", "connected", "homeomorphism",
                 "manifold", "homotopy", "continuous map", "hausdorff"],
}

# Pesos por defecto (directorio donde cada agente guarda sus pesos)
_DEFAULT_WEIGHTS_DIR = Path(__file__).parent.parent.parent / "training" / "agents" / "best"


def classify_query(text: str) -> str:
    """Clasifica un texto en una de las 14 categorías.

    Retorna la categoría con más coincidencias de palabras clave.
    Si empate → 'algebra' (más general).
    """
    text_lower = text.lower()
    scores: Dict[str, int] = {cat: 0 for cat in CATEGORIES}
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[cat] += 1
    best = max(scores, key=lambda c: scores[c])
    return best if scores[best] > 0 else "algebra"


class SpecializedAgent:
    """Agente GNN+PPO especializado en una categoría matemática.

    Envuelve a NucleoAgent y añade:
    - categoría explícita
    - ruta de pesos por categoría
    - estadísticas de uso
    """

    def __init__(
        self,
        category: str,
        weights_dir: Optional[Path] = None,
        use_neural: bool = True,
        mes_bridge=None,
    ):
        if category not in CATEGORIES:
            raise ValueError(f"Categoría desconocida: {category!r}. Válidas: {CATEGORIES}")
        self.category = category
        self.weights_dir = Path(weights_dir) if weights_dir else _DEFAULT_WEIGHTS_DIR
        self.weights_path = self.weights_dir / f"{category}.pt"
        self.use_neural = use_neural

        # MES Bridge — conexión con PatternManager + ColimitBuilder
        # Puede ser None (modo independiente) o compartido entre todos los agentes
        self.mes_bridge = mes_bridge

        # Estadísticas
        self.calls: int = 0
        self.correct: int = 0

        # Agente subyacente (lazy load)
        self._agent = None

    def _load_agent(self):
        """Carga NucleoAgent con los pesos de esta categoría."""
        from nucleo.graph.category import SkillCategory
        from nucleo.rl.agent import NucleoAgent, AgentConfig

        config = AgentConfig()
        agent = NucleoAgent(
            graph=SkillCategory(name=f"agent_{self.category}"),
            config=config,
            use_neural=self.use_neural,
        )

        # Cargar pesos específicos si existen
        if self.weights_path.exists():
            try:
                import torch
                state = torch.load(str(self.weights_path), map_location="cpu",
                                   weights_only=False)
                if isinstance(state, dict) and "network" in state:
                    agent._network.load_state_dict(state["network"])
                    if "optimizer" in state and agent._optimizer is not None:
                        agent._optimizer.load_state_dict(state["optimizer"])
                    logger.info(f"[{self.category}] Pesos cargados desde {self.weights_path}")
                else:
                    agent._network.load_state_dict(state)
                    logger.info(f"[{self.category}] Pesos (state_dict) cargados")
            except Exception as e:
                logger.warning(f"[{self.category}] No se pudo cargar pesos: {e}")
        else:
            # Intentar pesos base compartidos
            base = Path(__file__).parent.parent.parent / "data" / "neural_agent.json.pt"
            if base.exists():
                try:
                    import torch
                    state = torch.load(str(base), map_location="cpu", weights_only=False)
                    agent._network.load_state_dict(state)
                    logger.info(f"[{self.category}] Usando pesos base compartidos")
                except Exception as e:
                    logger.warning(f"[{self.category}] Pesos base no cargados: {e}")

        return agent

    @property
    def agent(self):
        if self._agent is None:
            self._agent = self._load_agent()
        return self._agent

    def select_action(self, state) -> Any:
        """Delega la selección de acción al agente subyacente.

        Si hay un MES Bridge activo, primero consulta si hay una táctica
        conocida para esta query (memoria procedimental).
        """
        self.calls += 1
        # Consultar mejor táctica conocida antes de usar la red neuronal
        if self.mes_bridge is not None:
            query = getattr(state, "query", "") or str(state)
            best_tactic = self.mes_bridge.query_best_tactic(self.category, query)
            if best_tactic:
                logger.debug(
                    f"[{self.category}] Táctica MES conocida: {best_tactic!r}"
                )
                # Retornar acción ASSIST con la táctica conocida
                from nucleo.types import Action, ActionType
                return Action(
                    action_type=ActionType.ASSIST,
                    tactic=best_tactic,
                    goal=getattr(state, "goal", ""),
                )
        return self.agent.select_action(state)

    def record_solution(
        self,
        query: str,
        tactic: str,
        lean_result: str,
        reward: float,
        skill_ids: Optional[List[str]] = None,
    ) -> None:
        """Registra una solución en el MES Bridge (si está activo).

        Debe llamarse después de cada interacción con Lean para que
        la memoria MES aprenda de las soluciones exitosas.

        Args:
            query:       Texto del problema resuelto
            tactic:      Táctica Lean que funcionó
            lean_result: "success" | "partial" | "failed"
            reward:      Recompensa recibida
            skill_ids:   Skills del grafo activadas (opcional)
        """
        self.correct += int(reward >= 0.8)
        if self.mes_bridge is not None:
            self.mes_bridge.record_success(
                category=self.category,
                query=query,
                tactic=tactic,
                lean_result=lean_result,
                reward=reward,
                skill_ids=skill_ids,
            )

    def update(self, transitions) -> Dict[str, float]:
        """Actualiza los pesos del agente con nuevas transiciones."""
        return self.agent.update(transitions)

    def save_weights(self):
        """Guarda los pesos del agente en su archivo dedicado."""
        import torch
        self.weights_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "network": self.agent.network.state_dict(),
            "optimizer": self.agent.optimizer.state_dict(),
            "category": self.category,
            "calls": self.calls,
        }
        torch.save(state, str(self.weights_path))
        logger.info(f"[{self.category}] Pesos guardados en {self.weights_path}")

    def stats(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "calls": self.calls,
            "weights_exist": self.weights_path.exists(),
        }

    def __repr__(self) -> str:
        return f"SpecializedAgent(category={self.category!r}, calls={self.calls})"
