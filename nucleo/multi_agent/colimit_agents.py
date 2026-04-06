"""
ColimitAgent — cada agente ES el colímite de los skills de su categoría.
========================================================================

En lugar de un agente externo que LEE el grafo de skills, cada agente
es el NODO COLÍMITE construido por ColimitBuilder a partir de los skills
de su categoría. Es el objeto universal que los resume a todos.

Jerarquía:
  L0: skills fundacionales  (parse_query, call_lean, ...)
      │ co-conos
  L1: skills de dominio     (factor_poly, norm_num, ...)
      │ co-conos
  L2: colímite[categoría]   = agente  ← AQUÍ
      │ co-conos
  L3: colímite[colímites]   = orquestador

El agente (colímite L2) tiene:
  - Morfismos de entrada desde todos sus skills (co-cono)
  - Memoria procedimental propia (qué tácticas funcionaron)
  - Capacidad de actualizar sus co-conos cuando llegan skills nuevos
  - Propiedad universal: cualquier solución que use sus skills
    factoriza a través del agente

Referencia: Teorema 2.10 (Complejificación), paper NLE v7.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

# Categorías NLE
CATEGORIES: List[str] = [
    "algebra", "analysis", "category-theory", "combinatorics", "computation",
    "geometry", "lean-tactics", "logic", "number-theory", "optimization",
    "probability", "proof-strategies", "set-theory", "topology",
]


@dataclass
class ColimitAgentState:
    """Estado interno del agente-colímite.

    Equivale al 'estado' del nodo colímite en el grafo:
    qué skills están activos, qué morfismos se han disparado,
    cuál es la solución en curso.
    """
    category: str
    colimit_skill_id: str          # ID del nodo colímite en el grafo
    active_skill_ids: List[str] = field(default_factory=list)
    current_tactic: str = ""
    current_reward: float = 0.0
    cocone_morphism_ids: List[str] = field(default_factory=list)


class ColimitAgent:
    """
    Agente matemático que ES el colímite de los skills de su categoría.

    Construcción:
      1. Se recopilan todos los SkillNodes de la categoría (L0 + L1)
      2. PatternManager crea un patrón con todos ellos
      3. ColimitBuilder construye el colímite → crea un SkillNode L2
         con co-conos verificados desde cada skill componente
      4. Este agente ENVUELVE ese SkillNode L2

    Uso:
      agent = ColimitAgent.build(category, graph, pattern_manager, colimit_builder)
      tactic = agent.select_tactic(query)
      agent.record_result(query, tactic, reward)
    """

    def __init__(
        self,
        category: str,
        colimit_skill,        # Skill (objeto del grafo, nivel L2)
        colimit_obj,          # Colimit (metadata del colímite)
        pattern,              # Pattern (el patrón de skills componentes)
        graph,                # SkillCategory (grafo global)
        pattern_manager,      # PatternManager
        colimit_builder,      # ColimitBuilder
    ):
        self.category = category
        self.colimit_skill = colimit_skill     # nodo L2 en el grafo
        self.colimit_obj = colimit_obj
        self.pattern = pattern
        self.graph = graph
        self.pattern_manager = pattern_manager
        self.colimit_builder = colimit_builder

        # Memoria procedimental propia del colímite
        self._memory: Dict[str, List[dict]] = {}  # query_hash → [resultados]
        self._tactic_success: Dict[str, float] = {}  # tactic → success_rate

        # Estado actual
        self.state = ColimitAgentState(
            category=category,
            colimit_skill_id=colimit_skill.id if colimit_skill else f"col_{category}",
        )

        # Estadísticas
        self.calls = 0
        self.successes = 0

    @classmethod
    def build(
        cls,
        category: str,
        graph,
        pattern_manager,
        colimit_builder,
    ) -> "ColimitAgent":
        """
        Construye el ColimitAgent para una categoría.

        Recopila todos los skills de la categoría del grafo,
        crea el patrón, y llama a ColimitBuilder para obtener
        el nodo colímite L2.

        Args:
            category:        Nombre de la categoría
            graph:           SkillCategory (grafo global de skills)
            pattern_manager: PatternManager del MES
            colimit_builder: ColimitBuilder del MES

        Returns:
            ColimitAgent con el nodo colímite construido y co-conos verificados
        """
        # 1. Recopilar skills de la categoría
        skill_ids = _collect_category_skills(category, graph)

        if not skill_ids:
            logger.warning(
                f"[{category}] No hay skills en el grafo. "
                "Construyendo agente con skills vacíos."
            )
            return cls(
                category=category,
                colimit_skill=_make_stub_skill(category),
                colimit_obj=None,
                pattern=None,
                graph=graph,
                pattern_manager=pattern_manager,
                colimit_builder=colimit_builder,
            )

        # 2. Crear patrón con todos los skills de la categoría
        # Los morfismos distinguidos son los links entre skills del mismo dominio
        distinguished = _collect_category_morphisms(skill_ids, graph)

        try:
            pattern = pattern_manager.create_pattern(
                component_ids=skill_ids,
                distinguished_links=distinguished,
                metadata={
                    "category": category,
                    "role": "category_colimit",
                    "n_components": len(skill_ids),
                },
                graph=graph,
            )
            logger.info(
                f"[{category}] Patrón creado: {len(skill_ids)} skills, "
                f"{len(distinguished)} morfismos distinguidos"
            )
        except Exception as e:
            logger.warning(f"[{category}] Error creando patrón: {e}")
            pattern = None

        # 3. Construir el colímite
        colimit_skill = None
        colimit_obj = None

        if pattern is not None:
            try:
                colimit_skill, colimit_obj = colimit_builder.build_colimit(
                    pattern=pattern,
                    graph=graph,
                    name=f"agent_{category}",
                    verify=True,
                )
                logger.info(
                    f"[{category}] Colímite construido: {colimit_skill.id} "
                    f"(nivel L{colimit_skill.level})"
                )
            except Exception as e:
                logger.warning(f"[{category}] Error construyendo colímite: {e}")
                colimit_skill = _make_stub_skill(category)

        if colimit_skill is None:
            colimit_skill = _make_stub_skill(category)

        return cls(
            category=category,
            colimit_skill=colimit_skill,
            colimit_obj=colimit_obj,
            pattern=pattern,
            graph=graph,
            pattern_manager=pattern_manager,
            colimit_builder=colimit_builder,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Interfaz principal
    # ──────────────────────────────────────────────────────────────────────────

    def select_tactic(self, query: str) -> str:
        """
        Selecciona la mejor táctica Lean para resolver una query.

        El colímite integra el conocimiento de todos sus skills componentes:
        1. Consulta la memoria procedimental (tácticas exitosas anteriores)
        2. Si no hay historial, usa el skill más relevante del co-cono
        3. Fallback: táctica por defecto de la categoría

        Args:
            query: Texto del problema matemático

        Returns:
            Nombre de la táctica Lean recomendada
        """
        self.calls += 1
        self.state.active_skill_ids = []

        # 1. Consultar memoria
        best = self._best_tactic_for_query(query)
        if best:
            logger.debug(f"[{self.category}] Táctica desde memoria: {best!r}")
            return best

        # 2. Activar co-cono: buscar qué skills del patrón son relevantes
        relevant = self._activate_cocone(query)
        if relevant:
            self.state.active_skill_ids = [s.id for s in relevant]
            # La táctica del skill más activado
            tactic = getattr(relevant[0], "default_tactic", None)
            if tactic:
                return tactic

        # 3. Táctica por defecto de la categoría
        return _default_tactic(self.category)

    def record_result(
        self,
        query: str,
        tactic: str,
        lean_result: str,
        reward: float,
    ) -> None:
        """
        Registra el resultado de una interacción con Lean.

        Actualiza:
        - La memoria procedimental del colímite
        - Las tasas de éxito por táctica
        - Los pesos de los co-conos (morfismos más usados → más fuertes)

        Args:
            query:       Texto del problema
            tactic:      Táctica Lean usada
            lean_result: "success" | "partial" | "failed"
            reward:      Recompensa (0.0 - 1.0)
        """
        success = reward >= 0.8

        self.calls += 1   # registrar interacción (tanto select como record)

        # Actualizar memoria
        qhash = _qhash(query)
        if qhash not in self._memory:
            self._memory[qhash] = []
        self._memory[qhash].append({
            "tactic": tactic,
            "reward": reward,
            "success": success,
            "query_snippet": query[:80],
        })

        # Actualizar tasa de éxito por táctica
        prev = self._tactic_success.get(tactic, 0.5)
        n = sum(1 for recs in self._memory.values()
                for r in recs if r["tactic"] == tactic)
        self._tactic_success[tactic] = (prev * (n - 1) + float(success)) / n

        if success:
            self.successes += 1
            # Fortalecer el co-cono de los skills activos
            self._strengthen_cocone(tactic, reward)

        logger.debug(
            f"[{self.category}] Registrado: tactic={tactic!r}, "
            f"reward={reward:.2f}, success={success}"
        )

    def absorb_new_skill(self, new_skill_id: str) -> bool:
        """
        Integra un nuevo skill en el colímite (re-complejificación).

        Cuando se añade un nuevo skill a la categoría, el colímite
        debe actualizarse para incluirlo — se añade un nuevo co-cono.

        Args:
            new_skill_id: ID del nuevo skill en el grafo

        Returns:
            True si el skill fue absorbido correctamente
        """
        if self.pattern is None or self.graph is None:
            return False

        new_skill = self.graph.get_skill(new_skill_id)
        if new_skill is None:
            return False

        # Añadir al patrón
        if new_skill_id not in self.pattern.component_ids:
            self.pattern.component_ids.append(new_skill_id)

        # Crear morfismo de co-cono: new_skill → colimit
        try:
            from nucleo.types import Morphism, MorphismType
            morphism_id = f"cocone_{new_skill_id}_to_{self.colimit_skill.id}"
            self.graph.add_morphism(Morphism(
                id=morphism_id,
                source_id=new_skill_id,
                target_id=self.colimit_skill.id,
                morphism_type=MorphismType.COMPOSITION,
                weight=0.5,  # peso inicial del co-cono
                metadata={"role": "cocone", "category": self.category},
            ))
            self.state.cocone_morphism_ids.append(morphism_id)
            logger.info(
                f"[{self.category}] Skill {new_skill_id!r} absorbido "
                f"en el colímite"
            )
            return True
        except Exception as e:
            logger.warning(f"[{self.category}] No se pudo absorber {new_skill_id}: {e}")
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Propiedad universal: morfismo mediador
    # ──────────────────────────────────────────────────────────────────────────

    def mediate(self, other_colimit: "ColimitAgent", query: str) -> Optional[str]:
        """
        Morfismo mediador hacia otro colímite (propiedad universal).

        Si otro colímite B también puede resolver esta query, existe
        un único morfismo mediador h: self → B tal que los co-conos
        son compatibles. Esto modela la factorización universal.

        En la práctica: si algebra puede resolver algo que también
        resuelve number-theory, el morfismo mediador es la táctica
        compartida que ambos usan.

        Returns:
            Táctica común (morfismo mediador) o None
        """
        my_tactics = set(self._tactic_success.keys())
        other_tactics = set(other_colimit._tactic_success.keys())
        shared = my_tactics & other_tactics

        if not shared:
            return None

        # El morfismo mediador es la táctica compartida con mayor éxito combinado
        best = max(
            shared,
            key=lambda t: (
                self._tactic_success.get(t, 0) +
                other_colimit._tactic_success.get(t, 0)
            )
        )
        return best

    # ──────────────────────────────────────────────────────────────────────────
    # Internos
    # ──────────────────────────────────────────────────────────────────────────

    def _best_tactic_for_query(self, query: str) -> Optional[str]:
        """Busca la mejor táctica conocida para una query similar."""
        qhash = _qhash(query)

        # Coincidencia exacta
        if qhash in self._memory:
            recs = self._memory[qhash]
            successful = [r for r in recs if r["success"]]
            if successful:
                return max(successful, key=lambda r: r["reward"])["tactic"]

        # Mejor táctica global de la categoría
        if self._tactic_success:
            best = max(self._tactic_success, key=self._tactic_success.get)
            if self._tactic_success[best] >= 0.6:
                return best

        return None

    def _activate_cocone(self, query: str) -> list:
        """Activa los skills del co-cono relevantes para la query."""
        if self.pattern is None or self.graph is None:
            return []
        query_lower = query.lower()
        relevant = []
        for skill_id in self.pattern.component_ids:
            skill = self.graph.get_skill(skill_id)
            if skill and skill.name.lower().split("_")[0] in query_lower:
                relevant.append(skill)
        return relevant[:3]  # top 3 más relevantes

    def _strengthen_cocone(self, tactic: str, reward: float) -> None:
        """Fortalece los morfismos de co-cono de los skills activos."""
        if self.graph is None:
            return
        for morph_id in self.state.cocone_morphism_ids:
            morph = self.graph.get_morphism(morph_id)
            if morph:
                morph.weight = min(1.0, morph.weight + reward * 0.05)

    def stats(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "colimit_skill_id": self.colimit_skill.id if self.colimit_skill else None,
            "n_components": len(self.pattern.component_ids) if self.pattern else 0,
            "n_cocones": len(self.state.cocone_morphism_ids),
            "calls": self.calls,
            "successes": self.successes,
            "tactic_success": dict(sorted(
                self._tactic_success.items(), key=lambda x: -x[1]
            )[:5]),
        }

    def __repr__(self) -> str:
        n = len(self.pattern.component_ids) if self.pattern else 0
        return (
            f"ColimitAgent(category={self.category!r}, "
            f"colimit={self.colimit_skill.id if self.colimit_skill else 'stub'!r}, "
            f"components={n})"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Constructor del sistema completo: 14 ColimitAgents + colímite superior
# ──────────────────────────────────────────────────────────────────────────────

class ColimitAgentSystem:
    """
    Sistema completo de colímites jerárquicos:

      L0: skills atómicos de pilares (31 skills)
              │ co-conos
      L1: 4 PillarAgents (colímites de pilares)
          colim[ZFC], colim[CatThy], colim[Logic], colim[TypeThy]
              │ morfismos pilar→categoría
      L2: 14 ColimitAgents (colímites de categorías)
          colim[algebra], colim[geometry], ..., colim[topology]
              │ co-conos
      L3: colimit_of_colimits = orquestador

    El colímite L3 es el punto de entrada único.
    """

    def __init__(self, graph, pattern_manager, colimit_builder):
        self.graph = graph
        self.pattern_manager = pattern_manager
        self.colimit_builder = colimit_builder

        self._agents: Dict[str, ColimitAgent] = {}    # L2: 14 categorías
        self._pillar_system = None                     # L1: 4 pilares
        self._top_colimit = None                       # L3: orquestador
        self._built = False

    def build(self) -> "ColimitAgentSystem":
        """Construye la jerarquía completa L0→L1→L2→L3."""
        from nucleo.multi_agent.pillar_agents import PillarAgentSystem

        # ── L1: 4 agentes pilar (construyen skills L0 en el grafo) ──
        logger.info("Construyendo PillarAgents L1 (4 pilares)...")
        self._pillar_system = PillarAgentSystem(
            graph=self.graph,
            pattern_manager=self.pattern_manager,
            colimit_builder=self.colimit_builder,
        ).build()

        # ── L2: 14 agentes categoría ──
        logger.info("Construyendo ColimitAgents L2 (14 categorías)...")
        for cat in CATEGORIES:
            agent = ColimitAgent.build(
                category=cat,
                graph=self.graph,
                pattern_manager=self.pattern_manager,
                colimit_builder=self.colimit_builder,
            )
            self._agents[cat] = agent

        # ── Morfismos L1→L2: pilares nutren categorías ──
        logger.info("Conectando pilares con categorías...")
        connections = self._pillar_system.connect_to_category_system(self)
        total_conn = sum(connections.values())
        logger.info(f"  {total_conn} morfismos pilar→categoría creados")

        # ── L3: colímite de los 14 colímites ──
        self._build_top_colimit()

        self._built = True
        logger.info(
            f"Sistema construido: 4 pilares + {len(self._agents)} categorías, "
            f"colímite L3: {self._top_colimit}"
        )
        return self

    def _build_top_colimit(self):
        """Construye el colímite de nivel L3 = colímite de los 14 agentes."""
        l2_ids = [
            a.colimit_skill.id
            for a in self._agents.values()
            if a.colimit_skill is not None
        ]
        if not l2_ids:
            return
        try:
            pattern = self.pattern_manager.create_pattern(
                component_ids=l2_ids,
                distinguished_links=[],
                metadata={"role": "orchestrator_colimit", "level": "L3"},
                graph=self.graph,
            )
            top_skill, top_obj = self.colimit_builder.build_colimit(
                pattern=pattern,
                graph=self.graph,
                name="orchestrator",
                verify=False,
            )
            self._top_colimit = top_skill
            logger.info(f"Colímite L3 (orquestador): {top_skill.id}")
        except Exception as e:
            logger.warning(f"No se pudo construir colímite L3: {e}")

    def route(self, query: str) -> Tuple[str, ColimitAgent]:
        """Enruta la query al agente-colímite apropiado."""
        from nucleo.multi_agent.specialized_agent import classify_query
        category = classify_query(query)
        return category, self._agents[category]

    def record_result(self, query: str, tactic: str, lean_result: str,
                      reward: float, category: Optional[str] = None):
        """Registra resultado y propaga al colímite de la categoría."""
        if category is None:
            from nucleo.multi_agent.specialized_agent import classify_query
            category = classify_query(query)
        if category in self._agents:
            self._agents[category].record_result(query, tactic, lean_result, reward)

        # Detectar morfismos mediadores entre colímites (convergencia)
        if reward >= 0.8:
            self._update_mediating_morphisms(query, tactic, category, reward)

    def _update_mediating_morphisms(self, query, tactic, primary_cat, reward):
        """Si otro agente conoce la misma táctica, refuerza el morfismo mediador."""
        for cat, agent in self._agents.items():
            if cat == primary_cat:
                continue
            if tactic in agent._tactic_success and agent._tactic_success[tactic] >= 0.5:
                mediator = self._agents[primary_cat].mediate(agent, query)
                if mediator:
                    logger.debug(
                        f"Morfismo mediador: {primary_cat} → {cat} "
                        f"via táctica {mediator!r}"
                    )

    def print_hierarchy(self):
        """Muestra la jerarquía completa de colímites L0→L1→L2→L3."""
        from nucleo.multi_agent.pillar_agents import PILLAR_NAMES, PILLAR_FEEDS_CATEGORIES
        print(f"\n{'='*65}")
        print(f"  Jerarquía de Colímites — NLE v7.0")
        print(f"{'='*65}")

        # L3
        if self._top_colimit:
            print(f"\n  L3  [orquestador]")
            print(f"      colim(14 agentes) = {self._top_colimit.id}")

        # L2
        print(f"\n  L2  [14 agentes-categoría]")
        for cat, agent in self._agents.items():
            n = len(agent.pattern.component_ids) if agent.pattern else 0
            sid = agent.colimit_skill.id if agent.colimit_skill else "stub"
            print(f"      [{cat:<20}] colim({n:2d} skills) → {sid}")

        # L1 pilares
        if self._pillar_system:
            print(f"\n  L1  [4 agentes-pilar]")
            for pillar, pa in self._pillar_system._agents.items():
                name = PILLAR_NAMES.get(pillar, pillar)
                n = len(pa.pillar_skills)
                cats = ", ".join(PILLAR_FEEDS_CATEGORIES.get(pillar, []))
                sid = pa.colimit_skill.id if pa.colimit_skill else "stub"
                print(f"      [{name:<30}] colim({n} skills L0) → {sid}")
                print(f"        nutre: {cats}")

        # L0 count
        l0_count = len([s for s in self.graph.skills if s.level == 0])
        print(f"\n  L0  [{l0_count} skills atómicos de pilares]")
        print()

    def stats(self) -> List[Dict]:
        return [a.stats() for a in self._agents.values()]


# ──────────────────────────────────────────────────────────────────────────────
# Utilidades
# ──────────────────────────────────────────────────────────────────────────────

def _collect_category_skills(category: str, graph) -> List[str]:
    """Recopila los IDs de skills pertenecientes a una categoría."""
    ids = []
    try:
        # SkillCategory expone .skills (dict id→Skill) o iterable
        all_skills = graph.skills if hasattr(graph, "skills") else []
        if isinstance(all_skills, dict):
            all_skills = all_skills.values()
        cat_words = set(category.replace("-", " ").split())
        for skill in all_skills:
            # 1. Metadata explícita
            meta_cat = (skill.metadata or {}).get("category", "")
            if meta_cat == category:
                ids.append(skill.id)
                continue
            # 2. Nombre contiene palabras clave de la categoría
            name_words = set(skill.name.lower().replace("_", " ").split())
            if cat_words & name_words:
                ids.append(skill.id)
    except Exception as e:
        logger.debug(f"_collect_category_skills({category}): {e}")
    return ids


def _collect_category_morphisms(skill_ids: List[str], graph) -> List[str]:
    """Recopila morfismos entre skills de la misma categoría."""
    id_set = set(skill_ids)
    morphism_ids = []
    try:
        all_morphisms = graph.morphisms if hasattr(graph, "morphisms") else {}
        if isinstance(all_morphisms, dict):
            all_morphisms = all_morphisms.values()
        for m in all_morphisms:
            if m.source_id in id_set and m.target_id in id_set:
                morphism_ids.append(m.id)
    except Exception as e:
        logger.debug(f"_collect_category_morphisms: {e}")
    return morphism_ids


def _default_tactic(category: str) -> str:
    """Táctica Lean por defecto para cada categoría."""
    defaults = {
        "algebra":         "ring",
        "analysis":        "norm_num",
        "category-theory": "simp",
        "combinatorics":   "omega",
        "computation":     "decide",
        "geometry":        "norm_num",
        "lean-tactics":    "simp",
        "logic":           "tauto",
        "number-theory":   "norm_num",
        "optimization":    "linarith",
        "probability":     "norm_num",
        "proof-strategies":"exact",
        "set-theory":      "simp",
        "topology":        "simp",
    }
    return defaults.get(category, "simp")


def _make_stub_skill(category: str):
    """Crea un skill stub cuando no hay suficientes skills en el grafo."""
    from nucleo.types import Skill
    import uuid
    return Skill(
        id=f"stub_{category}_{uuid.uuid4().hex[:6]}",
        name=f"agent_{category}",
        level=2,
        metadata={"category": category, "stub": True},
    )


def _qhash(query: str) -> str:
    normalized = " ".join(query.lower().split())[:200]
    return f"qh_{hash(normalized) % 1_000_000:06d}"
