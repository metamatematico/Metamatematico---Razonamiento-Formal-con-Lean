"""
SpecializedAgent — agente especializado en una categoría matemática.
====================================================================

Cada instancia envuelve un NucleoAgent heurístico y lleva la memoria
procedimental de su categoría a través del MES Bridge compartido. Hubo pesos
GNN+PPO por categoría; se retiraron con la red (ver `nucleo/rl/agent.py`).
"""

from __future__ import annotations

import os
import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# LA taxonomia vive en pillars/math_domains.py, derivada de las propias
# habilidades: es la imagen del funtor pi. Esta lista estaba escrita a mano
# en cinco sitios de tres subsistemas, atadas solo por un comentario.
from nucleo.pillars.math_domains import CATEGORIAS_DE_DOMINIO

CATEGORIES: List[str] = CATEGORIAS_DE_DOMINIO

# Palabras clave para clasificación rápida (subconjunto compacto)
_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "algebra": ["polynomial", "ring", "field", "group", "linear", "matrix", "vector",
                "equation", "factor", "root", "eigenvalue", "ideal", "module",
                # español
                "grupo", "anillo", "campo", "modulo", "polinomio", "ecuacion",
                "algebra", "conmutativ", "abelian"],
    "analysis": ["limit", "continuity", "derivative", "integral", "series", "convergence",
                 "measure", "metric", "sequence", "cauchy", "real analysis", "complex",
                 # español
                 "limite", "continuid", "derivada", "integral", "serie", "convergencia",
                 "medida", "sucesion", "analisis real", "analisis complejo"],
    "category-theory": ["functor", "morphism", "category", "adjoint", "topos", "natural transformation",
                        "colimit", "pushout", "pullback", "yoneda", "monad",
                        # español
                        "funtor", "morfismo", "categoria", "colimite", "adjunto", "transformacion natural"],
    "combinatorics": ["combinat", "permutation", "combination", "graph coloring", "chromatic",
                      "partition", "enumerat", "pigeonhole", "binomial", "catalan",
                      # español
                      "combinatoria", "permutacion", "combinacion", "coloracion", "particion"],
    "computation": ["algorithm", "complexity", "computab", "turing", "automaton", "recursion",
                    "decidab", "halting", "polynomial time", "np-hard",
                    # español
                    "algoritmo", "complejidad", "computabilidad", "automatón", "decidib", "recursion"],
    "geometry": ["triangle", "circle", "angle", "polygon", "area", "volume", "euclidean",
                 "coordinate", "distance", "convex hull", "conic", "perpendicular",
                 # español
                 "triangulo", "circulo", "angulo", "poligono", "euclidiana", "coordenada",
                 "distancia", "perpendicular", "geometria"],
    "lean-tactics": ["lean", "mathlib", "lean4", "tactic", "simp", "ring_nf",
                     "norm_num", "omega", "linarith", "cases", "exact", "apply", "rw", "have",
                     "lean proof", "lean theorem", "by simp", "by ring",
                     # español
                     "tactica", "verificador lean", "prueba lean"],
    "logic": ["propositional", "predicate", "satisfiab", "validity", "inference", "entailment",
              "modal", "boolean", "truth table", "quantifier", "axiom", "implication",
              "logical formula", "tautology", "first-order", "fol",
              # español
              "logica", "proposicional", "predicado", "validez", "inferencia",
              "cuantificador", "formula logica", "tautologia", "primer orden",
              "deduccion logica", "logica modal", "logica clasica"],
    "number-theory": ["prime", "divisib", "congruence", "modular", "diophantine", "gcd", "lcm",
                      "euler", "fermat", "number theory", "arithmetic", "integer",
                      "irrational", "rational number", "sqrt(2)", "floor", "ceiling",
                      "perfect square", "fibonacci", "pythagorean",
                      # español
                      "primo", "divisibilidad", "congruencia", "modular", "diofantin",
                      "teoria de numeros", "aritmetica", "entero", "irracional",
                      "numero racional", "raiz cuadrada", "cuadrado perfecto"],
    "optimization": ["maximiz", "minimiz", "gradient", "convex optim", "linear program",
                     "constraint", "lagrange", "objective", "optim", "loss function",
                     # español
                     "maximizar", "minimizar", "gradiente", "optimizacion", "restriccion",
                     "programacion lineal", "objetivo", "funcion de perdida"],
    "probability": ["probability", "random variable", "expectation", "variance", "distribution",
                    "markov", "bayes", "stochastic", "statistic", "sample space",
                    "p(a|b)", "p(a", "bernoulli", "binomial distribution", "normal distribution",
                    "expected value", "random walk",
                    # español
                    "probabilidad", "variable aleatoria", "esperanza", "varianza",
                    "distribucion", "estocastico", "estadistica", "espacio muestral"],
    "proof-strategies": ["induction", "contradiction", "contrapositive", "direct proof",
                         "existence", "uniqueness", "well-ordering", "pigeonhole",
                         # español
                         "induccion", "contradiccion", "contrapositivo", "prueba directa",
                         "existencia", "unicidad", "buen orden"],
    "set-theory": ["set", "subset", "union", "intersection", "cardinality", "ordinal",
                   "zfc", "axiom of choice", "cantor", "power set", "bijection",
                   # español
                   "conjunto", "subconjunto", "union", "interseccion", "cardinalidad",
                   "ordinal", "axioma de eleccion", "conjunto potencia", "biyeccion"],
    "topology": ["topology", "open set", "closed set", "compact", "connected", "homeomorphism",
                 "manifold", "homotopy", "continuous map", "hausdorff",
                 # español
                 "topologia", "abierto", "cerrado", "compacto", "conexo", "homeomorfismo",
                 "variedad", "homotopia", "hausdorff", "espacio topologico"],
}

# Pesos por defecto (directorio donde cada agente guarda sus pesos)
_DEFAULT_WEIGHTS_DIR = Path(__file__).parent.parent.parent / "training" / "agents" / "best"


def classify_query(text: str) -> str:
    """Clasifica un texto en una de las 14 categorías.

    Retorna la categoría con más coincidencias de palabras clave. El empate lo
    gana la coincidencia MÁS LARGA, y sin ninguna coincidencia se responde la
    clase mayoritaria.

    EL DESEMPATE ERA UNA CONSTANTE DISFRAZADA
    -----------------------------------------
    Esto hacía `max(scores, key=...)`, que ante un empate devuelve la PRIMERA
    clave del diccionario. Y la primera es `algebra`. No había criterio
    detrás: era el orden de una lista.

    Ante «Is the square root of 2 irrational?»:

        algebra        1   por «root»
        number-theory  1   por «irrational»

    y ganaba álgebra. Que además es la clase mayoritaria del banco —88,9 % en
    crudo—, así que ese desempate inflaba la exactitud cruda y hundía la
    equilibrada: la forma exacta de fallo contra la que existe la regla de
    medir con modelo nulo.

    UNA COINCIDENCIA LARGA ES MÁS ESPECÍFICA QUE UNA CORTA. «irrational» dice
    mucho más que «root», que sale en media biblioteca. Medido sobre las 3 000
    consultas etiquetadas de MATH+GSM8K (`scripts/parada_y_desempate.py`):

        variante                        equilibrada    cruda
        modelo nulo (siempre álgebra)        33,33 %   88,97 %
        empate → la primera de la lista      58,72 %   61,20 %
        empate → la coincidencia más larga   62,07 %   60,35 %

    +3,35 puntos de exactitud equilibrada, que es la que vale aquí: la cruda
    sobre un banco 88,9 % álgebra premia justo el fallo que se corrige.

    Y SE PROBÓ TAMBIÉN A CASAR CON LÍMITES DE PALABRA —`\\bprime\\b` en vez de
    `"prime" in texto`— Y SALE PEOR: 55,47 % equilibrada, 3,25 puntos por
    debajo de hoy. Las dos juntas dan 57,49 %, también peor. Queda escrito
    para que nadie lo intente otra vez sin medirlo: la subcadena está
    recogiendo plurales y derivados que los límites de palabra tiran.
    """
    text_lower = text.lower()
    aciertos: Dict[str, list] = {cat: [] for cat in CATEGORIES}
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        aciertos[cat] = [kw for kw in keywords if kw in text_lower]

    mejor = max((len(v) for v in aciertos.values()), default=0)
    if mejor == 0:
        # EL SUELO VA DECLARADO: sin ninguna coincidencia se responde la clase
        # mayoritaria, que es exactamente lo que hace el modelo nulo. Eso no
        # es un acierto del clasificador y no se cuenta como tal.
        return "algebra"

    empatadas = [c for c in CATEGORIES if len(aciertos[c]) == mejor]
    if len(empatadas) == 1:
        return empatadas[0]
    return max(empatadas,
               key=lambda c: (max(len(k) for k in aciertos[c]),
                              sum(len(k) for k in aciertos[c])))


class SpecializedAgent:
    """Agente especializado en una categoría matemática.

    Envuelve a NucleoAgent y añade:
    - categoría explícita
    - la memoria procedimental de su categoría (MES Bridge)
    - estadísticas de uso
    """

    def __init__(
        self,
        category: str,
        mes_bridge=None,
    ):
        if category not in CATEGORIES:
            raise ValueError(f"Categoría desconocida: {category!r}. Válidas: {CATEGORIES}")
        self.category = category

        # MES Bridge — conexión con PatternManager + ColimitBuilder
        # Puede ser None (modo independiente) o compartido entre todos los agentes
        self.mes_bridge = mes_bridge

        # Estadísticas
        self.calls: int = 0
        self.correct: int = 0

        # Agente subyacente (lazy load)
        self._agent = None

    def _load_agent(self):
        from nucleo.graph.category import SkillCategory
        from nucleo.rl.agent import NucleoAgent
        return NucleoAgent(graph=SkillCategory(name=f"agent_{self.category}"))

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
        # Consultar mejor táctica conocida antes de la heurística
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
        """Pasa las transiciones al agente subyacente."""
        return self.agent.update(transitions)

    def stats(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "calls": self.calls,
        }

    def __repr__(self) -> str:
        return f"SpecializedAgent(category={self.category!r}, calls={self.calls})"
