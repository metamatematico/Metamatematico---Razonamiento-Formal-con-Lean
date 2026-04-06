"""
PillarAgent — cada pilar fundacional tiene su propio agente-colímite.
=====================================================================

Los 4 pilares (ZFC, CatThy, Logic, TypeThy) son más fundacionales
que las 14 categorías matemáticas. Sus agentes son colímites de los
skills L0 de cada pilar — el nivel más bajo de la jerarquía activa.

Jerarquía completa:

  L0: skills atómicos de los pilares (31 skills)
      ZFC: naive-sets, zfc-axioms, ordinals, cardinals...
      CatThy: cat-basics, functors, nat-trans, limits...
      Logic: propositional, fol-syntax, fol-semantics...
      TypeThy: stlc, system-f, dependent-types...
            │ co-conos
            ▼
  L1 (PillarAgent): 4 agentes pilar
      colim[ZFC]     colim[CatThy]
      colim[Logic]   colim[TypeThy]
            │ morfismos hacia las categorías que los usan
            ▼
  L2 (ColimitAgent): 14 agentes categoría
      colim[algebra] ──usa──► colim[ZFC] + colim[Logic]
      colim[topology]──usa──► colim[CatThy] + colim[ZFC]
      colim[lean-tactics]──►  colim[TypeThy] + colim[Logic]
            │ co-conos
            ▼
  L3: colímite del orquestador

Cada pilar sabe qué categorías "nutren":
  ZFC       → algebra, set-theory, combinatorics, number-theory, probability
  CatThy    → category-theory, topology, algebra (abstracta), analysis
  Logic     → logic, proof-strategies, lean-tactics, computation
  TypeThy   → lean-tactics, proof-strategies, computation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

# Definición de los 4 pilares
PILLARS: List[str] = ["zfc", "category-theory-pillar", "logic-pillar", "type-theory-pillar"]

# Qué categorías L2 nutre cada pilar (morfismos pilar → categoría)
PILLAR_FEEDS_CATEGORIES: Dict[str, List[str]] = {
    "zfc": [
        "algebra", "set-theory", "combinatorics",
        "number-theory", "probability", "analysis",
    ],
    "category-theory-pillar": [
        "category-theory", "topology", "algebra", "analysis",
    ],
    "logic-pillar": [
        "logic", "proof-strategies", "lean-tactics",
        "computation", "set-theory",
    ],
    "type-theory-pillar": [
        "lean-tactics", "proof-strategies", "computation",
        "logic",
    ],
}

# Clases de pilares del sistema
PILLAR_CLASSES = {
    "zfc": "nucleo.pillars.set_theory.SetTheoryPillar",
    "category-theory-pillar": "nucleo.pillars.category_theory.CategoryTheoryPillar",
    "logic-pillar": "nucleo.pillars.logic.LogicPillar",
    "type-theory-pillar": "nucleo.pillars.type_theory.TypeTheoryPillar",
}

# Nombres legibles
PILLAR_NAMES = {
    "zfc": "ZFC (Teoría de Conjuntos)",
    "category-theory-pillar": "Teoría de Categorías",
    "logic-pillar": "Lógica (FOL + IL)",
    "type-theory-pillar": "Teoría de Tipos (Curry-Howard)",
}


class PillarAgent:
    """
    Agente-colímite de un pilar fundacional.

    Es el colímite de todos los skills L0 del pilar.
    Actúa como base fundacional para los ColimitAgents L2:
    envía señales (morfismos) a las categorías que dependen de él.

    Analogía: es la "neurona fundacional" — aprende los axiomas
    y principios base, y los transmite a los agentes especializados.
    """

    def __init__(
        self,
        pillar_name: str,
        colimit_skill,
        colimit_obj,
        pattern,
        graph,
        pattern_manager,
        colimit_builder,
        pillar_skills: List[Any],
    ):
        self.pillar_name = pillar_name
        self.colimit_skill = colimit_skill
        self.colimit_obj = colimit_obj
        self.pattern = pattern
        self.graph = graph
        self.pattern_manager = pattern_manager
        self.colimit_builder = colimit_builder
        self.pillar_skills = pillar_skills   # skills L0 del pilar

        # Qué categorías nutre este pilar
        self.feeds_categories = PILLAR_FEEDS_CATEGORIES.get(pillar_name, [])

        # Memoria: principios fundamentales usados exitosamente
        self._axiom_usage: Dict[str, int] = {}    # axiom_id → veces usado
        self._principle_success: Dict[str, float] = {}  # principio → tasa éxito

        self.calls = 0
        self.successes = 0

    @classmethod
    def build(
        cls,
        pillar_name: str,
        graph,
        pattern_manager,
        colimit_builder,
    ) -> "PillarAgent":
        """
        Construye el PillarAgent para un pilar.

        1. Instancia el Pillar y obtiene sus skills L0
        2. Los registra en el grafo global (si no existen)
        3. Crea el patrón y construye el colímite L1
        """
        # 1. Obtener skills L0 del pilar
        pillar_skills = _load_pillar_skills(pillar_name)
        if not pillar_skills:
            logger.warning(f"[{pillar_name}] No se pudieron cargar skills del pilar")
            pillar_skills = []

        # 2. Registrar skills L0 en el grafo (nivel 0)
        skill_ids = []
        for ps in pillar_skills:
            from nucleo.types import Skill, PillarType
            pillar_type = _pillar_name_to_type(pillar_name)
            skill = Skill(
                id=f"pillar_{pillar_name}_{ps.id}",
                name=ps.name,
                level=0,
                pillar=pillar_type,
                description=ps.description,
                metadata={
                    "pillar": pillar_name,
                    "role": "foundational",
                    "original_id": ps.id,
                },
            )
            if skill.id not in graph.skill_ids:
                graph.add_skill(skill)
            skill_ids.append(skill.id)

        logger.info(
            f"[{pillar_name}] {len(skill_ids)} skills L0 registrados en el grafo"
        )

        # 3. Crear patrón L0 → colímite L1
        colimit_skill = None
        colimit_obj = None
        pattern = None

        if skill_ids:
            try:
                pattern = pattern_manager.create_pattern(
                    component_ids=skill_ids,
                    distinguished_links=[],
                    metadata={
                        "pillar": pillar_name,
                        "role": "pillar_colimit",
                        "level": "L1",
                    },
                    graph=graph,
                )
                colimit_skill, colimit_obj = colimit_builder.build_colimit(
                    pattern=pattern,
                    graph=graph,
                    name=f"pillar_agent_{pillar_name}",
                    verify=True,
                )
                logger.info(
                    f"[{pillar_name}] Colímite L1 construido: "
                    f"{colimit_skill.id} ({len(skill_ids)} skills)"
                )
            except Exception as e:
                logger.warning(f"[{pillar_name}] Error construyendo colímite: {e}")
                colimit_skill = _stub_pillar_skill(pillar_name)

        if colimit_skill is None:
            colimit_skill = _stub_pillar_skill(pillar_name)

        return cls(
            pillar_name=pillar_name,
            colimit_skill=colimit_skill,
            colimit_obj=colimit_obj,
            pattern=pattern,
            graph=graph,
            pattern_manager=pattern_manager,
            colimit_builder=colimit_builder,
            pillar_skills=pillar_skills,
        )

    def inject_into_category_agent(self, category_agent) -> bool:
        """
        Crea un morfismo desde este pilar hacia un agente de categoría.

        Este morfismo representa "el agente de categoría usa este pilar".
        En términos categóricos: es parte del co-cono que hace que
        el agente de categoría sea colímite de sus skills + los pilares.

        Args:
            category_agent: ColimitAgent de la categoría que usa este pilar

        Returns:
            True si el morfismo fue creado correctamente
        """
        if self.colimit_skill is None or category_agent.colimit_skill is None:
            return False
        if self.graph is None:
            return False

        cat = category_agent.category
        if cat not in self.feeds_categories:
            return False  # este pilar no nutre esa categoría

        morph_id = f"pillar_{self.pillar_name}_to_{cat}"
        try:
            from nucleo.types import MorphismType
            self.graph.add_morphism(
                source_id=self.colimit_skill.id,
                target_id=category_agent.colimit_skill.id,
                morphism_type=MorphismType.DEPENDENCY,
                weight=0.8,
                metadata={
                    "role": "pillar_to_category",
                    "pillar": self.pillar_name,
                    "category": cat,
                },
            )
            logger.debug(
                f"Morfismo: colim[{self.pillar_name}] → colim[{cat}]"
            )
            return True
        except Exception as e:
            logger.debug(f"inject_into_category_agent error: {e}")
            return False

    def record_usage(self, axiom_id: str, success: bool) -> None:
        """Registra el uso de un axioma/principio del pilar."""
        self.calls += 1
        self._axiom_usage[axiom_id] = self._axiom_usage.get(axiom_id, 0) + 1
        prev = self._principle_success.get(axiom_id, 0.5)
        n = self._axiom_usage[axiom_id]
        self._principle_success[axiom_id] = (prev * (n - 1) + float(success)) / n
        if success:
            self.successes += 1

    def most_used_axioms(self, top_n: int = 3) -> List[Tuple[str, int]]:
        """Retorna los axiomas más usados."""
        return sorted(
            self._axiom_usage.items(), key=lambda x: -x[1]
        )[:top_n]

    def stats(self) -> Dict[str, Any]:
        return {
            "pillar": self.pillar_name,
            "colimit_id": self.colimit_skill.id if self.colimit_skill else None,
            "n_l0_skills": len(self.pillar_skills),
            "feeds_categories": self.feeds_categories,
            "calls": self.calls,
            "successes": self.successes,
            "top_axioms": self.most_used_axioms(),
        }

    def __repr__(self) -> str:
        n = len(self.pillar_skills)
        return (
            f"PillarAgent(pillar={self.pillar_name!r}, "
            f"colimit={self.colimit_skill.id if self.colimit_skill else 'stub'!r}, "
            f"l0_skills={n})"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Sistema de pilares integrado
# ──────────────────────────────────────────────────────────────────────────────

class PillarAgentSystem:
    """
    Los 4 PillarAgents + conexión con los 14 ColimitAgents.

    Construye la jerarquía L0 → L1(pilares) → L2(categorías).
    Inyecta morfismos desde cada pilar hacia las categorías que usa.
    """

    def __init__(self, graph, pattern_manager, colimit_builder):
        self.graph = graph
        self.pattern_manager = pattern_manager
        self.colimit_builder = colimit_builder
        self._agents: Dict[str, PillarAgent] = {}

    def build(self) -> "PillarAgentSystem":
        """Construye los 4 agentes pilar."""
        logger.info("Construyendo PillarAgentSystem (4 pilares)...")
        for pillar in PILLARS:
            agent = PillarAgent.build(
                pillar_name=pillar,
                graph=self.graph,
                pattern_manager=self.pattern_manager,
                colimit_builder=self.colimit_builder,
            )
            self._agents[pillar] = agent
            logger.info(f"  {repr(agent)}")
        return self

    def connect_to_category_system(self, category_system) -> Dict[str, int]:
        """
        Inyecta morfismos desde cada pilar hacia los ColimitAgents de categoría.

        Crea la relación L1(pilares) → L2(categorías) en el grafo.
        Returns dict con número de conexiones por pilar.
        """
        connections: Dict[str, int] = {}
        for pillar_name, pillar_agent in self._agents.items():
            count = 0
            for cat_name in pillar_agent.feeds_categories:
                cat_agent = category_system._agents.get(cat_name)
                if cat_agent and pillar_agent.inject_into_category_agent(cat_agent):
                    count += 1
            connections[pillar_name] = count
            logger.info(
                f"  [{pillar_name}] conectado a {count} categorías"
            )
        return connections

    def print_hierarchy(self):
        print(f"\n{'='*60}")
        print(f"  Pilares Fundacionales — L0 → L1")
        print(f"{'='*60}")
        for pillar, agent in self._agents.items():
            name = PILLAR_NAMES.get(pillar, pillar)
            n = len(agent.pillar_skills)
            cats = ", ".join(agent.feeds_categories[:3])
            if len(agent.feeds_categories) > 3:
                cats += f" (+{len(agent.feeds_categories)-3})"
            print(f"\n  [{name}]")
            print(f"    colim({n} skills L0) → {agent.colimit_skill.id}")
            print(f"    nutre: {cats}")

    def stats(self) -> List[Dict]:
        return [a.stats() for a in self._agents.values()]

    def __getitem__(self, key: str) -> PillarAgent:
        return self._agents[key]


# ──────────────────────────────────────────────────────────────────────────────
# Utilidades
# ──────────────────────────────────────────────────────────────────────────────

def _load_pillar_skills(pillar_name: str) -> List[Any]:
    """Carga los skills L0 de un pilar instanciando su clase."""
    class_path = PILLAR_CLASSES.get(pillar_name, "")
    if not class_path:
        return []
    try:
        module_path, class_name = class_path.rsplit(".", 1)
        import importlib
        module = importlib.import_module(module_path)
        PillarClass = getattr(module, class_name)
        pillar_instance = PillarClass()
        return pillar_instance.get_skills()
    except Exception as e:
        logger.warning(f"No se pudo cargar pilar {pillar_name}: {e}")
        return []


def _pillar_name_to_type(pillar_name: str):
    """Convierte nombre de pilar a PillarType."""
    from nucleo.types import PillarType
    mapping = {
        "zfc": PillarType.SET,
        "category-theory-pillar": PillarType.CAT,
        "logic-pillar": PillarType.LOG,
        "type-theory-pillar": PillarType.TYPE,
    }
    return mapping.get(pillar_name, PillarType.SET)


def _stub_pillar_skill(pillar_name: str):
    """Crea un skill stub para el pilar cuando no hay skills."""
    from nucleo.types import Skill
    import uuid
    return Skill(
        id=f"stub_pillar_{pillar_name}_{uuid.uuid4().hex[:6]}",
        name=f"pillar_agent_{pillar_name}",
        level=1,
        metadata={"pillar": pillar_name, "stub": True},
    )
