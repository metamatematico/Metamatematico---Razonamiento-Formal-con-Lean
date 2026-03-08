"""
Cliente Lean 4
==============

Cliente bidireccional para comunicacion con Lean 4.
Utiliza el REPL de Lake para enviar comandos y recibir feedback.

Flujo:
    Usuario -> LLM -> Nucleo -> LeanClient -> Lean 4
                                    |
                              LeanResult
"""

from __future__ import annotations

import asyncio
import subprocess
import json
import tempfile
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class LeanResultStatus(Enum):
    """Estado del resultado de Lean."""
    SUCCESS = auto()       # Prueba completada
    ERROR = auto()         # Error de compilacion/tipo
    TIMEOUT = auto()       # Timeout excedido
    INCOMPLETE = auto()    # Prueba incompleta (goals pendientes)
    SORRY = auto()         # Contiene sorry


@dataclass
class LeanGoal:
    """Un goal de Lean pendiente de resolver."""
    index: int
    hypothesis: list[str]
    target: str

    def __str__(self) -> str:
        hyps = "\n".join(f"  {h}" for h in self.hypothesis)
        return f"Goal {self.index}:\n{hyps}\n⊢ {self.target}"


@dataclass
class LeanResult:
    """
    Resultado de ejecutar codigo Lean.

    Attributes:
        status: Estado del resultado
        goals: Lista de goals pendientes (si hay)
        messages: Mensajes de Lean (errores, warnings, info)
        output: Output completo de Lean
        elapsed_ms: Tiempo de ejecucion en ms
    """
    status: LeanResultStatus
    goals: list[LeanGoal] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)
    output: str = ""
    elapsed_ms: float = 0.0

    @property
    def is_success(self) -> bool:
        return self.status == LeanResultStatus.SUCCESS

    @property
    def has_errors(self) -> bool:
        return any(m.get("severity") == "error" for m in self.messages)

    @property
    def error_messages(self) -> list[str]:
        return [m.get("message", "") for m in self.messages if m.get("severity") == "error"]

    def get_first_error(self) -> Optional[str]:
        errors = self.error_messages
        return errors[0] if errors else None


class LeanClient:
    """
    Cliente para comunicacion bidireccional con Lean 4.

    Metodos principales:
    - check_code: Verificar codigo Lean
    - check_theorem: Verificar un teorema
    - get_goal_state: Obtener estado de goals
    - apply_tactic: Aplicar una tactica

    Example:
        client = LeanClient(project_path="./")
        result = await client.check_theorem(
            name="my_theorem",
            statement="∀ n : Nat, n + 0 = n",
            proof="intro n; rfl"
        )
        if result.is_success:
            print("Prueba verificada!")
    """

    def __init__(
        self,
        project_path: Optional[Path | str] = None,
        lean_path: str = "lake",
        timeout_ms: int = 30000,
    ):
        """
        Inicializar cliente Lean.

        Args:
            project_path: Ruta al proyecto Lean (con lakefile.toml)
            lean_path: Ruta al ejecutable lake
            timeout_ms: Timeout en milisegundos
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.lean_path = lean_path
        self.timeout_s = timeout_ms / 1000.0

    async def check_code(self, code: str) -> LeanResult:
        """
        Verificar codigo Lean arbitrario.

        Args:
            code: Codigo Lean a verificar

        Returns:
            LeanResult con el estado de verificacion
        """
        import time
        start = time.perf_counter()

        # Crear archivo temporal con el codigo
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".lean",
            delete=False,
            dir=self.project_path,
            encoding="utf-8",
        ) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            result = await self._run_lean_check(temp_file)
            result.elapsed_ms = (time.perf_counter() - start) * 1000
            return result
        finally:
            # Limpiar archivo temporal
            temp_file.unlink(missing_ok=True)

    async def check_theorem(
        self,
        name: str,
        statement: str,
        proof: str,
        imports: Optional[list[str]] = None,
    ) -> LeanResult:
        """
        Verificar un teorema con su prueba.

        Args:
            name: Nombre del teorema
            statement: Enunciado del teorema
            proof: Prueba del teorema
            imports: Lista de imports necesarios

        Returns:
            LeanResult con el estado de verificacion
        """
        # Construir codigo completo
        import_lines = ""
        if imports:
            import_lines = "\n".join(f"import {imp}" for imp in imports) + "\n\n"

        code = f"""{import_lines}theorem {name} : {statement} := by
  {proof}
"""
        return await self.check_code(code)

    async def get_goal_state(
        self,
        code: str,
        position: tuple[int, int],
    ) -> list[LeanGoal]:
        """
        Obtener el estado de goals en una posicion del codigo.

        Args:
            code: Codigo Lean
            position: (linea, columna) - 0-indexed

        Returns:
            Lista de goals pendientes
        """
        # Por ahora, parsear desde mensajes de error/info
        result = await self.check_code(code)
        return result.goals

    async def apply_tactic(
        self,
        current_state: str,
        tactic: str,
    ) -> LeanResult:
        """
        Aplicar una tactica al estado actual.

        Args:
            current_state: Codigo Lean hasta el punto actual
            tactic: Tactica a aplicar

        Returns:
            LeanResult con el nuevo estado
        """
        # Añadir la tactica al codigo
        code = f"{current_state}\n  {tactic}"
        return await self.check_code(code)

    async def _run_lean_check(self, file_path: Path) -> LeanResult:
        """
        Ejecutar verificacion de Lean en un archivo.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                self.lean_path,
                "env",
                "lean",
                str(file_path),
                "--json",
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout_s
            )

            output = stdout.decode("utf-8", errors="replace")
            errors = stderr.decode("utf-8", errors="replace")

            return self._parse_lean_output(output, errors, proc.returncode or 0)

        except asyncio.TimeoutError:
            logger.warning(f"Lean timeout after {self.timeout_s}s")
            return LeanResult(
                status=LeanResultStatus.TIMEOUT,
                output=f"Timeout after {self.timeout_s}s"
            )
        except Exception as e:
            logger.error(f"Error running Lean: {e}")
            return LeanResult(
                status=LeanResultStatus.ERROR,
                messages=[{"severity": "error", "message": str(e)}],
                output=str(e)
            )

    def _parse_lean_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int
    ) -> LeanResult:
        """Parsear output de Lean."""
        messages = []
        goals = []

        # Parsear lineas JSON
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            try:
                msg = json.loads(line)
                messages.append(msg)

                # Extraer goals si los hay
                if "goals" in msg:
                    for i, goal_str in enumerate(msg["goals"]):
                        goals.append(LeanGoal(
                            index=i,
                            hypothesis=[],  # TODO: parsear hipotesis
                            target=goal_str
                        ))
            except json.JSONDecodeError:
                # Linea no es JSON, ignorar
                pass

        # Determinar estado
        has_errors = any(m.get("severity") == "error" for m in messages)
        has_sorry = "sorry" in stdout.lower()

        if has_errors:
            status = LeanResultStatus.ERROR
        elif has_sorry:
            status = LeanResultStatus.SORRY
        elif goals:
            status = LeanResultStatus.INCOMPLETE
        elif return_code == 0:
            status = LeanResultStatus.SUCCESS
        else:
            status = LeanResultStatus.ERROR

        return LeanResult(
            status=status,
            goals=goals,
            messages=messages,
            output=stdout + stderr
        )

    def check_code_sync(self, code: str) -> LeanResult:
        """Version sincrona de check_code."""
        return asyncio.run(self.check_code(code))

    def check_theorem_sync(
        self,
        name: str,
        statement: str,
        proof: str,
        imports: Optional[list[str]] = None,
    ) -> LeanResult:
        """Version sincrona de check_theorem."""
        return asyncio.run(self.check_theorem(name, statement, proof, imports))
