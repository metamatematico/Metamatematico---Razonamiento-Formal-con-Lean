"""
CLI del Nucleo Logico Evolutivo
===============================

Interfaz de linea de comandos para el Nucleo.

Comandos:
- nucleo chat: Sesion interactiva con Claude
- nucleo init: Inicializar proyecto
- nucleo check: Verificar integracion con Lean
- nucleo graph: Mostrar estadisticas del grafo
- nucleo validate: Validar axiomas
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from nucleo.config import NucleoConfig
from nucleo.graph.category import SkillCategory


console = Console()


# =========================================================================
# CHAT COMMAND
# =========================================================================

CHAT_COMMANDS = {
    "/help":   "Mostrar esta ayuda",
    "/stats":  "Estadisticas del sistema",
    "/skills": "Listar skills disponibles",
    "/axioms": "Verificar axiomas formales",
    "/clear":  "Limpiar historial de conversacion",
    "/quit":   "Salir",
}


def _print_banner(model: str) -> None:
    """Print welcome banner."""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]NLE v7.0[/] — Nucleo Logico Evolutivo\n"
        f"Modelo: [green]{model}[/]\n"
        "Escribe tu consulta matematica o /help",
        title="Chat Interactivo",
        border_style="cyan",
    ))
    console.print()


def _print_help() -> None:
    """Print available commands."""
    table = Table(title="Comandos", show_header=False, box=None)
    table.add_column(style="bold cyan", min_width=10)
    table.add_column()
    for cmd, desc in CHAT_COMMANDS.items():
        table.add_row(cmd, desc)
    console.print(table)
    console.print()


def _print_stats(nucleo) -> None:
    """Print system statistics."""
    stats = nucleo.stats
    table = Table(title="Estado del Sistema")
    table.add_column("Metrica", style="cyan")
    table.add_column("Valor", style="green")
    for key, value in stats.items():
        table.add_row(str(key), str(value))
    console.print(table)
    console.print()


def _print_skills(nucleo) -> None:
    """Print available skills grouped by pillar."""
    table = Table(title="Skills Disponibles")
    table.add_column("Pilar", style="bold")
    table.add_column("Nivel", style="dim")
    table.add_column("Skill", style="green")

    skills = []
    for skill_id in nucleo.graph.skill_ids:
        skill = nucleo.graph.get_skill(skill_id)
        if skill:
            pillar = skill.pillar.name if skill.pillar else "—"
            skills.append((pillar, skill.level, skill.name))

    for pillar, level, name in sorted(skills):
        table.add_row(pillar, str(level), name)

    console.print(table)
    console.print(f"[dim]Total: {len(skills)} skills[/]")
    console.print()


def _print_axioms(nucleo) -> None:
    """Verify and print formal axioms."""
    result = nucleo.graph.verify_all_axioms()

    table = Table(title="Axiomas Formales (8.1-8.4)")
    table.add_column("Axioma", style="cyan")
    table.add_column("Estado")

    for key in ["8.1_hierarchy", "8.2_multiplicity", "8.3_connectivity", "8.4_coverage"]:
        if key in result:
            ok = result[key].get("satisfies", False)
            status = "[green]PASS[/]" if ok else "[red]FAIL[/]"
            table.add_row(key, status)

    all_ok = result.get("all_satisfied", False)
    console.print(table)
    if all_ok:
        console.print("[bold green]Todos los axiomas satisfechos[/]")
    else:
        console.print("[bold red]Algunos axiomas no se satisfacen[/]")
    console.print()


def _print_response(response, verbose: bool = False) -> None:
    """Print a NucleoResponse."""
    # Action + confidence header
    action_name = response.action_type.name
    conf = response.confidence
    color = "green" if conf >= 0.7 else "yellow" if conf >= 0.4 else "red"
    console.print(f"[dim][{action_name} | confianza: [{color}]{conf:.2f}[/]][/]")

    # Content — render as markdown if it contains formatting
    content = response.content
    if any(c in content for c in ["```", "**", "##", "- "]):
        console.print(Markdown(content))
    else:
        console.print(content)

    # Token usage (if available in metadata)
    if verbose and response.metadata:
        tokens = response.metadata.get("tokens")
        if tokens:
            console.print(f"[dim](tokens: {tokens})[/]")

    # Lean result
    if response.lean_result:
        status = response.lean_result.status.name
        color = "green" if response.lean_result.is_success else "yellow"
        console.print(f"[dim]Lean: [{color}]{status}[/][/]")

    console.print()


async def _chat_loop(args: argparse.Namespace) -> int:
    """Async chat REPL."""
    from nucleo.core import Nucleo

    model = getattr(args, "model", None) or "claude-sonnet-4-20250514"
    verbose = getattr(args, "verbose", False)

    # Load config (puede tener api_key en nucleo_config.yaml)
    config_path = Path("nucleo_config.yaml")
    if config_path.exists():
        config = NucleoConfig.from_yaml(config_path)
    else:
        config = NucleoConfig()
    config.llm.model = model

    # Check API key: env var > config > warning
    api_key = os.environ.get("ANTHROPIC_API_KEY") or config.llm.api_key
    if not api_key:
        console.print("[bold yellow]Aviso:[/] No se encontro API key de Anthropic.")
        console.print("El sistema funcionara en modo mock (sin Claude real).")
        console.print("Para usar Claude, configura tu API key:")
        console.print("  [cyan]$env:ANTHROPIC_API_KEY='sk-ant-...'[/]  (PowerShell)")
        console.print("  [cyan]set ANTHROPIC_API_KEY=sk-ant-...[/]    (CMD)")
        console.print("  O agrega [cyan]api_key: 'sk-ant-...'[/] bajo [cyan]llm:[/] en nucleo_config.yaml")
        console.print()
    else:
        config.llm.api_key = api_key

    _print_banner(model)

    # Initialize Nucleo
    console.print("[dim]Inicializando sistema...[/]")
    nucleo = Nucleo(config=config)

    if verbose:
        def on_action(decision):
            console.print(
                f"  [dim][CR: {decision.source_cr.name} -> "
                f"{decision.action_type.name}][/]"
            )
        nucleo.on_action(on_action)

    await nucleo.initialize()

    skill_count = nucleo.stats.get("num_skills", 0)
    console.print(f"[green]Listo.[/] {skill_count} skills cargados.")
    console.print()

    # REPL
    while True:
        try:
            user_input = console.input("[bold cyan]Tu >[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Adios![/]")
            return 0

        if not user_input:
            continue

        # Special commands
        if user_input.startswith("/"):
            cmd = user_input.split()[0].lower()
            if cmd == "/quit" or cmd == "/exit":
                console.print("[dim]Adios![/]")
                return 0
            elif cmd == "/help":
                _print_help()
            elif cmd == "/stats":
                _print_stats(nucleo)
            elif cmd == "/skills":
                _print_skills(nucleo)
            elif cmd == "/axioms":
                _print_axioms(nucleo)
            elif cmd == "/clear":
                if nucleo._llm:
                    nucleo._llm.clear_conversation()
                console.print("[dim]Historial limpiado.[/]\n")
            else:
                console.print(f"[yellow]Comando desconocido: {cmd}[/]")
                _print_help()
            continue

        # Process with Nucleo
        try:
            response = await nucleo.process(user_input)
            _print_response(response, verbose=verbose)
        except Exception as e:
            console.print(f"[red]Error: {e}[/]\n")

    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    """Sesion interactiva con Claude."""
    return asyncio.run(_chat_loop(args))


# =========================================================================
# EXISTING COMMANDS
# =========================================================================

def cmd_init(args: argparse.Namespace) -> int:
    """Inicializar proyecto."""
    from nucleo.pillars import (
        PillarRegistry,
        TypeTheoryPillar,
        LogicPillar,
        CategoryTheoryPillar,
        SetTheoryPillar,
    )

    console.print("[bold green]Inicializando Nucleo Logico Evolutivo...[/]")

    # Crear configuracion
    config = NucleoConfig()

    # Crear directorios
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.models_dir.mkdir(parents=True, exist_ok=True)
    config.logs_dir.mkdir(parents=True, exist_ok=True)

    # Guardar configuracion
    config_path = Path("nucleo_config.yaml")
    config.save_yaml(config_path)

    console.print(f"[green]Configuracion guardada en {config_path}[/]")

    # Registrar pilares
    registry = PillarRegistry()
    registry.register(TypeTheoryPillar())
    registry.register(LogicPillar())
    registry.register(CategoryTheoryPillar())
    registry.register(SetTheoryPillar())

    console.print("[green]Pilares fundacionales registrados:[/]")
    for name in registry.pillar_names:
        console.print(f"  - {name}")

    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Verificar integracion con Lean."""
    console.print("[bold]Verificando integracion con Lean 4...[/]")

    try:
        from nucleo.lean import LeanClient

        client = LeanClient(project_path=Path.cwd())

        # Test basico
        code = """
theorem test : 1 + 1 = 2 := rfl
"""
        result = client.check_code_sync(code)

        if result.is_success:
            console.print("[green]Lean 4 conectado correctamente[/]")
            return 0
        else:
            console.print(f"[yellow]Lean respondio con errores:[/]")
            for err in result.error_messages:
                console.print(f"  {err}")
            return 1

    except Exception as e:
        console.print(f"[red]Error de conexion: {e}[/]")
        return 1


def cmd_graph(args: argparse.Namespace) -> int:
    """Mostrar estadisticas del grafo."""
    # Crear grafo de ejemplo
    graph = SkillCategory(name="DemoGraph")

    # Añadir skills de ejemplo
    from nucleo.types import Skill, PillarType, MorphismType

    skills = [
        Skill(id="fol", name="FOL Basics", pillar=PillarType.LOG),
        Skill(id="cic", name="CIC", pillar=PillarType.TYPE),
        Skill(id="cat", name="Categories", pillar=PillarType.CAT),
    ]

    for s in skills:
        graph.add_skill(s)

    graph.add_morphism("fol", "cic", MorphismType.TRANSLATION)
    graph.add_morphism("cat", "cic", MorphismType.DEPENDENCY)

    # Mostrar tabla
    table = Table(title="Grafo Categorico de Skills")
    table.add_column("Metrica", style="cyan")
    table.add_column("Valor", style="green")

    stats = graph.stats
    table.add_row("Nombre", graph.name)
    table.add_row("Skills", str(stats["num_skills"]))
    table.add_row("Morfismos", str(stats["num_morphisms"]))
    table.add_row("Peso total", f"{stats['total_weight']:.2f}")
    table.add_row("Conectado", "Si" if graph.is_connected() else "No")

    console.print(table)

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validar axiomas categoricos."""
    console.print("[bold]Validando axiomas del sistema...[/]")

    graph = SkillCategory()

    # Añadir algunos skills
    from nucleo.types import Skill

    for i in range(5):
        graph.add_skill(Skill(id=f"s{i}", name=f"Skill {i}"))

    # Verificar axiomas
    results = graph.verify_axioms()

    table = Table(title="Verificacion de Axiomas")
    table.add_column("Axioma", style="cyan")
    table.add_column("Estado", style="green")

    for axiom, passed in results.items():
        status = "[green]PASS[/]" if passed else "[red]FAIL[/]"
        table.add_row(axiom, status)

    console.print(table)

    all_passed = all(results.values())
    if all_passed:
        console.print("\n[bold green]Todos los axiomas verificados[/]")
        return 0
    else:
        console.print("\n[bold red]Algunos axiomas fallaron[/]")
        return 1


# =========================================================================
# MAIN
# =========================================================================

def main() -> int:
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        prog="nucleo",
        description="Nucleo Logico Evolutivo - CLI"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 7.0.0"
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos")

    # chat
    parser_chat = subparsers.add_parser(
        "chat", help="Sesion interactiva con Claude"
    )
    parser_chat.add_argument(
        "--model", "-m",
        default=None,
        help="Modelo Claude (default: claude-sonnet-4-20250514)"
    )
    parser_chat.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar detalles de debug (accion RL, etc.)"
    )
    parser_chat.set_defaults(func=cmd_chat)

    # init
    parser_init = subparsers.add_parser("init", help="Inicializar proyecto")
    parser_init.set_defaults(func=cmd_init)

    # check
    parser_check = subparsers.add_parser("check", help="Verificar Lean")
    parser_check.set_defaults(func=cmd_check)

    # graph
    parser_graph = subparsers.add_parser("graph", help="Estadisticas del grafo")
    parser_graph.set_defaults(func=cmd_graph)

    # validate
    parser_validate = subparsers.add_parser("validate", help="Validar axiomas")
    parser_validate.set_defaults(func=cmd_validate)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
