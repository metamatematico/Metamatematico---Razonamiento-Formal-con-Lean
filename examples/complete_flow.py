#!/usr/bin/env python3
"""
Ejemplo de Flujo Completo
=========================

Demuestra el sistema Nucleo Logico Evolutivo completo:
    Usuario -> LLM (Claude) -> Nucleo (RL) -> Lean 4

Flujo:
1. Usuario hace pregunta matematica
2. Nucleo procesa con LLM
3. Agente RL decide accion
4. Si es prueba, verifica con Lean
5. Retorna respuesta

Uso:
    python examples/complete_flow.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Agregar root al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nucleo.core import Nucleo, NucleoMode
from nucleo.types import ActionType


async def interactive_session():
    """Sesion interactiva con el Nucleo."""
    print("=" * 60)
    print("Nucleo Logico Evolutivo - Sesion Interactiva")
    print("=" * 60)
    print()
    print("Sistema: Sigma_t = (L, N_t, G_t, F)")
    print("  L: Claude (LLM)")
    print("  N_t: Agente RL")
    print("  G_t: Grafo Categorico")
    print("  F: Pilares Fundamentales")
    print()
    print("Comandos especiales:")
    print("  /stats  - Ver estadisticas")
    print("  /skills - Ver skills disponibles")
    print("  /quit   - Salir")
    print("=" * 60)
    print()

    # Inicializar Nucleo
    nucleo = Nucleo()

    # Callbacks para debug
    def on_action(action):
        print(f"  [Accion: {action.action_type.name}]")

    def on_reward(reward):
        print(f"  [Recompensa: {reward:.2f}]")

    nucleo.on_action(on_action)
    nucleo.on_reward(on_reward)

    print("Inicializando Nucleo...")
    await nucleo.initialize()
    print("Nucleo listo!")
    print()

    # Loop interactivo
    while True:
        try:
            user_input = input("Tu > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAdios!")
            break

        if not user_input:
            continue

        # Comandos especiales
        if user_input.startswith("/"):
            if user_input == "/quit":
                print("Adios!")
                break
            elif user_input == "/stats":
                stats = nucleo.stats
                print("\nEstadisticas:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
                print()
                continue
            elif user_input == "/skills":
                print("\nSkills disponibles:")
                for skill_id in nucleo.graph.skill_ids:
                    skill = nucleo.graph.get_skill(skill_id)
                    if skill:
                        pillar = skill.pillar.name if skill.pillar else "?"
                        print(f"  [{pillar}] {skill.name}")
                print()
                continue
            else:
                print(f"Comando desconocido: {user_input}")
                continue

        # Procesar con Nucleo
        print()
        response = await nucleo.process(user_input)
        print()
        print(f"Nucleo > {response.content}")
        print()


async def demo_scenarios():
    """Ejecutar escenarios de demostracion."""
    print("=" * 60)
    print("Nucleo Logico Evolutivo - Demo de Escenarios")
    print("=" * 60)
    print()

    nucleo = Nucleo()
    await nucleo.initialize()

    # Escenarios de prueba
    scenarios = [
        {
            "name": "Consulta conceptual",
            "input": "Que es la correspondencia Curry-Howard?",
            "expected_action": ActionType.RESPONSE
        },
        {
            "name": "Formalizacion",
            "input": "Como formalizo 'todo natural es mayor o igual a cero' en Lean?",
            "expected_action": ActionType.ASSIST
        },
        {
            "name": "Verificacion Lean",
            "input": """Verifica esta prueba:
```lean
theorem zero_le (n : Nat) : 0 <= n := by
  induction n with
  | zero => rfl
  | succ n ih => exact Nat.le_succ_of_le ih
```""",
            "expected_action": ActionType.ASSIST
        },
        {
            "name": "Sugerencia de tacticas",
            "input": "Tengo el goal 'forall n, n + 0 = n'. Que tactica uso?",
            "expected_action": ActionType.ASSIST
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*50}")
        print(f"Escenario {i}: {scenario['name']}")
        print(f"{'='*50}")
        print(f"\nInput: {scenario['input'][:100]}...")
        print()

        response = await nucleo.process(scenario["input"])

        print(f"Accion: {response.action_type.name}")
        print(f"Confianza: {response.confidence:.2f}")
        print(f"\nRespuesta:\n{response.content[:300]}...")

        if response.lean_result:
            print(f"\nResultado Lean: {response.lean_result.status.name}")

    # Estadisticas finales
    print("\n" + "=" * 60)
    print("Estadisticas Finales")
    print("=" * 60)
    stats = nucleo.stats
    for key, value in stats.items():
        print(f"  {key}: {value}")


async def demo_training_loop():
    """Demostrar loop de entrenamiento."""
    print("=" * 60)
    print("Nucleo Logico Evolutivo - Training Loop Demo")
    print("=" * 60)
    print()

    nucleo = Nucleo()
    await nucleo.initialize()

    # Datos de entrenamiento simulados
    training_data = [
        "Demuestra que 1 + 1 = 2",
        "Que es un funtor?",
        "Prueba por induccion que sum(1..n) = n*(n+1)/2",
        "Define ordinales en ZFC",
        "Explica la semantica de Kripke",
    ]

    print(f"Entrenando con {len(training_data)} ejemplos...")
    print()

    rewards = []

    for i, data in enumerate(training_data, 1):
        response = await nucleo.process(data)
        reward = nucleo._estimate_reward(
            nucleo.agent._last_action if hasattr(nucleo.agent, '_last_action') else None,
            response
        )
        rewards.append(reward if reward else 0.5)

        print(f"[{i}/{len(training_data)}] Epsilon: {nucleo.agent.epsilon:.3f}, Reward: {rewards[-1]:.2f}")

    avg_reward = sum(rewards) / len(rewards)
    print(f"\nRecompensa promedio: {avg_reward:.2f}")
    print(f"Epsilon final: {nucleo.agent.epsilon:.3f}")


def main():
    """Funcion principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Demo del Nucleo Logico Evolutivo"
    )
    parser.add_argument(
        "--mode",
        choices=["interactive", "demo", "train"],
        default="demo",
        help="Modo de ejecucion"
    )

    args = parser.parse_args()

    if args.mode == "interactive":
        asyncio.run(interactive_session())
    elif args.mode == "train":
        asyncio.run(demo_training_loop())
    else:
        asyncio.run(demo_scenarios())


if __name__ == "__main__":
    main()
