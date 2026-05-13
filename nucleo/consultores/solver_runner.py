"""
SolverRunner
============
Ejecuta los scripts Python generados por el módulo Consultores Avanzados
en un subproceso aislado con timeout.

Flujo completo:
    solver.py  → stdout + solution.json
    bridge.py  → lean_instance.lean
    LeanClient → verifica lean_instance.lean

El ejecutor NO usa eval/exec — corre siempre como subproceso independiente
para aislar el estado del proceso principal.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SolverResult:
    """Resultado de ejecutar un solver script."""
    success: bool = False
    stdout: str = ""
    stderr: str = ""
    returncode: int = -1
    solution: Optional[dict] = None          # contenido de solution.json si se generó
    lean_instance: Optional[str] = None      # código Lean producido por el bridge
    lean_verified: Optional[bool] = None     # resultado de verificación Lean
    lean_errors: list[str] = field(default_factory=list)
    elapsed_s: float = 0.0
    error_msg: str = ""


# Preámbulo que se inyecta al inicio de cada script para garantizar
# que las librerías más comunes estén disponibles sin imports extra.
_PREAMBLE = textwrap.dedent("""\
    import sys, os, json
    from pathlib import Path

    # Asegurar que solution.json se escribe junto al script
    _WORK_DIR = Path(__file__).parent
    os.chdir(_WORK_DIR)

""")


def run_solver(
    script: str,
    timeout_s: int = 60,
    work_dir: Optional[Path] = None,
) -> SolverResult:
    """
    Ejecuta un script Python de solver de forma síncrona.

    Args:
        script:    Código Python del solver (generado por el LLM).
        timeout_s: Tiempo máximo de ejecución en segundos.
        work_dir:  Directorio de trabajo (temporal si es None).

    Returns:
        SolverResult con stdout, stderr, solution.json (si existe) y
        el returncode del proceso.
    """
    import time

    result = SolverResult()
    t0 = time.perf_counter()

    with tempfile.TemporaryDirectory() as tmp:
        if work_dir is None:
            work_dir = Path(tmp)

        script_path = work_dir / "solver_generated.py"
        script_path.write_text(_PREAMBLE + script, encoding="utf-8")

        try:
            proc = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(work_dir),
                capture_output=True,
                timeout=timeout_s,
                text=False,
            )
            result.returncode = proc.returncode
            result.stdout = proc.stdout.decode("utf-8", errors="replace")
            result.stderr = proc.stderr.decode("utf-8", errors="replace")
            result.success = proc.returncode == 0

        except subprocess.TimeoutExpired:
            result.error_msg = f"Timeout: el solver tardó más de {timeout_s}s"
            result.success = False
        except Exception as e:
            result.error_msg = str(e)
            result.success = False
        finally:
            result.elapsed_s = time.perf_counter() - t0

        # Leer solution.json si el solver lo produjo
        sol_path = work_dir / "solution.json"
        if sol_path.exists():
            try:
                result.solution = json.loads(sol_path.read_text(encoding="utf-8"))
            except Exception:
                pass

    return result


def run_bridge(
    bridge_script: str,
    solution: dict,
    timeout_s: int = 30,
) -> tuple[Optional[str], str]:
    """
    Ejecuta el bridge script con la solución del solver.

    El bridge recibe solution.json y debe escribir lean_instance.lean
    o imprimir el código Lean por stdout.

    Returns:
        (lean_code, error_msg)  — lean_code es None si falla.
    """
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)

        # Escribir solution.json para que el bridge lo lea
        (work / "solution.json").write_text(
            json.dumps(solution, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        script_path = work / "bridge_generated.py"
        script_path.write_text(_PREAMBLE + bridge_script, encoding="utf-8")

        try:
            proc = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(work),
                capture_output=True,
                timeout=timeout_s,
                text=False,
            )
            stdout = proc.stdout.decode("utf-8", errors="replace").strip()
            stderr = proc.stderr.decode("utf-8", errors="replace").strip()

            if proc.returncode != 0:
                return None, stderr or "Bridge script falló sin output"

            # Preferir lean_instance.lean sobre stdout
            lean_path = work / "lean_instance.lean"
            if lean_path.exists():
                return lean_path.read_text(encoding="utf-8"), ""
            if stdout:
                return stdout, ""
            return None, "Bridge no produjo lean_instance.lean ni output"

        except subprocess.TimeoutExpired:
            return None, f"Bridge timeout ({timeout_s}s)"
        except Exception as e:
            return None, str(e)


async def run_full_pipeline(
    solver_script: str,
    bridge_script: str,
    lean_client,
    solver_timeout: int = 60,
    bridge_timeout: int = 30,
) -> SolverResult:
    """
    Pipeline completo: solver → bridge → Lean.

    Ejecuta el solver, si produce solución corre el bridge,
    y si el bridge genera Lean lo verifica con lean_client.
    """
    result = run_solver(solver_script, timeout_s=solver_timeout)

    if not result.success or result.solution is None:
        return result

    if bridge_script.strip():
        lean_code, err = run_bridge(bridge_script, result.solution,
                                    timeout_s=bridge_timeout)
        if lean_code:
            result.lean_instance = lean_code
            # Verificar con Lean
            try:
                lean_result = await lean_client.check_code(lean_code)
                from nucleo.lean.client import LeanResultStatus
                result.lean_verified = lean_result.status == LeanResultStatus.SUCCESS
                result.lean_errors = lean_result.error_messages
            except Exception as e:
                result.lean_errors = [str(e)]
        else:
            result.lean_errors = [f"Bridge falló: {err}"]

    return result
