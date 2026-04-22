"""
local_agent.py — Agente Local de METAMATEMÁTICO
================================================
Ejecuta verificación Lean 4 en tu propia máquina y conecta con
la instancia web del sistema para ampliar su capacidad de cómputo.

Uso:
    python scripts/local_agent.py --server https://tudominio.com
    python scripts/local_agent.py --server https://tudominio.com --token MI_TOKEN

El agente:
1. Se registra con la instancia web
2. Recibe snippets Lean para verificar
3. Los verifica localmente con tu instalación de Lean + Mathlib
4. Devuelve los resultados

Requisitos locales:
    - Lean 4 instalado (elan): https://elan.lean-lang.org
    - lake update (Mathlib descargado)
    - pip install requests websockets
"""

import sys
import os
import json
import time
import hashlib
import argparse
import subprocess
import tempfile
import threading
import logging
from pathlib import Path

try:
    import requests
    import websockets
    import asyncio
except ImportError:
    print("Instalando dependencias del agente...")
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "websockets", "-q"])
    import requests
    import websockets
    import asyncio

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("local_agent")

# ── Verificación Lean local ────────────────────────────────────────────

LEAN_HEADER = """import Mathlib.Tactic
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Data.Real.Irrational
set_option maxHeartbeats 400000
"""

def check_lean_local(code: str, timeout: int = 60) -> dict:
    """Verifica código Lean en esta máquina."""
    # Buscar lake en el PATH
    lake_cmd = None
    for candidate in ["lake", str(Path.home() / ".elan/bin/lake")]:
        try:
            subprocess.run([candidate, "--version"], capture_output=True, timeout=5)
            lake_cmd = candidate
            break
        except Exception:
            continue

    if lake_cmd is None:
        return {
            "success": False,
            "error": "Lean/lake no encontrado. Instala desde https://elan.lean-lang.org",
            "local": True,
        }

    # Escribir snippet en temp file
    full_code = LEAN_HEADER + "\n" + code
    with tempfile.NamedTemporaryFile(
        suffix=".lean", mode="w", encoding="utf-8", delete=False
    ) as f:
        f.write(full_code)
        tmp = f.name

    try:
        r = subprocess.run(
            [lake_cmd, "env", "lean", tmp],
            capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace",
        )
        success = r.returncode == 0
        out = (r.stdout + r.stderr).strip()
        has_sorry = "sorry" in code.lower()
        return {
            "success": success and not has_sorry,
            "has_sorry": has_sorry,
            "output": out[:2000],
            "local": True,
            "agent_id": _agent_id(),
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "timeout", "local": True}
    except Exception as e:
        return {"success": False, "error": str(e), "local": True}
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass


def _agent_id() -> str:
    import socket
    raw = socket.gethostname() + str(Path.home())
    return "agent-" + hashlib.sha1(raw.encode()).hexdigest()[:8]


# ── Modo polling (HTTP) ────────────────────────────────────────────────

def run_polling(server: str, token: str, interval: int = 5):
    """Modo simple: consulta el servidor periódicamente por tareas pendientes."""
    headers = {"X-Agent-Token": token, "X-Agent-ID": _agent_id()}
    tasks_url = server.rstrip("/") + "/api/lean_tasks"
    results_url = server.rstrip("/") + "/api/lean_results"

    log.info(f"Agente local conectado a {server} (polling cada {interval}s)")
    log.info(f"Agent ID: {_agent_id()}")

    while True:
        try:
            resp = requests.get(tasks_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                tasks = resp.json().get("tasks", [])
                for task in tasks:
                    task_id = task["id"]
                    code = task["code"]
                    log.info(f"Verificando tarea {task_id}...")
                    result = check_lean_local(code)
                    result["task_id"] = task_id
                    requests.post(results_url, json=result, headers=headers, timeout=10)
                    log.info(f"  → {'✔' if result['success'] else '✗'} {task_id}")
            elif resp.status_code == 404:
                pass  # endpoint no implementado aún — modo demo
        except requests.exceptions.ConnectionError:
            log.warning(f"No se puede conectar a {server}, reintentando...")
        except Exception as e:
            log.warning(f"Error: {e}")

        time.sleep(interval)


# ── Modo standalone (verificación directa) ────────────────────────────

def run_standalone():
    """Modo interactivo: pega código Lean y verifica localmente."""
    print("\n╔══════════════════════════════════════════╗")
    print("║   METAMATEMÁTICO — Agente Local Lean     ║")
    print("╚══════════════════════════════════════════╝\n")
    print("Pega código Lean 4 (termina con una línea que solo diga 'END'):\n")

    while True:
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line.strip() == "END":
                break
            lines.append(line)

        if not lines:
            break

        code = "\n".join(lines)
        print("\nVerificando con Lean local...")
        result = check_lean_local(code)
        status = "✔ CORRECTO" if result["success"] else "✗ INCORRECTO"
        print(f"\n{status}")
        if result.get("output"):
            print(result["output"][:500])
        print("\n--- (pega más código o Ctrl+C para salir) ---\n")


# ── Verificar instalación ─────────────────────────────────────────────

def verify_installation() -> bool:
    """Comprueba si Lean + Mathlib están disponibles."""
    print("\nVerificando instalación local de Lean 4...")

    # lean
    for cmd in ["lean", str(Path.home() / ".elan/bin/lean")]:
        try:
            r = subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
            if r.returncode == 0:
                v = r.stdout.decode().strip()
                print(f"  ✔ Lean: {v}")
                break
        except Exception:
            continue
    else:
        print("  ✗ Lean no encontrado")
        print("    → Instala desde: https://elan.lean-lang.org")
        print("    → curl https://elan.lean-lang.org/elan-init.sh -sSf | sh")
        return False

    # lake + mathlib
    lake_check = check_lean_local("theorem test : 1 + 1 = 2 := by norm_num")
    if lake_check["success"]:
        print("  ✔ Mathlib: disponible (1+1=2 verificado)")
        return True
    else:
        err = lake_check.get("error", lake_check.get("output", ""))
        print(f"  ✗ Mathlib: {err[:120]}")
        print("    → Ejecuta: lake update && lake exe cache get")
        return False


# ── Main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Agente local de verificación Lean para METAMATEMÁTICO"
    )
    parser.add_argument("--server", default="", help="URL de la instancia web (https://...)")
    parser.add_argument("--token",  default="local", help="Token de autenticación")
    parser.add_argument("--check",  action="store_true", help="Verificar instalación y salir")
    parser.add_argument("--interval", type=int, default=5, help="Segundos entre polls (default: 5)")
    args = parser.parse_args()

    if args.check or not args.server:
        ok = verify_installation()
        if ok and not args.server:
            print("\n✔ Tu sistema está listo.")
            print("Para conectar con una instancia web:")
            print("  python scripts/local_agent.py --server https://tuapp.com")
            run_standalone()
        return

    verify_installation()
    run_polling(args.server, args.token, args.interval)


if __name__ == "__main__":
    main()
