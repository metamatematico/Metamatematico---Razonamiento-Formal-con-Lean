#!/usr/bin/env python3
"""
Ejemplo de Integracion con Lean 4
=================================

Demuestra el flujo de verificacion bidireccional con Lean 4:
1. Verificar codigo Lean
2. Parsear errores y sugerir correcciones
3. Aplicar tacticas y verificar progreso
4. Seleccion inteligente de tacticas

Uso:
    python examples/lean_integration.py
"""

from __future__ import annotations

import asyncio
from typing import List, Tuple

from nucleo.lean.client import LeanClient, LeanConfig, LeanResultStatus
from nucleo.lean.parser import LeanParser, LeanMessage, MessageSeverity
from nucleo.lean.tactics import TacticMapper, TacticCategory


# =========================================
# Ejemplos de codigo Lean para probar
# =========================================

LEAN_EXAMPLES = {
    "valid_theorem": '''
theorem add_comm (a b : Nat) : a + b = b + a := by
  induction a with
  | zero => simp
  | succ n ih => simp [Nat.succ_add, ih]
''',

    "type_error": '''
def bad_function (n : Nat) : String :=
  n + 1
''',

    "unknown_ident": '''
theorem uses_unknown : forall n, unknown_lemma n := by
  sorry
''',

    "incomplete_proof": '''
theorem incomplete (P Q : Prop) (hp : P) (hq : Q) : P /\\ Q := by
  constructor
  -- falta: exact hp
  -- falta: exact hq
''',

    "simple_proof": '''
theorem modus_ponens (P Q : Prop) (hp : P) (hpq : P -> Q) : Q := by
  exact hpq hp
''',
}


async def demonstrate_code_verification():
    """Demostrar verificacion de codigo Lean."""
    print("\n" + "=" * 50)
    print("Verificacion de Codigo Lean")
    print("=" * 50)

    client = LeanClient()
    parser = LeanParser()

    for name, code in LEAN_EXAMPLES.items():
        print(f"\n--- {name} ---")
        print(code.strip()[:100] + "..." if len(code) > 100 else code.strip())

        result = await client.check_code(code)

        if result.status == LeanResultStatus.SUCCESS:
            print("[OK] Codigo valido")
        elif result.status == LeanResultStatus.ERROR:
            print("[ERROR] Errores encontrados:")

            # Parsear errores
            messages = parser.parse_output(result.raw_output or "")
            for msg in messages:
                if msg.severity == MessageSeverity.ERROR:
                    print(f"  - {msg.message}")
                    if msg.line:
                        print(f"    Linea: {msg.line}")

            # Sugerir correcciones
            suggestions = parser.suggest_fixes(result.raw_output or "", code)
            if suggestions:
                print("  Sugerencias:")
                for s in suggestions:
                    print(f"    => {s}")
        else:
            print(f"? Estado: {result.status.name}")


def demonstrate_tactic_selection():
    """Demostrar seleccion inteligente de tacticas."""
    print("\n" + "=" * 50)
    print("Seleccion Inteligente de Tacticas")
    print("=" * 50)

    mapper = TacticMapper()

    # Goals de ejemplo
    goals = [
        ("forall (n : Nat), P n", "Introducir variable universalmente cuantificada"),
        ("P -> Q", "Probar implicacion"),
        ("P /\\ Q", "Probar conjuncion"),
        ("P \\/ Q", "Probar disyuncion"),
        ("exists x, P x", "Probar existencial"),
        ("a = b", "Probar igualdad"),
        ("a + b = b + a", "Probar igualdad aritmetica"),
        ("n < m -> n <= m", "Probar desigualdad"),
        ("List.length (a :: as) = 1 + List.length as", "Probar sobre listas"),
    ]

    for goal, description in goals:
        print(f"\n  Goal: {goal}")
        print(f"  ({description})")

        # Obtener tacticas sugeridas
        tactics = mapper.suggest_tactics(goal)

        print("  Tacticas sugeridas:")
        for tactic in tactics[:3]:  # Top 3
            t = mapper.get_tactic(tactic)
            if t:
                print(f"    * {t.name}: {t.description}")
            else:
                print(f"    * {tactic}")


def demonstrate_tactic_catalog():
    """Mostrar catalogo de tacticas disponibles."""
    print("\n" + "=" * 50)
    print("Catalogo de Tacticas Lean 4")
    print("=" * 50)

    mapper = TacticMapper()

    # Agrupar por categoria
    categories = {}
    for name in mapper.tactic_names:
        tactic = mapper.get_tactic(name)
        if tactic:
            cat = tactic.category.name
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tactic)

    for cat_name, tactics in sorted(categories.items()):
        print(f"\n  {cat_name}:")
        for t in tactics:
            print(f"    * {t.name}")
            print(f"      {t.description}")
            if t.preconditions:
                print(f"      Pre: {', '.join(t.preconditions[:2])}")


def demonstrate_proof_workflow():
    """Demostrar flujo de trabajo de prueba."""
    print("\n" + "=" * 50)
    print("Flujo de Trabajo: Prueba Paso a Paso")
    print("=" * 50)

    # Teorema a probar
    theorem = "forall (P Q : Prop), P -> Q -> P /\\ Q"

    print(f"\n  Teorema: {theorem}")
    print("\n  Prueba interactiva:")

    steps = [
        ("|- forall (P Q : Prop), P -> Q -> P /\\ Q", "intro P", "Introducir P"),
        ("P : Prop |- forall (Q : Prop), P -> Q -> P /\\ Q", "intro Q", "Introducir Q"),
        ("P Q : Prop |- P -> Q -> P /\\ Q", "intro hp", "Introducir hipotesis hp : P"),
        ("P Q : Prop, hp : P |- Q -> P /\\ Q", "intro hq", "Introducir hipotesis hq : Q"),
        ("P Q : Prop, hp : P, hq : Q |- P /\\ Q", "constructor", "Dividir conjuncion"),
        ("P Q : Prop, hp : P, hq : Q |- P", "exact hp", "Usar hp para P"),
        ("P Q : Prop, hp : P, hq : Q |- Q", "exact hq", "Usar hq para Q"),
        ("No goals", "done", "Prueba completada"),
    ]

    for i, (state, tactic, explanation) in enumerate(steps, 1):
        print(f"\n  Paso {i}:")
        print(f"    Estado: {state}")
        print(f"    Tactica: {tactic}")
        print(f"    => {explanation}")

    print("\n  Codigo Lean completo:")
    print("  ```lean")
    print("  theorem and_intro (P Q : Prop) (hp : P) (hq : Q) : P /\\ Q := by")
    print("    constructor")
    print("    · exact hp")
    print("    · exact hq")
    print("  ```")


def demonstrate_error_recovery():
    """Demostrar recuperacion de errores."""
    print("\n" + "=" * 50)
    print("Recuperacion de Errores")
    print("=" * 50)

    parser = LeanParser()

    # Errores comunes y recuperacion
    errors = [
        (
            "error: type mismatch\n  has type\n    Nat\n  but is expected to have type\n    String",
            "Type mismatch: se esperaba String pero se encontro Nat"
        ),
        (
            "error: unknown identifier 'foo'",
            "Identificador desconocido: 'foo' no esta definido"
        ),
        (
            "error: unsolved goals\n⊢ P",
            "Prueba incompleta: quedan goals por resolver"
        ),
        (
            "error: invalid use of 'sorry'",
            "Uso de sorry: prueba no terminada"
        ),
    ]

    for error_msg, description in errors:
        print(f"\n  Error: {description}")

        messages = parser.parse_output(error_msg)
        for msg in messages:
            if msg.severity == MessageSeverity.ERROR:
                error_type = parser.detect_error_pattern(msg.message)
                print(f"    Tipo: {error_type}")

                suggestions = parser.suggest_fixes(error_msg, "")
                if suggestions:
                    print(f"    Sugerencia: {suggestions[0]}")


async def main():
    """Funcion principal."""
    print("=" * 60)
    print("Nucleo Logico Evolutivo - Integracion Lean 4")
    print("=" * 60)

    # 1. Verificacion de codigo
    await demonstrate_code_verification()

    # 2. Seleccion de tacticas
    demonstrate_tactic_selection()

    # 3. Catalogo de tacticas
    demonstrate_tactic_catalog()

    # 4. Flujo de prueba
    demonstrate_proof_workflow()

    # 5. Recuperacion de errores
    demonstrate_error_recovery()

    print("\n" + "=" * 60)
    print("Ejemplo de integracion completado!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
