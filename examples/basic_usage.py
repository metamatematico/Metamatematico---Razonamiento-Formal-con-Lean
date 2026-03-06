#!/usr/bin/env python3
"""
Ejemplo Basico de Uso
=====================

Demuestra el flujo completo del Nucleo Logico Evolutivo:
1. Inicializar el grafo categorico
2. Agregar skills de los pilares fundamentales
3. Crear morfismos entre skills
4. Ejecutar el agente RL
5. Simular asistencia con Lean

Uso:
    python examples/basic_usage.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from nucleo.types import (
    Skill, Morphism, MorphismType, PillarType,
    State, Action, ActionType
)
from nucleo.config import NucleoConfig
from nucleo.graph.category import SkillCategory
from nucleo.graph.operations import GraphOperations
from nucleo.rl.mdp import MDP, Transition
from nucleo.rl.rewards import RewardFunction, RewardConfig, TaskResult
from nucleo.rl.agent import NucleoAgent, AgentConfig


def create_foundational_graph() -> SkillCategory:
    """
    Crear grafo con skills fundamentales de los 4 pilares.

    F = (F_Set, F_Cat, F_Log, F_Type)
    """
    graph = SkillCategory(name="NucleoFoundational")

    # =========================================
    # F_Set: Teoria de Conjuntos (ZFC)
    # =========================================
    graph.add_skill(Skill(
        id="zfc-basics",
        name="ZFC Basics",
        description="Axiomas basicos de Zermelo-Fraenkel con Eleccion",
        pillar=PillarType.SET,
        metadata={"axioms": ["extensionality", "pairing", "union", "powerset"]}
    ))

    graph.add_skill(Skill(
        id="ordinals",
        name="Ordinals",
        description="Numeros ordinales y aritmetica transfinita",
        pillar=PillarType.SET,
        metadata={"concepts": ["well-ordering", "transfinite-induction"]}
    ))

    # =========================================
    # F_Cat: Teoria de Categorias
    # =========================================
    graph.add_skill(Skill(
        id="cat-basics",
        name="Category Basics",
        description="Objetos, morfismos, composicion, identidad",
        pillar=PillarType.CAT,
        metadata={"concepts": ["object", "morphism", "composition", "identity"]}
    ))

    graph.add_skill(Skill(
        id="functors",
        name="Functors",
        description="Morfismos entre categorias",
        pillar=PillarType.CAT,
        metadata={"types": ["covariant", "contravariant", "bifunctor"]}
    ))

    graph.add_skill(Skill(
        id="adjunctions",
        name="Adjunctions",
        description="Pares adjuntos F ⊣ G",
        pillar=PillarType.CAT,
        metadata={"examples": ["free-forgetful", "curry-uncurry"]}
    ))

    # =========================================
    # F_Log: Logica (FOL=, IL, Kripke)
    # =========================================
    graph.add_skill(Skill(
        id="fol-basics",
        name="First-Order Logic",
        description="FOL= como 'sweet spot' metalogico",
        pillar=PillarType.LOG,
        metadata={"properties": ["complete", "compact", "lowenheim-skolem"]}
    ))

    graph.add_skill(Skill(
        id="intuitionistic",
        name="Intuitionistic Logic",
        description="IL sin LEM, semantica de Kripke",
        pillar=PillarType.LOG,
        metadata={"semantics": "kripke", "no_lem": True}
    ))

    graph.add_skill(Skill(
        id="natural-deduction",
        name="Natural Deduction",
        description="Sistema de deduccion natural",
        pillar=PillarType.LOG,
        metadata={"rules": ["intro", "elim"]}
    ))

    # =========================================
    # F_Type: Teoria de Tipos (CIC)
    # =========================================
    graph.add_skill(Skill(
        id="stlc",
        name="Simply Typed Lambda Calculus",
        description="Calculo lambda tipado simple",
        pillar=PillarType.TYPE,
        metadata={"features": ["function-types", "type-checking"]}
    ))

    graph.add_skill(Skill(
        id="dependent-types",
        name="Dependent Types",
        description="Tipos que dependen de valores",
        pillar=PillarType.TYPE,
        metadata={"examples": ["Vec n", "Fin n"]}
    ))

    graph.add_skill(Skill(
        id="cic",
        name="Calculus of Inductive Constructions",
        description="Base de Lean/Coq",
        pillar=PillarType.TYPE,
        metadata={"features": ["universes", "inductive-types", "recursion"]}
    ))

    graph.add_skill(Skill(
        id="curry-howard",
        name="Curry-Howard Correspondence",
        description="Proposiciones = Tipos, Pruebas = Programas",
        pillar=PillarType.TYPE,
        metadata={"isomorphism": "propositions-as-types"}
    ))

    # =========================================
    # Lean 4 Skills
    # =========================================
    graph.add_skill(Skill(
        id="lean-tactics",
        name="Lean 4 Tactics",
        description="Tacticas fundamentales de Lean 4",
        pillar=PillarType.TYPE,
        metadata={"tactics": ["intro", "apply", "simp", "rw", "cases", "induction"]}
    ))

    graph.add_skill(Skill(
        id="lean-mathlib",
        name="Mathlib Integration",
        description="Uso de Mathlib para matematicas formalizadas",
        pillar=PillarType.TYPE,
        metadata={"areas": ["algebra", "analysis", "topology", "number-theory"]}
    ))

    print(f"Creados {graph.stats['num_skills']} skills en el grafo")

    return graph


def create_morphisms(graph: SkillCategory) -> None:
    """
    Crear morfismos entre skills.

    Tipos de morfismo:
    - DEPENDENCY (->): t requiere s
    - SPECIALIZATION (->>): t especializa s
    - ANALOGY (<->): isomorfismo parcial
    - TRANSLATION (~>): entre pilares
    """

    # =========================================
    # Dependencias (->)
    # =========================================
    dependencies = [
        ("zfc-basics", "ordinals"),
        ("cat-basics", "functors"),
        ("functors", "adjunctions"),
        ("fol-basics", "intuitionistic"),
        ("fol-basics", "natural-deduction"),
        ("stlc", "dependent-types"),
        ("dependent-types", "cic"),
        ("cic", "lean-tactics"),
        ("lean-tactics", "lean-mathlib"),
    ]

    for source, target in dependencies:
        m = graph.add_morphism(
            source_id=source,
            target_id=target,
            morphism_type=MorphismType.DEPENDENCY,
            weight=1.0
        )
        if m:
            print(f"  {source} -> {target}")

    # =========================================
    # Especializaciones (->>)
    # =========================================
    specializations = [
        ("fol-basics", "natural-deduction", 0.9),
        ("cat-basics", "adjunctions", 0.7),
    ]

    for source, target, weight in specializations:
        m = graph.add_morphism(
            source_id=source,
            target_id=target,
            morphism_type=MorphismType.SPECIALIZATION,
            weight=weight
        )
        if m:
            print(f"  {source} ->> {target} (w={weight})")

    # =========================================
    # Traducciones entre pilares (~>)
    # Curry-Howard: LOG ~> TYPE
    # =========================================
    translations = [
        # Curry-Howard
        ("natural-deduction", "stlc", 0.95, {"translation": "curry-howard"}),
        ("intuitionistic", "dependent-types", 0.9, {"translation": "curry-howard"}),

        # Categorias y Tipos
        ("adjunctions", "curry-howard", 0.8, {"translation": "adjunction-correspondence"}),

        # Conjuntos y Tipos
        ("zfc-basics", "cic", 0.7, {"translation": "sets-as-types"}),
    ]

    for source, target, weight, metadata in translations:
        m = graph.add_morphism(
            source_id=source,
            target_id=target,
            morphism_type=MorphismType.TRANSLATION,
            weight=weight,
            metadata=metadata
        )
        if m:
            print(f"  {source} ~> {target} ({metadata.get('translation', '')})")

    print(f"\nCreados {graph.stats['num_morphisms']} morfismos")


def demonstrate_categorical_properties(graph: SkillCategory) -> None:
    """
    Demostrar propiedades categoricas del grafo.
    """
    print("\n" + "=" * 50)
    print("Verificacion de Axiomas Categoricos")
    print("=" * 50)

    axioms = graph.verify_axioms()

    for axiom, passed in axioms.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {axiom}")

    # Demostrar composicion
    print("\nComposicion de morfismos:")

    # Buscar cadena de dependencias
    if "dependent-types" in graph.skill_ids and "lean-tactics" in graph.skill_ids:
        # stlc -> dependent-types -> cic -> lean-tactics
        print("  Cadena: stlc -> dependent-types -> cic -> lean-tactics")

        # Verificar hom-sets
        hom_1 = graph.hom("stlc", "dependent-types")
        hom_2 = graph.hom("dependent-types", "cic")
        hom_3 = graph.hom("cic", "lean-tactics")

        print(f"    hom(stlc, dependent-types): {len(hom_1)} morfismo(s)")
        print(f"    hom(dependent-types, cic): {len(hom_2)} morfismo(s)")
        print(f"    hom(cic, lean-tactics): {len(hom_3)} morfismo(s)")


def run_agent_episode(graph: SkillCategory, num_steps: int = 10) -> dict:
    """
    Ejecutar un episodio del agente RL.
    """
    print("\n" + "=" * 50)
    print("Episodio del Agente RL")
    print("=" * 50)

    # Configurar agente
    agent_config = AgentConfig(
        epsilon_start=0.5,  # Mas exploracion para demo
        epsilon_decay=0.9,
    )

    agent = NucleoAgent(graph, config=agent_config)
    mdp = MDP(graph, gamma=0.99)

    # Ejecutar episodio
    metrics = agent.train_episode(mdp, max_steps=num_steps)

    print(f"\nResultados del episodio:")
    print(f"  Recompensa: {metrics['episode_reward']:.2f}")
    print(f"  Pasos: {metrics['episode_length']}")
    print(f"  Epsilon: {agent.epsilon:.3f}")
    print(f"  Buffer size: {metrics['buffer_size']}")

    return metrics


def simulate_lean_assistance() -> None:
    """
    Simular asistencia con prueba Lean.
    """
    print("\n" + "=" * 50)
    print("Simulacion de Asistencia Lean")
    print("=" * 50)

    # Goal de ejemplo
    goal = "forall (n : Nat), n + 0 = n"

    print(f"\nGoal: {goal}")
    print("\nSugerencias de tacticas:")

    # Heuristica simple basada en patrones
    suggestions = []

    if "forall" in goal:
        suggestions.append(("intro n", "Introducir variable cuantificada"))

    if "=" in goal:
        suggestions.append(("rfl", "Igualdad por reflexividad"))
        suggestions.append(("simp", "Simplificar automaticamente"))

    if "+" in goal:
        suggestions.append(("ring", "Aritmetica de anillos"))
        suggestions.append(("omega", "Aritmetica lineal"))

    for i, (tactic, reason) in enumerate(suggestions, 1):
        print(f"  {i}. {tactic}")
        print(f"     => {reason}")

    # Prueba sugerida
    print("\nPrueba sugerida:")
    print("  theorem add_zero (n : Nat) : n + 0 = n := by")
    print("    induction n with")
    print("    | zero => rfl")
    print("    | succ n ih => simp [Nat.add_succ, ih]")


def demonstrate_pillar_translations() -> None:
    """
    Demostrar traducciones entre pilares (Curry-Howard).
    """
    print("\n" + "=" * 50)
    print("Correspondencia Curry-Howard")
    print("=" * 50)

    correspondences = [
        ("Proposicion", "Tipo"),
        ("Prueba de P", "Termino de tipo P"),
        ("P -> Q", "Tipo funcion P -> Q"),
        ("P /\\ Q", "Tipo producto P x Q"),
        ("P \\/ Q", "Tipo suma P + Q"),
        ("forall x.P(x)", "Tipo dependiente (x : A) -> P x"),
        ("exists x.P(x)", "Tipo sigma (x : A) x P x"),
        ("False", "Tipo vacio Empty"),
        ("Not P", "P -> Empty"),
    ]

    print("\n  Logica (F_Log)          ~>  Tipos (F_Type)")
    print("  " + "-" * 50)

    for logic, types in correspondences:
        print(f"  {logic:<25} ~>  {types}")


def main():
    """Funcion principal del ejemplo."""
    print("=" * 60)
    print("Nucleo Logico Evolutivo - Ejemplo de Uso")
    print("=" * 60)
    print()

    # 1. Crear grafo con skills fundamentales
    print("1. Creando grafo categorico con skills fundamentales...")
    graph = create_foundational_graph()

    # 2. Crear morfismos
    print("\n2. Creando morfismos entre skills...")
    create_morphisms(graph)

    # 3. Verificar propiedades categoricas
    demonstrate_categorical_properties(graph)

    # 4. Ejecutar agente
    run_agent_episode(graph, num_steps=5)

    # 5. Simular asistencia Lean
    simulate_lean_assistance()

    # 6. Demostrar Curry-Howard
    demonstrate_pillar_translations()

    # Estadisticas finales
    print("\n" + "=" * 60)
    print("Estadisticas Finales del Grafo")
    print("=" * 60)

    stats = graph.stats
    print(f"  Skills totales: {stats['num_skills']}")
    print(f"  Morfismos totales: {stats['num_morphisms']}")
    print(f"  Conectado: {'Si' if graph.is_connected() else 'No'}")

    # Skills por pilar
    print("\n  Skills por pilar:")
    pillar_counts = {}
    for skill in graph.skills:
        pillar = skill.pillar.name if skill.pillar else "None"
        pillar_counts[pillar] = pillar_counts.get(pillar, 0) + 1

    for pillar, count in sorted(pillar_counts.items()):
        print(f"    F_{pillar}: {count}")

    print("\nEjemplo completado!")


if __name__ == "__main__":
    main()
