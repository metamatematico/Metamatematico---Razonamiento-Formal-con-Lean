"""
MES Bridge — conexión entre los 14 agentes especializados y el sistema MES.
===========================================================================

Implementa la arquitectura MES completa para los agentes multi-categoría:

  Cada SpecializedAgent es un co-regulador L1 con:
  - ProceduralMemory propia (tácticas exitosas por categoría)
  - Conexión al PatternManager global (patrones compartidos)
  - Reporte al ColimitBuilder cuando convergen dos agentes en un problema

  Cuando dos o más agentes resuelven un mismo problema por rutas distintas,
  el ColimitBuilder construye una skill emergente (colímite) que captura
  la solución más general — conforme al Teorema 2.10 del paper v7.0.

Flujo:
  query → agente_cat → Lean → éxito
                              ↓
                    MESBridge.record_success()
                              ↓
                    ProceduralMemory[cat].add_procedure()
                    PatternManager.update_or_create()
                              ↓
                    ¿Otro agente resolvió lo mismo?
                              ↓ sí
                    ColimitBuilder → SkillNodo emergente
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


@dataclass
class AgentSolution:
    """Registro de una solución encontrada por un agente."""
    category: str
    query: str
    tactic: str
    lean_result: str          # "success" | "partial" | "failed"
    reward: float
    timestamp: datetime = field(default_factory=datetime.now)
    pattern_id: str = ""      # ID del patrón MES asociado


class MESBridge:
    """
    Puente entre los SpecializedAgents y el sistema MES (PatternManager,
    ColimitBuilder, ProceduralMemory global).

    Cada instancia es compartida por todos los agentes vía el orquestador.
    """

    def __init__(
        self,
        pattern_manager=None,
        colimit_builder=None,
        skill_graph=None,
    ):
        """
        Args:
            pattern_manager: PatternManager del sistema MES.
            colimit_builder: ColimitBuilder del sistema MES.
            skill_graph:     SkillCategory global (para registrar skills emergentes).
        """
        self.pattern_manager = pattern_manager
        self.colimit_builder = colimit_builder
        self.skill_graph = skill_graph

        # ProceduralMemory por categoría (cada agente tiene la suya)
        self._procedural_memories: Dict[str, Any] = {}

        # Historial de soluciones por query_hash → lista de AgentSolution
        # Usado para detectar convergencia entre agentes
        self._solutions_by_query: Dict[str, List[AgentSolution]] = {}

        # Skills emergentes creadas por convergencia
        self._emergent_skills: List[Dict[str, Any]] = []

        # Estadísticas
        self.total_recorded = 0
        self.total_emergent = 0

    def get_memory(self, category: str):
        """Obtiene (o crea) la ProceduralMemory para una categoría."""
        if category not in self._procedural_memories:
            try:
                from nucleo.mes.memory import ProceduralMemory
                self._procedural_memories[category] = ProceduralMemory(
                    max_procedures=500
                )
            except ImportError:
                self._procedural_memories[category] = _FallbackMemory(category)
        return self._procedural_memories[category]

    def record_success(
        self,
        category: str,
        query: str,
        tactic: str,
        lean_result: str,
        reward: float,
        skill_ids: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Registra una solución exitosa de un agente especializado.

        1. Guarda en ProceduralMemory de la categoría.
        2. Crea o actualiza patrón en PatternManager global.
        3. Comprueba si otro agente ya resolvió la misma query (convergencia).
        4. Si hay convergencia → llama a ColimitBuilder para skill emergente.

        Args:
            category:    Categoría del agente ("algebra", "geometry", etc.)
            query:       Texto del problema
            tactic:      Táctica Lean usada ("norm_num", "simp", etc.)
            lean_result: "success" | "partial" | "failed"
            reward:      Recompensa recibida (0.0 - 1.0)
            skill_ids:   Skills del grafo activadas (para el patrón)

        Returns:
            ID del patrón creado o None
        """
        self.total_recorded += 1
        success = lean_result == "success" or reward >= 0.8

        # 1. ProceduralMemory de la categoría
        memory = self.get_memory(category)
        pattern_id = f"pat_{category}_{hash(query) % 100000:05d}"
        memory.add_procedure(
            pattern_id=pattern_id,
            action_sequence=[tactic],
            success=success,
            query_text=query,
            tactic_used=tactic,
        )

        # 2. PatternManager global
        if self.pattern_manager is not None and skill_ids:
            try:
                pat = self.pattern_manager.create_pattern(
                    component_ids=skill_ids,
                    distinguished_links=[],
                    metadata={
                        "category": category,
                        "tactic": tactic,
                        "reward": reward,
                        "query_snippet": query[:80],
                    },
                    graph=self.skill_graph,
                )
                pattern_id = pat.id
            except Exception as e:
                logger.debug(f"PatternManager.create_pattern error: {e}")

        # 3. Registrar en historial de convergencia
        solution = AgentSolution(
            category=category,
            query=query,
            tactic=tactic,
            lean_result=lean_result,
            reward=reward,
            pattern_id=pattern_id,
        )
        qhash = _query_hash(query)
        if qhash not in self._solutions_by_query:
            self._solutions_by_query[qhash] = []
        self._solutions_by_query[qhash].append(solution)

        # 4. Detectar convergencia entre agentes
        existing = self._solutions_by_query[qhash]
        categories_solved = {s.category for s in existing if s.reward >= 0.5}
        if len(categories_solved) >= 2:
            self._handle_convergence(query, existing, categories_solved)

        return pattern_id

    def _handle_convergence(
        self,
        query: str,
        solutions: List[AgentSolution],
        categories: set,
    ) -> None:
        """
        Dos o más agentes resolvieron el mismo problema.
        Construye una skill emergente (colímite) que captura la solución general.
        """
        cats_str = "+".join(sorted(categories))
        emergent_id = f"emergent_{cats_str}_{hash(query) % 10000:04d}"

        # Verificar que no existe ya
        if any(e["id"] == emergent_id for e in self._emergent_skills):
            return

        logger.info(
            f"Convergencia detectada: [{cats_str}] en query {query[:50]!r}"
        )

        # Colímite real si está disponible
        if self.colimit_builder is not None and self.skill_graph is not None:
            try:
                from nucleo.mes.patterns import Pattern as MESPattern
                skill_ids = [f"skill_{c}" for c in categories]
                pat = None
                if self.pattern_manager:
                    pat = self.pattern_manager.create_pattern(
                        component_ids=skill_ids,
                        distinguished_links=[],
                        metadata={"convergence": True, "categories": list(categories)},
                        graph=self.skill_graph,
                    )
                if pat:
                    colimit = self.colimit_builder.build_colimit(pat, self.skill_graph)
                    logger.info(f"Skill emergente construida: {colimit}")
            except Exception as e:
                logger.debug(f"ColimitBuilder error (no bloqueante): {e}")

        # Registrar skill emergente
        emergent = {
            "id": emergent_id,
            "categories": list(categories),
            "query_snippet": query[:100],
            "tactics": list({s.tactic for s in solutions}),
            "avg_reward": sum(s.reward for s in solutions) / len(solutions),
            "created_at": datetime.now().isoformat(),
        }
        self._emergent_skills.append(emergent)
        self.total_emergent += 1

        # Añadir al grafo de skills si está disponible
        if self.skill_graph is not None:
            try:
                from nucleo.graph.skills import SkillNode, SkillLevel
                node = SkillNode(
                    skill_id=emergent_id,
                    name=f"Emergent: {cats_str}",
                    level=SkillLevel.L2,
                    metadata={"emergent": True, "categories": list(categories)},
                )
                self.skill_graph.add_skill(node)
                logger.info(f"Skill emergente añadida al grafo: {emergent_id}")
            except Exception as e:
                logger.debug(f"No se pudo añadir skill emergente al grafo: {e}")

    def query_best_tactic(self, category: str, query: str) -> Optional[str]:
        """
        Consulta la mejor táctica conocida para una query en esta categoría.
        Busca primero en la memoria propia, luego en otras categorías.

        Returns:
            Nombre de la táctica o None si no hay historial.
        """
        # Memoria propia
        memory = self.get_memory(category)
        pattern_id = f"pat_{category}_{hash(query) % 100000:05d}"
        try:
            proc = memory.get_best_for_query(query)
            if proc and proc.tactic_used:
                return proc.tactic_used
        except Exception:
            pass

        # Buscar en convergencias registradas
        qhash = _query_hash(query)
        solutions = self._solutions_by_query.get(qhash, [])
        if solutions:
            best = max(solutions, key=lambda s: s.reward)
            if best.reward >= 0.5:
                return best.tactic

        return None

    def stats(self) -> Dict[str, Any]:
        """Estadísticas del bridge MES."""
        return {
            "total_recorded": self.total_recorded,
            "total_emergent": self.total_emergent,
            "categories_with_memory": list(self._procedural_memories.keys()),
            "convergent_queries": len([
                k for k, v in self._solutions_by_query.items()
                if len({s.category for s in v}) >= 2
            ]),
            "emergent_skills": [e["id"] for e in self._emergent_skills[-10:]],
        }

    def print_stats(self):
        s = self.stats()
        print(f"\n=== MES Bridge Stats ===")
        print(f"  Soluciones registradas : {s['total_recorded']}")
        print(f"  Skills emergentes      : {s['total_emergent']}")
        print(f"  Queries convergentes   : {s['convergent_queries']}")
        print(f"  Memorias por categoría : {len(s['categories_with_memory'])}")
        if s['emergent_skills']:
            print(f"  Últimas emergentes     : {s['emergent_skills']}")


# ──────────────────────────────────────────────────────────────────────────────
# Fallback cuando MES no está disponible
# ──────────────────────────────────────────────────────────────────────────────

class _FallbackMemory:
    """ProceduralMemory mínima cuando el import MES falla."""

    def __init__(self, category: str):
        self.category = category
        self._records: list = []

    def add_procedure(self, pattern_id, action_sequence, success=True,
                      query_text="", tactic_used="", lean_goal=""):
        self._records.append({
            "pattern_id": pattern_id,
            "tactic": tactic_used,
            "success": success,
            "query": query_text[:80],
        })

    def get_best_for_query(self, query: str):
        matches = [r for r in self._records if r["success"] and
                   any(w in query.lower() for w in r["query"].lower().split()[:5])]
        return matches[-1] if matches else None


# ──────────────────────────────────────────────────────────────────────────────
# Utilidades
# ──────────────────────────────────────────────────────────────────────────────

def _query_hash(query: str) -> str:
    """Hash estable de una query para detectar duplicados entre agentes."""
    # Normalizar: minúsculas, sin espacios extra, primeras 200 chars
    normalized = " ".join(query.lower().split())[:200]
    return f"qh_{hash(normalized) % 1_000_000:06d}"
